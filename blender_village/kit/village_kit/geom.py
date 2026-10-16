"""village_kit.geom -- vectorised mesh primitives and the strict hygiene hook of the polygonal / tiered buildings.

Added in kit 1.1.0 with the hilltop-keep migration.  Everything here is generic (no building dimensions):

  noise            n1 / fbm90 / vnoise90: value noise on the keep's historic table (core.Noise(90210)); fbm90 is
                   the un-normalised 3-octave sum the keep's shapes were tuned with
  rounded boxes    rbox_v(X, Y, Z, r): MANY rounded / chamfered boxes at once from per-instance axis coordinate
                   arrays (rows of ax4 / ax5 / axn / axr); inst_faces() offsets the shared quad topology
  sweeps           sweep(path, ups, prof): a closed profile (or one profile per station) swept along a path;
                   prof_rect / prof_circle; lathe_rz((r, z) profile)
  oriented boxes   obox(acc, O, EX, EY, EZ, LX, LY, LZ, r, mat): boards / blocks / timber in any frame; beam(p0, p1)
  2-D helpers      rot2, rounded_outline, inside_poly, catmull_closed, smooth_wave, softplus, box_sum, runs_of
  frames           frame_matrix, axis_matrix (local +Z -> axis), R_of(M)
  hygiene          strict_clean(me): producer notes 1 / 6 / 9 clean-up used as a core.Acc `hygiene` hook --
                   clip at the buried-skirt limit (-5 cm) and drop faces lying on it, core.nanite_clean (remove
                   doubles, degenerates, needle fix), zero-area < 5e-8 m2, outward normals, a mesh-tessellation
                   re-pass for n-gons, the sharp-edge angle re-applied after the clean-up, and the per-ISLAND Mask
                   R / G (village_kit.mask fallback 3: every connected piece -- stone, shingle, plank -- gets its
                   own R / wear G even when a whole wall of stones was added in one Acc.add() call)
  Acc / finalize   Acc(name) -> core.Acc without a ground cull; finalize(acc, coll, smooth_deg, recalc, clip_z)
                   builds it with strict_clean (None for an empty accumulator)
"""
import math
from functools import partial

import numpy as np

from .core import Noise, nrm  # noqa: F401
from . import core

CLIP_Z = -0.05            # nothing below 5 cm under the ground (producer notes 1 / 6 / 10)
TAN22 = math.tan(math.radians(22.5))

# ---------------------------------------------------------------------------------------------------------------
# noise on the keep's historic table (seed 90210)
# ---------------------------------------------------------------------------------------------------------------
_N90 = Noise(90210)


def vnoise90(p):
    return _N90.vnoise(p)


def fbm90(p, octaves=3):
    """un-normalised fbm (sum of octaves, gain 0.5, lacunarity 2.03), the keep's shape noise."""
    return _N90.fbm(p, octaves, normalize=False)


def n1(x, seed, freq=1.0):
    """smooth 1-D noise in about [-1, 1]."""
    x = np.asarray(x, float)
    return vnoise90(np.stack([x * freq, np.full_like(x, seed * 17.31), np.full_like(x, seed * 3.7)], -1))


def hash01(x, seed=0.0):
    x = np.asarray(x, np.float64)
    v = np.sin(x * 12.9898 + seed * 78.233 + 0.5) * 43758.5453
    return v - np.floor(v)


# ---------------------------------------------------------------------------------------------------------------
# vectorised rounded boxes
# ---------------------------------------------------------------------------------------------------------------
_TOPO = {}


def rbox_topo(nx, ny, nz, skip_back=False, skip_front=False):
    key = (nx, ny, nz, skip_back, skip_front)
    if key in _TOPO:
        return _TOPO[key]
    idx = -np.ones((nx, ny, nz), np.int64)
    pts = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                onb = i in (0, nx - 1) or j in (0, ny - 1) or k in (0, nz - 1)
                if not onb:
                    continue
                inner_ij = 0 < i < nx - 1 and 0 < j < ny - 1
                if skip_back and k == 0 and inner_ij:
                    continue
                if skip_front and k == nz - 1 and inner_ij:
                    continue
                idx[i, j, k] = len(pts)
                pts.append((i, j, k))
    q = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            if not skip_front:
                k = nz - 1
                q.append((idx[i, j, k], idx[i + 1, j, k], idx[i + 1, j + 1, k], idx[i, j + 1, k]))
            if not skip_back:
                q.append((idx[i, j, 0], idx[i, j + 1, 0], idx[i + 1, j + 1, 0], idx[i + 1, j, 0]))
    for j in range(ny - 1):
        for k in range(nz - 1):
            i = nx - 1
            q.append((idx[i, j, k], idx[i, j + 1, k], idx[i, j + 1, k + 1], idx[i, j, k + 1]))
            q.append((idx[0, j, k], idx[0, j, k + 1], idx[0, j + 1, k + 1], idx[0, j + 1, k]))
    for k in range(nz - 1):
        for i in range(nx - 1):
            j = ny - 1
            q.append((idx[i, j, k], idx[i, j, k + 1], idx[i + 1, j, k + 1], idx[i + 1, j, k]))
            q.append((idx[i, 0, k], idx[i + 1, 0, k], idx[i + 1, 0, k + 1], idx[i, 0, k + 1]))
    res = (np.array(pts, np.int64), np.array(q, np.int64))
    _TOPO[key] = res
    return res


def rbox_v(X, Y, Z, r, skip_back=False, skip_front=False, round_back=True, chamfer=False):
    """rounded boxes from per-instance axis coordinate arrays X (M, nx), Y (M, ny), Z (M, nz) and radii r (M,).
    Returns P (M, V, 3) and the shared quads (Q, 4) (per-instance local indices; see inst_faces).
    kit 1.5.0: chamfer=True -> true planar 45 deg chamfers of leg r instead of round-overs (L1 instead of L2
    normalisation of the corner offset)."""
    X, Y, Z = np.atleast_2d(X), np.atleast_2d(Y), np.atleast_2d(Z)
    gi, quads = rbox_topo(X.shape[1], Y.shape[1], Z.shape[1], skip_back, skip_front)
    P = np.stack([X[:, gi[:, 0]], Y[:, gi[:, 1]], Z[:, gi[:, 2]]], -1)
    r = np.broadcast_to(np.asarray(r, float), (X.shape[0],))
    lo = np.stack([X[:, 0] + r, Y[:, 0] + r, (Z[:, 0] + r) if round_back else np.full(len(r), -1e9)], -1)[:, None, :]
    hi = np.stack([X[:, -1] - r, Y[:, -1] - r, Z[:, -1] - r], -1)[:, None, :]
    C = np.clip(P, lo, hi)
    D = P - C
    n = np.abs(D).sum(-1, keepdims=True) if chamfer else np.linalg.norm(D, axis=-1, keepdims=True)
    P = np.where(n > 1e-9, C + D / np.maximum(n, 1e-9) * r[:, None, None], P)
    return P, quads


def inst_faces(quads, M, V):
    return (quads[None, :, :] + (np.arange(M) * V)[:, None, None]).reshape(-1, quads.shape[1])


def ax5(h, r):
    z = np.zeros_like(h)
    return np.stack([-h, -h + r, z, h - r, h], 1)


def ax4(h, r):
    return np.stack([-h, -h + r, h - r, h], 1)


def axn(a, b, r, n):
    """n >= 4 coordinates from a to b with chamfer rows at r from the ends."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    inner = [a + r] + [a + (b - a) * (i / (n - 3)) for i in range(1, n - 3)] + [b - r]
    return np.stack([a] + inner + [b], 1)


def axr(h, r, n):
    """n >= 8 coordinates from -h..h with a 2-segment rounded arris band (-h, -h + 0.3 r, -h + r, ..., h)."""
    h = np.asarray(h, float)
    r = np.asarray(r, float)
    ni = n - 6
    inner = [-h + r + (2 * h - 2 * r) * (i / (ni - 1)) for i in range(ni)]
    return np.stack([-h, -h + 0.3 * r] + inner + [h - 0.3 * r, h], 1)


# ---------------------------------------------------------------------------------------------------------------
# sweeps, lathe
# ---------------------------------------------------------------------------------------------------------------
def sweep(path, ups, prof, caps=True):
    """sweep a closed CCW profile (m, 2) [right, up] (or one per station, (n, m, 2)) along path (n, 3).
    Returns verts, [quads, caps]."""
    path = np.asarray(path, float)
    ups = np.broadcast_to(np.asarray(ups, float), path.shape)
    n = len(path)
    T = np.zeros_like(path)
    T[1:-1] = path[2:] - path[:-2]
    T[0] = path[1] - path[0]
    T[-1] = path[-1] - path[-2]
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    U = ups - (ups * T).sum(1, keepdims=True) * T
    U /= np.linalg.norm(U, axis=1, keepdims=True)
    R = np.cross(U, T)
    prof = np.asarray(prof, float)
    if prof.ndim == 2:
        prof = np.broadcast_to(prof, (n,) + prof.shape)
    m = prof.shape[1]
    V = path[:, None, :] + prof[:, :, 0:1] * R[:, None, :] + prof[:, :, 1:2] * U[:, None, :]
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    a = i * m + j
    b = i * m + (j + 1) % m
    quads = np.stack([a, b, b + m, a + m], -1).reshape(-1, 4)
    faces = [quads]
    if caps:
        faces.append(np.arange(m)[::-1][None, :])
        faces.append((n - 1) * m + np.arange(m)[None, :])
    return V.reshape(-1, 3), faces


def prof_rect(w, h, c):
    w2, h2 = w / 2, h / 2
    return np.array([(w2, -h2 + c), (w2, h2 - c), (w2 - c, h2), (-w2 + c, h2), (-w2, h2 - c),
                     (-w2, -h2 + c), (-w2 + c, -h2), (w2 - c, -h2)])


def prof_circle(r, n=8):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([r * np.cos(a), r * np.sin(a)], 1)


def lathe_rz(prof_rz, seg, cx=0.0, cy=0.0, z0=0.0, cap_bottom=True, cap_top=True, phase=0.0):
    """revolve an (r, z) profile about the vertical axis through (cx, cy).  Returns V, [quads, caps]."""
    prof = np.asarray(prof_rz, float)
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False) + phase
    nr = len(prof)
    V = np.zeros((nr, seg, 3))
    V[:, :, 0] = cx + prof[:, 0:1] * np.cos(a)[None]
    V[:, :, 1] = cy + prof[:, 0:1] * np.sin(a)[None]
    V[:, :, 2] = z0 + prof[:, 1:2]
    V = V.reshape(-1, 3)
    i = np.arange(nr - 1)[:, None]
    j = np.arange(seg)[None, :]
    A = i * seg + j
    B = i * seg + (j + 1) % seg
    faces = [np.stack([A, B, B + seg, A + seg], -1).reshape(-1, 4)]
    extra = []
    if cap_bottom and prof[0, 0] > 1e-6:
        extra.append(np.arange(seg)[::-1][None])
    if cap_top and prof[-1, 0] > 1e-6:
        extra.append(((nr - 1) * seg + np.arange(seg))[None])
    return V, faces + extra


# ---------------------------------------------------------------------------------------------------------------
# frames, oriented boxes
# ---------------------------------------------------------------------------------------------------------------
def rot2(x, y, a):
    c, s = np.cos(a), np.sin(a)
    return x * c - y * s, x * s + y * c


def frame_matrix(origin, ex, ey, ez):
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ex, ey, ez, origin
    return M


def axis_matrix(p, axis, roll=0.0):
    """4x4: local +Z -> axis at p (orthonormal frame, optional roll about the axis)."""
    z = np.asarray(axis, float)
    z = z / np.linalg.norm(z)
    up = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    c, s = math.cos(roll), math.sin(roll)
    x, y = x * c + y * s, -x * s + y * c
    return frame_matrix(np.asarray(p, float), x, y, z)


def obox(acc, O, EX, EY, EZ, LX, LY, LZ, r, mat, nx=4, ny=4, nz=4, deform=None, grain_uv=True, skip_back=False,
         skip_front=False):
    """boxes: x in [0, LX] along EX, y in [-LY/2, LY/2] along EY, z in [-LZ/2, LZ/2] along EZ (M at once)."""
    O = np.atleast_2d(np.asarray(O, float))
    M = len(O)
    bc = lambda a: np.broadcast_to(np.asarray(a, float), (M,)).copy()  # noqa: E731
    LX, LY, LZ, r = bc(LX), bc(LY), bc(LZ), bc(r)
    r = np.minimum(r, np.minimum(np.minimum(LX, LY), LZ) * 0.45)
    EX = np.broadcast_to(np.asarray(EX, float), (M, 3))
    EY = np.broadcast_to(np.asarray(EY, float), (M, 3))
    EZ = np.broadcast_to(np.asarray(EZ, float), (M, 3))
    X = axn(np.zeros(M), LX, r, nx)
    Y = axn(-LY / 2, LY / 2, r, ny)
    Z = axn(-LZ / 2, LZ / 2, r, nz)
    P, quads = rbox_v(X, Y, Z, r, skip_back=skip_back, skip_front=skip_front)
    if deform is not None:
        P = deform(P)
    W = O[:, None, :] + P[..., 0:1] * EX[:, None, :] + P[..., 1:2] * EY[:, None, :] + P[..., 2:3] * EZ[:, None, :]
    det = np.einsum("ij,ij->i", np.cross(EX, EY), EZ)
    if (det < 0).any():
        fq = inst_faces(quads, M, P.shape[1]).reshape(M, -1, 4)
        fq[det < 0] = fq[det < 0][:, :, ::-1]
        faces = fq.reshape(-1, 4)
    else:
        faces = inst_faces(quads, M, P.shape[1])
    uv = None
    if grain_uv:
        uv = np.stack([P[..., 0], P[..., 1] + P[..., 2]], -1).reshape(-1, 2)
    acc.add(W.reshape(-1, 3), faces, mat, uv=uv)


def beam(acc, p0, p1, w, h, c, mat, up=(0, 0, 1), nx=4, deform=None):
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    ex = d / L
    up = np.asarray(up, float)
    ey = np.cross(up, ex)
    if np.linalg.norm(ey) < 1e-6:
        ey = np.cross((1, 0, 0), ex)
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    obox(acc, p0[None], ex, ey, ez, L, w, h, c, mat, nx=nx, deform=deform)


# ---------------------------------------------------------------------------------------------------------------
# 2-D helpers
# ---------------------------------------------------------------------------------------------------------------
def inside_poly(px, py, poly):
    """vectorised crossing-number point-in-polygon."""
    inside = np.zeros(np.broadcast(px, py).shape, bool)
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]
        x2, y2 = poly[(k + 1) % n]
        cond = ((y1 > py) != (y2 > py))
        xi = x1 + (py - y1) * (x2 - x1) / ((y2 - y1) if abs(y2 - y1) > 1e-12 else 1e-12)
        inside ^= cond & (px < xi)
    return inside


def rounded_outline(poly, rc, spacing):
    """resample a polygon with corners rounded at radius rc; returns points (N, 2) and inward unit normals."""
    P = np.asarray(poly, float)
    n = len(P)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        P = P[::-1]
    out = []
    for k in range(n):
        a, b, c = P[k - 1], P[k], P[(k + 1) % n]
        d1 = (a - b) / max(np.linalg.norm(a - b), 1e-9)
        d2 = (c - b) / max(np.linalg.norm(c - b), 1e-9)
        cosang = float(np.clip(np.dot(d1, d2), -0.999, 0.999))
        half = math.acos(cosang) / 2
        t = min(rc / max(math.tan(half), 1e-3), 0.45 * np.linalg.norm(a - b), 0.45 * np.linalg.norm(c - b))
        p1, p2 = b + d1 * t, b + d2 * t
        for tt in ((0.0, 1.0) if t < 0.012 else (0.0, 0.5, 1.0)):
            out.append((1 - tt) ** 2 * p1 + 2 * tt * (1 - tt) * b + tt ** 2 * p2)
    O = np.array(out)
    pts = []
    m = len(O)
    for k in range(m):
        a, b = O[k], O[(k + 1) % m]
        L = np.linalg.norm(b - a)
        ns = max(1, int(math.ceil(L / spacing)))
        for j in range(ns):
            pts.append(a + (b - a) * (j / ns))
    Q = np.array(pts)
    keep = np.ones(len(Q), bool)
    dd = np.linalg.norm(np.diff(np.vstack([Q, Q[:1]]), axis=0), axis=1)
    keep[1:] = dd[:-1] > 1e-5
    Q = Q[keep]
    T = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    return Q, N


def box_sum(A, k):
    """sum over a (2k+1)^2 window (zero padded) via a summed-area table."""
    A = A.astype(np.int32)
    P = np.pad(A, ((k + 1, k), (k + 1, k)))
    C = P.cumsum(0).cumsum(1)
    n0, n1_ = A.shape
    w = 2 * k + 1
    return C[w:w + n0, w:w + n1_] - C[0:n0, w:w + n1_] - C[w:w + n0, 0:n1_] + C[0:n0, 0:n1_]


def catmull_closed(C, n_per):
    """closed Catmull-Rom resample of control polygon C (k, 2); n_per samples per span (array or int)."""
    k = len(C)
    n_per = np.broadcast_to(np.asarray(n_per), (k,))
    out, seg_id = [], []
    for i in range(k):
        p0, p1, p2, p3 = C[i - 1], C[i], C[(i + 1) % k], C[(i + 2) % k]
        for t in np.linspace(0, 1, int(n_per[i]), endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
            seg_id.append(i + t)
    return np.array(out), np.array(seg_id)


def smooth_wave(A, rng, lam=(2.0, 4.0), n=3):
    """sum of n sines with random wavelengths in lam and random phases, normalised to [-1, 1]."""
    A = np.asarray(A, float)
    w = rng.uniform(0.5, 1.0, n)
    w /= w.sum()
    out = np.zeros_like(A)
    for wi in w:
        out += wi * np.sin(2 * np.pi * A / rng.uniform(*lam) + rng.uniform(0, 2 * np.pi))
    return out


def softplus(d, k):
    return k * np.logaddexp(0.0, d / k)


def runs_of(P, ok, min_len=3):
    """contiguous runs of the points P whose flag `ok` is set (arrays of >= min_len points)."""
    runs, cur = [], []
    for i, o in enumerate(list(ok) + [False]):
        if o:
            cur.append(P[i])
        else:
            if len(cur) >= min_len:
                runs.append(np.array(cur))
            cur = []
    return runs


def runs_of_list(pts, min_len=3):
    """runs of consecutive non-None entries of a list."""
    runs, cur = [], []
    for p_ in list(pts) + [None]:
        if p_ is None:
            if len(cur) >= min_len:
                runs.append(np.array(cur))
            cur = []
        else:
            cur.append(p_)
    return runs


# ---------------------------------------------------------------------------------------------------------------
# strict hygiene hook + accumulator helpers
# ---------------------------------------------------------------------------------------------------------------
def mesh_needle_polys(me, h_min=1e-4):
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    if n == 0:
        return np.zeros(0, int)
    t = np.zeros(n * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", t)
    t = t.reshape(-1, 3)
    pi = np.zeros(n, np.int64)
    me.loop_triangles.foreach_get("polygon_index", pi)
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    A, B, C = co[t[:, 0]], co[t[:, 1]], co[t[:, 2]]
    ar2 = np.linalg.norm(np.cross(B - A, C - A), axis=1)
    L = np.max(np.stack([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1),
                         np.linalg.norm(A - C, axis=1)]), axis=0)
    return np.unique(pi[ar2 / np.maximum(L, 1e-12) < h_min])


def strict_clean(me, clip_z=CLIP_Z, recalc=True, sharp_deg=None, min_area=5e-8, islands=True):
    """core.Acc hygiene hook (see module doc).  In place."""
    import bmesh
    if islands:
        for nm_ in ("_mask_r", "_mask_g"):
            if nm_ in me.attributes:
                me.attributes.remove(me.attributes[nm_])
    if clip_z is not None:
        bm = bmesh.new()
        bm.from_mesh(me)
        low = [v for v in bm.verts if v.co.z < clip_z]
        for v in low:
            v.co.z = clip_z
        flat = [f for f in bm.faces if all(v.co.z <= clip_z + 1e-6 for v in f.verts)]
        if flat:
            bmesh.ops.delete(bm, geom=flat, context="FACES")
        bm.to_mesh(me)
        bm.free()
    core.nanite_clean(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    zero = [f for f in bm.faces if f.calc_area() < min_area]
    if zero:
        bmesh.ops.delete(bm, geom=zero, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    # the mesh tessellation can differ from the bmesh one on n-gons: triangulate any polygon whose mesh
    # triangulation still holds a needle, then clean again
    for _ in range(2):
        bad_p = mesh_needle_polys(me)
        if not len(bad_p):
            break
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.triangulate(bm, faces=[bm.faces[int(i)] for i in bad_p], quad_method="BEAUTY",
                              ngon_method="BEAUTY")
        bm.to_mesh(me)
        bm.free()
        me.update()
        core.nanite_clean(me)
    if sharp_deg is not None:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))


def Acc(name, sharp=38.0):
    """core.Acc with no ground cull and no z clamp (the strict hook clips at -5 cm instead)."""
    return core.Acc(name, sharp, cull=None)


def finalize(acc, coll, smooth_deg=38.0, recalc=True, clip_z=CLIP_Z):
    """build an accumulator into an object in coll with strict_clean; None when it is empty."""
    if acc.n == 0 or not acc.Fsz:
        core.log("  (empty)", acc.name)
        return None
    acc.sharp_angle = smooth_deg
    acc.hygiene = partial(strict_clean, clip_z=clip_z, recalc=recalc, sharp_deg=smooth_deg)
    ob = acc.build(coll)
    return ob


def pool_hygiene():
    """the strict hook for pooled variant meshes (local coordinates: no clip)."""
    return partial(strict_clean, clip_z=None, recalc=True, sharp_deg=40.0)
