"""components.stone_body -- coursed-rubble BODIES of any plan, their openings and ledges (kit 1.7.0, v2_tiered_hall).

    stone_body(g, name, openings, clip_by, below, seed, cfg, coping)   KIT COMPONENT
        the coursed rubble of a declared tier_frame.Body (round or regular polygon, battered), laid by the keep's
        stone_wall.layout_wall / round_stone_wall (the kit's ONE stone generator), with
          * openings: door / window specs (opening(...)); the courses are cut round each opening's frame and the
            lintel / sill heights snap to the actual course beds, so frame and masonry close without a gap;
          * clip_by: bodies this one is engaged with (an engaged turret, a hall wall): stones and mortar inside
            them are dropped, so two bodies meet in one re-entrant masonry joint instead of interpenetrating;
          * below: a roof (bell_tier name) this body rises through: stones under the roof covering are dropped;
          * its own recessed mortar body (stone_wall.mortar_sheet), cut exactly round the openings and the clip
            bodies, refined near them;
          * coping=(z, r_in): a dressed coping ledge on the body top, closing it to an inner radius (a belt or a
            smaller body standing on it).
        Objects <P>_<name>_stones, <P>_<name>_mortar, <P>_<name>_coping.
    opening(kind, th_deg, width, height, sill=0.0, ...)                 an opening spec ('door' / 'window')
    framed_openings(g, seed)                                            KIT COMPONENT
        the timber frame of every published opening: jambs, a lintel let into the course above, a projecting
        stone sill with drip (windows), a dressed threshold (doors), a vertical plank leaf with strap hinges and
        nail heads (doors) or a mullioned frame with closed board shutters (windows), and a backing board, so no
        opening shows the hollow wall.  Objects <P>_openings_frame, _leaf, _iron, _sill, _backing.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, obox
from .stone_wall import mortar_sheet, round_map_factory, round_stone_wall

# default coursing (village rubble at the chunky scale; ~8-22 cm courses, 0.2-0.6 m stones)
RUBBLE_CFG = dict(footing=0.30, ch=(0.10, 0.19), p_tall=0.08, len=(0.22, 0.58), foot_len=(0.45, 1.05),
                  foot_lvl=(-0.08, 0.09), joint=(0.010, 0.020), front=(0.006, 0.032), foot_proj=(0.04, 0.09),
                  bevel=(0.008, 0.03), pillow=(0.003, 0.012), tilt=0.008, rot=0.014, p_double=0.07, p_long=0.05,
                  back=0.09, bed_amp=0.025)


def opening(kind, th_deg, width=1.0, height=2.10, sill=0.0, jamb=0.18, lintel_min=0.22, depth=0.34, proud=0.06,
            sill_h=0.12, threshold=0.10):
    """an opening spec for stone_body: kind 'door' (clear width x height above a `threshold` m threshold stone) or
    'window' (clear width x height above the sill height `sill`); th_deg = plan angle of the opening's centre."""
    return dict(kind=kind, th=math.radians(th_deg), width=width, height=height, sill=sill, jamb=jamb,
                lintel_min=lintel_min, depth=depth, proud=proud, sill_h=sill_h, threshold=threshold)


def _prep_openings(body, openings):
    ops = []
    for o in openings:
        o = dict(o)
        o["th"] = o["th"] % (2 * math.pi)
        if o["kind"] == "door":
            o["z_clear0"] = o["threshold"]
            o["z_bot"] = -10.0
        else:
            o["z_clear0"] = o["sill"]
            o["z_bot"] = o["sill"] - o["sill_h"]
        o["head"] = o["z_clear0"] + o["height"]
        o["hw"] = 0.5 * o["width"]
        o["hw_tot"] = o["hw"] + o["jamb"]
        o["_ztop"] = o["head"] + o["lintel_min"]
        o["_zbot"] = o["z_bot"]
        o["_rec"] = False
        o["sh"] = float(1.0 / body.shape(np.array(o["th"])))      # s units per face metre at the opening
        ops.append(o)
    return ops


class SurfMap:
    """the surface coordinates (s along the course, z up, w out of the face) of a declared body.
    Round body: the keep's round_map_factory (s = arc length at the course's nominal radius).
    Polygon body (kit 1.7.1, poly=True): every FACET is a straight run -- s = perimeter length from corner 0 (at
    plan angle rot - 180/sides deg) at the course's nominal apothem, mapped piecewise-linearly onto the battered
    facet planes, so a stone never bends round a corner (a piece laid across a corner folds on the true arris)."""

    def __init__(self, body, poly):
        self.b = body
        self.poly = bool(poly)
        self.n = body.sides
        if not self.poly:
            self.mapfn = round_map_factory(body.c, body.r_nom, body.r_eff)
        else:
            self.step = 2 * math.pi / self.n
            self.tn = math.tan(math.pi / self.n)
            self.mapfn = self._poly_map

    def side(self, z):
        return 2.0 * self.b.r_nom(z) * self.tn

    def perim(self, z):
        """course perimeter at height(s) z (a float for a scalar z)."""
        p = 2 * math.pi * self.b.r_nom(z) if not self.poly else self.n * self.side(z)
        return float(p) if np.ndim(p) == 0 else p

    def s_of_th(self, th, z):
        """course coordinate s of the face point in plan direction th at height z."""
        b = self.b
        if not self.poly:
            return th * float(b.r_nom(z))
        k = int(round((th - b.rot) / self.step)) % self.n
        d = math.atan2(math.sin(th - b.rot - k * self.step), math.cos(th - b.rot - k * self.step))
        return ((k + 0.5) * float(self.side(z)) + float(b.r_nom(z)) * math.tan(d)) % self.perim(z)

    def _poly_map(self, s, z, w, zc):
        b = self.b
        s, z, w, zc = (np.asarray(v, float) for v in (s, z, w, zc))
        L = self.side(zc)
        sm = np.mod(s, self.n * L)
        k = np.floor(sm / L)
        x = sm - (k + 0.5) * L
        phi = b.rot + np.mod(k, self.n) * self.step
        nr = 1.0 / math.sqrt(1.0 + b.bat ** 2)
        R = b.r_nom(z) + w * nr
        cp, sp = np.cos(phi), np.sin(phi)
        return np.stack([b.c[0] + R * cp - x * sp, b.c[1] + R * sp + x * cp, z + w * b.bat * nr], -1)


def _excl_factory(body, ops, smap=None):
    """layout_wall exclusion: every course crossing an opening's frame is cut (frame + jambs); the first layout
    pass records the beds the frame must reach (lintel top, sill bottom)."""
    def excl(za, zb, zm):
        out = []
        layout = (zb - za) > 0.07                 # a course (layout_wall) vs a fill_voids raster row
        lo, hi = za + 0.03, zb - 0.03
        for o in ops:
            if layout:
                hit = (hi > o["z_bot"]) and (lo < o["head"] + o["lintel_min"])
                if hit:
                    if not o["_rec"]:
                        o["_ztop"] = hi
                        o["_zbot"] = lo if o["kind"] == "window" else o["z_bot"]
                        o["_rec"] = True
                    o["_ztop"] = max(o["_ztop"], hi)
                    if o["kind"] == "window":
                        o["_zbot"] = min(o["_zbot"], lo)
            else:
                hit = (zm > o["_zbot"]) and (zm < o["_ztop"])
            if hit:
                sc = o["th"] * float(body.r_nom(zm)) if smap is None else smap.s_of_th(o["th"], zm)
                hw = o["hw_tot"] * o["sh"]
                out.append((sc - hw, sc + hw))
        return out
    return excl


def stone_body(g, name, openings=(), clip_by=(), below=None, seed=101, cfg=None, coping=None, side_depth=0.018,
               joint_lap=0.06, quoins=True, quoin_len=(0.40, 0.52), quoin_short=(0.20, 0.27), quoin_min_h=0.18):
    """KIT COMPONENT: the coursed rubble of the declared body `name` (see the module doc).
    kit 1.7.1 junction rules:
      joint_lap  each body's OWN mortar sheet runs this far (m) past the face of every clip_by body (the stones
                 still stop exactly at it), so the two sheets cross behind the re-entrant joint and any gap between
                 the two bodies' stones shows mortar, never the hollow interior;
      quoins     polygon bodies: facets laid as straight runs (SurfMap), courses continuous round the corner, every
                 corner closed by alternating long (quoin_len) / short (quoin_short) dressed corner stones from the
                 kit's one stone generator, each spanning >= quoin_min_h of courses (footing course excepted)."""
    body = g.body(name)
    seed = int(seed) + g.seed_offset
    cfg = dict(RUBBLE_CFG, **(cfg or {}), seed=seed % 997)
    poly = (not body.round) and bool(quoins)
    smap = SurfMap(body, poly)
    ops = _prep_openings(body, openings)
    if poly:
        for o in ops:
            o["sh"] = 1.0                      # s is in face metres on a straight facet
    excl = _excl_factory(body, ops, smap)
    roof = g.roofs[below]["roof"] if below else None

    def under_roof(P):
        if roof is None:
            return np.zeros(P.shape[:-1], bool)
        from .tier_frame import roof_z
        return P[..., 2] < roof_z(roof, P[..., 0], P[..., 1]) - 0.06

    def cull(P):
        return g.inside_any(P, clip_by, margin=0.0, zpad=0.05) | under_roof(P)

    def cull_mortar(P):
        return g.inside_any(P, clip_by, margin=joint_lap, zpad=0.05) | under_roof(P)

    coll = g.sub(name)
    if poly:
        S = _poly_stone_wall(g, name, coll, body, smap, seed, cfg, excl, cull, side_depth, quoin_len, quoin_short,
                             quoin_min_h)
    else:
        S = round_stone_wall(g.name(name), coll, body.c, body.r_nom, body.z0, body.z1, seed, cfg,
                             eff_radius_fn=body.r_eff, excl_fn=excl, cull_fn=cull,
                             mortar_cull_fn=lambda C: np.ones(len(C), bool),        # own mortar body below
                             side_depth=side_depth, relief=g.min_relief)
        _drop_empty(g.name(name) + "_mortar")
    # ---- own mortar body: cut exactly round the openings' frames, lapped past the clip bodies, refined near them
    r0 = body.apothem
    mapfn = smap.mapfn
    P0 = smap.perim(0.0)
    wrap = lambda s, z, w: mapfn(np.asarray(s) / P0 * smap.perim(z), z, w, z)   # noqa: E731  (s in z=0 units)
    L0 = P0
    if poly:                                   # cell edges on every corner (the sheet folds on the arris)
        s_edges = np.concatenate([np.linspace(k * P0 / body.sides, (k + 1) * P0 / body.sides,
                                              max(int(P0 / body.sides / 0.30), 2) + 1)[:-1]
                                  for k in range(body.sides)] + [[P0]])
    else:
        s_edges = np.linspace(0.0, L0, max(int(L0 / 0.30), 24) + 1)
    z_lo = max(body.z0, -0.05)
    z_edges = np.linspace(z_lo, body.z1 + 0.02, max(int((body.z1 - z_lo) / 0.24), 3) + 1)

    def op_s(o):
        if poly:
            return smap.s_of_th(o["th"], 0.0), o["hw"]
        return o["th"] * r0, o["hw"] * o["sh"] * r0 / max(float(body.r_nom(0.5 * (o["z_clear0"] + o["head"]))), 1e-3)

    def near(sc, zc, ds, dz):
        out = np.zeros(len(sc), bool)
        for o in ops:
            s_o, hw = op_s(o)
            out |= (np.abs(sc - s_o) < hw + 0.32) & (zc > o["z_clear0"] - 0.3) & (zc < o["head"] + 0.3)
        if clip_by or roof is not None:
            P = wrap(sc, zc, np.zeros(len(sc)))
            for n in clip_by:
                out |= np.abs(g.body(n).dist(P)) < 0.25
            if roof is not None:
                from .tier_frame import roof_z
                out |= np.abs(P[:, 2] - roof_z(roof, P[:, 0], P[:, 1])) < 0.22
        return out

    def keep(s, z):
        ok = np.ones(len(s), bool)
        for o in ops:
            s_o, hw = op_s(o)
            ok &= ~((np.abs(s - s_o) < hw + 0.03) & (z > o["z_clear0"] - 0.03) & (z < o["head"] + 0.03))
        P = wrap(s, z, np.zeros(len(s)))
        ok &= ~cull_mortar(P)
        return ok

    accm = Acc(g.name(name) + "_mortar")
    n = mortar_sheet(accm, wrap, s_edges, z_edges, near, keep, sub=4, w0=-0.006, w_amp=0.003, seed=seed * 0.01)
    finalize(accm, coll)
    log(f"  {name}: {len(S['sc'])} stones, mortar cells {n}")
    # ---- publish the openings (world frames) for framed_openings / decals / the cull's door views
    for o in ops:
        thn = body.facet_normal(o["th"])
        nrm = np.array([math.cos(thn), math.sin(thn), 0.0])
        tng = np.array([-nrm[1], nrm[0], 0.0])
        zmid = 0.5 * (o["z_clear0"] + o["head"])
        P0 = body.point(np.array(o["th"]), np.array(zmid))
        # plumb reference plane through the face at mid height of the opening
        o.update(body=name, origin=np.array([P0[0], P0[1], 0.0]), normal=nrm, tangent=tng)
        g.openings.append(o)
        log(f"    {o['kind']} at {math.degrees(o['th']):.0f} deg: frame z {o['_zbot']:.2f}..{o['_ztop']:.2f}")
    if coping is not None:
        z_c, r_in = coping
        coping_ledge(g, name, z_c, r_in, seed=seed + 5)
    return S


def _poly_stone_wall(g, name, coll, body, smap, seed, cfg, excl_open, cull_fn, side_depth, quoin_len, quoin_short,
                     quoin_min_h):
    """coursed rubble on a POLYGON body: straight facet runs (smap) with dressed long-and-short corner stones.  The
    same layout / pinning / stone generator chain as stone_wall.round_stone_wall; the corner bands are excluded from
    the rubble layout course by course and filled with one dressed quoin per corner per quoin course (a quoin course
    groups consecutive rubble courses until it is >= quoin_min_h tall; long and short alternate up the corner and
    between neighbouring corners).  Objects <P>_<name>_stones and <P>_<name>_quoins."""
    from .stone_wall import (cat_stones, dress_irregular, fill_voids, filt, lay_poly_stones, lay_stones, layout_wall,
                             polygonize, rough_footing, stone_rec)
    n = body.sides
    rng = np.random.default_rng(seed)
    qrng = np.random.default_rng(seed + 77)
    groups = []
    state = dict(cur=None)

    def corner_iv(zc, parity):
        L = float(smap.side(zc))
        out = []
        for j in range(n):
            lo_, sh_ = qrng.uniform(*quoin_len), qrng.uniform(*quoin_short)
            a, b = (lo_, sh_) if (j + parity) % 2 == 0 else (sh_, lo_)
            out.append((j * L - a, j * L + b))
        a0, b0 = out[0]
        return out, out + [(a0 + n * L, b0 + n * L)]

    def excl(za, zb, zm):
        out = list(excl_open(za, zb, zm))
        if (zb - za) > 0.07:                       # a layout_wall course
            z0, z1 = za + 0.03, zb - 0.03
            if z0 <= body.z0 + 1e-6:               # the stepped footing course runs round the corner
                return out
            cur = state["cur"]
            if cur is None or cur["closed"]:
                iv, ivx = corner_iv(0.5 * (z0 + z1), len(groups) % 2)
                cur = dict(z0=z0, z1=z1, iv=iv, ivx=ivx, closed=False)
                groups.append(cur)
                state["cur"] = cur
            cur["z1"] = z1
            if z1 - cur["z0"] >= quoin_min_h:
                cur["closed"] = True
            out += cur["ivx"]
        else:                                      # a fill_voids raster row
            for q in groups:
                if q["z0"] - 0.004 <= zm <= q["z1"] + 0.004:
                    out += q["ivx"]
        return out

    mapfn = smap.mapfn
    srange = lambda zm: [(0.0, smap.perim(zm))]   # noqa: E731
    S = layout_wall(rng, srange, body.z0, body.z1, excl, cfg)
    S = polygonize(S, S["foot"] > 0.5, np.random.default_rng(seed + 305))
    S = rough_footing(S, np.random.default_rng(seed + 306))
    pins, _, _ = fill_voids(S, srange, excl, body.z0, body.z1, rng, cfg, label=g.name(name))
    S = cat_stones(S, pins)
    S = filt(S, ~cull_fn(mapfn(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])))
    acc = Acc(g.name(name) + "_stones")
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    foot = (S["foot"] > 0.5) & ~small
    relief = g.min_relief
    lay_poly_stones(acc, filt(S, foot), mapfn, "M_stone", np.random.default_rng(seed + 406), rough=1.15,
                    side_depth=side_depth, relief=relief)
    small &= ~foot
    lay_stones(acc, filt(S, ~small & ~foot), mapfn, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009,
               side_depth=side_depth, relief=relief)
    lay_stones(acc, filt(S, small), mapfn, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True,
               side_depth=side_depth, relief=relief)
    finalize(acc, coll, smooth_deg=28.0)
    # ---- dressed long-and-short corner stones
    R = []
    jt = 0.010
    for q in groups:
        zc = 0.5 * (q["z0"] + q["z1"])
        hy = 0.5 * (q["z1"] - q["z0"]) - 0.5 * jt
        for (a, b) in q["iv"]:
            R.append((0.5 * (a + b), zc, 0.5 * (b - a) - 0.5 * jt, hy))
    if R:
        R = np.array(R)
        qr = np.random.default_rng(seed + 501)
        keep = ~cull_fn(mapfn(R[:, 0], R[:, 1], np.zeros(len(R)), R[:, 1]))
        R = R[keep]
        Sq = stone_rec(R[:, 0], R[:, 1], R[:, 2], R[:, 3], qr.uniform(0.012, 0.022, len(R)), 0.14,
                       qr.uniform(0.010, 0.015, len(R)), R[:, 1], qr)
        dress_irregular(Sq, qr)
        accq = Acc(g.name(name) + "_quoins")
        lay_stones(accq, Sq, mapfn, "M_stone_dressed", qr, rough=0.5, dressed=True, grid=(26, 14),
                   side_depth=side_depth, relief=relief)
        finalize(accq, coll, smooth_deg=24.0)
    log(f"  {name}: {len(S['sc'])} rubble stones on {n} straight facets, {len(R)} quoins in {len(groups)} quoin "
        f"courses")
    return S


def _drop_empty(obname):
    import bpy
    ob = bpy.data.objects.get(obname)
    if ob is not None and len(ob.data.polygons) == 0:
        bpy.data.objects.remove(ob)


def coping_ledge(g, name, z, r_in, overhang=0.07, t=0.11, n_stones=None, seed=7):
    """dressed coping ledge on top of body `name` at height z: a ring of dressed slabs (radial joints) from r_in
    to the body face + overhang, with chamfered top arris and a drip under the overhang.  Closes the body top
    round a belt / smaller body standing on it."""
    body = g.body(name)
    rng = np.random.default_rng(seed)
    acc = Acc(g.name(name) + "_coping")
    r_face = float(body.r_nom(z))
    n_st = n_stones or max(8, int(2 * math.pi * r_face / 0.55))
    edges = np.sort(rng.uniform(-0.25, 0.25, n_st) / n_st * 2 * math.pi + np.arange(n_st) * 2 * math.pi / n_st)
    for i in range(n_st):
        a0, a1 = edges[i] + 0.006 / r_face, edges[(i + 1) % n_st] + (2 * math.pi if i == n_st - 1 else 0) - 0.006 / r_face
        th = np.linspace(a0, a1, 7)
        ov = overhang + rng.uniform(-0.01, 0.015)
        tt = t + rng.uniform(-0.012, 0.012)
        dz = rng.uniform(-0.006, 0.006)
        ro = body.r_eff(th, z) + ov
        prof = [(r_in, z - 0.02), (r_in, z + tt - 0.02 + dz), (ro - 0.025, z + tt + dz), (ro, z + tt - 0.025 + dz),
                (ro, z + 0.02), (ro - 0.02, z), (r_face - 0.03, z - 0.0)]
        _ring_piece(acc, body.c, th, [(p[0] if np.ndim(p[0]) else np.full(len(th), p[0]), p[1]) for p in prof],
                    "M_stone_dressed", closed=False)
    finalize(acc, g.sub(name), smooth_deg=35.0)
    g.copings.append((name, z + t))


def _ring_piece(acc, c, th, prof, mat, closed=True):
    """sweep a closed (r, z) profile (each r may vary per angle) along the angles th about centre c; end caps unless
    closed (a full ring)."""
    m = len(prof)
    n = len(th)
    V = np.zeros((n, m, 3))
    for j, (r, z) in enumerate(prof):
        r = np.broadcast_to(np.asarray(r, float), (n,))
        V[:, j, 0] = c[0] + r * np.cos(th)
        V[:, j, 1] = c[1] + r * np.sin(th)
        V[:, j, 2] = z
    i = np.arange(n - 1 if not closed else n)[:, None]
    jj = np.arange(m)[None, :]
    a = i * m + jj
    b = i * m + (jj + 1) % m
    i2 = (i + 1) % n
    q = np.stack([a, b, i2 * m + (jj + 1) % m, i2 * m + jj], -1).reshape(-1, 4)
    faces = [q]
    if not closed:
        faces += [np.arange(m)[None, ::-1], ((n - 1) * m + np.arange(m))[None]]
    acc.add(V.reshape(-1, 3), faces, mat)


# =================================================================================================================
# framed openings
# =================================================================================================================
def _box(acc, o, x0, x1, z0, z1, w0, w1, mat, r=0.012, n=(4, 4, 4)):
    """axis box in an opening's frame: x along the tangent, z up, w along the outward normal."""
    O = o["origin"] + o["tangent"] * x0 + np.array([0, 0, 0.5 * (z0 + z1)]) + o["normal"] * (0.5 * (w0 + w1))
    obox(acc, O[None], o["tangent"], o["normal"], np.array([0, 0, 1.0]), x1 - x0, w1 - w0, z1 - z0, r, mat,
         nx=n[0], ny=n[1], nz=n[2])


def _boxz(acc, o, x0, x1, z0, z1, w0, w1, mat, r=0.012):
    """as _box but the obox's long axis vertical (posts, planks)."""
    O = o["origin"] + o["tangent"] * (0.5 * (x0 + x1)) + np.array([0, 0, z0]) + o["normal"] * (0.5 * (w0 + w1))
    obox(acc, O[None], np.array([0, 0, 1.0]), o["tangent"], o["normal"], z1 - z0, x1 - x0, w1 - w0, r, mat,
         nx=4, ny=4, nz=3)


def framed_openings(g, seed=808):
    """KIT COMPONENT: frames, leaves / shutters, sills, thresholds and backings of every opening published by
    stone_body (see the module doc)."""
    from .hewn import nail_heads
    rng = np.random.default_rng(seed + g.seed_offset)
    coll = g.sub("openings")
    accf, accl, acci, accs, accb = (Acc(g.name("openings_" + p)) for p in ("frame", "leaf", "iron", "sill", "backing"))
    for o in g.openings:
        body = g.body(o["body"])
        hw, jw, dp, pr = o["hw"], o["jamb"], o["depth"], o["proud"]
        # the face leans with the batter: keep the frame front `proud` in front of the face at the frame foot
        w_face = float(body.r_nom(o["_zbot"] if o["kind"] == "window" else 0.0) - body.r_nom(0.5 * (o["z_clear0"] + o["head"])))
        wf = w_face + pr
        wb = -dp
        zc0, head, ztop = o["z_clear0"], o["head"], o["_ztop"] + 0.004
        wd = lambda: rng.uniform(-0.004, 0.004)  # noqa: E731
        if o["kind"] == "door":
            # dressed threshold stone (projecting 0.22 m, top = clear sill), jambs, lintel let into the course above
            _box(accs, o, -hw - jw - 0.06, hw + jw + 0.06, -0.05, zc0, wb - 0.02, wf + 0.22, "M_stone_dressed",
                 r=0.018, n=(6, 4, 3))
            jz0 = zc0
        else:
            # projecting sill stone with a drip, from the bed the masonry was cut to up to the clear sill
            _box(accs, o, -hw - jw - 0.07, hw + jw + 0.07, o["_zbot"] + 0.004, zc0, wb, wf + 0.07, "M_stone_dressed",
                 r=0.014, n=(6, 4, 3))
            jz0 = zc0
        for sgn in (-1, 1):
            xa, xb = sorted((sgn * hw, sgn * (hw + jw)))
            _boxz(accf, o, xa + wd(), xb + wd(), jz0 - 0.004, head + 0.01, wb, wf - 0.005, "M_timber")
        bear = 0.16 + rng.uniform(0.0, 0.06)
        _box(accf, o, -hw - jw - bear, hw + jw + bear, head, ztop, wb, wf + 0.01, "M_timber", r=0.016, n=(6, 4, 4))
        # backing board: closes the opening behind the leaf / shutters (the masonry is a facing shell)
        _box(accb, o, -hw - 0.02, hw + 0.02, zc0 - 0.02, head + 0.02, wb - 0.04, wb + 0.0, "M_timber_weathered",
             r=0.004, n=(4, 4, 4))
        if o["kind"] == "door":
            # vertical plank leaf, 16-30 cm boards with 0.6-1.2 cm gaps, set 0.18 m behind the frame front
            x = -hw + 0.004
            wl0, wl1 = wf - 0.24, wf - 0.19
            planks = []
            while x < hw - 0.05:
                w_ = min(rng.uniform(0.16, 0.30), hw - 0.004 - x)
                if hw - 0.004 - (x + w_) < 0.10:
                    w_ = hw - 0.004 - x
                planks.append((x, x + w_))
                x += w_ + rng.uniform(0.006, 0.012)
            for (a, b) in planks:
                _boxz(accl, o, a, b - 0.003, zc0 + 0.008, head - 0.008 + rng.uniform(-0.006, 0.0), wl0, wl1 + wd() * 0.5,
                      "M_timber", r=0.006)
            # strap hinges (hinge side -x) with nail heads, a ring-pull plate
            for zh in (zc0 + 0.32, head - 0.36):
                _box(acci, o, -hw + 0.02, hw * 0.55, zh - 0.025, zh + 0.025, wl1, wl1 + 0.007, "M_iron", r=0.002,
                     n=(6, 4, 3))
                xs = np.linspace(-hw + 0.08, hw * 0.45, 4)
                P = [o["origin"] + o["tangent"] * xx + np.array([0, 0, zh]) + o["normal"] * (wl1 + 0.007) for xx in xs]
                nail_heads(g, np.array(P), o["normal"], rad=0.008)
            _box(acci, o, hw * 0.55, hw * 0.55 + 0.07, zc0 + 0.95, zc0 + 1.07, wl1, wl1 + 0.008, "M_iron", r=0.002)
        else:
            # mullioned frame (2 x 2 lights) and closed board shutters behind it
            fr = 0.06
            wm0, wm1 = wf - 0.16, wf - 0.08
            _boxz(accf, o, -0.03, 0.03, zc0, head, wm0, wm1, "M_timber", r=0.008)
            _box(accf, o, -hw, hw, 0.5 * (zc0 + head) - 0.03, 0.5 * (zc0 + head) + 0.03, wm0, wm1, "M_timber", r=0.008)
            for sgn in (-1, 1):
                xa, xb = sorted((sgn * hw, sgn * (hw - fr)))
                _boxz(accf, o, xa, xb, zc0, head, wm0, wm1, "M_timber", r=0.008)
            _box(accf, o, -hw, hw, zc0, zc0 + fr, wm0, wm1, "M_timber", r=0.008)
            _box(accf, o, -hw, hw, head - fr, head, wm0, wm1, "M_timber", r=0.008)
            x = -hw + 0.004
            while x < hw - 0.06:
                w_ = min(rng.uniform(0.12, 0.2), hw - 0.004 - x)
                _boxz(accl, o, x, x + w_ - 0.004, zc0 + 0.004, head - 0.004, wb + 0.01, wb + 0.035, "M_timber_weathered",
                      r=0.004)
                x += w_
    for a in (accf, accl, acci, accs, accb):
        finalize(a, coll, smooth_deg=35.0)
