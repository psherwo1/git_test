"""Read-only: list palette material -> objects for a .blend.  Usage: python.exe -I r2_mats.py <file.blend>"""
import sys
from collections import defaultdict

import bpy

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
d = defaultdict(list)
for o in bpy.context.scene.objects:
    if o.type == "MESH" and not o.hide_render:
        for m in o.data.materials:
            d[m.name if m else "-"].append(o.name)
for k, v in sorted(d.items()):
    print(f"  {k:20s} {len(v):3d} {v[:10]}")
