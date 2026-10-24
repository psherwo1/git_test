"""components.daub_path -- kit 1.21.0 (v9 ale-house round 2): the OPTIONAL PATH-WALL mode of the wattle-and-daub wall.

daub.round_daub_wall builds the daub wall of a RoundFrame hut (post ring, door bay, plate, plinth stones, cone roof).
This module lays the SAME wall -- the same material slots (M_daub, M_wattle, M_timber), the same weave (wattle.weave_panel),
the same coat (a 6.2 cm mean face over the wattle line, a 2-2.5 cm hand lump now and then, a soft bulge and sag, a slit
beside every post so the posts stand proud, a tucked foot and head, exposed-wattle patches with a broken margin), the
same round-hewn posts (timber.round_post) -- along ANY plan path on a PlanFrame (or any frame with g.acc / g.coll):
straight runs and corners (a half-storey or a gablet between timber posts, on a rubble ground storey) or an arc / a
full circle (a round stair turret, an oven house), on a rubble plinth.  Nothing here changes an existing module;
daub.py / wattle.py / frame.py are untouched and the round-hut build is byte-identical.

    line_run(points)                    a polyline wattle line; OUTWARD = the RIGHT of travel (the rubble path walls'
                                        convention: interior on the left)
    arc_run(center, r, a0, a1)          an arc (a full circle by default), counter-clockwise, outward = radial
    even_posts(L, spacing, closed)      post positions (arc length) of an open / closed run
    polyline_posts(run, spacing)        the same on a polyline: a post at every corner
    path_daub(g, name, run, posts, z_lo, z_hi, ...)
                                        posts + coat + weave (where the coat is broken) + inner skin + windows + sill
                                        beam; objects <P>_<name>_posts / _daub / _wattle_rods / _inner_blocker / _sill /
                                        <P>_<name>_win_frames ...  (the inner skin is named *_blocker: composite_hidden_cull
                                        never culls it, so the cull cannot open a see-through hole)

z_lo (float or fn(s)) is where the wall stands (the stone top / plinth top); z_hi fn(s) its head (the roof's deck
underside).  Everything is deterministic (the seed).
"""
import math
from types import SimpleNamespace

import numpy as np

from ..core import fbm, grid_quads, log, n2, nrm, smoothstep
from .wattle import weave_panel

COAT = 0.062                 # mean coat face outside the wattle centre line (daub.COAT_R_NOM)
POST_OUT = 0.02              # post axis outside the wattle line (frame.POST_OUT)
INNER = 0.12                 # inner skin behind the wattle line
EDGE_T = 0.034               # coat thickness on the broken face of a patch margin


# =================================================================================================================
# runs
# =================================================================================================================
def line_run(points):
    """polyline wattle line; outward = right of travel (interior on the left)."""
    P = np.asarray(points, float)
    seg = P[1:] - P[:-1]
    ln = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(ln)])
    d = seg / ln[:, None]
    nrm_ = np.stack([d[:, 1], -d[:, 0]], -1)

    def f(s):
        s = np.asarray(s, float)
        k = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(ln) - 1)
        pt = P[k] + (s - cum[k])[..., None] * d[k]
        return pt, nrm_[k]
    return SimpleNamespace(f=f, L=float(cum[-1]), kind="line", cum=cum, closed=False)


def arc_run(center, r, a0=0.0, a1=2.0 * math.pi):
    """counter-clockwise arc (radians, from +x); outward = radial.  A full circle by default."""
    c = np.asarray(center, float)

    def f(s):
        a = a0 + np.asarray(s, float) / r
        nn = np.stack([np.cos(a), np.sin(a)], -1)
        return c + r * nn, nn
    full = abs((a1 - a0) - 2.0 * math.pi) < 1e-6
    return SimpleNamespace(f=f, L=float(r * (a1 - a0)), kind="arc", cum=None, closed=full)


def even_posts(L, spacing=1.45, closed=False, phase=0.0):
    """post positions (arc length): open run -> both ends and equal bays <= spacing; closed run -> equal bays from
    `phase` (the last bay wraps to the first post)."""
    if closed:
        n = max(3, int(round(L / spacing)))
        return [float(phase + k * L / n) for k in range(n)]
    n = max(1, int(math.ceil(L / spacing - 1e-9)))
    return [float(v) for v in np.linspace(0.0, L, n + 1)]


def polyline_posts(run, spacing=1.45):
    """a post at every corner and equal bays <= spacing along every segment of a line_run."""
    out = []
    for k, (a, b) in enumerate(zip(run.cum[:-1], run.cum[1:])):
        seg = [float(a) + p for p in even_posts(float(b - a), spacing)]
        out.extend(seg if k == 0 else seg[1:])
    return out


# =================================================================================================================
# fields
# =================================================================================================================
def _patch_fn(sc, zc, hw, hz, sd):
    """exposed-wattle patch: signed distance (m, negative inside) of a leaning, ragged, near-elliptic outline."""
    u0 = min(hw, hz)

    def f(s, z):
        s = np.asarray(s, float)
        z = np.asarray(z, float)
        a = (s - sc) / hw
        b = (z - zc) / hz
        th = np.arctan2(b, a)
        rr = 1.0 + 0.22 * n2(np.cos(th) * 1.6, np.sin(th) * 1.6, sd) + 0.10 * (b * np.sign(a))
        q = np.sqrt(a * a + b * b) / np.maximum(rr, 0.4)
        return (q - 1.0) * u0 + 0.003 * n2(s * 30.0, z * 30.0, sd + 6)
    return SimpleNamespace(f=f, sc=sc, hw=hw)


def _win_rec(path, s_c, sp, shrink=0.012):
    from .openings import resolve
    r = resolve(sp, "wall")
    if r["kind"] != "window":
        raise ValueError("path_daub windows must be window specs")
    hw, fw = r["width"] / 2, r["frame"]
    hx = hw + fw + 0.004 - shrink                       # the coat hole: the reveal rectangle, shrunk
    z0, z1 = r["sill"] - fw + shrink, r["sill"] + r["height"] + fw - shrink
    rb = dict(hx=hw + fw - 0.01, z0=r["sill"] - fw + 0.01, z1=r["sill"] + r["height"] + fw - 0.01)   # inner-skin hole

    def f(s, z):
        s = np.asarray(s, float)
        z = np.asarray(z, float)
        return np.maximum(np.abs(s - s_c) - hx, np.maximum(z0 - z, z - z1))
    return SimpleNamespace(f=f, s=float(s_c), hx=hx, z0=z0, z1=z1, spec=sp, rb=rb, r=r)


def _graded(lo, hi, hc, fine):
    xs = [lo]
    while xs[-1] < hi - 1e-6:
        x = xs[-1]
        hh = min([h for (a, b, h) in fine if a <= x + 0.5 * h and x - 0.5 * h <= b] + [hc])
        xs.append(min(hi, x + hh))
    if len(xs) > 2 and xs[-1] - xs[-2] < 0.3 * min(hc, 0.02):
        xs.pop(-2)
    return np.array(xs)


class _Shift:
    """forwards timber.round_post's mesh pieces, moved by d (the post is modelled about the origin)."""

    def __init__(self, acc, d):
        self.acc, self.d = acc, d

    def add(self, V, F, mat, uv=None, wrap=False, smooth=True, wear=None):
        self.acc.add(np.asarray(V, float).reshape(-1, 3) + self.d, F, mat, uv, wrap)


def _tab(fn, L, closed, step=0.02):
    """a fast evaluator of fn over [-1, L + 1.5 * (closed)] (interpolated table)."""
    lo, hi = -0.5, L + (L if closed else 0.5)
    ss = np.linspace(lo, hi, int((hi - lo) / step) + 2)
    vals = np.asarray(fn(ss), float)
    return lambda s, _s=ss, _v=vals: np.interp(np.asarray(s, float), _s, _v)


# =================================================================================================================
# the wall
# =================================================================================================================
def path_daub(g, name, run, posts, z_lo, z_hi, seed=1, closed=None, windows=(), patches=(), sill=False,
                   post_rad=(0.085, 0.10), grid=(0.05, 0.025, 0.0125), lumps=(2.0, 3.0), sill_half=(0.07, 0.085)):
    """KIT COMPONENT (kit 1.21.0, optional path-wall mode).  A wattle-and-daub wall along `run` (line_run / arc_run):
    run.f(s) -> (xy, outward normal) is the WATTLE centre line; `posts` the post positions (arc length; a closed run's
    last bay wraps to the first post); z_lo / z_hi the foot and head (float or fn(s) -> z).
      windows  [(s, window spec), ...]  (openings.window(width, height, sill, depth=0.15, room=0.7)): a hole in the coat
               and the inner skin and a wall_openings window set in it (frame, mortar reveal, dressed sill, lintel)
      patches  [(s, z, half_w, half_h, seed), ...]  exposed-wattle patches (the roundhut's fallen-out daub), each inside
               one bay and clear of the posts; the weave is modelled only there (rods and stakes under the coat are not)
      sill     a hewn sill beam along the foot (straight runs): the daub on a rubble ground storey stands on it
      grid     (coat step along, coat step up, step along near a patch / window) in metres
    Needs on g: acc(), coll, prefix (any Building); ROD_STORE / ROD_SHADOW_Z are filled in if the frame lacks them.
    -> a dict of the object names."""
    from .timber import round_post, timber_box
    from .wall_openings import build_opening, finish_accs, opening_accs
    rng = np.random.RandomState(seed)
    closed = bool(run.closed if closed is None else closed)
    L = run.L
    if not hasattr(g, "ROD_STORE"):
        g.ROD_STORE = {}
    if not hasattr(g, "ROD_SHADOW_Z"):
        g.ROD_SHADOW_Z = 99.0
    zl_f = _tab(z_lo if callable(z_lo) else (lambda s, _z=float(z_lo): np.full(np.shape(s), _z)), L, closed)
    zh_f = _tab(z_hi, L, closed)
    posts = [float(p) for p in posts]
    ps = posts + [posts[0] + L] if closed else list(posts)
    nb = len(ps) - 1
    rads = [float(rng.uniform(*post_rad)) for _ in posts]
    rad_all = rads + [rads[0]] if closed else list(rads)
    ez = np.array([0.0, 0.0, 1.0])
    out = {}

    # ---- posts (timber.round_post: the hut's hewn post, modelled about the origin and moved into place) ------------
    acc_p = g.acc(f"{name}_posts", 15)
    for i, s in enumerate(posts):
        pt, nn = run.f(np.array([s]))
        xy, n = pt[0] + nn[0] * POST_OUT, nn[0]
        zb = float(zl_f(s)) - 0.07
        zt = float(zh_f(s))
        if zt - zb < 0.3:
            log(f"  {name}: post {i} skipped (too short)")
            continue
        base = np.array([n[0], n[1], zb])
        top = np.array([n[0], n[1], zt])
        shim = SimpleNamespace(EAVE_SHADOW_Z=zt - 0.05)
        mr = g.detail.min_at((float(xy[0]), float(xy[1]), 1.2)) if hasattr(g, "detail") else 0.0
        round_post(shim, _Shift(acc_p, np.array([xy[0] - n[0], xy[1] - n[1], 0.0])), base, top, rads[i], rng,
                   check=(i % 3 == 1), radial=0.3, min_relief=mr)
    if acc_p.n:
        acc_p.build(g.coll)
        out["posts"] = f"{g.prefix}_{name}_posts"

    # ---- windows / patches -----------------------------------------------------------------------------------------
    wrecs = [_win_rec(run, s, sp) for s, sp in windows]
    prec = []
    for k, (sc, zc, hw, hz, sd) in enumerate(patches):
        prec.append(_patch_fn(float(sc), float(zc), float(hw), float(hz), int(sd)))

    acc_c = g.acc(f"{name}_daub", 70)
    acc_r = g.acc(f"{name}_wattle_rods", 60)
    acc_b = g.acc(f"{name}_inner_blocker", 70)
    n_rods = 0
    placed_p = 0
    for b in range(nb):
        sa, sb = ps[b], ps[b + 1]
        ra, rb_ = rad_all[b], rad_all[b + 1]
        pats = [p for p in prec if sa + ra + 0.05 < p.sc - p.hw and p.sc + p.hw < sb - rb_ - 0.05]
        wins = [w for w in wrecs if sa < w.s < sb]
        placed_p += len(pats)
        fine = ([(p.sc - p.hw - 0.08, p.sc + p.hw + 0.08, grid[2]) for p in pats]
                + [(w.s - w.hx - 0.06, w.s + w.hx + 0.06, grid[2]) for w in wins])
        lo, hi = sa + 0.04, sb - 0.04
        Sv = _graded(lo, hi, grid[0], fine)
        if wins:
            Sv = np.unique(np.round(np.concatenate([Sv] + [[w.s - w.hx, w.s + w.hx] for w in wins]), 5))
            Sv = Sv[(Sv >= lo - 1e-9) & (Sv <= hi + 1e-9)]
        zl = zl_f(Sv) - 0.05
        zh = zh_f(Sv)
        nv = int(math.ceil(float((zh - zl).max()) / grid[1])) + 1
        Vv = np.linspace(0.0, 1.0, nv)
        nu = len(Sv)
        S = np.repeat(Sv[:, None], nv, 1)
        Z = zl[:, None] + Vv[None, :] * (zh - zl)[:, None]
        zfoot = (zl + 0.05)[:, None]
        # fields
        fo = np.full(S.shape, 9.0)
        for w in wins:
            fo = np.minimum(fo, w.f(S, Z))
        fp = np.full(S.shape, 9.0)
        for p in pats:
            fp = np.minimum(fp, p.f(S, Z))
        # coat thickness
        P3 = np.stack([S * 1.7, Z * 1.7, np.full(S.shape, b * 1.31 + seed * 0.37)], -1)
        bul = fbm(P3, 2, gain=0.45)
        bul = (bul - bul.mean()) / max(float(bul.std()), 1e-6)
        T = COAT + 0.0062 * np.clip(bul, -2.2, 2.2)
        z_sag = float(zl.min()) + 0.5 + 0.3 * ((b * 0.618) % 1.0)
        T = T + (0.008 + 0.004 * n2(S * 1.3, np.full(S.shape, 0.5), seed + b)) * np.exp(-((Z - z_sag) / 0.28) ** 2)
        xl, xr = S - sa, sb - S
        dfl = np.minimum(xl - ra, xr - rb_)
        area = (hi - lo) * float((zh - zl).mean())
        rl = np.random.RandomState(seed * 31 + b)
        lump = np.zeros(S.shape)
        for _ in range(int(round(area * rl.uniform(*lumps)))):
            c_s = rl.uniform(lo + 0.1, hi - 0.1)
            c_z = rl.uniform(float(zl.min()) + 0.2, float(zh.max()) - 0.1)
            sg = rl.uniform(0.045, 0.08)
            el = rl.uniform(1.0, 1.6)
            A = rl.uniform(0.020, 0.025)
            r2 = ((S - c_s) / (sg * el)) ** 2 + ((Z - c_z) / sg) ** 2
            m = r2 < 9.0
            if m.any():
                lump += A * np.where(((Z - c_z) / sg) < 0, np.exp(-0.75 * r2), np.exp(-0.5 * r2)) * m
        fade = smoothstep(0.03, 0.14, dfl) * smoothstep(0.04, 0.14, fp) * smoothstep(0.02, 0.12, fo)
        T = T + lump * fade
        zone = 1 - smoothstep(0.07, 0.11, dfl)                      # the shrinkage slit beside every post
        T = T - (0.012 + 0.008 * np.clip(0.5 + 0.6 * n2(Z * 4.0, np.full(S.shape, b * 1.0), seed + 21), 0, 1)) * zone
        cap_l = np.where(xl < ra, POST_OUT + np.sqrt(np.clip(ra * ra - xl * xl, 0, None)) - 0.012, 9.0)
        cap_r = np.where(xr < rb_, POST_OUT + np.sqrt(np.clip(rb_ * rb_ - xr * xr, 0, None)) - 0.012, 9.0)
        T = np.minimum(T, np.minimum(cap_l, cap_r))
        T = T - 0.04 * (1 - smoothstep(zfoot - 0.03, zfoot + 0.03, Z))     # the bedded foot tucks into the stone / sill
        T = T - 0.032 * smoothstep(zh[:, None] - 0.09, zh[:, None], Z)      # the head tucks under the thatch
        T = np.where(fp < 0.09, np.maximum(T, 0.05), T)                    # the coat stands over the exposed rods
        T = np.where(fp < 0.0, EDGE_T, T)                                  # the broken face of a patch margin
        T = np.maximum(T, 0.0)
        pt, nn = run.f(S.ravel())
        Pv = np.concatenate([pt + nn * T.ravel()[:, None], Z.ravel()[:, None]], 1)
        F = grid_quads(nu, nv)
        neg_o, neg_p = (fo < 0).ravel(), (fp < 0).ravel()
        keep = ~(neg_o[F].all(1) | neg_p[F].all(1))
        F = F[keep]
        if len(F):
            q = Pv[F[0]]
            nmid = np.cross(q[1] - q[0], q[3] - q[0])
            nout = np.append(nn[len(nn) // 2], 0.0)
            if float(nmid @ nout) < 0:
                F = F[:, ::-1]
            acc_c.add(Pv, F, "M_daub")
        # ---- the weave, only where the coat is broken (and ~6 cm under its margin)
        if pats:
            def hide(s_, z_, _pats=pats, _wins=wins):
                s_ = np.asarray(s_, float)
                z_ = np.asarray(z_, float)
                f_ = np.full(np.broadcast(s_, z_).shape, 9.0)
                for p in _pats:
                    f_ = np.minimum(f_, p.f(s_, z_))
                hb = (f_ > 0.06) | (z_ > zh_f(s_) - 0.05)
                for w in _wins:
                    hb |= w.f(s_, z_) < 0.02
                return hb
            n_rods += weave_panel(g, acc_r, acc_r, run.f, sa, sb, float(zl.min()) + 0.05, float(zh.max()),
                                  seed * 1000 + b * 17, hide=hide, trim=(0.075, 0.075), knots=0.0)
        # ---- the inner skin (dark backing behind the weave; the wall seen through a window): a coarse sheet
        Sb = _graded(sa, sb, 0.25, [(w.s - w.rb["hx"] - 0.1, w.s + w.rb["hx"] + 0.1, 0.0125) for w in wins])
        if wins:
            Sb = np.unique(np.round(np.concatenate([Sb] + [[w.s - w.rb["hx"], w.s + w.rb["hx"]] for w in wins]), 5))
        zlb, zhb = zl_f(Sb) - 0.05, zh_f(Sb)
        nvb = int(math.ceil(float((zhb - zlb).max()) / 0.025)) + 1
        Sg = np.repeat(Sb[:, None], nvb, 1)
        Zg = zlb[:, None] + np.linspace(0, 1, nvb)[None, :] * (zhb - zlb)[:, None]
        pb, nb_ = run.f(Sg.ravel())
        Pb = np.concatenate([pb - nb_ * INNER, Zg.ravel()[:, None]], 1)
        Fb = grid_quads(len(Sb), nvb)
        hole = np.zeros(Sg.shape, bool)
        for w in wins:
            hole |= (np.abs(Sg - w.s) < w.rb["hx"] + 0.0001) & (Zg > w.rb["z0"] - 0.0001) & (Zg < w.rb["z1"] + 0.0001)
        Fb = Fb[~hole.ravel()[Fb].all(1)]
        if len(Fb):
            q = Pb[Fb[0]]
            if float(np.cross(q[1] - q[0], q[3] - q[0]) @ np.append(nb_[len(nb_) // 2], 0.0)) < 0:
                Fb = Fb[:, ::-1]
            acc_b.add(Pb, Fb, "M_daub")
    acc_c.build(g.coll)
    out["daub"] = f"{g.prefix}_{name}_daub"
    if n_rods:
        acc_r.build(g.coll)
        out["rods"] = f"{g.prefix}_{name}_wattle_rods"
    acc_b.build(g.coll)
    log(f"  {name}: {nb} bays, {len(posts)} posts, {placed_p}/{len(prec)} patches, {len(wrecs)} windows, rods {n_rods}")

    # ---- windows (wall_openings) ---------------------------------------------------------------------------------
    if wrecs:
        accs = opening_accs(g, f"{name}_win")
        orng = np.random.default_rng(seed + 11)
        for k, w in enumerate(wrecs):
            pt, nn = run.f(np.array([w.s]))
            p2, _ = run.f(np.array([w.s + 0.02]))
            p1, _ = run.f(np.array([w.s - 0.02]))
            t = nrm(np.append(p2[0] - p1[0], 0.0))
            n = np.append(nn[0], 0.0)
            O = np.append(pt[0] + nn[0] * COAT, 0.0)
            build_opening(g, w.spec, O, t, n, accs, orng, label=f"{name}_win{k}")
        finish_accs(g, accs)

    # ---- the sill beam (straight runs) -----------------------------------------------------------------------------
    if sill and run.kind == "line":
        acc_s = g.acc(f"{name}_sill", 20)
        s_lo, s_hi = posts[0], posts[-1]
        for k, (a, bb) in enumerate(zip(run.cum[:-1], run.cum[1:])):
            a_, b_ = max(float(a), s_lo), min(float(bb), s_hi)
            if b_ - a_ < 0.2:
                continue
            ea = 0.06 if (a_ > s_lo + 1e-6 or k > 0) else 0.0
            eb = 0.06 if (b_ < s_hi - 1e-6 or k < len(run.cum) - 2) else 0.0
            a_ -= ea
            b_ += eb
            mid = 0.5 * (a_ + b_)
            pm, nm = run.f(np.array([0.5 * (float(a) + float(bb))]))
            pc, _ = run.f(np.array([mid]))
            t3 = nrm(np.append(run.f(np.array([mid + 0.01]))[0][0] - run.f(np.array([mid - 0.01]))[0][0], 0.0))
            n3 = np.append(nm[0], 0.0)
            hz_ = float(zl_f(mid)) + 0.01
            center = np.append(pc[0] + nm[0] * (POST_OUT + 0.09 - sill_half[0] + 0.02), hz_)
            R = np.column_stack([t3, -n3, ez])
            timber_box(acc_s, center, (0.5 * (b_ - a_), sill_half[0], sill_half[1]), R, ch=0.022, noise=0.0045,
                       seed=seed * 17 + k)
        acc_s.build(g.coll)
        out["sill"] = f"{g.prefix}_{name}_sill"
    return out


__all__ = ["line_run", "arc_run", "even_posts", "polyline_posts", "path_daub", "COAT"]

