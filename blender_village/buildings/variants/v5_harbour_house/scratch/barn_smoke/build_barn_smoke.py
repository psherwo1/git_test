"""scratch smoke recipe (round 2): a timber barn from the timber family in a few lines -- proves the family stays a
short recipe, and exercises the large-door head rule (a 3.0 m door in a 2.6 m storey: "clamp" on the S face,
"trim" on the N face) and the open shutters on the kit's plank leaves / straps / pooled pintles.  Not a deliverable."""
import os
import sys

sys.path.insert(0, r"C:\GitHubDesktop\git_test\blender_village\kit")
from village_kit.assembly import build_building  # noqa: E402
from village_kit.components.composite import BACKED_PARTS, composite_decals, composite_hidden_cull, recenter  # noqa: E402
from village_kit.components.linear_roof import GableRoof, linear_roof  # noqa: E402
from village_kit.components.masonry import masonry_wall, window  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.timber_walls import boat_door, path_timber_wall, rect_openings, rect_path, roof_top_fn  # noqa: E402

R = (-4.0, 4.0, -2.75, 2.75)
ROOF = GableRoof(x0=-4.0, x1=4.0, half=2.75, wall_z=3.05, pitch_deg=50, overhang=0.45, verge=(0.40, 0.40),
                 ridge_sag=0.12, eave_sweep=0.18, verge_flare=0.30, wave=0.02)
OPS = rect_openings(R, [("E", 0.0, boat_door(width=2.6, height=3.0)), ("W", 0.0, boat_door(width=2.4, height=2.2,
                        head_rule="trim")), ("S", -2.0, window(width=0.55, height=0.6, sill=1.2)),
                        ("S", 2.0, window(width=0.55, height=0.6, sill=1.2))])

if __name__ == "__main__":
    out = os.environ.get("BARN_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "barn_smoke.blend"))
    build_building(dict(prefix="BARN", collection="BARN", building_id="barn_smoke", frame=PlanFrame,
                        params=dict(footprint=R, entrance=(0.0, -2.75)),
                        steps=[(masonry_wall, dict(name="plinth", path=rect_path(*R), top=0.30, seed=11)),
                               (path_timber_wall, dict(name="walls", path=rect_path(*R), z0=0.30, top=2.95,
                                                       top_fn=roof_top_fn(ROOF), style="post_plank", openings=OPS,
                                                       rough=True, bow=0.03)),
                               (linear_roof, dict(roof=ROOF, covering="shingle", verge="board", apex_finial="turned")),
                               (composite_hidden_cull, dict(parts=BACKED_PARTS)), recenter],
                        decals=lambda g: composite_decals(g, timber=True), out=out,
                        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json")))
