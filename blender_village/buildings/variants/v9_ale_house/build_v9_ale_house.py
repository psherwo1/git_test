"""v9_ale_house (ALEH) -- a low T-plan village ale-house / inn, round 1 (preview): the kit's ROOF and WALL add-ons
on rounded "loaf" thatch roofs (producer notes 16-19).  A declarative RECIPE: every piece is a village_kit module.

Run:  python -I build_v9_ale_house.py  -> v9_ale_house.blend + decal_anchors.json (next to this file)
      ALEH_FAST=1 skips the hidden-geometry cull (quick looks only); ALEH_OUT=<path.blend> writes elsewhere.

Plan (x along the main ridge, the front long side at y = -HALF, ground Z = 0), then recentred.
  hall     a rubble hall 12.0 x 6.0 m (path_stone_wall, RUBBLE_LARGE) under a soft thatch LOAF: GableRoof(hips="both",
           crown) -- a round hip at both ends, the eave an oval round the house; TWO thatch EYEBROWS (one per main
           slope: front x -2.8, back x +2.2) and a GABLED DORMER on the back slope
  wing     the cross wing 4.4 m wide projecting 6.0 m from the front under its own loaf (round hip at the free S
           end), a rolled thatch VALLEY where it meets the hall; the wing's west eave is lifted in one soft arch over
           the ENTRANCE, which has a kit PORCH (a bell-cast hood on two curved brackets)
  turret   a short ROUND STAIR TURRET (battered rubble, round_stone_body) at the wing's free SW corner, under a small
           thatch DOME (a round-hipped GableRoof: the hip half-cones meet in a round eave); the wing's roof runs into
           it (roof_junction.wall_abutment)
  chimney  a ROUND battered rubble stack at the east end through the east round hip, dressed cap and round pot
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.composite import (composite_decals, inside_box, inside_round, recenter,  # noqa: E402
                                              set_entrance)
from village_kit.components.lean_to import plane_wall  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, eyebrow, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.orient_fix import orient_closed_slabs, orient_open_islands  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.porch import porch  # noqa: E402
from village_kit.components.roof_addons import (GabledDormer, any_clip, chimney, chimney_decals,  # noqa: E402
                                                deck_clip, gabled_dormer, hidden_cull, reentrant_views, roof_valley,
                                                roofs_top_fn, solid_clip, straight_span)
from village_kit.components.roof_junction import wall_abutment  # noqa: E402
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall, round_stone_body  # noqa: E402
from village_kit.components.timber_walls import path_timber_wall  # noqa: E402
from village_kit.core import log  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v9_ale_house"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
DIM = KitParams(half=3.0, x0=-6.0, x1=6.0, wall_z=2.9, pitch=46.0, crown=0.5, wing_x=3.0, wing_half=2.2,
                wing_y0=-9.0, wing_pitch=42.0, wing_crown=0.12, door_y=-5.8, stack_x=6.15, stack_r=1.05,
                stack_batter=3.5, shoulder_z=3.0, brow_f=-2.8, brow_b=2.2, dormer_x=-2.2, tur_r=1.25,
                tur_batter=2.0, tur_wall_z=3.9)
HALF, X0, X1 = DIM["half"], DIM["x0"], DIM["x1"]
WX, WH, WY0 = DIM["wing_x"], DIM["wing_half"], DIM["wing_y0"]
DOOR_Y = DIM["door_y"]
CX, CY = WX - WH - 0.55, WY0 - 0.55          # the turret's axis: pushed 0.55 m out from the wing's free SW corner
BROW_F = eyebrow(DIM["brow_f"], side=-1, grid="thatch", profile="arch", respace=True, d=1.3, width=2.2, height=0.90,
                 lip=0.22, plateau=0.15, fade=1.0, window=dict(width=0.60, height=0.36, sill=0.05), close_ends=True,
                 span_rows=True, seed=3)
BROW_B = eyebrow(DIM["brow_b"], side=1, grid="thatch", profile="arch", respace=True, d=1.3, width=2.2, height=0.90,
                 lip=0.22, plateau=0.15, fade=1.0, window=dict(width=0.60, height=0.36, sill=0.05), close_ends=True,
                 span_rows=True, seed=4)
MAIN = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.45,
                 verge=(0.0, 0.0), thick=0.28, name="roof", ridge_sag=0.15, eave_sag=0.04, eave_sweep=0.16,
                 sweep_len=1.0, wave=0.02, wave_seed=71, ridge_seat=True, hips="both", hip_seam=(-1, WX),
                 crown=DIM["crown"], eyebrows=[BROW_F, BROW_B])
# the wing's west eave is lifted in one soft arch over the porch (a1's recipe); the wing's local x = world y
LIFT_W = eave_lift(DOOR_Y, side=1, width=4.8, height=1.75, fade=2.2)
LIFT_MAX = 0.08
WING = GableRoof(x0=WY0, x1=0.0, half=WH, wall_z=DIM["wall_z"] - 0.05, pitch_deg=DIM["wing_pitch"], overhang=0.45,
                 verge=(0.0, 0.0), origin=(WX, 0.0), yaw_deg=90.0, thick=0.28, name="wing_roof", ridge_sag=0.10,
                 eave_sag=0.03, eave_sweep=0.14, sweep_len=0.9, wave=0.02, wave_seed=73, ridge_seat=True,
                 hips=("lo",), crown=DIM["wing_crown"], eave_lifts=[LIFT_W])
DORMER = GabledDormer(MAIN, x=DIM["dormer_x"], side=1, d=0.35, width=1.30, pitch=50.0, overhang=0.22, verge=0.28,
                      window=dict(width=0.55, height=0.45, sill=0.30, lights=2), name="dormer")
# the turret's dome: both ends round hips, so the half-cones meet in a (nearly) round eave over the round stair
R_TOP = DIM["tur_r"] - DIM["tur_wall_z"] * np.tan(np.radians(DIM["tur_batter"]))
DOME = GableRoof(x0=-1.2, x1=1.2, half=float(R_TOP), wall_z=DIM["tur_wall_z"], pitch_deg=52.0, overhang=0.40,
                 verge=(0.0, 0.0), origin=(CX, CY), thick=0.22, step=0.08, exposure=0.26, name="turret_roof",
                 ridge_sag=0.0, eave_sweep=0.10, sweep_len=0.6, wave=0.015, wave_seed=79, ridge_seat=True,
                 hips="both", crown=0.10)

# ---- plan: one path round the T and back (interior on the left) --------------------------------------------------
PATH = [(X1, 0.0), (X1, HALF), (X0, HALF), (X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0),
        (WX + WH, -HALF), (X1, -HALF), (X1, 0.0)]
_S = [0.0]
for _a, _b in zip(PATH[:-1], PATH[1:]):
    _S.append(_S[-1] + abs(_b[0] - _a[0]) + abs(_b[1] - _a[1]))
S_N, S_W, S_F, S_WW, S_WS, S_WE, S_FE = _S[1], _S[2], _S[3], _S[4], _S[5], _S[6], _S[7]
WIN = window(width=0.50, height=0.60, sill=1.05)
SMALL = window(width=0.40, height=0.45, sill=1.20)
DOOR_S = S_WW + (-HALF - DOOR_Y)                       # the entrance: the wing's west wall, under the porch
OPENINGS = [(S_N + (X1 - DIM["dormer_x"]), WIN), (S_N + (X1 - DIM["brow_b"]), SMALL),            # back
            (S_N + (X1 - 4.4), SMALL),
            (S_W + (HALF - 0.9), SMALL),                                                       # west end
            (S_F + (DIM["brow_f"] - X0), SMALL), (S_F + (-0.2 - X0), WIN),                     # hall front
            (DOOR_S, door(width=1.0, height=1.95, threshold=0.14)),                            # the entrance
            (S_WW + 4.7, WIN),                                                                 # wing west, by the turret
            (S_WS + WH + 0.9, window(width=0.55, height=0.65, sill=1.05)),                     # wing south end
            (S_WE + 2.3, WIN), (S_WE + 4.6, WIN),                                              # wing east side
            (S_FE + 0.45, SMALL)]                                                              # front, east
TOP = roofs_top_fn([MAIN, WING])
Z_CAP = DIM["wall_z"] - 0.30


def _end_span(xy_fn, lim):
    ss = np.linspace(0.0, lim, 400)
    ok = [s for s in ss if TOP(*xy_fn(s)) >= Z_CAP + 0.35]
    return float(max(ok)) if ok else 0.0


YT = _end_span(lambda s: (X1, s), HALF)
YT_W = _end_span(lambda s: (WX + s, WY0), WH)


def stone_top(x, y):
    z = TOP(x, y)
    if ((abs(x - X1) < 0.75 or abs(x - X0) < 0.75) and abs(y) < YT) or (abs(y - WY0) < 0.75 and abs(x - WX) < YT_W):
        return min(z, Z_CAP)
    return z


GABLETS = [("hip_end_W", [(X0, YT), (X0, -YT)], 0.0),
           ("hip_end_E_s", [(X1, -YT), (X1, -0.30)], 0.16), ("hip_end_E_n", [(X1, 0.30), (X1, YT)], 0.16),
           ("hip_end_S", [(WX - YT_W, WY0), (WX + YT_W, WY0)], 0.0)]
FOOT = [(X0, -HALF), (WX - WH, -HALF), (WX - WH, WY0), (WX + WH, WY0), (WX + WH, -HALF), (X1, -HALF), (X1, HALF),
        (X0, HALF)]

# the turret's wall head: a hair into the dome's deck all round
_th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
_ring = np.column_stack([CX + (R_TOP - 0.05) * np.cos(_th), CY + (R_TOP - 0.05) * np.sin(_th)])
TUR_TOP = float(np.min(DOME.under_z_world(_ring))) + 0.02
TUR_OPEN = [(300.0, window(width=0.30, height=0.60, sill=1.40)), (10.0, window(width=0.30, height=0.60, sill=1.40)),
            (255.0, window(width=0.30, height=0.55, sill=2.60)), (345.0, window(width=0.30, height=0.55, sill=2.60))]

LEAN_PORCH = dict(name="porch", W=plane_wall((WX - WH, DOOR_Y), (-1.0, 0.0)), width=1.8, depth=0.95, clear=2.32,
                  pitch_deg=20.0, overhang=0.25, side=0.15, covering="shingle", brace=(0.65, 0.75),
                  soft=dict(eave_sweep=0.08, sweep_len=0.5, wave=0.008, verge_flare=0.05, flare_len=0.45,
                            eave_lifts=[eave_lift(0.0, side=1, width=2.6, height=0.22, fade=1.0)]),
                  verge_board=dict(below=0.025, above=0.025), below=WING, below_lift_max=LIFT_MAX, below_roll=0.25,
                  seed=1931)


def turret_attrs(g):
    """the round-wall junction pieces read a RoundFrame's cone profile (g.PZ / g.PR / g.R_WALL) only to register the
    seal-probe junction; publish the turret's battered face on the PlanFrame so they can."""
    tb = float(np.tan(np.radians(DIM["tur_batter"])))
    g.R_WALL = DIM["tur_r"] - 0.14
    g.PZ = np.array([0.0, 12.0])
    g.PR = np.array([DIM["tur_r"], DIM["tur_r"] - 12.0 * tb])


def turret_abutment(g):
    """the wing's thatch runs into the turret wall (flaunched on the true line); a failure here is logged, not fatal."""
    try:
        wall_abutment(g, WING, center=(CX, CY), name="turret_abutment", min_clear=0.0)
    except Exception as e:  # noqa: BLE001
        log(f"  turret_abutment FAILED: {type(e).__name__}: {e}")


def steps():
    deck = lambda roof: (lambda P: roof.under_z_world(P))  # noqa: E731
    in_house = inside_box(X0 + 0.15, X1 - 0.15, -HALF + 0.15, HALF - 0.15, z_fn=deck(MAIN))
    in_wing = inside_box(WX - WH + 0.15, WX + WH - 0.15, WY0 + 0.15, -HALF + 0.15, z_fn=deck(WING))
    base = inside_round((DIM["stack_x"], 0.0), DIM["stack_r"], depth=0.12, batter_deg=DIM["stack_batter"])
    upper = inside_round((DIM["stack_x"], 0.0), 0.72, depth=0.12, batter_deg=1.5)
    in_tur = inside_round((CX, CY), DIM["tur_r"], depth=0.12, batter_deg=DIM["tur_batter"])
    in_drum = inside_round((CX, CY), DIM["tur_r"], depth=0.10, batter_deg=DIM["tur_batter"])
    at_round = inside_round((CX, CY), DIM["tur_r"], depth=-0.04, batter_deg=DIM["tur_batter"])

    def in_stack(P, margin=0.0):
        P = np.asarray(P, float)
        return np.where(P[:, 2] < DIM["shoulder_z"], base(P, margin), upper(P, margin))
    return [
        (set_entrance, dict(xy=(WX - WH, DOOR_Y))),
        turret_attrs,
        (path_stone_wall, dict(name="walls", path=PATH, top_fn=stone_top, openings=OPENINGS,
                               clip=any_clip(in_stack, in_tur), cfg=RUBBLE_LARGE,
                               hero_s=(DOOR_S - 2.5, DOOR_S + 2.5), seed=31)),
        (round_stone_body, dict(name="turret", center=(CX, CY), r_base=DIM["tur_r"], batter_deg=DIM["tur_batter"],
                                top=TUR_TOP, openings=TUR_OPEN, clip=in_wing, seed=61)),
    ] + [(path_timber_wall, dict(name=nm, path=pth, z0=Z_CAP - dz, top=Z_CAP + 0.26, top_fn=TOP, style="post_plank",
                                 gable_style="board_batten", rough=True, seed=331 + k))
         for k, (nm, pth, dz) in enumerate(GABLETS)] + [
        (linear_roof, dict(roof=MAIN, covering="thatch", seed=71, comb=False,
                           clip=any_clip(solid_clip(WING), DORMER.clip_main()),
                           deck_clip=any_clip(deck_clip(WING), DORMER.deck_clip_main()))),
        (linear_roof, dict(roof=WING, covering="thatch", seed=72, comb=False, clip=any_clip(solid_clip(MAIN), in_drum),
                           deck_clip=deck_clip(MAIN), rafter_skip=at_round, rafter_lift_max=LIFT_MAX)),
        (roof_valley, dict(main=MAIN, wing=WING, name="wing_valley", seed=5, ridge_cut=-0.35, ridge_bury=0.25,
                           ridge_bury_w=0.45,
                           corner_opts=dict(cut=0.08, past=0.02, roll=dict(ext=0.60, blend=0.42, grow=1.08,
                                                                          end_f=0.90)))),
        turret_abutment,
        (linear_roof, dict(roof=DOME, covering="thatch", seed=73, comb=False)),
        (gabled_dormer, dict(D=DORMER, seed=81)),
        (porch, LEAN_PORCH),
        (chimney, dict(name="chimney", center=(DIM["stack_x"], 0.0), r_base=DIM["stack_r"],
                       batter_deg=DIM["stack_batter"], roof=MAIN, clip=in_house, crown="pot", over_ridge=0.62, seed=51,
                       shoulder=dict(z=DIM["shoulder_z"], r_base=0.72, batter_deg=1.5, h=0.30),
                       pot=dict(r=0.19, h=0.46), abut=dict(ring_fillet=dict(out=0.22, h_up=0.18, bury=0.06,
                                                                           step_deg=1.5)))),
        (orient_open_islands, dict(parts=("_stones",))),
        (orient_closed_slabs, dict(parts=("_deck",))),
    ] + ([] if os.environ.get("ALEH_FAST") else
         [(hidden_cull, dict(min_polys=200, extra_views=reentrant_views(FOOT)))]) + [recenter]


def decals(g):
    with straight_span(MAIN, WING):
        composite_decals(g, moss_normal="slope", timber=True, timber_soot=False)
    chimney_decals(g)


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_roof_blocker",
                                       "_cap_collar", "_abutment"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))


def main():
    out = os.environ.get("ALEH_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="ALEH", collection="ALEH", building_id=BID, frame=PlanFrame,
        params=dict(footprint=FOOT, entrance=(WX - WH, DOOR_Y)),
        steps=steps(), decals=decals, decal_validate=DECAL_VALIDATE, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(dims=dict(DIM), datum=dict(ground_z=0.0, note="built on the plan, then recentred"))))


if __name__ == "__main__":
    main()
