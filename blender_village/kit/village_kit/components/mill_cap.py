"""components.mill_cap -- the hipped, bell-cast, shingled mill cap with its gablet hood and windshaft (kit 1.2.0).

Public component: mill_cap(g, length, width, rise, ridge_len, yaw, seed).  Cap-local frame x' = shaft heading.
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (cap_dh, cap_h, cap_t, cap_z, capw, hood_z, to_cap_local, x_valley)  # noqa: F401
from .. import shingles
from ..tmplmesh import (D2R, HeightField, PI, T_BLK, T_BRD_OT, add_grid, blocks_world, circle_prof, euler,
                        frame_mats, lathe, log, lowfreq, member, mesh_tmpl, part_samples, rbox, rect_prof, rotm,
                        slab_along, sliver_keep, sweep, tmpl_box, unit, xform)  # noqa: F401


def kit_shingles(rng, L, W, unit="shingle"):
    """N hand-split shingles from the ONE village generator (village_kit.shingles.shingle_mesh with the 16 pooled
    SHINGLE_VARIANTS base shapes: ragged butt notches, rounded corners, cup, curl) at the SIZE_TABLE[unit] scale, in
    the cap frame: x along the slope (butt at -L/2), y up from the bed, z across.  L is the MODELLED length
    (exposure + lap; the deck is under every course, producer note 6), W the width.  No bed face, no head end.
    Returns (P (N, nv, 3), template)."""
    Ps, F, nv = [], None, 0
    small = unit == "shingle_small"
    m = len(shingles.SH_LOOP_X)
    for l_, w_ in zip(L, W):
        var = dict(shingles.SHINGLE_VARIANTS[int(rng.integers(0, len(shingles.SHINGLE_VARIANTS)))])
        if small:
            var["Tb"] = shingles.SIZE_TABLE["shingle_small"]["butt"]
            var["offs"] = var["offs"] * 0.5
            ys = l_ * np.array([0.0, 0.04, 0.11, 0.25, 0.45, 0.7, 1.0])
            th = shingles.SIZE_TABLE["shingle_small"]["head"]
        else:
            ys = np.concatenate([[0.0, 0.006, 0.018, 0.04, 0.075, 0.13], np.linspace(0.2, l_, 4)])
            th = shingles.SIZE_TABLE["shingle"]["head"]
        V, faces, _ = shingles.shingle_mesh(float(w_), float(l_), var, Th=th, ys=ys, bottom=False, head=False)
        Ps.append(np.stack([V[:, 1] - l_ / 2, V[:, 2], V[:, 0]], -1))
        F, nv = faces, len(V)
    n = nv // m
    top = (np.arange(n)[:, None] * m + np.arange(6)[None]).ravel()
    return np.array(Ps), mesh_tmpl(F, nv, top=top, fan_from=8)


def cap_member(g, part, mat, a, b, w, d, up=(0, 0, 1), **kw):
    upw = capw(g, np.asarray(up, float)[None])[0]
    return member(part, mat, capw(g, np.atleast_2d(a)), capw(g, np.atleast_2d(b)), w, d, up=upw, **kw)


def build_cap_cappings(g, P_sh, P_fr, P_ir, rng):
    """Continuous V ridge capping, lapped V hip cappings (0.6-0.9 m lengths following the bell-cast hip line),
    lead hip-end saddles where hips meet the ridge, hood ridge capping and the knob on a square plinth.
    The boards sit 5 cm above the roof surface; shingle courses under each board's footprint are dressed
    down under it (so every board bears on the shingles)."""
    TB, WL = 0.025, 0.165
    SEAT = 0.070                              # board bottom above the roof surface (chunky shingle butts ~7 cm)
    Z3 = np.array([0, 0, 1.0])
    T_SAD = 0.90

    def hip_xy(fx, sy, t):
        t = np.asarray(t, float)
        x = (g.CAP_AF - t * g.CAP_EF) if fx == 0 else (-g.CAP_AB + t * g.CAP_EB)
        return x, sy * (g.CAP_B - t * g.CAP_SB)
    gaps, devs = [], []
    bottoms = []                              # underside sample points of every capping board
    groups = []

    def v_cap(apex, eA, nA, wA, eB, nB, wB):
        """two leaves meeting at the apex line; leaf B laps over leaf A's top edge"""
        out = []
        for (e, nn, w, over) in ((eA, nA, wA, False), (eB, nB, wB, True)):
            base = apex - (e * 0.022 if over else 0) + (nn * 0.010 if over else 0)
            ww = w + (0.022 if over else 0)
            out.append(slab_along(P_fr, "M_timber_weathered", capw(g, base), capw(g, e), capw(g, nn), ww, TB))
            grp = np.array([base + e * (f * ww)[:, None] for f in np.linspace(0, 1, 14)])
            bottoms.extend(list(grp))
            groups.append(grp)
        return out

    caps_V = []
    # ---------------- hips ----------------
    for fx in (0, 1):
        Rend = g.CAP_EF if fx == 0 else g.CAP_EB
        oE = np.array([1.0 if fx == 0 else -1.0, 0, 0])
        for sy in (-1, 1):
            oS = np.array([0, float(sy), 0])

            def Hf(t):
                x, y = hip_xy(fx, sy, t)
                return np.stack([x, y, g.CAP_ZE + cap_h(g, np.asarray(t, float))], -1)
            tt_ = np.linspace(-0.035, T_SAD, 400)
            Hp = Hf(tt_)
            sacc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Hp, axis=0), axis=1))])
            Ltot = sacc[-1]
            npc = max(1, int(math.ceil(Ltot / 0.80)))
            cuts = np.linspace(0, Ltot, npc + 1)
            cuts[1:-1] += rng.uniform(-0.05, 0.05, npc - 1)
            for k in range(npc):
                s0 = cuts[k] - (0.06 if k > 0 else 0.0)
                s1 = cuts[k + 1]
                ss = np.linspace(s0, s1, 12)
                t = np.interp(ss, sacc, tt_)
                H = Hf(t)
                Tg = unit(Hf(t + 1e-3) - Hf(t - 1e-3))
                se = np.arctan(cap_dh(g, np.maximum(t, 0)) / Rend)
                sS = np.arctan(cap_dh(g, np.maximum(t, 0)) / g.CAP_SB)
                nE = np.sin(se)[:, None] * oE + np.cos(se)[:, None] * Z3
                nS = np.sin(sS)[:, None] * oS + np.cos(sS)[:, None] * Z3
                eE = unit(np.cross(nE, Tg))
                eE *= np.where((eE @ np.array([0, -sy, 0])) > 0, 1.0, -1.0)[:, None]
                eS = unit(np.cross(nS, Tg))
                eS *= np.where((eS @ -oE) > 0, 1.0, -1.0)[:, None]
                wE = np.minimum(WL, np.abs(H[:, 1]) / np.maximum(np.abs(eE[:, 1]), 1e-3) - 0.004)
                if fx == 0:     # front hips: the end-face leaf is cut to fit against the hood cheek
                    far = H + eE * wE[:, None]
                    near_hood = far[:, 0] > float(x_valley(g, g.HOOD_YW)) - 0.12
                    wh = (np.abs(H[:, 1]) - 0.452) / np.maximum(np.abs(eE[:, 1]), 1e-3)
                    wE = np.where(near_hood, np.clip(np.minimum(wE, wh), 0.03, None), wE)
                lift = np.full(len(H), SEAT)
                if k > 0:   # rides over the feathered head of the piece below (lap 6 cm, < 1 deg)
                    lift = lift + 0.010 * (1 - (ss - s0) / (s1 - s0))
                lift += lowfreq(ss, rng, 0.003)
                apex = H + Z3 * lift[:, None]
                caps_V.append(v_cap(apex, eE, nE, wE, eS, nS, np.full(len(H), WL)))
                ch = apex[-1] - apex[0]
                hh = H[-1] - H[0]
                devs.append(math.degrees(math.acos(np.clip(ch @ hh / np.linalg.norm(ch) / np.linalg.norm(hh), -1, 1))))
    # ---------------- ridge ----------------
    sg = g.CAP_TMAX * D2R
    xr = np.linspace(g.XR0 + 0.03, g.XR1 - 0.03, 12)
    H = np.stack([xr, 0 * xr, np.full(12, g.CAP_ZE + g.CAP_RISE)], 1)
    eA = np.repeat([[0, -math.cos(sg), -math.sin(sg)]], 12, 0)
    nA = np.repeat([[0, -math.sin(sg), math.cos(sg)]], 12, 0)
    eB = np.repeat([[0, math.cos(sg), -math.sin(sg)]], 12, 0)
    nB = np.repeat([[0, math.sin(sg), math.cos(sg)]], 12, 0)
    wR = np.full(12, 0.165)
    ridge_apex = H + Z3 * (SEAT + lowfreq(xr, rng, 0.003))[:, None]
    caps_V.append(v_cap(ridge_apex, eA, nA, wR, eB, nB, wR))
    # ---------------- hood ridge ----------------
    sl = math.atan2(g.HOOD_ZR - g.HOOD_ZE, g.HOOD_YW + 0.03)
    xh = np.linspace(float(x_valley(g, 0.0)) + 0.03, g.HOOD_XF + 0.05, 8)
    H = np.stack([xh, 0 * xh, np.full(8, g.HOOD_ZR)], 1)
    eA = np.repeat([[0, -math.cos(sl), -math.sin(sl)]], 8, 0)
    nA = np.repeat([[0, -math.sin(sl), math.cos(sl)]], 8, 0)
    eB = np.repeat([[0, math.cos(sl), -math.sin(sl)]], 8, 0)
    nB = np.repeat([[0, math.sin(sl), math.cos(sl)]], 8, 0)
    wH = np.full(8, 0.15)
    caps_V.append(v_cap(H + Z3 * SEAT, eA, nA, wH, eB, nB, wH))
    # ---- dress the shingle courses down under the boards: every shingle vertex under a board's footprint
    # (+1 cm) is pressed to 3 mm below that board's underside -> the cappings bear on the shingles ----
    B = np.concatenate(bottoms)                 # cap-local already
    cb = 0.01
    bx0, by0 = B[:, 0].min() - 0.05, B[:, 1].min() - 0.05
    BF = np.full((int((B[:, 0].max() + 0.05 - bx0) / cb) + 1, int((B[:, 1].max() + 0.05 - by0) / cb) + 1), np.inf)
    np.minimum.at(BF, (((B[:, 0] - bx0) / cb).astype(int), ((B[:, 1] - by0) / cb).astype(int)), B[:, 2])
    for _ in range(2):                         # close sampling holes + 1 cm margin
        G2 = BF.copy()
        G2[1:] = np.minimum(G2[1:], BF[:-1])
        G2[:-1] = np.minimum(G2[:-1], BF[1:])
        G2[:, 1:] = np.minimum(G2[:, 1:], BF[:, :-1])
        G2[:, :-1] = np.minimum(G2[:, :-1], BF[:, 1:])
        BF = G2

    def bf(x, y):
        i = ((x - bx0) / cb).astype(int)
        j = ((y - by0) / cb).astype(int)
        ok = (i >= 0) & (i < BF.shape[0]) & (j >= 0) & (j < BF.shape[1])
        out = np.full(len(x), np.inf)
        out[ok] = BF[i[ok], j[ok]]
        return out

    def press(Vw):
        Vl = to_cap_local(g, Vw)
        Vw = Vw.copy()
        Vw[:, 2] = np.minimum(Vw[:, 2], bf(Vl[:, 0], Vl[:, 1]) - 0.003)
        return Vw
    P_sh.V = [press(V) for V in P_sh.V]

    def not_covered(Vi):
        Vl = to_cap_local(g, Vi.reshape(-1, 3)).reshape(Vi.shape)
        b = bf(Vl[..., 0].ravel(), Vl[..., 1].ravel()).reshape(Vi.shape[:2])
        under_board = np.isfinite(b).all(1)
        # ... or under a lead hip-end saddle (t >= 0.86 within 0.10 m of the ridge ends)
        tq = cap_t(g, Vl[..., 0], Vl[..., 1])
        sad = (tq >= 0.865) & ((Vl[..., 0] >= g.XR1 - 0.10) | (Vl[..., 0] <= g.XR0 + 0.10))
        return ~(under_board | sad.all(1))
    ncull = P_sh.filter_instances(not_covered)
    log("cap shingles wholly under the cappings (never visible): %d culled" % ncull)
    HF = HeightField(to_cap_local(g, part_samples(P_sh, 0.02)))
    st_gap = []
    for grp in groups:                         # per station: smallest gap across the board's width
        gg = grp[1:-1, :, 2] - HF(grp[1:-1, :, 0].ravel(), grp[1:-1, :, 1].ravel(), r=0).reshape(grp[1:-1, :, 2].shape)
        gg = np.where(np.abs(gg) < 1.0, gg, np.nan)
        st_gap.extend(list(np.nanmin(gg, 0)))
    g_ = np.array(st_gap)
    g_ = g_[np.isfinite(g_)]
    log("CAP cappings: %d hip pieces (%.2f-%.2f m), max deviation from hip line %.2f deg; bearing gap per "
        "station (board underside to highest shingle under it): median %.3f, 90%% %.3f m, 1%% %.3f" % (len(devs), np.diff(cuts).min(), np.diff(cuts).max(),
                                                             max(devs), np.median(g_), np.percentile(g_, 90), np.percentile(g_, 1)))
    # ---------------- lead hip-end saddles over the ridge ends ----------------
    apex_z = {}
    for fx in (0, 1):
        Rend = g.CAP_EF if fx == 0 else g.CAP_EB
        xin = (g.XR1 - 0.11) if fx == 0 else (g.XR0 + 0.11)
        rows = []
        for t in np.linspace(0.85, 1.0, 9):
            xh_ = (g.CAP_AF - t * g.CAP_EF) if fx == 0 else (-g.CAP_AB + t * g.CAP_EB)
            yh = g.CAP_B - t * g.CAP_SB
            pts = np.array([[xin, yh], [xh_, yh], [xh_, -yh], [xin, -yh]])
            seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
            acc = np.concatenate([[0], np.cumsum(seg)])
            u = np.linspace(0, acc[-1], 31)
            xy = np.stack([np.interp(u, acc, pts[:, 0]), np.interp(u, acc, pts[:, 1])], 1)
            z = np.maximum(HF(xy[:, 0], xy[:, 1], r=2), cap_z(g, xy[:, 0], xy[:, 1]) + 0.03)
            z = np.convolve(np.pad(z, 2, mode="edge"), np.ones(5) / 5, mode="valid")
            z = np.maximum(z, HF(xy[:, 0], xy[:, 1], r=1)) + 0.004
            rows.append(np.stack([xy[:, 0], xy[:, 1], z], 1))
        G = np.array(rows)
        apex_z[fx] = float(G[-1, :, 2].max())
        Gb = G - np.array([0, 0, 0.004])
        fl = fx == 1
        add_grid(P_ir, "M_lead", capw(g, G), flip=not fl)
        # (the lead underside lies on the shingles and is never seen: not modelled)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[0], G[0]], 0)), flip=fl)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[:, 0], G[:, 0]], 1)), flip=not fl)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[:, -1], G[:, -1]], 1)), flip=fl)
    # ---------------- lead aprons beside the hood cheeks (main front face, cheek -> hip capping) -----------
    x_up = float(x_valley(g, g.HOOD_YW)) - 0.14
    for sy in (-1, 1):
        xs_ = np.linspace(x_up, g.HOOD_XF + 0.10, 16)
        rows = []
        for x in xs_:
            t_h = (g.CAP_AF - x) / g.CAP_EF
            y_hip = g.CAP_B - t_h * g.CAP_SB
            ys_ = np.linspace(0.437, max(y_hip - 0.03, 0.47), 8)
            zsurf = cap_z(g, np.full(8, x), ys_)
            ramp = np.clip((x - x_up) / 0.10, 0, 1)
            z = zsurf + 0.012 + (SEAT - 0.006 - 0.012) * ramp
            if x > g.HOOD_XF - 0.03:      # dressed over the eave course below the hood front
                z = np.maximum(z, HF(np.full(8, x), sy * ys_, r=1) + 0.004)
            rows.append(np.stack([np.full(8, x), sy * ys_, z], 1))
        G = np.array(rows)
        Gb = G - np.array([0, 0, 0.004])
        fl = sy < 0
        add_grid(P_ir, "M_lead", capw(g, G), flip=fl)
        # (the lead underside lies on the shingles and is never seen: not modelled)
        for edge in (G[0], G[-1]):
            pass
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[0], G[0]], 0)), flip=not fl)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[-1], G[-1]], 0)), flip=fl)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[:, 0], G[:, 0]], 1)), flip=fl)
        add_grid(P_ir, "M_lead", capw(g, np.stack([Gb[:, -1], G[:, -1]], 1)), flip=not fl)
    # ---------------- knob on a square plinth at the rear ridge end ----------------
    zp = apex_z[1] - 0.03
    blocks_world(P_fr, "M_timber", capw(g, np.array([[g.XR0 + 0.02, 0.0, zp + 0.04]])),
                 frame_mats(capw(g, np.array([[1.0, 0, 0]])), capw(g, np.array([[0, 1.0, 0]])), np.array([[0, 0, 1.0]])),
                 [[0.075, 0.075, 0.04]], c=0.008, T=T_BLK)
    prof = np.array([(0.0, 0.0), (0.06, 0.0), (0.062, 0.015), (0.045, 0.035), (0.04, 0.055), (0.065, 0.10),
                     (0.067, 0.13), (0.047, 0.18), (0.02, 0.225), (0.0, 0.24)])
    P, T = lathe(prof[None], 16, open_base=True)
    P = xform(P, euler([0.8 * D2R], [-1.2 * D2R], [0.0]), capw(g, np.array([[g.XR0 + 0.02, 0.0, zp + 0.08]])))
    P_fr.add(P, T, mat="M_timber", smooth="all")


def build_cap(g, parts):
    P_sh, P_fr, P_ir = parts["cap_shingles"], parts["cap_frame"], parts["cap_iron"]
    rng = g.RNG("cap")
    log("cap: side max pitch %.1f deg (bell-cast to 25), end faces %.1f deg; ridge %.2f m long at z %.2f; "
        "valley x %.2f..%.2f" % (g.CAP_TMAX, math.atan(math.tan(g.CAP_TMAX * D2R) * g.CAP_SB / g.CAP_EF) / D2R, g.RIDGE_L,
                                 g.CAP_ZE + g.CAP_RISE, g.VAL_X[0], g.VAL_X[-1]))
    deck_under = lambda x, y: cap_z(g, x, y) - 0.047
    # ---- frame: sheers + cross beams carried on four truck wheels ----
    ZW = g.ZCT + 0.10                    # wheel axle (wheel dia 0.20 rolls on the curb top)
    ZSH = g.ZCT + 0.30                   # sheer centre (0.20 deep: bottom rests on the wheel tops)
    YS = 0.78
    # sheers: ends project ~11 cm past the valance face through notched gaps, splayed (chamfered) ends with an
    # end check (a split running in from the end grain and along the top for ~0.3 m)
    T_SHR = tmpl_box(9, 7, 5)
    SH_X = (-0.995, 0.972)
    for s, (x0, x1) in [(s_, xr_) for s_ in (-1, 1) for xr_ in
                        ((SH_X[0] + rng.uniform(-0.01, 0.01), SH_X[0] + 0.40), (SH_X[1] - 0.40, SH_X[1] + rng.uniform(-0.01, 0.01)))]:
        # only the ends of the sheers show (outside the valance): each end is modelled as a 0.4 m stub
        L = x1 - x0
        h = np.array([[L / 2, 0.08, 0.10]])
        P = rbox(T_SHR, h, np.array([[0.02, 0.02, 0.02]]))
        yl = T_SHR["idx"][:, 1]
        P[:, yl == 2, 1] = -0.005           # two edge loops 1 cm apart along the centre line (the check's lips)
        P[:, yl == 4, 1] = 0.005
        ux = P[:, :, 0] / h[0, 0]
        uz = P[:, :, 2] / h[0, 2]
        uy = P[:, :, 1] / h[0, 1]
        endz = np.abs(ux) > 1 - 0.021 / h[0, 0]
        # splayed end: the soffit is cut back 7 cm (sloping end face)
        P[:, :, 0] -= np.sign(ux) * endz * 0.07 * (1 - uz) / 2
        # end check: a split in the end grain from the pith to the top arris, and a short check on the top face
        mid = np.abs(uy) < 0.01
        P[:, :, 0] -= np.sign(ux) * (endz & mid) * (0.012 + 0.03 * np.clip(uz + 0.3, 0, 1))
        top_near = (uz > 0.99) & mid & (np.abs(ux) > 0.6)
        P[:, :, 2] -= top_near * 0.012 * np.clip((np.abs(ux) - 0.6) / 0.4, 0, 1)
        P[:, :, 1] += rng.uniform(-0.004, 0.004) * (1 - ux ** 2)
        Pc = np.stack([(x0 + x1) / 2 + P[:, :, 0], s * YS + P[:, :, 1], ZSH + P[:, :, 2]], -1)
        P_fr.add(capw(g, Pc), T_SHR, Pl=P, mat="M_timber", smooth="bevel")
    # (cross beams, truck wheels and the breast beam sit wholly inside the valance box: not modelled)
    # ---- deck shell (sarking boards with real thickness) ----
    nx, ny = 46, 40
    xs = np.linspace(-g.CAP_AB - 0.03, g.CAP_AF + 0.03, nx)
    ys = np.linspace(-g.CAP_B - 0.03, g.CAP_B + 0.03, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zt = cap_z(g, X, Y) - 0.012
    # the deck's top skin is entirely under shingles / lead and its soffit inside the valance box is enclosed:
    # only the soffit outside the valance (seen from below) and the edge band are modelled
    Rpl = np.hypot(X, Y)
    rmax = np.maximum(np.maximum(Rpl[:-1, :-1], Rpl[1:, :-1]), np.maximum(Rpl[:-1, 1:], Rpl[1:, 1:]))
    add_grid(P_fr, "M_timber", capw(g, np.stack([X, Y, Zt - 0.035], 2)), keep=rmax > g.SKIRT_R - 0.04, flip=True)
    per = np.concatenate([np.stack([xs, np.full(nx, ys[0])], 1), np.stack([np.full(ny, xs[-1]), ys], 1)[1:],
                          np.stack([xs[::-1], np.full(nx, ys[-1])], 1)[1:], np.stack([np.full(ny, xs[0]), ys[::-1]], 1)[1:]])
    zt = cap_z(g, per[:, 0], per[:, 1]) - 0.012
    band = np.stack([np.stack([per[:, 0], per[:, 1], zt - 0.035], 1), np.stack([per[:, 0], per[:, 1], zt], 1)], 1)
    add_grid(P_fr, "M_timber", capw(g, band), flip=False)
    # sarking deck (round 4): a continuous board deck under every cap face, so a missing / slipped shingle or a
    # gap between courses shows boards, never sky or a void. Each face is a ruled strip between its hip lines
    # (the bell-cast profile varies only up the slope); boards 15-25 cm wide, 4 mm V joints between them.
    for fi in range(4):
        Rf = (g.CAP_EF, g.CAP_EB, g.CAP_SB, g.CAP_SB)[fi]
        t0 = -0.03 / Rf
        slope_len = float(np.sum(np.hypot(np.diff(g.CAP_DS), np.diff(g.CAP_HS)))) * Rf / g.CAP_SB
        ts = [t0]
        while ts[-1] < 1.0:
            ts.append(ts[-1] + rng.uniform(0.15, 0.25) / slope_len)
        ts[-1] = 1.0
        rows_t, rows_d = [], []
        for k in range(len(ts) - 1):
            a_, b_ = ts[k], ts[k + 1]
            e = 0.004 / slope_len
            for tq, dq in ((a_ + e, 0.0), (b_ - e, 0.0), (b_, -0.004)):
                rows_t.append(tq)
                rows_d.append(dq)
        rows_t = np.array([t0] + rows_t[:-1])
        rows_d = np.array([0.0] + rows_d[:-1])
        hw = g.CAP_B - rows_t * g.CAP_SB + 0.0
        if fi == 0:
            x = g.CAP_AF - rows_t * g.CAP_EF
            G = np.stack([np.stack([x, -hw, 0 * x], 1), np.stack([x, hw, 0 * x], 1)], 1)
        elif fi == 1:
            x = -g.CAP_AB + rows_t * g.CAP_EB
            G = np.stack([np.stack([x, hw, 0 * x], 1), np.stack([x, -hw, 0 * x], 1)], 1)
        else:
            sy = 1.0 if fi == 2 else -1.0
            y = sy * (g.CAP_B - rows_t * g.CAP_SB)
            xa = -g.CAP_AB + rows_t * g.CAP_EB
            xb = g.CAP_AF - rows_t * g.CAP_EF
            G = np.stack([np.stack([xa, y, 0 * y], 1), np.stack([xb, y, 0 * y], 1)], 1)
            if fi == 3:
                G = G[:, ::-1]
        G[..., 2] = g.CAP_ZE + cap_h(g, rows_t)[:, None] - 0.016 + rows_d[:, None]
        nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
        add_grid(P_fr, "M_timber", capw(g, G), flip=bool(nrm_[2] < 0), smooth="none")
    # rafters under the deck: 4 hips + commons
    rafters = []
    for sy in (-1, 1):
        rafters.append(((g.CAP_AF - 0.05, sy * (g.CAP_B - 0.05)), (g.XR1, 0.0)))
        rafters.append(((-g.CAP_AB + 0.05, sy * (g.CAP_B - 0.05)), (g.XR0, 0.0)))
        for xx in (g.XR0, g.CAP_XC, g.XR1):
            rafters.append(((xx, sy * (g.CAP_B - 0.05)), (xx, sy * 0.05)))
    rafters.append(((g.CAP_AF - 0.05, 0.0), (g.XR1 + 0.05, 0.0)))
    # (no rear centre rafter: the tail boom rails run out under the rear eave there)
    for (x0, y0), (x1, y1) in rafters:
        # rafter tails only: the run inside the valance box is enclosed
        tq = np.linspace(0, 1, 200)
        rq = np.hypot(x0 + (x1 - x0) * tq, y0 + (y1 - y0) * tq)
        if rq[0] < g.SKIRT_R:
            continue
        t_end = tq[np.argmax(rq < g.SKIRT_R - 0.05)] if (rq < g.SKIRT_R - 0.05).any() else 1.0
        n = 5
        t = np.linspace(0, t_end, n)
        xx = x0 + (x1 - x0) * t
        yy = y0 + (y1 - y0) * t
        zz = deck_under(xx, yy) - 0.05
        P, T = sweep(capw(g, np.stack([xx, yy, zz], 1))[None], rect_prof(0.07, 0.1, 0.012), up=(0, 0, 1))
        mq = (np.arange(len(T["quads"])) % 8) != 2          # top face bears on the deck soffit: not modelled
        T = dict(T, quads=T["quads"][mq], qflat=T["qflat"][mq])
        P_fr.add(P, T, mat="M_timber", smooth="bevel")
    # ---- valance: vertical board skirt hanging outside the curb (covers the wheel gap). The boards are notched
    # around the four sheer ends with 1 cm clearance: the ring leaves a gap where each sheer passes, filled by a
    # short board below the sheer and one above it where there is room. ----
    rr = g.SKIRT_R + 0.0125
    r_in, r_out = g.SKIRT_R, g.SKIRT_R + 0.025
    blocks = []
    for sy_ in (-1, 1):
        for xe in SH_X:
            angs = []
            for rq in (r_in - 0.003, r_out + 0.003):
                for yq in (sy_ * (YS - 0.08 - 0.01), sy_ * (YS + 0.08 + 0.01)):
                    xq = math.copysign(math.sqrt(rq ** 2 - yq ** 2), xe)
                    angs.append(math.atan2(yq, xq) % (2 * PI))
            blocks.append((min(angs), max(angs), ZSH - 0.11, ZSH + 0.11))
    angs = []
    for rq in (r_in - 0.003, r_out + 0.003):
        for yq in (-(g.TB_YC + g.TB_RW / 2 + 0.01), g.TB_YC + g.TB_RW / 2 + 0.01):
            angs.append(math.atan2(yq, -math.sqrt(rq ** 2 - yq ** 2)) % (2 * PI))
    blocks.append((min(angs), max(angs), g.TB_Z - g.TB_RH / 2 - 0.01, g.TB_Z + g.TB_RH / 2 + 0.01))   # tail boom notch
    blocks.sort()
    arcs = []                                  # (a0, a1, kind) kind 0 = free, 1 = sheer gap
    for i, (b0, b1, zlo, zhi) in enumerate(blocks):
        nb0 = blocks[(i + 1) % len(blocks)][0] + (2 * PI if i == len(blocks) - 1 else 0)
        arcs.append((b0, b1, (zlo, zhi)))
        arcs.append((b1, nb0, 0))
    gap = 0.008
    vb = []                                    # (angle centre, arc width, z bottom, z top)
    for a0, a1, kind in arcs:
        S_ = (a1 - a0) * rr
        if kind != 0:
            zlo, zhi = kind
            ac = (a0 + a1) / 2
            cx, cy = rr * math.cos(ac), rr * math.sin(ac)
            zb = g.ZCT - 0.065 + rng.uniform(-0.01, 0.01)
            if zlo - zb > 0.03:
                vb.append((ac, S_ + 0.02, zb, zlo))     # under-board spans the notch (+1 cm laps)
            zt = float(deck_under(np.array(cx), np.array(cy))) + 0.01
            if zt - zhi > 0.03:
                vb.append((ac, S_ + 0.02, zhi, zt))
            continue
        ws = []
        while sum(ws) < S_ - 0.01:
            ws.append(rng.uniform(0.13, 0.2))
        ws = np.array(ws) * (S_ / sum(ws))
        edges = a0 + np.concatenate([[0], np.cumsum(ws)]) / rr
        for j in range(len(ws)):
            ac = (edges[j] + edges[j + 1]) / 2
            w = ws[j] - gap - (0.02 if j in (0, len(ws) - 1) else 0.0)      # 1 cm clearance at the sheers
            if j == 0:
                ac += 0.01 / rr
            if j == len(ws) - 1:
                ac -= 0.01 / rr
            cx, cy = rr * math.cos(ac), rr * math.sin(ac)
            zt = float(deck_under(np.array(cx), np.array(cy))) + 0.01
            vb.append((ac, w, g.ZCT - 0.065 + rng.uniform(-0.012, 0.012), zt))
    vb = np.array(vb)
    a_c, ws, zbot, ztop = vb[:, 0], vb[:, 1], vb[:, 2], vb[:, 3]
    N = len(vb)
    cx, cy = rr * np.cos(a_c), rr * np.sin(a_c)
    Lz = ztop - zbot
    h = np.stack([Lz / 2, np.full(N, 0.0125), ws / 2], 1)
    P = rbox(T_BRD_OT, h, np.stack([np.full(N, 0.006), np.full(N, 0.005), np.minimum(0.006, ws / 5)], 1))
    P[:, :, 1] += rng.uniform(-0.003, 0.003, N)[:, None]
    radv = np.stack([np.cos(a_c), np.sin(a_c), np.zeros(N)], 1)
    tanv = np.stack([-np.sin(a_c), np.cos(a_c), np.zeros(N)], 1)
    zv = np.repeat([[0, 0, 1.0]], N, 0)
    Rk = frame_mats(zv, radv, np.cross(zv, radv))
    sk = np.clip(rng.normal(0, 0.3, N), -0.5, 0.5) * D2R * (Lz > 0.2)
    Rk = Rk @ rotm([0, 1, 0], sk)
    ctr = np.stack([cx, cy, (ztop + zbot) / 2], 1)
    Wk = xform(P, Rk, ctr)
    P_fr.add(capw(g, Wk), T_BRD_OT, Pl=P, mat="M_timber_weathered", smooth="bevel")
    log("valance boards %d (4 sheer notches)" % N)
    # nail heads along the top (into the eave plate)
    sel = Lz > 0.15
    nl = np.stack([cx, cy, ztop - 0.06], 1)[sel]
    prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
    Pn, Tn = lathe(np.repeat(prof[None], int(sel.sum()), 0), 6, open_base=True)
    Rn = frame_mats(tanv[sel], zv[sel], radv[sel])
    P_ir.add(capw(g, xform(Pn, Rn, nl + radv[sel] * 0.0125)), Tn, mat="M_iron", smooth="all")
    # ---- shingles (4 hipped faces) ----
    faces = [  # (o, e, run)
        (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), g.CAP_EF),
        (np.array([-1.0, 0, 0]), np.array([0, -1.0, 0]), g.CAP_EB),
        (np.array([0, 1.0, 0]), np.array([-1.0, 0, 0]), g.CAP_SB),
        (np.array([0, -1.0, 0]), np.array([1.0, 0, 0]), g.CAP_SB)]

    def face_point(fi, t, s):
        """cap-local (x, y) of normalised height t and lateral s on face fi."""
        o, e, R = faces[fi]
        if fi == 0:
            return g.CAP_AF - t * R, s
        if fi == 1:
            return -g.CAP_AB + t * R, -s
        if fi == 2:
            return g.CAP_XC - s, g.CAP_B - t * R
        return g.CAP_XC + s, -g.CAP_B + t * R

    def half_span(fi, t):
        if fi < 2:
            return g.CAP_B - t * g.CAP_SB
        return (g.CAP_AF + g.CAP_AB) / 2 - t * g.CAP_EF

    SH = shingles.SIZE_TABLE["shingle"]              # the village's chunky unit (ensemble review: one scale)
    t = -0.03 / g.CAP_SB
    courses = []
    while t < 1 - 0.045:
        courses.append(t)
        sig = math.atan(float(cap_dh(g, t + 0.05)) / g.CAP_SB)
        t += rng.uniform(*SH["exposure"]) * math.cos(sig) / g.CAP_SB
    courses = [courses[0]] + courses
    nsh = 0
    nsliver = 0
    for ci, tb in enumerate(courses):
        starter = ci == 0
        for fi, (o, e, R) in enumerate(faces):
            hl = half_span(fi, max(tb, 0)) + 0.10
            if hl <= 0.03:
                continue
            wl = []
            tot = 0
            while tot < 2 * hl:
                w = SH["target_w"] * rng.uniform(*SH["w_jitter"])         # +-24 % widths (director r6 #6)
                wl.append(w)
                tot += w + rng.uniform(*SH["gap"])
            wl = np.array(wl) * 2 * hl / tot
            lc = -hl + np.cumsum(wl) + (np.arange(len(wl)) + 0.5) * (2 * hl - wl.sum()) / len(wl) - wl / 2
            # joints break course to course by about half a unit (never aligned over 3 courses)
            lc += (ci % 2) * 0.5 * float(wl.mean()) + rng.uniform(-0.05, 0.05) + (0.12 if starter else 0.0)
            N = len(wl)
            # exposure + 6-8 cm lap only: the rest of each covered shingle is not modelled (the deck is under it)
            expo = (courses[min(ci + 1, len(courses) - 1)] - tb) * g.CAP_SB if ci + 1 < len(courses) else 0.34
            L = np.clip(expo + rng.uniform(0.06, 0.08, N), 0.30, 0.50) * (0.8 if starter else 1.0)
            tbb = tb + (rng.uniform(-0.006, 0.006, N) + (0.004 if starter else 0.0)) / R
            sig = np.arctan(cap_dh(g, tbb + L * 0.35 / R) / R)
            tc = tbb + L / 2 * np.cos(sig) / R
            xc, yc = face_point(fi, tc, lc)
            if fi == 0:
                under = (np.abs(yc) < g.HOOD_YW + 0.03) & (xc > x_valley(g, yc) - 0.06)
                # strip beside the hood cheek (down to the hood front): dressed in a lead apron instead
                under |= (np.abs(yc) > g.HOOD_YW - 0.06) & (xc > float(x_valley(g, g.HOOD_YW)) - 0.10) & \
                    (xc < g.HOOD_XF - 0.02)
            else:
                under = np.zeros(N, bool)
            # shingles whose centre lies past a hip line are not laid (no squashed slivers); the hip board
            # covers the cut edges of the rest
            if fi < 2:
                tx_c = (g.CAP_AF - xc) / g.CAP_EF if fi == 0 else (g.CAP_AB + xc) / g.CAP_EB
                under |= np.abs(yc) - wl * 0.25 > g.CAP_B - g.CAP_SB * tx_c
            else:
                ts_c = (g.CAP_B - np.abs(yc)) / g.CAP_SB
                under |= (xc + wl * 0.25 < -g.CAP_AB + g.CAP_EB * ts_c) | (xc - wl * 0.25 > g.CAP_AF - g.CAP_EF * ts_c)
            zb = g.CAP_ZE + cap_h(g, tc)
            # lift at butt / head: course 1 rides on the starter's butt, the others on the head of the course below
            ob, ot = (0.006, 0.002) if starter else ((0.042, 0.006) if ci == 1 else (0.032, 0.005))
            beta = np.arctan2(ob - ot, L) + rng.uniform(-0.01, 0.02, N)
            tt = -np.cos(sig)[:, None] * o[None] + np.sin(sig)[:, None] * np.array([0, 0, 1.0])
            nn = np.sin(sig)[:, None] * o[None] + np.cos(sig)[:, None] * np.array([0, 0, 1.0])
            ee = np.cross(tt, nn)
            P, Tsh = kit_shingles(rng, L, wl * rng.uniform(0.97, 1.03, N))
            # in-plane rotation: +-1 deg on most, +-3 deg on 20 % (director r6 #6)
            rot = np.where(rng.random(N) < 0.2, rng.uniform(2.0, 3.5, N) * rng.choice([-1, 1], N),
                           np.clip(rng.normal(0, 1.0, N), -2.0, 2.0))
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rot * D2R)
            ctr = np.stack([xc, yc, zb], 1) + nn * ((ob + ot) / 2 + rng.uniform(-0.002, 0.003, N))[:, None]
            Wl = xform(P, frame_mats(tt, nn, ee) @ Rl, ctr)
            W0 = Wl.copy()
            # clamp to the hip lines
            if fi < 2:
                tx = (g.CAP_AF - Wl[:, :, 0]) / g.CAP_EF if fi == 0 else (g.CAP_AB + Wl[:, :, 0]) / g.CAP_EB
                lim = g.CAP_B - g.CAP_SB * tx + 0.025
                Wl[:, :, 1] = np.clip(Wl[:, :, 1], -lim, lim)
            else:
                ts = (g.CAP_B - np.abs(Wl[:, :, 1])) / g.CAP_SB
                Wl[:, :, 0] = np.clip(Wl[:, :, 0], -g.CAP_AB + g.CAP_EB * ts - 0.025, g.CAP_AF - g.CAP_EF * ts + 0.025)
                # top course stops at the ridge line (under the V ridge capping), never across it
                sgn = 1.0 if fi == 2 else -1.0
                Wl[:, :, 1] = sgn * np.maximum(sgn * Wl[:, :, 1], -0.015)
            if fi == 0:
                # stop short of the valleys (exposes the lead valley); fold clamped vertices onto the face
                near = np.abs(Wl[:, :, 1]) < g.HOOD_YW + 0.05
                xlim = x_valley(g, Wl[:, :, 1]) - 0.035
                xn = np.where(near, np.minimum(Wl[:, :, 0], xlim), Wl[:, :, 0])
                Wl[:, :, 2] += cap_h(g, (g.CAP_AF - xn) / g.CAP_EF) - cap_h(g, (g.CAP_AF - Wl[:, :, 0]) / g.CAP_EF)
                Wl[:, :, 0] = xn
            Wl[:, :, 2] = np.minimum(Wl[:, :, 2], g.CAP_ZE + g.CAP_RISE + 0.03)
            # nothing projects past the eave line / hip-board ends at the eave corners (round-4 shard trim)
            Wl[:, :, 0] = np.clip(Wl[:, :, 0], -g.CAP_AB - 0.045, g.CAP_AF + 0.045)
            Wl[:, :, 1] = np.clip(Wl[:, :, 1], -g.CAP_B - 0.045, g.CAP_B + 0.045)
            keep = (~under) & (rng.random(N) > 0.015)
            kk = sliver_keep(W0, Wl, tt, ee, T=Tsh)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(g, Wl[keep]), Tsh, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
            nsh += keep.sum()
    log("cap shingles", nsh, "slivers culled", nsliver)
    # ---- hood (gablet) over the windshaft neck ----
    yv = np.linspace(0, g.HOOD_YW + 0.05, 8)
    for s in (-1, 1):
        # roof board shell from the valley line to the front verge
        u = np.linspace(0, 1, 10)
        Yv = np.repeat(yv[None], len(u), 0)
        xv0 = x_valley(g, Yv) - 0.03
        X = xv0 + (g.HOOD_XF + 0.05 - xv0) * u[:, None]
        Z = hood_z(g, Yv) - 0.01
        Gt = np.stack([X, s * Yv, Z], 2)
        Gb = np.stack([X, s * Yv, Z - 0.03], 2)
        add_grid(P_fr, "M_timber", capw(g, Gt), flip=(s > 0))
        # (the hood boarding's soffit faces the closed hood interior: not modelled)
        add_grid(P_fr, "M_timber", capw(g, np.stack([Gb[:, -1], Gt[:, -1]], 1)), flip=(s < 0))
        add_grid(P_fr, "M_timber", capw(g, np.stack([Gb[-1, :], Gt[-1, :]], 1)), flip=(s > 0))
        # shingles: courses parallel to the hood eave, stopped at the valley
        sl = math.atan2(g.HOOD_ZR - g.HOOD_ZE, g.HOOD_YW + 0.03)
        for ci, yb in enumerate(np.arange(g.HOOD_YW + 0.06, 0.02, -0.11 * math.cos(sl))):
            x_start = float(x_valley(g, yb)) - 0.1
            xl = np.arange(x_start, g.HOOD_XF + 0.02, 0.15)
            N = len(xl)
            if N == 0:
                continue
            SS = shingles.SIZE_TABLE["shingle_small"]       # the hood's documented small unit
            L = rng.uniform(*SS["length"], N)
            W = rng.uniform(*SS["width"], N)
            P, Tsh = kit_shingles(rng, L, W, unit="shingle_small")
            tt = np.array([0.0, -s * math.cos(sl), math.sin(sl)])
            nn = np.array([0.0, s * math.sin(sl), math.cos(sl)])
            ee = np.cross(tt, nn)
            yc = yb - L / 2 * math.cos(sl)
            ctr = np.stack([xl + 0.075 + (ci % 2) * 0.07, s * yc, hood_z(g, yc) + 0.02], 1)
            Rr = np.repeat(frame_mats(tt[None], nn[None], ee[None]), N, 0) @ rotm([0, 0, 1], np.full(N, -0.06))
            Wl = xform(P, Rr, ctr)
            W0h = Wl.copy()
            Wl[:, :, 0] = np.clip(Wl[:, :, 0], x_valley(g, Wl[:, :, 1]) + 0.035, g.HOOD_XF + 0.05)
            # never cross the hood ridge: clip at the ridge line and keep the vertex on its own plane
            yo_ = Wl[:, :, 1].copy()
            yn_ = s * np.maximum(s * yo_, 0.012)
            Wl[:, :, 2] += -(g.HOOD_ZR - g.HOOD_ZE) * (s * yn_ - s * yo_) / (g.HOOD_YW + 0.03)
            Wl[:, :, 1] = yn_
            keep = Wl[:, :, 0].max(1) > x_valley(g, Wl[:, :, 1]).max(1) + 0.06
            kk = sliver_keep(W0h, Wl, tt, ee, T=Tsh)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(g, Wl[keep]), Tsh, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
        # lead valley flashing: folded strip lying on both roof planes under the shingle edges
        yy = np.linspace(0.0, g.HOOD_YW + 0.03, 12)
        xv_ = x_valley(g, yy)
        rows = []
        for dx in (-0.11, -0.04, 0.0, 0.04, 0.11):
            xq = xv_ + dx
            zq = np.where(dx < 0, cap_z(g, xq, yy), hood_z(g, yy)) - 0.012
            rows.append(np.stack([xq, s * yy, zq], 1))
        G = np.stack(rows, 0)
        add_grid(P_ir, "M_lead", capw(g, G + np.array([0, 0, 0.006])), flip=(s < 0))
        # (the valley lead underside lies on the boarding and is never seen: not modelled)
        # cheek: vertical boards closing the gap between the hood eave and the falling main roof
        xa = float(x_valley(g, g.HOOD_YW))
        for xb in np.arange(xa + 0.04, g.HOOD_XF, 0.13):
            zb = float(cap_z(g, np.array(xb), np.array(g.HOOD_YW - 0.03))) - 0.04
            cap_member(g, P_fr, "M_timber_weathered", [xb, s * (g.HOOD_YW - 0.03), zb], [xb, s * (g.HOOD_YW - 0.03),
                                                                                     g.HOOD_ZE + 0.0], 0.12, 0.025,
                       up=(0, s, 0), c=0.005, rng=rng, bow=0.003)
    log("cap + hood shingles: slivers culled (< 5 cm wide after clamping)", nsliver)
    build_cap_cappings(g, P_sh, P_fr, P_ir, rng)
    # front gable boards with a hole for the shaft
    zsh = g.HUB_Z - (g.HUB_D - g.HOOD_XF) * math.tan(g.TILT)
    rh = 0.215
    for yb in np.arange(-g.HOOD_YW + 0.06, g.HOOD_YW - 0.02, 0.125):
        zb0 = float(cap_z(g, np.array(g.HOOD_XF), np.array(yb))) - 0.05
        zt = float(hood_z(g, yb)) - 0.03
        segs = [(zb0, zt)]
        if abs(yb) < rh + 0.06:
            ext = math.sqrt(max(rh ** 2 - min(abs(yb), rh) ** 2, 0)) + 0.01
            segs = [(zb0, zsh - ext), (zsh + ext, zt)]
        for z0, z1 in segs:
            if z1 - z0 > 0.04:
                cap_member(g, P_fr, "M_timber_weathered", [g.HOOD_XF, yb, z0], [g.HOOD_XF, yb, z1], 0.12, 0.025,
                           up=(1, 0, 0), c=0.005, rng=rng, bow=0.002)
    # iron neck collar plate around the hole
    a = np.linspace(0, 2 * PI, 33)[:-1]
    ring = np.stack([np.full(32, g.HOOD_XF + 0.02), (rh + 0.02) * np.cos(a), zsh + (rh + 0.02) * np.sin(a)], 1)
    P, T = sweep(capw(g, ring)[None], rect_prof(0.03, 0.07, 0.004), up=capw(g, np.array([[1.0, 0, 0]]))[0], closed=True)
    P_ir.add(P, T, mat="M_iron", smooth="bevel")
    # ---- windshaft (16-sided) with iron hoops ----
    x0, x1 = g.HOOD_XF - 0.2, g.HUB_D - 0.36 * math.cos(g.TILT)     # (the run inside the cap is enclosed)
    n = 6
    xs = np.linspace(x0, x1, n)
    zs = g.HUB_Z - (g.HUB_D - xs) * math.tan(g.TILT)
    P, T = sweep(capw(g, np.stack([xs, np.zeros(n), zs], 1))[None], circle_prof(0.19, 16), up=(0, 0, 1))
    P_ws = parts["windshaft"]
    P_ws.add(P, T, mat="M_timber", smooth="all")
    for xh in (g.HOOD_XF + 0.08, g.HOOD_XF + 0.42):
        zh = g.HUB_Z - (g.HUB_D - xh) * math.tan(g.TILT)
        pp = np.stack([np.array([xh - 0.025, xh + 0.025]), np.zeros(2), np.array([zh, zh]) + np.array([-0.0035, 0.0035])],
                      1)
        P, T = sweep(capw(g, pp)[None], circle_prof(0.2, 16), up=(0, 0, 1))
        P_ws.add(P, T, mat="M_iron", smooth="all")


def mill_cap(g, length=None, width=None, rise=None, ridge_len=None, yaw=None, seed=None):
    """Hipped shingled mill cap (kit component): footprint length (along the windshaft) x width, `rise` from the
    bell-cast eave to a short ridge of ridge_len, yawed `yaw` deg; sheers, sarking deck, valance, chunky shingle
    courses (village_kit.shingles), lapped V hip / ridge cappings, lead saddles, a gablet hood over the shaft neck
    with lead valleys, and the windshaft (<PREFIX>_cap_frame / _cap_shingles / _cap_iron / _windshaft)."""
    kw = {}
    if length is not None:
        kw["CAP_AF"], kw["CAP_AB"] = length * 0.4638, length * 0.5362
    if width is not None:
        kw["CAP_B"] = width / 2
    if rise is not None:
        kw["CAP_RISE"] = rise
    if ridge_len is not None:
        kw["RIDGE_L"] = ridge_len
    if yaw is not None:
        kw["CAP_AZ"] = yaw * D2R
    g.set(**kw)
    with g.seeded(seed):
        build_cap(g, g.parts)
