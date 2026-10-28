"""v4 r4 probe 4: where the mill-doorway rays that reach the sky go.  For every escaping up-ray: camera, direction,
the point where it crosses the drum axis plane / z 2.5, 4, 6 (relative to the drum centre), and the list of objects
the ray passes near (multi-hit walk ignoring nothing).  Also the V4M_interior / ceiling objects present."""
import sys
from collections import Counter

import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
M = Vector((2.82, 1.36, 0.0))
D, hw, ht = Vector((2.82, 1.36 - 2.02, 0.0)), 0.5, 2.2
print("INTERIOR OBJECTS", [(o.name, len(o.data.polygons)) for o in bpy.data.objects
                           if o.type == "MESH" and o.name.startswith("V4M_") and
                           any(k in o.name for k in ("interior", "floor", "ceiling", "blocker", "core", "door"))])
esc = []
for cx in (-1.2, -0.6, 0.0, 0.6, 1.2):
    for cy in (0.8, 1.5, 3.0):
        for cz in (0.6, 1.2, 1.65, 1.8):
            cam = D + Vector((cx, -cy, cz))
            for tx in range(-8, 9):
                for tz in range(0, 19):
                    p = D + Vector((tx / 8.0 * hw * 0.95, 0.0, 0.05 + tz / 18.0 * (ht - 0.1)))
                    d = (p - cam).normalized()
                    hit, loc, nrm, idx, ob, Mx = scn.ray_cast(dg, cam, d)
                    if hit or d.z <= 0:
                        continue
                    # walk the ray backwards from far away to see what it passes through on the way: the last surfaces
                    # near the drum
                    pts = []
                    for z in (2.3, 3.0, 4.0, 5.5):
                        t = (z - cam.z) / d.z
                        q = cam + d * t
                        pts.append((z, round((q - M).to_2d().length, 2)))
                    esc.append((tuple(round(c, 2) for c in cam - D), tuple(round(c, 2) for c in d), pts))
print("ESCAPING UP-RAYS", len(esc))
cams = Counter(e[0] for e in esc)
print("  by camera (rel. door)", cams.most_common(10))
for e in esc[:15]:
    print("  ", e)
# multi-hit walk on the first few: list every surface the ray crosses (two-sided) within 8 m
for e in esc[:6]:
    cam = D + Vector(e[0])
    d = Vector(e[1])
    o = cam.copy()
    seq = []
    for _ in range(12):
        hit, loc, nrm, idx, ob, Mx = scn.ray_cast(dg, o, d)
        if not hit:
            break
        seq.append((ob.name, round(loc.z, 2), round((loc - M).to_2d().length, 2), "back" if nrm.dot(d) > 0 else "front"))
        o = loc + d * 1e-3
    print("  WALK", e[0], seq)
