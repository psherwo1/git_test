"""v4 r3 probe 6: open (boundary) edges of the house wall-head skins, by house azimuth sector -- holes the cull opened.
Reports boundary edges of V4H_daub and V4H_wall_plate with z > 2.3 m, binned by 30 deg of house azimuth."""
import math
import sys

import bpy
import bmesh

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
HX, HY = -1.462, 0.214
for nm in ("V4H_daub", "V4H_wall_plate", "V4H_daub_interior", "V4H_eave_closure"):
    ob = bpy.data.objects[nm]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bins = {}
    zs = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        p = ob.matrix_world @ ((e.verts[0].co + e.verts[1].co) / 2)
        if p.z < 2.3:
            continue
        az = math.degrees(math.atan2(p.y - HY, p.x - HX))
        k = int((az + 180) // 30) * 30 - 180
        bins[k] = bins.get(k, 0) + 1
        zs.append(p.z)
    print("%-20s boundary edges above z 2.3: %d  z %s  by house-az sector %s" % (
        nm, sum(bins.values()), (round(min(zs), 2), round(max(zs), 2)) if zs else None, dict(sorted(bins.items()))))
    bm.free()
