"""components.timber_walls -- the TIMBER WALL family: framed timber walls along ANY plan polyline, with openings from
the kit's ONE opening spec (kit, variant v5_harbour_house; new module, no existing building uses it).

A timber wall is laid on a frame line: the plan polyline `path` is the OUTER FACE of the frame (posts), interior on the
LEFT of the walking direction (rubble_walls.PathMap, reused).  Local wall coordinates per run: s along, z up, w out.

    path_timber_wall(g, name, path, z0, top=2.6, top_fn=None, style="post_plank", openings=(), ...)   KIT COMPONENT
        z0          top of whatever carries the wall (plinth, floor band); the sill beam sits on it
        top         height of the wall plate top (the eave / storey head), flat
        top_fn      top_fn(x, y) -> height the cladding rises to above the plate (a gable under a roof deck: the deck
                    underside + 2 cm, e.g. timber_walls.roof_top_fn(roof)); None = the wall stops at the plate
        style       "post_plank"   exposed frame (sill, posts <= bay_max apart, plate) with horizontal planks set
                                   3 cm back between the posts (Nordic skiftesverk / post-and-plank)
                    "weatherboard" lapped horizontal boards (wedge section) over the frame, proud corner posts
                    "board_batten" vertical boards with battens over the joints, proud corner posts
        gable_style the cladding above the plate (default: "board_batten"; the boards run up to top_fn)
        openings    [(s, spec), ...] at path distance s (centre of the clear opening); spec from components.openings:
                    door(width, height, threshold=0, steps_to=None, ...), window(width, height, sill, shutters=True,
                    ...), or boat_door(...) below (a large two-leaf boat / barn / loading door)
        sill / plate / post   (depth w, height) of the sill beam and plate, (face, depth) of the posts
        lap_out     how far a sill / plate runs past the other wall's face at an outside corner (crossed, halved ends)
        backing     a closed sheathing slab behind the cladding (cut at the openings): producer note 6's backing, so
                    no plank gap, slipped board or cull ever shows the sky or a void (<P>_<name>_blocker)
    Builds <P>_<name>_frame (sill, posts, plate), _boards, _blocker (backing); the openings come from the kit's ONE
    opening builder, wall_openings.build_opening(host=timber) (round 2): <P>_<name>_frames (jambs, heads, sills,
    window frames, plank leaves and shutters), _ironwork (straps on the leaves; pintles are pooled linked duplicates),
    _blockers (dark rooms behind openings, note 6), _dressed (built-in stone steps).
    Publishes g.TIMBER_WALLS (name, PathMap, z0, top, style) and every opening on g.OPENINGS (the record layout of
    components.wall_openings: kind, O at Z = 0 on the face, t, n, width, height, z0, z1, head, sill, threshold,
    lintel_w), so the clearance guard, the cull's door views and the decal recipes see them.

    boat_door(width=2.6, height=2.6, leaves=2, jamb=(0.26, 0.24), head=0.30, bearing=0.30, ...)
        a large boat / barn / loading door spec: components.openings.door(...) with boat=True detail -- two (or one)
        ledged-and-braced leaves with the ledges and Z braces OUTSIDE, three strap hinges per leaf, heavy jambs and a
        head beam bearing past them into the wall.
    rect_path(x0, x1, y0, y1), rect_openings(rect, [(side, coord, spec)])   a rectangle's CCW path and its openings
        by side ("S" -Y, "E" +X, "N" +Y, "W" -X) and world coordinate along that side
    roof_top_fn(roof, tuck=0.02)        top_fn for walls under a linear_roof.GableRoof (deck underside + tuck)

Every board, plank, post and beam is one closed piece (Mask R per piece through geom.strict_clean's islands); the
cladding pieces have no back face (the backing is behind them).  Timber is M_timber (frame) / M_timber_weathered
(cladding, leaves); the kit's uvgrain pass lays the grain along each piece.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, obox
from .openings import Opening, door as _door
from .rubble_walls import PathMap

EZ = np.array([0.0, 0.0, 1.0])

STYLES = dict(
    post_plank=dict(rows=True, mid_posts=True, board=(-0.075, -0.030), post_out=0.0, sill_out=0.02, plate=True,
                    backing=(-0.150, -0.120), cover_sill=False, h=(0.20, 0.30), casing=False),
    weatherboard=dict(rows=True, mid_posts=False, board=(0.0, 0.034), post_out=0.05, sill_out=0.0, plate=False,
                      backing=(-0.030, 0.0), cover_sill=True, h=(0.19, 0.24), casing=True),
    board_batten=dict(rows=False, mid_posts=False, board=(0.0, 0.030), post_out=0.05, sill_out=0.0, plate=False,
                      backing=(-0.030, 0.0), cover_sill=True, w=(0.20, 0.30), casing=True),
)
"""per style: horizontal rows or vertical boards, visible intermediate posts, cladding w-range (m, + = out of the
frame face), how proud the corner posts / sill stand, whether the plate is visible, the backing's w-range, whether the
cladding laps 4 cm down over the sill face, board heights (rows) or widths (vertical), cased openings."""

TIMBER_OPENING = dict(
    door=dict(width=1.0, height=2.10, threshold=0.0, jamb=(0.16, 0.20), head=0.18, planks=5, leaf_t=0.045,
              leaf_set=0.06, steps_to=None, rise=0.17, tread=0.32, room=1.4, head_rule=None),
    window=dict(width=0.55, height=0.60, sill=1.15, jamb=(0.14, 0.18), head=0.16, rail=0.14, frame=0.06,
                shutters=True, room=1.0, room_pad=(0.35, 0.6, 0.35), lights=4),
    boat=dict(width=2.6, height=2.6, threshold=0.0, jamb=(0.26, 0.24), head=0.30, bearing=0.30, leaves=2,
              leaf_t=0.05, ledges=3, room=1.6, steps_to=None, rise=0.17, tread=0.32, head_rule=None),
)
"""the timber family's opening defaults (a None in the shared spec takes these): clear width / height, threshold above
the sill beam (doors) or clear sill height above the floor = sill-beam top (windows), jamb (face, depth), head / rail
heights, leaf thickness and set-back, built-in steps down to `steps_to` (absolute z), dark-room depth (note 6).
kit 1.13 (v5 round 5; default = the old fixed margins): window room_pad=(side, below, above) -- how far the dark room
reaches past the clear opening (an eyebrow window's room must stay under the wave).
kit 1.14 (v5 round 6; default = the old cross mullion): window lights=4 (cross mullion, 2 x 2) or 2 (one vertical
mullion: a two-light window)."""


def boat_door(width=2.6, height=2.6, leaves=2, jamb=(0.26, 0.24), head=0.30, bearing=0.30, ledges=3, room=1.6,
              steps_to=None, at=None, head_rule=None):
    """a large boat / barn / loading door: the shared opening spec (components.openings.door) with boat=True.
    round 2: head_rule None (the wall's: "clamp") / "clamp" / "trim" -- what happens when it is taller than its
    storey (wall_openings.TIMBER_HOST): it never crosses the storey head."""
    return _door(width=width, height=height, threshold=0.0, at=at, boat=True, leaves=leaves, jamb=jamb, head=head,
                 bearing=bearing, ledges=ledges, room=room, steps_to=steps_to, head_rule=head_rule)


def rect_path(x0, x1, y0, y1):
    """counter-clockwise closed path of a rectangle (interior on the left): S, E, N, W runs."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def side_s(rect, side, coord):
    """path distance (rect_path) of the point at world coordinate `coord` (x for S / N, y for E / W) on `side`."""
    x0, x1, y0, y1 = rect
    W, L = x1 - x0, y1 - y0
    return {"S": coord - x0, "E": W + (coord - y0), "N": W + L + (x1 - coord), "W": 2 * W + L + (y1 - coord)}[side]


def rect_openings(rect, items):
    """[(side, coord, spec), ...] -> [(s, spec), ...] on rect_path(rect)."""
    return [(side_s(rect, sd, c), sp) for (sd, c, sp) in items]


def roof_top_fn(roof, tuck=0.02):
    """top_fn(x, y) for walls under a GableRoof: the deck underside over (x, y) + tuck (the cladding tucks under)."""
    def fn(x, y):
        if getattr(roof, "warped", False):          # round 2: a sagging / swept roof (GableRoof warp)
            return float(roof.under_z_world(np.array([[float(x), float(y)]]))[0]) + tuck
        L = roof.to_local(np.array([[float(x), float(y), 0.0]]))
        return float(roof.under_z(L[0, 1])) + tuck
    return fn


def _resolve(spec):
    """a shared opening spec (components.openings) -> the timber family's dict (defaults: TIMBER_OPENING)."""
    if isinstance(spec, Opening):
        d = dict(spec["detail"])
        kind = "boat" if d.pop("boat", False) else ("door" if spec["kind"] == "door" else "window")
        out = dict(TIMBER_OPENING[kind])
        for k in ("width", "height", "sill", "threshold"):
            if spec.get(k) is not None and k in out:
                out[k] = spec[k]
        for k, v in d.items():
            if k not in out:
                raise KeyError(f"timber opening ({kind}): unknown detail {k!r}; known {sorted(out)}")
            out[k] = v
    else:
        d = dict(spec)
        kind = d.pop("kind")
        out = dict(TIMBER_OPENING[kind])
        out.update(d)
    out["kind"] = kind
    return out


# ---------------------------------------------------------------------------------------------------------------
# geometry helpers (a run's local frame: O = run start on the face line at Z = 0, t along, n out)
# ---------------------------------------------------------------------------------------------------------------
ROUGH = dict(w=(0.16, 0.40), fillet=(0.12, (0.08, 0.12)), tilt_deg=1.0, sag=0.025, edge_r=0.014, end_jag=0.015,
             thick=(0.032, 0.042), w_jit=0.005)
"""round 2 (client direction 1, at FORM level -- no surface detail, note 12): old, rough timber.  w: board widths /
row heights (m); fillet: (probability, width range) of an occasional narrow fillet board; tilt_deg: boards out of
true (+-, about their own centre); sag: mid-span sag (m) of a long horizontal member (scaled by length / 4 m, up to
1x); edge_r: the chunkier, hand-split arris radius; end_jag: uneven board ends (+- m); thick: board thickness range;
w_jit: per-board depth jitter (neighbours that lean into each other overlap in depth, never in one plane).  Shared
by path_timber_wall(rough=...) and the cruck infill (components.cruck)."""


def rough_opts(rough):
    """None -> None; True -> ROUGH; a dict -> ROUGH updated with it."""
    if rough is None or rough is False:
        return None
    out = dict(ROUGH)
    if isinstance(rough, dict):
        out.update(rough)
    return out


def board_widths(rng, a, b, ws, rough=None):
    """split [a, b] into boards of widths in ws (or rough['w'] with occasional fillets); the last one closes the
    run (a short remainder is merged into the board before it)."""
    if rough is None:
        xs = [a]
        while b - xs[-1] > ws[1]:
            xs.append(xs[-1] + rng.uniform(*ws))
        xs.append(b)
        if len(xs) > 2 and xs[-1] - xs[-2] < 0.6 * ws[0]:
            xs.pop(-2)
        return xs
    lo, hi = rough["w"]
    p_f, f_rng = rough["fillet"]
    xs = [a]
    while b - xs[-1] > hi:
        w = rng.uniform(*f_rng) if rng.uniform() < p_f else math.exp(rng.uniform(math.log(lo), math.log(hi)))
        xs.append(xs[-1] + w)
    xs.append(b)
    if len(xs) > 2 and xs[-1] - xs[-2] < 0.6 * lo:
        xs.pop(-2)
    return xs


def wbox(acc, F, s0, s1, z0, z1, w0, w1, mat, r=0.008, ns=4, nz=4, clamp=None, skip_back=False, wear=None,
         kick=None, tilt=0.0, sag=0.0, floor=None):
    """one closed rounded box in a run frame F = (O, t, n[, bow]): s in [s0, s1], z in [z0, z1], w in [w0, w1].
    clamp(s) -> z: vertices above it are lowered onto it (a board under a roof rake); skip_back: no inward (-w) face
    (cladding with a backing behind); kick=(k_top, k_bot): wedge section -- the thickness scales from k_top at the
    top to 1 at the bottom and the bottom kicks out (lapped weatherboards).
    round 2: tilt (rad) -- the piece is out of true in the wall plane (sheared about its centre: a tall piece leans
    along s, a long one slopes in z); sag (m) -- a long piece sags at mid-span; floor(s) -> z: vertices below it
    are raised onto it (a board standing on an arch); F[3] = bow(s) -> w: the whole run bows out of its plane."""
    O, t, n = F[0], F[1], F[2]
    bow = F[3] if len(F) > 3 else None
    if s1 - s0 < 0.004 or z1 - z0 < 0.004 or w1 - w0 < 0.002:
        return
    zc = 0.5 * (z0 + z1)
    org = O + s0 * t + 0.5 * (w0 + w1) * n + zc * EZ
    LZ = w1 - w0
    Ls, Lz = s1 - s0, z1 - z0

    def deform(P):
        P = P.copy()
        if kick is not None:
            v = (P[..., 1] + 0.5 * (z1 - z0)) / (z1 - z0)
            th = kick[0] + (1.0 - kick[0]) * (1.0 - v)
            P[..., 2] = (P[..., 2] + 0.5 * LZ) * th - 0.5 * LZ + kick[1] * (1.0 - v)
        if tilt:
            if Lz >= Ls:
                P[..., 0] = P[..., 0] + P[..., 1] * math.tan(tilt)
            else:
                P[..., 1] = P[..., 1] + (P[..., 0] - 0.5 * Ls) * math.tan(tilt)
        if sag:
            P[..., 1] = P[..., 1] - sag * np.sin(np.pi * np.clip(P[..., 0] / Ls, 0, 1))
        if floor is not None:
            s = s0 + P[..., 0]
            zf = np.vectorize(floor)(s) - zc
            P[..., 1] = np.maximum(P[..., 1], zf)
        if clamp is not None:
            s = s0 + P[..., 0]
            zt = np.vectorize(clamp)(s) - zc
            P[..., 1] = np.minimum(P[..., 1], zt)
        if bow is not None:
            P[..., 2] = P[..., 2] + np.vectorize(bow)(s0 + P[..., 0])
        return P
    need = clamp is not None or kick is not None or tilt or sag or floor is not None or bow is not None
    obox(acc, org[None], t, EZ, n, s1 - s0, z1 - z0, LZ, r, mat, nx=ns, ny=nz, nz=4,
         deform=deform if need else None, skip_back=skip_back)
    if wear is not None and acc.MG:
        acc.MG[-1][:] = wear


def _sub_rect(p, b):
    """rectangle p minus rectangle b (both (s0, s1, z0, z1)) -> list of pieces."""
    s0, s1, z0, z1 = p
    a0, a1, c0, c1 = b
    if a1 <= s0 or a0 >= s1 or c1 <= z0 or c0 >= z1:
        return [p]
    out = []
    if a0 > s0:
        out.append((s0, a0, z0, z1))
    if a1 < s1:
        out.append((a1, s1, z0, z1))
    m0, m1 = max(s0, a0), min(s1, a1)
    if c0 > z0:
        out.append((m0, m1, z0, c0))
    if c1 < z1:
        out.append((m0, m1, c1, z1))
    return out


def _subtract(pieces, blocks):
    for b in blocks:
        nxt = []
        for p in pieces:
            nxt.extend(_sub_rect(p, b))
        pieces = nxt
    return pieces


def _free(lo, hi, occ):
    """the parts of [lo, hi] not covered by the intervals occ."""
    out = [(lo, hi)]
    for (a, b) in sorted(occ):
        nxt = []
        for (u, v) in out:
            if b <= u or a >= v:
                nxt.append((u, v))
                continue
            if a > u:
                nxt.append((u, a))
            if b < v:
                nxt.append((b, v))
        out = nxt
    return [(u, v) for (u, v) in out if v - u > 0.03]


def _sheet(acc, F, ss, zs, keep, w0, w1, mat, clamp=None):
    """a closed slab on the (s, z) grid ss x zs between w0 and w1, cells keep(i, j) only (front, back and the side
    walls on every open cell edge); clamp(s) -> z lowers nodes onto a roof rake (cells that collapse are dropped)."""
    O, t, n = F[0], F[1], F[2]
    bow = F[3] if len(F) > 3 else None
    ss, zs = np.asarray(ss, float), np.asarray(zs, float)
    S, Z = np.meshgrid(ss, zs, indexing="ij")
    if clamp is not None:
        Z = np.minimum(Z, np.array([[clamp(s)] * len(zs) for s in ss]))
    ns_, nz_ = S.shape
    Wb = np.zeros(S.shape) if bow is None else np.vectorize(bow)(S)
    P = lambda w: (O[None, None] + S[..., None] * t + Z[..., None] * EZ + (w + Wb)[..., None] * n).reshape(-1, 3)  # noqa: E731
    V = np.concatenate([P(w1), P(w0)])
    off = ns_ * nz_
    I = lambda i, j: i * nz_ + j  # noqa: E731
    K = np.zeros((ns_ - 1, nz_ - 1), bool)
    for i in range(ns_ - 1):
        for j in range(nz_ - 1):
            dz = max(Z[i, j + 1] - Z[i, j], Z[i + 1, j + 1] - Z[i + 1, j])
            K[i, j] = keep(i, j) and dz > 0.002
    Fq = []
    for i in range(ns_ - 1):
        for j in range(nz_ - 1):
            if not K[i, j]:
                continue
            Fq.append((I(i, j), I(i + 1, j), I(i + 1, j + 1), I(i, j + 1)))
            Fq.append((off + I(i, j), off + I(i, j + 1), off + I(i + 1, j + 1), off + I(i + 1, j)))
            if j == 0 or not K[i, j - 1]:
                Fq.append((I(i, j), off + I(i, j), off + I(i + 1, j), I(i + 1, j)))
            if j == nz_ - 2 or not K[i, j + 1]:
                Fq.append((I(i, j + 1), I(i + 1, j + 1), off + I(i + 1, j + 1), off + I(i, j + 1)))
            if i == 0 or not K[i - 1, j]:
                Fq.append((I(i, j), I(i, j + 1), off + I(i, j + 1), off + I(i, j)))
            if i == ns_ - 2 or not K[i + 1, j]:
                Fq.append((I(i + 1, j), off + I(i + 1, j), off + I(i + 1, j + 1), I(i + 1, j + 1)))
    if Fq:
        acc.add(V, np.array(Fq), mat)


# ---------------------------------------------------------------------------------------------------------------
# openings: the kit's ONE opening builder, wall_openings.build_opening(host=...) (round 2: the private builder retired)
# ---------------------------------------------------------------------------------------------------------------
def _opening_layout(sp, s_c, floor, st, head_max=None, plate_top=None, head_rule="clamp"):
    """an opening's clear rect and the cladding block rect (the opening's own jambs, rails and head, cased).
    round 2: a door taller than its storey head (head_max) is laid out as wall_openings' timber host builds it --
    "clamp": the clear top and the block stop at the plate underside; "trim": the block stops at the plate top."""
    hw = sp["width"] / 2
    jw = sp["jamb"][0]
    if sp["kind"] == "window":
        cz0 = floor + sp["sill"]
        cz1 = cz0 + sp["height"]
        bot = cz0 - sp["rail"]
        top = cz1 + sp["head"]
    else:
        cz0 = floor + sp["threshold"]
        cz1 = cz0 + sp["height"]
        bot = floor - 0.30                       # a door's block reaches through the sill line
        top = cz1 + sp["head"]
        if head_max is not None and top > head_max + 1e-6:
            rule = sp.get("head_rule") or head_rule
            if rule == "clamp":
                cz1 = top = head_max
            elif rule == "trim" and plate_top is not None:
                top = plate_top
    clear = (s_c - hw, s_c + hw, cz0, cz1)
    block = (s_c - hw - jw - (0.04 if sp["kind"] != "window" else 0.0), s_c + hw + jw +
             (0.04 if sp["kind"] != "window" else 0.0), bot, top)
    return clear, block


def _plate_cut(sp, s_c, floor, plate_bot, head_rule):
    """(s0, s1) of the plate an opening cuts (head_rule 'trim', the opening taller than its storey), else None."""
    if sp["kind"] == "window":
        return None
    rule = sp.get("head_rule") or head_rule
    cz1 = floor + sp["threshold"] + sp["height"]
    if rule == "trim" and cz1 + sp["head"] > plate_bot + 1e-6:
        hw, jw = sp["width"] / 2, sp["jamb"][0]
        return (s_c - hw - jw, s_c + hw + jw)
    return None


def _build_opening(g, oaccs, F, sp, s_c, floor, head_max, st, rng, label, ground, plate_top=None, plate_w=None,
                   head_rule="clamp"):
    """one opening of a timber wall: wall_openings.build_opening with the timber host (see TIMBER_HOST there)."""
    from .wall_openings import build_opening
    O, t, n = F[0], F[1], F[2]
    bow = F[3] if len(F) > 3 else None
    w_off = 0.0 if bow is None else float(bow(s_c))
    host = dict(face=st["board"][1] if st["casing"] else 0.0, floor=floor, head_max=head_max, plate_top=plate_top,
                plate_w=plate_w, head_rule=head_rule, ground=ground, casing=st["casing"])
    return build_opening(g, sp, O + s_c * t + w_off * n, t, n, oaccs, rng, label=label, host=host)


# ---------------------------------------------------------------------------------------------------------------
# the wall
# ---------------------------------------------------------------------------------------------------------------
def path_timber_wall(g, name, path, z0, top=2.6, top_fn=None, style="post_plank", gable_style="board_batten",
                     openings=(), sill=(0.24, 0.18), plate=(0.22, 0.20), post=(0.22, 0.22), bay_max=2.4, lap_out=0.07,
                     backing=True, seed=301, clip_z=None, ground_z=0.0, rough=None, bow=0.0, head_rule="clamp"):
    """KIT COMPONENT (see the module doc).
    round 2 (defaults = round 1 except the openings, which now come from wall_openings.build_opening(host=...)):
    rough=True | dict -- old, rough timber at form level (ROUGH: wider-ranging board widths with fillets, boards
    +-1 deg out of true, sagging long members, chunkier split edges, uneven ends); bow (m) -- every run bows out of
    true by this much at mid-run; head_rule -- a door / boat door taller than its storey: "clamp" (the plate is the
    lintel) or "trim" (the plate is cut and the head beam replaces it flush); see wall_openings.TIMBER_HOST."""
    if style not in STYLES or gable_style not in STYLES:
        raise ValueError(f"path_timber_wall {name!r}: style {style!r} / {gable_style!r}; one of {sorted(STYLES)}")
    st, gst = STYLES[style], STYLES[gable_style]
    pm = PathMap(path)
    rng = np.random.default_rng(seed)
    pre = f"{g.prefix}_{name}"
    A = pm.A
    closed = bool(np.allclose(A[0], A[-1]))
    nseg = len(pm.L)
    sd, sh = sill
    pd_, ph = plate
    pw, pdp = post
    from .wall_openings import finish_accs, opening_accs
    accs = dict(frame=Acc(pre + "_frame"), boards=Acc(pre + "_boards"), back=Acc(pre + "_blocker"))
    oaccs = opening_accs(g, name)                    # <P>_<name>_frames, _dressed, _ironwork, _reveals, _blockers
    ro = rough_opts(rough)

    def corner_kind(k):
        """vertex k of the path: 'convex' / 'concave' / 'open' (path end)."""
        if not closed and (k == 0 or k == nseg):
            return "open"
        a = pm.dir[(k - 1) % nseg]
        b = pm.dir[k % nseg]
        return "convex" if a[0] * b[1] - a[1] * b[0] > 1e-6 else ("concave" if a[0] * b[1] - a[1] * b[0] < -1e-6
                                                                    else "straight")
    ops_by_seg = {i: [] for i in range(nseg)}
    for s_c, spec in openings:
        i = int(pm.seg(s_c))
        ops_by_seg[i].append((float(s_c - pm.S[i]), _resolve(spec)))
    floor = z0 + sh
    n_open = 0
    for i in range(nseg):
        L = float(pm.L[i])
        O = np.array([A[i][0], A[i][1], 0.0])
        t = np.array([pm.dir[i][0], pm.dir[i][1], 0.0])
        n = np.array([pm.nrm[i][0], pm.nrm[i][1], 0.0])
        if bow:                                      # round 2: the run bows out of true (0 at its ends)
            F = (O, t, n, lambda s, L=float(pm.L[i]): bow * math.sin(math.pi * min(max(s / L, 0.0), 1.0)))
        else:
            F = (O, t, n)
        k0, k1 = corner_kind(i), corner_kind(i + 1)

        def ext(k, side):
            if k == "convex":
                return st["sill_out"] + lap_out
            if k == "concave":
                return -sd
            return 0.0
        dz = 0.015 * (i % 2)
        rake = None
        if top_fn is not None:
            def rake(s, O=O, t=t):
                p = O + s * t
                return float(top_fn(p[0], p[1]))
        zt_max = top if rake is None else max(top, max(rake(s) for s in np.linspace(0, L, 41)))
        # ---- sill and plate (crossed, halved ends at outside corners; heights alternate by 1.5 cm per run)
        e0, e1 = ext(k0, 0), ext(k1, 1)
        sag_l = 0.0 if ro is None else ro["sag"] * min(1.0, L / 4.0)
        wbox(accs["frame"], F, -e0, L + e1, z0, floor - dz, -sd, st["sill_out"], "M_timber", r=0.014,
             ns=max(4, int(L / 1.2) + 2))
        seg_ops = sorted(ops_by_seg[i], key=lambda o: o[0])
        plate_bot = top - ph + dz
        if st["plate"]:
            # round 2: a door taller than its storey with head_rule "trim" cuts the plate between its jambs (its head
            # beam replaces the plate there, flush); every other opening stays under the plate
            cuts = sorted(c for c in (_plate_cut(sp, sc, floor, plate_bot, head_rule) for (sc, sp) in seg_ops) if c)
            spans, a_ = [], -e0
            for (c0, c1) in cuts:
                spans.append((a_, c0 - 0.004))
                a_ = c1 + 0.004
            spans.append((a_, L + e1))
            for (u_, v_) in spans:
                if v_ - u_ > 0.02:
                    wbox(accs["frame"], F, u_, v_, plate_bot, top, -pd_, st["sill_out"], "M_timber", r=0.014,
                         ns=max(4, int((v_ - u_) / 1.2) + 2), sag=sag_l if not cuts else 0.0)
        # ---- posts: corner / end posts, opening jambs, intermediate posts
        occ = []
        out = st["post_out"]
        p_lo = floor - dz - 0.02
        p_hi_frame = (top - ph + dz + 0.02) if st["plate"] else top
        # corner / end posts: an outside corner's post is built once, by the run that ends there, and stands `out`
        # proud of both faces; an open path end gets a plain end post
        for (k, s_at) in ((k0, 0.0), (k1, L)):
            if k not in ("convex", "open"):
                continue
            if k == "open":
                a, b = (0.0, pw) if s_at == 0.0 else (L - pw, L)
            else:
                a, b = (-out, pw - out) if s_at == 0.0 else (L - pw + out, L + out)
            if k == "open" or s_at == L:
                zt = p_hi_frame if rake is None else max(p_hi_frame, top, rake(min(max(s_at, 0.0), L)))
                wbox(accs["frame"], F, a, b, p_lo, zt, -pdp + out, out, "M_timber", r=0.016)
            occ.append((a, b))
        blocks, clears = [], []
        for (sc, sp) in seg_ops:
            clear, block = _opening_layout(sp, sc, floor, st, head_max=plate_bot if st["plate"] else top,
                                           plate_top=top if st["plate"] else None, head_rule=head_rule)
            clears.append(clear)
            blocks.append(block)                              # the cladding stops at the opening's own jambs
        if st["mid_posts"]:
            gaps = _free(0.0, L, occ + [(b_[0], b_[1]) for b_ in blocks])
            for (u, v) in gaps:
                nb = int(math.ceil((v - u) / bay_max))
                for k in range(1, nb):
                    sm = u + (v - u) * k / nb
                    wbox(accs["frame"], F, sm - pw / 2, sm + pw / 2, p_lo, p_hi_frame, -pdp, 0.0, "M_timber",
                         r=0.016)
                    occ.append((sm - pw / 2, sm + pw / 2))
        # ---- openings: wall_openings.build_opening with the timber host (it records them on g.OPENINGS)
        for (sc, sp) in seg_ops:
            _build_opening(g, oaccs, F, sp, sc, floor, plate_bot if st["plate"] else top, st, rng,
                           f"{name}_{n_open}", ground_z, plate_top=top if st["plate"] else None,
                           plate_w=(-pd_, st["sill_out"]), head_rule=head_rule)
            n_open += 1
        # ---- cladding below the plate (the storey) and above it (gable / eave strip)
        corner_occ = [(a, b) for (a, b) in occ if a <= 1e-6 or b >= L - 1e-6]
        z_lo = (floor - dz - 0.04) if st["cover_sill"] else (floor - dz - 0.01)
        z_hi = (top - ph + dz + 0.01) if st["plate"] else top
        has_gable = rake is not None and zt_max > top + 0.03
        if has_gable and not st["plate"] and gst is st and not st["rows"]:
            # vertical cladding with a hidden plate runs on unbroken from the sill to the roof line
            _clad(accs, F, L, z_lo, zt_max, st, corner_occ, blocks, rng,
                  lambda s, rake=rake: max(rake(s), top), rough=ro)
        else:
            _clad(accs, F, L, z_lo, z_hi, st, occ if st["mid_posts"] else corner_occ, blocks, rng, None, rough=ro)
            if has_gable:
                g_lo = top - 0.012 if st["plate"] else z_hi
                _clad(accs, F, L, g_lo, zt_max, gst, corner_occ, blocks, rng, rake, gable=True, rough=ro)
        # ---- backing behind the cladding (cut at the clear openings)
        if backing:
            w0, w1 = st["backing"]
            ss = sorted(set([0.0, L] + [c for cl in clears for c in (cl[0], cl[1])]
                            + (list(np.arange(0.6, L, 0.6)) if rake is not None else [])))
            zz = sorted(set([floor - dz - 0.02, top] + [c for cl in clears for c in (cl[2], cl[3])]
                            + ([zt_max] if zt_max > top + 0.03 else [])))
            ss, zz = np.array(ss), np.array(zz)

            def keep(a, b, ss=ss, zz=zz, clears=clears):
                sm, zm = 0.5 * (ss[a] + ss[a + 1]), 0.5 * (zz[b] + zz[b + 1])
                return not any(c[0] < sm < c[1] and c[2] < zm < c[3] for c in clears)
            _sheet(accs["back"], F, ss, zz, keep, w0, w1, "M_timber_weathered",
                   clamp=None if rake is None else (lambda s, rake=rake: max(rake(s) - 0.01, top)))
    for k, a in accs.items():
        if a.n:
            finalize(a, g.coll, smooth_deg=30.0, **({} if clip_z is None else dict(clip_z=clip_z)))
    finish_accs(g, oaccs)
    if not hasattr(g, "TIMBER_WALLS"):
        g.TIMBER_WALLS = []
    g.TIMBER_WALLS.append(dict(name=name, map=pm, z0=z0, floor=floor, top=top, top_fn=top_fn, style=style))
    log(f"  {pre}: timber wall ({style}), {nseg} runs, {n_open} openings")
    return pm


def _clad(accs, F, L, z_lo, z_hi, st, occ, blocks, rng, rake, gable=False, rough=None):
    """the cladding of one run between z_lo and z_hi (rake: the roof line above), minus posts and opening blocks.
    rough (ROUGH, round 2): rough timber at form level (see ROUGH)."""
    if rough is not None:
        return _clad_rough(accs, F, L, z_lo, z_hi, st, occ, blocks, rng, rake, rough)
    acc = accs["boards"]
    w0, w1 = st["board"]
    free = _free(0.0, L, occ)
    clamp = None if rake is None else rake
    if st["rows"]:
        hs = st["h"]
        zs = [z_lo]
        while z_hi - zs[-1] > hs[1]:
            zs.append(zs[-1] + rng.uniform(*hs))
        zs.append(z_hi)
        if len(zs) > 2 and zs[-1] - zs[-2] < 0.6 * hs[0]:
            zs.pop(-2)
        lap = 0.03 if st.get("cover_sill") else 0.0
        for k in range(len(zs) - 1):
            za, zb = zs[k], zs[k + 1]
            pieces = []
            for (u, v) in free:
                if rake is not None:
                    sg = np.linspace(u, v, max(3, int((v - u) / 0.02)))
                    ok = np.array([rake(s) > za + 0.03 for s in sg])
                    if not ok.any():
                        continue
                    idx = np.flatnonzero(ok)
                    u_, v_ = float(sg[idx[0]]), float(sg[idx[-1]])
                else:
                    u_, v_ = u, v
                tuck = 0.0 if st["casing"] else 0.03
                pieces.append((u_ - tuck, v_ + tuck, za - (lap if k > 0 else 0.0), zb))
            pieces = _subtract(pieces, blocks)
            for (a, b, c, d) in pieces:
                if b - a < 0.05 or d - c < 0.03:
                    continue
                # long runs of cladding split into staggered lengths (2.5-4.5 m)
                cuts = [a]
                while b - cuts[-1] > 4.6:
                    cuts.append(cuts[-1] + rng.uniform(2.5, 4.4))
                cuts.append(b)
                for j in range(len(cuts) - 1):
                    sa, sb = cuts[j] + (0.002 if j else 0.0), cuts[j + 1] - (0.002 if j < len(cuts) - 2 else 0.0)
                    ns_ = max(4, int((sb - sa) / 0.25) + 3) if rake is not None else max(4, int((sb - sa) / 1.5) + 3)
                    kick = (0.35, 0.016) if st.get("cover_sill") else None
                    wbox(acc, F, sa, sb, c, d - 0.003, w0, w1, "M_timber_weathered", r=0.006, ns=ns_, nz=4,
                         clamp=clamp, skip_back=True, kick=kick)
    else:
        ws = st["w"]
        for (u, v) in free:
            xs = [u]
            while v - xs[-1] > ws[1]:
                xs.append(xs[-1] + rng.uniform(*ws))
            xs.append(v)
            if len(xs) > 2 and xs[-1] - xs[-2] < 0.6 * ws[0]:
                xs.pop(-2)
            pieces = []
            for j in range(len(xs) - 1):
                a, b = xs[j] + 0.003, xs[j + 1] - 0.003
                hi = z_hi if rake is None else max(rake(a), rake(b))
                if rake is not None and hi < z_lo + 0.03:
                    continue
                pieces.append((a, b, z_lo, hi))
            pieces = _subtract(pieces, blocks)
            for (a, b, c, d) in pieces:
                if b - a < 0.04 or d - c < 0.03:
                    continue
                wbox(acc, F, a, b, c, d, w0, w1, "M_timber_weathered", r=0.006, ns=4, nz=4, clamp=clamp,
                     skip_back=True)
            # battens over the board joints
            for j in range(1, len(xs) - 1):
                xm = xs[j]
                hi = z_hi if rake is None else rake(xm) - 0.01
                for (a, b, c, d) in _subtract([(xm - 0.035, xm + 0.035, z_lo + 0.02, hi)], blocks):
                    if d - c < 0.05 or b - a < 0.05:
                        continue
                    wbox(acc, F, a, b, c, d, w1, w1 + 0.022, "M_timber_weathered", r=0.006, ns=4, nz=4, clamp=clamp)


def _clad_rough(accs, F, L, z_lo, z_hi, st, occ, blocks, rng, rake, ro):
    """_clad with ROUGH (round 2): irregular widths / row heights with fillets, pieces out of true, sagging rows,
    chunky arrises, uneven board ends, per-board depth jitter.  Battens over vertical-board joints as before."""
    acc = accs["boards"]
    w0 = st["board"][0]
    free = _free(0.0, L, occ)
    clamp = None if rake is None else rake
    tilt = math.radians(ro["tilt_deg"])
    if st["rows"]:
        zs = board_widths(rng, z_lo, z_hi, None, dict(ro, w=(max(0.14, ro["w"][0]), min(0.34, ro["w"][1]))))
        lap = 0.03 if st.get("cover_sill") else 0.0
        for k in range(len(zs) - 1):
            za, zb = zs[k], zs[k + 1]
            pieces = []
            for (u, v) in free:
                if rake is not None:
                    sg = np.linspace(u, v, max(3, int((v - u) / 0.02)))
                    ok = np.array([rake(s) > za + 0.03 for s in sg])
                    if not ok.any():
                        continue
                    idx = np.flatnonzero(ok)
                    u_, v_ = float(sg[idx[0]]), float(sg[idx[-1]])
                else:
                    u_, v_ = u, v
                tuck = 0.0 if st["casing"] else 0.03
                pieces.append((u_ - tuck, v_ + tuck, za - (lap if k > 0 else 0.0), zb))
            for (a, b, c, d) in _subtract(pieces, blocks):
                if b - a < 0.05 or d - c < 0.03:
                    continue
                th = rng.uniform(*ro["thick"])
                wj = rng.uniform(-ro["w_jit"], ro["w_jit"])
                ns_ = max(4, int((b - a) / 0.25) + 3) if rake is not None else max(5, int((b - a) / 0.6) + 3)
                kick = (0.35, 0.016) if st.get("cover_sill") else None
                wbox(acc, F, a, b, c, d - 0.003, w0 + wj, w0 + wj + th, "M_timber_weathered", r=ro["edge_r"],
                     ns=ns_, nz=4, clamp=clamp, skip_back=True, kick=kick,
                     tilt=0.3 * tilt * rng.uniform(-1, 1), sag=ro["sag"] * min(1.0, (b - a) / 4.0) * rng.uniform(0.5, 1))
        return
    for (u, v) in free:
        xs = board_widths(rng, u, v, None, ro)
        pieces = []
        for j in range(len(xs) - 1):
            a, b = xs[j] + 0.004, xs[j + 1] - 0.004
            hi = z_hi if rake is None else max(rake(a), rake(b))
            if rake is not None and hi < z_lo + 0.03:
                continue
            pieces.append((a, b, z_lo + rng.uniform(-0.5, 0.5) * ro["end_jag"], hi))
        for (a, b, c, d) in _subtract(pieces, blocks):
            if b - a < 0.04 or d - c < 0.03:
                continue
            th = rng.uniform(*ro["thick"])
            wj = rng.uniform(-ro["w_jit"], ro["w_jit"])
            d_ = d if rake is not None else d - rng.uniform(0, ro["end_jag"])
            wbox(acc, F, a, b, c, d_, w0 + wj, w0 + wj + th, "M_timber_weathered", r=ro["edge_r"], ns=4,
                 nz=max(4, int((d_ - c) / 0.8) + 3), clamp=clamp, skip_back=True, tilt=tilt * rng.uniform(-1, 1))
        w1 = w0 + ro["thick"][1] + ro["w_jit"]
        for j in range(1, len(xs) - 1):
            xm = xs[j]
            hi = z_hi if rake is None else rake(xm) - 0.01
            for (a, b, c, d) in _subtract([(xm - 0.04, xm + 0.04, z_lo + 0.02, hi)], blocks):
                if d - c < 0.05 or b - a < 0.05:
                    continue
                wbox(acc, F, a, b, c, d, w1, w1 + 0.025, "M_timber_weathered", r=0.008, ns=4,
                     nz=max(4, int((d - c) / 0.8) + 3), clamp=clamp, tilt=0.4 * tilt * rng.uniform(-1, 1))


def resolve_timber(spec):
    """a shared opening spec (components.openings) -> the timber family's dict (TIMBER_OPENING defaults); the input
    of wall_openings.build_opening(host=...)."""
    return _resolve(spec)


__all__ = ["path_timber_wall", "boat_door", "rect_path", "rect_openings", "side_s", "roof_top_fn", "wbox",
           "STYLES", "TIMBER_OPENING", "ROUGH", "rough_opts", "board_widths", "resolve_timber"]
