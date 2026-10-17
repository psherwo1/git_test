"""Director close-ups of every module junction, v1_stone_watchtower round 5 (same clay / sun / world as render_review).
python dir_render_r05.py <blend> <out_dir> [names|all|probe|sky|hyg] [samples]
'probe' prints junction contact measurements (BVH overlap + nearest distance) and renders nothing.
'sky'   level rays through the crown-to-drum floor sandwich (z 8.70-9.19, 5 mm) from 16 azimuths over |s| <= 2.75 m
        (the full cornice plus the cantilever band), counted per lateral band.
'hyg'   mesh hygiene of every WATCH_ mesh (zero-area, slivers, non-manifold, boundary edges)."""
import math
import os
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend, out = sys.argv[1], os.path.abspath(sys.argv[2])
arg = sys.argv[3] if len(sys.argv) > 3 else "all"
only = None if arg in ("", "all", "probe", "sky", "hyg") else set(arg.split(","))
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


if arg == "hyg":
    for ob in sorted((o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("WATCH_")
                      and o.data.users == 1), key=lambda o: o.name):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        z0 = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
        sl = 0
        for f in bm.faces:
            a = f.calc_area()
            mx = max((e.calc_length() for e in f.edges), default=0)
            if mx > 0 and 2 * a / mx < 1e-4:
                sl += 1
        nm = sum(1 for e in bm.edges if not e.is_manifold)
        bnd = sum(1 for e in bm.edges if e.is_boundary)
        me = ob.data
        ca = me.color_attributes.get("Mask")
        print("HYG %-26s faces %7d area<1e-8 %4d slivers %4d nonmanifold %6d boundary %6d  Mask %s/%s act %s def %s"
              "  uv %d  ident %s" % (
                  ob.name, len(bm.faces), z0, sl, nm, bnd, ca.domain if ca else None, ca.data_type if ca else None,
                  me.color_attributes.active_color_name, me.color_attributes.default_color_name, len(me.uv_layers),
                  ob.matrix_world.is_identity if hasattr(ob.matrix_world, "is_identity") else
                  (tuple(ob.location) == (0, 0, 0))), flush=True)
        bm.free()
    sys.exit(0)

if arg == "probe":
    pairs = [("WATCH_cabin_struts", "WATCH_cabin_corbels"), ("WATCH_cabin_struts", "WATCH_cabin_floor"),
             ("WATCH_cabin_corbels", "WATCH_base_stones"), ("WATCH_cabin_corbels", "WATCH_base_mortar"),
             ("WATCH_cabin_corbels", "WATCH_wall_core"),
             ("WATCH_cabin_floor", "WATCH_base_dressed"),
             ("WATCH_cabin_frame", "WATCH_cabin_floor"), ("WATCH_cabin_boards", "WATCH_cabin_frame"),
             ("WATCH_cabin_roof_frame", "WATCH_cabin_frame"), ("WATCH_cabin_roof_deck", "WATCH_cabin_roof_frame"),
             ("WATCH_cabin_roof_deck", "WATCH_cabin_frame"),
             ("WATCH_cabin_ceiling", "WATCH_cabin_frame"),
             ("WATCH_cabin_shingles", "WATCH_cabin_roof_deck"), ("WATCH_cabin_hips", "WATCH_cabin_shingles"),
             ("WATCH_cabin_hips", "WATCH_cabin_roof_deck"), ("WATCH_cabin_hips", "WATCH_cabin_roof_frame"),
             ("WATCH_cabin_lead", "WATCH_cabin_shingles"), ("WATCH_cabin_lead", "WATCH_cabin_hips"),
             ("WATCH_cabin_finial", "WATCH_cabin_lead"),
             ("WATCH_door_step", "WATCH_base_stones"), ("WATCH_door_step", "WATCH_door_surround"),
             ("WATCH_ceiling", "WATCH_wall_core"), ("WATCH_base_dressed", "WATCH_base_stones")]
    for a, b in pairs:
        ta, Va = bvh(a)
        tb, Vb = bvh(b)
        if ta is None or tb is None:
            print("PROBE", a, b, "missing")
            continue
        ov = len(ta.overlap(tb))
        dmin = min((tb.find_nearest(v)[3] for v in Va), default=-1)
        print("PROBE %-26s -> %-24s overlaps %6d  nearest-vertex %.4f m" % (a, b, ov, dmin), flush=True)
    # the curb + end blocks: cabin_floor vertices between z 8.68 and 9.20 and r 2.20..2.70
    ob = bpy.data.objects["WATCH_cabin_floor"]
    V, F = mesh_data(ob)
    cb = [v for v in V if 8.68 <= v.z <= 9.20 and 2.20 <= math.hypot(v.x, v.y) <= 2.47]
    if cb:
        print("CURB verts %d  r %.3f..%.3f  z %.3f..%.3f" % (
            len(cb), min(math.hypot(v.x, v.y) for v in cb), max(math.hypot(v.x, v.y) for v in cb),
            min(v.z for v in cb), max(v.z for v in cb)))
    # saddle ends: hips vertices below z 11.45 near the four corners
    ob = bpy.data.objects["WATCH_cabin_hips"]
    V, F = mesh_data(ob)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pts = [v for v in V if v.x * sx > 2.6 and v.y * sy > 2.6]
            if pts:
                print("SADDLE corner (%+d,%+d): verts %d  z %.3f..%.3f  max plan reach %.3f" % (
                    sx, sy, len(pts), min(v.z for v in pts), max(v.z for v in pts),
                    max(max(abs(v.x), abs(v.y)) for v in pts)))
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
    print("SKY bvh faces", len(allF), flush=True)
    zs = [8.700 + 0.005 * i for i in range(0, 99)]          # 8.700 .. 9.190 (cornice top to deck top), 5 mm
    tot = 0
    for k16 in range(16):
        az = k16 * 22.5
        a = math.radians(az)
        d = Vector((-math.sin(a), math.cos(a), 0.0))
        side = Vector((math.cos(a), math.sin(a), 0.0))
        bands = {"|s|<2.28": [0, 0], "2.28-2.46": [0, 0], "2.46-2.51": [0, 0], "2.51-2.75": [0, 0]}
        zsky = {}
        for z in zs:
            for i in range(-550, 551):
                s = 0.005 * i
                o = Vector((math.sin(a) * 12.0, -math.cos(a) * 12.0, z)) + side * s
                hit = T.ray_cast(o, d, 30.0)
                aS = abs(s)
                k = ("|s|<2.28" if aS < 2.28 else "2.28-2.46" if aS < 2.46 else "2.46-2.51" if aS < 2.51
                     else "2.51-2.75")
                bands[k][0] += 1
                if hit[0] is None:
                    bands[k][1] += 1
                    zsky.setdefault(k, []).append((round(s, 3), round(z, 3)))
        tot += sum(v[1] for kk, v in bands.items() if kk != "2.51-2.75")
        print("SKY az %6.1f  " % az + "  ".join("%s: %d/%d" % (k, v[1], v[0]) for k, v in bands.items()), flush=True)
        for k, pts in zsky.items():
            print("        band %s: %d sky rays, e.g. %s" % (k, len(pts), pts[:4]), flush=True)
    print("SKY TOTAL within |s|<2.51: %d" % tot)
    sys.exit(0)

SHOTS = {
    # crown on the drum: bed curb, end blocks, bearers, dragon beams, struts, pads
    "j01_floor_sandwich_level_front": (P(0, 16.0, 8.95), P(0, 0.0, 8.95), 85),
    "j02_floor_sandwich_level_side": (P(90, 16.0, 9.05), P(90, 0.0, 9.05), 85),
    "j03_floor_sandwich_level_az45": (P(45, 16.0, 8.90), P(45, 0.0, 8.90), 85),
    "j04_curb_bearer_on_cornice_az40": (P(28, 4.6, 8.35), P(40, 2.40, 8.85), 40),
    "j05_curb_under_joists_az90_close": (P(75, 4.2, 8.55), P(90, 2.35, 9.02), 40),
    "j06_dragon_beam_strut_head_az45": (P(28, 6.2, 8.1), P(45, 3.45, 8.85), 50),
    "j07_strut_foot_pad_az-135": (P(-118, 4.6, 6.9), P(-135, 2.3, 7.4), 45),
    "j08_underfloor_from_ground": (P(-20, 3.6, 1.7), P(0, 0.4, 9.0), 24),
    "j09_bed_from_above_corner": (P(-45, 5.6, 12.4), P(-45, 2.45, 8.9), 40),
    "j10_bed_from_above_az-20_outside_eave": (P(-20, 6.8, 11.0), P(-35, 2.45, 8.95), 45),
    "j38_end_blocks_+X_north_close": (P(90, 4.6, 8.75) + Vector((0, 2.2, 0)), Vector((1.6, 2.45, 9.03)), 45),
    "j39_end_blocks_-X_south_close": (P(270, 4.6, 8.75) + Vector((0, -2.2, 0)), Vector((-1.6, -2.45, 9.03)), 45),
    "j40_end_block_centre_bearer_+Y": (P(170, 4.4, 8.6), Vector((0.0, 2.45, 9.03)), 45),
    "j41_curb_facets_from_below_az-60": (P(-60, 3.4, 7.6), P(-60, 2.4, 8.85), 30),
    # cabin body: floor edge / sill, corner post, openings, head beam to plate, ceiling
    "j11_sill_on_floor_edge_raking": (P(-52, 6.2, 9.5), P(0, 2.7, 9.35), 60),
    "j12_cabin_corner_post": (P(-45, 6.8, 10.3), P(-45, 3.76, 10.3), 50),
    "j13_through_openings_level": (P(0, 14.0, 10.75), P(0, 0.0, 10.75), 70),
    "j14_head_beam_into_plate_raking": (P(-25, 5.0, 11.0), P(-10, 2.66, 11.45), 55),
    "j15_ceiling_and_plate_inside": (P(-12, 3.9, 10.75), P(8, -0.8, 11.45), 26),
    # roof module: plate / rafter tails / soffit, hips, saddle ends at all four corners, cap, finial
    "j16_eave_corner_hip_below": (P(-28, 8.5, 9.6), P(-45, 4.3, 11.0), 60),
    "j17_saddle_eave_end_close": (P(-60, 6.2, 11.6), P(-45, 4.50, 11.32), 60),
    "j18_hip_from_crane": (P(-45, 10.0, 15.5), P(-45, 2.2, 13.0), 50),
    "j19_saddle_into_lead_cap_crane": (P(-30, 4.5, 16.2), Vector((0, 0, 14.9)), 55),
    "j20_eave_hip_silhouette_aerial": (P(-10, 7.5, 17.0), P(-45, 3.6, 11.4), 50),
    "j21_apex_cap_from_ground": (P(-20, 18.0, 2.0), Vector((0, 0, 15.2)), 135),
    "j22_roof_elevation_face_on_az0": (P(0, 40.0, 13.2), Vector((0, 0, 13.2)), 120),
    "j23_roof_elevation_hip_on_az45": (P(45, 40.0, 13.2), Vector((0, 0, 13.2)), 120),
    "j35_saddle_end_level_az45": (P(45, 9.0, 11.35), P(45, 4.4, 11.35), 70),
    "j36_saddle_end_level_az135": (P(135, 9.0, 11.35), P(135, 4.4, 11.35), 70),
    "j37_saddle_end_level_az-135": (P(-135, 9.0, 11.35), P(-135, 4.4, 11.35), 70),
    "j42_saddle_end_level_az-45": (P(-45, 9.0, 11.35), P(-45, 4.4, 11.35), 70),
    "j43_saddle_end_side_raking_az-30": (P(-30, 6.0, 11.25), P(-45, 4.45, 11.30), 70),
    "j44_saddle_end_from_below": (P(-45, 5.6, 9.6), P(-45, 4.45, 11.25), 45),
    "j45_hip_tuck_mid_slope_close": (P(-25, 5.2, 13.6), P(-45, 3.0, 12.9), 55),
    "j46_saddle_end_from_above_close": (P(-45, 5.2, 12.6), P(-45, 4.35, 11.35), 40),
    # drum: string course, slits, door, step, footing, and the note-15 tmpl_lod seam at z 4.0 m / entrance zone
    "j24_string_course_az90": (P(70, 4.6, 5.25), P(90, 2.3, 5.47), 50),
    "j25_slit1_az60": (P(60, 4.2, 3.0), P(60, 2.4, 2.95), 45),
    "j26_slit3_az180": (P(180, 4.2, 6.55), P(180, 2.3, 6.6), 45),
    "j27_door_step_threshold": (P(-18, 3.4, 1.0), P(0, 2.4, 0.35), 35),
    "j28_door_step_from_side_az90": (P(80, 5.5, 0.5), P(0, 2.6, 0.08), 50),
    "j29_back_footing": (P(160, 4.0, 0.8), P(160, 2.5, 0.12), 40),
    "j47_lod_seam_z4_grazing_az100": (P(60, 4.2, 4.0), P(100, 2.4, 4.0), 40),
    "j48_lod_seam_z4_face_on_az140": (P(140, 5.5, 4.0), P(140, 2.4, 4.0), 40),
    "j49_lod_entrance_zone_edge_az-35": (P(-50, 4.6, 2.6), P(-30, 2.4, 2.9), 40),
    "j50_lod_seam_mid_shot_az120": (P(120, 12.0, 3.5), P(120, 0.0, 4.3), 40),
    # reads
    "j30_thumbnail_45m_az30": (P(30, 45.0, 8.0), Vector((0, 0, 8.4)), 50),
    "j31_neighbour_eye_az120": (P(120, 11.0, 9.6), P(120, 2.4, 10.0), 40),
    "j33_tele_80m_level_az90_north_edge": (P(90, 80.0, 9.04) + Vector((0, 2.45, 0)), Vector((0, 2.45, 9.04)), 600),
    "j34_tele_80m_level_az90_crown": (P(90, 80.0, 9.6), Vector((0, 0, 9.6)), 300),
    "j51_tele_80m_level_az270_south_edge": (P(270, 80.0, 9.04) + Vector((0, -2.45, 0)), Vector((0, -2.45, 9.04)),
                                            600),
    "j52_tele_80m_level_az0_east_edge": (P(0, 80.0, 9.04) + Vector((2.45, 0, 0)), Vector((2.45, 0, 9.04)), 600),
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
