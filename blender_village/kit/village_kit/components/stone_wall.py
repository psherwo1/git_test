"""components.stone_wall -- coursed rubble walls on any parametric wall surface (kit 1.1.0, from the hilltop keep).

A wall is laid out in SURFACE coordinates (s along the wall / course, z up, w out of the face) and mapped onto the
building by a map function mapfn(s, z, w, zc) -> world points (zc = the stone's course coordinate, so a battered or
flared wall keeps each course on its own perimeter).  The stones themselves come from the kit's ONE stone generator
(village_kit.stones.make_stone): style 'coursed' for whole batches of rubble / dressed blocks, 'coursed_poly' for hero
stones with true polygonal outlines.

    layout_wall(rng, srange_fn, z_bot, z_top, excl_fn, cfg, ztop_fn)   coursed rubble layout -> stone record S
          courses 8-25 cm from a height mixture, wandering beds (+-3 cm), pinch-outs (beds ramp so a course thins to a
          slip), coherent slanted joints shared by neighbours, split / double-height stones, through stones, a
          stepped footing course (cfg footing / foot_lvl / foot_proj) and exclusions (openings, dressed work, posts)
    fill_voids(S, ...)          plug every mortar void wider than ~3 cm with pinning stones (rasterised coverage)
    polygonize(S, sel, rng)     hero stones -> knocked-off corners, wedges, kinked beds (5-7 sided outlines)
    rough_footing(S, rng)       footing stones -> split field stone (sloping tops, split planes, chipped arrises)
    dress_irregular(S, rng)     dressed blocks set 1-2 deg out of square
    lay_stones / lay_poly_stones   build the stones of a record onto a surface (note 11 relief threshold per stone)
    mortar_sheet(...)           the recessed mortar body behind the stones (coarse cells, refined near openings)
    round_stone_wall(...)       a round (optionally clipped, battered or flared) coursed rubble tower body + mortar
    stone_rec(...), filt(S, mask), cat_stones(*S)   record helpers

cfg keys (layout_wall): seed, footing (top of the footing course), ch (course height range), ch_mix (mixture),
p_tall, len / foot_len (stone lengths), foot_lvl, joint, front / foot_proj (face projection), bevel (arris), pillow,
rot, p_double, p_long, p_split, back, bed_amp, slant, pinch=(rate per m, amplitude, width).
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, CLIP_Z, box_sum, finalize, inside_poly, inst_faces, lathe_rz, n1, vnoise90
from ..stones import make_stone, stone_outline


def lay_stones(acc, S, mapfn, mat, rng, relief=None, premap=None, **kw):
    """build the stones of record S (style 'coursed', one batch) mapped by mapfn onto acc.  relief(P) -> producer
    note 11 threshold at world points (e.g. OctFrame.min_relief; None = phase-1 detail); premap(x, y, S) -> (s, z)
    replaces the default s = sc + x, z = zc + y (voussoirs on an arch).  Other keywords: see stones.coursed_batch."""
    M = len(S["sc"])
    if M == 0:
        return
    zcr0 = np.asarray(S["zcrs"], float)
    if relief is not None:
        if premap is not None:
            s0, z0 = premap(np.zeros((M, 1)), np.zeros((M, 1)), S)
            s0, z0 = s0[:, 0], z0[:, 0]
        else:
            s0, z0 = np.asarray(S["sc"], float), np.asarray(S["zc"], float)
        mr = relief(mapfn(s0, z0, np.zeros(M), zcr0))
    else:
        mr = 0.0
    P, quads = make_stone("coursed", rng, S=S, min_relief=mr, **kw)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    if premap is not None:
        s_, z_ = premap(x, y, S)
    else:
        s_ = np.asarray(S["sc"], float)[:, None] + x
        z_ = np.asarray(S["zc"], float)[:, None] + y
    zcr = np.broadcast_to(zcr0[:, None], x.shape)
    W = mapfn(s_.ravel(), z_.ravel(), z.ravel(), zcr.ravel())
    acc.add(W, inst_faces(quads, M, P.shape[1]), mat)


def lay_poly_stones(acc, S, mapfn, mat, rng, relief=None, **kw):
    """hero rubble (style 'coursed_poly'), one stone per call to the generator, mapped by mapfn onto acc."""
    M = len(S["sc"])
    if M == 0:
        return
    if relief is not None:
        mr = relief(mapfn(np.asarray(S["sc"], float), np.asarray(S["zc"], float), np.zeros(M),
                          np.asarray(S["zcrs"], float)))
    else:
        mr = np.zeros(M)
    for i in range(M):
        V, F = make_stone("coursed_poly", rng, S=S, i=i, min_relief=float(mr[i]), **kw)
        s_ = S["sc"][i] + V[:, 0]
        z_ = S["zc"][i] + V[:, 1]
        W = mapfn(s_, z_, V[:, 2], np.full(len(s_), S["zcrs"][i]))
        acc.add(W, F, mat)


def layout_wall(rng, srange_fn, z_bot, z_top, excl_fn, cfg, ztop_fn=None):
    """Coursed rubble layout. Returns dict of stone arrays (in surface coords s, z)."""
    st = {k: [] for k in ("sc", "zc", "hx", "hy", "f", "back", "r", "rot", "zcrs", "pillow", "tiltx", "tilty", "foot")}
    seed = cfg.get("seed", 1)
    foot_lvl = cfg.get("foot_lvl")          # footing tops step +-8 cm stone by stone (not a kerb line)
    foot_steps = []
    # course boundaries
    bounds = [z_bot]
    z = z_bot
    if cfg.get("footing"):
        z = cfg["footing"]
        bounds.append(z)
    mix = cfg.get("ch_mix")
    while z < z_top - 1e-6:
        if mix is not None:
            # course-height mixture over the full 8-25 cm range (thin pinning courses .. through courses)
            u_ = rng.uniform()
            acc_p = 0.0
            h = rng.uniform(*mix[-1][1:])
            for pr_, lo_, hi_ in mix:
                acc_p += pr_
                if u_ < acc_p:
                    h = rng.uniform(lo_, hi_)
                    break
        else:
            h = rng.uniform(*cfg["ch"])
            if rng.uniform() < cfg.get("p_tall", 0.08):
                h = rng.uniform(0.2, 0.26)
        if foot_lvl is not None and len(bounds) == 2:
            h = max(h, 0.18)                 # the course over a stepped footing must swallow the steps
        if z + h > z_top - cfg["ch"][0] * 0.7:
            h = z_top - z
        z += h
        bounds.append(z)
    nb = len(bounds)
    amp = cfg.get("bed_amp", 0.022)
    # pinch-outs: local ramps in a bed line so the course above/below thins to a slip (5-6 cm) over 0.7-1.8 m
    # and swells again; the stones in the ramp become wedges / trapezoids with angled beds (shared, coherent)
    bumps = {k: [] for k in range(nb)}
    pin = cfg.get("pinch")
    if pin is not None:
        L_ = max(b for a, b in srange_fn(0.5 * (z_bot + z_top)))
        for k in range(1, nb - 1):
            n_b = rng.poisson(L_ * pin[0])
            for _ in range(n_b):
                sc_ = rng.uniform(0, L_)
                w_ = rng.uniform(*pin[2])
                A_ = rng.uniform(*pin[1]) * (1 if rng.uniform() < 0.5 else -1)
                room = (bounds[k + 1] - bounds[k]) - 0.055 if A_ > 0 else (bounds[k] - bounds[k - 1]) - 0.055
                if room < 0.025:
                    continue
                A_ = math.copysign(min(abs(A_), room), A_)
                clash = any(abs(sc_ - b_[0]) < 0.5 * (w_ + b_[1]) + 0.1 for kk in (k - 1, k + 1) for b_ in bumps.get(kk, []))
                if clash:
                    continue
                bumps[k].append((sc_, w_, A_))

    def bed(k, s):
        s = np.asarray(s, float)
        if k == 0 or k == nb - 1:
            return np.full_like(s, bounds[k])
        v = bounds[k] + amp * n1(s, seed * 100 + k, 1.0 / 3.5)
        for sc_, w_, A_ in bumps[k]:
            v = v + A_ * 0.5 * (1 + np.cos(np.pi * np.clip((s - sc_) / (0.5 * w_), -1, 1)))
        return v

    blocked = {}
    for k_ in ("shl", "shr", "sbb", "sbt"):
        st[k_] = []
    sl_sd = cfg.get("slant", 0.22)

    def bed_slope(k, s):
        return float((bed(k, s + 0.04) - bed(k, s - 0.04)) / 0.08)

    def foot_top(ss):
        v = np.full(len(ss), bounds[1])
        for a_, b_, zt_ in foot_steps:
            v = np.where((ss >= a_ - 0.02) & (ss <= b_ + 0.02), np.maximum(v, zt_), v)
        return v

    def push(sc, zc, hx, hy, fr, r, zm, shl, shr, kb, kt, tilt_back=None, foot=0.0):
        st["sc"].append(sc)
        st["zc"].append(zc)
        st["hx"].append(hx)
        st["hy"].append(hy)
        st["f"].append(fr)
        st["back"].append(cfg.get("back", 0.09))
        st["r"].append(r)
        st["rot"].append(rng.normal(0, cfg.get("rot", 0.004)))
        st["zcrs"].append(zm)
        st["pillow"].append(rng.uniform(*cfg["pillow"]))
        # tilt: +-1 deg sideways, ~1/3 of the stones lean back up to 3 deg (top edge recessed)
        st["tiltx"].append(rng.normal(0, 0.012) * hx)
        tb = -math.tan(math.radians(rng.uniform(0.5, 3.0))) * hy if rng.uniform() < 0.35 else rng.normal(0, 0.01) * hy
        st["tilty"].append(tb if tilt_back is None else tilt_back)
        st["shl"].append(shl)
        st["shr"].append(shr)
        st["sbb"].append(bed_slope(kb, sc) if 0 < kb < nb - 1 and not (kb == 1 and foot_lvl) else 0.0)
        st["sbt"].append(bed_slope(kt, sc) if 0 < kt < nb - 1 and not (kt == 1 and foot_lvl) else 0.0)
        st["foot"].append(foot)

    def arris():
        u = rng.uniform()
        lo, hi = cfg["bevel"]
        return lo + (hi - lo) * u ** 2.2

    for k in range(nb - 1):
        z0, z1 = bounds[k], bounds[k + 1]
        zm = 0.5 * (z0 + z1)
        footing = cfg.get("footing") and k == 0
        free = []
        for a, b in srange_fn(zm):
            free.append([a, b])
        ex = excl_fn(z0 - 0.03, z1 + 0.03, zm) + blocked.get(k, [])
        for ea, eb in ex:
            nf = []
            for a, b in free:
                if eb <= a or ea >= b:
                    nf.append([a, b])
                else:
                    if ea > a:
                        nf.append([a, ea])
                    if eb < b:
                        nf.append([eb, b])
            free = nf
        lr = cfg["foot_len"] if footing else cfg["len"]
        for a, b in free:
            j0 = rng.uniform(*cfg["joint"])
            pos = a + j0 * 0.5
            prev_slant = 0.0
            run_start = len(st["sc"])
            while b - pos > 0.07:
                L = rng.uniform(*lr)
                if rng.uniform() < cfg.get("p_long", 0.06) and not footing:
                    L = rng.uniform(0.75, 0.92)
                j = rng.uniform(*cfg["joint"])
                rem = b - pos - j * 0.5
                if rem - L - j < lr[0] * 0.75:
                    L = rem if rem < lr[1] * 1.35 else rem * 0.5
                if L < 0.05:
                    break
                if L < 0.16 and not footing:
                    L = max(L, 0.07)
                s0, s1 = pos, pos + L
                sc = 0.5 * (s0 + s1)
                dbl = (not footing) and k + 2 < nb and (z1 - z0) < 0.17 and (bounds[k + 2] - z1) < 0.17 \
                    and L < 0.62 and rng.uniform() < cfg.get("p_double", 0.07)
                zb = float(bed(k, sc))
                zt = float(bed(k + 2 if dbl else k + 1, sc))
                if footing and foot_lvl is not None:
                    zt = bounds[1] + rng.uniform(*foot_lvl)
                    foot_steps.append((s0, s1, zt))
                if k == 1 and foot_steps:
                    zb = max(zb, float(foot_top(np.linspace(s0, s1, 9)).max()))
                if ztop_fn is not None:
                    lim = ztop_fn(sc)
                    if zb > lim - 0.05:
                        pos = s1 + j
                        prev_slant = 0.0
                        continue
                    zt = min(zt, lim)
                jb = rng.uniform(*cfg["joint"]) * 0.5
                jt = rng.uniform(*cfg["joint"]) * 0.5
                hy = 0.5 * (zt - zb) - 0.5 * (jb + jt)
                if hy < 0.03:
                    pos = s1 + j
                    prev_slant = 0.0
                    continue
                if dbl:
                    blocked.setdefault(k + 1, []).append((s0 - j * 0.5, s1 + j * 0.5))
                # slant of this stone's right-hand joint (shared with the next stone's left end)
                at_end = b - (s1 + j) < 0.08
                slant = 0.0 if at_end else float(np.clip(rng.normal(0, sl_sd), -0.4, 0.4))
                if footing:
                    slant *= 0.4
                split = (not footing) and (not dbl) and (zt - zb) > 0.12 and rng.uniform() < cfg.get("p_split", 0.10)
                if split:
                    # thin stone + one or two thin stones stacked on it, filling the full course
                    zm2 = zb + (zt - zb) * rng.uniform(0.4, 0.6)
                    jj = rng.uniform(*cfg["joint"]) * 0.5
                    push(sc, 0.5 * (zb + jb + zm2 - jj), 0.5 * L - 0.002, 0.5 * (zm2 - jj - zb - jb),
                         rng.uniform(*cfg["front"]), arris() * 0.7, zm, prev_slant, slant, k, k)
                    if rng.uniform() < 0.5 or L < 0.25:
                        push(sc, 0.5 * (zm2 + jj + zt - jt), 0.5 * L - 0.002, 0.5 * (zt - jt - zm2 - jj),
                             rng.uniform(*cfg["front"]), arris() * 0.7, zm, prev_slant, slant, k + 1, k + 1)
                    else:
                        cut = s0 + L * rng.uniform(0.35, 0.65)
                        jx = rng.uniform(*cfg["joint"])
                        ms = float(np.clip(rng.normal(0, sl_sd), -0.4, 0.4))
                        for (pa, pb, sl0, sl1) in ((s0, cut - jx / 2, prev_slant, ms), (cut + jx / 2, s1, ms, slant)):
                            push(0.5 * (pa + pb), 0.5 * (zm2 + jj + zt - jt), 0.5 * (pb - pa) - 0.002,
                                 0.5 * (zt - jt - zm2 - jj), rng.uniform(*cfg["front"]), arris() * 0.7, zm,
                                 sl0, sl1, k + 1, k + 1)
                    pos = s1 + j
                    prev_slant = slant
                    continue
                fr = rng.uniform(*cfg["front"]) + (rng.uniform(*cfg["foot_proj"]) if footing else 0.0)
                uu = rng.uniform()
                if uu < 0.07:
                    fr += rng.uniform(0.008, 0.016)      # bulging / proud stone
                elif uu < 0.14:
                    fr = max(0.005, fr - 0.010)          # weathered-back stone
                push(sc, 0.5 * (zb + jb + zt - jt) if not footing else 0.5 * (zb + zt - jt), 0.5 * L - 0.002,
                     hy if not footing else 0.5 * (zt - zb - jt), fr, arris(), zm, prev_slant, slant,
                     k, k + 2 if dbl else k + 1, foot=1.0 if footing else 0.0)
                pos = s1 + j
                prev_slant = slant
            # close the run: stretch the last stone(s) so no gap is left at the run end
            gap = b - pos
            if len(st["sc"]) > run_start and gap > 0.004:
                n_last = 1
                zc_last = st["zc"][-1]
                if len(st["sc"]) - run_start >= 2 and abs(st["sc"][-2] - st["sc"][-1]) < 1e-6:
                    n_last = 2
                for q in range(1, n_last + 1):
                    st["hx"][-q] += 0.5 * (gap - 0.006)
                    st["sc"][-q] += 0.5 * (gap - 0.006)
                    st["shr"][-q] = 0.0
                if n_last == 1 and len(st["sc"]) - run_start >= 2 and abs(st["zc"][-2] - zc_last) > 0.02 and \
                        abs((st["sc"][-2] + st["hx"][-2]) - (st["sc"][-1] + st["hx"][-1])) < 0.2:
                    st["hx"][-2] += 0.5 * (gap - 0.006)
                    st["sc"][-2] += 0.5 * (gap - 0.006)
                    st["shr"][-2] = 0.0
    return {k: np.array(v, float) for k, v in st.items()}


def stone_footprint_mask(S, s0, z0, res, shape):
    """rasterise stone faces (s,z param space) into a bool grid (approx. inverse of the joint shears)."""
    mask = np.zeros(shape, bool)
    ns, nz = shape
    for i in range(len(S["sc"])):
        sc, zc, hx, hy = S["sc"][i], S["zc"][i], S["hx"][i], S["hy"][i]
        ext = hx + hy * 0.4 + 0.01
        a0 = max(int((sc - ext - s0) / res), 0)
        a1 = min(int((sc + ext - s0) / res) + 2, ns)
        b0 = max(int((zc - hy - 0.02 - z0) / res), 0)
        b1 = min(int((zc + hy + 0.02 - z0) / res) + 2, nz)
        if a1 <= a0 or b1 <= b0:
            continue
        ss = s0 + (np.arange(a0, a1) + 0.5) * res
        zz = z0 + (np.arange(b0, b1) + 0.5) * res
        dx = ss[:, None] - sc
        dy = zz[None, :] - zc
        c, s_ = math.cos(-S["rot"][i]), math.sin(-S["rot"][i])
        dx, dy = dx * c - dy * s_, dx * s_ + dy * c
        if any(_g(S, k_, i) > 0.004 for k_ in ("cq0", "cq1", "cq2", "cq3", "kk")):
            mask[a0:a1, b0:b1] |= inside_poly(dx, dy, stone_outline(S, i))
            continue
        shx = np.where(dx > 0, S["shr"][i], S["shl"][i]) if "shl" in S else 0.0
        shy = np.where(dy > 0, S["sbt"][i], S["sbb"][i]) if "sbb" in S else 0.0
        xx = dx - dy * shx
        yy = dy - dx * shy
        mask[a0:a1, b0:b1] |= (np.abs(xx) <= hx) & (np.abs(yy) <= hy)
    return mask


def fill_voids(S, srange_fn, excl_fn, z_bot, z_top, rng, cfg, ztop_fn=None, res=0.01, label=""):
    """find mortar voids wider than ~3 cm between laid stones and plug them with pinning stones.
    Returns (pin stone dict, visible-mortar fraction before, after)."""
    L = max(b for zm in np.linspace(z_bot, z_top, 5) for a, b in srange_fn(zm))
    ns, nz = int(L / res) + 1, int((z_top - z_bot) / res) + 1
    valid = np.zeros((ns, nz), bool)
    ss = (np.arange(ns) + 0.5) * res
    zt_arr = np.array([ztop_fn(s_) for s_ in ss]) if ztop_fn is not None else None
    for j in range(nz):
        z = z_bot + (j + 0.5) * res
        row = np.zeros(ns, bool)
        for a, b in srange_fn(z):
            row |= (ss >= a + 0.012) & (ss <= b - 0.012)
        for ea, eb in excl_fn(z - 0.004, z + 0.004, z):
            row &= ~((ss >= ea - 0.012) & (ss <= eb + 0.012))
        if zt_arr is not None:
            row &= z < zt_arr - 0.015
        valid[:, j] = row
    valid[:, :2] = False
    valid[:, -2:] = False
    stone = stone_footprint_mask(S, 0.0, z_bot, res, (ns, nz))
    empty = valid & ~stone
    frac0 = empty.sum() / max(valid.sum(), 1)
    pins = {k: [] for k in S.keys()}
    filled = ~empty
    for it in range(4000):
        core = box_sum(~filled, 1) == 9
        idx = np.flatnonzero(core)
        if len(idx) == 0:
            break
        # deterministic pick: stride through the candidates
        pick = idx[(it * 7919) % len(idx)]
        i, j = np.unravel_index(pick, core.shape)
        # free extent along s and z
        def run(arr):
            n = 0
            for v in arr:
                if v:
                    break
                n += 1
            return n
        l = run(filled[i::-1, j][:40])
        rgt = run(filled[i:, j][:40])
        d = run(filled[i, j::-1][:30])
        u = run(filled[i, j:][:30])
        hx = max((l + rgt - 1) * res * 0.5 - 0.006, 0.008)
        hy = max((d + u - 1) * res * 0.5 - 0.006, 0.008)
        sc = (i - l + 1 + (l + rgt - 1) * 0.5) * res
        zc = z_bot + (j - d + 1 + (d + u - 1) * 0.5) * res
        # long thin voids: split into chunks
        if hx > 0.16:
            hx = rng.uniform(0.05, 0.12)
            sc = (i + 0.5) * res
        if hy > 0.10:
            hy = rng.uniform(0.04, 0.08)
            zc = z_bot + (j + 0.5) * res
        a0, a1 = int(max(sc - hx - 0.006, 0) / res), int((sc + hx + 0.006) / res) + 1
        b0, b1 = int(max(zc - hy - 0.006 - z_bot, 0) / res), int((zc + hy + 0.006 - z_bot) / res) + 1
        filled[a0:a1, b0:b1] = True
        filled[i, j] = True
        pins["sc"].append(sc)
        pins["zc"].append(zc)
        pins["hx"].append(hx)
        pins["hy"].append(hy)
        pins["f"].append(rng.uniform(0.004, cfg["front"][1] * 0.6))
        pins["back"].append(0.05)
        pins["r"].append(rng.uniform(0.004, 0.009))
        pins["rot"].append(rng.normal(0, 0.15))
        pins["zcrs"].append(zc)
        pins["pillow"].append(rng.uniform(0.002, 0.006))
        pins["tiltx"].append(rng.normal(0, 0.002))
        pins["tilty"].append(rng.normal(0, 0.002))
        for kk in ("shl", "shr", "sbb", "sbt"):
            if kk in pins:
                pins[kk].append(0.0)
        for kk in pins:
            if len(pins[kk]) < len(pins["sc"]):
                pins[kk].append(0.0)
    P = {k: np.array(v, float) for k, v in pins.items()}
    frac1 = (valid & ~filled).sum() / max(valid.sum(), 1)
    log(f"  {label} visible mortar {frac0 * 100:.1f}% -> {frac1 * 100:.1f}% after {len(P['sc'])} pinning stones")
    return P, frac0, frac1


def filt(S, mask):
    return {k: v[mask] for k, v in S.items()}


def cat_stones(*Ss):
    keys = Ss[0].keys()
    return {k: np.concatenate([np.asarray(s[k], float) for s in Ss]) for k in keys}


def stone_rec(sc, zc, hx, hy, f, back, r, zcrs, rng, pillow=(0.002, 0.006), rot=0.004, tilt=0.002):
    M = len(np.atleast_1d(sc))
    return {"sc": np.atleast_1d(np.asarray(sc, float)), "zc": np.atleast_1d(np.asarray(zc, float)),
            "hx": np.broadcast_to(np.asarray(hx, float), (M,)).copy(),
            "hy": np.broadcast_to(np.asarray(hy, float), (M,)).copy(),
            "f": np.broadcast_to(np.asarray(f, float), (M,)).copy(),
            "back": np.broadcast_to(np.asarray(back, float), (M,)).copy(),
            "r": np.broadcast_to(np.asarray(r, float), (M,)).copy(),
            "zcrs": np.broadcast_to(np.asarray(zcrs, float), (M,)).copy(),
            "rot": rng.normal(0, rot, M), "pillow": rng.uniform(*pillow, M),
            "tiltx": rng.normal(0, tilt, M), "tilty": rng.normal(0, tilt, M)}


def _g(S, k, i, d=0.0):
    v = S.get(k)
    return float(v[i]) if v is not None else d


def polygonize(S, sel, rng, p_cut=0.34, p_taper=0.16, p_kink=0.12):
    """turn a share of the selected (hero) stones into non-rectangular pieces: knocked-off corners (5-6 sided),
    one long bed angled 5-14 deg (wedges), kinked top beds (6-7 sided). Voids are later pinned by fill_voids."""
    M = len(S["sc"])
    for k in ("cq0", "cq1", "cq2", "cq3", "ca0", "ca1", "ca2", "ca3", "kk", "kt", "spl"):
        if k not in S:
            S[k] = np.zeros(M)
    for i in np.flatnonzero(sel):
        hx, hy = S["hx"][i], S["hy"][i]
        if hx < 0.06 or hy < 0.035:
            continue
        u = rng.uniform()
        if u < p_cut:
            ncut = 1 if rng.uniform() < 0.65 else 2
            for k in rng.choice(4, ncut, replace=False):
                S[f"cq{k}"][i] = min(rng.uniform(0.035, 0.11), 0.9 * hy, 0.6 * hx)
                S[f"ca{k}"][i] = rng.uniform(0.6, 1.6)
        elif u < p_cut + p_taper:
            ang = math.radians(rng.uniform(5.0, 14.0))
            D = min(2 * hx * math.tan(ang), 0.9 * hy)
            sg = 1 if rng.uniform() < 0.5 else -1
            if rng.uniform() < 0.6:          # top bed drops toward one end
                S["sbt"][i] -= sg * D / (2 * hx)
                S["hy"][i] -= D / 4
                S["zc"][i] -= D / 4
            else:                             # bottom bed rises toward one end
                S["sbb"][i] += sg * D / (2 * hx)
                S["hy"][i] -= D / 4
                S["zc"][i] += D / 4
        elif u < p_cut + p_taper + p_kink:
            S["kk"][i] = rng.uniform(0.012, 0.028)
            S["kt"][i] = rng.uniform(0.3, 0.7)
        # 1-2 big split planes on (almost) every hero face
        S["spl"][i] = 1 + (rng.uniform() < 0.45)
    return S


def rough_footing(S, rng):
    """footing stones read as split field stone, not kerbs: tops slope 3-8 deg (the course above is pinned onto
    them), 1-2 cm pillow, two split planes, heavy chipped arrises (flag 'footx' read by the coursed_poly style)."""
    M = len(S["sc"])
    for k in ("sbt", "footx"):
        if k not in S:
            S[k] = np.zeros(M)
    for i in np.flatnonzero(S["foot"] > 0.5):
        hx = float(S["hx"][i])
        t = math.tan(math.radians(rng.uniform(3.0, 8.0))) * rng.choice([-1, 1])
        D = abs(t) * hx
        S["sbt"][i] += t
        S["hy"][i] -= D / 2
        S["zc"][i] -= D / 2
        S["pillow"][i] = rng.uniform(0.08, 0.11)
        S["spl"][i] = 2
        # knock off 1-2 top corners (the field stone outline, not a sawn block)
        if all(S[f"cq{q}"][i] < 0.004 for q in range(4)) and "cq0" in S:
            for q in rng.choice([2, 3], 1 + int(rng.uniform() < 0.5), replace=False):
                S[f"cq{q}"][i] = min(rng.uniform(0.05, 0.12), 0.6 * float(S["hy"][i]), 0.4 * hx)
                S[f"ca{q}"][i] = rng.uniform(0.6, 1.6)
        S["footx"][i] = 1.0
        S["tiltx"][i] = rng.normal(0, 0.010)
        # round 6: the face leans back 1.5-3.5 cm toward the top (a field stone bedded on its broad side, not a
        # plumb kerb face); the foot bulges out to the ground
        S["tilty"][i] = -rng.uniform(0.015, 0.035)
    return S


def dress_irregular(S, rng, rot_sd=0.012):
    """dressed blocks set +-1-2 deg out of square (sheared ends / beds, slight rotation)."""
    M = len(S["sc"])
    sgn = lambda: np.where(rng.uniform(0, 1, M) < 0.5, -1.0, 1.0)
    S["shl"] = sgn() * np.tan(np.radians(rng.uniform(0.8, 2.0, M)))
    S["shr"] = sgn() * np.tan(np.radians(rng.uniform(0.8, 2.0, M)))
    S["sbb"] = sgn() * np.tan(np.radians(rng.uniform(0.3, 1.2, M)))
    S["sbt"] = sgn() * np.tan(np.radians(rng.uniform(0.3, 1.2, M)))
    S["rot"] = rng.normal(0, rot_sd, M)
    S["margin"] = rng.uniform(0.02, 0.03, M)
    S["tiltx"] = rng.normal(0, 0.004, M)
    S["tilty"] = rng.normal(0, 0.004, M)
    S["pillow"] = rng.uniform(0.001, 0.003, M)


def mortar_sheet(acc, mapfn, s_edges, z_edges, near_fn, keep_fn, sub=5, w0=-0.004, w_amp=0.003, seed=0.0):
    """recessed mortar body as a coarse cell sheet behind the stones (cells subdivided sub x sub only where
    near_fn says so: openings, junctions); keep_fn(s, z) culls cells (openings, buried zones). Duplicate
    corner vertices are welded in finalize."""
    s_edges = np.asarray(s_edges, float)
    z_edges = np.asarray(z_edges, float)
    SA, ZA = np.meshgrid(s_edges[:-1], z_edges[:-1], indexing="ij")
    SB, ZB = np.meshgrid(s_edges[1:], z_edges[1:], indexing="ij")
    SA, ZA, SB, ZB = SA.ravel(), ZA.ravel(), SB.ravel(), ZB.ravel()
    nr = near_fn(0.5 * (SA + SB), 0.5 * (ZA + ZB), SB - SA, ZB - ZA)
    cells = [np.stack([SA[~nr], ZA[~nr], SB[~nr], ZB[~nr]], 1)]
    if nr.any():
        f = (np.arange(sub) / sub)
        sa, za, sb, zb = SA[nr], ZA[nr], SB[nr], ZB[nr]
        ds, dz = (sb - sa) / sub, (zb - za) / sub
        for i in range(sub):
            for j in range(sub):
                cells.append(np.stack([sa + ds * i, za + dz * j, sa + ds * (i + 1), za + dz * (j + 1)], 1))
    C = np.concatenate(cells)
    keep = keep_fn(0.5 * (C[:, 0] + C[:, 2]), 0.5 * (C[:, 1] + C[:, 3]))
    C = C[keep]
    S4 = np.stack([C[:, 0], C[:, 2], C[:, 2], C[:, 0]], 1).ravel()
    Z4 = np.stack([C[:, 1], C[:, 1], C[:, 3], C[:, 3]], 1).ravel()
    W4 = w0 + w_amp * vnoise90(np.stack([S4 * 2.1, Z4 * 2.1, np.full(len(S4), seed)], -1))
    V = mapfn(S4, Z4, W4)
    q = np.arange(len(C) * 4).reshape(-1, 4)
    # wind every cell outward (toward +w) so the sheet never shows its back through a joint
    O = mapfn(S4, Z4, W4 + 0.01) - V
    n_ = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 3]] - V[q[:, 0]])
    flip = (n_ * O[q[:, 0]]).sum(1) < 0
    q[flip] = q[flip][:, ::-1]
    acc.add(V, q, "M_mortar")
    return len(C)


def round_map_factory(center, r_nom_fn, r_eff_fn):
    """surface map for a round (optionally clipped) battered wall: s = arc length at the course's nominal radius,
    z up, w outward along the surface normal."""
    cx, cy = float(center[0]), float(center[1])

    def mapfn(s, z, w, zc):
        th = np.asarray(s, float) / r_nom_fn(zc)
        z = np.asarray(z, float)
        r = r_eff_fn(th, z)
        e = 1e-3
        drdz = (r_nom_fn(z + e) - r_nom_fn(z - e)) / (2 * e)
        nr = 1 / np.sqrt(1 + drdz ** 2)
        R = r + np.asarray(w) * nr
        return np.stack([cx + R * np.cos(th), cy + R * np.sin(th), z - np.asarray(w) * drdz * nr], -1)
    return mapfn


def round_stone_wall(name, coll, center, radius_fn, z0, z1, seed, cfg, eff_radius_fn=None, excl_fn=None,
                     cull_fn=None, extra_fn=None, mortar_cull_fn=None, side_depth=0.018, relief=None):
    """Kit component: a round coursed-rubble wall / tower body. radius_fn(z) is the nominal (battered / flared)
    profile, eff_radius_fn(theta, z) an optional clipped version (engaged in other walls). Stepped polygonal footing,
    pinned voids, shallow stone sides (no buried geometry) and a recessed mortar body. Returns the stone record."""
    rng = np.random.default_rng(seed)
    eff = eff_radius_fn if eff_radius_fn is not None else (lambda th, z: radius_fn(z))
    mapfn = round_map_factory(center, radius_fn, eff)
    excl = excl_fn if excl_fn is not None else (lambda a_, b_, c_: [])
    acc = Acc(f"{name}_stones")
    srange = lambda zm: [(0.0, 2 * math.pi * float(radius_fn(zm)))]
    S = layout_wall(rng, srange, z0, z1, excl, cfg)
    S = polygonize(S, S["foot"] > 0.5, np.random.default_rng(seed + 305))
    S = rough_footing(S, np.random.default_rng(seed + 306))
    pins, _, _ = fill_voids(S, srange, excl, z0, z1, rng, cfg, label=name)
    S = cat_stones(S, pins)
    if cull_fn is not None:
        P = mapfn(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
        S = filt(S, ~cull_fn(P))
    log(f"  {name} stones", len(S["sc"]))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    foot = (S["foot"] > 0.5) & ~small
    lay_poly_stones(acc, filt(S, foot), mapfn, "M_stone", np.random.default_rng(seed + 406), rough=1.15,
                      side_depth=side_depth, relief=relief)
    small &= ~foot
    low = (S["zc"] < 3.6) & ~foot
    lay_stones(acc, filt(S, ~small & low), mapfn, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009,
                 side_depth=side_depth, relief=relief)
    lay_stones(acc, filt(S, ~small & ~low & ~foot), mapfn, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009,
                 nz2=True, side_depth=side_depth, relief=relief)
    lay_stones(acc, filt(S, small), mapfn, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=side_depth, relief=relief)
    if extra_fn is not None:
        extra_fn(acc)
    finalize(acc, coll, smooth_deg=28.0)
    accm = Acc(f"{name}_mortar")
    zs = np.linspace(max(z0, CLIP_Z), z1 + 0.02, 26)
    cx, cy = float(center[0]), float(center[1])
    V, F = lathe_rz(np.stack([radius_fn(zs) - 0.004, zs], 1), 120, cx=cx, cy=cy, cap_bottom=False, cap_top=False)
    thv = np.arctan2(V[:, 1] - cy, V[:, 0] - cx)
    rv = eff(thv, V[:, 2]) - 0.004
    V[:, 0] = cx + rv * np.cos(thv)
    V[:, 1] = cy + rv * np.sin(thv)
    Vg = V.reshape(len(zs), 120, 3)
    Cq = 0.25 * (Vg[:-1] + np.roll(Vg[:-1], -1, 1) + Vg[1:] + np.roll(Vg[1:], -1, 1))
    keep = np.ones(len(F[0]), bool) if mortar_cull_fn is None else ~mortar_cull_fn(Cq.reshape(-1, 3))
    accm.add(V, F[0][keep], "M_mortar")
    finalize(accm, coll)
    return S

