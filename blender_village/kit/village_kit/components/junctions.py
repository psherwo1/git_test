"""components.junctions -- junction pieces between bodies of DIFFERENT module families (kit 1.7.0 candidate, v4_mixed).

They run as compound junction steps fn(c, ...) (village_kit.compound) after every wing is placed, read the placed
geometry / frames of the wings they join and build their own objects <junction prefix>_<part> in world coordinates.
The body descriptions are generic -- a round TOWER is (centre, outer face radius R(z)), a ROOF is a set of placed
roof objects ray-cast from above, a round WALL is (centre, face radius) -- so the same pieces close a hut cone
against a mill drum, a drum against an octagonal hall's turret, a cone against a keep cone, etc.  Adapters read
them from the family frames (tower_of / round_wall_of).

    roof_tower_flashing(c, roof, tower, ...)   where a roof runs INTO a round masonry tower: the true roof-top /
        tower-face intersection is traced by ray casts on the built roofing and closed with the keep family's
        flaunching language (components.thatch.flaunch_loop: a lime-mortar fillet where the line is flatter than
        `steep_deg`, stepped lead flashing tucked into the bed joints where it is steeper); the run's ends are
        dressed down over the cut eave lip with a lead end-apron (wall_end_apron) so no shingle edge shows against
        the stone -> <P>_<name>_fillet (M_mortar / M_lead)
    wall_end_apron(acc, P_end, out_n, along, drop, ...)   the lead plate on a wall face where a cut eave lip meets
        it; kit 1.8.0: renamed from end_apron (deprecated alias kept), roof_junction.cone_nose_apron is the cone piece
    wall_tower_abutment(c, wall, tower, ...)   where a round post-and-infill wall runs into a round masonry tower: a
        hewn abutment post (components.hewn.hewn_square, the keep family's square timber) on each side, its drum
        half let into the masonry, covering the daub / stone seam from the plinth to the wall plate, with a mortar
        bead pointing the post / stone seam -> <P>_<name>_posts (M_timber), <P>_<name>_pointing (M_mortar)

Decal anchors (producer note 11) for the junction: moss in the roof valley against the tower (debris collects
there) and damp rising at the abutment-post feet -- added to c.decals and audited with the whole building.
"""
import math

import numpy as np

from ..core import log


# =================================================================================================================
# body adapters (family frame -> generic description in world coordinates)
# =================================================================================================================
def tower_of(c, name):
    """a placed DrumFrame wing as a round tower: centre (x, y) and the outer face radius R(z) (battered drum)."""
    from .drum_frame import R_out
    w = c.wing(name)
    g = w.g
    return dict(center=w.center[:2], R=lambda z, g=g: np.asarray(R_out(g, np.asarray(z, float)), float),
                z_top=float(g.Z_CORN0), name=name)


def round_wall_of(c, name):
    """a placed RoundFrame wing as a round post-and-infill wall: centre, wattle line, coat face, plinth top, plate."""
    w = c.wing(name)
    g = w.g
    return dict(center=w.center[:2], r_line=float(g.R_WALL), r_coat=float(g.R_WALL + g.COAT_R_NOM),
                z0=float(g.PLINTH_TOP), z_plate=float(g.PLATE_BOT), z_plate_top=float(g.PLATE_TOP), name=name)


def _bvh(objs):
    from mathutils.bvhtree import BVHTree
    V, T, nv = [], [], 0
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", lt)
        V.append(co)
        T.append(lt.reshape(-1, 3) + nv)
        nv += len(co)
    V = np.concatenate(V)
    T = np.concatenate(T)
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)


def _down(bvh, x, y, z_from=40.0):
    from mathutils import Vector
    hit = bvh.ray_cast(Vector((float(x), float(y), z_from)), Vector((0.0, 0.0, -1.0)), z_from + 1.0)
    return None if hit[0] is None else float(hit[0][2])


# =================================================================================================================
# roof into a round tower
# =================================================================================================================
def trace_roof_on_tower(bvh, tower, offsets=(0.006, 0.02), step_deg=0.5, z_guess=3.0):
    """the line where the roof top meets the tower face: for every azimuth round the tower centre the highest
    roof-top hit just outside the face (R(z) + offsets), iterated for the batter.  Returns the contiguous runs
    [(theta (n,), P (n, 3))] (theta = math angle about the tower centre)."""
    C = np.asarray(tower["center"], float)
    th = np.radians(np.arange(0.0, 360.0, step_deg))
    Z = np.full(len(th), np.nan)
    for i, t in enumerate(th):
        d = np.array([math.cos(t), math.sin(t)])
        z = z_guess
        zz = None
        for _ in range(3):
            hs = []
            for off in offsets:
                r = float(tower["R"](z)) + off
                h = _down(bvh, C[0] + d[0] * r, C[1] + d[1] * r)
                if h is not None:
                    hs.append(h)
            if not hs:
                zz = None
                break
            zz = max(hs)
            z = zz
        if zz is not None:
            Z[i] = zz
    ok = np.isfinite(Z)
    if not ok.any():
        return []
    # close short misses (a ray slipping through a shingle joint) by interpolation: <= max_gap samples
    max_gap = max(2, int(round(3.0 / step_deg)))
    n_ = len(Z)
    i = 0
    while i < n_:
        if ok[i]:
            i += 1
            continue
        j = i
        while j < n_ and not ok[j]:
            j += 1
        a, b = i - 1, j % n_
        if j - i <= max_gap and ok[a % n_] and ok[b] and (i > 0 or ok[-1]):
            za, zb = Z[a % n_], Z[b]
            for k_ in range(i, j):
                f = (k_ - a) / (j - a)
                Z[k_] = za * (1 - f) + zb * f
        i = j
    ok = np.isfinite(Z)
    if ok.all():
        raise ValueError("roof covers the whole tower: not a roof-into-tower junction")
    # contiguous runs on the circle
    k0 = int(np.flatnonzero(~ok)[0])
    order = np.roll(np.arange(len(th)), -k0)
    runs, cur = [], []
    for i in order:
        if ok[i]:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    out = []
    for r_ in runs:
        if len(r_) < 4:
            continue
        idx = np.array(r_)
        t_ = np.unwrap(th[idx])
        z_ = Z[idx]
        rr = np.array([float(tower["R"](zv)) for zv in z_])
        P = np.stack([C[0] + rr * np.cos(t_), C[1] + rr * np.sin(t_), z_], 1)
        out.append((t_, P))
    return out


def _smooth_up(z, n_max=3, n_avg=4):
    """upper envelope (running max over +-n_max samples) then a light smoothing: the line rides on the shingle tops."""
    z = np.asarray(z, float)
    m = np.array([z[max(0, i - n_max):i + n_max + 1].max() for i in range(len(z))])
    for _ in range(n_avg):
        m[1:-1] = 0.25 * m[:-2] + 0.5 * m[1:-1] + 0.25 * m[2:]
    return np.maximum(m, z)


def wall_end_apron(acc, P_end, out_n, along, drop, w=0.16, t=0.004, proud=0.025, turn=0.05, closed_lip=False):
    """kit 1.8.0: renamed from junctions.end_apron (roof_junction.end_apron is a different piece, now
    roof_junction.cone_nose_apron); `end_apron` stays here as a deprecated alias.
    lead end-apron where a roof's cut eave lip meets a wall: a plate on the wall face from just above the roof
    line down over the lip (`drop`), `w` wide toward the roof, its lower edge turned out `turn` under the lip.
    closed_lip=True (kit v4 r3, director v4 r2 must-fix 1): the drip lip is a CLOSED bent strip with its own
    vertices (top, bottom and both end caps), tucked 3 mm up into the plate's bottom edge instead of welded onto
    it, so the plate and the lip are each closed (0 non-manifold edges); False keeps the r2 open folded strip."""
    n = np.asarray(out_n, float)
    n = n / np.linalg.norm(n)
    a = np.asarray(along, float)
    a = a - n * (a @ n)
    a[2] = 0.0
    a = a / (np.linalg.norm(a) + 1e-9)
    z = np.array([0.0, 0.0, 1.0])
    P = np.asarray(P_end, float)
    # plate: u along a (0..w), v down (0..drop+0.06), thickness t standing proud of the face
    us = np.linspace(-0.03, w, 5)
    vs = np.linspace(-0.06, drop, 6)
    U, Vv = np.meshgrid(us, vs, indexing="ij")
    base = P[None, None] + a[None, None] * U[..., None] - z[None, None] * Vv[..., None]
    F0 = base + n * proud
    F1 = base + n * (proud + t)
    # turned-out lower edge
    nu, nv = U.shape
    from ..core import grid_quads
    Vf = np.concatenate([F1.reshape(-1, 3), F0.reshape(-1, 3)])
    q_out = grid_quads(nu, nv)
    q_in = grid_quads(nu, nv, nu * nv)[:, ::-1]
    # side walls (close the plate)
    ii = np.arange(nu)
    jj = np.arange(nv)
    o = nu * nv
    sides = []
    for j0 in (0, nv - 1):
        for i in range(nu - 1):
            a0, b0 = ii[i] * nv + j0, ii[i + 1] * nv + j0
            sides.append([a0, b0, b0 + o, a0 + o] if j0 == 0 else [b0, a0, a0 + o, b0 + o])
    for i0 in (0, nu - 1):
        for j in range(nv - 1):
            a0, b0 = i0 * nv + jj[j], i0 * nv + jj[j + 1]
            sides.append([b0, a0, a0 + o, b0 + o] if i0 == 0 else [a0, b0, b0 + o, a0 + o])
    acc.add(Vf, [q_out, q_in, np.array(sides)], "M_lead")
    # drip lip: a small rolled bead along the bottom edge, turned out
    bot = base[:, -1] + n * proud
    if closed_lip:
        # closed section (n out, z up, relative to the plate's bottom edge): root tucked into the plate, tip turned
        # out and down; swept along the edge, quads round the ring, a cap at each end
        prof = [(0.0012, 0.003), (turn, -0.012), (turn, -0.012 - t), (0.0012, -t)]
        m_ = len(bot)
        ring = np.stack([bot + n * dn + z * dz for dn, dz in prof], 1)          # (m_, 4, 3)
        quads = []
        for i in range(m_ - 1):
            for k in range(4):
                k1 = (k + 1) % 4
                quads.append([i * 4 + k, i * 4 + k1, (i + 1) * 4 + k1, (i + 1) * 4 + k])
        caps = np.array([[3, 2, 1, 0], [(m_ - 1) * 4 + k for k in range(4)]])
        acc.add(ring.reshape(-1, 3), [np.array(quads), caps], "M_lead")
        return
    lip = np.concatenate([bot, bot + n * turn - z * 0.012, bot + n * turn - z * 0.012 - z * t,
                          bot - z * t])
    m_ = len(bot)
    quads = []
    for k in range(3):
        for i in range(m_ - 1):
            quads.append([k * m_ + i, k * m_ + i + 1, (k + 1) * m_ + i + 1, (k + 1) * m_ + i])
    acc.add(lip, [np.array(quads)[:, ::-1]], "M_lead")


end_apron = wall_end_apron
"""deprecated alias (kit 1.8.0): use wall_end_apron."""


# parts of a RoundFrame roof wing that are trimmed at the tower face (structure first, then the roofing)
ROOF_TRIM_PARTS = (("rafters", 0.02), ("purlin_rings", 0.02), ("battens", 0.02), ("wall_plate", 0.03),
                   ("eave_closure", 0.02), ("roof_blocker", 0.03), ("roof_starter", 0.03), ("roof_shingles", 0.035),
                   ("roof_underlap", 0.035))


def tower_field(T, P):
    """signed plan distance of points P (n, 3) from a round tower's face R(z): > 0 outside, < 0 in the masonry."""
    P = np.asarray(P, float)
    C = np.asarray(T["center"], float)
    return np.hypot(P[:, 0] - C[0], P[:, 1] - C[1]) - np.asarray(T["R"](P[:, 2]), float)


def clip_at_tower(ob, T, inset=0.02, z_range=None):
    """TRIM (not bury) a placed single-user mesh object at the surface R(z) - inset of a round tower: every edge
    that crosses it is split exactly there (bmesh.bisect_edges interpolates UVs and the Mask corner colours), the
    crossed faces are split along the cut, and everything inside is deleted -- an open cut `inset` m inside the
    masonry, so a pole, batten, board or shingle stops AT the stone face instead of running on into it.  Only
    vertices with z in z_range (default: any) count as inside.  Returns the number of faces removed."""
    import bmesh
    from mathutils import Matrix
    if ob is None or ob.type != "MESH" or ob.data.users > 1:
        return 0
    if ob.matrix_world != Matrix.Identity(4):
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix.Identity(4)
    me = ob.data
    nv = len(me.vertices)
    if nv == 0:
        return 0
    co = np.zeros(nv * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    f = tower_field(T, co) + inset
    if z_range is not None:
        f = np.where((co[:, 2] >= z_range[0]) & (co[:, 2] <= z_range[1]), f, np.abs(f) + 1.0)
    if (f >= 0).all():
        return 0
    n_f0 = len(me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.verts.layers.float.new("_clip_f")
    bm.verts.ensure_lookup_table()
    for v, fv in zip(bm.verts, f):
        v[lay] = float(fv)
    cross = [e for e in bm.edges if (e.verts[0][lay] < 0) != (e.verts[1][lay] < 0)
             and e.verts[0][lay] != 0 and e.verts[1][lay] != 0]
    if cross:
        new_v = []
        for e in cross:
            v0, v1 = e.verts
            f0, f1 = v0[lay], v1[lay]
            c0, c1 = v0.co.copy(), v1.co.copy()
            # the field is far from linear along a long edge at a grazing angle: bisect on the true surface
            a0, a1 = np.array(c0), np.array(c1)
            lo_, hi_ = 0.0, 1.0
            for _ in range(24):
                m_ = 0.5 * (lo_ + hi_)
                fm = float(tower_field(T, (a0 + (a1 - a0) * m_)[None])[0]) + inset
                if (fm < 0) == (f0 < 0):
                    lo_ = m_
                else:
                    hi_ = m_
            p = float(np.clip(0.5 * (lo_ + hi_), 1e-4, 1 - 1e-4))
            _, nv_ = bmesh.utils.edge_split(e, v0, p)              # loop data (UV, Mask) interpolated
            nv_.co = c0 + (c1 - c0) * p                             # exactly on the cut, whatever fac means
            nv_[lay] = 0.0
            new_v.append(nv_)
        if new_v:
            bmesh.ops.connect_verts(bm, verts=new_v, check_degenerate=False)
    inside = [fc for fc in bm.faces if max(v[lay] for v in fc.verts) <= 1e-9]
    if inside:
        bmesh.ops.delete(bm, geom=inside, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.verts.layers.float.remove(lay)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n_f0 - len(me.polygons) + 0


def trim_wing_at_tower(c, wing, tower, parts=ROOF_TRIM_PARTS, z_range=None):
    """JUNCTION STEP: trim the named parts [(part, inset)] of a placed wing at a placed round tower's face (see
    clip_at_tower).  Usable on its own for any wing whose pieces run into a tower."""
    w = c.wing(wing)
    T = tower_of(c, tower) if isinstance(tower, str) else tower
    out = {}
    for part, inset in parts:
        ob = next((o for o in w.meshes() if o.name == f"{w.prefix}_{part}"), None)
        if ob is None:
            continue
        n0 = len(ob.data.polygons)
        clip_at_tower(ob, T, inset, z_range)
        out[part] = (n0, len(ob.data.polygons))
    log("  trim at tower face: " + ", ".join(f"{k} {a}->{b}" for k, (a, b) in out.items() if a != b))
    return out


def _env(z, n_max=3, n_avg=4):
    """upper envelope + smoothing that ignores NaN (missing hits stay NaN)."""
    z = np.asarray(z, float)
    ok = np.isfinite(z)
    if not ok.any():
        return z
    zz = np.where(ok, z, -1e9)
    m = np.array([zz[max(0, i - n_max):i + n_max + 1].max() for i in range(len(z))])
    m = np.where(m < -1e8, np.nan, m)
    f = np.isfinite(m)
    if f.sum() >= 2:
        idx = np.arange(len(m))
        m = np.interp(idx, idx[f], m[f])
    for _ in range(n_avg):
        m[1:-1] = 0.25 * m[:-2] + 0.5 * m[1:-1] + 0.25 * m[2:]
    return np.maximum(m, np.where(ok, z, -1e9))


def ride_fillet(acc, th, zb, T, bvh, h_up=0.10, out=0.11, lift=0.05, bury=0.035, taper=0.30, cove=0.012):
    """lime-mortar flaunching that READS (director v4 r1 must-fix 2): a fillet whose section is fitted to the roofing
    it lies on, sampled by ray casts along the tower's outward normal -- so where the roof RISES away from the wall
    (the upslope side of a cone running into a tower, a 39 deg valley) it fills the valley instead of sinking under
    the shingles.  Per station: the back buried `bury` in the masonry; a hard crease h_up over the highest roofing
    at the face; a cove down to a toe `out` m out over the roofing, standing `lift` m over the highest butt peak
    there (a visible mortar edge); the skirt drops 3 cm into the course under the toe.  Both ends taper over `taper`
    m.  th (n,) tower-centred angles, zb (n,) roof top at the face (upper envelope)."""
    C = np.asarray(T["center"], float)
    n = len(th)
    nrm_ = np.stack([np.cos(th), np.sin(th)], 1)
    ds = (0.01, 0.035, 0.6 * out, out, out + 0.02)
    Z = np.full((n, len(ds)), np.nan)
    for i in range(n):
        R_ = float(T["R"](zb[i]))
        for k, d in enumerate(ds):
            q = C + nrm_[i] * (R_ + d)
            Z[i, k] = np.nan if (h := _down(bvh, q[0], q[1])) is None else h
    for k in range(len(ds)):
        Z[:, k] = _env(Z[:, k])
        Z[:, k] = np.where(np.isfinite(Z[:, k]), Z[:, k], zb)
    # arc length along the run, taper factor
    P0 = np.column_stack([C[0] + nrm_[:, 0] * T["R"](zb), C[1] + nrm_[:, 1] * T["R"](zb), zb])
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P0, axis=0), axis=1))])
    tf = np.clip(np.minimum(s, s[-1] - s) / max(taper, 1e-3), 0, 1)
    tf = 0.35 + 0.65 * np.sqrt(tf * (2 - tf))
    face = np.maximum(zb, Z[:, 0])
    z_toe = np.maximum(Z[:, 3], Z[:, 4]) + lift * tf
    z_cr = np.maximum(face + h_up * tf, z_toe + 0.03)
    o = out * tf
    low = np.minimum(Z.min(1), zb) - 0.06
    prof = np.stack([
        np.stack([np.full(n, -bury), z_cr + 0.015], 1),                  # back, in the bed joint above
        np.stack([np.full(n, 0.004), z_cr], 1),                          # hard crease on the stone
        np.stack([0.55 * o, 0.5 * (z_cr + z_toe) - cove * tf], 1),       # cove
        np.stack([o, z_toe], 1),                                         # toe edge over the butt peaks
        np.stack([o + 0.012, np.minimum(Z[:, 4], Z[:, 3]) - 0.03], 1),    # skirt into the course
        np.stack([0.4 * o, low], 1),
        np.stack([np.full(n, -bury), low], 1),
    ], 1)                                                                # (n, 7, [d, z])
    for _ in range(3):                                                   # no station-to-station jitter
        prof[1:-1] = 0.25 * prof[:-2] + 0.5 * prof[1:-1] + 0.25 * prof[2:]
    npf = prof.shape[1]
    Rz = np.asarray(T["R"](prof[..., 1]), float)
    V = np.stack([C[0] + nrm_[:, None, 0] * (Rz + prof[..., 0]), C[1] + nrm_[:, None, 1] * (Rz + prof[..., 0]),
                  prof[..., 1]], -1)
    ii = np.arange(n - 1)[:, None]
    jj = np.arange(npf)[None, :]
    a_ = ii * npf + jj
    b_ = ii * npf + (jj + 1) % npf
    quads = np.stack([a_, b_, b_ + npf, a_ + npf], -1).reshape(-1, 4)
    caps = [np.arange(npf)[::-1][None, :], ((n - 1) * npf + np.arange(npf))[None, :]]
    acc.add(V.reshape(-1, 3), [quads] + caps, "M_mortar")
    return dict(z_crease=z_cr, z_toe=z_toe, face=face, out=o)


def _corbel_meshes(c, tower):
    w = c.wing(tower)
    mes = []
    for o in w.objects():
        if o.type == "MESH" and o.name.startswith(f"{w.prefix}_corbel_") and o.data not in mes:
            mes.append(o.data)
    return sorted(mes, key=lambda m: m.name)


def pole_plate_ledger(c, th, zb, T, tower, name, section=(0.15, 0.20), drop=0.33, let_in=0.03, trim_end=0.10,
                      min_rise=0.0, n_corbels=None, corbel_bury=0.02, seed=2611):
    """hewn pole-plate / ledger on stone corbels under a roof that runs into a round tower (director v4 r1 must-fix
    1): the roof's rafters, cut at the tower face, bear on it.  It follows the traced roof line `drop` m under the
    roof top (its top under the rafters' feet), as straight hewn_square lengths (keep family) scarfed over 2-3
    corbels (the tower wing's pooled corbel meshes, linked duplicates), its back `let_in` m in the masonry.  The
    lowest `trim_end` m of each run end, and stations less than `min_rise` m over the run's lowest point (the eave
    lip, where only the lead end-apron belongs), are left out.  Objects <P>_<name>_ledger, <P>_<name>_corbel_###."""
    import bpy
    from mathutils import Matrix
    from .hewn import hewn_square
    C = np.asarray(T["center"], float)
    wy, wz = section
    P = np.column_stack([C[0] + np.cos(th) * T["R"](zb), C[1] + np.sin(th) * T["R"](zb), zb])
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    keep = (s > trim_end) & (s < s[-1] - trim_end) & (zb >= zb.min() + min_rise)
    if keep.sum() < 4:
        return None
    i0, i1 = np.flatnonzero(keep)[[0, -1]]
    ss = s[i0:i1 + 1]
    L = ss[-1] - ss[0]
    nc = n_corbels if n_corbels is not None else int(np.clip(round(L / 1.1), 2, 3))
    # stations: ends + joints over the corbels
    fr = np.concatenate([[0.0], (np.arange(nc) + 1) / (nc + 1), [1.0]])
    st = ss[0] + fr * L
    tt = np.interp(st, s, th)
    zt = np.interp(st, s, zb) - drop - wz / 2                      # ledger centre line
    rr = np.asarray(T["R"](zt), float) + wy / 2 - let_in
    Q = np.column_stack([C[0] + np.cos(tt) * rr, C[1] + np.sin(tt) * rr, zt])
    acc = c.acc(f"{name}_ledger", 40.0)
    rng = np.random.default_rng(seed)
    for k in range(len(Q) - 1):
        a, b = Q[k], Q[k + 1]
        EX = b - a
        Lk = float(np.linalg.norm(EX))
        EX = EX / Lk
        nmid = np.array([math.cos(0.5 * (tt[k] + tt[k + 1])), math.sin(0.5 * (tt[k] + tt[k + 1])), 0.0])
        EZ = np.cross(EX, nmid)
        EZ = EZ / np.linalg.norm(EZ)
        if EZ[2] < 0:
            EZ = -EZ
        EY = np.cross(EZ, EX)
        lap = 0.06 if 0 < k else 0.0                                  # scarfed over the corbel
        hewn_square(acc, a - EX * lap, EX, EY, EZ, Lk + lap + (0.06 if k < len(Q) - 2 else 0.0), wy, wz, rng,
                    mat="M_timber", chamfer=0.02, nf=2, st_len=0.12, adze=0.0, wave=0.004, seed=seed + k)
    c.finalize(acc, smooth_deg=40.0)
    # corbels under the joints
    mes = _corbel_meshes(c, tower)
    placed = []
    if mes:
        for j in range(1, len(Q) - 1):
            t_ = tt[j]
            nv = np.array([math.cos(t_), math.sin(t_), 0.0])
            xv = np.array([nv[1], -nv[0], 0.0])
            zc = Q[j, 2] - wz / 2 - 0.068
            p = np.array([C[0], C[1], 0.0]) + nv * (float(T["R"](zc)) - corbel_bury) + np.array([0, 0, zc])
            M = np.eye(4)
            M[:3, :3] = np.stack([xv, nv, [0, 0, 1.0]], 1)
            M[:3, 3] = p
            ob = bpy.data.objects.new(f"{c.prefix}_{name}_corbel_{j:03d}", mes[(j * 5 + seed) % len(mes)])
            ob.matrix_world = Matrix(M.tolist())
            c.coll.objects.link(ob)
            placed.append(ob)
    log(f"  {name}: ledger {len(Q) - 1} lengths, {L:.2f} m, z {Q[:, 2].min():.2f}..{Q[:, 2].max():.2f}, "
        f"{len(placed)} corbels")
    return dict(stations=Q, corbels=placed)


def _world_co(ob):
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(ob.matrix_world)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


def rafter_feet(ob, T, inset=0.02, tol=0.0015, link=0.08):
    """the cut feet of a rafter object trimmed at a round tower (clip_at_tower, `inset`): the vertices lying on the
    cut surface, clustered (single linkage, `link` m) into one foot per rafter.  Returns [(centroid (3,), z_min)]
    sorted by tower angle."""
    if ob is None or len(ob.data.vertices) == 0:
        return []
    P = _world_co(ob)
    on = np.flatnonzero(np.abs(tower_field(T, P) + inset) < tol)
    if len(on) == 0:
        return []
    Q = P[on]
    lab = np.arange(len(Q))

    def root(i):
        while lab[i] != i:
            lab[i] = lab[lab[i]]
            i = lab[i]
        return i
    D = np.linalg.norm(Q[:, None] - Q[None], axis=-1)
    for i, j in zip(*np.nonzero(np.triu(D < link, 1))):
        ri, rj = root(i), root(j)
        if ri != rj:
            lab[max(ri, rj)] = min(ri, rj)
    groups = {}
    for i in range(len(Q)):
        groups.setdefault(root(i), []).append(i)
    C = np.asarray(T["center"], float)
    feet = [(Q[g].mean(0), float(Q[g][:, 2].min())) for g in groups.values() if len(g) >= 3]
    feet.sort(key=lambda f: math.atan2(f[0][1] - C[1], f[0][0] - C[0]))
    return feet


def rafter_bearings(c, roof, tower, name, part="rafters", inset=0.02, pad=(0.40, 0.15, 0.11), let_in=0.03,
                    head_clear=0.05, ends=(), end_clear=0.0, corbel_bury=0.02, seed=2611):
    """STEPPED BEARING for the rafters of a roof that runs into a round tower (kit v4 r3; replaces the sloping
    pole_plate_ledger as roof_tower_flashing's default, director v4 r2 audit issue 1).  Every rafter foot cut at the
    tower face (rafter_feet) that lands OUTSIDE the roof wing's wall head -- where the wall plate does not carry it --
    gets its own short LEVEL hewn pad (keep family hewn_square, pad = length along the face, out from the face, height;
    back `let_in` m in the masonry) with its top at the rafter's underside at the stone face, on a stone corbel
    under its middle (a linked duplicate of the tower wing's pooled corbel meshes).  So the bearing steps down with
    the roof line, one level length per rafter, every visible end has a corbel under it, and nothing slopes.
    Feet whose pad would reach the wall head (the wall plate / eave closure / abutment posts, `head_clear` m) bear
    on the wall plate and get nothing; so do feet within `end_clear` m (along the face) of a point in `ends` (the
    lead end-aprons).  Objects <P>_<name>_pads (M_timber), <P>_<name>_corbel_###.  Returns the placed bearings."""
    import bpy
    from mathutils import Matrix
    from .hewn import hewn_square
    rw = c.wing(roof)
    T = tower_of(c, tower) if isinstance(tower, str) else tower
    C = np.asarray(T["center"], float)
    H = np.asarray(rw.center[:2], float)
    ob = next((o for o in rw.meshes() if o.name == f"{rw.prefix}_{part}"), None)
    feet = rafter_feet(ob, T, inset)
    # the wall head's outer plan radius about the roof centre (plate, eave closure, post faces)
    r_head = 0.0
    for p_ in ("wall_plate", "eave_closure"):
        o_ = next((o for o in rw.meshes() if o.name == f"{rw.prefix}_{p_}"), None)
        if o_ is not None and len(o_.data.vertices):
            Pw = _world_co(o_)
            r_head = max(r_head, float(np.hypot(Pw[:, 0] - H[0], Pw[:, 1] - H[1]).max()))
    try:
        Wl = round_wall_of(c, roof)
        r_head = max(r_head, Wl["r_line"] + 0.15)          # abutment post outer faces (wall_tower_abutment)
    except Exception:  # noqa: BLE001 -- not a RoundFrame wing: plate / closure only
        pass
    Pr = _world_co(ob) if feet else np.zeros((0, 3))
    fr = tower_field(T, Pr) if feet else np.zeros(0)
    mes = _corbel_meshes(c, tower)
    acc = c.acc(f"{name}_pads", 40.0)
    rng = np.random.default_rng(seed)
    L, wy, wz = pad
    out = []
    skipped = 0
    for k, (q, zc) in enumerate(feet):
        th = math.atan2(q[1] - C[1], q[0] - C[0])
        nv = np.array([math.cos(th), math.sin(th), 0.0])
        tv = np.array([-nv[1], nv[0], 0.0])
        Rz = float(T["R"](zc))
        f_face = C + nv[:2] * Rz                                       # plan point on the stone face
        # pad footprint must stay clear of the wall head and the end aprons
        corners = [f_face + nv[:2] * dn + tv[:2] * dt for dn in (-let_in, wy - let_in) for dt in (-L / 2, L / 2)]
        if min(float(np.linalg.norm(p_ - H)) for p_ in corners) < r_head + head_clear:
            skipped += 1
            continue
        if any(float(np.linalg.norm(np.asarray(e, float)[:2] - f_face)) < end_clear for e in ends):
            skipped += 1
            continue
        # the rafter's underside AT the stone face: from the cut (2 cm in) and its lowest vertex just outside
        near = (np.linalg.norm(Pr - q, axis=1) < 0.40) & (fr > 0.005) & (fr < 0.22)
        z_face = zc
        if near.any():
            i1 = np.flatnonzero(near)[np.argmin(Pr[near, 2])]
            kz = (Pr[i1, 2] - zc) / (fr[i1] + inset)
            z_face = zc + max(kz, 0.0) * inset
        z_top = z_face - 0.004
        zm = z_top - wz / 2
        O = np.array([f_face[0], f_face[1], zm]) + nv * (wy / 2 - let_in) - tv * (L / 2)
        hewn_square(acc, O, tv, nv, np.array([0.0, 0.0, 1.0]), L, wy, wz, rng, mat="M_timber", chamfer=0.018,
                    nf=2, st_len=0.08, adze=0.0, wave=0.003, seed=seed + k)
        rec = dict(foot=q, z_top=z_top, theta=th)
        if mes:
            zc_ = z_top - wz - 0.073                                   # corbel origin: its top under the pad
            p = np.array([C[0], C[1], 0.0]) + nv * (float(T["R"](zc_)) - corbel_bury) + np.array([0, 0, zc_])
            M = np.eye(4)
            M[:3, :3] = np.stack([np.array([nv[1], -nv[0], 0.0]), nv, [0, 0, 1.0]], 1)
            M[:3, 3] = p
            cb = bpy.data.objects.new(f"{c.prefix}_{name}_corbel_{len(out) + 1:03d}", mes[(k * 5 + seed) % len(mes)])
            cb.matrix_world = Matrix(M.tolist())
            c.coll.objects.link(cb)
            rec["corbel"] = cb
        out.append(rec)
    c.finalize(acc, smooth_deg=40.0)
    log(f"  {name}: {len(feet)} rafter feet at the tower face, {len(out)} level pads on corbels "
        f"(z {', '.join(f'{r_['z_top']:.2f}' for r_ in out)}), {skipped} carried by the wall plate / under an apron")
    return out


def roof_tower_flashing(c, roof, tower, roof_parts=("roof_shingles", "roof_starter"), name="roof_tower",
                        steep_deg=50.0, bury=0.035, lift=0.05, mortar_only=True, end_aprons=True, seed=2601,
                        decals=True, ledger=True, trim=True, section="ride", fillet=(0.10, 0.11), ledger_kw=None,
                        apron=(0.20, 0.24), bearing="corbels", bearing_kw=None, apron_closed=True):
    """JUNCTION: a placed roof (wing `roof`, its roofing objects roof_parts) runs into a placed round masonry tower
    (wing `tower`).  Traces the true roof-top / tower-face line (by ray casts on the built roofing), then
    (kit 1.7 r2 defaults, director v4 r1 must-fixes 1-2):
      trim=True     every structural part and the roofing of the roof wing is TRIMMED at the tower face
                    (trim_wing_at_tower / ROOF_TRIM_PARTS: rafters, rings, battens, plate, eave closure, blocker,
                    starter, shingles) -- nothing runs on into the stone;
      ledger=True   the cut rafter feet get a bearing: bearing="corbels" (kit v4 r3 default) -> rafter_bearings, a
                    level hewn pad on a stone corbel under every foot outside the wall head (stepped with the roof
                    line, nothing sloping, nothing through the wall head); bearing="ledger" -> the r2 sloping
                    pole_plate_ledger on 2-3 corbels;
      section       "ride": a mortar fillet fitted to the roofing (ride_fillet: fillet = (h_up, out), toe `lift`
                    over the butt peaks) that reads at 10 m; "flaunch": the keep family's thatch.flaunch_loop
                    (mortar_only=False -> stepped lead where steeper than steep_deg), lifted `lift`;
      end_aprons    a lead end-apron (apron = width, drop) over each cut eave lip, starter course and closure.
    Object <P>_<name>_fillet (+ _ledger, _corbel_###).  Returns the traced runs."""
    from .thatch import flaunch_loop
    rw = c.wing(roof)
    T = tower_of(c, tower)
    objs = [o for o in rw.meshes() if any(o.name == f"{rw.prefix}_{p}" for p in roof_parts)]
    if not objs:
        raise ValueError(f"no roofing objects {roof_parts} in wing {roof}")
    bvh = _bvh(objs)
    runs = trace_roof_on_tower(bvh, T, z_guess=float(getattr(rw.g, "Z_EAVE", 3.0)) + 0.5)
    if trim and runs:
        zlo = min(float(P[:, 2].min()) for _, P in runs) - 0.8
        trim_wing_at_tower(c, roof, T, z_range=(zlo, float(T["z_top"])))
    acc = c.acc(f"{name}_fillet")
    C = np.asarray(T["center"], float)
    g = rw.g
    ends = []
    for k, (th, P) in enumerate(runs):
        P = P.copy()
        zb = _smooth_up(P[:, 2])
        log(f"  {name}: run {k}: {len(P)} samples, azimuth {np.degrees(th[0]):.1f}..{np.degrees(th[-1]):.1f} deg, "
            f"z {zb.min():.2f}..{zb.max():.2f}")
        if section == "ride":
            ride_fillet(acc, th, zb, T, bvh, h_up=fillet[0], out=fillet[1], lift=lift, bury=bury)
        else:
            P[:, 2] = zb + lift
            flaunch_loop(acc, P, C, seed + 17 * k, steep_deg=steep_deg, mortar_only=mortar_only, bury=bury)
        if ledger and bearing == "ledger":
            pitch = float(getattr(g, "PITCH", math.radians(45.0)))
            stack = 0.07 + float(getattr(g, "BATTEN_T", 0.025)) + 2 * float(getattr(g, "RAFT_R", 0.055))
            kw = dict(drop=stack / math.cos(pitch) - 0.02)
            kw.update(ledger_kw or {})
            pole_plate_ledger(c, th, zb, T, tower, f"{name}_{k}" if len(runs) > 1 else name, seed=seed + 31 * k,
                              **kw)
        if end_aprons:
            # at each run end (the cut eave lip, the starter course and the eave closure against the stone) the
            # apron reaches apron[0] past the lip and apron[1] down
            Pe = P.copy()
            Pe[:, 2] = zb + 0.03
            for i0, i1 in ((0, 1), (-1, -2)):
                n_out = np.array([Pe[i0, 0] - C[0], Pe[i0, 1] - C[1], 0.0])
                wall_end_apron(acc, Pe[i0] + np.array([0, 0, 0.02]), n_out, Pe[i0] - Pe[i1], apron[1], w=apron[0],
                               closed_lip=apron_closed)
                ends.append(Pe[i0].copy())
        if decals:
            _roof_junction_decals(c, P, C, seed + k)
    if ledger and bearing != "ledger" and trim and runs:
        kw = dict(ends=ends)
        kw.update(bearing_kw or {})
        rafter_bearings(c, roof, tower, name, seed=seed + 10, **kw)
    c.finalize(acc, smooth_deg=35.0)
    c.__dict__.setdefault("junction_runs", {})[name] = runs
    if runs:
        # kit 1.9.0 (guard seal_probe): the roof runs into the tower -- registered on the compound for the generic
        # see-through probe after the whole-building cull (village_kit.guards; no geometry change)
        from ..guards import register_junction
        zs = np.concatenate([P[:, 2] for _, P in runs])
        register_junction(c, f"{roof} roof / {tower} tower", tuple(o.name for o in objs), C,
                          lambda z, R=T["R"]: float(R(z)), (float(zs.min()) - 0.3, float(zs.max()) + 0.3))
    return runs


def _roof_junction_decals(c, P, C, seed):
    """moss in the roof valley against the tower (debris collects there), 0.3 m out from the face on the shingles
    -- on the built surfaces (SurfaceProbe), audited later with the building."""
    from ..decals import SurfaceProbe
    probe = getattr(c, "_probe", None)
    if probe is None:
        probe = SurfaceProbe([o for w in c.wings.values() for o in w.meshes()])
        c._probe = probe
    rng = np.random.RandomState(seed)
    n = len(P)
    for f in (0.3, 0.5, 0.7):
        i = int(f * (n - 1))
        d = np.array([P[i, 0] - C[0], P[i, 1] - C[1], 0.0])
        d /= np.linalg.norm(d)
        q = P[i] + d * 0.30
        hit = probe.cast((q[0], q[1], q[2] + 1.5), (0, 0, -1), 3.0)
        c.decals.add_hit("moss", hit, (0.45, 0.35), probability=0.7, seed=int(rng.randint(1 << 30)),
                         surfaces={"M_roof_shingle"}, up=tuple(-d))


# =================================================================================================================
# round wall into a round tower
# =================================================================================================================
def _circle_x(c1, r1, c2, r2):
    """the two intersection points of two circles (plan)."""
    c1, c2 = np.asarray(c1, float), np.asarray(c2, float)
    d = float(np.linalg.norm(c2 - c1))
    if d > r1 + r2 or d < abs(r1 - r2):
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    e = (c2 - c1) / d
    p = c1 + a * e
    nrm = np.array([-e[1], e[0]])
    return [p + h * nrm, p - h * nrm]


def wall_tower_abutment(c, wall, tower, name="abutment", post=(0.22, 0.22), into=0.04, z_mid=1.2, seed=2701,
                        pointing=0.032, decals=True):
    """JUNCTION: a placed round post-and-infill wall (wing `wall`, RoundFrame) runs into a placed round masonry tower
    (wing `tower`).  At both plan intersections of the wall's coat face with the tower face (at z_mid) a hewn
    abutment post (post = section along / across the wall, m) stands on the plinth up to the wall plate, slid along
    the wall until its tower-side outer corner is `into` m inside the masonry, so it straddles the seam; a mortar
    bead (radius `pointing`) points the line where the post's outer face leaves the stone.  Objects
    <P>_<name>_posts, <P>_<name>_pointing."""
    from .hewn import hewn_square
    from ..core import tube
    Wl = round_wall_of(c, wall)
    T = tower_of(c, tower)
    H = np.asarray(Wl["center"], float)
    C = np.asarray(T["center"], float)
    Rt = float(T["R"](z_mid))
    pts = _circle_x(H, Wl["r_coat"], C, Rt)
    if not pts:
        log(f"  {name}: wall and tower do not meet")
        return []
    accp = c.acc(f"{name}_posts", 40.0)
    accm = c.acc(f"{name}_pointing", 50.0)
    rng = np.random.default_rng(seed)
    wy, wz = post
    z0, z1 = Wl["z0"] - 0.10, Wl["z_plate"] + 0.01
    r_c = Wl["r_line"] + 0.04               # post centre radius (outer face ~9 cm proud of the coat)
    placed = []
    for k, p in enumerate(pts):
        a0 = math.atan2(p[1] - H[1], p[0] - H[0])
        # which way along the wall is "into the tower"
        sgn = 1.0 if np.linalg.norm(H + Wl["r_coat"] * np.array([math.cos(a0 + 0.01), math.sin(a0 + 0.01)]) - C) \
            < np.linalg.norm(p - C) else -1.0

        def corner_in(a):
            n_ = np.array([math.cos(a), math.sin(a)])
            t_ = np.array([-n_[1], n_[0]]) * sgn
            q = H + n_ * (r_c + wz / 2) + t_ * (wy / 2)             # outer corner on the tower side
            return float(np.linalg.norm(q - C)) - float(T["R"](z_mid))
        lo, hi = a0 - sgn * 0.25, a0 + sgn * 0.25
        # bisection: corner_in(a) decreases moving toward the tower; find corner_in = -into
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            if corner_in(mid) > -into:
                lo = mid
            else:
                hi = mid
        a = 0.5 * (lo + hi)
        n3 = np.array([math.cos(a), math.sin(a), 0.0])
        t3 = np.array([-n3[1], n3[0], 0.0]) * sgn
        O = np.array([H[0] + n3[0] * r_c, H[1] + n3[1] * r_c, z0])
        hewn_square(accp, O, np.array([0, 0, 1.0]), t3, n3, z1 - z0, wy, wz, rng, mat="M_timber", chamfer=0.02,
                    nf=2, st_len=0.08, adze=0.0, wave=0.004, seed=seed + k)
        # the seam on the post's outer face: where that face line leaves the tower face
        def face_pt(s):
            return H + n3[:2] * (r_c + wz / 2) + t3[:2] * s
        s_lo, s_hi = -wy / 2, wy / 2
        for _ in range(40):
            sm = 0.5 * (s_lo + s_hi)
            if np.linalg.norm(face_pt(sm) - C) > float(T["R"](z_mid)):
                s_lo = sm
            else:
                s_hi = sm
        q = face_pt(0.5 * (s_lo + s_hi))
        zz = np.linspace(z0 + 0.06, z1 - 0.02, 24)
        path = []
        for zv in zz:
            # follow the batter: the seam point moves with R(z)
            s_lo, s_hi = -wy / 2, wy / 2
            Rz = float(T["R"](zv))
            for _ in range(30):
                sm = 0.5 * (s_lo + s_hi)
                if np.linalg.norm(face_pt(sm) - C) > Rz:
                    s_lo = sm
                else:
                    s_hi = sm
            qz = face_pt(0.5 * (s_lo + s_hi))
            path.append([qz[0], qz[1], zv])
        path = np.array(path)
        wob = 1.0 + 0.15 * np.sin(zz * 3.1 + k)
        Vt, Ft, uvt, wt = tube(path, pointing * wob, 8, up=tuple(n3))
        accm.add(Vt, Ft, "M_mortar", uvt, wt)
        placed.append(dict(center=O, normal=n3, along=t3))
        if decals:
            _post_decals(c, O, n3, t3, wy, wz, z0, seed + k)
        log(f"  {name}: post {k} at ({O[0]:.2f}, {O[1]:.2f}), seam {q.round(3).tolist()}")
    c.finalize(accp, smooth_deg=40.0)
    c.finalize(accm, smooth_deg=60.0)
    return placed


def _post_decals(c, O, n3, t3, wy, wz, z0, seed):
    """damp rising at the abutment post's foot (rain off the tower runs down the seam)."""
    from ..decals import SurfaceProbe
    probe = getattr(c, "_probe", None)
    if probe is None:
        probe = SurfaceProbe([o for w in c.wings.values() for o in w.meshes()])
        c._probe = probe
    p = np.array([O[0], O[1], 0.62]) - t3 * (wy * 0.15)
    hit = probe.cast(p + n3 * 0.4, -n3, 1.0)
    c.decals.add_hit("damp_rise", hit, (0.12, 0.40), probability=0.7, seed=seed, surfaces={"M_timber"})
