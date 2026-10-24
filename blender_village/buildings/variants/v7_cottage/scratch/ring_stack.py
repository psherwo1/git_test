"""v7 round 2 scratch (FAST, not a deliverable): the cottage recipe + a second round stack r 0.52 THROUGH the back
slope, to prove roof_addons.chimney's through-slope path (_ring_abutment: ring trim, ring flaunching, seal-probe
registration).  The same blend serves the round-2 iteration close-ups of the front junctions (no cull).
python -I ring_stack.py [out.blend]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["COTT_FAST"] = "1"
os.environ["COTT_OUT"] = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fast", "v7_ring_stack.blend")
sys.path.insert(0, os.path.dirname(HERE))

import build_v7_cottage as R  # noqa: E402
from village_kit.components.composite import inside_box  # noqa: E402

_orig = R.steps


def steps():
    s = _orig()
    in_house = inside_box(R.X0 + 0.15, R.X1 - 0.15, -R.HALF + 0.15, R.HALF - 0.15,
                          z_fn=lambda P: R.MAIN.under_z_world(P))
    s.insert(len(s) - 1, (R.chimney, dict(name="ring_stack", center=(-2.4, 1.45), r_base=0.52, batter_deg=1.5,
                                          roof=R.MAIN, clip=in_house, over_ridge=0.45, seed=61)))
    return s


R.steps = steps

if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.environ["COTT_OUT"]), exist_ok=True)
    R.main()
