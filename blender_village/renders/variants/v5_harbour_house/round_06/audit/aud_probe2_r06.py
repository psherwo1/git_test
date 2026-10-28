"""Auditor round-6: classify the eyebrow ray-probe misses whose target has something overhead (read-only)."""
import math, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
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
FX, blo, bhi = -1.239, (-1.239, -3.175, 3.676), (-0.539, 0.035, 4.981)
up, dn = Vector((0, 0, 1)), Vector((0, 0, -1))
cls = {}
ex = []
for yaw in (-60, -35, -15, 0, 15, 35, 60):
    for pitch in (-35, -15, 0, 15, 30):
        a, b = math.radians(180 + yaw), math.radians(pitch)
        dvec = -Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
        for yy in np.arange(blo[1] - 0.25, bhi[1] + 0.25, 0.04):
            for zz in np.arange(blo[2] - 0.1, bhi[2] + 0.45, 0.04):
                tgt = Vector((FX + 0.02, yy, zz))
                if bvh.ray_cast(tgt - dvec * 4.0, dvec, 30.0)[0] is not None:
                    continue
                hu = bvh.ray_cast(tgt, up, 30.0)
                if hu[0] is None:
                    continue
                hd = bvh.ray_cast(tgt, dn, 30.0)
                # is the target inside closed geometry / under the roof? count crossings straight up
                k = (objs[OWN[hu[2]]].name, round(hu[0].z - zz, 1))
                cls[k] = cls.get(k, 0) + 1
                if len(ex) < 8:
                    ex.append((yaw, pitch, round(float(yy), 2), round(float(zz), 2), objs[OWN[hu[2]]].name,
                               tuple(round(c, 2) for c in hu[0]),
                               None if hd[0] is None else (objs[OWN[hd[2]]].name, round(zz - hd[0].z, 2))))
print("misses with something overhead, grouped (object overhead, height above target):", cls)
for e in ex:
    print("  ", e)
# the miss rays: closest approach of the ray to any geometry (is it threading a gap, or passing in open air?)
for (yaw, pitch, yy, zz, *_ ) in ex[:4]:
    a, b = math.radians(180 + yaw), math.radians(pitch)
    dvec = -Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
    tgt = Vector((FX + 0.02, yy, zz)); dmin = 99; at = None
    for s in np.arange(-4.0, 8.0, 0.02):
        p = tgt + dvec * s
        d = bvh.find_nearest(p)[3]
        if d < dmin:
            dmin, at = d, tuple(round(c, 2) for c in p)
    print(f"   ray yaw {yaw} pitch {pitch} target ({yy},{zz}): nearest geometry along the ray {dmin:.3f} m at {at}")
print("DONE")
