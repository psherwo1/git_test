"""Director distinctness lineup: watchtower (centre) beside the tower_windmill (+X) and wattle_roundhut (-X).
Run: blender -b <watchtower.blend> --python dir_lineup_r01.py -- <out_dir> <mill.blend> <hut.blend>
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
out, mill, hut = os.path.abspath(argv[0]), argv[1], argv[2]
scn = bpy.context.scene


def bring(path, dx):
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith("DA_")]
    for o in dst.objects:
        if o is None or o.type not in ("MESH", "CURVE"):
            continue
        if o.parent is not None:
            continue
        inst = o.copy() if False else bpy.data.objects.new(o.name + "_lu", o.data)
        inst.matrix_world = Matrix.Translation((dx, 0, 0)) @ o.matrix_world
        scn.collection.objects.link(inst)


bring(mill, 13.0)
bring(hut, -11.0)

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
for x in (-11.0 + 0.0, 0.0, 13.0):
    loc = Vector((x + 2.5, -5.0, 0.0))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.45, location=loc + Vector((0, 0, 0.725)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=loc + Vector((0, 0, 1.68)))
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
c, t = Vector((2.0, -48.0, 6.0)), Vector((1.0, 0.0, 6.5))
cam.location = c
cam.rotation_euler = (t - c).to_track_quat("-Z", "Y").to_euler()
scn.render.filepath = os.path.join(out, "j18_lineup_hut_watch_mill.png")
bpy.ops.render.render(write_still=True)
print("WROTE lineup")
