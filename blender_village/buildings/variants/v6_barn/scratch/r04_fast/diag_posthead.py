"""r04 builder diag: horizontal +y rays through the front wall zone at the post heads.  python -I diag_posthead.py -- <blend>
Map per (x, z): '#' first hit is in front (y < -3.0) of the wall's inside; '.' = the ray passes y -3.0 unobstructed
(a see-through slot through the wall zone).  Also lists which objects are hit first around the pocket."""
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
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(m.loop_triangles), oi)); off += len(co)
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
names = [o.name for o in objs]
CX = float(a[1]) if len(a) > 1 else 0.058
for sg in (1, -1):
    print(f"=== side {'E' if sg > 0 else 'W'}  (cols x = CX + sg * 1.70 .. 2.95 step 0.025; rows z 4.40 .. 3.30)")
    hits = {}
    xs = np.arange(1.70, 2.951, 0.025)
    for z in np.arange(4.40, 3.299, -0.025):
        row = ""
        for xr in xs:
            o = Vector((CX + sg * xr, -4.2, z))
            h = bvh.ray_cast(o, Vector((0, 1, 0)), 1.2)        # to y -3.0
            if h[0] is None:
                row += "."
            else:
                nm = names[OWN[h[2]]].replace("BARN_", "")
                hits[nm] = hits.get(nm, 0) + 1
                row += {"walls_boards": "w", "walls_blocker": "k", "cart_entry_boards": "i", "cart_entry_frame": "F",
                        "cart_entry_blocker": "b", "barn_roof_deck": "R", "walls_frame": "p"}.get(nm, "o")
        print(f"z {z:5.3f} {row}")
    print("first hits:", hits)
    # down-the-depth profile at a few x: every surface the ray crosses
    for xr in (2.20, 2.30, 2.35, 2.40, 2.45, 2.50, 2.60):
        for z in (3.60, 3.70, 3.80, 3.90):
            o = Vector((CX + sg * xr, -4.2, z)); d = Vector((0, 1, 0)); seq = []; t = 0.0
            while t < 1.4:
                h = bvh.ray_cast(o + d * (t + 1e-4), d, 1.4 - t)
                if h[0] is None:
                    break
                t = (h[0] - o).length
                seq.append(f"{names[OWN[h[2]]].replace('BARN_', '')}@{h[0].y:.3f}")
            print(f"  x {xr:.2f} z {z:.2f}: " + ", ".join(seq[:6]))
print("DONE")
