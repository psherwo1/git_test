"""Independent look at what hangs over each entrance (verification helper, 4_verify; reads only).

Usage: <bpy-python> clear_probe.py <file.blend> [d0]

Rays straight up from the kit gate's 5 x 5 stations (clear width x d0 .. d0 + 0.6 m in front of the face), through
EVERY mesh (no skip list).  Prints, per entrance, the lowest down-facing hit of each object between 1.5 and 6 m, and
whether guards.DOOR_PARTS would skip that object -- so a skipped object that is really an eave is visible.
"""
import json
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

DOOR_PARTS = ("door", "threshold", "step", "surround", "openings_", "_frames", "iron", "nail", "hinge", "pintle",
              "interior", "floor", "hearth", "reveals", "blocker", "lintel", "leaf", "_backing")


def main(path, d0=0.15):
    bpy.ops.wm.open_mainfile(filepath=path)
    ents = json.loads(bpy.context.scene.get("kit_entrances") or "[]")
    dg = bpy.context.evaluated_depsgraph_get()
    V, T, own = [], [], []
    off = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        me = o.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        t = np.zeros(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get("vertices", t)
        V.append(co); T.append(t.reshape(-1, 3) + off); own += [o.name] * len(me.loop_triangles); off += len(co)
    V = np.vstack(V); T = np.vstack(T)
    bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)
    up = Vector((0, 0, 1))
    for e in ents:
        O = np.array(e["origin"], float); n = np.array(e["out"], float); n[2] = 0; n /= np.linalg.norm(n)
        tv = np.array([-n[1], n[0], 0.0])
        lowest = {}
        for u in np.linspace(-0.5, 0.5, 5) * e["width"]:
            for k in range(5):
                P = O + n * (d0 + 0.15 * k) + tv * u
                z0 = 0.6
                for _ in range(200):
                    h = bvh.ray_cast(Vector((P[0], P[1], z0)), up, 8.0)
                    if h[0] is None:
                        break
                    z = h[0][2]
                    ob = own[h[2]]
                    if h[1][2] < 0 and 1.5 <= z <= 6.0:
                        if ob not in lowest or z < lowest[ob][0]:
                            lowest[ob] = (round(z, 3), (round(float(P[0]), 2), round(float(P[1]), 2)))
                    z0 = z + 1e-4
        print(f"ENTRANCE {e['name']} head {e['head']}  (d0 {d0})")
        for ob, (z, at) in sorted(lowest.items(), key=lambda kv: kv[1][0])[:12]:
            sk = any(s in ob for s in DOOR_PARTS)
            print(f"    {z:7.3f}  {ob:40s} {'SKIPPED by DOOR_PARTS' if sk else ''}  at {at}")


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(a[0], float(a[1]) if len(a) > 1 else 0.15)
