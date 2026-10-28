"""village_kit.anchor_audit -- kit 1.4.0: the director's / sign-off auditor's decal-anchor plausibility test as a
build-time check (producer note 11; tower windmill round 8).

    audit_anchors(da, probe, max_offset=0.015, min_dot=0.85, start=0.25, reach=0.6, drop=False)

For every anchor of a decals.DecalAnchors set: a ray from `start` m out along the anchor's normal (+Z of the empty)
back along -Z, `reach` m long.  The FIRST surface hit must
    * lie within +-max_offset of the anchor (neither floating nor buried),
    * be a front face whose own normal . the anchor's +Z >= min_dot (no back faces of covered shingles, no faces
      inside a baluster, no tilted chamfers),
    * carry the palette slot the anchor declares in `surface`.
Returns the failures as strings; drop=True also removes the failing anchors from da.items.  A separate module so
decals.py / decal_gate.py / anchor_validate.py (shared, edited by other builders) are unchanged.
"""
import numpy as np

from .decals import _unit


def audit_one(probe, it, max_offset=0.015, min_dot=0.85, start=0.25, reach=0.6):
    """None when the anchor passes, else the reason."""
    from mathutils import Vector
    n = _unit(it["normal"])
    p = np.asarray(it["pos"], float)
    o = p + n * start
    h = probe.bvh.ray_cast(Vector(tuple(map(float, o))), Vector(tuple(map(float, -n))), reach)
    if h[0] is None:
        return "no surface"
    off = start - float(h[3])                       # + proud of the surface, - buried
    dot = float(np.dot(np.array(h[1]), n))
    surf = probe.mats[h[2]]
    if abs(off) > max_offset or dot < min_dot or surf != it["surface"]:
        return "off %+.3f m, dot %.2f, hit %s / %s, declared %s" % (off, dot, probe.names[h[2]], surf, it["surface"])
    return None


def audit_anchors(da, probe, max_offset=0.015, min_dot=0.85, start=0.25, reach=0.6, drop=False):
    bad, keep = [], []
    cnt = {}
    for it in da.items:
        cnt[it["type"]] = cnt.get(it["type"], 0) + 1
        why = audit_one(probe, it, max_offset, min_dot, start, reach)
        if why is None:
            keep.append(it)
        else:
            bad.append("%s #%d at %s: %s" % (it["type"], cnt[it["type"]], np.round(it["pos"], 3).tolist(), why))
    if drop:
        da.items = keep
    return bad
