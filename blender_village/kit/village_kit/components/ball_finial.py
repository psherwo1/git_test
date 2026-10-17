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


def ball_finial(g, ball_r=0.24, hat_r=0.62, hat_drop=None, lean_deg=0.8, center=(0.0, 0.0), seed=5,
                hat_pitch_deg=44.0, blocker=True, clear=0.02):
    """hat_drop None (round 2 default): the art bible's ~44 deg lead collar, hat_drop = hat_r tan(hat_pitch_deg),
    the drip fitted over the cone's top shingles the way round_apex.turned_apex does (apex = max(reference apex,
    top shingle near the axis) + 2 cm; finial.lead_hat lifts the drip until every shingle under it is `clear`
    under the lead); blocker=True adds apex_blocker under the hat."""
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
    z_top = lead_hat(lead, cx, cy, z_ap, hat_r, hat_drop, seg=40, cover=cover, clear=clear)
    finalize(lead, g.coll, smooth_deg=50.0)
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
