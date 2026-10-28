"""Auditor round-6 (read-only): size the r05 triangles that the r06 hidden-face cull dropped OUTSIDE the eyebrow zone
and that a ray from outside could reach in r05: area, width (2*area / longest edge), what the same ray hits in r06,
how much deeper, and whether it misses (see-through)."""
import math, sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]


def dump(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
        co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co)
        tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
        out[o.name] = (co.reshape(-1, 3), tv.reshape(-1, 3)); o.evaluated_get(dg).to_mesh_clear()
    return out


R5, R6 = dump(a[0]), dump(a[1])
names6 = list(R6.keys())


def scene_bvh(D):
    V, T, O, off = [], [], [], 0
    for i, (k, (c, t)) in enumerate(D.items()):
        V.append(c); T.append(t + off); O.append(np.full(len(t), i)); off += len(c)
    return BVHTree.FromPolygons(np.concatenate(V).tolist(), np.concatenate(T).tolist(), all_triangles=True), \
        np.concatenate(O)


B5, _ = scene_bvh(R5); B6, O6 = scene_bvh(R6)
dirs = []
for i in range(400):
    z = 1 - (i + 0.5) / 400 * 1.7
    r = math.sqrt(max(0, 1 - z * z)); phi = i * math.pi * (3 - math.sqrt(5))
    dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
worst = 0.0
for k in ("HARB_roof_covering", "HARB_tower_stones", "HARB_wing_roof_covering", "HARB_roof_comb"):
    c5, t5 = R5[k]; c6, t6 = R6[k]
    b6 = BVHTree.FromPolygons(c6.tolist(), t6.tolist(), all_triangles=True)
    cen = c5[t5].mean(1)
    zone = (np.abs(cen[:, 1] + 1.57) <= 2.1) & (cen[:, 0] < 1.6)
    cand = [i for i in np.nonzero(~zone)[0] if b6.find_nearest(Vector(cen[i]))[3] > 0.002]
    for ti in cand:
        P = c5[t5[ti]]; e = [np.linalg.norm(P[(j + 1) % 3] - P[j]) for j in range(3)]
        area = 0.5 * np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0])); wid = 2 * area / max(e)
        p = Vector(cen[ti]); rows = []
        for d in dirs:
            o = p + d * 15.0
            h5 = B5.ray_cast(o, -d, 16.0)
            if h5[0] is None or (h5[0] - p).length > 0.01:
                continue
            h6 = B6.ray_cast(o, -d, 40.0)
            if h6[0] is None:
                rows.append(("MISS", None)); continue
            dd = h6[3] - h5[3]
            if dd > 0.02:
                # where is this viewpoint? origin height and the first r06 object the incoming ray passes nearest
                rows.append((names6[O6[h6[2]]], round(dd, 3), "dir", tuple(round(v, 2) for v in d),
                             "origin z", round(o.z, 1)))
        if rows:
            worst = max(worst, wid)
            print(f"{k:24s} tri at {np.round(cen[ti], 3).tolist()} area {area*1e4:6.2f} cm2 width {wid*100:5.2f} cm "
                  f"longest edge {max(e)*100:5.1f} cm | rays deeper in r06: {len(rows)} -> {rows[:4]}", flush=True)
print(f"widest dropped-and-reachable triangle with a deeper r06 hit: {worst*100:.2f} cm")
print("DONE")

