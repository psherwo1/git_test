"""Director round-1 close-ups for v7_cottage (adapted from v6_barn dir_render_r03.py: clay, sun, 1.8 m figures).
Twins:
  _red  = black override + red world, no ground / figures / sun: see-through (red = sky through the building).
  _void = front faces black, BACK faces emissive yellow, red world: a slot into a hollow shows yellow, see-through red.
Interior shots (i..) put the camera INSIDE a closed volume (attic, wing attic, dormer, room) with the red twin:
any red pixel there is daylight entering the volume (a fog beam in UE).
Cameras in PLAN coordinates (the recipe's), moved by the build's recentre shift (-0.418, +2.587).
python -I dir_render_r01.py <blend> <out_dir> [only_prefix ...]    (or blender -b --python ... -- <args>)"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])  # r05: absolute BEFORE open_mainfile
only = argv[2:]
SX, SY = -0.418, 2.587
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
for (x, y) in ((-3.0, -4.3), (6.6, -2.0)):
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

# plan: main x -5..5, y -2.75..2.75 (ridge y 0, ~6.4); wing x -0.9..3.9, y -8..-2.75 (ridge x 1.5);
# dormer x -3.0, front y -2.4, wall_z 4.69, ridge 5.46, back y -0.86; chimney (5.3, 0), shoulder 4.7, head ~7.2
SHOTS = {
    # ---- interior volumes (red twin only matters) ----
    "i01_attic_to_W_valley": ((-2.6, 1.2, 4.1), (0.2, -2.6, 3.7), 14, "red", False),
    "i02_attic_to_E_valley": ((4.0, 1.2, 4.1), (2.8, -2.6, 3.7), 14, "red", False),
    "i03_wing_attic_up_to_main": ((1.5, -7.0, 3.5), (1.5, -2.0, 4.8), 14, "red", False),
    "i04_attic_to_dormer": ((-3.0, 0.6, 4.5), (-3.0, -2.2, 4.6), 16, "red", False),
    "i05_dormer_back_from_attic_above": ((-1.6, -0.2, 5.2), (-3.0, -1.2, 5.0), 16, "red", False),
    "i06_attic_to_chimney_gable": ((1.5, 0.0, 4.0), (5.0, 0.0, 4.6), 14, "red", False),
    "i07_room_W_inside_corner_head": ((0.6, -1.6, 2.0), (-0.9, -2.75, 2.85), 16, "red", False),
    "i08_room_E_inside_corner_head": ((2.4, -1.6, 2.0), (3.9, -2.75, 2.85), 16, "red", False),
    # ---- exterior junctions (void twin) ----
    "x01_dormer_back_oblique_W": ((-5.4, -3.2, 7.2), (-3.0, -0.9, 5.5), 55, "void", True),
    "x02_dormer_back_oblique_E": ((-0.6, -3.2, 7.2), (-3.0, -0.9, 5.5), 55, "void", True),
    "x03_dormer_cheek_foot_E": ((-1.3, -4.4, 4.6), (-2.35, -2.0, 4.0), 45, "void", True),
    "x04_dormer_mid_far": ((-4.0, -16.0, 4.0), (-3.0, -2.0, 4.9), 70, "void", True),
    "x05_W_inside_corner_soffit": ((-2.2, -4.3, 1.65), (-0.9, -2.75, 2.95), 32, "void", True),
    "x06_E_inside_corner_soffit": ((5.2, -4.3, 1.65), (3.9, -2.75, 2.95), 32, "void", True),
    "x07_W_valley_foot_mid": ((-3.2, -6.2, 4.6), (-0.9, -2.8, 3.3), 45, "void", True),
    "x08_wing_ridge_notch": ((1.5, -5.6, 7.1), (1.5, -1.6, 5.9), 60, "void", True),
    "x09_chimney_S_verge_into_stack": ((8.2, -3.6, 5.2), (5.0, -0.9, 5.7), 45, "void", True),
    "x10_chimney_N_verge_into_stack": ((8.2, 3.6, 5.2), (5.0, 0.9, 5.7), 45, "void", True),
    "x11_chimney_base_wall_crevice_S": ((7.2, -2.6, 2.0), (5.0, -0.9, 2.6), 35, "void", True),
    "x12_chimney_shoulder_side": ((9.0, -0.6, 4.6), (5.3, 0.0, 4.9), 50, "void", True),
    "x13_door_eave_actor": ((-4.6, -6.0, 1.6), (-3.0, -2.75, 2.2), 28, None, True),
    "x14_thumb_SW": ((-30.0, -36.0, 14.0), (0.0, -2.0, 3.5), 50, None, False),
    "x15_thumb_NE": ((30.0, 34.0, 13.0), (0.0, -2.0, 3.5), 50, None, False),
}


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
    interior = name.startswith("i")
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
