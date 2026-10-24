"""Auditor v6_barn round 4 (read-only): size the residual leak rays of the post-head _6m / _eye_far shots
(aud_seethru_r04.py close; they enter inside the arch, x ~ cart_x +-0.15, z 2.4-2.9) -- where is the pinch and how wide.
blender -b -P aud_slit_size_r04.py -- <v6_barn.blend> <aud_seethru_close.json>"""
import json
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
CX, FW = 0.058, -3.499
CAMS = {"W_post_head_eye_far": (CX - 3.0, FW - 6.0, 1.7), "E_post_head_eye_far": (CX + 3.0, FW - 6.0, 1.7),
        "W_post_head_6m": (CX - 3.0, FW - 6.0, 6.0), "E_post_head_6m": (CX + 3.0, FW - 6.0, 6.0)}
J = json.load(open(a[1]))
allap = []
for nm, cam in CAMS.items():
    cam = Vector(cam)
    aps, pins = [], []
    for L in J[nm]["leaks"]:
        ent = Vector(L[3]); d = (ent - cam).normalized()
        t0, t1 = (FW - 0.12 - cam.y) / d.y, (FW + 0.55 - cam.y) / d.y
        best = (9.0, None, None)
        for t in np.linspace(t0, t1, 200):
            p = cam + d * t
            h = bvh.find_nearest(p)
            if h[3] < best[0]:
                best = (h[3], p, names[OWN[h[2]]])
        aps.append(2 * best[0]); pins.append((best[1], best[2]))
    aps = np.array(aps); allap += list(aps)
    C = np.array([list(p) for p, _ in pins])
    who = {}
    for p, w in pins:
        who[w] = who.get(w, 0) + 1
    print(f"{nm}: leak rays {len(aps)}; aperture median {np.median(aps)*1000:.1f} mm, max {aps.max()*1000:.1f} mm; "
          f"pinch bbox x {C[:,0].min():.3f}..{C[:,0].max():.3f} y {C[:,1].min():.3f}..{C[:,1].max():.3f} "
          f"z {C[:,2].min():.3f}..{C[:,2].max():.3f}; nearest at pinch {who}")
    i = int(np.argmax(aps)); p = Vector(C[i]); near = set()
    for dv in [Vector(x) for x in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0))]:
        hh = bvh.ray_cast(p, dv, 0.3)
        if hh[0] is not None:
            near.add((names[OWN[hh[2]]], tuple(round(c, 2) for c in dv), round(hh[3], 3)))
    print("   widest pinch at", [round(c, 3) for c in p], "bounded by", sorted(near))
print(f"ALL: {len(allap)} rays, aperture max {max(allap)*1000:.1f} mm")
print("DONE")
