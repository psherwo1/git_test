"""components.eave -- THE eave closure of a round wall head under a cone roof (kit 1.8.0 consolidation).

Before kit 1.8.0 the kit had three eave closures:
    conical_roof.build_eave_closure      the hut's daub band (door gap, closed 3 cm band since kit 1.7 / v4 r2)
    round_roof_parts.eave_closure        the outward ring of tower / tier roofs (= tower_roof._eave_closure)
    roof_junction.round_eave_fill        the masonry fill of a stone round body (reference surface, no ray test)
They are now ONE public function with three kinds.  The first two were one algorithm with different constants and
share one implementation here (_ray_band); the fill solves its top from the cone's reference surface instead of
ray-testing the built shingles, so it stays a separate implementation (_fill_band) behind the same entry point.
Every old name is a thin wrapper that calls this module with its historic constants (hash-identical builds).

    eave_closure(g, r_b, mat="M_mortar", n_az=240, kind="ring", **kw)          KIT COMPONENT
      g      a round roof frame (components.frame.RoundFrame or a tower_roof.roof_frame sub-frame): PITCH, R_WALL,
             PLATE_TOP, prefix, coll and the cone profile (PS / PR / PZ / PA) are read
      r_b    plan radius of the band (normally g.R_WALL - 0.075; kind="fill": g.R_WALL - 0.06)
      kind   "ring"  closed ring all the way round, faces OUT (seen from below the eave), top ray-tested into the
                     <prefix>_roof_shingles / _roof_starter stack (build the shingles FIRST)      -> <P>_eave_closure
             "door"  as "ring" but open over the door sector (+-door_half rad about -Y; default the frame's
                     EAVE_CLOSURE_DOOR_HALF_DEG or 2 deg inside the door posts), the hut's band   -> <P>_eave_closure
             "fill"  masonry / daub fill whose top follows the cone's reference surface + 2 cm (no ray test), for a
                     stone round body under a cone; skip(P) drops parts inside an attached body   -> <P>_eave_fill
      Keywords (defaults per kind = the historic behaviour; see KINDS):
        thickness  >0: a CLOSED band this thick (outer face out, inner face in, top / bottom / end caps); 0 = one
                   sheet ("ring" / "fill": outward, "door": inward)
        door_half  "door" only: half-angle (rad) of the open door sector
        coll       collection to build into (default g.coll)
        z_bot, center, skip   "fill" only (roof_junction.round_eave_fill's parameters)
"""
import math

import numpy as np

KINDS = dict(
    ring=dict(closed=True, face_out=True, ss=(2.5, 500), jitter=(0.008, 2611), wobble=(0.006, 2612),
              thickness=0.0, require=False),
    door=dict(closed=False, face_out=False, ss=(2.0, 400), jitter=(0.01, 2601), wobble=(0.008, 2602),
              thickness=0.03, require=True),
)
"""the constants of the two ray-tested kinds (ss = slope range / samples of the profile, jitter = mid-row height
noise (amp, seed), wobble = mid-row radial wobble (amp, n2 seed), require = missing shingle objects raise)."""


def eave_closure(g, r_b=None, mat="M_mortar", n_az=240, kind="ring", **kw):
    """KIT COMPONENT: the one eave closure (see the module doc)."""
    if kind == "fill":
        return _fill_band(g, r_b=r_b, mat=mat, n_az=n_az, **kw)
    if kind not in KINDS:
        raise ValueError(f"eave_closure: kind={kind!r}; one of 'ring', 'door', 'fill'")
    if r_b is None:
        r_b = g.R_WALL - 0.075
    k = dict(KINDS[kind])
    coll = kw.pop("coll", None)
    thickness = kw.pop("thickness", k["thickness"])
    if kind == "door":
        door_half = kw.pop("door_half", None)
        if door_half is None and getattr(g, "EAVE_CLOSURE_DOOR_HALF_DEG", None) is not None:
            door_half = math.radians(float(g.EAVE_CLOSURE_DOOR_HALF_DEG))
        if door_half is None:
            door_half = g.WALL_POST_AZ_DOOR - math.radians(2.0)
        az = np.linspace(door_half, 2 * math.pi - door_half, n_az)
    else:
        az = np.linspace(0.0, 2 * math.pi, n_az, endpoint=False)
    if kw:
        raise TypeError(f"eave_closure(kind={kind!r}): unexpected keywords {sorted(kw)}")
    return _ray_band(g, coll if coll is not None else g.coll, r_b, az, mat, k["closed"], k["face_out"], k["ss"],
                     k["jitter"], k["wobble"], thickness, k["require"])


def _ray_band(g, coll, r_b, az, mat, closed, face_out, ss_spec, jitter, wobble, thickness, require):
    """the ray-tested band ("ring" / "door"): plate top - 3 cm up into the shingle stack, its top lowered wherever a
    slipped / missing shingle would expose it.  Bodies of conical_roof.build_eave_closure and
    round_roof_parts.eave_closure (kit 1.7.x) merged statement for statement."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from ..core import grid_quads, n2
    from .cone import az2th, surf
    n_az = len(az)
    acc = g.acc("eave_closure", 30, cull=None)
    ss = np.linspace(0.0, ss_spec[0], ss_spec[1])
    bv = []
    for nm in (f"{g.prefix}_roof_shingles", f"{g.prefix}_roof_starter"):
        if require or nm in bpy.data.objects:
            me = bpy.data.objects[nm].data
            bv.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p_.vertices[:] for p_ in me.polygons]))
    top = np.zeros(n_az)
    cs_p, sn_p = math.cos(g.PITCH), math.sin(g.PITCH)
    for i, a in enumerate(az):
        P = surf(g, np.full_like(ss, float(az2th(a))), ss)
        rr = np.hypot(P[:, 0], P[:, 1])
        z_s = float(np.interp(-r_b, -rr, P[:, 2]))
        nrm_ = Vector((math.sin(a) * sn_p, -math.cos(a) * sn_p, cs_p))
        # top edge buried in the shingle stack (seals the eave gap), lowered wherever a slipped or missing shingle
        # would leave it exposed
        for dz in (0.05, 0.03, 0.012, -0.006):
            o = Vector((math.sin(a) * r_b, -math.cos(a) * r_b, z_s + dz)) + nrm_ * 0.002
            if any(b_.ray_cast(o, nrm_, 0.4)[0] is not None for b_ in bv):
                break
        top[i] = z_s + dz
    bot = np.full(n_az, g.PLATE_TOP - 0.03)
    rng = np.random.RandomState(jitter[1])
    zz = np.stack([bot, (bot + top) / 2 + jitter[0] * rng.uniform(-1, 1, n_az), top], 1)
    rad = r_b + np.stack([np.zeros(n_az), wobble[0] * n2(az * 6.0, np.full(n_az, 0.3), wobble[1]), np.zeros(n_az)], 1)
    P = np.stack([np.sin(az)[:, None] * rad, -np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(n_az, 3, closed_u=True) if closed else grid_quads(n_az, 3)
    q = P[F[0]]
    d_ = float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0]))
    if (d_ < 0) if face_out else (d_ > 0):
        F = F[:, ::-1]                      # normals OUT (seen from below the eave) / IN (the hut, seen through the door)
    if thickness and thickness > 0:
        acc.add(*_closed_band(g, P, F, zz, rad, az, float(thickness), closed), mat)
    else:
        acc.add(P, F, mat)
    acc.build(coll)


def _closed_band(g, P, F, zz, rad, az, t_, closed):
    """kit 1.7 (v4_mixed r2, director must-fix 4): a CLOSED band t_ m thick -- the face at r_b faces OUT (seen from
    outside under the eave, between the rafter feet; art bible 8: no single-sided planes where seen), an inner face
    t_ further in faces the hut, top / bottom (/ end) caps close it.  The inner top rises with the roof pitch so it
    is buried in the shingle stack as deep as the outer top.  F is the inward-facing sheet (the "door" kind)."""
    n_az = len(az)
    zi = zz.copy()
    zi[:, 2] += t_ * math.tan(g.PITCH)
    zi[:, 1] = 0.5 * (zi[:, 0] + zi[:, 2]) + (zz[:, 1] - 0.5 * (zz[:, 0] + zz[:, 2]))
    Pi = np.stack([np.sin(az)[:, None] * (rad - t_), -np.cos(az)[:, None] * (rad - t_), zi], -1).reshape(-1, 3)
    o = n_az * 3
    Fo = F[:, ::-1]                                          # outer face: outward
    Fi = F + o                                               # inner face: inward (old orientation)
    ii = np.arange(n_az if closed else n_az - 1)
    jn = (ii + 1) % n_az
    top_ = np.stack([ii * 3 + 2, jn * 3 + 2, o + jn * 3 + 2, o + ii * 3 + 2], 1)
    bot_ = np.stack([ii * 3, o + ii * 3, o + jn * 3, jn * 3], 1)
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
    if closed:
        return PP, [Fo, Fi, top_, bot_]
    ends = []
    for i0, s_ in ((0, 1), (n_az - 1, -1)):
        for j in range(2):
            q_ = [i0 * 3 + j, i0 * 3 + j + 1, o + i0 * 3 + j + 1, o + i0 * 3 + j]
            ends.append(q_ if s_ > 0 else q_[::-1])
    e0, e1 = np.array(ends[:2]), np.array(ends[2:])
    tan0 = np.array([math.cos(az[0]), math.sin(az[0]), 0.0])      # d/daz of (sin, -cos): toward +az
    e0 = _orient(e0, lambda f: -tan0)
    tan1 = np.array([math.cos(az[-1]), math.sin(az[-1]), 0.0])
    e1 = _orient(e1, lambda f: tan1)
    return PP, [Fo, Fi, top_, bot_, e0, e1]


def _fill_band(g, r_off=0.06, z_bot=None, center=(0.0, 0.0), skip=None, mat="M_mortar", n_az=240, r_b=None):
    """the "fill" kind: roof_junction.round_eave_fill's body (kit 1.7.x v3), moved here unchanged (r_b, when given,
    replaces g.R_WALL - r_off)."""
    from ..core import grid_quads, n2
    from ..geom import Acc, finalize
    from .roof_junction import cone_ref_z
    r_b = g.R_WALL - r_off if r_b is None else r_b
    z0 = g.PLATE_TOP - 0.03 if z_bot is None else z_bot
    az = np.linspace(0, 2 * math.pi, n_az + 1)
    zt = cone_ref_z(g, center[0] + np.sin(az) * r_b, center[1] - np.cos(az) * r_b, center) + 0.02
    zz = np.stack([np.full(len(az), z0), 0.5 * (z0 + zt), zt], 1)
    rad = r_b + np.stack([np.zeros(len(az)), 0.008 * n2(az * 6.0, np.full(len(az), 0.3), 2602), np.zeros(len(az))], 1)
    P = np.stack([center[0] + np.sin(az)[:, None] * rad, center[1] - np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(len(az), 3)
    q = P[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0])) < 0:
        F = F[:, ::-1]                      # outward (seen from under the eave)
    if skip is not None:
        C = P[F].mean(1)
        F = F[~skip(C)]
    acc = Acc(f"{g.prefix}_eave_fill", 30)
    acc.add(P, F, mat)
    return finalize(acc, g.coll, smooth_deg=30.0, recalc=False)
