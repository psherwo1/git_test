"""a1 round 3 builder: ONE look render of the porch reuse smoke on v5 (land-gable door), real materials, plus a clay
void twin of the hood / wall junction.
python -I bx_smoke_v5_r03.py <smoke.blend> <out_dir> <shift_x> <shift_y>"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
blend, out, SX, SY = argv[0], argv[1], float(argv[2]), float(argv[3])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
scn = bpy.context.scene
DX, DY = 4.8, 0.2                                  # v5 DOOR_X, Y0 (recipe plan)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.06))
gr = bpy.context.object
gr.scale = (300, 300, 1)
for (x, y) in ((DX + 1.1, DY - 1.9),):            # a 1.8 m figure beside the door
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x + SX, y + SY, 0.775))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x + SX, y + SY, 1.67))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(55), 0, math.radians(-30)))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_B_world")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
bg.inputs["Strength"].default_value = 0.5
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
scn.render.image_settings.file_format = "PNG"
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02
SHOTS = {
    "S01_v5_porch_reuse": ((DX - 3.6, DY - 6.8, 1.75), (DX + 0.2, DY, 2.55), 30, None),
    "S02_v5_porch_junction": ((DX + 2.3, DY - 1.9, 3.7), (DX + 0.6, DY - 0.1, 3.1), 35, "void"),
}
void = bpy.data.materials.new("_B_void")
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
for name, (loc, tgt, lens, twin) in SHOTS.items():
    cam.location = Vector((loc[0] + SX, loc[1] + SY, loc[2]))
    cam.data.lens = lens
    t = Vector((tgt[0] + SX, tgt[1] + SY, tgt[2]))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.view_layers[0].material_override = None
    scn.cycles.samples = 32
    scn.cycles.use_denoising = True
    gr.hide_render = False
    sun.hide_render = False
    bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
    bg.inputs["Strength"].default_value = 0.5
    scn.view_settings.view_transform = "AgX"
    scn.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    if twin:
        scn.view_layers[0].material_override = void
        gr.hide_render = True
        sun.hide_render = True
        bg.inputs["Color"].default_value = (1.0, 0.0, 0.0, 1)
        bg.inputs["Strength"].default_value = 1.0
        scn.view_settings.view_transform = "Standard"
        scn.cycles.samples = 4
        scn.cycles.use_denoising = False
        p = os.path.join(out, name + "_void.png")
        scn.render.filepath = p
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(p)
        px = im.pixels[:]
        r = sum(1 for i in range(0, len(px), 4) if px[i] > 0.5 and px[i + 1] < 0.2 and px[i + 2] < 0.2)
        y = sum(1 for i in range(0, len(px), 4) if px[i] > 0.5 and px[i + 1] > 0.4 and px[i + 2] < 0.2)
        print("COUNT", name, "void red", r, "yellow", y, flush=True)
    print("SHOT", name, flush=True)
