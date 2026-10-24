"""v6_barn (BARN) -- the village barn, round 2.  A declarative RECIPE: every piece is a village_kit module; the building
is dimensions + the order of the steps.

Run:  python -I build_v6_barn.py  -> v6_barn.blend + decal_anchors.json (next to this file)
      BARN_FAST=1 skips the hidden-geometry cull (quick looks only); BARN_OUT=<path.blend> writes elsewhere.

Built with the kiln's axis at the origin, then recentred on the plan bounding box (the build log's shift).
  barn   13.6 x 7.0 m: a rubble plinth (path_stone_wall) under rough old post-and-plank walls with board-and-batten
         gables (path_timber_wall rough / bow), a steep 50 deg soft thatch roof (GableRoof ridge sag, swept eaves,
         flared verges) with turned finials on lead hats at both gables
  kiln   the round element (note 17): a SQUAT round rubble drying kiln / granary (5.0 m across, 3.95 m wall: wall /
         diameter 0.79) standing against the middle of the front long side (round_stone_body; its back meets the
         thatch just above the eave), under its own low 44 deg mossy shingle cone (cone_roof) with the village stone
         ball finial, apex well under the barn ridge; the barn's thatch eave runs into its wall (wall_abutment) and its
         cone eave oversails the thatch -- it breaks the barn's eave line instead of standing at a corner or an end
         (v5 / v3), and is lower than the barn, not a tower
  doors  double cart doors on the front long side (boat_door), a man door with steps in the east gable, a hayloft
         door high in the west gable under a hoist beam, small windows and slits
"""
import os
import sys
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.ball_finial import ball_finial  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull, cone_roof,  # noqa: E402
                                              inside_box, inside_round, recenter, set_entrance)
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.roof_junction import round_eave_fill, wall_abutment  # noqa: E402
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall, round_stone_body  # noqa: E402
from village_kit.components.timber_walls import (boat_door, hoist_beam, loft_door, path_timber_wall,  # noqa: E402
                                                 roof_top_fn)
from village_kit.components.wall_openings import door_spec, window_spec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v6_barn"

# ---- the ONE dimension tables: the kiln's RoundFrame (cone) and the barn ----------------------------------------
KIT = KitParams(radius=2.36, eave_z=4.15, overhang=0.42, pitch_deg=44.0, collar_r=0.74,
                cone_age=age_defaults(**AGE_R10), detail_rule=True)
DIM = KitParams(r_kiln=2.50, batter=1.5, c=2.30, half=3.5, x0=-7.0, x1=7.0, plinth=0.35, plate=3.0, wall_z=3.10,
                pitch=50.0, cart_x=-4.5, cart_w=3.0, end=0.50)
HALF, C = DIM["half"], DIM["c"]                    # the front wall line is y = C (the kiln's axis 2.30 m in front)
X0, X1, Y0, Y1 = DIM["x0"], DIM["x1"], C, C + 2 * HALF
XE, XW = DIM["end"], -DIM["end"]                   # the front runs end inside the kiln's wall
ROOF = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.55,
                 verge=(0.45, 0.45), origin=(0.0, C + HALF), thick=0.34, name="barn_roof", ridge_sag=0.30, eave_sag=0.05,
                 eave_sweep=0.22, sweep_len=1.2, verge_flare=0.24, flare_len=1.8, wave=0.03, wave_seed=61, ridge_seat=True,
                 eave_lifts=[eave_lift(DIM["cart_x"], side=-1, width=6.4, height=0.85, fade=2.5)])
PAD = DIM["cart_w"] / 2 + 0.26 + 0.05            # the plinth runs into the cart door's stone pads (half door + jamb + 5 cm)

# ---- plan: one open path round the barn from the kiln's east side to its west side (interior on the left) --------
PATH = [(XE, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0), (XW, Y0)]
PLINTHS = [PATH[:-1] + [(DIM["cart_x"] - PAD, Y0)], [(DIM["cart_x"] + PAD, Y0), (XW, Y0)]]
L0, LW, LL = X1 - XE, 2 * HALF, X1 - X0
S = dict(SE=lambda x: x - XE, E=lambda y: L0 + (y - Y0), N=lambda x: L0 + LW + (X1 - x),
         W=lambda y: L0 + LW + LL + (Y1 - y), SW=lambda x: L0 + 2 * LW + LL + (x - X0))
SLIT = window(width=0.24, height=0.62, sill=1.30, shutters=False)
OPENINGS = [(S["SW"](DIM["cart_x"]), boat_door(width=DIM["cart_w"], height=2.9, to_ground=True)),
            (S["SE"](3.6), window(width=0.50, height=0.55, sill=1.10)),
            (S["E"](Y0 + 2.2), door(width=1.0, height=2.05, steps_to=0.0)),
            (S["E"](Y0 + 5.0), SLIT), (S["N"](-4.4), SLIT), (S["N"](0.0), SLIT), (S["N"](4.4), SLIT),
            (S["W"](Y0 + HALF), loft_door(width=1.20, height=1.70, sill=2.63)), (S["W"](Y0 + 1.6), SLIT)]
KILN_OPENINGS = [(0.0, door_spec(width=0.95, height=2.05)),
                 (62.0, window_spec(width=0.32, height=0.42, sill=2.70)),
                 (298.0, window_spec(width=0.32, height=0.42, sill=2.70))]


def steps():
    deck = lambda P: ROOF.under_z_world(P)  # noqa: E731
    in_barn = inside_box(X0 + 0.15, X1 - 0.15, Y0 + 0.15, Y1 - 0.15, z_fn=deck)
    in_kiln = inside_round((0.0, 0.0), DIM["r_kiln"], depth=0.12, batter_deg=DIM["batter"])
    at_kiln = inside_round((0.0, 0.0), DIM["r_kiln"], depth=-0.10, batter_deg=DIM["batter"])
    deep_kiln = inside_round((0.0, 0.0), DIM["r_kiln"], depth=0.10, batter_deg=DIM["batter"])
    return [
        (set_entrance, dict(xy=(DIM["cart_x"], Y0))),
        (round_stone_body, dict(name="kiln", r_base=DIM["r_kiln"], batter_deg=DIM["batter"], openings=KILN_OPENINGS,
                                clip=in_barn, open_z="mid", cfg=RUBBLE_LARGE, seed=41)),
    ] + [(path_stone_wall, dict(name=f"plinth{i}", path=p, top=DIM["plinth"], clip=in_kiln, cfg=RUBBLE_LARGE,
                                 seed=31 + i)) for i, p in enumerate(PLINTHS)] + [
        (path_timber_wall, dict(name="walls", path=PATH, z0=DIM["plinth"], top=DIM["plate"], top_fn=roof_top_fn(ROOF),
                                style="post_plank", openings=OPENINGS, rough=True, bow=0.03, seed=303)),
        (linear_roof, dict(roof=ROOF, covering="thatch", clip=deep_kiln, seed=71, rafter_skip=at_kiln,
                           ridge_caps=True, verge_apex=True, apex_finial="turned",
                           verge_roll=True, comb_step=0.75, comb_backing=True, rafter_lift_max=0.08)),
        (wall_abutment, dict(roof=ROOF, center=(0.0, 0.0))),
        (cone_roof, dict(seed=606)),
        (ball_finial, dict(seed=5, hat_seg=96, fit=True)),
        (hoist_beam, dict(name="hoist", at=(X0, C + HALF), out=(-1.0, 0.0), z=6.30)),
        (round_eave_fill, dict(z_bot="wall", r_off=-0.03)),
    ] + ([] if os.environ.get("BARN_FAST") else [(composite_hidden_cull, dict(min_polys=200))]) + [recenter]


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_eave_fill",
                                       "_roof_blocker", "_abutment", "_cap_collar", "_apex_blocker"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,      # round 2: v3's gate for stepped
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))      # thatch / shingle courses (moss)


def main():
    out = os.environ.get("BARN_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="BARN", collection="BARN", building_id=BID, frame=RoundFrame, params=KIT,
        steps=steps(), decals=partial(composite_decals, moss_normal="slope", timber=True, timber_soot=False),
        decal_validate=DECAL_VALIDATE, out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items() if k != "cone_age"}, dims=dict(DIM),
                        datum=dict(ground_z=0.0, note="built with the kiln axis at the origin, then recentred"))))


if __name__ == "__main__":
    main()
