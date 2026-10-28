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

# ---- round 3: responds under the cruck posts, corner diagonals, footing overhang over the quay faces ----
for o in meshes:
    if "respond" in o.name or "water_gable_pads" in o.name or "quay_backing" in o.name:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print("BBOX %-36s min %s max %s faces %d" % (o.name, tuple(round(min(v[i] for v in bb), 3) for i in range(3)),
              tuple(round(max(v[i] for v in bb), 3) for i in range(3)), len(o.data.polygons)))
for lab, x0, d in (("E respond", 1.9, (1, 0, 0)), ("W respond", 1.9, (-1, 0, 0))):
    for y in (3.10, 3.25, 3.40, 3.50):
        hits = []
        for z in np.arange(-2.45, 0.6, 0.25):
            r = ray((x0, y, z), d)
            hits.append("%.2f:%s@%.2f" % (z, r[0].replace("HARB_", "")[:18] if r else None, r[1] if r else -1))
        print("RESP %s y=%.2f  %s" % (lab, y, "  ".join(hits)))
for lab, (x, y) in (("E post foot", (4.05, 3.30)), ("W post foot", (-0.27, 3.30)), ("E post foot outer", (4.15, 3.45)),
                    ("W post foot outer", (-0.37, 3.45))):
    for dz in (0.01, 0.05):
        r = ray((x, y, dz), (0, 0, -1))
        print("DOWN %-20s z=%.2f -> %s" % (lab, dz, r))
for lab, (x, y) in (("E corner", (4.192, 3.427)), ("W corner", (-0.408, 3.427))):
    sx = 1 if x > 1.9 else -1
    for z in np.arange(-2.35, -0.05, 0.3):
        for dv in ((-sx, -1, 0), (-sx * 0.5, -1, 0), (-sx, -0.5, 0)):
            # start 0.6 m outside the convex corner arris (outside = toward the slip side and water)
            p = (x - sx * 0.0 + (-dv[0]) * 0.6, y + 0.6, z)
            p = (x + (-sx) * -0.0, y, z)
        for ang in (30, 45, 60):
            import math
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            # convex corner: the solid lies at x beyond the corner (east: x > 4.192 is quay; slip at x<4.192 & y<3.427)
            # from the water outside (y > 3.427) and over the slip (x toward 1.9), aim at the arris
            o_ = Vector((x - sx * dx * 0.8, y + dy * 0.8, z))
            r = ray(o_, Vector((x, y, z)) - o_)
            if r is None or r[1] > 0.83:
                print("CORNER %s z=%.2f ang %d -> %s" % (lab, z, ang, r))
print("CORNER scan done")
# footing overhang: rays straight down just outside the quay faces under the flush runs
for lab, pts in (("slip E wall", [(4.192 - 0.06, y, 0.6) for y in np.arange(0.4, 3.4, 0.1)]),
                 ("slip W wall", [(-0.408 + 0.06, y, 0.6) for y in np.arange(0.4, 3.4, 0.1)]),
                 ("E pier face", [(x, 3.427 + 0.06, 0.6) for x in np.arange(4.3, 4.9, 0.05)]),
                 ("W pier face", [(x, 3.427 + 0.06, 0.6) for x in np.arange(-1.1, -0.45, 0.05)])):
    hit = [(round(p[0], 2), round(p[1], 2), ray(p, (0, 0, -1))) for p in pts]
    bad = [(h[0], h[1], h[2][0], round(0.6 - h[2][1], 3)) for h in hit if h[2] and 0.6 - h[2][1] > -0.30]
    print("FOOT %-12s rays %d hits above z-0.30: %d %s" % (lab, len(pts), len(bad), bad[:6]))
