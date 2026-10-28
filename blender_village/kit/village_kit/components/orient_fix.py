"""components.orient_fix -- kit 1.21 (v7 cottage round 5): re-orient INVERTED open-backed stone shells.

    orient_open_islands(g, parts=("_stones",), min_score=0.25)
        KIT COMPONENT (post step; a recipe opts in): every linked face island of the matching meshes is scored --
        an OPEN shell (a coursed wall stone, its back open into the mortar body) by the area-weighted mean of its
        face normals along (island centroid - open-boundary centroid), i.e. away from its open back; a CLOSED shell
        by its normals against the radial direction from its centroid.  An island scoring below -min_score is
        flipped whole.  -> number of islands flipped (logged per object).

Why: geom.finalize's strict_clean recalculates normals (bmesh recalc_face_normals), whose outside test is
unreliable on open shells; now and then a wall stone comes out facing INTO the wall.  Cycles' clay shades it
normally, but the review's void twin shows its back faces (yellow), and with Unreal's single-sided materials it
is a hole in the wall (round 4: the W inside corner by the cottage's door).  Not called by any existing recipe,
so no other building changes.
"""
import numpy as np

from ..core import log


def orient_closed_slabs(g, parts=("_deck",), reach=0.12):
    """KIT COMPONENT (post step, kit 1.21): each face of the matching meshes (thin CLOSED slabs: a roof deck, a
    soffit board) whose normal points INTO its own slab is flipped -- a ray from the face centre along its normal
    that meets, within `reach` m, a face of the same mesh looking the same way has run through the slab's inside.
    -> faces flipped."""
    import bpy  # noqa: F401
    import bmesh
    from mathutils.bvhtree import BVHTree
    total = 0
    for ob in [o for o in g.coll.all_objects if o.type == "MESH" and any(p in o.name for p in parts)]:
        if ob.data.users != 1 or not len(ob.data.polygons):
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        bvh = BVHTree.FromBMesh(bm)
        bad = []
        for f in bm.faces:
            n = f.normal
            if n.length < 0.5:
                continue
            c = f.calc_center_median()
            hit, hn, hi, _d = bvh.ray_cast(c + n * 1e-4, n, reach)
            if hit is not None and hi != f.index and hn.dot(n) > 0.2:
                bad.append(f)
        for f in bad:
            f.normal_flip()
        if bad:
            bm.to_mesh(ob.data)
            ob.data.update()
        bm.free()
        log(f"  orient_closed_slabs {ob.name}: {len(bad)} inward face(s) flipped")
        total += len(bad)
    return total


def _islands(bm):
    seen = np.zeros(len(bm.faces), bool)
    for f in bm.faces:
        if seen[f.index]:
            continue
        isl, stack = [], [f]
        seen[f.index] = True
        while stack:
            h = stack.pop()
            isl.append(h)
            for e in h.edges:
                for k in e.link_faces:
                    if not seen[k.index]:
                        seen[k.index] = True
                        stack.append(k)
        yield isl


def orient_open_islands(g, parts=("_stones",), min_score=0.25, face_dot=0.5):
    """see the module doc.  face_dot: in an open shell, a face whose normal looks back toward the open side
    (normal . front < -face_dot, after the shell's own orientation) is flipped on its own."""
    import bpy  # noqa: F401
    import bmesh
    total = 0
    for ob in [o for o in g.coll.all_objects if o.type == "MESH" and any(p in o.name for p in parts)]:
        if ob.data.users != 1 or not len(ob.data.polygons):
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        n_flip = n_face = 0
        for isl in _islands(bm):
            C = np.array([f.calc_center_median() for f in isl])
            N = np.array([f.normal for f in isl])
            A = np.array([f.calc_area() for f in isl])
            if A.sum() <= 0:
                continue
            c = (C * A[:, None]).sum(0) / A.sum()
            bnd = {v for f in isl for e in f.edges if len(e.link_faces) < 2 for v in e.verts}
            if len(bnd) >= 3:
                d = c - np.array([v.co for v in bnd]).mean(0)
                ln = float(np.linalg.norm(d))
                if ln < 1e-6:
                    continue
                dh = d / ln
                dots = N @ dh
                score = float((A * dots).sum() / A.sum())
                # an open shell has no face looking straight back at its open side: the faces of a MIXED shell
                # (recalc left part of it inverted) that do are flipped one by one, the rest as the whole shell
                sgn = -1.0 if score < -min_score else 1.0
                bad = [f for f, dt in zip(isl, dots) if sgn * dt < -face_dot]
                for f in bad:
                    f.normal_flip()
                n_face += len(bad)
                if sgn < 0:
                    for f in isl:
                        f.normal_flip()
                    n_flip += 1
                continue
            else:
                R = C - c
                rl = np.linalg.norm(R, axis=1)
                ok = rl > 1e-6
                if not ok.any():
                    continue
                score = float((A[ok] * ((R[ok] / rl[ok, None]) * N[ok]).sum(1)).sum() / A[ok].sum())
            if score < -min_score:
                for f in isl:
                    f.normal_flip()
                n_flip += 1
        if n_flip or n_face:
            bm.to_mesh(ob.data)
            ob.data.update()
        bm.free()
        log(f"  orient_open_islands {ob.name}: {n_flip} inverted island(s) flipped, {n_face} single face(s)")
        total += n_flip
    return total
