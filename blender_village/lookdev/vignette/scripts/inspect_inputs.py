"""Inspect the nine r2 lookdev blends: eligible building meshes, tris, bounds, entrance dir, images."""
import json
import os
import sys

import bpy
from mathutils import Vector

ROOT = r"C:\GitHubDesktop\git_test\blender_village\lookdev\village_r2\work"
IDS = ["hilltop_keep", "wattle_roundhut", "tower_windmill", "v1_stone_watchtower", "v2_tiered_hall",
       "v3_longhouse_roundend", "v4_mixed", "v5_harbour_house", "v6_barn"]
HELPER_KEYS = ("scale_fig", "figure", "helper", "human", "proxy", "dummy", "measure", "ref_", "gizmo")
out = {}
for bid in IDS:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, bid + "_lookdev.blend"))
    scn = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    objs = []
    for o in scn.objects:
        n = o.name.lower()
        if o.type != "MESH" or o.hide_render or o.name.startswith("LD_"):
            continue
        if any(c.name.upper().startswith("DECAL_ANCHOR") or c.hide_render for c in o.users_collection):
            continue
        if any(k in n for k in HELPER_KEYS):
            continue
        objs.append(o)
    tris = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = [round(min(p[i] for p in pts), 2) for i in range(3)]
    mx = [round(max(p[i] for p in pts), 2) for i in range(3)]
    other = sorted({o.type for o in scn.objects})
    parents = sum(1 for o in objs if o.parent is not None)
    mods = sorted({m.type for o in objs for m in o.modifiers})
    missing = [im.name for im in bpy.data.images if im.source == "FILE" and not im.packed_file
               and not os.path.exists(bpy.path.abspath(im.filepath))]
    ents = scn.get("kit_entrances")
    out[bid] = dict(n=len(objs), tris=tris, mn=mn, mx=mx, types=other, parented=parents, mods=mods,
                    missing=missing[:5], ents=(json.loads(ents) if ents else None),
                    imgs=len(bpy.data.images), img0=[bpy.data.images[i].filepath for i in range(min(2, len(bpy.data.images)))],
                    world=scn.world.name if scn.world else None, cols=[c.name for c in bpy.data.collections][:12])
    print("INSPECT", bid, json.dumps(out[bid]), flush=True)
with open(sys.argv[-1], "w") as f:
    json.dump(out, f, indent=1)
