"""v4 r4 probe 2: what the eye-level back-face hits under the house eave are (rafters, starter, shingles).
For each back-face hit: object, location (house radius, z, azimuth), and whether the hit face's neighbourhood is open
(boundary edges on the hit polygon = a hole cut by the cull or an open-modelled part).  Also: boundary-edge counts of
V4H_rafters / _roof_starter by house radius band, i.e. where those parts are open."""
import math
import sys
from collections import Counter

import bpy  # noqa: I001
import bmesh
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
H = Vector((-1.462, 0.214, 0.0))
M = Vector((2.82, 1.36, 0.0))
OBS = ("V4H_rafters", "V4H_roof_starter", "V4H_roof_shingles")
bms = {}
for n in OBS:
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[n].data)
    bm.faces.ensure_lookup_table()
    bms[n] = bm
hits = []
for R in (4.0, 6.0):
    for az in range(-180, 180, 15):
        a = math.radians(az)
        cam = H + Vector((math.cos(a) * R, math.sin(a) * R, 1.65))
        if (cam - M).to_2d().length < 2.4:
            continue
        for da in range(-24, 25, 2):
            for zi in range(0, 11):
                aa = a + math.radians(da)
                for rr in (2.45, 2.60, 2.75):
                    p = H + Vector((math.cos(aa) * rr, math.sin(aa) * rr, 2.45 + 0.05 * zi))
                    d = (p - cam).normalized()
                    hit, loc, nrm, idx, ob, Mx = scn.ray_cast(dg, cam, d)
                    if hit and ob.name in OBS and nrm.dot(d) > 0:
                        f = bms[ob.name].faces[idx]
                        openf = any(e.is_boundary for e in f.edges)
                        rel = loc - H
                        hits.append((ob.name, round(rel.to_2d().length, 2), round(loc.z, 2),
                                     int(round(math.degrees(math.atan2(rel.y, rel.x)))), openf,
                                     round(f.normal.z, 2), R, az))
c = Counter((h[0], h[4]) for h in hits)
print("BACKHITS (object, hit polygon has boundary edge):", dict(c))
for n in OBS:
    hs = [h for h in hits if h[0] == n]
    if hs:
        rs = [h[1] for h in hs]
        zs = [h[2] for h in hs]
        nz = Counter(round(h[5], 1) for h in hs)
        print(f"  {n}: r {min(rs)}..{max(rs)}  z {min(zs)}..{max(zs)}  face normal z {dict(nz)}")
        print("   sample", hs[:8])
for n in OBS:
    bm = bms[n]
    cnt = Counter()
    for e in bm.edges:
        if not e.is_boundary:
            continue
        m = (e.verts[0].co + e.verts[1].co) / 2 - H
        cnt[round(m.to_2d().length * 2) / 2] += 1
    print(f"BOUNDARY {n} by house radius (0.5 m bins):", sorted(cnt.items()))
