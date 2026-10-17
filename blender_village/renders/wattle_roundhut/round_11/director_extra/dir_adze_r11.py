"""Director check r11: adze-groove relief depth on door-frame front faces (note 11, entrance >= 1 cm).
Run: blender -b <blend> --python dir_adze_r11.py
Casts rays in +Y from the front along horizontal lines on each frame member and reports the depth range.
"""
import bpy
from mathutils import Vector

scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
fr = bpy.data.objects["HUT_door_frame"]
lo = fr.matrix_world @ Vector(fr.bound_box[0]); hi = fr.matrix_world @ Vector(fr.bound_box[6])
print("FRAME bbox", [round(v, 3) for v in lo], [round(v, 3) for v in hi])
# vertical scan lines at several x across members; z 0.6-2.0 step 2 mm
for x in [-0.98, -0.62, -0.58, 0.58, 0.62, 0.98, 0.0]:
    zs = [0.6 + i * 0.002 for i in range(700)] if x != 0.0 else [2.29 + i * 0.001 for i in range(120)]
    ds = []
    for z in zs:
        o = Vector((x, -5.0, z))
        hit, loc, nor, fi, ob, _ = scn.ray_cast(dg, o, Vector((0, 1, 0)), distance=3)
        if hit and ob.name == "HUT_door_frame":
            ds.append(loc.y)
    if not ds:
        print("x", x, "no frame hits"); continue
    # local relief: depth relative to running max over 6 cm window (groove depth)
    rel = []
    w = 30 if x != 0.0 else 30
    for i in range(len(ds)):
        seg = ds[max(0, i - w): i + w]
        rel.append(ds[i] - min(seg))
    rel.sort()
    print("x", x, "hits", len(ds), "y range", round(min(ds), 4), round(max(ds), 4),
          "groove p50 %.4f p90 %.4f p99 %.4f max %.4f" % (rel[len(rel)//2], rel[int(len(rel)*.9)], rel[int(len(rel)*.99)], rel[-1]))
