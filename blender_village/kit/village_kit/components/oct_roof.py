"""components.oct_roof -- tiered octagonal bell-cast roofs: the skirt roof and the bell caps (kit 1.1.0, from the
hilltop keep).

Every roof here is an oct_frame.OctRoof surface (octagonal, bell-cast eave kick, concave hips, eave wave, sag).

covering_boards(roof, acc, ...)   horizontal courses of long boards (SIZE_TABLE 'skirt_board') between slope coords:
                                  staggered, jittered, slipped / missing units, curl at the eave; every unit keeps only
                                  its exposed part + a short tuck (producer note 6) except where the covered part shows;
                                  scribe(x, y) cuts the units obliquely along an adjoining roof (a thatch valley)
cap_shingles(roof, acc, rng, p_top)   the village's CHUNKY shingles on a bell cap (shingles.shingle_mesh, SIZE_TABLE
                                  'shingle' 0.35-0.55 m wide, 3.4-4.2 cm butts, 'shingle_apex' for the top 3 courses,
                                  doubled 'starter' course at the eave): horizontal courses bent onto the bell-cast facets,
                                  staggered joints, 2 % missing / 3 % slipped, curled eave course
sarking_deck(...)                 continuous 2 cm deck under a covering on all 8 facets (no hole ever shows sky)
hip_boards(...)                   saddle boards along the 8 hips (SIZE_TABLE 'hip_board')
eave_structure(...)               common / jack / hip rafters with haunched sprocket ends, soffit boards, a fascia with
                                  scarf joints and a low-frequency wave (scribed where a thatch rises over it)
build_cap(...)                    a complete bell cap: covering + hips + structure + deck + carved ring beam + brackets

Public components (g = OctFrame):
    skirt_roof(g, seed=303)       tier 1: <P>_roof_skirt_boards / _hips / _structure / _deck
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, TAN22, ax4, axn, finalize, inst_faces, n1, prof_rect, rbox_v, rot2, sweep
from ..shingles import SHINGLE_VARIANTS, SIZE_TABLE, course_widths, shingle_mesh
from .hewn import hewn_square, peg
from .oct_frame import FR, in_wing, oct_corner, thatch_low, wing_roof_zone


def _hewn(*a, **k):
    return hewn_square(*a, relief=FR.min_relief, dropped=FR.dropped_checks, **k)


def cap_shingles(roof, acc, rng, p_top, m0=-0.03, rot_sd=0.027, frac_missing=0.02, frac_slip=0.03, overlap=0.065,
                 exposure=None, hip_bed=None):
    """chunky shingle courses on all 8 facets of a bell cap (see the module doc), from the eave up to the course
    whose facet is narrower than the apex unit at p_top (the lead hat covers the rest).  Each shingle keeps its
    exposed part + `overlap` of covered length (producer note 6; the sarking deck backs every gap) except the eave
    courses and the ones under a missing / slipped shingle.  rot_sd: course-line jitter (director round 6: halved so
    the horizontal courses read at 15 m).  Returns (number of shingles, height of the covering top over the roof
    surface: where the hip boards sit).
    kit 1.3.0 (keep round 8): exposure=(lo, hi) overrides the SIZE_TABLE exposure (the keep's caps use 0.24-0.28 so
    ~12 courses read as in ref1, the unit widths stay chunky); hip_bed=(h_bed, w_pos[8], w_neg[8]) seats flat hip
    saddles: inside each facet's hip strips (w_pos at +x, w_neg at -x) the shingles are pressed down to just under
    h_bed (a 3 cm ramp outside), so the saddle board beds with no shadow gap and no butt pokes through it."""
    T = SIZE_TABLE["shingle"]
    expo_rng = T["exposure"] if exposure is None else exposure
    TA = SIZE_TABLE["shingle_apex"]
    ST = SIZE_TABLE["starter"]
    L_full = T["length"]
    B_WEDGE, B0 = 0.066, 0.037            # stacking wedges as on the hut cone (2 layers under every course)

    def place(k, x0, x1, mb, Lk, var, phi, lift, curl, base_fn, closed=True, wear=None, ys=None):
        W = x1 - x0
        P, F, uv = shingle_mesh(W, Lk, var, curl=curl, ys=ys, bottom=closed, head=closed)
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        c, s_ = math.cos(phi), math.sin(phi)
        xr = x * c - y * s_ + 0.5 * (x0 + x1)
        yr = x * s_ + y * c
        v = np.clip(y / L_full, 0, 1)
        m = mb + yr
        p = np.maximum(roof.p_of_m(m), 0.02)
        xh = p * TAN22 + 0.004
        xr = np.clip(xr, -xh, xh)
        h = base_fn(v) + z + lift * (1 - v)
        if hip_bed is not None:
            hb, wp_, wn_ = hip_bed
            edge = p * TAN22
            out_p = (edge - wp_[k] - 0.01) - xr          # > 0: inward of the +x saddle's footprint
            out_n = xr + (edge - wn_[k] - 0.01)          # > 0: inward of the -x saddle's footprint
            o_ = np.minimum(out_p, out_n)
            cap_h = hb - 0.004 + np.clip(o_ / 0.03, 0, 1) * 0.08
            h = np.minimum(h, cap_h)
        W3 = roof.world(np.full(len(xr), k), xr, p, h)
        acc.add(W3, F, "M_roof_shingle", uv, wear=wear)

    # ---- course layout: exposure 0.30-0.40 per course, up to the apex
    m_stop = float(roof.m_of_p(p_top))
    courses = []
    mb = m0
    while mb < m_stop:
        e_ = rng.uniform(*expo_rng)
        courses.append((mb, e_))
        mb += e_
    nC = len(courses)
    n_sh = 0
    full_under = set()
    recs = []
    for ci, (mb, e_) in enumerate(courses):
        p_mid = float(roof.p_of_m(mb + 0.5 * e_))
        xh = p_mid * TAN22 + 0.06
        apex = ci >= nC - TA["courses_below_collar"]
        tw = TA["target_w"] if apex else T["target_w"]
        n_u = max(1, int(round(2 * xh / tw)))
        for k in range(8):
            w, gaps = course_widths(rng, 2 * xh, n_u, T["w_jitter"], T["gap"])
            x = -xh + rng.uniform(-0.5, 0.5) * w[0] * 0.5          # staggered joints course to course
            for i in range(n_u):
                x0, x1 = x, x + w[i]
                x += w[i] + gaps[i]
                ri = rng.uniform()
                rec = dict(ci=ci, k=k, x0=x0, x1=x1, mb=mb + rng.normal(0, 0.012), var=int(rng.integers(16)),
                           phi=rng.normal(0, rot_sd), lift=rng.uniform(0.0, 0.012), slip=0.0, missing=False)
                if 0 < ci < nC - 1 and ri < frac_missing:
                    rec["missing"] = True
                    full_under.add((ci - 1, k, round(0.5 * (x0 + x1), 2)))
                elif ci > 0 and ri < frac_missing + frac_slip:
                    rec["slip"] = rng.uniform(0.04, 0.09)
                    rec["lift"] += 0.012
                recs.append(rec)
    # ---- doubled starter course at the eave (its underside is seen from below)
    for k in range(8):
        p0 = float(roof.p_of_m(m0 + 0.2))
        xh = p0 * TAN22 + 0.06
        n_u = max(1, int(round(2 * xh / ST["target_w"])))
        w, gaps = course_widths(rng, 2 * xh, n_u, ST["w_jitter"], ST["gap"])
        x = -xh + rng.uniform(0, 0.5) * w[0] * 0.5
        for i in range(n_u):
            var = dict(SHINGLE_VARIANTS[int(rng.integers(16))])
            var["Tb"], var["cup"] = ST["butt"], 0.002
            place(k, x, x + w[i], m0 + 0.012, ST["length"], var, rng.normal(0, 0.01), 0.0, 0.0, lambda v: 0.0 * v,
                  ys=[0.0, 0.006, 0.018, 0.04, 0.12, ST["length"]])
            x += w[i] + gaps[i]
            n_sh += 1
    # ---- the courses
    for r in recs:
        if r["missing"]:
            continue
        ci, k = r["ci"], r["k"]
        xc = 0.5 * (r["x0"] + r["x1"])
        under_hole = any(c_ == ci and k_ == k and abs(xc_ - xc) < 0.5 for (c_, k_, xc_) in full_under)
        e_ = courses[ci][1]
        L_avail = max(m_stop + 0.25 - r["mb"], 0.12)
        full = under_hole or r["slip"] > 0 or ci < 2
        Lk = max(min(L_full if full else e_ + overlap + r["slip"], L_avail, L_full), 0.25)
        var = SHINGLE_VARIANTS[r["var"]]
        curl = var["curl_eave"] if ci < 2 else var["curl"]
        base_fn = (lambda v: B0 * (1 - v)) if ci == 0 else (lambda v: B_WEDGE * (1 - v))
        closed = ci < 2 or full
        wear = 0.9 if r["slip"] > 0 else None
        place(k, r["x0"], r["x1"], r["mb"] - r["slip"], Lk, var, r["phi"], r["lift"], curl, base_fn, closed=closed,
              wear=wear)
        n_sh += 1
    return n_sh, B_WEDGE + T["butt"][1] - 0.018      # hip boards bed on the butt peaks


def covering_boards(roof, acc, mat, rng, m0, m1, expo, W, t, lens, gap, nx=6, nm=5, base_h=0.0,
                    cull=None, p_floor=None, frac_missing=0.02, frac_slip=0.025, curl=0.0, rot_sd=0.02,
                    width_var=None, round_r=0.008, jit_m=0.012, tuck=0.06, scribe=None):
    """Horizontal courses of boards/shingles on an OctRoof between slope coords m0..m1.
    scribe(x, y) -> z: where an adjoining roof rises over this one (wing thatch), every unit is scribed onto it:
    its ends are cut obliquely along the true intersection (butt and tail cut separately), so all course ends
    line up on the valley over the lead apron instead of stepping down as whole dropped boards."""
    recs = []
    missing = []
    base_of = {}
    for k in range(8):
        mb = m0
        ci = 0
        while mb < m1:
            p_b = float(roof.p_of_m(mb + 0.5 * W))
            xh = p_b * TAN22 + 0.06
            x = -xh - rng.uniform(0, lens[1] * 0.6)
            while x < xh:
                L = rng.uniform(*lens)
                if width_var is not None:
                    L = float(np.clip(rng.normal(width_var[0], width_var[1]), lens[0], lens[1]))
                x0, x1 = x, x + L - gap
                x = x + L
                if x1 < -xh or x0 > xh:
                    continue
                mbb = mb + rng.normal(0, jit_m)
                lift = rng.normal(0, 0.004 + jit_m * 0.2)
                slip = 0.0
                u = rng.uniform()
                if u < frac_missing and ci > 0:
                    missing.append((k, ci, x0, x1))
                    continue
                if u < frac_missing + frac_slip:
                    slip = rng.uniform(0.04, 0.10)
                    lift += 0.006
                recs.append((k, x0, x1, mbb - slip, rng.normal(0, rot_sd), lift, ci, t * rng.uniform(0.85, 1.15), slip,
                             mb))
            base_of[(k, ci)] = mb
            mb += expo * rng.uniform(0.96, 1.04)
            ci += 1
    R = np.array(recs)
    k = R[:, 0].astype(int)
    x0, x1, mb, rot, lift, ci, tt, slp = R[:, 1], R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 6], R[:, 7], R[:, 8]
    # each unit keeps only its exposed length plus a short tuck under the next course (hidden-geometry budget):
    # m_keep = where the next course's butt (worst case jitter) covers it; units under a missing piece keep all
    nxt = np.array([base_of.get((int(k_), int(c_) + 1), np.nan) for k_, c_ in zip(k, ci)])
    m_keep = np.where(np.isnan(nxt), W, nxt - mb + 2.5 * jit_m + 0.012)
    full = np.isnan(nxt)
    for (km, cm, xa, xb) in missing:
        under = (k == km) & (ci == cm - 1) & (x1 > xa - 0.02) & (x0 < xb + 0.02)
        full |= under
    m_keep = np.where(full, W, np.clip(m_keep, 0.05, W - 0.03))
    Wr = np.where(full, W, np.minimum(W, m_keep + tuck))
    xa_b, xb_b, xa_t, xb_t = x0.copy(), x1.copy(), x0.copy(), x1.copy()
    if scribe is not None:
        ns = 48
        f_ = np.linspace(0, 1, ns)
        keep_s = np.ones(len(k), bool)
        for which, mm in ((0, mb), (1, mb + Wr)):
            XS = x0[:, None] + (x1 - x0)[:, None] * f_[None]
            PS = np.broadcast_to(roof.p_of_m(mm)[:, None], XS.shape)
            S3 = roof.world(np.broadcast_to(k[:, None], XS.shape), XS, PS, np.zeros(XS.shape))
            ok = S3[..., 2] > scribe(S3[..., 0], S3[..., 1])
            for i in np.flatnonzero(~ok.all(1)):
                o = ok[i]
                if not o.any():
                    if which == 0:
                        keep_s[i] = False
                    continue
                # longest contiguous valid run
                best, cur, st = (0, -1), 0, 0
                for j_ in range(ns + 1):
                    if j_ < ns and o[j_]:
                        if cur == 0:
                            st = j_
                        cur += 1
                        if cur > best[1] - best[0] + 1:
                            best = (st, j_)
                    else:
                        cur = 0
                a_, b_ = XS[i, best[0]], XS[i, best[1]]
                if which == 0:
                    xa_b[i], xb_b[i] = a_, b_
                    if b_ - a_ < 0.10:
                        keep_s[i] = False
                else:
                    xa_t[i], xb_t[i] = a_, b_
        # a tail cut may not be wider than the butt cut by more than the valley slope allows (no overhangs)
        xa_t = np.where(xb_t - xa_t < 0.05, xa_b, xa_t)
        xb_t = np.where(xb_t - xa_t < 0.05, xb_b, xb_t)
        k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t = [
            a[keep_s] for a in (k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t)]
    if cull is not None:
        pc = roof.p_of_m(mb + W * 0.5)
        C = roof.world(k, 0.5 * (x0 + x1), pc, np.full(len(k), base_h + t))
        keep = ~cull(C)
        k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t = [
            a[keep] for a in (k, x0, x1, mb, rot, lift, ci, tt, Wr, m_keep, full, xa_b, xb_b, xa_t, xb_t)]
    M = len(k)
    rr = np.full(M, round_r)
    X = axn(x0, x1, rr, nx)
    # stations along the slope: butt arris, mid exposure, the cover line (m_keep), tuck end
    mk = np.minimum(mb + m_keep, mb + Wr - rr - 0.004)
    Y = np.stack([mb, mb + rr, 0.5 * (mb + rr + mk), mk, mb + Wr - rr, mb + Wr], 1)
    Z = np.stack([np.zeros(M), tt - rr, tt], 1)
    P, quads = rbox_v(X, Y, Z, rr, skip_back=True, round_back=False)
    x, m, h = P[..., 0], P[..., 1], P[..., 2]
    if scribe is not None:
        # oblique scribed ends: affine remap of x between the butt cut and the tail cut
        fm = np.clip((m - mb[:, None]) / Wr[:, None], 0, 1)
        xa = xa_b[:, None] + (xa_t - xa_b)[:, None] * fm
        xb = xb_b[:, None] + (xb_t - xb_b)[:, None] * fm
        x = xa + (x - x0[:, None]) / (x1 - x0)[:, None] * (xb - xa)
        P = P.copy()
        P[..., 0] = x
    xc = 0.5 * (x0 + x1)[:, None]
    mc = (mb + 0.5 * Wr)[:, None]
    xr, mr = rot2(x - xc, m - mc, rot[:, None])
    x, m = xr + xc, mr + mc
    fr = np.clip((m - mb[:, None]) / W, 0, 1)
    hl = h * (1 - 0.45 * fr) + (tt[:, None] * 0.95 + lift[:, None]) * (1 - fr)
    if curl:
        hl = hl + curl * np.clip(1 - ci[:, None] / 3.0, 0, 1) * (1 - fr) ** 2 * ((x - xc) / (0.5 * (x1 - x0))[:, None]) ** 2
    p = roof.p_of_m(m)
    if p_floor is not None:
        p = np.maximum(p, p_floor)
    xh = p * TAN22 + 0.004
    x = np.clip(x, -xh, xh)
    W3 = roof.world(np.broadcast_to(k[:, None], x.shape), x, p, hl + base_h)
    uv = np.stack([x, m], -1).reshape(-1, 2)
    F = inst_faces(quads, M, P.shape[1]).reshape(M, -1, 4)
    # drop every face of a unit lying wholly under the next course (beyond its cover line)
    ym = P[..., 1]
    qmin = ym[:, quads].min(axis=2)
    hid = (qmin >= (mk - 1e-6)[:, None]) & ~full[:, None]
    acc.add(W3.reshape(-1, 3), F[~hid], mat, uv=uv)
    return M


def sarking_deck(roof, acc, m0, m1, h_top=-0.005, t=0.02, nx=10, dm=0.25, cull=None, p_floor=0.02,
                 mat="M_timber"):
    """Kit component: continuous sarking deck (t thick, top h_top under the covering) on all 8 facets of an
    OctRoof between slope coords m0..m1. Any gap, slipped or missing covering unit shows timber, never sky or the
    interior (producer note 6). cull(P) -> True drops a cell whose 4 top corners are all buried (e.g. under thatch)."""
    nm = max(2, int(math.ceil((m1 - m0) / dm)) + 1)
    ms = np.linspace(m0, m1, nm)
    u = np.linspace(-1.0, 1.0, nx + 1)
    for k in range(8):
        M_, U_ = np.meshgrid(ms, u, indexing="ij")
        p = np.maximum(roof.p_of_m(M_), p_floor)
        x = U_ * p * TAN22
        top = roof.world(np.full(x.shape, k), x, p, np.full(x.shape, h_top))
        bot = roof.world(np.full(x.shape, k), x, p, np.full(x.shape, h_top - t))
        a, b = top.shape[:2]
        idx = np.arange(a * b).reshape(a, b)
        q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
        if cull is not None:
            Tf = top.reshape(-1, 3)
            buried = np.all(cull(Tf[q]), axis=1)
            q = q[~buried]
        if not len(q):
            continue
        V = np.concatenate([top.reshape(-1, 3), bot.reshape(-1, 3)])
        n = a * b
        F = [q, q[:, ::-1] + n]
        # closed edges along the lowest row (the deck's eave edge) and the hip sides
        e0 = idx[0, :]
        F.append(np.stack([e0[1:], e0[:-1], e0[:-1] + n, e0[1:] + n], -1))
        for col in (idx[:, 0], idx[:, -1]):
            F.append(np.stack([col[:-1], col[1:], col[1:] + n, col[:-1] + n], -1))
        uv = np.concatenate([np.stack([x.ravel(), M_.ravel()], -1)] * 2)
        acc.add(V, F, mat, uv=uv)


def hip_boards(roof, acc, mat, rng, p_lo, p_hi, w, t, h0, piece=(0.8, 1.3), cull=None):
    """Saddle boards along the 8 hips from p_lo (lip) up to p_hi."""
    recs = []
    for k in range(8):
        for side in (0, 1):
            p = p_lo + 0.02
            while p > p_hi + 0.05:
                L = rng.uniform(*piece)
                pa, pb = p, max(p - L * 0.75, p_hi)
                recs.append((k, side, pa, pb, w * rng.uniform(0.9, 1.1), t, rng.normal(0, 0.004)))
                p = pb + 0.03
    R = np.array(recs)
    M = len(R)
    k, side = R[:, 0].astype(int), R[:, 1].astype(int)
    pa, pb, ww, tt, lift = R[:, 2], R[:, 3], R[:, 4], R[:, 5], R[:, 6]
    rr = np.full(M, 0.007)
    X = axn(pb, pa, rr, 8)
    Y = axn(np.zeros(M), ww, rr, 4)
    Z = axn(np.zeros(M), tt, rr, 3)
    P, quads = rbox_v(X, Y, Z, rr)
    p, a, h = P[..., 0], P[..., 1], P[..., 2]
    sgn = np.where(side == 0, 1.0, -1.0)[:, None]
    # side 0 on facet k (x = +hip), side 1 on facet k+1 (x = -hip); side 1 sits higher & overlaps
    kk = np.where(side == 0, k, (k + 1) % 8)[:, None]
    x = sgn * (p * TAN22 - a + np.where(side == 1, -0.025, 0.0)[:, None])
    hh = h0 + h + lift[:, None] + np.where(side == 1, tt * 0.6, 0.0)[:, None] + 0.02 * a / ww[:, None]
    W3 = roof.world(np.broadcast_to(kk, x.shape), x, p, hh)
    if cull is not None:
        keep = ~cull(W3.mean(1))
        W3 = W3[keep]
        P = P[keep]
        M = len(W3)
    acc.add(W3.reshape(-1, 3), inst_faces(quads, M, P.shape[1]), mat,
            uv=np.stack([P[..., 0], P[..., 1]], -1).reshape(-1, 2))


def hip_saddles(roof, acc, mat, p_lo, p_hi, W, T, h_bed, lap=0.03, chamfer=0.01, bed=0.02, n_st=40):
    """kit 1.3.0 (keep round 8, director r7 must-fix 3): exactly ONE saddle pair per hip -- two flat continuous
    boards of rectangular section (W[k, side] wide, T[k, side] thick, `chamfer` arrises), bedded at h_bed over the
    roof surface on their own `bed`-deep packing (the board solid runs down into the pressed shingles, so no shadow
    gap opens under it).  Side 0 lies on facet k and laps `lap` past the hip line; side 1 (facet k+1) closes
    against it, set 0.4 T higher.  The boards follow the bell curve with n_st stations."""
    recs = []
    for k in range(8):
        for side in (0, 1):
            recs.append((k, side, W[k, side], T[k, side]))
    R = np.array(recs)
    M = len(R)
    k, side = R[:, 0].astype(int), R[:, 1].astype(int)
    ww, tt = R[:, 2], R[:, 3]
    rr = np.full(M, chamfer)
    X = axn(np.full(M, p_hi), np.full(M, p_lo), rr * 0.5, n_st)
    Y = axn(np.zeros(M), ww + np.where(side == 0, lap, 0.004), rr, 4)
    Z = axn(np.full(M, -bed), tt, rr, 4)
    P, quads = rbox_v(X, Y, Z, rr)
    p, a, h = P[..., 0], P[..., 1], P[..., 2]
    sgn = np.where(side == 0, 1.0, -1.0)[:, None]
    kk = np.where(side == 0, k, (k + 1) % 8)[:, None]
    e = np.where(side == 0, lap, 0.004)[:, None]
    x = sgn * (p * TAN22 + e - a)
    hh = h_bed + h + np.where(side == 1, 0.4 * tt, 0.0)[:, None]
    W3 = roof.world(np.broadcast_to(kk, x.shape), x, np.maximum(p, 0.02), hh)
    acc.add(W3.reshape(-1, 3), inst_faces(quads, M, P.shape[1]), mat,
            uv=np.stack([P[..., 0], P[..., 1]], -1).reshape(-1, 2))


def eave_structure(roof, acc_r, acc_s, acc_f, rng, p_wall, z_plate_top, sheath_t, n_raft, rw, rd_tip,
                   cull=None, fascia_h=0.18, fascia_t=0.04, soffit_w=(0.17, 0.24), mat_r="M_timber", scribe=None,
                   fascia_joint=(2.5, 4.0), fascia_wave=0.0):
    """rafters (incl. jacks & hips), soffit/sheathing boards and fascia under an OctRoof eave."""
    pl = roof.p_lip
    sp = 2 * p_wall * TAN22 / n_raft
    # common & jack rafters
    jmax = int(math.ceil(pl * TAN22 / sp)) + 1
    for k in range(8):
        for j in range(-jmax, jmax + 1):
            xj = (j + 0.5) * sp if n_raft % 2 == 0 else j * sp
            if abs(xj) > pl * TAN22 - 0.12:
                continue
            p_start = max(p_wall - 0.10, abs(xj) / TAN22 + 0.07)
            p_end = pl - fascia_t - 0.005
            if p_end - p_start < 0.15:
                continue
            _rafter(roof, acc_r, rng, k, xj, p_start, p_end, p_wall, z_plate_top, sheath_t, rw, rd_tip, False, cull, mat_r)
        # hip rafter
        _rafter(roof, acc_r, rng, k, None, p_wall - 0.10, pl - fascia_t - 0.02, p_wall, z_plate_top, sheath_t,
                rw * 1.2, rd_tip * 1.1, True, cull, mat_r)
    # soffit / sheathing boards (visible from below between rafters)
    m_wall = float(roof.m_of_p(p_wall - 0.10))
    m = -0.005
    recs = []
    while m < m_wall:
        wd = rng.uniform(*soffit_w)
        for k in range(8):
            recs.append((k, m, min(wd - 0.006, m_wall - m + 0.02)))
        m += wd
    R = np.array(recs)
    M = len(R)
    k = R[:, 0].astype(int)
    m0, wd = R[:, 1], R[:, 2]
    rr = np.full(M, 0.004)
    xh = pl * TAN22 + 0.05
    X = axn(np.full(M, -xh), np.full(M, xh), rr, 9)
    Y = axn(m0, m0 + wd, rr, 4)
    Z = axn(np.full(M, -sheath_t), np.zeros(M), rr, 3)
    P, quads = rbox_v(X, Y, Z, rr, skip_front=True)               # top face is under the covering
    x, mm, h = P[..., 0], P[..., 1], P[..., 2]
    p = roof.p_of_m(mm)
    x = np.clip(x, -p * TAN22, p * TAN22)
    W3 = roof.world(np.broadcast_to(k[:, None], x.shape), x, p, h)
    if cull is not None:
        keep = ~cull(W3.mean(1))
        W3, P = W3[keep], P[keep]
    acc_s.add(W3.reshape(-1, 3), inst_faces(quads, len(W3), P.shape[1]), "M_timber",
              uv=np.stack([P[..., 0], P[..., 1]], -1).reshape(-1, 2))
    # fascia: boards at the lip, mitred at the hips, following the kicked eave; hand-fitted lengths with butt /
    # scarf joints every 2.5-4 m, low-frequency wave; where an adjoining roof (wing thatch) rises over the eave the
    # board is scribed down onto that surface and ends there (no floating cut ends)
    for k in range(8):
        n = 40
        xh = pl * TAN22
        xs = np.linspace(-xh, xh, n)
        # joints along this facet (absolute x positions)
        cuts = []
        xj = -xh + rng.uniform(0.6, 1.8)
        while xj < xh - 0.6:
            cuts.append(xj)
            xj += rng.uniform(*fascia_joint)
        xs = np.unique(np.concatenate([xs, np.array(cuts) - 0.004, np.array(cuts) + 0.004]))
        n = len(xs)
        pf0, pf1 = pl - fascia_t, pl + 0.002
        top = roof.world(np.full(n, k), xs, np.full(n, pl), np.zeros(n))[:, 2] + 0.004
        seg_id = np.searchsorted(np.array(cuts), xs)
        wv = fascia_wave * n1(xs * 0.9 + k * 3.1, 77 + k) + 0.006 * (seg_id % 2) * fascia_wave / 0.02 \
            + 0.004 * n1(seg_id * 1.7 + k, 91) * (fascia_wave > 0)
        V = []
        for pp in (pf0, pf1):
            for zoff in (-fascia_h, 0.0):
                xx = np.clip(xs, -pp * TAN22, pp * TAN22)
                S = roof.surf(np.full(n, k), xx, np.full(n, pp))
                S[:, 2] = top + zoff + wv
                V.append(S)
        V = np.stack(V, 1)  # n, 4 (inner-bot, inner-top, outer-bot, outer-top)
        if scribe is None:
            if cull is not None and cull(V.reshape(-1, 3).mean(0)[None])[0]:
                continue
            keep = np.ones(n, bool)
        else:
            zt = scribe(V[:, 2, :2])
            keep = zt < V[:, 1, 2] - 0.03
            bot = np.maximum(V[:, [0, 2], 2], zt[:, None])
            V[:, 0, 2], V[:, 2, 2] = bot[:, 0], bot[:, 1]
        # split into board runs at joints and at buried sections
        brk = np.zeros(n, bool)
        for c in cuts:
            brk |= np.isclose(xs, c + 0.004)
        runs, cur = [], []
        for i in range(n):
            if not keep[i] or brk[i]:
                if len(cur) >= 2:
                    runs.append(cur)
                cur = [i] if keep[i] else []
            else:
                cur.append(i)
        if len(cur) >= 2:
            runs.append(cur)
        ring = [0, 2, 3, 1]
        for run in runs:
            Vr = V[run][:, ring, :]
            m_ = len(run)
            i = np.arange(m_ - 1)[:, None]
            jj = np.arange(4)[None, :]
            a = i * 4 + jj
            b = i * 4 + (jj + 1) % 4
            quads = np.stack([a, b, b + 4, a + 4], -1).reshape(-1, 4)
            caps = [np.array([[0, 3, 2, 1]]), ((m_ - 1) * 4 + np.array([[0, 1, 2, 3]]))]
            acc_f.add(Vr.reshape(-1, 3), [quads] + caps, "M_timber",
                      uv=np.stack([np.repeat(xs[run], 4), np.tile([0, 0.04, 0.22, 0.18], m_)], -1))


def _rafter(roof, acc, rng, k, xj, p0, p1, p_wall, z_plate, sheath_t, rw, rd_tip, hip, cull, mat):
    n = 12
    us = np.linspace(0, 1, n)
    M = 1
    r = 0.016
    X = axn(np.zeros(1), np.ones(1), np.array([0.03]), 8)
    Y = ax4(np.array([rw / 2]), np.array([r]))
    Z = ax4(np.array([0.5]), np.array([0.06]))
    P, quads = rbox_v(X, Y, Z, np.array([r]), skip_front=True)     # the top face lies under the sheathing
    P = P[0]
    u, a, v = P[:, 0], P[:, 1], P[:, 2] + 0.5   # v in [0,1]
    p = p0 + (p1 - p0) * u
    if hip:
        x = p * TAN22
        hipdir = np.array([math.cos(roof.phi[k] + math.radians(22.5)), math.sin(roof.phi[k] + math.radians(22.5))])
        across = np.array([-hipdir[1], hipdir[0]])
        top = roof.world(np.full_like(p, k), x, p, np.full_like(p, -sheath_t))
        top = top - 0.012 * np.array([0, 0, 1.0])
        xy = roof.surf(np.full_like(p, k), x, p)[:, :2] + a[:, None] * across[None]
    else:
        x = np.full_like(p, xj)
        top = roof.world(np.full_like(p, k), x + a, p, np.full_like(p, -sheath_t))
        xy = top[:, :2]
    ztop = top[:, 2]
    # depth: tip rd_tip, deepening (haunched sprocket) to bear on the plate at the wall line
    z_tip_bot = ztop - rd_tip
    pw = p_wall + 0.06
    wl = np.clip((roof.p_lip - p) / max(roof.p_lip - pw, 1e-3), 0, 1)
    # smooth concave (haunched) underside from the tip down to the plate bearing
    zb_plate = np.full_like(p, z_plate)
    blend = wl ** 2.2
    zbot = np.where(p < pw, np.minimum(zb_plate, z_tip_bot), z_tip_bot * (1 - blend) + zb_plate * blend)
    zbot = np.minimum(zbot, ztop - rd_tip)
    W = np.zeros((len(P), 3))
    W[:, :2] = xy
    W[:, 2] = zbot + v * (ztop - zbot)
    if cull is not None and cull(W.mean(0)[None])[0]:
        return
    acc.add(W, quads, mat, uv=np.stack([u * (p1 - p0), a + v * 0.1], -1))


def build_cap(coll, roof, prefix, rng, p_wall, z_plate, n_raft, p_top, expo, W, t, lens, bracket_z0, chunky=True,
              saddles=False, cap_exposure=None):
    """bell cap on an OctRoof: covering, hip boards, eave structure (rafters, soffit, fascia), sarking deck, carved
    ring beam with pegged laps and curved corner brackets.  chunky=True: the village's chunky shingles
    (cap_shingles, SIZE_TABLE 'shingle' / 'shingle_apex' / 'starter'; ensemble review 1); chunky=False: the phase-1
    fine board courses (expo / W / t / lens).  Returns the covering's vertices (for fitting the lead hat).
    kit 1.3.0: saddles=True (with chunky) lays ONE flat saddle pair per hip (hip_saddles, 14-18 cm x 2.5-3.5 cm,
    1 cm chamfers) bedded into pressed shingles instead of the hip_boards runs; cap_exposure=(lo, hi) sets the
    cap's course exposure."""
    acc = Acc(f"{prefix}_shingles")
    acch = Acc(f"{prefix}_hips")
    accs = Acc(f"{prefix}_structure")
    if chunky and saddles:
        rs = np.random.default_rng(int(rng.integers(1 << 30)))
        Wsd = rs.uniform(0.14, 0.18, (8, 2))
        Tsd = rs.uniform(0.025, 0.035, (8, 2))
        h_bed = 0.072
        w_pos = Wsd[:, 0] + 0.03                         # side 0 of hip k lies on facet k (+x), lapping 3 cm
        w_neg = Wsd[(np.arange(8) - 1) % 8, 1]           # side 1 of hip k-1 lies on facet k (-x)
        n, h_top = cap_shingles(roof, acc, rng, p_top, exposure=cap_exposure, hip_bed=(h_bed, w_pos, w_neg))
        hip_saddles(roof, acch, "M_roof_shingle", roof.p_lip + 0.02, p_top, Wsd, Tsd, h_bed)
    elif chunky:
        n, h_top = cap_shingles(roof, acc, rng, p_top)
        hw, ht = SIZE_TABLE["hip_board"]["cap"]
        hip_boards(roof, acch, "M_roof_shingle", rng, roof.p_lip + 0.02, p_top, hw, ht, h_top, piece=(0.5, 0.8))
    else:
        m_top = float(roof.m_of_p(p_top))
        n = covering_boards(roof, acc, "M_roof_shingle", rng, -0.03, m_top, expo=expo, W=W, t=t, lens=lens, gap=0.007,
                            nx=4, nm=4, frac_missing=0.02, frac_slip=0.03, curl=0.012, rot_sd=0.055, p_floor=0.03,
                            jit_m=0.02)
        hip_boards(roof, acch, "M_roof_shingle", rng, roof.p_lip + 0.02, p_top, 0.08, 0.02, 0.032, piece=(0.5, 0.8))
    log(f"  {prefix} shingles", n)
    eave_structure(roof, accs, accs, accs, rng, p_wall=p_wall, z_plate_top=z_plate, sheath_t=0.02, n_raft=n_raft,
                   rw=0.07, rd_tip=0.09, fascia_h=0.11, fascia_t=0.03, soffit_w=(0.12, 0.17), fascia_wave=0.006)
    # sarking deck under the shingles from just inside the plate line to the lead hat
    accdk = Acc(f"{prefix}_deck")
    sarking_deck(roof, accdk, float(roof.m_of_p(p_wall - 0.10)) - 0.03, float(roof.m_of_p(0.04)), h_top=-0.004,
                 t=0.018, nx=6, dm=0.2, p_floor=0.03)
    finalize(accdk, coll)
    # carved eave ring beam + corner brackets
    for k in range(8):
        phi = math.radians(45 * k) + roof.rot
        n3 = np.array([math.cos(phi), math.sin(phi), 0])
        t3 = np.array([-math.sin(phi), math.cos(phi), 0])
        ca = np.array([*(roof.c + oct_corner(p_wall + 0.05, k, -1)), z_plate - 0.06])
        cb = np.array([*(roof.c + oct_corner(p_wall + 0.05, k, 1)), z_plate - 0.06])
        ca[:2] = roof.c + rot2(*(ca[:2] - roof.c), roof.rot)
        cb[:2] = roof.c + rot2(*(cb[:2] - roof.c), roof.rot)

        # one hewn ring-beam piece per facet: butted at one corner, lapped 0.12 m past the other with a peg
        dzk = rng.uniform(-0.008, 0.008) + (0.012 if k % 2 else -0.012)
        Lk = float(np.linalg.norm(cb - ca)) + 0.13
        _hewn(accs, ca + t3 * 0.004 + np.array([0, 0, dzk]), t3, n3, np.array([0, 0, 1.0]), Lk, 0.12, 0.12, rng,
                    chamfer=0.016, nf=2, st_len=0.08, adze=0.003, wave=0.003, seed=200 + k)
        peg(FR, cb + t3 * 0.06 + n3 * 0.062 + np.array([0, 0, dzk]), n3, rad=0.011, proud=0.012)
        # bracket at the corner (curved), from the post below out to the hip rafter
        cd = np.array([*(rot2(*oct_corner(1.0, k, 1), roof.rot))])
        cd = np.array([cd[0], cd[1], 0]) / np.linalg.norm(cd)
        base = np.array([*(roof.c + cd[:2] * (p_wall / math.cos(math.radians(22.5)) - 0.04)), bracket_z0])
        top = np.array([*(roof.c + cd[:2] * (p_wall / math.cos(math.radians(22.5)) + 0.35)), z_plate + 0.02])
        ctrl = np.array([base[0], base[1], top[2]])
        us = np.linspace(0, 1, 10)
        path = ((1 - us) ** 2)[:, None] * base + (2 * us * (1 - us))[:, None] * ctrl + (us ** 2)[:, None] * top
        tg = np.array([-cd[1], cd[0], 0])
        V, F = sweep(path, tg, prof_rect(0.08, 0.09, 0.012))
        accs.add(V, F, "M_timber")
    Vsh = np.concatenate(acc.V) if acc.V else np.zeros((0, 3))
    finalize(acc, coll)
    finalize(acch, coll)
    finalize(accs, coll)
    return Vsh


def build_skirt(coll, seed=303):
    rng = np.random.default_rng(seed)
    acc = Acc(FR.prefix + "_roof_skirt_boards")
    acc_h = Acc(FR.prefix + "_roof_skirt_hips")
    acc_r = Acc(FR.prefix + "_roof_skirt_structure")
    cull = lambda C: wing_roof_zone(C, 0.03)

    def board_scribe(x, y):
        inside = (x > FR.WX_W - FR.W_OVH - 0.05) & (x < FR.WX_E + FR.W_OVH + 0.05) & (y > FR.WY_S - FR.W_OVH - 0.05) & \
            (y < FR.WY_N + FR.W_OVH + 0.05)
        return np.where(inside, thatch_low(x, y) + 0.035, -10.0)
    m_top = float(FR.SKIRT.m_of_p(FR.COLLAR_P - 0.08))          # the collar shakes cover the rest
    sb = SIZE_TABLE["skirt_board"]
    n = covering_boards(FR.SKIRT, acc, "M_roof_shingle", rng, -0.05, m_top, expo=sb["exposure"], W=sb["slope_len"],
                        t=sb["butt"], lens=sb["length"], gap=sb["gap"], nx=8, nm=5, base_h=0.0, scribe=board_scribe,
                        frac_missing=0.015, frac_slip=0.025, curl=0.012, rot_sd=0.012)
    log("  skirt boards", n)
    hw, ht = SIZE_TABLE["hip_board"]["skirt"]
    hip_boards(FR.SKIRT, acc_h, "M_roof_shingle", rng, FR.SKIRT.p_lip + 0.03, 3.3, hw, ht, 0.065, cull=cull)
    def scribe(XY):
        x, y = XY[:, 0], XY[:, 1]
        inside = (x > FR.WX_W - FR.W_OVH) & (x < FR.WX_E + FR.W_OVH) & (y > FR.WY_S - FR.W_OVH) & (y < FR.WY_N + FR.W_OVH)
        return np.where(inside, thatch_low(x, y) + 0.02, -10.0)
    eave_structure(FR.SKIRT, acc_r, acc_r, acc_r, rng, p_wall=FR.PLATE_APO + FR.PLATE_W / 2, z_plate_top=FR.RAFTER_SEAT,
                   sheath_t=FR.SKIRT_SHEATH, n_raft=6, rw=0.10, rd_tip=0.14,
                   cull=lambda C: wing_roof_zone(C, 0.05) | in_wing(C, margin=-0.6, zpad=-0.5), scribe=scribe,
                   fascia_wave=0.02)
    # continuous sarking deck under the boards on all 8 facets, from just inside the wall plate (where the soffit
    # boards stop) to under the collar shakes; cells deep under the wing thatch are dropped
    def deck_cull(P):
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        inside = (x > FR.WX_W - FR.W_OVH) & (x < FR.WX_E + FR.W_OVH) & (y > FR.WY_S - FR.W_OVH) & (y < FR.WY_N + FR.W_OVH)
        return inside & (z < thatch_low(x, y) - 0.08)
    accdk = Acc(FR.prefix + "_roof_skirt_deck")
    sarking_deck(FR.SKIRT, accdk, float(FR.SKIRT.m_of_p(FR.PLATE_APO + FR.PLATE_W / 2 - 0.10)) - 0.03,
                 float(FR.SKIRT.m_of_p(FR.COLLAR_P - 0.30)), h_top=-0.004, t=0.02, nx=12, dm=0.22, cull=deck_cull)
    finalize(accdk, coll)
    finalize(acc, coll)
    finalize(acc_h, coll)
    finalize(acc_r, coll)


def skirt_roof(g, seed=303):
    """KIT COMPONENT: tier 1, the octagonal hipped skirt roof (g.SKIRT): board courses scribed into an adjoining
    thatch valley, saddle hip boards, rafters / soffit / fascia, sarking deck."""
    build_skirt(g.sub("roof_skirt"), seed=seed)
