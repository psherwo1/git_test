"""Director smoke test r5: pyramid_roof with the NEW defaults (hip_tuck=None -> 0.8 board, hip_bed=0.30) on 3, 6 and 8
sides, off-centre, no cabin -- do the closed saddle ends and the tucked shingles generalise beyond the square?
Also a 4-sided steep (60 deg) and a shallow (35 deg) roof.  Renders an overview and level close-ups of saddle ends.
python dir_pyramid_reuse_smoke_r05.py <out_dir>"""
import math
import os
import sys
import types

import bpy
from mathutils import Vector

sys.path.insert(0, r"C:\GitHubDesktop\git_test\blender_village\kit")
from village_kit.components.pyramid_roof import pyramid_roof  # noqa: E402

out = os.path.abspath(sys.argv[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
coll = bpy.data.collections.new("TEST")
scn.collection.children.link(coll)
recs = {}
for tag, n, cx, pitch in (("t3", 3, -14.0, 50.0), ("t6", 6, -4.5, 50.0), ("t8", 8, 4.5, 50.0),
                          ("s60", 4, 14.0, 60.0), ("s35", 4, 24.0, 35.0)):
    g = types.SimpleNamespace(prefix=tag.upper(), coll=coll)
    rec = pyramid_roof(g, 2.4, 3.0, name="roof", sides=n, rot_deg=-90.0, cx=cx, cy=5.0, pitch_deg=pitch,
                       eave_out=0.6, bell_deg=22.0, bell_len=0.8, kick=0.05, seed=tag)
    recs[tag] = (n, cx, rec)
    print("SMOKE %s sides %d pitch %.0f: objs %s eave z %.2f corner %.2f apex %.2f tip %.2f shingles %d" % (
        tag, n, pitch, sorted(rec["objs"]), rec["z_eave"], rec["z_eave_corner"], rec["apex"], rec["tip"],
        rec["n_shingles"]), flush=True)
clay = bpy.data.materials.new("_REVIEW_clay")
clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.41, 0.39, 1)
b.inputs["Roughness"].default_value = 0.65
scn.view_layers[0].material_override = clay
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
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.view_settings.view_transform = "AgX"
bpy.ops.object.camera_add()
cam = bpy.context.object
scn.camera = cam
cam.data.clip_start = 0.02


def shot(name, c, t, lens):
    cam.location = c
    cam.data.lens = lens
    cam.rotation_euler = (t - c).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", name, flush=True)


shot("j53_pyramid_reuse_r5_overview", Vector((5.0, -30.0, 12.0)), Vector((5.0, 5.0, 3.5)), 30)
# a level close-up of one saddle end on the 3-, 6- and 8-sided roofs and the steep / shallow squares:
# find the lowest hip-saddle vertex of each and look at it level from outside along its plan direction
for tag, (n, cx, rec) in recs.items():
    ob = bpy.data.objects.get(tag.upper() + "_roof_hips")
    if ob is None:
        print("no hips object for", tag, [o.name for o in bpy.data.objects if o.name.startswith(tag.upper())])
        continue
    me = ob.data
    vs = [ob.matrix_world @ v.co for v in me.vertices]
    lo = min(vs, key=lambda v: v.z)
    c0 = Vector((cx, 5.0, lo.z))
    d = (lo - c0)
    d.z = 0
    d.normalize()
    side = Vector((-d.y, d.x, 0))
    tgt = lo + Vector((0, 0, 0.08))
    shot("j54_saddle_end_%s_level" % tag, tgt + d * 3.2 + side * 0.9 + Vector((0, 0, 0.15)), tgt, 60)
