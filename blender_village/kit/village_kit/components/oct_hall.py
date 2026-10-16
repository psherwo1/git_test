"""components.oct_hall -- polygonal post-and-stone hall walls (kit 1.1.0, from the hilltop keep).

The octagonal hall of an OctFrame (components.oct_frame): a battered, bulging coursed-rubble wall (stone_wall layout,
hero stones with polygonal outlines on the entrance side, a stepped field-stone footing course, pinned voids, a
recessed mortar body), dressed surrounds (an arched door with jambs of alternating long / short blocks and an
irregular voussoir ring, rectangular windows with jambs, lintel and a projecting drip sill; a timber-framed window
variant), reveal tubes and dark blocker rooms behind the openings (only the visible depth is modelled), and the
timber frame: engaged hewn corner posts on chamfered dressed pedestals, paired curved knee braces (Y-brackets),
a lap-jointed eave plate with projecting ends, a scarf-jointed raising plate, all pegged.

Openings are dicts (OctFrame.OPENINGS): name, k (facet), xc (along the facet), kind 'arch' (hw, z0, zs = springing,
depth) or 'rect' (hw, z0, z1, depth, frame, surround='timber' for a timber surround with a stone sill only).

Public components (g = OctFrame):
    oct_hall_walls(g, seed=101)     KEEP_hall_wall_stones / _dressed_stones / _dressed_joint_mortar / _wall_mortar /
                                    _interior
    oct_hall_frame(g, seed=202)     KEEP_hall_posts / _post_bases / _knee_braces / _eave_plate (+ pooled pegs)
    door_threshold(g, seed=1010)    KEEP_threshold (worn threshold stone + built-in step)
Helpers other components use: facet_obox (boxes in a facet frame), rough_block, open_contains / open_outline.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, TAN22, fbm90, finalize, obox, prof_rect, sweep
from .hewn import hewn_square, peg
from .oct_frame import (F, FN, FT, FPHI, corner_dir, face_apo, facet_s, fmap, hall_L, hall_map, in_wing)
from .stone_wall import (cat_stones, dress_irregular, fill_voids, filt, layout_wall, lay_poly_stones, lay_stones,
                         mortar_sheet, polygonize, rough_footing, stone_rec)
from ..stones import stone_outline
from ..geom import axn, rbox_v


def _lay(*a, **k):
    return lay_stones(*a, relief=F.min_relief, **k)


def _lay_poly(*a, **k):
    return lay_poly_stones(*a, relief=F.min_relief, **k)


def _hewn(*a, **k):
    return hewn_square(*a, relief=F.min_relief, dropped=F.dropped_checks, **k)


def open_contains(op, x, z, m=0.0):
    x = np.asarray(x, float) - op["xc"]
    z = np.asarray(z, float)
    hw = op["hw"] + m
    if op["kind"] == "arch":
        rect = (np.abs(x) <= hw) & (z >= op["z0"] - m) & (z <= op["zs"])
        arc = (x * x + (z - op["zs"]) ** 2 <= hw * hw) & (z > op["zs"])
        return rect | arc
    return (np.abs(x) <= hw) & (z >= op["z0"] - m) & (z <= op["z1"] + m)


def open_outline(op, grow=0.0, n_arc=16):
    """CCW outline (x,z) in facet coords."""
    hw = op["hw"] + grow
    xc = op["xc"]
    if op["kind"] == "arch":
        z0 = op["z0"] - grow - 0.12
        pts = [(xc - hw, z0), (xc + hw, z0)]
        for a in np.linspace(0, math.pi, n_arc):
            pts.append((xc + hw * math.cos(a), op["zs"] + hw * math.sin(a)))
        return np.array(pts)
    z0, z1 = op["z0"] - grow, op["z1"] + grow
    return np.array([(xc - hw, z0), (xc + hw, z0), (xc + hw, z1), (xc - hw, z1)])


def poly_band_extent(poly, z0, z1):
    P = np.asarray(poly, float)
    Q = np.roll(P, -1, axis=0)
    t = np.linspace(0, 1, 14)[None, :, None]
    S = (P[:, None, :] * (1 - t) + Q[:, None, :] * t).reshape(-1, 2)
    m = (S[:, 1] >= z0) & (S[:, 1] <= z1)
    if not m.any():
        if P[:, 1].min() < z0 and P[:, 1].max() > z1:
            return P[:, 0].min(), P[:, 0].max()
        return None
    return S[m, 0].min(), S[m, 0].max()


def _post_corners():
    out = []
    for c in range(8):
        d = np.array([math.cos(FPHI[c] + math.radians(22.5)), math.sin(FPHI[c] + math.radians(22.5))])
        P0 = np.array([d[0] * 4.30, d[1] * 4.30, 1.5])
        if not in_wing(P0, margin=-0.3, zpad=0.0):
            out.append(c)
    return out


def hall_excl(z0, z1, zm):
    out = []
    # no rubble behind the engaged corner posts (and their pedestals): those faces can never be seen
    for c in _post_corners():
        sc_ = (c + 0.5) / 8.0 * float(hall_L(zm))
        hw_ = 0.13 if z0 > 0.38 else 0.21
        if z1 > 0.0:
            out.append((sc_ - hw_, sc_ + hw_))
    for op in F.OPENINGS:
        e = poly_band_extent(open_outline(op, grow=0.0), z0, z1)
        if e is not None:
            out.append((float(facet_s(op["k"], e[0] - 0.01, zm)), float(facet_s(op["k"], e[1] + 0.01, zm))))
    for k in range(8):
        for poly in F.DRESSED_POLYS[k]:
            e = poly_band_extent(poly, z0, z1)
            if e is not None:
                out.append((float(facet_s(k, e[0] - 0.012, zm)), float(facet_s(k, e[1] + 0.012, zm))))
    return out


def build_door_dressing(acc_d, op, rng):
    k, xc, hw, zs = op["k"], op["xc"], op["hw"], op["zs"]
    leaf_apo = F.A_REF - op["depth"]
    recs = []
    # jambs (alternating long / short), both sides
    hs = np.array([0.40, 0.33, 0.37, 0.34, 0.33]) * rng.uniform(0.94, 1.06, 5)
    zb = -0.06
    hs = hs / hs.sum() * (zs - zb)
    zz = zb + np.concatenate([[0], np.cumsum(hs)])
    jwd = {}
    for side in (-1, 1):
        for i in range(5):
            long_ = (i % 2 == 0) == (side < 0)
            wd = (0.39 if long_ else 0.27) + rng.uniform(-0.03, 0.03)
            jwd[(side, i)] = wd
            z0_, z1_ = zz[i] + 0.006, zz[i + 1] - 0.006
            x_in = xc + side * hw
            x_out = x_in + side * wd
            xa, xb = min(x_in, x_out), max(x_in, x_out)
            zc = 0.5 * (z0_ + z1_)
            back = float(face_apo(k, x_in, zc)) - leaf_apo - 0.012
            recs.append(dict(x=0.5 * (xa + xb), zc=zc, hx=0.5 * (xb - xa) - 0.006, hy=0.5 * (z1_ - z0_),
                             f=0.05 + rng.uniform(0, 0.012), back=back))
            F.DRESSED_POLYS[k].append([(xa, z0_), (xb, z0_), (xb, z1_), (xa, z1_)])
    # recessed lime mortar in the jamb bed joints (1.2 cm back from the face and from the reveal)
    for side in (-1, 1):
        for i in range(1, 5):
            zj = zz[i]
            x_in = xc + side * hw
            wj = min(jwd[(side, i - 1)], jwd[(side, i)]) - 0.012
            xa, xb = sorted([x_in + side * 0.03, x_in + side * wj])
            wf_ = float(face_apo(k, x_in, zj)) - F.A_REF + 0.05 - 0.015 - 0.016
            facet_obox(F.JOINT_ACC, k, xa, xb, zj - 0.0095, zj + 0.0095, leaf_apo - F.A_REF, wf_, 0.003, "M_mortar",
                       nx=4, ny=3, nz=3)
    S = stone_rec([facet_s(k, r["x"], r["zc"]) for r in recs], [r["zc"] for r in recs],
                  [r["hx"] for r in recs], [r["hy"] for r in recs], [r["f"] for r in recs],
                  [r["back"] for r in recs], rng.uniform(0.010, 0.015, len(recs)),
                  [r["zc"] for r in recs], rng)
    dress_irregular(S, rng)
    wear = np.clip(1.1 - S["zc"] / 0.9, 0, 1)
    _lay(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(30, 32), wear=wear)
    # voussoirs: irregular widths, thicker at the crown
    nv = 13
    wts = rng.permutation(np.linspace(0.78, 1.24, nv))
    wts[nv // 2] = max(wts[nv // 2], 1.0) * 1.12
    th = math.pi - np.concatenate([[0], np.cumsum(wts) / wts.sum() * math.pi])
    vs = []
    for i in range(nv):
        ta, tb = th[i], th[i + 1]
        tm = 0.5 * (ta + tb)
        rin = hw
        rout = hw + 0.31 + 0.05 * math.sin(tm) + rng.uniform(-0.03, 0.045) + (0.03 if i == nv // 2 else 0)
        rm = 0.5 * (rin + rout)
        hx = 0.5 * (ta - tb) * rm - 0.007
        zc_abs = zs + rm * math.sin(tm)
        xm = xc + rm * math.cos(tm)
        back = float(face_apo(k, xm, zc_abs)) - leaf_apo - 0.012
        vs.append((tm, rm, hx, 0.5 * (rout - rin) - 0.004, back, zc_abs, 0.055 + rng.uniform(0, 0.012) + (0.012 if i == nv // 2 else 0)))
        poly = [(xc + rin * math.cos(a), zs + rin * math.sin(a)) for a in np.linspace(tb, ta, 5)] + \
               [(xc + rout * math.cos(a), zs + rout * math.sin(a)) for a in np.linspace(ta, tb, 5)]
        F.DRESSED_POLYS[k].append(poly)
    # radial joints between voussoirs: mortar wedges recessed 1.2 cm from the face and the intrados
    for i in range(1, nv):
        tj = th[i]
        r0_ = hw + 0.03
        r1_ = min(vs[i - 1][1] + vs[i - 1][3], vs[i][1] + vs[i][3]) - 0.02
        cs, sn = math.cos(tj), math.sin(tj)
        tx, tz = -sn, cs
        wf_ = float(face_apo(k, xc + 0.5 * (r0_ + r1_) * cs, zs + 0.5 * (r0_ + r1_) * sn)) - F.A_REF + 0.055 - 0.031
        P8 = []
        for rr_ in (r0_, r1_):
            for dd_ in (-0.0095, 0.0095):
                for ww_ in (leaf_apo - F.A_REF, wf_):
                    P8.append((xc + rr_ * cs + dd_ * tx, zs + rr_ * sn + dd_ * tz, ww_))
        P8 = np.array(P8)
        Wp = fmap(k, P8[:, 0], P8[:, 1], P8[:, 2])
        quads = np.array([(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        F.JOINT_ACC.add(Wp, quads, "M_mortar")
    vs = np.array(vs)
    S = stone_rec(np.zeros(nv), vs[:, 5], vs[:, 2], vs[:, 3], vs[:, 6], vs[:, 4],
                  rng.uniform(0.010, 0.015, nv), vs[:, 5], rng)
    dress_irregular(S, rng, rot_sd=0.0)
    S["th"] = vs[:, 0]
    S["rm"] = vs[:, 1]

    def premap(x, y, SS):
        t = SS["th"][:, None] - x / SS["rm"][:, None]
        R = SS["rm"][:, None] + y
        xf = xc + R * np.cos(t)
        zf = zs + R * np.sin(t)
        return facet_s(k, xf, SS["zcrs"][:, None]), zf

    _lay(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, premap=premap, dressed=True, grid=(22, 24))


def build_rect_dressing(acc_d, op, rng, sill_acc):
    k, xc, hw, z0, z1 = op["k"], op["xc"], op["hw"], op["z0"], op["z1"]
    depth = op["depth"]
    fr_apo = F.A_REF - depth
    h = z1 - z0
    if op.get("surround") == "timber":
        # simple heavy timber frame set in the rubble (ref1): no dressed jambs, only the stone sill;
        # the timber lintel (built with the frame) bears 0.16 m into the rubble each side.
        F.DRESSED_POLYS[k].append([(xc - hw - 0.17, z1 - 0.01), (xc + hw + 0.17, z1 - 0.01),
                                 (xc + hw + 0.17, z1 + 0.21), (xc - hw - 0.17, z1 + 0.21)])
        build_sill(sill_acc, op, rng)
        return
    nj = 3 if h > 0.8 else 2
    hs = rng.uniform(0.9, 1.1, nj)
    hs = hs / hs.sum() * h
    zz = z0 + np.concatenate([[0], np.cumsum(hs)])
    recs = []
    for side in (-1, 1):
        for i in range(nj):
            long_ = (i % 2 == 0) == (side < 0)
            wd = (0.30 if long_ else 0.22) * (1.0 if hw > 0.2 else 0.85) + rng.uniform(-0.02, 0.02)
            za, zb = zz[i] + 0.006, zz[i + 1] - 0.006
            x_in = xc + side * hw
            xa, xb = sorted([x_in, x_in + side * wd])
            zc = 0.5 * (za + zb)
            back = float(face_apo(k, x_in, zc)) - fr_apo - 0.006
            recs.append((0.5 * (xa + xb), zc, 0.5 * (xb - xa) - 0.006, 0.5 * (zb - za), 0.045 + rng.uniform(0, 0.01), back))
            F.DRESSED_POLYS[k].append([(xa, za), (xb, za), (xb, zb), (xa, zb)])
    # lintel
    lw = hw + (0.30 if hw > 0.2 else 0.22) + rng.uniform(0.0, 0.05)
    lh = 0.26 if hw > 0.2 else 0.2
    za, zb = z1 + 0.006, z1 + lh
    zc = 0.5 * (za + zb)
    recs.append((xc + rng.uniform(-0.03, 0.03), zc, lw, 0.5 * (zb - za), 0.05, float(face_apo(k, xc, zc)) - fr_apo - 0.006))
    F.DRESSED_POLYS[k].append([(xc - lw, za), (xc + lw, za), (xc + lw, zb), (xc - lw, zb)])
    R = np.array(recs)
    S = stone_rec(facet_s(k, R[:, 0], R[:, 1]), R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5],
                  rng.uniform(0.010, 0.015, len(R)), R[:, 1], rng)
    dress_irregular(S, rng)
    _lay(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(24, 24))
    build_sill(sill_acc, op, rng)


def build_sill(sill_acc, op, rng):
    """projecting stone sill: weathered, tooled top, drip groove underneath, chipped arrises."""
    k, xc, hw, z0 = op["k"], op["xc"], op["hw"], op["z0"]
    depth = op["depth"]
    sw = hw + (0.16 if hw > 0.2 else 0.12)
    st = 0.13 if hw > 0.2 else 0.11
    proj = 0.07 if hw > 0.2 else 0.05
    ztop = z0 - 0.004
    wf = 0.04 + proj          # front of sill relative to wall face plane
    wb = -depth - 0.02
    c = 0.012
    prof = np.array([(wb, ztop - st), (wf - 0.035, ztop - st), (wf - 0.035, ztop - st + 0.014),
                     (wf - 0.022, ztop - st + 0.014), (wf - 0.022, ztop - st), (wf - c, ztop - st),
                     (wf, ztop - st + c), (wf, ztop - 0.02 - c), (wf - c, ztop - 0.02),
                     (0.0, ztop), (wb, ztop)])
    xs = np.linspace(xc - sw, xc + sw, 36)
    nx_, npf = len(xs), len(prof)
    V = np.zeros((nx_, npf, 3))
    V[:, :, 0] = xs[:, None]
    V[:, :, 1] = prof[None, :, 1]
    V[:, :, 2] = prof[None, :, 0]
    V[:, :, 1] += 0.004 * np.sin(np.linspace(0, 3, nx_))[:, None] * (V[:, :, 2] > -0.01)
    # out of level by ~1 deg, tooled undulation, worn & chipped front arris
    V[:, :, 1] += (xs[:, None] - xc) * math.tan(math.radians(rng.uniform(-1.2, 1.2)))
    sd = rng.uniform(0, 50)
    thr = float(F.min_relief(fmap(k, np.array([xc]), np.array([ztop]), np.array([0.0])))[0])
    kt = 1.0 if 0.003 >= thr else 0.0               # producer note 11: 3 mm tooling -> materials
    V[:, :, 1] += kt * 0.003 * fbm90(np.stack([V[:, :, 0] * 8 + sd, V[:, :, 2] * 8, V[:, :, 1] * 8], -1), 2)
    V[:, :, 2] += kt * 0.003 * fbm90(np.stack([V[:, :, 0] * 6, V[:, :, 1] * 9 + sd, V[:, :, 2]], -1), 2) * (V[:, :, 2] > 0.0)
    front = (V[:, :, 2] > wf - 0.03)
    for _ in range(rng.integers(2, 5)):
        cx_ = rng.uniform(xc - sw + 0.03, xc + sw - 0.03)
        rad = rng.uniform(0.015, 0.035)
        dd = np.clip(1 - np.abs(V[:, :, 0] - cx_) / rad, 0, 1) ** 1.2 * front * (rad * 0.35 >= thr)
        V[:, :, 2] -= dd * rad * 0.35
        V[:, :, 1] -= dd * rad * 0.25 * (V[:, :, 1] > ztop - 0.03)
    V = V.reshape(-1, 3)
    W = fmap(k, V[:, 0], V[:, 1], V[:, 2], a_ref=float(face_apo(k, xc, ztop)))
    i = np.arange(nx_ - 1)[:, None]
    j = np.arange(npf)[None, :]
    a = i * npf + j
    b = i * npf + (j + 1) % npf
    quads = np.stack([a, a + npf, b + npf, b], -1).reshape(-1, 4)
    caps = [np.arange(npf)[None, :], ((nx_ - 1) * npf + np.arange(npf)[::-1])[None, :]]
    sill_acc.add(W, [quads] + caps, "M_stone_dressed")
    F.DRESSED_POLYS[k].append([(xc - sw, ztop - st), (xc + sw, ztop - st), (xc + sw, ztop), (xc - sw, ztop)])


def hall_cull(S):
    P = hall_map(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
    return ~in_wing(P, margin=0.12, zpad=0.12)


def build_hall_masonry(coll, seed=101):
    rng = np.random.default_rng(seed)
    acc = Acc(F.prefix + "_hall_wall_stones")
    accd = Acc(F.prefix + "_hall_dressed_stones")
    F.JOINT_ACC = Acc(F.prefix + "_hall_dressed_joint_mortar")
    for op in F.OPENINGS:
        if op["kind"] == "arch":
            build_door_dressing(accd, op, rng)
        else:
            build_rect_dressing(accd, op, rng, accd)
    cfg = dict(seed=7 + (seed - 101), footing=0.33, ch=(0.085, 0.18), p_tall=0.08, len=(0.18, 0.62), foot_len=(0.40, 1.10),
               foot_lvl=(-0.10, 0.10), joint=(0.008, 0.017), front=(0.005, 0.032), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
               pillow=(0.002, 0.007), rot=0.004, p_double=0.07, p_long=0.05, back=0.09, bed_amp=0.028,
               slant=0.27, ch_mix=[(0.30, 0.08, 0.11), (0.38, 0.11, 0.16), (0.22, 0.16, 0.21), (0.10, 0.21, 0.25)],
               pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
    srange = lambda zm: [(0.0, float(hall_L(zm)))]
    S = layout_wall(rng, srange, -0.10, F.WALL_H, hall_excl, cfg)

    def hero_of(SS):
        t = np.mod(SS["sc"] / hall_L(SS["zcrs"]), 1.0)
        fac = np.round(t * 8).astype(int) % 8
        return np.isin(fac, (2, 3, 4)) & (SS["zc"] < 3.5), fac
    hero0, _ = hero_of(S)
    S = polygonize(S, (hero0 & (S["zc"] > 0.3)) | (S["foot"] > 0.5), np.random.default_rng(seed + 1818))
    S = rough_footing(S, np.random.default_rng(seed + 1819))
    pins, _, _ = fill_voids(S, srange, hall_excl, -0.10, F.WALL_H, rng, cfg, label="hall")
    S = cat_stones(S, pins)
    S = filt(S, hall_cull(S))
    log("  hall stones:", len(S["sc"]))
    # hero zone (SW, S door, SE facets): true polygonal outlines, split planes, chisel facets, chipped arrises
    hero, fac = hero_of(S)
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    foot = S["foot"] > 0.5
    poly_n = (hero | foot) & ~small
    hero = hero | foot
    npoly = int(sum(1 for i in np.flatnonzero(poly_n) if len(stone_outline(S, i)) != 4 or
                    abs(S["sbt"][i] - S["sbb"][i]) > 0.06 or abs(S["shl"][i] - S["shr"][i]) > 0.12))
    log(f"  hall hero stones {int(poly_n.sum())} (non-rectangular {npoly}), other {int((~hero & ~small).sum())}, "
        f"pins {int(small.sum())}")
    _lay_poly(acc, filt(S, poly_n), hall_map, "M_stone", np.random.default_rng(seed + 1919), side_depth=0.018,
                      rings=(0.8, 0.58, 0.33))
    # non-hero facets: N / NE / E / NW thinned (single side segment + chamfer band)
    _lay(acc, filt(S, ~hero & ~small), hall_map, "M_stone", rng, rough=1.0, nxy=5, noise_amp=0.008, nz2=True,
                 side_depth=0.018)
    _lay(acc, filt(S, small & hero), hall_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005, side_depth=0.018)
    _lay(acc, filt(S, small & ~hero), hall_map, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=0.018)
    finalize(acc, coll, smooth_deg=28.0)
    finalize(accd, coll, smooth_deg=24.0)          # crisp 1-1.5 cm arrises (no soft shading across the bevel)
    finalize(F.JOINT_ACC, coll)
    return S


def build_hall_mortar(coll):
    acc = Acc(F.prefix + "_hall_wall_mortar")
    # t = perimeter fraction; corner arcs of the rounded octagon are kept as knots
    tt = np.unique(np.round(np.concatenate([np.linspace(0, 1, 89), F.OT[(F.OB == 0)]]), 6))
    zs = np.concatenate([np.linspace(-0.05, F.WALL_H, 13)])

    def near(t, z, dt, dz):
        nr = np.zeros(len(t), bool)
        for op in F.OPENINGS:
            xl = (t - op["k"] / 8.0) * hall_L(z)
            ext = op["hw"] + 0.55
            ztop = op.get("z1", op.get("zs", 2.0) + op["hw"]) + 0.6
            nr |= (np.abs(xl - op["xc"]) < ext) & (z > op["z0"] - 0.6) & (z < ztop)
        return nr

    def keep(t, z):
        k = np.ones(len(t), bool)
        for op in F.OPENINGS:
            xl = (t - op["k"] / 8.0) * hall_L(z)
            k &= ~open_contains(op, xl, z, m=0.03)
        Pc = hall_map(t * hall_L(z), z, np.zeros(len(t)), z)
        k &= ~in_wing(Pc, margin=0.12, zpad=0.15)
        return k
    n = mortar_sheet(acc, lambda t, z, w: hall_map(t * hall_L(z), z, w, z), tt, zs, near, keep, sub=4, seed=1.0)
    log(f"  hall mortar cells {n}")
    finalize(acc, coll, recalc=False)


def build_hall_interior(coll):
    """reveal tubes through the wall at every opening plus, behind each window, a simple dark blocker room
    (floor, ceiling, side and back walls ~1.5 m deep): only the depth visible through the openings is modelled."""
    acc = Acc(F.prefix + "_hall_interior")

    def add_facing(V, F, mat, R):
        """add faces wound toward the viewer point R (in front of the opening): Unreal culls back faces."""
        out = []
        for f_ in F:
            f_ = np.array(f_)
            nrm = np.cross(V[f_[:, 1]] - V[f_[:, 0]], V[f_[:, 2]] - V[f_[:, 0]])
            flip = (nrm * (R - V[f_].mean(1))).sum(1) < 0
            f_[flip] = f_[flip][:, ::-1]
            out.append(f_)
        acc.add(V, out, mat)
    for op in F.OPENINGS:
        k = op["k"]
        zc_ = op.get("z1", op.get("zs", 1.5) + op["hw"])
        R_ = fmap(k, np.array([op["xc"]]), np.array([0.5 * (op["z0"] + zc_)]), np.array([0.6]))[0]
        o1 = open_outline(op, grow=0.05)
        o2 = open_outline(op, grow=0.20)
        if op["kind"] == "arch":
            o1[:2, 1] = np.maximum(o1[:2, 1], 0.0)
            o2[:2, 1] = np.maximum(o2[:2, 1], 0.0)
        n = len(o1)
        r1 = fmap(k, o1[:, 0], o1[:, 1], np.full(n, -op["depth"] + 0.005))
        r2 = fmap(k, o2[:, 0], o2[:, 1], np.zeros(n), a_ref=F.INNER_APO)
        V = np.concatenate([r1, r2])
        q = np.array([(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)])
        add_facing(V, [q], "M_mortar", R_)
        if op["kind"] == "arch":
            continue            # the door leaf is closed: nothing behind it can be seen
        # blocker room behind the window
        xa, xb = op["xc"] - op["hw"] - 0.9, op["xc"] + op["hw"] + 0.9
        z0, z1 = 0.12, F.WALL_H
        a_in, a_bk = F.INNER_APO + 0.02, F.INNER_APO - 1.5
        X = np.array([xa, xb, xb, xa, xa, xb, xb, xa])
        Z = np.array([z0, z0, z1, z1, z0, z0, z1, z1])
        Wv = np.array([0, 0, 0, 0, 1, 1, 1, 1], float)
        P = np.stack([X, Z, Wv], 1)
        V = np.concatenate([fmap(k, P[:4, 0], P[:4, 1], np.zeros(4), a_ref=a_in),
                            fmap(k, P[4:, 0], P[4:, 1], np.zeros(4), a_ref=a_bk)])
        # faces seen from the window: back wall, floor, ceiling, two sides
        add_facing(V, [np.array([[4, 5, 6, 7]]), np.array([[3, 2, 6, 7]]), np.array([[0, 3, 7, 4]]),
                    np.array([[1, 5, 6, 2]])], "M_mortar", R_)
        add_facing(V, [np.array([[0, 1, 5, 4]])], "M_stone", R_)
    finalize(acc, coll, recalc=False)


def build_hall_frame(coll, seed=202):
    rng = np.random.default_rng(seed)
    acc_p = Acc(F.prefix + "_hall_posts")
    acc_b = Acc(F.prefix + "_hall_post_bases")
    acc_k = Acc(F.prefix + "_hall_knee_braces")
    acc_pl = Acc(F.prefix + "_hall_eave_plate")
    up = np.array([0, 0, 1.0])
    for c in range(8):
        d, a = corner_dir(c)
        P0 = np.array([d[0] * F.R_POST, d[1] * F.R_POST, 0.0])
        if in_wing(P0 + np.array([0, 0, 1.5]), margin=-0.3, zpad=0.0):
            continue
        ex = np.array([-math.sin(a), math.cos(a), 0.0])     # tangential
        ey = np.array([d[0], d[1], 0.0])                    # radial
        # pedestal: dressed block with splayed foot, tooled faces, chipped arrises, set ~1-2 deg out of square
        hp = 0.35
        yaw = math.radians(rng.uniform(-2.0, 2.0))
        exr = ex * math.cos(yaw) + ey * math.sin(yaw)
        eyr = -ex * math.sin(yaw) + ey * math.cos(yaw)
        chips = rng.uniform(0, 1, (4, 4))
        psd = rng.uniform(0, 50)
        thr = float(F.min_relief(P0[None] + np.array([[0, 0, 0.2]]))[0])

        def ped_def(P, chips=chips, psd=psd, thr=thr):
            z = P[..., 0]
            s = 1 + 0.16 * np.clip(1 - z / 0.12, 0, 1) ** 1.5
            P = P.copy()
            # tooled faces: 2-5 mm undulation + pitched face inside a drafted margin
            und = 0.0035 * fbm90(np.stack([P[..., 0] * 9 + psd, P[..., 1] * 9, P[..., 2] * 9], -1), 2)
            ry, rz = np.abs(P[..., 1]) / 0.24, np.abs(P[..., 2]) / 0.24
            on_y = ry > rz
            marg = np.clip((np.minimum(np.where(on_y, rz, ry), 1 - z / 0.4) - 0.0) * 0.24 / 0.025, 0, 1)
            nud = (und + 0.002 * marg) * (0.0035 >= thr)       # tooled faces (note 11: materials)
            P[..., 1] += np.where(on_y, np.sign(P[..., 1]) * nud, 0.0)
            P[..., 2] += np.where(~on_y, np.sign(P[..., 2]) * nud, 0.0)
            # arris chips (1-3 cm), mostly on the vertical arrises and the top edge
            for c_ in chips:
                sy, sz = (1 if c_[0] < 0.5 else -1), (1 if c_[1] < 0.5 else -1)
                zc_ = 0.08 + 0.3 * c_[2]
                rad = 0.012 + 0.02 * c_[3]
                d = np.sqrt((P[..., 1] - sy * 0.24) ** 2 + (P[..., 2] - sz * 0.24) ** 2 + (z - zc_) ** 2)
                dep = rad * 0.6 * np.clip(1 - d / rad, 0, 1) ** 1.2 * (rad * 0.6 >= thr)
                P[..., 1] -= sy * dep
                P[..., 2] -= sz * dep
            P[..., 1] *= s
            P[..., 2] *= s
            return P
        obox(acc_b, (P0 - np.array([0, 0, 0.05]))[None], up, exr, eyr, hp + 0.05, 0.48, 0.48, 0.03, "M_stone_dressed",
             nx=10, ny=12, nz=12, deform=ped_def)
        # post: hand-hewn, +-1 deg lean, +-1 cm swell/taper, adze facets; modelled checks on the posts that
        # flank the door (c=2, 3) and the post by the SW window (c=1)
        checks = []
        if c in (1, 2, 3):
            checks.append(dict(face=1, pos=rng.uniform(-0.35, 0.35), x0=rng.uniform(0.08, 0.2), x1=rng.uniform(0.6, 0.85),
                               depth=rng.uniform(0.022, 0.032), width=rng.uniform(0.012, 0.018)))
            if c != 1:
                checks.append(dict(face=0 if c == 2 else 2, pos=rng.uniform(-0.3, 0.3), x0=rng.uniform(0.35, 0.5),
                                   x1=rng.uniform(0.8, 0.95), depth=rng.uniform(0.016, 0.024),
                                   width=rng.uniform(0.009, 0.013)))
        lean = np.clip(rng.normal(0, 0.009, 2), -0.0175, 0.0175)
        _hewn(acc_p, P0 + np.array([0, 0, hp - 0.01]), up, ex, ey, F.WALL_H - hp + 0.02, 0.28, 0.28, rng,
                    chamfer=0.03, nf=6, st_len=0.035, adze=0.008, lean=tuple(lean), swell=rng.uniform(-0.01, 0.01),
                    taper=rng.uniform(0.0, 0.01), wave=0.004, checks=checks, seed=40 + c, drop=(3,))
        # knee braces into the two adjacent plate runs
        for side, fk in ((-1, c), (1, (c + 1) % 8)):
            t = np.array([FT[fk][0], FT[fk][1], 0.0])
            nk = np.array([FN[fk][0], FN[fk][1], 0.0])
            base = np.array([d[0] * F.R_POST, d[1] * F.R_POST, 0.0])
            base = base - nk * (np.dot(base, nk) - (F.PLATE_APO + 0.02))
            dirv = -t if side < 0 else t
            pa = base + dirv * 0.12 + np.array([0, 0, 2.78])
            pc = base + dirv * 0.12 + np.array([0, 0, F.WALL_H - 0.04])
            pb = base + dirv * 0.56 + np.array([0, 0, F.WALL_H + 0.02])
            us = np.linspace(0, 1, 14)
            ctrl = pc * 0.85 + 0.15 * (pa + pb) * 0.5
            path = ((1 - us) ** 2)[:, None] * pa + (2 * us * (1 - us))[:, None] * ctrl + (us ** 2)[:, None] * pb
            path[0] -= dirv * 0.05
            path[-1] += np.array([0, 0, 0.05])
            wob = 0.006 * np.sin(us * 3.1 + c)
            path = path + wob[:, None] * nk
            # chunky Y-bracket arm, slightly thicker at the root, adze-wobbled
            nn_ = len(us)
            profs = np.stack([prof_rect(0.17 * (1.12 - 0.12 * u_), 0.16 + 0.01 * math.sin(7 * u_ + c), 0.024) for u_ in us])
            V, F = sweep(path, nk, profs)
            acc_k.add(V, F, "M_timber")
            peg(F, base + dirv * 0.09 + np.array([0, 0, 2.86]) + nk * 0.165, nk)
            peg(F, base + dirv * 0.46 + np.array([0, 0, F.WALL_H + 0.10]) + nk * (F.PLATE_W / 2 + 0.02), nk)
    # eave plate: 8 runs, lap-jointed corners with projecting ends
    for k in range(8):
        n, t = FN[k], FT[k]
        half = F.PLATE_APO * TAN22
        cA = n * F.PLATE_APO - t * half
        cB = n * F.PLATE_APO + t * half
        if in_wing(np.array([*(n * F.PLATE_APO), 3.5]), margin=-0.4, zpad=0.0):
            continue
        dz = rng.uniform(-0.004, 0.004)
        up_half = (k % 2 == 0)
        tv = np.array([t[0], t[1], 0.0])
        ey = np.array([n[0], n[1], 0.0])

        def pl_def(P):
            P = P.copy()
            P[..., 2] += 0.006 * np.sin(P[..., 0] * 1.3 + k)
            return P
        A3 = np.array([cA[0], cA[1], F.WALL_H + F.PLATE_H / 2 + dz])
        _hewn(acc_pl, A3 + tv * 0.02, tv, ey, np.array([0, 0, 1.0]), 2 * half - 0.04, F.PLATE_W, F.PLATE_H, rng,
                    chamfer=0.025, nf=3, st_len=0.11, adze=0.004, wave=0.007, seed=60 + k,
                    checks=[dict(face=1, pos=rng.uniform(-0.3, 0.3), x0=0.15, x1=0.7, depth=0.012, width=0.006)]
                    if k in (2, 3, 4) else (), drop=(1, 2))
        for end, sgn in ((cA, -1), (cB, 1)):
            zoff = F.PLATE_H / 4 if up_half else -F.PLATE_H / 4
            E3 = np.array([end[0], end[1], F.WALL_H + F.PLATE_H / 2 + zoff + dz])
            ext = 0.17
            o = E3 + tv * (-0.04) if sgn > 0 else E3 - tv * ext
            obox(acc_pl, o[None], tv, ey, np.array([0, 0, 1.0]), ext + 0.04, F.PLATE_W - 0.004, F.PLATE_H / 2 - 0.004,
                 0.02, "M_timber", nx=4)
            if sgn > 0:
                peg(F, E3 + np.array([0, 0, (F.PLATE_H / 4) if up_half else -(F.PLATE_H / 4)]),
                    np.array([0, 0, 1.0 if up_half else -1.0]))
    # raising plate (rafter plate) on top of the eave plate, scarf-jointed runs with pegs
    for k in range(8):
        n, t = FN[k], FT[k]
        if in_wing(np.array([*(n * F.PLATE_APO), 3.5]), margin=-0.4, zpad=0.0):
            continue
        half = (F.PLATE_APO + 0.02) * TAN22
        tv = np.array([t[0], t[1], 0.0])
        ey = np.array([n[0], n[1], 0.0])
        c0 = n * (F.PLATE_APO + 0.02) - t * (half + 0.06)
        o = np.array([c0[0], c0[1], F.PLATE_TOP + F.RPLATE_H / 2 + rng.uniform(-0.003, 0.003)])
        _hewn(acc_pl, o, tv, ey, np.array([0, 0, 1.0]), 2 * half + 0.12, 0.21, F.RPLATE_H, rng, chamfer=0.02,
                    nf=2, st_len=0.13, adze=0.0035, wave=0.006, seed=70 + k, drop=(1, 2))
        mid = n * (F.PLATE_APO + 0.02 + 0.105) + t * rng.uniform(-0.4, 0.4)
        peg(F, np.array([mid[0], mid[1], F.PLATE_TOP + 0.10]), ey)
    for a in (acc_b, acc_p, acc_k, acc_pl):
        finalize(a, coll)


def facet_obox(acc, k, x0, x1, z0, z1, w0, w1, r, mat, nx=4, ny=4, nz=4, deform=None, a_ref=None):
    """axis aligned box in facet-local coords (x,z,w) -> world (plumb)."""
    X = axn(np.array([x0]), np.array([x1]), np.array([r]), nx)
    Y = axn(np.array([z0]), np.array([z1]), np.array([r]), ny)
    Z = axn(np.array([w0]), np.array([w1]), np.array([r]), nz)
    P, quads = rbox_v(X, Y, Z, np.array([r]))
    P = P[0]
    if deform is not None:
        P = deform(P)
    W = fmap(k, P[:, 0], P[:, 1], P[:, 2], a_ref=a_ref)
    acc.add(W, quads, mat, uv=np.stack([P[:, 1], P[:, 0] + P[:, 2]], -1))


def rough_block(acc, k, x0, x1, z0, z1, w0, w1, r, mat, rng, amp=0.006, dip=0.0, a_ref=None, outline=0.0, chips=0):
    # chipped arrises: conchoidal dents at random points on the top edges (radius 3-6 cm, 1-2.5 cm deep)
    cps = []
    for _ in range(chips):
        side = int(rng.integers(0, 4))
        t_ = rng.uniform(0.15, 0.85)
        ex = x0 + (x1 - x0) * (t_ if side < 2 else (0.0 if side == 2 else 1.0))
        ew = (w0 if side == 0 else w1) if side < 2 else w0 + (w1 - w0) * t_
        cps.append((ex, ew, rng.uniform(0.03, 0.06), rng.uniform(0.01, 0.025)))

    thr = float(F.min_relief(fmap(k, np.array([(x0 + x1) / 2]), np.array([z1]), np.array([(w0 + w1) / 2]),
                                   a_ref=a_ref))[0])
    k_amp = 1.0 if amp >= thr else 0.0              # producer note 11: sub-threshold surface noise -> materials
    cps = [c_ for c_ in cps if c_[3] >= thr]

    def dfm(P):
        P = P.copy()
        nz = fbm90(P * 9.0 + rng.uniform(0, 50), 2) * k_amp
        P[:, 1] += amp * nz * (P[:, 1] > (z0 + z1) / 2)
        if outline:
            # irregular plan outline: edges wander, corners rounded off unevenly
            cx, cw = (x0 + x1) / 2, (w0 + w1) / 2
            ux = (P[:, 0] - cx) / ((x1 - x0) / 2)
            uw = (P[:, 2] - cw) / ((w1 - w0) / 2)
            o1 = fbm90(np.stack([P[:, 0] * 3.0, P[:, 2] * 3.0, np.full(len(P), 7.7)], -1), 2)
            P[:, 0] -= np.sign(ux) * np.abs(ux) ** 6 * (outline * (0.6 + 0.6 * o1))
            P[:, 2] -= np.sign(uw) * np.abs(uw) ** 6 * (outline * (0.6 - 0.6 * o1))
            cut = (np.abs(ux) * np.abs(uw)) ** 3
            P[:, 0] -= np.sign(ux) * cut * outline * 1.5
            P[:, 2] -= np.sign(uw) * cut * outline * 1.5
            # worn, slightly domed top with a hollow where feet land
            top = P[:, 1] > (z0 + z1) / 2
            P[:, 1] -= top * 0.012 * np.exp(-((ux * 1.3) ** 2 + (uw * 1.6) ** 2))
            P[:, 1] -= top * 0.015 * np.clip(np.abs(ux) ** 4 + np.abs(uw) ** 4, 0, 1)
        if dip:
            xr = (P[:, 0] - (x0 + x1) / 2) / ((x1 - x0) / 2)
            P[:, 1] -= dip * (1 - np.clip(xr, -1, 1) ** 2) * (P[:, 1] > (z0 + z1) / 2)
        for ex, ew, rad, dep in cps:
            dd = np.sqrt((P[:, 0] - ex) ** 2 + (P[:, 2] - ew) ** 2 + (P[:, 1] - z1) ** 2)
            P[:, 1] -= dep * np.clip(1 - dd / rad, 0, 1) ** 1.3
        P[:, 0] += k_amp * amp * 0.6 * fbm90(P[:, [1, 2, 0]] * 7.0, 2)
        P[:, 2] += k_amp * amp * 0.6 * fbm90(P[:, [2, 0, 1]] * 7.0 + 3, 2)
        return P
    nx_, nz_ = (24, 14) if chips else (12, 8)
    facet_obox(acc, k, x0, x1, z0, z1, w0, w1, r, mat, nx=nx_, ny=4, nz=nz_, deform=dfm, a_ref=a_ref)


def build_threshold(coll, seed=1010):
    rng = np.random.default_rng(seed)
    acc = Acc(F.prefix + "_threshold")
    op = F.OPENINGS[0]
    k, xc = op["k"], op["xc"]
    rough_block(acc, k, xc - 0.62, xc + 0.62, -0.08, 0.12, -0.55, 0.20, 0.025, "M_stone_dressed", rng, amp=0.004, dip=0.012,
                outline=0.012)
    # outside step stone 1.4 x 0.6 x 0.12 (top 0.115)
    rough_block(acc, k, xc - 0.70, xc + 0.70, -0.05, 0.115, 0.24, 0.84, 0.04, "M_stone", rng, amp=0.010, dip=0.0,
                outline=0.06, chips=3)
    # interior floor flags
    finalize(acc, coll)



# =================================================================================================================
# public components
# =================================================================================================================
def oct_hall_walls(g, seed=101):
    """KIT COMPONENT: the hall's rubble wall with its dressed surrounds, mortar body and opening reveals."""
    coll = g.sub("hall")
    build_hall_masonry(coll, seed=seed)
    build_hall_mortar(coll)
    build_hall_interior(coll)


def oct_hall_frame(g, seed=202):
    """KIT COMPONENT: corner posts on pedestals, paired knee braces, eave plate and raising plate (pegged)."""
    build_hall_frame(g.sub("hall"), seed=seed)


def door_threshold(g, seed=1010):
    """KIT COMPONENT: worn threshold stone and the built-in outside step of the principal (arched) door."""
    build_threshold(g.sub("hall"), seed=seed)
