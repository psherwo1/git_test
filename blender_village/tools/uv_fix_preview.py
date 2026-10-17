"""Preview the kit 1.10.0 UV pass on an already-built .blend (UV only; no rebuild, geometry untouched).

Usage:  <python-with-bpy> blender_village/tools/uv_fix_preview.py <in.blend> <out.blend>
Runs village_kit.uvgrain.finish_uvs on every rendered mesh and saves a copy (never the input).  For iterating on
the UV writer in seconds; the real result is always a rebuild (the pass runs inside build_building /
build_compound, together with the walked-top Mask rule, which needs the frame's entrances).
"""
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kit"))
from village_kit import uvgrain  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
src, dst = os.path.abspath(args[0]), os.path.abspath(args[1])
assert src != dst, "never overwrite the input"
bpy.ops.wm.open_mainfile(filepath=src)
t0 = time.time()
uvgrain.finish_uvs([o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render], log=print)
print(f"uv pass {time.time() - t0:.1f} s")
os.makedirs(os.path.dirname(dst), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True, copy=True)
