"""BUILDER ROUND-4 copy (bx_render_r04.py) of the director's dir_render_r03.py: the round-4 build recentres by (+4.606, -0.328), i.e. SY = -0.075 against round 2; plus builder r03 shots x01, x02, x10, x13, x15, z01.  DIRECTOR ROUND-3 (dir_render_r03.py, from bx_render_r03.py / dir_render_r02.py): the rounded-hip lean-to, its end walls, the host attic, the porch profiles. BUILDER ROUND-3 copy of the director's round-2 close-ups (dir_render_r02.py): the round-3 build recentres by (+4.606, -0.303), i.e. SY = -0.05 against round 2, and the lean-to is 2.0 m deep (LF + 0.10).  Director ROUND-2 close-ups for a1_longhouse_addons (copy of round_01 dir_render_r01.py; round-2 world coordinates
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
SX, SY = 0.0, -0.075
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
    # ---- interior volumes (red twin) ----
    "i01_shed_up_to_crease": ((LX + 0.6, LY + 1.55, 0.9), (LX, LY, 3.1), 22, "red", False),
    "i04_host_room_N_head_under_arch": ((LX, LY - 2.15, 1.7), (LX, LY - 0.45, 3.4), 18, "red", False),
    "i05_host_room_S_head_under_arch": ((PX, PY + 2.15, 1.7), (PX, PY + 0.45, 3.2), 18, "red", False),
    "i06_host_attic_N_lifted_eave": ((LX, LY - 1.75, 4.0), (LX, LY - 0.15, 3.7), 16, "red", False),
    "i07_host_attic_S_lifted_eave": ((PX, PY + 2.45, 3.9), (PX, PY + 0.45, 3.5), 16, "red", False),
    "i08_under_hood_up_to_crease": ((PX, PY - 0.70, 1.55), (PX, PY - 0.07, 2.95), 18, "red", False),
    "i10_shed_E_front_corner_plate": ((LX - 0.8, LY + 0.7, 1.6), (LX + 1.6, LF - 0.05, 2.3), 30, "red", False),
    "i11_shed_W_hip_endwall_head": ((LX + 0.4, LY + 1.3, 1.3), (LX - 1.85, LY + 1.0, 2.75), 30, "red", False),
    "i12_shed_E_hip_endwall_head": ((LX - 0.4, LY + 1.3, 1.3), (LX + 1.85, LY + 1.0, 2.75), 30, "red", False),
    "i13_host_attic_N_far_W": ((LX - 3.0, LY - 1.6, 4.1), (LX - 3.0, LY - 0.1, 3.8), 18, "red", False),
    "i15_host_attic_NW_gable_corner": ((-4.9, 1.0, 3.6), (-6.15, 2.25, 2.75), 30, "red", False),
    "i16_host_attic_SW_gable_corner": ((-4.9, -2.1, 3.6), (-6.15, -3.35, 2.75), 30, "red", False),
    "z05_NW_gable_corner_outside": ((-7.6, 3.9, 2.4), (-6.2, 2.3, 2.75), 35, "void", True),
    "i14_host_attic_N_far_E": ((LX + 1.6, LY - 1.6, 4.1), (LX + 1.6, LY - 0.1, 3.8), 18, "red", False),
    # ---- the rounded hips (void twin) ----
    "h01_leanto_W_hip_endon": ((LX - 7.0, LY + 1.3, 1.7), (LX - 2.0, LY + 1.0, 2.6), 35, "void", True),
    "h02_leanto_E_hip_endon": ((LX + 7.0, LY + 1.3, 1.7), (LX + 2.0, LY + 1.0, 2.6), 35, "void", True),
    "h03_leanto_W_hip_soffit": ((LX - 2.7, LY + 1.5, 1.1), (LX - 2.2, LY + 0.8, 2.75), 26, "void", True),
    "h04_leanto_E_hip_soffit": ((LX + 2.7, LY + 1.5, 1.1), (LX + 2.2, LY + 0.8, 2.75), 26, "void", True),
    "h05_leanto_NW_threequarter": ((LX - 5.5, LF + 4.5, 3.4), (LX - 1.2, LY + 1.0, 2.6), 35, None, True),
    "h06_leanto_plan_from_above": ((LX + 0.01, LY + 1.4, 13.0), (LX, LY + 1.4, 2.8), 32, "void", False),
    "h07_leanto_W_hip_meets_wall": ((LX - 3.4, LY + 1.5, 4.3), (LX - 2.35, LY + 0.05, 3.0), 38, "void", True),
    "h08_leanto_E_hip_meets_wall": ((LX + 3.4, LY + 1.5, 4.3), (LX + 2.35, LY + 0.05, 3.0), 38, "void", True),
    "h09_leanto_eave_thickness_vs_host_roll": ((LX - 3.2, LF + 1.6, 2.5), (LX - 2.0, LY + 0.6, 3.0), 30, None, True),
    # ---- porch ----
    "p01_porch_E_profile": ((PX + 3.2, PY - 1.6, 2.5), (PX + 0.3, PY - 0.5, 2.8), 35, "void", True),
    "p02_porch_W_profile": ((PX - 3.2, PY - 1.6, 2.5), (PX - 0.3, PY - 0.5, 2.8), 35, "void", True),
    "p03_porch_hood_top_W_corner": ((PX - 1.6, PY - 1.4, 3.9), (PX - 1.0, PY - 0.1, 3.05), 40, "void", True),
    # ---- builder round-3 shots (bx_render_r03.py), kept for round 4 ----
    "x01_leanto_W_rake_endwall": ((LX - 3.7, LF + 0.65, 3.1), (LX - 1.9, LY + 0.75, 2.7), 40, "void", True),
    "x02_leanto_E_rake_endwall": ((LX + 3.7, LF + 0.65, 3.1), (LX + 1.9, LY + 0.75, 2.7), 40, "void", True),
    "x13_leanto_W_verge_vs_roll": ((LX - 4.0, LF + 0.6, 3.4), (LX - 2.2, LY + 0.4, 3.2), 40, "void", True),
    "x15_leanto_E_front_quoin_plate": ((LX + 2.6, LF + 1.4, 2.0), (LX + 1.8, LF - 0.1, 2.3), 40, "void", True),
    "x10_leanto_actor_approach": ((LX + 2.7, LF + 4.65, 1.6), (LX, LY + 0.85, 1.9), 35, None, True),
    "z01_leanto_E_endwall_host_corner": ((LX + 2.9, LY + 0.95, 3.0), (LX + 2.0, LY + 0.05, 2.8), 40, "void", True),
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



