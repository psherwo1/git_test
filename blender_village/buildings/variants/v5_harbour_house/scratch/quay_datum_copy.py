"""scratch (not a deliverable): a copy of the building cut at Z = -0.05 (the quay datum), so tools/render_review.py
puts its ground plane and 1.8 m figure on the quay instead of the harbour bed.  python -I quay_datum_copy.py <in> <out>"""
import sys

import bpy
import bmesh

src, dst = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=src)
done = set()
for ob in list(bpy.data.objects):
    if ob.type != "MESH" or ob.data.name in done:
        continue
    done.add(ob.data.name)
    me = ob.data
    if min((ob.matrix_world @ v.co).z for v in me.vertices) > -0.05:
        continue
    bm = bmesh.new()
    bm.from_mesh(me)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, -0.05), plane_no=(0, 0, 1), clear_inner=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if len(me.polygons) == 0:
        bpy.data.objects.remove(ob)
bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
print("quay-datum copy saved", dst)
