"""Director round-6 (eyebrow e-shots re-aimed at the round-6 wave; x/y/z = the round-4 set unchanged). Round-4 junction close-ups for v5_harbour_house (coordinates after the build's recentre, shift -1.808, -5.973).
python -I dir_render_r04.py -- <blend> <out_dir> [only_prefix ...]
The round-3 camera set (dir_render_r03.py) moved with the geometry: slip centre x 1.892 (unchanged), jambs -0.608 / 4.392,
hall faces -1.608 / 5.392, tower axis (-1.808, -5.973), quay ends -4.808 / 8.792, jetty x 6.392-8.192; plus z-shots for
the round-4 roof (eave corners, verge flare, ridge sag, soffits, tie / verge triangle, W arris column).
Scene: quay-datum land blocks (top Z = -0.045) round the slip and behind the quay face line (y = 3.427), water at Z = -0.9,
1.8 m figures.  `red` twins: black override, red world, no land / water / figures (see-through check)."""
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
box(-100, -0.608 - 0.30, YS, YQ, -3.0, TOP)
box(4.392 + 0.30, 100, YS, YQ, -3.0, TOP)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.9)); water = bpy.context.object
water.scale = (200, 200, 1); aux.append(water)
for (x, y, z) in ((2.99, -7.0, TOP), (-5.9, -8.7, TOP), (7.3, 6.2, -0.04), (-3.1, 2.6, TOP)):
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
    "x01_ref4_angle": ((10.5, 19.0, 9.5), (1.0, -1.5, 4.0), 32, False),
    "x02_thumb_45m": ((-30.0, -36.0, 14.0), (0.5, -2.0, 4.0), 50, False),
    "x03_land_door_eye": ((3.6, -12.0, 1.65), (2.6, -5.8, 1.6), 28, False),
    "x04_tower_hall_gable_junction": ((2.1, -9.2, 1.7), (0.4, -5.8, 1.8), 35, True),
    "x05_tower_wing_S_junction": ((-4.7, -11.0, 1.7), (-3.36, -7.7, 1.8), 35, True),
    "x07_main_roof_tower_land": ((3.0, -11.5, 8.0), (-0.7, -4.8, 4.8), 45, True),
    "x08_main_roof_tower_west": ((-7.0, -1.0, 8.5), (-1.3, -4.3, 4.6), 42, True),
    "x09_wing_roof_tower_S": ((-7.0, -11.5, 6.5), (-3.2, -6.6, 4.0), 40, True),
    "x10_wing_roof_tower_N_nook": ((-6.0, -0.5, 4.5), (-2.5, -4.2, 3.3), 35, True),
    "x12_tower_top_foot_ring": ((2.3, -10.5, 7.6), (-1.8, -6.2, 7.6), 50, True),
    "x15_water_gable_from_water": ((1.9, 13.5, 1.4), (1.9, 3.4, 3.6), 26, False),
    "x16_tie_bearing_E_pier": ((7.7, 6.8, 3.6), (4.9, 3.43, 3.4), 42, True),
    "x19_slip_interior": ((1.9, 7.0, 1.0), (1.9, 0.3, 1.0), 28, True),
    "x21_apex_water_finial_blades": ((4.2, 9.0, 8.5), (1.9, 3.6, 7.6), 60, True),
    "x22_E_eave_corner_water": ((8.0, 7.0, 2.6), (5.5, 3.5, 3.0), 40, True),
    "x23_E_eave_lookup": ((8.0, -1.5, 1.65), (5.4, -1.0, 3.2), 34, True),
    "x24_W_eave_lookup": ((-4.5, 0.8, 1.65), (-1.6, -1.0, 3.2), 34, True),
    "x25_land_verge_apex": ((4.8, -10.0, 6.2), (2.0, -6.0, 7.6), 48, True),
    "x26_wing_free_gable": ((-12.0, -9.5, 3.8), (-8.1, -6.0, 4.0), 36, True),
    "x27_quay_W_end_pier": ((-7.0, 7.5, 0.6), (-3.0, 3.4, -0.3), 30, True),
    "x28_quay_E_end_jetty": ((11.5, 7.5, 0.8), (8.1, 3.5, -0.3), 30, True),
    "x30_jetty_deck_to_quay": ((7.3, 10.5, 1.65), (7.3, 3.5, 0.0), 32, True),
    "x34_side_elevation_eye": ((17.0, -1.0, 2.0), (1.9, -1.0, 4.2), 30, False),
    "y01_slip_mouth_water_level_nowater": ((1.9, 9.5, -1.2), (1.9, 3.3, -0.9), 30, True),
    "y06_E_post_foot_close": ((3.2, 4.6, 0.6), (4.25, 3.35, 0.0), 35, True),
    "y07_W_post_foot_close": ((0.6, 4.6, 0.6), (-0.47, 3.35, 0.0), 35, True),
    "y09_post_to_slipwall_gap": ((1.9, 2.4, 1.2), (4.3, 3.2, 1.0), 40, True),
    "y11_E_corner_diag_nowater": ((3.4, 4.6, -1.0), (4.392, 3.427, -1.2), 30, True),
    "y12_W_corner_diag_nowater": ((0.4, 4.6, -1.0), (-0.608, 3.427, -1.2), 30, True),
    "y14_ref4_angle_high": ((14.0, 22.0, 13.0), (1.0, -1.5, 3.5), 30, False),
    "y15_land_three_quarter_eye": ((12.0, -16.0, 1.65), (1.0, -3.0, 4.0), 28, False),
    "z01_W_arris_column_graze_nowater": ((-2.6, 3.95, -1.0), (-0.6, 3.43, -1.1), 40, True),
    "z02_NE_eave_verge_corner": ((7.6, 5.6, 2.0), (6.0, 3.9, 2.8), 38, True),
    "z03_SE_eave_verge_corner_land": ((7.6, -8.4, 2.0), (6.0, -6.3, 2.8), 38, True),
    "z04_ridge_sag_side_high": ((13.0, -1.0, 8.5), (1.9, -1.2, 6.4), 34, False),
    "z05_E_soffit_midlength": ((7.2, -1.2, 1.6), (6.0, -1.2, 2.8), 30, True),
    "z06_water_gable_from_jetty_eye": ((7.3, 9.0, 1.65), (1.9, 3.4, 4.0), 26, False),
    "z07_W_tie_end_verge_triangle": ((-2.8, 6.2, 3.5), (-1.1, 3.43, 3.5), 40, True),
    "z08_roof_wing_tower_from_above": ((-6.5, -1.0, 10.0), (-1.5, -4.6, 4.5), 38, True),
    "z09_NW_eave_verge_corner_water": ((-3.4, 5.6, 2.0), (-2.2, 3.9, 2.8), 38, True),
    "z10_ref4_side_compare": ((15.0, 15.0, 6.0), (1.9, -1.0, 4.0), 30, False),
}
SHOTS.update({
    # round-6 eyebrow (wave y -3.32..0.18, centre y -1.57; front x ~ -1.17, sill z 3.72, wave eave z 4.98; W slope).
    # e01 / e10 are the round-5 cameras unchanged, for a like-for-like before / after.
    "e01_brow_ref4_NW_high": ((-12.0, 10.0, 10.0), (-0.6, -1.6, 4.6), 34, False),
    "e02_brow_square_W_eye": ((-11.0, -1.57, 1.7), (-1.2, -1.57, 4.5), 45, True),
    "e03_brow_square_W_crane": ((-7.5, -1.57, 6.0), (-1.2, -1.57, 4.6), 50, True),
    "e04_brow_oblique_from_S": ((-5.5, -6.5, 5.2), (-1.2, -1.57, 4.6), 50, True),
    "e05_brow_oblique_from_N": ((-5.5, 3.6, 5.2), (-1.2, -1.57, 4.6), 50, True),
    "e08_brow_above_fade": ((-3.5, -1.57, 9.5), (-0.2, -1.57, 5.3), 40, True),
    "e09_brow_window_lowgraze": ((-3.0, -2.3, 4.3), (-1.17, -1.5, 4.3), 45, True),
    "e10_brow_thumb_45m_W": ((-38.0, 8.0, 14.0), (0.5, -2.0, 4.0), 50, False),
    "e11_brow_S_front_end": ((-3.4, -4.3, 4.7), (-1.2, -2.9, 4.3), 50, True),
    "e12_brow_N_front_end": ((-3.4, 1.4, 4.7), (-1.2, -0.25, 4.3), 50, True),
    "e13_brow_crest_from_ridge": ((0.6, -1.57, 8.2), (-0.7, -1.57, 5.3), 35, True),
    "e14_brow_25m_NW": ((-20.0, 8.0, 9.0), (-0.8, -1.6, 4.6), 50, False),
})

SHOTS.update({
    "e15_brow_S_end_from_NW": ((-3.8, -1.2, 5.6), (-1.15, -3.0, 4.85), 45, True),
    "e16_brow_S_end_high": ((-2.6, -4.6, 7.2), (-1.0, -3.0, 4.9), 40, True),
    "e17_brow_N_end_from_SW": ((-3.8, -2.0, 5.6), (-1.15, -0.1, 4.85), 45, True),
})

SHOTS.update({
    # cull check: from the narrow directions where a face r05 had and r06 culled is reachable (cullvis_r06_out.txt)
    "c01_cull_wing_nook_NE": ((-2.880 + 8 * 0.401, -3.879 + 8 * 0.582, 2.674 + 8 * 0.707), (-2.880, -3.879, 2.674), 85, True),
    "c02_cull_tower_E_high": ((-0.024 + 8 * 0.846, -4.800 - 8 * 0.214, 6.747 + 8 * 0.488), (-0.024, -4.800, 6.747), 85, True),
    "c03_cull_tower_from_N": ((-0.609 - 8 * 0.446, -4.178 + 8 * 0.885, 5.203 - 8 * 0.132), (-0.609, -4.178, 5.203), 85, True),
})

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




