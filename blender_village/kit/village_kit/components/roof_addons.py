"""components.roof_addons -- the ROOF add-ons (kit 1.19, v7 cottage; plan step 4): small reusable pieces that
attach to any GableRoof design.  Every piece is built from the kit's existing modules and materials (note 16) and
carries the village's soft, round language (note 17).

    roof_valley(g, main, wing, ...)   KIT COMPONENT: two linear roofs meeting in a VALLEY at any angle (an L or T
                                      plan, a dormer roof into its host slope).  The wing (the roof that runs INTO
                                      the other) is traced where its covering top meets the main roof's top -- up one
                                      valley, over the wing's ridge roll, down the other valley -- and a soft ROLLED
                                      THATCH VALLEY (the eave roll's D language, swelling +-1 cm, rounded tapered ends)
                                      is swept along that line, its two skirts buried in both coverings.  The wing's
                                      comb shakes near the main slope are dropped whole.  -> <P>_<name> (M_thatch)
    solid_clip(roof, under=True)      clip(P, margin=0) for linear_roof(clip=...): inside (and, under=True, anywhere
                                      under) another roof's solid -- the coverings yield to each other at the valley
    deck_clip(roof, below=0.0)        P under another roof's DECK top (its plan columns) -- for linear_roof(deck_clip=),
                                      so the two decks are kept up to the line where they cross: a closed backing
    any_clip(*clips)                  the union of clips
    roofs_top_fn(roofs, tuck=0.02)    top_fn(x, y) for walls under SEVERAL roofs (an L plan): the highest deck
                                      underside over the point, + tuck
    top_world(roof, P) / top_normal(roof, P)   the roof solid's top (world z, warp included) / its normal over plan P

    GabledDormer(main, x, side, ...)  the spec of a GABLED DORMER on a GableRoof slope (a sibling of the shingle
                                      eyebrow, GableRoof(eyebrows=)): its own small soft GableRoof (.roof, yawed 90 deg
                                      to the host), a board-and-batten front and two cheeks, the kit window, and the
                                      host clips (.clip_main, .deck_clip_main)
    gabled_dormer(g, D, ...)          KIT COMPONENT: builds it after the host roof: the dormer's walls
                                      (timber_walls.path_timber_wall, board_batten, rough, kit window), its roof
                                      (linear_roof, thatch, its own lead hat + turned finial at the front apex), the
                                      valley into the host (roof_valley) and a rolled thatch FOOT ROLL round the
                                      cheeks and the front where the host thatch meets the boards (no slot, no tooth)

    chimney(g, name, center, ...)     KIT COMPONENT: a round, battered and softened rubble chimney stack
                                      (rubble_walls.round_stone_body) through / against a GableRoof (a stack at a gable
                                      or through the slope or ridge), sealed with the v3 / v5 roof-into-round-wall
                                      junction (roof_junction.wall_abutment: trim, lime-mortar flaunching on the true
                                      line, lead end aprons; a ring of flaunching when the roof surrounds the stack),
                                      a dressed drip-course cap, a dark flue, and a round crown: "pot" (default, a
                                      round dressed-stone pot) or "louvre" (opt-in: a LOW round smoke louvre, dressed
                                      posts under a little lead cone, no finial unless asked) -> <P>_<name>_* ;
                                      g.CHIMNEYS
    chimney_decals(g, seed)           soot / lichen anchors on every chimney's head (run in the recipe's decals step)

All functions take the frame g first, are deterministic for their seeds, and add nothing a recipe does not call.
"""
import math

import numpy as np

from ..core import log, n2
from ..geom import Acc, finalize


# =================================================================================================================
# clips and height fields
# =================================================================================================================
def solid_clip(roof, under=True, lift=0.0, x_pad=0.06):
    """clip(P, margin=0) -> bool: P (world) inside `roof`'s solid (GableRoof.keep_out), or with under=True anywhere
    under it in its plan columns; margin > 0 asks for points that much deeper (linear_roof's deck call)."""
    def clip(V, margin=0.0):
        return roof.keep_out(np.asarray(V, float), lift=lift - margin, x_pad=x_pad, under=under)
    return clip


def deck_clip(roof, below=0.0, x_pad=0.0):
    """clip(P, margin=0) -> bool: P (world) under `roof`'s deck top (reference surface, warp included) inside its
    plan columns (|y| < lip, xa..xb) -- for linear_roof(deck_clip=...)."""
    def clip(V, margin=0.0):
        L = roof.to_local(np.asarray(V, float))
        return ((L[:, 0] > roof.xa - x_pad) & (L[:, 0] < roof.xb + x_pad) & (np.abs(L[:, 1]) < roof.Y)
                & (L[:, 2] < roof.ref_z(L[:, 1]) - below - margin))
    return clip


def any_clip(*clips):
    """the union of clip(P, margin) functions (None entries are skipped)."""
    cs = [c for c in clips if c is not None]

    def clip(V, margin=0.0):
        V = np.asarray(V, float)
        m = np.zeros(len(V), bool)
        for c in cs:
            m |= np.asarray(c(V, margin), bool)
        return m
    return clip


def top_world(roof, P):
    """the top of `roof`'s solid (covering envelope, eave roll, ridge roll; GableRoof.section_columns) in WORLD z
    (warp included) over the plan points P (n, 2|3); -inf outside its plan columns."""
    P = np.atleast_2d(np.asarray(P, float))
    Q = np.zeros((len(P), 3))
    Q[:, :2] = P[:, :2]
    L = roof.to_local(Q)
    ya, zt, _zb = roof.section_columns()
    ok = np.isfinite(zt)
    ay = np.abs(L[:, 1])
    top = np.interp(ay, ya[ok], zt[ok])
    inside = (ay <= float(ya[ok].max())) & (L[:, 0] >= roof.xa) & (L[:, 0] <= roof.xb)
    return np.where(inside, top + roof.warp_z(L[:, 0], L[:, 1]), -np.inf)


def top_normal(roof, P, e=0.03):
    """unit normals of top_world(roof, .) at plan points P (central differences; +Z where undefined)."""
    P = np.atleast_2d(np.asarray(P, float))[:, :2]
    ex, ey = np.array([e, 0.0]), np.array([0.0, e])
    dx = (top_world(roof, P + ex) - top_world(roof, P - ex)) / (2 * e)
    dy = (top_world(roof, P + ey) - top_world(roof, P - ey)) / (2 * e)
    dx, dy = np.nan_to_num(dx, nan=0.0, posinf=0.0, neginf=0.0), np.nan_to_num(dy, nan=0.0, posinf=0.0, neginf=0.0)
    n = np.stack([-dx, -dy, np.ones(len(P))], 1)
    return n / np.linalg.norm(n, axis=1, keepdims=True)


class straight_span:
    """kit 1.20 (v7 round 4): `with straight_span(MAIN, WING): composite_decals(g, ...)` -- while inside, each
    round-hipped GableRoof (GableRoof(hips=...)) reports its STRAIGHT ridge span as xa / xb, so the composite moss
    anchors (laid on the plain slope frame along xa..xb) stay off the folded hips, whose slope frame turns.
    Roofs without hips are untouched."""

    def __init__(self, *roofs):
        self.roofs = [r for r in roofs if getattr(r, "HIPS", None) is not None]
        self.saved = []

    def __enter__(self):
        self.saved = [(r, r.xa, r.xb) for r in self.roofs]
        for r in self.roofs:
            r.xa, r.xb = r.ridge_span()
        return self

    def __exit__(self, *exc):
        for r, a, b in self.saved:
            r.xa, r.xb = a, b
        return False


def roofs_top_fn(roofs, tuck=0.02):
    """top_fn(x, y) for walls under several GableRoofs (an L / T plan): the highest deck underside (warp included)
    of the roofs whose plan columns hold (x, y), + tuck; the first roof's if none does."""
    roofs = list(roofs)

    def fn(x, y):
        best = None
        for r in roofs:
            L = r.to_local(np.array([[float(x), float(y), 0.0]]))[0]
            if r.xa - 0.05 <= L[0] <= r.xb + 0.05 and abs(L[1]) <= r.Y:
                z = float(r.under_z_world([[x, y]])[0])
                best = z if best is None else max(best, z)
        if best is None:
            best = float(roofs[0].under_z_world([[x, y]])[0])
        return best + tuck
    return fn


# =================================================================================================================
# kit 1.21 (v7 round 5): the hidden-geometry cull with eye-level views into the RE-ENTRANT corners of an L / T plan
# =================================================================================================================
def reentrant_views(footprint, reach=(0.35, 0.9, 1.7, 2.8, 4.0), heights=(0.9, 1.7, 2.5)):
    """viewpoints (n, 3) in the exterior wedge of every RE-ENTRANT (concave) corner of a plan polygon: the grid
    corner + a u1 + b u2 (u1, u2 the two wall directions away from the corner; a, b in `reach`) at each height.
    footprint_views loops round the plan BOUNDING BOX, so the pocket under the deep eave of an L's inside corner
    (and its valley foot) is seen by none of them, and the cull deleted wall faces a visitor at the door sees."""
    F = np.asarray(footprint, float)[:, :2]
    if np.allclose(F[0], F[-1]):
        F = F[:-1]
    n = len(F)
    area = 0.5 * float(np.sum(F[:, 0] * np.roll(F[:, 1], -1) - np.roll(F[:, 0], -1) * F[:, 1]))
    orient = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        a, v, b = F[i - 1], F[i], F[(i + 1) % n]
        e1, e2 = v - a, b - v
        if orient * (e1[0] * e2[1] - e1[1] * e2[0]) >= -1e-9:       # convex or straight
            continue
        u1, u2 = (a - v) / np.linalg.norm(a - v), (b - v) / np.linalg.norm(b - v)
        for s in reach:
            for t in reach:
                p = v + s * u1 + t * u2
                for z in heights:
                    out.append((p[0], p[1], z))
    return np.array(out).reshape(-1, 3)


def hidden_cull(g, extra_views=(), min_polys=0, procs=4):
    """KIT COMPONENT (post step, kit 1.21): composite.composite_hidden_cull(views="lean") plus `extra_views` (n, 3)
    tested for every target (e.g. reentrant_views(footprint)).  extra_views=() is the lean cull unchanged."""
    from ..core import visibility_cull
    from .composite import BACKING, LEAN_VIEWS, ROOF_PARTS, ROOF_VIEWS, _meshes, footprint_views
    targets = [o.name for o in _meshes(g)
               if o.data.users == 1 and not any(b in o.name for b in BACKING) and len(o.data.polygons) >= min_polys]
    ex = np.asarray(extra_views, float).reshape(-1, 3)
    common = np.concatenate([footprint_views(g, **ROOF_VIEWS), ex])
    low = footprint_views(g, **dict(LEAN_VIEWS, heights=(0.6,), crane=(6.0, ())))
    by = {t: low for t in targets if not any(r in t for r in ROOF_PARTS)}
    n = visibility_cull(targets, extra_views=common, extra_by_target=by, procs=procs)
    log(f"hidden-geometry cull: -{n} polygons on {len(targets)} objects (+{len(ex)} re-entrant corner views)")
    return n


# =================================================================================================================
# the swept crease roll (valley / dormer foot)
# =================================================================================================================
def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-9)


def _crease_roll(acc, P, nA, nB, a, b, width=(0.34, 0.34), crown=0.16, bury=(0.10, 0.10), var=0.06, seed=0,
                 taper=0.30, end_out=0.10, mat="M_thatch", wear=0.45, sink=(0.0, 0.0), n_tuck=4, bury_dir=None):
    """sweep ONE soft closed roll along the crease line P (n, 3) where surface A (normal nA, in-surface direction a
    pointing away from the crease) meets surface B (nB, b).  The section: a buried keel under the crease, each skirt
    `width` out along its surface ending `bury` under it, a rounded back rising to `crown` over the crease on the
    bisector; it swells +-var (one low-frequency wave, like thatch.d_roll), and both ends taper over `taper` m and
    close in a ROUNDED TUCK (kit 1.19 r2): `n_tuck` rings on a quarter circle `end_out` m past the line's end,
    shrinking to a point and diving sink[0] / sink[1] m (start / end) under the bisector -- the roll's end is tucked
    into the coverings, no flat cap.  Each section is kept non-folding (the skirts never cross the bisector).
    kit 1.19 r3: bury_dir=(dA, dB) (each None or (n, 3)): the direction each skirt END dives along (default -nA / -nB);
    over a tight convex bend (a valley arch over a ridge roll) a radial dive folds the skirt end back on itself."""
    n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    T = _unit(T)

    def perp(v):
        return _unit(v - (v * T).sum(1, keepdims=True) * T)
    a, b = perp(a), perp(b)
    bis = perp(nA + nB)
    wa, wb = width
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    sw = 1.0 + var * n2(s * 0.9, np.zeros(n), seed)
    de = np.minimum(s, s[-1] - s)
    tf = 0.40 + 0.60 * np.clip(de / max(taper, 1e-3), 0, 1) ** 0.6
    f = (sw * tf)[:, None]
    dA, dB = (bury_dir or (None, None))
    dA = nA if dA is None else dA
    dB = nB if dB is None else dB
    ring = [
        -bis * 0.5 * (bury[0] + bury[1]),
        a * wa - dA * bury[0],
        a * wa * 0.84 + nA * 0.025,
        a * wa * 0.60 + nA * 0.075,
        a * wa * 0.34 + nA * 0.115 + bis * 0.015,
        a * wa * 0.12 + bis * crown * 0.93,
        bis * crown,
        b * wb * 0.12 + bis * crown * 0.93,
        b * wb * 0.34 + nB * 0.115 + bis * 0.015,
        b * wb * 0.60 + nB * 0.075,
        b * wb * 0.84 + nB * 0.025,
        b * wb - dB * bury[1],
    ]
    L = np.stack([P + f * r for r in ring], 1)                     # (n, m, 3)
    # the rounded tucks: rings on a quarter circle past each end, shrinking and diving under the bisector
    so = np.atleast_1d(np.asarray(end_out, float))
    so = np.repeat(so, 2) if len(so) == 1 else so
    sk = np.atleast_1d(np.asarray(sink, float))
    sk = np.repeat(sk, 2) if len(sk) == 1 else sk
    tucks, tips = [], []
    for e, (i, sgn) in enumerate(((0, -1.0), (n - 1, 1.0))):
        rr = []
        for k in range(1, int(n_tuck) + 1):
            th = 0.5 * math.pi * k / (n_tuck + 1)
            c = P[i] + T[i] * sgn * so[e] * math.sin(th) - bis[i] * sk[e] * (1.0 - math.cos(th))
            rr.append(c[None, :] + (L[i] - P[i][None, :]) * math.cos(th))
        tucks.append(np.stack(rr))
        tips.append(P[i] + T[i] * sgn * so[e] - bis[i] * sk[e])
    L = np.concatenate([tucks[0][::-1], L, tucks[1]])
    nn, m = L.shape[:2]
    V = np.vstack([L.reshape(-1, 3), np.array(tips)])
    t0, t1 = nn * m, nn * m + 1
    i = np.arange(nn - 1)[:, None]
    j = np.arange(m)[None, :]
    a_ = i * m + j
    b_ = i * m + (j + 1) % m
    Q = np.stack([a_, b_, b_ + m, a_ + m], -1).reshape(-1, 4)
    jj = np.arange(m)
    C0 = np.stack([np.full(m, t0), (jj + 1) % m, jj], 1)
    C1 = np.stack([np.full(m, t1), (nn - 1) * m + jj, (nn - 1) * m + (jj + 1) % m], 1)
    # outward: the face at the crest of the middle station must face along the bisector
    im = n // 2
    k = (im + int(n_tuck)) * m + 6
    qq = V[[k, k + 1, k + 1 + m, k + m]]
    if float(np.cross(qq[1] - qq[0], qq[3] - qq[0]) @ bis[im]) < 0:
        Q, C0, C1 = Q[:, ::-1], C0[:, ::-1], C1[:, ::-1]
    acc.add(V, [Q, C0, C1], mat, wear=wear)
    return float(s[-1])


def _continuous(v, want):
    """direction vectors v (n, 3) made continuous along the line (each flipped to agree with the previous one), then
    flipped as a whole to agree with the majority of the per-station wishes `want` (n, 3) -- a valley skirt never
    twists from one station to the next (kit 1.19 r2: the crumpled foot cap)."""
    out = v.copy()
    for i in range(1, len(out)):
        if float(out[i] @ out[i - 1]) < 0:
            out[i] = -out[i]
    if float(np.sign((out * want).sum(1)).sum()) < 0:
        out = -out
    return out


def _smooth_rows(v, passes=3):
    """a few 1-2-1 passes along the line, renormalised (normals / skirt directions of a calm section)."""
    v = v.copy()
    for _ in range(passes):
        v[1:-1] = 0.25 * v[:-2] + 0.5 * v[1:-1] + 0.25 * v[2:]
    return _unit(v)


def _plan_cols(roof, V, pad=0.0):
    """V (world) inside `roof`'s plan columns padded by `pad` m (|local y| < Y + pad, xa - pad < x < xb + pad)."""
    L = roof.to_local(np.asarray(V, float))
    return (np.abs(L[:, 1]) < roof.Y + pad) & (L[:, 0] > roof.xa - pad) & (L[:, 0] < roof.xb + pad)


def _plan_meet(main, wing, ym, yw):
    """the plan point (world x, y) where main-local y = ym meets wing-local y = yw."""
    p0 = main.to_world(np.array([[0.0, ym, 0.0]]))[0]
    p1 = main.to_world(np.array([[1.0, ym, 0.0]]))[0]
    w0, w1 = wing.to_local(np.array([p0, p1]))[:, 1]
    t = (yw - w0) / (w1 - w0)
    return p0[:2] + t * (p1[:2] - p0[:2])


def _drop_faces(ob, pred):
    """delete the faces of mesh object `ob` whose world centroid satisfies pred(C (n, 3)) -> bool; returns the count."""
    import bmesh
    mw = np.array(ob.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    faces = list(bm.faces)
    if not faces:
        bm.free()
        return 0
    C = np.array([f.calc_center_median() for f in faces])
    C = C @ mw[:3, :3].T + mw[:3, 3]
    kill = np.asarray(pred(C), bool)
    bmesh.ops.delete(bm, geom=[f for f, k in zip(faces, kill) if k], context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return int(kill.sum())


def _lip_frame(main, wing, sgm, sgw):
    """the re-entrant lip corner Cl (plan) and the two lip directions away from it: e_m along main's lip (away from
    the wing), e_w along the wing's lip (away from main); the exterior quadrant is Cl + a e_m + b e_w (a, b > 0)."""
    Cl = np.asarray(_plan_meet(main, wing, sgm * main.Y, sgw * wing.Y), float)
    out = []
    for r, o in ((main, wing), (wing, main)):
        d = np.asarray(r.dir_world(np.array([1.0, 0.0, 0.0]))[:2], float)
        d = d / np.linalg.norm(d)
        q = np.array([[*(Cl + 0.6 * d), 0.0]])
        if bool(_plan_cols(o, q)[0]):
            d = -d
        out.append(d)
    return Cl, out[0], out[1]


def _lip_z(roof, sg, Q):
    """world z of `roof`'s lip line (u = 0 on its reference surface, warp included) at the local x of plan points Q."""
    Q = np.atleast_2d(np.asarray(Q, float))
    L = roof.to_local(np.column_stack([Q[:, :2], np.zeros(len(Q))]))
    return roof.to_world(roof.surf(L[:, 0], np.zeros(len(Q)), int(sg), 0.0))[:, 2]


def _corner_roll(acc, main, wing, sgm, sgw, r=0.25, ext=0.30, grow=1.05, end_f=0.94, seed=0, blend=None):
    """kit 1.19 r3: ONE swept INTERNAL-CORNER ROLL -- the eave roll's own D section (main.roll_section()) carried
    round the re-entrant lip corner on a fillet of radius r in plan (tangent to both lips, in the exterior quadrant),
    with `ext` m straight runs on along both lips; the lip height and the section's up blend smoothly from main's
    slope to the wing's.  The section is `grow` x the straight rolls' (it envelops their cut ends, _corner_close) and
    tapers to end_f x over the last 0.1 m of each run, where it dives inside the straight rolls.
    kit 1.21 (v7 r5; None = old): blend (m) -- the taper runs over the last `blend` m of each run as a smoothstep
    (tangent at both ends): a long, shallow overlap in which the corner roll sinks into the straight roll, in place
    of the short 0.1 m step that read as a flat-faced sleeve band."""
    Cl, em, ew = _lip_frame(main, wing, sgm, sgw)
    C = Cl + r * em + r * ew
    ds = 0.03
    s_m = np.arange(ext, 0.0, -ds)
    ph = np.linspace(0.0, 0.5 * math.pi, max(8, int(0.5 * math.pi * r / ds) + 1))
    s_w = np.arange(ds, ext + 1e-9, ds)
    Pm = (Cl + r * em)[None] + em[None] * s_m[:, None]
    Pa = C[None] - r * (np.cos(ph)[:, None] * ew[None] + np.sin(ph)[:, None] * em[None])
    Pw = (Cl + r * ew)[None] + ew[None] * s_w[:, None]
    Q = np.concatenate([Pm, Pa, Pw])
    w = np.concatenate([np.zeros(len(Pm)), 0.5 - 0.5 * np.cos(2.0 * ph), np.ones(len(Pw))])
    inward = np.concatenate([np.repeat(-ew[None], len(Pm), 0), (Pa - C[None]) / r, np.repeat(-em[None], len(Pw), 0)])
    sd = np.concatenate([s_m, np.zeros(len(Pa)), s_w])           # distance out along a straight run
    z = (1 - w) * _lip_z(main, sgm, Q) + w * _lip_z(wing, sgw, Q)
    P = np.column_stack([Q, z])
    Nm = np.asarray(main.dir_world(main.normal(int(sgm))), float)
    Nw = np.asarray(wing.dir_world(wing.normal(int(sgw))), float)
    N = _unit((1 - w)[:, None] * Nm[None] + w[:, None] * Nw[None])
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    T = _unit(T)
    N = _unit(N - (N * T).sum(1, keepdims=True) * T)
    I = _unit(np.cross(N, T))
    I3 = np.column_stack([inward, np.zeros(len(P))])
    I = np.where(((I * I3).sum(1) < 0)[:, None], -I, I)
    uo, _vis = main.roll_section()
    uo = np.asarray(uo, float)
    if blend is None:
        f = grow - (grow - end_f) * np.clip((sd - (ext - 0.10)) / 0.10, 0, 1)
    else:
        tb = np.clip((sd - (ext - float(blend))) / max(float(blend), 1e-6), 0, 1)
        f = grow - (grow - end_f) * tb * tb * (3.0 - 2.0 * tb)
    L = P[:, None, :] + f[:, None, None] * (I[:, None, :] * uo[None, :, 0:1] + N[:, None, :] * uo[None, :, 1:2])
    n, m = L.shape[:2]
    V = np.vstack([L.reshape(-1, 3), L[0].mean(0)[None], L[-1].mean(0)[None]])
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    a_ = i * m + j
    b_ = i * m + (j + 1) % m
    Qf = np.stack([a_, b_, b_ + m, a_ + m], -1).reshape(-1, 4)
    jj = np.arange(m)
    t0, t1 = n * m, n * m + 1
    C0 = np.stack([np.full(m, t0), (jj + 1) % m, jj], 1)
    C1 = np.stack([np.full(m, t1), (n - 1) * m + jj, (n - 1) * m + (jj + 1) % m], 1)
    # outward: the crest face of the middle station must face along N
    k = (n // 2) * m + int(np.argmax(uo[:, 1]))
    qq = V[[k, k + 1, k + 1 + m, k + m]] if (k % m) < m - 1 else V[[k - 1, k, k + m, k - 1 + m]]
    if float(np.cross(qq[1] - qq[0], qq[3] - qq[0]) @ N[n // 2]) < 0:
        Qf, C0, C1 = Qf[:, ::-1], C0[:, ::-1], C1[:, ::-1]
    acc.add(V, [Qf, C0, C1], "M_thatch", wear=0.45)
    return Cl, em, ew, r


def _corner_close(g, main, wing, sgm, sgw, name, clear=0.35, into=0.12, past=-0.05, t=0.035, n=8, corner_r=0.25,
                  cut=0.13, roll=None):
    """kit 1.19 r2 / r3: the RE-ENTRANT EAVE CORNER of a valley (two eaves at one height meeting inside an L / T):
    (1) every rafter tail of either roof within `clear` m of the other roof's plan columns is dropped WHOLE (no
    clipped, open-ended box under the corner); (2) a BOARDED SOFFIT FILL closes the corner from below: one closed
    board slab over the plan square between the two wall faces and the two lips (`into` m on into the walls, ending
    `past` m from the lips, under the roll bodies).  r3: the slab runs from 1.5 cm under the lower deck underside up
    to just over the HIGHER deck top, so the two decks' cut board ends where they cross are buried in it (no X of
    boards); (3) r3, in place of the r2 ball knot: ONE swept internal-corner roll (_corner_roll, fillet radius
    corner_r) -- the two straight eave rolls are cut back `cut` m from its tangent points (their open ends lie inside
    it), so the eave roll visibly runs round the corner.
    -> <P>_<name> (M_timber slab), <P>_<name>_roll (M_thatch); returns rafter units dropped."""
    import bpy
    from .composite import drop_units
    dropped = 0
    for r, other in ((main, wing), (wing, main)):
        ob = bpy.data.objects.get(f"{g.prefix}_{r.name}_rafters")
        if ob is not None and len(ob.data.polygons):
            dropped += drop_units(ob, lambda V, o=other: _plan_cols(o, V, pad=clear), rule="any")
    um = sgm * np.linspace(main.half - into, main.Y + past, n)
    uw = sgw * np.linspace(wing.half - into, wing.Y + past, n)
    G = np.array([[_plan_meet(main, wing, a, b) for b in uw] for a in um])        # (n, n, 2)
    flat = G.reshape(-1, 2)
    zb = np.minimum(main.under_z_world(flat), wing.under_z_world(flat)) - 0.015
    zt = np.maximum(main.under_z_world(flat) + main.deck_t / math.cos(main.p),
                    wing.under_z_world(flat) + wing.deck_t / math.cos(wing.p)) + 0.005
    top = np.column_stack([flat, zt])
    bot = np.column_stack([flat, zb])
    V = np.vstack([top, bot])
    nm = n * n
    idx = np.arange(nm).reshape(n, n)
    q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    # the top must face up (+z): test the first quad
    c = np.cross(V[q[0, 1]] - V[q[0, 0]], V[q[0, 3]] - V[q[0, 0]])
    if c[2] < 0:
        q = q[:, ::-1]
    rim = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
    side = np.stack([rim, np.roll(rim, -1), np.roll(rim, -1) + nm, rim + nm], 1)
    cs = np.cross(V[side[0, 1]] - V[side[0, 0]], V[side[0, 3]] - V[side[0, 0]])
    ctr = V[:nm].mean(0)
    if float(cs @ (V[side[0, 0]] - ctr)) < 0:
        side = side[:, ::-1]
    acc = Acc(f"{g.prefix}_{name}", 30)
    acc.add(V, [q, q[:, ::-1] + nm, side], "M_timber", wear=0.55)
    finalize(acc, g.coll, smooth_deg=30.0)
    # r3: the swept internal-corner roll, and the two straight eave rolls cut back inside it
    if getattr(main, "ROLL", None) is None:
        main.eave_roll()
    ak = Acc(f"{g.prefix}_{name}_roll", 70)
    Cl, em, ew, rr = _corner_roll(ak, main, wing, sgm, sgw, r=corner_r, **(roll or {}))  # kit 1.21: roll= options
    finalize(ak, g.coll, smooth_deg=70.0)
    n_cut = 0
    for r, e_along, e_out in ((main, em, ew), (wing, ew, em)):
        ob = bpy.data.objects.get(f"{g.prefix}_{r.name}_eave_roll")
        if ob is None or ob.type != "MESH":
            continue
        T0 = Cl + rr * e_along

        def pred(Cw, T0=T0, ea=e_along, eo=e_out):
            d = Cw[:, :2] - T0[None]
            s = d @ ea
            q = (Cw[:, :2] - Cl[None]) @ eo
            return (s < cut) & (s > -(rr + 1.2)) & (q > -1.0) & (q < 0.5)
        n_cut += _drop_faces(ob, pred)
    log(f"  {name}: corner roll r {rr:.2f} at lip corner ({Cl[0]:+.2f}, {Cl[1]:+.2f}); straight eave rolls cut back "
        f"({n_cut} faces)")
    return dropped


def _cut_ridge_under_arch(g, wing, P, ys, toward, back=0.12):
    """kit 1.19 r2: the wing's ridge roll and comb (and its backing) stop in a CLOSED end under the valley arch:
    both are bisected at the plane `back` m (wing-local x) on the wing side of the arch's crest, the part toward the
    main roof deleted and the cut filled -- no open roll end or comb-stop hole shows past the arch's skirt."""
    import bmesh
    import bpy
    i_c = int(np.argmin(np.abs(ys)))
    xc = float(wing.to_local(P[i_c][None])[0, 0])
    x_cut = xc - toward * float(back)
    o_l = np.array([[x_cut, 0.0, 0.0], [x_cut + toward, 0.0, 0.0]])
    o_w = wing.to_world(o_l)
    no = o_w[1] - o_w[0]
    no[2] = 0.0
    no = no / np.linalg.norm(no)
    co = o_w[0]
    n_cut = 0
    for part in ("ridge", "comb"):
        ob = bpy.data.objects.get(f"{g.prefix}_{wing.name}_{part}")
        if ob is None or ob.type != "MESH" or not len(ob.data.polygons):
            continue
        mw = np.array(ob.matrix_world)
        inv = np.linalg.inv(mw)
        co_l = (inv @ np.append(co, 1.0))[:3]
        no_l = inv[:3, :3].T @ no
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        res = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-5,
                                     plane_co=tuple(co_l), plane_no=tuple(no_l), clear_outer=True)
        cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        if cut:
            hf = bmesh.ops.holes_fill(bm, edges=cut, sides=0)
            # r3: each fill faces OUT of the kept part, along the cut plane's normal (the cleared side)
            nl = np.asarray(no_l, float)
            nl = nl / max(float(np.linalg.norm(nl)), 1e-9)
            for f in hf.get("faces", []):
                f.normal_update()
                if float(np.dot(np.array(f.normal), nl)) < 0:
                    f.normal_flip()
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        n_cut += 1
    return x_cut, n_cut


def _first_cross(fz, x_from, x_to, step=0.02):
    """scan x from x_from toward x_to; the first x where fz(x) < 0, refined (None if it never is)."""
    xs = np.arange(x_from, x_to, step if x_to > x_from else -step)
    if len(xs) < 2:
        return None
    v = np.array([fz(x) for x in xs])
    idx = np.flatnonzero(v < 0)
    if not len(idx) or idx[0] == 0:
        return None
    a, b = xs[idx[0] - 1], xs[idx[0]]
    for _ in range(30):
        mid = 0.5 * (a + b)
        if fz(mid) < 0:
            b = mid
        else:
            a = mid
    return 0.5 * (a + b)


def valley_line(main, wing, dy=0.03, edge=0.004, foot="crest", foot_back=0.0):
    """the junction line (world (n, 3), ordered across the wing from its -y lip to its +y lip) where the wing's
    covering top meets the main roof's top; also returns the wing-local y of each point.  The wing is scanned from
    its free end (the end farther from the main roof's centre) toward the main roof.  foot="crest": the line stops
    just past the crest of the wing's eave roll (the two eave rolls cross under its rounded end; beyond the crest the
    rolls' noses fall away and a section laid there would twist); "lip": it runs on to the lip."""
    cm = main.to_world(np.array([[0.5 * (main.xa + main.xb), 0.0, 0.0]]))[0]
    cl = wing.to_local(np.array([[cm[0], cm[1], 0.0]]))[0]
    toward = 1.0 if cl[0] > 0.5 * (wing.xa + wing.xb) else -1.0
    x_far, x_near = (wing.xa, wing.xb) if toward > 0 else (wing.xb, wing.xa)
    ya, zt, _ = wing.section_columns()
    ok = np.isfinite(zt)
    y_max = float(ya[ok].max()) - edge
    R = getattr(wing, "ROLL", None)
    if foot == "crest" and R is not None:
        y_max = min(y_max, wing.Y - (R["u_c"] + 0.02 + float(foot_back)) * math.cos(wing.p))
    ys = np.unique(np.concatenate([np.arange(-y_max, y_max + 1e-9, dy), [-y_max, y_max]]))
    pts, yy = [], []
    for y in ys:
        zl = float(np.interp(abs(y), ya[ok], zt[ok]))

        def fz(x, y=y, zl=zl):
            W = wing.to_world(np.array([[x, y, zl]]))[0]
            zm = float(top_world(main, W[None])[0])
            return 1.0 if not np.isfinite(zm) else float(W[2]) - zm
        x = _first_cross(fz, x_far, x_near)
        if x is None:
            continue
        pts.append(wing.to_world(np.array([[x, y, zl]]))[0])
        yy.append(y)
    return np.array(pts), np.array(yy)


def roof_valley(g, main, wing, name=None, width=(0.34, 0.34), crown=0.16, bury=(0.10, 0.10), dy=0.03,
                comb_clear=0.22, var=0.06, seed=0, taper=0.30, end_out=0.16, smooth=2, foot="crest", corner="auto",
                ridge_cut=0.12, sink=0.06, ridge_bury=0.12, ridge_bury_w=0.35, foot_back=None, corner_opts=None):
    """KIT COMPONENT (kit 1.19, v7): the rolled thatch valley where `wing` runs into `main` (both GableRoofs built by
    linear_roof; see the module doc).  Build the two roofs first with linear_roof(clip=solid_clip(other),
    deck_clip=deck_clip(other)) so the coverings and decks yield to each other at the valley; this then sweeps the
    roll on the true top-to-top line (valley_line) with each skirt `width` out on its own covering (main, wing),
    `bury` under it, the crest `crown` over the crease, and drops the wing's comb units within comb_clear m of the
    main roof's top (they would stand through the roll).  -> <P>_<name> (M_thatch); records g.VALLEYS.
    kit 1.19 r2: the skirt directions are continuous along the line (no twisted section at the foot), the normals
    are smoothed (no folded lip over a ridge roll), each end is a rounded tuck (end_out past the end, diving `sink`
    under the bisector); ridge_cut (m, None = off): the wing's ridge roll and comb end CLOSED that far on the wing
    side of the arch's crest (_cut_ridge_under_arch); corner="auto" (eaves within 0.3 m of one height) / True /
    False: each foot at a re-entrant eave corner gets _corner_close (rafter tails dropped, boarded soffit fill).
    kit 1.19 r3: _corner_close sweeps ONE internal-corner roll round each re-entrant corner (no ball knot) and buries
    the crossing deck ends in the soffit fill; at such a corner each foot tuck runs on >= 0.26 m and sinks by the
    crown + 8 cm into that roll; ridge_bury (m, 0 = off) / ridge_bury_w: both skirts bury that much deeper where the
    line crosses the wing's ridge roll (|wing y| < ridge_bury_w, fading), and the ridge cut's fill faces are oriented
    outward (no dark wedge either side of the comb).
    kit 1.21 (v7 r5; None = old): corner_opts -- keywords for each _corner_close (corner_r, cut, and roll=dict(ext=,
    blend=, grow=, end_f=) for the swept internal-corner roll's long smoothstep overlap into the straight rolls).
    A NEGATIVE ridge_cut ends the wing's ridge roll that far PAST the arch's crest, inside the main covering (a
    roof without a comb: the roll end is buried in the main thatch, no cut end or pocket under the arch)."""
    from .composite import drop_units
    import bpy
    name = name or f"{wing.name}_valley"
    same = abs(float(main.z_lip) - float(wing.z_lip)) < 0.3
    closing = foot == "crest" and (corner is True or (corner == "auto" and same))
    if foot_back is None:                    # r3: at a closed corner the line stops short of the roll's round nose
        foot_back = 0.22 if closing else 0.0
    P, ys = valley_line(main, wing, dy=dy, foot=foot, foot_back=foot_back)
    if len(P) < 6:
        raise ValueError(f"roof_valley: {wing.name} does not meet {main.name} (no valley line)")
    for _ in range(smooth):                                     # a calm line (the column table is stepped)
        P[1:-1] = 0.25 * P[:-2] + 0.5 * P[1:-1] + 0.25 * P[2:]
    zm = top_world(main, P)
    P[:, 2] = np.maximum(zm, top_world(wing, P))
    nA, nB = _smooth_rows(top_normal(main, P)), _smooth_rows(top_normal(wing, P))
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    T = _unit(T)
    a = _unit(np.cross(nA, T))
    b = _unit(np.cross(nB, T))
    # orient: along main AWAY from the crease is where main is the higher of the two tops (a valley is their max);
    # the per-station wishes are only votes -- the directions stay continuous along the line
    wa, wb = a.copy(), b.copy()
    for i in range(len(P)):
        q = P[i, :2] + a[i, :2] * 0.25
        if top_world(main, q[None])[0] < top_world(wing, q[None])[0]:
            wa[i] = -a[i]
        q = P[i, :2] + b[i, :2] * 0.25
        if top_world(wing, q[None])[0] < top_world(main, q[None])[0]:
            wb[i] = -b[i]
    a, b = _smooth_rows(_continuous(a, wa), 2), _smooth_rows(_continuous(b, wb), 2)
    if closing:
        # r3: each foot dives INTO the internal-corner roll (_corner_close): a longer tuck sinking by more than the
        # roll's own crown, so no folded flap or dark lip is left in the open at the eave
        sink = max(float(np.max(sink)), float(crown) + 0.08)
        end_out = max(float(np.max(end_out)), 0.26)
    # r3: over the wing's ridge roll (|ys| < ridge_bury_w) both skirts bury deeper and the wing skirt is steered
    # onto the roll's own axis (away from main, square to the line), so it lies down the ridge roll -- no lifted,
    # folded skirt end (dark wedge) either side of the comb
    rb = 0.0
    if ridge_bury:
        wgt = np.clip(1.0 - np.abs(ys) / float(ridge_bury_w), 0, 1)[:, None]
        rb = float(ridge_bury) * wgt
        cm_ = main.to_world(np.array([[0.5 * (main.xa + main.xb), 0.0, 0.0]]))[0]
        tw_ = 1.0 if wing.to_local(np.array([[cm_[0], cm_[1], 0.0]]))[0, 0] > 0.5 * (wing.xa + wing.xb) else -1.0
        bx = -tw_ * np.asarray(wing.dir_world(np.array([1.0, 0.0, 0.0])), float)
        bx = _unit(bx[None] - (bx[None] * T).sum(1, keepdims=True) * T)
        b = _unit((1 - wgt) * b + wgt * bx)
        # the wing skirt's end dives VERTICALLY over the ridge roll (a radial dive folds it back: the dark wedges)
        dB = _unit((1 - wgt) * nB + wgt * np.array([[0.0, 0.0, 1.0]]))
    else:
        dB = None
    bur = (bury[0] + rb, bury[1] + rb)
    acc = Acc(f"{g.prefix}_{name}", 70)
    length = _crease_roll(acc, P, nA, nB, a, b, width=width, crown=crown, bury=bur, var=var, seed=seed + 7,
                          taper=taper, end_out=end_out, sink=sink, bury_dir=(None, dB))
    ob = finalize(acc, g.coll, smooth_deg=70.0)
    dropped = 0
    cb = bpy.data.objects.get(f"{g.prefix}_{wing.name}_comb")
    if cb is not None and comb_clear:
        dropped = drop_units(cb, lambda V: main.top_depth(V) > -float(comb_clear), rule="any")
    # the wing's side toward the main roof (wing-local x)
    cm = main.to_world(np.array([[0.5 * (main.xa + main.xb), 0.0, 0.0]]))[0]
    toward = 1.0 if wing.to_local(np.array([[cm[0], cm[1], 0.0]]))[0, 0] > 0.5 * (wing.xa + wing.xb) else -1.0
    msg = ""
    if ridge_cut and float(np.abs(ys).min()) < 0.1:
        x_cut, n_cut = _cut_ridge_under_arch(g, wing, P, ys, toward, back=ridge_cut)
        msg += f"; ridge / comb closed at wing x {x_cut:+.2f} ({n_cut} parts)"
    if closing:
        wc = wing.to_world(np.array([[0.5 * (wing.xa + wing.xb), 0.0, 0.0]]))
        sgm = -1.0 if float(main.to_local(wc)[0, 1]) < 0 else 1.0
        nd = 0
        for k, sgw in enumerate((-1.0, 1.0)):
            nd += _corner_close(g, main, wing, sgm, sgw, f"{name}_soffit_{k}", **(corner_opts or {}))
        msg += f"; re-entrant corners closed (soffit fills, {nd} rafter polygons dropped)"
    if not hasattr(g, "VALLEYS"):
        g.VALLEYS = []
    g.VALLEYS.append(dict(main=main.name, wing=wing.name, P=P, name=name))
    log(f"  {name}: valley roll {len(P)} stations, {length:.2f} m (z {P[:, 2].min():.2f}..{P[:, 2].max():.2f}), "
        f"wing y {ys.min():+.2f}..{ys.max():+.2f}; comb polygons dropped {dropped}" + msg)
    return ob


# =================================================================================================================
# the gabled dormer
# =================================================================================================================
DORMER_SOFT = dict(ridge_sag=0.03, eave_sag=0.0, eave_sweep=0.08, sweep_len=0.45, verge_flare=0.10, flare_len=0.7,
                   wave=0.008, ridge_seat=True)
"""the dormer roof's soft options (GableRoof keywords; note 17: the small roof sags and sweeps like its host).
kit 1.19 r2: ridge_seat=True (as its host) -- the ridge roll is seated on the top course (no dark slot under it)."""


def dormer_verge_roll(hw, rc=None, apex_bend=None, bend_over=None, **kw):
    """kit 1.19 r2: the dormer hood's PATH (linear_roof(verge_roll=...)) scaled to the dormer: rc is the radius of
    the hood's EAVE-CORNER FILLET in the slope plane (not the roll's section), apex_bend the radius of the bend over
    the apex: rc = 0.18 * hw, apex_bend = 0.155 * hw, bend_over = 0.12 * hw by default, a recipe's rc / apex_bend
    capped at 0.20 * hw / 0.17 * hw.  The roll's SECTION (its fatness) is the dormer roof's eave roll:
    GabledDormer(roll=...) -> linear_roof(eave_roll=...), radius 0.15 * hw on a thin dormer thatch (kit 1.19 r3)."""
    cap_rc, cap_ab = 0.20 * hw, 0.17 * hw
    out = dict(kw)
    out["rc"] = min(float(rc if rc is not None else 0.18 * hw), cap_rc)
    out["apex_bend"] = min(float(apex_bend if apex_bend is not None else 0.155 * hw), cap_ab)
    out["bend_over"] = float(bend_over if bend_over is not None else 0.12 * hw)
    if (rc is not None and rc > cap_rc) or (apex_bend is not None and apex_bend > cap_ab):
        log(f"  dormer hood capped to the dormer: rc {rc} -> {out['rc']:.3f}, apex_bend {apex_bend} -> "
            f"{out['apex_bend']:.3f} (half width {hw:.2f})")
    return out


class GabledDormer:
    """kit 1.19 (v7): the spec of a gabled dormer on a GableRoof `main` (pure geometry, no meshes).
    x        centre along the host ridge (host local x)
    side     -1 / +1: the host slope (host local -y / +y)
    d        plan distance (m) in from the host's wall face (half) to the dormer's front frame face; >= 0.3 so the
             dormer's sill and cheek feet stand inside the building (under the host roof)
    width    the dormer's width at its cheek frame faces (its roof's `half` = width / 2)
    pitch, overhang, verge, thick, step   the dormer roof (GableRoof keywords)
    window   kit window keys (components.openings.window, timber family): width / height / sill (clear sill above
             the dormer's sill-beam top); the sill is raised, with a log line, until it clears the host thatch
    plate_gap  the dormer roof's reference height over its wall plate top
    soft     the dormer roof's soft options (DORMER_SOFT)
    back_run plan metres the cheeks run on past the point where their head meets the host deck (buried)"""

    def __init__(self, main, x, side=-1, d=0.55, width=1.30, pitch=50.0, overhang=0.22, verge=0.28, thick=0.13,
                 step=0.05, window=None, plate_gap=0.10, soft=None, back_run=0.30, name="dormer", sill_beam=0.18,
                 z0_drop=0.06, clear_thatch=0.06, head=0.16, roll=None, deck_t=0.025):
        from .linear_roof import GableRoof
        self.main, self.name = main, name
        self.x, self.sg = float(x), (1 if side > 0 else -1)
        self.hw = 0.5 * float(width)
        # kit 1.19 r3: the dormer's eave / hood roll SECTION scaled to the dormer (linear_roof(eave_roll=...)): radius
        # 0.15 * hw, a thin dormer thatch (thick / step / deck_t) and a low crest, so the hood's section is about a
        # fifth of the dormer's width or less (the host's 0.16 m roll on a 0.28 m thatch read as a "pretzel" knot)
        self.roll = dict(radius=0.15 * self.hw, proud=0.02, drop=0.015)
        self.roll.update(roll or {})
        self.win = dict(width=0.55, height=0.50, sill=0.30)
        self.win.update(window or {})
        sg, hw = self.sg, self.hw
        self.y_f = sg * (main.half - float(d))                       # host local y of the front frame face
        xs = np.linspace(self.x - hw, self.x + hw, 21)
        yf = np.full(len(xs), self.y_f)
        ref = main.ref_z(yf) + main.warp_z(xs, yf)
        self.z0 = float(ref.min()) - float(z0_drop)                  # the sill beam's foot (under the host deck)
        self.floor = self.z0 + float(sill_beam)
        Pf = main.to_world(np.stack([xs, np.full(len(xs), self.y_f + sg * 0.06), np.zeros(len(xs))], 1))
        z_th = float(top_world(main, Pf).max()) + main.step + 0.03   # the host thatch's butt peaks just in front
        need = z_th + float(clear_thatch) - self.floor
        if self.win["sill"] < need:
            log(f"  {name}: window sill raised {self.win['sill']:.2f} -> {need:.2f} m (clears the host thatch)")
            self.win["sill"] = float(need)
        self.plate = self.floor + self.win["sill"] + self.win["height"] + float(head) + 0.06
        self.wall_z = self.plate + float(plate_gap)
        # the cheeks' back end: where their head (wall_z) meets the host deck, + back_run (host local y)
        tp = math.tan(main.p)
        u_y = main.Y - (self.wall_z - main.z_lip) / tp                # |y| where the host's straight ref = wall_z
        self.y_back = sg * max(0.0, u_y - float(back_run) - 0.15)
        o = main.to_world(np.array([[self.x, 0.0, 0.0]]))[0]
        kw = dict(DORMER_SOFT if soft is None else soft)
        x0, x1 = (self.y_f, 0.0) if sg < 0 else (0.0, self.y_f)
        vg = (float(verge), 0.0) if sg < 0 else (0.0, float(verge))
        self.roof = GableRoof(x0=x0, x1=x1, half=hw, wall_z=self.wall_z, pitch_deg=pitch, overhang=overhang,
                              verge=vg, origin=(float(o[0]), float(o[1])),
                              yaw_deg=math.degrees(main.yaw) + 90.0, thick=thick, step=step, deck_t=deck_t,
                              ridge_roll=(0.26, 0.15), name=f"{name}_roof", **kw)
        r = self.roof
        top_d = r.z_ridge + (r.T0 + r.step) / math.cos(r.p) + r.roll_h + 0.05
        zm = float(top_world(main, main.to_world(np.array([[self.x, 0.6 * self.y_back + 0.4 * self.y_f, 0.0]])))[0])
        log(f"  {name}: front y {self.y_f:+.2f} (host local), sill-beam foot {self.z0:.2f}, floor {self.floor:.2f}, "
            f"plate {self.plate:.2f}, roof wall_z {self.wall_z:.2f}, ridge {r.z_ridge:.2f} (top ~{top_d:.2f}), "
            f"cheeks back to y {self.y_back:+.2f}")
        if top_d > float(main.z_ridge) + (main.T0 + 0.45 * main.step) / math.cos(main.p) - 0.15:
            raise ValueError(f"{name}: the dormer ridge ({top_d:.2f}) comes within 0.15 m of the host ridge; lower the "
                             f"window, d or the pitch")
        del zm

    # host-local helpers --------------------------------------------------------------------------------------------
    def _in_box(self, V, pad=0.02):
        L = self.main.to_local(np.asarray(V, float))
        lo, hi = sorted((self.y_f + self.sg * pad, self.y_back))
        return (np.abs(L[:, 0] - self.x) < self.hw - pad) & (L[:, 1] > lo) & (L[:, 1] < hi)

    def clip_main(self):
        """the host covering's clip: inside the dormer's walls (between the cheeks, behind the front) below the
        dormer roof's top, or inside the dormer roof's solid (never under its eaves: the host thatch is the floor of
        the little eave pocket there)."""
        sol = solid_clip(self.roof, under=False)

        def clip(V, margin=0.0):
            V = np.asarray(V, float)
            zt = top_world(self.roof, V)
            return (self._in_box(V) & (V[:, 2] < zt - margin)) | sol(V, margin)
        return clip

    def deck_clip_main(self):
        """the host deck's clip: inside the dormer's walls under the dormer's deck (the dormer's dark room sits there)."""
        def clip(V, margin=0.0):
            V = np.asarray(V, float)
            L = self.roof.to_local(V)
            under = L[:, 2] < self.roof.ref_z(L[:, 1])
            return self._in_box(V, pad=0.05) & under
        return clip

    def path(self):
        """the walls' plan path (world), interior on the left: cheek, front, cheek."""
        sg, x, hw = self.sg, self.x, self.hw
        if sg < 0:
            loc = [(x - hw, self.y_back), (x - hw, self.y_f), (x + hw, self.y_f), (x + hw, self.y_back)]
        else:
            loc = [(x + hw, self.y_back), (x + hw, self.y_f), (x - hw, self.y_f), (x - hw, self.y_back)]
        W = self.main.to_world(np.array([[p[0], p[1], 0.0] for p in loc]))
        return [(float(w[0]), float(w[1])) for w in W]


def _foot_path(D, w_face=0.03, rc=0.12, ds=0.03):
    """the dormer walls' foot line in plan (world): along the outer board face (w_face out of the frame face) of the
    cheek, the front and the other cheek, the two front corners rounded (radius rc, so the roll wraps them);
    returns points (n, 2) and outward normals (n, 2)."""
    pts = np.array(D.path())
    out = []
    nrm = []
    segs = []
    for i in range(len(pts) - 1):
        d = pts[i + 1] - pts[i]
        L = float(np.linalg.norm(d))
        t = d / L
        nn = np.array([t[1], -t[0]])                              # outward = right of the walking direction
        segs.append((pts[i] + nn * w_face, t, nn, L))
    # straight parts shortened by the corner arcs
    for k, (p0, t, nn, L) in enumerate(segs):
        a0 = rc if k > 0 else 0.0
        a1 = rc if k < len(segs) - 1 else 0.0
        s = np.arange(a0, L - a1 + 1e-9, ds)
        out.append(p0[None] + t[None] * s[:, None])
        nrm.append(np.repeat(nn[None], len(s), 0))
        if k < len(segs) - 1:                                     # the convex corner arc to the next run
            p1, t1, n1, _ = segs[k + 1]
            # centre of the arc: inside the corner, rc from both faces
            ctr = p0 + t * (L - rc) - nn * rc
            a_s = math.atan2(nn[1], nn[0])
            a_e = math.atan2(n1[1], n1[0])
            da = (a_e - a_s + math.pi) % (2 * math.pi) - math.pi
            na = max(3, int(abs(da) * rc / ds) + 1)
            ang = a_s + da * np.linspace(0, 1, na)[1:-1]
            out.append(ctr[None] + rc * np.stack([np.cos(ang), np.sin(ang)], 1))
            nrm.append(np.stack([np.cos(ang), np.sin(ang)], 1))
    return np.concatenate(out), np.concatenate(nrm)


def _dormer_foot_roll(g, D, width=(0.24, 0.20), crown=0.12, bury=(0.09, 0.035), seed=0, under_eave=0.16,
                      taper=0.40, sink=0.10):
    """the rolled thatch foot round the dormer: where the host thatch top meets the cheek / front boards.
    kit 1.19 r2: it stops `under_eave` m under the dormer's eave soffit and tapers over `taper` m into a tuck that
    dives `sink` m into the host thatch, so each end dies under the dormer valley's skirt instead of crossing it."""
    main, r = D.main, D.roof
    Q, Nn = _foot_path(D)
    z = top_world(main, Q)
    zs = r.under_z_world(Q) - under_eave                         # stop under the dormer's eave soffit
    ok = np.isfinite(z) & (z < zs)
    idx = np.flatnonzero(ok)
    if len(idx) < 6:
        log(f"  {D.name}: no foot roll (the host thatch never meets the walls)")
        return None
    # the longest contiguous run
    runs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    idx = max(runs, key=len)
    P = np.column_stack([Q[idx], z[idx]])
    nb = np.column_stack([Nn[idx], np.zeros(len(idx))])
    na = top_normal(main, P)
    a = _unit(nb - (nb * na).sum(1, keepdims=True) * na)          # down the host slope, away from the wall
    up = np.array([0.0, 0.0, 1.0])
    b = np.repeat(up[None], len(P), 0)
    acc = Acc(f"{g.prefix}_{D.name}_foot_roll", 70)
    L = _crease_roll(acc, P, na, nb, a, b, width=width, crown=crown, bury=bury, var=0.05, seed=seed + 3,
                     taper=taper, end_out=0.10, sink=sink)
    finalize(acc, g.coll, smooth_deg=70.0)
    log(f"  {D.name}: foot roll {len(P)} stations, {L:.2f} m")
    return L


def gabled_dormer(g, D, seed=81, covering="thatch", finial=True, foot_roll=True, valley=None, walls=None,
                  verge_roll="auto"):
    """KIT COMPONENT (kit 1.19, v7): build the gabled dormer `D` (GabledDormer) after its host roof D.main (built
    with linear_roof(clip=any_clip(..., D.clip_main()), deck_clip=any_clip(..., D.deck_clip_main()))).  Steps:
    the walls (timber_walls.path_timber_wall: board_batten front and cheeks, rough, from the sill-beam foot under the
    host deck to the dormer roof; the kit window centred in the front), the roof (linear_roof, `covering`, yielding
    to the host: clip / deck_clip; finial=True puts the village's lead hat and turned finial on its front apex), the
    valley into the host (roof_valley, kwargs `valley`) and the foot roll round the walls (foot_roll).
    walls: extra path_timber_wall keywords; verge_roll: linear_roof(verge_roll=...) for the dormer's front verge
    (the rolled rake of kit 1.17 / 1.18, one free verge: kit 1.19); None = the plain verge face.
    kit 1.19 r2: verge_roll="auto" (default) = the hood scaled to the dormer (dormer_verge_roll(D.hw)); a dict is
    passed through dormer_verge_roll too, so its rc / apex_bend are capped to the dormer's width."""
    from .linear_roof import linear_roof
    from .openings import window as _window
    from .timber_walls import path_timber_wall, roof_top_fn
    if covering != "thatch":
        raise ValueError("gabled_dormer: covering='thatch' only in kit 1.19 (the shingle valley is not built yet)")
    path = D.path()
    pa = np.array(path)
    L_ch = float(np.linalg.norm(pa[1] - pa[0]))
    wk = dict(D.win)
    ww, wh, ws = wk.pop("width"), wk.pop("height"), wk.pop("sill")
    wk.setdefault("shutters", False)
    wk.setdefault("room", 0.30)
    wk.setdefault("room_pad", (0.05, 0.10, 0.04))
    WIN = _window(width=ww, height=wh, sill=ws, **wk)
    kw = dict(style="board_batten", gable_style="board_batten", rough=True, bow=0.015, seed=seed + 300)
    kw.update(walls or {})
    path_timber_wall(g, name=f"{D.name}_walls", path=path, z0=D.z0, top=D.plate, top_fn=roof_top_fn(D.roof),
                     openings=[(L_ch + D.hw, WIN)], **kw)
    if isinstance(verge_roll, str) and verge_roll == "auto":
        verge_roll = dormer_verge_roll(D.hw)
    elif isinstance(verge_roll, dict):
        verge_roll = dormer_verge_roll(D.hw, **verge_roll)
    linear_roof(g, D.roof, covering="thatch", clip=solid_clip(D.main, under=True), deck_clip=deck_clip(D.main),
                seed=seed, ridge_caps=True, verge_apex=True, apex_finial="turned" if finial else None,
                comb_step=0.75, comb_backing=True, verge_roll=verge_roll, eave_roll=D.roll)
    vk = dict(width=(0.26, 0.24), crown=0.13, bury=(0.09, 0.08), comb_clear=0.18, seed=seed)
    vk.update(valley or {})
    roof_valley(g, D.main, D.roof, name=f"{D.name}_valley", **vk)
    if foot_roll:
        _dormer_foot_roll(g, D, seed=seed)
    if not hasattr(g, "DORMERS"):
        g.DORMERS = []
    g.DORMERS.append(dict(name=D.name, x=D.x, side=D.sg, y_f=D.y_f, wall_z=D.wall_z))
    return D


# =================================================================================================================
# the chimney
# =================================================================================================================
CHIMNEY_CAP = dict(drip=0.07, h=0.15, inset=0.17, wobble=0.012)
"""the dressed drip-course cap on the stack head: drip = how far it oversails the stack face, h = its height,
inset = the flue's wall thickness (flue radius = head radius - inset), wobble = +-m of soft out-of-round."""


def _ring_trace(bvh, T, step_deg=1.0, z_guess=3.0, offsets=(0.006, 0.02)):
    """a CLOSED roof-top / stack-face line (the roof surrounds the stack): like junctions.trace_roof_on_tower but
    every azimuth must hit; returns [(theta (n,), P (n, 3))] with the ring closed by a 20 deg overlap."""
    from .junctions import _down
    C = np.asarray(T["center"], float)
    th = np.radians(np.arange(0.0, 360.0, step_deg))
    Z = np.full(len(th), np.nan)
    for i, t in enumerate(th):
        d = np.array([math.cos(t), math.sin(t)])
        z = z_guess
        for _ in range(3):
            hs = [h for off in offsets
                  if (h := _down(bvh, C[0] + d[0] * (float(T["R"](z)) + off),
                                 C[1] + d[1] * (float(T["R"](z)) + off))) is not None]
            if not hs:
                break
            z = max(hs)
        else:
            Z[i] = z
    ok = np.isfinite(Z)

    log(f"  ring trace: {int(ok.sum())} / {len(Z)} azimuths hit the roof top"
        + (f", z {np.nanmin(Z):.2f}..{np.nanmax(Z):.2f}" if ok.any() else ""))
    if ok.mean() < 0.85:                                     # the roof does not surround the stack
        return None
    if not ok.all():                                         # rays slipping through a course joint: close the gaps
        Z = np.interp(th, th[ok], Z[ok], period=2 * math.pi)
    k = int(round(20.0 / step_deg))
    th2 = np.concatenate([th, th[:k] + 2 * math.pi])
    Z2 = np.concatenate([Z, Z[:k]])
    rr = np.array([float(T["R"](z_)) for z_ in Z2])
    P = np.stack([C[0] + rr * np.cos(th2), C[1] + rr * np.sin(th2), Z2], 1)
    return [(th2, P)]


def _ring_abutment(g, roof, center, radius, name, parts, fillet=None):
    """the roof surrounds the stack (a chimney through the slope or the ridge): trim the roof at the stack face and
    run the lime-mortar flaunching (junctions.ride_fillet) round the whole ring (closed by an overlap)."""
    import bpy
    from .junctions import _bvh, _smooth_up, clip_at_tower, ride_fillet
    C = np.asarray(center, float)[:2]
    T = dict(center=C, R=lambda z, f=radius: np.asarray(f(np.asarray(z, float)), float), name="stack")
    pre = f"{g.prefix}_{roof.name}"
    for part, depth in parts:
        ob = bpy.data.objects.get(f"{pre}_{part}")
        if ob is not None and ob.type == "MESH":
            clip_at_tower(ob, T, inset=float(depth))
    objs = [o for o in (bpy.data.objects.get(f"{pre}_{p}") for p in ("covering", "eave_roll", "ridge", "comb"))
            if o is not None and len(o.data.polygons)]
    bvh = _bvh(objs)
    fk = dict(h_up=0.12, out=0.12, lift=0.05, bury=0.035, taper=0.15)      # kit 1.20: fillet= overrides
    fk.update(fillet or {})
    step = float(fk.pop("step_deg", 1.0))                                  # kit 1.20: ring sampling (deg)
    runs = _ring_trace(bvh, T, step_deg=step, z_guess=float(roof.z_lip))   # low: the battered face is widest (r2 fix)
    if not runs:
        raise ValueError(f"chimney {name}: the roof does not surround the stack (use the gable placement)")
    acc = Acc(f"{pre}_{name}", 35)
    for th, P in runs:
        ride_fillet(acc, th, _smooth_up(P[:, 2]), T, bvh, **fk)
    log(f"  {name}: ring flaunching round the stack, {len(runs[0][0])} samples, z {runs[0][1][:, 2].min():.2f}.."
        f"{runs[0][1][:, 2].max():.2f}")
    ob = finalize(acc, g.coll, smooth_deg=35.0)
    # kit 1.19 r2: registered for the seal-probe guard like wall_abutment (the ring is the whole junction)
    from ..guards import register_junction
    zs = runs[0][1][:, 2]
    register_junction(g, f"{roof.name} / stack ring", (f"{pre}_covering", f"{pre}_eave_roll", f"{pre}_ridge"), C,
                      lambda z, f=radius: float(np.asarray(f(np.asarray(z, float)), float)),
                      (float(zs.min()) - 0.3, float(zs.max()) + 0.3))
    return ob


def chimney(g, name="chimney", center=(0.0, 0.0), r_base=0.62, batter_deg=2.0, top=None, roof=None,
            over_ridge=0.85, clip=None, cfg=None, seed=51, crown="pot", cap=None, parts=None, louvre=None,
            pot=None, abut=None, shoulder=None):
    """KIT COMPONENT (kit 1.19, v7): a round rubble chimney stack (see the module doc).
    center, r_base, batter_deg   the stack's axis (plan), face radius at the ground and batter (the village's
                 battered round rubble: rubble_walls.round_stone_body; cfg = its RUBBLE_CFG overrides, None = the village rubble)
    top          the stack head (absolute z); None = `over_ridge` m over the highest roof top within the stack's
                 radius (or the ridge of `roof`)
    roof         a built GableRoof the stack stands in / against: its parts are trimmed at the stack face and the
                 junction is flaunched -- roof_junction.wall_abutment (mortar on the true line, lead end aprons) when
                 the roof meets only part of the stack (a gable-end stack), a closed ring of flaunching when the roof
                 surrounds it (through a slope or the ridge).  abut: extra wall_abutment keywords
    clip         clip(P) -> bool: stack stones inside another body are dropped (the house's interior)
    shoulder     None (one battered stack) or dict(z, r_base, batter_deg, h): a BROAD BASE (r_base / batter_deg above)
                 up to z, a weathered offset (a rounded dressed-stone weathering `h` m high, the soft shoulder) and the
                 narrower upper stack (its own r_base at the ground and batter) from there to the head
    crown        "pot" (default, kit 1.19 r2: a round dressed-stone pot, `pot` = dict(r, h)) or "louvre" (opt-in: a
                 low round smoke louvre, `louvre` = dict(n posts, h <= 0.3 m, ring, hat pitch, finial scale -- None =
                 no finial, the default) under a little lead cone; producer note 23:12: no lantern / cupola read)
    -> <P>_<name>_stones / _mortar (stack), _cap (M_stone_dressed), _flue_blocker (dark flue), _crown (posts or pot),
       _cap_collar (the lead cone), _finial; the roof's <P>_<roof>_<name>_abutment.  Records g.CHIMNEYS."""
    from .rubble_walls import round_stone_body
    from .roof_junction import LINEAR_ROOF_PARTS, wall_abutment
    from ..geom import lathe_rz, obox
    from .finial import lead_hat, turned_finial
    C = np.asarray(center, float)[:2]
    tb = math.tan(math.radians(batter_deg))
    if top is None:
        if roof is None:
            raise ValueError("chimney: give top= or roof=")
        ang = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        ring = C[None] + 0.9 * r_base * np.stack([np.cos(ang), np.sin(ang)], 1)
        zt = top_world(roof, np.vstack([C[None], ring]))
        z_r = float(np.max(zt[np.isfinite(zt)])) if np.isfinite(zt).any() else float(roof.z_ridge) + 0.5
        top = max(z_r, float(roof.z_ridge) + roof.T0 / math.cos(roof.p) + roof.roll_h) + float(over_ridge)
    top = float(top)
    cxy = (float(C[0]), float(C[1]))
    if shoulder:
        sk = dict(z=3.6, r_base=0.70, batter_deg=1.5, h=0.28)
        sk.update(shoulder)
        z_sh = float(sk["z"])
        round_stone_body(g, f"{name}_base", center=cxy, r_base=r_base, batter_deg=batter_deg, top=z_sh, clip=clip,
                         cfg=cfg, seed=seed + 1)
        r_low, r_b0 = r_base - z_sh * tb, r_base
        r_base, batter_deg = float(sk["r_base"]), float(sk["batter_deg"])
        tb = math.tan(math.radians(batter_deg))
        r_up = r_base - z_sh * tb
        below = (lambda P, m=0.0: np.asarray(P, float)[:, 2] < z_sh - 0.06)
        clip_up = below if clip is None else (lambda P, m=0.0: clip(P) | below(P))
        round_stone_body(g, name, center=cxy, r_base=r_base, batter_deg=batter_deg, top=top, clip=clip_up, cfg=cfg,
                         seed=seed)
        # the weathered offset: a rounded dressed-stone weathering from the broad base's head onto the stack
        h_s = float(sk["h"])
        prof = [(r_up - 0.12, z_sh - 0.05), (r_low + 0.02, z_sh - 0.05), (r_low + 0.045, z_sh - 0.01),
                (r_low + 0.03, z_sh + 0.03), (r_low - 0.04, z_sh + 0.07), (0.5 * (r_low + r_up), z_sh + 0.55 * h_s),
                (r_up + 0.025, z_sh + h_s), (r_up - 0.12, z_sh + h_s)]
        Vw, Fw = lathe_rz(prof, 40, cx=0.0, cy=0.0, z0=0.0, cap_bottom=False, cap_top=False)
        nrw, aw = len(prof), np.arange(40)
        ew = np.stack([(nrw - 1) * 40 + aw, (nrw - 1) * 40 + (aw + 1) % 40, (aw + 1) % 40, aw], 1)
        phw = np.arctan2(Vw[:, 1], Vw[:, 0])
        Vw[:, :2] *= (1.0 + 0.015 * np.sin(3 * phw + 0.7))[:, None]
        Vw[:, 0] += C[0]
        Vw[:, 1] += C[1]
        aw_ = Acc(f"{g.prefix}_{name}_weathering", 40)
        aw_.add(Vw, list(Fw) + [ew], "M_stone_dressed", wear=0.6)
        finalize(aw_, g.coll, smooth_deg=40.0)
        log(f"  {name}: broad base r {r_b0:.2f}.. head {r_low:.2f} to z {z_sh:.2f}, weathered offset to the stack "
            f"(r {r_up:.2f})")
    else:
        round_stone_body(g, name, center=cxy, r_base=r_base, batter_deg=batter_deg, top=top, clip=clip, cfg=cfg,
                         seed=seed)
    stack_R = (lambda z, rb=r_base, t_=tb: rb - np.clip(np.asarray(z, float), 0, None) * t_)
    if roof is not None:
        prt = parts or (LINEAR_ROOF_PARTS + (("verge", 0.02),))
        kw = dict(abut or {})
        ring_fillet = kw.pop("ring_fillet", None)          # kit 1.20: the ring flaunching's ride_fillet keywords
        kw.setdefault("radius", stack_R)
        try:
            wall_abutment(g, roof, center=cxy, parts=prt, name=f"{name}_abutment", **kw)
        except ValueError as ex:
            if "covers the whole tower" not in str(ex):
                raise
            _ring_abutment(g, roof, C, kw["radius"], f"{name}_abutment", prt, fillet=ring_fillet)
    # ---- the cap: a dressed drip course, softly out of round ----------------------------------------------------
    ck = dict(CHIMNEY_CAP, **(cap or {}))
    R = r_base - top * tb
    r_in = R - ck["inset"]
    h, dr = ck["h"], ck["drip"]
    prof = [(r_in, top - 0.04), (R - 0.02, top - 0.04), (R + dr, top - 0.01), (R + dr + 0.01, top + 0.03),
            (R + dr - 0.01, top + 0.6 * h), (R + 0.01, top + h), (r_in + 0.03, top + h), (r_in, top + h - 0.03),
            (r_in, top - 0.04)]
    seg = 40
    V, F = lathe_rz(prof[:-1], seg, cx=0.0, cy=0.0, z0=0.0, cap_bottom=False, cap_top=False)
    # close the ring section (the lathe leaves the first / last profile rows open): connect last row to first
    nr = len(prof) - 1
    a = np.arange(seg)
    extra = np.stack([(nr - 1) * seg + a, (nr - 1) * seg + (a + 1) % seg, (a + 1) % seg, a], 1)
    ph = np.arctan2(V[:, 1], V[:, 0])
    rng = np.random.default_rng(seed + 5)
    p1, p2 = rng.uniform(0, 2 * math.pi, 2)
    wob = 1.0 + ck["wobble"] * (np.sin(3 * ph + p1) + 0.6 * np.sin(5 * ph + p2)) / max(R, 0.3)
    V[:, :2] *= wob[:, None]
    V[:, 0] += C[0]
    V[:, 1] += C[1]
    # the profile runs CCW in (r, z) (bottom out, outer face up, top in, flue face down): lathe_rz's quads face
    # outward; `extra` closes the flue face back to the first row the same way
    acc = Acc(f"{g.prefix}_{name}_cap", 40)
    acc.add(V, list(F) + [extra], "M_stone_dressed", wear=0.5)
    finalize(acc, g.coll, smooth_deg=40.0)
    # ---- the flue: a dark closed cup inside the cap (no view down the stack) -------------------------------------
    fb = Acc(f"{g.prefix}_{name}_flue_blocker", 40)
    Vf, Ff = lathe_rz([(0.0, top - 0.35), (r_in + 0.01, top - 0.35), (r_in + 0.01, top + h - 0.04)], 24,
                      cx=float(C[0]), cy=float(C[1]), z0=0.0, cap_bottom=False, cap_top=False)
    fb.add(Vf, Ff, "M_stone", wear=0.9)
    finalize(fb, g.coll, smooth_deg=40.0)
    z_cap = top + h
    rec = dict(name=name, center=C.copy(), R_head=R, top=top, z_cap=z_cap, crown=crown)
    # ---- the round crown ------------------------------------------------------------------------------------------
    cr = Acc(f"{g.prefix}_{name}_crown", 35)
    if crown == "louvre":
        lk = dict(n=6, h=0.24, ring=0.70, post=(0.12, 0.10), hat_r=0.95, hat_pitch=34.0, finial=None)
        lk.update(louvre or {})
        if lk["h"] > 0.30:                                    # producer note 23:12: a low louvre, never a lantern
            log(f"  {name}: louvre h {lk['h']:.2f} -> 0.30 m (kept low)")
            lk["h"] = 0.30
        r_l = lk["ring"] * R
        for k in range(int(lk["n"])):
            t = 2 * math.pi * (k + 0.5) / lk["n"] + rng.uniform(-0.05, 0.05)
            e_r = np.array([math.cos(t), math.sin(t), 0.0])
            e_t = np.array([-math.sin(t), math.cos(t), 0.0])
            O = np.array([C[0], C[1], z_cap - 0.01]) + e_r * r_l
            obox(cr, O[None], np.array([0.0, 0.0, 1.0]), e_t, e_r, lk["h"] + 0.03, lk["post"][0], lk["post"][1],
                 0.015, "M_stone_dressed", nx=3, ny=3, nz=3)
        finalize(cr, g.coll, smooth_deg=35.0)
        hat = Acc(f"{g.prefix}_{name}_cap_collar", 50)
        r0 = lk["hat_r"] * R
        h0 = r0 * math.tan(math.radians(lk["hat_pitch"]))
        z_apex = z_cap + lk["h"] + h0 + 0.01
        z_top = lead_hat(hat, float(C[0]), float(C[1]), z_apex, r0, h0, seg=32)
        finalize(hat, g.coll, smooth_deg=50.0)
        if lk["finial"]:
            fin = Acc(f"{g.prefix}_{name}_finial", 45)
            turned_finial(fin, (float(C[0]), float(C[1]), z_top - 0.01), scale=lk["finial"], lean_deg=1.0, seg=20)
            finalize(fin, g.coll, smooth_deg=45.0)
        # the smoke chamber behind the posts: a dark closed drum (no view through the louvre)
        sm = Acc(f"{g.prefix}_{name}_louvre_blocker", 40)
        Vs, Fs = lathe_rz([(0.0, z_cap - 0.02), (r_l - 0.07, z_cap - 0.02), (r_l - 0.07, z_apex - h0 + 0.02),
                           (0.0, z_apex - h0 + 0.02)], 24, cx=float(C[0]), cy=float(C[1]), z0=0.0,
                          cap_bottom=False, cap_top=False)
        sm.add(Vs, Fs, "M_stone", wear=0.9)
        finalize(sm, g.coll, smooth_deg=40.0)
        rec.update(z_top=z_top, hat_r=r0, drip=z_apex - h0)
    elif crown == "pot":
        pk = dict(r=0.20, h=0.50)
        pk.update(pot or {})
        rp, hp = pk["r"], pk["h"]
        prof = [(rp * 1.15, 0.0), (rp * 1.25, 0.05), (rp * 1.05, 0.12), (rp * 0.92, 0.35 * hp), (rp * 1.0, 0.8 * hp),
                (rp * 1.12, hp - 0.03), (rp * 1.10, hp), (rp * 0.80, hp), (rp * 0.78, hp - 0.10)]
        Vp, Fp = lathe_rz(prof, 28, cx=float(C[0]), cy=float(C[1]), z0=z_cap - 0.02, cap_bottom=True, cap_top=True)
        cr.add(Vp, Fp, "M_stone_dressed", wear=0.5)
        finalize(cr, g.coll, smooth_deg=40.0)
        rec.update(z_top=z_cap + hp)
    else:
        raise ValueError(f"chimney: crown {crown!r}; 'louvre' or 'pot'")
    if not hasattr(g, "CHIMNEYS"):
        g.CHIMNEYS = []
    g.CHIMNEYS.append(rec)
    log(f"  {name}: round stack r {r_base:.2f} -> {R:.2f} m (batter {batter_deg:.1f} deg), head {top:.2f}, cap "
        f"{z_cap:.2f}, crown {crown} to {rec['z_top']:.2f}")
    return rec


def chimney_decals(g, seed=1701):
    """producer note 11 anchors on every chimney (g.CHIMNEYS): soot on the stack's head under the cap (4 sides,
    most likely on the lee / north side) and lichen on the cap top.  Run in the recipe's decals step (after
    recenter: g.SHIFT is applied)."""
    from ..decals import SurfaceProbe
    sh = np.asarray(getattr(g, "SHIFT", np.zeros(3)), float)
    probe = SurfaceProbe([o for o in g.coll.all_objects if o.type == "MESH"])
    rng = np.random.RandomState(seed)
    n = 0
    for rec in getattr(g, "CHIMNEYS", []):
        C = rec["center"] + sh[:2]
        for k, az in enumerate((0.3, 1.9, 3.4, 4.9)):
            d = np.array([math.cos(az), math.sin(az), 0.0])
            hit = None
            for dz in (0.0, -0.08, 0.08, -0.16, 0.16, -0.24):           # a stone face, not a mortar joint
                o = np.array([C[0], C[1], rec["top"] - 0.35 + dz]) + d * (rec["R_head"] + 0.6)
                hit = probe.cast(o, -d, 1.2)
                if hit is not None and hit["surface"] == "M_stone" and "_mortar" not in hit["object"]:
                    break
                hit = None
            if hit is not None:
                p = 0.85 if d[1] > 0 else 0.6
                g.decals.add("soot", hit["pos"], hit["normal"], size=(0.55, 0.70), surface=hit["surface"],
                             probability=p, seed=int(rng.randint(1, 2 ** 31 - 1)))
                n += 1
        o = np.array([C[0] + rec["R_head"] * 0.95, C[1], rec["z_cap"] + 0.6])
        hit = probe.cast(o, (0.0, 0.0, -1.0), 1.0)
        if hit is not None and hit["surface"] == "M_stone_dressed":
            g.decals.add("lichen", hit["pos"], hit["normal"], size=(0.18, 0.18), surface="M_stone_dressed",
                         probability=0.5, seed=int(rng.randint(1, 2 ** 31 - 1)))
            n += 1
    log(f"  chimney decals: {n} anchors")
    return n
