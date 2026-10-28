"""r04 builder diag 2: at the post heads, the deck underside (soffit) z at several wall-zone planes vs the top z of each
wall-zone object (per-object BVH, ray down).  python -I diag2_posthead.py -- <blend> <CX>"""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
CX = float(a[1])
dg = bpy.context.evaluated_depsgraph_get()
B = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    k = o.name.replace("BARN_", "")
    if k not in ("barn_roof_deck", "walls_boards", "walls_blocker", "cart_entry_boards", "cart_entry_blocker",
                 "cart_entry_frame", "walls_frame"):
        continue
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    mw = o.matrix_world
    V = [tuple(mw @ v.co) for v in m.vertices]
    B[k] = BVHTree.FromPolygons(V, [tuple(t.vertices) for t in m.loop_triangles], all_triangles=True)
    print(k, len(m.loop_triangles))


def top(bv, x, y, zhi=5.5, zlo=2.5):
    h = bv.ray_cast(Vector((x, y, zhi)), Vector((0, 0, -1)), zhi - zlo)
    return h[0].z if h[0] is not None else None


def under(bv, x, y, zlo=2.0):
    h = bv.ray_cast(Vector((x, y, zlo)), Vector((0, 0, 1)), 6.0)
    return h[0].z if h[0] is not None else None


f = lambda v: "  -  " if v is None else f"{v:5.2f}"
YS = (-3.53, -3.515, -3.45, -3.41, -3.39, -3.355, -3.30, -3.20)
for sg in (1, -1):
    print(f"=== {'E' if sg > 0 else 'W'}: x_rel | deck underside at y {YS} | tops (max over y in plane band):"
          f" wall boards, wall blocker, entry boards, entry blocker, frame, wall frame")
    for xr in np.arange(1.80, 2.81, 0.05):
        x = CX + sg * xr
        du = [under(B["barn_roof_deck"], x, y) for y in YS]
        tops = []
        for k, band in (("walls_boards", (-3.56, -3.42)), ("walls_blocker", (-3.40, -3.34)),
                        ("cart_entry_boards", (-3.43, -3.37)), ("cart_entry_blocker", (-3.38, -3.32)),
                        ("cart_entry_frame", (-3.53, -3.22)), ("walls_frame", (-3.53, -3.30))):
            vs = [top(B[k], x, y) for y in np.linspace(band[0], band[1], 15)]
            vs = [v for v in vs if v is not None]
            tops.append(max(vs) if vs else None)
        print(f"{xr:4.2f} | " + " ".join(f(v) for v in du) + " | " + " ".join(f(v) for v in tops))
print("DONE")
