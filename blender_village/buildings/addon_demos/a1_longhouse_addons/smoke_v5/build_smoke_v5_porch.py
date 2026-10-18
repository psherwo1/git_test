"""a1 round 3, must-fix 3: REUSE SMOKE -- the a1 porch (components.porch, unchanged, no new module) on a second host,
the accepted v5 harbour house (r08), over its land-gable door.  v5's accepted recipe is IMPORTED read only (its main()
is never called; nothing under buildings/variants/v5_harbour_house/ is written).  FAST: v5's own HARB_FAST switch
skips the hidden cull.  No host eave_lift: the door is in the GABLE, so the roof (its verge, ~6 m) is far above.
The lean-to is NOT called: v5's eave walls carry the deck at 3.35 m with a swept eave, so a lean-to under it cannot
give the 2.10 m plate (art bible 7) without lifting the host eave (see the a1 round-3 builder entry).
Run:  python -I build_smoke_v5_porch.py   -> smoke_v5_porch.blend (next to this file)"""
import importlib.util
import os
import sys
from functools import partial

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "kit"))
os.environ.setdefault("HARB_FAST", "1")

from village_kit.assembly import build_building  # noqa: E402
from village_kit.components.composite import recenter  # noqa: E402
from village_kit.components.lean_to import plane_wall  # noqa: E402
from village_kit.components.linear_roof import eave_lift  # noqa: E402
from village_kit.components.porch import porch  # noqa: E402

_spec = importlib.util.spec_from_file_location("v5_recipe", os.path.join(
    ROOT, "buildings", "variants", "v5_harbour_house", "build_v5_harbour_house_r08_accepted.py"))
V5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V5)                     # the accepted recipe, read only

# ---- THE CALL (the a1 porch's own settings; only the wall frame and the host roof change) -------------------------
PORCH_V5 = dict(name="porch", W=plane_wall((V5.DOOR_X, V5.Y0), (0.0, -1.0)), width=2.1, depth=1.0, clear=2.32,
                pitch_deg=22.0, overhang=0.25, side=0.20, covering="shingle", brace=(0.65, 0.75),
                soft=dict(eave_sweep=0.08, sweep_len=0.5, wave=0.008, verge_flare=0.05, flare_len=0.45,
                          eave_lifts=[eave_lift(0.0, side=1, width=2.6, height=0.22, fade=1.0)]),
                verge_board=dict(below=0.025, above=0.0), below=V5.MAIN, below_roll=0.25, seed=1931)


def steps():
    st = [s for s in V5.steps() if (s[0] if isinstance(s, tuple) else s) is not recenter]
    return st + [(porch, PORCH_V5), recenter]


def main():
    out = os.environ.get("SMOKE_OUT", os.path.join(HERE, "smoke_v5_porch.blend"))
    build_building(dict(
        prefix="HARB", collection="HARB", building_id="smoke_v5_porch", frame=V5.RoundFrame, params=V5.KIT,
        steps=steps(), decals=partial(V5.composite_decals, moss_normal="slope", timber=True, waterfront=True),
        decal_validate=V5.DECAL_VALIDATE, out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(host="v5_harbour_house r08 (recipe imported)", smoke="a1 round 3 porch reuse")))


if __name__ == "__main__":
    main()
