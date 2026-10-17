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
# shared 15-slot kit palette (producer note 7); only the slots a mesh uses are attached to it
MAT_NAMES = ["M_stone", "M_stone_dressed", "M_rubble", "M_mortar", "M_daub", "M_wattle", "M_timber",
             "M_timber_weathered", "M_roof_shingle", "M_roof_shake", "M_thatch", "M_iron", "M_lead", "M_earth",
             "M_moss"]
MAT_COL = {"M_stone": (0.55, 0.52, 0.47), "M_stone_dressed": (0.68, 0.66, 0.6), "M_rubble": (0.5, 0.48, 0.44),
           "M_mortar": (0.6, 0.58, 0.52), "M_daub": (0.62, 0.55, 0.45), "M_wattle": (0.4, 0.32, 0.22),
           "M_timber": (0.35, 0.25, 0.17), "M_timber_weathered": (0.45, 0.42, 0.38),
           "M_roof_shingle": (0.38, 0.36, 0.3), "M_roof_shake": (0.42, 0.37, 0.3), "M_thatch": (0.5, 0.43, 0.28),
           "M_iron": (0.12, 0.12, 0.13), "M_lead": (0.4, 0.42, 0.44), "M_earth": (0.33, 0.28, 0.2),
           "M_moss": (0.25, 0.35, 0.15)}
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
CLIP_Z = -0.05          # nothing below 5 cm under the ground (producer notes 1 / 6)
# per-object Mask defaults (producer note 9): (G wear base, G wear spread)
WEAR_BY_MAT = {"M_stone_dressed": (0.08, 0.25), "M_iron": (0.25, 0.35), "M_lead": (0.1, 0.2),
               "M_timber": (0.15, 0.4), "M_timber_weathered": (0.35, 0.45), "M_roof_shingle": (0.2, 0.5),
               "M_roof_shake": (0.25, 0.5), "M_thatch": (0.25, 0.45), "M_mortar": (0.2, 0.3)}


def _hash01(x, seed=0.0):
    x = np.asarray(x, np.float64)
    v = np.sin(x * 12.9898 + seed * 78.233 + 0.5) * 43758.5453
    return v - np.floor(v)


def island_labels(nv, edges):
    """connected components of a mesh (label = smallest vertex index of the island); numpy min-propagation
    with pointer jumping."""
    lab = np.arange(nv, dtype=np.int64)
    if len(edges) == 0:
        return lab
    a, b = edges[:, 0], edges[:, 1]
    for _ in range(400):
        m = np.minimum(lab[a], lab[b])
        new = lab.copy()
        np.minimum.at(new, a, m)
        np.minimum.at(new, b, m)
        for _ in range(6):
            new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def write_mask(me, seed=0.0, ground=True):
    """mandatory 'Mask' colour attribute (CORNER, byte): R per-piece random, G per-piece wear, B moss/damp,
    A = 1. Pieces are the mesh islands."""
    nv = len(me.vertices)
    nl = len(me.loops)
    if nv == 0 or nl == 0:
        return
    ed = np.zeros(len(me.edges) * 2, np.int32)
    me.edges.foreach_get("vertices", ed)
    lab = island_labels(nv, ed.reshape(-1, 2).astype(np.int64))
    co = np.zeros(nv * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    vn = np.zeros(nv * 3, np.float32)
    me.vertices.foreach_get("normal", vn)
    vn = vn.reshape(-1, 3)
    lv = np.zeros(nl, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    pm = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", pm)
    ls = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_total", ls)
    lmat = np.repeat(pm, ls)
    mnames = [m.name for m in me.materials]
    R = _hash01(lab, seed)
    wear_u = _hash01(lab, seed + 3.1)
    gb = np.full(nl, 0.2)
    gs = np.full(nl, 0.4)
    for i, nm in enumerate(mnames):
        b0, sp = WEAR_BY_MAT.get(nm, (0.15, 0.45))
        sel = lmat == i
        gb[sel], gs[sel] = b0, sp
    G = np.clip(gb + gs * wear_u[lv] ** 1.6, 0, 1)
    z = co[lv, 2]
    n = vn[lv]
    ground = np.clip(1.0 - z / 0.9, 0, 1) ** 1.3 * (1.0 if ground else 0.0)
    upf = np.clip((n[:, 2] - 0.35) / 0.65, 0, 1) * (0.45 + 0.35 * np.clip(1 - z / 14.0, 0, 1))
    north = np.clip(n[:, 1], 0, 1) * 0.3 * np.clip(1 - z / 8.0, 0, 1)
    B = np.clip(np.maximum(ground, upf) + north + 0.08 * (_hash01(lab, seed + 7.7)[lv] - 0.5), 0, 1)
    col = np.stack([R[lv], G, B, np.ones(nl)], 1).astype(np.float32)
    at = me.color_attributes.new("Mask", "BYTE_COLOR", "CORNER")
    at.data.foreach_set("color_srgb", col.ravel())
    me.color_attributes.active_color_name = "Mask"
    me.color_attributes.default_color_name = "Mask"


def _needle_tris(bm, h_min):
    """faces (as BMFace) whose triangulation holds a triangle with altitude < h_min (needle / sliver)."""
    bm.verts.index_update()
    tris = bm.calc_loop_triangles()
    if not tris:
        return [], tris, np.zeros(0, bool)
    co = np.array([v.co[:] for v in bm.verts])
    I = np.array([[l.vert.index for l in t] for t in tris])
    A, B, C = co[I[:, 0]], co[I[:, 1]], co[I[:, 2]]
    ar2 = np.linalg.norm(np.cross(B - A, C - A), axis=1)
    L = np.max(np.stack([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1),
                         np.linalg.norm(A - C, axis=1)]), axis=0)
    bad = ar2 / np.maximum(L, 1e-12) < h_min
    return list({tris[i][0].face for i in np.flatnonzero(bad)}), tris, bad


def fix_needles(bm, h_min=1e-4, iters=5):
    """Nanite hygiene (round 6): no needle triangles. Bad n-gons are re-triangulated (beauty); remaining slivers
    lose their short edge (< 1 mm, collapsed) or get their long edge flipped against the neighbour; whatever is
    still a sliver after that is deleted (it is < 0.1 mm wide)."""
    for it in range(iters):
        bad_f, tris, bad = _needle_tris(bm, h_min)
        if not bad_f:
            return
        ngon = [f for f in bad_f if len(f.verts) > 3]
        if ngon:
            bmesh.ops.triangulate(bm, faces=ngon, quad_method="BEAUTY", ngon_method="BEAUTY")
            bad_f, tris, bad = _needle_tris(bm, h_min)
            if not bad_f:
                return
        if it == iters - 1:
            bmesh.ops.delete(bm, geom=[f for f in bad_f if f.is_valid], context="FACES")
            return
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


def clean_mesh(me, clip_z=CLIP_Z, recalc=True):
    """hygiene: clip at -5 cm, merge by distance (0.1 mm), dissolve degenerates, delete remaining zero-area faces."""
    bm = bmesh.new()
    bm.from_mesh(me)
    if clip_z is not None:
        low = [v for v in bm.verts if v.co.z < clip_z]
        for v in low:
            v.co.z = clip_z
        flat = [f for f in bm.faces if all(v.co.z <= clip_z + 1e-6 for v in f.verts)]
        if flat:
            bmesh.ops.delete(bm, geom=flat, context="FACES")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    fix_needles(bm)
    zero = [f for f in bm.faces if f.calc_area() < 5e-8]
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
    # triangulation still holds a needle, then fix again
    for _ in range(2):
        bad_p = mesh_needle_polys(me)
        if not len(bad_p):
            break
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        bmesh.ops.triangulate(bm, faces=[bm.faces[int(i)] for i in bad_p], quad_method="BEAUTY",
                              ngon_method="BEAUTY")
        fix_needles(bm)
        bm.to_mesh(me)
        bm.free()
        me.update()


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


def build_mesh(acc, smooth_deg=38.0, recalc=True, clip_z=CLIP_Z, mask_seed=None, mask_ground=True):
    """Acc -> cleaned bpy mesh with UVs, palette slots and the Mask attribute (no object)."""
    if acc.n == 0 or not acc.F:
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
    # UVs: explicit per-vertex UVs where given (grain aligned), otherwise box projection; set before the cleanup
    # so the loops carry them through it
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
    clean_mesh(me, clip_z=clip_z, recalc=recalc)
    me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    me.set_sharp_from_angle(angle=math.radians(smooth_deg))
    write_mask(me, seed=(sum(map(ord, acc.name)) % 997) * 0.37 if mask_seed is None else mask_seed,
               ground=mask_ground)
    return me


def finalize(acc, coll, smooth_deg=38.0, recalc=True, clip_z=CLIP_Z):
    me = build_mesh(acc, smooth_deg, recalc, clip_z)
    if me is None:
        log("  (empty)", acc.name)
        return None
    ob = bpy.data.objects.new(acc.name, me)
    coll.objects.link(ob)
    log(f"  {acc.name}: {len(me.vertices)} v, {sum(len(p.vertices) - 2 for p in me.polygons)} tris")
    return ob


# ----------------------------------------------------------------------------------------------
# shared-mesh pools (producer notes 2 / 3): small variant pools placed as linked duplicates
# ----------------------------------------------------------------------------------------------
POOL_MESHES = {}         # key -> list of bpy meshes (variants)
PLACEMENTS = []          # (pool key, variant index, 4x4 matrix, object name stem)


def frame_matrix(origin, ex, ey, ez):
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ex, ey, ez, origin
    return M


def axis_matrix(p, axis, roll=0.0):
    """local +Z -> axis at p (orthonormal frame, optional roll about the axis)."""
    z = np.asarray(axis, float)
    z = z / np.linalg.norm(z)
    up = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    c, s = math.cos(roll), math.sin(roll)
    x, y = x * c + y * s, -x * s + y * c
    return frame_matrix(np.asarray(p, float), x, y, z)


def get_pool(key, builder, n_var):
    """build (once) n_var variant meshes with builder(acc, variant_index) -> list of meshes."""
    if key not in POOL_MESHES:
        meshes = []
        for i in range(n_var):
            acc = Acc(f"KEEP_pool_{key}_v{i:02d}")
            builder(acc, i)
            meshes.append(build_mesh(acc, smooth_deg=40.0, clip_z=None, mask_seed=7.3 * i + len(key),
                                     mask_ground=False))
        POOL_MESHES[key] = meshes
    return POOL_MESHES[key]


def place(key, var, M, stem):
    PLACEMENTS.append((key, int(var), np.asarray(M, float), stem))


def realize_placements(coll):
    """one object per placement, every object of a variant sharing that variant's mesh data."""
    from mathutils import Matrix
    counts = {}
    for key, var, M, stem in PLACEMENTS:
        meshes = POOL_MESHES[key]
        me = meshes[var % len(meshes)]
        counts[stem] = counts.get(stem, 0) + 1
        ob = bpy.data.objects.new(f"{stem}_{counts[stem]:03d}", me)
        ob.matrix_world = Matrix([list(r) for r in M])
        coll.objects.link(ob)
    log(f"  placements: {len(PLACEMENTS)} linked duplicates of {sum(len(v) for v in POOL_MESHES.values())} "
        f"pooled meshes ({', '.join(f'{k}:{v}' for k, v in counts.items())})")


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
                 dressed=False, wear=None, front_min=0.003, nz2=False, side_depth=None):
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
    if side_depth is not None:
        # sides only reach side_depth behind the wall plane (1-2 cm into the mortar body); no back, no buried sides
        back = np.minimum(back, side_depth)
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
        # flat-tooled face: dome <= 4 mm (fine tooling undulation + a shallow punched field inside the margin)
        und = 0.0012 * fbm(np.stack([x * 7.0, y * 7.0, sid], -1), 2)
        pick = np.abs(fbm(np.stack([x * 38.0, y * 38.0, sid * 3.1], -1), 2))
        dm = np.minimum(HX - np.abs(x0_), HY - np.abs(y0_))
        marg = np.asarray(S.get("margin", np.full(M, 0.025)), float)[:, None]
        # (round 5) no stepped drafted margin: it shaded as a 2-3 cm round-over / seam line; the face is one flat
        # tooled plane with a sub-mm pick texture that fades out 1.5 cm before the arris
        inner = np.clip((dm - 0.015) / 0.03, 0, 1)
        relief = relief + und + inner * (0.0004 * pick)
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
    nch = rng.integers(0, 3, M) if dressed else rng.integers(2, 5, M)
    chips = np.zeros_like(x)
    cp = rng.uniform(0, 1, (M, 4, 4))
    for i in range(4):
        act = (i < nch)[:, None]
        t = cp[:, i, 0:1] * 4.0
        side = np.floor(t).astype(int)
        fr = t - side
        if dressed:
            fr = np.where(fr < 0.5, 0.0, 1.0)          # dressed work: chips only at the corners
        ex = np.where(side == 0, -1 + 2 * fr, np.where(side == 1, 1.0, np.where(side == 2, 1 - 2 * fr, -1.0)))
        ey = np.where(side == 0, -1.0, np.where(side == 1, -1 + 2 * fr, np.where(side == 2, 1.0, 1 - 2 * fr)))
        px, py = ex * HX, ey * HY
        rad = (0.015 + 0.015 * cp[:, i, 1:2]) if dressed else (0.01 + 0.02 * cp[:, i, 1:2])
        if wear is not None:
            rad = rad * (1 + 0.6 * np.asarray(wear, float)[:, None])
        dep = rad * ((0.3 + 0.2 * cp[:, i, 2:3]) if dressed else (0.35 + 0.35 * cp[:, i, 2:3]))
        d = np.sqrt((x0_ - px) ** 2 + (y0_ - py) ** 2)
        chips = np.minimum(chips, -np.where(act, dep * np.clip(1 - d / rad, 0, 1) ** 1.3, 0.0))
    dz = relief + nzv + facets + chips
    zf = z + fw * dz
    # never let the face sink behind the mortar body
    zf = np.where(fw > 0.3, np.maximum(zf, front_min - (1 - fw) * 0.01), zf)
    # chips also nibble the outline a little (broken arris)
    pull = np.clip(-chips, 0, 0.03) * (0.5 if dressed else 0.5) * fw
    x = x - np.sign(x0_) * pull * (np.abs(ux) > 0.6)
    y = y - np.sign(y0_) * pull * (np.abs(uy) > 0.6)
    z = zf
    if wear is not None:
        # worn stones: arrises and face rounded off further (lower jamb blocks, threshold)
        wv = np.asarray(wear, float)[:, None]
        rim = np.clip(np.maximum(np.abs(ux), np.abs(uy)) - 0.75, 0, 1) * 4
        z = z - fw * wv * 0.0015 * rim ** 2
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
    st = {k: [] for k in ("sc", "zc", "hx", "hy", "f", "back", "r", "rot", "zcrs", "pillow", "tiltx", "tilty", "foot")}
    seed = cfg.get("seed", 1)
    foot_lvl = cfg.get("foot_lvl")          # footing tops step +-8 cm stone by stone (not a kerb line)
    foot_steps = []
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
        if foot_lvl is not None and len(bounds) == 2:
            h = max(h, 0.18)                 # the course over a stepped footing must swallow the steps
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

    def foot_top(ss):
        v = np.full(len(ss), bounds[1])
        for a_, b_, zt_ in foot_steps:
            v = np.where((ss >= a_ - 0.02) & (ss <= b_ + 0.02), np.maximum(v, zt_), v)
        return v

    def push(sc, zc, hx, hy, fr, r, zm, shl, shr, kb, kt, tilt_back=None, foot=0.0):
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
        st["sbb"].append(bed_slope(kb, sc) if 0 < kb < nb - 1 and not (kb == 1 and foot_lvl) else 0.0)
        st["sbt"].append(bed_slope(kt, sc) if 0 < kt < nb - 1 and not (kt == 1 and foot_lvl) else 0.0)
        st["foot"].append(foot)

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
                if footing and foot_lvl is not None:
                    zt = bounds[1] + rng.uniform(*foot_lvl)
                    foot_steps.append((s0, s1, zt))
                if k == 1 and foot_steps:
                    zb = max(zb, float(foot_top(np.linspace(s0, s1, 9)).max()))
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
                     k, k + 2 if dbl else k + 1, foot=1.0 if footing else 0.0)
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


def rough_footing(S, rng):
    """footing stones read as split field stone, not kerbs: tops slope 3-8 deg (the course above is pinned onto
    them), 1-2 cm pillow, two split planes, heavy chipped arrises (flag 'footx' read by build_poly_stones)."""
    M = len(S["sc"])
    for k in ("sbt", "footx"):
        if k not in S:
            S[k] = np.zeros(M)
    for i in np.flatnonzero(S["foot"] > 0.5):
        hx = float(S["hx"][i])
        t = math.tan(math.radians(rng.uniform(3.0, 8.0))) * rng.choice([-1, 1])
        D = abs(t) * hx
        S["sbt"][i] += t
        S["hy"][i] -= D / 2
        S["zc"][i] -= D / 2
        S["pillow"][i] = rng.uniform(0.08, 0.11)
        S["spl"][i] = 2
        # knock off 1-2 top corners (the field stone outline, not a sawn block)
        if all(S[f"cq{q}"][i] < 0.004 for q in range(4)) and "cq0" in S:
            for q in rng.choice([2, 3], 1 + int(rng.uniform() < 0.5), replace=False):
                S[f"cq{q}"][i] = min(rng.uniform(0.05, 0.12), 0.6 * float(S["hy"][i]), 0.4 * hx)
                S[f"ca{q}"][i] = rng.uniform(0.6, 1.6)
        S["footx"][i] = 1.0
        S["tiltx"][i] = rng.normal(0, 0.010)
        # round 6: the face leans back 1.5-3.5 cm toward the top (a field stone bedded on its broad side, not a
        # plumb kerb face); the foot bulges out to the ground
        S["tilty"][i] = -rng.uniform(0.015, 0.035)
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


def build_poly_stones(acc, S, mapfn, mat, rng, rough=1.0, spacing=0.05, rings=(0.62, 0.3), noise_amp=0.006,
                      front_min=0.003, side_depth=None):
    """Hero rubble: every stone built from its true (polygonal) outline with a rounded front arris, a split / cleaved
    face (1-2 large planes at 5-15 deg), chisel facets, chipped arrises and a low pillow. Rings: outline at the back,
    arris start, arris middle, face edge, then rings scaled toward the centroid and a centre fan."""
    M = len(S["sc"])
    for i in range(M):
        poly = stone_outline(S, i)
        hx, hy = float(S["hx"][i]), float(S["hy"][i])
        fx = _g(S, "footx", i) > 0.5
        r = float(min(S["r"][i], 0.3 * min(hx, hy), 0.02))
        r = max(r, 0.004)
        if fx:
            r = float(min(0.035, 0.3 * min(hx, hy)))      # weathered field-stone shoulder, not a sawn arris
        f = float(S["f"][i])
        back = float(S["back"][i]) if side_depth is None else min(float(S["back"][i]), side_depth)
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
            if _g(S, "footx", i) > 0.5:
                ang = rng.uniform(13.0, 22.0)
            planes.append((dvec, c0, math.tan(math.radians(ang))))
        maxdep = sum(t * max(0.0, np.abs(poly @ d).max() - c) for d, c, t in planes)
        if fx and maxdep > 1.0 * f + 0.045:
            # footing: keep every split plane inside the projection (never flattened back onto front_min)
            sc_ = (1.0 * f + 0.045) / maxdep
            planes = [(d, c, t * sc_) for d, c, t in planes]
            maxdep *= sc_
        f_eff = f + (min(0.5 * maxdep, 0.05) if fx else min(0.55 * maxdep, 0.03))
        Q, N = rounded_outline(poly, rc=max(r * 1.08, 0.006), spacing=spacing)
        nq = len(Q)
        cen = Q.mean(0)
        R0 = Q
        R1 = Q
        R2 = Q + N * (0.29 * r)
        R3 = Q + N * r
        rings_i = (0.86, 0.7, 0.54, 0.38, 0.22) if fx else rings
        inner = [cen + (R3 - cen) * sc_ for sc_ in rings_i]
        ring_xy = [R0, R1, R3] + inner + [cen[None, :]]
        rho = [1.0, 1.0, 1.0] + list(rings_i) + [0.0]

        def relief(xy, rh):
            x, y = xy[:, 0], xy[:, 1]
            ux_ = np.clip((x - cen[0]) / max(hx, 1e-3), -1, 1)
            uy_ = np.clip((y - cen[1]) / max(hy, 1e-3), -1, 1)
            pil = _g(S, "pillow", i, 0.004) * 0.25 * (1 - ux_ ** 2) * (1 - uy_ ** 2)
            tilt = _g(S, "tiltx", i) * x / max(hx, 1e-3) + _g(S, "tilty", i) * y / max(hy, 1e-3)
            # low-frequency face undulation only: the coarse ring topology must not show 'spokes'
            nz = fbm(np.stack([x * 7.0 + sd, y * 7.0, np.full(len(x), sd * 0.37)], -1), 2)
            lump = 0.0
            if fx:
                # footing: broad +-1.5-2 cm lumps and hollows (weathered field stone, absolute amplitude)
                lump = 0.03 * fbm(np.stack([x * 5.0 + sd * 1.7, y * 5.0, np.full(len(x), sd * 0.11)], -1), 2)
            fac = np.zeros(len(x))
            for dvec, c0, tn in planes:
                fac -= tn * np.maximum(xy @ dvec - c0, 0.0)
            # two small chisel facets near the edge
            return pil + tilt + noise_amp * rough * nz + fac + lump
        # chisel facets & chips (shared between rings via position)
        chis = [(np.array([math.cos(a_), math.sin(a_)]), rng.uniform(0.55, 0.85), rng.uniform(0.004, 0.012))
                for a_ in rng.uniform(0, 2 * np.pi, 2)]
        nch = int(rng.integers(2, 5)) if not fx else int(rng.integers(4, 8))
        chip_pts = Q[rng.integers(0, nq, nch)]
        chip_rad = rng.uniform(0.012, 0.03, nch) if not fx else rng.uniform(0.03, 0.06, nch)

        def extra(xy):
            e = np.zeros(len(xy))
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
TUR_SCALE = 1.0                  # plan scale of the turret (body profile, cushion, drum, cap) -- kit parameter
TUR_Z_TOP = 5.92                 # top of the stone body (cushion sits on it)
# concave stone cone (ref1, Director's round-3 profile): flank leans ~24 deg where it leaves the wing eave, easing
# to ~8 deg under the cushion; below the eave a D4.7 base bulging out of the wing's N and W walls
_TPZ = np.array([-0.3, 0.0, 1.3, 2.6, 3.5, 4.5, 5.4, 5.9, 6.1])
_TPR = np.array([2.385, 2.38, 2.365, 2.35, 1.95, 1.55, 1.32, 1.25, 1.24])


def _tur_table():
    zf = np.linspace(_TPZ[0], _TPZ[-1], 641)
    rf = np.interp(zf, _TPZ, _TPR * TUR_SCALE)
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


HIP_RC = 0.55          # plan radius of the rounded thatch hips (every contour of the roof keeps this corner radius)


def q_rr(x, y, rc=HIP_RC):
    """inward horizontal inset of plan points from the wing's eave outline (W, S, N eaves; the E end dies into the
    hall), measured to the family of rounded-rectangle contours that all keep corner radius rc: the hipped thatch
    surface z = 2.40 + q * tan(pitch) is rounded over the hips at every height (no crease, no hip-roll tube)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    dW = x - (WX_W - W_OVH)
    dS = y - (WY_S - W_OVH)
    dN = (WY_N + W_OVH) - y
    q = np.minimum(np.minimum(dW, dS), dN)
    for d2 in (dS, dN):
        a, b = dW - rc, d2 - rc
        dc = 0.5 * ((a + b) + np.sqrt(np.maximum(2 * rc * rc - (a - b) ** 2, 0.0)))
        q = np.where(np.abs(a - b) < rc, np.minimum(q, dc), q)
    return q


def wing_under(x, y):
    """underside of the wing thatch (rounded-hip deck)."""
    return 2.40 + W_TAN * q_rr(x, y)


def thatch_low(x, y):
    """lowest course surface of the (swelling) thatch above plan point (x, y)."""
    return wing_under(x, y) + TH_V_MIN + thatch_swell(x, y) / math.cos(W_PITCH)


def wing_top(x, y):
    return wing_under(x, y) + TH_V + thatch_swell(x, y) / math.cos(W_PITCH)


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


def _post_corners():
    out = []
    for c in range(8):
        d = np.array([math.cos(FPHI[c] + math.radians(22.5)), math.sin(FPHI[c] + math.radians(22.5))])
        P0 = np.array([d[0] * 4.30, d[1] * 4.30, 1.5])
        if not in_wing(P0, margin=-0.3, zpad=0.0):
            out.append(c)
    return out


def hall_excl(z0, z1, zm):
    out = []
    # no rubble behind the engaged corner posts (and their pedestals): those faces can never be seen
    for c in _post_corners():
        sc_ = (c + 0.5) / 8.0 * float(hall_L(zm))
        hw_ = 0.13 if z0 > 0.38 else 0.21
        if z1 > 0.0:
            out.append((sc_ - hw_, sc_ + hw_))
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
    jwd = {}
    for side in (-1, 1):
        for i in range(5):
            long_ = (i % 2 == 0) == (side < 0)
            wd = (0.39 if long_ else 0.27) + rng.uniform(-0.03, 0.03)
            jwd[(side, i)] = wd
            z0_, z1_ = zz[i] + 0.006, zz[i + 1] - 0.006
            x_in = xc + side * hw
            x_out = x_in + side * wd
            xa, xb = min(x_in, x_out), max(x_in, x_out)
            zc = 0.5 * (z0_ + z1_)
            back = float(face_apo(k, x_in, zc)) - leaf_apo - 0.012
            recs.append(dict(x=0.5 * (xa + xb), zc=zc, hx=0.5 * (xb - xa) - 0.006, hy=0.5 * (z1_ - z0_),
                             f=0.05 + rng.uniform(0, 0.012), back=back))
            DRESSED_POLYS[k].append([(xa, z0_), (xb, z0_), (xb, z1_), (xa, z1_)])
    # recessed lime mortar in the jamb bed joints (1.2 cm back from the face and from the reveal)
    for side in (-1, 1):
        for i in range(1, 5):
            zj = zz[i]
            x_in = xc + side * hw
            wj = min(jwd[(side, i - 1)], jwd[(side, i)]) - 0.012
            xa, xb = sorted([x_in + side * 0.03, x_in + side * wj])
            wf_ = float(face_apo(k, x_in, zj)) - A_REF + 0.05 - 0.015 - 0.016
            facet_obox(JOINT_ACC, k, xa, xb, zj - 0.0095, zj + 0.0095, leaf_apo - A_REF, wf_, 0.003, "M_mortar",
                       nx=4, ny=3, nz=3)
    S = stone_rec([facet_s(k, r["x"], r["zc"]) for r in recs], [r["zc"] for r in recs],
                  [r["hx"] for r in recs], [r["hy"] for r in recs], [r["f"] for r in recs],
                  [r["back"] for r in recs], rng.uniform(0.010, 0.015, len(recs)),
                  [r["zc"] for r in recs], rng)
    dress_irregular(S, rng)
    wear = np.clip(1.1 - S["zc"] / 0.9, 0, 1)
    build_stones(acc_d, S, hall_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(30, 32), wear=wear)
    # voussoirs: irregular widths, thicker at the crown
    nv = 13
    wts = rng.permutation(np.linspace(0.78, 1.24, nv))
    wts[nv // 2] = max(wts[nv // 2], 1.0) * 1.12
    th = math.pi - np.concatenate([[0], np.cumsum(wts) / wts.sum() * math.pi])
    vs = []
    for i in range(nv):
        ta, tb = th[i], th[i + 1]
        tm = 0.5 * (ta + tb)
        rin = hw
        rout = hw + 0.31 + 0.05 * math.sin(tm) + rng.uniform(-0.03, 0.045) + (0.03 if i == nv // 2 else 0)
        rm = 0.5 * (rin + rout)
        hx = 0.5 * (ta - tb) * rm - 0.007
        zc_abs = zs + rm * math.sin(tm)
        xm = xc + rm * math.cos(tm)
        back = float(face_apo(k, xm, zc_abs)) - leaf_apo - 0.012
        vs.append((tm, rm, hx, 0.5 * (rout - rin) - 0.004, back, zc_abs, 0.055 + rng.uniform(0, 0.012) + (0.012 if i == nv // 2 else 0)))
        poly = [(xc + rin * math.cos(a), zs + rin * math.sin(a)) for a in np.linspace(tb, ta, 5)] + \
               [(xc + rout * math.cos(a), zs + rout * math.sin(a)) for a in np.linspace(ta, tb, 5)]
        DRESSED_POLYS[k].append(poly)
    # radial joints between voussoirs: mortar wedges recessed 1.2 cm from the face and the intrados
    for i in range(1, nv):
        tj = th[i]
        r0_ = hw + 0.03
        r1_ = min(vs[i - 1][1] + vs[i - 1][3], vs[i][1] + vs[i][3]) - 0.02
        cs, sn = math.cos(tj), math.sin(tj)
        tx, tz = -sn, cs
        wf_ = float(face_apo(k, xc + 0.5 * (r0_ + r1_) * cs, zs + 0.5 * (r0_ + r1_) * sn)) - A_REF + 0.055 - 0.031
        P8 = []
        for rr_ in (r0_, r1_):
            for dd_ in (-0.0095, 0.0095):
                for ww_ in (leaf_apo - A_REF, wf_):
                    P8.append((xc + rr_ * cs + dd_ * tx, zs + rr_ * sn + dd_ * tz, ww_))
        P8 = np.array(P8)
        Wp = fmap(k, P8[:, 0], P8[:, 1], P8[:, 2])
        quads = np.array([(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        JOINT_ACC.add(Wp, quads, "M_mortar")
    vs = np.array(vs)
    S = stone_rec(np.zeros(nv), vs[:, 5], vs[:, 2], vs[:, 3], vs[:, 6], vs[:, 4],
                  rng.uniform(0.010, 0.015, nv), vs[:, 5], rng)
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
                  rng.uniform(0.010, 0.015, len(R)), R[:, 1], rng)
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


JOINT_ACC = None


def build_hall_masonry(coll):
    global JOINT_ACC
    rng = np.random.default_rng(101)
    acc = Acc("KEEP_hall_wall_stones")
    accd = Acc("KEEP_hall_dressed_stones")
    JOINT_ACC = Acc("KEEP_hall_dressed_joint_mortar")
    for op in OPENINGS:
        if op["kind"] == "arch":
            build_door_dressing(accd, op, rng)
        else:
            build_rect_dressing(accd, op, rng, accd)
    cfg = dict(seed=7, footing=0.33, ch=(0.085, 0.18), p_tall=0.08, len=(0.18, 0.62), foot_len=(0.40, 1.10),
               foot_lvl=(-0.10, 0.10), joint=(0.008, 0.017), front=(0.005, 0.032), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
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
    S = polygonize(S, (hero0 & (S["zc"] > 0.3)) | (S["foot"] > 0.5), np.random.default_rng(1919))
    S = rough_footing(S, np.random.default_rng(1920))
    pins, _, _ = fill_voids(S, srange, hall_excl, -0.10, WALL_H, rng, cfg, label="hall")
    S = cat_stones(S, pins)
    S = filt(S, hall_cull(S))
    log("  hall stones:", len(S["sc"]))
    # hero zone (SW, S door, SE facets): true polygonal outlines, split planes, chisel facets, chipped arrises
    hero, fac = hero_of(S)
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    foot = S["foot"] > 0.5
    poly_n = (hero | foot) & ~small
    hero = hero | foot
    npoly = int(sum(1 for i in np.flatnonzero(poly_n) if len(stone_outline(S, i)) != 4 or
                    abs(S["sbt"][i] - S["sbb"][i]) > 0.06 or abs(S["shl"][i] - S["shr"][i]) > 0.12))
    log(f"  hall hero stones {int(poly_n.sum())} (non-rectangular {npoly}), other {int((~hero & ~small).sum())}, "
        f"pins {int(small.sum())}")
    build_poly_stones(acc, filt(S, poly_n), hall_map, "M_stone", np.random.default_rng(2020), side_depth=0.018,
                      rings=(0.8, 0.58, 0.33))
    # non-hero facets: N / NE / E / NW thinned (single side segment + chamfer band)
    build_stones(acc, filt(S, ~hero & ~small), hall_map, "M_stone", rng, rough=1.0, nxy=5, noise_amp=0.008, nz2=True,
                 side_depth=0.018)
    build_stones(acc, filt(S, small & hero), hall_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005, side_depth=0.018)
    build_stones(acc, filt(S, small & ~hero), hall_map, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=0.018)
    finalize(acc, coll, smooth_deg=28.0)
    finalize(accd, coll, smooth_deg=24.0)          # crisp 1-1.5 cm arrises (no soft shading across the bevel)
    finalize(JOINT_ACC, coll)
    return S


def mortar_sheet(acc, mapfn, s_edges, z_edges, near_fn, keep_fn, sub=5, w0=-0.004, w_amp=0.003, seed=0.0):
    """recessed mortar body as a coarse cell sheet behind the stones (cells subdivided sub x sub only where
    near_fn says so: openings, junctions); keep_fn(s, z) culls cells (openings, buried zones). Duplicate
    corner vertices are welded in finalize."""
    s_edges = np.asarray(s_edges, float)
    z_edges = np.asarray(z_edges, float)
    SA, ZA = np.meshgrid(s_edges[:-1], z_edges[:-1], indexing="ij")
    SB, ZB = np.meshgrid(s_edges[1:], z_edges[1:], indexing="ij")
    SA, ZA, SB, ZB = SA.ravel(), ZA.ravel(), SB.ravel(), ZB.ravel()
    nr = near_fn(0.5 * (SA + SB), 0.5 * (ZA + ZB), SB - SA, ZB - ZA)
    cells = [np.stack([SA[~nr], ZA[~nr], SB[~nr], ZB[~nr]], 1)]
    if nr.any():
        f = (np.arange(sub) / sub)
        sa, za, sb, zb = SA[nr], ZA[nr], SB[nr], ZB[nr]
        ds, dz = (sb - sa) / sub, (zb - za) / sub
        for i in range(sub):
            for j in range(sub):
                cells.append(np.stack([sa + ds * i, za + dz * j, sa + ds * (i + 1), za + dz * (j + 1)], 1))
    C = np.concatenate(cells)
    keep = keep_fn(0.5 * (C[:, 0] + C[:, 2]), 0.5 * (C[:, 1] + C[:, 3]))
    C = C[keep]
    S4 = np.stack([C[:, 0], C[:, 2], C[:, 2], C[:, 0]], 1).ravel()
    Z4 = np.stack([C[:, 1], C[:, 1], C[:, 3], C[:, 3]], 1).ravel()
    W4 = w0 + w_amp * vnoise(np.stack([S4 * 2.1, Z4 * 2.1, np.full(len(S4), seed)], -1))
    V = mapfn(S4, Z4, W4)
    q = np.arange(len(C) * 4).reshape(-1, 4)
    # wind every cell outward (toward +w) so the sheet never shows its back through a joint
    O = mapfn(S4, Z4, W4 + 0.01) - V
    n_ = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 3]] - V[q[:, 0]])
    flip = (n_ * O[q[:, 0]]).sum(1) < 0
    q[flip] = q[flip][:, ::-1]
    acc.add(V, q, "M_mortar")
    return len(C)


def build_hall_mortar(coll):
    acc = Acc("KEEP_hall_wall_mortar")
    # t = perimeter fraction; corner arcs of the rounded octagon are kept as knots
    tt = np.unique(np.round(np.concatenate([np.linspace(0, 1, 89), OT[(OB == 0)]]), 6))
    zs = np.concatenate([np.linspace(-0.05, WALL_H, 13)])

    def near(t, z, dt, dz):
        nr = np.zeros(len(t), bool)
        for op in OPENINGS:
            xl = (t - op["k"] / 8.0) * hall_L(z)
            ext = op["hw"] + 0.55
            ztop = op.get("z1", op.get("zs", 2.0) + op["hw"]) + 0.6
            nr |= (np.abs(xl - op["xc"]) < ext) & (z > op["z0"] - 0.6) & (z < ztop)
        return nr

    def keep(t, z):
        k = np.ones(len(t), bool)
        for op in OPENINGS:
            xl = (t - op["k"] / 8.0) * hall_L(z)
            k &= ~open_contains(op, xl, z, m=0.03)
        Pc = hall_map(t * hall_L(z), z, np.zeros(len(t)), z)
        k &= ~in_wing(Pc, margin=0.12, zpad=0.15)
        return k
    n = mortar_sheet(acc, lambda t, z, w: hall_map(t * hall_L(z), z, w, z), tt, zs, near, keep, sub=4, seed=1.0)
    log(f"  hall mortar cells {n}")
    finalize(acc, coll, recalc=False)


def build_hall_interior(coll):
    """reveal tubes through the wall at every opening plus, behind each window, a simple dark blocker room
    (floor, ceiling, side and back walls ~1.5 m deep): only the depth visible through the openings is modelled."""
    acc = Acc("KEEP_hall_interior")

    def add_facing(V, F, mat, R):
        """add faces wound toward the viewer point R (in front of the opening): Unreal culls back faces."""
        out = []
        for f_ in F:
            f_ = np.array(f_)
            nrm = np.cross(V[f_[:, 1]] - V[f_[:, 0]], V[f_[:, 2]] - V[f_[:, 0]])
            flip = (nrm * (R - V[f_].mean(1))).sum(1) < 0
            f_[flip] = f_[flip][:, ::-1]
            out.append(f_)
        acc.add(V, out, mat)
    for op in OPENINGS:
        k = op["k"]
        zc_ = op.get("z1", op.get("zs", 1.5) + op["hw"])
        R_ = fmap(k, np.array([op["xc"]]), np.array([0.5 * (op["z0"] + zc_)]), np.array([0.6]))[0]
        o1 = open_outline(op, grow=0.05)
        o2 = open_outline(op, grow=0.20)
        if op["kind"] == "arch":
            o1[:2, 1] = np.maximum(o1[:2, 1], 0.0)
            o2[:2, 1] = np.maximum(o2[:2, 1], 0.0)
        n = len(o1)
        r1 = fmap(k, o1[:, 0], o1[:, 1], np.full(n, -op["depth"] + 0.005))
        r2 = fmap(k, o2[:, 0], o2[:, 1], np.zeros(n), a_ref=INNER_APO)
        V = np.concatenate([r1, r2])
        q = np.array([(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)])
        add_facing(V, [q], "M_mortar", R_)
        if op["kind"] == "arch":
            continue            # the door leaf is closed: nothing behind it can be seen
        # blocker room behind the window
        xa, xb = op["xc"] - op["hw"] - 0.9, op["xc"] + op["hw"] + 0.9
        z0, z1 = 0.12, WALL_H
        a_in, a_bk = INNER_APO + 0.02, INNER_APO - 1.5
        X = np.array([xa, xb, xb, xa, xa, xb, xb, xa])
        Z = np.array([z0, z0, z1, z1, z0, z0, z1, z1])
        Wv = np.array([0, 0, 0, 0, 1, 1, 1, 1], float)
        P = np.stack([X, Z, Wv], 1)
        V = np.concatenate([fmap(k, P[:4, 0], P[:4, 1], np.zeros(4), a_ref=a_in),
                            fmap(k, P[4:, 0], P[4:, 1], np.zeros(4), a_ref=a_bk)])
        # faces seen from the window: back wall, floor, ceiling, two sides
        add_facing(V, [np.array([[4, 5, 6, 7]]), np.array([[3, 2, 6, 7]]), np.array([[0, 3, 7, 4]]),
                    np.array([[1, 5, 6, 2]])], "M_mortar", R_)
        add_facing(V, [np.array([[0, 1, 5, 4]])], "M_stone", R_)
    finalize(acc, coll, recalc=False)


# ==============================================================================================
# GENERIC ORIENTED BOXES (timber members, boards)
# ==============================================================================================
def obox(acc, O, EX, EY, EZ, LX, LY, LZ, r, mat, nx=4, ny=4, nz=4, deform=None, grain_uv=True, skip_back=False,
         skip_front=False):
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
    P, quads = rbox(X, Y, Z, r, skip_back=skip_back, skip_front=skip_front)
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
                checks=(), end_bevel=True, seed=0, drop=()):
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


def _peg_builder(rad, proud, embed):
    def build(acc, i):
        rr = np.random.default_rng(4000 + i)
        n = 8
        a = np.linspace(0, 2 * np.pi, n, endpoint=False) + rr.uniform(0, 0.4)
        wob = 1 + rr.uniform(-0.08, 0.08, n)                       # hand-riven, slightly out of round
        ring = lambda r_, z_: np.stack([r_ * wob * np.cos(a), r_ * wob * np.sin(a), np.full(n, z_)], 1)
        top = proud * rr.uniform(0.85, 1.1)
        dome = rr.uniform(0.25, 0.45)
        V = np.concatenate([ring(rad * 0.97, -embed), ring(rad, top - 0.004), ring(rad * (0.92 - dome * 0.3), top - 0.001),
                            ring(rad * 0.55, top + rad * dome * 0.15)])
        q = []
        for r_ in range(3):
            for j in range(n):
                q.append((r_ * n + j, r_ * n + (j + 1) % n, (r_ + 1) * n + (j + 1) % n, (r_ + 1) * n + j))
        tilt = rr.normal(0, 0.12)
        V[:, 0] += tilt * np.clip(V[:, 2] - top + 0.004, 0, None)      # axe-trimmed, slightly skew head
        acc.add(V, [np.array(q), np.arange(3 * n, 4 * n)[None, :]], "M_timber")
    return build


def peg(acc, p, axis, rad=0.014, proud=0.016, embed=0.03, rng=None):
    """oak peg (pooled: 4 variants per size, placed as linked duplicates). acc is unused (kept for call sites)."""
    key = f"peg_{int(rad * 1000)}_{int(proud * 1000)}"
    get_pool(key, _peg_builder(rad, proud, embed), 4)
    h = int(_hash01(np.array([p[0] * 31.0 + p[1] * 17.0 + p[2] * 7.0]))[0] * 4)
    place(key, h, axis_matrix(p, axis, roll=h * 1.3), "KEEP_peg")


def _nail_builder(rad, h):
    def build(acc, i):
        rr = np.random.default_rng(5000 + i)
        prof = [(rad, -0.003), (rad, 0.0), (rad * rr.uniform(0.8, 0.9), h * 0.6), (rad * 0.45, h * rr.uniform(0.9, 1.0)),
                (0.0, h * rr.uniform(0.95, 1.05))]
        V, F = lathe(prof, 8, phase=rr.uniform(0, 0.8))
        # hand-forged: faceted, slightly off-centre heads
        V[:, 0] += rr.normal(0, 0.06) * V[:, 2]
        V[:, :2] *= (1 + rr.uniform(-0.06, 0.06, (len(V), 1)) * (V[:, 2:3] > 0.001))
        acc.add(V, F, "M_iron")
    return build


def nail_heads(acc, P, normal, rad=0.009, h=0.006, mat="M_iron"):
    """domed forged nail heads at points P (N,3) on a surface with normal (pooled linked duplicates)."""
    P = np.atleast_2d(P)
    key = f"nail_{int(rad * 10000)}_{int(h * 10000)}"
    get_pool(key, _nail_builder(rad, h), 4)
    for p in P:
        v = int(_hash01(np.array([p[0] * 53.0 + p[1] * 29.0 + p[2] * 11.0]))[0] * 4)
        place(key, v, axis_matrix(p, normal, roll=v * 0.7), "KEEP_nail")


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
                    width_var=None, round_r=0.008, jit_m=0.012, tuck=0.06, scribe=None):
    """Horizontal courses of boards/shingles on an OctRoof between slope coords m0..m1.
    scribe(x, y) -> z: where an adjoining roof rises over this one (wing thatch), every unit is scribed onto it:
    its ends are cut obliquely along the true intersection (butt and tail cut separately), so all course ends
    line up on the valley over the lead apron instead of stepping down as whole dropped boards."""
    recs = []
    missing = []
    base_of = {}
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
                    missing.append((k, ci, x0, x1))
                    continue
                if u < frac_missing + frac_slip:
                    slip = rng.uniform(0.04, 0.10)
                    lift += 0.006
                recs.append((k, x0, x1, mbb - slip, rng.normal(0, rot_sd), lift, ci, t * rng.uniform(0.85, 1.15), slip,
                             mb))
            base_of[(k, ci)] = mb
            mb += expo * rng.uniform(0.96, 1.04)
            ci += 1
    R = np.array(recs)
    k = R[:, 0].astype(int)
    x0, x1, mb, rot, lift, ci, tt, slp = R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 6], R[:, 7], R[:, 8]
    # each unit keeps only its exposed length plus a short tuck under the next course (hidden-geometry budget):
    # m_keep = where the next course's butt (worst case jitter) covers it; units under a missing piece keep all
    nxt = np.array([base_of.get((int(k_), int(c_) + 1), np.nan) for k_, c_ in zip(k, ci)])
    m_keep = np.where(np.isnan(nxt), W, nxt - mb + 2.5 * jit_m + 0.012)
    full = np.isnan(nxt)
    for (km, cm, xa, xb) in missing:
        under = (k == km) & (ci == cm - 1) & (x1 > xa - 0.02) & (x0 < xb + 0.02)
        full |= under
    m_keep = np.where(full, W, np.clip(m_keep, 0.05, W - 0.03))
    Wr = np.where(full, W, np.minimum(W, m_keep + tuck))
    xa_b, xb_b, xa_t, xb_t = x0.copy(), x1.copy(), x0.copy(), x1.copy()
    if scribe is not None:
        ns = 48
        f_ = np.linspace(0, 1, ns)
        keep_s = np.ones(len(k), bool)
        for which, mm in ((0, mb), (1, mb + Wr)):
            XS = x0[:, None] + (x1 - x0)[:, None] * f_[None]
            PS = np.broadcast_to(roof.p_of_m(mm)[:, None], XS.shape)
            S3 = roof.world(np.broadcast_to(k[:, None], XS.shape), XS, PS, np.zeros(XS.shape))
            ok = S3[..., 2] > scribe(S3[..., 0], S3[..., 1])
            for i in np.flatnonzero(~ok.all(1)):
                o = ok[i]
                if not o.any():
                    if which == 0:
                        keep_s[i] = False
                    continue
                # longest contiguous valid run
                best, cur, st = (0, -1), 0, 0
                for j_ in range(ns + 1):
                    if j_ < ns and o[j_]:
                        if cur == 0:
                            st = j_
                        cur += 1
                        if cur > best[1] - best[0] + 1:
                            best = (st, j_)
                    else:
                        cur = 0
                a_, b_ = XS[i, best[0]], XS[i, best[1]]
                if which == 0:
                    xa_b[i], xb_b[i] = a_, b_
                    if b_ - a_ < 0.10:
                        keep_s[i] = False
                else:
                    xa_t[i], xb_t[i] = a_, b_
        # a tail cut may not be wider than the butt cut by more than the valley slope allows (no overhangs)
        xa_t = np.where(xb_t - xa_t < 0.05, xa_b, xa_t)
        xb_t = np.where(xb_t - xa_t < 0.05, xb_b, xb_t)
        k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t = [
            a[keep_s] for a in (k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t)]
    if cull is not None:
        pc = roof.p_of_m(mb + W * 0.5)
        C = roof.world(k, 0.5 * (x0 + x1), pc, np.full(len(k), base_h + t))
        keep = ~cull(C)
        k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t = [
            a[keep] for a in (k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t)]
    M = len(k)
    rr = np.full(M, round_r)
    X = axn(x0, x1, rr, nx)
    # stations along the slope: butt arris, mid exposure, the cover line (m_keep), tuck end
    mk = np.minimum(mb + m_keep, mb + Wr - rr - 0.004)
    Y = np.stack([mb, mb + rr, 0.5 * (mb + rr + mk), mk, mb + Wr - rr, mb + Wr], 1)
    Z = np.stack([np.zeros(M), tt - rr, tt], 1)
    P, quads = rbox(X, Y, Z, rr, skip_back=True, round_back=False)
    x, m, h = P[..., 0], P[..., 1], P[..., 2]
    if scribe is not None:
        # oblique scribed ends: affine remap of x between the butt cut and the tail cut
        fm = np.clip((m - mb[:, None]) / Wr[:, None], 0, 1)
        xa = xa_b[:, None] + (xa_t - xa_b)[:, None] * fm
        xb = xb_b[:, None] + (xb_t - xb_b)[:, None] * fm
        x = xa + (x - x0[:, None]) / (x1 - x0)[:, None] * (xb - xa)
        P = P.copy()
        P[..., 0] = x
    xc = 0.5 * (x0 + x1)[:, None]
    mc = (mb + 0.5 * Wr)[:, None]
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
    F = inst_faces(quads, M, P.shape[1]).reshape(M, -1, 4)
    # drop every face of a unit lying wholly under the next course (beyond its cover line)
    ym = P[..., 1]
    qmin = ym[:, quads].min(axis=2)
    hid = (qmin >= (mk - 1e-6)[:, None]) & ~full[:, None]
    acc.add(W3.reshape(-1, 3), F[~hid], mat, uv=uv)
    return M


def sarking_deck(roof, acc, m0, m1, h_top=-0.005, t=0.02, nx=10, dm=0.25, cull=None, p_floor=0.02,
                 mat="M_timber"):
    """Kit component: continuous sarking deck (t thick, top h_top under the covering) on all 8 facets of an
    OctRoof between slope coords m0..m1. Any gap, slipped or missing covering unit shows timber, never sky or the
    interior (producer note 6). cull(P) -> True drops a cell whose 4 top corners are all buried (e.g. under thatch)."""
    nm = max(2, int(math.ceil((m1 - m0) / dm)) + 1)
    ms = np.linspace(m0, m1, nm)
    u = np.linspace(-1.0, 1.0, nx + 1)
    for k in range(8):
        M_, U_ = np.meshgrid(ms, u, indexing="ij")
        p = np.maximum(roof.p_of_m(M_), p_floor)
        x = U_ * p * TAN22
        top = roof.world(np.full(x.shape, k), x, p, np.full(x.shape, h_top))
        bot = roof.world(np.full(x.shape, k), x, p, np.full(x.shape, h_top - t))
        a, b = top.shape[:2]
        idx = np.arange(a * b).reshape(a, b)
        q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
        if cull is not None:
            Tf = top.reshape(-1, 3)
            buried = np.all(cull(Tf[q]), axis=1)
            q = q[~buried]
        if not len(q):
            continue
        V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
        n = a * b
        F = [q, q[:, ::-1] + n]
        # closed edges along the lowest row (the deck's eave edge) and the hip sides
        e0 = idx[0, :]
        F.append(np.stack([e0[1:], e0[:-1], e0[:-1] + n, e0[1:] + n], -1))
        for col in (idx[:, 0], idx[:, -1]):
            F.append(np.stack([col[:-1], col[1:], col[1:] + n, col[:-1] + n], -1))
        uv = np.concatenate([np.stack([x.ravel(), M_.ravel()], -1)] * 2)
        acc.add(V, F, mat, uv=uv)


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
            p_start = max(p_wall - 0.10, abs(xj) / TAN22 + 0.07)
            p_end = pl - fascia_t - 0.005
            if p_end - p_start < 0.15:
                continue
            _rafter(roof, acc_r, rng, k, xj, p_start, p_end, p_wall, z_plate_top, sheath_t, rw, rd_tip, False, cull, mat_r)
        # hip rafter
        _rafter(roof, acc_r, rng, k, None, p_wall - 0.10, pl - fascia_t - 0.02, p_wall, z_plate_top, sheath_t,
                rw * 1.2, rd_tip * 1.1, True, cull, mat_r)
    # soffit / sheathing boards (visible from below between rafters)
    m_wall = float(roof.m_of_p(p_wall - 0.10))
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
    X = axn(np.full(M, -xh), np.full(M, xh), rr, 9)
    Y = axn(m0, m0 + wd, rr, 4)
    Z = axn(np.full(M, -sheath_t), np.zeros(M), rr, 3)
    P, quads = rbox(X, Y, Z, rr, skip_front=True)               # top face is under the covering
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
    P, quads = rbox(X, Y, Z, np.array([r]), skip_front=True)     # the top face lies under the sheathing
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
                    taper=rng.uniform(0.0, 0.01), wave=0.004, checks=checks, seed=40 + c, drop=(3,))
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
                    if k in (2, 3, 4) else (), drop=(1, 2))
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
                    nf=2, st_len=0.13, adze=0.0035, wave=0.006, seed=70 + k, drop=(1, 2))
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

    def board_scribe(x, y):
        inside = (x > WX_W - W_OVH - 0.05) & (x < WX_E + W_OVH + 0.05) & (y > WY_S - W_OVH - 0.05) & \
            (y < WY_N + W_OVH + 0.05)
        return np.where(inside, thatch_low(x, y) + 0.035, -10.0)
    m_top = float(SKIRT.m_of_p(COLLAR_P - 0.08))          # the collar shakes cover the rest
    n = covering_boards(SKIRT, acc, "M_roof_shingle", rng, -0.05, m_top, expo=0.215, W=0.47, t=0.032,
                        lens=(0.6, 1.2), gap=0.009, nx=8, nm=5, base_h=0.0, scribe=board_scribe, frac_missing=0.015,
                        frac_slip=0.025, curl=0.012, rot_sd=0.012)
    log("  skirt boards", n)
    hip_boards(SKIRT, acc_h, "M_roof_shingle", rng, SKIRT.p_lip + 0.03, 3.3, 0.13, 0.03, 0.065, cull=cull)
    def scribe(XY):
        x, y = XY[:, 0], XY[:, 1]
        inside = (x > WX_W - W_OVH) & (x < WX_E + W_OVH) & (y > WY_S - W_OVH) & (y < WY_N + W_OVH)
        return np.where(inside, thatch_low(x, y) + 0.02, -10.0)
    eave_structure(SKIRT, acc_r, acc_r, acc_r, rng, p_wall=PLATE_APO + PLATE_W / 2, z_plate_top=RAFTER_SEAT,
                   sheath_t=SKIRT_SHEATH, n_raft=6, rw=0.10, rd_tip=0.14,
                   cull=lambda C: wing_roof_zone(C, 0.05) | in_wing(C, margin=-0.6, zpad=-0.5), scribe=scribe,
                   fascia_wave=0.02)
    # continuous sarking deck under the boards on all 8 facets, from just inside the wall plate (where the soffit
    # boards stop) to under the collar shakes; cells deep under the wing thatch are dropped
    def deck_cull(P):
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        inside = (x > WX_W - W_OVH) & (x < WX_E + W_OVH) & (y > WY_S - W_OVH) & (y < WY_N + W_OVH)
        return inside & (z < thatch_low(x, y) - 0.08)
    accdk = Acc("KEEP_roof_skirt_deck")
    sarking_deck(SKIRT, accdk, float(SKIRT.m_of_p(PLATE_APO + PLATE_W / 2 - 0.10)) - 0.03,
                 float(SKIRT.m_of_p(COLLAR_P - 0.30)), h_top=-0.004, t=0.02, nx=12, dm=0.22, cull=deck_cull)
    finalize(accdk, coll)
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
    m0 = float(np.interp(6.03, CONE_ZF, CONE_MF))       # below this the collar hides the cone
    m1 = float(np.interp(9.585, CONE_ZF, CONE_MF))
    cfg = dict(seed=11, footing=None, ch=(0.07, 0.13), p_tall=0.04, len=(0.12, 0.34), foot_len=(0.3, 0.5),
               joint=(0.006, 0.011), front=(0.008, 0.042), foot_proj=(0, 0), bevel=(0.005, 0.025),
               pillow=(0.004, 0.014), tilt=0.009, rot=0.02, p_double=0.05, p_long=0.02, back=0.08, bed_amp=0.018)
    srange = lambda mm: [(0.0, 2 * math.pi * float(np.interp(np.interp(mm, CONE_MF, CONE_ZF), CONE_ZF, CONE_RF)))]
    S = layout_wall(rng, srange, m0, m1, lambda a, b, c: [], cfg)
    pins, _, _ = fill_voids(S, srange, lambda a, b, c: [], m0, m1, rng, cfg, label="cone")
    S = cat_stones(S, pins)
    log("  cone stones:", len(S["sc"]))
    small = (S["hx"] < 0.045) & (S["hy"] < 0.045)
    # budget: one side segment + chamfer band (the cone is never seen closer than ~6 m)
    # round 5: tight joints and a less nibbled outline (visible mortar <= 15 %); 7x7 face grids only on the larger
    # stones, 5x5 on the rest (cone <= 150k tris)
    big = (S["hx"] > 0.13) & ~small
    build_stones(acc, filt(S, big), cone_map_factory(), "M_stone", rng, rough=1.0, noise_amp=0.009, nz2=True, nxy=7,
                 side_depth=0.022)
    build_stones(acc, filt(S, ~big & ~small), cone_map_factory(), "M_stone", rng, rough=1.0, noise_amp=0.008,
                 nz2=True, nxy=5, side_depth=0.022)
    build_stones(acc, filt(S, small), cone_map_factory(), "M_stone", rng, rough=0.9, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=0.022)
    finalize(acc, coll, smooth_deg=28.0)
    # mortar body (lathe) with noise
    accm = Acc("KEEP_cone_mortar")
    zs = np.linspace(5.95, 9.62, 24)
    seg = 72
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
    buried = fpw & (mid[:, 2] < thatch_low(mid[:, 0], mid[:, 1]))
    keep = ~buried
    layer, thc, w, rb, tb, butt, tip, kind, twist = [v[keep] for v in (layer, thc, w, rb, tb, butt, tip, kind, twist)]
    B, T, D, Lb, L = B[keep], T[keep], D[keep], Lb[keep], L[keep]
    M = len(thc)
    E = np.stack([-np.sin(thc), np.cos(thc), np.zeros(M)], 1)
    N = np.cross(E, D)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    rs = np.random.default_rng(5051)
    cang = np.radians(rs.uniform(20, 40, M)) * np.where(rs.uniform(0, 1, M) < 0.5, -1, 1)
    notch = rs.uniform(0.03, 0.07, M)
    taper = rs.uniform(0.10, 0.20, M)
    tb = rs.uniform(0.037, 0.044, M)
    # riven faces: 2-4 longitudinal ridges / hollows of 2-5 mm, drifting a little along the shake
    nrid = rs.integers(2, 5, M)
    rc = rs.uniform(-0.8, 0.8, (M, 4))
    ra = rs.uniform(0.002, 0.005, (M, 4)) * np.where(rs.uniform(0, 1, (M, 4)) < 0.3, -1, 1)
    rsig = rs.uniform(0.12, 0.25, (M, 4))
    # 5-8 % of the shakes are split down 20-40 % of their length (built as two halves that open at the top)
    split = (rs.uniform(0, 1, M) < 0.065) & (layer > 0.5)
    sl = rs.uniform(0.2, 0.4, M)

    def build(sel, ncol, halves=0):
        idx = np.flatnonzero(sel)
        if len(idx) == 0:
            return 0
        Mi = len(idx)
        wi = w[idx] if halves == 0 else w[idx] * 0.5 - 0.002
        rr = np.full(Mi, 0.0095)
        X = axn(-wi / 2, wi / 2, rr, ncol)
        Y = axn(np.zeros(Mi), L[idx], rr, 9)
        Z = np.stack([np.zeros(Mi), tb[idx] - rr, tb[idx]], 1)
        P, quads = rbox(X, Y, Z, rr, skip_back=True, round_back=False)
        x, u, h = P[..., 0], P[..., 1], P[..., 2]
        Li = L[idx][:, None]
        fu = u / Li
        # full-shake lateral coordinate (for ridges / taper) even for split halves
        xc_off = 0.0 if halves == 0 else (halves * (w[idx] * 0.25))[:, None]
        xf = x + xc_off
        xn_full = xf / (w[idx][:, None] / 2)
        # thickness 4 -> 2 cm along the shake (wedge-riven), riven ridges on the face
        h = h * (1 - 0.5 * fu)
        rid = np.zeros_like(h)
        for k_ in range(4):
            on = (k_ < nrid[idx])[:, None]
            c_ = rc[idx, k_][:, None] + 0.12 * np.sin(fu * 3.0 + k_ + idx[:, None])
            rid += np.where(on, ra[idx, k_][:, None] * np.exp(-((xn_full - c_) / rsig[idx, k_][:, None]) ** 2), 0.0)
        h = h + rid * np.clip(h / np.maximum(tb[idx][:, None] * (1 - 0.5 * fu), 1e-4), 0, 1) ** 4
        # width taper 10-20 % toward the top, edges wave +-5 mm
        x = xf * (1 - taper[idx][:, None] * fu)
        edge = np.clip(np.abs(xn_full) - 0.6, 0, 1) / 0.4
        x = x + np.sign(xf) * edge * 0.005 * n1(fu * 6.0 + idx[:, None] * 0.37 + np.sign(xf) * 3.1, 77)
        if halves != 0:
            # the split opens toward the top: halves splay apart and twist slightly
            sp_ = np.clip((fu - (1 - sl[idx][:, None])) / sl[idx][:, None], 0, 1) ** 1.3
            x = x + halves * sp_ * 0.012
            h = h + halves * sp_ * 0.004
        # blunt broken / split ends (never pointed)
        tipz = np.clip((u - (Li - 0.10)) / 0.10, 0, 1)
        xn = x / (w[idx][:, None] / 2)
        wl_ = w[idx][:, None] * 0.82
        k_i = kind[idx][:, None]
        u = u - np.where(k_i == 1, np.tan(np.abs(cang[idx]))[:, None] * (0.5 + 0.5 * np.sign(cang[idx])[:, None] * xn)
                         * wl_ * tipz, 0.0)
        if halves == 0:
            u = u - np.where((k_i == 2) & (np.abs(xn) < 0.22), notch[idx][:, None] * tipz, 0.0)
        u = u - np.where((k_i == 3) | (k_i == 0), 0.012 * tipz * np.abs(np.sin(xn * 4.0 + thc[idx][:, None] * 30)), 0.0)
        x = x + twist[idx][:, None] * u * (u / Li)
        Wv = B[idx][:, None, :] + u[..., None] * D[idx][:, None, :] + x[..., None] * E[idx][:, None, :] + \
            h[..., None] * N[idx][:, None, :]
        acc.add(Wv.reshape(-1, 3), inst_faces(quads, Mi, P.shape[1]), "M_roof_shake",
                uv=np.stack([x, u], -1).reshape(-1, 2))
        return Mi
    build((layer > 0.5) & ~split, 11)
    build(layer < 0.5, 7)
    build(split, 7, halves=-1)
    build(split, 7, halves=1)
    log(f"  collar shakes split: {int(split.sum())}")
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
                     nx=5, ny=4, nz=3, skip_back=k not in opening)
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
    # sarking deck under the shingles from just inside the plate line to the lead hat
    accdk = Acc(f"{prefix}_deck")
    sarking_deck(roof, accdk, float(roof.m_of_p(p_wall - 0.10)) - 0.03, float(roof.m_of_p(0.04)), h_top=-0.004,
                 t=0.018, nx=6, dm=0.2, p_floor=0.03)
    finalize(accdk, coll)
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


def _pintle_builder(acc, i):
    """forged knuckle eye round a pintle pin, with the square shank running into the jamb (local x)."""
    rr = np.random.default_rng(6100 + i)
    V, F = lathe([(0.017, -0.03), (0.0175, -0.026), (0.0175, 0.026), (0.017, 0.03)], 12, phase=rr.uniform(0, 0.5))
    acc.add(V, F, "M_iron")
    V, F = lathe([(0.009, -0.095), (0.009, 0.015), (0.012 + rr.uniform(0, 0.002), 0.02), (0.0, 0.025)], 10)
    acc.add(V, F, "M_iron")
    V, F = sweep(np.array([[0.0, 0, -0.045], [0.045, 0, -0.045], [0.088, 0, -0.045 + rr.normal(0, 0.002)]]),
                 (0, 0, 1), prof_rect(0.018, 0.018, 0.003))
    acc.add(V, F, "M_iron")


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
    # knuckle (rolled eye) + pintle + shank into the jamb: pooled forged part, placed as a linked duplicate
    kp = fmap(k, np.array([x_hinge + 0.012 * -direction]), np.array([z]), np.array([w_face - 0.01]), a_ref=a_ref)[0]
    get_pool("pintle", _pintle_builder, 3)
    ex = np.array([FT[k][0], FT[k][1], 0.0]) * -direction
    ez = np.array([0, 0, 1.0])
    place("pintle", int(z * 10) % 3, frame_matrix(kp, ex, np.cross(ez, ex), ez), "KEEP_pintle")
    # nails along the strap
    nn = int(rng.integers(6, 9))
    ui = np.linspace(0.08, 0.86, nn)
    tk_n = 0.006 * (1 - 0.15 * ui)
    P = fmap(k, x_hinge + direction * ui * x_len, z + np.where(np.arange(nn) % 2 == 0, 0.009, -0.009) * (ui < 0.8),
             w_face + tk_n, a_ref=a_ref)
    nail_heads(nails_acc, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.0085, h=0.006)


def plank_mesh(acc, mapfn, xl_fn, xr_fn, zb_fn, zt_fn, wf_fn, thick, rl_fn, rr_fn, nv, mat, rb=0.008, rt=0.004):
    """one hand-made plank (or split part) as a closed mesh in local door coords (x along the leaf, z up, w out).
    xl_fn/xr_fn(z): edges; zb_fn/zt_fn(x): bottom / top ends; wf_fn(x, z): front face height before arris wear;
    rl_fn/rr_fn(z): arris radius at the left / right edge (0 = square, flush with a neighbour part)."""
    v = np.linspace(0, 1, nv)
    xm0 = 0.5 * (xl_fn(np.array([1.0]))[0] + xr_fn(np.array([1.0]))[0])
    zb_m, zt_m = float(zb_fn(np.array([xm0]))[0]), float(zt_fn(np.array([xm0]))[0])
    zr = zb_m + v * (zt_m - zb_m)
    # extra rows for the rounded bottom and top arrises
    zr = np.concatenate([[zb_m, zb_m + 0.3 * rb, zb_m + rb], zr[1:-1], [zt_m - rt, zt_m - 0.3 * rt, zt_m]])
    zr = np.sort(zr)
    nr = len(zr)
    XL, XR = xl_fn(zr), xr_fn(zr)
    RL, RR = rl_fn(zr), rr_fn(zr)
    cl = np.array([0.0, 0.3, 1.0])
    inner = np.linspace(0, 1, 6)[1:-1]
    cols = []
    for c in cl:
        cols.append((XL + c * RL, RL - np.sqrt(np.maximum(RL ** 2 - (RL - c * RL) ** 2, 0))))
    for f in inner:
        cols.append(((XL + RL) + f * ((XR - RR) - (XL + RL)), np.zeros(nr)))
    for c in cl[::-1]:
        cols.append((XR - c * RR, RR - np.sqrt(np.maximum(RR ** 2 - (RR - c * RR) ** 2, 0))))
    nc = len(cols)
    X = np.stack([c[0] for c in cols], 1)          # (nr, nc)
    DROP = np.stack([c[1] for c in cols], 1)
    # re-map rows per column so the bottom / top follow the (uneven / arched) ends
    zb = zb_fn(X[0])
    zt = zt_fn(X[-1])
    t = (zr - zb_m) / max(zt_m - zb_m, 1e-6)
    tz = np.clip(t, 0, 1)[:, None]
    # keep the small arris rows at a fixed metric distance from the ends
    Z = zb[None, :] + tz * (zt - zb)[None, :]
    Z[1] = zb + 0.3 * rb
    Z[2] = zb + rb
    Z[-2] = zt - 0.3 * rt
    Z[-3] = zt - rt
    # end-arris drops
    endd = np.zeros_like(Z)
    endd[0] = rb
    endd[1] = rb - math.sqrt(rb * rb - (0.7 * rb) ** 2)
    endd[-1] = rt
    endd[-2] = rt - math.sqrt(rt * rt - (0.7 * rt) ** 2)
    W = wf_fn(X, Z) - np.maximum(DROP, endd)
    Vf = np.stack([X, Z, W], -1)
    # back face: edges only
    Wb = wf_fn(X[:, [0, -1]], Z[:, [0, -1]]) * 0 + (np.mean(wf_fn(X, Z)) - thick)
    Vb = np.stack([X[:, [0, -1]], Z[:, [0, -1]], Wb], -1)
    V = np.concatenate([Vf.reshape(-1, 3), Vb.reshape(-1, 3)])
    fi = lambda r, c: r * nc + c
    bi = lambda r, c: nr * nc + r * 2 + c
    F = []
    for r in range(nr - 1):
        for c in range(nc - 1):
            F.append((fi(r, c), fi(r, c + 1), fi(r + 1, c + 1), fi(r + 1, c)))
        F.append((bi(r, 0), bi(r + 1, 0), bi(r + 1, 1), bi(r, 1)))
        F.append((fi(r, 0), fi(r + 1, 0), bi(r + 1, 0), bi(r, 0)))
        F.append((fi(r, nc - 1), bi(r, 1), bi(r + 1, 1), fi(r + 1, nc - 1)))
    F = [np.array(F)]
    F.append(np.array([[fi(0, c) for c in range(nc)] + [bi(0, 1), bi(0, 0)]]))
    F.append(np.array([[fi(nr - 1, c) for c in range(nc)] + [bi(nr - 1, 1), bi(nr - 1, 0)]])[:, ::-1])
    Wd = mapfn(V[:, 0], V[:, 1], V[:, 2])
    acc.add(Wd, F, mat, uv=np.stack([V[:, 1], V[:, 0]], -1))


def plank_leaf(acc, mapfn, x0, x1, zb0, zt_fn, w_front, thick, rng, widths, split=None, rot_corner=None, mat="M_timber",
               nv=70, seed=0):
    """vertical-plank door leaf: widths (m) left->right; split=(plank index, gap m, length m); rot_corner=('L'|'R',
    depth m) rots back the bottom corner of the outermost plank on that side."""
    xs = x0 + np.concatenate([[0], np.cumsum(widths)]) * (x1 - x0) / np.sum(widths)
    n = len(widths)
    offs = rng.uniform(0.001, 0.003, n) * np.where(rng.uniform(0, 1, n) < 0.5, -1, 1)

    def zb_base(x, i):
        z = zb0 + 0.011 + 0.009 * n1(x * 9.0, seed + 7 * i)
        if rot_corner is not None:
            side, dep = rot_corner
            if (side == "L" and i == 0) or (side == "R" and i == n - 1):
                xe = xs[0] if side == "L" else xs[-1]
                d = np.abs(np.asarray(x) - xe)
                z = z + dep * np.clip(1 - d / 0.11, 0, 1) ** 1.4 * (1 + 0.25 * n1(np.asarray(x) * 40, seed + 3))
        return z
    for i in range(n):
        a, b = xs[i] + 0.0006, xs[i + 1] - 0.0006
        cup = rng.uniform(0.002, 0.004)
        rp = rng.uniform(0.003, 0.006)
        wo = offs[i]
        sd = seed * 10 + i

        def wf(x, z, a=a, b=b, cup=cup, wo=wo, sd=sd):
            u = (np.asarray(x) - a) / (b - a)
            grain = 0.0016 * fbm(np.stack([np.asarray(x) * 14.0, np.asarray(z) * 2.2, np.full(np.shape(x), sd * 1.7)], -1), 2)
            grain = grain + 0.0007 * np.sin((np.asarray(x) - a) * 120.0 + 2.0 * n1(np.asarray(z) * 1.5, sd + 2))
            adze = 0.0008 * np.sin(np.asarray(z) * 23.0 + sd) * np.cos(np.asarray(x) * 31.0)
            return w_front + wo - cup * (1 - (2 * np.clip(u, 0, 1) - 1) ** 2) + grain + adze

        def rr_z(z, rp=rp):
            return rp + (0.0095 - rp) * np.clip(1 - (np.asarray(z) - zb0) / 0.3, 0, 1)
        zb_f = lambda x, i=i: zb_base(x, i)
        if split is not None and split[0] == i:
            _, g0, Ls = split
            xsp = a + (b - a) * rng.uniform(0.38, 0.5)
            gap = lambda z: g0 * np.clip(1 - (np.asarray(z) - zb0) / Ls, 0, 1) ** 0.8
            wig = lambda z: 0.003 * n1(np.asarray(z) * 6.0, sd + 5)
            rs = lambda z: np.where(gap(z) > 0.0004, 0.0018, 0.0)
            plank_mesh(acc, mapfn, lambda z: np.full(np.shape(z), a), lambda z: xsp + wig(z) - 0.5 * gap(z) + 0.0003,
                       zb_f, zt_fn, wf, thick, rr_z, rs, nv, mat)
            plank_mesh(acc, mapfn, lambda z: xsp + wig(z) + 0.5 * gap(z) - 0.0003, lambda z: np.full(np.shape(z), b),
                       zb_f, zt_fn, wf, thick, rs, rr_z, nv, mat)
        else:
            plank_mesh(acc, mapfn, lambda z: np.full(np.shape(z), a), lambda z: np.full(np.shape(z), b), zb_f, zt_fn,
                       wf, thick, rr_z, rr_z, nv, mat)
    return xs


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
    widths = rng.permutation(np.array([0.13, 0.18, 0.145, 0.172, 0.135, 0.16, 0.176]))
    zt_fn = lambda x: zs + np.sqrt(np.maximum(R * R - (np.asarray(x) - xc) ** 2, 0.0)) - 0.004
    xs = plank_leaf(acc, lambda x, z, w: fmap(k, x, z, w), xc - R, xc + R, zb0 - 0.006, zt_fn, w_front, 0.04, rng,
                    widths, split=(2, 0.0048, 0.62), rot_corner=("L", 0.042), mat="M_timber", nv=72, seed=11)
    # ledges on the back
    for zl, half in ((0.42, R - 0.06), (1.12, R - 0.06), (1.78, R - 0.12)):
        facet_obox(acc, k, xc - half, xc + half, zl - 0.07, zl + 0.07, w_back - 0.04, w_back, 0.01, "M_timber", nx=6)
    # strap hinges (hinge side = +x edge)
    for zh, ln in ((0.42, 0.78), (1.12, 0.78), (1.80, 0.62)):
        strap_hinge(acci, k, xc + R - 0.005, ln, zh, w_front + 0.0032, rng, acci)
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
    P = fmap(k, pts[:, 0], pts[:, 1], np.full(len(pts), w_front + 0.0025))
    nail_heads(acci, P, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.008, h=0.006)
    # ring pull with backplate, keyhole escutcheon
    hx_ = xc - R + 0.17
    bp = fmap(k, np.array([hx_]), np.array([1.02]), np.array([w_front + 0.003]))[0]
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
        facet_obox(acci, k, hx_ + xa, hx_ + xb, za, zb2, w_front, w_front + 0.0065, 0.0015, "M_iron", nx=4, ny=4, nz=3)
    nail_heads(acci, fmap(k, np.array([hx_, hx_]), np.array([kz + 0.048, kz - 0.048]), np.array([w_front + 0.0065] * 2)),
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


def rough_block(acc, k, x0, x1, z0, z1, w0, w1, r, mat, rng, amp=0.006, dip=0.0, a_ref=A_REF, outline=0.0, chips=0):
    # chipped arrises: conchoidal dents at random points on the top edges (radius 3-6 cm, 1-2.5 cm deep)
    cps = []
    for _ in range(chips):
        side = int(rng.integers(0, 4))
        t_ = rng.uniform(0.15, 0.85)
        ex = x0 + (x1 - x0) * (t_ if side < 2 else (0.0 if side == 2 else 1.0))
        ew = (w0 if side == 0 else w1) if side < 2 else w0 + (w1 - w0) * t_
        cps.append((ex, ew, rng.uniform(0.03, 0.06), rng.uniform(0.01, 0.025)))

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
        for ex, ew, rad, dep in cps:
            dd = np.sqrt((P[:, 0] - ex) ** 2 + (P[:, 2] - ew) ** 2 + (P[:, 1] - z1) ** 2)
            P[:, 1] -= dep * np.clip(1 - dd / rad, 0, 1) ** 1.3
        P[:, 0] += amp * 0.6 * fbm(P[:, [1, 2, 0]] * 7.0, 2)
        P[:, 2] += amp * 0.6 * fbm(P[:, [2, 0, 1]] * 7.0 + 3, 2)
        return P
    nx_, nz_ = (24, 14) if chips else (12, 8)
    facet_obox(acc, k, x0, x1, z0, z1, w0, w1, r, mat, nx=nx_, ny=4, nz=nz_, deform=dfm, a_ref=a_ref)


def build_threshold(coll):
    rng = np.random.default_rng(1010)
    acc = Acc("KEEP_threshold")
    op = OPENINGS[0]
    k, xc = op["k"], op["xc"]
    rough_block(acc, k, xc - 0.62, xc + 0.62, -0.08, 0.12, -0.55, 0.20, 0.025, "M_stone_dressed", rng, amp=0.004, dip=0.012,
                outline=0.012)
    # outside step stone 1.4 x 0.6 x 0.12 (top 0.115)
    rough_block(acc, k, xc - 0.70, xc + 0.70, -0.05, 0.115, 0.24, 0.84, 0.04, "M_stone", rng, amp=0.010, dip=0.0,
                outline=0.06, chips=3)
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
# wing south window (clear 0.45 x 0.55, sill 1.30), clear of the turret base (which meets the S wall at x -9.1..-8.0)
WWIN = dict(xc=-7.4, hw=0.225, z0=1.30, z1=1.85, depth=0.16, fw=0.07)


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
        x_in = s_w + side * (w["hw"] + w["fw"])
        za, zb = w["z0"] - w["fw"], w["z1"] + w["fw"]
        for (z_a, z_b, wd) in ((za, 0.5 * (za + zb) - 0.004, 0.25 if side < 0 else 0.20),
                               (0.5 * (za + zb) + 0.004, zb, 0.20 if side < 0 else 0.25)):
            xa, xb = sorted([x_in, x_in + side * wd])
            recs.append((0.5 * (xa + xb), 0.5 * (z_a + z_b), 0.5 * (xb - xa) - 0.006, 0.5 * (z_b - z_a) - 0.006,
                         0.025, 0.22))
    return np.array(recs)


def wing_open_rects(with_extras=True):
    """opening rects in path coords (s0,s1,z0,z1): frames, lintels, sills, quoins."""
    d = WDOOR
    s_d = S_SOUTH0 + (d["xc"] - WX_W)
    w = WWIN
    s_w = S_SOUTH0 + (w["xc"] - WX_W)
    fw = w["fw"]
    rects = [(s_d - d["hw"] - d["fw"], s_d + d["hw"] + d["fw"], -0.2, d["z1"] + 0.24),
             (s_w - w["hw"] - fw, s_w + w["hw"] + fw, w["z0"] - fw - 0.11, w["z1"] + fw)]
    if with_extras:
        rects += [(s_d - d["hw"] - d["fw"] - 0.23, s_d + d["hw"] + d["fw"] + 0.25, d["z1"], d["z1"] + 0.245),
                  (s_w - w["hw"] - 0.31, s_w + w["hw"] + 0.31, w["z1"] + fw, w["z1"] + fw + 0.17),
                  (s_w - w["hw"] - 0.17, s_w + w["hw"] + 0.17, w["z0"] - fw - 0.115, w["z0"] - fw)]
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
    cfg = dict(seed=17, footing=0.32, ch=(0.09, 0.19), p_tall=0.08, len=(0.20, 0.62), foot_len=(0.40, 1.10),
               foot_lvl=(-0.10, 0.10), joint=(0.009, 0.018), front=(0.005, 0.036), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
               pillow=(0.002, 0.008), tilt=0.008, rot=0.012, p_double=0.07, p_long=0.05, back=0.09, bed_amp=0.03,
               slant=0.27, ch_mix=[(0.28, 0.08, 0.11), (0.38, 0.11, 0.16), (0.24, 0.16, 0.21), (0.10, 0.21, 0.25)],
               pinch=(0.22, (0.04, 0.09), (0.7, 1.8)))
    srange = lambda zm: [(0.0, WING_LEN)]
    S = layout_wall(rng, srange, -0.10, 3.85, excl, cfg, ztop_fn=wing_ztop)
    S = polygonize(S, ((S["sc"] > S_SOUTH0 - 0.05) & (S["zc"] < 3.5) & (S["zc"] > 0.3)) | (S["foot"] > 0.5),
                   np.random.default_rng(1920))
    S = rough_footing(S, np.random.default_rng(3762))
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
    hero = (((S["sc"] > S_SOUTH0 - 0.05) & (S["zc"] < 3.5)) | (S["foot"] > 0.5)) & ~small
    log(f"  wing hero stones {int(hero.sum())}, other {int((~hero & ~small).sum())}, pins {int(small.sum())}")
    build_poly_stones(acc, filt(S, hero), wing_map, "M_stone", np.random.default_rng(2021), rough=1.1, side_depth=0.018,
                      rings=(0.8, 0.58, 0.33))
    build_stones(acc, filt(S, ~hero & ~small), wing_map, "M_stone", rng, rough=1.1, nxy=5, noise_amp=0.008, side_depth=0.018)
    build_stones(acc, filt(S, small), wing_map, "M_stone", rng, rough=0.8, nxy=5, noise_amp=0.005, side_depth=0.018)
    finalize(acc, coll, smooth_deg=28.0)
    # dressed quoins / jamb blocks of the plank door and the window: tooled faces, chipped arrises, out of square
    accq = Acc("KEEP_wing_dressed_stones")
    R = wing_quoins()
    S2 = stone_rec(R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], rng.uniform(0.010, 0.015, len(R)), R[:, 1], rng)
    dress_irregular(S2, rng)
    wear = np.clip(1.0 - S2["zc"] / 0.8, 0, 1)
    build_stones(accq, S2, wing_map, "M_stone_dressed", rng, rough=0.5, dressed=True, grid=(26, 26), wear=wear)
    finalize(accq, coll, smooth_deg=24.0)
    # mortar body: coarse sheet, refined round the openings and the turret junction
    accm = Acc("KEEP_wing_wall_mortar")
    knots = WS[np.flatnonzero(np.abs(np.diff(WN[:, 0])) + np.abs(np.diff(WN[:, 1])) > 1e-6)]
    ss = np.unique(np.round(np.concatenate([np.linspace(0, WING_LEN, int(WING_LEN / 0.3) + 1), knots, knots + 0.01]), 5))
    zs = np.linspace(-0.05, 3.8, 14)
    rects = wing_open_rects(False)

    def near(sm, zm, ds, dz):
        nr = np.zeros(len(sm), bool)
        for s0, s1, za, zb in rects:
            nr |= (sm > s0 - 0.5) & (sm < s1 + 0.5) & (zm > za - 0.5) & (zm < zb + 0.5)
        return nr

    def keep(sm, zm):
        k = np.ones(len(sm), bool)
        for ri_, (s0, s1, za, zb) in enumerate(rects):
            top_m = 0.26 if ri_ == 0 else -0.02           # door rect includes its lintel; the window rect does not
            k &= ~((sm > s0 + 0.04) & (sm < s1 - 0.04) & (zm > za + 0.04) & (zm < zb - top_m))
        zt = np.array([wing_ztop(s_) for s_ in sm])
        k &= zm < zt + 0.02
        Pm = wing_map(sm, zm, np.zeros(len(sm)), zm)
        k &= tur_dist(Pm[:, 0], Pm[:, 1], Pm[:, 2]) > -0.06      # mortar body runs on just behind the turret stones
        ang = np.arctan2(Pm[:, 1], Pm[:, 0])
        kk = np.round(ang / (np.pi / 4)) % 8
        pp = Pm[:, 0] * np.cos(kk * np.pi / 4) + Pm[:, 1] * np.sin(kk * np.pi / 4)
        k &= pp > apo(Pm[:, 2]) - 0.05
        return k
    n = mortar_sheet(accm, lambda s_, z_, w_: wing_map(s_, z_, w_, z_), ss, zs, near, keep, seed=2.0)
    log(f"  wing mortar cells {n}")
    # eave filling (beam fill) on the wall heads of the N, W and S walls: closes the roof space between the wall top
    # and the thatch underside, set back 0.22 m behind the wall face (seen only in the eave gap behind the roll)
    sf = np.arange(0.0, WING_LEN, 0.1)
    Pf = wing_map(sf, np.full(len(sf), W_WALL_H), np.full(len(sf), -0.22), np.full(len(sf), W_WALL_H))
    ok_f = (Pf[:, 0] < WX_E - 0.2) & (tur_dist(Pf[:, 0], Pf[:, 1], np.full(len(sf), 2.8)) > -0.45)
    zt_f = wing_under(Pf[:, 0], Pf[:, 1]) + 0.08
    for r_ in runs_of(np.column_stack([sf, zt_f]), ok_f, 2):
        n_ = len(r_)
        lo = wing_map(r_[:, 0], np.full(n_, W_WALL_H - 0.06), np.full(n_, -0.22), np.full(n_, W_WALL_H))
        hi = wing_map(r_[:, 0], r_[:, 1], np.full(n_, -0.22), np.full(n_, W_WALL_H))
        V = np.concatenate([lo, hi])
        q = np.array([(i, i + 1, n_ + i + 1, n_ + i) for i in range(n_ - 1)])
        O = wing_map(r_[:1, 0], np.full(1, W_WALL_H), np.full(1, 0.5), np.full(1, W_WALL_H)) - lo[:1]
        nn = np.cross(V[q[0, 1]] - V[q[0, 0]], V[q[0, 3]] - V[q[0, 0]])
        if (nn * O[0]).sum() < 0:
            q = q[:, ::-1]
        accm.add(V, q, "M_daub")
    # reveals (door, window): tube through the wall
    def reveal_tube(ring, w0, w1):
        n = len(ring)
        r1 = wing_map(ring[:, 0], ring[:, 1], np.full(n, w0), ring[:, 1])
        r2 = wing_map(ring[:, 0], ring[:, 1], np.full(n, w1), ring[:, 1])
        V = np.concatenate([r1, r2])
        q = np.array([(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)])
        # reveal faces look into the opening (toward its axis)
        cen = V.mean(0)
        nrm = np.cross(V[q[:, 1]] - V[q[:, 0]], V[q[:, 3]] - V[q[:, 0]])
        fc = V[q].mean(1)
        flip = (nrm * (cen - fc)).sum(1) < 0
        q[flip] = q[flip][:, ::-1]
        accm.add(V, q, "M_mortar")
    for ri_, (s0, s1, za, zb) in enumerate(wing_open_rects(False)):
        if ri_ == 0:
            ring = np.array([(s0 + 0.03, za + 0.2), (s1 - 0.03, za + 0.2), (s1 - 0.03, zb - 0.22),
                             (s0 + 0.03, zb - 0.22)])
            if za < 0:
                ring[:2, 1] = 0.0
            reveal_tube(ring, 0.0, -0.64)
        else:
            # window: reveal round the frame from the face back to the frame, then the clear opening to the
            # blocker room (no panel across the head of the opening)
            w = WWIN
            s_w = S_SOUTH0 + (w["xc"] - WX_W)
            fw_, hw_ = w["fw"], w["hw"]
            ro = np.array([(s_w - hw_ - fw_ - 0.004, w["z0"] - fw_), (s_w + hw_ + fw_ + 0.004, w["z0"] - fw_),
                           (s_w + hw_ + fw_ + 0.004, w["z1"] + fw_), (s_w - hw_ - fw_ - 0.004, w["z1"] + fw_)])
            reveal_tube(ro, 0.0, -w["depth"] - 0.02)
            ri = np.array([(s_w - hw_ - 0.004, w["z0"] - 0.004), (s_w + hw_ + 0.004, w["z0"] - 0.004),
                           (s_w + hw_ + 0.004, w["z1"] + 0.004), (s_w - hw_ - 0.004, w["z1"] + 0.004)])
            reveal_tube(ri, -w["depth"] - 0.08, -0.64)
    finalize(accm, coll, recalc=False)


def build_wing_door_window(coll, door=None, window=None):
    """plank door (frame, leaf, ironwork, threshold) and / or small timber window in the wing's S wall, from the
    door / window spec dicts (see plank_door() and window())."""
    rng = np.random.default_rng(1212)
    acc = Acc("KEEP_wing_door")
    acci = Acc("KEEP_wing_door_ironwork")
    accw = Acc("KEEP_wing_window")
    d = door if door is not None else WDOOR
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

    if door is not None:
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
        widths = rng.permutation(np.array([0.135, 0.17, 0.15, 0.13, 0.165, 0.142, 0.158]))
        plank_leaf(acc, wl, xc - hw - 0.015, xc + hw + 0.015, z0 - 0.003, lambda x: np.full(np.shape(x), z1 + 0.02), lw1,
                   lw1 - lw0, rng, widths, split=(4, 0.0042, 0.48), rot_corner=("R", 0.036), mat="M_timber_weathered",
                   nv=60, seed=23)
        for zl in (0.42, 1.15, 1.92):
            box(acc, xc - hw + 0.03, xc + hw - 0.03, zl - 0.07, zl + 0.07, lw0 - 0.04, lw0, 0.01, "M_timber_weathered")
        # three strap hinges (hinge on the west side = -x), latch on +x
        for zh in (0.42, 1.15, 1.92):
            n = 36
            us = np.linspace(0, 1, n)
            xsx = xc - hw + 0.01 + us * 0.70
            wd = strap_widths(us, 0.048, 0.036, 0.074) * (1 + 0.04 * n1(us * 6, int(zh * 50)))
            tk = 0.006 * (1 - 0.15 * us)
            path = wl(xsx, zh + 0.002 * n1(us * 5, int(zh * 31)), lw1 + 0.0032 + 0.5 * tk)
            # profile: right = vertical strap width, up = outward normal (thickness) -> lies flat on the planks
            profs = np.stack([prof_rect(w_, t_, 0.0015) for w_, t_ in zip(wd, tk)])
            V, F = sweep(path, (0, -1, 0), profs)
            acci.add(V, F, "M_iron")
            ui = np.array([0.08, 0.28, 0.48, 0.66, 0.9])
            nail_heads(acci, wl(xc - hw + 0.01 + ui * 0.70, zh + np.array([0.008, -0.008, 0.008, -0.008, 0.0]),
                                lw1 + 0.0032 + 0.006 * (1 - 0.15 * ui)), np.array([0, -1.0, 0]), rad=0.008)
            kp = wl(np.array([xc - hw + 0.005]), np.array([zh]), np.array([lw1 - 0.008]))[0]
            get_pool("pintle", _pintle_builder, 3)
            ex = np.array([-1.0, 0, 0])
            place("pintle", int(zh * 10) % 3, frame_matrix(kp, ex, np.cross(np.array([0, 0, 1.0]), ex),
                                                           np.array([0, 0, 1.0])), "KEEP_pintle")
        # latch: thumb latch handle + bar
        hp = wl(np.array([xc + hw - 0.12]), np.array([1.05]), np.array([lw1]))[0]
        path = np.array([hp + np.array([0, 0, 0.09]), hp + np.array([0, -0.05, 0.06]), hp + np.array([0, -0.06, 0.0]),
                         hp + np.array([0, -0.05, -0.06]), hp + np.array([0, 0, -0.09])])
        V, F = sweep(path, (1, 0, 0), prof_rect(0.016, 0.01, 0.003))
        acci.add(V, F, "M_iron")
        for dz in (0.09, -0.09):
            V, F = lathe([(0.022, 0.0), (0.022, 0.004), (0.0, 0.006)], 10)
            acci.add(np.stack([V[:, 0], -V[:, 2], V[:, 1]], 1) + hp + np.array([0, -0.0, dz]), F, "M_iron")
    if window is not None:
        # window (wing south wall, clear of the turret): 0.07 m timber frame round a 0.45 x 0.55 clear opening with a
        # mullion, set 0.16 m back in the reveal; timber lintel above, projecting stone sill with a drip below; a dark
        # blocker room 1.0 m inside closes the view through it
        w = window
        xw, hww, fwn = w["xc"], w["hw"], w["fw"]
        wz0, wz1 = w["z0"], w["z1"]
        fd0, fd1 = -w["depth"] - 0.10, -w["depth"]
        box(accw, xw - hww - fwn, xw - hww, wz0 - fwn, wz1 + fwn, fd0, fd1, 0.01, "M_timber", ny=6)
        box(accw, xw + hww, xw + hww + fwn, wz0 - fwn, wz1 + fwn, fd0, fd1, 0.01, "M_timber", ny=6)
        box(accw, xw - hww - 0.004, xw + hww + 0.004, wz1, wz1 + fwn, fd0, fd1 - 0.004, 0.01, "M_timber", nx=6)
        box(accw, xw - hww - 0.004, xw + hww + 0.004, wz0 - fwn, wz0, fd0, fd1 - 0.004, 0.01, "M_timber", nx=6)
        box(accw, xw - 0.024, xw + 0.024, wz0 - 0.005, wz1 + 0.005, fd0 + 0.02, fd1 - 0.02, 0.008, "M_timber", ny=6)
        for zz in (wz0 - fwn / 2, wz1 + fwn / 2):
            for xx in (xw - hww - fwn / 2, xw + hww + fwn / 2):
                peg(accw, wl(np.array([xx]), np.array([zz]), np.array([fd1]))[0], np.array([0, -1.0, 0]), rad=0.009,
                    proud=0.007)
        box(accw, xw - hww - 0.30, xw + hww + 0.30, wz1 + fwn, wz1 + fwn + 0.17, -0.45, 0.03, 0.02, "M_timber", nx=6,
            deform=lambda P: adze(P, 7))
        box(accw, xw - hww - 0.16, xw + hww + 0.16, wz0 - fwn - 0.11, wz0 - fwn - 0.004, -0.30, 0.07, 0.012,
            "M_stone_dressed", nx=6)
        # blocker room 1.0 m inside (open toward the window)
        xa_, xb_ = xw - hww - 0.30, xw + hww + 0.30
        za_, zb_ = wz0 - 0.55, wz1 + 0.75
        Pb = np.array([(xa_, za_, -0.62), (xb_, za_, -0.62), (xb_, zb_, -0.62), (xa_, zb_, -0.62),
                       (xa_, za_, -1.0), (xb_, za_, -1.0), (xb_, zb_, -1.0), (xa_, zb_, -1.0)])
        Vb = wl(Pb[:, 0], Pb[:, 1], Pb[:, 2])
        accw.add(Vb, [np.array([[4, 5, 6, 7], [0, 1, 5, 4], [3, 2, 6, 7], [0, 3, 7, 4], [1, 5, 6, 2]])], "M_mortar")
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
    (0.45, 1.025), (0.36, 0.929), (0.25, 0.8106), (0.08, 0.616), (0.0, 0.517),
    (-0.06, 0.428), (-0.11, 0.330), (-0.135, 0.220), (-0.126, 0.118), (-0.088, 0.044), (-0.025, 0.008),
    (0.07, 0.0), (0.20, 0.012), (0.31, 0.055), (0.375, 0.15), (0.41, 0.30), (0.43, 0.44),
    (0.47, 0.62), (0.47, 0.90)])
# round 5: the bolster is slimmed from ~0.5 to ~0.35 m (lower part compressed, the buried tail kept)
_ROLL_CTRL[:, 1] = np.where(_ROLL_CTRL[:, 1] <= 0.6, _ROLL_CTRL[:, 1] * 0.7,
                            _ROLL_CTRL[:, 1] - 0.18 * np.clip((0.95 - _ROLL_CTRL[:, 1]) / 0.35, 0, 1))
# visible weight per control point (ribs / bulges are only applied where the roll can be seen)
_ROLL_VIS = np.array([0, 0.3, 0.3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.8, 0.3, 0, 0], float)


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
           taper=(0.0, 0.0), mat="M_thatch", z_wave=0.012, tmin=(0.45, 0.45), drop_hidden=False, keep_back_fn=None):
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
            tf = tmin[0] + (1 - tmin[0]) * math.sqrt(max(0.0, 1 - (1 - s / taper[0]) ** 2))
        if taper[1] > 0 and L - s < taper[1]:
            tf = min(tf, tmin[1] + (1 - tmin[1]) * math.sqrt(max(0.0, 1 - (1 - (L - s) / taper[1]) ** 2)))
        if tf < 1.0:
            pr = cen + (pr - cen) * tf
        profs.append(pr)
    V, F = sweep(P, ups, np.stack(profs))
    if drop_hidden:
        # the tail of the section buried in the thatch body is not modelled (no caps: the ends sit in stone / thatch)
        m_ = len(prof)
        jj = np.tile(np.arange(m_), len(st) - 1)
        hid = (vis[jj] < 0.5) & (vis[(jj + 1) % m_] < 0.5)
        if keep_back_fn is not None:
            # round 6: keep the roll's back where nothing else closes it (e.g. at the turret, where the core and
            # the turret stones are both cut away): no view into the open roll section
            kb = np.asarray(keep_back_fn(P), bool)
            hid &= ~np.repeat(kb[:-1] | kb[1:], m_)
        F = [F[0][~hid]] + list(F[1:])
    acc.add(V, F, mat)
    return P


EAVE_RC = HIP_RC


def oct_pp(x, y):
    """exact octagon support distance of plan points (max over the 8 facet normals)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return np.max(np.stack([x * math.cos(k * math.pi / 4) + y * math.sin(k * math.pi / 4) for k in range(8)], 0), 0)


def eave_path():
    """plan path of the eave line N -> W -> S with rounded hipped corners (radius EAVE_RC), at the 2.40 lip."""
    yS, yN, xW = WY_S - W_OVH, WY_N + W_OVH, WX_W - W_OVH
    xe = 0.4
    rc = EAVE_RC
    pts = []
    # NE return: the N eave turns the wing's NE corner under the hall skirt and runs south into the hall's N wall
    xr_ = WX_E + W_OVH
    for y in np.arange(3.5, yN - rc, 0.02):
        pts.append((xr_, y))
    for a in np.linspace(0.0, np.pi / 2, 12)[1:-1]:
        pts.append((xr_ - rc + rc * np.cos(a), yN - rc + rc * np.sin(a)))
    for x in np.arange(xr_ - rc, xW + rc, -0.02):
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
    """inward horizontal distance from the (rounded) eave line (same contour family as the deck)."""
    return q_rr(x, y, EAVE_RC)


def thatch_top_z(x, y):
    """approximate outer thatch surface (course tops near the mean, roll top near the eaves)."""
    zt = wing_under(x, y) + (TH_BASE + 0.045) / CP_
    q = eave_q(x, y)
    zr = 2.40 + roll_top_v(q) + 0.0 * q
    return np.where(q < -0.135, -1e9, np.where(q < 0.4, zr, zt))


def contour_polyline(d, x_east, step=0.01, rc=HIP_RC):
    """plan polyline of the roof contour at inset d: N eave side (east -> west), NW hip arc, W side, SW hip arc,
    S side (west -> east). Returns arc length, points, inward normals."""
    xW = WX_W - W_OVH + d
    yS = WY_S - W_OVH + d
    yN = WY_N + W_OVH - d
    P, N = [], []
    xs = np.arange(x_east, xW + rc, -step)
    P.append(np.stack([xs, np.full_like(xs, yN)], 1))
    N.append(np.tile([0.0, -1.0], (len(xs), 1)))
    na = max(int(0.5 * np.pi * rc / step), 4)
    for a0, cy_ in ((0.5 * np.pi, yN - rc), (np.pi, yS + rc)):
        a = np.linspace(a0, a0 + 0.5 * np.pi, na, endpoint=False)
        u = np.stack([np.cos(a), np.sin(a)], 1)
        P.append(np.array([xW + rc, cy_]) + rc * u)
        N.append(-u)
        if a0 < 3:
            ys = np.arange(yN - rc, yS + rc, -step)
            P.append(np.stack([np.full_like(ys, xW), ys], 1))
            N.append(np.tile([1.0, 0.0], (len(ys), 1)))
    xs = np.arange(xW + rc, x_east + 1e-9, step)
    P.append(np.stack([xs, np.full_like(xs, yS)], 1))
    N.append(np.tile([0.0, 1.0], (len(xs), 1)))
    P = np.concatenate(P)
    N = np.concatenate(N)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    keep = np.concatenate([[True], seg > 1e-7])
    P, N = P[keep], N[keep]
    S = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return S, P, N


def deck_point(Q):
    """thatch underside point and unit deck normal at plan points Q (n,2)."""
    e = 1e-3
    x, y = Q[..., 0], Q[..., 1]
    gx = (q_rr(x + e, y) - q_rr(x - e, y)) / (2 * e)
    gy = (q_rr(x, y + e) - q_rr(x, y - e)) / (2 * e)
    z = 2.40 + W_TAN * q_rr(x, y)
    n = np.stack([-W_TAN * gx, -W_TAN * gy, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.stack([x, y, z], -1), n


def thatch_swell(x, y):
    """coherent low-frequency swelling of the thatch mass (+-5-8 cm over 1.5-3 m), faded in from the eave roll."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    v = 0.09 * vnoise(np.stack([x / 2.3, y / 2.3, np.full_like(x, 4.11)], -1)) + \
        0.025 * vnoise(np.stack([x / 1.2 + 5.0, y / 1.2, np.full_like(x, 9.3)], -1))
    return v * np.clip((q_rr(x, y) - 0.45) / 0.6, 0, 1)


def hip_swell(x, y):
    """the thatch builds up over the rounded hips (rounded swell, ~0.25 m radius section)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    dW = x - (WX_W - W_OVH)
    dS = y - (WY_S - W_OVH)
    dN = (WY_N + W_OVH) - y
    out = np.zeros_like(x)
    for d2, other in ((dS, dN), (dN, dS)):
        dh = np.abs(dW - d2) / math.sqrt(2)
        out = np.maximum(out, 0.05 * np.exp(-(dh / 0.24) ** 2) * (np.minimum(dW, d2) < other))
    return out


def _interp_rows(mq, M5, H5):
    n = len(mq)
    ar = np.arange(n)
    idx = np.clip((mq[:, None] >= M5).sum(1) - 1, 0, M5.shape[1] - 2)
    m0, m1 = M5[ar, idx], M5[ar, idx + 1]
    h0, h1 = H5[ar, idx], H5[ar, idx + 1]
    t = np.clip((mq - m0) / np.maximum(m1 - m0, 1e-6), 0, 1)
    return h0 + (h1 - h0) * t


def smooth_wave(A, rng, lam=(2.0, 4.0), n=3):
    """sum of n sines with random wavelengths in lam and random phases, normalised to [-1, 1] (controlled amplitude
    low-frequency drift, unlike value noise whose amplitude is unpredictable)."""
    A = np.asarray(A, float)
    w = rng.uniform(0.5, 1.0, n)
    w /= w.sum()
    out = np.zeros_like(A)
    for wi in w:
        out += wi * np.sin(2 * np.pi * A / rng.uniform(*lam) + rng.uniform(0, 2 * np.pi))
    return out


def thatch_courses(acc, rng, seed, lobe_w=(0.025, 0.045), clump_w=(0.04, 0.12), m0=0.64, m_max=3.95,
                   drift=(0.085, 0.055), expo_lim=(0.24, 0.36), straw_pitch=(0.015, 0.03), straw_depth=(0.005, 0.015),
                   straw_patch=(0.2, 0.5), straw_skew_deg=5.0, end_feather=0.4):
    """Kit component: stepped thatch courses laid as continuous strips round the whole hipped roof (N side, rounded
    NW hip, W end, rounded SW hip, S side), so the hips are a swell of the courses themselves.
    Round 5:
      * course lines drift: a shared low-frequency drift (drift[0], in slope metres) plus an independent per-course
        drift (drift[1]) over 2-4 m wavelengths; the exposure stays inside expo_lim along the whole run, so
        neighbouring butt lines visibly converge and diverge;
      * straw relief on the S slope, both hips and the W end: fall-line ridges straw_depth deep at straw_pitch,
        broken into straw_patch long patches whose direction is skewed +-straw_skew_deg; the N side keeps the
        grouped lobes;
      * every course end (valley under the hall skirt, turret flanks) feathers to nothing over end_feather metres:
        the step, crown and straw relief die out and the course sinks under the course below (no cut stubs);
      * the exposed course top carries an extra crowned row (soft, lumpy, not a flat slab)."""
    from mathutils.kdtree import KDTree
    ms = []
    m = m0
    while m < m_max:
        E = rng.uniform(0.27, 0.33)
        ms.append((m, E))
        m += E
    nC = len(ms)
    pinch_ids = set(int(v) for v in rng.choice(np.arange(2, nC - 2), 2, replace=False))
    x_east = WX_E + W_OVH
    m_ridge = 0.5 * ((WY_N + W_OVH) - (WY_S - W_OVH)) / CP_
    rng_sh = np.random.default_rng(seed * 7 + 1)
    sh_l = [rng_sh.uniform(2.0, 4.0) for _ in range(3)]
    sh_p = [rng_sh.uniform(0, 2 * np.pi) for _ in range(3)]
    sh_w = np.array([0.45, 0.35, 0.2])

    def shared(Aq):
        return sum(w_ * np.sin(2 * np.pi * Aq / l_ + p_) for w_, l_, p_ in zip(sh_w, sh_l, sh_p))
    prev = None
    prev_line = None
    nq_tot = 0
    for ci, (m_i, E) in enumerate(ms):
        d_i = m_i * CP_
        Sx, Px, Nx = contour_polyline(d_i, x_east)
        Lc = Sx[-1]
        # end of the N side straight on this contour: straw relief on the hips, W end and S side only
        xW_c = WX_W - W_OVH + d_i
        A_n = x_east - (xW_c + HIP_RC)
        def in_straw(Aq):
            return np.clip((np.asarray(Aq) - (A_n - 0.4)) / 0.4, 0, 1)
        # columns: grouped lobes on the N side, straw ridges (crest + trough per ridge) elsewhere
        lb = [-rng.uniform(0.0, 0.03)]
        flags = [True]
        nxt = lb[0] + rng.uniform(*clump_w)
        while lb[-1] < Lc + 0.02:
            if in_straw(lb[-1]) > 0.5:
                nb = lb[-1] + rng.uniform(*straw_pitch)
            else:
                nb = lb[-1] + rng.uniform(0.028, 0.042)      # N side: coarser, shallower straw
            fl = nb >= nxt - 0.008
            if fl:
                nxt = nb + rng.uniform(*clump_w)
            lb.append(nb)
            flags.append(fl)
        lb = np.array(lb)
        flags = np.array(flags)
        nl = len(lb) - 1
        clump_of_b = np.cumsum(flags) - 1
        lobe_clump = clump_of_b[:-1]
        A = np.empty(2 * nl + 1)
        A[0::2] = lb
        A[1::2] = lb[:-1] + np.diff(lb) * rng.uniform(0.38, 0.62, nl)
        ncol = len(A)
        isb = np.zeros(ncol, bool)
        isb[0::2] = True
        lid = np.minimum(np.arange(ncol) // 2, nl - 1)
        lprev = np.maximum(lid - 1, 0)
        ncl = int(lobe_clump.max()) + 1
        prot_c = np.clip(0.012 * n1(np.arange(ncl) * 0.35, seed * 31 + ci) + rng.normal(0, 0.004, ncl), -0.018, 0.018)
        prot_l = prot_c[lobe_clump] + rng.normal(0, 0.002, nl)
        crown = rng.uniform(0.002, 0.004, nl)
        bflag = np.zeros(ncol, bool)
        bflag[0::2] = flags
        crease = np.where(bflag, rng.uniform(0.0015, 0.002, ncol), rng.uniform(0.0005, 0.001, ncol))
        p_col = np.where(isb, np.minimum(prot_l[lprev], prot_l[lid]) - 0.002, prot_l[lid])
        cr_ = np.where(isb, -crease, crown[lid])
        # straw relief: patches of 0.2-0.5 m with their own depth and skew
        wst = 0.55 + 0.45 * in_straw(A)
        pb_ = [A[0] - 0.01]
        while pb_[-1] < A[-1] + 0.01:
            pb_.append(pb_[-1] + rng.uniform(*straw_patch))
        pb_ = np.array(pb_)
        npch = len(pb_) - 1
        pch = np.clip(np.searchsorted(pb_, A) - 1, 0, npch - 1)
        pdep = rng.uniform(*straw_depth, npch)
        pskw = np.radians(rng.uniform(-straw_skew_deg, straw_skew_deg, npch))
        # blend patch values over ~4 cm at the patch boundaries (no tearing between patches)
        k_ = np.exp(-0.5 * ((A[:, None] - 0.5 * (pb_[:-1] + pb_[1:])[None]) /
                            (0.25 * np.diff(pb_)[None] + 0.02)) ** 2)
        k_ /= k_.sum(1, keepdims=True)
        skew = k_ @ pskw
        rdep = (k_ @ pdep) * rng.uniform(0.6, 1.0, ncol)
        rd = np.where(isb, -0.5, 0.5) * rdep * wst
        # the straw replaces the soft lobes on the straw zone
        p_col = p_col * 0.25
        cr_ = cr_ * 0.25
        pinch = np.ones(ncol)
        if ci in pinch_ids:
            for _ in range(2):
                ac = rng.uniform(1.0, Lc - 1.0)
                wpi = rng.uniform(0.9, 1.6)
                pinch *= 1 - 0.8 * 0.5 * (1 + np.cos(np.pi * np.clip((A - ac) / (0.5 * wpi), -1, 1)))

        def frame(Aq):
            Pq = np.stack([np.interp(Aq, Sx, Px[:, 0]), np.interp(Aq, Sx, Px[:, 1])], -1)
            Nq = np.stack([np.interp(Aq, Sx, Nx[:, 0]), np.interp(Aq, Sx, Nx[:, 1])], -1)
            return Pq, Nq / np.linalg.norm(Nq, axis=-1, keepdims=True)
        Pc, Nc = frame(A)
        # course line: shared drift + independent drift (2-4 m), exposure clamped to expo_lim against the course
        # below
        # A on a common reference contour (the inner contours are shorter by 2*inset round the W end)
        arc_ = 0.5 * np.pi * HIP_RC
        A_ref = A + 2 * (d_i - m0 * CP_) * np.clip((A - A_n) / arc_, 0, 1)
        indep = smooth_wave(A_ref, rng, (2.0, 4.0), 3)
        mi = m_i + drift[0] * shared(A_ref) + drift[1] * indep
        if prev_line is not None:
            mprev = np.interp(A_ref, prev_line[0], prev_line[1])
            mi = np.clip(mi, mprev + expo_lim[0], mprev + expo_lim[1])
        stp0 = (0.05 + 0.02 * n1(A / 0.7, seed * 100 + ci + 50)) * pinch
        # valley fade toward the hall skirt (the steps die out; the courses sweep into a rounded valley)
        Pb = Pc + Nc * ((mi - m_i) * CP_)[:, None]
        Db, _ = deck_point(Pb)
        zs_b, pp_b = skirt_z_at(Pb[:, 0], Pb[:, 1])
        ztop_nom = Db[:, 2] + (TH_BASE + thatch_swell(Pb[:, 0], Pb[:, 1])) / CP_
        g = ztop_nom - (zs_b + 0.07)
        infoot = pp_b < SKIRT.p_lip + 0.35
        fade = np.where(infoot, np.clip(g / 0.45, 0, 1), 1.0)
        fade = fade * fade * (3 - 2 * fade)
        F = 0.10 + 0.05 * (0.5 + 0.5 * n1(A / 0.9, seed + ci * 7))
        beta = np.radians(rng.uniform(32.0, 40.0))
        bump = 0.004 + 0.006 * (0.5 + 0.5 * n1(A / 0.33, seed * 13 + ci))       # crowned exposure, 0.4-1 cm
        fe = np.ones(ncol)                                                      # end feather (pass 2)

        for pass_ in (0, 1):
            ff = fade * fe
            stp = stp0 * ff
            crr = cr_ * ff
            rdd = rd * fe
            mb = mi - p_col * ff
            m_far = mi + E + 0.07

            def plan(mrow, Ash=None):
                mrow = np.minimum(mrow, m_ridge)
                if Ash is None:
                    return Pc + Nc * ((mrow - m_i) * CP_)[:, None]
                Pq, Nq = frame(A + Ash)
                return Pq + Nq * ((mrow - m_i) * CP_)[:, None]

            def low_at(mrow):
                Q = plan(mrow)
                mg = q_rr(Q[:, 0], Q[:, 1]) / CP_
                if prev is None:
                    return np.interp(mg, ROLL_TOP_M, ROLL_TOP_H)
                kd, pM, pH = prev
                idx = np.array([kd.find((float(q_[0]), float(q_[1]), 0.0))[1] for q_ in Q])
                return _interp_rows(mg, pM[idx], pH[idx])
            Qb = plan(mb)
            sw_b = thatch_swell(Qb[:, 0], Qb[:, 1]) + hip_swell(Qb[:, 0], Qb[:, 1])
            top = TH_BASE + stp + sw_b + np.where(isb, 0.45, 1.0) * crr
            low_b = low_at(mb)
            dh = np.maximum(top - low_b, 0.012) * fe - 0.008 * (1 - fe)
            run = np.maximum(np.abs(dh), 0.004) / np.tan(beta)
            m_mid = mb + run + 0.5 * np.maximum(m_far - mb - run, 0.02)
            rows_m = np.stack([mb - F, mb - 0.45 * F, mb - 0.12 * F, mb - 0.01, mb + run, m_mid, m_far], 1)
            Qf = plan(m_far)
            h_far = TH_BASE - 0.004 + thatch_swell(Qf[:, 0], Qf[:, 1]) + hip_swell(Qf[:, 0], Qf[:, 1]) + 0.3 * crr
            h_top = low_b + dh
            rows_h = np.stack([low_at(mb - F) - 0.004, low_at(mb - 0.45 * F) + 0.05 * dh,
                               low_at(mb - 0.12 * F) + 0.22 * dh, low_b + 0.72 * dh, h_top,
                               0.5 * (h_top + h_far) + bump * ff, h_far], 1)
            # straw ridges (fall-line), all exposed rows; skewed per patch
            rows_h = rows_h + rdd[:, None] * np.array([0.3, 0.6, 0.9, 1.0, 1.0, 1.0, 0.7])[None]
            NR = rows_m.shape[1]
            Am = np.repeat(A[:, None], NR, 1)
            sk = np.tan(skew) * wst
            Q = np.stack([plan(rows_m[:, j], sk * (rows_m[:, j] - mb) * CP_) for j in range(NR)], 1)
            D, Nd = deck_point(Q)
            W = D + rows_h[..., None] * Nd
            # under the hall skirt eave: soft clamp below the skirt sheathing near the valley line
            zs_, pp_ = skirt_z_at(W[..., 0], W[..., 1])
            g_v = wing_top(W[..., 0], W[..., 1]) - (zs_ + 0.07)
            wv = np.clip(0.5 - g_v / 0.2, 0, 1) * (pp_ < SKIRT.p_lip + 0.06)
            wv = wv * wv * (3 - 2 * wv)
            zl = zs_ - 0.05
            zc_ = zl - 0.05 * np.logaddexp(0.0, (zl - W[..., 2]) / 0.05)
            W[..., 2] = W[..., 2] * (1 - wv) + np.minimum(zc_, W[..., 2]) * wv
            idx = np.arange(ncol * NR).reshape(ncol, NR)
            q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
            Wf = W.reshape(-1, 3)
            n0 = np.cross(Wf[q[:, 1]] - Wf[q[:, 0]], Wf[q[:, 3]] - Wf[q[:, 0]])
            if np.median(n0[:, 2]) < 0:
                q = q[:, ::-1]
            C = Wf[q].mean(1)
            x_, y_ = C[:, 0], C[:, 1]
            bad = thatch_cull(C, tol_skirt=False)
            bad |= ~((x_ > WX_W - W_OVH - 0.12) & (x_ < WX_E + W_OVH + 0.04) & (y_ > WY_S - W_OVH - 0.12) &
                     (y_ < WY_N + W_OVH + 0.12))
            bad |= eave_q(x_, y_) < 0.08
            # course tails buried under the ridge dome (within 0.2 m of the ridge line, east of the W hip apex)
            Wq = Wf[q]
            bad |= (np.abs(Wq[..., 1] - WY_R) < 0.2).all(1) & (Wq[..., 0] > WX_W + (WY_R - WY_S) - 0.4).all(1)
            zsq, ppq = skirt_z_at(Wf[q][..., 0], Wf[q][..., 1])
            bad |= ((ppq < SKIRT.p_lip - 0.35) & (Wf[q][..., 2] < zsq - 0.04)).all(1)
            if pass_ == 0:
                # columns whose butt quads survive; feather every course end over end_feather metres
                badc = bad.reshape(ncol - 1, NR - 1)[:, 2:5].any(1)
                dead = np.concatenate([badc, badc[-1:]])
                if dead.any() and not dead.all():
                    di = np.flatnonzero(dead)
                    dd = np.abs(A[:, None] - A[di][None]).min(1)
                    t_ = np.clip(dd / end_feather, 0, 1)
                    fe = t_ * t_ * (3 - 2 * t_)
                    # the run's outer ends (contour ends) are not course ends
                    continue
                break
        q = q[~bad]
        if len(q):
            used = np.unique(q)
            remap = -np.ones(ncol * NR, np.int64)
            remap[used] = np.arange(len(used))
            acc.add(Wf[used], remap[q], "M_thatch", uv=np.stack([Am.ravel(), rows_m.ravel()], -1)[used])
            nq_tot += len(q)
        kd = KDTree(ncol)
        for i_, p_ in enumerate(plan(mb)):
            kd.insert((float(p_[0]), float(p_[1]), 0.0), i_)
        kd.balance()
        prev = (kd, rows_m, rows_h)
        prev_line = (A_ref, mi)
    return nC, nq_tot


def build_wing_roof(coll, seed=3):
    rng = np.random.default_rng(1313)
    acc = Acc("KEEP_wing_roof_thatch")
    # --- continuous stepped courses round the rounded hips (built first: the core is trimmed under them)
    accc = Acc("KEEP_wing_roof_thatch_courses")
    n_c, n_q = thatch_courses(accc, rng, seed)
    log(f"  thatch: {n_c} courses, {n_q} quads")
    ob_c = finalize(accc, coll, smooth_deg=60.0, recalc=False)
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bvh_c = BVHTree.FromObject(ob_c, bpy.context.evaluated_depsgraph_get())
    # --- thatch core body (height field): kept only where it can be seen (verges, holes in the course cover,
    # the eave overhang underside); thinned toward the eaves so its edge is buried inside the eave roll
    xs = np.arange(WX_W - W_OVH, WX_E + W_OVH + 1e-6, 0.09)
    ys = np.linspace(WY_S - W_OVH, WY_N + W_OVH, 60)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zu = wing_under(X, Y)
    Zt = Zu + (CORE_T + thatch_swell(X, Y) + hip_swell(X, Y)) / CP_
    qe = eave_q(X, Y)
    Zt = Zt - 0.22 * np.clip(1 - qe / 0.6, 0, 1)
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
    # top: drop cells under the course cover (probe the 4 corners and the centre)
    covered = np.ones(xm.shape, bool)
    for fx, fy in ((0.5, 0.5), (0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)):
        px = X[:-1, :-1] + (X[1:, 1:] - X[:-1, :-1]) * fx
        py = Y[:-1, :-1] + (Y[1:, 1:] - Y[:-1, :-1]) * fy
        pz = Zt[:-1, :-1] * (1 - fx) * (1 - fy) + Zt[1:, :-1] * fx * (1 - fy) + Zt[:-1, 1:] * (1 - fx) * fy + \
            Zt[1:, 1:] * fx * fy
        hit = np.array([bvh_c.ray_cast(Vector((float(a_), float(b_), float(c_) - 0.01)), Vector((0, 0, 1.0)), 0.6)[0]
                        is not None for a_, b_, c_ in zip(px.ravel(), py.ravel(), pz.ravel())]).reshape(xm.shape)
        covered &= hit
    # keep the core skin wherever the courses thin out or end (hips, the turret flanks, the eave): a grazing view
    # there must meet thatch, never the back of the core
    covered &= (eave_q(xm, ym) > 0.3) & (tur_dist(xm, ym, ztm) > 1.1)
    inside = (xm > WX_W + 0.05) & (xm < WX_E - 0.05) & (ym > WY_S + 0.05) & (ym < WY_N - 0.05)
    Vt = np.stack([X, Y, Zt], -1).reshape(-1, 3)
    Vb = np.stack([X, Y, Zu], -1).reshape(-1, 3)
    acc.add(Vt, quads[(keep & ~covered).ravel()], "M_thatch")
    acc.add(Vb, quads[(keep & ~inside).ravel()][:, ::-1], "M_thatch")
    # close the core's cut edges (turret, hips, eave): a side wall on every boundary edge of the kept region, so a
    # grazing view past a course end or the roll end meets thatch, never the inside of the core
    nv_ = nx_ * ny_
    Vs_ = np.concatenate([Vt, Vb])
    side = []
    K = np.pad(keep, 1, constant_values=False)
    for di, dj, e0, e1 in ((1, 0, (1, 0), (1, 1)), (-1, 0, (0, 1), (0, 0)), (0, 1, (1, 1), (0, 1)),
                           (0, -1, (0, 0), (1, 0))):
        nb = K[1 + di:K.shape[0] - 1 + di, 1 + dj:K.shape[1] - 1 + dj]
        ii, jj = np.nonzero(keep & ~nb)
        a_ = idx[ii + e0[0], jj + e0[1]]
        b_ = idx[ii + e1[0], jj + e1[1]]
        side.append(np.stack([a_, b_, b_ + nv_, a_ + nv_], 1))
    side = np.concatenate(side)
    acc.add(Vs_, side, "M_thatch")
    log(f"  thatch core: top cells {int((keep & ~covered).sum())}/{int(keep.sum())}, "
        f"underside {int((keep & ~inside).sum())}")
    # east verge closing strip (under the hall skirt)
    yv = ys
    xe = np.full_like(yv, xs[-1])
    V = np.concatenate([np.stack([xe, yv, Zu[-1]], 1), np.stack([xe, yv, Zt[-1]], 1)])
    n = len(yv)
    q = np.array([(i, i + 1, n + i + 1, n + i) for i in range(n - 1)])
    cv = np.stack([xe, yv, Zu[-1] + 0.1], 1)
    acc.add(V, q[~thatch_cull(cv[:-1], tol_skirt=False)], "M_thatch")
    # --- eave roll: one continuous D-section roll N -> W -> S round the hipped corners
    path = eave_path()
    # cut where the whole section is buried in the turret stone (W eave) or inside the hall walls (E ends)
    T = np.gradient(path, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Rv = np.cross(np.array([0, 0, 1.0]), T)
    probes = [(-0.135, 0.22), (-0.06, 0.43), (0.0, 0.52), (0.43, 0.44), (0.07, 0.0), (0.25, 0.81)]
    inside_all = np.ones(len(path), bool)
    hall_all = np.ones(len(path), bool)
    for qq, vv in probes:
        Pp = path + Rv * qq + np.array([0, 0, vv])
        inside_all &= tur_dist(Pp[:, 0], Pp[:, 1], Pp[:, 2]) < -0.03
        hall_all &= oct_pp(Pp[:, 0], Pp[:, 1]) < apo(Pp[:, 2]) - 0.05
    # the N eave passes outside the hall's N face: it ends under the skirt with a rounded, tucked-up taper
    ok = ~hall_all & ~inside_all
    global EAVE_RUNS
    EAVE_RUNS = []
    for r_ in runs_of(path, ok, min_len=4):
        # round 6: a run end that dies into the turret tapers (rounded, 0.45 m) instead of stopping as a cut section
        r_a = np.asarray(r_, float)
        near_t = tur_dist(r_a[[0, -1], 0], r_a[[0, -1], 1], r_a[[0, -1], 2] + 0.3) < 0.6
        tp = (0.45 if near_t[0] else 0.0, 0.45 if near_t[1] else 0.0)
        EAVE_RUNS.append(d_roll(acc, r_, ROLL_P, ROLL_VIS, 5 + len(r_), rng, var=0.03, taper=tp, tmin=(0.3, 0.3),
                                drop_hidden=True, sp=(0.022, 0.05),
                                keep_back_fn=lambda P_: tur_dist(P_[:, 0], P_[:, 1], P_[:, 2]) < 1.3))
    nt = 0
    for P in EAVE_RUNS:
        if P is not None:
            nt += tuft_fringe(acc, P, np.random.default_rng(4040 + len(P)))
    log(f"  eave fringe tufts {nt}")
    finalize(acc, coll, smooth_deg=70.0)


def tuft_fringe(acc, P, rng, q_rng=(-0.07, 0.0), L_rng=(0.02, 0.06), sp=(0.004, 0.009), mat="M_thatch"):
    """Kit component: irregular hanging straw fringe along the lower edge of an eave roll swept along path P
    (section ROLL_P): tapered tufts 2-6 cm long (lengths clumped, not a regular zigzag), 1-3 cm wide, staggered
    in depth, splayed outward, with gaps; the tuft roots are buried 1.5 cm in the roll."""
    P = np.asarray(P, float)
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    if d[-1] < 0.3:
        return 0
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Rv = np.cross(np.array([0, 0, 1.0]), T)
    Rv /= np.linalg.norm(Rv, axis=1, keepdims=True) + 1e-9
    low = ROLL_P[ROLL_P[:, 1] < 0.2]
    o = np.argsort(low[:, 0])
    s_ = rng.uniform(0, 0.02)
    recs = []
    clump = smooth_wave(np.array([0.0]), rng)  # advance rng deterministically
    Lw = smooth_wave(d, rng, (0.15, 0.6), 3)
    while s_ < d[-1] - 0.02:
        if rng.uniform() < 0.08:                    # small gaps in the fringe
            s_ += rng.uniform(0.02, 0.06)
            continue
        i = int(np.searchsorted(d, s_))
        i = min(max(i, 0), len(P) - 1)
        q = rng.uniform(*q_rng)
        v = float(np.interp(q, low[o, 0], low[o, 1]))
        lf = float(np.interp(s_, d, Lw))
        L = np.clip(0.5 * (L_rng[0] + L_rng[1]) + 0.5 * (L_rng[1] - L_rng[0]) * (0.6 * lf + 0.4 * rng.uniform(-1, 1)),
                    L_rng[0], L_rng[1])
        recs.append((s_, i, q, v, L, rng.uniform(0.006, 0.013), rng.uniform(0.003, 0.006), rng.uniform(0.0, 0.12),
                     rng.normal(0, 0.25)))
        s_ += rng.uniform(*sp)
    V, F = [], []
    nb = 0
    for (s_, i, q, v, L, w, t, splay, twist) in recs:
        base = np.interp(s_, d, P[:, 0]), np.interp(s_, d, P[:, 1]), np.interp(s_, d, P[:, 2])
        base = np.array(base) + Rv[i] * q + np.array([0, 0, v + 0.015])
        if tur_dist(base[0], base[1], base[2]) < 0.03 or oct_pp(base[0], base[1]) < apo(base[2]) + 0.05:
            continue
        dn = np.array([0, 0, -1.0]) - Rv[i] * splay
        dn /= np.linalg.norm(dn)
        ax = T[i] * math.cos(twist) + Rv[i] * math.sin(twist) * 0.3
        ax -= dn * (ax @ dn)
        ax /= np.linalg.norm(ax)
        bx = np.cross(dn, ax)
        rings = []
        for f_, sc in ((0.0, 1.0), (1.0, rng.uniform(0.1, 0.25))):
            c = base + dn * (L + 0.015) * f_ + bx * 0.004 * f_ * f_
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                rings.append(c + ax * sx * w * 0.5 * sc + bx * sy * t * 0.5 * sc)
        V.append(np.array(rings))
        q4 = []
        for j in range(4):
            a_, b_ = j, (j + 1) % 4
            q4.append((a_ + nb, b_ + nb, b_ + 4 + nb, a_ + 4 + nb))
        q4.append((4 + nb, 5 + nb, 6 + nb, 7 + nb))
        F.append(np.array(q4))
        nb += 8
    if V:
        acc.add(np.concatenate(V), [np.concatenate(F)], mat)
    return len(V)


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


COMB_LEN = np.array([0.24, 0.27, 0.30, 0.33, 0.36, 0.39, 0.42, 0.46, 0.50, 0.55])


def _comb_builder(acc, i):
    """riven ridge-comb shake variant i (local: x across, y along the shake from the butt, z thickness)."""
    rr = np.random.default_rng(7100 + i)
    L = float(COMB_LEN[i])
    wd = rr.uniform(0.06, 0.11)
    th = rr.uniform(0.03, 0.05)              # wedge-thick riven shakes (3-5 cm at the butt)
    r_ = 0.006
    X = axn(np.array([-wd / 2]), np.array([wd / 2]), np.array([r_]), 6)
    Y = axn(np.array([0.0]), np.array([L]), np.array([r_]), 8)
    Z = ax4(np.array([th / 2]), np.array([r_]))
    P, qd = rbox(X, Y, Z, np.array([r_]))
    P = P[0]
    x_, u, h = P[:, 0], P[:, 1], P[:, 2]
    xn = x_ / (wd / 2)
    tip = np.clip((u - (L - 0.08)) / 0.08, 0, 1)
    kind = i % 3
    cang = math.radians(rr.uniform(20, 40)) * rr.choice([-1, 1])
    if kind == 1:
        u = u - math.tan(abs(cang)) * (0.5 + 0.5 * math.copysign(1, cang) * xn) * wd * tip * 0.6
    elif kind == 2:
        u = u - np.where(np.abs(xn) < 0.3, rr.uniform(0.02, 0.045) * tip, 0.0)
    u = u - 0.008 * tip * np.abs(np.sin(xn * 4.0 + L * 37.0))
    h = h * (1 - 0.3 * u / L) + 0.002 * np.cos(xn * np.pi * 1.5 + L * 11) * (h > 0)
    x_ = x_ * (1 - 0.12 * u / L) + 0.004 * np.sin(u * 9 + i)
    acc.add(np.stack([x_, u, h], 1), qd, "M_roof_shake", uv=np.stack([x_, u], 1))


def build_wing_ridge(coll):
    rng = np.random.default_rng(1414)
    acc = Acc("KEEP_wing_ridge_comb")
    acct = Acc("KEEP_wing_roof_rolls")
    x_apex = WX_W + (WY_R - WY_S)
    z_apex = W_RAFT + (WY_R - WY_S) * W_TAN + (TH_BASE + 0.045) / CP_
    xs = np.arange(x_apex - 0.6, WX_E - 0.2, 0.03)
    path = np.stack([xs, np.full_like(xs, WY_R), np.full_like(xs, z_apex)], 1)
    path[:, 2] += 0.03 * n1(xs * 0.5, 31) - 0.03 * np.sin(np.pi * np.clip((xs - x_apex) / (WX_E - x_apex), 0, 1))
    path[:, 2] += thatch_swell(path[:, 0], path[:, 1]) / CP_          # rides the swelling thatch mass
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
    d_roll(acct, path, RIDGE_DOME, RIDGE_VIS, 71, rng, var=0.02, sp=(0.012, 0.04), dep=(0.003, 0.012), drop_hidden=True)
    # ridge-rider log, seated 3 cm into the dome; starts clear of the cushion
    lp = path + np.array([0, 0, 0.115 + 0.07 - 0.03])
    okl = turret_outer(lp[:, 0], lp[:, 1], lp[:, 2]) > -0.08
    lp = lp[np.argmax(okl):]
    LOG_R = 0.07
    V, F = sweep(lp, (0, 0, 1), prof_circle(LOG_R, 12))
    acc.add(V, F, "M_timber_weathered")
    # comb: short, stubby, dense crossed split shakes (V/X pairs) pinned by the log (ref1: a crest 0.15-0.30 m
    # tall); the shakes are a pool of 10 riven variants placed as linked duplicates, butts buried in the dome
    get_pool("comb", _comb_builder, len(COMB_LEN))
    x = lp[0, 0] + rng.uniform(0.08, 0.14)
    x_end = lp[-1, 0] - 0.06
    ncomb = 0
    while x < x_end:
        psi = math.radians(rng.choice([-1, 1]) * rng.uniform(10, 36))
        hdir = np.array([math.sin(psi), math.cos(psi), 0.0])
        zl = float(np.interp(x, lp[:, 0], lp[:, 2]))
        zc = zl + LOG_R + 0.03
        u = rng.uniform()
        sides = (-1, 1) if u > 0.12 else ((rng.choice([-1, 1]),))
        for side in sides:
            lean = math.radians(rng.uniform(18, 34))
            D = side * math.sin(lean) * hdir + math.cos(lean) * np.array([0, 0, 1.0])
            D += np.array([rng.normal(0, 0.06), 0, 0])
            D /= np.linalg.norm(D)
            Lup = rng.uniform(0.07, 0.20) if rng.uniform() < 0.8 else rng.uniform(0.18, 0.25)
            cross = np.array([x + rng.normal(0, 0.012), WY_R + rng.normal(0, 0.01), zc + rng.normal(0, 0.01)])
            # pick the shortest variant that still buries its butt >= 4.5 cm in the dome (or in the rider log)
            Ldn = 0.06
            while Ldn < 0.32:
                pb = cross - D * Ldn
                lat = pb[1] - WY_R
                zd = float(np.interp(pb[0], path[:, 0], path[:, 2])) + float(ridge_dome_top(lat)) - 0.015
                if pb[2] < zd - 0.045 or math.hypot(lat, pb[2] - zl) < LOG_R - 0.025:
                    break
                Ldn += 0.01
            need = Lup + Ldn
            vi = int(np.argmin(np.where(COMB_LEN >= need, COMB_LEN, 9.0)))
            if COMB_LEN[vi] < need:
                vi = int(np.argmax(COMB_LEN))
            base = cross + D * Lup - D * COMB_LEN[vi]
            E = np.cross(D, np.array([0, 0, 1.0]))
            E = E / np.linalg.norm(E) if np.linalg.norm(E) > 1e-3 else np.array([1.0, 0, 0])
            roll = rng.normal(0, 0.25)
            Nn = np.cross(E, D)
            E2 = E * math.cos(roll) + Nn * math.sin(roll)
            place("comb", vi, frame_matrix(base, E2, D, np.cross(E2, D)), "KEEP_ridge_comb_shake")
            ncomb += 1
        # V tufts clustered in groups of 2-3 with gaps between the clusters
        x += rng.uniform(0.05, 0.09) if rng.uniform() < 0.62 else rng.uniform(0.16, 0.26)
    log("  ridge comb shakes", ncomb)
    for xx in np.arange(lp[0, 0] + 0.3, lp[-1, 0], 0.9):
        zz = np.interp(xx, lp[:, 0], lp[:, 2])
        peg(acc, np.array([xx, WY_R, zz + LOG_R]), np.array([0, 0, 1.0]), rad=0.016, proud=0.03)
    # (round 4) the west hips are no longer separate roll tubes: the thatch courses themselves swell round the
    # hips (see thatch_courses), dying into the turret on the fillet
    global HIP_ENDS
    HIP_ENDS = []
    finalize(acc, coll)
    finalize(acct, coll, smooth_deg=70.0)


RIDGE_PATH = None
HIP_ENDS = []


def _wall_frame(r_, nr_):
    """tangent T, up-the-wall U (perpendicular to T in the wall plane) for a polyline on a wall with normals nr_."""
    T_ = np.gradient(r_, axis=0)
    T_ /= np.linalg.norm(T_, axis=1, keepdims=True) + 1e-12
    zz_ = np.array([0, 0, 1.0])
    U_ = zz_[None, :] - (T_ @ zz_)[:, None] * T_ - (nr_ @ zz_)[:, None] * nr_
    un_ = np.linalg.norm(U_, axis=1)
    U_ /= un_[:, None] + 1e-9
    good = un_ > 0.2
    if good.any():
        gi = np.flatnonzero(good)
        for i_ in np.flatnonzero(~good):
            U_[i_] = U_[gi[np.argmin(np.abs(gi - i_))]]
    for _ in range(3):
        U_[1:-1] = U_[:-2] + 2 * U_[1:-1] + U_[2:]
        U_ -= (U_ * T_).sum(1, keepdims=True) * T_
        U_ -= (U_ * nr_).sum(1, keepdims=True) * nr_
        U_ /= np.linalg.norm(U_, axis=1, keepdims=True) + 1e-9
    return T_, U_


def _resample(pts, out_n, step):
    r_ = np.asarray(pts, float)
    dd_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(r_, axis=0), axis=1))])
    ss_ = np.linspace(0, dd_[-1], max(int(dd_[-1] / step) + 1, 2))
    r_ = np.stack([np.interp(ss_, dd_, r_[:, i]) for i in range(3)], 1)
    nr_ = np.stack([np.interp(ss_, dd_, np.asarray(out_n, float)[:, i]) for i in range(3)], 1)
    nr_[:, 2] = 0.0
    nr_ /= np.linalg.norm(nr_, axis=1, keepdims=True) + 1e-9
    return ss_, r_, nr_


def _sweep_wall(acc, r_, U_, nr_, profs, mat):
    n_, npf = profs.shape[:2]
    V = r_[:, None, :] + profs[..., 0:1] * U_[:, None, :] + profs[..., 1:2] * nr_[:, None, :]
    ii = np.arange(n_ - 1)[:, None]
    jj = np.arange(npf)[None, :]
    a_ = ii * npf + jj
    b_ = ii * npf + (jj + 1) % npf
    quads = np.stack([a_, b_, b_ + npf, a_ + npf], -1).reshape(-1, 4)
    caps = [np.arange(npf)[::-1][None, :], ((n_ - 1) * npf + np.arange(npf))[None, :]]
    acc.add(V.reshape(-1, 3), [quads] + caps, mat)


def mortar_fillet(acc, pts, out_n, seed, h_up=0.052, out=0.055, taper=(0.3, 0.3), smooth=True):
    """Kit component: lime-mortar flaunching where a thatch / shingle surface meets masonry (round 5 section):
    a hard top crease feathered 4 mm proud into the stone, one planar ~43 deg face standing <= 5.5 cm proud, the
    toe tucked 3 cm down under the course butts, and the back buried in the wall. The line wanders only at low
    frequency (+-1.5 cm, wavelength >= 1.3 m). Both ends taper to nothing over taper metres (no square cut ends).
    Built with split normals at the crease and the toe (finalize the receiving object with a low smoothing angle)."""
    ss_, r_, nr_ = _resample(pts, out_n, 0.04)
    if ss_[-1] < 0.05 or len(r_) < 2:
        return
    if smooth:
        for _ in range(4):
            r_[1:-1] = 0.25 * r_[:-2] + 0.5 * r_[1:-1] + 0.25 * r_[2:]
    r_[:, 2] += 0.015 * n1(ss_ / 1.3, seed)
    T_, U_ = _wall_frame(r_, nr_)
    L = ss_[-1]
    tf = np.ones(len(ss_))
    if taper[0] > 0:
        tf = np.minimum(tf, np.clip(ss_ / taper[0], 0, 1))
    if taper[1] > 0:
        tf = np.minimum(tf, np.clip((L - ss_) / taper[1], 0, 1))
    tf = np.sqrt(tf * (2 - tf))
    sc_h = (1 + 0.10 * n1(ss_ / 1.6, seed + 1)) * (0.15 + 0.85 * tf)
    sc_o = (1 + 0.10 * n1(ss_ / 1.9, seed + 2)) * (0.1 + 0.9 * tf)
    prof = np.zeros((len(ss_), 6, 2))
    h = h_up * sc_h
    o = out * sc_o
    prof[:, 0] = np.stack([h + 0.012, np.full_like(h, -0.012)], 1)          # buried in the bed joint above
    prof[:, 1] = np.stack([h, np.full_like(h, 0.004)], 1)                   # hard top crease, 4 mm proud
    prof[:, 2] = np.stack([np.zeros_like(h), o], 1)                         # toe on the thatch (planar face)
    prof[:, 3] = np.stack([np.full_like(h, -0.03), o + 0.006], 1)           # toe tucked 3 cm under the butts
    prof[:, 4] = np.stack([np.full_like(h, -0.05), 0.35 * o], 1)
    prof[:, 5] = np.stack([np.full_like(h, -0.05), np.full_like(h, -0.012)], 1)
    _sweep_wall(acc, r_, U_, nr_, prof, "M_mortar")


def stepped_flashing(acc, pts, out_n, seed, step_h=0.16, w=(0.035, 0.20), turn=0.08):
    """Kit component: stepped lead flashing where a roof edge runs steeply (> 50 deg) down a masonry face: the
    lead lies on the stone with its upper edge in level steps (each step tucked into a bed joint every step_h),
    and turns out 'turn' metres over the thatch below; 2 mm proud, 3 mm thick."""
    ss_, r_, nr_ = _resample(pts, out_n, 0.02)
    if ss_[-1] < 0.1 or len(r_) < 3:
        return
    T_, U_ = _wall_frame(r_, nr_)
    z0 = r_[:, 2].min() + 0.03 * n1(np.array([seed * 1.0]), seed)[0]
    ztop = z0 + step_h * np.ceil((r_[:, 2] + 0.05 - z0) / step_h)
    uz = np.maximum(U_[:, 2], 0.25)
    wd = np.clip((ztop - r_[:, 2]) / uz, w[0], w[1])
    prof = np.zeros((len(ss_), 6, 2))
    prof[:, 0] = np.stack([wd + 0.012, np.full_like(wd, -0.010)], 1)
    prof[:, 1] = np.stack([wd, np.full_like(wd, 0.004)], 1)
    prof[:, 2] = np.stack([np.full_like(wd, 0.0), np.full_like(wd, 0.006)], 1)
    prof[:, 3] = np.stack([np.full_like(wd, -0.02), np.full_like(wd, turn)], 1)
    prof[:, 4] = np.stack([np.full_like(wd, -0.03), np.full_like(wd, turn - 0.004)], 1)
    prof[:, 5] = np.stack([np.full_like(wd, -0.012), np.full_like(wd, -0.006)], 1)
    _sweep_wall(acc, r_, U_, nr_, prof, "M_lead")


def flaunch_loop(acc, pts, center, seed, steep_deg=50.0):
    """split a (closed or open) thatch/stone intersection into one continuous run: mortar fillet where the line is
    flatter than steep_deg, stepped lead flashing where steeper; the two overlap by a few cm at every change."""
    P = np.asarray(pts, float)
    if len(P) < 4:
        return
    dxy = np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1)
    dz = np.abs(np.diff(P[:, 2]))
    ang = np.degrees(np.arctan2(dz, dxy + 1e-9))
    # 3-sample running mean with hysteresis-free majority
    ang = np.convolve(np.concatenate([ang[:1], ang, ang[-1:]]), np.ones(3) / 3, "valid")
    st = np.concatenate([ang > steep_deg, [ang[-1] > steep_deg]])
    nrm = np.column_stack([P[:, 0] - center[0], P[:, 1] - center[1], np.zeros(len(P))])
    i0 = 0
    for i in range(1, len(P) + 1):
        if i == len(P) or st[i] != st[i0]:
            a_, b_ = max(i0 - 1, 0), min(i + 1, len(P))
            seg = P[a_:b_]
            if len(seg) >= 2:
                first, last = i0 == 0, i == len(P)
                if st[i0]:
                    stepped_flashing(acc, seg, nrm[a_:b_], seed + i0)
                else:
                    mortar_fillet(acc, seg, nrm[a_:b_], seed + i0, taper=(0.3 if first else 0.0,
                                                                           0.3 if last else 0.0), smooth=False)
            i0 = i


def build_wing_structure(coll):
    """wall plates, rafter poles and battens visible in the eave gap; thatch/stone fillets."""
    rng = np.random.default_rng(1515)
    acc = Acc("KEEP_wing_roof_structure")
    accf = Acc("KEEP_wing_flashing")
    accm = Acc("KEEP_wing_fillet")
    # (round 4) wall plates and battens are buried in the thatch: only the rafter-pole ends that show in the eave
    # gap behind the roll are modelled
    # rafter poles every ~0.6 m with battens across; the pole feet sit on the wall plate and project 2-5 cm past
    # its face into the eave gap behind the roll: chamfered / axe-cut ends, some checked
    prng = np.random.default_rng(1517)
    for name in ("S", "N"):
        pl = PLANES[name]
        m_wall = W_OVH / CP_
        for xr in np.arange(WX_W + 0.35, WX_E + 0.3, 0.62):
            xr2 = xr + rng.normal(0, 0.03)
            proj = prng.uniform(0.02, 0.05)
            m0 = m_wall - (proj + 0.01) / CP_
            ms = np.array([m0, m0 + 0.012, m0 + 0.03, m0 + 0.06, m0 + 0.1, m0 + 0.2, m0 + 0.32])
            path = pl["o"](np.full_like(ms, xr2), ms) - pl["n"] * 0.12
            path[:, 2] -= 0.004 * np.sin(np.linspace(0, 3, len(ms)))
            if thatch_cull(path.mean(0)[None], tol_skirt=False)[0]:
                continue
            if tur_dist(path[:, 0], path[:, 1], path[:, 2]).min() < 0.15:
                continue
            zs_, pp_ = skirt_z_at(path[:, 0], path[:, 1])
            if (pp_ < SKIRT.p_lip + 0.4).any():
                continue
            rr0 = 0.058 + prng.uniform(-0.007, 0.007)
            npf = 12
            ang = np.linspace(0, 2 * np.pi, npf, endpoint=False)
            kch = int(prng.integers(0, npf)) if prng.uniform() < 0.6 else -1
            chd = prng.uniform(0.012, 0.02)
            dcut = (ms - m0) * CP_
            profs = []
            for i_, d_ in enumerate(dcut):
                rad = rr0 * (0.78 if i_ == 0 else (0.94 if i_ == 1 else 1.0))
                pr = np.stack([rad * np.cos(ang), rad * np.sin(ang)], 1) * (1 + 0.04 * np.sin(ang * 2 + xr))[:, None]
                if kch >= 0 and d_ < 0.09:
                    f_ = (1 - d_ / 0.09)
                    pr[kch] *= 1 - chd / rad * f_
                    pr[(kch + 6) % npf] *= 1 - 0.5 * chd / rad * f_ * (prng.uniform() < 0.5)
                profs.append(pr)
            V, F = sweep(path, pl["n"], np.stack(profs))
            # axe-cut end: the end ring is skewed +-12 deg
            tilt = math.tan(math.radians(prng.uniform(-12, 12)))
            ax_ = path[1] - path[0]
            ax_ /= np.linalg.norm(ax_)
            V[:npf] += ax_ * (tilt * (V[:npf] - path[0]) @ np.cross(ax_, pl["n"]))[:, None]
            acc.add(V, F, "M_timber_weathered")
    finalize(acc, coll)
    # lime-mortar fillet where the thatch meets the turret stone (S, W and N): a triangular flaunching, 6-10 cm up
    # the stone with a flat ~42 deg face, wandering only at low frequency; the course butts run straight into it
    frng = np.random.default_rng(1516)
    ell = np.stack([np.cos(np.linspace(0, 2 * np.pi, 12, endpoint=False)),
                    np.sin(np.linspace(0, 2 * np.pi, 12, endpoint=False))], 1)

    def mortar_tube(pts, ups, rx, ry, seed):
        pts = np.asarray(pts, float)
        if len(pts) < 3:
            return
        prof = ell * np.array([rx, ry])
        d_roll(accf, pts, prof, np.ones(len(prof)), seed, frng, up=ups, var=0.007, sp=(0.06, 0.12),
               dep=(0.0, 0.0015), taper=(0.04, 0.04), mat="M_mortar", z_wave=0.0)
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
    # heavy smoothing round the loop (wavelength >= 1 m), bounded to +-2.5 cm of the real thatch surface
    n_all = len(pts)
    zraw = np.array([p_[2] if p_ is not None else np.nan for p_ in pts])
    zs2 = zraw.copy()
    for i_ in range(n_all):
        if pts[i_] is None:
            continue
        ww, vv = 0.0, 0.0
        for k_ in range(-45, 46, 3):
            z_ = zraw[(i_ + k_) % n_all]
            if not np.isnan(z_):
                g_ = math.exp(-(k_ / 22.0) ** 2)
                ww += g_
                vv += g_ * z_
        zs2[i_] = float(np.clip(vv / ww, zraw[i_] - 0.025, zraw[i_] + 0.02))
    for i_ in range(n_all):
        if pts[i_] is not None:
            pts[i_] = pts[i_].copy()
            pts[i_][2] = zs2[i_]
    # one continuous run along the true intersection: mortar flaunching where it is flatter than 50 deg, stepped
    # lead where steeper; the open ends (where the thatch leaves the stone) taper to nothing
    first_none = next((i for i, p_ in enumerate(pts) if p_ is None), 0)
    pts = pts[first_none:] + pts[:first_none]
    for r_ in runs_of_list(pts, 4):
        flaunch_loop(accm, r_, TUR_C, 400 + len(r_))
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
        nrm_ = np.column_stack([pts[:, 0], pts[:, 1], np.zeros(len(pts))])
        kk_ = np.round(np.arctan2(pts[:, 1], pts[:, 0]) / (np.pi / 4)) % 8
        nrm_ = np.column_stack([np.cos(kk_ * np.pi / 4), np.sin(kk_ * np.pi / 4), np.zeros(len(pts))])
        mortar_fillet(accm, pts - np.array([0, 0, 0.01]), nrm_, 53)
    # lead valley apron where the hall skirt roof and the wing thatch meet: a 0.32 m lead sheet dressed over the
    # real course steps (ray-cast onto the built thatch) and tucked under the skirt boards
    def thatch_z(x, y, z0):
        best = None
        for tr in trees:
            hit = tr.ray_cast(Vector((float(x), float(y), float(z0))), Vector((0, 0, -1.0)), 1.5)
            if hit[0] is not None and (best is None or hit[0].z > best):
                best = hit[0].z
        return best
    for k in range(1, 8):
        # d(x, p) = skirt sheathing top - thatch reference on a grid over the facet; the apron follows d = 0
        xg = np.linspace(-SKIRT.p_lip * TAN22, SKIRT.p_lip * TAN22, 140)
        pg = np.linspace(SKIRT.p_lip + 0.02, 3.4, 110)
        XG, PG = np.meshgrid(xg, pg, indexing="ij")
        Sg = SKIRT.surf(np.full(XG.shape, k), XG, PG)
        xx, yy = Sg[..., 0], Sg[..., 1]
        inside = (xx > WX_W - W_OVH + 0.05) & (xx < WX_E + W_OVH) & (yy > WY_S - W_OVH + 0.05) & \
            (yy < WY_N + W_OVH - 0.05) & (np.abs(XG) < PG * TAN22 - 0.02)
        dG = Sg[..., 2] + SKIRT_SHEATH - (thatch_low(xx, yy) + 0.03)
        dG = np.where(inside, dG, np.nan)
        pts_ = []
        for i_ in range(len(xg)):
            for j_ in range(len(pg)):
                for di, dj in ((1, 0), (0, 1)):
                    if i_ + di >= len(xg) or j_ + dj >= len(pg):
                        continue
                    a_, b_ = dG[i_, j_], dG[i_ + di, j_ + dj]
                    if np.isnan(a_) or np.isnan(b_) or (a_ > 0) == (b_ > 0):
                        continue
                    f_ = a_ / (a_ - b_)
                    pts_.append((xg[i_] + di * f_ * (xg[1] - xg[0]), pg[j_] + dj * f_ * (pg[1] - pg[0])))
        if len(pts_) < 6:
            continue
        pts_ = np.array(pts_)
        # chain the crossing points by nearest-neighbour walking, splitting at jumps
        used = np.zeros(len(pts_), bool)
        chains = []
        while not used.all():
            i_ = int(np.flatnonzero(~used)[np.argmin(pts_[~used, 1])])
            ch = [i_]
            used[i_] = True
            while True:
                dd = np.hypot(pts_[:, 0] - pts_[ch[-1], 0], pts_[:, 1] - pts_[ch[-1], 1])
                dd[used] = 1e9
                j_ = int(np.argmin(dd))
                if dd[j_] > 0.12:
                    break
                ch.append(j_)
                used[j_] = True
            if len(ch) >= 6:
                chains.append(pts_[ch])
        for C in chains:
            # resample evenly and smooth
            dl = np.concatenate([[0], np.cumsum(np.hypot(np.diff(C[:, 0]), np.diff(C[:, 1])))])
            ss = np.arange(0, dl[-1], 0.05)
            if len(ss) < 4:
                continue
            C = np.stack([np.interp(ss, dl, C[:, 0]), np.interp(ss, dl, C[:, 1])], 1)
            for _ in range(4):
                C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
            # cross direction: toward the skirt-on-top side (d > 0)
            Tn = np.gradient(C, axis=0)
            Tn /= np.linalg.norm(Tn, axis=1, keepdims=True) + 1e-9
            Nn = np.stack([-Tn[:, 1], Tn[:, 0]], 1)
            probe = C + Nn * 0.1
            Sp_ = SKIRT.surf(np.full(len(C), k), probe[:, 0], probe[:, 1])
            dp_ = Sp_[:, 2] + SKIRT_SHEATH - (thatch_low(Sp_[:, 0], Sp_[:, 1]) + 0.03)
            Nn = Nn * np.where(np.median(dp_) > 0, 1.0, -1.0)
            offs = np.array([0.17, 0.09, 0.02, -0.06, -0.15])
            n_ = len(C)
            G = np.zeros((n_, len(offs), 3))
            for i_ in range(n_):
                for j_, o_ in enumerate(offs):
                    q_ = C[i_] + Nn[i_] * o_
                    S3 = SKIRT.surf(np.array([k]), np.array([q_[0]]), np.array([q_[1]]))[0]
                    zt_ = thatch_z(S3[0], S3[1], S3[2] + 0.6)
                    if zt_ is None:
                        zt_ = S3[2] - 0.05
                    z_ = zt_ + 0.012
                    if o_ > 0:
                        z_ = min(z_, S3[2] - 0.012)
                    G[i_, j_] = (S3[0], S3[1], z_)
            G[1:-1] = 0.25 * G[:-2] + 0.5 * G[1:-1] + 0.25 * G[2:]
            Gb = G - np.array([0, 0, 0.009])
            nc_ = len(offs)
            V = np.concatenate([G.reshape(-1, 3), Gb.reshape(-1, 3)])
            off_b = n_ * nc_
            F = []
            for i_ in range(n_ - 1):
                for j_ in range(nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, a_ + 1, a_ + nc_ + 1, a_ + nc_))
                    F.append((off_b + a_, off_b + a_ + nc_, off_b + a_ + nc_ + 1, off_b + a_ + 1))
                for j_ in (0, nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, a_ + nc_, off_b + a_ + nc_, off_b + a_))
            for i_ in (0, n_ - 1):
                for j_ in range(nc_ - 1):
                    a_ = i_ * nc_ + j_
                    F.append((a_, off_b + a_, off_b + a_ + 1, a_ + 1))
            accf.add(V, np.array(F), "M_lead")
            log(f"  valley apron facet {k}: {n_} stations")
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
        d = zz_ - np.where(inside, thatch_low(xx, yy) + 0.04, -10.0)
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
    finalize(accm, coll, smooth_deg=25.0)


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


CUSH = dict(r_body=1.25, z_base=5.92, r_drum=1.15, z_top_drum=6.575, droop_dir=CUSH_E, droop=0.12,
            proj_lo=(0.12, 0.23), proj_up=(0.15, 0.43), h_lo=(0.25, 0.29), stone_len=(0.35, 0.70), joint=0.025,
            weather_deg=10.0, lip_droop=0.15, seed=2323)


def _cush_f(th, spec=CUSH):
    """0 on the W/NW side .. 1 on the E/SE side (the lopsided overhang of ref1)."""
    return 0.5 * (1 + np.cos(np.asarray(th, float) - spec["droop_dir"]))


def cush_out_r(th):
    """outer radius of the cushion's upper corbel course about the turret axis."""
    f = _cush_f(th)
    return CUSH["r_body"] + CUSH["proj_up"][0] + (CUSH["proj_up"][1] - CUSH["proj_up"][0]) * f


def cush_lip_z(th):
    """underside of the lower corbel course (droops toward E/SE)."""
    return CUSH["z_base"] - CUSH["droop"] * _cush_f(th)


TUR_R_TOP = 1.25


TUR_CAP = OctRoof(TUR_C[0], TUR_C[1], p_lip=1.65, z_lip=7.10, d_pts=[0, 0.25, 0.45, 1.65], a_pts=[22, 32, 46, 47],
                  p_min=0.02, kick=0.03, kick_len=0.45, wave=0.008, sag=0.012, seed=13, rot_deg=8.0)


def _softplus(d, k):
    return k * np.logaddexp(0.0, d / k)


def corbel_cushion(acc, accm, center, spec=CUSH):
    """Corbelled stone cushion under a turret cap (kit component): two rough corbel courses of individual stones in
    2-3 cm joints over a mortar body. The lower course projects proj_lo, the upper proj_up beyond the body, both
    growing toward droop_dir, where the lip also sits 'droop' lower; the whole outline wanders +-5 cm round the ring.
    Round 5, per stone: length 0.35-0.70 m, height 0.20-0.36 m (each upper stone its own height: the beds step and
    are packed with 2-4 pinning stones), tilt +-3-6 deg, outer face +-4 cm, 1.2-2 cm arrises, 2-3 planar cleaves
    4-8 cm deep, and a rounded (3-8 cm) top lip on only about half of the upper stones. The bed and head joints are
    filled with mortar recessed 3 cm (no open slot between the courses)."""
    rng = np.random.default_rng(spec["seed"])
    cx, cy = center
    rb, rd = spec["r_body"], spec["r_drum"]
    tw = math.tan(math.radians(spec["weather_deg"]))
    ztd = spec["z_top_drum"]
    wob = lambda th_, c_: 0.05 * (0.6 * np.sin(2 * th_ + 1.3 + c_) + 0.4 * np.sin(5 * th_ + 0.4 + 2 * c_))
    courses = []
    for c in (0, 1):
        r_ref = rb + (0.18 if c == 0 else 0.3)
        th = rng.uniform(0, 2 * np.pi)
        th0 = th
        st = []
        while th < th0 + 2 * np.pi - 1e-6:
            L = rng.uniform(*spec["stone_len"])
            if c == 1:
                # round 6: wider length spread on the upper course (no even 'tyre tread' rhythm)
                L = rng.uniform(spec["stone_len"][0] * 0.85, spec["stone_len"][1] * 1.08)
            dth = (L + spec["joint"]) / r_ref
            if th0 + 2 * np.pi - (th + dth) < spec["stone_len"][0] / r_ref * 0.8:
                dth = th0 + 2 * np.pi - th
            st.append((th, th + dth))
            th += dth
        courses.append(st)

    def covers(a_, b_, t_):
        return np.mod(t_ - a_, 2 * np.pi) <= np.mod(b_ - a_, 2 * np.pi)
    stones = []
    lo_top = []
    pins_wanted = set(int(i) for i in rng.choice(len(courses[1]), 3, replace=False))
    pins = []
    for c, st in enumerate(courses):
        for si, (ta, tb) in enumerate(st):
            tm = 0.5 * (ta + tb)
            f = float(_cush_f(tm, spec))
            jt = spec["joint"] * rng.uniform(0.85, 1.2)
            dj = jt / (rb + 0.3)
            ta_, tb_ = ta + 0.5 * dj, tb - 0.5 * dj
            off = rng.uniform(-0.04, 0.04) * (1.5 if c == 1 else 1.0) + float(wob(tm, c))
            if c == 0:
                proj = spec["proj_lo"][0] + (spec["proj_lo"][1] - spec["proj_lo"][0]) * f + off
                zb = spec["z_base"] - spec["droop"] * f + rng.uniform(-0.015, 0.015)
                h = rng.uniform(0.20, 0.36) - 0.04 * f
                r_in = rb - 0.05
                lo_top.append((ta, tb, zb + h, rb + proj))
                top = zb + h
            else:
                proj = spec["proj_up"][0] + (spec["proj_up"][1] - spec["proj_up"][0]) * f + off
                tt = np.linspace(ta, tb, 9)
                zl = -1e9
                for (a_, b_, z_, r_) in lo_top:
                    if any(covers(a_, b_, t_) for t_ in tt):
                        zl = max(zl, z_)
                zb = zl + spec["joint"] * rng.uniform(0.85, 1.15)
                top = ztd + rng.uniform(-0.075, 0.03)
                h = top - zb
                if h > 0.34:
                    zb = top - 0.34
                    h = 0.34
                if h < 0.20:
                    h = 0.20
                    top = zb + h
                if si in pins_wanted and zb - zl < 0.05:
                    zb = zl + 0.055
                    h = top - zb
                if zb - zl > 0.04 and len(pins) < 4:
                    pins.append((ta_ + (tb_ - ta_) * rng.uniform(0.2, 0.8), zl, zb, rb + min(proj, 0.3)))
                r_in = rd - 0.12 if top < ztd - 0.015 else rd + 0.012
            stones.append(dict(c=c, ta=ta_, tb=tb_, r_in=r_in, r_out=rb + proj, zb=zb, h=h, f=f, top=top,
                               slope=tw + (spec["lip_droop"] * f / max(proj + rb - rd, 0.1) if c == 1 else 0.0)))
    nlo = sum(1 for s_ in stones if s_["c"] == 0)
    log(f"  cushion stones: {nlo} lower + {len(stones) - nlo} upper, {len(pins)} pinning stones")
    for sd in stones:
        r_out, r_in, h = sd["r_out"], sd["r_in"], sd["h"]
        hx = 0.5 * (sd["tb"] - sd["ta"]) * r_out
        dep = r_out - r_in
        ra = rng.uniform(0.012, 0.02)
        X = axn(np.array([-hx]), np.array([hx]), np.array([ra]), 11)
        Y = axn(np.array([0.0]), np.array([h]), np.array([ra]), 7)
        Zc = axn(np.array([0.0]), np.array([dep]), np.array([ra]), 6 if sd["c"] == 0 else 7)
        P, quads = rbox(X, Y, Zc, np.array([ra]), skip_back=True)
        P = P[0]
        Q = P.copy()
        # 2-3 planar cleaves 4-8 cm deep at the outline (crisp planes)
        planes = []
        for _ in range(int(rng.integers(2, 4))):
            ta_ = math.tan(math.radians(rng.uniform(14, 34))) * rng.choice([-1, 1])
            tb_ = math.tan(math.radians(rng.uniform(8, 26))) * rng.choice([-1, 1])
            n_ = np.array([ta_, tb_, 1.0])
            n_ /= np.linalg.norm(n_)
            corner = np.array([np.sign(n_[0]) * hx, (h if n_[1] > 0 else 0.0), dep])
            planes.append((n_, corner @ n_ - rng.uniform(0.04, 0.08) * max(n_[2], 0.5)))
        n_ = np.array([rng.uniform(-0.2, 0.2), -1.0, rng.uniform(0.6, 1.1)])
        n_ /= np.linalg.norm(n_)
        planes.append((n_, np.array([0.0, 0.0, dep]) @ n_ - rng.uniform(0.03, 0.06)))
        if sd["c"] == 1:
            # 1-2 cleaved facets across the top / outer top edge (no upholstered top)
            for _ in range(int(rng.integers(1, 3))):
                n_ = np.array([rng.uniform(-0.5, 0.5), 1.0, rng.uniform(0.3, 0.9)])
                n_ /= np.linalg.norm(n_)
                corner = np.array([np.sign(n_[0]) * hx * rng.uniform(0.3, 1.0), h, dep])
                planes.append((n_, corner @ n_ - rng.uniform(0.03, 0.06)))
        for n_, d0 in planes:
            d = Q @ n_ - d0
            Q = Q - n_[None, :] * _softplus(d, 0.003)[:, None]
        if sd["c"] == 1 and rng.uniform() < 0.5:
            # rounded top outer lip on about half of the upper stones (3-8 cm)
            rl = rng.uniform(0.03, 0.08)
            n_ = np.array([0.0, 1.0, 1.0]) / math.sqrt(2)
            d0 = np.array([0.0, h, dep]) @ n_ - rl * 0.6
            d = Q @ n_ - d0
            Q = Q - n_[None, :] * _softplus(d, 0.25 * rl)[:, None]
        r = r_in + Q[:, 2]
        bb = Q[:, 1]
        if sd["c"] == 1:
            bb = bb - sd["slope"] * np.clip(r - rd, 0, None) * np.clip(bb / max(h, 1e-3), 0, 1)
        tilt = math.tan(math.radians(rng.uniform(3, 6) * rng.choice([-1, 1])))
        pitch = math.tan(math.radians(rng.uniform(-3, 3)))
        bb = bb + tilt * Q[:, 0] + pitch * (Q[:, 2] - dep)
        # round 6: each stone yawed 4-10 deg in plan (one end stands proud of its neighbour: a stepped, lumpy
        # outline instead of a turned ring) and about half get a bellied outer face (2-4 cm)
        wq = np.clip(Q[:, 2] / max(dep, 1e-3), 0.0, 1.0)
        yaw = math.tan(math.radians(rng.uniform(4, 10))) * rng.choice([-1, 1])
        r = r + yaw * Q[:, 0] * wq
        if rng.uniform() < 0.55:
            vb = np.clip(Q[:, 1] / max(h, 1e-3), 0.0, 1.0)
            r = r + rng.uniform(0.02, 0.04) * (4 * vb * (1 - vb)) * wq ** 2
        thv = 0.5 * (sd["ta"] + sd["tb"]) + Q[:, 0] / r_out
        W = np.stack([cx + r * np.cos(thv), cy + r * np.sin(thv), sd["zb"] + bb], 1)
        acc.add(W, quads, "M_stone", uv=np.stack([Q[:, 0] + Q[:, 2], Q[:, 1]], 1))
    # pinning stones packed into the stepped beds (flat slabs, 1 cm back from the lower course face)
    for (tp, zl, zb, r_o) in pins:
        hh = max(zb - zl - 0.008, 0.025)
        L = rng.uniform(0.10, 0.18)
        X = axn(np.array([-L / 2]), np.array([L / 2]), np.array([0.008]), 5)
        Y = axn(np.array([0.0]), np.array([hh]), np.array([0.008]), 4)
        Zc = axn(np.array([0.0]), np.array([0.12]), np.array([0.008]), 4)
        P, quads = rbox(X, Y, Zc, np.array([0.008]), skip_back=True)
        P = P[0]
        r = r_o - 0.13 + P[:, 2] - 0.01
        thv = tp + P[:, 0] / r_o
        W = np.stack([cx + r * np.cos(thv), cy + r * np.sin(thv), zl + 0.004 + P[:, 1] +
                      0.01 * P[:, 0] / L], 1)
        acc.add(W, quads, "M_stone")
    # mortar body, per angle from the stones over it: lower course face -3.5 cm, bed joint filled to 3 cm behind
    # the lower course face, upper course -4 cm, top -3.5 cm under the drum
    NT = 180
    th = np.linspace(0, 2 * np.pi, NT, endpoint=False)

    def course_at(c, key, default):
        out = np.full(NT, np.nan)
        for sd in stones:
            if sd["c"] != c:
                continue
            m_ = covers(sd["ta"] - 0.02, sd["tb"] + 0.02, th)
            out = np.where(m_ & np.isnan(out), sd[key], np.where(m_, np.maximum(out, sd[key]) if key != "zb"
                                                                  else np.minimum(out, sd[key]), out))
        return np.where(np.isnan(out), default, out)
    f = _cush_f(th, spec)
    r_lo = course_at(0, "r_out", rb + 0.15)
    zlo = course_at(0, "zb", spec["z_base"])
    lt = course_at(0, "top", spec["z_base"] + 0.28)
    ub = course_at(1, "zb", spec["z_base"] + 0.3)
    r_up = course_at(1, "r_out", rb + 0.3)
    top = course_at(1, "top", ztd)
    zto = top - tw * (r_up - rd) - spec["lip_droop"] * f
    prof = [(np.full(NT, rb - 0.03), zlo - 0.05), (r_lo - 0.035, zlo + 0.035), (r_lo - 0.035, lt - 0.005),
            (r_lo - 0.03, np.maximum(ub, lt) + 0.012), (r_up - 0.04, np.maximum(ub, lt) + 0.04),
            (r_up - 0.04, zto - 0.06), (r_up - 0.07, zto - 0.035), (np.full(NT, rd - 0.01), np.full(NT, ztd - 0.035))]
    R_ = np.stack([np.broadcast_to(p_[0], (NT,)) for p_ in prof], 1)
    Z_ = np.stack([np.broadcast_to(p_[1], (NT,)) for p_ in prof], 1)
    npf = R_.shape[1]
    V = np.stack([cx + R_ * np.cos(th)[:, None], cy + R_ * np.sin(th)[:, None], Z_], -1).reshape(-1, 3)
    i = np.arange(NT)[:, None]
    j = np.arange(npf - 1)[None, :]
    a0 = i * npf + j
    b0 = ((i + 1) % NT) * npf + j
    accm.add(V, np.stack([a0, a0 + 1, b0 + 1, b0], -1).reshape(-1, 4), "M_mortar")
    return stones


def build_cushion(coll, rng):
    acc = Acc("KEEP_turret_corbel_collar")
    accm = Acc("KEEP_turret_corbel_mortar")
    corbel_cushion(acc, accm, (float(TUR_C[0]), float(TUR_C[1])), CUSH)
    finalize(acc, coll, smooth_deg=26.0)
    finalize(accm, coll)


def turret_cull(C, wing_margin=0.0):
    C = np.asarray(C, float)
    x, y, z = C[..., 0], C[..., 1], C[..., 2]
    fp = (x > WX_W - W_OVH) & (x < WX_E + W_OVH) & (y > WY_S - W_OVH) & (y < WY_N + W_OVH)
    bad = fp & (z > wing_under(x, y) - 0.06) & (z < thatch_low(x, y) - 0.02)
    bad |= in_wing(C, margin=wing_margin, zpad=0.0)
    return bad


def round_map_factory(center, r_nom_fn, r_eff_fn):
    """surface map for a round (optionally clipped) battered wall: s = arc length at the course's nominal radius,
    z up, w outward along the surface normal."""
    cx, cy = float(center[0]), float(center[1])

    def mapfn(s, z, w, zc):
        th = np.asarray(s, float) / r_nom_fn(zc)
        z = np.asarray(z, float)
        r = r_eff_fn(th, z)
        e = 1e-3
        drdz = (r_nom_fn(z + e) - r_nom_fn(z - e)) / (2 * e)
        nr = 1 / np.sqrt(1 + drdz ** 2)
        R = r + np.asarray(w) * nr
        return np.stack([cx + R * np.cos(th), cy + R * np.sin(th), z - np.asarray(w) * drdz * nr], -1)
    return mapfn


def round_stone_wall(name, coll, center, radius_fn, z0, z1, seed, cfg, eff_radius_fn=None, excl_fn=None,
                     cull_fn=None, extra_fn=None, mortar_cull_fn=None, side_depth=0.018):
    """Kit component: a round coursed-rubble wall / tower body. radius_fn(z) is the nominal (battered / flared)
    profile, eff_radius_fn(theta, z) an optional clipped version (engaged in other walls). Stepped polygonal footing,
    pinned voids, shallow stone sides (no buried geometry) and a recessed mortar body. Returns the stone record."""
    rng = np.random.default_rng(seed)
    eff = eff_radius_fn if eff_radius_fn is not None else (lambda th, z: radius_fn(z))
    mapfn = round_map_factory(center, radius_fn, eff)
    excl = excl_fn if excl_fn is not None else (lambda a_, b_, c_: [])
    acc = Acc(f"{name}_stones")
    srange = lambda zm: [(0.0, 2 * math.pi * float(radius_fn(zm)))]
    S = layout_wall(rng, srange, z0, z1, excl, cfg)
    S = polygonize(S, S["foot"] > 0.5, np.random.default_rng(seed + 305))
    S = rough_footing(S, np.random.default_rng(seed + 306))
    pins, _, _ = fill_voids(S, srange, excl, z0, z1, rng, cfg, label=name)
    S = cat_stones(S, pins)
    if cull_fn is not None:
        P = mapfn(S["sc"], S["zc"], np.zeros_like(S["sc"]), S["zcrs"])
        S = filt(S, ~cull_fn(P))
    log(f"  {name} stones", len(S["sc"]))
    small = (S["hx"] < 0.05) & (S["hy"] < 0.05)
    foot = (S["foot"] > 0.5) & ~small
    build_poly_stones(acc, filt(S, foot), mapfn, "M_stone", np.random.default_rng(seed + 406), rough=1.15,
                      side_depth=side_depth)
    small &= ~foot
    low = (S["zc"] < 3.6) & ~foot
    build_stones(acc, filt(S, ~small & low), mapfn, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009,
                 side_depth=side_depth)
    build_stones(acc, filt(S, ~small & ~low & ~foot), mapfn, "M_stone", rng, rough=1.15, nxy=5, noise_amp=0.009,
                 nz2=True, side_depth=side_depth)
    build_stones(acc, filt(S, small), mapfn, "M_stone", rng, rough=0.8, nxy=4, noise_amp=0.005, nz2=True,
                 side_depth=side_depth)
    if extra_fn is not None:
        extra_fn(acc)
    finalize(acc, coll, smooth_deg=28.0)
    accm = Acc(f"{name}_mortar")
    zs = np.linspace(max(z0, CLIP_Z), z1 + 0.02, 26)
    cx, cy = float(center[0]), float(center[1])
    V, F = lathe(np.stack([radius_fn(zs) - 0.004, zs], 1), 120, cx=cx, cy=cy, cap_bottom=False, cap_top=False)
    thv = np.arctan2(V[:, 1] - cy, V[:, 0] - cx)
    rv = eff(thv, V[:, 2]) - 0.004
    V[:, 0] = cx + rv * np.cos(thv)
    V[:, 1] = cy + rv * np.sin(thv)
    Vg = V.reshape(len(zs), 120, 3)
    Cq = 0.25 * (Vg[:-1] + np.roll(Vg[:-1], -1, 1) + Vg[1:] + np.roll(Vg[1:], -1, 1))
    keep = np.ones(len(F[0]), bool) if mortar_cull_fn is None else ~mortar_cull_fn(Cq.reshape(-1, 3))
    accm.add(V, F[0][keep], "M_mortar")
    finalize(accm, coll)
    return S


def build_turret(coll):
    rng = np.random.default_rng(1616)
    cfg = dict(seed=23, footing=0.31, ch=(0.09, 0.17), p_tall=0.07, len=(0.18, 0.52), foot_len=(0.40, 1.10),
               foot_lvl=(-0.09, 0.10), joint=(0.009, 0.018), front=(0.005, 0.034), foot_proj=(0.035, 0.095),
               bevel=(0.005, 0.03),
               pillow=(0.003, 0.012), tilt=0.008, rot=0.016, p_double=0.07, p_long=0.04, back=0.09, bed_amp=0.03)
    # engaged in the wing's N and W walls (bonded with toothing stones), clipped behind the S wall face
    round_stone_wall("KEEP_turret", coll, TUR_C, tur_r, -0.10, TUR_Z_TOP, 1616, cfg, eff_radius_fn=tur_reff,
                     excl_fn=tooth_excl_tur, cull_fn=lambda P: turret_cull(P, wing_margin=0.04),
                     extra_fn=lambda acc: build_tooth_stones(acc, np.random.default_rng(1819)),
                     mortar_cull_fn=lambda C: turret_cull(C, wing_margin=0.06))
    build_cushion(coll, rng)
    # board drum with sill & head rings
    accd = Acc("KEEP_turret_drum")
    z0, z1 = 6.60, 7.02
    th = rng.uniform(0, 0.1)
    TS = TUR_SCALE
    rD = 1.15 * TS
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
             "M_timber_weathered", nx=4, ny=4, nz=3, skip_back=True)
        th += dth
    # sill & head rings: 8 hewn straight pieces each, butt-jointed at every facet corner, pegged
    for ri, (zz, rr_, sz) in enumerate(((z0 + 0.04, 1.08 * TS, 0.12), (z1 - 0.05, 1.08 * TS, 0.1))):
        apo_r = rr_ * math.cos(math.radians(22.5)) + 0.03
        for k in range(8):
            phi = math.radians(45 * k + 11.0 * ri)
            n3 = np.array([math.cos(phi), math.sin(phi), 0])
            t3 = np.array([-math.sin(phi), math.cos(phi), 0])
            half = apo_r * TAN22
            o = np.array([TUR_C[0], TUR_C[1], zz + rng.uniform(-0.006, 0.006)]) + n3 * apo_r - t3 * (half - 0.004)
            hewn_member(accd, o, t3, n3, np.array([0, 0, 1.0]), 2 * half + sz * 0.45, sz, sz, rng, chamfer=0.014,
                        nf=2, st_len=0.16, adze=0.003, wave=0.003, seed=300 + k + 10 * ri, drop=(2,))
            peg(accd, o + t3 * (2 * half + sz * 0.2) + n3 * (sz / 2), n3, rad=0.01, proud=0.01)
    V = np.stack([TUR_C[0] + 1.1 * TS * np.cos(np.linspace(0, 2 * np.pi, 24, endpoint=False)),
                  TUR_C[1] + 1.1 * TS * np.sin(np.linspace(0, 2 * np.pi, 24, endpoint=False)), np.full(24, z1)], 1)
    accd.add(V, np.arange(24)[None, ::-1], "M_timber")
    finalize(accd, coll)
    build_cap(coll, TUR_CAP, "KEEP_turret_cap", rng, p_wall=1.17 * TS, z_plate=7.02, n_raft=4, p_top=0.12,
              expo=0.14, W=0.32, t=0.022, lens=(0.12, 0.17), bracket_z0=6.72)
    accf = Acc("KEEP_finial_turret")
    apex = float(TUR_CAP.zb(0.02))
    lead_hat(accf, TUR_C[0], TUR_C[1], apex, 0.19 * max(TS, 0.85), 0.16)
    finial(accf, (TUR_C[0], TUR_C[1], apex + 0.03), 0.8, 1.5, (-0.3, 1.0))
    finalize(accf, coll)


# ==============================================================================================
# HIDDEN-SURFACE CLEAN-UP (producer note 6): delete polygons no exterior viewpoint can ever reach
# ==============================================================================================
_VIS = {}


def _vis_worker(chunk):
    from mathutils import Vector
    bvh, Vw, T, own = _VIS["bvh"], _VIS["V"], _VIS["T"], _VIS["own"]
    views, VN = _VIS["views"], _VIS["views_np"]
    hidden = []
    for pid, tri_ids in chunk:
        vis = False
        for ti in tri_ids:
            p0, p1, p2 = (Vector(Vw[i]) for i in T[ti])
            cen = (p0 + p1 + p2) / 3
            nrm = (p1 - p0).cross(p2 - p0)
            nrm = nrm.normalized() if nrm.length > 1e-12 else Vector((0, 0, 1))
            pts = [cen] + [cen + (p - cen) * 0.8 for p in (p0, p1, p2)]
            dv = VN - np.array(cen)
            fac = (dv @ np.array(nrm)) / np.maximum(np.linalg.norm(dv, axis=1), 1e-9)
            for side in (1, -1):
                ns = nrm * side
                # most frontal viewpoints first (early exit for visible faces)
                order = [views[i] for i in np.argsort(-fac * side)]
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


def exterior_views(lo, hi, extra=()):
    """the exterior review viewpoints (eye-level rings, crane, aerial) plus near-field actor positions."""
    from mathutils import Vector
    c = (lo + hi) / 2
    r = max(hi[0] - lo[0], hi[1] - lo[1]) / 2
    gz = max(lo[2], 0.0)
    views = []
    for dist_f, z, count in ((1.4, gz + 1.7, 24), (2.5, gz + 1.7, 16), (2.0, gz + (hi[2] - gz) * 0.6, 16),
                             (2.2, hi[2] + r * 1.2, 12), (1.6, hi[2] + r * 2.5, 8)):
        for k in range(count):
            ang = 2 * math.pi * (k + 0.5 * (dist_f > 2)) / count
            views.append(Vector((c[0] + math.cos(ang) * r * dist_f, c[1] + math.sin(ang) * r * dist_f, z)))
    views.append(Vector((c[0], c[1], hi[2] + r * 4)))
    views += [Vector(tuple(map(float, e))) for e in extra]
    return views


# objects whose never-seen faces are deleted by ray test (roof level, structure, stone bodies); close-up hero pieces
# (doors, ironwork, dressed surrounds, eave roll) are left whole
CULL_TARGETS = ["KEEP_roof_collar_shakes", "KEEP_cap_structure", "KEEP_turret_cap_structure", "KEEP_turret_drum",
                "KEEP_cap_shingles", "KEEP_turret_cap_shingles", "KEEP_roof_skirt_boards", "KEEP_roof_skirt_structure",
                "KEEP_hall_eave_plate",
                "KEEP_cap_hips", "KEEP_turret_cap_hips", "KEEP_roof_skirt_hips", "KEEP_lantern_boards",
                "KEEP_lantern_frame", "KEEP_cone_ledge_slabs", "KEEP_wing_roof_structure",
                "KEEP_hall_posts",
                "KEEP_hall_post_bases", "KEEP_hall_knee_braces", "KEEP_door_leaf", "KEEP_wing_door",
                "KEEP_wing_window", "KEEP_threshold", "KEEP_hall_window_frames", "KEEP_wing_ridge_comb",
                "KEEP_turret_stones", "KEEP_wing_wall_stones", "KEEP_turret_corbel_collar"]


def door_views():
    """close-up positions in front of both doors (0.5-2 m out, knee to above head height, either side)."""
    V = []
    k = 3
    for dist in (0.5, 1.0, 2.0):
        for z in (0.4, 1.1, 1.7, 2.3):
            for x in (-0.9, 0.0, 0.9):
                V.append(fmap(k, np.array([OPENINGS[0]["xc"] + x]), np.array([z]), np.array([dist]))[0])
                V.append((WDOOR["xc"] + x, WY_S - dist, z))
    return np.array(V)


def near_views():
    """actor-scale viewpoints close to the building (so nothing an actor could see near the walls / under the
    eaves is ever removed): rings round the hall under and outside the skirt eave, low ground views, along the
    wing walls and round the turret, plus close crane views of the upper tiers."""
    V = []
    for r, z, n in ((4.75, 1.65, 28), (6.2, 1.65, 20), (5.0, 0.6, 14), (7.5, 3.0, 14), (6.5, 9.0, 10), (3.5, 13.5, 6)):
        for k in range(n):
            a = 2 * math.pi * (k + 0.37) / n
            V.append((r * math.cos(a), r * math.sin(a), z))
    for x in np.arange(-10.6, -1.2, 1.3):
        for y in (WY_S - 0.35, WY_S - 1.6, WY_N + 0.35, WY_N + 1.6):
            V.append((x, y, 1.65))
    for y in np.arange(-0.8, 6.0, 1.3):
        V += [(WX_W - 0.35, y, 1.65), (WX_W - 1.6, y, 1.65)]
    for k in range(10):
        a = 2 * math.pi * k / 10
        V.append((TUR_C[0] + 3.6 * math.cos(a), TUR_C[1] + 3.6 * math.sin(a), 6.0))
    # off-ring crane stations (elevation 25-40 deg, azimuths between the review stations): the cull must not
    # open anything a camera between the review rings would see
    for k in range(12):
        a = 2 * math.pi * (k + 0.29) / 12
        for r, z in ((15.0, 9.5), (19.0, 16.0)):
            V.append((-2.5 + r * math.cos(a), r * math.sin(a), z))
    P = np.array(V)
    inside = (oct_pp(P[:, 0], P[:, 1]) < A0 + 0.1) | ((P[:, 0] > WX_W - 0.1) & (P[:, 0] < WX_E + 0.1) &
                                                    (P[:, 1] > WY_S - 0.1) & (P[:, 1] < WY_N + 0.1) & (P[:, 2] < 6.5))
    return P[~inside]


def visibility_cull(targets, extra_views, procs=3, extra_by_target=None):
    """delete the polygons of the target objects that no exterior / near-field viewpoint can see (sampled at each
    triangle's centroid and near its corners, both sides; the same test the review tool applies)."""
    from mathutils.bvhtree import BVHTree
    import multiprocessing as mp
    dg = bpy.context.evaluated_depsgraph_get()
    Vs, Ts, owns = [], [], []
    tri_base = {}
    nv = 0
    nt = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
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
        owns.append(lp + (len(owns) + 1) * 10 ** 7)          # unique id per polygon
        nv += len(co)
        nt += len(lp)
    Vw = np.concatenate(Vs)
    T = np.concatenate(Ts)
    own = np.concatenate(owns)
    lo, hi = Vw.min(0), Vw.max(0)
    base_views = exterior_views(lo, hi, extra_views)
    bvh = BVHTree.FromPolygons(Vw.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)
    _VIS.update(bvh=bvh, V=Vw, T=T, own=own)
    log(f"  visibility: {nt} tris, {len(base_views)} viewpoints")
    total_del = 0
    for name in targets:
        if name not in tri_base:
            continue
        t0, lp = tri_base[name]
        ob = bpy.data.objects[name]
        from mathutils import Vector
        views = base_views + [Vector(tuple(map(float, e))) for e in (extra_by_target or {}).get(name, ())]
        _VIS["views"] = views
        _VIS["views_np"] = np.array([tuple(v) for v in views])
        order = np.argsort(lp, kind="stable")
        bounds = np.flatnonzero(np.diff(lp[order])) + 1
        groups = np.split(order + t0, bounds)
        items = [(int(own[g[0]]), [int(x) for x in g]) for g in groups]
        chunks = [items[i::procs * 8] for i in range(procs * 8)]
        try:
            with mp.get_context("fork").Pool(procs) as pool:
                res = pool.map(_vis_worker, chunks)
        except Exception as ex:          # no fork available: single process
            log("  (visibility: single process)", ex)
            res = [_vis_worker(c_) for c_ in chunks]
        hid = set(int(h) for r_ in res for h in r_)
        base_id = int(own[t0]) - int(lp[0]) if len(lp) else 0
        pids = sorted(h - base_id for h in hid)
        if not pids:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in pids], context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        total_del += len(pids)
        log(f"  visibility cull {name}: -{len(pids)} of {len(groups)} polygons")
    return total_del


# ==============================================================================================
# MODULAR KIT (producer note 2)
# Every component below is a parameterised function that builds its own named object(s). The low-level helpers
# (wall maps, thatch surface functions, turret profile, ...) read one shared dimension table; kit_set() publishes a
# component's parameters to it and _derive() re-derives every dependent table (wing path, turret profile and cap,
# cushion spec, thatch planes, roll seating, toothing). main() builds this keep from the components with its own
# numbers; KEEP_KIT_VARIANT=1 builds a different keep (0.8x turret, 4.0 m x 7.0 m wing) from the same code.
# ==============================================================================================
_CUSH0 = dict(CUSH)
_TURCAP0 = dict(p_lip=1.65, z_lip=7.10, d_pts=[0, 0.25, 0.45, 1.65], a_pts=[22, 32, 46, 47], p_min=0.02, kick=0.03,
                kick_len=0.45, wave=0.008, sag=0.012, seed=13, rot_deg=8.0)


def _derive():
    g = globals()
    g["WY_R"] = 0.5 * (WY_S + WY_N)
    g["W_TAN"] = math.tan(W_PITCH)
    g["W_RAFT"] = 2.40 + W_OVH * W_TAN
    g["TH_V"] = (CORE_T + 0.06) / math.cos(W_PITCH)
    g["TH_V_MIN"] = (CORE_T + 0.01) / math.cos(W_PITCH)
    g["TH_BASE"] = CORE_T + 0.02
    g["SP_"], g["CP_"] = math.sin(W_PITCH), math.cos(W_PITCH)
    g["TUR_ZF"], g["TUR_RF"] = _tur_table()
    g["TOOTH"] = _tooth_specs()
    g["WS"], g["WP"], g["WN"] = build_wing_path()
    g["WING_LEN"] = WS[-1]
    g["S_SOUTH0"] = wing_s_of(WX_W, WY_S)
    g["ROLL_TOP_M"], g["ROLL_TOP_H"] = _roll_top_mh()
    PLANES["S"]["a_rng"] = PLANES["N"]["a_rng"] = (WX_W - W_OVH - 0.3, WX_E + W_OVH)
    PLANES["W"]["a_rng"] = (WY_S - W_OVH - 0.3, WY_N + W_OVH + 0.3)
    PLANES["S"]["n"], PLANES["N"]["n"] = np.array([0, -SP_, CP_]), np.array([0, SP_, CP_])
    PLANES["W"]["n"] = np.array([-SP_, 0, CP_])
    ts = TUR_SCALE
    CUSH.update(r_body=_CUSH0["r_body"] * ts, r_drum=_CUSH0["r_drum"] * ts,
                proj_lo=tuple(v * ts for v in _CUSH0["proj_lo"]), proj_up=tuple(v * ts for v in _CUSH0["proj_up"]),
                stone_len=tuple(v * max(ts, 0.85) for v in _CUSH0["stone_len"]))
    g["TUR_R_TOP"] = 1.25 * ts
    tc = dict(_TURCAP0)
    tc["p_lip"] = _TURCAP0["p_lip"] * ts
    tc["d_pts"] = [d * ts for d in _TURCAP0["d_pts"]]
    g["TUR_CAP"] = OctRoof(TUR_C[0], TUR_C[1], **tc)


def kit_set(**kw):
    """publish component parameters to the shared dimension table and re-derive everything that depends on them."""
    g = globals()
    for k_, v_ in kw.items():
        assert k_ in g, "unknown kit parameter " + k_
        g[k_] = np.asarray(v_, float) if k_ == "TUR_C" else v_
    _derive()


def stone_wall(coll, path="hall", height=None, openings=None, seed=None):
    """Kit component: coursed rubble wall with footing course, dressed surrounds and recessed mortar body along a
    named plan path: 'hall' (battered, bulging octagon of apothem A0) or 'wing' (the wing's N, W and S walls
    between the hall and the turret). openings: list of opening specs (hall) or (door, window) specs (wing)."""
    if path == "hall":
        if height is not None:
            kit_set(WALL_H=height)
        if openings is not None:
            kit_set(OPENINGS=openings)
        build_hall_masonry(coll)
        build_hall_mortar(coll)
        build_hall_interior(coll)
    else:
        if height is not None:
            kit_set(W_WALL_H=height)
        if openings is not None:
            kit_set(WDOOR=openings[0], WWIN=openings[1])
        build_wing_walls(coll)


def arched_door(coll, width=None, spring=None):
    """Kit component: arch-topped plank leaf with strap hinges, pintles, ring pull and clinch nails filling the
    principal arched opening (OPENINGS[0]); width = clear width, spring = springing height above the sill."""
    op = OPENINGS[0]
    if width is not None:
        op["hw"] = width / 2
    if spring is not None:
        op["zs"] = op["z0"] + spring
    build_main_door(coll)


def plank_door(xc=-5.05, width=1.0, height=2.10, frame=0.18, depth=0.20, threshold=0.10):
    """Kit component spec: rectangular plank door (heavy frame, 6-7 planks, 3 strap hinges, latch, stone
    threshold) in a wing wall; returns the spec consumed by stone_wall('wing') and wing_openings()."""
    return dict(xc=xc, hw=width / 2, z0=threshold, z1=threshold + height, fw=frame, depth=depth)


def window(xc=-7.4, width=0.45, height=0.55, sill=1.30, frame=0.07, depth=0.16):
    """Kit component spec: small timber window with a cross mullion, projecting stone sill, timber lintel and a
    dark blocker room behind; returns the spec consumed by stone_wall('wing') and wing_openings()."""
    return dict(xc=xc, hw=width / 2, z0=sill, z1=sill + height, depth=depth, fw=frame)


def wing_openings(coll, door, win):
    """Kit component: builds the door (KEEP_wing_door, _ironwork) and window (KEEP_wing_window) from their specs."""
    kit_set(WDOOR=door, WWIN=win)
    build_wing_door_window(coll, door, win)


def thatch_roof(coll, outline=None, pitch_deg=None, thickness=None, overhang=None, seed=3):
    """Kit component: hipped thatch roof over a rectangular annex outline (x_w, x_e, y_s, y_n): rounded-hip deck,
    stepped straw courses with drift and fall-line straw relief, closed core, D eave roll with a hanging fringe,
    ridge dome with comb and rider log, eave poles, mortar / lead flashings where it meets masonry."""
    kw = {}
    if outline is not None:
        kw.update(WX_W=outline[0], WX_E=outline[1], WY_S=outline[2], WY_N=outline[3])
    if pitch_deg is not None:
        kw["W_PITCH"] = math.radians(pitch_deg)
    if thickness is not None:
        kw["CORE_T"] = thickness
    if overhang is not None:
        kw["W_OVH"] = overhang
    if kw:
        kit_set(**kw)
    build_wing_roof(coll, seed=seed)
    build_wing_ridge(coll)
    build_wing_structure(coll)


def turret(coll, center=None, scale=None, cushion=None):
    """Kit component: engaged round rubble turret (concave profile scaled by 'scale'), corbelled cushion collar
    (spec dict, see CUSH), board drum, bell-cast shingle cap with deck and structure, finial."""
    kw = {}
    if center is not None:
        kw["TUR_C"] = center
    if scale is not None:
        kw["TUR_SCALE"] = scale
    if kw:
        kit_set(**kw)
    if cushion is not None:
        CUSH.update(cushion)
    build_turret(coll)


KEEP_VARIANT = dict(WX_W=-8.3, WY_N=4.4, TUR_C=(-7.14, 2.24), TUR_SCALE=0.8)


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
    for nm in ("KEEP_hall", "KEEP_roof_skirt", "KEEP_tower", "KEEP_wing", "KEEP_turret"):
        c = bpy.data.collections.new(nm)
        root.children.link(c)
        subs[nm] = c
    variant = bool(os.environ.get("KEEP_KIT_VARIANT"))
    if variant:
        # the kit test: a different keep from the same components (0.8x turret, 4.0 x 7.0 m wing)
        kit_set(**KEEP_VARIANT)
        door = plank_door(xc=-4.85)
        win = window(xc=-6.05)
    else:
        door = plank_door()
        win = window()
    kit_set(WDOOR=door, WWIN=win)
    log("hall")
    stone_wall(subs["KEEP_hall"], "hall", height=3.45)
    build_hall_frame(subs["KEEP_hall"])
    arched_door(subs["KEEP_hall"])
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
    stone_wall(subs["KEEP_wing"], "wing", openings=(door, win))
    wing_openings(subs["KEEP_wing"], door, win)
    thatch_roof(subs["KEEP_wing"])
    log("turret")
    turret(subs["KEEP_turret"])
    log("pooled linked duplicates")
    pc = bpy.data.collections.new("KEEP_kit_instances")
    root.children.link(pc)
    realize_placements(pc)
    log("hidden-surface clean-up")
    dv = door_views()
    if os.environ.get("KEEP_FAST"):
        CULL_TARGETS.clear()
    visibility_cull(CULL_TARGETS, near_views(), extra_by_target={"KEEP_door_leaf": dv, "KEEP_wing_door": dv,
                                                                 "KEEP_threshold": dv, "KEEP_hall_posts": dv,
                                                                 "KEEP_hall_post_bases": dv})
    tot = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            tot += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    log(f"objects {len(bpy.data.objects)}  triangles {tot}")
    bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backups next to the deliverable
    out = os.environ.get("KEEP_OUT", OUT)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    if os.path.exists(out + "1"):
        os.remove(out + "1")
    log("saved", out, f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
