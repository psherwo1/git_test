"""rubble_store -- a small rubble store under a plain thatched gable (no lean-to), written from village_kit/README.md
alone (section 5) as the 4_verify "can a new builder write a recipe" test.  Scratch only, not a deliverable.

6.4 x 4.6 m plan, ridge along X, 50 deg roof with a 0.40 m overhang and 0.35 m verges, an off-centre door in the
-Y eave wall (x = -1.2), one small window in the +X gable end.  Output override: STORE_OUT.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # -> kit/
from village_kit.assembly import KitParams, build_building
from village_kit.components.composite import recenter
from village_kit.components.finish import building_decals, hidden_cull
from village_kit.components.linear_roof import GableRoof, linear_roof
from village_kit.components.masonry import door, masonry_wall, window
from village_kit.components.plan_frame import PlanFrame

KIT = KitParams(x=3.2, y=2.3, wall_z=3.0, pitch_deg=50.0, overhang=0.40, verge=0.35, door_x=-1.2,
                covering="thatch")                                 # the ONE dimension table
# 4_verify note: first try was covering="shake" (README section 7 lists a `shake` in shingles.SIZE_TABLE), which
# raised "unknown covering 'shake'": linear_roof only knows "thatch" and "shingle", and the README does not say so.
KIT.set(covering=os.environ.get("STORE_COVERING", KIT["covering"]),          # 4_verify scoping runs only
        pitch_deg=float(os.environ.get("STORE_PITCH", KIT["pitch_deg"])))
X, Y = KIT["x"], KIT["y"]
ROOF = GableRoof(x0=-X, x1=X, half=Y, wall_z=KIT["wall_z"], pitch_deg=KIT["pitch_deg"],
                 overhang=KIT["overhang"], verge=(KIT["verge"], KIT["verge"]), name="roof")
PATH = [(-X, -Y), (X, -Y), (X, Y), (-X, Y), (-X, -Y)]              # counter-clockwise: interior on the left
OPENINGS = [(X + KIT["door_x"], door(width=1.0, height=2.10)),      # -Y eave wall, off centre (x = -1.2)
            (2 * X + Y, window(width=0.45, sill=1.30))]             # middle of the +X gable end


def top(x, y):                                                      # wall heads tuck 2 cm into the roof deck
    return float(ROOF.under_z(ROOF.to_local([[x, y, 0.0]])[0][1])) + 0.02


if __name__ == "__main__":                                          # spawn workers re-import this file
    out = os.environ.get("STORE_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rubble_store.blend"))
    build_building(dict(
        prefix="STORE", collection="STORE", building_id="rubble_store", frame=PlanFrame,
        params=dict(footprint=(-X, X, -Y, Y), entrance=(KIT["door_x"], -Y)),
        steps=[(masonry_wall, dict(name="walls", path=PATH, top_fn=top, openings=OPENINGS, seed=21)),
               (linear_roof, dict(roof=ROOF, covering=KIT["covering"], seed=22)),
               hidden_cull, recenter],
        decals=building_decals,
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json")))
