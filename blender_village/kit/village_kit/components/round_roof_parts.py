"""components.round_roof_parts -- public closure parts for ANY round cone roof frame (kit changes v2_tiered_hall
round 3; new module, nothing existing changed).

These two parts were private helpers of components.tower_roof (`_roof_deck`, `_eave_closure`, v1_stone_watchtower).
tier_roof.round_tier imported them across builders, so a change to v1's private helper could silently change any
building with a round tier.  They are promoted here as documented, stable kit components; the bodies are the
tower_roof versions as of 2026-10-16 19:55:57 (byte-for-byte the same geometry).  tower_roof keeps its own private
copies untouched (another builder's module); it can alias these later (`_roof_deck = roof_deck`).

Both take a RoundFrame `f` (components.frame.RoundFrame, as built by tower_roof.roof_frame or round_tier) whose
profile (PS / PR / PZ / PA), PITCH, R_WALL, S_END, BATTEN_T, PLATE_TOP, prefix and coll are set, and build ONE mesh
object into f.coll through f.acc (so Mask, palette and hygiene follow the frame).  Frame axes: azimuth from -Y toward
+X, Z up, metres, centred on the frame origin (callers move the object onto their body centre).

    roof_deck(f, r_in, gap=0.006, eave_s=0.10, t=0.012)            -> <prefix>_roof_deck   (M_timber_weathered)
        continuous sarking deck under the battens and shingles: one outward sheet from `eave_s` slope metres above
        the lip to the apex course (S_END - 0.04), plus a closed `t`-thick board slab over the eave overhang (soffit
        face down to slope r_in + 0.03, edge face at the eave).  Producer note 6 backing: culled shingle backs and
        joints show this surface, never sky.
          r_in   plan radius of the wall line (the slab's soffit runs in to r_in + 3 cm of slope)
          gap    clearance between the deck and the batten underside (m)
          eave_s slope distance of the deck edge above the eave lip (m)
          t      slab thickness over the overhang (m)

    eave_closure(f, r_b, mat="M_mortar", n_az=240)                  -> <prefix>_eave_closure (mat)
        the wall head between the rafter feet: a band at plan radius r_b from 3 cm inside the plate top up into the
        shingle stack (its top lowered wherever a slipped / missing shingle would expose it, ray-tested against
        <prefix>_roof_shingles / _roof_starter, so build the shingles FIRST), all the way round, facing OUT.
          r_b    plan radius of the band (normally f.R_WALL - 0.075)
          mat    palette slot (M_mortar on stone heads, M_timber_weathered on board belts)
          n_az   azimuth stations
"""
import math

import numpy as np


def roof_deck(f, r_in, gap=0.006, eave_s=0.10, t=0.012):
    """KIT COMPONENT: continuous sarking deck + overhang slab of round roof frame f (see the module doc)."""
    from .cone import az2th, s_at_r, surf_frame
    from ..core import grid_quads
    acc = f.acc("roof_deck", 30, cull=None)
    az = np.linspace(0, 2 * np.pi, 145)
    th = az2th(az)
    s_in = s_at_r(f, r_in)

    def sheet(s0, s1, ns, depth, up=True):
        ss = np.linspace(s0, s1, ns)
        TH, SS = np.meshgrid(th, ss, indexing="ij")
        P, ts, tt, n = surf_frame(f, TH.ravel(), SS.ravel())
        P = P - n * depth
        F = grid_quads(len(th), len(ss))
        q = P[F[0]]
        if (float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), n[F[0][0]])) < 0) == up:
            F = F[:, ::-1]
        acc.add(P, F, "M_timber_weathered")
        return P.reshape(len(th), len(ss), 3)

    d0 = f.BATTEN_T + gap
    sheet(eave_s, f.S_END - 0.04, 22, d0, up=True)                     # the deck (top face), lip to apex
    sheet(eave_s, s_in + 0.03, 5, d0 + t, up=False)                    # the soffit face over the overhang
    P0, ts, tt, n = surf_frame(f, th, np.full_like(th, eave_s))        # the slab edge at the eave, facing out
    E = np.stack([P0 - n * d0, P0 - n * (d0 + t)], 1)                  # (n_th, 2, 3)
    F = grid_quads(len(th), 2)
    q = E.reshape(-1, 3)[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), -ts[0])) < 0:
        F = F[:, ::-1]
    acc.add(E.reshape(-1, 3), F, "M_timber_weathered")
    acc.build(f.coll)


def eave_closure(f, r_b, mat="M_mortar", n_az=240):
    """KIT COMPONENT: outward-facing eave closure band between the rafter feet of round roof frame f (see the
    module doc).  Build the shingles before calling it."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from ..core import grid_quads, n2
    from .cone import az2th, surf
    acc = f.acc("eave_closure", 30, cull=None)
    az = np.linspace(0.0, 2 * math.pi, n_az, endpoint=False)
    ss = np.linspace(0.0, 2.5, 500)
    bv = []
    for nm in (f"{f.prefix}_roof_shingles", f"{f.prefix}_roof_starter"):
        if nm in bpy.data.objects:
            me = bpy.data.objects[nm].data
            bv.append(BVHTree.FromPolygons([v.co[:] for v in me.vertices], [p_.vertices[:] for p_ in me.polygons]))
    top = np.zeros(n_az)
    cs_p, sn_p = math.cos(f.PITCH), math.sin(f.PITCH)
    for i, a in enumerate(az):
        P = surf(f, np.full_like(ss, float(az2th(a))), ss)
        rr = np.hypot(P[:, 0], P[:, 1])
        z_s = float(np.interp(-r_b, -rr, P[:, 2]))
        nrm_ = Vector((math.sin(a) * sn_p, -math.cos(a) * sn_p, cs_p))
        for dz in (0.05, 0.03, 0.012, -0.006):
            o = Vector((math.sin(a) * r_b, -math.cos(a) * r_b, z_s + dz)) + nrm_ * 0.002
            if any(b_.ray_cast(o, nrm_, 0.4)[0] is not None for b_ in bv):
                break
        top[i] = z_s + dz
    bot = np.full(n_az, f.PLATE_TOP - 0.03)
    rng = np.random.RandomState(2611)
    zz = np.stack([bot, (bot + top) / 2 + 0.008 * rng.uniform(-1, 1, n_az), top], 1)
    rad = r_b + np.stack([np.zeros(n_az), 0.006 * n2(az * 6.0, np.full(n_az, 0.3), 2612), np.zeros(n_az)], 1)
    P = np.stack([np.sin(az)[:, None] * rad, -np.cos(az)[:, None] * rad, zz], -1).reshape(-1, 3)
    F = grid_quads(n_az, 3, closed_u=True)
    q = P[F[0]]
    if float(np.dot(np.cross(q[1] - q[0], q[3] - q[0]), [math.sin(az[0]), -math.cos(az[0]), 0])) < 0:
        F = F[:, ::-1]                       # normals face OUT (seen from below the eave)
    acc.add(P, F, mat)
    acc.build(f.coll)
