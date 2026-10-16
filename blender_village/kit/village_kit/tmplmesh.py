"""village_kit.tmplmesh -- template-instanced mesh batches: many pieces of one topology per numpy call.

Added in kit 1.2.0 with the tower-windmill migration.  It is the vectorised counterpart of core.Acc for the
buildings whose walls, roofs and rotors are laid as thousands of pieces sharing a few topologies (the mill drum
lays ~9k rubble stones, the cap ~600 shingles, the wheel 60 board blades):

  templates      tmpl_box(nx, ny, nz, drop_back, yfront, drop) -- a welded box grid with any faces dropped (the
                 buried / covered faces of producer note 6 are never built); tmpl_rings (lathe / sweep topology);
                 orient / flip_tmpl; T_* -- the shared templates (stones, dressed blocks, boards, shingles, planks)
  shapes         rbox(T, h, r) rounded boxes for N instances at once; sweep(path, prof); lathe(prof_rz, m);
                 circle_prof / rect_prof; profile_block; add_grid (a quad grid as one piece)
  transforms     rotm / euler / xform / frame_mats / unit; noise_field / lowfreq (smooth per-instance noise)
  timber         blocks_world, member (chamfered member between two points), hewn_beam / hewn_between (worn
                 arrises, adze scallops, checks, split end grain -- each switchable for producer note 11)
  BatchAcc       the accumulator: add(Vw (N, nv, 3), T, ...) adds N pieces (one Mask R / G per piece), then
                 build() -> a bpy mesh with palette slots (village_kit.palette), box UVs, smooth-by-angle sharp
                 edges, degenerate / buried-face removal, Nanite hygiene (core.nanite_clean) and the Mask attribute
                 (village_kit.mask.write_mask, the ONE writer); fill_acc() copies a batch into a core.Acc so pooled
                 variants go through village_kit.pools
  analysis       hull2d, chamfer_dt, part_samples, voxel_min_gap, HeightField, sliver_keep

Local frames: a template box is x along, y out of the surface (front face +y), z up, centred on 0.  Everything is
deterministic for a given np.random.Generator.  No building dimension lives here.
"""
import math
import os
import zlib

import numpy as np

try:
    import bpy
except ImportError:                    # pragma: no cover
    bpy = None

from . import palette
from . import mask as _mask
from .core import log, nanite_clean as _nanite_clean, sliver_report as _sliver_report

PI = math.pi
D2R = PI / 180.0


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


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


T_BLK_PLX = tmpl_box(4, 4, 4, drop={(2, 0), (0, 0)})     # baluster plinth (variant frame): no bed, no back


T_BLK_ABX = tmpl_box(4, 4, 4, drop={(2, 1), (0, 0)})     # baluster abacus: no head, no back


T_GRUB = tmpl_box(9, 4, 9, drop={(1, 0)})        # settled ground stone: local y is UP, no bed face (buried)


R_UPRIGHT = frame_mats(np.array([[1.0, 0, 0]]), np.array([[0, 0, 1.0]]), np.array([[0, -1.0, 0]]))[0]


def orient_open(T, P0):
    """Winding for an open ring surface (flag top + sides): the top centre fan must face up."""
    t = T["tris"][0]
    a, b, c = P0[t]
    return flip_tmpl(T) if np.cross(b - a, c - a)[2] < 0 else T


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


def perm_tmpl(T, odd):
    return flip_tmpl(T) if odd else T


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


# =============================================================================================
# BatchAcc: one Blender mesh object accumulated from template-instanced pieces
# =============================================================================================
def tower_b(V, VN, moss0=0.0, zoff=0.0):
    """Mask B (moss / dirt / damp) for tall buildings: high near the ground (bottom 1.2 m), on up-facing faces
    (ledges, sills, shingle butts) and on north (+Y) faces, lower high up on vertical faces.  World V."""
    z = V[:, 2] + zoff
    up = np.clip(VN[:, 2], 0, 1)
    b = 0.85 * np.clip(1 - z / 1.2, 0, 1) ** 1.5 + 0.35 * up ** 2 + 0.15 * np.clip(VN[:, 1], 0, 1) + moss0
    b *= 1 - 0.25 * np.clip((z - 3.0) / 8.0, 0, 1) * (1 - up)
    return np.clip(b, 0, 1)


class BatchAcc:
    """numpy accumulator of template-instanced pieces -> one mesh object (see the module doc).

        acc = BatchAcc("MILL_base_stones", ["M_stone"])
        acc.add(W (N, nv, 3), T, Pl=P_local, mat="M_stone", smooth="all" | "none" | "bevel", wear=None)
        ob = acc.build(collection, post=lean_fn)

    One add() call adds N pieces; Mask R is random per piece and Mask G = the part's wear baseline +-0.2 per piece
    (or `wear`, +-0.05).  smooth='bevel': the template's flat main faces flat, its rounded arrises smooth.
    mats are palette slot names (village_kit.palette.check)."""

    def __init__(self, name, mats, angle=33.0, wear=0.35, moss=0.0, mesh_only=False):
        self.name = name
        self.wear0 = wear           # Mask G baseline (per-piece wear, jittered per piece)
        self.moss0 = moss           # Mask B bias for this part (roof butts, ground pieces)
        self.R, self.G = [], []     # per-vertex Mask R (piece random) and G (piece wear)
        self.rng_mask = np.random.default_rng(zlib.crc32(("mask_" + name).encode("utf8")))
        self.mats = [palette.check(m) for m in mats]
        self.angle = angle          # smooth-by-angle threshold (deg): sharper dihedrals get split normals
        self.V = []
        self.Q, self.QM, self.QS, self.QU = [], [], [], []
        self.Tr, self.TM, self.TS, self.TU = [], [], [], []
        self.nv = 0
        self.calls = []
        self.rng_uv = np.random.default_rng(zlib.crc32(("uv_" + name).encode("utf8")))
        self.mesh_only = mesh_only
        self.zmin = 0.0             # anything below is cut flat (buried skirt limit)
        self.zref = 0.0             # height offset for Mask B of pooled (local-coordinate) meshes
        self.n_degenerate = self.n_ground = self.n_alt = self.n_area = 0

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
            # every solid piece faces OUTWARD in world space: several placement maps are mirror maps, so the
            # first instance's signed volume decides the winding
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
        """Drop whole pieces (e.g. shingles completely covered by a capping). keep_fn(V (N,nv,3)) -> bool (N,)."""
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

    def pieces(self):
        """iterate (V (nv,3), quads, tris, material index per face, Mask G) piece by piece (local vertex indices)."""
        qi = ti = 0
        vb = 0
        for ci, ((N, nv, nq, nt), V) in enumerate(zip(self.calls, self.V)):
            Vi = V.reshape(N, nv, 3)
            Q = self.Q[qi].reshape(N, nq, 4) if nq else None
            QM = self.QM[qi].reshape(N, nq) if nq else None
            Tt = self.Tr[ti].reshape(N, nt, 3) if nt else None
            TM = self.TM[ti].reshape(N, nt) if nt else None
            for j in range(N):
                b0 = vb + j * nv
                yield (Vi[j], Q[j] - b0 if nq else np.zeros((0, 4), np.int64),
                       Tt[j] - b0 if nt else np.zeros((0, 3), np.int64),
                       np.concatenate([QM[j] if nq else [], TM[j] if nt else []]).astype(int),
                       float(self.G[ci][j * nv]))
            qi += 1 if nq else 0
            ti += 1 if nt else 0
            vb += N * nv

    def build_mesh(self, post=None, b_fn=None, hygiene=True):
        """-> bpy mesh (see the class doc).  post(V) maps world positions (e.g. a tower lean); b_fn(V, VN) the
        Mask B (default tower_b with this part's moss bias / zref)."""
        if self.nv == 0:
            return None
        V = np.concatenate(self.V)
        if post is not None:
            V = post(V)
        V[:, 2] = np.maximum(V[:, 2], self.zmin)  # anything buried is cut flat at the ground
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        Tt = np.concatenate(self.Tr) if self.Tr else np.zeros((0, 3), np.int64)
        QU = np.concatenate(self.QU).reshape(-1, 4, 2) if self.QU else np.zeros((0, 4, 2))
        TU = np.concatenate(self.TU).reshape(-1, 3, 2) if self.TU else np.zeros((0, 3, 2))
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32)
        QS = np.concatenate(self.QS) if self.QS else np.zeros(0, bool)
        TS = np.concatenate(self.TS) if self.TS else np.zeros(0, bool)
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
        good_q = (a1 > eps) & (a2 > eps) & (b1 > eps) & (b2 > eps)
        # faces lying entirely on the ground cut (buried bottoms flattened by the clamp) can never be seen
        zc_ = self.zmin + 1e-5
        on_g = (V[Q, 2] <= zc_).all(1)
        tris_new, tu_new, tm_new, ts_new = [], [], [], []
        done = None
        for corner in range(4):
            keep_c = [c_ for c_ in range(4) if c_ != corner]
            sel = ~good_q & ~on_g & (tri_area(*[Q[:, c_] for c_ in keep_c]) > eps)
            if corner > 0:
                sel &= ~done
            done = sel if corner == 0 else (done | sel)
            if sel.any():
                tris_new.append(Q[sel][:, keep_c])
                tu_new.append(QU[sel][:, keep_c])
                tm_new.append(QM[sel])
                ts_new.append(QS[sel])
        good_t = tri_area(Tt[:, 0], Tt[:, 1], Tt[:, 2]) > eps if len(Tt) else np.zeros(0, bool)
        good_q &= ~on_g
        if len(Tt):
            good_t &= ~(V[Tt, 2] <= zc_).all(1)
        self.n_ground = int(on_g.sum())
        self.n_degenerate = int((~good_q).sum() + (~good_t).sum())
        Q, QU, QM, QS = Q[good_q], QU[good_q], QM[good_q], QS[good_q]
        Tt, TU, TM, TS = Tt[good_t], TU[good_t], TM[good_t], TS[good_t]
        if tris_new:
            Tt = np.concatenate([Tt] + tris_new)
            TU = np.concatenate([TU] + tu_new)
            TM = np.concatenate([TM] + tm_new)
            TS = np.concatenate([TS] + ts_new)
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
            me.materials.append(palette.material(mn))        # the ONE palette (producer note 7)
        me.validate(clean_customdata=False)
        # smooth by angle: smooth shading everywhere, every edge whose dihedral exceeds the threshold is sharp
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
        # per-piece Mask R / G ride along as point attributes through the hygiene pass (village_kit.mask)
        if len(me.vertices) == len(V):
            for nm_, arr in (("_mask_r", np.concatenate(self.R)), ("_mask_g", np.concatenate(self.G))):
                a_ = me.attributes.new(nm_, "FLOAT", "POINT")
                a_.data.foreach_set("value", arr.astype(np.float32))
        if hygiene and not os.environ.get("KIT_NOCLEAN"):
            self.n_alt, self.n_area = _nanite_clean(me)          # producer note 1 (core.nanite_clean)
        else:
            self.n_alt, self.n_area = _sliver_report(me)
        moss0, zref = self.moss0, self.zref
        _mask.write_mask(me, b_fn=b_fn or (lambda V_, VN_: tower_b(V_, VN_, moss0, zref)))
        return me

    def build(self, collection, post=None, b_fn=None, hygiene=True):
        me = self.build_mesh(post=post, b_fn=b_fn, hygiene=hygiene)
        if me is None:
            return None
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


def fill_acc(batch, acc, mat_override=None):
    """copy a BatchAcc into a core.Acc piece by piece (one add() per piece: the Mask R / G stay per piece), so a
    template-built variant goes through village_kit.pools (Pools.mesh(pool, k, make) with make = fill_acc)."""
    for V, Q, Tt, M, G in batch.pieces():
        faces = [f for f in (Q, Tt) if len(f)]
        mat = mat_override or batch.mats[int(M[0]) if len(M) else 0]
        acc.add(V, faces, mat, smooth=True, wear=G)
