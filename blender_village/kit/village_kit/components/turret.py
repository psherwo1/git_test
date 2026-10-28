"""components.turret -- an engaged round side turret with a corbelled cushion, a board drum and a bell cap (kit
1.1.0, from the hilltop keep; ref1's west turret).

side_turret(g, seed=1616)   KIT COMPONENT (g = OctFrame; profile g.TUR_ZF / TUR_RF from TUR_SCALE, centre TUR_C):
    a round coursed-rubble body (stone_wall.round_stone_wall) on a concave profile, clipped behind the annex's south
    wall face and bonded into its N and W walls with toothing stones every 2-3 courses; a corbelled CUSHION of two
    rough corbel courses (corbel_cushion: lopsided toward CUSH['droop_dir'], stepped beds packed with pinning stones,
    cleaved faces, rounded lips, mortar body); a drum of vertical boards (SIZE_TABLE 'board') between hewn sill and
    head rings; a bell cap (oct_roof.build_cap, chunky shingles) with a lead hat and a turned finial.
    -> <P>_turret_stones / _mortar, _turret_corbel_collar / _corbel_mortar, _turret_drum, _turret_cap_*,
       <P>_finial_turret
tooth_excl_wall(z0, z1, zm)  the s-ranges of the annex wall the toothing stones occupy (annex.annex_walls reads it)
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, TAN22, axn, finalize, obox, rbox_v, softplus
from ..shingles import SIZE_TABLE
from .finial import lead_hat, turned_finial
from .hewn import hewn_square, peg
from .oct_frame import (FR, cush_f, in_wing, junction, thatch_low, tur_r, tur_reff, wing_s_of, wing_under)
from .oct_roof import build_cap
from .stone_wall import lay_stones, round_stone_wall, stone_rec


def _lay(*a, **k):
    return lay_stones(*a, relief=FR.min_relief, **k)


def _hewn(*a, **k):
    return hewn_square(*a, relief=FR.min_relief, dropped=FR.dropped_checks, **k)


def tooth_map_factory(name):
    def mapfn(u, z, w, zc):
        u = np.asarray(u, float)
        z = np.asarray(z, float)
        w = np.asarray(w, float)
        xj, yj, thj, sg = junction(name, z)
        r = tur_r(z)
        if name == "N":
            pw = np.stack([xj + u, yj], -1)
            nw = np.stack([np.zeros_like(u), np.ones_like(u)], -1)
        else:
            pw = np.stack([xj + 0 * u, yj - u], -1)
            nw = np.stack([-np.ones_like(u), np.zeros_like(u)], -1)
        th = thj + sg * np.maximum(-u, 0) / r
        pt = np.stack([FR.TUR_C[0] + r * np.cos(th), FR.TUR_C[1] + r * np.sin(th)], -1)
        nt = np.stack([np.cos(th), np.sin(th)], -1)
        on_wall = (u >= 0)[..., None]
        P = np.where(on_wall, pw, pt)
        bl = np.clip(0.5 + u / 0.12, 0, 1)[..., None]
        bl = bl * bl * (3 - 2 * bl)
        N = nt * (1 - bl) + nw * bl
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        # bridge the concave crease: push the corner region out a little so the stone wraps it
        P = P + N * (w + 0.012 * np.exp(-(u / 0.06) ** 2))[..., None]
        return np.concatenate([P, z[..., None]], -1)
    return mapfn


def tooth_cull(P, which):
    """True for wall ('wall') or turret ('tur') stone centres displaced by a toothing stone."""
    P = np.asarray(P, float)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    bad = np.zeros(x.shape, bool)
    for t in FR.TOOTH:
        zin = (z > t["z0"] - 0.05) & (z < t["z1"] + 0.05)
        xj, yj, thj, sg = junction(t["j"], z)
        if which == "wall":
            if t["j"] == "N":
                u = x - xj
                onw = np.abs(y - yj) < 0.2
            else:
                u = yj - y
                onw = np.abs(x - xj) < 0.2
            bad |= zin & onw & (u > -0.05) & (u < t["Lw"] + 0.03)
        else:
            th = np.arctan2(y - FR.TUR_C[1], x - FR.TUR_C[0])
            dth = np.angle(np.exp(1j * (th - thj)))
            u = -sg * dth * tur_r(z)
            bad |= zin & (u < 0.05) & (u > -t["Lt"] - 0.03)
    return bad


def tooth_excl_wall(z0, z1, zm):
    """s-ranges (wing path coords) occupied by toothing stones in the band z0..z1."""
    out = []
    for t in FR.TOOTH:
        if z1 < t["z0"] - 0.012 or z0 > t["z1"] + 0.012:
            continue
        xj, yj, thj, sg = junction(t["j"], zm)
        sj = wing_s_of(float(xj), float(yj))
        if t["j"] == "N":
            out.append((sj - t["Lw"] - 0.012, sj + 0.4))
        else:
            out.append((sj - 0.4, sj + t["Lw"] + 0.012))
    return out


def tooth_excl_tur(z0, z1, zm):
    """s-ranges (turret coords, s = theta * r) occupied by toothing stones."""
    out = []
    r = float(tur_r(zm))
    L = 2 * math.pi * r
    for t in FR.TOOTH:
        if z1 < t["z0"] - 0.012 or z0 > t["z1"] + 0.012:
            continue
        xj, yj, thj, sg = junction(t["j"], zm)
        th = float(np.mod(thj, 2 * np.pi))
        a = th * r
        lo, hi = (a - 0.15, a + t["Lt"] + 0.012) if sg > 0 else (a - t["Lt"] - 0.012, a + 0.15)
        for sh in (-L, 0.0, L):
            if hi + sh > 0 and lo + sh < L:
                out.append((max(lo + sh, 0.0), min(hi + sh, L)))
    return out


def build_tooth_stones(acc, rng):
    for name in ("N", "W"):
        T = [t for t in FR.TOOTH if t["j"] == name]
        if not T:
            continue
        sc = np.array([(t["Lw"] - t["Lt"]) / 2 for t in T])
        hx = np.array([(t["Lw"] + t["Lt"]) / 2 for t in T])
        zc = np.array([(t["z0"] + t["z1"]) / 2 for t in T])
        hy = np.array([(t["z1"] - t["z0"]) / 2 - 0.006 for t in T])
        S = stone_rec(sc, zc, hx, hy, np.array([t["f"] for t in T]), 0.14, np.array([t["r"] for t in T]), zc, rng,
                      pillow=(0.003, 0.008), rot=0.01, tilt=0.004)
        _lay(acc, S, tooth_map_factory(name), "M_stone", rng, rough=1.1, grid=(16, 8), noise_amp=0.009)


def tur_map(s, z, w, zc):
    rc = tur_r(zc)
    th = np.asarray(s, float) / rc + math.pi * 0.0
    r = tur_reff(th, z)
    e = 1e-3
    drdz = (tur_r(np.asarray(z) + e) - tur_r(np.asarray(z) - e)) / (2 * e)
    nr = 1 / np.sqrt(1 + drdz ** 2)
    R = r + np.asarray(w) * nr
    return np.stack([FR.TUR_C[0] + R * np.cos(th), FR.TUR_C[1] + R * np.sin(th), np.asarray(z) - np.asarray(w) * drdz * nr], -1)


def corbel_cushion(acc, accm, center, spec=None):
    """Corbelled stone cushion under a turret cap (kit component): two rough corbel courses of individual stones in
    2-3 cm joints over a mortar body. The lower course projects proj_lo, the upper proj_up beyond the body, both
    growing toward droop_dir, where the lip also sits 'droop' lower; the whole outline wanders +-5 cm round the ring.
    Round 5, per stone: length 0.35-0.70 m, height 0.20-0.36 m (each upper stone its own height: the beds step and
    are packed with 2-4 pinning stones), tilt +-3-6 deg, outer face +-4 cm, 1.2-2 cm arrises, 2-3 planar cleaves
    4-8 cm deep, and a rounded (3-8 cm) top lip on only about half of the upper stones. The bed and head joints are
    filled with mortar recessed 3 cm (no open slot between the courses)."""
    spec = FR.CUSH if spec is None else spec
    rng = np.random.default_rng(spec["seed"])
    cx, cy = center
    rb, rd = spec["r_body"], spec["r_drum"]
    tw = math.tan(math.radians(spec["weather_deg"]))
    ztd = spec["z_top_drum"]
    wob = lambda th_, c_: 0.05 * (0.6 * np.sin(2 * th_ + 1.3 + c_) + 0.4 * np.sin(5 * th_ + 0.4 + 2 * c_))
    courses = []
    for c in (0, 1):
        r_ref = rb + (0.18 if c == 0 else 0.3)
        th = rng.uniform(0, 2 * np.pi)
        th0 = th
        st = []
        while th < th0 + 2 * np.pi - 1e-6:
            L = rng.uniform(*spec["stone_len"])
            if c == 1:
                # round 6: wider length spread on the upper course (no even 'tyre tread' rhythm)
                L = rng.uniform(spec["stone_len"][0] * 0.85, spec["stone_len"][1] * 1.08)
            dth = (L + spec["joint"]) / r_ref
            if th0 + 2 * np.pi - (th + dth) < spec["stone_len"][0] / r_ref * 0.8:
                dth = th0 + 2 * np.pi - th
            st.append((th, th + dth))
            th += dth
        courses.append(st)

    def covers(a_, b_, t_):
        return np.mod(t_ - a_, 2 * np.pi) <= np.mod(b_ - a_, 2 * np.pi)
    stones = []
    lo_top = []
    pins_wanted = set(int(i) for i in rng.choice(len(courses[1]), 3, replace=False))
    pins = []
    for c, st in enumerate(courses):
        for si, (ta, tb) in enumerate(st):
            tm = 0.5 * (ta + tb)
            f = float(cush_f(tm, spec))
            jt = spec["joint"] * rng.uniform(0.85, 1.2)
            dj = jt / (rb + 0.3)
            ta_, tb_ = ta + 0.5 * dj, tb - 0.5 * dj
            off = rng.uniform(-0.04, 0.04) * (1.5 if c == 1 else 1.0) + float(wob(tm, c))
            if c == 0:
                proj = spec["proj_lo"][0] + (spec["proj_lo"][1] - spec["proj_lo"][0]) * f + off
                zb = spec["z_base"] - spec["droop"] * f + rng.uniform(-0.015, 0.015)
                h = rng.uniform(0.20, 0.36) - 0.04 * f
                r_in = rb - 0.05
                lo_top.append((ta, tb, zb + h, rb + proj))
                top = zb + h
            else:
                proj = spec["proj_up"][0] + (spec["proj_up"][1] - spec["proj_up"][0]) * f + off
                tt = np.linspace(ta, tb, 9)
                zl = -1e9
                for (a_, b_, z_, r_) in lo_top:
                    if any(covers(a_, b_, t_) for t_ in tt):
                        zl = max(zl, z_)
                zb = zl + spec["joint"] * rng.uniform(0.85, 1.15)
                top = ztd + rng.uniform(-0.075, 0.03)
                h = top - zb
                if h > 0.34:
                    zb = top - 0.34
                    h = 0.34
                if h < 0.20:
                    h = 0.20
                    top = zb + h
                if si in pins_wanted and zb - zl < 0.05:
                    zb = zl + 0.055
                    h = top - zb
                if zb - zl > 0.04 and len(pins) < 4:
                    pins.append((ta_ + (tb_ - ta_) * rng.uniform(0.2, 0.8), zl, zb, rb + min(proj, 0.3)))
                r_in = rd - 0.12 if top < ztd - 0.015 else rd + 0.012
            stones.append(dict(c=c, ta=ta_, tb=tb_, r_in=r_in, r_out=rb + proj, zb=zb, h=h, f=f, top=top,
                               slope=tw + (spec["lip_droop"] * f / max(proj + rb - rd, 0.1) if c == 1 else 0.0)))
    nlo = sum(1 for s_ in stones if s_["c"] == 0)
    log(f"  cushion stones: {nlo} lower + {len(stones) - nlo} upper, {len(pins)} pinning stones")
    for sd in stones:
        r_out, r_in, h = sd["r_out"], sd["r_in"], sd["h"]
        hx = 0.5 * (sd["tb"] - sd["ta"]) * r_out
        dep = r_out - r_in
        ra = rng.uniform(0.012, 0.02)
        fine = bool(spec.get("bulb", False)) and sd["c"] == 1
        X = axn(np.array([-hx]), np.array([hx]), np.array([ra]), 11)
        Y = axn(np.array([0.0]), np.array([h]), np.array([ra]), 11 if fine else 7)
        Zc = axn(np.array([0.0]), np.array([dep]), np.array([ra]), 6 if sd["c"] == 0 else (11 if fine else 7))
        P, quads = rbox_v(X, Y, Zc, np.array([ra]), skip_back=True)
        P = P[0]
        Q = P.copy()
        # 2-3 planar cleaves 4-8 cm deep at the outline (crisp planes)
        planes = []
        for _ in range(int(rng.integers(2, 4))):
            ta_ = math.tan(math.radians(rng.uniform(14, 34))) * rng.choice([-1, 1])
            tb_ = math.tan(math.radians(rng.uniform(8, 26))) * rng.choice([-1, 1])
            n_ = np.array([ta_, tb_, 1.0])
            n_ /= np.linalg.norm(n_)
            corner = np.array([np.sign(n_[0]) * hx, (h if n_[1] > 0 else 0.0), dep])
            planes.append((n_, corner @ n_ - rng.uniform(0.04, 0.08) * max(n_[2], 0.5)))
        n_ = np.array([rng.uniform(-0.2, 0.2), -1.0, rng.uniform(0.6, 1.1)])
        n_ /= np.linalg.norm(n_)
        planes.append((n_, np.array([0.0, 0.0, dep]) @ n_ - rng.uniform(0.03, 0.06)))
        bulb = bool(spec.get("bulb", False)) and sd["c"] == 1
        bulb_on = bulb and rng.uniform() < 0.8
        if sd["c"] == 1 and not bulb_on:
            # 1-2 cleaved facets across the top / outer top edge (no upholstered top)
            for _ in range(int(rng.integers(1, 3))):
                n_ = np.array([rng.uniform(-0.5, 0.5), 1.0, rng.uniform(0.3, 0.9)])
                n_ /= np.linalg.norm(n_)
                corner = np.array([np.sign(n_[0]) * hx * rng.uniform(0.3, 1.0), h, dep])
                planes.append((n_, corner @ n_ - rng.uniform(0.03, 0.06)))
        for n_, d0 in planes:
            d = Q @ n_ - d0
            Q = Q - n_[None, :] * softplus(d, 0.003)[:, None]
        if bulb_on:
            # kit 1.3.0 (keep r8 must-fix 8, ref1's bulbous 'mossy rounded ring'): the top crowned 3-6 cm over the
            # stone's length and depth, and the outer top arris rounded over 6-10 cm (a quarter-round, not a cleave)
            crown = rng.uniform(0.03, 0.06)
            ux = np.clip(Q[:, 0] / max(hx, 1e-3), -1, 1)
            uz = np.clip(Q[:, 2] / max(dep, 1e-3), 0, 1)
            vb = np.clip(Q[:, 1] / max(h, 1e-3), 0, 1)
            Q[:, 1] = Q[:, 1] + crown * (1 - ux ** 2) * np.sin(np.pi * np.clip(0.15 + 0.85 * uz, 0, 1)) ** 0.7 * vb ** 2
            rl = rng.uniform(0.06, 0.10)
            yc, zc = h + 0.5 * crown - rl, dep - rl
            dy, dz = Q[:, 1] - yc, Q[:, 2] - zc
            m_ = (dy > 0) & (dz > 0)
            rr_ = np.hypot(dy, dz)
            s_ = np.where(m_ & (rr_ > rl), rl / np.maximum(rr_, 1e-9), 1.0)
            Q[:, 1] = np.where(m_, yc + dy * s_, Q[:, 1])
            Q[:, 2] = np.where(m_, zc + dz * s_, Q[:, 2])
        elif sd["c"] == 1 and rng.uniform() < 0.5:
            # rounded top outer lip on about half of the upper stones (3-8 cm)
            rl = rng.uniform(0.03, 0.08)
            n_ = np.array([0.0, 1.0, 1.0]) / math.sqrt(2)
            d0 = np.array([0.0, h, dep]) @ n_ - rl * 0.6
            d = Q @ n_ - d0
            Q = Q - n_[None, :] * softplus(d, 0.25 * rl)[:, None]
        r = r_in + Q[:, 2]
        bb = Q[:, 1]
        if sd["c"] == 1:
            bb = bb - sd["slope"] * np.clip(r - rd, 0, None) * np.clip(bb / max(h, 1e-3), 0, 1)
        tilt = math.tan(math.radians(rng.uniform(3, 6) * rng.choice([-1, 1])))
        pitch = math.tan(math.radians(rng.uniform(-3, 3)))
        bb = bb + tilt * Q[:, 0] + pitch * (Q[:, 2] - dep)
        # round 6: each stone yawed 4-10 deg in plan (one end stands proud of its neighbour: a stepped, lumpy
        # outline instead of a turned ring) and about half get a bellied outer face (2-4 cm)
        wq = np.clip(Q[:, 2] / max(dep, 1e-3), 0.0, 1.0)
        yaw = math.tan(math.radians(rng.uniform(4, 10))) * rng.choice([-1, 1])
        r = r + yaw * Q[:, 0] * wq
        if rng.uniform() < 0.55:
            vb = np.clip(Q[:, 1] / max(h, 1e-3), 0.0, 1.0)
            r = r + rng.uniform(0.02, 0.04) * (4 * vb * (1 - vb)) * wq ** 2
        thv = 0.5 * (sd["ta"] + sd["tb"]) + Q[:, 0] / r_out
        W = np.stack([cx + r * np.cos(thv), cy + r * np.sin(thv), sd["zb"] + bb], 1)
        acc.add(W, quads, "M_stone", uv=np.stack([Q[:, 0] + Q[:, 2], Q[:, 1]], 1))
    # pinning stones packed into the stepped beds (flat slabs, 1 cm back from the lower course face)
    for (tp, zl, zb, r_o) in pins:
        hh = max(zb - zl - 0.008, 0.025)
        L = rng.uniform(0.10, 0.18)
        X = axn(np.array([-L / 2]), np.array([L / 2]), np.array([0.008]), 5)
        Y = axn(np.array([0.0]), np.array([hh]), np.array([0.008]), 4)
        Zc = axn(np.array([0.0]), np.array([0.12]), np.array([0.008]), 4)
        P, quads = rbox_v(X, Y, Zc, np.array([0.008]), skip_back=True)
        P = P[0]
        r = r_o - 0.13 + P[:, 2] - 0.01
        thv = tp + P[:, 0] / r_o
        W = np.stack([cx + r * np.cos(thv), cy + r * np.sin(thv), zl + 0.004 + P[:, 1] +
                      0.01 * P[:, 0] / L], 1)
        acc.add(W, quads, "M_stone")
    # mortar body, per angle from the stones over it: lower course face -3.5 cm, bed joint filled to 3 cm behind
    # the lower course face, upper course -4 cm, top -3.5 cm under the drum
    NT = 180
    th = np.linspace(0, 2 * np.pi, NT, endpoint=False)

    def course_at(c, key, default):
        out = np.full(NT, np.nan)
        for sd in stones:
            if sd["c"] != c:
                continue
            m_ = covers(sd["ta"] - 0.02, sd["tb"] + 0.02, th)
            out = np.where(m_ & np.isnan(out), sd[key], np.where(m_, np.maximum(out, sd[key]) if key != "zb"
                                                                  else np.minimum(out, sd[key]), out))
        return np.where(np.isnan(out), default, out)
    f = cush_f(th, spec)
    r_lo = course_at(0, "r_out", rb + 0.15)
    zlo = course_at(0, "zb", spec["z_base"])
    lt = course_at(0, "top", spec["z_base"] + 0.28)
    ub = course_at(1, "zb", spec["z_base"] + 0.3)
    r_up = course_at(1, "r_out", rb + 0.3)
    top = course_at(1, "top", ztd)
    zto = top - tw * (r_up - rd) - spec["lip_droop"] * f
    prof = [(np.full(NT, rb - 0.03), zlo - 0.05), (r_lo - 0.035, zlo + 0.035), (r_lo - 0.035, lt - 0.005),
            (r_lo - 0.03, np.maximum(ub, lt) + 0.012), (r_up - 0.04, np.maximum(ub, lt) + 0.04),
            (r_up - 0.04, zto - 0.06), (r_up - 0.07, zto - 0.035), (np.full(NT, rd - 0.01), np.full(NT, ztd - 0.035))]
    R_ = np.stack([np.broadcast_to(p_[0], (NT,)) for p_ in prof], 1)
    Z_ = np.stack([np.broadcast_to(p_[1], (NT,)) for p_ in prof], 1)
    npf = R_.shape[1]
    V = np.stack([cx + R_ * np.cos(th)[:, None], cy + R_ * np.sin(th)[:, None], Z_], -1).reshape(-1, 3)
    i = np.arange(NT)[:, None]
    j = np.arange(npf - 1)[None, :]
    a0 = i * npf + j
    b0 = ((i + 1) % NT) * npf + j
    accm.add(V, np.stack([a0, a0 + 1, b0 + 1, b0], -1).reshape(-1, 4), "M_mortar")
    return stones


def build_cushion(coll, rng):
    acc = Acc(FR.prefix + "_turret_corbel_collar")
    accm = Acc(FR.prefix + "_turret_corbel_mortar")
    corbel_cushion(acc, accm, (float(FR.TUR_C[0]), float(FR.TUR_C[1])), FR.CUSH)
    finalize(acc, coll, smooth_deg=26.0)
    finalize(accm, coll)


def turret_cull(C, wing_margin=0.0):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    fp = (x > FR.WX_W - FR.W_OVH) & (x < FR.WX_E + FR.W_OVH) & (y > FR.WY_S - FR.W_OVH) & (y < FR.WY_N + FR.W_OVH)
    bad = fp & (z > wing_under(x, y) - 0.06) & (z < thatch_low(x, y) - 0.02)
    bad |= in_wing(C, margin=wing_margin, zpad=0.0)
    return bad


def build_turret(coll, seed=1616, saddles=False, cap_exposure=None, bulb_cushion=False, drum_backing=False,
                 saddle_taper=None):
    rng = np.random.default_rng(seed)
    if bulb_cushion:
        FR.CUSH["bulb"] = True
    cfg = dict(seed=23 + (seed - 1616), footing=0.31, ch=(0.09, 0.17), p_tall=0.07, len=(0.18, 0.52), foot_len=(0.40, 1.10),
               foot_lvl=(-0.09, 0.10), joint=(0.009, 0.018), front=(0.005, 0.034), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
               pillow=(0.003, 0.012), tilt=0.008, rot=0.016, p_double=0.07, p_long=0.04, back=0.09, bed_amp=0.03)
    # engaged in the wing's N and W walls (bonded with toothing stones), clipped behind the S wall face
    round_stone_wall(FR.prefix + "_turret", coll, FR.TUR_C, tur_r, -0.10, FR.TUR_Z_TOP, seed, cfg, eff_radius_fn=tur_reff,
                     excl_fn=tooth_excl_tur, cull_fn=lambda P: turret_cull(P, wing_margin=0.04),
                     extra_fn=lambda acc: build_tooth_stones(acc, np.random.default_rng(seed + 203)),
                     mortar_cull_fn=lambda C: turret_cull(C, wing_margin=0.06), relief=FR.min_relief)
    build_cushion(coll, rng)
    # board drum with sill & head rings
    accd = Acc(FR.prefix + "_turret_drum")
    z0, z1 = 6.60, 7.02
    th = rng.uniform(0, 0.1)
    TS = FR.TUR_SCALE
    rD = 1.15 * TS
    bw = SIZE_TABLE["board"]["width"] if FR.units == "kit" else (0.14, 0.22)
    while th < 2 * math.pi - 0.05:
        wd = rng.uniform(*bw)
        dth = wd / rD
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0])
        o = np.array([FR.TUR_C[0], FR.TUR_C[1], 0]) + n3 * rD + np.array([0, 0, z0 - 0.06 + rng.uniform(-0.02, 0.01)])
        ask = rng.normal(0, 0.004)
        ex = np.array([0, 0, 1.0]) + t3 * ask
        obox(accd, o[None], ex / np.linalg.norm(ex), t3, n3, z1 - z0 + 0.08, wd - 0.012, 0.028, 0.006,
             "M_timber_weathered", nx=4, ny=4, nz=3, skip_back=True)
        th += dth
    if drum_backing:
        # kit 1.3.0 (keep r7 nice-to-have): a closed dark backing drum 2 cm behind the boards, so the 1-1.5 cm
        # joints between them show timber, never a black void
        nb_ = 48
        a_ = np.linspace(0, 2 * np.pi, nb_, endpoint=False)
        rb_ = rD - 0.014 - 0.02
        ring = np.stack([FR.TUR_C[0] + rb_ * np.cos(a_), FR.TUR_C[1] + rb_ * np.sin(a_)], 1)
        Vb_ = np.concatenate([np.column_stack([ring, np.full(nb_, z0 - 0.07)]),
                              np.column_stack([ring, np.full(nb_, z1 + 0.01)])])
        i_ = np.arange(nb_)
        accb = Acc(FR.prefix + "_turret_drum_backing")      # its own object: a backing is never a cull target
        accb.add(Vb_, np.stack([i_, (i_ + 1) % nb_, (i_ + 1) % nb_ + nb_, i_ + nb_], 1), "M_timber_weathered")
        finalize(accb, coll)
    # sill & head rings: 8 hewn straight pieces each, butt-jointed at every facet corner, pegged
    for ri, (zz, rr_, sz) in enumerate(((z0 + 0.04, 1.08 * TS, 0.12), (z1 - 0.05, 1.08 * TS, 0.1))):
        apo_r = rr_ * math.cos(math.radians(22.5)) + 0.03
        for k in range(8):
            phi = math.radians(45 * k + 11.0 * ri)
            n3 = np.array([math.cos(phi), math.sin(phi), 0])
            t3 = np.array([-math.sin(phi), math.cos(phi), 0])
            half = apo_r * TAN22
            o = np.array([FR.TUR_C[0], FR.TUR_C[1], zz + rng.uniform(-0.006, 0.006)]) + n3 * apo_r - t3 * (half - 0.004)
            _hewn(accd, o, t3, n3, np.array([0, 0, 1.0]), 2 * half + sz * 0.45, sz, sz, rng, chamfer=0.014,
                        nf=2, st_len=0.16, adze=0.003, wave=0.003, seed=300 + k + 10 * ri, drop=(2,))
            peg(FR, o + t3 * (2 * half + sz * 0.2) + n3 * (sz / 2), n3, rad=0.01, proud=0.01)
    V = np.stack([FR.TUR_C[0] + 1.1 * TS * np.cos(np.linspace(0, 2 * np.pi, 24, endpoint=False)),
                  FR.TUR_C[1] + 1.1 * TS * np.sin(np.linspace(0, 2 * np.pi, 24, endpoint=False)), np.full(24, z1)], 1)
    accd.add(V, np.arange(24)[None, ::-1], "M_timber")
    finalize(accd, coll)
    chunky = FR.units == "kit"
    Vsh = build_cap(coll, FR.TUR_CAP, FR.prefix + "_turret_cap", rng, p_wall=1.17 * TS, z_plate=7.02, n_raft=4,
                    p_top=0.28 if chunky else 0.12, expo=0.14, W=0.32, t=0.022, lens=(0.12, 0.17), bracket_z0=6.72,
                    chunky=chunky, saddles=saddles, cap_exposure=cap_exposure, saddle_taper=saddle_taper)
    accf = Acc(FR.prefix + "_finial_turret")
    apex = float(FR.TUR_CAP.zb(0.02))
    if chunky:
        z_top = lead_hat(accf, FR.TUR_C[0], FR.TUR_C[1], apex, 0.38 * max(TS, 0.85), 0.55, cover=Vsh)
        turned_finial(accf, (FR.TUR_C[0], FR.TUR_C[1], z_top - 0.01), 0.8, 1.5, (-0.3, 1.0))
    else:
        lead_hat(accf, FR.TUR_C[0], FR.TUR_C[1], apex, 0.19 * max(TS, 0.85), 0.16)
        turned_finial(accf, (FR.TUR_C[0], FR.TUR_C[1], apex + 0.03), 0.8, 1.5, (-0.3, 1.0))
    finalize(accf, coll)



def side_turret(g, seed=1616, saddles=False, cap_exposure=None, bulb_cushion=False, drum_backing=False,
                saddle_taper=None):
    """KIT COMPONENT: the engaged side turret (see the module doc).  kit 1.3.0 options (defaults = kit 1.1.0):
    saddles / cap_exposure as oct_roof.build_cap; bulb_cushion=True crowns ~80 % of the cushion's upper stones 3-6 cm
    and rounds their outer top arris over 6-10 cm (ref1's bulbous lip); drum_backing=True closes the board drum with
    a dark backing ring."""
    build_turret(g.sub("turret"), seed=seed, saddles=saddles, cap_exposure=cap_exposure, bulb_cushion=bulb_cushion,
                 drum_backing=drum_backing, saddle_taper=saddle_taper)   # kit 1.5.0: tapered saddles
