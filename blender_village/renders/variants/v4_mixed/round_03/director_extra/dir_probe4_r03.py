"""v4 r3 probe 4: what the black blocks under the west house eave (a07) are.  Casts camera rays through a pixel grid
of the a07 framing and reports, per pixel, the first object hit and whether the hit face is a BACK face (normal
pointing away from the camera) -- a back face seen from outside means a hole in a closed piece."""
import math
import sys

import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
cam_loc = Vector((-5.6, -0.8, 1.7))
tgt = Vector((-3.9, 0.2, 2.75))
lens, sensor = 30.0, 36.0
W, Hh = 1280, 720
q = (tgt - cam_loc).to_track_quat("-Z", "Y")
fwd = q @ Vector((0, 0, -1))
right = q @ Vector((1, 0, 0))
up = q @ Vector((0, 1, 0))
f = lens / sensor * W
stats = {}
first_back = {}
for py in range(250, 600, 10):
    for px in range(200, 1280, 10):
        d = (fwd * f + right * (px - W / 2) + up * (Hh / 2 - py)).normalized()
        hit, loc, nrm, idx, ob, M = scn.ray_cast(dg, cam_loc, d)
        if not hit:
            continue
        back = nrm.dot(d) > 0
        k = (ob.name, back)
        stats[k] = stats.get(k, 0) + 1
        if back and ob.name not in first_back:
            first_back[ob.name] = (px, py, tuple(round(x, 3) for x in loc))
for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
    print("HIT %-28s back=%s  %d" % (k[0], k[1], v))
for k, v in first_back.items():
    print("BACK example", k, v)
