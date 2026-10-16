"""components.windows -- small deep-set timber windows (kit 1.1.0, from the hilltop keep).

hall_windows(g, seed=909)      KIT COMPONENT: heavy pegged timber frames with a cross mullion (2 x 2 lights) in every
                               framed rectangular opening of an OctFrame hall (the dressed jambs / sills / lintels are
                               part of oct_hall's masonry) -> <P>_hall_window_frames
annex_window(g)                KIT COMPONENT: the annex window (g.WWIN): timber frame + mullion set back in the reveal,
                               timber lintel, projecting stone sill with a drip, dark blocker room -> <P>_wing_window
window_spec(...)               the spec dict annex_window / the annex wall read
"""
import numpy as np

from ..geom import Acc, finalize
from .hewn import peg
from .oct_frame import FR, FN, fmap
from .oct_hall import facet_obox
from .plank_doors import build_wall_openings


def build_window_frames(coll, seed=909):
    rng = np.random.default_rng(seed)  # noqa: F841  (kept: the seed slot of the phase-1 build)
    acc = Acc(FR.prefix + "_hall_window_frames")
    for op in FR.OPENINGS:
        if op["kind"] != "rect" or not op.get("frame"):
            continue
        k, xc, hw, z0, z1, d = op["k"], op["xc"], op["hw"], op["z0"], op["z1"], op["depth"]
        fw = 0.10 if hw > 0.3 else 0.08
        w0, w1 = -d - 0.12, -d
        r = 0.012
        facet_obox(acc, k, xc - hw, xc - hw + fw, z0, z1, w0, w1, r, "M_timber")
        facet_obox(acc, k, xc + hw - fw, xc + hw, z0, z1, w0, w1, r, "M_timber")
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, z0, z0 + fw, w0, w1 + 0.01, r, "M_timber")
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, z1 - fw, z1, w0, w1, r, "M_timber")
        mw = 0.055
        facet_obox(acc, k, xc - mw / 2, xc + mw / 2, z0 + fw - 0.01, z1 - fw + 0.01, w0 + 0.02, w1 - 0.02, 0.008, "M_timber")
        zt = z0 + (z1 - z0) * 0.56
        facet_obox(acc, k, xc - hw + fw - 0.01, xc + hw - fw + 0.01, zt - mw / 2, zt + mw / 2, w0 + 0.02, w1 - 0.02, 0.008,
                   "M_timber")
        # pegs at the frame corners
        for xx in (xc - hw + fw / 2, xc + hw - fw / 2):
            for zz in (z0 + fw / 2, z1 - fw / 2):
                p = fmap(k, np.array([xx]), np.array([zz]), np.array([w1]))[0]
                peg(FR, p, np.array([FN[k][0], FN[k][1], 0.0]), rad=0.010, proud=0.008)
    finalize(acc, coll)



def window_spec(xc=-7.4, width=0.45, height=0.55, sill=1.30, frame=0.07, depth=0.16):
    """small timber window spec (clear width / height, sill height, frame width, set-back in the reveal)."""
    return dict(xc=xc, hw=width / 2, z0=sill, z1=sill + height, depth=depth, fw=frame)


def hall_windows(g, seed=909):
    """KIT COMPONENT: timber frames of the hall's framed windows."""
    build_window_frames(g.sub("hall"), seed=seed)


def annex_window(g):
    """KIT COMPONENT: the annex wall's small timber window (g.WWIN)."""
    build_wall_openings(g.sub("wing"), door=None, window=g.WWIN)
