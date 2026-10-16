"""Hilltop Keep (KEEP) -- deterministic procedural build, geometry only.

Run:  /opt/bpyenv/bin/python build_hilltop_keep.py
Saves hilltop_keep.blend next to this script.

Layout (metres, Z up, hall centred on origin, principal door facing -Y):
  * octagonal rubble hall, 8.0 m across flats, wall to 3.45 m, 8 hewn corner posts on
    pedestals with curved knee braces, lap-jointed eave plate
  * tier 1: octagonal hipped skirt roof of long boards, bell-cast sprocketed eave
  * tier 2: steep collar of long split shakes with ragged comb top
  * tier 3: concave rubble stone cone ("candle snuffer")
  * lantern belt of vertical boards, tier 4 bell-cast shingle cap, turned/forged finial
  * west wing (thatch, ridge comb, plank door) with an engaged round turret
    (cushion collar, board drum, shingle cap, finial)
All randomness is seeded; the script is bit-for-bit reproducible.
"""
import math
import os
import time

import bpy
import bmesh  # noqa: E402  (must follow bpy)
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hilltop_keep.blend")
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


TAN22 = math.tan(math.radians(22.5))
MAT_NAMES = ["M_stone", "M_stone_dressed", "M_mortar", "M_timber", "M_timber_weathered",
             "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_glass",
             "M_rubble", "M_moss_clump"]
MAT_COL = {"M_stone": (0.55, 0.52, 0.47), "M_stone_dressed": (0.68, 0.66, 0.6),
           "M_mortar": (0.6, 0.58, 0.52), "M_timber": (0.35, 0.25, 0.17),
           "M_timber_weathered": (0.45, 0.42, 0.38), "M_roof_shingle": (0.38, 0.36, 0.3),
           "M_roof_shake": (0.42, 0.37, 0.3), "M_thatch": (0.5, 0.43, 0.28),
           "M_iron": (0.12, 0.12, 0.13), "M_lead": (0.4, 0.42, 0.44), "M_glass": (0.2, 0.25, 0.3),
           "M_rubble": (0.5, 0.48, 0.44), "M_moss_clump": (0.25, 0.35, 0.15)}
MATS = {}

# ----------------------------------------------------------------------------------------------
# noise (deterministic value noise, numpy)
# ----------------------------------------------------------------------------------------------
_NRS = np.random.RandomState(90210)
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


def n1(x, seed, freq=1.0):
    """smooth 1-D noise in [-1,1]."""
    x = np.asarray(x, float)
    return vnoise(np.stack([x * freq, np.full_like(x, seed * 17.31), np.full_like(x, seed * 3.7)], -1))


def fbm(p, octaves=3):
    p = np.asarray(p, float)
    tot = 0.0
    amp = 1.0
    for _ in range(octaves):
        tot = tot + amp * vnoise(p)
        p = p * 2.03 + 11.7
        amp *= 0.5
    return tot


# ----------------------------------------------------------------------------------------------
# mesh accumulator
# ----------------------------------------------------------------------------------------------
class Acc:
    def __init__(self, name):
        self.name = name
        self.V, self.F, self.M, self.UVv = [], [], [], []
        self.n = 0
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, verts, faces, mat, uv=None):
        verts = np.asarray(verts, float).reshape(-1, 3)
        if len(verts) == 0:
            return self.n
        base = self.n
        if not isinstance(faces, (list, tuple)):
            faces = [faces]
        self.V.append(verts)
        if uv is None:
            self.UVv.append(np.full((len(verts), 2), np.nan))
        else:
            self.UVv.append(np.asarray(uv, float).reshape(-1, 2))
        for f in faces:
            f = np.asarray(f, np.int64)
            if f.size == 0:
                continue
            if f.ndim == 1:
                f = f[None, :]
            self.F.append(f + base)
            self.M.append(np.full(len(f), self.mi(mat), np.int32))
        self.n += len(verts)
        return base

    def ntris(self):
        return int(sum(len(f) * (f.shape[1] - 2) for f in self.F))


COLLS = {}


def finalize(acc, coll, smooth_deg=38.0, recalc=True):
    if acc.n == 0 or not acc.F:
        log("  (empty)", acc.name)
        return None
    V = np.concatenate(acc.V)
    loops = np.concatenate([f.ravel() for f in acc.F])
    sizes = np.concatenate([np.full(len(f), f.shape[1], np.int32) for f in acc.F])
    mats = np.concatenate(acc.M)
    me = bpy.data.meshes.new(acc.name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops.astype(np.int32))
    me.polygons.add(len(sizes))
    starts = np.zeros(len(sizes), np.int32)
    starts[1:] = np.cumsum(sizes)[:-1]
    me.polygons.foreach_set("loop_start", starts)
    me.polygons.foreach_set("loop_total", sizes)
    me.polygons.foreach_set("material_index", mats)
    me.update(calc_edges=True)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
        loops = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops)
        sizes = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", sizes)
    # UVs: explicit per-vertex UVs where given (grain aligned), otherwise box projection
    nrm = np.zeros(len(sizes) * 3, np.float32)
    me.polygons.foreach_get("normal", nrm)
    nrm = nrm.reshape(-1, 3)
    lp = np.repeat(np.arange(len(sizes)), sizes)
    co = V[loops]
    ax = np.argmax(np.abs(nrm), 1)[lp]
    uv = np.where(ax[:, None] == 0, co[:, [1, 2]], np.where(ax[:, None] == 1, co[:, [0, 2]], co[:, [0, 1]]))
    vuv = np.concatenate(acc.UVv)[loops]
    has = ~np.isnan(vuv[:, 0])
    uv[has] = vuv[has]
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", uv.astype(np.float32).ravel())
    for m in acc.mats:
        me.materials.append(MATS[m])
    me.polygons.foreach_set("use_smooth", np.ones(len(sizes), bool))
    me.set_sharp_from_angle(angle=math.radians(smooth_deg))
    ob = bpy.data.objects.new(acc.name, me)
    coll.objects.link(ob)
    log(f"  {acc.name}: {len(V)} v, {acc.ntris()} tris")
    return ob


# ----------------------------------------------------------------------------------------------
# primitive generators (vectorised)
# ----------------------------------------------------------------------------------------------
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


def rbox(X, Y, Z, r, skip_back=False, skip_front=False, round_back=True):
    """Rounded boxes from per-instance axis coordinate arrays. X (M,nx) etc. r (M,).
    Returns P (M,V,3), quads (Q,4) (per-instance local indices)."""
    X, Y, Z = np.atleast_2d(X), np.atleast_2d(Y), np.atleast_2d(Z)
    gi, quads = rbox_topo(X.shape[1], Y.shape[1], Z.shape[1], skip_back, skip_front)
    P = np.stack([X[:, gi[:, 0]], Y[:, gi[:, 1]], Z[:, gi[:, 2]]], -1)
    r = np.broadcast_to(np.asarray(r, float), (X.shape[0],))
    lo = np.stack([X[:, 0] + r, Y[:, 0] + r, (Z[:, 0] + r) if round_back else np.full(len(r), -1e9)], -1)[:, None, :]
    hi = np.stack([X[:, -1] - r, Y[:, -1] - r, Z[:, -1] - r], -1)[:, None, :]
    C = np.clip(P, lo, hi)
    D = P - C
    n = np.linalg.norm(D, axis=-1, keepdims=True)
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
    """n>=4 coords from a to b with chamfer rows at r from the ends."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    inner = [a + r] + [a + (b - a) * (i / (n - 3)) for i in range(1, n - 3)] + [b - r]
    return np.stack([a] + inner + [b], 1)


def sweep(path, ups, prof, caps=True):
    """Sweep closed CCW profile (m,2) [right,up] along path (n,3). Returns verts, [quads, caps]."""
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


def lathe(prof_rz, seg, cx=0.0, cy=0.0, z0=0.0, cap_bottom=True, cap_top=True, phase=0.0):
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


def rot2(x, y, a):
    c, s = np.cos(a), np.sin(a)
    return x * c - y * s, x * s + y * c


# ----------------------------------------------------------------------------------------------
# irregular stones on a parametric surface
# ----------------------------------------------------------------------------------------------
def axr(h, r, n):
    """n>=8 coords from -h..h with a 2-segment rounded arris band (-h, -h+0.3r, -h+r, ..., h)."""
    h = np.asarray(h, float)
    r = np.asarray(r, float)
    ni = n - 6
    inner = [-h + r + (2 * h - 2 * r) * (i / (ni - 1)) for i in range(ni)]
    return np.stack([-h, -h + 0.3 * r] + inner + [h - 0.3 * r, h], 1)


def build_stones(acc, S, mapfn, mat, rng, rough=1.0, nxy=5, premap=None, noise_amp=0.006, grid=None,
                 dressed=False, wear=None, front_min=0.003, nz2=False):
    """S: dict of arrays sc, zc, hx, hy, f (front), back, r, rot, zcrs (course coord for mapfn).
    Optional per-stone: shl/shr (end-joint shear dx/dy of left/right ends), sbb/sbt (bed slopes dy/dx of
    bottom/top beds), pillow, tiltx/tilty (metres at the stone edge).
    Local stone frame: x along s, y along z, z = outward offset w.
    Outline changes are clamped so joints stay 1-3 cm; relief = pillow + tilt + split facets + chips."""
    M = len(S["sc"])
    if M == 0:
        return
    hx, hy, f, back, r = [np.asarray(S[k], float) for k in ("hx", "hy", "f", "back", "r")]
    r = np.minimum(r, np.minimum(hx, hy) * 0.32)
    if grid is not None:
        X = axr(hx, r, grid[0])
        Y = axr(hy, r, grid[1])
        Z = np.stack([-back, f - r, f], 1)
    elif nxy == 7:
        X = axn(-hx, hx, r, 7)
        Y = axn(-hy, hy, r, 7)
        Z = np.stack([-back, f - r, f], 1)
    else:
        X = ax5(hx, r) if nxy == 5 else ax4(hx, r)
        Y = ax5(hy, r) if nxy == 5 else ax4(hy, r)
        Z = np.stack([-back, f - r, f], 1)
    if nz2:
        # single side segment + one chamfer band (cheap stones for distant / non-hero masonry)
        Z = np.stack([-back, f], 1)
    P, quads = rbox(X, Y, Z, r, skip_back=True, round_back=False)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    ux = np.clip(x / hx[:, None], -1, 1)
    uy = np.clip(y / hy[:, None], -1, 1)
    HX, HY = hx[:, None], hy[:, None]
    co = rng.uniform(0, 1, (M, 12))
    # --- outline: tiny end bow / bed wave only (absolute, clamped) -> joints stay tight
    endp = (0.003 * co[:, 0:1] + 0.006 * (co[:, 1:2] - 0.5) * (uy + 1)) * rough
    endn = (0.003 * co[:, 3:4] + 0.006 * (co[:, 4:5] - 0.5) * (uy + 1)) * rough
    sh = np.where(ux > 0, endp, endn).clip(0, 0.006) * np.abs(ux) ** 4
    x = x - np.sign(x) * sh
    topw = (0.002 * co[:, 6:7] + 0.005 * (co[:, 7:8] - 0.5) * (ux + 1)) * rough
    botw = (0.0015 * co[:, 8:9] + 0.004 * (co[:, 9:10] - 0.5) * (ux + 1)) * rough
    shy = np.where(uy > 0, topw, botw).clip(0, 0.005) * np.abs(uy) ** 4
    y = y - np.sign(y) * shy
    # knocked-off corners: small (<= ~2 cm), in the face plane; the void is filled by pinning stones
    cc = rng.uniform(0, 1, (M, 8))
    for ci_, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        on = cc[:, ci_:ci_ + 1] < (0.12 if dressed else 0.35)
        depth = np.where(on, np.minimum((0.006 + 0.016 * cc[:, 4 + ci_:5 + ci_]) * min(rough, 1.0) + 0.004,
                                        0.3 * np.minimum(HX, HY)), 0.0)
        ang = 0.3 + 0.4 * cc[:, 4 + ci_:5 + ci_]
        e = (sx * x - HX) * ang + (sy * y - HY) * (1 - ang) + depth
        e = np.maximum(e, 0.0)
        x = x - sx * e * ang
        y = y - sy * e * (1 - ang)
    # broken-edge in-plane noise on the outline (mm scale)
    on = fbm(np.stack([x * 11.0, y * 11.0, np.broadcast_to(co[:, 11:12] * 77.0, x.shape)], -1), 2)
    edge = np.clip(np.maximum(np.abs(ux), np.abs(uy)) - 0.6, 0, 1) * 2.5
    x = x - np.sign(x) * np.abs(on) * (0.0015 if dressed else 0.003) * rough * edge
    y = y - np.sign(y) * np.abs(on) * (0.0012 if dressed else 0.0025) * rough * edge
    # --- coherent joint shears (neighbours share the same slanted joint / bed line)
    shl = np.asarray(S.get("shl", np.zeros(M)), float)[:, None]
    shr = np.asarray(S.get("shr", np.zeros(M)), float)[:, None]
    sbb = np.asarray(S.get("sbb", np.zeros(M)), float)[:, None]
    sbt = np.asarray(S.get("sbt", np.zeros(M)), float)[:, None]
    x0_, y0_ = x.copy(), y.copy()
    x = x0_ + y0_ * (shl * (1 - ux) * 0.5 + shr * (1 + ux) * 0.5)
    y = y0_ + x0_ * (sbb * (1 - uy) * 0.5 + sbt * (1 + uy) * 0.5)
    # --- face relief (front region only)
    fw = np.clip((z + back[:, None] * 0.35) / (f[:, None] + back[:, None] * 0.35), 0, 1) ** 2
    pil = np.asarray(S.get("pillow", np.full(M, 0.008)), float)[:, None]
    tx = np.asarray(S.get("tiltx", np.zeros(M)), float)[:, None]
    ty = np.asarray(S.get("tilty", np.zeros(M)), float)[:, None]
    relief = pil * (1 - ux ** 2) * (1 - uy ** 2) + tx * ux + ty * uy
    sid = np.broadcast_to(np.arange(M)[:, None] * 1.37 + co[:, 10:11] * 13.0, x.shape)
    if dressed:
        # tooled face: 2-5 mm undulation, punched/pitched centre inside a 2-3 cm drafted margin
        und = 0.0045 * fbm(np.stack([x * 7.0, y * 7.0, sid], -1), 2)
        pick = np.abs(fbm(np.stack([x * 38.0, y * 38.0, sid * 3.1], -1), 2))
        dm = np.minimum(HX - np.abs(x0_), HY - np.abs(y0_))
        marg = np.asarray(S.get("margin", np.full(M, 0.025)), float)[:, None]
        inner = np.clip((dm - marg) / 0.008, 0, 1)
        relief = relief + und + inner * (0.003 + 0.004 * pick) - (1 - inner) * 0.0015
        facets = 0.0
        nzv = 0.0
    else:
        nz = fbm(np.stack([x * 16.0 + co[:, 11:12] * 50, y * 16.0, sid], -1), 3)
        nz = nz + 0.6 * np.abs(fbm(np.stack([x * 31.0, y * 31.0 + co[:, 10:11] * 40, sid * 0.52], -1), 2)) - 0.3
        nzv = noise_amp * rough * nz
        # chisel / split facets: 3 planar breaks per stone, 0.5-2.5 cm deep at the stone edge
        cr = rng.uniform(0, 1, (M, 16))
        facets = 0.0
        for i in range(4):
            aa = np.cos(cr[:, i:i + 1] * 6.283)
            bb = np.sin(cr[:, i:i + 1] * 6.283)
            c0 = 0.2 + 0.55 * cr[:, 4 + i:5 + i]
            dep = 0.006 + 0.024 * cr[:, 8 + i:9 + i] ** 1.2
            # metric slope so the facet depth at the arris is 'dep'
            dn = np.maximum(aa * ux + bb * uy - c0, 0.0) / np.maximum(1.0 - c0, 0.2)
            facets = facets - dep * dn * rough
    # arris chips: 2-4 per stone, 1-3 cm, conchoidal dents on the edge
    nch = rng.integers(3, 6, M) if dressed else rng.integers(2, 5, M)
    chips = np.zeros_like(x)
    cp = rng.uniform(0, 1, (M, 4, 4))
    for i in range(4):
        act = (i < nch)[:, None]
        t = cp[:, i, 0:1] * 4.0
        side = np.floor(t).astype(int)
        fr = t - side
        ex = np.where(side == 0, -1 + 2 * fr, np.where(side == 1, 1.0, np.where(side == 2, 1 - 2 * fr, -1.0)))
        ey = np.where(side == 0, -1.0, np.where(side == 1, -1 + 2 * fr, np.where(side == 2, 1.0, 1 - 2 * fr)))
        px, py = ex * HX, ey * HY
        rad = (0.016 + 0.022 * cp[:, i, 1:2]) if dressed else (0.01 + 0.02 * cp[:, i, 1:2])
        if wear is not None:
            rad = rad * (1 + 0.6 * np.asarray(wear, float)[:, None])
        dep = rad * ((0.5 + 0.35 * cp[:, i, 2:3]) if dressed else (0.35 + 0.35 * cp[:, i, 2:3]))
        d = np.sqrt((x0_ - px) ** 2 + (y0_ - py) ** 2)
        chips = np.minimum(chips, -np.where(act, dep * np.clip(1 - d / rad, 0, 1) ** 1.3, 0.0))
    dz = relief + nzv + facets + chips
    zf = z + fw * dz
    # never let the face sink behind the mortar body
    zf = np.where(fw > 0.3, np.maximum(zf, front_min - (1 - fw) * 0.01), zf)
    # chips also nibble the outline a little (broken arris)
    pull = np.clip(-chips, 0, 0.03) * (0.8 if dressed else 0.5) * fw
    x = x - np.sign(x0_) * pull * (np.abs(ux) > 0.6)
    y = y - np.sign(y0_) * pull * (np.abs(uy) > 0.6)
    z = zf
    if wear is not None:
        # worn stones: arrises and face rounded off further (lower jamb blocks, threshold)
        wv = np.asarray(wear, float)[:, None]
        rim = np.clip(np.maximum(np.abs(ux), np.abs(uy)) - 0.75, 0, 1) * 4
        z = z - fw * wv * 0.012 * rim ** 2
    rr = np.asarray(S.get("rot", np.zeros(M)), float)[:, None]
    x, y = rot2(x, y, rr)
    if premap is not None:
        s_, z_ = premap(x, y, S)
    else:
        s_ = np.asarray(S["sc"], float)[:, None] + x
        z_ = np.asarray(S["zc"], float)[:, None] + y
    zcr = np.broadcast_to(np.asarray(S["zcrs"], float)[:, None], x.shape)
    W = mapfn(s_.ravel(), z_.ravel(), z.ravel(), zcr.ravel())
    acc.add(W, inst_faces(quads, M, P.shape[1]), mat)


def stone_footprint_mask(S, s0, z0, res, shape):
    """rasterise stone faces (s,z param space) into a bool grid (approx. inverse of the joint shears)."""
    mask = np.zeros(shape, bool)
    ns, nz = shape
    for i in range(len(S["sc"])):
        sc, zc, hx, hy = S["sc"][i], S["zc"][i], S["hx"][i], S["hy"][i]
        ext = hx + hy * 0.4 + 0.01
        a0 = max(int((sc - ext - s0) / res), 0)
        a1 = min(int((sc + ext - s0) / res) + 2, ns)
        b0 = max(int((zc - hy - 0.02 - z0) / res), 0)
        b1 = min(int((zc + hy + 0.02 - z0) / res) + 2, nz)
        if a1 <= a0 or b1 <= b0:
            continue
        ss = s0 + (np.arange(a0, a1) + 0.5) * res
        zz = z0 + (np.arange(b0, b1) + 0.5) * res
        dx = ss[:, None] - sc
        dy = zz[None, :] - zc
        c, s_ = math.cos(-S["rot"][i]), math.sin(-S["rot"][i])
        dx, dy = dx * c - dy * s_, dx * s_ + dy * c
        if any(_g(S, k_, i) > 0.004 for k_ in ("cq0", "cq1", "cq2", "cq3", "kk")):
            mask[a0:a1, b0:b1] |= _inside_poly(dx, dy, stone_outline(S, i))
            continue
        shx = np.where(dx > 0, S["shr"][i], S["shl"][i]) if "shl" in S else 0.0
        shy = np.where(dy > 0, S["sbt"][i], S["sbb"][i]) if "sbb" in S else 0.0
        xx = dx - dy * shx
        yy = dy - dx * shy
        mask[a0:a1, b0:b1] |= (np.abs(xx) <= hx) & (np.abs(yy) <= hy)
    return mask


def box_sum(A, k):
    """sum over a (2k+1)^2 window (zero padded) via summed-area table."""
    A = A.astype(np.int32)
    P = np.pad(A, ((k + 1, k), (k + 1, k)))
    C = P.cumsum(0).cumsum(1)
    n0, n1 = A.shape
    w = 2 * k + 1
    return C[w:w + n0, w:w + n1] - C[0:n0, w:w + n1] - C[w:w + n0, 0:n1] + C[0:n0, 0:n1]


def fill_voids(S, srange_fn, excl_fn, z_bot, z_top, rng, cfg, ztop_fn=None, res=0.01, label=""):
    """find mortar voids wider than ~3 cm between laid stones and plug them with pinning stones.
    Returns (pin stone dict, visible-mortar fraction before, after)."""
    L = max(b for zm in np.linspace(z_bot, z_top, 5) for a, b in srange_fn(zm))
    ns, nz = int(L / res) + 1, int((z_top - z_bot) / res) + 1
    valid = np.zeros((ns, nz), bool)
    ss = (np.arange(ns) + 0.5) * res
    zt_arr = np.array([ztop_fn(s_) for s_ in ss]) if ztop_fn is not None else None
    for j in range(nz):
        z = z_bot + (j + 0.5) * res
        row = np.zeros(ns, bool)
        for a, b in srange_fn(z):
            row |= (ss >= a + 0.012) & (ss <= b - 0.012)
        for ea, eb in excl_fn(z - 0.004, z + 0.004, z):
            row &= ~((ss >= ea - 0.012) & (ss <= eb + 0.012))
        if zt_arr is not None:
            row &= z < zt_arr - 0.015
        valid[:, j] = row
    valid[:, :2] = False
    valid[:, -2:] = False
    stone = stone_footprint_mask(S, 0.0, z_bot, res, (ns, nz))
    empty = valid & ~stone
    frac0 = empty.sum() / max(valid.sum(), 1)
    pins = {k: [] for k in S.keys()}
    filled = ~empty
    for it in range(4000):
        core = box_sum(~filled, 1) == 9
        idx = np.flatnonzero(core)
        if len(idx) == 0:
            break
        # deterministic pick: stride through the candidates
        pick = idx[(it * 7919) % len(idx)]
        i, j = np.unravel_index(pick, core.shape)
        # free extent along s and z
        def run(arr):
            n = 0
            for v in arr:
                if v:
                    break
                n += 1
            return n
        l = run(filled[i::-1, j][:40])
        rgt = run(filled[i:, j][:40])
        d = run(filled[i, j::-1][:30])
        u = run(filled[i, j:][:30])
        hx = max((l + rgt - 1) * res * 0.5 - 0.006, 0.008)
        hy = max((d + u - 1) * res * 0.5 - 0.006, 0.008)
        sc = (i - l + 1 + (l + rgt - 1) * 0.5) * res
        zc = z_bot + (j - d + 1 + (d + u - 1) * 0.5) * res
        # long thin voids: split into chunks
        if hx > 0.16:
            hx = rng.uniform(0.05, 0.12)
            sc = (i + 0.5) * res
        if hy > 0.10:
            hy = rng.uniform(0.04, 0.08)
            zc = z_bot + (j + 0.5) * res
        a0, a1 = int(max(sc - hx - 0.006, 0) / res), int((sc + hx + 0.006) / res) + 1
        b0, b1 = int(max(zc - hy - 0.006 - z_bot, 0) / res), int((zc + hy + 0.006 - z_bot) / res) + 1
        filled[a0:a1, b0:b1] = True
        filled[i, j] = True
        pins["sc"].append(sc)
        pins["zc"].append(zc)
        pins["hx"].append(hx)
        pins["hy"].append(hy)
        pins["f"].append(rng.uniform(0.004, cfg["front"][1] * 0.6))
        pins["back"].append(0.05)
        pins["r"].append(rng.uniform(0.004, 0.009))
        pins["rot"].append(rng.normal(0, 0.15))
        pins["zcrs"].append(zc)
        pins["pillow"].append(rng.uniform(0.002, 0.006))
        pins["tiltx"].append(rng.normal(0, 0.002))
        pins["tilty"].append(rng.normal(0, 0.002))
        for kk in ("shl", "shr", "sbb", "sbt"):
            if kk in pins:
                pins[kk].append(0.0)
        for kk in pins:
            if len(pins[kk]) < len(pins["sc"]):
                pins[kk].append(0.0)
    P = {k: np.array(v, float) for k, v in pins.items()}
    frac1 = (valid & ~filled).sum() / max(valid.sum(), 1)
    log(f"  {label} visible mortar {frac0 * 100:.1f}% -> {frac1 * 100:.1f}% after {len(P['sc'])} pinning stones")
    return P, frac0, frac1


def layout_wall(rng, srange_fn, z_bot, z_top, excl_fn, cfg, ztop_fn=None):
    """Coursed rubble layout. Returns dict of stone arrays (in surface coords s, z)."""
    st = {k: [] for k in ("sc", "zc", "hx", "hy", "f", "back", "r", "rot", "zcrs", "pillow", "tiltx", "tilty")}
    seed = cfg.get("seed", 1)
    # course boundaries
    bounds = [z_bot]
    z = z_bot
    if cfg.get("footing"):
        z = cfg["footing"]
        bounds.append(z)
    mix = cfg.get("ch_mix")
    while z < z_top - 1e-6:
        if mix is not None:
            # course-height mixture over the full 8-25 cm range (thin pinning courses .. through courses)
            u_ = rng.uniform()
            acc_p = 0.0
            h = rng.uniform(*mix[-1][1:])
            for pr_, lo_, hi_ in mix:
                acc_p += pr_
                if u_ < acc_p:
                    h = rng.uniform(lo_, hi_)
                    break
        else:
            h = rng.uniform(*cfg["ch"])
            if rng.uniform() < cfg.get("p_tall", 0.08):
                h = rng.uniform(0.2, 0.26)
        if z + h > z_top - cfg["ch"][0] * 0.7:
            h = z_top - z
        z += h
        bounds.append(z)
    nb = len(bounds)
    amp = cfg.get("bed_amp", 0.022)
    # pinch-outs: local ramps in a bed line so the course above/below thins to a slip (5-6 cm) over 0.7-1.8 m
    # and swells again; the stones in the ramp become wedges / trapezoids with angled beds (shared, coherent)
    bumps = {k: [] for k in range(nb)}
    pin = cfg.get("pinch")
    if pin is not None:
        L_ = max(b for a, b in srange_fn(0.5 * (z_bot + z_top)))
        for k in range(1, nb - 1):
            n_b = rng.poisson(L_ * pin[0])
            for _ in range(n_b):
                sc_ = rng.uniform(0, L_)
                w_ = rng.uniform(*pin[2])
                A_ = rng.uniform(*pin[1]) * (1 if rng.uniform() < 0.5 else -1)
                room = (bounds[k + 1] - bounds[k]) - 0.055 if A_ > 0 else (bounds[k] - bounds[k - 1]) - 0.055
                if room < 0.025:
                    continue
                A_ = math.copysign(min(abs(A_), room), A_)
                clash = any(abs(sc_ - b_[0]) < 0.5 * (w_ + b_[1]) + 0.1 for kk in (k - 1, k + 1) for b_ in bumps.get(kk, []))
                if clash:
                    continue
                bumps[k].append((sc_, w_, A_))

    def bed(k, s):
        s = np.asarray(s, float)
        if k == 0 or k == nb - 1:
            return np.full_like(s, bounds[k])
        v = bounds[k] + amp * n1(s, seed * 100 + k, 1.0 / 3.5)
        for sc_, w_, A_ in bumps[k]:
            v = v + A_ * 0.5 * (1 + np.cos(np.pi * np.clip((s - sc_) / (0.5 * w_), -1, 1)))
        return v

    blocked = {}
    for k_ in ("shl", "shr", "sbb", "sbt"):
        st[k_] = []
    sl_sd = cfg.get("slant", 0.22)

    def bed_slope(k, s):
        return float((bed(k, s + 0.04) - bed(k, s - 0.04)) / 0.08)

    def push(sc, zc, hx, hy, fr, r, zm, shl, shr, kb, kt, tilt_back=None):
        st["sc"].append(sc)
        st["zc"].append(zc)
        st["hx"].append(hx)
        st["hy"].append(hy)
        st["f"].append(fr)
        st["back"].append(cfg.get("back", 0.09))
        st["r"].append(r)
        st["rot"].append(rng.normal(0, cfg.get("rot", 0.004)))
        st["zcrs"].append(zm)
        st["pillow"].append(rng.uniform(*cfg["pillow"]))
        # tilt: +-1 deg sideways, ~1/3 of the stones lean back up to 3 deg (top edge recessed)
        st["tiltx"].append(rng.normal(0, 0.012) * hx)
        tb = -math.tan(math.radians(rng.uniform(0.5, 3.0))) * hy if rng.uniform() < 0.35 else rng.normal(0, 0.01) * hy
        st["tilty"].append(tb if tilt_back is None else tilt_back)
        st["shl"].append(shl)
        st["shr"].append(shr)
        st["sbb"].append(bed_slope(kb, sc) if 0 < kb < nb - 1 else 0.0)
        st["sbt"].append(bed_slope(kt, sc) if 0 < kt < nb - 1 else 0.0)

    def arris():
        u = rng.uniform()
        lo, hi = cfg["bevel"]
        return lo + (hi - lo) * u ** 2.2

    for k in range(nb - 1):
        z0, z1 = bounds[k], bounds[k + 1]
        zm = 0.5 * (z0 + z1)
        footing = cfg.get("footing") and k == 0
        free = []
        for a, b in srange_fn(zm):
            free.append([a, b])
        ex = excl_fn(z0 - 0.03, z1 + 0.03, zm) + blocked.get(k, [])
        for ea, eb in ex:
            nf = []
            for a, b in free:
                if eb <= a or ea >= b:
                    nf.append([a, b])
                else:
                    if ea > a:
                        nf.append([a, ea])
                    if eb < b:
                        nf.append([eb, b])
            free = nf
        lr = cfg["foot_len"] if footing else cfg["len"]
        for a, b in free:
            j0 = rng.uniform(*cfg["joint"])
            pos = a + j0 * 0.5
            prev_slant = 0.0
            run_start = len(st["sc"])
            while b - pos > 0.07:
                L = rng.uniform(*lr)
                if rng.uniform() < cfg.get("p_long", 0.06) and not footing:
                    L = rng.uniform(0.75, 0.92)
                j = rng.uniform(*cfg["joint"])
                rem = b - pos - j * 0.5
                if rem - L - j < lr[0] * 0.75:
                    L = rem if rem < lr[1] * 1.35 else rem * 0.5
                if L < 0.05:
                    break
                if L < 0.16 and not footing:
                    L = max(L, 0.07)
                s0, s1 = pos, pos + L
                sc = 0.5 * (s0 + s1)
                dbl = (not footing) and k + 2 < nb and (z1 - z0) < 0.17 and (bounds[k + 2] - z1) < 0.17 \
                    and L < 0.62 and rng.uniform() < cfg.get("p_double", 0.07)
                zb = float(bed(k, sc))
                zt = float(bed(k + 2 if dbl else k + 1, sc))
                if ztop_fn is not None:
                    lim = ztop_fn(sc)
                    if zb > lim - 0.05:
                        pos = s1 + j
                        prev_slant = 0.0
                        continue
                    zt = min(zt, lim)
                jb = rng.uniform(*cfg["joint"]) * 0.5
                jt = rng.uniform(*cfg["joint"]) * 0.5
                hy = 0.5 * (zt - zb) - 0.5 * (jb + jt)
                if hy < 0.03:
                    pos = s1 + j
                    prev_slant = 0.0
                    continue
                if dbl:
                    blocked.setdefault(k + 1, []).append((s0 - j * 0.5, s1 + j * 0.5))
                # slant of this stone's right-hand joint (shared with the next stone's left end)
                at_end = b - (s1 + j) < 0.08
                slant = 0.0 if at_end else float(np.clip(rng.normal(0, sl_sd), -0.4, 0.4))
                if footing:
                    slant *= 0.4
                split = (not footing) and (not dbl) and (zt - zb) > 0.12 and rng.uniform() < cfg.get("p_split", 0.10)
                if split:
                    # thin stone + one or two thin stones stacked on it, filling the full course
                    zm2 = zb + (zt - zb) * rng.uniform(0.4, 0.6)
                    jj = rng.uniform(*cfg["joint"]) * 0.5
                    push(sc, 0.5 * (zb + jb + zm2 - jj), 0.5 * L - 0.002, 0.5 * (zm2 - jj - zb - jb),
                         rng.uniform(*cfg["front"]), arris() * 0.7, zm, prev_slant, slant, k, k)
                    if rng.uniform() < 0.5 or L < 0.25:
                        push(sc, 0.5 * (zm2 + jj + zt - jt), 0.5 * L - 0.002, 0.5 * (zt - jt - zm2 - jj),
                             rng.uniform(*cfg["front"]), arris() * 0.7, zm, prev_slant, slant, k + 1, k + 1)
                    else:
                        cut = s0 + L * rng.uniform(0.35, 0.65)
                        jx = rng.uniform(*cfg["joint"])
                        ms = float(np.clip(rng.normal(0, sl_sd), -0.4, 0.4))
                        for (pa, pb, sl0, sl1) in ((s0, cut - jx / 2, prev_slant, ms), (cut + jx / 2, s1, ms, slant)):
                            push(0.5 * (pa + pb), 0.5 * (zm2 + jj + zt - jt), 0.5 * (pb - pa) - 0.002,
                                 0.5 * (zt - jt - zm2 - jj), rng.uniform(*cfg["front"]), arris() * 0.7, zm,
                                 sl0, sl1, k + 1, k + 1)
                    pos = s1 + j
                    prev_slant = slant
                    continue
                fr = rng.uniform(*cfg["front"]) + (rng.uniform(*cfg["foot_proj"]) if footing else 0.0)
                uu = rng.uniform()
                if uu < 0.07:
                    fr += rng.uniform(0.008, 0.016)      # bulging / proud stone
                elif uu < 0.14:
                    fr = max(0.005, fr - 0.010)          # weathered-back stone
                push(sc, 0.5 * (zb + jb + zt - jt) if not footing else 0.5 * (zb + zt - jt), 0.5 * L - 0.002,
                     hy if not footing else 0.5 * (zt - zb - jt), fr, arris(), zm, prev_slant, slant,
                     k, k + 2 if dbl else k + 1)
                pos = s1 + j
                prev_slant = slant
            # close the run: stretch the last stone(s) so no gap is left at the run end
            gap = b - pos
            if len(st["sc"]) > run_start and gap > 0.004:
                n_last = 1
                zc_last = st["zc"][-1]
                if len(st["sc"]) - run_start >= 2 and abs(st["sc"][-2] - st["sc"][-1]) < 1e-6:
                    n_last = 2
                for q in range(1, n_last + 1):
                    st["hx"][-q] += 0.5 * (gap - 0.006)
                    st["sc"][-q] += 0.5 * (gap - 0.006)
                    st["shr"][-q] = 0.0
                if n_last == 1 and len(st["sc"]) - run_start >= 2 and abs(st["zc"][-2] - zc_last) > 0.02 and \
                        abs((st["sc"][-2] + st["hx"][-2]) - (st["sc"][-1] + st["hx"][-1])) < 0.2:
                    st["hx"][-2] += 0.5 * (gap - 0.006)
                    st["sc"][-2] += 0.5 * (gap - 0.006)
                    st["shr"][-2] = 0.0
    return {k: np.array(v, float) for k, v in st.items()}


def filt(S, mask):
    return {k: v[mask] for k, v in S.items()}


def cat_stones(*Ss):
    keys = Ss[0].keys()
    return {k: np.concatenate([np.asarray(s[k], float) for s in Ss]) for k in keys}


def stone_rec(sc, zc, hx, hy, f, back, r, zcrs, rng, pillow=(0.002, 0.006), rot=0.004, tilt=0.002):
    M = len(np.atleast_1d(sc))
    return {"sc": np.atleast_1d(np.asarray(sc, float)), "zc": np.atleast_1d(np.asarray(zc, float)),
            "hx": np.broadcast_to(np.asarray(hx, float), (M,)).copy(),
            "hy": np.broadcast_to(np.asarray(hy, float), (M,)).copy(),
            "f": np.broadcast_to(np.asarray(f, float), (M,)).copy(),
            "back": np.broadcast_to(np.asarray(back, float), (M,)).copy(),
            "r": np.broadcast_to(np.asarray(r, float), (M,)).copy(),
            "zcrs": np.broadcast_to(np.asarray(zcrs, float), (M,)).copy(),
            "rot": rng.normal(0, rot, M), "pillow": rng.uniform(*pillow, M),
            "tiltx": rng.normal(0, tilt, M), "tilty": rng.normal(0, tilt, M)}


def _g(S, k, i, d=0.0):
    v = S.get(k)
    return float(v[i]) if v is not None else d


def stone_outline(S, i):
    """CCW polygon (local x along s, y up) of stone i: sheared quadrilateral (shared joint slants / bed slopes),
    optional big knocked-off corners (cq0..cq3: BL, BR, TR, TL) and an optional kink on the top bed (kk)."""
    hx, hy = float(S["hx"][i]), float(S["hy"][i])
    shl, shr, sbb, sbt = _g(S, "shl", i), _g(S, "shr", i), _g(S, "sbb", i), _g(S, "sbt", i)
    C = [np.array([-hx - hy * shl, -hy - hx * sbb]), np.array([hx - hy * shr, -hy + hx * sbb]),
         np.array([hx + hy * shr, hy + hx * sbt]), np.array([-hx + hy * shl, hy - hx * sbt])]
    pts = []
    for k in range(4):
        cur, prv, nxt = C[k], C[k - 1], C[(k + 1) % 4]
        c = _g(S, f"cq{k}", i)
        if c > 0.004:
            d1, d2 = prv - cur, nxt - cur
            l1, l2 = np.linalg.norm(d1), np.linalg.norm(d2)
            asp = _g(S, f"ca{k}", i, 1.0)
            a = min(c * asp, 0.45 * l1)
            b = min(c / max(asp, 0.3), 0.45 * l2)
            pts.append(cur + d1 / l1 * a)
            pts.append(cur + d2 / l2 * b)
        else:
            pts.append(cur)
        if k == 2 and _g(S, "kk", i) > 0.004:
            # kink in the top bed: a shallow concave break between TR and TL
            t = _g(S, "kt", i, 0.5)
            q = C[2] * (1 - t) + C[3] * t
            pts.append(q - np.array([0.0, _g(S, "kk", i)]))
    return np.array(pts)


def _inside_poly(px, py, poly):
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


def polygonize(S, sel, rng, p_cut=0.34, p_taper=0.16, p_kink=0.12):
    """turn a share of the selected (hero) stones into non-rectangular pieces: knocked-off corners (5-6 sided),
    one long bed angled 5-14 deg (wedges), kinked top beds (6-7 sided). Voids are later pinned by fill_voids."""
    M = len(S["sc"])
    for k in ("cq0", "cq1", "cq2", "cq3", "ca0", "ca1", "ca2", "ca3", "kk", "kt", "spl"):
        if k not in S:
            S[k] = np.zeros(M)
    for i in np.flatnonzero(sel):
        hx, hy = S["hx"][i], S["hy"][i]
        if hx < 0.06 or hy < 0.035:
            continue
        u = rng.uniform()
        if u < p_cut:
            ncut = 1 if rng.uniform() < 0.65 else 2
            for k in rng.choice(4, ncut, replace=False):
                S[f"cq{k}"][i] = min(rng.uniform(0.035, 0.11), 0.9 * hy, 0.6 * hx)
                S[f"ca{k}"][i] = rng.uniform(0.6, 1.6)
        elif u < p_cut + p_taper:
            ang = math.radians(rng.uniform(5.0, 14.0))
            D = min(2 * hx * math.tan(ang), 0.9 * hy)
            sg = 1 if rng.uniform() < 0.5 else -1
            if rng.uniform() < 0.6:          # top bed drops toward one end
                S["sbt"][i] -= sg * D / (2 * hx)
                S["hy"][i] -= D / 4
                S["zc"][i] -= D / 4
            else:                             # bottom bed rises toward one end
                S["sbb"][i] += sg * D / (2 * hx)
                S["hy"][i] -= D / 4
                S["zc"][i] += D / 4
        elif u < p_cut + p_taper + p_kink:
            S["kk"][i] = rng.uniform(0.012, 0.028)
            S["kt"][i] = rng.uniform(0.3, 0.7)
        # 1-2 big split planes on (almost) every hero face
        S["spl"][i] = 1 + (rng.uniform() < 0.45)
    return S


def rounded_outline(poly, rc, spacing):
    """resample a polygon with corners rounded at radius rc; returns points (N,2) and inward unit normals."""
    P = np.asarray(poly, float)
    n = len(P)
    # orientation
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        P = P[::-1]
    out, nrm = [], []
    for k in range(n):
        a, b, c = P[k - 1], P[k], P[(k + 1) % n]
        d1 = (a - b) / max(np.linalg.norm(a - b), 1e-9)
        d2 = (c - b) / max(np.linalg.norm(c - b), 1e-9)
        cosang = float(np.clip(np.dot(d1, d2), -0.999, 0.999))
        half = math.acos(cosang) / 2
        t = min(rc / max(math.tan(half), 1e-3), 0.45 * np.linalg.norm(a - b), 0.45 * np.linalg.norm(c - b))
        p1, p2 = b + d1 * t, b + d2 * t
        # arc from p1 to p2 (quadratic Bezier approximation, 3 points)
        for tt in ((0.0, 1.0) if t < 0.012 else (0.0, 0.5, 1.0)):
            q = (1 - tt) ** 2 * p1 + 2 * tt * (1 - tt) * b + tt ** 2 * p2
            out.append(q)
        # straight edge to the next corner is added implicitly by resampling below
    O = np.array(out)
    # resample along the closed loop with max spacing, keeping all corner-arc points
    pts = []
    m = len(O)
    for k in range(m):
        a, b = O[k], O[(k + 1) % m]
        L = np.linalg.norm(b - a)
        ns = max(1, int(math.ceil(L / spacing)))
        for j in range(ns):
            pts.append(a + (b - a) * (j / ns))
    Q = np.array(pts)
    # drop near duplicates
    keep = np.ones(len(Q), bool)
    dd = np.linalg.norm(np.diff(np.vstack([Q, Q[:1]]), axis=0), axis=1)
    keep[1:] = dd[:-1] > 1e-5
    Q = Q[keep]
    T = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    N = np.stack([-T[:, 1], T[:, 0]], 1)          # left of a CCW tangent = inward
    return Q, N


def build_poly_stones(acc, S, mapfn, mat, rng, rough=1.0, spacing=0.05, rings=(0.62, 0.3), noise_amp=0.009,
                      front_min=0.003):
    """Hero rubble: every stone built from its true (polygonal) outline with a rounded front arris, a split / cleaved
    face (1-2 large planes at 5-15 deg), chisel facets, chipped arrises and a low pillow. Rings: outline at the back,
    arris start, arris middle, face edge, then rings scaled toward the centroid and a centre fan."""
    M = len(S["sc"])
    for i in range(M):
        poly = stone_outline(S, i)
        hx, hy = float(S["hx"][i]), float(S["hy"][i])
        r = float(min(S["r"][i], 0.3 * min(hx, hy), 0.02))
        r = max(r, 0.004)
        f = float(S["f"][i])
        back = float(S["back"][i])
        nspl = int(_g(S, "spl", i))
        sd = rng.uniform(0, 100)
        # split planes (metric): z_off = -tan(a) * max(0, d.p - c)
        planes = []
        th0 = rng.uniform(0, 2 * np.pi)
        for ip in range(nspl):
            # one dominant split plane over 40-70 % of the face; an optional smaller facet that never opposes it
            th = th0 if ip == 0 else th0 + rng.choice([-1, 1]) * rng.uniform(0.35, 1.2)
            dvec = np.array([math.cos(th), math.sin(th)])
            ext = np.abs(poly @ dvec).max()
            c0 = (rng.uniform(-0.25, 0.25) if ip == 0 else rng.uniform(0.3, 0.6)) * ext
            ang = rng.uniform(5.0, 12.0) if ip == 0 else rng.uniform(8.0, 15.0)
            planes.append((dvec, c0, math.tan(math.radians(ang))))
        maxdep = sum(t * max(0.0, np.abs(poly @ d).max() - c) for d, c, t in planes)
        f_eff = f + min(0.55 * maxdep, 0.03)
        Q, N = rounded_outline(poly, rc=max(r * 1.08, 0.006), spacing=spacing)
        nq = len(Q)
        cen = Q.mean(0)
        R0 = Q
        R1 = Q
        R2 = Q + N * (0.29 * r)
        R3 = Q + N * r
        inner = [cen + (R3 - cen) * sc_ for sc_ in rings]
        ring_xy = [R0, R1, R3] + inner + [cen[None, :]]
        rho = [1.0, 1.0, 1.0] + list(rings) + [0.0]

        def relief(xy, rh):
            x, y = xy[:, 0], xy[:, 1]
            pil = _g(S, "pillow", i, 0.004) * (1 - rh ** 2) * 0.8
            tilt = _g(S, "tiltx", i) * x / max(hx, 1e-3) + _g(S, "tilty", i) * y / max(hy, 1e-3)
            nz = fbm(np.stack([x * 15.0 + sd, y * 15.0, np.full(len(x), sd * 0.37)], -1), 3)
            nz = nz + 0.5 * np.abs(fbm(np.stack([x * 34.0, y * 34.0 + sd, np.full(len(x), sd)], -1), 2)) - 0.25
            fac = np.zeros(len(x))
            for dvec, c0, tn in planes:
                fac -= tn * np.maximum(xy @ dvec - c0, 0.0)
            # two small chisel facets near the edge
            return pil + tilt + noise_amp * rough * nz + fac
        # chisel facets & chips (shared between rings via position)
        chis = [(np.array([math.cos(a_), math.sin(a_)]), rng.uniform(0.55, 0.85), rng.uniform(0.004, 0.012))
                for a_ in rng.uniform(0, 2 * np.pi, 2)]
        nch = int(rng.integers(2, 5))
        chip_pts = Q[rng.integers(0, nq, nch)]
        chip_rad = rng.uniform(0.012, 0.03, nch)

        def extra(xy):
            e = np.zeros(len(xy))
            for dvec, c0, dep in chis:
                ext = np.abs(poly @ dvec).max()
                e -= dep * np.maximum((xy @ dvec) / ext - c0, 0) / (1 - c0)
            for cp_, cr_ in zip(chip_pts, chip_rad):
                dd = np.linalg.norm(xy - cp_, axis=1)
                e -= cr_ * 0.5 * np.clip(1 - dd / cr_, 0, 1) ** 1.3
            return e
        Vr = []
        zface = []
        for j, (xy, rh) in enumerate(zip(ring_xy, rho)):
            if j == 0:
                z = np.full(len(xy), -back)
            else:
                zf = f_eff + relief(xy, rh) + extra(xy)
                zf = np.maximum(zf, front_min)
                z = zf - 0.75 * r if j == 1 else zf
            Vr.append(np.column_stack([xy, z]))
        V = np.vstack(Vr)
        # faces: quads between consecutive rings (same count nq), centre fan
        F = []
        for j in range(len(ring_xy) - 2):
            a0 = j * nq
            b0 = (j + 1) * nq
            k_ = np.arange(nq)
            F.append(np.stack([a0 + k_, a0 + (k_ + 1) % nq, b0 + (k_ + 1) % nq, b0 + k_], 1))
        c_idx = (len(ring_xy) - 1) * nq
        a0 = (len(ring_xy) - 2) * nq
        k_ = np.arange(nq)
        F.append(np.stack([a0 + k_, a0 + (k_ + 1) % nq, np.full(nq, c_idx)], 1))
        # local -> param -> world
        x, y = rot2(V[:, 0], V[:, 1], _g(S, "rot", i))
        s_ = S["sc"][i] + x
        z_ = S["zc"][i] + y
        W = mapfn(s_, z_, V[:, 2], np.full(len(s_), S["zcrs"][i]))
        acc.add(W, F, mat)


# ==============================================================================================
# GLOBAL LAYOUT
# ==============================================================================================
A0 = 4.0                      # hall outer apothem at ground (8.0 m across flats)
WALL_H = 3.45
BAT = math.tan(math.radians(2.0))
BULGE = 0.04
A_REF = 3.99                  # plumb reference plane for joinery in openings
INNER_APO = 3.30              # inner wall face (0.7 m wall)

# facets CCW from NW: 0 NW, 1 W, 2 SW, 3 S(door), 4 SE, 5 E, 6 NE, 7 N
FPHI = [math.radians(135 + 45 * k) for k in range(8)]
FN = [np.array([math.cos(p), math.sin(p)]) for p in FPHI]
FT = [np.array([-math.sin(p), math.cos(p)]) for p in FPHI]

# west wing / turret
WX_W, WX_E, WY_S, WY_N = -10.0, -1.3, 0.4, 4.6
WY_R = 0.5 * (WY_S + WY_N)
W_WALL_H = 2.55
W_PITCH = math.radians(47.0)
W_TAN = math.tan(W_PITCH)
W_OVH = 0.55
W_RAFT = 2.40 + W_OVH * W_TAN          # thatch underside at outer wall line (eave lip at 2.40)
CORE_T = 0.30                           # perpendicular thickness of the thatch core body under the courses
TH_V = (CORE_T + 0.06) / math.cos(W_PITCH)   # vertical thickness to the mean course surface (~0.36-0.40 perp)
TH_V_MIN = (CORE_T + 0.01) / math.cos(W_PITCH)  # vertical thickness to the lowest point of the course sawtooth
TUR_C = np.array([-8.55, 2.70])
TUR_Z_TOP = 5.92                 # top of the stone body (cushion sits on it)
# concave stone cone (ref1, Director's round-3 profile): flank leans ~24 deg where it leaves the wing eave, easing
# to ~8 deg under the cushion; below the eave a D4.7 base bulging out of the wing's N and W walls
_TPZ = np.array([-0.3, 0.0, 1.3, 2.6, 3.5, 4.5, 5.4, 5.9, 6.1])
_TPR = np.array([2.385, 2.38, 2.365, 2.35, 1.95, 1.55, 1.32, 1.25, 1.24])


def _tur_table():
    zf = np.linspace(_TPZ[0], _TPZ[-1], 641)
    rf = np.interp(zf, _TPZ, _TPR)
    for _ in range(45):
        rf[1:-1] = 0.25 * rf[:-2] + 0.5 * rf[1:-1] + 0.25 * rf[2:]
    return zf, rf


TUR_ZF, TUR_RF = _tur_table()
TUR_CLIP_Y = 0.42                 # nothing of the turret may stand in front of the wing's south wall face


def tur_r(z):
    return np.interp(np.asarray(z, float), TUR_ZF, TUR_RF)


def tur_reff(th, z):
    """effective radius in plan direction th: the circle, flattened onto the south wall plane below the thatch."""
    r = tur_r(z)
    sn = np.sin(th)
    lim = np.where(sn < -1e-3, (TUR_C[1] - TUR_CLIP_Y) / np.maximum(-sn, 1e-3), 1e9)
    return np.where(np.asarray(z, float) < 3.4, np.minimum(r, lim), r)


def tur_dist(x, y, z):
    """signed horizontal distance of points from the turret stone surface (+ outside)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    th = np.arctan2(y - TUR_C[1], x - TUR_C[0])
    return np.hypot(x - TUR_C[0], y - TUR_C[1]) - tur_reff(th, z)


# ----------------------------------------------------------------------------------------------
# turret / wing-wall junctions: bonded with toothing stones that wrap the re-entrant corner every 2-3 courses
# ----------------------------------------------------------------------------------------------
def _junction(name, z):
    """junction point (x,y), turret angle and arc direction sign for the wall 'N' (north wall, east of the
    turret) or 'W' (west wall, south of the turret) at height z."""
    z = np.asarray(z, float)
    r = tur_r(z)
    if name == "N":
        yf = WY_N - z * BAT
        xj = TUR_C[0] + np.sqrt(np.maximum(r * r - (yf - TUR_C[1]) ** 2, 0))
        return xj, yf, np.arctan2(yf - TUR_C[1], xj - TUR_C[0]), 1.0
    xf = WX_W + z * BAT
    yj = TUR_C[1] - np.sqrt(np.maximum(r * r - (xf - TUR_C[0]) ** 2, 0))
    return xf, yj, np.arctan2(yj - TUR_C[1], xf - TUR_C[0]), -1.0


def _tooth_specs():
    rng = np.random.default_rng(1818)
    out = []
    for name in ("N", "W"):
        z = rng.uniform(0.34, 0.45)
        while z < 2.30:
            h = rng.uniform(0.15, 0.23)
            out.append(dict(j=name, z0=z, z1=z + h, Lt=rng.uniform(0.22, 0.36), Lw=rng.uniform(0.26, 0.42),
                            f=rng.uniform(0.032, 0.05), r=rng.uniform(0.012, 0.024)))
            z += h + rng.uniform(0.16, 0.30)        # every 2-3 courses
    return out


TOOTH = _tooth_specs()


def tooth_map_factory(name):
    def mapfn(u, z, w, zc):
        u = np.asarray(u, float)
        z = np.asarray(z, float)
        w = np.asarray(w, float)
        xj, yj, thj, sg = _junction(name, z)
        r = tur_r(z)
        if name == "N":
            pw = np.stack([xj + u, yj], -1)
            nw = np.stack([np.zeros_like(u), np.ones_like(u)], -1)
        else:
            pw = np.stack([xj + 0 * u, yj - u], -1)
            nw = np.stack([-np.ones_like(u), np.zeros_like(u)], -1)
        th = thj + sg * np.maximum(-u, 0) / r
        pt = np.stack([TUR_C[0] + r * np.cos(th), TUR_C[1] + r * np.sin(th)], -1)
        nt = np.stack([np.cos(th), np.sin(th)], -1)
        on_wall = (u >= 0)[..., None]
        P = np.where(on_wall, pw, pt)
        bl = np.clip(0.5 + u / 0.12, 0, 1)[..., None]
        bl = bl * bl * (3 - 2 * bl)
        N = nt * (1 - bl) + nw * bl
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        # bridge the concave crease: push the corner region out a little so the stone wraps it
        P = P + N * (w + 0.012 * np.exp(-(u / 0.06) ** 2))[..., None]
        return np.concatenate([P, z[..., None]], -1)
    return mapfn


def tooth_cull(P, which):
    """True for wall ('wall') or turret ('tur') stone centres displaced by a toothing stone."""
    P = np.asarray(P, float)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    bad = np.zeros(x.shape, bool)
    for t in TOOTH:
        zin = (z > t["z0"] - 0.05) & (z < t["z1"] + 0.05)
        xj, yj, thj, sg = _junction(t["j"], z)
        if which == "wall":
            if t["j"] == "N":
                u = x - xj
                onw = np.abs(y - yj) < 0.2
            else:
                u = yj - y
                onw = np.abs(x - xj) < 0.2
            bad |= zin & onw & (u > -0.05) & (u < t["Lw"] + 0.03)
        else:
            th = np.arctan2(y - TUR_C[1], x - TUR_C[0])
            dth = np.angle(np.exp(1j * (th - thj)))
            u = -sg * dth * tur_r(z)
            bad |= zin & (u < 0.05) & (u > -t["Lt"] - 0.03)
    return bad


def tooth_excl_wall(z0, z1, zm):
    """s-ranges (wing path coords) occupied by toothing stones in the band z0..z1."""
    out = []
    for t in TOOTH:
        if z1 < t["z0"] - 0.012 or z0 > t["z1"] + 0.012:
            continue
        xj, yj, thj, sg = _junction(t["j"], zm)
        sj = wing_s_of(float(xj), float(yj))
        if t["j"] == "N":
            out.append((sj - t["Lw"] - 0.012, sj + 0.4))
        else:
            out.append((sj - 0.4, sj + t["Lw"] + 0.012))
    return out


def tooth_excl_tur(z0, z1, zm):
    """s-ranges (turret coords, s = theta * r) occupied by toothing stones."""
    out = []
    r = float(tur_r(zm))
    L = 2 * math.pi * r
    for t in TOOTH:
        if z1 < t["z0"] - 0.012 or z0 > t["z1"] + 0.012:
            continue
        xj, yj, thj, sg = _junction(t["j"], zm)
        th = float(np.mod(thj, 2 * np.pi))
        a = th * r
        lo, hi = (a - 0.15, a + t["Lt"] + 0.012) if sg > 0 else (a - t["Lt"] - 0.012, a + 0.15)
        for sh in (-L, 0.0, L):
            if hi + sh > 0 and lo + sh < L:
                out.append((max(lo + sh, 0.0), min(hi + sh, L)))
    return out


def build_tooth_stones(acc, rng):
    for name in ("N", "W"):
        T = [t for t in TOOTH if t["j"] == name]
        if not T:
            continue
        sc = np.array([(t["Lw"] - t["Lt"]) / 2 for t in T])
        hx = np.array([(t["Lw"] + t["Lt"]) / 2 for t in T])
        zc = np.array([(t["z0"] + t["z1"]) / 2 for t in T])
        hy = np.array([(t["z1"] - t["z0"]) / 2 - 0.006 for t in T])
        S = stone_rec(sc, zc, hx, hy, np.array([t["f"] for t in T]), 0.14, np.array([t["r"] for t in T]), zc, rng,
                      pillow=(0.003, 0.008), rot=0.01, tilt=0.004)
        build_stones(acc, S, tooth_map_factory(name), "M_stone", rng, rough=1.1, grid=(16, 8), noise_amp=0.009)


def wing_under(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    zs = W_RAFT + (y - WY_S) * W_TAN
    zn = W_RAFT + (WY_N - y) * W_TAN
    zw = W_RAFT + (x - WX_W) * W_TAN
    return np.minimum(np.minimum(zs, zn), zw)


def wing_top(x, y):
    return wing_under(x, y) + TH_V


def in_wing(P, margin=0.0, zpad=0.03):
    """points inside the wing envelope (under the thatch, within walls)."""
    P = np.asarray(P, float)
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    return (x < WX_E - margin) & (x > WX_W + margin) & (y > WY_S + margin) & (y < WY_N - margin) & \
        (z < wing_under(x, y) - zpad)


def apo(z):
    return A0 - np.asarray(z, float) * BAT


def build_outline():
    rc = 0.08 / A0
    half = TAN22 - rc * TAN22
    pts, nrm, bul = [], [], []

    def straight(k, x0, x1):
        n, t = FN[k], FT[k]
        xs = np.arange(x0, x1, 0.004)
        for x in xs:
            pts.append(n + t * x)
            nrm.append(n)
            bul.append(math.sin(math.pi * (x + half) / (2 * half)))

    def arc(k):
        phi = FPHI[k]
        cang = phi + math.radians(22.5)
        cen = (1 - rc) / math.cos(math.radians(22.5)) * np.array([math.cos(cang), math.sin(cang)])
        for a in np.linspace(phi, phi + math.radians(45), 6)[:-1]:
            d = np.array([math.cos(a), math.sin(a)])
            pts.append(cen + rc * d)
            nrm.append(d)
            bul.append(0.0)

    straight(0, 0.0, half)
    arc(0)
    for k in range(1, 8):
        straight(k, -half, half)
        arc(k)
    straight(0, -half, 0.0)
    pts.append(pts[0])
    nrm.append(nrm[0])
    bul.append(bul[0])
    P = np.array(pts)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    return L / L[-1], P, np.array(nrm), np.array(bul), L[-1]


OT, OP, ON, OB, L1 = build_outline()


def hall_L(z):
    return apo(z) * L1


def hall_map(s, z, w, zc):
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    t = np.mod(s / hall_L(zc), 1.0)
    ox, oy = np.interp(t, OT, OP[:, 0]), np.interp(t, OT, OP[:, 1])
    nx, ny = np.interp(t, OT, ON[:, 0]), np.interp(t, OT, ON[:, 1])
    nn = np.sqrt(nx * nx + ny * ny)
    nx, ny = nx / nn, ny / nn
    b = BULGE * np.interp(t, OT, OB)
    a = apo(z)
    k3 = 1.0 / math.sqrt(1 + BAT * BAT)
    return np.stack([a * ox + b * nx + w * nx * k3, a * oy + b * ny + w * ny * k3, z + w * BAT * k3], -1)


def face_apo(k, x, z):
    """apothem of the outer wall face at facet-local x, height z."""
    half = TAN22 * A0
    return apo(z) + BULGE * np.sin(np.pi * np.clip((x + half) / (2 * half), 0, 1))


def fmap(k, x, z, w, a_ref=A_REF):
    """plumb facet-local frame: x along facet (CCW), z up, w outward from plane at a_ref."""
    x = np.asarray(x, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    n, t = FN[k], FT[k]
    return np.stack([(a_ref + w) * n[0] + x * t[0], (a_ref + w) * n[1] + x * t[1], z], -1)


def facet_s(k, x, zc):
    return (k / 8.0) * hall_L(zc) + np.asarray(x, float)


# ----------------------------------------------------------------------------------------------
# openings
# ----------------------------------------------------------------------------------------------
OPENINGS = [
    dict(name="door", k=3, xc=0.35, kind="arch", hw=0.525, z0=0.12, zs=1.77, depth=0.30),
    dict(name="win_sw", k=2, xc=0.0, kind="rect", hw=0.47, z0=1.24, z1=2.38, depth=0.09, frame=True, surround="timber"),
    dict(name="slit_w", k=1, xc=0.62, kind="rect", hw=0.09, z0=1.45, z1=2.05, depth=0.30, frame=False),
    dict(name="win_e", k=5, xc=-0.25, kind="rect", hw=0.25, z0=1.42, z1=2.02, depth=0.30, frame=True),
    dict(name="win_ne", k=6, xc=0.2, kind="rect", hw=0.25, z0=1.42, z1=2.02, depth=0.30, frame=True),
]


def open_contains(op, x, z, m=0.0):
    x = np.asarray(x, float) - op["xc"]
    z = np.asarray(z, float)
    hw = op["hw"] + m
    if op["kind"] == "arch":
        rect = (np.abs(x) <= hw) & (z >= op["z0"] - m) & (z <= op["zs"])
        arc = (x * x + (z - op["zs"]) ** 2 <= hw * hw) & (z > op["zs"])
        return rect | arc
    return (np.abs(x) <= hw) & (z >= op["z0"] - m) & (z <= op["z1"] + m)


def open_outline(op, grow=0.0, n_arc=16):
    """CCW outline (x,z) in facet coords."""
    hw = op["hw"] + grow
    xc = op["xc"]
    if op["kind"] == "arch":
        z0 = op["z0"] - grow - 0.12
        pts = [(xc - hw, z0), (xc + hw, z0)]
        for a in np.linspace(0, math.pi, n_arc):
            pts.append((xc + hw * math.cos(a), op["zs"] + hw * math.sin(a)))
        return np.array(pts)
    z0, z1 = op["z0"] - grow, op["z1"] + grow
    return np.array([(xc - hw, z0), (xc + hw, z0), (xc + hw, z1), (xc - hw, z1)])


DRESSED_POLYS = {k: [] for k in range(8)}   # facet -> list of (x,z) polygons (exclusions)


def poly_band_extent(poly, z0, z1):
    P = np.asarray(poly, float)
    Q = np.roll(P, -1, axis=0)
    t = np.linspace(0, 1, 14)[None, :, None]
    S = (P[:, None, :] * (1 - t) + Q[:, None, :] * t).reshape(-1, 2)
    m = (S[:, 1] >= z0) & (S[:, 1] <= z1)
    if not m.any():
        if P[:, 1].min() < z0 and P[:, 1].max() > z1:
            return P[:, 0].min(), P[:, 0].max()
        return None
    return S[m, 0].min(), S[m, 0].max()


def hall_excl(z0, z1, zm):
    out = []
    for op in OPENINGS:
        e = poly_band_extent(open_outline(op, grow=0.0), z0, z1)
        if e is not None:
            out.append((float(facet_s(op["k"], e[0] - 0.01, zm)), float(facet_s(op["k"], e[1] + 0.01, zm))))
    for k in range(8):
        for poly in DRESSED_POLYS[k]:
            e = poly_band_extent(poly, z0, z1)
            if e is not None:
                out.append((float(facet_s(k, e[0] - 0.012, zm)), float(facet_s(k, e[1] + 0.012, zm))))
    return out


# ==============================================================================================
# HALL MASONRY
# ==============================================================================================
def build_door_dressing(acc_d, op, rng):
    k, xc, hw, zs = op["k"], op["xc"], op["hw"], op["zs"]
    leaf_apo = A_REF - op["depth"]
    recs = []
    # jambs (alternating long / short), both sides
    hs = np.array([0.40, 0.33, 0.37, 0.34, 0.33]) * rng.uniform(0.94, 1.06, 5)
    zb = -0.06
    hs = hs / hs.sum() * (zs - zb)
    zz = zb + np.concatenate([[0], np.cumsum(hs)])
    for side in (-1, 1):
        for i in range(5):
            long_ = (i % 2 == 0) == (side < 0)
            wd = (0.39 if long_ else 0.27) + rng.uniform(-0.03, 0.03)
            z0_, z1_ = zz[i] + 0.006, zz[i + 1] - 0.006
            x_in = xc + side * hw
            x_out = x_in + side * wd
            xa, xb = min(x_in, x_out), max(x_in, x_out)
            zc = 0.5 * (z0_ + z1_)
            back = float(face_apo(k, x_in, zc)) - leaf_apo - 0.012
            recs.append(dict(x=0.5 * (xa + xb), zc=zc, hx=0.5 * (xb - xa) - 0.006, hy=0.5 * (z1_ - z0_),
                             f=0.05 + rng.uniform(0, 0.012), back=back))
            DRESSED_POLYS[k].append([(xa, z0_), (xb, z0_), (xb, z1_), (xa, z1_)])
    S = stone_rec([facet_s(k, r["x"], r["zc"]) for r in recs], [r["zc"] for r in recs],
                  [r["hx"] for r in recs], [r["hy"] for r in recs], [r["f"] for r in recs],
                  [r["back"] for r in recs], rng.uniform(0.008, 0.022, len(recs)),
                  [r["zc"] for r in recs], rng)
    dress_irregular(S, rng)
    wear = np.clip(1.1 - S["zc"] / 0.9, 0, 1)
    build_stones(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(30, 32), wear=wear)
    # voussoirs: irregular widths, thicker at the crown
    nv = 13
    wts = rng.uniform(0.8, 1.2, nv)
    wts[nv // 2] *= 1.15
    th = math.pi - np.concatenate([[0], np.cumsum(wts) / wts.sum() * math.pi])
    vs = []
    for i in range(nv):
        ta, tb = th[i], th[i + 1]
        tm = 0.5 * (ta + tb)
        rin = hw
        rout = hw + 0.31 + 0.05 * math.sin(tm) + rng.uniform(-0.015, 0.035) + (0.03 if i == nv // 2 else 0)
        rm = 0.5 * (rin + rout)
        hx = 0.5 * (ta - tb) * rm - 0.007
        zc_abs = zs + rm * math.sin(tm)
        xm = xc + rm * math.cos(tm)
        back = float(face_apo(k, xm, zc_abs)) - leaf_apo - 0.012
        vs.append((tm, rm, hx, 0.5 * (rout - rin) - 0.004, back, zc_abs, 0.055 + rng.uniform(0, 0.012) + (0.012 if i == nv // 2 else 0)))
        poly = [(xc + rin * math.cos(a), zs + rin * math.sin(a)) for a in np.linspace(tb, ta, 5)] + \
               [(xc + rout * math.cos(a), zs + rout * math.sin(a)) for a in np.linspace(ta, tb, 5)]
        DRESSED_POLYS[k].append(poly)
    vs = np.array(vs)
    S = stone_rec(np.zeros(nv), vs[:, 5], vs[:, 2], vs[:, 3], vs[:, 6], vs[:, 4],
                  rng.uniform(0.008, 0.022, nv), vs[:, 5], rng)
    dress_irregular(S, rng, rot_sd=0.0)
    S["th"] = vs[:, 0]
    S["rm"] = vs[:, 1]

    def premap(x, y, SS):
        t = SS["th"][:, None] - x / SS["rm"][:, None]
        R = SS["rm"][:, None] + y
        xf = xc + R * np.cos(t)
        zf = zs + R * np.sin(t)
        return facet_s(k, xf, SS["zcrs"][:, None]), zf

    build_stones(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, premap=premap, dressed=True, grid=(22, 24))


def dress_irregular(S, rng, rot_sd=0.012):
    """dressed blocks set +-1-2 deg out of square (sheared ends / beds, slight rotation)."""
    M = len(S["sc"])
    sgn = lambda: np.where(rng.uniform(0, 1, M) < 0.5, -1.0, 1.0)
    S["shl"] = sgn() * np.tan(np.radians(rng.uniform(0.8, 2.0, M)))
    S["shr"] = sgn() * np.tan(np.radians(rng.uniform(0.8, 2.0, M)))
    S["sbb"] = sgn() * np.tan(np.radians(rng.uniform(0.3, 1.2, M)))
    S["sbt"] = sgn() * np.tan(np.radians(rng.uniform(0.3, 1.2, M)))
    S["rot"] = rng.normal(0, rot_sd, M)
    S["margin"] = rng.uniform(0.02, 0.03, M)
    S["tiltx"] = rng.normal(0, 0.004, M)
    S["tilty"] = rng.normal(0, 0.004, M)
    S["pillow"] = rng.uniform(0.001, 0.003, M)


def build_rect_dressing(acc_d, op, rng, sill_acc):
    k, xc, hw, z0, z1 = op["k"], op["xc"], op["hw"], op["z0"], op["z1"]
    depth = op["depth"]
    fr_apo = A_REF - depth
    h = z1 - z0
    if op.get("surround") == "timber":
        # simple heavy timber frame set in the rubble (ref1): no dressed jambs, only the stone sill;
        # the timber lintel (built with the frame) bears 0.16 m into the rubble each side.
        DRESSED_POLYS[k].append([(xc - hw - 0.17, z1 - 0.01), (xc + hw + 0.17, z1 - 0.01),
                                 (xc + hw + 0.17, z1 + 0.21), (xc - hw - 0.17, z1 + 0.21)])
        build_sill(sill_acc, op, rng)
        return
    nj = 3 if h > 0.8 else 2
    hs = rng.uniform(0.9, 1.1, nj)
    hs = hs / hs.sum() * h
    zz = z0 + np.concatenate([[0], np.cumsum(hs)])
    recs = []
    for side in (-1, 1):
        for i in range(nj):
            long_ = (i % 2 == 0) == (side < 0)
            wd = (0.30 if long_ else 0.22) * (1.0 if hw > 0.2 else 0.85) + rng.uniform(-0.02, 0.02)
            za, zb = zz[i] + 0.006, zz[i + 1] - 0.006
            x_in = xc + side * hw
            xa, xb = sorted([x_in, x_in + side * wd])
            zc = 0.5 * (za + zb)
            back = float(face_apo(k, x_in, zc)) - fr_apo - 0.006
            recs.append((0.5 * (xa + xb), zc, 0.5 * (xb - xa) - 0.006, 0.5 * (zb - za), 0.045 + rng.uniform(0, 0.01), back))
            DRESSED_POLYS[k].append([(xa, za), (xb, za), (xb, zb), (xa, zb)])
    # lintel
    lw = hw + (0.30 if hw > 0.2 else 0.22) + rng.uniform(0.0, 0.05)
    lh = 0.26 if hw > 0.2 else 0.2
    za, zb = z1 + 0.006, z1 + lh
    zc = 0.5 * (za + zb)
    recs.append((xc + rng.uniform(-0.03, 0.03), zc, lw, 0.5 * (zb - za), 0.05, float(face_apo(k, xc, zc)) - fr_apo - 0.006))
    DRESSED_POLYS[k].append([(xc - lw, za), (xc + lw, za), (xc + lw, zb), (xc - lw, zb)])
    R = np.array(recs)
    S = stone_rec(facet_s(k, R[:, 0], R[:, 1]), R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5],
                  rng.uniform(0.008, 0.014, len(R)), R[:, 1], rng)
    dress_irregular(S, rng)
    build_stones(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(24, 24))
    build_sill(sill_acc, op, rng)


def build_sill(sill_acc, op, rng):
    """projecting stone sill: weathered, tooled top, drip groove underneath, chipped arrises."""
    k, xc, hw, z0 = op["k"], op["xc"], op["hw"], op["z0"]
    depth = op["depth"]
    sw = hw + (0.16 if hw > 0.2 else 0.12)
    st = 0.13 if hw > 0.2 else 0.11
    proj = 0.07 if hw > 0.2 else 0.05
    ztop = z0 - 0.004
    wf = 0.04 + proj          # front of sill relative to wall face plane
    wb = -depth - 0.02
    c = 0.012
    prof = np.array([(wb, ztop - st), (wf - 0.035, ztop - st), (wf - 0.035, ztop - st + 0.014),
                     (wf - 0.022, ztop - st + 0.014), (wf - 0.022, ztop - st), (wf - c, ztop - st),
                     (wf, ztop - st + c), (wf, ztop - 0.02 - c), (wf - c, ztop - 0.02),
                     (0.0, ztop), (wb, ztop)])
    xs = np.linspace(xc - sw, xc + sw, 36)
    nx_, npf = len(xs), len(prof)
    V = np.zeros((nx_, npf, 3))
    V[:, :, 0] = xs[:, None]
    V[:, :, 1] = prof[None, :, 1]
    V[:, :, 2] = prof[None, :, 0]
    V[:, :, 1] += 0.004 * np.sin(np.linspace(0, 3, nx_))[:, None] * (V[:, :, 2] > -0.01)
    # out of level by ~1 deg, tooled undulation, worn & chipped front arris
    V[:, :, 1] += (xs[:, None] - xc) * math.tan(math.radians(rng.uniform(-1.2, 1.2)))
    sd = rng.uniform(0, 50)
    V[:, :, 1] += 0.003 * fbm(np.stack([V[:, :, 0] * 8 + sd, V[:, :, 2] * 8, V[:, :, 1] * 8], -1), 2)
    V[:, :, 2] += 0.003 * fbm(np.stack([V[:, :, 0] * 6, V[:, :, 1] * 9 + sd, V[:, :, 2]], -1), 2) * (V[:, :, 2] > 0.0)
    front = (V[:, :, 2] > wf - 0.03)
    for _ in range(rng.integers(2, 5)):
        cx_ = rng.uniform(xc - sw + 0.03, xc + sw - 0.03)
        rad = rng.uniform(0.015, 0.035)
        dd = np.clip(1 - np.abs(V[:, :, 0] - cx_) / rad, 0, 1) ** 1.2 * front
        V[:, :, 2] -= dd * rad * 0.35
        V[:, :, 1] -= dd * rad * 0.25 * (V[:, :, 1] > ztop - 0.03)
    V = V.reshape(-1, 3)
    W = fmap(k, V[:, 0], V[:, 1], V[:, 2], a_ref=float(face_apo(k, xc, ztop)))
    i = np.arange(nx_ - 1)[:, None]
    j = np.arange(npf)[None, :]
    a = i * npf + j
    b = i * npf + (j + 1) % npf
    quads = np.stack([a, a + npf, b + npf, b], -1).reshape(-1, 4)
    caps = [np.arange(npf)[None, :], ((nx_ - 1) * npf + np.arange(npf)[::-1])[None, :]]
    sill_acc.add(W, [quads] + caps, "M_stone_dressed")
    DRESSED_POLYS[k].append([(xc - sw, ztop - st), (xc + sw, ztop - st), (xc + sw, ztop), (xc - sw, ztop)])


def hall_cull(S):
    P = hall_map(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
    return ~in_wing(P, margin=0.12, zpad=0.12)


def build_hall_masonry(coll):
    rng = np.random.default_rng(101)
    acc = Acc("KEEP_hall_wall_stones")
    accd = Acc("KEEP_hall_dressed_stones")
    for op in OPENINGS:
        if op["kind"] == "arch":
            build_door_dressing(accd, op, rng)
        else:
            build_rect_dressing(accd, op, rng, accd)
    cfg = dict(seed=7, footing=0.34, ch=(0.085, 0.18), p_tall=0.08, len=(0.18, 0.62), foot_len=(0.45, 0.85),
               joint=(0.008, 0.017), front=(0.005, 0.032), foot_proj=(0.03, 0.06), bevel=(0.005, 0.03),
               pillow=(0.002, 0.007), rot=0.004, p_double=0.07, p_long=0.05, back=0.09, bed_amp=0.028,
               slant=0.27, ch_mix=[(0.30, 0.08, 0.11), (0.38, 0.11, 0.16), (0.22, 0.16, 0.21), (0.10, 0.21, 0.25)],
               pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
    srange = lambda zm: [(0.0, float(hall_L(zm)))]
    S = layout_wall(rng, srange, -0.10, WALL_H, hall_excl, cfg)

    def hero_of(SS):
        t = np.mod(SS["sc"] / hall_L(SS["zcrs"]), 1.0)
        fac = np.round(t * 8).astype(int) % 8
        return np.isin(fac, (2, 3, 4)) & (SS["zc"] < 3.5), fac
    hero0, _ = hero_of(S)
    S = polygonize(S, hero0 & (S["zc"] > 0.3), np.random.default_rng(1919))
    pins, _, _ = fill_voids(S, srange, hall_excl, -0.10, WALL_H, rng, cfg, label="hall")
    S = cat_stones(S, pins)
    S = filt(S, hall_cull(S))
    log("  hall stones:", len(S["sc"]))
    # hero zone (SW, S door, SE facets): true polygonal outlines, split planes, chisel facets, chipped arrises
    hero, fac = hero_of(S)
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    poly_n = hero & ~small
    npoly = int(sum(1 for i in np.flatnonzero(poly_n) if len(stone_outline(S, i)) != 4 or
                    abs(S["sbt"][i] - S["sbb"][i]) > 0.06 or abs(S["shl"][i] - S["shr"][i]) > 0.12))
    log(f"  hall hero stones {int(poly_n.sum())} (non-rectangular {npoly}), other {int((~hero & ~small).sum())}, "
        f"pins {int(small.sum())}")
    build_poly_stones(acc, filt(S, poly_n), hall_map, "M_stone", np.random.default_rng(2020))
    # non-hero facets: N / NE / E / NW thinned (single side segment + chamfer band)
    build_stones(acc, filt(S, ~hero & ~small), hall_map, "M_stone", rng, rough=1.0, nxy=5, noise_amp=0.008, nz2=True)
    build_stones(acc, filt(S, small & hero), hall_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005)
    build_stones(acc, filt(S, small & ~hero), hall_map, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True)
    finalize(acc, coll, smooth_deg=28.0)
    finalize(accd, coll)
    return S


def build_hall_mortar(coll):
    acc = Acc("KEEP_hall_wall_mortar")
    Lr = hall_L(0.0)
    ns = int(Lr / 0.06)
    tt = np.unique(np.concatenate([np.linspace(0, 1, ns + 1), OT[(OB == 0)]]))
    zs = np.linspace(-0.10, WALL_H, 37)
    T, Z = np.meshgrid(tt, zs, indexing="ij")
    S = T * hall_L(Z)
    nzz = 0.004 * fbm(np.stack([T * 300, Z * 6, np.zeros_like(T)], -1), 2)
    W = hall_map(S.ravel(), Z.ravel(), (-0.004 + nzz).ravel(), Z.ravel())
    nt, nzr = T.shape
    idx = np.arange(nt * nzr).reshape(nt, nzr)
    a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
    quads = np.stack([a, b, c, d], -1).reshape(-1, 4)
    # remove cells in openings or inside the wing
    tcm = 0.5 * (T[:-1, :-1] + T[1:, 1:])
    zcm = 0.5 * (Z[:-1, :-1] + Z[1:, 1:])
    keep = np.ones(tcm.shape, bool)
    for op in OPENINGS:
        k = op["k"]
        xl = (tcm - k / 8.0) * hall_L(zcm)
        keep &= ~open_contains(op, xl, zcm, m=0.03)
    Pc = hall_map((tcm * hall_L(zcm)).ravel(), zcm.ravel(), np.zeros(tcm.size), zcm.ravel())
    keep &= ~in_wing(Pc, margin=0.12, zpad=0.15).reshape(keep.shape)
    acc.add(W, quads[keep.ravel()], "M_mortar")
    # wall top (under the plate) and inner face, floor, ceiling
    ang = np.linspace(0, 2 * np.pi, 9)[:-1] + math.radians(22.5)
    ro = (apo(WALL_H) - 0.01) / math.cos(math.radians(22.5))
    ri = INNER_APO / math.cos(math.radians(22.5))
    for z, r0, r1 in ((WALL_H, ro, ri),):
        V = np.concatenate([np.stack([r0 * np.cos(ang), r0 * np.sin(ang), np.full(8, z)], 1),
                            np.stack([r1 * np.cos(ang), r1 * np.sin(ang), np.full(8, z)], 1)])
        q = np.array([(i, (i + 1) % 8, 8 + (i + 1) % 8, 8 + i) for i in range(8)])
        acc.add(V, q, "M_mortar")
    finalize(acc, coll)


def build_hall_interior(coll):
    """inner wall face, reveals through the wall, floor & ceiling (gives depth through openings)."""
    acc = Acc("KEEP_hall_interior")
    # inner face: plumb octagon at INNER_APO with holes at openings
    for k in range(8):
        half = INNER_APO * TAN22
        xs = np.linspace(-half, half, 23)
        zs = np.linspace(0.12, WALL_H, 18)
        X, Z = np.meshgrid(xs, zs, indexing="ij")
        W = fmap(k, X.ravel(), Z.ravel(), np.zeros(X.size), a_ref=INNER_APO)
        nxx, nzz = X.shape
        idx = np.arange(nxx * nzz).reshape(nxx, nzz)
        quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
        xm = 0.5 * (X[:-1, :-1] + X[1:, 1:])
        zm = 0.5 * (Z[:-1, :-1] + Z[1:, 1:])
        keep = np.ones(xm.shape, bool)
        for op in OPENINGS:
            if op["k"] == k:
                keep &= ~open_contains(op, xm, zm, m=0.16)
        acc.add(W, quads[keep.ravel()], "M_mortar")
    # reveal tubes: from the leaf/frame plane to the inner face, splayed
    for op in OPENINGS:
        k = op["k"]
        o1 = open_outline(op, grow=0.05)
        o2 = open_outline(op, grow=0.20)
        n = len(o1)
        r1 = fmap(k, o1[:, 0], o1[:, 1], np.full(n, -op["depth"] + 0.005))
        r2 = fmap(k, o2[:, 0], o2[:, 1], np.zeros(n), a_ref=INNER_APO)
        V = np.concatenate([r1, r2])
        q = np.array([(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)])
        acc.add(V, q, "M_mortar")
        # behind the dressed stones: short flange from face to leaf plane (inside the stones)
    # floor and ceiling
    ang = np.linspace(0, 2 * np.pi, 9)[:-1] + math.radians(22.5)
    r = INNER_APO / math.cos(math.radians(22.5)) + 0.02
    for z, flip in ((0.12, False), (WALL_H, True)):
        V = np.stack([r * np.cos(ang), r * np.sin(ang), np.full(8, z)], 1)
        f = np.arange(8)[None, :]
        acc.add(V, f[:, ::-1] if flip else f, "M_stone" if z < 1 else "M_timber")
    finalize(acc, coll)


# ==============================================================================================
# GENERIC ORIENTED BOXES (timber members, boards)
# ==============================================================================================
def obox(acc, O, EX, EY, EZ, LX, LY, LZ, r, mat, nx=4, ny=4, nz=4, deform=None, grain_uv=True):
    """Boxes: x in [0,LX] along EX, y in [-LY/2,LY/2] along EY, z in [-LZ/2,LZ/2] along EZ."""
    O = np.atleast_2d(np.asarray(O, float))
    M = len(O)
    bc = lambda a: np.broadcast_to(np.asarray(a, float), (M,)).copy()
    LX, LY, LZ, r = bc(LX), bc(LY), bc(LZ), bc(r)
    r = np.minimum(r, np.minimum(np.minimum(LX, LY), LZ) * 0.45)
    EX = np.broadcast_to(np.asarray(EX, float), (M, 3))
    EY = np.broadcast_to(np.asarray(EY, float), (M, 3))
    EZ = np.broadcast_to(np.asarray(EZ, float), (M, 3))
    X = axn(np.zeros(M), LX, r, nx)
    Y = axn(-LY / 2, LY / 2, r, ny)
    Z = axn(-LZ / 2, LZ / 2, r, nz)
    P, quads = rbox(X, Y, Z, r)
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


def hewn_member(acc, O, EX, EY, EZ, L, wy, wz, rng, mat="M_timber", chamfer=0.025, nf=3, st_len=0.05,
                adze=0.004, adze_period=(0.07, 0.13), lean=(0.0, 0.0), swell=0.0, taper=0.0, wave=0.0,
                checks=(), end_bevel=True, seed=0):
    """hand-hewn square timber along EX from O (length L), section wy (EY) x wz (EZ).
    Adze facets (scalloped, per face), lean (rad, EY/EZ), swell/taper (m), low-freq wave (m),
    modelled checks: dicts face(0:+EY,1:+EZ,2:-EY,3:-EZ), pos(-1..1 across), x0, x1 (0..1), depth, width."""
    O = np.asarray(O, float)
    EX, EY, EZ = [np.asarray(e, float) / np.linalg.norm(e) for e in (EX, EY, EZ)]
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
        sc_d = adze * (0.6 + 0.8 * rng.uniform(0, 1, ns))
        dip = sc_d[:, None] * (1 - (2 * fr[:, None] - 1) ** 2) * (0.7 + 0.3 * np.cos((acr[None, :] - 0.5) * np.pi))
        off += np.where(fid[None, :] == fi, -dip, 0.0)
        # occasional broad flat-hewn facet (shallow plane tilted across the face)
        tilt = rng.normal(0, adze * 0.8)
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
        along = np.array([b_ for (a_, b_, n_) in corners for _ in [0]])  # unused placeholder
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
    caps = [np.arange(m)[None, :], ((ns - 1) * m + np.arange(m)[::-1])[None, :]]
    per = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1))])[:m]
    uv = np.stack([np.repeat(xs, m), np.tile(per, ns)], -1)
    acc.add(V.reshape(-1, 3), [quads] + caps, mat, uv=uv)


def peg(acc, p, axis, rad=0.014, proud=0.016, embed=0.03, rng=None):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    up = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0, 0])
    path = np.array([p - axis * embed, p + axis * (proud - 0.004), p + axis * proud])
    prof = np.stack([prof_circle(rad, 8), prof_circle(rad, 8), prof_circle(rad * 0.7, 8)])
    V, F = sweep(path, up, prof)
    acc.add(V, F, "M_timber")


def nail_heads(acc, P, normal, rad=0.009, h=0.006, mat="M_iron"):
    """domed nail heads at points P (N,3) on a surface with normal."""
    P = np.atleast_2d(P)
    normal = np.asarray(normal, float)
    normal = normal / np.linalg.norm(normal)
    for p in P:
        prof = [(rad, -0.003), (rad, 0.0), (rad * 0.85, h * 0.6), (rad * 0.45, h * 0.95), (0.0, h)]
        V, F = lathe(prof, 8)
        # orient z->normal
        z = normal
        x = np.cross((0, 0, 1.0), z) if abs(z[2]) < 0.95 else np.array([1.0, 0, 0])
        x = x / np.linalg.norm(x)
        y = np.cross(z, x)
        W = p + V[:, 0:1] * x + V[:, 1:2] * y + V[:, 2:3] * z
        acc.add(W, F, mat)


# ==============================================================================================
# OCTAGONAL BELL-CAST ROOF SURFACE
# ==============================================================================================
class OctRoof:
    def __init__(self, cx, cy, p_lip, z_lip, d_pts, a_pts, p_min, kick=0.0, kick_len=1.0, wave=0.0,
                 sag=0.0, seed=1, rot_deg=0.0):
        self.c = np.array([cx, cy], float)
        self.p_lip = p_lip
        d = np.linspace(0, p_lip - p_min, 600)
        th = np.radians(np.interp(d, d_pts, a_pts))
        tz = np.tan(th)
        z = z_lip + np.concatenate([[0], np.cumsum(0.5 * (tz[1:] + tz[:-1]) * np.diff(d))])
        m = np.concatenate([[0], np.cumsum(np.sqrt(1 + (0.5 * (tz[1:] + tz[:-1])) ** 2) * np.diff(d))])
        self.Pp, self.Zp, self.Mp = p_lip - d, z, m
        self.kick, self.kick_len, self.wave, self.sag, self.seed = kick, kick_len, wave, sag, seed
        self.D = p_lip - p_min
        self.rot = math.radians(rot_deg)
        self.phi = [self.rot + math.radians(45 * k) for k in range(8)]

    def zb(self, p):
        return np.interp(-np.asarray(p, float), -self.Pp, self.Zp)

    def p_of_m(self, m):
        return np.interp(m, self.Mp, self.Pp)

    def m_of_p(self, p):
        return np.interp(-np.asarray(p, float), -self.Pp, self.Mp)

    def surf(self, k, x, p):
        k = np.asarray(k).astype(np.int64)
        x = np.asarray(x, float)
        p = np.asarray(p, float)
        phi = np.asarray(self.phi)[k]
        nx_, ny_ = np.cos(phi), np.sin(phi)
        X = self.c[0] + p * nx_ - x * ny_
        Y = self.c[1] + p * ny_ + x * nx_
        d = self.p_lip - p
        xr = np.clip(np.abs(x) / np.maximum(p * TAN22, 1e-3), 0, 1)
        z = self.zb(p)
        z = z + self.kick * xr ** 3 * np.clip(1 - d / self.kick_len, 0, 1) ** 2
        ang = phi + np.arctan2(x, np.maximum(p, 1e-3))
        z = z + self.wave * n1(ang * 2.2, self.seed) * np.clip(1 - d / (0.8 * self.D), 0.2, 1)
        z = z - self.sag * (1 - xr ** 2) * np.sin(np.pi * np.clip(d / self.D, 0, 1))
        return np.stack([X, Y, z], -1)

    def world(self, k, x, p, h):
        e = 1e-3
        S0 = self.surf(k, x, p)
        dx = self.surf(k, np.asarray(x) + e, p) - S0
        dp = self.surf(k, x, np.asarray(p) - e) - S0      # upslope
        N = np.cross(dx, dp)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        return S0 + np.asarray(h, float)[..., None] * N


def covering_boards(roof, acc, mat, rng, m0, m1, expo, W, t, lens, gap, nx=6, nm=5, base_h=0.0,
                    cull=None, p_floor=None, frac_missing=0.02, frac_slip=0.025, curl=0.0, rot_sd=0.02,
                    width_var=None, round_r=0.008, jit_m=0.012):
    """Horizontal courses of boards/shingles on an OctRoof between slope coords m0..m1."""
    recs = []
    for k in range(8):
        mb = m0
        ci = 0
        while mb < m1:
            p_b = float(roof.p_of_m(mb + 0.5 * W))
            xh = p_b * TAN22 + 0.06
            x = -xh - rng.uniform(0, lens[1] * 0.6)
            while x < xh:
                L = rng.uniform(*lens)
                if width_var is not None:
                    L = float(np.clip(rng.normal(width_var[0], width_var[1]), lens[0], lens[1]))
                x0, x1 = x, x + L - gap
                x = x + L
                if x1 < -xh or x0 > xh:
                    continue
                mbb = mb + rng.normal(0, jit_m)
                lift = rng.normal(0, 0.004 + jit_m * 0.2)
                slip = 0.0
                u = rng.uniform()
                if u < frac_missing and ci > 0:
                    continue
                if u < frac_missing + frac_slip:
                    slip = rng.uniform(0.04, 0.10)
                    lift += 0.006
                recs.append((k, x0, x1, mbb - slip, rng.normal(0, rot_sd), lift, ci, t * rng.uniform(0.85, 1.15)))
            mb += expo * rng.uniform(0.96, 1.04)
            ci += 1
    R = np.array(recs)
    k = R[:, 0].astype(int)
    x0, x1, mb, rot, lift, ci, tt = R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 6], R[:, 7]
    if cull is not None:
        pc = roof.p_of_m(mb + W * 0.5)
        C = roof.world(k, 0.5 * (x0 + x1), pc, np.full(len(k), base_h + t))
        keep = ~cull(C)
        k, x0, x1, mb, rot, lift, ci, tt = [a[keep] for a in (k, x0, x1, mb, rot, lift, ci, tt)]
    M = len(k)
    rr = np.full(M, round_r)
    X = axn(x0, x1, rr, nx)
    Y = axn(mb, mb + W, rr, nm)
    Z = np.stack([np.zeros(M), tt - rr, tt], 1)
    P, quads = rbox(X, Y, Z, rr, skip_back=True, round_back=False)
    x, m, h = P[..., 0], P[..., 1], P[..., 2]
    xc = 0.5 * (x0 + x1)[:, None]
    mc = (mb + 0.5 * W)[:, None]
    xr, mr = rot2(x - xc, m - mc, rot[:, None])
    x, m = xr + xc, mr + mc
    fr = np.clip((m - mb[:, None]) / W, 0, 1)
    hl = h * (1 - 0.45 * fr) + (tt[:, None] * 0.95 + lift[:, None]) * (1 - fr)
    if curl:
        hl = hl + curl * np.clip(1 - ci[:, None] / 3.0, 0, 1) * (1 - fr) ** 2 * ((x - xc) / (0.5 * (x1 - x0))[:, None]) ** 2
    p = roof.p_of_m(m)
    if p_floor is not None:
        p = np.maximum(p, p_floor)
    xh = p * TAN22 + 0.004
    x = np.clip(x, -xh, xh)
    W3 = roof.world(np.broadcast_to(k[:, None], x.shape), x, p, hl + base_h)
    uv = np.stack([x, m], -1).reshape(-1, 2)
    acc.add(W3.reshape(-1, 3), inst_faces(quads, M, P.shape[1]), mat, uv=uv)
    return M


def hip_boards(roof, acc, mat, rng, p_lo, p_hi, w, t, h0, piece=(0.8, 1.3), cull=None):
    """Saddle boards along the 8 hips from p_lo (lip) up to p_hi."""
    recs = []
    for k in range(8):
        for side in (0, 1):
            p = p_lo + 0.02
            while p > p_hi + 0.05:
                L = rng.uniform(*piece)
                pa, pb = p, max(p - L * 0.75, p_hi)
                recs.append((k, side, pa, pb, w * rng.uniform(0.9, 1.1), t, rng.normal(0, 0.004)))
                p = pb + 0.03
    R = np.array(recs)
    M = len(R)
    k, side = R[:, 0].astype(int), R[:, 1].astype(int)
    pa, pb, ww, tt, lift = R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 6]
    rr = np.full(M, 0.007)
    X = axn(pb, pa, rr, 8)
    Y = axn(np.zeros(M), ww, rr, 4)
    Z = axn(np.zeros(M), tt, rr, 3)
    P, quads = rbox(X, Y, Z, rr)
    p, a, h = P[..., 0], P[..., 1], P[..., 2]
    sgn = np.where(side == 0, 1.0, -1.0)[:, None]
    # side 0 on facet k (x = +hip), side 1 on facet k+1 (x = -hip); side 1 sits higher & overlaps
    kk = np.where(side == 0, k, (k + 1) % 8)[:, None]
    x = sgn * (p * TAN22 - a + np.where(side == 1, -0.025, 0.0)[:, None])
    hh = h0 + h + lift[:, None] + np.where(side == 1, tt * 0.6, 0.0)[:, None] + 0.02 * a / ww[:, None]
    W3 = roof.world(np.broadcast_to(kk, x.shape), x, p, hh)
    if cull is not None:
        keep = ~cull(W3.mean(1))
        W3 = W3[keep]
        P = P[keep]
        M = len(W3)
    acc.add(W3.reshape(-1, 3), inst_faces(quads, M, P.shape[1]), mat,
            uv=np.stack([P[..., 0], P[..., 1]], -1).reshape(-1, 2))


def eave_structure(roof, acc_r, acc_s, acc_f, rng, p_wall, z_plate_top, sheath_t, n_raft, rw, rd_tip,
                   cull=None, fascia_h=0.18, fascia_t=0.04, soffit_w=(0.17, 0.24), mat_r="M_timber", scribe=None,
                   fascia_joint=(2.5, 4.0), fascia_wave=0.0):
    """rafters (incl. jacks & hips), soffit/sheathing boards and fascia under an OctRoof eave."""
    pl = roof.p_lip
    sp = 2 * p_wall * TAN22 / n_raft
    # common & jack rafters
    jmax = int(math.ceil(pl * TAN22 / sp)) + 1
    for k in range(8):
        for j in range(-jmax, jmax + 1):
            xj = (j + 0.5) * sp if n_raft % 2 == 0 else j * sp
            if abs(xj) > pl * TAN22 - 0.12:
                continue
            p_start = max(p_wall - 0.25, abs(xj) / TAN22 + 0.07)
            p_end = pl - fascia_t - 0.005
            if p_end - p_start < 0.15:
                continue
            _rafter(roof, acc_r, rng, k, xj, p_start, p_end, p_wall, z_plate_top, sheath_t, rw, rd_tip, False, cull, mat_r)
        # hip rafter
        _rafter(roof, acc_r, rng, k, None, p_wall - 0.25, pl - fascia_t - 0.02, p_wall, z_plate_top, sheath_t,
                rw * 1.2, rd_tip * 1.1, True, cull, mat_r)
    # soffit / sheathing boards (visible from below between rafters)
    m_wall = float(roof.m_of_p(p_wall - 0.3))
    m = -0.005
    recs = []
    while m < m_wall:
        wd = rng.uniform(*soffit_w)
        for k in range(8):
            recs.append((k, m, min(wd - 0.006, m_wall - m + 0.02)))
        m += wd
    R = np.array(recs)
    M = len(R)
    k = R[:, 0].astype(int)
    m0, wd = R[:, 1], R[:, 2]
    rr = np.full(M, 0.004)
    xh = pl * TAN22 + 0.05
    X = axn(np.full(M, -xh), np.full(M, xh), rr, 12)
    Y = axn(m0, m0 + wd, rr, 4)
    Z = axn(np.full(M, -sheath_t), np.zeros(M), rr, 3)
    P, quads = rbox(X, Y, Z, rr)
    x, mm, h = P[..., 0], P[..., 1], P[..., 2]
    p = roof.p_of_m(mm)
    x = np.clip(x, -p * TAN22, p * TAN22)
    W3 = roof.world(np.broadcast_to(k[:, None], x.shape), x, p, h)
    if cull is not None:
        keep = ~cull(W3.mean(1))
        W3, P = W3[keep], P[keep]
    acc_s.add(W3.reshape(-1, 3), inst_faces(quads, len(W3), P.shape[1]), "M_timber",
              uv=np.stack([P[..., 0], P[..., 1]], -1).reshape(-1, 2))
    # fascia: boards at the lip, mitred at the hips, following the kicked eave; hand-fitted lengths with butt /
    # scarf joints every 2.5-4 m, low-frequency wave; where an adjoining roof (wing thatch) rises over the eave the
    # board is scribed down onto that surface and ends there (no floating cut ends)
    for k in range(8):
        n = 40
        xh = pl * TAN22
        xs = np.linspace(-xh, xh, n)
        # joints along this facet (absolute x positions)
        cuts = []
        xj = -xh + rng.uniform(0.6, 1.8)
        while xj < xh - 0.6:
            cuts.append(xj)
            xj += rng.uniform(*fascia_joint)
        xs = np.unique(np.concatenate([xs, np.array(cuts) - 0.004, np.array(cuts) + 0.004]))
        n = len(xs)
        pf0, pf1 = pl - fascia_t, pl + 0.002
        top = roof.world(np.full(n, k), xs, np.full(n, pl), np.zeros(n))[:, 2] + 0.004
        seg_id = np.searchsorted(np.array(cuts), xs)
        wv = fascia_wave * n1(xs * 0.9 + k * 3.1, 77 + k) + 0.006 * (seg_id % 2) * fascia_wave / 0.02 \
            + 0.004 * n1(seg_id * 1.7 + k, 91) * (fascia_wave > 0)
        V = []
        for pp in (pf0, pf1):
            for zoff in (-fascia_h, 0.0):
                xx = np.clip(xs, -pp * TAN22, pp * TAN22)
                S = roof.surf(np.full(n, k), xx, np.full(n, pp))
                S[:, 2] = top + zoff + wv
                V.append(S)
        V = np.stack(V, 1)  # n, 4 (inner-bot, inner-top, outer-bot, outer-top)
        if scribe is None:
            if cull is not None and cull(V.reshape(-1, 3).mean(0)[None])[0]:
                continue
            keep = np.ones(n, bool)
        else:
            zt = scribe(V[:, 2, :2])
            keep = zt < V[:, 1, 2] - 0.03
            bot = np.maximum(V[:, [0, 2], 2], zt[:, None])
            V[:, 0, 2], V[:, 2, 2] = bot[:, 0], bot[:, 1]
        # split into board runs at joints and at buried sections
        brk = np.zeros(n, bool)
        for c in cuts:
            brk |= np.isclose(xs, c + 0.004)
        runs, cur = [], []
        for i in range(n):
            if not keep[i] or brk[i]:
                if len(cur) >= 2:
                    runs.append(cur)
                cur = [i] if keep[i] else []
            else:
                cur.append(i)
        if len(cur) >= 2:
            runs.append(cur)
        ring = [0, 2, 3, 1]
        for run in runs:
            Vr = V[run][:, ring, :]
            m_ = len(run)
            i = np.arange(m_ - 1)[:, None]
            jj = np.arange(4)[None, :]
            a = i * 4 + jj
            b = i * 4 + (jj + 1) % 4
            quads = np.stack([a, b, b + 4, a + 4], -1).reshape(-1, 4)
            caps = [np.array([[0, 3, 2, 1]]), ((m_ - 1) * 4 + np.array([[0, 1, 2, 3]]))]
            acc_f.add(Vr.reshape(-1, 3), [quads] + caps, "M_timber",
                      uv=np.stack([np.repeat(xs[run], 4), np.tile([0, 0.04, 0.22, 0.18], m_)], -1))


def _rafter(roof, acc, rng, k, xj, p0, p1, p_wall, z_plate, sheath_t, rw, rd_tip, hip, cull, mat):
    n = 12
    us = np.linspace(0, 1, n)
    M = 1
    r = 0.016
    X = axn(np.zeros(1), np.ones(1), np.array([0.03]), 8)
    Y = ax4(np.array([rw / 2]), np.array([r]))
    Z = ax4(np.array([0.5]), np.array([0.06]))
    P, quads = rbox(X, Y, Z, np.array([r]))
    P = P[0]
    u, a, v = P[:, 0], P[:, 1], P[:, 2] + 0.5   # v in [0,1]
    p = p0 + (p1 - p0) * u
    if hip:
        x = p * TAN22
        hipdir = np.array([math.cos(roof.phi[k] + math.radians(22.5)), math.sin(roof.phi[k] + math.radians(22.5))])
        across = np.array([-hipdir[1], hipdir[0]])
        top = roof.world(np.full_like(p, k), x, p, np.full_like(p, -sheath_t))
        top = top - 0.012 * np.array([0, 0, 1.0])
        xy = roof.surf(np.full_like(p, k), x, p)[:, :2] + a[:, None] * across[None]
    else:
        x = np.full_like(p, xj)
        top = roof.world(np.full_like(p, k), x + a, p, np.full_like(p, -sheath_t))
        xy = top[:, :2]
    ztop = top[:, 2]
    # depth: tip rd_tip, deepening (haunched sprocket) to bear on the plate at the wall line
    z_tip_bot = ztop - rd_tip
    pw = p_wall + 0.06
    wl = np.clip((roof.p_lip - p) / max(roof.p_lip - pw, 1e-3), 0, 1)
    # smooth concave (haunched) underside from the tip down to the plate bearing
    zb_plate = np.full_like(p, z_plate)
    blend = wl ** 2.2
    zbot = np.where(p < pw, np.minimum(zb_plate, z_tip_bot), z_tip_bot * (1 - blend) + zb_plate * blend)
    zbot = np.minimum(zbot, ztop - rd_tip)
    W = np.zeros((len(P), 3))
    W[:, :2] = xy
    W[:, 2] = zbot + v * (ztop - zbot)
    if cull is not None and cull(W.mean(0)[None])[0]:
        return
    acc.add(W, quads, mat, uv=np.stack([u * (p1 - p0), a + v * 0.1], -1))


# ==============================================================================================
# HALL TIMBER FRAME: pedestals, posts, knee braces, eave plate
# ==============================================================================================
R_POST = 4.30
PLATE_APO = 3.93
PLATE_W, PLATE_H = 0.25, 0.30
PLATE_TOP = WALL_H + PLATE_H
RPLATE_H = 0.20
RAFTER_SEAT = PLATE_TOP + RPLATE_H


def corner_dir(c):
    a = FPHI[c] + math.radians(22.5)        # corner between facet c and c+1
    return np.array([math.cos(a), math.sin(a)]), a


def build_hall_frame(coll):
    rng = np.random.default_rng(202)
    acc_p = Acc("KEEP_hall_posts")
    acc_b = Acc("KEEP_hall_post_bases")
    acc_k = Acc("KEEP_hall_knee_braces")
    acc_pl = Acc("KEEP_hall_eave_plate")
    up = np.array([0, 0, 1.0])
    for c in range(8):
        d, a = corner_dir(c)
        P0 = np.array([d[0] * R_POST, d[1] * R_POST, 0.0])
        if in_wing(P0 + np.array([0, 0, 1.5]), margin=-0.3, zpad=0.0):
            continue
        ex = np.array([-math.sin(a), math.cos(a), 0.0])     # tangential
        ey = np.array([d[0], d[1], 0.0])                    # radial
        # pedestal: dressed block with splayed foot, tooled faces, chipped arrises, set ~1-2 deg out of square
        hp = 0.35
        yaw = math.radians(rng.uniform(-2.0, 2.0))
        exr = ex * math.cos(yaw) + ey * math.sin(yaw)
        eyr = -ex * math.sin(yaw) + ey * math.cos(yaw)
        chips = rng.uniform(0, 1, (4, 4))
        psd = rng.uniform(0, 50)

        def ped_def(P, chips=chips, psd=psd):
            z = P[..., 0]
            s = 1 + 0.16 * np.clip(1 - z / 0.12, 0, 1) ** 1.5
            P = P.copy()
            # tooled faces: 2-5 mm undulation + pitched face inside a drafted margin
            und = 0.0035 * fbm(np.stack([P[..., 0] * 9 + psd, P[..., 1] * 9, P[..., 2] * 9], -1), 2)
            ry, rz = np.abs(P[..., 1]) / 0.24, np.abs(P[..., 2]) / 0.24
            on_y = ry > rz
            marg = np.clip((np.minimum(np.where(on_y, rz, ry), 1 - z / 0.4) - 0.0) * 0.24 / 0.025, 0, 1)
            nud = und + 0.002 * marg
            P[..., 1] += np.where(on_y, np.sign(P[..., 1]) * nud, 0.0)
            P[..., 2] += np.where(~on_y, np.sign(P[..., 2]) * nud, 0.0)
            # arris chips (1-3 cm), mostly on the vertical arrises and the top edge
            for c_ in chips:
                sy, sz = (1 if c_[0] < 0.5 else -1), (1 if c_[1] < 0.5 else -1)
                zc_ = 0.08 + 0.3 * c_[2]
                rad = 0.012 + 0.02 * c_[3]
                d = np.sqrt((P[..., 1] - sy * 0.24) ** 2 + (P[..., 2] - sz * 0.24) ** 2 + (z - zc_) ** 2)
                dep = rad * 0.6 * np.clip(1 - d / rad, 0, 1) ** 1.2
                P[..., 1] -= sy * dep
                P[..., 2] -= sz * dep
            P[..., 1] *= s
            P[..., 2] *= s
            return P
        obox(acc_b, (P0 - np.array([0, 0, 0.05]))[None], up, exr, eyr, hp + 0.05, 0.48, 0.48, 0.03, "M_stone_dressed",
             nx=10, ny=12, nz=12, deform=ped_def)
        # post: hand-hewn, +-1 deg lean, +-1 cm swell/taper, adze facets; modelled checks on the posts that
        # flank the door (c=2, 3) and the post by the SW window (c=1)
        checks = []
        if c in (1, 2, 3):
            checks.append(dict(face=1, pos=rng.uniform(-0.35, 0.35), x0=rng.uniform(0.08, 0.2), x1=rng.uniform(0.6, 0.85),
                               depth=rng.uniform(0.022, 0.032), width=rng.uniform(0.012, 0.018)))
            if c != 1:
                checks.append(dict(face=0 if c == 2 else 2, pos=rng.uniform(-0.3, 0.3), x0=rng.uniform(0.35, 0.5),
                                   x1=rng.uniform(0.8, 0.95), depth=rng.uniform(0.016, 0.024),
                                   width=rng.uniform(0.009, 0.013)))
        lean = np.clip(rng.normal(0, 0.009, 2), -0.0175, 0.0175)
        hewn_member(acc_p, P0 + np.array([0, 0, hp - 0.01]), up, ex, ey, WALL_H - hp + 0.02, 0.28, 0.28, rng,
                    chamfer=0.03, nf=6, st_len=0.035, adze=0.008, lean=tuple(lean), swell=rng.uniform(-0.01, 0.01),
                    taper=rng.uniform(0.0, 0.01), wave=0.004, checks=checks, seed=40 + c)
        # knee braces into the two adjacent plate runs
        for side, fk in ((-1, c), (1, (c + 1) % 8)):
            t = np.array([FT[fk][0], FT[fk][1], 0.0])
            nk = np.array([FN[fk][0], FN[fk][1], 0.0])
            base = np.array([d[0] * R_POST, d[1] * R_POST, 0.0])
            base = base - nk * (np.dot(base, nk) - (PLATE_APO + 0.02))
            dirv = -t if side < 0 else t
            pa = base + dirv * 0.12 + np.array([0, 0, 2.78])
            pc = base + dirv * 0.12 + np.array([0, 0, WALL_H - 0.04])
            pb = base + dirv * 0.56 + np.array([0, 0, WALL_H + 0.02])
            us = np.linspace(0, 1, 14)
            ctrl = pc * 0.85 + 0.15 * (pa + pb) * 0.5
            path = ((1 - us) ** 2)[:, None] * pa + (2 * us * (1 - us))[:, None] * ctrl + (us ** 2)[:, None] * pb
            path[0] -= dirv * 0.05
            path[-1] += np.array([0, 0, 0.05])
            wob = 0.006 * np.sin(us * 3.1 + c)
            path = path + wob[:, None] * nk
            # chunky Y-bracket arm, slightly thicker at the root, adze-wobbled
            nn_ = len(us)
            profs = np.stack([prof_rect(0.17 * (1.12 - 0.12 * u_), 0.16 + 0.01 * math.sin(7 * u_ + c), 0.024) for u_ in us])
            V, F = sweep(path, nk, profs)
            acc_k.add(V, F, "M_timber")
            peg(acc_k, base + dirv * 0.09 + np.array([0, 0, 2.86]) + nk * 0.165, nk)
            peg(acc_k, base + dirv * 0.46 + np.array([0, 0, WALL_H + 0.10]) + nk * (PLATE_W / 2 + 0.02), nk)
    # eave plate: 8 runs, lap-jointed corners with projecting ends
    for k in range(8):
        n, t = FN[k], FT[k]
        half = PLATE_APO * TAN22
        cA = n * PLATE_APO - t * half
        cB = n * PLATE_APO + t * half
        if in_wing(np.array([*(n * PLATE_APO), 3.5]), margin=-0.4, zpad=0.0):
            continue
        dz = rng.uniform(-0.004, 0.004)
        up_half = (k % 2 == 0)
        tv = np.array([t[0], t[1], 0.0])
        ey = np.array([n[0], n[1], 0.0])

        def pl_def(P):
            P = P.copy()
            P[..., 2] += 0.006 * np.sin(P[..., 0] * 1.3 + k)
            return P
        A3 = np.array([cA[0], cA[1], WALL_H + PLATE_H / 2 + dz])
        hewn_member(acc_pl, A3 + tv * 0.02, tv, ey, np.array([0, 0, 1.0]), 2 * half - 0.04, PLATE_W, PLATE_H, rng,
                    chamfer=0.025, nf=3, st_len=0.11, adze=0.004, wave=0.007, seed=60 + k,
                    checks=[dict(face=1, pos=rng.uniform(-0.3, 0.3), x0=0.15, x1=0.7, depth=0.012, width=0.006)]
                    if k in (2, 3, 4) else ())
        for end, sgn in ((cA, -1), (cB, 1)):
            zoff = PLATE_H / 4 if up_half else -PLATE_H / 4
            E3 = np.array([end[0], end[1], WALL_H + PLATE_H / 2 + zoff + dz])
            ext = 0.17
            o = E3 + tv * (-0.04) if sgn > 0 else E3 - tv * ext
            obox(acc_pl, o[None], tv, ey, np.array([0, 0, 1.0]), ext + 0.04, PLATE_W - 0.004, PLATE_H / 2 - 0.004,
                 0.02, "M_timber", nx=4)
            if sgn > 0:
                peg(acc_pl, E3 + np.array([0, 0, (PLATE_H / 4) if up_half else -(PLATE_H / 4)]),
                    np.array([0, 0, 1.0 if up_half else -1.0]))
    # raising plate (rafter plate) on top of the eave plate, scarf-jointed runs with pegs
    for k in range(8):
        n, t = FN[k], FT[k]
        if in_wing(np.array([*(n * PLATE_APO), 3.5]), margin=-0.4, zpad=0.0):
            continue
        half = (PLATE_APO + 0.02) * TAN22
        tv = np.array([t[0], t[1], 0.0])
        ey = np.array([n[0], n[1], 0.0])
        c0 = n * (PLATE_APO + 0.02) - t * (half + 0.06)
        o = np.array([c0[0], c0[1], PLATE_TOP + RPLATE_H / 2 + rng.uniform(-0.003, 0.003)])
        hewn_member(acc_pl, o, tv, ey, np.array([0, 0, 1.0]), 2 * half + 0.12, 0.21, RPLATE_H, rng, chamfer=0.02,
                    nf=2, st_len=0.13, adze=0.0035, wave=0.006, seed=70 + k)
        mid = n * (PLATE_APO + 0.02 + 0.105) + t * rng.uniform(-0.4, 0.4)
        peg(acc_pl, np.array([mid[0], mid[1], PLATE_TOP + 0.10]), ey)
    for a in (acc_b, acc_p, acc_k, acc_pl):
        finalize(a, coll)


# ==============================================================================================
# SKIRT ROOF (tier 1)
# ==============================================================================================
SKIRT = OctRoof(0.0, 0.0, p_lip=5.25, z_lip=3.735, d_pts=[0, 0.4, 0.8, 1.2, 3.25],
                a_pts=[25, 31, 37, 38, 39], p_min=2.0, kick=0.022, kick_len=0.8, wave=0.022,
                sag=0.03, seed=3)
SKIRT_SHEATH = 0.025
COLLAR_P = 3.62


def wing_roof_zone(C, pad=0.02):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    inside = (x > WX_W - W_OVH - 0.05) & (x < WX_E + W_OVH + 0.05) & (y > WY_S - W_OVH - 0.05) & (y < WY_N + W_OVH + 0.05)
    zs, pp = skirt_z_at(x, y)
    thatch_on_top = wing_top(x, y) > zs + 0.07
    return inside & (z < wing_top(x, y) + pad) & thatch_on_top


def skirt_z_at(x, y):
    """height of the skirt sheathing surface above plan point (x,y) (approx, no noise)."""
    ang = np.arctan2(y, x)
    k = np.round(ang / (np.pi / 4)).astype(int) % 8
    phi = k * np.pi / 4
    p = x * np.cos(phi) + y * np.sin(phi)
    return SKIRT.zb(p), p


def build_skirt(coll):
    rng = np.random.default_rng(303)
    acc = Acc("KEEP_roof_skirt_boards")
    acc_h = Acc("KEEP_roof_skirt_hips")
    acc_r = Acc("KEEP_roof_skirt_structure")
    cull = lambda C: wing_roof_zone(C, 0.03)
    m_top = float(SKIRT.m_of_p(3.25))
    n = covering_boards(SKIRT, acc, "M_roof_shingle", rng, -0.05, m_top, expo=0.215, W=0.47, t=0.032,
                        lens=(0.6, 1.2), gap=0.009, nx=8, nm=5, base_h=0.0, cull=cull, frac_missing=0.015,
                        frac_slip=0.025, curl=0.012, rot_sd=0.012)
    log("  skirt boards", n)
    hip_boards(SKIRT, acc_h, "M_roof_shingle", rng, SKIRT.p_lip + 0.03, 3.3, 0.13, 0.03, 0.065, cull=cull)
    def scribe(XY):
        x, y = XY[:, 0], XY[:, 1]
        inside = (x > WX_W - W_OVH) & (x < WX_E + W_OVH) & (y > WY_S - W_OVH) & (y < WY_N + W_OVH)
        return np.where(inside, wing_under(x, y) + TH_V_MIN + 0.02, -10.0)
    eave_structure(SKIRT, acc_r, acc_r, acc_r, rng, p_wall=PLATE_APO + PLATE_W / 2, z_plate_top=RAFTER_SEAT,
                   sheath_t=SKIRT_SHEATH, n_raft=6, rw=0.10, rd_tip=0.14,
                   cull=lambda C: wing_roof_zone(C, 0.05) | in_wing(C, margin=-0.6, zpad=-0.5), scribe=scribe,
                   fascia_wave=0.02)
    finalize(acc, coll)
    finalize(acc_h, coll)
    finalize(acc_r, coll)


# ==============================================================================================
# SHAKE COLLAR (tier 2) and STONE CONE (tier 3)
# ==============================================================================================
CONE_Z = np.array([4.4, 5.2, 6.0, 6.6, 7.35, 8.2, 9.0, 9.6])
CONE_R = np.array([3.12, 2.92, 2.68, 2.30, 1.90, 1.56, 1.36, 1.25])
COLLAR_TOP_Z, COLLAR_TOP_R = 6.02, 3.02


def cone_r(z):
    from_z = np.asarray(z, float)
    # smooth monotone interpolation (cubic through points via fine linear table)
    return np.interp(from_z, CONE_ZF, CONE_RF)


def _smooth_profile():
    zf = np.linspace(CONE_Z[0], CONE_Z[-1], 400)
    rf = np.interp(zf, CONE_Z, CONE_R)
    for _ in range(40):
        rf[1:-1] = 0.25 * rf[:-2] + 0.5 * rf[1:-1] + 0.25 * rf[2:]
    return zf, rf


CONE_ZF, CONE_RF = _smooth_profile()
_dz = np.diff(CONE_ZF)
_dr = np.diff(CONE_RF)
CONE_MF = np.concatenate([[0], np.cumsum(np.sqrt(_dz ** 2 + _dr ** 2))])
CONE_DRDZ = np.gradient(CONE_RF, CONE_ZF)


def cone_map_factory(z_base_m=0.0):
    def mapfn(s, m, w, mc):
        z = np.interp(m, CONE_MF, CONE_ZF)
        zc = np.interp(mc, CONE_MF, CONE_ZF)
        r = np.interp(z, CONE_ZF, CONE_RF)
        rc = np.interp(zc, CONE_ZF, CONE_RF)
        th = s / rc
        drdz = np.interp(z, CONE_ZF, CONE_DRDZ)
        nr = 1 / np.sqrt(1 + drdz ** 2)
        nzz = -drdz * nr
        R = r + w * nr
        return np.stack([R * np.cos(th), R * np.sin(th), z + w * nzz], -1)
    return mapfn


def build_cone(coll):
    rng = np.random.default_rng(404)
    acc = Acc("KEEP_cone_stones")
    m0 = float(np.interp(5.62, CONE_ZF, CONE_MF))
    m1 = float(np.interp(9.585, CONE_ZF, CONE_MF))
    cfg = dict(seed=11, footing=None, ch=(0.07, 0.13), p_tall=0.04, len=(0.12, 0.34), foot_len=(0.3, 0.5),
               joint=(0.008, 0.016), front=(0.008, 0.042), foot_proj=(0, 0), bevel=(0.005, 0.025),
               pillow=(0.004, 0.014), tilt=0.009, rot=0.02, p_double=0.05, p_long=0.02, back=0.08, bed_amp=0.018)
    srange = lambda mm: [(0.0, 2 * math.pi * float(np.interp(np.interp(mm, CONE_MF, CONE_ZF), CONE_ZF, CONE_RF)))]
    S = layout_wall(rng, srange, m0, m1, lambda a, b, c: [], cfg)
    pins, _, _ = fill_voids(S, srange, lambda a, b, c: [], m0, m1, rng, cfg, label="cone")
    S = cat_stones(S, pins)
    log("  cone stones:", len(S["sc"]))
    small = (S["hx"] < 0.045) & (S["hy"] < 0.045)
    # budget: one side segment + chamfer band (the cone is never seen closer than ~6 m)
    build_stones(acc, filt(S, ~small), cone_map_factory(), "M_stone", rng, rough=1.35, noise_amp=0.009, nz2=True)
    build_stones(acc, filt(S, small), cone_map_factory(), "M_stone", rng, rough=0.9, nxy=4, noise_amp=0.005, nz2=True)
    finalize(acc, coll, smooth_deg=28.0)
    # mortar body (lathe) with noise
    accm = Acc("KEEP_cone_mortar")
    zs = np.linspace(4.5, 9.62, 60)
    seg = 96
    rr = np.interp(zs, CONE_ZF, CONE_RF) - 0.004
    V, F = lathe(np.stack([rr, zs], 1), seg, cap_top=False, cap_bottom=False)
    th = np.arctan2(V[:, 1], V[:, 0])
    nz_ = 0.006 * fbm(np.stack([np.cos(th) * 8, np.sin(th) * 8, V[:, 2] * 4], -1), 2)
    rad = np.hypot(V[:, 0], V[:, 1]) + nz_
    V[:, 0] = rad * np.cos(th)
    V[:, 1] = rad * np.sin(th)
    accm.add(V, F, "M_mortar")
    finalize(accm, coll)


def build_collar(coll):
    rng = np.random.default_rng(505)
    acc = Acc("KEEP_roof_collar_shakes")
    recs = []
    for layer in (0, 1):
        th = rng.uniform(0, 0.05)
        while th < 2 * math.pi - 0.02:
            w = rng.uniform(0.12, 0.22)
            # butt radius: octagonal foot line at apothem COLLAR_P on the skirt
            kf = int(np.round(th / (math.pi / 4))) % 8
            delta = th - kf * math.pi / 4
            delta = (delta + math.pi) % (2 * math.pi) - math.pi
            rb = COLLAR_P / math.cos(delta)
            dth = w / rb
            thc = th + dth / 2
            recs.append((layer, thc, w, rb, rng.uniform(0.03, 0.045), float(np.clip(rng.normal(0, 0.035), -0.06, 0.06)),
                         rng.uniform(0.05, 0.25) * (1.0 if layer else 0.75), rng.integers(0, 4), rng.normal(0, 0.008)))
            th += dth * (1.0 if layer else 0.97) + rng.uniform(0.0, 0.004)
    R = np.array(recs, float)
    M = len(R)
    layer, thc, w, rb, tb, butt, tip, kind, twist = [R[:, i] for i in range(9)]
    kind = kind.astype(int)
    xb, yb = rb * np.cos(thc), rb * np.sin(thc)
    zsk, _ = skirt_z_at(xb, yb)
    zb = zsk + 0.13 + butt + layer * 0.035
    B = np.stack([xb, yb, zb], 1)
    rt = COLLAR_TOP_R + layer * 0.03
    T = np.stack([rt * np.cos(thc), rt * np.sin(thc), np.full(M, COLLAR_TOP_Z)], 1)
    D = T - B
    Lb = np.linalg.norm(D, axis=1)
    D /= Lb[:, None]
    L = Lb + tip
    # shakes whose upper half lies under the wing thatch are buried there -> dropped (partly buried ones stay, scribed)
    mid = B + D * (Lb * 0.6)[:, None]
    fpw = (mid[:, 0] > WX_W - W_OVH) & (mid[:, 0] < WX_E + W_OVH) & (mid[:, 1] > WY_S - W_OVH) & (mid[:, 1] < WY_N + W_OVH)
    buried = fpw & (mid[:, 2] < wing_under(mid[:, 0], mid[:, 1]) + TH_V_MIN)
    keep = ~buried
    layer, thc, w, rb, tb, butt, tip, kind, twist = [v[keep] for v in (layer, thc, w, rb, tb, butt, tip, kind, twist)]
    B, T, D, Lb, L = B[keep], T[keep], D[keep], Lb[keep], L[keep]
    M = len(thc)
    E = np.stack([-np.sin(thc), np.cos(thc), np.zeros(M)], 1)
    N = np.cross(E, D)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    rr = np.full(M, 0.008)
    X = ax5(w / 2, rr)
    Y = axn(np.zeros(M), L, rr, 9)
    Z = np.stack([np.zeros(M), tb - rr, tb], 1)
    P, quads = rbox(X, Y, Z, rr, skip_back=True, round_back=False)
    x, u, h = P[..., 0], P[..., 1], P[..., 2]
    fu = u / L[:, None]
    # taper toward the top (converging circumference) + wedge thickness
    x = x * (1 - 0.22 * fu)
    h = h * (1 - 0.5 * fu) + tb[:, None] * 0.5 * (1 - fu)
    # blunt broken / split ends (never pointed): 0 square-broken, 1 diagonal break 20-40 deg,
    # 2 split (notch 3-7 cm down the middle, leaving two blunt prongs >=3 cm wide), 3 ragged square break
    tipz = np.clip((u - (L[:, None] - 0.10)) / 0.10, 0, 1)
    xn = x / (w[:, None] / 2)
    wl_ = w[:, None] * (1 - 0.22)
    rs = np.random.default_rng(5051)
    cang = np.radians(rs.uniform(20, 40, M)) * np.where(rs.uniform(0, 1, M) < 0.5, -1, 1)
    notch = rs.uniform(0.03, 0.07, M)
    u = u - np.where((kind == 1)[:, None], np.tan(np.abs(cang))[:, None] * (0.5 + 0.5 * np.sign(cang)[:, None] * xn)
                     * wl_ * tipz, 0.0)
    u = u - np.where((kind == 2)[:, None] & (np.abs(xn) < 0.22), notch[:, None] * tipz, 0.0)
    u = u - np.where((kind == 3)[:, None] | (kind == 0)[:, None],
                     0.012 * tipz * np.abs(np.sin(xn * 4.0 + thc[:, None] * 30)), 0.0)
    x = x + twist[:, None] * u * (u / L[:, None])
    W = B[:, None, :] + u[..., None] * D[:, None, :] + x[..., None] * E[:, None, :] + h[..., None] * N[:, None, :]
    acc.add(W.reshape(-1, 3), inst_faces(quads, M, P.shape[1]), "M_roof_shake",
            uv=np.stack([x, u], -1).reshape(-1, 2))
    log("  collar shakes", M)
    # backing frustum + ledge to the cone
    prof = [(COLLAR_P - 0.06, 4.70), (COLLAR_TOP_R - 0.05, COLLAR_TOP_Z - 0.02), (COLLAR_TOP_R - 0.12, COLLAR_TOP_Z + 0.02),
            (float(np.interp(COLLAR_TOP_Z + 0.08, CONE_ZF, CONE_RF)) - 0.01, COLLAR_TOP_Z + 0.08)]
    V, F = lathe(prof, 64, cap_top=False, cap_bottom=False)
    acc.add(V, F, "M_roof_shake")
    finalize(acc, coll)
    # cope slabs on the ledge between the comb and the cone (shed water off the ledge)
    accl = Acc("KEEP_cone_ledge_slabs")
    zl = COLLAR_TOP_Z + 0.06
    rin = float(np.interp(zl + 0.06, CONE_ZF, CONE_RF)) - 0.05
    th = rng.uniform(0, 0.1)
    while th < 2 * math.pi - 0.05:
        wd = rng.uniform(0.24, 0.40)
        dth = wd / 2.85
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0.0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0.0])
        tilt = math.radians(rng.uniform(8, 16))
        ex = n3 * math.cos(tilt) - np.array([0, 0, 1.0]) * math.sin(tilt)
        ez = np.cross(ex, t3)
        if ez[2] < 0:
            ez = -ez
        o = n3 * rin + np.array([0, 0, zl + 0.07 + rng.uniform(-0.01, 0.01)])
        L = COLLAR_TOP_R - 0.06 - rin + rng.uniform(-0.03, 0.03)
        hh = rng.uniform(0.05, 0.08)
        seed = rng.uniform(0, 100)

        def dfm(P, seed=seed):
            P = P.copy()
            P[..., 2] += 0.008 * fbm(P * 9 + seed, 2)
            P[..., 1] *= 1 - 0.12 * (P[..., 0] / max(L, 0.1))
            return P
        obox(accl, o[None], ex, t3, ez, L, wd - rng.uniform(0.01, 0.025), hh, 0.015, "M_stone", nx=5, ny=5, nz=4,
             deform=dfm)
        th += dth
    finalize(accl, coll)


# ==============================================================================================
# LANTERN, CAP (tier 4), FINIALS
# ==============================================================================================
LANT_APO = 1.375
LANT_Z0, LANT_Z1 = 9.6, 10.55
CAP = OctRoof(0.0, 0.0, p_lip=1.95, z_lip=10.57, d_pts=[0, 0.3, 0.6, 1.95], a_pts=[22, 32, 48, 50],
              p_min=0.02, kick=0.035, kick_len=0.5, wave=0.008, sag=0.012, seed=8)


def oct_corner(apo_, k, sgn):
    """corner of octagon (facet normals at k*45deg) at the end sgn of facet k."""
    phi = math.radians(45 * k)
    n = np.array([math.cos(phi), math.sin(phi)])
    t = np.array([-math.sin(phi), math.cos(phi)])
    return n * apo_ + t * apo_ * TAN22 * sgn


def build_lantern(coll):
    rng = np.random.default_rng(606)
    accb = Acc("KEEP_lantern_boards")
    accf = Acc("KEEP_lantern_frame")
    up = np.array([0, 0, 1.0])
    # sole ring on the cone top, head ring, corner posts
    for k in range(8):
        phi = math.radians(45 * k)
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        for apo_, z, sz in ((1.24, LANT_Z0 + 0.1, 0.2), (1.27, LANT_Z1 - 0.075, 0.15)):
            a = np.array([*oct_corner(apo_, k, -1), z])
            b = np.array([*oct_corner(apo_, k, 1), z])
            beam(accf, a - t3 * 0.08, b + t3 * 0.08, sz, sz, 0.02, "M_timber", up=up, nx=6)
        c = oct_corner(1.27, k, 1)
        cd = c / np.linalg.norm(c)
        cp = np.array([*(c - cd * 0.0), LANT_Z0 + 0.2])
        beam(accf, cp, cp + np.array([0, 0, LANT_Z1 - LANT_Z0 - 0.35]), 0.14, 0.14, 0.02, "M_timber",
             up=np.array([cd[0], cd[1], 0]), nx=4)
    # vertical boards (with openings on facet 6 (-Y) and 5 (SW))
    opening = {6: (0.05, 10.0, 0.35, 0.45), 5: (-0.1, 10.0, 0.35, 0.45)}
    for k in range(8):
        phi = math.radians(45 * k)
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        half = LANT_APO * TAN22
        x = -half + 0.03
        while x < half - 0.06:
            wd = min(rng.uniform(0.14, 0.24), half - 0.03 - x)
            if wd < 0.07:
                break
            zb = LANT_Z0 - 0.08 + rng.uniform(-0.02, 0.02)
            zt = LANT_Z1 + 0.02
            segs = [(zb, zt)]
            if k in opening:
                ox, oz, ow, oh = opening[k]
                if x + wd > ox - ow / 2 and x < ox + ow / 2:
                    segs = [(zb, oz - oh / 2 - 0.004), (oz + oh / 2 + 0.004, zt)]
            ask = rng.normal(0, 0.012) if rng.uniform() < 0.25 else rng.normal(0, 0.003)
            for za, zb2 in segs:
                o = n3 * (LANT_APO - 0.015) + t3 * (x + wd / 2) + np.array([0, 0, za])
                ex = np.array([0, 0, 1.0]) + t3 * ask
                ex /= np.linalg.norm(ex)
                obox(accb, o[None], ex, t3, n3, zb2 - za, wd - 0.012, 0.03, 0.006, "M_timber_weathered",
                     nx=5, ny=4, nz=3)
            x += wd
        # corner battens
        c = oct_corner(LANT_APO + 0.02, k, 1)
        cd = np.array([c[0], c[1], 0]) / np.linalg.norm(c)
        ct = np.array([-cd[1], cd[0], 0])
        obox(accb, np.array([[c[0], c[1], LANT_Z0 - 0.09]]), up, ct, cd, LANT_Z1 - LANT_Z0 + 0.1, 0.10, 0.035, 0.008,
             "M_timber_weathered", nx=4, ny=4, nz=3)
        if k in opening:
            ox, oz, ow, oh = opening[k]
            # opening frame
            for (a, b) in (((ox - ow / 2, oz - oh / 2), (ox + ow / 2, oz - oh / 2)), ((ox - ow / 2, oz + oh / 2), (ox + ow / 2, oz + oh / 2))):
                pa = n3 * (LANT_APO + 0.02) + t3 * (a[0] - 0.05) + np.array([0, 0, a[1]])
                pb = n3 * (LANT_APO + 0.02) + t3 * (b[0] + 0.05) + np.array([0, 0, b[1]])
                beam(accf, pa, pb, 0.06, 0.05, 0.01, "M_timber", up=n3)
            for xx in (ox - ow / 2 - 0.025, ox + ow / 2 + 0.025):
                pa = n3 * (LANT_APO + 0.02) + t3 * xx + np.array([0, 0, oz - oh / 2 - 0.03])
                beam(accf, pa, pa + np.array([0, 0, oh + 0.06]), 0.05, 0.06, 0.01, "M_timber", up=n3)
            # dark interior backing behind the opening
            pa = n3 * (LANT_APO - 0.6) + t3 * ox + np.array([0, 0, oz - oh / 2 - 0.1])
            obox(accb, pa[None], up, t3, n3, oh + 0.2, ow + 0.3, 0.05, 0.005, "M_timber", nx=4)
            if k == 5:
                # hinged hatch propped open (hinge at top, swung out ~40 deg)
                hz = oz + oh / 2 + 0.03
                ang = math.radians(38)
                hdir = -np.array([0, 0, 1.0]) * math.cos(ang) + n3 * math.sin(ang)
                base = n3 * (LANT_APO + 0.05) + t3 * ox + np.array([0, 0, hz])
                for i, bw in enumerate((0.15, 0.14, 0.15)):
                    xo = ox - 0.22 + 0.075 + i * 0.147
                    o = n3 * (LANT_APO + 0.05) + t3 * xo + np.array([0, 0, hz])
                    obox(accb, o[None], hdir, t3, np.cross(hdir, t3), 0.55, bw - 0.01, 0.028, 0.006, "M_timber_weathered",
                         nx=4, ny=4, nz=3)
                for zz in (0.12, 0.42):
                    o = base + hdir * zz - np.cross(hdir, t3) * 0.025 - t3 * 0.21
                    beam(accb, o, o + t3 * 0.42, 0.05, 0.025, 0.006, "M_timber_weathered", up=-np.cross(hdir, t3))
                # prop stick
                tip = base + hdir * 0.5
                foot = n3 * (LANT_APO + 0.03) + t3 * (ox + 0.12) + np.array([0, 0, oz - oh / 2 - 0.02])
                V, F = sweep(np.array([foot, tip]), n3, prof_circle(0.018, 8))
                accb.add(V, F, "M_timber")
                # strap hinges
                for xo in (-0.12, 0.12):
                    o = base + t3 * (ox + xo - ox) * 1 - np.cross(hdir, t3) * 0.0 + n3 * 0.0
                    beam(accf, base + t3 * xo + hdir * 0.0 + np.cross(hdir, t3) * 0.018,
                         base + t3 * xo + hdir * 0.32 + np.cross(hdir, t3) * 0.018, 0.035, 0.006, 0.002, "M_iron",
                         up=np.cross(hdir, t3))
    # lantern floor & ceiling closure
    ang = np.radians(np.arange(8) * 45 + 22.5)
    r = 1.30 / math.cos(math.radians(22.5))
    for z, fl in ((LANT_Z0 + 0.2, False), (LANT_Z1, True)):
        V = np.stack([r * np.cos(ang), r * np.sin(ang), np.full(8, z)], 1)
        f = np.arange(8)[None]
        accf.add(V, f[:, ::-1] if fl else f, "M_timber")
    finalize(accb, coll)
    finalize(accf, coll)


def build_cap(coll, roof, prefix, rng, p_wall, z_plate, n_raft, p_top, expo, W, t, lens, bracket_z0):
    acc = Acc(f"{prefix}_shingles")
    acch = Acc(f"{prefix}_hips")
    accs = Acc(f"{prefix}_structure")
    m_top = float(roof.m_of_p(p_top))
    n = covering_boards(roof, acc, "M_roof_shingle", rng, -0.03, m_top, expo=expo, W=W, t=t, lens=lens, gap=0.007,
                        nx=4, nm=4, frac_missing=0.02, frac_slip=0.03, curl=0.012, rot_sd=0.055, p_floor=0.03, jit_m=0.02)
    log(f"  {prefix} shingles", n)
    hip_boards(roof, acch, "M_roof_shingle", rng, roof.p_lip + 0.02, p_top, 0.08, 0.02, 0.032, piece=(0.5, 0.8))
    eave_structure(roof, accs, accs, accs, rng, p_wall=p_wall, z_plate_top=z_plate, sheath_t=0.02, n_raft=n_raft,
                   rw=0.07, rd_tip=0.09, fascia_h=0.11, fascia_t=0.03, soffit_w=(0.12, 0.17), fascia_wave=0.006)
    # carved eave ring beam + corner brackets
    for k in range(8):
        phi = math.radians(45 * k) + roof.rot
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        ca = np.array([*(roof.c + oct_corner(p_wall + 0.05, k, -1)), z_plate - 0.06])
        cb = np.array([*(roof.c + oct_corner(p_wall + 0.05, k, 1)), z_plate - 0.06])
        ca[:2] = roof.c + rot2(*(ca[:2] - roof.c), roof.rot)
        cb[:2] = roof.c + rot2(*(cb[:2] - roof.c), roof.rot)

        def ring_def(P):
            P = P.copy()
            # carved bead: a groove along the outer face
            m = np.abs(P[..., 2]) < 0.025
            P[..., 1] -= np.where(m & (P[..., 1] > 0), 0.012, 0)
            return P
        # one hewn ring-beam piece per facet: butted at one corner, lapped 0.12 m past the other with a peg
        dzk = rng.uniform(-0.008, 0.008) + (0.012 if k % 2 else -0.012)
        Lk = float(np.linalg.norm(cb - ca)) + 0.13
        hewn_member(accs, ca + t3 * 0.004 + np.array([0, 0, dzk]), t3, n3, np.array([0, 0, 1.0]), Lk, 0.12, 0.12, rng,
                    chamfer=0.016, nf=2, st_len=0.08, adze=0.003, wave=0.003, seed=200 + k)
        peg(accs, cb + t3 * 0.06 + n3 * 0.062 + np.array([0, 0, dzk]), n3, rad=0.011, proud=0.012)
        # bracket at the corner (curved), from the post below out to the hip rafter
        cd = np.array([*(rot2(*oct_corner(1.0, k, 1), roof.rot))])
        cd = np.array([cd[0], cd[1], 0]) / np.linalg.norm(cd)
        base = np.array([*(roof.c + cd[:2] * (p_wall / math.cos(math.radians(22.5)) - 0.04)), bracket_z0])
        top = np.array([*(roof.c + cd[:2] * (p_wall / math.cos(math.radians(22.5)) + 0.35)), z_plate + 0.02])
        ctrl = np.array([base[0], base[1], top[2]])
        us = np.linspace(0, 1, 10)
        path = ((1 - us) ** 2)[:, None] * base + (2 * us * (1 - us))[:, None] * ctrl + (us ** 2)[:, None] * top
        tg = np.array([-cd[1], cd[0], 0])
        prof = np.array([(0.04, -0.05), (0.04, 0.05), (-0.04, 0.05), (-0.04, -0.05)])
        V, F = sweep(path, tg, prof_rect(0.08, 0.09, 0.012))
        accs.add(V, F, "M_timber")
    finalize(acc, coll)
    finalize(acch, coll)
    finalize(accs, coll)


def finial(acc, base, scale, lean_deg, lean_dir, seg=28, kind="main"):
    prof = [(0.10, 0.0), (0.105, 0.09), (0.128, 0.105), (0.128, 0.14), (0.075, 0.16), (0.08, 0.21),
            (0.105, 0.26), (0.112, 0.31), (0.105, 0.35), (0.06, 0.41), (0.048, 0.43), (0.068, 0.445),
            (0.068, 0.465), (0.048, 0.48), (0.066, 0.495), (0.066, 0.512), (0.042, 0.53), (0.05, 0.57),
            (0.072, 0.63), (0.076, 0.67), (0.068, 0.72), (0.045, 0.79), (0.024, 0.86), (0.021, 0.9),
            (0.032, 0.915), (0.032, 0.94), (0.019, 0.96), (0.015, 1.05), (0.010, 1.2), (0.004, 1.38), (0.0, 1.45)]
    prof = np.array(prof)
    prof = prof * scale
    V, F = lathe(prof, seg, cap_bottom=True, cap_top=False)
    a = math.radians(lean_deg)
    d = np.array([lean_dir[0], lean_dir[1], 0.0])
    d /= np.linalg.norm(d)
    # lean: shear proportional to height
    V = V + d[None] * (V[:, 2:3] * math.tan(a))
    acc.add(V + np.asarray(base)[None], F, "M_iron")


def lead_hat(acc, cx, cy, z_apex, r0, h0, seg=28):
    prof = [(r0 + 0.02, -h0 - 0.01), (r0 + 0.025, -h0 + 0.012), (r0, -h0 + 0.02), (r0 * 0.55, -h0 * 0.45),
            (0.09, 0.02), (0.085, 0.05), (0.0, 0.05)]
    prof = [(r, z) for r, z in prof]
    V, F = lathe(prof, seg, cx=cx, cy=cy, z0=z_apex, cap_bottom=True, cap_top=False)
    acc.add(V, F, "M_lead")


def build_main_cap_and_finial(coll):
    rng = np.random.default_rng(707)
    build_cap(coll, CAP, "KEEP_cap", rng, p_wall=LANT_APO, z_plate=LANT_Z1, n_raft=4, p_top=0.14,
              expo=0.15, W=0.34, t=0.024, lens=(0.12, 0.18), bracket_z0=LANT_Z1 - 0.45)
    acc = Acc("KEEP_finial_main")
    apex = float(CAP.zb(0.02))
    lead_hat(acc, 0, 0, apex, 0.24, 0.20)
    finial(acc, (0, 0, apex + 0.04), 1.0, 1.0, (0.6, -0.8))
    finalize(acc, coll)
    return apex


# ==============================================================================================
# MAIN DOOR (arched plank leaf, ironwork), WINDOW FRAMES, THRESHOLD, STEP
# ==============================================================================================
def facet_obox(acc, k, x0, x1, z0, z1, w0, w1, r, mat, nx=4, ny=4, nz=4, deform=None, a_ref=A_REF):
    """axis aligned box in facet-local coords (x,z,w) -> world (plumb)."""
    X = axn(np.array([x0]), np.array([x1]), np.array([r]), nx)
    Y = axn(np.array([z0]), np.array([z1]), np.array([r]), ny)
    Z = axn(np.array([w0]), np.array([w1]), np.array([r]), nz)
    P, quads = rbox(X, Y, Z, np.array([r]))
    P = P[0]
    if deform is not None:
        P = deform(P)
    W = fmap(k, P[:, 0], P[:, 1], P[:, 2], a_ref=a_ref)
    acc.add(W, quads, mat, uv=np.stack([P[:, 1], P[:, 0] + P[:, 2]], -1))


def strap_widths(us, w0=0.050, w1=0.038, spear_w=0.080, u_sp=0.80):
    """forged strap plan: 50 mm at the knuckle tapering to ~38 mm, necked, spear terminal ~80 mm wide."""
    us = np.asarray(us, float)
    wd = w0 + (w1 - w0) * np.clip(us / u_sp, 0, 1)
    s_ = np.clip((us - u_sp) / (1 - u_sp), 0, 1)
    neck = w1 - 0.008 * np.clip(s_ / 0.12, 0, 1)
    flare = (w1 - 0.008) + (spear_w - w1 + 0.008) * np.sin(0.5 * np.pi * np.clip((s_ - 0.12) / 0.33, 0, 1))
    point = spear_w + (0.012 - spear_w) * np.clip((s_ - 0.45) / 0.55, 0, 1) ** 0.9
    wd = np.where(us <= u_sp, wd, np.where(s_ < 0.12, neck, np.where(s_ < 0.45, flare, point)))
    return wd


def strap_hinge(acc, k, x_hinge, x_len, z, w_face, rng, nails_acc, a_ref=A_REF, direction=-1):
    """forged strap lying flat on the door face (6 mm proud), from the hinge edge; spear terminal; knuckle."""
    n = 40
    us = np.linspace(0, 1, n)
    xs = x_hinge + direction * us * x_len
    width = strap_widths(us) * (1 + 0.04 * n1(us * 6, int(z * 100)))
    tk = 0.006 * (1 - 0.15 * us)
    zz = z + 0.002 * n1(us * 5, int(z * 37) + 3)
    path = fmap(k, xs, zz, w_face + 0.5 * tk + 0.0005 * n1(us * 9, 5), a_ref=a_ref)
    # profile: right = vertical (strap width), up = facet normal (strap thickness)
    profs = np.stack([prof_rect(wd, t_, min(0.0018, t_ * 0.3)) for wd, t_ in zip(width, tk)])
    nrm = np.array([FN[k][0], FN[k][1], 0.0])
    V, F = sweep(path, nrm, profs)
    acc.add(V, F, "M_iron")
    # knuckle (rolled eye) around the pintle at the hinge edge
    kp = fmap(k, np.array([x_hinge + 0.012 * -direction]), np.array([z]), np.array([w_face - 0.01]), a_ref=a_ref)[0]
    Vk, Fk = lathe([(0.017, -0.03), (0.017, 0.03)], 12, cx=kp[0], cy=kp[1], z0=z)
    acc.add(Vk, Fk, "M_iron")
    # pintle: vertical pin + shank into the jamb reveal
    Vp, Fp = lathe([(0.009, -0.06), (0.009, 0.05), (0.012, 0.055), (0.0, 0.06)], 10, cx=kp[0], cy=kp[1], z0=z - 0.035)
    acc.add(Vp, Fp, "M_iron")
    sh0 = kp + np.array([0, 0, -0.045])
    sh1 = fmap(k, np.array([x_hinge + 0.10 * -direction]), np.array([z - 0.045]), np.array([w_face - 0.01]), a_ref=a_ref)[0]
    Vs, Fs = sweep(np.array([sh0, sh1]), (0, 0, 1), prof_rect(0.018, 0.018, 0.003))
    acc.add(Vs, Fs, "M_iron")
    # nails along the strap
    nn = int(rng.integers(6, 9))
    ui = np.linspace(0.08, 0.86, nn)
    tk_n = 0.006 * (1 - 0.15 * ui)
    P = fmap(k, x_hinge + direction * ui * x_len, z + np.where(np.arange(nn) % 2 == 0, 0.009, -0.009) * (ui < 0.8),
             w_face + tk_n, a_ref=a_ref)
    nail_heads(nails_acc, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.0085, h=0.006)


def build_main_door(coll):
    rng = np.random.default_rng(808)
    op = OPENINGS[0]
    k, xc, hw, zs = op["k"], op["xc"], op["hw"], op["zs"]
    acc = Acc("KEEP_door_leaf")
    acci = Acc("KEEP_door_ironwork")
    R = hw + 0.03
    w_front = -op["depth"]
    w_back = w_front - 0.04
    zb0 = op["z0"] + 0.006
    widths = rng.uniform(0.13, 0.18, 7)
    widths = widths / widths.sum() * (2 * R)
    xs = xc - R + np.concatenate([[0], np.cumsum(widths)])
    planks = []
    for i in range(7):
        a, b = xs[i] + 0.0015, xs[i + 1] - 0.0015
        if i == 2:   # split plank: two pieces with a thin crack
            m = a + (b - a) * 0.42
            planks += [(a, m - 0.002, 0.0), (m + 0.002, b, -0.002)]
        else:
            planks.append((a, b, rng.uniform(-0.0015, 0.0015)))
    for a, b, dw in planks:
        zb = zb0 + rng.uniform(-0.006, 0.008)

        def dfm(P, a=a, b=b, zb=zb):
            P = P.copy()
            x = P[:, 0]
            dx = np.clip(np.abs(x - xc), 0, R - 1e-4)
            ztop = zs + np.sqrt(R * R - dx * dx) - 0.004
            v = (P[:, 1] - zb) / (1.0)
            P[:, 1] = zb + v * (ztop - zb)
            # weathering: slight cupping and wear at the bottom
            xr = (x - 0.5 * (a + b)) / (0.5 * (b - a))
            P[:, 2] += 0.002 * (1 - xr ** 2) - 0.003 * np.clip(1 - v * 6, 0, 1)
            return P
        facet_obox(acc, k, a, b, zb, zb + 1.0, w_back, w_front + dw, 0.007, "M_timber", nx=5, ny=12, nz=3,
                   deform=dfm)
    # ledges on the back
    for zl, half in ((0.42, R - 0.06), (1.12, R - 0.06), (1.78, R - 0.12)):
        facet_obox(acc, k, xc - half, xc + half, zl - 0.07, zl + 0.07, w_back - 0.04, w_back, 0.01, "M_timber", nx=6)
    # strap hinges (hinge side = +x edge)
    for zh, ln in ((0.42, 0.78), (1.12, 0.78), (1.80, 0.62)):
        strap_hinge(acci, k, xc + R - 0.005, ln, zh, w_front, rng, acci)
    # clinch nails along ledge lines (one per plank, two rows offset)
    pts = []
    for zl in (0.42, 1.12):
        for i in range(7):
            xm = 0.5 * (xs[i] + xs[i + 1])
            if xm > xc + R - 0.78 - 0.02:
                continue
            for dz in (-0.035, 0.035):
                pts.append((xm + rng.normal(0, 0.008), zl + dz + rng.normal(0, 0.004)))
    for zl in (0.80, 1.48):
        for i in range(7):
            xm = 0.5 * (xs[i] + xs[i + 1])
            pts.append((xm + rng.normal(0, 0.008), zl + rng.normal(0, 0.004)))
    pts = np.array(pts)
    P = fmap(k, pts[:, 0], pts[:, 1], np.full(len(pts), w_front + 0.001))
    nail_heads(acci, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.008, h=0.006)
    # ring pull with backplate, keyhole escutcheon
    hx_ = xc - R + 0.17
    bp = fmap(k, np.array([hx_]), np.array([1.02]), np.array([w_front]))[0]
    nrm = np.array([FN[k][0], FN[k][1], 0.0])
    tan = np.array([FT[k][0], FT[k][1], 0.0])
    V, F = lathe([(0.055, 0.0), (0.055, 0.004), (0.045, 0.007), (0.02, 0.009), (0.012, 0.022), (0.0, 0.024)], 20)
    W = bp + V[:, 0:1] * tan + V[:, 1:2] * np.array([0, 0, 1.0]) + V[:, 2:3] * nrm
    acci.add(W, F, "M_iron")
    ring_c = bp + nrm * 0.03 - np.array([0, 0, 0.06])
    a = np.linspace(0, 2 * np.pi, 25)
    ring = ring_c + 0.062 * (np.cos(a)[:, None] * tan + np.sin(a)[:, None] * np.array([0, 0, 1.0])) + \
        nrm * 0.004 * np.sin(a)[:, None]
    V, F = sweep(ring, nrm, prof_circle(0.0085, 8), caps=False)
    acci.add(V, F, "M_iron")
    # keyhole plate: a frame of four small plates around a slot
    kz = 0.90
    for (xa, xb, za, zb2) in ((-0.025, 0.025, kz + 0.025, kz + 0.06), (-0.025, 0.025, kz - 0.06, kz - 0.022),
                              (-0.025, -0.006, kz - 0.022, kz + 0.025), (0.006, 0.025, kz - 0.022, kz + 0.025)):
        facet_obox(acci, k, hx_ + xa, hx_ + xb, za, zb2, w_front, w_front + 0.004, 0.0015, "M_iron", nx=4, ny=4, nz=3)
    nail_heads(acci, fmap(k, np.array([hx_, hx_]), np.array([kz + 0.048, kz - 0.048]), np.array([w_front + 0.004] * 2)),
               nrm, rad=0.005, h=0.004)
    finalize(acc, coll)
    finalize(acci, coll)


def build_window_frames(coll):
    rng = np.random.default_rng(909)
    acc = Acc("KEEP_hall_window_frames")
    for op in OPENINGS:
        if op["kind"] != "rect" or not op.get("frame"):
            continue
        k, xc, hw, z0, z1, d = op["k"], op["xc"], op["hw"], op["z0"], op["z1"], op["depth"]
        fw = 0.10 if hw > 0.3 else 0.08
        w0, w1 = -d - 0.12, -d
        r = 0.012
        facet_obox(acc, k, xc - hw, xc - hw + fw, z0, z1, w0, w1, r, "M_timber")
        facet_obox(acc, k, xc + hw - fw, xc + hw, z0, z1, w0, w1, r, "M_timber")
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, z0, z0 + fw, w0, w1 + 0.01, r, "M_timber")
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, z1 - fw, z1, w0, w1, r, "M_timber")
        mw = 0.055
        facet_obox(acc, k, xc - mw / 2, xc + mw / 2, z0 + fw - 0.01, z1 - fw + 0.01, w0 + 0.02, w1 - 0.02, 0.008, "M_timber")
        zt = z0 + (z1 - z0) * 0.56
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, zt - mw / 2, zt + mw / 2, w0 + 0.02, w1 - 0.02, 0.008,
                   "M_timber")
        # pegs at the frame corners
        for xx in (xc - hw + fw / 2, xc + hw - fw / 2):
            for zz in (z0 + fw / 2, z1 - fw / 2):
                p = fmap(k, np.array([xx]), np.array([zz]), np.array([w1]))[0]
                peg(acc, p, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.010, proud=0.008)
    finalize(acc, coll)


def rough_block(acc, k, x0, x1, z0, z1, w0, w1, r, mat, rng, amp=0.006, dip=0.0, a_ref=A_REF, outline=0.0):
    def dfm(P):
        P = P.copy()
        nz = fbm(P * 9.0 + rng.uniform(0, 50), 2)
        P[:, 1] += amp * nz * (P[:, 1] > (z0 + z1) / 2)
        if outline:
            # irregular plan outline: edges wander, corners rounded off unevenly
            cx, cw = (x0 + x1) / 2, (w0 + w1) / 2
            ux = (P[:, 0] - cx) / ((x1 - x0) / 2)
            uw = (P[:, 2] - cw) / ((w1 - w0) / 2)
            o1 = fbm(np.stack([P[:, 0] * 3.0, P[:, 2] * 3.0, np.full(len(P), 7.7)], -1), 2)
            P[:, 0] -= np.sign(ux) * np.abs(ux) ** 6 * (outline * (0.6 + 0.6 * o1))
            P[:, 2] -= np.sign(uw) * np.abs(uw) ** 6 * (outline * (0.6 - 0.6 * o1))
            cut = (np.abs(ux) * np.abs(uw)) ** 3
            P[:, 0] -= np.sign(ux) * cut * outline * 1.5
            P[:, 2] -= np.sign(uw) * cut * outline * 1.5
            # worn, slightly domed top with a hollow where feet land
            top = P[:, 1] > (z0 + z1) / 2
            P[:, 1] -= top * 0.012 * np.exp(-((ux * 1.3) ** 2 + (uw * 1.6) ** 2))
            P[:, 1] -= top * 0.015 * np.clip(np.abs(ux) ** 4 + np.abs(uw) ** 4, 0, 1)
        if dip:
            xr = (P[:, 0] - (x0 + x1) / 2) / ((x1 - x0) / 2)
            P[:, 1] -= dip * (1 - np.clip(xr, -1, 1) ** 2) * (P[:, 1] > (z0 + z1) / 2)
        P[:, 0] += amp * 0.6 * fbm(P[:, [1, 2, 0]] * 7.0, 2)
        P[:, 2] += amp * 0.6 * fbm(P[:, [2, 0, 1]] * 7.0 + 3, 2)
        return P
    facet_obox(acc, k, x0, x1, z0, z1, w0, w1, r, mat, nx=12, ny=4, nz=8, deform=dfm, a_ref=a_ref)


def build_threshold(coll):
    rng = np.random.default_rng(1010)
    acc = Acc("KEEP_threshold")
    op = OPENINGS[0]
    k, xc = op["k"], op["xc"]
    rough_block(acc, k, xc - 0.62, xc + 0.62, -0.08, 0.12, -0.55, 0.20, 0.025, "M_stone_dressed", rng, amp=0.004, dip=0.012,
                outline=0.012)
    # outside step stone 1.4 x 0.6 x 0.12 (top 0.115)
    rough_block(acc, k, xc - 0.70, xc + 0.70, -0.05, 0.115, 0.24, 0.84, 0.04, "M_stone", rng, amp=0.010, dip=0.0,
                outline=0.06)
    # interior floor flags
    finalize(acc, coll)


# ==============================================================================================
# WEST WING: walls (rubble), thatch roof, ridge comb, plank door, window
# ==============================================================================================
def build_wing_path():
    pts = [(WX_E, 3.70), (WX_E, WY_N), (WX_W, WY_N), (WX_W, WY_S), (-3.70, WY_S)]
    rc = 0.07
    P, N = [], []
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        n = np.array([d[1], -d[0]])
        sa = rc if i > 0 else 0.0
        sb = rc if i < len(pts) - 2 else 0.0
        for u in np.arange(sa, L - sb, 0.01):
            P.append(a + d * u)
            N.append(n)
        if i < len(pts) - 2:
            c = b
            nb = np.array(pts[i + 2], float)
            d2 = (nb - c) / np.linalg.norm(nb - c)
            n2 = np.array([d2[1], -d2[0]])
            cen = c - n * rc - n2 * rc
            for t in np.linspace(0, 1, 7)[:-1]:
                nn = n * (1 - t) + n2 * t
                nn /= np.linalg.norm(nn)
                P.append(cen + nn * rc)
                N.append(nn)
    P.append(np.array(pts[-1], float))
    N.append(N[-1])
    P = np.array(P)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    S = np.concatenate([[0], np.cumsum(seg)])
    return S, P, np.array(N)


WS, WP, WN = build_wing_path()
WING_LEN = WS[-1]


def wing_map(s, z, w, zc):
    s = np.asarray(s, float)
    z = np.asarray(z, float)
    w = np.asarray(w, float)
    px, py = np.interp(s, WS, WP[:, 0]), np.interp(s, WS, WP[:, 1])
    nx, ny = np.interp(s, WS, WN[:, 0]), np.interp(s, WS, WN[:, 1])
    nn = np.sqrt(nx * nx + ny * ny)
    nx, ny = nx / nn, ny / nn
    off = w - z * BAT
    return np.stack([px + nx * off, py + ny * off, z + w * BAT], -1)


def wing_s_of(x, y):
    d = np.hypot(WP[:, 0] - x, WP[:, 1] - y)
    return float(WS[np.argmin(d)])


S_SOUTH0 = wing_s_of(WX_W, WY_S)
WDOOR = dict(xc=-5.05, hw=0.50, z0=0.10, z1=2.20, fw=0.18, depth=0.20)
WWIN = dict(xc=-8.55, hw=0.225, z0=1.30, z1=1.85, depth=0.16)


def wing_ztop(s):
    x, y = np.interp(s, WS, WP[:, 0]), np.interp(s, WS, WP[:, 1])
    if x > WX_E - 0.05 and y > 3.6:
        return float(wing_under(x, y)) - 0.02
    return W_WALL_H


def wing_quoins():
    rng = np.random.default_rng(1113)
    recs = []
    d = WDOOR
    s_d = S_SOUTH0 + (d["xc"] - WX_W)
    for side in (-1, 1):
        z = -0.06
        i = 0
        while z < d["z1"] - 0.05:
            h = min(rng.uniform(0.30, 0.42), d["z1"] + 0.0 - z)
            if h < 0.12:
                break
            wd = (0.36 if (i % 2 == 0) == (side < 0) else 0.25) + rng.uniform(-0.03, 0.03)
            x_in = s_d + side * (d["hw"] + d["fw"])
            xa, xb = sorted([x_in, x_in + side * wd])
            recs.append((0.5 * (xa + xb), z + h / 2, 0.5 * (xb - xa) - 0.007, h / 2 - 0.008, rng.uniform(0.022, 0.036), 0.26))
            z += h
            i += 1
    w = WWIN
    s_w = S_SOUTH0 + (w["xc"] - WX_W)
    for side in (-1, 1):
        x_in = s_w + side * (w["hw"] + 0.07)
        xa, xb = sorted([x_in, x_in + side * 0.24])
        recs.append((0.5 * (xa + xb), (w["z0"] + w["z1"]) / 2, 0.11, (w["z1"] - w["z0"]) / 2 - 0.006, 0.025, 0.2))
    return np.array(recs)


def wing_open_rects(with_extras=True):
    """opening rects in path coords (s0,s1,z0,z1): frames, lintels, sills, quoins."""
    d = WDOOR
    s_d = S_SOUTH0 + (d["xc"] - WX_W)
    w = WWIN
    s_w = S_SOUTH0 + (w["xc"] - WX_W)
    rects = [(s_d - d["hw"] - d["fw"], s_d + d["hw"] + d["fw"], -0.2, d["z1"] + 0.24),
             (s_w - w["hw"] - 0.07, s_w + w["hw"] + 0.07, w["z0"] - 0.12, w["z1"] + 0.20)]
    if with_extras:
        rects += [(s_d - d["hw"] - d["fw"] - 0.23, s_d + d["hw"] + d["fw"] + 0.25, d["z1"], d["z1"] + 0.245),
                  (s_w - w["hw"] - 0.31, s_w + w["hw"] + 0.31, w["z1"] + 0.05, w["z1"] + 0.25),
                  (s_w - w["hw"] - 0.15, s_w + w["hw"] + 0.15, w["z0"] - 0.125, w["z0"])]
        for q in wing_quoins():
            rects.append((q[0] - q[2] - 0.006, q[0] + q[2] + 0.006, q[1] - q[3] - 0.006, q[1] + q[3] + 0.006))
    return rects


def build_wing_walls(coll):
    rng = np.random.default_rng(1111)
    acc = Acc("KEEP_wing_wall_stones")
    rects = wing_open_rects()

    def excl(z0, z1, zm):
        out = []
        for s0, s1, za, zb in rects:
            if z1 > za and z0 < zb:
                out.append((s0 - 0.012, s1 + 0.012))
        return out + tooth_excl_wall(z0, z1, zm)
    cfg = dict(seed=17, footing=0.32, ch=(0.09, 0.19), p_tall=0.08, len=(0.20, 0.62), foot_len=(0.45, 0.85),
               joint=(0.009, 0.018), front=(0.005, 0.036), foot_proj=(0.03, 0.06), bevel=(0.005, 0.03),
               pillow=(0.002, 0.008), tilt=0.008, rot=0.012, p_double=0.07, p_long=0.05, back=0.09, bed_amp=0.03,
               slant=0.27, ch_mix=[(0.28, 0.08, 0.11), (0.38, 0.11, 0.16), (0.24, 0.16, 0.21), (0.10, 0.21, 0.25)],
               pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
    srange = lambda zm: [(0.0, WING_LEN)]
    S = layout_wall(rng, srange, -0.10, 3.85, excl, cfg, ztop_fn=wing_ztop)
    S = polygonize(S, (S["sc"] > S_SOUTH0 - 0.05) & (S["zc"] < 3.5) & (S["zc"] > 0.3), np.random.default_rng(1920))
    pins, _, _ = fill_voids(S, srange, excl, -0.10, 3.85, rng, cfg, ztop_fn=wing_ztop, label="wing")
    S = cat_stones(S, pins)
    P = wing_map(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
    keep = tur_dist(P[:, 0], P[:, 1], P[:, 2]) > -0.04
    ang = np.arctan2(P[:, 1], P[:, 0])
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = P[:, 0] * np.cos(kk * np.pi / 4) + P[:, 1] * np.sin(kk * np.pi / 4)
    keep &= pp > apo(P[:, 2]) - 0.02
    S = filt(S, keep)
    log("  wing stones", len(S["sc"]))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    # hero zone: the wing's south wall below 3.5 m (seen in the hero/front/actor shots)
    hero = (S["sc"] > S_SOUTH0 - 0.05) & (S["zc"] < 3.5) & ~small
    log(f"  wing hero stones {int(hero.sum())}, other {int((~hero & ~small).sum())}, pins {int(small.sum())}")
    build_poly_stones(acc, filt(S, hero), wing_map, "M_stone", np.random.default_rng(2021), rough=1.1)
    build_stones(acc, filt(S, ~hero & ~small), wing_map, "M_stone", rng, rough=1.1, nxy=5, noise_amp=0.008)
    build_stones(acc, filt(S, small), wing_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005)
    finalize(acc, coll, smooth_deg=28.0)
    # dressed quoins / jamb blocks of the plank door and the window: tooled faces, chipped arrises, out of square
    accq = Acc("KEEP_wing_dressed_stones")
    R = wing_quoins()
    S2 = stone_rec(R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], rng.uniform(0.008, 0.022, len(R)), R[:, 1], rng)
    dress_irregular(S2, rng)
    wear = np.clip(1.0 - S2["zc"] / 0.8, 0, 1)
    build_stones(accq, S2, wing_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(26, 26), wear=wear)
    finalize(accq, coll)
    # mortar body
    accm = Acc("KEEP_wing_wall_mortar")
    ss = np.linspace(0, WING_LEN, int(WING_LEN / 0.06))
    zs = np.linspace(-0.1, 3.8, 40)
    Sg, Zg = np.meshgrid(ss, zs, indexing="ij")
    W = wing_map(Sg.ravel(), Zg.ravel(), np.full(Sg.size, -0.004), Zg.ravel())
    ns, nz = Sg.shape
    idx = np.arange(ns * nz).reshape(ns, nz)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    sm = 0.5 * (Sg[:-1, :-1] + Sg[1:, 1:])
    zm = 0.5 * (Zg[:-1, :-1] + Zg[1:, 1:])
    keep = np.ones(sm.shape, bool)
    for s0, s1, za, zb in wing_open_rects(False):
        keep &= ~((sm > s0 + 0.04) & (sm < s1 - 0.04) & (zm > za + 0.04) & (zm < zb - 0.26))
    zt = np.array([wing_ztop(s) for s in sm[:, 0]])
    keep &= zm < zt[:, None] + 0.02
    Pm = wing_map(sm.ravel(), zm.ravel(), np.zeros(sm.size), zm.ravel()).reshape(sm.shape + (3,))
    keep &= tur_dist(Pm[..., 0], Pm[..., 1], Pm[..., 2]) > -0.18      # mortar body runs on behind the turret stones
    ang = np.arctan2(Pm[..., 1], Pm[..., 0])
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = Pm[..., 0] * np.cos(kk * np.pi / 4) + Pm[..., 1] * np.sin(kk * np.pi / 4)
    keep &= pp > apo(Pm[..., 2]) - 0.05
    accm.add(W, quads[keep.ravel()], "M_mortar")
    # reveals (door, window): tube through the wall
    for s0, s1, za, zb in wing_open_rects(False):
        dep = 0.62
        ring = np.array([(s0 + 0.03, za + 0.2), (s1 - 0.03, za + 0.2), (s1 - 0.03, zb - 0.22), (s0 + 0.03, zb - 0.22)])
        if za < 0:
            ring[:2, 1] = 0.0
        n = 4
        r1 = wing_map(ring[:, 0], ring[:, 1], np.full(n, 0.0), ring[:, 1])
        r2 = wing_map(ring[:, 0], ring[:, 1], np.full(n, -dep), ring[:, 1])
        V = np.concatenate([r1, r2])
        q = np.array([(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)])
        accm.add(V, q, "M_mortar")
    finalize(accm, coll)


def build_wing_door_window(coll):
    rng = np.random.default_rng(1212)
    acc = Acc("KEEP_wing_door")
    acci = Acc("KEEP_wing_door_ironwork")
    accw = Acc("KEEP_wing_window")
    d = WDOOR
    # local frame on the south wall (plumb): x east, w outward (-y), z up
    yface = WY_S

    def wl(x, z, w):
        x = np.asarray(x, float)
        return np.stack([x, np.full_like(x, yface) - np.asarray(w, float), np.asarray(z, float)], -1)

    def box(a, x0, x1, z0, z1, w0, w1, r, mat, nx=4, ny=4, nz=4, deform=None):
        X = axn(np.array([x0]), np.array([x1]), np.array([r]), nx)
        Y = axn(np.array([z0]), np.array([z1]), np.array([r]), ny)
        Z = axn(np.array([w0]), np.array([w1]), np.array([r]), nz)
        P, quads = rbox(X, Y, Z, np.array([r]))
        P = P[0]
        if deform is not None:
            P = deform(P)
        a.add(wl(P[:, 0], P[:, 1], P[:, 2]), quads, mat, uv=np.stack([P[:, 1], P[:, 0] + P[:, 2]], -1))

    xc, hw, fw = d["xc"], d["hw"], d["fw"]
    wf0, wf1 = -d["depth"] - 0.20, -d["depth"]          # frame depth range (w)
    z0, z1 = d["z0"], d["z1"]

    def adze(P, seed=0):
        P = P.copy()
        P[:, 2] += 0.003 * np.sin(P[:, 1] * 13 + seed) * (P[:, 2] > -0.25)
        return P
    # jambs, lintel, sill-beam
    # hand-hewn jambs and lintel (adze facets, slight lean/wave, a modelled check in the lintel face)
    EXo, EYo, EZo = np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, -1.0, 0])
    for jx, sd_ in ((xc - hw - fw / 2, 1), (xc + hw + fw / 2, 2)):
        hewn_member(acc, wl(jx, -0.02, 0.5 * (wf0 + wf1)), np.array([0, 0, 1.0]), EXo, EZo, z1 + fw + 0.02, fw,
                    wf1 - wf0, rng, chamfer=0.022, nf=3, st_len=0.05, adze=0.004,
                    lean=(rng.normal(0, 0.006), 0.0), swell=rng.uniform(-0.006, 0.006), seed=500 + sd_,
                    checks=[dict(face=1, pos=rng.uniform(-0.3, 0.3), x0=0.2, x1=0.7, depth=0.012, width=0.006)])
    lw0, lw1_ = wf0 - 0.05, wf1 + 0.17
    hewn_member(acc, wl(xc - hw - fw - 0.22, z1 + 0.12, 0.5 * (lw0 + lw1_)), EXo, EYo, EZo,
                2 * hw + 2 * fw + 0.46, 0.23, lw1_ - lw0, rng, chamfer=0.025, nf=4, st_len=0.04, adze=0.005,
                wave=0.006, seed=510,
                checks=[dict(face=1, pos=0.15, x0=0.12, x1=0.62, depth=0.018, width=0.009),
                        dict(face=1, pos=-0.4, x0=0.55, x1=0.9, depth=0.010, width=0.005)])
    for xx in (xc - hw - fw / 2, xc + hw + fw / 2):
        for zz in (z1 + 0.12,):
            p = wl(np.array([xx]), np.array([zz]), np.array([wf1 + 0.17]))[0]
            peg(acc, p, np.array([0, -1.0, 0]))
    # stone threshold at +0.10
    box(acc, xc - hw - fw - 0.05, xc + hw + fw + 0.05, -0.08, z0, -0.62, 0.10, 0.02, "M_stone_dressed", nx=8, ny=3, nz=6,
        deform=lambda P: P + np.stack([np.zeros(len(P)), -0.01 * (1 - ((P[:, 0] - xc) / 0.7) ** 2) * (P[:, 1] > 0.0), np.zeros(len(P))], 1))
    # plank leaf (7 planks) set in the frame
    lw0, lw1 = wf0 + 0.06, wf0 + 0.10
    widths = rng.uniform(0.13, 0.17, 7)
    widths = widths / widths.sum() * (2 * hw + 0.03)
    xs = xc - hw - 0.015 + np.concatenate([[0], np.cumsum(widths)])
    for i in range(7):
        zb = z0 + 0.008 + rng.uniform(-0.005, 0.006)
        box(acc, xs[i] + 0.0015, xs[i + 1] - 0.0015, zb, z1 + 0.02, lw0, lw1 + rng.uniform(-0.002, 0.002), 0.006,
            "M_timber_weathered", nx=4, ny=8, nz=3)
    for zl in (0.42, 1.15, 1.92):
        box(acc, xc - hw + 0.03, xc + hw - 0.03, zl - 0.07, zl + 0.07, lw0 - 0.04, lw0, 0.01, "M_timber_weathered")
    # three strap hinges (hinge on the west side = -x), latch on +x
    for zh in (0.42, 1.15, 1.92):
        n = 36
        us = np.linspace(0, 1, n)
        xsx = xc - hw + 0.01 + us * 0.70
        wd = strap_widths(us, 0.048, 0.036, 0.074) * (1 + 0.04 * n1(us * 6, int(zh * 50)))
        tk = 0.006 * (1 - 0.15 * us)
        path = wl(xsx, zh + 0.002 * n1(us * 5, int(zh * 31)), lw1 + 0.5 * tk)
        # profile: right = vertical strap width, up = outward normal (thickness) -> lies flat on the planks
        profs = np.stack([prof_rect(w_, t_, 0.0015) for w_, t_ in zip(wd, tk)])
        V, F = sweep(path, (0, -1, 0), profs)
        acci.add(V, F, "M_iron")
        ui = np.array([0.08, 0.28, 0.48, 0.66, 0.9])
        nail_heads(acci, wl(xc - hw + 0.01 + ui * 0.70, zh + np.array([0.008, -0.008, 0.008, -0.008, 0.0]),
                            lw1 + 0.006 * (1 - 0.15 * ui)), np.array([0, -1.0, 0]), rad=0.008)
        kp = wl(np.array([xc - hw + 0.005]), np.array([zh]), np.array([lw1]))[0]
        Vk, Fk = lathe([(0.015, -0.03), (0.015, 0.03)], 10, cx=kp[0], cy=kp[1], z0=zh)
        acci.add(Vk, Fk, "M_iron")
    # latch: thumb latch handle + bar
    hp = wl(np.array([xc + hw - 0.12]), np.array([1.05]), np.array([lw1]))[0]
    path = np.array([hp + np.array([0, 0, 0.09]), hp + np.array([0, -0.05, 0.06]), hp + np.array([0, -0.06, 0.0]),
                     hp + np.array([0, -0.05, -0.06]), hp + np.array([0, 0, -0.09])])
    V, F = sweep(path, (1, 0, 0), prof_rect(0.016, 0.01, 0.003))
    acci.add(V, F, "M_iron")
    for dz in (0.09, -0.09):
        V, F = lathe([(0.022, 0.0), (0.022, 0.004), (0.0, 0.006)], 10)
        acci.add(np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1) + hp + np.array([0, -0.0, dz]), F, "M_iron")
    # window (wing south wall, near the west end): frame, mullion, lintel, sill
    w = WWIN
    xw, hww = w["xc"], w["hw"]
    fd0, fd1 = -w["depth"] - 0.10, -w["depth"]
    box(accw, xw - hww - 0.07, xw - hww + 0.01, w["z0"] - 0.02, w["z1"] + 0.02, fd0, fd1, 0.01, "M_timber")
    box(accw, xw + hww - 0.01, xw + hww + 0.07, w["z0"] - 0.02, w["z1"] + 0.02, fd0, fd1, 0.01, "M_timber")
    box(accw, xw - hww - 0.07, xw + hww + 0.07, w["z1"] - 0.02, w["z1"] + 0.06, fd0, fd1, 0.01, "M_timber")
    box(accw, xw - 0.025, xw + 0.025, w["z0"], w["z1"], fd0 + 0.02, fd1 - 0.02, 0.008, "M_timber")
    box(accw, xw - hww - 0.30, xw + hww + 0.30, w["z1"] + 0.06, w["z1"] + 0.24, -0.45, 0.03, 0.02, "M_timber", nx=6,
        deform=lambda P: adze(P, 7))
    box(accw, xw - hww - 0.14, xw + hww + 0.14, w["z0"] - 0.12, w["z0"] - 0.005, -0.30, 0.07, 0.012, "M_stone_dressed",
        nx=6)
    finalize(acc, coll)
    finalize(acci, coll)
    finalize(accw, coll)


# ----------------------------------------------------------------------------------------------
# wing thatch
# ----------------------------------------------------------------------------------------------
SP_, CP_ = math.sin(W_PITCH), math.cos(W_PITCH)
PLANES = {
    "S": dict(o=lambda a, m: np.stack([a, (WY_S - W_OVH) + m * CP_, 2.40 + m * SP_], -1), n=np.array([0, -SP_, CP_]),
              a_rng=(WX_W - W_OVH - 0.3, WX_E + W_OVH)),
    "N": dict(o=lambda a, m: np.stack([a, (WY_N + W_OVH) - m * CP_, 2.40 + m * SP_], -1), n=np.array([0, SP_, CP_]),
              a_rng=(WX_W - W_OVH - 0.3, WX_E + W_OVH)),
    "W": dict(o=lambda a, m: np.stack([(WX_W - W_OVH) + m * CP_, a, 2.40 + m * SP_], -1), n=np.array([-SP_, 0, CP_]),
              a_rng=(WY_S - W_OVH - 0.3, WY_N + W_OVH + 0.3)),
}


def plane_under(name, x, y):
    if name == "S":
        return W_RAFT + (y - WY_S) * W_TAN
    if name == "N":
        return W_RAFT + (WY_N - y) * W_TAN
    return W_RAFT + (x - WX_W) * W_TAN


def thatch_cull(C, tol_skirt=True):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    bad = tur_dist(x, y, z) < -0.06
    ang = np.arctan2(y, x)
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = x * np.cos(kk * np.pi / 4) + y * np.sin(kk * np.pi / 4)
    zs = SKIRT.zb(pp)
    # inside the hall's plan: only what lies below the skirt sheathing (walls, plates, rafters) is culled; thatch
    # above the skirt runs on over it until it meets the collar / cone
    bad |= (pp < apo(np.clip(z, 0, WALL_H)) + 0.02) & (z < np.maximum(zs - 0.02, RAFTER_SEAT + 0.1))
    if tol_skirt:
        wt = wing_top(x, y)
        bad |= (pp < SKIRT.p_lip + 0.08) & (wt < zs + 0.07) & (z > zs - 0.27)
    r = np.hypot(x, y)
    bad |= (r < np.interp(z, CONE_ZF, CONE_RF) + 0.12) & (z > 4.4)
    # under the shake collar: the thatch runs on under the collar shakes (shakes buried in the thatch are dropped);
    # only cull what would pass through the collar backing frustum
    bad |= (z > 4.5) & (z < COLLAR_TOP_Z + 0.1) & (r < np.interp(z, [4.6, COLLAR_TOP_Z], [3.5, 2.95]) - 0.10)
    return bad


def runs_of_list(pts, min_len=3):
    runs, cur = [], []
    for p_ in list(pts) + [None]:
        if p_ is None:
            if len(cur) >= min_len:
                runs.append(np.array(cur))
            cur = []
        else:
            cur.append(p_)
    return runs


def runs_of(P, ok, min_len=3):
    runs, cur = [], []
    for i, o in enumerate(list(ok) + [False]):
        if o:
            cur.append(P[i])
        else:
            if len(cur) >= min_len:
                runs.append(np.array(cur))
            cur = []
    return runs


def thatch_roll(acc, path, r0, seed, flat=0.8, seg=12, mat="M_thatch", bind=0.16, stri=0.0, step=0.05):
    """lumpy bound thatch roll along a path (constrictions every ~0.34 m, irregular section).
    stri > 0: strand striations wrapping the roll (grooves every 1.5-3 cm along the path, depth = stri)."""
    path = np.asarray(path, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    if d[-1] < 0.1:
        return
    n = max(4, int(d[-1] / step))
    ds = np.linspace(0, d[-1], n)
    P = np.stack([np.interp(ds, d, path[:, i]) for i in range(3)], 1)
    bnd = (1 - bind) + bind * np.clip(np.abs(np.sin(np.pi * ds / 0.34 + seed)) * 2.2, 0, 1)
    rr = r0 * bnd * (1 + 0.12 * n1(ds * 1.3, seed))
    # ends taper and round off (rolls die into the neighbouring roll / surface instead of ending as flat caps)
    te = min(0.3, d[-1] * 0.3)
    endf = np.minimum(np.clip(ds / te, 0, 1), np.clip((d[-1] - ds) / te, 0, 1))
    rr = rr * (0.45 + 0.55 * np.sqrt(np.clip(1 - (1 - endf) ** 2, 0, 1)))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    profs = []
    for i in range(n):
        lump = 1 + 0.10 * fbm(np.stack([np.cos(a) * 1.7 + ds[i] * 4.0, np.sin(a) * 1.7, np.full(seg, seed * 3.3)], -1), 2)
        if stri > 0:
            ph = ds[i] / 0.022 + 2.5 * n1(np.full(seg, ds[i]) * 2.0 + a * 0.4, seed + 5)
            lump = lump - (stri / r0) * np.clip(np.cos(np.pi * ph) * 1.6 - 0.6, 0, 1) * (0.6 + 0.4 * np.sin(a) ** 2)
        profs.append(np.stack([rr[i] * np.cos(a) * lump, rr[i] * flat * np.sin(a) * lump], 1))
    V, F = sweep(P, (0, 0, 1), np.stack(profs))
    acc.add(V, F, mat)


# ---- eave roll: flattened, sheared D-section (q = inward horizontal from the eave line, v = up from the 2.40 lip)
TH_BASE = CORE_T + 0.02                 # perpendicular height of the course baseline (course far ends) above the deck
_ROLL_CTRL = np.array([
    (0.95, 0.5425 + 1.0724 * 0.95), (0.55, 0.5425 + 1.0724 * 0.55), (0.25, 0.8106), (0.08, 0.616), (0.0, 0.517),
    (-0.06, 0.428), (-0.11, 0.330), (-0.135, 0.220), (-0.126, 0.118), (-0.088, 0.044), (-0.025, 0.008),
    (0.07, 0.0), (0.20, 0.012), (0.31, 0.055), (0.375, 0.15), (0.41, 0.30), (0.43, 0.44),
    (0.55, 0.70), (0.90, 1.30)])
# visible weight per control point (ribs / bulges are only applied where the roll can be seen)
_ROLL_VIS = np.array([0, 0, 0.3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.8, 0.3, 0, 0], float)


def catmull_closed(C, n_per):
    """closed Catmull-Rom resample of control polygon C (k,2); n_per samples per span (array or int)."""
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


def roll_profile():
    nper = np.array([1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1])
    P, sid = catmull_closed(_ROLL_CTRL, nper)
    vis = np.interp(sid, np.arange(len(_ROLL_CTRL) + 1), np.concatenate([_ROLL_VIS, _ROLL_VIS[:1]]))
    return P, vis


ROLL_P, ROLL_VIS = roll_profile()


def _roll_top_mh():
    """roll upper surface in plane coords (m, h): used to seat the first course into the roll."""
    up = ROLL_P[:np.argmin(ROLL_P[:, 0]) + 1]            # tail -> nose (upper surface)
    q, v = up[:, 0], up[:, 1]
    m = q * CP_ + v * SP_
    h = -q * SP_ + v * CP_
    o = np.argsort(m)
    return m[o], h[o]


ROLL_TOP_M, ROLL_TOP_H = _roll_top_mh()


def roll_top_v(q):
    """vertical height (above the 2.40 lip) of the roll's upper surface at inward distance q; -inf beyond the nose."""
    up = ROLL_P[:np.argmin(ROLL_P[:, 0]) + 1]
    o = np.argsort(up[:, 0])
    q = np.asarray(q, float)
    v = np.interp(q, up[o, 0], up[o, 1])
    return np.where(q < up[:, 0].min(), -1e9, v)


def prof_normals(P):
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    N = np.stack([T[:, 1], -T[:, 0]], 1)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    c = P.mean(0)
    sgn = np.sign(np.sum((P - c) * N, 1, keepdims=True))
    sgn[sgn == 0] = 1
    return N * np.where(np.median(sgn) < 0, -1.0, 1.0)


def rib_stations(L, rng, sp=(0.01, 0.04), dep=(0.003, 0.015)):
    """irregular strand ribs along a roll: groove centres at 1-4 cm spacing, 0.3-1.5 cm deep; returns station
    positions and the groove depth at each station (midpoints between grooves carry 0)."""
    g = [rng.uniform(0, sp[1])]
    while g[-1] < L:
        g.append(g[-1] + rng.uniform(*sp))
    g = np.array(g[:-1])
    d = dep[0] + (dep[1] - dep[0]) * rng.uniform(0, 1, len(g)) ** 1.2
    mids = 0.5 * (g[1:] + g[:-1])
    st = np.concatenate([[0.0], g, mids, [L]])
    dd = np.concatenate([[0.0], d, np.zeros(len(mids)), [0.0]])
    o = np.argsort(st)
    st, dd = st[o], dd[o]
    keep = np.concatenate([[True], np.diff(st) > 0.002])
    return st[keep], dd[keep]


def d_roll(acc, path, prof, vis, seed, rng, up=(0.0, 0.0, 1.0), var=0.03, sp=(0.01, 0.04), dep=(0.003, 0.015),
           taper=(0.0, 0.0), mat="M_thatch", z_wave=0.012):
    """sweep a (D / dome) section along a path with irregular strand ribs (no regular binding), +-var section
    swelling over 0.5-1 m, and optional rounded tapers at the ends (taper lengths in m)."""
    path = np.asarray(path, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    L = d[-1]
    if L < 0.08:
        return
    st, dd = rib_stations(L, rng, sp, dep)
    P = np.stack([np.interp(st, d, path[:, i]) for i in range(3)], 1)
    P[:, 2] += z_wave * n1(st * 0.9, seed + 1)
    ups = np.asarray(up, float)
    if ups.ndim == 2:
        ups = np.stack([np.interp(st, d, ups[:, i]) for i in range(3)], 1)
    N2 = prof_normals(prof)
    cen = prof[vis > 0.5].mean(0) if (vis > 0.5).any() else prof.mean(0)
    pidx = np.arange(len(prof))
    profs = []
    for i, s in enumerate(st):
        sw = var * (0.65 * n1(np.full(len(prof), s / 0.75), seed) + 0.35 * n1(np.full(len(prof), s / 0.45), seed + 7))
        sw = sw * (0.75 + 0.25 * np.cos(pidx * 0.7 + s * 3.0))
        gr = dd[i] * (0.55 + 0.45 * n1(pidx * 0.45 + s * 5.0, seed + 3))
        pr = prof + N2 * ((sw - gr) * vis)[:, None]
        tf = 1.0
        if taper[0] > 0 and s < taper[0]:
            tf = 0.45 + 0.55 * math.sqrt(max(0.0, 1 - (1 - s / taper[0]) ** 2))
        if taper[1] > 0 and L - s < taper[1]:
            tf = min(tf, 0.45 + 0.55 * math.sqrt(max(0.0, 1 - (1 - (L - s) / taper[1]) ** 2)))
        if tf < 1.0:
            pr = cen + (pr - cen) * tf
        profs.append(pr)
    V, F = sweep(P, ups, np.stack(profs))
    acc.add(V, F, mat)
    return P


def eave_path():
    """plan path of the eave line N -> W -> S with rounded hipped corners (radius 0.32), at the 2.40 lip."""
    yS, yN, xW = WY_S - W_OVH, WY_N + W_OVH, WX_W - W_OVH
    xe = WX_E + W_OVH
    rc = 0.32
    pts = []
    for x in np.arange(xe, xW + rc, -0.02):
        pts.append((x, yN))
    for a in np.linspace(np.pi / 2, np.pi, 12)[1:-1]:
        pts.append((xW + rc + rc * np.cos(a), yN - rc + rc * np.sin(a)))
    for y in np.arange(yN - rc, yS + rc, -0.02):
        pts.append((xW, y))
    for a in np.linspace(np.pi, 1.5 * np.pi, 12)[1:-1]:
        pts.append((xW + rc + rc * np.cos(a), yS + rc + rc * np.sin(a)))
    for x in np.arange(xW + rc, xe + 1e-6, 0.02):
        pts.append((x, yS))
    P = np.array(pts)
    return np.column_stack([P, np.full(len(P), 2.40)])


def eave_q(x, y):
    """inward horizontal distance from the (rounded) eave line, for points inside the roof footprint."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    yS, yN, xW = WY_S - W_OVH, WY_N + W_OVH, WX_W - W_OVH
    rc = 0.32
    q = np.minimum(np.minimum(y - yS, yN - y), x - xW)
    cS = (x < xW + rc) & (y < yS + rc)
    q = np.where(cS, rc - np.hypot(x - (xW + rc), y - (yS + rc)), q)
    cN = (x < xW + rc) & (y > yN - rc)
    q = np.where(cN, rc - np.hypot(x - (xW + rc), y - (yN - rc)), q)
    return q


def thatch_top_z(x, y):
    """approximate outer thatch surface (course tops near the mean, roll top near the eaves)."""
    zt = wing_under(x, y) + (TH_BASE + 0.045) / CP_
    q = eave_q(x, y)
    zr = 2.40 + roll_top_v(q) + 0.0 * q
    return np.where(q < -0.135, -1e9, np.where(q < 0.6, zr, zt))


def thatch_courses(acc, name, rng, lobe_w, seed, m_max=4.15, m0=0.64):
    """Stepped thatch courses on one roof plane, each one continuous strip along the eave direction.
    Every course butt is a sheared, bevelled face cut back 31-39 deg from the roof plane, 0.06-0.10 m deep,
    built from rounded convex strand lobes (2.5-4 cm wide, crowned 0.6-1.3 cm, protrusion +-2 cm, creased
    between lobes). Exposure 0.26-0.34 m per course, low-frequency swelling +-2.5 cm over ~1.1 m, course lines
    wave +-2.5 cm; 1-2 courses per plane pinch out. Each butt tucks 3.5 cm under the course (or roll) below."""
    pl = PLANES[name]
    nrm = pl["n"]
    a_lo, a_hi = pl["a_rng"]
    o = pl["o"]
    e = 1e-3
    dA = o(np.array([e]), np.array([0.0]))[0] - o(np.array([0.0]), np.array([0.0]))[0]
    dM = o(np.array([0.0]), np.array([e]))[0] - o(np.array([0.0]), np.array([0.0]))[0]
    flip = np.dot(np.cross(dA, dM), nrm) < 0
    ms = []
    m = m0
    while m < m_max:
        E = rng.uniform(0.26, 0.34)
        ms.append((m, E))
        m += E
    nC = len(ms)
    npin = 2 if rng.uniform() < 0.6 else 1
    pinch_ids = set(int(v) for v in rng.choice(np.arange(2, nC - 2), npin, replace=False))
    prev = None
    nq_tot = 0

    def swell(a, mm):
        return 0.025 * vnoise(np.stack([a / 1.1, mm / 1.1, np.full_like(a, seed * 1.37)], -1))
    for ci, (m, E) in enumerate(ms):
        step = rng.uniform(0.085, 0.12)
        beta = math.radians(rng.uniform(31.0, 39.0))
        bnd = [a_lo - rng.uniform(0.0, 0.03)]
        while bnd[-1] < a_hi + 0.02:
            bnd.append(bnd[-1] + rng.uniform(*lobe_w))
        bnd = np.array(bnd)
        nl = len(bnd) - 1
        wl = np.diff(bnd)
        A = np.empty(3 * nl + 1)
        A[0::3] = bnd
        A[1::3] = bnd[:-1] + wl * rng.uniform(0.28, 0.38, nl)
        A[2::3] = bnd[:-1] + wl * rng.uniform(0.62, 0.72, nl)
        ncol = len(A)
        isb = np.zeros(ncol, bool)
        isb[0::3] = True
        lid = np.minimum(np.arange(ncol) // 3, nl - 1)
        # lobes come in loose clumps: protrusion varies smoothly over 4-8 lobes plus a little per-lobe jitter
        li = np.arange(nl)
        prot = np.clip(0.013 * n1(li * 0.22, seed * 31 + ci) + rng.normal(0, 0.004, nl), -0.02, 0.02)
        crown = rng.uniform(0.005, 0.010, nl)
        lean_l = rng.normal(0, 0.006, nl)
        lprev = np.maximum(lid - 1, 0)
        p_col = np.where(isb, np.minimum(prot[lprev], prot[lid]) - rng.uniform(0.003, 0.007, ncol), prot[lid])
        lean_c = np.where(isb, 0.5 * (lean_l[lprev] + lean_l[lid]), lean_l[lid])
        pinch = np.ones(ncol)
        if ci in pinch_ids:
            ac = rng.uniform(a_lo + 1.2, a_hi - 1.2)
            wpi = rng.uniform(0.9, 1.6)
            pinch = 1 - 0.86 * 0.5 * (1 + np.cos(np.pi * np.clip((A - ac) / (0.5 * wpi), -1, 1)))
        wave = 0.025 * n1(A / 1.1, seed * 100 + ci)
        stp = step * (1 + 0.15 * n1(A * 0.9, seed * 100 + ci + 50)) * pinch
        cr_ = np.where(isb, -rng.uniform(0.002, 0.005, ncol), crown[lid]) * pinch
        mi = m + wave
        mb = mi - p_col * pinch
        # height of the surface below at the tip (course below, or the eave roll for the first course)
        if prev is None:
            low = np.interp(mb, ROLL_TOP_M, ROLL_TOP_H)
        else:
            pA, pm3, ph3, pm4, ph4 = prev
            m3 = np.interp(A, pA, pm3)
            h3 = np.interp(A, pA, ph3)
            m4 = np.interp(A, pA, pm4)
            h4 = np.interp(A, pA, ph4)
            f = np.clip((mb - m3) / np.maximum(m4 - m3, 1e-3), 0, 1)
            low = h3 + (h4 - h3) * f
        sw_b = swell(A, mi)
        top = TH_BASE + stp + sw_b + np.where(isb, 0.45, 1.0) * cr_
        dh = np.maximum(top - low, 0.012)
        run = dh / math.tan(beta)
        m_far = mi + E + 0.07
        rows_m = np.stack([mb + 0.03, mb, mb + run - 0.012, mb + run + 0.022, m_far], 1)
        h_far = TH_BASE - 0.004 + swell(A, m_far) + 0.3 * cr_
        rows_h = np.stack([low - 0.035, low + 0.004 + np.where(isb, cr_, 0.0), top - 0.007, top, h_far], 1)
        Am = np.repeat(A[:, None], 5, 1)
        Am = Am + lean_c[:, None] * np.array([0.0, 0.0, 1.0, 1.2, 2.5])[None, :]
        Am = Am + 0.003 * n1(rows_m * 6.0 + A[:, None] * 0.4, seed + 9)
        W = o(Am, rows_m) + rows_h[..., None] * nrm
        # butts turn up 2-4 cm against the turret fillet
        dtu = tur_dist(W[..., 0], W[..., 1], W[..., 2])
        tu = 0.032 * np.clip(1 - dtu / 0.32, 0, 1) ** 1.5
        tu[:, 0] *= 0.0
        W = W + (tu[..., None] * nrm)
        rows_h = rows_h + tu
        # squashed under the hall skirt where the skirt is the upper roof; deep under it the courses are dropped
        zs_, pp_ = skirt_z_at(W[..., 0], W[..., 1])
        under = (pp_ < SKIRT.p_lip + 0.06) & (wing_top(W[..., 0], W[..., 1]) < zs_ + 0.07)
        W[..., 2] = np.where(under, np.minimum(W[..., 2], zs_ - 0.05 - 0.008 * (ci % 3)), W[..., 2])
        idx = np.arange(ncol * 5).reshape(ncol, 5)
        q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
        if flip:
            q = q[:, ::-1]
        Wf = W.reshape(-1, 3)
        C = Wf[q].mean(1)
        x_, y_ = C[:, 0], C[:, 1]
        bad = thatch_cull(C, tol_skirt=False)
        bad |= (plane_under(name, x_, y_) - wing_under(x_, y_)) > 0.05
        bad |= ~((x_ > WX_W - W_OVH - 0.12) & (x_ < WX_E + W_OVH + 0.04) & (y_ > WY_S - W_OVH - 0.12) &
                 (y_ < WY_N + W_OVH + 0.12))
        zsq, ppq = skirt_z_at(Wf[q][..., 0], Wf[q][..., 1])
        deep = ((ppq < SKIRT.p_lip - 0.35) & (Wf[q][..., 2] < zsq - 0.04)).all(1)
        bad |= deep
        q = q[~bad]
        if len(q):
            used = np.unique(q)
            remap = -np.ones(ncol * 5, np.int64)
            remap[used] = np.arange(len(used))
            acc.add(Wf[used], remap[q], "M_thatch", uv=np.stack([Am.ravel(), rows_m.ravel()], -1)[used])
            nq_tot += len(q)
        prev = (A, rows_m[:, 3], rows_h[:, 3], rows_m[:, 4], rows_h[:, 4])
    return nC, nq_tot


def build_wing_roof(coll):
    rng = np.random.default_rng(1313)
    acc = Acc("KEEP_wing_roof_thatch")
    # --- thatch core body (height field over the roof footprint): top + underside; thinned toward the eaves so
    # its edge is buried >= 6 cm inside the eave roll
    xs = np.arange(WX_W - W_OVH, WX_E + W_OVH + 1e-6, 0.09)
    ys = np.linspace(WY_S - W_OVH, WY_N + W_OVH, 60)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zu = wing_under(X, Y)
    Zt = Zu + CORE_T / CP_
    qe = eave_q(X, Y)
    Zt = Zt - 0.10 * np.clip(1 - qe / 0.5, 0, 1)
    zsk, ppk = skirt_z_at(X, Y)
    under = (ppk < SKIRT.p_lip + 0.1) & (wing_top(X, Y) < zsk + 0.07)
    Zt = np.where(under, np.minimum(Zt, zsk - 0.24), Zt)
    Zu = np.minimum(Zu, Zt - 0.06)
    nx_, ny_ = X.shape
    idx = np.arange(nx_ * ny_).reshape(nx_, ny_)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    xm, ym = 0.5 * (X[:-1, :-1] + X[1:, 1:]), 0.5 * (Y[:-1, :-1] + Y[1:, 1:])
    ztm = 0.25 * (Zt[:-1, :-1] + Zt[1:, :-1] + Zt[1:, 1:] + Zt[:-1, 1:])
    keep = ~thatch_cull(np.stack([xm, ym, ztm], -1), tol_skirt=False)
    keep &= ~(tur_dist(xm, ym, ztm) < -0.05)
    keep &= eave_q(xm, ym) > -0.01
    Vt = np.stack([X, Y, Zt], -1).reshape(-1, 3)
    Vb = np.stack([X, Y, Zu], -1).reshape(-1, 3)
    acc.add(Vt, quads[keep.ravel()], "M_thatch")
    acc.add(Vb, quads[keep.ravel()][:, ::-1], "M_thatch")
    # east verge closing strip (under the hall skirt)
    yv = ys
    xe = np.full_like(yv, xs[-1])
    V = np.concatenate([np.stack([xe, yv, Zu[-1]], 1), np.stack([xe, yv, Zt[-1]], 1)])
    n = len(yv)
    q = np.array([(i, i + 1, n + i + 1, n + i) for i in range(n - 1)])
    cv = np.stack([xe, yv, Zu[-1] + 0.1], 1)
    acc.add(V, q[~thatch_cull(cv[:-1], tol_skirt=False)], "M_thatch")
    # --- continuous stepped courses with bevelled lobe butts
    accc = Acc("KEEP_wing_roof_thatch_courses")
    for name, lw, sd in (("S", (0.025, 0.036), 3), ("N", (0.028, 0.040), 5), ("W", (0.026, 0.038), 7)):
        n_c, n_q = thatch_courses(accc, name, rng, lw, sd)
        log(f"  thatch {name}: {n_c} courses, {n_q} quads")
    finalize(accc, coll, smooth_deg=60.0, recalc=False)
    # --- eave roll: one continuous D-section roll N -> W -> S round the hipped corners
    path = eave_path()
    x, y = path[:, 0], path[:, 1]
    hall_in = thatch_cull(path + np.array([0, 0, 0.3]), tol_skirt=False) & (np.hypot(x, y) < 6.0)
    # cut where the whole section is buried in the turret stone (W eave)
    T = np.gradient(path, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Rv = np.cross(np.array([0, 0, 1.0]), T)
    probes = [(-0.135, 0.22), (-0.06, 0.43), (0.0, 0.52), (0.43, 0.44), (0.07, 0.0), (0.25, 0.81)]
    inside_all = np.ones(len(path), bool)
    for qq, vv in probes:
        Pp = path + Rv * qq + np.array([0, 0, vv])
        inside_all &= tur_dist(Pp[:, 0], Pp[:, 1], Pp[:, 2]) < -0.03
    ok = ~hall_in & ~inside_all
    global EAVE_RUNS
    EAVE_RUNS = []
    for r_ in runs_of(path, ok, min_len=4):
        EAVE_RUNS.append(d_roll(acc, r_, ROLL_P, ROLL_VIS, 5 + len(r_), rng, var=0.03))
    finalize(acc, coll, smooth_deg=70.0)


EAVE_RUNS = []
HIP_DOME = np.array([(-0.27, -0.17), (-0.235, -0.06), (-0.19, 0.035), (-0.12, 0.105), (-0.035, 0.14), (0.05, 0.138),
                     (0.13, 0.10), (0.20, 0.03), (0.24, -0.06), (0.27, -0.17), (0.0, -0.22)])
HIP_VIS = np.array([0.2, 1, 1, 1, 1, 1, 1, 1, 1, 0.2, 0.0])
RIDGE_DOME = np.array([(-0.31, -0.40), (-0.30, -0.30), (-0.265, -0.15), (-0.205, -0.02), (-0.12, 0.075),
                       (-0.02, 0.115), (0.08, 0.10), (0.17, 0.035), (0.24, -0.07), (0.29, -0.22), (0.31, -0.40),
                       (0.0, -0.50)])
RIDGE_VIS = np.array([0.2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.2, 0.0])


def ridge_dome_top(lat):
    """height of the ridge dome's upper surface above the ridge apex at lateral offset lat."""
    P = RIDGE_DOME[:-1]
    return np.interp(lat, P[:, 0], P[:, 1])


def turret_outer(x, y, z):
    """signed distance from the turret envelope including the cushion collar (for ridge / comb ends)."""
    th = np.arctan2(np.asarray(y) - TUR_C[1], np.asarray(x) - TUR_C[0])
    r = np.hypot(np.asarray(x) - TUR_C[0], np.asarray(y) - TUR_C[1])
    z = np.asarray(z, float)
    in_c = (z > cush_lip_z(th) - 0.02) & (z < 6.66)
    rr = np.where(in_c, np.maximum(cush_out_r(th) - 0.03, tur_r(z)), tur_r(z))
    return r - rr


def build_wing_ridge(coll):
    rng = np.random.default_rng(1414)
    acc = Acc("KEEP_wing_ridge_comb")
    acct = Acc("KEEP_wing_roof_rolls")
    x_apex = WX_W + (WY_R - WY_S)
    z_apex = W_RAFT + (WY_R - WY_S) * W_TAN + (TH_BASE + 0.045) / CP_
    xs = np.arange(x_apex - 0.6, WX_E - 0.2, 0.03)
    path = np.stack([xs, np.full_like(xs, WY_R), np.full_like(xs, z_apex)], 1)
    path[:, 2] += 0.03 * n1(xs * 0.5, 31) - 0.03 * np.sin(np.pi * np.clip((xs - x_apex) / (WX_E - x_apex), 0, 1))
    ok = ~thatch_cull(path + np.array([0, 0, -0.3]), tol_skirt=False)
    # west end: the dome dies into the turret body / under the drooping cushion (whole section inside)
    ok &= turret_outer(path[:, 0], path[:, 1] - 0.0, path[:, 2] - 0.2) > -0.25
    best, cur = (0, 0), 0
    for i, o_ in enumerate(list(ok) + [False]):
        if o_:
            cur += 1
        else:
            if cur > best[1] - best[0]:
                best = (i - cur, i)
            cur = 0
    path = path[best[0]:best[1]]
    global RIDGE_PATH
    RIDGE_PATH = path
    d_roll(acct, path, RIDGE_DOME, RIDGE_VIS, 71, rng, var=0.02, sp=(0.012, 0.04), dep=(0.003, 0.012))
    # ridge-rider log, seated 3 cm into the dome; starts clear of the cushion
    lp = path + np.array([0, 0, 0.115 + 0.07 - 0.03])
    okl = turret_outer(lp[:, 0], lp[:, 1], lp[:, 2]) > -0.08
    lp = lp[np.argmax(okl):]
    LOG_R = 0.07
    V, F = sweep(lp, (0, 0, 1), prof_circle(LOG_R, 12))
    acc.add(V, F, "M_timber_weathered")
    # comb: stubby, dense crossed split shakes (V/X pairs) pinned by the log; butts end >= 4 cm inside the dome
    x = lp[0, 0] + rng.uniform(0.08, 0.14)
    x_end = lp[-1, 0] - 0.06
    recs = []
    while x < x_end:
        psi = math.radians(rng.choice([-1, 1]) * rng.uniform(10, 36))
        hdir = np.array([math.sin(psi), math.cos(psi), 0.0])
        zl = float(np.interp(x, lp[:, 0], lp[:, 2]))
        zc = zl + LOG_R + 0.03
        u = rng.uniform()
        sides = (-1, 1) if u > 0.12 else ((rng.choice([-1, 1]),))
        for side in sides:
            lean = math.radians(rng.uniform(18, 36))
            D = side * math.sin(lean) * hdir + math.cos(lean) * np.array([0, 0, 1.0])
            D += np.array([rng.normal(0, 0.06), 0, 0])
            D /= np.linalg.norm(D)
            Lup = rng.uniform(0.12, 0.36) if rng.uniform() < 0.75 else rng.uniform(0.30, 0.42)
            cross = np.array([x + rng.normal(0, 0.012), WY_R + rng.normal(0, 0.01), zc + rng.normal(0, 0.01)])
            # walk down the shake axis until the butt is >= 4.5 cm inside the dome (or near the log axis)
            Ldn = 0.06
            buried = False
            while Ldn < 0.32:
                pb = cross - D * Ldn
                lat = pb[1] - WY_R
                zd = float(np.interp(pb[0], path[:, 0], path[:, 2])) + float(ridge_dome_top(lat)) - 0.015
                dl = math.hypot(lat, pb[2] - zl)
                if pb[2] < zd - 0.045 or dl < LOG_R - 0.025:
                    buried = True
                    break
                Ldn += 0.01
            if not buried:
                # steep leaners: stand them more upright and end the butt inside the rider log
                lean = min(lean, math.atan(0.035 / (zc - zl)))
                D = side * math.sin(lean) * hdir + math.cos(lean) * np.array([0, 0, 1.0])
                D /= np.linalg.norm(D)
                Ldn = (zc - zl) / max(D[2], 0.5)
            recs.append((cross - D * Ldn, D, Lup + Ldn, rng.uniform(0.06, 0.12), rng.uniform(0.02, 0.04),
                         int(rng.integers(0, 3)), math.radians(rng.uniform(20, 40)) * rng.choice([-1, 1]),
                         rng.uniform(0.02, 0.05), Ldn))
        x += rng.uniform(0.10, 0.22)
    M = len(recs)
    base = np.array([r[0] for r in recs])
    D = np.array([r[1] for r in recs])
    L = np.array([r[2] for r in recs])
    wd = np.array([r[3] for r in recs])
    th = np.array([r[4] for r in recs])
    kind = np.array([r[5] for r in recs])
    cang = np.array([r[6] for r in recs])
    notch = np.array([r[7] for r in recs])
    E = np.cross(D, np.stack([np.zeros(M), np.zeros(M), np.ones(M)], 1))
    En = np.linalg.norm(E, axis=1, keepdims=True)
    E = np.where(En > 1e-3, E / np.maximum(En, 1e-6), np.array([[1.0, 0, 0]]))
    Nn = np.cross(E, D)
    rr = np.full(M, 0.006)
    X = axn(-wd / 2, wd / 2, rr, 6)
    Y = axn(np.zeros(M), L, rr, 8)
    Z = ax4(th / 2, rr)
    P, qd = rbox(X, Y, Z, rr)
    x_, u, h = P[..., 0], P[..., 1], P[..., 2]
    xn = x_ / (wd[:, None] / 2)
    tip = np.clip((u - (L[:, None] - 0.10)) / 0.10, 0, 1)
    u = u - np.where((kind == 1)[:, None], np.tan(np.abs(cang))[:, None] * (0.5 + 0.5 * np.sign(cang)[:, None] * xn)
                     * wd[:, None] * tip * 0.6, 0.0)
    u = u - np.where((kind == 2)[:, None] & (np.abs(xn) < 0.3), notch[:, None] * tip, 0.0)
    u = u - 0.008 * tip * np.abs(np.sin(xn * 4.0 + L[:, None] * 37.0))
    h = h * (1 - 0.3 * u / L[:, None])
    # riven faces: 2 shallow longitudinal ridges
    h = h + 0.002 * np.cos(xn * np.pi * 1.5 + L[:, None] * 11) * (h > 0)
    Wc = base[:, None, :] + u[..., None] * D[:, None, :] + x_[..., None] * E[:, None, :] + h[..., None] * Nn[:, None, :]
    acc.add(Wc.reshape(-1, 3), inst_faces(qd, M, P.shape[1]), "M_roof_shake", uv=np.stack([x_, u], -1).reshape(-1, 2))
    ldn = np.array([r[8] for r in recs])
    log("  ridge comb shakes", M, "butt depth below crossing: min %.2f mean %.2f max %.2f" % (ldn.min(), ldn.mean(), ldn.max()))
    for xx in np.arange(lp[0, 0] + 0.3, lp[-1, 0], 0.9):
        zz = np.interp(xx, lp[:, 0], lp[:, 2])
        peg(acc, np.array([xx, WY_R, zz + LOG_R]), np.array([0, 0, 1.0]), rad=0.016, proud=0.03)
    # west hip rolls (dome section on the hip line), from the eave roll at the corner up to the turret fillet
    global HIP_ENDS
    HIP_ENDS = []
    for sy in (-1, 1):
        corner = np.array([WX_W - W_OVH + 0.32 * 0.3, (WY_S - W_OVH + 0.32 * 0.3) if sy < 0 else (WY_N + W_OVH - 0.32 * 0.3)])
        apex = np.array([x_apex, WY_R])
        t = np.linspace(0, 1, 200)[:, None]
        xy = corner * (1 - t) + apex * t
        z = np.minimum(plane_under("W", xy[:, 0], xy[:, 1]),
                       plane_under("S" if sy < 0 else "N", xy[:, 0], xy[:, 1]))
        nS = PLANES["S" if sy < 0 else "N"]["n"]
        nW = PLANES["W"]["n"]
        nb_ = nS + nW
        nb_ /= np.linalg.norm(nb_)
        hp = np.column_stack([xy, z + (TH_BASE + 0.05) / CP_])
        hp[:, 2] -= 0.40 * np.clip(1 - t[:, 0] / 0.16, 0, 1) ** 1.6
        # stop where the dome meets the fillet against the turret stone
        dt = tur_dist(hp[:, 0], hp[:, 1], hp[:, 2])
        stop = np.flatnonzero(dt < 0.10)
        i_end = int(stop[0]) if len(stop) else len(hp)
        hp = hp[:i_end]
        if len(hp) > 4:
            d_roll(acct, hp, HIP_DOME, HIP_VIS, 61 + sy, rng, up=nb_, var=0.02, sp=(0.012, 0.04),
                   dep=(0.003, 0.012), taper=(0.0, 0.28))
            HIP_ENDS.append((hp[-1], (hp[-1] - hp[-2]) / np.linalg.norm(hp[-1] - hp[-2]), nb_))
    finalize(acc, coll)
    finalize(acct, coll, smooth_deg=70.0)


RIDGE_PATH = None
HIP_ENDS = []


def build_wing_structure(coll):
    """wall plates, rafter poles and battens visible in the eave gap; thatch/stone fillets."""
    rng = np.random.default_rng(1515)
    acc = Acc("KEEP_wing_roof_structure")
    accf = Acc("KEEP_wing_flashing")
    # wall plates on S and N walls
    for y, sgn in ((WY_S, 1), (WY_N, -1)):
        beam(acc, np.array([WX_W + 0.1, y + sgn * 0.12, W_WALL_H + 0.1]), np.array([-3.95 if sgn > 0 else WX_E - 0.05,
             y + sgn * 0.12, W_WALL_H + 0.1]), 0.22, 0.2, 0.02, "M_timber", nx=10)
    # rafter poles every ~0.6 m with battens across
    for name in ("S", "N"):
        pl = PLANES[name]
        for xr in np.arange(WX_W + 0.35, WX_E + 0.3, 0.62):
            xr2 = xr + rng.normal(0, 0.03)
            m0, m1 = 0.16, 1.25
            ms = np.linspace(m0, m1, 6)
            path = pl["o"](np.full_like(ms, xr2), ms) - pl["n"] * 0.12
            if thatch_cull(path.mean(0)[None], tol_skirt=False)[0]:
                continue
            if tur_dist(path[:, 0], path[:, 1], path[:, 2]).min() < 0.15:
                continue
            zs_, pp_ = skirt_z_at(path[:, 0], path[:, 1])
            if (pp_ < SKIRT.p_lip + 0.4).any():
                continue
            V, F = sweep(path, pl["n"], prof_circle(0.058 + rng.uniform(-0.006, 0.006), 9))
            acc.add(V, F, "M_timber_weathered")
        for mb in (0.15, 0.45, 0.75):
            a = np.linspace(WX_W - 0.2, WX_E + W_OVH - 0.1, 30)
            path = pl["o"](a, np.full_like(a, mb)) - pl["n"] * 0.04
            ok = ~thatch_cull(path, tol_skirt=False) & (tur_dist(path[:, 0], path[:, 1], path[:, 2]) > 0.12)
            ok &= skirt_z_at(path[:, 0], path[:, 1])[1] > SKIRT.p_lip + 0.4
            if ok.sum() < 3:
                continue
            path = path[ok]
            V, F = sweep(path, pl["n"], prof_circle(0.024, 7))
            acc.add(V, F, "M_timber_weathered")
    finalize(acc, coll)
    # lime-mortar fillet where the thatch meets the turret stone (S, W and N): irregular, 8-12 cm high on the
    # stone, 5-8 cm out over the thatch; the course butts turn up into it
    frng = np.random.default_rng(1516)
    ell = np.stack([np.cos(np.linspace(0, 2 * np.pi, 12, endpoint=False)),
                    np.sin(np.linspace(0, 2 * np.pi, 12, endpoint=False))], 1)

    def mortar_tube(pts, ups, rx, ry, seed):
        pts = np.asarray(pts, float)
        if len(pts) < 3:
            return
        prof = ell * np.array([rx, ry])
        d_roll(accf, pts, prof, np.ones(len(prof)), seed, frng, up=ups, var=0.016, sp=(0.03, 0.08),
               dep=(0.0, 0.004), taper=(0.04, 0.04), mat="M_mortar", z_wave=0.0)
    # find the real outer thatch surface next to the stone by ray-casting down onto the built thatch meshes
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(bpy.data.objects[nm], dg) for nm in
             ("KEEP_wing_roof_thatch_courses", "KEEP_wing_roof_thatch", "KEEP_wing_roof_rolls") if nm in bpy.data.objects]
    pts = []
    for th in np.linspace(0, 2 * np.pi, 720, endpoint=False):
        best = None
        for zz in np.arange(6.4, 2.3, -0.04):
            r = float(tur_reff(th, zz)) + 0.035
            x, y = TUR_C[0] + r * math.cos(th), TUR_C[1] + r * math.sin(th)
            zh = None
            for tr in trees:
                hit = tr.ray_cast(Vector((x, y, zz + 0.04)), Vector((0, 0, -1.0)), 0.08)
                if hit[0] is not None and (zh is None or hit[0].z > zh):
                    zh = hit[0].z
            if zh is not None:
                best = (x, y, zh)
                break
        if best is None:
            pts.append(None)
            continue
        x, y, zh = best
        zsk, ppk = skirt_z_at(np.array([x]), np.array([y]))
        if x > WX_E - 0.3 or float(ppk[0]) < SKIRT.p_lip + 0.1:
            pts.append(None)
            continue
        r = float(tur_reff(th, zh))
        pts.append(np.array([TUR_C[0] + r * math.cos(th), TUR_C[1] + r * math.sin(th), zh + 0.01]))
    # median-smooth the heights round the loop (course steps become gentle ramps under the fillet)
    zs_ = np.array([p_[2] if p_ is not None else np.nan for p_ in pts])
    for i_ in range(len(pts)):
        if pts[i_] is None:
            continue
        w_ = zs_[[(i_ + k_) % len(pts) for k_ in range(-4, 5)]]
        w_ = w_[~np.isnan(w_)]
        pts[i_] = pts[i_].copy()
        pts[i_][2] = max(float(np.median(w_)), pts[i_][2] - 0.02)
    first_none = next((i for i, p_ in enumerate(pts) if p_ is None), 0)
    pts = pts[first_none:] + pts[:first_none]
    wedge = np.array([(0.13, -0.035), (0.118, 0.003), (0.09, 0.011), (0.058, 0.024), (0.03, 0.043), (0.008, 0.06),
                      (-0.012, 0.07), (-0.03, 0.062), (-0.07, 0.03), (-0.08, -0.035)])
    for r_ in runs_of_list(pts, 4):
        # resample evenly and smooth the curve
        dd_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(r_, axis=0), axis=1))])
        ss_ = np.arange(0, dd_[-1], 0.03)
        r_ = np.stack([np.interp(ss_, dd_, r_[:, i]) for i in range(3)], 1)
        for _ in range(3):
            r_[1:-1] = 0.25 * r_[:-2] + 0.5 * r_[1:-1] + 0.25 * r_[2:]
        if len(r_) < 4:
            continue
        ups = np.column_stack([r_[:, 0] - TUR_C[0], r_[:, 1] - TUR_C[1], np.zeros(len(r_))])
        ups /= np.linalg.norm(ups, axis=1, keepdims=True)
        T_ = np.gradient(r_, axis=0)
        Rz = np.cross(ups, T_)[:, 2].mean()
        prof = wedge * np.array([1.0 if Rz > 0 else -1.0, 1.0])
        # irregular: top edge height and toe reach vary along the run, small lumps
        n_ = len(r_)
        sc_top = 1 + 0.22 * n1(ss_[:n_] / 0.55, 400 + n_)
        sc_out = 1 + 0.25 * n1(ss_[:n_] / 0.45, 410 + n_)
        profs = []
        for i_ in range(n_):
            pr = prof.copy()
            pr[:, 0] = np.where(pr[:, 0] * np.sign(prof[0, 0]) > 0, pr[:, 0] * sc_top[i_], pr[:, 0])
            pr[:, 1] = np.where(pr[:, 1] > 0, pr[:, 1] * sc_out[i_], pr[:, 1])
            pr = pr + 0.004 * n1(np.arange(len(pr)) * 1.3 + i_ * 0.7, 420)[:, None]
            profs.append(pr)
        V, F = sweep(r_, ups, np.stack(profs))
        accf.add(V, F, "M_mortar")
    # collars where the eave roll dives into the stone (W eave): trace the roll section's entry curve
    for P in EAVE_RUNS:
        if P is None or len(P) < 5:
            continue
        T = np.gradient(P, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True)
        Rv = np.cross(np.array([0, 0, 1.0]), T)
        vis_idx = np.flatnonzero(ROLL_VIS > 0.5)
        for end in (0, -1):
            nose = P[end] + Rv[end] * -0.135 + np.array([0, 0, 0.22])
            if tur_dist(nose[0], nose[1], nose[2]) > 0:
                continue
            order = np.arange(len(P)) if end == 0 else np.arange(len(P))[::-1]
            cur = []
            for j in vis_idx:
                q_, v_ = ROLL_P[j]
                Q = P[order] + Rv[order] * q_ + np.array([0, 0, v_])
                dd = tur_dist(Q[:, 0], Q[:, 1], Q[:, 2])
                k = np.flatnonzero(dd > 0)
                if len(k):
                    cur.append(Q[k[0]])
            if len(cur) > 3:
                C = np.array(cur)
                ups = np.column_stack([C[:, 0] - TUR_C[0], C[:, 1] - TUR_C[1], np.zeros(len(C))])
                ups /= np.linalg.norm(ups, axis=1, keepdims=True)
                tg = np.gradient(C, axis=0)
                ups = ups - (ups * tg).sum(1, keepdims=True) * tg / np.maximum((tg * tg).sum(1, keepdims=True), 1e-9)
                mortar_tube(C, ups, 0.085, 0.045, 77 + len(cur))
    # ridge dome entering the turret body / under the cushion
    if RIDGE_PATH is not None and len(RIDGE_PATH) > 4:
        P = RIDGE_PATH
        cur = []
        for lat, dz in RIDGE_DOME[1:-2]:
            Q = P + np.array([0, lat, dz])
            dd = turret_outer(Q[:, 0], Q[:, 1], Q[:, 2])
            k = np.flatnonzero(dd > 0)
            if len(k):
                cur.append(Q[k[0]])
        if len(cur) > 3:
            C = np.array(cur)
            ups = np.tile(np.array([[1.0, 0, 0]]), (len(C), 1))
            mortar_tube(C, ups, 0.085, 0.045, 91)
    # hip-roll ends bedded on the fillet: a mortar saddle joining the tapered roll end to the stone
    for pe, de, nb_ in HIP_ENDS:
        cen = pe + de * 0.05 - nb_ * 0.02
        V, F = lathe([(0.0, -0.11), (0.10, -0.095), (0.165, -0.04), (0.17, 0.0), (0.13, 0.06), (0.06, 0.095),
                      (0.0, 0.10)], 14)
        V[:, :2] *= (1 + 0.12 * fbm(V * 7 + 3.3, 2))[:, None]
        zax = nb_
        xax = np.cross(zax, np.array([0, 0, 1.0]))
        xax = xax / (np.linalg.norm(xax) + 1e-9) if np.linalg.norm(xax) > 1e-6 else np.array([1.0, 0, 0])
        yax = np.cross(zax, xax)
        W = cen + V[:, 0:1] * xax + V[:, 1:2] * yax + V[:, 2:3] * zax
        accf.add(W, F, "M_mortar")
    # fillet where thatch meets the hall wall (W facet / N facet)
    pts = []
    for t in np.linspace(0.05, 1.0 - 0.07, 220):
        s = t * hall_L(3.0)
        lo, hi = 2.0, WALL_H
        P = hall_map(np.array([s]), np.array([hi]), np.array([0.0]), np.array([3.0]))[0]
        if not ((P[0] < WX_E + 0.3) and (P[1] > WY_S - 0.6) and (P[1] < WY_N + 0.6)):
            continue
        def g(z):
            Q = hall_map(np.array([s]), np.array([z]), np.array([0.0]), np.array([3.0]))[0]
            return z - float(wing_top(Q[0], Q[1])), Q
        if g(lo)[0] > 0 or g(hi)[0] < 0:
            continue
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if g(mid)[0] > 0:
                hi = mid
            else:
                lo = mid
        pts.append(g(lo)[1])
    if len(pts) > 3:
        pts = np.array(pts)
        thatch_roll(accf, pts - np.array([0, 0, 0.03]), 0.06, 53, flat=0.75, seg=10, mat="M_mortar")
    # lead flashing in the valley where the hall skirt roof and the wing thatch intersect
    for k in range(1, 8):
        P_ = []
        for x in np.linspace(-SKIRT.p_lip * TAN22, SKIRT.p_lip * TAN22, 160):
            ps = np.linspace(SKIRT.p_lip + 0.02, max(abs(x) / TAN22 + 0.05, 3.0), 120)
            Sp = SKIRT.surf(np.full(len(ps), k), np.full(len(ps), x), ps)
            xx, yy = Sp[:, 0], Sp[:, 1]
            inside = (xx > WX_W - W_OVH) & (xx < WX_E + W_OVH) & (yy > WY_S - W_OVH) & (yy < WY_N + W_OVH)
            zt = np.where(inside, wing_under(xx, yy) + TH_V_MIN + 0.03, -10.0)
            d = Sp[:, 2] + SKIRT_SHEATH - zt
            hit = np.flatnonzero((d[:-1] > 0) & (d[1:] <= 0))
            if len(hit) == 0 or not inside[hit[0]]:
                P_.append(None)
                continue
            i = hit[0]
            f = d[i] / (d[i] - d[i + 1])
            q = Sp[i] * (1 - f) + Sp[i + 1] * f
            P_.append(q + np.array([0, 0, 0.035]))
        runs, cur = [], []
        for q in P_ + [None]:
            if q is None:
                if len(cur) > 4:
                    runs.append(np.array(cur))
                cur = []
            else:
                cur.append(q)
        for r_ in runs:
            thatch_roll(accf, r_, 0.12, 57 + k, flat=0.28, seg=10, mat="M_lead", bind=0.0)
    # lead flashing where the wing thatch dies into the shake collar (collar surface line butt -> top)
    P_ = []
    for th in np.linspace(0, 2 * np.pi, 720, endpoint=False):
        kf = int(np.round(th / (math.pi / 4))) % 8
        delta = (th - kf * math.pi / 4 + math.pi) % (2 * math.pi) - math.pi
        rb = COLLAR_P / math.cos(delta) + 0.06
        zb = float(skirt_z_at(np.array([rb * math.cos(th)]), np.array([rb * math.sin(th)]))[0][0]) + 0.13
        t = np.linspace(0, 1, 80)
        rr_ = rb + (COLLAR_TOP_R + 0.07 - rb) * t
        zz_ = zb + (COLLAR_TOP_Z - zb) * t
        xx, yy = rr_ * math.cos(th), rr_ * math.sin(th)
        inside = (xx > WX_W - W_OVH) & (xx < WX_E + W_OVH) & (yy > WY_S - W_OVH) & (yy < WY_N + W_OVH)
        d = zz_ - np.where(inside, wing_under(xx, yy) + TH_V_MIN + 0.04, -10.0)
        hit = np.flatnonzero((d[:-1] < 0) & (d[1:] >= 0))
        if len(hit) == 0 or not inside[hit[0]]:
            P_.append(None)
            continue
        i = hit[0]
        f = -d[i] / (d[i + 1] - d[i])
        P_.append(np.array([xx[i] + (xx[i + 1] - xx[i]) * f, yy[i] + (yy[i + 1] - yy[i]) * f, zz_[i] + (zz_[i + 1] - zz_[i]) * f]))
    runs, cur = [], []
    for q in P_ + [None]:
        if q is None:
            if len(cur) > 4:
                runs.append(np.array(cur))
            cur = []
        else:
            cur.append(q)
    for r_ in runs:
        thatch_roll(accf, r_, 0.12, 97, flat=0.35, seg=10, mat="M_lead", bind=0.0)
    finalize(accf, coll)


# ==============================================================================================
# SIDE TURRET
# ==============================================================================================
def tur_map(s, z, w, zc):
    rc = tur_r(zc)
    th = np.asarray(s, float) / rc + math.pi * 0.0
    r = tur_reff(th, z)
    e = 1e-3
    drdz = (tur_r(np.asarray(z) + e) - tur_r(np.asarray(z) - e)) / (2 * e)
    nr = 1 / np.sqrt(1 + drdz ** 2)
    R = r + np.asarray(w) * nr
    return np.stack([TUR_C[0] + R * np.cos(th), TUR_C[1] + R * np.sin(th), np.asarray(z) - np.asarray(w) * drdz * nr], -1)


CUSH_E = math.radians(-25.0)        # the cushion leans out / droops toward E-SE (ref1)


def cush_out_r(th):
    """outer radius of the cushion about the turret axis: 0.40-0.45 m proud of the body on E/SE, 0.12-0.18 on W/NW."""
    return TUR_R_TOP + 0.285 + 0.145 * np.cos(np.asarray(th, float) - CUSH_E)


def cush_lip_z(th):
    return 5.80 - 0.065 * (1 + np.cos(np.asarray(th, float) - CUSH_E))


TUR_R_TOP = 1.25


TUR_CAP = OctRoof(TUR_C[0], TUR_C[1], p_lip=1.5, z_lip=7.10, d_pts=[0, 0.25, 0.45, 1.5], a_pts=[22, 32, 46, 47],
                  p_min=0.02, kick=0.03, kick_len=0.45, wave=0.008, sag=0.012, seed=13, rot_deg=8.0)


def build_cushion(coll, rng):
    """lopsided, drooping stone cushion under the turret cap (ref1): 13 irregular weathered boulders (one split
    into two), offset toward E/SE, top tilted down ~10 deg more on that side, lower lip drooping ~0.13 m lower there;
    creased joints, +-6 cm height variation round the ring, cleaved flat facets on ~40 % of the boulders."""
    acc = Acc("KEEP_turret_corbel_collar")
    NT, NR = 340, 34
    th = np.linspace(0, 2 * np.pi, NT, endpoint=False)
    e = np.cos(th - CUSH_E)
    r_out = cush_out_r(th)
    z_lip = cush_lip_z(th)
    z_in = 6.62
    slope = np.radians(14.0 + 10.0 * (1 + e) / 2)
    # boulders: partition of the ring (arc lengths 0.55-0.95 m on the outer face), per-boulder height offsets
    nb = 13
    w = rng.uniform(0.7, 1.3, nb)
    bnd = np.concatenate([[0], np.cumsum(w) / w.sum() * 2 * np.pi]) + rng.uniform(0, 0.5)
    dzb = rng.uniform(-0.06, 0.06, nb)
    bulge = rng.uniform(0.018, 0.04, nb)
    drb = rng.uniform(-0.022, 0.03, nb)                  # boulders sit proud / back of their neighbours
    bedj = {int(b): (rng.uniform(0.36, 0.58), rng.uniform(-0.12, 0.12), rng.uniform(-0.03, 0.025))
            for b in rng.choice(nb, 4, replace=False)}   # 4 boulders are two slabs (bed joint, stepped)
    cen = 0.5 * (bnd[:-1] + bnd[1:])

    def part(thx):
        tt_ = np.mod(thx - bnd[0], 2 * np.pi) + bnd[0]
        b_ = np.clip(np.searchsorted(bnd, tt_) - 1, 0, nb - 1)
        return tt_, b_, (tt_ - bnd[b_]) / (bnd[b_ + 1] - bnd[b_])
    tt, bid, u = part(th)
    win = np.sin(np.pi * u) ** 0.8
    dz_th = dzb[bid] * (0.45 + 0.55 * win)
    z_sh = z_in - (r_out - 0.10 - 1.12) * np.tan(slope) + dz_th
    z_lp = z_lip + 0.6 * dz_th
    # cross-section control points (r, z) per angle, from inside the body (bottom) round the lip to the drum (top)
    rb = float(tur_r(5.84))
    ctrl = [(np.full(NT, rb - 0.06), np.full(NT, 5.84)),
            (np.full(NT, rb + 0.004), np.full(NT, 5.885)),
            (0.5 * (rb + r_out - 0.12), 0.45 * 5.885 + 0.55 * (z_lp + 0.035)),
            (r_out - 0.10, z_lp + 0.012),
            (r_out - 0.03, z_lp + 0.06),
            (r_out, z_lp + 0.22 * (z_sh - z_lp)),
            (r_out - 0.006, z_lp + 0.52 * (z_sh - z_lp)),
            (r_out - 0.03, z_lp + 0.84 * (z_sh - z_lp)),
            (r_out - 0.10, z_sh + 0.012),
            (0.5 * (r_out - 0.10) + 0.5 * 1.16, 0.5 * (z_sh + 0.012) + 0.5 * z_in - 0.004),
            (np.full(NT, 1.16), np.full(NT, z_in)),
            (np.full(NT, 1.08), np.full(NT, z_in + 0.04))]
    CR = np.stack([c[0] for c in ctrl], 1)
    CZ = np.stack([c[1] for c in ctrl], 1)
    nc_ = len(ctrl)
    tq = np.linspace(0, 1, NR)
    seg = np.clip((tq * (nc_ - 1)).astype(int), 0, nc_ - 2)
    lt = tq * (nc_ - 1) - seg

    def cr(Cx):
        p0 = Cx[:, np.clip(seg - 1, 0, nc_ - 1)]
        p1 = Cx[:, seg]
        p2 = Cx[:, seg + 1]
        p3 = Cx[:, np.clip(seg + 2, 0, nc_ - 1)]
        t = lt[None, :]
        return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    R = cr(CR)
    Z = cr(CZ)
    dR = np.gradient(R, axis=1)
    dZ = np.gradient(Z, axis=1)
    nn = np.sqrt(dR ** 2 + dZ ** 2) + 1e-9
    nr, nz = dZ / nn, -dR / nn
    vis = np.clip((tq - 0.08) / 0.1, 0, 1) * np.clip((0.92 - tq) / 0.08, 0, 1)
    # 2-D boulder map: joints meander and lean (not a pumpkin of vertical ribs); per-boulder pillow (flat middle,
    # rounded toward the joints), radial step against the neighbours, creased joints 1-2 cm deep
    TQ = np.broadcast_to(tq[None, :], (NT, NR))
    dth = 0.05 * vnoise(np.stack([np.cos(th)[:, None] * 2.2 + TQ * 2.6, np.sin(th)[:, None] * 2.2 + 0 * TQ,
                                  TQ * 1.7 + 4.4], -1)) + 0.03 * (TQ - 0.5)
    tt2, bid2, u2 = part(th[:, None] + dth)
    Rm = R
    s_arc = u2 * (bnd[bid2 + 1] - bnd[bid2]) * Rm
    s_len = (bnd[bid2 + 1] - bnd[bid2]) * Rm
    dj = np.minimum(s_arc, s_len - s_arc)
    cdep = rng.uniform(0.011, 0.02, nb)[bid2]
    crease = np.clip(1 - dj / 0.04, 0, 1) ** 1.6 * cdep
    fl = np.clip(dj / 0.16, 0, 1)
    pil = bulge[bid2] * (1 - (1 - fl) ** 2.2) * np.sin(np.pi * np.clip((TQ - 0.1) / 0.8, 0, 1)) ** 0.5
    step = drb[bid2] * np.clip(dj / 0.03, 0, 1)
    for b, (tb, inc, dru) in bedj.items():
        m = bid2 == b
        tj = tb + inc * (u2 - 0.5)
        dtb = np.abs(TQ - tj)
        crease = np.maximum(crease, np.where(m, np.clip(1 - dtb / 0.035, 0, 1) ** 1.6 * 0.016, 0.0))
        step = step + np.where(m & (TQ > tj), dru * np.clip((TQ - tj) / 0.03, 0, 1), 0.0)
    fine = 0.003 * fbm(np.stack([np.cos(th)[:, None] * 11 + 0 * R, np.sin(th)[:, None] * 11 + 0 * R, Z * 11], -1), 2)
    off = (pil + step - crease + fine) * vis[None, :]
    Rf = R + off * nr
    Zf = Z + off * nz
    X = TUR_C[0] + Rf * np.cos(th)[:, None]
    Y = TUR_C[1] + Rf * np.sin(th)[:, None]
    V = np.stack([X, Y, Zf], -1)
    bid = bid2
    # cleaved facets: flat planes cutting ~40 % of the boulders across part of their outer face
    for b in range(nb):
        if rng.uniform() > 0.42 and b != 2:
            continue
        m = (bid == b) & (np.clip(dj / 0.05, 0, 1) > 0.99)
        tc = cen[b] + rng.uniform(-0.15, 0.15) * (bnd[b + 1] - bnd[b])
        j0 = int(rng.uniform(0.38, 0.62) * NR)
        ic = int(np.argmin(np.abs(np.angle(np.exp(1j * (th - tc))))))
        p0 = V[ic, j0]
        n0 = np.array([math.cos(th[ic]) * nr[ic, j0], math.sin(th[ic]) * nr[ic, j0], nz[ic, j0]])
        tilt_ax = np.cross(n0, np.array([0, 0, 1.0]))
        tilt_ax /= np.linalg.norm(tilt_ax) + 1e-9
        a = math.radians(rng.uniform(10, 25)) * rng.choice([-1, 1])
        b2 = math.radians(rng.uniform(-15, 15))
        n1_ = n0 * math.cos(a) + np.cross(tilt_ax, n0) * math.sin(a)
        n1_ = n1_ + np.array([0, 0, 1.0]) * math.sin(b2)
        n1_ /= np.linalg.norm(n1_)
        p0 = p0 - n1_ * rng.uniform(0.01, 0.025)
        d = (V - p0) @ n1_
        cut = m & (d > 0) & (vis[None, :] > 0.5)
        V = V - np.where(cut[..., None], d[..., None] * n1_[None, None, :], 0.0)
    # quads (wrap in theta)
    i = np.arange(NT)[:, None]
    j = np.arange(NR - 1)[None, :]
    a_ = i * NR + j
    b_ = ((i + 1) % NT) * NR + j
    quads = np.stack([a_, a_ + 1, b_ + 1, b_], -1).reshape(-1, 4)
    acc.add(V.reshape(-1, 3), quads, "M_stone")
    finalize(acc, coll, smooth_deg=40.0)


def turret_cull(C, wing_margin=0.0):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    fp = (x > WX_W - W_OVH) & (x < WX_E + W_OVH) & (y > WY_S - W_OVH) & (y < WY_N + W_OVH)
    bad = fp & (z > wing_under(x, y) - 0.06) & (z < wing_under(x, y) + TH_V_MIN - 0.02)
    bad |= in_wing(C, margin=wing_margin, zpad=0.0)
    return bad


def build_turret(coll):
    rng = np.random.default_rng(1616)
    acc = Acc("KEEP_turret_stones")
    cfg = dict(seed=23, footing=0.30, ch=(0.09, 0.17), p_tall=0.07, len=(0.18, 0.52), foot_len=(0.4, 0.75),
               joint=(0.009, 0.018), front=(0.005, 0.034), foot_proj=(0.03, 0.06), bevel=(0.005, 0.03),
               pillow=(0.003, 0.012), tilt=0.008, rot=0.016, p_double=0.07, p_long=0.04, back=0.09, bed_amp=0.03)
    srange = lambda zm: [(0.0, 2 * math.pi * float(tur_r(zm)))]
    S = layout_wall(rng, srange, -0.10, TUR_Z_TOP, tooth_excl_tur, cfg)
    pins, _, _ = fill_voids(S, srange, tooth_excl_tur, -0.10, TUR_Z_TOP, rng, cfg, label="turret")
    S = cat_stones(S, pins)
    P = tur_map(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
    # stones straddling the wall faces are kept (the wall stones do the same): the junction interlocks
    S = filt(S, ~turret_cull(P, wing_margin=0.04))
    log("  turret stones", len(S["sc"]))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    low = S["zc"] < 3.6
    build_stones(acc, filt(S, ~small & low), tur_map, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009)
    build_stones(acc, filt(S, ~small & ~low), tur_map, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009, nz2=True)
    build_stones(acc, filt(S, small), tur_map, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True)
    build_tooth_stones(acc, np.random.default_rng(1819))
    finalize(acc, coll, smooth_deg=28.0)
    accm = Acc("KEEP_turret_mortar")
    zs = np.linspace(-0.1, TUR_Z_TOP + 0.02, 64)
    V, F = lathe(np.stack([tur_r(zs) - 0.004, zs], 1), 120, cx=TUR_C[0], cy=TUR_C[1], cap_bottom=False, cap_top=False)
    thv = np.arctan2(V[:, 1] - TUR_C[1], V[:, 0] - TUR_C[0])
    rv = tur_reff(thv, V[:, 2]) - 0.004
    V[:, 0] = TUR_C[0] + rv * np.cos(thv)
    V[:, 1] = TUR_C[1] + rv * np.sin(thv)
    Vg = V.reshape(len(zs), 120, 3)
    Cq = 0.25 * (Vg[:-1] + np.roll(Vg[:-1], -1, 1) + Vg[1:] + np.roll(Vg[1:], -1, 1))
    # mortar body runs on 0.18 m into the wing walls so the junction can never show through
    keep = ~turret_cull(Cq.reshape(-1, 3), wing_margin=0.18)
    accm.add(V, F[0][keep], "M_mortar")
    finalize(accm, coll)
    build_cushion(coll, rng)
    # board drum with sill & head rings
    accd = Acc("KEEP_turret_drum")
    z0, z1 = 6.60, 7.02
    th = rng.uniform(0, 0.1)
    rD = 1.15
    while th < 2 * math.pi - 0.05:
        wd = rng.uniform(0.14, 0.22)
        dth = wd / rD
        tc = th + dth / 2
        n3 = np.array([math.cos(tc), math.sin(tc), 0])
        t3 = np.array([-math.sin(tc), math.cos(tc), 0])
        o = np.array([TUR_C[0], TUR_C[1], 0]) + n3 * rD + np.array([0, 0, z0 - 0.06 + rng.uniform(-0.02, 0.01)])
        ask = rng.normal(0, 0.004)
        ex = np.array([0, 0, 1.0]) + t3 * ask
        obox(accd, o[None], ex / np.linalg.norm(ex), t3, n3, z1 - z0 + 0.08, wd - 0.012, 0.028, 0.006,
             "M_timber_weathered", nx=4, ny=4, nz=3)
        th += dth
    # sill & head rings: 8 hewn straight pieces each, butt-jointed at every facet corner, pegged
    for ri, (zz, rr_, sz) in enumerate(((z0 + 0.04, 1.08, 0.12), (z1 - 0.05, 1.08, 0.1))):
        apo_r = rr_ * math.cos(math.radians(22.5)) + 0.03
        for k in range(8):
            phi = math.radians(45 * k + 11.0 * ri)
            n3 = np.array([math.cos(phi), math.sin(phi), 0])
            t3 = np.array([-math.sin(phi), math.cos(phi), 0])
            half = apo_r * TAN22
            o = np.array([TUR_C[0], TUR_C[1], zz + rng.uniform(-0.006, 0.006)]) + n3 * apo_r - t3 * (half - 0.004)
            hewn_member(accd, o, t3, n3, np.array([0, 0, 1.0]), 2 * half + sz * 0.45, sz, sz, rng, chamfer=0.014,
                        nf=2, st_len=0.08, adze=0.003, wave=0.003, seed=300 + k + 10 * ri)
            peg(accd, o + t3 * (2 * half + sz * 0.2) + n3 * (sz / 2), n3, rad=0.01, proud=0.01)
    V = np.stack([TUR_C[0] + 1.1 * np.cos(np.linspace(0, 2 * np.pi, 24, endpoint=False)),
                  TUR_C[1] + 1.1 * np.sin(np.linspace(0, 2 * np.pi, 24, endpoint=False)), np.full(24, z1)], 1)
    accd.add(V, np.arange(24)[None, ::-1], "M_timber")
    finalize(accd, coll)
    build_cap(coll, TUR_CAP, "KEEP_turret_cap", rng, p_wall=1.17, z_plate=7.02, n_raft=4, p_top=0.12,
              expo=0.14, W=0.32, t=0.022, lens=(0.12, 0.17), bracket_z0=6.72)
    accf = Acc("KEEP_finial_turret")
    apex = float(TUR_CAP.zb(0.02))
    lead_hat(accf, TUR_C[0], TUR_C[1], apex, 0.19, 0.16)
    finial(accf, (TUR_C[0], TUR_C[1], apex + 0.03), 0.8, 1.5, (-0.3, 1.0))
    finalize(accf, coll)


# ==============================================================================================
# GROUND CONTACT: scattered rubble
# ==============================================================================================
def build_ground(coll):
    rng = np.random.default_rng(1717)
    acc = Acc("KEEP_ground_rubble")
    pts = []
    # along the hall base (outside), clustered at corners/pedestals
    for c in range(8):
        d, a = corner_dir(c)
        for _ in range(rng.integers(3, 7)):
            r = R_POST + rng.uniform(0.25, 0.75)
            aa = a + rng.normal(0, 0.06)
            pts.append((r * math.cos(aa), r * math.sin(aa)))
    for _ in range(28):
        t = rng.uniform(0, 1)
        s = t * hall_L(0)
        P = hall_map(np.array([s]), np.array([0.0]), np.array([rng.uniform(0.2, 0.7)]), np.array([0.0]))[0]
        pts.append((P[0], P[1]))
    for _ in range(26):
        s = rng.uniform(0, WING_LEN)
        P = wing_map(np.array([s]), np.array([0.0]), np.array([rng.uniform(0.15, 0.6)]), np.array([0.0]))[0]
        pts.append((P[0], P[1]))
    for _ in range(10):
        a = rng.uniform(math.pi * 0.5, math.pi * 1.5)
        r = float(tur_r(0.0)) + rng.uniform(0.15, 0.6)
        pts.append((TUR_C[0] + r * math.cos(a), TUR_C[1] + r * math.sin(a)))
    pts = np.array(pts)
    # keep clear of the door step and wing door threshold, and outside walls
    door = fmap(3, np.array([0.35]), np.array([0.0]), np.array([0.6]))[0]
    keep = np.hypot(pts[:, 0] - door[0], pts[:, 1] - door[1]) > 1.1
    keep &= np.hypot(pts[:, 0] - WDOOR["xc"], pts[:, 1] - (WY_S - 0.4)) > 0.9
    ang = np.arctan2(pts[:, 1], pts[:, 0])
    kk = np.round(ang / (np.pi / 4)) % 8
    pp = pts[:, 0] * np.cos(kk * np.pi / 4) + pts[:, 1] * np.sin(kk * np.pi / 4)
    keep &= pp > A0 + 0.08
    keep &= ~((pts[:, 0] > WX_W - 0.08) & (pts[:, 0] < WX_E + 0.08) & (pts[:, 1] > WY_S - 0.08) & (pts[:, 1] < WY_N + 0.08))
    keep &= tur_dist(pts[:, 0], pts[:, 1], np.zeros(len(pts))) > 0.08
    pts = pts[keep]
    M = len(pts)
    u = rng.uniform(0, 1, M)
    size = np.where(u < 0.6, rng.uniform(0.05, 0.12, M), np.where(u < 0.9, rng.uniform(0.12, 0.25, M), rng.uniform(0.25, 0.40, M)))
    hx = size * rng.uniform(0.8, 1.2, M) / 2
    hy = size * rng.uniform(0.6, 1.0, M) / 2
    hz = size * rng.uniform(0.35, 0.6, M) / 2
    rr = np.minimum(np.minimum(hx, hy), hz) * 0.45
    P, qd = rbox(ax4(hx, rr), ax4(hy, rr), ax4(hz, rr), rr)
    nz = fbm(P * 6.0 + np.arange(M)[:, None, None] * 3.1, 2)
    P = P * (1 + 0.18 * nz[..., None])
    yaw = rng.uniform(0, 2 * np.pi, M)[:, None]
    x, y = rot2(P[..., 0], P[..., 1], yaw)
    pitch = rng.normal(0, 0.2, M)[:, None]
    y2, z2 = rot2(y, P[..., 2], pitch)
    sink = hz * rng.uniform(0.2, 0.7, M)
    W = np.stack([x + pts[:, 0:1], y2 + pts[:, 1:2], z2 + (hz - sink * 2 + hz * 0.3)[:, None] * 0 + (hz * 0.4 - sink * 0.6)[:, None]], -1)
    acc.add(W.reshape(-1, 3), inst_faces(qd, M, P.shape[1]), "M_rubble")
    log("  rubble", M)
    finalize(acc, coll)


# ==============================================================================================
# MAIN
# ==============================================================================================
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in MAT_NAMES:
        mat = bpy.data.materials.new(m)
        mat.diffuse_color = (*MAT_COL[m], 1.0)
        MATS[m] = mat
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    root = bpy.data.collections.new("KEEP")
    scn.collection.children.link(root)
    subs = {}
    for nm in ("KEEP_hall", "KEEP_roof_skirt", "KEEP_tower", "KEEP_wing", "KEEP_turret", "KEEP_ground"):
        c = bpy.data.collections.new(nm)
        root.children.link(c)
        subs[nm] = c
    log("hall")
    build_hall_masonry(subs["KEEP_hall"])
    build_hall_mortar(subs["KEEP_hall"])
    build_hall_interior(subs["KEEP_hall"])
    build_hall_frame(subs["KEEP_hall"])
    build_main_door(subs["KEEP_hall"])
    build_window_frames(subs["KEEP_hall"])
    build_threshold(subs["KEEP_hall"])
    log("skirt")
    build_skirt(subs["KEEP_roof_skirt"])
    log("collar / cone / lantern / cap")
    build_collar(subs["KEEP_tower"])
    build_cone(subs["KEEP_tower"])
    build_lantern(subs["KEEP_tower"])
    build_main_cap_and_finial(subs["KEEP_tower"])
    log("wing")
    build_wing_walls(subs["KEEP_wing"])
    build_wing_door_window(subs["KEEP_wing"])
    build_wing_roof(subs["KEEP_wing"])
    build_wing_ridge(subs["KEEP_wing"])
    build_wing_structure(subs["KEEP_wing"])
    log("turret")
    build_turret(subs["KEEP_turret"])
    log("ground")
    build_ground(subs["KEEP_ground"])
    tot = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            tot += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    log(f"objects {len(bpy.data.objects)}  triangles {tot}")
    bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backups next to the deliverable
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    if os.path.exists(OUT + "1"):
        os.remove(OUT + "1")
    log("saved", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
