"""Builder round-2 close-ups for v6_barn (adapted from v5 dir_render_r08.py: clay, sun, 1.8 m figures, `red` twins =
black override + red world, no ground / figures: see-through check).  Coordinates after the build's recentre
(+0.058, -3.678): kiln axis (0.058, -3.678), front wall y -1.378, back wall y 5.622, gables x -6.942 / 7.058, ridge
line y 2.122, cart doors x -4.442.
python -I bld_render_r02.py -- <blend> <out_dir> [only_prefix ...]"""
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


clay = mat("_B_clay", (0.42, 0.41, 0.39))
black = mat("_B_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.002)); gr = bpy.context.object
gr.scale = (300, 300, 1); aux.append(gr)
for (x, y) in ((-4.0, -4.2), (2.6, -6.6), (-9.0, 1.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=(x, y, 0.725)); aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, 1.68)); aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38))); sun = bpy.context.object
sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_B_world"); world.use_nodes = True
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
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

KX, KY = 0.058, -3.678                       # round 2: recentred by (+0.058, -3.678)
FW, RL, BW, GW, GE = -1.378, 2.122, 5.622, -6.942, 7.058   # front wall, ridge line, back wall, gables
SHOTS = {
    "b01_kiln_squat_front_eye": ((7.5, -14.0, 2.2), (KX, KY + 1.2, 3.4), 30, False),
    "b02_cart_doors_eye": ((-5.5, -7.2, 1.65), (-4.442, FW, 2.0), 30, False),
    "b03_west_gable_verge_roll": ((-12.5, -2.5, 5.0), (GW, RL, 5.6), 36, False),
    "b04_ref4_three_quarter_high": ((-15.0, -17.0, 11.0), (0.0, 1.0, 3.2), 32, False),
    "b05_side_elev_W_rake": ((-26.0, RL, 4.6), (GW, RL, 5.2), 50, True),
    "b06_kiln_vs_ridge_front": ((KX, -24.0, 4.0), (KX, RL, 4.6), 40, False),
    "s08_eave_lift_lookup": ((-4.4, FW - 2.2, 1.5), (-4.44, FW - 0.25, 3.1), 30, True),
    "s09_ridge_comb_close": ((-2.0, RL - 3.55, 9.0), (-2.0, RL, 7.2), 45, True),
    "s10_W_apex_finial_verge": ((-10.0, RL - 2.05, 7.4), (GW, RL, 7.0), 50, True),
    "s12_SE_corner_eave_verge": ((10.0, FW - 2.65, 2.4), (GE, FW, 2.9), 40, True),
    "s13_NW_corner_back": ((-10.5, BW + 2.95, 2.6), (GW, BW, 2.8), 38, True),
    "s16_ridge_spars_close": ((1.0, RL - 1.6, 8.7), (2.2, RL, 7.6), 50, False),
    "d02_kiln_back_thatch_W_from_ridge": ((KX - 3.5, KY + 6.2, 8.6), (KX - 1.0, KY + 2.4, 3.9), 40, True),
    "d03_kiln_back_thatch_E_from_ridge": ((KX + 3.5, KY + 6.2, 8.6), (KX + 1.0, KY + 2.4, 3.9), 40, True),
    "d05_eave_lip_into_kiln_W_low": ((KX - 4.6, KY - 3.0, 2.0), (KX - 1.3, FW - 0.6, 3.0), 38, True),
    "d06_eave_lip_into_kiln_E_low": ((KX + 4.6, KY - 3.0, 2.0), (KX + 1.3, FW - 0.6, 3.0), 38, True),
    "d09_SW_corner_eave_verge_lift": ((-10.0, FW - 2.85, 2.4), (GW, FW, 2.9), 40, True),
    "d10_ridge_skyline_E_half": ((4.5, RL - 17.55, 7.4), (4.5, RL, 7.1), 85, True),
    "d13_thumb_SW_45m": ((-30.0, -36.0, 14.0), (0.0, 0.0, 4.0), 50, False),
    "d14_thumb_SE_45m": ((32.0, -34.0, 14.0), (0.0, 0.0, 4.0), 50, False),
    "d16_E_three_quarter_eye": ((15.0, -10.0, 1.7), (1.5, -1.0, 3.6), 28, False),
}

def shoot(name, loc, tgt, lens, red):
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
