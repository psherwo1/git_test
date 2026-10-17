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

## Round 5 (kit 1.10.2 proposal): dressed flashing over the covering envelope, eave cheek, clip check, lean cull

**Two NEW files only** (`components/tier_flashing.py`, `components/tier_cull.py`).  No existing kit file or
function was edited, so no other building can change and the HASH RULE re-run is not needed ("adding new files or
functions alone needs no re-run").  `tier_roof.roof_flashing` and `tier_finish.tier_hidden_cull` are unchanged and
still public; the v2 recipe now calls the new modules instead.

| module | public API | what it fixes (round-4 sign-off audit) |
|---|---|---|
| `tier_flashing.py` | `dressed_flashing(g, roof_name, body_name, up, apron, t, gap, step, nd, d_face, tuck, cheek, check, cheek_kw, sub, dd)` | The roof / through-body junction module.  The apron's underside follows the covering's real UPPER ENVELOPE (`covering_envelope`: a downward ray map of every mesh of the tier at 6 sub-stations x 5 mm, plus every piece vertex splatted into its cell, because a triangle's highest point is a vertex), max-filtered over each apron cell plus `gap` = 8 mm.  So the lead laps over every course and rises over every hip board that runs into the body, and no shingle, starter or hip stands through it.  No turned-down drip is cut into the courses (round 4's `drip=0.03` made 1,817 shingle vertices stand through the lead) and no covering is cut under the apron.  Works on octagonal, round and pyramid tiers (reads only the registry). Registers the body in the tier's `flashings` (seal probe). |
| | `eave_cheek(g, roof_name, body_name, ok, step, d_out, t, tuck, pad, reach, lip_pad)` | Where a body passes through a tier's OVERHANG (outside the supporting wall line, inside the lip + fascia): a lead cheek plate 6 cm off the body face with top, bottom and end returns tucked into the wall, from 3 cm under the lowest tier member that meets the face (fascia, soffit, deck lap, rafters) to the covering top at the open eave end, or to the base surface where the apron covers the top.  The eave members now butt into a cheek instead of dying square into the masonry (k03 / k04 / k06).  Called by `dressed_flashing(cheek=True)` whenever the body leaves the roof (open flashing runs).  Name `..._flashing_cheek`, so the hidden cull never targets it. |
| | `flashing_clip_check(g, roof_name, ob, fail=True)` + `FlashingClipError` | **KIT CHECK** (sibling of `seal_probe`): BVH overlap of the flashing against every other mesh of its tier; any intersecting triangle pair fails the build, naming the object, the pair count and a world point.  Run by `dressed_flashing(check=True)` on every junction.  Proof: on the first draft (ray map only, no vertex splat) it failed with 3 pairs on `HALL_skirt1_shingles` at (2.84, -1.17, 5.64), a thin shingle spike between ray samples; with the vertex splat all four junctions give 0 pairs. |
| `tier_cull.py` | `tier_hidden_cull_lean(g, max_views=40, skip=(), extra_targets=(), procs=None, seal=True, seal_kw=None)`, `cap_views(P, n, must)` | Build time (art bible 8): cuts the cull WORK instead of adding workers.  Same targets, building views and per-object facing selection as `tier_hidden_cull`, but each object is ray-tested against at most `max_views` building viewpoints (door close-up views always kept, the rest a deterministic farthest-point subset, so the kept views still surround the object at every height), plus the review tool's own viewpoints that `core.visibility_cull` always adds.  A hidden polygon's cost is proportional to the views it is tested against; on v2 the large wrapped objects drop from 109 + 77 to 40 + 77 views.  `skip` leaves named objects untested.  Then zero-face objects are dropped and `seal_probe.through_seal_probe` runs, as before. |


## Round 6 (kit 1.10.3 proposal): dressed flashing laid ON the course, closed run ends, self and lift checks

Only `components/tier_flashing.py` changed (my own round-5 file, not yet merged into the 1.10.1 reference).  It is
imported by no other building and no other kit module (grep over `buildings/` and `kit/`: only
`build_v2_tiered_hall.py`), so no other building's geometry can change and the HASH RULE re-run was not needed.
Every new parameter is optional; `dress="max"` rebuilds the round-5 profile.

| module | change |
|---|---|
| `tier_flashing.dressed_flashing(dress="tight", taper=3, min_apron=0.05, max_lift=0.05, max_foot=0.05, butt=0.015, butt_clear=0.03, lift_aim=0.03)` | **Dressed onto the course (round-5 director must-fix 1).** The round-5 apron took the envelope maximum over each radial cell and then over +-2 stations, so on a falling roof it floated 8-13 cm (median) over the courses. Now (`_dress_tight`) every apron vertex starts on its OWN station's envelope and one minimal-norm pass lifts only the corners of the split triangles that a covering sample stands over, so the lead rises over a hip or a lifted shingle only where it is. The envelope is guarded by a 3 x 3 sample dilation (8 mm x 5 mm), not the cell / +-2-station maximum. The apron ends ON the course it laps: it stops `butt_clear` short of the first course butt found over the station's span (staggered butts would otherwise hold the sheet up), never overhangs the lip, and the drip edge turns down to 3 mm over the course; stations whose drip still stands more than `lift_aim` over the course beyond are pulled in (<= 4 passes). |
| | **Closed run ends (must-fix 2).** The sheet is now triangulated by `_tri_sweep` with one diagonal rule in (station, d) space, so the top and underside (which share their (station, d) vertices, with a flat foot) can never cross: 0 self-intersecting pairs, against 48 + 46 in round 5. Every open run tapers monotonically over its last `taper` stations to d_face + 0.03 m and closes with ONE planar end cap in the end station's radial plane (convex quads: head, upstand, foot, one per apron bay, drip triangle). The eave cheek (`eave_cheek(top_cap=...)`, new optional) stays 4 mm under the apron foot, so the turned-down lead laps over the cheek top. |
| `tier_flashing.flashing_clip_check(..., body_name, max_lift, foot, self_check=True, others=True, lift_foot_w=0.012)` | **Extended KIT CHECK.** Besides the tier: the flashing against ITSELF (`self_intersections`, non-adjacent pairs) and against the tier's other flashing pieces (cheeks); the LIFT test (`flashing_lift`): per 1-deg sector the outermost apron vertex, 1 cm out, rays down onto the covering; any sector over `max_lift` fails the build, named by angle and world point (the single-ray figure is logged too; the test uses the highest hit of a 1.2 cm footprint, so a ray that drops into the joint between two shingles is not counted as lift); and any station whose upstand foot stands more than `max_foot` over the local roof line. |
| `tier_flashing.flashing_lift`, `self_intersections`, `_runs`, `_tri_sweep`, `_dress_tight` | new helpers (above). |
| `tier_flashing.dressed_flashing(step=...)` | the eave cheek now inherits the apron's `step` (it reads the apron's stations). |


## Round 7 (kit 1.10.3 proposal, continued): cheek fitted to the masonry, straight run ends, normal lead thickness

Only `components/tier_flashing.py` changed (my own file, imported by no other building or kit module: grep over
`buildings/` and `kit/` finds only `build_v2_tiered_hall.py`), so the HASH RULE re-run is not needed.  Every new
parameter is an optional keyword.

| module | change |
|---|---|
| `tier_flashing.eave_cheek(fit=True, clear=0.004, d_block=0.07, apron_under=None)` | **The cheek no longer clips the rubble (v2 round-6 audit: 1,182-1,216 cheek / stone pairs across the plate face).** `fit=True` (default) ray-maps the real outer envelope of every masonry mesh round the body (`masonry_envelope`) and stands the plate `clear` + t + 8 mm off it (one offset per run, so the plate stays one straight lead face); the top and bottom returns end `clear` outside the outermost stone on their own line (also across the heights a sloping return passes between stations) instead of being tucked 3.5 cm through the rubble.  A station whose envelope stands more than `d_block` out (an engaged neighbour's stones at the re-entrant) is left out.  `apron_under=(Dk, U, ok)`: the top return stays under the apron's dressed underside out to the plate face.  `fit=False` gives the round-6 plate. |
| `tier_flashing.masonry_meshes(g, lo, hi)`, `masonry_envelope(g, body, ths, zs, sub, d_max, d_min, objs)` | new helpers: every declared body's meshes near a box; the wall-side sibling of `covering_envelope` (horizontal rays in towards the axis plus a vertex splat). |
| `tier_flashing.flashing_clip_check(..., tier=True, bodies=None, layer_tol=None)` | `bodies`: a list of masonry meshes the piece must not touch (any pair fails the build); `tier=False` skips the tier pool; `layer_tol`: **near-coincident layer test** (`near_layers`: non-adjacent faces whose centroid lies within layer_tol of another face) fails the build.  `dressed_flashing` now checks the cheek against `masonry_meshes` round it (and itself). |
| `tier_flashing.dressed_flashing(end_line=True, normal_t=6.0, lift_rays=True, passes=12, foot_cost=4.0, layer_tol=0.002, foot_d=None, adaptive=False, blunt_drip=False)` | `end_line`: the end station and the `taper` stations of every open run are ONE straight line from the upstand foot to the drip corner (`_end_lines`: the lowest line on or over every dressed vertex), so each run ends in one turned-down plate.  `normal_t`: the top stands t * sqrt(1 + slope^2) (capped) over the underside (`_slope_factor`), so a steep step never leaves two shells within a few mm (round 6: 47-74 faces per turret apron within 2 mm; now 0 / 8 / 3 / 1).  `lift_rays`: the drip pull-in loop measures each station's lift exactly as the gate does (`_drip_lift`) for up to `passes` passes; a station still over `lift_aim` at the shortest apron (a butt at its foot) is dressed on over that butt onto the next course, and goes back if that stands higher.  `foot_cost`: weighted minimal-norm lift in `_dress_tight(cost=)` (the foot corners lift less).  Experimental, off by default: `foot_d` (first apron vertex foot_d out), `adaptive` (half-step stations, every other dropped where not needed: too few dropped on v2's chunky covering, +37 k triangles), `blunt_drip` (a 6 mm drip face; more near layers, not less). |
| `tier_flashing._adaptive_keep`, `_end_lines`, `_drip_lift`, `_slope_factor`, `near_layers` | new helpers (above). |

**Not closed in round 7:** the 0.05 m kit lift / foot gates.  Measured on the delivered recipe (gate measure,
1.2 cm footprint): drip-edge lift max drum 0.030, tur_e 0.037, tur_nw 0.083, lantern 0.062 m; upstand foot max
drum 0.052, tur_e 0.066, tur_nw 0.097, lantern 0.053 m.  The recipe passes `max_lift=0.09, max_foot=0.10,
layer_tol=0.001` (round 6: 0.10 / 0.10 / none).  The foot outliers are on the turrets' upslope back gutter, where the
chunky shingle stack stands 6-10 cm over the deck right next to the wall.
