"""components.tail_vane -- the fixed tail vane on a rear boom (client correction): doubled hewn boom, hanger,
braces, king post with a lead collar, and the fanned board vane (kit 1.2.0).

Public component: rear_tail_vane(g, boom_end, vane_s0, vane_length, vane_h0, vane_h1, seed).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (relief_far, cap_z, capw, inst_bolts, to_cap_local)  # noqa: F401
from ..tmplmesh import (D2R, PI, T_BLK, T_BRD, T_PLK, add_grid, blocks_world, bolt_heads, circle_prof, frame_mats,
    hewn_between, log, member, orient, rbox, rect_prof, sweep, unit)  # noqa: F401


def _hewn(g, *a, **kw):
    """hewn_between with the frame's producer-note-11 threshold (adze marks and checks -> material)."""
    kw.setdefault("min_relief", relief_far(g))
    return hewn_between(*a, **kw)


def tail_boom(g, parts, x0=None, x1=None, z=None, seed="tail"):
    """Doubled hewn boom with spacer blocks, iron bands, a hanger with a lower brace and an upper brace from
    the rear ridge end; all in cap-local coordinates (turns with the cap). Returns the boom droop function."""
    x0 = g.TB_X0 if x0 is None else x0
    x1 = g.TB_X1 if x1 is None else x1
    z = g.TB_Z if z is None else z
    P_b, P_i = parts["tail_boom"], parts["tail_iron"]
    rng = g.RNG(seed + "_boom")
    Z3 = np.array([0, 0, 1.0])
    droop = 0.022                                   # cantilever sag at the tip

    def zb(x):
        return z - droop * np.clip((x0 - np.asarray(x, float)) / (x0 - x1), 0, 1) ** 2

    def C(x, y, zz):
        return capw(g, np.array([x, y, zz], float))
    for sy in (-1, 1):
        _hewn(g, P_b, "M_timber_weathered", C(x0, sy * g.TB_YC, zb(x0)), C(x1 + rng.uniform(-0.02, 0.02),
                     sy * g.TB_YC, zb(x1)), g.TB_RW, g.TB_RH, Z3, rng, chamfer=(0.012, 0.022), checks=(1, 1),
                     check_len=(0.6, 1.2), end_split=1, bow=0.006)
    # spacer blocks between the rails (behind the vane the boards themselves fill the gap)
    for xs_ in (-1.30, -2.05, -2.80):
        blocks_world(P_b, "M_timber", C(xs_, 0.0, zb(xs_))[None],
                     frame_mats(capw(g, np.array([[1.0, 0, 0]])), capw(g, np.array([[0, 1.0, 0]])), Z3[None]),
                     [[0.07, g.TB_GAP / 2 + 0.002, g.TB_RH / 2 - 0.008]], c=0.006, T=T_BLK)
    # iron bands round the rail pair, each with a through-bolt (hex heads both sides)
    hb, hh = g.TB_YC + g.TB_RW / 2 + 0.003, g.TB_RH / 2 + 0.003
    for xb_ in (-1.92, -2.62, -3.30, -4.75, -5.92):
        zc_ = float(zb(xb_))
        loop = []
        cr = 0.01
        for (cy, cz) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            for a_ in np.linspace(0, PI / 2, 4):
                aa_ = math.atan2(cz, cy) - PI / 4 + a_
                loop.append((cy * (hb - cr) + cr * math.cos(aa_), cz * (hh - cr) + cr * math.sin(aa_)))
        loop = np.array(loop)
        path = capw(g, np.stack([np.full(len(loop), xb_), loop[:, 0], zc_ + loop[:, 1]], 1))
        Pb_, Tb_ = sweep(path[None], rect_prof(0.006, 0.045, 0.0015), up=capw(g, np.array([[1.0, 0, 0]]))[0],
                         closed=True)
        P_i.add(Pb_, Tb_, mat="M_iron", smooth="bevel")
        for sy in (-1, 1):
            inst_bolts(g, g.prefix + "_tail_bolt", C(xb_ + 0.04, sy * (hb + 0.002), zc_ - 0.02)[None],
                       capw(g, np.array([[0, sy, 0.0]])), 0.016, leaned=True, rng=rng)
    # hanger: two uprights clasping the rails just outside the rear eave, a cross block at their foot, and iron
    # stays from the foot back to the sheer ends (the hanger is carried by the cap frame)
    xh = -(g.CAP_AB + 0.18)
    zfoot = g.ZCT - 0.49
    yu = g.TB_YC + g.TB_RW / 2 + 0.036
    for sy in (-1, 1):
        _hewn(g, P_b, "M_timber_weathered", C(xh, sy * yu, zfoot), C(xh, sy * yu, zb(xh) + 0.12), 0.09, 0.07,
                     capw(g, np.array([1.0, 0, 0])), rng, checks=(0, 1), end_split=1)
        for zq in (zb(xh), zfoot + 0.05):
            inst_bolts(g, g.prefix + "_tail_bolt", C(xh, sy * (yu + 0.036), zq)[None], capw(g, np.array([[0, sy, 0.0]])), 0.018,
                       leaned=True, rng=rng)
        # stay rod (dia 22 mm) from the hanger foot to the sheer end, with an eye plate on the sheer
        a_ = C(xh + 0.03, sy * (yu + 0.04), zfoot + 0.05)
        b_ = C(-1.00, sy * 0.70, g.ZCT + 0.30 - 0.07)       # sheer end (sheer centre ZCT + 0.30)
        Pr, Tr = sweep(np.stack([a_, b_])[None], circle_prof(0.011, 8), up=Z3)
        P_i.add(Pr, Tr, mat="M_iron", smooth="all")
    blocks_world(P_b, "M_timber", C(xh, 0.0, zfoot + 0.05)[None],
                 frame_mats(capw(g, np.array([[0, 1.0, 0]])), capw(g, np.array([[-1.0, 0, 0]])), Z3[None]),
                 [[yu - 0.045, 0.05, 0.05]], c=0.01, T=T_BLK)
    Y3 = capw(g, np.array([0, 1.0, 0]))
    # lower brace (round 5: hewn 0.08 x 0.10, 1.5-2.5 cm chamfers like the rails): from the cross block up and out
    # to the boom underside (just inside the vane), iron shoe
    xl = -3.24
    _hewn(g, P_b, "M_timber_weathered", C(xh - 0.03, 0.0, zfoot + 0.10), C(xl, 0.0, zb(xl) - g.TB_RH / 2 - 0.04),
                 0.10, 0.08, Y3, rng, chamfer=(0.015, 0.025), checks=(0, 1), end_split=0)
    blocks_world(P_i, "M_iron", C(xl, 0.0, zb(xl) - g.TB_RH / 2 - 0.02)[None],
                 frame_mats(capw(g, np.array([[1.0, 0, 0]])), capw(g, np.array([[0, 1.0, 0]])), Z3[None]),
                 [[0.07, g.TB_YC + g.TB_RW / 2, 0.02]], c=0.003, T=T_BLK)
    # ---- round 5: hewn king post (0.12 x 0.12) rising ~0.30 m through the rear hip-end saddle from the cap
    # frame, with a draped lead collar; the upper brace is carried on it by an iron strap shoe and 2 bolts ----
    xk = g.XR0 - 0.16
    zt, xu1 = king_post(g, parts, xk, rng)
    a_ = C(xk - 0.02, 0.0, zt - 0.085)
    b_ = C(xu1, 0.0, zb(xu1) + g.TB_RH / 2 + 0.05)
    _hewn(g, P_b, "M_timber_weathered", a_, b_, 0.10, 0.08, Y3, rng, chamfer=(0.015, 0.025), checks=(1, 1),
                 check_len=(0.4, 0.8), end_split=0)
    bdir = unit(b_ - a_)
    for sy in (-1, 1):
        # strap shoe: a plate down the post side and a plate along the brace side, each with a pooled hex bolt
        pa = C(xk, sy * 0.064, zt - 0.03)
        pb = C(xk, sy * 0.064, zt - 0.24)
        member(P_i, "M_iron", pa[None], pb[None], 0.05, 0.007, up=Y3 * sy, c=0.002)
        qa = a_ + Y3 * sy * 0.044 + bdir * 0.05
        qb = a_ + Y3 * sy * 0.044 + bdir * 0.33
        member(P_i, "M_iron", qa[None], qb[None], 0.05, 0.007, up=Y3 * sy, c=0.002)
        inst_bolts(g, g.prefix + "_tail_bolt", np.stack([C(xk, sy * 0.068, zt - 0.15), a_ + Y3 * sy * 0.048 + bdir * 0.24]),
                   np.stack([Y3 * sy, Y3 * sy]), 0.018, leaned=True, rng=rng)
    blocks_world(P_i, "M_iron", C(xu1, 0.0, float(zb(xu1)) + g.TB_RH / 2 + 0.008)[None],
                 frame_mats(capw(g, np.array([[1.0, 0, 0]])), capw(g, np.array([[0, 1.0, 0]])), Z3[None]),
                 [[0.07, 0.055, 0.008]], c=0.002, T=T_BLK)
    log("tail boom: rails x' %.2f..%.2f at z %.2f (droop %.3f), hanger at x' %.2f, braces to x' %.2f / %.2f"
        % (x0, x1, z, droop, xh, xl, xu1))
    return zb


def king_post(g, parts, xk, rng, h_above=0.30, half=0.06):
    """Hewn king post (kit component) through the cap roof at cap-local (xk, 0): from the cap frame 0.30 m
    under the covering to `h_above` over it, with a draped lead collar (upstand 6 cm, apron 9 cm) dressed onto
    the local roof surface (sampled from the built covering). Returns (post top z, x' of the brace foot)."""
    P_b, P_ir = parts["tail_boom"], parts["cap_iron"]
    Lc = to_cap_local(g, np.concatenate(parts["cap_shingles"].V + parts["cap_iron"].V))

    def roof(x, y, r=0.035):
        m_ = (np.abs(Lc[:, 0] - x) < r) & (np.abs(Lc[:, 1] - y) < r)
        return float(Lc[m_, 2].max()) if m_.any() else float(cap_z(g, np.array(x), np.array(y))) + 0.04
    z0 = roof(xk, 0.0, 0.07)
    zt = z0 + h_above
    _hewn(g, P_b, "M_timber_weathered", capw(g, np.array([xk, 0.0, z0 - 0.30])), capw(g, np.array([xk, 0.0, zt])),
                 2 * half, 2 * half, capw(g, np.array([1.0, 0, 0])), rng, chamfer=(0.012, 0.02), checks=(1, 1),
                 check_len=(0.15, 0.3), end_split=1)
    # lead collar: square ring path round the post
    n_side = 6
    def sq(e):
        pts = []
        for (ax0, ay0, ax1, ay1) in ((1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1), (-1, -1, 1, -1)):
            for q in range(n_side):
                f = q / n_side
                pts.append((ax0 + (ax1 - ax0) * f, ay0 + (ay1 - ay0) * f))
        return np.array(pts) * e
    rows = []
    for (e, dz, up_) in ((half + 0.006, 0.065, True), (half + 0.006, 0.008, False), (half + 0.05, 0.007, False),
                         (half + 0.09, 0.004, False)):
        P2 = sq(e)
        zz = np.array([roof(xk + px, py, 0.06) for px, py in P2])
        zz = (np.roll(zz, 1) + 2 * zz + np.roll(zz, -1)) / 4        # dressed lead: no crumple following each butt
        zz = (np.roll(zz, 1) + 2 * zz + np.roll(zz, -1)) / 4 + 0.006
        if up_:
            zz = np.maximum(zz, z0) + dz - 0.008 + 0.008
        else:
            zz = zz + dz
        rows.append(np.stack([xk + P2[:, 0], P2[:, 1], zz], 1))
    rows[0][:, 2] = np.maximum(rows[0][:, 2], rows[1][:, 2] + 0.05)
    G = capw(g, np.stack(rows, 1))
    nrm_ = np.cross(G[1, 2] - G[0, 2], G[0, 3] - G[0, 2])
    add_grid(P_ir, "M_lead", G, wrap=True, flip=bool(nrm_[2] < 0), smooth="all")
    # a turned-over lip at the upstand top
    log("king post at x' %.2f: roof %.3f -> top %.3f m (0.12 x 0.12 hewn, lead collar)" % (xk, z0, zt))
    return zt, -3.26


def tail_vane(g, parts, zb, s0=None, length=None, h0=None, h1=None, seed="tail"):
    """Vertical board panel in the plane of the boom, clasped between the two rails: slightly fanned boards
    (2 cm), ragged outer edge, one cracked board, one replaced board, two cleats on each face, nails."""
    s0 = g.TV_S0 if s0 is None else s0
    length = g.TV_LEN if length is None else length
    h0 = g.TV_H0 if h0 is None else h0
    h1 = g.TV_H1 if h1 is None else h1
    P_v, P_i = parts["tail_vane"], parts["tail_iron"]
    rng = g.RNG(seed + "_vane")

    def vt(s):
        return h0[1] + (h1[1] - h0[1]) * np.clip(s / length, 0, 1)

    def vbot(s):
        return h0[0] + (h1[0] - h0[0]) * np.clip(s / length, 0, 1)
    ws = []
    while sum(ws) < length:
        ws.append(rng.uniform(0.17, 0.24))
    ws = np.array(ws) * length / sum(ws)
    edges = np.concatenate([[0], np.cumsum(ws)])
    nb = len(ws)
    cracked = int(rng.integers(2, nb // 2))
    replaced = int(rng.integers(nb // 2, nb - 2))
    nails = []
    cleat_z = (0.48, -0.40)
    for j in range(nb):
        g0, g1 = rng.uniform(0.002, 0.0045, 2)
        sa, sb_ = edges[j] + g0, edges[j + 1] - g1
        w = sb_ - sa
        sc_ = (sa + sb_) / 2
        fan = 7.0 * D2R * (sc_ / length - 0.35)
        th = 0.026 if j == replaced else 0.02
        pieces = [(-1.0, 1.0, 0.0)]
        if j == cracked:            # split along its upper 60 %: two halves 5 mm apart, one sprung 6 mm out
            pieces = [(-1.0, 0.0, -0.0025), (0.0, 1.0, 0.0025)]
        for (q0, q1, dq) in pieces:
            h = np.array([[0.5, th / 2, 0.5]])
            P = rbox(T_BRD, h, np.array([[0.004, min(0.004, th * 0.3), 0.008]]))
            tt = P[:, :, 0] + 0.5                      # 0 bottom .. 1 top
            lat = P[:, :, 2] + 0.5                     # 0 inner .. 1 outer (across the board)
            if j == cracked:
                lat = q0 / 2 + 0.5 + lat * (q1 - q0) / 2
                # the crack runs only through the top 60 %: below that the halves join
                gap_ = np.where(tt > 0.4, dq * np.clip((tt - 0.4) / 0.1, 0, 1), 0.0)
            else:
                gap_ = 0.0
            s_ = sa + lat * w + gap_
            rag_t = 0.0 if j == replaced else rng.uniform(-0.03, 0.02) + 0.012 * np.sin(lat * 7 + j)
            rag_b = 0.0 if j == replaced else rng.uniform(-0.02, 0.03) + 0.01 * np.sin(lat * 5 + 2 * j)
            if j == nb - 1:                            # outermost board: top corner broken off
                rag_t = rag_t - 0.09 * np.clip((lat - 0.3) / 0.7, 0, 1) ** 1.5
            v = (vbot(s_) + rag_b) + tt * ((vt(s_) + rag_t) - (vbot(s_) + rag_b))
            s2 = s_ + math.tan(fan) * v
            y = P[:, :, 1] + rng.uniform(-0.002, 0.002) + 0.004 * ((2 * lat - 1) ** 2 - 0.33) * rng.choice([-1, 1])
            if j == cracked:
                y = y + np.where((tt > 0.5) & (lat > 0.5), 0.006 * (tt - 0.5) * 2, 0.0)
            xq = -s0 - s2
            Q = np.stack([xq, y, zb(xq) + v], -1)
            W = capw(g, Q)
            T = orient(T_BRD, W[0])
            P_v.add(W, T, Pl=P, mat="M_timber" if j == replaced else "M_timber_weathered", smooth="bevel",
                    wear=0.15 if j == replaced else (0.85 if j in (cracked, nb - 1) else None))
        for cz in cleat_z:
            for sg in (-1, 1):
                nails.append((-s0 - sc_ + rng.uniform(-0.03, 0.03), sg * (th / 2 + 0.022), cz + rng.uniform(-0.01, 0.01)))
    # cleats: both faces, above and below the boom
    for cz in cleat_z:
        for sg in (-1, 1):
            sa, sb_ = 0.04, length - rng.uniform(0.06, 0.12)
            h = np.array([[(sb_ - sa) / 2, 0.011, 0.035]])
            P = rbox(T_PLK, h, np.array([[0.006, 0.005, 0.006]]))
            xq = -s0 - (sa + sb_) / 2 - P[:, :, 0]
            Q = np.stack([xq, sg * (0.0105 + 0.011) + P[:, :, 1] * sg, zb(xq) + cz + P[:, :, 2] +
                          rng.uniform(-0.01, 0.01) * P[:, :, 0] / h[0, 0]], -1)
            W = capw(g, Q)
            P_v.add(W, orient(T_PLK, W[0]), Pl=P, mat="M_timber_weathered", smooth="bevel")
    nails = np.array(nails)
    xq = nails[:, 0]
    C = capw(g, np.stack([xq, nails[:, 1], zb(xq) + nails[:, 2]], 1))
    Nn = capw(g, np.stack([0 * xq, np.sign(nails[:, 1]), 0 * xq], 1))
    bolt_heads(P_i, C, Nn, rad=0.008, hgt=0.005, sides=6)
    log("tail vane: %d boards over %.2f m (x' %.2f..%.2f), height %.2f -> %.2f m, cracked %d, replaced %d"
        % (nb, length, -s0, -s0 - length, h0[1] - h0[0], h1[1] - h1[0], cracked, replaced))


def rear_tail_vane(g, boom_end=None, vane_s0=None, vane_length=None, vane_h0=None, vane_h1=None, seed="tail"):
    """Fixed tail vane on a rear boom (kit component, client correction): a doubled hewn boom on the shaft heading
    running back from the cap to cap-local x' = boom_end, with spacer blocks, iron bands, a hanger, a lower brace
    and an upper brace from a king post through the cap; the fanned board vane (vane_length long from vane_s0
    behind the axis, vane_h0 / vane_h1 = (bottom, top) at its inner / outer edge) clasped between the rails.
    It turns with the cap (<PREFIX>_tail_boom / _tail_vane / _tail_iron)."""
    kw = {k_: v_ for k_, v_ in (("TB_X1", boom_end), ("TV_S0", vane_s0), ("TV_LEN", vane_length),
                                ("TV_H0", vane_h0), ("TV_H1", vane_h1)) if v_ is not None}
    g.set(**kw)
    zb = tail_boom(g, g.parts, seed=seed)
    tail_vane(g, g.parts, zb, seed=seed)
