"""Stone-and-timber tower windmill (MILL) -- a declarative assembly on the shared village kit (phase 2, round 7).

Run:  /opt/bpyenv/bin/python build_tower_windmill.py
          -> tower_windmill.blend + decal_anchors.json (next to this script)
      MILL_KIT_VARIANT=1 /opt/bpyenv/bin/python build_tower_windmill.py
          -> kit_variant/tower_windmill_kit_variant.blend + kit_variant/decal_anchors.json
             (the kit test: a smaller drum, a shorter tower, 12 blades -- the same components, other numbers)

The mill is the signed-off phase-1 mill (round 6, ref1 mill) rebuilt from village_kit components:
  * battered rubble drum (components.drum_wall): footing course, coursed split rubble, balustrade band, blind
    arcade of 10 round-headed recesses, dentil corbels and moulded cornice; arched door with the plank leaf ajar,
    slit windows, the built-in door step (producer note 10: no ground dressing)
  * split-shake apron, octagonal boarded smock tower with a 0.55 deg lean, hipped bell-cast shingled cap with a
    hood over the windshaft neck
  * the 16-blade annular fan wheel on four hewn arms (client correction: no lattice sails)
  * the fixed tail vane on a doubled rear boom behind the wheel (client correction), braced from a king post
  * three raking props on the -X side; NO sloping buttress (client correction 2: that was terrain)
Shared kit modules: palette (slots), mask (the Mask writer), pools (linked duplicates), split_stones (registered in
stones.STYLES), shingles (SIZE_TABLE), tmplmesh (template-instanced pieces), decals (producer note 11).
All randomness is seeded; the build is deterministic.  Dimensions live in ONE table, KIT (kit_set convention).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kit"))

from village_kit.assembly import KitParams, build_building  # noqa: E402
from village_kit.components.drum_frame import DrumFrame, drum_finish, drum_hidden_cull  # noqa: E402
from village_kit.components.drum_wall import round_stone_drum  # noqa: E402
from village_kit.components.drum_door import entrance_step  # noqa: E402
from village_kit.components.smock_tower import smock_tower  # noqa: E402
from village_kit.components.shake_apron import shake_apron  # noqa: E402
from village_kit.components.mill_cap import mill_cap  # noqa: E402
from village_kit.components.fan_wheel import fan_wheel  # noqa: E402
from village_kit.components.tail_vane import rear_tail_vane  # noqa: E402
from village_kit.components.raking_props import raking_props  # noqa: E402
from village_kit.components.drum_decals import drum_tower_decals  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# the mill's dimension table: one parameter dict per component (components document every key)
KIT = KitParams(
    drum=dict(r_base=2.60, r_top=2.45, height=4.62, zones=dict(band=(2.55, 2.65, 2.82, 2.92)), windows=(70, -130),
              door=dict(width=1.05, spring=1.65, reveal=0.30),
              arcade=dict(n=10, clear_w=0.72, clear_h=1.08, z_sill=2.92, az0=18.0)),
    step=dict(),
    tower=dict(af_bottom=3.10, af_top=1.90, z0=5.95, z1=11.45),
    apron=dict(r_eave=3.17, z_eave=4.62, r_top=1.60, z_top=6.00, courses=3),
    cap=dict(length=2.76, width=2.56, rise=1.18, ridge_len=1.0, yaw=21.0),
    wheel=dict(r_in=1.35, r_rim=3.20, r_tip=3.90, n_blades=16, pitch=13.0, hub_d=1.95),
    tail=dict(),
    props=dict(),
)
# MILL_KIT_VARIANT: a different mill from the same components -- drum r 2.0 m with 8 arches, tower 4.0 m tall,
# 12 blades, its own props and tail
MILL_KIT_VARIANT = dict(
    drum=dict(r_base=2.00, r_top=1.88, height=4.20, zones=dict(band=(2.25, 2.35, 2.52, 2.62)), windows=(65, -125),
              door=dict(width=1.0, spring=1.62, reveal=0.30),
              arcade=dict(n=8, clear_w=0.66, clear_h=0.95, z_sill=2.62, az0=22.5), seed="kit"),
    step=dict(),
    tower=dict(af_bottom=2.70, af_top=1.90, z0=5.30, z1=9.30, seed="kit"),
    apron=dict(r_eave=2.50, z_eave=4.20, r_top=1.42, z_top=5.35, courses=3, seed="kit"),
    cap=dict(length=2.60, width=2.40, rise=1.05, ridge_len=0.9, yaw=21.0, seed="kit"),
    wheel=dict(r_in=1.20, r_rim=2.80, r_tip=3.40, n_blades=12, pitch=14.0, hub_d=1.85, seed="kit"),
    tail=dict(boom_end=-5.6, vane_s0=3.4, vane_length=2.1, seed="kit"),
    props=dict(props="variant"),
)


def kit_set(**kw):
    """publish component parameters to the mill's dimension table (unknown keys raise)."""
    KIT.set(**kw)


def variant_props(g):
    """the variant's prop set, attached under its (lower) collar."""
    from village_kit.components.drum_frame import TZ
    zc = g.Z_COLLAR - 0.11
    return ((6, 0.32, zc, (-5.2, -1.0)), (6, -0.32, zc, (-5.0, 0.8)), (6, 0.58, float(TZ(g, 7.30)), (-5.0, -2.6)))


def _props_step(g, props=None, seed=None):
    raking_props(g, variant_props(g) if props == "variant" else props, seed=seed)


def _dump_parts(g):
    """debug: dump every part's accumulated geometry (refactor verification against the phase-1 build)."""
    path = os.environ.get("MILL_DUMP_PARTS")
    if not path:
        return
    import numpy as np
    D = {}
    for p in g.batch + list(g.pool_parts.values()):
        if not p.V:
            continue
        D[p.name + "|V"] = np.concatenate(p.V)
        D[p.name + "|Q"] = np.concatenate(p.Q) if p.Q else np.zeros((0, 4), int)
        D[p.name + "|T"] = np.concatenate(p.Tr) if p.Tr else np.zeros((0, 3), int)
        D[p.name + "|M"] = np.concatenate(p.QM + p.TM) if (p.QM or p.TM) else np.zeros(0, int)
    for (name, key, M, leaned) in g.placements:
        k = "PL|" + key + "|" + str(leaned)
        D[k] = np.concatenate([D.get(k, np.zeros((0, 4, 4))), M[None]])
    np.savez_compressed(path, **D)


def main():
    variant = bool(os.environ.get("MILL_KIT_VARIANT"))
    if variant:
        kit_set(**MILL_KIT_VARIANT)
        out = os.path.join(HERE, "kit_variant", "tower_windmill_kit_variant.blend")
    else:
        out = os.path.join(HERE, "tower_windmill.blend")
    out = os.environ.get("MILL_OUT", out)
    build_building(dict(
        prefix="MILL", collection="MILL", building_id="tower_windmill" + ("_kit_variant" if variant else ""),
        frame=DrumFrame, params=dict(detail_rule=True),
        steps=[(round_stone_drum, KIT["drum"]),     # drum, band, arcade, cornice, door, windows
               (entrance_step, KIT["step"]),
               (smock_tower, KIT["tower"]),
               (shake_apron, KIT["apron"]),
               (mill_cap, KIT["cap"]),
               (fan_wheel, KIT["wheel"]),
               (rear_tail_vane, KIT["tail"]),
               (_props_step, KIT["props"]),
               _dump_parts,
               drum_finish,                        # parts -> objects, pools, clearance checks
               drum_hidden_cull],                  # producer note 6
        decals=drum_tower_decals,                  # producer note 11
        out=out,
        decal_json=os.path.join(os.path.dirname(out), "decal_anchors.json"),
        decal_meta=dict(kit_params={k: v for k, v in KIT.items()}),
    ))


if __name__ == "__main__":
    main()
