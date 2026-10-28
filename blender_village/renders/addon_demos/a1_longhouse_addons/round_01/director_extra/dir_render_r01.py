"""Director round-1 close-ups for a1_longhouse_addons (lean-to + porch on the v3 longhouse demo; copied from
v7_cottage r1 dir_render_r01.py: clay, sun, 1.8 m figures).  Cameras in WORLD coordinates (after the recentre):
lean-to x -3.294..0.706, host north face y 2.150, front y 4.350; porch centre x -2.394, south face y -3.050.
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
blend, out = argv[0], argv[1]
only = argv[2:]
SX, SY = 0.0, 0.0
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
for (x, y) in ((-0.9, -4.6), (0.3, 5.3)):
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

# world: lean-to LX -1.294 (x -3.294..0.706), host N face y 2.150, lean-to front y 4.350, deck z 2.86 at the wall;
# porch PX -2.394, host S face y -3.050, front beam y -4.050, beam underside 2.32; host eave (deck at faces) 2.81
SHOTS = {
    # ---- interior volumes (red twin: any red = daylight into the volume) ----
    "i01_shed_up_to_crease": ((-0.7, 3.7, 0.9), (-1.294, 2.15, 2.75), 22, "red", False),
    "i02_shed_W_endwall_head": ((-0.3, 2.7, 1.5), (-3.0, 3.0, 2.5), 35, "red", False),
    "i03_shed_E_endwall_head": ((-2.3, 2.7, 1.5), (0.4, 3.0, 2.5), 35, "red", False),
    "i04_host_room_N_head_under_arch": ((-1.294, 0.0, 1.7), (-1.294, 1.7, 3.2), 18, "red", False),
    "i05_host_room_S_head_under_arch": ((-2.394, -0.9, 1.7), (-2.394, -2.6, 3.2), 18, "red", False),
    "i06_host_attic_N_lifted_eave": ((-1.294, 0.4, 3.7), (-1.294, 2.0, 3.3), 16, "red", False),
    "i07_host_attic_S_lifted_eave": ((-2.394, -0.6, 3.7), (-2.394, -2.6, 3.3), 16, "red", False),
    "i08_under_hood_up_to_crease": ((-2.394, -3.75, 1.55), (-2.394, -3.12, 2.95), 18, "red", False),
    # ---- exterior junctions (void twin) ----
    "x01_leanto_W_rake_endwall": ((-5.0, 5.0, 2.9), (-3.2, 2.9, 2.5), 40, "void", True),
    "x02_leanto_E_rake_endwall": ((2.4, 5.0, 2.9), (0.6, 2.9, 2.5), 40, "void", True),
    "x03_leanto_crease_from_above": ((-0.8, 5.0, 4.0), (-1.294, 2.2, 2.95), 40, "void", True),
    "x04_leanto_front_soffit": ((-2.2, 5.3, 1.25), (-1.6, 4.3, 2.15), 28, "void", True),
    "x05_porch_E_verge_vs_thatch": ((0.2, -4.6, 3.0), (-1.2, -3.3, 3.05), 40, "void", True),
    "x06_porch_W_verge_vs_thatch": ((-5.0, -4.6, 3.0), (-3.6, -3.3, 3.05), 40, "void", True),
    "x07_porch_top_gap": ((-2.394, -4.6, 4.2), (-2.394, -3.2, 3.0), 30, "void", True),
    "x08_porch_W_brace_foot": ((-4.4, -4.3, 1.5), (-3.45, -3.1, 1.85), 40, "void", True),
    "x09_porch_actor_approach": ((-3.6, -8.5, 1.6), (-2.394, -3.1, 2.3), 35, None, True),
    "x10_leanto_actor_approach": ((1.4, 9.0, 1.6), (-1.294, 3.0, 1.9), 35, None, True),
    "x11_thumb_back_NE": ((26.0, 34.0, 12.0), (-1.0, 0.0, 3.0), 50, None, False),
    "x12_thumb_front_SW": ((-28.0, -36.0, 13.0), (-1.0, 0.0, 3.0), 50, None, False),
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

