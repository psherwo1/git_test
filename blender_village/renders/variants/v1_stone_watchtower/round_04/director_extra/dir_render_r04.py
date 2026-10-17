"""Director close-ups of every module junction, v1_stone_watchtower round 4 (same clay / sun / world as render_review).
python dir_render_r04.py <blend> <out_dir> [names|all|probe|sky] [samples]
'probe' prints junction contact measurements (BVH overlap + nearest distance) and renders nothing.
'sky'   casts level rays through the crown-to-drum floor sandwich (z 8.70-9.19) from 8 azimuths over the FULL
        cornice width (|s| <= 2.50 m) and counts rays that reach the sky, split by lateral band."""
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend, out = sys.argv[1], os.path.abspath(sys.argv[2])
arg = sys.argv[3] if len(sys.argv) > 3 else "all"
only = None if arg in ("", "all", "probe", "sky") else set(arg.split(","))
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 24
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def P(az, r, z):
    a = math.radians(az)
    return Vector((math.sin(a) * r, -math.cos(a) * r, z))


def mesh_data(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = [ob.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


def bvh(name):
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH":
        return None, None
    V, F = mesh_data(ob)
    return BVHTree.FromPolygons(V, F), V


if arg == "probe":
    pairs = [("WATCH_cabin_struts", "WATCH_cabin_corbels"), ("WATCH_cabin_struts", "WATCH_cabin_floor"),
             ("WATCH_cabin_corbels", "WATCH_base_stones"), ("WATCH_cabin_corbels", "WATCH_base_mortar"),
             ("WATCH_cabin_corbels", "WATCH_wall_core"),
             ("WATCH_cabin_floor", "WATCH_base_dressed"), ("WATCH_cabin_bed", "WATCH_base_dressed"),
             ("WATCH_cabin_frame", "WATCH_cabin_floor"), ("WATCH_cabin_boards", "WATCH_cabin_frame"),
             ("WATCH_cabin_roof_frame", "WATCH_cabin_frame"), ("WATCH_cabin_roof_deck", "WATCH_cabin_roof_frame"),
             ("WATCH_cabin_roof_deck", "WATCH_cabin_frame"),
             ("WATCH_cabin_ceiling", "WATCH_cabin_frame"),
             ("WATCH_cabin_shingles", "WATCH_cabin_roof_deck"), ("WATCH_cabin_hips", "WATCH_cabin_shingles"),
             ("WATCH_cabin_hips", "WATCH_cabin_roof_deck"),
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
    # the rim ring: vertices of WATCH_cabin_floor between r 2.27 and 2.41 (the lathe ring), its z range
    ob = bpy.data.objects["WATCH_cabin_floor"]
    V, F = mesh_data(ob)
    ring = [v for v in V if 2.27 <= math.hypot(v.x, v.y) <= 2.41 and v.z < 9.2]
    if ring:
        print("RING verts %d  r %.3f..%.3f  z %.3f..%.3f" % (
            len(ring), min(math.hypot(v.x, v.y) for v in ring), max(math.hypot(v.x, v.y) for v in ring),
            min(v.z for v in ring), max(v.z for v in ring)))
    for n in sorted(o.name for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("WATCH_cabin")):
        ob = bpy.data.objects[n]
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print("BBOX %-26s z %.3f..%.3f  x %.3f..%.3f" % (n, min(v.z for v in bb), max(v.z for v in bb),
                                                        min(v.x for v in bb), max(v.x for v in bb)))
    for n in ("WATCH_base_dressed", "WATCH_base_stones", "WATCH_door_step"):
        ob = bpy.data.objects.get(n)
        if ob:
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            print("BBOX %-26s z %.3f..%.3f  y %.3f..%.3f" % (n, min(v.z for v in bb), max(v.z for v in bb),
                                                            min(v.y for v in bb), max(v.y for v in bb)))
    # materials / mask / transforms on the new objects
    for n in ("WATCH_cabin_floor", "WATCH_cabin_roof_frame", "WATCH_cabin_roof_deck", "WATCH_cabin_shingles",
              "WATCH_cabin_hips", "WATCH_cabin_lead", "WATCH_cabin_finial"):
        ob = bpy.data.objects[n]
        me = ob.data
        ca = me.color_attributes.get("Mask")
        print("OBJ %-24s mats %s  Mask %s/%s active %s  uv %d  loc %s rot %s scale %s" % (
            n, [m.name for m in me.materials if m], ca.domain if ca else None, ca.data_type if ca else None,
            me.color_attributes.active_color_name, len(me.uv_layers), tuple(round(x, 4) for x in ob.location),
            tuple(round(x, 4) for x in ob.rotation_euler), tuple(round(x, 4) for x in ob.scale)))
    sys.exit(0)

if arg == "sky":
    allV, allF = [], []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.name.startswith("WATCH_"):
            continue
        V, F = mesh_data(ob)
        o = len(allV)
        allV += V
        allF += [tuple(i + o for i in f) for f in F]
    T = BVHTree.FromPolygons(allV, allF)
    print("SKY bvh tris-ish", len(allF), flush=True)
    zs = [8.70 + 0.01 * i for i in range(0, 50)]          # 8.70 .. 9.19 (cornice top to deck top)
    for az in (0, 45, 90, 135, 180, 225, 270, 315):
        a = math.radians(az)
        d = Vector((-math.sin(a), math.cos(a), 0.0))         # ray direction toward the axis from azimuth az
        side = Vector((math.cos(a), math.sin(a), 0.0))
        bands = {"|s|<2.28": [0, 0], "2.28-2.40": [0, 0], "2.40-2.46": [0, 0], "2.46-2.50": [0, 0]}
        zsky = {}
        for z in zs:
            for i in range(-250, 251):
                s = 0.01 * i
                o = Vector((math.sin(a) * 12.0, -math.cos(a) * 12.0, z)) + side * s
                hit = T.ray_cast(o, d, 30.0)
                sky = hit[0] is None
                aS = abs(s)
                k = ("|s|<2.28" if aS < 2.28 else "2.28-2.40" if aS < 2.40 else "2.40-2.46" if aS < 2.46
                     else "2.46-2.50")
                bands[k][0] += 1
                if sky:
                    bands[k][1] += 1
                    zsky.setdefault(k, set()).add(round(z, 2))
        print("SKY az %4d  " % az + "  ".join("%s: %d/%d" % (k, v[1], v[0]) for k, v in bands.items()), flush=True)
        for k, zz in zsky.items():
            print("        sky z in band %s: %.2f..%.2f (%d levels)" % (k, min(zz), max(zz), len(zz)), flush=True)
    sys.exit(0)

SHOTS = {
    # crown on the drum: bed, rim ring, bearers, dragon beams, struts, pads
    "j01_floor_sandwich_level_front": (P(0, 16.0, 8.95), P(0, 0.0, 8.95), 85),
    "j02_floor_sandwich_level_side": (P(90, 16.0, 9.05), P(90, 0.0, 9.05), 85),
    "j03_floor_sandwich_level_az45": (P(45, 16.0, 8.90), P(45, 0.0, 8.90), 85),
    "j04_rim_ring_bearer_on_cornice_az40": (P(28, 4.6, 8.35), P(40, 2.40, 8.85), 40),
    "j05_rim_ring_under_joists_az90_close": (P(75, 4.2, 8.55), P(90, 2.35, 9.02), 40),
    "j06_dragon_beam_strut_head_az45": (P(28, 6.2, 8.1), P(45, 3.45, 8.85), 50),
    "j07_strut_foot_pad_az-135": (P(-118, 4.6, 6.9), P(-135, 2.3, 7.4), 45),
    "j08_underfloor_from_ground": (P(-20, 3.6, 1.7), P(0, 0.4, 9.0), 24),
    "j09_bed_from_above_corner": (P(-45, 5.6, 12.4), P(-45, 2.45, 8.9), 40),
    "j10_bed_from_above_az-20_outside_eave": (P(-20, 6.8, 11.0), P(-35, 2.45, 8.95), 45),
    # cabin body: floor edge / sill, corner post, openings, head beam to plate, ceiling
    "j11_sill_on_floor_edge_raking": (P(-52, 6.2, 9.5), P(0, 2.7, 9.35), 60),
    "j12_cabin_corner_post": (P(-45, 6.8, 10.3), P(-45, 3.76, 10.3), 50),
    "j13_through_openings_level": (P(0, 14.0, 10.75), P(0, 0.0, 10.75), 70),
    "j14_head_beam_into_plate_raking": (P(-25, 5.0, 11.0), P(-10, 2.66, 11.45), 55),
    "j15_ceiling_and_plate_inside": (P(-12, 3.9, 10.75), P(8, -0.8, 11.45), 26),
    # roof module: plate / rafter tails / soffit, hips, saddle end, eave silhouette, cap, finial, bell-cast profile
    "j16_eave_corner_hip_below": (P(-28, 8.5, 9.6), P(-45, 4.3, 11.0), 60),
    "j17_saddle_eave_end_close": (P(-60, 6.2, 11.6), P(-45, 4.50, 11.32), 60),
    "j18_hip_from_crane": (P(-45, 10.0, 15.5), P(-45, 2.2, 13.0), 50),
    "j19_saddle_into_lead_cap_crane": (P(-30, 4.5, 16.2), Vector((0, 0, 14.9)), 55),
    "j20_eave_hip_silhouette_aerial": (P(-10, 7.5, 17.0), P(-45, 3.6, 11.4), 50),
    "j21_apex_cap_from_ground": (P(-20, 18.0, 2.0), Vector((0, 0, 15.2)), 135),
    "j22_roof_elevation_face_on_az0": (P(0, 40.0, 13.2), Vector((0, 0, 13.2)), 120),
    "j23_roof_elevation_hip_on_az45": (P(45, 40.0, 13.2), Vector((0, 0, 13.2)), 120),
    # drum: string course, slits, door, step, footing (unchanged modules, re-checked)
    "j24_string_course_az90": (P(70, 4.6, 5.25), P(90, 2.3, 5.47), 50),
    "j25_slit1_az60": (P(60, 4.2, 3.0), P(60, 2.4, 2.95), 45),
    "j26_slit3_az180": (P(180, 4.2, 6.55), P(180, 2.3, 6.6), 45),
    "j27_door_step_threshold": (P(-18, 3.4, 1.0), P(0, 2.4, 0.35), 35),
    "j28_door_step_from_side_az90": (P(80, 5.5, 0.5), P(0, 2.6, 0.08), 50),
    "j29_back_footing": (P(160, 4.0, 0.8), P(160, 2.5, 0.12), 40),
    # reads
    "j30_thumbnail_45m_az30": (P(30, 45.0, 8.0), Vector((0, 0, 8.4)), 50),
    "j31_neighbour_eye_az120": (P(120, 11.0, 9.6), P(120, 2.4, 10.0), 40),
    # the north end of the floor sandwich from +X, level, telephoto (near-parallel rays: the 'sky' slot at y ~2.45)
    "j33_tele_80m_level_az90_north_edge": (P(90, 80.0, 9.04) + Vector((0, 2.45, 0)), Vector((0, 2.45, 9.04)), 600),
    "j34_tele_80m_level_az90_crown": (P(90, 80.0, 9.6), Vector((0, 0, 9.6)), 300),
    # the eave corner seen from above (the dark triangles in j09) and from outside at eave level
    "j35_eave_corner_from_above_close": (P(-45, 5.0, 12.6), P(-45, 4.35, 11.35), 40),
    "j36_eave_corner_outside_above": (P(-30, 7.2, 12.9), P(-45, 4.40, 11.40), 55),
    "j37_eave_corner_level_az-45": (P(-45, 9.0, 11.35), P(-45, 4.4, 11.35), 70),
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
