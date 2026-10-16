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
    nseg = 50
    t = np.linspace(0, 1, nseg)
    lean = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]) * math.tan(math.radians(0.7))
    H = top[2] - base[2]
    bow = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]) * 0.012
    path = base[None, :] + np.outer(t, top - base) + np.outer(t * H, lean) + np.outer(np.sin(np.pi * t), bow)
    taper = rad * (1 + 0.05 * (0.5 - t)) + rng.uniform(-0.005, 0.005)
    ph0 = rng.uniform(0, 1)
    ang = 2 * np.pi * np.arange(sides) / sides + ph0
    seed = rng.randint(1000)
    A2 = np.broadcast_to(ang, (nseg, sides)).copy()
    T2 = np.broadcast_to(t[:, None], (nseg, sides))
    rr = 1 + 0.02 * n2(A2 * 1.3, T2 * 4, seed) + 0.002 * n2(A2 * 2, T2 * 30, seed + 1)
    # adze flats: planar cuts 5-8 mm deep over a stretch of the post, feathered at their ends
    nfl = rng.randint(6, 11)
    for kf in range(nfl):
        af = ph0 + 2 * np.pi * (kf + rng.uniform(-0.3, 0.3)) / nfl
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
        ka = ph0 + rng.uniform(0, 2 * np.pi)
        kt = rng.uniform(0.25, 0.8)
        da = np.angle(np.exp(1j * (A2 - ka))) * rad
        dz = (T2 - kt) * H
        dist = np.hypot(da, dz * 0.8)
        rr = rr + (0.012 * np.exp(-(dist / 0.04) ** 2)) / rad
        stubs.append((ka, kt))
    if check:  # drying check: a narrow, deep V split down one face
        k = rng.randint(sides)
        z0, z1 = rng.uniform(0.15, 0.35), rng.uniform(0.55, 0.8)
        m = smoothstep(z0, z0 + 0.08, t) * (1 - smoothstep(z1 - 0.08, z1, t))
        rr[:, k] *= (1 - 0.13 * m)
        dA = 2 * np.pi / sides
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
                end_checks=0, sag=0.0, adze=True, mat="M_timber", ds=0.012, ns=7, nc=6, swell=0.008):
    """hand-hewn squared timber along local +X (half = (L/2, a, b)); R columns = local axes in world.
    adze facets 4-8 cm wide x 3-6 mm deep on every face, +-8 mm swell along the length, rounded
    arrises, wane (bark-edge rounding) on chosen corners (0:+y+z 1:-y+z 2:-y-z 3:+y-z), narrow
    drying checks on chosen faces (0:+z 1:-y 2:-z 3:+y), end-grain checks at both ends."""
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
    rc = np.full((n, 4), ch)
    for cw in wane:
        rc[:, cw] = np.clip(0.045 + 0.02 * n2(tt * 4.0, np.full(n, cw * 3.1), seed + 5 + cw), 0.025, 0.065)
    # build the profile rings: corners c0..c3, CCW in (y,z); each side has ns interior points
    M = 4 * (ns + nc)
    Y = np.zeros((n, M))
    Zp = np.zeros((n, M))
    face = np.full(M, -1)
    across = np.zeros(M)
    corner_sign = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for i in range(n):
        a, b = sw_a[i], sw_b[i]
        pts = []
        for c in range(4):
            sy, sz = corner_sign[c]
            r = min(rc[i, c], a * 0.6, b * 0.6)
            cy, cz = sy * (a - r), sz * (b - r)
            a_start = math.atan2(0, sy) if c in (0, 2) else math.atan2(sz, 0)
            # corner arcs CCW: c0 from +y dir (0) to +z (90); c1 from +z(90) to -y(180); etc.
            a_beg = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi][c]
            arc = a_beg + np.linspace(0, 0.5 * np.pi, nc)
            for k_ in range(nc):
                pts.append((cy + r * math.cos(arc[k_]), cz + r * math.sin(arc[k_])))
            # side after corner c -> corner c+1
            cn = (c + 1) % 4
            sy2, sz2 = corner_sign[cn]
            r2 = min(rc[i, cn], a * 0.6, b * 0.6)
            p_from = np.array([cy + r * math.cos(arc[-1]), cz + r * math.sin(arc[-1])])
            p_to_c = np.array([sy2 * (a - r2), sz2 * (b - r2)])
            a_beg2 = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi][cn]
            p_to = p_to_c + r2 * np.array([math.cos(a_beg2), math.sin(a_beg2)])
            for k_ in range(ns):
                u = (k_ + 1) / (ns + 1)
                pts.append(tuple(p_from + (p_to - p_from) * u))
        pts = np.array(pts)
        Y[i] = pts[:, 0]
        Zp[i] = pts[:, 1]
    for c in range(4):
        for k_ in range(ns):
            j = c * (ns + nc) + nc + k_
            face[j] = c
            across[j] = (k_ + 1) / (ns + 1) * 2 - 1
    # face outward normals in (y,z): side after c0 is the +z face, etc.
    fn = {0: (0, 1), 1: (-1, 0), 2: (0, -1), 3: (1, 0)}
    disp = np.zeros((n, M))
    if adze:
        # adze strokes: each face is worked in 2-3 overlapping lanes; every stroke leaves a shallow
        # scoop 4-8 cm long, 2-6 mm deep, skewed across the lane, ending in a small ridge
        for c in range(4):
            js = np.where(face == c)[0]
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
                    bnd.append(bnd[-1] + rng.uniform(0.04, 0.08))
                bnd = np.array(bnd)
                dep = rng.uniform(0.003, 0.0065, len(bnd)) * (rng.rand(len(bnd)) > 0.1)
                skew = rng.uniform(-0.03, 0.03, len(bnd))
                xe = xs[:, None] + skew[np.clip(np.searchsorted(bnd, xs) - 1, 0, len(bnd) - 2)][:, None] * across[jl][None, :]
                k = np.clip(np.searchsorted(bnd, xe.ravel()) - 1, 0, len(bnd) - 2).reshape(xe.shape)
                tl = np.clip((xe - bnd[k]) / (bnd[k + 1] - bnd[k]), 0, 1)
                sc = dep[k] * (1 - (2 * tl - 1) ** 2) ** 0.5 * (0.6 + 0.4 * (1 - tl))
                disp[:, jl] += sc
                lane_scoop_mid += sc.mean(1) / nlane
            # corner points get part of the adjacent face scoop
            for jc in range(c * (ns + nc), c * (ns + nc) + nc):
                disp[:, jc] += 0.35 * lane_scoop_mid
    # apply face displacement (inward along the face normal)
    for c in range(4):
        js = np.where(face == c)[0]
        ny, nz = fn[c]
        Y[:, js] -= ny * disp[:, js]
        Zp[:, js] -= nz * disp[:, js]
    cj = np.where(face < 0)[0]
    rad_ = np.hypot(Y[:, cj], Zp[:, cj])
    Y[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)
    Zp[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)
    # drying checks (narrow V split: centre line sinks, neighbours pulled in)

    def apply_check(c, j_off, i0, i1, depth, width, from_end=0):
        j = c * (ns + nc) + nc + j_off
        ny, nz = fn[c]
        ii = np.arange(i0, i1)
        tl = (ii - i0) / max(1, (i1 - i0 - 1))
        if from_end < 0:
            m = (1 - tl) ** 0.7
        elif from_end > 0:
            m = tl ** 0.7
        else:
            m = smoothstep(0.0, 0.18, tl) * (1 - smoothstep(0.82, 1.0, tl))
        tyz = np.array([-nz, ny], float)       # across-face direction (toward increasing j)
        hw = width / 2 * (0.35 + 0.65 * np.sqrt(np.clip(m, 0, 1)))
        for jn, sg in ((j - 1, 1), (j + 1, -1)):
            # pull the neighbour line in to the crack lip using the REAL spacing on this ring
            dist = np.abs((Y[ii, jn] - Y[ii, j]) * tyz[0] + (Zp[ii, jn] - Zp[ii, j]) * tyz[1])
            pull = np.clip(dist - hw, 0, None) * smoothstep(0.0, 0.35, m)
            Y[ii, jn] += sg * tyz[0] * pull
            Zp[ii, jn] += sg * tyz[1] * pull
        Y[ii, j] -= ny * depth * m
        Zp[ii, j] -= nz * depth * m

    for _ in range(n_checks):
        c = int(rng.choice(check_faces))
        j_off = rng.randint(2, ns - 2)
        lc = rng.uniform(0.15, 0.4)
        x0 = rng.uniform(-hl + 0.15, hl - 0.15 - lc)
        i0 = int(np.searchsorted(xs, x0))
        i1 = int(np.searchsorted(xs, x0 + lc))
        apply_check(c, j_off, i0, i1, rng.uniform(0.012, 0.02), rng.uniform(0.004, 0.006))
    for _ in range(end_checks):
        for side_ in (-1, 1):
            c = rng.randint(4)
            j_off = rng.randint(1, ns - 1)
            lc = rng.uniform(0.06, 0.16)
            if side_ < 0:
                i0, i1 = 0, int(np.searchsorted(xs, -hl + lc))
            else:
                i0, i1 = int(np.searchsorted(xs, hl - lc)), n
            apply_check(c, j_off, i0, i1, rng.uniform(0.012, 0.022), rng.uniform(0.003, 0.006), from_end=side_)
    # end chamfer rings
    for i_e, f_e in ((0, 1), (n - 1, 1)):
        Y[i_e] *= 1 - che / max(a0, 1e-3)
        Zp[i_e] *= 1 - che / max(b0, 1e-3)
    X = np.broadcast_to(xs[:, None], (n, M)).copy()
    if sag:
        X_t = xs / hl
        Zp += (-sag * (1 - X_t ** 2))[:, None]
    # end faces: inner ring + centre; end checks also notch into the end face
    V = np.stack([X, Y, Zp], -1).reshape(-1, 3)
    inner0 = np.stack([X[0] + 0.002, Y[0] * 0.55, Zp[0] * 0.55], -1)
    inner1 = np.stack([X[-1] - 0.002, Y[-1] * 0.55, Zp[-1] * 0.55], -1)
    cen = np.array([[xs[0] + 0.003, 0, Zp[0].mean()], [xs[-1] - 0.003, 0, Zp[-1].mean()]])
    V = np.concatenate([V, inner0, inner1, cen])
    j = np.arange(M)
    j1 = (j + 1) % M
    i = np.arange(n - 1)[:, None]
    Fs = np.stack([i * M + j, i * M + j1, (i + 1) * M + j1, (i + 1) * M + j], -1).reshape(-1, 4)
    o_in0 = n * M
    o_in1 = n * M + M
    c0i = n * M + 2 * M
    c1i = c0i + 1
    last = (n - 1) * M
    cap0 = np.stack([o_in0 + j, o_in0 + j1, j1, j], -1)                       # faces -X
    cap1 = np.stack([last + j, last + j1, o_in1 + j1, o_in1 + j], -1)         # faces +X
    fan0 = np.stack([np.full(M, c0i), o_in0 + j1, o_in0 + j], -1)
    fan1 = np.stack([np.full(M, c1i), o_in1 + j, o_in1 + j1], -1)
    Vw = xf(V, R, center)
    acc.add(Vw, [Fs, cap0, cap1, fan0, fan1], mat)


def build_posts(coll):
    acc = Acc("HUT_posts", 15)          # low angle: adze-flat edges crisp, 48-gon stays smooth
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


ROD_SIDES = 6


def rod_profile(n_rings, seed, oval):
    """slightly oval, knobbly rod section, varying ring to ring (6 sides)."""
    ang = 2 * np.pi * np.arange(ROD_SIDES) / ROD_SIDES
    rs = np.random.RandomState(seed)
    ph = rs.uniform(0, 6.3)
    kn = 0.07 * n2(np.arange(n_rings)[:, None] * 0.35 + ang[None, :] * 0.0, np.broadcast_to(ang, (n_rings, ROD_SIDES)) * 1.7, seed)
    rr = 1.0 + kn
    x = np.cos(ang + ph) * rr
    y = np.sin(ang + ph) * rr * oval
    return np.stack([x, y], -1)


def weave_panel(rods, stakes_acc, pathf, s0, s1, z0, z1, seed, hide=None, n_stakes=None,
                end_stakes=True, stake_bottom=None, amp_scale=1.0, slant=0.0, pitch=(0.058, 0.078),
                rod_r=(0.0135, 0.018)):
    """woven panel between s0 and s1 (ends are hidden in posts/jambs).
    Coarse open weave: rows every 6-8 cm (+-1.5), rods dia 2.4-3.6 cm, so 2-4 cm dark gaps read
    between rows. Each rod has its own low-frequency drift, knots (+15% dia bumps every 0.3-0.6 m),
    taper and an oval knobbly section; ~15% of rows are paired or tripled."""
    rng = np.random.RandomState(seed)
    L = s1 - s0
    if n_stakes is None:
        n_stakes = max(1, int(round(L / 0.29)) - 1)
    st = np.linspace(s0, s1, n_stakes + 2)
    st[1:-1] += rng.uniform(-0.025, 0.025, n_stakes) * min(1.0, L / 0.6)
    real_st = st[1:-1]
    # stakes (sails)
    zb = z0 - 0.07 if stake_bottom is None else stake_bottom
    for k, ss in enumerate(real_st):
        r = rng.uniform(0.02, 0.027)
        if hide is not None and hide(np.full(5, ss), np.linspace(z0, z1, 5), 0.0).all():
            continue
        nz = 16
        zz = np.linspace(zb, z1 + 0.03, nz)
        pt, nn = pathf(np.full(nz, ss))
        wob = 0.01 * n2(zz * 1.5, np.full(nz, ss * 3.0), seed + k)
        tang = np.stack([nn[:, 1], -nn[:, 0]], -1)
        xy = pt + tang * wob[:, None] + nn * (0.007 * n2(zz * 2.0, np.full(nz, ss), seed + 50 + k))[:, None]
        path = np.c_[xy, zz]
        rad = r * (1 + 0.08 * n2(zz * 3.0, np.full(nz, ss), seed + 70 + k)) * np.linspace(1.08, 0.92, nz)
        path, rr = chamfer_path(path, rad, 0.006)
        P, F, uv, w = tube(path, rr, 8, up=(nn[0, 0], nn[0, 1], 0))
        stakes_acc.add(P, F, "M_wattle", uv, w)
    # rods
    z = z0 + rng.uniform(0.012, 0.03)
    row = 0
    tilt = rng.uniform(-0.01, 0.01) + slant
    steep = abs(slant) > 0.1
    if steep:          # rows start below the panel so the rising rods fill the bottom corner
        z = z0 - max(0.0, tilt) * L + rng.uniform(0.0, 0.02)
    z_stop = z1 - 0.02 - (min(0.0, tilt) * L if steep else 0.0)
    n_rods = 0
    while z < z_stop:
        u = rng.rand()
        nsub = 3 if u < 0.045 else (2 if u < 0.155 else 1)
        r_row = rng.uniform(*rod_r)
        split = rng.rand() < 0.22
        A = rng.uniform(0.025, 0.03) * amp_scale
        signs = np.array([(-1) ** (k + row) for k in range(len(st))], float)
        pieces = []
        if split and L > 0.6:
            ks = rng.randint(1, len(st) - 1) if len(st) > 2 else 1
            sm = st[ks]
            pieces.append((s0 - 0.01, min(s1, sm + 0.33), -0.006, 1))
            pieces.append((max(s0, sm - 0.33), s1 + 0.01, 0.006, -1))
        else:
            pieces.append((s0 - 0.01, s1 + 0.01, 0.0, 0))
        if nsub == 1:
            subs = [(r_row, 0.0)]
        elif nsub == 2:
            rA, rB = r_row * rng.uniform(0.72, 0.85), r_row * rng.uniform(0.68, 0.82)
            subs = [(rA, -rB * 0.95), (rB, rA * 0.95)]
        else:
            rr_ = r_row * rng.uniform(0.6, 0.72, 3)
            subs = [(rr_[0], -(rr_[0] + rr_[1]) * 0.95), (rr_[1], 0.0), (rr_[2], (rr_[1] + rr_[2]) * 0.95)]
        bundle_h = sum(2 * x for x, _ in subs)
        for (a, b, dz, tipside) in pieces:
            for si, (rr0, dzz) in enumerate(subs):
                rseed = seed * 131 + row * 7 + si * 3 + int(a * 10)
                # knots: +15% diameter bumps every 0.3-0.6 m, resolved with extra rings
                kpos = []
                kp = a + rng.uniform(0.05, 0.4)
                while kp < b - 0.03:
                    kpos.append(kp)
                    kp += rng.uniform(0.3, 0.6)
                base = np.linspace(a, b, max(4, int((b - a) / 0.03) + 1))
                extra = [kp_ + d for kp_ in kpos for d in (-0.02, -0.009, 0.0, 0.009, 0.02)]
                ss = np.unique(np.concatenate([base, np.clip(extra, a, b)]))
                n = len(ss)
                # per-rod low-frequency drift (+-3 cm per metre) + slight shared tilt
                drift = (0.016 * n2(ss * 1.1, np.full(n, rseed * 0.37), 7000 + seed % 97)
                         + 0.004 * n2(ss * 4.0, np.full(n, rseed * 0.71), 7100 + seed % 89))
                for kp_ in kpos:          # kinks: sharp little bends where a side shoot was
                    if rng.rand() < 0.55:
                        drift = drift + rng.uniform(-1, 1) * 0.009 * np.clip(1 - np.abs(ss - kp_) / 0.07, 0, 1) ** 1.5
                zz = z + dz + dzz + drift + tilt * (ss - s0)
                if steep:      # trim to the panel (ends die into the sole rail / lintel)
                    ok = (zz > z0 - 0.012) & (zz < z1 + 0.012)
                    if ok.sum() < 3:
                        continue
                    idx = np.where(ok)[0]
                    sl = slice(idx[0], idx[-1] + 1)
                    ss, zz, drift = ss[sl], zz[sl], drift[sl]
                    n = len(ss)
                if hide is not None and hide(ss, zz, 0.012).all():
                    continue
                off = weave_offset(ss, st, signs, A)
                if tipside != 0:
                    tip = b if tipside > 0 else a
                    tt = 1 - np.clip(np.abs(ss - tip) / 0.1, 0, 1)
                    off = off + 0.035 * tt ** 2 * (1 if rng.rand() < 0.7 else -1)
                pt, nn = pathf(ss)
                xy = pt + nn * off[:, None]
                path = np.c_[xy, zz]
                taper = np.linspace(1.0, 0.7, n) if rng.rand() < 0.5 else np.linspace(0.7, 1.0, n)
                knot = np.zeros(n)
                for kp_ in kpos:
                    knot += 0.15 * np.exp(-((ss - kp_) / 0.011) ** 2)
                rr = rr0 * taper * (1 + knot + 0.05 * n2(ss * 5, np.full(n, z), seed + 7))
                prof = rod_profile(n, rseed, rng.uniform(0.78, 0.9))
                P, F, uv, w = tube(path, rr, ROD_SIDES, up=(0, 0, 1), profile=prof)
                rods.add(P, F, "M_wattle", uv, w)
                n_rods += 1
        z += rng.uniform(*pitch) + max(0.0, bundle_h - 2 * r_row) + rng.uniform(-0.004, 0.004)
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

    def side_field(s, z):
        # remnant of an old daub coat on the lower part of the bay, against its left post
        zt = 1.30 + 0.16 * n2(s * 2.6, 0.5, 921) + 0.05 * n2(s * 9.0, 1.5, 922) + 0.02 * n2(s * 23, 2.5, 923)
        sr = s0 + 0.62 * (s1 - s0) + 0.14 * n2(z * 2.4, 3.5, 924) + 0.04 * n2(z * 10, 4.5, 925)
        zb = 0.47 + 0.05 * n2(s * 5, 6.5, 926)
        f = np.minimum(np.minimum(zt - z, sr - s), z - zb)
        isl = np.clip(n2(s * 8.0, z * 8.0, 927) * 1.6 - 0.4, 0, 1) * 0.08
        f = np.where(f < 0, np.maximum(f, f + isl * (1 - smoothstep(0.0, 0.2, -f)) * 1.5), f)
        return f

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
        weave_panel(rods, stakes, f, -0.06, (x1 - x0) + 0.06, 0.40, HEAD_Z, 3000 + side, n_stakes=2,
                    stake_bottom=0.33, amp_scale=0.55, slant=0.85 * side, pitch=(0.042, 0.05),
                    rod_r=(0.011, 0.014))
        # cheek panels: door post back corner -> wall post
        pa = np.array([side * 1.02, FRONT_Y + 0.17])
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL)[:2]
        L = float(np.linalg.norm(wp - pa))
        d = (wp - pa) / L
        nout = np.array([d[1], -d[0]]) * (1 if side > 0 else -1)
        if nout[0] * side < 0:
            nout = -nout
        f2 = line_path(pa, wp, nout)
        weave_panel(rods, stakes, f2, -0.05, L + 0.02, 0.40, HEAD_Z, 3100 + side, n_stakes=2,
                    stake_bottom=0.33, amp_scale=0.6, slant=-0.6 * side, pitch=(0.045, 0.055),
                    rod_r=(0.011, 0.015))
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
        zlo, zhi = 0.42, WATTLE_TOP + 0.02
        # crop to where the daub exists
        Sc, Zc = np.meshgrid(np.linspace(s0, s1, 120), np.linspace(zlo, zhi, 160), indexing="ij")
        fc = field(Sc, Zc)
        live = fc > -0.07
        ss_live = Sc[live]
        zz_live = Zc[live]
        cs0, cs1 = max(s0, ss_live.min() - 0.03), min(s1, ss_live.max() + 0.03)
        cz0, cz1 = max(zlo, zz_live.min() - 0.03), min(zhi, zz_live.max() + 0.03)
        nu = int((cs1 - cs0) / h) + 1
        nv = int((cz1 - cz0) / h) + 1
        S, Z = np.meshgrid(np.linspace(cs0, cs1, nu), np.linspace(cz0, cz1, nv), indexing="ij")
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
        drift = 0.02 * n2(S * 1.1, np.full(S.shape, 3.3), 4500 + bay)
        rid = np.cos(2 * np.pi * (Z + drift) / 0.07 + 0.5 * n2(S * 3, Z, 4510 + bay))
        thin = 1 - smoothstep(-0.9, 0.4, bul)
        patchy = np.clip(n2(S * 2.5, Z * 2.5, 4511 + bay) * 2.0 + 0.2, 0, 1)
        ridge = 0.0065 * rid * thin ** 2 * patchy
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


INNER_SKIN_D = 0.08            # inner daub skin face, behind the wattle centre line


def build_inner_skin(coll):
    """inner daub skin: behind the daubed bays (hides the back of the daub coat) and round the back
    arc seen through the doorway (keeps the interior dark). The open front/side bays have no inner
    skin, so their weave shows dark gaps as in ref2."""
    acc = Acc("HUT_daub_interior", 70)
    arcs = [(WALL_POST_AZ_DOOR, 2 * math.pi - WALL_POST_AZ_DOOR)]
    for k, (a0, a1) in enumerate(arcs):
        nu = max(8, int((a1 - a0) * R_WALL / 0.08))
        nv = 30
        A, Z = np.meshgrid(np.linspace(a0, a1, nu), np.linspace(0.17, PLATE_BOT + 0.02, nv), indexing="ij")
        lump = 0.012 * fbm(np.stack([A * 4, Z * 2.5, np.full(A.shape, k * 1.7)], -1), 3)
        ro = R_WALL - INNER_SKIN_D - 0.002 * k + 0.6 * lump
        ri = R_WALL - INNER_SKIN_D - 0.05 + lump
        P = np.stack([np.sin(A) * ri, -np.cos(A) * ri, Z], -1)
        Q = np.stack([np.sin(A) * ro, -np.cos(A) * ro, Z], -1)
        V, F = slab(Q, P)
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
SH_XS = np.array([-1.0, -CH_C, -0.55, -0.18, 0.18, 0.55, CH_C, 1.0])
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
    # ragged hand-split butt: per-column offsets (2-3 notches, skew, +-1.5 cm)
    col = np.clip(np.searchsorted(SH_XS, Vt[:, 0] - 1e-6), 0, len(SH_XS) - 1)
    butt = Vt[:, 1] <= -CH_C + 1e-6
    y = y + np.where(butt, np.asarray(rng_vals)[col], 0.0)
    # cup (edges lift) and curl (butt lifts)
    z = z + cup * (2 * x / W) ** 2 + curl * (1 - v) ** 2
    return np.stack([x, y, z], -1), F


def build_shingles(coll):
    acc = Acc("HUT_roof_shingles", 45)
    st_acc = Acc("HUT_roof_starter", 45)
    rng = np.random.RandomState(606)
    B_WEDGE = 0.066
    prev_joints = None
    n_total = 0

    def place(acc_, th_c, s_b, W, L, Tb, Th, phi, lift, cup, curl, base_fn, rc):
        offs = rng.uniform(-0.012, 0.012, 8)
        offs[[0, 1, 6, 7]] *= 0.4
        for c_ in rng.choice([2, 3, 4, 5], rng.randint(2, 4), replace=False):
            offs[c_] += rng.uniform(0.012, 0.022)
        offs += np.linspace(-1, 1, 8) * rng.uniform(-0.012, 0.012)
        Pl, F = shingle_local(W, L, Tb, Th, rc, cup, curl, offs)
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
        place(st_acc, thc, s_b, w[i], 0.46, 0.034, 0.012, math.radians(rng.uniform(-1.5, 1.5)), 0.0,
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
        base_fn = (lambda v: 0.037 * (1 - v)) if k == 0 else (lambda v: B_WEDGE * (1 - v))
        for i in range(n):
            dth = (w[i] + gaps[i]) / rb
            thc = acc_ang + dth / 2
            acc_ang += dth
            ri = rng.rand()
            if k > 0 and k < N_COURSES - 1 and ri < 0.012:
                continue                                    # missing shingle
            sb = s_b + cwave[int((thc % (2 * np.pi)) / (2 * np.pi) * 512) % 512] + rng.uniform(-0.012, 0.012)
            lift = rng.uniform(0.0, 0.015)
            phi = math.radians(rng.uniform(-4.5, 4.5))
            Tb = rng.uniform(0.034, 0.042)
            curl = rng.uniform(0.006, 0.016) if k < 2 else rng.uniform(0.0, 0.005)
            cup = rng.uniform(0.002, 0.008)
            rc = rng.uniform(0.03, 0.07)
            Wi = w[i]
            if k > 0 and 0.012 < ri < 0.03:                 # slipped
                sb -= rng.uniform(0.05, 0.11)
                lift += 0.016
                phi += math.radians(rng.uniform(-4, 4))
            dd_door = abs(float(np.angle(np.exp(1j * (thc + np.pi / 2)))))
            door_eave = (k < 4) and dd_door < 1.0 and (0.03 < ri < 0.13)
            if (0.03 < ri < 0.045 or door_eave) and Wi > 0.34:      # split into two pieces
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
    under = [(0.0, zf + 0.70)] + [(r_, zf + 0.012 + (R - r_) * tp * 0.97) for r_ in np.linspace(0.2, R - 0.03, 6)]
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
    for f in np.linspace(0.06, 1.0, 12):
        r_ = 0.075 + (ru - 0.012 - 0.075) * (1 - f) ** 1.9
        prof_u.append((r_, zu1 + (H_u - 0.015) * f))
    z_s = zu1 + H_u - 0.015
    prof_u.append((0.0, z_s + 0.004))
    V, F, uv, w = lathe(prof_u, 64, rfunc=lambda th_, z_: 1 + 0.005 * np.sin(2 * th_ + 0.4))
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_lead", uv, w)
    # ---- turned spindle (timber): seat ring, bead ring 0.20, neck 0.10, vase bulb 0.18, top ring
    sp = [(0.0, z_s - 0.01), (0.07, z_s - 0.01), (0.088, z_s + 0.004), (0.09, z_s + 0.02),          # seat
          (0.1, z_s + 0.034), (0.102, z_s + 0.05), (0.094, z_s + 0.064),                               # bead ring
          (0.064, z_s + 0.078), (0.052, z_s + 0.1), (0.05, z_s + 0.12),                                # neck
          (0.066, z_s + 0.15), (0.086, z_s + 0.185), (0.091, z_s + 0.215), (0.084, z_s + 0.245),       # bulb
          (0.062, z_s + 0.275), (0.054, z_s + 0.3), (0.056, z_s + 0.318),                              # upper neck
          (0.078, z_s + 0.338), (0.088, z_s + 0.356), (0.086, z_s + 0.374), (0.076, z_s + 0.385),      # top ring
          (0.0, z_s + 0.387)]
    V, F, uv, w = lathe(sp, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_timber", uv, w)
    # ---- spike (iron): conical from dia ~0.15 to a sharp point at FINIAL_TIP
    z_k = z_s + 0.385
    tip = max(FINIAL_TIP, z_k + 0.6)
    spk = [(0.0, z_k - 0.004), (0.074, z_k - 0.004), (0.077, z_k + 0.01), (0.074, z_k + 0.022)]
    for f in np.linspace(0.06, 0.985, 18):
        spk.append((0.071 * (1 - f) ** 1.05 + 0.0015, z_k + 0.022 + (tip - z_k - 0.022) * f))
    spk += [(0.0012, tip - 0.003), (0.0, tip)]
    V, F, uv, w = lathe(spk, 40)
    V = (V - piv) @ lean.T + piv
    fin.add(V, F, "M_iron", uv, w)
    acc.build(coll)
    fin.build(coll)
    return zf, zd, z_top, z_s, z_k, tip


# =============================================================================================
# plinth, rubble, apron
# =============================================================================================
R_PL_FACE = 3.76            # plinth outer face line (rough wall line, +-4 cm)


def plinth_face_r(az):
    return R_PL_FACE + 0.018 * ring_noise(np.asarray(az, float), 9091, 6, 1.0)


def build_plinth(coll):
    """dry-stone plinth: sub-angular split boulders in contact along a rough face line.
    ~45% single tall stones, ~40% two-high (flat lower stone + flatter upper slab), a few low
    stones carrying pinning slabs, 2-3 long through-stones. Wedge chinking recessed in joints."""
    acc = Acc("HUT_plinth_stones", 70)
    chink = Acc("HUT_plinth_chinking", 70)
    rng = np.random.RandomState(9090)
    r_c = 3.53
    a_start = math.asin(1.30 / 3.78)
    a_end = 2 * math.pi - a_start
    a = a_start
    stones = []
    through_at = set(rng.choice(np.arange(6, 34), 3, replace=False).tolist())
    k = 0
    while a < a_end - 0.02:
        kind = rng.choice(["single", "double", "low"], p=[0.45, 0.40, 0.15])
        if k in through_at:
            kind = "through"
            L = rng.uniform(0.76, 0.86)
        elif kind == "double":
            L = rng.uniform(0.45, 0.85)
        else:
            L = rng.choice([rng.uniform(0.25, 0.42), rng.uniform(0.38, 0.65)], p=[0.35, 0.65])
        if a + L / r_c > a_end:
            L = (a_end - a) * r_c
            if L < 0.2:
                break
            if kind == "through":
                kind = "single"
        g = rng.uniform(-0.03, 0.0)              # in contact (rounded corners leave a V joint)
        stones.append([a + (L / 2) / r_c, L, kind])
        a += (L + g) / r_c
        k += 1
    post_az = list(POST_AZ)
    n_up = n_pin = n_ch = 0
    tops = []

    def put(Pl, Fl, az, z_bot, depth, rot_jit=0.04, tilt=(0.02, 0.02), mat="M_stone", tgt=None, face_off=0.0):
        """place a local stone (x along the ring, y radial-in, z up) with its outer face on the line."""
        rf = float(plinth_face_r(az)) - face_off
        R = rotz(az + rng.uniform(-rot_jit, rot_jit)) @ rotx(rng.uniform(-tilt[0], tilt[0])) @ \
            roty(rng.uniform(-tilt[1], tilt[1]))
        Vw = xf(Pl, R, (0, 0, 0))
        # shift so the outermost point of the stone face sits on the face line
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        out_ext = float((Vw @ u).max())
        c = u * (rf - out_ext)
        c[2] = z_bot - float(Vw[:, 2].min())
        (tgt or acc).add(Vw + c, Fl, mat)
        return c

    for i, (ac, L, kind) in enumerate(stones):
        near_post = min(abs(np.angle(np.exp(1j * (ac - pa)))) for pa in post_az) * r_c < L / 2 + 0.05
        top = rng.uniform(0.355, 0.41)
        if near_post:
            top = rng.uniform(0.365, 0.385)
        bot = -rng.uniform(0.05, 0.10)
        D = rng.uniform(0.36, 0.52)
        rr = rng.uniform(0.02, 0.04)
        if kind == "single" or (kind == "low" and near_post):
            H = top - bot
            P, F = rock((L / 2, D / 2, H / 2), rng, round_r=rr, facets=(4, 7), segs=(10, 6, 7),
                        warp=0.04, amp=rng.uniform(0.006, 0.009), freq=3.0, face_bias=(0, -1, 0),
                        bias_p=0.2, face_cuts=rng.randint(2, 4), fillet=0.012, flat_top=H / 2 - rng.uniform(0.01, 0.03), flat_bot=-H / 2 + 0.02,
                        batter=rng.uniform(0.015, 0.05))
            put(P, F, ac, bot, D, tilt=(0.05, 0.05))
            tops.append(top)
        elif kind == "through":
            lo_top = rng.uniform(0.17, 0.24)
            H = lo_top - bot
            Dt = rng.uniform(0.62, 0.72)
            P, F = rock((L / 2, Dt / 2, H / 2), rng, round_r=rr, facets=(3, 5), segs=(12, 7, 5),
                        warp=0.04, amp=0.007, freq=3.0, face_bias=(0, -1, 0), bias_p=0.2, face_cuts=2,
                        fillet=0.012, flat_top=H / 2 - 0.012,
                        flat_bot=-H / 2 + 0.02)
            put(P, F, ac, bot, Dt, face_off=-rng.uniform(0.02, 0.05))   # projects slightly
            # two upper stones on the through-stone
            xs_ = [-L * 0.24, L * 0.26]
            for xo in xs_:
                Lu = L * rng.uniform(0.42, 0.5)
                Hu = top - lo_top + 0.01
                Pu, Fu = rock((Lu / 2, D * 0.45, Hu / 2), rng, round_r=min(rr, Hu * 0.3), facets=(3, 5),
                              segs=(7, 5, 5), warp=0.04, amp=0.007, freq=3.5, face_bias=(0, -1, 0), bias_p=0.2,
                              face_cuts=rng.randint(1, 3), fillet=0.012,
                              flat_top=Hu / 2 - 0.01, flat_bot=-Hu / 2 + 0.012)
                put(Pu, Fu, ac + xo / r_c, lo_top - 0.008, D * 0.9, face_off=rng.uniform(0.01, 0.04))
                n_up += 1
            tops.append(top)
        elif kind == "double":
            lo_top = rng.uniform(0.15, 0.25)
            H = lo_top - bot
            b_lo = rng.uniform(0.0, 0.025)
            P, F = rock((L / 2, D / 2, H / 2), rng, round_r=rr, facets=(3, 6), segs=(10, 6, 5),
                        warp=0.04, amp=0.007, freq=3.0, face_bias=(0, -1, 0), bias_p=0.2, face_cuts=rng.randint(1, 4),
                        fillet=0.012, flat_top=H / 2 - 0.012,
                        flat_bot=-H / 2 + 0.02, batter=b_lo)
            put(P, F, ac, bot, D, tilt=(0.04, 0.04))
            # one or two flatter upper slabs, offset (break the joint)
            nu_ = 2 if (L > 0.62 and rng.rand() < 0.55) else 1
            span = L * rng.uniform(0.85, 1.05)
            for j in range(nu_):
                Lu = span / nu_ * rng.uniform(0.85, 1.0)
                xo = (j - (nu_ - 1) / 2) * span / nu_ + rng.uniform(-0.06, 0.06)
                Hu = top - lo_top + 0.008
                Pu, Fu = rock((Lu / 2, D * rng.uniform(0.38, 0.48), Hu / 2), rng,
                              round_r=min(rng.uniform(0.018, 0.032), Hu * 0.3), facets=(3, 5), segs=(8, 5, 4),
                              warp=0.04, amp=0.007, freq=3.5, face_bias=(0, -1, 0), bias_p=0.2,
                              face_cuts=rng.randint(1, 3), fillet=0.012, flat_top=Hu / 2 - 0.008, flat_bot=-Hu / 2 + 0.01, batter=rng.uniform(0.0, 0.03))
                put(Pu, Fu, ac + xo / r_c, lo_top - 0.006, D * 0.85, face_off=b_lo + rng.uniform(-0.005, 0.03),
                    tilt=(0.05, 0.05))
                n_up += 1
            # wedge chinking in the course joint
            for _ in range(rng.randint(1, 3)):
                xo = rng.uniform(-L / 2, L / 2) * 0.8
                hs = np.array([rng.uniform(0.035, 0.07), rng.uniform(0.05, 0.07), rng.uniform(0.012, 0.022)])
                Pc, Fc = rock(hs, rng, round_r=0.006, facets=(2, 3), segs=(2, 1, 1), warp=0.08, amp=0.002)
                Pc[:, 2] *= (1.0 - 0.6 * (Pc[:, 1] / hs[1] + 1) / 2)            # wedge: thin inward end
                put(Pc, Fc, ac + xo / r_c, lo_top - 0.012, 0.1, tilt=(0.05, 0.05), mat="M_rubble",
                    tgt=chink, face_off=b_lo + rng.uniform(0.035, 0.06))
                n_ch += 1
            tops.append(top)
        else:   # low stone + pinning slabs to bring the bed up to the wattle
            lo_top = rng.uniform(0.22, 0.28)
            H = lo_top - bot
            P, F = rock((L / 2, D / 2, H / 2), rng, round_r=rr, facets=(3, 6), segs=(9, 6, 5),
                        warp=0.04, amp=0.007, freq=3.0, face_bias=(0, -1, 0), bias_p=0.2, face_cuts=rng.randint(1, 4),
                        fillet=0.012, flat_top=H / 2 - 0.015,
                        flat_bot=-H / 2 + 0.02)
            put(P, F, ac, bot, D)
            kk = 2 if L > 0.45 else 1
            for j in range(kk):
                pl = L / kk * rng.uniform(0.6, 0.85)
                hp = np.array([pl / 2, rng.uniform(0.12, 0.17), (top - lo_top) / 2 + 0.004])
                Pp, Fp = rock(hp, rng, round_r=min(0.015, hp[2] * 0.5), facets=(2, 4), segs=(5, 4, 3),
                              warp=0.06, amp=0.003, flat_top=hp[2] * 0.8)
                xo = (j - (kk - 1) / 2) * L / kk + rng.uniform(-0.03, 0.03)
                put(Pp, Fp, ac + xo / r_c, lo_top - 0.004, 0.3, face_off=rng.uniform(0.04, 0.08))
                n_pin += 1
            tops.append(top)
        # wedge chinking driven into the vertical joint after this stone (recessed 2-5 cm)
        if i < len(stones) - 1:
            ga = ac + (L / 2) / r_c
            for zc in rng.choice([0.04, 0.12, 0.2, 0.3], rng.randint(1, 3), replace=False):
                hs = np.array([rng.uniform(0.018, 0.03), rng.uniform(0.05, 0.08), rng.uniform(0.03, 0.055)])
                Pc, Fc = rock(hs, rng, round_r=0.006, facets=(2, 3), segs=(1, 2, 2), warp=0.08, amp=0.002)
                Pc[:, 0] *= (1.0 - 0.65 * (Pc[:, 1] / hs[1] + 1) / 2)            # wedge: thin inward end
                put(Pc, Fc, ga + rng.uniform(-0.004, 0.004), zc + rng.uniform(-0.02, 0.02), 0.1,
                    rot_jit=0.15, tilt=(0.1, 0.25), mat="M_rubble", tgt=chink, face_off=rng.uniform(0.02, 0.05))
                n_ch += 1
    log("plinth stones:", len(stones), "upper:", n_up, "pinning:", n_pin, "chinking:", n_ch,
        "kinds:", {kk_: sum(1 for st in stones if st[2] == kk_) for kk_ in ("single", "double", "low", "through")})
    acc.build(coll)
    chink.build(coll)


def build_rubble(coll):
    acc = Acc("HUT_ground_rubble", 70)
    rng = np.random.RandomState(1011)
    pts = []
    # drip-line / plinth foot scatter (spalls fallen from the plinth, pebbles in the drip trench)
    for i in range(30):
        az = rng.uniform(0.35, 2 * math.pi - 0.35)
        r = rng.choice([rng.uniform(3.84, 4.0), rng.uniform(4.05, 4.45)])
        pts.append((az, r, rng.uniform(0.04, 0.15)))
    # cluster by the door, avoiding the path
    for i in range(14):
        x = rng.choice([-1, 1]) * rng.uniform(0.85, 1.7)
        y = rng.uniform(-4.6, -3.88)
        pts.append((math.atan2(x, -y), math.hypot(x, y), rng.uniform(0.04, 0.12)))
    for (az, r, sz) in pts:
        half = np.array([sz * rng.uniform(0.8, 1.2), sz * rng.uniform(0.65, 1.0), sz * rng.uniform(0.5, 0.8)])
        P, F = rock(half, rng, round_r=float(half.min()) * rng.uniform(0.35, 0.6), facets=(2, 4), segs=(4, 3, 3),
                    warp=0.12, amp=sz * 0.04, freq=2.0 / sz, fillet=sz * 0.25)
        R = rotz(rng.uniform(0, 6.28)) @ rotx(rng.uniform(-0.3, 0.3)) @ roty(rng.uniform(-0.3, 0.3))
        x_, y_ = math.sin(az) * r, -math.cos(az) * r
        g = float(apron_height(np.array([x_]), np.array([y_]))[0])
        c = (x_, y_, g + half[2] * rng.uniform(-0.45, 0.05))          # half-buried
        acc.add(xf(P, R, c), F, "M_rubble")
    acc.build(coll)


STEP_C = (0.04, FRONT_Y - 0.44)       # step stone centre (x, y)
APRON_RIM = 4.62


def apron_height(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    # mound: flat inside ~4.45 m, falls to Z_MIN at the rim, then a flat band at exactly Z_MIN
    rim = APRON_RIM + 0.10 * ring_noise(th, 1111, 5, 1.0)
    m = 1 - smoothstep(rim - 0.85, rim, r)
    h = Z_MIN + (0.0 - Z_MIN) * m
    lumps = 0.012 * fbm(np.stack([X * 0.9, Y * 0.9, np.zeros_like(X)], -1), 3) * m
    # drip-line trench under the eave (not across the path)
    dr = r - (4.17 + 0.03 * ring_noise(th, 1112, 5, 1.0))
    trench = -0.032 * np.exp(-(dr / 0.13) ** 2) * (1 - (np.abs(X) < 1.1) * (Y < 0))
    # gentle wear hollow along the path
    wear = -0.012 * np.exp(-(X / 0.5) ** 2) * (Y < -3.8) * (Y > -6.2)
    base = h + (lumps + trench + wear) * m
    # earth banked round the step stone: its top stands ~5 cm proud, the foot is buried
    ex = (X - STEP_C[0]) / 0.66
    ey = (Y - STEP_C[1]) / 0.39
    e = np.sqrt(ex ** 2 + ey ** 2)
    bank = 0.045 + 0.006 * n2(X * 6, Y * 6, 1120)
    w_ = 1 - smoothstep(1.0, 1.9, e)
    return np.where(e < 1.9, np.maximum(base, base * (1 - w_) + bank * w_), base)


def build_apron(coll):
    acc = Acc("HUT_ground_apron", 30)
    r_in, r_out = 3.15, 5.25
    rr = np.concatenate([np.arange(r_in, 4.95, 0.045), np.linspace(4.95, r_out, 4)])
    nt = 500
    th = 2 * np.pi * np.arange(nt) / nt
    R_, T_ = np.meshgrid(rr, th, indexing="ij")
    # irregular soil margin (no CG ring): the outer rows wander +-0.18 m
    edge_r = (5.1 + 0.12 * ring_noise(th, 1113, 9, 1.0, 0.6) + 0.05 * ring_noise(th, 1114, 45, 1.0, 0.2)
              + 0.02 * ring_noise(th, 1115, 120, 1.0, 0.0))
    over = np.clip((R_ - 4.95) / (r_out - 4.95), 0, 1)
    R_ = np.where(R_ > 4.95, 4.95 + over * (edge_r[None, :] - 4.95), R_)
    X = R_ * np.cos(T_)
    Y = R_ * np.sin(T_)
    Z = apron_height(X, Y)
    outer = R_ > (APRON_RIM + 0.10 * ring_noise(T_, 1111, 5, 1.0))
    Z = np.where(outer, Z_MIN, np.maximum(Z, Z_MIN))
    Z[-4:, :] = Z_MIN                 # >= 0.4 m flat band exactly at the bbox-min level
    P = np.stack([X, Y, Z], -1).reshape(-1, 3)
    nr = len(rr)
    i = np.arange(nr - 1)[:, None]
    j = np.arange(nt)[None, :]
    j1 = (j + 1) % nt
    F = np.stack([i * nt + j, (i + 1) * nt + j, (i + 1) * nt + j1, i * nt + j1], -1).reshape(-1, 4)   # normals up
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


def peg(acc, p, d, rng, r=0.015, proud=0.016, depth=0.05):
    """whittled oak peg: irregular octagon, proud 1.5-1.8 cm with a domed, slightly split head."""
    d = nrm(d)
    proud = proud * rng.uniform(0.95, 1.12)
    path = np.linspace(p - d * depth, p + d * proud, 5)
    ang = 2 * np.pi * np.arange(8) / 8 + rng.uniform(0, 1)
    rr = 1 + rng.uniform(-0.08, 0.08, 8)
    prof = np.stack([np.cos(ang) * rr, np.sin(ang) * rr], -1)
    rad = np.full(5, r * rng.uniform(0.9, 1.1))
    path, rad = chamfer_path(path, rad, 0.005)
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    P, F, uv, w = tube(path, rad, 8, up=up, profile=prof)
    acc.add(P, F, "M_timber", uv, w)


def build_door(coll):
    fr = Acc("HUT_door_frame", 28)      # adze ridges / checks read crisp; corner arcs are 18 deg
    leaf = Acc("HUT_door_leaf", 40)
    iron = Acc("HUT_door_ironwork", 50)
    thr = Acc("HUT_threshold", 50)
    rng = np.random.RandomState(1212)
    yc = FRONT_Y + 0.11                       # frame centre plane
    POST_BASE = 0.355
    for side in (-1, 1):
        x = side * 1.02
        # pad stone under each door post
        P, F = rock(np.array([0.27, 0.25, 0.22]), rng, round_r=0.03, facets=(4, 6), segs=(7, 7, 6), warp=0.08,
                    amp=0.009, freq=3.0, flat_top=0.20, flat_bot=-0.2, face_bias=(0, -1, 0), bias_p=0.4,
                    batter=0.03)
        thr.add(xf(P, rotz(side * 0.2 + rng.uniform(-0.1, 0.1)), (side * 1.04, -3.62, POST_BASE - 0.20)), F, "M_stone")
        # door posts (heavier, squared)
        RV = np.array([[0.0, 1, 0], [0, 0, 1], [1, 0, 0]])        # local X -> world Z (vertical member)
        wane_c = (3, 0) if side > 0 else (2, 1)                    # front-outer + back-outer arrises
        inner_f, outer_f = (1, 3) if side > 0 else (3, 1)
        hewn_member(fr, (x, yc, (POST_BASE + HEAD_Z) / 2), ((HEAD_Z - POST_BASE) / 2, 0.12, 0.11),
                    rotz(side * 0.006) @ RV, rng, ch=0.02, wane=wane_c, n_checks=3, check_faces=(2, 2, outer_f, inner_f),
                    ns=9, nc=6)
        # inner jambs on the sill
        xj = side * 0.60
        hewn_member(fr, (xj, yc, (SILL_TOP + HEAD_Z) / 2), ((HEAD_Z - SILL_TOP) / 2, 0.10, 0.11),
                    rotz(side * 0.004) @ roty(side * 0.003) @ RV, rng, ch=0.018, wane=(2 if side > 0 else 3,),
                    n_checks=2, check_faces=(2, inner_f), ns=8, nc=6)
        # sole rail under the side panel, resting on the sill end
        hewn_member(fr, (side * 0.805, yc, (SILL_TOP + 0.405) / 2), (0.115, 0.075, (0.405 - SILL_TOP) / 2),
                    np.eye(3), rng, ch=0.015, ns=6, nc=5, ds=0.015)
        # return tie beam from the door post to the wall post
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL, 0)
        p0 = np.array([x, yc + 0.05, HEAD_Z + 0.11])
        p1 = np.array([wp[0], wp[1], HEAD_Z + 0.11])
        L = float(np.linalg.norm(p1 - p0))
        R = frame_R(p1 - p0, (0, 0, 1))
        hewn_member(fr, (p0 + p1) / 2, (L / 2 + 0.1, 0.08, 0.10), R, rng, ch=0.02, wane=(0,), end_checks=1,
                    sag=0.004, ns=6, nc=6)
        # pegs: lintel -> door post and jamb tenons, sill tenons
        for (px, pz, fy) in ((x - side * 0.03, HEAD_Z + 0.06, FRONT_Y - 0.009), (x + side * 0.045, HEAD_Z + 0.15, FRONT_Y - 0.009),
                             (xj, HEAD_Z + 0.07, FRONT_Y - 0.009), (xj - side * 0.03, SILL_TOP + 0.05, FRONT_Y + 0.004)):
            peg(fr, np.array([px, fy, pz]), (0, -1, 0), rng)
        peg(fr, p1 - R[:, 0] * 0.06 + np.array([0, 0, 0.10]), (0, 0, 1), rng)
    # lintel on the door posts (front face slightly proud), slight sag
    hewn_member(fr, (0.0, yc - 0.008, HEAD_Z + 0.11), (1.15, 0.115, 0.11), np.eye(3), rng, ch=0.022,
                wane=(1,), n_checks=2, check_faces=(1,), end_checks=2, sag=0.008, ns=9, nc=6)
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
    P, F = rock(np.array([0.95, 0.30, 0.075]), rng, round_r=0.02, facets=(3, 5), segs=(14, 5, 3), warp=0.04,
                amp=0.006, freq=2.5, flat_top=0.06, chips=4, face_bias=(0, -1, 0), bias_p=0.5)
    thr.add(xf(P, rotz(0.01), (0.0, FRONT_Y + 0.12, 0.09 - 0.06)), F, "M_stone")
    V, F = rbox((0.92, 0.13, (SILL_TOP - 0.09) / 2), 0.02, (14, 3, 1))
    top = V[:, 2] > 0
    V[top, 2] -= 0.018 * np.exp(-(V[top, 0] / 0.30) ** 2) * (0.55 + 0.45 * (V[top, 1] < 0))
    V[:, 2] += 0.003 * np.sin(V[:, 0] * 9.0)
    V = xf(V, None, (0.0, yc, (SILL_TOP + 0.09) / 2))
    thr.add(V, F, "M_timber")
    # big flat step stone (top ~0.09)
    # big flat step stone: split slab with a flat, wear-dished top, chipped arrises, foot buried
    hs = np.array([0.64, 0.37, 0.07])
    rs_step = np.random.RandomState(1314)
    P, F = rock(hs, rs_step, round_r=0.022, facets=(5, 7), segs=(16, 10, 3), warp=0.03, amp=0.004, freq=3.0,
                chips=6, flat_top=hs[2] - 0.012, flat_bot=-hs[2] + 0.01, fillet=0.014, nz_w=0.12)
    rq = (P[:, 0] / hs[0]) ** 2 + (P[:, 1] / hs[1]) ** 2
    top_ = P[:, 2] > hs[2] * 0.4
    P[top_, 2] -= 0.008 * np.clip(1 - rq[top_] * 1.1, 0, 1) ** 0.8
    P = xf(P, rotz(0.05))
    thr.add(P + [STEP_C[0], STEP_C[1], 0.095 - float(P[:, 2].max())], F, "M_stone")
    # stepping-stone path: irregular flags laid one or two abreast, ~2.5 m out from the step
    ys = -4.50
    k = 0
    n_flags = 0
    while ys > -6.15:
        ly = rng.uniform(0.15, 0.21)
        two = rng.rand() < 0.75
        xc = 0.08 * math.sin(k * 1.7) + rng.uniform(-0.12, 0.12)
        if two:
            lxa, lxb = rng.uniform(0.2, 0.3), rng.uniform(0.18, 0.28)
            gap = rng.uniform(0.04, 0.09)
            xs_ = [(xc - gap / 2 - lxa, lxa), (xc + gap / 2 + lxb, lxb)]
        else:
            lx = rng.uniform(0.28, 0.42)
            xs_ = [(xc + rng.uniform(-0.1, 0.1), lx)]
        for (xo, lx) in xs_:
            lyy = ly * rng.uniform(0.85, 1.1)
            yo = ys - ly + rng.uniform(-0.04, 0.04)
            P, F = flagstone(lx, lyy, 0.10, rng)
            topz = rng.uniform(0.006, 0.02) + max(float(apron_height(np.array([xo]), np.array([yo]))[0]), Z_MIN)   # bedded
            thr.add(xf(P, rotz(rng.uniform(-0.35, 0.35)) @ rotx(rng.uniform(-0.012, 0.012)), (xo, yo, topz)), F, "M_stone")
            n_flags += 1
        ys -= 2 * ly + rng.uniform(0.04, 0.09)
        k += 1
    log("path flags:", n_flags)
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
        outline = [(0.0, -0.026), (-Ls + 0.10, -0.023), (-Ls + 0.055, -0.038), (-Ls, 0.0),
                   (-Ls + 0.055, 0.038), (-Ls + 0.10, 0.023), (0.0, 0.026)]
        V, faces = prism(outline[::-1], 0.007)
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
            Vn = np.stack([Vn[:, 0] + xn, face_y - 0.007 - Vn[:, 2], Vn[:, 1] + zh], -1)
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
    zz = build_collar_finial(coll)
    log("collar drip %.3f fascia top %.3f lower top %.3f upper top %.3f spindle top %.3f tip %.3f" % zz)
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
