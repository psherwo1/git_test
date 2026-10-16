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
    raw = n.copy()
    if np.dot(n, d) > 0:                     # back face: report the side facing the ray
        n = -n
    return dict(pos=np.array(hit[0]), normal=n, surface=mats[hit[2]], object=names[hit[2]], dist=float(hit[3]),
                normal_raw=raw)


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


def footprint_normal(probe, pos, normal, up, size, tol=0.10, exclude_objects=()):
    """kit 1.5.0: the surface normal averaged over the 3 x 3 footprint rays of a decal (hits within tol of the decal
    plane, each turned to face the decal side).  Returns (unit normal or None, hits)."""
    r, u, n = decal_frame(normal, up)
    acc = np.zeros(3)
    k = 0
    for a in (-0.4, 0.0, 0.4):
        for b in (-0.4, 0.0, 0.4):
            q = np.asarray(pos, float) + r * (a * size[0]) + u * (b * size[1])
            h = _cast(probe.bvh, probe.mats, probe.names, q + n * tol, -n, 2 * tol)
            if h is None or any(e in h["object"] for e in exclude_objects):
                continue
            acc += _unit(h["normal"])
            k += 1
    if k == 0 or np.linalg.norm(acc) < 1e-9:
        return None, 0
    return _unit(acc), k


STRICT_R11 = dict(
    tol=0.04,                 # every footprint point within 4 cm of the decal plane ...
    need=7,                   # ... and on the declared slot, for >= 7 of 9 points (EVERY slot, shingles included)
    span=0.45,                # footprint grid at +-0.45 x size (the director's inspection grid)
    out=0.15, depth=0.25,     # footprint rays from 15 cm in front, 25 cm behind (first hit of ANY mesh counts)
    dot=0.97,                 # footprint-mean surface normal . anchor normal
    wall_surfaces=("M_daub", "M_timber", "M_timber_weathered"),
    wall_nz=0.15,             # wall-slot anchors (generator normal |n.z| < 0.6): |n.z| <= 0.15
    shifts=((0.0, 0.0), (0.0, -0.05), (0.0, 0.05), (-0.06, 0.0), (0.06, 0.0), (0.0, -0.10), (-0.12, 0.0),
            (0.12, 0.0), (0.0, 0.10), (-0.06, -0.06), (0.06, -0.06), (-0.06, 0.06), (0.06, 0.06)),
    shrink=(1.0, 0.8, 0.65),
)
"""kit 1.6.0 (hut round 11, sign-off audit r10): the strict footprint gate -- validate_anchors(strict=STRICT_R11)."""


def strict_footprint(probe, pos, normal, up, size, surface, tol=0.04, span=0.45, out=0.15, depth=0.25,
                     families=SLOT_FAMILIES):
    """kit 1.6.0: the director's anchor inspection as a gate.  3 x 3 rays at +-span x size, each from `out` in front
    of the decal plane back along -normal (first hit of ANY mesh).  Returns (n_ok, mean_normal or None, n_hit):
    n_ok = points whose first hit carries the declared slot (family) within tol of the plane."""
    r, u, n = decal_frame(normal, up)
    p = np.asarray(pos, float)
    n_ok = 0
    acc = np.zeros(3)
    k = 0
    for a in (-1.0, 0.0, 1.0):
        for b in (-1.0, 0.0, 1.0):
            q = p + r * (a * span * size[0]) + u * (b * span * size[1])
            h = _cast(probe.bvh, probe.mats, probe.names, q + n * out, -n, out + depth)
            if h is None:
                continue
            acc += _unit(h["normal_raw"])            # the face's own normal: a back face counts against it
            k += 1
            if _same_slot(h["surface"], surface, families) and abs(float(np.dot(h["pos"] - q, n))) < tol:
                n_ok += 1
    if k == 0 or np.linalg.norm(acc) < 1e-9:
        return n_ok, None, 0
    return n_ok, _unit(acc), k


def _strict_place(probe, it, hit_pos, n_start, strict, offset, reach, excl, families, clear):
    """kit 1.6.0: search (shrink x shift) for a placement of anchor `it` that passes the strict gate.  The normal is
    the footprint-mean surface normal (wall slots: |n.z| clamped to wall_nz), re-snapped along it.  Returns
    (pos, normal, up, right, size) or None."""
    S = dict(STRICT_R11)
    S.update(strict or {})
    n0 = _unit(it["normal"])
    wall = it["surface"] in S["wall_surfaces"] and abs(float(n0[2])) < 0.6
    up_hint = it["up"] if abs(float(np.dot(_unit(it["up"]), n_start))) < 0.95 else (0.0, 0.0, 1.0)

    def flat(v):
        v = np.array(v, float)
        if wall:
            v[2] = float(np.clip(v[2], -S["wall_nz"], S["wall_nz"]))
        return _unit(v)

    def snap(p, n):
        h = _cast(probe.bvh, probe.mats, probe.names, p + n * reach, -n, 2 * reach)
        if h is None or any(e in h["object"] for e in excl) or not _same_slot(h["surface"], it["surface"], families):
            return None
        return h["pos"]

    r0, u0, nn0 = decal_frame(flat(n_start), up_hint)
    for f_ in S["shrink"]:
        size = (it["size"][0] * f_, it["size"][1] * f_)
        for (dr, du) in S["shifts"]:
            p = snap(hit_pos + r0 * dr + u0 * du, nn0)
            if p is None:
                continue
            n = nn0
            for _ in range(3):
                ok, mean, k = strict_footprint(probe, p + n * offset, n, up_hint, size, it["surface"], S["tol"],
                                               S["span"], S["out"], S["depth"], families)
                if mean is None:
                    break
                n2_ = flat(mean)
                p2 = snap(p, n2_)
                if p2 is None:
                    break
                n, p = n2_, p2
            ok, mean, k = strict_footprint(probe, p + n * offset, n, up_hint, size, it["surface"], S["tol"],
                                           S["span"], S["out"], S["depth"], families)
            if mean is None or ok < S["need"] or float(np.dot(mean, n)) < S["dot"]:
                continue
            if wall and abs(float(n[2])) > S["wall_nz"] + 1e-6:
                continue
            if _cast(probe.bvh, probe.mats, probe.names, p + n * 0.002, n, clear) is not None:
                continue
            r, u, n = decal_frame(n, up_hint)
            return p + n * offset, n, u, r, size
    return None


def validate_anchors(da, probe, apply=True, reach=0.05, offset=0.004, clear=0.15, min_sep=0.25, exclude_objects=(),
                     footprint=True, fp_tol=0.08, fp_any=8, fp_mat=5, strict_types=(), fp_mat_strict=8,
                     shrink=(0.75,), normal_min_dot=0.2, fp_skip_surfaces=("M_roof_shingle",),
                     families=SLOT_FAMILIES, keep_macro_dot=0.8, normal_fp_dot=None, fp_ntol=0.10,
                     fp_skip_need=None, no_tops=None, strict=None):
    """see the module doc.  da: decals.DecalAnchors; probe: decals.SurfaceProbe of the building's meshes.
    keep_macro_dot: the generator's (macro) normal is kept when the hit face's outward normal agrees with it to
    this dot product (adze ridges, lumps and shingle cups do not tilt the decal); otherwise the anchor takes the
    hit's outward normal.
    fp_skip_surfaces: slots whose anchors skip the footprint test (stepped shingle courses never lie within fp_tol
    of one plane; the centre snap, the open-side test and the de-duplication still apply).
    Returns the report dict (counts per reason, `bad`: [(anchor, reason)]); with apply=True da.items is replaced
    and da.validation holds the counts."""
    excl = tuple(exclude_objects)
    strict_cfg = strict            # (the name `strict` is re-bound per anchor by the footprint test below)
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
        if no_tops and any(s_ in hit["object"] for s_ in no_tops.get(it["type"], ())):
            rep.setdefault("implausible", 0)
            rep["implausible"] += 1
            rep["bad"].append((nm, "%s on %s (trodden / implausible surface)" % (it["type"], hit["object"])))
            continue
        if strict_cfg is not None:
            # kit 1.6.0 (hut r11, sign-off audit r10): the strict gate replaces the normal / footprint tests below
            res = _strict_place(probe, it, hit["pos"], hn, strict_cfg, offset, reach, excl, families, clear)
            if res is None:
                rep.setdefault("strict", 0)
                rep["strict"] += 1
                n_ok, mean, _k = strict_footprint(probe, hit["pos"] + hn * offset, hn, it["up"], it["size"],
                                                  it["surface"], families=families)
                rep["bad"].append((nm, "strict gate: fp %d of 9, mean-normal dot %s" % (
                    n_ok, "-" if mean is None else "%.3f" % float(np.dot(mean, hn)))))
                continue
            pos, n, u, r, size = res
            if any(o["type"] == it["type"] and np.linalg.norm(o["pos"] - pos) < min_sep for o in out):
                rep["duplicate"] += 1
                rep["bad"].append((nm, "within %.2f m of another %s" % (min_sep, it["type"])))
                continue
            mv = float(np.linalg.norm(pos - p0))
            rep["max_move"] = max(rep["max_move"], mv)
            rep["snapped"] += mv > 0.005
            rep["shrunk"] += size[0] < it["size"][0] - 1e-9
            new = dict(it)
            new.update(pos=pos, normal=n, up=u, right=r, size=(float(size[0]), float(size[1])))
            out.append(new)
            continue
        if normal_fp_dot is not None:
            # kit 1.5.0 (director r9 #4): the normal is judged against the surface normal AVERAGED over the decal's
            # 3 x 3 footprint, not the single face under the centre (a butt / side face must not pass or steer it)
            up0 = it["up"] if abs(float(np.dot(_unit(it["up"]), n0))) < 0.95 else (0.0, 0.0, 1.0)
            avg, k_ = footprint_normal(probe, hit["pos"], n0, up0, it["size"], fp_ntol, excl)
            if avg is None:
                rep["footprint"] += 1
                rep["bad"].append((nm, "no footprint surface for the normal test"))
                continue
            if float(np.dot(avg, n0)) >= normal_fp_dot:
                hn = n0
            else:
                up1 = up0 if abs(float(np.dot(_unit(up0), avg))) < 0.95 else (0.0, 0.0, 1.0)
                avg2, k2 = footprint_normal(probe, hit["pos"], avg, up1, it["size"], fp_ntol, excl)
                if avg2 is None or float(np.dot(avg2, avg)) < normal_fp_dot:
                    rep.setdefault("normal_off", 0)
                    rep["normal_off"] += 1
                    rep["bad"].append((nm, "normal %.2f off the footprint-mean surface normal" % float(np.dot(avg, n0))))
                    continue
                hn = avg
                rep["renormal"] += 1
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
                hs_ = []
                for a in (-0.4, 0.0, 0.4):
                    for b in (-0.4, 0.0, 0.4):
                        q = hit["pos"] + r * (a * size[0]) + u * (b * size[1])
                        h_ = cast(q + n * fp_tol, -n, 2 * fp_tol)
                        hs_.append("-" if h_ is None else h_["object"].replace("HUT_", "")[:10])
                rep["bad"].append((nm, "footprint off the surface (n.n0 %.2f) %s" % (float(np.dot(n, n0)), hs_)))
                continue
        elif footprint and fp_skip_need:
            # kit 1.5.0: stepped-shingle anchors get a looser footprint test (fp_ntol, >= fp_skip_need of 9 on the slot)
            ok = False
            for f_ in (1.0,) + tuple(shrink):
                s2 = (size[0] * f_, size[1] * f_)
                if footprint_ok(probe, hit["pos"], n, u, s2, it["surface"], fp_ntol, fp_skip_need, fp_skip_need, excl,
                                families):
                    rep["shrunk"] += f_ < 1.0
                    size, ok = s2, True
                    break
            if not ok:
                rep["footprint"] += 1
                rep["bad"].append((nm, "footprint off the surface (shingles)"))
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
