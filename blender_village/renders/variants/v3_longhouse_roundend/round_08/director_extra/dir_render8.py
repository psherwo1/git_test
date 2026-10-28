"""Director round-8 probe + junction close-ups for v3_longhouse_roundend (gable roof abutting a round wall).
python -I dir_render8.py -- <blend> <out_dir> [probe_only]"""
import bpy, sys, os, math, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, out = argv[0], argv[1]
probe_only = len(argv) > 2 and argv[2] == "probe_only"
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

meshes = [o for o in scn.objects if o.type == "MESH"]
for o in meshes:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]
    mx = [max(v[i] for v in bb) for i in range(3)]
    print("OBJ %-34s polys %7d  min %s  max %s" % (o.name, len(o.data.polygons),
          tuple(round(x, 2) for x in mn), tuple(round(x, 2) for x in mx)))
rw = [o for o in meshes if "round_wall" in o.name and "frame" not in o.name]
bb = [rw[0].matrix_world @ Vector(c) for c in rw[0].bound_box]
CX = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
CY = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
print("ROUND CENTRE", rw[0].name, round(CX, 3), round(CY, 3))

# ---- floating-island probe on junction pieces --------------------------------------------------------------
bvh = {}
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bvh[o.name] = BVHTree.FromBMesh(bm); bm.free()
keys = ("abut", "flaunch", "apron", "fillet", "lead", "junction", "ridge", "comb", "eave_roll", "roll")
for o in meshes:
    if not any(k in o.name.lower() for k in keys):
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bm.verts.ensure_lookup_table()
    seen = set(); islands = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; isl = []; seen.add(v.index)
        while stack:
            w = stack.pop(); isl.append(w.co.copy())
            for e in w.link_edges:
                u = e.other_vert(w)
                if u.index not in seen:
                    seen.add(u.index); stack.append(u)
        islands.append(isl)
    worst = []
    for isl in islands:
        step = max(1, len(isl) // 60)
        best = 1e9
        for p in isl[::step]:
            for n, t in bvh.items():
                if n == o.name:
                    continue
                r = t.find_nearest(p, 0.5)
                if r[0] is not None:
                    best = min(best, r[3])
            if best < 0.005:
                break
        if best > 0.01:
            c = sum(isl, Vector()) / len(isl)
            worst.append((best, tuple(round(x, 2) for x in c), len(isl)))
    worst.sort(reverse=True)
    print("ISLANDS %-30s n=%5d  floating>1cm: %d  %s" % (o.name, len(islands), len(worst),
          [(round(b * 100, 1), c, n) for b, c, n in worst[:6]]))
    bm.free()
if probe_only:
    sys.exit(0)

C = (CX, CY)
def P(dx, dy, z):
    return (C[0] + dx, C[1] + dy, z)
S_E, N_E, RID = P(-1.99, -3.05, 2.4), P(-1.99, 3.05, 2.4), P(-3.55, 0.0, 5.2)
SHOTS = {
    "j01_s_eave_end_west_eye": (P(-4.5, -5.6, 1.65), S_E, 40, True),
    "j02_s_eave_end_east_eye": (P(1.2, -6.2, 1.65), S_E, 50, True),
    "j03_n_eave_end_west_eye": (P(-4.5, 5.6, 1.65), N_E, 40, True),
    "j04_n_eave_end_east_eye": (P(1.2, 6.2, 1.65), N_E, 50, True),
    "j05_s_eave_end_tele": (P(-3.2, -7.5, 2.0), S_E, 120, True),
    "j06_n_eave_end_tele": (P(-3.2, 7.5, 2.0), N_E, 120, True),
    "j07_s_soffit_lookup": (P(-2.7, -4.2, 1.4), P(-2.0, -3.0, 2.55), 28, True),
    "j08_n_soffit_lookup": (P(-2.7, 4.2, 1.4), P(-2.0, 3.0, 2.55), 28, True),
    "j09_s_slope_crane": (P(-7.0, -9.0, 7.5), P(-2.8, -1.5, 3.9), 50, True),
    "j10_n_slope_crane": (P(-7.0, 9.0, 7.5), P(-2.8, 1.5, 3.9), 50, True),
    "j11_ridge_into_drum": (P(-9.5, 0.8, 6.6), RID, 70, True),
    "j12_ridge_tele_s_crane": (P(-5.5, -5.5, 7.8), P(-3.55, 0, 5.3), 100, True),
    "j13_s_flaunch_tele": (P(-4.2, -8.0, 4.6), P(-2.9, -1.8, 3.9), 110, True),
    "j14_n_flaunch_tele": (P(-4.2, 8.0, 4.6), P(-2.9, 1.8, 3.9), 110, True),
    "j15_junction_top_down": (P(-2.6, -0.01, 15.0), P(-2.6, 0.0, 4.0), 35, True),
    "j16_drum_over_roof_n_crane": (P(-6.0, 7.5, 8.5), P(-2.5, 1.2, 5.5), 55, True),
    "j17_cone_eave_lookup_e": (P(5.6, -1.0, 1.6), P(3.9, 0.0, 5.9), 28, True),
    "j18_drum_eye_figure_s": (P(1.5, -12.0, 1.65), P(0.0, 0.0, 4.0), 35, False),
    "j19_drum_ene_upper_win": (P(7.5, 3.5, 4.0), P(0.0, 0.0, 4.0), 45, False),
    "j20_drum_se_upper_win": (P(6.0, -6.5, 4.0), P(0.0, 0.0, 4.0), 45, False),
    "j21_gap_above_ridge_w_eye": (P(-14.0, -0.4, 1.65), P(-3.0, 0.0, 5.6), 85, True),
}

clay = bpy.data.materials.new("_DIR_clay"); clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1); b.inputs["Roughness"].default_value = 0.65
black = bpy.data.materials.new("_DIR_black"); black.use_nodes = True
bb2 = black.node_tree.nodes.get("Principled BSDF")
bb2.inputs["Base Color"].default_value = (0, 0, 0, 1); bb2.inputs["Roughness"].default_value = 1.0
bb2.inputs["Specular IOR Level"].default_value = 0.0
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.002)); ground = bpy.context.object
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.8, location=(C[0] + 1.0, C[1] - 4.6, 0.9)); fig = bpy.context.object
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
except Exception as e:
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device)
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

def shoot(name, loc, tgt, lens, red):
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    ground.hide_render = False; sun.hide_render = False; fig.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1); bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24; scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png"); bpy.ops.render.render(write_still=True)
    if red:
        scn.view_layers[0].material_override = black
        ground.hide_render = True; sun.hide_render = True; fig.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1); bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4; scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(out, name + "_red.png"); bpy.ops.render.render(write_still=True)

for name, (loc, tgt, lens, red) in SHOTS.items():
    shoot(name, loc, tgt, lens, red)
    print("SHOT", name, flush=True)
