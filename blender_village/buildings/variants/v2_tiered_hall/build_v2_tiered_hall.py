"""v2_tiered_hall -- the tall tiered great hall of ref2 (centre), assembled ONLY from village_kit modules.

Run:  python build_v2_tiered_hall.py   -> v2_tiered_hall.blend + decal_anchors.json (next to this script)
      HALL_FAST=1 skips the hidden-geometry ray test (quick looks only); HALL_OUT=<path.blend> redirects the output.

The recipe is two tables and a step list.  BODIES declares the building's vertical bodies (components.tier_frame);
STEPS stacks kit modules on them by name:
  * a 10 m octagonal battered rubble hall (stone_body: straight facet runs, long-and-short dressed quoins) with a
    timber-framed door facing -Y and four windows (framed_openings), two engaged round stone turrets of different
    size on the E and NW facets (stone_body, clip_by -> one shared masonry joint with the hall, mortar lapped behind
    it), each closed by a dressed coping (coping_ledge);
  * tier 1: a deep bell-cast octagonal skirt (bell_tier 'skirt' on the polygon hall) pierced by the upper drum and
    both turrets, lead flashings round all three (roof_flashing);
  * an upper round rubble drum rising through the skirt (stone_body, below='skirt1') carrying tier 2, a ROUND
    bell-cast skirt (bell_tier 'skirt_steep' on a round body -> round_tier, plate and frieze at the drum face);
  * a board lantern belt through tier 2 (board_belt + roof_flashing), tier 3 a tall round witch-hat spire
    (bell_tier 'witch_hat' -> round_tier, 70 deg) with lead-hat collar and spike finial (tier_finial);
  * on each turret a board belt and its own round witch-hat spire and finial; the tall E turret carries its cone
    clear above skirt2's eave (every tier passes the kit's roof-to-roof clearance gate, >= 0.5 m, when it registers);
  * note 6 cull and note 11 decal anchors derived from the declared bodies (tier_finish); after the cull the kit's
    see-through probe (seal_probe) fires ~1 M exterior rays at every roof / through-body junction and fails the build
    on any ray that passes a covering to the sky or the interior (kit 1.7.3: every octagonal tier lays an eave deck
    lap over its wall line and overhang, every flashing apron is turned down into the courses).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.tier_frame import TierFrame, declare_bodies  # noqa: E402
from village_kit.components.stone_body import framed_openings, opening, stone_body  # noqa: E402
from village_kit.components.tier_roof import bell_tier, roof_flashing, tier_finial  # noqa: E402
from village_kit.components.board_belt import board_belt  # noqa: E402
from village_kit.components.tier_finish import tier_decals, tier_hidden_cull  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = KitParams(entrance=(0.0, -5.0), detail_rule=True, units="kit", seed_offset=0)

# ---- the bodies (plan angle 0 = +X, CCW; the principal entrance faces -Y)
BODIES = dict(
    hall=dict(sides=8, apothem=5.0, z0=-0.05, z1=3.50, batter_deg=2.0, corner_p=160.0),
    tur_e=dict(center=(5.45, 0.0), apothem=1.40, z0=-0.05, z1=8.40, batter_deg=1.0),   # cone clears skirt2
    tur_nw=dict(center=(-3.75, 3.75), apothem=1.10, z0=-0.05, z1=5.70, batter_deg=1.0),
    drum=dict(apothem=3.0, z0=4.80, z1=8.30),
    lantern=dict(apothem=1.45, z0=9.10, z1=12.40, kind="belt"),
    tur_e_belt=dict(center=(5.45, 0.0), apothem=1.22, z0=8.47, z1=9.45, kind="belt"),
    tur_nw_belt=dict(center=(-3.75, 3.75), apothem=0.94, z0=5.77, z1=6.62, kind="belt"),
)
DOOR = opening("door", 270, width=1.0, height=2.10)
WINDOWS = [opening("window", 225, 0.62, 0.78, sill=1.25), opening("window", 315, 0.62, 0.78, sill=1.25),
           opening("window", 180, 0.50, 0.66, sill=1.32), opening("window", 45, 0.50, 0.66, sill=1.32),
           opening("window", 90, 0.26, 0.72, sill=1.40, jamb=0.14)]

STEPS = [
    (declare_bodies, dict(bodies=BODIES)),
    (stone_body, dict(name="hall", openings=[DOOR] + WINDOWS, clip_by=("tur_e", "tur_nw"), seed=101)),
    (stone_body, dict(name="tur_e", clip_by=("hall",), coping=(8.40, 1.19), seed=131)),
    (stone_body, dict(name="tur_nw", clip_by=("hall",), coping=(5.70, 0.91), seed=151)),
    (framed_openings, dict(seed=808)),
    (bell_tier, dict(name="skirt1", on="hall", overhang=1.25, profile="skirt", through=("drum", "tur_e", "tur_nw"),
                     seed=303)),
    (stone_body, dict(name="drum", below="skirt1", seed=404)),
    (roof_flashing, dict(roof_name="skirt1", body_name="drum")),
    (roof_flashing, dict(roof_name="skirt1", body_name="tur_e")),
    (roof_flashing, dict(roof_name="skirt1", body_name="tur_nw")),
    (bell_tier, dict(name="skirt2", on="drum", overhang=0.80, profile="skirt_steep", through=("lantern",), seed=505)),
    (board_belt, dict(name="lantern", below="skirt2", seed=606)),
    (roof_flashing, dict(roof_name="skirt2", body_name="lantern")),
    (bell_tier, dict(name="cap", on="lantern", overhang=0.60, profile="witch_hat", seed=707)),
    (tier_finial, dict(name="cap", scale=1.2)),
    (board_belt, dict(name="tur_e_belt", seed=616)),
    (bell_tier, dict(name="tur_e_cap", on="tur_e_belt", overhang=0.45, profile="witch_hat", seed=717)),
    (tier_finial, dict(name="tur_e_cap", scale=0.8)),
    (board_belt, dict(name="tur_nw_belt", seed=626)),
    (bell_tier, dict(name="tur_nw_cap", on="tur_nw_belt", overhang=0.45, profile="witch_hat", seed=727)),
    (tier_finial, dict(name="tur_nw_cap", scale=0.7)),
    (tier_hidden_cull, {}),                                   # producer note 6 (HALL_FAST=1 skips)
]


def main():
    out = os.environ.get("HALL_OUT", os.path.join(HERE, "v2_tiered_hall.blend"))
    build_building(dict(
        prefix="HALL", collection="HALL", building_id="v2_tiered_hall", frame=TierFrame, params=KIT,
        steps=STEPS, decals=tier_decals, decal_validate=True, out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params=dict(KIT), bodies=BODIES),
    ))


if __name__ == "__main__":
    main()
