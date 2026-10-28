"""Director round-1 junction close-ups for v5_harbour_house.
python -I dir_render_r01.py <blend> <out_dir> [only_prefix ...]
Scene: a land block (top Z = -0.004) for y < 2.0 (the quay / terrain the house will be placed in), a water plane at
Z = -0.9 for the harbour, a 1.8 m figure on the quay at the land door and one on the deck.  `red` twins: black
override, red world, no land / water / figures (see-through check)."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
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
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -48.0, -1.302)); land = bpy.context.object
land.scale = (200, 100, 2.596); aux.append(land)                          # top -0.004, y in (-98, 2.0)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 51.0, -0.9)); water = bpy.context.object
water.scale = (200, 98, 1); aux.append(water)                             # y in (2.0, 100)
for (x, y, z) in ((0.9, -8.75, 0.0), (-1.6, 3.4, 0.5)):
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
    "d01_land_gable_door_eye": ((1.6, -16.5, 1.65), (0.0, -7.4, 2.6), 26, False),
    "d02_sw_corner_ground_eye": ((-4.8, -9.8, 1.3), (-2.8, -7.23, 1.0), 40, True),
    "d03_sw_jetty_corner_lookup": ((-4.3, -10.0, 1.6), (-2.8, -7.5, 3.2), 45, True),
    "d04_jetty_soffit_lookup": ((-0.8, -8.7, 1.5), (0.3, -7.45, 3.15), 30, True),
    "d05_east_eave_lookup": ((4.9, -5.0, 1.65), (3.0, -4.0, 5.4), 35, True),
    "d06_verge_foot_sw": ((-5.8, -10.8, 4.6), (-3.3, -8.15, 5.4), 50, True),
    "d07_apex_horns_land": ((-3.0, -13.5, 9.6), (0.0, -8.2, 9.4), 70, True),
    "d08_apex_horns_water": ((3.0, 8.5, 10.0), (0.0, 2.2, 9.4), 60, True),
    "d09_water_gable_boat_door_deck": ((-1.0, 7.4, 2.15), (0.0, 1.77, 2.6), 30, False),
    "d10_deck_sill_junction": ((-2.2, 3.2, 1.1), (-1.0, 1.8, 0.5), 35, True),
    "d11_deck_underside_waterlevel": ((-6.5, 7.0, -0.6), (0.0, 4.0, -0.1), 28, False),
    "d12_jetty_finger_end_ladder": ((4.6, 12.5, 1.2), (1.3, 8.9, 0.0), 35, False),
    "d13_east_wall_eye": ((8.0, -3.0, 1.65), (2.8, -3.0, 2.8), 28, True),
    "d14_ne_corner_band_rim": ((5.2, 4.2, 3.0), (2.8, 1.77, 3.2), 40, True),
    "d15_window_shutter_close": ((4.1, -0.2, 1.95), (2.8, -1.13, 1.95), 35, True),
    "d16_door_steps_close": ((1.5, -9.8, 1.25), (0.0, -7.5, 0.45), 35, False),
    "d17_upper_loading_door": ((2.6, 7.5, 5.0), (0.0, 1.77, 4.3), 45, True),
    "d18_crane_roof_ne": ((11.0, 9.0, 14.0), (0.0, -2.7, 6.5), 35, True),
    "d19_thumbnail_45m": ((-30.0, -36.0, 14.0), (0.0, -1.5, 4.0), 50, False),
    "d20_gable_verge_underside_sw": ((-4.6, -6.3, 3.9), (-2.85, -7.9, 5.8), 35, True),
    "d21_nw_corner_plinth_crib": ((-5.4, 3.3, 0.9), (-2.8, 1.77, 0.4), 40, False),
    "d22_boat_door_head_band_oblique": ((-2.6, 3.4, 2.5), (-1.45, 1.77, 3.05), 38, False),
    "d23_crib_land_face_buried_check": ((-6.5, -12.5, 0.6), (-3.5, -8.9, -0.6), 35, False),
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
