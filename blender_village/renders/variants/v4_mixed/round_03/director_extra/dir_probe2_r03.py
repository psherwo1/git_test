"""v4 r3 probe 2: where house posts / floor / daub run into the drum, and whether any of it is outside the
abutment posts' cover; rafter tails vs wall plate support at the drum face; rays through the house doorway."""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get()
MILL = np.array((2.82, 1.36))
HOUSE = np.array((-1.462, 0.214))


def world(ob):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices]) if len(me.vertices) else np.zeros((0, 3))
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


def R(z):
    return 2.05 + (1.70 - 2.05) * np.clip(z, 0, 5.5) / 5.5


def field(P):
    return np.hypot(P[:, 0] - MILL[0], P[:, 1] - MILL[1]) - R(P[:, 2])


for nm in ("V4H_posts", "V4H_floor", "V4H_daub", "V4H_daub_interior"):
    V, F = world(bpy.data.objects[nm])
    f = field(V)
    ins = V[f < -0.01]
    if len(ins):
        az = np.degrees(np.arctan2(ins[:, 1] - HOUSE[1], ins[:, 0] - HOUSE[0]))
        print("%s inside drum: n %d  x %.2f..%.2f  y %.2f..%.2f z %.2f..%.2f  house-az %.1f..%.1f" % (
            nm, len(ins), ins[:, 0].min(), ins[:, 0].max(), ins[:, 1].min(), ins[:, 1].max(), ins[:, 2].min(),
            ins[:, 2].max(), az.min(), az.max()))

# posts: cluster posts' vertices by house azimuth, report r range for the posts near the drum
V, F = world(bpy.data.objects["V4H_posts"])
az = np.degrees(np.arctan2(V[:, 1] - HOUSE[1], V[:, 0] - HOUSE[0]))
r = np.hypot(V[:, 0] - HOUSE[0], V[:, 1] - HOUSE[1])
sel = (np.abs(az - 15) < 40)
bins = np.round(az[sel] / 3) * 3
for bv in sorted(set(bins)):
    m = bins == bv
    P = V[sel][m]
    print("post az~%5.0f n %4d r %.2f..%.2f field min %.3f" % (bv, m.sum(), r[sel][m].min(), r[sel][m].max(),
                                                              field(P).min()))
V, F = world(bpy.data.objects["V4J_abutment_posts"])
az = np.degrees(np.arctan2(V[:, 1] - HOUSE[1], V[:, 0] - HOUSE[0]))
print("abutment posts house-az %.1f..%.1f; split:" % (az.min(), az.max()))
for lo, hi in ((-90, 15), (15, 90)):
    m = (az >= lo) & (az < hi)
    if m.any():
        P = V[m]
        print("  post az %.1f..%.1f x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (az[m].min(), az[m].max(), P[:, 0].min(),
              P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max()))

# wall plate support under the cut rafter feet: for each rafter vertex within 3 cm of the drum face, ray down
allV, allF = [], []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith("V4H_wall_plate"):
        continue
    Vp, Fp = world(o)
    off = len(allV)
    allV += [Vector(v) for v in Vp]
    allF += [tuple(i + off for i in f) for f in Fp]
Tp = BVHTree.FromPolygons(allV, allF)
V, F = world(bpy.data.objects["V4H_rafters"])
f = field(V)
cut = V[np.abs(f + 0.02) < 0.004]
print("rafter verts on cut surface", len(cut))
for p in cut:
    h = Tp.ray_cast(Vector((p[0], p[1], p[2] + 0.001)), Vector((0, 0, -1)), 0.5)
    print("  cut (%.3f, %.3f, %.3f) r_house %.3f -> plate below at %s" % (
        p[0], p[1], p[2], math.hypot(p[0] - HOUSE[0], p[1] - HOUSE[1]),
        None if h[0] is None else "dz %.3f" % (p[2] - h[0].z)))
Vp = np.array([tuple(v) for v in allV])
rp = np.hypot(Vp[:, 0] - HOUSE[0], Vp[:, 1] - HOUSE[1])
print("wall plate r %.3f..%.3f z %.3f..%.3f" % (rp.min(), rp.max(), Vp[:, 2].min(), Vp[:, 2].max()))
