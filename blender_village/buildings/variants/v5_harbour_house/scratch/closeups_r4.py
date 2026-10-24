"""scratch: round-4 clay close-ups of the slip mouth (not a deliverable).  python -I closeups_r3.py <blend> <out_dir>
Recentred coordinates (round 4): slip-mouth corners at (-0.608, 3.427) and (4.392, 3.427); land at the quay datum."""
import math
import os
import sys

import bpy
from mathutils import Vector

blend, out = sys.argv[1], sys.argv[2]
CAMS = {
    "r4_slip_mouth": ((1.9, 9.8, -0.6), (1.9, 3.0, 0.4), 24),
    "r4_corner_W": ((0.7, 5.4, -1.0), (-0.7, 3.3, -1.0), 26),
    "r4_corner_E": ((3.1, 5.4, -1.0), (4.5, 3.3, -1.0), 26),
    "r4_gable": ((1.9, 14.0, 1.6), (1.9, 3.4, 4.0), 30),
    "r4_pier_W_out": ((-1.4, 6.2, 3.1), (-1.1, 3.4, 3.4), 35),
    "r4_pier_W_in": ((0.4, 1.8, 2.4), (-1.1, 3.3, 3.4), 30),
    "r4_pier_E_out": ((5.2, 6.2, 3.1), (4.9, 3.4, 3.4), 35),
    "r4_roof_ne": ((14.0, 14.0, 6.0), (1.9, -1.0, 5.0), 30),
}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scn = bpy.context.scene
clay = bpy.data.materials.new("_clay")
clay.use_nodes = True
clay.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -2.505))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(150)))
bpy.context.object.data.energy = 3.5
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
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
for name, (loc, tgt, lens) in CAMS.items():
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scn.render.filepath = os.path.join(os.path.abspath(out), name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", name)


