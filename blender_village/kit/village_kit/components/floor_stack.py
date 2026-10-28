"""components.floor_stack -- storeys of a rectangular timber building, with JETTIED upper floors (kit, variant
v5_harbour_house; new module, no existing building uses it).

    jetty_floor(g, name, lower, z, jetty=None, joist=(0.15, 0.20), spacing=0.45, rim=0.20, proud=0.04, soffit_t=0.03)
        KIT COMPONENT: the floor band between two storeys.  lower = (x0, x1, y0, y1): the lower storey's frame faces;
        z = the top of its wall plate; jetty = {"S": d, "N": d, "E": d, "W": d}: how far the upper storey oversails
        each side (m; opposite sides only -- two jettied sides meeting at a corner need a dragon beam, not built yet:
        it raises).  On a jettied side the joists run out through the lower wall head and show their ends (proud of
        the upper face by `proud`) under the bressummer (the upper storey's sole plate); the jetty soffit is CLOSED
        (a plank soffit between the joists' tops, and blocking boards between the joists over the lower wall plate,
        so no bay looks into the building).  On the other sides a rim beam (the outer joist / girt) closes the band,
        running out to the jetty line at its ends.  Builds <P>_<name>_joists, _rims, _soffit; returns
        dict(upper=(x0, x1, y0, y1) of the upper storey's frame faces, z_top = z + joist height).
    timber_storeys(g, name, rect, z_base, storeys, jetty=None, roof=None, floor=None, seed=500)
        KIT COMPONENT: a stack of path_timber_wall storeys on one rectangle with a jetty_floor between each pair.
        storeys = [dict(height=..., style=..., gable_style=..., openings=[(side, coord, spec)], sill=, plate=,
        post=, bay_max=), ...] bottom up; `height` = sill bottom to plate top.  jetty: one dict (between storeys 0
        and 1) or a list (one per floor band).  roof: a linear_roof.GableRoof over the top storey -- its walls are
        clad up to the deck (timber_walls.roof_top_fn), closing the eave strip and filling the gables.
        Publishes g.STOREYS = [dict(rect, z0, top, floor), ...] and returns it.
"""
import numpy as np

from ..core import log
from ..geom import Acc, finalize
from .timber_walls import EZ, path_timber_wall, rect_openings, rect_path, roof_top_fn, wbox

SIDE_N = dict(S=(0.0, -1.0), N=(0.0, 1.0), E=(1.0, 0.0), W=(-1.0, 0.0))


def _side_frame(rect, side):
    """(O, t, n, L) of a rectangle side as a run of rect_path (CCW: S +x, E +y, N -x, W -y)."""
    x0, x1, y0, y1 = rect
    if side == "S":
        return np.array([x0, y0, 0.0]), np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), x1 - x0
    if side == "E":
        return np.array([x1, y0, 0.0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), y1 - y0
    if side == "N":
        return np.array([x1, y1, 0.0]), np.array([-1.0, 0, 0]), np.array([0, 1.0, 0]), x1 - x0
    return np.array([x0, y1, 0.0]), np.array([0, -1.0, 0]), np.array([-1.0, 0, 0]), y1 - y0


def jetty_floor(g, name, lower, z, jetty=None, joist=(0.15, 0.20), spacing=0.45, rim=0.20, proud=0.04, soffit_t=0.03,
                tail=0.70, seed=0):
    """KIT COMPONENT (see the module doc)."""
    jetty = {k: float(v) for k, v in (jetty or {}).items() if v}
    for a, b in (("S", "E"), ("E", "N"), ("N", "W"), ("W", "S")):
        if a in jetty and b in jetty:
            raise ValueError(f"jetty_floor {name!r}: jettied sides {a} and {b} meet at a corner (a dragon beam is "
                             f"not in the kit yet); jetty opposite sides only")
    x0, x1, y0, y1 = lower
    up = (x0 - jetty.get("W", 0.0), x1 + jetty.get("E", 0.0), y0 - jetty.get("S", 0.0), y1 + jetty.get("N", 0.0))
    jw, jh = joist
    pre = f"{g.prefix}_{name}"
    rng = np.random.default_rng(seed)
    joists, rims, soffit = Acc(pre + "_joists"), Acc(pre + "_rims"), Acc(pre + "_soffit")
    zt = z + jh
    # ---- rims on the sides that are not jettied: they run out to the jetty lines (+ proud) at their ends
    for k, side in enumerate(("S", "E", "N", "W")):
        if side in jetty:
            continue
        O, t, n, L = _side_frame(up, side)
        prev_s = ("W", "S", "E", "N")[k]
        next_s = ("E", "N", "W", "S")[k]
        e0 = proud if prev_s in jetty else 0.06
        e1 = proud if next_s in jetty else 0.06
        dz = 0.015 * (k % 2)
        wbox(rims, (O, t, n), -e0, L + e1, z + dz, zt, -rim, 0.02, "M_timber", r=0.014,
             ns=max(4, int(L / 1.2) + 2), wear=float(rng.uniform(0.2, 0.4)))
    # ---- jettied sides: joists, blocking over the lower wall plate, the closed soffit
    for side, d in jetty.items():
        O, t, n, L = _side_frame(up, side)                 # the upper face line (the jetty line)
        # the band between the two rims (the rims of the adjacent sides are the outermost joists)
        a, b = rim + 0.02, L - rim - 0.02
        nj = max(2, int(round((b - a) / spacing)))
        for s in np.linspace(a + jw / 2 + 0.05, b - jw / 2 - 0.05, nj):
            s_ = s + rng.uniform(-0.02, 0.02)
            wbox(joists, (O, t, n), s_ - jw / 2, s_ + jw / 2, z + rng.uniform(-0.004, 0.004), zt,
                 -(d + tail), proud, "M_timber", r=0.016, ns=4, nz=4)
        # blocking boards between the joists over the lower wall head (w = -d .. -d - 0.05: the lower face line)
        wbox(soffit, (O, t, n), a - 0.03, b + 0.03, z - 0.01, zt - soffit_t + 0.002, -d - 0.06, -d - 0.01,
             "M_timber_weathered", r=0.004, ns=max(4, int(L / 1.0) + 2))
        # soffit planks across the oversail, between the joists' tops (seen from below)
        ns_ = max(2, int(round((b - a) / 0.26)))
        xs = np.linspace(a - 0.03, b + 0.03, ns_ + 1)
        for i in range(ns_):
            wbox(soffit, (O, t, n), xs[i] + 0.002, xs[i + 1] - 0.002, zt - soffit_t, zt, -d - 0.02, -0.005,
                 "M_timber_weathered", r=0.004)
    for a_ in (joists, rims, soffit):
        if a_.n:
            finalize(a_, g.coll, smooth_deg=30.0)
    log(f"  {pre}: floor band at z {z:.2f}-{zt:.2f}, jetty {jetty or 'none'}")
    return dict(upper=up, z_top=zt, jetty=jetty)


def timber_storeys(g, name, rect, z_base, storeys, jetty=None, roof=None, floor=None, seed=500):
    """KIT COMPONENT (see the module doc)."""
    floor = dict(floor or {})
    jets = jetty if isinstance(jetty, (list, tuple)) else [jetty] * max(0, len(storeys) - 1)
    rect_k, z0 = tuple(rect), float(z_base)
    out = []
    for k, sd in enumerate(storeys):
        sd = dict(sd)
        height = float(sd.pop("height"))
        ops = rect_openings(rect_k, sd.pop("openings", []))
        last = k == len(storeys) - 1
        top = z0 + height
        path_timber_wall(g, f"{name}{k}", rect_path(*rect_k), z0, top=top,
                         top_fn=roof_top_fn(roof) if (last and roof is not None) else None,
                         openings=ops, seed=seed + 17 * k, **sd)
        out.append(dict(rect=rect_k, z0=z0, top=top, floor=z0 + float(sd.get("sill", (0.24, 0.18))[1])))
        if not last:
            fb = jetty_floor(g, f"{name}{k}_jetty", rect_k, top, jetty=jets[k], seed=seed + 5 + k, **floor)
            rect_k, z0 = fb["upper"], fb["z_top"]
    g.STOREYS = out
    return out


__all__ = ["jetty_floor", "timber_storeys", "SIDE_N"]
_ = EZ
