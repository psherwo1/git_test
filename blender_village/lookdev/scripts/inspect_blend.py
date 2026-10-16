import sys, bpy, collections
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
sc = bpy.context.scene
print('scene', sc.name, 'engine', sc.render.engine, 'cams', [o.name for o in bpy.data.objects if o.type=='CAMERA'], 'lights', [o.name for o in bpy.data.objects if o.type=='LIGHT'])
print('world', sc.world.name if sc.world else None)
print('collections', [(c.name, len(c.all_objects), c.hide_render) for c in bpy.data.collections])
types = collections.Counter(o.type for o in bpy.data.objects); print(types)
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
names = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
print('bounds', tuple(round(v,2) for v in mn), tuple(round(v,2) for v in mx))
mats = collections.Counter()
for o in bpy.data.objects:
    if o.type == 'MESH':
        for s in o.material_slots:
            if s.material: mats[s.material.name] += 1
print('materials', dict(mats))
print('all mats', [m.name for m in bpy.data.materials])
o = next(o for o in bpy.data.objects if o.type=='MESH')
print('sample', o.name, [u.name for u in o.data.uv_layers], [(a.name, a.domain, a.data_type) for a in o.data.color_attributes])
for o in bpy.data.objects:
    n = o.name.lower()
    if o.type != 'MESH' or any(k in n for k in ('door','thresh','decal','anchor','figure','scale','helper','human','ref')):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        c = sum(bb, Vector()) / 8 if bb else o.location
        print('OBJ', o.type, o.name, 'loc', tuple(round(v,2) for v in o.matrix_world.translation), 'center', tuple(round(v,2) for v in c), 'hide_render', o.hide_render, 'parent', o.parent.name if o.parent else None)
print('nobj', len(bpy.data.objects))
print('sample names', sorted(o.name for o in bpy.data.objects)[:400])
