"""Auditor round-8 (read-only): the client's "ONE flowing, continuous curve" checked geometrically on r07 accepted and r08.
1) LIP profile along the eave: for y across the wave, a ray UP from below the lip (x just in front of the front) gives the
   lip underside z(y); a ray DOWN gives the lip top.  Reports the length of the level run (within 1 cm / 2 cm of the peak),
   the slope and curvature of a smoothed z(y), and the front's top edge (max z of the boards / blocker per y bin).
2) COURSE SPACING over the crown: rays down along the slope line at the wave centre and at a plain reference line;
   course butts = upward steps in z(x) beyond the local trend; spacing reported against the plain exposure.
   blender -b --python aud_arch_r08.py -- <r07.blend> <r08.blend>"""
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    dg = bpy.context.evaluated_depsgraph_get(); per = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
        co = np.empty(len(m.vertices) * 3, np.float64); m.vertices.foreach_get("co", co)
        tv = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", tv)
        per[o.name] = (co.reshape(-1, 3), tv.reshape(-1, 3)); o.evaluated_get(dg).to_mesh_clear()
    return per


def bvh_of(per, names):
    V, T, off = [], [], 0
    for n in names:
        co, tv = per[n]; V.append(co); T.append(tv + off); off += len(co)
    return BVHTree.FromPolygons(np.concatenate(V).tolist(), np.concatenate(T).tolist(), all_triangles=True)


def smooth(z, k=9):
    w = np.ones(k) / k
    zp = np.pad(z, k // 2, mode="edge")
    return np.convolve(zp, w, mode="valid")


for tag, path in (("r07", a[0]), ("r08", a[1])):
    per = load(path)
    cov = bvh_of(per, ["HARB_roof_covering"])
    print(f"===== {tag} {path}")
    ys = np.arange(-3.6, 0.45, 0.01)
    front = bvh_of(per, [n for n in per if "eyebrow0" in n])
    profs = {}
    # (a) lip TOP: first covering hit of a ray DOWN just in front of the boards; (b) front TOP EDGE: the highest z at
    #     which a horizontal ray (+x) from outside hits the eyebrow front objects only (lip excluded)
    for lab, fn in (("LIP TOP (ray down at x=-1.30)", lambda y: cov.ray_cast(Vector((-1.30, y, 8.0)), Vector((0, 0, -1)), 9.0)),
                    ("LIP TOP (ray down at x=-1.27)", lambda y: cov.ray_cast(Vector((-1.27, y, 8.0)), Vector((0, 0, -1)), 9.0))):
        zz = []
        for y in ys:
            h = fn(y); zz.append(np.nan if h[0] is None else h[0].z)
        profs[lab] = np.array(zz)
    ft = []
    for y in ys:
        zt = np.nan
        for z in np.arange(4.75, 3.55, -0.004):
            h = front.ray_cast(Vector((-2.5, y, z)), Vector((1, 0, 0)), 1.45)
            if h[0] is not None:
                zt = z; break
        ft.append(zt)
    profs["FRONT TOP EDGE (eyebrow objects, horizontal rays)"] = np.array(ft)
    for lab, z in profs.items():
        ok = ~np.isnan(z)
        base = np.nanmedian(np.r_[z[:25], z[-25:]]) if "LIP" in lab else np.nanmin(z)
        pk = np.nanmax(z); ypk = ys[np.nanargmax(z)]
        print(f"{lab}: base z {base:.3f}, peak z {pk:.3f} at y {ypk:.2f}, rise {pk-base:.3f} m, misses {(~ok).sum()}")
        for tol in (0.005, 0.01, 0.02):
            sel = ys[ok & (z >= pk - tol)]
            print(f"   within {tol*100:.1f} cm of the peak: y {sel.min():.2f}..{sel.max():.2f} = {sel.max()-sel.min():.2f} m")
        zf = z.copy(); zf[~ok] = base
        s = smooth(zf, 11)
        d1 = np.gradient(s, ys); d2 = np.gradient(d1, ys)
        kap = -d2 / (1 + d1 ** 2) ** 1.5
        for half in (0.4, 0.27):     # the window span: +-0.40 m (frame outer) and +-0.27 m about the crown
            m = ok & (np.abs(ys - ypk) <= half)
            print(f"   over y = crown +-{half:.2f} m: curvature min {kap[m].min():.2f} /m, median {np.median(kap[m]):.2f} /m; "
                  f"drop at the ends {pk - z[m].min():.3f} m")
        print("   z(y) every 0.10 m:", " ".join(f"{y:.1f}:{v:.2f}" for y, v in zip(ys[::10], z[::10])))
    # course spacing along the slope (x up the slope) at the crown and at a plain line
    for yl, lab in ((-1.57, "crown"), (-1.0, "crown+0.57"), (2.4, "plain N")):
        xs = np.arange(-1.9, 1.85, 0.002)
        z = []
        for x in xs:
            h = cov.ray_cast(Vector((x, yl, 20.0)), Vector((0, 0, -1)), 30.0)
            z.append(np.nan if h[0] is None else h[0].z)
        z = np.array(z)
        dz = np.diff(z)
        trend = np.array([np.nanmedian(dz[max(0, i - 25):i + 26]) for i in range(len(dz))])   # local slope
        jumps = np.where(dz - trend > 0.006)[0]
        step = np.where(dz - trend > 0.006, trend, dz)                       # the surface without the butt steps
        sarc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.nan_to_num(step)))])
        # merge adjacent indices
        js = []
        for j in jumps:
            if not js or j - js[-1][-1] > 3:
                js.append([j])
            else:
                js[-1].append(j)
        xb = np.array([xs[g[0]] for g in js])
        sp = np.diff(xb)
        print(f"COURSES {lab} y={yl}: {len(xb)} butts; x {np.round(xb, 3).tolist()}")
        print(f"   plan spacing (m): {np.round(sp, 3).tolist()}")
        ib = np.array([g[0] for g in js])
        sa = np.diff(sarc[ib])
        print(f"   ARC spacing along the surface (m): {np.round(sa, 3).tolist()}")
print("DONE")

