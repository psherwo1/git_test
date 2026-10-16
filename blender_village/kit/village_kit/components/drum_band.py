"""components.drum_band -- the balustrade band and cornice parts of a stone drum (kit 1.2.0): a row of stubby
turned stone balusters and the dentil corbels under the cornice, both as pooled variant meshes placed as linked
duplicates (producer note 3, village_kit.pools).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (R_out, place_instance, pool_part)  # noqa: F401
from ..split_stones import (stone_local)  # noqa: F401
from ..tmplmesh import (D2R, PI, T_BLK_ABX, T_BLK_PLX, blocks_world, euler, lathe, log)  # noqa: F401


def baluster_row(g, rb, spans, z0, z1, n_var=8, pitch=0.22):
    """Relief 'balustrade' of stubby turned balusters (kit component): a pool of 8 variant meshes (5 turned,
    2 eroded, 1 plain replacement block), placed as linked duplicates along the drum with pitch +-1.5 cm,
    yaw +-7 deg and lean +-1.5 deg in the object transforms. Variant frame: +x outward, z up from z0."""
    HB = z1 - z0
    TP, TA = 0.022, 0.022
    hs0 = HB - TP - TA
    base = np.array([(0.034, 0.0), (0.041, 0.005), (0.042, 0.015), (0.035, 0.021), (0.046, 0.044), (0.048, 0.062),
                     (0.041, 0.079), (0.030, 0.089), (0.038, 0.095), (0.039, 0.104), (0.031, 0.110),
                     (0.036, 0.118), (0.036, 1.0)])
    base[-1, 1] = hs0
    base[:-1, 1] *= hs0 / 0.126
    m = 16
    for v in range(n_var):
        pp = pool_part(g, "baluster_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = g.RNG("baluster_var_%d" % v)
        if v < n_var - 1:
            dh = rv.uniform(-0.008, 0.008)
            prof = base.copy()
            prof[:, 1] *= (hs0 + dh) / hs0
            prof[:, 0] *= rv.uniform(0.9, 1.1)
            prof[:, 0] += rv.normal(0, 0.001, len(prof))
            P, T = lathe(prof[None], m)
            jq = np.arange(len(T["quads"])) % m
            keep_q = (jq != m // 2 - 1) & (jq != m // 2)      # the arc facing the band wall is never seen
            T = dict(quads=T["quads"][keep_q], tris=np.zeros((0, 3), np.int64), qflat=T["qflat"][keep_q],
                     tflat=np.zeros(0, bool), nv=T["nv"])
            if v >= n_var - 3:                                   # eroded: part of a bead / neck lost, facing out
                ang = np.arctan2(P[:, :, 1], P[:, :, 0])
                zc_e = rv.choice([0.017, 0.05, 0.1]) * hs0 / 0.126
                d_ang = np.abs((ang - rv.uniform(-0.5, 0.5) + PI) % (2 * PI) - PI)
                fz = np.clip(1 - ((P[:, :, 2] - zc_e) / 0.03) ** 2, 0, 1)
                fa = np.clip(1 - d_ang / rv.uniform(0.8, 1.6), 0, 1)
                k = 1 - rv.uniform(0.35, 0.55) * fz * fa
                P[:, :, 0] *= k
                P[:, :, 1] *= k
            P[:, :, 2] += TP
            pp.add(P, T, Pl=P, mat="M_stone_dressed", smooth="all", wear=0.8 if v >= n_var - 3 else 0.35)
            ta = TA - dh
        else:
            Ps, Ts = stone_local(rv, [rv.uniform(0.085, 0.1)], [hs0 - 0.002], [rv.uniform(0.09, 0.1)], "dressed",
                                 rot_deg=(0.5, 0.5, 2.0))
            Q = np.stack([Ps[:, :, 1] + 0.05, -Ps[:, :, 0], Ps[:, :, 2] + TP + hs0 / 2], -1)
            pp.add(Q, Ts, Pl=Ps, mat="M_stone_dressed", smooth="bevel", wear=0.5)
            ta = TA
        I3 = np.eye(3)[None]
        blocks_world(pp, "M_stone_dressed", np.array([[0, 0, TP / 2]]), I3,
                     [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), TP / 2]], c=0.005, T=T_BLK_PLX)
        blocks_world(pp, "M_stone_dressed", np.array([[0, 0, HB - ta / 2]]), I3,
                     [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), ta / 2 - 0.0005]], c=0.005, T=T_BLK_ABX)
    Rb = float(R_out(g, z0 + HB / 2))
    a0, a1 = spans[0]
    nbal = int((a1 - a0) / pitch)
    us = a0 + (np.arange(nbal) + 0.5) * (a1 - a0) / nbal + rb.uniform(-0.015, 0.015, nbal)
    thb = us / Rb
    var = rb.integers(0, n_var - 3, nbal)
    for i in range(1, nbal):                                     # no two neighbours share a variant
        while var[i] == var[i - 1]:
            var[i] = rb.integers(0, n_var - 3)
    dfront = np.abs((thb + PI) % (2 * PI) - PI)
    fr_i, ot_i = np.nonzero(dfront < 0.75)[0], np.nonzero(dfront >= 0.75)[0]
    ero = np.concatenate([rb.choice(fr_i, 3, replace=False), rb.choice(ot_i, 5, replace=False)])
    var[ero] = np.where(np.arange(len(ero)) % 2 == 0, n_var - 3, n_var - 2)
    plain = rb.choice([i for i in range(nbal) if i not in set(ero)], 3, replace=False)
    var[plain] = n_var - 1
    rz = (thb - PI / 2) + rb.uniform(-0.12, 0.12, nbal)
    lx = np.clip(rb.normal(0, 0.8, nbal), -1.5, 1.5) * D2R
    ly = np.clip(rb.normal(0, 0.8, nbal), -1.5, 1.5) * D2R
    for i in range(nbal):
        R = euler([lx[i]], [ly[i]], [rz[i]])[0]
        ctr = np.array([(Rb + 0.055) * math.sin(thb[i]), -(Rb + 0.055) * math.cos(thb[i]), z0])
        place_instance(g, g.prefix + "_baluster_%03d" % i, "baluster_%d" % var[i], R, ctr)
    log("balusters %d placements from %d shared variants (eroded %d, %d on the front arc; plain blocks %d)"
        % (nbal, n_var, len(ero), 3, len(plain)))


def dentil_corbels(g, rc, zc, n=40, n_var=6, proj=0.18):
    """Dentil corbels under the cornice (kit component): 6 variant meshes (tapered, chipped dressed blocks, cut
    1 cm inside the frieze face: nothing modelled deeper), placed as linked duplicates round the drum."""
    for v in range(n_var):
        pp = pool_part(g, "corbel_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = g.RNG("corbel_var_%d" % v)
        P, T = stone_local(rv, [rv.uniform(0.115, 0.13)], [rv.uniform(0.14, 0.15)], [0.24], "dressed",
                           rot_deg=(0.3, 0.3, 0.6))
        pr = P[:, :, 1] > -proj
        hz = 0.075
        f = 0.45 + 0.55 * np.clip((P[:, :, 2] / hz + 1) / 2, 0, 1)
        P[:, :, 1] = np.where(pr, -proj + (P[:, :, 1] + proj) * f, P[:, :, 1])
        Q = P.copy()
        Q[:, :, 1] = np.maximum(Q[:, :, 1] + proj, -0.01)
        pp.add(Q, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.45)
    thc = (np.arange(n) + 0.5) * 2 * PI / n + rc.uniform(-0.012, 0.012, n)
    var = np.array([(i * 5 + int(rc.integers(0, 2))) % n_var for i in range(n)])
    for i in range(n):
        Rr = float(R_out(g, zc))
        th = thc[i]
        yv = np.array([math.sin(th), -math.cos(th), 0.0])
        xv = np.array([-math.cos(th), -math.sin(th), 0.0])
        R = np.stack([xv, yv, [0, 0, 1.0]], 1) @ euler([rc.normal(0, 0.005)], [rc.normal(0, 0.005)],
                                                        [rc.normal(0, 0.01)])[0]
        place_instance(g, g.prefix + "_corbel_%03d" % i, "corbel_%d" % var[i], R, yv * Rr + np.array([0, 0, zc]))
    log("dentil corbels %d placements from %d shared variants" % (n, n_var))
