"""Director junction close-ups, v1_stone_watchtower round 1 (same clay/sun/world as tools/render_review.py).
Run: blender -b <blend> --python dir_render_r01.py -- <out_dir> [names]
Also prints per-object bounds / junction measurements.
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
only = set(argv[1].split(",")) if len(argv) > 1 and argv[1] else None
os.makedirs(out, exist_ok=True)
scn = bpy.context.scene


def P(az, r, z):
    a = math.radians(az)
    return Vector((math.sin(a) * r, -math.cos(a) * r, z))


# ---- measurements ------------------------------------------------------------------------------------------------
dg = bpy.context.evaluated_depsgraph_get()
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type != "MESH" or o.data.users > 1 and not o.name.endswith(("_000", "_0")):
        pass
    if o.type == "MESH":
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        zs = [w.z for w in ws]
        rs = [math.hypot(w.x, w.y) for w in ws]
        if not o.name.startswith(("WATCH_baluster", "WATCH_corbel", "WATCH_peg")):
            print("OBJ %-28s z %6.3f..%6.3f  rmax %5.3f  polys %d" % (o.name, min(zs), max(zs), max(rs),
                                                                     len(o.data.polygons)))

SHOTS = {
    # name: (cam, target, lens)
    "j01_parapet_on_corbels_tele": (P(-30, 16, 3.0), P(-30, 2.6, 8.9), 160),
    "j02_parapet_on_corbels_eave_level": (P(40, 5.8, 8.4), P(40, 2.4, 8.9), 35),
    "j03_soffit_look_up": (P(-60, 4.2, 7.2), P(-60, 2.6, 9.5), 28),
    "j04_rafter_feet_eave_closure": (P(100, 3.5, 9.05), P(100, 2.3, 9.8), 30),
    "j05_eave_lip_profile": (P(90, 14, 9.5), P(0, 3.1, 9.5), 100),
    "j06_eave_from_crane": (P(-120, 8, 12.5), P(-120, 2.7, 9.5), 50),
    "j07_collar_finial": (P(-30, 8, 13.5), Vector((0, 0, 13.7)), 85),
    "j08_collar_top_course_crane": (P(150, 6, 17.5), Vector((0, 0, 13.1)), 85),
    "j09_string_course_band": (P(-40, 5.0, 5.0), P(-40, 2.3, 5.5), 35),
    "j10_band_from_ground_tele": (P(20, 10, 1.65), P(20, 2.3, 5.5), 135),
    "j11_slit_az-18": (P(-18, 4.8, 6.9), P(-18, 2.2, 6.75), 50),
    "j12_slit_az62": (P(62, 4.2, 2.9), P(62, 2.3, 2.9), 50),
    "j13_door_step_ground": (P(-28, 3.7, 0.55), P(-5, 2.35, 0.2), 35),
    "j14_door_depth_ceiling": (Vector((0.0, -5.2, 0.9)), Vector((0.0, -1.0, 2.6)), 35),
    "j15_footing_back": (P(160, 4.0, 0.45), P(160, 2.35, 0.2), 35),
    "j16_thumbnail_far": (P(-35, 45, 8.0), Vector((0, 0, 7.6)), 50),
    "j17_top_storey_eye_level_neighbour": (P(-70, 9.0, 9.0), P(-70, 2.3, 8.9), 50),
}

lo = Vector((-3.21, -3.18, -0.005))
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, lo.z - 0.002))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
w = bpy.data.worlds.new("_REVIEW_world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
scn.world = w
# 1.80 m figure beside the door
loc = Vector((1.0, -3.3, 0.0))
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
scn.cycles.samples = 32
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
    print("WROTE", name)
