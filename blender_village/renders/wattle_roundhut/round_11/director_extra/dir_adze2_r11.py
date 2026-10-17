"""Director check r11 (2): adze relief on the lintel front, horizontal scans; detrended groove depth.
Run: blender -b <blend> --python dir_adze2_r11.py
"""
import bpy
from mathutils import Vector

scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def scan(pts, d):
    ys = []
    names = {}
    for p in pts:
        hit, loc, nor, fi, ob, _ = scn.ray_cast(dg, p, d, distance=3)
        if hit:
            names[ob.name] = names.get(ob.name, 0) + 1
            if ob.name == "HUT_door_frame":
                ys.append((loc - p).dot(d))
        else:
            names["<none>"] = names.get("<none>", 0) + 1
    return ys, names


def groove(ds, w=25):
    # detrend with a 2*w-sample window: depth below the window's most-proud point minus the linear trend
    rel = []
    for i in range(len(ds)):
        seg = ds[max(0, i - w): i + w]
        rel.append(ds[i] - min(seg))
    rel.sort()
    return rel


for z in [2.30, 2.33, 2.36, 2.40, 2.44, 2.48]:
    pts = [Vector((-0.75 + i * 0.002, -5.0, z)) for i in range(750)]
    ys, names = scan(pts, Vector((0, 1, 0)))
    if len(ys) > 60:
        r = groove(ys)
        print("LINTEL z", z, "n", len(ys), "p50 %.4f p90 %.4f p99 %.4f max %.4f" % (r[len(r)//2], r[int(len(r)*.9)], r[int(len(r)*.99)], r[-1]), names)
    else:
        print("LINTEL z", z, names)
# jamb/outer-post fronts, horizontal scans across member width (diagonal grooves cross both ways)
for z in [0.8, 1.2, 1.6, 2.0]:
    pts = [Vector((0.45 + i * 0.001, -5.0, z)) for i in range(700)]
    ys, names = scan(pts, Vector((0, 1, 0)))
    r = groove(ys, 15) if ys else [0]
    print("RIGHT z", z, "n", len(ys), "p90 %.4f max %.4f" % (r[int(len(r)*.9)], r[-1]), names)
