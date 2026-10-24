import sys, bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
x0, x1, y = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
def ray(o, d, dist):
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector(o), Vector(d), distance=dist)
    return (round((loc - Vector(o)).length, 3), ob.name.replace("HARB_", "")) if hit else (None, None)
x = x0
while x <= x1 + 1e-6:
    up = ray((x, y, 2.6), (0, 0, 1), 3.0)          # from inside the slip / pier zone up: what is overhead
    zt = None
    # find the tie underside: march from 3.30 upward
    h = ray((x, y, 3.55), (0, 0, -1), 1.0)            # from inside the tie (3.42-3.74) down: its underside
    zb = 3.55 - h[0] if h[0] is not None else None
    dn = ray((x, y, zb - 0.002), (0, 0, -1), 4.0) if zb else (None, None)
    print(f"x {x:6.2f}: underside {zb if zb is None else round(zb,3)} ({h[1]})  below: gap {dn[0]} -> {dn[1]}")
    x += 0.05

