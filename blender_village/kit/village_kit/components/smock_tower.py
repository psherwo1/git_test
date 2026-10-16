"""components.smock_tower -- the octagonal boarded timber smock tower of a tower mill (kit 1.2.0).

Public component: smock_tower(g, af_bottom, af_top, z0, z1, lean_deg, seed).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (COS225, TAN225, TZ, face_axes, face_map, post_geom, tw_a)  # noqa: F401
from ..tmplmesh import (BatchAcc, D2R, PI, T_BRD_O3, T_BRD_O3B, T_BRD_O3T, T_BRD_O3TB, T_PLK, T_PLK_DB, T_PLK_NI,
    add_grid, blocks_world, frame_mats, lathe, log, member, rbox, rect_prof, rotm, sweep, unit, xform)  # noqa: F401


def build_tower(g, parts):
    P_b, P_f, P_i = parts["tower_boards"], parts["tower_frame"], parts["tower_iron"]
    rng = g.RNG("tower")
    lifts = [(float(TZ(g, 5.52)), float(TZ(g, 7.24))), (float(TZ(g, 7.20)), float(TZ(g, 9.04))), (float(TZ(g, 9.0)), float(TZ(g, 10.36)))]
    hatch = dict(k=0, l=0.28, z0=float(TZ(g, 7.68)), z1=float(TZ(g, 8.34)))
    # age: split board ends (3) and one patched board, on faces seen from the front / hero cameras
    splits = {(7, 0), (1, 0), (6, 1), (0, 0), (0, 2), (6, 0), (6, 2), (7, 2)}   # split board ends (hero faces)
    cupped = {(0, 0), (6, 1), (7, 2)}                                            # strongly cupped boards (6-10 mm)
    patch_at = (7, 1)
    nb_total = 0
    ncup_total = [0]
    patches = []
    for k in range(8):
        for li, (z0, z1) in enumerate(lifts):
            zm = (z0 + z1) / 2
            hw = (float(tw_a(g, zm)) + 0.03) * TAN225 - 0.12
            # boards across the face
            ws = []
            tot = 0
            while tot < 2 * hw:
                w = rng.uniform(0.15, 0.28)
                ws.append(w)
                tot += w + 0.011
            if tot - 2 * hw > 0.5 * ws[-1] and len(ws) > 1:
                tot -= ws.pop() + 0.011
            ws = np.array(ws) * 2 * hw / tot
            lc = -hw + np.cumsum(ws + 0.011 * 2 * hw / tot) - ws / 2 - 0.0055
            N = len(ws)
            isplit = int(rng.integers(0, N)) if (k, li) in splits else -1
            ipatch = int(rng.integers(1, N - 1)) if (k, li) == patch_at else -1
            pieces = []   # (lateral centre, width, z bottom, z top, extra skew deg)
            icup = int(rng.integers(0, N)) if (k, li) in cupped else -1
            cup_of = []
            # 1-2 staggered horizontal butt joints across the face between the rails, 1-2 cm drip gaps
            nj = int(rng.integers(1, 3))
            zj = np.sort(rng.uniform(z0 + 0.35, z1 - 0.35, nj))
            if nj == 2 and zj[1] - zj[0] < 0.3:
                zj[1] = min(zj[0] + 0.3, z1 - 0.3)
            for i in range(N):
                zb = z0 + rng.uniform(-0.03, 0.03)
                zt = z1 + rng.uniform(-0.01, 0.015)
                n0 = len(pieces)
                if k == hatch["k"] and li == 1 and abs(lc[i]) - ws[i] / 2 < hatch["l"] + 0.02:
                    pieces.append((lc[i], ws[i], zb, hatch["z0"] - 0.04, 0.0))
                    pieces.append((lc[i], ws[i], hatch["z1"] + 0.06, zt, 0.0))
                elif rng.random() < 0.7 and i != isplit:
                    zc_j = zj[i % nj] + rng.uniform(-0.04, 0.04)
                    g_ = rng.uniform(0.01, 0.02) / 2
                    pieces.append((lc[i], ws[i], zb, zc_j - g_, 0.0))
                    pieces.append((lc[i], ws[i], zc_j + g_, zt, 0.0))
                elif i == isplit:
                    # split end: the bottom 0.26 m is cracked into two halves, one sprung outward/sideways
                    zs_ = zb + 0.26
                    pieces.append((lc[i], ws[i], zs_ - 0.004, zt, 0.0))
                    hw2 = ws[i] / 2 - 0.004
                    pieces.append((lc[i] - ws[i] / 4 - 0.002, hw2, zb, zs_ + 0.01, 0.0))
                    pieces.append((lc[i] + ws[i] / 4 + 0.004, hw2, zb + 0.015, zs_ + 0.01, 2.2))
                else:
                    pieces.append((lc[i], ws[i], zb, zt, 0.0))
                cup_of.extend([i == icup] * (len(pieces) - n0))
                if i == ipatch:
                    zp = zm + rng.uniform(-0.3, 0.1)
                    patches.append((k, lc[i], ws[i] + 0.03, zp - 0.28, zp + 0.28))
            pc = np.array(pieces)
            N = len(pc)
            Lz = pc[:, 3] - pc[:, 2]
            h = np.stack([Lz / 2, np.full(N, 0.015), pc[:, 1] / 2], 1)
            P = rbox(T_BRD_O3, h, np.stack([np.full(N, 0.006), np.full(N, 0.006), np.full(N, 0.008)], 1))
            u = P[:, :, 0] / h[:, None, 0]
            # cup, bow, loose boards
            cupf = np.array(cup_of, bool)
            cupa = np.where(cupf, rng.uniform(0.006, 0.010, N) * rng.choice([-1, 1], N), rng.uniform(-0.004, 0.004, N))
            P[:, :, 1] += cupa[:, None] * ((P[:, :, 2] / h[:, None, 2]) ** 2 - 0.5)
            ncup_total[0] += int(cupf.sum() > 0)
            P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (1 - u ** 2)
            loose = rng.random(N) < 0.05
            # each board leans up to +-0.5 deg, a few loose ones up to 1 deg
            skew = (np.where(loose, rng.uniform(-1.0, 1.0, N), np.clip(rng.normal(0, 0.3, N), -0.5, 0.5))
                    + pc[:, 4]) * D2R
            yoff = 0.015 + np.where(loose, rng.uniform(0.006, 0.014, N), rng.uniform(-0.004, 0.004, N))
            yoff = yoff + np.where(pc[:, 4] > 0, 0.012, 0.0)
            zc = (pc[:, 2] + pc[:, 3]) / 2
            zz = zc[:, None] + P[:, :, 0]
            # split halves spring outward toward their free end
            sprung = (pc[:, 4] > 0)[:, None] * np.clip((pc[:, 2:3] + 0.27 - zz) / 0.27, 0, 1) * 0.012
            ll = pc[:, 0][:, None] + P[:, :, 2] + skew[:, None] * P[:, :, 0]
            scale = (tw_a(g, zz) + 0.03) / (float(tw_a(g, zm)) + 0.03)
            yy = yoff[:, None] + P[:, :, 1] + sprung
            W = face_map(g, k, ll * scale, zz, yy)
            # inner faces never seen; top ends tucked under a rail / the curb are not modelled either
            covered_top = pc[:, 3] > z1 - 0.03
            covered_bot = pc[:, 2] < z0 + 0.035              # on the sill / tucked behind the rail below
            for sel_, Tq in ((covered_top & covered_bot, T_BRD_O3TB), (covered_top & ~covered_bot, T_BRD_O3T),
                             (~covered_top & covered_bot, T_BRD_O3B), (~covered_top & ~covered_bot, T_BRD_O3)):
                if sel_.any():
                    P_b.add(W[sel_], Tq, Pl=P[sel_], mat="M_timber_weathered", smooth="bevel")
            nb_total += N
            # cover battens on ~40% of joints
            js = lc[:-1] + ws[:-1] / 2 + 0.004
            sel = rng.random(len(js)) < 0.4
            for jl in js[sel]:
                zz2 = np.array([z0 + 0.03, z1 - 0.02])
                pa = face_map(g, k, np.array([jl * float(tw_a(g, zz2[0]) + 0.03) / (float(tw_a(g, zm)) + 0.03)]),
                              zz2[:1], np.array([0.042]))
                pb = face_map(g, k, np.array([jl * float(tw_a(g, zz2[1]) + 0.03) / (float(tw_a(g, zm)) + 0.03)]),
                              zz2[1:], np.array([0.042]))
                n, t = face_axes(k)
                member(P_b, "M_timber_weathered", pa, pb, 0.045, 0.018, up=n, c=0.005, rng=rng, bow=0.004, T=T_PLK_NI)
    log("tower boards %d pieces, %d strongly cupped boards, %d split ends" % (nb_total, ncup_total[0], len(splits)))
    # patched board: a short plank nailed over a rotten one
    for (k, l0, w, zb, zt) in patches:
        n, t = face_axes(k)
        pa = face_map(g, k, np.array([l0 + 0.01]), np.array([zb]), np.array([0.058]))
        pb = face_map(g, k, np.array([l0 - 0.01]), np.array([zt]), np.array([0.058]))
        member(P_b, "M_timber_weathered", pa, pb, w, 0.022, up=n, c=0.005, rng=rng, bow=0.003, T=T_PLK_NI)
        nl_ = np.array([[l0 - w * 0.3, zb + 0.06], [l0 + w * 0.3, zb + 0.07], [l0 - w * 0.28, zt - 0.06],
                        [l0 + w * 0.3, zt - 0.07]])
        prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
        Pn, Tn = lathe(np.repeat(prof[None], 4, 0), 6, open_base=True)
        Rn = np.repeat(frame_mats(t[None], np.cross(n, t)[None], n[None]), 4, 0)
        P_i.add(xform(Pn, Rn, face_map(g, k, nl_[:, 0], nl_[:, 1], np.full(4, 0.069))), Tn, mat="M_iron", smooth="all")
    # corner (cant) posts, proud of the boards
    for k in range(8):
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        za, zb = g.TW_Z0 - 0.1, g.ZCT - g.CURB_D - 0.005
        a = bis * float(post_geom(g, za)) + np.array([0, 0, za])
        b = bis * float(post_geom(g, zb)) + np.array([0, 0, zb])
        member(P_f, "M_timber", a[None], b[None], 0.2, 0.2, up=bis, c=0.025, rng=rng, bow=0.01, T=T_PLK_NI)

    # sill beams, rails with drip boards
    def ring_members(z, yout, w, d, ext, mat, part, cc=0.015, bow=0.0):
        for k in range(8):
            c0 = (k - 0.5) * PI / 4
            c1 = (k + 0.5) * PI / 4
            rr = (float(tw_a(g, z)) + yout) / COS225
            pa = np.array([math.sin(c0) * rr, -math.cos(c0) * rr, z])
            pb = np.array([math.sin(c1) * rr, -math.cos(c1) * rr, z])
            dd = unit(pb - pa)
            n, t = face_axes(k)
            member(part, mat, (pa - dd * ext)[None], (pb + dd * ext)[None], w, d, up=n, c=cc, rng=rng, bow=bow,
                   T=T_PLK_NI)
    ring_members(float(TZ(g, 5.41)), -0.03, 0.24, 0.24, 0.06, "M_timber", P_f, cc=0.02, bow=0.008)  # sill
    for zr in (float(TZ(g, 7.22)), float(TZ(g, 9.02))):
        ring_members(zr, 0.075, 0.05, 0.11, -0.10, "M_timber", P_f, cc=0.01)       # rail (girt)
        # drip board on the rail, sloping outward, projecting 4 cm
        for k in range(8):
            n, t = face_axes(k)
            hw = (float(tw_a(g, zr + 0.07)) + 0.03) * TAN225 - 0.10
            ctr = face_map(g, k, np.array([0.0]), np.array([zr + 0.075]), np.array([0.09]))[0]
            xa = t
            ya = unit(np.array([0, 0, 1.0]) + n * 0.28)
            za = np.cross(xa, ya)
            blocks_world(P_f, "M_timber", ctr[None], frame_mats(xa[None], ya[None], za[None]),
                         [[hw, 0.011, 0.055]], c=0.004, T=T_PLK_DB)
    # ---- top curb: circular, 8 timber segments joined by half-laps, two oak pegs per joint ----
    lap = 0.13 / g.CURB_R
    gap = 0.004 / g.CURB_R
    th_j = np.arange(8) * PI / 4 + 0.17 + rng.uniform(-0.05, 0.05, 8)
    dz_s = rng.uniform(-0.004, 0.004, 8)
    dr_s = rng.uniform(-0.005, 0.005, 8)

    def arc_piece(t0, t1, zc_, hd, rr, top_hidden=True):
        n = max(3, int((t1 - t0) * rr / 0.08) + 1)
        tt = np.linspace(t0, t1, n)
        path = np.stack([rr * np.sin(tt), -rr * np.cos(tt), np.full(n, zc_)], 1)[None]
        Pp, Tp = sweep(path, rect_prof(g.CURB_W, hd, 0.018 if hd > 0.15 else 0.01), up=(0, 0, 1))
        if top_hidden:      # the curb's top face is enclosed under the cap frame and valance
            mq = (np.arange(len(Tp["quads"])) % 8) != 2
            Tp = dict(Tp, quads=Tp["quads"][mq], qflat=Tp["qflat"][mq])
        P_f.add(Pp, Tp, mat="M_timber", smooth="bevel")
    D = g.CURB_D
    for j in range(8):
        t0, t1 = th_j[j], th_j[(j + 1) % 8] + (2 * PI if j == 7 else 0)
        rr = g.CURB_R + dr_s[j]
        zt = g.ZCT + dz_s[j]
        arc_piece(t0 + lap + gap, t1 - lap - gap, zt - D / 2, D, rr)          # full section
        arc_piece(t1 - lap - gap * 0.5, t1 + lap, zt - D / 4, D / 2 - 0.003, rr)   # top half over the next joint
        arc_piece(t0 - lap, t0 + lap + gap * 0.5, zt - 3 * D / 4, D / 2 - 0.003, rr)  # bottom half under the joint
    pegs = []
    for j in range(8):
        for o in (-0.5, 0.5):
            tq = th_j[j] + o * lap * 0.9
            pegs.append([g.CURB_R * math.sin(tq), -g.CURB_R * math.cos(tq), g.ZCT + dz_s[j - 1] - 0.003])
    prof = np.array([(0.0, 0.0), (0.014, 0.0), (0.014, 0.012), (0.011, 0.018), (0.0, 0.019)])
    Pg, Tg = lathe(np.repeat(prof[None], len(pegs), 0), 8, open_base=True)
    P_f.add(Pg + np.array(pegs)[:, None, :], Tg, mat="M_timber", smooth="all")
    # ---- iron prop collar: flat strap 60 x 10 mm lying on the boards, following the octagon and
    # stepping out over the corner posts, with bolts ----
    zc = g.Z_COLLAR
    a_ = float(tw_a(g, zc))
    pts = []
    bolts = []
    for k in range(8):
        n, t = face_axes(k)
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        tang = np.array([math.cos(phi), math.sin(phi), 0.0])
        c = bis * float(post_geom(g, zc)) + np.array([0, 0, zc])
        yf = a_ + 0.058
        # where face k's strap line meets the post's near side plane
        e = 0.106
        l_hit = ((c - n * yf) @ tang - e) / (t @ tang)
        A0 = n * yf + t * l_hit + np.array([0, 0, zc])
        A = c + bis * e - tang * e
        B = c + bis * e + tang * e
        n2, t2 = face_axes(k + 1)
        l_hit2 = ((c - n2 * yf) @ tang + e) / (t2 @ tang)
        B0 = n2 * yf + t2 * l_hit2 + np.array([0, 0, zc])
        pts += [A0, A, B, B0]
        for l in (-0.18, 0.18):
            bolts.append((face_map(g, k, np.array([l]), np.array([zc]), np.array([0.063]))[0], n, t))
    path = np.array(pts)[None]
    Pc, Tc = sweep(path, rect_prof(0.010, 0.060, 0.002), up=(0, 0, 1), closed=True)
    P_i.add(Pc, Tc, mat="M_iron", smooth="bevel")
    prof = np.array([(0.0, 0.0), (0.019, 0.0), (0.019, 0.008), (0.012, 0.013), (0.0, 0.014)])
    Pb_, Tb_ = lathe(np.repeat(prof[None], len(bolts), 0), 6, open_base=True)
    Rb = np.array([frame_mats(t[None], np.cross(n, t)[None], n[None])[0] for (_, n, t) in bolts])
    P_i.add(xform(Pb_, Rb, np.array([b[0] for b in bolts])), Tb_, mat="M_iron", smooth="none")
    # hatch on the front face (frame, shutter propped open, interior deck)
    k = hatch["k"]
    n, t = face_axes(k)
    lw, z0, z1 = hatch["l"], hatch["z0"], hatch["z1"]

    def fm(l, z, y):
        return face_map(g, k, np.atleast_1d(np.asarray(l, float)), np.atleast_1d(np.asarray(z, float)),
                        np.atleast_1d(np.asarray(y, float)))
    for s in (-1, 1):
        member(P_f, "M_timber", fm(s * (lw + 0.03), z0 - 0.06, 0.03), fm(s * (lw + 0.03), z1 + 0.08, 0.03), 0.07,
               0.075, up=n, c=0.01)
    member(P_f, "M_timber", fm(-lw - 0.08, z0 - 0.035, 0.035), fm(lw + 0.08, z0 - 0.035, 0.035), 0.07, 0.09, up=n,
           c=0.01)
    member(P_f, "M_timber", fm(-lw - 0.08, z1 + 0.05, 0.03), fm(lw + 0.08, z1 + 0.05, 0.03), 0.075, 0.08, up=n,
           c=0.01)
    # shutter: 3 boards + 2 ledges, hinged at the head, propped open 38 deg
    ang = 38 * D2R
    hinge = fm(0.0, z1 + 0.02, 0.075)[0]
    Rsh = rotm(t, [-ang])[0]   # lower edge swings outward (-n)

    def shutter(P):
        return (P - hinge) @ Rsh.T + hinge
    bw = (2 * lw + 0.06) / 3
    for i in range(3):
        lc = -lw - 0.03 + bw * (i + 0.5)
        pa = fm(lc, z0 - 0.02, 0.09)
        pb = fm(lc, z1 + 0.02, 0.09)
        tmp = BatchAcc("tmp", ["M_timber"])
        member(tmp, "M_timber", pa, pb, bw - 0.008, 0.028, up=n, c=0.005, rng=rng, bow=0.004)
        P_f.add(shutter(tmp.V[0])[None], T_PLK, mat="M_timber_weathered", smooth="bevel")
    for zl in (z0 + 0.1, z1 - 0.1):
        tmp = BatchAcc("tmp", ["M_timber"])
        member(tmp, "M_timber", fm(-lw - 0.01, zl, 0.06), fm(lw + 0.01, zl, 0.06), 0.028, 0.08, up=n, c=0.005)
        P_f.add(shutter(tmp.V[0])[None], T_PLK, mat="M_timber_weathered", smooth="bevel")
    for s in (-0.16, 0.16):
        tmp = BatchAcc("tmp", ["M_iron"])
        member(tmp, "M_iron", fm(s, z1 + 0.03, 0.108), fm(s, z0 + 0.05, 0.108), 0.04, 0.006, up=n, c=0.002)
        P_i.add(shutter(tmp.V[0])[None], T_PLK, mat="M_iron", smooth="none")
    # prop stick from the sill to the shutter's lower edge
    low = shutter(fm(0.18, z0 - 0.01, 0.09))[0]
    member(P_f, "M_timber", fm(0.18, z0 - 0.02, 0.07), low[None], 0.035, 0.035, up=n, c=0.008)
    # interior deck under the hatch (dark interior)
    zd = float(TZ(g, 7.66))
    ang8 = np.arange(9) * PI / 4 - PI / 8
    rr = (float(tw_a(g, zd)) - 0.02) / COS225
    ring = np.stack([rr * np.sin(ang8), -rr * np.cos(ang8), np.full(9, zd)], 1)
    ctr = np.repeat([[0, 0, zd]], 9, 0)
    add_grid(P_f, "M_timber", np.stack([ctr, ring], 1), flip=False)


def smock_tower(g, af_bottom=None, af_top=None, z0=None, z1=None, lean_deg=None, seed=None):
    """Octagonal boarded smock tower (kit component): across-flats af_bottom at z0 tapering to af_top at z1,
    leaning lean_deg; cant posts, sill, rails with drip boards, a lapped round top curb with pegs, vertical
    weatherboards with battens, split / cupped / patched boards, a propped hatch and the iron prop collar
    (<PREFIX>_tower_boards / _tower_frame / _tower_iron)."""
    kw = {k_: v_ for k_, v_ in (("TW_A0", None if af_bottom is None else af_bottom / 2),
                                ("TW_A1", None if af_top is None else af_top / 2), ("TW_Z0", z0), ("TW_Z1", z1),
                                ("LEAN_ANG", None if lean_deg is None else lean_deg * D2R))
          if v_ is not None}
    g.set(**kw)
    with g.seeded(seed):
        build_tower(g, g.parts)
