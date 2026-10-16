"""Wattle-and-Daub Round Hut with Shingle Cone (HUT) -- deterministic procedural build.

Geometry only (named placeholder material slots, UVs on every mesh).

Run:  /opt/bpyenv/bin/python build_wattle_roundhut.py
Saves wattle_roundhut.blend next to this script.

Layout (metres, Z up, hut centred on the world origin, door centred on -Y):
  * dry-stone boulder plinth ring (outer dia ~7.5 m, top ~0.38 m) with chinking, standing on a flat
    Z = 0 datum with a <= 4 cm buried skirt (producer note 10: no apron / path / rubble / flags)
  * 14 round-hewn posts; MOSTLY INTACT DAUB on every bay (client r6) over woven wattle that is modelled
    only where it shows: the ref2 eroded band left of the door, 3 small broken-away patches (+X side,
    back-right foot, back-left under the eave), the weathered foot and the door rope panels
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
Round 4: wattle joints only at stakes (22 % of rows, ends hidden behind the stake, shared row lane),
twisted-rope door side / cheek panels (rope_panel, ends buried in the framing, daub backing),
plinth of rounded polyhedral field stones (field_stone / facet_stone: crowned tops, bulging fronts,
varied arrises, 35 % fracture facets) with the weave bedded onto the stone tops, low boulder door
pads, split 3-slab threshold, dished step, paving flags laid from their real outlines with partial
earth lips, sub-angular rubble, eroded back-bay daub carried to the plinth, horizontal-only daub
ridging with palm dents, V-section timber checks and diagonal adze lanes, post heads inside the plate.
Round 6 (client correction): daub on all 13 bays (graded tensor grid, hand-applied dabs, sag belly,
splash-eroded foot, shrinkage cracks), fracture-polygon exposed patches stepped along the rod rows,
rods / stakes / post flanks / plinth tops buried in the coat deleted, ground dressing removed.
All randomness is seeded; the script is reproducible bit-for-bit.
"""
import math
import os
import time
import zlib

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
    (skirt depth outside / interior floor) is culled."""

    def __init__(self, name, sharp_angle=40.0, cull="ground", moss=None):
        self.name = name
        self.V, self.UV = [], []
        self.MR, self.MG = [], []                     # Mask R (per-piece random), G (per-piece wear)
        self.mrng = np.random.RandomState(zlib.crc32(name.encode()) & 0x7FFFFFFF)
        self.moss = moss                              # None: B from world height / facing
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

    def mask_b(self, V, VN):
        """moss / dirt / damp: high near the ground and on the plinth, on up-facing ledges and roof butts,
        on shaded north faces; low on sheltered faces high up."""
        if self.moss is not None:
            return np.full(len(V), float(self.moss))
        z = V[:, 2]
        ground = np.clip(1.0 - z / 0.7, 0, 1) ** 1.5
        up = np.clip(VN[:, 2], 0, 1)
        north = np.clip(VN[:, 1], 0, 1) * 0.25
        high = smoothstep(0.9, 2.6, z) * (1 - smoothstep(2.6, 3.2, z))      # sheltered wall under the eave
        b = np.maximum(ground, 0.45 * up) + north - 0.2 * high
        return np.clip(b + 0.06 * n2(V[:, 0] * 2.0, V[:, 1] * 2.0 + z, 77), 0, 1)

    def add_part(self, part, mat, smooth=True):
        self.add(part[0], part[1], mat, part[2] if len(part) > 2 else None,
                 wrap=part[3] if len(part) > 3 else False, smooth=smooth)

    def build_mesh(self, name=None, clamp=True):
        V = np.concatenate(self.V)
        if clamp:
            V[:, 2] = np.maximum(V[:, 2], Z_MIN + 0.004)
        UVv = np.concatenate(self.UV)
        MR = np.concatenate(self.MR)
        MG = np.concatenate(self.MG)
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
        # ---- producer note 9: 'Mask' colour attribute (CORNER, active + default/render)
        VN = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertex_normals.foreach_get("vector", VN)
        VN = VN.reshape(-1, 3)
        Vm = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", Vm)
        Vm = Vm.reshape(-1, 3).astype(float)
        if len(Vm) == len(MR):
            mr, mg = MR, MG
        else:                                         # validate() changed the vertex set (rare)
            mr = np.full(len(Vm), 0.5)
            mg = np.full(len(Vm), 0.3)
        mb = self.mask_b(Vm, VN)
        li = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", li)
        col = np.stack([mr[li], mg[li], mb[li], np.ones(len(li))], -1).astype(np.float32)
        ca = me.color_attributes.new("Mask", "BYTE_COLOR", "CORNER")
        ca.data.foreach_set("color", col.ravel())
        me.color_attributes.active_color_name = "Mask"
        me.color_attributes.default_color_name = "Mask"
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


POOL_MOSS = {"chink": 0.6}


def pool_mesh(pool, k, make, sharp=40.0):
    """k-th variant of a pool; make(acc, k) fills an Acc in local coords. Built once, reused."""
    key = (pool, k)
    if key not in POOLS:
        acc = Acc(f"HUT_{pool}_v{k:02d}", sharp, cull=None, moss=POOL_MOSS.get(pool, 0.2))
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


def _spow(x, e):
    return np.sign(x) * np.abs(x) ** e


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


def vert_normals(P, faces):
    VN = np.zeros_like(P)
    for Fx in faces:
        Fx = np.asarray(Fx)
        Q = P[Fx]
        n_ = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0])
        for k in range(Fx.shape[1]):
            np.add.at(VN, Fx[:, k], n_)
    return nrm(VN + 1e-12)


def stone_skin(P, faces, rng, n_scoop=(6, 12), scoop_r=(0.04, 0.10), scoop_d=(0.004, 0.010), lump_a=0.010,
               lump_f=8.0, pit_a=0.0025, vis=None, size=1.0):
    """hand-split stone surface (director r4 #2b): shallow CONCHOIDAL flake scars -- dish-shaped, deepest
    near the impact side, ending in a crisp crease (profile (1 - r/R)^0.6 -> steep at the rim; where
    scars overlap the deeper one wins, leaving a sharp ridge between them), 1-2 cm lumps at a 10-15 cm
    wavelength and small pits.  vis(P, VN) -> weight 0..1 of 'visible face' (scars go there)."""
    VN = vert_normals(P, faces)
    w_vis = np.ones(len(P)) if vis is None else vis(P, VN)
    off = rng.uniform(-50, 50, 3)
    lump = lump_a * size * (fbm(P * lump_f + off, 2) + 0.35 * vnoise(P * lump_f * 2.3 + off * 0.7))
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
        cutd = np.minimum(cutd, d * 1.6) * w_vis * m
        P = P - VN * cutd[:, None]
    pits = pit_a * np.clip(vnoise(P * 55.0 + off * 1.3) * 2.2 - 0.9, 0, 1)
    P = P - VN * (pits * w_vis)[:, None]
    return P


def plinth_kind_stone(kind, half, rng, fracture=True, frac_side=None, n_front=80, n_up=34):
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
    V, F = facet_stone(half, rng, S, k_round=k_r, fracs=fr, k_frac=0.0018, lump=0.002, lump_f=6.0, pit=0.0,
                       th=th, ph=ph, chips=rng.randint(1, 3))

    def vis(P, VN):
        return np.clip((VN[:, 1] + 0.2) * 2.0, 0, 1) * np.clip((P[:, 2] + c * 0.6) / (c * 0.5), 0, 1) \
            + np.clip(VN[:, 2] * 1.5, 0, 1) * (P[:, 1] > -0.2 * b)
    V = stone_skin(V, F, rng, n_scoop=(6, 12), scoop_r=(0.04, 0.10), scoop_d=(0.004, 0.010),
                   lump_a=0.010 if kind != "boulder" else 0.014, lump_f=8.0, pit_a=0.003,
                   vis=lambda P, VN: np.clip(vis(P, VN), 0, 1))
    return V, F


def pad_stone(rng, plan=(0.23, 0.18), vis_h=0.18, bury=0.05, tilt_deg=(1.0, 3.0), n_corner=(6, 8), batter=(16, 36)):
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
    V, F = facet_stone((hu, hv, c), rng, S, k_round=0.0028, fracs=fr, k_frac=0.0018, lump=0.0015, lump_f=7.0,
                       pit=0.0, th=th, ph=ph, chips=rng.randint(1, 3))
    V = stone_skin(V, F, rng, n_scoop=(5, 8), scoop_r=(0.03, 0.07), scoop_d=(0.003, 0.007), lump_a=0.004,
                   lump_f=9.0, pit_a=0.002, vis=lambda P, VN: np.clip(VN[:, 2] * 0.5 + 0.6, 0, 1) * (P[:, 2] > -c * 0.2))
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


def frame_wall(az):
    """local stone frame on the ring at azimuth az: x along the ring (-tangent), y radial out, z up."""
    t = np.array([math.cos(az), math.sin(az), 0.0])
    u = np.array([math.sin(az), -math.cos(az), 0.0])
    return np.stack([-t, u, np.array([0, 0, 1.0])], -1)


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
Z_MIN = -0.045               # lowest point (buried footing skirt); nothing deeper than 5 cm (note 6)
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
    t_sh = 1 - 0.26 / (top[2] - base[2])
    t_sh = 1 - 0.016 / (top[2] - base[2])
    t = np.concatenate([np.linspace(0, tz, 40), np.linspace(tz, t_sh, 3)[1:], np.linspace(t_sh, 1, 3)[1:]])
    nseg = len(t)
    lean = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]) * math.tan(math.radians(0.7))
    H = top[2] - base[2]
    bow = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]) * 0.012
    path = base[None, :] + np.outer(t, top - base) + np.outer(t * H, lean) + np.outer(np.sin(np.pi * t), bow)
    taper = rad * (1 + 0.05 * (0.5 - t)) + rng.uniform(-0.005, 0.005)
    # director r4 #5d: the post is cut square under the plate (the plate bears on its end grain): only a
    # 1.5 cm arris chamfer at the head, no long visible taper / sliver under the plate
    shoulder = smoothstep(H - 0.016, H, t * H)
    taper = taper * (1 - 0.14 * shoulder)
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
                hero=(), hidden=(), deform=None, stride=7, caps=(True, True), wear=None):
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
    # director r4 #4: STROKE-ALIGNED topology.  Every adzed face gets one diagonal stroke skew; its vertex
    # columns are slid along the member by -skew * across, so each vertex row runs exactly along a stroke
    # boundary line (no stair-stepped crease across the grid).  The corner arcs blend the two neighbouring
    # faces' edge shifts; the shear ramps out over the last 12 cm at each end (square end cuts).
    skews = np.zeros(4)
    for c in range(4):
        if adze and c not in hidden:
            fhw = a0 if c in (0, 2) else b0
            skews[c] = rng.choice([-1.0, 1.0]) * math.tan(math.radians(rng.uniform(25.0, 40.0))) * fhw
    # each face's strokes follow the adze swing: a slight bow (one per face), stroke boundaries stay on rows
    bows = np.array([rng.uniform(0.05, 0.12) * abs(skews[c]) * rng.choice([-1.0, 1.0]) for c in range(4)])
    shift = np.zeros(M)
    for c in range(4):
        js = np.where(face == c)[0]
        shift[js] = skews[c] * across[js] + bows[c] * (across[js] ** 2 - 1.0)
        cp = (c - 1) % 4
        for k_ in range(nc):
            t_ = k_ / max(nc - 1, 1)
            shift[c * (ns + nc) + k_] = skews[cp] * (1 - t_) - skews[c] * t_
    ramp = smoothstep(0.0, min(0.12, hl * 0.45), xs + hl) * smoothstep(0.0, min(0.12, hl * 0.45), hl - xs)
    Xs = xs[:, None] - shift[None, :] * ramp[:, None]          # actual vertex positions along the member
    if adze:
        for c in range(4):
            if c in hidden:
                continue
            js = np.where(face == c)[0]
            hero_f = c in hero
            nlane = 1                    # director r4 #4: one stroke lane per face (no lane-seam steps)
            # consistent diagonal lanes per face (director r3 #6): every stroke boundary on this face
            # runs at the same 25-40 deg skew
            skew_f = skews[c]
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
                xe = Xs[:, jl] + skew_f * across[jl][None, :] + bows[c] * (across[jl][None, :] ** 2 - 1.0)
                k = np.clip(np.searchsorted(bnd, xe.ravel()) - 1, 0, len(bnd) - 2).reshape(xe.shape)
                tl = np.clip((xe - bnd[k]) / (bnd[k + 1] - bnd[k]), 0, 1)
                # scoop: deepest early in the stroke, ends in a small ridge; fades toward lane edges
                ac_ = np.abs(across[jl])[None, :]
                fade = 1 - 0.35 * smoothstep(0.7, 1.0, ac_)
                # scoop: steep entry at the boundary -> crisp crease between strokes, shallower run-out
                sc = dep[k] * np.sin(np.pi * tl) ** 0.6 * (0.7 + 0.3 * (1 - tl)) * fade
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
        # V-section (director r3 #6): the lips close onto the crack line wherever the crack is shallow,
        # so the mouth width and the depth both run to zero at the ends (no rectangular pocket)
        hw = width / 2 * np.sqrt(np.clip(m, 0, 1))
        for jn, sg in ((j - 1, 1), (j + 1, -1)):
            dist = np.abs((Y[ii, jn] - Y[ii, j]) * tyz[0] + (Zp[ii, jn] - Zp[ii, j]) * tyz[1])
            pull = np.clip(dist - hw, 0, None)
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
        w_ck = rng.uniform(0.006, 0.010)
        apply_check(c, j_off, i0, i1, w_ck * rng.uniform(0.9, 1.3), w_ck)
        if rng.rand() < 0.6:          # short en-echelon branch (parallel, i.e. <= 30 deg), own lips
            jb = j_off + rng.choice([-3, 3])
            if 1 <= jb <= ns - 2:
                lb = rng.uniform(0.05, 0.12)
                xb = x0 + rng.uniform(0.2, 0.7) * lc
                ib0 = int(np.searchsorted(xs, xb))
                ib1 = int(np.searchsorted(xs, min(xb + lb, hl - 0.05)))
                w_b = rng.uniform(0.003, 0.005)
                apply_check(c, jb, ib0, ib1, w_b * rng.uniform(0.9, 1.3), w_b)
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
            w_e = rng.uniform(0.004, 0.007)
            apply_check(c, j_off, i0, i1, w_e * rng.uniform(1.0, 1.6), w_e, from_end=side_)
    for i_e in (0, n - 1):
        Y[i_e] *= 1 - che / max(a0, 1e-3)
        Zp[i_e] *= 1 - che / max(b0, 1e-3)
    X = Xs.copy()
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
    acc.add(Vw, Fl + ([cap0, fan0] if caps[0] else []) + ([cap1, fan1] if caps[1] else []), mat, wear=wear)


def post_cull(V):
    """producer note 6 / client r6: the post flanks buried in the intact daub coat (the coat meets each
    post ~6 cm proud of the wattle line) and the post backs behind the wattle line are never seen.
    Door-side flanks of the two door-bay wall posts stay whole (seen through the doorway)."""
    hid = cull_below_ground(V)
    X, Y, Zv = V[:, 0], V[:, 1], V[:, 2]
    az = np.mod(np.arctan2(X, -Y), 2 * np.pi)
    dr = np.hypot(X, Y) - R_WALL
    ip = np.argmin(np.abs(np.angle(np.exp(1j * (az[:, None] - POST_AZ[None, :])))), axis=1)
    dt = np.angle(np.exp(1j * (az - POST_AZ[ip])))
    nb = len(POST_AZ) - 1
    bay = np.where(dt > 0, ip, ip - 1)
    door_side = (bay < 0) | (bay >= nb)
    intact = np.zeros(len(V), bool)
    for b in range(nb):
        m = bay == b
        if m.any():
            s_side = (POST_AZ[ip[m]] + np.sign(dt[m]) * 0.12 / R_WALL) * R_WALL
            intact[m] = DAUB_BAYS[b](s_side, Zv[m]) > 0.07
    intact &= (Zv > 0.3) & (Zv < PLATE_BOT - 0.12)
    thr = np.where(intact, 0.02, -0.015)
    return hid | (~door_side & (Zv > 0.3) & (dr < thr))


def plinth_under_coat(V):
    """client r6: where the intact daub foot comes down onto the stones, the stone top behind the wattle
    centre line (under the bottom rod row and the coat) is never seen."""
    r_ = np.hypot(V[:, 0], V[:, 1])
    cand = (r_ < R_WALL + 0.005) & (V[:, 2] > 0.18)
    hid = np.zeros(len(V), bool)
    if not cand.any():
        return hid
    az = np.mod(np.arctan2(V[cand, 0], -V[cand, 1]), 2 * np.pi)
    sw = az * R_WALL
    cover = np.zeros(len(az), bool)
    for b in range(len(POST_AZ) - 1):
        sb0, sb1 = bay_s(b)
        m = (sw > sb0 + 0.10) & (sw < sb1 - 0.10)
        if m.any():
            cover[m] = DAUB_BAYS[b](sw[m], wall_floor(sw[m]) + 0.045) > 0.0
    hid[np.where(cand)[0][cover]] = True
    return hid


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


def build_posts(coll):
    acc = Acc("HUT_posts", 15, cull=post_cull)   # low angle: adze-flat edges crisp, 48-gon stays smooth
    rng = np.random.RandomState(202)
    for i, az in enumerate(POST_AZ):
        # stand on the crowned stone under the post: lowest stone point under the footprint (no float)
        fp = [az_pt(az + da / R_WALL, R_WALL + dr) for da in (-0.08, 0.0, 0.08) for dr in (-0.07, 0.0, 0.08)]
        zb_ = float(np.min(stone_top([p_[0] for p_ in fp], [p_[1] for p_ in fp])))
        b = az_pt(az, R_WALL, zb_ - 0.012)
        tp = az_pt(az, R_WALL, PLATE_BOT + 0.004)       # head bears on the plate underside
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
ROD_SHADOW_Z = 2.28
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


ROD_STORE = {}       # panel seed -> [(s, path, radius)] of its rods (daub clumps wrap them)


def weave_panel(rods, stakes_acc, pathf, s0, s1, z0, z1, seed, hide=None, n_stakes=None, stake_bottom=None,
                slant=0.0, rod_r=(0.014, 0.019), gap=(0.002, 0.009), stake_r=(0.014, 0.018), trim=(0.0, 0.0),
                junctions=True, lean=1.5, stake_sp=0.40, stake_back=0.022, junction_p=0.22, floor=None):
    """woven panel between s0 and s1 (post / jamb centres; rods end `trim` inside them).
    Spec amendment r2: thin stakes (dia 3-4 cm) ~0.38-0.50 m apart, jittered +-4 cm and leaning
    +-1.5 deg, mostly hidden behind the rods; rods dia 2.5-3.8 cm with 0.5-2.5 cm dark gaps between
    rows; every rod wraps its stakes with a clearance of 3-5 mm (offset = stake_r + rod_r + gap, 60 %
    of the swing within +-6 cm of the stake) so no rod intersects a stake; per-rod drift +-1 dia at
    0.5-1 m wavelength; rods tapered butt->tip 1.0->0.55; ~15 % paired / tripled rows; knots, kinks.
    Joints (r4): only `junction_p` of rows, always AT a stake the row passes behind, both ends hidden
    there, never at the same stake in consecutive rows; <= 10 % of tips flicked 1-3 cm.
    floor(s): optional stone-top height -- the weave is bedded onto it (nothing modelled below)."""
    rng = np.random.RandomState(seed)
    L = s1 - s0
    if floor is not None:
        # the weave is bedded down onto the crowned plinth stones: anything under the local stone top
        # (floor(s)) is inside the stone and is not modelled
        hide0 = hide

        def hide(s_, z_, _h=hide0):
            hb = np.asarray(z_) < floor(s_) - 0.004
            return hb if _h is None else (hb | _h(s_, z_))
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
        zb_k = zb if floor is None else float(floor(np.array([base[k]]))[0]) - 0.03
        zz = np.linspace(zb_k, z1 + 0.03, nz)
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
    # ---- rods (director r4 #1): every row is laid ON the one below.  The row centre line is computed
    # from the previous row's real envelope top (local tapered radius along s) plus a 0-1.2 cm gap that
    # wanders slowly along the row (rows may touch / press together, they never open up), so the dark
    # gaps stay 0.3-1.5 cm everywhere and the weave reads as a packed band.  Taper butt->tip 1.0->0.8.
    tilt = rng.uniform(-0.008, 0.008) + slant
    z_lo = z0 - (max(0.0, tilt) * L if steep else 0.0)
    z_stop = z1 - (min(0.0, tilt) * L if steep else 0.0)
    sg = np.linspace(s0, s1, max(24, int(L / 0.01) + 1))
    top_prev = z_lo + tilt * (sg - s0)
    K_ENV = 0.97                         # visible half-height of a rod section (arc ends at >= 76 deg)

    def g_smooth(v, sig_m=0.035):
        sig = max(1.0, sig_m / max(sg[1] - sg[0], 1e-4))
        kk = np.arange(-int(3 * sig), int(3 * sig) + 1)
        ker = np.exp(-0.5 * (kk / sig) ** 2)
        ker /= ker.sum()
        return np.convolve(np.pad(v, len(kk) // 2, mode="edge"), ker, mode="valid")

    def taper_f(s_, a, b, tipside):
        tpos = np.clip((s_ - a) / max(b - a, 1e-3), 0, 1)
        return 1.0 - 0.2 * (tpos if tipside > 0 else 1 - tpos)

    row = 0
    n_rods = 0
    prev_j = None
    while True:
        u = rng.rand()
        nsub = 3 if u < 0.04 else (2 if u < 0.15 else 1)
        r_row = rng.uniform(*rod_r)
        if nsub == 1:
            subs = [(r_row, 0.0)]
        elif nsub == 2:
            rA, rB = r_row * rng.uniform(0.72, 0.85), r_row * rng.uniform(0.68, 0.82)
            subs = [(rA, -rB * 1.0), (rB, rA * 1.0)]
        else:
            rr_ = r_row * rng.uniform(0.6, 0.72, 3)
            subs = [(rr_[0], -(rr_[0] + rr_[1]) * 1.0), (rr_[1], 0.0), (rr_[2], (rr_[1] + rr_[2]) * 1.0)]
        signs_par = (row % 2)
        z_est = float(top_prev.mean()) + r_row
        # pieces (director r3 #1): one rod post to post, or -- in ~22 % of rows -- two rods joined AT a
        # stake the row passes BEHIND (both ends hidden there); <= 10 % of tips flick out 1-3 cm.
        pieces = []
        a0, a1 = s0 + trim[0], s1 - trim[1]
        jk = None
        if junctions and n_stakes >= 1 and L > 0.9 and rng.rand() < junction_p:
            cand = [k for k in range(n_stakes) if (-1.0) ** (k + 1 + signs_par) < 0 and k != prev_j]
            if cand:
                jk = int(cand[rng.randint(len(cand))])
        if jk is not None:
            sjk = float(stake_s(jk, z_est))
            dA, dB = rng.uniform(0.02, 0.05), rng.uniform(0.02, 0.05)
            flickA = rng.uniform(0.01, 0.03) if rng.rand() < 0.1 else 0.0
            pieces.append((a0, sjk + dA, ("A", sjk, dA, flickA), 1))
            pieces.append((sjk - dB, a1, ("B", sjk, dA, 0.0), 1))
            prev_j = jk
        else:
            pieces.append((a0, a1, None, 1 if rng.rand() < 0.5 else -1))
            prev_j = None
        # row envelope relative to the row centre line, on the panel grid sg
        e_lo = np.full(len(sg), np.inf)
        e_hi = np.full(len(sg), -np.inf)
        rn_row = 1 + 0.05 * n2(sg * 5, np.full(len(sg), z_est), seed + 7)
        for (a, b, jinfo, tipside) in pieces:
            inr = (sg >= a - 0.01) & (sg <= b + 0.01)
            for (rr0, dzz) in subs:
                rp = rr0 * taper_f(sg, a, b, tipside) * rn_row
                e_lo = np.where(inr, np.minimum(e_lo, dzz - K_ENV * rp), e_lo)
                e_hi = np.where(inr, np.maximum(e_hi, dzz + K_ENV * rp), e_hi)
        okm = np.isfinite(e_lo)
        e_lo = np.interp(sg, sg[okm], e_lo[okm])
        e_hi = np.interp(sg, sg[okm], e_hi[okm])
        # gap to the row below: 0-1.2 cm, wandering at 0.3-0.7 m; touching (slightly pressed) in places
        wl = rng.uniform(0.3, 0.7)
        gap_s = (rng.uniform(gap[0], gap[1]) + 0.0035 * n2(sg / wl, np.full(len(sg), seed * 0.13 + row * 1.7), 7000 + seed % 97))
        gap_s = np.clip(gap_s, -0.003, 0.012)
        if row == 0:
            gap_s = gap_s * 0 + rng.uniform(0.002, 0.008)
        centre = g_smooth(top_prev + gap_s - e_lo)
        if float((centre + e_lo).min()) > z_stop - 0.006:
            break
        top_prev = centre + e_hi
        for (a, b, jinfo, tipside) in pieces:
            junction_piece = jinfo is not None
            for si, (rr0, dzz) in enumerate(subs):
                rseed = seed * 131 + row * 7 + si * 3 + int(a * 10)
                z = float(np.interp((a + b) / 2, sg, centre)) + dzz
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
                if z > ROD_SHADOW_Z:
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
                # small wobble + kinks at side shoots (the rows still bear on each other)
                drift = 0.0015 * n2(ss * 4.0, np.full(n, rseed * 0.71), 7100 + seed % 89)
                for kp_ in kpos:
                    if rng.rand() < 0.55:
                        drift = drift + rng.uniform(-1, 1) * 0.005 * np.clip(1 - np.abs(ss - kp_) / 0.07, 0, 1) ** 1.5
                zz = np.interp(ss, sg, centre) + dzz + drift
                k_ = np.clip(np.searchsorted(st, ss) - 1, 0, len(st) - 2)
                D = st[k_ + 1] - st[k_]
                t = np.clip((ss - st[k_]) / np.maximum(D, 1e-3), 0, 1)
                tau = np.clip(0.06 / np.maximum(D, 1e-3), 0.05, 0.3)
                o0 = sgn[k_] * Ak[k_] + rho[k_]
                o1 = sgn[k_ + 1] * Ak[k_ + 1] + rho[k_ + 1]
                off = o0 + (o1 - o0) * _hermite_F(t, tau)
                taper = taper_f(ss, a, b, tipside)
                tip_at_end = junction_piece and jinfo[0] == "A"
                tip_at_start = junction_piece and jinfo[0] == "B"
                flick = np.zeros(n)
                if tip_at_end and jinfo[3] > 0:
                    tt_ = 1 - np.clip(np.abs(ss - b) / 0.08, 0, 1)
                    flick = jinfo[3] * tt_ ** 2
                if tip_at_start:
                    # new rod: tucked behind the old one through the overlap at the stake, then free
                    sjk_, dA_ = jinfo[1], jinfo[2]
                    w_ = 1 - smoothstep(sjk_ + dA_, sjk_ + dA_ + 0.06, ss)
                    off = off - w_ * rr0 * 2.0
                off = off + flick
                pt, nn = pathf(ss)
                path = np.c_[pt + nn * off[:, None], zz]
                knot = np.zeros(n)
                for kp_ in kpos:
                    knot += 0.15 * np.exp(-((ss - kp_) / 0.011) ** 2)
                rad = rr0 * taper * (1 + knot) * np.interp(ss, sg, rn_row)
                if seed in ROD_STORE:
                    ROD_STORE[seed].append((ss.copy(), path.copy(), rad.copy()))
                kn = 0.05 * n2(np.arange(n)[:, None] * 0.35 + np.zeros((1, len(ROD_ARC))),
                               np.broadcast_to(ROD_ARC * 1.7, (n, len(ROD_ARC))), rseed)
                vis = np.ones(n, bool) if hide is None else ~hide(ss, zz)
                vis &= (zz - rad) < z_stop + 0.004            # fully inside the wall plate: not modelled
                vis = vis | np.roll(vis, 1) | np.roll(vis, -1) | np.roll(vis, 2) | np.roll(vis, -2)
                close = flick > 0.002
                oval = rng.uniform(0.85, 0.94)
                # section arc (up side first, then down side, degrees from the outward horizontal): the
                # side facing the viewers is carried past the vertical; the far side stops at 76-90 deg
                proud = np.clip((off - rho.mean()) / np.maximum(Ak.mean(), 1e-3), 0, 1)
                if junction_piece:
                    proud = np.maximum(proud, 0.5)
                if z > ROD_SHADOW_Z:             # deep in the eave shadow (seen from below): lighter
                    up_a, dn_a = np.full(n, 78.0), 96.0 + 10.0 * proud
                elif z < 1.55:                   # below eye level: the tops are seen
                    up_a, dn_a = 98.0 + 14.0 * proud, 78.0 + 6.0 * proud
                else:                            # above eye level: the undersides are seen
                    up_a, dn_a = 78.0 + 6.0 * proud, 98.0 + 14.0 * proud
                m_arc = 4 if (z > ROD_SHADOW_Z and not steep) else len(ROD_ARC)
                arc_n = -np.radians(up_a)[:, None] + (np.radians(up_a + dn_a))[:, None] * np.linspace(0, 1, m_arc)[None, :]
                kn = kn[:, :m_arc]
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


def rope_panel(rods, stakes_acc, back_acc, pathf, W, z0, z1, seed, slant, embed=(0.03, 0.03, 0.03, 0.03),
               rod_r=(0.012, 0.015), gap=(0.002, 0.005), stake_r=(0.012, 0.014), n_stakes=2, back_gap=0.012):
    """narrow 'twisted rope' wattle panel (director r3 #2), e.g. between a door jamb and a door post.
    Diagonal rods (slope `slant` = dz/ds) packed with a 2-5 mm perpendicular gap; each rod is one
    continuous S-curve that passes alternately in front of / behind the `n_stakes` vertical stakes
    (neighbouring rods in opposite phase), so the panel reads as a braid.  Every rod starts and ends
    INSIDE the framing timber: `embed` = (into the timber at s<0, at s>W, below z0, above z1).  A thin
    daub backing sheet sits behind the weave, so nothing is see-through.
    pathf(s) -> (xy, outward normal) along the panel line, s in [0, W]."""
    rng = np.random.RandomState(seed)
    e0, e1, ez0, ez1 = embed
    pt_mid, nn_mid = pathf(np.array([W / 2]))
    outward3 = np.array([nn_mid[0, 0], nn_mid[0, 1], 0.0])
    st = W * (np.arange(n_stakes) + 1) / (n_stakes + 1) + rng.uniform(-0.006, 0.006, n_stakes)
    srk = rng.uniform(*stake_r, n_stakes)
    A = float(srk.max()) + rod_r[1] + 0.003                        # weave half-swing: rods clear the stakes
    D = float(np.mean(np.diff(st))) if n_stakes > 1 else W / 2
    zb, zt = z0 - ez0, z1 + ez1
    for k in range(n_stakes):
        zz = np.linspace(zb, zt, 24)
        pt, nn = pathf(np.full(len(zz), st[k]))
        path = np.c_[pt, zz]
        rad = srk[k] * (1 + 0.06 * n2(zz * 4.0, np.full(len(zz), st[k] * 9), seed + k))
        V, F, uv = open_tube(path, rad, STAKE_ARC, outward3, (0, 0, 1))
        stakes_acc.add(V, F, "M_wattle", uv, True)
    cos_t = 1.0 / math.sqrt(1.0 + slant * slant)
    s_lo, s_hi = -e0, W + e1
    c_min = zb - max(slant * s_lo, slant * s_hi)
    c_max = zt - min(slant * s_lo, slant * s_hi)
    c = c_min - 0.01
    r_prev = None
    i = 0
    n_r = 0
    while c < c_max + 0.01:
        r_i = rng.uniform(*rod_r)
        if r_prev is not None:
            c += (r_prev + r_i + rng.uniform(*gap)) / cos_t
        r_prev = r_i
        ss = np.unique(np.concatenate([np.linspace(s_lo, s_hi, 14), (st[:, None] + [-0.012, 0.0, 0.012]).ravel()]))
        zz = c + slant * ss + 0.002 * n2(ss * 6.0, np.full(len(ss), c * 13.0), seed + 77)
        ok = (zz >= zb) & (zz <= zt)
        if ok.sum() >= 2:
            idx = np.where(ok)[0]
            i0, i1 = idx[0], idx[-1]
            # extend the clipped run exactly to the band edges (ends buried in the rail / lintel)
            sa = ss[i0]
            sb = ss[i1]
            if i0 > 0:
                zlim0 = zb if slant > 0 else zt
                sa = ss[i0 - 1] + ((zlim0 - zz[i0 - 1]) / (zz[i0] - zz[i0 - 1])) * (ss[i0] - ss[i0 - 1])
            if i1 < len(ss) - 1:
                zlim = zt if slant > 0 else zb
                sb = ss[i1] + ((zlim - zz[i1]) / (zz[i1 + 1] - zz[i1])) * (ss[i1 + 1] - ss[i1])
            s_run = np.unique(np.concatenate([[sa], ss[i0:i1 + 1], [sb]]))
            if len(s_run) >= 3 and s_run[-1] - s_run[0] > 0.02:
                z_run = c + slant * s_run + 0.002 * n2(s_run * 6.0, np.full(len(s_run), c * 13.0), seed + 77)
                sgn = 1.0 if i % 2 == 0 else -1.0
                off = sgn * A * np.cos(np.pi * (s_run - st[0]) / D)
                pt, nn = pathf(s_run)
                path = np.c_[pt + nn * off[:, None], z_run]
                rad = r_i * (1 + 0.06 * n2(s_run * 7.0, np.full(len(s_run), c * 5.0), seed + 91))
                arc = np.radians(np.linspace(-100.0, 100.0, 6))
                V, F, uv = open_tube(path, rad, arc, outward3, (0, 0, 1), oval=0.92)
                rods.add(V, F, "M_wattle", uv, True)
                n_r += 1
        i += 1
    # daub backing behind the weave (inner face of the panel): no see-through slots
    sb_ = np.linspace(s_lo, s_hi, 5)
    zb_ = np.linspace(zb, zt, max(4, int((zt - zb) / 0.15)))
    S, Z = np.meshgrid(sb_, zb_, indexing="ij")
    pt, nn = pathf(S.ravel())
    dpt = -(A + rod_r[1] + back_gap) + 0.004 * n2(S.ravel() * 8, Z.ravel() * 8, seed + 5)
    P = np.c_[pt + nn * dpt[:, None], Z.ravel()]
    Fq = grid_quads(len(sb_), len(zb_))
    q0 = P[Fq[0]]
    if float(np.dot(np.cross(q0[1] - q0[0], q0[3] - q0[0]), outward3)) < 0:
        Fq = Fq[:, ::-1]
    back_acc.add(P, Fq, "M_daub")
    return n_r


# ---------------------------------------------------------------------------------------------
# daub definitions
# ---------------------------------------------------------------------------------------------
def bay_s(i):
    a0 = POST_AZ[i]
    a1 = POST_AZ[i + 1]
    return a0 * R_WALL, a1 * R_WALL


DAUB_BAYS = {}   # bay index -> function(s, z) -> thickness above wattle centre (m), <=0 => none
DAUB_COVER = {}  # bay index -> field value above which the rods are buried in the daub coat
DAUB_HIDE = {}   # bay index -> hide(s, z) for the rods (overrides DAUB_COVER)


def CLUMP_BAYS():
    """bays with exposed wattle (clinging daub clumps wrap their rods)."""
    return sorted({len(POST_AZ) - 2} | {p[0] for p in DAUB_PATCHES})


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
    """eroded lower edge of the big bay left of the door (director r4 #5a): the broken edge runs post to
    post at z 0.65-0.95 (ragged +-12 cm at a 5-15 cm wavelength) with 2-3 deeper bites, exposing the
    bottom wattle across the whole bay (ref2) -- no arch, the coat never reaches the plinth."""
    if "door" not in _EDGE_CURVE:
        _EDGE_CURVE["door"] = _knot_curve(9011, 17.5, 22.5, 0.32, 0.07)
        sb0, sb1 = bay_s(len(POST_AZ) - 2)
        rs = np.random.RandomState(9013)
        nb = 3
        cs_ = sb0 + (sb1 - sb0) * (np.arange(nb) + 0.5 + rs.uniform(-0.3, 0.3, nb)) / nb
        _EDGE_CURVE["door_bites"] = [(c_, rs.uniform(0.025, 0.05), rs.uniform(0.04, 0.08), rs.uniform(0.08, 0.13))
                                     for c_ in cs_]
    fs, fv = _EDGE_CURVE["door"]
    s = np.asarray(s, float)
    e = (0.79 + np.interp(s, fs, fv) + 0.05 * n2(s * 8.0, 1.7, 902)
         + 0.035 * n2(s * 15.0, 3.1, 903) + 0.012 * n2(s * 37.0, 5.3, 904))
    for (c_, wl_, wr_, d_) in _EDGE_CURVE["door_bites"]:          # asymmetric bites (steep one side)
        w_ = np.where(s < c_, wl_, wr_)
        e = e + d_ * np.exp(-np.abs((s - c_) / w_) ** 1.5) * (1 + 0.3 * n2(s * 30.0, c_, 905))
    return np.clip(e, 0.62, 1.02)


DAUB_KEEP_UNDER = 0.07     # client r6: wattle is kept only in the exposed patches + ~7-10 cm under their edges
ROD_ROW_P = 0.036          # nominal rod row pitch: patch margins break along the rows
# client correction r6: the exterior is MOSTLY INTACT DAUB; exposed wattle only in 4 small patches where
# the coat has fallen away (bay, kind, centre fraction along the bay, centre z, half width, half height, seed)
DAUB_PATCHES = [
    (2, "hole", 0.50, 1.30, 0.47, 0.30, 9310),      # +X side, mid height (side view)
    (5, "low", 0.45, 0.55, 0.50, 0.18, 9320),       # back right, broken out above the plinth (back view)
    (10, "hole", 0.42, 1.86, 0.42, 0.28, 9330),     # back left, under the eave (hero / aerial)
]


def stepped_curve(seed_, lo_s, hi_s, lo, hi, run=(0.06, 0.22), soft=0.008):
    """piecewise-constant offsets (in rod rows, lo..hi) with 6-22 cm runs, softened by ~1 cm: a daub
    margin that breaks along the rod rows, with no grid comb."""
    rs = np.random.RandomState(seed_)
    ks = [lo_s - 0.3]
    while ks[-1] < hi_s + 0.3:
        ks.append(ks[-1] + rs.uniform(*run))
    lv = rs.randint(lo, hi + 1, len(ks)) * ROD_ROW_P
    fine = np.linspace(ks[0], ks[-1], 1500)
    v = lv[np.clip(np.searchsorted(ks, fine) - 1, 0, len(ks) - 1)].astype(float)
    sig = soft / (fine[1] - fine[0])
    kk = np.arange(-int(3 * sig), int(3 * sig) + 1)
    ker = np.exp(-0.5 * (kk / sig) ** 2)
    ker /= ker.sum()
    v = np.convolve(np.pad(v, len(kk) // 2, mode="edge"), ker, mode="valid")
    return fine, v


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


def daub_hole(c_s, c_z, h_s, h_z, seed, floor=None):
    """field of one exposed-wattle patch: NEGATIVE inside the hole (~ -distance to its broken margin),
    positive in the intact coat.  The outline is a FRACTURE polygon (9-14 straight-ish breaks meeting
    at sharp corners, 2-3 deep re-entrant notches where a chunk fell), never a rounded blob; its top and
    bottom margins are shifted in 6-22 cm runs by whole rod rows (the coat breaks along the rows); fine
    ragged noise.
    floor(s): a "low" patch is open down to the stone tops (the coat broken away above the plinth)."""
    st_top = stepped_curve(seed + 1, c_s - h_s, c_s + h_s, 0, 1)
    st_bot = stepped_curve(seed + 2, c_s - h_s, c_s + h_s, 0, 1)
    rs = np.random.RandomState(seed + 3)
    nk = rs.randint(9, 15)
    th = np.sort(rs.uniform(0, 2 * np.pi, nk) * 0.0 + (np.arange(nk) + rs.uniform(-0.3, 0.3, nk)) * 2 * np.pi / nk)
    th = th + rs.uniform(0, 2 * np.pi)
    rr = rs.uniform(0.72, 1.12, nk)
    notch = rs.choice(nk, rs.randint(2, 4), replace=False)
    rr[notch] *= rs.uniform(0.55, 0.75, len(notch))
    P = np.stack([c_s + h_s * rr * np.cos(th), c_z + h_z * rr * np.sin(th)], -1)
    if floor is not None:                                      # open to the stones: drop the lower half
        P = P[P[:, 1] >= c_z - 0.2 * h_z]
        P = P[np.argsort(np.arctan2(P[:, 1] - c_z, P[:, 0] - c_s))]
        lo_s, hi_s = P[:, 0].min(), P[:, 0].max()
        P = np.vstack([[[hi_s + rs.uniform(-0.03, 0.03), c_z - 1.0]], P, [[lo_s + rs.uniform(-0.03, 0.03), c_z - 1.0]]])
        P = P[np.argsort(np.arctan2(P[:, 1] - c_z, P[:, 0] - c_s))]

    def f(s, z):
        s = np.asarray(s, float)
        z = np.asarray(z, float)
        ze = z - np.where(z > c_z, -np.interp(s, *st_top), np.interp(s, *st_bot))
        inside = poly_sdf(s, ze, P)
        if floor is not None:
            inside = np.minimum(inside, z - (floor(s) - 0.06))
        # (the clinging daub is modelled as torn sleeves wrapped round the exposed rods, see build_daub)
        return -inside + 0.005 * n2(s * 18.0, z * 18.0, seed + 6)
    return f


def low_margin(bay, seed, bite_amp=0.07, bite_max=0.10):
    """weathered lower margin of an intact bay: the coat stops 2-4 cm over the stone tops (the bottom rod
    shows), with occasional splash-eroded bites up to ~10 cm, rounding up into the posts."""
    bs0, bs1 = bay_s(bay)
    fs, fv = _knot_curve(seed, bs0 - 0.3, bs1 + 0.3, 0.17, bite_amp)

    def e(s):
        s = np.asarray(s, float)
        fl = wall_floor(s)
        bite = np.clip(np.interp(s, fs, fv) - 0.015, 0.0, bite_max)
        out = (fl + 0.028 + bite + 0.012 * n2(s * 9.0, 2.7, seed + 1) * (bite > 0.01) + 0.008 * n2(s * 23.0, 4.1, seed + 2))
        sp = np.minimum(s - bs0, bs1 - s)
        out = out + 0.05 * (1 - smoothstep(0.05, 0.24, sp)) ** 2
        return np.clip(out, fl + 0.02, 0.62)
    return e


def make_daub_fields():
    """every bay is daubed (client r6); field(s, z) ~ distance inside the intact coat (m), negative in the
    exposed patches.  Door bay: the ref2 eroded lower band (post to post, edge at z 0.62-1.0)."""
    nb = len(POST_AZ) - 1
    door_bay = nb - 1                      # between POST_AZ[-2] and POST_AZ[-1] (az -45..-21)

    def door_field(s, z):
        f = z - daub_edge_door_bay(s)
        # clinging scabs just below the break (within 10 cm of it: nothing below z 0.5)
        isl = np.clip(n2(s * 9.0, z * 9.0, 905) * 1.6 - 0.45, 0, 1) * 0.06
        f = np.where(f < 0, np.maximum(f, f + isl * (1 - smoothstep(0.0, 0.10, -f)) * 1.5), f)
        # a few pock holes where daub has fallen out higher up
        hole = np.clip(n2(s * 6.0, z * 6.0, 906) * 2.2 - 1.5, 0, 1)
        return np.minimum(f - hole * 0.6, 1.0)

    patches = {}
    for (bay, kind, cf, cz, hs, hz, seed) in DAUB_PATCHES:
        s0, s1 = bay_s(bay)
        patches.setdefault(bay, []).append(
            daub_hole(s0 + cf * (s1 - s0), cz, hs, hz, seed, floor=wall_floor if kind == "low" else None))
    for bay in range(nb):
        if bay == door_bay:
            DAUB_BAYS[bay] = door_field
            continue
        lm = low_margin(bay, 9500 + 13 * bay)
        holes = patches.get(bay, [])

        def field(s, z, _lm=lm, _holes=holes):
            f = np.asarray(z, float) - _lm(s)
            for h_ in _holes:
                f = np.minimum(f, h_(s, z))
            return np.minimum(f, 1.0)

        def hide(s, z, _lm=lm, _holes=holes):
            # rods buried in the intact coat are not modelled: kept ~7 cm under a patch margin, but only
            # ~3.5 cm (the bottom row) under the weathered foot
            hb = (np.asarray(z, float) - _lm(s)) > 0.035
            for h_ in _holes:
                hb &= h_(s, z) > DAUB_KEEP_UNDER
            return hb
        DAUB_BAYS[bay] = field
        DAUB_HIDE[bay] = hide
    for bay in DAUB_BAYS:
        DAUB_COVER[bay] = DAUB_KEEP_UNDER


def daub_hides(bay):
    f = DAUB_BAYS.get(bay)
    if f is None:
        return None
    if bay in DAUB_HIDE:
        return DAUB_HIDE[bay]

    thr = DAUB_COVER.get(bay, DAUB_KEEP_UNDER)

    def hide(s, z):
        # the daub stops >= 4 cm under the plate: the top rods stay, tucking under the plate
        return f(s, z) > thr
    return hide


def build_wattle(coll):
    make_daub_fields()
    rods = Acc("HUT_wattle_rods", 60)
    stakes = Acc("HUT_wattle_stakes", 60)
    backing = Acc("HUT_door_panel_backing", 40)
    pathf = arc_path(R_WALL)
    nb = len(POST_AZ) - 1
    nr = 0
    for bay in CLUMP_BAYS():
        ROD_STORE[1000 + bay * 17] = []
    for i in range(nb):
        s0, s1 = bay_s(i)
        z0 = max(0.22, float(wall_floor(np.linspace(s0, s1, 60)).min()) - 0.01)
        nr += weave_panel(rods, stakes, pathf, s0, s1, z0, WATTLE_TOP, 1000 + i * 17, hide=daub_hides(i),
                          trim=(0.075, 0.075), floor=wall_floor)
    # door side panels (front plane, jamb face -> door post face) and cheek panels (door post -> wall
    # post): twisted-rope weave, every rod end buried in the timber (director r3 #2)
    yc = FRONT_Y + 0.11
    for side in (-1, 1):
        x0, x1 = 0.70, 0.90
        f = line_path((side * x0, yc), (side * x1, yc), (0, -1))
        nr += rope_panel(rods, stakes, backing, f, x1 - x0, 0.405, HEAD_Z, 3000 + side, slant=0.85 * side,
                         embed=(0.035, 0.035, 0.03, 0.03), rod_r=(0.012, 0.015), gap=(0.002, 0.005))
        pa = np.array([side * 1.02, FRONT_Y + 0.17])
        wp = az_pt(WALL_POST_AZ_DOOR * side, R_WALL)[:2]
        L = float(np.linalg.norm(wp - pa))
        d = (wp - pa) / L
        nout = np.array([d[1], -d[0]])
        if nout[0] * side < 0:
            nout = -nout
        sa, sb = 0.085, L - 0.095
        f2 = line_path(pa + d * sa, wp, nout)
        nr += rope_panel(rods, stakes, backing, f2, sb - sa, 0.405, HEAD_Z, 3100 + side, slant=-0.6 * side,
                         embed=(0.05, 0.05, 0.03, 0.03), rod_r=(0.012, 0.015), gap=(0.002, 0.005))
    log("rods:", nr)
    rods.build(coll)
    stakes.build(coll)
    backing.build(coll)


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
    """front daub coat on every bay (client r6): 2.5-4 cm bulges (0.4-0.8 m), hand-applied dabs, a sag
    belly, palm dents, 2-4 shrinkage cracks per bay, ridging over the rods only where the coat thins at
    a patch margin, chipped edges against the posts, a splash-eroded foot, thick broken margins round
    the exposed patches, torn clumps wrapped round the exposed rods. Every boundary tucks behind the
    wattle / into the posts / into the plate, so no clean cut edge is exposed."""
    acc = Acc("HUT_daub", 70)
    h = 0.0075                     # fine grid: patch margins, cracks, the weathered foot
    H_S, H_Z = 0.016, 0.013        # intact coat away from them (hand-applied dabs and bulges)
    H_CR = 0.0105                  # crack boxes and the weathered foot
    n_cr = 0
    for bay, field in DAUB_BAYS.items():
        rng = np.random.RandomState(4400 + bay)
        sb0, sb1 = bay_s(bay)
        s0, s1 = sb0 + 0.04, sb1 - 0.04
        zlo, zhi = 0.30, PLATE_BOT + 0.012           # client r6: the intact coat runs up INTO the plate (no gap)
        # crop to where the daub exists
        Sc, Zc = np.meshgrid(np.linspace(s0, s1, 120), np.linspace(zlo, zhi, 160), indexing="ij")
        fc = field(Sc, Zc)
        live = fc > -0.07
        ss_live = Sc[live]
        zz_live = Zc[live]
        cs0, cs1 = max(s0, ss_live.min() - 0.03), min(s1, ss_live.max() + 0.03)
        cz0, cz1 = max(zlo, zz_live.min() - 0.03), min(zhi, zz_live.max() + 0.03)
        # ---- shrinkage cracks first (their boxes are refined): random-walk polylines in intact coat
        cracks = []
        ncr = rng.randint(2, 5)
        tries = 0
        while len(cracks) < ncr and tries < 200:
            tries += 1
            ps = rng.uniform(cs0 + 0.12, cs1 - 0.12)
            pz = rng.uniform(cz0 + 0.18, cz1 - 0.12)
            if field(np.array([ps]), np.array([pz]))[0] < 0.15:
                continue
            Lc = rng.uniform(0.12, 0.35)
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
            cracks.append((pts, rng.uniform(0.004, 0.008), rng.uniform(0.008, 0.014)))
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
        # ---- graded tensor grid: fine (7.5 mm) rows / columns through the patch margins, the cracks and
        # the weathered foot; 1.3-1.6 cm over the intact coat
        fine_s, fine_z = [], [(zlo, float(wall_floor(np.linspace(sb0, sb1, 40)).max()) + 0.22, H_CR)]
        edge_m = (fc > -0.06) & (fc < 0.12)
        if edge_m.any():
            # rows / columns that cross a patch margin (not the lower margin, which is z-refined above)
            em = edge_m & (Zc > fine_z[0][1] - 0.05)
            if em.any():
                cols = np.where(em.any(axis=1))[0]
                rows = np.where(em.any(axis=0))[0]
                for (a_, b_) in _runs(np.isin(np.arange(Sc.shape[0]), cols)):
                    fine_s.append((Sc[a_, 0] - 0.03, Sc[b_ - 1, 0] + 0.03, h))
                for (a_, b_) in _runs(np.isin(np.arange(Zc.shape[1]), rows)):
                    fine_z.append((Zc[0, a_] - 0.03, Zc[0, b_ - 1] + 0.03, h))
        for (pts, wd, dp) in cracks:
            pa = np.asarray(pts)
            fine_s.append((pa[:, 0].min() - 0.03, pa[:, 0].max() + 0.03, h))
            fine_z.append((pa[:, 1].min() - 0.03, pa[:, 1].max() + 0.03, h))

        def graded(lo, hi, hc, rngs):
            xs = [lo]
            while xs[-1] < hi - 1e-6:
                x = xs[-1]
                hh = min([hr for (a, b, hr) in rngs if a <= x + 0.5 * hr and x - 0.5 * hr <= b] + [hc])
                xs.append(min(hi, x + hh))
            if len(xs) > 2 and xs[-1] - xs[-2] < 0.3 * h:
                xs.pop(-2)
            return np.array(xs)
        su = graded(cs0, cs1, H_S, fine_s)
        zt_ = min(cz1, EAVE_SHADOW_Z - 0.06)
        zr = graded(cz0, zt_, H_Z, fine_z)
        if cz1 > zt_ + 0.005:
            zr = np.concatenate([zr, np.linspace(zr[-1], cz1, int((cz1 - zr[-1]) / 0.02) + 2)[1:]])
        nu, nv = len(su), len(zr)
        log(f"  daub bay {bay}: grid {nu} x {nv}, cracks {len(cracks)}")
        S, Z = np.meshgrid(su, zr, indexing="ij")
        dsu = np.gradient(su) if nu > 1 else np.full(nu, H_S)
        dzr = np.gradient(zr) if nv > 1 else np.full(nv, H_Z)
        HL = np.maximum(dsu[:, None], dzr[None, :])         # local grid spacing per vertex
        crack_d = np.zeros(S.shape)
        for (pts, wd, dp) in cracks:
            dist, cs_, cz_, ct = _seg_dist(S, Z, pts)
            prof = np.sin(np.pi * np.clip(ct, 0, 1)) ** 0.5
            ww = wd * 0.5 * (0.3 + 0.7 * prof)
            core = dist < 0.55 * HL
            band = (dist >= 0.55 * HL) & (dist < 1.8 * HL)
            # core vertices snap onto the crack centre line (groove bottom)
            S = np.where(core, cs_, S)
            Z = np.where(core, cz_, Z)
            # neighbours are pulled in to the crack lip (narrow 0.5-1 cm crack)
            with np.errstate(invalid="ignore", divide="ignore"):
                ux = (S - cs_) / np.maximum(dist, 1e-9)
                uz = (Z - cz_) / np.maximum(dist, 1e-9)
            dn = ww + (dist - 0.55 * HL) * (1.8 * HL - ww) / (1.25 * HL)
            S = np.where(band, cs_ + ux * dn, S)
            Z = np.where(band, cz_ + uz * dn, Z)
            crack_d = np.minimum(crack_d, np.where(core, -dp * (0.2 + 0.8 * prof), 0.0))
            n_cr += 1
        f = field(S, Z)
        # director r4 #5c: the sheet's cut boundary (where it is dropped behind the rods) is snapped onto
        # the smooth field contour -- no grid stair-steps along any daub margin
        F_all = grid_quads(nu, nv)
        sp0 = np.minimum(S - sb0, sb1 - S)
        hv0 = ((f < -0.03) | (sp0 < 0.085)).ravel()
        F_keep = F_all[~hv0[F_all].all(axis=1)]
        used = np.zeros(S.size, bool)
        used[F_keep.ravel()] = True
        mv = (used & (f.ravel() < -0.03) & (sp0.ravel() >= 0.085)).reshape(S.shape)
        if mv.any():
            ps, pz = S[mv].copy(), Z[mv].copy()
            hm = HL[mv]
            for _ in range(4):
                e_ = 1e-3
                f0 = field(ps, pz) + 0.03
                gs = (field(ps + e_, pz) - field(ps - e_, pz)) / (2 * e_)
                gz = (field(ps, pz + e_) - field(ps, pz - e_)) / (2 * e_)
                g2 = np.maximum(gs * gs + gz * gz, 0.05)
                ds_ = np.clip(-f0 * gs / g2, -hm, hm)
                dz_ = np.clip(-f0 * gz / g2, -hm, hm)
                ps, pz = ps + ds_, pz + dz_
            S = S.copy()
            Z = Z.copy()
            S[mv], Z[mv] = ps, pz
            f = field(S, Z)
        P3 = np.stack([S * 1.7, Z * 1.7, np.full(S.shape, bay * 1.31)], -1)
        # ---- big soft bulges (2.5-4 cm at 0.4-0.8 m)
        bul = fbm(P3, 2, gain=0.45)
        bul = (bul - bul.mean()) / max(bul.std(), 1e-6)
        bulge = 0.011 * np.clip(bul, -2.2, 2.2) + 0.004 * n2(S * 7.0, Z * 7.0, 4490 + bay)
        # ---- faint horizontal ridging over the rods beneath (6-8 cm pitch), strongest where thin
        # ridging only in small patches (<= 0.3 m) where the coat is thin, pitch 5-7.5 cm and amplitude varying
        # ridges follow the horizontal rod rows only: pitch 4.5-6.5 cm varying slowly ALONG the wall,
        # phase depending on s only, 3-6 mm, in horizontally elongated patches
        drift = 0.006 * n2(S * 1.1, np.full(S.shape, 3.3), 4500 + bay)
        pitch = 0.05 + 0.012 * (bay % 3) / 2.0           # one pitch per bay (4.5-6.5 cm): rows stay level
        rid = np.cos(2 * np.pi * (Z + drift) / pitch)
        thin = 1 - smoothstep(-0.9, 0.4, bul)
        patchy = np.clip(n2(S * 2.5, Z * 7.0, 4511 + bay) * 2.4 - 0.5, 0, 1)
        r_amp = 0.0018 + 0.0022 * np.clip(n2(S * 2.0, Z * 5.0, 4512 + bay) + 0.5, 0, 1)
        ridge = r_amp * rid * (0.35 + 0.65 * thin) * patchy * (1 - smoothstep(0.05, 0.22, field(S, Z)))
        # ---- client r6: hand-applied dabs over the intact coat (handful pats 6-11 cm, 2-5 mm proud, a
        # slightly sharper lower lip where each was pushed upward)
        dabs = np.zeros(S.shape)
        for _ in range(int((cs1 - cs0) * (cz1 - cz0) * 30)):
            c_s = rng.uniform(cs0, cs1)
            c_z = rng.uniform(cz0, cz1)
            R_ = rng.uniform(0.06, 0.11)
            ds_ = (S - c_s) / (R_ * rng.uniform(0.9, 1.4))
            dz_ = (Z - c_z) / R_
            r2 = ds_ ** 2 + dz_ ** 2
            m = r2 < 4.0
            if not m.any():
                continue
            lip = np.where(dz_ < 0, np.exp(-r2 * 2.2), np.exp(-r2 * 1.1))
            dabs += rng.uniform(0.002, 0.005) * lip * m
        # ---- palm-press dents (director r3 #5c): round 7-12 cm dents 0.8-1.8 cm deep with a slight
        # squeezed-up rim; they break the long undulations (no strokes, no folds)
        smear = np.zeros(S.shape)
        area = (cs1 - cs0) * (cz1 - cz0)
        for _ in range(int(area * 7)):
            c_s = rng.uniform(cs0, cs1)
            c_z = rng.uniform(cz0, cz1)
            R_ = rng.uniform(0.05, 0.08)
            el = rng.uniform(0.8, 1.25)
            r2 = ((S - c_s) / (R_ * el)) ** 2 + ((Z - c_z) * el / R_) ** 2
            m = r2 < 6.0
            if not m.any():
                continue
            A_ = rng.uniform(0.006, 0.012)
            rr_ = np.sqrt(r2)
            smear += A_ * (-np.exp(-r2 * 1.3) + 0.12 * np.exp(-((rr_ - 1.1) / 0.35) ** 2)) * m
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
        T_full = 0.088 + bulge * (0.3 + 0.7 * smoothstep(0.07, 0.25, sp)) + ridge * (1 - nearp) + smear + fine + dabs
        T_full = T_full - 0.024 * chip - 0.008 * nearp
        # thickness envelope: tucks behind the rods where the field ends (eroded / patch edges)
        # ---- client r6: slight sag (a soft belly where the wet coat slumped, 0.5-1.0 m up) and a
        # weathered foot (splash-eroded: thinner, pitted, rougher over the bottom ~25 cm)
        z_sag = 0.62 + 0.3 * ((bay * 0.618) % 1.0)
        sag = (0.010 + 0.005 * n2(S * 1.3, np.full(S.shape, 0.5), 4540 + bay)) * np.exp(-((Z - z_sag) / 0.28) ** 2)
        sag = sag * (1 - smoothstep(0.42, 0.62, np.abs(Z - z_sag) / 0.6))
        foot = 1 - smoothstep(0.0, 0.26, Z - wall_floor(S))
        foot_n = np.clip(n2(S * 14.0, Z * 30.0, 4541 + bay) * 1.4 + 0.3, 0, 1)
        T_full = (T_full + sag - foot * (0.010 + 0.012 * foot_n)
                  + foot * (0.0045 * n2(S * 22.0, Z * 45.0, 4542 + bay) - 0.004 * np.clip(n2(S * 35, Z * 55, 4543 + bay) * 2 - 0.6, 0, 1)))
        edge = smoothstep(-0.004, 0.045, f)
        pit = 0.01 * np.clip(n2(S * 25, Z * 25, bay + 77), 0, 1) * (1 - smoothstep(0.04, 0.16, f))
        T = -0.036 + (T_full + 0.036 - pit) * edge + crack_d * edge
        # tuck into the posts at the very ends of the sheet, and back under the plate at the top
        T = T - 0.04 * (1 - smoothstep(0.045, 0.095, sp)) * edge
        T = T - 0.032 * smoothstep(zhi - 0.09, zhi, Z)
        a = S / R_WALL
        rad = R_WALL + T
        P = np.stack([np.sin(a) * rad, -np.cos(a) * rad, Z], -1)
        Vv = P.reshape(-1, 3)
        # drop the parts never seen: sheet tucked behind the rods below the break, and inside the posts
        acc.add(Vv, F_keep, "M_daub")
        # ---- detached clumps (director r4 #2e): 2-3 flattened, torn daub blobs 4-8 cm long WRAPPED round
        # real rods just below the break (a sleeve on the rod path, thickest on the top / front, ragged
        # ends), never a free-floating lump
        if 1000 + bay * 17 in ROD_STORE:
            store = ROD_STORE.get(1000 + bay * 17, [])
            cand = []
            for (ss_r, pth, rad_r) in store:
                for ic in range(3, len(ss_r) - 4, 3):
                    if not (s0 + 0.15 < ss_r[ic] < s1 - 0.15):
                        continue
                    if pth[ic, 2] < float(wall_floor(np.array([ss_r[ic]]))[0]) + 0.12:
                        continue
                    fc_ = float(field(np.array([ss_r[ic]]), np.array([pth[ic, 2]]))[0])
                    if -0.22 < fc_ < -0.05:
                        cand.append((ss_r, pth, rad_r, ic))
            picks = []
            for _ in range(60):
                if len(picks) >= (3 if bay == len(POST_AZ) - 2 else 2) or not cand:
                    break
                c_ = cand[rng.randint(len(cand))]
                if all(abs(c_[0][c_[3]] - q[0][q[3]]) > 0.25 for q in picks):
                    picks.append(c_)
            for (ss_r, pth, rad_r, ic) in picks:
                Lc = rng.uniform(0.04, 0.08)
                s_c = ss_r[ic]
                tt = np.linspace(-0.5, 0.5, 9)
                sq = s_c + tt * Lc
                C = np.stack([np.interp(sq, ss_r, pth[:, k]) for k in range(3)], -1)
                rr_c = np.interp(sq, ss_r, rad_r)
                nside = 12
                ang = 2 * np.pi * np.arange(nside) / nside
                Tn, Nn, Bn = frames(C, (0, 0, 1))
                cut = 0.5 - rng.uniform(0.0, 0.22, nside)                 # ragged torn ends per side
                cut = np.minimum(cut, np.roll(cut, 1) * 0.5 + cut * 0.5)
                T0 = rng.uniform(0.010, 0.016)
                thick = np.zeros((len(tt), nside))
                for k_ in range(nside):
                    w_ = np.clip(1 - (np.abs(tt) / max(cut[k_], 0.05)) ** 2, 0, 1) ** 0.6
                    bias = 1.0 + 0.6 * max(0.0, math.cos(ang[k_])) + 0.4 * max(0.0, math.sin(ang[k_]))
                    thick[:, k_] = T0 * w_ * bias * (0.7 + 0.3 * rng.rand())
                rr2 = rr_c[:, None] + thick + 0.001
                # flatten: squash the sleeve toward the wall plane (pressed blob, not a bead)
                Vb = (C[:, None, :] + (np.cos(ang)[None, :, None] * rr2[..., None]) * Nn[:, None, :]
                      + (np.sin(ang)[None, :, None] * rr2[..., None] * 0.8) * Bn[:, None, :])
                Vb = Vb.reshape(-1, 3)
                i_ = np.arange(len(tt) - 1)[:, None]
                j_ = np.arange(nside)[None, :]
                j1_ = (j_ + 1) % nside
                Fb = [np.stack([i_ * nside + j_, i_ * nside + j1_, (i_ + 1) * nside + j1_, (i_ + 1) * nside + j_], -1).reshape(-1, 4)]
                Fb.append(np.arange(nside)[::-1][None, :])
                Fb.append(((len(tt) - 1) * nside + np.arange(nside))[None, :])
                acc.add(Vb, Fb, "M_daub", wear=0.8)
    log("daub cracks:", n_cr)
    acc.build(coll)


INNER_SKIN_D = 0.17            # inner daub skin face, behind the wattle centre line (director r2: >= 0.15)


def build_inner_skin(coll):
    """inner daub skin 17 cm behind the rod centre line: the dark back of the open weave (gaps read dark,
    rod backs are never visible) and the inner wall face seen through the doorway.  A single lumpy sheet
    (both faces are seen: the outer through the weave gaps, the inner through the door) with a folded
    top lip under the plate, continuous all the way round from door cheek to door cheek."""
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
    # director r4 #3a: the skin is kept over the FULL circumference (also behind the daubed bays, whose
    # posts and rods are open-backed): no ray through the doorway can leave the hut through the wall
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



def build_eave_closure(coll, r_off=0.075, door_half=math.radians(19.0), n_az=240):
    """daub eave closure (director r4 #3b): a low band on the inner half of the wall plate, from the plate
    top up to the underside of the roof deck, between the rafters.  It closes the eave gap from the
    inside, so no ray through the doorway can leave the hut between the plate and the roof (it reads
    from outside, deep in the eave shadow, as the daubed wall top between the rafter feet)."""
    acc = Acc("HUT_eave_closure", 30, cull=None)
    r_b = R_WALL - r_off
    az = np.linspace(door_half, 2 * math.pi - door_half, n_az)
    ss = np.linspace(0.0, 2.0, 400)
    top = np.zeros(n_az)
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bv = []
    for nm in ("HUT_roof_shingles", "HUT_roof_starter"):
        me = bpy.data.objects[nm].data
        bv.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p_.vertices[:] for p_ in me.polygons]))
    cs_p, sn_p = math.cos(PITCH), math.sin(PITCH)
    for i, a in enumerate(az):
        P = surf(np.full_like(ss, float(az2th(a))), ss)
        rr = np.hypot(P[:, 0], P[:, 1])
        z_s = float(np.interp(-r_b, -rr, P[:, 2]))
        nrm_ = Vector((math.sin(a) * sn_p, -math.cos(a) * sn_p, cs_p))
        # top edge buried in the shingle stack (seals the eave gap), lowered wherever a slipped or
        # missing shingle would leave it exposed
        for dz in (0.05, 0.03, 0.012, -0.006):
            o = Vector((math.sin(a) * r_b, -math.cos(a) * r_b, z_s + dz)) + nrm_ * 0.002
            if any(b_.ray_cast(o, nrm_, 0.4)[0] is not None for b_ in bv):
                break
        top[i] = z_s + dz
    bot = np.full(n_az, PLATE_TOP - 0.03)
    rng = np.random.RandomState(2601)
    zz = np.stack([bot, (bot + top) / 2 + 0.01 * rng.uniform(-1, 1, n_az), top], 1)
    rad = r_b + np.stack([np.zeros(n_az), 0.008 * n2(az * 6.0, np.full(n_az, 0.3), 2602), np.zeros(n_az)], 1)
    P = np.stack([np.sin(az)[:, None] * rad, -np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(n_az, 3)
    q = P[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0])) > 0:
        F = F[:, ::-1]                      # normals face the hut interior (seen through the door)
    acc.add(P, F, "M_daub")
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

    def place(acc_, th_c, s_b, W, L, var, phi, lift, curl, base_fn, ys=None, closed=True, wear_=None):
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
        acc_.add(V, F, "M_roof_shingle", uv, smooth=True, wear=wear_)

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
                place(acc, tha, sb, wa, L, var, phi - 0.02, lift, curl, base_fn, closed=closed, wear_=0.85)
                place(acc, thb, sb + 0.01, wb, L - 0.01, var, phi + 0.025, lift + 0.004, curl, base_fn, closed=closed,
                      wear_=0.9)
                n_total += 2
                continue
            wr = 0.9 if r["slip"] > 0 else (0.55 + 0.2 * (k < 2) if k < 4 else None)
            place(acc, thc, sb, Wi, L, var, phi, lift, curl, base_fn, closed=closed, wear_=wr)
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
# plinth, door step (producer note 10: no ground dressing)
# =============================================================================================
R_PL_FACE = 3.76            # plinth outer face line (rough wall line, +-4 cm)
PLINTH_TOP = 0.33
PAD_TOP = 0.225             # door-post pad stones: bearing bed height (~0.17 visible)
STEP_C = (0.04, FRONT_Y - 0.58)       # step stone centre (x, y)
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
                face_fr=(0.0, 0.34, 0.6, 0.8, 0.93), sm_scale=1.0, n_facet=0, frac_k=(0.004, 0.01), chips=0,
                chip_w=(0.04, 0.08), chip_d=(0.012, 0.025), side_slope=0.0, Rf=None, spalls=0,
                spall_r=(0.03, 0.06), spall_d=(0.002, 0.005), rr_var=0.45):
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
        w = w + noise * 0.35 * vnoise(np.stack([u * freq * 4.1, v * freq * 4.1, np.full(np.shape(u), off[2] + 3)], -1))
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
            plane = float(yf0(np.array([uc]), np.array([vc]))[0]) - ds - sl_ * a1 * 0.1
            w = w - win * np.maximum(0.0, w - plane)
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


FLAGS = []          # the built-in door step (dict)


def earth_base(X, Y):
    """producer note 10: no apron / mound / path -- the terrain is built separately in Unreal; the
    building stands on a flat Z = 0 datum and its own footing carries a <= 4 cm buried skirt."""
    X = np.asarray(X, float)
    return np.zeros(np.shape(X))


GROUND_SKIRT = 0.04          # buried skirt depth below Z = 0 kept on the footing (producer note 10: <= 5 cm)


def ground_z(X, Y):
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    r = np.hypot(X, Y)
    return np.where(r < R_FLOOR_EDGE, floor_z(X, Y), earth_base(X, Y))


def cull_below_ground(V):
    """vertex is never visible: deeper than the buried skirt outside (flat Z = 0 datum), or more than
    1.2 cm under the interior earth floor."""
    hid = np.zeros(len(V), bool)
    low = V[:, 2] < 0.26
    if low.any():
        X, Y = V[low, 0], V[low, 1]
        inside = np.hypot(X, Y) < R_FLOOR_EDGE
        g = np.where(inside, floor_z(X, Y) - 0.012, earth_base(X, Y) - GROUND_SKIRT)
        hid[low] = V[low, 2] < g
    return hid


def plan_path():
    """the built-in door step only (producer note 10: no path flags / stepping stones)."""
    rng = np.random.RandomState(1414)
    FLAGS.append(dict(kind="step", c=(STEP_C[0], STEP_C[1]), rot=0.05, hu=0.62, hv=0.34, ext=0.7,
                      R=outline_radius(rng, "flag"), top=0.095, th=0.16, seed=77))


def build_step(coll):
    """the door step built into the entrance (kept per producer note 10): a flat slightly dished slab
    (1-1.5 cm arris, sloping sides, 1-2 edge chips) bedded to the skirt depth."""
    acc = Acc("HUT_step_stone", 30)
    for fl in FLAGS:
        rng = np.random.RandomState(fl["seed"])
        if fl["kind"] == "step":
            V, F = shell_stone(fl["hu"], fl["hv"], rng, "flag", fl["th"], rr=(0.006, 0.018), rr_var=0.8, dome=0.0,
                               tilt=0.01, n_frac=0, frac_depth=(0.008, 0.015), frac_k=(0.003, 0.005), n_th=128,
                               noise=0.012, freq=4.5, side_bulge=0.0, side_slope=0.12, thick_var=0.12,
                               dish=0.009, chips=3, chip_w=(0.04, 0.08), chip_d=(0.012, 0.022), Rf=fl["R"],
                               spalls=3, face_fr=tuple(np.linspace(0.0, 0.95, 15)))
            wear = 0.8
        V[:, 2] += fl["top"] - V[0, 2]
        P, _ = map_uvw(V, "plan")
        acc.add(xf(P, rotz(fl["rot"]), (fl["c"][0], fl["c"][1], 0.0)), F, "M_stone", wear=wear)
    acc.build(coll)


PL_TOP = {}         # stone-top sampler along the wall line (filled by build_plinth)


def stone_top(x, y, default=PLINTH_TOP):
    """height of the plinth stone surface under (x, y) (vertical ray-cast); default where no stone."""
    from mathutils import Vector
    bvh = PL_TOP.get("bvh")
    out = []
    for xx, yy in zip(np.atleast_1d(x), np.atleast_1d(y)):
        hit = None if bvh is None else bvh.ray_cast(Vector((float(xx), float(yy), 1.5)), Vector((0, 0, -1.0)), 2.0)
        out.append(default if hit is None or hit[0] is None else float(hit[0][2]))
    return np.array(out)


def wall_floor(s):
    """plinth stone top under the wattle line at arc length s (R_WALL), for weave bedding."""
    return np.interp(np.mod(np.asarray(s, float) / R_WALL, 2 * np.pi), PL_TOP["az"], PL_TOP["z"])


def plinth_stone(rng, L, z_bot, z_top, depth, fracture, kind="block", upper=False):
    """one plinth stone (local frame, see plinth_kind_stone()); bottom at z_bot, high point ~z_top."""
    c = max(0.05, (z_top - z_bot) / 2)
    b = depth / 2
    V, F = plinth_kind_stone(kind, (L / 2, b, c), rng, fracture=fracture,
                             n_front=72 if not upper else 56, n_up=30 if not upper else 24)
    V[:, 2] += z_bot - V[:, 2].min()
    return V, F


def build_plinth(coll):
    """dry-stone plinth (director r3 #3a): ONE course of rounded / sub-angular field boulders, each a
    superellipsoid body with a crowned top (4-8 cm, high point off-centre), a front bulging 3-6 cm,
    sloping sides and crisp fracture facets on ~35 % of stones only; crown heights alternate so that
    neighbours differ by >= 4 cm (visible 0.18-0.34 m), ~20 % two-high with a smaller upper stone;
    neighbours overlap at their rounded ends so face joints close to <= 3 cm.  Only what is outside
    the wattle line and above ground is modelled.  Flat wedge chinking (pooled) is ray-tested into
    the open V-joints."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    def cull_pl(V):
        return cull_below_ground(V) | (np.hypot(V[:, 0], V[:, 1]) < R_WALL - 0.035)
    acc = Acc("HUT_plinth_stones", 30, cull=cull_pl)
    rng = np.random.RandomState(9191)
    r_c = 3.60
    a_start = math.asin(1.20 / 3.78)          # runs on under the cheek panels to the door-post pads
    a_end = 2 * math.pi - a_start
    post_az = list(POST_AZ)
    a = a_start
    stones = []
    # director r4 #2b: shape mix ~30 % sub-rounded boulders, ~40 % flat slabs, the rest blocky, never two
    # neighbours of the same kind (lengths by kind: slabs long and low, h:L <= 0.45)
    kinds = []
    len_rng = {"slab": (0.62, 0.84), "block": (0.42, 0.62), "boulder": (0.42, 0.58)}
    while a < a_end - 0.02:
        opts = [k_ for k_ in ("slab", "block", "boulder") if not kinds or k_ != kinds[-1]]
        w = np.array([{"slab": 0.46, "block": 0.30, "boulder": 0.24}[k_] for k_ in opts])
        kind = opts[rng.choice(len(opts), p=w / w.sum())]
        L = rng.uniform(*len_rng[kind])
        if a + L / r_c > a_end:
            L = (a_end - a) * r_c
            if L < 0.25:
                stones[-1][1] += L * 0.6
                break
        stones.append([a + (L / 2) / r_c, L])
        kinds.append(kind)
        a += (L - rng.uniform(0.035, 0.06)) / r_c          # rounded ends overlap: tight joints
    n_two = n_fr = 0
    placed = []
    z_prev = None
    ground_face = 0.045
    vis_rng = {"slab": (0.17, 0.22), "block": (0.22, 0.30), "boulder": (0.27, 0.35)}
    n_kind = {"slab": 0, "block": 0, "boulder": 0}
    for i, (ac, L) in enumerate(stones):
        kind = kinds[i]
        n_kind[kind] += 1
        near_post = min(abs(np.angle(np.exp(1j * (ac - pa)))) for pa in post_az) * r_c < L / 2 + 0.02
        # visible heights by kind, neighbours >= 4 cm apart
        for _ in range(40):
            zt = ground_face + rng.uniform(*vis_rng[kind])
            if near_post:
                zt = max(zt, ground_face + 0.22)
            if z_prev is None or abs(zt - z_prev) >= 0.04:
                break
        z_prev = zt
        fr_ = rng.rand() < 0.62
        n_fr += fr_
        face = float(plinth_face_r(ac)) + rng.uniform(-0.015, 0.02)
        depth = face - (R_WALL - 0.10)
        R = frame_wall(ac) @ rotz(rng.uniform(-0.08, 0.08)) @ rotx(rng.uniform(-0.05, 0.03)) @ roty(rng.uniform(-0.05, 0.05))
        two = (not near_post) and kind != "slab" and L > 0.5 and rng.rand() < 0.22
        z_b = -0.06 if kind == "slab" else -0.11
        if not two:
            V, F = plinth_stone(rng, L, z_b, zt, depth, fr_, kind)
            Pw = xf(V, R)
            u = np.array([math.sin(ac), -math.cos(ac), 0.0])
            Pw += u * (face - float((Pw @ u).max()))
            acc.add(Pw, F, "M_stone", wear=rng.uniform(0.2, 0.5) + 0.3 * fr_)
            placed.append((ac, zt, L))
        else:
            n_two += 1
            lo_top = ground_face + rng.uniform(0.11, 0.15)
            V, F = plinth_stone(rng, L, -0.07, lo_top, depth, fr_, "slab")
            Pw = xf(V, R)
            u = np.array([math.sin(ac), -math.cos(ac), 0.0])
            Pw += u * (face - float((Pw @ u).max()))
            acc.add(Pw, F, "M_stone", wear=rng.uniform(0.2, 0.5))
            Lu = L * rng.uniform(0.55, 0.72)
            xo = rng.uniform(-0.15, 0.15) * L
            zu = max(zt, lo_top + 0.12)
            Vu, Fu = plinth_stone(rng, Lu, lo_top - 0.03, zu, depth - 0.05, rng.rand() < 0.6, kind, upper=True)
            acu = ac + xo / r_c
            Ru = frame_wall(acu) @ rotz(rng.uniform(-0.1, 0.1)) @ roty(rng.uniform(-0.06, 0.06))
            Pu = xf(Vu, Ru)
            uu = np.array([math.sin(acu), -math.cos(acu), 0.0])
            Pu += uu * (face - rng.uniform(0.025, 0.05) - float((Pu @ uu).max()))
            acc.add(Pu, Fu, "M_stone", wear=rng.uniform(0.3, 0.6))
            placed.append((ac, zu, L))
    log("plinth kinds:", n_kind)
    log("plinth stones:", len(stones), "two-high:", n_two, f"({100 * n_two / len(stones):.0f} %)",
        "fractured:", n_fr)
    stones_ob = acc.build(coll)
    me = stones_ob.data
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])
    PL_TOP["bvh"] = bvh
    az_s = np.linspace(0, 2 * np.pi, 1441)
    zs = []
    for az in az_s:
        best = None
        for rr_ in (R_WALL - 0.03, R_WALL + 0.03):
            hit = bvh.ray_cast(Vector((math.sin(az) * rr_, -math.cos(az) * rr_, 1.5)), Vector((0, 0, -1.0)), 2.0)
            if hit[0] is not None:
                best = hit[0][2] if best is None else max(best, hit[0][2])
        zs.append(PLINTH_TOP if best is None else best)
    PL_TOP["az"], PL_TOP["z"] = az_s, np.array(zs)

    # ---------------- chinking: pooled FLAT wedges, ray-tested into open joints
    def face_r(az, z):
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        o = u * 4.6 + np.array([0, 0, z])
        hit = bvh.ray_cast(Vector(o), Vector(-u), 2.0)
        if hit[0] is None:
            return None
        return 4.6 - hit[3]

    def make_chink(acc_, k):
        rs = np.random.RandomState(7300 + k)
        hx, hz = rs.uniform(0.03, 0.05), rs.uniform(0.008, 0.014)
        V, F = boulder((hx, 0.035, hz), rs, p_h=3.4, p_v=3.0, crown=0.0, bulge=0.0, n_frac=2, frac_k=0.002,
                       frac_cut=(0.08, 0.2), warp=0.12, amp=0.0015, freq=25.0, pit=0.0006, taper=0.05,
                       nu=14, nv=6)
        V[:, 2] *= 1 - 0.55 * np.clip(-V[:, 1] / 0.035, 0, 1)        # wedge: thins toward the back
        acc_.add(V, F, "M_rubble")

    n_ch = n_try = 0
    ch_rng = np.random.RandomState(9393)
    cands = []
    for i in range(len(placed) - 1):
        ac, zt, L = placed[i]
        ga = ac + (L / 2 - 0.02) / r_c
        zj = min(zt, placed[i + 1][1])
        for zc in (zj - 0.03, zj * 0.65, zj * 0.35):
            cands.append((ga + ch_rng.uniform(-0.003, 0.003), zc + ch_rng.uniform(-0.015, 0.015)))
    for (az, zc) in cands:
        n_try += 1
        rL = face_r(az - 0.05 / R_PL_FACE, zc)
        rR = face_r(az + 0.05 / R_PL_FACE, zc)
        rC = face_r(az, zc)
        if rL is None or rR is None:
            continue
        front = min(rL, rR) - 0.012 - ch_rng.uniform(0.0, 0.01)
        if rC is not None and rC > front - 0.012:
            continue                     # no open joint here (stones touch)
        k = ch_rng.randint(8)
        mesh = pool_mesh("chink", k, make_chink)
        R = frame_wall(az) @ roty(math.pi / 2 + ch_rng.uniform(-0.5, 0.5)) @ rotx(ch_rng.uniform(-0.15, 0.15))
        u = np.array([math.sin(az), -math.cos(az), 0.0])
        place_instance(mesh, "plinth_chink", R, u * (front - 0.03) + np.array([0, 0, zc]))
        n_ch += 1
    log("chinking:", n_ch, "of", n_try, "candidate joints")


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
    def cull_thr(V):
        # under the sill (the slabs run in beneath it): never visible (producer note 6)
        under_sill = (np.abs(V[:, 0]) < 0.88) & (V[:, 1] > FRONT_Y + 0.11 - 0.13 + 0.025) & (V[:, 2] < 0.10)
        return cull_below_ground(V) | under_sill
    thr = Acc("HUT_threshold", 30, cull=cull_thr)
    rng = np.random.RandomState(1212)
    yc = FRONT_Y + 0.11                       # frame centre plane
    POST_BASE = PAD_TOP
    RV = np.array([[0.0, 1, 0], [0, 0, 1], [1, 0, 0]])        # local X -> world Z (vertical member)
    for side in (-1, 1):
        x = side * 1.02
        # pad stone under each door post (director r4 #2a): low and wide (0.46 x 0.36 plan, ~0.18 visible),
        # irregular 6-9-corner plan, battered planar sides, 2-3 planar split faces, flat bed tilted 1-3 deg
        prs = np.random.RandomState(5150 + side)
        pc = np.array([side * 1.04, -3.61])
        g_pad = float(earth_base(pc[:1], pc[1:])[0])
        # stands on the flat Z = 0 datum (producer note 10): nearly upright sides, no flared foot
        V, F = pad_stone(prs, plan=(0.23, 0.18), vis_h=POST_BASE - g_pad, bury=0.06, batter=(5, 13))
        V[:, 2] += POST_BASE
        thr.add(xf(V, rotz(side * 0.25 + prs.uniform(-0.1, 0.1)), (pc[0], pc[1], 0.0)), F, "M_stone", wear=0.45)
        # cheek-panel sole rail: door post -> wall post, on the pad and the first plinth stone
        wp0 = az_pt(WALL_POST_AZ_DOOR * side, R_WALL, 0)
        q0 = np.array([side * 1.02, FRONT_Y + 0.17, 0.0])
        Lr = float(np.linalg.norm(wp0[:2] - q0[:2]))
        Rr = frame_R(wp0 - q0, (0, 0, 1))
        z_top_r = 0.405
        z_bot_r = min(max(float(stone_top([wp0[0]], [wp0[1]])[0]) - 0.01, PAD_TOP - 0.01), 0.30)
        hw_r = 0.06
        hewn_member(fr, (q0 + wp0) / 2 + np.array([0, 0, (z_top_r + z_bot_r) / 2]),
                    (Lr / 2, hw_r, (z_top_r - z_bot_r) / 2), Rr, rng, ch=0.015, ns=5, nc=4, ds=0.02,
                    end_checks=1, hidden=(2,))
        # director r4 #3c: packing stones under the cheek sole rail (no black void between the pad and the
        # first plinth stone): two split spalls bedded in the earth, their tops wedged under the rail
        for kf, tf in enumerate((0.28, 0.6)):
            frs = np.random.RandomState(5170 + 10 * side + kf)
            hf = np.array([frs.uniform(0.10, 0.13), frs.uniform(0.08, 0.10), 0.5 * (z_bot_r + 0.03)])
            Vf, Ff = spall_stone(frs, hf, n_planes=(6, 8), k_round=0.003)
            pf = q0 + (wp0 - q0) * tf + np.array([0, 0, 0]) - np.array([side * 0.0, 0.0, 0.0])
            Vf = xf(Vf, rotz(math.atan2(wp0[1] - q0[1], wp0[0] - q0[0]) + frs.uniform(-0.3, 0.3)), (0, 0, 0))
            Vf[:, 2] += (z_bot_r - 0.004) - Vf[:, 2].max()
            Vf[:, :2] += pf[:2] + nrm(np.array([q0[0], q0[1]])) * frs.uniform(-0.02, 0.03)
            thr.add(Vf, Ff, "M_stone", wear=0.5)
        # door posts (heavier, squared): front & door-side faces are hero faces, back face hidden
        wane_c = (3, 0) if side > 0 else (2, 1)
        inner_f, outer_f = (1, 3) if side > 0 else (3, 1)
        hewn_member(fr, (x, yc, (POST_BASE + HEAD_Z) / 2), ((HEAD_Z - POST_BASE) / 2, 0.12, 0.11),
                    rotz(side * 0.006) @ RV, rng, ch=0.02, wane=wane_c, n_checks=3,
                    check_faces=(2, 2, outer_f, inner_f), ns=11, nc=6, hero=(2, outer_f), hidden=(0, inner_f),
                    caps=(False, False), ds=0.007)
        # inner jambs on the sill
        xj = side * 0.60
        hewn_member(fr, (xj, yc, (SILL_TOP + HEAD_Z) / 2), ((HEAD_Z - SILL_TOP) / 2, 0.10, 0.11),
                    rotz(side * 0.004) @ roty(side * 0.003) @ RV, rng, ch=0.018, wane=(2 if side > 0 else 3,),
                    n_checks=2, check_faces=(2, inner_f), ns=10, nc=6, hero=(2, inner_f), hidden=(0, outer_f),
                    caps=(False, False), ds=0.007)
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
    # threshold (director r3 #3c): three flat slabs under the sill front, front edges wandering, depth
    # 0.22-0.35 m, 1-2 cm steps between the pieces, chipped notches of 3-6 cm
    trs = np.random.RandomState(5300)
    xs_t = [-0.64, 0.0, 0.62]
    tops_t = [0.081, 0.093, 0.074]
    for kt in range(3):
        hu_t = trs.uniform(0.36, 0.39)
        hv_t = trs.uniform(0.13, 0.17)
        # director r4 #2c: tops undulating 0.5-1.5 cm at 15-25 cm, 2-3 shallow spalls, arris 0.5-2.5 cm
        V, F = shell_stone(hu_t, hv_t, trs, "flag", 0.11, rr=(0.006, 0.016), rr_var=0.8, dome=0.004, tilt=0.008,
                           n_frac=0, frac_depth=(0.008, 0.016), frac_k=(0.003, 0.005), n_th=100, noise=0.013,
                           freq=5.0, side_bulge=0.0, side_slope=0.25, sm_scale=0.5, chips=trs.randint(2, 4),
                           chip_w=(0.03, 0.06), chip_d=(0.01, 0.02), spalls=trs.randint(2, 4),
                           face_fr=tuple(np.linspace(0.0, 0.94, 11)))
        V[:, 2] += tops_t[kt] - V[0, 2]
        yc_t = FRONT_Y - 0.03 + trs.uniform(-0.04, 0.03)
        add_shell(thr, V, F, "plan", rotz(trs.uniform(-0.06, 0.06)), (xs_t[kt] + trs.uniform(-0.02, 0.02), yc_t, 0.0),
                  "M_stone")

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
        # director r4 #4: irregular wear instead of periodic adze beads -- 1-3 soft lumps / hollows per
        # metre on the front face, varied in size, plus slow undulation
        ff = smoothstep(-0.13 + 0.03, -0.13, V[:, 1])
        for (xc_, wl_, am_) in sill_lumps:
            V[:, 1] -= am_ * np.exp(-((x - xc_) / wl_) ** 2) * ff
        V[:, 1] -= 0.002 * n2(x * 2.3, V[:, 2] * 3.0, 5333) * ff
        return V
    srs = np.random.RandomState(5331)
    sill_lumps = [(xc_, srs.uniform(0.05, 0.16), srs.choice([-1, 1]) * srs.uniform(0.002, 0.005))
                  for xc_ in np.sort(srs.uniform(-0.85, 0.85, srs.randint(3, 5)))]
    hewn_member(thr, (0.0, yc, (SILL_TOP + 0.09) / 2), (0.92, 0.13, sh), np.eye(3), rng, ch=0.015,
                end_checks=2, n_checks=1, check_faces=(0,), ns=8, nc=5, hero=(0, 1), hidden=(2, 3),
                deform=sill_wear, mat="M_timber", wear=0.9, adze=False)

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
    build_plinth(coll)
    build_wattle(coll)
    log("wattle")
    build_posts(coll)                 # after the daub fields: post flanks buried in the coat are culled
    log("plinth tops under the daub foot culled:", cull_object(bpy.data.objects["HUT_plinth_stones"], plinth_under_coat))
    log("plinth + posts")
    build_daub(coll)
    build_inner_skin(coll)
    log("daub")
    build_wall_plate(coll)
    build_rafters(coll)
    build_purlins_battens(coll)
    log("roof structure")
    build_shingles(coll)
    build_roof_blocker(coll)
    build_eave_closure(coll)
    log("shingles")
    zz = build_collar_finial(coll)
    log("collar drip %.3f fascia top %.3f lower top %.3f upper top %.3f spindle top %.3f tip %.3f" % zz)
    build_step(coll)
    log("step")
    build_door(coll)
    build_interior(coll)
    log("door + interior")
    tris = 0
    obs = list(coll.all_objects)
    for ob in obs:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    log(f"objects {len(obs)} (instances {N_INST[0]}, pooled meshes {len(POOLS)}) triangles {tris}")
    bpy.context.preferences.filepaths.save_version = 0          # no .blend1 backups in the building folder
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log("saved", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
