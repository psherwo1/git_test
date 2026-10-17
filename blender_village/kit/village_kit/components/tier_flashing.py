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
        world point (fail=False only logs).  Run by dressed_flashing(check=True).
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


def _dress_tight(E, d_f, sub, Dk, ap, ok, zj, d_lo, d_hi, gap):
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
    ww = w00 ** 2 + w10 ** 2 + w11 ** 2 + w01 ** 2
    for _ in range(3):                              # one pass suffices; the rest only mop up float round-off
        z = sum(w * U[ci, ck] for ci, ck, w in corners)
        de = se + gap - z
        if not (de > 1e-5).any():
            break
        de = np.maximum(de, 0.0)
        R = np.zeros_like(U)
        for ci, ck, w in corners:
            np.maximum.at(R, (ci, ck), de * w / ww)
        U = U + R
    return U


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
                     dress="tight", taper=3, min_apron=0.05, max_lift=0.05, max_foot=0.05):
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
    tier's `flashings` (the seal probe tests it)."""
    roof = g.roofs[roof_name]["roof"]
    body = g.body(body_name)
    n, ths, zj = _junction(g, roof, body, step)
    P = body.point(ths, zj)
    pf = roof_support(roof, P[:, 0], P[:, 1])
    room = roof.p_lip - pf - 0.03
    tight = dress == "tight"
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
    s = np.linspace(0.0, 1.0, nd)
    Dk = d_face + (ap[:, None] - d_face) * s[None, :]                    # (n, nd) apron radial stations
    if tight:
        U = _dress_tight(E, d_f, sub, Dk, ap, ok, zj, t + dd, 0.012, gap)
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
    prof = []
    for i in range(n):
        u = U[i]
        z_up = max(zj[i] + up, u[0] + t + 0.10)
        z_drip = u[-1] + 0.5 * t
        if tight:           # the drip edge carries on down the slope of the last bay (dressed onto the course)
            z_drip -= 0.008 * max(0.0, (u[-2] - u[-1]) / max(Dk[i, -1] - Dk[i, -2], 1e-6))
        top = [(-tuck, z_up), (d_face, z_up)] + [(Dk[i, k], u[k] + t) for k in range(nd)] + \
              [(ap[i] + 0.008, z_drip)]
        if tight:           # underside exactly t under the top at the same (station, d): a flat foot, then the back
            bot = [(Dk[i, k], u[k]) for k in range(nd - 1, -1, -1)] + [(d_face - t, u[0]), (d_face - t, z_up - t),
                                                                       (-tuck, z_up - t)]
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
              [(2 + k, 3 + k, m - 5 - k, m - 4 - k) for k in range(nd - 1)] + [(nd + 1, nd + 2, nd + 3)]
        n_run = _tri_sweep(acc, W, D, Z, ok, cap)
    else:
        n_run = _sweep(acc, W, ok, m)
    if not n_run:
        log(f"  dressed flashing {roof_name}/{body_name}: no junction")
        return None
    ob = finalize(acc, g.sub(roof_name), smooth_deg=50.0)
    rise = U[:, 0] - zj
    # the upstand foot over the LOCAL roof line (the covering envelope under the foot at its own station)
    cm = (d_f >= d_face - t - dd) & (d_f <= d_face + dd)
    Eface = E[sub * np.arange(n)][:, cm]
    Eface = np.max(np.where(np.isfinite(Eface), Eface, -np.inf), axis=1)
    foot = U[:, 0] - np.where(np.isfinite(Eface), Eface, zj)
    log(f"  dressed flashing {roof_name}/{body_name} ({dress}): {int(ok.sum())}/{n} stations, {n_run} run(s), apron "
        f"over the covering envelope (+{gap * 1000:.0f} mm), upstand foot {foot[ok].min():.3f}..{foot[ok].max():.3f} m "
        f"over the local roof line ({rise[ok].min():.3f}..{rise[ok].max():.3f} m over the base-surface junction)")
    g.roofs[roof_name].setdefault("flashings", []).append(body_name)
    ch = None
    if cheek and not ok.all():
        kw = dict(cheek_kw or {})
        if tight:
            kw.setdefault("top_cap", np.where(ok, U[:, 0] - 0.004, np.inf))   # cheek top stays under the apron foot
        ch = eave_cheek(g, roof_name, body_name, ok=ok, **kw)
    if check:
        if tight:
            flashing_clip_check(g, roof_name, ob, body_name=body_name, max_lift=max_lift,
                                foot=dict(lift=foot, ok=ok, ths=ths, max=max_foot, point=body.point(ths, U[:, 0])))
        else:
            flashing_clip_check(g, roof_name, ob, self_check=False, others=False)
    return ob


def eave_cheek(g, roof_name, body_name, ok=None, step=0.05, d_out=0.06, t=0.012, tuck=0.035, pad=0.03,
               reach=(-0.03, 0.12), lip_pad=0.15, top_cap=None):
    """KIT COMPONENT: see the module doc.  ok: the flashing's valid stations (same `step`), where the apron covers
    the top of the junction (the cheek then stops at the roof base surface under it); d_out: plate standoff from
    the nominal face; reach: the shell round the face (m) in which tier members are taken to meet it; pad: how far
    the cheek runs past the members' lowest / highest point; top_cap (round 6, optional, per station): the cheek
    top never rises above it (dressed_flashing passes its apron foot, so a lead dressed down onto the covering
    still laps over the cheek instead of meeting it)."""
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
    prof = []
    for i in range(n):
        tp, bt = float(top[i]), float(bot[i])
        prof.append([(-tuck, tp), (d_out, tp), (d_out, bt), (-tuck, bt), (-tuck, bt + t), (d_out - t, bt + t),
                     (d_out - t, tp - t), (-tuck, tp - t)])
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
    return len(pr), tuple(np.round(Vf[Tf[pr[0, 0]]].mean(0), 2))


def flashing_lift(g, roof_name, body_name, ob, bins=360, out=0.01, above=0.4):
    """KIT HELPER (round 6): the drip-edge lift of a flashing over the covering it laps.  Per `bins` sectors round
    the body: the flashing's outermost vertex, then `out` m further out along the radial, a ray straight down onto
    the tier's covering (every non-flashing mesh of the tier).  Returns (sector angles in deg, vertex points, lift
    in m; NaN where the ray finds no covering)."""
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
    for q, i in enumerate(idx):
        P = Vf[i]
        o = P[:2] + out * np.array([math.cos(th[i]), math.sin(th[i])])
        h = bvh.ray_cast(Vector((float(o[0]), float(o[1]), float(P[2]) + above)), down, above + 1.0)
        if h[0] is not None:
            lift[q] = float(P[2]) - float(h[0][2])
    return np.degrees(th[idx]), Vf[idx], lift


def flashing_clip_check(g, roof_name, ob, fail=True, skip=("_flashing",), body_name=None, max_lift=None, foot=None,
                        self_check=True, others=True):
    """KIT CHECK: see the module doc.  Returns {object name: intersecting triangle pairs}.  Round 6 (all optional):
    self_check -- the flashing against ITSELF (non-adjacent pairs, `self_intersections`; note 1, closed solid
    pieces); others -- against the tier's other flashing pieces (eave cheeks, other aprons); body_name + max_lift --
    the drip-edge lift test (`flashing_lift`): any sector whose drip edge stands more than max_lift over the covering
    fails, named by its angle round the body and its world point; foot=dict(lift, ok, ths, max, point) -- the same
    for the upstand foot over the local roof line, per station."""
    from .seal_probe import _bvh
    if ob is None:
        return {}
    Vf, Tf, _ = _world_tris([ob])
    bf = _bvh(Vf, Tf)
    out = {}
    worst = None
    pool = list(_tier_meshes(g, roof_name, skip=skip))
    if others:
        pool += [o for o in _tier_meshes(g, roof_name, skip=()) if "_flashing" in o.name and o.name != ob.name]
    for o in pool:
        V, T, _ = _world_tris([o])
        pairs = bf.overlap(_bvh(V, T))
        if pairs:
            out[o.name] = len(pairs)
            if worst is None:
                a = pairs[0][0]
                worst = (o.name, tuple(np.round(Vf[Tf[a]].mean(0), 2)))
    msgs = []
    if self_check:
        n_self, p_self = self_intersections(ob)
        if n_self:
            out[ob.name + " (self)"] = n_self
            msgs.append(f"{n_self} self-intersecting triangle pairs, first at {p_self}")
            if worst is None:
                worst = (ob.name + " (self)", p_self)
    rep = "0 intersecting triangle pairs with the tier" + (" or itself" if self_check else "")
    if body_name is not None and max_lift is not None:
        ang, pts, lift = flashing_lift(g, roof_name, body_name, ob)
        fin = np.isfinite(lift)
        if fin.any():
            lf = lift[fin]
            rep += (f"; drip-edge lift over the covering median {np.median(lf):.3f}, p90 {np.percentile(lf, 90):.3f}, "
                    f"max {lf.max():.3f} m ({int(fin.sum())} sectors)")
            bad = np.flatnonzero(fin & (lift > max_lift))
            if len(bad):
                j = bad[np.argmax(lift[bad])]
                out[ob.name + " (lift)"] = len(bad)
                msgs.append(f"{len(bad)} sectors with the drip edge more than {max_lift:.2f} m over the covering, worst "
                            f"{lift[j]:.3f} m at {ang[j]:.0f} deg round {body_name} {tuple(np.round(pts[j], 2))}")
    if foot is not None:
        fl = np.where(foot["ok"], foot["lift"], -np.inf)
        rep += f"; upstand foot max {fl.max():.3f} m over the local roof line"
        bad = np.flatnonzero(fl > foot["max"])
        if len(bad):
            j = bad[np.argmax(fl[bad])]
            out[ob.name + " (foot)"] = len(bad)
            msgs.append(f"{len(bad)} stations with the upstand foot more than {foot['max']:.2f} m over the roof line, "
                        f"worst {fl[j]:.3f} m at {math.degrees(foot['ths'][j]):.0f} deg "
                        f"{tuple(np.round(foot['point'][j], 2))}")
    pair_out = {k: v for k, v in out.items() if not k.endswith(("(self)", "(lift)", "(foot)"))}
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
