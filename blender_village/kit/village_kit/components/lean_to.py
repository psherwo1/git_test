"""components.lean_to -- the WALL add-ons' shared core and the lean-to (kit 1.19, a1 add-ons; plan step 4).

A single-slope (mono-pitch) roof against ANY straight wall face of ANY design, from the kit's own pieces:

    W = plane_wall(origin=(x, y), out=(nx, ny))        # a straight outer wall face and its outward normal
    lean_to(g, "store", W, s0=-1.2, s1=1.3, depth=1.8, z_face=2.26, pitch_deg=20, covering="shingle",
            soft=dict(eave_sag=0.03, eave_sweep=0.05), below=HOST_ROOF)

How it is built (nothing new is invented for the roof itself, note 16):
  roof     a GableRoof (components.linear_roof, so the village's shingle / thatch courses, deck, verge board,
           eave roll and the soft-line warp: sag, swept / bell-cast eave, out-of-true wave) whose RIDGE lies
           `ridge_in` behind the wall face; linear_roof builds it, the far slope (inside the host) is clipped away
           and every part is TRIMMED `trim` behind the face (junctions.clip_at_tower on the wall as the face of a
           very large circle -- the round-wall junction machinery reused unchanged on a straight wall).
  framing  common rafters from a hewn LEDGER let into the wall to the eave (the kit's rafter section), a
           plate / front beam at the support line, both following the roof's warp.
  junction the true covering / wall line is traced by rays; a lime-mortar flaunching (junctions.ride_fillet) rides
           on it and a closed lead apron (junctions.wall_end_apron) closes each verge end against the stone, the
           v3 longhouse's roof-into-wall language; the junction is registered for the seal-probe guard
           (guards.register_junction(arc=...)).  below=<host GableRoof>: the add-on must stay `below_clear` under
           the host's eave (its rafter tails or soffit) along the whole run, or a ValueError says where.
  supports lean_to: rubble END walls (rubble_walls.path_stone_wall, a thin U path, quoins at the front corners,
           heads tucked under the deck) or open ends; the front on the plate with dressed-pad posts and curved
           knee braces where the span needs them.
Objects: <P>_<name>_deck / _covering / _verge / _rafters (kit), <P>_<name>_framing (ledger, rafters, plate,
posts: M_timber), <P>_<name>_pads (M_stone_dressed), <P>_<name>_flashing (M_mortar / M_lead), the end walls'
<P>_<name>_end<k>_stones / _quoins / _mortar.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, beam, finalize, obox, prof_rect, sweep

EZ = np.array([0.0, 0.0, 1.0])
ROOF_PARTS = (("deck", 0.03), ("rafters", 0.02), ("covering", 0.03), ("eave_roll", 0.03), ("ridge", 0.03),
              ("comb", 0.03), ("verge", 0.03))
"""linear_roof's objects (<P>_<roof>_<part>) and how far behind the wall face each is trimmed (behind the rubble's
recessed mortar body, so no cut end shows)."""

RAFTER = dict(w=0.11, h=0.15, spacing=0.55)
"""the kit's rafter section (linear_roof._rafters) and the common-rafter spacing."""


SAGITTA = 0.001
"""a1 round 2: the largest bow (m) the stand-in circle of a straight wall may show over the add-on's run."""


def wall_R(L, sagitta=SAGITTA):
    """a1 round 2: the stand-in circle's radius for a straight run of L m: sagitta L^2 / (8 R) <= `sagitta`, and
    never under the round-1 2 km (so every run up to 4 m keeps R = 2000)."""
    return max(2000.0, float(L) ** 2 / (8.0 * float(sagitta)))


def plane_wall(origin, out, R=None, run=None):
    """a straight outer wall face: origin (x, y) on it, out = its outward plan normal.  -> dict(O, n, t, R) with
    t = the run direction (n turned -90 deg, so the add-on's local +y is n).  R: the radius of the circle whose face
    stands in for the plane in the round-wall junction pieces.  a1 round 2: R=None sizes it from the run (wall_R:
    sagitta <= 1 mm) -- from `run` (m) here when given, else from the add-on's own covering length when mono_roof
    builds on it (resolve_wall), so a straight wall of any length works; an explicit R is kept as given."""
    n = np.array([float(out[0]), float(out[1]), 0.0])
    n /= np.linalg.norm(n)
    t = np.array([n[1], -n[0], 0.0])
    if R is None and run is not None:
        R = wall_R(run)
    return dict(O=np.array([float(origin[0]), float(origin[1]), 0.0]), n=n, t=t, R=None if R is None else float(R))


def resolve_wall(W, L):
    """a1 round 2: W with its stand-in radius fixed for a run of L m (W's own R if it has one, else wall_R(L)); a
    given R whose sagitta over L exceeds 1 mm raises (the junction pieces would bow off the face)."""
    R = W.get("R")
    if R is None:
        return dict(W, R=wall_R(L))
    if float(L) ** 2 / (8.0 * float(R)) > SAGITTA + 1e-9:
        raise ValueError(f"plane_wall: R {R:.0f} m bows {1000 * L ** 2 / (8 * R):.1f} mm over the {L:.2f} m run "
                         f"(> {1000 * SAGITTA:.0f} mm); leave R=None (sized from the run) or pass run=")
    return W


def wall_field(W, s_mid):
    """the junctions 'tower' dict of the wall face, centred on the run's middle (s_mid along t)."""
    C = W["O"] + W["t"] * float(s_mid) - W["n"] * W["R"]
    R = W["R"]
    return dict(center=C[:2].copy(), R=lambda z, _R=R: np.full(np.shape(np.asarray(z, float)), _R), name="wall")


def behind(W, P):
    """plan distance of points P (n, 3) behind the wall face (> 0 inside the masonry / host)."""
    P = np.atleast_2d(np.asarray(P, float))
    return -((P[:, 0] - W["O"][0]) * W["n"][0] + (P[:, 1] - W["O"][1]) * W["n"][1])


def _down(bvh, x, y, z_from=40.0):
    from mathutils import Vector
    h = bvh.ray_cast(Vector((float(x), float(y), z_from)), Vector((0.0, 0.0, -1.0)), z_from + 1.0)
    return None if h[0] is None else float(h[0][2])


def _host_bottom(host, P, lift_max=None):
    """the lowest part of a host GableRoof's eave over world plan points P: its deck underside, minus its rafter
    tails (kit section) where it has them (none where an eave lift exceeds lift_max)."""
    z = host.under_z_world(P)
    tails = np.full(len(z), RAFTER["h"] / math.cos(host.p))
    if lift_max is not None and getattr(host, "LIFTS", None):
        Ql = host.to_local(np.column_stack([P[:, 0], P[:, 1], np.zeros(len(P))]))
        tails[host.lift_z(Ql[:, 0], Ql[:, 1]) > lift_max] = 0.0
    return z - tails


ROLL_NEAR_REACH = 2.0
"""a1 round 3: how far (m) the lateral roll check looks from each add-on vertex (find_nearest's reach)."""


def _roll_gap(g, below, pre, W, near=True):
    """a1 round 2: the host's eave roll's BELLY over the add-on -- rays straight up from every vertex of the
    add-on's covering / verge / eave roll that lies out from the wall face, against the host's built eave roll
    (<P>_<host>_eave_roll); -> (smallest vertical gap m or None, its point, smallest distance m or None, its point).
    a1 round 3 (near=True): also the NEAREST distance from the same vertices to the roll (bvh.find_nearest, within
    ROLL_NEAR_REACH), so a roll passing BESIDE a verge, not over it, is measured too."""
    import bpy
    from mathutils import Vector
    from .junctions import _bvh
    hob = bpy.data.objects.get(f"{g.prefix}_{below.name}_eave_roll")
    if hob is None or hob.type != "MESH" or not len(hob.data.polygons):
        return None, None, None, None
    bvh = _bvh([hob])
    best, at, nbest, nat = None, None, None, None
    up = Vector((0.0, 0.0, 1.0))
    for q in ("covering", "verge", "eave_roll"):
        ob = bpy.data.objects.get(f"{pre}_{q}")
        if ob is None or ob.type != "MESH" or not len(ob.data.vertices):
            continue
        co = np.zeros(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        co = co[behind(W, co) < -0.02]
        for P in co:
            v = Vector((float(P[0]), float(P[1]), float(P[2])))
            h = bvh.ray_cast(v + up * 1e-4, up, 6.0)
            if h[0] is not None and (best is None or h[3] < best):
                best, at = float(h[3]), (round(float(P[0]), 3), round(float(P[1]), 3), round(float(P[2]), 3))
            if near:
                f = bvh.find_nearest(v, ROLL_NEAR_REACH)
                if f[0] is not None and (nbest is None or f[3] < nbest):
                    nbest, nat = float(f[3]), (round(float(P[0]), 3), round(float(P[1]), 3), round(float(P[2]), 3))
    return best, at, nbest, nat


def _beam_along(acc, roof, xs, y, z_local, w, h, mat, c=0.02):
    """a hewn beam along the roof's local x (stations xs) at local y, its CENTRE at local z_local(x) -- laid
    through to_world, so it follows the roof's warp (sag, sweep, wave)."""
    xs = np.asarray(xs, float)
    zc = np.array([float(z_local(x)) for x in xs])
    path = roof.to_world(np.column_stack([xs, np.full(len(xs), y), zc]))
    V, F = sweep(path, EZ, prof_rect(w, h, c))
    acc.add(V, F, mat, wear=0.45)


def _wall_junction(g, name, pre, W, T, x_lo, x_hi, fillet, apron, below, below_clear, below_lift_max, below_roll,
                   below_roll_near, register, trim_ends=False):
    """a1 round 3: mono_roof's wall junction and host checks as one helper (shared with the rounded lean-to roof,
    round_lean_roof; mono_roof's behaviour is unchanged): the covering / wall line traced by rays between x_lo and
    x_hi along W["t"] (trim_ends: only the stretch where the covering meets the face), the lime flaunching on it, a
    lead apron at each end, the `below` host-eave and eave-roll checks, the seal-probe registration.
    -> (zb the roof line at the face, th its angles on the stand-in circle, C the circle centre)."""
    import bpy
    from .junctions import _bvh, _smooth_up, ride_fillet, wall_end_apron
    # ---- the junction: traced covering / wall line, flaunching, verge-end aprons -------------------------------------
    objs = [o for o in (bpy.data.objects.get(f"{pre}_{q}") for q in ("covering", "eave_roll", "ridge", "verge"))
            if o is not None and o.type == "MESH" and len(o.data.polygons)]
    bvh = _bvh(objs)
    ss = np.arange(x_lo, x_hi + 1e-9, 0.03)
    Z, Pl = [], []
    for s in ss:
        q = W["O"] + W["t"] * s
        hs = [h for h in (_down(bvh, *(q + W["n"] * off)[:2]) for off in (0.006, 0.02)) if h is not None]
        Z.append(max(hs) if hs else np.nan)
        Pl.append(q)
    Z, Pl = np.array(Z), np.array(Pl)
    ok = np.isfinite(Z)
    if trim_ends and ok.sum():                               # a1 round 3: only where the covering meets the face
        k0, k1 = np.flatnonzero(ok)[[0, -1]]
        Z, Pl, ok = Z[k0:k1 + 1], Pl[k0:k1 + 1], ok[k0:k1 + 1]
    if ok.sum() < 4:
        raise ValueError(f"mono_roof {name}: the covering does not meet the wall face")
    Z = np.interp(np.arange(len(Z)), np.flatnonzero(ok), Z[ok])
    zb = _smooth_up(Z)
    C = np.asarray(T["center"], float)
    th = np.unwrap(np.arctan2(Pl[:, 1] - C[1], Pl[:, 0] - C[0]))
    if th[-1] < th[0]:                                       # ride_fillet / apron runs go with increasing angle
        th, zb, Pl = th[::-1], zb[::-1], Pl[::-1]
    fl = Acc(pre + "_flashing", 35)
    fit = ride_fillet(fl, th, zb, T, bvh, h_up=fillet[0], out=fillet[1], lift=0.03, bury=0.035)
    if apron is not None:
        Pe = np.column_stack([Pl[:, 0], Pl[:, 1], zb + 0.03])
        for i0, i1 in ((0, 1), (-1, -2)):
            wall_end_apron(fl, Pe[i0] + EZ * 0.02, W["n"], Pe[i0] - Pe[i1], apron[1], w=apron[0], closed_lip=True)
    finalize(fl, g.coll, smooth_deg=35.0)
    crest = np.asarray(fit["z_crease"], float)
    log(f"  {pre}: flaunching {len(th)} stations, roof at the face z {zb.min():.2f}..{zb.max():.2f}, "
        f"crease {crest.max():.2f}")
    # ---- below the host's eave -------------------------------------------------------------------------------------
    if below is not None:
        hb_face = _host_bottom(below, Pl, below_lift_max)
        lip = Pl + W["n"] * float(below.ovh)
        z_lip = np.array([(_down(bvh, x, y) or -1e9) for x, y in lip[:, :2]])
        hb_lip = _host_bottom(below, lip, below_lift_max)
        m_face = float(np.min(hb_face - crest - below_clear))
        m_lip = float(np.min(hb_lip - z_lip - below_clear))
        log(f"  {pre}: under the host eave: margin at the face {m_face + below_clear:.3f} m (crease), at the host "
            f"lip line {m_lip + below_clear:.3f} m (covering)")
        if m_face < 0 or m_lip < 0:
            raise ValueError(f"mono_roof {name}: the add-on reaches the host's eave (margin face {m_face:.3f}, lip "
                             f"{m_lip:.3f} m under the {below_clear:.2f} m clearance); lower z_face or the pitch")
        if below_roll is not None:
            gap, at, gap_n, at_n = _roll_gap(g, below, pre, W, near=below_roll_near)
            if gap is None:
                log(f"  {pre}: host eave roll belly: none over the add-on")
            else:
                log(f"  {pre}: host eave roll belly over the add-on: smallest gap {gap:.3f} m at {at} "
                    f"(rule >= {below_roll:.2f} m)")
                if gap < below_roll:
                    raise ValueError(f"mono_roof {name}: the host's eave roll hangs {gap:.3f} m over the add-on at "
                                     f"{at} (< {below_roll:.2f} m); lift the host eave there or lower / trim the add-on")
            if below_roll_near:
                if gap_n is None:
                    log(f"  {pre}: host eave roll, lateral: none within {ROLL_NEAR_REACH:.1f} m of the add-on")
                else:
                    log(f"  {pre}: host eave roll, lateral (nearest from the same vertices): {gap_n:.3f} m at "
                        f"{at_n} (rule >= {below_roll:.2f} m)")
                    if gap_n < below_roll:
                        raise ValueError(f"mono_roof {name}: the host's eave roll passes {gap_n:.3f} m beside the "
                                         f"add-on at {at_n} (< {below_roll:.2f} m); lift the host eave there or "
                                         f"trim the add-on's verge / side")
    if register:
        from ..guards import register_junction
        register_junction(g, f"{name} / wall", (f"{pre}_covering", f"{pre}_verge", f"{pre}_eave_roll"),
                          C, lambda z, _R=W["R"]: _R, (float(zb.min()) - 0.3, float(zb.max()) + 0.3),
                          ring=(0.0, 0.6), arc=(float(th.min()), float(th.max())))
    return zb, th, C


def mono_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=20.0, overhang=0.30, verge=(0.18, 0.18),
              covering="shingle", ridge_in=0.30, soft=None, seed=1901, trim=None, fillet=(0.07, 0.10),
              apron=(0.12, 0.30), ledger=(0.15, 0.17), rafters=None, plate=(0.17, 0.18), below=None,
              below_clear=0.03, below_lift_max=None, thatch=(0.22, 0.08), register=True, below_roll=0.10,
              verge_board=None, below_roll_near=True):
    """KIT COMPONENT (kit 1.19): a mono-pitch roof against the straight wall face W (plane_wall), the shared core of
    lean_to and porch.porch.
        s0, s1      along W["t"]: the roof's two "gable faces" (the support ends); verge = (v0, v1) beyond them
        depth       plan distance from the wall face out to the support line (lean-to front / porch front beam)
        z_face      deck top (the roof's reference surface) at the wall face
        pitch_deg   slope; overhang: eave past the support line; covering "shingle" | "thatch" (thatch=(thick, step))
        ridge_in    the GableRoof's ridge lies this far behind the face (its far slope is clipped away)
        soft        GableRoof soft-line options (eave_sag, eave_sweep, sweep_len, ridge_sag, verge_flare, flare_len,
                    wave, wave_seed) -- note 17
        fillet      (h_up, out) of the lime-mortar flaunching; apron = (width past the verge, drop) of the lead
                    end aprons; ledger / plate = (depth, height) of the hewn ledger at the wall / the beam at the
                    support line (None: not built)
        rafters     list of local x for the common rafters (None: evenly between the verge rafters, RAFTER spacing)
        below       a host GableRoof: the add-on (flaunching crease at the face, covering under the host's lip)
                    must stay below_clear under its eave (rafter tails, or the soffit where an eave lift >
                    below_lift_max dropped them)
        below_roll  a1 round 2: with `below`, the host's built thatch eave roll must also clear every out-from-the-
                    wall vertex of the add-on's covering / verge by this much, measured straight up (_roll_gap: the
                    roll's belly, which the spec check above does not model); None: not checked
        below_roll_near a1 round 3 (GUARD, on by default; False = the round-2 vertical check only): the nearest
                    distance from the same vertices to the roll must clear below_roll too (a roll passing BESIDE
                    a verge); both numbers are logged
        verge_board a1 round 2: VERGE_BOARD overrides for the shingle bargeboards (e.g. dict(below=0.025, above=0.0):
                    a 0.12 m board cut to the covering line); None = the kit board
    W["R"] None (plane_wall's default) is sized from the covering's length here (resolve_wall).
    -> dict(roof, W, T, frame helpers); objects see the module doc."""
    import bpy
    from .junctions import _bvh, _smooth_up, clip_at_tower, ride_fillet, wall_end_apron
    from .linear_roof import GableRoof, linear_roof
    p = math.radians(pitch_deg)
    tp = math.tan(p)
    half = float(depth) + float(ridge_in)
    yaw = math.degrees(math.atan2(W["t"][1], W["t"][0]))
    origin = W["O"] - W["n"] * ridge_in
    kw = dict(soft or {})
    if covering == "thatch":
        kw.update(thick=thatch[0], step=thatch[1])
    roof = GableRoof(x0=s0, x1=s1, half=half, wall_z=float(z_face) - depth * tp, pitch_deg=pitch_deg,
                     overhang=overhang, verge=verge, origin=(origin[0], origin[1]), yaw_deg=yaw, name=name, **kw)
    if verge_board:
        roof.verge_kw = dict(verge_board)
    W = resolve_wall(W, roof.xb - roof.xa)
    pre = f"{g.prefix}_{name}"
    trim_d = dict(ROOF_PARTS) if trim is None else dict(trim)
    cut = min(trim_d.values())

    def clip(V, margin=0.0):
        return behind(W, V) > cut + margin

    linear_roof(g, roof, covering=covering, clip=clip, seed=seed, comb=False,
                rafter_skip=lambda P: np.ones(len(P), bool),            # common rafters are built below
                verge="board" if covering == "shingle" else None)
    s_mid = 0.5 * (roof.xa + roof.xb)
    T = wall_field(W, s_mid)
    done = []
    for part, d in trim_d.items():
        ob = bpy.data.objects.get(f"{pre}_{part}")
        if ob is None or ob.type != "MESH":
            continue
        n0 = len(ob.data.polygons)
        clip_at_tower(ob, T, inset=float(d))
        done.append(f"{part} {n0}->{len(ob.data.polygons)}")
    log(f"  {pre}: trimmed at the wall face: " + ", ".join(done))

    # ---- framing: ledger, common rafters, plate (local frame; laid through to_world -> follows the warp) ------------
    fr = Acc(pre + "_framing")
    rw, rh = RAFTER["w"], RAFTER["h"]
    cp = math.cos(p)
    t_ = roof.deck_t
    u_face = (roof.Y - ridge_in) / cp                        # slope distance lip -> wall face

    def raf_bot(y):                                          # rafter underside (local z) at local y
        return float(roof.ref_z(y)) - (t_ + rh) / cp
    xv0, xv1 = roof.xa + 0.07, roof.xb - 0.07                # the kit's verge rafters
    if rafters is None:
        n_in = max(1, int(math.ceil((xv1 - xv0) / RAFTER["spacing"])) - 1)
        rafters = list(np.linspace(xv0, xv1, n_in + 2)[1:-1])
    for x in rafters:
        a = roof.surf(x, 0.03, 1, -t_ - rh / 2)
        b = roof.surf(x, u_face + 0.03 / cp, 1, -t_ - rh / 2)
        beam(fr, roof.to_world(a), roof.to_world(b), rw, rh, 0.012, "M_timber", up=roof.dir_world(roof.normal(1)))
    xs = np.linspace(roof.xa + 0.03, roof.xb - 0.03, max(4, int((roof.xb - roof.xa) / 0.25) + 2))
    if ledger is not None:
        ld, lh = ledger
        yl = ridge_in + 0.5 * ld - 0.03                      # let 3 cm into the masonry
        _beam_along(fr, roof, xs, yl, lambda x: raf_bot(yl) - lh / 2 + 0.01, ld, lh, "M_timber")
    if plate is not None:
        pd, ph = plate
        _beam_along(fr, roof, xs, half, lambda x: raf_bot(half) - ph / 2 + 0.01, pd, ph, "M_timber")
    finalize(fr, g.coll, smooth_deg=30.0)
    log(f"  {pre}: ledger, {len(rafters)} common rafters, plate at {depth:.2f} m out")

    zb, th, C = _wall_junction(g, name, pre, W, T, roof.xa + 0.015, roof.xb - 0.015, fillet, apron, below, below_clear,
                               below_lift_max, below_roll, below_roll_near, register)
    rec = dict(name=name, roof=roof, W=W, T=T, depth=float(depth), half=half, ridge_in=float(ridge_in),
               raf_bot=raf_bot, rafters=list(rafters), z_face_line=zb, plate=plate, ledger=ledger)
    if not hasattr(g, "ADDONS"):
        g.ADDONS = []
    g.ADDONS.append(rec)
    return rec


class RoundLean:
    """a1 round 3 (CLIENT DIRECTION 2026-10-18 00:22, producer note 19 "an oval on the rectangle"): the reference
    surface (deck top) of a ROUNDED-HIP mono-pitch roof against the wall W.  Local frame: x along W["t"], y out from
    the SPINE (the high line, `ridge_in` behind the wall face, from x = a to x = b), z = world z.  The roof falls
    from the spine by one normalised radius rho (0 at the spine, 1 at the eave): on the straight run rho = y / Ey,
    past each end of the spine a SUPERELLIPSE quarter (exponent ne) with reach Ex along the wall and Ey out:
    rho = ((dx / Ex)^ne + (y / Ey)^ne)^(1/ne), so the eave runs round the shed's front corners in one tangent curve
    and back to the wall -- no verge, no hip crease.  The fall is softly CONVEX (+4 bulge rho (1 - rho)), and the
    whole roof arches up along the wall (arch_wall at the wall line, arch_eave at the eave, (1 - t^2)^2 along x) with
    a small out-of-true wave.  Duck-types what lean_to needs from a GableRoof: under_z_world, to_world."""

    def __init__(self, W, s0, s1, depth, z_face, pitch_deg=16.0, overhang=0.22, end_over=0.45, hip=0.55,
                 ridge_in=0.30, ne=3.0, bulge=0.04, arch_wall=0.15, arch_eave=0.18, wave=0.012, wave_seed=37,
                 deck_t=0.035, name="lean_to"):
        self.name = name
        self.W, self.t, self.n = W, np.asarray(W["t"], float), np.asarray(W["n"], float)
        self.O = np.asarray(W["O"], float) - self.n * float(ridge_in)
        self.ridge_in = float(ridge_in)
        self.a, self.b = float(s0) + float(hip), float(s1) - float(hip)
        if self.b <= self.a:
            raise ValueError(f"RoundLean: hip {hip} m leaves no straight run between s0 {s0} and s1 {s1}")
        self.Ex, self.Ey = float(hip) + float(end_over), float(ridge_in) + float(depth) + float(overhang)
        self.p = math.radians(pitch_deg)
        self.H = self.Ey * math.tan(self.p)
        self.ne, self.bulge, self.aw, self.ae = float(ne), float(bulge), float(arch_wall), float(arch_eave)
        self.wave, self.wave_seed, self.deck_t = float(wave), int(wave_seed), float(deck_t)
        self.xm, self.hl = 0.5 * (s0 + s1), 0.5 * (s1 - s0) + float(end_over)
        self.x_lo, self.x_hi = self.a - self.Ex, self.b + self.Ex
        rf = self.ridge_in / self.Ey
        self.rho_face = rf
        self.z0 = float(z_face) + self.H * rf - 4.0 * self.bulge * rf * (1.0 - rf)

    def local(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        d = P[:, :2] - self.O[:2]
        return d @ self.t[:2], d @ self.n[:2]

    def rho(self, x, y):
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        xx = np.clip(np.maximum(self.a - x, x - self.b), 0.0, None) / self.Ex
        yy = np.clip(y, 0.0, None) / self.Ey
        return (xx ** self.ne + yy ** self.ne) ** (1.0 / self.ne)

    def z_ref(self, x, y):
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        r = self.rho(x, y)
        tx = np.clip((x - self.xm) / self.hl, -1.0, 1.0)
        z = self.z0 - self.H * r + 4.0 * self.bulge * r * (1.0 - r)
        z = z + (1.0 - tx * tx) ** 2 * (self.aw * (1.0 - np.clip(r, 0, 1)) + self.ae * np.clip(r, 0, 1))
        if self.wave:
            from ..core import n2
            z = z + self.wave * n2(x * 0.35, y * 0.30, self.wave_seed)
        return z

    def under_z_world(self, P):
        x, y = self.local(P)
        return self.z_ref(x, y) - self.deck_t

    def to_world(self, Q):
        Q = np.atleast_2d(np.asarray(Q, float))
        out = np.zeros((len(Q), 3))
        out[:, :2] = self.O[:2] + Q[:, :1] * self.t[:2] + Q[:, 1:2] * self.n[:2]
        out[:, 2] = Q[:, 2]
        return out

    def columns(self, n_hip=16, step=0.20):
        """the contour columns: left hip (phi 0 -> 90 deg), the straight run, right hip (90 -> 0 deg); per column
        (x0, dx, dy): plan point at rho = (x0 + rho dx, rho dy)."""
        ph = np.linspace(0.0, 0.5 * np.pi, n_hip)
        c = np.cos(ph) ** (2.0 / self.ne)
        s = np.sin(ph) ** (2.0 / self.ne)
        xs = np.linspace(self.a, self.b, max(3, int(math.ceil((self.b - self.a) / step)) + 1))[1:-1]
        x0 = np.concatenate([np.full(n_hip, self.a), xs, np.full(n_hip, self.b)])
        dx = np.concatenate([-c * self.Ex, np.zeros(len(xs)), (c * self.Ex)[::-1]])
        dy = np.concatenate([s * self.Ey, np.full(len(xs), self.Ey), (s * self.Ey)[::-1]])
        return x0, dx, dy

    def grid(self, R, cols):
        """R (nr, nc) rho per row and column -> local X, Y (nr, nc)."""
        x0, dx, dy = cols
        return x0[None] + R * dx[None], R * dy[None]


def _grid_faces(nr, nc, off=0):
    i = np.arange(nr - 1)[:, None]
    j = np.arange(nc - 1)[None, :]
    a = off + i * nc + j
    return np.stack([a, a + 1, a + nc + 1, a + nc], -1).reshape(-1, 4)


def round_lean_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=16.0, overhang=0.22, end_over=0.45, hip=0.55,
                    ridge_in=0.30, ne=3.0, bulge=0.04, arch_wall=0.15, arch_eave=0.18, wave=0.012, seed=1901,
                    thatch=(0.08, 0.05), course=0.26, fillet=(0.07, 0.10), apron=(0.12, 0.30), ledger=(0.15, 0.17),
                    rafters=None, plate=(0.17, 0.18), end_t=0.40, hip_rafters=(22.0, 45.0, 68.0), below=None,
                    below_clear=0.03, below_lift_max=None, below_roll=0.10, below_roll_near=True, register=True,
                    verge_board=None):
    """KIT COMPONENT (kit 1.19, a1 round 3; CLIENT DIRECTION 00:22 / producer note 19): the lean-to's ROUNDED roof --
    a softly convex thatch slope whose two free ends curve round as rounded hips (RoundLean: one superellipse eave
    round each front corner and back to the wall, oversailing the end walls by end_over; no verge, no crease), in the
    village's continuous thatch courses (M_thatch: each course ONE sheet round the whole contour, a rounded butt
    thatch[1] proud of the T0 = thatch[0] coat, the eave course's nose wrapped under the deck edge), on a closed deck
    (M_timber_weathered), common rafters from a hewn ledger to past the plate, radial rafters fanning round each hip
    from the end-wall head; trimmed into the wall and sealed exactly as mono_roof (_wall_junction: the traced line,
    lime flaunching, lead aprons at the two eave ends, the `below` / roll guards, the seal-probe registration).
        end_over   how far the rounded end oversails the end wall's outer face along the wall (m)
        hip        how far in from s0 / s1 the straight spine stops (the hip's reach is hip + end_over)
        ne         the superellipse exponent of the plan curve (2 = an ellipse; 3 = fuller corners)
        bulge      convexity of the fall (m at mid-slope); arch_wall / arch_eave: the arch along the wall (m)
        course     course spacing (plan m on the straight run)
    verge_board is accepted and ignored (there are no verges).  -> the lean_to record (roof = the RoundLean)."""
    import bpy
    from .junctions import clip_at_tower
    _ = verge_board
    S = RoundLean(W, s0, s1, depth, z_face, pitch_deg=pitch_deg, overhang=overhang, end_over=end_over, hip=hip,
                  ridge_in=ridge_in, ne=ne, bulge=bulge, arch_wall=arch_wall, arch_eave=arch_eave, wave=wave,
                  wave_seed=seed % 97, name=name)
    W = resolve_wall(W, S.x_hi - S.x_lo)
    S.W = W
    pre = f"{g.prefix}_{name}"
    cols = S.columns()
    x0, dx, dy = cols
    Lc = np.hypot(dx, dy)                                    # plan metres per unit rho, per column
    nc = len(x0)
    T0, st = float(thatch[0]), float(thatch[1])
    dt = S.deck_t
    rng = np.random.default_rng(seed)

    def world(X, Y, Z):
        return np.column_stack([(S.O[0] + X * S.t[0] + Y * S.n[0]).ravel(), (S.O[1] + X * S.t[1] + Y * S.n[1]).ravel(),
                                np.asarray(Z, float).ravel()])
    # ---- deck: one closed slab rho 0.02 .. 1 ---------------------------------------------------------------------
    rr = np.linspace(0.02, 1.0, 15)
    R = np.repeat(rr[:, None], nc, 1)
    X, Y = S.grid(R, cols)
    Zt = S.z_ref(X, Y)
    nr = len(rr)
    V = np.concatenate([world(X, Y, Zt), world(X, Y, Zt - dt)])
    off = nr * nc
    top = _grid_faces(nr, nc)
    bot = _grid_faces(nr, nc, off)[:, ::-1]
    ii = np.arange(nc - 1)
    edge_o = np.stack([(nr - 1) * nc + ii, off + (nr - 1) * nc + ii, off + (nr - 1) * nc + ii + 1, (nr - 1) * nc + ii + 1], 1)
    edge_i = np.stack([ii + 1, off + ii + 1, off + ii, ii], 1)
    jj = np.arange(nr - 1)
    end0 = np.stack([jj * nc, off + jj * nc, off + (jj + 1) * nc, (jj + 1) * nc], 1)[:, ::-1]
    end1 = np.stack([jj * nc + nc - 1, (jj + 1) * nc + nc - 1, off + (jj + 1) * nc + nc - 1, off + jj * nc + nc - 1], 1)[:, ::-1]
    dk = Acc(pre + "_deck")
    dk.add(V, [top, bot, edge_o, edge_i, end0, end1], "M_timber_weathered", wear=0.4)
    finalize(dk, g.coll, smooth_deg=30.0)
    # ---- the thatch: continuous course sheets round the whole contour ----------------------------------------------
    cov = Acc(pre + "_covering", 60)
    d_r = course / S.Ey
    butts = []
    r_ = 1.0
    while r_ > S.rho_face + 0.35 * d_r:
        butts.append(r_)
        r_ -= d_r
    from ..core import n2
    for i, rb in enumerate(butts):
        Dm = course
        prof = [(-1.25 * Dm, T0 * 0.85), (-0.70 * Dm, T0 + 0.25 * st), (-0.30 * Dm, T0 + 0.65 * st),
                (-0.06 * Dm, T0 + 0.95 * st), (0.0, T0 + st)]
        if i == 0:                                           # the eave course: its nose wraps under the deck edge
            prof += [(0.035, T0 + 0.55 * st), (0.055, 0.02), (0.045, -dt - 0.03), (0.0, -dt - 0.05),
                     (-0.10, -dt - 0.025)]
        else:
            prof += [(0.025, T0 + 0.70 * st), (0.035, T0 * 0.55), (0.02, T0 * 0.25), (-0.06, T0 * 0.10)]
        dm = np.array([q[0] for q in prof])
        hh = np.array([q[1] for q in prof])
        R = rb + dm[:, None] / Lc[None, :]
        if i == len(butts) - 1:                              # the top course runs on up to the spine (into the wall)
            R[0] = 0.02
        wob = 0.018 * n2(x0 * 0.8 + 3.0 * i, np.full(nc, i * 1.7), seed + 11)       # butt line out of true
        R = R + wob[None, :] / Lc[None, :] * (np.arange(len(dm)) > 0)[:, None]
        R = np.clip(R, 0.0, 1.0 + 0.08 / Lc[None, :])
        X, Y = S.grid(R, cols)
        lift = 0.010 * n2(X * 0.9, Y * 0.9 + 4.1 * i, seed + 23)
        Z = S.z_ref(X, Y) + hh[:, None] + lift
        if i == 0:                                           # the nose below the deck hangs from the deck's own edge
            Z = np.where(hh[:, None] < 0, S.z_ref(*S.grid(np.ones_like(R), cols)) + hh[:, None], Z)
        cov.add(world(X, Y, Z), _grid_faces(len(dm), nc), "M_thatch", wear=float(rng.uniform(0.2, 0.4)))
    finalize(cov, g.coll, smooth_deg=60.0, recalc=False)
    # ---- framing: ledger, common rafters, the plate, radial hip rafters ---------------------------------------------
    fr = Acc(pre + "_framing")
    rw, rh = RAFTER["w"], RAFTER["h"]
    yl_face = S.ridge_in

    def raf_c(X, Y):                                         # rafter centre line under the deck
        return S.z_ref(X, Y) - dt - rh / 2
    a_in, b_in = s0 + end_t, s1 - end_t
    if rafters is None:
        n_in = max(1, int(math.ceil((b_in - a_in - 0.2) / RAFTER["spacing"])))
        rafters = list(np.linspace(a_in + 0.1, b_in - 0.1, n_in + 1))
    for x in rafters:
        ys = np.linspace(yl_face - 0.03, S.Ey - 0.04, 12)
        xs_ = np.full(len(ys), float(x))
        Vb, Fb = sweep(world(xs_, ys, raf_c(xs_, ys)), EZ, prof_rect(rw, rh, 0.012))
        fr.add(Vb, Fb, "M_timber", wear=0.45)
    for side, (xa_, sgn) in enumerate(((S.a, -1.0), (S.b, 1.0))):
        for phd in hip_rafters:                              # radial rafters round the hip from the end-wall head
            phr = math.radians(phd)
            c_, s_ = math.cos(phr) ** (2.0 / S.ne), math.sin(phr) ** (2.0 / S.ne)
            x_wall = (s0 + end_t) if sgn < 0 else (s1 - end_t)
            r0 = max(abs(xa_ - x_wall) / max(c_ * S.Ex, 1e-6), (yl_face + 0.05) / max(s_ * S.Ey, 1e-6))
            if r0 > 0.85:
                continue
            rs = np.linspace(r0, 0.97, 10)
            Xh, Yh = xa_ + sgn * rs * c_ * S.Ex, rs * s_ * S.Ey
            Vb, Fb = sweep(world(Xh, Yh, raf_c(Xh, Yh)), EZ, prof_rect(rw, rh, 0.012))
            fr.add(Vb, Fb, "M_timber", wear=0.45)
    xs = np.linspace(s0 + 0.03, s1 - 0.03, max(4, int((s1 - s0) / 0.25) + 2))
    if ledger is not None:
        ld, lh = ledger
        yl = yl_face + 0.5 * ld - 0.03
        xl = np.linspace(a_in, b_in, max(4, int((b_in - a_in) / 0.25) + 2))
        Vb, Fb = sweep(world(xl, np.full(len(xl), yl), raf_c(xl, np.full(len(xl), yl)) - rh / 2 - lh / 2 + 0.01),
                       EZ, prof_rect(ld, lh, 0.02))
        fr.add(Vb, Fb, "M_timber", wear=0.45)
    y_pl = S.ridge_in + float(depth)

    def plate_c(x):
        x = np.asarray(x, float)
        return raf_c(x, np.full(x.shape, y_pl)) - rh / 2 - plate[1] / 2 + 0.01
    if plate is not None:
        Vb, Fb = sweep(world(xs, np.full(len(xs), y_pl), plate_c(xs)), EZ, prof_rect(plate[0], plate[1], 0.02))
        fr.add(Vb, Fb, "M_timber", wear=0.45)
    finalize(fr, g.coll, smooth_deg=30.0)
    log(f"  {pre}: ROUNDED roof (note 19): {len(butts)} thatch courses round the contour, hips reach "
        f"{S.Ex:.2f} m along the wall ({end_over:.2f} m past the end walls), {S.Ey - S.ridge_in:.2f} m out; "
        f"ledger, {len(rafters)} common + radial hip rafters, plate at {depth:.2f} m out")
    # ---- trim at the wall face, then the junction and the guards (shared with mono_roof) ----------------------------
    T = wall_field(W, 0.5 * (S.x_lo + S.x_hi))
    done = []
    for part, d in (("deck", 0.03), ("covering", 0.03), ("framing", -0.03)):
        ob = bpy.data.objects.get(f"{pre}_{part}")
        if ob is None or ob.type != "MESH" or d < 0:         # the framing (ledger let in) is not trimmed
            continue
        n0 = len(ob.data.polygons)
        clip_at_tower(ob, T, inset=float(d))
        done.append(f"{part} {n0}->{len(ob.data.polygons)}")
    log(f"  {pre}: trimmed at the wall face: " + ", ".join(done))
    zb, th, C = _wall_junction(g, name, pre, W, T, S.x_lo + 0.015, S.x_hi - 0.015, fillet, apron, below, below_clear,
                               below_lift_max, below_roll, below_roll_near, register, trim_ends=True)

    def plate_under(x):
        return float(plate_c(np.array([float(x)]))[0]) - plate[1] / 2
    rec = dict(name=name, roof=S, W=W, T=T, depth=float(depth), half=y_pl, ridge_in=float(ridge_in),
               raf_bot=None, rafters=list(rafters), z_face_line=zb, plate=plate, ledger=ledger,
               plate_under=plate_under, round=True)
    if not hasattr(g, "ADDONS"):
        g.ADDONS = []
    g.ADDONS.append(rec)
    return rec


def knee_brace(acc, foot, head, w=(0.11, 0.12), mat="M_timber", n=13, run_in=(0.05, 0.05)):
    """a curved knee brace (the village's curved-timber language: the hoist beam's / cruck's quarter arc): from
    `foot` (on a post or a wall face, tangent vertical there) to `head` (under a beam, tangent horizontal), an
    elliptical quarter in the vertical plane through both, running run_in past each end into the members."""
    foot, head = np.asarray(foot, float), np.asarray(head, float)
    hvec = head - foot
    hvec[2] = 0.0
    bo = float(np.linalg.norm(hvec))
    hdir = hvec / bo
    bd = float(head[2] - foot[2])
    th = np.linspace(0.0, 0.5 * np.pi, n)
    s_ = bo * (1.0 - np.cos(th))
    z_ = bd * np.sin(th)
    s_ = np.concatenate([[0.0], s_, [bo + run_in[1]]])
    z_ = np.concatenate([[-run_in[0]], z_, [bd]])
    path = foot[None] + s_[:, None] * hdir[None] + z_[:, None] * EZ[None]
    side = np.cross(EZ, hdir)
    V, F = sweep(path, side, prof_rect(w[1], w[0], 0.015))
    acc.add(V, F, mat, wear=0.5)


def _clamp_under(obname, roof, tuck=0.015):
    """the rubble wall's coarse mortar sheet (0.3 m cells, kept by cell centre) can stand up to half a cell over a
    nearly level head and through the add-on's deck and covering: pull every vertex down to `tuck` m over the deck
    underside (still inside the deck, so the head stays closed)."""
    import bpy
    ob = bpy.data.objects.get(obname)
    if ob is None or ob.type != "MESH" or not len(ob.data.vertices):
        return 0
    co = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    zt = roof.under_z_world(co[:, :2]) + tuck
    m = co[:, 2] > zt
    co[m, 2] = zt[m]
    ob.data.vertices.foreach_set("co", co.ravel())
    ob.data.update()
    log(f"  {obname}: {int(m.sum())} mortar vertices clamped under the deck")
    return int(m.sum())


def lean_to(g, name, W, s0, s1, depth=1.8, z_face=2.25, pitch_deg=20.0, overhang=0.30, verge=(0.18, 0.18),
            covering="shingle", ends="rubble", end_t=0.40, front="open", post=0.20, max_span=1.8, braces=True,
            soft=None, below=None, seed=1901, end_seed=None, brace=(0.45, 0.48), headroom=(2.10, 1.95),
            gate=True, orient=True, roof_ends="square", round_kw=None, **kw):
    """KIT COMPONENT (kit 1.19): a lean-to against the straight wall W (plane_wall) between s0 and s1 (the outer
    faces of its end walls / its end posts) -- a mono_roof (see there for the roof keys, soft lines, the junction
    and the `below` host check) on its own supports:
        ends      "rubble": two rubble end walls (path_stone_wall on a thin U path: outer face, quoined front end,
                  inner face), `end_t` thick, running from 10 cm inside the host wall out to the support line, their
                  heads tucked 2 cm under the deck along the rake; "open": a post at each front corner
        front     "open": the plate spans between the end walls; with ends "open" or a clear span over max_span it is
                  carried on posts (`post` square, hewn, on dressed pad stones) with curved knee braces (braces)
        brace     a1 round 2: (reach along the plate, drop down the post) of each knee brace (round 1: 0.45, 0.48)
        headroom  a1 round 2 (GUARD, on by default; None = off): (plate, brace) -- the plate's underside over the
                  open front >= plate m and every knee-brace foot >= brace m (art bible 7, a walking bay), or a
                  guards.ClearanceError says where
        gate      a1 round 2: the open front is published as an entrance (g.CRUCK_ENTRANCES, the opt-in list the
                  guards.entrance_clearance gate reads), so the eave lip over it must clear 2.30 m and the plate
        orient    a1 round 3 (on by default; False = round 2): rubble_walls.orient_stones on each end wall, so no
                  stone comes out inside out (finalize's normal recalc guesses the side of an open stone shell)
        roof_ends a1 round 3 (CLIENT DIRECTION 00:22, producer note 19: square walls get rounded roofs; "square" =
                  round 2): "round" -- round_lean_roof: a softly CONVEX thatch slope whose two free ends curve round
                  as rounded hips (an oval over the rectangle, oversailing the corners), no verges; round_kw = its
                  keys (end_over, hip, ne, bulge, arch_wall, arch_eave, thatch, ...)
    -> the mono_roof / round_lean_roof record (+ "posts", "headroom")."""
    from .rubble_walls import orient_stones, path_stone_wall
    if ends not in ("rubble", "open") or front not in ("open",):
        raise ValueError(f"lean_to: ends {ends!r} ('rubble' | 'open'), front {front!r} ('open')")
    rafters = kw.pop("rafters", None)
    if rafters is None and ends == "rubble":
        a, b = s0 + end_t + 0.10, s1 - end_t - 0.10
        n_in = max(1, int(math.ceil((b - a) / RAFTER["spacing"])))
        rafters = list(np.linspace(a, b, n_in + 1))
    if roof_ends == "round":                                 # a1 round 3: CLIENT DIRECTION 00:22 / producer note 19
        rec = round_lean_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=pitch_deg, overhang=overhang,
                              below=below, seed=seed, rafters=rafters, end_t=end_t, **dict(round_kw or {}), **kw)
    elif roof_ends == "square":
        rec = mono_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=pitch_deg, overhang=overhang, verge=verge,
                        covering=covering, soft=soft, below=below, seed=seed, rafters=rafters, **kw)
    else:
        raise ValueError(f"lean_to: roof_ends {roof_ends!r} ('square' | 'round')")
    roof = rec["roof"]
    n, t, O = W["n"], W["t"], W["O"]
    pre = f"{g.prefix}_{name}"

    def top_fn(x, y):
        return float(roof.under_z_world(np.array([[x, y]]))[0]) + 0.02

    def in_host(P):
        return behind(W, P) > 0.04
    es = end_seed if end_seed is not None else seed + 40
    if ends == "rubble":
        for k, (sa, sb) in enumerate(((s0, s0 + end_t), (s1 - end_t, s1))):
            A0 = O + t * sa
            B0 = O + t * sb
            # interior (the wall core) on the LEFT: walk out along one face, round the front end, back along the other
            pts = [B0 - n * 0.10, B0 + n * depth, A0 + n * depth, A0 - n * 0.10]
            path_stone_wall(g, f"{name}_end{k}", [tuple(q[:2]) for q in pts], top_fn=top_fn, clip=in_host,
                            seed=es + 7 * k)
            _clamp_under(f"{pre}_end{k}_mortar", roof)
            if orient:                                       # a1 round 3: no stone turned inside out
                orient_stones(g, f"{name}_end{k}")
    # ---- posts under the plate ---------------------------------------------------------------------------------------
    posts = []
    if ends == "open":
        posts = [s0 + post / 2, s1 - post / 2]
    a_, b_ = (s0 + end_t, s1 - end_t) if ends == "rubble" else (s0 + post, s1 - post)
    if b_ - a_ > max_span:
        k = int(math.ceil((b_ - a_) / max_span))
        posts += list(np.linspace(a_, b_, k + 1)[1:-1])
    pdp, php = rec["plate"]
    yl = rec["half"]

    def plate_under(x):                                      # world z of the plate's underside at local x
        if rec.get("plate_under") is not None:               # a1 round 3: the rounded roof gives its own
            return float(rec["plate_under"](x))
        return float(roof.to_world(np.array([[x, yl, rec["raf_bot"](yl) - php + 0.01]]))[0, 2])
    xo = np.linspace(a_, b_, 41)
    zp = np.array([plate_under(x) for x in xo])
    feet = []
    if posts:
        fr, pd = Acc(pre + "_posts"), Acc(pre + "_pads")
        rng = np.random.default_rng(seed + 3)
        for x in sorted(posts):
            z_top = plate_under(x)
            base = roof.to_world(np.array([[x, yl, 0.0]]))[0]
            base[2] = 0.0
            pad_h = 0.14
            obox(pd, (base - t * 0.19 + EZ * (pad_h / 2 - 0.08))[None], t, n, EZ, 0.38, 0.36, pad_h + 0.08,
                 0.03, "M_stone_dressed", nx=5, ny=5, nz=4)
            lean = rng.uniform(-0.012, 0.012)
            beam(fr, base + EZ * (pad_h - 0.01), base + EZ * (z_top + 0.01) + t * lean, post, post, 0.02, "M_timber",
                 up=n, nx=6)
            if braces:
                for sg in (-1, 1):
                    reach = min(float(brace[0]), 0.5 * (b_ - a_) / max(1, len(posts) + 1))
                    foot = base + t * (sg * post / 2) + EZ * (z_top - float(brace[1]))
                    head = base + t * (sg * (post / 2 + reach)) + EZ * (z_top - 0.005)
                    knee_brace(fr, foot, head, w=(0.10, 0.11))
                    feet.append(float(foot[2]))
        finalize(fr, g.coll, smooth_deg=30.0)
        finalize(pd, g.coll, smooth_deg=30.0)
        log(f"  {pre}: {len(posts)} posts on dressed pads under the plate")
    rec["posts"] = posts
    # ---- a1 round 2: headroom of the open front (art bible 7) --------------------------------------------------------
    hr = dict(plate_min=round(float(zp.min()), 3), plate_mid=round(float(zp[len(zp) // 2]), 3),
              brace_min=None if not feet else round(min(feet), 3), opening=round(float(b_ - a_), 3))
    rec["headroom"] = hr
    log(f"  {pre}: open front {hr['opening']:.2f} m wide, plate underside {hr['plate_min']:.3f} m (ends) .. "
        f"{hr['plate_mid']:.3f} m (middle), lowest knee-brace foot "
        + ("none" if hr["brace_min"] is None else f"{hr['brace_min']:.3f} m")
        + ("" if headroom is None else f" (rule plate >= {headroom[0]:.2f}, brace >= {headroom[1]:.2f} m)"))
    if headroom is not None:
        from ..guards import ClearanceError
        bad = []
        if hr["plate_min"] < headroom[0] - 1e-6:
            bad.append(f"plate underside {hr['plate_min']:.3f} m < {headroom[0]:.2f} m")
        if hr["brace_min"] is not None and hr["brace_min"] < headroom[1] - 1e-6:
            bad.append(f"knee-brace foot {hr['brace_min']:.3f} m < {headroom[1]:.2f} m")
        if bad:
            raise ClearanceError(f"lean_to {name}: the open front's headroom (art bible 7): " + "; ".join(bad)
                                 + ".  Raise z_face / the host's eave arch, flatten the pitch or shorten the brace drop.")
    if gate:
        if not hasattr(g, "CRUCK_ENTRANCES"):
            g.CRUCK_ENTRANCES = []
        Oe = O + t * (0.5 * (a_ + b_)) + n * float(depth)
        g.CRUCK_ENTRANCES.append(dict(name=f"{name}_front", origin=np.array([Oe[0], Oe[1], 0.0]), out=n[:2].copy(),
                                      width=float(b_ - a_) - 0.10, head=hr["plate_min"], d0=0.12))
    return rec


__all__ = ["plane_wall", "wall_field", "behind", "mono_roof", "knee_brace", "lean_to", "ROOF_PARTS", "RAFTER"]
