"""Build script: "Stone-and-Timber Tower Windmill" (prefix MILL, collection MILL).

Source of truth for buildings/tower_windmill/tower_windmill.blend.
Run:  /opt/bpyenv/bin/python build_tower_windmill.py

Deterministic: every component draws from its own seeded numpy Generator (crc32 of
its name), so the output is reproducible bit for bit.

Conventions (art bible section 8 / spec section 1)
  metres, Z up, ground Z=0, tower axis at the origin, entrance faces -Y.
  azimuth az (deg) -> horizontal direction (sin az, -cos az); az=0 is -Y (front),
  az=+90 is +X (buttress side), az=-90 is -X (props side).
"""
import math
import os
import sys
import time
import zlib

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_BLEND = os.path.join(HERE, "tower_windmill.blend")
PI = math.pi
D2R = PI / 180.0
T0 = time.time()


def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def RNG(name):
    return np.random.default_rng(zlib.crc32(name.encode("utf8")))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# =============================================================================================
# Templates (topology shared by many instances, positions computed per instance with numpy)
# =============================================================================================
def tmpl_box(nx, ny, nz, drop_back=False):
    """Welded box grid. Lines per axis: [-h, -(h-r) ... (h-r), h]. Returns topology."""
    ids = {}
    idx = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if i in (0, nx - 1) or j in (0, ny - 1) or k in (0, nz - 1):
                    ids[(i, j, k)] = len(idx)
                    idx.append((i, j, k))
    n = [nx, ny, nz]
    quads, flat = [], []
    for ax in range(3):
        a1, a2 = [a for a in range(3) if a != ax]
        for side in (0, n[ax] - 1):
            if drop_back and ax == 1 and side == 0:
                continue
            outward = np.eye(3)[ax] * (1 if side > 0 else -1)
            nrm = np.cross(np.eye(3)[a1], np.eye(3)[a2])
            for p in range(n[a1] - 1):
                for q in range(n[a2] - 1):
                    cs = []
                    for dp, dq in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        c = [0, 0, 0]
                        c[ax] = side
                        c[a1] = p + dp
                        c[a2] = q + dq
                        cs.append(ids[tuple(c)])
                    if np.dot(nrm, outward) < 0:
                        cs = cs[::-1]
                    quads.append(cs)
                    flat.append(1 <= p and p + 1 <= n[a1] - 2 and 1 <= q and q + 1 <= n[a2] - 2)
    return dict(idx=np.array(idx), n=np.array(n), quads=np.array(quads, np.int64),
                tris=np.zeros((0, 3), np.int64), qflat=np.array(flat, bool),
                tflat=np.zeros(0, bool), nv=len(idx))


def tmpl_rings(n_rings, m, closed_path=False, cap0=True, cap1=True):
    """Generic ring topology (lathe or sweep). Ring i has m verts; optional cap centre verts.
    Quad winding assumes ring direction x profile direction gives outward (fixed later)."""
    quads = []
    last = n_rings if closed_path else n_rings - 1
    for i in range(last):
        i2 = (i + 1) % n_rings
        for j in range(m):
            j2 = (j + 1) % m
            quads.append([i * m + j, i2 * m + j, i2 * m + j2, i * m + j2])
    tris = []
    nv = n_rings * m
    if not closed_path:
        if cap0:
            c = nv
            nv += 1
            for j in range(m):
                tris.append([c, j, (j + 1) % m])
        if cap1:
            c = nv
            nv += 1
            b = (n_rings - 1) * m
            for j in range(m):
                tris.append([c, b + (j + 1) % m, b + j])
    return dict(quads=np.array(quads, np.int64).reshape(-1, 4), tris=np.array(tris, np.int64).reshape(-1, 3),
                qflat=np.zeros(len(quads), bool), tflat=np.ones(len(tris), bool), nv=nv,
                n_rings=n_rings, m=m, closed=closed_path, cap0=cap0 and not closed_path,
                cap1=cap1 and not closed_path)


def flip_tmpl(T):
    T = dict(T)
    T["quads"] = T["quads"][:, ::-1].copy()
    T["tris"] = T["tris"][:, ::-1].copy()
    return T


def signed_volume(P, T):
    v = 0.0
    for f in T["quads"]:
        a, b, c, d = P[f]
        v += np.dot(a, np.cross(b, c)) + np.dot(a, np.cross(c, d))
    for f in T["tris"]:
        a, b, c = P[f]
        v += np.dot(a, np.cross(b, c))
    return v / 6.0


def orient(T, P0):
    """Flip template winding if the sample instance P0 (nv,3) has negative volume."""
    c = P0.mean(0)
    return flip_tmpl(T) if signed_volume(P0 - c, T) < 0 else T


def box_lines(n, h, r):
    t = np.linspace(-1.0, 1.0, n - 2)
    inner = t[None, :] * (h - r)[:, None]
    return np.concatenate([-h[:, None], inner, h[:, None]], axis=1)


def rbox(T, h, r):
    """Rounded box positions for N instances. h,r (N,3) half sizes / edge radii."""
    h = np.asarray(h, float)
    r = np.minimum(np.asarray(r, float), h * 0.48)
    N = len(h)
    P = np.empty((N, T["nv"], 3))
    for a in range(3):
        L = box_lines(T["n"][a], h[:, a], r[:, a])
        P[:, :, a] = L[:, T["idx"][:, a]]
    lim = (h - r)[:, None, :]
    inner = np.clip(P, -lim, lim)
    d = (P - inner) / r[:, None, :]
    nr = np.linalg.norm(d, axis=2, keepdims=True)
    dn = np.where(nr > 1e-9, d / np.maximum(nr, 1e-9), 0.0)
    return inner + dn * r[:, None, :]


def ring_verts(centers, ex, ey, prof):
    """centers (N,n,3); ex,ey (N,n,3) frame axes; prof (N,n,m,2) or (m,2) -> (N, n*m, 3)."""
    prof = np.asarray(prof, float)
    if prof.ndim == 2:
        prof = np.broadcast_to(prof, centers.shape[:2] + prof.shape)
    P = centers[:, :, None, :] + prof[..., 0:1] * ex[:, :, None, :] + prof[..., 1:2] * ey[:, :, None, :]
    N = centers.shape[0]
    return P.reshape(N, -1, 3)


def add_caps(P, T):
    """Append cap centre verts (mean of first/last ring) to P (N, n*m, 3)."""
    m, n = T["m"], T["n_rings"]
    extra = []
    if T["cap0"]:
        extra.append(P[:, :m].mean(1, keepdims=True))
    if T["cap1"]:
        extra.append(P[:, (n - 1) * m:n * m].mean(1, keepdims=True))
    if extra:
        P = np.concatenate([P] + extra, axis=1)
    return P


def path_frames(path, up=(0, 0, 1)):
    """path (N,n,3) -> tangent, ex, ey (N,n,3) with ex = normalize(T x up), ey = ex x T."""
    T = np.gradient(path, axis=1)
    T /= np.linalg.norm(T, axis=2, keepdims=True) + 1e-12
    up = np.broadcast_to(np.asarray(up, float), path.shape)
    ex = np.cross(T, up)
    bad = np.linalg.norm(ex, axis=2) < 1e-6
    if bad.any():
        alt = np.cross(T, np.array([1.0, 0, 0]))
        ex = np.where(bad[..., None], alt, ex)
    ex /= np.linalg.norm(ex, axis=2, keepdims=True)
    ey = np.cross(ex, T)
    return T, ex, ey


def sweep(path, prof, up=(0, 0, 1), closed=False, caps=True, T_cache={}):
    """Sweep profile(s) along paths. path (N,n,3); prof (m,2) or (N,n,m,2). Returns (P, T)."""
    N, n = path.shape[:2]
    prof = np.asarray(prof, float)
    m = prof.shape[-2]
    key = (n, m, closed, caps)
    Tp, ex, ey = path_frames(path, up)
    P = ring_verts(path, ex, ey, prof)
    if key not in T_cache:
        T = tmpl_rings(n, m, closed_path=closed, cap0=caps, cap1=caps)
        P0 = add_caps(P[:1], T)[0]
        T_cache[key] = orient(T, P0) if not closed else T
    T = T_cache[key]
    if closed:
        # orientation for closed loops: outward = away from the loop centre line
        P0 = P[0]
        q = T["quads"][0]
        nrm = np.cross(P0[q[2]] - P0[q[0]], P0[q[3]] - P0[q[1]])
        ring_c = path[0, 0]
        if np.dot(nrm, P0[q].mean(0) - ring_c) < 0:
            T = flip_tmpl(T)
            T_cache[key] = T
    return add_caps(P, T), T


def circle_prof(rad, m, sx=1.0, sy=1.0, phase=0.0):
    a = np.linspace(0, 2 * PI, m, endpoint=False) + phase
    return np.stack([np.cos(a) * rad * sx, np.sin(a) * rad * sy], 1)


def rect_prof(w, h, c=0.0):
    """Rectangle profile with chamfered corners (8 pts), centred, CCW."""
    a, b = w / 2, h / 2
    c = min(c, a * 0.45, b * 0.45)
    if c <= 0:
        return np.array([[a, -b], [a, b], [-a, b], [-a, -b]])
    return np.array([[a, -b + c], [a, b - c], [a - c, b], [-a + c, b], [-a, b - c], [-a, -b + c],
                     [-a + c, -b], [a - c, -b]])


def lathe(prof_rz, m, caps=True, T_cache={}):
    """prof_rz (N,n,2) (radius, z). Returns local verts (N,nv,3) and template."""
    prof_rz = np.asarray(prof_rz, float)
    N, n = prof_rz.shape[:2]
    a = np.linspace(0, 2 * PI, m, endpoint=False)
    P = np.empty((N, n, m, 3))
    P[..., 0] = prof_rz[..., 0:1] * np.cos(a)
    P[..., 1] = prof_rz[..., 0:1] * np.sin(a)
    P[..., 2] = prof_rz[..., 1:2]
    P = P.reshape(N, n * m, 3)
    key = (n, m, caps)
    if key not in T_cache:
        T = tmpl_rings(n, m, closed_path=False, cap0=caps, cap1=caps)
        T_cache[key] = orient(T, add_caps(P[:1], T)[0])
    T = T_cache[key]
    return add_caps(P, T), T


# =============================================================================================
# Transform helpers
# =============================================================================================
def rotm(axis, ang):
    """Vectorised rotation matrices about unit axis (3,) or (N,3) by angle(s) (N,)."""
    ang = np.atleast_1d(np.asarray(ang, float))
    axis = np.asarray(axis, float)
    if axis.ndim == 1:
        axis = np.broadcast_to(axis, (len(ang), 3))
    axis = axis / np.linalg.norm(axis, axis=1, keepdims=True)
    x, y, z = axis[:, 0], axis[:, 1], axis[:, 2]
    c, s = np.cos(ang), np.sin(ang)
    C = 1 - c
    R = np.empty((len(ang), 3, 3))
    R[:, 0, 0] = c + x * x * C
    R[:, 0, 1] = x * y * C - z * s
    R[:, 0, 2] = x * z * C + y * s
    R[:, 1, 0] = y * x * C + z * s
    R[:, 1, 1] = c + y * y * C
    R[:, 1, 2] = y * z * C - x * s
    R[:, 2, 0] = z * x * C - y * s
    R[:, 2, 1] = z * y * C + x * s
    R[:, 2, 2] = c + z * z * C
    return R


def euler(ax, ay, az):
    return rotm([0, 0, 1], az) @ rotm([0, 1, 0], ay) @ rotm([1, 0, 0], ax)


def xform(P, R, t):
    """P (N,nv,3), R (N,3,3) or (3,3), t (N,3) or (3,)."""
    R = np.asarray(R, float)
    if R.ndim == 2:
        out = P @ R.T
    else:
        out = np.einsum("nij,nvj->nvi", R, P)
    return out + np.asarray(t, float).reshape(-1, 1, 3) if np.ndim(t) == 2 else out + np.asarray(t, float)


def frame_mats(xa, ya, za):
    """Columns = local axes in world. Each (N,3)."""
    return np.stack([xa, ya, za], axis=2)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def az_dir(az):
    az = np.asarray(az, float)
    return np.stack([np.sin(az), -np.cos(az), np.zeros_like(az)], -1)


# =============================================================================================
# Noise / deformation helpers
# =============================================================================================
def noise_field(u, rng, nterms=3, fmin=0.8, fmax=2.4):
    """Smooth per-instance noise. u (N,nv,3) normalised coords -> (N,nv) in ~[-1,1]."""
    N = u.shape[0]
    K = rng.normal(size=(N, nterms, 3))
    K /= np.linalg.norm(K, axis=2, keepdims=True)
    K *= rng.uniform(fmin, fmax, (N, nterms, 1)) * PI / 2
    ph = rng.uniform(0, 2 * PI, (N, nterms))
    a = rng.uniform(0.5, 1.0, (N, nterms))
    a /= a.sum(1, keepdims=True)
    return np.einsum("nt,nvt->nv", a, np.sin(np.einsum("nvc,ntc->nvt", u, K) + ph[:, None, :]))


def lowfreq(x, rng, amp, n=3, fmin=0.3, fmax=1.2):
    """1-D smooth noise for eave lines / sag (deterministic sum of sines)."""
    out = np.zeros_like(np.asarray(x, float))
    for _ in range(n):
        f = rng.uniform(fmin, fmax)
        out = out + np.sin(x * f * 2 * PI + rng.uniform(0, 2 * PI)) / n
    return out * amp


# =============================================================================================
# Part = one Blender mesh object being accumulated
# =============================================================================================
MAT_NAMES = ["M_stone", "M_stone_dressed", "M_mortar", "M_rubble", "M_timber", "M_timber_weathered",
             "M_roof_shingle", "M_roof_shake", "M_iron", "M_lead", "M_moss_clump"]


def box_uv(Pl, faces):
    F = Pl[:, faces]  # N,F,k,3
    k = faces.shape[1]
    if k == 4:
        nrm = np.cross(F[:, :, 2] - F[:, :, 0], F[:, :, 3] - F[:, :, 1])
    else:
        nrm = np.cross(F[:, :, 1] - F[:, :, 0], F[:, :, 2] - F[:, :, 0])
    ax = np.argmax(np.abs(nrm), axis=2)[..., None]
    u = np.where(ax == 0, F[..., 1], F[..., 0])
    v = np.where(ax == 2, F[..., 1], F[..., 2])
    return np.stack([u, v], -1)


class Part:
    registry = []

    def __init__(self, name, mats):
        self.name = name
        self.mats = list(mats)
        self.V = []
        self.Q, self.QM, self.QS, self.QU = [], [], [], []
        self.Tr, self.TM, self.TS, self.TU = [], [], [], []
        self.nv = 0
        self.rng_uv = RNG("uv_" + name)
        Part.registry.append(self)

    def add(self, Vw, T, Pl=None, mat=None, smooth="bevel", uv_rand=True):
        """Vw (N,nv,3) world positions; T template; Pl (N,nv,3) local positions for UVs.
        mat: slot name or index. smooth: 'all' | 'none' | 'bevel' (flat main faces, smooth bevels)."""
        Vw = np.asarray(Vw, float)
        if Vw.ndim == 2:
            Vw = Vw[None]
        N, nv = Vw.shape[:2]
        assert nv == T["nv"], (self.name, nv, T["nv"])
        Pl = Vw if Pl is None else (Pl[None] if Pl.ndim == 2 else Pl)
        mi = 0 if mat is None else (self.mats.index(mat) if isinstance(mat, str) else int(mat))
        base = self.nv + np.arange(N) * nv
        off = self.rng_uv.uniform(0, 4, (N, 1, 1, 2)) if uv_rand else 0.0
        for faces, flat, (L, LM, LS, LU) in ((T["quads"], T["qflat"], (self.Q, self.QM, self.QS, self.QU)),
                                             (T["tris"], T["tflat"], (self.Tr, self.TM, self.TS, self.TU))):
            if len(faces) == 0:
                continue
            L.append((faces[None] + base[:, None, None]).reshape(-1, faces.shape[1]))
            uv = box_uv(Pl, faces) + off
            LU.append(uv.reshape(-1, faces.shape[1], 2))
            LM.append(np.full(N * len(faces), mi, np.int32))
            if smooth == "all":
                s = np.ones(len(faces), bool)
            elif smooth == "none":
                s = np.zeros(len(faces), bool)
            else:
                s = ~flat
            LS.append(np.tile(s, N))
        self.V.append(Vw.reshape(-1, 3))
        self.nv += N * nv

    def tri_count(self):
        q = sum(len(a) for a in self.Q)
        t = sum(len(a) for a in self.Tr)
        return 2 * q + t

    def build(self, collection, mat_lookup, post=None):
        if self.nv == 0:
            return None
        V = np.concatenate(self.V)
        if post is not None:
            V = post(V)
        V[:, 2] = np.maximum(V[:, 2], 0.0)  # anything buried is cut flat at the ground
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        Tt = np.concatenate(self.Tr) if self.Tr else np.zeros((0, 3), np.int64)
        nq, nt = len(Q), len(Tt)
        loops = np.concatenate([Q.ravel(), Tt.ravel()]).astype(np.int32)
        ls = np.concatenate([np.arange(nq) * 4, nq * 4 + np.arange(nt) * 3]).astype(np.int32)
        me = bpy.data.meshes.new(self.name)
        me.vertices.add(len(V))
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        me.loops.add(len(loops))
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(nq + nt)
        me.polygons.foreach_set("loop_start", ls)
        me.update(calc_edges=True)
        uvs = []
        if self.QU:
            uvs.append(np.concatenate(self.QU).reshape(-1, 2))
        if self.TU:
            uvs.append(np.concatenate(self.TU).reshape(-1, 2))
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", np.concatenate(uvs).astype(np.float32).ravel())
        mats = np.concatenate(self.QM + self.TM).astype(np.int32)
        sm = np.concatenate(self.QS + self.TS).astype(bool)
        me.polygons.foreach_set("material_index", mats)
        me.polygons.foreach_set("use_smooth", sm)
        for mn in self.mats:
            me.materials.append(mat_lookup[mn])
        me.validate(clean_customdata=False)
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


# =============================================================================================
# Shared templates
# =============================================================================================
T_RUB = tmpl_box(9, 4, 7, drop_back=True)     # rubble stones (back face culled, buried in mortar)
T_RUBF = tmpl_box(7, 4, 5)                    # free-standing rubble / boulders
T_DRS = tmpl_box(6, 4, 5)                     # dressed blocks
T_BLK = tmpl_box(4, 4, 4)                     # small chamfered blocks / timbers
T_PLK = tmpl_box(9, 4, 4)                     # long members (bendable along x)
T_SHK = tmpl_box(6, 4, 4)                     # shakes / shingles (x = length)
T_BRD = tmpl_box(10, 4, 5)                    # long boards (x length, z width)


def chamfer_r(h, c):
    return np.broadcast_to(np.asarray(c, float), np.asarray(h).shape).copy()


def blocks_world(part, mat, centers, R, h, c=0.012, T=T_BLK, smooth="bevel", deform=None):
    """Place chamfered boxes: centers (N,3), R (N,3,3) local->world, h (N,3) half sizes."""
    h = np.atleast_2d(np.asarray(h, float))
    if len(h) == 1 and len(centers) > 1:
        h = np.repeat(h, len(centers), 0)
    P = rbox(T, h, chamfer_r(h, c))
    if deform is not None:
        P = deform(P, h)
    W = xform(P, R, centers)
    part.add(W, T, Pl=P, mat=mat, smooth=smooth)
    return W


def member(part, mat, a, b, w, d, up=(0, 0, 1), c=0.015, T=T_PLK, rng=None, bow=0.0, twist=0.0):
    """Timber member from points a to b (N,3); w = width (ex dir), d = depth (ey dir)."""
    a = np.atleast_2d(np.asarray(a, float))
    b = np.atleast_2d(np.asarray(b, float))
    N = len(a)
    xa = unit(b - a)
    upv = np.broadcast_to(np.asarray(up, float), xa.shape)
    ya = np.cross(upv, xa)
    bad = np.linalg.norm(ya, axis=1) < 1e-6
    ya[bad] = np.cross(np.array([1.0, 0, 0]), xa[bad])
    ya = unit(ya)
    za = np.cross(xa, ya)
    L = np.linalg.norm(b - a, axis=1)
    w = np.broadcast_to(np.asarray(w, float), (N,))
    d = np.broadcast_to(np.asarray(d, float), (N,))
    h = np.stack([L / 2, w / 2, d / 2], 1)
    P = rbox(T, h, chamfer_r(h, c))
    if rng is not None and (bow or twist):
        u = P[:, :, 0] / h[:, None, 0]
        bw = rng.uniform(-bow, bow, (N, 2))
        P[:, :, 1] += bw[:, None, 0] * (1 - u ** 2)
        P[:, :, 2] += bw[:, None, 1] * (1 - u ** 2)
        if twist:
            tw = rng.uniform(-twist, twist, N)[:, None] * u
            y, z = P[:, :, 1].copy(), P[:, :, 2].copy()
            P[:, :, 1] = y * np.cos(tw) - z * np.sin(tw)
            P[:, :, 2] = y * np.sin(tw) + z * np.cos(tw)
    R = frame_mats(xa, ya, za)
    W = xform(P, R, (a + b) / 2)
    part.add(W, T, Pl=P, mat=mat, smooth="bevel")
    return W


# =============================================================================================
# Stones
# =============================================================================================
STYLE = {
    # rounding (frac of min dim, min, max), outline noise, face noise (m), pillow range (m), taper, shear
    "rubble": dict(rr=(0.13, 0.009, 0.028), ry=0.014, nxz=0.16, ny=0.012, pil=(0.003, 0.016), tap=0.22,
                   shear=0.14, chip=0.0, T=T_RUB, cuts=2, hf=0.005),
    "footing": dict(rr=(0.14, 0.015, 0.04), ry=0.025, nxz=0.14, ny=0.012, pil=(0.008, 0.025), tap=0.16,
                    shear=0.1, chip=0.0, T=T_RUBF, cuts=2, hf=0.006),
    "boulder": dict(rr=(0.3, 0.015, 0.12), ry=0.3, nxz=0.16, ny=0.02, pil=(0.0, 0.02), tap=0.2,
                    shear=0.15, chip=0.0, T=T_RUBF, cuts=3, hf=0.006),
    "dressed": dict(rr=(0.1, 0.008, 0.016), ry=0.012, nxz=0.018, ny=0.002, pil=(0.0, 0.004), tap=0.02,
                    shear=0.015, chip=0.6, T=T_DRS),
    "ashlar": dict(rr=(0.14, 0.01, 0.022), ry=0.016, nxz=0.04, ny=0.004, pil=(0.002, 0.008), tap=0.05,
                   shear=0.03, chip=0.4, T=T_DRS),
    "flag": dict(rr=(0.2, 0.015, 0.04), ry=0.015, nxz=0.08, ny=0.004, pil=(0.0, 0.006), tap=0.12,
                 shear=0.08, chip=0.3, T=T_RUBF),
}


def stone_local(rng, L, H, D, style, rot_deg=(1.5, 1.5, 2.0)):
    """Irregular stone, local x = length, y = outward (front face at y=0), z = up. (N,nv,3)."""
    st = STYLE[style]
    T = st["T"]
    L, H, D = (np.asarray(v, float) for v in (L, H, D))
    N = len(L)
    h = np.stack([L / 2, D / 2, H / 2], 1)
    mn = np.minimum(L, H)
    rxz = np.clip(st["rr"][0] * mn, st["rr"][1], st["rr"][2])
    ry = np.minimum(st["ry"], 0.45 * D) if st["ry"] < 0.3 else st["ry"] * np.minimum(mn, D)
    r = np.stack([rxz, np.broadcast_to(ry, (N,)), rxz], 1)
    P = rbox(T, h, r)
    u = P / h[:, None, :]
    tap = rng.uniform(-st["tap"], st["tap"], N)
    sh = rng.uniform(-st["shear"], st["shear"], N)
    P[:, :, 0] *= 1 + tap[:, None] * u[:, :, 2]
    P[:, :, 0] += sh[:, None] * u[:, :, 2] * h[:, None, 2]
    P[:, :, 0] += st["nxz"] * h[:, None, 0] * 0.6 * noise_field(u, rng)
    P[:, :, 2] += st["nxz"] * h[:, None, 2] * noise_field(u, rng)
    front = np.clip(u[:, :, 1], 0, 1)
    P[:, :, 1] += st["ny"] * noise_field(u * 1.6, rng, fmin=1.5, fmax=3.5) * (0.4 + 0.6 * front)
    if st.get("hf", 0):
        P[:, :, 1] += st["hf"] * noise_field(u * 3.0, rng, nterms=4, fmin=2.0, fmax=5.0) * (0.3 + 0.7 * front)
    pil = rng.uniform(*st["pil"], N)
    P[:, :, 1] += pil[:, None] * front * np.clip(1 - u[:, :, 0] ** 2, 0, 1) * np.clip(1 - u[:, :, 2] ** 2, 0, 1)
    if st["chip"] > 0:
        has = rng.random(N) < st["chip"]
        cx = rng.choice([-1.0, 1.0], N)
        cz = rng.choice([-1.0, 1.0], N)
        dep = rng.uniform(0.008, 0.03, N) * has
        dist = np.sqrt(((u[:, :, 0] - cx[:, None]) / 0.55) ** 2 + ((u[:, :, 2] - cz[:, None]) / 0.7) ** 2 +
                       ((u[:, :, 1] - 1) / 0.9) ** 2)
        k = np.clip(1 - dist, 0, 1) ** 1.5 * dep[:, None]
        P[:, :, 0] -= k * cx[:, None] * 0.6
        P[:, :, 2] -= k * cz[:, None] * 0.6
        P[:, :, 1] -= k
    if st.get("cuts", 0):
        # split-stone facets: corner cuts in the face outline + a tilted plane shaving the face
        for _ in range(st["cuts"]):
            a = rng.uniform(0, 2 * PI, N)
            nrm = np.stack([np.cos(a) / h[:, 0], np.zeros(N), np.sin(a) / h[:, 2]], 1)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            proj = np.einsum("nvc,nc->nv", P, nrm)
            o = proj.max(1) * rng.uniform(0.62, 0.9, N)
            exc = np.clip(proj - o[:, None], 0, None)
            P -= exc[:, :, None] * nrm[:, None, :] * rng.uniform(0.75, 1.0, (N, 1, 1))
        nf = unit(np.stack([rng.normal(0, 0.35, N), np.ones(N), rng.normal(0, 0.35, N)], 1))
        proj = np.einsum("nvc,nc->nv", P, nf)
        o = proj.max(1) - rng.uniform(0.002, 0.014, N)
        exc = np.clip(proj - o[:, None], 0, None)
        P -= exc[:, :, None] * nf[:, None, :]
    P[:, :, 1] -= h[:, None, 1]
    rx, ry_, rz = rot_deg
    R = euler(rng.normal(0, rx * D2R, N), rng.normal(0, ry_ * D2R, N), rng.normal(0, rz * D2R, N))
    return xform(P, R, np.zeros(3)), T


# ----- wall radius (battered drum) -----
R_BASE0, R_BASE1, Z_BATTER = 2.60, 2.45, 4.05


def R_out(z):
    return R_BASE0 - (R_BASE0 - R_BASE1) * np.clip(z, 0, 4.6) / Z_BATTER


def cyl_place(P, th, zc, yoff, Rfun=R_out):
    """Map local stone coords onto the drum. x -> arc length, y -> outward, z -> up."""
    z = zc[:, None] + P[:, :, 2]
    R = Rfun(z)
    r = R + yoff[:, None] + P[:, :, 1]
    thv = th[:, None] + P[:, :, 0] / R
    return np.stack([r * np.sin(thv), -r * np.cos(thv), z], 2)


def open_place(P, th0, xc, zc, yoff, Rfun=R_out):
    """Opening-aligned mapping: parallel reveals (x lateral, straight), front follows the drum."""
    x = xc[:, None] + P[:, :, 0]
    z = zc[:, None] + P[:, :, 2]
    R = Rfun(z)
    d = np.sqrt(np.maximum(R ** 2 - x ** 2, 0.01)) + yoff[:, None] + P[:, :, 1]
    c, s = np.cos(th0)[:, None], np.sin(th0)[:, None]
    return np.stack([x * c + d * s, x * s - d * c, z], 2)


def coursing(rng, z0, z1, free_fn, hr=(0.10, 0.16), hbig=0.24, p_big=0.12, lr=(0.22, 0.62), joint=(0.014, 0.03),
             wob=0.018, p_tall=0.05, p_pin=0.12, fix_ends=True, Dr=(0.18, 0.30), lmin=0.12):
    """Generic coursed walling in (u, z). free_fn(zb, zt) -> list of (ua, ub) free spans.
    Returns dict of arrays uc, zc, L, H, D for each stone."""
    zs = [z0]
    while zs[-1] < z1 - 1e-6:
        zs.append(zs[-1] + (rng.uniform(*hr) if rng.random() > p_big else rng.uniform(hr[1], hbig)))
    zs = np.array(zs)
    if len(zs) > 2 and (zs[-1] - z1) > 0.5 * (zs[-1] - zs[-2]):
        zs = zs[:-1]
    zs = z0 + (zs - z0) * (z1 - z0) / (zs[-1] - z0)
    nb = len(zs)
    ch = np.diff(zs)
    wa = np.zeros(nb)
    for k in range(1, nb - 1):
        wa[k] = rng.uniform(0.3, 1.0) * min(wob, 0.28 * min(ch[k - 1], ch[k]))
    if not fix_ends:
        wa[0] = wa[-1] = 0
    wf = rng.uniform(0.25, 0.9, nb)
    wp = rng.uniform(0, 2 * PI, nb)

    def B(k, u):
        return zs[k] + wa[k] * np.sin(u * wf[k] + wp[k])

    out = {k: [] for k in ("uc", "zc", "L", "H", "D")}
    carry = []  # spans blocked by tall stones for the next course
    for k in range(nb - 1):
        spans = free_fn(zs[k], zs[k + 1])
        new_carry = []
        # subtract carried tall-stone spans
        sp2 = []
        for a, b in spans:
            cuts = sorted([c for c in carry if c[1] > a and c[0] < b])
            cur = a
            for ca, cb in cuts:
                if ca > cur:
                    sp2.append((cur, ca))
                cur = max(cur, cb)
            if b > cur:
                sp2.append((cur, b))
        for a, b in sp2:
            S = b - a
            if S < 0.06:
                continue
            Ls, Js = [], []
            tot = 0.0
            while tot < S:
                Lr = rng.uniform(*lr) if rng.random() > 0.15 else rng.uniform(lr[1], lr[1] * 1.45)
                j = rng.uniform(*joint)
                Ls.append(Lr)
                Js.append(j)
                tot += Lr + j
            if len(Ls) > 1 and tot - S > 0.5 * Ls[-1]:
                tot -= Ls[-1] + Js[-1]
                Ls.pop()
                Js.pop()
            f = S / tot
            pos = a
            for Lr, j in zip(Ls, Js):
                Lr *= f
                j *= f
                uc = pos + j / 2 + Lr / 2
                pos += Lr + j
                tall = (rng.random() < p_tall) and (k + 2 < nb) and Lr < 0.7
                kt = k + 2 if tall else k + 1
                zb, zt = B(k, uc), B(kt, uc)
                jv = rng.uniform(*joint)
                Hs = (zt - zb) - jv - rng.uniform(0, 0.012)
                zc = (zb + zt) / 2 + rng.uniform(-0.004, 0.004)
                Ds = rng.uniform(*Dr)
                if tall:
                    new_carry.append((uc - Lr / 2 - j / 2, uc + Lr / 2 + j / 2))
                if (not tall) and rng.random() < p_pin and Hs > 0.09 and Lr > 0.25:
                    # main stone + small pinning stones in a strip above or below
                    frac = rng.uniform(0.62, 0.75)
                    top = rng.random() < 0.5
                    Hm = Hs * frac
                    Hp = Hs - Hm - jv * 0.6
                    zm = zc - Hs / 2 + Hm / 2 if not top else zc + Hs / 2 - Hm / 2
                    zp = zc + Hs / 2 - Hp / 2 if not top else zc - Hs / 2 + Hp / 2
                    for kk, v in zip(("uc", "zc", "L", "H", "D"), (uc, zm, Lr, Hm, Ds)):
                        out[kk].append(v)
                    npin = 1 if Lr < 0.4 else 2
                    seg = Lr / npin
                    for q in range(npin):
                        lp = seg * rng.uniform(0.55, 0.85)
                        up = uc - Lr / 2 + seg * (q + 0.5) + rng.uniform(-0.03, 0.03)
                        for kk, v in zip(("uc", "zc", "L", "H", "D"), (up, zp, lp, Hp, Ds * 0.7)):
                            out[kk].append(v)
                    continue
                for kk, v in zip(("uc", "zc", "L", "H", "D"), (uc, zc, Lr, Hs, Ds)):
                    out[kk].append(v)
        carry = new_carry
    return {k: np.array(v) for k, v in out.items()}


def free_on_circle(Rmid, blocks):
    """blocks: list of (u_centre, half_width) in arc length at Rmid -> free spans (cyclic)."""
    C = 2 * PI * Rmid
    if not blocks:
        return None
    iv = sorted(((uc - hw) % C, hw * 2) for uc, hw in blocks)
    # merge on a circle by unrolling from the first block start
    start = iv[0][0]
    segs = sorted(((a - start) % C, (a - start) % C + w) for a, w in iv)
    merged = []
    for a, b in segs:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    free = []
    for i, (a, b) in enumerate(merged):
        nxt = merged[i + 1][0] if i + 1 < len(merged) else C
        if nxt > b:
            free.append((b + start, nxt + start))
    return free


def add_grid(part, mat, P, keep=None, wrap=False, flip=False, smooth="all"):
    """P (nu, nv, 3) grid of points -> quads for kept cells (nu-1 or nu if wrap, nv-1)."""
    nu, nv = P.shape[:2]
    cu = nu if wrap else nu - 1
    if keep is None:
        keep = np.ones((cu, nv - 1), bool)
    I, J = np.nonzero(keep)
    if len(I) == 0:
        return
    i2 = (I + 1) % nu
    q = np.stack([I * nv + J, i2 * nv + J, i2 * nv + J + 1, I * nv + J + 1], 1)
    if flip:
        q = q[:, ::-1]
    used = np.unique(q)
    remap = -np.ones(nu * nv, np.int64)
    remap[used] = np.arange(len(used))
    Vf = P.reshape(-1, 3)[used]
    T = dict(quads=remap[q], tris=np.zeros((0, 3), np.int64), qflat=np.zeros(len(q), bool),
             tflat=np.zeros(0, bool), nv=len(used))
    part.add(Vf[None], T, mat=mat, smooth=smooth)


def profile_block(prof, L, nseg, chamfer=0.012):
    """Straight block of length L along x with a closed (y,z) profile; ends chamfered by shrinking."""
    prof = np.asarray(prof, float)
    cy, cz = prof[:, 0].mean(), prof[:, 1].mean()
    xs = np.concatenate([[0.0, chamfer], np.linspace(chamfer, L - chamfer, nseg + 1)[1:-1], [L - chamfer, L]]) - L / 2
    n = len(xs)
    rings = np.repeat(prof[None], n, 0).copy()
    for i in (0, n - 1):
        sy = 1 - 2 * chamfer / max(np.ptp(prof[:, 0]), 1e-3)
        sz = 1 - 2 * chamfer / max(np.ptp(prof[:, 1]), 1e-3)
        rings[i, :, 0] = cy + (rings[i, :, 0] - cy) * sy
        rings[i, :, 1] = cz + (rings[i, :, 1] - cz) * sz
    P = np.empty((n, len(prof), 3))
    P[:, :, 0] = xs[:, None]
    P[:, :, 1] = rings[:, :, 0]
    P[:, :, 2] = rings[:, :, 1]
    return P.reshape(-1, 3), n


_TPB = {}


def profile_course(part, mat, rng, z0, prof, seg=(0.6, 0.95), skip=(), Rfun=R_out, joint=0.01, jit=0.004):
    """Ring course of dressed profile blocks around the drum (cyl mapped). skip: list of (th_c, half_arc_m)."""
    Rm = float(Rfun(z0))
    C = 2 * PI * Rm
    if skip:
        spans = free_on_circle(Rm, [(t * Rm, hw) for t, hw in skip])
    else:
        u0 = rng.uniform(0, C)
        spans = [(u0, u0 + C)]
    for a, b in spans:
        S = b - a
        n = max(1, int(round(S / rng.uniform(*seg))))
        cuts = np.sort(np.concatenate([[0, S], rng.uniform(0.15, 0.85, n - 1) * 0 + (np.arange(1, n) + rng.uniform(-0.25, 0.25, n - 1)) * S / n]))
        for i in range(n):
            L = cuts[i + 1] - cuts[i] - joint
            uc = a + (cuts[i] + cuts[i + 1]) / 2
            nseg = max(3, int(L / 0.1))
            P, nr = profile_block(prof, L, nseg)
            key = (nr, len(prof))
            if key not in _TPB:
                T = tmpl_rings(nr, len(prof), cap0=True, cap1=True)
                _TPB[key] = orient(T, add_caps(P[None], T)[0])
            T = _TPB[key]
            P = add_caps(P[None], T)
            # tiny irregularity: settle / roll / out-of-line
            P[:, :, 2] += rng.uniform(-jit, jit) + P[:, :, 0] * rng.uniform(-0.006, 0.006)
            P[:, :, 1] += rng.uniform(-jit, jit)
            W = cyl_place(P, np.array([uc / Rm]), np.array([z0]), np.array([0.0]), Rfun)
            part.add(W, T, Pl=P, mat=mat, smooth="bevel")


# =============================================================================================
# A. STONE BASE
# =============================================================================================
R_DOOR = float(R_out(1.0))
DOOR_CW = 0.525          # clear half width (1.05 m)
Z_TH = 0.14              # threshold top
ZS_DOOR = Z_TH + 1.65    # springing
DOOR_JAMBS = {-1: [0.42, 0.30, 0.44, 0.32], 1: [0.31, 0.43, 0.30, 0.42]}
DOOR_JZ = [0.0, 0.44, 0.86, 1.30, ZS_DOOR]
DOOR_RING = (0.18, 0.215)
WIN_AZ = [70 * D2R, -130 * D2R]
WIN = dict(cw=0.08, z0=1.30, z1=1.85, jz=[1.30, 1.56, 1.85], fw=[(0.17, 0.21), (0.21, 0.17)])
ARCH_AZ = [(18 + 36 * k) * D2R for k in range(10) if k != 2]
ARCH = dict(cw=0.36, z0=2.97, zs=3.42, ring=(0.17, 0.19), fw=0.17, jz=[2.97, 3.20, 3.42])
BUTT_AZ = 90 * D2R
Z_BAND0, Z_BAL0, Z_BAL1, Z_BAND1 = 2.55, 2.65, 2.87, 2.97
Z_CORN0 = 4.05


def butt_halfwidth(z):
    return 0.80 - 0.10 * np.clip(z, 0, 3.6) / 3.6


def hw_door(z):
    z = np.asarray(z, float)
    out = np.zeros_like(z)
    for s in (-1, 1):
        pass
    for i in range(4):
        m = (z >= DOOR_JZ[i] - 0.01) & (z < DOOR_JZ[i + 1])
        out = np.where(m, DOOR_CW + max(DOOR_JAMBS[-1][i], DOOR_JAMBS[1][i]) + 0.012, out)
    ro = DOOR_CW + DOOR_RING[1] + 0.012
    dz = z - ZS_DOOR
    arch = np.sqrt(np.clip(ro ** 2 - dz ** 2, 0, None))
    out = np.where(z >= ZS_DOOR, np.where(dz < ro, arch, 0.0), out)
    return out


def hw_window(z):
    z = np.asarray(z, float)
    out = np.zeros_like(z)
    out = np.where((z >= 1.17) & (z < WIN["z0"]), 0.31, out)
    out = np.where((z >= WIN["z0"]) & (z < WIN["z1"]), WIN["cw"] + 0.22, out)
    out = np.where((z >= WIN["z1"]) & (z < 2.04), 0.37, out)
    return out


def hw_arch(z):
    z = np.asarray(z, float)
    out = np.where((z >= ARCH["z0"] - 0.01) & (z < ARCH["zs"]), ARCH["cw"] + ARCH["fw"] + 0.012, 0.0)
    ro = ARCH["cw"] + ARCH["ring"][1] + 0.012
    dz = z - ARCH["zs"]
    return np.where(z >= ARCH["zs"], np.sqrt(np.clip(ro ** 2 - dz ** 2, 0, None)), out)


def hw_butt(z):
    z = np.asarray(z, float)
    return np.where(z < 3.86, butt_halfwidth(z) + 0.03, 0.0)


OPENINGS = [(0.0, hw_door)] + [(a, hw_window) for a in WIN_AZ] + [(a, hw_arch) for a in ARCH_AZ] + \
           [(BUTT_AZ, hw_butt)]


def free_fn_drum(rng, extra_rad=0.0):
    def f(zb, zt):
        zz = np.linspace(zb, zt, 5)
        Rm = float(R_out((zb + zt) / 2)) + extra_rad
        blocks = []
        for th, fn in OPENINGS:
            w = fn(zz)
            if w.max() <= 0:
                continue
            hw = 0.5 * (w.max() + w.mean())
            blocks.append((th * Rm, hw))
        if not blocks:
            u0 = rng.uniform(0, 2 * PI * Rm)
            return [(u0, u0 + 2 * PI * Rm)]
        return free_on_circle(Rm, blocks)
    return f


def emit_drum_stones(part, mat, rng, S, style, yoff_base, bulge=True):
    if len(S["uc"]) == 0:
        return 0
    zc = S["zc"]
    th = S["uc"] / R_out(zc)
    P, T = stone_local(rng, S["L"], S["H"], S["D"], style)
    yo = yoff_base + rng.normal(0, 0.004, len(zc))
    if bulge:  # stones bulge in and out of the wall plane (low-frequency)
        yo += 0.008 * np.sin(th * 3 + 1.3) * np.sin(zc * 2.1 + 0.4) + 0.006 * np.sin(th * 7 + zc * 3)
    W = cyl_place(P, th, zc, yo)
    part.add(W, T, Pl=P, mat=mat, smooth="all")
    return len(zc)


def arch_set(P_dr, rng, th0, ri, zs, nv, ring, Dv, jambs, Rfun, yfront=0.03, vert=False):
    """Dressed voussoir ring + jamb blocks for an arch at azimuth th0.
    jambs: dict side -> list of (z0, z1, face_width)."""
    # voussoirs
    w = rng.uniform(0.85, 1.15, nv)
    w[nv // 2] *= 1.18
    edges = np.concatenate([[0], np.cumsum(w)]) / w.sum() * PI
    for i in range(nv):
        a0, a1 = edges[i], edges[i + 1]
        ac = (a0 + a1) / 2
        dep = ring[0] + (ring[1] - ring[0]) * math.sin(ac) + rng.uniform(-0.012, 0.012)
        rm = ri + dep / 2
        L = (a1 - a0) * rm - 0.012
        P, T = stone_local(rng, [L], [dep], [Dv], "dressed", rot_deg=(0.2, 0.2, 0.2))
        rho = ri + dep / 2 + P[:, :, 2]
        al = ac - P[:, :, 0] / rm
        E = np.stack([rho * np.cos(al), P[:, :, 1], zs + rho * np.sin(al)], 2)
        W = open_place(E, np.array([th0]), np.array([0.0]), np.array([0.0]), np.array([yfront]), Rfun)
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # jambs
    for s, blocks in jambs.items():
        for (z0, z1, fw) in blocks:
            H = z1 - z0 - 0.012
            P, T = stone_local(rng, [fw], [H], [Dv], "dressed", rot_deg=(0.2, 0.2, 0.3))
            W = open_place(P, np.array([th0]), np.array([s * (ri + fw / 2)]), np.array([(z0 + z1) / 2]),
                           np.array([yfront]), Rfun)
            P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")


def build_base(parts):
    P_st, P_mo, P_dr = parts["stones"], parts["mortar"], parts["dressed"]
    rng = RNG("base_rubble")
    n = 0
    # 1. footing course (big stones projecting ~7 cm, bottoms cut at the ground)
    S = coursing(rng, -0.04, 0.40, free_fn_drum(rng), hr=(0.18, 0.24), hbig=0.26, p_big=0.0, lr=(0.42, 0.85),
                 p_tall=0.0, p_pin=0.06, Dr=(0.3, 0.4), wob=0.015)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "footing", 0.065)
    # 2. plain rubble 0.40 - 2.55
    S = coursing(rng, 0.40, Z_BAND0, free_fn_drum(rng), hr=(0.095, 0.15), hbig=0.22, p_big=0.1, lr=(0.2, 0.6),
                 p_tall=0.05, p_pin=0.14)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0)
    # 4. arcade zone: ashlar-ish piers to springing, rubble spandrels above
    S = coursing(rng, Z_BAND1, ARCH["zs"], free_fn_drum(rng), hr=(0.2, 0.25), hbig=0.25, p_big=0.0,
                 lr=(0.24, 0.45), p_tall=0.0, p_pin=0.0, wob=0.0, joint=(0.01, 0.016))
    n += emit_drum_stones(P_st, "M_stone", rng, S, "ashlar", 0.012, bulge=False)
    S = coursing(rng, ARCH["zs"], Z_CORN0, free_fn_drum(rng), hr=(0.09, 0.14), hbig=0.18, p_big=0.1,
                 lr=(0.18, 0.5), p_tall=0.03, p_pin=0.1, wob=0.012)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0)
    log("drum rubble stones", n)

    # ---- dressed: door ----
    rd = RNG("door_surround")
    jam = {s: [(DOOR_JZ[i], DOOR_JZ[i + 1], DOOR_JAMBS[s][i]) for i in range(4)] for s in (-1, 1)}
    arch_set(P_dr, rd, 0.0, DOOR_CW, ZS_DOOR, 11, DOOR_RING, 0.34, jam, lambda z: np.full_like(z, R_DOOR),
             yfront=0.03)
    # threshold stone (worn dip in the middle)
    P, T = stone_local(rd, [1.32], [0.17], [0.46], "dressed", rot_deg=(0.2, 0.2, 0.2))
    u = P[:, :, 0] / 0.66
    top = P[:, :, 2] > 0.04
    P[:, :, 2] -= top * 0.012 * np.exp(-(u * 2.2) ** 2) * np.exp(-((P[:, :, 1] + 0.2) / 0.2) ** 2)
    W = open_place(P, np.array([0.0]), np.array([0.0]), np.array([Z_TH - 0.085]), np.array([0.07]),
                   lambda z: np.full_like(z, R_DOOR))
    P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="all")
    # ---- dressed: slit windows ----
    rw = RNG("windows")
    for k, th in enumerate(WIN_AZ):
        fw = WIN["fw"][k]
        jam = {-1: [(WIN["jz"][0], WIN["jz"][1], fw[0]), (WIN["jz"][1], WIN["jz"][2], fw[1])],
               1: [(WIN["jz"][0], WIN["jz"][1], fw[1]), (WIN["jz"][1], WIN["jz"][2], fw[0])]}
        for s, bl in jam.items():
            for (z0, z1, w) in bl:
                P, T = stone_local(rw, [w], [z1 - z0 - 0.012], [0.32], "dressed", rot_deg=(0.2, 0.2, 0.3))
                W = open_place(P, np.array([th]), np.array([s * (WIN["cw"] + w / 2)]), np.array([(z0 + z1) / 2]),
                               np.array([0.02]))
                P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        # sill with drip (projects 6 cm) and lintel
        P, T = stone_local(rw, [0.62], [0.12], [0.40], "dressed", rot_deg=(0.2, 0.3, 0.2))
        P[:, :, 2] += np.where(P[:, :, 2] > 0, -0.02 * np.clip(P[:, :, 1] + 0.1, 0, 1) * 6, 0)
        W = open_place(P, np.array([th]), np.array([0.0]), np.array([1.235]), np.array([0.06]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        P, T = stone_local(rw, [0.74], [0.18], [0.34], "dressed", rot_deg=(0.2, 0.2, 0.4))
        W = open_place(P, np.array([th]), np.array([0.0]), np.array([1.945]), np.array([0.02]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
        # splayed embrasure behind the slit (closed, dark): sides, sill, head and back (mortar)
        cth, sth = math.cos(th), math.sin(th)
        Rz = float(R_out(1.575))

        def wpt(x, d, z):
            return [x * cth + (Rz + d) * sth, x * sth - (Rz + d) * cth, z]

        z0, z1 = WIN["z0"], WIN["z1"]
        cw = WIN["cw"]
        for s in (-1, 1):
            G = np.array([[wpt(s * cw, -0.30, z0), wpt(s * cw, -0.30, z1)],
                          [wpt(s * 0.22, -0.62, z0), wpt(s * 0.22, -0.62, z1)]])
            add_grid(P_mo, "M_mortar", G, flip=(s < 0))
        for zz, fl in ((z0, True), (z1 + 0.06, False)):
            G = np.array([[wpt(-cw, -0.30, zz), wpt(-0.22, -0.62, zz)],
                          [wpt(cw, -0.30, zz), wpt(0.22, -0.62, zz)]])
            add_grid(P_mo, "M_mortar", G, flip=fl)
        G = np.array([[wpt(-0.22, -0.62, z0), wpt(-0.22, -0.62, z1 + 0.06)],
                      [wpt(0.22, -0.62, z0), wpt(0.22, -0.62, z1 + 0.06)]])
        add_grid(P_mo, "M_mortar", G, flip=False)

    # ---- dressed: blind arcade ----
    ra = RNG("arcade")
    for th in ARCH_AZ:
        jam = {s: [(ARCH["jz"][0], ARCH["jz"][1], ARCH["fw"] + ra.uniform(-0.01, 0.01)),
                   (ARCH["jz"][1], ARCH["jz"][2], ARCH["fw"] + ra.uniform(-0.01, 0.01))] for s in (-1, 1)}
        arch_set(P_dr, ra, th, ARCH["cw"], ARCH["zs"], int(ra.choice([9, 11])), ARCH["ring"], 0.46, jam, R_out,
                 yfront=0.018)
        # rubble back of the recess (0.25 deep)
        cw = ARCH["cw"]

        def ff(zb, zt, cw=cw):
            zm = (zb + zt) / 2
            if zm < ARCH["zs"]:
                return [(-cw, cw)]
            dz = zt - ARCH["zs"]
            if dz >= cw - 0.05:
                return []
            w = math.sqrt(cw ** 2 - min(dz, cw) ** 2) + 0.03
            return [(-w, w)]

        S = coursing(ra, ARCH["z0"], ARCH["zs"] + cw, ff, hr=(0.09, 0.14), hbig=0.16, p_big=0.1, lr=(0.16, 0.4),
                     p_tall=0.0, p_pin=0.1, wob=0.01, Dr=(0.15, 0.22))
        if len(S["uc"]):
            P, T = stone_local(ra, S["L"], S["H"], S["D"], "rubble")
            W = open_place(P, np.full(len(S["uc"]), th), S["uc"], S["zc"], np.full(len(S["uc"]), -0.25))
            P_st.add(W, T, Pl=P, mat="M_stone", smooth="all")
        # mortar back panel of the recess
        xs = np.linspace(-cw - 0.06, cw + 0.06, 12)
        zz = np.linspace(ARCH["z0"] - 0.02, ARCH["zs"] + cw + 0.05, 14)
        X, Z = np.meshgrid(xs, zz, indexing="ij")
        Rz = R_out(Z)
        d = np.sqrt(Rz ** 2 - X ** 2) - 0.272
        G = np.stack([X * math.cos(th) + d * math.sin(th), X * math.sin(th) - d * math.cos(th), Z], 2)
        add_grid(P_mo, "M_mortar", G, flip=False)

    # ---- band: strings, back panel, balusters ----
    rb = RNG("band")
    skip_b = [(BUTT_AZ, butt_halfwidth(2.7) + 0.02)]
    prof_lo = [(-0.30, 0), (0.10, 0), (0.12, 0.018), (0.12, 0.08), (0.105, 0.097), (-0.30, 0.10)]
    prof_up = [(-0.30, 0), (0.08, 0), (0.10, 0.018), (0.10, 0.082), (0.088, 0.098), (-0.30, 0.10)]
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAND0, prof_lo, skip=skip_b)
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAL1, prof_up, skip=skip_b)
    Rm = float(R_out(Z_BAL0))
    spans = free_on_circle(Rm, [(BUTT_AZ * Rm, butt_halfwidth(2.7) + 0.02)])
    S = coursing(rb, Z_BAL0, Z_BAL1, lambda zb, zt: spans, hr=(0.22, 0.22), p_big=0, lr=(0.3, 0.55), p_tall=0,
                 p_pin=0, wob=0, joint=(0.008, 0.014), Dr=(0.2, 0.25))
    th = S["uc"] / R_out(S["zc"])
    P, T = stone_local(rb, S["L"], S["H"], S["D"], "ashlar")
    P_dr.add(cyl_place(P, th, S["zc"], np.full(len(th), -0.03)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # balusters: turned 12-sided lathe + square plinth and abacus
    Rb = float(R_out(2.76))
    a0, a1 = spans[0]
    nbal = int((a1 - a0) / 0.22)
    us = a0 + (np.arange(nbal) + 0.5) * (a1 - a0) / nbal + rb.uniform(-0.012, 0.012, nbal)
    thb = us / Rb
    prof = np.array([(0.038, 0.0), (0.044, 0.012), (0.050, 0.04), (0.052, 0.07), (0.047, 0.095), (0.034, 0.12),
                     (0.027, 0.14), (0.029, 0.152), (0.036, 0.16), (0.04, 0.17)])
    prof = np.repeat(prof[None], nbal, 0)
    prof[:, :, 0] *= rb.uniform(0.93, 1.07, (nbal, 1))
    prof[:, :, 0] += rb.normal(0, 0.0015, (nbal, prof.shape[1]))
    P, T = lathe(prof, 12)
    P[:, :, 2] += Z_BAL0 + 0.025
    lean = euler(rb.normal(0, 1.2 * D2R, nbal), rb.normal(0, 1.2 * D2R, nbal), rb.uniform(0, PI, nbal))
    ctr = np.stack([(Rb + 0.055) * np.sin(thb), -(Rb + 0.055) * np.cos(thb), np.zeros(nbal)], 1)
    Pc = P - np.array([0, 0, Z_BAL0 + 0.11])
    W = xform(Pc, lean, ctr + np.array([0, 0, Z_BAL0 + 0.11]))
    P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="all")
    for zc in (Z_BAL0 + 0.0125, Z_BAL1 - 0.0125):
        h = np.repeat([[0.056, 0.056, 0.0125]], nbal, 0) * rb.uniform(0.96, 1.04, (nbal, 3))
        Rz = rotm([0, 0, 1], thb + rb.normal(0, 0.03, nbal))
        c = ctr + np.array([0, 0, zc])
        blocks_world(P_dr, "M_stone_dressed", c, Rz, h, c=0.006, T=T_BLK)

    # ---- cornice ----
    rc = RNG("cornice")
    profile_course(P_dr, "M_stone_dressed", rc, Z_CORN0, [(-0.3, 0), (0.03, 0), (0.04, 0.01), (0.04, 0.06),
                                                        (0.03, 0.07), (-0.3, 0.07)], seg=(0.5, 0.8))
    # frieze course between corbels
    S = coursing(rc, 4.12, 4.27, lambda zb, zt: [(0.3, 0.3 + 2 * PI * float(R_out(4.2)))], hr=(0.15, 0.15),
                 p_big=0, lr=(0.25, 0.5), p_tall=0, p_pin=0, wob=0, joint=(0.008, 0.012), Dr=(0.2, 0.25))
    th = S["uc"] / R_out(S["zc"])
    P, T = stone_local(rc, S["L"], S["H"], S["D"], "ashlar")
    P_dr.add(cyl_place(P, th, S["zc"], np.full(len(th), -0.005)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # corbels / dentils
    ncb = 40
    thc = (np.arange(ncb) + 0.5) * 2 * PI / ncb + rc.uniform(-0.012, 0.012, ncb)
    P, T = stone_local(rc, rc.uniform(0.115, 0.13, ncb), rc.uniform(0.14, 0.15, ncb), np.full(ncb, 0.40),
                       "dressed", rot_deg=(0.3, 0.3, 0.6))
    proj = P[:, :, 1] > -0.18
    hz = 0.075
    f = 0.45 + 0.55 * np.clip((P[:, :, 2] / hz + 1) / 2, 0, 1)
    P[:, :, 1] = np.where(proj, -0.18 + (P[:, :, 1] + 0.18) * f, P[:, :, 1])
    P_dr.add(cyl_place(P, thc, np.full(ncb, 4.195), np.full(ncb, 0.18)), T, Pl=P, mat="M_stone_dressed",
             smooth="bevel")
    profile_course(P_dr, "M_stone_dressed", rc, 4.27, [(-0.3, 0), (0.19, 0), (0.20, 0.01), (0.20, 0.042),
                                                     (0.19, 0.05), (-0.3, 0.05)], seg=(0.6, 0.9))
    cap = [(-0.42, 0), (0.19, 0), (0.235, 0.035), (0.24, 0.042), (0.243, 0.056), (0.252, 0.056), (0.256, 0.046),
           (0.29, 0.058), (0.305, 0.072), (0.305, 0.145), (0.29, 0.16), (0.0, 0.18), (-0.42, 0.18)]
    profile_course(P_dr, "M_stone_dressed", rc, 4.32, cap, seg=(0.75, 1.05), joint=0.008)

    # ---- mortar core (outer skin, 2.4 cm behind stone faces) ----
    nth = 288
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.concatenate([np.linspace(0.0, 2.55, 27), np.linspace(2.65, 4.15, 16)])
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    rm = RNG("mortar")
    r = R_out(Z) - 0.024 + 0.004 * np.sin(TH * 13 + Z * 7) * np.sin(TH * 5 - Z * 3)
    G = np.stack([r * np.sin(TH), -r * np.cos(TH), Z], 2)
    keep = np.ones((nth, len(zs) - 1), bool)
    # remove cells touching the clear part of door / windows / arcade recesses
    for i in range(nth):
        for j in range(len(zs) - 1):
            th_s = np.array([ths[i], ths[i], ths[(i + 1) % nth] if i + 1 < nth else 2 * PI, ths[i] + PI / nth])
            th_s = np.array([ths[i], ths[i] + 2 * PI / nth, ths[i] + PI / nth])
            z_s = np.array([zs[j], zs[j + 1], (zs[j] + zs[j + 1]) / 2])
            for tq in th_s:
                for zq in z_s:
                    if inside_clear(tq, zq):
                        keep[i, j] = False
    add_grid(P_mo, "M_mortar", G, keep=keep, wrap=True, flip=False)
    # top of the drum under the cornice / curb (hidden mostly)
    return n


def inside_clear(th, z):
    """Is point (azimuth th, height z) on the drum face inside a clear opening?"""
    R = float(R_out(z))

    def lat(th0):
        d = (th - th0 + PI) % (2 * PI) - PI
        return R * math.sin(d), abs(d) < PI / 2

    x, ok = lat(0.0)
    if ok and abs(x) < DOOR_CW and Z_TH - 0.2 <= z <= ZS_DOOR + math.sqrt(max(DOOR_CW ** 2 - x ** 2, 0)):
        return True
    for a in WIN_AZ:
        x, ok = lat(a)
        if ok and abs(x) < WIN["cw"] and WIN["z0"] <= z <= WIN["z1"]:
            return True
    for a in ARCH_AZ:
        x, ok = lat(a)
        if ok and abs(x) < ARCH["cw"] and ARCH["z0"] <= z <= ARCH["zs"] + math.sqrt(max(ARCH["cw"] ** 2 - x ** 2, 0)):
            return True
    return False


def build_door_and_interior(parts):
    P_mo, P_int, P_leaf, P_iron = parts["mortar"], parts["interior"], parts["door"], parts["door_iron"]
    rng = RNG("door_leaf")
    Rd = R_DOOR
    # ---- passage behind the rebate (plastered rubble), rere-arch vault ----
    XW = 0.675
    d0, d1 = -0.31, -0.97
    ZV = 1.95

    def to_world(x, d, z):  # door frame: x lateral (+X), d = depth offset from face (negative = inward)
        return np.stack([x, -(Rd + d), z], -1)

    nz = 12
    for s in (-1, 1):
        dd = np.linspace(d0, d1, 6)
        zz = np.linspace(Z_TH - 0.02, ZV, nz)
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
    zz = np.linspace(ZS_DOOR - 0.05, ZV + XW * 0.9 + 0.02, 10)
    X, Z = np.meshgrid(xs, zz, indexing="ij")
    keep = np.ones((len(xs) - 1, len(zz) - 1), bool)
    for i in range(len(xs) - 1):
        for j in range(len(zz) - 1):
            xc, zc = (xs[i] + xs[i + 1]) / 2, (zz[j] + zz[j + 1]) / 2
            inside_door = (zc - ZS_DOOR) ** 2 + xc ** 2 < (DOOR_CW + 0.01) ** 2 or zc < ZS_DOOR
            keep[i, j] = (not inside_door)
    add_grid(P_mo, "M_mortar", to_world(X, np.full_like(X, d0 - 0.004), Z), keep=keep, flip=True)

    # ---- interior: inner wall face, flagstone floor, ceiling beams, boards, ladder ----
    nth = 96
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.linspace(Z_TH - 0.02, 3.34, 15)
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    r = R_out(Z) - 0.80 + 0.012 * np.sin(TH * 11 + Z * 4) * np.sin(TH * 4 - Z * 6)
    G = np.stack([r * np.sin(TH), -r * np.cos(TH), Z], 2)
    keep = np.ones((nth, len(zs) - 1), bool)
    for i in range(nth):
        for j in range(len(zs) - 1):
            for tq in (ths[i], ths[i] + 2 * PI / nth):
                d = (tq + PI) % (2 * PI) - PI
                x = 1.8 * math.sin(d)
                zt = zs[j]
                if abs(d) < PI / 2 and abs(x) < XW + 0.02 and zt < ZV + 0.9 * math.sqrt(max(XW ** 2 - x ** 2, 0)):
                    keep[i, j] = False
    add_grid(P_int, "M_mortar", G, keep=keep, wrap=True, flip=True)
    # flagstone floor
    rf = RNG("floor")
    cells = []
    y = -2.45
    while y < 1.9:
        hrow = rf.uniform(0.38, 0.6)
        x = -1.9 + rf.uniform(0, 0.3)
        while x < 1.9:
            w = rf.uniform(0.35, 0.7)
            cx, cy = x + w / 2, y + hrow / 2
            inside = math.hypot(cx, cy) < 1.95 or (abs(cx) < 0.75 and cy < -1.5)
            if inside:
                cells.append((cx, cy, w - 0.025, hrow - 0.025))
            x += w
        y += hrow
    c = np.array(cells)
    N = len(c)
    P, T = stone_local(rf, c[:, 2], c[:, 3], np.full(N, 0.07), "flag", rot_deg=(0.3, 0.3, 1.5))
    # stone_local: x = length, y = "outward" (thickness), z = height -> lay flat: local y -> world z
    Rm = frame_mats(np.repeat([[1.0, 0, 0]], N, 0), np.repeat([[0, 0, 1.0]], N, 0), np.repeat([[0, -1.0, 0]], N, 0))
    W = xform(P, Rm, np.stack([c[:, 0], c[:, 1], np.full(N, Z_TH) + rf.normal(0, 0.003, N)], 1))
    P_int.add(W, T, Pl=P, mat="M_stone", smooth="all")
    # ceiling beams + floor boards (first floor at 3.0 m)
    rt = RNG("ceiling")
    for yb in (-0.95, 0.05, 1.0):
        half = math.sqrt(max(1.95 ** 2 - yb ** 2, 0.1))
        member(P_int, "M_timber", [[-half, yb, 3.12]], [[half, yb, 3.12]], 0.24, 0.28, c=0.02, rng=rt, bow=0.015)
    bx = -1.9
    a, b = [], []
    while bx < 1.9:
        w = rt.uniform(0.18, 0.28)
        cx = bx + w / 2
        if not (0.3 < cx < 0.85):  # hatch for the ladder
            half = math.sqrt(max(1.95 ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, half, 3.285])
        else:
            half = math.sqrt(max(1.95 ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, 0.75, 3.285])
        bx += w + 0.008
    a, b = np.array(a), np.array(b)
    member(P_int, "M_timber", a, b, np.full(len(a), 0.0) + rt.uniform(0.17, 0.26, len(a)), 0.035, c=0.006)
    # ladder up to the hatch
    lx = 0.57
    p0, p1 = np.array([lx, 0.15, Z_TH]), np.array([lx, 1.05, 3.35])
    for s in (-0.23, 0.23):
        member(P_int, "M_timber", [p0 + [s, 0, 0]], [p1 + [s, 0, 0]], 0.06, 0.11, c=0.012, rng=rt, bow=0.01)
    nr = 10
    for i in range(nr):
        t = (i + 0.6) / (nr + 0.4)
        pc = p0 + (p1 - p0) * t
        member(P_int, "M_timber", [pc + [-0.27, 0, 0]], [pc + [0.27, 0, 0]], 0.04, 0.04, c=0.01,
               rng=rt, bow=0.004)

    # ---- door leaf (arch-topped plank door, hung ajar 26 deg inward) ----
    LEAF_W = 2 * (DOOR_CW + 0.055)
    leaf_x0 = -LEAF_W / 2
    hinge = np.array([-DOOR_CW - 0.03, -(Rd - 0.335), 0.0])  # hinge axis x,y (vertical)
    ajar = 34 * D2R
    Rleaf = rotm([0, 0, 1], [ajar])[0]  # free edge swings inward (+Y)

    def leaf_xf(P):
        """leaf-local: x lateral, y = thickness (outer face y=0 toward -Y outward), z up -> world."""
        W = np.stack([P[..., 0], -(Rd - 0.335) + P[..., 1], P[..., 2]], -1)
        return (W - hinge) @ Rleaf.T + hinge

    widths = rng.uniform(0.17, 0.23, 6)
    widths = widths / widths.sum() * (LEAF_W - 5 * 0.005)
    ra_top = DOOR_CW + 0.055
    x = leaf_x0
    for w in widths:
        xc = x + w / 2
        h = np.array([[w / 2, 0.021, 1.2]])
        P = rbox(T_BRD, np.array([[1.2, 0.021, w / 2]]), np.array([[0.006, 0.006, 0.006]]))
        # T_BRD is x-length; rotate: plank length vertical -> local x->z
        P = P[:, :, [2, 1, 0]]
        zb = Z_TH + 0.01
        xs_ = xc + P[:, :, 0]
        ztop = ZS_DOOR + np.sqrt(np.clip(ra_top ** 2 - xs_ ** 2, 0, None)) - 0.01
        t = (P[:, :, 2] + 1.2) / 2.4
        Pz = zb + t * (ztop - zb)
        Pl = np.stack([xs_, P[:, :, 1] + 0.021 + rng.uniform(-0.002, 0.002), Pz], -1)
        Pl[:, :, 1] += 0.003 * np.sin(Pz * 3 + xc * 20)  # slight warp
        T_v = dict(T_BRD)
        T_v = flip_tmpl(T_BRD)  # axis permutation flips handedness
        P_leaf.add(leaf_xf(Pl), T_v, Pl=P, mat="M_timber_weathered", smooth="bevel")
        x += w + 0.005
    # ledges + braces on the inner face
    ly = 0.042 + 0.018
    for zl in (Z_TH + 0.32, Z_TH + 1.02, Z_TH + 1.62):
        a = np.array([[leaf_x0 + 0.06, ly, zl]])
        b = np.array([[-leaf_x0 - 0.06, ly, zl]])
        Wm = Part("tmp", ["M_timber"])
        Part.registry.pop()
        member(Wm, "M_timber", a, b, 0.15, 0.036, up=(0, 1, 0), c=0.008)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK, mat="M_timber_weathered", smooth="bevel")
    for (z0, z1) in ((Z_TH + 0.40, Z_TH + 0.94), (Z_TH + 1.10, Z_TH + 1.54)):
        a = np.array([[leaf_x0 + 0.14, ly, z0]])
        b = np.array([[-leaf_x0 - 0.14, ly, z1]])
        Wm = Part("tmp", ["M_timber"])
        Part.registry.pop()
        member(Wm, "M_timber", a, b, 0.11, 0.032, up=(0, 1, 0), c=0.008)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK, mat="M_timber_weathered", smooth="bevel")
    # ---- iron: strap hinges with spear terminals, nail heads, pintles, ring pull, clinched nails ----
    for zh in (Z_TH + 0.32, Z_TH + 1.02, Z_TH + 1.62):
        L = 0.78 if zh < 1.6 else 0.62
        # strap
        n = 12
        xs_ = np.linspace(leaf_x0 + 0.01, leaf_x0 + L, n)
        wv = np.full(n, 0.026)
        wv[-3:] = [0.04, 0.03, 0.006]  # spear terminal
        path = np.stack([xs_, np.full(n, -0.0045), np.full(n, zh)], 1)[None]
        prof = np.array([[0.0045, -1], [0.0045, 1], [-0.0045, 1], [-0.0045, -1]], float)
        prof = np.repeat(prof[None], n, 0)
        prof[:, :, 1] *= wv[:, None]
        prof = prof[None]
        P, T = sweep(path, prof, up=(0, -1, 0))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="none")
        # knuckle around pintle
        kp = np.array([[[leaf_x0 + 0.005, -0.012, zh - 0.05], [leaf_x0 + 0.005, -0.012, zh + 0.05]]])
        P, T = sweep(kp, circle_prof(0.016, 10), up=(1, 0, 0))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
        # nail heads along strap
        nx = np.linspace(leaf_x0 + 0.08, leaf_x0 + L - 0.1, 5)
        prof = np.array([(0.0, 0.0), (0.012, 0.0), (0.011, 0.004), (0.006, 0.008), (0.0, 0.009)])
        P, T = lathe(np.repeat(prof[None], len(nx), 0), 8)
        Rn = rotm([1, 0, 0], np.full(len(nx), PI / 2))
        P = xform(P, Rn, np.stack([nx, np.full(len(nx), -0.008), np.full(len(nx), zh)], 1))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
        # pintle: L-pin leaded into the jamb rebate
        pin = np.array([[hinge[0] - 0.09, hinge[1] - 0.012, zh - 0.06], [hinge[0] + 0.004, hinge[1] - 0.012,
                                                                        zh - 0.06]])
        P, T = sweep(pin[None], rect_prof(0.022, 0.022, 0.004), up=(0, 0, 1))
        P_iron.add(P, T, mat="M_iron", smooth="none")
    # clinched nail heads in rows over the ledges (outer face)
    nails = []
    for zl in (Z_TH + 0.32, Z_TH + 1.02, Z_TH + 1.62):
        x = leaf_x0
        for w in widths:
            for o in (0.3, 0.7):
                nails.append((x + w * o + rng.uniform(-0.01, 0.01), zl + rng.uniform(-0.03, 0.03)))
            x += w + 0.005
    nails = np.array(nails)
    prof = np.array([(0.0, 0.0), (0.009, 0.0), (0.008, 0.003), (0.004, 0.006), (0.0, 0.0065)])
    P, T = lathe(np.repeat(prof[None], len(nails), 0), 6)
    Rn = rotm([1, 0, 0], np.full(len(nails), PI / 2))
    P = xform(P, Rn, np.stack([nails[:, 0], np.full(len(nails), 0.0), nails[:, 1]], 1))
    P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
    # ring pull with back plate and staple
    rx, rz = -leaf_x0 - 0.22, Z_TH + 0.98
    prof = np.array([(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.044, 0.007), (0.012, 0.009), (0.0, 0.016)])
    P, T = lathe(prof[None], 16)
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


def build_ground(parts):
    P_r = parts["rubble"]
    rng = RNG("ground_rubble")
    # clustered scattered rubble around the base and buttress toe, keeping the door path clear
    centers = [(-2.9, 1.6), (-3.1, -0.6), (-1.6, 2.9), (0.9, 3.1), (3.0, 1.9), (4.6, -1.0), (5.9, 0.7),
               (2.7, -2.4), (-2.6, -2.2), (5.2, 1.3), (3.6, 2.6)]
    pts = []
    for cx, cy in centers:
        n = rng.integers(3, 8)
        for _ in range(n):
            pts.append((cx + rng.normal(0, 0.35), cy + rng.normal(0, 0.35)))
    pts = np.array(pts)
    r = np.hypot(pts[:, 0], pts[:, 1])
    ok = (r > 2.75) & ~((np.abs(pts[:, 0]) < 1.0) & (pts[:, 1] < -2.4))
    pts = pts[ok]
    N = len(pts)
    size = np.exp(rng.uniform(np.log(0.06), np.log(0.45), N))
    L = size * rng.uniform(1.0, 1.5, N)
    H = size * rng.uniform(0.5, 0.9, N)
    D = size * rng.uniform(0.7, 1.1, N)
    P, T = stone_local(rng, L, H, D, "boulder", rot_deg=(8, 8, 10))
    P[:, :, 1] += D[:, None] / 2
    R = euler(rng.normal(0, 0.1, N), rng.normal(0, 0.1, N), rng.uniform(0, 2 * PI, N))
    W = xform(P, R, np.stack([pts[:, 0], pts[:, 1], H * rng.uniform(0.05, 0.3, N)], 1))
    P_r.add(W, T, Pl=P, mat="M_rubble", smooth="all")
    # worn path flags and the step stone in front of the door
    fl = [(0.0, -2.95, 1.25, 0.6, 0.075), (0.15, -3.62, 0.95, 0.62, 0.04), (-0.2, -4.3, 0.85, 0.6, 0.03),
          (0.45, -4.85, 0.6, 0.45, 0.025)]
    fl = np.array(fl)
    N = len(fl)
    P, T = stone_local(rng, fl[:, 2], fl[:, 3], np.full(N, 0.16), "flag", rot_deg=(0.5, 0.5, 4))
    # wear: dish the top centre of the step
    P[:, :, 1] -= 0.008 * np.exp(-(P[:, :, 0] / 0.3) ** 2 - (P[:, :, 2] / 0.2) ** 2) * (P[:, :, 1] > -0.02)
    Rm = frame_mats(np.repeat([[1.0, 0, 0]], N, 0), np.repeat([[0, 0, 1.0]], N, 0), np.repeat([[0, -1.0, 0]], N, 0))
    W = xform(P, Rm, np.stack([fl[:, 0], fl[:, 1], fl[:, 4]], 1))
    P_r.add(W, T, Pl=P, mat="M_stone", smooth="all")
    log("ground rubble", len(pts))


# =============================================================================================
# B. SLOPING BUTTRESS (+X)
# =============================================================================================
BT_TOP_X, BT_TOP_Z, BT_TOE_X = 2.40, 3.60, 5.60


def bt_slope_z(x):
    return BT_TOP_Z * (BT_TOE_X - x) / (BT_TOE_X - BT_TOP_X)


def build_buttress(parts):
    P_b = parts["buttress"]
    rng = RNG("buttress")
    k = BT_TOP_Z / (BT_TOE_X - BT_TOP_X)
    for side in (1, -1):
        def ff(zb, zt):
            zm = (zb + zt) / 2
            w = float(butt_halfwidth(zm))
            xa = math.sqrt(max(float(R_out(zm)) ** 2 - w ** 2, 0)) - 0.03
            xb = BT_TOE_X - zm / k + 0.04
            return [(xa, xb)] if xb - xa > 0.1 else []
        S = coursing(rng, 0.0, BT_TOP_Z + 0.05, ff, hr=(0.10, 0.17), hbig=0.24, p_big=0.12, lr=(0.22, 0.6),
                     p_tall=0.05, p_pin=0.14)
        # footing stones bigger: first course boost
        N = len(S["uc"])
        P, T = stone_local(rng, S["L"], S["H"], S["D"], "rubble")
        zc = S["zc"]
        z = zc[:, None] + P[:, :, 2]
        y = butt_halfwidth(z) + rng.normal(0, 0.004, N)[:, None] + P[:, :, 1] + 0.006 * np.sin(S["uc"] * 3)[:, None]
        if side > 0:
            W = np.stack([S["uc"][:, None] + P[:, :, 0], y, z], 2)
        else:
            W = np.stack([S["uc"][:, None] - P[:, :, 0], -y, z], 2)
        P_b.add(W, T, Pl=P, mat="M_stone", smooth="all")
        # mortar core face
        xs = np.linspace(2.1, BT_TOE_X + 0.02, 26)
        jj = np.linspace(0, 1, 12)
        X, J = np.meshgrid(xs, jj, indexing="ij")
        Z = np.minimum(bt_slope_z(X), BT_TOP_Z + 0.4) * J
        Y = side * (butt_halfwidth(Z) - 0.024)
        add_grid(P_b, "M_mortar", np.stack([X, Y, Z], 2), flip=(side < 0))
    # dressed coping slabs along the slope
    sdir = unit(np.array([1.0, 0, -k]))
    ndir = unit(np.array([k, 0, 1.0]))
    x0, x1 = 2.05, BT_TOE_X + 0.25
    Ltot = (x1 - x0) / sdir[0]
    n = 9
    cuts = np.linspace(0, Ltot, n + 1) + np.concatenate([[0], rng.uniform(-0.05, 0.05, n - 1), [0]])
    for i in range(n):
        L = cuts[i + 1] - cuts[i] - 0.014
        sc = (cuts[i] + cuts[i + 1]) / 2
        p = np.array([x0, 0, bt_slope_z(x0)]) + sdir * sc
        w = 2 * float(butt_halfwidth(p[2])) + 0.13 + rng.uniform(-0.03, 0.03)
        th = rng.uniform(0.15, 0.2)
        P, T = stone_local(rng, [L], [w], [th], "ashlar", rot_deg=(1.2, 0.8, 0.8))
        R = frame_mats(sdir[None], ndir[None], unit(np.cross(sdir, ndir))[None])
        W = xform(P, R, (p + ndir * (th + rng.uniform(0, 0.012)) + np.array([0, rng.uniform(-0.025, 0.025), 0]))[None])
        P_b.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # toe footing stones
    N = 4
    P, T = stone_local(rng, rng.uniform(0.4, 0.6, N), rng.uniform(0.18, 0.26, N), rng.uniform(0.3, 0.4, N), "footing")
    R = rotm([0, 0, 1], rng.uniform(-0.3, 0.3, N) + np.array([0, PI, PI / 2, -PI / 2]))
    c = np.array([[5.2, 0.85, 0.07], [5.0, -0.85, 0.06], [5.85, 0.3, 0.05], [5.75, -0.3, 0.05]])
    P_b.add(xform(P, R, c), T, Pl=P, mat="M_stone", smooth="all")


# =============================================================================================
# C. CURB + SHINGLE APRON
# =============================================================================================
AP_RE = 3.17                       # eave radius of the shake bed
AP_ZE = 4.50                       # bed height at the eave
AP_RT = 1.60                       # top radius (tower foot)
AP_ZT = 5.45
AP_A = math.atan2(AP_ZT - AP_ZE, AP_RE - AP_RT)


def cone_frame(phi, alpha):
    """Frame (t_up-slope, n, e_phi) for a cone point at azimuth phi (N,)."""
    phi = np.atleast_1d(phi)
    er = np.stack([np.sin(phi), -np.cos(phi), np.zeros_like(phi)], 1)
    ep = np.stack([np.cos(phi), np.sin(phi), np.zeros_like(phi)], 1)
    ez = np.array([0, 0, 1.0])
    alpha = np.broadcast_to(alpha, phi.shape)[:, None]
    t = -np.cos(alpha) * er + np.sin(alpha) * ez
    n = np.sin(alpha) * er + np.cos(alpha) * ez
    return frame_mats(t, n, ep), er, n


def shingle_local(rng, L, W, tb, tt, jag=0.012, curl=0.012, cup=0.004, comb=0.0, T=T_SHK):
    """Shingle/shake: x = length (butt at -L/2), y = thickness from 0 (bed) up, z = width."""
    N = len(L)
    h = np.stack([L / 2, np.full(N, 0.01), W / 2], 1)
    P = rbox(T, h, np.stack([np.full(N, 0.006), np.full(N, 0.004), np.full(N, 0.006)], 1))
    u = P[:, :, 0] / h[:, None, 0]
    vz = P[:, :, 2] / h[:, None, 2]
    th = tb[:, None] + (tt - tb)[:, None] * (u + 1) / 2
    P[:, :, 1] = (P[:, :, 1] / 0.01 + 1) / 2 * th
    bw = (1 - u) / 2
    a1 = rng.uniform(-jag, jag, N)[:, None]
    a2 = rng.uniform(-jag, jag, N)[:, None]
    f2 = rng.uniform(1.5, 4.0, N)[:, None]
    P[:, :, 0] += (a1 * vz + a2 * np.sin(vz * f2 + a1 * 50)) * bw ** 3
    if comb > 0:
        P[:, :, 0] += rng.uniform(-comb, comb * 0.4, N)[:, None] * ((u + 1) / 2) ** 3 \
                      + rng.uniform(-comb, comb, N)[:, None] * 0.4 * vz * ((u + 1) / 2) ** 3
    P[:, :, 1] += rng.uniform(0, curl, N)[:, None] * bw ** 2 + rng.uniform(-cup, cup, N)[:, None] * vz ** 2
    return P


def apron_wave(phi):
    """Eave line wanders +-3 cm (low frequency) and the skirt sags ~1.5 cm between the 32 rafters."""
    phi = np.asarray(phi, float)
    return 0.018 * np.sin(2 * phi + 0.7) + 0.012 * np.sin(5 * phi + 2.1) - 0.015 * np.sin(16 * phi) ** 2


def build_apron(parts):
    P_c, P_s, P_r = parts["curb"], parts["apron"], parts["apron_frame"]
    rng = RNG("apron")
    ca, sa = math.cos(AP_A), math.sin(AP_A)
    # stone kerb inside (carries the tower sill; hidden behind rafters)
    prof = np.array([[1.40, 4.45], [1.78, 4.45], [1.78, 5.30], [1.40, 5.30]])
    P, T = lathe(np.array([[[1.40, 4.45], [1.78, 4.45], [1.78, 5.30], [1.40, 5.30], [1.40, 4.45]]])[:, :4], 48)
    P_c.add(P, T, mat="M_mortar", smooth="none")
    # timber curb on the cornice (16 lapped segments, 0.22 x 0.24)
    n = 16
    rc = 2.30
    ph = np.arange(n) * 2 * PI / n + rng.uniform(-0.01, 0.01, n)
    a = np.stack([rc * np.sin(ph - PI / n - 0.05), -rc * np.cos(ph - PI / n - 0.05), np.full(n, 4.62)], 1)
    b = np.stack([rc * np.sin(ph + PI / n + 0.05), -rc * np.cos(ph + PI / n + 0.05), np.full(n, 4.62)], 1)
    member(P_c, "M_timber", a, b, 0.22, 0.24, c=0.02, rng=rng, bow=0.006)
    # rafters (32) from the kerb to past the eave
    nr = 32
    ph = (np.arange(nr) + 0.5) * 2 * PI / nr
    def bed(r):
        return AP_ZE + (AP_RE - r) * math.tan(AP_A)
    rr0, rr1 = 1.52, 3.12
    off = -0.025 - 0.02 - 0.06  # below batten + sarking, centre of a 0.12 rafter
    er0 = np.stack([np.sin(ph), -np.cos(ph), np.zeros(nr)], 1)
    nn = np.stack([sa * er0[:, 0], sa * er0[:, 1], np.full(nr, ca)], 1)
    a = er0 * rr0 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr0))], 1) + nn * off
    b = er0 * rr1 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr1))], 1) + nn * off
    member(P_r, "M_timber", a, b, 0.08, 0.12, up=(0, 0, 1), c=0.012, rng=rng, bow=0.01)
    # sarking (thick board shell) from tower foot to just inside the cornice edge
    rs = np.linspace(1.55, 2.78, 6)
    prof_top = np.stack([rs, bed(rs) - 0.025], 1)
    prof_bot = np.stack([rs[::-1], bed(rs[::-1]) - 0.045], 1)
    pr = np.concatenate([prof_top, prof_bot])[None]
    P, T = lathe(pr, 64, caps=False)
    # close as a loop: lathe of a closed profile -> add extra ring connecting last to first
    P_r.add(P, T, mat="M_timber", smooth="none")
    # battens (ring of chords between rafters) at each nailing line
    for rb in (3.06, 2.62, 2.12, 1.70):
        ph0 = np.arange(nr) * 2 * PI / nr
        ph1 = ph0 + 2 * PI / nr
        zb = bed(rb) - 0.0125
        a = np.stack([rb * np.sin(ph0), -rb * np.cos(ph0), np.full(nr, zb)], 1)
        b = np.stack([rb * np.sin(ph1), -rb * np.cos(ph1), np.full(nr, zb)], 1)
        member(P_r, "M_timber", a, b, 0.06, 0.025, c=0.005)
    # shakes: 3 visible courses, each double layered (offset under-layer), long split shakes
    courses = [(0.0, 0.62), (0.62, 1.24), (1.24, 1.86)]
    lift = 0.0
    stats = 0
    for ci, (sb, _) in enumerate(courses):
        rb_ = AP_RE - sb * ca
        C = 2 * PI * rb_
        for layer in (0, 1):
            widths = []
            tot = 0
            while tot < C:
                w = rng.uniform(0.14, 0.22)
                widths.append(w)
                tot += w + rng.uniform(0.004, 0.012)
            widths = np.array(widths) * C / tot
            gaps = C / len(widths)
            phc = (np.cumsum(widths) - widths / 2) / C * 2 * PI + (0.5 * gaps / rb_ if layer == 0 else 0) + ci * 0.37
            phc += rng.uniform(-0.004, 0.004, len(phc))
            N = len(phc)
            L = rng.uniform(0.72, 0.84, N) if ci < 2 else np.zeros(N)
            if ci == 2:
                # top course: reach the tower face (octagon) with ragged comb tips
                a_t = 1.55 + 0.03
                rel = (phc + PI / 8) % (PI / 4) - PI / 8
                r_face = a_t / np.cos(rel) + 0.012
                L = (rb_ - r_face) / ca + rng.uniform(-0.01, 0.07, N)
            sbb = sb - (0.035 if layer == 0 else 0.0) + rng.uniform(-0.015, 0.015, N)
            W = widths * rng.uniform(0.95, 1.04, N)
            tb = rng.uniform(0.026, 0.034, N)
            tt = np.full(N, 0.01)
            P = shingle_local(rng, L, W, tb, tt, jag=0.018, curl=0.015, comb=0.05 if ci == 2 else 0.0)
            keep = rng.random(N) > (0.02 if layer == 1 else 0.0)
            # split shakes: narrow some
            ob = 0.003 + (0.026 if ci > 0 else 0.0) + (0.028 if layer == 1 else 0.0)
            ot = 0.0 + (0.012 if layer == 1 else 0.0)
            beta = np.arctan2(ob - ot, L) + rng.uniform(-0.01, 0.02, N)
            Rf, er, nrm = cone_frame(phc, AP_A)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rng.normal(0, 2.5 * D2R, N))
            sc = sbb + L / 2
            wave = apron_wave(phc) * (1 - sc / 2.2)
            ctr = er * (AP_RE - sc * ca)[:, None] + np.stack([0 * sc, 0 * sc, AP_ZE + sc * sa + wave], 1) \
                + nrm * ((ob + ot) / 2 + rng.uniform(-0.004, 0.006, N))[:, None]
            Wd = xform(P, Rf @ Rl, ctr)
            P_s.add(Wd[keep], T_SHK, Pl=P[keep], mat="M_roof_shake", smooth="bevel")
            stats += keep.sum()
    log("apron shakes", stats)


# =============================================================================================
# D. OCTAGONAL TIMBER SMOCK TOWER
# =============================================================================================
TW_Z0, TW_Z1 = 5.40, 10.55
TW_TAPER = 0.55 / 5.15
TAN225 = math.tan(PI / 8)
COS225 = math.cos(PI / 8)
LEAN_DIR = unit(np.array([-0.95, 0.31, 0.0]))
LEAN_ANG = 0.55 * D2R
LEAN_PIVOT = np.array([0, 0, 5.30])
LEAN_R = rotm(np.cross([0, 0, 1.0], LEAN_DIR), [LEAN_ANG])[0]


def lean(V):
    return (V - LEAN_PIVOT) @ LEAN_R.T + LEAN_PIVOT


def tw_a(z):
    return 1.55 - (np.asarray(z, float) - TW_Z0) * TW_TAPER


def face_axes(k):
    phi = k * PI / 4
    n = np.array([math.sin(phi), -math.cos(phi), 0.0])
    t = np.array([math.cos(phi), math.sin(phi), 0.0])
    return n, t


def face_map(k, l, z, y):
    """Point on tower face k: lateral l (scaled with taper about z), height z, outward y from frame line."""
    n, t = face_axes(k)
    a = tw_a(z)
    return (a + y)[..., None] * n + l[..., None] * t + z[..., None] * np.array([0, 0, 1.0])


def build_tower(parts):
    P_b, P_f, P_i = parts["tower_boards"], parts["tower_frame"], parts["tower_iron"]
    rng = RNG("tower")
    lifts = [(5.52, 7.24), (7.20, 9.04), (9.0, 10.36)]
    hatch = dict(k=0, l=0.28, z0=7.68, z1=8.34)
    nb_total = 0
    for k in range(8):
        for li, (z0, z1) in enumerate(lifts):
            zm = (z0 + z1) / 2
            hw = (float(tw_a(zm)) + 0.03) * TAN225 - 0.12
            # boards across the face
            ws = []
            tot = 0
            while tot < 2 * hw:
                w = rng.uniform(0.15, 0.28)
                ws.append(w)
                tot += w + 0.008
            if tot - 2 * hw > 0.5 * ws[-1] and len(ws) > 1:
                tot -= ws.pop() + 0.008
            ws = np.array(ws) * 2 * hw / tot
            lc = -hw + np.cumsum(ws + 0.008 * 2 * hw / tot) - ws / 2 - 0.004
            N = len(ws)
            pieces = []
            for i in range(N):
                zb = z0 + rng.uniform(-0.025, 0.01)
                zt = z1 + rng.uniform(-0.01, 0.015)
                if k == hatch["k"] and li == 1 and abs(lc[i]) - ws[i] / 2 < hatch["l"] + 0.02:
                    pieces.append((lc[i], ws[i], zb, hatch["z0"] - 0.04))
                    pieces.append((lc[i], ws[i], hatch["z1"] + 0.06, zt))
                else:
                    pieces.append((lc[i], ws[i], zb, zt))
            pc = np.array(pieces)
            N = len(pc)
            Lz = pc[:, 3] - pc[:, 2]
            h = np.stack([Lz / 2, np.full(N, 0.015), pc[:, 1] / 2], 1)
            P = rbox(T_BRD, h, np.stack([np.full(N, 0.006), np.full(N, 0.006), np.full(N, 0.008)], 1))
            u = P[:, :, 0] / h[:, None, 0]
            # cup, bow, loose boards
            P[:, :, 1] += rng.uniform(-0.004, 0.004, N)[:, None] * (P[:, :, 2] / h[:, None, 2]) ** 2
            P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (1 - u ** 2)
            loose = rng.random(N) < 0.06
            skew = np.where(loose, rng.uniform(-1.0, 1.0, N), rng.normal(0, 0.2, N)) * D2R
            yoff = 0.015 + np.where(loose, rng.uniform(0.006, 0.014, N), rng.uniform(-0.002, 0.003, N))
            zc = (pc[:, 2] + pc[:, 3]) / 2
            zz = zc[:, None] + P[:, :, 0]
            ll = pc[:, 0][:, None] + P[:, :, 2] + skew[:, None] * P[:, :, 0]
            scale = (tw_a(zz) + 0.03) / (float(tw_a(zm)) + 0.03)
            yy = yoff[:, None] + P[:, :, 1] + 0.0 * zz
            W = face_map(k, ll * scale, zz, yy)
            P_b.add(W, T_BRD, Pl=P, mat="M_timber_weathered", smooth="bevel")
            nb_total += N
            # cover battens on ~40% of joints
            js = lc[:-1] + ws[:-1] / 2 + 0.004
            sel = rng.random(len(js)) < 0.4
            for jl in js[sel]:
                zz2 = np.array([z0 + 0.03, z1 - 0.02])
                pa = face_map(k, np.array([jl * float(tw_a(zz2[0]) + 0.03) / (float(tw_a(zm)) + 0.03)]),
                              zz2[:1], np.array([0.042]))
                pb = face_map(k, np.array([jl * float(tw_a(zz2[1]) + 0.03) / (float(tw_a(zm)) + 0.03)]),
                              zz2[1:], np.array([0.042]))
                n, t = face_axes(k)
                member(P_b, "M_timber_weathered", pa, pb, 0.045, 0.018, up=n, c=0.005, rng=rng, bow=0.004)
    log("tower boards", nb_total)
    # corner (cant) posts, proud of the boards
    for k in range(8):
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        za, zb = TW_Z0 - 0.1, 10.33
        ra = (float(tw_a(za)) + 0.03) / COS225 + 0.02 - 0.10
        rb = (float(tw_a(zb)) + 0.03) / COS225 + 0.02 - 0.10
        a = bis * ra + np.array([0, 0, za])
        b = bis * rb + np.array([0, 0, zb])
        member(P_f, "M_timber", a[None], b[None], 0.2, 0.2, up=bis, c=0.025, rng=rng, bow=0.01)
    # sill beams, rails with drip boards, top curb, prop collar band
    def ring_members(z, yout, w, d, ext, mat, part, cc=0.015, bow=0.0):
        for k in range(8):
            c0 = (k - 0.5) * PI / 4
            c1 = (k + 0.5) * PI / 4
            rr = (float(tw_a(z)) + yout) / COS225
            pa = np.array([math.sin(c0) * rr, -math.cos(c0) * rr, z])
            pb = np.array([math.sin(c1) * rr, -math.cos(c1) * rr, z])
            dd = unit(pb - pa)
            n, t = face_axes(k)
            member(part, mat, (pa - dd * ext)[None], (pb + dd * ext)[None], w, d, up=n, c=cc, rng=rng, bow=bow)
    ring_members(5.41, -0.03, 0.24, 0.24, 0.06, "M_timber", P_f, cc=0.02, bow=0.008)  # sill
    for zr in (7.22, 9.02):
        ring_members(zr, 0.075, 0.05, 0.11, -0.10, "M_timber", P_f, cc=0.01)       # rail (girt)
        # drip board on the rail, sloping outward, projecting 4 cm
        for k in range(8):
            n, t = face_axes(k)
            hw = (float(tw_a(zr + 0.07)) + 0.03) * TAN225 - 0.10
            ctr = face_map(k, np.array([0.0]), np.array([zr + 0.075]), np.array([0.09]))[0]
            R = frame_mats(t[None], (np.array([0, 0, 1.0]) * 0.97 + n * 0.25)[None] / np.linalg.norm([0.97, 0.25]),
                           None) if False else None
            xa = t
            ya = unit(np.array([0, 0, 1.0]) + n * 0.28)
            za = np.cross(xa, ya)
            blocks_world(P_f, "M_timber", ctr[None], frame_mats(xa[None], ya[None], za[None]),
                         [[hw, 0.011, 0.055]], c=0.004, T=T_PLK)
    ring_members(10.43, -0.0, 0.22, 0.25, 0.08, "M_timber", P_f, cc=0.02)          # top curb
    # iron prop collar at 9.5 m with bolt heads
    for k in range(8):
        n, t = face_axes(k)
        hw = (float(tw_a(9.5)) + 0.05) * TAN225 + 0.02
        pa = face_map(k, np.array([-hw]), np.array([9.5]), np.array([0.052]))
        pb = face_map(k, np.array([hw]), np.array([9.5]), np.array([0.052]))
        member(P_i, "M_iron", pa, pb, 0.012, 0.085, up=n, c=0.003)
        bl = np.array([-hw * 0.5, hw * 0.5])
        bp = face_map(k, bl, np.full(2, 9.5), np.full(2, 0.062))
        prof = np.array([(0.0, 0.0), (0.022, 0.0), (0.022, 0.01), (0.014, 0.016), (0.0, 0.016)])
        P, T = lathe(np.repeat(prof[None], 2, 0), 6)
        R = np.repeat(frame_mats(t[None], np.cross(n, t)[None], n[None]), 2, 0)
        P_i.add(xform(P, R, bp), T, mat="M_iron", smooth="none")
    # hatch on the front face (frame, shutter propped open, interior deck)
    k = hatch["k"]
    n, t = face_axes(k)
    lw, z0, z1 = hatch["l"], hatch["z0"], hatch["z1"]
    def fm(l, z, y):
        return face_map(k, np.atleast_1d(np.asarray(l, float)), np.atleast_1d(np.asarray(z, float)),
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
    up_face = unit(fm(0, z1, 0)[0] - fm(0, z0, 0)[0])
    Rsh = rotm(t, [-ang])[0]   # lower edge swings outward (-n)
    def shutter(P):
        return (P - hinge) @ Rsh.T + hinge
    bw = (2 * lw + 0.06) / 3
    for i in range(3):
        lc = -lw - 0.03 + bw * (i + 0.5)
        pa = fm(lc, z0 - 0.02, 0.09)
        pb = fm(lc, z1 + 0.02, 0.09)
        tmp = Part("tmp", ["M_timber"]); Part.registry.pop()
        member(tmp, "M_timber", pa, pb, bw - 0.008, 0.028, up=n, c=0.005, rng=rng, bow=0.004)
        P_f.add(shutter(tmp.V[0])[None], T_PLK, mat="M_timber_weathered", smooth="bevel")
    for zl in (z0 + 0.1, z1 - 0.1):
        tmp = Part("tmp", ["M_timber"]); Part.registry.pop()
        member(tmp, "M_timber", fm(-lw - 0.01, zl, 0.06), fm(lw + 0.01, zl, 0.06), 0.028, 0.08, up=n, c=0.005)
        P_f.add(shutter(tmp.V[0])[None], T_PLK, mat="M_timber_weathered", smooth="bevel")
        tmp = Part("tmp", ["M_iron"]); Part.registry.pop()
        member(tmp, "M_iron", fm(-0.12 + 0 * zl, z1 + 0.02, 0.108), fm(-0.12, zl - 0.15, 0.108), 0.035, 0.006, up=n,
               c=0.002)
    for s in (-0.16, 0.16):
        tmp = Part("tmp", ["M_iron"]); Part.registry.pop()
        member(tmp, "M_iron", fm(s, z1 + 0.03, 0.108), fm(s, z0 + 0.05, 0.108), 0.04, 0.006, up=n, c=0.002)
        P_i.add(shutter(tmp.V[0])[None], T_PLK, mat="M_iron", smooth="none")
    # prop stick from the sill to the shutter's lower edge
    low = shutter(fm(0.18, z0 - 0.01, 0.09))[0]
    member(P_f, "M_timber", fm(0.18, z0 - 0.02, 0.07), low[None], 0.035, 0.035, up=n, c=0.008)
    # interior deck under the hatch (dark interior)
    ang8 = np.arange(9) * PI / 4 - PI / 8
    rr = (float(tw_a(7.66)) - 0.02) / COS225
    ring = np.stack([rr * np.sin(ang8), -rr * np.cos(ang8), np.full(9, 7.66)], 1)
    ctr = np.repeat([[0, 0, 7.66]], 9, 0)
    add_grid(P_f, "M_timber", np.stack([ctr, ring], 1), flip=False)


# =============================================================================================
# E. CAP (hipped, bell-cast, with a hood over the windshaft neck)   cap-local: X'=heading, Y', Z
# =============================================================================================
CAP_AZ = -15 * D2R
HDIR = np.array([math.sin(CAP_AZ), -math.cos(CAP_AZ), 0.0])
YDIR = np.cross([0, 0, 1.0], HDIR)
CAP_AF, CAP_AB, CAP_B, CAP_ZE, CAP_RISE = 1.22, 1.48, 1.25, 10.80, 1.78
CAP_XC = (CAP_AF - CAP_AB) / 2   # ridge centre (cap extends further aft, over the tail)
HUB_D, HUB_Z, TILT = 1.72, 11.60, 8 * D2R
HOOD_XF, HOOD_YW, HOOD_ZE, HOOD_ZR = 1.10, 0.44, 11.62, 12.06


def _cap_profile():
    ds = np.linspace(0, CAP_B, 600)
    def h_for(tmax):
        th = (25 + (tmax - 25) * smoothstep(0.0, 0.42, ds)) * D2R
        return np.concatenate([[0], np.cumsum(np.tan(th[1:]) * np.diff(ds))])
    lo, hi = 30.0, 80.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if h_for(mid)[-1] < CAP_RISE:
            lo = mid
        else:
            hi = mid
    return ds, h_for(lo), lo


CAP_DS, CAP_HS, CAP_TMAX = _cap_profile()


def cap_h(d):
    d = np.asarray(d, float)
    return np.where(d < 0, d * math.tan(25 * D2R), np.interp(d, CAP_DS, CAP_HS))


def cap_slope(d):
    return (25 + (CAP_TMAX - 25) * smoothstep(0.0, 0.42, np.clip(d, 0, None))) * D2R


def cap_d(x, y):
    x = np.asarray(x, float)
    return np.minimum(np.where(x >= 0, CAP_AF - x, CAP_AB + x), CAP_B - np.abs(y))


def cap_z(x, y):
    return CAP_ZE + cap_h(cap_d(x, y))


def cap_inv_h(hh):
    return np.interp(hh, CAP_HS, CAP_DS)


def hood_z(y):
    return HOOD_ZR - (HOOD_ZR - HOOD_ZE) * np.abs(y) / (HOOD_YW + 0.03)


def capw(P):
    """cap-local (x', y', z) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return P[..., 0:1] * HDIR + P[..., 1:2] * YDIR + P[..., 2:3] * np.array([0, 0, 1.0])


def cap_member(part, mat, a, b, w, d, up=(0, 0, 1), **kw):
    upw = capw(np.asarray(up, float)[None])[0]
    return member(part, mat, capw(np.atleast_2d(a)), capw(np.atleast_2d(b)), w, d, up=upw, **kw)


def build_cap(parts):
    P_sh, P_fr, P_ir = parts["cap_shingles"], parts["cap_frame"], parts["cap_iron"]
    rng = RNG("cap")
    log("cap max pitch %.1f deg" % CAP_TMAX)
    # ---- frame: sheers, cross beams, eave plate, rafters, truck wheels ----
    for s in (-1, 1):
        cap_member(P_fr, "M_timber", [-1.38, s * 0.78, 10.68], [1.12, s * 0.78, 10.68], 0.16, 0.18, c=0.02,
                   rng=rng, bow=0.006)
    for xx in (-1.12, 0.92):
        cap_member(P_fr, "M_timber", [xx, -0.86, 10.68], [xx, 0.86, 10.68], 0.15, 0.17, c=0.018)
    # eave plate ring under the deck
    ins = 0.16
    xf, xb_, ye = CAP_AF - ins, CAP_AB - ins, CAP_B - ins
    corners = [(xf, ye), (-xb_, ye), (-xb_, -ye), (xf, -ye)]
    for i in range(4):
        (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 4]
        dd = unit(np.array([x1 - x0, y1 - y0]))
        cap_member(P_fr, "M_timber", [x0 - dd[0] * 0.08, y0 - dd[1] * 0.08, 10.85],
                   [x1 + dd[0] * 0.08, y1 + dd[1] * 0.08, 10.85], 0.13, 0.15, c=0.025)
    # truck wheels (iron) between curb and sheers
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = capw(np.array([[sx * 0.63, sy * 0.78, 10.625]]))[0]
            radial = unit(np.array([c[0], c[1], 0.0]))
            prof = np.array([(0.0, -0.022), (0.06, -0.022), (0.07, -0.012), (0.07, 0.012), (0.06, 0.022),
                             (0.0, 0.022)])
            P, T = lathe(prof[None], 16)
            tz = np.cross(radial, [0, 0, 1.0])
            R = frame_mats(tz[None], np.array([[0, 0, 1.0]]), radial[None])
            P_ir.add(xform(P, R, c), T, mat="M_iron", smooth="bevel")
            # fork bracket
            for o in (-0.03, 0.03):
                a = c + radial * o + np.array([0, 0, -0.01])
                b = c + radial * o + np.array([0, 0, 0.06])
                member(P_ir, "M_iron", a[None], b[None], 0.03, 0.008, up=radial, c=0.002)
    # ---- deck shell (sarking boards with real thickness) ----
    nx, ny = 30, 28
    xs = np.linspace(-CAP_AB - 0.03, CAP_AF + 0.03, nx)
    ys = np.linspace(-CAP_B - 0.03, CAP_B + 0.03, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zt = cap_z(X, Y) - 0.012
    add_grid(P_fr, "M_timber", np.stack([X, Y, Zt], 2) @ np.eye(3), flip=False)
    Zb = Zt - 0.035
    G = np.stack([X, Y, Zb], 2)
    add_grid(P_fr, "M_timber", G, flip=True)
    # eave band joining top and bottom
    per = np.concatenate([np.stack([xs, np.full(nx, ys[0])], 1), np.stack([np.full(ny, xs[-1]), ys], 1)[1:],
                          np.stack([xs[::-1], np.full(nx, ys[-1])], 1)[1:], np.stack([np.full(ny, xs[0]), ys[::-1]], 1)[1:]])
    zt = cap_z(per[:, 0], per[:, 1]) - 0.012
    band = np.stack([np.stack([per[:, 0], per[:, 1], zt - 0.035], 1), np.stack([per[:, 0], per[:, 1], zt], 1)], 1)
    for part_pts in (band,):
        Pw = part_pts
        add_grid(P_fr, "M_timber", capw(Pw), flip=False)
    # (grids above were built in cap-local; convert)
    # NOTE: add_grid stores given coordinates -> convert the two deck grids too
    for arr in P_fr.V[-3:-1]:
        arr[:] = capw(arr)
    # rafters under the deck: 4 hips + 8 commons
    rafters = []
    for sx, A in ((1, CAP_AF), (-1, CAP_AB)):
        for sy in (-1, 1):
            rafters.append(((sx * (A - 0.05), sy * (CAP_B - 0.05)), (sx * (A - CAP_B + 0.02), 0.0)))
        rafters.append(((sx * (A - 0.05), 0.0), (sx * (A - CAP_B + 0.08), 0.0)))
    for s in (-1, 1):
        for xx in (-0.55, 0.0, 0.55):
            rafters.append(((xx + CAP_XC, s * (CAP_B - 0.05)), (xx * 0.3 + CAP_XC, s * 0.05)))
    for (x0, y0), (x1, y1) in rafters:
        n = 8
        t = np.linspace(0, 1, n)
        xx = x0 + (x1 - x0) * t
        yy = y0 + (y1 - y0) * t
        zz = cap_z(xx, yy) - 0.047 - 0.05
        path = capw(np.stack([xx, yy, zz], 1))[None]
        P, T = sweep(path, rect_prof(0.07, 0.1, 0.012), up=(0, 0, 1))
        P_fr.add(P, T, mat="M_timber", smooth="bevel")
    # ---- shingles ----
    AM = (CAP_AF + CAP_AB) / 2
    sides = [((1, 0), (0, 1), CAP_B, CAP_AF), ((-1, 0), (0, -1), CAP_B, CAP_AB),
             ((0, 1), (-1, 0), AM, CAP_B), ((0, -1), (1, 0), AM, CAP_B)]
    d = -0.035
    courses = []
    while d < CAP_B - 0.06:
        courses.append(d)
        d += 0.12 * math.cos(float(cap_slope(d + 0.06))) * rng.uniform(0.96, 1.04)
    nsh = 0
    # starter (under) course at the eave, then the regular courses; the eave course sits on the starter
    courses = [courses[0]] + courses
    for ci, db in enumerate(courses):
        starter = ci == 0
        for (o, e, hl_base, own) in sides:
            o = np.array([o[0], o[1], 0.0])
            e = np.array([e[0], e[1], 0.0])
            hl = hl_base - db + 0.10
            if hl <= 0.02:
                continue
            ws = []
            tot = 0
            while tot < 2 * hl:
                w = rng.uniform(0.12, 0.2)
                ws.append(w)
                tot += w + rng.uniform(0.003, 0.008)
            ws = np.array(ws) * 2 * hl / tot
            lc = -hl + np.cumsum(ws) + (np.arange(len(ws)) + 0.5) * (2 * hl - ws.sum()) / len(ws) - ws / 2
            lc += (ci % 2) * 0.06 + (0.07 if starter else 0.0)
            N = len(ws)
            L = rng.uniform(0.29, 0.34, N) * (0.8 if starter else 1.0)
            dbb = db + rng.uniform(-0.006, 0.006, N) + (0.012 if starter else 0.0)
            sig = cap_slope(dbb + L * 0.35)
            dc = dbb + L / 2 * np.cos(sig)
            # position on the side in cap-local
            dist_out = own - dc  # coordinate along o
            base = o[None] * dist_out[:, None] + e[None] * lc[:, None]
            if abs(o[1]) > 0.5:
                base = base + np.array([CAP_XC, 0, 0])
            # skip under the hood (front side)
            if o[0] > 0.5:
                under = (np.abs(lc) < HOOD_YW + 0.06) & (CAP_ZE + cap_h(dc) < hood_z(lc) + 0.02)
            else:
                under = np.zeros(N, bool)
            zb = CAP_ZE + cap_h(dc)
            ob, ot = (0.006, 0.002) if starter else ((0.022, 0.004) if ci == 1 else (0.03, 0.004))
            beta = np.arctan2(ob - ot, L) + rng.uniform(-0.01, 0.02, N)
            t = -np.cos(sig)[:, None] * o[None] + np.sin(sig)[:, None] * np.array([0, 0, 1.0])
            nn = np.sin(sig)[:, None] * o[None] + np.cos(sig)[:, None] * np.array([0, 0, 1.0])
            ee = np.cross(t, nn)
            P = shingle_local(rng, L, ws * rng.uniform(0.97, 1.03, N), rng.uniform(0.016, 0.02, N),
                              np.full(N, 0.007), jag=0.01, curl=0.01, cup=0.003)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rng.normal(0, 1.2 * D2R, N))
            ctr = base + np.array([0, 0, 1.0]) * zb[:, None] + nn * ((ob + ot) / 2 + rng.uniform(-0.002, 0.003, N))[:, None]
            Wl = xform(P, frame_mats(t, nn, ee) @ Rl, ctr)
            # clamp to the hip lines
            if abs(o[0]) > 0.5:
                A = CAP_AF if o[0] > 0 else CAP_AB
                lim = CAP_B - A + np.abs(Wl[:, :, 0]) + 0.025
                Wl[:, :, 1] = np.clip(Wl[:, :, 1], -lim, lim)
            else:
                ay = np.abs(Wl[:, :, 1])
                Wl[:, :, 0] = np.clip(Wl[:, :, 0], -(CAP_AB - CAP_B + ay) - 0.025, CAP_AF - CAP_B + ay + 0.025)
            keep = (~under) & (rng.random(N) > 0.015)
            # lower clamp to the ridge height
            Wl[:, :, 2] = np.minimum(Wl[:, :, 2], CAP_ZE + CAP_RISE + 0.03)
            P_sh.add(capw(Wl[keep]), T_SHK, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
            nsh += keep.sum()
    log("cap shingles", nsh)
    # ---- hip boards, ridge roll ----
    vprof = np.array([(0.10, -0.085), (0.10, -0.062), (0.0, 0.028), (-0.10, -0.062), (-0.10, -0.085), (0.0, 0.004)])
    for sx, A in ((1, CAP_AF), (-1, CAP_AB)):
        for sy in (-1, 1):
            dd = np.linspace(-0.05, CAP_B, 16)
            x = sx * (A - dd)
            y = sy * (CAP_B - dd)
            z = CAP_ZE + cap_h(dd) + 0.05 + lowfreq(dd, rng, 0.006)
            path = capw(np.stack([x, y, z], 1))[None]
            P, T = sweep(path, vprof, up=(0, 0, 1))
            P_fr.add(P, T, mat="M_timber_weathered", smooth="bevel")
    path = capw(np.stack([np.linspace(-(CAP_AB - CAP_B) - 0.1, CAP_AF - CAP_B + 0.1, 5), np.zeros(5),
                          np.full(5, CAP_ZE + CAP_RISE + 0.05)],
                         1))[None]
    P, T = sweep(path, vprof * [1.0, 1.0], up=(0, 0, 1))
    P_fr.add(P, T, mat="M_timber_weathered", smooth="bevel")
    # ---- finial: lead hat + turned rings + spike ----
    prof = np.array([(0.2, 0.0), (0.17, 0.045), (0.09, 0.13), (0.065, 0.155), (0.07, 0.17), (0.07, 0.19),
                     (0.045, 0.2), (0.05, 0.235), (0.032, 0.265), (0.038, 0.29), (0.022, 0.32), (0.018, 0.36),
                     (0.009, 0.44), (0.0, 0.5)])
    P, T = lathe(prof[None], 16)
    R = euler([1.2 * D2R], [0.6 * D2R], [0.0])
    P = xform(P, R, capw(np.array([[CAP_XC, 0.0, CAP_ZE + CAP_RISE + 0.02]])))
    P_ir.add(P, T, mat="M_lead", smooth="all")
    # ---- hood over the windshaft neck ----
    # roof planes (boards) + shingles, cheeks (vertical boards), front gable (boards around the shaft)
    yv = np.linspace(0, HOOD_YW + 0.05, 6)
    for s in (-1, 1):
        # roof board shell
        xs = np.linspace(0.2, HOOD_XF + 0.04, 10)
        X, Yv = np.meshgrid(xs, yv, indexing="ij")
        Z = hood_z(Yv) - 0.01
        Gt = np.stack([X, s * Yv, Z], 2)
        Gb = np.stack([X, s * Yv, Z - 0.03], 2)
        add_grid(P_fr, "M_timber", capw(Gt), flip=(s > 0))
        add_grid(P_fr, "M_timber", capw(Gb), flip=(s < 0))
        # eave + verge edge bands
        edge = np.stack([Gb[:, -1], Gt[:, -1]], 1)
        add_grid(P_fr, "M_timber", capw(edge), flip=(s < 0))
        edge = np.stack([Gb[-1, :], Gt[-1, :]], 1)
        add_grid(P_fr, "M_timber", capw(edge), flip=(s > 0))
        # shingles on the hood: courses parallel to its eave
        sl = math.atan2(HOOD_ZR - HOOD_ZE, HOOD_YW + 0.03)
        for ci, yb in enumerate(np.arange(HOOD_YW + 0.06, 0.0, -0.11 * math.cos(sl))):
            xs0 = cap_inv_h(hood_z(yb) - CAP_ZE)
            x_start = CAP_AF - xs0 - 0.04
            xl = np.arange(x_start, HOOD_XF + 0.02, 0.15)
            if len(xl) == 0:
                continue
            N = len(xl)
            L = rng.uniform(0.26, 0.3, N)
            W = rng.uniform(0.13, 0.16, N)
            P = shingle_local(rng, L, W, np.full(N, 0.017), np.full(N, 0.007), jag=0.008, curl=0.008)
            t = np.array([0.0, -s * math.cos(sl), math.sin(sl)])
            nn = np.array([0.0, s * math.sin(sl), math.cos(sl)])
            ee = np.cross(t, nn)
            ctr = np.stack([xl + 0.075 + (ci % 2) * 0.07, np.full(N, s * (yb - L.mean() / 2 * math.cos(sl))),
                            hood_z(yb - L / 2 * math.cos(sl)) + 0.02], 1)
            R = np.repeat(frame_mats(t[None], nn[None], ee[None]), N, 0) @ rotm([0, 0, 1], np.full(N, -0.06))
            Wl = xform(P, R, ctr)
            Wl[:, :, 0] = np.minimum(Wl[:, :, 0], HOOD_XF + 0.05)
            P_sh.add(capw(Wl), T_SHK, Pl=P, mat="M_roof_shingle", smooth="bevel")
        # cheek: vertical boards from the main roof to the hood eave
        for xb in np.arange(0.45, HOOD_XF, 0.13):
            zb = float(cap_z(np.array(xb), np.array(HOOD_YW))) - 0.05
            if zb > HOOD_ZE - 0.05:
                continue
            cap_member(P_fr, "M_timber_weathered", [xb, s * HOOD_YW, zb], [xb, s * HOOD_YW, HOOD_ZE + 0.02],
                       0.12, 0.025, up=(0, s, 0), c=0.005, rng=rng, bow=0.003)
    # ridge of the hood
    path = capw(np.stack([np.linspace(0.25, HOOD_XF + 0.05, 5), np.zeros(5), np.full(5, HOOD_ZR + 0.035)], 1))[None]
    P, T = sweep(path, vprof * [0.8, 0.8], up=(0, 0, 1))
    P_fr.add(P, T, mat="M_timber_weathered", smooth="bevel")
    # front gable boards with a hole for the shaft
    zsh = HUB_Z - (HUB_D - HOOD_XF) * math.tan(TILT)
    rh = 0.235
    for yb in np.arange(-HOOD_YW + 0.06, HOOD_YW - 0.02, 0.125):
        zb0 = float(cap_z(np.array(HOOD_XF), np.array(yb))) - 0.05
        zt = float(hood_z(yb)) - 0.03
        segs = [(zb0, zt)]
        if abs(yb) < rh + 0.06:
            ext = math.sqrt(max(rh ** 2 - min(abs(yb), rh) ** 2, 0)) + 0.01
            segs = [(zb0, zsh - ext), (zsh + ext, zt)]
        for z0, z1 in segs:
            if z1 - z0 > 0.04:
                cap_member(P_fr, "M_timber_weathered", [HOOD_XF, yb, z0], [HOOD_XF, yb, z1], 0.12, 0.025,
                           up=(1, 0, 0), c=0.005, rng=rng, bow=0.002)
    # iron neck collar plate around the hole
    a = np.linspace(0, 2 * PI, 33)[:-1]
    ring = np.stack([np.full(32, HOOD_XF + 0.02), (rh + 0.02) * np.cos(a), zsh + (rh + 0.02) * np.sin(a)], 1)
    P, T = sweep(capw(ring)[None], rect_prof(0.03, 0.07, 0.004), up=capw(np.array([[1.0, 0, 0]]))[0], closed=True)
    P_ir.add(P, T, mat="M_iron", smooth="bevel")
    # breast beam + bearing inside the hood
    cap_member(P_fr, "M_timber", [0.96, -0.4, zsh - 0.32], [0.96, 0.4, zsh - 0.32], 0.22, 0.25, c=0.02)
    # ---- windshaft (16-sided) with iron hoops ----
    x0, x1 = -0.7, HUB_D - 0.36 * math.cos(TILT)
    n = 10
    xs = np.linspace(x0, x1, n)
    zs = HUB_Z - (HUB_D - xs) * math.tan(TILT)
    path = capw(np.stack([xs, np.zeros(n), zs], 1))[None]
    P, T = sweep(path, circle_prof(0.19, 16), up=(0, 0, 1))
    P_ws = parts["windshaft"]
    P_ws.add(P, T, mat="M_timber", smooth="all")
    for xh in (HOOD_XF + 0.06, HOOD_XF + 0.16):
        zh = HUB_Z - (HUB_D - xh) * math.tan(TILT)
        pp = np.stack([np.array([xh - 0.025, xh + 0.025]), np.zeros(2), np.array([zh, zh]) + np.array([-0.0035, 0.0035])],
                      1)
        P, T = sweep(capw(pp)[None], circle_prof(0.2, 16), up=(0, 0, 1))
        P_ws.add(P, T, mat="M_iron", smooth="all")


# =============================================================================================
# F-H. ROTOR: poll end, 4 lattice sails (A boarded), annular 16-blade wind-wheel
# =============================================================================================
S_AX = math.cos(TILT) * HDIR + math.sin(TILT) * np.array([0, 0, 1.0])
E1 = unit(np.cross(-S_AX, [0, 0, 1.0]))
E2 = np.cross(E1, -S_AX)
HUB = HDIR * HUB_D + np.array([0, 0, HUB_Z])
PHI_A = (180 - 8) * D2R
SAIL_R0, SAIL_R1, LAT_LEAD, LAT_TRAIL = 1.3, 5.6, 0.45, 1.10
W_WH = -0.21


def rotw(P):
    """rotor-local (x, y, w) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return HUB + P[..., 0:1] * E1 + P[..., 1:2] * E2 + P[..., 2:3] * S_AX


def er_t(phi):
    return np.array([math.cos(phi), math.sin(phi), 0.0]), np.array([-math.sin(phi), math.cos(phi), 0.0])


def stock_depth(r):
    return 0.30 - 0.14 * np.clip(r, 0, 5.6) / 5.6


def whip_depth(r):
    return 0.16 - 0.06 * np.clip(r - 1.2, 0, 4.4) / 4.4


def stock_w(i):
    return 0.16 if i % 2 == 0 else -0.16


def whip_w(r, i):
    return stock_w(i) + stock_depth(r) / 2 + whip_depth(r) / 2


def twist(r):
    return 12 * D2R * (1 - np.clip((r - SAIL_R0) / (SAIL_R1 - SAIL_R0), 0, 1))


def sail_map(P, i, use_twist=True):
    """sail-local (r, l, z) -> rotor-local; z measured from the whip centre."""
    phi = PHI_A + i * PI / 2
    er, t = er_t(phi)
    r, l, z = P[..., 0], P[..., 1], P[..., 2]
    b = -twist(r) if use_twist else 0 * r
    l2 = l * np.cos(b) - z * np.sin(b)
    z2 = l * np.sin(b) + z * np.cos(b)
    w = whip_w(r, i) + z2
    return r[..., None] * er + l2[..., None] * t + w[..., None] * np.array([0, 0, 1.0])


def perm_tmpl(T, odd):
    return flip_tmpl(T) if odd else T


ROTOR_PARTS = []
STOCK_SIDE = {3: 1, 4: -1, 11: 1, 12: -1}   # wheel blades next to the B and D stocks -> side facing the stock


def build_rotor(parts):
    rng = RNG("rotor")
    P_poll, P_wir = parts["poll_end"], parts["wheel_spokes"]
    letters = "ABCD"
    for i in range(4):
        L = letters[i]
        P_st, P_wh, P_bar, P_hem = parts["sail_%s_stock" % L], parts["sail_%s_whip" % L], parts["sail_%s_bars" % L], \
            parts["sail_%s_hemlaths" % L]
        phi = PHI_A + i * PI / 2
        er, t = er_t(phi)
        # stock half (tapering), from inside the poll end to the tip
        r0, r1 = -0.15, SAIL_R1 + 0.05
        h = np.array([[(r1 - r0) / 2, 0.15, 0.15]])
        P = rbox(T_PLK, h, np.array([[0.02, 0.018, 0.018]]))
        r = (r0 + r1) / 2 + P[:, :, 0]
        sc = stock_depth(r) / 0.30
        Q = np.stack([r, P[:, :, 1] * sc, P[:, :, 2] * sc + stock_w(i)], -1)
        Q[..., 1] += rng.uniform(-0.01, 0.01) * (r / 5.6) ** 2
        Wr = Q[..., 0:1] * er + Q[..., 1:2] * t + Q[..., 2:3] * np.array([0, 0, 1.0])
        P_st.add(rotw(Wr), T_PLK, Pl=P, mat="M_timber_weathered", smooth="bevel")
        # whip
        r0, r1 = 1.2, SAIL_R1 + 0.02
        h = np.array([[(r1 - r0) / 2, 0.08, 0.08]])
        P = rbox(T_PLK, h, np.array([[0.015, 0.014, 0.014]]))
        r = (r0 + r1) / 2 + P[:, :, 0]
        sc = whip_depth(r) / 0.16
        Q = np.stack([r, P[:, :, 1] * sc, P[:, :, 2] * sc], -1)
        P_wh.add(rotw(sail_map(Q, i, use_twist=False)), T_PLK, Pl=P, mat="M_timber_weathered", smooth="bevel")
        # clamps (U-straps) whip -> stock, with nuts
        for rc in (1.45, 2.5, 3.6, 4.75):
            hs = float(stock_depth(rc)) / 2
            hw = float(whip_depth(rc)) / 2
            wc = float(whip_w(rc, i))
            wb = stock_w(i) - hs - 0.008
            wf = wc + hw + 0.008
            sw = max(hs, hw) + 0.008
            bars = [((rc, -sw, wf), (rc, sw, wf)), ((rc, -sw, wb), (rc, sw, wb)),
                    ((rc, -sw, wb), (rc, -sw, wf)), ((rc, sw, wb), (rc, sw, wf))]
            for a, b in bars:
                a = np.array(a)[None]
                b = np.array(b)[None]
                aw = rotw(a[:, 0:1] * er + a[:, 1:2] * t + a[:, 2:3] * np.array([0, 0, 1.0]))
                bw = rotw(b[:, 0:1] * er + b[:, 1:2] * t + b[:, 2:3] * np.array([0, 0, 1.0]))
                dirv = unit(bw - aw)
                member(P_st, 1, aw - dirv * 0.008, bw + dirv * 0.008, 0.05, 0.012, up=rotw(er[None])[0] - HUB, c=0.003)
        # bars (sail-local: length along l) -> permuted axes
        nbar = 18
        rs = np.linspace(SAIL_R0 + 0.04, SAIL_R1 - 0.04, nbar) + rng.uniform(-0.01, 0.01, nbar)
        l0, l1 = LAT_LEAD + 0.035, -LAT_TRAIL - 0.035
        h = np.repeat([[(l0 - l1) / 2, 0.015, 0.025]], nbar, 0)
        P = rbox(T_PLK, h, np.repeat([[0.006, 0.005, 0.006]], nbar, 0))
        P[:, :, 1] += rng.uniform(-0.006, 0.006, (nbar, 1)) * (1 - (P[:, :, 0] / h[:, None, 0]) ** 2)
        Q = np.stack([rs[:, None] + P[:, :, 1], (l0 + l1) / 2 + P[:, :, 0], P[:, :, 2]], -1)
        P_bar.add(rotw(sail_map(Q, i)), perm_tmpl(T_PLK, True), Pl=P, mat="M_timber_weathered", smooth="bevel")
        # hemlaths / uplongs (leading edge, trailing edge, middle of trailing side)
        for lat, wid in ((LAT_LEAD, 0.045), (-0.58, 0.04), (-LAT_TRAIL, 0.05)):
            r0, r1 = SAIL_R0 - 0.02, SAIL_R1 + 0.01
            h = np.array([[(r1 - r0) / 2, wid / 2, 0.035]])
            P = rbox(T_PLK, h, np.array([[0.008, 0.008, 0.008]]))
            Q = np.stack([(r0 + r1) / 2 + P[:, :, 0], lat + P[:, :, 1], P[:, :, 2] + 0.005], -1)
            Q[..., 1] += rng.uniform(-0.012, 0.012) * np.sin((Q[..., 0] - r0) / (r1 - r0) * PI)
            P_hem.add(rotw(sail_map(Q, i)), T_PLK, Pl=P, mat="M_timber_weathered", smooth="bevel")
        if i == 0:
            # board cladding on the trailing lattice of sail A (5 weathered boards, nailed)
            P_bd = parts["sail_A_boards"]
            nbd = 5
            span = LAT_TRAIL - 0.10
            wbd = (span - (nbd - 1) * 0.008) / nbd
            for j in range(nbd):
                lc = -0.10 - wbd / 2 - j * (wbd + 0.008)
                r0 = 1.62 + rng.uniform(-0.04, 0.04)
                r1 = SAIL_R1 - 0.06 + rng.uniform(-0.06, 0.02)
                h = np.array([[(r1 - r0) / 2, 0.01, wbd / 2 * rng.uniform(0.94, 1.0)]])
                P = rbox(T_BRD, h, np.array([[0.006, 0.005, 0.006]]))
                u = P[:, :, 0] / h[0, 0]
                P[:, :, 1] += rng.uniform(-0.008, 0.008) * (1 - u ** 2) + 0.004 * (P[:, :, 2] / h[0, 2]) ** 2
                Q = np.stack([(r0 + r1) / 2 + P[:, :, 0], lc + P[:, :, 2], 0.025 + 0.011 + P[:, :, 1]], -1)
                P_bd.add(rotw(sail_map(Q, i)), perm_tmpl(T_BRD, True), Pl=P, mat="M_timber_weathered",
                         smooth="bevel")
            # nail heads in rows over the bars
            nails = []
            for rb in rs[2::2]:
                for j in range(nbd):
                    lc = -0.10 - wbd / 2 - j * (wbd + 0.008)
                    nails.append((rb, lc + rng.uniform(-0.03, 0.03), 0.047))
            nails = np.array(nails)
            prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
            P, T = lathe(np.repeat(prof[None], len(nails), 0), 6)
            Q = sail_map(nails, i)
            nrm = sail_map(nails + [0, 0, 0.01], i) - Q
            Rn = []
            for v in nrm:
                zz = unit(v)
                xx = unit(np.cross([0.3, 0.5, 0.8], zz))
                Rn.append(np.stack([xx, np.cross(zz, xx), zz], 1))
            Rn = np.array(Rn)
            Wn = xform(P, Rn, Q)
            parts["rotor_iron"].add(rotw(Wn), T, mat="M_iron", smooth="all")
    # ---- poll end (cast-iron cross box) ----
    er, t = er_t(PHI_A)
    h = np.array([[0.23, 0.23, 0.37]])
    P = rbox(T_DRS, h, np.array([[0.025, 0.025, 0.025]]))
    W = P[..., 0:1] * er + P[..., 1:2] * t + P[..., 2:3] * np.array([0, 0, 1.0])
    P_poll.add(rotw(W), T_DRS, Pl=P, mat="M_iron", smooth="bevel")
    # front end cap + boss, rear flange
    prof = np.array([(0.0, 0.37), (0.21, 0.37), (0.22, 0.39), (0.2, 0.42), (0.1, 0.44), (0.06, 0.5), (0.0, 0.51)])
    Pc, T = lathe(prof[None], 24)
    P_poll.add(rotw(Pc), T, mat="M_iron", smooth="all")
    prof = np.array([(0.0, -0.40), (0.36, -0.40), (0.37, -0.385), (0.36, -0.37), (0.0, -0.37)])
    Pc, T = lathe(prof[None], 32)
    P_poll.add(rotw(Pc), T, mat="M_iron", smooth="bevel")
    # bolt heads on the box faces
    bolts = []
    for side in range(4):
        a = PHI_A + side * PI / 2 + PI / 4
        ang = PHI_A + side * PI / 2
        nrm = np.array([math.cos(ang), math.sin(ang), 0])
        tan = np.array([-math.sin(ang), math.cos(ang), 0])
        for u in (-0.15, 0.15):
            for w in (-0.28, 0.28):
                bolts.append((nrm * 0.235 + tan * u + np.array([0, 0, w]), nrm))
    prof = np.array([(0.0, 0.0), (0.026, 0.0), (0.026, 0.014), (0.016, 0.02), (0.0, 0.02)])
    P, T = lathe(np.repeat(prof[None], len(bolts), 0), 6)
    Rb = []
    for c, nrm in bolts:
        xx = unit(np.cross([0, 0, 1.0], nrm))
        Rb.append(np.stack([xx, np.cross(nrm, xx), nrm], 1))
    P_poll.add(rotw(xform(P, np.array(Rb), np.array([b[0] for b in bolts]))), T, mat="M_iron", smooth="bevel")
    # ---- wind-wheel ----
    P_rim, P_bl = parts["wheel_rim"], parts["wheel_blades"]
    ring_w = {1.8: -0.33, 2.85: -0.36}
    for rr, ww in ring_w.items():
        a = np.linspace(0, 2 * PI, 129)[:-1]
        path = np.stack([rr * np.cos(a), rr * np.sin(a), np.full(128, ww) + 0.003 * np.sin(a * 3)], 1)
        P, T = sweep(rotw(path)[None], rect_prof(0.06, 0.012, 0.003), up=S_AX, closed=True)
        P_rim.add(P, T, mat="M_iron", smooth="bevel")
    pitch = 25 * D2R
    nbl = 16
    for k in range(nbl):
        phi = PHI_A + (11.25 + 22.5 * k) * D2R
        er, t = er_t(phi)

        def blade_map(Q):
            r, l, z = Q[..., 0], Q[..., 1], Q[..., 2]
            l2 = l * math.cos(pitch) - z * math.sin(pitch)
            z2 = l * math.sin(pitch) + z * math.cos(pitch)
            return r[..., None] * er + l2[..., None] * t + (W_WH + z2)[..., None] * np.array([0, 0, 1.0])

        nb = 3
        for j in range(nb):
            f0, f1 = j / nb, (j + 1) / nb
            r0 = 1.78
            h = np.array([[1.0, 0.01, 0.5]])
            P = rbox(T_BRD, h, np.array([[0.006, 0.005, 0.006]]))
            u = (P[:, :, 0] + 1.0) / 2.0          # 0..1 along r
            v = (P[:, :, 2] + 0.5)                # 0..1 across this board
            fl = f0 + (f1 - f0) * v               # fraction across the blade
            lat = fl * 2 - 1                      # -1..1 across the blade
            tip = 3.80 - 0.07 * lat ** 2 + rng.uniform(-0.03, 0.02) + 0.01 * np.sin(lat * 7 + k)
            r = r0 + u * (tip - r0)
            Wd = 0.50 + 0.35 * np.clip(r - 1.8, 0, None) / 2.0
            gap = 0.004
            l = (fl - 0.5) * Wd + np.where(v < 0.5, gap, -gap)
            # blades flanking the B/D stock are relieved (notched) on the stock side near the inner ring
            if k in STOCK_SIDE:
                trim = 0.055 * np.clip(1 - (r - 1.8) / 0.9, 0, 1)
                side = STOCK_SIDE[k]
                l = np.where(np.sign(l) == side, l * (1 - trim / (Wd / 2)), l)
            z = P[:, :, 1] + 0.01 * (1 - (lat) ** 2) * 0
            Q = np.stack([r, l, z + rng.uniform(-0.003, 0.003)], -1)
            P_bl.add(rotw(blade_map(Q)), perm_tmpl(T_BRD, True), Pl=P, mat="M_timber", smooth="bevel")
        # central batten on the back
        r0, r1 = 1.74, 3.62
        h = np.array([[(r1 - r0) / 2, 0.025, 0.018]])
        P = rbox(T_PLK, h, np.array([[0.006, 0.006, 0.006]]))
        Q = np.stack([(r0 + r1) / 2 + P[:, :, 0], P[:, :, 1], P[:, :, 2] - 0.028], -1)
        P_bl.add(rotw(blade_map(Q)), T_PLK, Pl=P, mat="M_timber", smooth="bevel")
        # iron brackets batten -> rings, rivet heads on the face
        for rr, ww in ring_w.items():
            top = blade_map(np.array([[rr, 0.0, -0.046]]))[0]
            bot = top.copy()
            bot[2] = ww + 0.007
            member(P_wir, "M_iron", rotw(top[None]), rotw(bot[None]), 0.05, 0.008, up=rotw(er[None])[0] - HUB,
                   c=0.002)
            riv = blade_map(np.array([[rr, -0.06, 0.012], [rr, 0.06, 0.012]]))
            prof = np.array([(0.0, 0.0), (0.012, 0.0), (0.01, 0.004), (0.0, 0.006)])
            P, T = lathe(np.repeat(prof[None], 2, 0), 6)
            nrm = unit(blade_map(np.array([[rr, 0, 0.1]]))[0] - blade_map(np.array([[rr, 0, 0.0]]))[0])
            xx = unit(np.cross(er, nrm))
            R = np.repeat(np.stack([xx, np.cross(nrm, xx), nrm], 1)[None], 2, 0)
            P_wir.add(rotw(xform(P, R, riv)), T, mat="M_iron", smooth="all")
    # spokes (8) to the inner ring and ties (8) to the outer rim
    for k in range(8):
        for (phi, r0, w0, r1, w1) in ((PHI_A + (22.5 + 45 * k) * D2R, 0.30, -0.345, 1.8, -0.33),
                                      (PHI_A + (45 * k) * D2R, 0.33, -0.385, 2.85, -0.372)):
            er, t = er_t(phi)
            n = 6
            rr = np.linspace(r0, r1, n)
            ww = np.linspace(w0, w1, n)
            path = rr[:, None] * er + ww[:, None] * np.array([0, 0, 1.0])
            P, T = sweep(rotw(path)[None], circle_prof(0.0125, 8), up=S_AX)
            P_wir.add(P, T, mat="M_iron", smooth="all")
            # eye / clip at the ring
            pp = rotw((r1 - 0.03) * er + w1 * np.array([0, 0, 1.0]))
            pq = rotw((r1 + 0.035) * er + w1 * np.array([0, 0, 1.0]))
            member(P_wir, "M_iron", pp[None], pq[None], 0.04, 0.02, up=S_AX, c=0.004)
    # clips where the rings pass behind the B/D stock
    for i in (1, 3):
        phi = PHI_A + i * PI / 2
        er, t = er_t(phi)
        for rr, ww in ring_w.items():
            back = stock_w(i) - float(stock_depth(rr)) / 2
            a = rotw(rr * er + (ww - 0.008) * np.array([0, 0, 1.0]))
            b = rotw(rr * er + (back + 0.004) * np.array([0, 0, 1.0]))
            member(P_wir, "M_iron", a[None], b[None], 0.07, 0.03, up=rotw(t[None])[0] - HUB, c=0.004)


# =============================================================================================
# I. RAKING PROPS (-X)
# =============================================================================================
def build_props(parts):
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = RNG("props")
    defs = []
    # two near-parallel long props from the collar (9.5 m) on the -X face, one shorter from 7.3 m on the -X/-Y face
    for (k, lat, z, gnd) in ((6, 0.36, 9.42, (-6.3, -1.2)), (6, -0.36, 9.42, (-6.0, 0.9)),
                             (6, 0.62, 7.30, (-6.0, -3.1))):
        n, t = face_axes(k)
        top = face_map(k, np.array([lat]), np.array([z]), np.array([0.14]))[0]
        defs.append((lean(top[None])[0], np.array([gnd[0], gnd[1], 0.16]), k))
    for idx, (top, bot, k) in enumerate(defs):
        n = 18
        t = np.linspace(0, 1, n)
        axis = bot - top
        L = np.linalg.norm(axis)
        side = unit(np.cross(axis, [0, 0, 1.0]))
        sag = rng.uniform(0.04, 0.08) * np.sin(t * PI) * rng.choice([-1, 1])
        path = top + axis * t[:, None] + side * sag[:, None] + np.array([0, 0, -1.0]) * (0.03 * np.sin(t * PI))[:, None]
        rad = 0.085 + 0.012 * t + 0.004 * np.sin(t * 17 + idx)
        prof = []
        for j in range(n):
            pr = circle_prof(rad[j], 12, sx=1 + rng.uniform(-0.04, 0.04), sy=1 + rng.uniform(-0.04, 0.04))
            prof.append(pr)
        prof = np.array(prof)
        # bark knots
        for _ in range(4):
            j = rng.integers(2, n - 2)
            m = rng.integers(0, 12)
            prof[j, m] *= 1.25
            prof[j, (m + 1) % 12] *= 1.1
        P, T = sweep(path[None], prof[None], up=(0, 0, 1))
        P_p.add(P, T, mat="M_timber_weathered", smooth="all")
        # cut end at the tower: cleat block on the face + iron strap and bolts
        nn, tt = face_axes(k)
        cle = top - nn * 0.09 + np.array([0, 0, -0.18])
        member(P_p, 0, (cle - [0, 0, 0.16])[None], (cle + [0, 0, 0.16])[None], 0.16, 0.08, up=nn, c=0.015)
        ax = unit(axis)
        for o in (0.12, 0.35):
            c = top + ax * o
            a = np.linspace(0, 2 * PI, 17)[:-1]
            uu = unit(np.cross(ax, [0, 0, 1.0]))
            vv = np.cross(ax, uu)
            ring = c + (rad[0] + 0.006) * (np.cos(a)[:, None] * uu + np.sin(a)[:, None] * vv)
            Pr, Tr = sweep(ring[None], rect_prof(0.006, 0.045, 0.002), up=ax, closed=True)
            P_i.add(Pr, Tr, mat="M_iron", smooth="bevel")
        # strap from pole to the collar / cleat
        member(P_i, "M_iron", (top + ax * 0.2)[None], (cle + [0, 0, 0.12])[None], 0.045, 0.008,
               up=nn, c=0.002)
        # ground: stone pad, timber chock, iron pin
        pad = bot + np.array([0, 0, -0.08])
        Pst, Tst = stone_local(rng, [0.62], [0.24], [0.48], "ashlar", rot_deg=(1, 1, 1))
        Rm = frame_mats(np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]), np.array([[0, -1.0, 0]]))
        Rm = rotm([0, 0, 1], [math.atan2(axis[1], axis[0])]) @ Rm
        P_a.add(xform(Pst, Rm, pad[None] + [0, 0, 0.0]), Tst, Pl=Pst, mat="M_stone", smooth="bevel")
        hz = unit(np.array([axis[0], axis[1], 0]))
        member(P_a, "M_timber", (bot - hz * 0.22 + [0, 0, 0.0])[None], (bot - hz * 0.02 + [0, 0, 0.0])[None], 0.2,
               0.1, up=(0, 0, 1), c=0.012)
        member(P_a, "M_iron", (bot + [0, 0, -0.1])[None], (bot + [0, 0, 0.07])[None] + ax * 0.0, 0.025, 0.025,
               up=(1, 0, 0), c=0.004)
    # cross brace between the two long props at ~3 m with bolts
    def at_z(top, bot, z):
        tt = (top[2] - z) / (top[2] - bot[2])
        return top + (bot - top) * tt
    a = at_z(defs[0][0], defs[0][1], 3.1)
    b = at_z(defs[1][0], defs[1][1], 3.3)
    member(P_p, 0, a[None], b[None], 0.11, 0.09, up=(0, 0, 1), c=0.015, rng=rng, bow=0.02)
    return defs


# =============================================================================================
# clearance checks (rotating parts vs. tower / cap / apron / props)
# =============================================================================================
def part_samples(p, res):
    V = np.concatenate(p.V)
    pts = [V]
    if p.Q:
        Q = np.concatenate(p.Q)
        E = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
        a, b = V[E[:, 0]], V[E[:, 1]]
        L = np.linalg.norm(b - a, axis=1)
        m = L > res
        a, b, L = a[m], b[m], L[m]
        n = np.ceil(L / res).astype(int)
        for nn in np.unique(n):
            sel = n == nn
            t = np.linspace(0, 1, nn + 1)[1:-1]
            pts.append((a[sel, None, :] + (b - a)[sel, None, :] * t[None, :, None]).reshape(-1, 3))
    return np.concatenate(pts)


def chamfer_dt(G, res):
    D = np.where(G, 0.0, 1e9)
    a, b = res, res * math.sqrt(2)
    nw, nr = D.shape
    idx = np.arange(nr) * a
    for rows in (range(nw), range(nw - 1, -1, -1)):
        prev = None
        for i in rows:
            row = D[i].copy()
            if prev is not None:
                row = np.minimum(row, prev + a)
                row[1:] = np.minimum(row[1:], prev[:-1] + b)
                row[:-1] = np.minimum(row[:-1], prev[1:] + b)
            row = np.minimum(row, np.minimum.accumulate(row - idx) + idx)
            row = np.minimum(row, (np.minimum.accumulate((row + idx)[::-1]))[::-1] - idx)
            D[i] = row
            prev = row
    return D


def voxel_min_gap(A, B, cell=0.04):
    """Exact minimum distance between sample sets A and B if below `cell`, else returns `cell`."""
    off = 1 << 20

    def key(k):
        return ((k[:, 0] + off) << 42) | ((k[:, 1] + off) << 21) | (k[:, 2] + off)
    ka = np.floor(A / cell).astype(np.int64)
    kb = key(np.floor(B / cell).astype(np.int64))
    order = np.argsort(kb)
    sb = kb[order]
    best = cell
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                kk = key(ka + np.array([dx, dy, dz]))
                lo = np.searchsorted(sb, kk, "left")
                hi = np.searchsorted(sb, kk, "right")
                cand = np.nonzero(hi > lo)[0]
                for a in cand[:20000]:
                    bb = B[order[lo[a]:hi[a]]]
                    d = np.sqrt(((bb - A[a]) ** 2).sum(1)).min()
                    best = min(best, d)
    return best


def rotor_internal_report(parts):
    """Blades vs stocks (exact box test) and lattice/boards vs wheel (voxel proximity < 3-6 cm)."""
    def loc(V):
        d = V - HUB
        return np.stack([d @ E1, d @ E2, d @ S_AX], 1)
    bl = loc(part_samples(parts["wheel_blades"], 0.01))
    worst = 9.0
    for i in range(4):
        phi = PHI_A + i * PI / 2
        er = np.array([math.cos(phi), math.sin(phi)])
        t = np.array([-math.sin(phi), math.cos(phi)])
        r = bl[:, :2] @ er
        l = bl[:, :2] @ t
        hs = stock_depth(r) / 2
        band = (r > 0) & (np.abs(bl[:, 2] - stock_w(i)) < hs)
        if band.any():
            worst = min(worst, float((np.abs(l) - hs)[band].min()))
    log("ROTOR blades vs stocks: min lateral gap inside a stock's depth band = %.3f m %s" %
        (worst, "(PASS)" if worst > 0.01 else "(FAIL)"))
    wheel = np.concatenate([loc(part_samples(parts[k], 0.01)) for k in ("wheel_blades", "wheel_rim", "wheel_spokes")])
    lat = np.concatenate([loc(part_samples(parts["sail_%s_%s" % (L, s)], 0.01)) for L in "ABCD"
                          for s in ("bars", "hemlaths")] + [loc(part_samples(parts["sail_A_boards"], 0.01))])
    gap = voxel_min_gap(lat, wheel, 0.04)
    log("ROTOR lattice/boards vs wind-wheel: min gap %.3f m %s" % (gap, "(PASS)" if gap > 0.015 else "(FAIL)"))
    return worst, gap


def clearance_report(rot_parts, static_parts, xf, res=0.02):
    """Rotation-swept clearance on FINAL (post-lean) positions: map everything to
    (w along the shaft, radius from the shaft). xf(part, V) -> final positions."""
    hub = lean(HUB[None])[0]
    sax = LEAN_R @ S_AX

    def to_rot(V):
        d = V - hub
        w = d @ sax
        rho = np.linalg.norm(d - w[:, None] * sax, axis=1)
        return w, rho
    RV = np.concatenate([xf(p, part_samples(p, res)) for p in rot_parts if p.V])
    w, rho = to_rot(RV)
    w0, w1, r1 = -1.0, 1.2, 6.2
    nw, nr = int((w1 - w0) / res) + 1, int(r1 / res) + 1
    G = np.zeros((nw, nr), bool)
    G[np.clip(((w - w0) / res).astype(int), 0, nw - 1), np.clip((rho / res).astype(int), 0, nr - 1)] = True
    DT = chamfer_dt(G, res)
    out = {}
    for p in static_parts:
        if not p.V:
            continue
        sw, sr = to_rot(xf(p, part_samples(p, res)))
        m = (sw > w0) & (sw < w1) & (sr < r1)
        if not m.any():
            out[p.name] = 9.9
            continue
        d = DT[((sw[m] - w0) / res).astype(int), (sr[m] / res).astype(int)]
        out[p.name] = float(d.min())
    return out


# =============================================================================================
# MAIN
# =============================================================================================
LEANED = ("tower_", "cap_", "windshaft", "poll_end", "sail_", "rotor_iron", "wheel_")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    mats = {mn: bpy.data.materials.new(mn) for mn in MAT_NAMES}
    col = bpy.data.collections.new("MILL")
    scn.collection.children.link(col)
    TW = ["M_timber_weathered"]
    parts = dict(
        stones=Part("MILL_base_stones", ["M_stone"]),
        mortar=Part("MILL_base_mortar", ["M_mortar"]),
        dressed=Part("MILL_base_dressed", ["M_stone_dressed"]),
        interior=Part("MILL_interior", ["M_stone", "M_timber", "M_mortar"]),
        door=Part("MILL_door_leaf", TW),
        door_iron=Part("MILL_door_iron", ["M_iron"]),
        buttress=Part("MILL_buttress_stones", ["M_stone", "M_stone_dressed", "M_mortar"]),
        rubble=Part("MILL_ground_rubble", ["M_rubble", "M_stone"]),
        curb=Part("MILL_curb", ["M_timber", "M_mortar"]),
        apron_frame=Part("MILL_apron_rafters", ["M_timber"]),
        apron=Part("MILL_apron_shingles", ["M_roof_shake"]),
        tower_boards=Part("MILL_tower_boards", TW),
        tower_frame=Part("MILL_tower_frame", ["M_timber", "M_timber_weathered"]),
        tower_iron=Part("MILL_tower_iron", ["M_iron"]),
        cap_frame=Part("MILL_cap_frame", ["M_timber", "M_timber_weathered"]),
        cap_shingles=Part("MILL_cap_shingles", ["M_roof_shingle"]),
        cap_iron=Part("MILL_cap_iron", ["M_iron", "M_lead"]),
        windshaft=Part("MILL_windshaft", ["M_timber", "M_iron"]),
        poll_end=Part("MILL_poll_end", ["M_iron"]),
        rotor_iron=Part("MILL_rotor_iron", ["M_iron"]),
        wheel_rim=Part("MILL_wheel_rim", ["M_iron"]),
        wheel_blades=Part("MILL_wheel_blades", ["M_timber"]),
        wheel_spokes=Part("MILL_wheel_spokes", ["M_iron"]),
        props=Part("MILL_props", TW),
        prop_anchors=Part("MILL_prop_anchors", ["M_stone", "M_timber", "M_iron"]),
        prop_iron=Part("MILL_prop_iron", ["M_iron"]),
    )
    for L in "ABCD":
        parts["sail_%s_stock" % L] = Part("MILL_sail_%s_stock" % L, ["M_timber_weathered", "M_iron"])
        parts["sail_%s_whip" % L] = Part("MILL_sail_%s_whip" % L, TW)
        parts["sail_%s_bars" % L] = Part("MILL_sail_%s_bars" % L, TW)
        parts["sail_%s_hemlaths" % L] = Part("MILL_sail_%s_hemlaths" % L, TW)
    parts["sail_A_boards"] = Part("MILL_sail_A_boards", TW)

    for fn in (build_base, build_door_and_interior, build_ground, build_buttress, build_apron, build_tower,
               build_cap, build_rotor, build_props):
        fn(parts)
        log("built", fn.__name__)

    # ---- clearance checks (spec G / I): rotating parts vs. tower, cap, apron, props ----
    rot = [p for k, p in parts.items() if k.startswith(("sail_", "wheel_", "poll_end", "rotor_iron"))]
    stat = [parts[k] for k in ("tower_boards", "tower_frame", "tower_iron", "cap_frame", "cap_shingles", "cap_iron",
                               "apron", "curb", "props", "prop_anchors", "prop_iron")]
    def is_leaned(p):
        return p.name.replace("MILL_", "").startswith(LEANED)
    clr = clearance_report(rot, stat, lambda p, V: lean(V) if is_leaned(p) else V)
    for k, v in sorted(clr.items(), key=lambda kv: kv[1]):
        log("CLEARANCE rotor -> %-24s %.3f m" % (k, v))
    lowest = min(lean(np.concatenate(p.V))[:, 2].min() for p in rot if p.V)
    log("lowest rotating point z = %.3f m (apron top 5.45 m, ground 0)" % lowest)
    rotor_internal_report(parts)
    log("CLEARANCE CHECK sails vs apron/props >= 0.30 m: %s" %
        ("PASS" if min(clr["MILL_apron_shingles"], clr["MILL_props"]) >= 0.30 else "FAIL"))

    total = 0
    for p in Part.registry:
        ob = p.build(col, mats, post=lean if is_leaned(p) else None)
        if ob is not None:
            total += p.tri_count()
            log("%-28s tris %8d" % (p.name, p.tri_count()))
    log("TOTAL tris", total, "objects", len(col.objects))
    lo = np.min([np.array(o.bound_box).min(0) for o in col.objects], 0)
    hi = np.max([np.array(o.bound_box).max(0) for o in col.objects], 0)
    log("bbox", np.round(lo, 3), np.round(hi, 3))
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    log("saved", OUT_BLEND, "%.1f MB" % (os.path.getsize(OUT_BLEND) / 1e6))


if __name__ == "__main__":
    main()
