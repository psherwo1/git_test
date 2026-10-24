"""Auditor a1 round-4 re-audit supplement (read-only): is the post's foot embedded in its pad, with no sight-line through?
python -I aud_postfoot_embed_r04b.py -- <blend>
(1) pad mesh: closed? top z over the post footprint; post foot z; embedment depth.
(2) dense horizontal rings at the post axis (z 0.100..0.160, 2.5 mm, 72 azimuths): rays that pass clean; and for the
    pad-height rings, the one ray (if any) that passes, with its azimuth (edge graze vs real gap).
(3) the 144 audit cameras (as aud_postfoot_r04.py): any first hit on the POST below the pad top (a visible foot) or on
    anything other than pad / post when aimed at the post's skin between z 0.125 and the pad top."""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off, per = [], [], [], 0, {}
for oi, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world); co = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    ed = np.empty(len(m.edges) * 2, np.int32); m.edges.foreach_get("vertices", ed); ed = ed.reshape(-1, 2)
    # boundary edges (used by one face)
    cnt = {}
    for p in m.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            k = tuple(sorted((vs[i], vs[(i + 1) % len(vs)])))
            cnt[k] = cnt.get(k, 0) + 1
    per[o.name] = (co, tv, sum(1 for v in cnt.values() if v == 1))
    V.append(co); T.append(tv + off); OWN.append(np.full(len(tv), oi)); off += len(co)
    o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
names = [o.name for o in objs]
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
pc, _, pb = per["A1L_lean_to_posts"]; dc, dt, db = per["A1L_lean_to_pads"]
low = pc[pc[:, 2] < 0.40]
cx, cy = low[:, 0].mean(), low[:, 1].mean()
foot_z = low[:, 2].min()
print(f"PAD verts {len(dc)} tris {len(dt)} boundary edges {db}; z {dc[:,2].min():.4f}..{dc[:,2].max():.4f}; "
      f"xy {np.round(dc[:,:2].min(0),3).tolist()} {np.round(dc[:,:2].max(0),3).tolist()}")
print(f"POST foot z {foot_z:.4f}; foot xy {np.round(low[:,:2].min(0),3).tolist()} {np.round(low[:,:2].max(0),3).tolist()}; axis ({cx:.3f}, {cy:.3f})")
pad = BVHTree.FromPolygons(dc.tolist(), dt.tolist(), all_triangles=True)
tops = []
for dx in np.linspace(-0.099, 0.099, 9):
    for dy in np.linspace(-0.099, 0.099, 9):
        h = pad.ray_cast(Vector((cx + dx, cy + dy, 1.0)), Vector((0, 0, -1)), 2.0)
        tops.append(h[0].z if h[0] is not None else np.nan)
tops = np.array(tops)
print(f"PAD top over the post footprint (81 pts): min {np.nanmin(tops):.4f} max {np.nanmax(tops):.4f} missing {np.isnan(tops).sum()}")
print(f"EMBEDMENT: post foot {foot_z:.4f} vs pad top {np.nanmin(tops):.4f} -> gap {foot_z - np.nanmin(tops):+.4f} m (<= 0 is contact)")
# (2) dense rings
for z in np.arange(0.100, 0.1601, 0.0025):
    clean = []
    for k in range(72):
        ang = k * math.pi / 36
        d = Vector((math.cos(ang), math.sin(ang), 0.0))
        h = bvh.ray_cast(Vector((cx, cy, z)) + d * 1.0, -d, 2.0)
        if h[0] is None:
            clean.append(k * 5)
    print(f"   ring z {z:.4f}: pass clean {len(clean)}/72 {clean[:6]}")
# the old ring (36 rays, 10 deg) at pad heights: which ray passes, and what does it skirt?
for z in (0.08, 0.11, 0.12):
    for k in range(36):
        ang = k * math.pi / 18
        d = Vector((math.cos(ang), math.sin(ang), 0.0))
        o = Vector((cx, cy, z)) + d * 1.0
        if bvh.ray_cast(o, -d, 2.0)[0] is None:
            # nearest geometry along the ray
            best = (9, None)
            for t in np.linspace(0.5, 1.5, 401):
                p = o - d * t
                f = bvh.find_nearest(p)
                if f[0] is not None and f[3] < best[0]:
                    best = (f[3], names[OWN[f[2]]], [round(c, 4) for c in p])
            print(f"   old-ring clean ray z {z:.2f} az {k*10} deg: nearest geometry {best[0]:.5f} m ({best[1]}) at {best[2]}")
# (3) cameras aimed at the post skin between z 0.125 and the pad top
PX, PY = cx, cy
ptop = float(np.nanmin(tops))
cams = {}
for dist in (2.5, 4.0, 6.0, 10.0):
    for ang in range(-80, 81, 20):
        th = math.radians(90 + ang)
        for z in (0.4, 1.0, 1.7, 6.0):
            cams[f"d{dist:.1f}_a{ang:+d}_z{z:.1f}"] = Vector((PX + dist * math.cos(th), PY + dist * math.sin(th), z))
hw = 0.1
skin = []
for s in np.linspace(-hw, hw, 9):
    for z in np.linspace(0.125, ptop - 0.001, 5):
        skin += [Vector((PX + s, PY + hw, z)), Vector((PX + s, PY - hw, z)), Vector((PX + hw, PY + s, z)), Vector((PX - hw, PY + s, z))]
first = {}
post_below = 0
for cn, c in cams.items():
    for p in skin:
        d = p - c; L = d.length; d.normalize()
        h = bvh.ray_cast(c, d, L + 0.3)
        nmh = names[OWN[h[2]]] if h[0] is not None else "SKY/GROUND"
        if h[0] is not None and nmh == "A1L_lean_to_posts" and h[0].z < ptop - 1e-4:
            post_below += 1
        first[nmh] = first.get(nmh, 0) + 1
print(f"CAMERAS {len(cams)} x {len(skin)} rays at the post skin z 0.125..{ptop:.3f}: first hits {dict(sorted(first.items(), key=lambda kv:-kv[1]))}")
print(f"   first hit on the POST below the pad top (a visible foot / gap): {post_below}")
print("DONE")
