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
  * lead-hat apex collar (53 deg, dia 1.49, 6.5 cm drip fascia, folded standing seams), bell-cast
    upper collar with its own drip, turned spindle (bead / neck / bulb) and conical spike
Round 2: coarse open wattle (6-8 cm rows, knots, kinks, oval rods, bundles), sub-angular two-high
plinth with recessed wedge chinking, bulging/cracked/smeared daub, hand-hewn frame timber (adze
strokes, wane, swell, drying + end checks), adze-flatted knotty posts, flat-banded apron.
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
    "M_moss": (0.25, 0.35, 0.15),
}
# producer note 7: the shared 15-slot kit palette -- nothing else may be used
PALETTE = ("M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber",
           "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead",
           "M_earth", "M_moss")
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
    """numpy mesh accumulator. cull(V) -> bool per vertex 'never visible'; faces whose vertices are all
    culled are dropped (producer note 6). By default everything more than 1.2 cm below the local ground
    (apron / interior floor) is culled."""

    def __init__(self, name, sharp_angle=40.0, cull="ground"):
        self.name = name
        self.V, self.UV = [], []
        self.Fidx, self.Fsz, self.Fmat, self.Fsm, self.Fwrap = [], [], [], [], []
        self.n = 0
        self.mats = []
        self.sharp_angle = sharp_angle
        self.cull = cull

    def mi(self, m):
        assert m in PALETTE, m
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

    def build_mesh(self, name=None, clamp=True):
        V = np.concatenate(self.V)
        if clamp and self.name != "HUT_ground_apron":
            V[:, 2] = np.maximum(V[:, 2], Z_MIN + 0.004)
        UVv = np.concatenate(self.UV)
        fidx = np.concatenate(self.Fidx)
        fsz = np.concatenate(self.Fsz)
        fmat = np.concatenate(self.Fmat)
        fsm = np.concatenate(self.Fsm)
        fwrap = np.concatenate(self.Fwrap)
        # ---- cull never-visible faces (all vertices culled)
        cull = self.cull
        if cull == "ground":
            cull = cull_below_ground
        if cull is not None:
            vh = cull(V)
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
        V, UVv, fidx = V[used], UVv[used], remap[fidx]
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
        return me

    def build(self, coll):
        me = self.build_mesh()
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        log(f"  {self.name}: {len(me.vertices)} verts, {len(me.polygons)} faces")
        return ob


# ---------------------------------------------------------------------------------------------
# shared-mesh variant pools (producer note 3): linked duplicates of a few base meshes
# ---------------------------------------------------------------------------------------------
POOLS = {}
INST_COLL = {}
N_INST = [0]


def pool_mesh(pool, k, make, sharp=40.0):
    """k-th variant of a pool; make(acc, k) fills an Acc in local coords. Built once, reused."""
    key = (pool, k)
    if key not in POOLS:
        acc = Acc(f"HUT_{pool}_v{k:02d}", sharp, cull=None)
        make(acc, k)
        POOLS[key] = acc.build_mesh(clamp=False)
    return POOLS[key]


def place_instance(mesh, part, R=None, t=(0, 0, 0), scale=1.0):
    """linked duplicate (shared mesh data) placed with a rigid transform (+ uniform scale)."""
    from mathutils import Matrix
    M = np.eye(4)
    M[:3, :3] = (np.eye(3) if R is None else np.asarray(R, float)) * scale
    M[:3, 3] = t
    N_INST[0] += 1
    ob = bpy.data.objects.new(f"HUT_{part}_{N_INST[0]:03d}", mesh)
    ob.matrix_world = Matrix(M.tolist())
    INST_COLL["c"].objects.link(ob)
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


def stone(half, r_frac, segs, rng, amp=0.02, freq=3.0, flat_top=None, flat_bot=None, facets=(3, 6),
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


def flagstone(lx, ly, th, rng, segs=30):
    """flat irregular slab (top at z=0) with rounded arrises and a slightly domed, pitted top."""
    seed = rng.randint(1, 100000)
    # random convex-ish polygon outline (5-7 corners), radius sampled per lathe angle
    k = rng.randint(5, 8)
    ang = np.sort(rng.uniform(0, 2 * np.pi, k))
    ang = np.sort(np.mod(np.linspace(0, 2 * np.pi, k, endpoint=False) + rng.uniform(-0.35, 0.35, k)
                         + rng.uniform(0, 6.3), 2 * np.pi))
    rad = rng.uniform(0.82, 1.1, k)
    poly = np.stack([np.cos(ang) * rad, np.sin(ang) * rad], -1)

    def poly_r(t):
        d = np.stack([np.cos(t), np.sin(t)], -1)
        best = np.full(len(t), 10.0)
        for i in range(k):
            a, b = poly[i], poly[(i + 1) % k]
            e = b - a
            den = d[:, 0] * (-e[1]) - d[:, 1] * (-e[0])
            with np.errstate(divide="ignore", invalid="ignore"):
                tt = (a[0] * (-e[1]) - a[1] * (-e[0])) / den
                u = (d[:, 0] * a[1] - d[:, 1] * a[0]) / den
            ok = (tt > 0) & (u >= -1e-6) & (u <= 1 + 1e-6)
            best = np.where(ok & (tt < best), tt, best)
        return best

    def rf(t, z):
        return poly_r(t) * (1 + 0.035 * ring_noise(t, seed, 7, 1.0, 0.7))

    e = min(0.025, th * 0.3)
    prof = [(0.0, -th), (0.86, -th), (0.97, -th + e * 0.8), (1.0, -e), (0.975, -e * 0.15), (0.93, 0.0),
            (0.6, 0.004), (0.3, 0.006), (0.0, 0.007)]
    V, F, uv, w = lathe(prof, segs, rfunc=rf)
    V[:, 0] *= lx
    V[:, 1] *= ly
    top = V[:, 2] > -e * 0.5
    off = rng.uniform(-50, 50, 3)
    V[top, 2] += 0.006 * fbm(V[top] * 4 + off, 3)
    return V, F


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
Z_MIN = -0.045               # lowest point (apron outer band); nothing deeper than 5 cm (note 6)
R_WALL = 3.50                 # wattle centre line / post centre line
WALL_POST_AZ_DOOR = math.radians(21.0)
N_POSTS = 14
Z_WATTLE0 = 0.345            # director r2: ref2's plinth is one course of low stones (~0.3 m visible)
PITCH = math.radians(51.0)
R_EAVE = 4.13                 # roof reference surface radius at the eave
Z_EAVE = 2.395                # roof reference surface height at the eave
N_RAFT = 28
RAFT_R = 0.055
BATTEN_T = 0.03
SH_EXPOSE = 0.318
SH_LEN = 0.72
N_COURSES = 17
COLLAR_R = 0.745               # lead-hat drip radius (dia 1.49)
COLLAR_PITCH = math.radians(53.0)   # director r1: collar matches / slightly exceeds roof pitch
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
    sub = bpy.data.collections.new("HUT_kit_instances")      # linked duplicates of pooled parts
    coll.children.link(sub)
    INST_COLL["c"] = sub
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


def round_post(acc, base, top, rad, rng, sides=48, check=False, n_knots=None):
    """round-hewn post: lean, bow, taper, 6-10 long adze flats 5-8 mm deep, adze scallops,
    1-2 branch-stub knots with a swelling round them, optional drying check (narrow V split)."""
    tz = (EAVE_SHADOW_Z - base[2]) / (top[2] - base[2])
    t = np.concatenate([np.linspace(0, tz, 40), np.linspace(tz, 1, 5)[1:]])
    nseg = len(t)
    lean = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]) * math.tan(math.radians(0.7))
    H = top[2] - base[2]
    bow = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]) * 0.012
    path = base[None, :] + np.outer(t, top - base) + np.outer(t * H, lean) + np.outer(np.sin(np.pi * t), bow)
    taper = rad * (1 + 0.05 * (0.5 - t)) + rng.uniform(-0.005, 0.005)
    ph0 = rng.uniform(0, 1)
    # only the outward 240 deg are modelled; the back (against the wattle / inner skin) is one flat chord
    a_out = math.atan2(top[1] + base[1], top[0] + base[0])
    sides = 33
    ang = a_out + np.linspace(-2.1, 2.1, sides)
    ph0 = a_out
    seed = rng.randint(1000)
    A2 = np.broadcast_to(ang, (nseg, sides)).copy()
    T2 = np.broadcast_to(t[:, None], (nseg, sides))
    rr = 1 + 0.02 * n2(A2 * 1.3, T2 * 4, seed) + 0.002 * n2(A2 * 2, T2 * 30, seed + 1)
    # adze flats: planar cuts 5-8 mm deep over a stretch of the post, feathered at their ends
    nfl = rng.randint(6, 11)
    for kf in range(nfl):
        af = ph0 + 2 * np.pi * (kf + rng.uniform(-0.3, 0.3)) / nfl * 0.7 - 2.2
        d = rng.uniform(0.005, 0.008) / rad
        t0 = rng.uniform(-0.1, 0.45)
        t1 = t0 + rng.uniform(0.45, 1.0)
        wgt = smoothstep(t0, t0 + 0.06, T2) * (1 - smoothstep(t1 - 0.06, t1, T2))
        # scalloped depth along the flat (adze strokes 5-8 cm)
        dd = d * wgt * (0.75 + 0.25 * np.abs(np.sin(T2 * H / 0.065 * np.pi + kf)))
        ca = np.cos(A2 - af)
        cutr = np.where(ca > 0.2, (1 - dd) / np.maximum(ca, 0.2), 10.0)
        rr = np.minimum(rr, cutr)
    # knots: branch stubs (separate pieces) + swelling of the surface round them
    if n_knots is None:
        n_knots = rng.randint(1, 3)
    stubs = []
    for _ in range(n_knots):
        ka = ph0 + rng.uniform(-1.4, 1.4)
        kt = rng.uniform(0.25, 0.8)
        da = np.angle(np.exp(1j * (A2 - ka))) * rad
        dz = (T2 - kt) * H
        dist = np.hypot(da, dz * 0.8)
        rr = rr + (0.012 * np.exp(-(dist / 0.04) ** 2)) / rad
        stubs.append((ka, kt))
    if check:  # drying check: a narrow, deep V split down one face
        k = rng.randint(6, sides - 6)
        z0, z1 = rng.uniform(0.15, 0.35), rng.uniform(0.55, 0.8)
        m = smoothstep(z0, z0 + 0.08, t) * (1 - smoothstep(z1 - 0.08, z1, t))
        rr[:, k] *= (1 - 0.13 * m)
        dA = 2 * np.pi / sides
        dA = 4.2 / (sides - 1)
        A2[:, (k - 1) % sides] += dA * 0.82 * m
        A2[:, (k + 1) % sides] -= dA * 0.82 * m
    prof = np.stack([np.cos(A2) * rr, np.sin(A2) * rr], -1)
    P, F, uv, w = tube(path, taper, sides, up=(1, 0, 0), profile=prof)
    acc.add(P, F, "M_timber", uv, w)
    T_, N_, B_ = frames(path, (1, 0, 0))
    for (ka, kt) in stubs:
        i = int(kt * (nseg - 1))
        dirv = nrm(np.cos(ka) * N_[i] + np.sin(ka) * B_[i])
        c0 = path[i] + dirv * taper[i] * 0.6
        dirv2 = nrm(dirv + np.array([0, 0, rng.uniform(0.2, 0.6)]))
        L = taper[i] * 0.4 + rng.uniform(0.014, 0.024)
        pth = np.linspace(c0, c0 + dirv2 * L, 4)
        rs_ = rng.uniform(0.016, 0.024)
        pth, rk = chamfer_path(pth, np.linspace(rs_ * 1.25, rs_, 4), 0.005)
        Pk, Fk, uvk, wk = tube(pth, rk, 10, up=(0, 0, 1))
        acc.add(Pk, Fk, "M_timber", uvk, wk)


def hewn_member(acc, center, half, R, rng, ch=0.018, wane=(), n_checks=0, check_faces=(0, 1, 2, 3),
                end_checks=0, sag=0.0, adze=True, mat="M_timber", ds=0.013, ns=7, nc=6, swell=0.008,
                hero=(), hidden=(), deform=None, stride=7, caps=(True, True)):
    """hand-hewn squared timber along local +X (half = (L/2, a, b)); R columns = local axes in world.
    Faces: 0:+z 1:-y 2:-z 3:+y.  Corners: 0:+y+z 1:-y+z 2:-y-z 3:+y-z.
    * adze scallops on every face: 3-6.5 mm deep, 4-8 cm long; on `hero` faces 6-12 mm deep, 5-9 cm
    * +-8 mm swell along the length; arris rounding varies 1.5-3 cm along the member
    * wane (bark-edge rounding) on chosen corners that comes and goes along the length
    * drying checks 6-10 mm wide at the mouth, tapering in width and depth, wandering +-3 mm, some
      with a short parallel / branch check; end-grain checks at both ends
    * `hidden` faces (against the wall / interior / under the roof) are closed with coarse quads only
    * deform(V_local) -> V_local runs before the world transform"""
    hl, a0, b0 = (float(v) for v in half)
    L = 2 * hl
    nl = max(6, int(L / ds) + 1)
    che = min(ch, 0.012)
    xs = np.concatenate([[-hl, -hl + che], np.linspace(-hl + che * 2, hl - che * 2, nl), [hl - che, hl]])
    n = len(xs)
    tt = (xs + hl) / L
    seed = rng.randint(100000)
    sw_a = a0 + swell * n2(tt * 3.0, np.full(n, 0.5), seed)
    sw_b = b0 + swell * n2(tt * 3.0, np.full(n, 2.5), seed + 1)
    rc = np.zeros((n, 4))
    for c in range(4):
        rc[:, c] = np.clip(ch * (1.1 + 0.5 * n2(tt * 3.0 * max(1.0, L / 1.5), np.full(n, c * 1.7), seed + 9)),
                           0.75 * ch, 1.5 * ch)
    for cw in wane:
        wv = smoothstep(-0.25, 0.25, n2(tt * 2.4 * max(1.0, L / 1.5), np.full(n, cw * 3.1), seed + 25 + cw))
        wr = np.clip(0.045 + 0.02 * n2(tt * 4.0, np.full(n, cw * 3.1), seed + 5 + cw), 0.025, 0.065)
        rc[:, cw] = rc[:, cw] * (1 - wv) + wr * wv
    M = 4 * (ns + nc)
    Y = np.zeros((n, M))
    Zp = np.zeros((n, M))
    face = np.full(M, -1)
    across = np.zeros(M)
    corner_sign = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    a_beg_l = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi]
    arcs = np.linspace(0, 0.5 * np.pi, nc)
    for c in range(4):
        sy, sz = corner_sign[c]
        cn = (c + 1) % 4
        sy2, sz2 = corner_sign[cn]
        r = np.minimum(rc[:, c], np.minimum(sw_a, sw_b) * 0.6)
        r2 = np.minimum(rc[:, cn], np.minimum(sw_a, sw_b) * 0.6)
        cy, cz = sy * (sw_a - r), sz * (sw_b - r)
        base_j = c * (ns + nc)
        for k_ in range(nc):
            ang = a_beg_l[c] + arcs[k_]
            Y[:, base_j + k_] = cy + r * math.cos(ang)
            Zp[:, base_j + k_] = cz + r * math.sin(ang)
        pf_y, pf_z = Y[:, base_j + nc - 1], Zp[:, base_j + nc - 1]
        pt_y = sy2 * (sw_a - r2) + r2 * math.cos(a_beg_l[cn])
        pt_z = sz2 * (sw_b - r2) + r2 * math.sin(a_beg_l[cn])
        for k_ in range(ns):
            u = (k_ + 1) / (ns + 1)
            j = base_j + nc + k_
            Y[:, j] = pf_y + (pt_y - pf_y) * u
            Zp[:, j] = pf_z + (pt_z - pf_z) * u
            face[j] = c
            across[j] = u * 2 - 1
    fn = {0: (0, 1), 1: (-1, 0), 2: (0, -1), 3: (1, 0)}
    disp = np.zeros((n, M))
    if adze:
        for c in range(4):
            if c in hidden:
                continue
            js = np.where(face == c)[0]
            hero_f = c in hero
            nlane = rng.randint(2, 4)
            edges = np.sort(np.concatenate([[-1.01, 1.01], rng.uniform(-0.5, 0.5, nlane - 1)]))
            lane_scoop_mid = np.zeros(n)
            for ln in range(nlane):
                inl = (across[js] >= edges[ln]) & (across[js] < edges[ln + 1])
                if not inl.any():
                    continue
                jl = js[inl]
                bnd = [-hl - rng.uniform(0, 0.06)]
                while bnd[-1] < hl + 0.1:
                    bnd.append(bnd[-1] + (rng.uniform(0.05, 0.09) if hero_f else rng.uniform(0.04, 0.08)))
                bnd = np.array(bnd)
                if hero_f:
                    dep = rng.uniform(0.006, 0.012, len(bnd)) * (rng.rand(len(bnd)) > 0.06)
                else:
                    dep = rng.uniform(0.003, 0.0065, len(bnd)) * (rng.rand(len(bnd)) > 0.1)
                skew = rng.uniform(-0.03, 0.03, len(bnd))
                xe = xs[:, None] + skew[np.clip(np.searchsorted(bnd, xs) - 1, 0, len(bnd) - 2)][:, None] * across[jl][None, :]
                k = np.clip(np.searchsorted(bnd, xe.ravel()) - 1, 0, len(bnd) - 2).reshape(xe.shape)
                tl = np.clip((xe - bnd[k]) / (bnd[k + 1] - bnd[k]), 0, 1)
                # scoop: deepest early in the stroke, ends in a small ridge; fades toward lane edges
                ac_ = np.abs(across[jl])[None, :]
                fade = 1 - 0.35 * smoothstep(0.7, 1.0, ac_)
                sc = dep[k] * (1 - (2 * tl - 1) ** 2) ** 0.5 * (0.6 + 0.4 * (1 - tl)) * fade
                disp[:, jl] += sc
                lane_scoop_mid += sc.mean(1) / nlane
            for jc in range(c * (ns + nc), c * (ns + nc) + nc):
                disp[:, jc] += 0.3 * lane_scoop_mid
    for c in range(4):
        js = np.where(face == c)[0]
        ny, nz = fn[c]
        Y[:, js] -= ny * disp[:, js]
        Zp[:, js] -= nz * disp[:, js]
    cj = np.where(face < 0)[0]
    rad_ = np.hypot(Y[:, cj], Zp[:, cj])
    Y[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)
    Zp[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)

    def apply_check(c, j_off, i0, i1, depth, width, from_end=0, wander=0.003):
        j = c * (ns + nc) + nc + j_off
        ny, nz = fn[c]
        ii = np.arange(i0, i1)
        if len(ii) < 3:
            return
        tl = (ii - i0) / max(1, (i1 - i0 - 1))
        if from_end < 0:
            m = (1 - tl) ** 0.7
        elif from_end > 0:
            m = tl ** 0.7
        else:
            m = smoothstep(0.0, 0.25, tl) * (1 - smoothstep(0.6, 1.0, tl))     # tapers both ways
        tyz = np.array([-nz, ny], float)
        wv = wander * n2(xs[ii] * 9.0, np.full(len(ii), j * 0.37), seed + 11 + j)
        # wander: the crack line and its lips drift sideways together
        for jj in (j - 1, j, j + 1):
            Y[ii, jj] += tyz[0] * wv * smoothstep(0.0, 0.2, m)
            Zp[ii, jj] += tyz[1] * wv * smoothstep(0.0, 0.2, m)
        hw = width / 2 * (0.25 + 0.75 * np.sqrt(np.clip(m, 0, 1)))
        for jn, sg in ((j - 1, 1), (j + 1, -1)):
            dist = np.abs((Y[ii, jn] - Y[ii, j]) * tyz[0] + (Zp[ii, jn] - Zp[ii, j]) * tyz[1])
            pull = np.clip(dist - hw, 0, None) * smoothstep(0.0, 0.3, m)
            Y[ii, jn] += sg * tyz[0] * pull
            Zp[ii, jn] += sg * tyz[1] * pull
        Y[ii, j] -= ny * depth * m
        Zp[ii, j] -= nz * depth * m

    for _ in range(n_checks):
        c = int(rng.choice(check_faces))
        if c in hidden:
            continue
        j_off = rng.randint(2, ns - 2)
        lc = rng.uniform(0.15, 0.4)
        x0 = rng.uniform(-hl + 0.15, hl - 0.15 - lc)
        i0 = int(np.searchsorted(xs, x0))
        i1 = int(np.searchsorted(xs, x0 + lc))
        apply_check(c, j_off, i0, i1, rng.uniform(0.014, 0.022), rng.uniform(0.006, 0.010))
        if rng.rand() < 0.6:          # short parallel / branch check off the main one
            jb = j_off + rng.choice([-2, 2])
            if 1 <= jb <= ns - 2:
                lb = rng.uniform(0.05, 0.12)
                xb = x0 + rng.uniform(0.2, 0.7) * lc
                ib0 = int(np.searchsorted(xs, xb))
                ib1 = int(np.searchsorted(xs, min(xb + lb, hl - 0.05)))
                apply_check(c, jb, ib0, ib1, rng.uniform(0.006, 0.01), rng.uniform(0.003, 0.005))
    for _ in range(end_checks):
        for side_ in (-1, 1):
            c = rng.randint(4)
            if c in hidden:
                c = (c + 1) % 4
            j_off = rng.randint(1, ns - 1)
            lc = rng.uniform(0.06, 0.16)
            if side_ < 0:
                i0, i1 = 0, int(np.searchsorted(xs, -hl + lc))
            else:
                i0, i1 = int(np.searchsorted(xs, hl - lc)), n
            apply_check(c, j_off, i0, i1, rng.uniform(0.012, 0.022), rng.uniform(0.004, 0.007), from_end=side_)
    for i_e in (0, n - 1):
        Y[i_e] *= 1 - che / max(a0, 1e-3)
        Zp[i_e] *= 1 - che / max(b0, 1e-3)
    X = np.broadcast_to(xs[:, None], (n, M)).copy()
    if sag:
        X_t = xs / hl
        Zp += (-sag * (1 - X_t ** 2))[:, None]
    V = np.stack([X, Y, Zp], -1).reshape(-1, 3)
    inner0 = np.stack([X[0] + 0.002, Y[0] * 0.55, Zp[0] * 0.55], -1)
    inner1 = np.stack([X[-1] - 0.002, Y[-1] * 0.55, Zp[-1] * 0.55], -1)
    cen = np.array([[xs[0] + 0.003, 0, Zp[0].mean()], [xs[-1] - 0.003, 0, Zp[-1].mean()]])
    V = np.concatenate([V, inner0, inner1, cen])
    j = np.arange(M)
    j1 = (j + 1) % M
    # profile segments belonging to hidden faces (from the last arc point of corner c to the first of c+1)
    hseg = np.zeros(M, bool)
    for c in hidden:                  # the face plus the halves of its two corner arcs
        js0 = c * (ns + nc) + nc - 1 - (nc - 1) // 2
        for q in range(ns + 1 + 2 * ((nc - 1) // 2)):
            hseg[(js0 + q) % M] = True
    i = np.arange(n - 1)[:, None]
    jk = j[~hseg][None, :]
    jk1 = j1[~hseg][None, :]
    Fs = np.stack([i * M + jk, i * M + jk1, (i + 1) * M + jk1, (i + 1) * M + jk], -1).reshape(-1, 4)
    Fl = [Fs]
    if hseg.any():
        ir = np.unique(np.concatenate([np.arange(0, n - 1, stride), [n - 1]]))
        a_ = ir[:-1][:, None]
        b_ = ir[1:][:, None]
        jh = j[hseg][None, :]
        jh1 = j1[hseg][None, :]
        Fl.append(np.stack([a_ * M + jh, a_ * M + jh1, b_ * M + jh1, b_ * M + jh], -1).reshape(-1, 4))
    o_in0 = n * M
    o_in1 = n * M + M
    c0i = n * M + 2 * M
    c1i = c0i + 1
    last = (n - 1) * M
    cap0 = np.stack([o_in0 + j, o_in0 + j1, j1, j], -1)
    cap1 = np.stack([last + j, last + j1, o_in1 + j1, o_in1 + j], -1)
    fan0 = np.stack([np.full(M, c0i), o_in0 + j1, o_in0 + j], -1)
    fan1 = np.stack([np.full(M, c1i), o_in1 + j, o_in1 + j1], -1)
    if deform is not None:
        V = deform(V)
    Vw = xf(V, R, center)
    acc.add(Vw, Fl + ([cap0, fan0] if caps[0] else []) + ([cap1, fan1] if caps[1] else []), mat)


def build_posts(coll):
    acc = Acc("HUT_posts", 15)          # low angle: adze-flat edges crisp, 48-gon stays smooth
    rng = np.random.RandomState(202)
    for i, az in enumerate(POST_AZ):
        b = az_pt(az, R_WALL, PLINTH_TOP - 0.012)
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


EAVE_SHADOW_Z = 2.36           # above this the wall is in the deep eave shadow (lighter geometry)
ROD_ARC = np.radians(np.array([-108.0, -65.0, -22.0, 22.0, 65.0, 108.0]))   # open-backed front shell
STAKE_ARC = np.radians(np.array([-105.0, -52.0, 0.0, 52.0, 105.0]))


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


def _hermite_F(t, tau):
    """0->1 weave transition between two stakes: 30 % of the swing within tau of each stake (tight
    wrap round the stake, zero slope at the stake), 40 % over the straight middle run."""
    t = np.asarray(t, float)
    tau = np.asarray(tau, float)
    mslope = 0.4 * tau / (0.3 * (1 - 2 * tau))

    def h(u):
        return (mslope - 2) * u ** 3 + (3 - mslope) * u ** 2
    a = 0.3 * h(np.clip(t / tau, 0, 1))
    b = 0.3 + 0.4 * np.clip((t - tau) / (1 - 2 * tau), 0, 1)
    c = 1 - 0.3 * h(np.clip((1 - t) / tau, 0, 1))
    return np.where(t < tau, a, np.where(t > 1 - tau, c, b))


def _runs(mask):
    """contiguous True runs -> list of (start, stop) index pairs."""
    m = np.concatenate([[False], np.asarray(mask, bool), [False]])
    d = np.diff(m.astype(np.int8))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def weave_panel(rods, stakes_acc, pathf, s0, s1, z0, z1, seed, hide=None, n_stakes=None, stake_bottom=None,
                slant=0.0, rod_r=(0.0125, 0.019), gap=(-0.004, 0.01), stake_r=(0.014, 0.018), trim=(0.0, 0.0),
                junctions=True, lean=1.5, stake_sp=0.40, stake_back=0.022):
    """woven panel between s0 and s1 (post / jamb centres; rods end `trim` inside them).
    Spec amendment r2: thin stakes (dia 3-4 cm) ~0.38-0.50 m apart, jittered +-4 cm and leaning
    +-1.5 deg, mostly hidden behind the rods; rods dia 2.5-3.8 cm with 0.5-2.5 cm dark gaps between
    rows; every rod wraps its stakes with a clearance of 3-5 mm (offset = stake_r + rod_r + gap, 60 %
    of the swing within +-6 cm of the stake) so no rod intersects a stake; per-rod drift +-1 dia at
    0.5-1 m wavelength; rods tapered butt->tip 1.0->0.55, joints staggered >= 0.3 m row to row, tips
    flicked 2-5 cm out; ~15 % paired / tripled rows; knots and kinks."""
    rng = np.random.RandomState(seed)
    L = s1 - s0
    if n_stakes is None:
        n_stakes = max(1, int(round(L / stake_sp)) - 1)
    base = np.linspace(s0, s1, n_stakes + 2)[1:-1] + rng.uniform(-0.04, 0.04, n_stakes) * min(1.0, L / 0.6)
    lean_k = np.tan(np.radians(rng.uniform(-lean, lean, n_stakes)))
    sr_k = rng.uniform(*stake_r, n_stakes)
    zmid = (z0 + z1) / 2
    steep = abs(slant) > 0.1

    def stake_s(k, z):
        return base[k] + lean_k[k] * (z - zmid) + 0.005 * n2(z * 1.3, base[k] * 3.0, seed + k)

    def stake_rho(k, z):
        return -stake_back + 0.004 * n2(z * 1.7, base[k] * 2.0, seed + 50 + k)

    pt_mid, nn_mid = pathf(np.array([(s0 + s1) / 2]))
    outward3 = np.array([nn_mid[0, 0], nn_mid[0, 1], 0.0])
    # ---- stakes (open-backed; trimmed where buried in daub)
    zb = z0 - 0.07 if stake_bottom is None else stake_bottom
    for k in range(n_stakes):
        nz = 26
        zz = np.linspace(zb, z1 + 0.03, nz)
        ss = stake_s(k, zz)
        pt, nn = pathf(ss)
        xy = pt + nn * stake_rho(k, zz)[:, None]
        path = np.c_[xy, zz]
        rad = sr_k[k] * (1 + 0.08 * n2(zz * 3.0, np.full(nz, base[k]), seed + 70 + k)) * np.linspace(1.08, 0.92, nz)
        vis = np.ones(nz, bool) if hide is None else ~hide(ss, zz)
        vis = vis | np.roll(vis, 1) | np.roll(vis, -1)
        for (a_, b_) in _runs(vis):
            if b_ - a_ < 2:
                continue
            V, F, uv = open_tube(path[a_:b_], rad[a_:b_], STAKE_ARC, outward3, (0, 0, 1), cap1=(b_ == nz))
            stakes_acc.add(V, F, "M_wattle", uv, True)
    # ---- rods
    tilt = rng.uniform(-0.008, 0.008) + slant
    z_lo = z0 - (max(0.0, tilt) * L if steep else 0.0)
    z_stop = z1 - (min(0.0, tilt) * L if steep else 0.0)
    row = 0
    n_rods = 0
    top_prev = None
    prev_j = None
    while True:
        u = rng.rand()
        nsub = 3 if u < 0.04 else (2 if u < 0.15 else 1)
        r_row = rng.uniform(*rod_r)
        if nsub == 1:
            subs = [(r_row, 0.0)]
        elif nsub == 2:
            rA, rB = r_row * rng.uniform(0.72, 0.85), r_row * rng.uniform(0.68, 0.82)
            subs = [(rA, -rB * 1.02), (rB, rA * 1.02)]
        else:
            rr_ = r_row * rng.uniform(0.6, 0.72, 3)
            subs = [(rr_[0], -(rr_[0] + rr_[1]) * 1.02), (rr_[1], 0.0), (rr_[2], (rr_[1] + rr_[2]) * 1.02)]
        lo = min(dz - r for r, dz in subs)
        hi = max(dz + r for r, dz in subs)
        if top_prev is None:
            z = z_lo + (-lo) + rng.uniform(0.002, 0.008)
        else:
            z = top_prev + rng.uniform(*gap) - lo
        if z + hi > z_stop - 0.003:
            break
        top_prev = z + hi
        signs_par = (row % 2)
        # pieces: one rod post to post, or two rods meeting in a staggered overlap
        pieces = []
        a0, a1 = s0 + trim[0], s1 - trim[1]
        if junctions and L > 0.9 and rng.rand() < 0.65:
            for _ in range(12):
                sj = rng.uniform(s0 + 0.35, s1 - 0.35)
                if prev_j is None or abs(sj - prev_j) >= 0.3:
                    break
            ov = rng.uniform(0.18, 0.32)
            pieces.append((a0, sj + ov / 2, -0.55, 1))
            pieces.append((sj - ov / 2, a1, 0.55, -1))
            prev_j = sj
        else:
            pieces.append((a0, a1, 0.0, 1 if rng.rand() < 0.5 else -1))
            prev_j = None if rng.rand() < 0.5 else prev_j
        for (a, b, dzf, tipside) in pieces:
            junction_piece = dzf != 0.0
            for si, (rr0, dzz) in enumerate(subs):
                rseed = seed * 131 + row * 7 + si * 3 + int(a * 10)
                # stake positions and wrap offsets at this row's height
                st = np.array([s0] + [float(stake_s(k, z)) for k in range(n_stakes)] + [s1])
                rho = np.array([0.0] + [float(stake_rho(k, z)) for k in range(n_stakes)] + [0.0])
                srk = np.concatenate([[0.02], sr_k, [0.02]])
                Ak = srk + rr0 * 1.24 + rng.uniform(0.003, 0.005, len(st))
                sgn = np.array([(-1.0) ** (k + signs_par) for k in range(len(st))])
                ok_ = np.argsort(st)
                st, rho, Ak, sgn = st[ok_], rho[ok_], Ak[ok_], sgn[ok_]
                kpos = []
                kp = a + rng.uniform(0.05, 0.4)
                while kp < b - 0.03:
                    kpos.append(kp)
                    kp += rng.uniform(0.3, 0.6)
                if z > EAVE_SHADOW_Z:
                    dense = (st[:, None] + np.array([-0.045, 0.0, 0.045])[None, :]).ravel()
                    extra = []
                    step_ = 0.1
                else:
                    dense = (st[:, None] + np.array([-0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06])[None, :]).ravel()
                    extra = [kp_ + d for kp_ in kpos for d in (-0.01, 0.0, 0.01)]
                    step_ = 0.05
                ss = np.unique(np.concatenate([np.arange(a, b, step_), dense, extra, [a, b]]))
                ss = ss[(ss >= a) & (ss <= b)]
                keep = np.concatenate([[True], np.diff(ss) > 0.007])
                keep[-1] = True
                ss = ss[keep]
                n = len(ss)
                if n < 3:
                    continue
                # per-rod drift: +-1 rod diameter at 0.5-1 m wavelength, plus kinks at side shoots
                wl = rng.uniform(0.35, 0.75)
                drift = 1.2 * 2 * rr0 * n2(ss / wl, np.full(n, rseed * 0.37), 7000 + seed % 97) \
                    + 0.003 * n2(ss * 4.0, np.full(n, rseed * 0.71), 7100 + seed % 89)
                for kp_ in kpos:
                    if rng.rand() < 0.55:
                        drift = drift + rng.uniform(-1, 1) * 0.008 * np.clip(1 - np.abs(ss - kp_) / 0.07, 0, 1) ** 1.5
                zz = z + dzz + dzf * rr0 + drift + tilt * (ss - s0)
                if steep:
                    okz = (zz > z0 - 0.012) & (zz < z1 + 0.012)
                    if okz.sum() < 3:
                        continue
                    idx = np.where(okz)[0]
                    sl = slice(idx[0], idx[-1] + 1)
                    ss, zz = ss[sl], zz[sl]
                    n = len(ss)
                k_ = np.clip(np.searchsorted(st, ss) - 1, 0, len(st) - 2)
                D = st[k_ + 1] - st[k_]
                t = np.clip((ss - st[k_]) / np.maximum(D, 1e-3), 0, 1)
                tau = np.clip(0.06 / np.maximum(D, 1e-3), 0.05, 0.3)
                o0 = sgn[k_] * Ak[k_] + rho[k_]
                o1 = sgn[k_ + 1] * Ak[k_ + 1] + rho[k_ + 1]
                off = o0 + (o1 - o0) * _hermite_F(t, tau)
                # taper butt -> tip 1.0 -> 0.55 (tip at the free end / overlap)
                tpos = (ss - a) / max(b - a, 1e-3)
                taper = 1.0 - 0.45 * (tpos if tipside > 0 else 1 - tpos)
                tip_at_end = junction_piece and tipside > 0
                tip_at_start = junction_piece and tipside < 0
                flick = np.zeros(n)
                if tip_at_end or tip_at_start:
                    tipp = b if tip_at_end else a
                    tt_ = 1 - np.clip(np.abs(ss - tipp) / 0.1, 0, 1)
                    flick = rng.uniform(0.02, 0.05) * tt_ ** 2
                off = off + flick
                pt, nn = pathf(ss)
                path = np.c_[pt + nn * off[:, None], zz]
                knot = np.zeros(n)
                for kp_ in kpos:
                    knot += 0.15 * np.exp(-((ss - kp_) / 0.011) ** 2)
                rad = rr0 * taper * (1 + knot + 0.05 * n2(ss * 5, np.full(n, z), seed + 7))
                kn = 0.07 * n2(np.arange(n)[:, None] * 0.35 + np.zeros((1, len(ROD_ARC))),
                               np.broadcast_to(ROD_ARC * 1.7, (n, len(ROD_ARC))), rseed)
                vis = np.ones(n, bool) if hide is None else ~hide(ss, zz)
                vis = vis | np.roll(vis, 1) | np.roll(vis, -1) | np.roll(vis, 2) | np.roll(vis, -2)
                if not vis[0]:
                    vis[:2] = vis[:2]
                close = flick > 0.002
                oval = rng.uniform(0.8, 0.92)
                # section arc: +-108 deg where the rod passes proud of its neighbours (in front of a stake,
                # top & bottom glimpsed), +-72 deg where it is level with or behind them (occluded)
                proud = np.clip((off - rho.mean()) / np.maximum(Ak.mean(), 1e-3), 0, 1)
                if junction_piece:
                    proud = np.maximum(proud, 0.5)
                if steep:                        # recessed rope-weave door panels
                    lo_a, hi_a = np.full(n, 58.0), np.full(n, 80.0)
                elif z > EAVE_SHADOW_Z:          # deep in the eave shadow: lighter section
                    lo_a, hi_a = 50.0 + 20.0 * proud, 62.0 + 22.0 * proud
                elif z < 1.55:                   # below eye level: undersides face away from every viewer
                    lo_a, hi_a = 46.0 + 30.0 * proud, 78.0 + 30.0 * proud
                else:                            # above eye level: tops face away from most viewers
                    lo_a, hi_a = 62.0 + 34.0 * proud, 68.0 + 30.0 * proud
                arc_n = -np.radians(lo_a)[:, None] + (np.radians(lo_a + hi_a))[:, None] * np.linspace(0, 1, len(ROD_ARC))[None, :]
                for (ra, rb) in _runs(vis):
                    if rb - ra < 3:
                        continue
                    V, F, uv = open_tube(path[ra:rb], rad[ra:rb], arc_n[ra:rb], outward3, (0, 0, 1), rr=1 + kn[ra:rb],
                                         close_mask=close[ra:rb], cap0=(tip_at_start and ra == 0),
                                         cap1=(tip_at_end and rb == n), oval=oval)
                    rods.add(V, F, "M_wattle", uv, True)
                    n_rods += 1
        row += 1
    return n_rods


# ---------------------------------------------------------------------------------------------
# daub definitions
# ---------------------------------------------------------------------------------------------
def bay_s(i):
    a0 = POST_AZ[i]
    a1 = POST_AZ[i + 1]
    return a0 * R_WALL, a1 * R_WALL


DAUB_BAYS = {}   # bay index -> function(s, z) -> thickness above wattle centre (m), <=0 => none
DAUB_COVER = {}  # bay index -> field value above which the rods are buried in the daub coat
DAUB_SIDE = [None]


def _knot_curve(seed, s_lo, s_hi, spacing, amp):
    rs = np.random.RandomState(seed)
    ks = np.arange(s_lo - spacing, s_hi + 2 * spacing, spacing) + rs.uniform(-0.3, 0.3, 1) * spacing
    kv = rs.uniform(-1, 1, len(ks)) * amp
    fine = np.linspace(ks[0], ks[-1], 600)
    v = np.interp(fine, ks, kv)
    ker = np.exp(-np.linspace(-2, 2, 31) ** 2)
    ker /= ker.sum()
    v = np.convolve(np.pad(v, 15, mode="edge"), ker, mode="valid")
    return fine, v


_EDGE_CURVE = {}


def daub_edge_door_bay(s):
    """eroded lower edge of the big bay left of the door: break height ~0.62 m +-12 cm with bites."""
    if "door" not in _EDGE_CURVE:
        _EDGE_CURVE["door"] = _knot_curve(9011, 17.5, 22.5, 0.25, 0.24)
    fs, fv = _EDGE_CURVE["door"]
    s = np.asarray(s, float)
    return (0.61 + np.interp(s, fs, fv) + 0.025 * n2(s * 7.0, 1.7, 902)
            + 0.014 * n2(s * 17.0, 3.1, 903) + 0.007 * n2(s * 41.0, 5.3, 904))


def make_daub_fields():
    nb = len(POST_AZ) - 1
    door_bay = nb - 1                      # between POST_AZ[-2] and POST_AZ[-1] (az -45..-21)
    back_bay = 5
    side_bay = 2
    s0, s1 = bay_s(side_bay)
    pc_s = s0 + 0.55 * (s1 - s0)
    pc_z = 1.75

    def door_field(s, z):
        f = z - daub_edge_door_bay(s)
        # clinging remnants and scabs just below the break
        isl = np.clip(n2(s * 9.0, z * 9.0, 905) * 1.6 - 0.35, 0, 1) * 0.09
        f = np.where(f < 0, np.maximum(f, f + isl * (1 - smoothstep(0.0, 0.22, -f)) * 1.5), f)
        # a few pock holes where daub has fallen out higher up
        hole = np.clip(n2(s * 6.0, z * 6.0, 906) * 2.2 - 1.5, 0, 1)
        return f - hole * 0.6

    def back_field(s, z):
        return np.minimum(z - (0.50 + 0.05 * n2(s * 3, 0.0, 911)), 1.0)

    srng = np.random.RandomState(9210)
    side_R = outline_radius(srng, "pad")
    c_s, c_z = s0 + 0.47 * (s1 - s0), 0.93
    h_s, h_z = 0.50, 0.44

    def side_field(s, z):
        """an old daub coat remnant: irregular blob (no straight run > 15 cm), crumbled lower margin,
        thin spots where the rods show through; value ~ distance inside the outline (m)."""
        du, dv = (s - c_s) / h_s, (z - c_z) / h_z
        th = np.arctan2(dv, du)
        rho = np.hypot(du, dv)
        rb = side_R(th)
        scale = np.hypot(h_s * np.cos(th), h_z * np.sin(th))
        f = (rb - rho) * scale
        f = f + 0.05 * n2(s * 6.0, z * 6.0, 921) + 0.02 * n2(s * 15, z * 15, 922)
        low = smoothstep(0.0, -0.8, np.sin(th))                 # crumbled lower margin
        f = f - low * (0.06 * np.clip(n2(s * 9, z * 9, 923) + 0.3, 0, 2))
        isl = np.clip(n2(s * 8.0, z * 8.0, 927) * 1.6 - 0.4, 0, 1) * 0.08
        f = np.where(f < 0, np.maximum(f, f + isl * (1 - smoothstep(0.0, 0.2, -f)) * 1.5), f)
        thin = np.clip(n2(s * 7.0, z * 7.0, 928) * 2.4 - 1.1, 0, 1)
        return f - 0.16 * thin

    DAUB_BAYS[door_bay] = door_field
    DAUB_BAYS[back_bay] = back_field
    DAUB_BAYS[side_bay] = side_field
    DAUB_COVER[side_bay] = 0.11
    DAUB_COVER[door_bay] = 0.04
    DAUB_COVER[back_bay] = 0.04
    DAUB_SIDE[0] = side_bay


def daub_hides(bay):
    f = DAUB_BAYS.get(bay)
    if f is None:
        return None

    thr = DAUB_COVER.get(bay, 0.04)

    def hide(s, z):
        return f(s, z) > thr
    return hide


def build_wattle(coll):
    make_daub_fields()
    rods = Acc("HUT_wattle_rods", 60)
    stakes = Acc("HUT_wattle_stakes", 60)
    pathf = arc_path(R_WALL)
    nb = len(POST_AZ) - 1
    nr = 0
    for i in range(nb):
        s0, s1 = bay_s(i)
        nr += weave_panel(rods, stakes, pathf, s0, s1, Z_WATTLE0, WATTLE_TOP, 1000 + i * 17, hide=daub_hides(i),
                          trim=(0.075, 0.075))
    # door side panels (front plane) between jamb and door post: rope-like diagonal weave
    for side in (-1, 1):
        x0, x1 = 0.70, 0.90
        p0 = (side * x0, FRONT_Y + 0.11)
        p1 = (side * x1, FRONT_Y + 0.11)
        f = line_path(p0, p1, (0, -1))
        nr += weave_panel(rods, stakes, f, -0.012, (x1 - x0) + 0.012, 0.40, HEAD_Z, 3000 + side, n_stakes=2,
                          stake_bottom=0.33, slant=0.85 * side, rod_r=(0.0105, 0.0135), gap=(0.003, 0.009),
                          stake_r=(0.012, 0.014), junctions=False, lean=0.0, stake_back=0.0)
        # cheek panels: door post back corner -> wall post
        pa = np.array([side * 1.02, FRONT_Y + 0.17])
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL)[:2]
        L = float(np.linalg.norm(wp - pa))
        d = (wp - pa) / L
        nout = np.array([d[1], -d[0]]) * (1 if side > 0 else -1)
        if nout[0] * side < 0:
            nout = -nout
        f2 = line_path(pa, wp, nout)
        nr += weave_panel(rods, stakes, f2, -0.05, L + 0.02, 0.40, HEAD_Z, 3100 + side, n_stakes=2,
                          stake_bottom=0.33, slant=-0.6 * side, rod_r=(0.0105, 0.014), gap=(0.003, 0.01),
                          stake_r=(0.012, 0.015), junctions=False, lean=0.0, stake_back=0.0)
    log("rods:", nr)
    rods.build(coll)
    stakes.build(coll)


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


def build_daub(coll):
    """front daub sheets: 2.5-4 cm bulges (0.4-0.8 m), faint horizontal ridging over the rods,
    palm / trowel smears, 3-6 shrinkage cracks per bay, chipped edges against the posts, eroded
    ragged lower edge, detached clumps clinging to the rods. Every boundary tucks behind the
    wattle / into the posts / under the plate, so no clean cut edge is exposed."""
    acc = Acc("HUT_daub", 70)
    h = 0.0075
    n_cr = 0
    for bay, field in DAUB_BAYS.items():
        rng = np.random.RandomState(4400 + bay)
        sb0, sb1 = bay_s(bay)
        s0, s1 = sb0 + 0.04, sb1 - 0.04
        zlo, zhi = Z_WATTLE0 + 0.02, WATTLE_TOP + 0.02
        # crop to where the daub exists
        Sc, Zc = np.meshgrid(np.linspace(s0, s1, 120), np.linspace(zlo, zhi, 160), indexing="ij")
        fc = field(Sc, Zc)
        live = fc > -0.07
        ss_live = Sc[live]
        zz_live = Zc[live]
        cs0, cs1 = max(s0, ss_live.min() - 0.03), min(s1, ss_live.max() + 0.03)
        cz0, cz1 = max(zlo, zz_live.min() - 0.03), min(zhi, zz_live.max() + 0.03)
        nu = int((cs1 - cs0) / h) + 1
        zr = np.linspace(cz0, min(cz1, EAVE_SHADOW_Z - 0.06), int((min(cz1, EAVE_SHADOW_Z - 0.06) - cz0) / h) + 1)
        if cz1 > EAVE_SHADOW_Z - 0.06:
            zr = np.concatenate([zr, np.linspace(zr[-1], cz1, int((cz1 - zr[-1]) / 0.02) + 2)[1:]])
        nv = len(zr)
        S, Z = np.meshgrid(np.linspace(cs0, cs1, nu), zr, indexing="ij")
        # ---- shrinkage cracks: random-walk polylines; snap grid lines into narrow V grooves
        cracks = []
        ncr = rng.randint(4, 7)
        tries = 0
        while len(cracks) < ncr and tries < 200:
            tries += 1
            ps = rng.uniform(cs0 + 0.12, cs1 - 0.12)
            pz = rng.uniform(cz0 + 0.12, cz1 - 0.1)
            if field(np.array([ps]), np.array([pz]))[0] < 0.15:
                continue
            Lc = rng.uniform(0.3, 0.8)
            ang = rng.choice([rng.uniform(-0.5, 0.5) + np.pi / 2, rng.uniform(-1.2, 1.2)])
            pts = [(ps, pz)]
            l = 0.0
            while l < Lc:
                st_ = rng.uniform(0.035, 0.06)
                ang += rng.uniform(-0.45, 0.45)
                ps += math.cos(ang) * st_
                pz += math.sin(ang) * st_
                pts.append((ps, pz))
                l += st_
            cracks.append((pts, rng.uniform(0.005, 0.01), rng.uniform(0.012, 0.02)))
            if rng.rand() < 0.4:        # short branch
                kb = rng.randint(1, len(pts) - 1)
                bs, bz = pts[kb]
                ang2 = ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
                bp = [(bs, bz)]
                for _ in range(rng.randint(3, 6)):
                    ang2 += rng.uniform(-0.4, 0.4)
                    bs += math.cos(ang2) * 0.04
                    bz += math.sin(ang2) * 0.04
                    bp.append((bs, bz))
                cracks.append((bp, rng.uniform(0.004, 0.007), rng.uniform(0.01, 0.015)))
        crack_d = np.zeros(S.shape)
        for (pts, wd, dp) in cracks:
            dist, cs_, cz_, ct = _seg_dist(S, Z, pts)
            prof = np.sin(np.pi * np.clip(ct, 0, 1)) ** 0.5
            ww = wd * 0.5 * (0.3 + 0.7 * prof)
            core = dist < 0.55 * h
            band = (dist >= 0.55 * h) & (dist < 1.8 * h)
            # core vertices snap onto the crack centre line (groove bottom)
            S = np.where(core, cs_, S)
            Z = np.where(core, cz_, Z)
            # neighbours are pulled in to the crack lip (narrow 0.5-1 cm crack)
            with np.errstate(invalid="ignore", divide="ignore"):
                ux = (S - cs_) / np.maximum(dist, 1e-9)
                uz = (Z - cz_) / np.maximum(dist, 1e-9)
            dn = ww + (dist - 0.55 * h) * (1.8 * h - ww) / (1.25 * h)
            S = np.where(band, cs_ + ux * dn, S)
            Z = np.where(band, cz_ + uz * dn, Z)
            crack_d = np.minimum(crack_d, np.where(core, -dp * (0.2 + 0.8 * prof), 0.0))
            n_cr += 1
        f = field(S, Z)
        P3 = np.stack([S * 1.7, Z * 1.7, np.full(S.shape, bay * 1.31)], -1)
        # ---- big soft bulges (2.5-4 cm at 0.4-0.8 m)
        bul = fbm(P3, 2, gain=0.45)
        bul = (bul - bul.mean()) / max(bul.std(), 1e-6)
        bulge = 0.016 * np.clip(bul, -2.2, 2.2)
        # ---- faint horizontal ridging over the rods beneath (6-8 cm pitch), strongest where thin
        # ridging only in small patches (<= 0.3 m) where the coat is thin, pitch 5-7.5 cm and amplitude varying
        drift = 0.02 * n2(S * 1.1, np.full(S.shape, 3.3), 4500 + bay)
        pitch = 0.0625 + 0.0125 * n2(S * 1.7, Z * 0.9, 4505 + bay)
        rid = np.cos(2 * np.pi * (Z + drift) / pitch + 0.6 * n2(S * 3, Z, 4510 + bay))
        thin = 1 - smoothstep(-0.9, 0.4, bul)
        patchy = np.clip(n2(S * 5.5, Z * 5.5, 4511 + bay) * 2.6 - 0.7, 0, 1)
        r_amp = 0.0045 + 0.0035 * np.clip(n2(S * 4.0, Z * 4.0, 4512 + bay) + 0.5, 0, 1)
        ridge = r_amp * rid * thin ** 2 * patchy
        # ---- palm / trowel smears
        smear = np.zeros(S.shape)
        area = (cs1 - cs0) * (cz1 - cz0)
        for _ in range(int(area * 22)):
            c_s = rng.uniform(cs0, cs1)
            c_z = rng.uniform(cz0, cz1)
            l_ = rng.uniform(0.18, 0.4)
            w_ = rng.uniform(0.07, 0.14)
            an = rng.choice([rng.uniform(-0.6, 0.6), rng.uniform(0.9, 2.2)])
            du = (S - c_s) * math.cos(an) + (Z - c_z) * math.sin(an)
            dv = -(S - c_s) * math.sin(an) + (Z - c_z) * math.cos(an)
            # curved palm sweep: bend the stroke, gaussian trough, soft heaped edge ahead of it
            dv = dv - 0.6 * (du ** 2) / max(l_, 1e-3) * rng.uniform(-1, 1)
            e2 = (du / (l_ / 2)) ** 2 + (dv / (w_ / 2)) ** 2
            m = e2 < 9.0
            if not m.any():
                continue
            A_ = rng.uniform(0.005, 0.009)
            tr = -np.exp(-e2 * 1.2)
            ahead = np.exp(-((du / (l_ / 2) - 1.05) / 0.35) ** 2 - (dv / (w_ * 0.7)) ** 2)
            smear += A_ * (tr + 0.6 * ahead) * m
        fine = (0.0035 * n2(S * 9, Z * 9, bay + 40) + 0.0012 * n2(S * 30, Z * 30, bay + 41)
                + 0.0005 * n2(S * 80, Z * 80, bay + 42))
        # ---- chipped / crumbled edges where the daub meets the posts (no clean vertical line)
        sp = np.minimum(S - sb0, sb1 - S)
        side_ = np.where(S - sb0 < sb1 - S, 0.0, 1.0)
        # broken margin: its distance from the post wanders 9-17 cm in irregular bites
        reach = (0.13 + 0.035 * n2(Z * 5.5, side_ * 7.0 + bay, 4520) + 0.015 * n2(Z * 17, side_ * 3.0 + bay, 4521))
        chip = (1 - smoothstep(reach - 0.025, reach + 0.004, sp)) * smoothstep(0.06, 0.08, sp)
        chip = chip * np.clip(0.55 + 0.6 * n2(S * 9, Z * 9, 4522 + bay), 0.25, 1.0)
        nearp = 1 - smoothstep(0.08, 0.22, sp)
        T_full = 0.088 + bulge * (0.3 + 0.7 * smoothstep(0.07, 0.25, sp)) + ridge * (1 - nearp) + smear + fine
        T_full = T_full - 0.024 * chip - 0.008 * nearp
        # thickness envelope: tucks behind the rods where the field ends (eroded / patch edges)
        if bay == DAUB_SIDE[0]:       # thin old coat: feathered 0 -> 4 cm over ~12 cm, rods show at the edge
            T_full = 0.072 + 0.5 * (T_full - 0.088)
            edge = smoothstep(-0.004, 0.13, f)
        else:
            edge = smoothstep(-0.004, 0.045, f)
        pit = 0.01 * np.clip(n2(S * 25, Z * 25, bay + 77), 0, 1) * (1 - smoothstep(0.04, 0.16, f))
        T = -0.036 + (T_full + 0.036 - pit) * edge + crack_d * edge
        # tuck into the posts at the very ends of the sheet
        T = T - 0.04 * (1 - smoothstep(0.045, 0.095, sp)) * edge
        a = S / R_WALL
        rad = R_WALL + T
        P = np.stack([np.sin(a) * rad, -np.cos(a) * rad, Z], -1)
        Vv = P.reshape(-1, 3)
        F = grid_quads(nu, nv)
        # drop the parts never seen: sheet tucked behind the rods below the break, and inside the posts
        hv = ((f < -0.03) | (sp < 0.085)).ravel()
        F = F[~hv[F].all(axis=1)]
        acc.add(Vv, F, "M_daub")
        # ---- detached clumps clinging to the rods below the break (eroded bays)
        if bay == len(POST_AZ) - 2:
            for kcl in range(3):
                cs_ = rng.uniform(s0 + 0.2, s1 - 0.2)
                cz_ = float(daub_edge_door_bay(np.array([cs_]))[0]) - rng.uniform(0.07, 0.2)
                hs = np.array([rng.uniform(0.04, 0.07), rng.uniform(0.022, 0.03), rng.uniform(0.03, 0.05)])
                Pc, Fc = stone(hs, 0.95, (6, 5, 5), rng, amp=0.007, freq=11, warp=0.35, facets=(0, 1))
                ac_ = cs_ / R_WALL
                cc = az_pt(ac_, R_WALL + 0.035 + hs[1] * 0.4, cz_)
                acc.add(xf(Pc, rotz(ac_) @ roty(rng.uniform(-0.4, 0.4)), cc), Fc, "M_daub")
    log("daub cracks:", n_cr)
    acc.build(coll)


INNER_SKIN_D = 0.17            # inner daub skin face, behind the wattle centre line (director r2: >= 0.15)


def build_inner_skin(coll):
    """inner daub skin 17 cm behind the rod centre line: the dark back of the open weave (gaps read dark,
    rod backs are never visible) and the inner wall face seen through the doorway.  A single lumpy sheet
    (both faces are seen: the outer through the weave gaps, the inner through the door) with a folded
    top lip under the plate; it is left out behind fully daubed areas whose interior side is not visible
    through the door."""
    acc = Acc("HUT_daub_interior", 70)
    a0, a1 = WALL_POST_AZ_DOOR, 2 * math.pi - WALL_POST_AZ_DOOR
    nu = max(8, int((a1 - a0) * R_WALL / 0.08))
    zt = PLATE_BOT + 0.02
    zz = np.concatenate([np.linspace(0.15, zt, 30), [zt + 0.002]])
    A, Z = np.meshgrid(np.linspace(a0, a1, nu), zz, indexing="ij")
    lump = 0.012 * fbm(np.stack([A * 4, Z * 2.5, np.zeros(A.shape)], -1), 3)
    ro = R_WALL - INNER_SKIN_D + lump
    ro[:, -1] = R_WALL - 0.115                                # top lip folded back toward the wattle
    P = np.stack([np.sin(A) * ro, -np.cos(A) * ro, Z], -1)
    F = grid_quads(nu, len(zz))[:, ::-1]                     # normals face the hut interior
    # hidden: behind daubed bays whose inner side cannot be seen through the doorway
    hv = np.zeros(A.shape, bool)
    for bay, fld in DAUB_BAYS.items():
        sb0, sb1 = bay_s(bay)
        if bay == 5:
            continue
        S = A * R_WALL
        inb = (S > sb0 + 0.06) & (S < sb1 - 0.06)
        hv |= inb & (fld(S, Z) > 0.05)
    hv = hv.ravel()
    F = F[~hv[F].all(axis=1)]
    acc.add(P.reshape(-1, 3), F, "M_daub")
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
        # pegs through the laps, driven in from the outer face (heads proud, seen from under the eave)
        for aj in (a0, a1):
            for d in (-0.07, 0.07):
                az_ = aj + d / R_WALL
                u = np.array([math.sin(az_), -math.cos(az_), 0.0])
                p = az_pt(az_, R_WALL + hw - 0.002, zc + rng.uniform(-0.03, 0.03))
                peg(p, u, rng)
    acc.build(coll)


# =============================================================================================
# roof structure
# =============================================================================================
def interior_visible(az, half_width=math.radians(110.0)):
    """roof structure on this azimuth can be seen from outside through the doorway (back arc)."""
    return abs(float(np.angle(np.exp(1j * (az - math.pi))))) < half_width


RAFT_ARC = np.radians(np.array([-115.0, -80.0, -45.0, -15.0, 15.0, 45.0, 80.0, 115.0]))


def build_rafters(coll):
    """28 pole rafters.  Seen from outside only under the eave and, in the back arc, through the door:
    the front-arc rafters are modelled as eave stubs ending 16 cm inside the wall, and every rafter is
    open on its top (it faces the battens / shingle underside and is never visible)."""
    acc = Acc("HUT_rafters", 50)
    rng = np.random.RandomState(404)
    s_hub = s_at_r(0.34)
    s_stub = s_at_r(R_WALL - 0.16)
    for j in range(N_RAFT):
        az = RAFT_AZ0 + j * 2 * math.pi / N_RAFT
        th = float(az2th(az))
        full = interior_visible(az)
        s_tip = rng.uniform(0.04, 0.12)
        s_end = s_hub if full else s_stub
        ss = np.concatenate([np.linspace(s_tip, s_tip + 0.3, 5), np.linspace(s_tip + 0.3, s_end, 12 if full else 4)[1:]])
        C, ts, tt, n = rafter_center(np.full_like(ss, th), ss)
        crook = 0.018 * n2(ss * 0.6, np.full_like(ss, j * 1.0), 405) * np.sin(np.pi * (ss - s_tip) / (s_hub - s_tip))
        C = C + tt * crook[:, None]
        r0 = rng.uniform(0.05, 0.06)
        rad = r0 * (1.0 - 0.25 * (ss - s_tip) / (s_hub - s_tip))
        down = -n[len(n) // 2]
        rr = 1 + 0.04 * n2(np.arange(len(ss))[:, None] * 0.2 + np.zeros((1, len(RAFT_ARC))), np.broadcast_to(RAFT_ARC * 2, (len(ss), len(RAFT_ARC))), j)
        split = (j % 5 == 2)
        if split:
            ks = int(np.searchsorted(ss, s_tip + 0.22))
            V, F, uv = open_tube(C[ks:], rad[ks:], RAFT_ARC, down, tuple(n[0]), rr=rr[ks:], cap0=True, cap1=not full)
            acc.add(V, F, "M_timber", uv, True)
            ang2 = np.linspace(-np.pi / 2, np.pi / 2, 8)
            for sgn in (-1, 1):
                seg = C[:ks + 1].copy()
                kk = np.linspace(1, 0, len(seg))
                seg = seg + tt[:ks + 1] * (sgn * (0.004 + 0.014 * kk ** 2))[:, None]
                dprof = np.stack([np.sin(ang2), -np.cos(ang2) * sgn], -1)
                if sgn < 0:
                    dprof = dprof[::-1]
                pth, rr_ = chamfer_path(seg[::-1], rad[:ks + 1][::-1], 0.006)
                P, F, uv, w = tube(pth, rr_, 8, up=tuple(n[0]), profile=dprof)
                acc.add(P, F, "M_timber", uv, w)
        else:
            V, F, uv = open_tube(C, rad, RAFT_ARC, down, tuple(n[0]), rr=rr, cap0=True, cap1=not full)
            # uneven, slightly skewed saw / axe cut at the tip
            m = len(RAFT_ARC)
            sk = rng.uniform(-0.035, 0.035)
            t_end = nrm(C[0] - C[1])
            proj = ((V[:m] - C[0]) @ tt[0]) / max(rad[0], 1e-3)
            V[:m] += t_end[None, :] * (sk * proj)[:, None]
            acc.add(V, F, "M_timber", uv, True)
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
    for sp in (1.25,):
        az = RAFT_AZ0 + np.arange(N_RAFT + 1) * d
        th = az2th(az)
        C, ts, tt, n = rafter_center(th, np.full_like(th, sp))
        C = C - n * (RAFT_R + 0.035)
        for k in range(N_RAFT):
            if not (interior_visible(az[k], math.radians(55)) and interior_visible(az[k + 1], math.radians(55))):
                continue                     # only where the doorway shows them
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
        eave_ring = sb < 0.9                 # seen from outside in the eave gap
        for st in starts:
            a = max(st, 0)
            b = min(st + step, N_RAFT)
            if b <= a:
                continue
            if not eave_ring and not (sb < 2.3 and interior_visible(az[a], math.radians(75))
                                      and interior_visible(az[b], math.radians(75))):
                continue
            p0, p1 = Cb[a], Cb[b]
            # lath runs straight from rafter a to rafter b (chord); overhang 4 cm
            x = p1 - p0
            L = float(np.linalg.norm(x))
            mid = (p0 + p1) / 2
            nmid = nrm(n[a] + n[b])
            R = frame_R(x, nmid)
            hw = 0.025 if kb > 0 else 0.045
            V, F = rbox((L / 2 + 0.03, hw, BATTEN_T / 2), 0.004, (1, 1, 1), chamfer=False)
            V = xf(V, R, mid + R[:, 1] * rng.uniform(-0.005, 0.005))
            bat.add(V, F, "M_timber_weathered", smooth=True)
    pur.build(coll)
    bat.build(coll)


# =============================================================================================
# shingles
# =============================================================================================
SH_LOOP_X = np.array([-0.97, -0.6, -0.2, 0.2, 0.6, 0.97, 1.0, 0.97, -0.97, -1.0])   # x / (W/2)
SH_LOOP_Z = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.5])            # z / thickness
SH_TOP = np.arange(6)


def shingle_variant(k):
    """pool of 16 hand-split shingle base shapes (producer note 3): ragged butt notches, corner
    rounding, cup, curl, butt thickness.  Placement only scales / bends them onto the cone."""
    rs = np.random.RandomState(6060 + k)
    offs = rs.uniform(-0.012, 0.012, 10)
    offs[[0, 5, 6, 7, 8, 9]] *= 0.4
    for c_ in rs.choice([1, 2, 3, 4], rs.randint(2, 4), replace=False):
        offs[c_] += rs.uniform(0.012, 0.022)
    offs += SH_LOOP_X * rs.uniform(-0.012, 0.012)
    offs[[7, 8]] = offs[[5, 0]]
    offs[[6, 9]] = offs[[5, 0]]
    return dict(offs=offs, rc=rs.uniform(0.03, 0.07), cup=rs.uniform(0.002, 0.008), Tb=rs.uniform(0.034, 0.042),
                curl=rs.uniform(0.0, 0.005), curl_eave=rs.uniform(0.006, 0.016))


SH_VARIANTS = [shingle_variant(k) for k in range(16)]


def shingle_mesh(W, L, var, Th=0.01, curl=None, ys=None, bottom=True, head=True):
    """one shingle in local coords: x across (W), y from butt (0) to head (L), z up (0..thickness).
    Section loop: 6 top points (cup), rounded side edges, ONE bottom strip (the underside lies on the
    course below and is never seen), n-gon end caps.  Thickness tapers as on a full 0.72 m shingle,
    so a trimmed shingle is the exposed part of a real one."""
    if ys is None:
        base = [0.0, 0.006, 0.018, 0.04, 0.075, 0.13]
        ys = np.array(base + list(np.arange(0.2, L - 0.03, 0.07)) + [L])
    ys = np.asarray(ys, float)
    n, m = len(ys), len(SH_LOOP_X)
    Tb = var["Tb"]
    cup = var["cup"]
    curl = var["curl"] if curl is None else curl
    rc = var["rc"]
    Y = np.broadcast_to(ys[:, None], (n, m)).copy()
    X = np.broadcast_to(SH_LOOP_X[None, :] * W / 2, (n, m)).copy()
    thick = Tb - (Tb - Th) * np.clip(ys / 0.72, 0, 1)
    Z = SH_LOOP_Z[None, :] * thick[:, None]
    # rounded butt corners in plan
    x_edge = W / 2 - rc + np.sqrt(np.clip(rc ** 2 - (rc - np.minimum(ys, rc)) ** 2, 0, None))
    shrink = (W / 2 - x_edge)[:, None] * smoothstep(0.5, 1.0, np.abs(SH_LOOP_X))[None, :]
    X = X - np.sign(X) * shrink
    # ragged hand-split butt on the first rings; arris rounding: ring 0 inset
    Y[:2] += var["offs"][None, :] * np.array([[1.0], [0.85]])
    X[0] *= 1 - 0.008 / max(W, 0.1)
    Z[0] = Z[0] * 0.8 + thick[0] * 0.1
    # cup (edges lift) and curl (butt lifts)
    Z = Z + cup * (2 * X / W) ** 2 + curl * (1 - np.clip(Y / 0.72, 0, 1)) ** 2
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    j1 = (j + 1) % m
    jj = j if bottom else j[:, SH_LOOP_Z[j[0]] + SH_LOOP_Z[j1[0]] > 0]       # drop the underside strip
    jj1 = (jj + 1) % m
    F = [np.stack([i * m + jj, i * m + jj1, (i + 1) * m + jj1, (i + 1) * m + jj], -1).reshape(-1, 4),
         np.arange(m)[::-1][None, :] * 1]
    if head:
        F.append(((n - 1) * m + np.arange(m))[None, :])
    uv = np.stack([V[:, 0] / max(W, 1e-3) + 0.5, V[:, 1]], -1)
    return V, F, uv


FULL_WIN_DEG = 66.0     # back-arc window seen through the doorway: shingles full length, no blocker
FULL_WIN_Z = 4.0


def build_roof_blocker(coll):
    """dark blocker surface (producer note 6): a plain cone under the rafters over the front arc, where
    the shingles are modelled only as their exposed part + overlap.  It keeps the interior seen through
    the doorway dark (no light through the trimmed joints); it is never visible from outside."""
    acc = Acc("HUT_roof_blocker", 30, cull=None)
    az = np.linspace(0, 2 * np.pi, 97)
    th = az2th(az)
    s0, s1 = s_at_r(R_WALL + 0.06), S_END - 0.05
    ss = np.linspace(s0, s1, 13)
    TH, SS = np.meshgrid(th, ss, indexing="ij")
    P, ts, tt, n = surf_frame(TH.ravel(), SS.ravel())
    P = P - n * (BATTEN_T + 2 * RAFT_R + 0.02)
    F = grid_quads(len(th), len(ss))[:, ::-1]
    # leave open the window whose underside is seen through the doorway (full-length shingles there)
    AZ = np.broadcast_to(az[:, None], TH.shape).ravel()
    win = (np.abs(np.angle(np.exp(1j * (AZ - np.pi)))) < math.radians(FULL_WIN_DEG - 4)) & (P[:, 2] < FULL_WIN_Z - 0.25)
    F = F[~win[F].all(axis=1)]
    acc.add(P, F, "M_timber_weathered")
    acc.build(coll)


def build_shingles(coll):
    """17 courses + doubled starter.  Each shingle is modelled as its exposed part plus ~6.5 cm of
    covered overlap (producer note 6); shingles keep their full 0.72 m length where their covered part
    can be seen: under a missing shingle of the course above, under a slipped one, and in the back arc
    whose underside shows through the doorway."""
    acc = Acc("HUT_roof_shingles", 45)
    st_acc = Acc("HUT_roof_starter", 45)
    rng = np.random.RandomState(606)
    B_WEDGE = 0.066
    OV = 0.065

    def place(acc_, th_c, s_b, W, L, var, phi, lift, curl, base_fn, ys=None, closed=True):
        Pl, F, uv = shingle_mesh(W, L, var, curl=curl, ys=ys, bottom=closed, head=closed)
        x, y, z = Pl[:, 0], Pl[:, 1], Pl[:, 2]
        c, s_ = math.cos(phi), math.sin(phi)
        xr = x * c - y * s_
        yr = x * s_ + y * c
        v = np.clip(y / 0.72, 0, 1)
        ss = s_b + yr
        th = np.full_like(ss, th_c)
        P0, ts, tt, n = surf_frame(th, ss)
        rb = float(np.hypot(*surf(th_c, s_b)[:2]))
        rcur = np.hypot(P0[:, 0], P0[:, 1])
        xr = xr * np.clip(rcur / rb, 0.3, 1.0)
        off = base_fn(v) + z + lift * (1 - v)
        V = P0 + tt * xr[:, None] + n * off[:, None]
        acc_.add(V, F, "M_roof_shingle", uv, smooth=True)

    # ---- doubled starter course (underside seen from below at the eave)
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
        var = dict(SH_VARIANTS[rng.randint(16)])
        var["Tb"] = 0.034
        var["cup"] = 0.002
        place(st_acc, thc, s_b, w[i], 0.46, var, math.radians(rng.uniform(-1.5, 1.5)), 0.0, 0.0,
              lambda v: 0.0 * v, ys=[0.0, 0.006, 0.018, 0.04, 0.12, 0.46])
    prev_joints = np.mod(off0 + np.cumsum((w + gaps) / rb), 2 * math.pi)

    # ---- pass 1: lay out every course (positions, widths, damage)
    courses = []
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
        best, best_d = 0.0, -1
        for _ in range(12):
            o = rng.uniform(0, 2 * math.pi)
            j = np.mod(o + np.cumsum((w + gaps) / rb), 2 * math.pi)
            dmin = np.min(np.abs(np.angle(np.exp(1j * (j[:, None] - prev_joints[None, :])))), axis=1) * rb
            sc = np.min(dmin)
            if sc > best_d:
                best_d, best = sc, o
        acc_ang = best
        recs = []
        for i in range(n):
            dth = (w[i] + gaps[i]) / rb
            thc = acc_ang + dth / 2
            acc_ang += dth
            ri = rng.rand()
            rec = dict(k=k, thc=thc, half=w[i] / 2 / rb, W=w[i], ri=ri,
                       sb=s_b + cwave[int((thc % (2 * np.pi)) / (2 * np.pi) * 512) % 512] + rng.uniform(-0.012, 0.012),
                       lift=rng.uniform(0.0, 0.015), phi=math.radians(rng.uniform(-4.5, 4.5)),
                       var=rng.randint(16), slip=0.0, missing=False, full=False)
            if k > 0 and k < N_COURSES - 1 and ri < 0.012:
                rec["missing"] = True
            elif k > 0 and 0.012 < ri < 0.03:
                rec["slip"] = rng.uniform(0.05, 0.11)
                rec["lift"] += 0.016
                rec["phi"] += math.radians(rng.uniform(-4, 4))
            recs.append(rec)
        courses.append(recs)
        prev_joints = np.mod(best + np.cumsum((w + gaps) / rb), 2 * math.pi)
    # ---- pass 2: which covered parts can be seen -> full length there
    for k in range(N_COURSES - 1):
        holes = [(r["thc"], r["half"] + 0.02) for r in courses[k + 1] if r["missing"]]
        for r in courses[k]:
            for (tc, hh) in holes:
                if abs(float(np.angle(np.exp(1j * (r["thc"] - tc))))) < r["half"] + hh:
                    r["full"] = True
    n_total = n_full = 0
    for k, recs in enumerate(courses):
        s_b = k * SH_EXPOSE
        base_fn = (lambda v: 0.037 * (1 - v)) if k == 0 else (lambda v: B_WEDGE * (1 - v))
        for r in recs:
            if r["missing"]:
                continue
            az = float(r["thc"]) + math.pi / 2
            zb = float(surf(r["thc"], r["sb"])[2])
            if interior_visible(az, math.radians(FULL_WIN_DEG)) and zb < FULL_WIN_Z:
                r["full"] = True
            L_full = min(SH_LEN, S_END - s_b + 0.02)
            L = L_full if r["full"] else min(SH_EXPOSE + OV + r["slip"], L_full)
            var = SH_VARIANTS[r["var"]]
            curl = var["curl_eave"] if k < 2 else var["curl"]
            sb = r["sb"] - r["slip"]
            thc, Wi, phi, lift = r["thc"], r["W"], r["phi"], r["lift"]
            rb = float(np.hypot(*surf(0.0, s_b)[:2]))
            dd_door = abs(float(np.angle(np.exp(1j * (thc + np.pi / 2)))))
            door_eave = (k < 4) and dd_door < 1.0 and (0.03 < r["ri"] < 0.13)
            n_full += r["full"]
            # underside (lies on the course below) and head end (under the course above) are only
            # modelled where they can be seen: eave courses, full-length shingles, slipped ones
            closed = k < 2 or r["full"] or r["slip"] > 0
            if (0.03 < r["ri"] < 0.045 or door_eave) and Wi > 0.34:      # split into two pieces
                g = 0.012
                wa = Wi * rng.uniform(0.4, 0.6)
                wb = Wi - wa - g
                tha = thc - (Wi / 2 - wa / 2) / rb
                thb = thc + (Wi / 2 - wb / 2) / rb
                place(acc, tha, sb, wa, L, var, phi - 0.02, lift, curl, base_fn, closed=closed)
                place(acc, thb, sb + 0.01, wb, L - 0.01, var, phi + 0.025, lift + 0.004, curl, base_fn, closed=closed)
                n_total += 2
                continue
            place(acc, thc, sb, Wi, L, var, phi, lift, curl, base_fn, closed=closed)
            n_total += 1
    log("shingles:", n_total, "full-length (covered part visible):", n_full)
    SHINGLE_TOP["V"] = np.concatenate(acc.V + st_acc.V)
    acc.build(coll)
    st_acc.build(coll)


# =============================================================================================
# apex collar + finial
# =============================================================================================
SHINGLE_TOP = {}


def collar_drip_z(clear=0.02):
    """lowest fascia-bottom height that clears every shingle vertex under the 53 deg collar."""
    V = SHINGLE_TOP["V"]
    r = np.hypot(V[:, 0], V[:, 1])
    m = r < COLLAR_R + 0.03
    need = V[m, 2] - np.maximum(COLLAR_R - r[m], 0.0) * math.tan(COLLAR_PITCH) * 0.97
    return float(need.max()) + clear


def ccw(prof):
    prof = np.asarray(prof, float)
    x, y = prof[:, 0], prof[:, 1]
    area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    return prof if area > 0 else prof[::-1]


def build_collar_finial(coll):
    """lead-hat collar (smooth 53 deg cone, dia 1.49, 6.5 cm drip fascia standing ~8 cm off the
    shingles, rolled drip bead, 10 folded standing seams), bell-cast upper collar (dia 0.57) with its
    own 4.5 cm drip, turned spindle (bead ring 0.20 / neck 0.10 / bulb 0.18) and a conical spike.
    Upper collar + finial lean 1 deg."""
    acc = Acc("HUT_cap_collar", 50)
    fin = Acc("HUT_finial", 50)
    R = COLLAR_R
    tp = math.tan(COLLAR_PITCH)
    zf = collar_drip_z()                     # fascia bottom (drip line)
    FD = 0.065                               # fascia depth
    zd = zf + FD                             # where the cone surface meets the fascia top
    r_top = 0.25
    z_top = zd + (R - r_top) * tp
    seed = 808

    def dent(th, z):
        return 1 + 0.007 * n2(th * 2.2, np.full_like(th, z * 3), seed) + 0.003 * n2(th * 7, np.full_like(th, z * 9), seed + 1)

    # CCW in (r,z): underside (from the axis outward), fascia inner face, drip bead, fascia, cone
    under = [(0.0, zf + 0.70)] + [(r_, zf + 0.012 + (R - r_) * tp * 0.97) for r_ in np.linspace(0.4, R - 0.03, 2)]
    prof = under + [(R - 0.018, zf + 0.04), (R - 0.016, zf + 0.012),
            (R - 0.012, zf + 0.001), (R - 0.002, zf - 0.004), (R + 0.008, zf + 0.0), (R + 0.0135, zf + 0.009),
            (R + 0.012, zf + 0.019), (R + 0.004, zf + 0.026), (R + 0.0015, zf + 0.035), (R + 0.001, zd - 0.012),
            (R - 0.002, zd - 0.003), (R - 0.009, zd + 0.004)]
    for f in np.linspace(0.04, 1.0, 14):
        rr = (R - 0.012) - (R - 0.012 - r_top + 0.0) * f
        prof.append((rr, zd + (R - rr) * tp))
    prof.append((0.2, z_top + 0.01))
    prof.append((0.0, z_top + 0.02))
    V, F, uv, w = lathe(prof, 128, rfunc=dent)
    acc.add(V, F, "M_lead", uv, w)
    # folded standing seams (raised 6-8 mm fins with soft fillets), 10 of them
    fin_prof = ccw([(-0.003, 0.0), (-0.0012, 0.013), (0.0018, 0.0058), (0.0052, 0.0034), (0.0074, 0.0014),
                    (0.0076, -0.0012), (0.0054, -0.0032), (0.002, -0.0056), (-0.0012, -0.013)])
    for k in range(10):
        th = 2 * np.pi * k / 10 + 0.13 + 0.03 * math.sin(k * 2.7)
        rr = np.linspace(R - 0.02, r_top + 0.01, 16)
        zz = zd + (R - rr) * tp
        dd = dent(np.full_like(rr, th), zz)
        path = np.stack([np.cos(th) * rr * dd, np.sin(th) * rr * dd, zz], -1)
        nrmv = np.array([math.cos(th) * math.sin(COLLAR_PITCH), math.sin(th) * math.sin(COLLAR_PITCH),
                         math.cos(COLLAR_PITCH)])
        path = path + nrmv * 0.001
        P, Fp, uvp, wp = tube(path, 1.0, len(fin_prof), up=tuple(nrmv), profile=fin_prof)
        acc.add(P, Fp, "M_lead", uvp, wp)
    # ---- upper collar (bell-cast), leaning 1 deg with the finial
    lean = rotx(math.radians(0.75)) @ roty(math.radians(-0.65))
    piv = np.array([0.0, 0.0, z_top])
    ru = 0.285
    zu0 = z_top - 0.03                       # its drip bottom (4.5 cm fascia)
    zu1 = zu0 + 0.045
    H_u = 0.30
    prof_u = [(0.0, z_top - 0.02), (ru - 0.03, zu0 + 0.012), (ru - 0.014, zu0 + 0.004), (ru - 0.006, zu0 - 0.002),
              (ru + 0.005, zu0 + 0.002), (ru + 0.009, zu0 + 0.01), (ru + 0.006, zu0 + 0.018),
              (ru + 0.001, zu0 + 0.024), (ru, zu1 - 0.006), (ru - 0.005, zu1 + 0.002)]
    for f in np.linspace(0.06, 1.0, 10):           # straight 54 deg cone, r 0.285 -> 0.07 over 0.30 m
        r_ = 0.07 + (ru - 0.012 - 0.07) * (1 - f)
        prof_u.append((r_, zu1 + (H_u - 0.015) * f))
    z_s = zu1 + H_u - 0.015
    prof_u.append((0.0, z_s + 0.004))
    V, F, uv, w = lathe(prof_u, 64, rfunc=lambda th_, z_: 1 + 0.005 * np.sin(2 * th_ + 0.4))
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_lead", uv, w)
    # ---- turned spindle (timber), ref2's stack: bead ring -> tapered spindle -> ring
    sp = [(0.0, z_s - 0.01), (0.068, z_s - 0.01), (0.082, z_s + 0.004),                                # seat
          (0.096, z_s + 0.018), (0.101, z_s + 0.036), (0.097, z_s + 0.054), (0.08, z_s + 0.066),       # bead ring
          (0.066, z_s + 0.076), (0.064, z_s + 0.12), (0.059, z_s + 0.2), (0.053, z_s + 0.28),          # tapered spindle
          (0.052, z_s + 0.3), (0.07, z_s + 0.312), (0.094, z_s + 0.328), (0.1, z_s + 0.346),           # ring
          (0.097, z_s + 0.366), (0.085, z_s + 0.379), (0.0, z_s + 0.385)]
    V, F, uv, w = lathe(sp, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_timber", uv, w)
    # ---- spike (iron): base dia 0.19, knop ring ~0.2 m up, straight taper to a sharp point
    z_k = z_s + 0.383
    tip = max(FINIAL_TIP, z_k + 0.6)
    Hs = tip - z_k
    rb_ = 0.095

    def r_sp(h):
        return rb_ * (1 - h / Hs) + 0.0008
    hk = 0.2
    spk = [(0.0, z_k - 0.003), (rb_ - 0.004, z_k - 0.003), (rb_, z_k + 0.004), (r_sp(0.012), z_k + 0.012),
           (r_sp(hk - 0.02), z_k + hk - 0.02), (r_sp(hk - 0.014) + 0.013, z_k + hk - 0.012),
           (r_sp(hk) + 0.015, z_k + hk), (r_sp(hk + 0.014) + 0.013, z_k + hk + 0.012),
           (r_sp(hk + 0.02), z_k + hk + 0.02)]
    for f in np.linspace(0.0, 1.0, 9)[1:]:
        h = hk + 0.02 + (Hs - 0.006 - hk - 0.02) * f
        spk.append((r_sp(h), z_k + h))
    spk += [(0.0, tip)]
    V, F, uv, w = lathe(spk, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_iron", uv, w)
    acc.build(coll)
    fin.build(coll)
    return zf, zd, z_top, z_s, z_k, tip


# =============================================================================================
# plinth, rubble, apron, path
# =============================================================================================
R_PL_FACE = 3.76            # plinth outer face line (rough wall line, +-4 cm)
PLINTH_TOP = 0.33
STEP_C = (0.04, FRONT_Y - 0.50)       # step stone centre (x, y)
APRON_RIM = 4.62
R_FLOOR_EDGE = 3.36         # inside this radius the ground is the interior earth floor


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
                face_fr=(0.0, 0.34, 0.6, 0.8, 0.93), sm_scale=1.0, n_facet=0, frac_k=(0.004, 0.01)):
    """irregular stone as an open SHELL: an exposed face (domed, tilted, crossed by 1-2 fracture planes
    with 3-8 cm edge breaks, faint pitting), a rounded arris whose radius varies round the outline, and
    sides running back `depth` -- no back face (it is never visible: producer note 6).
    Local frame: outline in (u, v), face normal +w.  Returns V (u, v, w), faces."""
    Rf = outline_radius(rng, kind, sm_scale=sm_scale)
    th = 2 * np.pi * np.arange(n_th) / n_th + rng.uniform(0, 0.1)
    Rn = Rf(th)
    ou, ov = hu * Rn * np.cos(th), hv * Rn * np.sin(th)
    Rabs = np.hypot(ou, ov)
    seed = rng.randint(1, 10 ** 6)
    rr_t = np.clip(rng.uniform(*rr) * (1 + 0.45 * ring_noise(th, seed + 3, 4, 1.0)), 0.004, 0.07)
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
        u0 = ext * rng.uniform(0.0, 0.35)
        fr.append((psi, u0, rng.uniform(0.12, 0.3), rng.uniform(0.003, 0.007), dome * rng.uniform(0.6, 0.9)))

    def yf(u, v):
        q = np.clip((u / hu) ** 2 + (v / hv) ** 2, 0, 1.4)
        w = dome * (1 - q) + ta * u / max(hu, hv) * max(hu, hv) * 1.0 + tb * v
        w = w + noise * fbm(np.stack([u * freq + off[0], v * freq + off[1], np.full(np.shape(u), off[2])], -1), 3)
        w = w + noise * 0.35 * vnoise(np.stack([u * freq * 4.1, v * freq * 4.1, np.full(np.shape(u), off[2] + 3)], -1))
        for (psi, u0, slope, k, wref) in fr:
            uu = u * math.cos(psi) + v * math.sin(psi)
            plane = wref - (uu - u0) * slope
            w = smin(w, plane, k)
        if dish:
            w = w - dish * np.clip(1 - q * 1.3, 0, 1) ** 0.8
        if flat_face is not None:
            w = np.where(w > flat_face, flat_face + (w - flat_face) * 0.15, w)
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
        sc = (Rabs + bul) / np.maximum(Rabs, 1e-6)
        ww = (w_e - rr_t) + tt * (w_back - (w_e - rr_t))
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


def plinth_face_r(az):
    return R_PL_FACE + 0.018 * ring_noise(np.asarray(az, float), 9091, 6, 1.0)


def floor_z(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    R_ = np.hypot(X, Y)
    z = (SILL_TOP - 0.004 + 0.008 * fbm(np.stack([X * 1.2, Y * 1.2, np.zeros_like(X)], -1), 3)
         - 0.015 * np.exp(-(R_ / 0.9) ** 2))
    # trodden hollow just inside the sill: the floor steps down ~2.5 cm from the sill top
    door = np.exp(-(X / 0.9) ** 2) * (1 - smoothstep(-3.45, -2.4, Y))
    return z - 0.024 * door


FLAGS = []          # planned path flags + step stone (dicts), used by the apron lips and the geometry


def _mound(X, Y):
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    rim = APRON_RIM + 0.10 * ring_noise(th, 1111, 5, 1.0)
    m = 1 - smoothstep(rim - 0.85, rim, r)
    h = Z_MIN + (0.0 - Z_MIN) * m
    lumps = 0.010 * fbm(np.stack([X * 0.9, Y * 0.9, np.zeros_like(X)], -1), 3) * m
    dr = r - (4.17 + 0.03 * ring_noise(th, 1112, 5, 1.0))
    trench = -0.028 * np.exp(-(dr / 0.13) ** 2) * (1 - (np.abs(X) < 1.1) * (Y < 0))
    bank = (0.05 + 0.015 * ring_noise(th, 1116, 9, 1.0)) * (1 - smoothstep(3.80, 4.05, r)) \
        * (1 - np.exp(-(X / 0.9) ** 2) * (Y < 0))
    return h + (lumps + trench) * m + bank


def _path_mound(X, Y):
    """earth of the trodden path running out from the door, beyond the apron mound."""
    w = 0.95 + 0.12 * n2(Y * 1.3, 0.5, 1130)
    core = (1 - smoothstep(w * 0.75, w * 1.2, np.abs(X - 0.06 * np.sin(Y * 1.1)))) * \
        (1 - smoothstep(-6.55, -7.05, Y)) * (Y < -3.6)
    hz = -0.006 + 0.008 * fbm(np.stack([X * 2.0, Y * 2.0, np.full(X.shape, 4.0)], -1), 2)
    hz = hz - 0.012 * np.exp(-(X / 0.5) ** 2)                  # wear hollow along the path
    return Z_MIN + (hz - Z_MIN) * core


def earth_base(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    return np.maximum(_mound(X, Y), _path_mound(X, Y))


def flag_local(fl, X, Y):
    c, s = math.cos(fl["rot"]), math.sin(fl["rot"])
    dx, dy = X - fl["c"][0], Y - fl["c"][1]
    u = dx * c + dy * s
    v = -dx * s + dy * c
    th = np.arctan2(v / fl["hv"], u / fl["hu"])
    rn = fl["R"](th)
    rabs = np.hypot(fl["hu"] * rn * np.cos(th), fl["hv"] * rn * np.sin(th))
    return np.hypot(u, v), rabs


def apron_height(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    base = earth_base(X, Y)
    out = base
    for fl in FLAGS:
        if np.all((np.abs(X - fl["c"][0]) > fl["ext"] + 0.12) | (np.abs(Y - fl["c"][1]) > fl["ext"] + 0.12)):
            continue
        rho, rabs = flag_local(fl, X, Y)
        dout = rho - rabs
        # soft earth lip wrapping the edge: rises to 1-1.5 cm under the top at the outline, gone 7 cm out
        lip_top = fl["top"] - fl["lip"]
        lip = lip_top - (lip_top - base) * smoothstep(0.0, fl["lip_w"], dout)
        lip = lip + 0.003 * n2(X * 30, Y * 30, 1140)
        out = np.where(dout < fl["lip_w"], np.maximum(out, lip), out)
    return out


def ground_z(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    r = np.hypot(X, Y)
    return np.where(r < R_FLOOR_EDGE, floor_z(X, Y), apron_height(X, Y))


def cull_below_ground(V):
    """vertex is never visible: more than 1.2 cm under the local ground (apron or floor)."""
    hid = np.zeros(len(V), bool)
    low = V[:, 2] < 0.26
    if low.any():
        g = ground_z(V[low, 0], V[low, 1])
        hid[low] = V[low, 2] < g - 0.012
    return hid


def plan_path():
    """lay out the step stone and the stepping-stone path BEFORE the apron is built (the apron grows a
    soft earth lip round every flag)."""
    rng = np.random.RandomState(1414)
    # step stone (top ~0.09-0.10, the earth banked round it)
    FLAGS.append(dict(kind="step", c=(STEP_C[0], STEP_C[1]), rot=0.05, hu=0.62, hv=0.36, ext=0.7,
                      R=outline_radius(rng, "flag"), top=0.095, th=0.13, lip=0.035, lip_w=0.11, seed=77))
    ys = -4.62
    k = 0
    while ys > -6.55:
        ly = rng.uniform(0.17, 0.24)
        two = rng.rand() < 0.6
        xc = 0.07 * math.sin(k * 1.7) + rng.uniform(-0.1, 0.1)
        if two:
            lxa, lxb = rng.uniform(0.2, 0.3), rng.uniform(0.18, 0.28)
            gap = rng.uniform(0.05, 0.1)
            xs_ = [(xc - gap / 2 - lxa, lxa), (xc + gap / 2 + lxb, lxb)]
        else:
            lx = rng.uniform(0.3, 0.42)
            xs_ = [(xc + rng.uniform(-0.08, 0.08), lx)]
        for (xo, lx) in xs_:
            lyy = ly * rng.uniform(0.85, 1.1)
            yo = ys - ly + rng.uniform(-0.04, 0.04)
            b = float(earth_base(np.array([xo]), np.array([yo]))[0])
            FLAGS.append(dict(kind="flag", c=(xo, yo), rot=rng.uniform(-0.4, 0.4), hu=lx, hv=lyy,
                              ext=max(lx, lyy) * 1.15, R=outline_radius(rng, "flag"),
                              top=b + rng.uniform(0.018, 0.03), th=rng.uniform(0.085, 0.11),
                              lip=rng.uniform(0.008, 0.014), lip_w=rng.uniform(0.05, 0.08),
                              seed=rng.randint(10 ** 5)))
        ys -= 2 * ly + rng.uniform(0.07, 0.13)
        k += 1
    log("path flags planned:", len(FLAGS) - 1)


def build_path(coll):
    """step stone + flags: non-convex 10-16 corner outlines with edge noise and notches, thickness
    +-2 cm, tops tilted 1-3 deg, arris rounding 0.5-3 cm varying round the outline, bases buried."""
    acc = Acc("HUT_path_stones", 40)
    for fl in FLAGS:
        rng = np.random.RandomState(fl["seed"])
        if fl["kind"] == "step":
            V, F = shell_stone(fl["hu"], fl["hv"], rng, "flag", fl["th"], rr=(0.008, 0.028), dome=0.004,
                               tilt=0.01, n_frac=2, frac_depth=(0.015, 0.03), n_th=72, noise=0.003, freq=5.0,
                               side_bulge=0.006, thick_var=0.12, dish=0.016,
                               face_fr=(0.0, 0.18, 0.36, 0.54, 0.7, 0.84, 0.94))
        else:
            V, F = shell_stone(fl["hu"], fl["hv"], rng, "flag", fl["th"], rr=(0.005, 0.03), dome=0.008,
                               tilt=math.tan(math.radians(rng.uniform(1, 3))) / 1.4, n_frac=2,
                               frac_depth=(0.012, 0.03), frac_k=(0.003, 0.006), n_facet=2, n_th=60, noise=0.009,
                               freq=3.5, side_bulge=0.004, thick_var=0.2, sm_scale=0.6,
                               face_fr=(0.0, 0.3, 0.55, 0.75, 0.9))
        V[:, 2] += fl["top"] - V[0, 2]
        add_shell(acc, V, F, "plan", rotz(fl["rot"]), (fl["c"][0], fl["c"][1], 0.0), "M_stone")
    acc.build(coll)


def build_plinth(coll):
    """dry-stone plinth after ref2: mostly ONE course of low rounded boulders (0.4-0.7 m long),
    irregular elevation outlines (rounded trapezoid / D / rounded triangle, no parallel sides), domed
    and tilted faces crossed by fracture planes, arris rounding 1-6 cm per stone, ~22 % two-high with a
    clearly smaller upper.  Stones are open shells (face + sides back to the wattle line).  Chinking
    wedges are ray-tested so every one sits >= 2 cm behind both neighbouring faces and is visible."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    acc = Acc("HUT_plinth_stones", 60)
    rng = np.random.RandomState(9191)
    r_c = 3.62
    a_start = math.asin(1.30 / 3.78)
    a_end = 2 * math.pi - a_start
    post_az = list(POST_AZ)
    a = a_start
    stones = []
    while a < a_end - 0.02:
        L = rng.uniform(0.40, 0.70)
        if rng.rand() < 0.12:
            L = rng.uniform(0.72, 0.85)         # long through-stone
        if a + L / r_c > a_end:
            L = (a_end - a) * r_c
            if L < 0.25:
                stones[-1][1] += L * 0.6
                break
        stones.append([a + (L / 2) / r_c, L])
        a += (L - rng.uniform(0.0, 0.04)) / r_c
    kinds = ["trap", "D", "trap", "tri", "D", "trap"]
    n_two = 0
    placed = []          # (az, z_top, L) for chinking

    def place(V, F, az, z_bot, face_off=0.0, rot=(0.0, 0.0, 0.0)):
        P, flip = map_uvw(V, "wall")
        Ff = [f[:, ::-1] for f in F] if flip else F
        R = rotz(az) @ rotx(rot[0]) @ roty(rot[1]) @ rotz(rot[2])
        Pw = xf(P, R)
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        rf = float(plinth_face_r(az)) + face_off
        c = u * (rf - float((Pw @ u).max()))
        c[2] = z_bot - float(Pw[:, 2].min())
        acc.add(Pw + c, Ff, "M_stone")
        return c

    for i, (ac, L) in enumerate(stones):
        near_post = min(abs(np.angle(np.exp(1j * (ac - pa)))) for pa in post_az) * r_c < L / 2 + 0.05
        top = PLINTH_TOP + (rng.uniform(-0.015, 0.025) if not near_post else rng.uniform(-0.005, 0.008))
        bot = -0.035
        two = (rng.rand() < 0.5) and L > 0.46 and not near_post
        kind = kinds[rng.randint(len(kinds))] if not near_post else "trap"
        depth_face = plinth_face_r(ac) - (R_WALL - 0.06)            # face -> just behind the wattle line
        rr = (rng.uniform(0.008, 0.035), rng.uniform(0.015, 0.05))
        rr = (min(rr), max(rr))
        if not two:
            H = top - bot
            V, F = shell_stone(L / 2, H / 2, rng, kind, depth_face, rr=rr, dome=rng.uniform(0.02, 0.045),
                               tilt=math.tan(math.radians(rng.uniform(5, 15))) / 1.4, n_frac=rng.randint(1, 3),
                               frac_depth=(0.04, 0.08), frac_k=(0.003, 0.006), n_facet=rng.randint(2, 4),
                               noise=0.006, freq=6.0, side_bulge=0.0, sm_scale=0.25, n_th=56,
                               face_fr=(0.0, 0.25, 0.45, 0.62, 0.78, 0.9))
            V[:, 1] *= 1.0
            place(V, F, ac, bot, face_off=rng.uniform(-0.015, 0.02),
                  rot=(rng.uniform(-0.04, 0.04), rng.uniform(-0.05, 0.05), 0.0))
            placed.append((ac, top, L, None))
        else:
            n_two += 1
            lo_top = rng.uniform(0.15, 0.21)
            H = lo_top - bot
            V, F = shell_stone(L / 2, H / 2, rng, rng.choice(["trap", "D"]), depth_face, rr=rr,
                               dome=rng.uniform(0.02, 0.04), tilt=math.tan(math.radians(rng.uniform(5, 12))) / 1.4,
                               n_frac=rng.randint(1, 3), frac_depth=(0.04, 0.07), frac_k=(0.003, 0.006),
                               n_facet=rng.randint(1, 3), noise=0.006, freq=6.0, side_bulge=0.0, sm_scale=0.25,
                               n_th=52)
            place(V, F, ac, bot, face_off=rng.uniform(0.0, 0.02), rot=(rng.uniform(-0.03, 0.03), 0.0, 0.0))
            Lu = L * rng.uniform(0.55, 0.75)
            Hu = top - lo_top + 0.006
            xo = rng.uniform(-0.12, 0.12) * L
            Vu, Fu = shell_stone(Lu / 2, Hu / 2, rng, rng.choice(["D", "tri", "trap"]), depth_face - 0.03,
                                 rr=(0.01, min(0.04, Hu * 0.3)), dome=rng.uniform(0.015, 0.035),
                                 tilt=math.tan(math.radians(rng.uniform(5, 15))) / 1.4, n_frac=1, n_th=40,
                                 frac_depth=(0.03, 0.06), frac_k=(0.003, 0.006), n_facet=rng.randint(1, 3),
                                 noise=0.005, freq=7.0, side_bulge=0.004, sm_scale=0.5)
            place(Vu, Fu, ac + xo / r_c, lo_top - 0.008, face_off=-rng.uniform(0.02, 0.05),
                  rot=(rng.uniform(-0.05, 0.05), rng.uniform(-0.06, 0.06), 0.0))
            placed.append((ac, top, L, (ac + xo / r_c, lo_top, Lu)))
    log("plinth stones:", len(stones), "two-high:", n_two, f"({100 * n_two / len(stones):.0f} %)")
    stones_ob = acc.build(coll)
    # ---------------- chinking: pooled wedge variants, ray-tested recess + visibility
    me = stones_ob.data
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])

    def face_r(az, z):
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        o = u * 4.6 + np.array([0, 0, z])
        hit = bvh.ray_cast(Vector(o), Vector(-u), 2.0)
        if hit[0] is None:
            return None
        return 4.6 - hit[3]

    def make_chink(acc_, k):
        rs = np.random.RandomState(7300 + k)
        hu_, hv_ = rs.uniform(0.022, 0.045), rs.uniform(0.016, 0.03)
        V, F = shell_stone(hu_, hv_, rs, "pad", 0.05, rr=(0.004, 0.008), dome=0.006, tilt=0.12, n_frac=1,
                           frac_depth=(0.004, 0.01), n_th=12, noise=0.002, freq=25.0, side_bulge=0.0,
                           face_fr=(0.0, 0.6))
        # wedge: the sides converge toward the back (driven in, thin end inward)
        bk = V[:, 2] < -0.004
        sc = 1 + V[bk, 2] / 0.05 * 0.7
        V[bk, 0] *= sc
        V[bk, 1] *= sc
        P, _ = map_uvw(V, "wall")
        acc_.add(P, F, "M_rubble")

    n_ch = n_try = 0
    ch_rng = np.random.RandomState(9393)
    cands = []
    for i in range(len(placed) - 1):
        ac, top, L, up = placed[i]
        ga = ac + (L / 2) / r_c
        for zc in (0.05, 0.13, 0.22, 0.31):
            cands.append((ga + ch_rng.uniform(-0.004, 0.004), zc + ch_rng.uniform(-0.03, 0.03)))
        if up is not None:
            for _ in range(2):
                cands.append((up[0] + ch_rng.uniform(-0.4, 0.4) * up[2] / r_c, up[1] + 0.003))
    for (az, zc) in cands:
        n_try += 1
        rL = face_r(az - 0.06 / R_PL_FACE, zc)
        rR = face_r(az + 0.06 / R_PL_FACE, zc)
        rC = face_r(az, zc)
        if rL is None or rR is None:
            continue
        front = min(rL, rR) - 0.02 - ch_rng.uniform(0.0, 0.015)
        if rC is not None and rC > front - 0.008:
            continue                     # no open joint here (stones touch) -> no chink needed / visible
        k = ch_rng.randint(8)
        mesh = pool_mesh("chink", k, make_chink)
        R = rotz(az) @ rotx(ch_rng.uniform(-0.25, 0.25)) @ roty(ch_rng.uniform(-0.4, 0.4))
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        place_instance(mesh, "plinth_chink", R, u * front + np.array([0, 0, zc]))
        n_ch += 1
    log("chinking:", n_ch, "of", n_try, "candidate joints")


def make_rubble_variant(acc, k):
    """half-buried spall / pebble: the part above the bedding cut only (cut plane = local z 0)."""
    rs = np.random.RandomState(8100 + k)
    half = np.array([rs.uniform(0.85, 1.15), rs.uniform(0.6, 0.95), rs.uniform(0.45, 0.75)]) * 0.1
    P, F = rock(half, rs, round_r=float(half.min()) * rs.uniform(0.3, 0.55), facets=(2, 4), segs=(5, 4, 4),
                warp=0.12, amp=0.004, freq=20.0, fillet=0.025, chips=rs.randint(0, 3))
    P[:, 2] += half[2] * (1 - 2 * rs.uniform(0.25, 0.45))   # bury 25-45 % of the height
    P[:, 2] = np.maximum(P[:, 2], -0.01)                    # flat bedding under the cut
    keep_f = (P[F, 2] > -0.0099).any(axis=1)
    acc.add(P, F[keep_f], "M_rubble")


def build_rubble(coll):
    """25-50 spalls / pebbles round the plinth foot and the door, linked duplicates of 10 variants."""
    rng = np.random.RandomState(1011)
    pts = []
    for i in range(26):
        az = rng.uniform(0.35, 2 * math.pi - 0.35)
        r = rng.choice([rng.uniform(3.84, 4.0), rng.uniform(4.05, 4.45)])
        pts.append((math.sin(az) * r, -math.cos(az) * r, rng.uniform(0.4, 1.4)))
    for i in range(12):
        x = rng.choice([-1, 1]) * rng.uniform(0.95, 1.7)
        y = rng.uniform(-4.6, -3.9)
        pts.append((x, y, rng.uniform(0.4, 1.1)))
    for (x_, y_, sc) in pts:
        k = rng.randint(10)
        mesh = pool_mesh("rubble", k, make_rubble_variant)
        g = float(apron_height(np.array([x_]), np.array([y_]))[0])
        R = rotz(rng.uniform(0, 6.28)) @ rotx(rng.uniform(-0.15, 0.15)) @ roty(rng.uniform(-0.15, 0.15))
        place_instance(mesh, "ground_rubble", R, (x_, y_, max(g - 0.004, Z_MIN + 0.0101 * sc)), scale=sc)
    log("rubble instances:", len(pts))


def apron_phi(X, Y):
    """signed 'inside' field of the earth apron's outer margin (> 0 inside, ~metres)."""
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    edge_r = (5.1 + 0.12 * ring_noise(th, 1113, 9, 1.0, 0.6) + 0.05 * ring_noise(th, 1114, 45, 1.0, 0.2))
    phi_ring = edge_r - r
    wx = 1.45 + 0.28 * n2(Y * 0.9, 0.3, 1131) + 0.08 * n2(Y * 3.1, 1.3, 1133) - np.abs(X + 0.15 * n2(Y * 0.5, 2.1, 1134))
    wy = Y + 7.35 - 0.18 * n2(X * 1.2, 0.7, 1132)
    phi_path = np.where(Y < -3.0, smin(wx, wy, 0.6), -1.0)
    return np.maximum(phi_ring, phi_path)


def build_apron(coll):
    """earth apron: one heightfield (4.5 cm grid) from under the plinth face out to an irregular soil
    margin, extended out along the path; outermost >= 0.4 m flat band at Z_MIN; soft lips round the
    flags; nothing below -5 cm.  Margin vertices are snapped onto the smooth margin curve (no grid
    stair-steps)."""
    acc = Acc("HUT_ground_apron", 30, cull=None)
    hs = 0.045
    xs = np.arange(-5.5, 5.5 + hs, hs)
    ys = np.arange(-7.7, 5.5 + hs, hs)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    r = np.hypot(X, Y)
    r_in = np.where((np.abs(X) < 1.35) & (Y < 0), 3.42, 3.64)
    phi = apron_phi(X, Y)
    inside = (phi > 0) & (r >= r_in)
    nx, ny = X.shape
    cell = inside[:-1, :-1] | inside[1:, :-1] | inside[:-1, 1:] | inside[1:, 1:]
    i = np.arange(nx - 1)[:, None]
    j = np.arange(ny - 1)[None, :]
    F = np.stack([i * ny + j, (i + 1) * ny + j, (i + 1) * ny + j + 1, i * ny + j + 1], -1)[cell]
    # snap outside corners of margin cells onto the phi = 0 curve (two Newton steps)
    Xf, Yf = X.ravel().copy(), Y.ravel().copy()
    used = np.zeros(len(Xf), bool)
    used[F.ravel()] = True
    mv = used & (phi.ravel() <= 0) & (r.ravel() > 4.0)
    for _ in range(3):
        px, py = Xf[mv], Yf[mv]
        f0 = apron_phi(px, py)
        e = 1e-3
        gx = (apron_phi(px + e, py) - apron_phi(px - e, py)) / (2 * e)
        gy = (apron_phi(px, py + e) - apron_phi(px, py - e)) / (2 * e)
        g2 = np.maximum(gx * gx + gy * gy, 1e-6)
        Xf[mv] = px - f0 * gx / g2
        Yf[mv] = py - f0 * gy / g2
    Z = np.maximum(apron_height(Xf, Yf), Z_MIN)
    P = np.stack([Xf, Yf, Z], -1)
    acc.add(P, F, "M_earth")
    acc.build(coll)


# =============================================================================================
# door assembly
# =============================================================================================
def timber_box(acc, center, half, R=None, ch=0.02, segs=(1, 1, 1), noise=0.0, seed=0, mat="M_timber",
               sag=0.0, splits=None):
    half = np.asarray(half, float)
    ax = int(np.argmax(half))
    if noise > 0:
        sg = list(segs)
        sg[ax] = max(sg[ax], int(half[ax] * 2 / 0.035))
        for k in range(3):
            if k != ax:
                sg[k] = max(sg[k], 3)
        segs = tuple(sg)
    V, F = rbox(half, ch, segs)
    if noise > 0:
        q = V / half
        dom = np.argmax(np.abs(q) - (np.arange(3) == ax) * 0.5, axis=1)
        nd = np.zeros_like(V)
        nd[np.arange(len(V)), dom] = np.sign(q[np.arange(len(V)), dom])
        sc = np.ones(3) * 18.0
        sc[ax] = 3.0
        rs = np.random.RandomState(seed + 500)
        o = rs.uniform(-50, 50, 3)
        hew = (noise * fbm(V * sc + o, 2)
               + 0.0028 * np.abs(np.sin(V[:, ax] / 0.11 * np.pi + 3 * vnoise(V * 6 + o)))  # adze scallops
               + 0.004 * vnoise(V * 1.5 + o * 2))
        V = V - nd * hew[:, None]
    if sag:
        t = V[:, 0] / half[0]
        V[:, 2] -= sag * (1 - t ** 2)
    V = xf(V, R, center)
    acc.add(V, F, mat)


def R_y_to(d, hint=(0, 0, 1)):
    """rotation whose local +Y axis points along d."""
    y = nrm(np.asarray(d, float))
    h = np.asarray(hint, float)
    if abs(float(np.dot(h, y))) > 0.9:
        h = np.array([1.0, 0, 0])
    x = nrm(np.cross(y, h))
    z = np.cross(x, y)
    return np.stack([x, y, z], -1)


def make_peg(acc, k):
    """whittled oak peg (pool variant): irregular octagon, head proud 1.5-1.8 cm along local +Y with a
    domed, slightly split head; only 1.2 cm of shank modelled inside the timber."""
    rs = np.random.RandomState(6100 + k)
    proud = rs.uniform(0.015, 0.018)
    r = 0.015 * rs.uniform(0.9, 1.1)
    path = np.linspace([0, -0.03, 0], [0, proud, 0], 4)
    ang = 2 * np.pi * np.arange(8) / 8 + rs.uniform(0, 1)
    rr = 1 + rs.uniform(-0.09, 0.09, 8)
    prof = np.stack([np.cos(ang) * rr, np.sin(ang) * rr], -1)
    path, rad = chamfer_path(path, np.full(4, r), 0.005)
    P, F, uv, w = tube(path, rad, 8, up=(0, 0, 1), profile=prof)
    top = P[:, 1] > proud - 0.004
    P[top, 1] += 0.002 * rs.uniform(-1, 1) * np.sign(P[top, 0])          # split / skewed head
    acc.add(P, F, "M_timber", uv, w)


def peg(p, d, rng):
    mesh = pool_mesh("peg", rng.randint(6), make_peg, 28)
    place_instance(mesh, "peg", R_y_to(d) @ rotx(0) @ np.eye(3), p)


def make_nail_head(acc, k):
    """forged nail head (pool variant), local +Y out of the iron, base at y=0."""
    rs = np.random.RandomState(6200 + k)
    rd = rs.uniform(0.0085, 0.0105)
    prof = [(0.0, -0.004), (rd * 0.9, -0.004), (rd, 0.0), (rd, 0.0015), (rd * 0.66, 0.0042), (0.0, 0.0054)]
    V, F, uv, w = lathe(prof, 8, rfunc=lambda t, z: 1 + 0.08 * np.sin(2 * t + k))
    acc.add(np.stack([V[:, 0], V[:, 2], V[:, 1]], -1), [f[:, ::-1] for f in F], "M_iron")


def make_clench(acc, k):
    rs = np.random.RandomState(6300 + k)
    V, F = rbox((0.004 * rs.uniform(0.9, 1.1), 0.003, 0.0045), 0.0012)
    V[:, 2] += V[:, 1] * rs.uniform(-0.3, 0.3)
    acc.add(V, F, "M_iron")


def build_door(coll):
    fr = Acc("HUT_door_frame", 28)      # adze ridges / checks read crisp; corner arcs are 18 deg
    leaf = Acc("HUT_door_leaf", 40)
    iron = Acc("HUT_door_ironwork", 50)
    thr = Acc("HUT_threshold", 50)
    rng = np.random.RandomState(1212)
    yc = FRONT_Y + 0.11                       # frame centre plane
    POST_BASE = 0.355
    RV = np.array([[0.0, 1, 0], [0, 0, 1], [1, 0, 0]])        # local X -> world Z (vertical member)
    for side in (-1, 1):
        x = side * 1.02
        # pad stone under each door post: rough boulder, irregular plan, flat bed for the post
        V, F = shell_stone(0.25, 0.20, rng, "pad", 0.30, rr=(0.02, 0.045), dome=0.004, tilt=0.01, n_frac=2,
                           frac_depth=(0.02, 0.05), n_th=36, noise=0.006, freq=5.0, side_bulge=0.02,
                           flat_face=0.0, face_fr=(0.0, 0.4, 0.7, 0.9))
        V[:, 2] += POST_BASE - 0.004
        add_shell(thr, V, F, "plan", rotz(side * 0.2 + rng.uniform(-0.1, 0.1)), (side * 1.05, -3.62, 0.0), "M_stone")
        # door posts (heavier, squared): front & door-side faces are hero faces, back face hidden
        wane_c = (3, 0) if side > 0 else (2, 1)
        inner_f, outer_f = (1, 3) if side > 0 else (3, 1)
        hewn_member(fr, (x, yc, (POST_BASE + HEAD_Z) / 2), ((HEAD_Z - POST_BASE) / 2, 0.12, 0.11),
                    rotz(side * 0.006) @ RV, rng, ch=0.02, wane=wane_c, n_checks=3,
                    check_faces=(2, 2, outer_f, inner_f), ns=9, nc=6, hero=(2, outer_f), hidden=(0, inner_f),
                    caps=(False, False))
        # inner jambs on the sill
        xj = side * 0.60
        hewn_member(fr, (xj, yc, (SILL_TOP + HEAD_Z) / 2), ((HEAD_Z - SILL_TOP) / 2, 0.10, 0.11),
                    rotz(side * 0.004) @ roty(side * 0.003) @ RV, rng, ch=0.018, wane=(2 if side > 0 else 3,),
                    n_checks=2, check_faces=(2, inner_f), ns=8, nc=6, hero=(2, inner_f), hidden=(0, outer_f),
                    caps=(False, False))
        # sole rail under the side panel, resting on the sill end
        hewn_member(fr, (side * 0.805, yc, (SILL_TOP + 0.405) / 2), (0.115, 0.075, (0.405 - SILL_TOP) / 2),
                    np.eye(3), rng, ch=0.015, ns=5, nc=4, ds=0.02, hidden=(3,))
        # return tie beam from the door post to the wall post (top under the roof, inner face hidden)
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL, 0)
        p0 = np.array([x, yc + 0.05, HEAD_Z + 0.11])
        p1 = np.array([wp[0], wp[1], HEAD_Z + 0.11])
        L = float(np.linalg.norm(p1 - p0))
        R = frame_R(p1 - p0, (0, 0, 1))
        mid = (p0 + p1) / 2
        inner_side = 3 if float(np.dot(R[:, 1], -mid)) > 0 else 1
        hewn_member(fr, mid, (L / 2 + 0.1, 0.08, 0.10), R, rng, ch=0.02, wane=(0,), end_checks=1,
                    sag=0.004, ns=3, nc=3, ds=0.04, adze=False, hidden=(0, inner_side))
        for (px, pz, fy) in ((x - side * 0.03, HEAD_Z + 0.06, FRONT_Y - 0.009), (x + side * 0.045, HEAD_Z + 0.15, FRONT_Y - 0.009),
                             (xj, HEAD_Z + 0.07, FRONT_Y - 0.009), (xj - side * 0.03, SILL_TOP + 0.05, FRONT_Y + 0.004)):
            peg(np.array([px, fy, pz]), (0, -1, 0), rng)
        pe = p1 - R[:, 0] * 0.12
        peg(pe + R[:, 1] * (0.08 if inner_side == 1 else -0.08) * 1.0, R[:, 1] * (1 if inner_side == 1 else -1), rng)
    # lintel on the door posts (front face proud), slight sag; top + back hidden
    hewn_member(fr, (0.0, yc - 0.008, HEAD_Z + 0.11), (1.15, 0.115, 0.11), np.eye(3), rng, ch=0.022,
                wane=(1,), n_checks=2, check_faces=(1,), end_checks=2, sag=0.008, ns=9, nc=6, ds=0.016,
                hero=(1, 2), hidden=(0, 3))
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
    # threshold stone (front lip visible between the sill and the step stone)
    V, F = shell_stone(0.98, 0.10, rng, "pad", 0.12, rr=(0.012, 0.03), dome=0.003, tilt=0.01, n_frac=2,
                       frac_depth=(0.01, 0.03), n_th=56, noise=0.004, freq=4.0, side_bulge=0.01, flat_face=0.0,
                       face_fr=(0.0, 0.5, 0.85))
    V[:, 2] += 0.088
    add_shell(thr, V, F, "plan", rotz(0.012), (0.0, FRONT_Y - 0.03, 0.0), "M_stone")

    # worn timber sill: hewn, with a 2.2 cm trodden dip over the middle 0.6 m, a worn outer arris
    # and end checks; underside (on the stone) and inner face hidden
    sh = (SILL_TOP - 0.09) / 2

    def sill_wear(V):
        x = V[:, 0]
        dip = np.exp(-np.abs(x / 0.36) ** 3.2)
        top = smoothstep(-0.2 * sh, sh, V[:, 2])
        V[:, 2] -= 0.022 * dip * top * (0.75 + 0.25 * smoothstep(0.13, -0.13, V[:, 1]))
        front = smoothstep(-0.13 + 0.06, -0.13, V[:, 1]) * smoothstep(sh - 0.05, sh, V[:, 2] + 0.022 * dip)
        V[:, 2] -= 0.012 * (0.4 + 0.6 * dip) * front
        V[:, 1] += 0.008 * (0.4 + 0.6 * dip) * front
        return V
    hewn_member(thr, (0.0, yc, (SILL_TOP + 0.09) / 2), (0.92, 0.13, sh), np.eye(3), rng, ch=0.015,
                end_checks=2, n_checks=1, check_faces=(0,), ns=8, nc=5, hero=(0, 1), hidden=(2, 3),
                deform=sill_wear, mat="M_timber")

    # ---------------- door leaf: 6 boards (16-30 cm) + 2 ledges + brace, open 75 deg inward
    LY = 0.024
    pivot = np.array([0.555, -3.50 - 0.0065 + 0.0015, 0.0])
    Rl = rotz(math.radians(-75.0))
    parts = []
    for _ in range(200):
        widths = rng.uniform(0.155, 0.30, 6)
        widths = widths / widths.sum() * (1.06 - 5 * 0.009)
        if widths.min() >= 0.155 and widths.max() <= 0.30:
            break
    x = 0.02
    h0, h1 = SILL_TOP + 0.012, HEAD_Z + 0.035
    cup_b = set(rng.choice(6, 2, replace=False).tolist())
    edge_fns = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(6)]
    for b in range(6):
        bw = widths[b]
        cx = -(x + bw / 2)
        V, F = rbox((bw / 2, 0.0175, (h1 - h0) / 2), 0.006, (3, 1, 10))
        zl = V[:, 2] / ((h1 - h0) / 2)
        # gaps 0.5-1.5 cm varying along the length: each edge wanders +-3 mm
        ea, eb = edge_fns[b]
        right = V[:, 0] > 0
        wl = 0.003 * n2(zl * 1.6, np.full(len(V), ea), 1500 + b)
        wr = 0.003 * n2(zl * 1.6, np.full(len(V), eb), 1600 + b)
        V[:, 0] += np.where(right, wr, wl) * np.clip(np.abs(V[:, 0]) / (bw / 2), 0, 1)
        # uneven board ends +-1 cm
        top_off = rng.uniform(-0.01, 0.01) + V[:, 0] * rng.uniform(-0.03, 0.03)
        bot_off = rng.uniform(-0.008, 0.004)
        V[:, 2] += np.where(zl > 0, top_off * (zl > 0.9), bot_off * (zl < -0.9))
        if b in cup_b:                      # cupped board: edges lift 3-5 mm on the outer face
            V[:, 1] -= rng.uniform(0.003, 0.005) * (2 * V[:, 0] / bw) ** 2
        V[:, 1] += 0.002 * np.sin(V[:, 2] * 1.7 + b * 2) * (V[:, 0] / bw)
        V = V + [cx, LY, (h0 + h1) / 2]
        parts.append((V, F, "M_timber"))
        x += bw + 0.009
    W = x - 0.009 - 0.02
    clench = []
    for zl_ in (h0 + 0.32, h1 - 0.34):
        V, F = rbox((W / 2 - 0.04, 0.016, 0.075), 0.01, (4, 1, 1))
        parts.append((V + [-0.02 - W / 2, LY + 0.0175 + 0.016, zl_], F, "M_timber"))
        for xn in np.linspace(-0.1, -W + 0.06, 6):
            clench.append(np.array([xn, LY + 0.0175 + 0.032 + 0.003, zl_ + 0.03]))
    za_, zb_ = h0 + 0.32 + 0.06, h1 - 0.34 - 0.06
    p0 = np.array([-0.1, 0.0, za_])
    p1 = np.array([-W + 0.06, 0.0, zb_])
    L = float(np.linalg.norm(p1 - p0))
    Rb = frame_R(p1 - p0, (0, 1, 0))
    V, F = rbox((L / 2 - 0.02, 0.065, 0.016), 0.01, (4, 1, 1))
    V = xf(V, Rb, (p0 + p1) / 2 + [0, LY + 0.0175 + 0.016, 0])
    parts.append((V, F, "M_timber"))
    V, F = rbox((0.24, 0.016, 0.022), 0.006, (3, 1, 1))
    parts.append((V + [-W + 0.10, LY + 0.0175 + 0.05, 1.12], F, "M_timber"))
    V, F = rbox((0.03, 0.014, 0.04), 0.005)
    parts.append((V + [-W + 0.28, LY + 0.0175 + 0.014, 1.12], F, "M_timber"))
    for V, F, m in parts:
        leaf.add(xf(V, Rl, pivot), F, m)
    for c_ in clench:
        place_instance(pool_mesh("clench_nail", rng.randint(3), make_clench), "door_clench_nail", Rl,
                       pivot + Rl @ c_)
    face_y = LY - 0.0175                 # outer face

    def make_strap(acc_, k):
        Ls = 0.80
        outline = [(0.0, -0.026), (-Ls + 0.10, -0.023), (-Ls + 0.055, -0.038), (-Ls, 0.0),
                   (-Ls + 0.055, 0.038), (-Ls + 0.10, 0.023), (0.0, 0.026)]
        V, faces = prism(outline[::-1], 0.007)
        V = np.stack([V[:, 0], -V[:, 2], V[:, 1]], -1)
        acc_.add(V, faces, "M_iron", smooth=False)

    def make_knuckle(acc_, k):
        Pk, Fk, uvk, wk = tube(np.linspace([0, 0, -0.03], [0, 0, 0.03], 3), 0.014, 12, up=(1, 0, 0))
        acc_.add(Pk, Fk, "M_iron", uvk, wk)

    def make_pintle(acc_, k):
        Pp, Fp, uvp, wpp = tube(np.linspace([0, 0, -0.05], [0, 0, 0.045], 3), 0.0075, 8, up=(1, 0, 0))
        acc_.add(Pp, Fp, "M_iron", uvp, wpp)
        V, F = rbox((0.009, 0.035, 0.009), 0.002)
        acc_.add(V + [0.0, -0.03, -0.05], F, "M_iron")

    for zh in (h0 + 0.30, h1 - 0.30):
        place_instance(pool_mesh("hinge_strap", 0, make_strap), "door_hinge_strap", Rl, pivot + Rl @ np.array([0, face_y, zh]))
        place_instance(pool_mesh("hinge_knuckle", 0, make_knuckle), "door_hinge_knuckle", Rl, pivot + Rl @ np.array([0, 0, zh]))
        place_instance(pool_mesh("hinge_pintle", 0, make_pintle), "door_hinge_pintle", None, pivot + np.array([0, 0, zh]))
        for xn in (-0.07, -0.22, -0.38, -0.54, -0.68):
            Rn = Rl @ np.array([[1.0, 0, 0], [0, -1, 0], [0, 0, -1]])      # head points out of the face (-y)
            place_instance(pool_mesh("nail_head", rng.randint(3), make_nail_head), "door_nail",
                           Rn @ rotz(0), pivot + Rl @ np.array([xn, face_y - 0.007, zh]))
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
    """earthen floor (tucked under the sill: no seam inside the doorway), hearth ring."""
    acc = Acc("HUT_floor", 40)
    rng = np.random.RandomState(1313)
    nr, nt = 18, 96
    T1 = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    dth = np.angle(np.exp(1j * (T1 + np.pi / 2)))
    r_out = R_WALL + 0.02 + 0.20 * np.exp(-(dth / 0.22) ** 2)
    f_ = np.linspace(0.0, 1.0, nr)
    R_ = 0.03 + f_[:, None] * (r_out[None, :] - 0.03)
    T_ = np.broadcast_to(T1[None, :], R_.shape)
    X = R_ * np.cos(T_)
    Y = R_ * np.sin(T_)
    Z = floor_z(X, Y)
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
    plan_path()
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
    build_roof_blocker(coll)
    log("shingles")
    zz = build_collar_finial(coll)
    log("collar drip %.3f fascia top %.3f lower top %.3f upper top %.3f spindle top %.3f tip %.3f" % zz)
    build_plinth(coll)
    build_rubble(coll)
    build_apron(coll)
    build_path(coll)
    log("ground")
    build_door(coll)
    build_interior(coll)
    log("door + interior")
    tris = 0
    obs = list(coll.all_objects)
    for ob in obs:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    log(f"objects {len(obs)} (instances {N_INST[0]}, pooled meshes {len(POOLS)}) triangles {tris}")
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log("saved", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
