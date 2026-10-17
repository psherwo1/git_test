"""v4 r3 probe 5: holes at the house wall head.  From eye-level cameras (z 1.65) round the house at 4.0 and 6.0 m
from its centre, rays are aimed at the wall-head band (house r 2.40-2.75, z 2.45-2.95) under the eave.  A ray whose
first hit is a BACK face (normal away from the camera) is looking through a hole in a culled skin.  Reported per
camera azimuth (house azimuth, 0 = +X, -90 = the door side -Y), and the objects whose back faces are hit."""
import math
import sys

import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
H = Vector((-1.462, 0.214, 0.0))
M = Vector((2.82, 1.36, 0.0))
tot_all = back_all = 0
for R in (4.0, 6.0):
    for az in range(-180, 180, 15):
        a = math.radians(az)
        cam = H + Vector((math.cos(a) * R, math.sin(a) * R, 1.65))
        if (cam - M).to_2d().length < 2.4:
            continue
        n = b = 0
        objs = {}
        for da in range(-24, 25, 2):
            for zi in range(0, 11):
                aa = a + math.radians(da)
                for rr in (2.45, 2.60, 2.75):
                    p = H + Vector((math.cos(aa) * rr, math.sin(aa) * rr, 2.45 + 0.05 * zi))
                    d = (p - cam).normalized()
                    hit, loc, nrm, idx, ob, Mx = scn.ray_cast(dg, cam, d)
                    if not hit or not ob.name.startswith("V4"):
                        continue
                    n += 1
                    if nrm.dot(d) > 0 and ob.name in ("V4H_daub_interior", "V4H_wall_plate", "V4H_daub",
                                                       "V4H_eave_closure", "V4H_roof_blocker"):
                        b += 1
                        objs[ob.name] = objs.get(ob.name, 0) + 1
        tot_all += n
        back_all += b
        print("R %.1f az %4d: %4d / %4d rays see a back face  %s" % (R, az, b, n, objs))
print("TOTAL back-face hits %d of %d" % (back_all, tot_all))
