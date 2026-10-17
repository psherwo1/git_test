"""Auditor (read-only): does the CURRENT recipe (edited 14:20:29, after the 14:18:05 build start) describe the saved
blend?  Imports the recipe module WITHOUT running main(), evaluates its roof surfaces and plan, and compares them with
the saved blend.  python -I aud_recipe_match_r04.py <recipe.py> <blend>"""
import importlib.util
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

recipe, blend = sys.argv[-2], sys.argv[-1]
spec = importlib.util.spec_from_file_location("harb_recipe", recipe)
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
SH = Vector((-1.808, -5.973, 0.0))
print("recipe DIM", dict(R.DIM))
print("recipe MAIN overhang/sweep/flare", R.MAIN.__dict__.get("ovh"), [getattr(R.MAIN, k, None) for k in
      ("eave_sweep", "sweep_len", "verge_flare", "flare_len", "ridge_sag", "eave_sag")])
print("HX, XW, XE, Y0, Y1, DOOR_X", R.HX, R.XW, R.XE, R.Y0, R.Y1, R.DOOR_X)
bpy.ops.wm.open_mainfile(filepath=blend)
dg = bpy.context.evaluated_depsgraph_get()
for objname, roof in (("HARB_roof_deck", R.MAIN), ("HARB_wing_roof_deck", R.WING)):
    o = bpy.data.objects[objname]
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = [v.co.copy() for v in m.vertices]; tris = [tuple(t.vertices) for t in m.loop_triangles]
    bvh = BVHTree.FromPolygons(co, tris, all_triangles=True)
    d = []
    if roof is R.MAIN:
        pts = [(x, y) for x in np.linspace(R.XW + 0.3, R.XE - 0.3, 9) for y in np.linspace(R.Y0 + 0.3, R.Y1 - 0.3, 9)]
    else:
        pts = [(x, y) for x in np.linspace(R.DIM["wing_x0"] + 0.3, -2.5, 7)
               for y in np.linspace(-R.DIM["wing_half"] + 0.3, R.DIM["wing_half"] - 0.3, 5)]
    for (x, y) in pts:
        zr = float(roof.under_z_world([[x, y]])[0])
        h = bvh.ray_cast(Vector((x, y, -5.0)) + SH, Vector((0, 0, 1)), 30.0)
        if h[0] is not None:
            d.append(h[0].z - zr)
    d = np.array(d)
    print(f"{objname}: {len(d)} points, blend deck underside - recipe under_z: mean {d.mean()*1000:.1f} mm, "
          f"max |dev| {np.abs(d).max()*1000:.1f} mm")
    o.evaluated_get(dg).to_mesh_clear()
print("DONE")
