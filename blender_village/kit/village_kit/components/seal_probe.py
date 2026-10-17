"""components.seal_probe -- the see-through check for roof junctions (kit 1.7.3, v2_tiered_hall round 4).

    through_seal_probe(g, ...)    KIT CHECK (producer note 6, rubric axis 4 "no see-through pixels")
        For every registered roof tier and every body that rises through it (`through`, plus every body it was
        flashed against), exterior rays are fired at the tier's covering inside an annulus round the body
        (default 0-0.6 m outside the body face): seeded points everywhere round the body where the covering really
        exists, each hit from n_dir of the 24 compass directions x elevations 10-80 deg (directions closer than
        min_incidence = 10 deg to grazing the local covering are not fired: at a few degrees a ray threads the air
        between chunky shingle pieces and battens, a sub-pixel artefact of any layered covering).  Each ray is
        aimed at a point on the tier's base surface.  A ray stopped before that point is sealed.  A ray that passes
        it is a LEAK when it then reaches nothing (the sky), a point more than `depth` (0.6 m) under this tier's
        surface (through the roof: the hall interior, the wall face under the eave), or a point inside a declared
        body more than `depth` below the target (the hollow body).  A ray that comes out over the covering again
        and lands on an exterior surface is not a see-through.  Passes:
          * 'see-through' (always, fails the build): all meshes of the building (what a camera sees);
          * 'backing' (backing=True, report only unless fail='all'): the covering removed (shingles, hips,
            starters, under-laps, battens) -- where a deck, flashing, structure or body is missing under the
            covering (today: the deck seams under the hip boards and under round-tier collars are reported).
        A see-through leak raises SealError naming the tier, the body, the plan point, the height, the ray
        direction and what the ray reached (fail=False only logs).  Deterministic (seeded sampling).  Returns a list
        of per-junction records.  Run by tier_finish.tier_hidden_cull AFTER the cull (and in FAST builds), so neither
        a module nor the cull can ship a see-through.  About 1 M rays, 12-20 s on v2.
        v2 round 4 proof: on the round-3 delivered geometry it fails with 8 leaks, 'skirt1' round 'tur_nw' at
        (-4.29, 2.50, 3.95) (the director's k05 slit) and (-2.66, 4.65, 3.67) (the NE-flank slit); with the
        kit 1.7.3 eave_deck_lap + flashing drip it passes with 0 leaks on all four junctions.
"""
import math

import numpy as np

from ..core import log

COVERING = ("shingles", "_hips", "starter", "underlap", "battens")


class SealError(RuntimeError):
    """exterior rays pass a roof covering next to a body that rises through it (kit 1.7.3)."""


def _mesh_arrays(objs):
    Vs, Ts, names = [], [], []
    nv = 0
    for ob in objs:
        me = ob.data
        me.calc_loop_triangles()
        if not len(me.loop_triangles):
            continue
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", lt)
        Vs.append(co)
        Ts.append(lt.reshape(-1, 3) + nv)
        names += [ob.name] * len(me.loop_triangles)
        nv += len(co)
    return np.concatenate(Vs), np.concatenate(Ts), np.array(names, dtype=object)


def _bvh(V, T):
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)


def _targets(g, tname, t, body, ring, density, rng):
    """seeded points on tier t's base surface in the annulus ring=(d0, d1) outside body's face, where the covering
    really exists and the body really rises through it."""
    from .tier_frame import _covered, roof_z
    roof = t["roof"]
    R = float(body.r_nom(0.5 * (body.z0 + body.z1)))
    area = 2 * math.pi * (R + 0.5 * (ring[0] + ring[1])) * (ring[1] - ring[0])
    n = int(area * density)
    th = rng.uniform(0, 2 * math.pi, n)
    d = rng.uniform(ring[0], ring[1], n)
    z = np.full(n, 0.5 * (body.z0 + body.z1))
    for _ in range(3):                              # the junction height round the body (as roof_flashing)
        P = body.point(th, z, d=d)
        zz = roof_z(roof, P[:, 0], P[:, 1])
        z = np.where(np.isfinite(zz), zz, body.z0)
    P = body.point(th, z, d=d)
    zr, ok = _covered(g, t, P[:, 0], P[:, 1])
    ok &= np.isfinite(zr) & (zr > body.z0 + 0.05) & (zr < body.z1)
    P = np.column_stack([P[:, 0], P[:, 1], np.where(ok, zr, 0.0)])
    return P[ok]


def through_seal_probe(g, ring=(0.0, 0.6), el_deg=(10, 20, 30, 45, 60, 80), n_az=24, density=6000.0, n_dir=8,
                       depth=0.6, far=30.0, backing=False, fail=True, seed=4242, report=8, min_incidence=10.0):
    """KIT CHECK: see the module doc.  ring: annulus (m outside the body face); el_deg / n_az: the exterior ray
    directions; density: target points per m2 of annulus; n_dir: directions tried per target point (seeded subset
    of the n_az x el grid); depth: how far (m, vertical) below the base surface a ray may travel before it must
    hit something."""
    import time
    from mathutils import Vector
    t0 = time.time()
    rng = np.random.default_rng(seed)
    objs = [o for o in g.coll.all_objects if o.type == "MESH"]
    V, T, own = _mesh_arrays(objs)
    passes = [("see-through", _bvh(V, T), own)]
    if backing:
        keep = np.array([not any(s in nm for s in COVERING) for nm in own])
        passes.append(("backing", _bvh(V, T[keep]), own[keep]))
    az = np.radians(np.arange(n_az) * 360.0 / n_az + 7.5)
    el = np.radians(np.asarray(el_deg, float))
    A, E = np.meshgrid(az, el, indexing="ij")
    DIRS = np.column_stack([(np.cos(E) * np.cos(A)).ravel(), (np.cos(E) * np.sin(A)).ravel(), np.sin(E).ravel()])
    DEG = np.column_stack([np.degrees(A).ravel(), np.degrees(E).ravel()])
    out, bad = [], []
    for tname, t in g.roofs.items():
        bodies = list(dict.fromkeys(list(t.get("through", ())) + list(t.get("flashings", ()))))
        for bname in bodies:
            body = g.body(bname)
            P = _targets(g, tname, t, body, ring, density, rng)
            if not len(P):
                continue
            pick = np.argsort(rng.random((len(P), len(DIRS))), axis=1)[:, :n_dir]
            # the covering's local normal at every target (base surface gradient): rays closer than min_incidence
            # to grazing the covering are not fired -- at a few degrees they thread the air between chunky shingle
            # pieces and battens for a metre (a sub-pixel artefact of any layered covering, not a junction hole)
            from .tier_frame import roof_z
            e_ = 0.02
            zx = (roof_z(t["roof"], P[:, 0] + e_, P[:, 1]) - roof_z(t["roof"], P[:, 0] - e_, P[:, 1])) / (2 * e_)
            zy = (roof_z(t["roof"], P[:, 0], P[:, 1] + e_) - roof_z(t["roof"], P[:, 0], P[:, 1] - e_)) / (2 * e_)
            with np.errstate(invalid="ignore"):
                zx = np.nan_to_num(zx, nan=0.0, posinf=0.0, neginf=0.0)
                zy = np.nan_to_num(zy, nan=0.0, posinf=0.0, neginf=0.0)
            NRM = np.column_stack([-zx, -zy, np.ones(len(P))])
            NRM /= np.linalg.norm(NRM, axis=1)[:, None]
            s_min = math.sin(math.radians(min_incidence))
            for pname, bvh, owner in passes:
                leaks = []
                n_ray = 0
                passed = []                             # (target, direction, hit or None) of rays that passed T
                for i in range(len(P)):
                    Tp = P[i]
                    for j in pick[i]:
                        dvec = DIRS[j]
                        if float(dvec @ NRM[i]) < s_min:
                            continue
                        O = Tp + dvec * far
                        h = bvh.ray_cast(Vector(O), Vector(-dvec), 4.0 * far)
                        n_ray += 1
                        if h[0] is None:
                            passed.append((Tp, j, None))
                        elif h[3] > far + 1e-4:
                            passed.append((Tp, j, (np.array(h[0]), str(owner[h[2]]).replace(g.prefix + "_", ""))))
                # classify what a ray that passed the covering reaches: nothing (the sky), a point under this tier
                # deeper than `depth` (through the roof), or a point inside a body deeper than `depth` below the
                # target (the hollow body).  A grazing ray that runs under a few shingles and comes out over the
                # covering again (it lands on an exterior surface above the roof) is not a see-through.
                from .tier_frame import roof_z
                allb = list(g.bodies)
                for Tp, j, hit in passed:
                    if hit is None:
                        leaks.append((Tp, j, "sky", None))
                        continue
                    H, hob = hit
                    zr = float(roof_z(t["roof"], H[0], H[1]))
                    under = np.isfinite(zr) and H[2] < zr - depth
                    inside = bool(g.inside_any(H[None], allb, margin=0.02)[0]) and H[2] < Tp[2] - depth
                    if under or inside:
                        leaks.append((Tp, j, f"interior ({hob} at {H[0]:.2f}, {H[1]:.2f}, {H[2]:.2f})", None))
                rec = dict(tier=tname, body=bname, pass_=pname, rays=n_ray, targets=len(P), leaks=len(leaks),
                           passed=len(passed),
                           points=[(tuple(float(x) for x in np.round(L[0], 3)), tuple(float(x) for x in DEG[L[1]]),
                                    L[2]) for L in leaks[:report]])
                out.append(rec)
                log(f"  seal probe [{pname}] {tname} / {bname}: {len(P)} points, {n_ray} rays, {len(passed)} grazing "
                    f"pass(es), {len(leaks)} leak(s)" + (f" e.g. {rec['points'][:3]}" if leaks else ""))
                if leaks and (pname == "see-through" or fail == "all"):
                    bad.append(rec)
    log(f"  seal probe: {sum(r['rays'] for r in out)} rays on {len(out)} junction passes in {time.time() - t0:.1f} s")
    if bad and fail:
        msg = "; ".join(
            f"[{r['pass_']}] tier {r['tier']!r} round body {r['body']!r}: {r['leaks']} of {r['rays']} rays leak, "
            f"first at plan ({r['points'][0][0][0]:.2f}, {r['points'][0][0][1]:.2f}) z {r['points'][0][0][2]:.2f} "
            f"from az {r['points'][0][1][0]:.0f} el {r['points'][0][1][1]:.0f} to the {r['points'][0][2]}"
            for r in bad)
        raise SealError(f"see-through at a roof/body junction (producer note 6): {msg}.  Close it in the module: "
                        f"run the deck / structure to the body face under the flashing apron, or widen the apron.")
    return out
