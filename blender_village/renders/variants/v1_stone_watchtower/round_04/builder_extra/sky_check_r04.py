"""scratch: level see-through test of the crown-to-drum junction + bboxes.
python sky_check.py <blend>: horizontal rays from -Y and from +X at z 8.72..9.18 (cornice cap to deck), plan offset
|s| < 2.3 m (inside the drum silhouette); a ray that hits nothing = a sky pixel."""
import sys

import bpy
import numpy as np
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get()
scn = bpy.context.scene
for name, org, d in (("from -Y", lambda s, z: Vector((s, -30.0, z)), Vector((0, 1, 0))),
                     ("from +X", lambda s, z: Vector((30.0, s, z)), Vector((-1, 0, 0))),
                     ("from az45", lambda s, z: Vector((s * 0.7071 + 21.2, -s * 0.7071 - 21.2, z)) * 1.0,
                      Vector((-0.7071, 0.7071, 0)))):
    miss, tot, worst = 0, 0, []
    for z in np.arange(8.72, 9.185, 0.01):
        for s in np.arange(-2.3, 2.301, 0.01):
            hit, loc, nrm, idx, ob, mat = scn.ray_cast(dg, org(float(s), float(z)), d, distance=80.0)
            tot += 1
            if not hit:
                miss += 1
                if len(worst) < 6:
                    worst.append((round(float(s), 2), round(float(z), 3)))
    print("SKY %-9s %d of %d rays see sky %s" % (name, miss, tot, worst))
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type == "MESH" and o.name.startswith("WATCH_cabin"):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print("BBOX %-26s z %.3f..%.3f  x %.3f..%.3f  polys %d" % (o.name, min(v.z for v in bb), max(v.z for v in bb),
                                                                   min(v.x for v in bb), max(v.x for v in bb),
                                                                   len(o.data.polygons)))
