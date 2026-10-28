"""scratch: round-5 eyebrow close-ups (not a deliverable).  python -I closeups_r5.py <blend> <out_dir> [names]
Recentred coordinates (shift -1.808, -5.973, as round 4): the eyebrow front centre is at about (-0.73, -1.37, 4.86).
Clay views as closeups_r4.py; `red` shots also render a see-through twin (black override, red world, no ground)."""
import math
import os
import sys

import bpy
from mathutils import Vector

blend, out = sys.argv[1], sys.argv[2]
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
CAMS = {
    "r5_brow_eye": ((-9.5, 0.5, 1.7), (-0.7, -1.4, 4.7), 35, True),        # eye level from the land / quay side
    "r5_brow_ref4": ((-13.0, 13.0, 8.5), (0.0, -2.0, 4.0), 30, False),    # the ref4 three-quarter (NW, over water)
    "r5_brow_graze": ((-1.9, 5.0, 4.6), (-0.6, -1.6, 5.0), 40, True),     # grazing along the west slope
    "r5_brow_close": ((-4.2, -0.2, 4.4), (-0.8, -1.4, 4.75), 40, True),   # the window, its eave and the front ends
}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_clay", (0.42, 0.41, 0.39))
black = mat("_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.045))
ground = bpy.context.object
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-120)))
sun = bpy.context.object
sun.data.energy = 3.5
w = bpy.data.worlds.new("w")
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
scn.world = w
scn.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scn.cycles.device = "GPU"
except Exception:
    pass
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.clip_start = 0.02
scn.camera = cam
os.makedirs(out, exist_ok=True)
for name, (loc, tgt, lens, red) in CAMS.items():
    if only and name not in only:
        continue
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scn.view_layers[0].material_override = clay
    ground.hide_render = sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.5
    scn.cycles.samples = 24
    scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(os.path.abspath(out), name + ".png")
    bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        ground.hide_render = sun.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1)
        bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4
        scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(os.path.abspath(out), name + "_red.png")
        bpy.ops.render.render(write_still=True)
    print("wrote", name, flush=True)
