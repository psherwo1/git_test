"""Build script: "Stone-and-Timber Tower Windmill" (prefix MILL, collection MILL).

Source of truth for buildings/tower_windmill/tower_windmill.blend.
Run:  /opt/bpyenv/bin/python build_tower_windmill.py

Deterministic: every component draws from its own seeded numpy Generator (crc32 of
its name), so the output is reproducible bit for bit.

Conventions (art bible section 8 / spec section 1)
  metres, Z up, ground Z=0, tower axis at the origin, entrance faces -Y.
  azimuth az (deg) -> horizontal direction (sin az, -cos az); az=0 is -Y (front),
  az=+90 is +X, az=-90 is -X (props side).
"""
import math
import os
import sys
import time
import zlib

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_BLEND = os.environ.get('MILL_OUT') or os.path.join(HERE, 'tower_windmill.blend')
PI = math.pi
D2R = PI / 180.0
T0 = time.time()


def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


SEED_SALT = ""          # kit: a component's `seed` salts every generator it draws from ("" = this mill's seeds)


def RNG(name):
    return np.random.default_rng(zlib.crc32((name + SEED_SALT).encode("utf8")))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# =============================================================================================
# Templates (topology shared by many instances, positions computed per instance with numpy)
# =============================================================================================
def tmpl_box(nx, ny, nz, drop_back=False, yfront=False, drop=()):
    """Welded box grid. Lines per axis: [-h, -(h-r) ... (h-r), h]. Returns topology.
    yfront (with ny=3): y lines are [-h, h-r, h] -> only the front arris is rounded; the open back
    (drop_back) and one short side strip are all that sits in the wall (no buried geometry)."""
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
            if (ax, 0 if side == 0 else 1) in drop:
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
                tflat=np.zeros(0, bool), nv=len(idx), yfront=yfront)


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


def box_lines(n, h, r, grade=0.0):
    t = np.linspace(-1.0, 1.0, n - 2)
    if grade:
        # round 6: grid lines graded toward the arrises (spacing there ~(1-grade) x the mean) so the spall
        # scoops on the dressed arrises resolve on a fine grid while the flat face centre stays coarse
        t = (1 - grade) * t + grade * np.sign(t) * (1 - (1 - np.abs(t)) ** 2)
    inner = t[None, :] * (h - r)[:, None]
    return np.concatenate([-h[:, None], inner, h[:, None]], axis=1)


def rbox(T, h, r):
    """Rounded box positions for N instances. h,r (N,3) half sizes / edge radii."""
    h = np.asarray(h, float)
    r = np.minimum(np.asarray(r, float), h * 0.48)
    N = len(h)
    P = np.empty((N, T["nv"], 3))
    for a in range(3):
        if a == 1 and T.get("yfront"):
            if T.get("yoffs") is not None:
                # round 6: extra side-face rows behind the front arris (spall scoops resolve on the sides too)
                yo_ = [np.minimum(h[:, 1] - np.minimum(o_, 1.6 * h[:, 1]), h[:, 1] - r[:, 1] - 0.002 * (q_ + 1))
                       for q_, o_ in enumerate(T["yoffs"])]
                L = np.stack([-h[:, 1]] + yo_[::-1] + [h[:, 1] - r[:, 1], h[:, 1]], 1)
                L[:, 1:-2] = np.maximum(L[:, 1:-2], -h[:, 1:2] + 0.002)
            else:
                L = np.stack([-h[:, 1], h[:, 1] - r[:, 1], h[:, 1]], 1)
        else:
            L = box_lines(T["n"][a], h[:, a], r[:, a], T.get("grade", 0.0))
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


def lathe(prof_rz, m, caps=True, T_cache={}, open_base=False):
    """prof_rz (N,n,2) (radius, z). Returns local verts (N,nv,3) and template.
    Profile points on the axis (radius 0) become a single apex vertex (no degenerate zero-area ring / fan).
    open_base: the first end is seated on (or sunk into) a surface and is not closed."""
    prof_rz = np.asarray(prof_rz, float)
    ax0 = bool((np.abs(prof_rz[:, 0, 0]) < 1e-7).all())
    ax1 = bool((np.abs(prof_rz[:, -1, 0]) < 1e-7).all())
    z0 = prof_rz[:, 0, 1].copy()
    z1 = prof_rz[:, -1, 1].copy()
    pr = prof_rz[:, (1 if ax0 else 0):(prof_rz.shape[1] - 1 if ax1 else prof_rz.shape[1])]
    N, n = pr.shape[:2]
    a = np.linspace(0, 2 * PI, m, endpoint=False)
    P = np.empty((N, n, m, 3))
    P[..., 0] = pr[..., 0:1] * np.cos(a)
    P[..., 1] = pr[..., 0:1] * np.sin(a)
    P[..., 2] = pr[..., 1:2]
    P = P.reshape(N, n * m, 3)
    c0 = caps and not open_base
    c1 = caps
    key = (n, m, c0, c1)
    extra = []
    if c0:
        e = P[:, :m].mean(1, keepdims=True)
        if ax0:
            e[:, 0, 2] = z0
        extra.append(e)
    if c1:
        e = P[:, (n - 1) * m:].mean(1, keepdims=True)
        if ax1:
            e[:, 0, 2] = z1
        extra.append(e)
    if extra:
        P = np.concatenate([P] + extra, axis=1)
    if key not in T_cache:
        T = tmpl_rings(n, m, closed_path=False, cap0=c0, cap1=c1)
        T_cache[key] = orient(T, P[0])
    return P, T_cache[key]


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
             "M_roof_shingle", "M_roof_shake", "M_iron", "M_lead", "M_moss", "M_earth"]


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


def set_mask(me, V, R, G, moss0=0.0, zoff=0.0):
    """Producer note 9: CORNER colour attribute 'Mask' (active + default). R per-piece random, G per-piece wear,
    B moss / dirt / damp per vertex: high near the ground, on upward-facing faces and on north (+Y) faces,
    lower high up on vertical faces. A = 1."""
    nl = len(me.loops)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    npg = len(me.polygons)
    lt = np.empty(npg, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    pn = np.empty(npg * 3, np.float32)
    me.polygons.foreach_get("normal", pn)
    ln = np.repeat(pn.reshape(-1, 3), lt, axis=0)
    z = V[lv, 2] + zoff
    up = np.clip(ln[:, 2], 0, 1)
    b = 0.85 * np.clip(1 - z / 1.2, 0, 1) ** 1.5 + 0.35 * up ** 2 + 0.15 * np.clip(ln[:, 1], 0, 1) + moss0
    b *= 1 - 0.25 * np.clip((z - 3.0) / 8.0, 0, 1) * (1 - up)
    col = np.stack([R[lv], G[lv], np.clip(b, 0, 1), np.ones(nl)], 1).astype(np.float32)
    at = me.color_attributes.new("Mask", "BYTE_COLOR", "CORNER")
    at.data.foreach_set("color_srgb", col.ravel())
    me.color_attributes.active_color_name = "Mask"
    me.color_attributes.default_color_name = "Mask"


def sliver_counts(me):
    """Producer note 1 test (director round 5): loop triangles with altitude 2*area/longest edge < 0.1 mm, and
    polygons with area < 1e-8 m2, judged on the float32 positions the mesh stores."""
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
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
    return alt < 1e-4, int((pa < 1e-8).sum())


def nanite_clean(me, passes=4):
    """Round 6 (producer note 1): weld coincident vertices (remove_doubles 0.2 mm) and dissolve degenerate
    geometry (dissolve_degenerate 0.1 mm) so no needle triangle or zero-area polygon survives; any needle left
    after that (a long thin triangle whose short altitude spans no short edge) is collapsed onto its
    longest edge. Returns (altitude count, area count) after cleaning: both must be 0."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-4)
    for _ in range(passes):
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-4)
        bm.faces.ensure_lookup_table()
        # remaining needles: faces with a vertex within 0.1 mm of the line through its neighbours, or a
        # triangulation needle -> collapse that vertex's shortest edge
        bad = []
        for f in bm.faces:
            if f.calc_area() < 1e-8:
                bad.append(min(f.edges, key=lambda e: e.calc_length()))
                continue
            for l in f.loops:
                a, b, c = l.link_loop_prev.vert.co, l.vert.co, l.link_loop_next.vert.co
                ab, ac = c - a, b - a
                L = ab.length
                if L < 1e-9:
                    continue
                if ab.cross(ac).length / L < 1e-4:
                    e1, e2 = l.edge, l.link_loop_prev.edge
                    bad.append(e1 if e1.calc_length() < e2.calc_length() else e2)
                    break
        if not bad:
            break
        bad = list({e.index: e for e in bad if e.is_valid}.values())
        bmesh.ops.collapse(bm, edges=bad, uvs=True)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-4)
    # a quad / n-gon whose triangulation makes a needle: triangulate it with the beauty method
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-4)
    bm.to_mesh(me)
    bm.free()
    me.update()
    m, na = sliver_counts(me)
    if m.any():
        # last resort: triangulate the offending polygons (beauty) so their split is not along a needle
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        lp = np.empty(len(me.loop_triangles), np.int32)
        me.loop_triangles.foreach_get("polygon_index", lp)
        fs = [bm.faces[i] for i in sorted(set(lp[m].tolist())) if len(bm.faces[i].verts) > 3]
        if fs:
            bmesh.ops.triangulate(bm, faces=fs, quad_method="BEAUTY", ngon_method="BEAUTY")
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-4)
        bm.to_mesh(me)
        bm.free()
        me.update()
        m, na = sliver_counts(me)
    return int(m.sum()), na


class Part:
    registry = []

    def __init__(self, name, mats, angle=33.0, wear=0.35, moss=0.0):
        self.name = name
        self.wear0 = wear           # Mask G baseline (per-piece wear, jittered per piece)
        self.moss0 = moss           # Mask B bias for this part (roof butts, ground pieces)
        self.R, self.G = [], []     # per-vertex Mask R (piece random) and G (piece wear)
        self.rng_mask = RNG("mask_" + name)
        self.mats = list(mats)
        self.angle = angle          # smooth-by-angle threshold (deg): sharper dihedrals get split normals
        self.V = []
        self.Q, self.QM, self.QS, self.QU = [], [], [], []
        self.Tr, self.TM, self.TS, self.TU = [], [], [], []
        self.nv = 0
        self.calls = []
        self.rng_uv = RNG("uv_" + name)
        Part.registry.append(self)

    def add(self, Vw, T, Pl=None, mat=None, smooth="bevel", uv_rand=True, wear=None):
        """Vw (N,nv,3) world positions; T template; Pl (N,nv,3) local positions for UVs.
        mat: slot name or index. smooth: 'all' | 'none' | 'bevel' (flat main faces, smooth bevels).
        wear: Mask G for these pieces (scalar or (N,)); default = the part's baseline +- 0.2 per piece."""
        Vw = np.asarray(Vw, float)
        if Vw.ndim == 2:
            Vw = Vw[None]
        N, nv = Vw.shape[:2]
        assert nv == T["nv"], (self.name, nv, T["nv"])
        Pl = Vw if Pl is None else (Pl[None] if Pl.ndim == 2 else Pl)
        mi = 0 if mat is None else (self.mats.index(mat) if isinstance(mat, str) else int(mat))
        if N > 0 and ("idx" in T or "n_rings" in T) and not T.get("no_auto"):
            # round 4: every solid piece faces OUTWARD in world space. Several placement maps (drum / opening
            # mappings) are mirror maps, which used to turn whole walls inside out: check the first instance's
            # signed volume in world space and flip the winding if needed.
            P0 = Vw[0] - Vw[0].mean(0)
            q = T["quads"]
            vol = 0.0
            if len(q):
                A_, B_, C_, D_ = P0[q[:, 0]], P0[q[:, 1]], P0[q[:, 2]], P0[q[:, 3]]
                vol += (np.einsum("ij,ij->i", A_, np.cross(B_, C_)) + np.einsum("ij,ij->i", A_, np.cross(C_, D_))).sum()
            if len(T["tris"]):
                t_ = T["tris"]
                vol += np.einsum("ij,ij->i", P0[t_[:, 0]], np.cross(P0[t_[:, 1]], P0[t_[:, 2]])).sum()
            if vol < 0:
                T = flip_tmpl(T)
                self.n_flipped = getattr(self, "n_flipped", 0) + N
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
        # Mask (producer note 9): R constant per piece (one instance = one stone / shingle / plank), G wear
        r_ = self.rng_mask.random(N)
        if wear is None:
            g_ = np.clip(self.wear0 + self.rng_mask.uniform(-0.2, 0.2, N), 0, 1)
        else:
            g_ = np.clip(np.broadcast_to(np.asarray(wear, float), (N,)) + self.rng_mask.uniform(-0.05, 0.05, N), 0, 1)
        self.R.append(np.repeat(r_, nv))
        self.G.append(np.repeat(g_, nv))
        self.nv += N * nv
        self.calls.append((N, nv, len(T["quads"]), len(T["tris"])))

    def filter_instances(self, keep_fn):
        """Drop whole instances (e.g. shingles completely covered by a capping). keep_fn(V (N,nv,3)) -> bool (N,)."""
        V2, Q2, QM2, QS2, QU2, T2, TM2, TS2, TU2, calls2 = [], [], [], [], [], [], [], [], [], []
        R2, G2 = [], []
        qi = ti = 0
        vbase_old = 0
        vbase_new = 0
        removed = 0
        for (N, nv, nq, nt), V in zip(self.calls, self.V):
            Vi = V.reshape(N, nv, 3)
            keep = np.asarray(keep_fn(Vi), bool)
            removed += int((~keep).sum())
            k = int(keep.sum())
            if nq:
                Q = self.Q[qi].reshape(N, nq, 4) - vbase_old
                Q = Q[keep] - (np.arange(N)[keep] * nv)[:, None, None] + (np.arange(k) * nv)[:, None, None]
                Q2.append((Q + vbase_new).reshape(-1, 4))
                QM2.append(self.QM[qi].reshape(N, nq)[keep].ravel())
                QS2.append(self.QS[qi].reshape(N, nq)[keep].ravel())
                QU2.append(self.QU[qi].reshape(N, nq, 4, 2)[keep].reshape(-1, 4, 2))
                qi += 1
            if nt:
                Tt = self.Tr[ti].reshape(N, nt, 3) - vbase_old
                Tt = Tt[keep] - (np.arange(N)[keep] * nv)[:, None, None] + (np.arange(k) * nv)[:, None, None]
                T2.append((Tt + vbase_new).reshape(-1, 3))
                TM2.append(self.TM[ti].reshape(N, nt)[keep].ravel())
                TS2.append(self.TS[ti].reshape(N, nt)[keep].ravel())
                TU2.append(self.TU[ti].reshape(N, nt, 3, 2)[keep].reshape(-1, 3, 2))
                ti += 1
            V2.append(Vi[keep].reshape(-1, 3))
            R2.append(self.R[len(V2) - 1].reshape(N, nv)[keep].ravel())
            G2.append(self.G[len(V2) - 1].reshape(N, nv)[keep].ravel())
            calls2.append((k, nv, nq, nt))
            vbase_old += N * nv
            vbase_new += k * nv
        self.V, self.Q, self.QM, self.QS, self.QU = V2, Q2, QM2, QS2, QU2
        self.Tr, self.TM, self.TS, self.TU = T2, TM2, TS2, TU2
        self.calls, self.nv = calls2, vbase_new
        self.R, self.G = R2, G2
        return removed

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
        V[:, 2] = np.maximum(V[:, 2], getattr(self, "zmin", 0.0))  # anything buried is cut flat at the ground
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        Tt = np.concatenate(self.Tr) if self.Tr else np.zeros((0, 3), np.int64)
        QU = np.concatenate(self.QU).reshape(-1, 4, 2) if self.QU else np.zeros((0, 4, 2))
        TU = np.concatenate(self.TU).reshape(-1, 3, 2) if self.TU else np.zeros((0, 3, 2))
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32)
        # Nanite hygiene: no zero-area / degenerate faces. Faces collapsed by clamps and cuts are dropped; a quad
        # with one collapsed half becomes the triangle of its other half.
        eps = 2e-8
        V32 = V.astype(np.float32)          # judge areas on the float32 positions the mesh actually stores

        def tri_area(a, b, c):
            return 0.5 * np.linalg.norm(np.cross(V32[b] - V32[a], V32[c] - V32[a]).astype(np.float64), axis=1)
        a1 = tri_area(Q[:, 0], Q[:, 1], Q[:, 2])
        a2 = tri_area(Q[:, 0], Q[:, 2], Q[:, 3])
        b1 = tri_area(Q[:, 0], Q[:, 1], Q[:, 3])
        b2 = tri_area(Q[:, 1], Q[:, 2], Q[:, 3])
        # a quad is degenerate if any of its 4 corner triangles collapses (coincident corners / collinear edge)
        good_q = (a1 > eps) & (a2 > eps) & (b1 > eps) & (b2 > eps)
        # faces lying entirely on the ground cut (buried bottoms flattened by the clamp) can never be seen
        zc_ = getattr(self, "zmin", 0.0) + 1e-5
        on_g = (V[Q, 2] <= zc_).all(1)
        tris_new, tu_new, tm_new = [], [], []
        for corner in range(4):
            # quad -> triangle dropping one collapsed corner (keep the three others), if that triangle has area
            keep_c = [c_ for c_ in range(4) if c_ != corner]
            cand = ~good_q & ~on_g & (tri_area(*[Q[:, c_] for c_ in keep_c]) > eps)
            sel = cand & np.all([~np.isnan(a1)], 0)
            if corner > 0:
                sel &= ~done
            done = sel if corner == 0 else (done | sel)
            if sel.any():
                tris_new.append(Q[sel][:, keep_c])
                tu_new.append(QU[sel][:, keep_c])
                tm_new.append(QM[sel])
        good_t = tri_area(Tt[:, 0], Tt[:, 1], Tt[:, 2]) > eps if len(Tt) else np.zeros(0, bool)
        good_q &= ~on_g
        if len(Tt):
            good_t &= ~(V[Tt, 2] <= zc_).all(1)
        self.n_ground = int(on_g.sum())
        self.n_degenerate = int((~good_q).sum() + (~good_t).sum())
        Q, QU, QM = Q[good_q], QU[good_q], QM[good_q]
        Tt, TU, TM = Tt[good_t], TU[good_t], TM[good_t]
        if tris_new:
            Tt = np.concatenate([Tt] + tris_new)
            TU = np.concatenate([TU] + tu_new)
            TM = np.concatenate([TM] + tm_new)
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
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", np.concatenate([QU.reshape(-1, 2), TU.reshape(-1, 2)]).astype(np.float32).ravel())
        mats = np.concatenate([QM, TM]).astype(np.int32)
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
        set_mask(me, V, np.concatenate(self.R), np.concatenate(self.G), self.moss0, getattr(self, "zref", 0.0))
        self.n_alt, self.n_area = nanite_clean(me) if not os.environ.get("MILL_NOCLEAN") else (-1, -1)
        if getattr(self, "mesh_only", False):
            return me
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


# =============================================================================================
# Shared-mesh pools (producer note 3): a small pool of variant meshes per repeated element, placed as
# linked-duplicate mesh objects; per-placement jitter lives in the object transform.
# =============================================================================================
POOLS = {}          # key -> Part (mesh_only)
PLACEMENTS = []     # (object name, pool key, 4x4 matrix, leaned)


def pool_part(key, mats):
    if key not in POOLS:
        p = Part("MILL_pool_" + key, mats)
        p.mesh_only = True
        p.zref = 2.6 if key.startswith("baluster") else (4.3 if key.startswith("corbel") else 11.0)
        POOLS[key] = p
    return POOLS[key]


def place_instance(name, key, R, t, leaned=False):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    PLACEMENTS.append((name, key, M, leaned))


BOLT_POOL = [(0.016, 0.012), (0.018, 0.013), (0.020, 0.014), (0.020, 0.0145), (0.026, 0.020), (0.026, 0.019)]


def bolt_pool():
    """Six hex bolt-head / nut variants (radius, height; two chamfer styles), built once."""
    for i, (rad, hgt) in enumerate(BOLT_POOL):
        key = "bolt_hex_%d" % i
        if key in POOLS:
            continue
        p = pool_part(key, ["M_iron"])
        ch = 0.75 if i % 2 == 0 else 0.62
        prof = np.array([(0.0, -0.002), (rad, -0.002), (rad, hgt * 0.7), (rad * ch, hgt), (0.0, hgt)])
        P, T = lathe(prof[None], 6, caps=True)
        p.add(P, T, mat="M_iron", smooth="none", wear=0.4)


def inst_bolts(prefix, centers, normals, rad, leaned=True, rng=None):
    """Place pooled hex heads (world centres + outward normals, pre-lean) as linked duplicates."""
    bolt_pool()
    centers = np.atleast_2d(centers)
    Rs = bolt_frames(normals)
    cand = [i for i, (r_, _) in enumerate(BOLT_POOL) if abs(r_ - rad) < 0.0025] or [2]
    for j in range(len(centers)):
        r_ = rng if rng is not None else RNG_BOLT
        k = cand[int(r_.integers(0, len(cand)))]
        ang = r_.uniform(0, PI / 3)
        place_instance("%s_%03d" % (prefix, len([q for q in PLACEMENTS if q[0].startswith(prefix)])),
                       "bolt_hex_%d" % k, Rs[j] @ rotm([0, 0, 1], [ang])[0], centers[j], leaned)


# =============================================================================================
# Shared templates
# =============================================================================================
T_RUB = tmpl_box(9, 4, 7, drop_back=True)     # rubble stones (back face culled, buried in mortar)
T_RUB3 = tmpl_box(9, 3, 7, drop_back=True, yfront=True)    # wall stones: exposed face + sides to the mortar only
# below eye level (top < 1.5 m) a stone's downward-facing side can never be seen by a standing viewer: dropped
T_RUB3_NB = tmpl_box(9, 3, 7, drop_back=True, yfront=True, drop={(2, 0)})
T_RUBF_NB = tmpl_box(7, 4, 5, drop={(2, 0)})                # ground rubble: no face under the ground
T_SHK_ST = tmpl_box(6, 4, 4, drop={(1, 1), (0, 1)})        # starter shingle: top and head wholly under course 1
# eye-level wall stones (close-up zone): denser face grid for the pillowing / facets / fracture outlines
T_RUB3_HI = tmpl_box(13, 3, 9, drop_back=True, yfront=True)
T_RUB3_HI_NB = tmpl_box(13, 3, 9, drop_back=True, yfront=True, drop={(2, 0)})
T_RUB3_XHI = tmpl_box(17, 3, 11, drop_back=True, yfront=True)           # actor-height band (< 2.6 m)
T_RUB3_XHI_NB = tmpl_box(17, 3, 11, drop_back=True, yfront=True, drop={(2, 0)})
EYE_XHI = 2.6
EYE_HI = 4.3                 # the whole drum is the hero surface (every view): dense faces up to the cornice


def wall_stone_tmpl(zc, H, base_T):
    """Per-stone template: open back always; no soffit below eye height; denser face in the eye-level zone."""
    if base_T is not T_RUB3:
        return [base_T] * len(zc)
    out = []
    for z, hh in zip(zc, H):
        low = z - hh / 2 + 0.01 < EYE_SOFFIT
        hi = z < EYE_HI
        if z < EYE_XHI:
            out.append(T_RUB3_XHI_NB if low else T_RUB3_XHI)
        else:
            out.append((T_RUB3_HI_NB if low else T_RUB3_HI) if hi else (T_RUB3_NB if low else T_RUB3))
    return out


def stones_by_tmpl(rng, L, H, D, style, tmpls):
    """stone_local for groups of stones sharing a template. Returns list of (index array, P, T)."""
    groups = []
    ids = {}
    for i, T in enumerate(tmpls):
        ids.setdefault(id(T), (T, []))[1].append(i)
    for key in sorted(ids, key=lambda k: ids[k][1][0]):
        T, ix = ids[key]
        ix = np.array(ix)
        P, _ = stone_local(rng, L[ix], H[ix], D[ix], style, T=T)
        groups.append((ix, P, T))
    return groups
T_FLAG_O = tmpl_box(7, 3, 5, drop_back=True, yfront=True)  # floor flags: no bed face, one side strip
T_BLK_PL = tmpl_box(4, 4, 4, drop={(2, 0), (1, 1)})         # baluster plinth: no bed, no back (against the band)
T_BLK_AB = tmpl_box(4, 4, 4, drop={(2, 1), (1, 1)})         # baluster abacus: no head, no back
T_BRD_O3 = tmpl_box(10, 3, 5, drop_back=True, yfront=True)  # cladding board: open back, one side strip
T_DRS3 = tmpl_box(8, 3, 6, drop_back=True, yfront=True)    # wall-set dressed stones (open back)
T_DRSH3 = tmpl_box(11, 3, 10, drop_back=True, yfront=True)  # hero dressed stones (open back)
# round 5: crisp dressed work - denser front grids so straight arrises, flat faces and crisp spall scars resolve
T_DRS3X = tmpl_box(17, 6, 15, drop_back=True, yfront=True)
T_DRSH3X = tmpl_box(27, 6, 25, drop_back=True, yfront=True)
T_DRS3X["grade"] = 0.6
T_DRSH3X["grade"] = 0.65
T_DRS3X["yoffs"] = T_DRSH3X["yoffs"] = (0.016, 0.026, 0.040)
T_DRS3L = tmpl_box(13, 3, 11, drop_back=True, yfront=True)   # band / frieze ashlar (above the actor zone)
T_DRS3L["grade"] = 0.45
T_SHK_O = tmpl_box(6, 3, 4, drop_back=True, yfront=True, drop={(0, 1)})   # shingle: no bed face, no covered head end
T_SHK2_O = tmpl_box(10, 3, 8, drop_back=True, yfront=True, drop={(0, 1)})  # split shake: no bed face, no covered head
T_BRD_O3T = tmpl_box(10, 3, 5, drop_back=True, yfront=True, drop={(0, 1)})  # board whose top end is covered
T_BRD_O3B = tmpl_box(10, 3, 5, drop_back=True, yfront=True, drop={(0, 0)})  # ... bottom end covered
T_BRD_O3TB = tmpl_box(10, 3, 5, drop_back=True, yfront=True, drop={(0, 0), (0, 1)})
T_BRD_O = tmpl_box(10, 4, 5, drop_back=True)  # cladding board without its (inner) back face
T_BRD_OT = tmpl_box(10, 4, 5, drop_back=True, drop={(0, 1)})  # valance board: no back, no top end (under the deck)
T_RUBF = tmpl_box(7, 4, 5)                    # free-standing rubble / boulders
EYE_SOFFIT = 1.55                             # a stone soffit below 1.55 m faces the ground: from eye height (1.65 m) and above it is never seen
T_PIN = tmpl_box(6, 3, 5, drop_back=True, yfront=True)     # pinning stones (open back)
T_PIN_NB = tmpl_box(6, 3, 5, drop_back=True, yfront=True, drop={(2, 0)})   # ... below eye level: no soffit
T_DRS = tmpl_box(8, 4, 6)                     # dressed blocks
T_DRSH = tmpl_box(11, 4, 10)                  # hero dressed blocks (door surround, coping): room for spalls
T_BLK = tmpl_box(4, 4, 4)                     # small chamfered blocks / timbers
T_PLK = tmpl_box(9, 4, 4)                     # long members (bendable along x)
T_SHK = tmpl_box(6, 4, 4)                     # shingles (x = length)
T_SHK2 = tmpl_box(8, 4, 6)                    # split shakes (tapered, cupped, ragged)
T_BRD = tmpl_box(10, 4, 5)                    # long boards (x length, z width)
T_PLK_NI = tmpl_box(9, 4, 4, drop={(2, 0)})   # tower frame member: no inner face (against the board backs)
T_PLK_DB = tmpl_box(9, 4, 4, drop={(1, 0), (2, 0)})   # drip board: no underside (on the rail), no back edge
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


def hewn_tmpl(nx, drop=()):
    key = (nx, tuple(sorted(drop)))
    if key not in _T_HEWN:
        _T_HEWN[key] = tmpl_box(nx, 7, 7, drop=set(drop))
    return _T_HEWN[key]


def hewn_beam(rng, L, w, d, nx=None, chamfer=(0.015, 0.03), adze=(0.003, 0.005), n_scallop=(2, 3),
              checks=(1, 2), check_len=(0.5, 1.5), end_split=1, faces_check=(2, 1), drop=()):
    """One hewn timber, local x = length (centred), y = width, z = depth. Returns (P (1,nv,3), T).
    - chamfer radius varies along the length within `chamfer` (worn arrises),
    - every long face carries 2-3 shallow concave adze scallops (`adze` deep),
    - `checks`: 1-2 long checks (1 cm wide V, 1-1.5 cm deep) on the faces in `faces_check`
      (axis index 1 = +-y faces, 2 = +-z faces),
    - end_split: +1 / -1 / 0 -> a radial split in the end grain at that end."""
    if nx is None:
        nx = int(np.clip(L / 0.12, 8, 60))
    T = hewn_tmpl(nx, drop)
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


def hewn_between(part, mat, a, b, w, d, up, rng, chamfer=(0.012, 0.022), adze=(0.003, 0.005), checks=(0, 1),
                 check_len=(0.3, 0.8), end_split=1, bow=0.0, nx=None, drop=()):
    """Hewn timber (hewn_beam) from point a to b (world): w across (normal to `up`), d along `up`."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    xa = (b - a) / L
    ya = np.cross(np.asarray(up, float), xa)
    ya /= np.linalg.norm(ya)
    za = np.cross(xa, ya)
    P, T = hewn_beam(rng, L, w, d, nx=nx, chamfer=chamfer, adze=adze, checks=checks, check_len=check_len,
                     end_split=end_split, drop=drop)
    if bow:
        u = P[:, :, 0] / (L / 2)
        bw = rng.uniform(-bow, bow, 2)
        P[:, :, 1] += bw[0] * (1 - u ** 2)
        P[:, :, 2] += bw[1] * (1 - u ** 2)
    W = P @ np.stack([xa, ya, za], 1).T + (a + b) / 2
    part.add(W, T, Pl=P[0], mat=mat, smooth="bevel")
    return W


# =============================================================================================
# Stones
# =============================================================================================
STYLE = {
    # rounding (frac of min dim, min, max), outline noise, face noise (m), pillow range (m), taper, shear
    # cuts = (min, max) straight fracture cuts on the outline; facets = (min, max) tilted face planes;
    # spall = (min, max) edge spalls (dressed work)
    "rubble": dict(avar=(0.003, 0.015, 0.8), rr=(0.08, 0.008, 0.013), ry=0.009, nxz=0.045, ny=0.006, pil=(0.002, 0.009), tap=0.07,
                   shear=0.06, T=T_RUB3, cuts=(2, 4), cutk=(0.8, 0.94), facets=(1, 2), hf=0.003, ftilt=0.25,
                   fshave=(0.008, 0.02)),
    "pin": dict(avar=(0.002, 0.008, 0.8), rr=(0.12, 0.004, 0.008), ry=0.006, nxz=0.05, ny=0.004, pil=(0.0, 0.004), tap=0.12,
                shear=0.08, T=T_PIN, cuts=(1, 3), cutk=(0.8, 0.92), facets=(0, 1), hf=0.0015, ftilt=0.3,
                fshave=(0.003, 0.008)),
    # round 6: footing stones split like the drum rubble (z01): flat beds (low outline noise), straight
    # fracture cuts that only take the corners, 0.3-1.5 cm arris variation with 1-2 crisp broken edges, and
    # low-tilt face facets (no melted, bevelled top arris)
    "footing": dict(avar=(0.003, 0.015, 0.7), rr=(0.09, 0.01, 0.015), ry=0.010, nxz=0.03, ny=0.005, pil=(0.002, 0.008), tap=0.06,
                    shear=0.05, T=T_RUB3, cuts=(2, 4), cutk=(0.82, 0.95), facets=(1, 2), hf=0.0025, ftilt=0.22,
                    fshave=(0.004, 0.012), ncrisp=(1, 2)),
    "boulder": dict(rr=(0.2, 0.012, 0.05), ry=0.2, nxz=0.12, ny=0.012, pil=(0.0, 0.01), tap=0.2,
                    shear=0.15, T=T_RUBF, cuts=(3, 4), facets=(1, 2), hf=0.003),
    # round 5: dressed / hero / ashlar are CRISP: straight edges (outline noise <= 2 mm), flat faces (+-1 mm),
    # a 1 cm chamfer, and the wear concentrated in crisp spalls (sramp = 4 mm ramp at the scar ends)
    "dressed": dict(rr=(0.1, 0.009, 0.010), ry=0.010, nxz=0.003, ny=0.0007, pil=(0.0, 0.0012), tap=0.004,
                    shear=0.004, T=T_DRS3X, spall=(2, 3), sramp=0.004),
    "hero": dict(rr=(0.1, 0.010, 0.010), ry=0.010, nxz=0.002, ny=0.0006, pil=(0.0, 0.001), tap=0.003,
                 shear=0.003, T=T_DRSH3X, spall=(2, 4), sramp=0.004),
    "ashlar": dict(rr=(0.1, 0.008, 0.012), ry=0.010, nxz=0.008, ny=0.0012, pil=(0.0, 0.002), tap=0.01,
                   shear=0.008, T=T_DRS3L, spall=(1, 2), facets=(0, 1), sramp=0.005),
    "flag": dict(rr=(0.2, 0.022, 0.035), ry=0.028, nxz=0.07, ny=0.003, pil=(0.0, 0.004), tap=0.12,
                 shear=0.08, T=T_RUBF, cuts=(2, 3)),
}


def rbox_pv(T, h, rv):
    """Rounded box with a PER-VERTEX arris radius rv (N, nv, 3): every edge of a stone can carry its own wear."""
    h = np.asarray(h, float)
    rv = np.minimum(rv, h[:, None, :] * 0.48)
    N = len(h)
    idx = T["idx"]
    P = np.empty((N, T["nv"], 3))
    for a in range(3):
        n = T["n"][a]
        ia = idx[:, a]
        if a == 1 and T.get("yfront"):
            pos = np.where(ia == 0, -h[:, None, 1], np.where(ia == 1, h[:, None, 1] - rv[:, :, 1], h[:, None, 1]))
        else:
            t = -1 + 2 * (ia - 1) / max(n - 3, 1)
            pos = np.where(ia == 0, -h[:, None, a], np.where(ia == n - 1, h[:, None, a],
                                                             t[None] * (h[:, None, a] - rv[:, :, a])))
        P[:, :, a] = pos
    lim = h[:, None, :] - rv
    inner = np.clip(P, -lim, lim)
    d = (P - inner) / rv
    nr = np.linalg.norm(d, axis=2, keepdims=True)
    dn = np.where(nr > 1e-9, d / np.maximum(nr, 1e-9), 0.0)
    return inner + dn * rv


def edge_radii(rng, T, N, rmin, rmax, ry_k, D, ncrisp=(1, 2)):
    """Per-vertex arris radii: each of a stone's four face edges gets its own wear in [rmin, rmax], and 1-2
    edges per stone are crisp broken edges (<= 3 mm)."""
    re = rng.uniform(rmin, rmax, (N, 4))
    nc = rng.integers(ncrisp[0], ncrisp[1] + 1, N)
    for k in range(ncrisp[1]):
        e = rng.integers(0, 4, N)
        sel = k < nc
        re[np.arange(N)[sel], e[sel]] = rng.uniform(0.0015, 0.003, int(sel.sum()))
    idx = T["idx"]
    tx = idx[:, 0] / (T["n"][0] - 1) * 2 - 1
    tz = idx[:, 2] / (T["n"][2] - 1) * 2 - 1
    rx = np.where(tx[None] < 0, re[:, 0:1], re[:, 1:2])
    rz = np.where(tz[None] < 0, re[:, 2:3], re[:, 3:4])
    ry = np.where(np.abs(tx)[None] >= np.abs(tz)[None], rx, rz) * ry_k
    ry = np.minimum(ry, 0.45 * np.asarray(D, float)[:, None])
    return np.stack([rx, ry, rz], 2)


def conchoidal(rng, P, T, frac=0.3, dep=(0.003, 0.008)):
    """Shallow conchoidal scoop (3-8 mm, crisp rim) on the front face of ~30 % of the stones (in place)."""
    N = len(P)
    front = T["idx"][:, 1] == T["n"][1] - 1
    sel = np.nonzero(rng.random(N) < frac)[0]
    for i in sel:
        F = P[i, front]
        lo, hi = F[:, [0, 2]].min(0), F[:, [0, 2]].max(0)
        c = lo + (hi - lo) * rng.uniform(0.2, 0.8, 2)
        R = min(rng.uniform(0.04, 0.10), 0.6 * float((hi - lo).min()))
        rho = np.hypot(F[:, 0] - c[0], F[:, 2] - c[1]) / max(R, 1e-3)
        d = rng.uniform(*dep) * np.clip(1 - rho ** 2, 0, 1)
        P[i, np.nonzero(front)[0], 1] -= d
    return len(sel)


def stone_local(rng, L, H, D, style, rot_deg=(2.0, 0.8, 1.1), spall=None, T=None):
    """Irregular stone, local x = length, y = outward (front face at y=0), z = up. (N,nv,3).
    Split-stone language: angular outline from straight fracture cuts, a flat bed face with 1-2 tilted
    facets (pillow <= 1 cm), small arris radius. Dressed work: flat faces, 1 cm chamfer, edge spalls."""
    st = STYLE[style]
    T = st["T"] if T is None else T
    L, H, D = (np.asarray(v, float) for v in (L, H, D))
    N = len(L)
    h = np.stack([L / 2, D / 2, H / 2], 1)
    mn = np.minimum(L, H)
    rxz = np.clip(st["rr"][0] * mn, st["rr"][1], st["rr"][2])
    ry = np.minimum(st["ry"], 0.45 * D) if st["ry"] < 0.15 else st["ry"] * np.minimum(mn, D)
    r = np.stack([rxz, np.broadcast_to(ry, (N,)), rxz], 1)
    if st.get("avar"):
        # round 4: the arris varies per edge (0.3-1.5 cm) with 1-2 crisp broken edges per stone
        a0, a1, kry = st["avar"]
        P = rbox_pv(T, h, edge_radii(rng, T, N, a0, a1, kry, D))
    else:
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
        # round 6: spalls as the intersection of 3 tilted fracture planes (director r5 #5): two planes meeting
        # along the arris tilt the scar so its depth (1-3 cm at the deepest point) falls linearly to 0 at both
        # ends, a third plane skews it toward the face or the side -> an irregular, tapering, crisp-rimmed
        # chip with no rectangular corner. Each vertex inside all three half-spaces is pushed back along its OWN
        # face normal (front -> -y, side -> into the side; blended on the chamfer) onto the nearest plane, so
        # nothing ever moves outward or folds over its neighbour (no lips, tabs or flaps).
        s0, s1 = sp
        nsp = rng.integers(s0, s1 + 1, N)
        yh = np.array([0, 1.0, 0])
        ar = np.arange(N)
        for k in range(s1):
            side = rng.integers(0, 4, N)            # 0:+x 1:-x 2:+z 3:-z
            dax = np.where(side < 2, 0, 2)
            sgn = np.where(side % 2 == 0, 1.0, -1.0)
            aax = np.where(side < 2, 2, 0)
            dvec = np.zeros((N, 3))
            dvec[ar, dax] = sgn
            avec = np.zeros((N, 3))
            avec[ar, aax] = 1.0
            kk = rng.uniform(0.75, 1.5, N)
            nrm = unit(dvec + yh * kk[:, None])
            bvec = unit(np.cross(nrm, avec))
            ha = h[ar, aax]
            hd = h[ar, dax]
            dep = rng.uniform(0.012, 0.03, N)
            ca_ = rng.uniform(-0.7, 0.7, N) * ha
            hl1 = np.minimum(rng.uniform(0.035, 0.08, N), 0.6 * ha)
            hl2 = np.minimum(hl1 * rng.uniform(0.6, 1.5, N), 0.6 * ha)
            edge = dvec * hd[:, None] + yh * h[:, 1:2]
            c0 = edge + avec * ca_[:, None] - nrm * dep[:, None]
            n1 = unit(nrm + avec * (dep / hl1)[:, None])
            n2 = unit(nrm - avec * (dep / hl2)[:, None])
            n3 = unit(nrm + bvec * rng.uniform(-0.45, 0.45, N)[:, None] + avec * rng.uniform(-0.15, 0.15, N)[:, None])
            c3 = c0 - nrm * (rng.uniform(-0.25, 0.1, N) * dep)[:, None]
            on = (k < nsp)[:, None]
            ds = np.abs(hd[:, None] - sgn[:, None] * np.take_along_axis(P, dax[:, None, None].repeat(P.shape[1], 1), 2)[:, :, 0])
            df = np.abs(h[:, 1:2] - P[:, :, 1])
            ws, wf = 1.0 / (ds + 0.002), 1.0 / (df + 0.002)
            m = unit((ws[:, :, None] * dvec[:, None, :] + wf[:, :, None] * yh) / (ws + wf)[:, :, None])
            fs, ts = [], []
            for nn, cc in ((n1, c0), (n2, c0), (n3, c3)):
                f = np.einsum("nvc,nc->nv", P - cc[:, None, :], nn)
                fs.append(f)
                ts.append(f / np.maximum(np.einsum("nvc,nc->nv", m, nn), 0.2))
            inside = (fs[0] > 0) & (fs[1] > 0) & (fs[2] > 0) & on
            t = np.where(inside, np.minimum(np.minimum(ts[0], ts[1]), ts[2]), 0.0)
            t = np.clip(t, 0, 0.045)
            P -= t[:, :, None] * m
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


def wall_cut_prof(prof, depth=0.012):
    """Profile (y outward, z) cut 1.2 cm behind the wall face: vertices are inserted where the outline crosses
    the wall plane (y = 0) so the faces inside the wall can be dropped."""
    out = []
    n = len(prof)
    for j in range(n):
        a, b = np.asarray(prof[j], float), np.asarray(prof[(j + 1) % n], float)
        out.append((max(a[0], -depth), a[1]))
        if (a[0] < 0) != (b[0] < 0) and abs(b[0] - a[0]) > 1e-9:
            t = -a[0] / (b[0] - a[0])
            out.append((0.0, a[1] + t * (b[1] - a[1])))
    return out


def profile_course(part, mat, rng, z0, prof, seg=(0.6, 0.95), skip=(), Rfun=R_out, joint=0.01, jit=0.004, top_back=0.0):
    """Ring course of dressed profile blocks around the drum (cyl mapped). skip: list of (th_c, half_arc_m).
    Faces inside the wall (behind y = 0) are not modelled, except (top_back > 0) the top bed, which runs
    `top_back` m back into the wall core so no slot opens between the course and the walling above."""
    prof = wall_cut_prof(prof, depth=max(0.012, top_back))
    ztop_p = max(p_[1] for p_ in prof)
    inwall = np.array([p_[0] <= 0.0005 and not (top_back > 0 and p_[1] >= ztop_p - 1e-6) for p_ in prof])
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
            key = (nr, len(prof), tuple(inwall))
            if key not in _TPB:
                T = tmpl_rings(nr, len(prof), cap0=True, cap1=True)
                T = dict(orient(T, add_caps(P[None], T)[0]))
                m_ = len(prof)
                jq = np.arange(len(T["quads"])) % m_
                keep_q = ~(inwall[jq] & inwall[(jq + 1) % m_])
                T["quads"], T["qflat"] = T["quads"][keep_q], T["qflat"][keep_q]
                _TPB[key] = T
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
ARCH_AZ = [(18 + 36 * k) * D2R for k in range(10)]   # round 5: all 10 bays (client correction 2: no buttress bay)
# blind arcade: clear 0.72 w x 1.08 h (h/w 1.5 as in mill_stone_base), sill on the upper string course
ARCH = dict(cw=0.36, z0=2.92, zs=3.64, ring=(0.15, 0.165), fw=0.17, jz=[2.92, 3.28, 3.64])
Z_BAND0, Z_BAL0, Z_BAL1, Z_BAND1 = 2.55, 2.65, 2.82, 2.92
Z_CORN0 = 4.17                     # cornice raised 0.12 m (4.17 - 4.62) to make room for the taller arcade
DZ = 0.12                          # everything above the cornice moves up by this much
MORTAR_RECESS = 0.014


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


# (client correction 2: the sloping buttress was terrain in the art and is deleted; the drum runs continuous)
OPENINGS = [(0.0, hw_door)] + [(a, hw_window) for a in WIN_AZ] + [(a, hw_arch) for a in ARCH_AZ]


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


RING2 = {id(T): (ring_loop(T, T["n"][1] - 2), ring_loop(T, 0 if T["n"][1] > 3 else T["n"][1] - 3))
         for T in (T_RUB, T_RUBF, T_PIN, T_DRS, T_DRSH, T_RUB3, T_DRS3, T_DRSH3, T_DRS3X, T_DRSH3X, T_DRS3L, T_RUB3_NB, T_PIN_NB, T_RUB3_HI,
                   T_RUB3_HI_NB, T_RUB3_XHI, T_RUB3_XHI_NB)}


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
                 cell=0.01, flip=False):
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
        self.flip = flip
        Wall.registry.append(self)

    def tw(self, T):
        return perm_tmpl(T, self.flip)

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

    def covered_rect(self, ua, ub, za, zb, dil=1):
        """True where the wall rectangle [ua,ub]x[za,zb] is entirely stone-covered (stone outlines dilated by the
        skirt width) or dressed / blocked work."""
        cov = self.cov.copy()
        for _ in range(dil):
            g = cov.copy()
            g[1:] |= cov[:-1]
            g[:-1] |= cov[1:]
            g[:, 1:] |= cov[:, :-1]
            g[:, :-1] |= cov[:, 1:]
            cov = g
        unc = (~cov).astype(np.int32)       # dressed / blocked work does not count: its joints need the skin
        S = np.zeros((self.nu + 1, self.nz + 1), np.int64)
        S[1:, 1:] = unc.cumsum(0).cumsum(1)
        ua, ub, za, zb = np.broadcast_arrays(ua, ub, za, zb)
        i0 = np.clip(np.floor((ua - self.u0) / self.cell).astype(int), 0, self.nu)
        i1 = np.clip(np.ceil((ub - self.u0) / self.cell).astype(int), 0, self.nu)
        k0 = np.clip(np.floor((za - self.z0) / self.cell).astype(int), 0, self.nz)
        k1 = np.clip(np.ceil((zb - self.z0) / self.cell).astype(int), 0, self.nz)
        cnt = S[i1, k1] - S[i0, k1] - S[i1, k0] + S[i0, k0]
        inside = (i1 > i0) & (k1 > k0)
        return inside & (cnt == 0)

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
        # a gap of n free cells has its centre (n+1)/2 cells from the nearest stone cell centre -> width 2D - c
        if where:
            i, k = np.unravel_index(np.argmax(D), D.shape)
            return 2 * float(D.max()) - self.cell, self.U[i, k], self.Z[i, k]
        return 2 * float(D.max()) - self.cell

    def fill_pins(self, part, rng, yo=(0.012, 0.024), erode=0.0055, hw=(7, 6)):
        """Fill every mortar void wider than 3 cm with pinning stones shaped to the void: the free region
        around the widest point (eroded by the joint width, limited to ~15 x 13 cm) is flood-filled, its convex
        hull becomes the pin's outline (a box template mapped radially onto the polygon)."""
        c = self.cell
        npins = 0
        handled = np.zeros_like(self.cov)       # void regions already given a pin (never re-seeded)
        for it in range(14):
            occ = self.cov | self.block
            D = chamfer_dt(occ, c)
            cand = np.argwhere((D > 0.0155) & ~handled)
            if len(cand) == 0:
                break
            order = np.argsort(-D[cand[:, 0], cand[:, 1]], kind="stable")
            supp = np.zeros_like(occ)
            new = []
            seeds = []
            foot = []
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
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    continue
                pu = self.u0 + (i + (cells[:, 0] - si) + 0.5) * c
                pz = self.z0 + (kk[cells[:, 1]] + 0.5) * c
                pts = np.stack([pu, pz], 1)
                h = hull2d(pts)
                if len(h) < 3:
                    continue
                ext = np.ptp(h, 0)
                if ext.min() < 0.008 or ext.max() < 0.02:
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    continue
                if self.name == "drum" and pz.mean() < FOOT_PIN_Z:
                    # round 6: footing bed joints take only sparse irregular wedge pinners (below); the rest of
                    # the joint stays open mortar - never a row of chips
                    sub_ = handled[np.ix_(ii, kk)] | comp
                    handled[np.ix_(ii, kk)] = sub_
                    handled[i, k] = True
                    foot.append(h)
                    continue
                new.append(h)
                seeds.append((i, k))
            npins += self.footing_wedges(part, rng, foot)
            if not new:
                if foot:
                    continue
                break
            W_all, P_all = [], []
            for h in new:
                cen = h.mean(0)
                hp = cen + (h - cen) * 0.97
                ext = np.ptp(hp, 0)
                yo_pin = rng.uniform(*yo)
                dep = yo_pin + 0.008
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
                d = self.mortar_d(np.array([cen2[0]]), np.array([cen2[1]]))[0] + yo_pin
                W_all.append(self.to_world(nu_, nz_, d + y))
                P_all.append(np.stack([nu_ - cen2[0], y, nz_ - cen2[1]], 1))
            W = np.array(W_all)
            lowp = np.array([float(h_[:, 1].min()) + 0.01 < EYE_SOFFIT for h_ in new]) & (self.name != "arch")
            for sel_, Tq in ((lowp, T_PIN_NB), (~lowp, T_PIN)):
                if sel_.any():
                    part.add(W[sel_], self.tw(Tq), Pl=np.array(P_all)[sel_], mat="M_stone", smooth="all")
                    self.add(W[sel_], self.tw(Tq))
            npins += len(W)
            fb = []
            occ2 = self.cov | self.block
            for (i, k) in seeds:            # a pin that did not cover its own seed is never re-seeded there
                if self.z0 + (k + 0.5) * c < FOOT_PIN_Z and self.name == "drum":
                    continue
                if not self.cov[i, k]:
                    handled[max(i - 2, 0):i + 3, max(k - 2, 0):k + 3] = True
                    # fallback: a small squared pin centred in the free row / column runs through the seed
                    row, col = occ2[:, k], occ2[i, :]
                    il = i
                    while il > 0 and not row[il - 1] and i - il < 6:
                        il -= 1
                    ir = i
                    while ir < self.nu - 1 and not row[ir + 1] and ir - i < 6:
                        ir += 1
                    kl = k
                    while kl > 0 and not col[kl - 1] and k - kl < 5:
                        kl -= 1
                    kr = k
                    while kr < self.nz - 1 and not col[kr + 1] and kr - k < 5:
                        kr += 1
                    Lu = (ir - il + 1) * c - 0.012
                    Lz = (kr - kl + 1) * c - 0.012
                    if min(Lu, Lz) >= 0.018:
                        fb.append((self.u0 + (il + ir + 1) / 2 * c, self.z0 + (kl + kr + 1) / 2 * c,
                                   min(Lu, 0.07), min(Lz, 0.06)))
            if fb:
                fb = np.array(fb)
                Nf = len(fb)
                yq = rng.uniform(*yo, Nf)
                Pq, Tq = stone_local(rng, fb[:, 2], fb[:, 3], yq + 0.008, "pin", rot_deg=(1, 1, 3))
                yo_ = self.mortar_d(fb[:, 0], fb[:, 1]) + yq
                Wq = self.to_world(fb[:, 0, None] + Pq[:, :, 0], fb[:, 1, None] + Pq[:, :, 2],
                                   yo_[:, None] + Pq[:, :, 1])
                part.add(Wq, self.tw(Tq), Pl=Pq, mat="M_stone", smooth="all")
                self.add(Wq, self.tw(Tq))
                npins += Nf
            self.iters = getattr(self, "iters", []) + [len(W)]
        self.rejected = 0
        return npins

    def footing_wedges(self, part, rng, voids):
        """Round 6 (director r5 #2): 0-2 irregular wedge pinning stones per footing bed joint, 3-8 cm long,
        rotated +-20 deg, every one a different size and shape, never more than 2 in a row along a joint."""
        if not voids:
            return 0
        acc = getattr(self, "_foot_acc", [])
        n = 0
        for h in voids:
            cen = h.mean(0)
            ext = np.ptp(h, 0)
            if ext[1] < 0.012 or ext[0] < 0.03:
                continue
            near = [a for a in acc if abs(self.unwrap(np.array([a[0]]), cen[0])[0] - cen[0]) < 0.55 and abs(a[1] - cen[1]) < 0.05]
            close = [a for a in near if abs(self.unwrap(np.array([a[0]]), cen[0])[0] - cen[0]) < 0.16]
            if len(near) >= 2 or close or rng.random() < 0.35:
                continue
            L = float(np.clip(ext[0] * rng.uniform(0.55, 0.9), 0.03, 0.08))
            Hh = float(np.clip(ext[1] * rng.uniform(0.75, 1.05), 0.012, 0.045))
            yq = rng.uniform(0.010, 0.022)
            P, T = stone_local(rng, [L], [Hh], [yq + 0.012], "pin", rot_deg=(1.5, 1.5, 0.0))
            x, z = P[0, :, 0].copy(), P[0, :, 2].copy()
            # wedge: one end 35-60 % thinner, the thin edge slightly skewed
            tw = rng.uniform(0.35, 0.6) * rng.choice([-1, 1])
            z *= 1 - tw * np.clip(x / L + 0.5, 0, 1) if tw > 0 else 1 + tw * np.clip(0.5 - x / L, 0, 1)
            a = rng.uniform(-20, 20) * D2R
            xr, zr = x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a)
            cu, cz = cen[0] + rng.uniform(-0.2, 0.2) * ext[0] * 0.3, cen[1]
            d = self.mortar_d(np.array([cu]), np.array([cz]))[0] + yq
            W = self.to_world(cu + xr, cz + zr, d + P[0, :, 1])[None]
            Tq = self.tw(T_PIN_NB if T is T_PIN else T)
            if Tq["nv"] != W.shape[1]:
                Tq = self.tw(T)
            part.add(W, Tq, Pl=P, mat="M_stone", smooth="all", wear=0.5)
            self.add(W, Tq)
            acc.append((cu, cz))
            n += 1
        self._foot_acc = acc
        return n

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
            okst = (np.median(da - dm, 1) > 0.001) & (np.abs(dmo - dm).max(1) < 0.01) & \
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
            a, b_, c_ = V[0, q[0, 0]], V[0, q[0, 1]], V[0, q[0, 2]]
            nrm = np.cross(b_ - a, c_ - a)
            out = self.to_world(np.array([ui[0, 0]]), np.array([zi[0, 0]]), np.array([di[0, 0] + 0.05]))[0] - a
            if np.dot(nrm, out) < 0:
                q = q[:, ::-1].copy()
            # drop skirt quads that dive under a neighbouring stone (both outer corners under stone cover)
            ii = np.clip(((uo - self.u0) / self.cell).astype(int), -self.nu, 2 * self.nu)
            ii = ii % self.nu if self.period is not None else np.clip(ii, 0, self.nu - 1)
            kk = np.clip(((zo - self.z0) / self.cell).astype(int), 0, self.nz - 1)
            under = self.cov[ii, kk]                            # (N, m)
            # round 4: a skirt quad whose two outer corners both lie under a neighbouring stone can never be seen
            qk = ~(under & np.roll(under, -1, axis=1))
            qq = (q[None] + (np.arange(N) * 2 * m)[:, None, None])[qk]
            if len(qq) == 0:
                continue
            T2 = dict(quads=qq, tris=np.zeros((0, 3), np.int64), qflat=np.zeros(len(qq), bool),
                      tflat=np.zeros(0, bool), nv=N * 2 * m)
            part.add(V.reshape(1, -1, 3), T2, mat="M_mortar", smooth="all")

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
FOOT_PIN_Z = 0.47           # round 6: below this the drum's bed joints get sparse wedge pinners only


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
    band = (z > Z_BAND0 + 0.004) & (z < Z_BAND1 - 0.004)
    d = np.where(band, -0.085, d)                                  # behind the recessed ashlar of the balustrade band
    return d + wall_relief(u, z)


def depth_tilt_params(rng, N, p_tilt=0.18):
    """Per-stone face depth (2 cm range) and a 2-4 deg yaw on ~18% of stones so one end stands proud."""
    tilt = rng.random(N) < p_tilt
    ang = np.where(tilt, rng.uniform(2.0, 4.0, N) * rng.choice([-1, 1], N), 0.0) * D2R
    return ang, rng.uniform(-0.006, 0.012, N)


def wall_depth(face_d, mortar_d, L, ang, margin=0.008):
    """Stone depth = its protrusion above the mortar + margin (+ what a yawed end swings back): nothing of the
    stone is modelled deeper than ~2 cm behind the mortar surface."""
    return np.maximum(face_d - mortar_d + margin + np.abs(np.sin(ang)) * L / 2, 0.03)


def apply_tilt(P, ang):
    return xform(P, rotm([0, 0, 1], ang), np.zeros(3))


def emit_drum_stones(part, mat, rng, S, style, yoff_base, bulge=True, wall=None, tilt=True):
    if len(S["uc"]) == 0:
        return 0
    zc = S["zc"]
    th = S["uc"] / R_out(zc)
    N = len(zc)
    if tilt:
        ang, dy = depth_tilt_params(rng, N)
    else:
        ang, dy = np.zeros(N), rng.uniform(-0.003, 0.004, N)
    yo = yoff_base + dy
    D = wall_depth(yo, drum_mortar_d(S["uc"], zc), S["L"], ang)
    if bulge:  # stones bulge in and out of the wall plane (low-frequency)
        yo += 0.004 * np.sin(th * 3 + 1.3) * np.sin(zc * 2.1 + 0.4) + 0.003 * np.sin(th * 7 + zc * 3)
    for ix, P, Tq in stones_by_tmpl(rng, S["L"], S["H"], D, style, wall_stone_tmpl(zc, S["H"], STYLE[style]["T"])):
        low = zc[ix] < 2.2
        if low.any():          # conchoidal scoops on ~30 % of the faces in the bottom 2.2 m
            Pl_ = P[low]
            conchoidal(rng, Pl_, Tq)
            P[low] = Pl_
        P = apply_tilt(P, ang[ix])
        W = cyl_place(P, th[ix], zc[ix], yo[ix])
        part.add(W, Tq, Pl=P, mat=mat, smooth="all")
        if wall is not None:
            wall.add(W, Tq)
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
        P, T = stone_local(rng, [L], [dep], [Dv], style, rot_deg=(0.1, 0.1, 0.1))
        rho = ri + dep / 2 + P[:, :, 2]
        al = ac - P[:, :, 0] / rm
        E = np.stack([rho * np.cos(al), P[:, :, 1], zs + rho * np.sin(al)], 2)
        W = open_place(E, np.array([th0]), np.array([0.0]), np.array([0.0]), np.array([yfront]), Rfun)
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    # jambs
    for s, blocks in jambs.items():
        for (z0, z1, fw) in blocks:
            H = z1 - z0 - 0.012
            # more wear on the lower jambs (scuffed by carts / feet): 3-4 crisp spalls
            P, T = stone_local(rng, [fw], [H], [Dv], style, rot_deg=(0.1, 0.1, 0.15),
                               spall=(3, 4) if z0 < 1.0 else None)
            W = open_place(P, np.array([th0]), np.array([s * (ri + fw / 2)]), np.array([(z0 + z1) / 2]),
                           np.array([yfront]), Rfun)
            P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel")


T_BLK_PLX = tmpl_box(4, 4, 4, drop={(2, 0), (0, 0)})     # baluster plinth (variant frame): no bed, no back
T_BLK_ABX = tmpl_box(4, 4, 4, drop={(2, 1), (0, 0)})     # baluster abacus: no head, no back


def baluster_row(rb, spans, z0, z1, n_var=8, pitch=0.22):
    """Relief 'balustrade' of stubby turned balusters (kit component): a pool of 8 variant meshes (5 turned,
    2 eroded, 1 plain replacement block), placed as linked duplicates along the drum with pitch +-1.5 cm,
    yaw +-7 deg and lean +-1.5 deg in the object transforms. Variant frame: +x outward, z up from z0."""
    HB = z1 - z0
    TP, TA = 0.022, 0.022
    hs0 = HB - TP - TA
    base = np.array([(0.034, 0.0), (0.041, 0.005), (0.042, 0.015), (0.035, 0.021), (0.046, 0.044), (0.048, 0.062),
                     (0.041, 0.079), (0.030, 0.089), (0.038, 0.095), (0.039, 0.104), (0.031, 0.110),
                     (0.036, 0.118), (0.036, 1.0)])
    base[-1, 1] = hs0
    base[:-1, 1] *= hs0 / 0.126
    m = 16
    for v in range(n_var):
        pp = pool_part("baluster_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = RNG("baluster_var_%d" % v)
        if v < n_var - 1:
            dh = rv.uniform(-0.008, 0.008)
            prof = base.copy()
            prof[:, 1] *= (hs0 + dh) / hs0
            prof[:, 0] *= rv.uniform(0.9, 1.1)
            prof[:, 0] += rv.normal(0, 0.001, len(prof))
            P, T = lathe(prof[None], m)
            jq = np.arange(len(T["quads"])) % m
            keep_q = (jq != m // 2 - 1) & (jq != m // 2)      # the arc facing the band wall is never seen
            T = dict(quads=T["quads"][keep_q], tris=np.zeros((0, 3), np.int64), qflat=T["qflat"][keep_q],
                     tflat=np.zeros(0, bool), nv=T["nv"])
            if v >= n_var - 3:                                   # eroded: part of a bead / neck lost, facing out
                ang = np.arctan2(P[:, :, 1], P[:, :, 0])
                zc_e = rv.choice([0.017, 0.05, 0.1]) * hs0 / 0.126
                d_ang = np.abs((ang - rv.uniform(-0.5, 0.5) + PI) % (2 * PI) - PI)
                fz = np.clip(1 - ((P[:, :, 2] - zc_e) / 0.03) ** 2, 0, 1)
                fa = np.clip(1 - d_ang / rv.uniform(0.8, 1.6), 0, 1)
                k = 1 - rv.uniform(0.35, 0.55) * fz * fa
                P[:, :, 0] *= k
                P[:, :, 1] *= k
            P[:, :, 2] += TP
            pp.add(P, T, Pl=P, mat="M_stone_dressed", smooth="all", wear=0.8 if v >= n_var - 3 else 0.35)
            ta = TA - dh
        else:
            Ps, Ts = stone_local(rv, [rv.uniform(0.085, 0.1)], [hs0 - 0.002], [rv.uniform(0.09, 0.1)], "dressed",
                                 rot_deg=(0.5, 0.5, 2.0))
            Q = np.stack([Ps[:, :, 1] + 0.05, -Ps[:, :, 0], Ps[:, :, 2] + TP + hs0 / 2], -1)
            pp.add(Q, Ts, Pl=Ps, mat="M_stone_dressed", smooth="bevel", wear=0.5)
            ta = TA
        I3 = np.eye(3)[None]
        blocks_world(pp, "M_stone_dressed", np.array([[0, 0, TP / 2]]), I3,
                     [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), TP / 2]], c=0.005, T=T_BLK_PLX)
        blocks_world(pp, "M_stone_dressed", np.array([[0, 0, HB - ta / 2]]), I3,
                     [[rv.uniform(0.05, 0.06), rv.uniform(0.05, 0.06), ta / 2 - 0.0005]], c=0.005, T=T_BLK_ABX)
    Rb = float(R_out(z0 + HB / 2))
    a0, a1 = spans[0]
    nbal = int((a1 - a0) / pitch)
    us = a0 + (np.arange(nbal) + 0.5) * (a1 - a0) / nbal + rb.uniform(-0.015, 0.015, nbal)
    thb = us / Rb
    var = rb.integers(0, n_var - 3, nbal)
    for i in range(1, nbal):                                     # no two neighbours share a variant
        while var[i] == var[i - 1]:
            var[i] = rb.integers(0, n_var - 3)
    dfront = np.abs((thb + PI) % (2 * PI) - PI)
    fr_i, ot_i = np.nonzero(dfront < 0.75)[0], np.nonzero(dfront >= 0.75)[0]
    ero = np.concatenate([rb.choice(fr_i, 3, replace=False), rb.choice(ot_i, 5, replace=False)])
    var[ero] = np.where(np.arange(len(ero)) % 2 == 0, n_var - 3, n_var - 2)
    plain = rb.choice([i for i in range(nbal) if i not in set(ero)], 3, replace=False)
    var[plain] = n_var - 1
    rz = (thb - PI / 2) + rb.uniform(-0.12, 0.12, nbal)
    lx = np.clip(rb.normal(0, 0.8, nbal), -1.5, 1.5) * D2R
    ly = np.clip(rb.normal(0, 0.8, nbal), -1.5, 1.5) * D2R
    for i in range(nbal):
        R = euler([lx[i]], [ly[i]], [rz[i]])[0]
        ctr = np.array([(Rb + 0.055) * math.sin(thb[i]), -(Rb + 0.055) * math.cos(thb[i]), z0])
        place_instance("MILL_baluster_%03d" % i, "baluster_%d" % var[i], R, ctr)
    log("balusters %d placements from %d shared variants (eroded %d, %d on the front arc; plain blocks %d)"
        % (nbal, n_var, len(ero), 3, len(plain)))


def dentil_corbels(rc, zc, n=40, n_var=6, proj=0.18):
    """Dentil corbels under the cornice (kit component): 6 variant meshes (tapered, chipped dressed blocks, cut
    1 cm inside the frieze face: nothing modelled deeper), placed as linked duplicates round the drum."""
    for v in range(n_var):
        pp = pool_part("corbel_%d" % v, ["M_stone_dressed"])
        if pp.nv:
            continue
        rv = RNG("corbel_var_%d" % v)
        P, T = stone_local(rv, [rv.uniform(0.115, 0.13)], [rv.uniform(0.14, 0.15)], [0.24], "dressed",
                           rot_deg=(0.3, 0.3, 0.6))
        pr = P[:, :, 1] > -proj
        hz = 0.075
        f = 0.45 + 0.55 * np.clip((P[:, :, 2] / hz + 1) / 2, 0, 1)
        P[:, :, 1] = np.where(pr, -proj + (P[:, :, 1] + proj) * f, P[:, :, 1])
        Q = P.copy()
        Q[:, :, 1] = np.maximum(Q[:, :, 1] + proj, -0.01)
        pp.add(Q, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.45)
    thc = (np.arange(n) + 0.5) * 2 * PI / n + rc.uniform(-0.012, 0.012, n)
    var = np.array([(i * 5 + int(rc.integers(0, 2))) % n_var for i in range(n)])
    for i in range(n):
        Rr = float(R_out(zc))
        th = thc[i]
        yv = np.array([math.sin(th), -math.cos(th), 0.0])
        xv = np.array([-math.cos(th), -math.sin(th), 0.0])
        R = np.stack([xv, yv, [0, 0, 1.0]], 1) @ euler([rc.normal(0, 0.005)], [rc.normal(0, 0.005)],
                                                        [rc.normal(0, 0.01)])[0]
        place_instance("MILL_corbel_%03d" % i, "corbel_%d" % var[i], R, yv * Rr + np.array([0, 0, zc]))
    log("dentil corbels %d placements from %d shared variants" % (n, n_var))


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
                 p_tall=0.0, p_pin=0.0, Dr=(0.3, 0.4), wob=0.015)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "footing", 0.065, wall=WD)
    # 2. plain rubble 0.40 - 2.55
    S = coursing(rng, 0.40, Z_BAND0, free_fn_drum(rng), hr=(0.095, 0.15), hbig=0.22, p_big=0.1, lr=(0.2, 0.6),
                 p_tall=0.05, p_pin=0.14)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD)
    # 4. arcade zone: round 6 - the piers are laid by blind_arcade() as coursed long-and-short dressed blocks
    # (arcade_piers); without an arcade the zone is plain coursed ashlar
    if not ARCH_AZ:
        S = coursing(rng, Z_BAND1, ARCH["zs"], free_fn_drum(rng), hr=(0.2, 0.25), hbig=0.25, p_big=0.0,
                     lr=(0.24, 0.45), p_tall=0.0, p_pin=0.0, wob=0.0, joint=(0.01, 0.016))
        n += emit_drum_stones(P_st, "M_stone", rng, S, "ashlar", 0.012, bulge=False, wall=WD, tilt=False)
    S = coursing(rng, ARCH["zs"], Z_CORN0, free_fn_drum(rng), hr=(0.09, 0.14), hbig=0.18, p_big=0.1,
                 lr=(0.18, 0.5), p_tall=0.03, p_pin=0.1, wob=0.012)
    n += emit_drum_stones(P_st, "M_stone", rng, S, "rubble", 0.0, wall=WD)
    log("drum rubble stones", n)

    # ---- door, slit windows and blind arcade (kit components set into this drum) ----
    arched_door(parts, _drum_call=True)
    build_slit_windows(parts)
    blind_arcade(parts, _drum_call=True)
    build_band_cornice_and_finish(parts)
    return n


def arched_door_surround(parts):
    """Dressed door surround (jambs, irregular voussoir ring) and the worn threshold, in its own object."""
    P_dr = kpart(parts, "door_surround", ["M_stone_dressed"], wear=0.45, angle=22.0)
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


def build_slit_windows(parts):
    P_dr, P_mo = parts["dressed"], parts["mortar"]
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



def blind_arcade_build(parts):
    """Blind arcade recesses: voussoir rings, dressed jambs and sill slabs (object <PREFIX>_arcade_dressed) and the
    coursed rubble backs (<PREFIX>_arcade_backs; their pins and strike are laid with the drum's walls)."""
    P_dr = kpart(parts, "arcade_dressed", ["M_stone_dressed"], wear=0.4, angle=22.0)
    P_st = kpart(parts, "arcade_backs", ["M_stone"])
    # ---- dressed: blind arcade ----
    ra = RNG("arcade")
    for th in ARCH_AZ:
        jam = {s: [(ARCH["jz"][0], ARCH["jz"][1], ARCH["fw"] + ra.uniform(-0.01, 0.01)),
                   (ARCH["jz"][1], ARCH["jz"][2], ARCH["fw"] + ra.uniform(-0.01, 0.01))] for s in (-1, 1)}
        arch_set(P_dr, ra, th, ARCH["cw"], ARCH["zs"], int(ra.choice([9, 11])), ARCH["ring"], 0.30, {}, R_out,
                 yfront=0.018)
        # round 5: dressed sill slab on the floor of the recess (full 0.25 m recess depth, top 2.92-2.94 m,
        # 1 cm chamfer, 1-2 chips): the recess floor was open into the hollow drum from above
        cw = ARCH["cw"]
        zsill = ARCH["z0"] + ra.uniform(0.003, 0.016)
        P, T = stone_local(ra, [2 * cw + 0.10], [0.06], [0.275], "dressed", rot_deg=(0.25, 0.15, 0.2), spall=(1, 2))
        W = open_place(P, np.array([th]), np.array([ra.uniform(-0.01, 0.01)]), np.array([zsill - 0.03]),
                       np.array([0.006]))
        P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.5)

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
            ang, dy = depth_tilt_params(ra, len(S["uc"]))
            P, T = stone_local(ra, S["L"], S["H"], wall_depth(dy, a_mort(S["uc"], S["zc"]), S["L"], ang), "rubble")
            P = apply_tilt(P, ang)
            W = open_place(P, np.full(len(S["uc"]), th), S["uc"], S["zc"], -0.25 + dy)
            P_st.add(W, T, Pl=P, mat="M_stone", smooth="all")
            WA.add(W, T)
        # mortar back panel of the recess (low-frequency relief): laid after the pins, behind-stone cells culled
        WA.panel = (a_world, a_mort, cw)
        WA.part = P_st
    arcade_piers(P_dr, RNG("arcade_piers"))


def pier_courses(rng, H, hr=(0.15, 0.30)):
    """Course heights for one pier: 3-4 courses of 0.15-0.30 m summing to H, a different sequence per pier."""
    nmin, nmax = max(int(math.ceil(H / hr[1] - 1e-6)), 1), max(int(math.floor(H / hr[0] + 1e-6)), 1)
    for _ in range(200):
        n = int(rng.integers(nmin, min(nmax, nmin + 1) + 1))
        h = rng.uniform(0.7, 1.3, n)
        h *= H / h.sum()
        if (h >= hr[0]).all() and (h <= hr[1]).all():
            return h
    return np.full(nmin, H / nmin)


def arcade_piers(P_dr, rng, yfront=0.015, depth=0.30):
    """Round 6 (director r5 #6): every pier between two arcade recesses is laid as coursed dressed blocks -
    course heights 0.15-0.30 m (own sequence per pier), long and short blocks of 0.30-0.55 m alternating
    quoin-fashion so the vertical joints break course to course, the first block of each course returning
    into the recess reveal as its jamb. A block's reveal end follows the opening's axis (open mapping) and its
    joint end is radial (drum mapping), so neighbouring blocks close tight with ~1 cm joints, no voids."""
    if not ARCH_AZ:
        return 0
    WD = [w for w in Wall.registry if w.name == "drum"][-1]
    cw, z0, zs = ARCH["cw"], ARCH["z0"], ARCH["zs"]
    azs = sorted(float(a) % (2 * PI) for a in ARCH_AZ)
    nb = 0
    for k, a0 in enumerate(azs):
        a1 = azs[(k + 1) % len(azs)] + (2 * PI if k + 1 == len(azs) else 0.0)
        hs = pier_courses(rng, zs - z0 - 0.002)
        zb = z0 + 0.001
        phase = int(rng.integers(0, 2))
        for c, hc in enumerate(hs):
            zc = zb + hc / 2
            R = float(R_out(zc))
            th_l = a0 + math.asin(cw / R)          # left reveal edge (right side of arch k)
            th_r = a1 - math.asin(cw / R)          # right reveal edge (left side of arch k+1)
            S = R * (th_r - th_l)
            nblk = max(2, int(round(S / 0.42)))
            lens = []
            for q in range(nblk):
                lng = (q + c + phase) % 2 == 0
                lens.append(rng.uniform(0.44, 0.55) if lng else rng.uniform(0.28, 0.36))
            j = rng.uniform(0.008, 0.012, nblk - 1)
            lens = np.array(lens) * (S - j.sum()) / sum(lens)
            starts = np.concatenate([[0.0], np.cumsum(lens[:-1] + j)])
            H = hc - rng.uniform(0.009, 0.013)
            for q in range(nblk):
                L = float(lens[q])
                P, T = stone_local(rng, [L], [H], [depth], "dressed", rot_deg=(0.1, 0.1, 0.12),
                                   spall=(1, 3) if q in (0, nblk - 1) else (0, 2))
                u = starts[q] + L / 2 + P[0, :, 0]          # arc length from the left reveal edge
                y = P[0, :, 1] + yfront + rng.uniform(-0.003, 0.004)
                z = zc + P[0, :, 2] + rng.uniform(-0.002, 0.002)
                Rz = R_out(z)
                phi = th_l + u / Rz
                rr = Rz + y
                Wc = np.stack([rr * np.sin(phi), -rr * np.cos(phi), z], 1)
                # opening-aligned mapping near each reveal: lateral coordinate in that arch's frame
                Wo = Wc.copy()
                wgt = np.ones(len(u))
                for (ath, uref, sg) in ((a0, 0.0, 1.0), (a1, S, -1.0)):
                    dist = sg * (u - uref)
                    near = dist < 0.15
                    if not near.any():
                        continue
                    xo = Rz * np.sin(phi - ath)
                    d = np.sqrt(np.maximum(Rz ** 2 - xo ** 2, 0.01)) + y
                    Wa = np.stack([xo * math.cos(ath) + d * math.sin(ath), xo * math.sin(ath) - d * math.cos(ath), z], 1)
                    wv = smoothstep(0.0, 0.15, dist)
                    Wo = np.where(near[:, None], Wa, Wo)
                    wgt = np.where(near, wv, wgt)
                W = (Wo * (1 - wgt[:, None]) + Wc * wgt[:, None])[None]
                P_dr.add(W, T, Pl=P, mat="M_stone_dressed", smooth="bevel", wear=0.35)
                WD.add(W, T)
                nb += 1
            zb += hc
    log("arcade piers: %d coursed long-and-short dressed blocks in %d piers" % (nb, len(azs)))
    return nb


def build_band_cornice_and_finish(parts):
    P_st, P_mo, P_dr = parts["stones"], parts["mortar"], parts["dressed"]

    # ---- band: strings, back panel, balusters ----
    rb = RNG("band")
    skip_b = ()
    # profiles stop 5 cm inside the wall face (nothing modelled deeper)
    prof_lo = [(-0.05, 0), (0.10, 0), (0.12, 0.018), (0.12, 0.08), (0.105, 0.097), (-0.05, 0.10)]
    prof_up = [(-0.05, 0), (0.08, 0), (0.10, 0.018), (0.10, 0.082), (0.088, 0.098), (-0.05, 0.10)]
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAND0, prof_lo, skip=skip_b)
    profile_course(P_dr, "M_stone_dressed", rb, Z_BAL1, prof_up, skip=skip_b, top_back=0.065)
    Rm = float(R_out(Z_BAL0))
    u0b = rb.uniform(0, 2 * PI * Rm)
    spans = [(u0b, u0b + 2 * PI * Rm)]
    S = coursing(rb, Z_BAL0, Z_BAL1, lambda zb, zt: spans, hr=(0.17, 0.17), p_big=0, lr=(0.3, 0.55), p_tall=0,
                 p_pin=0, wob=0, joint=(0.008, 0.014), Dr=(0.05, 0.06))
    th = S["uc"] / R_out(S["zc"])
    P, T = stone_local(rb, S["L"], S["H"], S["D"], "ashlar")
    P_dr.add(cyl_place(P, th, S["zc"], np.full(len(th), -0.03)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    baluster_row(rb, spans, Z_BAL0, Z_BAL1)

    # ---- cornice (raised: 4.17 - 4.62) ----
    rc = RNG("cornice")
    zc0 = Z_CORN0
    profile_course(P_dr, "M_stone_dressed", rc, zc0, [(-0.05, 0), (0.03, 0), (0.04, 0.01), (0.04, 0.06),
                                                    (0.03, 0.07), (-0.05, 0.07)], seg=(0.5, 0.8))
    # frieze course between corbels
    S = coursing(rc, zc0 + 0.07, zc0 + 0.22, lambda zb, zt: [(0.3, 0.3 + 2 * PI * float(R_out(zc0 + 0.15)))],
                 hr=(0.15, 0.15), p_big=0, lr=(0.25, 0.5), p_tall=0, p_pin=0, wob=0, joint=(0.008, 0.012),
                 Dr=(0.05, 0.06))
    th = S["uc"] / R_out(S["zc"])
    P, T = stone_local(rc, S["L"], S["H"], S["D"], "ashlar")
    P_dr.add(cyl_place(P, th, S["zc"], np.full(len(th), -0.005)), T, Pl=P, mat="M_stone_dressed", smooth="bevel")
    dentil_corbels(rc, zc0 + 0.145, n=int(round(40 * float(R_out(zc0)) / 2.446)))
    profile_course(P_dr, "M_stone_dressed", rc, zc0 + 0.22, [(-0.05, 0), (0.19, 0), (0.20, 0.01), (0.20, 0.042),
                                                           (0.19, 0.05), (-0.05, 0.05)], seg=(0.6, 0.9))
    cap = [(-0.06, 0), (0.19, 0), (0.235, 0.035), (0.24, 0.042), (0.243, 0.056), (0.252, 0.056), (0.256, 0.046),
           (0.29, 0.058), (0.305, 0.072), (0.305, 0.145), (0.29, 0.16), (0.0, 0.18), (-0.06, 0.18)]
    profile_course(P_dr, "M_stone_dressed", rc, zc0 + 0.27, cap, seg=(0.75, 1.05), joint=0.008)

    # ---- pinning stones in every void > 3 cm, concave strike skirts, visible-mortar report ----
    rp = RNG("pins")
    for wl in [w for w in Wall.registry if w.name in ("drum", "arch")]:
        before = wl.mortar_fraction(*wl.metric_z)[0] if wl.metric_z else wl.mortar_fraction()[0]
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_pre.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        npin = wl.fill_pins(getattr(wl, "part", P_st), rp)
        if os.environ.get("MILL_DUMP") and wl.name == "drum":
            np.save(os.environ["MILL_DUMP"] + "_post.npy", (wl.cov.astype(np.uint8) + 2 * wl.block.astype(np.uint8)))
        if wl.name == "drum":
            log("drum pins %d, rejected %d (plain-zone mortar before pins %.1f%%)" % (npin, wl.rejected, 100 * before))
            wl.report("drum")
            log("  pins per iteration", wl.iters)
        if not os.environ.get("MILL_NOSKIRT"):
            wl.skirts(P_mo)
        if wl.name == "arch":
            a_world, a_mort, cw = wl.panel
            xs = np.linspace(-cw - 0.06, cw + 0.06, 16)
            zz = np.linspace(ARCH["z0"] - 0.02, ARCH["zs"] + cw + 0.05, 20)
            X, Z = np.meshgrid(xs, zz, indexing="ij")
            hid = wl.covered_rect(X[:-1, :-1], X[1:, :-1], Z[:-1, :-1], Z[:-1, 1:])
            add_grid(P_mo, "M_mortar", a_world(X, Z, a_mort(X, Z)), keep=~hid, flip=False)
    arch_walls = [w for w in Wall.registry if w.name == "arch"]
    fr = np.mean([w.mortar_fraction()[0] for w in arch_walls])
    log("WALL arcade backs: mean visible mortar %.1f%%, widest void %.3f m" %
        (100 * fr, max(w.max_void() for w in arch_walls)))

    # ---- mortar core (outer skin): recessed 2.2 cm (4.5 cm raked in the bottom 0.6 m), +-5 mm relief ----
    nth = 288
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.concatenate([np.linspace(0.0, 0.40, 6), np.linspace(0.41, 0.70, 5), np.linspace(0.78, Z_BAND0, 22),
                         [Z_BAND0 + 0.005, Z_BAND1 - 0.005], np.linspace(Z_BAND1, Z_CORN0 + 0.12, 15)])
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
    # remove cells hidden behind full stone cover (stone outlines + their 1 cm mortar strike skirts, dressed work)
    WD = [w for w in Wall.registry if w.name == "drum"][0]
    us0 = np.where(ths > PI, ths - 2 * PI, ths) * RREF
    us1 = us0 + 2 * PI / nth * RREF
    hid = WD.covered_rect(us0[:, None], us1[:, None], zs[None, :-1], zs[None, 1:])
    band = (zs[None, :-1] > Z_BAND0 - 0.01) & (zs[None, 1:] < Z_BAND1 + 0.01)
    ledge = (zs[None, 1:] > 0.30) & (zs[None, :-1] < 0.50)      # footing ledge: no skirts there, keep the skin
    ledge |= (zs[None, 1:] > Z_BAND1) & (zs[None, :-1] < ARCH["zs"])   # pier joints: mortar skin, never the core
    n0 = int(keep.sum())
    keep &= ~(hid & ~band & ~ledge)
    log("drum mortar skin: %d of %d cells hidden behind stone cover -> culled" % (n0 - int(keep.sum()), n0))
    add_grid(P_mo, "M_mortar", G, keep=keep, wrap=True, flip=False)
    wall_core_backing(P_mo, Z_BAL1 + 0.02, Z_CORN0 + 0.28)


def wall_core_backing(part, z0, z1, d_out=None, depth=0.30, nth=180, nz=9):
    """Round 5 (producer note 6, 'never open holes when culling'): a cheap closed wall-core ring behind the
    band / arcade / cornice zone at R_out(z) - MORTAR_RECESS - 0.02, holed only at the clear openings (whose
    pockets are closed by the jambs, voussoirs, sill slabs and rubble backs), with top and bottom annuli and an
    inner face behind the recess backs. Culled stone soffits and mortar now show this surface, never a void."""
    d_out = -(MORTAR_RECESS + 0.02) if d_out is None else d_out
    ths = np.linspace(0, 2 * PI, nth, endpoint=False)
    zs = np.linspace(z0, z1, nz)
    TH, Z = np.meshgrid(ths, zs, indexing="ij")
    Rr = R_out(Z) + d_out
    G = np.stack([Rr * np.sin(TH), -Rr * np.cos(TH), Z], -1)
    keep = np.ones((nth, nz - 1), bool)
    for i in range(nth):
        for j in range(nz - 1):
            for tq in (ths[i], ths[i] + PI / nth, ths[i] + 2 * PI / nth):
                for zq in (zs[j], 0.5 * (zs[j] + zs[j + 1]), zs[j + 1]):
                    if inside_clear(tq, zq):
                        keep[i, j] = False
    add_grid(part, "M_mortar", G, keep=keep, wrap=True, flip=False)
    Ri = R_out(Z) + d_out - depth
    Gi = np.stack([Ri * np.sin(TH), -Ri * np.cos(TH), Z], -1)
    add_grid(part, "M_mortar", Gi[::4], wrap=True, flip=False)
    for j, fl in ((0, True), (nz - 1, False)):          # bottom annulus faces down, top faces up
        A = np.stack([G[::4, j], Gi[::4, j]], 1)
        add_grid(part, "M_mortar", A, wrap=True, flip=fl)
    log("wall-core backing z %.2f..%.2f at d %.3f: %d of %d outer cells kept (openings holed)"
        % (z0, z1, d_out, int(keep.sum()), keep.size))


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


def door_planks(part, rng, x0, width, z_bot, ztop_fn, xf, n=6, t=0.042):
    """Arch-topped ledged door leaf planks (kit component), leaf-local x lateral (hinge at x0), y thickness from
    the outer face (y = 0) inward, z up; xf maps leaf-local -> world. Age per art bible section 4: outer arrises
    worn 1.5-2.5 cm (more in the bottom 0.4 m and on the lock stile), ragged rotted bottom end (+-2-4 cm) with
    two planks 3-5 cm short, face checks (3-5 mm wide, 0.3-0.9 m long), one split at the arched head, plank
    proudness +-3 mm, gaps 4-10 mm, free edge sagging 5-8 mm. Returns [(xa, xb, dy)] per plank."""
    gaps = rng.uniform(0.004, 0.010, n - 1)
    wds = rng.uniform(0.17, 0.23, n)
    wds = wds / wds.sum() * (width - gaps.sum())
    xa_s = x0 + np.concatenate([[0], np.cumsum(wds[:-1] + gaps)])
    short = set(int(v) for v in rng.choice(n, 2, replace=False))
    checked = set(int(v) for v in rng.choice(n, 3, replace=False))
    split = int(np.argmin(np.abs(xa_s + wds / 2 - (x0 + width / 2))))          # the plank under the crown
    sag = rng.uniform(0.005, 0.008)
    nr = 48
    tt = np.linspace(0, 1, nr)
    tt = tt + 0.35 * tt * (1 - tt) * (0.5 - tt)                              # a little denser at both ends
    out = []
    for i in range(n):
        xa, w = xa_s[i], wds[i]
        dy = rng.uniform(-0.003, 0.003)
        th = t + rng.uniform(-0.002, 0.002)
        lock = i == n - 1
        cf0 = rng.uniform(0.015, 0.022, 2) + (np.array([0.0, 0.005]) if lock else 0.0)
        xc = rng.uniform(0.3, 0.7) * w
        ck0, ckl = rng.uniform(0.1, 0.9), rng.uniform(0.3, 0.9)
        ckd = rng.uniform(0.004, 0.006)
        sh = rng.uniform(0.03, 0.05) if i in short else 0.0
        ph = rng.uniform(0, 6, 3)
        rings, xs_all = [], []
        for k, tq in enumerate(tt):
            # approximate height above the bottom for the extra rot wear (bottom 0.4 m)
            zz = tq * 2.15
            rot = 0.009 * np.clip(1 - zz / 0.4, 0, 1)
            cl, cr = cf0[0] + rot + 0.002 * math.sin(zz * 3 + ph[0]), cf0[1] + rot + 0.002 * math.sin(zz * 2.3 + ph[1])
            cyl, cyr = min(0.55 * cl, 0.016), min(0.55 * cr, 0.016)
            c45 = 1 - math.cos(PI / 4)
            # face check (and the split at the head)
            dep, hw_ = 0.0, 0.0025
            if i in checked:
                u = (zz - ck0) / ckl
                if 0 < u < 1:
                    dep = ckd * math.sqrt(math.sin(u * PI))
            if i == split and zz > 1.85:
                u = min((zz - 1.85) / 0.35, 1.0)
                dep = max(dep, 0.65 * th * math.sqrt(u))
                hw_ = 0.0015 + 0.0015 * u
            xcs = xc if i not in checked and i != split else xc
            prof = [(0.0, cyl), (cl * c45, cyl * c45), (cl, 0.0),
                    (cl + (xcs - hw_ - cl) * 0.5, 0.0), (xcs - hw_, 0.0), (xcs, dep), (xcs + hw_, 0.0),
                    (xcs + hw_ + (w - cr - xcs - hw_) * 0.5, 0.0),
                    (w - cr, 0.0), (w - cr * c45, cyr * c45), (w, cyr),
                    (w, th - 0.004), (w - 0.004, th), (0.004, th), (0.0, th - 0.004)]
            rings.append(prof)
        R_ = np.array(rings)                                               # (nr, m, 2)
        m = R_.shape[1]
        X = xa + R_[..., 0]
        # ragged rotted bottom end, short planks
        zb = z_bot + 0.012 + 0.010 * np.sin(X * 37 + ph[2]) + 0.007 * np.sin(X * 91 + i) + \
            0.006 * np.abs(np.sin(X * 23 + 2 * i)) + sh
        zt_ = ztop_fn(X)
        Z = zb + tt[:, None] * (zt_ - zb)
        Z -= sag * (X - x0) / width
        Y = R_[..., 1] + dy + 0.0025 * np.sin(Z * 3 + xa * 20)                # slight warp
        P = np.stack([X, Y, Z], -1).reshape(1, -1, 3)
        T = tmpl_rings(nr, m, cap0=True, cap1=True)
        P = add_caps(P, T)
        T = orient(T, P[0])
        part.add(xf(P), T, Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.65 + 0.2 * (i in short))
        out.append((xa, xa + w, dy))
    log("door planks %d: short %s, checks %s, split at the head %d, free-edge sag %.1f mm"
        % (n, sorted(short), sorted(checked), split, sag * 1000))
    return out


def build_door_and_interior(parts):
    P_mo, P_int, P_leaf, P_iron = parts["mortar"], parts["interior"], parts["door"], parts["door_iron"]
    rng = RNG("door_leaf")
    Rd = R_DOOR
    RI = R_BASE0 - 0.80                    # inner wall radius (kit: follows the drum)
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
        # only the arc of the inner wall that can be seen through the door is modelled
        if abs(((ths[i] + PI / nth) % (2 * PI)) - PI) > 1.25:
            keep[i, :] = False
            continue
        for j in range(len(zs) - 1):
            for tq in (ths[i], ths[i] + 2 * PI / nth):
                d = (tq + PI) % (2 * PI) - PI
                x = RI * math.sin(d)
                zt = zs[j]
                if abs(d) < PI / 2 and abs(x) < XW + 0.02 and zt < ZV + 0.9 * math.sqrt(max(XW ** 2 - x ** 2, 0)):
                    keep[i, j] = False
    add_grid(P_int, "M_mortar", G, keep=keep, wrap=True, flip=True)
    # flagstone floor
    rf = RNG("floor")
    cells = []
    y = -(RI + 0.65)
    while y < RI + 0.1:
        hrow = rf.uniform(0.38, 0.6)
        x = -(RI + 0.1) + rf.uniform(0, 0.3)
        while x < RI + 0.1:
            w = rf.uniform(0.35, 0.7)
            cx, cy = x + w / 2, y + hrow / 2
            inside = (math.hypot(cx, cy) < RI + 0.15 and cy < -0.6 and abs(cx) < RI - 0.3) or (abs(cx) < 0.75 and cy < -(RI - 0.3))
            if inside:
                cells.append((cx, cy, w - 0.025, hrow - 0.025))
            x += w
        y += hrow
    c = np.array(cells)
    N = len(c)
    P, T = stone_local(rf, c[:, 2], c[:, 3], np.full(N, 0.035), "flag", rot_deg=(0.3, 0.3, 1.5), T=T_FLAG_O)
    # stone_local: x = length, y = "outward" (thickness), z = height -> lay flat: local y -> world z
    Rm = frame_mats(np.repeat([[1.0, 0, 0]], N, 0), np.repeat([[0, 0, 1.0]], N, 0), np.repeat([[0, -1.0, 0]], N, 0))
    W = xform(P, Rm, np.stack([c[:, 0], c[:, 1], np.full(N, Z_TH) + rf.normal(0, 0.003, N)], 1))
    P_int.add(W, T, Pl=P, mat="M_stone", smooth="all")
    # ceiling beams + floor boards (first floor at 3.0 m)
    rt = RNG("ceiling")
    # (the first-floor beams and boards are above the line of sight through the door: not modelled)
    bx = -(RI + 0.1)
    a, b = [], []
    while False:            # (the floor boards above the beams cannot be seen through the door: not modelled)
        w = rt.uniform(0.18, 0.28)
        cx = bx + w / 2
        if not (0.3 < cx < 0.85):  # hatch for the ladder
            half = math.sqrt(max((RI + 0.15) ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, half, 3.285])
        else:
            half = math.sqrt(max((RI + 0.15) ** 2 - cx ** 2, 0.05))
            a.append([cx, -half, 3.285])
            b.append([cx, 0.75, 3.285])
        bx += w + 0.008
    a, b = np.array(a), np.array(b)
    # beyond ~1.5 m of visible depth (y > -0.65) the floor is a plain flagged surface: one low-res sheet
    # (producer note: interiors only to the depth seen through openings)
    xs_ = np.linspace(-(RI + 0.1), RI + 0.1, 9)
    ys_ = np.linspace(-0.66, RI + 0.15, 7)
    X_, Y_ = np.meshgrid(xs_, ys_, indexing="ij")
    keep_ = np.hypot((X_[:-1, :-1] + X_[1:, 1:]) / 2, (Y_[:-1, :-1] + Y_[1:, 1:]) / 2) < RI + 0.25
    add_grid(P_int, "M_stone", np.stack([X_, Y_, np.full_like(X_, Z_TH - 0.004)], 2), keep=keep_, flip=False)

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

    planks = door_planks(P_leaf, rng, leaf_x0, LEAF_W, Z_TH + 0.01, lambda x: ZS_DOOR + np.sqrt(
        np.clip((DOOR_CW + 0.055) ** 2 - x ** 2, 0, None)) - 0.01, leaf_xf)
    # ledges + braces on the inner face
    ly = 0.042 + 0.018
    for zl in (Z_TH + 0.32, Z_TH + 1.02, Z_TH + 1.62):
        a = np.array([[leaf_x0 + 0.06, ly, zl]])
        b = np.array([[-leaf_x0 - 0.06, ly, zl]])
        Wm = Part("tmp", ["M_timber"])
        Part.registry.pop()
        member(Wm, "M_timber", a, b, 0.15, 0.036, up=(0, 1, 0), c=0.008, T=T_PLK_NI)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK_NI, mat="M_timber_weathered", smooth="bevel")
    for (z0, z1) in ((Z_TH + 0.40, Z_TH + 0.94), (Z_TH + 1.10, Z_TH + 1.54)):
        a = np.array([[leaf_x0 + 0.14, ly, z0]])
        b = np.array([[-leaf_x0 - 0.14, ly, z1]])
        Wm = Part("tmp", ["M_timber"])
        Part.registry.pop()
        member(Wm, "M_timber", a, b, 0.11, 0.032, up=(0, 1, 0), c=0.008, T=T_PLK_NI)
        P_leaf.add(leaf_xf(Wm.V[0].reshape(1, -1, 3)), T_PLK_NI, mat="M_timber_weathered", smooth="bevel")
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
        path = np.stack([xs_, np.full(n, -th_ - 0.003), np.full(n, zh) + rng.uniform(-0.002, 0.002, n)], 1)[None]
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
        P, T = lathe(np.repeat(prof[None], len(nx), 0), 8, open_base=True)
        Rn = rotm([1, 0, 0], np.full(len(nx), PI / 2))
        P = xform(P, Rn, np.stack([nx, np.full(len(nx), -0.0098), np.full(len(nx), zh)], 1))
        P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
        # pintle: L-pin leaded into the jamb rebate
        pin = np.array([[hinge[0] - 0.09, hinge[1] - 0.012, zh - 0.06], [hinge[0] + 0.004, hinge[1] - 0.012,
                                                                        zh - 0.06]])
        P, T = sweep(pin[None], rect_prof(0.022, 0.022, 0.004), up=(0, 0, 1))
        P_iron.add(P, T, mat="M_iron", smooth="none")
    # clinched nail heads in rows over the ledges (outer face)
    nails = []
    for zl in (Z_TH + 0.32, Z_TH + 1.02, Z_TH + 1.62):
        for (xa_, xb_, dy_) in planks:
            for o in (0.3, 0.7):
                nails.append((xa_ + (xb_ - xa_) * o + rng.uniform(-0.01, 0.01), zl + rng.uniform(-0.03, 0.03), dy_))
    nails = np.array(nails)
    prof = np.array([(0.0, 0.0), (0.009, 0.0), (0.008, 0.003), (0.004, 0.006), (0.0, 0.0065)])
    P, T = lathe(np.repeat(prof[None], len(nails), 0), 6, open_base=True)
    Rn = rotm([1, 0, 0], np.full(len(nails), PI / 2))
    P = xform(P, Rn, np.stack([nails[:, 0], nails[:, 2] - 0.001, nails[:, 1]], 1))
    P_iron.add(leaf_xf(P), T, mat="M_iron", smooth="all")
    # ring pull with back plate and staple
    rx, rz = -leaf_x0 - 0.22, Z_TH + 0.98
    prof = np.array([(0.0, 0.0), (0.05, 0.0), (0.05, 0.004), (0.044, 0.007), (0.012, 0.009), (0.0, 0.016)])
    P, T = lathe(prof[None], 16, open_base=True)
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


T_GRUB = tmpl_box(9, 4, 9, drop={(1, 0)})        # settled ground stone: local y is UP, no bed face (buried)
T_GRAV = tmpl_box(6, 3, 6, drop={(1, 0)})        # gravel / pebble (same convention, lighter)
STYLE["ground"] = dict(rr=(0.06, 0.008, 0.015), ry=0.012, nxz=0.05, ny=0.008, pil=(0.0, 0.008), tap=0.15,
                       shear=0.12, T=T_GRUB, cuts=(3, 4), cutk=(0.78, 0.9), facets=(1, 2), hf=0.003, ftilt=0.45,
                       fshave=(0.01, 0.03))
STYLE["gravel"] = dict(rr=(0.12, 0.003, 0.006), ry=0.004, nxz=0.05, ny=0.003, pil=(0.0, 0.003), tap=0.15,
                       shear=0.12, T=T_GRAV, cuts=(2, 3), cutk=(0.75, 0.9), facets=(0, 1), hf=0.0, ftilt=0.5,
                       fshave=(0.003, 0.008))
# round 6: large half-buried ground stones - fracture-cut outline, crisp broken top arris (1-2 crisp edges,
# 0.3-1.2 cm arris variation), 1-2 tilted split facets on the top, flat-ish beds
T_GRUB_B = tmpl_box(13, 6, 13, drop={(1, 0)})
STYLE["ground_big"] = dict(avar=(0.003, 0.012, 0.6), rr=(0.06, 0.006, 0.012), ry=0.010, nxz=0.04, ny=0.008,
                           pil=(0.002, 0.012), tap=0.12, shear=0.10, T=T_GRUB_B, cuts=(3, 4), cutk=(0.8, 0.92),
                           facets=(1, 2), hf=0.003, ftilt=0.35, fshave=(0.012, 0.035))
R_UPRIGHT = frame_mats(np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]), np.array([[0, -1.0, 0]]))[0]


def settled_stones(part, rng, xy, L, W, Hh, bury=(0.45, 0.65), style="ground", collar=(0.02, 0.04),
                   collar_min=0.10, tilt=4.0, mat="M_rubble", z0=0.0, expose=None, tilt_range=None, expose_abs=None):
    """Split stones settled into the ground (kit component): plan L x W, height Hh; 45-65 % of the height is
    buried (nothing modelled deeper than the ground cut), angular fracture-cut outline, faceted top, 0.8-1.5 cm
    arrises. Round 5: `expose` = (min, max) height of the stone's highest point above the ground (so no exposed
    side is taller than that), `tilt_range` = (min, max) deg of bed tilt; stones larger than `collar_min` get a
    CONCAVE soil collar (M_earth) that climbs the stone to its local surface height and runs out tangentially."""
    N = len(xy)
    P, T = stone_local(rng, L, W, Hh, style, rot_deg=(0, 0, 0))
    bur = rng.uniform(*bury, N)
    yaw = rng.uniform(0, 2 * PI, N)
    if tilt_range is not None:
        ta = rng.uniform(*tilt_range, N) * D2R
        td = rng.uniform(0, 2 * PI, N)
        R = euler(ta * np.cos(td), ta * np.sin(td), yaw) @ R_UPRIGHT
    else:
        R = euler(rng.normal(0, tilt * D2R, N), rng.normal(0, tilt * D2R, N), yaw) @ R_UPRIGHT
    ctr = np.stack([xy[:, 0], xy[:, 1], Hh * (1 - bur) + z0], 1)
    W_ = xform(P, R, ctr)
    if expose is not None or expose_abs is not None:
        ex_ = (rng.uniform(*expose, N) if expose_abs is None else np.asarray(expose_abs, float)) + \
            np.broadcast_to(np.asarray(z0, float), (N,))
        W_[:, :, 2] += (ex_ - W_[:, :, 2].max(1))[:, None]
    part.add(W_, T, Pl=P, mat=mat, smooth="all", wear=0.6)
    if collar is None:
        return W_
    for i in np.nonzero(np.maximum(L, W) > collar_min)[0]:
        soil_collar(part, rng, W_[i], rng.uniform(*collar), (0.05, 0.09), i)
    return W_


def soil_collar(part, rng, Wi, hc, wout_r, seed_i=0, m=24, inset=0.93):
    """Concave soil fillet (M_earth) round a bedded stone (kit component): the inner edge follows the stone's
    ground outline (max radius per angular bin), climbs to just under the stone's local surface (at most hc),
    and the profile z = h (1 - f)^2.6 runs out tangentially to the ground over wout_r (min, max) m."""
    a = np.linspace(0, 2 * PI, m, endpoint=False)
    prof_f = np.array([0.0, 0.08, 0.18, 0.31, 0.46, 0.63, 0.81, 1.0])
    cxy = Wi[:, :2].mean(0)
    dv = Wi[:, :2] - cxy
    av = np.arctan2(dv[:, 1], dv[:, 0])
    rv = np.hypot(dv[:, 0], dv[:, 1])
    near_g = Wi[:, 2] > -0.02
    rr = np.zeros(m)
    zs_ = np.zeros(m)
    for j in range(m):
        sel = (np.abs((av - a[j] + PI) % (2 * PI) - PI) < PI / m * 1.6) & near_g
        if sel.any():
            k_ = np.argmax(np.where(sel, rv, -1))
            rr[j] = rv[k_]
            zs_[j] = Wi[k_, 2]
    if (rr <= 0).any():
        rr[rr <= 0] = np.median(rr[rr > 0]) if (rr > 0).any() else 0.1
    rin = rr * inset
    zin = np.clip(np.minimum(zs_ - 0.006, hc), -0.004, None)
    wout = rng.uniform(*wout_r) * (1 + 0.25 * np.sin(a * 3 + rng.uniform(0, 6)) + 0.1 * np.sin(a * 5 + seed_i))
    rows = []
    for f in prof_f:
        rad_ = rin + (rr * (1 - inset) + wout) * f
        zf = zin * (1 - f) ** 2.6 if f < 1 else np.full(m, -0.003)
        rows.append(np.stack([cxy[0] + rad_ * np.cos(a), cxy[1] + rad_ * np.sin(a), zf], 1))
    G = np.stack(rows, 1)
    nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
    add_grid(part, "M_earth", G, wrap=True, flip=bool(nrm_[2] < 0))


def flag_outline(rf, Lf, Wf, m=96, front_facets=0):
    """Irregular 5-7 sided flag outline (+-4 cm corners, 1-3 straight broken corners, wandering edges).
    front_facets (round 6, step stone): the front (-y) edge is split into that many straight fracture
    segments with +-1.5 cm kinks. Returns (O (mm,2), straight mask (mm,), segment id (mm,): >= 0 on a front
    facet, -1 elsewhere)."""
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
    front_seg = {}
    if front_facets:
        nside0 = len(corners)
        segl = [np.linalg.norm(corners[(j + 1) % nside0] - corners[j]) for j in range(nside0)]
        cand = [j for j in range(nside0) if (corners[j][1] + corners[(j + 1) % nside0][1]) / 2 < -Wf / 4]
        jf = max(cand, key=lambda j: segl[j])
        a_, b_ = corners[jf], corners[(jf + 1) % nside0]
        fr = np.sort(rf.uniform(0.25, 0.75, front_facets - 1)) if front_facets > 2 else np.array([rf.uniform(0.38, 0.62)])
        ins = [a_ + (b_ - a_) * f + np.array([rf.uniform(-0.01, 0.01), rf.uniform(-0.015, 0.015)]) for f in fr]
        corners = np.concatenate([corners[:jf + 1], np.array(ins), corners[jf + 1:]])
        for q in range(front_facets):
            straight.add(jf + q)
            front_seg[jf + q] = q
    nside = len(corners)
    if not front_facets:
        straight.add(int(rf.integers(0, nside)))       # 1-2 crisp straight fracture edges per flag
    segs = [np.linalg.norm(corners[(j + 1) % nside] - corners[j]) for j in range(nside)]
    tot = sum(segs)
    pts, st, sid = [], [], []
    for j in range(nside):
        nseg = max(2, int(round(m * segs[j] / tot)))
        a, b = corners[j], corners[(j + 1) % nside]
        nrm_e = np.array([b[1] - a[1], a[0] - b[0]]) / max(segs[j], 1e-6)
        for q in range(nseg):
            u = q / nseg
            wob = 0.0 if j in straight else 0.01 * math.sin(u * PI) * math.sin(u * 7 + j) + \
                rf.uniform(-0.004, 0.004) * math.sin(u * PI)
            pts.append(a + (b - a) * u + nrm_e * wob)
            st.append(j in straight and 0 < q)
            sid.append(front_seg.get(j, -1))
    return np.array(pts), np.array(st), np.array(sid)


def path_flags(part, rng, flags, step_index=0):
    """Worn path flags set INTO the ground (kit component). flags: list of (cx, cy, L, W, z_high, thk).
    Ordinary flags stand 1.0-2.5 cm proud on the high side and 0-1 cm on the low side (0.5-1 deg tilt); the
    step stone keeps its height. 0.5-1 cm arris broken by chips, 1-2 crisp straight fracture edges, an M_earth
    soil fillet 3-6 cm wide round every flag, gravel bedded in the joints (40-70 % buried)."""
    outlines = []
    for fi_, (cx, cy, Lf, Wf, ztop, thk) in enumerate(flags):
        step = fi_ == step_index
        O, st, sid = flag_outline(rng, Lf, Wf, front_facets=int(rng.integers(2, 4)) if step else 0)
        mm = len(O)
        rad = np.linalg.norm(O, axis=1)
        if step:
            ztf = np.full(mm, ztop)
            tdir = np.array([1.0, 0.0])
        else:
            ta = rng.uniform(0, 2 * PI)
            tdir = np.array([math.cos(ta), math.sin(ta)])
            tilt = math.tan(rng.uniform(0.6, 1.0) * D2R)
            proj = O @ tdir
            ztf = ztop - tilt * (proj - proj.min())
            ztf = np.maximum(ztf, 0.003)
        # rings: interior (top undulation), arris insets, side down to the ground (no bed: it is buried)
        inner_f = [0.18, 0.36, 0.52, 0.66, 0.78, 0.87, 0.94]
        rings = []
        for f in inner_f:
            xy = O * f
            zz = np.interp(xy @ tdir, O @ tdir, ztf) if not step else np.full(mm, ztop)
            rings.append(np.concatenate([xy, zz[:, None]], 1))
        # arris: 0.5-1.0 cm, crisp (<= 3 mm) along the straight fracture edges
        d_ar = np.where(st, 0.003, rng.uniform(0.005, 0.010)) * (1 + 0.25 * np.sin(np.arange(mm) * 0.31 + fi_))
        if step:        # round 6: the step's split front keeps a 0.5-1 cm arris (crisp, not a rolled nose)
            d_ar = np.where(sid >= 0, rng.uniform(0.005, 0.009), d_ar)
        dz_ar = np.where(st, 0.002, d_ar * 0.8)
        dz_ar = np.where(sid >= 0, d_ar * 0.9, dz_ar)
        for d_, dz_ in ((d_ar * 1.8, 0.0), (d_ar * 0.45, dz_ar * 0.45), (0.0 * d_ar, dz_ar)):
            xy = O * (1 - d_ / rad)[:, None]
            rings.append(np.concatenate([xy, (ztf - dz_)[:, None]], 1))
        # round 6 (director r5 #3b): the side below the arris is ONE irregular split face - a kinked ring
        # 0.8-1.5 cm under the arris wanders +-3 mm in and out; the soil fillet starts on this face >= 1.2 cm
        # below the arris (no horizontal shelf). The step's front facets are planar with their own batter.
        nrm2 = O / rad[:, None]
        ph_s = rng.uniform(0, 2 * PI, 2)
        jag = 0.0022 * np.sin(np.arange(mm) * 0.9 + ph_s[0]) + 0.0012 * np.sin(np.arange(mm) * 2.3 + ph_s[1])
        def circ_smooth(v, k=5):
            ker = np.ones(k) / k
            return np.convolve(np.concatenate([v[-k:], v, v[:k]]), ker, mode="same")[k:-k]
        jag *= 1 - 0.7 * circ_smooth(st.astype(float))
        bat = np.zeros(mm)
        if step:
            for q in range(int(sid.max()) + 1):
                bat[sid == q] = rng.uniform(0.004, 0.016)
            bat = circ_smooth(circ_smooth(bat, 3), 3)        # facets meet on a kink, never a crack
            jag *= 1 - circ_smooth((sid >= 0).astype(float))
        zmid = ztf - dz_ar - rng.uniform(0.008, 0.015)
        fmid = np.clip((ztf - dz_ar - zmid) / np.maximum(ztf - dz_ar + 0.03, 0.01), 0, 1)
        rings.append(np.concatenate([O + nrm2 * (jag + bat * fmid)[:, None], zmid[:, None]], 1))
        rings.append(np.concatenate([O + nrm2 * bat[:, None], np.full((mm, 1), -0.03)], 1))
        Pf = np.array(rings)
        nr_ = len(rings)
        # round 5: low-frequency undulation of the whole worn top and arris (+-5-8 mm), not just the centre
        topm = np.arange(nr_) < nr_ - 1
        ph_ = rng.uniform(0, 2 * PI, 3)
        un = rng.uniform(0.005, 0.0065) * np.sin(Pf[..., 0] * 4.1 + ph_[0]) * np.sin(Pf[..., 1] * 5.3 + ph_[1]) + \
            0.0018 * np.sin(Pf[..., 0] * 9.5 - Pf[..., 1] * 7.7 + ph_[2])
        if not step:
            Pf[..., 2] += un * topm[:, None]
            Pf[:-1, :, 2] = np.maximum(Pf[:-1, :, 2], 0.004)
        else:           # round 6: the step's top undulates +-5 mm too (no cast-concrete plane)
            Pf[..., 2] += un * (0.005 / 0.0083) * topm[:, None]
        # 1-2 crisp spalls (1-2 cm deep) knocked off the exposed top arris: flat-bottomed scar with 1-vertex
        # ramps, sloping back from the edge to nothing ~2 cm in
        KA = len(inner_f)
        for _ in range(int(rng.integers(1, 3))):
            j0 = int(rng.integers(0, mm))
            dj = np.abs((np.arange(mm) - j0 + mm // 2) % mm - mm // 2)
            w_ = np.clip((rng.uniform(2.0, 4.0) - dj) / 1.0, 0, 1)
            dep = min(rng.uniform(0.010, 0.020), 0.8 * float(Pf[KA, j0, 2]))
            for k in (KA - 1, KA, KA + 1, KA + 2):
                Pf[k, :, 2] -= w_ * dep * (0.25 if k == KA - 1 else 1.0)
                Pf[k, :, :2] *= (1 - w_ * (0.03 if k >= KA else 0.0))[:, None]
        Pf[KA + 3, :, 2] = np.minimum(Pf[KA + 3, :, 2], Pf[KA + 2, :, 2] - 0.004)   # split face stays below the arris
        if step:
            front = np.clip(-Pf[..., 1] / (Wf / 2), 0, 1) ** 3
            hol = 0.026 * np.exp(-(Pf[..., 0] / 0.2) ** 2) * front
            Pf[..., 2] -= hol * (np.arange(nr_) <= KA + 2)[:, None]
        Pf[..., 0] += cx
        Pf[..., 1] += cy
        V = Pf.reshape(1, -1, 3)
        Tf = tmpl_rings(nr_, mm, cap0=True, cap1=False)
        V = add_caps(V, Tf)
        Tf = orient_open(Tf, V[0])
        part.add(V, Tf, mat="M_stone", smooth="bevel", wear=0.75)
        outlines.append((O + np.array([cx, cy]), ztf, d_ar))
        # soil fillet: from inside the side (just under the arris) out 3-6 cm to the ground, slightly concave
        wf = rng.uniform(0.03, 0.06) * (1 + 0.3 * np.sin(np.arange(mm) * 0.2 + fi_))
        nrm2 = O / rad[:, None]
        zin = np.maximum(Pf[len(inner_f) + 2, :, 2] - rng.uniform(0.012, 0.02), 0.0) * (0.55 if step else 1.0)
        # round 5: CONCAVE fillet 3-8 cm wide, z = zin (1 - f)^2.6, meeting the ground tangentially
        wf = rng.uniform(0.03, 0.08) * (1 + 0.3 * np.sin(np.arange(mm) * 0.2 + fi_ + rng.uniform(0, 6)))
        wf = np.clip(wf, 0.03, 0.08)
        rows = []
        side_off = bat * 0.5 if step else np.zeros(mm)
        for f in (0.0, 0.1, 0.24, 0.42, 0.62, 0.82, 1.0):
            off = -0.003 + side_off + (wf + 0.003) * f
            zf = (zin + 0.005) * (1 - f) ** 2.6 - 0.005
            rows.append(np.concatenate([O + nrm2 * off[:, None] + np.array([cx, cy]), zf[:, None]], 1))
        G = np.stack(rows, 1)
        nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
        add_grid(part, "M_earth", G, wrap=True, flip=bool(nrm_[2] < 0))
    # round 6 (director r5 #3a): no strings of chips - 0-2 irregular 2-5 cm split chips per flag, half buried,
    # set 4-12 cm off its edge line
    gp, gs = [], []
    for (O, _, _) in outlines:
        c = O.mean(0)
        for _ in range(int(rng.integers(0, 3))):
            j = int(rng.integers(0, len(O)))
            out = (O[j] - c) / np.linalg.norm(O[j] - c)
            gp.append(O[j] + out * rng.uniform(0.04, 0.12) + rng.normal(0, 0.02, 2))
            gs.append(rng.uniform(0.02, 0.05))
    gp = np.array(gp).reshape(-1, 2)
    gs = np.array(gs)
    okg = np.hypot(gp[:, 0], gp[:, 1]) > R_BASE0 + 0.12
    gp, gs = gp[okg], gs[okg]
    Ng = len(gp)
    if Ng:
        settled_stones(part, rng, gp, gs * rng.uniform(1.0, 1.5, Ng), gs * rng.uniform(0.6, 0.95, Ng),
                       gs * rng.uniform(0.5, 0.8, Ng), bury=(0.45, 0.55), style="gravel", collar=None,
                       tilt_range=(8.0, 25.0))
    log("path flags %d (tops %s), gravel in joints %d" % (len(flags), [round(float(o[1].max()), 3) for o in outlines], Ng))


def orient_open(T, P0):
    """Winding for an open ring surface (flag top + sides): the top centre fan must face up."""
    t = T["tris"][0]
    a, b, c = P0[t]
    return flip_tmpl(T) if np.cross(b - a, c - a)[2] < 0 else T


def hull_sdist(H, X):
    """Signed distance (negative inside) from points X (n,2) to the convex CCW polygon H (k,2)."""
    A = H
    B = np.roll(H, -1, 0)
    E = B - A
    L2 = np.maximum((E ** 2).sum(1), 1e-12)
    t = np.clip(((X[:, None, :] - A[None]) * E[None]).sum(2) / L2[None], 0, 1)
    Q = A[None] + t[..., None] * E[None]
    d = np.sqrt(((X[:, None, :] - Q) ** 2).sum(2)).min(1)
    cr = E[None, :, 0] * (X[:, None, 1] - A[None, :, 1]) - E[None, :, 1] * (X[:, None, 0] - A[None, :, 0])
    inside = (cr >= 0).all(1)
    return np.where(inside, -d, d)


def cluster_collar(part, stones, z_end=-0.005, cell=0.016):
    """Round 6 (director r5 #1): ONE shared soil collar per rubble cluster, as a height field: round each
    stone's ground outline (convex hull of its vertices at the ground cut) the soil climbs hc (0.6-3.5 cm)
    and runs out over w (3-8 cm) as z = hc (1 - d / w)^2.6 - tangential to the ground, no crest, no step;
    neighbouring stones share it (max of the profiles). Cells deep inside a stone (hidden) or flat on the
    ground are not modelled. stones: list of (W (nv,3), hc, w)."""
    hulls, hcs, ws = [], [], []
    for W, hc, w in stones:
        g = W[W[:, 2] < 0.012, :2]
        if len(g) < 3:
            continue
        h_ = hull2d(g)
        if len(h_) < 3:
            continue
        hulls.append(h_)
        hcs.append(hc)
        ws.append(w)
    if not hulls:
        return 0
    allp = np.concatenate(hulls)
    lo = allp.min(0) - max(ws) - 0.02
    hi = allp.max(0) + max(ws) + 0.02
    nx = int(math.ceil((hi[0] - lo[0]) / cell)) + 1
    ny = int(math.ceil((hi[1] - lo[1]) / cell)) + 1
    X, Y = np.meshgrid(lo[0] + np.arange(nx) * cell, lo[1] + np.arange(ny) * cell, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel()], 1)
    Z = np.zeros(len(pts))
    inside_deep = np.zeros(len(pts), bool)
    for h_, hc, w in zip(hulls, hcs, ws):
        sd = hull_sdist(h_, pts)
        prof = np.where(sd > 0, hc * np.clip(1 - sd / w, 0, 1) ** 2.6, hc + 0.3 * np.minimum(-sd, 0.03))
        Z = np.maximum(Z, prof)
        inside_deep |= sd < -0.03
    Z = Z.reshape(nx, ny)
    inside_deep = inside_deep.reshape(nx, ny)
    flat = Z <= 1e-5
    cf = flat[:-1, :-1] & flat[1:, :-1] & flat[:-1, 1:] & flat[1:, 1:]
    ci = inside_deep[:-1, :-1] & inside_deep[1:, :-1] & inside_deep[:-1, 1:] & inside_deep[1:, 1:]
    keep = ~cf & ~ci
    G = np.stack([X, Y, Z + z_end], -1)
    add_grid(part, "M_earth", G, keep=keep, flip=False)
    return int(keep.sum())


def build_ground(parts):
    """Round 6 (director r5 #1): 45-60 rubble stones in 5 clusters hugging the footing course (0-0.6 m from the
    drum face) at the -X prop side, the +X side, the rear and either side of the path; 8-12 of them are
    0.20-0.45 m stones buried 40-60 % (6-15 cm proud, tilted beds, crisp fractured top arris), the rest
    0.05-0.15 m buried 30-50 %; one shared, tangential soil collar per cluster. The open field stays clear."""
    P_r = parts["rubble"]
    rng = RNG("ground_rubble_r6")
    r_face = R_BASE0 + 0.07                               # footing course face
    # cluster centre azimuths (deg; 0 = front -Y, +90 = +X): prop side, +X side, rear, path left / right
    clusters = [(-92.0, 11, 2), (88.0, 11, 2), (176.0, 10, 2), (-27.0, 10, 2), (27.0, 9, 2)]
    allW, n_big, n_all = [], 0, 0
    for ci_, (az, n, nb) in enumerate(clusters):
        th0 = az * D2R
        xy, big = [], []
        sizes = np.concatenate([rng.uniform(0.22, 0.44, nb), np.exp(rng.uniform(np.log(0.05), np.log(0.15), n - nb))])
        for q, sz in enumerate(sizes):
            for _try in range(60):
                if q < nb:
                    dr = sz * 0.5 + rng.uniform(0.0, 0.12)                 # big ones lean on the footing
                    du = rng.uniform(-0.45, 0.45)
                else:
                    dr = sz * 0.5 + rng.uniform(0.0, 0.55)
                    du = rng.uniform(-0.75, 0.75)
                th = th0 + du / r_face
                rr_ = r_face + dr
                c_ = np.array([rr_ * math.sin(th), -rr_ * math.cos(th)])
                if abs(c_[0]) < 0.85 and c_[1] < 0:                       # keep the path clear
                    continue
                ok = all(np.hypot(*(c_ - xy[j])) > 0.5 * (sz + sizes[j]) * 0.92 for j in range(len(xy)))
                if ok:
                    xy.append(c_)
                    big.append(q < nb)
                    break
        xy = np.array(xy)
        big = np.array(big)
        Nc = len(xy)
        sz = sizes[:Nc]
        stones = []
        for sel, kind in ((big, "big"), (~big, "small")):
            if not sel.any():
                continue
            ns = int(sel.sum())
            L = sz[sel] * rng.uniform(1.0, 1.25, ns)
            Wd = sz[sel] * rng.uniform(0.65, 0.9, ns)
            if kind == "big":
                bur = rng.uniform(0.40, 0.60, ns)
                ex = rng.uniform(0.06, 0.15, ns)
                Hh = np.clip(ex / (1 - bur), 0.10, 0.34)
                W_ = settled_stones(P_r, rng, xy[sel], L, Wd, Hh, style="ground_big", collar=None,
                                    expose_abs=np.minimum(ex, Hh * (1 - bur)), tilt_range=(6.0, 16.0), mat="M_rubble")
                hc = rng.uniform(0.018, 0.035, ns)
                wc = rng.uniform(0.05, 0.08, ns)
                n_big += ns
            else:
                bur = rng.uniform(0.30, 0.50, ns)
                Hh = sz[sel] * rng.uniform(0.45, 0.7, ns)
                W_ = settled_stones(P_r, rng, xy[sel], L, Wd, Hh, bury=(0.30, 0.50), style="ground",
                                    collar=None, tilt_range=(5.0, 20.0), mat="M_rubble")
                hc = np.minimum(rng.uniform(0.006, 0.014, ns), 0.5 * W_[:, :, 2].max(1))
                wc = rng.uniform(0.03, 0.05, ns)
            for i in range(ns):
                stones.append((W_[i], float(hc[i]), float(wc[i])))
        ncell = cluster_collar(P_r, stones)
        n_all += Nc
        log("ground cluster %d (az %+.0f): %d stones (%d big), shared collar %d cells" % (ci_, az, Nc, int(big.sum()), ncell))
    log("ground rubble %d settled split stones in %d clusters (%d of 0.20-0.45 m, 6-15 cm proud)"
        % (n_all, len(clusters), n_big))
    rf = RNG("path_flags")
    dy_ = R_BASE0 - 2.60                                  # kit: the path starts at the drum's door
    path_flags(P_r, rf, [(0.0, -2.95 - dy_, 1.25, 0.60, 0.075, 0.12), (0.15, -3.62 - dy_, 0.95, 0.62, 0.021, 0.10),
                         (-0.2, -4.30 - dy_, 0.85, 0.60, 0.019, 0.095), (0.45, -4.85 - dy_, 0.60, 0.45, 0.017, 0.085)])


# =============================================================================================
# C. CURB + SHINGLE APRON
# =============================================================================================
AP_RE = 3.17                       # eave radius of the shake bed
AP_ZE = 4.50 + DZ                  # bed height at the eave (4.62)
AP_RT = 1.60                       # top radius (tower foot)
AP_ZT = 6.00                       # tower foot: apron ~41 deg (art bible 35-45)
AP_A = math.atan2(AP_ZT - AP_ZE, AP_RE - AP_RT)
AP_COURSES = 3


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


def shake_local(rng, L, W, tb=(0.025, 0.035), tt=0.008, comb=0.0, T=None):
    """Split shake (T_SHK2): x = length (butt at -L/2), y = thickness from the bed up, z = width.
    Thickness tapers from a 2.5-3.5 cm butt to a 0.8 cm head; split, tapered outline (each long edge
    wanders +-2 cm and the head is narrower); slight cup or crown; ragged, uneven butt."""
    N = len(L)
    T = T_SHK2 if T is None else T
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


def eave_fascia(part, rng, r_out, z_top, n=16, t=0.03, H=(0.14, 0.18), wave_fn=None):
    """Polygonal eave fascia (kit component): n straight boards (0.9-1.3 m chords), 2.5-3.5 cm thick, 14-18 cm
    deep, butt joints with 3-6 mm gaps and ends cut to the polygon; +-5 mm height and +-3 mm out-of-plane per
    board, worn lower arris, following the low-frequency eave wave. r_out: outer-face radius at the polygon
    vertices; z_top: top edge height. Returns the vertex angles and the inner-face radius per vertex (the
    sarking edge)."""
    wave_fn = apron_wave if wave_fn is None else wave_fn
    base = rng.uniform(0, 2 * PI / n)
    w_ = rng.uniform(0.8, 1.2, n)
    ang = base + np.concatenate([[0], np.cumsum(w_)[:-1]]) / w_.sum() * 2 * PI
    nxt = np.append(ang[1:], ang[0] + 2 * PI)
    Z3 = np.array([0, 0, 1.0])
    d_in = np.zeros(n)
    for k in range(n):
        a0, a1 = ang[k], nxt[k]
        half = (a1 - a0) / 2
        am = (a0 + a1) / 2
        nrm = np.array([math.sin(am), -math.cos(am), 0.0])
        tan = np.cross(nrm, Z3)
        tk = rng.uniform(0.025, 0.035)
        Hk = rng.uniform(*H)
        d_out = r_out * math.cos(half)
        L = 2 * r_out * math.sin(half) - rng.uniform(0.003, 0.006)
        h = np.array([[L / 2, tk / 2, Hk / 2]])
        P = rbox(T_BRD, h, np.array([[0.004, 0.004, 0.004]]))
        yl = P[0, :, 1].copy()
        # worn lower outer arris (8-14 mm), varying along the board
        wr = rng.uniform(0.008, 0.014) * (1 + 0.3 * np.sin(P[0, :, 0] * 7 + k))
        on_face = yl > tk / 2 - 1e-6
        on_bot = P[0, :, 2] < -Hk / 2 + 1e-6
        low = P[0, :, 2] < -(Hk / 2 - 0.004) + 1e-6
        outr = yl > tk / 2 - 0.004 - 1e-6
        P[0, :, 2] = np.where(on_face & low, np.maximum(P[0, :, 2], -(Hk / 2 - wr)), P[0, :, 2])
        P[0, :, 1] = np.where(on_bot & outr, np.minimum(P[0, :, 1], tk / 2 - wr * 0.8), P[0, :, 1])
        # ends cut to the polygon (mitre along the radial bisector): the inner face is shorter
        P[0, :, 0] += np.sign(P[0, :, 0]) * (P[0, :, 1] - tk / 2) * math.tan(half)
        # out of plane +-3 mm, height +-5 mm, eave wave (linear between the board's end vertices)
        u = P[0, :, 0] / (L / 2)
        P[0, :, 1] += rng.uniform(-0.003, 0.003) + rng.uniform(-0.002, 0.002) * u
        zw = (wave_fn(a0) * (1 - u) + wave_fn(a1) * (1 + u)) / 2 * 0.97
        ctr = nrm * (d_out - tk / 2) + np.array([0, 0, z_top - Hk / 2 + rng.uniform(-0.005, 0.005)])
        W = P[0] @ np.stack([tan, nrm, Z3], 1).T + ctr
        W[:, 2] += zw
        part.add(W[None], T_BRD, Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.6)
        d_in[k] = d_out - tk - 0.004

    def r_edge(phi):
        """radius of the fascia's inner face (polygon) at azimuth phi -> the sarking edge"""
        phi = np.asarray(phi, float)
        k = (np.searchsorted(ang, (phi - ang[0]) % (2 * PI) + ang[0], side="right") - 1) % n
        am = (ang[k] + nxt[k]) / 2
        return d_in[k] / np.cos(((phi - am + PI) % (2 * PI)) - PI)
    return ang[0], r_edge


def tower_foot_flashing(part, rng, bed_fn, z_top=None):
    """One vertical flashing board per octagon face over the tower sill (kit component), its lower edge scribed
    to the shakes, ends lapped over the neighbours (alternate boards stand 2.6 cm further out)."""
    z_sill = float(TZ(5.41))
    z_top = z_sill + 0.165 if z_top is None else z_top
    for k in range(8):
        n_, t_ = face_axes(k)
        d = float(tw_a(z_sill)) - 0.03 + 0.12 + 0.006 + (0.026 if k % 2 else 0.0)
        L = 2 * d * math.tan(PI / 8) + (0.09 if k % 2 else 0.02)
        tk = rng.uniform(0.022, 0.028)
        h = np.array([[L / 2, tk / 2, 0.5]])
        P = rbox(T_BRD, h, np.array([[0.004, 0.004, 0.01]]))
        x = P[0, :, 0]
        r = np.hypot(d + tk / 2, x)
        # round 5: STRAIGHT drip edge at the level the shakes reach at the board ends; the top shake course
        # tucks under the board (no scalloped scribed frill seen from above)
        zb = float(bed_fn(r).min()) + 0.03 + rng.uniform(-0.003, 0.003) + 0.002 * x / (L / 2)
        zt = z_top + rng.uniform(-0.006, 0.006) + 0.004 * x / (L / 2)
        zz = zb + (P[0, :, 2] + 0.5) * (zt - zb)
        W = (d + tk / 2 + P[0, :, 1] + rng.uniform(-0.002, 0.002))[:, None] * n_ + x[:, None] * t_ + \
            zz[:, None] * np.array([0, 0, 1.0])
        part.add(W[None], orient(T_BRD, W), Pl=P, mat="M_timber_weathered", smooth="bevel", wear=0.55)


def build_apron(parts):
    P_c, P_s, P_r = parts["curb"], parts["apron"], parts["apron_frame"]
    rng = RNG("apron")
    ca, sa = math.cos(AP_A), math.sin(AP_A)
    # stone kerb inside (carries the tower sill; hidden behind rafters)
    # (the stone kerb under the tower sill is fully enclosed by the apron: not modelled)
    # timber curb on the cornice (16 lapped segments, 0.22 x 0.24)
    n = 16
    rc = 2.30
    ph = np.arange(n) * 2 * PI / n + rng.uniform(-0.01, 0.01, n)
    a = np.stack([rc * np.sin(ph - PI / n - 0.05), -rc * np.cos(ph - PI / n - 0.05), np.full(n, 4.62 + DZ)], 1)
    b = np.stack([rc * np.sin(ph + PI / n + 0.05), -rc * np.cos(ph + PI / n + 0.05), np.full(n, 4.62 + DZ)], 1)
    # (the curb ring is wholly enclosed under the apron: not modelled)
    # rafters (32) from the kerb to past the eave
    nr = 32
    ph = (np.arange(nr) + 0.5) * 2 * PI / nr

    def bed(r):
        return AP_ZE + (AP_RE - r) * math.tan(AP_A)
    rr0, rr1 = AP_RE - 0.67, AP_RE - 0.05   # rafter feet only: above the cornice they are enclosed by the apron
    off = -0.025 - 0.02 - 0.06  # below batten + sarking, centre of a 0.12 rafter
    er0 = np.stack([np.sin(ph), -np.cos(ph), np.zeros(nr)], 1)
    nn = np.stack([sa * er0[:, 0], sa * er0[:, 1], np.full(nr, ca)], 1)
    a = er0 * rr0 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr0))], 1) + nn * off
    b = er0 * rr1 + np.stack([0 * ph, 0 * ph, np.full(nr, bed(rr1))], 1) + nn * off
    member(P_r, "M_timber", a, b, 0.08, 0.12, up=(0, 0, 1), c=0.012, rng=rng, bow=0.01)
    # eave fascia (round 4): 16 straight boards on a polygon, butt-jointed, ends cut to the polygon, eave wave
    a_first, r_edge_fn = eave_fascia(P_r, rng, AP_RE + 0.0, bed(AP_RE) - 0.025, n=16)
    # sarking: a closed board shell (2 cm) from the tower foot out to the fascia's inner face (polygonal edge,
    # following the eave wave) -> no see-through, and its end grain is covered by the fascia
    na = 16 * 9
    aa = np.linspace(0, 2 * PI, na, endpoint=False) + a_first
    r_edge = r_edge_fn(aa)
    fr_ = np.linspace(0, 1, 6)
    R_ = (AP_RT - 0.05) + (r_edge[:, None] - (AP_RT - 0.05)) * fr_[None]
    wave_ = apron_wave(aa)[:, None] * np.clip(1 - (AP_RE - R_) / ca / 2.0, 0, 1)
    Zt = bed(R_) - 0.025 + wave_
    top = np.stack([R_ * np.sin(aa)[:, None], -R_ * np.cos(aa)[:, None], Zt], 2)
    bot = top - np.array([0, 0, 0.022])
    add_grid(P_r, "M_timber", top, wrap=True, flip=True, smooth="none")
    add_grid(P_r, "M_timber", bot, wrap=True, flip=False, smooth="none")
    add_grid(P_r, "M_timber", np.stack([bot[:, -1], top[:, -1]], 1), wrap=True, flip=True, smooth="none")
    # tower-foot flashing: one vertical board per octagon face over the sill, scribed to the shakes, lapped
    tower_foot_flashing(P_r, rng, bed)
    # shakes: 3 visible courses, each double layered (offset under-layer), long split shakes.
    # Lift per layer is a fixed offset normal to the bed (no per-shake pitch blow-up), the under-layer is
    # complete, and only isolated top-layer shakes are missing (exposing the under-layer).
    slope_len = (AP_RE - AP_RT) / ca
    # AP_COURSES visible courses of 0.72-0.84 m shakes (3 over this mill's 2.09 m slope at 41 deg)
    courses = [i * (slope_len - 0.73) / max(AP_COURSES - 1, 1) for i in range(AP_COURSES)]
    stats = 0
    for ci, sb in enumerate(courses):
        rb_ = AP_RE - sb * ca
        C = 2 * PI * rb_
        for layer in (1,):          # single layer (the under-layer was ~all hidden); sarking shows in the gaps
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
                a_t = AP_RT - 0.02
                rel = (phc + PI / 8) % (PI / 4) - PI / 8
                r_face = a_t / np.cos(rel) + 0.012
                L = np.clip((rb_ - r_face) / ca + rng.uniform(-0.01, 0.06, N), 0.3, None)
                comb = 0.04
            sbb = sb - (0.04 if layer == 0 else 0.0) - (0.045 if ci == 0 else 0.0) + rng.uniform(-0.02, 0.02, N)
            W = widths * rng.uniform(0.93, 1.0, N)
            Tsh = T_SHK2_O               # the sarking runs out past every eave butt, so no bed face is ever seen
            P = shake_local(rng, L, W, comb=comb, T=Tsh)
            # a few slipped shakes (2-3 %) hang 4-7 cm low instead of leaving holes
            slip = rng.random(N) < 0.025
            sbb = sbb - np.where(slip, rng.uniform(0.04, 0.07, N), 0.0)
            keep = np.ones(N, bool)
            # lift: courses below (butt) -> straight plane, slight pitch only
            ob = 0.004 + (0.028 if ci > 0 else 0.0)
            ot = 0.002
            beta = np.arctan2(ob - ot, np.maximum(L, 0.6)) + rng.uniform(-0.004, 0.008, N)
            Rf, er, nrm = cone_frame(phc, AP_A)
            Rl = rotm([0, 0, 1], -beta) @ rotm([0, 1, 0], rng.normal(0, 2.0 * D2R, N))
            sc = sbb + L / 2
            wave = apron_wave(phc) * np.clip(1 - sc / 2.0, 0, 1)
            ctr = er * (AP_RE - sc * ca)[:, None] + np.stack([0 * sc, 0 * sc, AP_ZE + sc * sa + wave], 1) \
                + nrm * ((ob + ot) / 2 + rng.uniform(-0.002, 0.004, N))[:, None]
            Wd = xform(P, Rf @ Rl, ctr)
            P_s.add(Wd[keep], Tsh, Pl=P[keep], mat="M_roof_shake", smooth="bevel")
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
    splits = {(7, 0), (1, 0), (6, 1), (0, 0), (0, 2), (6, 0), (6, 2), (7, 2)}   # split board ends (hero faces)
    cupped = {(0, 0), (6, 1), (7, 2)}                                            # strongly cupped boards (6-10 mm)
    patch_at = (7, 1)
    nb_total = 0
    ncup_total = [0]
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
                tot += w + 0.011
            if tot - 2 * hw > 0.5 * ws[-1] and len(ws) > 1:
                tot -= ws.pop() + 0.011
            ws = np.array(ws) * 2 * hw / tot
            lc = -hw + np.cumsum(ws + 0.011 * 2 * hw / tot) - ws / 2 - 0.0055
            N = len(ws)
            isplit = int(rng.integers(0, N)) if (k, li) in splits else -1
            ipatch = int(rng.integers(1, N - 1)) if (k, li) == patch_at else -1
            pieces = []   # (lateral centre, width, z bottom, z top, extra skew deg)
            icup = int(rng.integers(0, N)) if (k, li) in cupped else -1
            cup_of = []
            # 1-2 staggered horizontal butt joints across the face between the rails, 1-2 cm drip gaps
            nj = int(rng.integers(1, 3))
            zj = np.sort(rng.uniform(z0 + 0.35, z1 - 0.35, nj))
            if nj == 2 and zj[1] - zj[0] < 0.3:
                zj[1] = min(zj[0] + 0.3, z1 - 0.3)
            for i in range(N):
                zb = z0 + rng.uniform(-0.03, 0.03)
                zt = z1 + rng.uniform(-0.01, 0.015)
                n0 = len(pieces)
                if k == hatch["k"] and li == 1 and abs(lc[i]) - ws[i] / 2 < hatch["l"] + 0.02:
                    pieces.append((lc[i], ws[i], zb, hatch["z0"] - 0.04, 0.0))
                    pieces.append((lc[i], ws[i], hatch["z1"] + 0.06, zt, 0.0))
                elif rng.random() < 0.7 and i != isplit:
                    zc_j = zj[i % nj] + rng.uniform(-0.04, 0.04)
                    g = rng.uniform(0.01, 0.02) / 2
                    pieces.append((lc[i], ws[i], zb, zc_j - g, 0.0))
                    pieces.append((lc[i], ws[i], zc_j + g, zt, 0.0))
                elif i == isplit:
                    # split end: the bottom 0.26 m is cracked into two halves, one sprung outward/sideways
                    zs_ = zb + 0.26
                    pieces.append((lc[i], ws[i], zs_ - 0.004, zt, 0.0))
                    hw2 = ws[i] / 2 - 0.004
                    pieces.append((lc[i] - ws[i] / 4 - 0.002, hw2, zb, zs_ + 0.01, 0.0))
                    pieces.append((lc[i] + ws[i] / 4 + 0.004, hw2, zb + 0.015, zs_ + 0.01, 2.2))
                else:
                    pieces.append((lc[i], ws[i], zb, zt, 0.0))
                cup_of.extend([i == icup] * (len(pieces) - n0))
                if i == ipatch:
                    zp = zm + rng.uniform(-0.3, 0.1)
                    patches.append((k, lc[i], ws[i] + 0.03, zp - 0.28, zp + 0.28))
            pc = np.array(pieces)
            N = len(pc)
            Lz = pc[:, 3] - pc[:, 2]
            h = np.stack([Lz / 2, np.full(N, 0.015), pc[:, 1] / 2], 1)
            P = rbox(T_BRD_O3, h, np.stack([np.full(N, 0.006), np.full(N, 0.006), np.full(N, 0.008)], 1))
            u = P[:, :, 0] / h[:, None, 0]
            # cup, bow, loose boards
            cupf = np.array(cup_of, bool)
            cupa = np.where(cupf, rng.uniform(0.006, 0.010, N) * rng.choice([-1, 1], N), rng.uniform(-0.004, 0.004, N))
            P[:, :, 1] += cupa[:, None] * ((P[:, :, 2] / h[:, None, 2]) ** 2 - 0.5)
            ncup_total[0] += int(cupf.sum() > 0)
            P[:, :, 1] += rng.uniform(-0.006, 0.008, N)[:, None] * (1 - u ** 2)
            loose = rng.random(N) < 0.05
            # each board leans up to +-0.5 deg, a few loose ones up to 1 deg
            skew = (np.where(loose, rng.uniform(-1.0, 1.0, N), np.clip(rng.normal(0, 0.3, N), -0.5, 0.5))
                    + pc[:, 4]) * D2R
            yoff = 0.015 + np.where(loose, rng.uniform(0.006, 0.014, N), rng.uniform(-0.004, 0.004, N))
            yoff = yoff + np.where(pc[:, 4] > 0, 0.012, 0.0)
            zc = (pc[:, 2] + pc[:, 3]) / 2
            zz = zc[:, None] + P[:, :, 0]
            # split halves spring outward toward their free end
            sprung = (pc[:, 4] > 0)[:, None] * np.clip((pc[:, 2:3] + 0.27 - zz) / 0.27, 0, 1) * 0.012
            ll = pc[:, 0][:, None] + P[:, :, 2] + skew[:, None] * P[:, :, 0]
            scale = (tw_a(zz) + 0.03) / (float(tw_a(zm)) + 0.03)
            yy = yoff[:, None] + P[:, :, 1] + sprung
            W = face_map(k, ll * scale, zz, yy)
            # inner faces never seen; top ends tucked under a rail / the curb are not modelled either
            covered_top = pc[:, 3] > z1 - 0.03
            covered_bot = pc[:, 2] < z0 + 0.035              # on the sill / tucked behind the rail below
            for sel_, Tq in ((covered_top & covered_bot, T_BRD_O3TB), (covered_top & ~covered_bot, T_BRD_O3T),
                             (~covered_top & covered_bot, T_BRD_O3B), (~covered_top & ~covered_bot, T_BRD_O3)):
                if sel_.any():
                    P_b.add(W[sel_], Tq, Pl=P[sel_], mat="M_timber_weathered", smooth="bevel")
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
                member(P_b, "M_timber_weathered", pa, pb, 0.045, 0.018, up=n, c=0.005, rng=rng, bow=0.004, T=T_PLK_NI)
    log("tower boards %d pieces, %d strongly cupped boards, %d split ends" % (nb_total, ncup_total[0], len(splits)))
    # patched board: a short plank nailed over a rotten one
    for (k, l0, w, zb, zt) in patches:
        n, t = face_axes(k)
        pa = face_map(k, np.array([l0 + 0.01]), np.array([zb]), np.array([0.058]))
        pb = face_map(k, np.array([l0 - 0.01]), np.array([zt]), np.array([0.058]))
        member(P_b, "M_timber_weathered", pa, pb, w, 0.022, up=n, c=0.005, rng=rng, bow=0.003, T=T_PLK_NI)
        nl_ = np.array([[l0 - w * 0.3, zb + 0.06], [l0 + w * 0.3, zb + 0.07], [l0 - w * 0.28, zt - 0.06],
                        [l0 + w * 0.3, zt - 0.07]])
        prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
        Pn, Tn = lathe(np.repeat(prof[None], 4, 0), 6, open_base=True)
        Rn = np.repeat(frame_mats(t[None], np.cross(n, t)[None], n[None]), 4, 0)
        P_i.add(xform(Pn, Rn, face_map(k, nl_[:, 0], nl_[:, 1], np.full(4, 0.069))), Tn, mat="M_iron", smooth="all")
    # corner (cant) posts, proud of the boards
    for k in range(8):
        phi = k * PI / 4 + PI / 8
        bis = np.array([math.sin(phi), -math.cos(phi), 0.0])
        za, zb = TW_Z0 - 0.1, ZCT - CURB_D - 0.005
        a = bis * float(post_geom(za)) + np.array([0, 0, za])
        b = bis * float(post_geom(zb)) + np.array([0, 0, zb])
        member(P_f, "M_timber", a[None], b[None], 0.2, 0.2, up=bis, c=0.025, rng=rng, bow=0.01, T=T_PLK_NI)

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
            member(part, mat, (pa - dd * ext)[None], (pb + dd * ext)[None], w, d, up=n, c=cc, rng=rng, bow=bow,
                   T=T_PLK_NI)
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
                         [[hw, 0.011, 0.055]], c=0.004, T=T_PLK_DB)
    # ---- top curb: circular, 8 timber segments joined by half-laps, two oak pegs per joint ----
    lap = 0.13 / CURB_R
    gap = 0.004 / CURB_R
    th_j = np.arange(8) * PI / 4 + 0.17 + rng.uniform(-0.05, 0.05, 8)
    dz_s = rng.uniform(-0.004, 0.004, 8)
    dr_s = rng.uniform(-0.005, 0.005, 8)

    def arc_piece(t0, t1, zc_, hd, rr, top_hidden=True):
        n = max(3, int((t1 - t0) * rr / 0.08) + 1)
        tt = np.linspace(t0, t1, n)
        path = np.stack([rr * np.sin(tt), -rr * np.cos(tt), np.full(n, zc_)], 1)[None]
        Pp, Tp = sweep(path, rect_prof(CURB_W, hd, 0.018 if hd > 0.15 else 0.01), up=(0, 0, 1))
        if top_hidden:      # the curb's top face is enclosed under the cap frame and valance
            mq = (np.arange(len(Tp["quads"])) % 8) != 2
            Tp = dict(Tp, quads=Tp["quads"][mq], qflat=Tp["qflat"][mq])
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
    Pg, Tg = lathe(np.repeat(prof[None], len(pegs), 0), 8, open_base=True)
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
    Pb_, Tb_ = lathe(np.repeat(prof[None], len(bolts), 0), 6, open_base=True)
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
CAP_AZ = 21 * D2R                # round 5: hub 0.70 m right of the axis -> the vane reads left of the tower from the ref1 camera
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
# tail boom (client correction): two hewn rails 0.10 x 0.12 m either side of the vane boards, passing out under
# the rear eave through a notch in the valance, 4.6 m beyond the cap
TB_Z = ZCT + 0.09                                  # rail centre height (11.55): 3 cm over the curb, under the soffit
TB_RW, TB_RH, TB_GAP = 0.10, 0.12, 0.028           # rail width / height, gap between the rails (vane boards)
TB_YC = TB_GAP / 2 + TB_RW / 2                     # rail centre offset from the cap axis
TB_X0, TB_X1 = -1.13, -6.08                        # cap-local x of the rail ends (cap rear eave at -1.48)


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


def sliver_keep(W0, Wl, tt, ee, min_w=0.05, T=T_SHK):
    """Shingles altered by hip / valley clamping keep only if the clamped outline is still >= 5 cm wide
    (minimum caliper width of its top face) -> no thin triangular slivers at hips and valleys."""
    N = len(Wl)
    keep = np.ones(N, bool)
    top_ = np.nonzero(T["idx"][:, 1] == T["n"][1] - 1)[0]
    moved = np.abs(Wl - W0).max(axis=(1, 2)) > 0.002
    tt = np.broadcast_to(tt, (N, 3))
    ee = np.broadcast_to(ee, (N, 3))
    for q in np.nonzero(moved)[0]:
        V = Wl[q, top_]
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

    def not_covered(Vi):
        Vl = to_cap_local(Vi.reshape(-1, 3)).reshape(Vi.shape)
        b = bf(Vl[..., 0].ravel(), Vl[..., 1].ravel()).reshape(Vi.shape[:2])
        under_board = np.isfinite(b).all(1)
        # ... or under a lead hip-end saddle (t >= 0.86 within 0.10 m of the ridge ends)
        tq = cap_t(Vl[..., 0], Vl[..., 1])
        sad = (tq >= 0.865) & ((Vl[..., 0] >= XR1 - 0.10) | (Vl[..., 0] <= XR0 + 0.10))
        return ~(under_board | sad.all(1))
    ncull = P_sh.filter_instances(not_covered)
    log("cap shingles wholly under the cappings (never visible): %d culled" % ncull)
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
        # (the lead underside lies on the shingles and is never seen: not modelled)
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
        # (the lead underside lies on the shingles and is never seen: not modelled)
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
    P, T = lathe(prof[None], 16, open_base=True)
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
    for s, (x0, x1) in [(s_, xr_) for s_ in (-1, 1) for xr_ in
                        ((SH_X[0] + rng.uniform(-0.01, 0.01), SH_X[0] + 0.40), (SH_X[1] - 0.40, SH_X[1] + rng.uniform(-0.01, 0.01)))]:
        # only the ends of the sheers show (outside the valance): each end is modelled as a 0.4 m stub
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
    # (cross beams, truck wheels and the breast beam sit wholly inside the valance box: not modelled)
    # ---- deck shell (sarking boards with real thickness) ----
    nx, ny = 46, 40
    xs = np.linspace(-CAP_AB - 0.03, CAP_AF + 0.03, nx)
    ys = np.linspace(-CAP_B - 0.03, CAP_B + 0.03, ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Zt = cap_z(X, Y) - 0.012
    # the deck's top skin is entirely under shingles / lead and its soffit inside the valance box is enclosed:
    # only the soffit outside the valance (seen from below) and the edge band are modelled
    Rpl = np.hypot(X, Y)
    rmax = np.maximum(np.maximum(Rpl[:-1, :-1], Rpl[1:, :-1]), np.maximum(Rpl[:-1, 1:], Rpl[1:, 1:]))
    add_grid(P_fr, "M_timber", capw(np.stack([X, Y, Zt - 0.035], 2)), keep=rmax > SKIRT_R - 0.04, flip=True)
    per = np.concatenate([np.stack([xs, np.full(nx, ys[0])], 1), np.stack([np.full(ny, xs[-1]), ys], 1)[1:],
                          np.stack([xs[::-1], np.full(nx, ys[-1])], 1)[1:], np.stack([np.full(ny, xs[0]), ys[::-1]], 1)[1:]])
    zt = cap_z(per[:, 0], per[:, 1]) - 0.012
    band = np.stack([np.stack([per[:, 0], per[:, 1], zt - 0.035], 1), np.stack([per[:, 0], per[:, 1], zt], 1)], 1)
    add_grid(P_fr, "M_timber", capw(band), flip=False)
    # sarking deck (round 4): a continuous board deck under every cap face, so a missing / slipped shingle or a
    # gap between courses shows boards, never sky or a void. Each face is a ruled strip between its hip lines
    # (the bell-cast profile varies only up the slope); boards 15-25 cm wide, 4 mm V joints between them.
    for fi in range(4):
        Rf = (CAP_EF, CAP_EB, CAP_SB, CAP_SB)[fi]
        t0 = -0.03 / Rf
        slope_len = float(np.sum(np.hypot(np.diff(CAP_DS), np.diff(CAP_HS)))) * Rf / CAP_SB
        ts = [t0]
        while ts[-1] < 1.0:
            ts.append(ts[-1] + rng.uniform(0.15, 0.25) / slope_len)
        ts[-1] = 1.0
        rows_t, rows_d = [], []
        for k in range(len(ts) - 1):
            a_, b_ = ts[k], ts[k + 1]
            e = 0.004 / slope_len
            for tq, dq in ((a_ + e, 0.0), (b_ - e, 0.0), (b_, -0.004)):
                rows_t.append(tq)
                rows_d.append(dq)
        rows_t = np.array([t0] + rows_t[:-1])
        rows_d = np.array([0.0] + rows_d[:-1])
        hw = CAP_B - rows_t * CAP_SB + 0.0
        if fi == 0:
            x = CAP_AF - rows_t * CAP_EF
            G = np.stack([np.stack([x, -hw, 0 * x], 1), np.stack([x, hw, 0 * x], 1)], 1)
        elif fi == 1:
            x = -CAP_AB + rows_t * CAP_EB
            G = np.stack([np.stack([x, hw, 0 * x], 1), np.stack([x, -hw, 0 * x], 1)], 1)
        else:
            sy = 1.0 if fi == 2 else -1.0
            y = sy * (CAP_B - rows_t * CAP_SB)
            xa = -CAP_AB + rows_t * CAP_EB
            xb = CAP_AF - rows_t * CAP_EF
            G = np.stack([np.stack([xa, y, 0 * y], 1), np.stack([xb, y, 0 * y], 1)], 1)
            if fi == 3:
                G = G[:, ::-1]
        G[..., 2] = CAP_ZE + cap_h(rows_t)[:, None] - 0.016 + rows_d[:, None]
        nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
        add_grid(P_fr, "M_timber", capw(G), flip=bool(nrm_[2] < 0), smooth="none")
    # rafters under the deck: 4 hips + commons
    rafters = []
    for sy in (-1, 1):
        rafters.append(((CAP_AF - 0.05, sy * (CAP_B - 0.05)), (XR1, 0.0)))
        rafters.append(((-CAP_AB + 0.05, sy * (CAP_B - 0.05)), (XR0, 0.0)))
        for xx in (XR0, CAP_XC, XR1):
            rafters.append(((xx, sy * (CAP_B - 0.05)), (xx, sy * 0.05)))
    rafters.append(((CAP_AF - 0.05, 0.0), (XR1 + 0.05, 0.0)))
    # (no rear centre rafter: the tail boom rails run out under the rear eave there)
    for (x0, y0), (x1, y1) in rafters:
        # rafter tails only: the run inside the valance box is enclosed
        tq = np.linspace(0, 1, 200)
        rq = np.hypot(x0 + (x1 - x0) * tq, y0 + (y1 - y0) * tq)
        if rq[0] < SKIRT_R:
            continue
        t_end = tq[np.argmax(rq < SKIRT_R - 0.05)] if (rq < SKIRT_R - 0.05).any() else 1.0
        n = 5
        t = np.linspace(0, t_end, n)
        xx = x0 + (x1 - x0) * t
        yy = y0 + (y1 - y0) * t
        zz = deck_under(xx, yy) - 0.05
        P, T = sweep(capw(np.stack([xx, yy, zz], 1))[None], rect_prof(0.07, 0.1, 0.012), up=(0, 0, 1))
        mq = (np.arange(len(T["quads"])) % 8) != 2          # top face bears on the deck soffit: not modelled
        T = dict(T, quads=T["quads"][mq], qflat=T["qflat"][mq])
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
            blocks.append((min(angs), max(angs), ZSH - 0.11, ZSH + 0.11))
    angs = []
    for rq in (r_in - 0.003, r_out + 0.003):
        for yq in (-(TB_YC + TB_RW / 2 + 0.01), TB_YC + TB_RW / 2 + 0.01):
            angs.append(math.atan2(yq, -math.sqrt(rq ** 2 - yq ** 2)) % (2 * PI))
    blocks.append((min(angs), max(angs), TB_Z - TB_RH / 2 - 0.01, TB_Z + TB_RH / 2 + 0.01))   # tail boom notch
    blocks.sort()
    arcs = []                                  # (a0, a1, kind) kind 0 = free, 1 = sheer gap
    for i, (b0, b1, zlo, zhi) in enumerate(blocks):
        nb0 = blocks[(i + 1) % len(blocks)][0] + (2 * PI if i == len(blocks) - 1 else 0)
        arcs.append((b0, b1, (zlo, zhi)))
        arcs.append((b1, nb0, 0))
    gap = 0.008
    vb = []                                    # (angle centre, arc width, z bottom, z top)
    for a0, a1, kind in arcs:
        S_ = (a1 - a0) * rr
        if kind != 0:
            zlo, zhi = kind
            ac = (a0 + a1) / 2
            cx, cy = rr * math.cos(ac), rr * math.sin(ac)
            zb = ZCT - 0.065 + rng.uniform(-0.01, 0.01)
            if zlo - zb > 0.03:
                vb.append((ac, S_ + 0.02, zb, zlo))     # under-board spans the notch (+1 cm laps)
            zt = float(deck_under(np.array(cx), np.array(cy))) + 0.01
            if zt - zhi > 0.03:
                vb.append((ac, S_ + 0.02, zhi, zt))
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
    P = rbox(T_BRD_OT, h, np.stack([np.full(N, 0.006), np.full(N, 0.005), np.minimum(0.006, ws / 5)], 1))
    P[:, :, 1] += rng.uniform(-0.003, 0.003, N)[:, None]
    radv = np.stack([np.cos(a_c), np.sin(a_c), np.zeros(N)], 1)
    tanv = np.stack([-np.sin(a_c), np.cos(a_c), np.zeros(N)], 1)
    zv = np.repeat([[0, 0, 1.0]], N, 0)
    Rk = frame_mats(zv, radv, np.cross(zv, radv))
    sk = np.clip(rng.normal(0, 0.3, N), -0.5, 0.5) * D2R * (Lz > 0.2)
    Rk = Rk @ rotm([0, 1, 0], sk)
    ctr = np.stack([cx, cy, (ztop + zbot) / 2], 1)
    Wk = xform(P, Rk, ctr)
    P_fr.add(capw(Wk), T_BRD_OT, Pl=P, mat="M_timber_weathered", smooth="bevel")
    log("valance boards %d (4 sheer notches)" % N)
    # nail heads along the top (into the eave plate)
    sel = Lz > 0.15
    nl = np.stack([cx, cy, ztop - 0.06], 1)[sel]
    prof = np.array([(0.0, 0.0), (0.008, 0.0), (0.007, 0.003), (0.0, 0.005)])
    Pn, Tn = lathe(np.repeat(prof[None], int(sel.sum()), 0), 6, open_base=True)
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
                tot += w + rng.uniform(0.006, 0.012)
            wl = np.array(wl) * 2 * hl / tot
            lc = -hl + np.cumsum(wl) + (np.arange(len(wl)) + 0.5) * (2 * hl - wl.sum()) / len(wl) - wl / 2
            lc += (ci % 2) * 0.06 + (0.07 if starter else 0.0)
            N = len(wl)
            # exposure (0.12 m) + ~9 cm hidden lap only: the rest of each covered shingle is not modelled
            L = rng.uniform(0.14, 0.15, N) * (0.9 if starter else 1.0)     # exposure 0.12 + 2-3 cm lap (deck under)
            Tsh = T_SHK_ST if ci == 0 else T_SHK_O
            tbb = tb + (rng.uniform(-0.006, 0.006, N) + (0.004 if starter else 0.0)) / R
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
                              np.full(N, 0.007), jag=0.01, curl=0.01, cup=0.003, T=Tsh)
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
            # nothing projects past the eave line / hip-board ends at the eave corners (round-4 shard trim)
            Wl[:, :, 0] = np.clip(Wl[:, :, 0], -CAP_AB - 0.045, CAP_AF + 0.045)
            Wl[:, :, 1] = np.clip(Wl[:, :, 1], -CAP_B - 0.045, CAP_B + 0.045)
            keep = (~under) & (rng.random(N) > 0.015)
            kk = sliver_keep(W0, Wl, tt, ee, T=Tsh)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(Wl[keep]), Tsh, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
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
        # (the hood boarding's soffit faces the closed hood interior: not modelled)
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
            L = rng.uniform(0.16, 0.18, N)
            W = rng.uniform(0.13, 0.16, N)
            Tsh = T_SHK if ci == 0 else T_SHK_O
            P = shingle_local(rng, L, W, np.full(N, 0.017), np.full(N, 0.007), jag=0.008, curl=0.008, T=Tsh)
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
            kk = sliver_keep(W0h, Wl, tt, ee, T=Tsh)
            nsliver += int((keep & ~kk).sum())
            keep &= kk
            P_sh.add(capw(Wl[keep]), Tsh, Pl=P[keep], mat="M_roof_shingle", smooth="bevel")
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
        # (the valley lead underside lies on the boarding and is never seen: not modelled)
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
    # ---- windshaft (16-sided) with iron hoops ----
    x0, x1 = HOOD_XF - 0.2, HUB_D - 0.36 * math.cos(TILT)     # (the run inside the cap is enclosed)
    n = 6
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
PHI_A = (135 - 8) * D2R          # wheel arms on an "X" (the grey diagonals of mill_sails_wheel)
ARM_R1 = 3.35                    # the four arms end just past the rim
W_WH = -0.33                     # wind-wheel blade plane (behind both stocks)
RING_IN, RING_OUT = 1.35, 3.20
W_RING = W_WH - 0.058
BL_R0, BL_R1 = 1.35, 3.90
BL_W0, BL_W1 = 0.55, 1.175
BL_PITCH = 13 * D2R
BL_N = 16


def rotw(P):
    """rotor-local (x, y, w) -> world (pre-lean)."""
    P = np.asarray(P, float)
    return HUB + P[..., 0:1] * E1 + P[..., 1:2] * E2 + P[..., 2:3] * S_AX


def er_t(phi):
    return np.array([math.cos(phi), math.sin(phi), 0.0]), np.array([-math.sin(phi), math.cos(phi), 0.0])


def stock_w(i):
    return 0.30 if i % 2 == 0 else 0.0


def stock_depth(r, i=0):
    return 0.30 - 0.13 * np.clip(r, 0, ARM_R1) / ARM_R1


def loc3(er, t, r, l, w):
    return np.asarray(r)[..., None] * er + np.asarray(l)[..., None] * t + np.asarray(w)[..., None] * np.array([0, 0, 1.0])


def perm_tmpl(T, odd):
    return flip_tmpl(T) if odd else T


RNG_BOLT = RNG("bolt_pool")


def bolt_frames(normals):
    R = []
    for nrm in np.atleast_2d(normals):
        zz = unit(nrm)
        xx = unit(np.cross([0.31, 0.53, 0.79], zz))
        R.append(np.stack([xx, np.cross(zz, xx), zz], 1))
    return np.array(R)


def bolt_heads(part, centers, normals, rad=0.02, hgt=0.012, sides=6):
    """Hex bolt heads / nuts / nail heads (world centres + outward normals) merged into `part`."""
    centers = np.atleast_2d(centers)
    prof = np.array([(0.0, 0.0), (rad, 0.0), (rad, hgt * 0.7), (rad * 0.75, hgt), (0.0, hgt)])
    P, T = lathe(np.repeat(prof[None], len(centers), 0), sides, open_base=True)
    part.add(xform(P, bolt_frames(normals), centers), T, mat="M_iron", smooth="none")


def hex_heads(part, centers, normals, rad=0.02, hgt=0.012):
    """Hex bolt heads / nuts (rotor-local centres + normals) -> pooled linked duplicates (producer note 3)."""
    centers = rotw(np.atleast_2d(centers))
    normals = rotw(np.atleast_2d(normals)) - HUB
    inst_bolts("MILL_rotor_bolt", centers, normals, rad, leaned=True, rng=RNG_BOLT)


def build_rotor(parts):
    rng = RNG("rotor")
    P_poll, P_wir, P_ri = parts["poll_end"], parts["wheel_spokes"], parts["rotor_iron"]
    letters = "ABCD"
    Z3 = np.array([0, 0, 1.0])
    for i in range(4):
        L = letters[i]
        P_st = parts["wheel_arm_%s" % L]
        phi = PHI_A + i * PI / 2
        er, t = er_t(phi)
        sw = stock_w(i)
        # wheel arm (client correction: the four arms are the fan wheel's arms, 0.30 at the poll end tapering to
        # 0.17 at the rim, ending just past the outer ring with a bolted strap; no sails)
        r0, r1 = -0.15, ARM_R1
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

    er, t = er_t(PHI_A)
    # ---- poll end (cast-iron cross box) ----
    h = np.array([[0.23, 0.23, 0.37]])
    P = rbox(T_DRS, h, np.array([[0.025, 0.025, 0.025]]))
    P_poll.add(rotw(loc3(er, t, P[..., 0], P[..., 1], P[..., 2])), T_DRS, Pl=P, mat="M_iron", smooth="bevel")
    prof = np.array([(0.0, 0.37), (0.21, 0.37), (0.22, 0.39), (0.2, 0.42), (0.1, 0.44), (0.06, 0.5), (0.0, 0.51)])
    Pc, T = lathe(prof[None], 24, open_base=True)
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
    nbl = BL_N
    rivets_c, rivets_n = [], []
    for k in range(nbl):
        phi = PHI_A + (180.0 / nbl + 360.0 / nbl * k) * D2R + rng.normal(0, 0.3) * D2R
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
    P, T = lathe(np.repeat(prof[None], len(rivets_c), 0), 6, open_base=True)
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
# G'. TAIL BOOM + TAIL VANE (client correction: the board panel of ref1 is a fixed tail vane on a doubled boom
#     running back from the cap along the shaft heading; it turns with the cap)
# =============================================================================================
TV_S0 = 3.40                      # vane inner edge (cap-local x' = -TV_S0), outer edge ~2.65 m further out
TV_LEN = 2.65
TV_H0 = (-0.62, 0.78)             # inner edge: bottom / top relative to the boom centre (1.40 m tall)
TV_H1 = (-0.98, 1.22)             # outer edge: 2.20 m tall (boards fan slightly outward)


def tail_boom(parts, x0=None, x1=None, z=None, seed="tail"):
    """Doubled hewn boom with spacer blocks, iron bands, a hanger with a lower brace and an upper brace from
    the rear ridge end; all in cap-local coordinates (turns with the cap). Returns the boom droop function."""
    x0 = TB_X0 if x0 is None else x0
    x1 = TB_X1 if x1 is None else x1
    z = TB_Z if z is None else z
    P_b, P_i = parts["tail_boom"], parts["tail_iron"]
    rng = RNG(seed + "_boom")
    Z3 = np.array([0, 0, 1.0])
    droop = 0.022                                   # cantilever sag at the tip

    def zb(x):
        return z - droop * np.clip((x0 - np.asarray(x, float)) / (x0 - x1), 0, 1) ** 2

    def C(x, y, zz):
        return capw(np.array([x, y, zz], float))
    for sy in (-1, 1):
        hewn_between(P_b, "M_timber_weathered", C(x0, sy * TB_YC, zb(x0)), C(x1 + rng.uniform(-0.02, 0.02),
                     sy * TB_YC, zb(x1)), TB_RW, TB_RH, Z3, rng, chamfer=(0.012, 0.022), checks=(1, 1),
                     check_len=(0.6, 1.2), end_split=1, bow=0.006)
    # spacer blocks between the rails (behind the vane the boards themselves fill the gap)
    for xs_ in (-1.30, -2.05, -2.80):
        blocks_world(P_b, "M_timber", C(xs_, 0.0, zb(xs_))[None],
                     frame_mats(capw(np.array([[1.0, 0, 0]])), capw(np.array([[0, 1.0, 0]])), Z3[None]),
                     [[0.07, TB_GAP / 2 + 0.002, TB_RH / 2 - 0.008]], c=0.006, T=T_BLK)
    # iron bands round the rail pair, each with a through-bolt (hex heads both sides)
    hb, hh = TB_YC + TB_RW / 2 + 0.003, TB_RH / 2 + 0.003
    for xb_ in (-1.92, -2.62, -3.30, -4.75, -5.92):
        zc_ = float(zb(xb_))
        loop = []
        cr = 0.01
        for (cy, cz) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            for a_ in np.linspace(0, PI / 2, 4):
                aa_ = math.atan2(cz, cy) - PI / 4 + a_
                loop.append((cy * (hb - cr) + cr * math.cos(aa_), cz * (hh - cr) + cr * math.sin(aa_)))
        loop = np.array(loop)
        path = capw(np.stack([np.full(len(loop), xb_), loop[:, 0], zc_ + loop[:, 1]], 1))
        Pb_, Tb_ = sweep(path[None], rect_prof(0.006, 0.045, 0.0015), up=capw(np.array([[1.0, 0, 0]]))[0],
                         closed=True)
        P_i.add(Pb_, Tb_, mat="M_iron", smooth="bevel")
        for sy in (-1, 1):
            inst_bolts("MILL_tail_bolt", C(xb_ + 0.04, sy * (hb + 0.002), zc_ - 0.02)[None],
                       capw(np.array([[0, sy, 0.0]])), 0.016, leaned=True, rng=rng)
    # hanger: two uprights clasping the rails just outside the rear eave, a cross block at their foot, and iron
    # stays from the foot back to the sheer ends (the hanger is carried by the cap frame)
    xh = -(CAP_AB + 0.18)
    zfoot = ZCT - 0.49
    yu = TB_YC + TB_RW / 2 + 0.036
    for sy in (-1, 1):
        hewn_between(P_b, "M_timber_weathered", C(xh, sy * yu, zfoot), C(xh, sy * yu, zb(xh) + 0.12), 0.09, 0.07,
                     capw(np.array([1.0, 0, 0])), rng, checks=(0, 1), end_split=1)
        for zq in (zb(xh), zfoot + 0.05):
            inst_bolts("MILL_tail_bolt", C(xh, sy * (yu + 0.036), zq)[None], capw(np.array([[0, sy, 0.0]])), 0.018,
                       leaned=True, rng=rng)
        # stay rod (dia 22 mm) from the hanger foot to the sheer end, with an eye plate on the sheer
        a_ = C(xh + 0.03, sy * (yu + 0.04), zfoot + 0.05)
        b_ = C(-1.00, sy * 0.70, ZCT + 0.30 - 0.07)       # sheer end (sheer centre ZCT + 0.30)
        Pr, Tr = sweep(np.stack([a_, b_])[None], circle_prof(0.011, 8), up=Z3)
        P_i.add(Pr, Tr, mat="M_iron", smooth="all")
    blocks_world(P_b, "M_timber", C(xh, 0.0, zfoot + 0.05)[None],
                 frame_mats(capw(np.array([[0, 1.0, 0]])), capw(np.array([[-1.0, 0, 0]])), Z3[None]),
                 [[yu - 0.045, 0.05, 0.05]], c=0.01, T=T_BLK)
    Y3 = capw(np.array([0, 1.0, 0]))
    # lower brace (round 5: hewn 0.08 x 0.10, 1.5-2.5 cm chamfers like the rails): from the cross block up and out
    # to the boom underside (just inside the vane), iron shoe
    xl = -3.24
    hewn_between(P_b, "M_timber_weathered", C(xh - 0.03, 0.0, zfoot + 0.10), C(xl, 0.0, zb(xl) - TB_RH / 2 - 0.04),
                 0.10, 0.08, Y3, rng, chamfer=(0.015, 0.025), checks=(0, 1), end_split=0)
    blocks_world(P_i, "M_iron", C(xl, 0.0, zb(xl) - TB_RH / 2 - 0.02)[None],
                 frame_mats(capw(np.array([[1.0, 0, 0]])), capw(np.array([[0, 1.0, 0]])), Z3[None]),
                 [[0.07, TB_YC + TB_RW / 2, 0.02]], c=0.003, T=T_BLK)
    # ---- round 5: hewn king post (0.12 x 0.12) rising ~0.30 m through the rear hip-end saddle from the cap
    # frame, with a draped lead collar; the upper brace is carried on it by an iron strap shoe and 2 bolts ----
    xk = XR0 - 0.16
    zt, xu1 = king_post(parts, xk, rng)
    a_ = C(xk - 0.02, 0.0, zt - 0.085)
    b_ = C(xu1, 0.0, zb(xu1) + TB_RH / 2 + 0.05)
    hewn_between(P_b, "M_timber_weathered", a_, b_, 0.10, 0.08, Y3, rng, chamfer=(0.015, 0.025), checks=(1, 1),
                 check_len=(0.4, 0.8), end_split=0)
    bdir = unit(b_ - a_)
    for sy in (-1, 1):
        # strap shoe: a plate down the post side and a plate along the brace side, each with a pooled hex bolt
        pa = C(xk, sy * 0.064, zt - 0.03)
        pb = C(xk, sy * 0.064, zt - 0.24)
        member(P_i, "M_iron", pa[None], pb[None], 0.05, 0.007, up=Y3 * sy, c=0.002)
        qa = a_ + Y3 * sy * 0.044 + bdir * 0.05
        qb = a_ + Y3 * sy * 0.044 + bdir * 0.33
        member(P_i, "M_iron", qa[None], qb[None], 0.05, 0.007, up=Y3 * sy, c=0.002)
        inst_bolts("MILL_tail_bolt", np.stack([C(xk, sy * 0.068, zt - 0.15), a_ + Y3 * sy * 0.048 + bdir * 0.24]),
                   np.stack([Y3 * sy, Y3 * sy]), 0.018, leaned=True, rng=rng)
    blocks_world(P_i, "M_iron", C(xu1, 0.0, float(zb(xu1)) + TB_RH / 2 + 0.008)[None],
                 frame_mats(capw(np.array([[1.0, 0, 0]])), capw(np.array([[0, 1.0, 0]])), Z3[None]),
                 [[0.07, 0.055, 0.008]], c=0.002, T=T_BLK)
    log("tail boom: rails x' %.2f..%.2f at z %.2f (droop %.3f), hanger at x' %.2f, braces to x' %.2f / %.2f"
        % (x0, x1, z, droop, xh, xl, xu1))
    return zb


def king_post(parts, xk, rng, h_above=0.30, half=0.06):
    """Hewn king post (kit component) through the cap roof at cap-local (xk, 0): from the cap frame 0.30 m
    under the covering to `h_above` over it, with a draped lead collar (upstand 6 cm, apron 9 cm) dressed onto
    the local roof surface (sampled from the built covering). Returns (post top z, x' of the brace foot)."""
    P_b, P_ir = parts["tail_boom"], parts["cap_iron"]
    Lc = to_cap_local(np.concatenate(parts["cap_shingles"].V + parts["cap_iron"].V))

    def roof(x, y, r=0.035):
        m_ = (np.abs(Lc[:, 0] - x) < r) & (np.abs(Lc[:, 1] - y) < r)
        return float(Lc[m_, 2].max()) if m_.any() else float(cap_z(np.array(x), np.array(y))) + 0.04
    z0 = roof(xk, 0.0, 0.07)
    zt = z0 + h_above
    hewn_between(P_b, "M_timber_weathered", capw(np.array([xk, 0.0, z0 - 0.30])), capw(np.array([xk, 0.0, zt])),
                 2 * half, 2 * half, capw(np.array([1.0, 0, 0])), rng, chamfer=(0.012, 0.02), checks=(1, 1),
                 check_len=(0.15, 0.3), end_split=1)
    # lead collar: square ring path round the post
    n_side = 6
    def sq(e):
        pts = []
        for (ax0, ay0, ax1, ay1) in ((1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1), (-1, -1, 1, -1)):
            for q in range(n_side):
                f = q / n_side
                pts.append((ax0 + (ax1 - ax0) * f, ay0 + (ay1 - ay0) * f))
        return np.array(pts) * e
    rows = []
    for (e, dz, up_) in ((half + 0.006, 0.065, True), (half + 0.006, 0.008, False), (half + 0.05, 0.007, False),
                         (half + 0.09, 0.004, False)):
        P2 = sq(e)
        zz = np.array([roof(xk + px, py, 0.06) for px, py in P2])
        zz = (np.roll(zz, 1) + 2 * zz + np.roll(zz, -1)) / 4        # dressed lead: no crumple following each butt
        zz = (np.roll(zz, 1) + 2 * zz + np.roll(zz, -1)) / 4 + 0.006
        if up_:
            zz = np.maximum(zz, z0) + dz - 0.008 + 0.008
        else:
            zz = zz + dz
        rows.append(np.stack([xk + P2[:, 0], P2[:, 1], zz], 1))
    rows[0][:, 2] = np.maximum(rows[0][:, 2], rows[1][:, 2] + 0.05)
    G = capw(np.stack(rows, 1))
    nrm_ = np.cross(G[1, 2] - G[0, 2], G[0, 3] - G[0, 2])
    add_grid(P_ir, "M_lead", G, wrap=True, flip=bool(nrm_[2] < 0), smooth="all")
    # a turned-over lip at the upstand top
    log("king post at x' %.2f: roof %.3f -> top %.3f m (0.12 x 0.12 hewn, lead collar)" % (xk, z0, zt))
    return zt, -3.26


def tail_vane(parts, zb, s0=TV_S0, length=TV_LEN, h0=TV_H0, h1=TV_H1, seed="tail"):
    """Vertical board panel in the plane of the boom, clasped between the two rails: slightly fanned boards
    (2 cm), ragged outer edge, one cracked board, one replaced board, two cleats on each face, nails."""
    P_v, P_i = parts["tail_vane"], parts["tail_iron"]
    rng = RNG(seed + "_vane")

    def vt(s):
        return h0[1] + (h1[1] - h0[1]) * np.clip(s / length, 0, 1)

    def vbot(s):
        return h0[0] + (h1[0] - h0[0]) * np.clip(s / length, 0, 1)
    ws = []
    while sum(ws) < length:
        ws.append(rng.uniform(0.17, 0.24))
    ws = np.array(ws) * length / sum(ws)
    edges = np.concatenate([[0], np.cumsum(ws)])
    nb = len(ws)
    cracked = int(rng.integers(2, nb // 2))
    replaced = int(rng.integers(nb // 2, nb - 2))
    nails = []
    cleat_z = (0.48, -0.40)
    for j in range(nb):
        g0, g1 = rng.uniform(0.002, 0.0045, 2)
        sa, sb_ = edges[j] + g0, edges[j + 1] - g1
        w = sb_ - sa
        sc_ = (sa + sb_) / 2
        fan = 7.0 * D2R * (sc_ / length - 0.35)
        th = 0.026 if j == replaced else 0.02
        pieces = [(-1.0, 1.0, 0.0)]
        if j == cracked:            # split along its upper 60 %: two halves 5 mm apart, one sprung 6 mm out
            pieces = [(-1.0, 0.0, -0.0025), (0.0, 1.0, 0.0025)]
        for (q0, q1, dq) in pieces:
            h = np.array([[0.5, th / 2, 0.5]])
            P = rbox(T_BRD, h, np.array([[0.004, min(0.004, th * 0.3), 0.008]]))
            tt = P[:, :, 0] + 0.5                      # 0 bottom .. 1 top
            lat = P[:, :, 2] + 0.5                     # 0 inner .. 1 outer (across the board)
            if j == cracked:
                lat = q0 / 2 + 0.5 + lat * (q1 - q0) / 2
                # the crack runs only through the top 60 %: below that the halves join
                gap_ = np.where(tt > 0.4, dq * np.clip((tt - 0.4) / 0.1, 0, 1), 0.0)
            else:
                gap_ = 0.0
            s_ = sa + lat * w + gap_
            rag_t = 0.0 if j == replaced else rng.uniform(-0.03, 0.02) + 0.012 * np.sin(lat * 7 + j)
            rag_b = 0.0 if j == replaced else rng.uniform(-0.02, 0.03) + 0.01 * np.sin(lat * 5 + 2 * j)
            if j == nb - 1:                            # outermost board: top corner broken off
                rag_t = rag_t - 0.09 * np.clip((lat - 0.3) / 0.7, 0, 1) ** 1.5
            v = (vbot(s_) + rag_b) + tt * ((vt(s_) + rag_t) - (vbot(s_) + rag_b))
            s2 = s_ + math.tan(fan) * v
            y = P[:, :, 1] + rng.uniform(-0.002, 0.002) + 0.004 * ((2 * lat - 1) ** 2 - 0.33) * rng.choice([-1, 1])
            if j == cracked:
                y = y + np.where((tt > 0.5) & (lat > 0.5), 0.006 * (tt - 0.5) * 2, 0.0)
            xq = -s0 - s2
            Q = np.stack([xq, y, zb(xq) + v], -1)
            W = capw(Q)
            T = orient(T_BRD, W[0])
            P_v.add(W, T, Pl=P, mat="M_timber" if j == replaced else "M_timber_weathered", smooth="bevel",
                    wear=0.15 if j == replaced else (0.85 if j in (cracked, nb - 1) else None))
        for cz in cleat_z:
            for sg in (-1, 1):
                nails.append((-s0 - sc_ + rng.uniform(-0.03, 0.03), sg * (th / 2 + 0.022), cz + rng.uniform(-0.01, 0.01)))
    # cleats: both faces, above and below the boom
    for cz in cleat_z:
        for sg in (-1, 1):
            sa, sb_ = 0.04, length - rng.uniform(0.06, 0.12)
            h = np.array([[(sb_ - sa) / 2, 0.011, 0.035]])
            P = rbox(T_PLK, h, np.array([[0.006, 0.005, 0.006]]))
            xq = -s0 - (sa + sb_) / 2 - P[:, :, 0]
            Q = np.stack([xq, sg * (0.0105 + 0.011) + P[:, :, 1] * sg, zb(xq) + cz + P[:, :, 2] +
                          rng.uniform(-0.01, 0.01) * P[:, :, 0] / h[0, 0]], -1)
            W = capw(Q)
            P_v.add(W, orient(T_PLK, W[0]), Pl=P, mat="M_timber_weathered", smooth="bevel")
    nails = np.array(nails)
    xq = nails[:, 0]
    C = capw(np.stack([xq, nails[:, 1], zb(xq) + nails[:, 2]], 1))
    Nn = capw(np.stack([0 * xq, np.sign(nails[:, 1]), 0 * xq], 1))
    bolt_heads(P_i, C, Nn, rad=0.008, hgt=0.005, sides=6)
    log("tail vane: %d boards over %.2f m (x' %.2f..%.2f), height %.2f -> %.2f m, cracked %d, replaced %d"
        % (nb, length, -s0, -s0 - length, h0[1] - h0[0], h1[1] - h1[0], cracked, replaced))


# =============================================================================================
# I. RAKING PROPS (-X)
# =============================================================================================
T_PAD = tmpl_box(25, 4, 25, drop={(1, 0)})       # prop pad stone: dense top so the chock notch has crisp walls


def facet_shave(P, rng, faces, n=(1, 2), dep=(0.003, 0.006), tilt=0.12):
    """Planar adze / split facets: each listed face (axis, sign) of a centred block P (nv,3) is shaved by 1-2
    slightly tilted planes 3-6 mm deep (crisp facet edges, not a rounded box)."""
    for (ax_, sg) in faces:
        for _ in range(int(rng.integers(n[0], n[1] + 1))):
            nrm = np.zeros(3)
            nrm[ax_] = sg
            nrm += rng.normal(0, tilt, 3) * (np.arange(3) != ax_)
            nrm /= np.linalg.norm(nrm)
            pr = P @ nrm
            o = pr.max() - rng.uniform(*dep)
            P -= np.clip(pr - o, 0, None)[:, None] * nrm[None]
    return P


def prop_foot(P_a, rng, bot, hz, Zf, idx, pole_at, heel=0.10):
    """Raking-prop foot (kit component, round 5): a split-stone pad bedded in the soil with only its domed,
    irregular top showing (3-6 cm on the high side, 0-2 cm on the low side, no vertical side over 4 cm); a
    hewn chock with planar adze facets sunk >= 40 % of its height into a notch cut in the pad, a bird's-mouth
    step receiving the axe-cut pole foot, two iron dogs; a concave soil fillet that runs out tangentially, and
    3-5 split pebbles buried 40-60 %. hz: horizontal direction pole-top -> foot; seat at Zf, heel `heel` higher."""
    Z3 = np.array([0, 0, 1.0])
    sv = unit(np.cross(Z3, hz))
    Rg = frame_mats(hz[None], sv[None], Z3[None])[0]
    base = bot * np.array([1, 1, 0])

    def place(P, along, lat, z):
        return xform(P, Rg, base + hz * along + sv * lat + np.array([0, 0, z]))
    # ---- pad: bedded split stone, domed top, tilted 3-4 deg, highest point 4.5-5.5 cm ----
    Lpad, Wpad, Hpad = rng.uniform(0.64, 0.74), rng.uniform(0.56, 0.64), 0.20
    Pst, Tst = stone_local(rng, [Lpad], [Wpad], [Hpad], "ground", rot_deg=(0, 0, 0), T=T_PAD)
    uu = Pst[0, :, 0] / (Lpad / 2)
    ww = Pst[0, :, 2] / (Wpad / 2)
    up_w = np.clip((Pst[0, :, 1] + Hpad) / Hpad, 0, 1)
    Pst[0, :, 1] += rng.uniform(0.016, 0.022) * np.clip(1 - uu ** 2, 0, 1) * np.clip(1 - ww ** 2, 0, 1) * up_w
    Wp = xform(Pst, Rg @ R_UPRIGHT @ rotm([0, 1, 0], [rng.uniform(-0.15, 0.15)])[0], base - hz * 0.10)
    td = rng.uniform(0, 2 * PI)
    tdir = np.array([math.cos(td), math.sin(td), 0.0])
    Wp[0, :, 2] += math.tan(rng.uniform(3.0, 4.0) * D2R) * ((Wp[0] - base) @ tdir)
    Wp[0, :, 2] += rng.uniform(0.045, 0.055) - Wp[0, :, 2].max()
    # notch for the chock: chock footprint (+1 cm) pressed down to the notch floor
    al0, al1, hwc = -0.34, 0.15, 0.13
    d = Wp[0] - base
    al, lt = d @ hz, d @ sv
    # round 6: the notch is cut to the chock's footprint +3 mm (gap <= 5 mm), packed with soil below
    inn = (al > al0 - 0.003) & (al < al1 + 0.003) & (np.abs(lt) < hwc + 0.003)
    z_pad_c = float(np.max(np.where(inn, Wp[0, :, 2], -1)))
    z_n = -0.045
    Wp[0, :, 2] = np.where(inn, np.minimum(Wp[0, :, 2], z_n), Wp[0, :, 2])
    P_a.add(Wp, Tst, Pl=Pst, mat="M_stone", smooth="all", wear=0.7)
    # ---- chock: hewn block with planar adze facets, bird's-mouth step at along = 0 ----
    Lc = al1 - al0
    Hc = Zf + heel - z_n
    Pc, Tc = hewn_beam(rng, Lc, 2 * hwc, Hc, nx=18, chamfer=(0.007, 0.013), adze=(0.002, 0.004), checks=(1, 1),
                       check_len=(0.15, 0.3), end_split=1, drop=((2, 0),))
    # round 6 (director r5 #4): an irregular hewn WEDGE - the top 2-3 cm narrower than the base, the heel end
    # tapering 3-5 cm toward the top, and adze facets 6-12 mm deep that read from 2 m
    zr_ = np.clip((Pc[0, :, 2] + Hc / 2) / Hc, 0, 1)
    nw_ = rng.uniform(0.010, 0.015)
    Pc[0, :, 1] -= np.sign(Pc[0, :, 1]) * nw_ * zr_ * np.clip(np.abs(Pc[0, :, 1]) / hwc, 0, 1)
    et_ = rng.uniform(0.03, 0.05)
    Pc[0, :, 0] -= et_ * zr_ * np.clip((Pc[0, :, 0] + 0.02) / (Lc / 2), 0, 1)
    Pc[0, :, 1] += rng.uniform(-0.006, 0.006) * zr_ * np.sign(Pc[0, :, 1])  # the two cheeks not parallel
    Pc[0] = facet_shave(Pc[0], rng, ((1, 1), (1, -1), (2, 1), (0, 1), (0, -1)), n=(2, 3), dep=(0.006, 0.012),
                        tilt=0.18)
    xs_ = Pc[0, :, 0] + (al0 + al1) / 2                       # along
    zl = Pc[0, :, 2] + Hc / 2                                  # 0 .. Hc above the notch floor
    seat = xs_ < -0.003
    Pc[0, :, 2] = np.where(seat, -Hc / 2 + zl * (Zf - z_n) / Hc, Pc[0, :, 2])
    P_a.add(place(Pc, (al0 + al1) / 2, 0.0, z_n + Hc / 2), Tc, Pl=Pc[0], mat="M_timber_weathered", smooth="bevel",
            wear=0.75)
    sunk = (z_pad_c - z_n) / Hc
    # soil / chinking packed into the notch round the chock: a band from 1 cm down the chock's cheeks out over
    # the notch rim, tucked under the pad's top surface (no dark slot)
    zrel_rim = (z_pad_c - z_n) / Hc
    hw_rim = hwc - nw_ * zrel_rim
    perim = []
    for (a0_, a1_, l0_, l1_) in ((al0, al1, -hw_rim, -hw_rim), (al1 - et_ * zrel_rim, al1 - et_ * zrel_rim, -hw_rim, hw_rim),
                                 (al1, al0, hw_rim, hw_rim), (al0, al0, hw_rim, -hw_rim)):
        for u_ in np.linspace(0, 1, 9)[:-1]:
            perim.append((a0_ + (a1_ - a0_) * u_, l0_ + (l1_ - l0_) * u_))
    perim = np.array(perim)
    cc_ = perim.mean(0)
    dir_ = perim - cc_
    dir_ /= np.linalg.norm(dir_, axis=1, keepdims=True)
    padxy = Wp[0, :, :2]
    padz = Wp[0, :, 2]
    rows = []
    for f_, (off_, dz_) in enumerate(((-0.004, -0.010), (0.006, -0.004), (0.02, None), (0.035, None))):
        q_ = perim + dir_ * off_
        wq = base[None, :2] + hz[None, :2] * q_[:, :1] + sv[None, :2] * q_[:, 1:2]
        if dz_ is None:
            dd_ = np.linalg.norm(padxy[None] - wq[:, None], axis=2)
            near_ = np.argsort(dd_, axis=1)[:, :4]
            zq = padz[near_].max(1) - (0.002 if f_ == 2 else 0.006)
        else:
            zq = np.full(len(wq), z_pad_c + dz_)
        rows.append(np.concatenate([wq, zq[:, None]], 1))
    G = np.stack(rows, 1)
    nrm_ = np.cross(G[1, 0] - G[0, 0], G[0, 1] - G[0, 0])
    add_grid(P_a, "M_earth", G, wrap=True, flip=bool(nrm_[2] < 0))
    # iron dogs (round 6): a flat bar driven into the chock's top, bent, and lying FLAT on the pole's side
    # (gap <= 2 mm) for 14-18 cm, spike heads at both ends
    for sg in (-1, 1):
        za_, zb_ = Zf - 0.07, Zf - 0.012
        hwa = hwc - nw_ * (za_ - z_n) / Hc + 0.0035
        hwb = hwc - nw_ * (zb_ - z_n) / Hc + 0.0035
        a_ = place(np.zeros((1, 1, 3)), -0.12, sg * hwa, za_)[0, 0]
        a2_ = place(np.zeros((1, 1, 3)), -0.12, sg * hwb, zb_)[0, 0]
        z1_ = Zf + 0.11
        pc1, pr1 = pole_at(z1_)
        pc2, pr2 = pole_at(z1_ + rng.uniform(0.12, 0.16))
        b1_ = pc1 + sv * sg * (pr1 + 0.0035)
        b2_ = pc2 + sv * sg * (pr2 + 0.0035)
        member(P_a, "M_iron", a_[None], a2_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        member(P_a, "M_iron", a2_[None], b1_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        member(P_a, "M_iron", b1_[None], b2_[None], 0.03, 0.007, up=sv * sg, c=0.002)
        bolt_heads(P_a, np.stack([a_ + sv * sg * 0.004, b2_ + sv * sg * 0.004]),
                   np.stack([sv * sg, sv * sg]), rad=0.011, hgt=0.006, sides=8)
    # ---- concave soil fillet round the pad, running out tangentially 0.16-0.24 m beyond it ----
    hm = rng.uniform(0.022, 0.03)
    soil_collar(P_a, rng, Wp[0], hm, (0.16, 0.24), idx, m=32, inset=0.95)
    # ---- 3-5 split pebbles in the fillet, buried 40-60 % ----
    c0 = Wp[0, :, :2].mean(0)
    npb = int(rng.integers(3, 6))
    ap = rng.uniform(0, 2 * PI, npb)
    rp = 0.5 * max(Lpad, Wpad) + rng.uniform(0.03, 0.14, npb)
    xy = c0 + np.stack([rp * np.cos(ap), rp * np.sin(ap)], 1)
    fp = np.clip((rp - 0.5 * max(Lpad, Wpad)) / 0.2, 0, 1)
    sz = rng.uniform(0.04, 0.08, npb)
    settled_stones(P_a, rng, xy, sz * 1.2, sz * 0.9, sz * 0.55, bury=(0.4, 0.6), style="ground", collar=None,
                   z0=hm * (1 - fp) ** 2.6, tilt=10.0)
    log("prop foot %d: pad top %.3f m, chock %.0f%% sunk into the notch (height %.3f), seat %.2f, heel %.2f"
        % (idx, float(Wp[0, :, 2].max()), 100 * sunk, Hc, Zf, Zf + heel))


def raking_prop(parts, top, bot, k, zatt, idx=0, rng=None, Zf=0.08, seed=None):
    """Raking timber prop (kit component): a bowed, checked, knotted pole from its head `top` (on tower face k at
    height zatt, carried by a cleat, collar lugs and a through-bolt) down to the ground anchor at `bot`, ending in
    prop_foot() (bedded pad, sunk chock, soil fillet). Writes <PREFIX>_props / _prop_anchors / _prop_iron."""
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = RNG("prop_%s" % seed) if rng is None else rng
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
    dt = 0.045 / Lp
    t_main = np.arange(-0.02, 1.0 - 0.5 / Lp, dt)
    t_foot = np.arange(t_main[-1] + 0.012 / Lp, 1.06, 0.012 / Lp)
    t = np.concatenate([t_main, t_foot])
    n = len(t)
    bow = rng.uniform(0.08, 0.12) * rng.choice([-1, 1])
    sag = rng.uniform(0.0, 0.03)
    cen = top + axis * t[:, None] + side * (bow * np.sin(np.clip(t, 0, 1) * PI))[:, None] \
        - upv * (sag * np.sin(np.clip(t, 0, 1) * PI))[:, None]
    rad = 0.075 + 0.025 * np.clip(t, 0, 1) + 0.003 * np.sin(t * 13 + idx) + 0.002 * np.sin(t * 31 + 2 * idx)
    nck = int(rng.integers(2, 4))
    # first check on the face seen from the front / hero cameras (-side), the second on the upper face
    ck_a = np.array([PI + rng.uniform(-0.4, 0.4), PI / 2 + rng.uniform(-0.4, 0.4),
                     rng.uniform(-PI / 2, 0.2)])[:nck]
    # round 5: two more checks in the bottom 1.2 m of the pole (actor distance), on faces the cameras see
    jit_ = rng.uniform(-0.08, 0.08)
    for off_ in (0.55, -0.6, 1.0, -1.1, 2.4, -2.5, 3.14):
        cand_ = ck_a[0] + off_ + jit_
        if len(ck_a) < nck + 2 and np.min(np.abs((ck_a - cand_ + PI) % (2 * PI) - PI)) > 0.4:
            ck_a = np.append(ck_a, cand_)
    base_a = np.linspace(0, 2 * PI, 32, endpoint=False)
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
    for q in range(4):
        af = (PI + rng.uniform(-0.5, 0.5)) if q == 0 else rng.uniform(0, 2 * PI)
        lf = rng.uniform(0.8, 1.6) if q < 3 else rng.uniform(0.6, 0.9)
        s0 = rng.uniform(0.6, 3.5) if q == 0 else (rng.uniform(1.0, Lp - lf - 0.5) if q < 3 else
                                                     rng.uniform(0.12, 0.28))   # q 3: adze flat at the foot
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
        if len(checks) >= nck:              # foot checks: within the bottom 1.2 m
            lc = rng.uniform(0.6, 0.9)
            s0 = rng.uniform(0.15, 1.2 - lc)
        else:
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
    for ik, sk in enumerate(kd):
        tk = 1 - sk / Lp
        ak = rng.uniform(0, 2 * PI)
        dk = rng.uniform(0.05, 0.07) if ik < 2 else rng.uniform(0.04, 0.07)   # the two lower knots 5-7 cm
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
    p3 = stop + np.array([0, 0, Zf + 0.115 - stop[2]])
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
        Pb, Tb = lathe(prof_b[None], 6, open_base=True)
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
        Pb, Tb = lathe(prof_b[None], 6, open_base=True)
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
    # ---- ground (round 4): one hewn chock seated in a notch cut into a rough split-stone pad, iron dogs
    # from the chock onto the pole, and a soil mound round the pad with a few embedded pebbles ----
    def pole_at(z, top=top, axis=axis, side=side, bow=bow):
        tq = (top[2] - z) / (top[2] - bot[2])
        return top + axis * tq + side * bow * math.sin(min(tq, 1.0) * PI), 0.075 + 0.025 * min(tq, 1.0)
    prop_foot(P_a, rng, bot, hz, Zf, idx, pole_at)
    return top, bot


def build_props(parts, props=None):
    """The mill's prop set: `props` = [(tower face k, lateral offset, attach z, foot (x, y)), ...]; default: two
    near-parallel long props from just under the collar on the -X face and a shorter one on the -X/-Y face."""
    P_p, P_a, P_i = parts["props"], parts["prop_anchors"], parts["prop_iron"]
    rng = RNG("props")
    defs = []
    zc = Z_COLLAR - 0.11
    if props is None:
        props = ((6, 0.36, zc, (-6.3, -1.2)), (6, -0.36, zc, (-6.0, 0.9)), (6, 0.62, float(TZ(7.30)), (-6.0, -3.1)))
    for (k, lat, z, gnd) in props:
        top = face_map(k, np.array([lat]), np.array([z]), np.array([0.14]))[0]
        defs.append((lean(top[None])[0], np.array([gnd[0], gnd[1], 0.19]), k, z))
    Zf = 0.08                                   # round 5: seat of the sunk chock (pad top ~5 cm)
    for idx, (top, bot, k, zatt) in enumerate(defs):
        raking_prop(parts, top, bot, k, zatt, idx, rng, Zf)
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
    """Optional low moss cushions (M_moss) on the apron's shake butts (mostly the shaded north side)
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
    P_m.add(xform(P, Rf @ Rl, ctr), T, Pl=P, mat="M_moss", smooth="all")
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
    P_m.add(lean(W), T, Pl=P, mat="M_moss", smooth="all")


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
    """Blades vs wheel arms / arm straps (voxel proximity) and blade spacing."""
    def loc(V):
        d = V - HUB
        return np.stack([d @ E1, d @ E2, d @ S_AX], 1)
    bl = loc(part_samples(parts["wheel_blades"], 0.01))
    arms = np.concatenate([loc(part_samples(parts["wheel_arm_%s" % L], 0.01)) for L in "ABCD"])
    g1 = voxel_min_gap(bl, arms, 0.06)
    log("ROTOR wind-wheel blades vs arms: min gap %.3f m %s" % (g1, "(PASS)" if g1 > 0.015 else "(FAIL)"))
    for r in (2.5, BL_R1):
        s_ = np.clip((r - BL_R0) / (BL_R1 - BL_R0), 0, 1)
        w = BL_W0 + (BL_W1 - BL_W0) * s_
        log("WHEEL r=%.2f: blade width %.3f, pitch %.3f, gap %.3f m" % (r, w, 2 * PI * r / BL_N, 2 * PI * r / BL_N - w))
    return g1


def tail_clearance(parts, xf, res=0.02):
    """The tail turns with the cap about the (leaned) tower axis: collapse everything to (radius from the yaw
    axis, height along it) and measure the swept gap from the tail to the tower and the props at ANY yaw."""
    ax = LEAN_R @ np.array([0, 0, 1.0])

    def rz(V):
        d = V - LEAN_PIVOT
        h = d @ ax
        return np.linalg.norm(d - h[:, None] * ax, axis=1), h
    out = {}
    tail = np.concatenate([xf(parts[k], part_samples(parts[k], res)) for k in ("tail_boom", "tail_vane", "tail_iron")])
    tr, th = rz(tail)
    for k in ("tower_boards", "tower_frame", "tower_iron", "props", "prop_iron"):
        sr, sh = rz(xf(parts[k], part_samples(parts[k], res)))
        best = 9.9
        for zlo in np.arange(th.min(), th.max(), 0.25):
            mt = (th >= zlo - 0.3) & (th < zlo + 0.55)
            ms = (sh >= zlo) & (sh < zlo + 0.25)
            if not ms.any() or not mt.any():
                continue
            # tail radii vs static radii in this height slab (yaw-swept: only radius and height matter)
            dr = np.abs(tr[mt][:, None] - sr[ms][None, ::max(1, ms.sum() // 400)])
            dh = np.abs(th[mt][:, None] - sh[ms][None, ::max(1, ms.sum() // 400)])
            best = min(best, float(np.sqrt(dr ** 2 + dh ** 2).min()))
        out[k] = best
    log("TAIL swept clearance at any cap yaw: " + ", ".join("%s %.3f m" % (k, v) for k, v in out.items()))
    return out


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
# =============================================================================================
# MODULAR KIT (producer note 2). Every component is a parameterised function that writes its own named
# object(s) (<PREFIX>_<part>). Component parameters are published to the shared dimension table (the module
# constants the low-level placement helpers read: R_out, cap_z, face_map, ...) by kit_set(), which also
# re-derives every dependent constant (openings, cap profile and valley tables, rotor frame, ...). main() only
# calls the components with this mill's numbers; kit_variant() builds a different mill from the same code.
# =============================================================================================
PREFIX = "MILL"


def kpart(parts, key, mats, **kw):
    """Get or create the named object (Part) `<PREFIX>_<key>` of a component."""
    if key not in parts:
        parts[key] = Part("%s_%s" % (PREFIX, key), mats, **kw)
    return parts[key]


class seeded:
    """Salt every generator a component draws from (None / '' keeps this mill's seeds)."""
    def __init__(self, seed):
        self.seed = "" if seed in (None, "") else "|" + str(seed)

    def __enter__(self):
        global SEED_SALT
        self.old, SEED_SALT = SEED_SALT, self.seed

    def __exit__(self, *a):
        global SEED_SALT
        SEED_SALT = self.old


def _derive():
    g = globals()
    g["R_DOOR"] = float(R_out(1.0))
    g["RREF"] = R_BASE0 - 0.07
    g["DZ"] = Z_CORN0 - 4.05
    g["OPENINGS"] = [(0.0, hw_door)] + [(a, hw_window) for a in WIN_AZ] + [(a, hw_arch) for a in ARCH_AZ]
    g["AP_A"] = math.atan2(AP_ZT - AP_ZE, AP_RE - AP_RT)
    g["TW_TAPER"] = (TW_A0 - TW_A1) / (TW_Z1 - TW_Z0)
    g["LEAN_PIVOT"] = np.array([0, 0, TW_Z0 - 0.15])
    g["CURB_R"] = TW_A1 + 0.04
    g["ZCT"] = TW_Z1 + 0.01
    g["Z_COLLAR"] = TW_Z1 - 1.15
    g["HDIR"] = np.array([math.sin(CAP_AZ), -math.cos(CAP_AZ), 0.0])
    g["YDIR"] = np.cross([0, 0, 1.0], g["HDIR"])
    g["CAP_XC"] = (CAP_AF - CAP_AB) / 2
    g["XR0"], g["XR1"] = g["CAP_XC"] - RIDGE_L / 2, g["CAP_XC"] + RIDGE_L / 2
    g["CAP_EF"], g["CAP_EB"], g["CAP_SB"] = CAP_AF - g["XR1"], CAP_AB + g["XR0"], CAP_B
    g["CAP_ZE"] = g["ZCT"] + 0.24
    g["HUB_Z"] = g["CAP_ZE"] + 0.66
    g["HOOD_ZE"], g["HOOD_ZR"] = g["CAP_ZE"] + 0.62 * CAP_RISE / 1.18, g["CAP_ZE"] + CAP_RISE - 0.12
    g["TB_X0"] = -(CAP_AB - 0.35)
    g["SKIRT_R"] = g["CURB_R"] + CURB_W / 2 + 0.012
    g["TB_Z"] = g["ZCT"] + 0.09
    g["CAP_DS"], g["CAP_HS"], g["CAP_TMAX"] = _cap_profile()
    g["VAL_Y"], g["VAL_X"] = _valley_table()
    g["S_AX"] = math.cos(TILT) * g["HDIR"] + math.sin(TILT) * np.array([0, 0, 1.0])
    g["E1"] = unit(np.cross(-g["S_AX"], [0, 0, 1.0]))
    g["E2"] = np.cross(g["E1"], -g["S_AX"])
    g["HUB"] = g["HDIR"] * HUB_D + np.array([0, 0, g["HUB_Z"]])
    g["ARM_R1"] = RING_OUT + 0.15


def kit_set(**kw):
    """Publish component parameters to the dimension table and re-derive everything that depends on them."""
    g = globals()
    for k_, v_ in kw.items():
        assert k_ in g, "unknown kit parameter " + k_
        g[k_] = v_
    _derive()


def _door_params(width=None, spring=None, reveal=None, ring=None):
    kw = {}
    if width is not None:
        kw["DOOR_CW"] = width / 2
    if spring is not None:
        zs = Z_TH + spring
        kw["ZS_DOOR"] = zs
        kw["DOOR_JZ"] = [0.0] + [zs * f for f in (0.44 / 1.79, 0.86 / 1.79, 1.30 / 1.79)] + [zs]
    if ring is not None:
        kw["DOOR_RING"] = tuple(ring)
    if kw:
        kit_set(**kw)


def _arcade_params(n=None, clear_w=None, clear_h=None, z_sill=None, az0=18.0, ring=None, pier_fw=None):
    a = dict(ARCH)
    if clear_w is not None:
        a["cw"] = clear_w / 2
    if z_sill is not None:
        a["z0"] = z_sill
    if clear_h is not None or z_sill is not None or clear_w is not None:
        h = clear_h if clear_h is not None else (ARCH["zs"] + ARCH["cw"] - ARCH["z0"])
        a["zs"] = a["z0"] + h - a["cw"]
        a["jz"] = [a["z0"], 0.5 * (a["z0"] + a["zs"]), a["zs"]]
    if ring is not None:
        a["ring"] = tuple(ring)
    if pier_fw is not None:
        a["fw"] = pier_fw
    kw = dict(ARCH=a)
    if n is not None:
        kw["ARCH_AZ"] = [(az0 + 360.0 / n * k) * D2R for k in range(n)]
    kit_set(**kw)


def arched_door(parts, width=None, spring=None, reveal=None, ring=None, seed=None, _drum_call=False):
    """Arched stone doorway (kit component), facing -Y in its drum: clear `width`, semicircular head springing
    `spring` above the threshold, dressed jambs + irregular voussoirs (<PREFIX>_door_surround), threshold, the
    arch-topped ledged plank leaf with strap hinges (<PREFIX>_door_leaf / _door_iron) and the visible interior
    depth (<PREFIX>_interior). `reveal` is the rebate depth (0.30 m on this mill)."""
    _door_params(width, spring, reveal, ring)
    with seeded(seed):
        arched_door_surround(parts)
        build_door_and_interior(parts)


def blind_arcade(parts, n=None, clear_w=None, clear_h=None, z_sill=None, az0=18.0, seed=None, _drum_call=False):
    """Blind arcade of `n` round-headed recesses (clear_w x clear_h, sill at z_sill, first bay at az0 deg),
    0.25 m deep with rubble backs, 9-11 irregular voussoirs, dressed piers and sill slabs."""
    if n is not None or clear_w is not None or clear_h is not None or z_sill is not None:
        _arcade_params(n, clear_w, clear_h, z_sill, az0)
    with seeded(seed):
        blind_arcade_build(parts)


def round_stone_drum(parts, r_base=None, r_top=None, height=None, zones=None, door=None, arcade=None,
                     windows=None, seed=None):
    """Battered round rubble drum (kit component): radius r_base at the ground battering to r_top, cornice top
    at `height`. zones: dict(band=(z0, z_bal0, z_bal1, z1)) for the balustrade band. The door / arcade dicts are
    the arched_door() / blind_arcade() parameters, windows = slit-window azimuths (deg). Writes
    <PREFIX>_base_stones / _base_mortar / _base_dressed plus the door and arcade objects."""
    kw = {}
    if r_base is not None:
        kw["R_BASE0"] = r_base
    if r_top is not None:
        kw["R_BASE1"] = r_top
    if height is not None:
        kw["Z_CORN0"] = height - 0.45
        kw["Z_BATTER"] = height - 0.57
    if zones and "band" in zones:
        kw["Z_BAND0"], kw["Z_BAL0"], kw["Z_BAL1"], kw["Z_BAND1"] = zones["band"]
    if windows is not None:
        kw["WIN_AZ"] = [a * D2R for a in windows]
    kit_set(**kw)
    if door:
        _door_params(**door)
    if arcade:
        _arcade_params(**arcade)
    with seeded(seed):
        n = build_base(parts)
    return n


def shake_apron(parts, r_eave=None, z_eave=None, r_top=None, z_top=None, courses=None, seed=None):
    """Conical split-shake apron (kit component) from the cornice eave (r_eave, z_eave) up to the tower foot
    (r_top, z_top) in `courses` courses, with rafters, sarking, eave fascia and tower-foot flashing."""
    kw = {k_: v_ for k_, v_ in (("AP_RE", r_eave), ("AP_ZE", z_eave), ("AP_RT", r_top), ("AP_ZT", z_top),
                                ("AP_COURSES", courses)) if v_ is not None}
    kit_set(**kw)
    with seeded(seed):
        build_apron(parts)


def smock_tower(parts, af_bottom=None, af_top=None, z0=None, z1=None, seed=None):
    """Octagonal boarded smock tower (kit component): across-flats af_bottom at z0 tapering to af_top at z1;
    cant posts, sill, rails and curb rings, drip boards, weatherboards with battens, hatch, prop collar."""
    kw = {k_: v_ for k_, v_ in (("TW_A0", None if af_bottom is None else af_bottom / 2),
                                ("TW_A1", None if af_top is None else af_top / 2), ("TW_Z0", z0), ("TW_Z1", z1))
          if v_ is not None}
    kit_set(**kw)
    with seeded(seed):
        build_tower(parts)


def mill_cap(parts, length=None, width=None, rise=None, ridge_len=None, yaw=None, seed=None):
    """Hipped shingled mill cap (kit component): footprint length (along the windshaft) x width, `rise` from
    eave to ridge, a ridge of ridge_len, yawed `yaw` deg; frame, sarking, shingles, cappings, hood, valance."""
    kw = {}
    if length is not None:
        kw["CAP_AF"], kw["CAP_AB"] = length * 0.4638, length * 0.5362
    if width is not None:
        kw["CAP_B"] = width / 2
    if rise is not None:
        kw["CAP_RISE"] = rise
    if ridge_len is not None:
        kw["RIDGE_L"] = ridge_len
    if yaw is not None:
        kw["CAP_AZ"] = yaw * D2R
    kit_set(**kw)
    with seeded(seed):
        build_cap(parts)


def wind_wheel(parts, r_in=None, r_rim=None, r_tip=None, n_blades=None, pitch=None, hub_d=None, seed=None):
    """Annular wind-wheel (kit component): n_blades board blades from r_in to r_tip on an inner ring (r_in) and
    an outer rim (r_rim), pitched `pitch` deg; four tapered hewn arms, poll end, spokes, rivets. Blade widths
    scale with 16 / n_blades so the annulus stays near-continuous."""
    kw = {}
    if r_in is not None:
        kw["RING_IN"] = kw["BL_R0"] = r_in
    if r_rim is not None:
        kw["RING_OUT"] = r_rim
    if r_tip is not None:
        kw["BL_R1"] = r_tip
    if n_blades is not None:
        kw["BL_N"] = n_blades
        kw["BL_W0"], kw["BL_W1"] = 0.55 * 16 / n_blades, 1.175 * 16 / n_blades
    if pitch is not None:
        kw["BL_PITCH"] = pitch * D2R
    if hub_d is not None:
        kw["HUB_D"] = hub_d
    kit_set(**kw)
    with seeded(seed):
        build_rotor(parts)


def new_parts(prefix="MILL"):
    """The mill's named objects (components add their own through kpart())."""
    global PREFIX
    PREFIX = prefix
    TW = ["M_timber_weathered"]
    X = prefix + "_"
    parts = dict(
        stones=Part(X + "base_stones", ["M_stone"]),
        mortar=Part(X + "base_mortar", ["M_mortar"]),
        dressed=Part(X + "base_dressed", ["M_stone_dressed"]),
        interior=Part(X + "interior", ["M_stone", "M_timber", "M_mortar"]),
        door=Part(X + "door_leaf", TW),
        door_iron=Part(X + "door_iron", ["M_iron"]),
        rubble=Part(X + "ground_rubble", ["M_rubble", "M_stone", "M_earth"], moss=0.1),
        curb=Part(X + "curb", ["M_timber", "M_mortar"]),
        apron_frame=Part(X + "apron_rafters", ["M_timber", "M_timber_weathered"]),
        apron=Part(X + "apron_shingles", ["M_roof_shake"]),
        tower_boards=Part(X + "tower_boards", TW),
        tower_frame=Part(X + "tower_frame", ["M_timber", "M_timber_weathered"]),
        tower_iron=Part(X + "tower_iron", ["M_iron"]),
        cap_frame=Part(X + "cap_frame", ["M_timber", "M_timber_weathered"]),
        cap_shingles=Part(X + "cap_shingles", ["M_roof_shingle"]),
        cap_iron=Part(X + "cap_iron", ["M_iron", "M_lead"]),
        windshaft=Part(X + "windshaft", ["M_timber", "M_iron"]),
        poll_end=Part(X + "poll_end", ["M_iron"]),
        rotor_iron=Part(X + "rotor_iron", ["M_iron"]),
        wheel_rim=Part(X + "wheel_rim", ["M_iron"]),
        wheel_blades=Part(X + "wheel_blades", ["M_timber"]),
        wheel_spokes=Part(X + "wheel_spokes", ["M_iron"]),
        props=Part(X + "props", TW),
        prop_anchors=Part(X + "prop_anchors", ["M_stone", "M_timber_weathered", "M_iron", "M_earth", "M_rubble"],
                          moss=0.1),
        prop_iron=Part(X + "prop_iron", ["M_iron"]),
        moss=Part(X + "moss_clumps", ["M_moss"], angle=60.0),
    )
    for L in "ABCD":
        parts["wheel_arm_%s" % L] = Part(X + "wheel_arm_%s" % L, ["M_timber_weathered", "M_iron"])
    parts["tail_boom"] = Part(X + "tail_boom", ["M_timber_weathered", "M_timber"])
    parts["tail_vane"] = Part(X + "tail_vane", ["M_timber_weathered", "M_timber"], wear=0.55)
    parts["tail_iron"] = Part(X + "tail_iron", ["M_iron"])
    return parts


def build_mill(parts, variant=False):
    """This mill = the kit components called with its numbers (or the kit-test variant's)."""
    if not variant:
        round_stone_drum(parts, r_base=2.60, r_top=2.45, height=4.62,
                         zones=dict(band=(2.55, 2.65, 2.82, 2.92)), windows=(70, -130),
                         door=dict(width=1.05, spring=1.65, reveal=0.30),
                         arcade=dict(n=10, clear_w=0.72, clear_h=1.08, z_sill=2.92, az0=18.0))
        build_ground(parts)
        smock_tower(parts, af_bottom=3.10, af_top=1.90, z0=5.95, z1=11.45)
        shake_apron(parts, r_eave=3.17, z_eave=4.62, r_top=1.60, z_top=6.00, courses=3)
        mill_cap(parts, length=2.76, width=2.56, rise=1.18, ridge_len=1.0, yaw=21.0)
        wind_wheel(parts, r_in=1.35, r_rim=3.20, r_tip=3.90, n_blades=16, pitch=13.0, hub_d=1.95)
        zb = tail_boom(parts)
        tail_vane(parts, zb)
        build_props(parts)
    else:
        # kit test (director round 4/5): drum r 2.0 m, tower 4.0 m tall, 12 blades - same code, other numbers
        round_stone_drum(parts, r_base=2.00, r_top=1.88, height=4.20,
                         zones=dict(band=(2.25, 2.35, 2.52, 2.62)), windows=(65, -125),
                         door=dict(width=1.0, spring=1.62, reveal=0.30),
                         arcade=dict(n=8, clear_w=0.66, clear_h=0.95, z_sill=2.62, az0=22.5), seed="kit")
        build_ground(parts)
        smock_tower(parts, af_bottom=2.70, af_top=1.90, z0=5.30, z1=9.30, seed="kit")
        shake_apron(parts, r_eave=2.50, z_eave=4.20, r_top=1.42, z_top=5.35, courses=3, seed="kit")
        mill_cap(parts, length=2.60, width=2.40, rise=1.05, ridge_len=0.9, yaw=21.0, seed="kit")
        wind_wheel(parts, r_in=1.20, r_rim=2.80, r_tip=3.40, n_blades=12, pitch=14.0, hub_d=1.85, seed="kit")
        zb = tail_boom(parts, x1=-5.6, seed="kit")
        tail_vane(parts, zb, s0=3.4, length=2.1, seed="kit")
        zc = Z_COLLAR - 0.11
        build_props(parts, props=((6, 0.32, zc, (-5.2, -1.0)), (6, -0.32, zc, (-5.0, 0.8)),
                                  (6, 0.58, float(TZ(7.30)), (-5.0, -2.6))))


LEANED = ("tower_", "cap_", "windshaft", "poll_end", "rotor_iron", "wheel_", "tail_")


def build_tail(parts):
    zb = tail_boom(parts)
    tail_vane(parts, zb)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    mats = {mn: bpy.data.materials.new(mn) for mn in MAT_NAMES}
    variant = bool(os.environ.get("MILL_KIT_VARIANT"))
    col = bpy.data.collections.new("MILL")
    scn.collection.children.link(col)
    parts = new_parts("MILL")
    build_mill(parts, variant=variant)
    log("built all kit components")

    # ---- clearance checks (spec G / I): rotating parts vs. tower, cap, apron, props ----
    rot = [p for k, p in parts.items() if k.startswith(("wheel_", "poll_end", "rotor_iron"))]
    stat = [parts[k] for k in ("tower_boards", "tower_frame", "tower_iron", "cap_frame", "cap_shingles", "cap_iron",
                               "apron", "curb", "props", "prop_anchors", "prop_iron", "tail_boom", "tail_vane",
                               "tail_iron")]
    def is_leaned(p):
        return p.name.replace("MILL_", "").startswith(LEANED)
    clr = clearance_report(rot, stat, lambda p, V: lean(V) if is_leaned(p) else V)
    for k, v in sorted(clr.items(), key=lambda kv: kv[1]):
        log("CLEARANCE rotor -> %-24s %.3f m" % (k, v))
    lowest = min(lean(np.concatenate(p.V))[:, 2].min() for p in rot if p.V)
    log("lowest rotating point z = %.3f m (apron top %.2f m, ground 0)" % (lowest, AP_ZT))
    rotor_internal_report(parts)
    log("CLEARANCE CHECK wheel vs apron/props/tail >= 0.30 m: %s" %
        ("PASS" if min(clr["MILL_apron_shingles"], clr["MILL_props"], clr["MILL_tail_vane"]) >= 0.30 else "FAIL"))
    tail_clearance(parts, lambda p, V: lean(V) if is_leaned(p) else V)

    total = 0
    for k in ("rubble", "prop_anchors"):
        parts[k].zmin = -0.005          # soil fillets / collars feather 4 mm into the ground (no crease)
    def ntris(me):
        lt = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", lt)
        return int((lt - 2).sum())
    pool_meshes = {}
    for p in Part.registry:
        out = p.build(col, mats, post=lean if is_leaned(p) else None)
        if out is None:
            continue
        if getattr(p, "mesh_only", False):
            pool_meshes[p.name.replace("MILL_pool_", "")] = out
            continue
        ntri = ntris(out.data)
        total += ntri
        log("%-28s tris %8d  (degenerate faces removed %d, on-ground faces culled %d, pieces re-wound outward %d,"
            " slivers alt<0.1mm %d, area<1e-8 %d)"
            % (p.name, ntri, p.n_degenerate, p.n_ground, getattr(p, "n_flipped", 0), p.n_alt, p.n_area))
    # linked duplicates of the shared variant meshes (producer note 3)
    sub = bpy.data.collections.new("MILL_instances")
    col.children.link(sub)
    L4 = np.eye(4)
    L4[:3, :3] = LEAN_R
    L4[:3, 3] = LEAN_PIVOT - LEAN_R @ LEAN_PIVOT
    from mathutils import Matrix
    used = {}
    for (name, key, M, leaned) in PLACEMENTS:
        ob = bpy.data.objects.new(name, pool_meshes[key])
        ob.matrix_world = Matrix((L4 @ M if leaned else M).tolist())
        sub.objects.link(ob)
        used[key] = used.get(key, 0) + 1
        total += ntris(ob.data)
    n_obj = len(col.all_objects)
    log("OBJECTS %d (%d unique merged meshes + %d linked duplicates of %d shared variant meshes: %s)"
        % (n_obj, len(col.objects), len(PLACEMENTS), len(used),
           ", ".join("%s x%d" % (k, v) for k, v in sorted(used.items()))))
    log("TOTAL tris", total, "objects", n_obj)
    bpy.context.view_layer.update()
    pts = np.concatenate([np.array([o.matrix_world @ Vector(c) for c in o.bound_box]) for o in col.all_objects])
    lo, hi = pts.min(0), pts.max(0)
    log("bbox", np.round(lo, 3), np.round(hi, 3))
    bpy.context.preferences.filepaths.save_version = 0     # no .blend1 backups in the building folder
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    log("saved", OUT_BLEND, "%.1f MB" % (os.path.getsize(OUT_BLEND) / 1e6))


if __name__ == "__main__":
    main()
