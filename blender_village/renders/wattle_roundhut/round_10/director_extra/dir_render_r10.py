"""Director close-ups, round 10 (same clay/sun/world as tools/render_review.py).
Run: blender -b <blend> --python dir_render_r10.py -- <out_dir> [names]
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
only = set(argv[1].split(",")) if len(argv) > 1 else None
os.makedirs(out, exist_ok=True)
scn = bpy.context.scene


def P(az, r, z):
    a = math.radians(az)
    return Vector((math.sin(a) * r, -math.cos(a) * r, z))


HERO = Vector((-10.97, -15.86, 5.72))
ACTOR = Vector((-1.367, -8.343, 1.65))
SIDE = Vector((30.03, -0.195, 5.57))
BACK = Vector((0.0, 16.4, 6.4))
SHOTS = {
    # name: (cam, target, lens)
    "eave_patch": (P(-85, 5.3, 1.65), P(-85, 3.5, 1.80), 35),
    "eave_patch_hero_tele": (HERO, P(-85, 3.5, 1.80), 135),
    "side_patch": (P(81, 5.2, 1.40), P(81, 3.5, 1.33), 35),
    "side_patch_side_tele": (SIDE, P(81, 3.5, 1.33), 135),
    "back_low": (P(154, 5.0, 1.20), P(154, 3.5, 0.50), 35),
    "door_bay": (P(-34, 4.9, 1.30), P(-34, 3.5, 0.85), 35),
    "lintel": (ACTOR, Vector((0.5, -3.72, 2.30)), 85),
    "eave_under_door": (Vector((1.3, -5.4, 1.65)), Vector((0.3, -3.9, 2.45)), 28),
    "roof_flank": (HERO, P(-35, 2.4, 4.6), 120),
    "apex": (HERO + Vector((0, 0, 3)), Vector((0, 0, 7.2)), 200),
    "entrance_plinth": (Vector((-1.9, -5.0, 0.95)), Vector((-1.3, -3.6, 0.30)), 35),
    "door_depth": (Vector((0.15, -6.0, 1.6)), Vector((0.0, -3.0, 1.2)), 40),
}

lo, hi = Vector((-4.19, -4.59, -0.041)), Vector((4.19, 4.20, 8.73))
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, lo.z - 0.002))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
w = bpy.data.worlds.new("_REVIEW_world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
scn.world = w
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
scn.cycles.samples = 32
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02
for name, (c, t, lens) in SHOTS.items():
    if only and name not in only:
        continue
    cam.location = c
    cam.data.lens = lens
    cam.rotation_euler = (t - c).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(out, f"{name}_r10.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", name)

