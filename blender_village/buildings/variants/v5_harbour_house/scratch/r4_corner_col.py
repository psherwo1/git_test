import sys, bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
xj0, y1 = float(sys.argv[2]), float(sys.argv[3])
for off in (0.03, 0.05, 0.08, 0.12, 0.20, 0.28):
    bad = []
    for i in range(0, 95):
        z = -2.45 + i * 0.025
        o = Vector((xj0 - off, y1 + 0.3, z))
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, o, Vector((0, -1, 0)), distance=20.0)
        d = (loc - o).length if hit else None
        if not hit or d > 0.75:
            bad.append((round(z, 3), round(d, 2) if d else None, ob.name if hit else None))
    print(f"off {off}: {len(bad)} deep", bad[:5])
