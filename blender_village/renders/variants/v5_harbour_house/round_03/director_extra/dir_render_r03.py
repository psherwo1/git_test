"""Director round-3 junction close-ups for v5_harbour_house (coordinates after the build's recentre).
python -I dir_render_r03.py -- <blend> <out_dir> [only_prefix ...]
Scene: quay-datum land blocks (top Z = -0.045) round the slip and behind the quay face line (y = 3.43), a water plane
at Z = -0.9, 1.8 m figures at the hall door, the wing door, on the jetty and on the west quay.  `red` twins: black
override, red world, no land / water / figures (see-through check)."""
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


clay = mat("_DIR_clay", (0.42, 0.41, 0.39))
black = mat("_DIR_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
aux = []
TOP = -0.045


def box(x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object; o.scale = (x1 - x0, y1 - y0, z1 - z0); aux.append(o)


YQ = 3.427 - 0.30          # behind the quay blocks
YS = 0.227 - 0.30          # behind the slip head
box(-100, 100, -100, YS, -3.0, TOP)
box(-100, -0.408 - 0.30, YS, YQ, -3.0, TOP)
box(4.192 + 0.30, 100, YS, YQ, -3.0, TOP)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.9)); water = bpy.context.object
water.scale = (200, 200, 1); aux.append(water)
for (x, y, z) in ((2.99, -7.0, TOP), (-5.4, -8.7, TOP), (6.8, 6.2, -0.04), (-2.6, 2.6, TOP)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x, y, z + 0.775)); aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x, y, z + 1.67)); aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38))); sun = bpy.context.object
sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_DIR_world"); world.use_nodes = True
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
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

SHOTS = {
    "x01_ref4_angle": ((10.5, 19.0, 9.5), (0.5, -1.5, 4.0), 32, False),
    "x02_thumb_45m": ((-30.0, -36.0, 14.0), (0.5, -2.0, 4.0), 50, False),
    "x03_land_door_eye": ((3.6, -12.0, 1.65), (2.6, -5.8, 1.6), 28, False),
    "x04_tower_hall_gable_junction": ((2.6, -9.2, 1.7), (0.9, -5.8, 1.8), 35, True),
    "x05_tower_wing_S_junction": ((-4.2, -11.0, 1.7), (-2.86, -7.7, 1.8), 35, True),
    "x06_wing_door_eye": ((-4.6, -12.0, 1.65), (-5.4, -7.7, 1.3), 30, False),
    "x07_main_roof_tower_land": ((3.5, -11.5, 8.0), (-0.2, -4.8, 5.6), 45, True),
    "x08_main_roof_tower_west": ((-6.5, -1.0, 8.5), (-0.8, -4.3, 5.2), 42, True),
    "x09_wing_roof_tower_S": ((-6.5, -11.5, 6.5), (-2.7, -6.6, 4.0), 40, True),
    "x10_wing_roof_tower_N_nook": ((-5.5, -0.5, 4.5), (-2.0, -4.2, 3.3), 35, True),
    "x11_nook_eye": ((-4.5, -1.5, 1.65), (-1.6, -3.9, 2.6), 30, True),
    "x12_tower_top_foot_ring": ((2.8, -10.5, 7.6), (-1.3, -6.2, 7.6), 50, True),
    "x13_cone_eave_lookup": ((0.8, -9.2, 5.5), (-1.3, -6.6, 8.7), 38, True),
    "x14_cone_apex_finial": ((2.5, -11.5, 13.0), (-1.3, -6.0, 12.4), 75, False),
    "x15_water_gable_from_water": ((1.9, 13.5, 1.4), (1.9, 3.4, 4.0), 28, False),
    "x16_tie_bearing_E_pier": ((7.2, 6.8, 3.6), (4.4, 3.43, 3.4), 42, True),
    "x17_jamb_post_pad_E": ((2.4, 6.2, 0.5), (4.1, 3.3, 0.3), 32, True),
    "x18_jamb_post_pad_W": ((1.4, 6.2, 0.5), (-0.3, 3.3, 0.3), 32, True),
    "x19_slip_interior": ((1.9, 7.0, 1.0), (1.9, 0.3, 1.0), 28, True),
    "x20_arch_soffit_lookup": ((1.9, 4.6, 0.4), (1.9, 3.4, 3.0), 24, True),
    "x21_apex_water_finial_blades": ((4.2, 9.0, 9.0), (1.9, 3.6, 8.2), 60, True),
    "x22_E_eave_corner_water": ((7.5, 7.0, 2.6), (5.0, 3.5, 3.3), 40, True),
    "x23_E_eave_lookup": ((7.5, -1.5, 1.65), (4.9, -1.0, 3.5), 34, True),
    "x24_W_eave_lookup": ((-4.0, 0.8, 1.65), (-1.1, -1.0, 3.4), 34, True),
    "x25_land_verge_apex": ((4.8, -10.0, 6.2), (2.0, -6.0, 7.9), 48, True),
    "x26_wing_free_gable": ((-11.5, -9.5, 3.8), (-7.6, -6.0, 4.0), 36, True),
    "x27_quay_W_end_pier": ((-6.5, 7.5, 0.6), (-2.5, 3.4, -0.3), 30, True),
    "x28_quay_E_end_jetty": ((11.0, 7.5, 0.8), (7.6, 3.5, -0.3), 30, True),
    "x29_jetty_underside": ((3.4, 9.8, -0.6), (6.8, 6.0, -0.5), 30, False),
    "x30_jetty_deck_to_quay": ((6.8, 10.5, 1.65), (6.8, 3.5, 0.0), 32, True),
    "x31_hall_E_window": ((7.0, -5.2, 1.8), (4.9, -3.57, 1.9), 40, True),
    "x32_slip_quay_joints": ((1.9, 5.5, -0.3), (4.19, 1.5, -0.5), 30, True),
    "x33_outer_quay_face_close": ((-3.0, 5.0, -0.5), (-3.5, 3.43, -0.7), 30, True),
    "x34_side_elevation_eye": ((16.0, -1.0, 2.0), (1.9, -1.0, 4.5), 30, False),
    "y01_slip_mouth_water_level_nowater": ((1.9, 9.5, -1.2), (1.9, 3.3, -0.9), 30, True),
    "y02_E_respond_from_slip_nowater": ((1.6, 2.2, -1.0), (4.0, 3.3, -1.2), 28, True),
    "y03_W_respond_from_slip_nowater": ((2.2, 2.2, -1.0), (-0.2, 3.3, -1.2), 28, True),
    "y04_E_respond_from_water_nowater": ((5.6, 6.0, -1.0), (4.05, 3.45, -1.2), 30, True),
    "y05_W_respond_from_water_nowater": ((-1.8, 6.0, -1.0), (-0.3, 3.45, -1.2), 30, True),
    "y06_E_post_foot_close": ((3.0, 4.6, 0.6), (4.05, 3.35, 0.0), 35, True),
    "y07_W_post_foot_close": ((0.8, 4.6, 0.6), (-0.27, 3.35, 0.0), 35, True),
    "y08_E_respond_grazing_joint_nowater": ((1.9, 3.52, -1.95), (4.3, 3.52, -1.95), 50, True),
    "y09_post_to_slipwall_gap": ((1.9, 2.4, 1.2), (4.1, 3.2, 1.0), 40, True),
    "y10_slip_head_corners_nowater": ((1.9, 4.5, -0.8), (1.9, 0.2, -1.2), 22, True),
    "y11_E_corner_diag_nowater": ((3.2, 4.6, -1.0), (4.192, 3.427, -1.2), 30, True),
    "y12_W_corner_diag_nowater": ((0.6, 4.6, -1.0), (-0.408, 3.427, -1.2), 30, True),
    "y13_quay_free_end_W_nowater": ((-6.0, 5.5, -1.0), (-4.3, 3.0, -1.2), 30, True),
    "y14_ref4_angle_high": ((14.0, 22.0, 13.0), (1.0, -1.5, 3.5), 30, False),
    "y15_land_three_quarter_eye": ((12.0, -16.0, 1.65), (1.0, -3.0, 4.0), 28, False),
}

def shoot(name, loc, tgt, lens, red):
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    for o in aux:
        o.hide_render = False
    water.hide_render = name.endswith("nowater")
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
