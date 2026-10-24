"""round-3 waterline probe: (A) the cruck posts bear on masonry to the bed, (B) the quay faces have no
see-through joints, (C) no footing stone overhangs the quay faces under the flush runs, (D) the slip-mouth corners.
usage: python -I probe_r3.py <file.blend>"""
import sys

import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
SX, SY = -1.308, -5.973
HX, Y1, YP, XJ0, XJ1 = 3.2 + SX, 9.4 + SY, 6.2 + SY, 0.9 + SX, 5.5 + SY * 0 + SX


def ray(o, d, dist=50.0):
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist)
    return (hit, (loc - Vector(o)).length if hit else None, ob.name if hit else None)


def frange(a, b, st):
    out, v = [], a
    while v <= b + 1e-9:
        out.append(v)
        v += st
    return out


# (A) posts: horizontal rays from the slip centre toward each jamb at the post / respond line
print("(A) cruck posts and responds")
yc = Y1 - 0.12
for side, xs, dx in (("west", HX, -1.0), ("east", HX, 1.0)):
    seen = {}
    for z in frange(-2.40, 0.50, 0.05):
        h, d, nm = ray((xs, yc, z), (dx, 0, 0))
        key = (nm, round(d, 2) if d else None, "below 0" if z < 0 else "above 0")
        seen[key] = seen.get(key, 0) + 1
    print(f"  {side}:", sorted(seen.items(), key=lambda kv: str(kv[0])))
    # straight down under the post centre, from inside the respond's height
    h, d, nm = ray((HX + dx * 2.11, yc, -0.001), (0, 0, -1))
    print(f"  {side} below the post foot: hit {h} dist {d} {nm}")

# (B) quay faces: rays into the face at a 5 cm grid; a pass-through = no hit within 0.45 m behind the face
print("(B) quay faces see-through")
faces = [("outer W", [(x, Y1 + 0.3, z) for x in frange(-4.25, XJ0 - 0.05, 0.05) for z in frange(-2.45, -0.08, 0.025)],
          (0, -1, 0)),
         ("outer E", [(x, Y1 + 0.3, z) for x in frange(XJ1 + 0.45, 8.25, 0.05) for z in frange(-2.45, -0.08, 0.025)],
          (0, -1, 0)),
         ("slip W", [(XJ0 + 0.3, y, z) for y in frange(YP + 0.05, Y1 - 0.40, 0.05) for z in frange(-2.45, -0.08, 0.025)],
          (-1, 0, 0)),
         ("slip E", [(XJ1 - 0.3, y, z) for y in frange(YP + 0.05, Y1 - 0.40, 0.05) for z in frange(-2.45, -0.08, 0.025)],
          (1, 0, 0)),
         ("slip head", [(x, YP + 0.3, z) for x in frange(XJ0 + 0.05, XJ1 - 0.05, 0.05) for z in frange(-2.45, -0.08, 0.025)],
          (0, -1, 0))]
for nm, pts, d in faces:
    n_bad, deep = 0, 0
    for p in pts:
        h, dist, ob = ray(p, d, 2.0)
        if not h or dist > 0.3 + 0.45:
            n_bad += 1
        elif dist > 0.3 + 0.10:
            deep += 1
    print(f"  {nm}: {len(pts)} rays, {n_bad} pass through, {deep} reach the backing (> 10 cm deep)")

# (C) footing overhang: rays straight down 6 cm off the flush faces (into the water)
print("(C) footing overhang over the quay faces")
lines = [("slip W wall", [(XJ0 + 0.06, y) for y in frange(YP + 0.05, Y1 - 0.45, 0.02)]),
         ("slip E wall", [(XJ1 - 0.06, y) for y in frange(YP + 0.05, Y1 - 0.45, 0.02)]),
         ("W pier", [(x, Y1 + 0.06) for x in frange(0.2 + SX + 0.03, XJ0 - 0.03, 0.02)]),
         ("E pier", [(x, Y1 + 0.06) for x in frange(XJ1 + 0.03, 6.2 + SX - 0.03, 0.02)])]
for nm, pts in lines:
    hits = []
    for (x, y) in pts:
        h, d, ob = ray((x, y, 0.8), (0, 0, -1), 3.4)
        if h and 0.8 - d > -0.30:
            hits.append((round(x, 2), round(y, 2), round(0.8 - d, 3), ob))
    print(f"  {nm}: {len(pts)} rays, {len(hits)} hit above z -0.30", hits[:6])

# (D) the slip-mouth corners: diagonal rays at the corner arris
print("(D) slip-mouth corners")
for nm, cx, sgx in (("W", XJ0, -1), ("E", XJ1, 1)):
    worst = 0.0
    for z in frange(-2.45, -0.08, 0.01):
        for off in (-0.02, -0.01, 0.0, 0.01, 0.02):
            o = (cx - sgx * 0.5 + off, Y1 + 0.5, z)
            h, d, ob = ray(o, (sgx, -1, 0), 2.0)
            worst = max(worst, d if h else 9.0)
    print(f"  {nm} corner: deepest diagonal hit {worst - 0.707:.3f} m past the arris line")
