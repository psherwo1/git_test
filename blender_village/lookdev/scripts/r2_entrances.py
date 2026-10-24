"""Read-only: print the scene's kit_entrances JSON and door-like object names.  Usage: python.exe -I r2_entrances.py <file.blend>"""
import sys

import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
sc = bpy.context.scene
print("KIT_ENTRANCES", sc.get("kit_entrances"))
for o in sc.objects:
    n = o.name.lower()
    if any(k in n for k in ("door", "thresh", "step", "entr", "frame", "opening")):
        print("OBJ", o.name, o.type)
