"""components.daub_wall -- the village's wattle-and-daub on a PATH wall (kit 1.21.0, producer note 20; OPTIONAL mode).

daub.round_daub_wall builds the daub of a ROUND building (it needs a RoundFrame: azimuth bays, hut fields).  This module
is the straight / curved-path counterpart for any plan frame (PlanFrame): a daub infill between hewn timber posts, on a
sill or on a rubble plinth, under a roof line.  Nothing in daub.py / wattle.py is changed; the weave is wattle.weave_panel
(the hut's rods and stakes), the coat is M_daub with the hut's section (mean face 5 cm outside the wattle line, <= 1.5 cm
low-frequency bulge, a slit-dip beside every post so the posts stand proud, a coat foot bedded into the stones, a
tucked head under the roof) and the exposed-wattle patches are the fallen-out coat of the hut (ragged stepped margin,
woven rods + stakes inside, the interior daub skin behind).

path_daub_wall(g, name, path, z0, top_fn, ...)
    path      plan polyline [(x, y), ...], outward normal on the RIGHT (the path_stone_wall / path_timber_wall convention)
    z0        foot of the daub (a rubble plinth top - 0.06 -- bedded -- or the underside of a sill)
    top_fn    top_fn(x, y) -> z of the roof line over the wall (the coat and posts stop `tuck` under it)
    sill      True: a hewn sill beam at the foot (infill standing on a stone cap); False: the coat is bedded on the stones
    patches   [dict(s=, z=, hs=, hz=, seed=)]: fallen-out coat (path distance s, height z, half width / height)
    end_posts (bool, bool): a post at the path start / end (False where the wall runs into a masonry host)
Objects <PREFIX>_<name>_daub, _backing, _posts (M_timber), _wattle (rods + stakes), _sill.
Returns dict(pm=PathMap, posts=[s, ...], bays=[(sa, sb), ...], holes=n).
"""
import math

import numpy as np

from ..core import log, n2, smoothstep
from ..geom import beam
from .rubble_walls import PathMap
from .wattle import weave_panel


class _RodCtx:
    """what weave_panel reads from the frame (a round hut's g): no eave shadow, no rod store."""
    ROD_SHADOW_Z = 1.0e9
    ROD_STORE = {}


def _slab(acc, P_front, P_back, keep, mat, wear):
    """closed slab on an (ns, nz) vertex grid: front, back, and side faces on every open cell edge (cells keep[i, j])."""
    ns, nz = P_front.shape[:2]
    V = np.concatenate([P_front.reshape(-1, 3), P_back.reshape(-1, 3)])
    off = ns * nz

    def I(i, j):  # noqa: E741, E743
        return i * nz + j
    Fq = []
    for i in range(ns - 1):
        for j in range(nz - 1):
            if not keep[i, j]:
                continue
            Fq.append((I(i, j), I(i + 1, j), I(i + 1, j + 1), I(i, j + 1)))
            Fq.append((off + I(i, j), off + I(i, j + 1), off + I(i + 1, j + 1), off + I(i + 1, j)))
            if j == 0 or not keep[i, j - 1]:
                Fq.append((I(i, j), off + I(i, j), off + I(i + 1, j), I(i + 1, j)))
            if j == nz - 2 or not keep[i, j + 1]:
                Fq.append((I(i, j + 1), I(i + 1, j + 1), off + I(i + 1, j + 1), off + I(i, j + 1)))
            if i == 0 or not keep[i - 1, j]:
                Fq.append((I(i, j), I(i, j + 1), off + I(i, j + 1), off + I(i, j)))
            if i == ns - 2 or not keep[i + 1, j]:
                Fq.append((I(i + 1, j), off + I(i + 1, j), off + I(i + 1, j + 1), I(i + 1, j + 1)))
    if not Fq:
        return 0
    Fq = np.array(Fq)
    used, inv = np.unique(Fq.ravel(), return_inverse=True)
    acc.add(V[used], inv.reshape(-1, 4), mat, wear=wear)
    return len(Fq)


def _build(acc, coll):
    if acc.n:
        acc.build(coll)


def path_daub_wall(g, name, path, z0, top_fn, sill=False, sill_h=0.16, post=0.17, bay_max=1.25, end_posts=(True, True),
                   coat=0.052, wat=-0.030, back=(-0.080, -0.042), cell=0.05, patches=(), seed=1, tuck=0.015,
                   post_w=(-0.09, 0.095), foot_dip=0.14, mat_post="M_timber", mat_coat="M_daub", min_h=0.06):
    pm = PathMap(path)
    L = pm.total
    pre = f"{g.prefix}_{name}"
    rng = np.random.default_rng(seed)
    wc = 0.5 * (post_w[0] + post_w[1])
    wd = post_w[1] - post_w[0]

    # ---- post stations -------------------------------------------------------------------------------------------
    lo = post / 2 if end_posts[0] else 0.0
    hi = L - post / 2 if end_posts[1] else L
    nb = max(1, int(math.ceil((hi - lo) / bay_max)))
    st = np.linspace(lo, hi, nb + 1)
    pst = []
    for k, s in enumerate(st):
        if k == 0 and not end_posts[0]:
            continue
        if k == nb and not end_posts[1]:
            continue
        pst.append(float(s) + (float(rng.uniform(-0.05, 0.05)) if 0 < k < nb else 0.0))

    def at(s, w=0.0):
        i = int(pm.seg(s))
        return pm.A[i] + (s - pm.S[i]) * pm.dir[i] + w * pm.nrm[i]

    def ztop(s):
        x, y = at(s)
        return float(top_fn(x, y))

    # ---- posts (hewn, ~5 cm proud of the coat) and sill ---------------------------------------------------------
    posts = g.acc(f"{name}_posts", 40)
    for s in pst:
        i = int(pm.seg(s))
        x, y = at(s, wc)
        zt, zb = ztop(s) - 0.03, z0 - 0.03
        if zt - zb < 0.2:
            continue
        beam(posts, (x, y, zb), (x, y, zt), post, wd, 0.02, mat_post, up=(pm.nrm[i][0], pm.nrm[i][1], 0.0), nx=6)
    z_foot = z0
    if sill:
        sl = g.acc(f"{name}_sill", 40)
        for i in range(len(pm.L)):
            a, b, d = pm.A[i], pm.A[i + 1], pm.dir[i]
            e0 = 0.5 * wd if i > 0 else 0.0
            e1 = 0.5 * wd if i < len(pm.L) - 1 else 0.0
            p0 = np.array([*(a - d * e0 + pm.nrm[i] * wc), z0 + sill_h / 2])
            p1 = np.array([*(b + d * e1 + pm.nrm[i] * wc), z0 + sill_h / 2])
            beam(sl, p0, p1, wd, sill_h, 0.02, mat_post, up=(0, 0, 1), nx=6)
        _build(sl, g.coll)
        z_foot = z0 + sill_h - 0.02

    # ---- bays between the posts ------------------------------------------------------------------------------------
    cuts = [0.0] + [v for s in pst for v in (s - post / 2, s + post / 2)] + [L]
    edges = []
    for k in range(0, len(cuts), 2):
        a, b = cuts[k], cuts[k + 1]
        if b - a > 0.08:
            edges.append((max(0.0, a - 0.035), min(L, b + 0.035)))

    def post_d(s):
        d = np.full(np.shape(s), 9.0)
        for p in pst:
            d = np.minimum(d, np.abs(np.asarray(s, float) - p) - post / 2)
        return np.maximum(d, 0.0)

    holes = [dict(pt, seed=pt.get("seed", seed + 11 * k)) for k, pt in enumerate(patches)]

    def hole_f(s, z, grow=0.0):
        """> 0 inside a fallen-out patch (ragged margin, stepped by the grid)."""
        s, z = np.broadcast_arrays(np.asarray(s, float), np.asarray(z, float))
        f = np.full(s.shape, -9.0)
        for h in holes:
            r2 = ((s - h["s"]) / (h["hs"] + grow)) ** 2 + ((z - h["z"]) / (h["hz"] + grow)) ** 2
            f = np.maximum(f, 1.0 - r2 + 0.30 * n2(s * 7.0, z * 7.0, h["seed"]))
        return f

    daub, bk = g.acc(f"{name}_daub", 60), g.acc(f"{name}_backing", 60)
    n_cells = 0
    for (sa, sb) in edges:
        ns = max(2, int(math.ceil((sb - sa) / cell)) + 1)
        ss = np.linspace(sa, sb, ns)
        zh = np.array([ztop(s) - tuck for s in ss])
        zl = z_foot - (0.0 if sill else 0.06)
        hmax = float((zh - zl).max())
        if hmax < min_h:
            continue
        nz = max(3, int(math.ceil(hmax / cell)) + 1)
        Z = zl + (zh - zl)[:, None] * np.linspace(0.0, 1.0, nz)[None, :]
        S = np.repeat(ss[:, None], nz, 1)
        # the coat face: mean `coat`, low-frequency bulge, slit dip beside the posts, foot bedded into the stones
        w = coat + 0.013 * n2(S * 1.6, Z * 1.6, seed + 3) - 0.020 * (1.0 - smoothstep(0.0, 0.11, post_d(S)))
        w = -0.02 + (w + 0.02) * smoothstep(zl + 0.02, zl + foot_dip, Z)
        Pf = pm(S, Z, w)
        Pb = pm(S, Z, np.full(S.shape, back[1]))
        Sc = 0.25 * (S[:-1, :-1] + S[1:, :-1] + S[:-1, 1:] + S[1:, 1:])
        Zc = 0.25 * (Z[:-1, :-1] + Z[1:, :-1] + Z[:-1, 1:] + Z[1:, 1:])
        keep = (hole_f(Sc, Zc) <= 0.0) & ((Z[1:, 1:] - Z[1:, :-1]) > 0.002)
        n_cells += _slab(daub, Pf, Pb, keep, mat_coat, 0.35)
        # interior skin behind everything (the weave's back, seen through the fallen-out patches): a coarse grid
        nsb, nzb = max(2, int(math.ceil((sb - sa) / 0.2)) + 1), max(3, int(math.ceil(hmax / 0.25)) + 1)
        sb_ = np.linspace(sa, sb, nsb)
        zb_ = np.array([ztop(s) - tuck for s in sb_])
        Zb = zl + (zb_ - zl)[:, None] * np.linspace(0.0, 1.0, nzb)[None, :]
        Sb = np.repeat(sb_[:, None], nzb, 1)
        _slab(bk, pm(Sb, Zb, np.full(Sb.shape, back[1])), pm(Sb, Zb, np.full(Sb.shape, back[0])),
              np.ones((nsb - 1, nzb - 1), bool), mat_coat, 0.85)
    for a in (daub, bk, posts):
        _build(a, g.coll)

    # ---- the exposed wattle inside each patch (the hut's weave_panel; its margin runs under the coat) --------------
    nrods = 0
    if holes:
        rods = g.acc(f"{name}_wattle", 60)

        def pathf(s):
            s = np.asarray(s, float)
            i = pm.seg(s)
            return pm.A[i] + (s - pm.S[i])[..., None] * pm.dir[i] + wat * pm.nrm[i], pm.nrm[i]
        for k, h in enumerate(holes):
            s0, s1 = max(0.0, h["s"] - h["hs"] - 0.14), min(L, h["s"] + h["hs"] + 0.14)
            z_a = max(z_foot + 0.02, h["z"] - h["hz"] - 0.14)
            z_b = min(h["z"] + h["hz"] + 0.14, ztop(0.5 * (s0 + s1)) - 0.06)
            if z_b - z_a < 0.2:
                continue
            nrods += weave_panel(_RodCtx, rods, rods, pathf, s0, s1, z_a, z_b, 900 + seed * 7 + k,
                                 hide=(lambda s_, z_: hole_f(s_, z_, grow=0.12) <= 0.0), trim=(0.0, 0.0),
                                 stake_sp=0.34, knots=0.0)
        _build(rods, g.coll)
    log(f"  {pre}: daub wall, {len(pst)} posts, {len(edges)} bays, {n_cells} coat quads, {len(holes)} fallen-out "
        f"patches, {nrods} rods" + (", on a sill" if sill else ", bedded on the plinth"))
    return dict(pm=pm, posts=pst, bays=edges, holes=len(holes))


__all__ = ["path_daub_wall"]

