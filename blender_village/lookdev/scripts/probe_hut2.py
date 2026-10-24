import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
me = bpy.data.objects['HUT_daub'].data
a = np.empty(len(me.loops) * 4, np.float32); me.color_attributes['Mask'].data.foreach_get('color', a); a = a.reshape(-1, 4)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
P = co[a[:, 1] > 0.5 ][:0] if False else co[lv[a[:, 1] > 0.5]]
ang = np.degrees(np.arctan2(P[:, 1], P[:, 0]))
order = np.argsort(ang); ang_s = ang[order]; Ps = P[order]
cl = [[0]]
for i in range(1, len(ang_s)):
    (cl[-1].append(i) if ang_s[i] - ang_s[i-1] < 8 else cl.append([i]))
for c in cl:
    pts = Ps[c]; print('cluster n', len(c), 'angle %.0f..%.0f' % (ang_s[c[0]], ang_s[c[-1]]), 'centroid', pts.mean(0).round(2), 'z', pts[:, 2].min().round(2), pts[:, 2].max().round(2))
