"""Auditor round-5: identify the 6 new single red pixels in g01 (r05 vs r04) by ray-casting the ring camera (read-only)."""
import math, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
blend = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
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
W, H = 2560, 1440
scn.render.resolution_x, scn.render.resolution_y, scn.render.resolution_percentage = W, H, 100
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.data.lens = 24.0; cam.data.clip_start = 0.02
C = Vector((0.6, -1.5, 0.0)); a = math.radians(22.5 * 1 + 5.0)
cam.location = Vector((C.x + 13.0 * math.cos(a), C.y + 13.0 * math.sin(a), 1.7))
cam.rotation_euler = (Vector((C.x, C.y, 3.2)) - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
fr = cam.data.view_frame(scene=scn); tr, br, bl, tl = fr[0], fr[1], fr[2], fr[3]; R = cam.matrix_world.to_3x3()
def ray(u, v):
    d = tl + (tr - tl) * ((u + 0.5) / W) + (bl - tl) * ((v + 0.5) / H)
    return (R @ d).normalized()
for (u, v) in ((2035, 266), (2035, 270), (2042, 351), (2044, 373), (2052, 459), (2054, 488)):
    res = []
    for du, dv in ((0, 0), (-2, 0), (2, 0), (0, -2), (0, 2)):
        h = bvh.ray_cast(cam.location, ray(u + du, v + dv), 200.0)
        res.append("miss" if h[0] is None else f"{objs[OWN[h[2]]].name}@({h[0].x:.2f},{h[0].y:.2f},{h[0].z:.2f}) d{h[3]:.1f}")
    print("PIX", (u, v), " | ".join(res))
print("px size at 12 m:", round((tr.x - tl.x) / abs(tl.z) / W * 12 * 100, 2), "cm")
