"""components.round_apex -- cross-family apex dressing for a round cone (kit 1.7.0 candidate, v4_mixed).

The hut family closes its cone with the "spike" lead-hat collar (components.finial.finial); the keep family has a
"turned" finial over a fitted lead hat (finial.turned_finial / finial.lead_hat) but only on its octagonal bell caps.
turned_apex puts the keep's turned finial and fitted lead hat on ANY RoundFrame cone, so a hut-family roof can carry
the keep's finial language (finial(style) variety without touching either family's function).
"""
import math

import numpy as np

from ..core import log


def turned_apex(g, hat_r=None, hat_pitch_deg=44.0, scale=0.85, lean_deg=1.0, lean_dir=(0.6, -0.8), seg=32,
                clear=0.02):
    """KIT COMPONENT (RoundFrame, after conical_roof): a lead hat of radius hat_r (default g.COLLAR_R) and pitch
    hat_pitch_deg (art bible 1.5: shallower than the roof), its drip fitted over the cone's top shingles
    (finial.lead_hat(cover=...): no shingle pokes through), and the keep's turned finial (finial.TURNED_PROFILE x
    scale, ~1.45 m x scale) leaning lean_deg.  Objects <PREFIX>_cap_collar (M_lead) and <PREFIX>_finial (M_iron) --
    the names the round decal recipe looks for.  Sets g.COLLAR_R to the hat radius.  Returns (z_drip, z_top, tip)."""
    from ..geom import Acc, finalize
    from .finial import lead_hat, turned_finial
    r0 = float(hat_r if hat_r is not None else g.COLLAR_R)
    V = np.asarray(g.SHINGLE_TOP["V"], float)
    r = np.hypot(V[:, 0], V[:, 1])
    # apex height of the roof reference surface, extrapolated from its top sample to the axis
    pr, pz = np.asarray(g.PR, float), np.asarray(g.PZ, float)
    i = int(np.argmin(pr))
    z_axis = float(pz[i] + pr[i] * math.tan(g.PITCH))
    top_sh = float(V[r < 0.6, 2].max()) if (r < 0.6).any() else z_axis
    z_apex = max(z_axis, top_sh) + 0.02
    h0 = r0 * math.tan(math.radians(hat_pitch_deg))
    acc = Acc(f"{g.prefix}_cap_collar", 50.0)
    z_top = lead_hat(acc, 0.0, 0.0, z_apex, r0, h0, seg=seg, cover=V, clear=clear)
    fin = Acc(f"{g.prefix}_finial", 45.0)
    turned_finial(fin, (0.0, 0.0, z_top - 0.01), scale=scale, lean_deg=lean_deg, lean_dir=lean_dir, seg=seg)
    finalize(acc, g.coll, smooth_deg=50.0)
    finalize(fin, g.coll, smooth_deg=45.0)
    g.COLLAR_R = r0
    tip = z_top - 0.01 + 1.45 * scale
    log(f"turned apex: hat r {r0:.2f} apex {z_apex:.3f} top {z_top:.3f} finial tip ~{tip:.2f}")
    return z_apex - h0, z_top, tip
