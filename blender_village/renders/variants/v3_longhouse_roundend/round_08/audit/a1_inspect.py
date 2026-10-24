import sys, json
import bpy
import numpy as np
BL = r"C:\GitHubDesktop\git_test\blender_village\buildings\variants\v3_longhouse_roundend\redesign_r8_wip\v3_longhouse_roundend_r8.blend"
bpy.ops.wm.open_mainfile(filepath=BL)
tot = 0
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != "MESH":
        print("NONMESH", ob.name, ob.type)
        continue
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tot += nt
    V = np.array([ob.matrix_world @ v.co for v in me.vertices]) if len(me.vertices) else np.zeros((1, 3))
    mats = [m.name for m in me.materials if m]
    att = [a.name for a in me.attributes if a.name.lower() == "mask"]
    print(f"{ob.name:40s} tris {nt:7d} min {np.round(V.min(0),2)} max {np.round(V.max(0),2)} mats {mats} mask {att} hide {ob.hide_render}")
print("TOTAL", tot)
for k in ("LONG_finial",):
    ob = bpy.data.objects.get(k)
    if ob:
        V = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
        print("FINIAL centre", V.mean(0), V.min(0), V.max(0))
print("custom props", {k: (str(v)[:200]) for k, v in bpy.context.scene.items()})
