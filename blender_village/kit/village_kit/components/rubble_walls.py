"""components.rubble_walls -- coursed rubble walls along ANY plan polyline, and round rubble bodies, with openings,
corner quoins and junction culls (kit, variant v3_longhouse_roundend).

Both builders lay the kit's coursed rubble (components.stone_wall: layout_wall / polygonize / rough_footing /
fill_voids / lay_stones, i.e. the ONE stone generator) and the recessed mortar body behind it, and build their
openings with components.wall_openings.

    PathMap(path)                         surface map of a plan polyline (interior on the LEFT of the walking
                                          direction): s along the path, z up, w out along the outward normal
    path_stone_wall(g, name, path, ...)   KIT COMPONENT: rubble wall along a polyline (straight runs of any length,
                                          any number of corners), stepped footing, dressed long-and-short quoins on
                                          every outside corner (solid 3-D blocks), a sloping top (gable) from
                                          top_fn(x, y), openings at given s, and a clip that drops the stones / mortar
                                          inside another body (a round end, a tower) -> <P>_<name>_stones,
                                          _quoins, _mortar + the opening objects
    round_stone_body(g, name, ...)        KIT COMPONENT: battered round rubble body (stone_wall.round_stone_wall) with
                                          openings by azimuth and a clip for the part inside an attached body
                                          -> <P>_<name>_stones, _mortar + the opening objects
Both publish their faces on g.WALL_FACES (for decal anchors) and their openings on g.OPENINGS.
kit 1.8.0: openings may be components.openings specs (door(...) / window(...)); the kit's one rubble-body entry point
is components.masonry.masonry_wall (path= -> path_stone_wall, round= -> round_stone_body, body= -> stone_body).
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, obox
from .stone_wall import (cat_stones, fill_voids, filt, lay_poly_stones, lay_stones, layout_wall, mortar_sheet,
                         polygonize, rough_footing, round_stone_wall)
from .wall_openings import build_opening, finish_accs, opening_accs, opening_cut, opening_rects

RUBBLE_CFG = dict(footing=0.30, ch=(0.09, 0.19), p_tall=0.08, len=(0.20, 0.62), foot_len=(0.40, 1.10),
                  foot_lvl=(-0.10, 0.10), joint=(0.009, 0.018), front=(0.005, 0.036), foot_proj=(0.035, 0.095),
                  bevel=(0.005, 0.03), pillow=(0.002, 0.008), tilt=0.008, rot=0.012, p_double=0.07, p_long=0.05,
                  back=0.09, bed_amp=0.03, slant=0.27,
                  ch_mix=[(0.28, 0.08, 0.11), (0.38, 0.11, 0.16), (0.24, 0.16, 0.21), (0.10, 0.21, 0.25)],
                  pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
"""the village's flat-bedded coursed rubble (art bible 3; the keep's annex table): courses 8-25 cm, stones
20-62 cm (through-stones to 0.9 m), wandering beds, pinch-outs, stepped footing projecting 3.5-9.5 cm."""

RUBBLE_LARGE = dict(ch=(0.11, 0.23), len=(0.26, 0.72),
                    ch_mix=[(0.22, 0.11, 0.14), (0.40, 0.14, 0.18), (0.28, 0.18, 0.22), (0.10, 0.22, 0.25)])
"""kit 1.12 (v5 round 2; a cfg= override, nothing reads it by default): the same rubble with the larger courses and
longer stones of the bible's range (the drum family's note-15 setting, README section 4) -- ~30 % fewer stones on a
long hall wall, for path_stone_wall(cfg=RUBBLE_LARGE) / round_stone_body(cfg=RUBBLE_LARGE)."""


class PathMap:
    """surface map of a plan polyline (see module doc).  path: (x, y) points, interior on the left."""

    def __init__(self, path):
        A = np.asarray(path, float)
        self.A = A
        D = np.diff(A, axis=0)
        self.L = np.linalg.norm(D, axis=1)
        self.dir = D / self.L[:, None]
        self.nrm = np.stack([self.dir[:, 1], -self.dir[:, 0]], 1)
        self.S = np.concatenate([[0.0], np.cumsum(self.L)])
        self.total = float(self.S[-1])

    def seg(self, s):
        return np.clip(np.searchsorted(self.S, np.asarray(s, float), side="right") - 1, 0, len(self.L) - 1)

    def __call__(self, s, z, w, zc=None):
        s, z, w = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float), np.asarray(w, float))
        i = self.seg(s)
        xy = self.A[i] + (s - self.S[i])[..., None] * self.dir[i] + w[..., None] * self.nrm[i]
        return np.concatenate([xy, z[..., None]], -1)

    def frame(self, s):
        i = int(self.seg(s))
        xy = self.A[i] + (s - self.S[i]) * self.dir[i]
        return (np.array([xy[0], xy[1], 0.0]), np.array([*self.dir[i], 0.0]), np.array([*self.nrm[i], 0.0]))

    def corners(self):
        """outside (convex) corners: (s, i_before, i_after)."""
        out = []
        for i in range(1, len(self.A) - 1):
            a, b = self.dir[i - 1], self.dir[i]
            if a[0] * b[1] - a[1] * b[0] > 1e-6:          # left turn with the interior on the left = outside corner
                out.append((float(self.S[i]), i - 1, i))
        return out


def _quoin_courses(rng, z_top, h_rng=(0.24, 0.34), long_short=(0.50, 0.28), z0=-0.04):
    z = z0
    out = []
    k = 0
    while z < z_top - 0.08:
        h = min(rng.uniform(*h_rng), z_top - z)
        if z_top - (z + h) < 0.10:
            h = z_top - z
        la, lb = (long_short if k % 2 == 0 else long_short[::-1])
        out.append((z, z + h, la + rng.uniform(-0.04, 0.04), lb + rng.uniform(-0.03, 0.03)))
        z += h
        k += 1
    return out


def path_stone_wall(g, name, path, top=2.75, top_fn=None, openings=(), clip=None, seed=31, cfg=None, quoins=True,
                    proj=0.025, hero_s=None, base=None, clip_z=None):
    """KIT COMPONENT (see module doc).
    path      plan polyline [(x, y), ...], interior on the left (so the outward normal is on the right)
    top       wall-head height (flat); top_fn(x, y) -> height overrides it per point (a gable under a roof deck)
    openings  [(s, spec), ...]  door / window specs (components.wall_openings) centred at path distance s
    clip      clip(P) -> bool: stones / mortar whose centre is inside another body are dropped (junctions)
    hero_s    (s0, s1): the run laid with hero polygonal stones (the entrance face); default: the footing only
    base      kit 1.12 (v5 round 2; None = -0.10, the land wall's buried footing): the course base z -- a quay /
              harbour wall standing on the bed (waterfront.stone_quay) starts at the bed
    clip_z    kit 1.12 (None = the kit's -5 cm land clip): the finalize clip height (a quay wall: just under the bed)"""
    if base is not None or clip_z is not None:
        return _path_stone_wall_based(g, name, path, top, top_fn, openings, clip, seed, cfg, quoins, proj, hero_s,
                                      -0.10 if base is None else float(base), clip_z)
    return _path_stone_wall_based(g, name, path, top, top_fn, openings, clip, seed, cfg, quoins, proj, hero_s,
                                  None, None)


def _path_stone_wall_based(g, name, path, top, top_fn, openings, clip, seed, cfg, quoins, proj, hero_s, base,
                           clip_z):
    """path_stone_wall's body; base / clip_z None = the kit 1.11 literals (-0.10 / -0.05 mortar foot / CLIP_Z)."""
    z_base = -0.10 if base is None else base
    z_mfoot = -0.05 if base is None else base + 0.05
    fin = {} if clip_z is None else dict(clip_z=clip_z)
    pm = PathMap(path)
    rng = np.random.default_rng(seed)
    cfg = dict(RUBBLE_CFG, seed=seed, **(cfg or {}))
    pre = f"{g.prefix}_{name}"

    def ztop_s(s):
        P = pm(np.atleast_1d(s), np.zeros(1), np.zeros(1))
        return float(top_fn(P[0, 0], P[0, 1])) if top_fn is not None else float(top)
    z_top = max(ztop_s(s_) for s_ in np.linspace(0, pm.total, 200))
    # opening rectangles in wall coordinates
    rects, cuts = [], []
    for s_c, sp in openings:
        for (x0, x1, z0, z1) in opening_rects(sp):
            rects.append((s_c + x0, s_c + x1, z0, z1))
        x0, x1, z0, z1 = opening_cut(sp)
        cuts.append((s_c + x0, s_c + x1, z0, z1))
    # quoins on every outside corner
    qrng = np.random.default_rng(seed + 7)
    Q = []
    if quoins:
        for (sc, ia, ib) in pm.corners():
            if base is None:
                Q.append((sc, ia, ib, _quoin_courses(qrng, ztop_s(sc))))
            else:
                Q.append((sc, ia, ib, _quoin_courses(qrng, ztop_s(sc), z0=z_base + 0.06)))

    def excl(z0, z1, zm):
        out = [(a, b) for (a, b, za, zb) in rects if z1 > za and z0 < zb]
        for (sc, ia, ib, courses) in Q:
            for (qa, qb, la, lb) in courses:
                if z1 > qa and z0 < qb:
                    out.append((sc - la - 0.012, sc))
                    out.append((sc, sc + lb + 0.012))
        return out
    runs = [(float(pm.S[i]), float(pm.S[i + 1])) for i in range(len(pm.L))]
    srange = lambda zm: runs  # noqa: E731
    S = layout_wall(rng, srange, z_base, z_top, excl, cfg, ztop_fn=ztop_s)
    hero = S["foot"] > 0.5
    if hero_s is not None:
        hero |= (S["sc"] > hero_s[0]) & (S["sc"] < hero_s[1]) & (S["zc"] < 2.4)
    S = polygonize(S, hero, np.random.default_rng(seed + 1))
    S = rough_footing(S, np.random.default_rng(seed + 2))
    pins, _, _ = fill_voids(S, srange, excl, z_base, z_top, rng, cfg, ztop_fn=ztop_s, label=name)
    S = cat_stones(S, pins)
    if clip is not None:
        P = pm(S["sc"], S["zc"], np.zeros(len(S["sc"])))
        S = filt(S, ~clip(P))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    hero = S["foot"] > 0.5
    if hero_s is not None:
        hero = hero | ((S["sc"] > hero_s[0]) & (S["sc"] < hero_s[1]) & (S["zc"] < 2.4))
    hero &= ~small
    log(f"  {pre}: stones {len(S['sc'])} (hero {int(hero.sum())}, pins {int(small.sum())})")
    relief = g.detail.min_at_v
    acc = Acc(pre + "_stones")
    lay_poly_stones(acc, filt(S, hero), pm, "M_stone", np.random.default_rng(seed + 3), relief=relief, rough=1.1,
                    side_depth=0.018, rings=(0.8, 0.58, 0.33))
    lay_stones(acc, filt(S, ~hero & ~small), pm, "M_stone", rng, relief=relief, rough=1.1, nxy=5, noise_amp=0.008,
               side_depth=0.018)
    lay_stones(acc, filt(S, small), pm, "M_stone", rng, relief=relief, rough=0.8, nxy=4, noise_amp=0.005,
               side_depth=0.018)
    finalize(acc, g.coll, smooth_deg=28.0, **fin)
    # quoins: solid dressed blocks, long and short faces alternating, 2.5 cm proud of both faces
    if Q:
        accq = Acc(pre + "_quoins")
        ez = np.array([0.0, 0.0, 1.0])
        for (sc, ia, ib, courses) in Q:
            C = pm(np.array([sc]), np.zeros(1), np.zeros(1))[0]
            dA = np.array([*pm.dir[ia], 0.0])
            nA = np.array([*pm.nrm[ia], 0.0])
            for (qa, qb, la, lb) in courses:
                h = qb - qa - 0.012
                O = C + dA * (-la) + nA * (0.5 * (proj - lb)) + ez * (qa + 0.006 + h / 2)
                O = O + dA * qrng.uniform(-0.006, 0.006)
                obox(accq, O[None], dA, nA, ez, la + proj, lb + proj, h, qrng.uniform(0.012, 0.02), "M_stone_dressed",
                     nx=5, ny=5, nz=4)
        finalize(accq, g.coll, smooth_deg=30.0, **fin)
    # mortar body: coarse sheet, refined round the openings, open inside them, following the (gable) top
    accm = Acc(pre + "_mortar")
    se = [np.linspace(a, b, max(2, int((b - a) / 0.3) + 1)) for (a, b) in runs]
    knots = [c for r in cuts for c in (r[0], r[1])]
    ss = np.unique(np.round(np.concatenate(se + [np.array(knots)] if knots else se), 5))
    if base is None:
        zs = np.linspace(-0.05, z_top + 0.02, max(4, int((z_top + 0.07) / 0.3) + 1))
    else:
        zs = np.linspace(z_mfoot, z_top + 0.02, max(4, int((z_top + 0.02 - z_mfoot) / 0.3) + 1))
    zs = np.unique(np.round(np.concatenate([zs] + [np.array([r[2], r[3]]) for r in cuts]), 5))

    def near(sm, zm, ds, dz):
        nr = np.zeros(len(sm), bool)
        for (a, b, za, zb) in cuts:
            nr |= (sm > a - 0.4) & (sm < b + 0.4) & (zm > za - 0.4) & (zm < zb + 0.4)
        if top_fn is not None:                  # refine only under a SLOPING top (a gable rake), not a flat head
            zt_ = np.array([ztop_s(s_) for s_ in sm])
            sl_ = np.abs(np.array([ztop_s(s_ + 0.05) - ztop_s(s_ - 0.05) for s_ in sm])) > 0.01
            nr |= sl_ & (np.abs(zm - zt_) < 0.35)
        return nr

    def keep(sm, zm):
        k = np.ones(len(sm), bool)
        for (a, b, za, zb) in cuts:
            k &= ~((sm > a) & (sm < b) & (zm > za) & (zm < zb))
        k &= zm < np.array([ztop_s(s_) for s_ in sm]) + 0.02
        if clip is not None:
            k &= ~clip(pm(sm, zm, np.zeros(len(sm))))
        return k
    n_m = mortar_sheet(accm, pm, ss, zs, near, keep, sub=3, seed=float(seed % 17))
    finalize(accm, g.coll, recalc=False, **fin)
    log(f"  {pre}: mortar cells {n_m}")
    # openings
    accs = opening_accs(g, name)
    orng = np.random.default_rng(seed + 11)
    for k, (s_c, sp) in enumerate(openings):
        O, t, n = pm.frame(s_c)
        build_opening(g, sp, O, t, n, accs, orng, label=f"{name}_{k}")
    finish_accs(g, accs)
    if not hasattr(g, "WALL_FACES"):
        g.WALL_FACES = []
    g.WALL_FACES.append(dict(kind="path", name=name, map=pm, top=ztop_s, clip=clip))
    return pm


def round_stone_body(g, name, center=(0.0, 0.0), r_base=3.6, batter_deg=2.5, top=None, openings=(), clip=None,
                     seed=41, cfg=None, open_z=None):
    """KIT COMPONENT (see module doc).  r_base: outer face radius at the ground; top: wall-head height (default the
    round frame's plate underside g.PLATE_BOT); openings: [(azimuth deg from -Y toward +X, spec), ...];
    clip(P) -> bool drops the stones / mortar inside an attached body.
    open_z (v3 round 8): None (default, the round 1-7 rule) frames every opening on the battered face at z 1.2 m;
    "mid" frames each at the face radius at its own mid height (an upper-storey window of a tall battered body
    sits on its own face, not 1.2 m's)."""
    z1 = float(g.PLATE_BOT if top is None else top)
    tb = math.tan(math.radians(batter_deg))
    radius_fn = lambda z: r_base - np.clip(np.asarray(z, float), 0, None) * tb  # noqa: E731
    cfg = dict(RUBBLE_CFG, seed=seed, **(cfg or {}))
    specs = []
    for az_deg, sp in openings:
        th = (math.radians(az_deg) - math.pi / 2) % (2 * math.pi)
        specs.append((th, None, sp))

    def excl(z0, z1_, zm):
        # s is arc length at the course's own (battered) radius: the opening's s moves with the course
        r_ = float(radius_fn(zm))
        out = []
        for th, _, sp in specs:
            for (x0, x1, za, zb) in opening_rects(sp):
                if z1_ > za and z0 < zb:
                    out.append((th * r_ + x0, th * r_ + x1))
        return out
    cuts = []
    for th, s_c, sp in specs:
        x0, x1, za, zb = opening_cut(sp)
        cuts.append((th, x0, x1, za, zb))

    def mortar_cull(C):
        hid = np.zeros(len(C), bool) if clip is None else clip(C)
        thv = np.arctan2(C[:, 1] - center[1], C[:, 0] - center[0])
        for th, x0, x1, za, zb in cuts:
            dx = np.angle(np.exp(1j * (thv - th))) * r_base
            hid |= (dx > x0) & (dx < x1) & (C[:, 2] > za) & (C[:, 2] < zb)
        return hid
    round_stone_wall(f"{g.prefix}_{name}", g.coll, center, radius_fn, -0.10, z1, seed, cfg, excl_fn=excl,
                     cull_fn=clip, mortar_cull_fn=mortar_cull, relief=g.detail.min_at_v)
    accs = opening_accs(g, name)
    orng = np.random.default_rng(seed + 11)
    for k, (th, s_c, sp) in enumerate(specs):
        if open_z == "mid":
            _x0, _x1, za_, zb_ = opening_cut(sp)
            r_ = float(radius_fn(0.5 * (za_ + zb_)))
        else:
            r_ = float(radius_fn(1.2))
        O = np.array([center[0] + r_ * math.cos(th), center[1] + r_ * math.sin(th), 0.0])
        t = np.array([-math.sin(th), math.cos(th), 0.0])
        n = np.array([math.cos(th), math.sin(th), 0.0])
        build_opening(g, sp, O, t, n, accs, orng, label=f"{name}_{k}")
    finish_accs(g, accs)
    if not hasattr(g, "WALL_FACES"):
        g.WALL_FACES = []
    g.WALL_FACES.append(dict(kind="round", name=name, center=center, radius=radius_fn, top=z1, clip=clip))
    return radius_fn
