"""Auditor a1 round-4 contacts (read-only).  blender -b -P aud_contacts_r04.py -- <blend>
(1) the lean-to's middle post on its dressed pad: post foot vs pad top, and horizontal sight-lines through any gap;
(2) how far each add-on / seal part reaches past the host wall's outer face into the hollow host interior;
(3) the porch bracket feet and the lean-to plate ends on the walls (nearest wall surface)."""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
per, V, T, OWN, off = {}, [], [], [], 0
for oi, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    per[o.name] = (co, tv)
    V.append(co); T.append(tv + off); OWN.append(np.full(len(tv), oi)); off += len(co)
    o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
names = [o.name for o in objs]
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)


def bv(n):
    co, tv = per[n]
    return BVHTree.FromPolygons(co.tolist(), tv.tolist(), all_triangles=True)


# (1) post on pad
pc, _ = per["A1L_lean_to_posts"]; dc, _ = per["A1L_lean_to_pads"]
pad = bv("A1L_lean_to_pads")
low = pc[pc[:, 2] < 0.40]
print("POST verts below 0.40:", len(low), "z min", round(low[:, 2].min(), 4),
      "xy bbox", np.round(low[:, :2].min(0), 3).tolist(), np.round(low[:, :2].max(0), 3).tolist())
foot = pc[pc[:, 2] < low[:, 2].min() + 0.01]
gaps = []
for p in foot:
    h = pad.ray_cast(Vector(p) + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 0.5)
    gaps.append(None if h[0] is None else round(p[2] - h[0].z, 4))
g = [x for x in gaps if x is not None]
print("POST foot verts", len(foot), "gap to the pad below: min", min(g) if g else None, "max", max(g) if g else None,
      "no pad below:", gaps.count(None))
print("PAD verts z max", round(dc[:, 2].max(), 4), "pad xy bbox", np.round(dc[:, :2].min(0), 3).tolist(),
      np.round(dc[:, :2].max(0), 3).tolist())
# any other geometry (pin, base) between pad top and post foot?
cx, cy = low[:, 0].mean(), low[:, 1].mean()
for z in np.arange(0.06, 0.20, 0.01):
    hits = 0; through = 0
    for k in range(36):
        ang = k * np.pi / 18
        d = Vector((np.cos(ang), np.sin(ang), 0.0))
        o = Vector((cx, cy, z)) + d * 1.0
        h = bvh.ray_cast(o, -d, 2.0)
        if h[0] is None:
            through += 1
        else:
            hits += 1
    print(f"   sight-line ring at z {z:.2f}: rays aimed at the post axis that hit something {hits}/36, pass clean {through}/36")
# vertical profile at the post axis
for dx in (-0.05, 0.0, 0.05):
    o = Vector((cx + dx, cy, 0.5)); seq = []
    for _ in range(6):
        h = bvh.ray_cast(o, Vector((0, 0, -1)), 1.0)
        if h[0] is None:
            break
        seq.append((round(h[0].z, 4), names[OWN[h[2]]].replace("A1L_", "")))
        o = h[0] + Vector((0, 0, -1e-4))
    print(f"   down the post axis (dx {dx:+.2f}):", seq)

# (2) reach past the host wall's outer face (N y 2.272, S y -2.928) into the host body
for n in names:
    if not ("_lean_to" in n or "_porch" in n or "wall_head" in n or "gable_corner" in n):
        continue
    co, _ = per[n]
    inb = (co[:, 0] > -8.394) & (co[:, 0] < 2.606)
    yN = co[inb & (co[:, 1] < 2.272) & (co[:, 1] > 0)][:, 1]
    yS = co[inb & (co[:, 1] > -2.928) & (co[:, 1] < 0)][:, 1]
    print(f"REACH {n:36s} past N face {0 if len(yN)==0 else round(2.272 - yN.min(), 3):6} m  past S face "
          f"{0 if len(yS)==0 else round(yS.max() + 2.928, 3):6} m")
# the host wall's inner surface near the porch arms and the lean-to ledger
for lab, o, d in (("S skin at arm0", (-1.34, -1.0, 1.8), (0, -1, 0)), ("S skin at arm1", (-3.44, -1.0, 1.8), (0, -1, 0)),
                  ("N skin at ledger", (-1.6, 1.0, 3.0), (0, 1, 0)), ("N skin W", (-3.0, 1.0, 3.2), (0, 1, 0))):
    h = bvh.ray_cast(Vector(o), Vector(d), 5)
    print(f"INNER {lab}: first hit from the hollow at {None if h[0] is None else [round(c,3) for c in h[0]]} "
          f"{None if h[0] is None else names[OWN[h[2]]]}")
print("DONE")
