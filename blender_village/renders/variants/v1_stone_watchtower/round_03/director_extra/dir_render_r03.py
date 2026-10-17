"""Director close-ups of every module junction, v1_stone_watchtower round 3 (same clay / sun / world as render_review).
python dir_render_r03.py <blend> <out_dir> [names|all|probe] [samples]
'probe' prints junction contact measurements (BVH overlap + nearest distance) and renders nothing."""
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend, out = sys.argv[1], os.path.abspath(sys.argv[2])
arg = sys.argv[3] if len(sys.argv) > 3 else "all"
only = None if arg in ("", "all", "probe") else set(arg.split(","))
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 24
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def P(az, r, z):
    a = math.radians(az)
    return Vector((math.sin(a) * r, -math.cos(a) * r, z))


def bvh(name):
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH":
        return None, None
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = [ob.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(V, F), V


if arg == "probe":
    pairs = [("WATCH_cabin_struts", "WATCH_cabin_corbels"), ("WATCH_cabin_struts", "WATCH_cabin_floor"),
             ("WATCH_cabin_corbels", "WATCH_base_stones"), ("WATCH_cabin_corbels", "WATCH_base_mortar"),
             ("WATCH_cabin_corbels", "WATCH_wall_core"),
             ("WATCH_cabin_floor", "WATCH_base_dressed"), ("WATCH_cabin_bed", "WATCH_base_dressed"),
             ("WATCH_cabin_frame", "WATCH_cabin_floor"), ("WATCH_cabin_boards", "WATCH_cabin_frame"),
             ("WATCH_cabin_roof_frame", "WATCH_cabin_frame"), ("WATCH_cabin_roof_deck", "WATCH_cabin_roof_frame"),
             ("WATCH_cabin_ceiling", "WATCH_cabin_frame"),
             ("WATCH_cabin_shingles", "WATCH_cabin_roof_deck"), ("WATCH_cabin_hips", "WATCH_cabin_shingles"),
             ("WATCH_cabin_lead", "WATCH_cabin_shingles"), ("WATCH_cabin_lead", "WATCH_cabin_hips"),
             ("WATCH_cabin_finial", "WATCH_cabin_lead")]
    for a, b in pairs:
        ta, Va = bvh(a)
        tb, Vb = bvh(b)
        if ta is None or tb is None:
            print("PROBE", a, b, "missing")
            continue
        ov = len(ta.overlap(tb))
        dmin = min((tb.find_nearest(v)[3] for v in Va), default=-1)
        print("PROBE %-26s -> %-24s overlaps %6d  nearest-vertex %.4f m" % (a, b, ov, dmin), flush=True)
    for n in sorted(o.name for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("WATCH_cabin")):
        ob = bpy.data.objects[n]
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print("BBOX %-26s z %.3f..%.3f  x %.3f..%.3f" % (n, min(v.z for v in bb), max(v.z for v in bb),
                                                        min(v.x for v in bb), max(v.x for v in bb)))
    for n in ("WATCH_base_dressed", "WATCH_base_stones", "WATCH_cabin_finial", "WATCH_cabin_lead"):
        ob = bpy.data.objects.get(n)
        if ob:
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            print("BBOX %-26s z %.3f..%.3f" % (n, min(v.z for v in bb), max(v.z for v in bb)))
    sys.exit(0)

H = 8.70
SHOTS = {
    # crown on the drum: bed, bearers, dragon beams, struts, pads
    "j01_floor_sandwich_level_front": (P(0, 16.0, 8.95), P(0, 0.0, 8.95), 85),
    "j02_floor_sandwich_level_side": (P(90, 16.0, 9.05), P(90, 0.0, 9.05), 85),
    "j03_bearer_on_cornice_az40": (P(28, 4.6, 8.25), P(40, 2.46, 8.78), 45),
    "j04_dragon_beam_strut_head_az45": (P(28, 6.2, 8.1), P(45, 3.45, 8.85), 50),
    "j05_strut_foot_pad_az-135": (P(-118, 4.6, 6.9), P(-135, 2.3, 7.4), 45),
    "j06_underfloor_from_ground": (P(-20, 3.6, 1.7), P(0, 0.4, 9.0), 24),
    "j07_bed_from_above_corner": (P(-45, 5.6, 12.4), P(-45, 2.45, 8.9), 40),
    # cabin body: floor edge / sill, corner post, openings, ceiling
    "j08_sill_on_floor_edge_raking": (P(-52, 6.2, 9.5), P(0, 2.7, 9.35), 60),
    "j09_cabin_corner_post": (P(-45, 6.8, 10.3), P(-45, 3.76, 10.3), 50),
    "j10_through_openings_level": (P(0, 14.0, 10.75), P(0, 0.0, 10.75), 70),
    "j11_ceiling_and_plate_inside": (P(-12, 3.9, 10.75), P(8, -0.8, 11.45), 26),
    # roof: plate / rafter tails / soffit, hips, eave silhouette, cap, finial
    "j12_eave_corner_hip_below": (P(-28, 8.5, 9.6), P(-45, 4.3, 11.0), 60),
    "j13_hip_from_crane": (P(-45, 10.0, 15.5), P(-45, 2.2, 13.0), 50),
    "j14_eave_hip_silhouette_aerial": (P(-10, 7.5, 17.0), P(-45, 3.6, 11.4), 50),
    "j15_apex_cap_from_ground": (P(-20, 18.0, 2.0), Vector((0, 0, 15.2)), 135),
    # drum: string course, slits, door, footing
    "j16_string_course_az90": (P(70, 4.6, 5.25), P(90, 2.3, 5.47), 50),
    "j17_slit1_az60": (P(60, 4.2, 3.0), P(60, 2.4, 2.95), 45),
    "j18_slit3_az180": (P(180, 4.2, 6.55), P(180, 2.3, 6.6), 45),
    "j19_door_step_threshold": (P(-18, 3.4, 1.0), P(0, 2.4, 0.35), 35),
    "j20_back_footing": (P(160, 4.0, 0.8), P(160, 2.5, 0.12), 40),
    # reads
    "j21_thumbnail_45m_az30": (P(30, 45.0, 8.0), Vector((0, 0, 8.4)), 50),
    "j22_neighbour_eye_az120": (P(120, 11.0, 9.6), P(120, 2.4, 10.0), 40),
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
