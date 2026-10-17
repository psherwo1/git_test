"""Auditor round-4 probe 2 (read-only): ridge-comb slits, slip-wall foot slots, tower foot-ring seating.
python -I aud_probe2_r04.py <blend>"""
import sys
from collections import deque

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
dg = bpy.context.evaluated_depsgraph_get()
objs = [o for o in bpy.data.objects if o.type == "MESH"]
V, T, OWN, off = [], [], [], 0
for i, o in enumerate(objs):
    m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", co)
    tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
    V.append(co.reshape(-1, 3)); T.append(tv.reshape(-1, 3) + off); OWN.append(np.full(len(tv) // 3, i))
    off += len(m.vertices); o.evaluated_get(dg).to_mesh_clear()
V = np.concatenate(V); T = np.concatenate(T); OWN = np.concatenate(OWN)
bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True)
name = lambda h: objs[OWN[h[2]]].name  # noqa: E731


def enclosed(mask):
    """mask True = ray passed (miss).  Return the misses not 4-connected to the grid's border."""
    h, w = mask.shape; seen = np.zeros_like(mask); q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True; q.append((yy, xx))
    return mask & ~seen


def runs(col):
    """widths of consecutive True runs in a 1D bool array"""
    out, n = [], 0
    for v in col:
        if v:
            n += 1
        elif n:
            out.append(n); n = 0
    if n:
        out.append(n)
    return out


# ---- 1. ridge comb slits, looked at square-on from the side (rays along -X / +X), 5 mm grid ---------------------
STEP = 0.005
for label, axis, lo, hi, other, zlo, zhi, dirs in (
        ("MAIN ridge (along Y)", 1, -5.9, 3.55, 1.892, 6.3, 8.2, ((1, 0, 0), (-1, 0, 0))),
        ("WING ridge (along X)", 0, -8.2, -2.2, -5.973, 4.3, 5.4, ((0, 1, 0), (0, -1, 0)))):
    for d in dirs:
        D = Vector(d)
        us = np.arange(lo, hi, STEP); zs = np.arange(zlo, zhi, STEP)
        miss = np.zeros((len(zs), len(us)), bool)
        for j, u in enumerate(us):
            for i, z in enumerate(zs):
                p = [0.0, 0.0, z]; p[axis] = u; p[1 - axis] = other
                o = Vector(p) - D * 12.0
                miss[i, j] = bvh.ray_cast(o, D, 30.0)[0] is None
        enc = enclosed(miss[::-1])           # row 0 = top
        cols = enc.any(0)
        wid = runs(cols)
        hts = [int(enc[:, j].sum()) for j in range(len(us)) if cols[j]]
        print(f"COMB {label} rays {tuple(d)}: enclosed see-through cells {int(enc.sum())} (5 mm), "
              f"slits {len(wid)}, slit widths cm: max {max(wid) * 0.5 if wid else 0:.1f}, "
              f">=2 cm: {sum(1 for w in wid if w >= 4)}, >=3 cm: {sum(1 for w in wid if w >= 6)}; "
              f"tallest column {max(hts) * 0.5 if hts else 0:.1f} cm", flush=True)
        if wid:
            js = np.nonzero(cols)[0]
            print("    first slit positions (u):", [round(float(us[j]), 3) for j in js[:: max(1, len(js) // 12)]][:14])
        np.save(bpy.path.abspath("//") + "x", np.zeros(1)) if False else None

# ---- 2. slip-wall foot: horizontal rays from the slip centre into both slip walls -------------------------------
for side, x0, dx in (("W slip wall (x -0.608)", 1.9, -1.0), ("E slip wall (x 4.392)", 1.9, 1.0)):
    deep, total, worst = 0, 0, []
    for y in np.arange(0.35, 3.40, 0.01):
        for z in np.arange(-0.035, 0.40, 0.005):
            h = bvh.ray_cast(Vector((x0, y, z)), Vector((dx, 0, 0)), 10.0)
            total += 1
            face = -0.608 if dx < 0 else 4.392
            if h[0] is None or abs(h[0].x - face) > 0.25:
                deep += 1
                worst.append((round(float(y), 2), round(float(z), 3), None if h[0] is None else round(h[0].x, 2),
                              None if h[0] is None else name(h)))
    print(f"SLIPFOOT {side}: {total} rays z -0.035..0.40, {deep} go > 25 cm past the face", flush=True)
    for w in worst[:12]:
        print("    ", w)
    # through the wall: from 5 cm in front of the face, does the ray reach the hall side wall's inner face?
    thru = []
    for (yy, zz, hx, hn) in worst:
        h = bvh.ray_cast(Vector((x0, yy, zz)), Vector((dx, 0, 0)), 10.0)
        thru.append(None if h[0] is None else round(h[0].x, 2))
    if thru:
        print("     deepest hit x", min(t for t in thru if t is not None) if dx < 0 and any(t is not None for t in thru)
              else max(t for t in thru if t is not None) if any(t is not None for t in thru) else None,
              " misses", sum(1 for t in thru if t is None))

# ---- 3. tower foot ring: radial rays at the stone-top / timber-belt junction ------------------------------------
C = Vector((-1.808, -5.973, 0.0))
slot = []
for a in np.radians(np.arange(0, 360, 1.0)):
    u = Vector((np.cos(a), np.sin(a), 0.0))
    for z in np.arange(6.70, 7.20, 0.005):
        o = C + u * 4.0 + Vector((0, 0, z))
        h = bvh.ray_cast(o, -u, 4.0)
        if h[0] is None:
            continue
        r = (h[0] - Vector((C.x, C.y, h[0].z))).length
        slot.append((float(np.degrees(a)), float(z), r, name(h)))
S = np.array([(s[0], s[1], s[2]) for s in slot])
print("RING radial hits", len(S))
for a0 in range(0, 360, 30):
    sel = S[(S[:, 0] >= a0) & (S[:, 0] < a0 + 30)]
    print(f"   az {a0:3d}-{a0+30:3d}: hit radius min {sel[:, 2].min():.3f} max {sel[:, 2].max():.3f}")
deep = [s for s in slot if s[2] < 1.85]
print("RING rays that reach r < 1.85 m (inside the belt line):", len(deep), deep[:10])
# vertical gap between the foot-ring underside and the stone top at each azimuth
gaps = []
for a in np.radians(np.arange(0, 360, 2.0)):
    u = Vector((np.cos(a), np.sin(a), 0.0))
    for rr in (2.05, 2.15, 2.25):
        o = C + u * rr + Vector((0, 0, 6.2))
        h1 = bvh.ray_cast(o, Vector((0, 0, 1)), 2.0)            # first thing above the stone? (start inside wall?)
        o2 = C + u * rr + Vector((0, 0, 8.0))
        h2 = bvh.ray_cast(o2, Vector((0, 0, -1)), 2.5)
        if h2[0] is not None:
            gaps.append((round(float(np.degrees(a))), rr, round(h2[0].z, 3), name(h2)))
print("RING down-rays from 8.0 m at r 2.05/2.15/2.25 (first hit):")
from collections import Counter  # noqa: E402
print("   ", Counter((g[1], g[3]) for g in gaps).most_common(12))
print("DONE")
