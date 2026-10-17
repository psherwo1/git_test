"""components.ball_finial -- the stone ball finial of a stone-roofed / stone round end (art bible 1.5: "stone ball
finials appear only on stone-roofed round ends (ref1 longhouse)") (kit, variant v3_longhouse_roundend).

ball_finial(g, ...)   KIT COMPONENT on any round frame cone (components.frame.RoundFrame): a lead hat fitted over the
                      top shingles (components.finial.lead_hat, cover = g.SHINGLE_TOP), a dressed-stone socket drum,
                      a necked collar and a slightly flattened stone ball -> <P>_cap_collar (M_lead),
                      <P>_finial (M_stone_dressed).  Must run after the shingles.
"""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize, lathe_rz
from .finial import lead_hat


def cone_apex_z(g):
    """the cone reference surface extrapolated to the axis."""
    return float(g.PZ[-1] + g.PR[-1] * math.tan(g.PA[-1]))


def apex_blocker(g, r_out, center=(0.0, 0.0), below=0.04, depth=0.14, seg=40, name="apex_blocker"):
    """KIT COMPONENT (round 2): a closed plug under a cone's apex hat -- its top follows the cone's reference
    surface `below` m down (under the top shingles) from the axis out to r_out, `depth` m thick -- so no ray that
    slips under the hat's drip and between the top shingles reaches the sky.  -> <P>_apex_blocker (BACKING)."""
    rr = np.linspace(0.0, r_out, 9)
    PR, PZ = np.asarray(g.PR, float), np.asarray(g.PZ, float)
    z_ax = cone_apex_z(g)
    zt = np.where(rr < PR[-1], z_ax - rr * math.tan(g.PA[-1]), np.interp(-rr, -PR, PZ)) - below
    # axis bottom -> rim bottom -> rim top -> along the top back to the axis (closed solid of revolution)
    prof = [(0.0, float(zt[-1] - depth)), (float(r_out), float(zt[-1] - depth))] + \
        [(float(r_), float(z_)) for r_, z_ in zip(rr[::-1], zt[::-1])]
    V, F = lathe_rz(prof, seg, cx=center[0], cy=center[1], z0=0.0, cap_bottom=False, cap_top=False)
    acc = Acc(f"{g.prefix}_{name}", 40)
    acc.add(V, F, "M_timber_weathered", wear=0.3)
    return finalize(acc, g.coll, smooth_deg=40.0, recalc=True)


def fine_hat(acc, cx, cy, z_apex, r0, h0, seg=96, cover=None, clear=0.02, step=0.025):
    """KIT HELPER (round 3): finial.lead_hat's fitted hat (same fit: drip lifted until every covering vertex is
    `clear` under the lead), re-lathed from a smoothed, finely subdivided profile: the 2-segment slope of
    lead_hat becomes one smooth curve (quadratic through its mid ring, never under lead_hat's own surface) in
    `step` m rings, so the smooth-shaded lead follows its true surface (no shading creases on the slope)."""
    from ..core import Acc as CoreAcc
    tmp = CoreAcc("_tmp_hat", 50.0)
    z_top = lead_hat(tmp, cx, cy, z_apex, r0, h0, seg=8, cover=cover, clear=clear)
    V0 = np.concatenate([np.asarray(v_, float) for v_ in tmp.V])
    mer = V0[(np.abs(V0[:, 1] - cy) < 1e-7) & (V0[:, 0] >= cx - 1e-9)]      # one meridian, profile order
    prof = [(float(p[0] - cx), float(p[2] - z_apex)) for p in mer]
    # profile: drip (3 pts), r0, mid ring, (0.09), (0.085), axis -> smooth r0 .. 0.09 through the mid ring
    i0 = 2
    i1 = next(i for i, p in enumerate(prof) if abs(p[0] - 0.09) < 1e-6)
    A, M, B = np.array(prof[i0]), np.array(prof[i0 + 1]), np.array(prof[i1])
    C = 2 * M - 0.5 * (A + B)                            # quadratic Bezier control through M at t = 0.5
    n = max(4, int(np.linalg.norm(B - A) / step))
    t = np.linspace(0, 1, n + 1)[:, None]
    Q = (1 - t) ** 2 * A + 2 * (1 - t) * t * C + t ** 2 * B
    fine = prof[:i0] + [tuple(q) for q in Q] + prof[i1 + 1:]
    V, F = lathe_rz(fine, seg, cx=cx, cy=cy, z0=z_apex, cap_bottom=True, cap_top=False)
    acc.add(V, F, "M_lead")
    return z_top


def hat_profile(HV, center=(0.0, 0.0)):
    """(r, z) outer profile of a lathed hat from its vertices: the upper envelope, r increasing; and its max r."""
    hr = np.round(np.hypot(HV[:, 0] - center[0], HV[:, 1] - center[1]), 4)
    rings = np.unique(hr)
    zr = np.array([HV[hr == r_, 2].max() for r_ in rings])
    keep = np.array([zr[i] >= zr[i + 1:].max(initial=-1e9) for i in range(len(rings))])
    return rings[keep], zr[keep], float(rings.max())


def hat_underside(acc, HV, hat_r, center=(0.0, 0.0), t=0.008, seg=96):
    """KIT HELPER (round 3): the lead hat's underside -- a second lathed sheet `t` under the outer surface from the
    axis to the drip, facing down, so the hat reads as a lead sheet with thickness (shadow rays that enter the
    smooth-shaded outer sheet stop on the lead, never on the shingle heads under it)."""
    rr, zz, _ = hat_profile(HV, center)
    m = (rr <= hat_r + 1e-6) & (rr >= 0.05)            # from under the finial socket to the drip
    prof = [(float(r_), float(z_ - t)) for r_, z_ in zip(rr[m], zz[m])]
    if len(prof) < 2:
        return 0
    V, F = lathe_rz(prof, seg, cx=center[0], cy=center[1], z0=0.0, cap_bottom=False, cap_top=False)
    Fl = F if isinstance(F, (list, tuple)) else [F]
    # outward = down (the shingle side): flip if the face over the middle ring points up
    for k, f in enumerate(Fl):
        f = np.asarray(f) if not isinstance(f, np.ndarray) else f
        if f.ndim == 2 and len(f):
            q = V[f[len(f) // 2]]
            if float(np.cross(q[1] - q[0], q[2] - q[0])[2]) > 0:
                f = f[:, ::-1]
        Fl[k] = f
    acc.add(V, Fl, "M_lead")
    return len(V)


def hat_fit_units(g, hat_ob, hat_r, center=(0.0, 0.0), clear=0.01, reach=0.05,
                  objs=("roof_shingles", "roof_underlap", "roof_starter", "rafters", "purlin_rings", "battens")):
    """KIT HELPER (round 3): fit a cone's covering to the lead hat over its apex.  Every vertex of every covering
    unit within hat_r + reach is tested against the hat's ACTUAL outer profile (read from the built hat mesh, after
    the age lift and rotation of each unit); a unit with any vertex less than `clear` under the hat is dropped, and
    so is every unit wholly under the hat (r < hat_r - 3 cm: never seen, apex_blocker closes the apex), so nothing
    under the lead can cast or poke through it.  The roof structure is tested too: the conical_roof rafter hub
    (r 0.39 m, its top ~2 cm over a 44 deg hat at that radius) was what showed through the round-2 hat.  Returns (units' polygons dropped, worst clearance kept)."""
    import bpy
    from .composite import drop_units
    rr, zz, r_max = hat_profile(np.array([v.co[:] for v in hat_ob.data.vertices]), center)

    def z_hat(r):
        return np.interp(r, rr, zz, left=zz[0], right=-1e9)
    out, worst = 0, 1e9
    for nm in objs:
        ob = bpy.data.objects.get(f"{g.prefix}_{nm}")
        if ob is None:
            continue

        def bad(V):
            r = np.hypot(V[:, 0] - center[0], V[:, 1] - center[1])
            under = r < hat_r - 0.03
            near = r < min(hat_r + reach, r_max)
            return near & ((V[:, 2] > z_hat(r) - clear) | under)

        def wholly_under(V):
            return np.hypot(V[:, 0] - center[0], V[:, 1] - center[1]) < hat_r - 0.03
        out += drop_units(ob, wholly_under, rule="all")
        out += drop_units(ob, lambda V: bad(V) & ~wholly_under(V), rule="any")
        V = np.array([v.co[:] for v in ob.data.vertices]) if len(ob.data.vertices) else np.zeros((0, 3))
        if len(V):
            r = np.hypot(V[:, 0] - center[0], V[:, 1] - center[1])
            m = r < min(hat_r + reach, r_max)
            if m.any():
                worst = min(worst, float((z_hat(r[m]) - V[m, 2]).min()))
    log(f"  hat fit: -{out} covering polygons under / through the hat; worst clearance kept {worst:.3f} m")
    return out, worst


def ball_finial(g, ball_r=0.24, hat_r=0.62, hat_drop=None, lean_deg=0.8, center=(0.0, 0.0), seed=5,
                hat_pitch_deg=44.0, blocker=True, clear=0.02, hat_seg=40, fit=False):
    """hat_drop None (round 2 default): the art bible's ~44 deg lead collar, hat_drop = hat_r tan(hat_pitch_deg),
    the drip fitted over the cone's top shingles the way round_apex.turned_apex does (apex = max(reference apex,
    top shingle near the axis) + 2 cm; finial.lead_hat lifts the drip until every shingle under it is `clear`
    under the lead); blocker=True adds apex_blocker under the hat.  Round 3: fit=True runs hat_fit_units (every
    vertex of every unit near the hat tested against the built hat; units through it or wholly under it dropped);
    hat_seg = the hat's segments round the axis (96 keeps the smooth-shaded lead close to its true surface)."""
    rng = np.random.default_rng(seed)
    cx, cy = center
    z_ap = cone_apex_z(g)
    cover = g.SHINGLE_TOP.get("V") if getattr(g, "SHINGLE_TOP", None) else None
    if hat_drop is None:
        hat_drop = hat_r * math.tan(math.radians(hat_pitch_deg))
        if cover is not None and len(cover):
            Vc = np.asarray(cover, float)
            r_ = np.hypot(Vc[:, 0] - cx, Vc[:, 1] - cy)
            if (r_ < 0.6).any():
                z_ap = max(z_ap, float(Vc[r_ < 0.6, 2].max())) + 0.02
    lead = Acc(f"{g.prefix}_cap_collar", 50)
    if fit:
        z_top = fine_hat(lead, cx, cy, z_ap, hat_r, hat_drop, seg=hat_seg, cover=cover, clear=clear)
    else:
        z_top = lead_hat(lead, cx, cy, z_ap, hat_r, hat_drop, seg=hat_seg, cover=cover, clear=clear)
    if fit:
        hat_underside(lead, np.concatenate([np.asarray(v_, float) for v_ in lead.V]), hat_r, center, seg=hat_seg)
    hat_ob = finalize(lead, g.coll, smooth_deg=50.0)
    if fit and hat_ob is not None:
        hat_fit_units(g, hat_ob, hat_r, center)
    if blocker:
        apex_blocker(g, hat_r + 0.30, center)
    if cover is not None and len(cover):
        Vc = np.asarray(cover, float)
        r_ = np.hypot(Vc[:, 0] - cx, Vc[:, 1] - cy)
        ring = (r_ > hat_r - 0.06) & (r_ < hat_r + 0.03)
        if ring.any():
            log(f"  ball finial: hat r {hat_r:.2f} pitch {hat_pitch_deg:.0f} deg, top shingle under the drip at "
                f"{float(Vc[ring, 2].max()):.3f}, apex {z_ap:.3f}, hat top {z_top:.3f}")
    st = Acc(f"{g.prefix}_finial", 50)
    # socket drum + necked collar + ball, one turned stone profile (r, z) from the hat top
    r = ball_r
    prof = [(0.0, -0.02), (0.15, -0.02), (0.165, 0.0), (0.165, 0.10), (0.15, 0.115), (0.11, 0.13), (0.085, 0.16),
            (0.095, 0.185), (0.10, 0.20)]
    zc = 0.20 + r * 0.92
    for a in np.linspace(-0.42 * math.pi, 0.5 * math.pi, 14)[1:]:
        prof.append((r * math.cos(a), zc + 0.94 * r * math.sin(a)))
    prof[-1] = (0.0, prof[-1][1])
    V, F = lathe_rz(prof, 32, cx=0.0, cy=0.0, z0=0.0, cap_bottom=True, cap_top=False)
    # weathered, slightly irregular ball (+-1.2 cm) and ~1 deg lean
    k = rng.uniform(0, 2 * math.pi)
    rr = np.hypot(V[:, 0], V[:, 1])
    th = np.arctan2(V[:, 1], V[:, 0])
    bump = 1 + 0.035 * np.sin(2 * th + k) * np.clip((V[:, 2] - 0.2) / r, 0, 1)
    V[:, 0] *= bump
    V[:, 1] *= bump
    a = math.radians(lean_deg)
    d = np.array([math.cos(k), math.sin(k), 0.0])
    V = V + d[None] * (V[:, 2:3] * math.tan(a))
    V[:, 0] += cx
    V[:, 1] += cy
    V[:, 2] += z_top - 0.03
    st.add(V, F, "M_stone_dressed", wear=0.6)
    finalize(st, g.coll, smooth_deg=50.0)
    tip = float(V[:, 2].max())
    g.FINIAL_TIP_Z = tip
    return tip
