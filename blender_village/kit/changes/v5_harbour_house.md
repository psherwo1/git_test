# v5_harbour_house: kit changes (variant builder)

Variant: `buildings/variants/v5_harbour_house/build_v5_harbour_house.py`, approved building 3 -- the timber /
rectangular / waterfront kit family, proved on the harbour house (round 2: the ref4 boat hall).  Recorded here for the
producer to merge into `../CHANGELOG.md` (proposed version 1.12.0).

---

## Round 5 (the client's ref4 eyebrow dormer, `reference/ref4b_eyebrow_dormer_markup.jpg`)

A reusable **eyebrow-dormer add-on** on the soft `GableRoof` / `linear_roof` (docstrings tag it "kit 1.13"; it can
merge with the proposed 1.12.0). Every new option defaults to the old behaviour, so **no hash re-run is needed**.

### `components/linear_roof.py` (existing module: new options only)

- **`GableRoof(..., eyebrows=())`**, plus the spec helper **`eyebrow(x, side=1, **kw)`** and its defaults
  **`EYEBROW`**. The defaults are `d=1.5`, `width=2.0`, `height=0.75`, `flat=0.70`, `plateau=0.18`, `fade=1.20`,
  `lip=0.20`, `set_back=0.04`, `window=dict(width=0.56, height=0.36, sill=0.05)`, `min_front=0.14` and `seed=0`.
  - Each bump is a term in the roof's ONE vertical warp field (`warp_z`).
  - The term is a **step at the front** (slope distance `u_t`). Below it, the slope runs on untouched. Above it, the
    roof is lifted by `height x bell(x)`: full height over `flat`, a cosine fall to 0 at `+-width/2`. Upslope it
    fades smoothly back into the slope (`plateau`, then `fade`), so there are no cheeks, no valleys and no ridge.
  - The front is snapped to the shingle course grid. One whole course (`k_lip`) is the wave's lowest course and
    overhangs the front by `lip` (the little dark eave).
  - Unknown keys raise. A wave that would reach within 0.30 m of the ridge raises.
- **`to_world(P, brow=None)` / `to_local(P, brow=None)` / `warp_z(x, y, brow=None)`**: a new optional argument.
  - `None` means each point is on the lifted side if its own slope distance is `>= u_t`. Queries and walls use this.
  - A number, an array, or `{bump: value}` puts a whole piece on one side, so a piece is never torn across the step.
    `_shingle_courses` passes one value per course; `_deck` passes one value per row.
  - Without `eyebrows` the argument is ignored: the result is bit-identical.
- **Every roof part follows the bump:**
  - `_shingle_courses`: a course is wholly lifted (`k >= k_lip`) or not. Courses under the wave stop their heads at
    the deck front. The eave course over the window gets closed undersides (`bottom=True`).
  - `_deck`: extra rows at the tear (`u_t - 1 mm`, `u_t`) and a fine grid over the wave. The deck becomes a closed
    vertical **deck front** under the wave, with a **framed opening** behind the window: the cells are removed and
    the cut edges are closed.
  - `_brow_eave_strip`: a lifted board strip under the wave's eave course (`u_lip` to `u_t`, from the deck underside
    to 5.5 cm over the deck), so no slot shows under the eave.
  - The rafters, comb, verge boards, eave and finials are outside the wave's footprint and are unchanged. The wave
    must stay 0.30 m under the ridge.
- **`_eyebrow_fronts(g, roof, pre)`**: `linear_roof` calls it when the roof has eyebrows, with its own seeded rng, so
  the roof's other random draws are unchanged. It builds:
  - a sill beam on the slope;
  - the timber family's rough board-and-batten cladding (`timber_walls._clad`), clamped to the wave's eave strip, so
    the front IS the wave's arch;
  - a closed backing (`timber_walls._sheet`) cut only at the clear opening, and end posts;
  - the **kit window**: `components.openings.window` resolved by `timber_walls.resolve_timber` and built by
    `wall_openings.build_opening(host=timber)`. It is the cross-mullion two-light frame, with no shutters and a dark
    room sized to stay under the wave.
  - The front is built where the gap is at least `min_front` tall. Beyond that, the deck front closes it.
  - It raises if the window head would cross the wave's eave.
  - Output objects: `<P>_<roof>_eyebrow<i>_frame`, `_boards`, `_blocker`, and `_frames` / `_blockers` (the window).
  - It publishes `roof.EYEBROW_FRONTS`.
- `linear_roof` raises if `eyebrows` is used with a thatch covering. Only shingle is built.

### `components/timber_walls.py`, `components/wall_openings.py` (existing modules: one new option)

- The timber window's `TIMBER_OPENING["window"]` gains `room_pad=(0.35, 0.6, 0.35)`: (side, below, above) margins of
  the dark room past the clear opening. These are the old hard-coded values, so it is identical by default.
  `_build_timber_opening` reads it. The eyebrow window uses `(0.05, 0.10, 0.04)` and a 0.45 m room.

### Hash rule

- Not triggered. No existing default changed: the empty `eyebrows`, `brow=None` and the default `room_pad` reproduce
  the old code path exactly. With no bumps, `_deck` builds the same grid and the same face order, and
  `_shingle_courses` builds the same pieces with the same rng draws.
- No `v5r5_hash` run.

### Known limitations (round 5)

- Shingle coverings only. A thatch eyebrow would need the course sheets split at the step.
- The bump is vertical only. Over the steep part of its flanks, the shingles shear (they follow the field exactly).
  A `width` of 2.0 m or more with `flat` at or under about 0.6 keeps this soft.
- One front per bump, on a straight slope. A bump must not overlap a verge, the eave band, another bump or a
  junction body; this is not checked.

---

## Round 4 (the client's broader, slumped hall roof)

**No kit module changed.** The wider, lower, more slumped hall is a recipe parameter change on `DIM` / `MAIN`
(`half` 3.0 -> 3.5, `pitch` 58 -> 49, `ridge_sag` 0.24 -> 0.50, overhang 0.45 -> 0.70, `eave_sweep` 0.28 -> 0.40
over 1.5 m, `clear` 4.6 -> 5.0; the CLIENT DIRECTION of 14:10 superseded a first 53.5 deg / 0.42 m build). Every plan coordinate in the
recipe (hall faces, slip, quay ends, jetty, ladder, moorings, door, path run distances) now derives from `DIM`, so the
roof change re-fitted `stone_quay` (quoin bond at the moved slip mouth), `cruck_frame` (span, tie, responds),
`path_stone_wall` (wall heads), `wall_abutment` and the seal probe by themselves. No hash re-run is needed.

---

## Round 3 (the four waterline must-fixes of the round-2 grade)

All four are kit fixes, so the boathouse inherits them.

### Existing module: one new option (the default keeps the old behaviour; hash rule `kit/baseline/v5r3_hash/`)

- **`rubble_walls.path_stone_wall(..., flush_runs=None)`**: the run indices (run i = `path[i] -> path[i+1]`) whose
  footing course is laid FLUSH. These are ordinary face stones of the footing course's height and lengths, with the
  kit `front` projection and no field-stone bulge (`foot` flag cleared before `polygonize` / `rough_footing`, own
  stream `seed + 19`). It is for walls standing flush on a quay face, where the projecting footing would hang over
  the water. `None` takes exactly the old code path (the `_path_stone_wall_based` call is unchanged).

### v5-only modules (no other building imports them)

- **`cruck.cruck_frame`**:
  - `pad_clip_z=None`: the finalize clip of the pad stones. None gives the kit's -5 cm clip, or just under
    `respond_z` when responds are built.
  - `respond_z=None` (with `respond_ch=(0.40, 0.56)`): carry each pad down to `respond_z` as a dressed stone
    RESPOND of the pad's plan. Courses have 1.2 cm joints and alternate courses are set back 1.5 cm. The joints
    are closed by an inset core `<P>_<name>_respond_blocker`, which is never culled. The respond has its own
    stream (`seed + 5`), so the frame's members are unchanged.
  - `king_strut=True`: False drops the tie-to-collar king strut. With `pointed=True` the pointed arch carries the
    collar; the strut inside it read as "a lancet with a cross".
  - Defaults reproduce the round-2 frame.
- **`waterfront.stone_quay(core_blocks=True)`**:
  - The recessed joint backing is now its own object, `<P>_<name>_backing_blocker`. The name falls in
    `composite.BACKING`, so `composite_hidden_cull` never removes it from behind a visible joint (producer note 6).
  - Course beds are drawn once per face group (`_block_courses`) and shared by its runs.
  - Every CONVEX corner between two water runs is quoin-bonded (`_core_blocks(quoin=(p0, p1))`). On alternate
    courses one run's end block runs through the corner to the other face (`BLOCK_FACE` in from the corner), and the
    other run butts its back (`BLOCK_DEPTH + gap/2`). The backing stops at the other run's backing face, so it is
    closed round the corner with nothing past either face.
  - The plain-end, concave-corner and `core_blocks=False` behaviour is unchanged.

---

## Round 2 (the ref4 boat hall; reuse mandate, note 16, note 17)

### Summary

- **Existing modules changed (optional parameters / new functions, defaults = kit 1.11.0 behaviour):**
  `linear_roof`, `rubble_walls`, `wall_openings`, `board_belt`, `composite`.  Hash rule re-run: step
  `kit/baseline/v5r2_hash/` (result in the round-2 builder entry of `director/log_variant_v5_harbour_house.md`).
- **New module:** `components/cruck.py` (`cruck_frame`).
- **Round-1 modules reworked (no other building uses them):** `timber_walls` (openings moved onto
  `wall_openings.build_opening(host=...)`, head rule, rough / bow options), `waterfront` (`stone_quay` replaces
  `crib_quay`).
- **Retired (reuse mandate):** `timber_roof.verge_boards` (folded into `linear_roof(verge="board")`, without the
  crossed horns) and `timber_finish` (folded into `composite_hidden_cull(parts=)` / `composite_decals(timber=,
  waterfront=)`).  Both files are now pointer stubs that raise `NotImplementedError` (deleting them was refused by the
  session's permission guard; the producer can delete them at the merge).  `waterfront.crib_quay` is removed.
- `floor_stack` is kept unchanged (clean; the ref4 hall has no jettied floor).

### Existing modules: new options (defaults keep the old behaviour)

| module | parameter / function | what it does |
|---|---|---|
| `linear_roof.GableRoof` | `ridge_sag=0, eave_sag=0, eave_sweep=0, sweep_len=1.0, verge_flare=0, flare_len=1.6, wave=0, wave_seed=33` | **note 17 soft lines as ONE vertical warp field** `warp_z(x, y)`: a parabolic ridge (and eave) sag, a bell-cast / swept eave (the lip lifted, fading quadratically over `sweep_len` m in from it, so the slope flattens toward the eave), an apex flare at every free verge (fading along the ridge and toward the eave: the verge line curves up to the apex), and a low-frequency +-`wave` out-of-true.  `to_world` adds it, `to_local` removes it, so every part `linear_roof` builds and every query (`keep_out`, `top_depth`, `under_soffit`, `eave_zone`) follows it.  All zero: `warped = False`, `to_world` / `to_local` bit-identical. |
| `linear_roof.GableRoof` | `warp_z(x, y)`, `under_z_world(P)` (new methods) | the warp, and the warped deck underside over world points (what walls / frames stop at) |
| `linear_roof._deck` | (warped roofs only) denser stations across and along the slope | the sarking deck follows the curved warp, so no shingle sinks into it |
| `linear_roof.linear_roof` | `verge=None` / `"board"` | the bargeboard of every free verge (`VERGE_BOARD`, `_verge_boards`; folded from the retired `timber_roof.verge_boards`, **no horns**), laid in the roof's local frame so it follows the warp: a sagging / flared roof gets the curved, apex-flared bargeboard of ref4; its eave foot curls up 5 cm -> `<P>_<roof>_verge` |
| `linear_roof.linear_roof` | `apex_finial=None` / `"turned"` | the village finial on each free gable apex: `finial.turned_finial` (the keep's turned / spike finial) on a `finial.lead_hat` fitted over the comb / covering / verge vertices under it (`_apex_finials`) -> `<P>_<roof>_apex_cap_collar`, `_apex_finial` |
| `linear_roof.linear_roof` | the plain (shingle / clumps) path now passes `rafter_skip` / `verge_apex` to `_rafters` when given | as on the thatch "courses" path; absent = the old call |
| `rubble_walls.path_stone_wall` | `base=None, clip_z=None` | the course base z (None = -0.10) and the finalize clip (None = the land clip): a quay wall stands on the harbour bed.  `None, None` runs the old literals. |
| `rubble_walls._quoin_courses` | `z0=-0.04` | the first quoin course's base (the same default) |
| `rubble_walls` | `RUBBLE_LARGE` (new constant) | a `cfg=` override with the larger courses / longer stones of the bible's range (~30 % fewer stones; README section 4's note-15 approach) |
| `wall_openings.build_opening` | `host=None` / `dict(...)` | **the timber host** (`TIMBER_HOST`, `_build_timber_opening`): the kit's ONE opening builder now also builds doors, windows and large boat / barn doors in timber walls -- jambs, heads, timber sills, the window frame and cross mullion, every leaf and shutter from `plank_doors.plank_leaf`, forged straps (`plank_doors.strap_widths`) on the leaves, the pooled `plank_doors.make_pintle` (linked duplicates, note 3) in the jamb, ledged-and-braced boat leaves, built-in stone steps, dark rooms.  `host=None`: the masonry opening, unchanged. |
| `wall_openings` | `TIMBER_HOST["head_rule"]` = `"clamp"` / `"trim"` | **a door / boat door never crosses the storey head**: "clamp" -- the clear height is clamped so the plate is the lintel (leaves 1 cm under it, no separate head beam; raises under 1.8 m / 2.0 m); "trim" -- the plate is cut between the jambs and the head beam replaces it flush at the plate's own depth and top (raises if the beam would be < 0.15 m); anything else raises.  The record's `z1` is the EFFECTIVE clear head, so the clearance guard reports it. |
| `board_belt.board_belt` | `body=None, gaps=(), foot_ring=False, openings=()` | the belt on a plain round body (`dict(center, r, z0, z1)`, `z1` may be callable(g)) on any frame -- e.g. the timber top storey of a `round_stone_body` tower under a `cone_roof` on a RoundFrame; window gaps; a second hewn ring (the timber sill band) round its foot; small cased windows from `wall_openings.build_opening(host=...)`.  `body=None`: the tier-family belt, unchanged. |
| `composite.composite_hidden_cull` | `parts=None` | only objects whose names contain one of these fragments are targets; `BACKED_PARTS` (new constant, folded from `timber_finish.CULL_PARTS` + the cone / quoin / ring parts) = the parts that always have a closed backing |
| `composite.composite_decals` | `timber=False, waterfront=False` | + `timber_anchors` (timber walls, cruck frames, board belts) and `waterfront_anchors` (damp / moss ONLY on quay water faces and piles, z -0.9 .. 0; lichen on the quay copings).  The old body is `_composite_decals`, called unchanged. |

### New module: `components/cruck.py`

- `cruck_frame(g, name, O, t, n, half, top_fn, z_pier, clear, spring=2.2, tie=0.28, member_w=(-0.28, 0.02), post=0.24,
  arch_t=0.24, blade=0.30, collar_at=0.50, collar=0.22, braces=True, pads=True, infill="plank", infill_w, backing_w,
  rough=True, seed=901)`: the cruck / arched-brace gable frame over a wide opening on stone piers -- a tie beam on
  the pier tops, jamb posts on dressed pad stones inside the stone jambs, two segmental ARCHED BRACES springing from
  the posts and meeting under the tie (round / segmental only, bible 1.8), a king strut, curved BLADES following the
  rake (`top_fn`: a warped roof gives curved blades) with an elbowed inner edge, a collar on CURVED BRACES, a king
  post at the apex, and ROUGH plank infill (the `timber_walls` board machinery) on a closed backing over the upper
  gable and the arch spandrels.  The opening is open (boats moor inside).  Publishes `g.CRUCKS`.
- **Why new:** nothing in the kit builds curved timber members, an arch framed in timber, or a gable frame over an
  opening (the keep's `hewn` / `timber` pieces are straight posts, plates and braces of the hut / keep families).

### Round-1 modules reworked

- **`timber_walls`**:
  - `_build_opening` (round 1: its own leaves, frames, shutters, steps, straps) is retired: openings call
    `wall_openings.build_opening(host=...)`, so the barn / boathouse doors are the village's doors.  The new
    wrapper `_build_opening` only builds the host dict.  Objects are now `<P>_<name>_frames`, `_ironwork`,
    `_blockers`, `_dressed` (wall_openings' names) + pooled `<P>_pintle_###`.
  - The plate is split at a "trim" door (`_plate_cut`).
  - `path_timber_wall(rough=None, bow=0.0, head_rule="clamp")`: `ROUGH` (board widths 0.16-0.40 m log-uniform with
    12 % fillets of 8-12 cm, +-1 deg out of true, sagging long rows / plates, 1.4 cm split arrises, +-1.5 cm uneven
    ends, 3.2-4.2 cm boards, +-5 mm depth jitter so leaning neighbours overlap in depth, never in one plane); `bow`
    m: every run bows out of true at mid-run (all pieces, the backing and the openings follow it).
  - Helpers `rough_opts`, `board_widths` (shared with `cruck`), `resolve_timber`; `wbox(tilt, sag, floor)` and the
    run frame's optional 4th element `bow(s)`; `roof_top_fn` reads `under_z_world` on a warped roof.
  - `boat_door(head_rule=None)`.
- **`waterfront`**: `stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, cfg=None, seed=651)` -- a quay edge
  of large blocks (`path_stone_wall` with `QUAY_BLOCKS`, `base=bed_z`); only the WATER runs are built (to the bed),
  land runs are left to the terrain (note 6: nothing deeper than 5 cm on land); `g.QUAYS` carries the water faces for
  the waterline anchors.  `crib_quay` removed.

### Round 2, relaunched fixer (12:10 onward): v5-only modules only, no existing module touched

- **`cruck.cruck_frame`**: new options `brace=0.17` (the collar braces' face width, was a literal 0.17) and
  `pointed=False, pointed_t=0.26, pointed_at=0.74` -- a two-centred POINTED ARCH of two curved timbers springing
  from the tie beam at `+-pointed_at * s_tie` and meeting under the collar at the king strut (ref4's inner gable
  arch; raises when there is no room).  Defaults = the 11:00 frame.  The recipe uses heavier members
  (`member_w=(-0.30, 0.06)`: the frame stands 6 cm proud of the stone face and the infill sits 15-18 cm behind the
  member faces; `post=0.30, arch_t=0.34, blade=0.40, tie=0.32, collar=0.26`), `pointed=True`, `braces=False`.
- **`waterfront.stone_quay`**: new option `core_blocks=False` -- the submerged core under `detail_z` is laid as
  low-poly LARGE BLOCKS (`_core_blocks`: courses 42-58 cm, blocks 0.85-1.55 m, broken joints, ~60 tris a block, a
  little out of line) on a recessed joint backing, instead of one flat slab per run (the slab read as "vertical
  planks" in the clay views).  With `detail_z >= top_z - 0.05` the WHOLE face is that block masonry with a flush
  coping course (no rubble band); the recipe uses `detail_z=QZ, core_blocks=True` -- the rubble quay stones (~58k
  tris that `hidden_tris.py` counts as buried below z -0.05) are gone, hidden 20.4 % -> 13.5 %.  Block / backing
  material `M_stone` (the palette; the old slab's `M_rubble` would be a 10th slot).
- **Hash rule:** no existing module changed in this pass.  Because the earlier fixer edited `rubble_walls` at
  11:06, after the hilltop_keep / wattle_roundhut / tower_windmill builds of `v5r2_hash` had started (10:52 /
  10:57 / 11:05), those three were rebuilt into `kit/baseline/v5r2b_hash/` (result in the builder entry).

### Known limitations (round 2)

- `GableRoof` warp: `ref_z` / `under_z` / `top_z` / `section_columns` stay the straight local profile (callers that
  need the warped deck use `under_z_world`); the warp is vertical only (no plan bow of the eave line).
- `cruck_frame` is symmetric about the gable centre; one opening per frame.
- `stone_quay` water runs end in open stone sections where the quay continues in the terrain.
- `board_belt(body=...)`: lookouts only (no doors); the window gaps cut whole boards.
- The eyebrow dormer, the curved stair round the tower and the small round store are not built (recipe choice).

---

## Round 1 (superseded where round 2 says so)

Only new modules: `timber_walls` (`path_timber_wall`, `boat_door`, `rect_path`, `side_s`, `rect_openings`,
`roof_top_fn`, `wbox`), `floor_stack` (`jetty_floor`, `timber_storeys`), `waterfront` (`pile`, `pile_deck`,
`crib_quay` -- removed in round 2, `ladder`), `timber_roof` (`verge_boards` -- retired in round 2), `timber_finish`
(`timber_hidden_cull`, `timber_decals` -- retired in round 2).  No existing module changed; no hash re-run needed.
