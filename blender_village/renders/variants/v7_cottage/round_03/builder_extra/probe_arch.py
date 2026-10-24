"""round 3 probe: the x08 wedge hits on the valley roll -> nearest vertex -> (station, ring index) of the sweep."""
import sys

import bpy
import numpy as np
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
SX, SY = -0.418, 2.587
dg = bpy.context.evaluated_depsgraph_get()
scn = bpy.context.scene
ob = bpy.data.objects["COTT_wing_valley"]
V = np.empty(len(ob.data.vertices) * 3)
ob.data.vertices.foreach_get("co", V)
V = V.reshape(-1, 3)
M = np.array(ob.matrix_world)
W = V @ M[:3, :3].T + M[:3, 3]
print("verts", len(W))
loc, tgt, lens = (1.5, -5.6, 7.1), (1.5, -1.6, 5.9), 60
o = Vector((loc[0] + SX, loc[1] + SY, loc[2]))
t = Vector((tgt[0] + SX, tgt[1] + SY, tgt[2]))
q = (t - o).to_track_quat("-Z", "Y")
fx = lens / 36.0 * 1280
for px, py in [(600, 240), (680, 240), (595, 255), (690, 255)]:
    d = (q @ Vector(((px - 640) / fx, -(py - 360) / fx, -1.0))).normalized()
    hit, p, n, i, hob, _ = scn.ray_cast(dg, o, d)
    if not hit:
        print(px, py, "miss")
        continue
    k = int(np.argmin(np.linalg.norm(W - np.array(p), axis=1)))
    poly = hob.data.polygons[i] if hob == ob else None
    vs = list(poly.vertices) if poly else []
    print(px, py, hob.name, "p", tuple(round(c, 3) for c in p), "near v", k, "st", k // 12, "ring", k % 12,
          "poly verts", [(v // 12, v % 12) for v in vs])
    for v in vs:
        print("    ", v // 12, v % 12, np.round(W[v], 3))
