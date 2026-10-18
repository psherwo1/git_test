"""v7_cottage builder close-ups, round 1 (adapted from v5's dir_render_r08.py): one close-up set per add-on, each with
a `red` see-through twin (black override, red world, no ground / figure / sun).
python -I b_render_r01.py <blend> <out_dir> <shift_x> <shift_y> [only_prefix ...]
Cameras are written in PLAN coordinates (the recipe's, before recentre) and moved by the shift."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[1:]
blend, out, sx, sy = argv[0], argv[1], float(argv[2]), float(argv[3])
only = argv[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_B_clay", (0.42, 0.41, 0.39))
black = mat("_B_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.01))
ground = bpy.context.object
ground.scale = (200, 200, 1)
aux.append(ground)
for (x, y) in ((-3.0, -4.3), (6.6, -2.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x + sx, y + sy, 0.775))
    aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x + sx, y + sy, 1.67))
    aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_B_world")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
scn.world = world
scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    if any(d.use for d in prefs.devices):
        scn.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02

# plan coordinates: main x -5..5, y -2.75..2.75 (ridge y 0); wing x -0.9..3.9, y -8..-2.75 (ridge x 1.5);
# dormer x -3.0 front y -2.4, sill ~3.9, eave ~4.7; chimney (5.3, 0), head 7.6
SHOTS = {
    "v01_valley_W_from_SW_high": ((-6.0, -9.5, 8.0), (-0.6, -2.6, 4.2), 40, True),
    "v02_valley_E_from_SE_high": ((9.5, -9.0, 8.0), (3.7, -2.6, 4.2), 40, True),
    "v03_valley_W_corner_eye": ((-3.6, -6.4, 1.7), (-0.9, -2.9, 2.9), 34, True),
    "v04_valley_E_corner_eye": ((6.8, -6.0, 1.7), (3.9, -2.9, 2.9), 34, True),
    "v05_valley_wing_ridge_top": ((1.5, -11.0, 9.5), (1.5, -1.0, 5.6), 50, True),
    "v06_valley_W_lookup_soffit": ((-2.2, -4.0, 1.6), (-1.0, -2.9, 2.6), 30, True),
    "d01_dormer_front_eye": ((-3.0, -9.0, 1.7), (-3.0, -2.4, 4.3), 45, True),
    "d02_dormer_oblique_W": ((-7.5, -6.5, 5.5), (-3.0, -2.2, 4.6), 50, True),
    "d03_dormer_oblique_E": ((0.8, -6.8, 5.5), (-3.0, -2.2, 4.6), 50, True),
    "d04_dormer_cheek_W_close": ((-5.2, -4.2, 5.0), (-3.65, -2.0, 4.4), 45, True),
    "d05_dormer_from_above": ((-3.0, -6.0, 9.0), (-3.0, -1.6, 5.2), 40, True),
    "c01_chimney_SE_eye": ((9.5, -6.5, 1.7), (5.3, 0.0, 5.0), 32, True),
    "c02_chimney_head_close": ((8.0, -3.0, 8.4), (5.3, 0.0, 7.8), 45, True),
    "c03_chimney_abutment_N": ((3.0, 4.5, 8.2), (5.0, 0.0, 6.6), 45, True),
    "c04_chimney_abutment_S": ((3.0, -4.5, 8.2), (5.0, 0.0, 6.6), 45, True),
    "c05_chimney_foot_gable": ((8.5, 2.6, 1.6), (5.3, 0.0, 1.5), 32, True),
    "h01_three_quarter_far": ((-14.0, -18.0, 6.0), (0.5, -2.5, 3.5), 32, False),
}


def shoot(name, loc, tgt, lens, red):
    cam.location = Vector((loc[0] + sx, loc[1] + sy, loc[2]))
    cam.data.lens = lens
    t = Vector((tgt[0] + sx, tgt[1] + sy, tgt[2]))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    for o in aux:
        o.hide_render = False
    sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24
    scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1)
        bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4
        scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(out, name + "_red.png")
        bpy.ops.render.render(write_still=True)


for name, (loc, tgt, lens, red) in SHOTS.items():
    if only and not any(name.startswith(p) for p in only):
        continue
    shoot(name, loc, tgt, lens, red)
    print("SHOT", name, flush=True)
