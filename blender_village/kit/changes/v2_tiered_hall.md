# v2_tiered_hall: kit changes (kit 1.7.0 proposal, the free tier-module family)

Builder: v2_tiered_hall variant, round 1 (2026-10-16).  **Only new files were added. No existing kit file was
edited**, so no existing function changed behaviour or signature and no hero re-run was needed (kit edit rules).

## Why

The keep family (`oct_frame` + its components) hard-codes one tier stack: hall apothem, collar at z 6.02, the
stone-cone profile table, a wing path that starts at x = -3.70, and a turret table in absolute heights.  It cannot
build a hall with a different tier count or turret placement.  These modules hold no building at all.  A recipe
declares its bodies and stacks modules on them by name, and every junction module finds the parts it joins through
the frame's registry.

## New modules (`kit/village_kit/components/`)

| module | public API | what it adds |
|---|---|---|
| `tier_frame.py` | `TierFrame(prefix, entrance, detail_rule, units, seed_offset)`, `Body(name, center, sides, apothem, z0, z1, batter_deg, rot_deg, corner_p, kind)`, `declare_bodies(g, bodies)`, `roof_support(roof, x, y)`, `roof_z(roof, x, y)` | A frame with no building in it, plus a registry of bodies (round or regular-polygon vertical prisms, any centre, height and batter) and roof tiers. Bodies provide `r_eff`, `point`, `dist`, `inside` and `facet_normal`. The frame activates itself as the `oct_frame.FR` proxy, so `oct_roof.build_cap`, `hewn` and the pooled pegs work outside the keep. |
| `stone_body.py` | `stone_body(g, name, openings, clip_by, below, seed, cfg, coping)`, `opening(kind, th_deg, width, height, sill, ...)`, `coping_ledge(g, name, z, r_in)`, `framed_openings(g, seed)`, `RUBBLE_CFG` | Coursed rubble on any declared body, through the keep's `stone_wall.round_stone_wall` / `layout_wall` and the ONE stone generator. Openings cut the courses, and the lintel and sill heights snap to the real course beds. `clip_by` gives one masonry joint between engaged bodies. `below` drops the stones under a roof covering. The module builds its own mortar body cut exactly round the openings and clip bodies. Optional dressed coping. `framed_openings` adds timber jambs, a lintel let into the course above, a stone sill with drip, a threshold, a plank leaf with strap hinges and pooled nail heads, mullioned windows with closed shutters, and a backing board behind each opening. |
| `tier_roof.py` | `bell_tier(g, name, on, overhang, profile, rise, through, p_top, rot_deg, n_raft, seed, saddles, ...)`, `tier_finial(g, name, scale, ...)`, `roof_flashing(g, roof_name, body_name, ...)`, `make_roof(...)`, `wall_head_band(...)`, `PROFILES` | An octagonal bell-cast tier seated on any body: polygon, round drum, board belt or turret. It solves the eave height from the body top and reuses `oct_roof.build_cap`. `through` drops every roof piece inside the bodies that rise through the tier. A closed frieze band follows the real soffit and closes the joint between the wall head and the eave. The profiles are `skirt`, `skirt_steep`, `cap` and `spire`. **`roof_flashing` is the junction module.** It places a lead upstand and apron along the true roof/body intersection, ending in closed caps where the body leaves the roof at the eave. |
| `board_belt.py` | `board_belt(g, name, below, seed, head_ring)` | A lantern belt or turret drum of SIZE_TABLE `board` units on a round body. It has a closed backing drum with a top closure, which is never a cull target, and a 16-piece head ring. With `below`, the boards start just under the roof covering they rise through. |
| `tier_finish.py` | `tier_hidden_cull(g)`, `tier_views(g)`, `tier_decals(g, seed)` | Producer note 6: `core.visibility_cull` with actor, eave, door and crane views derived from the declared bodies. Backings are never targets. `<PREFIX>_FAST=1` skips the cull. Producer note 11: anchors placed from what the recipe declared. Wall anchors take the body's macro normal and are re-cast onto the surface, then go through the kit's gate (`decal_validate=True`). |

## How a building uses them

`buildings/variants/v2_tiered_hall/build_v2_tiered_hall.py` is a BODIES table, two opening lists and a STEPS list
of `(module, kwargs)` passed to `assembly.build_building`.  A different building is a different table.  For
example, a round tower is `sides=0`, a 6-sided chapel is `sides=6`, and a second turret is one more body plus three
steps.

## Verification

- No existing kit file was touched, so the hero triangle counts cannot move. No hero re-runs were needed (rule:
  "Adding new files or functions alone does not need hero re-runs").
- v2_tiered_hall builds with these modules (see `director/log_variant_v2_tiered_hall.md` for the stats).

## Round 2 (kit 1.7.1 proposal): module-level junction fixes

Edited only the round-1 tier-family files (`tier_frame.py`, `stone_body.py`, `tier_roof.py`, `tier_finish.py`).
No hero imports any of them (grep: only `build_v2_tiered_hall.py` does), and every pre-existing kit module they call
(`stone_wall`, `cone`, `conical_roof`, `round_wall`, `tower_roof`, `finial`, `oct_roof`, `core`, `decals`) is used
unchanged, so no hero re-run was needed.  All new parameters are optional; the round-1 call signatures still work.

| module | change |
|---|---|
| `stone_body.stone_body` | **`joint_lap=0.06`**: each body's own mortar sheet now runs 6 cm past the face of every `clip_by` body (stones still stop exactly at it), so the two sheets cross behind the re-entrant joint and any gap shows mortar, never the hollow interior (ray probe along all four hall/turret joint bisectors, z 0.3-3.3 m: every ray hits stone or mortar within 1.2 cm of the joint line). **`quoins=True`** (polygon bodies): new `SurfMap` lays every facet as a straight run (piecewise-linear perimeter map, courses continuous round the corner, mortar cell edges on every corner) and `_poly_stone_wall` closes every corner with alternating long (0.40-0.52 m) / short (0.20-0.27 m) dressed corner stones from the one stone generator (`stone_rec` + `dress_irregular` + `lay_stones`), each spanning >= 0.18 m of courses; the stepped footing course runs round the corner. New object `<P>_<body>_quoins`. Round bodies are laid exactly as before. |
| `tier_roof.bell_tier` | **`sides=None`**: 0 (round) when `on` is a round body, 8 when it is a polygon; `sides=8` forces the old octagonal tier on a round body. New `round_tier` (kit component): the hut cone (`cone` / `conical_roof` rafters, battens, chunky shingle courses, under-laps), `tower_roof._roof_deck` / `_eave_closure` and `round_wall.wall_plate` on a `RoundFrame` sub-frame (as v1's `round_tower_roof`), moved onto the body centre. The round wall plate bears on the body's wall head at the body radius (a belt's head ring or a stone body's top course), the eave closure is the round frieze, the rafters bear on the plate (no brackets). `ROUND_PROFILES` maps the profile names to (pitch, bell-cast, bell length). Same interface: `through` / `p_top` cut the covering, the tier registers a `ConeRoof` (`zb`, `p_lip`, `c`, `rot`, `Pp`) so `roof_flashing`, `board_belt(below=)`, `stone_body(below=)` and `tier_decals` work unchanged. `tier_finial` on a round tier builds the hut lead-hat collar + spike finial (`finial.finial`), spike 0.95 m x `scale`. |
| `tier_frame.roof_support` | plan radius for a round tier (`roof.is_round`). |
| `tier_finish.tier_views` / `tier_hidden_cull` | build-time budget: two actor rings per ground body (count by circumference, 12-28), one deduplicated crane ring pair, 2 distances x 2 heights x 3 offsets per opening; each target is tested only against the views on its own side of the building (plus every view above 6 m) via `visibility_cull(extra_by_target=...)`. `closure`, `underlap` and `collar` joined the never-cull list (backings). |
| `tier_finish.tier_decals` | eave drips: a tier whose lip overhangs its body by <= 0.30 m streaks the wall under it; a deeper eave puts its `water_streak` where the drip lands, on a lower tier's shingles (ray down from just outside the lip), or nowhere when it lands on the ground. |
