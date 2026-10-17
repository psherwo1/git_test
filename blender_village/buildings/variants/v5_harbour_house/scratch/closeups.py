"""scratch: clay close-ups of the junctions (not a deliverable tool).  python -I closeups.py <blend> <out_dir> [shift_y]"""
import math
import os
import sys

import bpy
from mathutils import Vector

blend, out = sys.argv[1], sys.argv[2]
sy = float(sys.argv[3]) if len(sys.argv) > 3 else -2.73
CAMS = {
    "jetty_corner": ((4.2, -6.8, 1.4), (2.6, -4.8, 3.1), 30),
    "eave_verge": ((4.6, -8.0, 4.4), (2.6, -5.2, 5.9), 35),
    "boat_deck": ((3.8, 8.0, 1.6), (0.6, 4.6, 1.3), 30),
    "apex": ((3.5, -9.5, 8.0), (0.0, -5.3, 9.3), 50),
    "door": ((1.6, -8.2, 1.65), (0.0, -4.6, 1.4), 30),
    "under_deck": ((4.5, 10.5, -0.6), (0.0, 6.0, 0.1), 28),
    "west_eave": ((-5.5, -1.0, 2.0), (-2.8, 0.5, 5.2), 30),
    "quay_corner": ((5.0, -8.5, 1.2), (3.2, -5.8, 0.2), 30),
}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scn = bpy.context.scene
clay = bpy.data.materials.new("_clay")
clay.use_nodes = True
clay.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -2.505))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
bpy.context.object.data.energy = 3.5
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
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
scn.cycles.samples = 16
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 960, 540
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
os.makedirs(out, exist_ok=True)
only = sys.argv[4].split(",") if len(sys.argv) > 4 else list(CAMS)
for name in only:
    loc, tgt, lens = CAMS[name]
    cam.location = Vector((loc[0], loc[1] + sy, loc[2]))
    t = Vector((tgt[0], tgt[1] + sy, tgt[2]))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scn.render.filepath = os.path.join(os.path.abspath(out), name + ".png")
    bpy.ops.render.render(write_still=True)
