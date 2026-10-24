"""components.plank_doors -- arched and rectangular plank doors with forged ironwork (kit 1.1.0, from the hilltop keep).

plank_leaf(acc, mapfn, ...)    vertical-plank leaf in any local door frame (x along, z up, w out): 6-8 planks of
                               uneven width with V-chamfered joints, offsets, uneven bottom ends, a split plank, a
                               rotted corner; arched or square head (zt_fn)
strap_hinge(...)               forged strap (50 -> 38 mm, spear terminal) lying on a facet-mapped leaf, pooled pintle
                               knuckle in the jamb, nails
make_pintle(acc, i)            pooled forged knuckle eye + pintle + square shank (producer note 3)
arched_door(g, seed=808)       KIT COMPONENT: the arch-topped leaf of the principal (arched) opening of an OctFrame
                               with 3 ledges, 3 strap hinges, clinch nails, ring pull with backplate, keyhole plate
                               -> <P>_door_leaf, <P>_door_ironwork
plank_door(g, seed=1212)       KIT COMPONENT: rectangular plank door in the annex wall (g.WDOOR): hewn jambs and lintel,
                               stone threshold, 7-plank leaf with ledges, 3 strap hinges, thumb latch
                               -> <P>_wing_door, <P>_wing_door_ironwork
door_spec(...)                 the spec dict plank_door / the annex wall read
"""
import math  # noqa: F401

import numpy as np

from ..geom import Acc, axn, fbm90, finalize, frame_matrix, lathe_rz, n1, prof_circle, prof_rect, rbox_v, sweep
from .hewn import hewn_square, nail_heads, peg
from .oct_frame import FR, FN, FT, fmap, get_pool, place
from .oct_hall import facet_obox


def _hewn(*a, **k):
    return hewn_square(*a, relief=FR.min_relief, dropped=FR.dropped_checks, **k)


def strap_widths(us, w0=0.050, w1=0.038, spear_w=0.080, u_sp=0.80):
    """forged strap plan: 50 mm at the knuckle tapering to ~38 mm, necked, spear terminal ~80 mm wide."""
    us = np.asarray(us, float)
    wd = w0 + (w1 - w0) * np.clip(us / u_sp, 0, 1)
    s_ = np.clip((us - u_sp) / (1 - u_sp), 0, 1)
    neck = w1 - 0.008 * np.clip(s_ / 0.12, 0, 1)
    flare = (w1 - 0.008) + (spear_w - w1 + 0.008) * np.sin(0.5 * np.pi * np.clip((s_ - 0.12) / 0.33, 0, 1))
    point = spear_w + (0.012 - spear_w) * np.clip((s_ - 0.45) / 0.55, 0, 1) ** 0.9
    wd = np.where(us <= u_sp, wd, np.where(s_ < 0.12, neck, np.where(s_ < 0.45, flare, point)))
    return wd


def make_pintle(acc, i):
    """forged knuckle eye round a pintle pin, with the square shank running into the jamb (local x)."""
    rr = np.random.default_rng(6100 + i)
    V, F = lathe_rz([(0.017, -0.03), (0.0175, -0.026), (0.0175, 0.026), (0.017, 0.03)], 12, phase=rr.uniform(0, 0.5))
    acc.add(V, F, "M_iron")
    V, F = lathe_rz([(0.009, -0.095), (0.009, 0.015), (0.012 + rr.uniform(0, 0.002), 0.02), (0.0, 0.025)], 10)
    acc.add(V, F, "M_iron")
    V, F = sweep(np.array([[0.0, 0, -0.045], [0.045, 0, -0.045], [0.088, 0, -0.045 + rr.normal(0, 0.002)]]),
                 (0, 0, 1), prof_rect(0.018, 0.018, 0.003))
    acc.add(V, F, "M_iron")


def strap_hinge(acc, k, x_hinge, x_len, z, w_face, rng, nails_acc, a_ref=None, direction=-1):
    """forged strap lying flat on the door face (6 mm proud), from the hinge edge; spear terminal; knuckle."""
    n = 40
    us = np.linspace(0, 1, n)
    xs = x_hinge + direction * us * x_len
    width = strap_widths(us) * (1 + 0.04 * n1(us * 6, int(z * 100)))
    tk = 0.006 * (1 - 0.15 * us)
    zz = z + 0.002 * n1(us * 5, int(z * 37) + 3)
    path = fmap(k, xs, zz, w_face + 0.5 * tk + 0.0005 * n1(us * 9, 5), a_ref=a_ref)
    # profile: right = vertical (strap width), up = facet normal (strap thickness)
    profs = np.stack([prof_rect(wd, t_, min(0.0018, t_ * 0.3)) for wd, t_ in zip(width, tk)])
    nrm = np.array([FN[k][0], FN[k][1], 0.0])
    V, F = sweep(path, nrm, profs)
    acc.add(V, F, "M_iron")
    # knuckle (rolled eye) + pintle + shank into the jamb: pooled forged part, placed as a linked duplicate
    kp = fmap(k, np.array([x_hinge + 0.012 * -direction]), np.array([z]), np.array([w_face - 0.01]), a_ref=a_ref)[0]
    get_pool("pintle", make_pintle, 3)
    ex = np.array([FT[k][0], FT[k][1], 0.0]) * -direction
    ez = np.array([0, 0, 1.0])
    place("pintle", int(z * 10) % 3, frame_matrix(kp, ex, np.cross(ez, ex), ez), "pintle")
    # nails along the strap
    nn = int(rng.integers(6, 9))
    ui = np.linspace(0.08, 0.86, nn)
    tk_n = 0.006 * (1 - 0.15 * ui)
    P = fmap(k, x_hinge + direction * ui * x_len, z + np.where(np.arange(nn) % 2 == 0, 0.009, -0.009) * (ui < 0.8),
             w_face + tk_n, a_ref=a_ref)
    nail_heads(FR, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.0085, h=0.006)


def plank_mesh(acc, mapfn, xl_fn, xr_fn, zb_fn, zt_fn, wf_fn, thick, rl_fn, rr_fn, nv, mat, rb=0.008, rt=0.004):
    """one hand-made plank (or split part) as a closed mesh in local door coords (x along the leaf, z up, w out).
    xl_fn/xr_fn(z): edges; zb_fn/zt_fn(x): bottom / top ends; wf_fn(x, z): front face height before arris wear;
    rl_fn/rr_fn(z): arris radius at the left / right edge (0 = square, flush with a neighbour part)."""
    v = np.linspace(0, 1, nv)
    xm0 = 0.5 * (xl_fn(np.array([1.0]))[0] + xr_fn(np.array([1.0]))[0])
    zb_m, zt_m = float(zb_fn(np.array([xm0]))[0]), float(zt_fn(np.array([xm0]))[0])
    zr = zb_m + v * (zt_m - zb_m)
    # extra rows for the rounded bottom and top arrises
    zr = np.concatenate([[zb_m, zb_m + 0.3 * rb, zb_m + rb], zr[1:-1], [zt_m - rt, zt_m - 0.3 * rt, zt_m]])
    zr = np.sort(zr)
    nr = len(zr)
    XL, XR = xl_fn(zr), xr_fn(zr)
    RL, RR = rl_fn(zr), rr_fn(zr)
    cl = np.array([0.0, 0.3, 1.0])
    inner = np.linspace(0, 1, 6)[1:-1]
    cols = []
    for c in cl:
        cols.append((XL + c * RL, RL - np.sqrt(np.maximum(RL ** 2 - (RL - c * RL) ** 2, 0))))
    for f in inner:
        cols.append(((XL + RL) + f * ((XR - RR) - (XL + RL)), np.zeros(nr)))
    for c in cl[::-1]:
        cols.append((XR - c * RR, RR - np.sqrt(np.maximum(RR ** 2 - (RR - c * RR) ** 2, 0))))
    nc = len(cols)
    X = np.stack([c[0] for c in cols], 1)          # (nr, nc)
    DROP = np.stack([c[1] for c in cols], 1)
    # re-map rows per column so the bottom / top follow the (uneven / arched) ends
    zb = zb_fn(X[0])
    zt = zt_fn(X[-1])
    t = (zr - zb_m) / max(zt_m - zb_m, 1e-6)
    tz = np.clip(t, 0, 1)[:, None]
    # keep the small arris rows at a fixed metric distance from the ends
    Z = zb[None, :] + tz * (zt - zb)[None, :]
    Z[1] = zb + 0.3 * rb
    Z[2] = zb + rb
    Z[-2] = zt - 0.3 * rt
    Z[-3] = zt - rt
    # end-arris drops
    endd = np.zeros_like(Z)
    endd[0] = rb
    endd[1] = rb - math.sqrt(rb * rb - (0.7 * rb) ** 2)
    endd[-1] = rt
    endd[-2] = rt - math.sqrt(rt * rt - (0.7 * rt) ** 2)
    W = wf_fn(X, Z) - np.maximum(DROP, endd)
    Vf = np.stack([X, Z, W], -1)
    # back face: edges only
    Wb = wf_fn(X[:, [0, -1]], Z[:, [0, -1]]) * 0 + (np.mean(wf_fn(X, Z)) - thick)
    Vb = np.stack([X[:, [0, -1]], Z[:, [0, -1]], Wb], -1)
    V = np.concatenate([Vf.reshape(-1, 3), Vb.reshape(-1, 3)])
    fi = lambda r, c: r * nc + c
    bi = lambda r, c: nr * nc + r * 2 + c
    F = []
    for r in range(nr - 1):
        for c in range(nc - 1):
            F.append((fi(r, c), fi(r, c + 1), fi(r + 1, c + 1), fi(r + 1, c)))
        F.append((bi(r, 0), bi(r + 1, 0), bi(r + 1, 1), bi(r, 1)))
        F.append((fi(r, 0), fi(r + 1, 0), bi(r + 1, 0), bi(r, 0)))
        F.append((fi(r, nc - 1), bi(r, 1), bi(r + 1, 1), fi(r + 1, nc - 1)))
    F = [np.array(F)]
    F.append(np.array([[fi(0, c) for c in range(nc)] + [bi(0, 1), bi(0, 0)]]))
    F.append(np.array([[fi(nr - 1, c) for c in range(nc)] + [bi(nr - 1, 1), bi(nr - 1, 0)]])[:, ::-1])
    Wd = mapfn(V[:, 0], V[:, 1], V[:, 2])
    acc.add(Wd, F, mat, uv=np.stack([V[:, 1], V[:, 0]], -1))


def plank_leaf(acc, mapfn, x0, x1, zb0, zt_fn, w_front, thick, rng, widths, split=None, rot_corner=None, mat="M_timber",
               nv=70, seed=0, relief=None):
    """vertical-plank door leaf: widths (m) left->right; split=(plank index, gap m, length m); rot_corner=('L'|'R',
    depth m) rots back the bottom corner of the outermost plank on that side.
    Producer note 11 (relief(P) -> threshold at the leaf centre): the plank cup (2-4 mm), grain (1.6 mm) and fine
    adze marks are not modelled below it; the plank-to-plank offsets, V-chamfered joints, uneven bottom ends, the
    split and the rotted corner (discrete pieces, joints, outline) always are."""
    xs = x0 + np.concatenate([[0], np.cumsum(widths)]) * (x1 - x0) / np.sum(widths)
    n = len(widths)
    xm_ = 0.5 * (x0 + x1)
    thr = 0.0 if relief is None else float(relief(mapfn(np.array([xm_]), np.array([zb0 + 1.0]),
                                                         np.array([w_front])))[0])
    k_cup = 1.0 if 0.004 >= thr else 0.0
    k_grain = 1.0 if 0.0016 >= thr else 0.0
    offs = rng.uniform(0.001, 0.003, n) * np.where(rng.uniform(0, 1, n) < 0.5, -1, 1)

    def zb_base(x, i):
        z = zb0 + 0.011 + 0.009 * n1(x * 9.0, seed + 7 * i)
        if rot_corner is not None:
            side, dep = rot_corner
            if (side == "L" and i == 0) or (side == "R" and i == n - 1):
                xe = xs[0] if side == "L" else xs[-1]
                d = np.abs(np.asarray(x) - xe)
                z = z + dep * np.clip(1 - d / 0.11, 0, 1) ** 1.4 * (1 + 0.25 * n1(np.asarray(x) * 40, seed + 3))
        return z
    for i in range(n):
        a, b = xs[i] + 0.0006, xs[i + 1] - 0.0006
        cup = rng.uniform(0.002, 0.004)
        rp = rng.uniform(0.003, 0.006)
        wo = offs[i]
        sd = seed * 10 + i

        def wf(x, z, a=a, b=b, cup=cup, wo=wo, sd=sd):
            u = (np.asarray(x) - a) / (b - a)
            grain = 0.0016 * fbm90(np.stack([np.asarray(x) * 14.0, np.asarray(z) * 2.2, np.full(np.shape(x), sd * 1.7)], -1), 2)
            grain = grain + 0.0007 * np.sin((np.asarray(x) - a) * 120.0 + 2.0 * n1(np.asarray(z) * 1.5, sd + 2))
            adze = 0.0008 * np.sin(np.asarray(z) * 23.0 + sd) * np.cos(np.asarray(x) * 31.0)
            return w_front + wo - k_cup * cup * (1 - (2 * np.clip(u, 0, 1) - 1) ** 2) + k_grain * (grain + adze)

        def rr_z(z, rp=rp):
            return rp + (0.0095 - rp) * np.clip(1 - (np.asarray(z) - zb0) / 0.3, 0, 1)
        zb_f = lambda x, i=i: zb_base(x, i)
        if split is not None and split[0] == i:
            _, g0, Ls = split
            xsp = a + (b - a) * rng.uniform(0.38, 0.5)
            gap = lambda z: g0 * np.clip(1 - (np.asarray(z) - zb0) / Ls, 0, 1) ** 0.8
            wig = lambda z: 0.003 * n1(np.asarray(z) * 6.0, sd + 5)
            rs = lambda z: np.where(gap(z) > 0.0004, 0.0018, 0.0)
            plank_mesh(acc, mapfn, lambda z: np.full(np.shape(z), a), lambda z: xsp + wig(z) - 0.5 * gap(z) + 0.0003,
                       zb_f, zt_fn, wf, thick, rr_z, rs, nv, mat)
            plank_mesh(acc, mapfn, lambda z: xsp + wig(z) + 0.5 * gap(z) - 0.0003, lambda z: np.full(np.shape(z), b),
                       zb_f, zt_fn, wf, thick, rs, rr_z, nv, mat)
        else:
            plank_mesh(acc, mapfn, lambda z: np.full(np.shape(z), a), lambda z: np.full(np.shape(z), b), zb_f, zt_fn,
                       wf, thick, rr_z, rr_z, nv, mat)
    return xs


def build_main_door(coll, seed=808):
    rng = np.random.default_rng(seed)
    op = FR.OPENINGS[0]
    k, xc, hw, zs = op["k"], op["xc"], op["hw"], op["zs"]
    acc = Acc(FR.prefix + "_door_leaf")
    acci = Acc(FR.prefix + "_door_ironwork")
    R = hw + 0.03
    w_front = -op["depth"]
    w_back = w_front - 0.04
    zb0 = op["z0"] + 0.006
    widths = rng.permutation(np.array([0.13, 0.18, 0.145, 0.172, 0.135, 0.16, 0.176]))
    zt_fn = lambda x: zs + np.sqrt(np.maximum(R * R - (np.asarray(x) - xc) ** 2, 0.0)) - 0.004
    xs = plank_leaf(acc, lambda x, z, w: fmap(k, x, z, w), xc - R, xc + R, zb0 - 0.006, zt_fn, w_front, 0.04, rng,
                    widths, split=(2, 0.0048, 0.62), rot_corner=("L", 0.042), mat="M_timber", nv=72, seed=11,
                    relief=FR.min_relief)
    # ledges on the back
    for zl, half in ((0.42, R - 0.06), (1.12, R - 0.06), (1.78, R - 0.12)):
        facet_obox(acc, k, xc - half, xc + half, zl - 0.07, zl + 0.07, w_back - 0.04, w_back, 0.01, "M_timber", nx=6)
    # strap hinges (hinge side = +x edge)
    for zh, ln in ((0.42, 0.78), (1.12, 0.78), (1.80, 0.62)):
        strap_hinge(acci, k, xc + R - 0.005, ln, zh, w_front + 0.0032, rng, acci)
    # clinch nails along ledge lines (one per plank, two rows offset)
    pts = []
    for zl in (0.42, 1.12):
        for i in range(7):
            xm = 0.5 * (xs[i] + xs[i + 1])
            if xm > xc + R - 0.78 - 0.02:
                continue
            for dz in (-0.035, 0.035):
                pts.append((xm + rng.normal(0, 0.008), zl + dz + rng.normal(0, 0.004)))
    for zl in (0.80, 1.48):
        for i in range(7):
            xm = 0.5 * (xs[i] + xs[i + 1])
            pts.append((xm + rng.normal(0, 0.008), zl + rng.normal(0, 0.004)))
    pts = np.array(pts)
    P = fmap(k, pts[:, 0], pts[:, 1], np.full(len(pts), w_front + 0.0025))
    nail_heads(FR, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.008, h=0.006)
    # ring pull with backplate, keyhole escutcheon
    hx_ = xc - R + 0.17
    bp = fmap(k, np.array([hx_]), np.array([1.02]), np.array([w_front + 0.003]))[0]
    nrm = np.array([FN[k][0], FN[k][1], 0.0])
    tan = np.array([FT[k][0], FT[k][1], 0.0])
    V, F = lathe_rz([(0.055, 0.0), (0.055, 0.004), (0.045, 0.007), (0.02, 0.009), (0.012, 0.022), (0.0, 0.024)], 20)
    W = bp + V[:, 0:1] * tan + V[:, 1:2] * np.array([0, 0, 1.0]) + V[:, 2:3] * nrm
    acci.add(W, F, "M_iron")
    ring_c = bp + nrm * 0.03 - np.array([0, 0, 0.06])
    a = np.linspace(0, 2 * np.pi, 25)
    ring = ring_c + 0.062 * (np.cos(a)[:, None] * tan + np.sin(a)[:, None] * np.array([0, 0, 1.0])) + \
        nrm * 0.004 * np.sin(a)[:, None]
    V, F = sweep(ring, nrm, prof_circle(0.0085, 8), caps=False)
    acci.add(V, F, "M_iron")
    # keyhole plate: a frame of four small plates around a slot
    kz = 0.90
    for (xa, xb, za, zb2) in ((-0.025, 0.025, kz + 0.025, kz + 0.06), (-0.025, 0.025, kz - 0.06, kz - 0.022),
                              (-0.025, -0.006, kz - 0.022, kz + 0.025), (0.006, 0.025, kz - 0.022, kz + 0.025)):
        facet_obox(acci, k, hx_ + xa, hx_ + xb, za, zb2, w_front, w_front + 0.0065, 0.0015, "M_iron", nx=4, ny=4, nz=3)
    nail_heads(FR, fmap(k, np.array([hx_, hx_]), np.array([kz + 0.048, kz - 0.048]), np.array([w_front + 0.0065] * 2)),
               nrm, rad=0.005, h=0.004)
    finalize(acc, coll)
    finalize(acci, coll)


def build_wall_openings(coll, door=None, window=None, seed=1212):
    """plank door (frame, leaf, ironwork, threshold) and / or small timber window in the wing's S wall, from the
    door / window spec dicts (see plank_door() and window())."""
    rng = np.random.default_rng(seed)
    acc = Acc(FR.prefix + "_wing_door")
    acci = Acc(FR.prefix + "_wing_door_ironwork")
    accw = Acc(FR.prefix + "_wing_window")
    d = door if door is not None else FR.WDOOR
    # local frame on the south wall (plumb): x east, w outward (-y), z up
    yface = FR.WY_S
    thr = float(FR.min_relief(np.array([[d["xc"], yface, 1.0]]))[0])
    k_adze = 1.0 if 0.003 >= thr else 0.0           # producer note 11: 3 mm adze marks -> materials

    def adze(P, seed=0):
        P = P.copy()
        P[:, 2] += k_adze * 0.003 * np.sin(P[:, 1] * 13 + seed) * (P[:, 2] > -0.25)
        return P

    def wl(x, z, w):
        x = np.asarray(x, float)
        return np.stack([x, np.full_like(x, yface) - np.asarray(w, float), np.asarray(z, float)], -1)

    def box(a, x0, x1, z0, z1, w0, w1, r, mat, nx=4, ny=4, nz=4, deform=None):
        X = axn(np.array([x0]), np.array([x1]), np.array([r]), nx)
        Y = axn(np.array([z0]), np.array([z1]), np.array([r]), ny)
        Z = axn(np.array([w0]), np.array([w1]), np.array([r]), nz)
        P, quads = rbox_v(X, Y, Z, np.array([r]))
        P = P[0]
        if deform is not None:
            P = deform(P)
        a.add(wl(P[:, 0], P[:, 1], P[:, 2]), quads, mat, uv=np.stack([P[:, 1], P[:, 0] + P[:, 2]], -1))

    if door is not None:
        xc, hw, fw = d["xc"], d["hw"], d["fw"]
        wf0, wf1 = -d["depth"] - 0.20, -d["depth"]          # frame depth range (w)
        z0, z1 = d["z0"], d["z1"]

        # jambs, lintel, sill-beam
        # hand-hewn jambs and lintel (adze facets, slight lean/wave, a modelled check in the lintel face)
        EXo, EYo, EZo = np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, -1.0, 0])
        for jx, sd_ in ((xc - hw - fw / 2, 1), (xc + hw + fw / 2, 2)):
            _hewn(acc, wl(jx, -0.02, 0.5 * (wf0 + wf1)), np.array([0, 0, 1.0]), EXo, EZo, z1 + fw + 0.02, fw,
                        wf1 - wf0, rng, chamfer=0.022, nf=3, st_len=0.05, adze=0.004,
                        lean=(rng.normal(0, 0.006), 0.0), swell=rng.uniform(-0.006, 0.006), seed=500 + sd_,
                        checks=[dict(face=1, pos=rng.uniform(-0.3, 0.3), x0=0.2, x1=0.7, depth=0.012, width=0.006)])
        lw0, lw1_ = wf0 - 0.05, wf1 + 0.17
        _hewn(acc, wl(xc - hw - fw - 0.22, z1 + 0.12, 0.5 * (lw0 + lw1_)), EXo, EYo, EZo,
                    2 * hw + 2 * fw + 0.46, 0.23, lw1_ - lw0, rng, chamfer=0.025, nf=4, st_len=0.04, adze=0.005,
                    wave=0.006, seed=510,
                    checks=[dict(face=1, pos=0.15, x0=0.12, x1=0.62, depth=0.018, width=0.009),
                            dict(face=1, pos=-0.4, x0=0.55, x1=0.9, depth=0.010, width=0.005)])
        for xx in (xc - hw - fw / 2, xc + hw + fw / 2):
            for zz in (z1 + 0.12,):
                p = wl(np.array([xx]), np.array([zz]), np.array([wf1 + 0.17]))[0]
                peg(FR, p, np.array([0, -1.0, 0]))
        # stone threshold at +0.10
        box(acc, xc - hw - fw - 0.05, xc + hw + fw + 0.05, -0.08, z0, -0.62, 0.10, 0.02, "M_stone_dressed", nx=8, ny=3, nz=6,
            deform=lambda P: P + np.stack([np.zeros(len(P)), -0.01 * (0.01 >= thr) * (1 - ((P[:, 0] - xc) / 0.7) ** 2) * (P[:, 1] > 0.0), np.zeros(len(P))], 1))
        # plank leaf (7 planks) set in the frame
        lw0, lw1 = wf0 + 0.06, wf0 + 0.10
        widths = rng.permutation(np.array([0.135, 0.17, 0.15, 0.13, 0.165, 0.142, 0.158]))
        plank_leaf(acc, wl, xc - hw - 0.015, xc + hw + 0.015, z0 - 0.003, lambda x: np.full(np.shape(x), z1 + 0.02), lw1,
                   lw1 - lw0, rng, widths, split=(4, 0.0042, 0.48), rot_corner=("R", 0.036), mat="M_timber_weathered",
                   nv=60, seed=23, relief=FR.min_relief)
        for zl in (0.42, 1.15, 1.92):
            box(acc, xc - hw + 0.03, xc + hw - 0.03, zl - 0.07, zl + 0.07, lw0 - 0.04, lw0, 0.01, "M_timber_weathered")
        # three strap hinges (hinge on the west side = -x), latch on +x
        for zh in (0.42, 1.15, 1.92):
            n = 36
            us = np.linspace(0, 1, n)
            xsx = xc - hw + 0.01 + us * 0.70
            wd = strap_widths(us, 0.048, 0.036, 0.074) * (1 + 0.04 * n1(us * 6, int(zh * 50)))
            tk = 0.006 * (1 - 0.15 * us)
            path = wl(xsx, zh + 0.002 * n1(us * 5, int(zh * 31)), lw1 + 0.0032 + 0.5 * tk)
            # profile: right = vertical strap width, up = outward normal (thickness) -> lies flat on the planks
            profs = np.stack([prof_rect(w_, t_, 0.0015) for w_, t_ in zip(wd, tk)])
            V, F = sweep(path, (0, -1, 0), profs)
            acci.add(V, F, "M_iron")
            ui = np.array([0.08, 0.28, 0.48, 0.66, 0.9])
            nail_heads(FR, wl(xc - hw + 0.01 + ui * 0.70, zh + np.array([0.008, -0.008, 0.008, -0.008, 0.0]),
                                lw1 + 0.0032 + 0.006 * (1 - 0.15 * ui)), np.array([0, -1.0, 0]), rad=0.008)
            kp = wl(np.array([xc - hw + 0.005]), np.array([zh]), np.array([lw1 - 0.008]))[0]
            get_pool("pintle", make_pintle, 3)
            ex = np.array([-1.0, 0, 0])
            place("pintle", int(zh * 10) % 3, frame_matrix(kp, ex, np.cross(np.array([0, 0, 1.0]), ex),
                                                           np.array([0, 0, 1.0])), "pintle")
        # latch: thumb latch handle + bar
        hp = wl(np.array([xc + hw - 0.12]), np.array([1.05]), np.array([lw1]))[0]
        path = np.array([hp + np.array([0, 0, 0.09]), hp + np.array([0, -0.05, 0.06]), hp + np.array([0, -0.06, 0.0]),
                         hp + np.array([0, -0.05, -0.06]), hp + np.array([0, 0, -0.09])])
        V, F = sweep(path, (1, 0, 0), prof_rect(0.016, 0.01, 0.003))
        acci.add(V, F, "M_iron")
        for dz in (0.09, -0.09):
            V, F = lathe_rz([(0.022, 0.0), (0.022, 0.004), (0.0, 0.006)], 10)
            acci.add(np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1) + hp + np.array([0, -0.0, dz]), F, "M_iron")
    if window is not None:
        # window (wing south wall, clear of the turret): 0.07 m timber frame round a 0.45 x 0.55 clear opening with a
        # mullion, set 0.16 m back in the reveal; timber lintel above, projecting stone sill with a drip below; a dark
        # blocker room 1.0 m inside closes the view through it
        w = window
        xw, hww, fwn = w["xc"], w["hw"], w["fw"]
        wz0, wz1 = w["z0"], w["z1"]
        fd0, fd1 = -w["depth"] - 0.10, -w["depth"]
        box(accw, xw - hww - fwn, xw - hww, wz0 - fwn, wz1 + fwn, fd0, fd1, 0.01, "M_timber", ny=6)
        box(accw, xw + hww, xw + hww + fwn, wz0 - fwn, wz1 + fwn, fd0, fd1, 0.01, "M_timber", ny=6)
        box(accw, xw - hww - 0.004, xw + hww + 0.004, wz1, wz1 + fwn, fd0, fd1 - 0.004, 0.01, "M_timber", nx=6)
        box(accw, xw - hww - 0.004, xw + hww + 0.004, wz0 - fwn, wz0, fd0, fd1 - 0.004, 0.01, "M_timber", nx=6)
        box(accw, xw - 0.024, xw + 0.024, wz0 - 0.005, wz1 + 0.005, fd0 + 0.02, fd1 - 0.02, 0.008, "M_timber", ny=6)
        for zz in (wz0 - fwn / 2, wz1 + fwn / 2):
            for xx in (xw - hww - fwn / 2, xw + hww + fwn / 2):
                peg(FR, wl(np.array([xx]), np.array([zz]), np.array([fd1]))[0], np.array([0, -1.0, 0]), rad=0.009,
                    proud=0.007)
        box(accw, xw - hww - 0.30, xw + hww + 0.30, wz1 + fwn, wz1 + fwn + 0.17, -0.45, 0.03, 0.02, "M_timber", nx=6,
            deform=lambda P: adze(P, 7))
        box(accw, xw - hww - 0.16, xw + hww + 0.16, wz0 - fwn - 0.11, wz0 - fwn - 0.004, -0.30, 0.07, 0.012,
            "M_stone_dressed", nx=6)
        # blocker room 1.0 m inside (open toward the window)
        xa_, xb_ = xw - hww - 0.30, xw + hww + 0.30
        za_, zb_ = wz0 - 0.55, wz1 + 0.75
        Pb = np.array([(xa_, za_, -0.62), (xb_, za_, -0.62), (xb_, zb_, -0.62), (xa_, zb_, -0.62),
                       (xa_, za_, -1.0), (xb_, za_, -1.0), (xb_, zb_, -1.0), (xa_, zb_, -1.0)])
        Vb = wl(Pb[:, 0], Pb[:, 1], Pb[:, 2])
        accw.add(Vb, [np.array([[4, 5, 6, 7], [0, 1, 5, 4], [3, 2, 6, 7], [0, 3, 7, 4], [1, 5, 6, 2]])], "M_mortar")
    finalize(acc, coll)
    finalize(acci, coll)
    finalize(accw, coll)



def door_spec(xc=-5.05, width=1.0, height=2.10, frame=0.18, depth=0.20, threshold=0.10):
    """rectangular plank door spec (clear width / height, frame section, set-back, threshold top).
    kit 1.8.0: a thin wrapper of components.openings (family "annex"; the unambiguous name is openings.annex_door,
    the family-neutral spec openings.door(...).at(xc))."""
    from .openings import annex_door
    return annex_door(xc=xc, width=width, height=height, frame=frame, depth=depth, threshold=threshold)


def arched_door(g, seed=808):
    """KIT COMPONENT: arch-topped plank leaf and ironwork in the principal arched opening."""
    build_main_door(g.sub("hall"), seed=seed)


def plank_door(g, seed=1212):
    """KIT COMPONENT: the annex's rectangular plank door (g.WDOOR)."""
    build_wall_openings(g.sub("wing"), door=g.WDOOR, window=None, seed=seed)
