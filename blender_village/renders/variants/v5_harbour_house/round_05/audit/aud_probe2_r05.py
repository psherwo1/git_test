"""Auditor round-5: classify the eyebrow ray-probe misses (read-only).  blender -b --python aud_probe2_r05.py -- <blend>
A miss (ray from 4 m out, through a target on the x = -0.80 front plane, hitting nothing in 30 m) is a hole only if the
target lies UNDER the roof shell. For each miss: is the target under the roof (a ray straight up from the target hits a
roof part within 4 m, AND a ray straight down hits the deck / covering / eyebrow), where along the ray the miss is,
and the ray's closest approach to the roof surfaces."""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off = [], [], [], 0
for i, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", co)
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co.reshape(-1, 3)); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(tv) // 3, i))
    off += len(m.vertices); o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)


def first(o, d, L=30.0):
    h = bvh.ray_cast(o, d, L)
    return (None, None) if h[0] is None else (h, objs[OWN[h[2]]].name)


miss, under = [], []
n = 0
for yaw in (-50, -25, 0, 25, 50):
    for pitch in (-30, -10, 10, 30):
        a, b = math.radians(180 + yaw), math.radians(pitch)
        dvec = -Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
        for yy in np.arange(-2.6, -0.14, 0.04):
            for zz in np.arange(3.95, 5.05, 0.04):
                tgt = Vector((-0.80, yy, zz)); o = tgt - dvec * 4.0
                n += 1
                if bvh.ray_cast(o, dvec, 30.0)[0] is not None:
                    continue
                up, upn = first(tgt + Vector((0, 0, 1e-3)), Vector((0, 0, 1)), 4.0)
                dn, dnn = first(tgt, Vector((0, 0, -1)), 4.0)
                rec = (yaw, pitch, round(yy, 2), round(zz, 2), upn, None if up is None else round(up[3], 3), dnn,
                       None if dn is None else round(dn[3], 3))
                miss.append(rec)
                if upn is not None and upn.startswith("HARB_roof"):
                    under.append(rec)
print("rays", n, "misses", len(miss))
by = {}
for r in miss:
    by.setdefault((r[0], r[1]), 0); by[(r[0], r[1])] += 1
print("misses by (yaw, pitch):", by)
print("z range of missed targets", min(r[3] for r in miss) if miss else None, max(r[3] for r in miss) if miss else None)
print("misses whose target is UNDER a roof part (up-ray hits HARB_roof_* within 4 m):", len(under))
for r in under[:40]:
    print("   UNDER", r)
for r in miss[:15]:
    print("   sample miss (yaw, pitch, y, z, up-hit, up-dist, down-hit, down-dist)", r)
# where is the roof surface over the plane x = -0.80 (outside and inside the wave)?
for yy in (-2.6, -2.3, -2.0, -1.7, -1.37, -1.0, -0.7, -0.4, -0.14):
    h, nm = first(Vector((-0.80, yy, 9.0)), Vector((0, 0, -1)), 9.0)
    print(f"   roof top at x -0.80 y {yy:+.2f}: z {None if h is None else round(h[0].z, 3)} ({nm})")
print("DONE")
