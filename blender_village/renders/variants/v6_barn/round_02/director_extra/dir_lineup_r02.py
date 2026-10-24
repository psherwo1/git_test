"""Director note-16 line-up (adapted from v5 dir_lineup_r03.py): longhouse v3, harbour house v5, barn v6 and the
roundhut hero side by side at one scale, plus per-building thumbnails from ONE camera rig (same distance / lens) for
the note-17 distinctness check.
blender -b --python dir_lineup_r01.py -- <out_dir> <blend> [<blend> ...]   (left to right)"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
out, blends = argv[0], argv[1:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
x_cursor = 0.0
groups = []
for bl in blends:
    with bpy.data.libraries.load(bl, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    objs = [o for o in dst.objects if o is not None and o.type == "MESH"]
    for o in objs:
        scn.collection.objects.link(o)
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mnx = min(p.x for p in pts); mxx = max(p.x for p in pts)
    mny = min(p.y for p in pts); mxy = max(p.y for p in pts)
    top = max(p.z for p in pts)
    dx = x_cursor - mnx
    for o in objs:
        o.location.x += dx
    groups.append((os.path.basename(bl), x_cursor, x_cursor + (mxx - mnx), top, objs, 0.5 * (mny + mxy)))
    print("PLACED", os.path.basename(bl), "x", round(x_cursor, 2), "w", round(mxx - mnx, 2), "d",
          round(mxy - mny, 2), "top", round(top, 2), flush=True)
    x_cursor += (mxx - mnx) + 4.0
W = x_cursor - 4.0
clay = bpy.data.materials.new("_clay"); clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1); b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
bpy.ops.mesh.primitive_plane_add(size=400, location=(W / 2, 0, -0.003))
figs = []
for g in groups:
    x = 0.5 * (g[1] + g[2]) + 1.2
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.55, location=(x, -11.0, 0.775)); figs.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(x, -11.0, 1.67)); figs.append(bpy.context.object)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
sun = bpy.context.object; sun.data.energy = 3.5; sun.data.angle = math.radians(2.0)
world = bpy.data.worlds.new("_w"); world.use_nodes = True; scn.world = world
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1)
bg.inputs["Strength"].default_value = 0.45
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
scn.cycles.samples = 32; scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = 1920, 820
scn.render.image_settings.file_format = "PNG"; scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam
Hmax = max(g[3] for g in groups)
cam.data.type = "ORTHO"; cam.data.ortho_scale = W + 6.0
cam.location = Vector((W / 2, -80.0, Hmax * 0.42)); cam.rotation_euler = (math.radians(90), 0, 0)
scn.render.filepath = os.path.join(out, "L01_lineup_front_ortho.png"); bpy.ops.render.render(write_still=True)
print("SHOT L01", flush=True)
cam.data.type = "PERSP"; cam.data.lens = 30
cam.location = Vector((W * 0.62, -W * 1.05, 7.0))
cam.rotation_euler = (Vector((W / 2, 0.0, Hmax * 0.35)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scn.render.filepath = os.path.join(out, "L02_lineup_three_quarter.png"); bpy.ops.render.render(write_still=True)
print("SHOT L02", flush=True)
cam.data.lens = 30; cam.location = Vector((W * 0.5, -W * 0.8, W * 0.62))
cam.rotation_euler = (Vector((W / 2, 0.0, 2.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scn.render.filepath = os.path.join(out, "L03_lineup_aerial.png"); bpy.ops.render.render(write_still=True)
print("SHOT L03", flush=True)
# per-building thumbnails, one rig: 46 m away, 14 m up, lens 50, 320 x 180, from SW and SE
scn.render.resolution_x, scn.render.resolution_y = 320, 180
for o in figs:
    o.hide_render = True
for i, g in enumerate(groups):
    for h in groups:
        for o in h[4]:
            o.hide_render = h is not g
    cx = 0.5 * (g[1] + g[2]); cy = g[5]
    for tag, (dx, dy) in (("SW", (-30.0, -35.0)), ("SE", (30.0, -35.0))):
        cam.data.lens = 50; cam.location = Vector((cx + dx, cy + dy, 14.0))
        cam.rotation_euler = (Vector((cx, cy, 4.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        nm = os.path.splitext(g[0])[0]
        scn.render.filepath = os.path.join(out, f"T{i}_{tag}_{nm}.png"); bpy.ops.render.render(write_still=True)
        print("SHOT T", nm, tag, flush=True)
