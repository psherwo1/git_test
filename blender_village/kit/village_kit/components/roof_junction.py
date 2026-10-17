"""components.roof_junction -- junctions where a straight (gable) roof meets a round body under a conical roof (kit,
variant v3_longhouse_roundend).

The round body is any components.frame.RoundFrame cone (its reference profile g.PS / g.PR / g.PZ / g.PA), centred at
`center`; the straight roof is a components.linear_roof.GableRoof spec.  Nothing here is specific to one building:
any linear roof (thatch or shingle covering, any pitch / width / yaw) can be run into any round cone.

    cone_ref_z(g, x, y, center)         height of the cone's reference surface (top of battens) at world (x, y)
    inside_cone(g, center, depth)       clip(P, margin=0) -> bool: P is under the cone's covering (hidden), for
                                        linear_roof(..., clip=...) and wall culls
    abutment_curve(g, roof, center)     the junction line: the covering's top meets the cone's covering top (up one
                                        slope, over the ridge roll, down the other), continued down both eave noses
                                        and along both eave soffits to the wall faces
    cone_abutment(g, roof, center, ...) KIT COMPONENT: a continuous flashing (lead apron by default) along that line,
                                        its one skirt dressed down into the linear covering, the other up the cone and
                                        under its shingles, closed at both ends -> <P>_<roof>_abutment
    cone_nose_apron(acc, g, roof, sg, ...)   the closed lead apron folded over a linear roof's eave nose where it
                                        meets the cone (part of cone_abutment with end="apron"); kit 1.8.0: renamed from
                                        end_apron (deprecated alias kept), junctions.wall_end_apron is the wall piece
    round_eave_fill(g, r_off, ...)      KIT COMPONENT: masonry / daub eave fill on a round wall head between the
                                        plate and the cone's deck (closes the eave gap of a stone round body)
                                        -> <P>_eave_fill; kit 1.8.0: a wrapper of components.eave.eave_closure
                                        (kind="fill")
    wall_abutment(g, roof, center, ...) KIT COMPONENT (v3 round 8): a linear roof running into a round WALL that
                                        rises past its ridge (the cylinder version of cone_abutment): roof trimmed
                                        at the face, mortar flaunching on the true intersection line, lead end
                                        aprons, seal-probe registration -> <P>_<roof>_wall_abutment
    round_body_face(g, center)          (R(z), head z) of the round stone body on g.WALL_FACES
"""
import math

import numpy as np

from ..core import grid_quads, log, n2
from ..geom import Acc, finalize


def _cone_profile(g):
    return g.PR, g.PZ, g.PA


def cone_ref_z(g, x, y, center=(0.0, 0.0)):
    """reference-surface height of the cone of round frame g at world (x, y); -inf outside the eave circle."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    d = np.hypot(x - center[0], y - center[1])
    PR, PZ, PA = _cone_profile(g)
    z = np.interp(-d, -PR, PZ)
    inner = d < PR[-1]
    z = np.where(inner, PZ[-1] + (PR[-1] - d) * math.tan(PA[-1]), z)
    return np.where(d <= PR[0], z, -np.inf)


def cone_slope_k(g, d):
    """-dz/dd of the cone reference profile at horizontal distance d."""
    PR, PZ, PA = _cone_profile(g)
    return np.tan(np.interp(-np.asarray(d, float), -PR, PA))


def cone_normal(g, x, y, center=(0.0, 0.0)):
    dx, dy = np.asarray(x, float) - center[0], np.asarray(y, float) - center[1]
    d = np.maximum(np.hypot(dx, dy), 1e-6)
    k = cone_slope_k(g, d)
    n = np.stack([k * dx / d, k * dy / d, np.ones_like(d)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def inside_cone(g, center=(0.0, 0.0), depth=0.0):
    """clip(P, margin=0.0) -> bool per vertex: under the cone's reference surface by more than depth + margin (inside
    the round body's roof, never seen from outside)."""
    def clip(V, margin=0.0):
        V = np.asarray(V, float)
        zc = cone_ref_z(g, V[:, 0], V[:, 1], center)
        return V[:, 2] < zc - depth - margin
    return clip


def _first_inside(fz, x_from, x_to, step=0.02):
    """scan x from x_from toward x_to; first x where fz(x) < 0 (the covering is under the cone), refined."""
    xs = np.arange(x_from, x_to, step if x_to > x_from else -step)
    if not len(xs):
        return None
    v = np.array([fz(x) for x in xs])
    idx = np.flatnonzero(v < 0)
    if not len(idx) or idx[0] == 0:
        return None
    a, b = xs[idx[0] - 1], xs[idx[0]]
    for _ in range(30):
        m = 0.5 * (a + b)
        if fz(m) < 0:
            b = m
        else:
            a = m
    return 0.5 * (a + b)


def _cone_top_local(g, roof, center, cone_cover):
    def f(x, y, z=None):
        W = roof.to_world(np.array([[x, y, 0.0]]))[0]
        zc = cone_ref_z(g, W[0], W[1], center)
        return float(zc) + cone_cover / max(float(cone_normal(g, W[0], W[1], center)[2]), 0.3)
    return f


def section_meets_cone(g, roof, sg, u, o, center=(0.0, 0.0), cone_cover=0.05):
    """local ridge coordinate x where the roof-section point (slope distance u, offset o, side sg) first passes
    under the cone's covering top, scanning from the roof's far end toward the cone; None if it never does."""
    cl = roof.to_local(np.array([[center[0], center[1], 0.0]]))[0]
    toward = 1.0 if cl[0] > 0.5 * (roof.x0 + roof.x1) else -1.0
    x_far = roof.xa if toward > 0 else roof.xb

    def fz(xx):
        P = roof.surf(xx, u, sg, o)
        W = roof.to_world(P[None])[0]
        zc = cone_ref_z(g, W[0], W[1], center)
        if not np.isfinite(zc):
            return 1.0
        return float(W[2]) - (float(zc) + cone_cover / max(float(cone_normal(g, W[0], W[1], center)[2]), 0.3))
    return _first_inside(fz, x_far, cl[0])


def abutment_curve(g, roof, center=(0.0, 0.0), cone_cover=0.05, roof_lift=0.0, dy=0.03, ends="nose",
                   crest_over=0.015):
    """the junction line, as world points with the two surface normals at each:
    returns P (n, 3), n_roof (n, 3), n_cone (n, 3).  The roof's top is GableRoof.top_z (mid-step envelope incl. the
    ridge roll) + roof_lift; the cone's top is its reference surface + cone_cover (the shingle stack).  The line runs
    from the -y wall face along the eave soffit, up the eave nose, over the slopes and the ridge roll, and back down
    the +y side.  The roof end that meets the cone is the one nearer the cone centre."""
    cl = roof.to_local(np.array([[center[0], center[1], 0.0]]))[0]
    toward = 1.0 if cl[0] > 0.5 * (roof.x0 + roof.x1) else -1.0
    x_far = roof.xa if toward > 0 else roof.xb
    x_near = cl[0]
    cos_p = math.cos(roof.p)

    def cone_top_local(x, y):
        W = roof.to_world(np.array([[x, y, 0.0]]))[0]
        z = cone_ref_z(g, W[0], W[1], center)
        return float(z) + cone_cover / max(float(cone_normal(g, W[0], W[1], center)[2]), 0.3)

    pts, nr = [], []
    Y = roof.Y
    t_nose = (roof.T0 + roof.step) / cos_p
    z_soffit_lip = roof.z_lip - roof.deck_t / cos_p
    for sg in (-1, 1):
        seg = []
        if ends != "nose":                 # round 2: the sweep stops at the top of the eave nose (end aprons)
            pts.append(seg)
            continue
        # eave soffit (deck underside) from the wall face out to the lip
        for y in np.linspace(roof.half, Y, 6):
            zs = float(roof.under_z(y))
            x = _first_inside(lambda xx, y=y, zs=zs: zs - cone_top_local(xx, sg * y), x_far, x_near)
            if x is not None:
                seg.append(((x, sg * y, zs), (0.0, -sg * math.sin(roof.p), -cos_p)))
        # eave nose (the thick lip face), bottom -> top
        for z in np.linspace(z_soffit_lip - 0.04, roof.z_lip + t_nose, 7):
            x = _first_inside(lambda xx, z=z: z - cone_top_local(xx, sg * Y), x_far, x_near)
            if x is not None:
                seg.append(((x, sg * (Y + 0.01), z), (0.0, sg * cos_p, -math.sin(roof.p))))
        if sg > 0:
            seg = seg[::-1]
        pts.append(seg)
    # the slopes and the ridge: y from -Y to +Y
    mid = []
    y_m = Y - 0.04
    top_fn = roof.top_z
    ys = None
    if ends == "plane":
        # round 4: over the slopes, the ridge AND the eave roll up to just past its crest (the roof solid's column
        # top, linear_roof.GableRoof.section_columns), so the sweep meets the end apron with a lap, not a gap
        ya, ztc, _zb = roof.section_columns()
        ok = np.isfinite(ztc)
        ya_ok, zt_ok = ya[ok], ztc[ok]
        top_fn = lambda y: np.interp(np.abs(np.asarray(y, float)), ya_ok, zt_ok)  # noqa: E731
        band = ya_ok > ya_ok.max() - 0.45
        y_m = float(ya_ok[band][np.argmax(zt_ok[band])]) + crest_over
        ys = np.arange(-y_m, y_m + 1e-9, dy)
        fine = np.linspace(y_m - 0.20, y_m, 9)
        ys = np.unique(np.round(np.concatenate([ys[np.abs(ys) < y_m - 0.20], fine, -fine]), 6))
    elif ends != "nose":
        R = getattr(roof, "ROLL", None)
        y_m = Y - ((R["u_c"] + 0.06) if R is not None else 0.10) * cos_p
    for y in (np.arange(-y_m, y_m + 1e-9, dy) if ys is None else ys):
        zt = float(top_fn(y)) + roof_lift
        x = _first_inside(lambda xx, y=y, zt=zt: zt - cone_top_local(xx, y), x_far, x_near)
        if x is None:
            continue
        e = 0.01
        dzdy = (float(top_fn(y + e)) - float(top_fn(y - e))) / (2 * e)
        n_ = np.array([0.0, -dzdy, 1.0])
        mid.append(((x, y, zt), tuple(n_ / np.linalg.norm(n_))))
    seq = pts[0] + mid + pts[1]
    if len(seq) < 4:
        return None
    P = roof.to_world(np.array([s[0] for s in seq]))
    NR = roof.dir_world(np.array([s[1] for s in seq]))
    NC = cone_normal(g, P[:, 0], P[:, 1], center)
    return P, NR, NC


def _smooth(A, k=2):
    out = A.copy()
    for i in range(len(A)):
        a, b = max(0, i - k), min(len(A), i + k + 1)
        out[i] = A[a:b].mean(0)
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


KEPT_COVER = ("roof_shingles", "roof_starter", "roof_underlap")


def kept_cover_points(g, names=KEPT_COVER):
    """round 4: world vertices of the cone covering units that are still there (after composite.cone_keep_out)."""
    import bpy
    out = []
    for nm in names:
        ob = bpy.data.objects.get(f"{g.prefix}_{nm}")
        if ob is None or ob.type != "MESH" or not len(ob.data.vertices):
            continue
        V = np.zeros(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", V)
        out.append(V.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3])
    return np.concatenate(out) if out else np.zeros((0, 3))


def _first_kept_along(K, p, b, nc, reach=0.6, tube=0.05, up=(-0.04, 0.16)):
    """distance along direction b (on the cone surface, from junction point p) to the first kept covering vertex in a
    tube round that line (normal band `up` about the cone normal nc); None if none within reach."""
    d = K - p
    s = d @ b
    m = (s > 0.0) & (s < reach)
    if not m.any():
        return None
    d, s = d[m], s[m]
    h = d @ nc
    side = np.linalg.norm(d - s[:, None] * b - h[:, None] * nc, axis=1)
    k = (side < tube) & (h > up[0]) & (h < up[1])
    return float(s[k].min()) if k.any() else None


def cone_nose_apron(acc, g, roof, sg, center=(0.0, 0.0), w_out=0.20, w_in=0.12, t=(0.012, 0.010), z_min=None,
                    cone_cover=0.05, mat="M_lead", n_rows=14, w_in_kept=False, kept_lap=0.06, w_in_max=0.45,
                    u_top=0.10):
    """kit 1.8.0: renamed from roof_junction.end_apron (junctions.end_apron is a different piece, now
    junctions.wall_end_apron); `end_apron` stays here as a deprecated alias.
    KIT COMPONENT (part of cone_abutment(end="apron")): a closed lead end-apron where the eave of a linear roof
    meets a round body's cone.  It lies on the eave nose (the GableRoof.ROLL section, or the plain covering edge),
    from just above the crest down over the nose face, as a band w_out (onto the linear roof) + w_in (tucked under
    the cone's starter course) wide along the ridge axis, centred on the seam where the cone's covering crosses the
    nose; lead `t` = (out, in) thick about the nose surface.  Nothing goes below z_min (default: the cone's eave
    lip, g.Z_EAVE).  Returns the number of rows built (0: the nose never meets the cone)."""
    R = getattr(roof, "ROLL", None)
    if R is None:
        R = dict(u_c=0.11, Ru=0.11, o_m=0.5 * (roof.T0 + roof.step - roof.deck_t - 0.07),
                 hh=0.5 * (roof.T0 + roof.step + roof.deck_t + 0.07), H=roof.T0 + roof.step, L=0.4,
                 o_end=roof.T0)
    z_min = float(getattr(g, "Z_EAVE", -1e9)) + 0.01 if z_min is None else z_min
    # rows: the top of the roll just up-slope of the crest (under the sweep's end), then the nose face downward
    u_top = min(u_top, R["L"] - 0.005)
    ut = np.linspace(R["u_c"] + u_top, R["u_c"] + 0.005, 4 if u_top <= 0.10 else 7)
    tt = (ut - R["u_c"]) / R["L"]
    ot = R["o_end"] + (R["H"] - R["o_end"]) * (1 - tt) ** 1.5
    dodu = -1.5 * (R["H"] - R["o_end"]) * (1 - tt) ** 0.5 / R["L"]
    nt = np.stack([-dodu, np.ones_like(dodu)], 1)
    a = np.linspace(0.5 * np.pi, -0.30 * np.pi, n_rows)
    ua = R["u_c"] - R["Ru"] * np.cos(a)
    oa = R["o_m"] + R["hh"] * np.sin(a)
    na = np.stack([-np.cos(a) / R["Ru"], np.sin(a) / R["hh"]], 1)
    us, os_ = np.concatenate([ut, ua]), np.concatenate([ot, oa])
    N = np.concatenate([nt, na])
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    rows = []
    for u_, o_, n_ in zip(us, os_, N):
        x_s = section_meets_cone(g, roof, sg, u_, o_, center, cone_cover)
        if x_s is None:
            continue
        z_ = float(roof.to_world(roof.surf(x_s, u_, sg, o_)[None])[0][2])
        if z_ < z_min + 0.02:
            break
        rows.append((x_s, u_, o_, n_))
    if len(rows) < 3:
        return 0
    cl = roof.to_local(np.array([[center[0], center[1], 0.0]]))[0]
    toward = 1.0 if cl[0] > 0.5 * (roof.x0 + roof.x1) else -1.0
    cols = np.linspace(-w_out, w_in, 7) * toward
    xs_ = np.array([r[0] for r in rows])
    for _ in range(2):                                    # a calm seam line (no kinks from the cone's facets)
        xs_[1:-1] = 0.25 * xs_[:-2] + 0.5 * xs_[1:-1] + 0.25 * xs_[2:]
    nr, nc = len(rows), len(cols)
    w_ins = np.full(nr, float(w_in))
    if w_in_kept:
        # round 4: the cone-side width per row from the units the keep-out KEPT: the apron runs kept_lap m under
        # (behind) the first kept cone unit beyond the seam, so no dropped unit leaves a void beside it
        K = kept_cover_points(g)
        if len(K):
            KL = roof.to_local(K)
            for i, (x_s, u_, o_, n_) in enumerate(rows):
                p = roof.surf(xs_[i], u_, sg, o_)
                d = (KL[:, 0] - xs_[i]) * toward
                m = (d > 0) & (d < w_in_max) & (np.abs(KL[:, 1] - p[1]) < 0.12) & (KL[:, 2] > p[2] - 0.06) & \
                    (KL[:, 2] < p[2] + 0.30)
                if m.any():
                    w_ins[i] = min(w_in_max, max(w_in, float(d[m].min()) + kept_lap))
            for _ in range(3):
                w_ins[1:-1] = 0.25 * w_ins[:-2] + 0.5 * w_ins[1:-1] + 0.25 * w_ins[2:]
    out_, in_ = [], []
    for i, ((x_s, u_, o_, n_), xs0) in enumerate(zip(rows, xs_)):
        X = xs0 + np.linspace(-w_out, w_ins[i], nc) * toward
        out_.append(roof.surf(X, u_ + n_[0] * t[0], sg, o_ + n_[1] * t[0]))
        in_.append(roof.surf(X, u_ - n_[0] * t[1], sg, o_ - n_[1] * t[1]))
    Vo = np.concatenate(out_)
    Vi = np.concatenate(in_)
    V = np.concatenate([Vo, Vi])
    off = nr * nc
    ii = np.arange(nr - 1)[:, None] * nc + np.arange(nc - 1)[None, :]
    Fo = np.stack([ii, ii + 1, ii + nc + 1, ii + nc], -1).reshape(-1, 4)
    Fi = Fo[:, ::-1] + off
    rim = []
    for r in range(nr - 1):                              # the two long edges (along the rows)
        a0, b0 = r * nc, (r + 1) * nc
        rim.append((a0, b0, b0 + off, a0 + off))
        a1, b1 = r * nc + nc - 1, (r + 1) * nc + nc - 1
        rim.append((a1, a1 + off, b1 + off, b1))
    for c in range(nc - 1):                              # the top and bottom edges
        rim.append((c, c + off, c + 1 + off, c + 1))
        a2 = (nr - 1) * nc + c
        rim.append((a2, a2 + 1, a2 + 1 + off, a2 + off))
    F = np.concatenate([Fo, Fi, np.array(rim)])
    # outward: the outer sheet faces along the nose normal
    Pw = roof.to_world(V)
    q = Pw[F[len(Fo) // 2]]
    nu, no = rows[nr // 2][3]
    cp, sp = math.cos(roof.p), math.sin(roof.p)
    n_w = roof.dir_world(np.array([0.0, sg * (-nu * cp + no * sp), nu * sp + no * cp]))
    if float(np.cross(q[1] - q[0], q[3] - q[0]) @ n_w) < 0:
        F = [Fo[:, ::-1], Fi[:, ::-1], np.array(rim)[:, ::-1]]
    acc.add(Pw, F, mat, wear=0.4)
    if w_in_kept:
        log(f"  end apron {sg:+d}: w_in from kept units {w_ins.min():.2f}-{w_ins.max():.2f} m")
    return nr


end_apron = cone_nose_apron
"""deprecated alias (kit 1.8.0): use cone_nose_apron."""


def cone_abutment(g, roof, center=(0.0, 0.0), width=(0.26, 0.22), crown=0.09, mat="M_lead", seed=91,
                  cone_cover=0.05, roof_lift=0.0, dy=0.05, end="apron", apron=None, sweep_end="crest", taper=None,
                  fit_kept=False, kept_lap=0.06, wb_max=0.55):
    """KIT COMPONENT: the flashing along the junction of a linear roof and a round body's cone (see module doc).
    round 4 (all optional, defaults = round 3):
      sweep_end="plane": the slope sweep runs on over the eave roll to just past its crest (abutment_curve), so it
        laps over the end apron's top instead of stopping short of it;
      taper=m: the sweep's section closes smoothly over the last `m` metres of each end into a small domed cap (a
        closed lead end, no open or crumpled section);
      fit_kept=True: the skirt up the cone is sized per station from the cone units the keep-out actually KEPT
        (composite.cone_keep_out): it reaches `kept_lap` m under the first kept unit, so no dropped unit leaves a
        dark void beside the flashing (up to wb_max).
    width = (skirt down onto the linear covering, skirt up the cone) in metres; crown = height of the rounded bead
    over the junction line.  Both skirts end buried (8-12 cm under the coverings' tops), so the flashing closes the
    joint whatever the course steps, shingle butts or thatch clumps do under it; the ends are capped.
    end="apron" (round 2 default): the sweep runs over the slopes and the ridge only, stopping at the top of each
    eave nose, and each eave gets a separate closed lead end_apron (kwargs `apron`) folded down over the nose and
    tucked under the cone's starter course (nothing below the cone's eave lip).  end="nose": the round-1 sweep round
    the eave soffit and nose."""
    cur = abutment_curve(g, roof, center, cone_cover=cone_cover, roof_lift=roof_lift, dy=dy,
                         ends="nose" if end == "nose" else sweep_end)
    if cur is None:
        log("  abutment: no junction found")
        return None
    P, NR, NC = cur
    n = len(P)
    if taper and n > 12:
        # round 4: end the sweep where the roof normal still follows the slope -- the stations where the junction
        # turns over the eave roll's plateau twist the section (the round-3 crumpled tip); the end apron, run up
        # under the sweep end (cone_nose_apron(u_top=...)), covers that stretch
        c25 = math.cos(math.radians(25.0))
        k0, k1 = 0, n
        while k0 < n // 3 and float(NR[k0] @ NR[min(k0 + 6, n - 1)]) < c25:
            k0 += 1
        while k1 > 2 * n // 3 and float(NR[k1 - 1] @ NR[max(k1 - 7, 0)]) < c25:
            k1 -= 1
        P, NR, NC = P[k0:k1], NR[k0:k1], NC[k0:k1]
        n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0], T[-1] = P[1] - P[0], P[-1] - P[-2]
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    NR = _smooth(NR, 2)
    NC = _smooth(NC, 1)

    def perp(v):
        v = v - (v * T).sum(1, keepdims=True) * T
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    A = perp(-NC - (-NC * NR).sum(1, keepdims=True) * NR)          # along the roof, away from the cone
    B = perp(NR - (NR * NC).sum(1, keepdims=True) * NC)             # up the cone, away from the roof
    BI = perp(NR + NC)
    wr, wb = width
    wob = 1 + 0.08 * n2(np.arange(n) * 0.15, np.zeros(n), seed)
    up_lift = 0.035
    if fit_kept:
        K = kept_cover_points(g)
        if len(K):
            wb = np.full(n, float(wb))
            for i in range(n):
                gap = _first_kept_along(K, P[i], B[i], NC[i])
                if gap is not None:
                    wb[i] = min(wb_max, max(wb[i], (gap + kept_lap) / 0.62))
            for _ in range(3):                                     # a calm skirt edge
                wb[1:-1] = 0.25 * wb[:-2] + 0.5 * wb[1:-1] + 0.25 * wb[2:]
            wb = wb[:, None]
            up_lift = 0.05                                         # over the kept units' butts, not through them
    loop = [
        P - BI * 0.07,
        P + A * wr * wob[:, None] - NR * 0.12,
        P + A * wr * 0.62 + NR * 0.035,
        P + A * wr * 0.28 + NR * 0.075 + BI * 0.02,
        P + BI * crown,
        P + B * wb * 0.28 + NC * 0.07 + BI * 0.02,
        P + B * wb * 0.62 + NC * up_lift,
        P + B * wb * wob[:, None] - NC * 0.09,
    ]
    L = np.stack(loop, 1)                                          # (n, m, 3)
    if taper:
        # round 4: a closed, domed lead end -- the section shrinks over the last `taper` m and a final small ring
        # 3 cm past each end closes it (no open / folded section)
        sl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        de = np.minimum(sl, sl[-1] - sl)
        f = 0.55 + 0.45 * np.clip(de / taper, 0, 1) ** 0.6
        L = P[:, None, :] + (L - P[:, None, :]) * f[:, None, None]
        ends_ = []
        for i, sgn in ((0, -1.0), (n - 1, 1.0)):
            Pe = P[i] + T[i] * sgn * 0.03
            ends_.append(Pe[None, :] + (L[i] - P[i][None, :]) * 0.22)
        L = np.concatenate([ends_[0][None], L, ends_[1][None]])
        n = L.shape[0]
    m = L.shape[1]
    V = L.reshape(-1, 3)
    i = np.arange(n - 1)[:, None]
    j = np.arange(m)[None, :]
    a_ = i * m + j
    b_ = i * m + (j + 1) % m
    F = [np.stack([a_, b_, b_ + m, a_ + m], -1).reshape(-1, 4), np.arange(m)[::-1][None, :],
         ((n - 1) * m + np.arange(m))[None, :]]
    acc = Acc(f"{g.prefix}_{roof.name}_abutment", 45)
    acc.add(V, F, mat, wear=0.4)
    n_ap = []
    if end == "apron":
        for sg in (-1, 1):
            n_ap.append(cone_nose_apron(acc, g, roof, sg, center, cone_cover=cone_cover, mat=mat, **(apron or {})))
    ob = finalize(acc, g.coll, smooth_deg=45.0, recalc=True)
    log(f"  abutment: {n} stations, length {float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum()):.2f} m"
        + (f", end aprons {n_ap} rows" if n_ap else ""))
    if not hasattr(g, "ABUTMENTS"):
        g.ABUTMENTS = []
    g.ABUTMENTS.append(dict(roof=roof.name, P=P, NR=NR, NC=NC))
    # kit 1.9.0 (guard seal_probe): the linear roof runs into the round body / its cone -- registered for the
    # generic see-through probe after the cull (village_kit.guards; no geometry change).  The body face is the
    # cone's reference surface above its eave, the wall face (R_WALL + 0.14) below it.
    from ..guards import register_junction
    pz, pr = np.asarray(g.PZ, float), np.asarray(g.PR, float)
    r_face = float(g.R_WALL) + 0.14
    register_junction(g, f"{roof.name} / round body", (f"{g.prefix}_{roof.name}_covering",
                                                        f"{g.prefix}_{roof.name}_eave_roll"), center,
                      lambda z, pz=pz, pr=pr, rf=r_face: float(np.interp(z, pz, pr)) if z >= pz[0] else rf,
                      (float(P[:, 2].min()) - 0.3, float(P[:, 2].max()) + 0.3))
    return ob


def round_eave_fill(g, r_off=0.06, z_bot=None, center=(0.0, 0.0), skip=None, mat="M_mortar", n_az=240):
    """KIT COMPONENT: the eave fill of a round wall head (a stone or daub round body under a cone): a band on the
    inner half of the wall plate, from the plate top up into the cone's covering stack, so no eye can look from the
    eave gap into the roof space.  skip(P) -> bool drops parts inside an attached body.  -> <P>_eave_fill
    kit 1.8.0: a thin wrapper of THE eave closure, components.eave.eave_closure(kind="fill") (same geometry).
    round 5: z_bot="wall" -- the fill starts 3 cm inside the top of the round stone body published on g.WALL_FACES
    (rubble_walls.round_stone_body) at `center`: the masonry beam-fill of a round wall head that carries the rafters
    with NO timber wall plate (round_wall.wall_plate left out: under a deep stone eave it is never seen, note 1)."""
    from .eave import _fill_band
    if isinstance(z_bot, str) and z_bot == "wall":
        tops = [wf["top"] for wf in getattr(g, "WALL_FACES", []) if wf.get("kind") == "round"
                and np.allclose(wf.get("center", (0.0, 0.0)), center)]
        if not tops:
            raise ValueError("round_eave_fill(z_bot='wall'): no round stone body at this centre on g.WALL_FACES")
        z_bot = float(tops[0]) - 0.03
        log(f"  eave fill from the round wall head z {z_bot:.3f} m (no wall plate)")
    return _fill_band(g, r_off=r_off, z_bot=z_bot, center=center, skip=skip, mat=mat, n_az=n_az)


# =================================================================================================================
# kit round 8 (v3): a linear roof running into a round WALL (the cylinder version of cone_abutment)
# =================================================================================================================
LINEAR_ROOF_PARTS = (("deck", 0.03), ("rafters", 0.02), ("covering", 0.02), ("eave_roll", 0.02), ("ridge", 0.02),
                     ("comb", 0.02))
"""the objects linear_roof builds (<P>_<roof>_<part>) and the depth (m) behind the wall face each is trimmed at --
behind the round body's recessed mortar sheet (stone_wall.mortar_sheet, w0 -4 mm +- 3 mm), so no cut end shows."""


def round_body_face(g, center=(0.0, 0.0)):
    """(R(z), wall-head z) of the round stone body published on g.WALL_FACES at `center`
    (rubble_walls.round_stone_body); R(z) is its battered outer face radius."""
    for wf in getattr(g, "WALL_FACES", []):
        if wf.get("kind") == "round" and np.allclose(wf.get("center", (0.0, 0.0)), center):
            return wf["radius"], float(wf["top"])
    raise ValueError(f"no round stone body at {center} on g.WALL_FACES (build round_stone_body first)")


def wall_abutment(g, roof, center=(0.0, 0.0), radius=None, parts=LINEAR_ROOF_PARTS,
                  trace=("covering", "eave_roll", "ridge"), fillet=(0.10, 0.11), lift=0.05, bury=0.035,
                  end_aprons=True, apron=(0.18, 0.28), step_deg=0.5, name="wall_abutment", min_clear=0.25,
                  drop_near=(("comb", 0.15),)):
    """KIT COMPONENT (kit round 8, v3): a linear roof (GableRoof, built by linear_roof) runs INTO a round masonry
    WALL -- a round body whose wall rises past the roof's ridge, its own cone eave above it -- instead of the two
    eaves crossing (cone_abutment).  Generic over any GableRoof (thatch or shingle, any pitch / width / yaw) and any
    round body with a face radius R(z) (default: the round stone body on g.WALL_FACES at `center`).  The pieces are
    the compound family's roof-into-tower language (components.junctions), reused unchanged on a single frame:
      trim     every part of the roof (`parts`: [(part, depth)], LINEAR_ROOF_PARTS) is TRIMMED at the face, `depth`
               behind it (junctions.clip_at_tower: crossing edges split on the true battered surface, everything
               inside deleted) -- the deck, rafters, courses, eave rolls, ridge roll and comb stop inside the stone;
      trace    the true roof-top / wall-face line, by downward ray casts on the built covering (`trace` parts) just
               outside the face, every `step_deg` round the body (junctions.trace_roof_on_tower): up one slope, over
               the ridge, down the other, one run from eave to eave;
      fillet   a lime-mortar flaunching fitted to the covering along that line (junctions.ride_fillet: back buried
               `bury` in the masonry, crease fillet[0] over the covering at the face, toe fillet[1] out, `lift` over
               the courses), so no course step, thatch layer or ridge bundle can open a slot against the stone;
      aprons   end_aprons: a closed lead apron on the wall face at each eave end of the run (junctions.wall_end_apron,
               apron = (width past the eave, drop)) over the cut eave against the stone.
    drop_near [(part, d)]: units of these parts with any vertex less than d m outside the face are dropped WHOLE
    first (composite.drop_units) -- the ridge comb's shakes stop short of the flaunching instead of standing
    through it; the ridge roll under them runs on into the wall.
    The junction is registered for the seal-probe guard.  min_clear: when the round frame g has a cone (g.Z_EAVE),
    the roof's top within 1 m of the wall must stay min_clear m under the cone's eave lip, or the two eaves cross
    (that is cone_abutment's junction) and a ValueError says so.  -> <P>_<roof>_<name> (M_mortar / M_lead)."""
    import bpy
    from .junctions import _bvh, _smooth_up, clip_at_tower, ride_fillet, trace_roof_on_tower, wall_end_apron
    if radius is None:
        radius, _z_head = round_body_face(g, center)
    C = np.asarray(center, float)[:2]
    T = dict(center=C, R=lambda z, f=radius: np.asarray(f(np.asarray(z, float)), float), name="round wall")
    pre = f"{g.prefix}_{roof.name}"
    trimmed = []
    if drop_near:
        from .composite import drop_units
        from .junctions import tower_field
        for part, d in drop_near:
            ob = bpy.data.objects.get(f"{pre}_{part}")
            if ob is not None and ob.type == "MESH":
                n_ = drop_units(ob, lambda V, _d=float(d): tower_field(T, V) < _d, rule="any")
                trimmed.append(f"{part} -{n_} (whole units within {d:.2f} m)")
    for part, depth in parts:
        ob = bpy.data.objects.get(f"{pre}_{part}")
        if ob is None or ob.type != "MESH":
            continue
        n0 = len(ob.data.polygons)
        clip_at_tower(ob, T, inset=float(depth))
        trimmed.append(f"{part} {n0}->{len(ob.data.polygons)}")
    log(f"  {name}: trimmed at the wall face: " + ", ".join(trimmed))
    objs = [o for o in (bpy.data.objects.get(f"{pre}_{p}") for p in trace) if o is not None and len(o.data.polygons)]
    if not objs:
        raise ValueError(f"wall_abutment: no covering objects {trace} for roof {roof.name}")
    bvh = _bvh(objs)
    runs = trace_roof_on_tower(bvh, T, step_deg=step_deg, z_guess=float(roof.z_lip) + 1.0)
    if not runs:
        log(f"  {name}: the roof does not reach the wall")
        return None
    z_hi = max(float(P[:, 2].max()) for _, P in runs)
    if hasattr(g, "Z_EAVE") and z_hi > float(g.Z_EAVE) - min_clear:
        raise ValueError(f"wall_abutment: the roof top at the wall ({z_hi:.2f} m) is less than {min_clear:.2f} m under "
                         f"the cone's eave lip ({float(g.Z_EAVE):.2f} m) -- the eaves cross; raise the round body's "
                         f"eave_z or use cone_abutment")
    acc = Acc(f"{pre}_{name}", 35)
    for k, (th, P) in enumerate(runs):
        zb = _smooth_up(P[:, 2])
        log(f"  {name}: run {k}: {len(P)} samples, azimuth {np.degrees(th[0]):.1f}..{np.degrees(th[-1]):.1f} deg, "
            f"z {zb.min():.2f}..{zb.max():.2f} (cone eave lip {float(getattr(g, 'Z_EAVE', float('nan'))):.2f})")
        ride_fillet(acc, th, zb, T, bvh, h_up=fillet[0], out=fillet[1], lift=lift, bury=bury)
        if end_aprons:
            Pe = P.copy()
            Pe[:, 2] = zb + 0.03
            for i0, i1 in ((0, 1), (-1, -2)):
                n_out = np.array([Pe[i0, 0] - C[0], Pe[i0, 1] - C[1], 0.0])
                wall_end_apron(acc, Pe[i0] + np.array([0, 0, 0.02]), n_out, Pe[i0] - Pe[i1], apron[1], w=apron[0],
                               closed_lip=True)
    ob = finalize(acc, g.coll, smooth_deg=35.0)
    if not hasattr(g, "ABUTMENTS"):
        g.ABUTMENTS = []
    g.ABUTMENTS.append(dict(roof=roof.name, kind="wall", runs=runs, center=C))
    from ..guards import register_junction
    zs = np.concatenate([P[:, 2] for _, P in runs])
    register_junction(g, f"{roof.name} / round wall", (f"{pre}_covering", f"{pre}_eave_roll", f"{pre}_ridge"), C,
                      lambda z, f=radius: float(np.asarray(f(np.asarray(z, float)), float)),
                      (float(zs.min()) - 0.3, float(zs.max()) + 0.3))
    return ob
