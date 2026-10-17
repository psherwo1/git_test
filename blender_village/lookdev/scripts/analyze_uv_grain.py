import sys, bpy, bmesh, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for m in bpy.data.materials:
    p = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    print('MAT', m.name, tuple(round(c,3) for c in p.inputs['Base Color'].default_value) if p else m.diffuse_color[:], 'nodes', len(m.node_tree.nodes) if m.node_tree else 0)
WOOD = {'M_timber','M_timber_weathered','M_roof_shingle','M_roof_shake','M_thatch'}
stats = {}
deps = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    mats = [s.material.name if s.material else None for s in o.material_slots]
    if not WOOD & set(mats): continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    uv = bm.loops.layers.uv['UVMap']
    col = bm.loops.layers.color.get('Mask') if hasattr(bm.loops.layers,'color') else None
    # loose parts
    bm.faces.ensure_lookup_table()
    seen = set(); parts = []
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; seen.add(f.index); comp = []
        while stack:
            g = stack.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        parts.append(comp)
    for comp in parts:
        verts = {v for f in comp for v in f.verts}
        P = np.array([v.co[:] for v in verts]); C = P - P.mean(0)
        w, V = np.linalg.eigh(C.T @ C)
        long_ax = Vector(V[:, 2]); elong = (w[2] / max(w[1], 1e-9)) ** 0.5
        for f in comp:
            mname = mats[f.material_index] if f.material_index < len(mats) else None
            if mname not in WOOD: continue
            if len(f.loops) < 3: continue
            l0, l1, l2 = f.loops[0], f.loops[1], f.loops[2]
            p0, p1, p2 = l0.vert.co, l1.vert.co, l2.vert.co
            u0, u1, u2 = l0[uv].uv, l1[uv].uv, l2[uv].uv
            e1 = p1 - p0; e2 = p2 - p0; d1 = u1 - u0; d2 = u2 - u0
            det = d1.x * d2.y - d1.y * d2.x
            if abs(det) < 1e-12: continue
            dPdv = (e2 * d1.x - e1 * d2.x) / det
            if dPdv.length < 1e-9: continue
            gv = dPdv.normalized(); a = f.calc_area(); n = f.normal
            s = stats.setdefault(mname, dict(area=0, along=0, across=0, upslope=0, downslope=0, roofarea=0, scale=[]))
            s['area'] += a; s['scale'].append(dPdv.length)
            # only judge broad faces (normal not parallel to long axis) of elongated pieces
            if elong > 1.5:
                la = long_ax - n * long_ax.dot(n)
                if la.length > 1e-6:
                    c = abs(gv.dot(la.normalized()))
                    if c > 0.7: s['along'] += a
                    elif c < 0.3: s['across'] += a
            if n.z > 0.2:
                up = Vector((0, 0, 1)) - n * n.z
                if up.length > 1e-6:
                    c = gv.dot(up.normalized()); s['roofarea'] += a
                    if c > 0.7: s['upslope'] += a
                    elif c < -0.7: s['downslope'] += a
    bm.free()
for k, s in stats.items():
    sc = np.array(s['scale'])
    print(k, 'area %.1f' % s['area'], 'grain(V)-along-long-axis %.0f%%' % (100*s['along']/s['area']), 'across %.0f%%' % (100*s['across']/s['area']),
          '| up-facing area %.1f: V points upslope %.0f%% downslope %.0f%%' % (s['roofarea'], 100*s['upslope']/max(s['roofarea'],1e-9), 100*s['downslope']/max(s['roofarea'],1e-9)),
          '| metres per UV unit median %.2f' % np.median(sc))
# mask stats
for o in bpy.data.objects:
    if o.type=='MESH' and o.name in ('KEEP_cap_shingles','KEEP_hall_wall_stones','KEEP_roof_collar_shakes','KEEP_cone_stones'):
        a = np.empty(len(o.data.color_attributes['Mask'].data)*4, np.float32); o.data.color_attributes['Mask'].data.foreach_get('color', a); a = a.reshape(-1,4)
        print('MASK', o.name, 'mean', a.mean(0).round(3), 'min', a.min(0).round(3), 'max', a.max(0).round(3))
for o in bpy.data.objects:
    if o.type=='MESH' and any(s.material and s.material.name=='M_thatch' for s in o.material_slots): print('THATCH OBJ', o.name)
    if o.type=='MESH' and any(s.material and s.material.name=='M_roof_shingle' for s in o.material_slots): print('SHINGLE OBJ', o.name)
