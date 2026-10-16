import sys, bpy, bmesh
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
names = sys.argv[2].split(',')
for nm in names:
    o = bpy.data.objects[nm]
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    uv = bm.loops.layers.uv['UVMap']
    bad = 0; tot = 0; ex = []
    for f in bm.faces:
        if len(f.loops) < 3: continue
        l0, l1, l2 = f.loops[0], f.loops[1], f.loops[2]
        e1 = l1.vert.co - l0.vert.co; e2 = l2.vert.co - l0.vert.co
        d1 = l1[uv].uv - l0[uv].uv; d2 = l2[uv].uv - l0[uv].uv
        a3 = e1.cross(e2).length / 2; a2 = abs(d1.x * d2.y - d1.y * d2.x) / 2
        tot += f.calc_area()
        r = a2 / max(a3, 1e-12)
        if r < 0.3:
            bad += f.calc_area()
            if len(ex) < 5: ex.append((tuple(round(c, 2) for c in f.normal), round(r, 3)))
    print(nm, 'faces', len(bm.faces), 'area', round(tot, 2), 'area with UV/3D ratio<0.3:', round(bad, 2), ex)
