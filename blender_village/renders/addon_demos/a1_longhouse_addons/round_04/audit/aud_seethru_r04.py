"""Auditor a1_longhouse_addons round-4 interior-volume see-through probe (read-only), after the barn's round-3 audit
(renders/variants/v6_barn/round_03/audit/aud_seethru_r03.py), vectorised.
    blender -b -P aud_seethru_r04.py -- <blend> <out.json> [ring|close|all] [only shot names...]
Pinhole camera rays (like the renders) from ground-eye (1.7 m) and 6 m rings round the building and from close-up
cameras on every add-on junction (the director's r04 exterior camera positions plus ground / 6 m auditor views).
Each ray's first hit is found on the whole building; the ground is the plane z = 0.  Three closed or semi-closed zones:
  HOST   the longhouse body + round drum interior (inside the outer faces shrunk SH, z 0.05 .. top-roof-surface - 0.8 m).
         A ray that passes through it before its first hit (or whose first hit is the ground inside it) is a LEAK.
         Each leak ray gets an aperture = 2 x the narrowest nearest-surface clearance on its last 1.5 m before entering
         (a designed door / window reads >= 0.2 m; a slit reads cm), and is clustered by that pinch point.
  SHED   the lean-to store between its end walls, 0.30 m off the host wall, 0.20 m behind the front, up to the
         underside of its framing / deck - 3 cm.  It is open at the front, so a ray through it is a LEAK only if its
         first hit is the sky, the ground outside the shed, or the HOST ROOF (a gap in the shed roof or its crease).
  HOOD   the strip under the porch hood next to the wall (rays climbing steeper than 0.3): a LEAK if its first hit is
         the sky or the host roof (a gap at the hood's crease / wall junction).
A ray whose first hit is a BACK face is a VOID (a hollow seen from behind; not see-through)."""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
MODE = a[2] if len(a) > 2 else "all"
ONLY = a[3:]
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off = [], [], [], 0
for oi, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(m.loop_triangles), oi)); off += len(co)
    o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
_fin = [i for i, o in enumerate(objs) if o.name.endswith("_finial")]
if _fin and os.environ.get("AUD_ALIGN"):      # another build (e.g. the accepted v3): align its finial to a1's
    _tv = T[OWN == _fin[0]].ravel(); _p = V[_tv]
    _sh = np.array([4.6075, -0.3335]) - 0.5 * (_p.min(0)[:2] + _p.max(0)[:2])
    V[:, :2] += _sh
    print("ALIGNED by", _sh.round(4).tolist(), flush=True)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
names = [o.name for o in objs]
HOSTROOF = np.array([("_porch" not in n and "_lean_to" not in n) and (("body_roof" in n) or n.endswith(("_shingles", "_battens", "_rafters", "_starter", "_underlap",
                                                        "_soffit_deck", "_eave_fill", "_cap_collar")))
                     for n in names])
BLOCK = np.array(["_blockers" in n for n in names])
SHED_OK = np.array([("_lean_to" in n) or ("body_wall" in n) for n in names])

# ---- geometry (world = plan + (4.606, -0.328)) -----------------------------------------------------------------
XG, XE, YN, YS = -8.394, 2.606, 2.272, -2.928      # gable face, body end at the drum, N / S outer faces
RC = np.array([4.606, -0.328]); RF, BAT = 3.70, math.radians(1.5)
SH = 0.45            # the walls are facing skins; window reveals / blockers reach 0.33 m in
BX0, BX1, BY0, BY1 = XG + SH, XE, YS + SH, YN - SH
HX0, HX1, HY0, HY1 = XG + SH, RC[0] + RF - SH, RC[1] - RF + SH, RC[1] + RF - SH   # union bounding box
G = 0.1
gx = np.arange(HX0, HX1 + 1e-6, G); gy = np.arange(HY0, HY1 + 1e-6, G)
ZT = np.zeros((len(gx), len(gy)))
for i, x in enumerate(gx):
    for j, y in enumerate(gy):
        o = Vector((x, y, 30.0)); z = 0.0
        in_body = (BX0 - G <= x <= BX1 + G and BY0 - G <= y <= BY1 + G
                   and np.hypot(x - RC[0], y - RC[1]) > RF - SH - G)
        for _ in range(12):        # over the body (outside the drum): the BODY roof, not the cone's oversailing eave
            h = bvh.ray_cast(o, Vector((0, 0, -1)), 40)
            if h[0] is None:
                break
            if not in_body or "body_roof" in names[OWN[h[2]]] or "body_wall" in names[OWN[h[2]]]:
                z = h[0].z; break
            o = h[0] + Vector((0, 0, -1e-4))
        ZT[i, j] = z
ZT -= 0.8
ZTOP = float(ZT.max())


def host_in(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    body = (x > BX0) & (x < BX1) & (y > BY0) & (y < BY1)
    r = np.hypot(x - RC[0], y - RC[1])
    drum = r < (RF - np.maximum(z, 0) * math.tan(BAT) - SH)
    i = np.clip(np.round((x - HX0) / G).astype(int), 0, len(gx) - 1)
    j = np.clip(np.round((y - HY0) / G).astype(int), 0, len(gy) - 1)
    return (body | drum) & (z > 0.05) & (z < ZT[i, j])


def host_foot(x, y):
    body = (x > BX0) & (x < BX1) & (y > BY0) & (y < BY1)
    return body | (np.hypot(x - RC[0], y - RC[1]) < RF - SH)


# shed: x between the end walls' inner faces, y 0.30 off the host wall .. 0.20 behind the front
SX0, SX1, SY0, SY1 = -3.194 + 0.05, 0.006 - 0.05, YN + 0.30, 4.272 - 0.20
sgx = np.arange(SX0, SX1 + 1e-6, 0.05); sgy = np.arange(SY0, SY1 + 1e-6, 0.05)
SZ = np.zeros((len(sgx), len(sgy)))
for i, x in enumerate(sgx):
    for j, y in enumerate(sgy):
        h = bvh.ray_cast(Vector((x, y, 0.4)), Vector((0, 0, 1)), 10)
        SZ[i, j] = (h[0].z if h[0] is not None else 0.4) - 0.03
SZTOP = float(SZ.max())
print(f"SHED ceiling (underside - 3 cm): {SZ.min():.3f}..{SZTOP:.3f}; HOST ceiling max {ZTOP:.3f}", flush=True)


def shed_in(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    i = np.clip(np.round((x - SX0) / 0.05).astype(int), 0, len(sgx) - 1)
    j = np.clip(np.round((y - SY0) / 0.05).astype(int), 0, len(sgy) - 1)
    return (x > SX0) & (x < SX1) & (y > SY0) & (y < SY1) & (z > 0.05) & (z < SZ[i, j])


# hood strip: under the porch hood within 0.45 m of the wall, between the brackets
DX = -2.394
QX0, QX1, QY0, QY1, QZ0 = DX - 0.85, DX + 0.85, YS - 0.45, YS - 0.03, 2.75
qgx = np.arange(QX0, QX1 + 1e-6, 0.05); qgy = np.arange(QY0, QY1 + 1e-6, 0.03)
QZ = np.zeros((len(qgx), len(qgy)))
for i, x in enumerate(qgx):
    for j, y in enumerate(qgy):
        h = bvh.ray_cast(Vector((x, y, 2.6)), Vector((0, 0, 1)), 10)
        QZ[i, j] = (h[0].z if h[0] is not None else 2.6) - 0.02
QZTOP = float(QZ.max())
print(f"HOOD strip ceiling: {QZ.min():.3f}..{QZTOP:.3f}", flush=True)


def hood_in(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    i = np.clip(np.round((x - QX0) / 0.05).astype(int), 0, len(qgx) - 1)
    j = np.clip(np.round((y - QY0) / 0.03).astype(int), 0, len(qgy) - 1)
    return (x > QX0) & (x < QX1) & (y > QY0) & (y < QY1) & (z > QZ0) & (z < QZ[i, j])


def slab(O, D, lo, hi, tmax):
    """vectorised ray / box: t-interval [t0, t1] clipped to [0, tmax]; empty where t1 <= t0"""
    t0 = np.zeros(len(O)); t1 = tmax.copy()
    for k in range(3):
        d = D[:, k]; o = O[:, k]
        with np.errstate(divide="ignore", invalid="ignore"):
            ta = (lo[k] - o) / d; tb = (hi[k] - o) / d
        par = np.abs(d) < 1e-12
        ta = np.where(par, np.where((o > lo[k]) & (o < hi[k]), -1e18, 1e18), ta)
        tb = np.where(par, np.where((o > lo[k]) & (o < hi[k]), 1e18, -1e18), tb)
        t0 = np.maximum(t0, np.minimum(ta, tb)); t1 = np.minimum(t1, np.maximum(ta, tb))
    return t0, t1


def first_inside(O, D, t0, t1, fn, step):
    """for each ray, the first t in [t0, t1) where fn(point) is True (inf if none)"""
    res = np.full(len(O), np.inf)
    idx = np.flatnonzero(t1 > t0)
    if len(idx) == 0:
        return res
    n = np.ceil((t1[idx] - t0[idx]) / step).astype(int) + 1
    for c0 in range(0, len(idx), 4000):
        ii = idx[c0:c0 + 4000]; nn = n[c0:c0 + 4000]
        rep = np.repeat(np.arange(len(ii)), nn)
        k = np.arange(nn.sum()) - np.repeat(np.cumsum(nn) - nn, nn)
        t = np.minimum(t0[ii][rep] + k * step, t1[ii][rep] - 1e-6)
        P = O[ii][rep] + D[ii][rep] * t[:, None]
        ok = fn(P)
        if ok.any():
            tt = np.where(ok, t, np.inf)
            mn = np.full(len(ii), np.inf); np.minimum.at(mn, rep, tt)
            res[ii] = mn
    return res


IMG = os.path.join(os.path.dirname(os.path.abspath(a[1])), "probe_img"); os.makedirs(IMG, exist_ok=True)
res_out = {}
TOT = {"HOST": 0, "SHED": 0, "HOOD": 0, "rays": 0, "void": 0}


def shot(name, loc, tgt, lens, res):
    W, H = res
    loc, tgt = Vector(loc), Vector(tgt)
    fwd = (tgt - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
    sw = 36.0 / lens
    px, py = np.meshgrid(np.arange(W), np.arange(H))
    px = px.ravel(); py = py.ravel()
    sx = ((px + 0.5) / W - 0.5) * sw; sy = (0.5 - (py + 0.5) / H) * sw * H / W
    F, R, U = np.array(fwd), np.array(right), np.array(up)
    D = F[None] + sx[:, None] * R[None] + sy[:, None] * U[None]
    D /= np.linalg.norm(D, axis=1)[:, None]
    N = len(D)
    O = np.repeat(np.array(loc)[None], N, 0)
    th = np.full(N, np.inf); own = np.full(N, -1); back = np.zeros(N, bool); HP = np.zeros((N, 3))
    lv = loc
    for k in range(N):
        d = Vector(D[k])
        h = bvh.ray_cast(lv, d, 80.0)
        if h[0] is not None:
            th[k] = h[3]; own[k] = OWN[h[2]]; back[k] = h[1].dot(d) > 0; HP[k] = h[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        tg = np.where(D[:, 2] < -1e-9, -loc.z / D[:, 2], np.inf)
    tf = np.minimum(th, tg)
    tfc = np.where(np.isfinite(tf), tf, 80.0)
    gnd = tg < th
    GP = O + D * np.where(np.isfinite(tg), tg, 0.0)[:, None]
    # HOST
    t0, t1 = slab(O, D, (HX0, HY0, 0.05), (HX1, HY1, ZTOP), tfc)
    tin = first_inside(O, D, t0, t1, host_in, 0.02)
    host_leak = np.isfinite(tin) | (gnd & host_foot(GP[:, 0], GP[:, 1]))
    win = host_leak & (own >= 0) & ~gnd & BLOCK[np.maximum(own, 0)]     # through a window onto its blocker
    TOT["window_blocker"] = TOT.get("window_blocker", 0) + int(win.sum())
    host_leak &= ~win
    # SHED
    t0, t1 = slab(O, D, (SX0, SY0, 0.05), (SX1, SY1, SZTOP), tfc)
    sin_ = first_inside(O, D, t0, t1, shed_in, 0.02)
    shed_ok_hit = (own >= 0) & ~gnd & SHED_OK[np.maximum(own, 0)]
    gnd_in_shed = gnd & (GP[:, 0] > SX0 - 0.1) & (GP[:, 0] < SX1 + 0.1) & (GP[:, 1] > YN - 0.01) & (GP[:, 1] < 4.30)
    shed_leak = np.isfinite(sin_) & ~shed_ok_hit & ~gnd_in_shed & ~host_leak
    # HOOD (steep rays only)
    t0, t1 = slab(O, D, (QX0, QY0, QZ0), (QX1, QY1, QZTOP), tfc)
    qin = first_inside(O, D, t0, t1, hood_in, 0.01)
    sky = ~np.isfinite(tf)
    hood_leak = np.isfinite(qin) & (D[:, 2] > 0.3) & (sky | ((own >= 0) & ~gnd & HOSTROOF[np.maximum(own, 0)]))
    void = (own >= 0) & ~gnd & back & ~host_leak & ~shed_leak & ~hood_leak
    out = {"rays": N}
    for lab, mask, tz in (("HOST", host_leak, tin), ("SHED", shed_leak, sin_), ("HOOD", hood_leak, qin)):
        idx = np.flatnonzero(mask)
        TOT[lab] += len(idx)
        recs = []
        for k in idx[:400]:
            d = Vector(D[k]); te = tz[k] if np.isfinite(tz[k]) else tg[k]
            ap, pin = 9.0, None
            for t in np.linspace(max(0.0, te - 1.5), te, 60):
                p = loc + d * t
                dd = bvh.find_nearest(p)[3]
                if dd < ap:
                    ap, pin = dd, p
            hn = names[own[k]] if (own[k] >= 0 and not gnd[k]) else ("GROUND" if gnd[k] else "SKY")
            recs.append(dict(px=int(px[k]), py=int(py[k]), aperture=round(2 * ap, 4),
                             pinch=[round(c, 3) for c in pin], entry=[round(c, 3) for c in (loc + d * te)], first_hit=hn,
                             hit=[round(c, 3) for c in (HP[k] if hn not in ("SKY", "GROUND") else GP[k])]))
        out[lab] = dict(n=int(len(idx)), recs=recs)
    TOT["rays"] += N; TOT["void"] += int(void.sum())
    vo = {}
    for k in np.flatnonzero(void):
        vo[names[own[k]]] = vo.get(names[own[k]], 0) + 1
    out["void"] = dict(n=int(void.sum()), by=dict(sorted(vo.items(), key=lambda kv: -kv[1])[:6]))
    print(f"SHOT {name:40s} rays {N:7d} WIN {int(win.sum()):5d} HOST {out['HOST']['n']:5d} SHED {out['SHED']['n']:4d} HOOD {out['HOOD']['n']:4d}"
          f" VOID {out['void']['n']:5d} {out['void']['by']}", flush=True)
    for lab in ("HOST", "SHED", "HOOD"):
        recs = out[lab]["recs"]
        if not recs:
            continue
        cl = {}
        for r_ in recs:
            kk = tuple(round(c / 0.2) * 0.2 for c in r_["pinch"]) + tuple(round(c / 0.2) * 0.2 for c in r_["entry"])
            e = cl.setdefault(kk, [0, 0.0, {}])
            e[0] += 1; e[1] = max(e[1], r_["aperture"]); e[2][r_["first_hit"]] = e[2].get(r_["first_hit"], 0) + 1
        print(f"     {lab} pinch | entry clusters (0.2 m): n / max aperture m / first hits:",
              sorted(((round(k[0], 1), round(k[1], 1), round(k[2], 1), "|", round(k[3], 1), round(k[4], 1), round(k[5], 1), v[0], round(v[1], 3),
                       dict(sorted(v[2].items(), key=lambda kv: -kv[1])[:3])) for k, v in cl.items()),
                     key=lambda t: -t[7])[:8], flush=True)
    if host_leak.any() or shed_leak.any() or hood_leak.any():
        img = np.zeros((H, W, 4), np.float32); img[..., 3] = 1
        shade = np.where(np.isfinite(tf), 0.5, 0.15)
        img[py, px, 0] = shade; img[py, px, 1] = shade; img[py, px, 2] = shade
        for mask, col in ((host_leak, (1, 0, 0)), (shed_leak, (1, 0, 1)), (hood_leak, (0, 1, 1)), (void, (1, .85, 0))):
            k = np.flatnonzero(mask)
            for c in range(3):
                img[py[k], px[k], c] = col[c]
        im = bpy.data.images.new(name, W, H, alpha=True); im.pixels.foreach_set(img[::-1].ravel())
        im.filepath_raw = IMG + "/" + name + ".png"; im.file_format = "PNG"; im.save()
    res_out[name] = out


C = (0.0, -0.33)
if MODE in ("all", "ring"):
    for r, z, lens in ((6.0, 1.7, 24), (12.0, 1.7, 30), (8.0, 6.0, 24), (14.0, 6.0, 30)):
        for k in range(16):
            ang = 2 * math.pi * k / 16
            loc = (C[0] + (8.9 + r) * math.cos(ang), C[1] + (4.3 + r) * math.sin(ang), z)
            nmx = f"ring_r{r:.0f}_z{z:.0f}_{k:02d}"
            if ONLY and nmx not in ONLY:
                continue
            shot(nmx, loc, (C[0], C[1], 3.2 if z < 3 else 2.6), lens, (320, 180))
if MODE in ("all", "close"):
    SX, SY = 0.0, -0.075
    LX, LY, LF = -1.594, 2.347, 4.347              # director's round-2 plan numbers (+ SY below)
    PX, PY = -2.394, -2.853
    DIR = {   # the director's r04 EXTERIOR cameras (dir_render_r04.py), world = these + (SX, SY)
        "h01": ((LX - 7.0, LY + 1.3, 1.7), (LX - 2.0, LY + 1.0, 2.6), 35),
        "h02": ((LX + 7.0, LY + 1.3, 1.7), (LX + 2.0, LY + 1.0, 2.6), 35),
        "h03": ((LX - 2.7, LY + 1.5, 1.1), (LX - 2.2, LY + 0.8, 2.75), 26),
        "h04": ((LX + 2.7, LY + 1.5, 1.1), (LX + 2.2, LY + 0.8, 2.75), 26),
        "h05": ((LX - 5.5, LF + 4.5, 3.4), (LX - 1.2, LY + 1.0, 2.6), 35),
        "h07": ((LX - 3.4, LY + 1.5, 4.3), (LX - 2.35, LY + 0.05, 3.0), 38),
        "h08": ((LX + 3.4, LY + 1.5, 4.3), (LX + 2.35, LY + 0.05, 3.0), 38),
        "h09": ((LX - 3.2, LF + 1.6, 2.5), (LX - 2.0, LY + 0.6, 3.0), 30),
        "x01": ((LX - 3.7, LF + 0.65, 3.1), (LX - 1.9, LY + 0.75, 2.7), 40),
        "x02": ((LX + 3.7, LF + 0.65, 3.1), (LX + 1.9, LY + 0.75, 2.7), 40),
        "x10": ((LX + 2.7, LF + 4.65, 1.6), (LX, LY + 0.85, 1.9), 35),
        "x13": ((LX - 4.0, LF + 0.6, 3.4), (LX - 2.2, LY + 0.4, 3.2), 40),
        "x15": ((LX + 2.6, LF + 1.4, 2.0), (LX + 1.8, LF - 0.1, 2.3), 40),
        "z01": ((LX + 2.9, LY + 0.95, 3.0), (LX + 2.0, LY + 0.05, 2.8), 40),
        "z05": ((-7.6, 3.9, 2.4), (-6.2, 2.3, 2.75), 35),
        "z06": ((-7.0, 3.3, 3.0), (-6.2, 2.35, 2.8), 40),
        "z07": ((LX - 5.2, LY + 1.4, 3.6), (LX - 3.2, LY, 3.3), 34),
        "r01": ((LX - 3.3, LY + 1.1, 3.3), (LX - 2.4, LY + 0.05, 2.75), 42),
        "r02": ((LX + 3.3, LY + 1.1, 3.3), (LX + 2.4, LY + 0.05, 2.75), 42),
        "r03": ((LX - 1.2, LF + 0.9, 1.4), (LX - 2.2, LF + 0.1, 2.5), 30),
        "r04": ((LX + 0.6, LF + 2.6, 1.65), (LX, LF, 2.45), 30),
        "r05": ((LX - 2.9, LY + 0.9, 2.0), (LX - 2.45, LY + 0.1, 2.85), 32),
        "p01": ((PX + 3.2, PY - 1.6, 2.5), (PX + 0.3, PY - 0.5, 2.8), 35),
        "p02": ((PX - 3.2, PY - 1.6, 2.5), (PX - 0.3, PY - 0.5, 2.8), 35),
        "p03": ((PX - 1.6, PY - 1.4, 3.9), (PX - 1.0, PY - 0.1, 3.05), 40),
        "p04": ((PX + 1.6, PY - 1.4, 3.9), (PX + 1.0, PY - 0.1, 3.05), 40),
        "p05": ((PX + 1.2, PY - 4.6, 1.65), (PX, PY - 0.5, 2.4), 32),
    }
    J = [(f"dir_{k}", (l[0] + SX, l[1] + SY, l[2]), (t[0] + SX, t[1] + SY, t[2]), f) for k, (l, t, f) in DIR.items()]
    # auditor views (world): ground-eye and 6 m on every junction, and looking INTO the shed / under the hood
    LXw, LNw, LFw = -1.594, 2.272, 4.272
    PFw = -3.928
    J += [
        ("aud_shed_in_up_crease", (LXw + 0.4, LFw + 2.2, 1.0), (LXw, LNw + 0.1, 3.0), 24),
        ("aud_shed_in_up_W_hip", (LXw + 1.0, LFw + 2.0, 1.2), (LXw - 1.9, LNw + 0.6, 2.9), 26),
        ("aud_shed_in_up_E_hip", (LXw - 1.0, LFw + 2.0, 1.2), (LXw + 1.9, LNw + 0.6, 2.9), 26),
        ("aud_shed_in_low", (LXw, LFw + 1.2, 0.5), (LXw, LNw + 0.3, 2.9), 20),
        ("aud_shed_W_end_eye", (LXw - 4.5, LFw + 2.5, 1.7), (LXw - 2.0, LNw + 0.1, 3.0), 35),
        ("aud_shed_E_end_eye", (LXw + 4.5, LFw + 2.5, 1.7), (LXw + 2.0, LNw + 0.1, 3.0), 35),
        ("aud_shed_W_end_6m", (LXw - 5.0, LFw + 4.0, 6.0), (LXw - 2.0, LNw + 0.1, 3.0), 35),
        ("aud_shed_E_end_6m", (LXw + 5.0, LFw + 4.0, 6.0), (LXw + 2.0, LNw + 0.1, 3.0), 35),
        ("aud_shed_crease_6m", (LXw, LFw + 6.0, 6.0), (LXw, LNw, 3.3), 30),
        ("aud_back_head_W_6m", (-5.6, LNw + 6.0, 6.0), (-5.6, LNw, 3.2), 30),
        ("aud_back_head_W_eye", (-5.6, LNw + 5.0, 1.7), (-5.6, LNw, 3.2), 30),
        ("aud_NW_corner_eye", (XG - 3.0, LNw + 3.0, 1.7), (XG, LNw, 2.8), 35),
        ("aud_NW_corner_6m", (XG - 4.0, LNw + 4.0, 6.0), (XG, LNw, 2.9), 35),
        ("aud_SW_corner_eye", (XG - 3.0, YS - 3.0, 1.7), (XG, YS, 2.8), 35),
        ("aud_SW_corner_6m", (XG - 4.0, YS - 4.0, 6.0), (XG, YS, 2.9), 35),
        ("aud_back_head_E_6m", (1.6, LNw + 6.0, 6.0), (1.6, LNw, 3.2), 30),
        ("aud_hood_under_up", (DX, PFw - 0.2, 1.6), (DX, YS - 0.1, 3.0), 22),
        ("aud_hood_under_W", (DX + 0.6, PFw - 0.6, 1.5), (DX - 1.0, YS - 0.1, 2.95), 26),
        ("aud_hood_under_E", (DX - 0.6, PFw - 0.6, 1.5), (DX + 1.0, YS - 0.1, 2.95), 26),
        ("aud_hood_W_eye", (DX - 3.5, PFw - 2.0, 1.7), (DX - 1.1, YS, 3.0), 35),
        ("aud_hood_E_eye", (DX + 3.5, PFw - 2.0, 1.7), (DX + 1.1, YS, 3.0), 35),
        ("aud_hood_6m", (DX + 1.0, PFw - 5.0, 6.0), (DX, YS, 3.2), 32),
        ("aud_front_head_W_6m", (-5.4, YS - 6.0, 6.0), (-5.4, YS, 3.1), 30),
        ("aud_front_head_E_6m", (0.6, YS - 6.0, 6.0), (0.6, YS, 3.1), 30),
    ]
    for nm_, loc, tgt, lens in J:
        if ONLY and nm_ not in ONLY:
            continue
        shot(nm_, loc, tgt, lens, (480, 270))
print("TOTALS", TOT)
json.dump(res_out, open(a[1], "w"))
print("DONE")
