import sys, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for ob in bpy.data.objects:
    if ob.type=='MESH' and ('roof' in ob.name or 'gable' in ob.name or 'tower' in ob.name or 'cap' in ob.name or 'eave' in ob.name):
        zs=[v.co.z for v in ob.data.vertices]; xs=[v.co.x for v in ob.data.vertices]; ys=[v.co.y for v in ob.data.vertices]
        if zs: print(f"{ob.name:40s} z {min(zs):6.2f} {max(zs):6.2f}  x {min(xs):6.2f} {max(xs):6.2f}  y {min(ys):6.2f} {max(ys):6.2f}")
