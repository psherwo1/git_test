"""Read-only probe for the r2 look test: per-object material slots, tri counts and, for chosen
slots, which 3D direction the UV U and V axes follow (area-weighted, per face).

Usage: python.exe -I r2_probe.py <file.blend> [--slots M_wattle,M_timber_weathered] [--match blade,sail]
"""
import sys
import argparse

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--slots", default="")
ap.add_argument("--match", default="")
a = ap.parse_args(argv)
bpy.ops.wm.open_mainfile(filepath=a.src)
slots = [s for s in a.slots.split(",") if s]
match = [m for m in a.match.split(",") if m]

for o in sorted((o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render), key=lambda o: o.name):
    me = o.data
    mats = [m.name if m else "-" for m in me.materials]
    hit_slot = [s for s in slots if s in mats]
    hit_name = any(m in o.name.lower() for m in match)
    if not (hit_slot or hit_name):
        continue
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    line = f"{o.name:40s} tris={nt:7d} mats={mats}"
    if not hit_slot and not hit_name:
        print(line)
        continue
    # per-triangle dP/du, dP/dv
    uvl = me.uv_layers.active
    if uvl is None:
        print(line, "NO UV")
        continue
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    uv = np.zeros(len(me.loops) * 2); uvl.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    lt = np.zeros(nt * 3, np.int64); me.loop_triangles.foreach_get("loops", lt); lt = lt.reshape(-1, 3)
    vt = np.zeros(nt * 3, np.int64); me.loop_triangles.foreach_get("vertices", vt); vt = vt.reshape(-1, 3)
    mi = np.zeros(nt, np.int64); me.loop_triangles.foreach_get("material_index", mi)
    p0, p1, p2 = co[vt[:, 0]], co[vt[:, 1]], co[vt[:, 2]]
    t0, t1, t2 = uv[lt[:, 0]], uv[lt[:, 1]], uv[lt[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    d1, d2 = t1 - t0, t2 - t0
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    ok = np.abs(det) > 1e-12
    r = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    dpu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r[:, None]
    dpv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r[:, None]
    area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
    for si, sname in enumerate(mats):
        if slots and sname not in slots and not hit_name:
            continue
        sel = (mi == si) & ok
        if not sel.any():
            continue
        w = area[sel]
        nu = np.linalg.norm(dpu[sel], axis=1); nv = np.linalg.norm(dpv[sel], axis=1)
        uz = np.abs(dpu[sel][:, 2]) / np.maximum(nu, 1e-9)
        vz = np.abs(dpv[sel][:, 2]) / np.maximum(nv, 1e-9)
        print(f"{line}\n    slot {sname}: area {w.sum():.2f} m2, |dP/du| {np.average(nu, weights=w):.2f} m/uv, "
              f"|dP/dv| {np.average(nv, weights=w):.2f} m/uv, U-vertical {np.average(uz, weights=w):.2f}, "
              f"V-vertical {np.average(vz, weights=w):.2f}")
