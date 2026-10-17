"""village_kit.decal_gate -- producer note 11 plausibility gate for decal anchors (kit 1.3.0, hilltop keep round 8;
director keep round-7 rule).  A separate module so decals.py (shared by every building) is unchanged.

    snap_anchors(da, probe, ...)   ray-snap every anchor of a decals.DecalAnchors set to the first exterior surface
                                   along its intended normal; reject |offset| > 1.5 cm, alignment < 0.85, interior /
                                   blocker hits and enclosed spots; de-duplicate same-type anchors closer than 0.3 m.
    cast_raw(probe, origin, direction, dist=10.0)  a decals.SurfaceProbe ray cast that reports the face's OWN normal (not flipped
                                   toward the ray), so back faces and reversed shells can be rejected.

A generator may store item['macro'] (the wall / radial / slope normal the decal should project along) on an anchor
before the gate runs; otherwise the anchor's own normal is used.
"""
import math

import numpy as np

from .decals import _unit, decal_frame

REJECT_OBJECTS = ("interior", "blocker", "_block")


def cast_raw(probe, origin, direction, dist=10.0):
    from mathutils import Vector
    d = _unit(direction)
    hit = probe.bvh.ray_cast(Vector(tuple(map(float, origin))), Vector(tuple(map(float, d))), dist)
    if hit[0] is None:
        return None
    return dict(pos=np.array(hit[0]), normal=np.array(hit[1]), surface=probe.mats[hit[2]],
                object=probe.names[hit[2]], dist=float(hit[3]))


def _fib_dirs(n, axis, max_deg):
    """n deterministic directions inside a cone of half-angle max_deg round axis (golden-angle spiral)."""
    axis = _unit(axis)
    t = np.cross(axis, (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0))
    t = _unit(t)
    b = np.cross(axis, t)
    i = np.arange(n) + 0.5
    ct = 1 - (1 - math.cos(math.radians(max_deg))) * i / n
    st = np.sqrt(np.clip(1 - ct * ct, 0, 1))
    ph = i * math.pi * (3 - math.sqrt(5))
    return ct[:, None] * axis + st[:, None] * (np.cos(ph)[:, None] * t + np.sin(ph)[:, None] * b)


WALK_TYPES = ("lichen", "moss")


def door_walk_zone(center, outward, along, half_width, depth=1.5, inset=0.35, z_max=0.6):
    """kit 1.5.0 (keep round 9, director r8 must-fix 5): the trodden walking zone in front of a door -- a plan
    rectangle `half_width` either side of the door centre line (door clear width / 2 + 0.1 m), from `inset` m inside
    the threshold line to `depth` m out from it, up to z_max m above the ground (thresholds, steps, pavings)."""
    o = np.asarray(outward, float)[:2]
    o = o / max(np.linalg.norm(o), 1e-9)
    a = np.asarray(along, float)[:2]
    a = a / max(np.linalg.norm(a), 1e-9)
    return dict(c=np.asarray(center, float)[:2], o=o, a=a, hw=float(half_width), d0=-float(inset),
                d1=float(depth), z_max=float(z_max))


def in_walk_zone(it, zones, n_s=5):
    """True when any point of anchor `it`'s decal rectangle (size along right / up, sampled n_s x n_s) lies inside
    one of the walk zones (door_walk_zone)."""
    if not zones:
        return False
    n = _unit(it.get("macro", it["normal"]))
    r, u, n = decal_frame(n, it["up"])
    w, h = it["size"]
    f = np.linspace(-0.5, 0.5, n_s)
    P = np.asarray(it["pos"], float)[None, None, :] + f[:, None, None] * w * r[None, None, :] + \
        f[None, :, None] * h * u[None, None, :]
    P = P.reshape(-1, 3)
    for zn in zones:
        d = (P[:, :2] - zn["c"][None]) @ zn["o"]
        s = (P[:, :2] - zn["c"][None]) @ zn["a"]
        if np.any((np.abs(s) <= zn["hw"]) & (d >= zn["d0"]) & (d <= zn["d1"]) & (P[:, 2] <= zn["z_max"])):
            return True
    return False


def snap_anchors(da, probe, max_offset=0.015, min_align=0.85, dedupe=0.3, lift=0.004, reach=0.25,
                 search=(0.0, 0.03, 0.06, 0.10, 0.15), reject=REJECT_OBJECTS, exposure_dist=12.0, exposure_rays=24,
                 min_escape=2, log=None, clear=0.15, footprint_fn="auto", shrink=(0.75, 0.55),
                 fp_skip=("M_roof_shingle",), walk_zones=None, walk_types=WALK_TYPES):
    """Every anchor is ray-snapped to the FIRST surface along its intended normal: a ray from `reach` m outside the
    anchor back along -normal.  The hit is accepted only if
      * the face's own normal agrees with the intended normal (dot >= min_align; back faces / reversed shells and
        perpendicular faces fail),
      * the hit object is not an interior or blocker surface (names containing a `reject` token),
      * the spot is exposed: at least `min_escape` of `exposure_rays` rays in the 75 deg cone round the normal
        travel exposure_dist m without meeting geometry (an enclosed interior fails),
      * the anchor ends `lift` m off the face (lift <= max_offset).
    If the anchor's own spot fails, nearby spots in its surface plane (rings of `search` radii) are tried; an anchor
    with no valid spot is dropped.  Same-type anchors closer than `dedupe` m are then thinned (first kept).
      * nothing stands within `clear` m in front of the spot (not tucked under / behind another part),
      * the decal rectangle lies on the surface: footprint_fn (default: anchor_validate.footprint_ok, 3 x 3 rays
        within 8 cm of the decal plane) at full size or one of the `shrink` factors (slots in fp_skip are exempt).
      * kit 1.5.0: walk_zones (list of door_walk_zone) -- a `walk_types` anchor (lichen, moss) whose decal
        rectangle overlaps a door's walking zone is rejected (default None: no zone test, the 1.3.0 gate).
    Returns (kept, dropped) counts; da.items is replaced in place."""
    assert lift <= max_offset
    if footprint_fn == "auto":
        try:
            from .anchor_validate import footprint_ok as footprint_fn
        except ImportError:
            footprint_fn = None
    kept, dropped = [], []
    ang = np.radians(np.arange(8) * 45.0 + 22.5)
    for it in da.items:
        n = _unit(it.get("macro", it["normal"]))
        r, u, n = decal_frame(n, it["up"])
        p0 = np.asarray(it["pos"], float)
        cands = [p0]
        for rad in search[1:]:
            cands.extend(p0 + rad * (np.cos(a) * r + np.sin(a) * u) for a in ang)
        ok = None
        why = "no hit"
        for c in cands:
            h = cast_raw(probe, c + n * reach, -n, reach * 2.0)
            if h is None:
                continue
            if any(t in h["object"].lower() for t in reject):
                why = "interior/blocker " + h["object"]
                continue
            al = float(np.dot(h["normal"], n))
            if al < min_align:
                why = f"align {al:.2f} {h['object']}"
                continue
            q = h["pos"] + n * lift
            esc = 0
            for dv in _fib_dirs(exposure_rays, n, 75.0):
                if cast_raw(probe, q + dv * 0.01, dv, exposure_dist) is None:
                    esc += 1
                    if esc >= min_escape:
                        break
            if esc < min_escape:
                why = "enclosed " + h["object"]
                continue
            if clear > 0 and (cast_raw(probe, h["pos"] + n * 0.002, n, clear) is not None or
                              cast_raw(probe, h["pos"] + h["normal"] * 0.002, h["normal"], clear) is not None):
                why = f"occluded within {clear * 100:.0f} cm"
                continue
            size = it["size"]
            if footprint_fn is not None and h["surface"] not in fp_skip:
                good = False
                for f_ in (1.0,) + tuple(shrink):
                    s2 = (size[0] * f_, size[1] * f_)
                    if footprint_fn(probe, h["pos"], n, u, s2, h["surface"]):
                        size, good = s2, True
                        break
                if not good:
                    why = "footprint off the surface"
                    continue
            ok = (q, h, size)
            break
        if ok is None:
            dropped.append((it["type"], np.round(p0, 2).tolist(), why))
            continue
        q, h, size = ok
        it = dict(it)
        it.pop("macro", None)
        it["pos"], it["normal"], it["up"], it["right"] = q, n, u, r
        it["size"] = (float(size[0]), float(size[1]))
        if walk_zones and it["type"] in walk_types and in_walk_zone(it, walk_zones):
            # kit 1.5.0: lichen / moss never grow on the trodden line in front of a door
            dropped.append((it["type"], np.round(q, 2).tolist(), "door walking zone"))
            continue
        if h["surface"]:
            it["surface"] = h["surface"]
        kept.append(it)
    out = []
    for it in kept:
        if any(o["type"] == it["type"] and np.linalg.norm(o["pos"] - it["pos"]) < dedupe for o in out):
            dropped.append((it["type"], np.round(it["pos"], 2).tolist(), "duplicate"))
            continue
        out.append(it)
    da.items = out
    if log is not None:
        for d_ in dropped:
            log(f"    decal anchor dropped: {d_}")
    return len(out), len(dropped)
