"""components.oct_decals -- producer note 11 decal anchors for a tiered octagonal hall building (kit 1.1.0, from the
hilltop keep).  Every anchor is found by ray-casting the built meshes (decals.SurfaceProbe), so it sits on a real
surface and records that surface's palette slot.

    damp_rise     the foot of the hall facets, the annex walls and the turret (north faces more likely)
    moss          footing tops and north roof butts near the skirt eave, the collar comb, the cushion top,
                  north turret-cap shingles
    lichen        pedestal tops, window sills, the threshold and the step, the cone ledge slabs, cushion stones
    water_streak  below the window sills, below the bell-cap drip line on the cone (the cap overhang throws its
                  water onto the flaring cone), below the turret-cap drip on the cushion, below the cushion lip
    soot          above the arched door, the window heads, the lantern openings (smoke vents), the annex door
    rust_stain    below the strap-hinge terminals, the pintles and the ring pull of both doors
    crack         the springing points and crown of the arch, window corners, lintel ends, the hall / annex
                  settlement junction, and the timber checks note 11 dropped from the geometry (oct_frame.dropped_checks)
    grime         hand height on the door jambs and the posts flanking the door
    repair_patch  repointing patches on the rubble walls;  plaster_patch  on the daub eave filling of the annex
Aim: ~90-120 anchors.

oct_building_decals(g, seed=9900)   KIT COMPONENT (the build_building `decals` hook)
"""
import math

import numpy as np

from ..core import log
from .. import decals as D
from .oct_frame import FN, cush_lip_z, cush_out_r, fmap


def _fac_hit(probe, k, x, z, surfaces=None, reach=1.6):
    """horizontal ray onto hall facet k at facet-local x, height z."""
    o = fmap(k, np.array([x]), np.array([z]), np.array([reach]))[0]
    d = -np.array([FN[k][0], FN[k][1], 0.0])
    hit = probe.cast(o, d, reach * 2)
    if hit is None or (surfaces is not None and hit["surface"] not in surfaces):
        return None
    return hit


def _ray(probe, o, d, dist=4.0, surfaces=None):
    hit = probe.cast(np.asarray(o, float), np.asarray(d, float), dist)
    if hit is None or (surfaces is not None and hit["surface"] not in surfaces):
        return None
    return hit


def oct_building_decals(g, seed=9900):
    rng = np.random.RandomState(seed)
    da = g.decals
    obs = [o for o in g.coll.all_objects if o.type == "MESH"]
    probe = D.SurfaceProbe(obs)
    n0 = len(da)
    S = lambda: int(rng.randint(1 << 30))  # noqa: E731
    STONE = {"M_stone", "M_mortar"}
    door = next(o for o in g.OPENINGS if o["kind"] == "arch")
    kd = door["k"]

    def nb(normal, base, gain=0.6):
        return float(np.clip(base * (1.0 + gain * max(0.0, float(normal[1]))), 0, 1))

    # ---- damp_rise: hall facet feet (not under the annex, not in the doorway)
    for k in range(8):
        for x in (-0.9, 0.8):
            if k == kd and abs(x - door["xc"]) < door["hw"] + 0.5:
                x = door["xc"] - door["hw"] - 0.75
            h = rng.uniform(0.35, 0.6)
            hit = _fac_hit(probe, k, x, 0.25, STONE)
            if hit is None or hit["pos"][0] < g.WX_E + 0.05 and g.WY_S - 0.1 < hit["pos"][1] < g.WY_N + 0.1:
                continue
            da.add_hit("damp_rise", hit, (rng.uniform(0.8, 1.2), h), probability=nb(hit["normal"], 0.75), seed=S(),
                       shift_down=-h / 2 + 0.2)
    # annex walls: S, N and W feet
    xs = np.linspace(g.WX_W + 0.6, g.WX_E - 0.6, 5)
    for x in xs:
        for y0, dy in ((g.WY_S - 2.0, 1.0), (g.WY_N + 2.0, -1.0)):
            hit = _ray(probe, (x, y0, 0.25), (0, dy, 0), 3.0, STONE)
            if hit is not None and rng.rand() < 0.75:
                h = rng.uniform(0.35, 0.6)
                da.add_hit("damp_rise", hit, (rng.uniform(0.8, 1.2), h), probability=nb(hit["normal"], 0.75),
                           seed=S(), shift_down=-h / 2 + 0.2)
    for az in (math.radians(a) for a in (100, 150, 200, 250)):
        c = g.TUR_C
        u = np.array([math.cos(az), math.sin(az), 0.0])
        hit = _ray(probe, np.array([c[0], c[1], 0.3]) + u * 4.0, -u, 4.0, STONE)
        if hit is not None:
            da.add_hit("damp_rise", hit, (0.9, 0.5), probability=nb(hit["normal"], 0.75), seed=S(), shift_down=-0.05)
    # ---- moss: footing tops on the north side, north skirt-roof butts near the eave, collar comb, cushion top,
    # north turret-cap shingles
    for k in (6, 7, 0):
        for x in (-1.0, 0.0, 1.0):
            p = fmap(k, np.array([x]), np.array([0.6]), np.array([0.06]))[0]
            hit = _ray(probe, p, (0, 0, -1), 0.8, {"M_stone"})
            if hit is not None and hit["normal"][2] > 0.4:
                da.add_hit("moss", hit, (0.4, 0.25), probability=0.65, seed=S(), up=(FN[k][0], FN[k][1], 0))
    for a in np.radians(np.linspace(40, 140, 5)):
        r = g.SKIRT.p_lip - 0.35
        hit = _ray(probe, (r * math.cos(a), r * math.sin(a), 12.0), (0, 0, -1), 12.0, {"M_roof_shingle"})
        if hit is not None:
            da.add_hit("moss", hit, (0.7, 0.45), probability=0.6, seed=S(), up=(math.cos(a), math.sin(a), 0))
    for a in np.radians(np.linspace(20, 160, 4)):
        r = g.COLLAR_TOP_R + 0.05
        hit = _ray(probe, (r * math.cos(a), r * math.sin(a), 8.0), (0, 0, -1), 4.0, {"M_roof_shake"})
        if hit is not None:
            da.add_hit("moss", hit, (0.45, 0.3), probability=0.55, seed=S(), up=(math.cos(a), math.sin(a), 0))
    for a in np.radians(np.linspace(0, 300, 4) + 30):
        r = float(cush_out_r(a)) - 0.12
        c = g.TUR_C
        hit = _ray(probe, (c[0] + r * math.cos(a), c[1] + r * math.sin(a), 8.0), (0, 0, -1), 4.0, {"M_stone"})
        if hit is not None and hit["normal"][2] > 0.3:
            da.add_hit("moss", hit, (0.35, 0.25), probability=0.6, seed=S(), up=(math.cos(a), math.sin(a), 0))
    for a in np.radians((60, 100, 140)):
        r = g.TUR_CAP.p_lip - 0.35
        c = g.TUR_C
        hit = _ray(probe, (c[0] + r * math.cos(a), c[1] + r * math.sin(a), 12.0), (0, 0, -1), 8.0, {"M_roof_shingle"})
        if hit is not None:
            da.add_hit("moss", hit, (0.5, 0.35), probability=0.55, seed=S(), up=(math.cos(a), math.sin(a), 0))
    # ---- lichen: pedestal tops, sills, threshold / step, ledge slabs, cushion faces
    for c_ in range(8):
        a = math.radians(135 + 45 * c_ + 22.5)
        p = np.array([math.cos(a) * g.R_POST, math.sin(a) * g.R_POST, 0.9])
        p = p + np.array([math.cos(a), math.sin(a), 0]) * 0.13
        hit = _ray(probe, p, (0, 0, -1), 1.0, {"M_stone_dressed"})
        if hit is not None and hit["normal"][2] > 0.5 and rng.rand() < 0.7:
            da.add_hit("lichen", hit, (0.18, 0.15), probability=0.5, seed=S())
    for op in g.OPENINGS:
        if op["kind"] != "rect":
            continue
        p = fmap(op["k"], np.array([op["xc"] + rng.uniform(-0.2, 0.2) * op["hw"]]), np.array([op["z0"] + 0.3]),
                 np.array([0.06]))[0]
        hit = _ray(probe, p, (0, 0, -1), 0.6, {"M_stone_dressed"})
        if hit is not None and hit["normal"][2] > 0.5:
            da.add_hit("lichen", hit, (0.2, 0.12), probability=0.5, seed=S())
    for x, w in ((door["xc"] - 0.4, 0.55), (door["xc"] + 0.45, 0.7), (door["xc"] + 0.1, 0.0)):
        p = fmap(kd, np.array([x]), np.array([0.6]), np.array([w]))[0]
        hit = _ray(probe, p, (0, 0, -1), 1.0, {"M_stone", "M_stone_dressed"})
        if hit is not None:
            da.add_hit("lichen", hit, (0.22, 0.18), probability=0.45, seed=S())
    for a in np.radians((15, 95, 175, 255, 335)):
        r = float(np.interp(g.COLLAR_TOP_Z + 0.12, g.CONE_ZF, g.CONE_RF)) + 0.12
        hit = _ray(probe, (r * math.cos(a), r * math.sin(a), 7.5), (0, 0, -1), 2.0, {"M_stone"})
        if hit is not None and hit["normal"][2] > 0.4:
            da.add_hit("lichen", hit, (0.25, 0.2), probability=0.5, seed=S())
    for a in np.radians((-60, 30, 120)):
        c = g.TUR_C
        z = float(cush_lip_z(a)) + 0.15
        u = np.array([math.cos(a), math.sin(a), 0.0])
        hit = _ray(probe, np.array([c[0], c[1], z]) + u * 3.0, -u, 3.0, {"M_stone"})
        if hit is not None:
            da.add_hit("lichen", hit, (0.25, 0.2), probability=0.5, seed=S())
    # ---- water_streak: below sills, below the cap drip on the cone, below the turret-cap drip and the cushion lip
    for op in g.OPENINGS:
        if op["kind"] != "rect" or not op.get("frame", True) and op["hw"] < 0.15:
            continue
        for dx in (-0.6, 0.5):
            x = op["xc"] + dx * op["hw"]
            hit = _fac_hit(probe, op["k"], x, op["z0"] - 0.35, STONE)
            if hit is not None:
                da.add_hit("water_streak", hit, (0.12, 0.7), probability=0.6, seed=S(), shift_down=0.2)
    drip_r = g.CAP.p_lip
    zc = float(np.interp(drip_r * 0.98, g.CONE_RF[::-1], g.CONE_ZF[::-1]))
    for a in np.radians(np.linspace(0, 315, 8) + 10):
        u = np.array([math.cos(a), math.sin(a), 0.0])
        hit = _ray(probe, u * (drip_r + 1.5) + np.array([0, 0, zc - 0.25]), -u, 2.5, STONE)
        if hit is not None and rng.rand() < 0.7:
            da.add_hit("water_streak", hit, (0.15, 0.8), probability=0.55, seed=S(), shift_down=0.3)
    for a in np.radians((-40, 60, 160)):
        c = g.TUR_C
        z = float(cush_lip_z(a)) - 0.25
        u = np.array([math.cos(a), math.sin(a), 0.0])
        hit = _ray(probe, np.array([c[0], c[1], z]) + u * 3.0, -u, 3.0, STONE)
        if hit is not None:
            da.add_hit("water_streak", hit, (0.14, 0.7), probability=0.55, seed=S(), shift_down=0.25)
    # ---- soot: above the arched door, the window heads, the lantern openings, the annex door
    crown = door["zs"] + door["hw"] + 0.42
    hit = _fac_hit(probe, kd, door["xc"], crown, {"M_stone", "M_mortar", "M_stone_dressed"})
    if hit is not None:
        da.add_hit("soot", hit, (0.9, 0.5), probability=0.6, seed=S(), shift_down=-0.25)
    for op in g.OPENINGS:
        if op["kind"] == "rect" and op["hw"] > 0.2:
            hit = _fac_hit(probe, op["k"], op["xc"], op["z1"] + 0.4, STONE)
            if hit is not None:
                da.add_hit("soot", hit, (op["hw"] * 1.6, 0.45), probability=0.5, seed=S(), shift_down=-0.2)
    for kk, ox in ((6, 0.05), (5, -0.1)):
        phi = math.radians(45 * kk)
        n3 = np.array([math.cos(phi), math.sin(phi), 0.0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0.0])
        p = n3 * (g.LANT_APO + 1.0) + t3 * (ox + 0.28) + np.array([0, 0, g.LANT_Z0 + 0.62])
        hit = _ray(probe, p, -n3, 2.0, {"M_timber_weathered", "M_timber"})
        if hit is not None:
            da.add_hit("soot", hit, (0.3, 0.3), probability=0.6, seed=S())
    hit = _ray(probe, (g.WDOOR["xc"], g.WY_S - 1.5, g.WDOOR["z1"] + 0.5), (0, 1, 0), 2.5, STONE | {"M_timber"})
    if hit is not None:
        da.add_hit("soot", hit, (0.8, 0.4), probability=0.45, seed=S(), shift_down=-0.1)
    # ---- rust_stain: below hinge terminals, pintles and the ring pull
    n_d = np.array([FN[kd][0], FN[kd][1], 0.0])
    R = door["hw"] + 0.03
    for zh, ln in ((0.42, 0.78), (1.12, 0.78), (1.80, 0.62)):
        for xx in (door["xc"] + R - 0.05, door["xc"] + R - ln + 0.05):
            p = fmap(kd, np.array([xx]), np.array([zh - 0.05]), np.array([-door["depth"] + 0.6]))[0]
            hit = _ray(probe, p, -n_d, 1.0, {"M_timber", "M_timber_weathered", "M_stone_dressed"})
            if hit is not None:
                da.add_hit("rust_stain", hit, (0.06, 0.28), probability=0.65, seed=S(), shift_down=0.12)
    p = fmap(kd, np.array([door["xc"] - R + 0.17]), np.array([0.88]), np.array([-door["depth"] + 0.6]))[0]
    hit = _ray(probe, p, -n_d, 1.0, {"M_timber"})
    if hit is not None:
        da.add_hit("rust_stain", hit, (0.08, 0.3), probability=0.6, seed=S(), shift_down=0.1)
    wd = g.WDOOR
    for zh in (0.42, 1.15, 1.92):
        hit = _ray(probe, (wd["xc"] - wd["hw"] + 0.62, g.WY_S - 1.0, zh - 0.05), (0, 1, 0), 2.0,
                   {"M_timber", "M_timber_weathered"})
        if hit is not None:
            da.add_hit("rust_stain", hit, (0.06, 0.25), probability=0.6, seed=S(), shift_down=0.1)
    # ---- crack: arch springing / crown, window corners, lintel ends, settlement at the annex junction
    for x, z in ((door["xc"] - door["hw"] - 0.35, door["zs"]), (door["xc"] + door["hw"] + 0.35, door["zs"]),
                 (door["xc"] + 0.15, door["zs"] + door["hw"] + 0.36)):
        hit = _fac_hit(probe, kd, x, z, STONE | {"M_stone_dressed"})
        if hit is not None:
            da.add_hit("crack", hit, (0.25, 0.4), probability=0.5, seed=S())
    for op in g.OPENINGS:
        if op["kind"] != "rect":
            continue
        for sx, z in ((-1, op["z1"] + 0.05), (1, op["z1"] + 0.05), (1, op["z0"] - 0.15)):
            if rng.rand() < 0.8:
                hit = _fac_hit(probe, op["k"], op["xc"] + sx * (op["hw"] + 0.3), z, STONE)
                if hit is not None:
                    da.add_hit("crack", hit, (0.22, 0.35), probability=0.5, seed=S())
    for x in (wd["xc"] - wd["hw"] - 0.4, wd["xc"] + wd["hw"] + 0.4):
        hit = _ray(probe, (x, g.WY_S - 1.0, wd["z1"] + 0.15), (0, 1, 0), 2.0, STONE)
        if hit is not None:
            da.add_hit("crack", hit, (0.2, 0.35), probability=0.5, seed=S())
    ww = g.WWIN
    for x in (ww["xc"] - ww["hw"] - 0.3, ww["xc"] + ww["hw"] + 0.3):
        hit = _ray(probe, (x, g.WY_S - 1.0, ww["z0"] - 0.2), (0, 1, 0), 2.0, STONE)
        if hit is not None:
            da.add_hit("crack", hit, (0.2, 0.3), probability=0.5, seed=S())
    for z in (0.8, 1.9):                         # settlement where the annex S wall meets the hall
        hit = _ray(probe, (-3.9, g.WY_S - 1.2, z), (0, 1, 0), 2.0, STONE)
        if hit is not None:
            da.add_hit("crack", hit, (0.2, 0.5), probability=0.55, seed=S())
    dropped = sorted(g.dropped_checks, key=lambda c_: -c_["depth"])[:10]
    for ck in dropped:
        n_ = np.asarray(ck["normal"], float)
        hit = _ray(probe, np.asarray(ck["pos"], float) + n_ * 0.3, -n_, 0.6, {"M_timber", "M_timber_weathered"})
        if hit is not None:
            da.add_hit("crack", hit, (0.04, max(ck["length"], 0.2)), probability=0.7, seed=S(),
                       up=tuple(ck["along"]))
    # ---- grime: hand height on the door jambs and the posts flanking the door
    for x in (door["xc"] - door["hw"] - 0.15, door["xc"] + door["hw"] + 0.15):
        hit = _fac_hit(probe, kd, x, 1.1, {"M_stone_dressed", "M_stone"})
        if hit is not None:
            da.add_hit("grime", hit, (0.25, 0.4), probability=0.6, seed=S())
    for x in (wd["xc"] - wd["hw"] - 0.09, wd["xc"] + wd["hw"] + 0.09):
        hit = _ray(probe, (x, g.WY_S - 1.0, 1.1), (0, 1, 0), 2.0, {"M_timber", "M_timber_weathered"})
        if hit is not None:
            da.add_hit("grime", hit, (0.12, 0.4), probability=0.6, seed=S())
    for c_ in (2, 3):
        a = math.radians(135 + 45 * c_ + 22.5)
        u = np.array([math.cos(a), math.sin(a), 0.0])
        hit = _ray(probe, u * (g.R_POST + 1.0) + np.array([0, 0, 1.15]), -u, 1.5, {"M_timber"})
        if hit is not None:
            da.add_hit("grime", hit, (0.2, 0.35), probability=0.5, seed=S())
    # ---- repair_patch on the rubble (repointing), plaster_patch on the annex's daub eave filling
    for k, x, z in ((2, -1.0, 1.0), (4, 0.6, 2.2), (5, 0.9, 0.9), (7, -0.4, 1.6)):
        hit = _fac_hit(probe, k, x, z, STONE)
        if hit is not None:
            da.add_hit("repair_patch", hit, (rng.uniform(0.4, 0.7), rng.uniform(0.3, 0.5)), probability=0.35,
                       seed=S())
    for x in (g.WX_W + 1.5, 0.5 * (g.WX_W + g.WX_E)):
        hit = _ray(probe, (x, g.WY_S - 1.5, g.W_WALL_H + 0.08), (0, 1, 0), 2.5, {"M_daub"})
        if hit is not None:
            da.add_hit("plaster_patch", hit, (0.4, 0.12), probability=0.45, seed=S())
    log(f"  decal anchors: {len(da) - n0} ({da.counts()})")
    return len(da) - n0
