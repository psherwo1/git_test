"""Director probe 2: horizontal rays into the boat door (water gable, +Y face at y = 1.77) at several heights, and
into the land door / plate; reports the first object hit and its y.  python -I dir_probe2_r01.py <blend>"""
import sys
import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
dg = bpy.context.evaluated_depsgraph_get()
scn = bpy.context.scene


def ray(o, d):
    hit, loc, nrm, idx, ob, _ = scn.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=20)
    return (ob.name, tuple(round(v, 3) for v in loc)) if hit else None


print("BOAT DOOR (x = -0.6, ray -Y from the deck)")
for z in (2.3, 2.6, 2.8, 2.84, 2.9, 2.95, 3.0, 3.1, 3.2, 3.3, 3.4):
    print("  z %.2f" % z, ray((-0.6, 4.0, z), (0, -1, 0)))
print("BOAT DOOR (x = -1.75: under the head-beam bearing past the jamb)")
for z in (2.9, 3.0, 3.1, 3.2, 3.3):
    print("  z %.2f" % z, ray((-1.75, 4.0, z), (0, -1, 0)))
print("LAND DOOR (x = 0.2, ray +Y from the quay)")
for z in (2.4, 2.55, 2.6, 2.65, 2.8, 2.9, 3.0):
    print("  z %.2f" % z, ray((0.2, -10.0, z), (0, 1, 0)))
print("SHUTTER STRAPS east window y=-1.13 (ray -X)")
for y in (-1.6, -1.5, -1.45, -1.4, -0.9, -0.8, -0.75, -0.7):
    for z in (1.73, 2.13, 2.2):
        r = ray((5.0, y, z), (-1, 0, 0))
        print("  y %.2f z %.2f" % (y, z), r)
