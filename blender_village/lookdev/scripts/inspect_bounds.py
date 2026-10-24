import sys, bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
def bb(objs):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    for o in objs:
        if o.type != 'MESH': continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return tuple(round(v,2) for v in mn), tuple(round(v,2) for v in mx)
for c in bpy.data.collections:
    if c.name != 'DECAL_ANCHORS': print('COL', c.name, bb(c.all_objects))
for o in bpy.data.objects:
    if o.type=='MESH' and not any(k in o.name for k in ('_nail_','_peg_','ridge_comb_shake')):
        print(o.name, bb([o]), [s.material.name for s in o.material_slots if s.material])
