"""components.tower_decals -- producer note 11 decal anchors for a round stone tower WITHOUT a rotor (a watchtower,
a stair turret, a dovecote ...) built from the drum family + components.tower_roof (kit changes
v1_stone_watchtower; new module).

round_tower_decals(g)        places the anchors on the BUILT meshes (village_kit.decals helpers, ray-cast onto real
                             surfaces, palette slot reported by the hit):
    damp_rise / moss   round the drum foot (north more likely), moss on the north roof shingles
    lichen             up-facing stone tops: string course, slit-window sills (the coping is under the eave)
    water_streak       below every slit sill, below the string course and the parapet coping drip
    rust_stain         below the door strap hinges / ring pull
    soot               above the door head and the slits
    crack              door and slit corners, settlement low in the rubble, under the string course
    grime              hand height on the door jambs
    repair_patch       mortar repairs over the lower and the upper shaft
    plaster_patch      render remnants beside the door, the plastered passage
round_tower_decals_gated(g)  + the drum family's three gates (decal_gate.snap_anchors, anchor_validate, anchor_audit),
                             asserting 0 audit failures and 40-120 anchors (as drum_decals.drum_tower_decals_gated).
"""
import math

import numpy as np

from .. import decals as D
from ..core import log
from .drum_frame import R_out, win_list


def _az_pt(az, r, z):
    return np.array([math.sin(az) * r, -math.cos(az) * r, z])


def _out(az):
    return np.array([math.sin(az), -math.cos(az), 0.0])


BLOCKER_PARTS = ("_lookout_rooms", "_ceiling", "_cabin_ceiling")
"""v1_stone_watchtower r3: note-6 blocker / backing meshes no decal may sit on (the closed dark rooms behind the
lookouts, the ceiling disc over the ground floor, the cabin's ceiling).  `<PREFIX>_interior` is a blocker above the
door crown only (below it is the plastered passage seen through the door)."""


def blocker_hit(g, hit, exclude=BLOCKER_PARTS):
    """True when a SurfaceProbe hit lies on a note-6 blocker (see BLOCKER_PARTS) rather than on a real exterior or
    rendered surface."""
    if hit is None:
        return False
    name = hit["object"]
    if any(name == g.prefix + e for e in exclude):
        return True
    return name == g.prefix + "_interior" and float(hit["pos"][2]) > g.ZS_DOOR + g.DOOR_CW + 0.05


def drop_blocker_anchors(g, probe, exclude=BLOCKER_PARTS, reach=0.05):
    """remove every anchor whose surface (ray from `reach` along its normal) is a note-6 blocker; returns the
    dropped (type, pos, object) list."""
    keep, dropped = [], []
    for it in g.decals.items:
        n = np.asarray(it["normal"], float)
        hit = probe.cast(np.asarray(it["pos"], float) + n * reach, -n, 2 * reach)
        if blocker_hit(g, hit, exclude):
            dropped.append((it["type"], [round(float(v), 2) for v in it["pos"]], hit["object"]))
        else:
            keep.append(it)
    g.decals.items = keep
    return dropped


def cabin_decals(g, da, probe, rng):
    """v1_stone_watchtower r3: note-11 anchors of a square_cabin crown (g.CABIN): water streaks hanging below each
    lookout's sill board on the plank wall, and below every knee-strut corbel pad on the stone wall face."""
    cb = getattr(g, "CABIN", None)
    if not cb:
        return 0
    n0 = len(da)
    WOOD = {"M_timber", "M_timber_weathered"}
    do = cb["side"] / 2.0 - 0.04
    sides = [np.array(v, float) for v in ((0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0))]
    for k, c, ow, z_sill, oh in cb["openings"]:
        n = sides[k]
        t = np.array([-n[1], n[0], 0.0])
        p = t * (c + rng.uniform(-0.3, 0.3) * ow) + n * do + np.array([0.0, 0.0, z_sill - 0.13])
        D.below_points(da, probe, [p], [n], "water_streak", (0.14, 0.55), surfaces=WOOD, rng=rng, reach=0.3)
    for (fx, fy, fz) in cb.get("pads", ()):
        rad = np.array([fx, fy, 0.0]) / max(math.hypot(fx, fy), 1e-6)
        D.below_points(da, probe, [np.array([fx, fy, fz - 0.24])], [rad], "water_streak", (0.16, 0.6),
                       surfaces={"M_stone", "M_mortar"}, rng=rng, reach=0.4)
    return len(da) - n0


def round_tower_decals(g, seed=7410, exclude=BLOCKER_PARTS):
    """place the decal anchors of a rotor-less stone tower on its built meshes (module doc); returns the count.
    exclude (r3): blocker meshes no anchor may land on (blocker_hit)."""
    rng = np.random.RandomState(seed)
    da = g.decals
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    probe = D.SurfaceProbe(obs)
    n0 = len(da)

    def exterior(hit, wh_):
        return not blocker_hit(g, hit, exclude)
    STONE = {"M_stone", "M_mortar", "M_stone_dressed"}
    WOOD = {"M_timber", "M_timber_weathered"}
    R0 = g.R_BASE0
    door_half = math.asin(min(0.95, (g.DOOR_CW + 0.45) / R0))
    Rfar = R0 + 1.5
    wins = win_list(g)                                  # (az, window spec, dz): slits and lookouts
    wh = getattr(g, "WALL_HEAD", None)

    def free_az(a, margin=0.0):
        a = math.atan2(math.sin(a), math.cos(a))
        if abs(a) < door_half + margin:
            return False
        return all(abs(math.atan2(math.sin(a - w), math.cos(a - w))) > 0.12 + margin for w in g.WIN_AZ)

    # ---- damp_rise round the drum foot (north more likely), moss on the north foot ----
    az = [a for a in np.linspace(0, 2 * math.pi, 16, endpoint=False) + 0.13 if free_az(a)]
    D.base_ring(da, probe, (0, 0), Rfar, az, 0.24, "damp_rise", (0.95, 0.5), surfaces={"M_stone", "M_mortar"},
                rng=rng, up_shift=0.22)
    az = [a for a in np.linspace(math.radians(125), math.radians(235), 5) if free_az(a)]
    D.base_ring(da, probe, (0, 0), Rfar, az, 0.10, "moss", (0.6, 0.28), surfaces={"M_stone"}, rng=rng, up_shift=0.08)
    # ---- lichen on up-facing stone tops: string course, slit sills (the coping is sheltered by the eave) ----
    zs_top = g.Z_BAL1 + 0.10 if getattr(g, "BAND_STYLE", "") != "plain" else g.Z_BAND1 + 0.02
    pts = [(*_az_pt(a, float(R_out(g, zs_top)) + 0.05, 0)[:2], zs_top) for a in rng.uniform(0, 2 * math.pi, 5)]
    D.tops(da, probe, pts, "lichen", (0.3, 0.12), surfaces={"M_stone_dressed"}, rng=rng)
    for a, W, dz in wins:
        D.tops(da, probe, [(*_az_pt(a, float(R_out(g, W["z0"] - 0.06 + dz)) + 0.05, 0)[:2], W["z0"] + dz)], "lichen",
               (0.35, 0.12), surfaces={"M_stone_dressed"}, rng=rng)
    # ---- water streaks: below the slit sills, the string course, the coping drip ----
    for a, W, dz in wins:
        D.below_points(da, probe, [_az_pt(a, float(R_out(g, W["z0"] - 0.12 + dz)) + 0.02, W["z0"] - 0.13 + dz)], [_out(a)],
                       "water_streak",
                       (0.16, 0.7), surfaces=STONE, rng=rng, reach=0.4)
    for a in rng.uniform(0, 2 * math.pi, 5):
        D.below_points(da, probe, [_az_pt(a, float(R_out(g, g.Z_BAND0)), g.Z_BAND0 - 0.02)], [_out(a)],
                       "water_streak", (0.16, 0.7), surfaces=STONE, rng=rng, reach=0.5)
    if wh:
        z_cop = wh["z_top"] - 0.13
        for a in rng.uniform(0, 2 * math.pi, 6):
            D.below_points(da, probe, [_az_pt(a, wh["r_face"], z_cop)], [_out(a)], "water_streak", (0.16, 0.5),
                           surfaces={"M_stone", "M_mortar"}, rng=rng, reach=0.5)
    # ---- rust stains under the door ironwork ----
    iron = [o for o in obs if o.name.startswith(g.prefix + "_door_iron")]
    if iron:
        M_ = iron[0].matrix_world
        co = np.array([M_ @ v.co for v in iron[0].data.vertices])
        for zh in (g.Z_TH + 0.32, g.Z_TH + 1.02, g.Z_TH + 1.62):
            sel = np.abs(co[:, 2] - zh) < 0.04
            if sel.any():
                c = co[sel][np.argmin(co[sel][:, 0])] + np.array([0.12, 0.0, -0.05])
                D.below_points(da, probe, [c], [(0.0, -1.0, 0.0)], "rust_stain", (0.08, 0.35), surfaces=WOOD,
                               rng=rng, reach=0.25)
    # ---- soot above the door head and the slits ----
    D.above_opening(da, probe, (0.0, -g.R_DOOR), (0, -1, 0), 1.2, g.ZS_DOOR + g.DOOR_CW + 0.25, "soot", (1.0, 0.45),
                    surfaces=STONE, rng=rng, reach=0.6)
    for a, W, dz in wins:
        c = _az_pt(a, float(R_out(g, W["z1"] + 0.05 + dz)), 0.0)
        r = D.above_opening(da, probe, c[:2], _out(a), 0.4, W["z1"] + dz + W.get("lintel_h", 0.18) + 0.02, "soot",
                            (2 * W.get("hw_lintel", 0.37) * 0.6, 0.4),
                            surfaces=STONE, rng=rng, reach=0.5)
        for it in r:
            it["probability"] = 0.3
    # ---- cracks: door / slit corners, settlement low, under the string course ----
    fy = -g.R_DOOR - 0.02
    D.opening_corners(da, probe, [(-g.DOOR_CW - 0.2, fy, g.ZS_DOOR), (g.DOOR_CW + 0.2, fy, g.ZS_DOOR),
                                  (0.0, fy, g.ZS_DOOR + g.DOOR_CW + 0.15), (-g.DOOR_CW - 0.35, fy, 0.55)], (0, -1, 0),
                      "crack", (0.22, 0.5), surfaces=STONE, rng=rng, reach=0.5)
    for a, W, dz in wins:
        u, o = np.array([math.cos(a), math.sin(a), 0.0]), _out(a)
        Rz = float(R_out(g, W["z1"] + 0.05 + dz))
        D.opening_corners(da, probe, [_az_pt(a, Rz, W["z1"] + 0.10 + dz) + u * s * (W.get("hw_lintel", 0.37) + 0.05)
                                      for s in (-1, 1)], o, "crack",
                          (0.18, 0.4), surfaces=STONE, rng=rng, reach=0.5)
    for a in [a for a in rng.uniform(0, 2 * math.pi, 8) if free_az(a, 0.15)][:4]:
        D.opening_corners(da, probe, [_az_pt(a, float(R_out(g, 0.55)), 0.55)], _out(a), "crack", (0.25, 0.6),
                          surfaces=STONE, rng=rng, reach=0.5)
    for a in rng.uniform(0, 2 * math.pi, 3):
        D.opening_corners(da, probe, [_az_pt(a, float(R_out(g, g.Z_BAND0 - 0.2)), g.Z_BAND0 - 0.2)], _out(a), "crack",
                          (0.2, 0.45), surfaces=STONE, rng=rng, reach=0.5)
    # ---- grime at hand height on the door jambs ----
    D.opening_corners(da, probe, [(-g.DOOR_CW - 0.08, fy, 1.15), (g.DOOR_CW + 0.08, fy, 1.05)], (0, -1, 0), "grime",
                      (0.2, 0.5), surfaces={"M_stone_dressed"}, rng=rng, reach=0.5)
    # ---- moss on the north roof shingles ----
    rf = getattr(g, "ROOF", None)
    if rf:
        pts = []
        for a in rng.uniform(math.radians(130), math.radians(230), 6):
            r = rf["r_eave"] * rng.uniform(0.45, 0.85)
            pts.append((*_az_pt(a, r, 0)[:2], rf["z_eave"] + 6.0))
        D.tops(da, probe, pts, "moss", (0.5, 0.4), surfaces={"M_roof_shingle"}, rng=rng, min_up=0.3, h_from=0.5)
    # ---- a square_cabin crown: streaks under the lookout sill boards and under the strut corbel pads (r3) ----
    cabin_decals(g, da, probe, rng)
    # ---- mortar repairs on the shaft, render remnants beside the door, the plastered passage ----
    # (r3: accept=exterior -- a ray through a lookout never lands a patch on the dark room behind it)
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), Rfar, 5, (0.6, g.Z_BAND0 - 0.3), "repair_patch", ((0.3, 0.6), (0.25, 0.5)),
                   surfaces={"M_stone", "M_mortar"}, rng=rng, az_range=(door_half + 0.2, 2 * math.pi - door_half - 0.2),
                   avoid=avoid, min_sep=0.7, accept=exterior)
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), Rfar, 4, (g.Z_BAND1 + 0.3, g.Z_CORN0 - 0.2), "repair_patch",
                   ((0.3, 0.6), (0.25, 0.5)), surfaces={"M_stone", "M_mortar"}, rng=rng, avoid=avoid, min_sep=0.8,
                   accept=exterior)
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), Rfar, 3, (0.5, 1.9), "repair_patch", ((0.3, 0.55), (0.3, 0.6)),
                   surfaces={"M_stone", "M_mortar"}, rng=rng, az_range=(-door_half - 0.9, -door_half - 0.1),
                   avoid=avoid, min_sep=0.6, accept=exterior)
    for s in (-1, 1):                                   # plastered rubble passage (seen through the door)
        hit = probe.cast((0.0, -g.R_DOOR + 0.6, 1.2), (s, 0.0, 0.0), 1.2)
        da.add_hit("plaster_patch", hit, (0.4, 0.5), probability=0.5, seed=int(rng.randint(1 << 30)),
                   surfaces={"M_mortar"})
    n = len(da) - n0
    log(f"decal anchors placed: {n}  {da.counts()}")
    return n


def round_tower_decals_gated(g, seed=7410, max_offset=0.015, min_dot=0.85, count=(40, 120), exclude=BLOCKER_PARTS):
    """round_tower_decals + the drum family's three gates (see drum_decals.drum_tower_decals_gated): snap, validate,
    audit (the director's test); asserts 0 audit failures and a count in `count`.  exclude (r3): blocker meshes
    (BLOCKER_PARTS, plus <PREFIX>_interior above the door crown) are not decal surfaces: anchors on them are dropped
    before the gates, the validate gate rejects them, and a final check asserts none is left."""
    from ..anchor_validate import validate_anchors
    from ..anchor_audit import audit_anchors
    from ..decal_gate import snap_anchors
    from .drum_decals import _macro_normals
    round_tower_decals(g, seed=seed, exclude=exclude)
    probe = D.SurfaceProbe([o for o in g.coll.all_objects if o.type == "MESH"])
    for d_ in drop_blocker_anchors(g, probe, exclude):
        log(f"    decal anchor on a blocker dropped: {d_}")
    n_in = len(g.decals)
    _macro_normals(g)
    kept, dropped = snap_anchors(g.decals, probe, max_offset=max_offset, min_align=0.9, log=log)
    log(f"decal gate 1 (snap_anchors): {kept} kept, {dropped} dropped of {n_in}")
    rep = validate_anchors(g.decals, probe, apply=True, reach=0.03, offset=0.004, clear=0.10, min_sep=0.25,
                           fp_tol=0.06, fp_any=7, fp_mat=4, shrink=(0.75, 0.55), normal_min_dot=min_dot,
                           exclude_objects=tuple(g.prefix + e for e in exclude))
    log("decal gate 2 (anchor_validate): " + ", ".join(f"{k} {v}" for k, v in rep.items() if k != "bad"))
    for nm, why in rep["bad"]:
        log(f"    {nm}: {why}")
    bad = audit_anchors(g.decals, probe, max_offset=max_offset, min_dot=min_dot, drop=True)
    for b in bad:
        log(f"    audit drop: {b}")
    bad2 = audit_anchors(g.decals, probe, max_offset=max_offset, min_dot=min_dot, drop=False)
    on_blocker = drop_blocker_anchors(g, probe, exclude)
    assert not on_blocker, on_blocker
    n = len(g.decals)
    log(f"decal gate 3 (audit, director test): {len(bad)} dropped, {len(bad2)} failing after, {n} anchors "
        f"{g.decals.counts()}")
    assert not bad2, bad2
    assert count[0] <= n <= count[1], n
    g.decals.validation = dict(gates="decal_gate.snap_anchors + anchor_validate.validate_anchors + "
                                     "anchor_audit.audit_anchors", placed=n_in, kept=n,
                               audit=f"ray from +0.25 m along -Z: |offset| <= {max_offset} m, dot >= {min_dot}, "
                                     "front face, surface == material hit", audit_failures=0)
    return n
