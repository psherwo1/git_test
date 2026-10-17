"""components.tier_flashing -- the dressed roof/body flashing, its eave cheek and its clip check (kit 1.10.2 proposal,
v2_tiered_hall round 5).  NEW module: no existing kit function changed.

    dressed_flashing(g, roof_name, body_name, ...)      KIT COMPONENT (the roof-through-body junction module)
        The lead flashing where a declared body rises through a registered roof tier (octagonal, round or pyramid):
        an upstand tucked into the wall face and an apron DRESSED OVER THE COVERING.  The apron's underside follows
        the covering's real upper envelope (a downward ray map of every piece of the tier: shingles, starters, hip
        boards, under-laps), max-filtered over each apron cell plus `gap`, so the lead laps over every course and
        rises over every hip board that runs into the body; nothing of the covering stands through it (no turned-down
        drip cut into the courses, nothing to trim).  Replaces tier_roof.roof_flashing for new recipes:
        roof_flashing's apron follows the BASE surface (+0.075..0.15 m) and, with drip=0.03, cuts into the courses
        (v2 round-4 audit: 161 hip / apron triangle pairs, 1,817 shingle vertices above the lead).
        Where the body leaves the roof at the eave (open runs), eave_cheek closes the eave section against the body.
        check=True runs flashing_clip_check on the result (fails the build on any interpenetration).
        Round 6 (dress="tight", the default; v2 round-5 director: the max-filtered apron floated 8-13 cm over the
        courses and folded through itself at the turret run ends): every apron vertex starts on its OWN station's
        envelope and is lifted only as far as the sheet needs (`_dress_tight`), the apron ends on the course it laps
        (never just short of a butt), the drip edge turns down to 3 mm over the course, every open run tapers over
        its last `taper` stations onto one planar end cap over the eave cheek, and the sheet is triangulated so its
        top and underside can never cross (`_tri_sweep`).  dress="max" rebuilds the round-5 profile.
                                                          -> <P>_<roof>_<body>_flashing (+ _flashing_cheek)
    eave_cheek(g, roof_name, body_name, ...)            KIT COMPONENT
        A lead cheek on the body face wherever the body passes through the tier's OVERHANG (outside the supporting
        wall line, inside the eave lip + fascia): a plate standing `d_out` off the nominal face with top, bottom and
        end returns tucked into the wall, covering every tier member that meets the face there (fascia, soffit /
        deck, deck lap, rafters, starter and shingle ends), from `pad` under the lowest to the covering top (open
        eave end) or the roof base surface (under the apron).  The eave members butt into it instead of dying square
        into the masonry (v2 round-4 k03 / k04 / k06).  Its name contains "flashing", so the hidden cull never
        targets it.                                      -> <P>_<roof>_<body>_flashing_cheek
    flashing_clip_check(g, roof_name, flashing, fail=True)   KIT CHECK
        BVH overlap of a flashing object against every other mesh of its tier (covering, hips, deck, structure):
        any intersecting triangle pair raises FlashingClipError naming the tier, the object, the pair count and a
        world point (fail=False only logs).  Run by dressed_flashing(check=True).  Round 6: also the flashing
        against ITSELF (non-adjacent pairs, `self_intersections`) and against the tier's other flashing pieces
        (cheeks), and the LIFT test (`flashing_lift`): any 1-deg sector whose drip edge stands more than max_lift
        (0.05 m) over the course under it, or any station whose upstand foot stands more than max_foot (0.05 m)
        over the local roof line, fails the build, named by angle and world point.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize
from .tier_frame import roof_support, roof_z


class FlashingClipError(RuntimeError):
    """a flashing interpenetrates the covering / structure of its roof tier (kit 1.10.2 proposal)."""


def _tier_meshes(g, roof_name, skip=("_flashing",)):
    coll = g.sub(roof_name)
    return [o for o in coll.all_objects
            if o.type == "MESH" and len(o.data.polygons) and not any(s in o.name for s in skip)]


def _world_tris(objs):
    from .seal_probe import _mesh_arrays
    return _mesh_arrays(objs)


def _junction(g, roof, body, step):
    """stations round the body and the roof / body junction height at each (as tier_roof.roof_flashing)."""
    R = float(body.r_nom(0.5 * (body.z0 + body.z1)))
    n = max(64, int(2 * math.pi * R / step))
    ths = np.linspace(0, 2 * math.pi, n, endpoint=False)
    zj = np.full(n, 0.5 * (body.z0 + body.z1))
    for _ in range(3):
        P = body.point(ths, zj)
        zj = roof_z(roof, P[:, 0], P[:, 1])
        zj = np.where(np.isfinite(zj), zj, body.z0)
    return n, ths, zj


def _sweep(acc, W, ok, m, mat="M_lead"):
    """sweep a closed (n, m) profile ring W into runs of valid stations `ok` (closed ring when all valid, else open
    runs with closed end caps).  Returns the number of runs."""
    n = len(ok)
    if ok.all():
        runs = [(np.arange(n), True)]
    else:
        idx = np.flatnonzero(ok)
        if not len(idx):
            return 0
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
    n_run = 0
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
        acc.add(Vr.reshape(-1, 3), faces, mat)
        n_run += 1
    return n_run


def _runs(ok):
    """runs of valid stations: [(station ids, closed)] (one closed ring when every station is valid)."""
    n = len(ok)
    if ok.all():
        return [(np.arange(n), True)]
    if not ok.any():
        return []
    start = np.flatnonzero(~ok)[0]
    runs, cur = [], []
    for k in (np.arange(n) + start) % n:
        if ok[k]:
            cur.append(k)
        elif cur:
            runs.append((np.array(cur), False))
            cur = []
    if cur:
        runs.append((np.array(cur), False))
    return runs


def _tri_sweep(acc, W, D, Z, ok, cap, mat="M_lead"):
    """KIT HELPER (round 6): sweep a closed (n, m) profile ring W into runs of valid stations, TRIANGULATED with one
    diagonal rule in (station, d) parameter space: a segment running outward (d up, or straight down a vertical
    face) splits on the (i, j)-(i+1, j+1) diagonal, every other one on (i, j+1)-(i+1, j).  So two surfaces that
    share their (station, d) vertices -- the top and the underside of a lead sheet -- are always split the same way
    and never cross, however the profile twists between stations (v2 round-5: 94 self-intersecting pairs at the
    turret apron run ends with free quad splits).  Open runs get PLANAR end caps in the end station's radial plane,
    built from `cap` (convex quads / triangles of profile indices).  Returns the number of runs."""
    n, m = D.shape
    i0 = int(np.flatnonzero(ok)[0]) if ok.any() else 0
    dD = np.roll(D[i0], -1) - D[i0]
    dZ = np.roll(Z[i0], -1) - Z[i0]
    fwd = (dD > 1e-6) | ((np.abs(dD) <= 1e-6) & (dZ < 0))
    n_run = 0
    for ids, closed in _runs(ok):
        k_ = len(ids)
        if k_ < 2:
            continue
        ii = np.arange(k_ if closed else k_ - 1)[:, None]
        jj = np.arange(m)[None, :]
        i2 = (ii + 1) % k_
        A, B = ii * m + jj, ii * m + (jj + 1) % m
        C, Dd = i2 * m + (jj + 1) % m, i2 * m + jj
        f = np.broadcast_to(fwd[None, :], A.shape)
        t1 = np.where(f[..., None], np.stack([A, B, C], -1), np.stack([A, B, Dd], -1))
        t2 = np.where(f[..., None], np.stack([A, C, Dd], -1), np.stack([B, C, Dd], -1))
        faces = [t1.reshape(-1, 3), t2.reshape(-1, 3)]
        if not closed:
            for c in cap:
                c = np.asarray(c, np.int64)
                faces += [c[None, ::-1], ((k_ - 1) * m + c)[None]]
        acc.add(W[ids].reshape(-1, 3), faces, mat)
        n_run += 1
    return n_run


def _dress_tight(E, d_f, sub, Dk, ap, ok, zj, d_lo, d_hi, gap, cost=None):
    """KIT HELPER (round 6): the lowest apron underside heights U (n, nd) whose sheet -- as `_tri_sweep` splits it
    -- stands at least `gap` over every finite sample of the covering envelope E (sub fine rows per station, radial
    samples d_f) between the foot (d_face - t, `d_lo`) and the drip (ap + `d_hi`).  Each corner starts on its OWN
    station's envelope (no cross-station max), then one minimal-norm pass lifts the corners of every split triangle
    that a sample stands over (per sample, corner c is raised by deficit * w_c / sum(w^2); the per-corner maximum of
    those raises lifts every sample's triangle by at least its deficit).  So the lead rises over a hip board or a
    course butt only where it must, and lies `gap` over the course everywhere else."""
    n, nd = Dk.shape
    nf, nq = E.shape
    dd = float(d_f[1] - d_f[0])
    # sampling guard: a shingle corner or a course step can stand between two samples, where the sheet (falling
    # round a turret flank at up to 2:1) is already lower than at the sample that saw it.  So each sample takes
    # the maximum of its 3 x 3 neighbourhood (one fine row round the body, one radial sample): a dilation by one
    # sample spacing (8 mm x 5 mm), not the round-5 cell-wide / +-2 station maximum
    Ef = np.where(np.isfinite(E), E, -np.inf)
    Ed = Ef.copy()
    for s_ in (-1, 1):
        Ed = np.maximum(Ed, np.roll(Ef, s_, 0))
    Er = Ed.copy()
    Er[:, 1:] = np.maximum(Er[:, 1:], Ed[:, :-1])
    Er[:, :-1] = np.maximum(Er[:, :-1], Ed[:, 1:])
    E = np.where(np.isfinite(E), Er, E)
    Ef = np.where(np.isfinite(E), E, -np.inf)
    ki = np.clip(np.round((Dk - d_f[0]) / dd).astype(int), 0, nq - 1)
    U = Ef[(sub * np.arange(n))[:, None], ki]
    rowmax = np.max(np.where(np.isfinite(U), U, -np.inf), axis=1)
    U = np.where(np.isfinite(U), U, np.where(np.isfinite(rowmax), rowmax, zj)[:, None]) + gap
    U = np.where(ok[:, None], U, zj[:, None] + gap)
    S_i, S_i2, S_k, S_a, S_b, S_e = [], [], [], [], [], []
    for i in np.flatnonzero(ok):
        i2 = (i + 1) % n
        js = range(sub + 1) if ok[i2] else range(1)
        for j in js:
            a = j / sub
            Drow = (1 - a) * Dk[i] + a * Dk[i2]
            r = (sub * i + j) % nf
            sel = (d_f >= Drow[0] - d_lo) & (d_f <= ap[i] * (1 - a) + ap[i2] * a + d_hi) & np.isfinite(Ef[r])
            if not sel.any():
                continue
            dq = d_f[sel]
            k = np.clip(np.searchsorted(Drow, dq) - 1, 0, nd - 2)
            b = np.clip((dq - Drow[k]) / np.maximum(Drow[k + 1] - Drow[k], 1e-9), 0.0, 1.0)
            S_i.append(np.full(len(dq), i))
            S_i2.append(np.full(len(dq), i2 if j else i))
            S_k.append(k)
            S_a.append(np.full(len(dq), a))
            S_b.append(b)
            S_e.append(Ef[r, sel])
    if not S_i:
        return U
    si, si2, sk = np.concatenate(S_i), np.concatenate(S_i2), np.concatenate(S_k)
    sa, sb, se = np.concatenate(S_a), np.concatenate(S_b), np.concatenate(S_e)
    up = sa >= sb                                   # split: (00, 10, 11) when a >= b, else (00, 11, 01)
    w00 = np.where(up, 1 - sa, 1 - sb)
    w10 = np.where(up, sa - sb, 0.0)
    w11 = np.where(up, sb, sa)
    w01 = np.where(up, 0.0, sb - sa)
    corners = [(si, sk, w00), (si2, sk, w10), (si2, sk + 1, w11), (si, sk + 1, w01)]
    # round 7 (optional): a per-corner cost (n, nd) weights the minimal-norm lift -- a costly corner (the upstand
    # foot) is raised less and its outer neighbours more, so a shingle standing mid-cell tilts the sheet up outward
    # instead of lifting the foot off the local roof line
    cw = [np.ones(len(si)) if cost is None else cost[ci, ck] for ci, ck, _w in corners]
    ww = sum(w ** 2 / c for (_ci, _ck, w), c in zip(corners, cw))
    for _ in range(3 if cost is None else 6):       # one pass suffices; the rest only mop up float round-off
        z = sum(w * U[ci, ck] for ci, ck, w in corners)
        de = se + gap - z
        if not (de > 1e-5).any():
            break
        de = np.maximum(de, 0.0)
        R = np.zeros_like(U)
        for (ci, ck, w), c in zip(corners, cw):
            np.maximum.at(R, (ci, ck), de * w / c / ww)
        U = U + R
    return U


def _end_lines(U, s, sel):
    """KIT HELPER (round 7): rows `sel` of the dressed underside U (n, nd) replaced by ONE straight line over the
    apron parameter s (foot s=0 to drip s=1): the lowest line (least height at mid-apron) that stays on or over
    every dressed vertex of the row, so the sheet still clears the covering (raising a corner never lowers the
    split sheet) and the run end reads as one clean turned-down plate."""
    U = U.copy()
    nd = U.shape[1]
    S = np.broadcast_to(np.asarray(s, float), U.shape)
    for i in np.flatnonzero(sel):
        u = U[i]
        s = S[i]
        best = None
        for a in range(nd):
            for b in range(a + 1, nd):
                k = (u[b] - u[a]) / (s[b] - s[a])
                L = u[a] + k * (s - s[a])
                if (L >= u - 1e-9).all():
                    mid = u[a] + k * (0.5 - s[a])
                    if best is None or mid < best[0]:
                        best = (mid, L)
        if best is not None:
            U[i] = np.maximum(best[1], u)
    return U


def _adaptive_keep(U, ap, z_drip, Ztop, ok, ends, up_tol=0.006, ap_tol=0.002):
    """KIT HELPER (round 7): adaptive stations.  The apron was dressed on half-step stations; every odd station
    whose two neighbours are laid, are not run-end stations and carry the same apron (within ap_tol) is dropped when
    the straight sheet between its neighbours stands on or over its own dressed underside, top and drip, and no more
    than up_tol over them (so the lead stays dressed on the course and still clears everything the half-step
    station cleared).  Returns the keep mask (unlaid stations are always kept: they delimit the runs)."""
    n = len(ok)
    keep = np.ones(n, bool)
    for i in range(1, n - 1, 2):
        a, b = i - 1, i + 1
        if not (ok[a] and ok[i] and ok[b]) or ends[a] or ends[i] or ends[b]:
            continue
        if abs(ap[i] - 0.5 * (ap[a] + ap[b])) > ap_tol or abs(ap[a] - ap[b]) > 2 * ap_tol:
            continue
        mu = 0.5 * (U[a] + U[b]) - U[i]
        mt = 0.5 * (Ztop[a] + Ztop[b]) - Ztop[i]
        md = 0.5 * (z_drip[a] + z_drip[b]) - z_drip[i]
        if mu.min() >= -0.0005 and mu.max() <= up_tol and mt.min() >= -0.0005 and mt.max() <= up_tol and \
                -0.0005 <= md <= up_tol:
            keep[i] = False
    return keep


def _drip_lift(bvh, body, ths, z_drip, d_drip, ok, foot_w=0.012, out=0.01, above=0.4):
    """KIT HELPER (round 7): per station, the drip vertex's lift over the covering exactly as flashing_lift
    measures it (a ray down from `out` past the vertex, the highest hit of a 3 x 3 footprint +-foot_w along the
    edge and +-foot_w / 2 radially).  -inf where nothing is hit or the station is not laid."""
    from mathutils import Vector
    down = Vector((0.0, 0.0, -1.0))
    est = np.full(len(ths), -np.inf)
    P = body.point(ths, z_drip, d=d_drip)
    for i in np.flatnonzero(ok):
        rad = np.array([math.cos(ths[i]), math.sin(ths[i])])
        tan = np.array([-rad[1], rad[0]])
        top = None
        for a in (-foot_w, 0.0, foot_w):
            for b in (-0.5 * foot_w, 0.0, 0.5 * foot_w):
                o = P[i, :2] + (out + b) * rad + a * tan
                h = bvh.ray_cast(Vector((float(o[0]), float(o[1]), float(P[i, 2]) + above)), down, above + 1.0)
                if h[0] is not None and (top is None or h[0][2] > top):
                    top = float(h[0][2])
        if top is not None:
            est[i] = float(P[i, 2]) - top
    return est


def _slope_factor(U, Dk, ok, body, ths, cap=6.0):
    """KIT HELPER (round 7): sqrt(1 + slope^2) of the dressed sheet at every apron vertex (the steeper of its two
    radial segments and of its two tangential segments to valid neighbouring stations), capped at `cap`.  The top
    stands t times this over the underside, so the lead is t thick NORMAL to the sheet even where it steps down a
    course."""
    n, nd = U.shape
    gd = np.zeros((n, nd))
    sl = np.abs(np.diff(U, axis=1)) / np.maximum(np.diff(Dk, axis=1), 1e-4)
    gd[:, :-1] = np.maximum(gd[:, :-1], sl)
    gd[:, 1:] = np.maximum(gd[:, 1:], sl)
    gt = np.zeros((n, nd))
    dth = 2 * math.pi / n
    r = body.r_eff(ths, U[:, 0])[:, None] + Dk
    for s_ in (-1, 1):
        j = (np.arange(n) + s_) % n
        valid = (ok & ok[j])[:, None]
        g_ = np.abs(U[j] - U) / np.maximum(r * dth, 1e-4)
        gt = np.where(valid, np.maximum(gt, g_), gt)
    return np.clip(np.sqrt(1.0 + gd ** 2 + gt ** 2), 1.0, cap)


def covering_envelope(g, roof_name, body, ths, zj, d_lo, d_hi, sub=4, dd=0.01, lift=1.0, objs=None):
    """KIT HELPER: the upper envelope of tier `roof_name`'s pieces round `body` -- a (len(ths) * sub, nd) map of the
    highest covering point (downward rays against every mesh of the tier) at plan points `d` m outside the body face
    (d from d_lo to d_hi step dd) on `sub` sub-stations per station.  Where no piece is hit the roof's base surface
    is used (-inf beyond the lip).  Returns (th_f, d_f, E)."""
    from mathutils import Vector
    from .seal_probe import _bvh
    roof = g.roofs[roof_name]["roof"]
    objs = _tier_meshes(g, roof_name) if objs is None else objs
    V, T, _ = _world_tris(objs)
    bvh = _bvh(V, T)
    n = len(ths)
    th_f = np.arange(n * sub) * (2 * math.pi / (n * sub)) + ths[0]
    zj_f = np.interp(th_f, np.concatenate([ths, [ths[0] + 2 * math.pi]]), np.concatenate([zj, [zj[0]]]))
    d_f = np.arange(d_lo, d_hi + 1e-9, dd)
    TH, D = np.meshgrid(th_f, d_f, indexing="ij")
    ZJ = np.broadcast_to(zj_f[:, None], TH.shape)
    P = body.point(TH, ZJ, d=D)
    base = roof_z(roof, P[..., 0], P[..., 1])
    z0 = np.where(np.isfinite(base), base, ZJ) + lift
    E = np.array(base, float)
    down = Vector((0.0, 0.0, -1.0))
    flat = P.reshape(-1, 3)
    zf = z0.ravel()
    Ef = E.ravel()
    for i in range(len(flat)):
        h = bvh.ray_cast(Vector((float(flat[i, 0]), float(flat[i, 1]), float(zf[i]))), down, lift + 1.5)
        if h[0] is not None:
            Ef[i] = max(float(h[0][2]), Ef[i]) if np.isfinite(Ef[i]) else float(h[0][2])
    E = Ef.reshape(E.shape)
    # a triangle's highest point is one of its vertices: splat every piece vertex into its cell as well, so thin
    # spikes and corners between the ray samples are never missed
    dv = body.dist(V)
    sel = (dv > d_lo - dd) & (dv < d_hi + dd) & (V[:, 2] > body.z0 - 1.0) & (V[:, 2] < body.z1 + 1.0)
    if sel.any():
        Vs = V[sel]
        th_v = (np.arctan2(Vs[:, 1] - body.c[1], Vs[:, 0] - body.c[0]) - th_f[0]) % (2 * math.pi)
        ia = np.round(th_v / (2 * math.pi / len(th_f))).astype(int) % len(th_f)
        ib = np.clip(np.round((dv[sel] - d_lo) / dd).astype(int), 0, len(d_f) - 1)
        zj_v = np.interp(th_v + th_f[0], th_f, zj_f, period=2 * math.pi)
        near = np.abs(Vs[:, 2] - zj_v) < 1.0                 # this junction's covering, not another level's
        Es = np.where(np.isfinite(E), E, -np.inf)
        np.maximum.at(Es, (ia[near], ib[near]), Vs[near, 2])
        E = np.where(np.isfinite(Es), Es, E)
    return th_f, d_f, E


def dressed_flashing(g, roof_name, body_name, up=0.24, apron=0.26, t=0.012, gap=0.008, step=0.05, nd=8,
                     d_face=0.055, tuck=0.035, cheek=True, check=True, cheek_kw=None, sub=6, dd=0.005, smooth=2,
                     dress="tight", taper=3, min_apron=0.05, max_lift=0.05, max_foot=0.05, butt=0.015,
                     butt_clear=0.03, lift_aim=0.03, foot_cost=4.0, end_line=True, normal_t=6.0, lift_rays=True,
                     passes=12, layer_tol=0.002, foot_d=None, adaptive=False, blunt_drip=False):
    """KIT COMPONENT: see the module doc.  up: upstand height above the junction; apron: apron width over the
    covering (limited by the room before the eave lip); t: lead thickness; gap: clearance of the apron's underside
    over the covering's upper envelope; nd: apron vertices across; d_face: upstand standoff from the nominal face
    (clears the stone relief); tuck: how far the upstand head is let into the wall.
    dress="tight" (round 6, default): every apron vertex starts on its OWN station's envelope and is lifted only as
    far as the split sheet needs to clear the covering (`_dress_tight`): the lead lies `gap` over the course it
    laps, rises over a hip board only where the board is, and the upstand foot sits on the local roof line.  The
    apron is laid only where at least d_face + min_apron of roof lies before the lip (it never overhangs the lip),
    and over the last `taper` stations of every open run it narrows monotonically to d_face + min_apron, closing on
    a planar end cap over the eave cheek.  The build fails (flashing_clip_check) on any interpenetration, any
    self-intersection, any drip-edge lift over `max_lift` and any upstand foot more than `max_foot` over the local
    covering.
    dress="max": the round-5 profile (cell-wide envelope maximum, max-filtered over +-`smooth` stations; it floats
    8-13 cm over the courses on falling roofs -- kept only to reproduce round-5 files).  Registers the body in the
    tier's `flashings` (the seal probe tests it).
    Round 7 (tight only; v2 round-6 audit), all optional keywords:
      foot_d: the first apron vertex stands foot_d out from the foot (the rest evenly spaced to the drip), so a
        course rising away from the wall (the back gutter) lifts that vertex, not the foot;
      foot_cost: the upstand-foot corners cost this much more to lift in `_dress_tight`, so a shingle standing
        mid-cell tilts the sheet up outward instead of lifting the foot off the roof line (the max_foot gate holds
        at the kit default, no recipe override);
      lift_rays: the drip-edge pull-in loop measures each station's lift exactly as the gate does (rays down from
        1 cm past the drip vertex, highest hit of the 1.2 cm footprint) for up to `passes` passes; a station still
        over lift_aim at the shortest apron (a butt right at its foot) is dressed on over that butt and ends on the
        course below it;
      end_line: every open run's end station and its `taper` stations are dressed as ONE straight line from the
        upstand foot to the drip corner (the lowest line clearing the dressed sheet), so each run ends in one clean
        turned-down corner, not a course-following outline;
      normal_t: the lead keeps its thickness t NORMAL to the sheet (top = underside + t * sqrt(1 + slope^2), the
        factor capped at normal_t), so a steep step in the dressed sheet never leaves the top and the underside
        within a few mm of each other (doubled shells);
      layer_tol: flashing_clip_check also fails on non-adjacent faces closer than this (near-coincident layers);
      adaptive: the apron is dressed and gated on half-`step` stations, then every other station is dropped
        wherever the sheet between its neighbours still clears it (same apron, within 6 mm of the dressed height):
        half-step stations remain only where a staggered course or a hip needs them (run ends, steps, hips).
    The eave cheek is fitted to the real masonry envelope (eave_cheek(fit=True)) and checked against every masonry
    mesh round it: any cheek / stone / mortar pair fails the build."""
    roof = g.roofs[roof_name]["roof"]
    body = g.body(body_name)
    tight = dress == "tight"
    adapt = bool(tight and adaptive)
    if adapt:                       # round 7: dress on half-step stations, keep only those the sheet needs
        step = 0.5 * step
        taper = 2 * int(taper)
    n, ths, zj = _junction(g, roof, body, step)
    P = body.point(ths, zj)
    pf = roof_support(roof, P[:, 0], P[:, 1])
    room = roof.p_lip - pf - 0.03
    if tight:
        ok = (room > d_face + min_apron) & (pf > roof.Pp[-1] + 0.05) & (zj > body.z0 + 0.05) & (zj < body.z1 - up)
        ap = np.clip(room, d_face + min_apron, apron)
        if taper and not ok.all():                   # narrow the apron monotonically onto the run ends
            for ids, _closed in _runs(ok):
                kk = min(int(taper), len(ids) // 2)
                for e in range(kk):
                    f = (e + 1.0) / (kk + 1.0)
                    for i in (ids[e], ids[-1 - e]):
                        ap[i] = min(ap[i], d_face + min_apron + (ap[i] - d_face - min_apron) * f)
    else:
        ok = (room > 0.06) & (pf > roof.Pp[-1] + 0.05) & (zj > body.z0 + 0.05) & (zj < body.z1 - up)
        ap = np.minimum(apron, np.maximum(room, d_face + 0.06))
    th_f, d_f, E = covering_envelope(g, roof_name, body, ths, zj, -0.02, float(ap.max()) + 0.04, sub=sub, dd=dd)
    if tight:
        # end the apron ON the course it laps: course butts (a downward step of more than `butt` m in one radial
        # sample over the course's own fall) are found over the station's whole span (both neighbouring
        # intervals, so the edge between two stations is covered too); the drip stops `butt_clear` short of the
        # first butt beyond the foot.  Shingle butts are staggered along a course, so a lead dressed down over a
        # butt between 5 cm stations would be held up by the next shingle: it never bridges one.
        a0 = d_face + 0.03
        ap_room = ap.copy()                          # the widest apron the station allows (before the butt stop)
        b_first = np.full(n, np.inf)                 # the first course butt beyond the foot, per station
        for i in np.flatnonzero(ok):
            rows = E[np.arange(sub * i - sub, sub * i + sub + 1) % len(th_f)]
            B = []
            for row in rows:
                fin = np.isfinite(row)
                if fin.sum() < 4:
                    continue
                dz = row[:-1] - row[1:]                       # fall per radial sample
                okp = fin[:-1] & fin[1:]
                fall = float(np.median(dz[okp])) if okp.any() else 0.0
                B += list(d_f[:-1][okp & (dz - fall > butt) & (d_f[:-1] > d_face - t)] + 0.5 * dd)
            if not B:
                continue
            B = np.array(B)
            B = B[B > d_face + 0.01]                      # a step right at the foot is under the upstand
            if len(B):
                b_first[i] = float(B.min())
                ap[i] = float(np.clip(B.min() - butt_clear, a0, ap[i]))
    s = np.linspace(0.0, 1.0, nd)

    def _stations(ap_):
        """(n, nd) apron radial stations: evenly spaced, or (round 7, foot_d) with the first one foot_d out from
        the foot so a course rising away from the wall (the back gutter) lifts the next vertex, not the foot."""
        if tight and foot_d and nd >= 4:
            d1 = np.minimum(d_face + foot_d, d_face + 0.25 * (ap_ - d_face))
            return np.concatenate([np.full((len(ap_), 1), d_face), d1[:, None] +
                                   (ap_ - d1)[:, None] * np.linspace(0.0, 1.0, nd - 1)[None, :]], 1)
        return d_face + (ap_[:, None] - d_face) * s[None, :]
    Dk = _stations(ap)                                                   # (n, nd) apron radial stations
    z_drip = None
    if tight:
        # dress, then pull in any drip edge that would still stand more than lift_aim over the course just beyond
        # it (the next course is staggered or a neighbouring shingle holds the sheet up): up to 4 passes
        Efin = np.where(np.isfinite(E), E, -np.inf)
        nf = len(th_f)
        cost = None
        if foot_cost and foot_cost != 1.0:
            cost = np.ones((n, nd))
            cost[:, 0] = float(foot_cost)
        ends = np.zeros(n, bool)                     # the end station + taper stations of every open run
        if end_line and not ok.all():
            for ids, _closed in _runs(ok):
                kk = min(int(taper) + 1, len(ids))
                ends[ids[:kk]] = True
                ends[ids[-kk:]] = True
        bvh_c = None
        if lift_rays:
            from .seal_probe import _bvh
            Vc_, Tc_, _ = _world_tris(_tier_meshes(g, roof_name))
            bvh_c = _bvh(Vc_, Tc_)
        hard = np.zeros(n, bool)                     # stations dressed on over the butt onto the next course
        settled = np.zeros(n, bool)
        est_pre = np.full(n, np.nan)
        ap_pre = ap.copy()
        n_pass = 1 if not lift_rays else int(passes)
        for _pass in range(max(5, n_pass)):
            Dk = _stations(ap)
            U = _dress_tight(E, d_f, sub, Dk, ap, ok, zj, t + dd, 0.012, gap, cost=cost)
            if ends.any():
                U = _end_lines(U, (Dk - d_face) / np.maximum(ap - d_face, 1e-6)[:, None], ends & ok)
            z_drip = U[:, -1] + 0.5 * t
            est = np.full(n, -np.inf)
            for i in np.flatnonzero(ok):
                rr = np.arange(sub * i - sub // 2, sub * i + sub // 2 + 1) % nf
                e_d = np.max(Efin[rr][:, (d_f >= ap[i] - dd) & (d_f <= ap[i] + 0.012)], initial=-np.inf)
                # the drip edge turns down onto the course: 3 mm over the highest covering under it
                z_drip[i] = min(z_drip[i], max(e_d + 0.003, U[i, -1] - 0.004))
                if bvh_c is None:
                    rr1 = np.arange(sub * i - 1, sub * i + 2) % nf
                    beyond = Efin[rr1][:, (d_f >= ap[i] + 0.012) & (d_f <= ap[i] + 0.026)]
                    if np.isfinite(beyond).any():
                        est[i] = z_drip[i] - float(np.max(beyond))
            if bvh_c is not None:
                est = _drip_lift(bvh_c, body, ths, z_drip, ap + 0.008, ok)
            over = ok & (est > lift_aim)
            bad = over & (ap > d_face + 0.03 + 1e-6) & ~hard
            stuck = over & ~bad & ~hard
            # a station dressed on over a butt (below) that now stands higher than before goes back, once
            worse = hard & ~settled & np.isfinite(est_pre) & (est > est_pre + 1e-4)
            settled |= hard
            last = _pass >= max(4, n_pass - 1)
            if (not bad.any() and not stuck.any() and not worse.any()) or last:
                break
            if _pass >= max(4, n_pass - 1) - 1 and over.any():
                for i in np.flatnonzero(over)[:8]:
                    log(f"    drip over the course at {math.degrees(ths[i]):.0f} deg: {est[i]:.3f} m, apron "
                        f"{ap[i]:.3f} (room {ap_room[i]:.3f}, first butt {b_first[i]:.3f}), dressed on {hard[i]}")
            ap[worse] = ap_pre[worse]
            ap[bad] = np.maximum(d_face + 0.03, ap[bad] - 0.015)
            # a station still standing over the course at the shortest apron has a butt right at its foot: the lead
            # is dressed on over that butt and ends `butt_clear` + 1 cm out on the course below it instead
            ext = stuck & np.isfinite(b_first)
            est_pre[ext], ap_pre[ext] = est[ext], ap[ext]
            ap[ext] = np.clip(b_first[ext] + butt_clear + 0.01, a0, np.maximum(ap_room[ext], a0))
            hard |= stuck
    else:
        U = np.zeros((n, nd))
        for i in range(n):
            nb = [(i - 1) % n, i, (i + 1) % n]
            fi = np.arange(sub * i - sub, sub * i + sub + 1) % (n * sub)
            Ew = E[fi]
            for k in range(nd):
                lo = -0.02 if k == 0 else float(Dk[nb, k - 1].min())
                hi = float(Dk[nb, k + 1].max()) if k < nd - 1 else float(ap[nb].max()) + 0.03
                cm = (d_f >= lo - dd) & (d_f <= hi + dd)
                v = Ew[:, cm]
                v = v[np.isfinite(v)]
                U[i, k] = (float(v.max()) if len(v) else zj[i]) + gap
        if smooth:          # dressed lead spans the course butts: max over +-smooth stations (valid ones), no teeth
            Um = np.where(ok[:, None], U, -np.inf)
            U = np.maximum(U, np.max([np.roll(Um, s_, axis=0) for s_ in range(-smooth, smooth + 1)], axis=0))
    blunt = bool(tight and blunt_drip)
    tk = np.full((n, nd), float(t))                  # top over underside at each apron vertex
    if tight and normal_t and normal_t > 1.0:
        tk = t * _slope_factor(U, Dk, ok, body, ths, cap=float(normal_t))
    prof = []
    for i in range(n):
        u = U[i]
        z_up = max(zj[i] + up, u[0] + tk[i, 0] + 0.10)
        zd = float(z_drip[i]) if z_drip is not None else u[-1] + 0.5 * t
        top = [(-tuck, z_up), (d_face, z_up)] + [(Dk[i, k], u[k] + tk[i, k]) for k in range(nd)] + \
              [(ap[i] + 0.008, zd)]
        if tight:           # underside exactly t under the top at the same (station, d): a flat foot, then the back
            bot = [(Dk[i, k], u[k]) for k in range(nd - 1, -1, -1)] + [(d_face - t, u[0]), (d_face - t, z_up - t),
                                                                       (-tuck, z_up - t)]
            if blunt:       # round 7: a blunt drip (a 6 mm turned-down face), not a knife edge that doubles over
                top[-1] = (ap[i] + 0.006, zd + 0.5 * t)
                bot = [(ap[i] + 0.008, zd)] + bot
        else:
            bot = [(Dk[i, k], u[k]) for k in range(nd - 1, 0, -1)] + [(d_face - t, u[0]), (d_face - t, z_up - t),
                                                                       (-tuck, z_up - t)]
        prof.append(top + bot)
    m = len(prof[0])
    D = np.array([[p[0] for p in pts] for pts in prof])
    Z = np.array([[p[1] for p in pts] for pts in prof])
    TH = np.broadcast_to(ths[:, None], D.shape)
    W = body.point(TH, Z, d=D)
    acc = Acc(g.name(f"{roof_name}_{body_name}_flashing"))
    if tight:
        # planar end cap in the end station's radial plane, all convex pieces: the head, the upstand, the foot
        # triangle, one quad per apron bay (top row over its underside) and the drip triangle
        cap = [(0, 1, m - 2, m - 1), (1, 2, m - 3, m - 2), (2, m - 4, m - 3)] + \
              [(2 + k, 3 + k, m - 5 - k, m - 4 - k) for k in range(nd - 1)] + \
              ([(nd + 1, nd + 2, nd + 3, nd + 4)] if blunt else [(nd + 1, nd + 2, nd + 3)])
        keep = np.ones(n, bool)
        if adapt:
            keep = _adaptive_keep(U, ap, z_drip, U + tk, ok, ends if end_line else np.zeros(n, bool))
            log(f"  dressed flashing {roof_name}/{body_name}: adaptive stations, {int((keep & ok).sum())} of "
                f"{int(ok.sum())} half-step stations kept ({step * 100:.2f} cm half step)")
        n_run = _tri_sweep(acc, W[keep], D[keep], Z[keep], ok[keep], cap)
    else:
        n_run = _sweep(acc, W, ok, m)
    if not n_run:
        log(f"  dressed flashing {roof_name}/{body_name}: no junction")
        return None
    ob = finalize(acc, g.sub(roof_name), smooth_deg=50.0)
    rise = U[:, 0] - zj
    # the upstand foot over the LOCAL roof line (the covering envelope under the foot at its own station)
    cm = (d_f >= d_face - t - dd) & (d_f <= d_face + dd)
    hs = sub // 2                                  # the station's own span: +- half a station round the body
    Eface = np.stack([E[(sub * np.arange(n) + j) % len(th_f)][:, cm] for j in range(-hs, hs + 1)], 1)
    Eface = np.max(np.where(np.isfinite(Eface), Eface, -np.inf), axis=(1, 2))
    foot = U[:, 0] - np.where(np.isfinite(Eface), Eface, zj)
    log(f"  dressed flashing {roof_name}/{body_name} ({dress}): {int(ok.sum())}/{n} stations, {n_run} run(s), apron "
        f"over the covering envelope (+{gap * 1000:.0f} mm), upstand foot {foot[ok].min():.3f}..{foot[ok].max():.3f} m "
        f"over the local roof line ({rise[ok].min():.3f}..{rise[ok].max():.3f} m over the base-surface junction)")
    g.roofs[roof_name].setdefault("flashings", []).append(body_name)
    ch = None
    if cheek and not ok.all():
        kw = dict(cheek_kw or {})
        kw.setdefault("step", step)                     # the cheek reads the apron's stations
        if tight:
            kw.setdefault("top_cap", np.where(ok, U[:, 0] - 0.004, np.inf))   # cheek top stays under the apron foot
            kw.setdefault("apron_under", (Dk, U, ok))
        ch = eave_cheek(g, roof_name, body_name, ok=ok, **kw)
    if check:
        if tight:
            flashing_clip_check(g, roof_name, ob, body_name=body_name, max_lift=max_lift,
                                foot=dict(lift=foot, ok=ok, ths=ths, max=max_foot, point=body.point(ths, U[:, 0])),
                                layer_tol=layer_tol)
            if ch is not None:
                # round 7: the cheek against every masonry mesh round it (its body's rubble, mortar and an engaged
                # neighbour's stones) and against itself; the eave members still run into it (declared)
                Vch, _, _ = _world_tris([ch])
                flashing_clip_check(g, roof_name, ch, tier=False, others=False,
                                    bodies=masonry_meshes(g, Vch.min(0) - 0.05, Vch.max(0) + 0.05),
                                    layer_tol=layer_tol)
        else:
            flashing_clip_check(g, roof_name, ob, self_check=False, others=False)
    return ob


def masonry_meshes(g, lo=None, hi=None):
    """KIT HELPER (round 7): every mesh of every declared body's collection (stones, quoins, mortar, coping, belt
    boards), optionally only those whose world bounding box overlaps the box lo..hi."""
    out = []
    for b in g.bodies:
        if b not in g.subs:
            continue
        for o in g.subs[b].all_objects:
            if o.type != "MESH" or not len(o.data.polygons):
                continue
            if lo is not None:
                from mathutils import Vector
                bb = np.array([o.matrix_world @ Vector(c) for c in o.bound_box])
                if (bb.max(0) < lo).any() or (bb.min(0) > hi).any():
                    continue
            out.append(o)
    return out


def masonry_envelope(g, body, ths, zs, sub=6, d_max=0.30, d_min=-0.05, objs=None):
    """KIT HELPER (round 7): the real OUTER envelope of the masonry round `body` (the wall-side sibling of
    covering_envelope).  For every station th (the station's own span: `sub` fine angles each way, i.e. both
    neighbouring intervals) and every height z in zs: horizontal rays from d_max straight in towards the body axis
    against every masonry mesh near it (this body's rubble and mortar, and an engaged neighbour's stones), plus every
    masonry vertex splatted into its (station, z) cell, because a convex stone's outermost point is a vertex.
    Returns E (len(ths), len(zs)): the largest distance (m, + outside the nominal face) any masonry stands out in
    that cell, -inf where none.  A ray that starts inside another body's masonry reports ~d_max (blocked)."""
    from mathutils import Vector
    from .seal_probe import _bvh
    n = len(ths)
    zs = np.asarray(zs, float)
    dz = float(zs[1] - zs[0]) if len(zs) > 1 else 0.005
    dth = 2 * math.pi / n
    if objs is None:
        P0 = body.point(ths, np.full(n, float(zs.mean())), d=d_max)
        lo = np.array([P0[:, 0].min(), P0[:, 1].min(), zs.min()]) - d_max - 0.5
        hi = np.array([P0[:, 0].max(), P0[:, 1].max(), zs.max()]) + d_max + 0.5
        objs = masonry_meshes(g, lo, hi)
    E = np.full((n, len(zs)), -np.inf)
    if not objs:
        return E
    V, T, _ = _world_tris(objs)
    bvh = _bvh(V, T)
    span = d_max - d_min
    for i in range(n):
        for j in range(-sub, sub + 1):
            th = float(ths[i]) + j * dth / sub
            P = body.point(np.full(len(zs), th), zs, d=d_max)
            dr = Vector((-math.cos(th), -math.sin(th), 0.0))
            for q in range(len(zs)):
                h = bvh.ray_cast(Vector((float(P[q, 0]), float(P[q, 1]), float(P[q, 2]))), dr, span)
                if h[0] is not None:
                    E[i, q] = max(E[i, q], float(body.dist(np.array(h[0]))))
    dv = body.dist(V)
    sel = (dv > d_min) & (dv < d_max) & (V[:, 2] > zs.min() - dz) & (V[:, 2] < zs.max() + dz)
    if sel.any():
        Vs, ds = V[sel], dv[sel]
        th_v = (np.arctan2(Vs[:, 1] - body.c[1], Vs[:, 0] - body.c[0]) - ths[0]) % (2 * math.pi)
        iz = np.clip(np.round((Vs[:, 2] - zs[0]) / dz).astype(int), 0, len(zs) - 1)
        i0 = np.floor(th_v / dth).astype(int)
        for s_ in (0, 1):               # a vertex inside an interval belongs to the stations at both of its ends
            np.maximum.at(E, ((i0 + s_) % n, iz), ds)
    return E


def eave_cheek(g, roof_name, body_name, ok=None, step=0.05, d_out=0.06, t=0.012, tuck=0.035, pad=0.03,
               reach=(-0.03, 0.12), lip_pad=0.15, top_cap=None, fit=True, clear=0.004, d_block=0.07,
               apron_under=None):
    """KIT COMPONENT: see the module doc.  ok: the flashing's valid stations (same `step`), where the apron covers
    the top of the junction (the cheek then stops at the roof base surface under it); d_out: plate standoff from
    the nominal face; reach: the shell round the face (m) in which tier members are taken to meet it; pad: how far
    the cheek runs past the members' lowest / highest point; top_cap (round 6, optional, per station): the cheek
    top never rises above it (dressed_flashing passes its apron foot, so a lead dressed down onto the covering
    still laps over the cheek instead of meeting it).
    fit (round 7, default; v2 round-6 audit: the plate stood 6 cm off the NOMINAL face, inside the rubble that stands
    proud of it, 1,182-1,216 cheek / stone pairs across the plate's face): the plate stands `clear` + t off the real
    outer envelope of the masonry (`masonry_envelope`, one offset per run so the plate stays one straight lead
    face), and its top and bottom returns are dressed back onto the masonry -- each return ends `clear` outside the
    outermost stone along its own line instead of being tucked through the rubble -- so no stone, quoin or mortar
    face can pass through any part of the cheek.  A station whose envelope stands more than `d_block` out (the
    rays start inside an engaged neighbour's masonry, at the re-entrant) is left out.  fit=False: the round-6
    plate."""
    t_rec = g.roofs[roof_name]
    roof = t_rec["roof"]
    body = g.body(body_name)
    n, ths, zj = _junction(g, roof, body, step)
    if ok is None:
        ok = np.zeros(n, bool)
    Pm = body.point(ths, zj, d=0.03)
    p = roof_support(roof, Pm[:, 0], Pm[:, 1])
    under = (p > float(t_rec["p_wall"]) - 0.02) & (p < float(roof.p_lip) + lip_pad)
    objs = _tier_meshes(g, roof_name)
    V, _, _ = _world_tris(objs)
    dist = body.dist(V)
    sel = (dist > reach[0]) & (dist < reach[1]) & (V[:, 2] > body.z0) & (V[:, 2] < body.z1)
    V = V[sel]
    if not len(V):
        return None
    th_v = np.arctan2(V[:, 1] - body.c[1], V[:, 0] - body.c[0]) % (2 * math.pi)
    b = np.round(th_v / (2 * math.pi / n)).astype(int) % n
    zmin = np.full(n, np.inf)
    zmax = np.full(n, -np.inf)
    np.minimum.at(zmin, b, V[:, 2])
    np.maximum.at(zmax, b, V[:, 2])
    has = np.isfinite(zmin) & under
    # dilate one station each way (the members' cut ends span a station)
    zlo = np.minimum.reduce([np.where(has, zmin, np.inf)[(np.arange(n) + s) % n] for s in (-1, 0, 1)])
    zhi = np.maximum.reduce([np.where(has, zmax, -np.inf)[(np.arange(n) + s) % n] for s in (-1, 0, 1)])
    use = np.isfinite(zlo) & (under | np.roll(under, 1) | np.roll(under, -1))
    if not use.any():
        return None
    Pb = body.point(ths, zj, d=d_out)
    zbase = roof_z(roof, Pb[:, 0], Pb[:, 1])
    top = np.where(ok & np.isfinite(zbase), np.minimum(zhi + pad, zbase + 0.02), zhi + pad)
    if top_cap is not None:
        top = np.minimum(top, np.asarray(top_cap, float))
    bot = zlo - pad
    top = np.maximum(top, bot + 2 * t + 0.02)
    top = np.where(use, top, zj + 0.1)                       # unused stations: finite placeholders (not swept)
    bot = np.where(use, bot, zj)
    dp = np.full(n, float(d_out))                            # plate face, per station
    d_top = np.full(n, -float(tuck))                         # inner end of the top / bottom returns
    d_bot = np.full(n, -float(tuck))
    if fit:
        dz = 0.005
        zs = np.arange(float(bot[use].min()) - 0.02, float(top[use].max()) + 0.02 + 1e-9, dz)
        Em = masonry_envelope(g, body, ths, zs, sub=max(2, int(math.ceil(step / 0.006))),
                              d_max=max(0.30, d_block + 0.1))
        Ef = np.where(np.isfinite(Em), Em, -np.inf)
        Ef = np.maximum(Ef, np.maximum(np.roll(Ef, 1, 1), np.roll(Ef, -1, 1)))   # a stone edge between two rows

        def band(i, z0, z1):
            sel = (zs >= z0 - 0.5 * dz) & (zs <= z1 + 0.5 * dz)
            return float(Ef[i, sel].max()) if sel.any() else -np.inf
        env = np.array([band(i, bot[i], top[i]) if use[i] else -np.inf for i in range(n)])
        n_blk = int((use & (env > d_block)).sum())
        use = use & (env <= d_block)
        for ids, _closed in _runs(use):
            dp[ids] = max(float(d_out), float(env[ids].max()) + t + clear + 0.008)   # returns >= 8 mm wide
        if apron_under is not None:
            # the plate now stands further out than the apron foot: keep the whole top return under the apron's
            # dressed underside out to the plate face (the apron falls away from the wall over the course)
            Da, Ua, oka = apron_under
            for i in np.flatnonzero(use & oka):
                sel = Da[i] <= dp[i] + 0.01
                ucap = float(Ua[i][sel].min()) if sel.any() else float(Ua[i, 0])
                ucap = min(ucap, float(np.interp(dp[i] + 0.01, Da[i], Ua[i])))
                top[i] = min(top[i], ucap - 0.004)
            top = np.where(use, np.maximum(top, bot + 2 * t + 0.02), top)
        for i in np.flatnonzero(use):
            # a return slopes between stations whose top / bottom differ: clear every height it passes through
            nb = [j for j in ((i - 1) % n, i, (i + 1) % n) if use[j]]
            et = band(i, min(top[j] for j in nb) - t - clear, max(top[j] for j in nb) + clear)
            eb = band(i, min(bot[j] for j in nb) - clear, max(bot[j] for j in nb) + t + clear)
            # the return ends `clear` outside the outermost masonry on its line, never deeper than `tuck`
            d_top[i] = min(max(et + clear, -tuck), dp[i] - t - 0.003)
            d_bot[i] = min(max(eb + clear, -tuck), dp[i] - t - 0.003)
        if use.any():
            log(f"  eave cheek {roof_name}/{body_name}: fitted to the masonry envelope, plate {dp[use].min():.3f}.."
                f"{dp[use].max():.3f} m off the nominal face (masonry out to {env[use].max():.3f} m), returns end "
                f"{min(d_top[use].min(), d_bot[use].min()):.3f}..{max(d_top[use].max(), d_bot[use].max()):.3f} m, "
                f"{n_blk} station(s) blocked by an engaged neighbour")
        if not use.any():
            return None
    prof = []
    for i in range(n):
        tp, bt, do, dt_, db_ = float(top[i]), float(bot[i]), float(dp[i]), float(d_top[i]), float(d_bot[i])
        prof.append([(dt_, tp), (do, tp), (do, bt), (db_, bt), (db_, bt + t), (do - t, bt + t),
                     (do - t, tp - t), (dt_, tp - t)])
    m = len(prof[0])
    D = np.array([[q[0] for q in pts] for pts in prof])
    Z = np.array([[q[1] for q in pts] for pts in prof])
    TH = np.broadcast_to(ths[:, None], D.shape)
    W = body.point(TH, Z, d=D)
    acc = Acc(g.name(f"{roof_name}_{body_name}_flashing_cheek"))
    n_run = _sweep(acc, W, use, m)
    ob = finalize(acc, g.sub(roof_name), smooth_deg=50.0) if n_run else None
    log(f"  eave cheek {roof_name}/{body_name}: {int(use.sum())} stations in {n_run} run(s), z {bot[use].min():.2f}"
        f"..{top[use].max():.2f}")
    return ob


def _pt(p):
    return tuple(round(float(x), 2) for x in p)


def self_intersections(ob):
    """KIT HELPER (round 6): the non-adjacent intersecting triangle pairs of one mesh object (pairs sharing a vertex
    are adjacent and skipped).  Returns (count, world point of the first pair or None)."""
    from .seal_probe import _bvh
    Vf, Tf, _ = _world_tris([ob])
    bf = _bvh(Vf, Tf)
    pr = np.array(bf.overlap(bf), np.int64).reshape(-1, 2)
    pr = pr[pr[:, 0] < pr[:, 1]]
    if not len(pr):
        return 0, None
    share = (Tf[pr[:, 0]][:, :, None] == Tf[pr[:, 1]][:, None, :]).any(axis=(1, 2))
    pr = pr[~share]
    if not len(pr):
        return 0, None
    return len(pr), _pt(Vf[Tf[pr[0, 0]]].mean(0))


def flashing_lift(g, roof_name, body_name, ob, bins=360, out=0.01, above=0.4, foot_w=0.0):
    """KIT HELPER (round 6): the drip-edge lift of a flashing over the covering it laps.  Per `bins` sectors round
    the body: the flashing's outermost vertex, then `out` m further out along the radial, a ray straight down onto
    the tier's covering (every non-flashing mesh of the tier).  foot_w > 0: the course under the edge is the HIGHEST
    hit of a 3 x 3 footprint (+-foot_w along the edge, out +- foot_w / 2 radially), so a ray that drops into the
    joint between two shingles does not count as lift.  Returns (sector angles in deg, vertex points, lift in m;
    NaN where no ray finds covering)."""
    from mathutils import Vector
    from .seal_probe import _bvh
    body = g.body(body_name)
    Vf, _, _ = _world_tris([ob])
    dv = body.dist(Vf)
    th = np.arctan2(Vf[:, 1] - body.c[1], Vf[:, 0] - body.c[0]) % (2 * math.pi)
    b = (th / (2 * math.pi / bins)).astype(int) % bins
    order = np.lexsort((dv, b))
    last = np.flatnonzero(np.diff(np.append(b[order], -1)) != 0)
    idx = order[last]
    V, T, _ = _world_tris(_tier_meshes(g, roof_name))
    bvh = _bvh(V, T)
    down = Vector((0.0, 0.0, -1.0))
    lift = np.full(len(idx), np.nan)
    offs = [(0.0, 0.0)] if foot_w <= 0 else [(a, b) for a in (-foot_w, 0.0, foot_w) for b in (-0.5 * foot_w, 0.0,
                                                                                              0.5 * foot_w)]
    for q, i in enumerate(idx):
        P = Vf[i]
        rad = np.array([math.cos(th[i]), math.sin(th[i])])
        tan = np.array([-rad[1], rad[0]])
        top = None
        for a, b in offs:
            o = P[:2] + (out + b) * rad + a * tan
            h = bvh.ray_cast(Vector((float(o[0]), float(o[1]), float(P[2]) + above)), down, above + 1.0)
            if h[0] is not None and (top is None or h[0][2] > top):
                top = float(h[0][2])
        if top is not None:
            lift[q] = float(P[2]) - top
    return np.degrees(th[idx]), Vf[idx], lift


def near_layers(ob, tol=0.002):
    """KIT HELPER (round 7): near-coincident layers of one mesh object -- pairs of NON-adjacent triangles (no shared
    vertex) where one triangle's centroid lies within `tol` of the other (a doubled shell, smeared shading).
    Returns (pair count, face count, world point of the first or None)."""
    from mathutils import Vector
    from .seal_probe import _bvh
    Vf, Tf, _ = _world_tris([ob])
    if not len(Tf):
        return 0, 0, None
    bf = _bvh(Vf, Tf)
    C = Vf[Tf].mean(1)
    pairs, faces = 0, set()
    first = None
    for i in range(len(Tf)):
        ti = set(Tf[i].tolist())
        for hit in bf.find_nearest_range(Vector((float(C[i, 0]), float(C[i, 1]), float(C[i, 2]))), tol):
            j = hit[2]
            if j == i or ti & set(Tf[j].tolist()):
                continue
            pairs += 1
            faces.add(i)
            if first is None:
                first = _pt(C[i])
    return pairs, len(faces), first


def flashing_clip_check(g, roof_name, ob, fail=True, skip=("_flashing",), body_name=None, max_lift=None, foot=None,
                        self_check=True, others=True, lift_foot_w=0.012, tier=True, bodies=None, layer_tol=None):
    """KIT CHECK: see the module doc.  Returns {object name: intersecting triangle pairs}.  Round 6 (all optional):
    self_check -- the flashing against ITSELF (non-adjacent pairs, `self_intersections`; note 1, closed solid
    pieces); others -- against the tier's other flashing pieces (eave cheeks, other aprons); body_name + max_lift --
    the drip-edge lift test (`flashing_lift`): any sector whose drip edge stands more than max_lift over the covering
    fails, named by its angle round the body and its world point; foot=dict(lift, ok, ths, max, point) -- the same
    for the upstand foot over the local roof line, per station.  Round 7 (optional): tier=False skips the tier pool;
    bodies -- a list of masonry meshes (masonry_meshes) the piece must not touch (the eave cheek against its body's
    rubble and mortar); layer_tol -- near-coincident layers (`near_layers`, non-adjacent faces closer than
    layer_tol) fail as well."""
    from .seal_probe import _bvh
    if ob is None:
        return {}
    Vf, Tf, _ = _world_tris([ob])
    bf = _bvh(Vf, Tf)
    out = {}
    worst = None
    pool = list(_tier_meshes(g, roof_name, skip=skip)) if tier else []
    if others:
        pool += [o for o in _tier_meshes(g, roof_name, skip=()) if "_flashing" in o.name and o.name != ob.name]
    pool += [o for o in (bodies or ()) if o.name != ob.name and o not in pool]
    for o in pool:
        V, T, _ = _world_tris([o])
        pairs = bf.overlap(_bvh(V, T))
        if pairs:
            out[o.name] = len(pairs)
            if worst is None:
                a = pairs[0][0]
                worst = (o.name, _pt(Vf[Tf[a]].mean(0)))
    msgs = []
    rep = f"{sum(out.values())} intersecting triangle pairs with the " + \
        ("tier" if tier else "") + (" and " if tier and bodies else "") + ("masonry" if bodies else "") + \
        (f" (first at {worst[1]}, {worst[0]})" if worst else "")
    if layer_tol:
        n_lay, f_lay, p_lay = near_layers(ob, layer_tol)
        rep += f", {n_lay} near-coincident face pairs (< {layer_tol * 1000:.0f} mm)"
        if n_lay:
            out[ob.name + " (layers)"] = n_lay
            msgs.append(f"{n_lay} near-coincident non-adjacent face pairs on {f_lay} faces (closer than "
                        f"{layer_tol * 1000:.0f} mm), first at {p_lay}")
    if self_check:
        n_self, p_self = self_intersections(ob)
        rep += f", {n_self} with itself"
        if n_self:
            out[ob.name + " (self)"] = n_self
            msgs.append(f"{n_self} self-intersecting triangle pairs, first at {p_self}")
            if worst is None:
                worst = (ob.name + " (self)", p_self)
    if body_name is not None and max_lift is not None:
        _a1, _p1, l1 = flashing_lift(g, roof_name, body_name, ob)          # single ray (into joints as well)
        f1 = np.isfinite(l1)
        if f1.any():
            rep += (f"; drip-edge lift, single ray: median {np.median(l1[f1]):.3f}, p90 "
                    f"{np.percentile(l1[f1], 90):.3f}, max {l1[f1].max():.3f} m")
        ang, pts, lift = flashing_lift(g, roof_name, body_name, ob, foot_w=lift_foot_w)
        fin = np.isfinite(lift)
        if fin.any():
            lf = lift[fin]
            rep += (f"; over the course under the edge ({lift_foot_w * 100:.1f} cm footprint): median "
                    f"{np.median(lf):.3f}, p90 {np.percentile(lf, 90):.3f}, max {lf.max():.3f} m "
                    f"({int(fin.sum())} sectors)")
            bad = np.flatnonzero(fin & (lift > max_lift))
            if len(bad):
                j = bad[np.argmax(lift[bad])]
                out[ob.name + " (lift)"] = len(bad)
                msgs.append(f"{len(bad)} sectors with the drip edge more than {max_lift:.2f} m over the covering, worst "
                            f"{lift[j]:.3f} m at {ang[j]:.0f} deg round {body_name} {_pt(pts[j])}")
    if foot is not None:
        fl = np.where(foot["ok"], foot["lift"], -np.inf)
        rep += f"; upstand foot max {fl.max():.3f} m over the local roof line"
        bad = np.flatnonzero(fl > foot["max"])
        if len(bad):
            j = bad[np.argmax(fl[bad])]
            out[ob.name + " (foot)"] = len(bad)
            msgs.append(f"{len(bad)} stations with the upstand foot more than {foot['max']:.2f} m over the roof line, "
                        f"worst {fl[j]:.3f} m at {math.degrees(foot['ths'][j]):.0f} deg "
                        f"{_pt(foot['point'][j])}")
    pair_out = {k: v for k, v in out.items() if not k.endswith(("(self)", "(lift)", "(foot)", "(layers)"))}
    log(f"  flashing clip check {ob.name}: " + (", ".join(f"{k} {v}" for k, v in out.items()) if out else rep))
    if out:
        log("    " + "; ".join([rep] + msgs))
    if out and fail:
        raise FlashingClipError(f"{ob.name} fails the flashing check on tier {roof_name!r}: " +
                                ", ".join(f"{k}: {v} triangle pairs" for k, v in pair_out.items()) +
                                (f"; first at {worst[1]} ({worst[0]})" if worst else "") +
                                ("; " + "; ".join(msgs) if msgs else "") +
                                ".  Lay the apron over the covering envelope (dressed_flashing) or stop the piece "
                                "under the lead.")
    return out
