"""components.composite -- assembly helpers for buildings combined from several kit bodies (a round end + a linear
body, a tower + an annex ...) (kit, variant v3_longhouse_roundend).

    cone_roof(g, seed, structure_seeds)   KIT COMPONENT: the round frame's conical shingle roof (rafters + hub,
                                          purlin / batten rings, doubled starter + chunky shingle courses, blocker;
                                          components.conical_roof) WITHOUT the hut's daub eave closure, for a round
                                          body whose eave is closed by its own wall head (roof_junction.round_eave_fill)
    set_entrance(g, xy)                   producer note 11: the 1 cm entrance zone at the building's real entrance
    footprint_views(g, ...)               actor / crane viewpoints round the true (elongated) footprint
    composite_hidden_cull(g, ...)         KIT COMPONENT (post step): core.visibility_cull on every non-backing mesh
    recenter(g)                           KIT COMPONENT (last step): moves the whole building so its plan bounding
                                          box is centred on the origin (art bible 8), recording g.SHIFT
    composite_decals(g, seed)             producer note 11 anchors for rubble walls (straight and round), openings,
                                          thatch / shingle roofs and the round end's cone
"""
import math

import numpy as np

from ..core import DetailRule, log, review_cameras, ring_views, visibility_cull

BACKING = ("_deck", "_blocker", "_underlap", "_mortar", "_eave_fill", "_reveals", "_roof_blocker", "_abutment", "_finial",
           "_cap_collar")
"""object-name fragments that are never culled: backing surfaces (deck, blockers, mortar bodies, eave fill,
reveals) and small closed hero pieces."""


def cone_roof(g, seed=606, structure_seeds=(404, 505), soffit=True, soffit_skip=None):
    """soffit=True (round 2 default): cone_soffit under the whole eave overhang (soffit_skip(P) -> bool drops the
    part inside an attached body)."""
    from .conical_roof import build_purlins_battens, build_rafters, build_roof_blocker, build_shingles
    build_rafters(g, g.coll, seed=structure_seeds[0])
    build_purlins_battens(g, g.coll, seed=structure_seeds[1])
    build_shingles(g, g.coll, seed=seed)
    build_roof_blocker(g, g.coll)
    if soffit:
        cone_soffit(g, skip=soffit_skip)


def cone_soffit(g, r_in=None, eave_s=0.10, gap=0.006, t=0.012, skip=None, n_az=145):
    """KIT COMPONENT (round 2): the boarded soffit slab under a RoundFrame cone's eave overhang -- the closed slab of
    components.tower_roof._roof_deck (v1), limited to the overhang: top face up under the battens, soffit face down,
    edge face at the eave, from eave_s slope metres above the lip to r_in (default 7.5 cm inside the plate line,
    past the start of the roof blocker), so no eye-level ray finds sky between the rafters, plate, battens, under-lap
    and shingles of the overhang.  skip(P) -> bool drops faces inside an attached body.  -> <P>_roof_soffit_deck"""
    from ..core import grid_quads
    from ..geom import Acc, finalize
    from .cone import az2th, s_at_r, surf_frame
    r_in = g.R_WALL - 0.075 if r_in is None else r_in
    az = np.linspace(0, 2 * np.pi, n_az)
    th = az2th(az)
    s_in = s_at_r(g, r_in)
    d0 = g.BATTEN_T + gap
    acc = Acc(f"{g.prefix}_roof_soffit_deck", 30)

    def sheet(depth, up, ns=5):
        ss = np.linspace(eave_s, s_in + 0.03, ns)
        TH, SS = np.meshgrid(th, ss, indexing="ij")
        P, ts, tt, n = surf_frame(g, TH.ravel(), SS.ravel())
        P = P - n * depth
        F = grid_quads(len(th), len(ss))
        q = P[F[0]]
        if (float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0) == up:
            F = F[:, ::-1]
        return P, F
    parts = [sheet(d0, True), sheet(d0 + t, False)]
    P0, ts, tt, n = surf_frame(g, th, np.full_like(th, eave_s))
    E = np.stack([P0 - n * d0, P0 - n * (d0 + t)], 1).reshape(-1, 3)
    F = grid_quads(len(th), 2)
    q = E[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), -ts[0])) < 0:
        F = F[:, ::-1]
    parts.append((E, F))
    for P, F in parts:
        if skip is not None:
            F = F[~skip(P[F].mean(1))]
        acc.add(P, F, "M_timber_weathered", wear=0.4)
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=False)


def set_entrance(g, xy, radius=3.0, height=2.5):
    g.detail = DetailRule(entrance=tuple(xy), entrance_r=radius, entrance_h=height)
    g.ENTRANCE = tuple(xy)


def inside_box(x0, x1, y0, y1, z1=None):
    """clip(P, margin=0) -> bool: plan point inside the box (e.g. the interior of an attached rectangular body)."""
    def clip(P, margin=0.0):
        P = np.asarray(P, float)
        m = (P[:, 0] > x0 + margin) & (P[:, 0] < x1 - margin) & (P[:, 1] > y0 + margin) & (P[:, 1] < y1 - margin)
        if z1 is not None:
            m &= P[:, 2] < z1
        return m
    return clip


def inside_round(center, r_out, depth=0.12, batter_deg=0.0):
    """clip(P, margin=0) -> bool: plan point more than `depth` inside a round body's face (radius r_out at the
    ground, battered by batter_deg) -- e.g. a straight wall running into a round end."""
    tb = math.tan(math.radians(batter_deg))

    def clip(P, margin=0.0):
        P = np.asarray(P, float)
        r = r_out - np.clip(P[:, 2], 0, None) * tb
        return np.hypot(P[:, 0] - center[0], P[:, 1] - center[1]) < r - depth - margin
    return clip


def _meshes(g):
    return [o for o in g.coll.all_objects if o.type == "MESH"]


def _bounds(g):
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in _meshes(g)])
    return co.min(0), co.max(0)


LEAN_VIEWS = dict(dists=(0.8, 3.0), heights=(0.6, 1.65, 2.6), spacing=1.8, crane=(6.0, (7.0,)),
                  door=((0.8, 1.6, 2.4), (0.6, 1.2, 1.8), (-0.6, 0.0, 0.6)))
"""round 2: the lean view set (2 loop distances x 3 heights + 1 crane loop + 27 door views + the review cameras,
~1/3 of the round-1 set) -- keeps a full composite build under the art bible's ~10 min."""
ROOF_VIEWS = dict(dists=(0.8, 3.0), heights=(1.65, 2.6), spacing=1.8, crane=(6.0, (7.0,)), door=((), (), ()))
ROOF_PARTS = ("roof_shingles", "roof_starter", "_covering", "_eave_roll", "_ridge", "_comb")
"""roof coverings: no knee-height loop and no door views (they cannot see more of a roof than head height does)."""


def footprint_views(g, dists=(0.5, 1.5, 3.5), heights=(0.3, 1.0, 1.65, 2.3), spacing=1.2, crane=(6.0, (5.0, 9.0)),
                    door=((0.6, 1.2, 2.0), (0.5, 1.1, 1.7, 2.3), (-0.8, 0.0, 0.8))):
    """viewpoints on loops round the plan bounding box (offset by each distance) at actor heights, a crane loop, the
    review cameras and door views (1-2 m in front of every door, knee to above head height).
    door = (distances, heights, lateral offsets) of the door views."""
    lo, hi = _bounds(g)
    out = []

    def loop(d, z):
        x0, x1, y0, y1 = lo[0] - d, hi[0] + d, lo[1] - d, hi[1] + d
        per = 2 * ((x1 - x0) + (y1 - y0))
        n = max(16, int(per / spacing))
        for k in range(n):
            s = per * k / n
            if s < x1 - x0:
                p = (x0 + s, y0)
            elif s < (x1 - x0) + (y1 - y0):
                p = (x1, y0 + s - (x1 - x0))
            elif s < 2 * (x1 - x0) + (y1 - y0):
                p = (x1 - (s - (x1 - x0) - (y1 - y0)), y1)
            else:
                p = (x0, y1 - (s - 2 * (x1 - x0) - (y1 - y0)))
            out.append((p[0], p[1], z))
    for d in dists:
        for z in heights:
            loop(d, z)
    for z in crane[1]:
        loop(crane[0], z)
    for op in getattr(g, "OPENINGS", []):
        if op["kind"] != "door":
            continue
        for d in door[0]:
            for z in door[1]:
                for x in door[2]:
                    out.append(tuple(op["O"] + op["n"] * d + op["t"] * x + np.array([0, 0, z])))
    V = np.array(out)
    return np.concatenate([V, review_cameras(lo, hi)])


def composite_hidden_cull(g, targets=None, procs=4, views="lean", min_polys=0):
    """KIT COMPONENT (post step): delete the polygons no review / actor / crane / door viewpoint can see on every
    building mesh except the backing surfaces (BACKING) and the pooled instances (producer note 6).
    views: "lean" (round 2 default, LEAN_VIEWS), "full" (the round-1 set) or a footprint_views kwargs dict;
    min_polys: only ray-test objects with at least this many polygons (the small ones cost time, save little)."""
    if targets is None:
        targets = [o.name for o in _meshes(g)
                   if o.data.users == 1 and not any(b in o.name for b in BACKING)
                   and len(o.data.polygons) >= min_polys]
    if views == "lean":
        # roof coverings (ROOF_PARTS) are tested from the actor loops at head / eave height, the crane loop and the
        # review cameras; walls, openings and timbers also from the knee-height loops and the door views
        common = footprint_views(g, **ROOF_VIEWS)
        low = footprint_views(g, **dict(LEAN_VIEWS, heights=(0.6,), crane=(6.0, ())))
        by = {t: low for t in targets if not any(r in t for r in ROOF_PARTS)}
        n = visibility_cull(targets, extra_views=common, extra_by_target=by, procs=procs)
        log(f"hidden-geometry cull: -{n} polygons on {len(targets)} objects")
        return n
    kw = {} if views == "full" else dict(views)
    n = visibility_cull(targets, extra_views=footprint_views(g, **kw), procs=procs)
    log(f"hidden-geometry cull: -{n} polygons on {len(targets)} objects")
    return n


def recenter(g):
    """KIT COMPONENT (last geometry step): translate the building so its plan bounding box is centred on the origin
    (ground stays at Z = 0).  Unique meshes are moved in their data (transforms stay identity); pooled linked
    duplicates move by their matrices.  g.SHIFT records the move (later steps and decals add it)."""
    from mathutils import Matrix
    lo, hi = _bounds(g)
    sh = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, 0.0])
    T = Matrix.Translation(tuple(map(float, sh)))
    done = set()
    for o in _meshes(g):
        if o.data.users == 1 and o.matrix_world == Matrix.Identity(4):
            o.data.transform(T)
            o.data.update()
        else:
            o.matrix_world = T @ o.matrix_world
        done.add(o.name)
    g.SHIFT = sh
    log(f"recentred by ({sh[0]:+.3f}, {sh[1]:+.3f}); plan bbox {hi[0] - lo[0]:.2f} x {hi[1] - lo[1]:.2f} m, "
        f"height {hi[2]:.2f} m")
    return sh


# =================================================================================================================
# producer note 11: decal anchors
# =================================================================================================================
def composite_decals(g, seed=1201):
    """anchors on the composite's surfaces, all ray-snapped onto the built meshes (decals.SurfaceProbe), physically
    placed: damp_rise / moss at the wall feet (more and likelier on north faces), lichen on footing tops, quoins and
    weather (W / N) faces, water_streak under sills and the cone eave drip, soot over the door and windows, rust under
    the door straps, cracks at opening corners and lintel ends, grime beside the door, repair patches on the walls,
    moss on the north roof slopes and the cone's north shingle butts.  The kit gate (anchor_validate, the building
    spec's decal_validate) then snaps / drops them."""
    from ..decals import SurfaceProbe, above_opening, below_points, opening_corners, tops
    sh = getattr(g, "SHIFT", np.zeros(3))
    da = g.decals
    rng = np.random.RandomState(seed)
    probe = SurfaceProbe(_meshes(g))
    ez = np.array([0.0, 0.0, 1.0])
    STONE = ("M_stone", "M_stone_dressed", "M_mortar")

    def cast_wall(p, n, typ, size, prob=None, surfaces=STONE, up=(0, 0, 1)):
        hit = probe.cast(p + n * 0.6, -n, 1.2)
        if hit is None or hit["surface"] not in surfaces:
            return None
        return da.add(typ, hit["pos"], hit["normal"], size, hit["surface"], prob, seed=int(rng.randint(1 << 30)),
                      up=up)

    ops = getattr(g, "OPENINGS", [])

    def near_opening(p, m=0.5):
        for op in ops:
            d = p - (op["O"] + sh)
            x = float(d @ op["t"])
            if abs(x) < op["width"] / 2 + 0.45 + m and -0.3 < p[2] < op.get("head", 2.5) + m:
                if abs(float(d @ op["n"])) < 1.0:
                    return True
        return False
    # ---- wall feet, weather faces, repairs
    for wf in getattr(g, "WALL_FACES", []):
        if wf["kind"] == "path":
            pm = wf["map"]
            for s in np.arange(0.6, pm.total - 0.4, 1.7):
                O, t, n = pm.frame(s)
                p = O + sh + ez * 0.32
                if wf["clip"] is not None and wf["clip"]((O + ez * 0.3)[None])[0]:
                    continue
                if near_opening(p, 0.2):
                    continue
                north = n[1] > 0.5
                typ = "moss" if (north and rng.uniform() < 0.5) else "damp_rise"
                prob = min(1.0, 0.6 + 0.3 * north)
                cast_wall(p, n, typ, (rng.uniform(0.7, 1.1), rng.uniform(0.35, 0.5)), prob)
            for s in np.arange(1.0, pm.total - 0.5, 3.1):
                O, t, n = pm.frame(s)
                z = rng.uniform(1.3, max(1.4, wf["top"](s) - 0.4))
                p = O + sh + ez * z
                if (wf["clip"] is not None and wf["clip"]((O + ez * z)[None])[0]) or near_opening(p, 0.3):
                    continue
                weather = n[0] < -0.5 or n[1] > 0.5
                typ = "lichen" if weather else "repair_patch"
                cast_wall(p, n, typ, (rng.uniform(0.35, 0.6), rng.uniform(0.3, 0.5)))
        else:
            c = np.array([wf["center"][0], wf["center"][1], 0.0]) + sh
            for az in np.radians(np.arange(8.0, 360.0, 24.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                r = float(wf["radius"](0.3))
                O = c + n * r
                if wf["clip"] is not None and wf["clip"]((O - sh + ez * 0.3)[None])[0]:
                    continue
                if near_opening(O + ez * 0.3, 0.2):
                    continue
                typ = "moss" if (n[1] > 0.4 and rng.uniform() < 0.5) else "damp_rise"
                cast_wall(O + ez * 0.32, n, typ, (rng.uniform(0.7, 1.0), rng.uniform(0.35, 0.5)),
                          min(1.0, 0.6 + 0.3 * (n[1] > 0.4)))
            for az in np.radians(np.arange(20.0, 360.0, 52.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                z = rng.uniform(1.0, wf["top"] - 0.35)
                O = c + n * float(wf["radius"](z)) + ez * z
                if (wf["clip"] is not None and wf["clip"]((O - sh)[None])[0]) or near_opening(O, 0.3):
                    continue
                cast_wall(O, n, "lichen" if n[1] > 0.0 else "repair_patch",
                          (rng.uniform(0.35, 0.55), rng.uniform(0.3, 0.45)))
                # the cone's eave drip streaks the wall head under the plate
            for az in np.radians(np.arange(35.0, 360.0, 60.0)):
                n = np.array([math.sin(az), -math.cos(az), 0.0])
                z = wf["top"] - 0.15
                O = c + n * float(wf["radius"](z)) + ez * z
                if (wf["clip"] is not None and wf["clip"]((O - sh)[None])[0]) or near_opening(O, 0.3):
                    continue
                below_points(da, probe, [O], [n], "water_streak", size=(0.14, 0.7), surfaces=STONE, rng=rng)
    # ---- openings
    for op in ops:
        O, t, n = op["O"] + sh, op["t"], op["n"]
        mid = O + ez * 0.5 * (op["z0"] + op["z1"])
        hw = op["width"] / 2
        above_opening(da, probe, O, n, op["width"] + 0.2, op["head"] + 0.02, "soot",
                      size=(op["width"] + 0.3, 0.5), surfaces=STONE, rng=rng)
        cs = [O + t * (op["lintel_w"] / 2 + 0.06) + ez * (op["head"] + 0.1),
              O - t * (op["lintel_w"] / 2 + 0.06) + ez * (op["head"] + 0.1)]
        opening_corners(da, probe, cs, n, "crack", size=(0.22, 0.4), surfaces=STONE, rng=rng)
        if op["kind"] == "window":
            below_points(da, probe, [O + ez * (op["sill"] - 0.12) + n * 0.03], [n], "water_streak",
                         size=(op["width"] * 0.8, 0.7), surfaces=STONE, rng=rng)
            opening_corners(da, probe, [O + t * (hw + 0.25) + ez * (op["sill"] - 0.15)], n, "crack",
                            size=(0.2, 0.32), surfaces=STONE, rng=rng)
        else:
            for zs in (op["z0"] + 0.32, op["z1"] - 0.34):
                below_points(da, probe, [O + t * (-hw + 0.25) + ez * zs - n * 0.06], [n], "rust_stain",
                             size=(0.08, 0.3), surfaces=("M_timber_weathered", "M_timber"), rng=rng, drop=0.04)
            for sgn in (-1, 1):
                cast_wall(O + t * sgn * (hw + 0.55) + ez * 1.0, n, "grime", (0.35, 0.9), 0.7)
            tops(da, probe, [O + n * 0.2 + t * sgn * (hw + 0.1) for sgn in (-1, 1)], "lichen", size=(0.2, 0.15),
                 surfaces=("M_stone_dressed",), rng=rng)
    # ---- footing tops and quoins (lichen), roofs (moss)
    lo, hi = _bounds(g)
    for wf in getattr(g, "WALL_FACES", []):
        if wf["kind"] != "path":
            continue
        pm = wf["map"]
        for s in np.arange(1.2, pm.total - 0.5, 2.3):
            O, t, n = pm.frame(s)
            if near_opening(O + sh + ez * 0.3, 0.4):
                continue
            tops(da, probe, [O + sh + n * 0.06 + ez * 0.35], "lichen", size=(0.25, 0.15), surfaces=STONE, rng=rng,
                 h_from=0.25)
    for name, roof in getattr(g, "LINEAR_ROOFS", {}).items():
        mat = "M_thatch" if roof.covering == "thatch" else "M_roof_shingle"
        for x in np.arange(roof.xa + 0.6, roof.xb - 0.4, 1.6):
            for sg in (1, -1):
                for u in (0.5, roof.U * 0.55):
                    P = roof.to_world(roof.surf(x, u, sg, 0.0)) + sh
                    if sg < 0 and rng.uniform() < 0.6:
                        continue
                    hit = probe.cast(P + ez * 1.5, -ez, 3.0)
                    if hit is None or hit["surface"] != mat or hit["normal"][2] < 0.5:
                        continue
                    da.add("moss", hit["pos"], hit["normal"], (rng.uniform(0.5, 0.9), rng.uniform(0.4, 0.7)),
                           mat, 0.75 if sg > 0 else 0.4, seed=int(rng.randint(1 << 30)), up=roof.dir_world(
                               np.array([0.0, -sg * math.cos(roof.p), math.sin(roof.p)])))
    if hasattr(g, "R_EAVE"):
        c = np.array([0.0, 0.0, 0.0]) + sh
        for az in np.radians(np.arange(120.0, 260.0, 22.0)):
            for rr in (g.R_EAVE - 0.5, g.R_EAVE - 1.5):
                p = c + np.array([math.sin(az) * rr, -math.cos(az) * rr, 0.0])
                hit = probe.cast(p + ez * 12.0, -ez, 14.0)
                if hit is None or hit["surface"] != "M_roof_shingle":
                    continue
                da.add("moss", hit["pos"], hit["normal"], (0.6, 0.45), "M_roof_shingle", 0.7,
                       seed=int(rng.randint(1 << 30)), up=(0, 0, 1))
    log(f"composite decals: {len(da.items)} anchors before the gate")
    return da
