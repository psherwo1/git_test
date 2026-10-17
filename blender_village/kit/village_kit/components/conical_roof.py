"""components.conical_roof -- a round conical shingle roof on a round wall frame.

build_rafters          pole rafters (eave stubs in the front arc, full length where the doorway shows them), hub
build_purlins_battens  purlin ring + batten rings (only where visible: eave gap, doorway window)
build_shingles         doubled starter + N_COURSES of individually modelled shingles from the kit's shingle pool,
                       exposed part + overlap only (full length where covered parts can be seen), slipped / split /
                       missing pieces
build_roof_blocker     dark blocker cone under the rafters (no light through trimmed joints)
build_eave_closure     daub band sealing the eave gap above the plate
"""
import math
from functools import partial  # noqa: F401

import bpy
import numpy as np

from ..core import log

from ..core import chamfer_path, frame_R, grid_quads, lathe, n2, nrm, open_tube, rbox, ring_noise, tube, xf
from ..shingles import SH_VARIANTS, shingle_mesh
from .cone import az2th, rafter_center, s_at_r, sag_at, surf, surf_frame
from .frame import interior_visible


RAFT_ARC = np.radians(np.array([-115.0, -80.0, -45.0, -15.0, 15.0, 45.0, 80.0, 115.0]))


def build_rafters(g, coll, seed=404):
    """28 pole rafters.  Seen from outside only under the eave and, in the back arc, through the door:
    the front-arc rafters are modelled as eave stubs ending 16 cm inside the wall, and every rafter is
    open on its top (it faces the battens / shingle underside and is never visible)."""
    acc = g.acc("rafters", 50)
    rng = np.random.RandomState(seed)
    s_hub = s_at_r(g, 0.34)
    s_stub = s_at_r(g, g.R_WALL - 0.16)
    for j in range(g.N_RAFT):
        az = g.RAFT_AZ0 + j * 2 * math.pi / g.N_RAFT
        th = float(az2th(az))
        full = interior_visible(az)
        s_tip = rng.uniform(0.04, 0.12)
        s_end = s_hub if full else s_stub
        ss = np.concatenate([np.linspace(s_tip, s_tip + 0.3, 5), np.linspace(s_tip + 0.3, s_end, 12 if full else 4)[1:]])
        C, ts, tt, n = rafter_center(g, np.full_like(ss, th), ss)
        crook = 0.018 * n2(ss * 0.6, np.full_like(ss, j * 1.0), 405) * np.sin(np.pi * (ss - s_tip) / (s_hub - s_tip))
        C = C + tt * crook[:, None]
        r0 = rng.uniform(0.05, 0.06)
        rad = r0 * (1.0 - 0.25 * (ss - s_tip) / (s_hub - s_tip))
        down = -n[len(n) // 2]
        rr = 1 + 0.04 * n2(np.arange(len(ss))[:, None] * 0.2 + np.zeros((1, len(RAFT_ARC))), np.broadcast_to(RAFT_ARC * 2, (len(ss), len(RAFT_ARC))), j)
        split = (j % 5 == 2)
        if split:
            ks = int(np.searchsorted(ss, s_tip + 0.22))
            V, F, uv = open_tube(C[ks:], rad[ks:], RAFT_ARC, down, tuple(n[0]), rr=rr[ks:], cap0=True, cap1=not full)
            acc.add(V, F, "M_timber", uv, True)
            ang2 = np.linspace(-np.pi / 2, np.pi / 2, 8)
            for sgn in (-1, 1):
                seg = C[:ks + 1].copy()
                kk = np.linspace(1, 0, len(seg))
                seg = seg + tt[:ks + 1] * (sgn * (0.004 + 0.014 * kk ** 2))[:, None]
                dprof = np.stack([np.sin(ang2), -np.cos(ang2) * sgn], -1)
                if sgn < 0:
                    dprof = dprof[::-1]
                pth, rr_ = chamfer_path(seg[::-1], rad[:ks + 1][::-1], 0.006)
                P, F, uv, w = tube(pth, rr_, 8, up=tuple(n[0]), profile=dprof)
                acc.add(P, F, "M_timber", uv, w)
        else:
            V, F, uv = open_tube(C, rad, RAFT_ARC, down, tuple(n[0]), rr=rr, cap0=True, cap1=not full)
            # uneven, slightly skewed saw / axe cut at the tip
            m = len(RAFT_ARC)
            sk = rng.uniform(-0.035, 0.035)
            t_end = nrm(C[0] - C[1])
            proj = ((V[:m] - C[0]) @ tt[0]) / max(rad[0], 1e-3)
            V[:m] += t_end[None, :] * (sk * proj)[:, None]
            acc.add(V, F, "M_timber", uv, True)
    C, ts, tt, n = rafter_center(g, np.array([0.0]), np.array([s_hub]))
    zc = float(C[0, 2])
    prof = [(0.0, zc - 0.20), (0.36, zc - 0.20), (0.385, zc - 0.17), (0.385, zc + 0.14), (0.36, zc + 0.17), (0.0, zc + 0.17)]
    V, F, uv, w = lathe(prof, 24, rfunc=lambda t, z: 1 + 0.02 * np.sin(3 * t + 1))
    acc.add(V, F, "M_timber", uv, w)
    acc.build(coll)


def build_purlins_battens(g, coll, seed=505):
    pur = g.acc("purlin_rings", 50)
    bat = g.acc("battens", 35)
    rng = np.random.RandomState(seed)
    d = 2 * math.pi / g.N_RAFT
    # purlin rings inside (under rafters)
    for sp in (1.25,):
        az = g.RAFT_AZ0 + np.arange(g.N_RAFT + 1) * d
        th = az2th(az)
        C, ts, tt, n = rafter_center(g, th, np.full_like(th, sp))
        C = C - n * (g.RAFT_R + 0.035)
        for k in range(g.N_RAFT):
            if not (interior_visible(az[k], math.radians(55)) and interior_visible(az[k + 1], math.radians(55))):
                continue                     # only where the doorway shows them
            p0, p1 = C[k], C[k + 1]
            # extend a little past rafters (lapped / lashed)
            dd = p1 - p0
            path = np.linspace(p0 - dd * 0.06, p1 + dd * 0.06, 5)
            path[:, 2] -= 0.008 * np.sin(np.linspace(0, np.pi, 5))
            path, rr = chamfer_path(path, rng.uniform(0.032, 0.038), 0.006)
            P, F, uv, w = tube(path, rr, 8, up=tuple(n[k]))
            pur.add(P, F, "M_timber", uv, w)
    # batten rings under the shingle courses
    s_list = [0.03] + [k * g.SH_EXPOSE + 0.08 for k in range(1, g.N_COURSES + 1)]
    s_list += [g.N_COURSES * g.SH_EXPOSE + 0.30]
    for kb, sb in enumerate(s_list):
        if sb > g.S_END - 0.05:
            continue
        az = g.RAFT_AZ0 + np.arange(g.N_RAFT + 1) * d
        th = az2th(az)
        P0, ts, tt, n = surf_frame(g, th, np.full_like(th, sb))
        Cb = P0 - n * (g.BATTEN_T / 2)
        rr = float(np.hypot(Cb[0, 0], Cb[0, 1]))
        step = 2 if rr > 1.4 else 3
        k = rng.randint(step)
        starts = list(range(-k, g.N_RAFT, step))
        eave_ring = sb < 0.9                 # seen from outside in the eave gap
        for st in starts:
            a = max(st, 0)
            b = min(st + step, g.N_RAFT)
            if b <= a:
                continue
            if not eave_ring and not (sb < 2.3 and interior_visible(az[a], math.radians(75))
                                      and interior_visible(az[b], math.radians(75))):
                continue
            p0, p1 = Cb[a], Cb[b]
            # lath runs straight from rafter a to rafter b (chord); overhang 4 cm
            x = p1 - p0
            L = float(np.linalg.norm(x))
            mid = (p0 + p1) / 2
            nmid = nrm(n[a] + n[b])
            R = frame_R(x, nmid)
            hw = 0.025 if kb > 0 else 0.045
            V, F = rbox((L / 2 + 0.03, hw, g.BATTEN_T / 2), 0.004, (1, 1, 1), chamfer=False)
            V = xf(V, R, mid + R[:, 1] * rng.uniform(-0.005, 0.005))
            bat.add(V, F, "M_timber_weathered", smooth=True)
    pur.build(coll)
    bat.build(coll)


def build_roof_blocker(g, coll):
    """dark blocker surface (producer note 6): a plain cone under the rafters over the front arc, where
    the shingles are modelled only as their exposed part + overlap.  It keeps the interior seen through
    the doorway dark (no light through the trimmed joints); it is never visible from outside."""
    acc = g.acc("roof_blocker", 30, cull=None)
    az = np.linspace(0, 2 * np.pi, 97)
    th = az2th(az)
    s0, s1 = s_at_r(g, g.R_WALL + 0.06), g.S_END - 0.05
    ss = np.linspace(s0, s1, 13)
    TH, SS = np.meshgrid(th, ss, indexing="ij")
    P, ts, tt, n = surf_frame(g, TH.ravel(), SS.ravel())
    P = P - n * (g.BATTEN_T + 2 * g.RAFT_R + 0.02)
    F = grid_quads(len(th), len(ss))[:, ::-1]
    # leave open the window whose underside is seen through the doorway (full-length shingles there)
    AZ = np.broadcast_to(az[:, None], TH.shape).ravel()
    win = (np.abs(np.angle(np.exp(1j * (AZ - np.pi)))) < math.radians(g.FULL_WIN_DEG - 4)) & (P[:, 2] < g.FULL_WIN_Z - 0.25)
    F = F[~win[F].all(axis=1)]
    acc.add(P, F, "M_timber_weathered")
    acc.build(coll)


def build_eave_closure(g, coll, r_off=0.075, door_half=None, n_az=240, thickness=0.03):
    """daub eave closure (director r4 #3b): a low band on the inner half of the wall plate, from the plate
    top up to the underside of the roof deck, between the rafters.  It closes the eave gap from the
    inside, so no ray through the doorway can leave the hut between the plate and the roof (it reads
    from outside, deep in the eave shadow, as the daubed wall top between the rafter feet).
    kit 1.7 (v4_mixed r2): a closed band `thickness` m thick (outer + inner faces, top / bottom / end caps);
    thickness=0 gives the old single-sided band (normals into the hut)."""
    if door_half is None and getattr(g, "EAVE_CLOSURE_DOOR_HALF_DEG", None) is not None:
        # kit 1.7 r4 (v4_mixed, director r3 probe): optional frame attribute -- the closure runs on over the door
        # sector behind the door frame's infill, leaving only +-this many degrees open on the door axis.  On a small
        # plan the cheek opening between the infill end and the wall post (above the return beam) otherwise looks
        # straight into the eave void (the back of the roof blocker) from an oblique eye-level view.
        door_half = math.radians(float(g.EAVE_CLOSURE_DOOR_HALF_DEG))
    if door_half is None:                  # 2 deg inside the door-flanking wall posts
        door_half = g.WALL_POST_AZ_DOOR - math.radians(2.0)
    acc = g.acc("eave_closure", 30, cull=None)
    r_b = g.R_WALL - r_off
    az = np.linspace(door_half, 2 * math.pi - door_half, n_az)
    ss = np.linspace(0.0, 2.0, 400)
    top = np.zeros(n_az)
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bv = []
    for nm in (f"{g.prefix}_roof_shingles", f"{g.prefix}_roof_starter"):   # kit 1.7 (v4_mixed): was "HUT_" only
        me = bpy.data.objects[nm].data
        bv.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p_.vertices[:] for p_ in me.polygons]))
    cs_p, sn_p = math.cos(g.PITCH), math.sin(g.PITCH)
    for i, a in enumerate(az):
        P = surf(g, np.full_like(ss, float(az2th(a))), ss)
        rr = np.hypot(P[:, 0], P[:, 1])
        z_s = float(np.interp(-r_b, -rr, P[:, 2]))
        nrm_ = Vector((math.sin(a) * sn_p, -math.cos(a) * sn_p, cs_p))
        # top edge buried in the shingle stack (seals the eave gap), lowered wherever a slipped or
        # missing shingle would leave it exposed
        for dz in (0.05, 0.03, 0.012, -0.006):
            o = Vector((math.sin(a) * r_b, -math.cos(a) * r_b, z_s + dz)) + nrm_ * 0.002
            if any(b_.ray_cast(o, nrm_, 0.4)[0] is not None for b_ in bv):
                break
        top[i] = z_s + dz
    bot = np.full(n_az, g.PLATE_TOP - 0.03)
    rng = np.random.RandomState(2601)
    zz = np.stack([bot, (bot + top) / 2 + 0.01 * rng.uniform(-1, 1, n_az), top], 1)
    rad = r_b + np.stack([np.zeros(n_az), 0.008 * n2(az * 6.0, np.full(n_az, 0.3), 2602), np.zeros(n_az)], 1)
    P = np.stack([np.sin(az)[:, None] * rad, -np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(n_az, 3)
    q = P[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0])) > 0:
        F = F[:, ::-1]                      # normals face the hut interior (seen through the door)
    if thickness and thickness > 0:
        # kit 1.7 (v4_mixed r2, director must-fix 4): a CLOSED band `thickness` m thick -- the face at r_b now faces
        # OUT (it is seen from outside under the eave, between the rafter feet; art bible 8: no single-sided planes
        # where seen), an inner face `thickness` further in faces the hut, top / bottom / end caps close it.  The
        # inner top rises with the roof pitch so it is buried in the shingle stack as deep as the outer top.
        t_ = float(thickness)
        zi = zz.copy()
        zi[:, 2] += t_ * math.tan(g.PITCH)
        zi[:, 1] = 0.5 * (zi[:, 0] + zi[:, 2]) + (zz[:, 1] - 0.5 * (zz[:, 0] + zz[:, 2]))
        Pi = np.stack([np.sin(az)[:, None] * (rad - t_), -np.cos(az)[:, None] * (rad - t_), zi], -1).reshape(-1, 3)
        o = n_az * 3
        Fo = F[:, ::-1]                                          # outer face: outward
        Fi = F + o                                               # inner face: inward (old orientation)
        ii = np.arange(n_az - 1)
        top_ = np.stack([ii * 3 + 2, (ii + 1) * 3 + 2, o + (ii + 1) * 3 + 2, o + ii * 3 + 2], 1)
        bot_ = np.stack([ii * 3, o + ii * 3, o + (ii + 1) * 3, (ii + 1) * 3], 1)
        ends = []
        for i0, s_ in ((0, 1), (n_az - 1, -1)):
            for j in range(2):
                q_ = [i0 * 3 + j, i0 * 3 + j + 1, o + i0 * 3 + j + 1, o + i0 * 3 + j]
                ends.append(q_ if s_ > 0 else q_[::-1])
        PP = np.concatenate([P, Pi])

        def _orient(Fq, want):
            q_ = PP[Fq[0]]
            nn = np.cross(q_[1] - q_[0], q_[3] - q_[0])
            return Fq if float(np.dot(nn, want(Fq[0]))) >= 0 else Fq[:, ::-1]
        cen = lambda f: PP[f].mean(0)                            # noqa: E731
        Fo = _orient(Fo, lambda f: np.array([cen(f)[0], cen(f)[1], 0.0]))
        Fi = _orient(Fi, lambda f: -np.array([cen(f)[0], cen(f)[1], 0.0]))
        top_ = _orient(top_, lambda f: np.array([0.0, 0.0, 1.0]))
        bot_ = _orient(bot_, lambda f: np.array([0.0, 0.0, -1.0]))
        e0, e1 = np.array(ends[:2]), np.array(ends[2:])
        tan0 = np.array([math.cos(az[0]), math.sin(az[0]), 0.0])      # d/daz of (sin, -cos): toward +az
        e0 = _orient(e0, lambda f: -tan0)
        tan1 = np.array([math.cos(az[-1]), math.sin(az[-1]), 0.0])
        e1 = _orient(e1, lambda f: tan1)
        acc.add(PP, [Fo, Fi, top_, bot_, e0, e1], "M_daub")
    else:
        acc.add(P, F, "M_daub")
    acc.build(coll)


def build_shingles(g, coll, seed=606):
    """17 courses + doubled starter.  Each shingle is modelled as its exposed part plus ~6.5 cm of
    covered overlap (producer note 6); shingles keep their full 0.72 m length where their covered part
    can be seen: under a missing shingle of the course above, under a slipped one, and in the back arc
    whose underside shows through the doorway."""
    acc = g.acc("roof_shingles", 45)
    st_acc = g.acc("roof_starter", 45)
    rng = np.random.RandomState(seed)
    B_WEDGE = 0.066
    OV = 0.065
    # kit 1.3.0 (opt-in cone_age keys, components.cone.AGE_R9; director r8 #2)
    age = getattr(g, "cone_age", None) or {}
    rigid = bool(age.get("rigid_sag")) and bool(age.get("sag"))
    tilt_max = math.radians(age.get("rigid_tilt_deg", 1.5))
    ul_hw = float(age.get("underlap", 0.0)) if rigid else 0.0
    max_joint = age.get("max_joint")
    pieces = {}                      # course -> [(theta_c, half-angle, depth at left edge, depth at right edge, s_b)]

    ring_step = getattr(g, "SH_RING_STEP", None)

    def place(acc_, th_c, s_b, W, L, var, phi, lift, curl, base_fn, ys=None, closed=True, wear_=None, course=None):
        if ys is None and ring_step:
            # kit 1.7 r4 (v4_mixed, producer note 15): optional frame attribute SH_RING_STEP -- the shingle's
            # cross-section rings above the butt every SH_RING_STEP m instead of 0.07 m (the butt rings, which carry
            # the rounded butt and the curl, are kept); absent = unchanged
            ys = np.array([0.0, 0.006, 0.018, 0.04, 0.075, 0.13] + list(np.arange(0.2, L - 0.03, float(ring_step)))
                          + [L])
        Pl, F, uv = shingle_mesh(W, L, var, curl=curl, ys=ys, bottom=closed, head=closed)
        x, y, z = Pl[:, 0], Pl[:, 1], Pl[:, 2]
        c, s_ = math.cos(phi), math.sin(phi)
        xr = x * c - y * s_
        yr = x * s_ + y * c
        v = np.clip(y / 0.72, 0, 1)
        ss = s_b + yr
        th = np.full_like(ss, th_c)
        P0, ts, tt, n = surf_frame(g, th, ss, sag=not rigid)
        rb = float(np.hypot(*surf(g, th_c, s_b, sag=not rigid)[:2]))
        rcur = np.hypot(P0[:, 0], P0[:, 1])
        xr = xr * np.clip(rcur / rb, 0.3, 1.0)
        off = base_fn(v) + z + lift * (1 - v)
        if rigid:
            # the sag as a RIGID per-shingle offset (no shear, joint widths kept): evaluated at the centre of the
            # exposed part, translated along the cone normal, tilted about the shingle axis by <= tilt_max
            s_c = s_b + 0.5 * min(L, g.SH_EXPOSE)
            dth = 0.5 * W / max(rb, 0.2)
            sg_c, sg_l, sg_r = (float(sag_at(g, t_, s_c)) for t_ in (th_c, th_c - dth, th_c + dth))
            tilt = float(np.clip(math.atan2(sg_r - sg_l, max(W, 0.05)), -tilt_max, tilt_max))
            off = off - (sg_c + math.tan(tilt) * xr)
            if course is not None:
                pieces.setdefault(course, []).append((th_c, dth, sg_c - math.tan(tilt) * 0.5 * W,
                                                      sg_c + math.tan(tilt) * 0.5 * W, s_b))
        V = P0 + tt * xr[:, None] + n * off[:, None]
        acc_.add(V, F, "M_roof_shingle", uv, smooth=True, wear=wear_)

    def underlap(acc_, k, th_j, depth, s_b, wedge=B_WEDGE):
        """a strip of covered shingle under one side joint of course k (stand-in for the hidden upper part of the
        course below): 2 * ul_hw wide, from just above the butt line to under the next course, its top 4 mm under
        the deeper of the two neighbours' undersides; top face + butt end only (never seen edge-on)."""
        s_hi = min(s_b + g.SH_EXPOSE + 0.04, g.S_END)
        if s_hi - s_b < 0.08:
            return 0
        ys_ = np.array([s_b + 0.015, s_b + 0.5 * (g.SH_EXPOSE + 0.055), s_hi])
        xs_ = np.array([-ul_hw, 0.0, ul_hw])
        rb_ = float(np.hypot(*surf(g, th_j, s_b, sag=False)[:2]))
        Pt = []
        for yy in ys_:
            P0, ts, tt, n = surf_frame(g, np.full(3, th_j), np.full(3, yy), sag=False)
            rcur = np.hypot(P0[:, 0], P0[:, 1])
            xx = xs_ * np.clip(rcur / rb_, 0.3, 1.0)
            vv = (yy - s_b) / 0.72
            top = wedge * (1 - vv) - 0.004 - depth
            Pt.append(np.stack([P0 + tt * xx[:, None] + n * top, P0 + tt * xx[:, None] + n * (top - 0.012)], 0))
        Pt = np.array(Pt)                               # (row, layer, col, 3)
        V = np.concatenate([Pt[:, 0].reshape(-1, 3), Pt[0, 1]])           # top grid 3x3 + butt bottom edge
        F = [[r * 3 + c_, r * 3 + c_ + 1, (r + 1) * 3 + c_ + 1, (r + 1) * 3 + c_] for r in range(2) for c_ in range(2)]
        F += [[9 + c_, 9 + c_ + 1, c_ + 1, c_] for c_ in range(2)]     # butt end face
        F = np.array(F)
        q = V[F[0]]
        nn = np.cross(q[1] - q[0], q[3] - q[0])
        out = V[4] - Pt[1, 1, 1]                        # from the bottom layer toward the top: outward
        if float(np.dot(nn, out)) < 0:
            F = F[:, ::-1]
        acc_.add(V, F, "M_roof_shingle", None, smooth=False, wear=0.5)
        return 1

    # ---- doubled starter course (underside seen from below at the eave)
    s_b = 0.012
    rb = float(np.hypot(*surf(g, 0.0, s_b)[:2]))
    circ = 2 * math.pi * rb
    n = int(round(circ / 0.44))
    w = rng.uniform(0.75, 1.25, n)
    gaps = rng.uniform(0.005, 0.012, n)
    w = w / w.sum() * (circ - gaps.sum())
    off0 = rng.uniform(0, 2 * math.pi)
    acc_ang = off0
    for i in range(n):
        dth = (w[i] + gaps[i]) / rb
        thc = acc_ang + dth / 2
        acc_ang += dth
        var = dict(SH_VARIANTS[rng.randint(16)])
        var["Tb"] = 0.034
        var["cup"] = 0.002
        place(st_acc, thc, s_b, w[i], 0.46, var, math.radians(rng.uniform(-1.5, 1.5)), 0.0, 0.0,
              lambda v: 0.0 * v, ys=[0.0, 0.006, 0.018, 0.04, 0.12, 0.46])
    prev_joints = np.mod(off0 + np.cumsum((w + gaps) / rb), 2 * math.pi)

    # ---- pass 1: lay out every course (positions, widths, damage)
    courses = []
    for k in range(g.N_COURSES):
        s_b = k * g.SH_EXPOSE
        cwave = 0.018 * ring_noise(np.linspace(0, 2 * np.pi, 512, endpoint=False), 700 + k, 5, 1.0)
        rb = float(np.hypot(*surf(g, 0.0, s_b)[:2]))
        rmid = float(np.hypot(*surf(g, 0.0, s_b + g.SH_EXPOSE * 0.5)[:2]))
        circ = 2 * math.pi * rb
        target = 0.44 if k < g.N_COURSES - 3 else 0.40
        n = max(8, int(round(2 * math.pi * rmid / target)))
        w = rng.uniform(0.76, 1.24, n)
        gaps = rng.uniform(0.006, 0.016, n)
        if max_joint:                       # kit 1.3.0: side-joint gaps capped (director r8 #2)
            gaps = np.minimum(gaps, float(max_joint))
        w = w / w.sum() * (circ - gaps.sum())
        best, best_d = 0.0, -1
        for _ in range(12):
            o = rng.uniform(0, 2 * math.pi)
            j = np.mod(o + np.cumsum((w + gaps) / rb), 2 * math.pi)
            dmin = np.min(np.abs(np.angle(np.exp(1j * (j[:, None] - prev_joints[None, :])))), axis=1) * rb
            sc = np.min(dmin)
            if sc > best_d:
                best_d, best = sc, o
        acc_ang = best
        recs = []
        for i in range(n):
            dth = (w[i] + gaps[i]) / rb
            thc = acc_ang + dth / 2
            acc_ang += dth
            ri = rng.rand()
            rec = dict(k=k, thc=thc, half=w[i] / 2 / rb, W=w[i], ri=ri,
                       sb=s_b + cwave[int((thc % (2 * np.pi)) / (2 * np.pi) * 512) % 512] + rng.uniform(-0.012, 0.012),
                       lift=rng.uniform(0.0, 0.015), phi=math.radians(rng.uniform(-4.5, 4.5)),
                       var=rng.randint(16), slip=0.0, missing=False, full=False)
            if k > 0 and k < g.N_COURSES - 1 and ri < 0.012:
                rec["missing"] = True
            elif k > 0 and 0.012 < ri < 0.03:
                rec["slip"] = rng.uniform(0.05, 0.11)
                rec["lift"] += 0.016
                rec["phi"] += math.radians(rng.uniform(-4, 4))
            recs.append(rec)
        courses.append(recs)
        prev_joints = np.mod(best + np.cumsum((w + gaps) / rb), 2 * math.pi)
    # ---- pass 2: which covered parts can be seen -> full length there
    for k in range(g.N_COURSES - 1):
        holes = [(r["thc"], r["half"] + 0.02) for r in courses[k + 1] if r["missing"]]
        for r in courses[k]:
            for (tc, hh) in holes:
                if abs(float(np.angle(np.exp(1j * (r["thc"] - tc))))) < r["half"] + hh:
                    r["full"] = True
    n_total = n_full = 0
    for k, recs in enumerate(courses):
        s_b = k * g.SH_EXPOSE
        base_fn = (lambda v: 0.037 * (1 - v)) if k == 0 else (lambda v: B_WEDGE * (1 - v))
        for r in recs:
            if r["missing"]:
                continue
            az = float(r["thc"]) + math.pi / 2
            zb = float(surf(g, r["thc"], r["sb"])[2])
            if interior_visible(az, math.radians(g.FULL_WIN_DEG)) and zb < g.FULL_WIN_Z:
                r["full"] = True
            L_full = min(g.SH_LEN, g.S_END - s_b + 0.02)
            L = L_full if r["full"] else min(g.SH_EXPOSE + OV + r["slip"], L_full)
            var = SH_VARIANTS[r["var"]]
            curl = var["curl_eave"] if k < 2 else var["curl"]
            sb = r["sb"] - r["slip"]
            thc, Wi, phi, lift = r["thc"], r["W"], r["phi"], r["lift"]
            rb = float(np.hypot(*surf(g, 0.0, s_b)[:2]))
            dd_door = abs(float(np.angle(np.exp(1j * (thc + np.pi / 2)))))
            door_eave = (k < 4) and dd_door < 1.0 and (0.03 < r["ri"] < 0.13)
            n_full += r["full"]
            # underside (lies on the course below) and head end (under the course above) are only
            # modelled where they can be seen: eave courses, full-length shingles, slipped ones
            closed = k < 2 or r["full"] or r["slip"] > 0
            if (0.03 < r["ri"] < 0.045 or door_eave) and Wi > 0.34:      # split into two pieces
                gap_ = 0.012
                wa = Wi * rng.uniform(0.4, 0.6)
                wb = Wi - wa - gap_
                tha = thc - (Wi / 2 - wa / 2) / rb
                thb = thc + (Wi / 2 - wb / 2) / rb
                place(acc, tha, sb, wa, L, var, phi - 0.02, lift, curl, base_fn, closed=closed, wear_=0.85, course=k)
                place(acc, thb, sb + 0.01, wb, L - 0.01, var, phi + 0.025, lift + 0.004, curl, base_fn, closed=closed,
                      wear_=0.9, course=k)
                n_total += 2
                continue
            wr = 0.9 if r["slip"] > 0 else (0.55 + 0.2 * (k < 2) if k < 4 else None)
            place(acc, thc, sb, Wi, L, var, phi, lift, curl, base_fn, closed=closed, wear_=wr, course=k)
            n_total += 1
    log("shingles:", n_total, "full-length (covered part visible):", n_full)
    g.SHINGLE_TOP["V"] = np.concatenate(acc.V + st_acc.V)
    acc.build(coll)
    st_acc.build(coll)
    if ul_hw > 0.0:
        # kit 1.3.0 (director r8 #2): >= 8 cm of under-lap beside every side joint (courses >= 1), a separate
        # object outside round_hidden_cull's targets so it is never culled
        ul_acc = g.acc("roof_underlap", 45)
        n_ul = 0
        k_first = 0 if age.get("underlap_k0") else 1        # kit 1.5.0: course 1 over the starter too (opt-in)
        for k in sorted(pieces):
            if k < k_first:
                continue
            pc = sorted(pieces[k], key=lambda p_: p_[0] % (2 * math.pi))
            rb = float(np.hypot(*surf(g, 0.0, k * g.SH_EXPOSE, sag=False)[:2]))
            for i in range(len(pc)):
                a_, b_ = pc[i], pc[(i + 1) % len(pc)]
                ea = a_[0] + a_[1]
                eb = b_[0] - b_[1]
                gap = float(np.angle(np.exp(1j * (eb - ea))))
                if gap * rb > 0.05 or gap * rb < -0.10:      # a missing shingle / not neighbours: no joint
                    continue
                th_j = ea + 0.5 * gap
                n_ul += underlap(ul_acc, k, th_j, max(a_[3], b_[2]) + 0.002, max(a_[4], b_[4]),
                                 wedge=0.037 if k == 0 else B_WEDGE)
        log("underlap strips:", n_ul)
        if n_ul:
            ul_acc.build(coll)


def conical_roof(g, seed=606, structure_seeds=(404, 505)):
    """KIT COMPONENT: the conical shingle roof of a round frame -- eave radius g.R_EAVE (wall radius + overhang),
    pitch g.PITCH with the bell-cast eave kick, convexity, eave wave and the optional cone age pass
    (g.cone_age, see components.cone), on g.N_RAFT pole rafters: rafters + hub, purlin / batten rings, starter +
    g.N_COURSES chunky shingle courses (village_kit.shingles SIZE_TABLE), dark blocker, eave closure.
    Needs the wall plate height (g.PLATE_TOP, from the frame)."""
    build_rafters(g, g.coll, seed=structure_seeds[0])
    build_purlins_battens(g, g.coll, seed=structure_seeds[1])
    build_shingles(g, g.coll, seed=seed)
    build_roof_blocker(g, g.coll)
    build_eave_closure(g, g.coll)
