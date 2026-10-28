"""components.annex -- the rubble walls of a rectangular annex (wing) built against a polygonal hall (kit 1.1.0, from
the hilltop keep's west wing).

annex_walls(g, seed=1111)   KIT COMPONENT (g = OctFrame; plan WX_W..WX_E x WY_S..WY_N, wall W_WALL_H, door g.WDOOR,
    window g.WWIN): coursed rubble along the wing path (N wall from the hall, W wall, S wall back to the hall) with a
    stepped field-stone footing, hero polygonal stones on the south (entrance-side) face, pinned voids, the stones
    stopped where the turret and the hall take over, dressed quoins / jambs of the door and window (tooled, out of
    square), a recessed mortar body refined round the openings and the turret junction, an eave filling (M_daub) on
    the wall heads under the thatch and reveal tubes through the wall -> <P>_wing_wall_stones / _dressed_stones /
    _wall_mortar
"""
import numpy as np

from ..core import log
from ..geom import Acc, finalize, runs_of
from .oct_frame import FR, apo, tur_dist, wing_map, wing_under, wing_ztop
from .stone_wall import (cat_stones, dress_irregular, fill_voids, filt, lay_poly_stones, lay_stones, layout_wall,
                         mortar_sheet, polygonize, rough_footing, stone_rec)
from .turret import tooth_excl_wall


def _lay(*a, **k):
    return lay_stones(*a, relief=FR.min_relief, **k)


def _lay_poly(*a, **k):
    return lay_poly_stones(*a, relief=FR.min_relief, **k)


def wing_quoins():
    rng = np.random.default_rng(1113)
    recs = []
    d = FR.WDOOR
    s_d = FR.S_SOUTH0 + (d["xc"] - FR.WX_W)
    for side in (-1, 1):
        z = -0.06
        i = 0
        while z < d["z1"] - 0.05:
            h = min(rng.uniform(0.30, 0.42), d["z1"] + 0.0 - z)
            if h < 0.12:
                break
            wd = (0.36 if (i % 2 == 0) == (side < 0) else 0.25) + rng.uniform(-0.03, 0.03)
            x_in = s_d + side * (d["hw"] + d["fw"])
            xa, xb = sorted([x_in, x_in + side * wd])
            recs.append((0.5 * (xa + xb), z + h / 2, 0.5 * (xb - xa) - 0.007, h / 2 - 0.008, rng.uniform(0.022, 0.036), 0.26))
            z += h
            i += 1
    w = FR.WWIN
    s_w = FR.S_SOUTH0 + (w["xc"] - FR.WX_W)
    for side in (-1, 1):
        x_in = s_w + side * (w["hw"] + w["fw"])
        za, zb = w["z0"] - w["fw"], w["z1"] + w["fw"]
        for (z_a, z_b, wd) in ((za, 0.5 * (za + zb) - 0.004, 0.25 if side < 0 else 0.20),
                               (0.5 * (za + zb) + 0.004, zb, 0.20 if side < 0 else 0.25)):
            xa, xb = sorted([x_in, x_in + side * wd])
            recs.append((0.5 * (xa + xb), 0.5 * (z_a + z_b), 0.5 * (xb - xa) - 0.006, 0.5 * (z_b - z_a) - 0.006,
                         0.025, 0.22))
    return np.array(recs)


def wing_open_rects(with_extras=True):
    """opening rects in path coords (s0,s1,z0,z1): frames, lintels, sills, quoins."""
    d = FR.WDOOR
    s_d = FR.S_SOUTH0 + (d["xc"] - FR.WX_W)
    w = FR.WWIN
    s_w = FR.S_SOUTH0 + (w["xc"] - FR.WX_W)
    fw = w["fw"]
    rects = [(s_d - d["hw"] - d["fw"], s_d + d["hw"] + d["fw"], -0.2, d["z1"] + 0.24),
             (s_w - w["hw"] - fw, s_w + w["hw"] + fw, w["z0"] - fw - 0.11, w["z1"] + fw)]
    if with_extras:
        rects += [(s_d - d["hw"] - d["fw"] - 0.23, s_d + d["hw"] + d["fw"] + 0.25, d["z1"], d["z1"] + 0.245),
                  (s_w - w["hw"] - 0.31, s_w + w["hw"] + 0.31, w["z1"] + fw, w["z1"] + fw + 0.17),
                  (s_w - w["hw"] - 0.17, s_w + w["hw"] + 0.17, w["z0"] - fw - 0.115, w["z0"] - fw)]
        for q in wing_quoins():
            rects.append((q[0] - q[2] - 0.006, q[0] + q[2] + 0.006, q[1] - q[3] - 0.006, q[1] + q[3] + 0.006))
    return rects


def build_wing_walls(coll, seed=1111):
    rng = np.random.default_rng(seed)
    acc = Acc(FR.prefix + "_wing_wall_stones")
    rects = wing_open_rects()

    def excl(z0, z1, zm):
        out = []
        for s0, s1, za, zb in rects:
            if z1 > za and z0 < zb:
                out.append((s0 - 0.012, s1 + 0.012))
        return out + tooth_excl_wall(z0, z1, zm)
    cfg = dict(seed=17 + (seed - 1111), footing=0.32, ch=(0.09, 0.19), p_tall=0.08, len=(0.20, 0.62), foot_len=(0.40, 1.10),
               foot_lvl=(-0.10, 0.10), joint=(0.009, 0.018), front=(0.005, 0.036), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
               pillow=(0.002, 0.008), tilt=0.008, rot=0.012, p_double=0.07, p_long=0.05, back=0.09, bed_amp=0.03,
               slant=0.27, ch_mix=[(0.28, 0.08, 0.11), (0.38, 0.11, 0.16), (0.24, 0.16, 0.21), (0.10, 0.21, 0.25)],
               pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
    srange = lambda zm: [(0.0, FR.WING_LEN)]
    S = layout_wall(rng, srange, -0.10, 3.85, excl, cfg, ztop_fn=wing_ztop)
    S = polygonize(S, ((S["sc"] > FR.S_SOUTH0 - 0.05) & (S["zc"] < 3.5) & (S["zc"] > 0.3)) | (S["foot"] > 0.5),
                   np.random.default_rng(seed + 809))
    S = rough_footing(S, np.random.default_rng(seed + 2651))
    pins, _, _ = fill_voids(S, srange, excl, -0.10, 3.85, rng, cfg, ztop_fn=wing_ztop, label="wing")
    S = cat_stones(S, pins)
    P = wing_map(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
    keep = tur_dist(P[:, 0], P[:, 1], P[:, 2]) > -0.04
    ang = np.arctan2(P[:, 1], P[:, 0])
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = P[:, 0] * np.cos(kk * np.pi / 4) + P[:, 1] * np.sin(kk * np.pi / 4)
    keep &= pp > apo(P[:, 2]) - 0.02
    S = filt(S, keep)
    log("  wing stones", len(S["sc"]))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    # hero zone: the wing's south wall below 3.5 m (seen in the hero/front/actor shots)
    hero = (((S["sc"] > FR.S_SOUTH0 - 0.05) & (S["zc"] < 3.5)) | (S["foot"] > 0.5)) & ~small
    log(f"  wing hero stones {int(hero.sum())}, other {int((~hero & ~small).sum())}, pins {int(small.sum())}")
    _lay_poly(acc, filt(S, hero), wing_map, "M_stone", np.random.default_rng(seed + 910), rough=1.1, side_depth=0.018,
                      rings=(0.8, 0.58, 0.33))
    _lay(acc, filt(S, ~hero & ~small), wing_map, "M_stone", rng, rough=1.1, nxy=5, noise_amp=0.008, side_depth=0.018)
    _lay(acc, filt(S, small), wing_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005, side_depth=0.018)
    finalize(acc, coll, smooth_deg=28.0)
    # dressed quoins / jamb blocks of the plank door and the window: tooled faces, chipped arrises, out of square
    accq = Acc(FR.prefix + "_wing_dressed_stones")
    R = wing_quoins()
    S2 = stone_rec(R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], rng.uniform(0.010, 0.015, len(R)), R[:, 1], rng)
    dress_irregular(S2, rng)
    wear = np.clip(1.0 - S2["zc"] / 0.8, 0, 1)
    _lay(accq, S2, wing_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(26, 26), wear=wear)
    finalize(accq, coll, smooth_deg=24.0)
    # mortar body: coarse sheet, refined round the openings and the turret junction
    accm = Acc(FR.prefix + "_wing_wall_mortar")
    knots = FR.WS[np.flatnonzero(np.abs(np.diff(FR.WN[:, 0])) + np.abs(np.diff(FR.WN[:, 1])) > 1e-6)]
    ss = np.unique(np.round(np.concatenate([np.linspace(0, FR.WING_LEN, int(FR.WING_LEN / 0.3) + 1), knots, knots + 0.01]), 5))
    zs = np.linspace(-0.05, 3.8, 14)
    rects = wing_open_rects(False)

    def near(sm, zm, ds, dz):
        nr = np.zeros(len(sm), bool)
        for s0, s1, za, zb in rects:
            nr |= (sm > s0 - 0.5) & (sm < s1 + 0.5) & (zm > za - 0.5) & (zm < zb + 0.5)
        return nr

    def keep(sm, zm):
        k = np.ones(len(sm), bool)
        for ri_, (s0, s1, za, zb) in enumerate(rects):
            top_m = 0.26 if ri_ == 0 else -0.02           # door rect includes its lintel; the window rect does not
            k &= ~((sm > s0 + 0.04) & (sm < s1 - 0.04) & (zm > za + 0.04) & (zm < zb - top_m))
        zt = np.array([wing_ztop(s_) for s_ in sm])
        k &= zm < zt + 0.02
        Pm = wing_map(sm, zm, np.zeros(len(sm)), zm)
        k &= tur_dist(Pm[:, 0], Pm[:, 1], Pm[:, 2]) > -0.06      # mortar body runs on just behind the turret stones
        ang = np.arctan2(Pm[:, 1], Pm[:, 0])
        kk = np.round(ang / (np.pi / 4)) % 8
        pp = Pm[:, 0] * np.cos(kk * np.pi / 4) + Pm[:, 1] * np.sin(kk * np.pi / 4)
        k &= pp > apo(Pm[:, 2]) - 0.05
        return k
    n = mortar_sheet(accm, lambda s_, z_, w_: wing_map(s_, z_, w_, z_), ss, zs, near, keep, seed=2.0)
    log(f"  wing mortar cells {n}")
    # eave filling (beam fill) on the wall heads of the N, W and S walls: closes the roof space between the wall top
    # and the thatch underside, set back 0.22 m behind the wall face (seen only in the eave gap behind the roll)
    sf = np.arange(0.0, FR.WING_LEN, 0.1)
    Pf = wing_map(sf, np.full(len(sf), FR.W_WALL_H), np.full(len(sf), -0.22), np.full(len(sf), FR.W_WALL_H))
    ok_f = (Pf[:, 0] < FR.WX_E - 0.2) & (tur_dist(Pf[:, 0], Pf[:, 1], np.full(len(sf), 2.8)) > -0.45)
    zt_f = wing_under(Pf[:, 0], Pf[:, 1]) + 0.08
    for r_ in runs_of(np.column_stack([sf, zt_f]), ok_f, 2):
        n_ = len(r_)
        lo = wing_map(r_[:, 0], np.full(n_, FR.W_WALL_H - 0.06), np.full(n_, -0.22), np.full(n_, FR.W_WALL_H))
        hi = wing_map(r_[:, 0], r_[:, 1], np.full(n_, -0.22), np.full(n_, FR.W_WALL_H))
        V = np.concatenate([lo, hi])
        q = np.array([(i, i + 1, n_ + i + 1, n_ + i) for i in range(n_ - 1)])
        O = wing_map(r_[:1, 0], np.full(1, FR.W_WALL_H), np.full(1, 0.5), np.full(1, FR.W_WALL_H)) - lo[:1]
        nn = np.cross(V[q[0, 1]] - V[q[0, 0]], V[q[0, 3]] - V[q[0, 0]])
        if (nn * O[0]).sum() < 0:
            q = q[:, ::-1]
        accm.add(V, q, "M_daub")
    # reveals (door, window): tube through the wall
    def reveal_tube(ring, w0, w1):
        n = len(ring)
        r1 = wing_map(ring[:, 0], ring[:, 1], np.full(n, w0), ring[:, 1])
        r2 = wing_map(ring[:, 0], ring[:, 1], np.full(n, w1), ring[:, 1])
        V = np.concatenate([r1, r2])
        q = np.array([(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)])
        # reveal faces look into the opening (toward its axis)
        cen = V.mean(0)
        nrm = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 3]] - V[q[:, 0]])
        fc = V[q].mean(1)
        flip = (nrm * (cen - fc)).sum(1) < 0
        q[flip] = q[flip][:, ::-1]
        accm.add(V, q, "M_mortar")
    for ri_, (s0, s1, za, zb) in enumerate(wing_open_rects(False)):
        if ri_ == 0:
            ring = np.array([(s0 + 0.03, za + 0.2), (s1 - 0.03, za + 0.2), (s1 - 0.03, zb - 0.22),
                             (s0 + 0.03, zb - 0.22)])
            if za < 0:
                ring[:2, 1] = 0.0
            reveal_tube(ring, 0.0, -0.64)
        else:
            # window: reveal round the frame from the face back to the frame, then the clear opening to the
            # blocker room (no panel across the head of the opening)
            w = FR.WWIN
            s_w = FR.S_SOUTH0 + (w["xc"] - FR.WX_W)
            fw_, hw_ = w["fw"], w["hw"]
            ro = np.array([(s_w - hw_ - fw_ - 0.004, w["z0"] - fw_), (s_w + hw_ + fw_ + 0.004, w["z0"] - fw_),
                           (s_w + hw_ + fw_ + 0.004, w["z1"] + fw_), (s_w - hw_ - fw_ - 0.004, w["z1"] + fw_)])
            reveal_tube(ro, 0.0, -w["depth"] - 0.02)
            ri = np.array([(s_w - hw_ - 0.004, w["z0"] - 0.004), (s_w + hw_ + 0.004, w["z0"] - 0.004),
                           (s_w + hw_ + 0.004, w["z1"] + 0.004), (s_w - hw_ - 0.004, w["z1"] + 0.004)])
            reveal_tube(ri, -w["depth"] - 0.08, -0.64)
    finalize(accm, coll, recalc=False)



def annex_walls(g, seed=1111):
    """KIT COMPONENT: the annex's rubble walls, dressed quoins, mortar body, eave filling and reveals."""
    build_wing_walls(g.sub("wing"), seed=seed)
