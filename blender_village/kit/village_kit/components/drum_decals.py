"""components.drum_decals -- producer note 11 decal anchors for a stone-drum tower (the tower windmill and its
kit variants), kit 1.2.0.

drum_tower_decals(g) places ~90-120 anchors on the BUILT meshes of frame g with the village_kit.decals rules (every
anchor is ray-cast onto a real surface and reports that surface's palette slot):
    damp_rise     round the drum foot, more likely on the north (+Y) faces
    moss          footing / drum foot on the north arc, north apron shakes and cap shingles, the prop pads
    lichen        up-facing stone tops: cornice cap, upper string course, arcade and window sills
    water_streak  below the window and arcade sills, below the cornice drip, below the cap eave on the tower
                  boards, below the tail-boom end on the vane, below the wheel rim on the blades
    rust_stain    below the door strap hinges and ring pull, the prop collar and its lugs, the tail-boom bands,
                  the rotor arm bands and the prop dogs
    soot          above the door head and the slit windows, above the tower hatch
    crack         the door and window corners and lintel ends, arcade springers and crowns, settlement cracks low
                  in the rubble and under the band
    grime         hand height on the door jambs and the hatch frame
    repair_patch  mortar repairs on the rubble, patched tower boards
    plaster_patch render remnants on the rubble beside the door, the plastered passage
The sub-threshold relief dropped from the geometry (stone skin, spalls < 2 cm, wood checks, adze marks) is what the
crack / grime / repair decals and the Mask channels now carry.
"""
import math

import numpy as np

from .. import decals as D
from ..core import log
from .drum_frame import TZ, R_out, capw, face_axes, face_map, lean


def _az_pt(az, r, z):
    return np.array([math.sin(az) * r, -math.cos(az) * r, z])


def _out(az):
    return np.array([math.sin(az), -math.cos(az), 0.0])


def drum_tower_decals(g, seed=7310):
    """place the decal anchors of a drum tower on its built meshes (see the module doc); returns the count."""
    rng = np.random.RandomState(seed)
    da = g.decals
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    probe = D.SurfaceProbe(obs)
    n0 = len(da)
    STONE = {"M_stone", "M_mortar", "M_stone_dressed"}
    WOOD = {"M_timber", "M_timber_weathered"}
    R0 = g.R_BASE0
    door_half = math.asin(min(0.95, (g.DOOR_CW + 0.45) / R0))
    Rfar = R0 + 1.5

    def free_az(a, margin=0.0):
        a = math.atan2(math.sin(a), math.cos(a))
        if abs(a) < door_half + margin:
            return False
        return all(abs(math.atan2(math.sin(a - w), math.cos(a - w))) > 0.12 + margin for w in g.WIN_AZ)

    # ---- damp_rise round the drum foot (north more likely), moss on the north foot ----
    az = [a for a in np.linspace(0, 2 * math.pi, 18, endpoint=False) + 0.11 if free_az(a)]
    D.base_ring(da, probe, (0, 0), Rfar, az, 0.24, "damp_rise", (0.95, 0.5), surfaces={"M_stone", "M_mortar"},
                rng=rng, up_shift=0.22)
    az = [a for a in np.linspace(math.radians(125), math.radians(235), 5) if free_az(a)]
    D.base_ring(da, probe, (0, 0), Rfar, az, 0.10, "moss", (0.6, 0.28), surfaces={"M_stone"}, rng=rng, up_shift=0.08)
    # ---- lichen on up-facing stone tops: cornice cap, upper string course, arcade and window sills ----
    zc_top = g.Z_CORN0 + 0.45
    pts = [(*_az_pt(a, float(R_out(g, zc_top)) + 0.16, 0)[:2], zc_top) for a in rng.uniform(0, 2 * math.pi, 9)]
    D.tops(da, probe, pts, "lichen", (0.35, 0.22), surfaces={"M_stone_dressed"}, rng=rng)
    zs_top = g.Z_BAL1 + 0.10
    pts = [(*_az_pt(a, float(R_out(g, zs_top)) + 0.05, 0)[:2], zs_top) for a in rng.uniform(0, 2 * math.pi, 5)]
    D.tops(da, probe, pts, "lichen", (0.3, 0.12), surfaces={"M_stone_dressed"}, rng=rng)
    for a in g.ARCH_AZ[::2]:
        D.tops(da, probe, [(*_az_pt(a, float(R_out(g, g.ARCH["z0"])) - 0.12, 0)[:2], g.ARCH["z0"] + 0.05)],
               "lichen", (0.4, 0.18), surfaces={"M_stone_dressed"}, rng=rng)
    for a in g.WIN_AZ:
        D.tops(da, probe, [(*_az_pt(a, float(R_out(g, 1.24)) + 0.05, 0)[:2], 1.3)], "lichen", (0.35, 0.12),
               surfaces={"M_stone_dressed"}, rng=rng)
    # ---- water streaks: below the sills, the cornice drip, the cap eave, the boom end, the wheel rim ----
    for a in g.WIN_AZ:
        D.below_points(da, probe, [_az_pt(a, float(R_out(g, 1.18)) + 0.02, 1.17)], [_out(a)], "water_streak",
                       (0.16, 0.7), surfaces=STONE, rng=rng, reach=0.4)
    for a in g.ARCH_AZ[1::2]:
        D.below_points(da, probe, [_az_pt(a, float(R_out(g, g.ARCH["z0"])), g.ARCH["z0"] - 0.08)], [_out(a)],
                       "water_streak", (0.25, 0.32), surfaces=STONE, rng=rng, reach=0.5)
    for a in rng.uniform(0, 2 * math.pi, 7):
        D.below_points(da, probe, [_az_pt(a, float(R_out(g, g.Z_CORN0 + 0.2)), g.Z_CORN0 + 0.2)], [_out(a)],
                       "water_streak", (0.18, 0.8), surfaces=STONE, rng=rng, reach=0.5)
    for k in (0, 2, 5, 7):
        n_, t_ = face_axes(k)
        p = lean(g, face_map(g, k, np.array([rng.uniform(-0.2, 0.2)]), np.array([g.ZCT - 0.45]), np.array([0.03])))[0]
        D.below_points(da, probe, [p], [g.LEAN_R @ n_], "water_streak", (0.2, 0.9), surfaces=WOOD, rng=rng,
                       reach=0.4)
    # boom end over the vane (cap-local x' = TB_X1), both faces of the vane
    for sy in (-1.0, 1.0):
        p = lean(g, capw(g, np.array([[g.TB_X1 + 0.25, sy * 0.05, g.TB_Z - 0.2]])))[0]
        d = lean(g, capw(g, np.array([[0.0, sy, 0.0]]))) - lean(g, capw(g, np.zeros((1, 3))))
        D.below_points(da, probe, [p], [d[0]], "water_streak", (0.14, 0.7), surfaces=WOOD, rng=rng, reach=0.3)
    # below the wheel rim on the blades (front face of the wheel)
    fwd = lean(g, (g.HUB + g.S_AX)[None])[0] - lean(g, g.HUB[None])[0]
    for k in range(4):
        phi = g.PHI_A + (k + 0.5) * math.pi / 2
        p = g.HUB + g.E1 * math.cos(phi) * (g.RING_OUT - 0.05) + g.E2 * math.sin(phi) * (g.RING_OUT - 0.05)
        D.below_points(da, probe, [lean(g, p[None])[0]], [fwd], "water_streak", (0.12, 0.5), surfaces={"M_timber"},
                       rng=rng, reach=0.8)
    # ---- rust stains under ironwork ----
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
    for k in (5, 6, 7):
        n_, t_ = face_axes(k)
        for l_ in (-0.25, 0.2):
            p = lean(g, face_map(g, k, np.array([l_]), np.array([g.Z_COLLAR - 0.06]), np.array([0.07])))[0]
            D.below_points(da, probe, [p], [g.LEAN_R @ n_], "rust_stain", (0.07, 0.4), surfaces=WOOD, rng=rng,
                           reach=0.3)
    for xb in (-1.92, -3.30, -4.75):
        for sy in (-1.0, 1.0):
            if rng.rand() < 0.5:
                continue
            p = lean(g, capw(g, np.array([[xb, sy * (g.TB_YC + g.TB_RW / 2 + 0.005), g.TB_Z - 0.07]])))[0]
            d = lean(g, capw(g, np.array([[0.0, sy, 0.0]]))) - lean(g, capw(g, np.zeros((1, 3))))
            D.below_points(da, probe, [p], [d[0]], "rust_stain", (0.06, 0.25), surfaces=WOOD, rng=rng, reach=0.2)
    # ---- soot above the door head, the slit windows and the hatch ----
    D.above_opening(da, probe, (0.0, -g.R_DOOR), (0, -1, 0), 1.2, g.ZS_DOOR + g.DOOR_CW + 0.25, "soot", (1.0, 0.45),
                    surfaces=STONE, rng=rng, reach=0.6)
    for a in g.WIN_AZ:
        c = _az_pt(a, float(R_out(g, 1.9)), 0.0)
        r = D.above_opening(da, probe, c[:2], _out(a), 0.4, g.WIN["z1"] + 0.2, "soot", (0.45, 0.4), surfaces=STONE,
                            rng=rng, reach=0.5)
        for it in r:
            it["probability"] = 0.3
    n_, t_ = face_axes(0)
    ph = lean(g, face_map(g, 0, np.array([0.0]), np.array([float(TZ(g, 8.34)) + 0.2]), np.array([0.03])))[0]
    hit = probe.cast(ph + (g.LEAN_R @ n_) * 0.5, -(g.LEAN_R @ n_), 1.0)
    da.add_hit("soot", hit, (0.6, 0.35), probability=0.35, seed=int(rng.randint(1 << 30)), surfaces=WOOD)
    # ---- cracks: door / window / arcade corners, crown, settlement ----
    fy = -g.R_DOOR - 0.02
    D.opening_corners(da, probe, [(-g.DOOR_CW - 0.2, fy, g.ZS_DOOR), (g.DOOR_CW + 0.2, fy, g.ZS_DOOR),
                                  (0.0, fy, g.ZS_DOOR + g.DOOR_CW + 0.15), (-g.DOOR_CW - 0.35, fy, 0.55)], (0, -1, 0),
                      "crack", (0.22, 0.5), surfaces=STONE, rng=rng, reach=0.5)
    for a in g.WIN_AZ:
        u, o = np.array([math.cos(a), math.sin(a), 0.0]), _out(a)
        Rz = float(R_out(g, 1.9))
        D.opening_corners(da, probe, [_az_pt(a, Rz, 1.95) + u * s * 0.42 for s in (-1, 1)], o, "crack", (0.18, 0.4),
                          surfaces=STONE, rng=rng, reach=0.5)
    for a in rng.choice(np.array(g.ARCH_AZ), min(4, len(g.ARCH_AZ)), replace=False):
        u, o = np.array([math.cos(a), math.sin(a), 0.0]), _out(a)
        Rz = float(R_out(g, g.ARCH["zs"]))
        s = rng.choice([-1, 1])
        D.opening_corners(da, probe, [_az_pt(a, Rz, g.ARCH["zs"]) + u * s * (g.ARCH["cw"] + 0.12),
                                      _az_pt(a, Rz, g.ARCH["zs"] + g.ARCH["cw"] + 0.12)], o, "crack", (0.2, 0.45),
                          surfaces=STONE, rng=rng, reach=0.5)
    for a in [a for a in rng.uniform(0, 2 * math.pi, 8) if free_az(a, 0.15)][:4]:
        D.opening_corners(da, probe, [_az_pt(a, float(R_out(g, 0.55)), 0.55)], _out(a), "crack", (0.25, 0.6),
                          surfaces=STONE, rng=rng, reach=0.5)
    for a in rng.uniform(0, 2 * math.pi, 2):
        D.opening_corners(da, probe, [_az_pt(a, float(R_out(g, g.Z_BAND0 - 0.2)), g.Z_BAND0 - 0.2)], _out(a), "crack",
                          (0.2, 0.45), surfaces=STONE, rng=rng, reach=0.5)
    # ---- grime at hand height on the door jambs, the hatch frame ----
    D.opening_corners(da, probe, [(-g.DOOR_CW - 0.08, fy, 1.15), (g.DOOR_CW + 0.08, fy, 1.05)], (0, -1, 0), "grime",
                      (0.2, 0.5), surfaces={"M_stone_dressed"}, rng=rng, reach=0.5)
    hit = probe.cast(ph + np.array([0, 0, -0.75]) + (g.LEAN_R @ n_) * 0.5, -(g.LEAN_R @ n_), 1.0)
    da.add_hit("grime", hit, (0.5, 0.3), probability=0.5, seed=int(rng.randint(1 << 30)), surfaces=WOOD)
    # ---- moss: north apron shakes, north cap shingles, prop pads ----
    pts = []
    for a in rng.uniform(math.radians(140), math.radians(220), 5):
        r = g.AP_RT + rng.uniform(0.35, 0.8) * (g.AP_RE - g.AP_RT)
        pts.append((*_az_pt(a, r, 0)[:2], g.AP_ZE + 1.2))
    D.tops(da, probe, pts, "moss", (0.6, 0.45), surfaces={"M_roof_shake"}, rng=rng, min_up=0.4, h_from=1.5)
    pts = []
    for x_ in (-0.9, -0.3, 0.3):
        p = lean(g, capw(g, np.array([[x_, g.CAP_B - 0.35, 0.0]])))[0]
        pts.append((p[0], p[1], g.CAP_ZE + 0.6))
    D.tops(da, probe, pts, "moss", (0.5, 0.4), surfaces={"M_roof_shingle"}, rng=rng, min_up=0.3, h_from=1.5)
    for ob in obs:
        if ob.name == g.prefix + "_prop_anchors":
            co = np.array([ob.matrix_world @ v.co for v in ob.data.vertices])
            for c in getattr(g, "prop_feet", []):
                near = co[np.hypot(co[:, 0] - c[0], co[:, 1] - c[1]) < 0.4]
                if len(near):
                    top = near[np.argmax(near[:, 2])]
                    D.tops(da, probe, [(top[0] + 0.12, top[1], 0.3)], "moss", (0.3, 0.25), surfaces={"M_stone"},
                           rng=rng, min_up=0.4)
    # ---- mortar repairs on the rubble, patched tower boards, render remnants, plastered passage ----
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), Rfar, 5, (0.6, g.Z_BAND0 - 0.25), "repair_patch", ((0.3, 0.6), (0.25, 0.5)),
                   surfaces={"M_stone", "M_mortar"}, rng=rng, az_range=(door_half + 0.2, 2 * math.pi - door_half - 0.2),
                   avoid=avoid, min_sep=0.7)
    avoid = [it["pos"] for it in da.items]
    D.wall_scatter(da, probe, (0, 0), Rfar, 3, (0.5, 1.9), "plaster_patch", ((0.3, 0.55), (0.3, 0.6)),
                   surfaces={"M_stone", "M_mortar"}, rng=rng, az_range=(-door_half - 0.9, -door_half - 0.1),
                   avoid=avoid, min_sep=0.6)
    for k in (1, 6, 7):
        n_, t_ = face_axes(k)
        z_ = g.TW_Z0 + rng.uniform(0.25, 0.7) * (g.TW_Z1 - g.TW_Z0)
        p = lean(g, face_map(g, k, np.array([rng.uniform(-0.3, 0.3)]), np.array([z_]), np.array([0.03])))[0]
        hit = probe.cast(p + (g.LEAN_R @ n_) * 0.5, -(g.LEAN_R @ n_), 1.0)
        da.add_hit("repair_patch", hit, (0.25, 0.6), seed=int(rng.randint(1 << 30)), surfaces=WOOD)
    for s in (-1, 1):                                   # plastered rubble passage (seen through the door)
        hit = probe.cast((0.0, -g.R_DOOR + 0.6, 1.2), (s, 0.0, 0.0), 1.2)
        da.add_hit("plaster_patch", hit, (0.4, 0.5), probability=0.5, seed=int(rng.randint(1 << 30)),
                   surfaces={"M_mortar"})
    n = len(da) - n0
    log(f"decal anchors placed: {n}  {da.counts()}")
    return n


# =================================================================================================================
# kit 1.4.0: the gated version (mill director r7 must-fix 2 / sign-off audit): snap + validate + audit, assert 0
# =================================================================================================================
def wheel_end_streaks(g, da, n=4, size=(0.12, 0.45), seed=7311):
    """water_streak anchors on the OUTER ENDS of the wheel blades (note 11: 'the ends of the wheel'): the largest
    front-facing blade faces within 0.35 m of the tip radius, one per blade spread round the wheel; the decal's top
    edge sits at the blade tip (up = radially outward)."""
    obs = [o for o in g.coll.all_objects if o.type == "MESH" and o.name == g.prefix + "_wheel_blades"]
    if not obs:
        return 0
    ob = obs[0]
    M = np.array(ob.matrix_world)
    me = ob.data
    hub = lean(g, g.HUB[None])[0]
    ax = lean(g, (g.HUB + g.S_AX)[None])[0] - hub
    ax /= np.linalg.norm(ax)
    rows = []
    for p in me.polygons:
        c = M[:3, :3] @ np.array(p.center) + M[:3, 3]
        nrm = M[:3, :3] @ np.array(p.normal)
        nrm /= max(np.linalg.norm(nrm), 1e-9)
        v = c - hub
        rad = v - np.dot(v, ax) * ax
        rows.append((c, nrm, np.linalg.norm(rad), rad, p.area, p.material_index))
    rmax = max(r[2] for r in rows)
    slots = [m.name if m else "M_timber" for m in me.materials] or ["M_timber"]
    rng = np.random.RandomState(seed)
    e1 = np.cross(ax, (0, 0, 1.0))
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    added = 0
    for k in range(n):
        want = 2 * math.pi * (k + 0.25) / n
        best = None
        for (c, nrm, r, rad, area, mi) in rows:
            if r < rmax - 0.35 or r > rmax - 0.06 or abs(float(np.dot(nrm, ax))) < 0.85 or area < 0.004:
                continue
            a = math.atan2(float(np.dot(rad, e2)), float(np.dot(rad, e1)))
            da_ = abs(math.atan2(math.sin(a - want), math.cos(a - want)))
            score = da_ - 0.5 * area
            if best is None or score < best[0]:
                best = (score, c, nrm, rad, mi)
        if best is None:
            continue
        _, c, nrm, rad, mi = best
        up = rad / np.linalg.norm(rad)
        h = size[1] * rng.uniform(0.85, 1.15)
        da.add("water_streak", c, nrm, (size[0], h), slots[min(mi, len(slots) - 1)], probability=0.55,
               seed=int(rng.randint(1 << 30)), up=up)
        added += 1
    log(f"wheel-end water streaks: {added} on the outer blade ends (tip radius {rmax:.2f} m from the shaft)")
    return added


def _macro_normals(g):
    """the normal each anchor should project along: horizontal-radial on the drum walls (cracks on voussoirs, soot
    over the door, streaks under the sills -- never tilted by a chamfer or a bed), +Z on stone tops, else its own."""
    for it in g.decals.items:
        p, n = np.asarray(it["pos"], float), np.asarray(it["normal"], float)
        rxy = math.hypot(p[0], p[1])
        if p[2] < g.Z_CORN0 + 0.5 and rxy > 0.3 and rxy < float(R_out(g, max(p[2], 0.0))) + 0.45:
            radial = np.array([p[0] / rxy, p[1] / rxy, 0.0])
            if abs(n[2]) < 0.75 and float(np.dot(n, radial)) > 0.6:
                it["macro"] = radial
            elif n[2] >= 0.75:
                it["macro"] = np.array([0.0, 0.0, 1.0])


def drum_tower_decals_gated(g, seed=7310, max_offset=0.015, min_dot=0.85, count=(40, 120)):
    """drum_tower_decals + the wheel-end streaks, then the producer-note-11 gates and an audit that asserts:
      1. decal_gate.snap_anchors (macro normals, first-surface snap, front faces only, exposure, de-dup);
      2. anchor_validate.validate_anchors (surface slot, outward, not buried, 3x3 footprint);
      3. decal_gate.audit_anchors -- the director's test: a ray from 0.25 m out along each anchor's -Z hits a front
         face within +-1.5 cm, face normal . anchor Z >= 0.85, `surface` == the material hit.  Failures are dropped
         and the audit re-run; the build asserts 0 failures and a count in `count`."""
    from ..anchor_validate import validate_anchors
    from ..anchor_audit import audit_anchors
    from ..decal_gate import snap_anchors
    drum_tower_decals(g, seed=seed)
    wheel_end_streaks(g, g.decals)
    probe = D.SurfaceProbe([o for o in g.coll.all_objects if o.type == "MESH"])
    n_in = len(g.decals)
    _macro_normals(g)
    kept, dropped = snap_anchors(g.decals, probe, max_offset=max_offset, min_align=0.9, log=log)
    log(f"decal gate 1 (snap_anchors): {kept} kept, {dropped} dropped of {n_in}")
    rep = validate_anchors(g.decals, probe, apply=True, reach=0.03, offset=0.004, clear=0.10, min_sep=0.25,
                           fp_tol=0.06, fp_any=7, fp_mat=4, shrink=(0.75, 0.55), normal_min_dot=min_dot)
    log("decal gate 2 (anchor_validate): " + ", ".join(f"{k} {v}" for k, v in rep.items() if k != "bad"))
    for nm, why in rep["bad"]:
        log(f"    {nm}: {why}")
    bad = audit_anchors(g.decals, probe, max_offset=max_offset, min_dot=min_dot, drop=True)
    for b in bad:
        log(f"    audit drop: {b}")
    bad2 = audit_anchors(g.decals, probe, max_offset=max_offset, min_dot=min_dot, drop=False)
    n = len(g.decals)
    log(f"decal gate 3 (audit, director test): {len(bad)} dropped, {len(bad2)} failing after, {n} anchors "
        f"{g.decals.counts()}")
    assert not bad2, bad2
    assert count[0] <= n <= count[1], n
    g.decals.validation = dict(gates="decal_gate.snap_anchors + anchor_validate.validate_anchors + "
                                     "decal_gate.audit_anchors", placed=n_in, kept=n,
                               audit=f"ray from +0.25 m along -Z: |offset| <= {max_offset} m, dot >= {min_dot}, "
                                     "front face, surface == material hit", audit_failures=0)
    return n
