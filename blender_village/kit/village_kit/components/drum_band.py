"""components.drum_band -- the balustrade band and cornice parts of a stone drum (kit 1.2.0): a row of stubby
turned stone balusters (5 profile families, eroded / chipped / replaced / broken / lost ones, +-1 deg lean) and the
dentil corbels under the cornice, both as pooled variant meshes placed as linked duplicates (producer note 3,
village_kit.pools).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (relief_far, R_out, place_instance, pool_part)  # noqa: F401
from ..split_stones import (stone_local)  # noqa: F401
from ..tmplmesh import (D2R, PI, T_BLK_ABX, T_BLK_PLX, blocks_world, euler, lathe, log)  # noqa: F401


# turned-baluster profile families: (radius m, height fraction 0..1) -- several hands over 150 years of repairs
BALUSTER_PROFILES = {
    "vase": [(0.034, 0.0), (0.041, 0.04), (0.042, 0.119), (0.035, 0.167), (0.046, 0.349), (0.048, 0.492),
             (0.041, 0.627), (0.030, 0.706), (0.038, 0.754), (0.039, 0.825), (0.031, 0.873), (0.036, 0.937),
             (0.036, 1.0)],
    "double_bead": [(0.036, 0.0), (0.040, 0.05), (0.038, 0.12), (0.030, 0.2), (0.044, 0.3), (0.044, 0.38),
                    (0.029, 0.48), (0.031, 0.55), (0.044, 0.65), (0.044, 0.73), (0.030, 0.82), (0.035, 0.9),
                    (0.037, 1.0)],
    "squat_bulb": [(0.035, 0.0), (0.040, 0.05), (0.036, 0.1), (0.050, 0.25), (0.054, 0.4), (0.049, 0.55),
                   (0.034, 0.68), (0.026, 0.76), (0.033, 0.83), (0.034, 0.9), (0.030, 0.95), (0.034, 1.0)],
    "column": [(0.038, 0.0), (0.042, 0.06), (0.036, 0.12), (0.035, 0.3), (0.034, 0.45), (0.040, 0.5),
               (0.034, 0.55), (0.033, 0.75), (0.032, 0.88), (0.038, 0.94), (0.038, 1.0)],
    "inverted_vase": [(0.036, 0.0), (0.036, 0.063), (0.031, 0.127), (0.039, 0.175), (0.038, 0.246), (0.030, 0.294),
                      (0.041, 0.373), (0.048, 0.508), (0.046, 0.651), (0.035, 0.833), (0.042, 0.881),
                      (0.041, 0.96), (0.034, 1.0)],
}
# the pooled variants: (profile family, kind); kind = clean | eroded | chipped | plain | stump
BALUSTER_VARIANTS = [("vase", "clean"), ("double_bead", "clean"), ("squat_bulb", "clean"), ("column", "clean"),
                     ("inverted_vase", "clean"), ("vase", "clean"), ("double_bead", "clean"),
                     ("squat_bulb", "eroded"), ("vase", "eroded"), ("column", "chipped"), (None, "plain"),
                     ("vase", "stump")]


def baluster_row(g, rb, spans, z0, z1, n_var=None, pitch=0.22, lean_deg=1.0, n_missing=2, n_stumps=3,
                 n_chipped=4, n_eroded=8, n_plain=3):
    """Relief 'balustrade' of stubby turned stone balusters (kit component), aged for the ensemble review: a pool
    of 12 variant meshes -- 5 turned profile families (vase, double bead, squat bulb, column, inverted vase) from
    different hands, eroded beads, chipped (a 2-2.5 cm split facet off a bead), a plain square replacement block and
    broken stumps -- placed as linked duplicates (village_kit.pools) along the drum with pitch +-1.5 cm, yaw +-7 deg
    and a lean of +-lean_deg; a few balusters are lost altogether (n_missing gaps show the recessed ashlar behind).
    No two neighbours share a variant.  Variant frame: +x outward, z up from z0."""
    variants = BALUSTER_VARIANTS[:n_var] if n_var else BALUSTER_VARIANTS
    HB = z1 - z0
    TP, TA = 0.022, 0.022
    hs0 = HB - TP - TA
    m = 16
    for v, (fam, kind) in enumerate(variants):
        pp = pool_part(g, "baluster_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = g.RNG("baluster_var_%d" % v)
        ta = TA
        if kind != "plain":
            dh = rv.uniform(-0.008, 0.008)
            prof = np.array(BALUSTER_PROFILES[fam], float)
            prof[:, 1] *= hs0 + dh
            prof[:, 0] *= rv.uniform(0.9, 1.1)
            prof[:, 0] += rv.normal(0, 0.001, len(prof))
            if kind == "stump":                                  # broken off at 30-45 % of its height
                cut = rv.uniform(0.30, 0.45) * (hs0 + dh)
                keep = prof[:, 1] < cut
                prof = np.concatenate([prof[keep], [[float(np.interp(cut, prof[:, 1], prof[:, 0])), cut]]])
            P, T = lathe(prof[None], m)
            jq = np.arange(len(T["quads"])) % m
            keep_q = (jq != m // 2 - 1) & (jq != m // 2)      # the arc facing the band wall is never seen
            cap = kind == "stump"                                # only a stump shows its (broken) top
            T = dict(quads=T["quads"][keep_q], tris=T["tris"] if cap else np.zeros((0, 3), np.int64),
                     qflat=T["qflat"][keep_q], tflat=T["tflat"] if cap else np.zeros(0, bool), nv=T["nv"])
            if kind == "eroded":                                 # part of a bead / neck lost, facing out
                ang = np.arctan2(P[:, :, 1], P[:, :, 0])
                zc_e = rv.choice([0.13, 0.4, 0.8]) * hs0
                d_ang = np.abs((ang - rv.uniform(-0.5, 0.5) + PI) % (2 * PI) - PI)
                fz = np.clip(1 - ((P[:, :, 2] - zc_e) / 0.03) ** 2, 0, 1)
                fa = np.clip(1 - d_ang / rv.uniform(0.8, 1.6), 0, 1)
                k = 1 - rv.uniform(0.35, 0.55) * fz * fa
                P[:, :, 0] *= k
                P[:, :, 1] *= k
            if kind == "chipped":                                # a split facet 2-2.5 cm deep off one bead
                phi = rv.uniform(-0.6, 0.6)
                nrm = np.array([math.cos(phi), math.sin(phi), rv.choice([-0.7, 0.7])])
                nrm /= np.linalg.norm(nrm)
                pr = P[0] @ nrm
                o = pr.max() - rv.uniform(0.020, 0.025)
                P[0] -= np.clip(pr - o, 0, None)[:, None] * nrm[None]
            if kind == "stump":                                  # fractured top: two tilted break planes
                for _ in range(2):
                    nrm = np.array([rv.normal(0, 0.5), rv.normal(0, 0.5), 1.0])
                    nrm /= np.linalg.norm(nrm)
                    pr = P[0] @ nrm
                    o = pr.max() - rv.uniform(0.01, 0.025)
                    P[0] -= np.clip(pr - o, 0, None)[:, None] * nrm[None]
            P[:, :, 2] += TP
            wear = dict(clean=0.35, eroded=0.8, chipped=0.85, stump=0.95)[kind]
            pp.add(P, T, Pl=P, mat="M_stone_dressed", smooth="all", wear=wear)
            ta = TA - dh
        else:
            Ps, Ts = stone_local(rv, [rv.uniform(0.085, 0.1)], [hs0 - 0.002], [rv.uniform(0.09, 0.1)], "dressed",
                                 rot_deg=(0.5, 0.5, 2.0), min_relief=relief_far(g))
            Q = np.stack([Ps[:, :, 1] + 0.05, -Ps[:, :, 0], Ps[:, :, 2] + TP + hs0 / 2], -1)
            pp.add(Q, Ts, Pl=Ps, mat="M_stone_dressed", smooth="bevel", wear=0.5)
        I3 = np.eye(3)[None]
        blocks_world(pp, "M_stone_dressed", np.array([[0, 0, TP / 2]]), I3,
                     [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), TP / 2]], c=0.005, T=T_BLK_PLX)
        if kind != "stump":
            blocks_world(pp, "M_stone_dressed", np.array([[0, 0, HB - ta / 2]]), I3,
                         [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), ta / 2 - 0.0005]], c=0.005, T=T_BLK_ABX)
    Rb = float(R_out(g, z0 + HB / 2))
    a0, a1 = spans[0]
    nbal = int((a1 - a0) / pitch)
    us = a0 + (np.arange(nbal) + 0.5) * (a1 - a0) / nbal + rb.uniform(-0.015, 0.015, nbal)
    thb = us / Rb
    by_kind = {}
    for v, (_, kind) in enumerate(variants):
        by_kind.setdefault(kind, []).append(v)
    sound = by_kind["clean"]
    var = np.array([sound[int(i)] for i in rb.integers(0, len(sound), nbal)])
    for i in range(1, nbal):                                     # no two neighbours share a variant
        while var[i] == var[i - 1]:
            var[i] = sound[int(rb.integers(0, len(sound)))]
    dfront = np.abs((thb + PI) % (2 * PI) - PI)
    fr_i, ot_i = np.nonzero(dfront < 0.75)[0], np.nonzero(dfront >= 0.75)[0]
    taken = set()

    def pick(pool_i, n):
        cand = [i for i in pool_i if i not in taken and (i - 1) not in taken and (i + 1) not in taken]
        sel = rb.choice(cand, min(n, len(cand)), replace=False) if cand and n > 0 else []
        taken.update(int(i) for i in sel)
        return np.array(sel, int)
    # aged ones are spread round the drum; the front arc (actor and hero views) gets its share of each
    ero = np.concatenate([pick(fr_i, n_eroded * 3 // 8), pick(ot_i, n_eroded - n_eroded * 3 // 8)])
    chip = np.concatenate([pick(fr_i, n_chipped // 2), pick(ot_i, n_chipped - n_chipped // 2)])
    stump = np.concatenate([pick(fr_i, 1 if n_stumps else 0), pick(ot_i, max(n_stumps - 1, 0))])
    missing = pick(ot_i, n_missing)
    plain = pick(np.arange(nbal), n_plain)
    for idxs, kind in ((ero, "eroded"), (chip, "chipped"), (stump, "stump"), (plain, "plain")):
        opts = by_kind.get(kind, [])
        for j, i in enumerate(idxs):
            var[i] = opts[j % len(opts)]
    rz = (thb - PI / 2) + rb.uniform(-0.12, 0.12, nbal)
    lx = rb.uniform(-lean_deg, lean_deg, nbal) * D2R            # ensemble review: a +-1 deg lean, every one
    ly = rb.uniform(-lean_deg, lean_deg, nbal) * D2R
    sett = rb.uniform(-0.003, 0.002, nbal)                       # settled unevenly on the string course
    lost = set(int(i) for i in missing)
    for i in range(nbal):
        if i in lost:
            continue
        R = euler([lx[i]], [ly[i]], [rz[i]])[0]
        ctr = np.array([(Rb + 0.055) * math.sin(thb[i]), -(Rb + 0.055) * math.cos(thb[i]), z0 + min(sett[i], 0.0)])
        place_instance(g, g.prefix + "_baluster_%03d" % i, "baluster_%d" % var[i], R, ctr)
    g.balusters = dict(n=nbal, missing=sorted(lost), stumps=sorted(int(i) for i in stump),
                       chipped=sorted(int(i) for i in chip), eroded=sorted(int(i) for i in ero),
                       plain=sorted(int(i) for i in plain), th=thb, R=Rb + 0.055, z0=z0, z1=z1)
    log("balusters %d positions from %d shared variants (5 profile families): eroded %d, chipped %d, stumps %d, "
        "plain %d, missing %d; lean +-%.1f deg" % (nbal, len(variants), len(ero), len(chip), len(stump), len(plain),
                                                    len(lost), lean_deg))


def dentil_corbels(g, rc, zc, n=40, n_var=6, proj=0.18):
    """Dentil corbels under the cornice (kit component): 6 variant meshes (tapered, chipped dressed blocks, cut
    1 cm inside the frieze face: nothing modelled deeper), placed as linked duplicates round the drum."""
    for v in range(n_var):
        pp = pool_part(g, "corbel_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = g.RNG("corbel_var_%d" % v)
        P, T = stone_local(rv, [rv.uniform(0.115, 0.13)], [rv.uniform(0.14, 0.15)], [0.24], "dressed",
                           rot_deg=(0.3, 0.3, 0.6), min_relief=relief_far(g))
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
