"""components.timber -- hand-hewn timber members and small timber / iron fixings.

round_post()   round-hewn post (lean, bow, taper, adze flats, knots, optional drying check)
hewn_member()  squared hand-hewn member along local +X (stroke-aligned adze, swell, wane, checks, hidden faces)
timber_box()   simple chamfered board / block
make_peg / peg, make_nail_head, make_clench    pooled fixings (producer note 3)
"""
import math
from functools import partial  # noqa: F401

import numpy as np

from ..core import R_y_to, chamfer_path, fbm, frames, lathe, n2, nrm, rbox, rotx, smoothstep, tube, vnoise, xf


def round_post(g, acc, base, top, rad, rng, sides=48, check=False, n_knots=None, radial=1.0, min_relief=0.0):
    """round-hewn post: lean, bow, taper, 6-10 long adze flats 5-8 mm deep, adze scallops,
    1-2 branch-stub knots with a swelling round them, optional drying check (narrow V split).
    radial: scale of the lean / bow component toward or away from the wall centre (a wall post in a
    daubed wall keeps its face a constant distance proud of the coat; it leans along the wall).
    min_relief (producer note 11): adze flats (5-8 mm), the drying check and the fine surface noise are not
    modelled when shallower; knot swellings (1.2 cm) only where the entrance threshold (1 cm) applies.  The out-
    of-round section, lean, bow, taper and the branch-stub knots (discrete pieces) always stay."""
    tz = (g.EAVE_SHADOW_Z - base[2]) / (top[2] - base[2])
    t_sh = 1 - 0.26 / (top[2] - base[2])
    t_sh = 1 - 0.016 / (top[2] - base[2])
    t = np.concatenate([np.linspace(0, tz, 40), np.linspace(tz, t_sh, 3)[1:], np.linspace(t_sh, 1, 3)[1:]])
    nseg = len(t)
    lean = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]) * math.tan(math.radians(0.7))
    H = top[2] - base[2]
    bow = np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0]) * 0.012
    if radial != 1.0:
        u_r = np.array([base[0], base[1], 0.0]) / max(math.hypot(base[0], base[1]), 1e-6)
        lean = lean - (1 - radial) * (lean @ u_r) * u_r
        bow = bow - (1 - radial) * (bow @ u_r) * u_r
    path = base[None, :] + np.outer(t, top - base) + np.outer(t * H, lean) + np.outer(np.sin(np.pi * t), bow)
    taper = rad * (1 + 0.05 * (0.5 - t)) + rng.uniform(-0.005, 0.005)
    # director r4 #5d: the post is cut square under the plate (the plate bears on its end grain): only a
    # 1.5 cm arris chamfer at the head, no long visible taper / sliver under the plate
    shoulder = smoothstep(H - 0.016, H, t * H)
    taper = taper * (1 - 0.14 * shoulder)
    ph0 = rng.uniform(0, 1)
    # only the outward 240 deg are modelled; the back (against the wattle / inner skin) is one flat chord
    a_out = math.atan2(top[1] + base[1], top[0] + base[0])
    sides = 33
    ang = a_out + np.linspace(-2.1, 2.1, sides)
    ph0 = a_out
    seed = rng.randint(1000)
    A2 = np.broadcast_to(ang, (nseg, sides)).copy()
    T2 = np.broadcast_to(t[:, None], (nseg, sides))
    rr = 1 + 0.02 * n2(A2 * 1.3, T2 * 4, seed) + 0.002 * (min_relief <= 0.0) * n2(A2 * 2, T2 * 30, seed + 1)
    # adze flats: planar cuts 5-8 mm deep over a stretch of the post, feathered at their ends
    nfl = rng.randint(6, 11)
    for kf in range(nfl):
        af = ph0 + 2 * np.pi * (kf + rng.uniform(-0.3, 0.3)) / nfl * 0.7 - 2.2
        d = rng.uniform(0.005, 0.008) / rad
        t0 = rng.uniform(-0.1, 0.45)
        t1 = t0 + rng.uniform(0.45, 1.0)
        wgt = smoothstep(t0, t0 + 0.06, T2) * (1 - smoothstep(t1 - 0.06, t1, T2))
        # scalloped depth along the flat (adze strokes 5-8 cm)
        dd = d * wgt * (0.75 + 0.25 * np.abs(np.sin(T2 * H / 0.065 * np.pi + kf)))
        ca = np.cos(A2 - af)
        cutr = np.where(ca > 0.2, (1 - dd) / np.maximum(ca, 0.2), 10.0)
        if d * rad >= min_relief:
            rr = np.minimum(rr, cutr)
    # knots: branch stubs (separate pieces) + swelling of the surface round them
    if n_knots is None:
        n_knots = rng.randint(1, 3)
    stubs = []
    for _ in range(n_knots):
        ka = ph0 + rng.uniform(-1.4, 1.4)
        kt = rng.uniform(0.25, 0.8)
        da = np.angle(np.exp(1j * (A2 - ka))) * rad
        dz = (T2 - kt) * H
        dist = np.hypot(da, dz * 0.8)
        rr = rr + (0.012 * (0.012 >= min_relief) * np.exp(-(dist / 0.04) ** 2)) / rad
        stubs.append((ka, kt))
    if check:  # drying check: a narrow, deep V split down one face
        k = rng.randint(6, sides - 6)
        z0, z1 = rng.uniform(0.15, 0.35), rng.uniform(0.55, 0.8)
        m = smoothstep(z0, z0 + 0.08, t) * (1 - smoothstep(z1 - 0.08, z1, t)) * (min_relief <= 0.0)
        rr[:, k] *= (1 - 0.13 * m)
        dA = 2 * np.pi / sides
        dA = 4.2 / (sides - 1)
        A2[:, (k - 1) % sides] += dA * 0.82 * m
        A2[:, (k + 1) % sides] -= dA * 0.82 * m
    prof = np.stack([np.cos(A2) * rr, np.sin(A2) * rr], -1)
    P, F, uv, w = tube(path, taper, sides, up=(1, 0, 0), profile=prof)
    acc.add(P, F, "M_timber", uv, w)
    T_, N_, B_ = frames(path, (1, 0, 0))
    for (ka, kt) in stubs:
        i = int(kt * (nseg - 1))
        dirv = nrm(np.cos(ka) * N_[i] + np.sin(ka) * B_[i])
        c0 = path[i] + dirv * taper[i] * 0.6
        dirv2 = nrm(dirv + np.array([0, 0, rng.uniform(0.2, 0.6)]))
        L = taper[i] * 0.4 + rng.uniform(0.014, 0.024)
        pth = np.linspace(c0, c0 + dirv2 * L, 4)
        rs_ = rng.uniform(0.016, 0.024)
        pth, rk = chamfer_path(pth, np.linspace(rs_ * 1.25, rs_, 4), 0.005)
        Pk, Fk, uvk, wk = tube(pth, rk, 10, up=(0, 0, 1))
        acc.add(Pk, Fk, "M_timber", uvk, wk)


def hewn_member(acc, center, half, R, rng, ch=0.018, wane=(), n_checks=0, check_faces=(0, 1, 2, 3),
                end_checks=0, sag=0.0, adze=True, mat="M_timber", ds=0.013, ns=7, nc=6, swell=0.008,
                hero=(), hidden=(), deform=None, stride=7, caps=(True, True), wear=None, checks=True,
                hero_adze=None, adze_nonhero=True):
    """hand-hewn squared timber along local +X (half = (L/2, a, b)); R columns = local axes in world.
    Faces: 0:+z 1:-y 2:-z 3:+y.  Corners: 0:+y+z 1:-y+z 2:-y-z 3:+y-z.
    * adze scallops on every face: 3-6.5 mm deep, 4-8 cm long; on `hero` faces 6-12 mm deep, 5-9 cm
    * +-8 mm swell along the length; arris rounding varies 1.5-3 cm along the member
    * wane (bark-edge rounding) on chosen corners that comes and goes along the length
    * drying checks 6-10 mm wide at the mouth, tapering in width and depth, wandering +-3 mm, some
      with a short parallel / branch check; end-grain checks at both ends
    * `hidden` faces (against the wall / interior / under the roof) are closed with coarse quads only
    * deform(V_local) -> V_local runs before the world transform
    producer note 11 controls (defaults = phase-1 behaviour): checks=False drops the drying / end checks (wood
    checks go to decals); hero_adze=(lo, hi) remaps the hero-face stroke depth (e.g. >= 1 cm inside the entrance
    zone); adze_nonhero=False leaves the non-hero faces smooth (their 3-6.5 mm strokes are sub-threshold).  The
    random draws are unchanged, so the member's shape is otherwise identical."""
    hl, a0, b0 = (float(v) for v in half)
    L = 2 * hl
    nl = max(6, int(L / ds) + 1)
    che = min(ch, 0.012)
    xs = np.concatenate([[-hl, -hl + che], np.linspace(-hl + che * 2, hl - che * 2, nl), [hl - che, hl]])
    n = len(xs)
    tt = (xs + hl) / L
    seed = rng.randint(100000)
    sw_a = a0 + swell * n2(tt * 3.0, np.full(n, 0.5), seed)
    sw_b = b0 + swell * n2(tt * 3.0, np.full(n, 2.5), seed + 1)
    rc = np.zeros((n, 4))
    for c in range(4):
        rc[:, c] = np.clip(ch * (1.1 + 0.5 * n2(tt * 3.0 * max(1.0, L / 1.5), np.full(n, c * 1.7), seed + 9)),
                           0.75 * ch, 1.5 * ch)
    for cw in wane:
        wv = smoothstep(-0.25, 0.25, n2(tt * 2.4 * max(1.0, L / 1.5), np.full(n, cw * 3.1), seed + 25 + cw))
        wr = np.clip(0.045 + 0.02 * n2(tt * 4.0, np.full(n, cw * 3.1), seed + 5 + cw), 0.025, 0.065)
        rc[:, cw] = rc[:, cw] * (1 - wv) + wr * wv
    M = 4 * (ns + nc)
    Y = np.zeros((n, M))
    Zp = np.zeros((n, M))
    face = np.full(M, -1)
    across = np.zeros(M)
    corner_sign = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    a_beg_l = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi]
    arcs = np.linspace(0, 0.5 * np.pi, nc)
    for c in range(4):
        sy, sz = corner_sign[c]
        cn = (c + 1) % 4
        sy2, sz2 = corner_sign[cn]
        r = np.minimum(rc[:, c], np.minimum(sw_a, sw_b) * 0.6)
        r2 = np.minimum(rc[:, cn], np.minimum(sw_a, sw_b) * 0.6)
        cy, cz = sy * (sw_a - r), sz * (sw_b - r)
        base_j = c * (ns + nc)
        for k_ in range(nc):
            ang = a_beg_l[c] + arcs[k_]
            Y[:, base_j + k_] = cy + r * math.cos(ang)
            Zp[:, base_j + k_] = cz + r * math.sin(ang)
        pf_y, pf_z = Y[:, base_j + nc - 1], Zp[:, base_j + nc - 1]
        pt_y = sy2 * (sw_a - r2) + r2 * math.cos(a_beg_l[cn])
        pt_z = sz2 * (sw_b - r2) + r2 * math.sin(a_beg_l[cn])
        for k_ in range(ns):
            u = (k_ + 1) / (ns + 1)
            j = base_j + nc + k_
            Y[:, j] = pf_y + (pt_y - pf_y) * u
            Zp[:, j] = pf_z + (pt_z - pf_z) * u
            face[j] = c
            across[j] = u * 2 - 1
    fn = {0: (0, 1), 1: (-1, 0), 2: (0, -1), 3: (1, 0)}
    disp = np.zeros((n, M))
    # director r4 #4: STROKE-ALIGNED topology.  Every adzed face gets one diagonal stroke skew; its vertex
    # columns are slid along the member by -skew * across, so each vertex row runs exactly along a stroke
    # boundary line (no stair-stepped crease across the grid).  The corner arcs blend the two neighbouring
    # faces' edge shifts; the shear ramps out over the last 12 cm at each end (square end cuts).
    skews = np.zeros(4)
    for c in range(4):
        if adze and c not in hidden:
            fhw = a0 if c in (0, 2) else b0
            skews[c] = rng.choice([-1.0, 1.0]) * math.tan(math.radians(rng.uniform(25.0, 40.0))) * fhw
    # each face's strokes follow the adze swing: a slight bow (one per face), stroke boundaries stay on rows
    bows = np.array([rng.uniform(0.05, 0.12) * abs(skews[c]) * rng.choice([-1.0, 1.0]) for c in range(4)])
    shift = np.zeros(M)
    for c in range(4):
        js = np.where(face == c)[0]
        shift[js] = skews[c] * across[js] + bows[c] * (across[js] ** 2 - 1.0)
        cp = (c - 1) % 4
        for k_ in range(nc):
            t_ = k_ / max(nc - 1, 1)
            shift[c * (ns + nc) + k_] = skews[cp] * (1 - t_) - skews[c] * t_
    ramp = smoothstep(0.0, min(0.12, hl * 0.45), xs + hl) * smoothstep(0.0, min(0.12, hl * 0.45), hl - xs)
    Xs = xs[:, None] - shift[None, :] * ramp[:, None]          # actual vertex positions along the member
    if adze:
        for c in range(4):
            if c in hidden:
                continue
            js = np.where(face == c)[0]
            hero_f = c in hero
            nlane = 1                    # director r4 #4: one stroke lane per face (no lane-seam steps)
            # consistent diagonal lanes per face (director r3 #6): every stroke boundary on this face
            # runs at the same 25-40 deg skew
            skew_f = skews[c]
            edges = np.sort(np.concatenate([[-1.01, 1.01], rng.uniform(-0.5, 0.5, nlane - 1)]))
            lane_scoop_mid = np.zeros(n)
            for ln in range(nlane):
                inl = (across[js] >= edges[ln]) & (across[js] < edges[ln + 1])
                if not inl.any():
                    continue
                jl = js[inl]
                bnd = [-hl - rng.uniform(0, 0.06)]
                while bnd[-1] < hl + 0.1:
                    bnd.append(bnd[-1] + (rng.uniform(0.05, 0.09) if hero_f else rng.uniform(0.04, 0.08)))
                bnd = np.array(bnd)
                if hero_f:
                    dep = rng.uniform(0.006, 0.012, len(bnd)) * (rng.rand(len(bnd)) > 0.06)
                    if hero_adze is not None:
                        dep = np.where(dep > 0, hero_adze[0] + (dep - 0.006) / 0.006 * (hero_adze[1] - hero_adze[0]), 0.0)
                else:
                    dep = rng.uniform(0.003, 0.0065, len(bnd)) * (rng.rand(len(bnd)) > 0.1) * float(adze_nonhero)
                xe = Xs[:, jl] + skew_f * across[jl][None, :] + bows[c] * (across[jl][None, :] ** 2 - 1.0)
                k = np.clip(np.searchsorted(bnd, xe.ravel()) - 1, 0, len(bnd) - 2).reshape(xe.shape)
                tl = np.clip((xe - bnd[k]) / (bnd[k + 1] - bnd[k]), 0, 1)
                # scoop: deepest early in the stroke, ends in a small ridge; fades toward lane edges
                ac_ = np.abs(across[jl])[None, :]
                fade = 1 - 0.35 * smoothstep(0.7, 1.0, ac_)
                # scoop: steep entry at the boundary -> crisp crease between strokes, shallower run-out
                sc = dep[k] * np.sin(np.pi * tl) ** 0.6 * (0.7 + 0.3 * (1 - tl)) * fade
                disp[:, jl] += sc
                lane_scoop_mid += sc.mean(1) / nlane
            for jc in range(c * (ns + nc), c * (ns + nc) + nc):
                disp[:, jc] += 0.3 * lane_scoop_mid
    for c in range(4):
        js = np.where(face == c)[0]
        ny, nz = fn[c]
        Y[:, js] -= ny * disp[:, js]
        Zp[:, js] -= nz * disp[:, js]
    cj = np.where(face < 0)[0]
    rad_ = np.hypot(Y[:, cj], Zp[:, cj])
    Y[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)
    Zp[:, cj] *= 1 - disp[:, cj] / np.maximum(rad_, 1e-3)

    def apply_check(c, j_off, i0, i1, depth, width, from_end=0, wander=0.003):
        if not checks:
            return
        j = c * (ns + nc) + nc + j_off
        ny, nz = fn[c]
        ii = np.arange(i0, i1)
        if len(ii) < 3:
            return
        tl = (ii - i0) / max(1, (i1 - i0 - 1))
        if from_end < 0:
            m = (1 - tl) ** 0.7
        elif from_end > 0:
            m = tl ** 0.7
        else:
            m = smoothstep(0.0, 0.25, tl) * (1 - smoothstep(0.6, 1.0, tl))     # tapers both ways
        tyz = np.array([-nz, ny], float)
        wv = wander * n2(xs[ii] * 9.0, np.full(len(ii), j * 0.37), seed + 11 + j)
        # wander: the crack line and its lips drift sideways together
        for jj in (j - 1, j, j + 1):
            Y[ii, jj] += tyz[0] * wv * smoothstep(0.0, 0.2, m)
            Zp[ii, jj] += tyz[1] * wv * smoothstep(0.0, 0.2, m)
        # V-section (director r3 #6): the lips close onto the crack line wherever the crack is shallow,
        # so the mouth width and the depth both run to zero at the ends (no rectangular pocket)
        hw = width / 2 * np.sqrt(np.clip(m, 0, 1))
        for jn, sg in ((j - 1, 1), (j + 1, -1)):
            dist = np.abs((Y[ii, jn] - Y[ii, j]) * tyz[0] + (Zp[ii, jn] - Zp[ii, j]) * tyz[1])
            pull = np.clip(dist - hw, 0, None)
            Y[ii, jn] += sg * tyz[0] * pull
            Zp[ii, jn] += sg * tyz[1] * pull
        Y[ii, j] -= ny * depth * m
        Zp[ii, j] -= nz * depth * m

    for _ in range(n_checks):
        c = int(rng.choice(check_faces))
        if c in hidden:
            continue
        j_off = rng.randint(2, ns - 2)
        lc = rng.uniform(0.15, 0.4)
        x0 = rng.uniform(-hl + 0.15, hl - 0.15 - lc)
        i0 = int(np.searchsorted(xs, x0))
        i1 = int(np.searchsorted(xs, x0 + lc))
        w_ck = rng.uniform(0.006, 0.010)
        apply_check(c, j_off, i0, i1, w_ck * rng.uniform(0.9, 1.3), w_ck)
        if rng.rand() < 0.6:          # short en-echelon branch (parallel, i.e. <= 30 deg), own lips
            jb = j_off + rng.choice([-3, 3])
            if 1 <= jb <= ns - 2:
                lb = rng.uniform(0.05, 0.12)
                xb = x0 + rng.uniform(0.2, 0.7) * lc
                ib0 = int(np.searchsorted(xs, xb))
                ib1 = int(np.searchsorted(xs, min(xb + lb, hl - 0.05)))
                w_b = rng.uniform(0.003, 0.005)
                apply_check(c, jb, ib0, ib1, w_b * rng.uniform(0.9, 1.3), w_b)
    for _ in range(end_checks):
        for side_ in (-1, 1):
            c = rng.randint(4)
            if c in hidden:
                c = (c + 1) % 4
            j_off = rng.randint(1, ns - 1)
            lc = rng.uniform(0.06, 0.16)
            if side_ < 0:
                i0, i1 = 0, int(np.searchsorted(xs, -hl + lc))
            else:
                i0, i1 = int(np.searchsorted(xs, hl - lc)), n
            w_e = rng.uniform(0.004, 0.007)
            apply_check(c, j_off, i0, i1, w_e * rng.uniform(1.0, 1.6), w_e, from_end=side_)
    for i_e in (0, n - 1):
        Y[i_e] *= 1 - che / max(a0, 1e-3)
        Zp[i_e] *= 1 - che / max(b0, 1e-3)
    X = Xs.copy()
    if sag:
        X_t = xs / hl
        Zp += (-sag * (1 - X_t ** 2))[:, None]
    V = np.stack([X, Y, Zp], -1).reshape(-1, 3)
    inner0 = np.stack([X[0] + 0.002, Y[0] * 0.55, Zp[0] * 0.55], -1)
    inner1 = np.stack([X[-1] - 0.002, Y[-1] * 0.55, Zp[-1] * 0.55], -1)
    cen = np.array([[xs[0] + 0.003, 0, Zp[0].mean()], [xs[-1] - 0.003, 0, Zp[-1].mean()]])
    V = np.concatenate([V, inner0, inner1, cen])
    j = np.arange(M)
    j1 = (j + 1) % M
    # profile segments belonging to hidden faces (from the last arc point of corner c to the first of c+1)
    hseg = np.zeros(M, bool)
    for c in hidden:                  # the face plus the halves of its two corner arcs
        js0 = c * (ns + nc) + nc - 1 - (nc - 1) // 2
        for q in range(ns + 1 + 2 * ((nc - 1) // 2)):
            hseg[(js0 + q) % M] = True
    i = np.arange(n - 1)[:, None]
    jk = j[~hseg][None, :]
    jk1 = j1[~hseg][None, :]
    Fs = np.stack([i * M + jk, i * M + jk1, (i + 1) * M + jk1, (i + 1) * M + jk], -1).reshape(-1, 4)
    Fl = [Fs]
    if hseg.any():
        ir = np.unique(np.concatenate([np.arange(0, n - 1, stride), [n - 1]]))
        a_ = ir[:-1][:, None]
        b_ = ir[1:][:, None]
        jh = j[hseg][None, :]
        jh1 = j1[hseg][None, :]
        Fl.append(np.stack([a_ * M + jh, a_ * M + jh1, b_ * M + jh1, b_ * M + jh], -1).reshape(-1, 4))
    o_in0 = n * M
    o_in1 = n * M + M
    c0i = n * M + 2 * M
    c1i = c0i + 1
    last = (n - 1) * M
    cap0 = np.stack([o_in0 + j, o_in0 + j1, j1, j], -1)
    cap1 = np.stack([last + j, last + j1, o_in1 + j1, o_in1 + j], -1)
    fan0 = np.stack([np.full(M, c0i), o_in0 + j1, o_in0 + j], -1)
    fan1 = np.stack([np.full(M, c1i), o_in1 + j, o_in1 + j1], -1)
    if deform is not None:
        V = deform(V)
    Vw = xf(V, R, center)
    acc.add(Vw, Fl + ([cap0, fan0] if caps[0] else []) + ([cap1, fan1] if caps[1] else []), mat, wear=wear)


def timber_box(acc, center, half, R=None, ch=0.02, segs=(1, 1, 1), noise=0.0, seed=0, mat="M_timber",
               sag=0.0, splits=None):
    half = np.asarray(half, float)
    ax = int(np.argmax(half))
    if noise > 0:
        sg = list(segs)
        sg[ax] = max(sg[ax], int(half[ax] * 2 / 0.035))
        for k in range(3):
            if k != ax:
                sg[k] = max(sg[k], 3)
        segs = tuple(sg)
    V, F = rbox(half, ch, segs)
    if noise > 0:
        q = V / half
        dom = np.argmax(np.abs(q) - (np.arange(3) == ax) * 0.5, axis=1)
        nd = np.zeros_like(V)
        nd[np.arange(len(V)), dom] = np.sign(q[np.arange(len(V)), dom])
        sc = np.ones(3) * 18.0
        sc[ax] = 3.0
        rs = np.random.RandomState(seed + 500)
        o = rs.uniform(-50, 50, 3)
        hew = (noise * fbm(V * sc + o, 2)
               + 0.0028 * np.abs(np.sin(V[:, ax] / 0.11 * np.pi + 3 * vnoise(V * 6 + o)))  # adze scallops
               + 0.004 * vnoise(V * 1.5 + o * 2))
        V = V - nd * hew[:, None]
    if sag:
        t = V[:, 0] / half[0]
        V[:, 2] -= sag * (1 - t ** 2)
    V = xf(V, R, center)
    acc.add(V, F, mat)


def make_peg(acc, k):
    """whittled oak peg (pool variant): irregular octagon, head proud 1.5-1.8 cm along local +Y with a
    domed, slightly split head; only 1.2 cm of shank modelled inside the timber."""
    rs = np.random.RandomState(6100 + k)
    proud = rs.uniform(0.015, 0.018)
    r = 0.015 * rs.uniform(0.9, 1.1)
    path = np.linspace([0, -0.03, 0], [0, proud, 0], 4)
    ang = 2 * np.pi * np.arange(8) / 8 + rs.uniform(0, 1)
    rr = 1 + rs.uniform(-0.09, 0.09, 8)
    prof = np.stack([np.cos(ang) * rr, np.sin(ang) * rr], -1)
    path, rad = chamfer_path(path, np.full(4, r), 0.005)
    P, F, uv, w = tube(path, rad, 8, up=(0, 0, 1), profile=prof)
    top = P[:, 1] > proud - 0.004
    P[top, 1] += 0.002 * rs.uniform(-1, 1) * np.sign(P[top, 0])          # split / skewed head
    acc.add(P, F, "M_timber", uv, w)


def peg(g, p, d, rng):
    mesh = g.pools.mesh("peg", rng.randint(6), make_peg, 28)
    g.pools.place(mesh, "peg", R_y_to(d) @ rotx(0) @ np.eye(3), p)


def make_nail_head(acc, k):
    """forged nail head (pool variant), local +Y out of the iron, base at y=0."""
    rs = np.random.RandomState(6200 + k)
    rd = rs.uniform(0.0085, 0.0105)
    prof = [(0.0, -0.004), (rd * 0.9, -0.004), (rd, 0.0), (rd, 0.0015), (rd * 0.66, 0.0042), (0.0, 0.0054)]
    V, F, uv, w = lathe(prof, 8, rfunc=lambda t, z: 1 + 0.08 * np.sin(2 * t + k))
    acc.add(np.stack([V[:, 0], V[:, 2], V[:, 1]], -1), [f[:, ::-1] for f in F], "M_iron")


def make_clench(acc, k):
    rs = np.random.RandomState(6300 + k)
    V, F = rbox((0.004 * rs.uniform(0.9, 1.1), 0.003, 0.0045), 0.0012)
    V[:, 2] += V[:, 1] * rs.uniform(-0.3, 0.3)
    acc.add(V, F, "M_iron")
