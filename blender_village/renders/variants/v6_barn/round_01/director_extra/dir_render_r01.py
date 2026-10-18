"""Director round-1 close-ups for v6_barn (adapted from bld_render_r01.py / v5 dir_render_r08.py: clay, sun, 1.8 m
figures; `red` twins = black override + red world, no ground / figures: see-through check).  Coordinates after the
build's recentre: kiln axis (0.058, -3.401), front wall y -1.951, back wall y 5.049, gables x -6.942 / 7.058, ridge
line y 1.549, cart doors x -4.442.
blender -b --python dir_render_r01.py -- <blend> <out_dir> [only_prefix ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], argv[1]
only = argv[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_D_clay", (0.42, 0.41, 0.39))
black = mat("_D_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.002)); gr = bpy.context.object
gr.scale = (300, 300, 1); aux.append(gr)
for (x, y) in ((-4.0, -4.2), (2.6, -6.6), (-9.0, 1.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x, y, 0.775)); aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x, y, 1.67)); aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38))); sun = bpy.context.object
sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_D_world"); world.use_nodes = True
bg = world.node_tree.nodes["Background"]; scn.world = world
scn.render.engine = "CYCLES"; scn.cycles.device = "CPU"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    if any(d.use for d in prefs.devices):
        scn.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device)
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

KX, KY = 0.058, -3.401
SHOTS = {
    # junctions the builder did not probe (or mis-aimed: s14)
    "d02_kiln_back_thatch_W_from_ridge": ((KX - 3.5, KY + 5.8, 9.2), (KX - 1.0, KY + 1.9, 4.7), 40, True),
    "d03_kiln_back_thatch_E_from_ridge": ((KX + 3.5, KY + 5.8, 9.2), (KX + 1.0, KY + 1.9, 4.7), 40, True),
    "d04_cone_eave_E_fin": ((KX + 4.5, KY - 4.0, 6.5), (KX + 2.1, KY + 1.2, 5.0), 45, True),
    "d05_eave_lip_into_kiln_W_low": ((KX - 4.0, -6.0, 2.0), (KX - 1.1, -2.5, 2.9), 38, True),
    "d06_eave_lip_into_kiln_E_low": ((KX + 4.0, -6.0, 2.0), (KX + 1.1, -2.5, 2.9), 38, True),
    "d07_hoist_side_on_from_S": ((-7.6, -9.0, 6.3), (-7.6, 1.55, 6.2), 60, False),
    "d08_hoist_from_below_W": ((-11.5, 0.6, 1.7), (-7.6, 1.55, 5.8), 35, False),
    "d09_SW_corner_eave_verge_lift": ((-10.0, -4.8, 2.4), (-6.94, -1.95, 2.9), 40, True),
    "d10_ridge_skyline_E_half": ((4.5, -16.0, 7.4), (4.5, 1.55, 7.1), 85, True),
    "d11_kiln_door_eye": ((KX + 1.2, KY - 5.2, 1.65), (KX, KY - 2.25, 1.3), 35, False),
    "d12_loft_door_eye_W": ((-12.5, -1.5, 1.7), (-6.94, 1.55, 3.6), 30, False),
    # massing / thumbnails
    "d13_thumb_SW_45m": ((-30.0, -36.0, 14.0), (0.0, 0.0, 4.0), 50, False),
    "d14_thumb_SE_45m": ((32.0, -34.0, 14.0), (0.0, 0.0, 4.0), 50, False),
    "d15_thumb_NE_back_45m": ((30.0, 34.0, 13.0), (0.0, 0.0, 4.0), 50, False),
    "d16_E_three_quarter_eye": ((15.0, -10.0, 1.7), (1.5, -1.0, 3.6), 28, False),
    "d17_W_three_quarter_eye": ((-15.0, -10.0, 1.7), (-1.5, -1.0, 3.6), 28, False),
}


def shoot(name, loc, tgt, lens, red):
    small = "thumb" in name
    scn.render.resolution_x, scn.render.resolution_y = (320, 180) if small else (1280, 720)
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    for o in aux:
        o.hide_render = False
    sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1); bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24; scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png"); bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1); bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4; scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(out, name + "_red.png"); bpy.ops.render.render(write_still=True)


for name, (loc, tgt, lens, red) in SHOTS.items():
    if only and not any(name.startswith(p) for p in only):
        continue
    shoot(name, loc, tgt, lens, red)
    print("SHOT", name, flush=True)
