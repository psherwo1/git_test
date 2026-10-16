"""village_kit.core -- shared numpy / bmesh machinery for every kit building.

Contents
  * logging, deterministic RNG helpers (rng(), stable_seed())
  * value noise (vnoise / fbm / n2 / ring_noise) on a seeded permutation table; Noise(seed) gives an
    independent table (the module-level functions use the hut's historic seed 4711 so its build is unchanged)
  * small linear-algebra helpers (nrm, rotx/y/z, xf, frame_R, R_y_to, az_pt, frame_wall)
  * mesh primitives (grid_quads, tube, open_tube, chamfer_path, rbox / rbox2, lathe, slab, prism)
  * 2-D polygon helpers (poly_area, poly_sdf, seg_dist, ccw)
  * Acc: the numpy mesh accumulator -> bpy mesh with palette slots, UVs, sharp edges, Nanite hygiene and the
    Mask colour attribute (via village_kit.mask, the only Mask writer)
  * Nanite hygiene: nanite_clean() (remove doubles, dissolve degenerates, needle / sliver fix) + sliver_report()
  * cull_object(), visibility_cull() (producer note 6: delete faces no exterior / actor viewpoint can see)
  * scene helpers: reset_scene(), new_collection(), count_triangles(), save_blend()

Conventions: metres, Z up, ground Z = 0; azimuth `az` is measured from -Y toward +X (the principal entrance
faces -Y); every function is deterministic for a given seed / RandomState.
"""
import math
import os
import time
import zlib

import numpy as np

try:                                   # the kit is importable without Blender for pure-numpy helpers
    import bpy
except ImportError:                    # pragma: no cover
    bpy = None

from . import palette
from . import mask as _mask

T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# =============================================================================================
# deterministic randomness
# =============================================================================================
def stable_seed(*parts):
    """a stable 31-bit seed from any mix of strings / numbers (crc32, never Python's salted hash())."""
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


def rng(seed, *salt):
    """np.random.RandomState for a component: rng(404) or rng(404, 'rafters') (salted, still deterministic)."""
    return np.random.RandomState(stable_seed(seed, *salt) if salt else int(seed))


# =============================================================================================
# noise
# =============================================================================================
class Noise:
    """value noise on its own permutation table (seed).  Noise(4711) reproduces the module-level functions."""

    def __init__(self, seed=4711):
        rs = np.random.RandomState(seed)
        self.perm = np.tile(rs.permutation(256), 2)
        self.gv = rs.uniform(-1.0, 1.0, 256)

    def vnoise(self, p):
        return _vnoise(p, self.perm, self.gv)

    def fbm(self, p, octaves=3, lac=2.03, gain=0.5, normalize=True):
        p = np.asarray(p, float)
        tot, amp, norm = 0.0, 1.0, 0.0
        for _ in range(octaves):
            tot = tot + amp * self.vnoise(p)
            norm += amp
            p = p * lac + 11.7
            amp *= gain
        return tot / norm if normalize else tot


def _vnoise(p, perm, gv):
    p = np.asarray(p, dtype=float)
    shp = p.shape[:-1]
    p = p.reshape(-1, 3)
    i0 = np.floor(p).astype(np.int64)
    f = p - i0
    w = f * f * (3.0 - 2.0 * f)
    res = np.zeros(len(p))
    for dx in (0, 1):
        wx = w[:, 0] if dx else 1.0 - w[:, 0]
        ix = (i0[:, 0] + dx) & 255
        for dy in (0, 1):
            wy = w[:, 1] if dy else 1.0 - w[:, 1]
            iy = (i0[:, 1] + dy) & 255
            pxy = perm[perm[ix] + iy]
            for dz in (0, 1):
                wz = w[:, 2] if dz else 1.0 - w[:, 2]
                iz = (i0[:, 2] + dz) & 255
                res += gv[perm[pxy + iz]] * wx * wy * wz
    return res.reshape(shp)


# module-level noise: the hut's historic table (seed 4711)
_NRS = np.random.RandomState(4711)
_PERM = np.tile(_NRS.permutation(256), 2)
_GV = _NRS.uniform(-1.0, 1.0, 256)


def vnoise(p):
    return _vnoise(p, _PERM, _GV)


def fbm(p, octaves=3, lac=2.03, gain=0.5):
    p = np.asarray(p, float)
    tot = 0.0
    amp = 1.0
    norm = 0.0
    for _ in range(octaves):
        tot = tot + amp * vnoise(p)
        norm += amp
        p = p * lac + 11.7
        amp *= gain
    return tot / norm


def n2(a, b, seed):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a, b = np.broadcast_arrays(a, b)
    return vnoise(np.stack([a, b, np.full(a.shape, seed * 7.13 + 0.5)], -1))


def ring_noise(theta, seed, kmax=7, amp=1.0, p=1.0):
    """smooth periodic noise around a circle, ~[-amp, amp]."""
    rs = np.random.RandomState(seed)
    theta = np.asarray(theta, float)
    tot = np.zeros_like(theta)
    norm = 0.0
    for k in range(1, kmax + 1):
        a = 1.0 / k ** p
        tot += a * np.sin(k * theta + rs.uniform(0, 2 * np.pi))
        norm += a
    return amp * tot / norm * 1.6


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def nrm(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1.0, 0], [-s, 0, c]])


def az_pt(az, r, z=0.0):
    """azimuth measured from -Y, positive toward +X (counter-clockwise from above)."""
    return np.array([math.sin(az) * r, -math.cos(az) * r, z])


# =============================================================================================
# primitives
# =============================================================================================
def grid_quads(nu, nv, base=0, closed_u=False):
    """quads for an (nu, nv) vertex grid indexed i*nv + j; normal = du x dv."""
    iu = nu if closed_u else nu - 1
    i = np.arange(iu)[:, None]
    j = np.arange(nv - 1)[None, :]
    i1 = (i + 1) % nu
    a = i * nv + j
    b = i1 * nv + j
    c = i1 * nv + j + 1
    d = i * nv + j + 1
    return np.stack([a, b, c, d], -1).reshape(-1, 4) + base


def frames(path, up):
    T = np.gradient(path, axis=0)
    T = nrm(T)
    up = np.broadcast_to(np.asarray(up, float), path.shape)
    N = up - np.sum(up * T, -1, keepdims=True) * T
    N = nrm(N)
    B = np.cross(T, N)
    return T, N, B


def tube(path, radius, sides=8, up=(0, 0, 1), profile=None, caps=True, phase=0.0):
    """sweep a closed profile along path. profile: (sides,2) or (N,sides,2) in units of radius."""
    path = np.asarray(path, float)
    n = len(path)
    rad = np.broadcast_to(np.asarray(radius, float), (n,))
    T, N, B = frames(path, up)
    if profile is None:
        ang = phase + 2 * np.pi * np.arange(sides) / sides
        profile = np.stack([np.cos(ang), np.sin(ang)], -1)
    profile = np.asarray(profile, float)
    if profile.ndim == 2:
        profile = np.broadcast_to(profile, (n,) + profile.shape)
    m = profile.shape[1]
    pr = profile * rad[:, None, None]
    V = path[:, None, :] + pr[..., 0:1] * N[:, None, :] + pr[..., 1:2] * B[:, None, :]
    V = V.reshape(-1, 3)
    # quads: ring i (along path) x profile j ; want normal outward => tangential x T
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    j1 = (j + 1) % m
    F = np.stack([i * m + j, i * m + j1, (i + 1) * m + j1, (i + 1) * m + j], -1).reshape(-1, 4)
    faces = [F]
    if caps:
        faces.append(np.arange(m)[::-1][None, :])
        faces.append((n - 1) * m + np.arange(m)[None, :])
    seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
    alen = np.concatenate([[0], np.cumsum(seglen)])
    circ = 2 * np.pi * max(float(rad.mean()), 1e-3)
    u = np.tile(np.arange(m) / m, n)
    v = np.repeat(alen / circ, m)
    return V, faces, np.stack([u, v], -1), True


def chamfer_path(path, radius, ch):
    """add end chamfer rings to a tube path: returns new path, radius arrays."""
    path = np.asarray(path, float)
    rad = np.broadcast_to(np.asarray(radius, float), (len(path),)).copy()
    t0 = nrm(path[1] - path[0])
    t1 = nrm(path[-1] - path[-2])
    p = np.concatenate([[path[0]], [path[0] + t0 * ch], path[1:-1], [path[-1] - t1 * ch], [path[-1]]])
    r = np.concatenate([[rad[0] - ch], [rad[0]], rad[1:-1], [rad[-1]], [rad[-1] - ch]])
    return p, np.maximum(r, 0.002)


_TPL = {}


def box_template(xs, ys, zs):
    key = (tuple(xs), tuple(ys), tuple(zs))
    if key in _TPL:
        return _TPL[key]
    xs, ys, zs = (np.asarray(a, float) for a in (xs, ys, zs))
    Vs, Fs = [], []
    base = 0

    def face(a_vals, b_vals, mk):
        nonlocal base
        A, Bv = np.meshgrid(a_vals, b_vals, indexing="ij")
        P = mk(A, Bv).reshape(-1, 3)
        Vs.append(P)
        Fs.append(grid_quads(len(a_vals), len(b_vals), base))
        base += len(P)

    one = lambda A: np.ones_like(A)  # noqa: E731
    face(ys, zs, lambda A, B: np.stack([one(A), A, B], -1))
    face(zs, ys, lambda A, B: np.stack([-one(A), B, A], -1))
    face(zs, xs, lambda A, B: np.stack([B, one(A), A], -1))
    face(xs, zs, lambda A, B: np.stack([A, -one(A), B], -1))
    face(xs, ys, lambda A, B: np.stack([A, B, one(A)], -1))
    face(ys, xs, lambda A, B: np.stack([B, A, -one(A)], -1))
    V = np.concatenate(Vs)
    F = np.concatenate(Fs)
    key_r = np.round(V * 1e5).astype(np.int64)
    uniq, inv = np.unique(key_r, axis=0, return_inverse=True)
    inv = inv.ravel()
    Vu = np.zeros((len(uniq), 3))
    Vu[inv] = V
    F = inv[F]
    _TPL[key] = (Vu, F)
    return Vu, F


CH_C = 0.86


def ch_axis(n):
    """chamfer-template coordinates: -1, -c, interior..., c, 1"""
    return [-1.0] + list(np.linspace(-CH_C, CH_C, n + 1)) + [1.0]


def rbox(half, r, segs=(1, 1, 1), chamfer=True):
    """rounded/chamfered box in local coords, centred on 0. Returns V (K,3), F (Q,4)."""
    h = np.asarray(half, float)
    r = min(r, float(h.min()) * 0.95)
    if chamfer:
        Vt, F = box_template(ch_axis(segs[0]), ch_axis(segs[1]), ch_axis(segs[2]))
        a = np.abs(Vt)
        P = np.where(a > 0.999, np.sign(Vt) * h, Vt / CH_C * (h - r))
    else:
        Vt, F = box_template(*[np.linspace(-1, 1, s + 1) for s in segs])
        P = Vt * h
    q = np.clip(P, -(h - r), h - r)
    d = P - q
    L = np.linalg.norm(d, axis=1, keepdims=True)
    P = np.where(L > 1e-9, q + d / np.maximum(L, 1e-12) * r, P)
    return P, F


def rbox2(half, r, segs):
    """rounded box with TWO rows of vertices in every rounded edge zone (true 2-segment rounding)."""
    h = np.asarray(half, float)
    r = min(r, float(h.min()) * 0.9)
    c = 0.82
    axes = [[-1.0, -(1 + c) / 2, -c] + list(np.linspace(-c, c, n + 1)[1:-1]) + [c, (1 + c) / 2, 1.0]
            for n in segs]
    Vt, F = box_template(*axes)
    a = np.abs(Vt)
    P = np.where(a <= c + 1e-9, Vt / c * (h - r), np.sign(Vt) * (h - r + (a - c) / (1 - c) * r))
    q = np.clip(P, -(h - r), h - r)
    d = P - q
    L = np.linalg.norm(d, axis=1, keepdims=True)
    P = np.where(L > 1e-9, q + d / np.maximum(L, 1e-12) * r, P)
    return P, F


def smin(a, b, k):
    """polynomial smooth minimum (soft fillet of width k)."""
    hh = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - hh) + a * hh - k * hh * (1 - hh)


def _spow(x, e):
    return np.sign(x) * np.abs(x) ** e



def vert_normals(P, faces):
    VN = np.zeros_like(P)
    for Fx in faces:
        Fx = np.asarray(Fx)
        Q = P[Fx]
        n_ = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0])
        for k in range(Fx.shape[1]):
            np.add.at(VN, Fx[:, k], n_)
    return nrm(VN + 1e-12)



def frame_wall(az):
    """local stone frame on the ring at azimuth az: x along the ring (-tangent), y radial out, z up."""
    t = np.array([math.cos(az), math.sin(az), 0.0])
    u = np.array([math.sin(az), -math.cos(az), 0.0])
    return np.stack([-t, u, np.array([0, 0, 1.0])], -1)



def lathe(prof, segs, rfunc=None, phase=0.0):
    """revolve (r,z) profile ordered CCW in (r,z) (underside outward, outer surface upward)."""
    prof = np.asarray(prof, float)
    th = phase + 2 * np.pi * np.arange(segs) / segs
    Vs = []
    idx = []
    n = 0
    for (r, z) in prof:
        if r < 1e-6:
            Vs.append(np.array([[0.0, 0.0, z]]))
            idx.append(np.array([n]))
            n += 1
        else:
            rr = np.full(segs, r)
            if rfunc is not None:
                rr = rr * rfunc(th, z)
            Vs.append(np.stack([rr * np.cos(th), rr * np.sin(th), np.full(segs, z)], -1))
            idx.append(np.arange(n, n + segs))
            n += segs
    faces = []
    j = np.arange(segs)
    j1 = (j + 1) % segs
    for k in range(len(prof) - 1):
        a, b = idx[k], idx[k + 1]
        if len(a) > 1 and len(b) > 1:
            faces.append(np.stack([a[j], a[j1], b[j1], b[j]], -1))
        elif len(a) == 1 and len(b) > 1:
            faces.append(np.stack([np.full(segs, a[0]), b[j1], b[j]], -1))
        elif len(a) > 1 and len(b) == 1:
            faces.append(np.stack([a[j], a[j1], np.full(segs, b[0])], -1))
    V = np.concatenate(Vs)
    u = np.arctan2(V[:, 1], V[:, 0]) / (2 * np.pi) % 1.0
    return V, faces, np.stack([u, V[:, 2]], -1), True


def slab(P, Q):
    """closed slab from outer grid P (nu,nv,3) and inner grid Q (same). Outer normal = du x dv."""
    nu, nv = P.shape[:2]
    V = np.concatenate([P.reshape(-1, 3), Q.reshape(-1, 3)])
    off = nu * nv
    Fo = grid_quads(nu, nv)
    Fi = grid_quads(nu, nv, off)[:, ::-1]
    I = lambda i, j: i * nv + j  # noqa: E731
    sides = []
    i = np.arange(nu - 1)
    sides.append(np.stack([I(i + 1, 0), I(i, 0), I(i, 0) + off, I(i + 1, 0) + off], -1))
    t = nv - 1
    sides.append(np.stack([I(i, t), I(i + 1, t), I(i + 1, t) + off, I(i, t) + off], -1))
    j = np.arange(nv - 1)
    sides.append(np.stack([I(0, j), I(0, j + 1), I(0, j + 1) + off, I(0, j) + off], -1))
    e = nu - 1
    sides.append(np.stack([I(e, j + 1), I(e, j), I(e, j) + off, I(e, j + 1) + off], -1))
    return V, [Fo, Fi] + sides


def prism(outline, thick, ch=0.0015):
    """extrude a CCW 2-D outline (x,y) along +z from 0..thick with a small chamfer on top."""
    o = np.asarray(outline, float)
    m = len(o)
    c = o.mean(0)
    inset = c + (o - c) * (1 - ch / max(np.linalg.norm(o - c, axis=1).mean(), 1e-3))
    V = np.concatenate([
        np.c_[o, np.zeros(m)],
        np.c_[o, np.full(m, thick - ch)],
        np.c_[inset, np.full(m, thick)],
    ])
    j = np.arange(m)
    j1 = (j + 1) % m
    faces = [
        np.stack([j, j1, m + j1, m + j], -1),
        np.stack([m + j, m + j1, 2 * m + j1, 2 * m + j], -1),
        (2 * m + j)[None, :],
        j[::-1][None, :],
    ]
    return V, faces


def xf(V, R=None, t=(0, 0, 0)):
    V = np.asarray(V, float)
    if R is not None:
        V = V @ np.asarray(R).T
    return V + np.asarray(t, float)


def frame_R(x_axis, z_hint):
    x = nrm(np.asarray(x_axis, float))
    z = np.asarray(z_hint, float)
    z = nrm(z - np.dot(z, x) * x)
    y = np.cross(z, x)
    return np.stack([x, y, z], -1)



def R_y_to(d, hint=(0, 0, 1)):
    """rotation whose local +Y axis points along d."""
    y = nrm(np.asarray(d, float))
    h = np.asarray(hint, float)
    if abs(float(np.dot(h, y))) > 0.9:
        h = np.array([1.0, 0, 0])
    x = nrm(np.cross(y, h))
    z = np.cross(x, y)
    return np.stack([x, y, z], -1)



def open_tube(path, radius, rel_ang, outward, up, rr=None, close_mask=None, cap0=False, cap1=False, oval=1.0):
    """tube whose section is only the outward-facing arc `rel_ang` (radians about the outward direction):
    the back, which faces the daub / inner skin / a post and is never visible, is not modelled
    (producer note 6).  close_mask[i] closes the back of ring segment i with one flat quad (used where
    a free rod tip flicks out and its back could be glimpsed); cap0/cap1 close the end sections.
    rr: (n, m) per-ring radial factors (knobbly section)."""
    path = np.asarray(path, float)
    n = len(path)
    m = np.shape(rel_ang)[-1]
    rad = np.broadcast_to(np.asarray(radius, float), (n,))
    T, N, B = frames(path, up)
    mid = n // 2
    o = nrm(np.asarray(outward, float))
    c_ang = math.atan2(float(np.dot(o, B[mid])), float(np.dot(o, N[mid])))
    rel_ang = np.asarray(rel_ang, float)
    ang = c_ang + (rel_ang if rel_ang.ndim == 2 else rel_ang[None, :])
    if rr is None:
        rr = np.ones((n, m))
    # oval: squash the section along the outward axis
    cx = np.cos(ang) * rr
    cy = np.sin(ang) * rr
    ox, oy = math.cos(c_ang), math.sin(c_ang)
    along = cx * ox + cy * oy
    cx = cx - (1 - oval) * along * ox
    cy = cy - (1 - oval) * along * oy
    V = path[:, None, :] + (cx * rad[:, None])[..., None] * N[:, None, :] + (cy * rad[:, None])[..., None] * B[:, None, :]
    V = V.reshape(-1, 3)
    i = np.arange(n - 1)[:, None]
    j = np.arange(m - 1)[None, :]
    faces = [np.stack([i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j], -1).reshape(-1, 4)]
    if close_mask is not None and np.any(close_mask):
        ic = np.where(np.asarray(close_mask)[:n - 1])[0]
        faces.append(np.stack([ic * m + m - 1, ic * m, (ic + 1) * m, (ic + 1) * m + m - 1], -1))
    if cap0:
        faces.append(np.arange(m)[::-1][None, :])
    if cap1:
        faces.append(((n - 1) * m + np.arange(m))[None, :])
    seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
    alen = np.concatenate([[0], np.cumsum(seglen)])
    circ = 2 * np.pi * max(float(rad.mean()), 1e-3)
    u = np.tile(np.arange(m) / (m - 1) * 0.6, n)
    v = np.repeat(alen / circ, m)
    return V, faces, np.stack([u, v], -1)


def _runs(mask):
    """contiguous True runs -> list of (start, stop) index pairs."""
    m = np.concatenate([[False], np.asarray(mask, bool), [False]])
    d = np.diff(m.astype(np.int8))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))



# 2-D polygon helpers
def _poly_area(P):
    return 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))



def poly_sdf(s, z, P):
    """signed distance (m) from points to a closed polygon P (k, 2): positive inside."""
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    d = np.full(s.shape, np.inf)
    inside = np.zeros(s.shape, bool)
    k = len(P)
    for i in range(k):
        a, b = P[i], P[(i + 1) % k]
        e = b - a
        t = np.clip(((s - a[0]) * e[0] + (z - a[1]) * e[1]) / max(float(e @ e), 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(s - a[0] - t * e[0], z - a[1] - t * e[1]))
        cr = ((a[1] > z) != (b[1] > z)) & (s < a[0] + (z - a[1]) * e[0] / (b[1] - a[1] + 1e-12))
        inside ^= cr
    return np.where(inside, d, -d)



def _seg_dist(Sx, Zx, segs):
    """distance from grid points to a polyline (list of (s,z) points). returns dist, closest s,z, t along."""
    best = np.full(Sx.shape, 1e9)
    cs = np.zeros(Sx.shape)
    cz = np.zeros(Sx.shape)
    ct = np.zeros(Sx.shape)
    segs = np.asarray(segs, float)
    Ltot = np.sum(np.linalg.norm(np.diff(segs, axis=0), axis=1))
    acc_l = 0.0
    for k in range(len(segs) - 1):
        a = segs[k]
        b = segs[k + 1]
        d = b - a
        ll = float(np.dot(d, d))
        t = np.clip(((Sx - a[0]) * d[0] + (Zx - a[1]) * d[1]) / max(ll, 1e-12), 0, 1)
        px = a[0] + t * d[0]
        pz = a[1] + t * d[1]
        dist = np.hypot(Sx - px, Zx - pz)
        m = dist < best
        best = np.where(m, dist, best)
        cs = np.where(m, px, cs)
        cz = np.where(m, pz, cz)
        ct = np.where(m, (acc_l + t * math.sqrt(ll)) / Ltot, ct)
        acc_l += math.sqrt(ll)
    return best, cs, cz, ct



def ccw(prof):
    prof = np.asarray(prof, float)
    x, y = prof[:, 0], prof[:, 1]
    area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    return prof if area > 0 else prof[::-1]



def cull_object(ob, fn):
    """drop the faces of a built object whose vertices are all flagged by fn(V) (keeps UVs / Mask)."""
    import bmesh
    me = ob.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    flag = fn(V.reshape(-1, 3))
    if not flag.any():
        return 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    dead = [f for f in bm.faces if all(flag[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context="FACES_ONLY")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(dead)



# =============================================================================================
# producer note 11: detail-scale rule
# =============================================================================================
class DetailRule:
    """which modelled surface relief a component keeps (producer note 11, phase 2 onward).

    Geometry keeps silhouette / edge detail, every discrete piece, joints and recesses that cast real shadows,
    and relief >= min_relief (2 cm).  ENTRANCE EXCEPTION: within entrance_r (3 m, plan distance) of the main
    entrance and between 0 and entrance_h (2.5 m) high, relief >= entrance_relief (1 cm) is kept where it reads
    in grazing light at actor distance.  Everything shallower (daub shrinkage cracks, wood checks / splits, adze
    and saw marks, grain, chisel tooling, chips / spalls < 2 cm, straw striation, fine plank wear) goes to
    materials and decals.  DetailRule.off() reproduces the phase-1 (everything modelled) behaviour.

        rule.min_at(p)        relief threshold (m) at a world point
        rule.keeps(depth, p)  True when relief of `depth` at p is modelled
        rule.scale(depth, p)  1.0 / 0.0 multiplier for a relief component of amplitude `depth`
    """

    def __init__(self, min_relief=0.02, entrance_relief=0.01, entrance=(0.0, 0.0), entrance_r=3.0,
                 entrance_h=2.5, active=True):
        self.min_relief = min_relief
        self.entrance_relief = entrance_relief
        self.entrance = tuple(entrance)
        self.entrance_r = entrance_r
        self.entrance_h = entrance_h
        self.active = active

    @classmethod
    def off(cls):
        return cls(0.0, 0.0, active=False)

    def in_entrance(self, p):
        p = np.asarray(p, float)
        return (math.hypot(p[0] - self.entrance[0], p[1] - self.entrance[1]) <= self.entrance_r
                and -0.05 <= p[2] <= self.entrance_h)

    def min_at(self, p):
        if not self.active:
            return 0.0
        return self.entrance_relief if self.in_entrance(p) else self.min_relief

    def keeps(self, depth, p=(1e9, 1e9, 1e9)):
        return (not self.active) or depth >= self.min_at(p)

    def scale(self, depth, p=(1e9, 1e9, 1e9)):
        return 1.0 if self.keeps(depth, p) else 0.0


# =============================================================================================
# mesh accumulator
# =============================================================================================
class Acc:
    """numpy mesh accumulator.  One add() call = one PIECE (stone, shingle, rod, plank...) for the Mask
    attribute: R = per-piece random, G = per-piece wear (producer note 9).

    cull(V) -> bool per vertex 'never visible': faces whose vertices are all culled are dropped at build
    time (producer note 6).  z_clamp: vertices below it are lifted to it (buried-skirt limit, note 10).
    b_fn(V, VN) -> Mask B (moss / dirt / damp); moss: constant B instead.  hygiene: run nanite_clean() on the
    built mesh (remove doubles, dissolve degenerates, needle fix) -- the Mask follows the pieces through it.
    """

    def __init__(self, name, sharp_angle=40.0, cull=None, moss=None, z_clamp=None, b_fn=None, hygiene=False):
        self.name = name
        self.V, self.UV = [], []
        self.MR, self.MG = [], []                     # Mask R (per-piece random), G (per-piece wear)
        self.mrng = np.random.RandomState(zlib.crc32(name.encode()) & 0x7FFFFFFF)
        self.moss = moss
        self.b_fn = b_fn
        self.Fidx, self.Fsz, self.Fmat, self.Fsm, self.Fwrap = [], [], [], [], []
        self.n = 0
        self.mats = []
        self.sharp_angle = sharp_angle
        self.cull = cull
        self.z_clamp = z_clamp
        self.hygiene = hygiene

    def mi(self, m):
        palette.check(m)
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, V, faces, mat, uv=None, wrap=False, smooth=True, wear=None):
        """one call = one piece (stone, shingle, rod, plank...) for the Mask attribute."""
        V = np.asarray(V, float).reshape(-1, 3)
        if len(V) == 0:
            return
        r_ = self.mrng.rand()
        g_ = self.mrng.uniform(0.1, 0.45) if wear is None else wear
        self.MR.append(np.full(len(V), r_))
        self.MG.append(np.full(len(V), g_))
        base = self.n
        m = self.mi(mat)
        if isinstance(faces, np.ndarray):
            faces = [faces]
        for f in faces:
            f = np.asarray(f, np.int64)
            if f.ndim == 1:
                f = f[None]
            if len(f) == 0:
                continue
            self.Fidx.append((f + base).ravel())
            self.Fsz.append(np.full(len(f), f.shape[1], np.int64))
            self.Fmat.append(np.full(len(f), m, np.int64))
            self.Fsm.append(np.full(len(f), bool(smooth)))
            self.Fwrap.append(np.full(len(f), bool(wrap)))
        self.V.append(V)
        if uv is None:
            self.UV.append(np.full((len(V), 2), np.nan))
        else:
            self.UV.append(np.asarray(uv, float).reshape(-1, 2))
        self.n += len(V)

    def add_part(self, part, mat, smooth=True):
        self.add(part[0], part[1], mat, part[2] if len(part) > 2 else None,
                 wrap=part[3] if len(part) > 3 else False, smooth=smooth)

    def ntris(self):
        if not self.Fsz:
            return 0
        return int(np.sum(np.concatenate(self.Fsz) - 2))

    def build_mesh(self, name=None, clamp=True):
        V = np.concatenate(self.V)
        if clamp and self.z_clamp is not None:
            V[:, 2] = np.maximum(V[:, 2], self.z_clamp)
        UVv = np.concatenate(self.UV)
        MR = np.concatenate(self.MR)
        MG = np.concatenate(self.MG)
        fidx = np.concatenate(self.Fidx)
        fsz = np.concatenate(self.Fsz)
        fmat = np.concatenate(self.Fmat)
        fsm = np.concatenate(self.Fsm)
        fwrap = np.concatenate(self.Fwrap)
        # ---- cull never-visible faces (all vertices culled)
        if self.cull is not None:
            vh = self.cull(V)
            starts0 = np.concatenate([[0], np.cumsum(fsz)[:-1]])
            allh = np.minimum.reduceat(vh[fidx].astype(np.int8), starts0).astype(bool)
            keep = ~allh
            if not keep.all():
                lk = np.repeat(keep, fsz)
                fidx, fsz, fmat, fsm, fwrap = fidx[lk], fsz[keep], fmat[keep], fsm[keep], fwrap[keep]
        # ---- drop unused vertices
        used = np.zeros(len(V), bool)
        used[fidx] = True
        remap = np.cumsum(used) - 1
        V, UVv, MR, MG, fidx = V[used], UVv[used], MR[used], MG[used], remap[fidx]
        me = bpy.data.meshes.new(name or self.name)
        me.vertices.add(len(V))
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        me.loops.add(len(fidx))
        me.loops.foreach_set("vertex_index", fidx.astype(np.int32))
        starts = np.concatenate([[0], np.cumsum(fsz)[:-1]]).astype(np.int32)
        me.polygons.add(len(fsz))
        me.polygons.foreach_set("loop_start", starts)
        me.update(calc_edges=True)
        me.polygons.foreach_set("material_index", fmat.astype(np.int32))
        me.polygons.foreach_set("use_smooth", fsm)
        for m in self.mats:
            me.materials.append(palette.material(m))
        # ---- UVs: per-vertex where given, box projection elsewhere ----
        fn = np.zeros(len(fsz) * 3, np.float32)
        me.polygons.foreach_get("normal", fn)
        fn = fn.reshape(-1, 3)
        lface = np.repeat(np.arange(len(fsz)), fsz)
        luv = UVv[fidx].copy()
        bad = np.isnan(luv[:, 0])
        if bad.any():
            co = V[fidx[bad]]
            nn = np.abs(fn[lface[bad]])
            ax = np.argmax(nn, axis=1)
            u = np.where(ax == 0, co[:, 1], co[:, 0])
            v = np.where(ax == 2, co[:, 1], co[:, 2])
            luv[bad, 0] = u
            luv[bad, 1] = v
        if fwrap.any():
            u = luv[:, 0]
            umax = np.maximum.reduceat(u, starts)
            umin = np.minimum.reduceat(u, starts)
            fix = fwrap & ((umax - umin) > 0.5)
            lfix = fix[lface] & (u < 0.5)
            luv[lfix, 0] += 1.0
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", luv.astype(np.float32).ravel())
        me.set_sharp_from_angle(angle=math.radians(self.sharp_angle))
        me.validate(clean_customdata=False)
        # ---- per-piece Mask R / G ride along as point attributes through validate() / hygiene
        if len(me.vertices) == len(MR):
            for nm_, arr in (("_mask_r", MR), ("_mask_g", MG)):
                at = me.attributes.new(nm_, "FLOAT", "POINT")
                at.data.foreach_set("value", arr.astype(np.float32))
        if self.hygiene:
            # hygiene=True -> nanite_clean; a callable hygiene(me) is a building's own hook (kit 1.1.0,
            # e.g. geom.strict_clean), run at the same point (after validate, before the Mask is written)
            (self.hygiene if callable(self.hygiene) else nanite_clean)(me)
        _mask.write_mask(me, b_fn=self.b_fn, moss=self.moss)
        return me

    def build(self, coll):
        me = self.build_mesh()
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        log(f"  {self.name}: {len(me.vertices)} verts, {len(me.polygons)} faces")
        return ob


# =============================================================================================
# Nanite hygiene (producer note 1): no zero-area / degenerate faces, no needle triangles
# =============================================================================================
def sliver_report(me, h_min=1e-4, a_min=1e-8):
    """(number of loop triangles with altitude 2*area/longest-edge < h_min, number of polygons with area <
    a_min), judged on the float32 positions the mesh stores (the windmill's round-6 test)."""
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    if n == 0:
        return 0, 0
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3).astype(np.float64)
    T = np.empty(n * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", T)
    T = T.reshape(-1, 3)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    ar = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    le = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                          np.linalg.norm(a - c, axis=1)]), 0)
    alt = 2 * ar / np.maximum(le, 1e-30)
    pa = np.empty(len(me.polygons), np.float32)
    me.polygons.foreach_get("area", pa)
    return int((alt < h_min).sum()), int((pa < a_min).sum())


def _needle_faces(bm, h_min):
    bm.verts.index_update()
    tris = bm.calc_loop_triangles()
    if not tris:
        return []
    co = np.array([v.co[:] for v in bm.verts])
    I = np.array([[l_.vert.index for l_ in t] for t in tris])
    A, B, C = co[I[:, 0]], co[I[:, 1]], co[I[:, 2]]
    ar2 = np.linalg.norm(np.cross(B - A, C - A), axis=1)
    L = np.max(np.stack([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1),
                         np.linalg.norm(A - C, axis=1)]), axis=0)
    bad = ar2 / np.maximum(L, 1e-12) < h_min
    return list({tris[i][0].face for i in np.flatnonzero(bad)})


def nanite_clean(me, merge_dist=1e-4, h_min=1e-4, iters=5):
    """merge coincident vertices (remove doubles), dissolve degenerate edges / faces, then fix needle
    triangles: bad n-gons are re-triangulated (beauty), sub-mm edges of slivers collapsed, long edges flipped;
    whatever is still a sliver (< 0.1 mm wide) is deleted (the keep's round-6 fix_needles).  In place."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=merge_dist)
    for it in range(iters):
        bad_f = _needle_faces(bm, h_min)
        if not bad_f:
            break
        ngon = [f for f in bad_f if len(f.verts) > 3]
        if ngon:
            bmesh.ops.triangulate(bm, faces=ngon, quad_method="BEAUTY", ngon_method="BEAUTY")
            bad_f = _needle_faces(bm, h_min)
            if not bad_f:
                break
        if it == iters - 1:
            bmesh.ops.delete(bm, geom=[f for f in bad_f if f.is_valid], context="FACES")
            break
        short, longe = set(), set()
        for f in bad_f:
            if len(f.verts) != 3:
                continue
            es = sorted(f.edges, key=lambda e: e.calc_length())
            if es[0].calc_length() < 1e-3:
                short.add(es[0])
            elif es[-1].is_manifold:
                longe.add(es[-1])
        if longe:
            bmesh.ops.rotate_edges(bm, edges=[e for e in longe if e.is_valid and e not in short], use_ccw=False)
        if short:
            bmesh.ops.collapse(bm, edges=[e for e in short if e.is_valid], uvs=True)
    zero = [f for f in bm.faces if f.calc_area() < 5e-9]
    if zero:
        bmesh.ops.delete(bm, geom=zero, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return sliver_report(me, h_min)


# =============================================================================================
# hidden-geometry removal (producer note 6)
# =============================================================================================
_VIS = {}


def _vis_worker(chunk):
    from mathutils import Vector
    bvh, T, own, Vw = _VIS["bvh"], _VIS["T"], _VIS["own"], _VIS["V"]
    views, VN = _VIS["views"], _VIS["views_np"]
    hidden = []
    for pid, tri_ids in chunk:
        vis = False
        for ti in tri_ids:
            p0, p1, p2 = (Vector(Vw[i]) for i in T[ti])
            cen = (p0 + p1 + p2) / 3
            nrm_ = (p1 - p0).cross(p2 - p0)
            nrm_ = nrm_.normalized() if nrm_.length > 1e-12 else Vector((0, 0, 1))
            pts = [cen] + [cen + (p - cen) * 0.8 for p in (p0, p1, p2)]
            dv = VN - np.array(cen)
            fac = (dv @ np.array(nrm_)) / np.maximum(np.linalg.norm(dv, axis=1), 1e-9)
            for side in (1, -1):
                ns = nrm_ * side
                order = [views[i] for i in np.argsort(-fac * side)]       # most frontal viewpoints first
                for pt in pts:
                    probe = pt + ns * 0.002
                    for v in order:
                        if (v - pt).dot(ns) <= 0:
                            continue
                        d = probe - v
                        dist = d.length
                        if dist < 1e-6:
                            continue
                        hit = bvh.ray_cast(v, d / dist, dist + 0.01)
                        if hit[2] is not None and (own[hit[2]] == pid or (hit[0] - pt).length < 0.004):
                            vis = True
                            break
                    if vis:
                        break
                if vis:
                    break
            if vis:
                break
        if not vis:
            hidden.append(pid)
    return hidden


def review_views(lo, hi):
    """the exterior viewpoints the review tool's hidden-triangle estimate uses (eye-level rings at 1.4 / 2.5 x
    the half-size, a mid ring, crane and aerial rings, a top view), from the scene bounds lo / hi."""
    c = (np.asarray(lo, float) + np.asarray(hi, float)) / 2
    r = max(hi[0] - lo[0], hi[1] - lo[1]) / 2
    gz = max(lo[2], 0.0)
    V = []
    for dist_f, z, count in ((1.4, gz + 1.7, 24), (2.5, gz + 1.7, 16), (2.0, gz + (hi[2] - gz) * 0.6, 16),
                             (2.2, hi[2] + r * 1.2, 12), (1.6, hi[2] + r * 2.5, 8)):
        for k in range(count):
            ang = 2 * math.pi * (k + 0.5 * (dist_f > 2)) / count
            V.append((c[0] + math.cos(ang) * r * dist_f, c[1] + math.sin(ang) * r * dist_f, z))
    V.append((c[0], c[1], hi[2] + r * 4))
    return np.array(V)


def review_cameras(lo, hi):
    """positions of the review renderer's six cameras (hero, front, side, back, aerial, actor_closeup) for scene
    bounds lo / hi -- so a visibility cull never removes what a review render can see."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    views = {"hero": (-35, 8, 2.2, 35, 0.35), "front": (0, 4, 2.4, 50, 0.4), "side": (90, 4, 2.4, 50, 0.4),
             "back": (180, 12, 2.4, 40, 0.4), "aerial": (-50, 38, 2.6, 40, 0.3),
             "actor_closeup": (-20, 2, 0.9, 28, 0.12)}
    c = (lo + hi) / 2
    size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], 4.0)
    out = []
    for name, (az, el, dist_f, lens, look_f) in views.items():
        target = np.array([c[0], c[1], lo[2] + (hi[2] - lo[2]) * look_f])
        dist = size * dist_f * (lens / 35)
        if name == "actor_closeup":
            target = np.array([c[0], lo[1], lo[2] + 1.5])
            dist = max(size * 0.45, 4.0)
        a_, e_ = math.radians(az), math.radians(el)
        d = np.array([math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_)])
        p = target + d * dist
        if name == "actor_closeup":
            p[2] = max(lo[2] + 1.65, p[2])
        out.append(p)
    return np.array(out)


def ring_views(center, radii, heights, n=24, phase=0.37):
    """actor / crane viewpoints on rings round a centre: every (radius, height) pair, n stations each."""
    out = []
    for r_ in np.atleast_1d(radii):
        for z_ in np.atleast_1d(heights):
            for k in range(n):
                a = 2 * math.pi * (k + phase) / n
                out.append((center[0] + r_ * math.cos(a), center[1] + r_ * math.sin(a), z_))
    return np.array(out)


def visibility_cull(targets, extra_views=(), procs=3, extra_by_target=None, objects=None, min_keep=0):
    """delete the polygons of the target objects (names) that no viewpoint can see: the review viewpoints
    (review_views) plus extra_views (actor-scale near views, door views...), sampled at each triangle's centroid
    and near its corners, from both sides -- the same test the review tool applies.  Occluders are all mesh
    objects in `objects` (default: every mesh in the file, instances placed by their matrices).  Returns the
    number of polygons deleted.  Never run it on a backing surface whose job is to be seen through gaps."""
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    import multiprocessing as mp
    obs = objects if objects is not None else [o for o in bpy.data.objects if o.type == "MESH"]
    Vs, Ts, owns = [], [], []
    tri_base = {}
    nv = nt = 0
    for oi, ob in enumerate(obs):
        me = ob.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", lt)
        lp = np.zeros(len(me.loop_triangles), np.int64)
        me.loop_triangles.foreach_get("polygon_index", lp)
        Vs.append(co)
        Ts.append(lt.reshape(-1, 3) + nv)
        tri_base[ob.name] = (nt, lp)
        owns.append(lp + (oi + 1) * 10 ** 7)                  # unique id per polygon
        nv += len(co)
        nt += len(lp)
    Vw = np.concatenate(Vs)
    T = np.concatenate(Ts)
    own = np.concatenate(owns)
    lo, hi = Vw.min(0), Vw.max(0)
    base = [tuple(map(float, v)) for v in review_views(lo, hi)] + [tuple(map(float, v)) for v in extra_views]
    bvh = BVHTree.FromPolygons(Vw.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)
    _VIS.update(bvh=bvh, V=Vw, T=T, own=own)
    log(f"  visibility: {nt} tris, {len(base)} viewpoints")
    total = 0
    for name in targets:
        if name not in tri_base:
            continue
        t0, lp = tri_base[name]
        if len(lp) == 0:
            continue
        ob = bpy.data.objects[name]
        views = [Vector(v) for v in base] + [Vector(tuple(map(float, e)))
                                            for e in (extra_by_target or {}).get(name, ())]
        _VIS["views"] = views
        _VIS["views_np"] = np.array([tuple(v) for v in views])
        order = np.argsort(lp, kind="stable")
        bounds = np.flatnonzero(np.diff(lp[order])) + 1
        groups = np.split(order + t0, bounds)
        items = [(int(own[g_[0]]), [int(x) for x in g_]) for g_ in groups]
        chunks = [items[i::procs * 8] for i in range(procs * 8)]
        try:
            with mp.get_context("fork").Pool(procs) as pool:
                res = pool.map(_vis_worker, chunks)
        except Exception as ex:                                   # no fork available: single process
            log("  (visibility: single process)", ex)
            res = [_vis_worker(c_) for c_ in chunks]
        hid = sorted(set(int(h) for r_ in res for h in r_))
        base_id = int(own[t0]) - int(lp[0])
        pids = [h - base_id for h in hid]
        if len(pids) <= min_keep:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in pids], context="FACES_ONLY")
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        total += len(pids)
        log(f"  visibility cull {name}: -{len(pids)} of {len(groups)} polygons")
    return total


# =============================================================================================
# scene / file helpers
# =============================================================================================
def reset_scene():
    """empty factory scene, metric units (every build starts here, art bible section 8)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent is not None else bpy.context.scene.collection.children).link(c)
    return c


def count_triangles(objects):
    tris = 0
    for ob in objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            tris += len(ob.data.loop_triangles)
    return tris


def save_blend(path):
    """save compressed (art bible section 8), no .blend1 backup next to the deliverable."""
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    if os.path.exists(path + "1"):
        os.remove(path + "1")
    log("saved", path, f"{os.path.getsize(path) / 1e6:.1f} MB")
    return path


# public names for the 2-D helpers
poly_area = _poly_area
seg_dist = _seg_dist
runs = _runs
spow = _spow
