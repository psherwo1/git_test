"""BUILDER ROUND-3 copy of the director's round-2 close-ups (dir_render_r02.py): the round-3 build recentres by (+4.606, -0.303), i.e. SY = -0.05 against round 2, and the lean-to is 2.0 m deep (LF + 0.10).  Director ROUND-2 close-ups for a1_longhouse_addons (copy of round_01 dir_render_r01.py; round-2 world coordinates
from the build's recentre (+4.606, -0.253): lean-to centre x -1.594 (x -3.594..0.406, 1.9 m deep), host north face
y 2.347, front y 4.247; porch centre x -2.394, south face y -2.853, front beam y -3.853).  New in r02: i09, x13-x16.
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
SX, SY = 0.0, -0.05
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
LX, LY, LF = -1.594, 2.347, 4.347
PX, PY, PF = -2.394, -2.853, -3.853
for (x, y) in ((PX + 1.5, PY - 1.6), (LX + 1.6, LF + 1.2), (LX + 0.45, LF - 0.15)):
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

# round-2 world (see the doc): lean-to deck at the wall z ~3.22-3.31, plate underside 2.24-2.34, post at LX;
# porch beam underside 2.32, deck at the wall 3.10; host back arch 1.5 m / 9.5 m, front 1.4 m / 6 m
SHOTS = {
    # ---- interior volumes (red twin: any red = daylight into the volume) ----
    "i01_shed_up_to_crease": ((LX + 0.6, LY + 1.55, 0.9), (LX, LY, 3.1), 22, "red", False),
    "i02_shed_W_endwall_head": ((LX + 1.0, LY + 0.55, 1.5), (LX - 1.7, LY + 0.85, 2.7), 35, "red", False),
    "i03_shed_E_endwall_head": ((LX - 1.0, LY + 0.55, 1.5), (LX + 1.7, LY + 0.85, 2.7), 35, "red", False),
    "i04_host_room_N_head_under_arch": ((LX, LY - 2.15, 1.7), (LX, LY - 0.45, 3.4), 18, "red", False),
    "i05_host_room_S_head_under_arch": ((PX, PY + 2.15, 1.7), (PX, PY + 0.45, 3.2), 18, "red", False),
    "i06_host_attic_N_lifted_eave": ((LX, LY - 1.75, 4.0), (LX, LY - 0.15, 3.7), 16, "red", False),
    "i07_host_attic_S_lifted_eave": ((PX, PY + 2.45, 3.9), (PX, PY + 0.45, 3.5), 16, "red", False),
    "i08_under_hood_up_to_crease": ((PX, PY - 0.70, 1.55), (PX, PY - 0.07, 2.95), 18, "red", False),
    "i09_shed_W_front_corner_plate": ((LX + 0.8, LY + 0.7, 1.6), (LX - 1.6, LF - 0.05, 2.3), 30, "red", False),
    # ---- exterior junctions (void twin) ----
    "x01_leanto_W_rake_endwall": ((LX - 3.7, LF + 0.65, 3.1), (LX - 1.9, LY + 0.75, 2.7), 40, "void", True),
    "x02_leanto_E_rake_endwall": ((LX + 3.7, LF + 0.65, 3.1), (LX + 1.9, LY + 0.75, 2.7), 40, "void", True),
    "x03_leanto_crease_from_above": ((LX + 0.5, LF + 0.75, 4.4), (LX, LY + 0.05, 3.3), 40, "void", True),
    "x04_leanto_front_soffit": ((LX - 0.9, LF + 1.0, 1.25), (LX - 0.3, LF, 2.3), 28, "void", True),
    "x05_porch_E_verge_vs_thatch": ((PX + 2.6, PY - 1.55, 3.0), (PX + 1.2, PY - 0.25, 3.1), 40, "void", True),
    "x06_porch_W_verge_vs_thatch": ((PX - 2.6, PY - 1.55, 3.0), (PX - 1.2, PY - 0.25, 3.1), 40, "void", True),
    "x07_porch_top_gap": ((PX, PY - 1.55, 4.3), (PX, PY - 0.15, 3.1), 30, "void", True),
    "x08_porch_W_brace_foot": ((PX - 2.0, PY - 1.25, 1.5), (PX - 1.05, PY - 0.05, 1.85), 40, "void", True),
    "x13_leanto_W_verge_vs_roll": ((LX - 4.0, LF + 0.6, 3.4), (LX - 2.2, LY + 0.4, 3.2), 40, "void", True),
    "x14_porch_W_wall_corner_apron": ((PX - 1.9, PY - 1.1, 3.45), (PX - 1.3, PY - 0.05, 3.15), 40, "void", True),
    "x15_leanto_E_front_quoin_plate": ((LX + 2.6, LF + 1.4, 2.0), (LX + 1.8, LF - 0.1, 2.3), 40, "void", True),
    # ---- actor scale / thumbnails ----
    "x09_porch_actor_approach": ((PX - 1.2, PY - 5.45, 1.6), (PX, PY - 0.05, 2.3), 35, None, True),
    "x10_leanto_actor_approach": ((LX + 2.7, LF + 4.65, 1.6), (LX, LY + 0.85, 1.9), 35, None, True),
    "x16_leanto_figure_under_brace": ((LX + 1.4, LF + 3.2, 1.5), (LX + 0.3, LF - 0.3, 1.95), 35, None, True),
    # ---- zooms on findings (run with the prefix "z") ----
    "z01_leanto_E_endwall_host_corner": ((LX + 2.9, LY + 0.95, 3.0), (LX + 2.0, LY + 0.05, 2.8), 40, "void", True),
    "z02_host_attic_N_wallhead_W": ((-2.1, LY - 1.3, 4.0), (-2.1, LY - 0.3, 4.2), 24, "red", False),
    "z03_host_attic_N_wallhead_E": ((-0.6, LY - 1.3, 4.0), (-0.6, LY - 0.3, 4.2), 24, "red", False),
    "z04_host_N_wallhead_outside": ((LX, LY + 1.2, 3.6), (LX, LY, 4.2), 22, "void", True),
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

