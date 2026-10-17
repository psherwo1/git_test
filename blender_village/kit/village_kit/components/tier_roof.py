"""components.tier_roof -- stackable bell-cast roof TIERS and their junctions (kit 1.7.0, v2_tiered_hall).

    bell_tier(g, name, on, overhang, profile, ...)     KIT COMPONENT
        an octagonal bell-cast roof tier seated on ANY declared body (polygon hall, round drum, board belt,
        turret shaft): the keep's oct_roof.build_cap (chunky SIZE_TABLE shingles, starter course, hip boards or
        saddles, rafters / soffit / fascia, sarking deck, ring beam, corner brackets) on an OctRoof whose eave
        height is solved from the body top (the roof surface stands `rise` over the ring beam at the wall line),
        plus a closed wall-head band (frieze) from the wall top up to the soffit, so the wall-to-roof joint is
        closed all round.  `through` names the bodies rising through the tier: every roof piece wholly inside
        them is dropped and the covering stops at their face (p_top), the flashing below closes the joint.
        Profiles: PROFILES ('skirt' ~40 deg bell-cast to 25, 'skirt_steep' 45, 'cap' 50, 'spire' 60 witch hat).
        Objects <P>_<name>_shingles / _hips / _structure / _deck / _band.
        kit 1.7.1: on a ROUND body the default is a round witch-hat tier (sides=0 -> round_tier: the hut cone on a
        sub-frame, round wall plate and eave-closure frieze at the body radius, no brackets); sides=8 forces the
        octagonal tier.
        kit 1.7.2: every tier runs tier_frame.roof_clearance when it registers (two tiers on different bodies that
        overlap in plan need >= g.roof_clear = 0.50 m clear height, else RoofClearanceError names both); round
        tiers take their deck / eave closure from the public components.round_roof_parts (no private import from
        tower_roof) and drop every zero-face mesh object they create (drop_empty_meshes).
        kit 1.7.3: octagonal tiers lay eave_deck_lap (deck_lap=True): a continuous sarking strip from the main deck
        across the wall line and over the whole overhang, so no shingle joint opens on the body or the wall face
        under the eave where a `through` body cuts the eave structure (v2 round 3's skirt1 / tur_nw slit).
        kit 1.8.0: polygon tiers with ANY number of sides -- sides != 8 (or engine="pyramid") builds the tier with the
        kit's N-sided bell-cast roof, pyramid_roof / PyramidSurface, registered through the polygonal-roof protocol
        (OctRoof and PyramidSurface share n, phi, c, rot, p_lip, Pp, zb, m_of_p, p_of_m, surf); 8-sided tiers keep
        the octagonal OctRoof + build_cap path unchanged.
    eave_deck_lap(g, name, roof, p_wall, coll, ...)    KIT COMPONENT (kit 1.7.3)   -> <P>_<name>_deck_lap
    tier_finial(g, name, scale, ...)                  KIT COMPONENT: lead hat fitted over the tier's apex
        shingles + the kit's turned finial (components.finial)          -> <P>_<name>_finial
    roof_flashing(g, roof_name, body_name, ...)        KIT COMPONENT (the junction module)
        lead flashing where a body rises through a roof tier: an upstand tucked into the wall face, turned out over
        the covering as an apron following the true roof surface round the body, ending with closed caps at the
        eave if the body leaves the roof; kit 1.7.3: the apron edge is turned down into the courses (drip=0.03).
        Every junction is proven by components.seal_probe.through_seal_probe (run by tier_finish.tier_hidden_cull).
                                                          -> <P>_<roof>_<body>_flashing
"""
import math

import numpy as np

from ..core import cull_object, log
from ..geom import Acc, finalize
from .finial import lead_hat, turned_finial
from .oct_frame import OctRoof
from .oct_roof import build_cap
from .tier_frame import roof_clearance, roof_support, roof_z


def _register(g, name, rec):
    """kit 1.7.2: register tier `name` and run the roof-to-roof junction rule (tier_frame.roof_clearance) against
    every tier already on another body; g.roof_clear = None switches the gate off."""
    g.roofs[name] = rec
    if getattr(g, "roof_clear", None) is not None:
        roof_clearance(g, name)


def drop_empty_meshes(objs):
    """kit 1.7.2 (note 1, Nanite hygiene): remove every mesh object in `objs` that has no polygons (e.g. a culled
    purlin ring); returns the names removed."""
    import bpy
    gone = []
    for ob in list(objs):
        try:
            if ob.type == "MESH" and len(ob.data.polygons) == 0:
                gone.append(ob.name)
                bpy.data.objects.remove(ob)
        except ReferenceError:
            continue
    if gone:
        log(f"  dropped empty mesh objects {gone}")
    return gone

# bell-cast profiles: pitch (deg) at distances in from the eave lip (the last distance is stretched to the apex /
# p_min); kick / wave / sag as oct_frame.OctRoof
PROFILES = dict(
    skirt=dict(d_pts=[0, 0.4, 0.8, 1.2, 9.0], a_pts=[25, 31, 37, 39, 40], kick=0.022, kick_len=0.8, wave=0.02,
               sag=0.03),
    skirt_steep=dict(d_pts=[0, 0.3, 0.6, 1.0, 9.0], a_pts=[26, 33, 40, 44, 45], kick=0.025, kick_len=0.6,
                     wave=0.015, sag=0.02),
    cap=dict(d_pts=[0, 0.3, 0.6, 9.0], a_pts=[22, 32, 48, 50], kick=0.035, kick_len=0.5, wave=0.008, sag=0.012),
    spire=dict(d_pts=[0, 0.22, 0.5, 0.9, 9.0], a_pts=[24, 38, 55, 62, 64], kick=0.03, kick_len=0.45, wave=0.006,
               sag=0.01),
)


def make_roof(center, p_wall, z_seat, overhang, profile, rot_deg=0.0, p_min=0.02, seed=1):
    """an OctRoof whose surface is at z_seat over the wall line p_wall, eave lip `overhang` beyond it."""
    pr = dict(PROFILES[profile]) if isinstance(profile, str) else dict(profile)
    p_lip = p_wall + overhang
    D = p_lip - p_min
    d_pts = [d for d in pr["d_pts"][:-1] if d < D - 0.05] + [D]
    a_pts = list(pr["a_pts"][:len(d_pts) - 1]) + [pr["a_pts"][-1]]
    tmp = OctRoof(center[0], center[1], p_lip, 0.0, d_pts, a_pts, p_min)
    z_lip = z_seat - float(tmp.zb(p_wall))
    return OctRoof(center[0], center[1], p_lip, z_lip, d_pts, a_pts, p_min, kick=pr["kick"], kick_len=pr["kick_len"],
                   wave=pr["wave"], sag=pr["sag"], seed=seed, rot_deg=rot_deg)


def bell_tier(g, name, on, overhang=1.0, profile="skirt", rise=0.30, through=(), p_top=None, rot_deg=None,
              n_raft=6, seed=303, saddles=False, cap_exposure=None, saddle_taper=None, band=True, bracket_drop=0.55,
              sides=None, collar_r=None, pitch_deg=None, round_rafters=None, deck_lap=True, engine=None,
              pyramid=None):
    """KIT COMPONENT: a bell-cast roof tier on body `on` (see the module doc).
    sides (kit 1.7.1): None = 0 (ROUND witch-hat cone, round_tier) when `on` is a round body, the body's own side
    count (8 for the octagonal bodies so far) when it is a polygon body; pass sides=8 to force an octagonal tier on a
    round body.  collar_r / pitch_deg / round_rafters: round tiers only (lead-hat collar radius, cone pitch, pole
    rafter count).
    deck_lap (kit 1.7.3, octagonal tiers): True (or a dict of eave_deck_lap keywords) lays a continuous sarking strip
    across the wall line under the covering, lapping the main deck and the wall-head band, so no shingle joint at
    the eave ever opens on the hollow body or the sky (even where the hidden-geometry cull later removes the ring
    beam's faces); False = the kit 1.7.2 tier.
    kit 1.8.0 -- ONE polygonal bell-cast roof: any sides >= 3 other than 8 (or engine="pyramid" for 8) builds the tier
    with pyramid_roof.PyramidSurface / pyramid_roof (the kit's N-sided bell-cast roof: rafters, closed deck, coursed
    kit shingles, closed hip saddles, lead apex cap and turned finial), registered like any tier (roof_flashing,
    roof_clearance, stone_body(below=), tier_decals read it through the shared polygonal-roof protocol).  The profile
    maps to pitch = its top pitch, bell_deg = top - eave pitch, bell_len = its last fixed distance, kick / sag as
    given; pyramid = dict of extra pyramid_roof keywords.  engine=None / "oct" with sides 8 keeps the octagonal
    OctRoof + oct_roof.build_cap tier, unchanged: the two surfaces integrate different profiles (OctRoof: a
    600-sample pitch table with an eave wave, sag over the full run; PyramidSurface: a 4001-sample cosine bell, sag
    over the lip distance), so moving the octagonal tiers onto PyramidSurface would move every v2 / keep roof vertex."""
    body = g.body(on)
    if sides is None:
        sides = 0 if body.round else (body.sides if engine == "pyramid" or body.sides != 8 else 8)
    if int(sides) >= 3 and (int(sides) != 8 or engine == "pyramid"):
        return _pyramid_tier(g, name, on, int(sides), overhang=overhang, profile=profile, rise=rise, through=through,
                             rot_deg=rot_deg, seed=seed, pitch_deg=pitch_deg, extra=pyramid)
    if int(sides) < 3:
        return round_tier(g, name, on, overhang=overhang, profile=profile, through=through, p_top=p_top,
                          n_raft=round_rafters, seed=seed, collar_r=collar_r, pitch_deg=pitch_deg)
    seed = int(seed) + g.seed_offset
    rng = np.random.default_rng(seed)
    z1 = body.z1
    r_top = float(body.r_nom(z1))
    if body.round:
        # an octagonal ring beam on a round body: corners bear on the face, facet middles sit on the wall head
        p_wall = r_top * math.cos(math.pi / 8) + 0.04
        rot = 0.0 if rot_deg is None else rot_deg
    else:
        p_wall = r_top - 0.03
        rot = math.degrees(body.rot) if rot_deg is None else rot_deg
    z_plate = z1 + 0.12
    if p_top is None:
        if through:
            p_top = min(float(g.body(n).r_nom(z1)) for n in through if np.allclose(g.body(n).c, body.c)) - 0.12 \
                if any(np.allclose(g.body(n).c, body.c) for n in through) else 0.28
        else:
            p_top = 0.28
    p_min = max(0.02, 0.6 * p_top) if through else 0.02
    roof = make_roof(body.c, p_wall, z_plate + rise, overhang, profile, rot, p_min=p_min, seed=seed % 97)
    coll = g.sub(name)
    prefix = g.name(name)
    Vsh = build_cap(coll, roof, prefix, rng, p_wall, z_plate, n_raft, p_top, expo=0.14, W=0.32, t=0.022,
                    lens=(0.12, 0.17), bracket_z0=z_plate - bracket_drop, chunky=g.units == "kit", saddles=saddles,
                    cap_exposure=cap_exposure, saddle_taper=saddle_taper)
    if deck_lap:
        eave_deck_lap(g, name, roof, p_wall, coll, **(deck_lap if isinstance(deck_lap, dict) else {}))
    import bpy
    if through:
        fn = lambda V: g.inside_any(V, through, margin=0.015)  # noqa: E731
        n_drop = 0
        for part in ("shingles", "hips", "structure", "deck", "deck_lap"):
            ob = bpy.data.objects.get(f"{prefix}_{part}")
            if ob is not None:
                n0 = len(ob.data.polygons)
                cull_object(ob, fn)
                n_drop += n0 - len(ob.data.polygons)
        keep = ~g.inside_any(Vsh, through, margin=0.015) if len(Vsh) else np.zeros(0, bool)
        Vsh = Vsh[keep]
        log(f"  {name}: dropped {n_drop} faces inside {list(through)}")
    if band:
        wall_head_band(g, name, roof, p_wall, z_plate, coll)
    _register(g, name, dict(roof=roof, on=on, p_wall=p_wall, z_plate=z_plate, p_top=p_top, through=tuple(through),
                            Vsh=Vsh, z_lip=float(roof.zb(roof.p_lip))))
    log(f"  {name}: lip p {roof.p_lip:.2f} z {roof.zb(roof.p_lip):.2f}, wall p {p_wall:.2f} plate {z_plate:.2f}, "
        f"apex {roof.zb(roof.Pp[-1]):.2f}")
    return roof


def _pyramid_tier(g, name, on, sides, overhang=1.0, profile="skirt", rise=0.30, through=(), rot_deg=None, seed=303,
                  pitch_deg=None, extra=None):
    """kit 1.8.0: an N-sided bell-cast tier on body `on` built by pyramid_roof (see bell_tier)."""
    import bpy
    from .pyramid_roof import PARTS, pyramid_roof
    body = g.body(on)
    seed = int(seed) + g.seed_offset
    pr = dict(PROFILES[profile]) if isinstance(profile, str) else dict(profile)
    z1 = body.z1
    r_top = float(body.r_nom(z1))
    if body.round:                         # corners bear on the face, facet middles on the wall head
        p_wall = r_top * math.cos(math.pi / sides) + 0.04
        rot = -90.0 if rot_deg is None else rot_deg
    else:
        p_wall = r_top - 0.03
        rot = math.degrees(body.rot) if rot_deg is None else rot_deg
    z_plate = z1 + 0.12
    top = float(pitch_deg if pitch_deg is not None else pr["a_pts"][-1])
    kw = dict(pitch_deg=top, eave_out=overhang, bell_deg=max(0.0, top - float(pr["a_pts"][0])),
              bell_len=float(pr["d_pts"][-2]) if len(pr["d_pts"]) > 1 else 0.7, kick=pr.get("kick", 0.0),
              kick_len=pr.get("kick_len", 0.6), sag=pr.get("sag", 0.0))
    kw.update(extra or {})
    coll = g.sub(name)
    rec = pyramid_roof(g, p_wall, z_plate + rise, name=name, sides=sides, rot_deg=rot, cx=float(body.c[0]),
                       cy=float(body.c[1]), seed=seed, coll=coll, **kw)
    S = rec["surface"]
    prefix = g.name(name)
    if through:
        fn = lambda V: g.inside_any(V, through, margin=0.015)  # noqa: E731
        n_drop = 0
        for part in PARTS:
            ob = bpy.data.objects.get(f"{prefix}_{part}")
            if ob is not None:
                n0 = len(ob.data.polygons)
                cull_object(ob, fn)
                n_drop += n0 - len(ob.data.polygons)
        log(f"  {name}: dropped {n_drop} faces inside {list(through)}")
    _register(g, name, dict(roof=S, on=on, p_wall=p_wall, z_plate=z_plate, p_top=None, through=tuple(through),
                            Vsh=np.zeros((0, 3)), z_lip=float(S.zb(S.p_lip)), pyramid=True, tip=rec["tip"],
                            finial_top=rec["tip"]))
    log(f"  {name} ({sides}-sided pyramid tier): lip p {S.p_lip:.2f} z {float(S.zb(S.p_lip)):.2f}, wall p "
        f"{p_wall:.2f} plate {z_plate:.2f}, tip {rec['tip']:.2f}")
    return S


# =================================================================================================================
# kit 1.7.1: ROUND tiers (witch-hat cones) on round bodies
# =================================================================================================================
ROUND_PROFILES = dict(skirt=(42.0, 14.0, 0.9), skirt_steep=(47.0, 15.0, 0.8), cap=(52.0, 16.0, 0.6),
                      spire=(60.0, 16.0, 0.7),
                      witch_hat=(70.0, 20.0, 0.45))     # kit 1.7.2: ref2's tall witch hat, eave-to-apex H/D ~1.2-1.4
"""(cone pitch above the bell, bell-cast flattening (deg), bell length (slope m)) of a round tier per profile name."""


class ConeRoof:
    """registry view of a round tier (the hut cone of components.cone on a sub-frame, centred on its body): the same
    interface tier_frame.roof_z / roof_support, roof_flashing, board_belt and tier_decals read from an OctRoof
    (c, rot, p_lip, Pp, zb(p) = base surface height at plan radius p)."""
    is_round = True

    def __init__(self, f, center):
        self.f = f
        self.c = np.asarray(center, float)
        self.rot = 0.0
        self.p_lip = float(f.R_EAVE)
        self.Pp = np.array([self.p_lip, float(f.PR[-1])])

    def zb(self, p):
        f = self.f
        p = np.asarray(p, float)
        z = np.interp(-p, -f.PR, f.PZ)
        return np.where(p > f.PR[0], f.PZ[0] - (p - f.PR[0]) * math.tan(float(f.PA[0])), z)


def _wall_head(g, body):
    """(outer face radius, top) of the wall head a round tier's plate bears on: a board belt's head ring (16-piece
    ring 0.11 m square outside the boards, components.board_belt) or a stone body's top course."""
    if body.kind == "belt":
        return float(body.apothem) + 0.04 + 0.11, float(body.z1), 0.08
    return float(body.r_nom(body.z1)), float(body.z1), 0.0


def _shift_new(g, objs, c):
    """move objects a sub-frame built about the origin onto the body centre c (mesh data translated; pooled
    linked duplicates moved by their matrix)."""
    from mathutils import Matrix, Vector
    if abs(c[0]) < 1e-9 and abs(c[1]) < 1e-9:
        return
    inst = set(g.inst_coll.objects.keys()) if g.inst_coll is not None else set()
    T = Matrix.Translation(Vector((float(c[0]), float(c[1]), 0.0)))
    for ob in objs:
        if ob.type != "MESH":
            continue
        if ob.name in inst or ob.data.users > 1:
            ob.matrix_world = T @ ob.matrix_world
        else:
            ob.data.transform(T)
            ob.data.update()


def round_tier(g, name, on, overhang=0.6, profile="spire", through=(), p_top=None, n_raft=None, seed=707,
               collar_r=None, pitch_deg=None, bell_deg=None, bell_len=None, clear=0.05, cone_age="kit"):
    """KIT COMPONENT (kit 1.7.1): a ROUND bell-cast witch-hat tier on the round body `on` -- the hut's conical roof
    (components.cone / conical_roof: pole rafters, battens, chunky shingle courses with under-laps, sarking deck),
    the round wall plate (components.round_wall.wall_plate, pegged) bearing on the body's wall head at the body
    radius, and the eave closure (frieze) from the plate into the shingle stack, built on a RoundFrame sub-frame as
    components.tower_roof does and moved onto the body centre.  Same interface as the octagonal bell_tier:
    `through` bodies cut the covering (p_top = where it stops), the tier is registered for roof_flashing /
    board_belt(below=) / stone_body(below=) / tier_finial / tier_decals.  No brackets: the rafters bear on the
    plate.  Objects <P>_<name>_rafters / _battens / _purlin_rings / _roof_shingles / _roof_starter /
    _roof_underlap / _roof_deck / _eave_closure / _wall_plate (+ pooled pegs)."""
    import bpy
    from types import SimpleNamespace
    from .cone import AGE_R10, age_defaults, rafter_underside_z_at_r
    from .conical_roof import build_purlins_battens, build_rafters, build_shingles
    from .round_wall import wall_plate
    from .tower_roof import roof_frame
    from .round_roof_parts import eave_closure, roof_deck
    body = g.body(on)
    seed = int(seed) + g.seed_offset
    pr = ROUND_PROFILES[profile] if isinstance(profile, str) else tuple(profile)
    pitch = float(pitch_deg if pitch_deg is not None else pr[0])
    bd = float(bell_deg if bell_deg is not None else pr[1])
    bl = float(bell_len if bell_len is not None else pr[2])
    r_face, z_top, plate_in = _wall_head(g, body)
    conc = [n for n in through if np.allclose(g.body(n).c, body.c)]
    if p_top is None:
        p_top = (min(float(g.body(n).r_nom(z_top)) for n in conc) - 0.12) if conc else None
    if p_top is not None:
        s_end_r, collar = p_top, p_top + 0.20
    else:
        s_end_r = 0.40
        collar = float(collar_r if collar_r is not None else np.clip(0.24 * (r_face + overhang), 0.45, 0.66))
    coll = g.sub(name)
    proxy = SimpleNamespace(prefix=g.name(name), rule=g.detail, hygiene=g.hygiene, coll=coll, inst_coll=g.inst_coll,
                            pools=g.pools, decals=g.decals)
    age = age_defaults(**AGE_R10) if cone_age == "kit" else cone_age
    for _ in range(14):
        r_wall = r_face - plate_in - 0.10
        f = roof_frame(proxy, r_wall, z_top - 0.012, overhang + r_face - r_wall, pitch_deg=pitch, bell_deg=bd,
                       bell_len=bl, collar_r=collar, collar_pitch_deg=max(44.0, pitch - 10.0), finial_tip=None,
                       n_raft=n_raft, cone_age=age, s_end_r=s_end_r)
        gap = float(rafter_underside_z_at_r(f, r_face)) - z_top
        if gap >= clear or plate_in <= -0.04:
            break
        plate_in -= 0.02
    f.coll = coll
    before = set(bpy.data.objects.keys())
    s = seed % 1000
    build_rafters(f, coll, seed=404 + s)
    build_purlins_battens(f, coll, seed=505 + s)
    build_shingles(f, coll, seed=606 + s)
    roof_deck(f, r_in=f.R_WALL - 0.075)
    eave_closure(f, r_b=f.R_WALL - 0.075, mat="M_timber_weathered" if body.kind == "belt" else "M_mortar")
    wall_plate(f, seed=303 + s)
    new = [o for o in bpy.data.objects if o.name not in before]
    _shift_new(g, new, body.c)
    if through:
        fn = lambda V: g.inside_any(V, through, margin=0.015)  # noqa: E731
        n_drop = 0
        for ob in new:
            if ob.type == "MESH" and ob.data.users == 1 and ob.name not in g.inst_coll.objects:
                n0 = len(ob.data.polygons)
                cull_object(ob, fn)
                n_drop += n0 - len(ob.data.polygons)
        log(f"  {name}: dropped {n_drop} faces inside {list(through)}")
    drop_empty_meshes(new)                                     # kit 1.7.2: no zero-face objects (note 1)
    roof = ConeRoof(f, body.c)
    _register(g, name, dict(roof=roof, on=on, p_wall=r_face, z_plate=float(f.PLATE_TOP), p_top=p_top,
                            through=tuple(through), Vsh=np.zeros((0, 3)), z_lip=float(f.Z_EAVE), frame=f, round=True))
    log(f"  {name} (round): wall head r {r_face:.2f} z {z_top:.2f}, plate {f.PLATE_BOT:.2f}..{f.PLATE_TOP:.2f} on r "
        f"{f.R_WALL:.2f} (rafters clear the head by {gap:.3f}), eave r {f.R_EAVE:.2f} z {f.Z_EAVE:.2f}, pitch "
        f"{pitch:.0f}, {f.N_RAFT} rafters, {f.N_COURSES} courses")
    return roof


def eave_deck_lap(g, name, roof, p_wall, coll, out=None, inn=0.22, h_top=-0.009, t=0.018, nx=24, dm=0.06,
                  lip_gap=0.08):
    """KIT COMPONENT (kit 1.7.3, producer note 6 at the eave): a continuous sarking strip (oct_roof.sarking_deck,
    M_timber) on all 8 facets from `out` outside the wall line p_wall (default: the whole overhang, to `lip_gap`
    inside the eave lip) to `inn` inside it, h_top under the covering (just below the main deck, so where the two
    overlap the main deck stays on top).  It laps over the main deck's eave edge (build_cap starts that deck ~0.08 m
    inside p_wall) and over the wall-head band (p_wall - 0.07 .. p_wall - 0.02), closing the crack between them that
    otherwise only the ring beam's top faces back, and it boards the overhang over the rafters, so no ray through a
    shingle joint reaches the wall face under the eave where a `through` body has cut the eave structure.  Fine
    cells (nx across a facet, dm along the slope) so a `through` body cuts it close to its face.  Its name contains
    'deck', so the hidden-geometry cull never targets it.                              -> <P>_<name>_deck_lap"""
    from .oct_roof import sarking_deck
    acc = Acc(g.name(name) + "_deck_lap")
    if out is None:
        out = max(0.10, float(roof.p_lip) - p_wall - lip_gap)
    m0 = float(roof.m_of_p(p_wall + out))
    m1 = float(roof.m_of_p(max(p_wall - inn, 0.05)))
    sarking_deck(roof, acc, min(m0, m1), max(m0, m1), h_top=h_top, t=t, nx=nx, dm=dm, p_floor=0.03)
    return finalize(acc, coll)


def wall_head_band(g, name, roof, p_wall, z_plate, coll, t=0.05, drop=0.16, gap=0.035):
    """closed octagonal frieze band (M_timber_weathered) under a tier's soffit: from the wall head (z_plate - drop)
    to `gap` under the roof surface at the band line, so the joint between wall top and eave is closed."""
    a_o = p_wall - 0.02
    a_i = a_o - t
    z_bot = z_plate - drop
    acc = Acc(g.name(name) + "_band")
    ns = 8
    ks = np.repeat(np.arange(8), ns)
    u = np.tile(np.linspace(-1.0, 1.0, ns + 1)[:-1], 8)
    h = math.tan(math.pi / 8)
    # top edge follows the real (kicked / waved / sagging) surface: soffit underside = surface - sheathing
    S_o = roof.surf(ks, u * a_o * h, np.full(len(ks), a_o))
    S_i = roof.surf(ks, u * a_i * h, np.full(len(ks), a_i))
    pitch = math.atan(max(float(roof.zb(a_o - 0.05) - roof.zb(a_o + 0.05)) / 0.10, 1e-3))
    z_top = np.minimum(S_o[:, 2], S_i[:, 2]) - 0.022 / math.cos(pitch) - gap * 0.35
    N8 = len(ks)
    V = np.concatenate([np.column_stack([S_o[:, :2], np.full(N8, z_bot)]), np.column_stack([S_o[:, :2], z_top]),
                        np.column_stack([S_i[:, :2], np.full(N8, z_bot)]), np.column_stack([S_i[:, :2], z_top])])
    i = np.arange(N8)
    j = (i + 1) % N8
    o1, o2, o3 = N8, 2 * N8, 3 * N8
    F = [np.stack([i, j, j + o1, i + o1], 1), np.stack([o2 + j, o2 + i, o3 + i, o3 + j], 1),
         np.stack([o1 + i, o1 + j, o3 + j, o3 + i], 1), np.stack([j, i, o2 + i, o2 + j], 1)]
    acc.add(V, F, "M_timber_weathered")
    finalize(acc, coll, smooth_deg=30.0)


def tier_finial(g, name, scale=1.0, hat_r=0.42, hat_h=0.55, lean_deg=1.2, lean_dir=(0.5, -0.8)):
    """KIT COMPONENT: lead hat over tier `name`'s apex (fitted over its shingles) + the turned finial."""
    t = g.roofs[name]
    roof = t["roof"]
    if t.get("round"):
        return _round_finial(g, name, t, scale)
    if t.get("pyramid"):                  # kit 1.8.0: pyramid_roof already built its lead cap and turned finial
        log(f"  {name} finial: built by pyramid_roof, tip {t['finial_top']:.2f} m")
        return None
    acc = Acc(g.name(name) + "_finial")
    apex = float(roof.zb(0.02))
    z_top = lead_hat(acc, roof.c[0], roof.c[1], apex, hat_r, hat_h, cover=t["Vsh"])
    turned_finial(acc, (roof.c[0], roof.c[1], z_top - 0.01), scale, lean_deg, lean_dir)
    finalize(acc, g.sub(name))
    t["finial_top"] = z_top + 1.45 * scale
    log(f"  {name} finial tip ~{t['finial_top']:.2f} m")


def _round_finial(g, name, t, scale):
    """round tier: the hut's lead-hat collar (fitted over the top shingle courses) + turned spindle and spike
    (components.finial 'spike'), spike length 0.95 m x scale, moved onto the tier centre."""
    import bpy
    from .finial import collar_drip_z, finial
    f = t["frame"]
    tp = math.tan(f.COLLAR_PITCH)
    zd = collar_drip_z(f) + 0.065
    z_top = zd + (f.COLLAR_R - 0.25) * tp
    z_k = z_top - 0.03 + 0.045 + 0.30 - 0.015 + 0.383
    f.FINIAL_TIP = z_k + 0.95 * scale
    before = set(bpy.data.objects.keys())
    zz = finial(f)
    new = [o for o in bpy.data.objects if o.name not in before]
    _shift_new(g, new, t["roof"].c)
    drop_empty_meshes(new)                                     # kit 1.7.2: no zero-face objects (note 1)
    t["finial_top"] = float(zz[-1])
    log(f"  {name} finial tip ~{t['finial_top']:.2f} m")


def roof_flashing(g, roof_name, body_name,up=0.24, apron=0.26, t=0.012, cover_h=0.15, edge_h=0.075, step=0.05,
                  drip=0.03):
    """KIT COMPONENT: the lead flashing where body `body_name` rises through tier `roof_name` (see the module doc).
    up: upstand height above the junction; apron: width over the covering; cover_h / edge_h: apron height over the
    roof's base surface at the upstand / at the drip edge (clears the chunky shingle butts).
    drip (kit 1.7.3): the apron's outer edge is turned down (dressed) into the shingle stack to `drip` m under the
    roof's base surface, so no grazing ray can run under the apron between it and the covering and out to the sky
    (seal_probe); None = the kit 1.7.2 open drip edge."""
    roof = g.roofs[roof_name]["roof"]
    body = g.body(body_name)
    R = float(body.r_nom(0.5 * (body.z0 + body.z1)))
    n = max(64, int(2 * math.pi * R / step))
    ths = np.linspace(0, 2 * math.pi, n, endpoint=False)
    zj = np.full(n, 0.5 * (body.z0 + body.z1))
    for _ in range(3):
        P = body.point(ths, zj)
        zj = roof_z(roof, P[:, 0], P[:, 1])
        zj = np.where(np.isfinite(zj), zj, body.z0)
    P = body.point(ths, zj)
    pf = roof_support(roof, P[:, 0], P[:, 1])
    room = roof.p_lip - pf - 0.03                     # apron width available before the eave lip
    ok = (room > 0.06) & (pf > roof.Pp[-1] + 0.05) & (zj > body.z0 + 0.05) & (zj < body.z1 - up)
    ap = np.minimum(apron, np.maximum(room, 0.0))
    # local roof height along each radial line
    ds = np.array([0.0, 0.055, 0.09, 0.6, 0.97, 1.0])

    def loc(d, th, z):
        Q = body.point(np.asarray(th), np.asarray(z), d=np.asarray(d))
        return Q, roof_z(roof, Q[..., 0], Q[..., 1])

    prof_pts = []
    for i in range(n):
        th, z0 = ths[i], zj[i]
        a = ap[i]
        dd = np.array([0.055, 0.09, 0.6 * a, a, a + 0.012])
        Q, Lr = loc(dd, np.full(5, th), np.full(5, z0))
        Lr = np.where(np.isfinite(Lr), Lr, z0 - 0.3)
        z_up = max(z0 + up, float(Lr[0]) + cover_h + 0.10)
        top = [(-0.035, z_up), (0.055, z_up), (0.055, Lr[0] + cover_h + 0.03), (0.09, Lr[1] + cover_h),
               (0.6 * a, Lr[2] + cover_h - 0.01), (a, Lr[3] + edge_h + 0.02), (a + 0.012, Lr[4] + edge_h)]
        bot = [(a, Lr[3] + edge_h + 0.02 - t), (0.6 * a, Lr[2] + cover_h - 0.01 - t), (0.09 - t, Lr[1] + cover_h - t),
               (0.055 - t, Lr[0] + cover_h + 0.03 - t), (0.055 - t, z_up - t), (-0.035, z_up - t)]
        if drip is not None:                          # kit 1.7.3: turned-down drip dressed into the courses
            top = top + [(a + 0.012, Lr[4] - drip)]
            bot = [(a + 0.012 - t, Lr[4] - drip), (a + 0.012 - t, Lr[4] + edge_h - t)] + bot
        pts = top + bot
        prof_pts.append(pts)
    m = len(prof_pts[0])
    D = np.array([[p[0] for p in pts] for pts in prof_pts])        # (n, m) radial offsets
    Z = np.array([[p[1] for p in pts] for pts in prof_pts])        # (n, m) heights
    TH = np.broadcast_to(ths[:, None], D.shape)
    W = body.point(TH, Z, d=D)                                     # (n, m, 3)
    acc = Acc(g.name(f"{roof_name}_{body_name}_flashing"))
    # runs of valid angles (closed ring when every angle is valid)
    if ok.all():
        runs = [(np.arange(n), True)]
    else:
        idx = np.flatnonzero(ok)
        if not len(idx):
            log(f"  flashing {roof_name}/{body_name}: no junction")
            return None
        start = np.flatnonzero(~ok)[0]
        order = (np.arange(n) + start) % n
        runs, cur = [], []
        for k in order:
            if ok[k]:
                cur.append(k)
            elif cur:
                runs.append((np.array(cur), False))
                cur = []
        if cur:
            runs.append((np.array(cur), False))
    for ids, closed in runs:
        if len(ids) < 2:
            continue
        Vr = W[ids]
        k_ = len(ids)
        ii = np.arange(k_ if closed else k_ - 1)[:, None]
        jj = np.arange(m)[None, :]
        i2 = (ii + 1) % k_
        q = np.stack([ii * m + jj, ii * m + (jj + 1) % m, i2 * m + (jj + 1) % m, i2 * m + jj], -1).reshape(-1, 4)
        faces = [q]
        if not closed:
            faces += [np.arange(m)[None, ::-1], ((k_ - 1) * m + np.arange(m))[None]]
        acc.add(Vr.reshape(-1, 3), faces, "M_lead")
    ob = finalize(acc, g.sub(roof_name), smooth_deg=50.0)
    log(f"  flashing {roof_name}/{body_name}: {int(ok.sum())}/{n} stations, {len(runs)} run(s)")
    g.roofs[roof_name].setdefault("flashings", []).append(body_name)
    return ob
