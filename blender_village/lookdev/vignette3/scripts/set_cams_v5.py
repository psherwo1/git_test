import bpy, sys, math
from mathutils import Vector
bl = sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=bl)
CFG = eval(open(sys.argv[-2]).read())
for name, (loc, tgt, lens) in CFG.items():
    c = bpy.data.objects[name]
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = lens
bpy.ops.wm.save_as_mainfile(filepath=bl)
print("CAMS SET")
