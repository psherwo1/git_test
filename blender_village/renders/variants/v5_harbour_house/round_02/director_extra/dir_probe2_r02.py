"""Director round-2 probe 2: hole scan of the quay faces (slip returns, slip head, outer water face) and the
water-gable / tower / roof shells.  python -I dir_probe2_r02.py -- <blend>"""
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

blend = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bvh = {}
for o in meshes:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bvh[o.name] = BVHTree.FromBMesh(bm); bm.free()


def ray(p, d, maxd=30.0):
    p, d = Vector(p), Vector(d).normalized()
    best = None
    for n_, t in bvh.items():
        r = t.ray_cast(p, d, maxd)
        if r[0] is not None and (best is None or r[3] < best[1]):
            best = (n_, r[3], r[0])
    return best


def scan(label, pts, d, expect_max):
    miss, far = [], []
    for p in pts:
        r = ray(p, d)
        if r is None:
            miss.append(tuple(round(x, 2) for x in p))
        elif r[1] > expect_max:
            far.append((tuple(round(x, 2) for x in p), r[0], round(r[1], 2)))
    print("SCAN %-34s rays %4d  miss %4d  beyond %4d" % (label, len(pts), len(miss), len(far)))
    for m in miss[:12]:
        print("   miss", m)
    for f in far[:8]:
        print("   far ", f)


zs = np.arange(-2.40, -0.05, 0.15)
ys = np.arange(0.30, 3.40, 0.15)
scan("slip E return (+X from x=1.9)", [(1.9, y, z) for y in ys for z in zs], (1, 0, 0), 2.40)
scan("slip W return (-X from x=1.9)", [(1.9, y, z) for y in ys for z in zs], (-1, 0, 0), 2.40)
xs = np.arange(-0.30, 4.10, 0.15)
scan("slip head (-Y from y=2.0)", [(x, 2.0, z) for x in xs for z in zs], (0, -1, 0), 1.90)
xs = np.arange(-4.20, 8.25, 0.15)
xs_out = [x for x in xs if not (-0.40 < x < 4.19)]
scan("outer water face (-Y from y=6)", [(x, 6.0, z) for x in xs_out for z in zs], (0, -1, 0), 2.70)
# above the coping inside the slip: walls / partition (0 .. 3)
zw = np.arange(0.05, 3.0, 0.15)
scan("slip E wall (+X) z>0", [(1.9, y, z) for y in ys for z in zw], (1, 0, 0), 2.40)
scan("slip W wall (-X) z>0", [(1.9, y, z) for y in ys for z in zw], (-1, 0, 0), 2.40)
scan("partition (-Y) z>0", [(x, 2.0, z) for x in np.arange(-0.30, 4.10, 0.15) for z in zw], (0, -1, 0), 1.90)
# looking up inside the slip: the roof / tie / arch cover
scan("slip ceiling (up)", [(x, y, 0.5) for x in np.arange(-0.3, 4.1, 0.2) for y in np.arange(0.3, 3.3, 0.2)],
     (0, 0, 1), 12.0)
# from the water toward the water gable at every height (frame + infill + piers)
scan("water gable (-Y from y=8)", [(x, 8.0, z) for x in np.arange(-1.0, 4.8, 0.12)
                                    for z in np.arange(3.1, 8.2, 0.12)], (0, -1, 0), 5.0)
