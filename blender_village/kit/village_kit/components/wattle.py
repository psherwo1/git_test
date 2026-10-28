"""components.wattle -- woven wattle: stakes + rods (weave_panel), twisted-rope framing panels (rope_panel).

Rods / stakes are open-backed tubes (only the outward arc is modelled: producer note 6); a panel can be told
which parts are buried in a daub coat (`hide`) and the stone tops it is bedded on (`floor`).
pathf(s) -> (xy, outward normal) describes the panel line (arc_path for a round wall, line_path for a straight one).
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import _runs, grid_quads, n2, nrm, open_tube, smoothstep


ROD_ARC = np.radians(np.array([-108.0, -65.0, -22.0, 22.0, 65.0, 108.0]))   # open-backed front shell


STAKE_ARC = np.radians(np.array([-105.0, -52.0, 0.0, 52.0, 105.0]))


def arc_path(r):
    def f(s):
        a = np.asarray(s, float) / r
        pt = np.stack([np.sin(a) * r, -np.cos(a) * r], -1)
        nn = np.stack([np.sin(a), -np.cos(a)], -1)
        return pt, nn
    return f


def line_path(p0, p1, nout):
    p0 = np.asarray(p0, float)
    d = nrm(np.asarray(p1, float) - p0)
    nout = np.asarray(nout, float)

    def f(s):
        s = np.asarray(s, float)
        pt = p0 + s[..., None] * d
        return pt, np.broadcast_to(nout, pt.shape)
    return f


def _hermite_F(t, tau):
    """0->1 weave transition between two stakes: 30 % of the swing within tau of each stake (tight
    wrap round the stake, zero slope at the stake), 40 % over the straight middle run."""
    t = np.asarray(t, float)
    tau = np.asarray(tau, float)
    mslope = 0.4 * tau / (0.3 * (1 - 2 * tau))

    def h(u):
        return (mslope - 2) * u ** 3 + (3 - mslope) * u ** 2
    a = 0.3 * h(np.clip(t / tau, 0, 1))
    b = 0.3 + 0.4 * np.clip((t - tau) / (1 - 2 * tau), 0, 1)
    c = 1 - 0.3 * h(np.clip((1 - t) / tau, 0, 1))
    return np.where(t < tau, a, np.where(t > 1 - tau, c, b))


def weave_panel(g, rods, stakes_acc, pathf, s0, s1, z0, z1, seed, hide=None, n_stakes=None, stake_bottom=None,
                slant=0.0, rod_r=(0.014, 0.019), gap=(0.002, 0.009), stake_r=(0.014, 0.018), trim=(0.0, 0.0),
                junctions=True, lean=1.5, stake_sp=0.40, stake_back=0.022, junction_p=0.22, floor=None,
                knots=1.0):
    """woven panel between s0 and s1 (post / jamb centres; rods end `trim` inside them).
    Spec amendment r2: thin stakes (dia 3-4 cm) ~0.38-0.50 m apart, jittered +-4 cm and leaning
    +-1.5 deg, mostly hidden behind the rods; rods dia 2.5-3.8 cm with 0.5-2.5 cm dark gaps between
    rows; every rod wraps its stakes with a clearance of 3-5 mm (offset = stake_r + rod_r + gap, 60 %
    of the swing within +-6 cm of the stake) so no rod intersects a stake; per-rod drift +-1 dia at
    0.5-1 m wavelength; rods tapered butt->tip 1.0->0.55; ~15 % paired / tripled rows; knots, kinks.
    Joints (r4): only `junction_p` of rows, always AT a stake the row passes behind, both ends hidden
    there, never at the same stake in consecutive rows; <= 10 % of tips flicked 1-3 cm.
    floor(s): optional stone-top height -- the weave is bedded onto it (nothing modelled below).
    knots: scale of the sub-mm knot bumps / section wobble (0 under producer note 11; the side-shoot kinks of
    the rod path, which are its shape, stay)."""
    rng = np.random.RandomState(seed)
    L = s1 - s0
    if floor is not None:
        # the weave is bedded down onto the crowned plinth stones: anything under the local stone top
        # (floor(s)) is inside the stone and is not modelled
        hide0 = hide

        def hide(s_, z_, _h=hide0):
            hb = np.asarray(z_) < floor(s_) - 0.004
            return hb if _h is None else (hb | _h(s_, z_))
    if n_stakes is None:
        n_stakes = max(1, int(round(L / stake_sp)) - 1)
    base = np.linspace(s0, s1, n_stakes + 2)[1:-1] + rng.uniform(-0.04, 0.04, n_stakes) * min(1.0, L / 0.6)
    lean_k = np.tan(np.radians(rng.uniform(-lean, lean, n_stakes)))
    sr_k = rng.uniform(*stake_r, n_stakes)
    zmid = (z0 + z1) / 2
    steep = abs(slant) > 0.1

    def stake_s(k, z):
        return base[k] + lean_k[k] * (z - zmid) + 0.005 * n2(z * 1.3, base[k] * 3.0, seed + k)

    def stake_rho(k, z):
        return -stake_back + 0.004 * n2(z * 1.7, base[k] * 2.0, seed + 50 + k)

    pt_mid, nn_mid = pathf(np.array([(s0 + s1) / 2]))
    outward3 = np.array([nn_mid[0, 0], nn_mid[0, 1], 0.0])
    # ---- stakes (open-backed; trimmed where buried in daub)
    zb = z0 - 0.07 if stake_bottom is None else stake_bottom
    for k in range(n_stakes):
        nz = 26
        zb_k = zb if floor is None else float(floor(np.array([base[k]]))[0]) - 0.03
        zz = np.linspace(zb_k, z1 + 0.03, nz)
        ss = stake_s(k, zz)
        pt, nn = pathf(ss)
        xy = pt + nn * stake_rho(k, zz)[:, None]
        path = np.c_[xy, zz]
        rad = sr_k[k] * (1 + 0.08 * n2(zz * 3.0, np.full(nz, base[k]), seed + 70 + k)) * np.linspace(1.08, 0.92, nz)
        vis = np.ones(nz, bool) if hide is None else ~hide(ss, zz)
        vis = vis | np.roll(vis, 1) | np.roll(vis, -1)
        for (a_, b_) in _runs(vis):
            if b_ - a_ < 2:
                continue
            V, F, uv = open_tube(path[a_:b_], rad[a_:b_], STAKE_ARC, outward3, (0, 0, 1), cap1=(b_ == nz))
            stakes_acc.add(V, F, "M_wattle", uv, True)
    # ---- rods (director r4 #1): every row is laid ON the one below.  The row centre line is computed
    # from the previous row's real envelope top (local tapered radius along s) plus a 0-1.2 cm gap that
    # wanders slowly along the row (rows may touch / press together, they never open up), so the dark
    # gaps stay 0.3-1.5 cm everywhere and the weave reads as a packed band.  Taper butt->tip 1.0->0.8.
    tilt = rng.uniform(-0.008, 0.008) + slant
    z_lo = z0 - (max(0.0, tilt) * L if steep else 0.0)
    z_stop = z1 - (min(0.0, tilt) * L if steep else 0.0)
    sg = np.linspace(s0, s1, max(24, int(L / 0.01) + 1))
    top_prev = z_lo + tilt * (sg - s0)
    K_ENV = 0.97                         # visible half-height of a rod section (arc ends at >= 76 deg)

    def g_smooth(v, sig_m=0.035):
        sig = max(1.0, sig_m / max(sg[1] - sg[0], 1e-4))
        kk = np.arange(-int(3 * sig), int(3 * sig) + 1)
        ker = np.exp(-0.5 * (kk / sig) ** 2)
        ker /= ker.sum()
        return np.convolve(np.pad(v, len(kk) // 2, mode="edge"), ker, mode="valid")

    def taper_f(s_, a, b, tipside):
        tpos = np.clip((s_ - a) / max(b - a, 1e-3), 0, 1)
        return 1.0 - 0.2 * (tpos if tipside > 0 else 1 - tpos)

    row = 0
    n_rods = 0
    prev_j = None
    while True:
        u = rng.rand()
        nsub = 3 if u < 0.04 else (2 if u < 0.15 else 1)
        r_row = rng.uniform(*rod_r)
        if nsub == 1:
            subs = [(r_row, 0.0)]
        elif nsub == 2:
            rA, rB = r_row * rng.uniform(0.72, 0.85), r_row * rng.uniform(0.68, 0.82)
            subs = [(rA, -rB * 1.0), (rB, rA * 1.0)]
        else:
            rr_ = r_row * rng.uniform(0.6, 0.72, 3)
            subs = [(rr_[0], -(rr_[0] + rr_[1]) * 1.0), (rr_[1], 0.0), (rr_[2], (rr_[1] + rr_[2]) * 1.0)]
        signs_par = (row % 2)
        z_est = float(top_prev.mean()) + r_row
        # pieces (director r3 #1): one rod post to post, or -- in ~22 % of rows -- two rods joined AT a
        # stake the row passes BEHIND (both ends hidden there); <= 10 % of tips flick out 1-3 cm.
        pieces = []
        a0, a1 = s0 + trim[0], s1 - trim[1]
        jk = None
        if junctions and n_stakes >= 1 and L > 0.9 and rng.rand() < junction_p:
            cand = [k for k in range(n_stakes) if (-1.0) ** (k + 1 + signs_par) < 0 and k != prev_j]
            if cand:
                jk = int(cand[rng.randint(len(cand))])
        if jk is not None:
            sjk = float(stake_s(jk, z_est))
            dA, dB = rng.uniform(0.02, 0.05), rng.uniform(0.02, 0.05)
            flickA = rng.uniform(0.01, 0.03) if rng.rand() < 0.1 else 0.0
            pieces.append((a0, sjk + dA, ("A", sjk, dA, flickA), 1))
            pieces.append((sjk - dB, a1, ("B", sjk, dA, 0.0), 1))
            prev_j = jk
        else:
            pieces.append((a0, a1, None, 1 if rng.rand() < 0.5 else -1))
            prev_j = None
        # row envelope relative to the row centre line, on the panel grid sg
        e_lo = np.full(len(sg), np.inf)
        e_hi = np.full(len(sg), -np.inf)
        rn_row = 1 + 0.05 * n2(sg * 5, np.full(len(sg), z_est), seed + 7)
        for (a, b, jinfo, tipside) in pieces:
            inr = (sg >= a - 0.01) & (sg <= b + 0.01)
            for (rr0, dzz) in subs:
                rp = rr0 * taper_f(sg, a, b, tipside) * rn_row
                e_lo = np.where(inr, np.minimum(e_lo, dzz - K_ENV * rp), e_lo)
                e_hi = np.where(inr, np.maximum(e_hi, dzz + K_ENV * rp), e_hi)
        okm = np.isfinite(e_lo)
        e_lo = np.interp(sg, sg[okm], e_lo[okm])
        e_hi = np.interp(sg, sg[okm], e_hi[okm])
        # gap to the row below: 0-1.2 cm, wandering at 0.3-0.7 m; touching (slightly pressed) in places
        wl = rng.uniform(0.3, 0.7)
        gap_s = (rng.uniform(gap[0], gap[1]) + 0.0035 * n2(sg / wl, np.full(len(sg), seed * 0.13 + row * 1.7), 7000 + seed % 97))
        gap_s = np.clip(gap_s, -0.003, 0.012)
        if row == 0:
            gap_s = gap_s * 0 + rng.uniform(0.002, 0.008)
        centre = g_smooth(top_prev + gap_s - e_lo)
        if float((centre + e_lo).min()) > z_stop - 0.006:
            break
        top_prev = centre + e_hi
        for (a, b, jinfo, tipside) in pieces:
            junction_piece = jinfo is not None
            for si, (rr0, dzz) in enumerate(subs):
                rseed = seed * 131 + row * 7 + si * 3 + int(a * 10)
                z = float(np.interp((a + b) / 2, sg, centre)) + dzz
                # stake positions and wrap offsets at this row's height
                st = np.array([s0] + [float(stake_s(k, z)) for k in range(n_stakes)] + [s1])
                rho = np.array([0.0] + [float(stake_rho(k, z)) for k in range(n_stakes)] + [0.0])
                srk = np.concatenate([[0.02], sr_k, [0.02]])
                Ak = srk + rr0 * 1.24 + rng.uniform(0.003, 0.005, len(st))
                sgn = np.array([(-1.0) ** (k + signs_par) for k in range(len(st))])
                ok_ = np.argsort(st)
                st, rho, Ak, sgn = st[ok_], rho[ok_], Ak[ok_], sgn[ok_]
                kpos = []
                kp = a + rng.uniform(0.05, 0.4)
                while kp < b - 0.03:
                    kpos.append(kp)
                    kp += rng.uniform(0.3, 0.6)
                if z > g.ROD_SHADOW_Z:
                    dense = (st[:, None] + np.array([-0.045, 0.0, 0.045])[None, :]).ravel()
                    extra = []
                    step_ = 0.1
                else:
                    dense = (st[:, None] + np.array([-0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06])[None, :]).ravel()
                    extra = [kp_ + d for kp_ in kpos for d in (-0.01, 0.0, 0.01)]
                    step_ = 0.05
                ss = np.unique(np.concatenate([np.arange(a, b, step_), dense, extra, [a, b]]))
                ss = ss[(ss >= a) & (ss <= b)]
                keep = np.concatenate([[True], np.diff(ss) > 0.007])
                keep[-1] = True
                ss = ss[keep]
                n = len(ss)
                if n < 3:
                    continue
                # small wobble + kinks at side shoots (the rows still bear on each other)
                drift = 0.0015 * n2(ss * 4.0, np.full(n, rseed * 0.71), 7100 + seed % 89)
                for kp_ in kpos:
                    if rng.rand() < 0.55:
                        drift = drift + rng.uniform(-1, 1) * 0.005 * np.clip(1 - np.abs(ss - kp_) / 0.07, 0, 1) ** 1.5
                zz = np.interp(ss, sg, centre) + dzz + drift
                k_ = np.clip(np.searchsorted(st, ss) - 1, 0, len(st) - 2)
                D = st[k_ + 1] - st[k_]
                t = np.clip((ss - st[k_]) / np.maximum(D, 1e-3), 0, 1)
                tau = np.clip(0.06 / np.maximum(D, 1e-3), 0.05, 0.3)
                o0 = sgn[k_] * Ak[k_] + rho[k_]
                o1 = sgn[k_ + 1] * Ak[k_ + 1] + rho[k_ + 1]
                off = o0 + (o1 - o0) * _hermite_F(t, tau)
                taper = taper_f(ss, a, b, tipside)
                tip_at_end = junction_piece and jinfo[0] == "A"
                tip_at_start = junction_piece and jinfo[0] == "B"
                flick = np.zeros(n)
                if tip_at_end and jinfo[3] > 0:
                    tt_ = 1 - np.clip(np.abs(ss - b) / 0.08, 0, 1)
                    flick = jinfo[3] * tt_ ** 2
                if tip_at_start:
                    # new rod: tucked behind the old one through the overlap at the stake, then free
                    sjk_, dA_ = jinfo[1], jinfo[2]
                    w_ = 1 - smoothstep(sjk_ + dA_, sjk_ + dA_ + 0.06, ss)
                    off = off - w_ * rr0 * 2.0
                off = off + flick
                pt, nn = pathf(ss)
                path = np.c_[pt + nn * off[:, None], zz]
                knot = np.zeros(n)
                for kp_ in kpos:
                    knot += knots * 0.15 * np.exp(-((ss - kp_) / 0.011) ** 2)
                rad = rr0 * taper * (1 + knot) * np.interp(ss, sg, rn_row)
                if seed in g.ROD_STORE:
                    g.ROD_STORE[seed].append((ss.copy(), path.copy(), rad.copy()))
                kn = knots * 0.05 * n2(np.arange(n)[:, None] * 0.35 + np.zeros((1, len(ROD_ARC))),
                               np.broadcast_to(ROD_ARC * 1.7, (n, len(ROD_ARC))), rseed)
                vis = np.ones(n, bool) if hide is None else ~hide(ss, zz)
                vis &= (zz - rad) < z_stop + 0.004            # fully inside the wall plate: not modelled
                vis = vis | np.roll(vis, 1) | np.roll(vis, -1) | np.roll(vis, 2) | np.roll(vis, -2)
                close = flick > 0.002
                oval = rng.uniform(0.85, 0.94)
                # section arc (up side first, then down side, degrees from the outward horizontal): the
                # side facing the viewers is carried past the vertical; the far side stops at 76-90 deg
                proud = np.clip((off - rho.mean()) / np.maximum(Ak.mean(), 1e-3), 0, 1)
                if junction_piece:
                    proud = np.maximum(proud, 0.5)
                if z > g.ROD_SHADOW_Z:             # deep in the eave shadow (seen from below): lighter
                    up_a, dn_a = np.full(n, 78.0), 96.0 + 10.0 * proud
                elif z < 1.55:                   # below eye level: the tops are seen
                    up_a, dn_a = 98.0 + 14.0 * proud, 78.0 + 6.0 * proud
                else:                            # above eye level: the undersides are seen
                    up_a, dn_a = 78.0 + 6.0 * proud, 98.0 + 14.0 * proud
                m_arc = 4 if (z > g.ROD_SHADOW_Z and not steep) else len(ROD_ARC)
                arc_n = -np.radians(up_a)[:, None] + (np.radians(up_a + dn_a))[:, None] * np.linspace(0, 1, m_arc)[None, :]
                kn = kn[:, :m_arc]
                for (ra, rb) in _runs(vis):
                    if rb - ra < 3:
                        continue
                    V, F, uv = open_tube(path[ra:rb], rad[ra:rb], arc_n[ra:rb], outward3, (0, 0, 1), rr=1 + kn[ra:rb],
                                         close_mask=close[ra:rb], cap0=(tip_at_start and ra == 0),
                                         cap1=(tip_at_end and rb == n), oval=oval)
                    rods.add(V, F, "M_wattle", uv, True)
                    n_rods += 1
        row += 1
    return n_rods


def rope_panel(rods, stakes_acc, back_acc, pathf, W, z0, z1, seed, slant, embed=(0.03, 0.03, 0.03, 0.03),
               rod_r=(0.012, 0.015), gap=(0.002, 0.005), stake_r=(0.012, 0.014), n_stakes=2, back_gap=0.012):
    """narrow 'twisted rope' wattle panel (director r3 #2), e.g. between a door jamb and a door post.
    Diagonal rods (slope `slant` = dz/ds) packed with a 2-5 mm perpendicular gap; each rod is one
    continuous S-curve that passes alternately in front of / behind the `n_stakes` vertical stakes
    (neighbouring rods in opposite phase), so the panel reads as a braid.  Every rod starts and ends
    INSIDE the framing timber: `embed` = (into the timber at s<0, at s>W, below z0, above z1).  A thin
    daub backing sheet sits behind the weave, so nothing is see-through.
    pathf(s) -> (xy, outward normal) along the panel line, s in [0, W]."""
    rng = np.random.RandomState(seed)
    e0, e1, ez0, ez1 = embed
    pt_mid, nn_mid = pathf(np.array([W / 2]))
    outward3 = np.array([nn_mid[0, 0], nn_mid[0, 1], 0.0])
    st = W * (np.arange(n_stakes) + 1) / (n_stakes + 1) + rng.uniform(-0.006, 0.006, n_stakes)
    srk = rng.uniform(*stake_r, n_stakes)
    A = float(srk.max()) + rod_r[1] + 0.003                        # weave half-swing: rods clear the stakes
    D = float(np.mean(np.diff(st))) if n_stakes > 1 else W / 2
    zb, zt = z0 - ez0, z1 + ez1
    for k in range(n_stakes):
        zz = np.linspace(zb, zt, 24)
        pt, nn = pathf(np.full(len(zz), st[k]))
        path = np.c_[pt, zz]
        rad = srk[k] * (1 + 0.06 * n2(zz * 4.0, np.full(len(zz), st[k] * 9), seed + k))
        V, F, uv = open_tube(path, rad, STAKE_ARC, outward3, (0, 0, 1))
        stakes_acc.add(V, F, "M_wattle", uv, True)
    cos_t = 1.0 / math.sqrt(1.0 + slant * slant)
    s_lo, s_hi = -e0, W + e1
    c_min = zb - max(slant * s_lo, slant * s_hi)
    c_max = zt - min(slant * s_lo, slant * s_hi)
    c = c_min - 0.01
    r_prev = None
    i = 0
    n_r = 0
    while c < c_max + 0.01:
        r_i = rng.uniform(*rod_r)
        if r_prev is not None:
            c += (r_prev + r_i + rng.uniform(*gap)) / cos_t
        r_prev = r_i
        ss = np.unique(np.concatenate([np.linspace(s_lo, s_hi, 14), (st[:, None] + [-0.012, 0.0, 0.012]).ravel()]))
        zz = c + slant * ss + 0.002 * n2(ss * 6.0, np.full(len(ss), c * 13.0), seed + 77)
        ok = (zz >= zb) & (zz <= zt)
        if ok.sum() >= 2:
            idx = np.where(ok)[0]
            i0, i1 = idx[0], idx[-1]
            # extend the clipped run exactly to the band edges (ends buried in the rail / lintel)
            sa = ss[i0]
            sb = ss[i1]
            if i0 > 0:
                zlim0 = zb if slant > 0 else zt
                sa = ss[i0 - 1] + ((zlim0 - zz[i0 - 1]) / (zz[i0] - zz[i0 - 1])) * (ss[i0] - ss[i0 - 1])
            if i1 < len(ss) - 1:
                zlim = zt if slant > 0 else zb
                sb = ss[i1] + ((zlim - zz[i1]) / (zz[i1 + 1] - zz[i1])) * (ss[i1 + 1] - ss[i1])
            s_run = np.unique(np.concatenate([[sa], ss[i0:i1 + 1], [sb]]))
            if len(s_run) >= 3 and s_run[-1] - s_run[0] > 0.02:
                z_run = c + slant * s_run + 0.002 * n2(s_run * 6.0, np.full(len(s_run), c * 13.0), seed + 77)
                sgn = 1.0 if i % 2 == 0 else -1.0
                off = sgn * A * np.cos(np.pi * (s_run - st[0]) / D)
                pt, nn = pathf(s_run)
                path = np.c_[pt + nn * off[:, None], z_run]
                rad = r_i * (1 + 0.06 * n2(s_run * 7.0, np.full(len(s_run), c * 5.0), seed + 91))
                arc = np.radians(np.linspace(-100.0, 100.0, 6))
                V, F, uv = open_tube(path, rad, arc, outward3, (0, 0, 1), oval=0.92)
                rods.add(V, F, "M_wattle", uv, True)
                n_r += 1
        i += 1
    # daub backing behind the weave (inner face of the panel): no see-through slots
    sb_ = np.linspace(s_lo, s_hi, 5)
    zb_ = np.linspace(zb, zt, max(4, int((zt - zb) / 0.15)))
    S, Z = np.meshgrid(sb_, zb_, indexing="ij")
    pt, nn = pathf(S.ravel())
    dpt = -(A + rod_r[1] + back_gap) + 0.004 * n2(S.ravel() * 8, Z.ravel() * 8, seed + 5)
    P = np.c_[pt + nn * dpt[:, None], Z.ravel()]
    Fq = grid_quads(len(sb_), len(zb_))
    q0 = P[Fq[0]]
    if float(np.dot(np.cross(q0[1] - q0[0], q0[3] - q0[0]), outward3)) < 0:
        Fq = Fq[:, ::-1]
    back_acc.add(P, Fq, "M_daub")
    return n_r


def wattle_patch(g, name, s0, s1, z0, z1, seed, radius=None, line=None, **kw):
    """KIT COMPONENT: a free-standing woven wattle panel object <PREFIX>_<name> (rods + stakes) between arc lengths
    s0..s1 on a round wall of `radius` (default g.R_WALL), or along a straight `line` ((x0, y0), (x1, y1),
    outward normal), from z0 to z1.  Extra keywords go to weave_panel (rod_r, gap, stake_sp, floor, hide...)."""
    rods = g.acc(name, 60)
    if line is not None:
        p0, p1, nout = line
        pathf = line_path(p0, p1, nout)
        L = float(np.linalg.norm(np.asarray(p1, float) - np.asarray(p0, float)))
        s0, s1 = 0.0, L
    else:
        pathf = arc_path(radius if radius is not None else g.R_WALL)
    n = weave_panel(g, rods, rods, pathf, s0, s1, z0, z1, seed, **kw)
    return rods.build(g.coll) if n else None
