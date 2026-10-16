import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
o = bpy.data.objects['HUT_daub']; me = o.data
a = np.empty(len(me.loops) * 4, np.float32); me.color_attributes['Mask'].data.foreach_get('color', a); a = a.reshape(-1, 4)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
P = co[lv]
print('G hist', np.histogram(a[:, 1], bins=[0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.01])[0])
for th in (0.5, 0.7):
    m = a[:, 1] > th
    if m.any():
        pts = P[m]
        ang = np.degrees(np.arctan2(pts[:, 1], pts[:, 0]))
        print('G>', th, 'n', m.sum(), 'angle hist', np.histogram(ang, bins=12, range=(-180, 180))[0], 'z range', pts[:, 2].min().round(2), pts[:, 2].max().round(2))
# per angular sector, daub coverage via vertex count of daub vs wattle rods
w = bpy.data.objects['HUT_wattle_rods'].data
wc = np.empty(len(w.vertices) * 3, np.float32); w.vertices.foreach_get('co', wc); wc = wc.reshape(-1, 3)
print('daub verts angle hist', np.histogram(np.degrees(np.arctan2(co[:, 1], co[:, 0])), bins=36, range=(-180, 180))[0])
# z-binned per angle: find holes: angle/z cells with no daub verts
H, xe, ye = np.histogram2d(np.degrees(np.arctan2(co[:, 1], co[:, 0])), co[:, 2], bins=[36, 10], range=[[-180, 180], [0.2, 2.6]])
holes = np.argwhere(H == 0)
print('empty daub cells (angle_deg, z):', [(round(xe[i] + 5), round(ye[j] + 0.12, 2)) for i, j in holes])
