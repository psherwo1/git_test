"""components.drum_door -- the arched entrance of a stone drum (kit 1.2.0): dressed surround with an irregular
voussoir ring, worn threshold, arch-topped ledged plank leaf hung ajar with strap hinges, ring pull and nails, the
passage and the interior depth seen through the door, and the door step built into the entrance.

Public components: arched_door(g, width, spring, reveal, ring, seed), entrance_step(g, seed).
"""
import math
import os  # noqa: F401
from functools import partial  # noqa: F401

import numpy as np

from .drum_frame import (R_out, arch_set, door_params, kpart, open_place)  # noqa: F401
from ..split_stones import (stone_local)  # noqa: F401
from ..tmplmesh import (BatchAcc, D2R, PI, T_BLK, T_FLAG_O, T_PLK_NI, add_caps, add_grid, circle_prof, frame_mats,
    lathe, log, member, orient, orient_open, rbox, rect_prof, rotm, sweep, tmpl_rings, xform)  # noqa: F401


def arched_door_surround(g, parts):
    """Dressed door surround (jambs, irregular voussoir ring) and the worn threshold, in its own object."""
    P_dr = kpart(g, parts, "door_surround", ["M_stone_dressed"], wear=0.45, angle=22.0)
    rd = g.RNG("door_surround")
    jam = {s: [(g.DOOR_JZ[i], g.DOOR_JZ[i + 1], g.DOOR_JAMBS[s][i]) for i in range(4)] for s in (-1, 1)}
    arch_set(g, P_dr, rd, 0.0, g.DOOR_CW, g.ZS_DOOR, 11, g.DOOR_RING, 0.34, jam, lambda z: np.full_like(z, g.R_DOOR),
             yfront=0.03, style="hero")
    # threshold stone (worn dip in the middle)
    P, T = stone_local(rd, [1.32], [0.17], [0.46], "hero", rot_deg=(0.2, 0.2, 0.2), spall=(1, 2))
    u = P[:, :, 0] / 0.66
    top = P[:, :, 2] > 0.04
    P[:, :, 2] -= top * 0.012 * np.exp(-(u * 2.2) ** 2) * np.exp(-((P[:, :, 1] + 0.2) / 0.2) ** 2)
    W = open_place(g, P, np.array([0.0]), np.array([0.0]), np.array([g.Z_TH - 0.085]), np.array([0.07]),
                   lambda z: np.full_like(z, g.R_DOOR))
    P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="all")


def door_planks(part, rng, x0, width, z_bot, ztop_fn, xf, n=6, t=0.042):
    """Arch-topped ledged door leaf planks (kit component), leaf-local x lateral (hinge at x0), y thickness from
    the outer face (y = 0) inward, z up; xf maps leaf-local -> world. Age per art bible section 4: outer arrises
    worn 1.5-2.5 cm (more in the bottom 0.4 m and on the lock stile), ragged rotted bottom end (+-2-4 cm) with
    two planks 3-5 cm short, face checks (3-5 mm wide, 0.3-0.9 m long), one split at the arched head, plank
    proudness +-3 mm, gaps 4-10 mm, free edge sagging 5-8 mm. Returns [(xa, xb, dy)] per plank."""
    gaps = rng.uniform(0.004, 0.010, n - 1)
    wds = rng.uniform(0.17, 0.23, n)
    wds = wds / wds.sum() * (width - gaps.sum())
    xa_s = x0 + np.concatenate([[0], np.cumsum(wds[:-1] + gaps)])
    short = set(int(v) for v in rng.choice(n, 2, replace=False))
    checked = set(int(v) for v in rng.choice(n, 3, replace=False))
    split = int(np.argmin(np.abs(xa_s + wds / 2 - (x0 + width / 2))))          # the plank under the crown
    sag = rng.uniform(0.005, 0.008)
    nr = 48
    tt = np.linspace(0, 1, nr)
    tt = tt + 0.35 * tt * (1 - tt) * (0.5 - tt)                              # a little denser at both ends
    out = []
    for i in range(n):
        xa, w = xa_s[i], wds[i]
        dy = rng.uniform(-0.003, 0.003)
        th = t + rng.uniform(-0.002, 0.002)
        lock = i == n - 1
        cf0 = rng.uniform(0.015, 0.022, 2) + (np.array([0.0, 0.005]) if lock else 0.0)
        xc = rng.uniform(0.3, 0.7) * w
        ck0, ckl = rng.uniform(0.1, 0.9), rng.uniform(0.3, 0.9)
        ckd = rng.uniform(0.004, 0.006)
        sh = rng.uniform(0.03, 0.05) if i in short else 0.0
        ph = rng.uniform(0, 6, 3)
        rings, xs_all = [], []
        for k, tq in enumerate(tt):
            # approximate height above the bottom for the extra rot wear (bottom 0.4 m)
            zz = tq * 2.15
            rot = 0.009 * np.clip(1 - zz / 0.4, 0, 1)
            cl, cr = cf0[0] + rot + 0.002 * math.sin(zz * 3 + ph[0]), cf0[1] + rot + 0.002 * math.sin(zz * 2.3 + ph[1])
            cyl, cyr = min(0.55 * cl, 0.016), min(0.55 * cr, 0.016)
            c45 = 1 - math.cos(PI / 4)
            # face check (and the split at the head)
            dep, hw_ = 0.0, 0.0025
            if i in checked:
                u = (zz - ck0) / ckl
                if 0 < u < 1:
                    dep = ckd * math.sqrt(math.sin(u * PI))
            if i == split and zz > 1.85:
                u = min((zz - 1.85) / 0.35, 1.0)
                dep = max(dep, 0.65 * th * math.sqrt(u))
                hw_ = 0.0015 + 0.0015 * u
            xcs = xc if i not in checked and i != split else xc
            prof = [(0.0, cyl), (cl * c45, cyl * c45), (cl, 0.0),
                    (cl + (xcs - hw_ - cl) * 0.5, 0.0), (xcs - hw_, 0.0), (xcs, dep), (xcs + hw_, 0.0),
                    (xcs + hw_ + (w - cr - xcs - hw_) * 0.5, 0.0),
                    (w - cr, 0.0), (w - cr * c45, cyr * c45), (w, cyr),
                    (w, th - 0.004), (w - 0.004, th), (0.004, th), (0.0, th - 0.004)]
            rings.append(prof)
        R_ = np.array(rings)                                               # (nr, m, 2)
        m = R_.shape[1]
        X = xa + R_[..., 0]
        # ragged rotted bottom end, short planks
        zb = z_bot + 0.012 + 0.010 * np.sin(X * 37 + ph[2]) + 0.007 * np.sin(X * 91 + i) + \
            0.006 * np.abs(np.sin(X * 23 + 2 * i)) + sh
        zt_ = ztop_fn(X)
        Z = zb + tt[:, None] * (zt_ - zb)
        Z -= sag * (X - x0) / width
        Y = R_[..., 1] + dy + 0.0025 * np.sin(Z * 3 + xa * 20)                # slight warp
        P = np.stack([X, Y, Z], -1).reshape(1, -1, 3)
        T = tmpl_rings(nr, m, cap0=True, cap1=True)
        P = add_caps(P, T)
        T = orient(T, P[0])
        part.add(xf(P), T, Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.65 + 0.2 * (i in short))
        out.append((xa, xa + w, dy))
    log("door planks %d: short %s, checks %s, split at the head %d, free-edge sag %.1f mm"
        % (n, sorted(short), sorted(checked), split, sag * 1000))
    return out


def build_door_and_interior(g, parts):
    P_mo, P_int, P_leaf, P_iron = parts["mortar"], parts["interior"], parts["door"], parts["door_iron"]
    rng = g.RNG("door_leaf")
    Rd = g.R_DOOR
    RI = g.R_BASE0 - 0.80                    # inner wall radius (kit: follows the drum)
    # ---- passage behind the rebate (plastered rubble), rere-arch vault ----
    XW = 0.675
    d0, d1 = -0.31, -0.97
    ZV = 1.95

    def to_world(x, d, z):  # door frame: x lateral (+X), d = depth offset from face (negative = inward)
        return np.stack([x, -(Rd + d), z], -1)

    nz = 12
    for s in (-1, 1):
        dd = np.linspace(d0, d1, 6)
        zz = np.linspace(g.Z_TH - 0.02, ZV, nz)
        D, Z = np.meshgrid(dd, zz, indexing="ij")
        X = s * XW + s * 0.01 * np.sin(D * 9 + Z * 5) * np.sin(Z * 3.1)
        add_grid(P_mo, "M_mortar", to_world(X, D, Z), flip=(s > 0))
    # vault
    al = np.linspace(0, PI, 17)
    dd = np.linspace(d0, d1, 6)
    A, D = np.meshgrid(al, dd, indexing="ij")
    X = XW * np.cos(A)
    Z = ZV + XW * 0.9 * np.sin(A)
    add_grid(P_mo, "M_mortar", to_world(X, D, Z), flip=True)
    # rear face of the door arch between intrados and vault (at the rebate plane)
    xs = np.linspace(-XW, XW, 24)
    zz = np.linspace(g.ZS_DOOR - 0.05, ZV + XW * 0.9 + 0.02, 10)
    X, Z = np.meshgrid(xs, zz, indexing="ij")
    keep = np.ones((len(xs) - 1, len(zz) - 1), bool)
    for i in range(len(xs) - 1):
        for j in range(len(zz) - 1):
            xc, zc = (xs[i] + xs[i + 1]) / 2, (zz[j] + zz[j + 1]) / 2
            inside_door = (zc - g.ZS_DOOR) ** 2 + xc ** 2 < (g.DOOR_CW + 0.01) ** 2 or zc < g.ZS_DOOR
            keep[i, j] = (not inside_door)
    add_grid(P_mo, "M_mortar", to_world(X, np.full_like(X, d0 - 0.004), Z), keep=keep, flip=True)

    # ---- interior: inner wall face, flagstone floor, ceiling beams, boards, ladder ----
    nth = 96
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.linspace(g.Z_TH - 0.02, 3.34, 15)
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    r = R_out(g, Z) - 0.80 + 0.012 * np.sin(TH * 11 + Z * 4) * np.sin(TH * 4 - Z * 6)
    G = np.stack([r * np.sin(TH), -r * np.cos(TH), Z], 2)
    keep = np.ones((nth, len(zs) - 1), bool)
    for i in range(nth):
        # only the arc of the inner wall that can be seen through the door is modelled
        if abs(((ths[i] + PI / nth) % (2 * PI)) - PI) > 1.25:
            keep[i, :] = False
            continue
        for j in range(len(zs) - 1):
            for tq in (ths[i], ths[i] + 2 * PI / nth):
                d = (tq + PI) % (2 * PI) - PI
                x = RI * math.sin(d)
                zt = zs[j]
                if abs(d) < PI / 2 and abs(x) < XW + 0.02 and zt < ZV + 0.9 * math.sqrt(max(XW ** 2 - x ** 2, 0)):
                    keep[i, j] = False
    add_grid(P_int, "M_mortar", G, keep=keep, wrap=True, flip=True)
    # flagstone floor
    rf = g.RNG("floor")
    cells = []
    y = -(RI + 0.65)
    while y < RI + 0.1:
        hrow = rf.uniform(0.38, 0.6)
        x = -(RI + 0.1) + rf.uniform(0, 0.3)
        while x < RI + 0.1:
            w = rf.uniform(0.35, 0.7)
            cx, cy = x + w / 2, y + hrow / 2
            inside = (math.hypot(cx, cy) < RI + 0.15 and cy < -0.6 and abs(cx) < RI - 0.3) or (abs(cx) < 0.75 and cy < -(RI - 0.3))
            if inside:
                cells.append((cx, cy, w - 0.025, hrow - 0.025))
            x += w
        y += hrow
    c = np.array(cells)
    N = len(c)
    P, T = stone_local(rf, c[:, 2], c[:, 3], np.full(N, 0.035), "flag", rot_deg=(0.3, 0.3, 1.5), T=T_FLAG_O)
    # stone_local: x = length, y = "outward" (thickness), z = height -> lay flat: local y -> world z
    Rm = frame_mats(np.repeat([[1.0, 0, 0]], N, 0), np.repeat([[0, 0, 1.0]], N, 0), np.repeat([[0, -1.0, 0]], N, 0))
    W = xform(P, Rm, np.stack([c[:, 0], c[:, 1], np.full(N, g.Z_TH) + rf.normal(0, 0.003, N)], 1))
    P_int.add(W, T, Pl=P, mat="M_stone", smooth="all")
    # ceiling beams + floor boards (first floor at 3.0 m)
    rt = g.RNG("ceiling")
    # (the first-floor beams and boards are above the line of sight through the door: not modelled)
    bx = -(RI + 0.1)
    a, b = [], []
    while False:            # (the floor boards above the beams cannot be seen through the door: not modelled)
        w = rt.uniform(0.18, 0.28)
        cx = bx + w / 2
        if not (0.3 < cx < 0.85):  # hatch for the ladder
            half = math.sqrt(max((RI + 0.15) ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, half, 3.285])
        else:
            half = math.sqrt(max((RI + 0.15) ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, 0.75, 3.285])
        bx += w + 0.008
    a, b = np.array(a), np.array(b)
    # beyond ~1.5 m of visible depth (y > -0.65) the floor is a plain flagged surface: one low-res sheet
    # (producer note: interiors only to the depth seen through openings)
    xs_ = np.linspace(-(RI + 0.1), RI + 0.1, 9)
    ys_ = np.linspace(-0.66, RI + 0.15, 7)
    X_, Y_ = np.meshgrid(xs_, ys_, indexing="ij")
    keep_ = np.hypot((X_[:-1, :-1] + X_[1:, 1:]) / 2, (Y_[:-1, :-1] + Y_[1:, 1:]) / 2) < RI + 0.25
    add_grid(P_int, "M_stone", np.stack([X_, Y_, np.full_like(X_, g.Z_TH - 0.004)], 2), keep=keep_, flip=False)
    # round 6 (director r5 secondary): depth through the door - a worn oak floor sill across the inner end of the
    # passage (its top arris catches the door light: the visible floor edge) and the foot of the ladder to the
    # first floor, 1.0-1.5 m inside, right of the ajar leaf
    rl = g.RNG("ladder")
    y_sill = -(Rd + d1) - 0.07
    member(P_int, "M_timber", np.array([[-XW + 0.02, y_sill, g.Z_TH - 0.032]]), np.array([[XW - 0.02, y_sill, g.Z_TH - 0.028]]),
           0.15, 0.075, up=(0, 0, 1), c=0.012, rng=rl, bow=0.004)
    y_ft = -Rd + 1.30
    lean_ = 72.0 * D2R
    run_ = (3.25 - g.Z_TH) / math.tan(lean_)
    sx_ = (0.10, 0.52)
    stile_a, stile_b = [], []
    for k_, xs_l in enumerate(sx_):
        xs_l += rl.uniform(-0.01, 0.01)
        stile_a.append([xs_l, y_ft + rl.uniform(-0.01, 0.01), g.Z_TH - 0.01])
        stile_b.append([xs_l + rl.uniform(-0.02, 0.02), y_ft + run_, 3.25])
    stile_a, stile_b = np.array(stile_a), np.array(stile_b)
    member(P_int, "M_timber", stile_a, stile_b, 0.10, 0.055, up=(1, 0, 0), c=0.014, rng=rl, bow=0.01, twist=0.03)
    ra_, rb_ = [], []
    z_r = g.Z_TH + 0.26
    while z_r < 3.1:
        f_ = (z_r - g.Z_TH) / (3.25 - g.Z_TH)
        pa_ = stile_a[0] + (stile_b[0] - stile_a[0]) * f_
        pb_ = stile_a[1] + (stile_b[1] - stile_a[1]) * f_
        dz_ = rl.uniform(-0.012, 0.012)
        ra_.append(pa_ + np.array([0.0, 0.0, dz_]))
        rb_.append(pb_ + np.array([0.0, 0.0, -dz_]))
        z_r += rl.uniform(0.27, 0.31)
    member(P_int, "M_timber", np.array(ra_), np.array(rb_), 0.045, 0.040, up=(0, 0, 1), c=0.013, rng=rl, bow=0.006,
           twist=0.1)
    log("interior: floor sill at y %.2f, ladder foot %.2f m inside the door face, %d rungs" % (y_sill, 1.30, len(ra_)))

    # ---- door leaf (arch-topped plank door, hung ajar 26 deg inward) ----
    LEAF_W = 2 * (g.DOOR_CW + 0.055)
    leaf_x0 = -LEAF_W / 2
    hinge = np.array([-g.DOOR_CW - 0.03, -(Rd - 0.335), 0.0])  # hinge axis x,y (vertical)
    ajar = 34 * D2R
    Rleaf = rotm([0, 0, 1], [ajar])[0]  # free edge swings inward (+Y)

    def leaf_xf(P):
        """leaf-local: x lateral, y = thickness (outer face y=0 toward -Y outward), z up -> world."""
        W = np.stack([P[..., 0], -(Rd - 0.335) + P[..., 1], P[..., 2]], -1)
        return (W - hinge) @ Rleaf.T + hinge

    planks = door_planks(P_leaf, rng, leaf_x0, LEAF_W, g.Z_TH + 0.01, lambda x: g.ZS_DOOR + np.sqrt(
        np.clip((g.DOOR_CW + 0.055) ** 2 - x ** 2, 0, None)) - 0.01, leaf_xf)
    # ledges + braces on the inner face
    ly = 0.042 + 0.018
    for zl in (g.Z_TH + 0.32, g.Z_TH + 1.02, g.Z_TH + 1.62):
        a = np.array([[leaf_x0 + 0.06, ly, zl]])
        b = np.array([[-leaf_x0 - 0.06, ly, zl]])
        Wm = BatchAcc("tmp", ["M_timber"])
        member(Wm, "M_timber", a, b, 0.15, 0.036, up=(0, 1, 0), c=0.008, T=T_PLK_NI)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK_NI, mat="M_timber_weathered", smooth="bevel")
    for (z0, z1) in ((g.Z_TH + 0.40, g.Z_TH + 0.94), (g.Z_TH + 1.10, g.Z_TH + 1.54)):
        a = np.array([[leaf_x0 + 0.14, ly, z0]])
        b = np.array([[-leaf_x0 - 0.14, ly, z1]])
        Wm = BatchAcc("tmp", ["M_timber"])
        member(Wm, "M_timber", a, b, 0.11, 0.032, up=(0, 1, 0), c=0.008, T=T_PLK_NI)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK_NI, mat="M_timber_weathered", smooth="bevel")
    # ---- iron: strap hinges with spear terminals, nail heads, pintles, ring pull, clinched nails ----
    for zh in (g.Z_TH + 0.32, g.Z_TH + 1.02, g.Z_TH + 1.62):
        L = 0.78 if zh < 1.6 else 0.62
        # strap: lies FLAT on the plank face (50 mm wide in z, 7 mm thick in -y), flat spear terminal
        n = 16
        xs_ = np.linspace(leaf_x0 + 0.01, leaf_x0 + L, n)
        hw = np.full(n, 0.025)
        hw[-4:] = [0.025, 0.036, 0.024, 0.004]           # spear: swells then tapers to a point
        xs_[-4:] = leaf_x0 + L - np.array([0.13, 0.085, 0.04, 0.0])
        hw += rng.uniform(-0.0015, 0.0015, n) * (hw > 0.01)   # hand-forged width wobble
        th_ = 0.0035
        path = np.stack([xs_, np.full(n, -th_ - 0.003), np.full(n, zh) + rng.uniform(-0.002, 0.002, n)], 1)[None]
        # sweep frame with up=(0,-1,0): ex = +-z (in the leaf plane), ey = -y (out of the leaf)
        prof = np.array([[1, -1], [1, 1], [-1, 1], [-1, -1]], float)
        prof = np.repeat(prof[None], n, 0)
        prof[:, :, 0] *= hw[:, None]
        prof[:, :, 1] *= th_ * (1 - 0.3 * (np.arange(n) >= n - 2))[:, None]
        P, T = sweep(path, prof[None], up=(0, -1, 0))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="none")
        # knuckle around pintle
        kp = np.array([[[leaf_x0 + 0.005, -0.012, zh - 0.05], [leaf_x0 + 0.005, -0.012, zh + 0.05]]])
        P, T = sweep(kp, circle_prof(0.016, 10), up=(1, 0, 0))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
        # nail heads along strap
        nx = np.linspace(leaf_x0 + 0.08, leaf_x0 + L - 0.1, 5)
        prof = np.array([(0.0, 0.0), (0.012, 0.0), (0.011, 0.004), (0.006, 0.008), (0.0, 0.009)])
        P, T = lathe(np.repeat(prof[None], len(nx), 0), 8, open_base=True)
        Rn = rotm([1, 0, 0], np.full(len(nx), PI / 2))
        P = xform(P, Rn, np.stack([nx, np.full(len(nx), -0.0098), np.full(len(nx), zh)], 1))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
        # pintle: L-pin leaded into the jamb rebate
        pin = np.array([[hinge[0] - 0.09, hinge[1] - 0.012, zh - 0.06], [hinge[0] + 0.004, hinge[1] - 0.012,
                                                                        zh - 0.06]])
        P, T = sweep(pin[None], rect_prof(0.022, 0.022, 0.004), up=(0, 0, 1))
        P_iron.add(P, T, mat="M_iron", smooth="none")
    # clinched nail heads in rows over the ledges (outer face)
    nails = []
    for zl in (g.Z_TH + 0.32, g.Z_TH + 1.02, g.Z_TH + 1.62):
        for (xa_, xb_, dy_) in planks:
            for o in (0.3, 0.7):
                nails.append((xa_ + (xb_ - xa_) * o + rng.uniform(-0.01, 0.01), zl + rng.uniform(-0.03, 0.03), dy_))
    nails = np.array(nails)
    prof = np.array([(0.0, 0.0), (0.009, 0.0), (0.008, 0.003), (0.004, 0.006), (0.0, 0.0065)])
    P, T = lathe(np.repeat(prof[None], len(nails), 0), 6, open_base=True)
    Rn = rotm([1, 0, 0], np.full(len(nails), PI / 2))
    P = xform(P, Rn, np.stack([nails[:, 0], nails[:, 2] - 0.001, nails[:, 1]], 1))
    P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
    # ring pull with back plate and staple
    rx, rz = -leaf_x0 - 0.22, g.Z_TH + 0.98
    prof = np.array([(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.044, 0.007), (0.012, 0.009), (0.0, 0.016)])
    P, T = lathe(prof[None], 16, open_base=True)
    P = xform(P, rotm([1, 0, 0], [PI / 2]), np.array([[rx, 0.0, rz]]))
    P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
    a = np.linspace(0, 2 * PI, 24, endpoint=False)
    ring = np.stack([rx + 0.06 * np.sin(a) * 0.98, np.full(24, -0.03) - 0.012 * np.cos(a), rz - 0.06 + 0.06 * np.cos(a)],
                    1)[None]
    P, T = sweep(ring, circle_prof(0.0085, 8), up=(0, -1, 0), closed=True)
    P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
    # keyhole escutcheon
    P = rbox(T_BLK, np.array([[0.03, 0.003, 0.05]]), np.array([[0.006, 0.002, 0.006]]))
    P_iron.add(leaf_xf(P + np.array([rx, -0.003, rz - 0.18])), T_BLK, mat="M_iron", smooth="bevel")


def flag_outline(rf, Lf, Wf, m=96, front_facets=0):
    """Irregular 5-7 sided flag outline (+-4 cm corners, 1-3 straight broken corners, wandering edges).
    front_facets (round 6, step stone): the front (-y) edge is split into that many straight fracture
    segments with +-1.5 cm kinks. Returns (O (mm,2), straight mask (mm,), segment id (mm,): >= 0 on a front
    facet, -1 elsewhere)."""
    rc = np.array([[Lf / 2, Wf / 2], [-Lf / 2, Wf / 2], [-Lf / 2, -Wf / 2], [Lf / 2, -Wf / 2]])
    rc = rc + rf.uniform(-0.04, 0.04, (4, 2))
    ncut = int(rf.integers(1, 4))
    cutc = set(int(v) for v in rf.choice(4, ncut, replace=False))
    corners, straight = [], set()
    for j in range(4):
        c0, cp, cn = rc[j], rc[j - 1], rc[(j + 1) % 4]
        if j in cutc:
            a_ = rf.uniform(0.08, 0.2)
            b_ = rf.uniform(0.08, 0.2)
            corners.append(c0 + (cp - c0) / np.linalg.norm(cp - c0) * a_)
            straight.add(len(corners) - 1)
            corners.append(c0 + (cn - c0) / np.linalg.norm(cn - c0) * b_)
        else:
            corners.append(c0)
    corners = np.array(corners)
    front_seg = {}
    if front_facets:
        nside0 = len(corners)
        segl = [np.linalg.norm(corners[(j + 1) % nside0] - corners[j]) for j in range(nside0)]
        cand = [j for j in range(nside0) if (corners[j][1] + corners[(j + 1) % nside0][1]) / 2 < -Wf / 4]
        jf = max(cand, key=lambda j: segl[j])
        a_, b_ = corners[jf], corners[(jf + 1) % nside0]
        fr = np.sort(rf.uniform(0.25, 0.75, front_facets - 1)) if front_facets > 2 else np.array([rf.uniform(0.38, 0.62)])
        ins = [a_ + (b_ - a_) * f + np.array([rf.uniform(-0.01, 0.01), rf.uniform(-0.015, 0.015)]) for f in fr]
        corners = np.concatenate([corners[:jf + 1], np.array(ins), corners[jf + 1:]])
        for q in range(front_facets):
            straight.add(jf + q)
            front_seg[jf + q] = q
    nside = len(corners)
    if not front_facets:
        straight.add(int(rf.integers(0, nside)))       # 1-2 crisp straight fracture edges per flag
    segs = [np.linalg.norm(corners[(j + 1) % nside] - corners[j]) for j in range(nside)]
    tot = sum(segs)
    pts, st, sid = [], [], []
    for j in range(nside):
        nseg = max(2, int(round(m * segs[j] / tot)))
        a, b = corners[j], corners[(j + 1) % nside]
        nrm_e = np.array([b[1] - a[1], a[0] - b[0]]) / max(segs[j], 1e-6)
        for q in range(nseg):
            u = q / nseg
            wob = 0.0 if j in straight else 0.01 * math.sin(u * PI) * math.sin(u * 7 + j) + \
                rf.uniform(-0.004, 0.004) * math.sin(u * PI)
            pts.append(a + (b - a) * u + nrm_e * wob)
            st.append(j in straight and 0 < q)
            sid.append(front_seg.get(j, -1))
    return np.array(pts), np.array(st), np.array(sid)


def door_step(part, rng, cx, cy, Lf, Wf, ztop):
    """Door step built into the entrance (kit component; producer note 10 keeps only this): one split stone
    bedded against the footing course under the threshold, level top at ztop with +-5 mm undulation, a split
    front of 2-3 planar facets with a 0.5-1 cm arris, 1-2 crisp spalls, a worn hollow at the tread centre, and
    a 3 cm buried skirt (no soil fillet, no loose stones: terrain is built in Unreal)."""
    O, st, sid = flag_outline(rng, Lf, Wf, front_facets=int(rng.integers(2, 4)))
    mm = len(O)
    rad = np.linalg.norm(O, axis=1)
    ztf = np.full(mm, ztop)
    inner_f = [0.18, 0.36, 0.52, 0.66, 0.78, 0.87, 0.94]
    rings = [np.concatenate([O * f, np.full((mm, 1), ztop)], 1) for f in inner_f]
    d_ar = np.where(st, 0.003, rng.uniform(0.005, 0.010)) * (1 + 0.25 * np.sin(np.arange(mm) * 0.31))
    d_ar = np.where(sid >= 0, rng.uniform(0.005, 0.009), d_ar)
    dz_ar = np.where(st, 0.002, d_ar * 0.8)
    dz_ar = np.where(sid >= 0, d_ar * 0.9, dz_ar)
    for d_, dz_ in ((d_ar * 1.8, 0.0), (d_ar * 0.45, dz_ar * 0.45), (0.0 * d_ar, dz_ar)):
        xy = O * (1 - d_ / rad)[:, None]
        rings.append(np.concatenate([xy, (ztf - dz_)[:, None]], 1))
    nrm2 = O / rad[:, None]
    ph_s = rng.uniform(0, 2 * PI, 2)
    jag = 0.0022 * np.sin(np.arange(mm) * 0.9 + ph_s[0]) + 0.0012 * np.sin(np.arange(mm) * 2.3 + ph_s[1])

    def circ_smooth(v, k=5):
        ker = np.ones(k) / k
        return np.convolve(np.concatenate([v[-k:], v, v[:k]]), ker, mode="same")[k:-k]
    jag *= 1 - 0.7 * circ_smooth(st.astype(float))
    bat = np.zeros(mm)
    for q in range(int(sid.max()) + 1):
        bat[sid == q] = rng.uniform(0.004, 0.016)
    bat = circ_smooth(circ_smooth(circ_smooth(bat, 7), 7), 5)   # facets meet on a soft kink, never a crack
    jag *= 1 - circ_smooth((sid >= 0).astype(float))
    zmid = ztf - dz_ar - rng.uniform(0.008, 0.015)
    fmid = np.clip((ztf - dz_ar - zmid) / np.maximum(ztf - dz_ar + 0.03, 0.01), 0, 1)
    rings.append(np.concatenate([O + nrm2 * (jag + bat * fmid)[:, None], zmid[:, None]], 1))
    rings.append(np.concatenate([O + nrm2 * bat[:, None], np.full((mm, 1), -0.03)], 1))
    Pf = np.array(rings)
    nr_ = len(rings)
    topm = np.arange(nr_) < nr_ - 1
    ph_ = rng.uniform(0, 2 * PI, 3)
    un = rng.uniform(0.005, 0.0065) * np.sin(Pf[..., 0] * 4.1 + ph_[0]) * np.sin(Pf[..., 1] * 5.3 + ph_[1]) + \
        0.0018 * np.sin(Pf[..., 0] * 9.5 - Pf[..., 1] * 7.7 + ph_[2])
    Pf[..., 2] += un * (0.005 / 0.0083) * topm[:, None]
    KA = len(inner_f)
    for _ in range(int(rng.integers(1, 3))):         # 1-2 crisp spalls off the exposed top arris
        j0 = int(rng.integers(0, mm))
        dj = np.abs((np.arange(mm) - j0 + mm // 2) % mm - mm // 2)
        w_ = np.clip((rng.uniform(2.0, 4.0) - dj) / 1.0, 0, 1)
        dep = min(rng.uniform(0.010, 0.020), 0.8 * float(Pf[KA, j0, 2]))
        for k in (KA - 1, KA, KA + 1, KA + 2):
            Pf[k, :, 2] -= w_ * dep * (0.25 if k == KA - 1 else 1.0)
            Pf[k, :, :2] *= (1 - w_ * (0.03 if k >= KA else 0.0))[:, None]
    Pf[KA + 3, :, 2] = np.minimum(Pf[KA + 3, :, 2], Pf[KA + 2, :, 2] - 0.004)
    front = np.clip(-Pf[..., 1] / (Wf / 2), 0, 1) ** 3
    hol = 0.026 * np.exp(-(Pf[..., 0] / 0.2) ** 2) * front
    Pf[..., 2] -= hol * (np.arange(nr_) <= KA + 2)[:, None]
    Pf[..., 0] += cx
    Pf[..., 1] += cy
    V = Pf.reshape(1, -1, 3)
    Tf = tmpl_rings(nr_, mm, cap0=True, cap1=False)
    V = add_caps(V, Tf)
    Tf = orient_open(Tf, V[0])
    part.add(V, Tf, mat="M_stone", smooth="bevel", wear=0.75)
    log("door step: top %.3f m, %d front facets" % (float(Pf[:-1, :, 2].max()), int(sid.max()) + 1))


def build_ground(g, parts):
    """Producer note 10 (round 6): loose ground stones, rubble clusters, path flags, gravel and soil aprons are
    out of scope (terrain is built in Unreal) and are not modelled. Only the door step built into the entrance
    remains; the footing course meets Z = 0 with a <= 5 cm buried skirt."""
    dy_ = g.R_BASE0 - 2.60                                  # kit: the step sits at the drum's door
    door_step(parts["step"], g.RNG("path_flags"), 0.0, -2.95 - dy_, 1.25, 0.60, 0.075)


# =============================================================================================
# public kit components
# =============================================================================================
def arched_door(g, width=None, spring=None, reveal=None, ring=None, seed=None, _drum_call=False):
    """Arched stone doorway (kit component), facing -Y in its drum: clear `width`, semicircular head springing
    `spring` above the threshold, dressed jambs + irregular voussoirs (<PREFIX>_door_surround), threshold, the
    arch-topped ledged plank leaf hung ajar with strap hinges (<PREFIX>_door_leaf / _door_iron) and the visible
    interior depth -- passage, floor sill, ladder foot (<PREFIX>_interior).  `reveal` is the rebate depth."""
    door_params(g, width, spring, reveal, ring)
    with g.seeded(seed):
        arched_door_surround(g, g.parts)
        build_door_and_interior(g, g.parts)


def entrance_step(g, seed=None):
    """The door step built into the entrance (producer note 10 keeps only this): one split stone bedded against
    the footing under the threshold, split front of 2-3 facets, 1-2 spalls, a worn hollow (<PREFIX>_door_step)."""
    with g.seeded(seed):
        build_ground(g, g.parts)
