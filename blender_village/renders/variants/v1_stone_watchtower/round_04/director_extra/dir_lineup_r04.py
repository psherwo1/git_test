"""Director distinctness lineup r3: wattle_roundhut (-X), v1_stone_watchtower (centre), tower_windmill (+X).
python dir_lineup_r03.py <watch.blend> <out_dir> <mill.blend> <hut.blend>"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

watch, out, mill, hut = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3], sys.argv[4]
bpy.ops.wm.open_mainfile(filepath=watch)
scn = bpy.context.scene


def bring(path, dx):
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith("DA_")]
    for o in dst.objects:
        if o is None or o.type not in ("MESH", "CURVE") or o.parent is not None:
            continue
        inst = bpy.data.objects.new(o.name + "_lu", o.data)
        inst.matrix_world = Matrix.Translation((dx, 0, 0)) @ o.matrix_world
        scn.collection.objects.link(inst)


bring(mill, 14.0)
bring(hut, -12.0)
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.007))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
bpy.context.object.data.energy = 3.5
w = bpy.data.worlds.new("_REVIEW_world")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
scn.world = w
scn.render.engine = "CYCLES"
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
scn.cycles.samples = 24
scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1600, 720
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.lens = 35
cam.data.clip_end = 3000
c, t = Vector((2.0, -50.0, 6.0)), Vector((1.0, 0.0, 7.0))
cam.location = c
cam.rotation_euler = (t - c).to_track_quat("-Z", "Y").to_euler()
scn.render.filepath = os.path.join(out, "j23_lineup_hut_watch_mill.png")
bpy.ops.render.render(write_still=True)
print("WROTE lineup")
