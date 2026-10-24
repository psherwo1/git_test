"""Builder round-1 interior-volume see-through probe for a1_longhouse_addons (adapted from the v6 barn auditor's
renders/variants/v6_barn/round_03/audit/aud_seethru_r03.py; read-only).
python -I bx_seethru_r01.py -- <blend> <out.json> [ring|close|all]
Camera rays (pinhole, like the renders) from a ground-eye ring round the longhouse and dense close-ups on the two
add-on junctions.  A ray is a LEAK if, before its first hit, it passes through the host's INTERIOR volume (the body
box shrunk 0.45 m, or the round end's drum shrunk 0.45 m, between z 0.05 and the roof top - 0.8 m), or if its first
hit is the ground inside it.  A first hit on a BACK face counts as VOID (a hollow / single-sided shell seen from
behind).  Coordinates are after the build's recentre (+4.606, -0.450)."""
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
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
names = [o.name for o in objs]
SX, SY = 4.606, -0.450
SH = 0.45
BX0, BX1, BY0, BY1 = -13.0 + SX + SH, -2.0 + SX, -2.6 + SY + SH, 2.6 + SY - SH      # body interior box
RC, RR = (SX, SY), 3.53 - SH                                                          # round end drum
GX0, GX1, GY0, GY1 = -13.0 + SX - 0.6, SX + 4.0, -2.6 + SY - 0.6, 2.6 + SY + 0.6
gx = np.arange(GX0, GX1 + 1e-6, 0.1); gy = np.arange(GY0, GY1 + 1e-6, 0.1)
ZT = np.zeros((len(gx), len(gy)))
for i, x in enumerate(gx):
    for j, y in enumerate(gy):
        h = bvh.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 40)
        ZT[i, j] = h[0].z if h[0] is not None else 0.0
ZT -= 0.8


def interior(p):
    x, y, z = p
    if z <= 0.05:
        return False
    inb = BX0 < x < BX1 and BY0 < y < BY1
    inr = math.hypot(x - RC[0], y - RC[1]) < RR
    if not (inb or inr):
        return False
    i = min(len(gx) - 1, max(0, int(round((x - GX0) / 0.1))))
    j = min(len(gy) - 1, max(0, int(round((y - GY0) / 0.1))))
    return z < ZT[i, j]


def seg_box(o, d, box):
    t0, t1 = 0.0, 1e9
    for k, (lo, hi) in enumerate(box):
        if abs(d[k]) < 1e-12:
            if not (lo < o[k] < hi):
                return None
        else:
            ta, tb = (lo - o[k]) / d[k], (hi - o[k]) / d[k]
            t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
    return (t0, t1) if t1 > t0 else None


IBOX = ((BX0, RC[0] + RR), (min(BY0, RC[1] - RR), max(BY1, RC[1] + RR)), (0.05, 12.0))


def shot(name, loc, tgt, lens, res):
    W, H = res
    loc, tgt = Vector(loc), Vector(tgt)
    fwd = (tgt - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
    sw = 36.0 / lens
    leaks, voids, n = [], [], 0
    img = np.zeros((H, W, 4), np.float32); img[..., 3] = 1.0
    Ld = Vector((0.4, -0.6, 0.7)).normalized()
    for py in range(H):
        for px in range(W):
            sx = ((px + 0.5) / W - 0.5) * sw
            sy = (0.5 - (py + 0.5) / H) * sw * H / W
            d = (fwd + right * sx + up * sy).normalized()
            n += 1
            h = bvh.ray_cast(loc, d, 80.0)
            if h[0] is not None:
                s = 0.15 + 0.75 * abs(h[1].dot(Ld)); img[H - 1 - py, px, :3] = (s, s, s)
            else:
                img[H - 1 - py, px, :3] = (0.3, 0.5, 0.9)
            tg = (-loc.z / d.z) if d.z < -1e-9 else 1e9
            th = h[3] if h[0] is not None else 1e9
            tf = min(th, tg)
            sb = seg_box(loc, d, IBOX)
            leak = None
            if sb is not None and sb[0] < tf:
                t = sb[0]
                while t < min(sb[1], tf):
                    p = loc + d * t
                    if interior(p):
                        leak = p; break
                    t += 0.02
            if leak is None and tg < th:
                p = loc + d * tg
                if interior((p.x, p.y, 0.06)):
                    leak = p
            if leak is not None:
                hn = names[OWN[h[2]]] if (h[0] is not None and th < tg) else ('GROUND' if tg < 1e8 else 'SKY')
                img[H - 1 - py, px, :3] = (1.0, 0.0, 0.0)
                leaks.append((px, py, [round(c, 3) for c in leak], hn))
                continue
            if h[0] is not None and th < tg and h[1].dot(d) > 0:
                img[H - 1 - py, px, :3] = (1.0, 0.85, 0.0)
                voids.append((px, py, [round(c, 3) for c in h[0]], names[OWN[h[2]]]))
    im = bpy.data.images.new(name, W, H, alpha=True); im.pixels.foreach_set(img.ravel())
    im.filepath_raw = IMG + '/' + name + '.png'; im.file_format = 'PNG'; im.save()
    return n, leaks, voids


res_out = {}


def run(name, loc, tgt, lens, res):
    n, L, Vd = shot(name, loc, tgt, lens, res)
    vo = {}
    for v in Vd:
        vo[v[3]] = vo.get(v[3], 0) + 1
    lo = {}
    for l in L:
        lo[l[3]] = lo.get(l[3], 0) + 1
    print(f"SHOT {name:30s} rays {n:7d} LEAK {len(L):4d} {dict(sorted(lo.items(), key=lambda kv: -kv[1])[:4])} "
          f"VOID {len(Vd):4d} {dict(sorted(vo.items(), key=lambda kv: -kv[1])[:5])}", flush=True)
    for v in Vd[:3]:
        print("     void", v)
    for l in L[:3]:
        print("     leak", l)
    res_out[name] = dict(rays=n, leaks=L[:200], voids=Vd[:200])


MODE = a[2] if len(a) > 2 else "all"
IMG = os.path.join(os.path.dirname(os.path.abspath(a[1])), 'probe_img'); os.makedirs(IMG, exist_ok=True)
CX = -4.0
if MODE in ("all", "ring"):
    for r, z, lens in ((7.0, 1.7, 24), (8.0, 6.0, 24)):
        for k in range(12):
            ang = 2 * math.pi * k / 12
            loc = (CX + (9.0 + r) * math.cos(ang), SY + (2.6 + r) * math.sin(ang), z)
            run(f"ring_r{r:.0f}_z{z:.0f}_{k:02d}", loc, (CX, SY, 2.6 if z < 3 else 2.2), lens, (400, 225))
LX, LY, LF = -1.294, 2.150, 4.350
PX, PY, PF = -2.394, -3.050, -4.050
if MODE in ("all", "close"):
    J = [
        ("L_junction_NE", (LX + 2.6, LF + 2.4, 2.9), (LX, LY + 0.05, 2.25), 35),
        ("L_junction_NW", (LX - 2.6, LF + 2.4, 2.9), (LX, LY + 0.05, 2.25), 35),
        ("L_under_host_eave_E", (LX + 2.4, LY + 0.9, 1.9), (LX + 0.6, LY, 2.35), 35),
        ("L_under_host_eave_W", (LX - 2.4, LY + 0.9, 1.9), (LX - 0.6, LY, 2.35), 35),
        ("L_inside", (LX + 0.3, LY + 1.3, 0.7), (LX - 0.3, LY + 0.05, 2.1), 18),
        ("L_verge_W_end", (LX - 3.0, LF + 0.5, 1.6), (LX - 2.0, LY + 0.3, 2.6), 40),
        ("L_verge_E_end", (LX + 3.0, LF + 0.5, 1.6), (LX + 2.0, LY + 0.3, 2.6), 40),
        ("L_6m", (LX + 1.0, LF + 5.5, 6.0), (LX, LY + 0.5, 2.0), 35),
        ("P_eye_S", (PX, PF - 4.0, 1.65), (PX, PY, 2.8), 35),
        ("P_eye_SW", (PX - 2.6, PF - 2.6, 1.65), (PX - 0.6, PY, 3.0), 35),
        ("P_eye_SE", (PX + 2.6, PF - 2.6, 1.65), (PX + 0.6, PY, 3.0), 35),
        ("P_lookup", (PX + 0.4, PF - 0.6, 1.6), (PX, PY - 0.1, 3.0), 22),
        ("P_side_W_high", (PX - 3.0, PF - 1.3, 3.7), (PX - 1.1, PY, 3.15), 40),
        ("P_side_E_high", (PX + 3.0, PF - 1.3, 3.7), (PX + 1.1, PY, 3.15), 40),
        ("P_6m", (PX + 2.0, PF - 5.0, 6.0), (PX, PY, 3.2), 35),
    ]
    ODX, ODY = (float(a[3]), float(a[4])) if len(a) > 4 else (0.0, 0.0)   # e.g. the same shots on v3 (-0.018 +0.255)
    ONLY = a[5:]
    for nm, loc, tgt, lens in J:
        if ONLY and not any(nm.startswith(p) for p in ONLY):
            continue
        loc = (loc[0] + ODX, loc[1] + ODY, loc[2]); tgt = (tgt[0] + ODX, tgt[1] + ODY, tgt[2])
        run(nm, loc, tgt, lens, (480, 270))
json.dump(res_out, open(a[1], "w"))
print("DONE")
