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
OUT_BLEND = os.environ.get('MILL_OUT') or os.path.join(HERE, 'tower_windmill.blend')
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
             "M_roof_shingle", "M_roof_shake", "M_iron", "M_lead", "M_moss_clump", "M_soil"]


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

    def __init__(self, name, mats, angle=33.0):
        self.name = name
        self.mats = list(mats)
        self.angle = angle          # smooth-by-angle threshold (deg): sharper dihedrals get split normals
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
        me.polygons.foreach_set("material_index", mats)
        for mn in self.mats:
            me.materials.append(mat_lookup[mn])
        me.validate(clean_customdata=False)
        # smooth by angle: smooth shading everywhere, but every edge whose dihedral exceeds the
        # threshold is marked sharp -> flat faces stay flat, chamfers read crisp, curved sweeps stay soft
        npg = len(me.polygons)
        me.polygons.foreach_set("use_smooth", np.ones(npg, bool))
        ne, nl = len(me.edges), len(me.loops)
        le = np.empty(nl, np.int32)
        me.loops.foreach_get("edge_index", le)
        lt = np.empty(npg, np.int32)
        me.polygons.foreach_get("loop_total", lt)
        pn = np.empty(npg * 3, np.float32)
        me.polygons.foreach_get("normal", pn)
        pn = pn.reshape(-1, 3)
        lp = np.repeat(np.arange(npg), lt)
        order = np.argsort(le, kind="stable")
        cnt = np.bincount(le, minlength=ne)
        start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
        sharp = cnt > 2
        two = np.nonzero(cnt == 2)[0]
        f0 = lp[order[start[two]]]
        f1 = lp[order[start[two] + 1]]
        cosang = (pn[f0] * pn[f1]).sum(1)
        sharp[two[cosang < math.cos(self.angle * D2R)]] = True
        at = me.attributes.get("sharp_edge") or me.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
        at.data.foreach_set("value", sharp)
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


# =============================================================================================
# Shared templates
# =============================================================================================
T_RUB = tmpl_box(9, 4, 7, drop_back=True)     # rubble stones (back face culled, buried in mortar)
T_RUBF = tmpl_box(7, 4, 5)                    # free-standing rubble / boulders
T_PIN = tmpl_box(6, 4, 5, drop_back=True)     # pinning stones
T_DRS = tmpl_box(8, 4, 6)                     # dressed blocks
T_DRSH = tmpl_box(11, 4, 10)                  # hero dressed blocks (door surround, coping): room for spalls
T_BLK = tmpl_box(4, 4, 4)                     # small chamfered blocks / timbers
T_PLK = tmpl_box(9, 4, 4)                     # long members (bendable along x)
T_SHK = tmpl_box(6, 4, 4)                     # shingles (x = length)
T_SHK2 = tmpl_box(8, 4, 6)                    # split shakes (tapered, cupped, ragged)
T_BRD = tmpl_box(10, 4, 5)                    # long boards (x length, z width)
T_DOORB = tmpl_box(14, 4, 9)                  # door planks (fine across the width so the arch head is smooth)


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
# Hewn timber (round 3): variable worn chamfers, adze scallops, long checks, split end grain
# =============================================================================================
_T_HEWN = {}


def hewn_tmpl(nx):
    if nx not in _T_HEWN:
        _T_HEWN[nx] = tmpl_box(nx, 7, 7)
    return _T_HEWN[nx]


def hewn_beam(rng, L, w, d, nx=None, chamfer=(0.015, 0.03), adze=(0.003, 0.005), n_scallop=(2, 3),
              checks=(1, 2), check_len=(0.5, 1.5), end_split=1, faces_check=(2, 1)):
    """One hewn timber, local x = length (centred), y = width, z = depth. Returns (P (1,nv,3), T).
    - chamfer radius varies along the length within `chamfer` (worn arrises),
    - every long face carries 2-3 shallow concave adze scallops (`adze` deep),
    - `checks`: 1-2 long checks (1 cm wide V, 1-1.5 cm deep) on the faces in `faces_check`
      (axis index 1 = +-y faces, 2 = +-z faces),
    - end_split: +1 / -1 / 0 -> a radial split in the end grain at that end."""
    if nx is None:
        nx = int(np.clip(L / 0.12, 8, 60))
    T = hewn_tmpl(nx)
    idx = T["idx"]
    n = T["n"]
    h = np.array([L / 2, w / 2, d / 2])
    tx = idx[:, 0] / (n[0] - 1)
    # chamfer radius per vertex (varies along the length, per arris)
    rr = np.empty((len(idx), 3))
    for a in range(3):
        f = rng.uniform(0.5, 2.0, 2)
        ph = rng.uniform(0, 2 * PI, 2)
        k = 0.5 + 0.25 * np.sin(tx * f[0] * 2 * PI + ph[0]) + 0.25 * np.sin(tx * f[1] * 5 + ph[1])
        rr[:, a] = chamfer[0] + (chamfer[1] - chamfer[0]) * k
    rr[:, 0] = np.minimum(rr[:, 0], 0.02)
    rr = np.minimum(rr, h[None] * 0.45)
    P = np.empty((len(idx), 3))
    for a in range(3):
        na = n[a]
        ia = idx[:, a]
        t = -1 + 2 * (ia - 1) / max(na - 3, 1)
        pos = np.where(ia == 0, -h[a], np.where(ia == na - 1, h[a], t * (h[a] - rr[:, a])))
        P[:, a] = pos
    inner = np.clip(P, -(h - rr), h - rr)
    dd = (P - inner) / rr
    nr = np.linalg.norm(dd, axis=1, keepdims=True)
    P = inner + np.where(nr > 1e-9, dd / np.maximum(nr, 1e-9), 0) * rr
    # centre-line lips 1 cm apart (y and z) -> narrow checks
    for a in (1, 2):
        P[idx[:, a] == 2, a] = -0.005
        P[idx[:, a] == 4, a] = 0.005
        P[idx[:, a] == 3, a] = 0.0
    # adze scallops on the 4 long faces
    for a in (1, 2):
        for sgn in (-1, 1):
            on = (idx[:, a] == (n[a] - 1 if sgn > 0 else 0))
            dep = np.zeros(len(idx))
            for _ in range(int(rng.integers(n_scallop[0], n_scallop[1] + 1))):
                x0 = rng.uniform(-0.8, 0.8) * L / 2
                hl = rng.uniform(0.15, 0.4) * min(1.0, L / 1.2)
                dp = rng.uniform(*adze)
                b = 3 - a
                lat = P[:, b] / h[b]
                dep = np.maximum(dep, dp * np.clip(1 - ((P[:, 0] - x0) / hl) ** 2, 0, 1) *
                                 np.clip(1 - 0.5 * (lat - rng.uniform(-0.4, 0.4)) ** 2, 0, 1))
            P[:, a] -= sgn * dep * on
    # long checks
    nck = int(rng.integers(checks[0], checks[1] + 1)) if checks else 0
    for _ in range(nck):
        a = int(rng.choice(faces_check))
        sgn = rng.choice([-1, 1])
        b = 3 - a
        on = (idx[:, a] == (n[a] - 1 if sgn > 0 else 0)) & (idx[:, b] == 3)
        lc = min(rng.uniform(*check_len), 0.8 * L)
        x0 = rng.uniform(-L / 2 + lc / 2 + 0.05, L / 2 - lc / 2 - 0.05) if L > lc + 0.1 else 0.0
        s_ = np.clip(1 - np.abs(P[:, 0] - x0) / (lc / 2), 0, 1)
        P[:, a] -= sgn * on * rng.uniform(0.01, 0.015) * np.sqrt(s_)
    # split end grain
    if end_split:
        e = idx[:, 0] == (n[0] - 1 if end_split > 0 else 0)
        mid = idx[:, 1] == 3
        up = np.clip(P[:, 2] / h[2] + 0.3, 0, 1)
        P[:, 0] -= end_split * (e & mid) * (0.012 + 0.03 * up)
        mid2 = idx[:, 2] == 3
        P[:, 0] -= end_split * (e & mid2) * 0.012 * np.clip(P[:, 1] / h[1], 0, 1)
    return P[None], T


# =============================================================================================
# Stones
# =============================================================================================
STYLE = {
    # rounding (frac of min dim, min, max), outline noise, face noise (m), pillow range (m), taper, shear
    # cuts = (min, max) straight fracture cuts on the outline; facets = (min, max) tilted face planes;
    # spall = (min, max) edge spalls (dressed work)
    "rubble": dict(rr=(0.08, 0.008, 0.013), ry=0.009, nxz=0.045, ny=0.006, pil=(0.002, 0.009), tap=0.07,
                   shear=0.06, T=T_RUB, cuts=(2, 4), cutk=(0.8, 0.94), facets=(1, 2), hf=0.003, ftilt=0.25,
                   fshave=(0.008, 0.02)),
    "pin": dict(rr=(0.12, 0.004, 0.008), ry=0.006, nxz=0.05, ny=0.004, pil=(0.0, 0.004), tap=0.12,
                shear=0.08, T=T_PIN, cuts=(1, 3), cutk=(0.8, 0.92), facets=(0, 1), hf=0.0015, ftilt=0.3,
                fshave=(0.003, 0.008)),
    "footing": dict(rr=(0.09, 0.01, 0.015), ry=0.012, nxz=0.06, ny=0.006, pil=(0.002, 0.01), tap=0.14,
                    shear=0.1, T=T_RUBF, cuts=(3, 4), facets=(1, 2), hf=0.0025, ftilt=0.5, fshave=(0.006, 0.016)),
    "boulder": dict(rr=(0.2, 0.012, 0.05), ry=0.2, nxz=0.12, ny=0.012, pil=(0.0, 0.01), tap=0.2,
                    shear=0.15, T=T_RUBF, cuts=(3, 4), facets=(1, 2), hf=0.003),
    "dressed": dict(rr=(0.1, 0.008, 0.010), ry=0.010, nxz=0.012, ny=0.0015, pil=(0.0, 0.002), tap=0.015,
                    shear=0.012, T=T_DRS, spall=(1, 2)),
    "hero": dict(rr=(0.1, 0.009, 0.010), ry=0.010, nxz=0.010, ny=0.0015, pil=(0.0, 0.002), tap=0.012,
                 shear=0.01, T=T_DRSH, spall=(2, 4)),
    "ashlar": dict(rr=(0.1, 0.008, 0.012), ry=0.010, nxz=0.03, ny=0.003, pil=(0.0, 0.004), tap=0.04,
                   shear=0.025, T=T_DRS, spall=(0, 2), facets=(0, 1)),
    "flag": dict(rr=(0.2, 0.022, 0.035), ry=0.028, nxz=0.07, ny=0.003, pil=(0.0, 0.004), tap=0.12,
                 shear=0.08, T=T_RUBF, cuts=(2, 3)),
}


def stone_local(rng, L, H, D, style, rot_deg=(2.0, 0.8, 1.1), spall=None):
    """Irregular stone, local x = length, y = outward (front face at y=0), z = up. (N,nv,3).
    Split-stone language: angular outline from straight fracture cuts, a flat bed face with 1-2 tilted
    facets (pillow <= 1 cm), small arris radius. Dressed work: flat faces, 1 cm chamfer, edge spalls."""
    st = STYLE[style]
    T = st["T"]
    L, H, D = (np.asarray(v, float) for v in (L, H, D))
    N = len(L)
    h = np.stack([L / 2, D / 2, H / 2], 1)
    mn = np.minimum(L, H)
    rxz = np.clip(st["rr"][0] * mn, st["rr"][1], st["rr"][2])
    ry = np.minimum(st["ry"], 0.45 * D) if st["ry"] < 0.15 else st["ry"] * np.minimum(mn, D)
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
    if st.get("cuts"):
        # straight fracture cuts across corners of the face outline (exact planes -> straight edges)
        c0, c1 = st["cuts"]
        ncut = rng.integers(c0, c1 + 1, N)
        base_a = rng.uniform(0, 2 * PI, N)
        for k in range(c1):
            a = base_a + k * 2 * PI / c1 + rng.uniform(-0.45, 0.45, N)
            nrm = np.stack([np.cos(a) / h[:, 0], rng.normal(0, 0.12, N) / h[:, 1] * 0.0, np.sin(a) / h[:, 2]], 1)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            proj = np.einsum("nvc,nc->nv", P, nrm)
            o = proj.max(1) * rng.uniform(*st.get("cutk", (0.7, 0.9)), N)
            exc = np.clip(proj - o[:, None], 0, None) * (k < ncut)[:, None]
            P -= exc[:, :, None] * nrm[:, None, :]
    if st.get("facets"):
        # flat bed face + 1-2 tilted split facets shaving part of the face
        f0, f1 = st["facets"]
        nfac = rng.integers(f0, f1 + 1, N)
        for k in range(f1):
            ftl = st.get("ftilt", 0.32)
            nf = unit(np.stack([rng.normal(0, ftl, N), np.ones(N), rng.normal(0, ftl, N)], 1))
            proj = np.einsum("nvc,nc->nv", P, nf)
            o = proj.max(1) - rng.uniform(*st.get("fshave", (0.003, 0.011)), N)
            exc = np.clip(proj - o[:, None], 0, None) * (k < nfac)[:, None]
            P -= exc[:, :, None] * nf[:, None, :]
    sp = spall if spall is not None else st.get("spall")
    if sp:
        # edge spalls: a wedge knocked off a front arris (planar scar, tapered ends)
        s0, s1 = sp
        nsp = rng.integers(s0, s1 + 1, N)
        for k in range(s1):
            side = rng.integers(0, 4, N)            # 0:+x 1:-x 2:+z 3:-z
            dax = np.where(side < 2, 0, 2)
            sgn = np.where(side % 2 == 0, 1.0, -1.0)
            aax = np.where(side < 2, 2, 0)
            dvec = np.zeros((N, 3))
            dvec[np.arange(N), dax] = sgn
            kk = rng.uniform(0.7, 1.4, N)
            nrm = unit(dvec + np.array([0, 1.0, 0]) * kk[:, None])
            edge = dvec * h[np.arange(N), dax][:, None] + np.array([0, 1.0, 0]) * h[:, 1:2]
            dep = rng.uniform(0.012, 0.028, N)
            o = np.einsum("nc,nc->n", edge, nrm) - dep
            ha = h[np.arange(N), aax]
            ca = rng.uniform(-0.75, 0.75, N) * ha
            hl = np.minimum(rng.uniform(0.035, 0.09, N), 0.6 * ha)
            along = np.take_along_axis(P, aax[:, None, None].repeat(P.shape[1], 1), 2)[:, :, 0]
            # crisp scar: full depth over the spall length, short ramps at its ends
            win = np.clip((hl[:, None] - np.abs(along - ca[:, None])) / 0.012, 0, 1)
            proj = np.einsum("nvc,nc->nv", P, nrm)
            exc = np.clip(proj - o[:, None], 0, None) * win * (k < nsp)[:, None]
            P -= exc[:, :, None] * nrm[:, None, :]
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


def coursing(rng, z0, z1, free_fn, hr=(0.10, 0.16), hbig=0.24, p_big=0.12, lr=(0.22, 0.62), joint=(0.006, 0.013),
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
                Hs = (zt - zb) - jv - rng.uniform(0, 0.003)
                zc = (zb + zt) / 2 + rng.uniform(-0.004, 0.004)
                Ds = rng.uniform(*Dr)
                if tall:
                    new_carry.append((uc - Lr / 2 - j / 2, uc + Lr / 2 + j / 2))
                if (not tall) and rng.random() < p_pin and Hs > 0.13 and Lr > 0.25:
                    # main stone + small pinning stones in a strip above or below
                    frac = rng.uniform(0.62, 0.75)
                    top = rng.random() < 0.5
                    Hm = Hs * frac
                    Hp = max(Hs - Hm - jv * 0.6, 0.03)
                    Hm = Hs - Hp - jv * 0.6
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
# blind arcade: clear 0.72 w x 1.08 h (h/w 1.5 as in mill_stone_base), sill on the upper string course
ARCH = dict(cw=0.36, z0=2.92, zs=3.64, ring=(0.15, 0.165), fw=0.17, jz=[2.92, 3.28, 3.64])
BUTT_AZ = 90 * D2R
Z_BAND0, Z_BAL0, Z_BAL1, Z_BAND1 = 2.55, 2.65, 2.82, 2.92
Z_CORN0 = 4.17                     # cornice raised 0.12 m (4.17 - 4.62) to make room for the taller arcade
DZ = 0.12                          # everything above the cornice moves up by this much
MORTAR_RECESS = 0.014


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


# =============================================================================================
# Rubble wall analysis (round 3): every rubble wall records its stones; finalize() rasterises the stone
# outlines at 1 cm in wall coordinates (u along the wall, z up, d outward from the reference face), fills
# every mortar void wider than 3 cm with 4-12 cm pinning stones, measures the visible mortar fraction and
# lays a concave mortar strike (a fillet skirt climbing ~7 mm up each stone's side) around every stone.
# =============================================================================================
def ring_loop(T, j):
    """Boundary loop (around the x/z outline) of a tmpl_box template at y-line j."""
    lut = {tuple(v): i for i, v in enumerate(T["idx"])}
    nx, nz = T["n"][0], T["n"][2]
    loop = [(i, 0) for i in range(nx)] + [(nx - 1, k) for k in range(1, nz)] + \
        [(i, nz - 1) for i in range(nx - 2, -1, -1)] + [(0, k) for k in range(nz - 2, 0, -1)]
    return np.array([lut[(i, j, k)] for i, k in loop])


RING2 = {id(T): (ring_loop(T, 2), ring_loop(T, 1)) for T in (T_RUB, T_RUBF, T_PIN, T_DRS, T_DRSH)}


def hull2d(p):
    """Convex hull (monotone chain), CCW."""
    p = p[np.lexsort((p[:, 1], p[:, 0]))]
    if len(p) < 3:
        return p

    def half(pts):
        h = []
        for q in pts:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (q[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (q[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(q)
        return h
    lo = half(p)
    up = half(p[::-1])
    return np.array(lo[:-1] + up[:-1])


class Wall:
    registry = []

    def __init__(self, name, to_world, to_wall, mortar_d, u0, u1, z0, z1, blocked, period=None, metric_z=None,
                 cell=0.01):
        self.name, self.to_world, self.to_wall, self.mortar_d = name, to_world, to_wall, mortar_d
        self.u0, self.z0, self.cell, self.period = u0, z0, cell, period
        self.nu = int(math.ceil((u1 - u0) / cell))
        self.nz = int(math.ceil((z1 - z0) / cell))
        uc = u0 + (np.arange(self.nu) + 0.5) * cell
        zc = z0 + (np.arange(self.nz) + 0.5) * cell
        self.U, self.Z = np.meshgrid(uc, zc, indexing="ij")
        self.block = blocked(self.U, self.Z)
        self.cov = np.zeros((self.nu, self.nz), bool)
        self.metric_z = metric_z
        self.stones = []
        Wall.registry.append(self)

    def unwrap(self, u, ref):
        if self.period is None:
            return u
        C = self.period
        return ((u - ref + C / 2) % C) - C / 2 + ref

    def add(self, W, T):
        self.stones.append((np.asarray(W), T))
        self.raster(W, T)

    def raster(self, W, T):
        r2, _ = RING2[id(T)]
        R = W[:, r2]
        u, z, d = self.to_wall(R.reshape(-1, 3))
        u = u.reshape(R.shape[:2])
        z = z.reshape(R.shape[:2])
        c = self.cell
        for s in range(len(R)):
            us = self.unwrap(u[s], u[s, 0])
            h = hull2d(np.stack([us, z[s]], 1))
            if len(h) < 3:
                continue
            i0 = int(math.floor((h[:, 0].min() - self.u0) / c))
            i1 = int(math.ceil((h[:, 0].max() - self.u0) / c))
            k0 = max(int(math.floor((h[:, 1].min() - self.z0) / c)), 0)
            k1 = min(int(math.ceil((h[:, 1].max() - self.z0) / c)), self.nz)
            if k1 <= k0 or i1 <= i0:
                continue
            ii = np.arange(i0, i1)
            kk = np.arange(k0, k1)
            pu = self.u0 + (ii + 0.5) * c
            pz = self.z0 + (kk + 0.5) * c
            PU, PZ = np.meshgrid(pu, pz, indexing="ij")
            a = h
            b = np.roll(h, -1, 0)
            cr = (b[:, 0, None, None] - a[:, 0, None, None]) * (PZ[None] - a[:, 1, None, None]) - \
                (b[:, 1, None, None] - a[:, 1, None, None]) * (PU[None] - a[:, 0, None, None])
            ins = (cr >= 0).all(0)
            if self.period is not None:
                iw = ii % self.nu
            else:
                ok = (ii >= 0) & (ii < self.nu)
                ins = ins[ok]
                iw = ii[ok]
            self.cov[iw[:, None], kk[None, :]] |= ins

    def mortar_fraction(self, zlo=None, zhi=None):
        m = ~self.block
        if zlo is not None:
            m &= (self.Z >= zlo) & (self.Z <= zhi)
        n = m.sum()
        return float((~self.cov & m).sum()) / max(n, 1), int(n)

    def max_void(self, where=False):
        D = chamfer_dt(self.cov | self.block, self.cell)
        D[:, :5] = 0                     # ignore the raster's ground / top boundary rows
        D[:, -5:] = 0
        if where:
            i, k = np.unravel_index(np.argmax(D), D.shape)
            return 2 * float(D.max()), self.U[i, k], self.Z[i, k]
        return 2 * float(D.max())

    def fill_pins(self, part, rng, yo=(0.012, 0.024), erode=0.0055, hw=(7, 6)):
        """Fill every mortar void wider than 3 cm with pinning stones shaped to the void: the free region
        around the widest point (eroded by the joint width, limited to ~15 x 13 cm) is flood-filled, its convex
        hull becomes the pin's outline (a box template mapped radially onto the polygon)."""
        c = self.cell
        npins = 0
        polys = []
        for it in range(14):
            occ = self.cov | self.block
            D = chamfer_dt(occ, c)
            cand = np.argwhere(D > 0.0155)
            if len(cand) == 0:
                break
            order = np.argsort(-D[cand[:, 0], cand[:, 1]], kind="stable")
            supp = np.zeros_like(occ)
            new = []
            for q in order:
                i, k = cand[q]
                if supp[i, k]:
                    continue
                ii = np.arange(i - hw[0], i + hw[0] + 1)
                if self.period is not None:
                    ii = ii % self.nu
                else:
                    ii = ii[(ii >= 0) & (ii < self.nu)]
                kk = np.arange(max(k - hw[1], 0), min(k + hw[1] + 1, self.nz))
                free = (D[np.ix_(ii, kk)] >= erode) & ~supp[np.ix_(ii, kk)]
                si = int(np.nonzero(ii == i)[0][0])
                sk = int(np.nonzero(kk == k)[0][0])
                comp = np.zeros_like(free)
                comp[si, sk] = True
                for _ in range(40):
                    g = comp.copy()
                    g[1:] |= comp[:-1]
                    g[:-1] |= comp[1:]
                    g[:, 1:] |= comp[:, :-1]
                    g[:, :-1] |= comp[:, 1:]
                    g &= free
                    if (g == comp).all():
                        break
                    comp = g
                supp[np.ix_(ii, kk)] |= comp
                supp[i, k] = True
                cells = np.argwhere(comp)
                if len(cells) < 4:
                    continue
                pu = self.u0 + (i + (cells[:, 0] - si) + 0.5) * c
                pz = self.z0 + (kk[cells[:, 1]] + 0.5) * c
                pts = np.stack([pu, pz], 1)
                h = hull2d(pts)
                if len(h) < 3:
                    continue
                ext = np.ptp(h, 0)
                if ext.min() < 0.008 or ext.max() < 0.02:
                    continue
                new.append(h)
            if not new:
                break
            W_all, P_all = [], []
            for h in new:
                cen = h.mean(0)
                hp = cen + (h - cen) * 0.97
                ext = np.ptp(hp, 0)
                dep = rng.uniform(0.05, 0.09)
                hh = np.array([[ext[0] / 2, dep / 2, ext[1] / 2]])
                r = np.array([[min(0.006, ext[0] * 0.2), 0.005, min(0.006, ext[1] * 0.2)]])
                P = rbox(T_PIN, hh, r)[0]
                bc = (hp.min(0) + hp.max(0)) / 2
                x, z = P[:, 0], P[:, 2]
                # radial map of the box outline onto the polygon (about the bbox centre)
                cen2 = bc if all(((hp[(j + 1) % len(hp)] - hp[j])[0] * (bc[1] - hp[j][1]) -
                                  (hp[(j + 1) % len(hp)] - hp[j])[1] * (bc[0] - hp[j][0])) >= 0
                                 for j in range(len(hp))) else cen
                vx, vz = x + bc[0] - cen2[0], z + bc[1] - cen2[1]
                ang = np.arctan2(vz, vx)
                dx, dz = np.cos(ang), np.sin(ang)
                # box radius in that direction (about cen2) and polygon radius
                def ray_poly(poly):
                    a = poly - cen2
                    b = np.roll(poly, -1, 0) - cen2
                    e = b - a
                    den = dx[:, None] * e[None, :, 1] - dz[:, None] * e[None, :, 0]
                    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
                    t = (a[None, :, 0] * e[None, :, 1] - a[None, :, 1] * e[None, :, 0]) / den
                    s_ = (a[None, :, 0] * dz[:, None] - a[None, :, 1] * dx[:, None]) / den
                    t = np.where((s_ >= -1e-9) & (s_ <= 1 + 1e-9) & (t > 0), t, np.inf)
                    return t.min(1)
                box = np.array([[-hh[0, 0], -hh[0, 2]], [hh[0, 0], -hh[0, 2]], [hh[0, 0], hh[0, 2]],
                                [-hh[0, 0], hh[0, 2]]]) + bc
                Rb = ray_poly(box)
                Rp = ray_poly(hp)
                f = np.where(np.isfinite(Rb) & np.isfinite(Rp), Rp / np.maximum(Rb, 1e-6), 1.0)
                nu_ = cen2[0] + vx * f
                nz_ = cen2[1] + vz * f
                u_ = np.stack([P[:, 0] / hh[0, 0], P[:, 1] / hh[0, 1], P[:, 2] / hh[0, 2]], 1)[None]
                y = P[:, 1] - hh[0, 1] + 0.003 * noise_field(u_ * 1.5, rng, fmin=1.5, fmax=3.0)[0] * \
                    np.clip(u_[0, :, 1], 0, 1)
                d = self.mortar_d(np.array([cen2[0]]), np.array([cen2[1]]))[0] + rng.uniform(*yo)
                W_all.append(self.to_world(nu_, nz_, d + y))
                P_all.append(np.stack([nu_ - cen2[0], y, nz_ - cen2[1]], 1))
            W = np.array(W_all)
            part.add(W, T_PIN, Pl=np.array(P_all), mat="M_stone", smooth="all")
            self.add(W, T_PIN)
            npins += len(W)
            self.iters = getattr(self, "iters", []) + [len(W)]
        self.rejected = 0
        return npins

    def skirts(self, part, w_out=(0.010, 0.015), climb=0.007):
        """Concave mortar strike: a fillet strip around each stone from ~7 mm up its side down to the mortar."""
        for W, T in self.stones:
            r2, r1 = RING2[id(T)]
            sub = slice(0, None, 2)
            A = W[:, r2[sub]]
            B = W[:, r1[sub]]
            N, m = A.shape[:2]
            ua, za, da = (x.reshape(N, m) for x in self.to_wall(A.reshape(-1, 3)))
            ub, zb, db = (x.reshape(N, m) for x in self.to_wall(B.reshape(-1, 3)))
            ua = self.unwrap(ua, ua[:, :1])
            ub = self.unwrap(ub, ua[:, :1])
            dm = self.mortar_d(ua, za)
            # skip stones whose sides are not exposed, or that sit on a mortar-depth step (footing ledge)
            dmo = self.mortar_d(ua, za - 0.03)
            okst = (np.median(da - dm, 1) > 0.008) & (np.abs(dmo - dm).max(1) < 0.01) & \
                (np.abs(self.mortar_d(ua, za + 0.03) - dm).max(1) < 0.01)
            if not okst.any():
                continue
            sel = np.nonzero(okst)[0]
            ua, za, da, ub, zb, db, dm = ua[sel], za[sel], da[sel], ub[sel], zb[sel], db[sel], dm[sel]
            N = len(sel)
            tgt = dm + climb
            t = np.clip((da - tgt) / np.maximum(da - db, 1e-6), 0, 1)
            ui, zi, di = ua + t * (ub - ua), za + t * (zb - za), da + t * (db - da)
            di = np.maximum(di, dm + 0.001)
            cu, cz = ui.mean(1, keepdims=True), zi.mean(1, keepdims=True)
            du, dz = ui - cu, zi - cz
            nr = np.sqrt(du ** 2 + dz ** 2) + 1e-9
            wo = np.random.default_rng(len(self.stones) + N).uniform(*w_out, (N, 1))
            uo, zo = ui + du / nr * wo, zi + dz / nr * wo
            do = np.minimum(self.mortar_d(uo, zi) - 0.0015, di - 0.002)
            Pin = self.to_world(ui, zi, di)
            Pout = self.to_world(uo, zo, do)
            V = np.concatenate([Pin, Pout], 1)                # (N, 2m, 3)
            j = np.arange(m)
            q = np.stack([j, (j + 1) % m, m + (j + 1) % m, m + j], 1)
            # winding: outward normal must point away from the wall
            T2 = dict(quads=q, tris=np.zeros((0, 3), np.int64), qflat=np.zeros(m, bool), tflat=np.zeros(0, bool),
                      nv=2 * m)
            a, b_, c_ = V[0, q[0, 0]], V[0, q[0, 1]], V[0, q[0, 2]]
            nrm = np.cross(b_ - a, c_ - a)
            out = self.to_world(np.array([ui[0, 0]]), np.array([zi[0, 0]]), np.array([di[0, 0] + 0.05]))[0] - a
            if np.dot(nrm, out) < 0:
                T2["quads"] = q[:, ::-1].copy()
            part.add(V, T2, mat="M_mortar", smooth="all")

    def report(self, label):
        f_all, n = self.mortar_fraction()
        msg = "WALL %-18s visible mortar %.1f%% (%d cells)" % (label, 100 * f_all, n)
        if self.metric_z is not None:
            f, n2 = self.mortar_fraction(*self.metric_z)
            msg += ", plain zone %.1f%%" % (100 * f)
        mv = self.max_void(True)
        msg += ", widest void %.3f m at u %.2f z %.2f, stones %d" % (mv + (sum(len(W) for W, _ in self.stones),))
        log(msg)


def wall_relief(u, z, k=0.0):
    """Low-frequency +-5 mm relief of the mortar body."""
    return 0.0028 * np.sin(u * 7.1 + z * 3.3 + k) + 0.0022 * np.sin(u * 4.3 - z * 8.9 + 1.7 + k)


RREF = 2.53


def drum_to_world(u, z, d):
    th = np.asarray(u) / RREF
    r = R_out(z) + d
    return np.stack([r * np.sin(th), -r * np.cos(th), np.asarray(z, float) + 0 * th], -1)


def drum_to_wall(W):
    W = np.asarray(W)
    th = np.arctan2(W[..., 0], -W[..., 1])
    return th * RREF, W[..., 2], np.hypot(W[..., 0], W[..., 1]) - R_out(W[..., 2])


def drum_mortar_d(u, z):
    z = np.asarray(z, float)
    rec = -0.022 - 0.023 * (1 - smoothstep(0.45, 0.68, z))        # raked to 4.5 cm in the bottom 0.6 m
    foot = 0.065 - 0.042                                           # footing course projects 6.5 cm
    d = np.where(z < 0.40, foot, rec)
    return d + wall_relief(u, z)


def stone_depth_tilt(rng, P, N, p_tilt=0.18):
    """Per-stone face depth (2 cm range) and a 2-4 deg yaw on ~18% of stones so one end stands proud."""
    tilt = rng.random(N) < p_tilt
    ang = np.where(tilt, rng.uniform(2.0, 4.0, N) * rng.choice([-1, 1], N), 0.0) * D2R
    P = xform(P, rotm([0, 0, 1], ang), np.zeros(3))
    return P, rng.uniform(-0.006, 0.012, N)


def emit_drum_stones(part, mat, rng, S, style, yoff_base, bulge=True, wall=None, tilt=True):
    if len(S["uc"]) == 0:
        return 0
    zc = S["zc"]
    th = S["uc"] / R_out(zc)
    P, T = stone_local(rng, S["L"], S["H"], S["D"], style)
    N = len(zc)
    if tilt:
        P, dy = stone_depth_tilt(rng, P, N)
    else:
        dy = rng.uniform(-0.003, 0.004, N)
    yo = yoff_base + dy
    if bulge:  # stones bulge in and out of the wall plane (low-frequency)
        yo += 0.004 * np.sin(th * 3 + 1.3) * np.sin(zc * 2.1 + 0.4) + 0.003 * np.sin(th * 7 + zc * 3)
    W = cyl_place(P, th, zc, yo)
    part.add(W, T, Pl=P, mat=mat, smooth="all")
    if wall is not None:
        wall.add(W, T)
    return len(zc)


def arch_set(P_dr, rng, th0, ri, zs, nv, ring, Dv, jambs, Rfun, yfront=0.03, vert=False, style="dressed"):
    """Dressed voussoir ring + jamb blocks for an arch at azimuth th0.
    jambs: dict side -> list of (z0, z1, face_width)."""
    # voussoirs: widths vary +-25 %, key stone wider
    w = rng.uniform(0.75, 1.25, nv)
    w[nv // 2] = max(w[nv // 2], 1.0) * 1.15
    edges = np.concatenate([[0], np.cumsum(w)]) / w.sum() * PI
    for i in range(nv):
        a0, a1 = edges[i], edges[i + 1]
        ac = (a0 + a1) / 2
        dep = ring[0] + (ring[1] - ring[0]) * math.sin(ac) + rng.uniform(-0.012, 0.012)
        rm = ri + dep / 2
        L = (a1 - a0) * rm - 0.012
        P, T = stone_local(rng, [L], [dep], [Dv], style, rot_deg=(0.2, 0.2, 0.2))
        rho = ri + dep / 2 + P[:, :, 2]
        al = ac - P[:, :, 0] / rm
        E = np.stack([rho * np.cos(al), P[:, :, 1], zs + rho * np.sin(al)], 2)
        W = open_place(E, np.array([th0]), np.array([0.0]), np.array([0.0]), np.array([yfront]), Rfun)
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # jambs
    for s, blocks in jambs.items():
        for (z0, z1, fw) in blocks:
            H = z1 - z0 - 0.012
            P, T = stone_local(rng, [fw], [H], [Dv], style, rot_deg=(0.2, 0.2, 0.3))
            W = open_place(P, np.array([th0]), np.array([s * (ri + fw / 2)]), np.array([(z0 + z1) / 2]),
                           np.array([yfront]), Rfun)
            P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")


def build_base(parts):
    P_st, P_mo, P_dr = parts["stones"], parts["mortar"], parts["dressed"]
    rng = RNG("base_rubble")
    n = 0

    def drum_blocked(U, Z):
        b = (Z < 0.0) | (Z > Z_CORN0) | ((Z > Z_BAND0 - 0.005) & (Z < Z_BAND1 + 0.005))
        C = 2 * PI * RREF
        for th0, fn in OPENINGS:
            du = ((U - th0 * RREF + C / 2) % C) - C / 2
            b |= np.abs(du) < fn(Z) * RREF / R_out(Z)
        return b
    WD = Wall("drum", drum_to_world, drum_to_wall, drum_mortar_d, -PI * RREF, PI * RREF, 0.0, Z_CORN0, drum_blocked,
              period=2 * PI * RREF, metric_z=(0.40, Z_BAND0))
    # 1. footing course (big stones projecting ~7 cm, bottoms cut at the ground)
    S = coursing(rng, -0.04, 0.40, free_fn_drum(rng), hr=(0.18, 0.24), hbig=0.26, p_big=0.0, lr=(0.42, 0.85),
                 p_tall=0.0, p_pin=0.06, Dr=(0.3, 0.4), wob=0.015)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "footing", 0.065, wall=WD)
    # 2. plain rubble 0.40 - 2.55
    S = coursing(rng, 0.40, Z_BAND0, free_fn_drum(rng), hr=(0.095, 0.15), hbig=0.22, p_big=0.1, lr=(0.2, 0.6),
                 p_tall=0.05, p_pin=0.14)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD)
    # 4. arcade zone: ashlar-ish piers to springing, rubble spandrels above
    S = coursing(rng, Z_BAND1, ARCH["zs"], free_fn_drum(rng), hr=(0.2, 0.25), hbig=0.25, p_big=0.0,
                 lr=(0.24, 0.45), p_tall=0.0, p_pin=0.0, wob=0.0, joint=(0.01, 0.016))
    n += emit_drum_stones(P_st, "M_stone", rng, S, "ashlar", 0.012, bulge=False, wall=WD, tilt=False)
    S = coursing(rng, ARCH["zs"], Z_CORN0, free_fn_drum(rng), hr=(0.09, 0.14), hbig=0.18, p_big=0.1,
                 lr=(0.18, 0.5), p_tall=0.03, p_pin=0.1, wob=0.012)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD)
    log("drum rubble stones", n)

    # ---- dressed: door ----
    rd = RNG("door_surround")
    jam = {s: [(DOOR_JZ[i], DOOR_JZ[i + 1], DOOR_JAMBS[s][i]) for i in range(4)] for s in (-1, 1)}
    arch_set(P_dr, rd, 0.0, DOOR_CW, ZS_DOOR, 11, DOOR_RING, 0.34, jam, lambda z: np.full_like(z, R_DOOR),
             yfront=0.03, style="hero")
    # threshold stone (worn dip in the middle)
    P, T = stone_local(rd, [1.32], [0.17], [0.46], "hero", rot_deg=(0.2, 0.2, 0.2), spall=(1, 2))
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
        cth, sth = math.cos(th), math.sin(th)

        def a_world(u, z, d, cth=cth, sth=sth):
            u = np.asarray(u, float)
            z = np.asarray(z, float) + 0 * u
            al = np.sqrt(np.maximum(R_out(z) ** 2 - u ** 2, 0.01)) - 0.25 + d
            return np.stack([u * cth + al * sth, u * sth - al * cth, z], -1)

        def a_wall(W, cth=cth, sth=sth):
            W = np.asarray(W)
            u = W[..., 0] * cth + W[..., 1] * sth
            al = W[..., 0] * sth - W[..., 1] * cth
            z = W[..., 2]
            return u, z, al - np.sqrt(np.maximum(R_out(z) ** 2 - u ** 2, 0.01)) + 0.25

        def a_mort(u, z, k=th):
            return -0.022 + wall_relief(u, z, k)

        def a_block(U, Z, cw=cw):
            top = ARCH["zs"] + np.sqrt(np.clip(cw ** 2 - U ** 2, 0, None))
            return (np.abs(U) > cw) | (Z < ARCH["z0"]) | (Z > top)
        WA = Wall("arch", a_world, a_wall, a_mort, -cw - 0.05, cw + 0.05, ARCH["z0"] - 0.02, ARCH["zs"] + cw + 0.05,
                  a_block)
        if len(S["uc"]):
            P, T = stone_local(ra, S["L"], S["H"], S["D"], "rubble")
            P, dy = stone_depth_tilt(ra, P, len(S["uc"]))
            W = open_place(P, np.full(len(S["uc"]), th), S["uc"], S["zc"], -0.25 + dy)
            P_st.add(W, T, Pl=P, mat="M_stone", smooth="all")
            WA.add(W, T)
        # mortar back panel of the recess (low-frequency relief)
        xs = np.linspace(-cw - 0.06, cw + 0.06, 16)
        zz = np.linspace(ARCH["z0"] - 0.02, ARCH["zs"] + cw + 0.05, 20)
        X, Z = np.meshgrid(xs, zz, indexing="ij")
        add_grid(P_mo, "M_mortar", a_world(X, Z, a_mort(X, Z)), flip=False)

    # ---- band: strings, back panel, balusters ----
    rb = RNG("band")
    skip_b = [(BUTT_AZ, butt_halfwidth(2.7) + 0.02)]
    prof_lo = [(-0.30, 0), (0.10, 0), (0.12, 0.018), (0.12, 0.08), (0.105, 0.097), (-0.30, 0.10)]
    prof_up = [(-0.30, 0), (0.08, 0), (0.10, 0.018), (0.10, 0.082), (0.088, 0.098), (-0.30, 0.10)]
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAND0, prof_lo, skip=skip_b)
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAL1, prof_up, skip=skip_b)
    Rm = float(R_out(Z_BAL0))
    spans = free_on_circle(Rm, [(BUTT_AZ * Rm, butt_halfwidth(2.7) + 0.02)])
    S = coursing(rb, Z_BAL0, Z_BAL1, lambda zb, zt: spans, hr=(0.17, 0.17), p_big=0, lr=(0.3, 0.55), p_tall=0,
                 p_pin=0, wob=0, joint=(0.008, 0.014), Dr=(0.2, 0.25))
    th = S["uc"] / R_out(S["zc"])
    P, T = stone_local(rb, S["L"], S["H"], S["D"], "ashlar")
    P_dr.add(cyl_place(P, th, S["zc"], np.full(len(th), -0.03)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # balusters: stubby turned shafts with 2-3 bands; height, diameter, pitch and lean vary; some eroded,
    # a few replaced by plain blocks (repairs)
    HB = Z_BAL1 - Z_BAL0
    TP, TA = 0.022, 0.022                     # plinth / abacus nominal thickness
    Rb = float(R_out(Z_BAL0 + HB / 2))
    a0, a1 = spans[0]
    nbal = int((a1 - a0) / 0.22)
    us = a0 + (np.arange(nbal) + 0.5) * (a1 - a0) / nbal + rb.uniform(-0.015, 0.015, nbal)
    thb = us / Rb
    hs0 = HB - TP - TA
    base = np.array([(0.034, 0.0), (0.041, 0.005), (0.042, 0.015), (0.035, 0.021), (0.046, 0.044), (0.048, 0.062),
                     (0.041, 0.079), (0.030, 0.089), (0.038, 0.095), (0.039, 0.104), (0.031, 0.110),
                     (0.036, 0.118), (0.036, 1.0)])
    base[-1, 1] = hs0
    base[:-1, 1] *= hs0 / 0.126
    plain = np.zeros(nbal, bool)
    plain[rb.choice(nbal, 3, replace=False)] = True
    dh = rb.uniform(-0.008, 0.008, nbal)
    sel = ~plain
    nb = int(sel.sum())
    prof = np.repeat(base[None], nb, 0)
    prof[:, :, 1] *= ((hs0 + dh[sel]) / hs0)[:, None]
    prof[:, :, 0] *= rb.uniform(0.9, 1.1, (nb, 1))
    prof[:, :, 0] += rb.normal(0, 0.001, (nb, prof.shape[1]))
    m = 16
    P, T = lathe(prof, m)
    # erosion: ~13 % lose part of a bead / neck on one side
    ero = rb.random(nb) < 0.13
    ang = np.arctan2(P[:, :, 1], P[:, :, 0])
    a_c = rb.uniform(-PI, PI, nb)
    zc_e = rb.choice([0.017, 0.05, 0.1], nb) * hs0 / 0.126
    d_ang = np.abs((ang - a_c[:, None] + PI) % (2 * PI) - PI)
    fz = np.clip(1 - ((P[:, :, 2] - zc_e[:, None]) / 0.03) ** 2, 0, 1)
    fa = np.clip(1 - d_ang / rb.uniform(0.8, 1.6, (nb, 1)), 0, 1)
    k = 1 - rb.uniform(0.25, 0.45, (nb, 1)) * fz * fa * ero[:, None]
    P[:, :, 0] *= k
    P[:, :, 1] *= k
    P[:, :, 2] += Z_BAL0 + TP
    lean_r = euler(np.clip(rb.normal(0, 0.8, nb), -1.5, 1.5) * D2R, np.clip(rb.normal(0, 0.8, nb), -1.5, 1.5) * D2R,
                   rb.uniform(0, PI, nb))
    ctr = np.stack([(Rb + 0.055) * np.sin(thb), -(Rb + 0.055) * np.cos(thb), np.zeros(nbal)], 1)
    piv = np.array([0, 0, Z_BAL0 + TP])
    W = xform(P - piv, lean_r, ctr[sel] + piv)
    P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="all")
    log("balusters", nb, "eroded", int(ero.sum()), "plain blocks", int(plain.sum()))
    # plinths and abaci (abacus thickness takes up the shaft height variation)
    hpl = np.stack([rb.uniform(0.05, 0.06, nbal), rb.uniform(0.05, 0.06, nbal), np.full(nbal, TP / 2)], 1)
    Rz = rotm([0, 0, 1], thb + rb.normal(0, 0.04, nbal))
    blocks_world(P_dr, "M_stone_dressed", ctr + np.array([0, 0, Z_BAL0 + TP / 2]), Rz, hpl, c=0.005, T=T_BLK)
    ta = TA - dh
    hab = np.stack([rb.uniform(0.05, 0.06, nbal), rb.uniform(0.05, 0.06, nbal), ta / 2 - 0.0005], 1)
    Rz = rotm([0, 0, 1], thb + rb.normal(0, 0.04, nbal))
    blocks_world(P_dr, "M_stone_dressed", ctr + np.stack([0 * ta, 0 * ta, Z_BAL1 - ta / 2], 1), Rz, hab, c=0.005,
                 T=T_BLK)
    # plain replacement blocks
    ip = np.nonzero(plain)[0]
    P, T = stone_local(rb, rb.uniform(0.085, 0.1, len(ip)), np.full(len(ip), hs0 - 0.002), rb.uniform(0.09, 0.1, len(ip)),
                       "dressed", rot_deg=(0.5, 0.5, 2.0))
    P[:, :, 1] += 0.05
    Rz = rotm([0, 0, 1], thb[ip])
    W = xform(P, Rz, ctr[ip] + np.array([0, 0, Z_BAL0 + TP + hs0 / 2]))
    P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")

    # ---- cornice (raised: 4.17 - 4.62) ----
    rc = RNG("cornice")
    zc0 = Z_CORN0
    profile_course(P_dr, "M_stone_dressed", rc, zc0, [(-0.3, 0), (0.03, 0), (0.04, 0.01), (0.04, 0.06),
                                                    (0.03, 0.07), (-0.3, 0.07)], seg=(0.5, 0.8))
    # frieze course between corbels
    S = coursing(rc, zc0 + 0.07, zc0 + 0.22, lambda zb, zt: [(0.3, 0.3 + 2 * PI * float(R_out(zc0 + 0.15)))],
                 hr=(0.15, 0.15), p_big=0, lr=(0.25, 0.5), p_tall=0, p_pin=0, wob=0, joint=(0.008, 0.012),
                 Dr=(0.2, 0.25))
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
    P_dr.add(cyl_place(P, thc, np.full(ncb, zc0 + 0.145), np.full(ncb, 0.18)), T, Pl=P, mat="M_stone_dressed",
             smooth="bevel")
    profile_course(P_dr, "M_stone_dressed", rc, zc0 + 0.22, [(-0.3, 0), (0.19, 0), (0.20, 0.01), (0.20, 0.042),
                                                           (0.19, 0.05), (-0.3, 0.05)], seg=(0.6, 0.9))
    cap = [(-0.42, 0), (0.19, 0), (0.235, 0.035), (0.24, 0.042), (0.243, 0.056), (0.252, 0.056), (0.256, 0.046),
           (0.29, 0.058), (0.305, 0.072), (0.305, 0.145), (0.29, 0.16), (0.0, 0.18), (-0.42, 0.18)]
    profile_course(P_dr, "M_stone_dressed", rc, zc0 + 0.27, cap, seg=(0.75, 1.05), joint=0.008)

    # ---- pinning stones in every void > 3 cm, concave strike skirts, visible-mortar report ----
    rp = RNG("pins")
    for wl in [w for w in Wall.registry if w.name in ("drum", "arch")]:
        before = wl.mortar_fraction(*wl.metric_z)[0] if wl.metric_z else wl.mortar_fraction()[0]
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_pre.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        npin = wl.fill_pins(P_st, rp)
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_post.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        if wl.name == "drum":
            log("drum pins %d, rejected %d (plain-zone mortar before pins %.1f%%)" % (npin, wl.rejected, 100 * before))
            wl.report("drum")
            log("  pins per iteration", wl.iters)
        if not os.environ.get("MILL_NOSKIRT"):
            wl.skirts(P_mo)
    arch_walls = [w for w in Wall.registry if w.name == "arch"]
    fr = np.mean([w.mortar_fraction()[0] for w in arch_walls])
    log("WALL arcade backs: mean visible mortar %.1f%%, widest void %.3f m" %
        (100 * fr, max(w.max_void() for w in arch_walls)))

    # ---- mortar core (outer skin): recessed 2.2 cm (4.5 cm raked in the bottom 0.6 m), +-5 mm relief ----
    nth = 288
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.concatenate([np.linspace(0.0, 0.40, 6), np.linspace(0.41, 0.70, 5), np.linspace(0.78, Z_BAND0, 22),
                         np.linspace(Z_BAL0, Z_CORN0 + 0.12, 17)])
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    U = np.where(TH > PI, TH - 2 * PI, TH) * RREF
    G = drum_to_world(U, Z, drum_mortar_d(U, Z))
    keep = np.ones((nth, len(zs) - 1), bool)
    # remove cells touching the clear part of door / windows / arcade recesses
    for i in range(nth):
        for j in range(len(zs) - 1):
            th_s = np.array([ths[i], ths[i] + 2 * PI / nth, ths[i] + PI / nth])
            z_s = np.array([zs[j], zs[j + 1], (zs[j] + zs[j + 1]) / 2])
            for tq in th_s:
                for zq in z_s:
                    if inside_clear(tq, zq):
                        keep[i, j] = False
    add_grid(P_mo, "M_mortar", G, keep=keep, wrap=True, flip=False)
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
        P = rbox(T_DOORB, np.array([[1.2, 0.021, w / 2]]), np.array([[0.006, 0.006, 0.006]]))
        # T_DOORB is x-length; rotate: plank length vertical -> local x->z (7 lines across each plank so the
        # arched head is cut smoothly: > 40 segments over the arch)
        P = P[:, :, [2, 1, 0]]
        zb = Z_TH + 0.01
        xs_ = xc + P[:, :, 0]
        ztop = ZS_DOOR + np.sqrt(np.clip(ra_top ** 2 - xs_ ** 2, 0, None)) - 0.01
        t = (P[:, :, 2] + 1.2) / 2.4
        Pz = zb + t * (ztop - zb)
        Pl = np.stack([xs_, P[:, :, 1] + 0.021 + rng.uniform(-0.002, 0.002), Pz], -1)
        Pl[:, :, 1] += 0.003 * np.sin(Pz * 3 + xc * 20)  # slight warp
        T_v = flip_tmpl(T_DOORB)  # axis permutation flips handedness
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
        # strap: lies FLAT on the plank face (50 mm wide in z, 7 mm thick in -y), flat spear terminal
        n = 16
        xs_ = np.linspace(leaf_x0 + 0.01, leaf_x0 + L, n)
        hw = np.full(n, 0.025)
        hw[-4:] = [0.025, 0.036, 0.024, 0.004]           # spear: swells then tapers to a point
        xs_[-4:] = leaf_x0 + L - np.array([0.13, 0.085, 0.04, 0.0])
        hw += rng.uniform(-0.0015, 0.0015, n) * (hw > 0.01)   # hand-forged width wobble
        th_ = 0.0035
        path = np.stack([xs_, np.full(n, -th_), np.full(n, zh) + rng.uniform(-0.002, 0.002, n)], 1)[None]
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
        P, T = lathe(np.repeat(prof[None], len(nx), 0), 8)
        Rn = rotm([1, 0, 0], np.full(len(nx), PI / 2))
        P = xform(P, Rn, np.stack([nx, np.full(len(nx), -0.0068), np.full(len(nx), zh)], 1))
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
    # worn path flags and the step stone in front of the door: irregular 5-7 sided slabs (+-4 cm), 1-2 straight
    # broken edges, undulating tops (+-1 cm), 2-3 edge chips each, set in a ring of half-buried gravel; the
    # step's front arris is worn into a 2-3 cm hollow at the centre
    rf = RNG("path_flags")
    fl = [(0.0, -2.95, 1.25, 0.60, 0.075, 0.12), (0.15, -3.62, 0.95, 0.62, 0.062, 0.10),
          (-0.2, -4.30, 0.85, 0.60, 0.055, 0.095), (0.45, -4.85, 0.60, 0.45, 0.048, 0.085)]
    m = 56
    prof_f = [0.3, 0.6, 0.82, 0.93, 0.985, 1.0, 1.0, 0.97]
    gravel = []
    for fi_, (cx, cy, Lf, Wf, ztop, thk) in enumerate(fl):
        # rectangle with jittered corners (+-4 cm), 1-3 corners knocked off by straight broken edges -> 5-7 sides
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
        nside = len(corners)
        if rf.random() < 0.6:          # one long side broken straight as well
            straight.add(int(rf.integers(0, nside)))
        # resample the polygon by arc length; non-broken edges wander +-1 cm
        segs = [np.linalg.norm(corners[(j + 1) % nside] - corners[j]) for j in range(nside)]
        tot = sum(segs)
        pts = []
        for j in range(nside):
            nseg = max(2, int(round(m * segs[j] / tot)))
            a, b = corners[j], corners[(j + 1) % nside]
            nrm_e = np.array([b[1] - a[1], a[0] - b[0]]) / max(segs[j], 1e-6)
            for q in range(nseg):
                u = q / nseg
                wob = 0.0 if j in straight else 0.01 * math.sin(u * PI) * math.sin(u * 7 + j) + \
                    rf.uniform(-0.004, 0.004) * math.sin(u * PI)
                pts.append(a + (b - a) * u + nrm_e * wob)
        O = np.array(pts)
        mm = len(O)
        rings = []
        for k, f in enumerate(prof_f):
            xy = O * f
            if k <= 4:
                z = ztop - (0.0 if f < 0.95 else (0.003 if k == 4 else 0.0))
                if k == 4:
                    z = ztop - 0.004
            elif k == 5:
                z = ztop - 0.016
            elif k == 6:
                z = ztop - thk + 0.012
            else:
                z = ztop - thk
            zz = np.full(mm, z)
            rings.append(np.stack([xy[:, 0], xy[:, 1], zz], 1))
        Pf = np.array(rings)                                    # (rings, mm, 3) local around (cx, cy)
        topm = np.arange(len(prof_f)) <= 4
        # top undulation (+-1 cm) and a rounded-over top arris
        un = 0.008 * np.sin(Pf[..., 0] * 5.1 + fi_) * np.sin(Pf[..., 1] * 6.3 + 2 * fi_) + \
            0.004 * np.sin(Pf[..., 0] * 11 - Pf[..., 1] * 9 + fi_)
        Pf[..., 2] += un * topm[:, None]
        # 2-3 edge chips
        for _ in range(int(rf.integers(2, 4))):
            j0 = int(rf.integers(0, mm))
            dj = np.abs((np.arange(mm) - j0 + mm // 2) % mm - mm // 2)
            w_ = np.clip(1 - dj / rf.uniform(2.0, 3.5), 0, 1)
            dep = rf.uniform(0.015, 0.028)
            for k in (3, 4, 5):
                Pf[k, :, 2] -= w_ * dep * (0.35 if k == 3 else 1.0)
                Pf[k, :, :2] *= (1 - w_ * (0.02 if k >= 4 else 0.0))[:, None]
        if fi_ == 0:
            # the step's front arris (toward -Y) worn into a hollow at the centre
            front = np.clip(-Pf[..., 1] / (Wf / 2), 0, 1) ** 3
            hol = 0.026 * np.exp(-(Pf[..., 0] / 0.2) ** 2) * front
            Pf[..., 2] -= hol * (np.arange(len(prof_f)) <= 5)[:, None]
        Pf[..., 0] += cx
        Pf[..., 1] += cy
        V = Pf.reshape(1, -1, 3)
        Tf = tmpl_rings(len(prof_f), mm, cap0=True, cap1=True)
        V = add_caps(V, Tf)
        Tf = orient(Tf, V[0])
        P_r.add(V, Tf, mat="M_stone", smooth="bevel")
        # gravel / small stones half-buried round the flag
        ng = int(rf.integers(9, 15))
        jj = rf.integers(0, mm, ng)
        out = O[jj] / np.linalg.norm(O[jj], axis=1, keepdims=True)
        gp = O[jj] + out * rf.uniform(0.03, 0.07, ng)[:, None] + np.array([cx, cy])
        gravel.append(gp)
    gp = np.concatenate(gravel)
    gp = gp[np.hypot(gp[:, 0], gp[:, 1]) > R_BASE0 + 0.08]
    Ng = len(gp)
    sz = np.exp(rf.uniform(np.log(0.03), np.log(0.08), Ng))
    Pg, Tg = stone_local(rf, sz * rf.uniform(1.0, 1.4, Ng), sz * rf.uniform(0.6, 0.9, Ng), sz * rf.uniform(0.7, 1.0, Ng),
                         "boulder", rot_deg=(10, 10, 15))
    Pg[:, :, 1] += (sz * 0.45)[:, None]
    Rg = euler(rf.normal(0, 0.2, Ng), rf.normal(0, 0.2, Ng), rf.uniform(0, 2 * PI, Ng))
    P_r.add(xform(Pg, Rg, np.stack([gp[:, 0], gp[:, 1], sz * rf.uniform(-0.1, 0.15, Ng)], 1)), Tg, Pl=Pg,
            mat="M_rubble", smooth="all")
    log("path flags %d, gravel %d" % (len(fl), Ng))
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
        P, dy = stone_depth_tilt(rng, P, N)
        zc = S["zc"]
        z = zc[:, None] + P[:, :, 2]
        y = butt_halfwidth(z) + dy[:, None] + P[:, :, 1] + 0.004 * np.sin(S["uc"] * 3)[:, None]
        if side > 0:
            W = np.stack([S["uc"][:, None] + P[:, :, 0], y, z], 2)
        else:
            W = np.stack([S["uc"][:, None] - P[:, :, 0], -y, z], 2)
        P_b.add(W, T, Pl=P, mat="M_stone", smooth="all")

        def b_world(u, z, d, side=side):
            u = np.asarray(u, float)
            z = np.asarray(z, float) + 0 * u
            return np.stack([u, side * (butt_halfwidth(z) + d), z], -1)

        def b_wall(W, side=side):
            W = np.asarray(W)
            return W[..., 0], W[..., 2], side * W[..., 1] - butt_halfwidth(W[..., 2])

        def b_mort(u, z, side=side):
            z = np.asarray(z, float)
            return -0.022 - 0.02 * (1 - smoothstep(0.35, 0.6, z)) + wall_relief(u, z, 2.0 + side)

        def b_block(U, Z):
            w = butt_halfwidth(Z)
            xa = np.sqrt(np.maximum(R_out(Z) ** 2 - w ** 2, 0)) - 0.02
            return (U < xa) | (U > BT_TOE_X - Z / k - 0.02) | (Z < 0.0) | (Z > BT_TOP_Z + 0.05)
        WB = Wall("buttress", b_world, b_wall, b_mort, 2.0, BT_TOE_X + 0.1, 0.0, BT_TOP_Z + 0.1, b_block)
        WB.add(W, T)
        npin = WB.fill_pins(P_b, rng)
        WB.report("buttress %+d" % side)
        log("  pins per iteration", WB.iters)
        WB.skirts(P_b)
        # mortar core face (recessed 2.2 cm, raked low down, +-5 mm relief)
        xs = np.linspace(2.1, BT_TOE_X + 0.02, 40)
        jj = np.linspace(0, 1, 24)
        X, J = np.meshgrid(xs, jj, indexing="ij")
        Z = np.minimum(bt_slope_z(X), BT_TOP_Z + 0.4) * J
        add_grid(P_b, "M_mortar", b_world(X, Z, b_mort(X, Z) - 0.002), flip=(side < 0))
    # mortar bed along the slope (closes the top of the rubble core: nothing can be seen through)
    sdir = unit(np.array([1.0, 0, -k]))
    ndir = unit(np.array([k, 0, 1.0]))
    x0, x1 = 2.05, BT_TOE_X + 0.25
    xs = np.linspace(x0, x1, 24)
    zl = bt_slope_z(xs)
    pts = np.stack([xs, np.zeros_like(xs), zl], 1) - ndir * 0.012
    hwb = butt_halfwidth(np.clip(zl, 0, 3.6)) + 0.035
    prof = np.stack([np.stack([hwb, -0.03 + 0 * hwb], 1), np.stack([hwb, 0.015 + 0 * hwb], 1),
                     np.stack([-hwb, 0.015 + 0 * hwb], 1), np.stack([-hwb, -0.03 + 0 * hwb], 1)], 1)
    Pb, Tb = sweep(pts[None], prof[None], up=ndir)
    P_b.add(Pb, Tb, mat="M_mortar", smooth="none")
    # dressed coping slabs bedded on the mortar: lengths 0.5-0.9 m, tops flush (+-3 mm) at the joints,
    # weathered dished tops (+-1 cm), 1-2 spalls on the top arrises, upper arrises worn more than the lower,
    # two cracked slabs, one slab turned 1.5 deg in plan
    Ltot = (x1 - x0) / sdir[0]
    Ls = []
    while sum(Ls) < Ltot:
        Ls.append(rng.uniform(0.5, 0.9))
    Ls = np.array(Ls) * Ltot / sum(Ls)
    cuts = np.concatenate([[0], np.cumsum(Ls)])
    nsl = len(Ls)
    cracked = set(int(v) for v in rng.choice(np.arange(1, nsl - 1), 2, replace=False))
    turned = int(rng.choice([i for i in range(1, nsl - 1) if i not in cracked]))
    th = 0.172
    R0 = frame_mats(sdir[None], ndir[None], unit(np.cross(sdir, ndir))[None])
    for i in range(nsl):
        L = cuts[i + 1] - cuts[i] - 0.010
        sc = (cuts[i] + cuts[i + 1]) / 2
        p = np.array([x0, 0, bt_slope_z(x0)]) + sdir * sc
        w = 2 * float(butt_halfwidth(np.clip(p[2], 0, 3.6))) + 0.13 + rng.uniform(-0.01, 0.01)
        P, T = stone_local(rng, [L], [w], [th], "hero", rot_deg=(0.0, 0.0, 0.0), spall=(0, 0))
        hx, hz_ = L / 2, w / 2
        ux = P[:, :, 0] / hx
        uz = P[:, :, 2] / hz_
        top = np.clip((P[:, :, 1] + 0.03) / 0.03, 0, 1)            # 1 on the top face (local y = 0)
        # dished, weathered top (+-1 cm) - zero at the ends so joints stay flush
        P[:, :, 1] -= top * (0.008 * np.clip(1 - ux ** 2, 0, 1) * np.clip(1 - 0.6 * uz ** 2, 0, 1)
                             + 0.004 * noise_field(np.stack([ux, uz, ux * uz], -1), rng)[..., None][..., 0] *
                             np.clip(1 - ux ** 2, 0, 1))
        # the long top arrises are worn round (upper edges more than lower)
        P[:, :, 1] -= top * 0.014 * np.clip((np.abs(uz) - 0.82) / 0.18, 0, 1) ** 2
        P[:, :, 2] -= np.sign(uz) * top * 0.006 * np.clip((np.abs(uz) - 0.82) / 0.18, 0, 1)
        # 1-2 spalls on the top long arrises
        for _ in range(int(rng.integers(1, 3))):
            sz = rng.choice([-1, 1])
            ca = rng.uniform(-0.7, 0.7) * hx
            hl = rng.uniform(0.06, 0.12)
            dep = rng.uniform(0.02, 0.03)
            nrm_ = unit(np.array([0, 1.0, sz * rng.uniform(0.8, 1.3)]))
            edge = np.array([0, 0.0, sz * hz_])
            o = edge @ nrm_ - dep
            win = np.clip((hl - np.abs(P[:, :, 0] - ca)) / 0.012, 0, 1)
            exc = np.clip(P @ nrm_ - o, 0, None) * win
            P -= exc[..., None] * nrm_
        Rl = R0
        if i == turned:
            Rl = R0 @ rotm([0, 1, 0], [1.5 * D2R])[0]
        c = p + ndir * (th + 0.004) + np.array([0, rng.uniform(-0.008, 0.008), 0])
        if i in cracked:
            # an irregular crack across the slab: two pieces, 4 mm apart, matching fracture faces
            a_c = rng.uniform(-0.35, 0.35)
            nc = unit(np.array([math.cos(a_c), 0, math.sin(a_c)]))
            off = rng.uniform(-0.15, 0.15) * hx
            wob = 0.008 * np.sin(P[:, :, 2] * 23 + rng.uniform(0, 6)) + 0.004 * np.sin(P[:, :, 2] * 61)
            dd = P @ nc - off - wob
            for sg in (-1, 1):
                Q = P - (np.clip(sg * dd + 0.002, 0, None) * sg)[..., None] * nc
                P_b.add(xform(Q, Rl, c[None]), T, Pl=Q, mat="M_stone_dressed", smooth="bevel")
        else:
            P_b.add(xform(P, Rl, c[None]), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    log("buttress coping: %d slabs, cracked %s, turned %d" % (nsl, sorted(cracked), turned))
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
AP_ZE = 4.50 + DZ                  # bed height at the eave (4.62)
AP_RT = 1.60                       # top radius (tower foot)
AP_ZT = 6.00                       # tower foot: apron ~41 deg (art bible 35-45)
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
    """Shingle: x = length (butt at -L/2), y = thickness from 0 (bed) up, z = width."""
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


def shake_local(rng, L, W, tb=(0.025, 0.035), tt=0.008, comb=0.0):
    """Split shake (T_SHK2): x = length (butt at -L/2), y = thickness from the bed up, z = width.
    Thickness tapers from a 2.5-3.5 cm butt to a 0.8 cm head; split, tapered outline (each long edge
    wanders +-2 cm and the head is narrower); slight cup or crown; ragged, uneven butt."""
    N = len(L)
    T = T_SHK2
    h = np.stack([L / 2, np.full(N, 0.01), W / 2], 1)
    P = rbox(T, h, np.stack([np.full(N, 0.005), np.full(N, 0.003), np.full(N, 0.005)], 1))
    u = P[:, :, 0] / h[:, None, 0]               # -1 butt .. +1 head
    s = (u + 1) / 2                               # 0 butt .. 1 head
    vz = P[:, :, 2] / h[:, None, 2]               # -1 .. 1 across
    tbv = rng.uniform(*tb, N)
    th = tbv[:, None] + (tt - tbv)[:, None] * s
    P[:, :, 1] = (P[:, :, 1] / 0.01 + 1) / 2 * th
    # outline: head narrower, each edge wanders independently (split timber)
    taper = rng.uniform(0.0, 0.16, N)[:, None]
    e1 = rng.uniform(-0.02, 0.02, (N, 3))
    e2 = rng.uniform(-0.02, 0.02, (N, 3))
    def edge(e):
        return e[:, 0:1] * s + e[:, 1:2] * np.sin(s * PI) + e[:, 2:3] * np.sin(s * 2 * PI) * 0.5
    side = np.where(vz > 0, 1.0, -1.0)
    wid = (1 - taper * s) * np.abs(P[:, :, 2])
    # edges only ever wander inward (split timber never grows into its neighbour -> no interpenetration;
    # the widened gaps show the offset under-layer)
    off = -np.abs(np.where(vz > 0, edge(e1), edge(e2))) * np.clip(np.abs(vz), 0, 1)
    P[:, :, 2] = side * (wid + off)
    # ragged butt: piecewise steps across the width
    k = rng.uniform(-0.025, 0.02, (N, 4))
    zi = np.clip(((vz + 1) / 2 * 3.999).astype(int), 0, 3)
    jag = np.take_along_axis(k, zi, 1)
    P[:, :, 0] += jag * np.clip(1 - s * 2.5, 0, 1)
    if comb > 0:
        P[:, :, 0] += rng.uniform(-comb, comb * 0.4, N)[:, None] * s ** 3
    # cup / crown and a slight curl at the butt
    P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (vz ** 2 - 0.33) + \
        rng.uniform(0, 0.01, N)[:, None] * np.clip(1 - s * 3, 0, 1) ** 2
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
    P, T = lathe(np.array([[[1.40, 4.45 + DZ], [1.78, 4.45 + DZ], [1.78, 5.80], [1.40, 5.80]]]), 48)
    P_c.add(P, T, mat="M_mortar", smooth="none")
    # timber curb on the cornice (16 lapped segments, 0.22 x 0.24)
    n = 16
    rc = 2.30
    ph = np.arange(n) * 2 * PI / n + rng.uniform(-0.01, 0.01, n)
    a = np.stack([rc * np.sin(ph - PI / n - 0.05), -rc * np.cos(ph - PI / n - 0.05), np.full(n, 4.62 + DZ)], 1)
    b = np.stack([rc * np.sin(ph + PI / n + 0.05), -rc * np.cos(ph + PI / n + 0.05), np.full(n, 4.62 + DZ)], 1)
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
    # sarking: a closed board shell (2 cm) from the tower foot right out to the eave lip -> no see-through
    rs = np.linspace(1.55, AP_RE - 0.02, 9)
    zt_ = bed(rs) - 0.025 + apron_wave(0) * 0
    prof = np.concatenate([np.stack([rs, zt_], 1), np.stack([rs[::-1], zt_[::-1] - 0.022], 1)])[None]
    P, T = lathe(prof, 96, caps=False)
    T = dict(T)
    m_, nring = 96, prof.shape[1]
    # close the profile loop (outer eave edge and inner edge) by adding the last->first ring quads
    extra = np.array([[(nring - 1) * m_ + j, 0 * m_ + j, 0 * m_ + (j + 1) % m_, (nring - 1) * m_ + (j + 1) % m_]
                      for j in range(m_)], np.int64)
    T["quads"] = np.concatenate([T["quads"], extra])
    T["qflat"] = np.zeros(len(T["quads"]), bool)
    P_r.add(P, T, mat="M_timber", smooth="none")
    # eave fascia board under the lip
    a_ = np.linspace(0, 2 * PI, 97)[:-1]
    path = np.stack([(AP_RE - 0.03) * np.sin(a_), -(AP_RE - 0.03) * np.cos(a_), np.full(96, AP_ZE - 0.09)], 1)
    Pf, Tf = sweep(path[None], rect_prof(0.025, 0.12, 0.006), up=(0, 0, 1), closed=True)
    P_r.add(Pf, Tf, mat="M_timber", smooth="bevel")
    # shakes: 3 visible courses, each double layered (offset under-layer), long split shakes.
    # Lift per layer is a fixed offset normal to the bed (no per-shake pitch blow-up), the under-layer is
    # complete, and only isolated top-layer shakes are missing (exposing the under-layer).
    slope_len = (AP_RE - AP_RT) / ca
    courses = [0.0, 0.68, 1.36]          # 3 courses of 0.72-0.84 m shakes over the 2.09 m slope (41 deg)
    stats = 0
    for ci, sb in enumerate(courses):
        rb_ = AP_RE - sb * ca
        C = 2 * PI * rb_
        for layer in (0, 1):
            widths, gaps = [], []
            tot = 0
            while tot < C:
                widths.append(rng.uniform(0.14, 0.22))
                gaps.append(rng.uniform(0.005, 0.015))
                tot += widths[-1] + gaps[-1]
            widths = np.array(widths) * C / tot
            gaps = np.array(gaps) * C / tot
            # centres include every gap -> the ring closes evenly (no leftover hole at azimuth 0)
            phc = (np.cumsum(widths + gaps) - gaps - widths / 2) / C * 2 * PI + \
                (0.5 * widths.mean() / rb_ if layer == 0 else 0) + ci * 0.37
            phc += rng.uniform(-0.004, 0.004, len(phc))
            N = len(phc)
            if ci < 2:
                L = rng.uniform(0.74, 0.84, N)
                comb = 0.0
            else:
                # top course: reach the tower face (octagon) with a ragged comb top
                a_t = 1.55 + 0.03
                rel = (phc + PI / 8) % (PI / 4) - PI / 8
                r_face = a_t / np.cos(rel) + 0.012
                L = np.clip((rb_ - r_face) / ca + rng.uniform(-0.01, 0.06, N), 0.3, None)
                comb = 0.04
            sbb = sb - (0.04 if layer == 0 else 0.0) + rng.uniform(-0.02, 0.02, N)
            W = widths * rng.uniform(0.93, 1.0, N)
            P = shake_local(rng, L, W, comb=comb)
            if layer == 1:
                drop = rng.random(N) < 0.025
                drop &= ~np.roll(drop, 1)
            else:
                drop = np.zeros(N, bool)
            keep = ~drop
            # lift: courses below + under-layer thickness (butt) -> straight plane, slight pitch only
            ob = 0.004 + (0.028 if ci > 0 else 0.0) + (0.033 if layer == 1 else 0.0)
            ot = 0.002 + (0.009 if layer == 1 else 0.0)
            beta = np.arctan2(ob - ot, np.maximum(L, 0.6)) + rng.uniform(-0.004, 0.008, N)
            Rf, er, nrm = cone_frame(phc, AP_A)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rng.normal(0, 2.0 * D2R, N))
            sc = sbb + L / 2
            wave = apron_wave(phc) * np.clip(1 - sc / 2.0, 0, 1)
            ctr = er * (AP_RE - sc * ca)[:, None] + np.stack([0 * sc, 0 * sc, AP_ZE + sc * sa + wave], 1) \
                + nrm * ((ob + ot) / 2 + rng.uniform(-0.002, 0.004, N))[:, None]
            Wd = xform(P, Rf @ Rl, ctr)
            P_s.add(Wd[keep], T_SHK2, Pl=P[keep], mat="M_roof_shake", smooth="bevel")
            stats += keep.sum()
    log("apron shakes", stats)


# =============================================================================================
# D. OCTAGONAL TIMBER SMOCK TOWER
# =============================================================================================
TW_Z0, TW_Z1 = 5.95, 11.45               # timber tower 5.95 -> 11.45 m (round 3: +0.45..0.5 m, per ref1)
TW_A0, TW_A1 = 1.55, 0.95                # half across-flats at the foot / at the top
TW_TAPER = (TW_A0 - TW_A1) / (TW_Z1 - TW_Z0)
TAN225 = math.tan(PI / 8)
COS225 = math.cos(PI / 8)
LEAN_DIR = unit(np.array([-0.95, 0.31, 0.0]))
LEAN_ANG = 0.55 * D2R
LEAN_PIVOT = np.array([0, 0, 5.80])
LEAN_R = rotm(np.cross([0, 0, 1.0], LEAN_DIR), [LEAN_ANG])[0]
CURB_R, CURB_W, CURB_D = 0.99, 0.22, 0.24     # circular top curb (8 lapped segments) on the octagon
ZCT = TW_Z1 + 0.01                            # curb top
Z_COLLAR = 10.30                              # iron prop collar


def lean(V):
    return (V - LEAN_PIVOT) @ LEAN_R.T + LEAN_PIVOT


def TZ(z_old):
    """Map round-1 tower heights (5.40 .. 10.55) onto the taller tower."""
    return TW_Z0 + (np.asarray(z_old, float) - 5.40) * (TW_Z1 - TW_Z0) / (10.55 - 5.40)


def tw_a(z):
    return TW_A0 - (np.asarray(z, float) - TW_Z0) * TW_TAPER


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


def post_geom(z):
    """Corner post centre radius (along the bisector) at height z (posts are 0.2 x 0.2)."""
    return (tw_a(z) + 0.03) / COS225 + 0.02 - 0.10


def build_tower(parts):
    P_b, P_f, P_i = parts["tower_boards"], parts["tower_frame"], parts["tower_iron"]
    rng = RNG("tower")
    lifts = [(float(TZ(5.52)), float(TZ(7.24))), (float(TZ(7.20)), float(TZ(9.04))), (float(TZ(9.0)), float(TZ(10.36)))]
    hatch = dict(k=0, l=0.28, z0=float(TZ(7.68)), z1=float(TZ(8.34)))
    # age: split board ends (3) and one patched board, on faces seen from the front / hero cameras
    splits = {(7, 0), (1, 0), (6, 1)}
    patch_at = (7, 1)
    nb_total = 0
    patches = []
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
            isplit = int(rng.integers(0, N)) if (k, li) in splits else -1
            ipatch = int(rng.integers(1, N - 1)) if (k, li) == patch_at else -1
            pieces = []   # (lateral centre, width, z bottom, z top, extra skew deg)
            for i in range(N):
                zb = z0 + rng.uniform(-0.025, 0.01)
                zt = z1 + rng.uniform(-0.01, 0.015)
                if k == hatch["k"] and li == 1 and abs(lc[i]) - ws[i] / 2 < hatch["l"] + 0.02:
                    pieces.append((lc[i], ws[i], zb, hatch["z0"] - 0.04, 0.0))
                    pieces.append((lc[i], ws[i], hatch["z1"] + 0.06, zt, 0.0))
                elif i == isplit:
                    # split end: the bottom 0.26 m is cracked into two halves, one sprung outward/sideways
                    zs_ = zb + 0.26
                    pieces.append((lc[i], ws[i], zs_ - 0.004, zt, 0.0))
                    hw2 = ws[i] / 2 - 0.004
                    pieces.append((lc[i] - ws[i] / 4 - 0.002, hw2, zb, zs_ + 0.01, 0.0))
                    pieces.append((lc[i] + ws[i] / 4 + 0.004, hw2, zb + 0.015, zs_ + 0.01, 2.2))
                else:
                    pieces.append((lc[i], ws[i], zb, zt, 0.0))
                if i == ipatch:
                    zp = zm + rng.uniform(-0.3, 0.1)
                    patches.append((k, lc[i], ws[i] + 0.03, zp - 0.28, zp + 0.28))
            pc = np.array(pieces)
            N = len(pc)
            Lz = pc[:, 3] - pc[:, 2]
            h = np.stack([Lz / 2, np.full(N, 0.015), pc[:, 1] / 2], 1)
            P = rbox(T_BRD, h, np.stack([np.full(N, 0.006), np.full(N, 0.006), np.full(N, 0.008)], 1))
            u = P[:, :, 0] / h[:, None, 0]
            # cup, bow, loose boards
            P[:, :, 1] += rng.uniform(-0.004, 0.004, N)[:, None] * (P[:, :, 2] / h[:, None, 2]) ** 2
            P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (1 - u ** 2)
            loose = rng.random(N) < 0.05
            # each board leans up to +-0.5 deg, a few loose ones up to 1 deg
            skew = (np.where(loose, rng.uniform(-1.0, 1.0, N), np.clip(rng.normal(0, 0.3, N), -0.5, 0.5))
                    + pc[:, 4]) * D2R
            yoff = 0.015 + np.where(loose, rng.uniform(0.006, 0.014, N), rng.uniform(-0.002, 0.003, N))
            yoff = yoff + np.where(pc[:, 4] > 0, 0.012, 0.0)
            zc = (pc[:, 2] + pc[:, 3]) / 2
            zz = zc[:, None] + P[:, :, 0]
            # split halves spring outward toward their free end
            sprung = (pc[:, 4] > 0)[:, None] * np.clip((pc[:, 2:3] + 0.27 - zz) / 0.27, 0, 1) * 0.012
            ll = pc[:, 0][:, None] + P[:, :, 2] + skew[:, None] * P[:, :, 0]
            scale = (tw_a(zz) + 0.03) / (float(tw_a(zm)) + 0.03)
            yy = yoff[:, None] + P[:, :, 1] + sprung
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
    # patched board: a short plank nailed over a rotten one
    for (k, l0, w, zb, zt) in patches:
        n, t = face_axes(k)
        pa = face_map(k, np.array([l0 + 0.01]), np.array([zb]), np.array([0.058]))
        pb = face_map(k, np.array([l0 - 0.01]), np.array([zt]), np.array([0.058]))
        member(P_b, "M_timber_weathered", pa, pb, w, 0.022, up=n, c=0.005, rng=rng, bow=0.003)
        nl_ = np.array([[l0 - w * 0.3, zb + 0.06], [l0 + w * 0.3, zb + 0.07], [l0 - w * 0.28, zt - 0.06],
                        [l0 + w * 0.3, zt - 0.07]])
        prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
        Pn, Tn = lathe(np.repeat(prof[None], 4, 0), 6)
        Rn = np.repeat(frame_mats(t[None], np.cross(n, t)[None], n[None]), 4, 0)
        P_i.add(xform(Pn, Rn, face_map(k, nl_[:, 0], nl_[:, 1], np.full(4, 0.069))), Tn, mat="M_iron", smooth="all")
    # corner (cant) posts, proud of the boards
    for k in range(8):
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        za, zb = TW_Z0 - 0.1, ZCT - CURB_D - 0.005
        a = bis * float(post_geom(za)) + np.array([0, 0, za])
        b = bis * float(post_geom(zb)) + np.array([0, 0, zb])
        member(P_f, "M_timber", a[None], b[None], 0.2, 0.2, up=bis, c=0.025, rng=rng, bow=0.01)

    # sill beams, rails with drip boards
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
    ring_members(float(TZ(5.41)), -0.03, 0.24, 0.24, 0.06, "M_timber", P_f, cc=0.02, bow=0.008)  # sill
    for zr in (float(TZ(7.22)), float(TZ(9.02))):
        ring_members(zr, 0.075, 0.05, 0.11, -0.10, "M_timber", P_f, cc=0.01)       # rail (girt)
        # drip board on the rail, sloping outward, projecting 4 cm
        for k in range(8):
            n, t = face_axes(k)
            hw = (float(tw_a(zr + 0.07)) + 0.03) * TAN225 - 0.10
            ctr = face_map(k, np.array([0.0]), np.array([zr + 0.075]), np.array([0.09]))[0]
            xa = t
            ya = unit(np.array([0, 0, 1.0]) + n * 0.28)
            za = np.cross(xa, ya)
            blocks_world(P_f, "M_timber", ctr[None], frame_mats(xa[None], ya[None], za[None]),
                         [[hw, 0.011, 0.055]], c=0.004, T=T_PLK)
    # ---- top curb: circular, 8 timber segments joined by half-laps, two oak pegs per joint ----
    lap = 0.13 / CURB_R
    gap = 0.004 / CURB_R
    th_j = np.arange(8) * PI / 4 + 0.17 + rng.uniform(-0.05, 0.05, 8)
    dz_s = rng.uniform(-0.004, 0.004, 8)
    dr_s = rng.uniform(-0.005, 0.005, 8)

    def arc_piece(t0, t1, zc_, hd, rr):
        n = max(3, int((t1 - t0) * rr / 0.08) + 1)
        tt = np.linspace(t0, t1, n)
        path = np.stack([rr * np.sin(tt), -rr * np.cos(tt), np.full(n, zc_)], 1)[None]
        Pp, Tp = sweep(path, rect_prof(CURB_W, hd, 0.018 if hd > 0.15 else 0.01), up=(0, 0, 1))
        P_f.add(Pp, Tp, mat="M_timber", smooth="bevel")
    D = CURB_D
    for j in range(8):
        t0, t1 = th_j[j], th_j[(j + 1) % 8] + (2 * PI if j == 7 else 0)
        rr = CURB_R + dr_s[j]
        zt = ZCT + dz_s[j]
        arc_piece(t0 + lap + gap, t1 - lap - gap, zt - D / 2, D, rr)          # full section
        arc_piece(t1 - lap - gap * 0.5, t1 + lap, zt - D / 4, D / 2 - 0.003, rr)   # top half over the next joint
        arc_piece(t0 - lap, t0 + lap + gap * 0.5, zt - 3 * D / 4, D / 2 - 0.003, rr)  # bottom half under the joint
    pegs = []
    for j in range(8):
        for o in (-0.5, 0.5):
            tq = th_j[j] + o * lap * 0.9
            pegs.append([CURB_R * math.sin(tq), -CURB_R * math.cos(tq), ZCT + dz_s[j - 1] - 0.003])
    prof = np.array([(0.0, 0.0), (0.014, 0.0), (0.014, 0.012), (0.011, 0.018), (0.0, 0.019)])
    Pg, Tg = lathe(np.repeat(prof[None], len(pegs), 0), 8)
    P_f.add(Pg + np.array(pegs)[:, None, :], Tg, mat="M_timber", smooth="all")
    # ---- iron prop collar: flat strap 60 x 10 mm lying on the boards, following the octagon and
    # stepping out over the corner posts, with bolts ----
    zc = Z_COLLAR
    a_ = float(tw_a(zc))
    pts = []
    bolts = []
    for k in range(8):
        n, t = face_axes(k)
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        tang = np.array([math.cos(phi), math.sin(phi), 0.0])
        c = bis * float(post_geom(zc)) + np.array([0, 0, zc])
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
            bolts.append((face_map(k, np.array([l]), np.array([zc]), np.array([0.063]))[0], n, t))
    path = np.array(pts)[None]
    Pc, Tc = sweep(path, rect_prof(0.010, 0.060, 0.002), up=(0, 0, 1), closed=True)
    P_i.add(Pc, Tc, mat="M_iron", smooth="bevel")
    prof = np.array([(0.0, 0.0), (0.019, 0.0), (0.019, 0.008), (0.012, 0.013), (0.0, 0.014)])
    Pb_, Tb_ = lathe(np.repeat(prof[None], len(bolts), 0), 6)
    Rb = np.array([frame_mats(t[None], np.cross(n, t)[None], n[None])[0] for (_, n, t) in bolts])
    P_i.add(xform(Pb_, Rb, np.array([b[0] for b in bolts])), Tb_, mat="M_iron", smooth="none")
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
    for s in (-0.16, 0.16):
        tmp = Part("tmp", ["M_iron"]); Part.registry.pop()
        member(tmp, "M_iron", fm(s, z1 + 0.03, 0.108), fm(s, z0 + 0.05, 0.108), 0.04, 0.006, up=n, c=0.002)
        P_i.add(shutter(tmp.V[0])[None], T_PLK, mat="M_iron", smooth="none")
    # prop stick from the sill to the shutter's lower edge
    low = shutter(fm(0.18, z0 - 0.01, 0.09))[0]
    member(P_f, "M_timber", fm(0.18, z0 - 0.02, 0.07), low[None], 0.035, 0.035, up=n, c=0.008)
    # interior deck under the hatch (dark interior)
    zd = float(TZ(7.66))
    ang8 = np.arange(9) * PI / 4 - PI / 8
    rr = (float(tw_a(zd)) - 0.02) / COS225
    ring = np.stack([rr * np.sin(ang8), -rr * np.cos(ang8), np.full(9, zd)], 1)
    ctr = np.repeat([[0, 0, zd]], 9, 0)
    add_grid(P_f, "M_timber", np.stack([ctr, ring], 1), flip=False)


# =============================================================================================
# E. CAP: low hipped cap, short ridge along the windshaft, bell-cast eaves, a gablet hood over the shaft
#    neck with proper lead-lined valleys, a board skirt (valance) hanging outside the curb, and cast-iron
#    truck wheels on the curb.                       cap-local: X' = heading, Y', Z
# =============================================================================================
CAP_AZ = 3 * D2R                 # round 3: hub ~0.1 m right of the tower axis in the front view (ref1)
HDIR = np.array([math.sin(CAP_AZ), -math.cos(CAP_AZ), 0.0])
YDIR = np.cross([0, 0, 1.0], HDIR)
CAP_AF, CAP_AB, CAP_B = 1.28, 1.48, 1.28          # footprint 2.76 x 2.56 m
CAP_XC = (CAP_AF - CAP_AB) / 2
RIDGE_L = 1.0
XR0, XR1 = CAP_XC - RIDGE_L / 2, CAP_XC + RIDGE_L / 2
CAP_EF, CAP_EB, CAP_SB = CAP_AF - XR1, CAP_AB + XR0, CAP_B   # horizontal runs: front / back / sides
CAP_ZE = ZCT + 0.24                                # eave lip (11.70)
CAP_RISE = 1.18                                    # eave -> ridge (ridge 12.88)
HUB_D, TILT = 1.95, 8 * D2R
HUB_Z = CAP_ZE + 0.66                              # 12.36
HOOD_XF, HOOD_YW = 1.15, 0.45
HOOD_ZE, HOOD_ZR = CAP_ZE + 0.62, CAP_ZE + 1.06
SKIRT_R = CURB_R + CURB_W / 2 + 0.012              # inner face of the valance boards (gap to curb ~1-2 cm)


def _cap_profile():
    ds = np.linspace(0, CAP_SB, 800)

    def h_for(tmax):
        th = (25 + (tmax - 25) * smoothstep(0.0, 0.45, ds)) * D2R
        return np.concatenate([[0], np.cumsum(np.tan(th[1:]) * np.diff(ds))])
    lo, hi = 25.0, 85.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if h_for(mid)[-1] < CAP_RISE:
            lo = mid
        else:
            hi = mid
    return ds, h_for(lo), lo


CAP_DS, CAP_HS, CAP_TMAX = _cap_profile()


def cap_h(t):
    """Height above the eave at normalised hip coordinate t (0 eave .. 1 ridge)."""
    d = np.asarray(t, float) * CAP_SB
    return np.where(d < 0, d * math.tan(25 * D2R), np.interp(d, CAP_DS, CAP_HS))


def cap_dh(t):
    """d(height)/dt."""
    t = np.asarray(t, float)
    return (cap_h(t + 1e-3) - cap_h(t - 1e-3)) / 2e-3


def cap_t(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return np.minimum(np.minimum((CAP_B - np.abs(y)) / CAP_SB, (CAP_AF - x) / CAP_EF), (CAP_AB + x) / CAP_EB)


def cap_z(x, y):
    return CAP_ZE + cap_h(np.minimum(cap_t(x, y), 1.0))


def hood_z(y):
    return HOOD_ZR - (HOOD_ZR - HOOD_ZE) * np.abs(y) / (HOOD_YW + 0.03)


def _valley_table():
    ys = np.linspace(0, HOOD_YW + 0.06, 40)
    xv = []
    for y in ys:
        lo, hi = XR0, HOOD_XF + 0.2
        assert cap_z(lo, y) > hood_z(y) and cap_z(hi, y) < hood_z(y), "hood does not meet the cap roof"
        for _ in range(50):
            m = (lo + hi) / 2
            if cap_z(m, y) > hood_z(y):
                lo = m
            else:
                hi = m
        xv.append((lo + hi) / 2)
    return ys, np.array(xv)


VAL_Y, VAL_X = _valley_table()


def x_valley(y):
    return np.interp(np.abs(np.asarray(y, float)), VAL_Y, VAL_X)


def capw(P):
    """cap-local (x', y', z) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return P[..., 0:1] * HDIR + P[..., 1:2] * YDIR + P[..., 2:3] * np.array([0, 0, 1.0])


def cap_member(part, mat, a, b, w, d, up=(0, 0, 1), **kw):
    upw = capw(np.asarray(up, float)[None])[0]
    return member(part, mat, capw(np.atleast_2d(a)), capw(np.atleast_2d(b)), w, d, up=upw, **kw)


_SHK_TOP = np.nonzero(T_SHK["idx"][:, 1] == T_SHK["n"][1] - 1)[0]


def sliver_keep(W0, Wl, tt, ee, min_w=0.05):
    """Shingles altered by hip / valley clamping keep only if the clamped outline is still >= 5 cm wide
    (minimum caliper width of its top face) -> no thin triangular slivers at hips and valleys."""
    N = len(Wl)
    keep = np.ones(N, bool)
    moved = np.abs(Wl - W0).max(axis=(1, 2)) > 0.002
    tt = np.broadcast_to(tt, (N, 3))
    ee = np.broadcast_to(ee, (N, 3))
    for q in np.nonzero(moved)[0]:
        V = Wl[q, _SHK_TOP]
        pts = np.stack([V @ tt[q], V @ ee[q]], 1)
        h = hull2d(pts)
        if len(h) < 3:
            keep[q] = False
            continue
        best = 1e9
        for j in range(len(h)):
            e = h[(j + 1) % len(h)] - h[j]
            ln = np.linalg.norm(e)
            if ln < 1e-6:
                continue
            nrm = np.array([-e[1], e[0]]) / ln
            best = min(best, np.abs((h - h[j]) @ nrm).max())
        keep[q] = best >= min_w
    return keep


class HeightField:
    """Max-height field over cap-local (x, y) built from mesh samples (1.5 cm cells)."""

    def __init__(self, Vloc, cell=0.015):
        self.c = cell
        self.x0, self.y0 = Vloc[:, 0].min() - 0.1, Vloc[:, 1].min() - 0.1
        nx = int((Vloc[:, 0].max() + 0.1 - self.x0) / cell) + 1
        ny = int((Vloc[:, 1].max() + 0.1 - self.y0) / cell) + 1
        self.H = np.full((nx, ny), -1e9)
        self.add(Vloc)

    def add(self, Vloc):
        i = ((Vloc[:, 0] - self.x0) / self.c).astype(int)
        j = ((Vloc[:, 1] - self.y0) / self.c).astype(int)
        ok = (i >= 0) & (i < self.H.shape[0]) & (j >= 0) & (j < self.H.shape[1])
        np.maximum.at(self.H, (i[ok], j[ok]), Vloc[ok, 2])

    def __call__(self, x, y, r=1):
        i = ((np.asarray(x) - self.x0) / self.c).astype(int)
        j = ((np.asarray(y) - self.y0) / self.c).astype(int)
        out = np.full(np.shape(i), -1e9)
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                ii = np.clip(i + di, 0, self.H.shape[0] - 1)
                jj = np.clip(j + dj, 0, self.H.shape[1] - 1)
                out = np.maximum(out, self.H[ii, jj])
        return out


def to_cap_local(V):
    V = np.asarray(V)
    return np.stack([V @ HDIR, V @ YDIR, V[:, 2]], 1)


def slab_along(part, mat, A, E, Nn, w, t, c=0.004, T_cache={}):
    """Board lying along polyline A (n,3): width w toward E (n,3), thickness t toward Nn (n,3).
    Profile chamfered; caps at both ends."""
    A = np.asarray(A, float)
    n = len(A)
    w = np.broadcast_to(np.asarray(w, float), (n,))
    wm = float(w.min())
    prof = rect_prof(wm, t, c)                                  # centred (x across, y thickness)
    px = (prof[None, :, 0] + wm / 2) / wm * w[:, None]          # per-station width (tapered boards)
    P = A[:, None, :] + px[..., None] * E[:, None, :] + (prof[None, :, 1:2] + t / 2) * Nn[:, None, :]
    P = P.reshape(1, -1, 3)
    key = (n, len(prof))
    T = tmpl_rings(n, len(prof), cap0=True, cap1=True)
    P = add_caps(P, T)
    T = orient(T, P[0])
    part.add(P, T, mat=mat, smooth="bevel")
    return P[0]


def build_cap_cappings(P_sh, P_fr, P_ir, rng):
    """Continuous V ridge capping, lapped V hip cappings (0.6-0.9 m lengths following the bell-cast hip line),
    lead hip-end saddles where hips meet the ridge, hood ridge capping and the knob on a square plinth.
    The boards sit 5 cm above the roof surface; shingle courses under each board's footprint are dressed
    down under it (so every board bears on the shingles)."""
    TB, WL = 0.025, 0.165
    SEAT = 0.050                              # board bottom above the roof surface (shingle butts ~5 cm)
    Z3 = np.array([0, 0, 1.0])
    T_SAD = 0.90

    def hip_xy(fx, sy, t):
        t = np.asarray(t, float)
        x = (CAP_AF - t * CAP_EF) if fx == 0 else (-CAP_AB + t * CAP_EB)
        return x, sy * (CAP_B - t * CAP_SB)
    gaps, devs = [], []
    bottoms = []                              # underside sample points of every capping board
    groups = []

    def v_cap(apex, eA, nA, wA, eB, nB, wB):
        """two leaves meeting at the apex line; leaf B laps over leaf A's top edge"""
        out = []
        for (e, nn, w, over) in ((eA, nA, wA, False), (eB, nB, wB, True)):
            base = apex - (e * 0.022 if over else 0) + (nn * 0.010 if over else 0)
            ww = w + (0.022 if over else 0)
            out.append(slab_along(P_fr, "M_timber_weathered", capw(base), capw(e), capw(nn), ww, TB))
            grp = np.array([base + e * (f * ww)[:, None] for f in np.linspace(0, 1, 14)])
            bottoms.extend(list(grp))
            groups.append(grp)
        return out

    caps_V = []
    # ---------------- hips ----------------
    for fx in (0, 1):
        Rend = CAP_EF if fx == 0 else CAP_EB
        oE = np.array([1.0 if fx == 0 else -1.0, 0, 0])
        for sy in (-1, 1):
            oS = np.array([0, float(sy), 0])

            def Hf(t):
                x, y = hip_xy(fx, sy, t)
                return np.stack([x, y, CAP_ZE + cap_h(np.asarray(t, float))], -1)
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
                se = np.arctan(cap_dh(np.maximum(t, 0)) / Rend)
                sS = np.arctan(cap_dh(np.maximum(t, 0)) / CAP_SB)
                nE = np.sin(se)[:, None] * oE + np.cos(se)[:, None] * Z3
                nS = np.sin(sS)[:, None] * oS + np.cos(sS)[:, None] * Z3
                eE = unit(np.cross(nE, Tg))
                eE *= np.where((eE @ np.array([0, -sy, 0])) > 0, 1.0, -1.0)[:, None]
                eS = unit(np.cross(nS, Tg))
                eS *= np.where((eS @ -oE) > 0, 1.0, -1.0)[:, None]
                wE = np.minimum(WL, np.abs(H[:, 1]) / np.maximum(np.abs(eE[:, 1]), 1e-3) - 0.004)
                if fx == 0:     # front hips: the end-face leaf is cut to fit against the hood cheek
                    far = H + eE * wE[:, None]
                    near_hood = far[:, 0] > float(x_valley(HOOD_YW)) - 0.12
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
    sg = CAP_TMAX * D2R
    xr = np.linspace(XR0 + 0.03, XR1 - 0.03, 12)
    H = np.stack([xr, 0 * xr, np.full(12, CAP_ZE + CAP_RISE)], 1)
    eA = np.repeat([[0, -math.cos(sg), -math.sin(sg)]], 12, 0)
    nA = np.repeat([[0, -math.sin(sg), math.cos(sg)]], 12, 0)
    eB = np.repeat([[0, math.cos(sg), -math.sin(sg)]], 12, 0)
    nB = np.repeat([[0, math.sin(sg), math.cos(sg)]], 12, 0)
    wR = np.full(12, 0.165)
    ridge_apex = H + Z3 * (SEAT + lowfreq(xr, rng, 0.003))[:, None]
    caps_V.append(v_cap(ridge_apex, eA, nA, wR, eB, nB, wR))
    # ---------------- hood ridge ----------------
    sl = math.atan2(HOOD_ZR - HOOD_ZE, HOOD_YW + 0.03)
    xh = np.linspace(float(x_valley(0.0)) + 0.03, HOOD_XF + 0.05, 8)
    H = np.stack([xh, 0 * xh, np.full(8, HOOD_ZR)], 1)
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
        Vl = to_cap_local(Vw)
        Vw = Vw.copy()
        Vw[:, 2] = np.minimum(Vw[:, 2], bf(Vl[:, 0], Vl[:, 1]) - 0.003)
        return Vw
    P_sh.V = [press(V) for V in P_sh.V]
    HF = HeightField(to_cap_local(part_samples(P_sh, 0.02)))
    st_gap = []
    for grp in groups:                         # per station: smallest gap across the board's width
        gg = grp[1:-1, :, 2] - HF(grp[1:-1, :, 0].ravel(), grp[1:-1, :, 1].ravel(), r=0).reshape(grp[1:-1, :, 2].shape)
        gg = np.where(np.abs(gg) < 1.0, gg, np.nan)
        st_gap.extend(list(np.nanmin(gg, 0)))
    g = np.array(st_gap)
    g = g[np.isfinite(g)]
    log("CAP cappings: %d hip pieces (%.2f-%.2f m), max deviation from hip line %.2f deg; bearing gap per "
        "station (board underside to highest shingle under it): median %.3f, 90%% %.3f m, 1%% %.3f" % (len(devs), np.diff(cuts).min(), np.diff(cuts).max(),
                                                             max(devs), np.median(g), np.percentile(g, 90), np.percentile(g, 1)))
    # ---------------- lead hip-end saddles over the ridge ends ----------------
    apex_z = {}
    for fx in (0, 1):
        Rend = CAP_EF if fx == 0 else CAP_EB
        xin = (XR1 - 0.11) if fx == 0 else (XR0 + 0.11)
        rows = []
        for t in np.linspace(0.85, 1.0, 9):
            xh_ = (CAP_AF - t * CAP_EF) if fx == 0 else (-CAP_AB + t * CAP_EB)
            yh = CAP_B - t * CAP_SB
            pts = np.array([[xin, yh], [xh_, yh], [xh_, -yh], [xin, -yh]])
            seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
            acc = np.concatenate([[0], np.cumsum(seg)])
            u = np.linspace(0, acc[-1], 31)
            xy = np.stack([np.interp(u, acc, pts[:, 0]), np.interp(u, acc, pts[:, 1])], 1)
            z = np.maximum(HF(xy[:, 0], xy[:, 1], r=2), cap_z(xy[:, 0], xy[:, 1]) + 0.03)
            z = np.convolve(np.pad(z, 2, mode="edge"), np.ones(5) / 5, mode="valid")
            z = np.maximum(z, HF(xy[:, 0], xy[:, 1], r=1)) + 0.004
            rows.append(np.stack([xy[:, 0], xy[:, 1], z], 1))
        G = np.array(rows)
        apex_z[fx] = float(G[-1, :, 2].max())
        Gb = G - np.array([0, 0, 0.004])
        fl = fx == 1
        add_grid(P_ir, "M_lead", capw(G), flip=not fl)
        add_grid(P_ir, "M_lead", capw(Gb), flip=fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[0], G[0]], 0)), flip=fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[:, 0], G[:, 0]], 1)), flip=not fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[:, -1], G[:, -1]], 1)), flip=fl)
    # ---------------- lead aprons beside the hood cheeks (main front face, cheek -> hip capping) -----------
    x_up = float(x_valley(HOOD_YW)) - 0.14
    for sy in (-1, 1):
        xs_ = np.linspace(x_up, HOOD_XF + 0.10, 16)
        rows = []
        for x in xs_:
            t_h = (CAP_AF - x) / CAP_EF
            y_hip = CAP_B - t_h * CAP_SB
            ys_ = np.linspace(0.437, max(y_hip - 0.03, 0.47), 8)
            zsurf = cap_z(np.full(8, x), ys_)
            ramp = np.clip((x - x_up) / 0.10, 0, 1)
            z = zsurf + 0.012 + (SEAT - 0.006 - 0.012) * ramp
            if x > HOOD_XF - 0.03:      # dressed over the eave course below the hood front
                z = np.maximum(z, HF(np.full(8, x), sy * ys_, r=1) + 0.004)
            rows.append(np.stack([np.full(8, x), sy * ys_, z], 1))
        G = np.array(rows)
        Gb = G - np.array([0, 0, 0.004])
        fl = sy < 0
        add_grid(P_ir, "M_lead", capw(G), flip=fl)
        add_grid(P_ir, "M_lead", capw(Gb), flip=not fl)
        for edge in (G[0], G[-1]):
            pass
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[0], G[0]], 0)), flip=not fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[-1], G[-1]], 0)), flip=fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[:, 0], G[:, 0]], 1)), flip=fl)
        add_grid(P_ir, "M_lead", capw(np.stack([Gb[:, -1], G[:, -1]], 1)), flip=not fl)
    # ---------------- knob on a square plinth at the rear ridge end ----------------
    zp = apex_z[1] - 0.03
    blocks_world(P_fr, "M_timber", capw(np.array([[XR0 + 0.02, 0.0, zp + 0.04]])),
                 frame_mats(capw(np.array([[1.0, 0, 0]])), capw(np.array([[0, 1.0, 0]])), np.array([[0, 0, 1.0]])),
                 [[0.075, 0.075, 0.04]], c=0.008, T=T_BLK)
    prof = np.array([(0.0, 0.0), (0.06, 0.0), (0.062, 0.015), (0.045, 0.035), (0.04, 0.055), (0.065, 0.10),
                     (0.067, 0.13), (0.047, 0.18), (0.02, 0.225), (0.0, 0.24)])
    P, T = lathe(prof[None], 16)
    P = xform(P, euler([0.8 * D2R], [-1.2 * D2R], [0.0]), capw(np.array([[XR0 + 0.02, 0.0, zp + 0.08]])))
    P_fr.add(P, T, mat="M_timber", smooth="all")


def build_cap(parts):
    P_sh, P_fr, P_ir = parts["cap_shingles"], parts["cap_frame"], parts["cap_iron"]
    rng = RNG("cap")
    log("cap: side max pitch %.1f deg (bell-cast to 25), end faces %.1f deg; ridge %.2f m long at z %.2f; "
        "valley x %.2f..%.2f" % (CAP_TMAX, math.atan(math.tan(CAP_TMAX * D2R) * CAP_SB / CAP_EF) / D2R, RIDGE_L,
                                 CAP_ZE + CAP_RISE, VAL_X[0], VAL_X[-1]))
    deck_under = lambda x, y: cap_z(x, y) - 0.047
    # ---- frame: sheers + cross beams carried on four truck wheels ----
    ZW = ZCT + 0.10                    # wheel axle (wheel dia 0.20 rolls on the curb top)
    ZSH = ZCT + 0.30                   # sheer centre (0.20 deep: bottom rests on the wheel tops)
    YS = 0.78
    # sheers: ends project ~11 cm past the valance face through notched gaps, splayed (chamfered) ends with an
    # end check (a split running in from the end grain and along the top for ~0.3 m)
    T_SHR = tmpl_box(9, 7, 5)
    SH_X = (-0.995, 0.972)
    for s in (-1, 1):
        x0, x1 = SH_X[0] + rng.uniform(-0.01, 0.01), SH_X[1] + rng.uniform(-0.01, 0.01)
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
        P_fr.add(capw(Pc), T_SHR, Pl=P, mat="M_timber", smooth="bevel")
    for xx in (-0.50, 0.50):            # cross beams lapped into the sheers, ends inside the valance ring
        cap_member(P_fr, "M_timber", [xx, -YS - 0.075, ZSH + 0.01], [xx, YS + 0.075, ZSH + 0.01], 0.15, 0.17,
                   c=0.018)
    # ---- cast-iron truck wheels (dia 0.20) with axle brackets hung from the sheers ----
    xw = math.sqrt(CURB_R ** 2 - YS ** 2)
    wprof = np.array([(0.0, -0.042), (0.034, -0.042), (0.036, -0.014), (0.078, -0.009), (0.084, -0.026),
                      (0.096, -0.026), (0.100, -0.021), (0.100, 0.021), (0.096, 0.026), (0.084, 0.026),
                      (0.078, 0.009), (0.036, 0.014), (0.034, 0.042), (0.0, 0.042)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = capw(np.array([[sx * xw, sy * YS, ZW]]))[0]
            rad = unit(np.array([c[0], c[1], 0.0]))
            tan = np.cross([0, 0, 1.0], rad)
            Rw = frame_mats(tan[None], np.array([[0, 0, 1.0]]), rad[None])
            Pw, Tw = lathe(wprof[None], 20)
            P_ir.add(xform(Pw, Rw, c), Tw, mat="M_iron", smooth="bevel")
            # axle pin with nuts
            Pa, Ta = lathe(np.array([[(0.0, -0.075), (0.013, -0.075), (0.013, 0.075), (0.0, 0.075)]]), 10)
            P_ir.add(xform(Pa, Rw, c), Ta, mat="M_iron", smooth="bevel")
            for o in (-1, 1):
                # bracket cheek: flat iron plate (60 x 10) hanging from the sheer, broad face normal = axle
                a_ = c + rad * o * 0.058 + np.array([0, 0, ZSH - 0.10 - ZW + 0.005])
                b_ = c + rad * o * 0.058 + np.array([0, 0, -0.04])
                member(P_ir, "M_iron", a_[None], b_[None], 0.06, 0.010, up=rad, c=0.002)
                Pn, Tn = lathe(np.array([[(0.0, 0.0), (0.024, 0.0), (0.024, 0.014), (0.0, 0.016)]]), 6)
                Rn = frame_mats(tan[None], np.array([[0, 0, 1.0]]), (rad * o)[None])
                P_ir.add(xform(Pn, Rn, c + rad * o * 0.063), Tn, mat="M_iron", smooth="none")
            # bracket head plate bolted under the sheer
            hd = capw(np.array([[sx * xw, sy * YS, ZSH - 0.10 - 0.006]]))[0]
            blocks_world(P_ir, "M_iron", hd[None], frame_mats(capw(np.array([[1.0, 0, 0]])), capw(np.array([[0, 1.0, 0]])),
                                                              np.array([[0, 0, 1.0]])),
                         [[0.10, 0.075, 0.006]], c=0.002, T=T_BLK)
    # ---- deck shell (sarking boards with real thickness) ----
    nx, ny = 46, 40
    xs = np.linspace(-CAP_AB - 0.03, CAP_AF + 0.03, nx)
    ys = np.linspace(-CAP_B - 0.03, CAP_B + 0.03, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zt = cap_z(X, Y) - 0.012
    add_grid(P_fr, "M_timber", capw(np.stack([X, Y, Zt], 2)), flip=False)
    add_grid(P_fr, "M_timber", capw(np.stack([X, Y, Zt - 0.035], 2)), flip=True)
    per = np.concatenate([np.stack([xs, np.full(nx, ys[0])], 1), np.stack([np.full(ny, xs[-1]), ys], 1)[1:],
                          np.stack([xs[::-1], np.full(nx, ys[-1])], 1)[1:], np.stack([np.full(ny, xs[0]), ys[::-1]], 1)[1:]])
    zt = cap_z(per[:, 0], per[:, 1]) - 0.012
    band = np.stack([np.stack([per[:, 0], per[:, 1], zt - 0.035], 1), np.stack([per[:, 0], per[:, 1], zt], 1)], 1)
    add_grid(P_fr, "M_timber", capw(band), flip=False)
    # rafters under the deck: 4 hips + commons
    rafters = []
    for sy in (-1, 1):
        rafters.append(((CAP_AF - 0.05, sy * (CAP_B - 0.05)), (XR1, 0.0)))
        rafters.append(((-CAP_AB + 0.05, sy * (CAP_B - 0.05)), (XR0, 0.0)))
        for xx in (XR0, CAP_XC, XR1):
            rafters.append(((xx, sy * (CAP_B - 0.05)), (xx, sy * 0.05)))
    rafters.append(((CAP_AF - 0.05, 0.0), (XR1 + 0.05, 0.0)))
    rafters.append(((-CAP_AB + 0.05, 0.0), (XR0 - 0.05, 0.0)))
    for (x0, y0), (x1, y1) in rafters:
        n = 10
        t = np.linspace(0, 1, n)
        xx = x0 + (x1 - x0) * t
        yy = y0 + (y1 - y0) * t
        zz = deck_under(xx, yy) - 0.05
        P, T = sweep(capw(np.stack([xx, yy, zz], 1))[None], rect_prof(0.07, 0.1, 0.012), up=(0, 0, 1))
        P_fr.add(P, T, mat="M_timber", smooth="bevel")
    # ---- valance: vertical board skirt hanging outside the curb (covers the wheel gap). The boards are notched
    # around the four sheer ends with 1 cm clearance: the ring leaves a gap where each sheer passes, filled by a
    # short board below the sheer and one above it where there is room. ----
    rr = SKIRT_R + 0.0125
    r_in, r_out = SKIRT_R, SKIRT_R + 0.025
    blocks = []
    for sy_ in (-1, 1):
        for xe in SH_X:
            angs = []
            for rq in (r_in - 0.003, r_out + 0.003):
                for yq in (sy_ * (YS - 0.08 - 0.01), sy_ * (YS + 0.08 + 0.01)):
                    xq = math.copysign(math.sqrt(rq ** 2 - yq ** 2), xe)
                    angs.append(math.atan2(yq, xq) % (2 * PI))
            blocks.append((min(angs), max(angs)))
    blocks.sort()
    arcs = []                                  # (a0, a1, kind) kind 0 = free, 1 = sheer gap
    for i, (b0, b1) in enumerate(blocks):
        nb0 = blocks[(i + 1) % len(blocks)][0] + (2 * PI if i == len(blocks) - 1 else 0)
        arcs.append((b0, b1, 1))
        arcs.append((b1, nb0, 0))
    gap = 0.004
    vb = []                                    # (angle centre, arc width, z bottom, z top)
    for a0, a1, kind in arcs:
        S_ = (a1 - a0) * rr
        if kind == 1:
            ac = (a0 + a1) / 2
            cx, cy = rr * math.cos(ac), rr * math.sin(ac)
            zb = ZCT - 0.065 + rng.uniform(-0.01, 0.01)
            vb.append((ac, S_ + 0.02, zb, ZSH - 0.10 - 0.01))     # under-board spans the notch (+1 cm laps)
            zt = float(deck_under(np.array(cx), np.array(cy))) + 0.01
            if zt - (ZSH + 0.11) > 0.03:
                vb.append((ac, S_ + 0.02, ZSH + 0.10 + 0.01, zt))
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
            vb.append((ac, w, ZCT - 0.065 + rng.uniform(-0.012, 0.012), zt))
    vb = np.array(vb)
    a_c, ws, zbot, ztop = vb[:, 0], vb[:, 1], vb[:, 2], vb[:, 3]
    N = len(vb)
    cx, cy = rr * np.cos(a_c), rr * np.sin(a_c)
    Lz = ztop - zbot
    h = np.stack([Lz / 2, np.full(N, 0.0125), ws / 2], 1)
    P = rbox(T_BRD, h, np.stack([np.full(N, 0.006), np.full(N, 0.005), np.minimum(0.006, ws / 5)], 1))
    P[:, :, 1] += rng.uniform(-0.003, 0.003, N)[:, None]
    radv = np.stack([np.cos(a_c), np.sin(a_c), np.zeros(N)], 1)
    tanv = np.stack([-np.sin(a_c), np.cos(a_c), np.zeros(N)], 1)
    zv = np.repeat([[0, 0, 1.0]], N, 0)
    Rk = frame_mats(zv, radv, np.cross(zv, radv))
    sk = np.clip(rng.normal(0, 0.3, N), -0.5, 0.5) * D2R * (Lz > 0.2)
    Rk = Rk @ rotm([0, 1, 0], sk)
    ctr = np.stack([cx, cy, (ztop + zbot) / 2], 1)
    Wk = xform(P, Rk, ctr)
    P_fr.add(capw(Wk), T_BRD, Pl=P, mat="M_timber_weathered", smooth="bevel")
    log("valance boards %d (4 sheer notches)" % N)
    # nail heads along the top (into the eave plate)
    sel = Lz > 0.15
    nl = np.stack([cx, cy, ztop - 0.06], 1)[sel]
    prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
    Pn, Tn = lathe(np.repeat(prof[None], int(sel.sum()), 0), 6)
    Rn = frame_mats(tanv[sel], zv[sel], radv[sel])
    P_ir.add(capw(xform(Pn, Rn, nl + radv[sel] * 0.0125)), Tn, mat="M_iron", smooth="all")
    # ---- shingles (4 hipped faces) ----
    faces = [  # (o, e, run)
        (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), CAP_EF),
        (np.array([-1.0, 0, 0]), np.array([0, -1.0, 0]), CAP_EB),
        (np.array([0, 1.0, 0]), np.array([-1.0, 0, 0]), CAP_SB),
        (np.array([0, -1.0, 0]), np.array([1.0, 0, 0]), CAP_SB)]

    def face_point(fi, t, s):
        """cap-local (x, y) of normalised height t and lateral s on face fi."""
        o, e, R = faces[fi]
        if fi == 0:
            return CAP_AF - t * R, s
        if fi == 1:
            return -CAP_AB + t * R, -s
        if fi == 2:
            return CAP_XC - s, CAP_B - t * R
        return CAP_XC + s, -CAP_B + t * R

    def half_span(fi, t):
        if fi < 2:
            return CAP_B - t * CAP_SB
        return (CAP_AF + CAP_AB) / 2 - t * CAP_EF

    t = -0.03 / CAP_SB
    courses = []
    while t < 1 - 0.045:
        courses.append(t)
        sig = math.atan(float(cap_dh(t + 0.05)) / CAP_SB)
        t += 0.12 * math.cos(sig) / CAP_SB * rng.uniform(0.96, 1.04)
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
                w = rng.uniform(0.12, 0.2)
                wl.append(w)
                tot += w + rng.uniform(0.003, 0.008)
            wl = np.array(wl) * 2 * hl / tot
            lc = -hl + np.cumsum(wl) + (np.arange(len(wl)) + 0.5) * (2 * hl - wl.sum()) / len(wl) - wl / 2
            lc += (ci % 2) * 0.06 + (0.07 if starter else 0.0)
            N = len(wl)
            L = rng.uniform(0.29, 0.34, N) * (0.8 if starter else 1.0)
            tbb = tb + (rng.uniform(-0.006, 0.006, N) + (0.012 if starter else 0.0)) / R
            sig = np.arctan(cap_dh(tbb + L * 0.35 / R) / R)
            tc = tbb + L / 2 * np.cos(sig) / R
            xc, yc = face_point(fi, tc, lc)
            if fi == 0:
                under = (np.abs(yc) < HOOD_YW + 0.03) & (xc > x_valley(yc) - 0.06)
                # strip beside the hood cheek (down to the hood front): dressed in a lead apron instead
                under |= (np.abs(yc) > HOOD_YW - 0.06) & (xc > float(x_valley(HOOD_YW)) - 0.10) & \
                    (xc < HOOD_XF - 0.02)
            else:
                under = np.zeros(N, bool)
            # shingles whose centre lies past a hip line are not laid (no squashed slivers); the hip board
            # covers the cut edges of the rest
            if fi < 2:
                tx_c = (CAP_AF - xc) / CAP_EF if fi == 0 else (CAP_AB + xc) / CAP_EB
                under |= np.abs(yc) - wl * 0.25 > CAP_B - CAP_SB * tx_c
            else:
                ts_c = (CAP_B - np.abs(yc)) / CAP_SB
                under |= (xc + wl * 0.25 < -CAP_AB + CAP_EB * ts_c) | (xc - wl * 0.25 > CAP_AF - CAP_EF * ts_c)
            zb = CAP_ZE + cap_h(tc)
            ob, ot = (0.006, 0.002) if starter else ((0.022, 0.004) if ci == 1 else (0.03, 0.004))
            beta = np.arctan2(ob - ot, L) + rng.uniform(-0.01, 0.02, N)
            tt = -np.cos(sig)[:, None] * o[None] + np.sin(sig)[:, None] * np.array([0, 0, 1.0])
            nn = np.sin(sig)[:, None] * o[None] + np.cos(sig)[:, None] * np.array([0, 0, 1.0])
            ee = np.cross(tt, nn)
            P = shingle_local(rng, L, wl * rng.uniform(0.97, 1.03, N), rng.uniform(0.016, 0.02, N),
                              np.full(N, 0.007), jag=0.01, curl=0.01, cup=0.003)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], np.clip(rng.normal(0, 1.0, N), -2.5, 2.5) * D2R)
            ctr = np.stack([xc, yc, zb], 1) + nn * ((ob + ot) / 2 + rng.uniform(-0.002, 0.003, N))[:, None]
            Wl = xform(P, frame_mats(tt, nn, ee) @ Rl, ctr)
            W0 = Wl.copy()
            # clamp to the hip lines
            if fi < 2:
                tx = (CAP_AF - Wl[:, :, 0]) / CAP_EF if fi == 0 else (CAP_AB + Wl[:, :, 0]) / CAP_EB
                lim = CAP_B - CAP_SB * tx + 0.025
                Wl[:, :, 1] = np.clip(Wl[:, :, 1], -lim, lim)
            else:
                ts = (CAP_B - np.abs(Wl[:, :, 1])) / CAP_SB
                Wl[:, :, 0] = np.clip(Wl[:, :, 0], -CAP_AB + CAP_EB * ts - 0.025, CAP_AF - CAP_EF * ts + 0.025)
                # top course stops at the ridge line (under the V ridge capping), never across it
                sgn = 1.0 if fi == 2 else -1.0
                Wl[:, :, 1] = sgn * np.maximum(sgn * Wl[:, :, 1], -0.015)
            if fi == 0:
                # stop short of the valleys (exposes the lead valley); fold clamped vertices onto the face
                near = np.abs(Wl[:, :, 1]) < HOOD_YW + 0.05
                xlim = x_valley(Wl[:, :, 1]) - 0.035
                xn = np.where(near, np.minimum(Wl[:, :, 0], xlim), Wl[:, :, 0])
                Wl[:, :, 2] += cap_h((CAP_AF - xn) / CAP_EF) - cap_h((CAP_AF - Wl[:, :, 0]) / CAP_EF)
                Wl[:, :, 0] = xn
            Wl[:, :, 2] = np.minimum(Wl[:, :, 2], CAP_ZE + CAP_RISE + 0.03)
            keep = (~under) & (rng.random(N) > 0.015)
            kk = sliver_keep(W0, Wl, tt, ee)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(Wl[keep]), T_SHK, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
            nsh += keep.sum()
    log("cap shingles", nsh, "slivers culled", nsliver)
    # ---- hood (gablet) over the windshaft neck ----
    yv = np.linspace(0, HOOD_YW + 0.05, 8)
    for s in (-1, 1):
        # roof board shell from the valley line to the front verge
        u = np.linspace(0, 1, 10)
        Yv = np.repeat(yv[None], len(u), 0)
        xv0 = x_valley(Yv) - 0.03
        X = xv0 + (HOOD_XF + 0.05 - xv0) * u[:, None]
        Z = hood_z(Yv) - 0.01
        Gt = np.stack([X, s * Yv, Z], 2)
        Gb = np.stack([X, s * Yv, Z - 0.03], 2)
        add_grid(P_fr, "M_timber", capw(Gt), flip=(s > 0))
        add_grid(P_fr, "M_timber", capw(Gb), flip=(s < 0))
        add_grid(P_fr, "M_timber", capw(np.stack([Gb[:, -1], Gt[:, -1]], 1)), flip=(s < 0))
        add_grid(P_fr, "M_timber", capw(np.stack([Gb[-1, :], Gt[-1, :]], 1)), flip=(s > 0))
        # shingles: courses parallel to the hood eave, stopped at the valley
        sl = math.atan2(HOOD_ZR - HOOD_ZE, HOOD_YW + 0.03)
        for ci, yb in enumerate(np.arange(HOOD_YW + 0.06, 0.02, -0.11 * math.cos(sl))):
            x_start = float(x_valley(yb)) - 0.1
            xl = np.arange(x_start, HOOD_XF + 0.02, 0.15)
            N = len(xl)
            if N == 0:
                continue
            L = rng.uniform(0.26, 0.3, N)
            W = rng.uniform(0.13, 0.16, N)
            P = shingle_local(rng, L, W, np.full(N, 0.017), np.full(N, 0.007), jag=0.008, curl=0.008)
            tt = np.array([0.0, -s * math.cos(sl), math.sin(sl)])
            nn = np.array([0.0, s * math.sin(sl), math.cos(sl)])
            ee = np.cross(tt, nn)
            yc = yb - L / 2 * math.cos(sl)
            ctr = np.stack([xl + 0.075 + (ci % 2) * 0.07, s * yc, hood_z(yc) + 0.02], 1)
            Rr = np.repeat(frame_mats(tt[None], nn[None], ee[None]), N, 0) @ rotm([0, 0, 1], np.full(N, -0.06))
            Wl = xform(P, Rr, ctr)
            W0h = Wl.copy()
            Wl[:, :, 0] = np.clip(Wl[:, :, 0], x_valley(Wl[:, :, 1]) + 0.035, HOOD_XF + 0.05)
            # never cross the hood ridge: clip at the ridge line and keep the vertex on its own plane
            yo_ = Wl[:, :, 1].copy()
            yn_ = s * np.maximum(s * yo_, 0.012)
            Wl[:, :, 2] += -(HOOD_ZR - HOOD_ZE) * (s * yn_ - s * yo_) / (HOOD_YW + 0.03)
            Wl[:, :, 1] = yn_
            keep = Wl[:, :, 0].max(1) > x_valley(Wl[:, :, 1]).max(1) + 0.06
            kk = sliver_keep(W0h, Wl, tt, ee)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(Wl[keep]), T_SHK, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
        # lead valley flashing: folded strip lying on both roof planes under the shingle edges
        yy = np.linspace(0.0, HOOD_YW + 0.03, 12)
        xv_ = x_valley(yy)
        rows = []
        for dx in (-0.11, -0.04, 0.0, 0.04, 0.11):
            xq = xv_ + dx
            zq = np.where(dx < 0, cap_z(xq, yy), hood_z(yy)) - 0.012
            rows.append(np.stack([xq, s * yy, zq], 1))
        G = np.stack(rows, 0)
        add_grid(P_ir, "M_lead", capw(G + np.array([0, 0, 0.006])), flip=(s < 0))
        add_grid(P_ir, "M_lead", capw(G), flip=(s > 0))
        # cheek: vertical boards closing the gap between the hood eave and the falling main roof
        xa = float(x_valley(HOOD_YW))
        for xb in np.arange(xa + 0.04, HOOD_XF, 0.13):
            zb = float(cap_z(np.array(xb), np.array(HOOD_YW - 0.03))) - 0.04
            cap_member(P_fr, "M_timber_weathered", [xb, s * (HOOD_YW - 0.03), zb], [xb, s * (HOOD_YW - 0.03),
                                                                                     HOOD_ZE + 0.0], 0.12, 0.025,
                       up=(0, s, 0), c=0.005, rng=rng, bow=0.003)
    log("cap + hood shingles: slivers culled (< 5 cm wide after clamping)", nsliver)
    build_cap_cappings(P_sh, P_fr, P_ir, rng)
    # front gable boards with a hole for the shaft
    zsh = HUB_Z - (HUB_D - HOOD_XF) * math.tan(TILT)
    rh = 0.215
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
    P, T = sweep(capw(np.stack([xs, np.zeros(n), zs], 1))[None], circle_prof(0.19, 16), up=(0, 0, 1))
    P_ws = parts["windshaft"]
    P_ws.add(P, T, mat="M_timber", smooth="all")
    for xh in (HOOD_XF + 0.08, HOOD_XF + 0.42):
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
PHI_A = (180 - 8) * D2R          # sail A near 9 o'clock (ref1)
SAIL_R1 = 5.8                    # sail A tip radius (ref1 broad paddle, sweep ~5.85)
ARM_R1 = 3.35                    # bare arms B, C, D end just past the rim
PAD_R0 = 2.5                     # board panel heel radius on sail A
W_WH = -0.33                     # wind-wheel blade plane (behind both stocks)
RING_IN, RING_OUT = 1.35, 3.20
W_RING = W_WH - 0.058
BL_R0, BL_R1 = 1.35, 3.90
BL_W0, BL_W1 = 0.55, 1.175
BL_PITCH = 13 * D2R


def rotw(P):
    """rotor-local (x, y, w) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return HUB + P[..., 0:1] * E1 + P[..., 1:2] * E2 + P[..., 2:3] * S_AX


def er_t(phi):
    return np.array([math.cos(phi), math.sin(phi), 0.0]), np.array([-math.sin(phi), math.cos(phi), 0.0])


def stock_w(i):
    return 0.30 if i % 2 == 0 else 0.0


def stock_depth(r, i=0):
    if i == 0:
        return 0.30 - 0.14 * np.clip(r, 0, SAIL_R1) / SAIL_R1
    return 0.30 - 0.10 * np.clip(r, 0, ARM_R1) / ARM_R1


def whip_depth(r):
    return 0.16 - 0.06 * np.clip(r - 1.2, 0, 4.4) / 4.4


def whip_w(r):
    return stock_w(0) + stock_depth(r, 0) / 2 + whip_depth(r) / 2


def twist(r):
    return 10 * D2R * (1 - np.clip((r - 1.3) / (SAIL_R1 - 1.3), 0, 1))


def lead_w(r):
    return 1.02 + 0.23 * np.clip((r - PAD_R0) / (SAIL_R1 - PAD_R0), 0, 1)


def trail_w(r):
    return 1.30 + 0.33 * np.clip((r - PAD_R0) / (SAIL_R1 - PAD_R0), 0, 1)


def sail_map(P, use_twist=True):
    """sail-A-local (r, l, z) -> rotor-local; z measured from the whip centre."""
    er, t = er_t(PHI_A)
    r, l, z = P[..., 0], P[..., 1], P[..., 2]
    b = -twist(r) if use_twist else 0 * r
    l2 = l * np.cos(b) - z * np.sin(b)
    z2 = l * np.sin(b) + z * np.cos(b)
    w = whip_w(r) + z2
    return r[..., None] * er + l2[..., None] * t + w[..., None] * np.array([0, 0, 1.0])


def loc3(er, t, r, l, w):
    return np.asarray(r)[..., None] * er + np.asarray(l)[..., None] * t + np.asarray(w)[..., None] * np.array([0, 0, 1.0])


def perm_tmpl(T, odd):
    return flip_tmpl(T) if odd else T


def hex_heads(part, centers, normals, rad=0.02, hgt=0.012):
    """Hex bolt heads / nuts (rotor-local centres + normals) -> part (world)."""
    centers = np.atleast_2d(centers)
    prof = np.array([(0.0, 0.0), (rad, 0.0), (rad, hgt * 0.7), (rad * 0.75, hgt), (0.0, hgt)])
    P, T = lathe(np.repeat(prof[None], len(centers), 0), 6)
    R = []
    for nrm in np.atleast_2d(normals):
        zz = unit(nrm)
        xx = unit(np.cross([0.31, 0.53, 0.79], zz))
        R.append(np.stack([xx, np.cross(zz, xx), zz], 1))
    part.add(rotw(xform(P, np.array(R), centers)), T, mat="M_iron", smooth="none")


def build_rotor(parts):
    rng = RNG("rotor")
    P_poll, P_wir, P_ri = parts["poll_end"], parts["wheel_spokes"], parts["rotor_iron"]
    letters = "ABCD"
    Z3 = np.array([0, 0, 1.0])
    for i in range(4):
        L = letters[i]
        P_st = parts["sail_%s_stock" % L]
        phi = PHI_A + i * PI / 2
        er, t = er_t(phi)
        sw = stock_w(i)
        # stock half (tapering 0.30 -> 0.16 for A, 0.30 -> 0.20 for the bare arms), from inside the poll end
        r0, r1 = -0.15, (SAIL_R1 + 0.05 if i == 0 else ARM_R1)
        # hewn stock: adze scallops, worn chamfers (2-4 cm before the taper -> 1.5-3 cm), 1-2 long checks,
        # split end grain at the tip
        P, Th = hewn_beam(rng, r1 - r0, 0.30, 0.30, chamfer=(0.02, 0.04), adze=(0.005, 0.008),
                          checks=(1, 2), check_len=(0.6, 1.5), end_split=1, faces_check=(1, 2))
        r = (r0 + r1) / 2 + P[:, :, 0]
        sc = stock_depth(r, i) / 0.30
        Q = np.stack([r, P[:, :, 1] * sc, P[:, :, 2] * sc + sw], -1)
        Q[..., 1] += rng.uniform(-0.012, 0.012) * (r / r1) ** 2
        Q[..., 2] += rng.uniform(-0.008, 0.008) * (r / r1) ** 2
        P_st.add(rotw(loc3(er, t, Q[..., 0], Q[..., 1], Q[..., 2])), Th, Pl=P[0], mat="M_timber_weathered",
                 smooth="bevel")
        # two iron bands (50 x 6 mm) round the stock near the poll end, each with a through-bolt
        for rb_ in (0.47 + rng.uniform(-0.02, 0.02), 0.80 + rng.uniform(-0.02, 0.02)):
            hs_ = float(stock_depth(rb_, i)) / 2 + 0.003
            cr = 0.012
            loop = []
            for (cl, cw) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
                for a_ in np.linspace(0, PI / 2, 4):
                    base_a = math.atan2(cw, cl) - PI / 4
                    aa_ = base_a + a_
                    loop.append((cl * (hs_ - cr) + cr * math.cos(aa_), sw + cw * (hs_ - cr) + cr * math.sin(aa_)))
            loop = np.array(loop)
            path = rotw(loc3(er, t, np.full(len(loop), rb_), loop[:, 0], loop[:, 1]))
            Pb_, Tb_ = sweep(path[None], rect_prof(0.006, 0.05, 0.0015), up=rotw(er[None])[0] - HUB, closed=True)
            P_ri.add(Pb_, Tb_, mat="M_iron", smooth="bevel")
            hex_heads(P_ri, np.array([loc3(er, t, rb_, 0.0, sw + hs_ + 0.003), loc3(er, t, rb_, 0.0, sw - hs_ - 0.003)]),
                      np.array([Z3, -Z3]), rad=0.02, hgt=0.014)
        # strap to the outer rim: a foot plate bolted (2 bolts) to the stock's back face, a flat iron drop
        # strap on the stock's centre line down to the rim, and a clip plate behind the rim
        hs = float(stock_depth(RING_OUT, i)) / 2
        wback = sw - float(stock_depth(RING_OUT, i)) / 2
        a_ = rotw(loc3(er, t, RING_OUT - 0.12, 0.0, wback - 0.0045))
        b_ = rotw(loc3(er, t, RING_OUT + 0.12, 0.0, wback - 0.0045))
        member(P_ri, "M_iron", a_[None], b_[None], 0.06, 0.009, up=S_AX, c=0.002)
        a_ = rotw(loc3(er, t, RING_OUT, 0.0, wback - 0.009))
        b_ = rotw(loc3(er, t, RING_OUT, 0.0, W_RING - 0.016))
        member(P_ri, "M_iron", a_[None], b_[None], 0.05, 0.009, up=rotw(t[None])[0] - HUB, c=0.002)
        a_ = rotw(loc3(er, t, RING_OUT - 0.06, 0.0, W_RING - 0.0115))
        b_ = rotw(loc3(er, t, RING_OUT + 0.06, 0.0, W_RING - 0.0115))
        member(P_ri, "M_iron", a_[None], b_[None], 0.05, 0.009, up=S_AX, c=0.002)
        cen = [loc3(er, t, RING_OUT + dr, 0.0, wback - 0.009) for dr in (-0.085, 0.085)] + \
              [loc3(er, t, RING_OUT + dr, 0.0, sw + float(stock_depth(RING_OUT, i)) / 2) for dr in (-0.085, 0.085)]
        nrm = [-Z3, -Z3, Z3, Z3]
        hex_heads(P_ri, np.array(cen), np.array(nrm), rad=0.02, hgt=0.014)
        if i == 2:
            # cast-iron counterweight box on arm C (opposite the heavy board sail)
            P_cw = parts["sail_C_counterweight"]
            rc = 2.6
            hsc = float(stock_depth(rc, i)) / 2
            hb = np.array([[0.25, 0.15, 0.125]])
            P = rbox(T_DRS, hb, np.array([[0.012, 0.012, 0.012]]))
            P += rng.normal(0, 0.0015, P.shape)
            Q = np.stack([rc + P[:, :, 0], P[:, :, 1], sw + hsc + 0.127 + P[:, :, 2]], -1)
            P_cw.add(rotw(loc3(er, t, Q[..., 0], Q[..., 1], Q[..., 2])), T_DRS, Pl=P, mat="M_iron", smooth="bevel")
            for rq in (rc - 0.15, rc + 0.15):
                wf = sw + hsc + 0.254 + 0.005
                wb = sw - hsc - 0.005
                ls = 0.15 + 0.005
                for (l0, w0), (l1, w1), up in (((-ls, wf), (ls, wf), S_AX), ((-ls, wb), (ls, wb), S_AX),
                                               ((-ls, wb), (-ls, wf), None), ((ls, wb), (ls, wf), None)):
                    a_ = rotw(loc3(er, t, rq, l0, w0))
                    b_ = rotw(loc3(er, t, rq, l1, w1))
                    dv = unit(b_ - a_)
                    upv = S_AX if up is not None else rotw(t[None])[0] - HUB
                    member(P_ri, "M_iron", (a_ - dv * 0.006)[None], (b_ + dv * 0.006)[None], 0.045, 0.009, up=upv,
                           c=0.002)
                hex_heads(P_ri, np.array([loc3(er, t, rq, l, wb - 0.0045) for l in (-0.09, 0.09)]),
                          np.array([-Z3, -Z3]), rad=0.02, hgt=0.014)

    # ---- sail A: broad plank paddle (ref1, 9 o'clock) ----
    er, t = er_t(PHI_A)
    P_wh, P_bar, P_hem, P_bd = parts["sail_A_whip"], parts["sail_A_bars"], parts["sail_A_hemlaths"], \
        parts["sail_A_boards"]
    P_stA = parts["sail_A_stock"]
    # whip bolted to the stock face
    r0, r1 = 1.2, SAIL_R1 + 0.02
    P, Th = hewn_beam(rng, r1 - r0, 0.16, 0.16, chamfer=(0.015, 0.025), adze=(0.003, 0.005), checks=(1, 1),
                      check_len=(0.5, 1.0), end_split=1, faces_check=(2,))
    r = (r0 + r1) / 2 + P[:, :, 0]
    sc = whip_depth(r) / 0.16
    Q = np.stack([r, P[:, :, 1] * sc, P[:, :, 2] * sc], -1)
    P_wh.add(rotw(sail_map(Q, use_twist=False)), Th, Pl=P[0], mat="M_timber_weathered", smooth="bevel")
    # U-clamps whip -> stock: front/back straps lie flat on the faces (normal = shaft axis), side straps
    # flat on the side faces (normal = t)
    for rc in (1.45, 2.6, 3.8, 5.0):
        hs = float(stock_depth(rc, 0)) / 2
        hw = float(whip_depth(rc)) / 2
        wc = float(whip_w(rc))
        wb = stock_w(0) - hs - 0.0045
        wf = wc + hw + 0.0045
        sw_ = max(hs, hw) + 0.0045
        for (a, b, up) in (((-sw_, wf), (sw_, wf), S_AX), ((-sw_, wb), (sw_, wb), S_AX),
                           ((-sw_, wb), (-sw_, wf), None), ((sw_, wb), (sw_, wf), None)):
            aw = rotw(loc3(er, t, rc, a[0], a[1]))
            bw = rotw(loc3(er, t, rc, b[0], b[1]))
            dv = unit(bw - aw)
            upv = S_AX if up is not None else rotw(t[None])[0] - HUB
            member(P_stA, 1, aw - dv * 0.0045, bw + dv * 0.0045, 0.05, 0.009, up=upv, c=0.002)
        hex_heads(P_ri, np.array([loc3(er, t, rc, l, wb - 0.0045) for l in (-sw_ + 0.02, sw_ - 0.02)]),
                  np.array([-Z3, -Z3]), rad=0.019, hgt=0.014)
    # ---- ref1 broad board paddle: panel r 2.5 -> ~5.8, 2.3 m wide at the heel flaring to 2.9 m.
    # Construction (front -> back): whip + clamps, 2 cross cleats, full-length radial boards (2 cm), sail bars
    # (3 x 4.5 cm) BEHIND the boards (only their ends show past the edges), back uplongs. Sail-A-local z is
    # measured from the whip centre; the stock's front face is at z = -whip_depth/2.
    def z_bar(r):
        return -whip_depth(r) / 2 + 0.012 + 0.0225

    def z_board(r):
        return -whip_depth(r) / 2 + 0.012 + 0.045 + 0.0105

    def lin_(r):           # boards start just outside the stock + clamp side straps
        return stock_depth(r, 0) / 2 + 0.022
    rs = np.array([2.545, 3.17, 3.885, 4.50, 5.09, 5.62]) + rng.uniform(-0.006, 0.006, 6)
    nbar = len(rs)
    ext = rng.uniform(0.03, 0.05, (nbar, 2))
    l0 = lead_w(rs) + ext[:, 0]
    l1 = -trail_w(rs) - ext[:, 1]
    h = np.stack([(l0 - l1) / 2, np.full(nbar, 0.015), np.full(nbar, 0.0225)], 1)
    P = rbox(T_PLK, h, np.repeat([[0.006, 0.005, 0.006]], nbar, 0))
    P[:, :, 1] += rng.uniform(-0.005, 0.005, (nbar, 1)) * (1 - (P[:, :, 0] / h[:, None, 0]) ** 2)
    Q = np.stack([rs[:, None] + P[:, :, 1], ((l0 + l1) / 2)[:, None] + P[:, :, 0], z_bar(rs)[:, None] + P[:, :, 2]], -1)
    P_bar.add(rotw(sail_map(Q)), perm_tmpl(T_PLK, True), Pl=P, mat="M_timber_weathered", smooth="bevel")
    # back uplongs (hemlaths) behind the bars: leading edge, trailing edge and a mid-trailing one
    for lat_fn in (lambda r: lead_w(r) - 0.06, lambda r: -trail_w(r) + 0.06, lambda r: -0.5 * (trail_w(r) + lin_(r))):
        r0, r1 = PAD_R0 + 0.02, SAIL_R1 - 0.12
        h = np.array([[(r1 - r0) / 2, 0.022, 0.02]])
        P = rbox(T_PLK, h, np.array([[0.006, 0.006, 0.006]]))
        rr = (r0 + r1) / 2 + P[:, :, 0]
        Q = np.stack([rr, lat_fn(rr) + P[:, :, 1], z_bar(rr) - 0.0225 - 0.0205 + P[:, :, 2]], -1)
        Q[..., 1] += rng.uniform(-0.01, 0.01) * np.sin((rr - r0) / (r1 - r0) * PI)
        P_hem.add(rotw(sail_map(Q)), T_PLK, Pl=P, mat="M_timber_weathered", smooth="bevel")
    # full-length radial boards, 7 leading / 9 trailing, 2 cm thick, 0.5-1.5 cm gaps; seams fan toward the tip.
    # Ragged tip (+-4 cm), two boards short (8-15 cm, one broken on the diagonal), three with a butt joint
    # over a bar, cup / warp per board.
    nails = []
    nb_total = 0
    cleat_r = (2.72, 4.30)
    short = {(1, 4): 0.10, (-1, 6): 0.13}
    butt = {(1, 2): 3, (-1, 3): 2, (-1, 7): 3}
    for side, nbd in ((1, 7), (-1, 9)):
        fw = rng.uniform(0.88, 1.12, nbd)
        fr = np.concatenate([[0], np.cumsum(fw)]) / fw.sum()
        for j in range(nbd):
            g0 = rng.uniform(0.0025, 0.0075)
            g1 = rng.uniform(0.0025, 0.0075)
            rh_ = PAD_R0 + rng.uniform(-0.01, 0.02)
            rt_ = SAIL_R1 - 0.04 + rng.uniform(-0.04, 0.04) - short.get((side, j), 0.0)
            cup = rng.uniform(-0.005, 0.005)
            warp = rng.uniform(-0.005, 0.005)
            tw_end = rng.uniform(-0.004, 0.004)
            tip_k = rng.uniform(-0.03, 0.03)
            broken = (side, j) == (1, 4)
            jb = butt.get((side, j))
            pieces = [(rh_, rs[jb] - 0.002), (rs[jb] + 0.003, rt_)] if jb is not None else [(rh_, rt_)]
            for (pa, pb) in pieces:
                h = np.array([[(pb - pa) / 2, 0.01, 0.5]])
                P = rbox(T_BRD, h, np.array([[0.005, 0.004, 0.012]]))
                u = (P[:, :, 0] + h[0, 0]) / (2 * h[0, 0])
                v = P[:, :, 2] + 0.5
                rr = pa + u * (pb - pa)
                at_tip = u > 0.5 if pb == rt_ else np.zeros_like(u, bool)
                rr = rr + np.where(at_tip, tip_k * (v - 0.5) - (0.11 * v if broken else 0.0), 0.0)
                lout = lead_w(rr) if side > 0 else trail_w(rr)
                lin = lin_(rr)
                e0 = lin + fr[j] * (lout - lin) + g0
                e1 = lin + fr[j + 1] * (lout - lin) - g1
                lat = side * (e0 + v * (e1 - e0))
                s_ = (rr - rh_) / (rt_ - rh_)
                zz = z_board(rr) + P[:, :, 1] + cup * ((2 * v - 1) ** 2 - 0.33) + warp * np.sin(s_ * PI) + \
                    tw_end * (2 * v - 1) * s_
                Q = np.stack([rr, lat, zz], -1)
                P_bd.add(rotw(sail_map(Q)), perm_tmpl(T_BRD, side > 0), Pl=P, mat="M_timber_weathered",
                         smooth="bevel")
                nb_total += 1
            for rb in list(rs) + list(cleat_r):
                if rb > rt_ - 0.05:
                    continue
                lin = float(lin_(rb))
                lout = float(lead_w(rb) if side > 0 else trail_w(rb))
                wj = (fr[j + 1] - fr[j]) * (lout - lin)
                lc = lin + (fr[j] + fr[j + 1]) / 2 * (lout - lin)
                zf = float(z_board(rb)) + 0.0105 + (0.03 if rb in cleat_r else 0.0)
                offs = (-0.28, 0.28) if rb in cleat_r else (rng.uniform(-0.15, 0.15),)
                for o in offs:
                    nails.append((rb + rng.uniform(-0.01, 0.01), side * (lc + o * wj), zf))
    log("sail A boards", nb_total)
    # two cross cleats (8 x 3 cm) on the board faces, either side of the whip
    for rc in cleat_r:
        for side in (1, -1):
            la = float(lin_(rc)) + 0.015
            lb = float(lead_w(rc) if side > 0 else trail_w(rc)) - rng.uniform(0.02, 0.05)
            h = np.array([[(lb - la) / 2, 0.04, 0.015]])
            P = rbox(T_PLK, h, np.array([[0.008, 0.006, 0.006]]))
            P[:, :, 2] += rng.uniform(-0.003, 0.003) * (1 - (P[:, :, 0] / h[0, 0]) ** 2)
            Q = np.stack([rc + P[:, :, 1] + rng.uniform(-0.01, 0.01) * P[:, :, 0] / h[0, 0],
                          side * ((la + lb) / 2 + P[:, :, 0]), z_board(rc) + 0.0105 + 0.015 + P[:, :, 2]], -1)
            P_bar.add(rotw(sail_map(Q)), perm_tmpl(T_PLK, side < 0), Pl=P, mat="M_timber_weathered", smooth="bevel")
    nails = np.array(nails)
    prof = np.array([(0.0, -0.002), (0.0075, -0.002), (0.0072, 0.002), (0.004, 0.0045), (0.0, 0.005)])
    P, T = lathe(np.repeat(prof[None], len(nails), 0), 6)
    Q = sail_map(nails)
    nrm = sail_map(nails + [0, 0, 0.01]) - Q
    Rn = []
    for v in nrm:
        zz = unit(v)
        xx = unit(np.cross([0.3, 0.5, 0.8], zz))
        Rn.append(np.stack([xx, np.cross(zz, xx), zz], 1))
    P_ri.add(rotw(xform(P, np.array(Rn), Q)), T, mat="M_iron", smooth="all")

    # ---- poll end (cast-iron cross box) ----
    h = np.array([[0.23, 0.23, 0.37]])
    P = rbox(T_DRS, h, np.array([[0.025, 0.025, 0.025]]))
    P_poll.add(rotw(loc3(er, t, P[..., 0], P[..., 1], P[..., 2])), T_DRS, Pl=P, mat="M_iron", smooth="bevel")
    prof = np.array([(0.0, 0.37), (0.21, 0.37), (0.22, 0.39), (0.2, 0.42), (0.1, 0.44), (0.06, 0.5), (0.0, 0.51)])
    Pc, T = lathe(prof[None], 24)
    P_poll.add(rotw(Pc), T, mat="M_iron", smooth="all")
    prof = np.array([(0.0, -0.40), (0.36, -0.40), (0.37, -0.385), (0.36, -0.37), (0.0, -0.37)])
    Pc, T = lathe(prof[None], 32)
    P_poll.add(rotw(Pc), T, mat="M_iron", smooth="bevel")
    bolts = []
    for side in range(4):
        ang = PHI_A + side * PI / 2
        nrm_ = np.array([math.cos(ang), math.sin(ang), 0])
        tan = np.array([-math.sin(ang), math.cos(ang), 0])
        wl = (-0.28, -0.10) if side % 2 == 0 else (-0.28, 0.27)
        for u in (-0.15, 0.15):
            for w in wl:
                bolts.append((nrm_ * 0.232 + tan * u + np.array([0, 0, w]), nrm_))
    hex_heads(P_poll, np.array([b[0] for b in bolts]), np.array([b[1] for b in bolts]), rad=0.026, hgt=0.02)

    # ---- wind-wheel: 16 broad board blades on two flat iron rings (near-continuous annulus) ----
    P_rim, P_bl = parts["wheel_rim"], parts["wheel_blades"]
    for rr_ in (RING_IN, RING_OUT):
        a = np.linspace(0, 2 * PI, 161)[:-1]
        path = np.stack([rr_ * np.cos(a), rr_ * np.sin(a), np.full(160, W_RING) + 0.002 * np.sin(a * 3 + rr_)], 1)
        P, T = sweep(rotw(path)[None], rect_prof(0.06, 0.012, 0.003), up=S_AX, closed=True)
        P_rim.add(P, T, mat="M_iron", smooth="bevel")
    nbl = 16
    rivets_c, rivets_n = [], []
    for k in range(nbl):
        phi = PHI_A + (11.25 + 22.5 * k) * D2R + rng.normal(0, 0.3) * D2R
        er_k, t_k = er_t(phi)
        pitch = BL_PITCH + rng.uniform(-0.5, 0.5) * D2R
        dW = rng.uniform(-0.02, 0.02, 3)          # per-blade outline variation (+-2 cm)

        def blade_map(Q, er_k=er_k, t_k=t_k, pitch=pitch):
            r, l, z = Q[..., 0], Q[..., 1], Q[..., 2]
            l2 = l * math.cos(pitch) - z * math.sin(pitch)
            z2 = l * math.sin(pitch) + z * math.cos(pitch)
            return r[..., None] * er_k + l2[..., None] * t_k + (W_WH + z2)[..., None] * np.array([0, 0, 1.0])

        nb = 4 if k % 3 else 3
        fw = rng.uniform(0.85, 1.15, nb)
        fr = np.concatenate([[0], np.cumsum(fw)]) / fw.sum()
        for j in range(nb):
            h = np.array([[1.0, 0.01, 0.5]])
            P = rbox(T_BRD, h, np.array([[0.006, 0.005, 0.01]]))
            u = (P[:, :, 0] + 1.0) / 2.0
            v = P[:, :, 2] + 0.5
            fl = fr[j] + (fr[j + 1] - fr[j]) * v
            lat = fl * 2 - 1
            tip = BL_R1 + rng.uniform(-0.03, 0.03) + 0.008 * np.sin(lat * 5 + k)
            r = BL_R0 - 0.02 + u * (tip - BL_R0 + 0.02)
            s_ = np.clip((r - BL_R0) / (BL_R1 - BL_R0), 0, 1)
            Wd = BL_W0 + (BL_W1 - BL_W0) * s_ + dW[0] * s_ + dW[1] * np.sin(s_ * PI)
            # worn tip corners on the outer boards
            if j in (0, nb - 1):
                corner = np.clip((u - 0.93) / 0.07, 0, 1) * np.clip((np.abs(lat) - 0.7) / 0.3, 0, 1)
                r = r - corner * rng.uniform(0.02, 0.04)
            gap = 0.004
            l = (fl - 0.5) * Wd + np.where(v < 0.5, gap, -gap) + dW[2] * s_ * 0.5
            z = P[:, :, 1] + rng.uniform(-0.003, 0.003) + 0.003 * (2 * v - 1) ** 2
            Q = np.stack([r, l, z], -1)
            P_bl.add(rotw(blade_map(Q)), perm_tmpl(T_BRD, True), Pl=P, mat="M_timber", smooth="bevel")
        # central batten on the back, bearing on both rings
        r0, r1 = BL_R0 - 0.03, BL_R1 - 0.12
        h = np.array([[(r1 - r0) / 2, 0.025, 0.018]])
        P = rbox(T_PLK, h, np.array([[0.006, 0.006, 0.006]]))
        Q = np.stack([(r0 + r1) / 2 + P[:, :, 0], P[:, :, 1], P[:, :, 2] - 0.028], -1)
        P_bl.add(rotw(blade_map(Q)), T_PLK, Pl=P, mat="M_timber", smooth="bevel")
        for rr_ in (RING_IN, RING_OUT):
            for lq in (-0.012, 0.012):
                rivets_c.append(blade_map(np.array([[rr_, lq, 0.0105]]))[0])
                rivets_n.append(blade_map(np.array([[rr_, lq, 1.0]]))[0] - blade_map(np.array([[rr_, lq, 0.0]]))[0])
    prof = np.array([(0.0, 0.0), (0.011, 0.0), (0.009, 0.004), (0.0, 0.006)])
    rivets_c = np.array(rivets_c)
    P, T = lathe(np.repeat(prof[None], len(rivets_c), 0), 6)
    Rr = []
    for nv_ in rivets_n:
        zz = unit(nv_)
        xx = unit(np.cross([0.3, 0.5, 0.8], zz))
        Rr.append(np.stack([xx, np.cross(zz, xx), zz], 1))
    P_wir.add(rotw(xform(P, np.array(Rr), rivets_c)), T, mat="M_iron", smooth="all")
    # spokes (8) from the poll end's rear flange to the inner ring (the rim is carried by the blade
    # battens and by the four arm straps)
    for k in range(8):
        for (phi, r0, w0, r1, w1) in ((PHI_A + (22.5 + 45 * k) * D2R, 0.30, -0.36, RING_IN, W_RING),):
            er_k, t_k = er_t(phi)
            n = 8
            rr = np.linspace(r0, r1 - 0.03, n)
            ww = np.linspace(w0, w1, n)
            P, T = sweep(rotw(loc3(er_k, t_k, rr, 0 * rr, ww))[None], circle_prof(0.0125, 8), up=S_AX)
            P_wir.add(P, T, mat="M_iron", smooth="all")
            pp = rotw(loc3(er_k, t_k, r1 - 0.06, 0.0, w1))
            pq = rotw(loc3(er_k, t_k, r1 + 0.035, 0.0, w1))
            member(P_wir, "M_iron", pp[None], pq[None], 0.04, 0.02, up=S_AX, c=0.004)


# =============================================================================================
# I. RAKING PROPS (-X)
# =============================================================================================
def build_props(parts):
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = RNG("props")
    defs = []
    # two near-parallel long props from just under the collar on the -X face, one shorter on the -X/-Y face
    zc = Z_COLLAR - 0.11
    for (k, lat, z, gnd) in ((6, 0.36, zc, (-6.3, -1.2)), (6, -0.36, zc, (-6.0, 0.9)),
                             (6, 0.62, float(TZ(7.30)), (-6.0, -3.1))):
        top = face_map(k, np.array([lat]), np.array([z]), np.array([0.14]))[0]
        defs.append((lean(top[None])[0], np.array([gnd[0], gnd[1], 0.30]), k, z))
    Zf = 0.19                                   # top of the chock base (foot seat)
    for idx, (top, bot, k, zatt) in enumerate(defs):
        nn_, tt_ = face_axes(k)
        nn_ = LEAN_R @ nn_
        axis = bot - top
        Lp = np.linalg.norm(axis)
        ax = axis / Lp
        hz = unit(np.array([axis[0], axis[1], 0]))
        side = unit(np.cross(axis, [0, 0, 1.0]))
        upv = np.cross(side, ax)
        # ---- pole: 24 sides (+ check lips), rings every ~6.5 cm (1.5 cm over the foot), dia 0.15 -> 0.20,
        # 6-12 cm bow; 2-3 real V checks, 2 adze flats + a bark-strip remnant, 4-6 knots with branch stubs ----
        dt = 0.065 / Lp
        t_main = np.arange(-0.02, 1.0 - 0.5 / Lp, dt)
        t_foot = np.arange(t_main[-1] + 0.015 / Lp, 1.06, 0.015 / Lp)
        t = np.concatenate([t_main, t_foot])
        n = len(t)
        bow = rng.uniform(0.06, 0.12) * rng.choice([-1, 1])
        sag = rng.uniform(0.0, 0.03)
        cen = top + axis * t[:, None] + side * (bow * np.sin(np.clip(t, 0, 1) * PI))[:, None] \
            - upv * (sag * np.sin(np.clip(t, 0, 1) * PI))[:, None]
        rad = 0.075 + 0.025 * np.clip(t, 0, 1) + 0.003 * np.sin(t * 13 + idx) + 0.002 * np.sin(t * 31 + 2 * idx)
        nck = int(rng.integers(2, 4))
        # first check on the face seen from the front / hero cameras (-side), the second on the upper face
        ck_a = np.array([PI + rng.uniform(-0.4, 0.4), PI / 2 + rng.uniform(-0.4, 0.4),
                         rng.uniform(-PI / 2, 0.2)])[:nck]
        base_a = np.linspace(0, 2 * PI, 24, endpoint=False)
        extra = np.concatenate([[a - 0.115, a, a + 0.115] for a in ck_a]) % (2 * PI)
        keep_b = np.array([np.min(np.abs((b - extra + PI) % (2 * PI) - PI)) > 0.06 for b in base_a])
        ang = np.sort(np.concatenate([base_a[keep_b], extra]))
        m = len(ang)
        ell = 1 + rng.uniform(-0.04, 0.04) * np.cos(2 * ang + rng.uniform(0, PI))
        R = rad[:, None] * ell[None, :]
        sdist = (1 - t) * Lp                                    # distance from the foot (m)
        # low-frequency undulation of the trunk (+-3 mm)
        R += 0.003 * np.sin(sdist[:, None] * rng.uniform(2, 4) + ang[None, :] * 2 + rng.uniform(0, 6)) * \
            np.sin(sdist[:, None] * rng.uniform(0.7, 1.4) + rng.uniform(0, 6))
        # adze flats (+-1 cm) and a bark-strip remnant (proud 7 mm, ragged edges)
        for q in range(3):
            af = (PI + rng.uniform(-0.5, 0.5)) if q == 0 else rng.uniform(0, 2 * PI)
            lf = rng.uniform(0.8, 1.6)
            s0 = rng.uniform(0.6, 3.5) if q == 0 else rng.uniform(1.0, Lp - lf - 0.5)
            win = np.clip(np.minimum(sdist - s0, s0 + lf - sdist) / 0.15, 0, 1)
            da = (ang[None, :] - af + PI) % (2 * PI) - PI
            dep = rng.uniform(0.010, 0.014) * win
            flat = (rad[:, None] - dep[:, None]) / np.maximum(np.cos(da), 0.3)
            R = np.where(np.abs(da) < 1.2, np.minimum(R, flat), R)
        ab = rng.uniform(0, 2 * PI)
        lb = rng.uniform(0.5, 0.9)
        s0 = rng.uniform(2.0, Lp - lb - 1.0)
        inb = (sdist > s0) & (sdist < s0 + lb)
        hw_b = 0.3 + 0.08 * np.sin(sdist * 17 + idx) + 0.05 * np.sin(sdist * 41)
        da = np.abs((ang[None, :] - ab + PI) % (2 * PI) - PI)
        R += 0.010 * (inb[:, None] & (da < hw_b[:, None]))
        # V checks: 2.3 cm wide (lips at +-1.15 cm), 1.5-2.5 cm deep, 0.8-2 m long
        checks = []
        for a in ck_a:
            j = int(np.argmin(np.abs((ang - a % (2 * PI) + PI) % (2 * PI) - PI)))
            lc = rng.uniform(0.8, 2.0)
            s0 = rng.uniform(0.5, 4.5 - lc) if len(checks) == 0 else rng.uniform(0.8, Lp - lc - 0.8)
            u = np.clip((sdist - s0) / lc, 0, 1)
            dep = rng.uniform(0.015, 0.025) * np.sqrt(np.sin(u * PI))
            R[:, j] -= dep
            checks.append((s0, lc))
        # knots: 4-6, at least 2 within 2.5 m of the foot
        nk = int(rng.integers(4, 7))
        kd = np.concatenate([rng.uniform(0.7, 2.4, 2), rng.uniform(3.0, Lp - 1.0, nk - 2)])
        knots = []
        for sk in kd:
            tk = 1 - sk / Lp
            ak = rng.uniform(0, 2 * PI)
            dk = rng.uniform(0.04, 0.07)
            knots.append((tk, ak, dk))
            dda = np.abs((ang - ak + PI) % (2 * PI) - PI)
            R += 0.016 * np.exp(-(dda / 0.5) ** 2)[None, :] * np.exp(-((sdist - sk) / 0.09) ** 2)[:, None]
        ex = side
        ey = upv
        prof = np.stack([R * np.cos(ang)[None], R * np.sin(ang)[None]], -1)
        Pp = cen[:, None, :] + prof[..., 0:1] * ex + prof[..., 1:2] * ey
        # head: cut flush against the collar strap / boards (plane parallel to the face)
        face_pt = lean(face_map(k, np.array([0.0]), np.array([zatt]), np.array([0.064])))[0]
        dpl = (Pp - face_pt) @ nn_
        Pp -= np.clip(-dpl, 0, None)[..., None] * nn_
        # foot: three crisp axe-cut planes - heel cut bearing on the heel block, level seat on the sole,
        # and a 45 deg bevel taking off the heel's top corner
        stop = bot.copy()
        d1 = (Pp - stop) @ hz
        Pp -= np.clip(d1, 0, None)[..., None] * hz
        Pp[..., 2] = np.maximum(Pp[..., 2], Zf)
        n_up = unit(np.array([0, 0, 1.0]) - ax[2] * ax)          # the pole's upper surface normal
        n3 = unit(hz + n_up)
        p3 = stop + np.array([0, 0, Zf + 0.135 - stop[2]])
        d3 = (Pp - p3) @ n3
        Pp -= np.clip(d3, 0, None)[..., None] * n3
        Pp = Pp.reshape(1, -1, 3)
        T = tmpl_rings(n, m, cap0=True, cap1=True)
        Pp = add_caps(Pp, T)
        T = orient(T, Pp[0])
        P_p.add(Pp, T, mat="M_timber_weathered", smooth="all")
        # branch stubs (dia 4-7 cm, 2-4 cm proud, axe-trimmed flat ends), angled toward the tree top
        for tk, ak, dk in knots:
            jt = np.argmin(np.abs(t - tk))
            dirr = math.cos(ak) * ex + math.sin(ak) * ey
            base = cen[jt] + dirr * (rad[jt] - 0.01)
            out = unit(dirr * 0.85 - ax * 0.35)
            ln = 0.012 + rng.uniform(0.02, 0.04) / max(out @ dirr, 0.5)
            path = base + out * np.array([0.0, 0.25, 0.55, 0.85, 1.0])[:, None] * ln
            # flared boss -> broken stub with a ragged, slightly domed end
            rag = 1 + rng.uniform(-0.12, 0.12, 12)
            prof_k = np.array([circle_prof(dk / 2 * f, 12) * (rag[:, None] if f < 1.0 else 1.0)
                               for f in (1.7, 1.25, 1.02, 0.95, 0.75)])
            Pk, Tk = sweep(path[None], prof_k[None], up=ax)
            P_p.add(Pk, Tk, mat="M_timber_weathered", smooth="all")
        nknot_foot = int(sum(1 for sk in kd if sk <= 2.5))
        log("prop %d: %d rings x %d sides (ring spacing %.3f m), checks %s, knots %d (%d within 2.5 m of the foot)"
            % (idx, n, m, dt * Lp, [(round(a, 2), round(b, 2)) for a, b in checks], nk, nknot_foot))
        # ---- head: timber cleat under the pole, collar lugs (clevis ears) and a through-bolt ----
        Lt = LEAN_R @ tt_
        latc = float((top - lean(face_map(k, np.array([0.0]), np.array([zatt]), np.array([0.0])))[0]) @ Lt)
        cle = lean(face_map(k, np.array([latc]), np.array([zatt - 0.23]), np.array([0.095])))[0]
        member(P_p, 0, (cle - LEAN_R @ np.array([0, 0, 0.13]))[None], (cle + LEAN_R @ np.array([0, 0, 0.13]))[None],
               0.18, 0.09, up=nn_, c=0.015, rng=rng, bow=0.004)
        prof_b = np.array([(0.0, 0.0), (0.02, 0.0), (0.02, 0.009), (0.013, 0.014), (0.0, 0.015)])
        zear = (Z_COLLAR - 0.03 + zatt - 0.16) / 2
        hear = (Z_COLLAR - 0.03) - (zatt - 0.16)
        for sg in (-1, 1):
            lq = latc + sg * 0.092
            # lug plate lying on the collar strap, bolted through it
            a_ = lean(face_map(k, np.array([lq]), np.array([Z_COLLAR + 0.03]), np.array([0.068])))[0]
            b_ = lean(face_map(k, np.array([lq]), np.array([Z_COLLAR - 0.03]), np.array([0.068])))[0]
            member(P_i, "M_iron", a_[None], b_[None], 0.07, 0.010, up=nn_, c=0.002)
            bh = lean(face_map(k, np.array([lq]), np.array([Z_COLLAR + 0.005]), np.array([0.073])))
            Pb, Tb = lathe(prof_b[None], 6)
            Rb = frame_mats(Lt[None], np.cross(nn_, Lt)[None], nn_[None])
            P_i.add(xform(Pb, Rb, bh), Tb, mat="M_iron", smooth="none")
            # ear standing out from the face on each side of the pole head
            a_ = lean(face_map(k, np.array([lq]), np.array([zear]), np.array([0.058])))[0]
            b_ = lean(face_map(k, np.array([lq]), np.array([zear]), np.array([0.26])))[0]
            member(P_i, "M_iron", a_[None], b_[None], hear, 0.010, up=Lt, c=0.003)
        # through-bolt across the ears and the pole head, nuts outside
        ybolt = 0.175
        pa = lean(face_map(k, np.array([latc - 0.115]), np.array([zatt - 0.08]), np.array([ybolt])))[0]
        pb = lean(face_map(k, np.array([latc + 0.115]), np.array([zatt - 0.08]), np.array([ybolt])))[0]
        Pbt, Tbt = sweep(np.stack([pa, pb])[None], circle_prof(0.011, 8), up=nn_)
        P_i.add(Pbt, Tbt, mat="M_iron", smooth="all")
        for sg, pq in ((-1, pa), (1, pb)):
            Pb, Tb = lathe(prof_b[None], 6)
            Rb = frame_mats(nn_[None], np.cross(Lt * sg, nn_)[None], (Lt * sg)[None])
            P_i.add(xform(Pb, Rb, (pq - Lt * sg * 0.018)[None]), Tb, mat="M_iron", smooth="none")
        # strap band around the pole below the head
        for o in (0.32,):
            c = top + ax * o
            a = np.linspace(0, 2 * PI, 21)[:-1]
            rr = 0.077 + 0.025 * o / Lp + 0.006
            ring = c + rr * (np.cos(a)[:, None] * ex + np.sin(a)[:, None] * ey)
            Pr, Tr = sweep(ring[None], rect_prof(0.006, 0.045, 0.002), up=ax, closed=True)
            P_i.add(Pr, Tr, mat="M_iron", smooth="bevel")
        # ---- ground: rough sunk stone pad, hewn sole + heel block forming the bird's mouth that receives
        # the axe-cut foot, hewn cheeks with an iron pin through cheeks and foot ----
        ang_h = math.atan2(hz[1], hz[0])
        Rg = frame_mats(hz[None], unit(np.cross([0, 0, 1.0], hz))[None], np.array([[0, 0, 1.0]]))[0]
        sv = Rg[:, 1]

        def place(P, along, lat, z):
            return xform(P, Rg, (bot + hz * along + sv * lat) * np.array([1, 1, 0]) + np.array([0, 0, z]))
        # pad: irregular rough stone 0.55-0.75 m across, uneven top (+-2 cm), only 5-9 cm above ground
        Lpad, Wpad = rng.uniform(0.62, 0.75), rng.uniform(0.55, 0.65)
        Pst, Tst = stone_local(rng, [Lpad], [Wpad], [0.26], "boulder", rot_deg=(0.5, 0.5, 2))
        u_ = Pst / np.array([Lpad / 2, 0.13, Wpad / 2])
        Pst[:, :, 1] += 0.02 * noise_field(u_ * 1.2, rng, nterms=3, fmin=1.0, fmax=2.2) * np.clip(u_[:, :, 1] + 1, 0, 1) / 2
        Rm = Rg @ frame_mats(np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]), np.array([[0, -1.0, 0]]))[0]
        pad_c = (bot - hz * 0.10) * np.array([1, 1, 0]) + np.array([0, 0, 0.07])
        Wpad_ = xform(Pst, Rm, pad_c[None])
        P_a.add(Wpad_, Tst, Pl=Pst, mat="M_stone", smooth="all")
        # sole bears on the pad's highest point under it
        Zs0 = float(Wpad_[0, :, 2].max()) + 0.002
        Zs1 = Zf
        Ps, Ts = hewn_beam(rng, 0.56, 0.30, Zs1 - Zs0, nx=10, chamfer=(0.015, 0.025), checks=(0, 1),
                           check_len=(0.2, 0.35), end_split=1)
        P_a.add(place(Ps, -0.12, 0.0, (Zs0 + Zs1) / 2), Ts, Pl=Ps[0], mat="M_timber", smooth="bevel")
        Ph, Th = hewn_beam(rng, 0.16, 0.30, 0.12, nx=6, chamfer=(0.015, 0.025), checks=(0, 0), end_split=1)
        P_a.add(place(Ph, 0.003 + 0.08, 0.0, Zs1 + 0.06), Th, Pl=Ph[0], mat="M_timber", smooth="bevel")
        # treenails through the heel block into the sole
        prof_tn = np.array([(0.0, 0.0), (0.014, 0.0), (0.014, 0.008), (0.011, 0.013), (0.0, 0.014)])
        Ptn, Ttn = lathe(np.repeat(prof_tn[None], 2, 0), 8)
        P_a.add(Ptn + np.stack([place(np.array([[[0.0, 0, 0]]]), 0.083, l_, Zs1 + 0.12)[0, 0] for l_ in (-0.08, 0.08)])[:, None],
                Ttn, mat="M_timber", smooth="all")
        # foot centre: axis point 12 cm above the seat
        tf = (top[2] - (Zf + 0.12)) / (top[2] - bot[2])
        foot_c = top + axis * tf + side * bow * math.sin(min(tf, 1.0) * PI)
        rf = 0.075 + 0.025 * min(tf, 1.0)
        lat_f = float((foot_c - bot) @ sv)
        along_f = float((foot_c - bot) @ hz)
        for sg in (-1, 1):
            Pc, Tc = hewn_beam(rng, 0.30, 0.07, 0.13, nx=7, chamfer=(0.015, 0.022), checks=(0, 0),
                               end_split=-1 if sg > 0 else 1)
            P_a.add(place(Pc, along_f - 0.06, lat_f + sg * (rf + 0.012 + 0.035), Zs1 + 0.065), Tc, Pl=Pc[0],
                    mat="M_timber", smooth="bevel")
        pc = foot_c - hz * 0.06
        pc[2] = Zf + 0.075
        pin = np.stack([pc - sv * (rf + 0.11), pc + sv * (rf + 0.11)])
        Ppn, Tpn = sweep(pin[None], circle_prof(0.012, 8), up=(0, 0, 1))
        P_a.add(Ppn, Tpn, mat="M_iron", smooth="all")
        for sg, q in ((-1, pin[0]), (1, pin[1])):
            Pb, Tb = lathe(np.array([[(0.0, 0.0), (0.024, 0.0), (0.022, 0.01), (0.012, 0.016), (0.0, 0.017)]]), 8)
            Rb = frame_mats(hz[None], np.cross(sv * sg, hz)[None], (sv * sg)[None])
            P_a.add(xform(Pb, Rb, q[None]), Tb, mat="M_iron", smooth="all")
        # ring of 4-6 small half-buried stones and a soil lip round the pad
        nr_ = int(rng.integers(4, 7))
        aa = np.sort(rng.uniform(0, 2 * PI, nr_))
        rr_ = rng.uniform(0.33, 0.42, nr_)
        cs = np.stack([pad_c[0] + rr_ * np.cos(aa), pad_c[1] + rr_ * np.sin(aa), np.zeros(nr_)], 1)
        sz = rng.uniform(0.06, 0.14, nr_)
        Pr, Tr = stone_local(rng, sz * 1.2, sz * 0.9, sz * 0.7, "boulder", rot_deg=(8, 8, 10))
        Pr[:, :, 1] += (sz * 0.35)[:, None]
        Rr = euler(rng.normal(0, 0.15, nr_), rng.normal(0, 0.15, nr_), rng.uniform(0, 2 * PI, nr_))
        cs[:, 2] = sz * rng.uniform(0.05, 0.2, nr_)
        P_a.add(xform(Pr, Rr, cs), Tr, Pl=Pr, mat="M_stone", smooth="all")
        a_l = np.linspace(0, 2 * PI, 33)[:-1]
        rl = np.array([0.36, 0.40, 0.46, 0.52])
        zl = np.array([-0.01, 0.035, 0.03, -0.01])
        G = []
        for r_, z_ in zip(rl, zl):
            wob = 1 + 0.08 * np.sin(a_l * 3 + idx) + 0.05 * np.sin(a_l * 5 + 1.3 * idx)
            G.append(np.stack([pad_c[0] + r_ * wob * np.cos(a_l), pad_c[1] + r_ * wob * np.sin(a_l) * 0.92,
                               z_ * (1 + 0.3 * np.sin(a_l * 4 + idx))], 1))
        G = np.array(G).transpose(1, 0, 2)
        add_grid(P_a, "M_soil", G, wrap=True, flip=False)
        defs[idx] = (top, bot, k, zatt)
    # cross brace between the two long props at ~3 m with bolts
    def at_z(top, bot, z):
        tt = (top[2] - z) / (top[2] - bot[2])
        return top + (bot - top) * tt
    a = at_z(defs[0][0], defs[0][1], 3.1)
    b = at_z(defs[1][0], defs[1][1], 3.3)
    member(P_p, 0, a[None], b[None], 0.11, 0.09, up=(0, 0, 1), c=0.015, rng=rng, bow=0.02)
    return defs


def moss_cushion(rng, n, wmin, wmax, hmin, hmax):
    """Low lumpy moss cushions: local x/z footprint, y up (thickness). Returns (P (n,nv,3), T)."""
    m = 14
    prof = []
    for i in range(n):
        rr = np.array([1.0, 0.96, 0.85, 0.66, 0.38, 0.0])
        zz = np.array([0.0, 0.28, 0.58, 0.82, 0.96, 1.0])
        prof.append(np.stack([rr, zz], 1))
    P, T = lathe(np.array(prof), m)
    W = rng.uniform(wmin, wmax, n)
    D = W * rng.uniform(0.55, 0.9, n)
    Hh = rng.uniform(hmin, hmax, n)
    u = P.copy()
    P = np.stack([P[:, :, 0] * W[:, None] / 2, P[:, :, 2] * Hh[:, None], P[:, :, 1] * D[:, None] / 2], -1)
    P[:, :, 1] *= 1 + 0.45 * noise_field(u * 1.5, rng, nterms=3, fmin=1.5, fmax=3.0)
    P[:, :, 0] *= 1 + 0.3 * noise_field(u, rng, fmin=1.2, fmax=2.8)
    P[:, :, 2] *= 1 + 0.3 * noise_field(u * 1.2, rng, fmin=1.2, fmax=2.8)
    P[:, :, 1] -= 0.012                                   # tucked into the shingle gaps
    return P, flip_tmpl(T) if False else T


def build_moss(parts):
    """Optional low moss cushions (M_moss_clump) on the apron's shake butts (mostly the shaded north side)
    and on a few cap eave shingles."""
    P_m = parts["moss"]
    rng = RNG("moss")
    ca, sa = math.cos(AP_A), math.sin(AP_A)
    n = 14
    phi = np.concatenate([rng.normal(PI, 0.7, 10), rng.uniform(-PI, PI, 4)])
    sc = rng.choice([0.25, 0.85, 1.45], n) + rng.uniform(-0.05, 0.05, n)
    P, T = moss_cushion(rng, n, 0.28, 0.55, 0.014, 0.028)
    Rf, er, nrm = cone_frame(phi, AP_A)
    # local (x along slope, y normal, z around) from cushion (x, y=up, z)
    ctr = er * (AP_RE - sc * ca)[:, None] + np.stack([0 * sc, 0 * sc, AP_ZE + sc * sa], 1) + nrm * 0.058
    Rl = rotm([0, 1, 0], rng.uniform(-0.4, 0.4, n))
    P_m.add(xform(P, Rf @ Rl, ctr), T, Pl=P, mat="M_moss_clump", smooth="all")
    # cap eave: a few small cushions on the shaded back / side faces (cap is yawed + leaned)
    k = 6
    P, T = moss_cushion(rng, k, 0.1, 0.22, 0.02, 0.04)
    tt = rng.uniform(0.05, 0.25, k)
    xs = rng.uniform(-1.1, 0.5, k)
    ys = np.where(rng.random(k) < 0.5, 1.0, -1.0) * (CAP_B - tt * CAP_SB)
    zs = cap_z(xs, ys) + 0.035
    sig = np.arctan(cap_dh(tt) / CAP_SB)
    o = np.stack([0 * ys, np.sign(ys), 0 * ys], 1)
    upv = np.sin(sig)[:, None] * o + np.cos(sig)[:, None] * np.array([0, 0, 1.0])
    slope = -np.cos(sig)[:, None] * o + np.sin(sig)[:, None] * np.array([0, 0, 1.0])
    R = frame_mats(capw(slope), capw(upv), np.cross(capw(slope), capw(upv)))
    W = xform(P, R, capw(np.stack([xs, ys, zs], 1)))
    P_m.add(lean(W), T, Pl=P, mat="M_moss_clump", smooth="all")


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
    """Blades vs stocks/arm straps and sail-A lattice/boards vs wind-wheel (voxel proximity)."""
    def loc(V):
        d = V - HUB
        return np.stack([d @ E1, d @ E2, d @ S_AX], 1)
    bl = loc(part_samples(parts["wheel_blades"], 0.01))
    stocks = np.concatenate([loc(part_samples(parts["sail_%s_stock" % L], 0.01)) for L in "ABCD"] +
                            [loc(part_samples(parts["sail_C_counterweight"], 0.01))])
    g1 = voxel_min_gap(bl, stocks, 0.06)
    log("ROTOR wind-wheel blades vs stocks/arms: min gap %.3f m %s" % (g1, "(PASS)" if g1 > 0.015 else "(FAIL)"))
    wheel = np.concatenate([loc(part_samples(parts[k], 0.01)) for k in ("wheel_blades", "wheel_rim", "wheel_spokes")])
    lat = np.concatenate([loc(part_samples(parts["sail_A_%s" % s], 0.01)) for s in ("bars", "hemlaths", "boards", "whip")])
    g2 = voxel_min_gap(lat, wheel, 0.06)
    log("ROTOR sail A boards/bars vs wind-wheel: min gap %.3f m %s" % (g2, "(PASS)" if g2 > 0.015 else "(FAIL)"))
    sA = np.concatenate([loc(part_samples(parts["sail_A_%s" % s], 0.01)) for s in ("boards",)])
    stA = loc(part_samples(parts["sail_A_stock"], 0.01))
    g3 = voxel_min_gap(sA, stA, 0.06)
    log("ROTOR sail A boards vs stock + clamps: min gap %.3f m %s" % (g3, "(PASS)" if g3 > 0.004 else "(FAIL)"))
    # blade-to-blade spacing (ref1 near-continuous annulus)
    for r in (2.5, BL_R1):
        s_ = np.clip((r - BL_R0) / (BL_R1 - BL_R0), 0, 1)
        w = BL_W0 + (BL_W1 - BL_W0) * s_
        log("WHEEL r=%.2f: blade width %.3f, pitch %.3f, gap %.3f m" % (r, w, 2 * PI * r / 16, 2 * PI * r / 16 - w))
    return g1, g2


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
    w0, w1, r1 = -3.0, 1.2, 6.4
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
        prop_anchors=Part("MILL_prop_anchors", ["M_stone", "M_timber", "M_iron", "M_soil"]),
        prop_iron=Part("MILL_prop_iron", ["M_iron"]),
        moss=Part("MILL_moss_clumps", ["M_moss_clump"], angle=60.0),
    )
    for L in "ABCD":
        parts["sail_%s_stock" % L] = Part("MILL_sail_%s_stock" % L, ["M_timber_weathered", "M_iron"])
    parts["sail_A_whip"] = Part("MILL_sail_A_whip", TW)
    parts["sail_A_bars"] = Part("MILL_sail_A_bars", TW)
    parts["sail_A_hemlaths"] = Part("MILL_sail_A_hemlaths", TW)
    parts["sail_A_boards"] = Part("MILL_sail_A_boards", TW)
    parts["sail_C_counterweight"] = Part("MILL_sail_C_counterweight", ["M_iron"])

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
    log("lowest rotating point z = %.3f m (apron top %.2f m, ground 0)" % (lowest, AP_ZT))
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
    bpy.context.preferences.filepaths.save_version = 0     # no .blend1 backups in the building folder
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    log("saved", OUT_BLEND, "%.1f MB" % (os.path.getsize(OUT_BLEND) / 1e6))


if __name__ == "__main__":
    main()
