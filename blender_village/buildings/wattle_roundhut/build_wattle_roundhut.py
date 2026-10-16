"""Wattle-and-Daub Round Hut with Shingle Cone (HUT) -- deterministic procedural build.

Geometry only (named placeholder material slots, UVs on every mesh).

Run:  /opt/bpyenv/bin/python build_wattle_roundhut.py
Saves wattle_roundhut.blend next to this script.

Layout (metres, Z up, hut centred on the world origin, door centred on -Y):
  * dry-stone boulder plinth ring (outer dia ~7.5 m, top ~0.38 m), chinking, rubble, earth apron
    with a drip-line trench, flat stepping-stone path to the door
  * 14 round-hewn posts, woven wattle (stakes + tapered rods, real in/out weave), daubed bays
    (big eroded bay left of the door, full bay back right, partial patch on the +X side)
  * curved, scarf-jointed and pegged wall plate
  * projecting flat-fronted door frame (jambs, lintel on door posts, wattle side panels,
    cheek panels), worn timber sill on a threshold stone, step stone, ledged & braced plank
    leaf open ~75 deg inward with strap hinges / pintles / ring pull / latch bar
  * 28 pole rafters (uneven, some split ends) on the plate, purlin rings, batten rings, hub
  * 17-course individually modelled shingle cone (convex, eave kick, faceted between
    rafters), doubled starter, slipped / split / missing shingles
  * lead-hat apex collar with standing seams + upper collar + turned finial and spike
Interior: earth floor, daubed inner skin, hearth ring.
All randomness is seeded; the script is reproducible bit-for-bit.
"""
import math
import os
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "wattle_roundhut.blend")
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# =============================================================================================
# materials
# =============================================================================================
MAT_COL = {
    "M_stone": (0.52, 0.50, 0.46), "M_stone_dressed": (0.66, 0.64, 0.6), "M_rubble": (0.5, 0.48, 0.44),
    "M_timber": (0.33, 0.24, 0.16), "M_timber_weathered": (0.42, 0.39, 0.35),
    "M_roof_shingle": (0.36, 0.38, 0.27), "M_wattle": (0.30, 0.24, 0.17), "M_daub": (0.70, 0.66, 0.58),
    "M_lead": (0.30, 0.31, 0.33), "M_iron": (0.10, 0.10, 0.11), "M_earth": (0.36, 0.31, 0.24),
    "M_moss_clump": (0.25, 0.35, 0.15),
}
MATS = {}


def get_mat(name):
    if name not in MATS:
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*MAT_COL.get(name, (0.5, 0.5, 0.5)), 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*MAT_COL.get(name, (0.5, 0.5, 0.5)), 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
        MATS[name] = m
    return MATS[name]


# =============================================================================================
# noise
# =============================================================================================
_NRS = np.random.RandomState(4711)
_PERM = np.tile(_NRS.permutation(256), 2)
_GV = _NRS.uniform(-1.0, 1.0, 256)


def vnoise(p):
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
            pxy = _PERM[_PERM[ix] + iy]
            for dz in (0, 1):
                wz = w[:, 2] if dz else 1.0 - w[:, 2]
                iz = (i0[:, 2] + dz) & 255
                res += _GV[_PERM[pxy + iz]] * wx * wy * wz
    return res.reshape(shp)


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
# mesh accumulator
# =============================================================================================
class Acc:
    def __init__(self, name, sharp_angle=40.0):
        self.name = name
        self.V, self.UV = [], []
        self.Fidx, self.Fsz, self.Fmat, self.Fsm, self.Fwrap = [], [], [], [], []
        self.n = 0
        self.mats = []
        self.sharp_angle = sharp_angle

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, V, faces, mat, uv=None, wrap=False, smooth=True):
        V = np.asarray(V, float).reshape(-1, 3)
        if len(V) == 0:
            return
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

    def build(self, coll):
        V = np.concatenate(self.V)
        if self.name != "HUT_ground_apron":
            V[:, 2] = np.maximum(V[:, 2], Z_MIN + 0.004)
        UVv = np.concatenate(self.UV)
        fidx = np.concatenate(self.Fidx)
        fsz = np.concatenate(self.Fsz)
        fmat = np.concatenate(self.Fmat)
        fsm = np.concatenate(self.Fsm)
        fwrap = np.concatenate(self.Fwrap)
        me = bpy.data.meshes.new(self.name)
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
            me.materials.append(get_mat(m))
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
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        log(f"  {self.name}: {len(V)} verts, {len(fsz)} faces")
        return ob


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


def stone(half, r_frac, segs, rng, amp=0.02, freq=3.0, flat_top=None, flat_bot=None):
    """lumpy rounded boulder in local coords."""
    h = np.asarray(half, float)
    r = r_frac * float(h.min())
    P, F = rbox(h, r, segs, chamfer=False)
    dirn = nrm(P / h)
    off = rng.uniform(-100, 100, 3)
    d = fbm(P * freq + off, 3) * amp + fbm(P * freq * 3.1 + off * 1.7, 2) * amp * 0.3
    P = P + dirn * d[:, None]
    if flat_top is not None:
        P[:, 2] = np.minimum(P[:, 2], flat_top + (P[:, 2] - flat_top) * 0.15)
    if flat_bot is not None:
        P[:, 2] = np.maximum(P[:, 2], flat_bot)
    return P, F


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


# =============================================================================================
# global dimensions
# =============================================================================================
Z_MIN = -0.095               # lowest point (apron rim); everything else sits above
R_WALL = 3.50                 # wattle centre line / post centre line
WALL_POST_AZ_DOOR = math.radians(21.0)
N_POSTS = 14
Z_WATTLE0 = 0.40
PITCH = math.radians(51.0)
R_EAVE = 4.13                 # roof reference surface radius at the eave
Z_EAVE = 2.395                # roof reference surface height at the eave
N_RAFT = 28
RAFT_R = 0.055
BATTEN_T = 0.03
SH_EXPOSE = 0.318
SH_LEN = 0.72
N_COURSES = 17
COLLAR_R = 0.73
COLLAR_PITCH = math.radians(44.0)
FINIAL_TIP = 8.60
DOOR_W = 1.00
SILL_TOP = 0.20
HEAD_Z = SILL_TOP + 2.08       # 2.28
FRONT_Y = -3.72                # front plane of the projecting door frame
RAFT_AZ0 = math.pi / N_RAFT    # no rafter on the door axis


# ---------------------------------------------------------------------------------------------
# roof reference surface (top of battens == underside of shingle stack)
# ---------------------------------------------------------------------------------------------
def build_profile():
    ds = 0.004
    s = np.arange(0, 6.4, ds)
    alpha = PITCH - math.radians(4.0) * (1 - smoothstep(0.0, 0.55, s))
    r = R_EAVE - np.concatenate([[0], np.cumsum(np.cos(alpha[:-1]) * ds)])
    z = Z_EAVE + np.concatenate([[0], np.cumsum(np.sin(alpha[:-1]) * ds)])
    s_top = float(np.interp(0.0, -r, s))         # where straight profile reaches the axis
    b = 0.07 * np.sin(np.pi * np.clip(s / (s_top * 0.92), 0, 1)) ** 1.2
    r = r + b * np.sin(alpha)
    z = z + b * np.cos(alpha)
    keep = r > 0.18
    return s[keep], r[keep], z[keep], alpha[keep]


PS, PR, PZ, PA = build_profile()
WAVE_Z = None


def wave_z(theta):
    w = ring_noise(theta, 31, 7, 0.028)
    # keep the eave over the door from dipping (door at az 0 => theta = -pi/2)
    dd = np.angle(np.exp(1j * (theta + np.pi / 2)))
    return w + 0.02 * np.exp(-(dd / 0.35) ** 2) * (w < 0.0) * np.abs(w) / 0.02


def wave_r(theta):
    return ring_noise(theta, 57, 6, 0.025)


def facet(theta):
    d = 2 * np.pi / N_RAFT
    th_az = theta + np.pi / 2          # theta (math angle) -> azimuth from -Y
    ph = np.mod(th_az - RAFT_AZ0, d) - d / 2
    return math.cos(d / 2) / np.cos(ph)


def surf(theta, s):
    """theta: math angle (x=cos, y=sin). s: slope distance from the eave."""
    theta, s = np.broadcast_arrays(np.asarray(theta, float), np.asarray(s, float))
    R = np.interp(s, PS, PR)
    Z = np.interp(s, PS, PZ)
    fade = 1 - 0.75 * smoothstep(0.0, 3.5, s)
    R = R * facet(theta) + wave_r(theta) * fade
    # extrapolate below the eave along the eave tangent
    ext = np.minimum(s, 0.0)
    a0 = PA[0]
    R = R - ext * math.cos(a0)
    Z = Z + ext * math.sin(a0) + wave_z(theta) * fade
    return np.stack([R * np.cos(theta), R * np.sin(theta), Z], -1)


def surf_frame(theta, s):
    P = surf(theta, s)
    eps_s, eps_t = 2e-3, 2e-4
    ts = nrm(surf(theta, s + eps_s) - surf(theta, s - eps_s))
    tt = nrm(surf(theta + eps_t, s) - surf(theta - eps_t, s))
    n = nrm(np.cross(tt, ts))
    return P, ts, tt, n


def az2th(az):
    return np.asarray(az, float) - np.pi / 2


def s_at_r(r):
    return float(np.interp(-r, -PR, PS))


S_END = s_at_r(0.42)        # shingles terminate under the collar here


def rafter_center(theta, s):
    P, ts, tt, n = surf_frame(theta, s)
    return P - n * (BATTEN_T + RAFT_R), ts, tt, n


def rafter_underside_z_at_r(r):
    th = az2th(RAFT_AZ0)
    ss = np.linspace(0, 3.0, 600)
    C, ts, tt, n = rafter_center(np.full_like(ss, th), ss)
    rr = np.hypot(C[:, 0], C[:, 1])
    zc = np.interp(-r, -rr, C[:, 2])
    nz = np.interp(-r, -rr, n[:, 2])
    return zc - RAFT_R / max(nz, 0.3)


PLATE_TOP = float(rafter_underside_z_at_r(R_WALL + 0.09)) + 0.03
PLATE_H = 0.20
PLATE_BOT = PLATE_TOP - PLATE_H
WATTLE_TOP = PLATE_BOT


# =============================================================================================
# collection
# =============================================================================================
def make_collection():
    coll = bpy.data.collections.new("HUT")
    bpy.context.scene.collection.children.link(coll)
    return coll


# =============================================================================================
# posts
# =============================================================================================
def post_azimuths():
    rng = np.random.RandomState(101)
    a0 = WALL_POST_AZ_DOOR
    span = 2 * math.pi - 2 * a0
    az = [a0]
    for k in range(1, N_POSTS - 1):
        az.append(a0 + k * span / (N_POSTS - 1) + math.radians(rng.uniform(-1.2, 1.2)))
    az.append(2 * math.pi - a0)
    return np.array(az)


POST_AZ = post_azimuths()


def round_post(acc, base, top, rad, rng, sides=14, check=False):
    nseg = 14
    t = np.linspace(0, 1, nseg)
    lean = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]) * math.tan(math.radians(0.7))
    H = top[2] - base[2]
    bow = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]) * 0.012
    path = base[None, :] + np.outer(t, top - base) + np.outer(t * H, lean) + np.outer(np.sin(np.pi * t), bow)
    taper = rad * (1 + 0.05 * (0.5 - t)) + rng.uniform(-0.005, 0.005)
    ang = 2 * np.pi * np.arange(sides) / sides + rng.uniform(0, 1)
    # adze flats: random per-side flattening, slowly varying along the length
    flat = rng.uniform(0.0, 1.0, sides)
    prof = []
    seed = rng.randint(1000)
    for i, tt in enumerate(t):
        rr = 1 - 0.06 * flat * (0.6 + 0.4 * np.sin(tt * 5 + flat * 6)) + 0.025 * n2(ang * 1.3, tt * 4, seed)
        p = np.stack([np.cos(ang) * rr, np.sin(ang) * rr], -1)
        prof.append(p)
    prof = np.array(prof)
    if check:  # drying check: a groove down one face
        k = rng.randint(sides)
        z0, z1 = rng.uniform(0.15, 0.35), rng.uniform(0.6, 0.9)
        m = smoothstep(z0, z0 + 0.06, t) * (1 - smoothstep(z1 - 0.06, z1, t))
        prof[:, k, :] *= (1 - 0.15 * m)[:, None]
    P, F, uv, w = tube(path, taper, sides, up=(1, 0, 0), profile=prof)
    # chamfer ends: shrink end rings slightly
    acc.add(P, F, "M_timber", uv, w)


def build_posts(coll):
    acc = Acc("HUT_posts", 50)
    rng = np.random.RandomState(202)
    for i, az in enumerate(POST_AZ):
        b = az_pt(az, R_WALL, 0.362)
        tp = az_pt(az, R_WALL, PLATE_BOT + 0.01)
        round_post(acc, b, tp, rng.uniform(0.10, 0.12), rng, check=(i % 3 == 1))
    acc.build(coll)


# =============================================================================================
# wattle
# =============================================================================================
def arc_path(r):
    def f(s):
        a = np.asarray(s, float) / r
        pt = np.stack([np.sin(a) * r, -np.cos(a) * r], -1)
        nn = np.stack([np.sin(a), -np.cos(a)], -1)
        return pt, nn
    return f


def line_path(p0, p1, nout):
    p0 = np.asarray(p0, float)
    d = nrm(np.asarray(p1, float) - p0)
    nout = np.asarray(nout, float)

    def f(s):
        s = np.asarray(s, float)
        pt = p0 + s[..., None] * d
        return pt, np.broadcast_to(nout, pt.shape)
    return f


def weave_offset(s, stakes, signs, A):
    k = np.clip(np.searchsorted(stakes, s) - 1, 0, len(stakes) - 2)
    s0, s1 = stakes[k], stakes[k + 1]
    t = np.clip((s - s0) / (s1 - s0), 0, 1)
    c = 0.5 * (1 + np.cos(np.pi * t))
    return A * (signs[k] * c + signs[k + 1] * (1 - c))


def weave_panel(rods, stakes_acc, pathf, s0, s1, z0, z1, seed, hide=None, n_stakes=None,
                end_stakes=True, stake_bottom=None):
    """woven panel between s0 and s1 (ends are hidden in posts/jambs)."""
    rng = np.random.RandomState(seed)
    L = s1 - s0
    if n_stakes is None:
        n_stakes = max(1, int(round(L / 0.29)) - 1)
    st = np.linspace(s0, s1, n_stakes + 2)
    st[1:-1] += rng.uniform(-0.025, 0.025, n_stakes)
    real_st = st[1:-1]
    # stakes
    zb = z0 - 0.07 if stake_bottom is None else stake_bottom
    for k, ss in enumerate(real_st):
        r = rng.uniform(0.019, 0.026)
        if hide is not None and hide(np.full(5, ss), np.linspace(z0, z1, 5), 0.0).all():
            continue
        zz = np.linspace(zb, z1 + 0.03, 12)
        pt, nn = pathf(np.full(12, ss))
        wob = 0.008 * n2(zz * 1.5, np.full(12, ss * 3.0), seed + k)
        tang = np.stack([nn[:, 1], -nn[:, 0]], -1)
        xy = pt + tang * wob[:, None] + nn * (0.006 * n2(zz * 2.0, np.full(12, ss), seed + 50 + k))[:, None]
        path = np.c_[xy, zz]
        path, rr = chamfer_path(path, r, 0.006)
        P, F, uv, w = tube(path, rr, 8, up=(nn[0, 0], nn[0, 1], 0))
        stakes_acc.add(P, F, "M_wattle", uv, w)
    # rods
    z = z0 + 0.014
    row = 0
    r_row = rng.uniform(0.0105, 0.0175)
    shared_seed = seed * 3 + 1
    while z < z1 - 0.012:
        paired = rng.rand() < 0.12
        split = rng.rand() < 0.22
        A = 0.020 + r_row * 0.8
        signs = np.array([(-1) ** (k + row) for k in range(len(st))], float)
        pieces = []
        if split and L > 0.6:
            ks = rng.randint(1, len(st) - 1) if len(st) > 2 else 1
            sm = st[ks]
            pieces.append((s0 - 0.01, min(s1, sm + 0.33), -0.005, 1))
            pieces.append((max(s0, sm - 0.33), s1 + 0.01, 0.005, -1))
        else:
            pieces.append((s0 - 0.01, s1 + 0.01, 0.0, 0))
        for (a, b, dz, tipside) in pieces:
            subs = [(r_row, 0.0)]
            if paired:
                subs = [(r_row * 0.62, -r_row * 0.62), (r_row * 0.6, r_row * 0.62)]
            for (rr0, dzz) in subs:
                n = max(4, int((b - a) / 0.036) + 1)
                ss = np.linspace(a, b, n)
                zz = (z + dz + dzz + 0.012 * n2(ss * 1.2, np.full(n, z * 2.2), shared_seed)
                      + 0.004 * n2(ss * 3.0, np.full(n, z * 9.0), seed + row))
                if hide is not None and hide(ss, zz, 0.012).all():
                    continue
                off = weave_offset(ss, st, signs, A)
                if tipside != 0:
                    # free tip end flicks outward from the face (a visible stub)
                    tip = b if tipside > 0 else a
                    tt = 1 - np.clip(np.abs(ss - tip) / 0.1, 0, 1)
                    off = off + 0.035 * tt ** 2 * (1 if rng.rand() < 0.7 else -1)
                pt, nn = pathf(ss)
                xy = pt + nn * off[:, None]
                path = np.c_[xy, zz]
                taper = np.linspace(1.0, 0.68, n) if rng.rand() < 0.5 else np.linspace(0.68, 1.0, n)
                rr = rr0 * taper * (1 + 0.06 * n2(ss * 4, np.full(n, z), seed + 7))
                P, F, uv, w = tube(path, rr, 6, up=(0, 0, 1), phase=rng.uniform(0, 1))
                rods.add(P, F, "M_wattle", uv, w)
        r_next = rng.uniform(0.0105, 0.0175)
        pitch = (r_row if not paired else r_row * 1.24) + r_next + rng.uniform(0.002, 0.007)
        z += pitch
        r_row = r_next
        row += 1


# ---------------------------------------------------------------------------------------------
# daub definitions
# ---------------------------------------------------------------------------------------------
def bay_s(i):
    a0 = POST_AZ[i]
    a1 = POST_AZ[i + 1]
    return a0 * R_WALL, a1 * R_WALL


DAUB_BAYS = {}   # bay index -> function(s, z) -> thickness above wattle centre (m), <=0 => none


def daub_edge_door_bay(s):
    # eroded lower edge, about 0.55 m, ragged and chunky
    return (0.56 + 0.10 * n2(s * 2.2, 0.3, 901) + 0.045 * n2(s * 7.0, 1.7, 902)
            + 0.02 * n2(s * 19.0, 3.1, 903))


def make_daub_fields():
    nb = len(POST_AZ) - 1
    door_bay = nb - 1                      # between POST_AZ[-2] and POST_AZ[-1] (az -45..-21)
    back_bay = 5
    side_bay = 2
    s0, s1 = bay_s(side_bay)
    pc_s = s0 + 0.55 * (s1 - s0)
    pc_z = 1.75

    def door_field(s, z):
        return z - daub_edge_door_bay(s)

    def back_field(s, z):
        return np.minimum(z - (0.50 + 0.05 * n2(s * 3, 0.0, 911)), 1.0)

    def side_field(s, z):
        d = np.hypot((s - pc_s) / 0.55, (z - pc_z) / 0.42)
        return (1.0 - d + 0.22 * n2(s * 3.5, z * 3.5, 921) + 0.06 * n2(s * 11, z * 11, 922)) * 0.35

    DAUB_BAYS[door_bay] = door_field
    DAUB_BAYS[back_bay] = back_field
    DAUB_BAYS[side_bay] = side_field


def daub_hides(bay):
    f = DAUB_BAYS.get(bay)
    if f is None:
        return None

    def hide(s, z, margin):
        return f(s, z) > 0.05 + margin
    return hide


def build_wattle(coll):
    make_daub_fields()
    rods = Acc("HUT_wattle_rods", 60)
    stakes = Acc("HUT_wattle_stakes", 60)
    pathf = arc_path(R_WALL)
    nb = len(POST_AZ) - 1
    for i in range(nb):
        s0, s1 = bay_s(i)
        weave_panel(rods, stakes, pathf, s0 + 0.0, s1 - 0.0, Z_WATTLE0, WATTLE_TOP, 1000 + i * 17,
                    hide=daub_hides(i))
    # door side panels (front plane) between jamb and door post
    for side in (-1, 1):
        x0, x1 = 0.70, 0.91
        p0 = (side * x0, FRONT_Y + 0.11)
        p1 = (side * x1, FRONT_Y + 0.11)
        f = line_path(p0, p1, (0, -1))
        weave_panel(rods, stakes, f, -0.06, (x1 - x0) + 0.06, 0.40, HEAD_Z, 3000 + side, n_stakes=1,
                    stake_bottom=0.33)
        # cheek panels: door post back corner -> wall post
        pa = np.array([side * 1.02, FRONT_Y + 0.17])
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL)[:2]
        L = float(np.linalg.norm(wp - pa))
        d = (wp - pa) / L
        nout = np.array([d[1], -d[0]]) * (1 if side > 0 else -1)
        if nout[0] * side < 0:
            nout = -nout
        f2 = line_path(pa, wp, nout)
        weave_panel(rods, stakes, f2, -0.05, L + 0.02, 0.40, HEAD_Z, 3100 + side, n_stakes=1,
                    stake_bottom=0.33)
    rods.build(coll)
    stakes.build(coll)


def build_daub(coll):
    acc = Acc("HUT_daub", 70)
    for bay, field in DAUB_BAYS.items():
        s0, s1 = bay_s(bay)
        s0 += 0.05
        s1 -= 0.05
        nu = int((s1 - s0) / 0.018) + 1
        nv = int((WATTLE_TOP + 0.02 - 0.42) / 0.018) + 1
        S, Z = np.meshgrid(np.linspace(s0, s1, nu), np.linspace(0.42, WATTLE_TOP + 0.02, nv), indexing="ij")
        f = field(S, Z)
        # thickness (outward from wattle centre): full 0.062 + lumps; collapses behind the rods at edges
        lump = (0.011 * fbm(np.stack([S * 2.5, Z * 2.5, np.full(S.shape, bay * 1.3)], -1), 3)
                + 0.004 * n2(S * 13, Z * 13, bay + 40))
        edge = smoothstep(-0.005, 0.07, f)
        # crumbled lip: a slightly thinner, pitted band right above the break
        pit = 0.012 * np.clip(n2(S * 25, Z * 25, bay + 77), 0, 1) * (1 - smoothstep(0.05, 0.2, f))
        T = -0.035 + (0.097 + lump - pit) * edge
        # fillet against posts at the bay ends
        sp = np.minimum(S - s0, s1 - S)
        T = T + 0.012 * (1 - smoothstep(0.0, 0.12, sp)) * edge
        a = S / R_WALL
        rad = R_WALL + T
        P = np.stack([np.sin(a) * rad, -np.cos(a) * rad, Z], -1)
        rin = R_WALL - 0.05
        Q = np.stack([np.sin(a) * rin, -np.cos(a) * rin, Z], -1)
        V, F = slab(P, Q)
        acc.add(V, F, "M_daub")
    acc.build(coll)


def build_inner_skin(coll):
    acc = Acc("HUT_daub_interior", 70)
    a0 = WALL_POST_AZ_DOOR
    a1 = 2 * math.pi - WALL_POST_AZ_DOOR
    nu = 260
    nv = 30
    A, Z = np.meshgrid(np.linspace(a0, a1, nu), np.linspace(0.17, PLATE_BOT + 0.02, nv), indexing="ij")
    lump = 0.012 * fbm(np.stack([A * 4, Z * 2.5, np.zeros_like(A)], -1), 3)
    ro = R_WALL - 0.052 + 0.0 * lump
    ri = R_WALL - 0.10 + lump
    P = np.stack([np.sin(A) * ri, -np.cos(A) * ri, Z], -1)       # inner face is the visible one
    Q = np.stack([np.sin(A) * ro, -np.cos(A) * ro, Z], -1)
    V, F = slab(Q, P)  # outer = Q (toward wattle) so the slab normals face out on both sides
    acc.add(V, F, "M_daub")
    acc.build(coll)


# =============================================================================================
# wall plate
# =============================================================================================
def build_wall_plate(coll):
    acc = Acc("HUT_wall_plate", 40)
    rng = np.random.RandomState(303)
    joints = list(POST_AZ[::2][:7])           # 7 joints over every other post
    joints.sort()
    hw, hh = 0.09, PLATE_H / 2
    ch = 0.022
    prof = np.array([[hw - ch, -hh], [hw, -hh + ch], [hw, hh - ch], [hw - ch, hh],
                     [-hw + ch, hh], [-hw, hh - ch], [-hw, -hh + ch], [-hw + ch, -hh]])
    zc = PLATE_BOT + hh
    for k in range(7):
        a0 = joints[k]
        a1 = joints[(k + 1) % 7] + (2 * math.pi if k == 6 else 0)
        # overlap past the joints (scarf) by ~0.17 m each side
        e0 = a0 - 0.17 / R_WALL
        e1 = a1 + 0.17 / R_WALL
        n = max(8, int((e1 - e0) * R_WALL / 0.12))
        a = np.linspace(e0, e1, n)
        rr = R_WALL + 0.012 * np.sin(np.pi * (a - e0) / (e1 - e0)) * rng.uniform(-1, 1)
        zz = np.full(n, zc) - 0.012 * np.sin(np.pi * (a - e0) / (e1 - e0)) * rng.uniform(0.3, 1)
        path = np.stack([np.sin(a) * rr, -np.cos(a) * rr, zz], -1)
        pr = np.broadcast_to(prof, (n, 8, 2)).copy()
        # half-lap: the start end keeps only the lower half, the end keeps the upper half (scarf)
        lap0 = (a < a0 + 0.17 / R_WALL)
        lap1 = (a > a1 - 0.17 / R_WALL)
        pr[lap0, :, 1] = np.where(pr[lap0, :, 1] > 0, pr[lap0, :, 1] * 0.0 - 0.004, pr[lap0, :, 1])
        pr[lap1, :, 1] = np.where(pr[lap1, :, 1] < 0, pr[lap1, :, 1] * 0.0 + 0.004, pr[lap1, :, 1])
        # profile coordinates are (radial-ish N=up-projected?)  -> use frames with up=z: N=z, B=T x z
        prof_xy = np.stack([pr[..., 1], -pr[..., 0]], -1)
        P, F, uv, w = tube(path, 1.0, 8, up=(0, 0, 1), profile=prof_xy)
        acc.add(P, F, "M_timber", uv, w)
        # pegs through the laps (driven vertically, heads proud of the top)
        for aj in (a0, a1):
            for d in (-0.07, 0.07):
                p = az_pt(aj + d / R_WALL, R_WALL + rng.uniform(-0.02, 0.02), zc + hh)
                path_p = np.array([p - [0, 0, 0.05], p + [0, 0, rng.uniform(0.012, 0.02)]])
                path_p, rp = chamfer_path(np.linspace(path_p[0], path_p[1], 3), 0.014, 0.004)
                P, F, uv, w = tube(path_p, rp, 8, up=(1, 0, 0))
                acc.add(P, F, "M_timber", uv, w)
    acc.build(coll)


# =============================================================================================
# roof structure
# =============================================================================================
def build_rafters(coll):
    acc = Acc("HUT_rafters", 50)
    rng = np.random.RandomState(404)
    s_hub = s_at_r(0.34)
    for j in range(N_RAFT):
        az = RAFT_AZ0 + j * 2 * math.pi / N_RAFT
        th = float(az2th(az))
        s_tip = rng.uniform(0.04, 0.12)
        ss = np.linspace(s_tip, s_hub, 30)
        C, ts, tt, n = rafter_center(np.full_like(ss, th), ss)
        # sideways crook of a natural pole
        crook = 0.018 * n2(ss * 0.6, np.full_like(ss, j * 1.0), 405) * np.sin(np.pi * (ss - s_tip) / (s_hub - s_tip))
        C = C + tt * crook[:, None]
        r0 = rng.uniform(0.05, 0.06)
        rad = r0 * (1.0 - 0.25 * (ss - s_tip) / (s_hub - s_tip))
        sides = 10
        ang = 2 * np.pi * np.arange(sides) / sides
        prof = np.stack([np.cos(ang), np.sin(ang)], -1) * (1 + 0.04 * n2(ang * 2, np.zeros(sides), j))[:, None]
        split = (j % 5 == 2)
        if split:
            # main pole stops 0.22 m up from the tip; two diverging D-section halves form the split end
            ks = int(np.searchsorted(ss, s_tip + 0.22))
            P, F, uv, w = tube(C[ks:][::-1], rad[ks:][::-1], sides, up=tuple(n[0]), profile=prof)
            acc.add(P, F, "M_timber", uv, w)
            ang2 = np.linspace(-np.pi / 2, np.pi / 2, 8)
            for sgn in (-1, 1):
                seg = C[:ks + 1].copy()
                kk = np.linspace(1, 0, len(seg))
                seg = seg + tt[:ks + 1] * (sgn * (0.004 + 0.014 * kk ** 2))[:, None]
                # frames for a hub->tip path: B = -tt, so the half disc lies on B = -sgn
                dprof = np.stack([np.sin(ang2), -np.cos(ang2) * sgn], -1)
                if sgn < 0:
                    dprof = dprof[::-1]
                pth, rr = chamfer_path(seg[::-1], rad[:ks + 1][::-1], 0.006)
                P, F, uv, w = tube(pth, rr, 8, up=tuple(n[0]), profile=dprof)
                acc.add(P, F, "M_timber", uv, w)
        else:
            pth, rr = chamfer_path(C[::-1], rad[::-1], 0.008)
            # uneven, slightly skewed saw cut at the tip
            sk = rng.uniform(-0.03, 0.03)
            P, F, uv, w = tube(pth, rr, sides, up=tuple(n[0]), profile=prof)
            P = P.reshape(len(pth), sides, 3)
            t_end = nrm(pth[-1] - pth[-2])
            proj = ((P[-2] - pth[-2]) @ tt[0]) / max(rr[-2], 1e-3)
            P[-2:] += t_end[None, None, :] * (sk * proj)[None, :, None]
            acc.add(P.reshape(-1, 3), F, "M_timber", uv, w)
    # hub ring at the apex (rafters converge into it)
    C, ts, tt, n = rafter_center(np.array([0.0]), np.array([s_hub]))
    zc = float(C[0, 2])
    prof = [(0.0, zc - 0.20), (0.36, zc - 0.20), (0.385, zc - 0.17), (0.385, zc + 0.14), (0.36, zc + 0.17), (0.0, zc + 0.17)]
    V, F, uv, w = lathe(prof, 24, rfunc=lambda t, z: 1 + 0.02 * np.sin(3 * t + 1))
    acc.add(V, F, "M_timber", uv, w)
    acc.build(coll)


def build_purlins_battens(coll):
    pur = Acc("HUT_purlin_rings", 50)
    bat = Acc("HUT_battens", 35)
    rng = np.random.RandomState(505)
    d = 2 * math.pi / N_RAFT
    # purlin rings inside (under rafters)
    for sp in (1.25, 2.05, 2.85, 3.65, 4.45):
        az = RAFT_AZ0 + np.arange(N_RAFT + 1) * d
        th = az2th(az)
        C, ts, tt, n = rafter_center(th, np.full_like(th, sp))
        C = C - n * (RAFT_R + 0.035)
        for k in range(N_RAFT):
            p0, p1 = C[k], C[k + 1]
            # extend a little past rafters (lapped / lashed)
            dd = p1 - p0
            path = np.linspace(p0 - dd * 0.06, p1 + dd * 0.06, 5)
            path[:, 2] -= 0.008 * np.sin(np.linspace(0, np.pi, 5))
            path, rr = chamfer_path(path, rng.uniform(0.032, 0.038), 0.006)
            P, F, uv, w = tube(path, rr, 8, up=tuple(n[k]))
            pur.add(P, F, "M_timber", uv, w)
    # batten rings under the shingle courses
    s_list = [0.03] + [k * SH_EXPOSE + 0.08 for k in range(1, N_COURSES + 1)]
    s_list += [N_COURSES * SH_EXPOSE + 0.30]
    for kb, sb in enumerate(s_list):
        if sb > S_END - 0.05:
            continue
        az = RAFT_AZ0 + np.arange(N_RAFT + 1) * d
        th = az2th(az)
        P0, ts, tt, n = surf_frame(th, np.full_like(th, sb))
        Cb = P0 - n * (BATTEN_T / 2)
        rr = float(np.hypot(Cb[0, 0], Cb[0, 1]))
        step = 2 if rr > 1.4 else 3
        k = rng.randint(step)
        starts = list(range(-k, N_RAFT, step))
        for st in starts:
            a = max(st, 0)
            b = min(st + step, N_RAFT)
            if b <= a:
                continue
            p0, p1 = Cb[a], Cb[b]
            # lath runs straight from rafter a to rafter b (chord); overhang 4 cm
            x = p1 - p0
            L = float(np.linalg.norm(x))
            mid = (p0 + p1) / 2
            nmid = nrm(n[a] + n[b])
            R = frame_R(x, nmid)
            hw = 0.025 if kb > 0 else 0.045
            V, F = rbox((L / 2 + 0.03, hw, BATTEN_T / 2), 0.006, (3, 1, 1))
            V = xf(V, R, mid + R[:, 1] * rng.uniform(-0.005, 0.005))
            bat.add(V, F, "M_timber_weathered", smooth=True)
    pur.build(coll)
    bat.build(coll)


# =============================================================================================
# shingles
# =============================================================================================
SH_TPL = box_template(
    [-1.0, -CH_C, -0.55, -0.18, 0.18, 0.55, CH_C, 1.0],
    [-1.0, -CH_C, -0.55, -0.15, 0.25, 0.6, CH_C, 1.0],
    [-1.0, -CH_C, CH_C, 1.0])


def shingle_local(W, L, Tb, Th, rc, cup, curl, rng_vals):
    """one shingle in local coords x across, y along slope from butt(0) to head(L), z up (0..thick)."""
    Vt, F = SH_TPL
    h = np.array([W / 2, L / 2, 0.5])
    r = 0.007
    a = np.abs(Vt)
    hz = 0.5
    P = np.empty_like(Vt)
    hx = np.array([W / 2, L / 2, hz])
    rr = np.array([r, r, 0.12])
    P = np.where(a > 0.999, np.sign(Vt) * hx, Vt / CH_C * (hx - rr))
    q = np.clip(P, -(hx - rr), hx - rr)
    d = (P - q) / rr
    Ld = np.linalg.norm(d, axis=1, keepdims=True)
    P = np.where(Ld > 1e-9, q + d / np.maximum(Ld, 1e-12) * rr, P)
    x = P[:, 0]
    y = P[:, 1] + L / 2
    v = y / L
    zt = (P[:, 2] + hz) / (2 * hz)             # 0 bottom .. 1 top
    thick = Tb - (Tb - Th) * v
    z = zt * thick
    # butt corners rounded in plan
    cx = np.sign(x) * (W / 2 - rc)
    cy = rc
    m = (np.abs(x) > W / 2 - rc) & (y < rc)
    dx = x - cx
    dy = y - cy
    dl = np.hypot(dx, dy)
    sc = np.where(m & (dl > rc * 0.98), rc * (0.98 + 0.02 * zt) / np.maximum(dl, 1e-9), 1.0)
    x = np.where(m, cx + dx * sc, x)
    y = np.where(m, cy + dy * sc, y)
    # ragged hand-split butt
    jag = rng_vals[0] * np.sin(x * rng_vals[1] + rng_vals[2]) * (y < 0.03)
    y = y + jag
    # cup (edges lift) and curl (butt lifts)
    z = z + cup * (2 * x / W) ** 2 + curl * (1 - v) ** 2
    return np.stack([x, y, z], -1), F


def build_shingles(coll):
    acc = Acc("HUT_roof_shingles", 45)
    st_acc = Acc("HUT_roof_starter", 45)
    rng = np.random.RandomState(606)
    B_WEDGE = 0.052
    prev_joints = None
    n_total = 0

    def place(acc_, th_c, s_b, W, L, Tb, Th, phi, lift, cup, curl, base_fn, rc):
        Pl, F = shingle_local(W, L, Tb, Th, rc, cup, curl,
                              (rng.uniform(0.002, 0.006), rng.uniform(25, 60), rng.uniform(0, 6)))
        x, y, z = Pl[:, 0], Pl[:, 1], Pl[:, 2]
        c, s_ = math.cos(phi), math.sin(phi)
        xr = x * c - y * s_
        yr = x * s_ + y * c
        v = np.clip(y / L, 0, 1)
        ss = s_b + yr
        th = np.full_like(ss, th_c)
        P0, ts, tt, n = surf_frame(th, ss)
        # width taper toward the head so neighbours never interpenetrate on the cone
        rb = float(np.hypot(*surf(th_c, s_b)[:2]))
        rcur = np.hypot(P0[:, 0], P0[:, 1])
        xr = xr * np.clip(rcur / rb, 0.3, 1.0)
        off = base_fn(v) + z + lift * (1 - v)
        V = P0 + tt * xr[:, None] + n * off[:, None]
        uv = np.stack([x + 0.5, y], -1)
        acc_.add(V, F, "M_roof_shingle", uv, smooth=True)

    # ---- doubled starter course
    s_b = 0.012
    rb = float(np.hypot(*surf(0.0, s_b)[:2]))
    circ = 2 * math.pi * rb
    n = int(round(circ / 0.44))
    w = rng.uniform(0.75, 1.25, n)
    gaps = rng.uniform(0.005, 0.012, n)
    w = w / w.sum() * (circ - gaps.sum())
    off0 = rng.uniform(0, 2 * math.pi)
    acc_ang = off0
    for i in range(n):
        dth = (w[i] + gaps[i]) / rb
        thc = acc_ang + dth / 2
        acc_ang += dth
        place(st_acc, thc, s_b, w[i], 0.46, 0.028, 0.012, math.radians(rng.uniform(-1.5, 1.5)), 0.0,
              0.002, 0.0, lambda v: 0.0 * v, 0.03)
    starter_joints = np.mod(off0 + np.cumsum((w + gaps) / rb), 2 * math.pi)
    prev_joints = starter_joints

    for k in range(N_COURSES):
        s_b = k * SH_EXPOSE
        cwave = 0.018 * ring_noise(np.linspace(0, 2 * np.pi, 512, endpoint=False), 700 + k, 5, 1.0)
        rb = float(np.hypot(*surf(0.0, s_b)[:2]))
        rmid = float(np.hypot(*surf(0.0, s_b + SH_EXPOSE * 0.5)[:2]))
        circ = 2 * math.pi * rb
        target = 0.44 if k < N_COURSES - 3 else 0.40
        n = max(8, int(round(2 * math.pi * rmid / target)))
        w = rng.uniform(0.76, 1.24, n)
        gaps = rng.uniform(0.006, 0.016, n)
        w = w / w.sum() * (circ - gaps.sum())
        # choose an offset that staggers joints against the course below
        best, best_d = 0.0, -1
        for _ in range(12):
            o = rng.uniform(0, 2 * math.pi)
            j = np.mod(o + np.cumsum((w + gaps) / rb), 2 * math.pi)
            dmin = np.min(np.abs(np.angle(np.exp(1j * (j[:, None] - prev_joints[None, :])))), axis=1) * rb
            sc = np.min(dmin)
            if sc > best_d:
                best_d, best = sc, o
        acc_ang = best
        L = min(SH_LEN, S_END - s_b + 0.02)
        base_fn = (lambda v: 0.031 * (1 - v)) if k == 0 else (lambda v: B_WEDGE * (1 - v))
        for i in range(n):
            dth = (w[i] + gaps[i]) / rb
            thc = acc_ang + dth / 2
            acc_ang += dth
            ri = rng.rand()
            if k > 0 and k < N_COURSES - 1 and ri < 0.012:
                continue                                    # missing shingle
            sb = s_b + cwave[int((thc % (2 * np.pi)) / (2 * np.pi) * 512) % 512] + rng.uniform(-0.012, 0.012)
            lift = rng.uniform(0.0, 0.012)
            phi = math.radians(rng.uniform(-3.5, 3.5))
            Tb = rng.uniform(0.030, 0.036)
            curl = rng.uniform(0.006, 0.016) if k < 2 else rng.uniform(0.0, 0.005)
            cup = rng.uniform(0.002, 0.008)
            rc = rng.uniform(0.03, 0.07)
            Wi = w[i]
            if k > 0 and 0.012 < ri < 0.03:                 # slipped
                sb -= rng.uniform(0.05, 0.11)
                lift += 0.016
                phi += math.radians(rng.uniform(-4, 4))
            if 0.03 < ri < 0.045 and Wi > 0.36:             # split into two pieces
                g = 0.012
                wa = Wi * rng.uniform(0.4, 0.6)
                wb = Wi - wa - g
                tha = thc - (Wi / 2 - wa / 2) / rb
                thb = thc + (Wi / 2 - wb / 2) / rb
                place(acc, tha, sb, wa, L, Tb, 0.01, phi - 0.02, lift, cup * 0.5, curl, base_fn, rc)
                place(acc, thb, sb + 0.01, wb, L, Tb, 0.01, phi + 0.025, lift + 0.004, cup * 0.5, curl, base_fn, rc)
                n_total += 2
                continue
            place(acc, thc, sb, Wi, L, Tb, 0.01, phi, lift, cup, curl, base_fn, rc)
            n_total += 1
        prev_joints = np.mod(best + np.cumsum((w + gaps) / rb), 2 * math.pi)
    log("shingles:", n_total)
    acc.build(coll)
    st_acc.build(coll)


# =============================================================================================
# apex collar + finial
# =============================================================================================
def collar_base_z():
    best = -1e9
    for r in np.linspace(0.40, COLLAR_R + 0.02, 30):
        ss = s_at_r(r)
        th = np.linspace(0, 2 * np.pi, 64)
        P, ts, tt, n = surf_frame(th, np.full_like(th, ss))
        top = np.max(P[:, 2] + n[:, 2] * 0.075)
        best = max(best, top - (COLLAR_R - r) * math.tan(COLLAR_PITCH))
    return best + 0.012


def build_collar_finial(coll):
    acc = Acc("HUT_cap_collar", 50)
    fin = Acc("HUT_finial", 50)
    z0 = collar_base_z()
    t = 0.022
    za = z0 + COLLAR_R * math.tan(COLLAR_PITCH)
    R = COLLAR_R
    seed = 808

    def dent(th, z):
        return 1 + 0.010 * n2(th * 2.2, np.full_like(th, z * 3), seed) + 0.004 * n2(th * 7, np.full_like(th, z * 9), seed + 1)

    # CCW in (r,z): underside outward, drip roll, outer surface up to apex
    prof = [(0.0, za - t - 0.03), (R - 0.03, z0 - t + 0.005), (R - 0.005, z0 - 0.045), (R + 0.012, z0 - 0.058),
            (R + 0.027, z0 - 0.046), (R + 0.03, z0 - 0.025), (R + 0.018, z0 - 0.004), (R, z0 + 0.004)]
    for f in np.linspace(0.08, 0.92, 10):
        rr = R * (1 - f)
        prof.append((rr, z0 + 0.004 + (R - rr) * math.tan(COLLAR_PITCH)))
    prof.append((0.075, z0 + (R - 0.075) * math.tan(COLLAR_PITCH)))
    prof.append((0.0, za + 0.004))
    V, F, uv, w = lathe(prof, 112, rfunc=dent)
    acc.add(V, F, "M_lead", uv, w)
    # standing seams (10) running up the collar
    for k in range(10):
        th = 2 * np.pi * k / 10 + 0.13
        ts_ = np.linspace(0.02, 0.85, 12)
        rr = (R + 0.005) * (1 - ts_)
        zz = z0 + 0.004 + (R - rr) * math.tan(COLLAR_PITCH)
        dd = dent(np.full_like(rr, th), zz)
        path = np.stack([np.cos(th) * rr * dd, np.sin(th) * rr * dd, zz], -1)
        nrmv = np.array([math.cos(th) * math.sin(COLLAR_PITCH), math.sin(th) * math.sin(COLLAR_PITCH), math.cos(COLLAR_PITCH)])
        path = path + nrmv * 0.006
        prof2 = np.array([[1.0, 0.4], [0.6, 1.0], [-0.6, 1.0], [-1.0, 0.4], [-1.0, -0.6], [1.0, -0.6]])
        prof2 = np.stack([prof2[:, 0] * 0.009, prof2[:, 1] * 0.006], -1)
        # frames: N = up-projected (normal-ish), B across. profile (N,B) -> want height along normal
        prof2 = prof2[:, ::-1]
        P, Fp, uvp, wp = tube(path, 1.0, 6, up=tuple(nrmv), profile=prof2)
        acc.add(P, Fp, "M_lead", uvp, wp)
    # upper collar sits on the lead hat (same slope family), then turned spindle + spike (leans ~1 deg)
    up_r = 0.375
    zb = z0 + 0.004 + (R - up_r) * math.tan(COLLAR_PITCH) + 0.006
    up_pitch = math.tan(math.radians(43))
    prof_u = [(0.0, zb + 0.02), (up_r - 0.03, zb + 0.004), (up_r - 0.004, zb - 0.02), (up_r + 0.01, zb - 0.03),
              (up_r + 0.02, zb - 0.018), (up_r + 0.018, zb + 0.004), (up_r, zb + 0.016)]
    for f in np.linspace(0.12, 0.88, 6):
        rr = up_r - (up_r - 0.065) * f
        prof_u.append((rr, zb + 0.016 + (up_r - rr) * up_pitch))
    zf = zb + 0.016 + (up_r - 0.065) * up_pitch
    prof_u += [(0.065, zf), (0.0, zf + 0.004)]
    lean = rotx(math.radians(0.7)) @ roty(math.radians(-0.6))
    V, F, uv, w = lathe(prof_u, 64, rfunc=lambda th, z: 1 + 0.006 * np.sin(2 * th + 0.4))
    acc.add(V, F, "M_lead", uv, w)
    prof_f = [(0.0, zf - 0.01), (0.07, zf - 0.008), (0.084, zf + 0.004), (0.088, zf + 0.022), (0.08, zf + 0.04),   # ring 1
              (0.056, zf + 0.05), (0.045, zf + 0.08), (0.042, zf + 0.10), (0.05, zf + 0.125),                     # neck
              (0.083, zf + 0.15), (0.094, zf + 0.172), (0.088, zf + 0.196), (0.06, zf + 0.212),                 # bead
              (0.046, zf + 0.235), (0.05, zf + 0.26), (0.074, zf + 0.285), (0.078, zf + 0.30),                 # ring 2
              (0.07, zf + 0.318), (0.046, zf + 0.33), (0.036, zf + 0.35)]
    zs = zf + 0.35
    tip = FINIAL_TIP
    for f in np.linspace(0.08, 0.96, 12):
        prof_f.append((0.034 * (1 - f) ** 1.25 + 0.0014, zs + (tip - 0.004 - zs) * f))
    prof_f += [(0.0011, tip - 0.002), (0.0, tip)]
    V, F, uv, w = lathe(prof_f, 32)
    V = (V - [0, 0, zf]) @ lean.T + [0, 0, zf]
    fin.add(V, F, "M_iron", uv, w)
    acc.build(coll)
    fin.build(coll)
    return z0, za


# =============================================================================================
# plinth, rubble, apron
# =============================================================================================
def build_plinth(coll):
    acc = Acc("HUT_plinth_stones", 70)
    chink = Acc("HUT_plinth_chinking", 70)
    rng = np.random.RandomState(909)
    r_c = 3.53
    door_half = 0.80
    s_tot = 2 * math.pi * r_c
    # walk from the right door edge counter-clockwise around to the left door edge
    a_start = math.asin(1.30 / 3.78)
    a_end = 2 * math.pi - a_start
    a = a_start
    stones = []
    while a < a_end - 0.02:
        L = rng.uniform(0.36, 0.66)
        if a + L / r_c > a_end:
            L = (a_end - a) * r_c
            if L < 0.18:
                break
        g = rng.uniform(0.02, 0.06)
        stones.append((a + (L / 2) / r_c, L))
        a += (L + g) / r_c
    post_az = list(POST_AZ)
    for i, (ac, L) in enumerate(stones):
        H = rng.uniform(0.36, 0.47)
        D = rng.uniform(0.40, 0.52)
        bot = -rng.uniform(0.04, 0.08)
        top = bot + H
        # stones carrying posts get a flat bearing top at 0.375
        near_post = min(abs(np.angle(np.exp(1j * (ac - pa)))) for pa in post_az) * r_c < L / 2
        if near_post:
            top = 0.375
        else:
            top = rng.uniform(0.42, 0.46)
        H = top - bot
        half = np.array([L / 2, D / 2, H / 2])
        P, F = stone(half, rng.uniform(0.45, 0.62), (7, 6, 6), rng, amp=rng.uniform(0.02, 0.034),
                     freq=rng.uniform(2.5, 4.0),
                     flat_top=(H / 2 - 0.004) if near_post else (H / 2 - rng.uniform(0.015, 0.04)))
        # outer face bulges a little more than the back
        P[:, 1] *= 1.0
        R = rotz(ac + rng.uniform(-0.05, 0.05)) @ rotx(rng.uniform(-0.04, 0.04)) @ roty(rng.uniform(-0.05, 0.05))
        c = az_pt(ac, r_c + rng.uniform(-0.03, 0.03), bot + H / 2)
        # local y must point outward radially: az_pt uses (sin a, -cos a) => rotz(a) maps -y to outward
        V = xf(P, R, c)
        acc.add(V, F, "M_stone")
        # chinking stones in the gap after this stone
        if i < len(stones) - 1:
            ga = (ac + stones[i + 1][0]) / 2 + (L - stones[i + 1][1]) / 4 / r_c
            for _ in range(rng.randint(1, 3)):
                hs = np.array([rng.uniform(0.04, 0.08), rng.uniform(0.05, 0.09), rng.uniform(0.03, 0.06)])
                Pc, Fc = stone(hs, 0.35, (4, 4, 3), rng, amp=0.008, freq=8)
                zc = rng.uniform(0.04, 0.30)
                cc = az_pt(ga + rng.uniform(-0.01, 0.01), 3.76 - hs[1] * 0.6, zc)
                Vc = xf(Pc, rotz(ga + rng.uniform(-0.4, 0.4)) @ rotx(rng.uniform(-0.3, 0.3)), cc)
                chink.add(Vc, Fc, "M_rubble")
    log("plinth stones:", len(stones))
    acc.build(coll)
    chink.build(coll)


def build_rubble(coll):
    acc = Acc("HUT_ground_rubble", 70)
    rng = np.random.RandomState(1010)
    pts = []
    # drip-line / plinth foot scatter
    for i in range(30):
        az = rng.uniform(0.35, 2 * math.pi - 0.35)
        r = rng.choice([rng.uniform(3.85, 4.05), rng.uniform(4.05, 4.45)])
        pts.append((az, r, rng.uniform(0.04, 0.16)))
    # cluster by the door, avoiding the path
    for i in range(14):
        x = rng.choice([-1, 1]) * rng.uniform(0.85, 1.7)
        y = rng.uniform(-4.6, -3.85)
        pts.append((math.atan2(x, -y), math.hypot(x, y), rng.uniform(0.04, 0.13)))
    for (az, r, sz) in pts:
        half = np.array([sz * rng.uniform(0.8, 1.3), sz * rng.uniform(0.6, 1.0), sz * rng.uniform(0.35, 0.6)])
        P, F = stone(half, rng.uniform(0.3, 0.5), (4, 4, 3), rng, amp=sz * 0.12, freq=3 / sz)
        R = rotz(rng.uniform(0, 6.28)) @ rotx(rng.uniform(-0.25, 0.25))
        c = az_pt(az, r, half[2] * rng.uniform(-0.2, 0.35))
        acc.add(xf(P, R, c), F, "M_rubble")
    acc.build(coll)




def apron_height(X, Y):
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    # mound: flat inside ~4.45 m (+ path corridor), falls to Z_MIN at the rim
    rim = 4.62 + 0.10 * ring_noise(th, 1111, 5, 1.0)
    m_circle = 1 - smoothstep(rim - 0.85, rim, r)
    m_path = ((1 - smoothstep(0.85, 1.25, np.abs(X + 0.12 * np.sin(Y * 1.3))))
              * smoothstep(-6.15, -5.55, Y) * (Y < -2.0))
    m = np.maximum(m_circle, m_path)
    h = Z_MIN + (0.0 - Z_MIN) * m
    lumps = 0.012 * fbm(np.stack([X * 0.9, Y * 0.9, np.zeros_like(X)], -1), 3) * m
    # drip-line trench under the eave (not across the path)
    dr = r - (4.17 + 0.03 * ring_noise(th, 1112, 5, 1.0))
    trench = -0.032 * np.exp(-(dr / 0.13) ** 2) * (1 - (np.abs(X) < 1.1) * (Y < 0))
    # gentle wear hollow along the path
    wear = -0.012 * np.exp(-(X / 0.5) ** 2) * (Y < -3.8) * m_path
    return h + lumps + trench * m + wear


def build_apron(coll):
    acc = Acc("HUT_ground_apron", 30)
    step = 0.07
    xs = np.arange(-4.9, 4.9 + 1e-6, step)
    ys = np.arange(-6.9, 4.9 + 1e-6, step)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z = apron_height(X, Y)
    Z = np.maximum(Z, Z_MIN + 0.0005)
    P = np.stack([X, Y, Z], -1).reshape(-1, 3)
    F = grid_quads(len(xs), len(ys))
    zf = P[F, 2]
    rr = np.hypot(P[F, 0], P[F, 1]).max(1)
    keep = (zf.max(1) > Z_MIN + 0.002) & (rr > 3.1)
    F = F[keep]
    used = np.unique(F)
    remap = np.full(len(P), -1)
    remap[used] = np.arange(len(used))
    acc.add(P[used], remap[F], "M_earth")
    acc.build(coll)


# =============================================================================================
# door assembly
# =============================================================================================
def timber_box(acc, center, half, R=None, ch=0.02, segs=(1, 1, 1), noise=0.0, seed=0, mat="M_timber",
               sag=0.0, splits=None):
    V, F = rbox(half, ch, segs)
    if noise > 0:
        V = V + fbm(V * 4 + seed, 2)[:, None] * noise * nrm(V / np.asarray(half))
    if sag:
        t = V[:, 0] / half[0]
        V[:, 2] -= sag * (1 - t ** 2)
    V = xf(V, R, center)
    acc.add(V, F, mat)


def peg(acc, p, d, rng, r=0.014, proud=0.016, depth=0.05):
    d = nrm(d)
    path = np.linspace(p - d * depth, p + d * proud, 3)
    path, rr = chamfer_path(path, r * rng.uniform(0.9, 1.1), 0.004)
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    P, F, uv, w = tube(path, rr, 8, up=up)
    acc.add(P, F, "M_timber", uv, w)


def build_door(coll):
    fr = Acc("HUT_door_frame", 40)
    leaf = Acc("HUT_door_leaf", 40)
    iron = Acc("HUT_door_ironwork", 50)
    thr = Acc("HUT_threshold", 50)
    rng = np.random.RandomState(1212)
    yc = FRONT_Y + 0.11                       # frame centre plane
    POST_BASE = 0.355
    for side in (-1, 1):
        x = side * 1.02
        # pad stone under each door post
        P, F = stone(np.array([0.26, 0.25, 0.22]), 0.3, (5, 5, 4), rng, amp=0.012, freq=3.0, flat_top=0.20)
        thr.add(xf(P, rotz(side * 0.2 + rng.uniform(-0.1, 0.1)), (side * 1.04, -3.62, POST_BASE - 0.20)), F, "M_stone")
        # door posts (heavier, squared)
        timber_box(fr, (x, yc, (POST_BASE + HEAD_Z) / 2), (0.12, 0.11, (HEAD_Z - POST_BASE) / 2), rotz(side * 0.006),
                   ch=0.025, segs=(1, 1, 8), noise=0.006, seed=side + 3)
        # inner jambs on the sill
        xj = side * 0.60
        timber_box(fr, (xj, yc, (SILL_TOP + HEAD_Z) / 2), (0.10, 0.11, (HEAD_Z - SILL_TOP) / 2),
                   rotz(side * 0.004) @ roty(side * 0.003), ch=0.022, segs=(1, 1, 8), noise=0.005, seed=side + 9)
        # sole rail under the side panel, resting on the sill end
        timber_box(fr, (side * 0.805, yc, (SILL_TOP + 0.405) / 2), (0.115, 0.075, (0.405 - SILL_TOP) / 2), ch=0.015,
                   segs=(2, 1, 2), noise=0.004, seed=side + 15)
        # return tie beam from the door post to the wall post
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL, 0)
        p0 = np.array([x, yc + 0.05, HEAD_Z + 0.11])
        p1 = np.array([wp[0], wp[1], HEAD_Z + 0.11])
        L = float(np.linalg.norm(p1 - p0))
        R = frame_R(p1 - p0, (0, 0, 1))
        timber_box(fr, (p0 + p1) / 2, (L / 2 + 0.1, 0.08, 0.10), R, ch=0.02, segs=(3, 1, 1), seed=side + 21)
        # pegs: lintel -> door post and jamb tenons, sill tenons
        for (px, pz) in ((x - side * 0.03, HEAD_Z + 0.06), (x + side * 0.045, HEAD_Z + 0.15),
                         (xj, HEAD_Z + 0.07), (xj - side * 0.03, SILL_TOP + 0.05)):
            peg(fr, np.array([px, FRONT_Y - 0.014, pz]), (0, -1, 0), rng)
        peg(fr, p1 - R[:, 0] * 0.06 + np.array([0, 0, 0.10]), (0, 0, 1), rng)
    # lintel on the door posts (front face slightly proud), slight sag
    timber_box(fr, (0.0, yc - 0.008, HEAD_Z + 0.11), (1.15, 0.115, 0.11), ch=0.025, segs=(10, 1, 1),
               noise=0.006, seed=31, sag=0.008)
    # infill above the lintel up to the rafters: short vertical boards
    xx = -1.05
    k = 0
    while xx < 1.05:
        bw = min(rng.uniform(0.16, 0.26), 1.05 - xx)
        if bw < 0.05:
            break
        cx = xx + bw / 2
        r_ = math.hypot(cx, FRONT_Y + 0.1)
        top = float(rafter_underside_z_at_r(r_)) + 0.02
        h0 = HEAD_Z + 0.215
        if top - h0 > 0.04:
            timber_box(fr, (cx, FRONT_Y + 0.13, (h0 + top) / 2), (bw / 2 - 0.006, 0.016, (top - h0) / 2),
                       rotz(rng.uniform(-0.01, 0.01)), ch=0.006, segs=(1, 1, 2), seed=40 + k)
        xx += bw
        k += 1
    # threshold stone + worn timber sill
    P, F = stone(np.array([0.95, 0.30, 0.075]), 0.25, (8, 4, 3), rng, amp=0.008, freq=2.5, flat_top=0.06)
    thr.add(xf(P, rotz(0.01), (0.0, FRONT_Y + 0.12, 0.09 - 0.06)), F, "M_stone")
    V, F = rbox((0.92, 0.13, (SILL_TOP - 0.09) / 2), 0.02, (14, 3, 1))
    top = V[:, 2] > 0
    V[top, 2] -= 0.018 * np.exp(-(V[top, 0] / 0.30) ** 2) * (0.55 + 0.45 * (V[top, 1] < 0))
    V[:, 2] += 0.003 * np.sin(V[:, 0] * 9.0)
    V = xf(V, None, (0.0, yc, (SILL_TOP + 0.09) / 2))
    thr.add(V, F, "M_timber")
    # big flat step stone (top ~0.09)
    P, F = stone(np.array([0.64, 0.34, 0.085]), 0.35, (8, 5, 3), rng, amp=0.01, freq=2.2, flat_top=0.07)
    thr.add(xf(P, rotz(0.05), (0.04, FRONT_Y - 0.43, 0.09 - 0.07)), F, "M_stone")
    # stepping-stone path
    ys = -4.62
    k = 0
    while ys > -6.45:
        lx = rng.uniform(0.25, 0.42)
        ly = rng.uniform(0.2, 0.3)
        xo = 0.1 * math.sin(k * 1.9) + rng.uniform(-0.22, 0.22)
        P, F = stone(np.array([lx, ly, 0.055]), 0.35, (6, 5, 3), rng, amp=0.01, freq=2.5, flat_top=0.045)
        topz = rng.uniform(0.025, 0.045) + float(apron_height(np.array([xo]), np.array([ys - ly]))[0])
        thr.add(xf(P, rotz(rng.uniform(-0.6, 0.6)), (xo, ys - ly, topz - 0.045)), F, "M_stone")
        if rng.rand() < 0.6:
            lx2 = rng.uniform(0.16, 0.28)
            P, F = stone(np.array([lx2, lx2 * 0.8, 0.05]), 0.4, (5, 5, 3), rng, amp=0.008, freq=3, flat_top=0.04)
            x2 = xo + (1 if rng.rand() < 0.5 else -1) * (lx + lx2 + 0.06)
            thr.add(xf(P, rotz(rng.uniform(0, 3)), (x2, ys - ly * 1.2, topz - 0.055)), F, "M_stone")
        ys -= 2 * ly + rng.uniform(0.06, 0.14)
        k += 1
    # ---------------- door leaf: 6 boards + 2 ledges + brace, hung on the +X jamb, open 75 deg inward
    # local frame: origin on the pintle axis, boards toward -x, outer face at y=+0.0065, inner toward +y
    LY = 0.024
    pivot = np.array([0.555, -3.50 - 0.0065 + 0.0015, 0.0])
    Rl = rotz(math.radians(-75.0))
    parts = []
    widths = rng.uniform(0.16, 0.20, 6)
    widths = widths / widths.sum() * (1.06 - 5 * 0.007)
    x = 0.02
    h0, h1 = SILL_TOP + 0.012, HEAD_Z + 0.035
    for b in range(6):
        bw = widths[b]
        cx = -(x + bw / 2)
        V, F = rbox((bw / 2, 0.0175, (h1 - h0) / 2), 0.006, (2, 1, 10))
        V[:, 0] += 0.002 * np.sin(V[:, 2] * 3 + b)
        V[:, 1] += 0.003 * np.sin(V[:, 2] * 1.7 + b * 2) * (V[:, 0] / bw)
        V = V + [cx, LY, (h0 + h1) / 2 + rng.uniform(-0.006, 0.006)]
        parts.append((V, F, "M_timber"))
        x += bw + 0.007
    W = x - 0.007 - 0.02
    for zl in (h0 + 0.32, h1 - 0.34):
        V, F = rbox((W / 2 - 0.04, 0.016, 0.075), 0.01, (4, 1, 1))
        parts.append((V + [-0.02 - W / 2, LY + 0.0175 + 0.016, zl], F, "M_timber"))
        for xn in np.linspace(-0.1, -W + 0.06, 6):      # clenched nail tips through the ledges
            Vn, Fn = rbox((0.004, 0.003, 0.004), 0.0012)
            parts.append((Vn + [xn, LY + 0.0175 + 0.032 + 0.003, zl + 0.03], Fn, "M_iron"))
    za_, zb_ = h0 + 0.32 + 0.06, h1 - 0.34 - 0.06
    p0 = np.array([-0.1, 0.0, za_])
    p1 = np.array([-W + 0.06, 0.0, zb_])
    L = float(np.linalg.norm(p1 - p0))
    Rb = frame_R(p1 - p0, (0, 1, 0))
    V, F = rbox((L / 2 - 0.02, 0.065, 0.016), 0.01, (4, 1, 1))
    V = xf(V, Rb, (p0 + p1) / 2 + [0, LY + 0.0175 + 0.016, 0])
    parts.append((V, F, "M_timber"))
    # wooden latch bar + guide staple on the inner face near the free edge
    V, F = rbox((0.24, 0.016, 0.022), 0.006, (3, 1, 1))
    parts.append((V + [-W + 0.10, LY + 0.0175 + 0.05, 1.12], F, "M_timber"))
    V, F = rbox((0.03, 0.014, 0.04), 0.005)
    parts.append((V + [-W + 0.28, LY + 0.0175 + 0.014, 1.12], F, "M_timber"))
    for V, F, m in parts:
        (iron if m == "M_iron" else leaf).add(xf(V, Rl, pivot), F, m)
    face_y = LY - 0.0175                 # outer face
    for zh in (h0 + 0.30, h1 - 0.30):
        Ls = 0.80
        outline = [(0.0, -0.024), (-Ls + 0.10, -0.021), (-Ls + 0.055, -0.034), (-Ls, 0.0),
                   (-Ls + 0.055, 0.034), (-Ls + 0.10, 0.021), (0.0, 0.024)]
        V, faces = prism(outline, 0.006)
        V = np.stack([V[:, 0], face_y - V[:, 2], V[:, 1] + zh], -1)
        iron.add(xf(V, Rl, pivot), faces, "M_iron", smooth=False)
        # knuckle wrapped round the pintle
        Pk, Fk, uvk, wk = tube(np.linspace([0, 0, zh - 0.03], [0, 0, zh + 0.03], 3), 0.014, 12, up=(1, 0, 0))
        iron.add(xf(Pk, Rl, pivot), Fk, "M_iron", uvk, wk)
        # pintle pin + square shank driven into the jamb back face
        Pp, Fp, uvp, wpp = tube(np.linspace([0, 0, zh - 0.05], [0, 0, zh + 0.045], 3), 0.0075, 8, up=(1, 0, 0))
        iron.add(Pp + pivot, Fp, "M_iron", uvp, wpp)
        V, F = rbox((0.009, 0.035, 0.009), 0.002)
        iron.add(V + pivot + [0.0, -0.03, zh - 0.05], F, "M_iron")
        for xn in (-0.07, -0.22, -0.38, -0.54, -0.68):
            prof = [(0.0, 0.0), (0.009, 0.0), (0.009, 0.0018), (0.006, 0.0042), (0.0, 0.0052)]
            Vn, Fn, uvn, wn = lathe(prof, 8)
            Vn = np.stack([Vn[:, 0] + xn, face_y - 0.006 - Vn[:, 2], Vn[:, 1] + zh], -1)
            iron.add(xf(Vn, Rl, pivot), Fn, "M_iron")
    # ring pull with rose plate near the free edge
    plate = [(0.035 * math.cos(a), 0.035 * math.sin(a)) for a in np.linspace(0, 2 * np.pi, 13)[:-1]]
    V, faces = prism(plate, 0.005)
    xr = -0.02 - W + 0.13
    V = np.stack([V[:, 0] + xr, face_y - V[:, 2], V[:, 1] + 1.08], -1)
    iron.add(xf(V, Rl, pivot), faces, "M_iron", smooth=False)
    ang = np.linspace(0, 2 * np.pi, 25)[:-1]
    ring = np.stack([np.cos(ang) * 0.045 + xr, np.full_like(ang, face_y - 0.013), np.sin(ang) * 0.045 + 1.08 - 0.04], -1)
    ring = np.concatenate([ring, ring[:1]])
    Pr, Fr, uvr, wr = tube(ring, 0.0065, 8, up=(0, -1, 0), caps=False)
    iron.add(xf(Pr, Rl, pivot), Fr, "M_iron", uvr, wr)
    # keeper for the latch on the -X jamb (inner face)
    timber_box(fr, (-0.56, -3.50 + 0.03, 1.12), (0.03, 0.03, 0.05), ch=0.008, seed=77)
    fr.build(coll)
    leaf.build(coll)
    iron.build(coll)
    thr.build(coll)


# =============================================================================================
# interior
# =============================================================================================
def build_interior(coll):
    acc = Acc("HUT_floor", 40)
    rng = np.random.RandomState(1313)
    nr, nt = 26, 160
    R_, T_ = np.meshgrid(np.linspace(0.03, R_WALL + 0.02, nr), np.linspace(0, 2 * np.pi, nt, endpoint=False), indexing="ij")
    X = R_ * np.cos(T_)
    Y = R_ * np.sin(T_)
    Z = SILL_TOP - 0.004 + 0.008 * fbm(np.stack([X * 1.2, Y * 1.2, np.zeros_like(X)], -1), 3) - 0.015 * np.exp(-(R_ / 0.9) ** 2)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    i = np.arange(nr - 1)[:, None]
    j = np.arange(nt)[None, :]
    j1 = (j + 1) % nt
    F = np.stack([i * nt + j, (i + 1) * nt + j, (i + 1) * nt + j1, i * nt + j1], -1).reshape(-1, 4)
    acc.add(V, [F, np.arange(nt)[None, :]], "M_earth")
    hr = Acc("HUT_hearth", 60)
    for k in range(13):
        a = 2 * math.pi * k / 13 + rng.uniform(-0.08, 0.08)
        half = np.array([rng.uniform(0.11, 0.16), rng.uniform(0.08, 0.11), rng.uniform(0.06, 0.09)])
        P, F = stone(half, 0.4, (4, 4, 3), rng, amp=0.012, freq=6)
        c = (math.cos(a) * 0.55, math.sin(a) * 0.55 + 0.4, SILL_TOP - 0.02 + half[2] * 0.6)
        hr.add(xf(P, rotz(a + math.pi / 2), c), F, "M_stone")
    acc.build(coll)
    hr.build(coll)


# =============================================================================================
# main
# =============================================================================================
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = make_collection()
    log(f"plate top {PLATE_TOP:.3f}  wattle top {WATTLE_TOP:.3f}  S_END {S_END:.3f}")
    e = surf(np.array([az2th(0.0)]), np.array([0.0]))[0]
    log(f"eave ref surface at door: r={math.hypot(e[0], e[1]):.3f} z={e[2]:.3f}")
    build_posts(coll)
    log("posts")
    build_wattle(coll)
    log("wattle")
    build_daub(coll)
    build_inner_skin(coll)
    log("daub")
    build_wall_plate(coll)
    build_rafters(coll)
    build_purlins_battens(coll)
    log("roof structure")
    build_shingles(coll)
    log("shingles")
    z0, za = build_collar_finial(coll)
    log(f"collar base {z0:.3f} apex {za:.3f}")
    build_plinth(coll)
    build_rubble(coll)
    build_apron(coll)
    log("ground")
    build_door(coll)
    build_interior(coll)
    log("door + interior")
    tris = 0
    for ob in coll.objects:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    log(f"objects {len(coll.objects)} triangles {tris}")
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log("saved", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
