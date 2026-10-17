import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
from village_kit.assembly import KitParams, build_building
from village_kit.components.composite import recenter
from village_kit.components.finish import building_decals, hidden_cull
from village_kit.components.linear_roof import GableRoof, linear_roof
from village_kit.components.masonry import door, masonry_wall, window
from village_kit.components.plan_frame import PlanFrame

KIT = KitParams(x=4.5, y=3.0, wall_z=3.0, pitch_deg=45.0, overhang=0.45)    # the ONE dimension table
X, Y = KIT["x"], KIT["y"]
ROOF = GableRoof(x0=-X, x1=X, half=Y, wall_z=KIT["wall_z"], pitch_deg=KIT["pitch_deg"],
                 overhang=KIT["overhang"], verge=(0.40, 0.40), name="roof")
PATH = [(-X, -Y), (X, -Y), (X, Y), (-X, Y), (-X, -Y)]          # counter-clockwise: interior on the left
OPENINGS = [(X, door(width=1.0, height=2.10)),                   # path distance s: the middle of the -Y wall
            (2 * X + 2 * Y + 2.5, window(width=0.5, sill=1.25)),  # two windows in the +Y wall
            (2 * X + 2 * Y + 6.5, window(width=0.5, sill=1.25))]

def top(x, y):                                                   # wall heads tuck 2 cm into the roof deck
    return float(ROOF.under_z(ROOF.to_local([[x, y, 0.0]])[0][1])) + 0.02

if __name__ == "__main__":                                       # spawn workers re-import this file
    out = os.environ.get("BARN_OUT", os.path.join(os.path.dirname(__file__), "rubble_barn.blend"))
    build_building(dict(
        prefix="BARN", collection="BARN", building_id="rubble_barn", frame=PlanFrame,
        params=dict(footprint=(-X, X, -Y, Y), entrance=(0.0, -Y)),
        steps=[(masonry_wall, dict(name="walls", path=PATH, top_fn=top, openings=OPENINGS, seed=11)),
               (linear_roof, dict(roof=ROOF, covering="shingle", seed=12)),
               hidden_cull, recenter],                           # note 6 cull (family "plan"), then centre the plan
        decals=building_decals,                                  # note 11 anchors; the decal gate is on by default
        out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json")))

