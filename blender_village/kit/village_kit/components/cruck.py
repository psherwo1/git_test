"""components.cruck -- the CRUCK / ARCHED-BRACE GABLE FRAME of the timber family (kit, variant v5_harbour_house round
2; new module: nothing in the kit builds a curved-member timber frame or an arched opening framed in timber).

A heavy timber frame standing in a gable plane over a wide opening (ref4: the boat hall's water gable; equally a
barn's cart entrance or a boathouse's water door), on stone piers either side:

    cruck_frame(g, name, O, t, n, half, top_fn, z_pier, clear, ...)   KIT COMPONENT
        O, t, n      the frame's plane: O = the gable face's centre point at Z = 0, t along the gable, n outward
        half         half width of the gable at the outer faces (the piers' outer corners)
        top_fn(x, y) the rake the frame rises to (e.g. timber_walls.roof_top_fn(roof): the deck underside + 2 cm, so a
                     sagging / flared GableRoof gives curved blades)
        z_pier       the stone piers' top: the TIE BEAM bears on them (from the pier tops inward)
        clear        the opening's clear width between the stone jambs; the JAMB POSTS stand inside it on dressed pad
                     stones (corbelled from the quay / jamb foot), the ARCHED BRACES spring from the posts at
                     `spring` and meet under the tie beam's centre (a segmental arch: round or segmental only, art bible
                     1.8), a KING STRUT runs from the tie to the COLLAR, the curved BLADES (principals) rise from the
                     tie ends to the apex along the rake with an elbowed inner edge, CURVED BRACES carry the collar,
                     and a short king post closes the apex
        infill       "plank": vertical boards (timber_walls ROUGH board widths, out of true, chunky edges) set back
                     between the members over the upper gable and the arch spandrels, on a closed backing sheet
                     (note 6: no see-through between boards); None: members only
    Objects <P>_<name>_frame (members, M_timber), _boards (infill), _blocker (backing), _pads (M_stone_dressed).
    Publishes g.CRUCKS (O, t, n, half, clear, tie_z, spring, crown) for the decal recipe (composite.timber_anchors).
    The opening itself is open (boats moor inside under the arch); its clear height is the arch intrados.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, prof_rect, sweep
from .timber_walls import EZ, _sheet, board_widths, rough_opts, wbox


def _scan_root(fn, a, b, n=400):
    """the first s in [a, b] (walking from a) where fn(s) >= 0; b if none."""
    for s in np.linspace(a, b, n):
        if fn(float(s)) >= 0:
            return float(s)
    return float(b)


def _ribbon(acc, P, top, bot, w0, w1, mat, wear=None):
    """a closed extruded ribbon: plan-of-wall polyline samples s with top(s) / bot(s) edges, between w0 and w1.
    P(s, z, w) -> world point.  One piece."""
    k = len(top)
    # 4 vertices per station: front-top, front-bottom, back-bottom, back-top (a closed quad tube, capped)
    V = np.array([[P(top[i, 0], top[i, 1], w1), P(bot[i, 0], bot[i, 1], w1), P(bot[i, 0], bot[i, 1], w0),
                   P(top[i, 0], top[i, 1], w0)] for i in range(k)]).reshape(-1, 3)
    Fq = []
    for i in range(k - 1):
        for j in range(4):
            a, b = i * 4 + j, i * 4 + (j + 1) % 4
            Fq.append((a, a + 4, b + 4, b))
    acc.add(V, [np.array(Fq), np.array([[0, 1, 2, 3]]), np.array([[(k - 1) * 4 + j for j in (3, 2, 1, 0)]])], mat,
            wear=wear)


def cruck_frame(g, name, O, t, n, half, top_fn, z_pier, clear, spring=2.2, tie=0.28, member_w=(-0.28, 0.02),
                post=0.24, arch_t=0.24, blade=0.30, collar_at=0.50, collar=0.22, braces=True, pads=True,
                infill="plank", infill_w=(-0.125, -0.088), backing_w=(-0.16, -0.13), rough=True, seed=901):
    """KIT COMPONENT (see the module doc)."""
    O = np.asarray(O, float)
    t = np.asarray(t, float) / np.linalg.norm(t)
    n = np.asarray(n, float) / np.linalg.norm(n)
    rng = np.random.default_rng(seed)
    ro = rough_opts(rough)
    pre = f"{g.prefix}_{name}"
    fr, bd, bk, pd = Acc(pre + "_frame"), Acc(pre + "_boards"), Acc(pre + "_blocker"), Acc(pre + "_pads")
    w0, w1 = member_w

    def P(s, z, w):
        return O + s * t + z * EZ + w * n

    def rake(s):
        p = O + s * t
        return float(top_fn(p[0], p[1]))
    F = (O, t, n)
    tie_top = z_pier + tie
    # ---- the tie beam: on the pier tops, as far out as it stays 2 cm under the rake
    s_tie = half - _scan_root(lambda d: rake(half - d) - (tie_top + 0.02), 0.0, half)
    wbox(fr, F, -s_tie, s_tie, z_pier, tie_top, w0, w1, "M_timber", r=0.02, ns=max(6, int(2 * s_tie / 0.5) + 3),
         sag=0.0 if ro is None else 0.6 * ro["sag"])
    # ---- jamb posts on dressed pad stones, inside the stone jambs
    a_in = clear / 2 - 0.04 - post                        # the posts' inner faces = the arch springing
    for sg in (-1, 1):
        s0, s1 = sorted((sg * a_in, sg * (clear / 2 - 0.04)))
        wbox(fr, F, s0, s1, 0.0, z_pier + 0.01, w0, w1, "M_timber", r=0.018, ns=4, nz=6,
             tilt=0.0 if ro is None else math.radians(0.4) * rng.uniform(-1, 1))
        if pads:
            p0, p1 = sorted((sg * (a_in - 0.05), sg * (clear / 2 + 0.03)))
            wbox(pd, F, p0, p1, -0.30, 0.0, w0 - 0.07, w1 + 0.05, "M_stone_dressed", r=0.02, ns=5, nz=4)
    # ---- the segmental arch: intrados through (+-a_in, spring) and (0, crown), crown under the tie
    crown = z_pier - arch_t - 0.004
    rise = crown - spring
    if rise <= 0.2:
        raise ValueError(f"cruck_frame {name}: the arch rise {rise:.2f} m is too small (spring {spring:.2f}, "
                         f"tie underside {z_pier:.2f})")
    R = (a_in ** 2 + rise ** 2) / (2 * rise)
    zc = crown - R
    th0 = math.asin(min(1.0, a_in / R))
    wm = 0.5 * (w0 + w1) - 0.01
    for sg in (-1, 1):
        th = np.linspace(th0, 0.0, 18)                   # from the springing to the crown
        rr = R + 0.5 * arch_t
        path = np.array([P(sg * rr * math.sin(a), zc + rr * math.cos(a), wm) for a in th])
        V, Fc = sweep(path, n, prof_rect(arch_t, (w1 - w0) - 0.02, 0.02))
        fr.add(V, Fc, "M_timber", wear=float(rng.uniform(0.3, 0.6)))

    def extrados(s):
        s = min(abs(s), a_in)
        return zc + math.sqrt(max((R + arch_t) ** 2 - s * s, 0.0))
    # ---- blades: the rake's underside, elbowed inner edge, from the tie top to the apex (one piece a side)
    apex = rake(0.0)
    blade_bot = {}
    for sg in (-1, 1):
        ss = np.linspace(sg * (s_tie - 0.02), 0.0, 28)
        top = np.array([(s, rake(s) - 0.012) for s in ss])
        knee = np.clip(1.0 - np.abs(np.abs(ss) - 0.72 * s_tie) / (0.45 * s_tie), 0.0, 1.0) ** 1.5
        bot_z = np.maximum(top[:, 1] - blade * (1.0 + 0.9 * knee), tie_top - 0.01)
        keep = top[:, 1] - bot_z > 0.04
        ss_, top_, bot_ = ss[keep], top[keep], bot_z[keep]
        bot = np.stack([ss_, bot_], 1)
        _ribbon(fr, P, top_, bot, w0, w1, "M_timber", wear=float(rng.uniform(0.3, 0.6)))
        blade_bot[sg] = (ss_, bot_)
    # ---- collar between the blades, king strut (tie -> collar) and king post (collar -> apex)
    z_col = tie_top + collar_at * (apex - tie_top)

    def blade_under(sg, s):
        ss_, bb = blade_bot[sg]
        o = np.argsort(ss_)
        return float(np.interp(s, ss_[o], bb[o]))
    s_col = _scan_root(lambda s: (z_col + collar) - blade_under(1, s) - 0.0, 0.0, s_tie)
    wbox(fr, F, -s_col - 0.05, s_col + 0.05, z_col, z_col + collar, w0 + 0.02, w1 - 0.01, "M_timber", r=0.016,
         ns=6, clamp=lambda s: rake(s) - 0.02)
    wbox(fr, F, -0.09, 0.09, tie_top - 0.01, z_col + 0.01, w0 + 0.03, w1 - 0.015, "M_timber", r=0.014, nz=6)
    if apex - (z_col + collar) > 0.25:
        wbox(fr, F, -0.08, 0.08, z_col + collar - 0.01, apex - 0.02, w0 + 0.03, w1 - 0.015, "M_timber", r=0.012,
             nz=5, clamp=lambda s: rake(s) - 0.015)
    # ---- curved braces: from the blade's inner edge (down the rake) to the collar's underside
    if braces:
        for sg in (-1, 1):
            sa = sg * min(s_tie - 0.35, s_col + 0.75)
            za = blade_under(sg, sa) + 0.04
            sb, zb = sg * max(0.25, s_col - 0.55), z_col + 0.02
            # a quarter-ellipse bowing down-and-in (the "arched brace" of ref4)
            u = np.linspace(0.0, 1.0, 14)
            ps = sa + (sb - sa) * np.sin(0.5 * np.pi * u)
            pz = za + (zb - za) * (1.0 - np.cos(0.5 * np.pi * u))
            path = np.array([P(s, z, wm) for s, z in zip(ps, pz)])
            V, Fc = sweep(path, n, prof_rect(0.17, (w1 - w0) - 0.06, 0.015))
            fr.add(V, Fc, "M_timber", wear=float(rng.uniform(0.3, 0.6)))
    # ---- plank infill + backing: the upper gable (over the tie / pier tops) and the arch spandrels
    n_b = 0
    if infill == "plank":
        rb = ro or dict(w=(0.16, 0.30), fillet=(0.0, (0.1, 0.1)), tilt_deg=0.0, sag=0.0, edge_r=0.006,
                        end_jag=0.0, thick=(0.03, 0.03), w_jit=0.0)

        def floor_up(s):
            return (tie_top - 0.03) if abs(s) <= s_tie else (z_pier - 0.03)
        xs = board_widths(rng, -half + 0.01, half - 0.01, None, rb)
        tilt = math.radians(rb["tilt_deg"])
        for j in range(len(xs) - 1):
            a, b = xs[j] + 0.004, xs[j + 1] - 0.004
            hi = max(rake(a), rake(b))
            lo = min(floor_up(a), floor_up(b))
            if hi - lo < 0.05:
                continue
            th_ = rng.uniform(*rb["thick"])
            wj = rng.uniform(-rb["w_jit"], rb["w_jit"])
            wbox(bd, F, a, b, lo, hi, infill_w[0] + wj, infill_w[0] + wj + th_, "M_timber_weathered",
                 r=rb["edge_r"], ns=4, nz=max(4, int((hi - lo) / 0.6) + 3), clamp=lambda s: rake(s) - 0.004,
                 floor=floor_up, skip_back=True, tilt=tilt * rng.uniform(-1, 1))
            n_b += 1
        # spandrels: between the arch's extrados and the tie's underside
        xs = board_widths(rng, -a_in, a_in, None, rb)
        for j in range(len(xs) - 1):
            a, b = xs[j] + 0.004, xs[j + 1] - 0.004
            lo = min(extrados(a), extrados(b)) - 0.03
            hi = z_pier + 0.03
            if hi - lo < 0.05:
                continue
            th_ = rng.uniform(*rb["thick"])
            wbox(bd, F, a, b, lo, hi, infill_w[0], infill_w[0] + th_, "M_timber_weathered", r=rb["edge_r"], ns=4,
                 nz=4, floor=lambda s: extrados(s) - 0.03, skip_back=True)
            n_b += 1
        # the closed backing behind the boards (cells inside the infill regions only)
        ss = np.unique(np.round(np.concatenate([np.linspace(-half, half, int(2 * half / 0.15) + 1),
                                                [-s_tie, s_tie, -a_in, a_in]]), 5))
        zs = np.unique(np.round(np.concatenate([np.linspace(spring, apex + 0.05, int((apex - spring) / 0.12) + 2),
                                                [z_pier, tie_top]]), 5))

        def keep(i, k):
            sm, zm = 0.5 * (ss[i] + ss[i + 1]), 0.5 * (zs[k] + zs[k + 1])
            if zm > rake(sm) + 0.05:
                return False
            if zm >= floor_up(sm) - 0.02:
                return True
            return abs(sm) < a_in and zm > extrados(sm) - 0.06 and zm < z_pier + 0.02
        _sheet(bk, F, ss, zs, keep, backing_w[0], backing_w[1], "M_timber_weathered", clamp=lambda s: rake(s) - 0.008)
    for a_ in (fr, bd, bk, pd):
        if a_.n:
            finalize(a_, g.coll, smooth_deg=30.0)
    if not hasattr(g, "CRUCKS"):
        g.CRUCKS = []
    g.CRUCKS.append(dict(name=name, O=O, t=t, n=n, half=half, clear=clear, tie_z=z_pier, spring=spring,
                         crown=crown, apex=apex))
    log(f"  {pre}: cruck / arched-brace frame: clear {clear:.2f} m, arch {spring:.2f} -> {crown:.2f} m (R {R:.2f}), "
        f"tie {z_pier:.2f}-{tie_top:.2f} over +-{s_tie:.2f}, collar {z_col:.2f}, apex {apex:.2f}, {n_b} infill boards")
    return g.CRUCKS[-1]


__all__ = ["cruck_frame"]
