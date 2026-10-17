"""See-through probe along a gable ridge (verification helper, 4_verify; reads only).

Usage: <bpy-python> ridge_probe.py <file.blend> <x0> <x1> [<y_ridge>=0]

Targets on the ridge plane y = y_ridge, x in [x0, x1], at heights that are UNDER some covering (a ray straight down
from 2 m above the roof's top hits something above the target).  From each target, rays leave toward both sides
(azimuth +-Y, +-30 deg) at elevations 0-60 deg; a ray that leaves the target in BOTH directions (forward to the sky
and backward to the sky) without hitting anything is a line of sight straight through the ridge: see-through.
"""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main(path, x0, x1, yr=0.0, zlo=None, zhi=None):
    bpy.ops.wm.open_mainfile(filepath=path)
    V, T, off = [], [], 0
    zmax = 0.0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        me = o.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        t = np.zeros(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get("vertices", t)
        V.append(co); T.append(t.reshape(-1, 3) + off); off += len(co)
        zmax = max(zmax, float(co[:, 2].max()))
    V = np.vstack(V); T = np.vstack(T)
    bvh = BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)
    n_t = n_r = 0
    leaks = []
    for x in np.linspace(x0, x1, 61):
        for z in np.linspace(zmax - 1.6 if zlo is None else zlo, zmax if zhi is None else zhi, 33):
            P = Vector((float(x), yr, float(z)))
            h = bvh.ray_cast(Vector((float(x), yr, zmax + 2.0)), Vector((0, 0, -1)), 50.0)
            if h[0] is None or h[0][2] <= z + 1e-3:
                continue                                   # nothing above: open sky, not under the covering
            # the target must be in free air (not inside a solid): nearest hit upward is a back face -> inside
            hu = bvh.ray_cast(P, Vector((0, 0, 1)), 50.0)
            if hu[0] is not None and hu[1][2] > 0:
                continue
            n_t += 1
            for az in (-30, 0, 30):
                for el in (0, 10, 20, 35, 50, 60):
                    a, e = np.radians(az), np.radians(el)
                    d = Vector((float(np.sin(a) * np.cos(e)), float(np.cos(a) * np.cos(e)), float(np.sin(e))))
                    for sgn in (1, -1):
                        dd = Vector((d.x * sgn, d.y * sgn, d.z))      # the ray toward +Y or -Y, rising
                        n_r += 1
                        f = bvh.ray_cast(P, dd, 100.0)
                        b = bvh.ray_cast(P, -dd, 100.0)
                        if f[0] is None and b[0] is None:
                            leaks.append((round(float(x), 2), round(float(z), 3), az, el, sgn))
    print(f"RIDGE {path}: {n_t} targets under the covering, {n_r} rays, {len(leaks)} straight see-through lines")
    if leaks:
        xs = sorted({L[0] for L in leaks}); zs = sorted({L[1] for L in leaks})
        import collections; print("  by elevation", collections.Counter(L[3] for L in leaks), "by az", collections.Counter(L[2] for L in leaks)); print(f"  x range {xs[0]}..{xs[-1]} ({len(xs)} stations), z range {zs[0]}..{zs[-1]}; e.g. {leaks[:6]}")


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(a[0], float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 0.0, *(float(v) for v in a[4:6]))


