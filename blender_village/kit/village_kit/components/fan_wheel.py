"""components.fan_wheel -- the annular fan-wheel rotor of the tower windmill (kit 1.2.0): board blades on two
iron rings, four hewn arms, poll end, spokes, rivets, pooled bolt heads.

Public component: fan_wheel(g, r_in, r_rim, r_tip, n_blades, pitch, hub_d, seed)  (alias wind_wheel).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (relief_far, er_t, hex_heads, loc3, rotw, stock_depth, stock_w)  # noqa: F401
from ..tmplmesh import (D2R, PI, T_BRD, T_DRS, T_PLK, circle_prof, hewn_beam, lathe, member, perm_tmpl, rbox,
    rect_prof, sweep, unit, xform)  # noqa: F401


def build_rotor(g, parts):
    rng = g.RNG("rotor")
    P_poll, P_wir, P_ri = parts["poll_end"], parts["wheel_spokes"], parts["rotor_iron"]
    letters = "ABCD"
    Z3 = np.array([0, 0, 1.0])
    for i in range(4):
        L = letters[i]
        P_st = parts["wheel_arm_%s" % L]
        phi = g.PHI_A + i * PI / 2
        er, t = er_t(phi)
        sw = stock_w(i)
        # wheel arm (client correction: the four arms are the fan wheel's arms, 0.30 at the poll end tapering to
        # 0.17 at the rim, ending just past the outer ring with a bolted strap; no sails)
        r0, r1 = -0.15, g.ARM_R1
        # hewn stock: adze scallops, worn chamfers (2-4 cm before the taper -> 1.5-3 cm), 1-2 long checks,
        # split end grain at the tip
        P, Th = hewn_beam(rng, r1 - r0, 0.30, 0.30, chamfer=(0.02, 0.04), adze=(0.005, 0.008), min_relief=relief_far(g),
                          checks=(1, 2), check_len=(0.6, 1.5), end_split=1, faces_check=(1, 2))
        r = (r0 + r1) / 2 + P[:, :, 0]
        sc = stock_depth(g, r, i) / 0.30
        Q = np.stack([r, P[:, :, 1] * sc, P[:, :, 2] * sc + sw], -1)
        Q[..., 1] += rng.uniform(-0.012, 0.012) * (r / r1) ** 2
        Q[..., 2] += rng.uniform(-0.008, 0.008) * (r / r1) ** 2
        P_st.add(rotw(g, loc3(er, t, Q[..., 0], Q[..., 1], Q[..., 2])), Th, Pl=P[0], mat="M_timber_weathered",
                 smooth="bevel")
        # two iron bands (50 x 6 mm) round the stock near the poll end, each with a through-bolt
        for rb_ in (0.47 + rng.uniform(-0.02, 0.02), 0.80 + rng.uniform(-0.02, 0.02)):
            hs_ = float(stock_depth(g, rb_, i)) / 2 + 0.003
            cr = 0.012
            loop = []
            for (cl, cw) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
                for a_ in np.linspace(0, PI / 2, 4):
                    base_a = math.atan2(cw, cl) - PI / 4
                    aa_ = base_a + a_
                    loop.append((cl * (hs_ - cr) + cr * math.cos(aa_), sw + cw * (hs_ - cr) + cr * math.sin(aa_)))
            loop = np.array(loop)
            path = rotw(g, loc3(er, t, np.full(len(loop), rb_), loop[:, 0], loop[:, 1]))
            Pb_, Tb_ = sweep(path[None], rect_prof(0.006, 0.05, 0.0015), up=rotw(g, er[None])[0] - g.HUB, closed=True)
            P_ri.add(Pb_, Tb_, mat="M_iron", smooth="bevel")
            hex_heads(g, P_ri, np.array([loc3(er, t, rb_, 0.0, sw + hs_ + 0.003), loc3(er, t, rb_, 0.0, sw - hs_ - 0.003)]),
                      np.array([Z3, -Z3]), rad=0.02, hgt=0.014)
        # strap to the outer rim: a foot plate bolted (2 bolts) to the stock's back face, a flat iron drop
        # strap on the stock's centre line down to the rim, and a clip plate behind the rim
        hs = float(stock_depth(g, g.RING_OUT, i)) / 2
        wback = sw - float(stock_depth(g, g.RING_OUT, i)) / 2
        a_ = rotw(g, loc3(er, t, g.RING_OUT - 0.12, 0.0, wback - 0.0045))
        b_ = rotw(g, loc3(er, t, g.RING_OUT + 0.12, 0.0, wback - 0.0045))
        member(P_ri, "M_iron", a_[None], b_[None], 0.06, 0.009, up=g.S_AX, c=0.002)
        a_ = rotw(g, loc3(er, t, g.RING_OUT, 0.0, wback - 0.009))
        b_ = rotw(g, loc3(er, t, g.RING_OUT, 0.0, g.W_RING - 0.016))
        member(P_ri, "M_iron", a_[None], b_[None], 0.05, 0.009, up=rotw(g, t[None])[0] - g.HUB, c=0.002)
        a_ = rotw(g, loc3(er, t, g.RING_OUT - 0.06, 0.0, g.W_RING - 0.0115))
        b_ = rotw(g, loc3(er, t, g.RING_OUT + 0.06, 0.0, g.W_RING - 0.0115))
        member(P_ri, "M_iron", a_[None], b_[None], 0.05, 0.009, up=g.S_AX, c=0.002)
        cen = [loc3(er, t, g.RING_OUT + dr, 0.0, wback - 0.009) for dr in (-0.085, 0.085)] + \
              [loc3(er, t, g.RING_OUT + dr, 0.0, sw + float(stock_depth(g, g.RING_OUT, i)) / 2) for dr in (-0.085, 0.085)]
        nrm = [-Z3, -Z3, Z3, Z3]
        hex_heads(g, P_ri, np.array(cen), np.array(nrm), rad=0.02, hgt=0.014)

    er, t = er_t(g.PHI_A)
    # ---- poll end (cast-iron cross box) ----
    h = np.array([[0.23, 0.23, 0.37]])
    P = rbox(T_DRS, h, np.array([[0.025, 0.025, 0.025]]))
    P_poll.add(rotw(g, loc3(er, t, P[..., 0], P[..., 1], P[..., 2])), T_DRS, Pl=P, mat="M_iron", smooth="bevel")
    prof = np.array([(0.0, 0.37), (0.21, 0.37), (0.22, 0.39), (0.2, 0.42), (0.1, 0.44), (0.06, 0.5), (0.0, 0.51)])
    Pc, T = lathe(prof[None], 24, open_base=True)
    P_poll.add(rotw(g, Pc), T, mat="M_iron", smooth="all")
    prof = np.array([(0.0, -0.40), (0.36, -0.40), (0.37, -0.385), (0.36, -0.37), (0.0, -0.37)])
    Pc, T = lathe(prof[None], 32)
    P_poll.add(rotw(g, Pc), T, mat="M_iron", smooth="bevel")
    bolts = []
    for side in range(4):
        ang = g.PHI_A + side * PI / 2
        nrm_ = np.array([math.cos(ang), math.sin(ang), 0])
        tan = np.array([-math.sin(ang), math.cos(ang), 0])
        wl = (-0.28, -0.10) if side % 2 == 0 else (-0.28, 0.27)
        for u in (-0.15, 0.15):
            for w in wl:
                bolts.append((nrm_ * 0.232 + tan * u + np.array([0, 0, w]), nrm_))
    hex_heads(g, P_poll, np.array([b[0] for b in bolts]), np.array([b[1] for b in bolts]), rad=0.026, hgt=0.02)

    # ---- wind-wheel: 16 broad board blades on two flat iron rings (near-continuous annulus) ----
    P_rim, P_bl = parts["wheel_rim"], parts["wheel_blades"]
    for rr_ in (g.RING_IN, g.RING_OUT):
        a = np.linspace(0, 2 * PI, 161)[:-1]
        path = np.stack([rr_ * np.cos(a), rr_ * np.sin(a), np.full(160, g.W_RING) + 0.002 * np.sin(a * 3 + rr_)], 1)
        P, T = sweep(rotw(g, path)[None], rect_prof(0.06, 0.012, 0.003), up=g.S_AX, closed=True)
        P_rim.add(P, T, mat="M_iron", smooth="bevel")
    nbl = g.BL_N
    rivets_c, rivets_n = [], []
    for k in range(nbl):
        phi = g.PHI_A + (180.0 / nbl + 360.0 / nbl * k) * D2R + rng.normal(0, 0.3) * D2R
        er_k, t_k = er_t(phi)
        pitch = g.BL_PITCH + rng.uniform(-0.5, 0.5) * D2R
        dW = rng.uniform(-0.02, 0.02, 3)          # per-blade outline variation (+-2 cm)

        def blade_map(Q, er_k=er_k, t_k=t_k, pitch=pitch):
            r, l, z = Q[..., 0], Q[..., 1], Q[..., 2]
            l2 = l * math.cos(pitch) - z * math.sin(pitch)
            z2 = l * math.sin(pitch) + z * math.cos(pitch)
            return r[..., None] * er_k + l2[..., None] * t_k + (g.W_WH + z2)[..., None] * np.array([0, 0, 1.0])

        nb = 4 if k % 3 else 3
        fw = rng.uniform(0.85, 1.15, nb)
        fr = np.concatenate([[0], np.cumsum(fw)]) / fw.sum()
        for j in range(nb):
            h = np.array([[1.0, 0.01, 0.5]])
            P = rbox(T_BRD, h, np.array([[0.006, 0.0028, 0.006]]))
            u = (P[:, :, 0] + 1.0) / 2.0
            v = P[:, :, 2] + 0.5
            fl = fr[j] + (fr[j + 1] - fr[j]) * v
            lat = fl * 2 - 1
            tip = g.BL_R1 + rng.uniform(-0.03, 0.03) + 0.008 * np.sin(lat * 5 + k)
            r = g.BL_R0 - 0.02 + u * (tip - g.BL_R0 + 0.02)
            s_ = np.clip((r - g.BL_R0) / (g.BL_R1 - g.BL_R0), 0, 1)
            Wd = g.BL_W0 + (g.BL_W1 - g.BL_W0) * s_ + dW[0] * s_ + dW[1] * np.sin(s_ * PI)
            # worn tip corners on the outer boards
            if j in (0, nb - 1):
                corner = np.clip((u - 0.93) / 0.07, 0, 1) * np.clip((np.abs(lat) - 0.7) / 0.3, 0, 1)
                r = r - corner * rng.uniform(0.02, 0.04)
            gap = 0.0025                  # round 6: 5 mm board gap (reads 0.5-1 cm with the arrises)
            l = (fl - 0.5) * Wd + np.where(v < 0.5, gap, -gap) + dW[2] * s_ * 0.5
            z = P[:, :, 1] + rng.uniform(-0.003, 0.003) + 0.003 * (2 * v - 1) ** 2
            Q = np.stack([r, l, z], -1)
            P_bl.add(rotw(g, blade_map(Q)), perm_tmpl(T_BRD, True), Pl=P, mat="M_timber", smooth="bevel")
        # central batten on the back, bearing on both rings
        r0, r1 = g.BL_R0 - 0.03, g.BL_R1 - 0.12
        h = np.array([[(r1 - r0) / 2, 0.025, 0.018]])
        P = rbox(T_PLK, h, np.array([[0.006, 0.006, 0.006]]))
        Q = np.stack([(r0 + r1) / 2 + P[:, :, 0], P[:, :, 1], P[:, :, 2] - 0.028], -1)
        P_bl.add(rotw(g, blade_map(Q)), T_PLK, Pl=P, mat="M_timber", smooth="bevel")
        for rr_ in (g.RING_IN, g.RING_OUT):
            for lq in (-0.012, 0.012):
                rivets_c.append(blade_map(np.array([[rr_, lq, 0.0105]]))[0])
                rivets_n.append(blade_map(np.array([[rr_, lq, 1.0]]))[0] - blade_map(np.array([[rr_, lq, 0.0]]))[0])
    prof = np.array([(0.0, 0.0), (0.011, 0.0), (0.009, 0.004), (0.0, 0.006)])
    rivets_c = np.array(rivets_c)
    P, T = lathe(np.repeat(prof[None], len(rivets_c), 0), 6, open_base=True)
    Rr = []
    for nv_ in rivets_n:
        zz = unit(nv_)
        xx = unit(np.cross([0.3, 0.5, 0.8], zz))
        Rr.append(np.stack([xx, np.cross(zz, xx), zz], 1))
    P_wir.add(rotw(g, xform(P, np.array(Rr), rivets_c)), T, mat="M_iron", smooth="all")
    # spokes (8) from the poll end's rear flange to the inner ring (the rim is carried by the blade
    # battens and by the four arm straps)
    for k in range(8):
        for (phi, r0, w0, r1, w1) in ((g.PHI_A + (22.5 + 45 * k) * D2R, 0.30, -0.36, g.RING_IN, g.W_RING),):
            er_k, t_k = er_t(phi)
            n = 8
            rr = np.linspace(r0, r1 - 0.03, n)
            ww = np.linspace(w0, w1, n)
            P, T = sweep(rotw(g, loc3(er_k, t_k, rr, 0 * rr, ww))[None], circle_prof(0.0125, 8), up=g.S_AX)
            P_wir.add(P, T, mat="M_iron", smooth="all")
            pp = rotw(g, loc3(er_k, t_k, r1 - 0.06, 0.0, w1))
            pq = rotw(g, loc3(er_k, t_k, r1 + 0.035, 0.0, w1))
            member(P_wir, "M_iron", pp[None], pq[None], 0.04, 0.02, up=g.S_AX, c=0.004)


def fan_wheel(g, r_in=None, r_rim=None, r_tip=None, n_blades=None, pitch=None, hub_d=None, seed=None):
    """Annular fan-wheel rotor (kit component): n_blades board blades from r_in to r_tip on an inner ring (r_in)
    and an outer rim (r_rim), pitched `pitch` deg; four tapered hewn arms with iron bands and rim straps, the
    cast-iron poll end, spokes and rivets, hub `hub_d` in front of the tower axis.  Blade widths scale with
    16 / n_blades so the annulus stays near-continuous (<PREFIX>_wheel_* / _poll_end / _rotor_iron)."""
    kw = {}
    if r_in is not None:
        kw["RING_IN"] = kw["BL_R0"] = r_in
    if r_rim is not None:
        kw["RING_OUT"] = r_rim
    if r_tip is not None:
        kw["BL_R1"] = r_tip
    if n_blades is not None:
        kw["BL_N"] = n_blades
        kw["BL_W0"], kw["BL_W1"] = 0.55 * 16 / n_blades, 1.175 * 16 / n_blades
    if pitch is not None:
        kw["BL_PITCH"] = pitch * D2R
    if hub_d is not None:
        kw["HUB_D"] = hub_d
    g.set(**kw)
    with g.seeded(seed):
        build_rotor(g, g.parts)


wind_wheel = fan_wheel
