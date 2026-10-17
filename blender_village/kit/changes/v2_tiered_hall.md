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

## Round 3 (kit 1.7.2 proposal): roof-to-roof junction rule, public round-roof parts, hygiene

Again only tier-family files plus one NEW file.  No hero imports any of them (grep: only `build_v2_tiered_hall.py`
imports `tier_roof` / `tier_frame` / `tier_finish` / `round_roof_parts`), so no hero re-run was needed.  All new
parameters are optional; every round-2 call signature still works.  (Started by the interrupted round-3 fixer at
20:17-20:25; reviewed, kept and finished in this round.)

| module | change |
|---|---|
| `tier_frame.roof_clearance` (new KIT CHECK) + `RoofClearanceError` + `TierFrame.roof_clear = 0.50` / `roof_stack = 0.20` | **The roof-to-roof junction rule.** Every tier, when it registers, is tested against every tier already registered on ANOTHER body. Where both coverings really span the same plan point (inside both lips, outside both p_top openings and outside the bodies rising through them), the clear height between the upper tier's base surface and the lower tier's, less a 0.20 m allowance for the shingle stack and soffit, must be >= 0.50 m; otherwise the build stops with `RoofClearanceError` naming both tiers, both bodies, the worst plan point and the clear height. `g.roof_clear = None` switches it off (diagnostics). Proven both ways this round: it raised on the first witch-hat trial (`tur_e_cap` over `skirt2`, 0.26 m) and passes the delivered recipe (0.70 m). |
| `tier_roof._register` | every `bell_tier` / `round_tier` registers through it, so the rule runs for both tier kinds. |
| `round_roof_parts.py` (NEW) | `roof_deck(f, r_in, gap, eave_s, t)` and `eave_closure(f, r_b, mat, n_az)`: the sarking deck + overhang slab and the eave-closure frieze of any round cone frame, promoted from `tower_roof`'s private `_roof_deck` / `_eave_closure` (same geometry as tower_roof at 19:55:57). `round_tier` now imports these instead of another builder's private helpers. `tower_roof` itself is untouched. |
| `tier_roof.drop_empty_meshes` (new) | removes zero-polygon mesh objects; called at the end of `round_tier`, `_round_finial` and `tier_finish.tier_hidden_cull` (a fully culled object). The round-2 empties `*_cap_purlin_rings` are gone. |
| `tier_roof.ROUND_PROFILES['witch_hat']` (new entry) | (70 deg, 20 deg bell, 0.45 m bell): ref2's tall witch hat. Eave-to-apex H/D about 1.2-1.4 on spires and turret cones, against 0.65-0.8 with `spire`. Existing entries unchanged. |
| `tier_roof.bell_tier` | `sides` other than 0-2 (round) or 8 now raises `ValueError` instead of silently building an octagonal tier (only v2 calls it). |

## Round 4 (kit 1.7.3 proposal): see-through junction probe, eave deck lap, turned-down flashing drip, cull budget

Only tier-family files (`tier_roof.py`, `tier_finish.py`) plus one NEW file (`seal_probe.py`).  No hero and no other
variant imports any of them (grep over `buildings/` and `kit/`: only `build_v2_tiered_hall.py` and the tier family),
and every pre-existing kit module they call (`oct_roof.sarking_deck`, `core.visibility_cull`, `tier_frame`) is used
unchanged with its public signature, so no hero re-run was needed.  All new parameters are optional keywords.

**Root cause of round 3's skirt1 / tur_nw slit.** `oct_roof.build_cap` starts the sarking deck about 0.08 m inside
the wall line, and the wall-head band stands at p_wall - 0.07 .. - 0.02, so a 3-5 mm plan crack runs between the
deck's eave edge and the band all round every octagonal tier.  Only the ring beam's top faces (in `_structure`)
backed it.  The hidden-geometry cull removes those faces where no view sees them, and beside the NW turret the
shingle joints above the crack happened to line up, so rays ran through the joint, the crack and the hollow hall
to the sky (k05, 119 director rays).  The NE-flank slit is the same family one step further out: there the turret
cuts the eave structure, so a ray through the overhang lands on the hall's wall face under the eave.

| module | change |
|---|---|
| `seal_probe.py` (NEW) `through_seal_probe(g, ring=(0, 0.6), el_deg=(10..80), n_az=24, density, n_dir, depth=0.6, min_incidence=10, backing=False, fail=True)` + `SealError` | **The see-through KIT CHECK** asked for in round 3.  For every tier and every body that rises through it (`through` plus every flashed body), seeded points on the covering's base surface in a 0-0.6 m annulus round the body, each hit by exterior rays from 24 azimuths x elevations 10-80 deg (n_dir per point, rays within 10 deg of grazing the local covering skipped).  A ray that passes its point and reaches nothing (sky), a point > 0.6 m under the tier (through the roof) or a point inside a body > 0.6 m below (hollow interior) is a leak; any leak raises `SealError` naming the tier, the body, the point, the ray direction and what it reached.  Optional `backing=True` pass with the covering removed (report only).  ~1 M rays, 12-20 s.  **Proof:** on round 3's delivered geometry it fails with 8 leaks, `skirt1` round `tur_nw` at (-4.29, 2.50, 3.95) and (-2.66, 4.65, 3.67) (the director's two slits); tur_e, drum and lantern 0. |
| `tier_roof.eave_deck_lap` (new) + `bell_tier(deck_lap=True)` | A continuous sarking strip (`oct_roof.sarking_deck`, fine 24 x 0.06 m cells so a `through` body cuts it at its face) under every octagonal tier's covering, from 0.22 m inside the wall line, lapping the main deck and the wall-head band, out over the whole overhang to 0.08 m inside the lip.  Name contains `deck`, so the cull never targets it.  `deck_lap=False` gives the kit 1.7.2 tier; a dict passes keywords.  Only octagonal tiers (round tiers already carry `round_roof_parts.roof_deck`, lip to apex). |
| `tier_roof.roof_flashing(drip=0.03)` | The apron's outer edge is turned down into the shingle courses to 0.03 m under the base surface (a lead drip dressed into the stack) instead of hovering 0.075 m over it, so no grazing ray runs under the apron.  `drip=None` gives the kit 1.7.2 profile. |
| `tier_finish.tier_hidden_cull(procs=None, seal=True, seal_kw=None)` + `cull_procs()` | **Cull budget (art bible 8):** ray-test workers default to one per physical core less one (logical CPUs / 2 - 1, clamped 3-6; 5 on the 6-core build machine, was a fixed 3).  The result does not depend on it (each polygon's test is independent).  **Seal:** after the cull (and in FAST builds) it runs `through_seal_probe`, so neither a module nor the cull can ship a see-through. |
