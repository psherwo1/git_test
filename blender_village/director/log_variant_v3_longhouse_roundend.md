# Variant log: v3_longhouse_roundend

## v3_longhouse_roundend round 1 — builder entry

**What it is.** The ref1 longhouse (lower middle): a long, low rubble longhouse under a layered thatch gable roof,
ending in a round rubble house under a conical chunky-shingle roof with a stone ball finial.  Principal door on the
long south (-Y) wall.  Graded on the note-12 modularity rubric; no surface-detail work was done (note 12).

- Build: `buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py` (declarative recipe, 88
  non-blank non-comment lines including its docstring) -> `v3_longhouse_roundend.blend` (13.0 MB, compressed) +
  `decal_anchors.json`.  Build time 13 min (the hidden-geometry ray test is most of it; `LONG_FAST=1` skips it for
  look-dev, 70 s).
- Renders: `renders/variants/v3_longhouse_roundend/round_01/` (hero, front, side, back, aerial, actor_closeup at
  24 samples + stats.json + hidden.json).

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 518,075 |
| est_hidden_pct | 14.9 % |
| material slots | 10 (M_stone, M_stone_dressed, M_mortar, M_timber, M_timber_weathered, M_roof_shingle, M_roof_shake, M_thatch, M_iron, M_lead) |
| mask_attribute_missing | none |
| bbox | 17.72 x 8.56 x 7.67 m (z -0.05 .. 7.62), plan bbox centred on the origin |
| objects | 59 (28 pooled peg instances) |
| decal anchors | 88 (101 placed, kit gate `anchor_validate.validate_anchors` applied: 11 footprint, 1 no surface, 1 occluded dropped) |

### Dimensions

- Round end: RoundFrame radius 3.50 (plate line), rubble face r 3.64 m at the ground, 2.5 deg batter, wall head 2.5 m
  under a pegged plate; cone 48 deg, eave radius 4.22 m, eave lip 2.30 m, chunky kit shingles with the AGE_R10 sag /
  under-lap, lead hat + stone ball finial to 7.62 m.  Two deep-set windows.
- Body: rubble walls 13.0 x 5.2 m to the outer faces (gable face to the round-end centre; 11 m of it outside the
  round end), deck at the faces 2.75 m, 40 deg thatch, 0.45 m eave overhang (eave lip underside 2.33 m over the door),
  0.40 m verge at the free gable.  Door 1.00 x 2.10 m clear on a 12 cm threshold slab; four windows (sills 1.25-1.30).

### The recipe (what is combined)

`RoundFrame` (dimension table) -> `set_entrance` -> `round_stone_body` (clip: inside the body) -> `wall_plate` ->
`path_stone_wall` along the U-shaped body plan (clip: inside the round wall; gable top from the roof spec) ->
`cone_roof` -> `ball_finial` -> `round_eave_fill` -> `linear_roof(GableRoof, covering="thatch", abut_cone=(0, 0))` ->
`cone_abutment` -> `composite_hidden_cull` -> `recenter`; decals `composite_decals` + the kit anchor gate.
The only numbers in the recipe are the plan, heights, pitches, opening positions and seeds.

### New kit modules (all new files; no existing kit file edited -> no hero re-run needed)

Recorded in `kit/changes/v3_longhouse_roundend.md`.
- `components/linear_roof.py`: `GableRoof` spec + `linear_roof` (deck backing, rafter tails, verge rafters, layered
  thatch with rounded bundle butts and a half-round eave nose, or kit chunky shingles; ridge roll + shake comb; clip
  for the end that dies into another body).
- `components/roof_junction.py`: `inside_cone`, `abutment_curve`, `cone_abutment` (the linear-roof-to-cone junction:
  exact junction line from eave soffit over the eave nose, slopes and ridge roll to the other side, closed lead
  flashing with both skirts dressed into the coverings), `round_eave_fill`.
- `components/wall_openings.py`: frame-placed door (threshold, posts, lintel, plank leaf via `plank_doors.plank_leaf`,
  straps) and window (sill with drip, deep frame + mullion, lintel, reveal, blocker room) for any masonry wall.
- `components/rubble_walls.py`: `path_stone_wall` (coursed rubble along any plan polyline: footing, solid long-and-short
  quoins at every outside corner, gable rake top, openings, junction clip, mortar body) and `round_stone_body`.
- `components/ball_finial.py`: lead hat + stone ball finial (the README's "ball" extension point).
- `components/composite.py`: cone roof without the hut daub closure, entrance zone, junction clips, footprint-loop
  hidden cull, recentre, composite decal anchors.

### Junctions (rubric axis 4) -- checked in all six views

- Thatch -> cone: clipped under the cone covering; continuous lead flashing along the whole junction line (soffit,
  nose, both slopes, over the ridge roll); no see-through in back / hero / aerial.
- Body walls -> round wall: body stones dropped >12 cm inside the round face, the body mortar body continues into it;
  the round wall is dropped inside the body.  The footing courses meet in a re-entrant corner.
- Round wall head -> cone: wall plate + eave fill up into the shingle stack.
- Gable wall -> roof: stones and mortar follow the rake 2 cm into the deck; verge rafter and thatch verge face.

### Known gaps

- The thatch reads as rounded layered bundles at mid-shot but is fairly regular from the back / aerial; the ridge
  comb is small at review distance (ref1 shows a stronger crest).
- At the south / north eave corners where the thatch eave dies into the cone eave, the flashing end makes a small
  lead lump under the eave (closed, but not elegant).
- Straight walls have no batter (quoins are solid boxes); the round end has no timber posts in its wall (ref1 shows
  some) and no fringe under its eave.
- `cone_abutment` covers a linear roof meeting a CONE; a roof meeting a taller round WALL needs a cylinder variant.
- Determinism: every step is seeded (np.random default_rng / RandomState); a second full build was not compared
  bit for bit this round.

## v3_longhouse_roundend round 1 — score 7.8/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_01/`, plus `stats.json`, `hidden.json`
  and `decal_anchors.json` (88 anchors).
- The recipe and the six new kit modules.
- 17 director junction close-ups and 7 see-through checks (black clay against a red sky) in
  `renders/variants/v3_longhouse_roundend/round_01/director_extra/`.
- A second full build to scratch.

**Determinism and compliance (director-verified).** The rebuild matches the delivered file exactly: same geometry
hash (`381aeb20…`, 518,075 tris) and a byte-identical `decal_anchors.json`. Other checks all pass:
- every unique mesh has an identity transform;
- every mesh has a UV map;
- `Mask` is present on every mesh and is both the active and the render colour attribute;
- there are no zero-area faces;
- the collections are `LONG`, `LONG_kit_instances` and `DECAL_ANCHORS`.

The full build took 1017 s here, with director renders running at the same time; the builder reports 13 min.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.3 | It is unmistakably the ref1 longhouse with a round end: a low rubble body, a 48 deg cone and a ball finial, in the right plan arrangement. However, the "thatch" reads as rows of pillow tiles at thumbnail size, and the ridge crest is weak next to ref1. |
| 2 Proportion and actor scale | 8.8 | The door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is 2.33 m, sills are at 1.25-1.30 m and the round-end eave is at 2.30 m. The body is 13.0 x 5.2 m (about 10.5 m of exposed wall), which is in ref1's ratio to the 7.3 m round end. |
| 3 Construction logic | 8.4 | Walls sit on footings, there is a pegged wall plate on the round wall, rafter tails sit under the deck, and the gable wall follows the rake into the deck. The door has posts, a lintel and a threshold. The weak point is the eave crossing: both eaves are at about 2.3 m, the cone's eave shingles run into the thatch eave nose, and a crumpled lead mass hides the clash. |
| 4 Seams and junctions | 7.4 | The slope and ridge flashing is excellent: it follows the true intersection, with no gaps. The wall-to-wall joint is closed. But the flashing ends at both eaves crumple into faceted lead lumps that hang below the eave lines, 4.7 m from the door at eye level. The free gable verge shows a black barcode of slots along both rakes. Sky shows under the ball-finial lead hat, and there are sky pinholes under the cone overhang beside the junction (both ray-confirmed). |
| 5 Distinctness and reuse | 8.5 | It is a genuinely new building type. The recipe is 107 declarative lines, with six new reusable kit modules and no hero file edited. Points off: the thatch covering invents a second thatch language that does not match the kit's `thatch.py`. Several modules duplicate parallel-built ones (`stone_body`, `framed_openings`, `tier_hidden_cull`, `junctions.roof_tower_flashing`); this is for the producer's merge. |
| 6 Technical compliance | 8.5 | 518k tris, 14.9 % hidden (at the 15 % limit), 10 palette slots, no missing `Mask`, no ground dressing, 88 plausible decal anchors, and the bit-identical rebuild is confirmed. The build takes 13 min, over art bible §8's limit of about 10 min. |

**Verdict: 7.8/10, NOT PASSED (pass mark 8.2).** The kit test itself mostly works. GableRoof, the cone abutment
along the slopes and ridge, the polyline rubble wall and the round body combine from a short declarative recipe
into a convincing ref1 longhouse, and the rebuild is bit-identical. The grade is capped by the junction axis:
- the abutment's eave terminations crumple;
- the thatch verge has open slots;
- there are two see-through spots (under the finial hat, and under the cone overhang).

The thatch covering also needs to read as thatch. All the fixes are module-level, so every future building that
uses these modules gets them for free.

**Strengths**
- It is a genuinely new structure from a 107-line declarative recipe: a RoundFrame plus a GableRoof spec and
  ordered kit steps. No hero file was edited, and the rebuild is bit-identical.
- `GableRoof` is one spec object that the walls (`body_top`), the junction and the decals all read. Pitch, yaw,
  verge, covering and abutment are parameters, so it is properly reusable.
- The `cone_abutment` flashing on the slopes and over the ridge roll follows the analytic intersection cleanly.
  No gaps or clipping showed in the crane, back or ridge close-ups (j03, j04, j05, j17).
- `path_stone_wall` works on any polyline, with solid long-and-short quoins, a gable rake top tucked under the deck
  and junction clips. The gable wall and the verge rafter close with no sky (j11 red check).
- Actor scale is right everywhere, and the door, windows, threshold and sills are all module-built.
- Technically clean: palette, `Mask`, UVs, transforms, Nanite hygiene, pooled pegs, and decal anchors on plausible
  surfaces.

**Must-fix (round 2)**
1. **`roof_junction.cone_abutment`, eave ends.** These are on both sides at x ≈ 2.3, y ≈ ±3.1, z ≈ 2.2-2.5 m (after
   the recentre); see j01, j02, j06 and j17.
   - What is wrong: the 8-point flashing section is swept round the 90 deg soffit -> nose -> slope corners, and it
     crumples into a faceted lead lump that hangs below both eave lips. It is visible from the door approach and
     from the back.
   - What it should be: the swept flashing stops at the top of the thatch eave nose. Each end becomes a separate
     closed lead end-apron, folded down over the nose face and tucked under the cone's starter course. No part may
     sit below the cone eave lip (2.30 m), and the apron should be no more than about 0.35 m across. The soffit
     closure belongs to the deck and eave fill, not to the sweep.
   - Make it a `cone_abutment(end="apron")` option and use it by default, so every linear-roof-to-cone junction gets
     it.
2. **`linear_roof._thatch_courses`, free verge.** This is the west gable, both rakes, x ≈ -8.8; see j11.
   - What is wrong: the clump verge side faces leave an open wedge cavity between every two courses. They render as
     about 20 black slots per rake, from eye level at 5 m.
   - What it should be: one continuous closed verge face per rake, running from the deck underside to the covering
     top and following the course steps (or a continuous verge roll). The verge must read as a solid thatch edge,
     with no dark slots.
3. **`linear_roof` thatch covering: make it read as thatch, with LESS geometry, not more detail.**
   - What is wrong: the 0.20-0.48 m crowned clumps read as rows of clay tiles or slates in the hero, front, back and
     aerial views. They do not match the kit's existing thatch language (`thatch.py`, the keep's west wing) or ref1.
   - What it should be: continuous courses with drifting butt lines and only soft bundle undulation (crown ≤ 1 cm,
     clump runs of 1 m or more, or continuous). Reuse `thatch.py`'s eave roll (`d_roll`) and course approach where
     the geometry allows. A linear thatch roof and the keep wing must read as one material family at mid-shot.
4. **`ball_finial`, apex at z ≈ 6.4-6.6 m.** See j14 and `j14_ball_finial_cone_seethrough_red.png`.
   - What is wrong: sky is visible from crane height through the gap under the lead hat rim (ray-confirmed near
     (4.0, -0.1, 6.55)). The hat is also pitched at about 29 deg (`hat_drop` 0.34 on r 0.62), not the art bible's
     about 44 deg collar.
   - What it should be: hat pitch 44 deg (`hat_drop` ≈ r·tan 44 deg ≈ 0.60), with the drip fitted no more than 3 cm
     over the top shingle course, as `round_apex.turned_apex` already does, plus a closed apex blocker under the hat.
     No sky may pass under the hat from any crane view.
5. **`composite.cone_roof`, the round-end overhang.** This is at x ≈ 3.3-4.5, y ≈ -3.4 to -3.9, z ≈ 2.5-3.1 m,
   beside the junction; see `j10_round_eave_lookup_seethrough_red.png`.
   - What is wrong: there are pinholes of sky between the rafters, plate, battens, under-lap and shingles. The roof
     blocker starts at z = 2.91, so the overhang has no backing.
   - What it should be: a continuous sarking or soffit deck under the whole cone overhang (v1's
     `tower_roof.round_tower_roof` boarded soffit slab solves exactly this; reuse it). No eye-level ray may reach
     the sky through the eave.
6. **Build time, `composite.composite_hidden_cull`.**
   - What is wrong: the full build takes 13 min (17 min measured here under load), over the art bible §8 limit of
     about 10 min. `footprint_views` produces 953 viewpoints.
   - What it should be: a full build of 10 min or less on 4 shared cores, with est_hidden_pct still ≤ 15 %. For
     example, trim it to 2 loop distances x 3 heights + crane + door views, or ray-test only the large stone and
     shingle objects.

**Nice-to-have (not blocking)**
- The producer should merge the parallel duplicates into one kit API:
  - `rubble_walls.round_stone_body` with `stone_body.stone_body`;
  - `wall_openings` with `stone_body.opening` / `framed_openings`;
  - `composite_hidden_cull` with `tier_finish.tier_hidden_cull`;
  - `cone_abutment` with `junctions.roof_tower_flashing` / `tier_roof.roof_flashing`, as one junction family.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's strong crest; a silhouette change,
  not surface detail).
- In the recipe, `X_END` and the clip depth are hand-tuned (the body path runs 0.3 m into the round wall). A
  `path_to_round(center, r_face)` helper should derive the path end from the round body.
- A few clipped sliver stones remain near the body/round re-entrant joint at the wall head (j01, j07). The joint
  itself is an acceptable straight joint.
- Decals: add moss or debris anchors in the thatch-to-cone valley, and `water_streak` under the cone eave drip.
  `composite_decals` promises both, but none survived the gate. Move `lichen_003`/`004` off the threshold top
  (a walked surface).
- `cone_abutment`: a cylinder variant (roof into a taller round wall), as the builder noted.
- Optional later module parameters for ref1: timber posts in the round wall, and an eave fringe.
- Hidden is 14.9 %. Leave some margin after fixes 1-5 add backing.

## v3_longhouse_roundend round 2 — builder entry

All six must-fixes were made in the KIT MODULES (new functions and new keywords; the round-1 behaviour is still
available through the old keyword values). The recipe changed by one argument (`cone_roof(..., soffit_skip=in_body)`)
plus one decal-gate exclusion. No surface-detail work was done (note 12). Kit changes are recorded in
`kit/changes/v3_longhouse_roundend.md`. Only v3's own round-1 modules were edited. Grep confirms that no hero and no
other variant imports `linear_roof`, `roof_junction`, `ball_finial` or `composite`, so hero triangle counts cannot
move. `thatch.d_roll` is reused unchanged.

- Build: `buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py` (90 non-blank, non-comment lines
  including the docstring) -> `v3_longhouse_roundend.blend` (11.9 MB, compressed) + `decal_anchors.json` (89 anchors).
- Renders: `renders/variants/v3_longhouse_roundend/round_02/` (all six views at 24 samples, plus stats.json and
  hidden.json). Builder close-ups and red see-through checks are in `round_02/builder_checks/`.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 469,769 (round 1: 518,075) |
| est_hidden_pct | 12.9 % (round 1: 14.9 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m (z -0.05 .. 7.64), plan bbox centred on the origin |
| objects | 62 (28 pooled peg instances) |
| full build time | 9 min 24 s, measured with the CPU at 100 % load from other builders (round 1: 13 min) |

### Must-fixes

1. **`roof_junction.cone_abutment` eave ends -> `end="apron"` (new default).**
   - `abutment_curve(..., ends="crest")` makes the sweep run over the slopes and the ridge only. It stops 6 cm
     up-slope of the eave-roll crest.
   - The new `end_apron` builds each eave end as a separate closed lead apron lying on the roll's nose. It runs
     from just above the crest down the nose face. It is a band 0.20 m onto the thatch plus 0.12 m tucked under the
     cone's starter course (0.32 m across). The band is centred on the seam where the cone covering crosses the
     nose, and the seam line is smoothed.
   - Nothing sits below the cone eave lip: the apron's floor is g.Z_EAVE + 3 cm, and the roll's lowest point is
     about 2.36 m.
   - Checks: `builder_checks/apron_front`, `apron_w`, `s_eave_eye`, `n_eave_eye` and `actor_closeup` show no lumps
     under either eave.
   - Supporting module change: `linear_roof(..., abut_wall_in=0.10)`. A roof that abuts a cone is now dropped only
     where it is under the cone AND inside the round wall head. Under the cone's oversailing eave, the deck, eave
     roll and courses run on and die into the round wall. This closes the pocket the old soffit sweep used to hide,
     and leaves the soffit to the deck and the eave fill, as the review asked.
2. **Free verge -> `_verge_faces`.** Each free gable gets ONE tessellated closed polygon in the gable plane. It runs
   from the deck underside up to the upper envelope of the eave roll and of every course's end section, across both
   rakes and under the ridge roll. A foot strip runs back under the deck end. `verge` and `verge_red` show no slots
   and no sky.
3. **Thatch covering -> `linear_roof(..., thatch_style="courses")` (new default; `"clumps"` is round 1).**
   - Courses: each course is one continuous sheet per slope with a rounded butt. The butt line drifts by ±4.5 cm
     over 2-4 m. Courses are laid in bundle runs of 1.0-2.2 m, each with a ±1.8 cm set, at most 1.2 cm of lift and a
     soft crown of at most 9 mm.
   - Eave: the keep wing's eave-roll language. It is a D-section roll (`GableRoof.eave_roll`) swept with
     `thatch.d_roll`.
   - Result: fewer, wider units. The covering plus the roll is about 26k polygons, against the round-1 clumps
     (76k tris in the covering). In hero, back, aerial and `roof_mid` it reads as layered thatch courses, not tiles.
4. **`ball_finial`.**
   - The hat is pitched at 44 deg (`hat_drop = hat_r tan 44°` ≈ 0.60), with the apex set the way
     `round_apex.turned_apex` sets it. `finial.lead_hat` fits the drip over the top shingles with 2 cm clearance.
   - The new `apex_blocker` is a closed plug under the hat, 4 cm under the cone reference surface, out to
     r = 0.92 m (`LONG_apex_blocker`, backing).
   - `finial` and `finial_red` show no sky under the hat.
5. **`composite.cone_roof(..., soffit=True)` -> new `cone_soffit`.** This is v1's `tower_roof._roof_deck` closed
   boarded slab, limited to the overhang (top face, soffit face and eave edge) from 10 cm above the lip to 7.5 cm
   inside the plate line. The part inside the body is skipped. `s_soffit_up_red` and `s_eave_eye_red` show no sky
   through the round eave beside the junction.
6. **Build time -> `composite_hidden_cull(..., views="lean")`.**
   - Views: `LEAN_VIEWS` is 2 loop distances x 3 heights, 1 crane loop and 27 door views. Roof coverings
     (`ROOF_PARTS`) are ray-tested from `ROOF_VIEWS` only: no knee-height loop and no door views. That is 286
     viewpoints, against 953 in round 1.
   - Lighter roll: the eave roll is built without its buried back.
   - Result: 9 min 24 s under full shared load, with est_hidden 12.9 %.

### Known gaps

- I did not ray-test the hat drip gap per azimuth. `lead_hat` guarantees 2 cm clearance over every shingle vertex
  under the hat, but at one or two azimuths a shingle edge can show as a faint crease line on the hat in
  `builder_checks/finial`.
- Nice-to-haves were not done: the stronger ridge-comb crest, `path_to_round`, the decal valley moss, the cone
  cylinder variant and the duplicate-module merge.
- I did not compare a second full build bit for bit this round. Every step is seeded. The deliverable is the build
  made to scratch with the final code, copied in with its `decal_anchors.json`.

## v3_longhouse_roundend round 2 — score 8.1/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_02/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (89 anchors) and the builder's `builder_checks/`.
- The recipe, `kit/changes/v3_longhouse_roundend.md` and the round-2 module code (`roof_junction.end_apron`,
  `cone_abutment(end="apron")`, `linear_roof` courses / `_verge_faces` / `abut_wall_in`, `ball_finial.apex_blocker`,
  `composite.cone_soffit`, `LEAN_VIEWS`).
- 27 director junction close-ups, 11 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_02/director_extra/` (d01-d27): both eave crossings from west and
  east at eye level, both slopes from the crane, the ridge into the cone, both soffit crossings looking up,
  body wall into round wall (S and N), round wall head to cone eave, two round-eave look-ups, both gable verges, the
  verge/eave corner, the ridge end, the gable footing corner, the body eave look-up, the finial from four crane
  azimuths plus a clay close-up, the door, a round-end window, the ridge comb, a top-down junction and a back
  three-quarter.
- A second full build to scratch, compared with the delivered file.

**Determinism and compliance (director-verified).** The rebuild matches the delivered file exactly: same geometry
hash (`f14d1009…`, 469,769 tris) and a byte-identical `decal_anchors.json` (SHA-256 `4E359FB3…`). Every unique mesh
has an identity transform and a UV map; `Mask` is present on every mesh and is both the active and the render
colour attribute; there are no zero-area faces; the collections are `LONG`, `LONG_kit_instances` and
`DECAL_ANCHORS`; the 28 pegs share one mesh. Stats: 469,769 tris, est_hidden 12.9 %, 10 palette slots, nothing in
`mask_attribute_missing`, 62 objects, 11.9 MB. The rebuild took 678 s (11.3 min) here, with about ten other
builder processes on the CPU; the builder measured 9 min 24 s. That is at the art bible §8 limit (about 10 min) and
is not blocking.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | It is unmistakably the ref1 longhouse with a round end: a low rubble body, a 48 deg cone with a ball finial, and the thatch now reads as layered thatch courses (not tiles) in the hero, front, back and aerial views. The ridge crest is still weak next to ref1's strong comb. |
| 2 Proportion and actor scale | 8.8 | Unchanged and right: the door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is about 2.33 m, sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. The body-to-round-end ratio matches ref1. |
| 3 Construction logic | 8.3 | Walls sit on footings, the plate, rafters, deck and soffit carry the roofs, the finial has a hat and an apex plug, and the door and windows are module-built. The one illogical spot is the eave crossing: the cone's eave courses do not stop where the thatch eave roll is, they run on through it (must-fix 1). |
| 4 Seams and junctions | 7.9 | All four round-1 junction defects are fixed. There is no lead lump (d01, d02), the verge has no slots (d15/d16 red), there is no sky under the hat at any of four azimuths (d21) and none through the round eave (d13/d14 red); the slope and ridge flashing is still clean (d05-d07). One clear clipping defect remains at the key junction: at both eave crossings the cone's starter, under-lap and bottom shingle courses splay into a fan of 6-8 stacked plates with dark wedge gaps, crossing the thatch roll and hanging below the soffit (d03, d04, d08, d09). It is visible at eye level about 4.7 m from the door. There is also a dark open slot at both free-gable eave-roll ends (d15, d16) and shingle corners poke through the lead hat (d22). |
| 5 Distinctness and reuse | 8.6 | It is a genuinely new building type from a 90-line declarative recipe. All six fixes landed in kit modules as new keywords, the round-1 behaviour is still reachable, and the recipe changed by one argument. Points off as before: the parallel duplicate modules still await the producer's merge. |
| 6 Technical compliance | 8.8 | The rebuild is bit-identical; 470k tris, 12.9 % hidden, 10 palette slots, `Mask` everywhere, no ground dressing and 89 plausible decal anchors. The build time is at the limit under shared load. Two anchors (`lichen_003`/`004`) still sit on the threshold's walked top. |

**Verdict: 8.1/10, NOT PASSED (pass mark 8.2), but close.** Round 2 is a clear step up (7.8 -> 8.1). Every round-1
must-fix was made at module level, and four of the five junction defects are gone. The thatch reads as thatch with
fewer triangles, and the rebuild is bit-identical. The grade is capped by the eave crossing, the junction the brief
names as the key test. The linear roof now yields to the cone, but the cone does not yield to the linear roof: its
covering is built with no knowledge of the body roof and runs through the thatch eave roll as a splayed stack of
shingles. This is one module-level fix in `cone_roof`, and every future round-end, tower-annex or turret-to-roof
junction gets it for free.

**Strengths**
- All six round-1 must-fixes were made in the kit modules as new keywords (`end="apron"`, `thatch_style="courses"`,
  `abut_wall_in`, `soffit=True`, `apex_blocker`, `views="lean"`), with the old behaviour still reachable. The recipe
  changed by a single argument, which is how a kit should evolve.
- `end_apron`: the eave ends are now neat closed lead aprons, and nothing hangs below the cone eave lip (d01, d02).
  The slope and ridge sweep still follows the analytic intersection with no gaps (d05-d07, d07 red).
- `_verge_faces`: one closed verge face per gable, with no slots and no sky from either diagonal (d15/d16 red).
- `cone_soffit` and `apex_blocker` close every see-through path (d13, d14 and d21 red). Eye-level rays find no sky
  through the round eave, the body eave (d20 red) or under the hat.
- The thatch reads as layered thatch courses with a D eave roll reused from `thatch.d_roll`: the same family as the
  keep wing, with 48k fewer triangles than round 1.
- Technically clean and bit-identical on a director rebuild (geometry hash `f14d1009…`, identical decal JSON).

**Must-fix (round 3)**
1. **`composite.cone_roof` / `conical_roof.build_shingles`: the cone covering at the eave crossing.** This is on
   both sides at x ≈ 2.0-2.6, y ≈ ±(2.9-3.4), z ≈ 2.25-2.70 m (after the recentre); see d03, d04, d08, d09 and the
   enlarged crops `crop_d03`, `crop_d04` and `crop_d08` in `director_extra/`.
   - What is wrong: the cone's starter course, under-lap and bottom 2-3 shingle courses are built round the full
     360 deg with no knowledge of the body roof. Where the cone eave crosses the thatch eave roll they run on through
     the roll. They show as a fan of 6-8 splayed plates with dark wedge gaps, crossing the roll and hanging
     diagonally below the soffit over the wall head, visible from the door approach.
   - What it should be: a reusable keep-out on the cone side, matching `linear_roof(abut_cone=...)`, for example
     `cone_roof(..., abut_roof=ROOF)` or `keep_out=fn`. It drops every cone covering unit (shingle, starter,
     under-lap) whose footprint lies below `ROOF.top_z + 2 cm` on the body side of the abutment line, and the
     battens and soffit there with them.
   - Result: the cone's eave courses end in a regular, closed course line that rests on the end apron. The apron's
     `w_in` tucks under the last remaining starter. No cone unit sits inside or under the thatch roll, and none
     below the cone eave lip.
   - Re-shoot d03, d04, d08 and d09, plus red twins.
2. **`linear_roof._eave_rolls` / `_verge_faces`: the eave-roll ends at the free gable.** This is at both corners,
   x ≈ -8.8, y ≈ ±3.0, z ≈ 2.30-2.55 m; see d15 (north end) and d16 (south end, `crop_d16`).
   - What is wrong: a dark open slot about 4-5 cm wide and 20 cm tall between the end of the D-roll and the verge
     face. It reads from each diagonal approach at eye level.
   - What it should be: a closed end cap on the roll, and the verge face's lower envelope extended over the roll's
     full D section, so the verge face and the roll end meet with no gap or dark slot.
3. **`ball_finial` / `finial.lead_hat` fit: shingles through the hat.** This is at the apex, z ≈ 6.4-6.6 m,
   r ≈ 0.3-0.5 m, two azimuths; see d22 (`crop_d22`).
   - What is wrong: two shingle corners pierce the 44 deg hat surface as dark creases. The 2 cm clearance is tested
     against shingle centres or butts, not against every corner after the age lift and rotation.
   - What it should be: no shingle geometry above the hat's underside. Test the clearance against every vertex of
     every unit under `hat_r` + 5 cm, or drop and shorten the units that fail. This is the same rule
     `round_apex.turned_apex` applies.

**Nice-to-have (not blocking)**
- Thatch courses: in the back three-quarter and the north crane views (d27, d06), thin bright hairlines run along
  several course butts where a lower course's buried tail surfaces through the course above in a drift trough.
  Clamp each tail at least 1 cm under the envelope of the course above.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's strong crest; open since round 1).
- Verge face: it now reads as a flat barge board. A soft rounded or stepped thatch edge on the same closed face
  would read more like ref1 at mid-shot (silhouette, not surface detail).
- Decals: move `DA_lichen_003`/`004` off the threshold top (a walked surface). Add the promised `water_streak`
  under the cone eave drip and moss in the thatch-to-cone valley.
- Producer merge and helpers, carried over from round 1: `path_to_round(center, r_face)`; one junction family
  (`cone_abutment` + `junctions.roof_tower_flashing` + `tier_roof.roof_flashing`); a cylinder variant of
  `cone_abutment`; merging `round_stone_body` / `stone_body` and `wall_openings` / `framed_openings`.
- Build time: 11.3 min measured here under heavy shared load. Keep the margin when the cone keep-out adds work.

## v3_longhouse_roundend round 3 — builder entry

All three must-fixes were made in v3's own KIT MODULES as new functions, methods and keywords (the round-2
behaviour stays reachable through the keyword defaults). The shared `conical_roof.py`, `finial.py` and `thatch.py`
were reused unchanged. Grep confirms that no hero and no other variant imports `linear_roof`, `roof_junction`,
`ball_finial` or `composite`, so no hero re-run was needed. No surface-detail work was done (note 12). Kit changes
are recorded in `kit/changes/v3_longhouse_roundend.md` (round 3 section).

- Recipe: `linear_roof` now runs before `cone_roof`, because the cone needs the roof's eave-roll section for its
  keep-out. Two arguments were added: `cone_roof(..., abut_roof=ROOF)` and `ball_finial(..., hat_seg=96, fit=True)`.
  The recipe is 91 non-blank, non-comment lines.
- Build: `v3_longhouse_roundend.blend` (12.0 MB, compressed) and `decal_anchors.json` (88 anchors). The full build
  took 7 min 59 s under shared load (round 2: 9 min 24 s).
- Renders: `renders/variants/v3_longhouse_roundend/round_03/` (all six views at 24 samples, plus `stats.json` and
  `hidden.json`). There are 23 builder close-ups in `round_03/builder_checks/`, 7 of them red see-through twins.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 476,893 (round 2: 469,769) |
| est_hidden_pct | 13.4 % (round 2: 12.9 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 62 (28 pooled peg instances) |

### Must-fixes

1. **The cone covering at the eave crossing → `composite.cone_keep_out` / `cone_roof(abut_roof=ROOF)`.**
   - This is the mirror of `linear_roof(abut_cone=...)`: the cone now yields to the roof.
   - The roof is described as a solid by new `GableRoof` methods: `section_loop`, `section_columns`, `keep_out`,
     `top_depth`, `eave_zone` and `under_soffit`. The solid is the deck, courses, D eave roll and ridge roll, in
     vertical columns, so everything under the roof counts as inside it too.
   - The new helpers `mesh_islands` and `drop_units` delete whole units (connected islands) and never cut a unit.
   - Rule "tuck" (the default) drops whole shingles, starters, under-laps and battens in these cases:
     - the unit lies wholly inside the roof solid;
     - any vertex is under the soffit or the roll belly;
     - any vertex is in the eave band (the eave roll);
     - any vertex is more than 15 cm under the roof top.
   - Rafter, purlin and soffit faces that lie wholly inside are dropped as well.
   - Removed polygons: 12,910 shingle, 1,040 starter, 780 under-lap, 132 batten, 673 rafter and 96 soffit.
   - Result: at both eaves the cone's courses end on whole units over the roll and its end apron. Nothing sits
     inside or under the roll, and nothing hangs below the soffit (`s_/n_eave_east_eye`, `s_/n_eave_close`,
     `s_/n_soffit_up`). The red twins show no sky.
   - On the slopes, a unit may still tuck a corner just under the thatch beside the flashing, as it did in round 2,
     which the director graded clean (`s_slope_crane` and its red twin).
2. **Free-gable eave-roll ends → `_eave_rolls(end_caps=True)` + `_verge_faces(roll_cover=0.012)`.**
   - The roll keeps its back over the last 0.10 m of each free end, so the end is a closed, rounded cap.
   - The verge face's eave end now covers the roll's whole D section, 1.2 cm inside the roll's outline.
   - `s_/n_verge_corner` show no slot, and their red twins show no sky.
3. **Hat fit → `ball_finial(fit=True)`: `hat_fit_units`, `fine_hat` and `hat_underside`.**
   - The round-2 "creases" were not shingles. An exact BVH overlap test found no shingle polygon crossing the hat's
     outer surface; every shingle vertex was at least 2.0 cm under it. What did pierce the 44 deg hat was the
     `conical_roof` rafter hub (r 0.39 m), at the two bulges of its wavy lathe.
   - `hat_fit_units` tests every vertex of every covering and structure unit within hat_r + 5 cm against the BUILT
     hat's actual profile. It drops the units that come through the hat and the units wholly under it; this round
     that was the hub, 120 polygons.
   - `fine_hat` re-lathes the same fitted hat from a smooth, finely subdivided profile.
   - `hat_underside` adds an 8 mm lead underside.
   - The worst clearance kept is 2.0 cm. BVH overlap on the delivered file: nothing crosses the hat's outer surface.
     The only contacts are the drip's closed bottom cap on the top course, and the finial socket seated in the hat
     top.
   - `finial_az020`, `finial_az110`, `finial_az200`, `finial_az290` and `finial_top` are clean.

### Known gaps

- Soffit and rafter faces are dropped only when every vertex is inside the keep-out, so that no sky path opens. One
  thin soffit-board edge and one cone rafter tail still show at each eave crossing (`n_soffit_up`, top centre).
- A few small dark notches remain beside the slope flashing where a unit was dropped (`actor_closeup`, above the
  junction).
- The end apron's `w_in` is not yet sized from the last remaining cone unit. It reads closed in the checks, but it
  is not adaptive.
- Nice-to-haves were not done: the stronger ridge-comb crest, `path_to_round`, the decal valley moss, moving the
  threshold lichen, and the course-tail hairlines.
- I did not make a second build to compare bit for bit. Every step is seeded.

## v3_longhouse_roundend round 3 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12).

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_03/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (88 anchors) and all 23 builder close-ups in `round_03/builder_checks/`.
- The recipe, `kit/changes/v3_longhouse_roundend.md` (round 3) and the round-3 module code
  (`composite.cone_roof(abut_roof=...)`, `cone_keep_out`, `drop_units`, `mesh_islands`, the new `GableRoof` solid
  methods, `_eave_rolls(end_caps=True)`, `_verge_faces(roll_cover=...)`, `ball_finial.hat_fit_units` / `fine_hat` /
  `hat_underside`).
- 33 director close-ups, 21 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_03/director_extra/` (d01-d30): both eave crossings from west and east
  at eye level and on a 100 mm lens, both soffit crossings looking up, both slopes from the crane, the ridge into the
  cone, a top-down, body wall into round wall (S and N), round wall head to cone eave, a round-eave look-up, both
  gable verge corners, the gable ridge end, the body eave over the door, the finial from four crane azimuths plus a
  close-up, the door, a round-end window, the gable footing corner, a back three-quarter, a mid-shot of the junction
  from the door approach, and 160 mm tele shots of both flashing ends (d28, d29) and the south soffit crossing (d30).
- A second full build to scratch, compared object by object with the delivered file.

**Determinism and compliance (director-verified).** The rebuild is geometry-identical: all 62 objects have the same
vertices (max difference 0.0) and the same 476,893 triangles, and `decal_anchors.json` is byte-identical (SHA-256
`8A6F98A6…`). The one difference is the face ORDER of `LONG_body_wall_stones` (same face set; this rebuild ran the
visibility cull single-process inside blender.exe, the builder's ran 4 processes). Every mesh has an identity
transform and a UV map, `Mask` is present and is both the active and the render colour attribute on every mesh,
and there are no zero-area faces. Stats: 476,893 tris, est_hidden 13.4 %, 10 palette slots, nothing in
`mask_attribute_missing`, 62 objects, 12.0 MB. The rebuild took 988 s here because the cull ran single-process;
the builder's 7 min 59 s with 4 processes is inside the art bible §8 limit.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: it is unmistakably the ref1 longhouse with a round end (low rubble body, layered thatch, 48 deg cone, ball finial on a 44 deg hat). The ridge comb is still weak next to ref1's strong crest. |
| 2 Proportion and actor scale | 8.8 | Unchanged: the door is 1.00 x 2.10 m on a 12 cm threshold, the eave lip over the door is about 2.33 m, sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. |
| 3 Construction logic | 8.5 | The cone now yields to the thatch: its courses stop over the eave roll and the end apron, and nothing sits inside or under the roll (d01-d06). The hat no longer has a hub through it. Points off: at each crossing one thin soffit sheet cantilevers out over the thatch roll, carried by nothing (d07, d08, d30), and from the east the cut cone covering ends as a stacked, ragged edge (d03, d04). |
| 4 Seams and junctions | 8.2 | All three round-2 defects are gone. There is no shingle fan at either eave crossing, the free-gable roll ends are closed caps with no slot (d17, d18), and the hat is clean at four azimuths with no sky under it (d21, d22). All 21 red twins are closed. One small defect remains at both ends of the key junction: where the slope flashing sweep stops above the roll crest, its end is an open, crumpled lead tip, and beside it there is a dark void of about 0.25 x 0.08 m where `cone_keep_out` dropped units and nothing covers the gap (d28, d29). It reads as a dark notch at mid-shot from the door approach (d27) and in the official `actor_closeup`. The soffit sliver adds a little more. |
| 5 Distinctness and reuse | 8.8 | A genuinely new building type from a 91-line declarative recipe. The fix is the right kind of kit work. `GableRoof` now describes itself as a solid that any body can query, `drop_units` and `mesh_islands` are generic, `cone_keep_out` is the exact mirror of `linear_roof(abut_cone=...)`, and `hat_fit_units` tests units against the built hat. All are new keywords, the round-2 behaviour is still reachable, and the recipe changed by two arguments and one step order. The parallel duplicate modules still await the producer's merge. |
| 6 Technical compliance | 8.8 | 477k tris, 13.4 % hidden, 10 palette slots, `Mask` and UVs everywhere, identity transforms, no zero-area faces, no ground dressing, 88 decal anchors, and a geometry-identical rebuild. `DA_lichen_003`/`004` still sit on the threshold's walked top (third round). `LONG_cap_collar` is 12.3k tris, 57 % of them hidden (96-segment hat plus underside). |

**Verdict: 8.3/10, PASSED (pass mark 8.2).** The kit test the brief named is passed: a linear thatch roof and a
cone now each yield to the other through reusable keep-outs. The eave crossing is closed and logical from every
eye-level, look-up and crane view, with no see-through anywhere. Building 1 of the client-approved fallback list is
therefore proven buildable from kit modules. The grade is held at 8.3 by the junction axis: the small open flashing
tip and dark void at the bottom of each slope sweep, and the soffit sliver. All are module-level clean-ups in
`roof_junction` and `composite.cone_keep_out`, and every future round-end, tower-annex or turret junction gets the fix
for free.

**Strengths**
- `cone_keep_out` / `cone_roof(abut_roof=ROOF)` is a general mechanism, not a patch. The roof is a queryable solid
  (`keep_out`, `top_depth`, `eave_zone`, `under_soffit`), units are dropped whole (`drop_units`), never cut, and the
  same helpers can serve any body-meets-body junction in the kit.
- The eave crossing (the brief's key test) now reads as built: the cone courses finish over the thatch eave roll and
  the end apron, and nothing hangs below the soffit (d01-d06, red twins closed).
- `_eave_rolls(end_caps=True)` and `_verge_faces(roll_cover=...)` close the free-gable corners with no slot and no
  sky (d17, d18 and their red twins).
- `hat_fit_units` found and fixed the real cause of the round-2 hat creases (the rafter hub, not the shingles) by
  testing every unit vertex against the built hat. The hat is clean from four azimuths (d21).
- The recipe stays short and declarative, and every fix is a new keyword with the old behaviour reachable.
- Technically clean, with a geometry-identical director rebuild and a byte-identical decal JSON.

**Must-fix (next round on these modules)**
1. **`roof_junction.cone_abutment` sweep end, plus `end_apron`, at the lower end of both slope flashings.** This is
   at x ≈ 2.3, y ≈ ±2.85, z ≈ 2.9-3.0 m (after the recentre); see d28 and d29, which are visible in d27 and in
   `round_03/actor_closeup.png`.
   - What is wrong: the slope sweep (`ends="crest"`) stops 6 cm above the roll crest as an open, un-capped section
     that folds into a crumpled tip. Beside it is a dark void of about 0.25 x 0.08 m where `cone_keep_out` dropped
     cone units above the apron and nothing covers the gap.
   - What it should be: the sweep's lower end is closed with an end cap and laps at least 5 cm over the end apron,
     so it reads as one continuous lead piece from slope to apron.
   - The apron's cone-side width (`w_in`) is computed from the cone units that `cone_keep_out` actually kept, so the
     apron always runs under the last kept unit.
   - Alternatively, `cone_keep_out` lays a lead soaker under every dropped unit within 0.3 m of the junction line.
   - Either way, no dark void and no open lead end may be visible from the door approach or the crane.
   - Re-shoot d27, d28 and d29, plus red twins.
2. **`composite.cone_keep_out` on `LONG_roof_soffit_deck` (rule `"faces"`), at both soffit crossings.** This is at
   x ≈ 2.1-2.6, y ≈ ±(2.9-3.4), z ≈ 2.4-2.6 m; see d07, d08 and d30.
   - What is wrong: the slab's top, soffit and edge sheets are dropped face by face, independently. One thin soffit
     sheet is left cantilevering out over the thatch eave roll, single-sided and carried by nothing.
   - What it should be: treat the soffit slab as one unit per azimuth column (top, soffit and edge together). Drop a
     column when its centre lies inside the roof keep-out, and close the cut with an end face along the keep-out
     boundary. Alternatively, build `cone_soffit` with the roof keep-out passed in as `skip`.
   - No soffit board may reach past the round wall face into the body roof's zone.
3. **Decal anchors (producer note 11, plausible placement): `DA_lichen_003` and `DA_lichen_004`.**
   - They are at (-2.99 / -1.79, -2.81, 0.12), normal +Z: on the threshold slab's walked top, open since round 1.
   - Move them to the threshold's front riser or the door-jamb footing stones, or drop them.
   - Make `anchor_validate` exclude upward-facing threshold and step faces for `lichen` and `moss`.

**Nice-to-have (not blocking)**
- The cut cone covering seen from the east (d03, d04) ends as a stacked, ragged edge of plate ends. Add an even
  cut-line option (trim or align the last kept unit of each course parallel to the flashing), or lap a narrow lead
  skirt over the cut ends.
- Ridge comb: make the crest stand at least 0.3 m proud of the ridge roll (ref1's crest, a silhouette change; open
  since round 1).
- Ridge roll free end (d19): a flat octagonal disc with a dark slot under it, and a small open triangle at the comb
  end. Give it the same rounded closed cap as the new eave-roll ends.
- Thatch course-tail hairlines in the back three-quarter (d26).
- `composite_hidden_cull`: sort the kept faces canonically, so the file is bit-identical whatever the process count.
- `LONG_cap_collar`: 64 hat segments would read the same with fewer hidden triangles.
- One clipped wedge stone above the south-east round-end window (d24).
- Carried over: the producer's merge of duplicate modules, `path_to_round`, a cylinder variant of
  `cone_abutment`, and valley moss / cone-drip `water_streak` anchors.


## v3_longhouse_roundend round 4 — builder entry

All fixes are kit-module keywords whose defaults keep the round-3 behaviour. They are in v3's own `composite.py` and
`roof_junction.py`, plus one shared module, `anchor_validate.py`. That module got new optional keywords (default off),
so the three heroes were re-run to scratch. Kit changes are recorded in `kit/changes/v3_longhouse_roundend.md`
(round 4 section). No surface-detail work was done (note 12).

- Recipe: three steps changed and one gate keyword was added. It is now 94 non-blank, non-comment lines.
  - `cone_roof(..., abut_trim=True, abut_soakers=True, soffit_cut=True)`
  - `cone_abutment(..., taper=0.12, apron=dict(w_in_kept=True, u_top=0.54))`
  - `DECAL_VALIDATE["walk_zones"] = "da"`
- Build: `v3_longhouse_roundend.blend` (12.0 MB) and `decal_anchors.json` (82 anchors). The full build took
  7 min 09 s under shared load.
- Renders: `renders/variants/v3_longhouse_roundend/round_04/` holds all six views (24 samples), `stats.json` and
  `hidden.json`. `round_04/builder_checks/` holds re-shoots of d03, d04, d07, d08 and d27-d30 with red twins, made
  with the director's round-3 cameras.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 478,877 (round 3: 476,893) |
| est_hidden_pct | 13.8 % (round 3: 13.4 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 63 (new: `LONG_cone_soakers`) |

### Fixes

1. **Sweep end and void (hard requirement): `cone_abutment(taper=...)`, `end_apron(w_in_kept, u_top)` and
   `cone_keep_out(soakers=True)`.**
   - Cause: in the band where the cone surface runs under the thatch roll's top, both roofs yield. The thatch is
     clipped under the cone and the cone units are dropped inside the thatch solid, which left a pit. The round-3
     crumpled tip came from the last 3 sweep stations: there the junction turns over the roll plateau, the roof
     normal swings about 45 deg and the section twists.
   - Sweep end: the sweep now ends where the roof normal still follows the slope (stations more than 25 deg off are
     dropped). Its section closes over the last 0.12 m into a domed ring 3 cm past the end, so the end is closed
     lead with no open section.
   - Apron: it now runs 0.54 m up the roll tail (7 rows), under the sweep end, so the two lap by about 7 cm. Its
     cone-side `w_in` is computed per row from the cone units the keep-out actually kept (0.12-0.41 m south,
     0.12-0.32 m north).
   - Soaker: `cone_soakers` lays ONE closed lead soaker slab on the cone's reference surface under every unit
     dropped within 0.30 m of the roof top (40 units, each footprint grown by 3.5 cm).
   - Result: the pit now shows lead, not a dark void. The black slot is gone from `round_04/hero.png`,
     `actor_closeup.png` (px 800-850, 170-190) and `back.png`, and from d27, d28 and d29.
2. **Soffit crossing: `cone_soffit(cut=roof keep-out)` via `cone_roof(soffit_cut=True)`.**
   - The slab is built as whole azimuth spans. Each span's ends are refined per slope row by bisection onto the
     keep-out boundary, and each span is closed with top, soffit, eave edge and an end face at each cut.
   - No single-sided sheet is left and no board lies inside the roof's zone. The d30 and d07/d08 cantilevered sliver
     is gone.
3. **Decal anchors (note 11).**
   - `composite_decals(door_lichen="jamb")` puts the door lichen on the footing stones beside the jambs. They are now
     `DA_lichen_003` / `004` at (-3.51 / -1.27, -2.75, 0.24) with a -Y normal, so they are not on the threshold.
   - `south_moss=False` puts thatch moss on the north (+Y) slope only. Every thatch moss anchor now has y > 0.
   - `anchor_validate.validate_anchors(walk_zones="da")` (new, shared, default off) rejects lichen and moss on
     upward faces inside each door's trodden zone (`decal_gate.door_walk_zone`, reused unchanged). This build
     rejected nothing, because nothing is generated there any more.
4. **Even cut line (east, d03/d04): partly done.**
   - `trim_units` and `roof_eave_planes` (new kit helpers) cut units that cross the roof solid's eave plane on that
     plane and cap them, instead of dropping them whole: 8 shingles, 4 starters, 5 under-laps and 8 battens.
   - The ragged stack seen from the east is mostly NOT at that plane. It is the cone's eave courses that the keep-out
     keeps because they sit above the roll top, where the cone eave oversails the thatch. Each course ring meets the
     roll at a different azimuth. The soaker now backs the wedges with lead, but the stepped stack still reads in
     d03/d04 and the d07/d08 look-ups.

### Hero re-runs (anchor_validate changed; scratch outputs)

| hero | reference | round-4 re-run (scratch) | delta |
|---|---|---|---|
| hilltop_keep | 1,166,874 | 1,166,874 | 0 |
| wattle_roundhut | 876,619 | 878,355 | +0.20 % (inside +/-0.5 %; `anchor_validate` changes no geometry, so this is not from this change) |
| tower_windmill | 1,146,243 | 1,146,243 | 0 |

### Known gaps

- Item 2 of the audit is not finished: the stepped course ends over the roll from the east (d03, d04). The fix would
  be a second cut surface: trim the oversailing courses against the roof TOP (not the eave plane) near the eave band,
  or lap a lead skirt over them along the lower junction line. `cone_abutment(sweep_end="plane", fit_kept=True)` was
  tried and left in the kit as options, but the resulting skirt read as a folded flap, so the recipe does not use it.
- d29 (north, 160 mm tele) still shows one small dark slot beside a trimmed shingle at the cone side of the
  flashing. It does not show in the six review views.
- `cone_soakers` covers the whole slope junction (most of it under the thatch, and the cull removes 1,325 of its
  1,717 polygons). Hidden is 13.8 %.
- I did not make a second build to compare bit for bit. Every step is seeded.

## v3_longhouse_roundend round 4 — score 8.6/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12). Note 13 (no LED volume; the client's desktop is the reference
machine) changes nothing in this grade.

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_04/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (82 anchors) and all 16 builder re-shoots in `round_04/builder_checks/`.
- The recipe (94 lines, every step a `village_kit` import), `kit/changes/v3_longhouse_roundend.md` (round 4) and the
  round-4 module code (`composite.cone_soakers`, `trim_units`, `roof_eave_planes`, `_island_vertex_sets`,
  `cone_keep_out(trim, soakers, soffit_cut)`, `cone_soffit(cut=...)` / `_soffit_spans`, `roof_junction.end_apron
  (w_in_kept, u_top)` / `kept_cover_points`, `cone_abutment(taper)`, `anchor_validate(walk_zones)`).
- 48 director close-ups, 25 of them with red see-through twins (black clay against a red sky), in
  `renders/variants/v3_longhouse_roundend/round_04/director_extra/`: the round-3 set d01-d30 re-shot on the round-4
  file, plus new d31/d32 (both eave crossings from the east at 9 m, the mid-shot an actor walk-by sees), d33/d34
  (both slope-flashing lower ends from the crane on a 110 mm lens, the soaker zone), d35/d36 (the east stack on a
  120 mm lens), d37 (threshold and jamb footing), d38/d39 (the free gable and the ridge-roll end at eye level).
- A second full build to scratch, compared with the delivered file.

**Determinism and compliance (director-verified).** The rebuild is geometry-identical: the same 63 objects, 478,877
triangles and vertex hash (`ad0b6892…`), and a byte-identical `decal_anchors.json` (SHA-256 `1E858AC5…`). Every
unique mesh has an identity transform and a UV map (the 28 pegs are linked duplicates of 5 pooled meshes); `Mask` is
present and is both the active and the render colour attribute on every mesh; there are no zero-area faces; the
collections are `LONG`, `LONG_kit_instances` and `DECAL_ANCHORS`. Stats: 478,877 tris, est_hidden 13.8 %, 10 palette
slots, nothing in `mask_attribute_missing`, 12.0 MB. The rebuild took 7 min 32 s here, with director renders on the
GPU at the same time.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: unmistakably the ref1 longhouse with a round end (low rubble body, layered thatch, 48 deg cone, ball finial on a 44 deg hat). The ridge comb is still weak next to ref1's strong crest, and the ridge roll ends in a flat faceted disc against the sky at the gable (d38). |
| 2 Proportion and actor scale | 8.8 | Unchanged: door 1.00 x 2.10 m on a 12 cm threshold, eave lip over the door about 2.33 m, sills at 1.20-1.30 m, round-end eave at 2.30 m. |
| 3 Construction logic | 8.5 | The soffit sliver is gone: the boarded soffit now stops on the thatch boundary as whole closed spans (d07, d08, d30). The slope flashing now reads as one lead piece from slope to apron (d27, d28, d33). Points off: from the east the cone's eave courses over the thatch roll still end as a stepped stack of plates at actor distance (d03, d04, d35, d36), and the round end's pegged wall plate and all 28 pegs are now fully buried behind the soffit (100 % hidden in `hidden.json`), so a built module carries nothing visible. |
| 4 Seams and junctions | 8.5 | The round-3 hard requirement is met: no dark void and no open or crumpled lead tip at the lower end of either slope flashing (d27-d29, d33, d34; all red twins closed), and nothing shows in the official `actor_closeup`, `hero` or `back`. Every red twin across the 25 checks is closed. Remaining: the stepped east stack (closed, lead-backed, but cluttered at 5 m; at 9 m, d31/d32, it reads as a laced shingle valley and is acceptable); one small dark pocket beside a trimmed shingle at the north flashing (d29, d34, d06, tele only); and the ridge-roll free end (a flat octagonal disc with a dark slot under it, d19, d38, d39), open as a nice-to-have since round 3. |
| 5 Distinctness and reuse | 8.8 | A genuinely new building type from a 94-line declarative recipe. All round-4 geometry landed in kit modules as new keywords whose defaults keep round 3: `cone_soakers` and `trim_units` are generic (any mesh, any planes, any GableRoof), and `cone_soffit(cut=...)` takes any keep-out function. Points off: `cone_roof` has grown to 12 keywords, two options were left in the kit unused (`cone_abutment(sweep_end="plane")`, `fit_kept=True`), and `roof_junction.end_apron` now shares its name with the unrelated `junctions.end_apron`. The producer's merge of the parallel junction modules is still pending. |
| 6 Technical compliance | 8.9 | The rebuild is geometry-identical with a byte-identical decal JSON. 479k tris, 13.8 % hidden, 10 palette slots, `Mask` and UVs everywhere, no ground dressing, and 82 plausible anchors. The door lichen is now on the jamb footing stones (-Y normals), and the shared gate `walk_zones` is opt-in, so heroes are untouched. Build 7 min 09 s (builder) / 7 min 32 s (director, under load). Small points off: the wall plate and 28 peg objects are 100 % hidden, against note 1 ("nothing modelled that will never be seen"); and five thatch moss anchors carry a straight-up normal on a 40 deg slope. |

**Verdict: 8.6/10, PASSED (pass mark 8.2).** This round fixes all three round-3 must-fixes at module level, and the
key junction the brief names now holds from every eye-level, look-up and crane view:
- the slope flashing ends closed and laps the apron;
- a lead soaker backs every dropped unit;
- the soffit stops cleanly on the thatch;
- no see-through remains anywhere.

The rebuild is bit-identical. Building 1 of the client-approved fallback list is proven from kit modules, now with
cleaner seams than round 3 (8.3 -> 8.6).

Grade limits:
- The east-side stepped stack, still visible at close range.
- The ridge-roll end at the free gable.
- A built-but-invisible wall plate.

All three are module clean-ups that every future round-end, tower-annex or turret junction will inherit.

**Strengths**
- `cone_soakers` is the right kind of kit fix. Any body that yields to another backs its dropped units with one
  closed lead slab, so a keep-out can never open a dark void. It is generic over any GableRoof and is culled to 392
  visible polygons.
- `cone_abutment(taper)` together with `end_apron(u_top, w_in_kept)` makes the slope flashing one continuous, closed
  lead piece that laps the apron. The apron is sized from the units that were actually kept, so it adapts to any cone
  and roof combination (d27, d28, d33).
- `cone_soffit(cut=...)` builds the soffit as whole closed spans that stop on any keep-out boundary, with end faces.
  There are no single-sided sheets (d07, d08, d30, and their red twins are closed).
- `trim_units` and `roof_eave_planes` give the kit a general "cut on a plane and cap" helper alongside
  `drop_units`, for any unit mesh.
- Decal logic is now physical. Door lichen sits on the jamb footings, and moss is limited to the north slope. The
  shared gate's `walk_zones` is opt-in, so the heroes are unchanged.
- The recipe changed by three arguments and one gate keyword, and every fix is a keyword with round-3 behaviour still
  reachable. The rebuild is geometry-identical with a byte-identical decal JSON.

**Must-fix (next round on these modules; not blocking this pass)**
1. **`composite.cone_keep_out` / `trim_units`: the oversailing eave courses at both eave crossings, seen from the
   east.** This is at x ≈ 2.0-2.7, y ≈ ±(2.9-3.4), z ≈ 2.45-2.85 m (after the recentre); see d03, d04, d35 and d36.
   - What is wrong: the cone's lowest 3-4 courses that oversail the thatch eave roll are kept whole, because they sit
     above the roll top. Each course ring meets the roll at a different azimuth, so from the east at 5 m they end as a
     splayed, stepped stack of plate ends with dark slivers between them. It is closed and lead-backed, but cluttered.
   - What it should be: a second trim surface, `trim_units` against the GableRoof's TOP surface offset by `lift`
     within the eave band (`GableRoof.eave_zone`), for example `roof_top_planes(roof)` or a top-surface cut function.
     Every kept course should then end on one line that follows the roll's top, with capped cut ends that rest on
     the soaker or apron.
   - Do not use the folded-flap skirt.
   - Re-shoot d03, d04, d35 and d36 with red twins.
2. **`linear_roof` ridge roll, free (west) gable end.** This is at x ≈ -8.9, y ≈ 0, z ≈ 4.9-5.2 m; see d19, d38 and
   d39.
   - What is wrong: the ridge roll ends in a flat, faceted octagonal disc that oversails the verge face, with a thin
     dark slot under it. It reads against the sky from the gable approach at eye level.
   - What it should be: the same rounded, closed end cap the eave rolls got in round 3 (`_eave_rolls(end_caps=True)`),
     for example `_ridge_roll(end_caps=True)`. Its end should be flush with or no more than 5 cm past the verge face,
     and the verge face's top envelope should cover the roll's underside, so there is no slot.
3. **`composite.cone_soakers` and `trim_units`: the north flashing pocket.** This is at x ≈ 2.3, y ≈ +2.85,
   z ≈ 2.9-3.0 m; see d29, d34 and d06.
   - What is wrong: a dark pocket about 5 x 5 cm sits beside a trimmed shingle at the cone side of the flashing. The
     soaker's footprint is built from the DROPPED units only, so a unit that `trim_units` cut has no lead under its
     cut end.
   - What it should be: `cone_keep_out(soakers=True)` passes the trimmed units' removed parts (or their cut caps) to
     `cone_soakers` as footprints too, so lead runs under every cut or dropped unit within `reach`. No dark pocket may
     remain beside any trimmed unit.
4. **`round_wall.wall_plate` under `composite.cone_soffit` (note 1, nothing modelled that will never be seen).**
   - What is wrong: `LONG_wall_plate` (598 tris) and all 28 `LONG_peg_*` objects are 100 % hidden in
     `round_04/hidden.json`. The boarded soffit slab runs to 7.5 cm inside the plate line and buries them.
   - What it should be, either of:
     - `cone_soffit(r_in=...)` stops at the plate's outer face, so the plate and its pegs read under the eave from
       eye level (preferred: it is better construction logic);
     - or `wall_plate(pegs=False)` / a recipe flag that skips the plate and pegs when a soffit covers them.
   - Either way, no object may be 100 % hidden.

**Nice-to-have (not blocking)**
- Ridge comb: a crest at least 0.3 m proud of the ridge roll (ref1, silhouette; open since round 1).
- Thatch course-tail hairlines along several butts in the back three-quarter (d26; open since round 2).
- Decals:
  - `DA_moss_006/008/010/013/015` (thatch, y = 1.37) carry a (0, -0.03, 1.00) normal on a 40 deg slope. Snap the
    projection to the slope normal.
  - The `water_streak` under the cone eave drip and the valley moss promised by `composite_decals` are still absent.
- Kit hygiene:
  - Remove or document the unused `cone_abutment(sweep_end="plane")` and `fit_kept` options.
  - Rename `roof_junction.end_apron` (it clashes with `junctions.end_apron`).
  - Consider a `cone_roof(abut=dict(...))` sub-spec instead of 12 flat keywords.
- The small lead nub where the sweep's domed end ring shows at 100 mm (d06) could be flattened into the apron.
- Carried over for the producer:
  - merge the duplicate junction, opening and body modules;
  - add `path_to_round`;
  - add a cylinder variant of `cone_abutment`;
  - give `composite_hidden_cull` a canonical face order.
- The producer should confirm the wattle_roundhut +0.20 % drift in the builder's hero re-run has its own cause, as the
  builder says. `anchor_validate` changes no geometry.


## v3_longhouse_roundend round 4 — sign-off audit: REJECTED

Blocking issues (independent audit, copied by the producer from the workflow record):
- Seams and junctions are overgraded, and so is the overall score. The six official views (hero, front, side, back, aerial, actor_closeup) are clean, and every red twin is closed. But the director_extra close-ups show visible clipping and gaps at the brief's key junction. I score seams about 8.0 and construction about 8.2, not 8.5 and 8.5. The rubric overall is roughly the lowest axis, so this lands at about 8.0-8.1, under the 8.2 pass mark. The 8.6 is also inconsistent with round 2: there the same class of defect (a splayed shingle fan at the eave crossing) capped seams at 7.9.
- Hard requirement, clipping at the key junction: the east side of both eave crossings (composite.cone_keep_out / trim_units). Location: x 2.0-2.7, y +/-(2.9-3.4), z 2.45-2.85 m. In d03 and d04 (eye level, about 5 m away, about 4.7 m from the main door, inside the close-up priority zone of note 4) and in d35 and d36, the cone's lowest 3-4 oversailing courses end as a splayed jumble. Plates sit at different angles and trimmed caps are embedded in neighbouring plates; on the north side (d04) plate ends hang down beside the thatch eave roll. This is visible interpenetration, not just clutter. Fix it at module level: add a second trim against the GableRoof TOP surface inside eave_zone (e.g. roof_top_planes(roof) or a top-surface cut function), so every kept course ends on one line along the roll top with capped ends resting on the soaker or apron. No folded-flap skirt. Re-shoot d03, d04, d35 and d36 with red twins.
- Hard requirement, visible gaps beside the north slope flashing (composite.cone_soakers + trim_units). d29 and d34 show a dark pocket of about 5 x 5 cm beside a trimmed shingle at x 2.3, y +2.85, z 2.9-3.0 m. The top-down d12 shows another dark slot beside the north flashing near the ridge (around px 720,265). The cause: soakers are laid under DROPPED units only, so a unit that trim_units cut has no lead under its cut end. Fix: pass the trimmed units' removed parts (or their cut caps) to cone_soakers as footprints, so lead runs under every cut or dropped unit within reach.
- Hard requirement, visible gaps at the free (west) gable, linear_roof ridge-roll end and verge apex. Location: x -8.9, y 0, z 4.9-5.2 m. The ridge roll ends in a flat faceted octagonal disc that oversails the verge face, with a dark slot under it, seen against the sky from the eye-level gable approach (d19, d38, d39). There is also a small dark hole at the verge apex where the two verge faces and rafters meet (d39 around px 660,512; d38 around px 640,298). Fix: add _ridge_roll(end_caps=True), a rounded closed cap flush with or no more than 5 cm past the verge face, and extend the verge face's top envelope so it covers the roll underside and closes the apex.
- Technical compliance (note 1: nothing modelled that will never be seen; note 6): LONG_wall_plate (598 tris) and all 28 LONG_peg_* objects are 100% hidden in round_04/hidden.json, buried behind cone_soffit. A kit module that is built but never seen fails both construction logic and note 1. Fix: preferably cone_soffit(r_in=<plate outer face>), so the plate and pegs read under the eave from eye level. Otherwise use a wall_plate(pegs=False) / skip-when-soffit flag. No object may be 100% hidden.
- Construction logic in the soffit look-ups at both crossings (d07, d08): body rafter-tail blocks butt into and overlap the round wall's face stones. A loose thin curved stick pokes out of the deck edge into the dark slot between the body deck and the round wall head (d08, around px 1100-1190, 320-360). The linear_roof rafter tails should be clipped at the round wall face, using the same inside_round clip the walls use, and stray slivers removed.

## PRODUCER NOTE (2026-10-17) — closing round on kit 1.10.1

The kit has since been consolidated (1.8.0), the guard-rails turned on (1.9.0), the UV fix applied (1.10.0) and needle repair made deterministic (1.10.1); see kit/CHANGELOG.md and the rewritten README. Round 5 fixes every blocking issue above that still applies, on the current kit, and stays at or under 1,000,000 triangles (note 15). Kit edits to existing modules must keep every other building's geometry hash (HASH RULE).



## v3_longhouse_roundend round 5 — builder entry

Built on kit 1.10.1. Every fix is a new keyword or a new function in v3's own modules (`composite.py`, `linear_roof.py`,
`roof_junction.py`), and each keyword's default keeps the round-4 behaviour. Kit changes are recorded in
`kit/changes/v3_longhouse_roundend.md` (round 5 section). No surface-detail work was done (note 12).

- Recipe: 97 non-blank, non-comment lines (round 4: 94).
  - The `wall_plate` step was removed.
  - `round_eave_fill(z_bot="wall", r_off=-0.03)`
  - `linear_roof(..., rafter_skip=at_round, ridge_caps=True, verge_apex=True)`, where
    `at_round = inside_round(..., depth=-0.10)`
  - `cone_roof(..., abut_top_trim=True, abut_rake_deg=60.0, abut_min_keep=0.05)`
- Build: `v3_longhouse_roundend.blend` (13.0 MB) and `decal_anchors.json` (76 anchors). The full build took 17 min 20 s,
  because the CPU was shared with my six HASH-RULE rebuilds and with other builders.
- Fingerprint: geometry `9cc2fde8b210ef60`, uv `535af24558ca9557`, mask `44149668d2e2ff1a`, decal JSON SHA-256 `5F33F457…`.
- Renders:
  - `renders/variants/v3_longhouse_roundend/round_05/` holds all six views (24 samples), `stats.json` and `hidden.json`.
  - `round_05/builder_checks/` holds re-shoots with red twins (black clay against a red sky). Shots d03, d04, d35, d36,
    d38, d39, d07, d08, d12, d29, d33 and d34 are my approximations of the director's cameras; their positions are in
    the file names' targets: crossings at x ≈ 2.3-2.7, y ≈ ±3.1 and gable ridge end at x ≈ -8.95. Shot s1 looks
    square-on at the south crossing.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 479,497 (round 4: 478,877; cap 1,000,000) |
| est_hidden_pct | 13.3 % (round 4: 13.8 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 34 unique meshes (the plate and the 28 pooled pegs are gone) |
| objects 100 % hidden | `LONG_body_wall_blockers` only: the dark window blocker that note 6 prescribes (59 tris) |

### Guards (build log)

- Clearance at the door: eave lip 2.317 m, PASS.
- Seal probe at body_roof / round body: 41,407 rays, 0 leaks.
- Decal gate (applied): 99 checked, 76 kept.
- UV finish ran.

### Fixes, against the round-4 sign-off audit

1. **East side of both eave crossings (hard requirement): `cone_keep_out(top_trim=True, top_rake_deg=60)`.**
   - New `roof_cut_field`: a continuous cut surface for any body that yields to a `GableRoof`. It follows the roof
     solid's top (eave roll and ridge roll included, + lift). Past the roll's crest it runs down and out at
     `rake_deg`, so it does not drop vertically at the eave plane.
   - New kit helper `trim_units_field`: it cuts units on that curved surface, keeps the side above the surface and
     caps the cut, copying material, Mask and UVs. Eave-band units are now cut on that surface.
   - The cone courses that hung in front of the roll's nose were the round-4 stack of plates beside the roll. They
     are now cut on the raking line, or dropped if mostly under it.
   - The soaker now runs over the whole cut region. The result is one closed lead saddle in front of the roll nose,
     and the courses end on one line above it (`builder_checks/s1_south_face.png`, d04).
   - Every red twin is closed.
   - **Still open.** From the low SE/NE viewpoints (d03, d35), the layered eave edge of the lowest 3-4 cone courses
     still shows its layers where it stops at the roll. It reads as the layered butts of an eave edge seen from
     below, not as plates crossing each other.
   - The saddle shows as a dark lead plate under the north crossing in d04. It is one smooth closed piece, but it is
     visible.
   - A timber cheek board on the vertical cut plane was tried and then removed from the kit. It stood behind the cut
     courses from every eye-level view.
2. **North flashing pocket (hard requirement): `trim_units(removed=...)` / `trim_units_field(removed=...)` and
   `cone_soakers(always=...)`.**
   - The removed part of every CUT unit is now a soaker footprint too: 66 parts, plus the dropped units. Round 4
     soaked dropped units only.
   - d29 and d34 now show lead under the trimmed shingle beside the north flashing, with no dark pocket.
3. **Free west gable: ridge-roll end and verge apex (hard requirement): `linear_roof(ridge_caps=True,
   verge_apex=True)`.**
   - `_ridge_roll(end_caps=...)`: the roll runs 4.5 cm past the verge face and closes over its last 9 cm as a
     quarter ellipse, a rounded bundle end. It is no longer a flat octagonal disc.
   - `_verge_faces(ridge_cover=True)`: the verge face covers the roll's full section (top 1.2 cm inside its outline),
     so no slot is left under the roll.
   - `_rafters(verge_apex=True)`: the two verge rafters run 3 cm past the ridge into a crossed apex. The pocket at the
     apex is closed.
   - d38 and d39 are clean, and the red twin is closed.
4. **Wall plate and pegs 100 % hidden (note 1).**
   - I measured before choosing a fix. Deleting the soffit outright still leaves the plate 96.8 % hidden (pegs 100 %).
     `hidden_tris.py` views from rings at 1.4 x and 2.5 x the plan radius, and from there the 0.72 m stone eave hides
     the wall head. So `cone_soffit(r_in=plate face)` could not fix it.
   - I took the audit's alternative: no timber plate on this stone round end.
     - The wall head carries the rafters on a masonry beam-fill. This is `round_eave_fill(z_bot="wall")`: it starts
       3 cm into the round wall's top course (2.586 m), at r_off -0.03, just behind the stone face.
     - The wall head stays closed. The seal probe found 0 leaks.
   - `round_wall.wall_plate` is unchanged (the hut and v4 use it).
   - The only remaining 100 % hidden object is the window blocker (see stats).
5. **Body rafter tails at both crossings (d07, d08): `linear_roof(rafter_skip=...)`.**
   - A rafter tail with any box corner within 10 cm of the round wall face is not built (8 tails).
   - Each skipped tail still consumes its rng draw, so the thatch is laid identically.
   - d08 shows the body deck running cleanly into the round wall, with no blocks in the face stones.
   - The thin "stick" seen in round 4 was not seen again in d08.

### HASH RULE (existing kit modules edited)

The six other buildings were rebuilt to `kit/baseline/v3_r5_hash/` and fingerprinted. The grep and lazy-import check
in the changes file shows they import none of the three edited modules.

| building | reference (kit 1.10.1, `5_determinism`) | round-5 rebuild (`v3_r5_hash`) | result |
|---|---|---|---|
| hilltop_keep | 3e2a219a5901afc5, 1,166,874 | 3e2a219a5901afc5, 1,166,874 | identical (geometry, uv, mask) |
| wattle_roundhut | 7e5e7c2df5c4d367, 878,355 | 7e5e7c2df5c4d367, 878,355 | identical (geometry, uv, mask) |
| tower_windmill | 89bf4a2a2c60e049, 1,146,243 | 89bf4a2a2c60e049, 1,146,243 | identical (geometry, uv, mask) |
| v4_mixed (accepted) | 2e87caad61b68d34, 938,453 | 2e87caad61b68d34, 938,453 | identical (geometry, uv, mask) |
| v1_stone_watchtower | 47e4208df661a5a9, 1,057,164 | 465c7b1b8a7dbb22, 937,933 | changed by v1's own round: its recipe (05:41) and kit files edited by other builders today (`pyramid_roof`, `square_cabin`, `level_probe`, `tier_*`, 05:09-05:18). Neither the recipe nor those files reference `composite`, `linear_roof` or `roof_junction` (grep). Not from this round. |
| v2_tiered_hall | 87ba64b7f9d4a746, 954,925 | 48ded75fec0d442c, 966,704 | changed by v2's own round: its recipe (05:28) and `tier_cull` / `tier_flashing`. No reference to the three v3 modules (grep). Not from this round. |

### Known gaps

- d03 and d35 (SE/NE, eye level and tele): the lowest cone courses still show their layered eave edge where they stop
  at the roll. It is closed and lead-backed, with no interpenetration in the red twins.
- The lead saddle under each crossing (d04) is visible as one dark lead plate.
- The ridge roll's end dome is a 14-sided lathe; it is round at mid-shot.
- I made no second build to compare bit for bit. Every step is seeded. Round 4's rebuild was bit-identical, and every
  new helper in this round is deterministic.

## v3_longhouse_roundend round 5 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12). Checked against the round-4 sign-off audit's five blocking issues.

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_05/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (76 anchors) and all 26 builder re-shoots in `round_05/builder_checks/` (including `s1`).
- The recipe (97 lines; every step is a `village_kit` import, no local geometry), `kit/changes/v3_longhouse_roundend.md`
  (round 5) and the round-5 module code: `composite.roof_cut_field`, `trim_units_field`, `_copy_corner_data`,
  `cone_keep_out(top_trim, top_rake_deg, top_min_keep)`, `cone_soakers(always)`, `trim_units(removed)`,
  `linear_roof(rafter_skip, ridge_caps, verge_apex)` / `_ridge_roll(end_caps)` / `_verge_faces(ridge_cover)` /
  `_rafters(skip, verge_apex)`, and `roof_junction.round_eave_fill(z_bot="wall")`.
- 48 director close-ups, 32 of them with red see-through twins, in
  `renders/variants/v3_longhouse_roundend/round_05/director_extra/`. These are the round-4 cameras d01-d39 at their
  exact positions (so the comparison with round 4 is like for like), plus six new shots:
  - d40/d41: round wall head look-ups, S and N, at the removed plate.
  - d42/d43: both lead saddles from below on a 90 mm lens.
  - d44: the north crossing from the east at 8 m, eye level.
  - d45: the verge apex on a 120 mm lens.
- Two geometry probes on the delivered file: the extent and support of `LONG_cone_soakers`, and the eave heights at
  both crossings.
- A second full build to scratch (blender.exe 5.2, single-process cull, 9 min 54 s), hashed with `tools/geom_hash.py`.

**Determinism and compliance (director-verified).**
- The rebuild matches the delivered file and the builder's fingerprint:
  - geometry `9cc2fde8b210ef60` and mask `44149668d2e2ff1a` are identical;
  - 479,497 triangles and 34 objects in both;
  - `decal_anchors.json` is byte-identical (SHA-256 `5F33F457…`).
- The UV hash differs: rebuild `2ea3e665…`, delivered `535af245…`. The difference is in three objects only:
  `LONG_battens`, `LONG_rafters` and `LONG_round_wall_frames`.
  - The rebuild ran in blender.exe 5.2, while the builder ran the 5.1.2 module, so this may be a version difference.
    It is not proven to be.
- Stats: 479,497 tris (cap 1,000,000), est_hidden 13.3 %, 10 palette slots, nothing in `mask_attribute_missing`,
  13.0 MB.
- The only object that is 100 % hidden is `LONG_body_wall_blockers`, the note-6 window blocker (59 tris).

**Round-4 audit items:**

| # | audit item | round 5 |
|---|---|---|
| 1 | East eave crossings: stepped stack and clipping | **Partly fixed.** North: the courses now end on one raking line along the roll (d36, d43, d44), a clear change from round 4. South (d03, d35, d42 at 5 m): the upper courses end on the line, but the lowest three or four still end as a stepped stack with dark slivers between the plates. New: the lead saddle shows below the eave line (see below). |
| 2 | North flashing pocket | **Fixed.** d29 and d34 show lead with no pocket. In d12 there is no slot beside the north flashing. |
| 3 | Free west gable: ridge-roll end and verge apex | **Fixed.** The roll ends in a rounded cap with no slot under it, and the apex is a crossed, closed joint (d38, d39, d45, d19; red twins closed). The 14-sided dome reads slightly faceted only on the 135 mm lens. |
| 4 | Wall plate and pegs 100 % hidden | **Fixed by removal.** The rafters now bear on a masonry beam-fill on the wall head. It reads as built from below (d40, d41, d16). This is the audit's accepted alternative. |
| 5 | Body rafter tails in the round wall's face stones; loose stick | **Fixed.** d07 and d08 show no tail blocks in the face stones and no stick. |

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: unmistakably the ref1 longhouse with a round end. The ridge roll now ends in a rounded bundle against the sky at the gable (d38). The ridge comb is still weak next to ref1's crest. |
| 2 Proportion and actor scale | 8.8 | Unchanged. The door is 1.00 x 2.10 m on a 12 cm threshold, and the guard measures the eave lip over the door at 2.317 m (PASS). Sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. |
| 3 Construction logic | 8.2 | Three round-4 faults are gone: the rafter tails no longer pass through the face stones, the stick is gone, and the wall head visibly carries the rafters with nothing built-but-unseen. Points off for the new lead saddle. It lies on the cone's reference surface in the eave overhang, where `cone_keep_out` removed the cone's covering, soffit and rafters. It runs out to x ≈ 1.3 m under the thatch eave roll, 0.36-1.2 m outside both the body wall face and the round wall face, and down to z 2.27 m. That is 3 cm under the cone's own eave starters (2.30 m) and 14 cm under the thatch roll (2.41 m). The probe found 104 of 115 sampled low saddle vertices with nothing under them within 0.5 m, so it is a lead tray carried by nothing. It reads that way at eye level from the door approach (d01, d02), and as a dark faceted nub hanging below the eave from the east (d03, d04, d44). |
| 4 Seams and junctions | 8.2 | Better than round 4 by the audit's measure. Gable closed, north pocket closed, rafter tails clear, every one of the 32 director red twins closed, and all six official views clean. The north east crossing now ends on one line (d36, d44, and d32 at 9 m). Remaining: the south east stack still steps at 5 m and on the tele (d03, d35, d42); the saddle nub drops below the eave line (d04, d44); and small upturned triangular lead tabs stand on the saddle outline (d02 about px 520-580/375-430, d06 about px 520-700/440-570), which are `cone_soakers` raster corners. |
| 5 Distinctness and reuse | 8.7 | All new geometry is kit code: `roof_cut_field` and `trim_units_field` are generic over any `GableRoof` and any unit mesh, and `rafter_skip`, `ridge_caps`, `verge_apex` and `round_eave_fill(z_bot="wall")` are plain module keywords whose defaults keep round 4. The cheek board that was tried was taken out of the kit. The HASH RULE holds for keep, hut, mill and v4. The v1/v2 drift is from their own rounds (it does not touch these modules). Points off: `cone_roof` has grown to 15 keywords (8 of them `abut_*`), the unused `cone_abutment(sweep_end="plane")` / `fit_kept` options are still in the kit, and the `end_apron` name clash is still open. |
| 6 Technical compliance | 8.8 | Under the 1 M cap at 479k. 13.3 % hidden, 10 palette slots, `Mask` everywhere, no ground dressing, 76 plausible anchors. The rebuild is geometry- and mask-identical with byte-identical anchors. Small points off: the UV hash of three objects differs in the director rebuild (not yet attributed), and `DA_moss_005/007/009/012/014` still carry a straight-up normal on the 40 deg thatch (open since round 4). |

**Verdict: 8.3/10, PASSED (pass mark 8.2).** Graded against the stricter round-4 audit:
- Four of its five blocking issues are fixed at module level: the north pocket, the free gable, the hidden plate and
  the rafter tails.
- The fifth, the east crossing, is fixed on the north side and improved but not finished on the south side.
- The brief's key junction is closed from every eye-level, look-up, crane and top-down camera, with no see-through
  anywhere, and the six official views are clean.
- The rebuild matches in geometry, mask and decal anchors.

The grade is held at 8.3 by construction and seams:
- the new lead saddle is laid where the cone eave was removed, so it hangs unsupported under the thatch roll and dips
  below the eave line;
- the south-east stack still steps at 5 m.

Both are clean-ups inside `composite.cone_keep_out` / `cone_soakers`. Every future body that yields to a `GableRoof`
inherits them. Building 1 of the client-approved fallback list stays proven from kit modules.

**Strengths**
- `roof_cut_field` + `trim_units_field` are the right abstraction: one continuous, queryable cut surface for any body
  that yields to a `GableRoof` (roll and ridge included, optional raking line), and a generic "cut on a curved field and
  cap" helper that copies material, `Mask` and UVs. On the north crossing the cone courses now end on one raking line
  (d36, d44).
- `trim_units(removed=...)` / `cone_soakers(always=...)` close the class of defect, not just the instance: every cut or
  dropped unit now has lead under it (d29, d34).
- `linear_roof(ridge_caps=True, verge_apex=True)` gives any free gable a rounded, closed ridge-roll end and a closed
  verge apex (d38, d39, d45; red twins closed).
- `rafter_skip` takes any keep-out predicate and still consumes each rng draw, so the rest of the roof is laid
  identically. This is careful kit discipline.
- The builder measured first: it found that the plate was 96.8 % hidden even with no soffit, and so took the
  audit's alternative fix instead of a soffit change that could not have worked.
- HASH RULE evidence for the four untouched buildings. A director rebuild matches in geometry, mask and anchors.

**Must-fix (next round on these modules)**
1. **`composite.cone_soakers` / `cone_keep_out(top_trim=True, top_rake_deg=...)`: the lead saddle at both crossings
   hangs unsupported and below the eave line.**
   - Location: x ≈ 1.3-3.1, |y| ≈ 2.6-3.9, z 2.27-2.65 m (after the recentre). See d01, d02, d04, d06, d44 and the
     soaker probe.
   - What is wrong:
     - The saddle is laid on the cone's reference surface wherever cone units were cut or dropped, including the
       eave-overhang zone, where the keep-out has also removed the cone's soffit and rafters. It runs out to
       x ≈ 1.3 m, under the thatch eave roll and outside both wall faces, with nothing under it.
     - It reaches down to z 2.27 m, below the cone's eave starters (2.30) and 14 cm below the thatch roll (2.41).
     - From the west it reads as a flat lead tray cantilevered under the roll (d01, d02). From the east it reads as a
       dark faceted nub hanging below the eave (d04, d44).
   - What it should be:
     - Clip the saddle to where it is carried: over the kept cone soffit/deck, or dressed onto the thatch roll's top.
     - No part of it below the lower of (cone eave starter underside, roll top at that point).
     - Finish its free lower edge as a closed, turned-down drip that rests on the roll or on the soffit edge.
     - If the lead must reach further out, keep a closed `cone_soffit` span under it: pass the saddle outline as a
       keep region to `cone_soffit(cut=...)`.
     - Acceptance: a downward ray probe from every saddle vertex under z 2.42 hits a carrying surface within 5 cm.
   - Re-shoot d01, d02, d04, d06, d42, d43, d44 with red twins.
2. **`composite.cone_keep_out(top_trim=True)` / `trim_units_field`: the south-east stack.**
   - Location: x ≈ 2.0-2.7, y ≈ -(2.9-3.4), z ≈ 2.45-2.85 m. See d03, d35 and d42.
   - What is wrong: the north crossing now ends on one raking line, but on the south the lowest 3-4 courses still end
     as stepped plates with dark slivers between them at 5 m. Most likely cause: units that `abut_min_keep=0.05` and
     the "mostly above" rule keep whole, because they are not crossed by the field at any vertex.
   - What it should be:
     - Every covering unit inside `GableRoof.eave_zone` whose footprint (not only its vertices) crosses the raking
       cut is cut on it, with its cap resting on the saddle.
     - The south course ends form the same single line as the north.
   - Re-shoot d03, d35 and d42 with red twins.
3. **`composite.cone_soakers` outline: upturned lead tabs.**
   - Location: on the saddle's outline at both crossings, d02 (about px 520-580, 375-430) and d06 (about px 520-700,
     440-570).
   - What is wrong: small triangular tabs stand proud of the saddle. They are corners of the rasterised footprint
     (`cell` 2 cm).
   - What it should be: the slab outline is traced and simplified (or smoothed) before extrusion, so the sheet lies
     flat on its reference surface with a clean edge and no standing tabs.

**Nice-to-have (not blocking)**
- Determinism: run two builds in the builder's own bpy 5.1.2 environment and compare the `geom_hash` uv channel. If
  `LONG_battens`, `LONG_rafters` or `LONG_round_wall_frames` differ, make `uvgrain.finish_building` order-stable for
  them.
- `_ridge_roll(end_caps=True)`: 24 lathe segments instead of 14. The dome reads faceted on the 135 mm lens (d39).
- Decals:
  - snap `DA_moss_005/007/009/012/014` to the slope normal;
  - add the promised cone-drip `water_streak` and valley moss.
- Kit hygiene:
  - fold the 8 `cone_roof(abut_*)` keywords into one `abut=dict(...)` sub-spec;
  - remove or document `cone_abutment(sweep_end="plane")` / `fit_kept`;
  - rename `roof_junction.end_apron`.
- Ridge comb crest at least 0.3 m proud of the roll (ref1 silhouette, open since round 1).
- Carried over for the producer:
  - the merge of duplicate junction, opening and body modules;
  - `path_to_round`;
  - a cylinder variant of `cone_abutment`;
  - a canonical face order for `composite_hidden_cull`.

## v3_longhouse_roundend round 6 — builder entry

Built on kit 1.10.1. Every fix is a new function or a new keyword in v3's own `composite.py`, and each keyword's
default keeps the round-5 behaviour. Kit changes are recorded in `kit/changes/v3_longhouse_roundend.md` (round 6
section). No surface-detail work was done (note 12). This round answers the round-5 audit rejection and the director's
three round-5 must-fixes.

- Recipe: 101 non-blank, non-comment lines (round 5: 97).
  - `cone_roof(..., abut=dict(top_footprint=0.01, top_sliver=0.05, top_drop=("roof_underlap",), soaker_carry=True,
    soaker_smooth=4))`. `abut=` is the new sub-spec for keep-out options, so `cone_roof` no longer grows flat
    keywords.
  - `decals=partial(composite_decals, moss_normal="slope")`.
- Build: `v3_longhouse_roundend.blend` (13.3 MB) and `decal_anchors.json` (77 anchors). The full build took 14 min 55 s
  under shared load: my six HASH-RULE rebuilds and a second v3 build ran at the same time.
- Fingerprint (`tools/geom_hash.py`): geometry `c011a8a5759087ac`, uv `2f06eab003781dad`, mask `2a7c65ab15bb53a1`.
  The decal JSON SHA-256 begins `A0EB5EF24E35492A`.
- Renders:
  - `renders/variants/v3_longhouse_roundend/round_06/` holds all six views (24 samples), `stats.json` and
    `hidden.json`.
  - `round_06/builder_checks/` holds re-shoots on the director's exact round-5 cameras (positions copied from the
    director's `dir_render5.py`), 24 samples: d01, d02, d03, d04, d06, d07, d08, d28, d29, d33, d34, d35, d36, d42,
    d43 and d44. Every shot except d44 has a red twin.

### Stats (render_review stats.json)

| | |
|---|---|
| triangles | 491,890 (round 5: 479,497; cap 1,000,000) |
| est_hidden_pct | 12.9 % (round 5: 13.3 %) |
| material slots | 10 (unchanged) |
| mask_attribute_missing | none |
| bbox | 17.77 x 8.56 x 7.69 m, plan bbox centred on the origin |
| objects | 34 |
| `LONG_cone_soakers` | 13,465 tris, 36.1 % hidden. The cull removed 46,462 of its 53,318 polygons. The saddle is now one quad per cell (no long run quads, no T-junctions), so it costs about 12.7k more triangles than in round 5. |
| `LONG_roof_soffit_deck` | 78.3 % hidden (round 5: 95.7 %). It is a backing surface (note 6), so it is never culled. |

### Guards (build log)

- Clearance at the door: eave lip 2.317 m, PASS.
- Seal probe at body_roof / round body: 40,790 rays, 0 leaks.
- Decal gate: 99 checked, 77 kept.
- UV finish ran.

### Fixes, against the round-5 audit

1. **Floating lead saddle (construction logic): `cone_soakers(carry, seat, smooth)` via `soaker_support` and
   `cone_keep_out(soaker_carry=True)`.**
   - carry: a saddle cell is kept only where something carries it. That is on or in the thatch solid, never under its
     lower outline (the eave-roll belly or the deck underside, 5 mm clearance). Outside the roof's plan columns it is
     over the cone's kept soffit: slope distance at least soffit `eave_s` + 4 cm, with the soffit point under it also
     outside the columns. This build clipped 6,037 of 31,605 cells.
   - seat: over the soffit the sheet turns down and lies on the soffit boarding, ramped over about 4 cells (2,415
     nodes seated). Its free lower edge is a closed edge resting on the soffit.
   - Acceptance probe on the delivered file: a vertical ray from each saddle vertex, with the saddle itself
     excluded. Of 8,696 vertices, 489 are under z 2.42, and **0** have nothing within 5 cm below them. In round 5,
     my probe found 340 of 344 with nothing within 5 cm and 313 with nothing within 0.5 m. The lowest saddle vertex
     is now 2.354 m (round 5: 2.265).
   - d01 and d02: the cantilevered lead tray under the roll is gone. The saddle meets the roll end, and the round
     wall shows under the roll as at any eave.
   - d04: the dark faceted lead lump below the north eave is gone.
   - d03: the faceted block hanging below the south eave line (px 470-650, 330-480) is gone. That block was the
     saddle under the roll.
2. **Upturned tabs on the saddle outline (seams).**
   - Most of the tabs were not raster corners. They were the cut remnants of under-lap units (`LONG_roof_underlap`),
     left as bare plates on the saddle once the shingles over them were cut back (colour pass, d06).
   - `top_drop=("roof_underlap",)` now drops the under-laps that the cut touches whole (180 polygons).
   - `drop_slivers(h=0.05)` drops any cut unit left as a thin sliver on the cut: 105 shingle and 17 starter
     polygons.
   - `soaker_smooth=4` traces the raster outline into a smooth line, as asked.
   - d02 and d06 show no standing tabs. One cut starter end, a shingle, still points into the north crossing in the
     d06 tele.
3. **South-east stack (hard requirement): `cone_keep_out(top_footprint=0.01)` (`footprint_field`). Partly done.**
   - Eave-band units are now cut on their footprint, the cut field evaluated at each point's foot on the cone's
     reference surface. Every course, whatever its height in the stack, ends on the same surface, square to the cone,
     on one line in plan. A unit whose vertices sit above the cut but whose footprint crosses it is now cut too
     (24 shingles, 5 starters and 4 battens).
   - **Still open:** d03 and d35 still show the layered section of the cone's lowest 3-4 courses where they end
     against the roll and the abutment flashing. These are the shingle, starter, eave-batten and rafter layers, with
     gaps between the layers. Every red twin is closed, and no plate passes through another at the cut.
   - Tried and removed again: `cut_cheek_lead`, a closed lead cheek traced along the cut line over the cut course
     ends. It found kept units beside the traced line on only a few rows (4 short segments), so it covered nothing.
     It is not left in the kit.
4. **Not blocking alone:**
   - **Moss normals:** `composite_decals(moss_normal="slope")`. 13 of the 14 thatch moss anchors now carry the 40 deg
     slope normal (0, 0.643, 0.766). The decal gate re-snapped `DA_moss_007` to a course-top facet
     (-0.005, 0.095, 0.995).
   - **UV determinism, attributed:**
     - Re-running `uvgrain.finish_uvs` on the round-5 file in the 5.1.2 module reproduces the delivered UV hashes
       exactly, in two runs.
     - `regrain_mesh` sign-fixes the PCA major axis but not the second axis `B1` (uvgrain.py line 163). That sign is
       whatever the LAPACK build returns.
     - Flipping `B1` changes exactly `LONG_battens`, `LONG_rafters` and `LONG_round_wall_frames`, the three objects
       that differ in the director's blender.exe 5.2 rebuild.
     - The fix is `B1 = _sign_fix(B1)`. It is in the shared uvgrain and would change every building's UV hash, so it
       is left to the producer (noted in the changes file).
   - **Soffit deck:** not changed. It is a note-6 backing surface, and it now measures 78.3 % hidden.

### Red twins (builder_checks)

All 15 red twins are closed at the junction. Red shows only as sky beyond the silhouettes. In d01 there is one thin
sky slit between two shingles, high on the cone's silhouette (px 865-920, 185-230). It is identical in the round-5
director twin, so it is not from this round.

### HASH RULE (`composite.py` edited)

The six other buildings were rebuilt to `kit/baseline/v3_r6_hash/`. None of them imports `composite`.

| building | reference (kit 1.10.1, `5_determinism`) | round-6 rebuild (`v3_r6_hash`) | result |
|---|---|---|---|
| hilltop_keep | 3e2a219a5901afc5, 1,166,874 | 3e2a219a5901afc5, 1,166,874 | identical (geometry, uv, mask) |
| wattle_roundhut | 7e5e7c2df5c4d367, 878,355 | 7e5e7c2df5c4d367, 878,355 | identical (geometry, uv, mask) |
| tower_windmill | 89bf4a2a2c60e049, 1,146,243 | 89bf4a2a2c60e049, 1,146,243 | identical (geometry, uv, mask) |
| v4_mixed (accepted) | 2e87caad61b68d34, 938,453 | 2e87caad61b68d34, 938,453 | identical (geometry, uv, mask) |
| v1_stone_watchtower | 47e4208df661a5a9, 1,057,164 | 465c7b1b8a7dbb22, 937,933 | the same value as the round-5 run: v1's own round, which does not reference `composite` |
| v2_tiered_hall | 87ba64b7f9d4a746, 954,925 | 8c0a017d6d645cc6, 980,775 | v2's own ongoing round (`tier_flashing.py` edited 06:40 today); it does not reference `composite` |

### Known gaps

- **The south-east (and north-east) stack** of the cone's lowest courses still reads as layered cut ends at 5 m (d03,
  d35). The floating saddle and the lead lump that made it a jumble are gone. A closed cover over the cut section
  (a verge or cheek module that works) is the next step.
- `DA_moss_007` was re-snapped to a course-top facet normal by the decal gate.
- I made no second full build to compare bit for bit. Every new step is deterministic: numpy only, no random state,
  stable ordering.

## v3_longhouse_roundend round 6 — score 8.1/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only. No ground dressing is
scored (note 10), and no surface detail is asked for (note 12). Checked against the three round-5 must-fixes. The
south-east stack has been a hard requirement since the round-4 audit.

**Reviewed:**
- All six review renders in `renders/variants/v3_longhouse_roundend/round_06/`, plus `stats.json`, `hidden.json`,
  `decal_anchors.json` (77 anchors) and all 31 builder re-shoots in `round_06/builder_checks/`.
- The recipe (101 lines). Every step is a `village_kit` import with no local geometry.
- `kit/changes/v3_longhouse_roundend.md` (round 6) and the round-6 module code: `soaker_support`, `cone_soakers(carry,
  seat, smooth)` / `_soaker_cells` / `_outline_smooth`, `drop_slivers`, `footprint_field` / `_cone_foot`,
  `cone_keep_out(top_footprint, top_sliver, top_drop, soaker_carry, soaker_smooth)`, `cone_roof(abut=...)` and
  `composite_decals(moss_normal)`. I confirmed by grep that `cut_cheek_lead` is not in the kit.
- 56 director close-ups, 40 of them with red see-through twins, in
  `renders/variants/v3_longhouse_roundend/round_06/director_extra/`:
  - the round-5 cameras d01-d45 at their exact positions, so the comparison is like for like;
  - eight new shots:
    - d46/d47: both east stacks at eye level from 3 m;
    - d48/d49: both crossings square-on from 4 m;
    - d50/d51: along each eave roll from the west, at roll height;
    - d52/d53: look-ups at the saddle's seat on the soffit.
- Three probes on the delivered file:
  - hygiene;
  - saddle support (a downward ray from every saddle vertex);
  - a floating-piece probe at both crossings: the gap from each mesh island to all other geometry. I also ran this
    probe on the round-5 rebuild for comparison.
- A second full build to scratch (blender.exe 5.2.2, single-process cull), hashed with `tools/geom_hash.py`.

**Determinism and compliance (director-verified).**
- The rebuild matches the builder's fingerprint for geometry `c011a8a5759087ac` and mask `2a7c65ab15bb53a1`.
- Both files have 491,890 triangles and 34 objects.
- `decal_anchors.json` is byte-identical (SHA-256 `A0EB5EF2…`).
- The UV hash differs (`58ff1b08…` against `2f06eab0…`) in four objects: `LONG_battens`, `LONG_rafters`,
  `LONG_round_wall_frames`, and now also **`LONG_roof_shingles`**. The builder's B1 sign attribution covers the first
  three only.
- Every mesh has an identity transform, a UV map and `Mask` as both the active and the render attribute. No face has
  zero area.
- The collections are `LONG`, `LONG_kit_instances` and `DECAL_ANCHORS`.
- Stats: 491,890 tris (cap 1,000,000), est_hidden 12.9 %, 10 palette slots, nothing in `mask_attribute_missing`.
- **Build time:** my rebuild took **27 min 45 s**; round 5 took 9 min 54 s on the same machine and path.
  - 1,614 s of that is `composite_hidden_cull`.
  - Of that, **1,110 s is `LONG_cone_soakers` alone**: 53,318 one-quad-per-cell polygons, of which 46,462 are then
    culled. In round 5 this object had 2,170 polygons and its cull took 28 s.
  - The builder reports 14 min 55 s under load. Both times break the art-bible-8 limit of about 10 minutes.

**Round-5 must-fixes:**

| # | item | round 6 |
|---|---|---|
| 1 | Lead saddle hangs unsupported and below the eave line | **Fixed as asked.** My probe agrees with the builder's: 0 of 489 saddle vertices under z 2.42 have nothing within 5 cm below (round 5: 104 of 115 sampled had nothing within 0.5 m), and the lowest vertex is 2.354 m. The tray under the roll is gone (d01, d02), and so is the lump below the eave (d03, d04, d44). **But** see the new defects below: units that rested only on the clipped lead now hang free, and the lead no longer covers the roll-nose pocket. |
| 2 | Upturned tabs on the saddle outline | **Mostly fixed.** d02 shows no tabs. One cut starter remains in the d06 tele as a beak pointing into the north crossing, about 3 cm off any support (probe). A cut plate stands vertically beside the north roll end (d51, px 500-560 / 300-450). |
| 3 | South-east stack (hard requirement) | **Not fixed.** d03, d35 and d46 (3 m, eye level) still show the splayed, layered section of shingle, starter, eave batten and rafter ends in front of the roll, unchanged from round 5. **The north side has regressed:** in round 5 the north courses ended on one raking line over the lead (round-5 d36). With the lead clipped away, d36 and d47 now show the same layered section, with a plate crossing the stack diagonally. |

**New in round 6:**
- **Dark pocket at the south roll nose, in an official view.** `actor_closeup` (px ≈ 855-890, 200-215) and d28 show
  a dark wedge between the cut cone course ends and the top of the eave roll, where round 5 showed smooth lead. The red
  twins are closed, so it is a shadowed pocket and not a hole. It is new in the official set, which was clean in
  round 5.
- **Free-hanging eave-band pieces.** The floating-piece probe finds four new islands low in the eave band. None of
  them was in the round-5 file.
  - an under-lap at (2.62, +3.61, 2.40), 4.2 cm from anything;
  - a south eave batten at (3.27, -3.84, 2.30), 3.9 cm;
  - a north starter at (2.23, +3.42, 2.34), 3.3 cm: the d06 beak;
  - a south shingle at (2.20, -3.44, 2.37), 1.8 cm: a loose lump seen against the roll's underside in the d07
    look-up, px ≈ 590-740 / 115-195.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | Unchanged and right: unmistakably the ref1 longhouse with a round end. The low rubble body, the layered thatch, the 48 deg cone with its ball finial and the rounded ridge-roll end all read at thumbnail size. The ridge comb is still weak next to ref1's crest. |
| 2 Proportion and actor scale | 8.8 | Unchanged. The door is 1.00 x 2.10 m on a 12 cm threshold, and the guard measures the eave lip over the door at 2.317 m (PASS). Sills are at 1.20-1.30 m and the round-end eave is at 2.30 m. |
| 3 Construction logic | 8.3 | The round-5 fault is fixed: the lead now lies only where something carries it, and it seats on the soffit with a closed edge (probe verified). Points off because the fix was not followed through. The units that rested on the clipped lead were kept, so four eave-band pieces now hang 1.8-4.2 cm off any support. Two of them can be seen: the d06 beak and the d07 lump. |
| 4 Seams and junctions | 8.0 | All 40 director red twins are closed. The gable, the slope flashing, the soffit and the wall-head junctions are as clean as in round 5. But the key junction the brief names is no better than in round 5: (a) the south-east stack, a hard requirement for two rounds, is unchanged (d03, d35, d46); (b) the north-east stack, which ended on one line over lead in round 5, now shows the same layered section, with a crossing plate (d36, d47); (c) a new dark pocket shows at the south roll nose in the official `actor_closeup` and in d28. By the round-4 audit's standard, a splayed stack at actor distance is about 8.0. |
| 5 Distinctness and reuse | 8.7 | All new geometry is kit code. `soaker_support`, `footprint_field` and `drop_slivers` are generic over any cone and `GableRoof`, every keyword's default keeps round 5, and the cheek that did not work was taken out of the kit. `cone_roof(abut=dict(...))` is the right direction. Points off: the recipe still passes the eight older options as flat `abut_*` keywords beside the dict. The unused `cone_abutment(sweep_end="plane")` / `fit_kept` options and the `end_apron` name clash are still open. |
| 6 Technical compliance | 8.4 | The rebuild matches in geometry and mask, and the decal JSON is byte-identical. 492k tris, 12.9 % hidden, 10 palette slots, `Mask` and UVs everywhere, no ground dressing, 77 plausible anchors, 13 of 14 thatch moss anchors on the slope normal. Points off: (a) the build now takes 27:45 single-process (14:55 for the builder under load), against the 10-minute rule; the cause is the 53k-polygon per-cell saddle, 87 % of which is culled; (b) a fourth object, `LONG_roof_shingles`, now differs in UV hash, outside the builder's B1 attribution; (c) `DA_moss_007` still projects straight down on the 40 deg thatch. |

**Verdict: 8.1/10, NOT PASSED (pass mark 8.2).**

The round fixed exactly what was asked about the saddle. It is now carried, and the cantilevered tray and the hanging
lump are gone. The tabs are mostly gone, and the recipe and kit stay clean and declarative.

But clipping the lead took away the cover that had hidden the cut section on the north side. It left four eave-band
pieces with nothing under them, and it opened a dark pocket at the south roll nose that shows in the official
`actor_closeup`. The south-east stack, the one hard requirement left from the round-4 audit, is unchanged. The brief
names this junction as the key test of the kit, and it now reads worse on the north side than it did in round 5.

The saddle also tripled the build time. The grade drops from 8.3 to 8.1, held down by seams.

All of these are fixes inside `composite.cone_keep_out` / `cone_soakers`, so every future body that yields to a
`GableRoof` inherits them.

**Strengths**
- `soaker_support` + `cone_soakers(carry, seat)` are the right rule: lead exists only where a surface carries it, and
  over a soffit it turns down and seats with a closed edge. The acceptance probe passes in full (0 of 489).
- `footprint_field` / `_cone_foot` give the kit a cut evaluated at each point's foot on the cone's reference surface,
  so every course, whatever its height in the stack, is cut on one line in plan. This is the geometric basis for the
  cover module that is still missing.
- `drop_slivers` and `top_drop=("roof_underlap",)` remove the bare under-lap tabs at their source.
- The kit stays disciplined:
  - `cone_roof(abut=dict(...))` stops the keyword growth;
  - every default keeps round 5;
  - the HASH RULE was re-run for all six other buildings;
  - the failed cheek was removed, not left in the kit.
- The UV non-determinism was traced to a concrete line (`uvgrain` B1 sign) with a one-line fix, and was correctly
  left to the producer because it changes every building's hash.

**Must-fix (round 7, on these modules)**
1. **`composite.cone_keep_out(top_trim=True, top_footprint=...)`: a closed cover over the cut course section at both
   east crossings (hard requirement since the round-4 audit).**
   - Location: x ≈ 2.0-2.7, y ≈ ±(2.9-3.5), z ≈ 2.30-2.85 m (after the recentre). See d03, d35, d46 (south) and
     d36, d47 (north).
   - What is wrong: the lowest 3-4 cone courses end in front of the eave roll as an open, splayed section of
     shingle, starter, eave batten and rafter ends, with dark gaps between the layers. The north side now does this
     too, with one plate crossing the stack.
   - What it should be: one new keyword in `cone_keep_out`, for example `top_cover=dict(mat="M_lead", t=0.012,
     lap=0.06)`, building a single closed sheet.
     - It is swept along the footprint-cut line in plan. `footprint_field` already gives that line; drive the sweep
       from it, not from kept-unit adjacency, which is why `cut_cheek_lead` found only 4 segments.
     - It is dressed from 6 cm up-slope over the kept course ends, down across the cut faces, onto the roll top or
       end apron.
     - It is closed at both ends, and its lower edge rests on the roll.
   - The alternative: drop the eave-band starter, eave batten and rafter tails inside the cut region, and let the
     lowest kept course finish over lead on the roll.
   - Acceptance: d03, d35, d36, d46 and d47 each show one closed line with no layered section, and the red twins
     stay closed.
2. **`composite.cone_soakers(carry=...)` / `drop_slivers`: units left floating once the lead under them is clipped.**
   - Location:
     - an under-lap at (2.62, +3.61, 2.40);
     - an eave batten at (3.27, -3.84, 2.30);
     - a starter at (2.23, +3.42, 2.34): the d06 beak;
     - a shingle at (2.20, -3.44, 2.37): the d07 lump.
   - What is wrong: each piece is 1.8-4.2 cm from any other geometry. Their only support was the saddle cells that
     `soaker_carry` clipped.
   - What it should be: after the carry clip, a support pass in `cone_keep_out`, for example
     `drop_unsupported(ob, tol=0.005)` as a generic kit helper beside `drop_slivers`. It drops every covering or
     structure island within `GableRoof.eave_zone` whose nearest other geometry is more than 5 mm away, so carry and
     keep agree. Also remove the vertical cut plate beside the north roll end (d51).
   - Acceptance: an island-gap probe over x 1.0-3.8, |y| 2.2-4.2, z 2.2-3.4 finds no island more than 5 mm from
     other geometry, and d06, d07 and d51 show no free piece.
3. **`composite.soaker_support` (carry rule): the dark pocket at the south roll nose.**
   - Location: x ≈ 2.2-2.5, y ≈ -(3.0-3.3), z ≈ 2.45-2.60. See the official `actor_closeup` (px ≈ 855-890 /
     200-215) and d28.
   - What is wrong: the lead that covered the slot between the cut course ends and the roll top in round 5 has been
     clipped. A dark wedge now shows in an official view.
   - What it should be: carry also accepts cells lying on, or up to 1 cm above, the thatch solid's top surface
     (the roll crest), so the lead dresses over the roll top up to the cut line. Alternatively, the must-fix-1 cover
     closes the slot.
   - Acceptance: no dark pocket in `actor_closeup`, d28 or d48.
4. **`composite._soaker_cells` (art bible 8, build under about 10 minutes): the per-cell saddle cost.**
   - What is wrong: the saddle is built as 53,318 one-quad-per-cell polygons, and 46,462 of them are then culled.
     Its visibility cull alone takes 1,110 s single-process (round 5: 28 s), so the full build takes 27:45 here and
     14:55 for the builder.
   - What it should be: before the slab is built, drop cells that lie under kept covering, beyond `lap` from any cut
     or dropped unit. Then merge each azimuth row into strips that share row vertices, so there are no T-junctions.
     Aim for at most about 5k polygons before the cull.
   - Acceptance: the saddle reads as in round 6, and a full rebuild finishes in under about 10 minutes.

**Nice-to-have (not blocking)**
- Move the recipe's eight flat `abut_*` keywords into the `abut=dict(...)` sub-spec so the recipe has one keep-out
  spec.
- UV determinism: `LONG_roof_shingles` now differs too (4 objects). The producer should apply the `uvgrain`
  `B1 = _sign_fix(B1)` fix kit-wide and confirm that it also covers the shingles.
- `DA_moss_007`: keep the slope normal when the gate re-snaps it onto a course-top facet (for example, gate
  `normal_fp_dot` per surface).
- The pre-existing thin sky slit high on the cone silhouette in d01 (px ≈ 865-920 / 185-230).
- Kit hygiene, carried over:
  - remove or document `cone_abutment(sweep_end="plane")` / `fit_kept`;
  - rename `roof_junction.end_apron`.
- A ridge comb crest at least 0.3 m proud of the roll (ref1 silhouette, open since round 1).
- Carried over for the producer:
  - merge the duplicate junction, opening and body modules;
  - add `path_to_round`;
  - add a cylinder variant of `cone_abutment`;
  - give `composite_hidden_cull` a canonical face order.


## CLIENT DIRECTION (2026-10-17) — redesign the round end so the eaves no longer cross

Client's words, approving the producer's proposal: "I'm good with your redesign suggestion."

The proposal: raise the round end so that the longhouse's linear (thatch) roof runs into the round drum's WALL, below the cone's eave, instead of the two eaves crossing. That removes the eave-crossing junction, the cause of every audit rejection since round 3, instead of patching it again.

What this means for round 8:
- **Round end:** a taller round body. Its wall continues up past the longhouse's eave and ridge, so the cone's eave sits above the point where the longhouse roof meets the drum. Keep ref1's character: a mossy cone over a round stone end, unmistakably the longhouse with a round end. A raised round end, about one storey higher, is consistent with ref1. Keep proportions believable next to the 1.8 m figure, add a window or slit on the raised part if it reads blank, and stay at or under 1,000,000 triangles (note 15).
- **The junction becomes "gable roof abutting a round wall".** The thatch and its ridge die into the drum with a flashing or flaunching band following the true intersection curve on the cylinder; this is the kit's missing "cylinder version of cone_abutment" that both kit reviews asked for. Build it as a reusable kit module (for example `roof_junction.wall_abutment(round body)`), not one-off code. The eaves no longer meet the cone at all.
- **What carries over:** keep everything that already works (walls, gable, verge, ridge roll, soffits, doors, windows, thatch courses, decal gating, clearance). Remove or bypass the eave-crossing machinery (cone_keep_out, trim_units_field, top_trim, the eave-band saddle) in the recipe; the modules can stay in the kit for other designs.
- **Interrupted work:** a round-7 fixer was stopped at about 08:47. It had edited `build_v3_longhouse_roundend.py` (08:37) and `kit/village_kit/components/composite.py` (08:47) after the last complete build (round 6, 07:36). Review those edits and keep only what is sound.
- **Hash rule:** composite.py and the v3 modules are v3-only, but if you touch any shared module, every other building's geometry hash must stay identical (kit 1.10.1 table in the CHANGELOG).


## PRODUCER NOTE (2026-10-17 09:07): round-8 redesign fixer stopped for the session handoff

The round-8 fixer was stopped about 25 min in, after rewriting build_v3_longhouse_roundend.py (08:57) and before any build or render. The next round-8 fixer: start from the CLIENT DIRECTION above, review that partial recipe (and the earlier partial composite.py edit), keep what is sound, and complete the redesign.

## CLIENT DIRECTION (2026-10-17, session 2): longhouse time cap

Client's words: "The long house is cleared by me for this stage", then: "If it's mid run the round 8 redesign can continue but I don't want to spend much more time on the longhouse. Max 45 min." The round-8 fixer's build (09:08) had finished but had no builder entry; it was graded as built, with no further fix rounds.

## v3_longhouse_roundend round 8 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). This is the client-approved redesign:
the round end is raised so that the thatch roof runs into the drum's wall below the cone's eave. Geometry only. No
ground dressing is scored (note 10), and no surface detail is asked for (note 12). There is no builder entry (the
fixer was stopped before writing it), so every finding below comes from the geometry.

**Reviewed:**
- The six review renders in `round_08/` against `round_06/`, plus `stats.json` and `decal_anchors_r8.json`.
- The recipe `redesign_r8_wip/build_v3_longhouse_roundend_r8.py`, the Round 8 entry in
  `kit/changes/v3_longhouse_roundend.md`, and `roof_junction.wall_abutment` / `round_body_face` /
  `LINEAR_ROOF_PARTS`.
- 21 director close-ups, 17 of them with red see-through twins, in `round_08/director_extra/` (`dir_render8.py`,
  `run8.log`). The cameras are placed relative to the drum centre, measured at (4.72, -0.02):
  - j01-j08: both eave ends, at eye level and in tele, and look-ups at the soffit;
  - j09-j16: both flaunching slopes, the ridge into the drum, top-down, and the cone over the roof;
  - j17-j21: the cone eave, the drum next to a 1.8 m figure, and the upper windows.
- A probe on the delivered file:
  - per-object bounding boxes;
  - a floating-island probe on the eave roll, the ridge, the comb and the abutment, measuring each island's gap to
    all other objects.

**Compliance:**
- 617,342 tris, under the 1 M cap (note 15). This is up 25 % on round 6, mostly from the taller drum: 97k stone polygons.
- est_hidden 9.2 %, 10 palette slots, nothing in `mask_attribute_missing`.
- 89 decal anchors, 43 of them above 3 m, with a plausible mix.
- `wall_abutment` has 0 floating islands, and so does the eave roll.
- The probe flagged ridge-strap and comb islands as more than 1 cm from other objects. These are false positives: they
  sit on their own object (the ridge roll and the comb), and the probe skips a piece's own object.
- **Not verified:** determinism (I made no second build) and the six-building hash rule. The Round 8 kit entry points
  to "results in the round-8 builder entry", and that entry does not exist.

**The redesigned junction (gable roof abutting a round wall):**
- **Gone:** the eave-crossing junction behind every rejection since round 3 no longer exists. The two eaves never meet.
- **Trimming is clean.** The deck, rafters, courses, eave rolls, ridge roll and comb all stop inside the stone. I found
  no cut ends, see-through or slots (j09-j14).
- **No see-through.** Every red twin is closed (for example j16_red, j11_red, j09_red).
- **The lime flaunching follows the true intersection curve eave to eave and over the ridge** (j09, j10, j11, j13,
  j14). It reads as built work at mid-shot distance.
- It is a real kit module that reuses the compound family's `clip_at_tower`, `trace_roof_on_tower`, `ride_fillet` and
  `wall_end_apron`. It also guards itself: it raises if the two eaves would cross.

**Key defects (none blocking):**
1. **The eave-end lead aprons read as stuck-on tabs.**
   - **Where:** each apron is a flat rectangular plate, about 0.18 x 0.28 m, standing a few cm proud of the stone
     beside the eave-roll nose. It does not dress over or around the cut roll end.
   - **Renders:** south j01 (px ≈ 790-865 / 160-290), j05 (px ≈ 950-1210 / 0-145) and j07 (px ≈ 850-1010 / 170-310);
     north j03 (px ≈ 405-480 / 165-290) and j10 (px ≈ 215-260 / 615-680).
   - **Effect:** closed, but visually unexplained at 3-4 m from an actor.
2. **The cone eave hovers tight over the end of the ridge comb.**
   - **Measured clearance:** comb top 5.71 m, cone rafter feet 5.89 m and starter 5.96 m, so only 0.18-0.25 m of air
     under a 0.72 m overhang.
   - **Renders:** from a crane (j12, px ≈ 330-560 / 180-300) and in the j16 corner (px ≈ 1080-1280 / 290-320), the cone
     lip appears to sit on the comb. This is the same "eaves nearly meet" read the redesign was meant to remove. It is
     clean from the official cameras.
   - **Fix:** about 0.3 m more eave, or a lower ridge.
3. **The north flaunching crest is lumpy.** The crest undulates over each thatch course (j10, px ≈ 560-900 / 120-560).
   The flaunching ends in a small pointed toe on top of the north eave roll (j03, px ≈ 460-520 / 190-235). The south
   side is smoother (j09, j13).
4. **The round end now reads as a tower, not a round house end.**
   - **Massing:** a 6.0 m eave on a 7.4 m drum, 11.3 m to the finial, over a 2.3 m body eave (hero, front, back, j18).
     That is about 3.7 m, well over one storey, higher than the body eave.
   - **What still reads as ref1:** the mossy cone, the ball finial and the stone drum.
   - **What is lost:** the low, hunkered ref1 character of round 6. The drum now dominates the longhouse. A drum
     about 0.6-0.8 m lower would still clear the ridge if the cone eave clearance were tuned.
5. **The upper storey is blank.** It has three 0.45 x 0.60 m windows at a 3.7 m sill on a drum about 23 m round
   (front, side, j19). Only one shows in each official view, so the upper storey reads mostly as blank masonry.
   Acceptable, not rich.
6. **Process:** the build is at a work-in-progress path with `_r8` file names, and there is no builder entry. The
   hash-rule and determinism checks are outstanding for the audit.

**Regressions from round 6:**
- None in the body, the gable, the door, the windows, the soffits or the official views.
- The `actor_closeup` dark pocket of round 6 is gone (the junction no longer exists).
- The only loss is massing character (defect 4).

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.3 | Still unmistakably the longhouse with a round stone end under a mossy cone with a ball finial. But the raised drum reads as a tower that dominates the low body, more than the "about one storey" the brief asked for. The ref1 hunkered round house is weakened. |
| 2 Proportion and actor scale | 8.4 | The door (1.00 x 2.10 m), the body eave (2.30 m over the door), the sills and the ground floor of the round end are unchanged and right next to the 1.8 m figure. The upper windows are believable but small for the drum's wall area (j18, j19). |
| 3 Construction logic | 8.4 | The roof is visibly carried and dies into the masonry. The flaunching sits on the covering and is buried in the wall, with no floating abutment or eave pieces (probe). Points off: the aprons stand as unexplained plates, and the cone eave hovers 0.2 m over the comb. |
| 4 Seams and junctions | 8.4 | The junction that failed five rounds is now closed, flashed and free of see-through, along the true curve. All red twins are clean. Points off for the apron tabs, the lumpy north crest with its toe beak, and the tight cone-over-comb slot. |
| 5 Distinctness and reuse | 8.6 | `wall_abutment` is a genuine, generic kit module (any GableRoof, any round body R(z)) that reuses the junctions family. The recipe is declarative, and the eave-crossing machinery is bypassed, not deleted. The round-7 orphans were removed cleanly. |
| 6 Technical compliance | 8.2 | 617k tris (cap 1 M), 9.2 % hidden, 10 slots, `Mask` complete, 89 plausible anchors, no ground dressing. Points off: there is no builder entry, the six-building hash-rule results are referenced but missing, determinism is unverified, and the build is at a WIP path. |

**Verdict: 8.3/10, PASS (>= 8.2).** The pass is subject to the independent audit confirming determinism and the
hash rule. The redesign removes the junction that has failed every audit since round 3, and it replaces it with a
clean, reusable "roof into round wall" module. The remaining defects are cosmetic and none of them shows see-through.

## v3_longhouse_roundend round 8 — sign-off audit: UPHELD-IF-PASSED

Independent auditor, 2026-10-17. Read-only. I built nothing and edited no recipe, kit file or director log.
Audited file: `buildings/variants/v3_longhouse_roundend/redesign_r8_wip/v3_longhouse_roundend_r8.blend` (33 meshes, **617,342 tris**, under the 1,000,000 limit), built by `redesign_r8_wip/build_v3_longhouse_roundend_r8.py` (`linear_roof(clip=inside_round(depth=0.10))` + `roof_junction.wall_abutment`).
Scripts and evidence are in `renders/variants/v3_longhouse_roundend/round_08/audit/`: `a2_measure.py` → `measure.json`, `a3_followup.py` → `followup.json`, `a4_islands.py` → `islands.json`, and close-ups `a01`-`a08*.png` (1280x720, Cycles 24 spp, denoised, OPTIX).
Round centre in world space: (4.61, 0.0), from the cone and finial bounding box. Drum face R(z) = 3.70 - z·tan 1.5°.

### Measurements

| check | result | evidence |
|---|---|---|
| **See-through gaps at the junction** (roof/flaunching/drum) | **0 leaks in 745,302 rays.** Targets were 2 cm behind the drum face, azimuth 110-250° in 1° steps, z 2.0-6.05 m in 2.5 cm steps. Cameras: 62 positions at eye height (1.6 m) and 6 m, 5-12 m out on both sides, plus 6 m gable-end cameras. A leak meant a first hit more than 8 cm inside the face, or sky. A second pass at z 0.05-2.0 m: **0 leaks in 409,550 rays.** | measure.json `leak_count`, followup.json `lowz_leaks` |
| **Roof parts inside the masonry** (target 2-3 cm) | Deepest point inside the face: covering 2.4 cm, eave roll 2.5, ridge 1.9, deck 3.5 (12 verts > 3 cm, none > 5), flaunching/aprons 4.0 (intended 3.5 cm bury; none > 5). Comb and rafters stop 25 cm and 43 cm short of the face. **No roof part is more than 5 cm into the drum.** None of the roof-part vertices deeper than 3 cm is visible from any camera (412 tested). | measure.json `penetration_into_drum`, `visible_deep_roof_verts` |
| **Cone eave over the roof** (the eaves must not cross) | Lowest cone parts: rafters 5.89 m, battens 5.93, starter 5.965, shingles 5.99. Highest thatch under the cone: comb 5.706 m. **Minimum vertical clearance is 0.241 m** (comb tip at (0.48, -0.04, 5.71) to the cone battens). The cone eave lip never meets the thatch, and a05 and a08 show it oversailing clear. | measure.json `cone_clearance_min`, a05_ridge_gable_6m.png, a08_ridge_end_tele.png |
| **Eave-end aprons** | 4 lead pieces (a plate and a closed lip at each eave end) at x 3.05-3.26, y ±3.31-3.45, z 2.60-2.97. They stand 1.6-8 cm proud of the face and nowhere go into it. Both eave rolls end on the apron with no slot (0 leaks). | measure.json `aprons`, a01/a02/a06 |
| **Flaunching** | The radial range against the face is -12.8 cm to +4.0 cm (toe out over the covering, back buried). One run, eave to eave over the ridge, follows the curve on the cylinder (a03/a04). | measure.json `flaunching_depth_range` |
| **Floating pieces** within 0.5 m of the drum | Abutment, eave roll, comb, rafters and deck: none. Three small loose islands: (1) a covering sliver of 10 verts, 0.60 x 0.07 x 0.06 m, at (1.02-1.62, 2.17-2.24, 3.52-3.58), 2.8 cm off its neighbours. It is visible from some cameras, but at 85 mm tele (a07) it cannot be told apart from the course below. (2) A ridge ligger ring of 36 verts at x 0.66, 2.1 cm proud; it reads as a ligger (a08). (3) A 2-tri `LONG_purlin_rings` remnant at (2.5, 2.48, 6.83), 8.7 cm loose, **seen by 0 cameras** (inside the cone void). | measure.json `floating`, islands.json, a07, a08 |
| **Door clearance** (entrance body_wall_3, 1.0 m wide, head 2.22) | The lowest overhead from 0.05 to 1.5 m in front of the door is the rafter feet at **2.317 m** (>= 2.30). The approach is clear: no hit on horizontal rays at 0.3-2.1 m across the 0.9 m opening. | followup.json `door_overhead_min`, `door_approach_blocked` |
| **Mask attribute** | Present on all 33 meshes (`mask_missing: []`). | measure.json |
| **Decal anchors** `decal_anchors_r8.json` | 89 anchors (moss 28, crack 20, lichen 11, damp 10, soot 9, streak 5, patch 3, grime 2, rust 1). All are within 6 cm of a surface (0 far), and the blend holds 89 matching DA_ empties. | measure.json `decal_*` |
| Triangle budget | 617,342 / 1,000,000 | stats.json |

### Visual confirmation
Close-ups at ground level and at 6 m are a01 and a02 (eave ends, eye level, 7.5 m), a03 and a04 (slopes from 6 m), a05 (ridge into the drum from the gable side, 6 m) and a06 (eave look-up). In them the thatch, eave roll and ridge die into the drum under one continuous flaunching. No crossing eaves, no splayed shingle fan, no dark slot and no clipped course is visible. The six official views (hero, front, side, back, aerial, actor_closeup) are clean. The redesign removes the eave-crossing junction behind every rejection from round 3 to round 6.

### Non-blocking notes (for the director; none is visible as a defect from ground level or in quick pans)
1. **`LONG_body_roof_deck` is listed as 100% hidden** in `round_08/hidden.json` (sampled estimate, about 617 of 624 tris). The round-4 audit's note-1 rule says "no object may be 100% hidden", and round 6 had none. The cost is 0.1% of the budget and the deck is the trim reference for the roof. I did not verify this with my own rays. The fix is a cull, or accepting it as structural.
2. The eave-end lead apron reads as a small flat grey plate beside the roll nose (a02, a06), not as lead dressed over it. It is closed and has no gap. This is a matter of taste.
3. `LONG_body_wall_stones` and `_mortar` go up to 17.8 and 23 cm into the drum at the body/drum corner (x 2.28-2.30, y 2.58, z 0-2 m). This is carried over from round 6. The low-z leak pass found no see-through, and actor_closeup shows a clean corner. (My follow-up visibility count for these vertices is not valid: some of its cameras were inside the drum. It is not used here.)
4. The covering sliver (2.8 cm loose) and the 2-tri purlin remnant are cleanup items only.

**Verdict: UPHELD-IF-PASSED.** I found no geometric defect at the new roof-into-round-wall junction, or elsewhere, that should block sign-off at the 8.2 bar.

## PRODUCER NOTE (2026-10-17, session 2): round 8 ACCEPTED

Director 8.3 (pass mark 8.2), independent audit upheld, 617,342 tris (note 15). Round 8 is the deliverable: `buildings/variants/v3_longhouse_roundend/` (recipe, .blend, decal_anchors.json). Round 6 (director 8.1) is archived in `round06_archive/`; its recipe there was reconstructed from the interrupted round-7 file (the `soaker_lean` keyword and the `cone_cut_cover` step removed) and is unverified (its kit import path assumes the parent folder). Round 8 had no builder entry; the HASH RULE check for its kit edits (roof_junction.wall_abutment, rubble_walls open_z, composite inside_box z_fn) and a determinism rebuild of round 8 run in `kit/baseline/6_r8kit_check/`. The non-blocking notes (stuck-on eave-end aprons, 0.24 m cone eave over the comb end, tower-like drum, lumpy north flaunching, `LONG_body_roof_deck` 100 % hidden estimate, three tiny loose islands) are recorded for a later polish pass; no more longhouse rounds this stage.
