"""village_kit.guards -- the kit's guard-rails, ON by default (kit 1.9.0; technical review condition 4).

Every kit building (assembly.build_building, compound.build_compound) now runs these after its geometry is built.
A recipe that cannot pass one opts out EXPLICITLY, per guard, with a reason that is logged in every build:

    build_building(dict(..., opt_out=dict(clearance="signed-off hero: ...", decal_validate="...")))
    Wing("mill", DrumFrame, "V4M", ..., opt_out=dict(seal_probe="..."))

    guard            what it does                                                        on failure
    clearance        entrance_clearance: the lowest eave / roof underside directly over every entrance (rays up
                     from a 5 x 5 grid of stations in front of the door, door parts ignored) must be at least
                     2.30 m (art bible 7) and not below the door head                     ClearanceError (named)
    decal_validate   anchor_validate.validate_anchors APPLIED (snap, drop, de-duplicate) instead of report-only;
                     a recipe's dict still passes its own keywords                        anchors dropped
    seal_probe       junction_seal_probe at every roof-through-body junction a kit module registered
                     (register_junction: shake_apron, stone_cone.shake_collar, thatch.thatch_junctions,
                     roof_junction.cone_abutment, junctions.roof_tower_flashing); the tier family runs its own
                     seal_probe.through_seal_probe in tier_hidden_cull (seal=True)        seal_probe.SealError
    steep_cone_door  frame.RoundFrame(steep_door="auto"): a cone steeper than STEEP_CONE_DEG (52, the top of the
                     bible's hut range) gets DOOR_INFILL_DECK and EAVE_CLOSURE_DOOR_HALF_DEG = 1.0 (the v4 r4
                     door-head fix)                                                       (frame flags)
    lod_scope        lod.tmpl_lod's rule is unregistered at the end of the building / of each compound wing, so
                     a rule never leaks into the next wing or building                     (always on)

Opt-outs: GUARDS lists the names; an unknown name or an empty reason raises.  steep_cone_door is opted out on the
frame instead (RoundFrame(steep_door=False)), lod_scope cannot be opted out.

Deterministic; the checks never change geometry (decal_validate changes anchors only).
"""
import math

import numpy as np

from . import core

GUARDS = ("clearance", "decal_validate", "seal_probe", "steep_cone_door")
MIN_LIP = 2.30                       # art bible 7: every eave lip directly over a doorway is at least 2.30 m


class ClearanceError(RuntimeError):
    """an eave lip / roof underside over an entrance is under 2.30 m or below the door head (kit 1.9.0)."""


def opt_outs(spec, who="building"):
    """the validated {guard: reason} of a spec / Wing (key `opt_out`)."""
    d = dict(spec.get("opt_out") or {}) if isinstance(spec, dict) else dict(getattr(spec, "opt_out", None) or {})
    def _reason(k, v):
        if not isinstance(v, str) or len(v.strip()) < 10:
            raise ValueError(f"opt_out {k!r} ({who}) needs a reason (a sentence), got {v!r}")

    for k, v in d.items():
        if k not in GUARDS:
            raise KeyError(f"opt_out: unknown guard {k!r} ({who}); one of {GUARDS}")
        if k == "seal_probe" and isinstance(v, dict):          # per junction: {junction name: reason}
            for jn, r in v.items():
                _reason(f"seal_probe / {jn}", r)
        else:
            _reason(k, v)
    for k, v in d.items():
        if isinstance(v, dict):
            for jn, r in v.items():
                core.log(f"GUARD OPT-OUT {who}: {k} at junction {jn!r} -- {r}")
        else:
            core.log(f"GUARD OPT-OUT {who}: {k} -- {v}")
    return d


def probed_junctions(junctions, opt):
    """the registered junctions the seal guard still checks under the opt-outs `opt` (a whole-guard opt-out -> none;
    a {junction: reason} opt-out -> all but those)."""
    v = opt.get("seal_probe")
    if v is None:
        return list(junctions or [])
    if isinstance(v, dict):
        unknown = set(v) - {j["name"] for j in junctions or []}
        if unknown:
            raise KeyError(f"opt_out seal_probe: no registered junction {sorted(unknown)}; registered: "
                           f"{[j['name'] for j in junctions or []]}")
        return [j for j in junctions or [] if j["name"] not in v]
    return []


# =================================================================================================================
# shared ray machinery
# =================================================================================================================
def _scene_arrays(objs):
    from .components.seal_probe import _mesh_arrays
    return _mesh_arrays([o for o in objs if o.type == "MESH"])


def _bvh(V, T):
    from mathutils.bvhtree import BVHTree
    return BVHTree.FromPolygons(V.tolist(), T.tolist(), all_triangles=True, epsilon=0.0)


# =================================================================================================================
# 1. the entrance clearance gate
# =================================================================================================================
DOOR_PARTS = ("door", "threshold", "step", "surround", "openings_", "_frames", "iron", "nail", "hinge", "pintle",
              "interior", "floor", "hearth", "reveals", "blocker", "lintel", "leaf", "_backing")
"""object-name fragments of a door's own assembly (frame, lintel, leaf, step, ironwork, rooms behind it): the
clearance rays pass through them -- they are the door, not the eave over it."""


def _ent(name, origin, out, width, head, d0=0.15):
    o = np.asarray(origin, float)
    if o.shape == (2,):
        o = np.array([o[0], o[1], 0.0])
    n = np.array([float(out[0]), float(out[1]), 0.0])
    n /= max(float(np.linalg.norm(n)), 1e-9)
    return dict(name=name, origin=o, out=n, width=float(width), head=float(head), d0=float(d0))


def entrances_of(g):
    """the entrances of a frame, from what its door components published (local / current coordinates):
    [dict(name, origin (x, y, 0) on the wall face at the door centre, out (unit, horizontal), width (clear),
    head (z of the top of the clear opening), d0 (first station beyond the face))].  An explicit g.ENTRANCES list
    (a recipe may set it) wins."""
    import bpy
    if getattr(g, "ENTRANCES", None):
        return [_ent(**e) if not isinstance(e.get("origin"), np.ndarray) else e for e in g.ENTRANCES]
    names = {o.name for o in g.coll.all_objects} if g.coll is not None else set()
    shift = np.asarray(getattr(g, "SHIFT", np.zeros(3)), float)
    out = []
    fam = getattr(type(g), "FAMILY", None)
    # hut family: the projecting framed door at -Y
    if fam == "round" and f"{g.prefix}_door_frame" in names:
        out.append(_ent("framed_door", (shift[0], g.FRONT_Y + shift[1]), (0, -1), g.DOOR_W, g.HEAD_Z))
    # drum family: the arched door in the drum at -Y
    if fam == "drum" and hasattr(g, "R_DOOR") and f"{g.prefix}_door_surround" in names:
        out.append(_ent("drum_door", (0.0, -float(g.R_BASE0)), (0, -1), 2 * g.DOOR_CW, g.ZS_DOOR + g.DOOR_CW,
                        d0=0.15))
    # keep family: the hall's arched door(s) and the annex plank door
    if fam == "oct":
        from .components.oct_frame import FN, fmap
        for o in g.OPENINGS:
            if o["kind"] != "arch":
                continue
            p = fmap(o["k"], np.array([o["xc"]]), np.array([0.0]), np.array([0.0]))[0]
            out.append(_ent(o.get("name", "hall_door"), p, FN[o["k"]][:2], 2 * o["hw"], o["zs"] + o["hw"], d0=0.35))
        if f"{g.prefix}_wing_door" in names and getattr(g, "WDOOR", None):
            d = g.WDOOR
            out.append(_ent("annex_door", (d["xc"], g.WY_S), (0, -1), 2 * d["hw"], d["z1"], d0=0.15))
    # stone_body openings (tier family, any frame with g.openings)
    for o in getattr(g, "openings", None) or []:
        if not isinstance(o, dict) or o.get("kind") != "door" or "origin" not in o:
            continue
        out.append(_ent(f"{o.get('body', 'body')}_door", np.asarray(o["origin"], float) + shift, o["normal"][:2],
                        2 * o["hw"], o["head"], d0=0.25))
    # wall_openings doors (path walls, plan frames)
    for o in getattr(g, "OPENINGS", None) or []:
        if fam == "oct" or not isinstance(o, dict) or o.get("kind") != "door" or "O" not in o:
            continue
        O = np.asarray(o["O"], float) + shift
        out.append(_ent(o.get("label") or "wall_door", (O[0], O[1]), np.asarray(o["n"], float)[:2], o["width"],
                        o["z1"], d0=0.15))
    _ = bpy
    return out


def lip_over(bvh, owner, ent, z_start=0.6, n_u=5, n_d=5, step=0.15, skip=DOOR_PARTS, far=12.0):
    """the lowest roof / eave underside over one entrance: rays straight up from n_u x n_d stations (across the
    clear width, from d0 to d0 + (n_d-1)*step beyond the face); hits on the door's own parts (skip) are passed;
    a station whose first real hit is a BACK face starts inside a solid and is ignored.  Returns
    (lowest z or None, its station, its object, n_stations_used)."""
    from mathutils import Vector
    o, n = ent["origin"], ent["out"]
    t = np.array([-n[1], n[0], 0.0])
    best = (None, None, None)
    used = 0
    up = Vector((0.0, 0.0, 1.0))
    for u in np.linspace(-0.5, 0.5, n_u) * ent["width"]:
        for k in range(n_d):
            d = ent["d0"] + k * step
            P = o + n * d + t * u
            z0 = z_start
            hit = None
            for _ in range(64):
                h = bvh.ray_cast(Vector((float(P[0]), float(P[1]), float(z0))), up, far)
                if h[0] is None:
                    break
                ob = str(owner[h[2]])
                if any(s in ob for s in skip):
                    z0 = float(h[0][2]) + 1e-4
                    continue
                hit = (float(h[0][2]), ob, float(h[1][2]))
                break
            if hit is None:
                used += 1
                continue
            if hit[2] > 1e-6:                    # back face: the station starts inside a solid
                continue
            used += 1
            if best[0] is None or hit[0] < best[0]:
                best = (hit[0], (round(float(P[0]), 3), round(float(P[1]), 3)), hit[1])
    return best[0], best[1], best[2], used


def entrance_clearance(g, entrances=None, min_lip=MIN_LIP, head_margin=0.0, fail=True, objects=None):
    """GUARD (kit 1.9.0, on by default): every entrance's eave lip >= min_lip (2.30 m) and >= its door head +
    head_margin.  Raises ClearanceError naming the building, the entrance, the lip height, where and on what."""
    ents = entrances_of(g) if entrances is None else [e if isinstance(e.get("origin"), np.ndarray) else _ent(**e)
                                                      for e in entrances]
    if not ents:
        core.log(f"  clearance gate {g.prefix}: no entrance published (nothing to check)")
        return []
    objs = list(objects) if objects is not None else [o for o in g.coll.all_objects if o.type == "MESH"]
    V, T, owner = _scene_arrays(objs)
    bvh = _bvh(V, T)
    recs, bad = [], []
    for e in ents:
        z, at, ob, used = lip_over(bvh, owner, e)
        need = max(min_lip, e["head"] + head_margin)
        ok = z is None or z >= need - 1e-6
        rec = dict(entrance=e["name"], lip=None if z is None else round(z, 3), at=at, object=ob, head=round(e["head"], 3),
                   need=round(need, 3), stations=used, ok=ok)
        recs.append(rec)
        core.log(f"  clearance gate {g.prefix} {e['name']}: door head {e['head']:.2f} m, eave lip over it "
                 + ("none (open sky)" if z is None else f"{z:.3f} m at {at} on {ob}")
                 + f" (rule >= {need:.2f} m, {used} stations): {'PASS' if ok else 'FAIL'}")
        if not ok:
            bad.append(rec)
    g.CLEARANCE = recs
    if bad and fail:
        raise ClearanceError(
            f"{g.prefix}: entrance clearance (art bible 7: every eave lip directly over a doorway >= {min_lip:.2f} m "
            f"and above the door head): " + "; ".join(
                f"{r['entrance']} lip {r['lip']:.3f} m < {r['need']:.2f} m at {r['at']} on {r['object']}" for r in bad)
            + ".  Raise the eave / shorten the overhang over the door, or lower the door head.")
    return recs


# =================================================================================================================
# 2. the generic see-through probe at roof-through-body junctions
# =================================================================================================================
def register_junction(g, name, covering, center, radius, z_range, ring=(0.0, 0.6), poly=None):
    """called by the kit modules that build a roof-through-body junction: covering = object names (full names or
    <prefix>_ fragments) of the roof covering, center = (x, y) of the body's axis in g's current coordinates,
    radius = callable(z) -> the body face radius (an inscribed radius for a polygonal body; poly = its side count,
    for the log), z_range = (z_lo, z_hi) of the junction."""
    if not hasattr(g, "SEAL_JUNCTIONS"):
        g.SEAL_JUNCTIONS = []
    g.SEAL_JUNCTIONS.append(dict(name=name, covering=tuple(covering), center=np.asarray(center, float)[:2],
                                 radius=radius, z_range=(float(z_range[0]), float(z_range[1])), ring=tuple(ring),
                                 poly=poly, shift0=np.asarray(getattr(g, "SHIFT", np.zeros(3)), float).copy()))
    core.log(f"  seal junction registered: {name} (covering {', '.join(covering)}; z {z_range[0]:.2f}-"
             f"{z_range[1]:.2f})")


def junction_seal_probe(objs, junctions, prefix="", el_deg=(10, 20, 30, 45, 60, 80), n_az=24, density=4000.0,
                        n_dir=8, below=0.08, depth=0.6, far=30.0, seed=4243, min_incidence=10.0, fail=True,
                        report=6, transform=None, edge=0.2):
    """GUARD (kit 1.9.0): the tier family's see-through probe generalised to any registered junction.  For every
    junction: seeded plan points in the annulus `ring` outside the body face where the covering really is (a ray
    straight down onto the covering alone); each target lies `below` (8 cm) under the covering top, inside the roof
    build-up (something within `depth` under it) and at least `edge` (0.2 m) from the covering's free edges (it
    continues outward and to both sides) -- an eave lip, verge or comb tip is not a junction.  Exterior rays (n_dir of the n_az x el grid per target, none closer than min_incidence to grazing the
    local covering) are aimed at it through ALL meshes: a ray stopped before the target is sealed; one that passes it
    is a LEAK when it then reaches nothing (the sky), a point more than `depth` under the covering (the interior), or
    a point inside the body more than `depth` below the target (the hollow body).  Raises SealError on a leak.
    transform: optional fn(center xy) -> world xy (compound wings)."""
    import time
    from mathutils import Vector
    from .components.seal_probe import SealError
    t0 = time.time()
    rng = np.random.default_rng(seed)
    V, T, own = _scene_arrays(objs)
    bvh = _bvh(V, T)
    az = np.radians(np.arange(n_az) * 360.0 / n_az + 7.5)
    el = np.radians(np.asarray(el_deg, float))
    A, E = np.meshgrid(az, el, indexing="ij")
    DIRS = np.column_stack([(np.cos(E) * np.cos(A)).ravel(), (np.cos(E) * np.sin(A)).ravel(), np.sin(E).ravel()])
    DEG = np.column_stack([np.degrees(A).ravel(), np.degrees(E).ravel()])
    s_min = math.sin(math.radians(min_incidence))
    down = Vector((0.0, 0.0, -1.0))
    out, bad = [], []
    for j in junctions:
        cov = np.array([any(c == nm or (c in nm) for c in j["covering"]) for nm in own])
        if not cov.any():
            core.log(f"  seal probe {j['name']}: no covering objects {j['covering']} (skipped)")
            continue
        cbvh = _bvh(V, T[cov])
        c = np.asarray(j["center"], float)
        if transform is not None:
            c = np.asarray(transform(c), float)
        z_lo, z_hi = j["z_range"]
        r_mid = float(j["radius"](0.5 * (z_lo + z_hi)))
        ring = j["ring"]
        n = int(2 * math.pi * (r_mid + 0.5 * (ring[0] + ring[1])) * (ring[1] - ring[0]) * density)
        th = rng.uniform(0, 2 * math.pi, n)
        dd = rng.uniform(ring[0], ring[1], n)

        def top_at(x, y, z_from):
            h = cbvh.ray_cast(Vector((float(x), float(y), float(z_from))), down, 50.0)
            if h[0] is None:
                return None
            nn = np.array(h[1])
            if nn[2] < 0:
                nn = -nn
            return float(h[0][2]), nn

        targets, normals = [], []
        for i in range(n):
            z = 0.5 * (z_lo + z_hi)
            ok = False
            for _ in range(3):
                r = float(j["radius"](z)) + dd[i]
                x, y = c[0] + r * math.cos(th[i]), c[1] + r * math.sin(th[i])
                tp = top_at(x, y, z_hi + 3.0)
                if tp is None:
                    break
                z, nn = tp
                ok = True
            if not ok or not (z_lo <= z <= z_hi):
                continue
            # a target must lie INSIDE the roof build-up: something (deck, structure, body, a lower course) within
            # `depth` under it.  At an eave nose, a roll or a comb tip there is open air under the covering, and a
            # ray reaching such a point has simply come round the edge (not a junction see-through).
            hb = bvh.ray_cast(Vector((float(x), float(y), float(z - below))), down, depth)
            if hb[0] is None:
                continue
            # ... and away from the covering's free edges (eave lip, verge, comb): the covering continues `edge` m
            # outward (away from the body) and to both sides at about this height
            ux, uy = math.cos(th[i]), math.sin(th[i])
            inner = True
            for ex, ey in ((ux, uy), (-uy, ux), (uy, -ux)):
                tq = top_at(x + edge * ex, y + edge * ey, z_hi + 3.0)
                if tq is None or abs(tq[0] - z) > edge * 2.0:
                    inner = False
                    break
            if not inner:
                continue
            targets.append((x, y, z - below))
            normals.append(nn)
        P = np.array(targets).reshape(-1, 3)
        NRM = np.array(normals).reshape(-1, 3)
        leaks, n_ray, passed = [], 0, 0
        pick = np.argsort(rng.random((len(P), len(DIRS))), axis=1)[:, :n_dir] if len(P) else np.zeros((0, n_dir), int)
        for i in range(len(P)):
            Tp = P[i]
            for k in pick[i]:
                dv = DIRS[k]
                if float(dv @ NRM[i]) < s_min:
                    continue
                O = Tp + dv * far
                h = bvh.ray_cast(Vector(O), Vector(-dv), 4.0 * far)
                n_ray += 1
                if h[0] is not None and h[3] <= far + 1e-4:
                    continue                                     # stopped before the target: sealed
                passed += 1
                if h[0] is None:
                    leaks.append((Tp, k, "sky"))
                    continue
                H = np.array(h[0])
                hob = str(own[h[2]]).replace(prefix + "_", "") if prefix else str(own[h[2]])
                tp = top_at(H[0], H[1], H[2] + 6.0)
                under = tp is not None and H[2] < tp[0] - depth
                rb = float(j["radius"](H[2]))
                inside = math.hypot(H[0] - c[0], H[1] - c[1]) < rb - 0.02 and H[2] < Tp[2] - depth
                if under or inside:
                    leaks.append((Tp, k, f"interior ({hob} at {H[0]:.2f}, {H[1]:.2f}, {H[2]:.2f})"))
        rec = dict(junction=j["name"], targets=len(P), rays=n_ray, passed=passed, leaks=len(leaks),
                   points=[(tuple(float(x) for x in np.round(L[0], 3)), tuple(float(x) for x in DEG[L[1]]), L[2])
                           for L in leaks[:report]])
        out.append(rec)
        core.log(f"  seal probe [see-through] {j['name']}: {len(P)} points, {n_ray} rays, {passed} grazing pass(es), "
                 f"{len(leaks)} leak(s)" + (f" e.g. {rec['points'][:3]}" if leaks else ""))
        if leaks:
            bad.append(rec)
    core.log(f"  seal probe: {sum(r['rays'] for r in out)} rays on {len(out)} junction(s) in {time.time() - t0:.1f} s")
    if bad and fail:
        raise SealError("see-through at a roof/body junction (producer note 6): " + "; ".join(
            f"{r['junction']}: {r['leaks']} of {r['rays']} rays leak, first at {r['points'][0][0]} from az "
            f"{r['points'][0][1][0]:.0f} el {r['points'][0][1][1]:.0f} to the {r['points'][0][2]}" for r in bad)
            + ".  Close it in the junction module (flashing / deck / fillet), or opt the building out with a reason.")
    return out


def seal_junctions(g, junctions=None, objects=None, transform=None, **kw):
    """run junction_seal_probe on g's registered junctions (current coordinates: a recentred building's junctions
    are moved by the shift since they were registered)."""
    js = list(junctions if junctions is not None else getattr(g, "SEAL_JUNCTIONS", []))
    if not js:
        return []
    sh = np.asarray(getattr(g, "SHIFT", np.zeros(3)), float)
    moved = []
    for j in js:
        j2 = dict(j)
        j2["center"] = np.asarray(j["center"], float) + (sh - j.get("shift0", np.zeros(3)))[:2]
        moved.append(j2)
    objs = list(objects) if objects is not None else [o for o in g.coll.all_objects if o.type == "MESH"]
    return junction_seal_probe(objs, moved, prefix=g.prefix, transform=transform, **kw)


# =================================================================================================================
# 3. tmpl_lod scope
# =================================================================================================================
def end_lod_scope(g):
    """unregister g's lod.tmpl_lod rule (if any): a rule never outlives its building / wing."""
    from . import lod
    if (g.prefix + "_") in lod.RULES:
        lod.unregister(g.prefix + "_")
        core.log(f"  tmpl_lod {g.prefix}: rule unregistered (end of the wing / building)")


# =================================================================================================================
# the after-steps hook (build_building / build_compound)
# =================================================================================================================
def after_steps(g, opt, entrances=None):
    """run the geometry guards on a finished frame g (after its last step): the clearance gate and the junction
    seal probe, unless opted out; then end g's LOD scope."""
    end_lod_scope(g)
    if "clearance" not in opt:
        entrance_clearance(g, entrances=entrances)
    js = probed_junctions(getattr(g, "SEAL_JUNCTIONS", None), opt)
    if js:
        seal_junctions(g, junctions=js)
