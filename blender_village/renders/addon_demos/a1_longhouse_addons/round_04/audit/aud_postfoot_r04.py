"""Auditor a1 round-4: is the lean-to post's 3 cm hover over its pad visible from ground / 6 m cameras? (read-only)
blender -b -P aud_postfoot_r04.py -- <blend> <out_dir>
Targets: the pad's top face UNDER the post's foot (where post and pad should be in contact) and the post's own bottom
face.  For each camera, a target counts as SEEN if the first hit from the camera is that target point (within 5 mm).
Also renders a small Workbench close-up of the post foot from eye height (no file is changed)."""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = a[1]; os.makedirs(out, exist_ok=True)
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off = [], [], [], 0
for oi, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(m.loop_triangles), oi)); off += len(co)
    o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
names = [o.name for o in objs]
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
PX, PY = -1.594, 4.272                         # the post axis (world)
pad_top = [Vector((PX + dx, PY + dy, 0.1001)) for dx in np.linspace(-0.09, 0.09, 7) for dy in np.linspace(-0.09, 0.09, 7)]
post_bot = [Vector((PX + dx, PY + dy, 0.1299)) for dx in np.linspace(-0.09, 0.09, 7) for dy in np.linspace(-0.09, 0.09, 7)]
cams = {}
for dist in (2.5, 4.0, 6.0, 10.0):
    for ang in range(-80, 81, 20):
        th = math.radians(90 + ang)
        for z in (0.4, 1.0, 1.7, 6.0):
            cams[f"d{dist:.1f}_a{ang:+d}_z{z:.1f}"] = Vector((PX + dist * math.cos(th), PY + dist * math.sin(th), z))
tot = {"pad_top_under_post": 0, "post_bottom": 0}
seen_by = {}
for cn, c in cams.items():
    for lab, tg in (("pad_top_under_post", pad_top), ("post_bottom", post_bot)):
        k = 0
        for p in tg:
            d = p - c; L = d.length; d.normalize()
            h = bvh.ray_cast(c, d, L + 0.05)
            if h[0] is not None and (h[0] - p).length < 0.005:
                k += 1
        if k:
            tot[lab] += k
            seen_by.setdefault(lab, []).append((cn, k))
print("cameras", len(cams), "(rings of 2.5 / 4 / 6 / 10 m round the front, -80..+80 deg, eye z 0.4 / 1.0 / 1.7 / 6.0)")
for lab in tot:
    s = seen_by.get(lab, [])
    print(f"{lab}: seen from {len(s)} cameras; e.g. {s[:12]}")
    for zz in ("z1.7", "z6.0"):
        print(f"   from z {zz[1:]}: {[x for x in s if x[0].endswith(zz)][:10]}")
# Workbench close-ups
scn = bpy.context.scene
scn.render.engine = "BLENDER_WORKBENCH"
scn.display.shading.light = "STUDIO"
scn.display.shading.show_cavity = True
scn.render.resolution_x, scn.render.resolution_y = 960, 540
scn.render.image_settings.file_format = "PNG"
bpy.ops.object.camera_add(); cam = bpy.context.object; scn.camera = cam
for nm, loc, lens in (("post_foot_eye_3m", (PX + 0.6, PY + 3.0, 1.65), 70), ("post_foot_eye_5m", (PX + 1.0, PY + 5.0, 1.65), 85),
                      ("post_foot_low_2m", (PX + 0.4, PY + 2.0, 0.45), 60)):
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector((PX, PY, 0.15)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = os.path.join(out, nm + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER", nm)
print("DONE")
