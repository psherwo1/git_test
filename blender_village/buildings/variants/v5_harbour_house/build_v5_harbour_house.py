"""v5_harbour_house (HARB) -- approved building 3, round 3: the ref4 harbour boat hall.  A declarative RECIPE: every
piece is a village_kit module; the building is dimensions + the order of the steps.  Round 3: the cruck pads stand
on dressed responds to the bed (cruck_frame respond_z), the quay walls' footing is flush (path_stone_wall
flush_runs), and the quay's convex corners are quoin-bonded on a never-culled backing (stone_quay).  Round 4: the
client's broader, slumped hall roof (7.0 m at 49 deg, 0.50 m ridge sag, 0.70 m swept eaves), a parameter change:
every plan coordinate (the hall, slip, quay, jetty, ladder, moorings, door and run distances) derives from DIM.

Run:  python -I build_v5_harbour_house.py  -> v5_harbour_house.blend + decal_anchors.json (next to this file)
      HARB_FAST=1 skips the hidden-geometry cull (quick looks only); HARB_OUT=<path.blend> writes elsewhere.

Datum: quay / landward ground Z = 0 (the quay coping and the wall footings at -0.04); harbour bed Z = -2.5.  Built
with the round tower's axis at the origin, then recentred on the plan bounding box (the build log's shift).
  hall     coursed rubble boat hall 7.0 x 9.2 m (path_stone_wall), eave walls ~3.3 m, a 49 deg kit-shingle gable roof
           with a sagging ridge, swept eaves and apex-flared bargeboards (GableRoof soft options), turned finials on
           lead hats at both gables; the land gable carries the door
  water    the water gable: stone piers + a heavy cruck / arched-brace frame with a pointed inner
           arch and plank infill (cruck_frame) over a 5.0 m
  gable    arched boat opening; the slip runs into the hall (boats moor inside) behind a boarded partition
  tower    a round rubble tower at the landward corner (round_stone_body) with a 1.7 m timber top storey (board_belt on a
           plain body: boards, foot and head rings, four lookouts) under a mossy kit-shingle cone (cone_roof) with the
           spike finial; the main roof and the lower wing roof run into it (wall_abutment)
  wing     a lower rubble wing beside the tower under its own soft shingle gable
  quay     a stone quay edge of large blocks (stone_quay: water faces to the bed only, laid as
           low-poly large blocks with a flush coping course) and a short jetty on piles
"""
import os
import sys
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.board_belt import board_belt  # noqa: E402
from village_kit.components.composite import (composite_decals, composite_hidden_cull,  # noqa: E402
                                              cone_roof, inside_box, inside_round, recenter, set_entrance)
from village_kit.components.cone import AGE_R10, age_defaults  # noqa: E402
from village_kit.components.cruck import cruck_frame  # noqa: E402
from village_kit.components.finial import finial  # noqa: E402
from village_kit.components.frame import RoundFrame  # noqa: E402
from village_kit.components.linear_roof import GableRoof, linear_roof  # noqa: E402
from village_kit.components.openings import window  # noqa: E402
from village_kit.components.roof_junction import LINEAR_ROOF_PARTS, round_eave_fill, wall_abutment  # noqa: E402
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall, round_stone_body  # noqa: E402
from village_kit.components.timber_walls import path_timber_wall, roof_top_fn  # noqa: E402
from village_kit.components.wall_openings import door_spec, window_spec  # noqa: E402
from village_kit.components.waterfront import ladder, pile_deck, stone_quay  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v5_harbour_house"

# ---- the ONE dimension tables: the tower's RoundFrame (cone) and the rest of the building ----------------------
KIT = KitParams(radius=2.10, eave_z=8.60, overhang=0.50, pitch_deg=52.0, collar_r=0.62,
                cone_age=age_defaults(**AGE_R10), detail_rule=True)
# round 4 (client must-fix "broader, slumped roof" + CLIENT DIRECTION 14:10): the hall is 7.0 m wide at 49 deg with a
# 0.50 m ridge sag, a deeper overhang and a heavier swept eave.  It widens toward +X only (xw = the hall's west face,
# kept at 0.2 against the tower); the eave walls are not raised; everything else derives from DIM.
DIM = KitParams(r_tower=2.30, batter=1.5, stone_top=6.90, xw=0.2, hy=4.8, half=3.5, len=9.2, wall_z=3.35, pitch=49.0,
                ridge_sag=0.50, bay=3.2, clear=5.0, quay_z=-0.04, bed=-2.5, wing_x0=-6.3, wing_half=1.7, wing_z=2.85)
HALF, HY, QZ = DIM["half"], DIM["hy"], DIM["quay_z"]
HX = DIM["xw"] + HALF                                        # the hall's ridge line (3.7)
Y0, Y1 = HY - DIM["len"] / 2, HY + DIM["len"] / 2            # land gable / water gable faces (0.2 / 9.4)
XW, XE = HX - HALF, HX + HALF                                # hall side faces (0.2 / 7.2)
XJ0, XJ1 = HX - DIM["clear"] / 2, HX + DIM["clear"] / 2      # the arch jambs (1.2 / 6.2)
YP = Y1 - DIM["bay"]                                         # the bay partition / slip head (6.2)
K = HALF / 3.0                                               # the soft-roof options scale with the span (round-3 = 1)
MAIN = GableRoof(x0=Y0, x1=Y1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.70,
                 verge=(0.35, 0.50), origin=(HX, 0.0), yaw_deg=90.0, name="roof", ridge_sag=DIM["ridge_sag"],
                 eave_sag=0.10, eave_sweep=0.40, sweep_len=1.5, verge_flare=0.36 * K, flare_len=2.0 * K,
                 wave=0.02, wave_seed=41)
WING = GableRoof(x0=DIM["wing_x0"], x1=0.0, half=DIM["wing_half"], wall_z=DIM["wing_z"], pitch_deg=50.0,
                 overhang=0.35, verge=(0.40, 0.0), name="wing_roof", ridge_sag=0.14, eave_sweep=0.18, sweep_len=0.8,
                 verge_flare=0.24, flare_len=1.4, wave=0.015, wave_seed=43)
Z_PIER = float(MAIN.under_z_world([[XW, Y1]])[0]) + 0.02     # the water-gable piers stop at the eave line

# ---- plans (interior on the LEFT of the walking direction) -------------------------------------------------------
HALL = [(XJ0, YP), (XJ0, Y1), (XW, Y1), (XW, Y0), (XE, Y0), (XE, Y1), (XJ1, Y1), (XJ1, YP)]
ON_QUAY = (0, 1, 5, 6)                       # the slip walls and water piers stand flush on the quay: flush footing
WING_PATH = [(-0.3, DIM["wing_half"]), (DIM["wing_x0"], DIM["wing_half"]), (DIM["wing_x0"], -DIM["wing_half"]),
             (-0.3, -DIM["wing_half"])]
QUAY = [(XE + 3.4, Y1), (XJ1, Y1), (XJ1, YP), (XJ0, YP), (XJ0, Y1), (XW - 3.2, Y1)]   # every run a water face
XJT = XE + 1.0                                                # the jetty's west edge (it runs XJT .. XJT + 1.8)
JETTY = [(XJT, XJT + 1.8, Y1, Y1 + 5.0)]
S_W = DIM["bay"] + HALF - DIM["clear"] / 2                    # path distance at the W / S / E runs
S_S, S_E = S_W + DIM["len"], S_W + DIM["len"] + 2 * HALF
DOOR_X = HX + 1.1                                             # the land-gable door, 1.1 m east of the ridge line
HALL_OPENINGS = [(S_S + DOOR_X - XW, door_spec(width=1.0, height=2.10)),
                 (S_S + HX - XW, window_spec(width=0.45, height=0.55, sill=4.50)),
                 (S_E + 2.2, window_spec(sill=1.30)), (S_E + 4.8, window_spec(sill=1.30)),
                 (S_W + (Y1 - 4.6), window_spec(sill=1.30))]
W_N, W_W = -0.3 - DIM["wing_x0"], 2 * DIM["wing_half"]                     # wing run lengths (N face, W gable)
WING_OPENINGS = [(W_N + W_W + 2.2, door_spec(width=1.0, height=2.10)),          # S face, x = -4.1
                 (W_N + W_W + 0.9, window_spec(sill=1.30)), (3.2, window_spec(sill=1.30))]
TOWER_OPENINGS = [(15.0, window_spec(width=0.40, height=0.45, sill=1.45)),
                  (55.0, window_spec(width=0.40, height=0.45, sill=3.70)),
                  (215.0, window_spec(width=0.40, height=0.45, sill=5.30))]
LOOKOUTS = [(a, window(width=0.40, height=0.50, sill=0.75, shutters=False)) for a in (25.0, 115.0, 205.0, 295.0)]


def hall_top(x, y):
    """the hall's wall heads: 2 cm into the (sagging, swept) roof deck; the water-gable piers (and the bay faces'
    last 0.3 m behind the cruck infill) stop at the eave line, where the cruck frame's tie beam bears."""
    z = float(MAIN.under_z_world([[x, y]])[0]) + 0.02
    pier = y > Y1 - 0.05 and (x < XJ0 - 0.01 or x > XJ1 + 0.01)
    behind_infill = y > Y1 - 0.30 and (abs(x - XJ0) < 0.01 or abs(x - XJ1) < 0.01)
    return min(z, Z_PIER) if (pier or behind_infill) else z


def wing_top(x, y):
    return float(WING.under_z_world([[x, y]])[0]) + 0.02


def steps():
    deck = lambda roof: (lambda P: roof.under_z_world(P))  # noqa: E731
    in_hall = inside_box(XW + 0.15, XE - 0.15, Y0 + 0.15, Y1 - 0.15, z_fn=deck(MAIN))
    in_wing = inside_box(DIM["wing_x0"] + 0.15, 0.5, -DIM["wing_half"] + 0.15, DIM["wing_half"] - 0.15,
                         z_fn=deck(WING))
    in_tower = inside_round((0.0, 0.0), DIM["r_tower"], depth=0.12, batter_deg=DIM["batter"])
    at_tower = inside_round((0.0, 0.0), DIM["r_tower"], depth=-0.10, batter_deg=DIM["batter"])
    parts = LINEAR_ROOF_PARTS + (("verge", 0.02),)
    return [
        (set_entrance, dict(xy=(DOOR_X, Y0))),
        (stone_quay, dict(name="quay", path=QUAY, top_z=QZ, bed_z=DIM["bed"], detail_z=QZ, core_blocks=True,
                            seed=651)),
        (round_stone_body, dict(name="tower", r_base=DIM["r_tower"], batter_deg=DIM["batter"], top=DIM["stone_top"],
                                openings=TOWER_OPENINGS, clip=lambda P, m=0.0: in_hall(P, m) | in_wing(P, m),
                                open_z="mid", cfg=RUBBLE_LARGE, seed=41)),
        (path_stone_wall, dict(name="hall", path=HALL, top_fn=hall_top, openings=HALL_OPENINGS, clip=in_tower,
                               base=QZ, hero_s=(S_S + DOOR_X - XW - 3.0, S_S + DOOR_X - XW + 3.0), cfg=RUBBLE_LARGE,
                               flush_runs=ON_QUAY, seed=31)),
        (path_stone_wall, dict(name="wing", path=WING_PATH, top_fn=wing_top, openings=WING_OPENINGS, clip=in_tower,
                               cfg=RUBBLE_LARGE, seed=33)),
        (cruck_frame, dict(name="water_gable", O=(HX, Y1, 0.0), t=(1.0, 0.0, 0.0), n=(0.0, 1.0, 0.0), half=HALF,
                           top_fn=roof_top_fn(MAIN), z_pier=Z_PIER, clear=DIM["clear"], spring=2.0, tie=0.32,
                           member_w=(-0.30, 0.06), post=0.30, arch_t=0.34, blade=0.40, collar=0.26, braces=False,
                           pointed=True, pointed_t=0.28, pointed_at=0.62, king_strut=False, respond_z=DIM["bed"],
                           seed=901)),
        (path_timber_wall, dict(name="partition", path=[(XJ1, YP), (XJ0, YP)], z0=QZ, top=2.6,
                                top_fn=roof_top_fn(MAIN), style="board_batten", gable_style="board_batten",
                                rough=True, bow=0.03, seed=303)),
        (linear_roof, dict(roof=MAIN, covering="shingle", seed=12, verge="board", apex_finial="turned",
                           rafter_skip=at_tower)),
        (wall_abutment, dict(roof=MAIN, center=(0.0, 0.0), parts=parts)),
        (linear_roof, dict(roof=WING, covering="shingle", seed=13, verge="board", apex_finial="turned",
                           rafter_skip=at_tower)),
        (wall_abutment, dict(roof=WING, center=(0.0, 0.0), parts=parts, name="wing_abutment")),
        (board_belt, dict(name="tower_top", body=dict(center=(0.0, 0.0), r=KIT["radius"], z0=DIM["stone_top"],
                                                      z1=lambda g: float(g.PLATE_TOP)),
                          foot_ring=True, openings=LOOKOUTS, seed=606)),
        (cone_roof, dict(seed=606)),
        (finial, dict(style="spike")),
        (round_eave_fill, dict(z_bot=None, r_off=-0.03)),
        (pile_deck, dict(name="jetty", rects=JETTY, deck_z=QZ, bed_z=DIM["bed"], land="S", land_z=-0.45,
                         first_row=0.75, moor=[(XJT + 0.2, Y1 + 4.8), (XJT + 1.6, Y1 + 4.8)])),
        (ladder, dict(name="ladder", top=(XJT + 0.9, Y1 + 5.0, QZ), out=(0.0, 1.0), z_bot=DIM["bed"])),
    ] + ([] if os.environ.get("HARB_FAST") else [(composite_hidden_cull, dict(min_polys=200))]) + [recenter]


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_eave_fill",
                                       "_roof_blocker", "_abutment", "_cap_collar"))


def main():
    out = os.environ.get("HARB_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="HARB", collection="HARB", building_id=BID, frame=RoundFrame, params=KIT,
        steps=steps(), decals=partial(composite_decals, moss_normal="slope", timber=True, waterfront=True),
        decal_validate=DECAL_VALIDATE, out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items() if k != "cone_age"}, dims=dict(DIM),
                        datum=dict(quay_z=0.0, coping_z=QZ, bed_z=DIM["bed"], hall_floor="open water (boat slip)",
                                   note="built with the tower axis at the origin, then recentred: see the build log"))))


if __name__ == "__main__":
    main()
