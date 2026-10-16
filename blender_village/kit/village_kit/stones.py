"""village_kit.stones -- ONE stone generator for the whole village, parameterised by style.

    V, F = make_stone(style, rng, **params)        # local coords; F is a list of face arrays (quads / tris)

Styles (see STYLES for the defaults of each):
  rubble          flat-bedded split rubble for coursed walls: planar beds, pillowed face, tilted ends, 0-2 crisp
                  fracture planes, 1-3 cm worn arrises                                  (keep / mill walls)
  dressed         squared dressed stone (surrounds, quoins, string courses): flat faces, ~1 cm chamfer
  voussoir        dressed wedge for round / segmental arches: ends tilted by the wedge angle, thicker at the crown
  footing         large projecting footing / field stone (crowned top, bulging front)  (field_stone)
  plinth_slab     dry-stone plinth slab   } flat-bedded / blocky / sub-rounded hut plinth stones with planar
  plinth_block    dry-stone plinth block  } fracture faces and a hand-split skin          (plinth_kind_stone)
  plinth_boulder  dry-stone plinth boulder}
  pad             low, wide post pad stone with a flat tilted bearing bed                (pad_stone)
  spall           small split spall / pinning stone of 5-8 planar fracture faces         (spall_stone)
  chink           flat wedge chinking stone for open dry-stone joints                    (chink_stone)
  boulder         superellipsoid field boulder (crown, bulge, fracture facets)           (boulder)
  flag            open-shell flag / threshold / step slab from an outline (shell_stone, face +w)
  hearth          small rounded box stone (hearth rings)                                 (box_stone)

Local frame for wall stones: x along the wall, y out of the wall (exposed face +y), z up, centred on 0.
Every generator is deterministic for a given np.random.RandomState.

Detail-scale rule (producer note 11): the hand-split SKIN (conchoidal flake scars 4-10 mm, lumps 1-1.4 cm, pits)
is sub-2 cm relief.  stone_skin(min_relief=...) and the plinth / pad styles take `min_relief`: skin components
shallower than it are not modelled (materials / decals carry them).  min_relief=0 keeps the full phase-1 skin.
Stone SHAPE (facets, fracture planes, arris chips >= 1-2 cm) is always modelled.
"""
import math

import numpy as np

from .core import (nrm, vnoise, fbm, ring_noise, smoothstep, rbox, rbox2, smin, _spow, grid_quads, vert_normals, xf)

def box_stone(half, r_frac, segs, rng, amp=0.02, freq=3.0, flat_top=None, flat_bot=None, facets=(3, 6),
          warp=0.14, taper=(0.0, 0.18)):
    """irregular sub-angular stone in local coords (bedding face down)."""
    h = np.asarray(half, float)
    r = min(r_frac, 0.95) * float(h.min())
    P, F = rbox(h, r, segs, chamfer=False)
    off = rng.uniform(-100, 100, 3)
    q = P / h
    # low-frequency body warp (no two stones alike)
    wv = np.stack([vnoise(q * 0.85 + off + k * 17.3) for k in range(3)], -1)
    P = P + wv * h * warp
    # slightly narrower at the top
    tp = rng.uniform(*taper)
    P[:, :2] *= (1 - tp * (0.5 + 0.5 * q[:, 2:3]))
    # sub-angular: knock off random facets
    for _ in range(rng.randint(facets[0], facets[1] + 1)):
        nv = nrm(rng.normal(size=3) * [1.0, 1.0, 0.7])
        proj = P @ nv
        cut = proj.max() * rng.uniform(0.70, 0.88)
        over = proj - cut
        m = over > 0
        P[m] -= nv * (over[m] * rng.uniform(0.82, 0.96))[:, None]
    dirn = nrm(P / h)
    d = fbm(P * freq + off, 3) * amp + fbm(P * freq * 3.1 + off * 1.7, 2) * amp * 0.35
    P = P + dirn * d[:, None]
    if flat_top is not None:
        P[:, 2] = np.minimum(P[:, 2], flat_top + (P[:, 2] - flat_top) * 0.15)
    if flat_bot is not None:
        P[:, 2] = np.maximum(P[:, 2], flat_bot)
    return P, F


def rock(half, rng, round_r=0.03, facets=(3, 6), segs=(9, 7, 6), warp=0.05, amp=0.005, freq=4.0,
         flat_top=None, flat_bot=None, fillet=0.018, face_bias=None, chips=0, pit=0.0015, batter=0.0,
         bias_p=0.6, face_cuts=0, nz_w=0.55):
    """sub-angular split stone: small corner rounding, 3-6 big flat fracture facets with soft
    fillets, flat bedding faces, faint low-frequency undulation. local coords, bedding face down.
    face_bias: optional unit vector; facets are biased toward it (e.g. the exposed face)."""
    h = np.asarray(half, float)
    P, F = rbox2(h, round_r, segs)
    off = rng.uniform(-100, 100, 3)
    q = P / h
    wv = np.stack([vnoise(q * 0.7 + off + k * 17.3) for k in range(3)], -1)
    P = P + wv * h * warp
    nf = rng.randint(facets[0], facets[1] + 1)
    for _ in range(nf):
        nv = rng.normal(size=3) * [1.0, 1.0, nz_w]
        if face_bias is not None and rng.rand() < bias_p:
            nv = np.asarray(face_bias, float) * 1.0 + rng.normal(size=3) * [0.7, 0.6, 0.6]
        nv = nrm(nv)
        proj = P @ nv
        cut = proj.max() - (proj.max() - proj.min()) * rng.uniform(0.06, 0.2)
        newp = smin(proj, cut, fillet)
        P = P + nv * (newp - proj)[:, None]
    for _ in range(face_cuts):
        fb = nrm(np.asarray(face_bias if face_bias is not None else (0, -1, 0), float))
        ax_ = nrm(np.cross(fb, rng.normal(size=3)))
        an_ = rng.uniform(0.25, 0.65)
        nv = nrm(fb * math.cos(an_) + np.cross(ax_, fb) * math.sin(an_))
        proj = P @ nv
        cut = proj.max() - (proj.max() - proj.min()) * rng.uniform(0.04, 0.12)
        P = P + nv * (smin(proj, cut, fillet * 0.7) - proj)[:, None]
    for _ in range(chips):
        # small conchoidal chip off a top edge
        az = rng.uniform(0, 2 * np.pi)
        nv = nrm(np.array([math.cos(az), math.sin(az), rng.uniform(0.7, 1.3)]))
        proj = P @ nv
        cut = proj.max() - rng.uniform(0.012, 0.03)
        P = P + nv * (smin(proj, cut, 0.006) - proj)[:, None]
    dirn = nrm(P / h)
    d = fbm(P * freq + off, 3) * amp + vnoise(P * freq * 4.3 + off * 1.7) * pit
    P = P + dirn * d[:, None]
    if flat_top is not None:
        P[:, 2] = np.where(P[:, 2] > flat_top, flat_top + (P[:, 2] - flat_top) * 0.12, P[:, 2])
    if flat_bot is not None:
        P[:, 2] = np.maximum(P[:, 2], flat_bot)
    if batter:
        P[:, 1] += batter * (P[:, 2] / h[2] + 1) / 2          # face leans back toward the top
    return P, F


def boulder(half, rng, p_h=3.2, p_v=2.6, crown=0.05, crown_c=(0.25, -0.2), bulge=0.04, n_frac=0, frac_k=0.003,
            frac_cut=(0.08, 0.2), frac_bias=None, warp=0.07, amp=0.004, freq=7.0, pit=0.0015, taper=0.12,
            nu=30, nv=14, chips=0, bed=None, bed_k=0.006):
    """field boulder / split stone in local coords: x along, y outward (face side), z up, centred on 0.
    Superellipsoid body (curved everywhere: no planar area), a crowned top whose high point is
    off-centre (crown_c, normalised x/y), a bulging front (+y), sloping sides (taper), low-frequency
    warp, optional crisp fracture facets (smooth-min plane cuts, fillet frac_k), small arris chips,
    pitting.  bed: optional flat bearing cut at that height (post bed).  Returns V (K,3), [faces]."""
    a, b, c = (float(v) for v in half)
    th = 2 * np.pi * (np.arange(nu) + 0.5) / nu
    ph = np.linspace(-np.pi / 2, np.pi / 2, nv + 2)[1:-1]
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    eh, ev = 2.0 / p_h, 2.0 / p_v
    cp = _spow(np.cos(PH), ev)
    X = a * cp * _spow(np.cos(TH), eh)
    Y = b * cp * _spow(np.sin(TH), eh)
    Z = c * _spow(np.sin(PH), ev)
    P = np.concatenate([np.stack([X, Y, Z], -1).reshape(-1, 3), [[0, 0, -c], [0, 0, c]]])
    pb, pt = nu * nv, nu * nv + 1
    Fq = grid_quads(nu, nv, closed_u=True)
    i = np.arange(nu)
    i1 = (i + 1) % nu
    Fb = np.stack([np.full(nu, pb), i1 * nv, i * nv], -1)
    Ft = np.stack([np.full(nu, pt), i * nv + nv - 1, i1 * nv + nv - 1], -1)
    # orient outward on the undeformed (star-shaped) body
    for Fx in (Fq, Fb, Ft):
        Q = P[Fx]
        nn_ = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0])
        flip = np.sum(nn_ * Q.mean(1), -1) < 0
        Fx[flip] = Fx[flip][:, ::-1]
    q = P / np.array([a, b, c])
    # sloping sides: narrower toward the top
    P[:, :2] *= (1 + taper * 0.5 - taper * (q[:, 2:3] + 1) / 2)
    # crowned top, high point off-centre
    wt = np.clip(q[:, 2], 0, 1) ** 1.3
    dd = (q[:, 0] - crown_c[0]) ** 2 + (q[:, 1] - crown_c[1]) ** 2 * 0.8
    P[:, 2] += crown * wt * np.clip(1 - 0.75 * dd, -0.3, 1)
    # bulging front
    wf = np.clip(q[:, 1], 0, 1) ** 1.2
    P[:, 1] += bulge * wf * np.clip(1 - q[:, 0] ** 2, 0, 1) * np.sqrt(np.clip(1 - q[:, 2] ** 2, 0, 1))
    off = rng.uniform(-100, 100, 3)
    wv = np.stack([vnoise(q * 0.8 + off + k * 17.3) for k in range(3)], -1)
    P = P + wv * np.array([a, b, c]) * warp
    for _ in range(n_frac):
        if frac_bias is not None and rng.rand() < 0.75:
            nv_ = np.asarray(frac_bias, float) + rng.normal(size=3) * [0.6, 0.35, 0.5]
        else:
            nv_ = rng.normal(size=3) * [1.0, 1.0, 0.8]
        nv_ = nrm(nv_)
        proj = P @ nv_
        cut = proj.max() - (proj.max() - proj.min()) * rng.uniform(*frac_cut)
        P = P + nv_ * (smin(proj, cut, frac_k) - proj)[:, None]
    for _ in range(chips):
        az = rng.uniform(0, 2 * np.pi)
        nv_ = nrm(np.array([math.cos(az), math.sin(az), rng.uniform(0.6, 1.2)]))
        proj = P @ nv_
        cut = proj.max() - rng.uniform(0.012, 0.03)
        P = P + nv_ * (smin(proj, cut, 0.004) - proj)[:, None]
    if bed is not None:
        P[:, 2] = smin(P[:, 2], bed, bed_k)
    dirn = nrm(P / np.array([a, b, c]))
    d = fbm(P * freq + off, 3) * amp + vnoise(P * freq * 4.3 + off * 1.7) * pit
    P = P + dirn * d[:, None]
    return P, [Fq, Fb, Ft]


def sdf_stone(half, rng, crown=0.05, crown_c=(0.3, -0.3), bulge=0.04, end_slope=(0.15, 0.15), tilt=(0.0, 0.0),
              n_frac=0, frac_bias=None, frac_cut=(0.08, 0.18), k_round=0.012, k_frac=0.004, lump=0.008,
              lump_f=4.5, pit=0.0015, nu=40, nv=20, bed=None, chips=0, yaw_front=0.0, back_open=False, spalls=0):
    """sub-angular stone as an implicit surface, meshed by ray-bisection from its centre (star-shaped).
    Separate bounding surfaces -- a CROWNED top (high point off-centre), a BULGING front (+y), sloping
    ends, back and bed -- are joined by a log-sum-exp smooth max, so the arrises are rounded with a
    radius of a few cm (k_round) while the faces keep their own gentle curvature (no dome, no
    plateau).  Optional crisp fracture planes (k_frac), arris chips and a flat bearing bed.  Each
    surface carries its own low-frequency lumps (lump, ~lump_f cycles/m).  Local: x along, y out, z up."""
    a, b, c = (float(v) for v in half)
    off = rng.uniform(-100, 100, 3)
    fr_l = []
    for _ in range(n_frac):
        if frac_bias is not None and rng.rand() < 0.75:
            nv_ = np.asarray(frac_bias, float) + rng.normal(size=3) * [0.6, 0.35, 0.5]
        else:
            nv_ = rng.normal(size=3) * [1.0, 1.0, 0.8]
        nv_ = nrm(nv_)
        ext = abs(nv_[0]) * a + abs(nv_[1]) * b + abs(nv_[2]) * c
        fr_l.append((nv_, ext * (1 - rng.uniform(*frac_cut))))
    ch_l = []
    for _ in range(chips):
        az_ = rng.uniform(0, 2 * np.pi)
        nv_ = nrm(np.array([math.cos(az_), math.sin(az_), rng.uniform(0.6, 1.2)]))
        ext = abs(nv_[0]) * a + abs(nv_[1]) * b + abs(nv_[2]) * c
        ch_l.append((nv_, ext - rng.uniform(0.02, 0.045)))
    sl0, sl1 = end_slope
    tx, ty = tilt
    cyaw = math.tan(yaw_front)

    def lumps(P, k):
        return lump * fbm(P * lump_f + off + k * 13.1, 2)

    def f(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        xn, yn, zn = x / a, y / b, z / c
        top = z - (c + crown * np.clip(1 - 0.8 * (xn - crown_c[0]) ** 2 - 0.8 * (yn - crown_c[1]) ** 2, -0.5, 1)
                   + tx * x + ty * y + lumps(P, 0))
        front = y - (b + bulge * np.clip(1 - xn ** 2, 0, 1) * np.clip(1 - 0.6 * zn ** 2, 0, 1) + cyaw * x + lumps(P, 1))
        back = -y - b
        bot = -z - c
        e_r = x - (a - sl1 * a * (zn + 1) / 2 + 0.4 * lumps(P, 2))
        e_l = -x - (a - sl0 * a * (zn + 1) / 2 + 0.4 * lumps(P, 3))
        g = [top, front, back, bot, e_r, e_l]
        if bed is not None:
            g.append(z - bed)
        G = np.stack(g, 0)
        m = G.max(0)
        F_ = m + k_round * np.log(np.sum(np.exp((G - m) / k_round), 0))
        for (nv_, d_) in fr_l:
            gg = P @ nv_ - d_
            mm = np.maximum(F_, gg)
            F_ = mm + k_frac * np.log(np.exp((F_ - mm) / k_frac) + np.exp((gg - mm) / k_frac))
        for (nv_, d_) in ch_l:
            gg = P @ nv_ - d_
            mm = np.maximum(F_, gg)
            F_ = mm + 0.003 * np.log(np.exp((F_ - mm) / 0.003) + np.exp((gg - mm) / 0.003))
        return F_

    th = 2 * np.pi * (np.arange(nu) + 0.5) / nu
    ph = np.linspace(-np.pi / 2, np.pi / 2, nv + 2)[1:-1]
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    # directions spread on a rounded box (good vertex spacing near the arrises)
    D = np.stack([_spow(np.cos(PH), 0.6) * _spow(np.cos(TH), 0.6) * a,
                  _spow(np.cos(PH), 0.6) * _spow(np.sin(TH), 0.6) * b,
                  _spow(np.sin(PH), 0.6) * c], -1).reshape(-1, 3)
    D = np.concatenate([D, [[0, 0, -c], [0, 0, c]]])
    Dn = nrm(D)
    lo = np.zeros(len(Dn))
    hi = np.full(len(Dn), 2.5 * max(a, b, c) + crown + bulge)
    for _ in range(26):
        mid = (lo + hi) / 2
        inside = f(Dn * mid[:, None]) < 0
        lo = np.where(inside, mid, lo)
        hi = np.where(inside, hi, mid)
    P = Dn * ((lo + hi) / 2)[:, None]
    # spalls: small (4-9 cm) crisp-edged planar flakes knocked off the front and top faces
    for _ in range(spalls):
        if rng.rand() < 0.6:
            cand = np.where((P[:, 1] > b * 0.55) & (np.abs(P[:, 2]) < c * 0.9))[0]
        else:
            cand = np.where(P[:, 2] > c * 0.6)[0]
        if len(cand) == 0:
            continue
        p0 = P[cand[rng.randint(len(cand))]]
        nn0 = nrm(np.array([0.0, 1.0, 0.25]) if p0[1] > b * 0.55 and p0[2] < c * 0.6 else np.array([0, 0.3, 1.0]))
        nn0 = nrm(nn0 + rng.normal(size=3) * 0.35)
        wr = rng.uniform(0.02, 0.045)
        dep = rng.uniform(0.004, 0.012)
        rr_ = np.linalg.norm((P - p0) - np.outer((P - p0) @ nn0, nn0), axis=1)
        win = np.exp(-(rr_ / wr) ** 6)
        sd = (P - p0) @ nn0 + dep
        P = P - np.outer(win * np.maximum(sd, 0), nn0)
    P = P + Dn * (pit * vnoise(P * 60.0 + off * 1.7))[:, None]
    pb, pt = nu * nv, nu * nv + 1
    Fq = grid_quads(nu, nv, closed_u=True)
    i = np.arange(nu)
    i1 = (i + 1) % nu
    Fb = np.stack([np.full(nu, pb), i1 * nv, i * nv], -1)
    Ft = np.stack([np.full(nu, pt), i * nv + nv - 1, i1 * nv + nv - 1], -1)
    for Fx in (Fq, Fb, Ft):
        Q = Dn[Fx]
        nn_ = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0])
        flip = np.sum(nn_ * Q.mean(1), -1) < 0
        Fx[flip] = Fx[flip][:, ::-1]
    return P, [Fq, Fb, Ft]


def facet_stone(half, rng, surfs, k_round=0.012, fracs=(), k_frac=0.003, lump=0.006, lump_f=4.0, pit=0.0015,
                nu=48, nv=24, chips=0, th=None, ph=None):
    """rounded polyhedral stone: the intersection of gently CURVED facets (each facet: unit normal n,
    a point p0 on it, curvature cv -> the face sags away from p0 by cv * r^2, so no facet is planar),
    joined by a log-sum-exp smooth max (arris radius ~ a few k_round), plus crisp fracture planes
    (fracs: (n, d), k_frac), small arris chips, low-frequency lumps and pitting.  Meshed by ray
    bisection from the local origin (the stone must be star-shaped about it).  Returns V, [faces]."""
    a, b, c = (float(v) for v in half)
    off = rng.uniform(-100, 100, 3)
    ch_l = []
    for _ in range(chips):
        az_ = rng.uniform(0, 2 * np.pi)
        nv_ = nrm(np.array([math.cos(az_), math.sin(az_) * 0.8 + 0.4, rng.uniform(0.6, 1.2)]))
        ch_l.append(nv_)

    def lse(G, k):
        m = G.max(0)
        return m + k * np.log(np.sum(np.exp((G - m) / k), 0))

    def f(P):
        G = []
        for i_, (n_, p0, cv) in enumerate(surfs):
            d_ = P - p0
            h = d_ @ n_
            perp2 = np.sum(d_ * d_, 1) - h * h
            G.append(h + cv * perp2 - lump * fbm(P * lump_f + off + i_ * 7.7, 2)
                     - lump * 0.35 * vnoise(P * lump_f * 2.7 + off * 0.3 + i_ * 3.1))
        # arris radius varies along the edges: crisp in places, worn round in others
        kv = k_round * (0.35 + 1.3 * np.clip(0.5 + 0.9 * vnoise(P * 5.0 + off * 0.7), 0, 1))
        F_ = lse(np.stack(G, 0), kv)
        for (n_, d0) in fracs:
            F_ = lse(np.stack([F_, P @ n_ - d0]), k_frac)
        return F_

    if th is None:
        th = 2 * np.pi * (np.arange(nu) + 0.5) / nu
    if ph is None:
        ph = np.linspace(-np.pi / 2, np.pi / 2, nv + 2)[1:-1]
    th, ph = np.asarray(th, float), np.asarray(ph, float)
    nu, nv = len(th), len(ph)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    D = np.stack([_spow(np.cos(PH), 0.6) * _spow(np.cos(TH), 0.6) * a,
                  _spow(np.cos(PH), 0.6) * _spow(np.sin(TH), 0.6) * b,
                  _spow(np.sin(PH), 0.6) * c], -1).reshape(-1, 3)
    D = np.concatenate([D, [[0, 0, -c], [0, 0, c]]])
    Dn = nrm(D)
    lo = np.zeros(len(Dn))
    hi = np.full(len(Dn), 3.0 * max(a, b, c))
    for _ in range(26):
        mid = (lo + hi) / 2
        inside = f(Dn * mid[:, None]) < 0
        lo = np.where(inside, mid, lo)
        hi = np.where(inside, hi, mid)
    P = Dn * ((lo + hi) / 2)[:, None]
    for nv_ in ch_l:                                   # arris chips: small crisp planar breaks
        proj = P @ nv_
        cut = proj.max() - rng.uniform(0.012, 0.03)
        P = P + nv_[None, :] * (smin(proj, cut, 0.003) - proj)[:, None]
    P = P + Dn * (pit * vnoise(P * 55.0 + off * 1.7))[:, None]
    pb, pt = nu * nv, nu * nv + 1
    Fq = grid_quads(nu, nv, closed_u=True)
    i = np.arange(nu)
    i1 = (i + 1) % nu
    Fb = np.stack([np.full(nu, pb), i1 * nv, i * nv], -1)
    Ft = np.stack([np.full(nu, pt), i * nv + nv - 1, i1 * nv + nv - 1], -1)
    for Fx in (Fq, Fb, Ft):
        Q = Dn[Fx]
        nn_ = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0])
        flip = np.sum(nn_ * Q.mean(1), -1) < 0
        Fx[flip] = Fx[flip][:, ::-1]
    return P, [Fq, Fb, Ft]


def field_stone(half, rng, crown=0.05, bulge=0.045, lean=(0.03, 0.14), fracture=False, bevel=(0.1, 0.3),
                k_round=0.012, lump=0.006, nu=48, nv=24, chips=1, flat_bed=None, frac_bias=(0.0, 1.0, 0.45)):
    """plinth / footing boulder (director r3 #3a) built from curved facets: a crowned top whose high
    point is off-centre (4-8 cm), a front battered back by `lean` and bulging 3-6 cm, a big rounded
    top-front bevel, two corner facets, tilted ends, back and bed; ~fracture: 1-2 crisp split planes.
    Local: x along, y out (face), z up, centred on 0.  flat_bed: optional flat bearing cut at that z."""
    a, b, c = (float(v) for v in half)
    S = []
    # top: crowned paraboloid, apex off-centre
    xc, yc = rng.uniform(-0.45, 0.45) * a, rng.uniform(-0.5, 0.1) * b
    nt = nrm(np.array([rng.uniform(-0.08, 0.08), rng.uniform(0.0, 0.12), 1.0]))
    S.append((nt, np.array([xc, yc, c]), crown / (1.3 * a) ** 2))
    # front: battered back, bulging
    nf = nrm(np.array([rng.uniform(-0.12, 0.12), 1.0, rng.uniform(*lean)]))
    S.append((nf, np.array([rng.uniform(-0.2, 0.2) * a, b, rng.uniform(-0.3, 0.1) * c]), bulge / (1.05 * a) ** 2))
    # top-front bevel: a big rounded facet across the upper front arris
    nb = nrm(np.array([rng.uniform(-0.35, 0.35), 1.0, rng.uniform(0.8, 1.5)]))
    corner = np.array([0.0, b, c])
    S.append((nb, corner - nb * (rng.uniform(*bevel) * min(b, c)), 0.25))
    # lower front tuck (slight)
    nl = nrm(np.array([0.0, 1.0, -rng.uniform(0.5, 0.9)]))
    S.append((nl, np.array([0.0, b, -c]) - nl * rng.uniform(0.05, 0.15) * min(b, c), 0.2))
    # ends (tilted) and front corner facets
    for sx in (-1.0, 1.0):
        ne = nrm(np.array([sx, rng.uniform(-0.25, 0.25), rng.uniform(0.05, 0.35)]))
        S.append((ne, np.array([sx * a, 0.0, 0.0]), 0.25))
        nc = nrm(np.array([sx, rng.uniform(0.6, 1.2), rng.uniform(0.1, 0.5)]))
        S.append((nc, np.array([sx * a, b, 0.0]) - nc * rng.uniform(0.12, 0.3) * min(a, b), 0.3))
    for _ in range(2):                      # two extra oblique facets on the visible upper front
        no = nrm(np.array([rng.uniform(-1, 1), rng.uniform(0.4, 1.0), rng.uniform(0.3, 1.0)]))
        ext = abs(no[0]) * a + abs(no[1]) * b + abs(no[2]) * c
        S.append((no, no * ext * (1 - rng.uniform(0.04, 0.1)), 0.3))
    S.append((np.array([0.0, -1.0, 0.0]), np.array([0.0, -b, 0.0]), 0.0))
    S.append((np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, -c]), 0.0))
    fr = []
    if fracture:
        for _ in range(rng.randint(1, 3)):
            nv_ = nrm(np.asarray(frac_bias, float) + rng.normal(size=3) * [0.6, 0.3, 0.5])
            ext = abs(nv_[0]) * a + abs(nv_[1]) * (b + bulge) + abs(nv_[2]) * (c + crown)
            fr.append((nv_, ext * (1 - rng.uniform(0.1, 0.22))))
    if flat_bed is not None:
        fr.append((np.array([0.0, 0.0, 1.0]), flat_bed))
    return facet_stone(half, rng, S, k_round=k_round, fracs=fr, lump=lump, nu=nu, nv=nv, chips=chips)


def dir_grid(n_front=80, n_back=16, n_up=34, n_low=8, front=(-0.45, np.pi + 0.45), ph_split=-0.35):
    """(theta, phi) direction grids for star-meshed stones, dense over the visible front / top / ends and
    sparse over the back (against the wattle) and the buried bottom (producer note 6: triangles where
    the camera goes)."""
    f0, f1 = front
    th_f = np.linspace(f0, f1, n_front, endpoint=False)
    th_b = np.linspace(f1, f0 + 2 * np.pi, n_back, endpoint=False)
    th = np.concatenate([th_f, th_b])
    ph_l = np.linspace(-np.pi / 2, ph_split, n_low + 1)[1:-1]
    ph_u = np.linspace(ph_split, np.pi / 2, n_up + 1)[:-1]
    return th, np.concatenate([ph_l, ph_u])


def stone_skin(P, faces, rng, n_scoop=(6, 12), scoop_r=(0.04, 0.10), scoop_d=(0.004, 0.010), lump_a=0.010,
               lump_f=8.0, pit_a=0.0025, vis=None, size=1.0, min_relief=0.0):
    """hand-split stone surface (director r4 #2b): shallow CONCHOIDAL flake scars -- dish-shaped, deepest
    near the impact side, ending in a crisp crease (profile (1 - r/R)^0.6 -> steep at the rim; where
    scars overlap the deeper one wins, leaving a sharp ridge between them), 1-2 cm lumps at a 10-15 cm
    wavelength and small pits.  vis(P, VN) -> weight 0..1 of 'visible face' (scars go there).
    min_relief (producer note 11): components shallower than it (lumps, each scar, pits) are not applied; the
    random draws still happen, so the stone's shape is the same with or without the skin."""
    VN = vert_normals(P, faces)
    w_vis = np.ones(len(P)) if vis is None else vis(P, VN)
    off = rng.uniform(-50, 50, 3)
    lump = lump_a * size * (lump_a * size >= min_relief) * (fbm(P * lump_f + off, 2) + 0.35 * vnoise(P * lump_f * 2.3 + off * 0.7))
    P = P + VN * lump[:, None]
    cand = np.where(w_vis > 0.5)[0]
    n_s = rng.randint(n_scoop[0], n_scoop[1] + 1) if len(cand) else 0
    for _ in range(n_s):
        # one flake scar: a near-planar concave facet (plane tilted 6-16 deg off the local surface,
        # 4-10 mm deep at its impact side) inside an irregular window -> crisp crease at its rim
        c = cand[rng.randint(len(cand))]
        pc, nc = P[c], VN[c]
        R = rng.uniform(*scoop_r) * size
        d = rng.uniform(*scoop_d)
        t1 = nrm(np.cross(nc, rng.normal(size=3)))
        t2 = np.cross(nc, t1)
        tl = math.tan(math.radians(rng.uniform(6, 16)))
        npl = nrm(nc + t1 * tl)
        p0 = pc - nc * d
        q = P - pc
        el = rng.uniform(0.55, 1.0)
        rr = np.sqrt((q @ t1) ** 2 + ((q @ t2) / el) ** 2) / R
        # soft window (no vertex-level stair-steps): the crisp crease is the plane intersection itself
        m = (1 - smoothstep(0.75, 1.0, rr)) * smoothstep(0.35, 0.6, VN @ nc) * (np.abs(q @ nc) < R * 0.6)
        above = (P - p0) @ npl
        cutd = np.where(above > 0, above / max(float(npl @ nc), 0.3), 0.0)
        cutd = np.minimum(cutd, d * 1.6) * w_vis * m * (d >= min_relief)
        P = P - VN * cutd[:, None]
    pits = pit_a * (pit_a >= min_relief) * np.clip(vnoise(P * 55.0 + off * 1.3) * 2.2 - 0.9, 0, 1)
    P = P - VN * (pits * w_vis)[:, None]
    return P


def plinth_kind_stone(kind, half, rng, fracture=True, frac_side=None, n_front=80, n_up=34, min_relief=0.0):
    """plinth stone of a given kind (director r4 #2b), local x along, y out (face), z up, centred on 0:
    'slab'    flat bedded slab (h:L <= 0.45), near-planar top and battered front, tight 1-2 cm arrises
    'block'   blocky split stone, planar faces meeting at 1-3 cm arrises, corner facets
    'boulder' sub-rounded field boulder with an irregular (2-3 facet) top profile and soft 2-3 cm arrises
    each with one crisp planar fracture face (>= 50 % of stones) and a conchoidal / lumpy / pitted skin."""
    a, b, c = (float(v) for v in half)
    S = []
    if kind == "boulder":
        for k in range(rng.randint(2, 4)):                       # irregular top: 2-3 tilted facets
            nt = nrm(np.array([rng.uniform(-0.45, 0.45), rng.uniform(-0.1, 0.35), 1.0]))
            S.append((nt, np.array([rng.uniform(-0.5, 0.5) * a, rng.uniform(-0.4, 0.3) * b, c]),
                      rng.uniform(0.25, 0.6)))
        S.append((nrm(np.array([rng.uniform(-0.12, 0.12), 1.0, rng.uniform(0.05, 0.2)])), np.array([0, b, 0.0]),
                  rng.uniform(0.4, 0.8)))
        S.append((nrm(np.array([rng.uniform(-0.3, 0.3), 1.0, rng.uniform(0.7, 1.3)])),
                  np.array([0.0, b, c]) - nrm(np.array([0, 1.0, 1.0])) * rng.uniform(0.04, 0.09), 0.5))
        k_r = rng.uniform(0.010, 0.014)
    elif kind == "slab":
        S.append((nrm(np.array([rng.uniform(-0.05, 0.05), rng.uniform(0.0, 0.08), 1.0])),
                  np.array([rng.uniform(-0.3, 0.3) * a, 0.0, c]), rng.uniform(0.02, 0.08)))
        S.append((nrm(np.array([rng.uniform(-0.08, 0.08), 1.0, rng.uniform(0.05, 0.18)])), np.array([0, b, 0.0]),
                  rng.uniform(0.05, 0.15)))
        k_r = rng.uniform(0.004, 0.006)
    else:   # block
        S.append((nrm(np.array([rng.uniform(-0.12, 0.12), rng.uniform(0.0, 0.15), 1.0])),
                  np.array([rng.uniform(-0.3, 0.3) * a, 0.0, c]), rng.uniform(0.05, 0.2)))
        S.append((nrm(np.array([rng.uniform(-0.12, 0.12), 1.0, rng.uniform(0.04, 0.16)])), np.array([0, b, 0.0]),
                  rng.uniform(0.1, 0.3)))
        nb_ = nrm(np.array([rng.uniform(-0.4, 0.4), 1.0, rng.uniform(0.6, 1.4)]))
        S.append((nb_, np.array([0.0, b, c]) - nb_ * rng.uniform(0.02, 0.05), 0.1))
        k_r = rng.uniform(0.006, 0.009)
    for sx in (-1.0, 1.0):                                       # ends: tilted, sometimes undercut
        ne = nrm(np.array([sx, rng.uniform(-0.3, 0.3), rng.uniform(-0.1, 0.45)]))
        S.append((ne, np.array([sx * a, 0.0, 0.0]), rng.uniform(0.05, 0.4)))
        if kind != "slab" or rng.rand() < 0.5:
            nc = nrm(np.array([sx, rng.uniform(0.6, 1.3), rng.uniform(0.1, 0.6)]))
            S.append((nc, np.array([sx * a, b, 0.0]) - nc * rng.uniform(0.04, 0.12) * min(a, b), 0.15))
    S.append((np.array([0.0, -1.0, 0.0]), np.array([0.0, -b, 0.0]), 0.0))
    S.append((np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, -c]), 0.0))
    fr = []
    if fracture:
        side = frac_side if frac_side is not None else rng.choice(["front", "end", "topfront"])
        if side == "front":
            nv_ = nrm(np.array([rng.uniform(-0.5, 0.5), 1.0, rng.uniform(-0.1, 0.4)]))
        elif side == "end":
            nv_ = nrm(np.array([rng.choice([-1.0, 1.0]), rng.uniform(0.2, 0.9), rng.uniform(0.0, 0.5)]))
        else:
            nv_ = nrm(np.array([rng.uniform(-0.4, 0.4), 1.0, rng.uniform(0.6, 1.2)]))
        ext = abs(nv_[0]) * a + abs(nv_[1]) * b + abs(nv_[2]) * c
        fr.append((nv_, ext * (1 - rng.uniform(0.12, 0.22))))
    th, ph = dir_grid(n_front, max(12, n_front // 5), n_up, 6)
    V, F = facet_stone(half, rng, S, k_round=k_r, fracs=fr, k_frac=0.0018, lump=0.002 * (min_relief <= 0.002),
                       lump_f=6.0, pit=0.0,
                       th=th, ph=ph, chips=rng.randint(1, 3))

    def vis(P, VN):
        return np.clip((VN[:, 1] + 0.2) * 2.0, 0, 1) * np.clip((P[:, 2] + c * 0.6) / (c * 0.5), 0, 1) \
            + np.clip(VN[:, 2] * 1.5, 0, 1) * (P[:, 1] > -0.2 * b)
    V = stone_skin(V, F, rng, n_scoop=(6, 12), scoop_r=(0.04, 0.10), scoop_d=(0.004, 0.010),
                   lump_a=0.010 if kind != "boulder" else 0.014, lump_f=8.0, pit_a=0.003,
                   vis=lambda P, VN: np.clip(vis(P, VN), 0, 1), min_relief=min_relief)
    return V, F


def pad_stone(rng, plan=(0.23, 0.18), vis_h=0.18, bury=0.05, tilt_deg=(1.0, 3.0), n_corner=(6, 8), batter=(16, 36),
              min_relief=0.0):
    """door-post pad stone (director r4 #2a): low and wide (visible width:height >= 2.2), an irregular
    6-9-corner plan, battered planar sides, 2-3 planar split faces meeting at 0.5-1.5 cm arrises, and a
    flat bearing bed ~0.25 m across tilted 1-3 deg.  No rotationally symmetric profile.  Local: top bed
    at z = 0, bottom at -(vis_h + bury)."""
    hu, hv = plan
    k = rng.randint(n_corner[0], n_corner[1] + 1)
    ang = np.sort(np.mod(np.linspace(0, 2 * np.pi, k, endpoint=False) + rng.uniform(-0.25, 0.25, k)
                         + rng.uniform(0, 6.3), 2 * np.pi))
    rad = rng.uniform(0.74, 1.08, k)
    poly = np.stack([np.cos(ang) * rad * hu, np.sin(ang) * rad * hv], -1)
    H = vis_h + bury
    c = H / 2
    S = []
    tl = math.radians(rng.uniform(*tilt_deg))
    ta = rng.uniform(0, 2 * np.pi)
    S.append((nrm(np.array([math.sin(tl) * math.cos(ta), math.sin(tl) * math.sin(ta), math.cos(tl)])),
              np.array([0.0, 0.0, c]), 0.0))                                       # bearing bed
    for i in range(k):
        p0, p1 = poly[i], poly[(i + 1) % k]
        e = p1 - p0
        nh = nrm(np.array([e[1], -e[0], 0.0]))
        if np.dot(nh[:2], (p0 + p1) / 2) < 0:
            nh = -nh
        bat = math.radians(rng.uniform(*batter))                                    # battered side
        n_ = nrm(nh * math.cos(bat) + np.array([0, 0, math.sin(bat)]))
        S.append((n_, np.array([(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, -c * 0.4]), rng.uniform(0.0, 0.3)))
    S.append((np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, -c]), 0.0))
    fr = []
    for _ in range(rng.randint(2, 4)):                                             # planar split faces
        az_ = rng.uniform(0, 2 * np.pi)
        el = math.radians(rng.uniform(28, 50))
        nv_ = nrm(np.array([math.cos(az_) * math.cos(el), math.sin(az_) * math.cos(el), math.sin(el)]))
        ext = abs(nv_[0]) * hu + abs(nv_[1]) * hv + abs(nv_[2]) * c
        fr.append((nv_, ext * (1 - rng.uniform(0.22, 0.32))))
    th, ph = dir_grid(72, 24, 26, 5, front=(0.0, 2 * np.pi))
    th = np.linspace(0, 2 * np.pi, 84, endpoint=False)
    V, F = facet_stone((hu, hv, c), rng, S, k_round=0.0028, fracs=fr, k_frac=0.0018, lump=0.0015 * (min_relief <= 0.0015), lump_f=7.0,
                       pit=0.0, th=th, ph=ph, chips=rng.randint(1, 3))
    V = stone_skin(V, F, rng, n_scoop=(5, 8), scoop_r=(0.03, 0.07), scoop_d=(0.003, 0.007), lump_a=0.004,
                   lump_f=9.0, pit_a=0.002, vis=lambda P, VN: np.clip(VN[:, 2] * 0.5 + 0.6, 0, 1) * (P[:, 2] > -c * 0.2), min_relief=min_relief)
    V[:, 2] -= V[:, 2].max() - 0.004
    return V, F


def spall_stone(rng, half, n_planes=(5, 8), k_round=0.0025):
    """small split spall / rubble piece (director r4 #2f): a polyhedron of 5-8 planar fracture faces with
    tight arrises (they read at 2 m), a faint lumpy skin."""
    a, b, c = (float(v) for v in half)
    S = [(np.array([0.0, 0.0, -1.0]), np.array([0.0, 0.0, -c]), 0.0)]
    for _ in range(rng.randint(n_planes[0], n_planes[1] + 1)):
        nv_ = nrm(rng.normal(size=3) * [1.0, 1.0, 0.8] + [0, 0, 0.25])
        ext = abs(nv_[0]) * a + abs(nv_[1]) * b + abs(nv_[2]) * c
        S.append((nv_, nv_ * ext * (1 - rng.uniform(0.1, 0.3)), 0.0))
    for ax in range(3):
        for sg_ in (-1.0, 1.0):
            n_ = np.zeros(3)
            n_[ax] = sg_
            S.append((n_, n_ * half[ax] * 1.0, 0.0))
    th = np.linspace(0, 2 * np.pi, 28, endpoint=False)
    ph = np.linspace(-np.pi / 2, np.pi / 2, 16)[1:-1]
    V, F = facet_stone(half, rng, S, k_round=k_round, lump=0.0012, lump_f=12.0, pit=0.0006, th=th, ph=ph)
    return V, F


def outline_radius(rng, kind, n_out=720, sm_scale=1.0):
    """irregular closed outline, returned as a normalised radius function R(theta) (callable).
    kind 'flag': non-convex, 10-16 corners; 'trap' rounded trapezoid; 'D' D-shape; 'tri' rounded
    triangle; 'pad' rounded lump.  Corners are softened, then 3-8 cm-scale edge noise and 1-2
    notches are added, so no two outlines share a straight run or a parallel pair of sides."""
    if kind == "flag":
        k = rng.randint(10, 17)
        ang = np.sort(np.mod(np.linspace(0, 2 * np.pi, k, endpoint=False) + rng.uniform(-0.18, 0.18, k)
                             + rng.uniform(0, 6.3), 2 * np.pi))
        rad = rng.uniform(0.80, 1.06, k)
        rad[rng.randint(k)] *= rng.uniform(0.82, 0.9)              # one deep re-entrant corner
        poly = np.stack([np.cos(ang) * rad, np.sin(ang) * rad], -1)
        sm, noise_a, notch_n = 0.05, 0.022, rng.randint(1, 3)
    else:
        sk = rng.uniform(-0.25, 0.25)
        if kind == "trap":
            top_l, top_r = -rng.uniform(0.45, 0.8), rng.uniform(0.5, 0.85)
            pts = [(-1.0, -1.0), (1.0, -1.0), (rng.uniform(0.9, 1.0), rng.uniform(-0.3, 0.2)),
                   (top_r + sk * 0.3, 1.0), (top_l + sk * 0.3, rng.uniform(0.9, 1.0)),
                   (-rng.uniform(0.88, 1.0), rng.uniform(-0.1, 0.4))]
        elif kind == "D":
            pts = [(-1.0, -1.0), (1.0, -1.0), (1.0, rng.uniform(-0.2, 0.25)),
                   (rng.uniform(0.6, 0.75), rng.uniform(0.75, 0.9)), (sk * 0.4, 1.0),
                   (-rng.uniform(0.55, 0.75), rng.uniform(0.7, 0.9)), (-1.0, rng.uniform(-0.15, 0.3))]
        elif kind == "tri":
            pk = rng.uniform(-0.35, 0.35)
            pts = [(-1.0, -1.0), (1.0, -1.0), (rng.uniform(0.85, 1.0), rng.uniform(-0.6, -0.2)),
                   (pk + rng.uniform(0.35, 0.5), rng.uniform(0.75, 0.9)), (pk, 1.0),
                   (pk - rng.uniform(0.4, 0.55), rng.uniform(0.7, 0.85)),
                   (-rng.uniform(0.85, 1.0), rng.uniform(-0.55, -0.1))]
        else:   # pad / lump
            k = rng.randint(6, 9)
            ang = np.sort(np.mod(np.linspace(0, 2 * np.pi, k, endpoint=False) + rng.uniform(-0.2, 0.2, k), 2 * np.pi))
            rad = rng.uniform(0.85, 1.05, k)
            pts = list(zip(np.cos(ang) * rad, np.sin(ang) * rad))
        poly = np.asarray(pts, float)
        sm, noise_a, notch_n = 0.09, 0.016, rng.randint(1, 3)
    kp = len(poly)
    t = 2 * np.pi * np.arange(n_out) / n_out
    d = np.stack([np.cos(t), np.sin(t)], -1)
    best = np.full(n_out, 10.0)
    for i in range(kp):
        a, b = poly[i], poly[(i + 1) % kp]
        e = b - a
        den = d[:, 0] * (-e[1]) - d[:, 1] * (-e[0])
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (a[0] * (-e[1]) - a[1] * (-e[0])) / den
            u = (d[:, 0] * a[1] - d[:, 1] * a[0]) / den
        ok = (tt > 0) & (u >= -1e-6) & (u <= 1 + 1e-6)
        best = np.where(ok & (tt < best), tt, best)
    R = np.where(best > 5, 1.0, best)
    # soften the corners (circular gaussian smoothing of the radius function)
    sig = max(2, int(sm * sm_scale / (2 * np.pi) * n_out))
    ker = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
    ker /= ker.sum()
    R = np.convolve(np.concatenate([R[-3 * sig:], R, R[:3 * sig]]), ker, mode="valid")
    seed = rng.randint(1, 10 ** 6)
    R = R * (1 + noise_a * ring_noise(t, seed, 16, 1.0, 0.45) + 0.006 * ring_noise(t, seed + 1, 40, 1.0, 0.0))
    for _ in range(notch_n):
        c = rng.uniform(0, 2 * np.pi)
        dd = np.angle(np.exp(1j * (t - c)))
        R = R * (1 - rng.uniform(0.04, 0.08) * np.exp(-(dd / rng.uniform(0.06, 0.12)) ** 2))
    tt_ = np.concatenate([t, [2 * np.pi]])
    RR = np.concatenate([R, R[:1]])
    return lambda th: np.interp(np.mod(th, 2 * np.pi), tt_, RR)


def shell_stone(hu, hv, rng, kind, depth, rr=(0.02, 0.04), dome=0.03, tilt=0.15, n_frac=1, frac_depth=(0.03, 0.08),
                n_th=44, noise=0.005, freq=7.0, side_bulge=0.012, thick_var=0.0, dish=0.0, flat_face=None,
                face_fr=(0.0, 0.34, 0.6, 0.8, 0.93), sm_scale=1.0, n_facet=0, frac_k=(0.004, 0.01), chips=0,
                chip_w=(0.04, 0.08), chip_d=(0.012, 0.025), side_slope=0.0, Rf=None, spalls=0,
                spall_r=(0.03, 0.06), spall_d=(0.002, 0.005), rr_var=0.45, fine_scale=1.0, spall_scale=1.0):
    """irregular stone as an open SHELL: an exposed face (domed, tilted, crossed by 1-2 fracture planes
    with 3-8 cm edge breaks, faint pitting), a rounded arris whose radius varies round the outline, and
    sides running back `depth` -- no back face (it is never visible: producer note 6).
    Local frame: outline in (u, v), face normal +w.  Returns V (u, v, w), faces."""
    if Rf is None:
        Rf = outline_radius(rng, kind, sm_scale=sm_scale)
    th = 2 * np.pi * np.arange(n_th) / n_th + rng.uniform(0, 0.1)
    Rn = Rf(th)
    ou, ov = hu * Rn * np.cos(th), hv * Rn * np.sin(th)
    Rabs = np.hypot(ou, ov)
    seed = rng.randint(1, 10 ** 6)
    rr_t = np.clip(rng.uniform(*rr) * (1 + rr_var * ring_noise(th, seed + 3, 4, 1.0)), 0.004, 0.07)
    rr_t = np.minimum(rr_t, Rabs * 0.4)
    off = rng.uniform(-50, 50, 3)
    ta, tb = (rng.normal(size=2) * tilt)
    fr = []
    for _ in range(n_frac):
        psi = rng.uniform(0, 2 * np.pi)
        ext = float(np.max(ou * math.cos(psi) + ov * math.sin(psi)))
        u0 = ext * rng.uniform(0.25, 0.6)
        fr.append((psi, u0, rng.uniform(*frac_depth) / max(ext - u0, 0.02), rng.uniform(*frac_k), dome * 0.5))
    for _ in range(n_facet):                 # gentle split facets: the face reads as flat planes, not a dome
        psi = rng.uniform(0, 2 * np.pi)
        ext = float(np.max(ou * math.cos(psi) + ov * math.sin(psi)))
        u0 = ext * rng.uniform(0.05, 0.4)
        fr.append((psi, u0, rng.uniform(0.15, 0.38), rng.uniform(0.002, 0.005), dome * rng.uniform(0.55, 0.9)))

    chip_l = []
    for _ in range(chips):              # chipped arris: a 4-8 cm wide planar break off the top edge
        kc = rng.randint(n_th)
        pu, pv = ou[kc], ov[kc]
        psi = math.atan2(pv / hv ** 2, pu / hu ** 2)
        cw = rng.uniform(*chip_w)
        u_ext = pu * math.cos(psi) + pv * math.sin(psi)
        chip_l.append((psi, u_ext - cw * 0.6, rng.uniform(*chip_d) / (cw * 0.6),
                       -pu * math.sin(psi) + pv * math.cos(psi), cw * 0.5))

    sp_l = []
    for _ in range(spalls):                 # shallow planar spalls on the top face (crisp rims)
        rs_ = rng.uniform(0.0, 0.7)
        ps_ = rng.uniform(0, 2 * np.pi)
        sp_l.append((hu * rs_ * math.cos(ps_), hv * rs_ * math.sin(ps_), rng.uniform(*spall_r),
                     rng.uniform(*spall_d), rng.uniform(0, 2 * np.pi), rng.uniform(0.04, 0.12), rng.uniform(0.6, 1.0)))

    def yf0(u, v):
        q = np.clip((u / hu) ** 2 + (v / hv) ** 2, 0, 1.4)
        w = dome * (1 - q) + ta * u / max(hu, hv) * max(hu, hv) * 1.0 + tb * v
        w = w + noise * fbm(np.stack([u * freq + off[0], v * freq + off[1], np.full(np.shape(u), off[2])], -1), 3)
        w = w + fine_scale * noise * 0.35 * vnoise(np.stack([u * freq * 4.1, v * freq * 4.1, np.full(np.shape(u), off[2] + 3)], -1))
        for (psi, u0, slope, k, wref) in fr:
            uu = u * math.cos(psi) + v * math.sin(psi)
            plane = wref - (uu - u0) * slope
            w = smin(w, plane, k)
        if dish:
            w = w - dish * np.clip(1 - q * 1.3, 0, 1) ** 0.8
        for (psi, u0, slope, vc, hwc) in chip_l:
            uu = u * math.cos(psi) + v * math.sin(psi)
            vv = -u * math.sin(psi) + v * math.cos(psi)
            win = np.exp(-((vv - vc) / hwc) ** 4)
            plane = dome * 0.2 - (uu - u0) * slope
            w = w + win * (np.minimum(w, plane) - w)
        if flat_face is not None:
            w = np.where(w > flat_face, flat_face + (w - flat_face) * 0.15, w)
        return w

    def yf(u, v):
        w = yf0(u, v)
        for (uc, vc, Rs, ds, ang_, sl_, el_) in sp_l:
            du, dv = u - uc, v - vc
            a1 = du * math.cos(ang_) + dv * math.sin(ang_)
            a2 = (-du * math.sin(ang_) + dv * math.cos(ang_)) / el_
            rr_s = np.sqrt(a1 ** 2 + a2 ** 2) / Rs
            win = 1 - smoothstep(0.7, 1.0, rr_s)
            plane = float(yf0(np.array([uc]), np.array([vc]))[0]) - ds * spall_scale - sl_ * a1 * 0.1
            w = w - win * np.maximum(0.0, w - plane) * (spall_scale > 0)
        return w

    rings = []
    inner = (Rabs - rr_t) / np.maximum(Rabs, 1e-6)
    for f in face_fr[1:]:
        s_ = f * inner
        u, v = ou * s_, ov * s_
        rings.append(np.stack([u, v, yf(u, v)], -1))
    u_e, v_e = ou * inner, ov * inner
    w_e = yf(u_e, v_e)
    rings.append(np.stack([u_e, v_e, w_e], -1))
    for phi in (np.pi / 5, 2 * np.pi / 5, np.pi / 2):
        ins = rr_t * (1 - math.sin(phi))
        sc = (Rabs - ins) / np.maximum(Rabs, 1e-6)
        rings.append(np.stack([ou * sc, ov * sc, w_e - rr_t + rr_t * math.cos(phi)], -1))
    w_back = -depth * (1 + thick_var * ring_noise(th, seed + 7, 5, 1.0))
    for tt in (0.3, 0.65, 1.0):
        bul = side_bulge * math.sin(math.pi * min(tt, 0.85))
        ww = (w_e - rr_t) + tt * (w_back - (w_e - rr_t))
        sc = (Rabs + bul + side_slope * (w_e - rr_t - ww)) / np.maximum(Rabs, 1e-6)
        rings.append(np.stack([ou * sc, ov * sc, ww], -1))
    pole = np.array([[0.0, 0.0, float(yf(np.array([0.0]), np.array([0.0]))[0])]])
    V = np.concatenate([pole] + rings)
    n = n_th
    j = np.arange(n)
    j1 = (j + 1) % n
    faces = [np.stack([np.zeros(n, int), 1 + j, 1 + j1], -1)]       # fan, normal +w
    for k in range(len(rings) - 1):
        a = 1 + k * n
        b = 1 + (k + 1) * n
        faces.append(np.stack([a + j, b + j, b + j1, a + j1], -1))
    return V, faces


def map_uvw(V, mode):
    """'wall': u->x (along the ring), v->z (up), w->-y (outward).  'plan': u->x, v->y, w->z (up)."""
    if mode == "wall":
        return np.stack([V[:, 0], -V[:, 2], V[:, 1]], -1), False    # local -y is radial-out after rotz(az)
    return V.copy(), False


def add_shell(acc, V, faces, mode, R, t, mat):
    P, flip = map_uvw(V, mode)
    if flip:
        faces = [f[:, ::-1] for f in faces]
    acc.add(xf(P, R, t), faces, mat)


def chink_stone(rng, half=None):
    """flat wedge chinking stone for an open dry-stone joint (hut round 4): local x along the joint, y into the
    wall (thins toward the back), z up.  half=None draws the hut's 3-5 cm x 0.8-1.4 cm size."""
    if half is None:
        hx, hz = rng.uniform(0.03, 0.05), rng.uniform(0.008, 0.014)
        half = (hx, 0.035, hz)
    V, F = boulder(half, rng, p_h=3.4, p_v=3.0, crown=0.0, bulge=0.0, n_frac=2, frac_k=0.002,
                   frac_cut=(0.08, 0.2), warp=0.12, amp=0.0015, freq=25.0, pit=0.0006, taper=0.05, nu=14, nv=6)
    V[:, 2] *= 1 - 0.55 * np.clip(-V[:, 1] / half[1], 0, 1)        # wedge: thins toward the back
    return V, F


def rubble_stone(half, rng, pillow=(0.005, 0.02), k_round=(0.010, 0.03), n_frac=(0, 2), bed_tilt=0.04,
                 end_tilt=0.35, n_front=56, n_up=20, front_only=True):
    """flat-bedded, roughly coursed rubble (art bible section 3): near-planar beds (tilt <= bed_tilt), a pillowed
    face 0.5-2 cm proud, ends tilted / undercut, 0-2 crisp fracture planes across the face corners, arrises that
    vary 1-3 cm along their length.  Local x along the wall, y out (face), z up.  Mesh density concentrated on
    the face (dir_grid); the back is sparse (it is buried in the mortar body: producer note 6)."""
    a, b, c = (float(v) for v in half)
    S = []
    S.append((nrm(np.array([rng.uniform(-bed_tilt, bed_tilt), rng.uniform(-0.02, 0.06), 1.0])), np.array([0, 0, c]),
              rng.uniform(0.0, 0.05)))
    S.append((nrm(np.array([rng.uniform(-bed_tilt, bed_tilt), rng.uniform(-0.02, 0.02), -1.0])), np.array([0, 0, -c]),
              0.0))
    pil = rng.uniform(*pillow)
    S.append((nrm(np.array([rng.uniform(-0.08, 0.08), 1.0, rng.uniform(-0.05, 0.05)])), np.array([0, b, 0.0]),
              pil / max(a, c) ** 2))
    S.append((np.array([0.0, -1.0, 0.0]), np.array([0.0, -b, 0.0]), 0.0))
    for sx in (-1.0, 1.0):
        ne = nrm(np.array([sx, rng.uniform(-end_tilt, end_tilt), rng.uniform(-end_tilt, end_tilt)]))
        S.append((ne, np.array([sx * a, 0.0, 0.0]), rng.uniform(0.0, 0.3)))
    fr = []
    for _ in range(rng.randint(n_frac[0], n_frac[1] + 1)):
        nv_ = nrm(np.array([rng.choice([-1.0, 1.0]) * rng.uniform(0.3, 1.0), 1.0, rng.choice([-1.0, 1.0]) * rng.uniform(0.2, 0.9)]))
        ext = abs(nv_[0]) * a + abs(nv_[1]) * (b + pil) + abs(nv_[2]) * c
        fr.append((nv_, ext * (1 - rng.uniform(0.06, 0.16))))
    th, ph = dir_grid(n_front, max(10, n_front // 5), n_up, 5) if front_only else (None, None)
    return facet_stone(half, rng, S, k_round=rng.uniform(*k_round), fracs=fr, k_frac=0.002, lump=0.0, pit=0.0,
                       th=th, ph=ph, chips=rng.randint(0, 2))


def dressed_stone(half, rng, chamfer=0.01, n_front=48, n_up=18, chips=(0, 1)):
    """dressed stone (surrounds, quoins, string courses, corbels): flat planar faces, ~1 cm chamfer, at most one
    small arris chip.  Local x along, y out (face), z up."""
    a, b, c = (float(v) for v in half)
    S = [(np.array([0, 0, 1.0]), np.array([0, 0, c]), 0.0), (np.array([0, 0, -1.0]), np.array([0, 0, -c]), 0.0),
         (nrm(np.array([rng.uniform(-0.01, 0.01), 1.0, rng.uniform(-0.01, 0.01)])), np.array([0, b, 0.0]), 0.0),
         (np.array([0, -1.0, 0]), np.array([0, -b, 0.0]), 0.0),
         (np.array([1.0, 0, 0]), np.array([a, 0, 0.0]), 0.0), (np.array([-1.0, 0, 0]), np.array([-a, 0, 0.0]), 0.0)]
    th, ph = dir_grid(n_front, max(10, n_front // 5), n_up, 5)
    return facet_stone(half, rng, S, k_round=chamfer * 0.45, lump=0.0, pit=0.0, th=th, ph=ph,
                       chips=rng.randint(chips[0], chips[1] + 1))


def voussoir_stone(half, rng, wedge_deg=8.0, crown_extra=0.0, chamfer=0.01, irregular=0.25, n_front=48, n_up=18):
    """arch voussoir (art bible section 3: irregular widths, thicker at the crown -- pass crown_extra > 0 for the
    stones near the key): a dressed wedge whose two joint faces converge toward the arch centre (local -z) by
    wedge_deg in total.  Local x along the arch (tangential), y out of the wall face, z radial (extrados +z)."""
    a, b, c = (float(v) for v in half)
    c_top = c * (1 + crown_extra)
    w = math.radians(wedge_deg) / 2 * (1 + rng.uniform(-irregular, irregular))
    S = [(np.array([0, 0, 1.0]), np.array([0, 0, c_top]), rng.uniform(0.0, 0.05)),
         (np.array([0, 0, -1.0]), np.array([0, 0, -c]), 0.0),
         (nrm(np.array([rng.uniform(-0.02, 0.02), 1.0, rng.uniform(-0.02, 0.02)])), np.array([0, b, 0.0]), 0.0),
         (np.array([0, -1.0, 0]), np.array([0, -b, 0.0]), 0.0)]
    for sx in (-1.0, 1.0):
        S.append((nrm(np.array([sx * math.cos(w), 0.0, -math.sin(w)])), np.array([sx * a, 0, 0.0]), 0.0))
    th, ph = dir_grid(n_front, max(10, n_front // 5), n_up, 5)
    return facet_stone((a, b, max(c, c_top)), rng, S, k_round=chamfer * 0.45, lump=0.0, pit=0.0, th=th, ph=ph,
                       chips=rng.randint(0, 2))


# ---------------------------------------------------------------------------------------------------------------
# the unified entry point
# ---------------------------------------------------------------------------------------------------------------
STYLES = {
    "rubble": dict(fn="rubble_stone", needs_half=True),
    "dressed": dict(fn="dressed_stone", needs_half=True),
    "voussoir": dict(fn="voussoir_stone", needs_half=True),
    "footing": dict(fn="field_stone", needs_half=True),
    "plinth_slab": dict(fn="plinth_kind_stone", kind="slab"),
    "plinth_block": dict(fn="plinth_kind_stone", kind="block"),
    "plinth_boulder": dict(fn="plinth_kind_stone", kind="boulder"),
    "pad": dict(fn="pad_stone"),
    "spall": dict(fn="spall_stone"),
    "chink": dict(fn="chink_stone"),
    "boulder": dict(fn="boulder", needs_half=True),
    "flag": dict(fn="shell_stone"),
    "hearth": dict(fn="box_stone", needs_half=True),
}


def make_stone(style, rng, half=None, **kw):
    """the one stone generator: dispatch a style name to its shape model.  `half` = half extents (x along, y out,
    z up) for the styles that take them; every other keyword goes to the style's model (see its docstring).
    Returns (V, faces)."""
    if style not in STYLES:
        raise ValueError(f"unknown stone style {style!r}; known: {sorted(STYLES)}")
    st = STYLES[style]
    fn = globals()[st["fn"]]
    if st["fn"] == "plinth_kind_stone":
        return fn(st["kind"], half, rng, **kw)
    if st["fn"] == "pad_stone":
        return fn(rng, **kw)
    if st["fn"] == "spall_stone":
        return fn(rng, half, **kw)
    if st["fn"] == "chink_stone":
        return fn(rng, half)
    if st["fn"] == "shell_stone":
        return fn(kw.pop("hu"), kw.pop("hv"), rng, kw.pop("kind", "flag"), kw.pop("depth", 0.1), **kw)
    if st["fn"] == "box_stone":
        r_frac = kw.pop("r_frac", 0.4)
        segs = kw.pop("segs", (4, 4, 3))
        return fn(half, r_frac, segs, rng, **kw)
    return fn(half, rng, **kw)
