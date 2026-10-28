"""DIRECTOR round 5 (copied from dir_render_r04.py; every r4 shot + d21-d30 / di18-di23)."""
"""Director round-2 close-ups for v7_cottage (copied from round_01 dir_render_r01.py; r01 shots kept + new add-on
junction shots x17-x24 and the ring-stack interior i09 / i10 run on the FAST ring_stack blend with the `r` prefix).
Twins:
  _red  = black override + red world, no ground / figures / sun: see-through (red = sky through the building).
  _void = front faces black, BACK faces emissive yellow, red world: a slot into a hollow shows yellow, see-through red.
Interior shots (i..) put the camera INSIDE a closed volume (attic, wing attic, dormer, room) with the red twin:
any red pixel there is daylight entering the volume (a fog beam in UE).
Cameras in PLAN coordinates (the recipe's), moved by the build's recentre shift (-0.418, +2.587).
python -I dir_render_r01.py <blend> <out_dir> [only_prefix ...]    (or blender -b --python ... -- <args>)
ROUND 4 (builder, copied from round_03 b_render_r03.py): the shots moved to the round-4 plan (main 11 m with two
round hips, wing at x 1.0 with a round S hip, eyebrow on the back slope, chimney through the E hip) + new hip /
eyebrow / chimney-ring shots (h.., e.., c..).  The recentre shift comes from the env COTT_SHIFT="sx,sy"."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])   # director r04: absolute BEFORE open_mainfile
# (opening the blend changes the relative-path base: a relative out dir lands under C:\ -- the C:\round_03 strays)
only = argv[2:]
SX, SY = (float(v) for v in os.environ.get("COTT_SHIFT", "0,0").split(","))
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_D_clay", (0.42, 0.41, 0.39))
black = mat("_D_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
void = bpy.data.materials.new("_D_void")
void.use_nodes = True
nt = void.node_tree
nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial")
geo = nt.nodes.new("ShaderNodeNewGeometry")
mix = nt.nodes.new("ShaderNodeMixShader")
e0 = nt.nodes.new("ShaderNodeEmission")
e0.inputs["Color"].default_value = (0, 0, 0, 1)
e1 = nt.nodes.new("ShaderNodeEmission")
e1.inputs["Color"].default_value = (1.0, 0.85, 0.0, 1)
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
nt.links.new(e0.outputs[0], mix.inputs[1])
nt.links.new(e1.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], o_.inputs["Surface"])

aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.01))
gr = bpy.context.object
gr.scale = (300, 300, 1)
aux.append(gr)
for (x, y) in ((-3.1, -4.4), (7.2, -4.2)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x + SX, y + SY, 0.775))
    aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x + SX, y + SY, 1.67))
    aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_D_world")
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
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device)
scn.render.image_settings.file_format = "PNG"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02

# round-4 plan: main x -5.5..5.5, y -2.75..2.75, ridge y 0 ~6.25 over x -4.18..4.18, round hips to the noses x +-7.38;
# wing x -1.4..3.4, y -8..-2.75 (ridge x 1.0, hip centre y -6.76, nose y -9.61); dormer x -3.1; eyebrow x -0.8 on
# the back slope (front y 1.96, lip ~y 2.18, z ~4.5); chimney (5.65, 0) through the E hip, head ~7.1
SHOTS = {
    # ---- interior volumes (red twin only matters) ----
    "i01_attic_to_W_valley": ((-2.6, 1.2, 4.1), (-0.6, -2.6, 3.7), 14, "red", False),
    "i02_attic_to_E_valley": ((4.0, 1.2, 4.1), (2.6, -2.6, 3.7), 14, "red", False),
    "i03_wing_attic_up_to_main": ((1.0, -7.0, 3.5), (1.0, -2.0, 4.8), 14, "red", False),
    "i04_attic_to_dormer": ((-3.1, 0.6, 4.5), (-3.1, -2.2, 4.6), 16, "red", False),
    "i06_attic_to_E_hip_chimney": ((1.0, 0.0, 4.0), (5.2, 0.0, 4.4), 14, "red", False),
    "i07_room_W_inside_corner_head": ((0.1, -1.6, 2.0), (-1.4, -2.75, 2.85), 16, "red", False),
    "i08_room_E_inside_corner_head": ((1.9, -1.6, 2.0), (3.4, -2.75, 2.85), 16, "red", False),
    "i09_attic_to_W_hip": ((0.0, 0.0, 4.0), (-5.5, 0.0, 3.6), 14, "red", False),
    "i10_attic_to_eyebrow": ((-0.8, -0.6, 3.6), (-0.8, 2.0, 4.1), 16, "red", False),
    "i11_wing_attic_to_S_hip": ((1.0, -4.0, 3.4), (1.0, -8.5, 3.0), 14, "red", False),
    # ---- exterior junctions (void twin) ----
    "x04_dormer_mid_far": ((-4.0, -16.0, 4.0), (-3.1, -2.0, 4.9), 70, "void", True),
    "x05_W_inside_corner_soffit": ((-2.7, -4.3, 1.65), (-1.4, -2.75, 2.95), 32, "void", True),
    "x06_E_inside_corner_soffit": ((4.7, -4.3, 1.65), (3.4, -2.75, 2.95), 32, "void", True),
    "x07_W_valley_foot_mid": ((-3.7, -6.2, 4.6), (-1.4, -2.8, 3.3), 45, "void", True),
    "x08_wing_ridge_notch": ((1.0, -5.6, 7.1), (1.0, -1.6, 5.7), 60, "void", True),
    "x13_door_eave_actor": ((-4.7, -6.0, 1.6), (-3.1, -2.75, 2.2), 28, None, True),
    "x14_thumb_SW": ((-30.0, -36.0, 14.0), (0.0, -2.0, 3.5), 50, None, False),
    "x15_thumb_NE": ((30.0, 34.0, 13.0), (0.0, -2.0, 3.5), 50, None, False),
    "x17_E_valley_foot_mid": ((5.7, -6.2, 4.6), (3.4, -2.8, 3.3), 45, "void", True),
    "x19_dormer_hood_mid_eye": ((-3.1, -15.0, 1.7), (-3.1, -2.0, 5.2), 70, "void", True),
    "x22_E_corner_eye_wide": ((5.9, -7.2, 1.7), (3.4, -2.75, 2.8), 35, "void", True),
    "x24_wing_ridge_arch_side": ((4.1, -4.6, 7.0), (1.0, -1.9, 5.7), 55, "void", True),
    # ---- round 4: round hips, eyebrow, chimney through the hip ----
    "h01_E_hip_chimney_SE_eye": ((12.0, -8.0, 1.7), (5.5, 0.0, 4.0), 35, "void", True),
    "h02_W_hip_SW": ((-12.0, -7.0, 3.0), (-6.0, 0.0, 3.8), 35, "void", True),
    "h03_W_hip_soffit_eye": ((-9.0, -1.8, 1.6), (-6.3, 0.0, 2.8), 30, "void", True),
    "h04_W_hip_apex_dome": ((-6.8, -3.2, 7.8), (-4.2, 0.0, 6.2), 50, "void", True),
    "h05_wing_S_hip": ((1.0, -15.0, 3.0), (1.0, -8.5, 3.5), 40, "void", True),
    "h06_wing_S_hip_soffit_eye": ((3.8, -11.5, 1.6), (1.0, -9.0, 2.6), 30, "void", True),
    "c01_chimney_ring_SE": ((8.8, -2.6, 7.4), (5.65, 0.0, 5.4), 50, "void", True),
    "c02_chimney_ring_N": ((8.2, 3.4, 7.0), (5.65, 0.0, 5.2), 50, "void", True),
    "c03_chimney_base_under_hip": ((9.2, -2.2, 1.7), (6.0, 0.0, 3.0), 35, "void", True),
    "e01_eyebrow_back_eye": ((-0.8, 12.0, 1.7), (-0.8, 2.2, 4.3), 50, "void", True),
    "e02_eyebrow_oblique_NW": ((-3.9, 6.2, 5.8), (-0.8, 2.2, 4.4), 45, "void", True),
    "e03_eyebrow_lip_end_E": ((1.4, 5.0, 4.9), (0.45, 2.1, 4.1), 50, "void", True),
    "e04_eyebrow_from_above": ((-0.8, 6.8, 8.6), (-0.8, 2.0, 4.6), 45, "void", True),
}

# ---- DIRECTOR round 4 additions (d..): every add-on junction on the loaf roofs + extra interior volumes ----
SHOTS.update({
    "di05_dormer_back_from_attic_above": ((-1.6, -0.2, 5.2), (-3.1, -1.2, 5.0), 16, "red", False),
    "di12_attic_to_E_gablet_low": ((2.0, 0.8, 3.2), (5.5, -1.5, 2.7), 16, "red", False),
    "di13_attic_to_W_gablet_low": ((-2.0, -0.8, 3.2), (-5.5, 1.5, 2.7), 16, "red", False),
    "di14_wing_attic_to_S_gablet_low": ((1.0, -4.5, 3.2), (2.4, -8.0, 2.7), 16, "red", False),
    "di15_attic_to_eyebrow_side": ((0.8, 0.3, 3.6), (-1.6, 2.2, 4.2), 20, "red", False),
    "di16_attic_ridge_to_E_dome_stack": ((2.0, 0.0, 5.4), (5.0, 0.0, 5.9), 16, "red", False),
    "di17_attic_to_wing_ridge_join": ((1.0, 1.0, 4.6), (1.0, -2.5, 5.6), 16, "red", False),
    "d01_ridge_knob_from_N": ((1.0, 6.5, 8.2), (1.0, 0.0, 6.3), 45, "void", True),
    "d02_wing_ridge_join_above": ((-1.5, -4.5, 9.5), (1.0, -0.5, 6.2), 45, "void", True),
    "d03_W_corner_roll_eye_close": ((-2.8, -5.2, 1.7), (-1.4, -2.85, 2.95), 40, "void", True),
    "d04_W_inside_corner_standing": ((-2.3, -3.7, 1.7), (-1.4, -2.75, 2.8), 24, "void", True),
    "d05_dormer_back_oblique_W": ((-5.4, -3.2, 7.2), (-3.1, -0.9, 5.5), 55, "void", True),
    "d06_dormer_back_oblique_E": ((-0.6, -3.2, 7.2), (-3.1, -0.9, 5.5), 55, "void", True),
    "d07_dormer_apex_close": ((-3.1, -4.6, 6.2), (-3.1, -2.3, 5.5), 50, "void", True),
    "d08_dormer_cheek_foot_E": ((-1.8, -4.4, 4.6), (-2.45, -2.0, 4.0), 45, "void", True),
    "d09_eyebrow_lip_W_foot": ((-3.0, 5.0, 4.9), (-2.05, 2.1, 4.1), 50, "void", True),
    "d10_chimney_pot_head": ((8.3, -2.6, 8.1), (5.65, 0.0, 7.3), 55, "void", True),
    "d11_E_hip_nose_soffit_rafters": ((8.6, -3.6, 1.7), (6.8, -1.6, 2.8), 35, "void", True),
    "d12_wing_S_hip_SE_eye_wide": ((7.0, -14.0, 1.7), (1.0, -7.0, 3.8), 35, "void", True),
    "d13_E_corner_roll_above": ((5.1, -5.0, 5.0), (3.4, -2.75, 2.95), 40, "void", True),
    "d14_W_corner_roll_above": ((-3.1, -5.0, 5.0), (-1.4, -2.75, 2.95), 40, "void", True),
    "d15_W_hip_apex_dome_N": ((-6.8, 3.2, 7.8), (-4.2, 0.0, 6.2), 50, "void", True),
    "d16_E_hip_apex_and_stack": ((7.5, -2.5, 7.8), (4.2, 0.0, 6.2), 50, "void", True),
    "d17_eave_seam_under_wing": ((-0.2, -5.6, 1.5), (1.0, -2.9, 2.7), 30, "void", True),
    "d18_W_valley_foot_eye": ((-3.1, -7.8, 1.7), (-1.4, -2.9, 3.2), 50, "void", True),
    "d19_W_hip_gablet_eye": ((-9.5, 1.5, 1.4), (-5.5, 0.0, 3.0), 30, "void", True),
    "d20_N_hip_corner_NE_eye": ((9.0, 7.0, 1.7), (5.5, 2.75, 3.0), 35, "void", True),
})


# ---- DIRECTOR round 5 additions: the round-5 fixes (corner-roll blend cuffs, buried wing ridge end, dome bell, E
# gablet into the stack, the c01 chimney specks) + more interior see-through volumes ----
SHOTS.update({
    "d21_W_corner_roll_cuff_eye_W": ((-4.6, -4.4, 1.75), (-1.6, -2.95, 2.85), 40, "void", True),
    "d22_E_corner_roll_cuff_eye_E": ((6.4, -4.4, 1.75), (3.6, -2.95, 2.85), 40, "void", True),
    "d23_wing_ridge_buried_end_above": ((1.0, -4.2, 8.6), (1.0, -1.0, 6.2), 50, "void", True),
    "d24_wing_ridge_buried_end_W": ((-2.4, -2.2, 7.6), (1.0, -1.3, 6.0), 50, "void", True),
    "d25_E_dome_bell_S": ((5.6, -3.6, 7.6), (4.3, 0.0, 6.4), 55, "void", True),
    "d26_E_gablet_stack_S_eye": ((7.6, -1.9, 1.7), (5.5, -0.6, 2.8), 30, "void", True),
    "d27_E_gablet_stack_N_eye": ((7.6, 1.9, 1.7), (5.5, 0.6, 2.8), 30, "void", True),
    "d28_chimney_stones_SE_close": ((7.4, -1.8, 6.2), (5.65, 0.0, 5.2), 50, "void", True),
    "d29_dormer_valley_W_close": ((-4.9, -4.4, 5.6), (-3.75, -2.0, 4.6), 50, "void", True),
    "d30_W_valley_crest_close": ((-1.2, -4.6, 6.6), (-0.4, -2.4, 5.0), 50, "void", True),
    "di18_attic_to_E_stack_gablet_S": ((3.0, -1.0, 3.0), (5.45, -0.4, 2.7), 16, "red", False),
    "di19_attic_to_E_stack_gablet_N": ((3.0, 1.0, 3.0), (5.45, 0.4, 2.7), 16, "red", False),
    "di20_attic_to_W_corner_wallhead": ((-0.4, -1.4, 3.2), (-1.5, -2.9, 2.9), 16, "red", False),
    "di21_wing_attic_to_W_valley": ((1.0, -4.2, 3.4), (-1.2, -2.8, 3.8), 16, "red", False),
    "di22_wing_attic_to_E_valley": ((1.0, -4.2, 3.4), (3.2, -2.8, 3.8), 16, "red", False),
    "di23_attic_to_eyebrow_low": ((-0.8, 0.2, 3.1), (-0.8, 2.6, 3.4), 16, "red", False),
    # second pass: di12 / di18-di20 put the camera inside the attic floor's blocker solid (black clay); re-shot higher
    "dj18_attic_high_to_E_stack_gablet_S": ((3.2, -0.9, 3.9), (5.45, -0.45, 2.75), 16, "red", False),
    "dj19_attic_high_to_E_stack_gablet_N": ((3.2, 0.9, 3.9), (5.45, 0.45, 2.75), 16, "red", False),
    "dj20_attic_high_to_W_corner_wallhead": ((-0.2, -1.2, 3.9), (-1.45, -2.8, 2.9), 16, "red", False),
    "dj21_attic_high_to_E_corner_wallhead": ((2.2, -1.2, 3.9), (3.45, -2.8, 2.9), 16, "red", False),
})


def red_count(path):
    im = bpy.data.images.load(path)
    px = im.pixels[:]
    n = 0
    for i in range(0, len(px), 4):
        if px[i] > 0.5 and px[i + 1] < 0.2 and px[i + 2] < 0.2:
            n += 1
    yel = sum(1 for i in range(0, len(px), 4) if px[i] > 0.5 and px[i + 1] > 0.4 and px[i + 2] < 0.2)
    bpy.data.images.remove(im)
    return n, yel


def shoot(name, loc, tgt, lens, twin, show_aux):
    small = "thumb" in name
    scn.render.resolution_x, scn.render.resolution_y = (320, 180) if small else (1280, 720)
    cam.location = Vector((loc[0] + SX, loc[1] + SY, loc[2]))
    cam.data.lens = lens
    t = Vector((tgt[0] + SX, tgt[1] + SY, tgt[2]))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    interior = name.startswith("i") or name.startswith("ri")
    if not interior:
        scn.view_layers[0].material_override = clay
        for o in aux:
            o.hide_render = not show_aux and o is not gr
        gr.hide_render = False
        sun.hide_render = False
        scn.view_settings.view_transform = "AgX"
        bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
        bg.inputs["Strength"].default_value = 0.45
        scn.cycles.samples = 24
        scn.cycles.use_denoising = True
        scn.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
    else:
        # interior: a lit clay frame too (a lamp at the camera) so the volume can be read
        scn.view_layers[0].material_override = clay
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        bpy.ops.object.light_add(type="POINT", location=cam.location)
        lamp = bpy.context.object
        lamp.data.energy = 300.0
        scn.view_settings.view_transform = "AgX"
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1)
        bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 16
        scn.cycles.use_denoising = True
        scn.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(lamp, do_unlink=True)
    if twin:
        scn.view_layers[0].material_override = black if twin == "red" else void
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        scn.view_settings.view_transform = "Standard"
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1)
        bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4
        scn.cycles.use_denoising = False
        p = os.path.join(out, name + "_" + twin + ".png")
        scn.render.filepath = p
        bpy.ops.render.render(write_still=True)
        r, y = red_count(p)
        print("COUNT", name, twin, "red", r, "yellow", y, flush=True)


for name, (loc, tgt, lens, twin, show_aux) in SHOTS.items():
    if only and not any(name.startswith(p) for p in only):
        continue
    shoot(name, loc, tgt, lens, twin, show_aux)
    print("SHOT", name, flush=True)
