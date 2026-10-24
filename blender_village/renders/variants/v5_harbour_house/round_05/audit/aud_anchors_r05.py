"""Auditor round-5: decal anchors near the eyebrow / buried anchors (a surface within 5 cm IN FRONT along +normal)."""
import json, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, off = [], [], 0
for o in objs:
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", co)
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co.reshape(-1, 3)); T.append(tv.reshape(-1, 3) + off); off += len(m.vertices); o.evaluated_get(dg).to_mesh_clear()
bvh = BVHTree.FromPolygons(np.concatenate(V).tolist(), np.concatenate(T).tolist(), all_triangles=True)
J = json.load(open(a[1])); E = Vector((-0.80, -1.37, 4.40))
buried = []
for an in J["anchors"]:
    p, n = Vector(an["position"]), Vector(an["normal"])
    h = bvh.ray_cast(p + n * 0.005, n, 0.05)
    if h[0] is not None:
        buried.append((an["name"], an["type"], [round(x, 2) for x in an["position"]], round(h[3], 3)))
    if (p - E).length < 2.5:
        print("NEAR EYEBROW", an["name"], an["type"], [round(x, 2) for x in an["position"]], [round(x, 2) for x in an["normal"]])
print("anchors", len(J["anchors"]), "with a surface within 5 cm in front (buried):", len(buried), buried[:10])
