"""components.level_probe -- the LEVEL see-through check through a horizontal band of a building (kit changes
v1_stone_watchtower round 5; new module, nothing existing changed).

    level_sky_probe(g, z0, z1, s_max, centre=(0.0, 0.0), n_az=16, az0=0.0, ds=0.005, dz=0.005, objects=None,
                    far=30.0, name="band", fail=True, report=6)
    cabin_bed_probe(g, n_az=16, ds=0.005, dz=0.005, margin=0.05, fail=True)

Rubric axis 4 ("no see-through pixels") for a junction that is seen LEVEL, e.g. a floor sandwich, a sole plate or a
jettied floor sitting on a wall head: horizontal orthographic rays are fired across the band z0..z1 (every dz) at
plan offsets |s| <= s_max (every ds) from the centre, from n_az azimuths spread over 180 deg (a level line seen
from one side is the same line from the other).  A line that meets no mesh of the building is a see-through.  The
grid is fine enough (5 mm) to find hairline slots that a 1 cm review test misses (round 4: a 4 mm slot under a
deck).  `seal_probe.through_seal_probe` is the matching check for roofs that a body rises through.

cabin_bed_probe is the STEP for a square_cabin crown (run it after the hidden-geometry cull, so the cull cannot ship
a slot): the band from just above the wall head (g.CABIN["bed"]) to just under the deck top, |s| <= bed_r + margin
(the whole cornice cap and a little beyond).  It raises LevelSeeThroughError naming the azimuth, offset and height
of the first lines that reach the sky (fail=False only logs).  Returns the record dict(rays, leaks, points).
"""
import math
import time

import numpy as np

from ..core import log


class LevelSeeThroughError(RuntimeError):
    """level rays pass through a horizontal junction band (kit changes v1 r5)."""


def level_sky_probe(g, z0, z1, s_max, centre=(0.0, 0.0), n_az=16, az0=0.0, ds=0.005, dz=0.005, objects=None,
                    far=30.0, name="band", fail=True, report=6):
    """KIT CHECK: see the module doc.  objects: the meshes to test against (default every mesh object of g.coll,
    linked duplicates included, in world space)."""
    from mathutils import Vector

    from .seal_probe import _bvh, _mesh_arrays
    t0 = time.time()
    objs = [o for o in (objects if objects is not None else g.coll.all_objects) if o.type == "MESH"]
    sel = []
    for o in objs:                                   # only meshes that reach into the band
        zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
        if min(zs) <= z1 + 0.05 and max(zs) >= z0 - 0.05:
            sel.append(o)
    V, T, own = _mesh_arrays(sel)
    bvh = _bvh(V, T)
    cx, cy = float(centre[0]), float(centre[1])
    S = np.arange(-s_max, s_max + 1e-9, ds)
    Z = np.arange(z0, z1 + 1e-9, dz)
    leaks, n_ray = [], 0
    for k in range(n_az):
        az = math.radians(az0 + 180.0 * k / n_az)
        d = np.array([math.cos(az), math.sin(az), 0.0])
        e = np.array([-d[1], d[0], 0.0])
        D = Vector(d)
        for s in S:
            ox, oy = cx + e[0] * s - d[0] * far, cy + e[1] * s - d[1] * far
            for z in Z:
                n_ray += 1
                if bvh.ray_cast(Vector((ox, oy, z)), D, 2.0 * far)[0] is None:
                    leaks.append((round(math.degrees(az), 2), round(float(s), 3), round(float(z), 3)))
    rec = dict(name=name, rays=n_ray, leaks=len(leaks), points=leaks[:report], z=(z0, z1), s_max=s_max, n_az=n_az)
    log(f"  level probe [{name}]: z {z0:.3f}..{z1:.3f}, |s| <= {s_max:.3f} m, {n_az} azimuths, {len(sel)} meshes, "
        f"{n_ray} level rays, {len(leaks)} see-through" + (f" e.g. (az, s, z) {leaks[:3]}" if leaks else "")
        + f" ({time.time() - t0:.1f} s)")
    if leaks and fail:
        a_, s_, z_ = leaks[0]
        raise LevelSeeThroughError(
            f"see-through through the level band {name!r}: {len(leaks)} of {n_ray} level rays reach the sky, first "
            f"from az {a_} at offset {s_} m, z {z_} m.  Close it in the module (blocking, a curb or a fascia to the "
            f"outermost member).")
    return rec


def cabin_bed_probe(g, n_az=16, ds=0.005, dz=0.005, margin=0.05, fail=True):
    """STEP (a square_cabin crown, after the cull): the level see-through check over the wall head, from 4 mm above
    the bed to 4 mm under the deck top, |s| <= bed_r + margin."""
    c = getattr(g, "CABIN", None)
    if not c:
        log("  level probe: no square_cabin in this building, skipped")
        return None
    z1 = float(c.get("deck_top", c["floor"])) - 0.004
    return level_sky_probe(g, float(c["bed"]) + 0.004, z1, float(c["bed_r"]) + margin, n_az=n_az, ds=ds, dz=dz,
                           name="cabin floor over the wall head", fail=fail)
