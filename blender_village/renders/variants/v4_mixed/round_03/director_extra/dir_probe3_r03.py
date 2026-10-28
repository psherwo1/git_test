"""v4 r3 probe 3: fillet top vs the drum's band string course; BVH overlaps of V4J parts against the drum parts;
sky rays from under both eave ends and through the junction zone from exterior cameras."""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get()


def world(ob):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = [ob.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


def tree(names):
    allV, allF = [], []
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        V, F = world(ob)
        o = len(allV)
        allV += V
        allF += [tuple(i + o for i in f) for f in F]
    return BVHTree.FromPolygons(allV, allF), allV


Vf, Ff = world(bpy.data.objects["V4J_roof_tower_fillet"])
hi = sorted(Vf, key=lambda v: -v.z)[:5]
print("fillet top verts:", [tuple(round(x, 3) for x in v) for v in hi])
for n in ("V4M_base_dressed", "V4M_arcade_dressed", "V4M_base_stones", "V4M_base_mortar", "V4M_wall_core",
          "V4M_arcade_backs"):
    T, Vb = tree([n])
    Tf, _ = tree(["V4J_roof_tower_fillet"])
    ov = len(Tf.overlap(T))
    d = min(T.find_nearest(v)[3] for v in hi)
    # band verts nearest the fillet's top
    print("FILLET vs %-20s overlaps %5d  nearest from fillet top %.3f" % (n, ov, d))
# where is the band's lower edge near the fillet top
Vd, _ = world(bpy.data.objects["V4M_base_dressed"])
top = hi[0]
near = [v for v in Vd if math.hypot(v.x - top.x, v.y - top.y) < 0.4 and 3.6 < v.z < 4.3]
if near:
    print("band verts near fillet top: z %.3f..%.3f" % (min(v.z for v in near), max(v.z for v in near)))

# sky rays: all V4 meshes
names = [o.name for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("V4")]
T, _ = tree(names)
print("sky check")
for label, org in (("under front eave end", Vector((0.75, -1.55, 1.6))), ("under back eave end", Vector((0.15, 3.25, 1.6)))):
    n = s = 0
    for i in range(-20, 21):
        for j in range(2, 30):
            el = math.radians(3 * j)
            az = math.radians(6 * i) + math.atan2(1.4 if "front" in label else -1.1, 0.3 if "front" in label else 0.8)
            d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
            h = T.ray_cast(org, d, 40)
            n += 1
            if h[0] is None:
                s += 1
    print("  %s: %d / %d rays reach the sky (true sky past the eave included)" % (label, s, n))
# rays aimed AT the junction band region from 8 exterior cams: count rays whose target point region is within 0.4 m of
# the fillet line but that escape (pass through)
Tf, VF = tree(["V4J_roof_tower_fillet"])
pts = VF[::7]
for k in range(8):
    a = math.radians(45 * k)
    cam = Vector((1.3 + 12 * math.cos(a), 1.0 + 12 * math.sin(a), 6.0))
    esc = tot = 0
    for p in pts:
        d = (p - cam)
        dist = d.length
        h = T.ray_cast(cam, d.normalized(), dist + 0.6)
        tot += 1
        if h[0] is None:
            esc += 1
    print("  cam az %3d: %d / %d rays toward fillet points pass straight through (no hit)" % (45 * k, esc, tot))
