"""geometry hash of a .blend: SHA-1 over every mesh object's name, vertex coordinates (rounded to 1e-6), polygon
count and world matrix, sorted by name; plus the triangle count.  python dir_hash_r04.py <blend>"""
import hashlib
import sys

import bpy
import numpy as np

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
h = hashlib.sha1()
tris = 0
for ob in sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    h.update(ob.name.encode())
    h.update(np.round(co, 6).tobytes())
    h.update(str(len(me.polygons)).encode())
    h.update(np.round(np.array(ob.matrix_world), 6).tobytes())
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
print("HASH", h.hexdigest(), "TRIS", tris)
