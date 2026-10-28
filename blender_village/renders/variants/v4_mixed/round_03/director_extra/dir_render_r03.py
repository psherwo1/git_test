"""Director close-ups of every module junction, v4_mixed round 3 (same clay / sun / world as render_review).
python dir_render_r03.py <blend> <out_dir> [names|all] [samples] [red]
'red': black clay on a red sky, no ground plane -- any red pixel inside the silhouette is see-through."""
import math
import os
import sys

import bpy
from mathutils import Vector

blend, out = sys.argv[1], os.path.abspath(sys.argv[2])
arg = sys.argv[3] if len(sys.argv) > 3 else "all"
only = None if arg in ("", "all") else set(arg.split(","))
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 24
red = len(sys.argv) > 5 and sys.argv[5] == "red"
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
V = Vector
H = V((-1.462, 0.214, 0.0))
M = V((2.82, 1.36, 0.0))

SHOTS = {
    # roof into drum: both eave ends from outside at eye level, and looking up under the eave
    "r01_eave_end_front_eye": (V((0.3, -4.2, 1.65)), V((1.1, -0.3, 2.5)), 35),
    "r02_eave_end_front_lookup": (V((0.35, -1.45, 1.55)), V((1.05, -0.1, 2.75)), 22),
    "r03_eave_end_back_eye": (V((-0.2, 5.2, 1.65)), V((0.95, 2.2, 2.5)), 35),
    "r04_eave_end_back_lookup": (V((0.15, 3.25, 1.55)), V((0.95, 2.1, 2.75)), 22),
    "r05_eave_end_front_close": (V((0.55, -1.9, 2.3)), V((1.1, -0.25, 2.55)), 35),
    "r06_eave_end_back_close": (V((0.35, 3.85, 2.3)), V((0.95, 2.2, 2.55)), 35),
    # flaunching along the roof/drum line
    "r07_fillet_crane_front": (V((-1.0, -5.0, 7.5)), V((1.3, 0.9, 3.0)), 35),
    "r08_fillet_crane_back": (V((-1.2, 6.8, 6.5)), V((1.2, 1.2, 3.0)), 35),
    "r09_fillet_over_house": (V((-3.8, 1.0, 8.8)), V((1.3, 1.0, 3.0)), 35),
    "r10_fillet_mid_front": (V((-1.5, -6.5, 4.0)), V((1.2, 0.8, 3.0)), 40),
    "r11_band_over_roof": (V((-2.5, -2.2, 6.0)), V((1.3, 1.0, 4.0)), 35),
    # wall into drum: abutment posts and pointing, plinth into footing
    "w01_abutment_front_eye": (V((-0.1, -2.4, 1.5)), V((1.0, 0.1, 1.3)), 30),
    "w02_abutment_back_eye": (V((-0.2, 3.7, 1.5)), V((0.9, 1.6, 1.3)), 30),
    "w03_plinth_footing_front": (V((0.25, -2.0, 0.8)), V((1.0, 0.1, 0.15)), 30),
    "w04_plinth_footing_back": (V((0.0, 3.4, 0.8)), V((0.9, 1.6, 0.15)), 30),
    "w05_post_head_plate_front": (V((0.2, -1.3, 2.0)), V((1.0, 0.1, 2.75)), 30),
    # interior through the house doorway toward the drum side
    "i01_house_interior_to_drum": (V((-1.46, -2.65, 1.6)), V((0.9, 1.0, 1.4)), 22),
    # family-to-family joints inside each wing (apex, doors, apron, cap, wheel)
    "a01_house_apex_finial": (V((-4.5, -5.5, 7.6)), V((-1.46, 0.21, 7.4)), 60),
    "a02_house_door_actor": (V((-1.46, -6.8, 1.65)), V((-1.46, -2.3, 1.4)), 35),
    "a03_mill_door_reentrant": (V((2.0, -4.6, 1.65)), V((2.7, -0.4, 1.3)), 35),
    "a04_apron_cornice_smock": (V((5.8, -4.6, 6.4)), V((2.82, 1.36, 6.0)), 40),
    "a05_cap_tail_boom": (V((-2.2, 7.4, 11.0)), V((1.8, 3.0, 10.8)), 35),
    "a06_wheel_hub_cap": (V((3.3, -5.0, 11.2)), V((3.3, 0.0, 11.0)), 40),
    "a07_house_eave_closure_west": (V((-5.6, -0.8, 1.7)), V((-3.9, 0.2, 2.75)), 30),
    # reads
    "t01_thumbnail_45m_az210": (V((-22.0, -38.0, 9.0)), V((0.5, 1.0, 5.5)), 50),
    "t02_overview_junction_mid": (V((-3.5, -7.5, 5.0)), V((1.2, 0.9, 3.2)), 30),
    # second pass: reframed shots (first-pass cameras for r02 / w05 sat inside the house, w01 / w03 / r09 blocked)
    "r02b_eave_end_front_lookup": (V((0.75, -1.55, 1.6)), V((1.05, -0.15, 2.75)), 22),
    "r09b_fillet_over_house": (V((-2.6, -3.6, 8.3)), V((1.2, 1.0, 3.2)), 35),
    "r12_fillet_top_band_front_above": (V((-0.2, -1.0, 6.8)), V((1.18, 0.76, 3.82)), 40),
    "r13_fillet_top_band_back_above": (V((0.0, 2.8, 6.0)), V((1.18, 0.76, 3.82)), 40),
    "w01b_abutment_front_eye": (V((1.2, -2.0, 1.5)), V((1.1, 0.15, 1.3)), 30),
    "w03b_plinth_footing_front": (V((1.0, -1.6, 0.7)), V((1.1, 0.15, 0.15)), 30),
    "w05b_post_head_plate_front": (V((1.2, -1.9, 1.7)), V((1.1, 0.15, 2.75)), 28),
    # house wall head under the eave, eye level 4 m from the house centre (probe 5: back faces seen through the
    # culled wall plate / daub top on the west side)
    "h01_wall_head_west_4m": (V((-5.46, 0.214, 1.65)), V((-4.01, 0.214, 2.7)), 35),
    "h02_wall_head_sw_4m": (V((-5.33, -0.82, 1.65)), V((-3.93, -0.45, 2.7)), 35),
    "h03_wall_head_nw_4m": (V((-4.93, 2.21, 1.65)), V((-3.67, 1.49, 2.7)), 35),
    "h04_wall_head_west_close": (V((-5.0, 0.0, 2.0)), V((-4.0, 0.3, 2.75)), 40),
    # director test build (scratch): the same recipe with HOUSE overhang 1.10 m, so a rafter lands on the drum outside
    # the wall head and junctions.rafter_bearings places a pad on a corbel (pad at about (1.94, -0.35, 2.36-2.47))
    "x01_bearing_test_overhang110_front": (V((1.1, -2.6, 1.55)), V((1.94, -0.35, 2.4)), 35),
    "x02_bearing_test_overhang110_side": (V((3.0, -2.2, 1.7)), V((1.94, -0.35, 2.4)), 35),
}
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1) if red else (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
if not red:
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -0.007))
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.angle = math.radians(2.0)
w = bpy.data.worlds.new("_REVIEW_world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 0, 0, 1) if red else (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0 if red else 0.45
scn.world = w
loc = V((-0.2, -3.6, 0.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=loc + V((0, 0, 0.725)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=loc + V((0, 0, 1.68)))
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
scn.cycles.samples = 4 if red else samples
scn.cycles.use_denoising = not red
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "Standard" if red else "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02
cam.data.clip_end = 2000
for name, (c, t, lens) in SHOTS.items():
    if only and name not in only:
        continue
    cam.location = c
    cam.data.lens = lens
    cam.rotation_euler = (t - c).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(out, f"{name}{'_seethrough_red' if red else ''}.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", name, flush=True)
