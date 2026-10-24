"""Director round-3 close-ups for v6_barn (adapted from dir_render_r01.py / bld_render_r02.py: clay, sun, 1.8 m
figures).  Twins:
  _red  = black override + red world, no ground / figures: see-through check (red = sky through the building).
  _void = front faces black, BACK faces emissive yellow, red world: a slot into the culled interior / a hollow shows
          yellow (looking at a face from behind), see-through shows red.
Coordinates after the build's recentre (+0.058, +0.001): front wall y -3.499, back wall y 3.501, gables x -6.942 /
7.058, ridge line y 0.001, cruck cart entry x 0.058.
blender -b --python dir_render_r02.py -- <blend> <out_dir> [only_prefix ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], argv[1]
only = argv[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene


def mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m


clay = mat("_D_clay", (0.42, 0.41, 0.39))
black = mat("_D_black", (0, 0, 0), 1.0)
black.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.0
# void twin: emission black on front faces, yellow on back faces
void = bpy.data.materials.new("_D_void"); void.use_nodes = True
nt = void.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); geo = nt.nodes.new("ShaderNodeNewGeometry")
mix = nt.nodes.new("ShaderNodeMixShader")
e0 = nt.nodes.new("ShaderNodeEmission"); e0.inputs["Color"].default_value = (0, 0, 0, 1)
e1 = nt.nodes.new("ShaderNodeEmission"); e1.inputs["Color"].default_value = (1.0, 0.85, 0.0, 1)
e1.inputs["Strength"].default_value = 1.0
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0]); nt.links.new(e0.outputs[0], mix.inputs[1])
nt.links.new(e1.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs["Surface"])

aux = []
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.002)); gr = bpy.context.object
gr.scale = (300, 300, 1); aux.append(gr)
for (x, y) in ((-1.6, -5.6), (3.2, -6.4), (-9.0, 1.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=(x, y, 0.725)); aux.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, 1.68)); aux.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38))); sun = bpy.context.object
sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_D_world"); world.use_nodes = True
bg = world.node_tree.nodes["Background"]; scn.world = world
scn.render.engine = "CYCLES"; scn.cycles.device = "CPU"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    if any(d.use for d in prefs.devices):
        scn.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001
    print("GPU setup failed", e)
print("DEVICE", scn.cycles.device)
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "Standard"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam; cam.data.clip_start = 0.02

CX = 0.058
FW, RL, BW, GW, GE = -3.499, 0.001, 3.501, -6.942, 7.058
SHOTS = {
    # round 3 director: the cruck entry after the 4.2 m widening (posts moved 0.1 m out each side)
    "d21_W_post_head_under_eyelid": ((CX - 3.6, FW - 3.6, 2.3), (CX - 2.2, FW, 3.75), 55, "void"),
    "d22_E_post_head_under_eyelid": ((CX + 3.6, FW - 3.6, 2.3), (CX + 2.2, FW, 3.75), 55, "void"),
    "d37_W_post_head_notch_close": ((CX - 1.0, FW - 2.4, 2.7), (CX - 2.15, FW, 3.6), 45, "void"),
    "d38_E_post_head_notch_close": ((CX + 1.0, FW - 2.4, 2.7), (CX + 2.15, FW, 3.6), 45, "void"),
    "d23_arch_crown_tie_infill": ((CX + 0.3, FW - 4.5, 2.0), (CX, FW, 3.55), 60, "void"),
    "d39_W_leaf_foot_in_pad": ((CX + 0.4, FW - 1.5, 0.45), (CX - 1.80, FW + 0.05, 0.10), 40, "void"),
    "d40_E_leaf_foot_in_pad": ((CX - 0.4, FW - 1.5, 0.45), (CX + 1.80, FW + 0.05, 0.10), 40, "void"),
    "d26_eyelid_fade_E": ((CX + 6.5, FW - 3.2, 2.0), (CX + 4.6, FW, 3.4), 35, "void"),
    # apex bend, E side and from the ridge
    "d41_E_apex_above_oblique": ((GE + 2.6, RL + 2.2, 8.6), (GE, RL, 7.3), 50, "void"),
    "d42_W_apex_ridge_side": ((GW - 0.3, RL - 4.0, 7.7), (GW, RL, 7.3), 55, "void"),
    "d31_ridge_end_E_profile": ((GE + 0.2, RL - 6.0, 7.6), (GE - 0.6, RL, 7.4), 70, "red"),
    "d29_SW_corner_soffit": ((GW - 1.4, FW - 1.6, 1.7), (GW - 0.2, FW - 0.25, 2.95), 40, "void"),
    # hoist, back
    "d32_hoist_side_on_S": ((GW - 0.8, RL - 9.0, 6.3), (GW - 0.8, RL, 6.1), 55, None),
    "d34_back_eye_N": ((CX + 2.0, BW + 13.0, 1.7), (CX, BW, 3.6), 30, None),
    # massing / thumbnails (same rig as rounds 1-2)
    "d13_thumb_SW_45m": ((-30.0, -36.0, 14.0), (0.0, 0.0, 4.0), 50, None),
    "d14_thumb_SE_45m": ((32.0, -34.0, 14.0), (0.0, 0.0, 4.0), 50, None),
    "d15_thumb_NE_back_45m": ((30.0, 34.0, 13.0), (0.0, 0.0, 4.0), 50, None),
    "d17_W_three_quarter_eye": ((-15.0, -12.0, 1.7), (-1.5, -2.5, 3.6), 28, None),
}


def shoot(name, loc, tgt, lens, twin):
    small = "thumb" in name
    scn.render.resolution_x, scn.render.resolution_y = (320, 180) if small else (1280, 720)
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = clay
    for o in aux:
        o.hide_render = False
    sun.hide_render = False
    scn.view_settings.view_transform = "AgX"
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1); bg.inputs["Strength"].default_value = 0.45
    scn.cycles.samples = 24; scn.cycles.use_denoising = True
    scn.render.filepath = os.path.join(out, name + ".png"); bpy.ops.render.render(write_still=True)
    if twin:
        scn.view_layers[0].material_override = black if twin == "red" else void
        for o in aux:
            o.hide_render = True
        sun.hide_render = True
        scn.view_settings.view_transform = "Standard"
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1); bg.inputs["Strength"].default_value = 1.0
        scn.cycles.samples = 4; scn.cycles.use_denoising = False
        scn.render.filepath = os.path.join(out, name + "_" + twin + ".png"); bpy.ops.render.render(write_still=True)


for name, (loc, tgt, lens, twin) in SHOTS.items():
    if only and not any(name.startswith(p) for p in only):
        continue
    shoot(name, loc, tgt, lens, twin)
    print("SHOT", name, flush=True)
