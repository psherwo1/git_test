"""which mesh is hit along a camera ray: python -I who_at.py -- <blend> cx cy cz tx ty tz [u v ...]  (u, v in 0..1 frame
fractions, lens 32, 16:9) -- prints object, hit point."""
import sys

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
loc = Vector(tuple(map(float, a[1:4])))
tgt = Vector(tuple(map(float, a[4:7])))
lens = 32.0
uv = list(map(float, a[7:]))
dg = bpy.context.evaluated_depsgraph_get()
fwd = (tgt - loc).normalized()
right = fwd.cross(Vector((0, 0, 1))).normalized()
up = right.cross(fwd)
sw = 36.0 / lens
for i in range(0, len(uv), 2):
    u, v = uv[i], uv[i + 1]
    d = (fwd + right * ((u - 0.5) * sw) + up * ((0.5 - v) * sw * 9 / 16)).normalized()
    hit, p, n, idx, ob, M = bpy.context.scene.ray_cast(dg, loc, d)
    print("HIT", u, v, ob.name if ob else None, tuple(round(c, 3) for c in p) if hit else None)
