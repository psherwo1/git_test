"""Director junction close-ups for v3_longhouse_roundend round 6 (director; round-5 cameras + d46-d53).
blender -b --factory-startup --python dir_render.py -- <blend> <out_dir> [only_prefix,...]"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, out = argv[0], argv[1]
only = argv[2].split(",") if len(argv) > 2 else None
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene

C = (4.61, 0.0)   # round end centre (after recentre)
FZ = 6.7          # hat zone

def fin(az, el=25.0, d=3.6):
    a, e = math.radians(az), math.radians(el)
    return ((C[0] + d * math.sin(a) * math.cos(e), C[1] - d * math.cos(a) * math.cos(e), FZ + d * math.sin(e)),
            (C[0], C[1], FZ), 70)

SHOTS = {
    "d01_s_crossing_west_eye": ((-1.0, -4.6, 1.65), (2.3, -3.1, 2.5), 50, True),
    "d02_n_crossing_west_eye": ((-1.0, 4.6, 1.65), (2.3, 3.1, 2.5), 50, True),
    "d03_s_crossing_east_eye": ((6.2, -5.6, 1.65), (2.3, -3.1, 2.5), 50, True),
    "d04_n_crossing_east_eye": ((6.2, 5.6, 1.65), (2.3, 3.1, 2.5), 50, True),
    "d05_s_crossing_tele": ((0.6, -6.0, 1.8), (2.25, -3.15, 2.55), 100, False),
    "d06_n_crossing_tele": ((0.6, 6.0, 1.8), (2.25, 3.15, 2.55), 100, False),
    "d07_s_soffit_lookup": ((1.9, -4.0, 1.45), (2.4, -2.9, 2.6), 28, True),
    "d08_n_soffit_lookup": ((1.9, 4.0, 1.45), (2.4, 2.9, 2.6), 28, True),
    "d09_s_slope_crane": ((-2.0, -9.0, 8.0), (2.6, -1.5, 4.0), 50, True),
    "d10_n_slope_crane": ((-2.0, 9.0, 8.0), (2.6, 1.5, 4.0), 50, True),
    "d11_ridge_into_cone": ((-4.0, 0.6, 7.5), (2.8, 0.0, 5.4), 60, True),
    "d12_junction_top_down": ((2.0, -0.01, 14.0), (2.6, 0.0, 3.0), 35, False),
    "d13_body_round_wall_s": ((0.4, -5.6, 1.2), (2.4, -2.8, 1.3), 40, False),
    "d14_body_round_wall_n": ((0.4, 5.6, 1.2), (2.4, 2.8, 1.3), 40, False),
    "d15_round_wallhead_cone_se": ((7.8, -6.6, 1.65), (6.3, -3.4, 2.6), 40, False),
    "d16_round_eave_lookup_e": ((9.4, 0.4, 1.4), (8.3, 0.0, 2.75), 28, True),
    "d17_gable_verge_sw": ((-11.2, -4.2, 1.65), (-8.6, -2.9, 2.6), 40, True),
    "d18_gable_verge_nw": ((-11.2, 4.2, 1.65), (-8.6, 2.9, 2.6), 40, True),
    "d19_gable_ridge_end": ((-12.5, -1.8, 4.6), (-8.7, 0.0, 5.0), 50, True),
    "d20_body_eave_lookup_door": ((-1.6, -3.7, 1.45), (-2.2, -2.75, 2.45), 24, True),
    "d21_finial_az020": fin(20) + (True,),
    "d21_finial_az110": fin(110) + (True,),
    "d21_finial_az200": fin(200) + (True,),
    "d21_finial_az290": fin(290) + (True,),
    "d22_finial_clay_close": ((C[0] + 0.3, -2.0, 7.4), (C[0], 0.0, 6.6), 85, False),
    "d23_door_closeup": ((-2.4, -5.6, 1.65), (-2.4, -2.6, 1.25), 35, False),
    "d24_round_window": ((7.8, -6.0, 1.55), (6.6, -3.0, 1.45), 40, False),
    "d25_gable_footing_corner": ((-10.6, -4.6, 0.9), (-8.4, -2.6, 0.4), 35, False),
    "d26_back_three_quarter": ((-6.0, 11.0, 4.5), (0.0, 0.0, 2.6), 35, False),
    "d27_hero_junction_mid": ((-0.5, -10.0, 3.2), (2.4, -2.0, 3.0), 45, False),
    "d28_s_notch_tele": ((-0.5, -10.0, 3.2), (2.35, -2.85, 3.0), 160, True),
    "d29_n_notch_tele": ((-0.5, 10.0, 3.2), (2.35, 2.85, 3.0), 160, True),
    "d30_s_soffit_sliver_tele": ((1.4, -4.6, 1.5), (2.3, -3.0, 2.55), 70, True),
    "d31_s_crossing_east_mid": ((9.0, -8.5, 1.65), (2.4, -3.0, 2.6), 35, False),
    "d32_n_crossing_east_mid": ((9.0, 8.5, 1.65), (2.4, 3.0, 2.6), 35, False),
    "d33_s_soaker_crane_tele": ((1.0, -6.5, 6.0), (2.35, -2.85, 2.9), 110, True),
    "d34_n_soaker_crane_tele": ((1.0, 6.5, 6.0), (2.35, 2.85, 2.9), 110, True),
    "d35_s_east_stack_tele": ((5.2, -6.2, 1.9), (2.35, -3.05, 2.6), 120, True),
    "d36_n_east_stack_tele": ((5.2, 6.2, 1.9), (2.35, 3.05, 2.6), 120, True),
    "d37_door_jamb_lichen": ((-2.4, -4.4, 0.9), (-2.4, -2.7, 0.3), 30, False),
    "d38_gable_end_eye": ((-15.0, -2.5, 1.65), (-8.8, 0.0, 4.6), 55, True),
    "d39_gable_ridge_end_tele": ((-15.0, -1.2, 1.65), (-8.9, 0.0, 5.05), 135, True),
    "d40_round_wallhead_lookup_s": ((6.0, -5.0, 1.4), (5.6, -3.6, 2.45), 30, True),
    "d41_round_wallhead_lookup_n": ((3.6, 5.2, 1.4), (4.0, 3.6, 2.45), 30, True),
    "d42_s_saddle_lookup_tele": ((4.2, -5.4, 1.3), (2.45, -3.15, 2.55), 90, True),
    "d43_n_saddle_lookup_tele": ((4.2, 5.4, 1.3), (2.45, 3.15, 2.55), 90, True),
    "d44_n_crossing_east_eye8m": ((8.0, 7.5, 1.65), (2.4, 3.1, 2.6), 50, False),
    "d45_gable_verge_apex_tele": ((-14.0, 0.0, 2.4), (-8.9, 0.0, 4.9), 120, True),
    # round 6 additions: the east stack closer, square-on, along the roll, and the soffit seat
    "d46_s_east_stack_eye3m": ((4.2, -5.0, 1.65), (2.35, -3.05, 2.6), 50, True),
    "d47_n_east_stack_eye3m": ((4.2, 5.0, 1.65), (2.35, 3.05, 2.6), 50, True),
    "d48_s_crossing_square": ((2.4, -7.0, 1.65), (2.4, -3.0, 2.6), 50, True),
    "d49_n_crossing_square": ((2.4, 7.0, 1.65), (2.4, 3.0, 2.6), 50, True),
    "d50_s_along_roll_west": ((-3.5, -3.75, 2.1), (2.3, -3.1, 2.55), 60, True),
    "d51_n_along_roll_west": ((-3.5, 3.75, 2.1), (2.3, 3.1, 2.55), 60, True),
    "d52_s_saddle_seat_lookup": ((3.4, -4.3, 1.5), (2.9, -3.3, 2.5), 70, True),
    "d53_n_saddle_seat_lookup": ((3.4, 4.3, 1.5), (2.9, 3.3, 2.5), 70, True),
}

clay = bpy.data.materials.new("_DIR_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
black = bpy.data.materials.new("_DIR_black")
black.use_nodes = True
bb = black.node_tree.nodes.get("Principled BSDF")
bb.inputs["Base Color"].default_value = (0, 0, 0, 1)
bb.inputs["Roughness"].default_value = 1.0
bb.inputs["Specular IOR Level"].default_value = 0.0

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.002))
ground = bpy.context.object
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_DIR_world")
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
except Exception as e:
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device)
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02

def shoot(name, loc, tgt, lens, red):
    cam.location = Vector(loc)
    cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    # clay
    scn.view_layers[0].material_override = clay
    ground.hide_render = False
    sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24
    scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        ground.hide_render = True
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
    print("SHOT", name)



