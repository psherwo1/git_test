import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
scn = bpy.context.scene
# ---- hygiene ----
meshes = [ob for ob in scn.objects if ob.type == "MESH"]
bad_xf, no_uv, no_mask, zero = [], [], [], 0
datas = set()
for ob in meshes:
    if any(abs(v) > 1e-6 for v in ob.location) or any(abs(v) > 1e-6 for v in ob.rotation_euler) or any(abs(v - 1) > 1e-6 for v in ob.scale):
        bad_xf.append(ob.name)
    me = ob.data
    datas.add(me.name)
    if not me.uv_layers:
        no_uv.append(ob.name)
    ca = me.color_attributes
    m = ca.get("Mask")
    if m is None or m.domain != "CORNER" or ca.active_color_name != "Mask" or ca.render_color_index != list(ca).index(m):
        no_mask.append(ob.name)
    a = np.zeros(len(me.polygons))
    me.polygons.foreach_get("area", a)
    zero += int((a < 1e-10).sum())
print("HYG objects", len(meshes), "unique meshes", len(datas), "bad_xf", bad_xf, "no_uv", no_uv, "no_mask", no_mask, "zero_area", zero)
print("COLL", [c.name for c in bpy.data.collections])
# ---- soaker support ----
o = bpy.data.objects["LONG_cone_soakers"]
P = np.array([v.co[:] for v in o.data.vertices])
print("soaker verts", len(P), "z min", P[:, 2].min().round(3))
V, T, n = [], [], 0
for ob in meshes:
    if ob.name == o.name:
        continue
    mm = ob.data
    mm.calc_loop_triangles()
    co = np.array([v.co[:] for v in mm.vertices])
    lt = np.array([t.vertices[:] for t in mm.loop_triangles])
    if len(lt) == 0:
        continue
    V.append(co); T.append(lt + n); n += len(co)
V = np.concatenate(V); T = np.concatenate(T)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
low = P[P[:, 2] < 2.42]
free5 = sum(1 for p in low if bvh.ray_cast(Vector(p) + Vector((0, 0, -0.001)), Vector((0, 0, -1)), 0.05)[0] is None)
free50 = sum(1 for p in low if bvh.ray_cast(Vector(p) + Vector((0, 0, -0.001)), Vector((0, 0, -1)), 0.5)[0] is None)
print("low (<2.42) soaker verts", len(low), "free within 5cm", free5, "free within 0.5m", free50)
allfree = [p for p in P if bvh.ray_cast(Vector(p) + Vector((0, 0, -0.001)), Vector((0, 0, -1)), 0.05)[0] is None]
print("all soaker verts with nothing within 5cm below:", len(allfree), "of", len(P))
if allfree:
    F = np.array(allfree)
    print("   x", F[:, 0].min().round(2), F[:, 0].max().round(2), "y", F[:, 1].min().round(2), F[:, 1].max().round(2), "z", F[:, 2].min().round(2), F[:, 2].max().round(2))
# ---- anchors ----
da = [ob for ob in scn.objects if ob.name.startswith("DA_")]
print("anchors", len(da))
for ob in da:
    if ob.name.startswith("DA_moss"):
        nrm = -(ob.matrix_world.to_3x3() @ Vector((0, 0, 1)))
        print("  ", ob.name, tuple(round(c, 2) for c in ob.matrix_world.translation), "into", tuple(round(c, 3) for c in nrm), ob.get("surface"))
