"""Were the triangles that r05 had and r06 lost (comb / tower stones / wing covering) visible?  For each lost centroid,
cast 400 rays (Fibonacci sphere, from 15 m out) at it in the r06 blend: 'reach' = the ray gets within 3 mm of the
centroid before its first hit, i.e. the point would be seen from outside through the gap the lost face leaves.
blender -b --python dir_cullvis_r06.py -- <r05_blend> <r06_blend>"""
import math, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
NAMES = ["HARB_roof_comb", "HARB_tower_stones", "HARB_wing_roof_covering"]
def tris(path):
    bpy.ops.wm.open_mainfile(filepath=path); dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for n in NAMES:
        o = bpy.data.objects[n]; e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); mw = o.matrix_world
        V = [mw @ v.co for v in m.vertices]
        out[n] = {tuple(round(c, 3) for c in (V[t.vertices[0]] + V[t.vertices[1]] + V[t.vertices[2]]) / 3):
                  ((V[t.vertices[0]] + V[t.vertices[1]] + V[t.vertices[2]]) / 3) for t in m.loop_triangles}
        e.to_mesh_clear()
    return out
A = tris(a[0]); B = tris(a[1])
lost = {n: [A[n][k] for k in A[n] if k not in B[n]] for n in NAMES}
bpy.ops.wm.open_mainfile(filepath=a[1]); scn = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
N = 400; dirs = []
for i in range(N):
    z = 1 - 2 * (i + 0.5) / N; r = math.sqrt(1 - z * z); ph = i * math.pi * (3 - math.sqrt(5))
    dirs.append(Vector((r * math.cos(ph), r * math.sin(ph), z)))
for n in NAMES:
    vis = 0
    for c in lost[n]:
        reach = 0
        for d in dirs:
            if d.z < -0.2:
                continue
            o = c + d * 15.0
            ok, p, *_ = scn.ray_cast(dg, o, -d)
            if not ok or (p - o).length >= 15.0 - 0.003:
                reach += 1; print(f"   DIR {n} ({c.x:.3f},{c.y:.3f},{c.z:.3f}) d=({d.x:.3f},{d.y:.3f},{d.z:.3f})")
        vis += reach > 0
        if reach:
            print(f"   VISIBLE {n} at ({c.x:.3f},{c.y:.3f},{c.z:.3f}) from {reach} dirs")
    print(f"CULLVIS {n}: lost {len(lost[n])}, visible {vis}", flush=True)

