"""village_kit.uvgrain -- the kit's final UV writer (kit 1.10.0, the client-approved queued UV fix).

Every kit building (assembly.build_building, compound.build_compound) runs finish_uvs() on all its meshes once the
geometry is final (after the culls, the guards and the decal anchors).  It changes the `UVMap` layer only -- never a
vertex, a polygon or a material -- so a building's geometry fingerprint is unchanged.

1. Wood grain along each piece's long axis (slots GRAIN_SLOTS).  The rough-wood texture's grain runs along the
   texture's V axis (vertical in the image), and the look-dev test (lookdev/scripts/analyze_uv_grain.py) measures
   the grain as dP/dv, so V is laid along the grain:
     - a piece is an edge-connected loose part, split further by its Mask R byte (core.Acc / BatchAcc write one R
       per piece, so planks welded by the Nanite clean-up stay separate pieces);
     - timber (M_timber, M_timber_weathered): the grain axis is the piece's vertex PCA major axis;
     - shingles and shakes (M_roof_shingle, M_roof_shake): the grain runs UP-SLOPE: the axis is the up-slope
       direction of the piece's up-facing faces (area-weighted mean normal), PCA only for pieces with none;
     - V = position along the axis (metres, continuous over the whole piece, so the grain never jumps at an arris);
       side faces: a box map in the piece's own PCA frame -- U = position along the piece's width axis on the faces
       that face its thickness axis and vice versa (continuous over each side, also on adze-scalloped faces), or,
       for round / square pieces (poles, posts, round rafters; cross-section aspect > ROUND_ASPECT), U = mean
       radius x angle about the axis (one seam); end-grain faces (|n . axis| > END_COS): (width, thickness);
     - about 1 UV unit per metre, as before; a per-piece offset from the piece's position keeps neighbouring pieces
       off the same texture patch (the materials add their own Mask R offset on top).
   M_thatch keeps its UVs (already right: 96 % on the look-dev test); only its collapsed faces are re-projected.
2. No collapsed UVs.  Every remaining face (any slot) whose UV/3D area ratio is below FIX_RATIO (first triangle,
   the check_uv_stretch rule, or the whole face) is re-projected: the face's existing UV map is replaced by the
   nearest rigid (rotation / reflection) map at 1 UV unit per metre, centred on the face's old UV centre, so the
   texture keeps its place and direction and only the smeared axis gets its extent back.
Pooled meshes (shared by linked duplicates) are processed once, in the frame of their first user (by name).

Deterministic: numpy only, no random state.
"""
import json

import numpy as np

GRAIN_SLOTS = ("M_timber", "M_timber_weathered", "M_roof_shingle", "M_roof_shake")
ROOF_SLOTS = ("M_roof_shingle", "M_roof_shake")
END_COS = 0.7            # |n . axis| above this: an end-grain face (planar map of the face)
ROUND_ASPECT = 0.75      # sqrt(w0 / w1) above this (and elongated): U wraps round the axis
FIX_RATIO = 0.25         # collapsed-UV repair threshold (the brief's limit is 0.2; a margin for float32 UVs)


def _arrays(me, M):
    nv, npg, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if M is not None:
        M = np.asarray(M, float)
        co = co @ M[:3, :3].T + M[:3, 3]
    ls = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", lv)
    pm = np.empty(npg, np.int64)
    me.polygons.foreach_get("material_index", pm)
    return co, ls, lt, lv, pm


def _newell(co, ls, lt, lv, lp):
    nxt = np.arange(len(lv)) + 1
    nxt[ls + lt - 1] = ls
    N = np.zeros((len(ls), 3))
    np.add.at(N, lp, np.cross(co[lv], co[lv[nxt]]))
    nn = np.linalg.norm(N, axis=1)
    return N / np.maximum(nn, 1e-30)[:, None], 0.5 * nn


def face_components(me):
    """edge-connected face components (a label per polygon; the look-dev test's loose parts)."""
    npg, nl = len(me.polygons), len(me.loops)
    le = np.empty(nl, np.int64)
    me.loops.foreach_get("edge_index", le)
    lt = np.empty(npg, np.int64)
    me.polygons.foreach_get("loop_total", lt)
    lp = np.repeat(np.arange(npg), lt)
    order = np.argsort(le, kind="stable")
    les, lps = le[order], lp[order]
    same = les[1:] == les[:-1]
    a, b = lps[:-1][same], lps[1:][same]
    lab = np.arange(npg)
    if len(a) == 0:
        return lab
    for _ in range(2000):
        m = np.minimum(lab[a], lab[b])
        new = lab.copy()
        np.minimum.at(new, a, m)
        np.minimum.at(new, b, m)
        for _ in range(8):
            new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def _mask_r_byte(me, ls):
    ca = me.color_attributes.get("Mask")
    if ca is None or ca.domain != "CORNER":
        return np.zeros(len(ls), np.int64)
    col = np.empty(len(me.loops) * 4, np.float32)
    ca.data.foreach_get("color_srgb" if ca.data_type == "BYTE_COLOR" else "color", col)
    return np.round(col.reshape(-1, 4)[ls, 0] * 255).astype(np.int64)


def _sign_fix(L):
    """deterministic axis sign: +Z when the axis climbs, else its largest horizontal component positive."""
    s = np.where(np.abs(L[:, 2]) >= 0.2, np.sign(L[:, 2]),
                 np.where(np.abs(L[:, 0]) >= np.abs(L[:, 1]), np.sign(L[:, 0]), np.sign(L[:, 1])))
    return L * np.where(s == 0, 1.0, s)[:, None]


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-30)


def regrain_mesh(me, M=None):
    """re-write the UVMap of one mesh (see the module doc).  M: its object's world matrix (orientation of up-slope;
    None = identity).  Returns a stats dict."""
    st = dict(faces=len(me.polygons), grain_faces=0, round_pieces=0, sheet_pieces=0, pieces=0, collapsed_fixed=0)
    if len(me.polygons) == 0:
        return st
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.active
    if uvl is None:
        uvl = me.uv_layers.new(name="UVMap")
    co, ls, lt, lv, pm = _arrays(me, M)
    nl = len(lv)
    uv = np.empty(nl * 2, np.float32)
    uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2).astype(np.float64)
    lp = np.repeat(np.arange(len(ls)), lt)
    n, area = _newell(co, ls, lt, lv, lp)
    names = [m.name if m else "" for m in me.materials]
    slot = np.array([names[i] if i < len(names) else "" for i in pm], dtype=object).astype(str)
    grain = np.isin(slot, GRAIN_SLOTS) & (area > 1e-10)
    roof = np.isin(slot, ROOF_SLOTS)
    P = co[lv]                                          # loop positions
    if grain.any():
        comp = face_components(me)
        key = comp * 256 + _mask_r_byte(me, ls)
        _, piece = np.unique(key, return_inverse=True)
        piece = piece.ravel()
        gp = np.unique(piece[grain])                    # pieces with grain faces
        remap = np.full(piece.max() + 1, -1)
        remap[gp] = np.arange(len(gp))
        fpc = remap[piece]                              # piece index per face (-1: no grain face)
        st["pieces"] = int(len(gp))
        # PCA over each piece's unique vertices
        sel = fpc[lp] >= 0
        pairs = np.unique(fpc[lp][sel] * (len(co) + 1) + lv[sel])
        pc, vi = pairs // (len(co) + 1), pairs % (len(co) + 1)
        K = len(gp)
        cnt = np.bincount(pc, minlength=K).astype(float)
        cen = np.zeros((K, 3))
        np.add.at(cen, pc, co[vi])
        cen /= np.maximum(cnt, 1)[:, None]
        D = co[vi] - cen[pc]
        cov = np.zeros((K, 3, 3))
        np.add.at(cov, pc, D[:, :, None] * D[:, None, :])
        w, V = np.linalg.eigh(cov)
        L = _sign_fix(V[:, :, 2])
        B1 = V[:, :, 1]
        # shingles / shakes: the grain runs up-slope.  On any face the up-slope direction is the in-plane gradient
        # of the height, so V = z / k (k = the piece's mean sine of slope over its up-facing faces, ~1 UV / m along
        # the slope) is up-slope on every face and continuous over the whole piece, even on a cone ring or a curled
        # shake; U runs along the face's contour line.
        # Timber SHEETS with no long axis (sqrt(w2 / w1) <= 1.5: a cone or ring deck, an apron soffit) that are
        # mostly sloped get the same height mode -- boards running up the slope (radial on a cone) -- instead of
        # one arbitrary straight direction; flat sheets (floors, ceilings) keep their PCA direction.
        elong_s = np.sqrt(w[:, 2] / np.maximum(w[:, 1], 1e-12))
        slope_f = grain & (np.abs(n[:, 2]) > 0.2) & (np.abs(n[:, 2]) < 0.97)
        pa = np.bincount(fpc[grain], weights=area[grain], minlength=K)
        sa = np.bincount(fpc[slope_f], weights=area[slope_f], minlength=K)
        sheet = (elong_s <= 1.5) & (sa > 0.5 * pa)
        rpiece = np.zeros(K, bool)
        rpiece[fpc[grain & roof]] = True
        hmode = rpiece | sheet
        upf = grain & hmode[np.maximum(fpc, 0)] & (np.abs(n[:, 2]) > 0.2)
        ks = np.zeros(K)
        ka = np.zeros(K)
        np.add.at(ks, fpc[upf], np.sqrt(np.maximum(1 - n[upf, 2] ** 2, 0)) * area[upf])
        np.add.at(ka, fpc[upf], area[upf])
        kpc = np.where(ka > 1e-12, ks / np.maximum(ka, 1e-30), 1.0)
        kpc = np.clip(kpc, 0.25, 1.0)
        st["sheet_pieces"] = int(sheet.sum())
        use_s = hmode
        # B1: the across axis (perpendicular to L, nearest the second PCA axis)
        B1 = _unit(B1 - L * (B1 * L).sum(1, keepdims=True))
        bad_b = np.linalg.norm(B1, axis=1) < 0.5
        if bad_b.any():
            alt = np.cross(L[bad_b], np.array([0.0, 0.0, 1.0]))
            alt2 = np.cross(L[bad_b], np.array([1.0, 0.0, 0.0]))
            alt = np.where(np.linalg.norm(alt, axis=1, keepdims=True) > 0.3, alt, alt2)
            B1[bad_b] = _unit(alt)
        B2 = np.cross(L, B1)
        elong = w[:, 2] / np.maximum(w[:, 1], 1e-12)
        aspect = np.sqrt(np.maximum(w[:, 0], 0) / np.maximum(w[:, 1], 1e-12))
        rnd = (aspect > ROUND_ASPECT) & (elong > 2.25) & ~use_s
        st["round_pieces"] = int(rnd.sum())
        # per-piece texture offset (deterministic, from the piece position)
        ou = np.mod(cen @ np.array([0.37, 0.61, 0.53]) * 3.1, 4.0)
        ov = (cen * L).sum(1)
        # per-face frames
        gf = np.flatnonzero(grain)
        k = fpc[gf]
        nf = n[gf]
        ndl = (nf * L[k]).sum(1)
        end = np.abs(ndl) > END_COS
        # loop level
        gl = grain[lp]
        fl = lp[gl]
        pos = np.searchsorted(gf, fl)
        kl = fpc[fl]
        Q = P[gl] - cen[kl]
        # a box map in the piece's own PCA frame (L, B1, B2): V = along L; U = along B1 on the faces that face B2
        # (a board's broad faces) and along B2 on the faces that face B1 (its edges); end grain = (B1, B2).  U is
        # then continuous over each side even on adze-scalloped or warped faces (a per-face U breaks the grain
        # lines at every facet)
        q1 = (Q * B1[kl]).sum(1)
        q2 = (Q * B2[kl]).sum(1)
        face_b2 = np.abs((nf * B2[k]).sum(1)) >= np.abs((nf * B1[k]).sum(1))
        Ul = np.where(end[pos], q1, np.where(face_b2[pos], q1, q2))
        Vl = np.where(end[pos], q2, (Q * L[kl]).sum(1))
        # round pieces: U = mean radius x angle round the axis on the side faces
        rl = rnd[kl] & ~end[pos]
        if rl.any():
            x1 = (Q * B1[kl]).sum(1)
            x2 = (Q * B2[kl]).sum(1)
            th = np.arctan2(x2, x1)
            rad = np.hypot(x1, x2)
            rbar = np.zeros(K)
            rc = np.zeros(K)
            np.add.at(rbar, kl[rl], rad[rl])
            np.add.at(rc, kl[rl], 1.0)
            rbar /= np.maximum(rc, 1)
            # faces straddling the +-pi seam: lift their negative angles by 2 pi
            fmax = np.full(len(ls), -10.0)
            fmin = np.full(len(ls), 10.0)
            np.maximum.at(fmax, fl[rl], th[rl])
            np.minimum.at(fmin, fl[rl], th[rl])
            wrap = (fmax - fmin)[fl] > np.pi
            th = np.where(wrap & (th < 0), th + 2 * np.pi, th)
            Ul = np.where(rl, rbar[kl] * th, Ul)
        # shingle / shake faces and sloped timber sheets: height mode (see above)
        rf = hmode[k]
        if rf.any():
            hz = np.cross(np.array([0.0, 0.0, 1.0]), nf)
            hl_ = np.linalg.norm(hz, axis=1, keepdims=True)
            hb = B1[k] - nf * (nf * B1[k]).sum(1, keepdims=True)
            h_f = np.where(hl_ > 0.1, hz / np.maximum(hl_, 1e-30), _unit(hb))
            rl_ = rf[pos]
            Ul = np.where(rl_, (Q * h_f[pos]).sum(1), Ul)
            Vl = np.where(rl_, Q[:, 2] / kpc[kl], Vl)
            ov = np.where(hmode, cen[:, 2] / kpc, ov)
        uv[gl, 0] = Ul + ou[kl]
        uv[gl, 1] = Vl + ov[kl]
        st["grain_faces"] = int(len(gf))
    # ---- 2. collapsed faces: nearest rigid map at 1 UV / m
    ok3 = (lt >= 3) & (area > 1e-10)
    l0, l1, l2 = ls, ls + np.minimum(1, lt - 1), ls + np.minimum(2, lt - 1)
    e1, e2 = co[lv[l1]] - co[lv[l0]], co[lv[l2]] - co[lv[l0]]
    d1, d2 = uv[l1] - uv[l0], uv[l2] - uv[l0]
    a3 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
    a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    r_first = a2 / np.maximum(a3, 1e-12)
    # whole-face UV area (shoelace) / 3D area
    nxt = np.arange(nl) + 1
    nxt[ls + lt - 1] = ls
    sh = np.zeros(len(ls))
    np.add.at(sh, lp, uv[:, 0] * uv[nxt, 1] - uv[nxt, 0] * uv[:, 1])
    r_face = 0.5 * np.abs(sh) / np.maximum(area, 1e-12)
    bad = ok3 & ((r_first < FIX_RATIO) & (a3 > 1e-10) | (r_face < FIX_RATIO))
    if bad.any():
        bf = np.flatnonzero(bad)
        nb_ = n[bf]
        up = np.array([0.0, 0.0, 1.0]) - nb_ * nb_[:, 2:3]
        alt = np.array([0.0, 1.0, 0.0]) - nb_ * nb_[:, 1:2]
        bb = np.where(np.linalg.norm(up, axis=1, keepdims=True) > 0.3, up, alt)
        bb = _unit(bb)
        aa = _unit(np.cross(bb, nb_))
        bl = bad[lp]
        fl = lp[bl]
        pos = np.searchsorted(bf, fl)
        pc_ = np.zeros((len(ls), 3))
        np.add.at(pc_, lp, co[lv])
        pc_ /= lt[:, None]
        uc_ = np.zeros((len(ls), 2))
        np.add.at(uc_, lp, uv)
        uc_ /= lt[:, None]
        X = np.stack([((P[bl] - pc_[fl]) * aa[pos]).sum(1), ((P[bl] - pc_[fl]) * bb[pos]).sum(1)], 1)
        Y = uv[bl] - uc_[fl]
        YX = np.zeros((len(bf), 2, 2))
        np.add.at(YX, pos, Y[:, :, None] * X[:, None, :])
        Us, S, Vt = np.linalg.svd(YX)
        Rm = Us @ Vt
        zero = S[:, 0] < 1e-9
        Rm[zero] = np.eye(2)
        uv[bl] = uc_[fl] + np.einsum("lij,lj->li", Rm[pos], X)
        st["collapsed_fixed"] = int(len(bf))
    uvl.data.foreach_set("uv", uv.astype(np.float32).ravel())
    return st


def finish_uvs(objects, log=None):
    """regrain_mesh on every mesh among `objects` (each mesh datablock once, in the frame of its first user by
    name).  Returns {mesh name: stats}."""
    first = {}
    for o in sorted((o for o in objects if o.type == "MESH"), key=lambda o: o.name):
        first.setdefault(o.data.name, o)
    out = {}
    for nm in sorted(first):
        o = first[nm]
        out[nm] = regrain_mesh(o.data, np.array(o.matrix_world))
    if log:
        tot = {k: sum(s[k] for s in out.values())
               for k in ("grain_faces", "pieces", "round_pieces", "sheet_pieces", "collapsed_fixed")}
        log(f"uv grain (kit 1.10.0): {len(out)} meshes, {tot['pieces']} timber / shingle pieces "
            f"({tot['round_pieces']} round, {tot['sheet_pieces']} sloped sheets), {tot['grain_faces']} grain faces "
            f"re-projected, "
            f"{tot['collapsed_fixed']} collapsed faces repaired")
    return out


def entrances_record(ents):
    """JSON-safe copy of guards entrance dicts (origin, out, width, head, name) for the scene property."""
    rec = []
    for e in ents or []:
        o = np.asarray(e["origin"], float)
        if o.shape == (2,):
            o = np.array([o[0], o[1], 0.0])
        rec.append(dict(name=str(e["name"]), origin=[round(float(x), 5) for x in o],
                        out=[round(float(x), 6) for x in np.asarray(e["out"], float)[:3]],
                        width=round(float(e["width"]), 5), head=round(float(e["head"]), 5)))
    return rec


def store_entrances(rec):
    import bpy
    bpy.context.scene["kit_entrances"] = json.dumps(rec)


def finish_building(objects, entrances, log=None):
    """kit 1.10.0, run by build_building / build_compound on the finished building (UV + Mask only):
    finish_uvs (grain + collapsed), mask.clear_walked_tops on every entrance's walking zone (world coordinates),
    and the entrances recorded as the scene property `kit_entrances` (JSON; tools/uv_audit.py reads it)."""
    from . import mask
    objects = list(objects)
    st = finish_uvs(objects, log=log)
    rec = entrances_record(entrances)
    walked = mask.clear_walked_tops(objects, rec, log=log)
    store_entrances(rec)
    return st, walked
