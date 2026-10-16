"""village_kit.anchor_validate -- kit 1.3.0: snap and validate decal anchors against the built meshes.

Producer note 11 wants every decal anchor physically plausible.  The placement helpers in village_kit.decals aim
their rays well, but an anchor can still end up floating (its ray hit an underside, then it was shifted down its up
axis), proud of the part it decorates, buried under another part (a stone top under the timber sill), on a backing
mesh seen through a weave, or doubled up with a neighbour.  validate_anchors() is the gate for that (director, hut
round 8 #3):

    snap        a ray from `reach` outside the anchor back along -normal finds the surface under it, within `reach`
                (5 cm) on either side of the anchor plane; no surface -> dropped.  The anchor moves onto the hit
                (+ `offset`, no z-fight in previews).
    surface     the hit must be on the declared palette slot and not on an `exclude_objects` mesh.
    outward     the anchor takes the hit's normal, turned to the side it decorates; the spot must be open for
                `clear` metres along +normal (else it is buried -> dropped).
    footprint   3 x 3 rays over the decal rectangle: >= fp_any of 9 must find a surface within fp_tol of the anchor
                plane and >= fp_mat (fp_mat_strict for `strict_types`) the declared slot; a failing decal is retried
                at each `shrink` factor, else dropped.
    duplicates  same-type anchors closer than `min_sep` are thinned (the earlier one stays).

build_building(spec) runs it when spec["decal_validate"] is True or a dict of these keyword arguments (opt-in, so
the anchors of a building that does not ask for it are unchanged); without it, it only REPORTS (apply=False) in
the build log, so every building can see how many of its anchors fail.  The keep's own gate,
decals.snap_anchors(), is a separate, stricter option a component can call itself.
"""
import numpy as np

from .decals import _unit, decal_frame


def _cast(bvh, mats, names, origin, direction, dist):
    from mathutils import Vector
    d = _unit(direction)
    hit = bvh.ray_cast(Vector(tuple(map(float, origin))), Vector(tuple(map(float, d))), dist)
    if hit[0] is None:
        return None
    n = np.array(hit[1])
    if np.dot(n, d) > 0:                     # back face: report the side facing the ray
        n = -n
    return dict(pos=np.array(hit[0]), normal=n, surface=mats[hit[2]], object=names[hit[2]], dist=float(hit[3]))


SLOT_FAMILIES = (("M_timber", "M_timber_weathered"),)
"""palette slots one decal may straddle (the same material family)."""


def _same_slot(a, b, families=SLOT_FAMILIES):
    return a == b or any(a in f and b in f for f in families)


def footprint_ok(probe, pos, normal, up, size, surface, tol=0.08, need_any=8, need_mat=5, exclude_objects=(),
                 families=SLOT_FAMILIES):
    """3 x 3 rays over a decal rectangle (+-0.4 of its size) centred on pos: True when >= need_any of 9 find a
    surface within tol of the decal plane (not on an exclude_objects mesh) and >= need_mat the slot `surface`."""
    r, u, n = decal_frame(normal, up)
    n_any = n_mat = 0
    for a in (-0.4, 0.0, 0.4):
        for b in (-0.4, 0.0, 0.4):
            q = np.asarray(pos, float) + r * (a * size[0]) + u * (b * size[1])
            h = _cast(probe.bvh, probe.mats, probe.names, q + n * tol, -n, 2 * tol)
            if h is None or any(e in h["object"] for e in exclude_objects):
                continue
            n_any += 1
            n_mat += _same_slot(h["surface"], surface, families)
    return n_any >= need_any and n_mat >= need_mat


def validate_anchors(da, probe, apply=True, reach=0.05, offset=0.004, clear=0.15, min_sep=0.25, exclude_objects=(),
                     footprint=True, fp_tol=0.08, fp_any=8, fp_mat=5, strict_types=(), fp_mat_strict=8,
                     shrink=(0.75,), normal_min_dot=0.2, fp_skip_surfaces=("M_roof_shingle",),
                     families=SLOT_FAMILIES, keep_macro_dot=0.8):
    """see the module doc.  da: decals.DecalAnchors; probe: decals.SurfaceProbe of the building's meshes.
    keep_macro_dot: the generator's (macro) normal is kept when the hit face's outward normal agrees with it to
    this dot product (adze ridges, lumps and shingle cups do not tilt the decal); otherwise the anchor takes the
    hit's outward normal.
    fp_skip_surfaces: slots whose anchors skip the footprint test (stepped shingle courses never lie within fp_tol
    of one plane; the centre snap, the open-side test and the de-duplication still apply).
    Returns the report dict (counts per reason, `bad`: [(anchor, reason)]); with apply=True da.items is replaced
    and da.validation holds the counts."""
    excl = tuple(exclude_objects)
    rep = dict(checked=len(da.items), snapped=0, max_move=0.0, renormal=0, shrunk=0, no_surface=0, wrong_surface=0,
               excluded=0, occluded=0, footprint=0, duplicate=0, bad=[])
    out = []
    cnt = {}

    def cast(o, d, dist):
        return _cast(probe.bvh, probe.mats, probe.names, o, d, dist)

    def bad_obj(name):
        return any(e in name for e in excl)

    def fp_ok(pos, r, u, n, size, surf, strict):
        return footprint_ok(probe, pos, n, u, size, surf, fp_tol, fp_any, fp_mat_strict if strict else fp_mat,
                            excl, families)

    for it in da.items:
        cnt[it["type"]] = cnt.get(it["type"], 0) + 1
        nm = it.get("name", "DA_%s_%03d" % (it["type"], cnt[it["type"]]))
        n0 = _unit(it["normal"])
        p0 = np.asarray(it["pos"], float)
        hit = cast(p0 + n0 * reach, -n0, 2 * reach)
        if hit is None:
            rep["no_surface"] += 1
            rep["bad"].append((nm, "no surface within %.0f cm" % (reach * 100)))
            continue
        if bad_obj(hit["object"]):
            rep["excluded"] += 1
            rep["bad"].append((nm, "on backing mesh " + hit["object"]))
            continue
        if not _same_slot(hit["surface"], it["surface"], families):
            rep["wrong_surface"] += 1
            rep["bad"].append((nm, "hit %s (%s), declared %s" % (hit["surface"], hit["object"], it["surface"])))
            continue
        hn = _unit(hit["normal"])                        # outward: turned toward the side the anchor is on
        dn = float(np.dot(hn, n0))
        if dn < normal_min_dot:
            rep["renormal"] += 1
        if dn >= keep_macro_dot:
            hn = n0
        up_hint = it["up"] if abs(float(np.dot(_unit(it["up"]), hn))) < 0.95 else (0.0, 0.0, 1.0)
        r, u, n = decal_frame(hn, up_hint)
        pos = hit["pos"] + n * offset
        if cast(hit["pos"] + n * 0.002, n, clear) is not None:
            rep["occluded"] += 1
            rep["bad"].append((nm, "buried: occluded within %.0f cm" % (clear * 100)))
            continue
        size = it["size"]
        if footprint and it["surface"] not in fp_skip_surfaces:
            strict = it["type"] in strict_types
            ok = fp_ok(hit["pos"], r, u, n, size, it["surface"], strict)
            if not ok:
                for f_ in shrink:
                    s2 = (size[0] * f_, size[1] * f_)
                    if fp_ok(hit["pos"], r, u, n, s2, it["surface"], strict):
                        size, ok = s2, True
                        rep["shrunk"] += 1
                        break
            if not ok:
                rep["footprint"] += 1
                rep["bad"].append((nm, "footprint off the surface"))
                continue
        mv = float(np.linalg.norm(pos - p0))
        if any(o["type"] == it["type"] and np.linalg.norm(o["pos"] - pos) < min_sep for o in out):
            rep["duplicate"] += 1
            rep["bad"].append((nm, "within %.2f m of another %s" % (min_sep, it["type"])))
            continue
        rep["max_move"] = max(rep["max_move"], mv)
        rep["snapped"] += mv > 0.005
        new = dict(it)
        new.update(pos=pos, normal=n, up=u, right=r, size=(float(size[0]), float(size[1])))
        out.append(new)
    rep["kept"] = len(out)
    if apply:
        da.items = out
        da.validation = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rep.items() if k != "bad"}
    return rep
