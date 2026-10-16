# village_kit CHANGELOG

## Kit edit rules (all agents)

- You may ADD modules, functions, and optional parameters whose defaults keep the old behaviour.
- Never change the behaviour or the signature of an existing kit function that another building uses.
- After any kit edit:
  1. re-run every OTHER building script that imports `village_kit`;
  2. confirm it still builds without errors;
  3. confirm its triangle count is unchanged (within ±0.5 %);
  4. record the edit below, with the buildings you re-ran.

| Building | Imports village_kit since | Triangles at last check |
|---|---|---|
| wattle_roundhut | 1.0.0 (round 8) | 876,619 after 1.6.0 hut part (round 11; round 10: 837,924; round 9: 827,563; round 8: 744,105) |
| hilltop_keep | 1.1.0 (round 7) | 1,166,874 after 1.5.0 keep part (round 9; round 8: 1,159,180; round 7: 1,123,849; variant 1,025,777) |
| tower_windmill | 1.2.0 (round 7) | 1,146,243 (round 8, kit 1.4.0; round 7: 1,134,993, variant 865,123) |

---

## 1.6.0, hut part (2026-10-16): strict decal-anchor gate, crisp door-bay break, split-facet plinth stones, fine-relief gates (HUT builder, round 11)

Fixes the sign-off audit of hut round 10 (director 8.8).  Every change is a new function / constant or an optional
parameter whose default reproduces kit 1.5.0 exactly; only the hut passes the new options.

### New functions / constants

- **`anchor_validate.STRICT_R11`**, **`anchor_validate.strict_footprint(probe, pos, normal, up, size, surface, ...)`**
  and the private `_strict_place()`: the director's anchor inspection as a gate -- 3 x 3 rays at +-0.45 x size from
  15 cm in front, first hit of ANY mesh; >= 7 of 9 on the declared slot within 4 cm of the plane (every slot, shingles
  included); footprint-mean RAW face normal . anchor normal >= 0.97; wall slots (M_daub / M_timber*, generator
  |n.z| < 0.6) get |n.z| <= 0.15.  The normal is the footprint-mean normal (wall: z clamped), re-snapped; a failing
  anchor is retried over 13 small shifts (<= 12 cm) x 3 sizes (1.0 / 0.8 / 0.65), else dropped.
- **`components.daub.WALL_FINISH_R11` / `wall_finish_r11()`** and **`components.daub.door_break_r11(g)`**: the
  door-bay break in the patches' `_ragged_margin` language (8-25 cm runs <= 12 deg, 1-2 rod-row diagonal steps, no U
  notch, line tilted 1.5-3.5 deg), a slope-normalised (mitred) field so tab corners stay crisp, a steep 3 cm edge face
  ending on the snapped contour, coat 7.4 cm thick at the arris, no feathering.
- **`stones._split_scar()`**: a hand-split scar as a planar facet pocket (tilted floor + step / side / exit break
  planes; crisp plane-plane creases, no smooth window).

### New optional parameters (defaults = 1.5.0 behaviour)

- `anchor_validate.validate_anchors(..., strict=None)`; `_cast()` also returns `normal_raw`.
- `components.round_decals.round_building_decals(layout=4)`: one damp_rise per bay (width capped 0.12 m clear of each
  post flank), door-head soot on the lintel front clipped above the opening, patch-corner cracks starting 3 cm out,
  settlement cracks ending >= 5 cm under the plate, plaster / repair patches only >= 5 cm inside intact coat (daub
  field) with a strict footprint.
- `components.daub.clump_mesh(..., style=None)` ("slab": flat-fronted broken slab); wall_finish keys `door_break`,
  `door_edge_w`, `door_edge_T`, `clump_style` (w:depth 1.6-2.4, <= 1 clump at a corner), `ent_gate="feature"`
  (entrance dents / dabs kept whole or not at all by `g.detail.min_at(centre)`: no 0-1 cm fade band), `gate_fine`,
  `stone_style="split"`, `stone_scars_ent`.
- `stones.stone_skin(..., split=False, scar_keep_ent=None)`, `stones.plinth_kind_stone(..., split, scar_keep_ent)`,
  `components.plinth.plinth_stone(..., split, scar_keep_ent, dense=1.0)`; `build_plinth` (when `stone_style="split"`):
  no 1-1.4 cm skin lumps, entrance stones meshed 1.6x denser, flat bed (below z 0.5 cm no vertex > 1 cm proud of the
  face just above the ground).
- `stones.spall_stone(..., lump=0.0012, pit=0.0006)`, `stones.chink_stone(rng, half=None, min_relief=0.0)`;
  `components.doors` (when `gate_fine`): the cheek spalls' lumps / pits and the 9 mm step dish gated by
  `g.detail.min_at`; `components.plinth` chinking gated at the entrance threshold (1 cm).

### Other buildings re-run (to scratch, `KEEP_OUT` / `MILL_OUT`)

- **hilltop_keep:** 1,166,874 triangles = its 1.5.0 record; built without errors; 116 anchors (report-only gate).
- **tower_windmill:** 1,146,243 triangles = its record; built without errors; 106 anchors, audit 0 failing.
  (A first mill run on an intermediate edit dropped 20 anchors because `validate_anchors` re-binds the name `strict`
  per anchor; fixed by reading the option into `strict_cfg` -- the re-run above is on the final kit.)

---

## 1.5.0, keep part (2026-10-16): door walking-zone decal gate, tapered cap saddles, layered thatch, crisp entrance masonry (KEEP builder, round 9)

Fixes the sign-off audit of keep round 8 (director 8.5, audit ~8.0).  Every change is a new function or an optional
parameter whose default reproduces kit 1.4.0 exactly; only the keep passes the new options.

### New functions

- **`decal_gate.door_walk_zone(center, outward, along, half_width, depth=1.5, inset=0.35, z_max=0.6)`** and
  **`decal_gate.in_walk_zone(item, zones)`**: the trodden zone in front of a door (plan rectangle, door clear
  width / 2 + margin either side, from 0.35 m inside the threshold to 1.5 m out, up to 0.6 m high).
- **`components.thatch.tuft_skirt(acc, P, rng, ...)`**: the eave fringe as one ragged straw skirt under the roll
  (rooted inside the roll's underside, leaning 40 deg in under it, a chain of 3-7 cm tufts hanging 2.5-6 cm below a
  1.2 cm continuous butt): a dark ragged eave edge instead of pale pins / blades.
- **`components.thatch.tuft_droop(...)`**: short, thick, rounded drooping tufts (kept as an alternative; unused).
- **`components.oct_hall.footing_blocks(acc, S, mapfn, rng)`**: footing-course stones as split field stone (gridded
  blocks with 2-3 plumb-split planar facets stepped 2-4 cm and 4-12 deg apart, face yawed 5-10 deg off the wall
  line, 1-2 top-arris spalls 3-6 cm, 1.2-2.2 cm chamfers, no pillow dome).

### New optional parameters (defaults = 1.4.0 behaviour)

- `decal_gate.snap_anchors(..., walk_zones=None, walk_types=("lichen", "moss"))`: a lichen / moss anchor whose decal
  rectangle overlaps a walking zone is rejected.
- `components.oct_decals.oct_building_decals(g, ..., walk_gate=False)`: True moves the threshold / step lichen to
  the step ends (outside the walking width) and the N / NE footing tops, and gates both doors' walking zones.
- `geom.rbox_v(..., chamfer=False)`: True gives planar 45 deg chamfers (L1 corner offset) instead of round-overs.
- `stones.coursed_batch(..., chamfer=False, spalls=None, yaw=None, steps=None, nz_side=None)`: chamfered arrises,
  planar arris spalls, face yaw, stepped split facets with their own planes, extra side rows.
- `components.oct_roof.cap_shingles(..., hip_clip=None)`, `hip_saddles(..., w_fn=None, raise_frac=0.4)`,
  `build_cap(..., saddle_taper=None)`; `stone_cone.cone_cap(..., saddle_taper=None)`,
  `turret.side_turret(..., saddle_taper=None)`: tapered saddle boards (each <= max_frac of the facet width), 1.8-2.4
  cm thick, side 1 raised 0.2 t; shingles laid as whole units between the boards and clipped cleanly 1.5 cm under
  them, no unit with a visible butt under 4 cm.
- `components.thatch.thatch_wing_roof(..., layered=False)` (-> `build_wing_roof`, `thatch_courses(..., layered)`):
  ref1's layered thatch -- clumps 0.14-0.55 m (log-uniform) with joints pushed >= 30 % of a clump width off the course
  below, 0.8-1.4 cm flat crowns, 0.4-0.8 cm creases, ragged lobe butts (+-1-2 cm), 6 % slips; the first course's
  butt kept smooth and seated in the roll; course ends feathered out 0.14 m before the turret; short live remnants
  between dead stretches sunk whole; a smooth roll (0.45-0.9 m bundles bound 0.8-1.4 cm); the tuft skirt.
- `components.thatch.d_roll(..., calm_taper=False)`: smoothed station path (no folded sections at tight polyline
  corners), swelling / binding faded in the end tapers, the buried tail folded into the dome there (closed end cap).
- `components.thatch.mortar_fillet(..., bury=0.012)`, `flaunch_loop(..., bury=0.012)`,
  `build_wing_structure(..., band_bury=0.012)`, `thatch_junctions(..., band_bury=0.012)`: the band's buried back
  runs `bury` m into the stone (the keep uses 0.035).
- `components.oct_hall.oct_hall_walls(g, ..., crisp_entrance=False)` (-> `build_hall_masonry(..., crisp)`,
  `build_door_dressing(..., crisp)`): arched-door jamb and voussoir blocks with flat faces (dome <= 2 mm), true
  45 deg 1.0-1.5 cm chamfers and planar arris spalls; the footing course via `footing_blocks` (the hero rubble's
  random draws are unchanged: the footing stones' old draws are still made, into a scratch accumulator).

### Re-runs

All shared-module edits (geom, stones, decal_gate, oct_roof) were finished before these re-runs; the later edits
touched keep-family modules only (thatch, oct_hall).  Builds went to scratch (`MILL_OUT` / `HUT_OUT`), so the other
builders' deliverables were not overwritten.

- `tower_windmill`: builds without errors, 1,146,243 tris (record 1,146,243: identical).
- `wattle_roundhut`: builds without errors, 837,924 tris, identical to the hut builder's own round-10 file built at
  16:18 (837,924); the table's 827,563 predates the hut's own round-10 changes.
- `hilltop_keep` round 9: see the keep log (round 9 builder entry).

---

## 1.5.0, hut part (2026-10-16): ragged patch outlines, clinging clumps, plinth spalls, starter-course under-lap, footprint-normal anchor gate (HUT builder, round 10)

Fixes the sign-off audit of hut round 9 (director 8.6).  Every change is a new function / constant or an optional
parameter / opt-in switch whose default keeps the old build.

### New functions / constants

- **`components/daub.WALL_FINISH_R10`, `wall_finish_r10(**kw)`**: `WALL_FINISH_R9` plus `patch_style="r10"`,
  `edge_w`, `spall_w`, `rag`, `clumps`, `clump_n`, `clump_proud`, `clump_w`, `clump_h`, `stone_scars`.
- **`components/daub.fracture_patch_r10(g, c_s, c_z, h_s, h_z, seed, open_below=False)`**: the fallen-out patch
  outline: sides leaning 8-14 / 16-25 deg in opposite senses (2-3 segments each, +-9 deg), margins of sloping
  5-30 cm runs stepping 1-2 rod rows on 2-5.5 cm diagonal breaks (`_ragged_margin`, no up/down pair within 12 cm)
  and tilted 4-9 deg overall, principal corners under 100 deg chamfered with a broken 3-point cut (>= 2 per patch),
  2-3 conchoidal spall scallops (6-16 cm, 1.5-3 cm into the coat) on ~15-25 % of the perimeter.  `open_below`
  runs a `low` patch down to the stones.  Returns (polygon, spalls).
- **`components/daub.clump_mesh(rs, w, h, depth)`, `daub_clumps(g, acc, bay, field, store, s0, s1, wf)`**: 2-3 clinging
  clumps per break (3 in the door-bay band): faceted convex lumps 6-11 x 5-8.5 cm, 2.2-3.4 cm proud of the rod
  fronts, back bedded at the rod centre line (the rods run into them), rim at the fracture edge, preferably under
  the top margin.  Own random stream (8800 + bay).  `g.DAUB_CLUMPS` lists them.
- **`components/cone.AGE_R10`** = `AGE_R9` + `underlap_k0=True`.
- **`anchor_validate.footprint_normal(probe, pos, normal, up, size, tol, exclude_objects)`**: the surface normal
  averaged over a decal's 3 x 3 footprint.

### Optional parameters / opt-in switches (defaults = old behaviour)

- `daub.make_daub_fields` / `build_daub`: read `wall_finish["patch_style"] == "r10"` (outline above, +-5 mm
  mid-frequency rag, fracture-face width 1.5-5 cm varying round the patch and ~5.5 cm at the spalls, `g.PATCH_POLYS`
  / `g.PATCH_SPALLS` published) and `wall_finish["clumps"]`.  The door-bay break keeps its r9 profile.
- `conical_roof.build_shingles`: `cone_age["underlap_k0"]` puts the 8 cm under-lap strips under the side joints of
  the first course too (over the doubled starter); inner `underlap(..., wedge=)`.
- `stones.stone_skin(..., scar_keep=None)`, `stones.plinth_kind_stone(..., scar_keep=None)`,
  `plinth.plinth_stone(..., scar_keep=None)`; `plinth.build_plinth` reads `g.wall_finish["stone_scars"]`: flake scars at
  least `scar_keep` deep that note 11 would drop are kept as spalls deepened to the local threshold (2-2.5 cm, 1-1.25 cm
  in the entrance zone) and widened by sqrt(depth ratio) (<= 1.6x).  No random draw changes.
- `anchor_validate.validate_anchors(..., normal_fp_dot=None, fp_ntol=0.10, fp_skip_need=None, no_tops=None)`:
  `normal_fp_dot` judges each anchor's normal against the footprint-mean surface normal (keeps the generator's
  normal when it agrees, else takes the mean normal if that is self-consistent, else drops); `fp_skip_need` gives
  the shingle anchors (`fp_skip_surfaces`) a looser footprint test (>= N of 9 within `fp_ntol`); `no_tops` =
  {decal type: object-name substrings} it may not sit on (lichen on the trodden step).  The footprint failure
  message now lists what each footprint ray hit.
- `round_decals.round_building_decals(layout=3)`: collar soot on the cone's macro normal, 0.15 m below the drip,
  on the first spot whose face agrees (dot >= 0.9), never on the under-lap; the step lichen moved to the plinth
  weather top right of the door; patch-corner cracks from the sharpest convex corners of the actual outline; the
  settlement cracks 0.30 m off the posts with z +-8 cm.

### Verification

- `wattle_roundhut` round 10: 837,924 triangles, 7.3 % hidden, 10 slots, Mask complete, 93 anchors (gate applied),
  bbox unchanged; lintel sun-streak scan 26 -> 0 lit points.
- Other buildings re-run after the edits (to scratch, `KEEP_OUT` / `MILL_OUT`), both build without errors:
  - `tower_windmill`: **1,146,243** triangles = its 1.4.0 record; 106 anchors.
  - `hilltop_keep`: **1,160,238** (record 1,159,180, +0.09 %, within +-0.5 %).  The keep builder was editing its own
    1.5.0 modules concurrently; no hut option is on by default, so no keep code path changed through this edit.

---

## 1.4.0, mill part (2026-10-16): drum wall core, gated + audited decal anchors, entrance / prop-foot options (MILL builder, round 8)

Fixes the sign-off audit of mill round 7 (director 8.8): note-6 daylight through the drum masonry, note-11
implausible decal anchors, and the open round-6 entrance / ground-contact must-fixes.  Only drum-family modules
(used by the mill and its variant alone) and one new module are touched; every addition is a new function, a new
module, or an optional parameter / opt-in frame flag whose default keeps the old build.

### New modules / functions

- **`anchor_audit.py`** (new): `audit_anchors(da, probe, max_offset=0.015, min_dot=0.85, ...)` -- the director's
  test as a build-time check (ray from 0.25 m out along each anchor's -Z; first hit within +-1.5 cm, a front face
  with normal . anchor Z >= 0.85, `surface` == the material hit); `drop=True` removes failures.
- **`components/drum_wall.drum_wall_core(g, ...)`**: one continuous wall-core ring (`<PREFIX>_wall_core`,
  `M_mortar`) 6 mm behind the mortar skin on the skin's own z rows (footing ledge, raked foot, recessed band
  followed), z -0.05 to the cornice; cut exactly for the door, slit windows and arcade recesses (grid lines on every
  opening edge, arch heads closed by box-to-circle patches); bottom / top annuli to the interior radius and an
  inward inner face outside the interior's modelled arc (passage open).  ~11k triangles.
- **`components/drum_decals.drum_tower_decals_gated(g)`**, **`wheel_end_streaks(g, da)`**: the drum-tower anchors +
  4 water streaks on the outer blade ends, then `decal_gate.snap_anchors` (horizontal-radial / +Z macro normals),
  `anchor_validate.validate_anchors` (applied) and `anchor_audit.audit_anchors`; asserts 0 failures and 40-120.
- **`components/drum_door.threshold_two_stones(g, P_dr, rd)`**: the threshold as two straight dressed stones on
  their own chords with a joint (each front 2 facets), the worn dip across both.

### Optional parameters / opt-in switches (defaults = old behaviour)

- `drum_frame.arch_set(..., jamb_min_relief=None)`: separate note-11 threshold for the jamb blocks (0.035 drops
  their edge spalls with every random draw unchanged).
- Frame flag `g.ENTRANCE_R8` (default absent = False), read by `drum_door.arched_door_surround` (spall-free door
  jambs, two-stone threshold), `drum_door.build_door_and_interior` (passage vault and rear arch face wound toward
  the viewer) and `raking_props.raking_prop -> prop_foot(..., r8=False)` (single-stone pad: body pulled in to the
  top outline + 1 cm; chock plan skewed 4-6 deg with two 2-3 cm hewn top bevels; one 18 mm square-bar staple per
  side, 20-22 cm span, 13-18 mm proud, legs into the timber, instead of the flat-bar dogs).

### Verification

- `tower_windmill` round 8: 1,146,243 triangles, 13.3 % hidden, 10 slots, Mask complete, 106 anchors, 0 audit
  failures; bbox unchanged.
- **Other buildings re-run after the edits** (to scratch files, `HUT_OUT` / `KEEP_OUT`; neither imports a module
  changed here):
  - `wattle_roundhut`: builds without errors, **827,563 triangles**, 94 anchors.  This matches the round-9 hut
    count that the keep builder recorded after 1.3.0 (0.0 %).
  - `hilltop_keep`: builds without errors, **1,159,180 triangles** (1.3.0 keep-part record 1,159,180, 0.0 %).

---

## 1.3.0, hut part (2026-10-16): note-11 daub relief per vertex, rigid cone sag + under-lap, decal-anchor gate (HUT builder, round 9)

Fixes the sign-off audit of hut round 8 (director 8.4, `director/audit_wattle_roundhut_r8.md`, must-fix #1-#3).
The keep builder is adding its own 1.3.0 items in parallel (`decal_gate.py`, thatch / oct_roof / turret options);
nothing below touches those.  Reused from `director/partial_fix_wattle_roundhut_r9.patch`: the `surf(..., sag=)`
switch, the rigid per-shingle offset, the `wall_finish` frame key, the foot-bite limiter and the lump / dent ideas;
not reused: `fracture_patch_r9` / `stepped_margin` and the bite backing (untested, left for a later round).

### New modules

- **`anchor_validate.py`.** `validate_anchors(da, probe, ...)`: the decal-anchor gate.  Every anchor is snapped
  along -normal onto the surface under it (a ray from 5 cm outside; no surface within 5 cm -> dropped), must hit
  its declared slot (timber / weathered timber count as one family) and not a backing mesh (`exclude_objects`),
  keeps the generator's normal where the hit face agrees with it (dot >= 0.8; adze ridges and lumps do not tilt the
  decal), else takes the hit's outward normal, must be open for 15 cm along +normal (buried -> dropped), its 3 x 3
  footprint must be on the surface (shrunk to 0.75 once, else dropped; shingle anchors skip it), and same-type
  anchors closer than 0.25 m are thinned.  `footprint_ok(...)` is the footprint test on its own.

### Additions to existing modules (optional, defaults keep the old behaviour)

- **`assembly.build_building`.** Optional spec key `decal_validate` (True or a dict of `validate_anchors`
  keywords): the gate is APPLIED before the `DECAL_ANCHORS` collection and the json are written, and the json gets
  a `validation` block.  Without the key the gate only REPORTS in the build log (anchors, json and triangles
  unchanged), so every building can see how many of its anchors would fail.  The keep / mill can opt in with one
  spec line.
- **`decals.wall_scatter`.** Optional `accept=fn(hit, (w, h))` (default None = unchanged).
- **`components/frame.RoundFrame`.** Optional `wall_finish` dict (default `{}` = the 1.0.0 coat).
- **`components/daub`.** `WALL_FINISH_R9` / `wall_finish_r9()`.  With `wall_finish["daub_relief"]` the note-11
  entrance exception is applied PER VERTEX with `g.detail.min_at_v()`: inside the zone (3 m from the door, 0-2.5 m)
  the round-7 palm dents (same places, lifted to 1.0-1.5 cm) and every third round-7 hand dab (1.0-1.3 cm) are
  kept, fading out over the last 25 cm inside the zone boundary; every bay gets sparse 2.0-2.5 cm hand lumps
  (2-3 per m2, kept anywhere by the 2 cm rule); sag belly 1.1-1.5 cm; entrance bays on a 1.6 cm grid, the others
  2.5 cm.  `flakes=False` deletes the clinging flakes; `foot_bites=N` limits the splash bites to N round the hut
  (0-1 per bay, never adjacent, 20-40 x 2-4 cm).  `low_margin(..., shoulder=6)` is a new optional argument.
  Cracks stay decal anchors.
- **`components/cone`.** `surf(g, theta, s, sag=True)` / `surf_frame(..., sag=True)` (sag=False: without the
  age-pass sag).  `AGE_R9` (opt-in `cone_age` keys `rigid_sag`, `rigid_tilt_deg`, `underlap`, `max_joint`).
- **`components/conical_roof.build_shingles`.** With `rigid_sag` each shingle is laid on the unsagged surface and
  takes the sag as a RIGID offset (sag at its centre along the cone normal, tilt about its axis <= 1.5 deg), so
  the per-vertex shear no longer opens the side joints; `underlap` adds a 2 x 8 cm strip of covered shingle under
  every side joint of courses >= 1 (`<PREFIX>_roof_underlap`, 12 tris per strip, not a `round_hidden_cull`
  target, so never culled); `max_joint` caps side-joint gaps (1.5 cm).
- **`components/round_decals.round_building_decals`.** Optional `layout=2` (default 1 = unchanged): damp_rise /
  plinth-moss rings jittered (+-8 cm, +-6 deg) and kept clear of the low wattle patch, lintel-end streaks on the
  door-frame post fronts (x = +-0.97: the post fronts span |x| 0.91-1.13, so a 12 cm streak centred at 0.92 would
  hang off the inner edge), threshold lichen on the left door-post pad stone, plaster / repair patches balanced
  +X / -X and only where their footprint is on intact coat.

### Verification

- **wattle_roundhut round 9** (gate applied, `layout=2`): 827,563 triangles, 7.7 % hidden, 10 slots, Mask complete,
  94 anchors (103 placed: 5 footprint, 4 duplicate cracks dropped), every anchor within 4 mm of its declared slot,
  open, same-type spacing >= 0.33 m.  Seeded: two full builds gave the same 827,563 triangles and the same 94
  anchors by name and type (between them only the gate's normal rule changed).  Details in
  `director/log_wattle_roundhut.md` ("Round 9 — builder entry").
- **Other buildings re-run after the edits** (to scratch files, `KEEP_OUT` / `MILL_OUT`), twice because the keep
  and mill builders changed their own scripts / modules during this round:
  - `tower_windmill`, first run (before the mill's 1.4.0 part): builds without errors, **1,135,006 triangles**
    (record 1,134,993, +0.001 %), 107 anchors unchanged.  Second run on the final kit (hut 1.3.0 + keep 1.3.0 +
    mill 1.4.0): **1,146,243 triangles** = the mill's own 1.4.0 record (0.0 %), 106 anchors; the report-only hut
    gate passes all 106.
  - `hilltop_keep`, second run on the final kit: builds without errors, **1,159,180 triangles** = the keep's 1.3.0
    record (0.0 %), 113 anchors; the report-only hut gate passes all 113.  (The first run, 1,153,874, caught the
    keep builder's own edits half-way and is not a comparison.)

---

## 1.3.0, keep part (2026-10-16): decal plausibility gate, flat cap saddles, bound thatch, continuous flaunching (KEEP builder, round 8)

Recorded separately from the hut builder's concurrent 1.3.0 part (`anchor_validate.py`, the `decal_validate`
spec key, `decals.py` helper options); the keep did not touch `decals.py`, `assembly.py` or any shared module.

### New module

- **`decal_gate.py`.** `snap_anchors(da, probe, ...)`: producer note 11 plausibility gate (director keep r7 rule).
  Every anchor is ray-snapped to the first surface along its intended normal (`item["macro"]`, the wall / radial /
  slope normal a generator may record, else its own normal) and rejected if the face normal disagrees (< 0.85, so back
  faces / reversed shells fail), the hit is an interior / blocker mesh, the spot is enclosed (< 2 of 24 rays in a
  75 deg cone escape 12 m), something stands within 15 cm in front of it, or (via `anchor_validate.footprint_ok`
  when present) the decal rectangle leaves the surface at full, 0.75 or 0.55 size; nearby spots within 0.15 m are
  tried before an anchor is dropped; same-type anchors closer than 0.3 m are thinned. The anchor ends 4 mm off the
  face. `cast_raw(probe, ...)`: a ray cast reporting the face's own normal.

### Optional parameters on keep-family components (defaults = 1.1.0 behaviour; only the keep imports these)

- `components/oct_decals.oct_building_decals(g, seed, snap=True)`: macro normals on every anchor, the gate above,
  moss on the wing thatch N slope / N eave roll and the cushion top (rays from just above it), window-head soot
  0.38 m over the opening on the facet stone, plate checks moved onto the member's vertical face, wing-door soot
  below the bound roll. `snap=False` reproduces the 1.1.0 anchor set.
- `components/oct_roof`: `hip_saddles(roof, acc, mat, p_lo, p_hi, W, T, h_bed, ...)` (new: ONE continuous saddle pair
  per hip, rectangular section with 1 cm chamfers, bedded into pressed shingles); `cap_shingles(..., exposure=None,
  hip_bed=None)`; `build_cap(..., saddles=False, cap_exposure=None)`.
- `components/stone_cone.cone_cap(g, seed, saddles=False, cap_exposure=None)` and `build_main_cap_and_finial(...)`.
- `components/turret.side_turret(g, seed, saddles=False, cap_exposure=None, bulb_cushion=False, drum_backing=False)`
  (and `build_turret`); `corbel_cushion` reads an optional `spec["bulb"]` (crowned 3-6 cm upper stones with a
  6-10 cm rounded outer top arris on ~80 % of them); the drum backing is its own object
  `<P>_turret_drum_backing` (never a cull target).
- `components/thatch`: `thatch_wing_roof(g, seed, rng_seed, bundled=False)` (bound eave-roll bundles via the new
  `d_roll(..., bundles=...)`, 10-25 cm clumps crowned 2.5-4 cm with a wandering / slipped butt line via
  `thatch_courses(..., bundled=False)`, strand tufts via the new `tuft_bunches`, a closed 0.55 m roll-end taper);
  `ridge_comb(g, seed, dense=False)`; `thatch_junctions(g, seed, continuous_fillet=False)` (`flaunch_loop(...,
  mortar_only=False)`: one continuous flaunching band, no stepped plates).

### Verification

- `hilltop_keep`: 1,159,180 triangles (round 7: 1,123,849), 14.6 % hidden, 11 slots, Mask complete; 113 decal
  anchors, all passing the gate and an independent director-style audit (offset <= 1.5 cm, alignment >= 0.85, no
  interior hit, no same-type pair < 0.3 m).
- Other buildings re-run to scratch files (they import none of the changed modules):
  - `tower_windmill`: builds without errors, **1,135,006 triangles** (record 1,134,993, +0.001 %).
  - `wattle_roundhut`: builds without errors, 827,563 triangles, 94 anchors (gate applied). This differs from the
    744,105 record because of the hut builder's own concurrent round-9 / 1.3.0 hut-part changes (daub relief, cone
    sag, the hut's anchor gate); the hut imports none of the modules this entry changed (`decal_gate`, `oct_*`,
    `thatch`, `turret`, `stone_cone`), so the keep edits cannot move its count.
  - Keep variant (`KEEP_KIT_VARIANT=1`): 1,055,773 triangles (round 7: 1,025,777), 109 anchors.

---

## 1.2.0 (2026-10-16): the stone-drum tower family, tower windmill migrated (MILL builder, round 7)

### New modules (no existing module changed behaviour)

- **`tmplmesh.py`.** The mill's template-instanced mesh machinery: `tmpl_box` / `tmpl_rings` topologies with the
  buried / covered faces dropped, `rbox`, `sweep`, `lathe`, `profile_block`, `add_grid`, transforms, smooth noise,
  `hewn_beam` / `hewn_between` / `facet_shave` (note-11 `min_relief`, draws unchanged), and `BatchAcc` (N pieces per
  `add()`; palette slots via `palette.material`, box UVs, sharp-by-angle, degenerate / buried-face removal,
  `core.nanite_clean` + a < 1e-8 m2 polygon sweep, Mask through `mask.write_mask` with per-piece R / G); `mesh_tmpl`
  (a kit mesh such as `shingles.shingle_mesh` / `shake_mesh` as a batch template), `fill_acc` (a batch into a
  `core.Acc` so pooled variants go through `pools.Pools.mesh`), `tower_b` (Mask B for tall buildings).
- **`split_stones.py`.** The mill's vectorised split-stone language (`split_batch`, `SPLIT_STYLES`, `conchoidal`),
  with `min_relief` per stone (note 11: face skin, spalls and scoops below the threshold dropped, draws unchanged).
- **`components/`**: `drum_frame` (`DrumFrame`, helpers taking the frame first, `relief_min`, `drum_finish`,
  `drum_hidden_cull`), `drum_wall` (`round_stone_drum`, `blind_arcade`, `coursing` with wandering beds / pinch-outs,
  `follow_beds`, `Wall`), `drum_band` (`baluster_row` aged, `dentil_corbels`), `drum_door` (`arched_door`,
  `entrance_step`), `shake_apron`, `smock_tower`, `mill_cap`, `fan_wheel` (+ alias `wind_wheel`), `tail_vane`
  (`rear_tail_vane`), `raking_props`, `rotor_checks` (`rotor_clearance`), `drum_decals` (`drum_tower_decals`).

### Additions to existing modules (append-only)

- **`stones.py`.** At the end: imports the split styles and registers `split_rubble`, `split_footing`, `split_pin`,
  `split_dressed`, `split_hero`, `split_ashlar`, `split_flag` in `STYLES` (`make_stone("split_rubble", rng,
  half=...)`).  No existing style or function changed.
- **`shingles.py`.** At the end: SIZE_TABLE row `shingle_small` (the gablet hood over a windshaft, with its
  reason).  The mill cap now uses the shared chunky `shingle` unit and the apron the shared `shake_mesh`.
- **`README.md`.** Status line and a "Kit 1.2.0" section.

### Verification

- **Pure refactor.** Before any intentional change, the kit mill reproduced the phase-1 script exactly: all 236
  accumulated arrays (every part's vertices, faces and material indices, every pooled variant and every linked-
  duplicate matrix) identical, for the hero and for `MILL_KIT_VARIANT`.
- **Round 7 (note 11 on, ensemble roughening, chunky cap, kit shakes, cull):** 1,134,993 triangles, 12.1 % hidden,
  10 slots, Mask complete, 0 needle / 0 zero-area polygons, 107 decal anchors; variant 865,123 triangles, 13.2 %
  hidden, 108 anchors.  Deterministic: a second build gave the same triangle count and an identical
  `decal_anchors.json`.
- **Other buildings re-run after the 1.2.0 edits** (to scratch files):
  - `wattle_roundhut`: builds without errors, **744,105 triangles** (record 744,105, 0.0 %).
  - `hilltop_keep`: builds without errors, **1,123,849 triangles** (1.1.0 record 1,123,849, 0.0 %).
- `__init__.__version__` was left for the kit architect to bump (it still reads 1.0.0).

---

## 1.1.0 (2026-10-16): the tiered octagonal family, hilltop keep migrated (KEEP builder, round 7)

### New modules

- **`geom.py`.** Vectorised primitives from the keep: `rbox_v` (many rounded / chamfered boxes at once from
  per-instance axis rows `ax4` / `ax5` / `axn` / `axr`), `inst_faces`, `obox`, `beam`, `sweep`, `prof_rect`,
  `prof_circle`, `lathe_rz`; 2-D helpers (`rot2`, `rounded_outline`, `inside_poly`, `catmull_closed`, `smooth_wave`,
  `softplus`, `box_sum`, `runs_of`); the keep's noise (`n1`, `fbm90`, `vnoise90` on `core.Noise(90210)`); the strict
  hygiene hook `strict_clean` (clip at -5 cm, `core.nanite_clean`, 5e-8 m2 zero-area, outward normals, mesh
  tessellation re-pass, sharp edges re-applied after the clean-up, per-island Mask R / G); `Acc(name)` and
  `finalize(acc, coll, smooth_deg, recalc, clip_z)`.
- **`components/oct_frame.py`.** `OctFrame(Building)`: the frame / dimension table of a tiered octagonal hall
  building (`PARAMS`), `derive()` / `set()`, `OctRoof`, the envelope functions, `min_relief(P)` (note 11), pooled
  part helpers `get_pool` / `place` over `g.pools`.
- **`components/stone_wall.py`.** Coursed rubble on any parametric wall surface: `layout_wall`, `fill_voids`,
  `polygonize`, `rough_footing`, `dress_irregular`, `lay_stones` / `lay_poly_stones` (make_stone + mapping + per-stone
  note-11 threshold), `mortar_sheet`, `round_stone_wall`.
- **`components/oct_hall.py`** (`oct_hall_walls`, `oct_hall_frame`, `door_threshold`), **`plank_doors.py`**
  (`arched_door`, `plank_door`, `door_spec`, `plank_leaf`, `strap_hinge`, `make_pintle`), **`windows.py`**
  (`hall_windows`, `annex_window`, `window_spec`), **`oct_roof.py`** (`skirt_roof`, `build_cap`, `cap_shingles`,
  `covering_boards`, `sarking_deck`, `hip_boards`, `eave_structure`), **`stone_cone.py`** (`shake_collar`,
  `stone_cone`, `lantern`, `cone_cap`), **`turret.py`** (`side_turret`, `corbel_cushion`), **`annex.py`**
  (`annex_walls`), **`thatch.py`** (`thatch_wing_roof`, `ridge_comb`, `thatch_junctions`, `d_roll`, `tuft_fringe`,
  `mortar_fillet`, `stepped_flashing`), **`hewn.py`** (`hewn_square`, `peg`, `nail_heads` over the kit's pooled
  `timber.make_peg` / `make_nail_head`), **`oct_cull.py`** (`oct_hidden_cull`), **`oct_decals.py`**
  (`oct_building_decals`).

### Additions to existing modules (append-only; no existing function changed its signature or default behaviour)

- **`core.py`.** `Acc.build_mesh`: `hygiene` may now be a callable hook `hygiene(me)` run at the same point as
  `nanite_clean` (after validate, before the Mask).  `hygiene=True` still runs `nanite_clean`; `False` nothing.
- **`stones.py`.** Styles `coursed` (`coursed_batch`: a whole batch of coursed rubble / dressed blocks in surface
  coordinates) and `coursed_poly` (`poly_rubble_stone`: one hero stone from its polygonal outline), `stone_outline`.
  Both take `min_relief` (scalar or per stone) without changing the random draws.
- **`shingles.py`.** SIZE_TABLE rows `skirt_board`, `collar_shake`, `comb_shake`, `hip_board` (each with its reason);
  `riven_shakes` (the keep's riven collar shakes, vectorised, note-11 aware).
- **`components/finial.py`.** The "turned" style: `TURNED_PROFILE`, `turned_finial(acc, base, scale, lean_deg,
  lean_dir)`, `lead_hat(acc, cx, cy, z_apex, r0, h0, cover=...)` (fits the drip and cone over the covering under it).
  `finial(g, style)` and `FINIAL_STYLES` are unchanged.
- **`README.md`.** Status line and a "Kit 1.1.0" section.

### Verification

- **Pure refactor.** With `units="phase1"`, `detail_rule=False` and no cull, the kit keep matched a phase-1 build
  object by object: 52 of 55 unique meshes vertex-identical (vertex / triangle count, bounds, coordinate sum); the
  skirt boards and the two cap coverings within 4 vertices (clean-up order).  Pegs and nails changed on purpose (kit
  pools).
- **Round 7 (`units="kit"`, note 11 on):** 1,123,849 triangles, 14.1 % hidden, 11 slots, Mask complete, 0 needle /
  0 zero-area faces, 104 decal anchors.  Variant: 1,025,777 triangles, 14.9 % hidden, 107 anchors.
- **Other buildings re-run after the 1.1.0 edits:**
  - `wattle_roundhut` (HUT_OUT to a scratch file): builds without errors, **744,105 triangles** (round-8 record
    744,105, 0.0 %), 105 anchors.
  - `tower_windmill` (MILL_OUT to a scratch file; its migration to the kit is in progress by its own builder):
    builds without errors at **1,134,997 triangles** and 107 decal anchors (16:20).  There is no earlier
    kit-based triangle record to compare with yet; the only 1.1.0 change to code the mill calls is the `Acc` hygiene
    dispatch, which is unchanged for `hygiene=True` / `False`, so 1,134,997 is the mill's own number on this kit.

---

## 1.0.0 (2026-10-16): kit created, roundhut migrated (KIT ARCHITECT)

### New modules

- **`core.py`.** Based on the hut's proven numpy machinery:
  - noise, primitives, `open_tube`, 2-D polygon helpers, and the `Acc` accumulator with per-piece Mask R / G;
  - from the keep: Nanite hygiene (`nanite_clean`, `sliver_report`), the windmill's sliver test, and
    `visibility_cull`;
  - new: `DetailRule` (producer note 11), `review_views`, `review_cameras`, `ring_views`, `stable_seed`, `rng`,
    `Noise(seed)`, and the scene and save helpers.
- **`palette.py`.** The 15-slot palette. This is the only module that creates materials.
- **`mask.py`.** The one `Mask` writer. It replaces the hut's `Acc` writer, the keep's `write_mask` and the mill's
  `set_mask`.
  - The values are now stored raw (`color_srgb`), as the keep and mill already did. The phase-1 hut wrote them
    through a linear→sRGB conversion.
- **`pools.py`.** Shared-mesh variant pools and linked duplicates.
- **`stones.py`.** One generator, `make_stone(style, ...)`.
  - The hut's generators: facet / field / plinth / pad / spall / boulder / shell / box.
  - New styles: `rubble`, `dressed`, `voussoir` and `chink`.
  - `min_relief` / `fine_scale` / `spall_scale` implement note 11.
- **`shingles.py`.**
  - `SIZE_TABLE`, the village roofing scale. The shared unit is the chunky 0.35–0.55 m shingle. `shingle_apex`
    (0.40 m target) is a documented exception.
  - The hut's 16 shingle variants and `shingle_mesh`.
  - New: `shake_mesh`, `board_mesh`, `course_widths`, `units_per_course`.
- **`decals.py`.**
  - `DecalAnchors`, which builds the `DECAL_ANCHORS` collection and exports `decal_anchors.json`.
  - `SurfaceProbe`.
  - Placement helpers: `base_ring`, `tops`, `below_points`, `above_opening`, `opening_corners`, `wall_scatter`.
- **`assembly.py`.** The `Building` context, `KitParams` (the kit_set convention) and `build_building(spec)`.
- **`components/`.**
  - `frame` (`RoundFrame`, `round_hidden_cull`), `cone`, `conical_roof`, `plinth`, `daub`, `wattle`,
    `round_wall`, `finial`, `doors`, `timber`, `interior`, `round_decals`.
  - All of these are hut phase-1 code. Its module globals became the explicit frame `g`, and every hard-coded
    radius-dependent number was derived from the frame.

### Verification

- **Before the intentional round-8 changes**, the kit-based hut was compared with the signed-off round-7 build:
  all 123 objects were bit-identical (vertex positions and matrices hashed at 1e-6), with 1,309,222 triangles.
- **Then these changes were applied:**
  - Producer note 11. The sub-2 cm relief is dropped (1 cm stays in the entrance zone).
  - Ensemble age pass on the cone.
  - Nanite hygiene on every mesh.
  - Hidden-geometry cull.
  - Decal anchors.
- **Other buildings re-run:** none. No other building imports the kit yet.

### Round-8 results for wattle_roundhut on 1.0.0

| | Hero | `HUT_KIT_VARIANT` |
|---|---|---|
| Triangles | 744,105 | 662,300 |
| est_hidden_pct | 7.7 % | 6.6 % |
| Material slots | 10 | 10 |
| Mask missing | none | none |
| Needle / zero-area faces | 0 / 0 | — |
| Decal anchors | 105 | 98 |
| Deterministic rebuild | 0 of 229 objects differ | — |

- The variant hut has a 2.9 m radius and a 2.60 m eave.
