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


def plane_wall(origin, out, R=2000.0):
    """a straight outer wall face: origin (x, y) on it, out = its outward plan normal.  -> dict(O, n, t, R) with
    t = the run direction (n turned -90 deg, so the add-on's local +y is n).  R: the radius of the circle whose face
    stands in for the plane in the round-wall junction pieces (sagitta under 1 mm over +-1.9 m)."""
    n = np.array([float(out[0]), float(out[1]), 0.0])
    n /= np.linalg.norm(n)
    t = np.array([n[1], -n[0], 0.0])
    return dict(O=np.array([float(origin[0]), float(origin[1]), 0.0]), n=n, t=t, R=float(R))


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


def _beam_along(acc, roof, xs, y, z_local, w, h, mat, c=0.02):
    """a hewn beam along the roof's local x (stations xs) at local y, its CENTRE at local z_local(x) -- laid
    through to_world, so it follows the roof's warp (sag, sweep, wave)."""
    xs = np.asarray(xs, float)
    zc = np.array([float(z_local(x)) for x in xs])
    path = roof.to_world(np.column_stack([xs, np.full(len(xs), y), zc]))
    V, F = sweep(path, EZ, prof_rect(w, h, c))
    acc.add(V, F, mat, wear=0.45)


def mono_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=20.0, overhang=0.30, verge=(0.18, 0.18),
              covering="shingle", ridge_in=0.30, soft=None, seed=1901, trim=None, fillet=(0.07, 0.10),
              apron=(0.12, 0.30), ledger=(0.15, 0.17), rafters=None, plate=(0.17, 0.18), below=None,
              below_clear=0.03, below_lift_max=None, thatch=(0.22, 0.08), register=True):
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

    # ---- the junction: traced covering / wall line, flaunching, verge-end aprons -------------------------------------
    objs = [o for o in (bpy.data.objects.get(f"{pre}_{q}") for q in ("covering", "eave_roll", "ridge", "verge"))
            if o is not None and o.type == "MESH" and len(o.data.polygons)]
    bvh = _bvh(objs)
    ss = np.arange(roof.xa + 0.015, roof.xb - 0.015 + 1e-9, 0.03)
    Z, Pl = [], []
    for s in ss:
        q = W["O"] + W["t"] * s
        hs = [h for h in (_down(bvh, *(q + W["n"] * off)[:2]) for off in (0.006, 0.02)) if h is not None]
        Z.append(max(hs) if hs else np.nan)
        Pl.append(q)
    Z, Pl = np.array(Z), np.array(Pl)
    ok = np.isfinite(Z)
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
    if register:
        from ..guards import register_junction
        register_junction(g, f"{name} / wall", (f"{pre}_covering", f"{pre}_verge", f"{pre}_eave_roll"),
                          C, lambda z, _R=W["R"]: _R, (float(zb.min()) - 0.3, float(zb.max()) + 0.3),
                          ring=(0.0, 0.6), arc=(float(th.min()), float(th.max())))
    rec = dict(name=name, roof=roof, W=W, T=T, depth=float(depth), half=half, ridge_in=float(ridge_in),
               raf_bot=raf_bot, rafters=list(rafters), z_face_line=zb, plate=plate, ledger=ledger)
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
            soft=None, below=None, seed=1901, end_seed=None, **kw):
    """KIT COMPONENT (kit 1.19): a lean-to against the straight wall W (plane_wall) between s0 and s1 (the outer
    faces of its end walls / its end posts) -- a mono_roof (see there for the roof keys, soft lines, the junction
    and the `below` host check) on its own supports:
        ends      "rubble": two rubble end walls (path_stone_wall on a thin U path: outer face, quoined front end,
                  inner face), `end_t` thick, running from 10 cm inside the host wall out to the support line, their
                  heads tucked 2 cm under the deck along the rake; "open": a post at each front corner
        front     "open": the plate spans between the end walls; with ends "open" or a clear span over max_span it is
                  carried on posts (`post` square, hewn, on dressed pad stones) with curved knee braces (braces)
    -> the mono_roof record (+ "posts")."""
    from .rubble_walls import path_stone_wall
    if ends not in ("rubble", "open") or front not in ("open",):
        raise ValueError(f"lean_to: ends {ends!r} ('rubble' | 'open'), front {front!r} ('open')")
    rafters = kw.pop("rafters", None)
    if rafters is None and ends == "rubble":
        a, b = s0 + end_t + 0.10, s1 - end_t - 0.10
        n_in = max(1, int(math.ceil((b - a) / RAFTER["spacing"])))
        rafters = list(np.linspace(a, b, n_in + 1))
    rec = mono_roof(g, name, W, s0, s1, depth, z_face, pitch_deg=pitch_deg, overhang=overhang, verge=verge,
                    covering=covering, soft=soft, below=below, seed=seed, rafters=rafters, **kw)
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
    # ---- posts under the plate ---------------------------------------------------------------------------------------
    posts = []
    if ends == "open":
        posts = [s0 + post / 2, s1 - post / 2]
    a_, b_ = (s0 + end_t, s1 - end_t) if ends == "rubble" else (s0 + post, s1 - post)
    if b_ - a_ > max_span:
        k = int(math.ceil((b_ - a_) / max_span))
        posts += list(np.linspace(a_, b_, k + 1)[1:-1])
    if posts:
        fr, pd = Acc(pre + "_posts"), Acc(pre + "_pads")
        rng = np.random.default_rng(seed + 3)
        pdp, php = rec["plate"]
        for x in sorted(posts):
            yl = rec["half"]
            z_top = float(roof.to_world(np.array([[x, yl, rec["raf_bot"](yl) - php + 0.01]]))[0, 2])
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
                    reach = min(0.45, 0.5 * (b_ - a_) / max(1, len(posts) + 1))
                    foot = base + t * (sg * post / 2) + EZ * (z_top - 0.48)
                    head = base + t * (sg * (post / 2 + reach)) + EZ * (z_top - 0.005)
                    knee_brace(fr, foot, head, w=(0.10, 0.11))
            posts_rec = posts
        finalize(fr, g.coll, smooth_deg=30.0)
        finalize(pd, g.coll, smooth_deg=30.0)
        log(f"  {pre}: {len(posts)} posts on dressed pads under the plate")
    rec["posts"] = posts
    return rec


__all__ = ["plane_wall", "wall_field", "behind", "mono_roof", "knee_brace", "lean_to", "ROOF_PARTS", "RAFTER"]
