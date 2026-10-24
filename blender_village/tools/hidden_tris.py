"""Estimate buried / never-visible triangles in a building .blend.

Usage:
    /opt/bpyenv/bin/python blender_village/tools/hidden_tris.py <building.blend> [--samples 20000] [--json out.json]

Samples triangles at random and ray-casts each one from a set of exterior
viewpoints: eye-height rings (actors walking around the building), mid and
high rings (crane / aerial shots) and a top view. A triangle counts as visible
if any viewpoint's ray reaches it unobstructed, from its front or back side.
A triangle is tested at its centroid and near each corner. It reports the estimated hidden share per object and overall, plus the share
of triangles buried below ground (centroid below Z = -0.05 m).

This is a sampling estimate (about ±1% at 20k samples). Use it to find which
objects carry hidden geometry, then remove it in the build script.
"""
import argparse
import json
import math
import random
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("blend")
    p.add_argument("--samples", type=int, default=20000)
    p.add_argument("--json")
    return p.parse_args(sys.argv[1:])


def main():
    a = parse()
    bpy.ops.wm.open_mainfile(filepath=a.blend)
    dg = bpy.context.evaluated_depsgraph_get()

    verts, tris, owner = [], [], []
    names = []
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type != "MESH" or ob.name.startswith("_REVIEW"):
            continue
        me = ob.to_mesh()
        me.calc_loop_triangles()
        mw = inst.matrix_world.copy()
        base = len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        name = inst.instance_object.name if inst.is_instance and inst.instance_object else ob.name
        if name not in names:
            names.append(name)
        oi = names.index(name)
        for t in me.loop_triangles:
            tris.append(tuple(base + i for i in t.vertices))
            owner.append(oi)
        ob.to_mesh_clear()

    n = len(tris)
    print(f"triangles: {n:,}  objects: {len(names)}")
    bvh = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    c = (lo + hi) / 2
    r = max((hi - lo).x, (hi - lo).y) / 2
    gz = max(lo.z, 0.0)

    views = []
    for dist_f, z, count in ((1.4, gz + 1.7, 24), (2.5, gz + 1.7, 16), (2.0, gz + (hi.z - gz) * 0.6, 16),
                             (2.2, hi.z + r * 1.2, 12), (1.6, hi.z + r * 2.5, 8)):
        for k in range(count):
            ang = 2 * math.pi * (k + 0.5 * (dist_f > 2)) / count
            views.append(Vector((c.x + math.cos(ang) * r * dist_f, c.y + math.sin(ang) * r * dist_f, z)))
    views.append(Vector((c.x, c.y, hi.z + r * 4)))

    rng = random.Random(1)
    idx = rng.sample(range(n), min(a.samples, n))
    hidden = {}
    total = {}
    buried = 0
    for ti in idx:
        oi = owner[ti]
        total[oi] = total.get(oi, 0) + 1
        p0, p1, p2 = (verts[i] for i in tris[ti])
        cen = (p0 + p1 + p2) / 3
        if cen.z < -0.05:
            buried += 1
            hidden[oi] = hidden.get(oi, 0) + 1
            continue
        nrm = (p1 - p0).cross(p2 - p0)
        nrm = nrm.normalized() if nrm.length > 1e-12 else Vector((0, 0, 1))
        # Test the centroid and three points near the corners, so a triangle
        # that is only partly covered still counts as visible.
        pts = [cen] + [cen + (p - cen) * 0.8 for p in (p0, p1, p2)]
        seen = False
        for side in (1, -1):
            for pt in pts:
                probe = pt + nrm * side * 0.002
                for v in views:
                    if (v - pt).dot(nrm * side) <= 0:
                        continue  # viewpoint is behind this side of the face
                    d = probe - v
                    dist = d.length
                    if dist < 1e-6:
                        continue
                    hit = bvh.ray_cast(v, d / dist, dist + 0.01)
                    if hit[2] == ti or (hit[0] is not None and (hit[0] - pt).length < 0.004):
                        seen = True
                        break
                if seen:
                    break
            if seen:
                break
        if not seen:
            hidden[oi] = hidden.get(oi, 0) + 1

    hid = sum(hidden.values())
    rows = []
    for oi, t in sorted(total.items(), key=lambda kv: -hidden.get(kv[0], 0)):
        share_obj = t / len(idx)
        rows.append({
            "object": names[oi],
            "est_triangles": int(share_obj * n),
            "est_hidden_triangles": int(hidden.get(oi, 0) / len(idx) * n),
            "hidden_pct_of_object": round(100 * hidden.get(oi, 0) / t, 1),
        })
    report = {
        "triangles": n,
        "samples": len(idx),
        "viewpoints": len(views),
        "est_hidden_pct": round(100 * hid / len(idx), 1),
        "est_hidden_triangles": int(hid / len(idx) * n),
        "est_below_ground_pct": round(100 * buried / len(idx), 1),
        "objects": rows,
    }
    print(f"estimated hidden: {report['est_hidden_pct']}% (~{report['est_hidden_triangles']:,} tris), "
          f"below ground: {report['est_below_ground_pct']}%")
    for row in rows[:15]:
        print(f"  {row['object']:<40} hidden {row['hidden_pct_of_object']:5.1f}%  ~{row['est_hidden_triangles']:,} of {row['est_triangles']:,}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
