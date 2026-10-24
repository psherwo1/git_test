"""Auditor v6_barn round-3 see-through / void probe (read-only).  blender -b -P aud_seethru_r03.py -- <blend> <out.json>
Camera rays (pinhole, like the renders) from (A) ground-eye (1.7 m) and 6 m rings round the barn, and (B) dense
close-up windows on every module junction.  Each ray's first hit is found on the whole building; the ground is the
plane z = 0.  A ray is a LEAK if, before its first hit, it passes through the barn's INTERIOR volume (inside the
footprint shrunk 0.25 m, between z 0.05 and the roof covering's underside - 0.8 m), or if its first hit is the ground
inside that footprint.  A ray whose first hit is a BACK face (looking into a hollow / a single-sided shell from
behind) is counted as VOID.  Leaks and voids are reported per shot with their pixel / world positions."""
import json
import math
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
CX, FW, BW, GW, GE = 0.058, -3.499, 3.501, -6.942, 7.058
SH = 0.45
IX0, IX1, IY0, IY1 = GW + SH, GE - SH, FW + SH, BW - SH
# roof underside proxy: the top roof surface (first hit from above) on a 0.1 m grid
gx = np.arange(IX0, IX1 + 1e-6, 0.1); gy = np.arange(IY0, IY1 + 1e-6, 0.1)
ZT = np.zeros((len(gx), len(gy)))
for i, x in enumerate(gx):
    for j, y in enumerate(gy):
        h = bvh.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 40)
        ZT[i, j] = h[0].z if h[0] is not None else 0.0
ZT -= 0.8


def interior(p):
    x, y, z = p
    if not (IX0 < x < IX1 and IY0 < y < IY1 and z > 0.05):
        return False
    i = min(len(gx) - 1, max(0, int(round((x - IX0) / 0.1))))
    j = min(len(gy) - 1, max(0, int(round((y - IY0) / 0.1))))
    return z < ZT[i, j]


def seg_box(o, d):
    """t-interval of the ray inside the interior box (xy footprint, z 0.05..9)"""
    t0, t1 = 0.0, 1e9
    for k, (lo, hi) in enumerate(((IX0, IX1), (IY0, IY1), (0.05, 9.0))):
        if abs(d[k]) < 1e-12:
            if not (lo < o[k] < hi):
                return None
        else:
            ta, tb = (lo - o[k]) / d[k], (hi - o[k]) / d[k]
            t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
    return (t0, t1) if t1 > t0 else None


def seg_box2(o, d):
    t0, t1 = 0.0, 1e9
    for k, (lo, hi) in enumerate(((GW, GE), (FW, BW), (0.0, 9.0))):
        if abs(d[k]) < 1e-12:
            if not (lo < o[k] < hi):
                return None
        else:
            ta, tb = (lo - o[k]) / d[k], (hi - o[k]) / d[k]
            t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
    return (t0, t1) if t1 > t0 else None


def shot(name, loc, tgt, lens, res, win=None):
    """win = (u0, u1, v0, v1) fractions of the frame to sample (default all)"""
    W, H = res
    loc, tgt = Vector(loc), Vector(tgt)
    fwd = (tgt - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
    sw = 36.0 / lens                      # sensor width / focal (Blender default sensor 36 mm, fit horizontal)
    u0, u1, v0, v1 = win or (0, 1, 0, 1)
    leaks, voids, n = [], [], 0
    img = np.zeros((H, W, 4), np.float32); img[..., 3] = 1.0
    Ld = Vector((0.4, -0.6, 0.7)).normalized()
    for py in range(int(v0 * H), int(v1 * H)):
        for px in range(int(u0 * W), int(u1 * W)):
            sx = ((px + 0.5) / W - 0.5) * sw
            sy = (0.5 - (py + 0.5) / H) * sw * H / W
            d = (fwd + right * sx + up * sy).normalized()
            n += 1
            h = bvh.ray_cast(loc, d, 80.0)
            if h[0] is not None:
                sh = 0.15 + 0.75 * abs(h[1].dot(Ld)); img[H - 1 - py, px, :3] = (sh, sh, sh)
            else:
                img[H - 1 - py, px, :3] = (0.3, 0.5, 0.9)
            tg = (-loc.z / d.z) if d.z < -1e-9 else 1e9            # the ground plane z = 0
            th = h[3] if h[0] is not None else 1e9
            tf = min(th, tg)
            # pass through the interior before the first hit?
            sb = seg_box(loc, d)
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
                if IX0 < p.x < IX1 and IY0 < p.y < IY1:
                    leak = p
            if leak is not None:
                eb = seg_box2(loc, d)
                ent = loc + d * eb[0] if eb else leak
                hn = names[OWN[h[2]]] if (h[0] is not None and th < tg) else ('GROUND' if tg < 1e8 else 'SKY')
                hp = [round(c, 3) for c in (h[0] if (h[0] is not None and th < tg) else loc + d * min(tg, 40.0))]
                hb = names[OWN[h[2]]] if (h[0] is not None and th < tg) else ''
                img[H - 1 - py, px, :3] = (0.0, 0.8, 1.0) if 'blocker' in hb else (1.0, 0.0, 0.0)
                leaks.append((px, py, [round(c, 3) for c in leak], [round(c, 3) for c in ent], hn, hp))
                continue
            if h[0] is not None and th < tg and h[1].dot(d) > 0:
                img[H - 1 - py, px, :3] = (1.0, 0.85, 0.0)
                voids.append((px, py, [round(c, 3) for c in h[0]], names[OWN[h[2]]]))
    if IMG:
        im = bpy.data.images.new(name, W, H, alpha=True); im.pixels.foreach_set(img.ravel())
        im.filepath_raw = IMG + '/' + name + '.png'; im.file_format = 'PNG'; im.save()
    return n, leaks, voids


res_out = {}


def run(name, loc, tgt, lens, res, win=None):
    n, L, Vd = shot(name, loc, tgt, lens, res, win)
    vo = {}
    for v in Vd:
        vo[v[3]] = vo.get(v[3], 0) + 1
    print(f"SHOT {name:30s} rays {n:7d} LEAK {len(L):4d} VOID {len(Vd):4d} {dict(sorted(vo.items(), key=lambda kv: -kv[1])[:5])}",
          flush=True)
    cl = {}
    for l in L:
        k = tuple(round(c / 0.1) * 0.1 for c in l[3])
        cl[k] = cl.get(k, 0) + 1
    print('     leak entry clusters (0.1 m):', sorted(((round(k[0],1), round(k[1],1), round(k[2],1), v) for k, v in cl.items()), key=lambda t: -t[3])[:8])
    cv = {}
    for v in Vd:
        k = (v[3],) + tuple(round(c / 0.1) * 0.1 for c in v[2])
        cv[k] = cv.get(k, 0) + 1
    ch = {}
    for l in L:
        k = (l[4],) + tuple(round(c / 0.2) * 0.2 for c in l[5])
        ch[k] = ch.get(k, 0) + 1
    print('     leak first-hit clusters (0.2 m):', sorted(((k[0], round(k[1],1), round(k[2],1), round(k[3],1), v) for k, v in ch.items()), key=lambda t: -t[4])[:10])
    print('     void clusters (0.1 m):', sorted(((k[0], round(k[1],1), round(k[2],1), round(k[3],1), v) for k, v in cv.items()), key=lambda t: -t[4])[:8])
    for v in Vd[:4]:
        print("     void", v)
    res_out[name] = dict(rays=n, leaks=L[:200], voids=Vd[:200])


MODE = a[2] if len(a) > 2 else "all"
import os
IMG = os.path.join(os.path.dirname(os.path.abspath(a[1])), 'probe_img'); os.makedirs(IMG, exist_ok=True)
C = Vector((CX, 0.0, 3.5))
if MODE in ("all", "ring"):
    for r, z, lens in ((7.0, 1.7, 24), (12.0, 1.7, 30), (8.0, 6.0, 24), (14.0, 6.0, 30)):
        for k in range(16):
            ang = 2 * math.pi * k / 16
            # an ellipse round the rectangle so the near distance stays ~r from the wall
            loc = (CX + (7.0 + r) * math.cos(ang), (3.5 + r) * math.sin(ang), z)
            run(f"ring_r{r:.0f}_z{z:.0f}_{k:02d}", loc, (CX, 0.0, 3.6 if z < 3 else 3.0), lens, (400, 225))
if MODE in ("all", "close"):
    J = [  # (name, cam, target, lens) close-ups of every junction (ground / 6 m / director views)
        ("W_leaf_post_d39", (CX + 0.4, FW - 1.5, 0.45), (CX - 1.80, FW + 0.05, 0.10), 40),
        ("E_leaf_post_d40", (CX - 0.4, FW - 1.5, 0.45), (CX + 1.80, FW + 0.05, 0.10), 40),
        ("W_leaf_post_eye", (CX + 1.2, FW - 2.5, 1.7), (CX - 1.75, FW + 0.2, 0.8), 50),
        ("E_leaf_post_eye", (CX - 1.2, FW - 2.5, 1.7), (CX + 1.85, FW + 0.2, 0.8), 50),
        ("W_post_pad_plinth", (CX - 3.0, FW - 2.0, 0.8), (CX - 1.95, FW, 0.15), 50),
        ("E_post_pad_plinth", (CX + 3.0, FW - 2.0, 0.8), (CX + 1.95, FW, 0.15), 50),
        ("W_post_head", (CX - 3.6, FW - 3.6, 2.3), (CX - 2.2, FW, 3.75), 55),
        ("E_post_head", (CX + 3.6, FW - 3.6, 2.3), (CX + 2.2, FW, 3.75), 55),
        ("W_post_head_close", (CX - 1.0, FW - 2.4, 2.7), (CX - 2.15, FW, 3.6), 45),
        ("E_post_head_close", (CX + 1.0, FW - 2.4, 2.7), (CX + 2.15, FW, 3.6), 45),
        ("W_post_head_eye", (CX - 0.7, FW - 3.0, 1.7), (CX - 2.2, FW, 3.65), 50),
        ("E_post_head_eye", (CX + 0.7, FW - 3.0, 1.7), (CX + 2.2, FW, 3.65), 50),
        ("W_post_head_eye_far", (CX - 3.0, FW - 6.0, 1.7), (CX - 2.2, FW, 3.65), 50),
        ("E_post_head_eye_far", (CX + 3.0, FW - 6.0, 1.7), (CX + 2.2, FW, 3.65), 50),
        ("W_post_head_6m", (CX - 3.0, FW - 6.0, 6.0), (CX - 2.2, FW, 3.65), 60),
        ("E_post_head_6m", (CX + 3.0, FW - 6.0, 6.0), (CX + 2.2, FW, 3.65), 60),
        ("E_post_head_eye_6m_out", (CX + 2.2 - 3.0, FW - 6.0, 1.7), (CX + 2.2, FW, 3.65), 70),
        ("W_post_head_eye_6m_out", (CX - 2.2 + 3.0, FW - 6.0, 1.7), (CX - 2.2, FW, 3.65), 70),
        ("E_post_head_eye_4m_out", (CX + 2.2, FW - 3.5, 1.7), (CX + 2.2, FW, 3.65), 60),
        ("E_plinth_gable",(GE + 2.5, 0.5, 1.2), (GE, -0.1, 0.25), 40),
        ("arch_crown",(CX + 0.3, FW - 4.5, 2.0), (CX, FW, 3.55), 60),
        ("arch_springing_W", (CX + 1.0, FW - 2.0, 1.2), (CX - 1.8, FW, 1.95), 50),
        ("arch_springing_E", (CX - 1.0, FW - 2.0, 1.2), (CX + 1.8, FW, 1.95), 50),
        ("eyelid_fade_E", (CX + 6.5, FW - 3.2, 2.0), (CX + 4.6, FW, 3.4), 35),
        ("eyelid_fade_W", (CX - 6.5, FW - 3.2, 2.0), (CX - 4.6, FW, 3.4), 35),
        ("eyelid_6m", (CX + 2.0, FW - 6.0, 6.0), (CX, FW, 3.8), 35),
        ("W_apex_ground", (GW - 5.0, 0.0, 1.7), (GW, 0.0, 7.6), 70),
        ("E_apex_ground", (GE + 5.0, 0.0, 1.7), (GE, 0.0, 7.6), 70),
        ("W_apex_ground_obl", (GW - 4.0, -4.0, 1.7), (GW, 0.0, 7.6), 70),
        ("E_apex_ground_obl", (GE + 4.0, 4.0, 1.7), (GE, 0.0, 7.6), 70),
        ("W_apex_6m", (GW - 6.0, -2.0, 6.0), (GW, 0.0, 7.5), 70),
        ("E_apex_6m", (GE + 6.0, 2.0, 6.0), (GE, 0.0, 7.5), 70),
        ("W_apex_ridge_side_d42", (GW - 0.3, -4.0, 7.7), (GW, 0.0, 7.3), 55),
        ("E_apex_ridge_side", (GE + 0.3, 4.0, 7.7), (GE, 0.0, 7.3), 55),
        ("W_apex_above_b08", (GW - 2.6, -2.2, 8.6), (GW, 0.0, 7.3), 50),
        ("E_apex_above_d41", (GE + 2.6, 2.2, 8.6), (GE, 0.0, 7.3), 50),
        ("SW_corner", (GW - 1.4, FW - 1.6, 1.7), (GW - 0.2, FW - 0.25, 2.95), 40),
        ("SE_corner", (GE + 1.4, FW - 1.6, 1.7), (GE + 0.2, FW - 0.25, 2.95), 40),
        ("NW_corner", (GW - 1.4, BW + 1.6, 1.7), (GW - 0.2, BW + 0.25, 2.95), 40),
        ("NE_corner", (GE + 1.4, BW + 1.6, 1.7), (GE + 0.2, BW + 0.25, 2.95), 40),
        ("loft_hoist", (GW - 4.0, -1.5, 3.0), (GW, 0.0, 3.6), 45),
        ("loft_hoist_6m", (GW - 5.0, 1.5, 6.0), (GW, 0.0, 4.5), 40),
        ("man_door_E", (GE + 3.0, -2.5, 1.6), (GE, -1.3, 1.2), 40),
        ("back_eye", (CX + 2.0, BW + 8.0, 1.7), (CX, BW, 2.4), 28),
        ("ridge_6m_front", (CX, FW - 9.0, 6.0), (CX, 0.0, 7.0), 30),
    ]
    ONLY = a[3:] if len(a) > 3 else []
    for nm, loc, tgt, lens in J:
        if ONLY and nm not in ONLY:
            continue
        run(nm, loc, tgt, lens, (640, 360))
json.dump(res_out, open(a[1], "w"))
print("DONE")

