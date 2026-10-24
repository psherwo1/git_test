"""Director r4 hygiene check on the cabin objects: degenerate / near-zero-area faces, non-manifold edges, and
what the hip-trimmed shingles look like at the eave corners.
python dir_check_r04.py <blend>"""
import math
import sys

import bpy  # noqa: I001  (bpy must load before bmesh)
import bmesh

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for ob in sorted((o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("WATCH_")),
                 key=lambda o: o.name):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    z0 = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    z1 = sum(1 for f in bm.faces if f.calc_area() < 1e-6)
    sl = 0
    for f in bm.faces:
        if len(f.verts) < 3:
            continue
        a = f.calc_area()
        mx = max((e.calc_length() for e in f.edges), default=0)
        if mx > 0 and 2 * a / mx < 1e-4:       # altitude < 0.1 mm
            sl += 1
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bnd = sum(1 for e in bm.edges if e.is_boundary)
    print("HYG %-26s faces %7d  area<1e-8 %5d  area<1e-6 %5d  slivers<0.1mm %5d  non-manifold edges %6d  boundary %6d"
          % (ob.name, len(bm.faces), z0, z1, sl, nm, bnd), flush=True)
    bm.free()
