"""v6_barn (BARN) -- the village barn, round 2.  A declarative RECIPE: every piece is a village_kit module; the building
is dimensions + the order of the steps.

Run:  python -I build_v6_barn.py  -> v6_barn.blend + decal_anchors.json (next to this file)
      BARN_FAST=1 skips the hidden-geometry cull (quick looks only); BARN_OUT=<path.blend> writes elsewhere.

Built centred on the plan (x along the ridge, the front long side at y = Y0, ground Z = 0).
  barn   14.0 x 7.0 m: a low rubble plinth (path_stone_wall) under rough old post-and-plank walls with board-and-batten
         gables (path_timber_wall rough / bow), a steep 50 deg soft thatch roof (GableRoof ridge sag, swept eaves,
         flared verges, seated ridge roll) with one continuous ROLLED edge per slope (linear_roof verge_roll: the eave
         roll turns the corners and runs up both verges), a backed comb, and turned finials on lead hats at both gables
  entry  the round element (note 17; client direction 19:40): a round-arched timber CRUCK CART ENTRY in the middle of
         the front long side (cruck.cruck_frame on dry land, the harbour house's boat-arch module: jamb posts on
         dressed pad stones, a near-semicircular arch, tie beam, short blades and plank infill up to the thatch) with
         round-headed plank cart doors filling the arch (cruck.arched_doors), under the thatch EYELID: the eave
         sweeps up over it in one soft arch (GableRoof eave_lift) -- one organic composition
  doors  a man door with steps in the east gable, a hayloft door high in the west gable under a hoist beam, small
         shuttered windows and slits
"""
import os
import sys
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.composite import composite_decals, composite_hidden_cull, recenter, set_entrance  # noqa: E402
from village_kit.components.cruck import arched_doors, cruck_frame  # noqa: E402
from village_kit.components.linear_roof import GableRoof, eave_lift, linear_roof  # noqa: E402
from village_kit.components.openings import door, window  # noqa: E402
from village_kit.components.plan_frame import PlanFrame  # noqa: E402
from village_kit.components.rubble_walls import RUBBLE_LARGE, path_stone_wall  # noqa: E402
from village_kit.components.timber_walls import hoist_beam, loft_door, path_timber_wall, roof_top_fn  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BID = "v6_barn"

# ---- the ONE dimension table ----------------------------------------------------------------------------------
DIM = KitParams(half=3.5, x0=-7.0, x1=7.0, plinth=0.35, plate=3.0, wall_z=3.10, pitch=50.0,
                cart_x=0.0, clear=4.0, spring=1.90, arch_t=0.26, z_tie=3.52, frame_half=2.30, end=1.90,
                lift_w=10.0, lift_h=1.55, lift_fade=3.0)
HALF = DIM["half"]
X0, X1, Y0, Y1 = DIM["x0"], DIM["x1"], -HALF, HALF
XE, XW = DIM["cart_x"] + DIM["end"], DIM["cart_x"] - DIM["end"]    # the front runs end inside the cruck's posts
ROOF = GableRoof(x0=X0, x1=X1, half=HALF, wall_z=DIM["wall_z"], pitch_deg=DIM["pitch"], overhang=0.55,
                 verge=(0.45, 0.45), origin=(0.0, 0.0), thick=0.34, name="barn_roof", ridge_sag=0.30, eave_sag=0.05,
                 eave_sweep=0.22, sweep_len=1.2, verge_flare=0.24, flare_len=1.8, wave=0.03, wave_seed=61, ridge_seat=True,
                 eave_lifts=[eave_lift(DIM["cart_x"], side=-1, width=DIM["lift_w"], height=DIM["lift_h"],
                                       fade=DIM["lift_fade"])])
PAD = DIM["clear"] / 2 + 0.03 - 0.02           # the plinth runs 2 cm into the cruck's pad stones

# ---- plan: one open path round the barn from the entry's east post to its west post (interior on the left) -----
PATH = [(XE, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0), (XW, Y0)]
PLINTH = [(DIM["cart_x"] + PAD, Y0)] + PATH[1:-1] + [(DIM["cart_x"] - PAD, Y0)]
L0, LW, LL = X1 - XE, 2 * HALF, X1 - X0
S = dict(SE=lambda x: x - XE, E=lambda y: L0 + (y - Y0), N=lambda x: L0 + LW + (X1 - x),
         W=lambda y: L0 + LW + LL + (Y1 - y), SW=lambda x: L0 + 2 * LW + LL + (x - X0))
SLIT = window(width=0.24, height=0.62, sill=1.30, shutters=False)
OPENINGS = [(S["SE"](4.4), window(width=0.50, height=0.55, sill=1.10)),
            (S["SW"](-4.4), window(width=0.50, height=0.55, sill=1.10)),
            (S["E"](Y0 + 2.2), door(width=1.0, height=2.05, steps_to=0.0)),
            (S["E"](Y0 + 5.0), SLIT), (S["N"](-4.4), SLIT), (S["N"](0.0), SLIT), (S["N"](4.4), SLIT),
            (S["W"](Y0 + HALF), loft_door(width=1.20, height=1.70, sill=2.63)), (S["W"](Y0 + 1.6), SLIT)]
ROOF_TOP = roof_top_fn(ROOF)


def wall_top(x, y):
    """the walls' heads: 2 cm into the soft roof deck; over the cruck frame's width (front wall) they stop at the
    tie beam's bearing, where the frame's plank infill takes over (as the harbour house's piers)."""
    z = ROOF_TOP(x, y)
    if y < Y0 + 0.30 and abs(x - DIM["cart_x"]) < DIM["frame_half"] + 0.02:
        return min(z, DIM["z_tie"])
    return z


def steps():
    return [
        (set_entrance, dict(xy=(DIM["cart_x"], Y0))),
        (path_stone_wall, dict(name="plinth", path=PLINTH, top=DIM["plinth"], cfg=RUBBLE_LARGE, seed=31)),
        (path_timber_wall, dict(name="walls", path=PATH, z0=DIM["plinth"], top=DIM["plate"], top_fn=wall_top,
                                style="post_plank", openings=OPENINGS, rough=True, bow=0.03, seed=303)),
        (cruck_frame, dict(name="cart_entry", O=(DIM["cart_x"], Y0, 0.0), t=(1.0, 0.0, 0.0), n=(0.0, -1.0, 0.0),
                           half=DIM["frame_half"], top_fn=ROOF_TOP, z_pier=DIM["z_tie"], clear=DIM["clear"],
                           spring=DIM["spring"], tie=0.26, member_w=(-0.28, 0.02), post=0.26, arch_t=DIM["arch_t"],
                           blade=0.22, collar_at=0.45, collar=0.14, braces=False, king_strut=False, seed=901)),
        (arched_doors, dict(name="cart_doors", seed=911)),
        (linear_roof, dict(roof=ROOF, covering="thatch", seed=71, ridge_caps=True, verge_apex=True,
                           apex_finial="turned", verge_roll=True, comb_step=0.75, comb_backing=True,
                           rafter_lift_max=0.08)),
        (hoist_beam, dict(name="hoist", at=(X0, 0.0), out=(-1.0, 0.0), z=6.30)),
    ] + ([] if os.environ.get("BARN_FAST") else [(composite_hidden_cull, dict(min_polys=200))]) + [recenter]


DECAL_VALIDATE = dict(reach=0.06, min_sep=0.3, clear=0.15, walk_zones="da",
                      exclude_objects=("_blocker", "_deck", "_mortar", "_reveals", "_backing", "_roof_blocker",
                                       "_cap_collar"),
                      normal_fp_dot=0.85, fp_ntol=0.12, fp_skip_need=6,      # round 2: v3's gate for stepped
                      fp_skip_surfaces=("M_roof_shingle", "M_thatch"))      # thatch / shingle courses (moss)


def main():
    out = os.environ.get("BARN_OUT", os.path.join(HERE, BID + ".blend"))
    build_building(dict(
        prefix="BARN", collection="BARN", building_id=BID, frame=PlanFrame,
        params=dict(footprint=(X0, X1, Y0, Y1), entrance=(DIM["cart_x"], Y0)),
        steps=steps(), decals=partial(composite_decals, moss_normal="slope", timber=True, timber_soot=False),
        decal_validate=DECAL_VALIDATE, out=out, decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(dims=dict(DIM), datum=dict(ground_z=0.0, note="built centred on the plan"))))


if __name__ == "__main__":
    main()
