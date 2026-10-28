"""components.porch -- a door hood / porch canopy over ANY door in a straight wall (kit 1.19, a1 add-ons).

    W = plane_wall(origin=door_centre_on_face, out=door_normal)          # components.lean_to.plane_wall
    porch(g, "porch", W, width=2.2, depth=1.0, clear=2.32, pitch_deg=22, covering="shingle",
          soft=dict(eave_sweep=0.05, sweep_len=0.5), below=HOST_ROOF, below_lift_max=0.08)

The village's door hood: a mono-pitch canopy (components.lean_to.mono_roof: the kit's shingle / thatch courses,
deck, bargeboards and soft-line warp; trimmed into the wall under a lime-mortar flaunching with lead verge-end
aprons; registered for the seal-probe guard) carried on two CURVED BRACKETS -- each the barn's hoist-beam arm
(timber_walls.hoist_beam, block=False: a hewn arm run out of the wall on one curved knee brace) -- with a hewn front
beam across the arm ends and a ledger let into the wall under the rafter heads.
    width   between the two brackets (centred on W's origin, the door centre); side: the roof runs this far past each
            bracket (the verge rafters cantilever on the front beam and the ledger)
    depth   plan distance from the wall face to the front beam's centre line; overhang: the eave past it
    clear   the front beam's underside (art bible 7: >= 2.30 m over a doorway): the arm tops are at clear, the beam
            sits on them, the rafters on the beam; z_face follows from the pitch
    brace   (reach out along the arm, drop down the wall) of each bracket's curved brace
The roof must stay under the host's eave: pass below=<host GableRoof> (and below_lift_max for a host whose eave is
lifted over the door, GableRoof(eave_lifts=...), so the arched soffit is the limit).
Objects: <P>_<name>_* (mono_roof), <P>_<name>_arm0_frame / _arm1_frame (brackets), <P>_<name>_beam (front beam)."""
import math

import numpy as np

from ..core import log
from ..geom import Acc, finalize
from .lean_to import EZ, RAFTER, _beam_along, mono_roof


def porch(g, name, W, width=2.2, depth=1.0, clear=2.32, pitch_deg=22.0, overhang=0.25, side=0.25,
          covering="shingle", beam=(0.16, 0.18), arm=(0.16, 0.20), arm_out=0.12, arm_tail=0.20, brace=(0.55, 0.60),
          soft=None, below=None, below_lift_max=None, seed=1931, **kw):
    """KIT COMPONENT (kit 1.19): see the module doc.  -> the mono_roof record (+ "arms", "clear")."""
    from .timber_walls import hoist_beam
    p = math.radians(pitch_deg)
    bw, bh = beam
    raf_drop = (0.035 + RAFTER["h"]) / math.cos(p)          # deck top -> rafter underside (kit deck_t 0.035)
    z_ref_beam = clear + bh + raf_drop                      # deck top over the front beam's centre line
    z_face = z_ref_beam + depth * math.tan(p)
    hw = 0.5 * float(width)
    rec = mono_roof(g, name, W, -hw, hw, depth, z_face, pitch_deg=pitch_deg, overhang=overhang,
                    verge=(side, side), covering=covering, soft=soft, below=below, below_lift_max=below_lift_max,
                    seed=seed, plate=None, **kw)
    roof = rec["roof"]
    n, t, O = W["n"], W["t"], W["O"]
    pre = f"{g.prefix}_{name}"
    # ---- the front beam across the arm ends (under the rafters; follows the roof's warp) ----------------------------
    acc = Acc(pre + "_beam")
    xs = np.linspace(roof.xa + 0.03, roof.xb - 0.03, max(4, int((roof.xb - roof.xa) / 0.25) + 2))
    _beam_along(acc, roof, xs, rec["half"], lambda x: rec["raf_bot"](rec["half"]) - bh / 2 + 0.01, bw, bh, "M_timber")
    finalize(acc, g.coll, smooth_deg=30.0)
    # ---- the two curved brackets (the barn's hoist-beam arm, no pulley block) ----------------------------------------
    arms = []
    for k, x in enumerate((-hw, hw)):
        q = roof.to_world(np.array([[x, rec["half"], rec["raf_bot"](rec["half"]) - bh + 0.01]]))[0]
        z_arm = float(q[2]) + 0.005                          # the beam bears on the arm (5 mm into its underside)
        at = O + t * x
        hoist_beam(g, f"{name}_arm{k}", (at[0], at[1]), (n[0], n[1]), z_arm, length=depth + arm_out, tail=arm_tail,
                   section=arm, brace=brace, brace_t=(0.12, 0.13), block=False, lean=0.0)
        arms.append(dict(x=x, z=z_arm))
    z_under = min(a["z"] for a in arms) - arm[1]
    log(f"  {pre}: porch {width:.2f} m between brackets, front beam underside {clear:.2f} m, arm undersides "
        f"{z_under:.2f} m, deck at the wall {z_face:.2f} m")
    rec.update(arms=arms, clear=float(clear), z_face=z_face)
    _ = EZ
    return rec


__all__ = ["porch"]
