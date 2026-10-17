"""components.tower_roof -- the head of a round stone TOWER: corbelled parapet, conical roof on any round wall
head, interior ceiling, hidden-geometry cull (kit changes v1_stone_watchtower; new module, nothing existing changed).

Public components (every one is `component(g, ..., seed=None)`):

    corbelled_parapet(g, height, proj, coping_h, seed)
        drum family (components.drum_frame.DrumFrame): a coursed rubble parapet ring set OUT on the drum's corbelled
        cornice -- its face `proj` m beyond the drum face, its bottom course bedded 3 cm into the cornice cap top
        (closed junction, no shadow gap), a dressed coping ring whose top bed runs 0.32 m back over the wall, and a
        continuous mortar backing 2.2 cm behind the stone faces (never a see-through joint).  Objects
        <P>_parapet_stones / _parapet_coping / _parapet_mortar.  Publishes g.WALL_HEAD for a roof.

    round_tower_roof(g, pitch_deg, eave_out, bell_deg, bell_len, collar_r, finial_tip, n_raft, cone_age, seed)
        a conical chunky-shingle roof with a BELL-CAST eave on ANY round wall head (g.WALL_HEAD = dict(r_face, z_top),
        published by corbelled_parapet; without it the drum's cornice top).  It re-uses the round-roof kit (the hut's
        components.conical_roof / cone / finial / round_wall) on a sub-frame (components.frame.RoundFrame) that shares
        this building's collection, pools and decal anchors, so the cone, rafters, battens, shingle courses, under-lap
        strips, wall plate, lead-hat collar and spike finial are the SAME modules as the hut's, at any radius / height.
        Junctions: the pegged wall plate is bedded 1.2 cm into the coping; a mortar eave closure between the rafter
        feet runs from the plate top into the shingle stack; a continuous outward-facing sarking deck inside the wall
        line backs every shingle (culled shingle backs and side joints show the deck, never sky).
        Objects <P>_rafters / _purlin_rings / _battens / _roof_shingles / _roof_starter / _roof_underlap /
        _roof_deck / _eave_closure / _wall_plate / _cap_collar / _finial, pooled _peg_###.  Publishes g.ROOF.

    drum_ceiling(g, z)
        a boarded ceiling disc closing the hollow drum above the ground-floor interior seen through the door (a look
        up through the doorway meets a front face, never the inside of the tower head).  Object <P>_ceiling.

    tower_hidden_cull(g, targets)
        producer note 6: core.visibility_cull with the drum views plus eave-level and crane rings round the roof; only
        pieces with a continuous backing are culled.

Frames: azimuth from -Y toward +X, z up, metres; the entrance faces -Y.
"""
import math
import zlib

import numpy as np

from ..core import log, smoothstep
from ..tmplmesh import PI, add_grid
from .drum_frame import R_out, cyl_place, relief_far


# =================================================================================================================
# corbelled parapet (drum family)
# =================================================================================================================
COPING_PROFILE = [(-0.34, 0.0), (0.022, 0.0), (0.040, 0.012), (0.046, 0.030), (0.046, 0.088), (0.034, 0.104),
                  (0.010, 0.118), (-0.34, 0.12)]
"""(y outward from the parapet face, z up) of the dressed coping: 4.6 cm drip, weathered top, top bed 0.34 m deep."""


def drum_top(g):
    """height of the drum's cornice top (round_stone_drum: Z_CORN0 = height - 0.45)."""
    return float(g.Z_CORN0 + 0.45)


def corbelled_parapet(g, height=0.85, proj=0.24, coping_h=0.12, seed=None, rubble=None):
    """KIT COMPONENT (drum family): coursed rubble parapet ring set out on the corbelled cornice (see module doc).
    height: rubble height above the cornice top (m); proj: parapet face beyond the drum face at the cornice top (m,
    <= the cornice cap's 0.30 m projection less a 4-6 cm ledge); coping_h: coping course height; rubble: coursing()
    keywords (default: the frame's `plain` rubble table)."""
    from ..split_stones import STYLE
    from .drum_wall import (apply_tilt, coursing, depth_tilt_params, follow_beds, profile_course, stones_by_tmpl,
                            wall_depth, wall_stone_tmpl)
    H = drum_top(g)
    Rp = float(R_out(g, H)) + proj
    z0 = H - 0.045                       # bottom course bedded ~3 cm into the cornice cap top (closed junction)
    z1 = H + height

    def Rfun(z):
        return Rp + 0.0 * np.asarray(z, float)

    with g.seeded(seed):
        rng = g.RNG("parapet")
        P_st = g.part("parapet_stones", ["M_stone"])
        P_dr = g.part("parapet_coping", ["M_stone_dressed"], wear=0.4, angle=22.0)
        P_mo = g.part("parapet_mortar", ["M_mortar"])
        C = 2 * PI * Rp
        u0 = rng.uniform(0, C)
        S = coursing(rng, z0, z1, lambda zb, zt: [(u0, u0 + C)], **(rubble or g.rubble["plain"]))
        N = len(S["uc"])
        ang, dy = depth_tilt_params(rng, N)
        D = wall_depth(dy, -0.022, S["L"], ang)
        th = S["uc"] / Rp
        tm = wall_stone_tmpl(S["zc"], S["H"], STYLE["rubble"]["T"])
        for ix, P, Tq in stones_by_tmpl(rng, S["L"], S["H"], D, "rubble", tm, min_relief=relief_far(g)):
            P = follow_beds(P, S, ix)
            P = apply_tilt(P, ang[ix])
            W = cyl_place(g, P, th[ix], S["zc"][ix], dy[ix], Rfun)
            P_st.add(W, Tq, Pl=P, mat="M_stone", smooth="all")
        # dressed coping ring (top bed runs back over the wall: the roof's wall plate is bedded on it)
        prof = [(y_, z_ * coping_h / 0.12) for y_, z_ in COPING_PROFILE]
        profile_course(g, P_dr, "M_stone_dressed", rng, z1, prof, seg=(0.55, 0.85), Rfun=Rfun, joint=0.009,
                       top_back=0.34)
        # continuous mortar backing 2.2 cm behind the stone faces: from inside the cornice cap to under the coping
        nth = 200
        ths = np.linspace(0, 2 * PI, nth, endpoint=False)
        zs = np.linspace(z0 - 0.01, z1 + 0.03, max(4, int(math.ceil((z1 + 0.04 - z0) / 0.15)) + 1))
        TH, Z = np.meshgrid(ths, zs, indexing="ij")
        Rm = Rp - 0.022
        G = np.stack([Rm * np.sin(TH), -Rm * np.cos(TH), Z], -1)
        add_grid(P_mo, "M_mortar", G, wrap=True, flip=False)
        z_top = z1 + coping_h
        g.WALL_HEAD = dict(r_face=Rp, z_top=z_top, r_bed_in=Rp - 0.32, coping_out=Rp + 0.046)
        log("corbelled parapet: face r %.3f (drum %.3f + %.2f), z %.3f..%.3f, %d stones, coping top %.3f"
            % (Rp, Rp - proj, proj, z0, z1, N, z_top))
        return N


# =================================================================================================================
# interior ceiling (drum family)
# =================================================================================================================
def drum_ceiling(g, z=3.45, inset=0.775, seed=None):
    """KIT COMPONENT (drum family): boarded ceiling disc at height z closing the hollow drum above the interior
    seen through the door (faces down; its rim runs 0.5 cm into the wall core's inner face)."""
    P = g.part("ceiling", ["M_timber"])
    Rc = float(R_out(g, z)) - inset
    ths = np.linspace(0, 2 * PI, 72, endpoint=False)
    rs = np.linspace(0.06, Rc, 6)
    TH, RR = np.meshgrid(ths, rs, indexing="ij")
    G = np.stack([RR * np.sin(TH), -RR * np.cos(TH), np.full_like(TH, z)], -1)
    add_grid(P, "M_timber", G, wrap=True, flip=False)            # (theta, r) grid, flip False: faces down
    log("drum ceiling at z %.2f, r %.2f" % (z, Rc))


# =================================================================================================================
# conical roof with a bell-cast eave on any round wall head
# =================================================================================================================
def _bell_profile(f, bell_deg, bell_len, convex=0.07):
    """the cone reference profile of frame f (components.cone.build_profile) with a stronger bell-cast eave: the
    pitch flattens by bell_deg over the last bell_len slope metres (the hut's is 4 deg over 0.55 m)."""
    ds = 0.004
    s_max = 6.4 if (f.R_EAVE - 0.18) / math.cos(f.PITCH) < 6.3 else (f.R_EAVE - 0.18) / math.cos(f.PITCH) + 0.3
    s = np.arange(0, s_max, ds)
    alpha = f.PITCH - math.radians(bell_deg) * (1 - smoothstep(0.0, bell_len, s))
    r = f.R_EAVE - np.concatenate([[0], np.cumsum(np.cos(alpha[:-1]) * ds)])
    z = f.Z_EAVE + np.concatenate([[0], np.cumsum(np.sin(alpha[:-1]) * ds)])
    s_top = float(np.interp(0.0, -r, s))
    b = convex * np.sin(np.pi * np.clip(s / (s_top * 0.92), 0, 1)) ** 1.2
    r = r + b * np.sin(alpha)
    z = z + b * np.cos(alpha)
    keep = r > 0.18
    return s[keep], r[keep], z[keep], alpha[keep]


def roof_frame(g, r_wall, z_plate_bot, overhang, pitch_deg=52.0, bell_deg=12.0, bell_len=0.85, collar_r=0.62,
               collar_pitch_deg=50.0, finial_tip=None, n_raft=None, cone_age=None, s_end_r=0.40):
    """a components.frame.RoundFrame sized for a roof whose wall plate sits on a wall head at z_plate_bot, plate
    centre line r_wall, eave r_wall + overhang, bell-cast profile; it shares g's collection, pools and decals."""
    from .cone import rafter_underside_z_at_r, s_at_r
    from .frame import RoundFrame

    def make(eave_z):
        f = RoundFrame(g.prefix, radius=r_wall, eave_z=eave_z, overhang=overhang, pitch_deg=pitch_deg, n_raft=n_raft,
                       finial_tip=finial_tip, collar_r=collar_r, collar_pitch_deg=collar_pitch_deg,
                       cone_age=cone_age, detail_rule=bool(getattr(g.rule, "active", True)), hygiene=g.hygiene)
        f.PS, f.PR, f.PZ, f.PA = _bell_profile(f, bell_deg, bell_len)
        for k in ("_sag_amp", "_sag_mod", "_sag_s1"):          # the age pass caches the old profile
            f.__dict__.pop(k, None)
        f.S_END = s_at_r(f, s_end_r)
        # the top course's exposed part + overlap (exposure + 6.5 cm) must run >= 15 cm in under the lead hat
        s_need = s_at_r(f, max(collar_r - 0.15, s_end_r + 0.02))
        f.N_COURSES = int(math.ceil((s_need - f.SH_EXPOSE - 0.065) / f.SH_EXPOSE)) + 1
        f.PLATE_TOP = float(rafter_underside_z_at_r(f, f.R_WALL + 0.09)) + 0.03
        f.PLATE_BOT = f.PLATE_TOP - f.PLATE_H
        f.WATTLE_TOP = f.PLATE_BOT
        f.FULL_WIN_DEG = 0.0                 # no doorway looks up into this roof: no full-length shingle window
        return f

    f0 = make(0.0)
    f = make(z_plate_bot - f0.PLATE_BOT)     # every height is linear in eave_z
    f.coll, f.inst_coll, f.pools, f.decals = g.coll, g.inst_coll, g.pools, g.decals
    return f


def _roof_deck(f, r_in, gap=0.006, eave_s=0.10, t=0.012):
    """continuous sarking deck on the rafters, under the battens and the shingle stack (producer note 6): every culled
    shingle back, side joint or slipped piece shows this surface, never sky.  Inside the wall line (r <= r_in) one
    sheet facing OUT; over the eave overhang (from eave_s slope metres above the lip) a closed board slab `t` thick
    (top face up, soffit face down, edge at the eave), so no sunlight leaks through the overhang's shingle joints onto
    the wall head and the boarded soffit reads from below between the rafter feet."""
    from .cone import az2th, s_at_r, surf_frame
    from ..core import grid_quads
    acc = f.acc("roof_deck", 30, cull=None)
    az = np.linspace(0, 2 * np.pi, 145)
    th = az2th(az)
    s_in = s_at_r(f, r_in)

    def sheet(s0, s1, ns, depth, up=True):
        ss = np.linspace(s0, s1, ns)
        TH, SS = np.meshgrid(th, ss, indexing="ij")
        P, ts, tt, n = surf_frame(f, TH.ravel(), SS.ravel())
        P = P - n * depth
        F = grid_quads(len(th), len(ss))
        q = P[F[0]]
        if (float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0) == up:
            F = F[:, ::-1]
        acc.add(P, F, "M_timber_weathered")
        return P.reshape(len(th), len(ss), 3)

    d0 = f.BATTEN_T + gap
    sheet(eave_s, f.S_END - 0.04, 22, d0, up=True)                     # the deck (top face), lip to apex
    sheet(eave_s, s_in + 0.03, 5, d0 + t, up=False)                    # the soffit face over the overhang
    P0, ts, tt, n = surf_frame(f, th, np.full_like(th, eave_s))        # the slab edge at the eave, facing out
    E = np.stack([P0 - n * d0, P0 - n * (d0 + t)], 1)                  # (n_th, 2, 3)
    F = grid_quads(len(th), 2)
    q = E.reshape(-1, 3)[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), -ts[0])) < 0:
        F = F[:, ::-1]
    acc.add(E.reshape(-1, 3), F, "M_timber_weathered")
    acc.build(f.coll)


def _eave_closure(f, r_b, mat="M_mortar", n_az=240):
    """the wall head between the rafter feet: a band on the plate from its top (3 cm into it) up into the shingle
    stack (top lowered wherever a slipped / missing shingle would expose it), all the way round, FACING OUT (it is
    seen from outside, in the eave shadow).  The generic form of conical_roof.build_eave_closure."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from ..core import grid_quads, n2
    from .cone import az2th, surf
    acc = f.acc("eave_closure", 30, cull=None)
    az = np.linspace(0.0, 2 * math.pi, n_az, endpoint=False)
    ss = np.linspace(0.0, 2.5, 500)
    bv = []
    for nm in (f"{f.prefix}_roof_shingles", f"{f.prefix}_roof_starter"):
        if nm in bpy.data.objects:
            me = bpy.data.objects[nm].data
            bv.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p_.vertices[:] for p_ in me.polygons]))
    top = np.zeros(n_az)
    cs_p, sn_p = math.cos(f.PITCH), math.sin(f.PITCH)
    for i, a in enumerate(az):
        P = surf(f, np.full_like(ss, float(az2th(a))), ss)
        rr = np.hypot(P[:, 0], P[:, 1])
        z_s = float(np.interp(-r_b, -rr, P[:, 2]))
        nrm_ = Vector((math.sin(a) * sn_p, -math.cos(a) * sn_p, cs_p))
        for dz in (0.05, 0.03, 0.012, -0.006):
            o = Vector((math.sin(a) * r_b, -math.cos(a) * r_b, z_s + dz)) + nrm_ * 0.002
            if any(b_.ray_cast(o, nrm_, 0.4)[0] is not None for b_ in bv):
                break
        top[i] = z_s + dz
    bot = np.full(n_az, f.PLATE_TOP - 0.03)
    rng = np.random.RandomState(2611)
    zz = np.stack([bot, (bot + top) / 2 + 0.008 * rng.uniform(-1, 1, n_az), top], 1)
    rad = r_b + np.stack([np.zeros(n_az), 0.006 * n2(az * 6.0, np.full(n_az, 0.3), 2612), np.zeros(n_az)], 1)
    P = np.stack([np.sin(az)[:, None] * rad, -np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(n_az, 3, closed_u=True)
    q = P[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0])) < 0:
        F = F[:, ::-1]                       # normals face OUT (seen from below the eave)
    acc.add(P, F, mat)
    acc.build(f.coll)


def round_tower_roof(g, pitch_deg=52.0, eave_out=0.62, bell_deg=12.0, bell_len=0.85, collar_r=0.62,
                     collar_pitch_deg=50.0, finial_tip=None, n_raft=None, cone_age="kit", plate_in=0.14, clear=0.07,
                     seed=None):
    """KIT COMPONENT: conical shingle roof with a bell-cast eave on a round wall head (see the module doc).
    pitch_deg: cone pitch above the bell; eave_out: eave lip beyond the wall-head face (m); bell_deg / bell_len: the
    eave flattens by bell_deg over the last bell_len slope metres; collar_r / collar_pitch_deg: the apex lead hat;
    finial_tip: spike tip height (None: spindle + 0.95 m); n_raft: pole rafters (None: derived from the radius);
    cone_age: components.cone age dict, "kit" = the hut's signed-off AGE_R10 pass, None / {} = off; plate_in: wall
    plate outer face this far inside the wall-head face (moved out in 2 cm steps until the rafter undersides clear
    the wall head's outer arris -- WALL_HEAD["coping_out"] -- by `clear` m, so no rafter cuts the coping)."""
    from .cone import AGE_R10, age_defaults
    from .conical_roof import build_purlins_battens, build_rafters, build_shingles
    from .finial import finial
    from .round_wall import wall_plate
    wh = getattr(g, "WALL_HEAD", None) or dict(r_face=float(R_out(g, drum_top(g))) + 0.20, z_top=drum_top(g))
    if cone_age == "kit":
        cone_age = age_defaults(**AGE_R10)
    from .cone import rafter_underside_z_at_r
    r_face, z_top = float(wh["r_face"]), float(wh["z_top"])
    r_out = float(wh.get("coping_out", r_face))
    # the rafters must pass OVER the wall head's outer arris (>= `clear` m): the plate moves out toward the face
    # until they do (a steeper roof needs the plate nearer the face)
    for _ in range(12):
        r_wall = r_face - plate_in - 0.10        # plate (0.18 wide, centre r_wall + 0.01): outer face plate_in in
        f = roof_frame(g, r_wall, z_top - 0.012, eave_out + r_face - r_wall, pitch_deg=pitch_deg, bell_deg=bell_deg,
                       bell_len=bell_len, collar_r=collar_r, collar_pitch_deg=collar_pitch_deg,
                       finial_tip=finial_tip, n_raft=n_raft, cone_age=cone_age)
        gap = float(rafter_underside_z_at_r(f, r_out)) - z_top
        if gap >= clear or plate_in <= -0.02:
            break
        plate_in -= 0.02
    log("tower roof: plate outer face %.2f m inside the wall-head face, rafters clear the arris by %.3f m"
        % (plate_in, gap))
    s = 0 if seed in (None, "") else (zlib.crc32(str(seed).encode("utf8")) % 1000 if not isinstance(seed, int)
                                      else int(seed))
    build_rafters(f, f.coll, seed=404 + s)
    build_purlins_battens(f, f.coll, seed=505 + s)
    build_shingles(f, f.coll, seed=606 + s)
    _roof_deck(f, r_in=f.R_WALL - 0.075)
    _eave_closure(f, r_b=f.R_WALL - 0.075)
    wall_plate(f, seed=303 + s)
    zz = finial(f)
    g.ROOF = dict(frame=f, r_eave=f.R_EAVE, z_eave=f.Z_EAVE, plate_top=f.PLATE_TOP, r_wall=f.R_WALL,
                  pitch=pitch_deg, tip=zz[-1], collar_drip=zz[0])
    log("tower roof: eave r %.3f z %.3f (lip %.2f beyond the wall head), plate %.3f..%.3f on r %.3f, %d rafters, "
        "%d courses, collar drip %.3f, tip %.3f" % (f.R_EAVE, f.Z_EAVE, eave_out, f.PLATE_BOT, f.PLATE_TOP,
                                                   f.R_WALL, f.N_RAFT, f.N_COURSES, zz[0], zz[-1]))
    return f


# =================================================================================================================
# producer note 6 for a tower
# =================================================================================================================
TOWER_CULL_TARGETS = ("base_stones", "base_mortar", "base_dressed", "arcade_dressed", "arcade_backs", "parapet_stones",
                      "parapet_coping", "rafters", "purlin_rings", "battens", "roof_shingles", "roof_starter",
                      "wall_plate")
"""backed pieces only: drum stones / mortar skin / dressed work (the continuous wall core behind), parapet stones and
coping (the parapet mortar backing), roof timbers and shingles (the sarking deck)."""


def tower_views(g):
    """drum views (actor rings, door close-ups, crane rings, review cameras) + rings round the roof at eave level
    and above it (a neighbouring wall walk, a crane shot of the roof) + low rings looking up under the eave."""
    from ..core import ring_views
    from .drum_frame import drum_views
    V = [drum_views(g)]
    rf = getattr(g, "ROOF", None)
    if rf:
        re, ze = rf["r_eave"], rf["z_eave"]
        V.append(ring_views((0, 0), [re + 0.8, re + 3.0, re + 8.0], [ze - 2.0, ze, ze + 1.5], n=16, phase=0.29))
        V.append(ring_views((0, 0), [re + 12.0], [ze + 4.0, ze + 9.0], n=12, phase=0.07))
    return np.concatenate(V)


DRUM_PRECULL = ("base_stones", "base_mortar", "base_dressed")
"""drum masonry the analytic pre-cull and the reduced ray pass apply to (all backed by drum_wall_core)."""


def drum_precull(g, targets=DRUM_PRECULL, slack=0.002, margin=0.25, inward=-0.5, gap=0.006):
    """KIT (v1_stone_watchtower r2, producer note 6, any drum-family building with drum_wall_core): delete, without
    ray casting, the faces of the drum masonry that lie wholly behind the continuous wall core (every vertex inside
    R_out + drum_mortar_d - gap + slack), and inward-facing faces (normal . radial < `inward`) wholly behind the
    mortar skin.  Faces within `margin` of an opening (where the core is holed: door passage, embrasures, reveals)
    and outside the core's height range are never touched.  Returns the number of polygons deleted."""
    import bmesh
    import bpy
    from .drum_frame import drum_mortar_d
    from .drum_wall import _drum_openings
    ops = _drum_openings(g, 0.0)
    z_lo, z_hi = 0.02, float(g.Z_CORN0) + 0.04
    total = 0
    for t in targets:
        ob = bpy.data.objects.get(f"{g.prefix}_{t}")
        if ob is None or ob.type != "MESH" or not len(ob.data.polygons):
            continue
        me = ob.data
        M = np.array(ob.matrix_world)
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        npo = len(me.polygons)
        ls = np.empty(npo, np.int64)
        me.polygons.foreach_get("loop_start", ls)
        lv = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", lv)
        cen = np.empty(npo * 3)
        me.polygons.foreach_get("center", cen)
        cen = cen.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        nrm = np.empty(npo * 3)
        me.polygons.foreach_get("normal", nrm)
        nrm = nrm.reshape(-1, 3) @ M[:3, :3].T
        order = np.argsort(ls)
        rv = np.hypot(co[:, 0], co[:, 1])[lv]
        rmax = np.empty(npo)
        rmax[order] = np.maximum.reduceat(rv, ls[order])
        zc = cen[:, 2]
        rc = np.maximum(np.hypot(cen[:, 0], cen[:, 1]), 1e-6)
        th = np.arctan2(cen[:, 0], -cen[:, 1])
        r_skin = R_out(g, zc) + drum_mortar_d(g, th * g.RREF, zc)
        ndot = (nrm[:, 0] * cen[:, 0] + nrm[:, 1] * cen[:, 1]) / rc
        hid = (rmax < r_skin - gap + slack) | ((ndot < inward) & (rmax < r_skin - 0.003))
        hid &= (zc > z_lo) & (zc < z_hi)
        for (th0, Rr, w, zb, zs_, arched) in ops:
            ztop = zs_ + w if arched else zs_
            dth = (th - th0 + PI) % (2 * PI) - PI
            near = (np.abs(dth) < PI / 2) & (np.abs(rc * np.sin(dth)) < w + margin) & (zc > zb - margin) \
                & (zc < ztop + margin)
            hid &= ~near
        idx = np.flatnonzero(hid)
        if len(idx):
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[int(i)] for i in idx], context="FACES_ONLY")
            loose = [v for v in bm.verts if not v.link_faces]
            if loose:
                bmesh.ops.delete(bm, geom=loose, context="VERTS")
            bm.to_mesh(me)
            bm.free()
            me.update()
        log(f"  analytic pre-cull {ob.name}: -{len(idx)} of {npo} polygons (behind the wall core / inward)")
        total += len(idx)
    return total


def _drum_vis_worker(args):
    """core._vis_worker with a per-polygon candidate view set (packed bit masks): the same probes (centroid + 3
    inner corners, both sides, most frontal views first, own-hit or within 4 mm = visible)."""
    from mathutils import Vector
    from .. import core
    views_np, chunk = args
    V = core._VIS
    bvh, T, Vw, own = V["bvh"], V["T"], V["V"], V["own"]
    views = [Vector(tuple(map(float, v))) for v in views_np]
    nv = len(views)
    hidden = []
    for pid, tri_ids, bits in chunk:
        vids = np.flatnonzero(np.unpackbits(bits)[:nv])
        VN = views_np[vids]
        vis = False
        for ti in tri_ids:
            p0, p1, p2 = (Vector(Vw[i]) for i in T[ti])
            cen = (p0 + p1 + p2) / 3
            nrm_ = (p1 - p0).cross(p2 - p0)
            nrm_ = nrm_.normalized() if nrm_.length > 1e-12 else Vector((0, 0, 1))
            pts = [cen] + [cen + (p - cen) * 0.8 for p in (p0, p1, p2)]
            dv = VN - np.array(cen)
            fac = (dv @ np.array(nrm_)) / np.maximum(np.linalg.norm(dv, axis=1), 1e-9)
            for side in (1, -1):
                ns = nrm_ * side
                order = [views[vids[i]] for i in np.argsort(-fac * side)]
                for pt in pts:
                    probe = pt + ns * 0.002
                    for v in order:
                        if (v - pt).dot(ns) <= 0:
                            continue
                        d = probe - v
                        dist = d.length
                        if dist < 1e-6:
                            continue
                        hit = bvh.ray_cast(v, d / dist, dist + 0.01)
                        if hit[2] is not None and (own[hit[2]] == pid or (hit[0] - pt).length < 0.004):
                            vis = True
                            break
                    if vis:
                        break
                if vis:
                    break
            if vis:
                break
        if not vis:
            hidden.append(pid)
    return hidden


def drum_view_masks(g, cen, views, margin=0.25, shrink=0.03):
    """(n_poly, n_views) bool: the views that are NOT certainly blocked by the drum's continuous wall core for each
    polygon centre.  A view is blocked when the segment view -> centre passes inside the core cylinder (radius
    R_out + drum_mortar_d - 6 mm - `shrink`) between 5 cm above ground and the cornice -- the core is closed there
    except at the openings, so polygons within `margin` of an opening keep every view."""
    from .drum_frame import drum_mortar_d
    from .drum_wall import _drum_openings
    n = len(cen)
    out = np.ones((n, len(views)), bool)
    z_lo, z_hi = 0.05, float(g.Z_CORN0)
    rc = np.hypot(cen[:, 0], cen[:, 1])
    th = np.arctan2(cen[:, 0], -cen[:, 1])
    free = np.zeros(n, bool)
    for (th0, Rr, w, zb, zs_, arched) in _drum_openings(g, 0.0):
        ztop = zs_ + w if arched else zs_
        dth = (th - th0 + PI) % (2 * PI) - PI
        free |= (np.abs(dth) < PI / 2) & (np.abs(rc * np.sin(dth)) < w + margin) & (cen[:, 2] > zb - margin) \
            & (cen[:, 2] < ztop + margin)
    zz = np.linspace(0.0, z_hi, 400)
    r_min = float(np.min(R_out(g, zz) + drum_mortar_d(g, 0.0 * zz, zz))) - 0.006 - shrink   # inside the core everywhere
    Vx, Vy, Vz = (views[None, :, k] for k in range(3))
    for a in range(0, n, 8192):
        P = cen[a:a + 8192][:, None, :]                          # (m, 1, 3)
        D = P - views[None, :, :]                                # view -> point
        A = np.maximum(D[..., 0] ** 2 + D[..., 1] ** 2, 1e-12)
        B = 2 * (Vx * D[..., 0] + Vy * D[..., 1])
        Cq = Vx ** 2 + Vy ** 2 - r_min ** 2
        disc = B * B - 4 * A * Cq
        sq = np.sqrt(np.maximum(disc, 0.0))
        t1 = np.clip((-B - sq) / (2 * A), 0.0, 0.999)            # the chord of the sight line inside the core
        t2 = np.clip((-B + sq) / (2 * A), 0.0, 0.999)
        z1, z2 = Vz + t1 * D[..., 2], Vz + t2 * D[..., 2]
        lo_, hi_ = np.maximum(np.minimum(z1, z2), z_lo), np.minimum(np.maximum(z1, z2), z_hi)
        blocked = (disc > 0) & (t2 - t1 > 1e-4) & (lo_ < hi_)    # inside the closed core shell at some height
        out[a:a + 8192] = ~blocked
    out[free] = True
    return out


def drum_ray_cull(g, targets=DRUM_PRECULL, views=None, procs=3):
    """KIT (v1_stone_watchtower r2, producer note 6): core.visibility_cull for drum masonry, with every polygon
    tested only against the views its own drum does not certainly block (drum_view_masks) -- the same probes and
    hit rule as core.visibility_cull; a polygon no view can reach is deleted without a ray.  views: the extra
    views (core.review_views of the scene are always added, as there).  Returns the polygons deleted."""
    import bmesh
    import bpy
    import multiprocessing as mp
    from mathutils.bvhtree import BVHTree
    from .. import core
    obs = [o for o in bpy.data.objects if o.type == "MESH"]
    Vs, Ts, owns, tri_base = [], [], [], {}
    nv = nt = 0
    for oi, ob in enumerate(obs):
        me = ob.data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        lt = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", lt)
        lp = np.zeros(len(me.loop_triangles), np.int64)
        me.loop_triangles.foreach_get("polygon_index", lp)
        Vs.append(co)
        Ts.append(lt.reshape(-1, 3) + nv)
        tri_base[ob.name] = (nt, lp)
        owns.append(lp + (oi + 1) * 10 ** 7)
        nv += len(co)
        nt += len(lp)
    Vw, T, own = np.concatenate(Vs), np.concatenate(Ts), np.concatenate(owns)
    VN = np.concatenate([core.review_views(Vw.min(0), Vw.max(0)), np.asarray(views if views is not None
                                                                             else tower_views_lite(g), float)])
    log(f"  drum ray cull: {nt} tris, {len(VN)} viewpoints")
    pool = None
    total = 0
    for t_ in targets:
        name = f"{g.prefix}_{t_}"
        if name not in tri_base or not len(tri_base[name][1]):
            continue
        t0, lp = tri_base[name]
        ob = bpy.data.objects[name]
        me = ob.data
        cen = np.empty(len(me.polygons) * 3)
        me.polygons.foreach_get("center", cen)
        M = np.array(ob.matrix_world)
        cen = cen.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        mask = drum_view_masks(g, cen, VN)
        order = np.argsort(lp, kind="stable")
        bounds = np.flatnonzero(np.diff(lp[order])) + 1
        groups = np.split(order + t0, bounds)
        base_id = int(own[t0]) - int(lp[0])
        hid = []
        items = []
        for g_ in groups:
            pid = int(own[g_[0]])
            m_ = mask[pid - base_id]
            if not m_.any():
                hid.append(pid)
            else:
                items.append((pid, [int(x) for x in g_], np.packbits(m_)))
        n_free = len(hid)
        chunks = [items[i::procs * 8] for i in range(procs * 8)]
        res = None
        try:
            if "fork" in mp.get_all_start_methods():
                core._VIS.update(bvh=BVHTree.FromPolygons(Vw.tolist(), T.tolist(), all_triangles=True, epsilon=0.0),
                                 V=Vw, T=T, own=own)
                with mp.get_context("fork").Pool(procs) as pool_f:
                    res = pool_f.map(_drum_vis_worker, [(VN, c_) for c_ in chunks])
            else:
                if pool is None:
                    pool = core._vis_spawn_pool(procs, Vw, T, own)
                res = pool.map(_drum_vis_worker, [(VN, c_) for c_ in chunks])
        except Exception as ex:
            log("  (drum ray cull: pool failed)", ex)
        if res is None:
            if "bvh" not in core._VIS or core._VIS.get("T") is not T:
                core._VIS.update(bvh=BVHTree.FromPolygons(Vw.tolist(), T.tolist(), all_triangles=True, epsilon=0.0),
                                 V=Vw, T=T, own=own)
            res = [_drum_vis_worker((VN, c_)) for c_ in chunks]
        hid += [int(h) for r_ in res for h in r_]
        pids = sorted(set(h - base_id for h in hid))
        if pids:
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in pids], context="FACES_ONLY")
            loose = [v for v in bm.verts if not v.link_faces]
            if loose:
                bmesh.ops.delete(bm, geom=loose, context="VERTS")
            bm.to_mesh(me)
            bm.free()
            me.update()
        log(f"  drum ray cull {name}: -{len(pids)} of {len(groups)} polygons ({n_free} with no unblocked view, "
            f"mean {mask.sum(1).mean():.0f} of {len(VN)} views per polygon)")
        total += len(pids)
    if pool is not None:
        pool.close()
        pool.join()
    return total


def tower_head_views(g):
    """reduced views round a tower head (g.ROOF): a neighbour's wall walk below and above the eave at two
    distances, and a crane ring over the roof."""
    from ..core import ring_views
    rf = getattr(g, "ROOF", None)
    if not rf:
        return np.zeros((0, 3))
    re, ze = rf["r_eave"], rf["z_eave"]
    return np.concatenate([ring_views((0, 0), [re + 0.8, re + 3.0], [ze - 2.0, ze + 1.5], n=12, phase=0.29),
                           ring_views((0, 0), [re + 12.0], [ze + 4.0], n=12, phase=0.07)])


def tower_views_lite(g):
    """the reduced view set for the drum masonry's ray pass (core.review_views are always added): eye-level and
    knee rings 0.5-5 m out, a first-floor / lookout-level ring, the crane ring, the door close-ups and the six
    review cameras."""
    from ..core import ring_views, review_cameras
    R = g.R_BASE0
    V = [ring_views((0, 0), [R + 0.5, R + 2.0, R + 5.0], [0.4, 1.65], n=16),
         ring_views((0, 0), [R + 2.6], [4.5, 7.5], n=12, phase=0.21),
         ring_views((0, 0), [R + 9.0], [6.0, 11.0], n=12, phase=0.11)]
    fy = -g.R_DOOR
    V.append(np.array([(x, fy - d, z) for d in (0.5, 1.0, 2.0) for z in (0.4, 1.1, 1.7, 2.3) for x in (-0.9, 0.0, 0.9)]))
    co = np.concatenate([np.array(o.bound_box) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
                         for o in g.coll.all_objects if o.type == "MESH"])
    V.append(review_cameras(co.min(0), co.max(0)))
    return np.concatenate(V)


def tower_hidden_cull(g, targets=TOWER_CULL_TARGETS, procs=3, precull=DRUM_PRECULL, lite=DRUM_PRECULL):
    """KIT COMPONENT (post step, after drum_finish): delete the faces of the named objects no viewpoint can see.
    Every target has a continuous backing (wall core, mortar backing, sarking deck), so no cull opens a hole.
    Round 2 (build time): the `precull` drum objects first lose their faces behind the wall core analytically
    (drum_precull); then (lite non-empty) every target is ray-tested in ONE pass against tower_views_lite +
    tower_head_views (eye / knee, lookout-level, eave-level and crane rings, door close-ups, review cameras), each
    polygon only against the views the drum's closed core shell does not block (drum_ray_cull).
    precull=() and lite=() give the round-1 behaviour (core.visibility_cull on the full tower_views)."""
    import bpy
    from ..core import visibility_cull
    names = [f"{g.prefix}_{t}" for t in targets if f"{g.prefix}_{t}" in bpy.data.objects]
    n0 = drum_precull(g, [t for t in precull if t in targets]) if precull else 0
    if lite:                                  # one BVH / pool: drum masonry and head on the reduced views
        n1 = drum_ray_cull(g, [nm[len(g.prefix) + 1:] for nm in names],
                           views=np.concatenate([tower_views_lite(g), tower_head_views(g)]), procs=procs)
        n2 = 0
    else:
        n1, n2 = 0, visibility_cull(names, extra_views=tower_views(g), procs=procs)
    n = n0 + n1 + n2
    log(f"hidden-geometry cull ({len(names)} objects): -{n} polygons (analytic {n0}, reduced-view rays {n1}, "
        f"full-view rays {n2})")
    return n
