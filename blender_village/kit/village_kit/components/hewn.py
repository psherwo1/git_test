"""components.hewn -- hand-hewn square timber and the pooled pegs / nails of the tiered octagonal buildings
(kit 1.1.0, from the hilltop keep).

hewn_square(acc, O, EX, EY, EZ, L, wy, wz, rng, ...)   square hewn member along EX: chamfers, adze scallops per face,
        broad flat-hewn facets, lean, swell / taper, low-frequency wave, modelled checks, hidden faces dropped (drop)
peg(g, p, axis, rad, proud)                            oak peg: the kit's pooled peg (timber.make_peg), scaled
nail_heads(g, P, normal, rad)                          forged nail heads: the kit's pooled nail head (timber.make_nail_head)
"""
import math

import numpy as np

from ..core import R_y_to
from ..geom import hash01, n1
from .timber import make_nail_head, make_peg


def hewn_square(acc, O, EX, EY, EZ, L, wy, wz, rng, mat="M_timber", chamfer=0.025, nf=3, st_len=0.05,
                adze=0.004, adze_period=(0.07, 0.13), lean=(0.0, 0.0), swell=0.0, taper=0.0, wave=0.0,
                checks=(), end_bevel=True, seed=0, drop=(), relief=None, dropped=None):
    """hand-hewn square timber along EX from O (length L), section wy (EY) x wz (EZ).
    Adze facets (scalloped, per face), lean (rad, EY/EZ), swell/taper (m), low-freq wave (m),
    modelled checks: dicts face(0:+EY,1:+EZ,2:-EY,3:-EZ), pos(-1..1 across), x0, x1 (0..1), depth, width.
    Producer note 11: relief(P) -> threshold at the member's centre.  The adze scallops and the hewn-face tilt are
    modelled only where the deepest scallop (1.4 x adze) reaches it (the entrance zone's 1 cm); a check is modelled
    only when its depth reaches it, otherwise its world position / direction / length is appended to `dropped` (a
    list) so the decal pass can put a `crack` anchor there.  The random draws are made either way."""
    O = np.asarray(O, float)
    EX, EY, EZ = [np.asarray(e, float) / np.linalg.norm(e) for e in (EX, EY, EZ)]
    thr = 0.0 if relief is None else float(relief((O + EX * (L / 2))[None])[0])
    k_adze = 1.0 if adze * 1.4 >= thr else 0.0
    kept = []
    for ck in checks:
        if ck["depth"] >= thr:
            kept.append(ck)
        elif dropped is not None:
            fi = ck["face"]
            nrm_ = [EY, EZ, -EY, -EZ][fi]
            acr_ = [EZ, -EY, -EZ, EY][fi]
            half_ = [wz, wy, wz, wy][fi] / 2
            u0, u1 = ck["x0"] * L, ck["x1"] * L
            p_ = O + EX * (0.5 * (u0 + u1)) + nrm_ * ([wy, wz, wy, wz][fi] / 2) + acr_ * ck["pos"] * half_
            dropped.append(dict(pos=p_, normal=nrm_, along=EX, length=u1 - u0, depth=ck["depth"]))
    checks = kept
    n_in = max(4, int(L / st_len))
    c = chamfer
    xs = np.linspace(c * 0.7, L - c * 0.7, n_in)
    if end_bevel:
        xs = np.concatenate([[0.0], xs, [L]])
    ns = len(xs)
    u = xs / L
    # base profile, CCW from the +EY face
    hy, hz = wy / 2, wz / 2
    faces = []          # (start corner, end corner, outward normal, face id)
    corners = [((hy, -hz + c), (hy, hz - c), (1, 0)), ((hy - c, hz), (-hy + c, hz), (0, 1)),
               ((-hy, hz - c), (-hy, -hz + c), (-1, 0)), ((-hy + c, -hz), (hy - c, -hz), (0, -1))]
    pts, nrm, fid, acr = [], [], [], []
    for fi, (a, b, nn) in enumerate(corners):
        chk = [ck for ck in checks if ck["face"] == fi]
        ts = list(np.linspace(0, 1, nf + 2))
        for ck in chk:
            tc = 0.5 + 0.5 * ck["pos"]
            ts += [tc - 1e-3, tc, tc + 1e-3]
        ts = sorted(set(np.round(ts, 6)))
        for t in ts:
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            nrm.append(nn)
            fid.append(fi)
            acr.append(t)
    pts, nrm, fid, acr = np.array(pts), np.array(nrm, float), np.array(fid), np.array(acr)
    m = len(pts)
    A = np.broadcast_to(pts[None, :, 0], (ns, m)).copy()
    B = np.broadcast_to(pts[None, :, 1], (ns, m)).copy()
    # swell / taper
    sc_ = 1 + (swell * np.sin(np.pi * u) - taper * u) / (0.5 * min(wy, wz))
    A *= sc_[:, None]
    B *= sc_[:, None]
    # adze scallops per face (inward offsets), each face its own phase/period
    off = np.zeros((ns, m))
    for fi in range(4):
        per = rng.uniform(*adze_period)
        ph = rng.uniform(0, 1)
        fr = np.mod(xs / per + ph + 0.15 * n1(xs * 3, seed * 7 + fi), 1.0)
        sc_d = adze * (0.6 + 0.8 * rng.uniform(0, 1, ns)) * k_adze
        dip = sc_d[:, None] * (1 - (2 * fr[:, None] - 1) ** 2) * (0.7 + 0.3 * np.cos((acr[None, :] - 0.5) * np.pi))
        off += np.where(fid[None, :] == fi, -dip, 0.0)
        # occasional broad flat-hewn facet (shallow plane tilted across the face)
        tilt = rng.normal(0, adze * 0.8) * k_adze
        off += np.where(fid[None, :] == fi, tilt * (acr[None, :] - 0.5), 0.0)
    # checks (V-grooves on a face)
    for ck in checks:
        fi = ck["face"]
        tc = 0.5 + 0.5 * ck["pos"]
        env = np.clip(np.sin(np.pi * np.clip((u - ck["x0"]) / (ck["x1"] - ck["x0"]), 0, 1)), 0, 1) ** 0.7
        drift = 0.12 * n1(u * 4, seed + 31 + fi)
        on = (fid == fi)
        mid = on & (np.abs(acr - tc) < 5e-4)
        side = on & (np.abs(np.abs(acr - tc) - 1e-3) < 5e-4)
        off -= np.where(mid[None, :], ck["depth"] * env[:, None], 0.0)
        # open the lips by moving the side points apart along the face
        sgn = np.sign(acr - tc)
        dvec = np.array([[0, 1], [-1, 0], [0, -1], [1, 0]])[fi]
        for arr, comp in ((A, 0), (B, 1)):
            arr += np.where(side[None, :], (sgn[None, :] * 0.5 * ck["width"] * env[:, None]) * dvec[comp], 0.0)
            arr += np.where((mid | side)[None, :], drift[:, None] * 0.02 * dvec[comp], 0.0)
    A += off * nrm[None, :, 0]
    B += off * nrm[None, :, 1]
    # end bevel: shrink end stations
    if end_bevel:
        for i in (0, ns - 1):
            k_ = 1 - (c * 0.7) / (0.5 * min(wy, wz))
            A[i] *= k_
            B[i] *= k_
    # lean and wave
    cy = lean[0] * xs + wave * n1(xs * 0.9, seed + 3)
    cz = lean[1] * xs + wave * n1(xs * 0.9, seed + 4)
    V = (O[None, None, :] + xs[:, None, None] * EX + (A + cy[:, None])[..., None] * EY
         + (B + cz[:, None])[..., None] * EZ)
    i = np.arange(ns - 1)[:, None]
    j = np.arange(m)[None, :]
    a_ = i * m + j
    b_ = i * m + (j + 1) % m
    quads = np.stack([a_, a_ + m, b_ + m, b_], -1).reshape(-1, 4)
    if drop:
        # faces buried in masonry / under covering (face ids as for checks); the quads of a face are those whose
        # two profile points both belong to it (chamfer strips between faces are kept)
        jj = np.tile(np.arange(m), ns - 1)
        bad = np.isin(fid[jj], drop) & np.isin(fid[(jj + 1) % m], drop) & (fid[jj] == fid[(jj + 1) % m])
        quads = quads[~bad]
    caps = [np.arange(m)[None, :], ((ns - 1) * m + np.arange(m)[::-1])[None, :]]
    per = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1))])[:m]
    uv = np.stack([np.repeat(xs, m), np.tile(per, ns)], -1)
    acc.add(V.reshape(-1, 3), [quads] + caps, mat, uv=uv)



def _roll_about(R, ang):
    c, s = math.cos(ang), math.sin(ang)
    Ry = np.array([[c, 0, s], [0, 1.0, 0], [-s, 0, c]])
    return R @ Ry


def peg(g, p, axis, rad=0.014, proud=0.016):
    """oak peg at p along axis (the head stands proud along +axis): one of the kit's 6 pooled whittled pegs
    (components.timber.make_peg, r 1.5 cm, head 1.5-1.8 cm proud), placed as a linked duplicate scaled to rad."""
    p = np.asarray(p, float)
    k = int(hash01(np.array([p[0] * 31.0 + p[1] * 17.0 + p[2] * 7.0]))[0] * 6)
    me = g.pools.mesh("peg", k, make_peg, 28)
    R = _roll_about(R_y_to(axis), k * 1.3)
    return g.pools.place(me, "peg", R, p, scale=rad / 0.015)


def nail_heads(g, P, normal, rad=0.009):
    """forged nail heads at the points P (N, 3) on a surface with outward normal: the kit's pooled nail head
    (components.timber.make_nail_head, r ~0.95 cm) as linked duplicates scaled to rad."""
    P = np.atleast_2d(np.asarray(P, float))
    for p in P:
        k = int(hash01(np.array([p[0] * 53.0 + p[1] * 29.0 + p[2] * 11.0]))[0] * 6)
        me = g.pools.mesh("nail", k, make_nail_head, 40)
        g.pools.place(me, "nail", _roll_about(R_y_to(normal), k * 0.7), p, scale=rad / 0.0095)
