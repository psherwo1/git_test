"""Director junction close-ups, v1_stone_watchtower round 2 (same clay/sun/world as tools/render_review.py).
Run: blender -b <blend> --python dir_render_r02.py -- <out_dir> [names]
Graded build: the lookout-storey .blend of 20:05 (copied to scratch before rendering).
Azimuth convention as the kit: az 0 = -Y (door), az 90 = +X.
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


for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type == "MESH" and not o.name.startswith(("WATCH_corbel", "WATCH_peg")):
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        zs = [w.z for w in ws]
        rs = [math.hypot(w.x, w.y) for w in ws]
        print("OBJ %-28s z %6.3f..%6.3f  rmax %5.3f  polys %d" % (o.name, min(zs), max(zs), max(rs),
                                                                 len(o.data.polygons)))

SHOTS = {
    # lookout storey: drum_wall.lookout_room + window_spec(kind="lookout") in the rubble, under the corbel table
    "j01_lookout_front_az0": (P(-8, 5.2, 7.4), P(0, 2.2, 7.5), 40),
    "j02_lookout_reveal_raking_az90": (P(130, 4.0, 7.6), P(90, 2.2, 7.4), 40),
    "j03_lookout_into_room_az180": (P(180, 3.6, 7.35), P(180, 0.6, 7.35), 35),
    "j04_lookout_head_to_cornice_az270": (P(262, 4.0, 8.0), P(270, 2.2, 8.15), 50),
    "j05_lookout_storey_30m_tele": (P(-20, 30, 1.65), P(-20, 2.2, 7.9), 120),
    # string course: drum_band.string_course on the drum
    "j06_string_course_raking": (P(-75, 4.2, 5.2), P(-35, 2.3, 5.48), 40),
    "j07_string_course_drip_from_below": (P(20, 3.4, 4.2), P(20, 2.3, 5.4), 30),
    "j08_string_over_slit2_az-45": (P(-45, 4.0, 4.6), P(-45, 2.3, 4.9), 50),
    # slits: window_spec(kind="slit") stair lights
    "j09_slit1_az45": (P(45, 4.0, 3.0), P(45, 2.35, 2.95), 50),
    "j10_slit3_az-135": (P(-120, 4.0, 6.5), P(-135, 2.25, 6.55), 50),
    # head: parapet on the corbel table, roof on the parapet, collar / finial
    "j11_parapet_on_corbels_tele": (P(-30, 16, 3.0), P(-30, 2.6, 8.9), 160),
    "j12_soffit_rafter_feet": (P(60, 4.0, 7.6), P(60, 2.6, 9.5), 28),
    "j13_eave_from_crane": (P(-120, 8, 12.5), P(-120, 2.7, 9.5), 50),
    "j14_collar_finial": (P(-30, 8, 13.5), Vector((0, 0, 13.7)), 85),
    # ground: door, step, footing
    "j15_door_step_ground": (P(-28, 3.7, 0.55), P(-5, 2.35, 0.2), 35),
    "j16_door_depth_ceiling": (Vector((0.0, -5.2, 0.9)), Vector((0.0, -1.0, 2.6)), 35),
    "j17_footing_back": (P(160, 4.0, 0.45), P(160, 2.35, 0.2), 35),
    # reads
    "j18_thumbnail_45m": (P(-35, 45, 8.0), Vector((0, 0, 7.6)), 50),
    "j19_neighbour_eye_level": (P(-60, 9.0, 8.5), P(-60, 2.3, 8.2), 50),
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
    if os.environ.get("DIR_CPU"):          # shared machine short of GPU memory: render on the CPU
        raise RuntimeError("DIR_CPU set")
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
scn.cycles.samples = 24
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
