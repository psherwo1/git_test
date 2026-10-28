"""Director pixel picker: which object is under given pixels of a director shot.
python -I dir_pick_r02.py -- <blend> "<cx,cy,cz>" "<tx,ty,tz>" <lens> px,py [px,py ...]"""
import math
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
blend = a[0]
cam = Vector([float(v) for v in a[1].split(",")])
tgt = Vector([float(v) for v in a[2].split(",")])
lens = float(a[3])
pix = [tuple(float(v) for v in p.split(",")) for p in a[4:]]
bpy.ops.wm.open_mainfile(filepath=blend)
bvh = {}
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        bvh[o.name] = BVHTree.FromBMesh(bm); bm.free()
q = (tgt - cam).to_track_quat("-Z", "Y")
W, H, sw = 1280, 720, 36.0
for (px, py) in pix:
    x = (px / W - 0.5) * sw
    y = -(py / H - 0.5) * sw * H / W
    d = q @ Vector((x, y, -lens))
    d.normalize()
    hits = []
    for n_, t in bvh.items():
        r = t.ray_cast(cam, d, 60.0)
        if r[0] is not None:
            hits.append((round(r[3], 3), n_, tuple(round(c, 3) for c in r[0]), tuple(round(c, 2) for c in r[1])))
    hits.sort()
    print("PIX", (px, py), hits[:3])
