"""Director round-5 regression probe: compare every mesh of the round-5 blend with the accepted round-4 blend.
python -I dir_regress_r05.py -- <r04_blend> <r05_blend>
Per object: vertex count, bbox, and (same count) max vertex move plus the bbox of moved vertices (> 1 mm).
Changed counts: bbox of vertices that are not within 1 mm of any r04 vertex (KD-tree)."""
import sys

import bpy
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1:]


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        e = o.evaluated_get(dg); m = e.to_mesh()
        n = len(m.vertices)
        v = np.empty(n * 3, dtype=np.float64); m.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
        mw = np.array(o.matrix_world)
        v = v @ mw[:3, :3].T + mw[:3, 3]
        m.calc_loop_triangles()
        out[o.name] = (v, len(m.loop_triangles))
        e.to_mesh_clear()
    return out


A = load(argv[0]); B = load(argv[1])
print("R04 objects", len(A), "tris", sum(t for _, t in A.values()))
print("R05 objects", len(B), "tris", sum(t for _, t in B.values()))
for n in sorted(set(A) | set(B)):
    if n not in B:
        print(f"REMOVED {n}"); continue
    vb, tb = B[n]
    bb = f"x {vb[:,0].min():6.2f}..{vb[:,0].max():6.2f} y {vb[:,1].min():6.2f}..{vb[:,1].max():6.2f} z {vb[:,2].min():5.2f}..{vb[:,2].max():5.2f}" if len(vb) else ""
    if n not in A:
        print(f"NEW     {n:34s} v={len(vb):6d} t={tb:6d} {bb}"); continue
    va, ta = A[n]
    if len(va) == len(vb):
        d = np.abs(va - vb).max(axis=1) if len(va) else np.zeros(0)
        mv = d > 1e-3
        if not mv.any():
            print(f"SAME    {n:34s} v={len(vb):6d} t={tb:6d}"); continue
        w = vb[mv]
        print(f"MOVED   {n:34s} v={len(vb):6d} t={ta}->{tb} moved {int(mv.sum())} max {d.max():.3f} m  in x {w[:,0].min():6.2f}..{w[:,0].max():6.2f} "
              f"y {w[:,1].min():6.2f}..{w[:,1].max():6.2f} z {w[:,2].min():5.2f}..{w[:,2].max():5.2f}")
    else:
        kd = KDTree(len(va))
        for i, p in enumerate(va):
            kd.insert(p, i)
        kd.balance()
        off = np.array([kd.find(p)[2] > 1e-3 for p in vb])
        if not off.any():
            print(f"RECOUNT {n:34s} v={len(va)}->{len(vb)} t={ta}->{tb} all r05 verts on r04 verts"); continue
        w = vb[off]
        print(f"CHANGED {n:34s} v={len(va)}->{len(vb)} t={ta}->{tb} new-position verts {int(off.sum())} in x {w[:,0].min():6.2f}..{w[:,0].max():6.2f} "
              f"y {w[:,1].min():6.2f}..{w[:,1].max():6.2f} z {w[:,2].min():5.2f}..{w[:,2].max():5.2f}")
