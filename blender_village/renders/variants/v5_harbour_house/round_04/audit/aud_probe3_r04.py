"""Auditor round-4 probe 3 (read-only): characterise the slip-wall foot slot over the quay coping.
python -I aud_probe3_r04.py <blend>"""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
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
nm = lambda h: objs[OWN[h[2]]].name  # noqa: E731

# coping top under the slip walls
for x in (-0.55, -0.40, 4.33, 4.20, 1.9):
    h = bvh.ray_cast(Vector((x, 1.5, 0.5)), Vector((0, 0, -1)), 3.0)
    print("down-ray at x", x, "y 1.5 ->", None if h[0] is None else (round(h[0].z, 3), nm(h)))
for side, face, dx in (("W", -0.608, -1.0), ("E", 4.392, 1.0)):
    ys = np.arange(0.30, 3.42, 0.005); zs = np.arange(-0.039, 0.10, 0.002)
    deep = np.zeros((len(zs), len(ys)), bool); thru = np.zeros_like(deep)
    for j, y in enumerate(ys):
        for i, z in enumerate(zs):
            h = bvh.ray_cast(Vector((1.9, y, z)), Vector((dx, 0, 0)), 10.0)
            d = 99.0 if h[0] is None else abs(h[0].x - face)
            deep[i, j] = d > 0.10
            thru[i, j] = h[0] is None or abs(h[0].x - face) > 0.95
    zrow = deep.mean(1)
    print(f"SLOT {side}: share of y positions with a ray > 10 cm deep, by z:")
    print("   ", " ".join(f"{z:+.3f}:{s:.2f}" for z, s in zip(zs[::3], zrow[::3])))
    # contiguous openings in y at each z, and the tallest open column (slot height)
    col_h = deep.sum(0) * 0.002
    print(f"   tallest open column {col_h.max()*100:.1f} cm; columns with >= 2 cm open height: "
          f"{int((col_h >= 0.02).sum())} of {len(ys)} ({(col_h >= 0.02).mean()*100:.0f}% of the wall length)")
    print(f"   rays reaching > 0.95 m past the face (through the 1 m of masonry): {int(thru.sum())}; "
          f"max z of those {zs[np.nonzero(thru.any(1))[0].max()] if thru.any() else None}")
    # highest z with any deep ray
    if deep.any():
        print("   highest z with a > 10 cm deep ray:", round(float(zs[np.nonzero(deep.any(1))[0].max()]), 3))
print("DONE")
