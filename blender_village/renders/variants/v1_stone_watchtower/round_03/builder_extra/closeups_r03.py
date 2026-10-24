"""builder close-ups, v1_stone_watchtower round 3 (same clay / sun / world as render_review).
python closeups.py <blend> <out_dir> [names] [samples]"""
import math
import os
import sys

import bpy
from mathutils import Vector

blend, out = sys.argv[1], os.path.abspath(sys.argv[2])
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] not in ("", "all") else None
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 24
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def P(az, r, z):
    a = math.radians(az)
    return Vector((math.sin(a) * r, -math.cos(a) * r, z))


SHOTS = {
    "c01_slit2_under_string_az-60": (P(-60, 4.0, 4.9), P(-60, 2.3, 5.15), 45),
    "c02_cabin_bed_on_cornice_below": (P(25, 4.6, 7.2), P(20, 2.3, 9.0), 30),
    "c03_strut_foot_pad_az45": (P(25, 4.2, 7.0), P(45, 2.35, 7.55), 40),
    "c04_cabin_eave_soffit": (P(-25, 5.6, 9.8), P(-5, 2.9, 11.2), 30),
    "c05_cap_finial": (P(-30, 9.0, 15.5), Vector((0, 0, 15.2)), 70),
    "c06_cabin_opening_raking": (P(-35, 6.0, 10.8), P(0, 2.7, 10.7), 40),
    "c07_thumbnail_45m": (P(-35, 45, 8.0), Vector((0, 0, 8.4)), 50),
    "c08_neighbour_eye_level": (P(-60, 10.0, 9.0), P(-60, 2.3, 9.8), 40),
    "c09_cabin_corner_below": (P(-45, 4.0, 8.2), P(-45, 3.6, 9.3), 28),
}
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -0.007))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
w = bpy.data.worlds.new("_REVIEW_world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
scn.world = w
loc = Vector((1.0, -3.4, 0.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=loc + Vector((0, 0, 0.725)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=loc + Vector((0, 0, 1.68)))
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
scn.cycles.samples = samples
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
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
    scn.render.filepath = os.path.join(out, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", name, flush=True)
