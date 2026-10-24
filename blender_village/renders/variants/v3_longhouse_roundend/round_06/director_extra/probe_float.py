"""Floating-piece probe at both crossings: every mesh island of the cone covering / structure within the crossing
region; min gap from the island to any other geometry (other objects + other islands)."""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
X0, X1, Y0, Y1, Z0, Z1 = 1.0, 3.8, 2.2, 4.2, 2.2, 3.4
TARGETS = ("LONG_roof_shingles", "LONG_roof_starter", "LONG_battens", "LONG_rafters", "LONG_roof_underlap",
           "LONG_cone_soakers", "LONG_body_roof_abutment")
allV, allT, allI = [], [], []
n = 0
iid = 0
islands = []
for ob in bpy.context.scene.objects:
    if ob.type != "MESH":
        continue
    me = ob.data
    me.calc_loop_triangles()
    co = np.array([v.co[:] for v in me.vertices])
    if len(co) == 0:
        continue
    lt = np.array([t.vertices[:] for t in me.loop_triangles])
    # island labels via union-find on edges
    par = np.arange(len(co))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            par[a] = b
    lab = np.array([find(i) for i in range(len(co))])
    c = co[lt].mean(1)
    sel = (c[:, 0] > X0) & (c[:, 0] < X1) & (np.abs(c[:, 1]) > Y0) & (np.abs(c[:, 1]) < Y1) & (c[:, 2] > Z0) & (c[:, 2] < Z1)
    if not sel.any():
        continue
    lt = lt[sel]
    tl = lab[lt[:, 0]]
    _, inv = np.unique(tl, return_inverse=True)
    tid = inv + iid
    if ob.name in TARGETS:
        for k in np.unique(tid):
            islands.append((ob.name, k))
    iid = tid.max() + 1
    allV.append(co); allT.append(lt + n); allI.append(tid); n += len(co)
V = np.concatenate(allV); T = np.concatenate(allT); I = np.concatenate(allI)
print("region tris", len(T), "target islands", len(islands))
res = []
for name, k in islands:
    m = I == k
    vi = np.unique(T[m].ravel())
    other = T[~m]
    bvh = BVHTree.FromPolygons(V.tolist(), other.tolist(), all_triangles=True)
    d = min(bvh.find_nearest(Vector(V[j]))[3] for j in vi)
    P = V[vi]
    res.append((d, name, k, P.mean(0), P[:, 2].min(), len(vi)))
res.sort(key=lambda r: -r[0])
for d, name, k, c, zmin, nv in res[:15]:
    print(f"gap {d*100:6.2f} cm  {name:26s} isl {k}  centre ({c[0]:.2f},{c[1]:.2f},{c[2]:.2f}) zmin {zmin:.3f} nv {nv}")
print("islands with gap > 1 cm:", sum(1 for r in res if r[0] > 0.01), " > 3 cm:", sum(1 for r in res if r[0] > 0.03))
