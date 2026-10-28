"""v4 r4 probe 3: rays through both doorways.  Cameras in front of each door (0.8-3 m out, z 0.6-1.8), targets on a
grid over the clear opening.  Counts rays that hit nothing (sky / terrain below z 0 through the floor), rays whose
first hit is a back face (a one-sided hole in Unreal), and the objects."""
import math
import sys
from collections import Counter

import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
DOORS = {"house": (Vector((-1.462, 0.214 - 2.62, 0.0)), 0.48, 2.25), "mill": (Vector((2.82, 1.36 - 2.02, 0.0)), 0.5, 2.2)}
for name, (D, hw, ht) in DOORS.items():
    n = sky = back = 0
    objs = Counter()
    sky_z = Counter()
    for cx in (-1.2, -0.6, 0.0, 0.6, 1.2):
        for cy in (0.8, 1.5, 3.0):
            for cz in (0.6, 1.2, 1.65, 1.8):
                cam = D + Vector((cx, -cy, cz))
                for tx in range(-8, 9):
                    for tz in range(0, 19):
                        p = D + Vector((tx / 8.0 * hw * 0.95, 0.0, 0.05 + tz / 18.0 * (ht - 0.1)))
                        d = (p - cam).normalized()
                        hit, loc, nrm, idx, ob, Mx = scn.ray_cast(dg, cam, d)
                        n += 1
                        if not hit:
                            sky += 1
                            # where would it meet z = 0 (terrain)?
                            if d.z < 0:
                                t = -cam.z / d.z
                                sky_z["below floor -> terrain"] += 1
                            else:
                                sky_z["up -> sky"] += 1
                            continue
                        if nrm.dot(d) > 0:
                            back += 1
                            objs[ob.name] += 1
    print(f"DOORWAY {name}: {n} rays, escape {sky} {dict(sky_z)}, back-face first hits {back} {dict(objs.most_common(8))}")
