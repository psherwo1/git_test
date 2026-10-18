# village_kit CHANGELOG

## Kit edit rules (all agents)

- You may ADD modules, functions, and optional parameters whose defaults keep the old behaviour.
- Never change the behaviour or the signature of an existing kit function that another building uses.
- After any kit edit:
  1. re-run every OTHER building script that imports `village_kit`;
  2. confirm it still builds without errors;
  3. confirm its triangle count is unchanged (within ±0.5 %);
  4. record the edit below, with the buildings you re-ran.
- Since kit 1.9.0 the guard-rails (`village_kit/guards.py`: clearance, decal_validate, seal_probe, steep_cone_door,
  lod_scope) run on every build by default.  Never switch one off silently: a recipe opts out per guard (per junction
  for the seal probe) with a logged reason (`village_kit/README.md` section 3).  Since kit 1.8.0 the target is hash
  identity (`tools/build_baseline.ps1`, `tools/geom_hash.py`, `tools/geom_diff.py`), not only the +-0.5 % count.
- Since kit 1.10.0 every building's final UVs and walked-top Mask B come from `village_kit/uvgrain.py` /
  `mask.clear_walked_tops` (README section 3a).  A UV change must keep the geometry hash; measure it with
  `tools/uv_audit.py` (grain, collapsed UVs, walked tops).

Kits 1.11.0 and 1.12.0 merge the variant builders' modules (below).  The current reference table (eight buildings) is
in the 1.12.0 Verification section.

**Reference builds at kit 1.10.1** (fingerprints in `kit/baseline/5_determinism/`; the keep and v3 were rebuilt 3x
with identical hashes):

| Building | Imports village_kit since | Triangles | Geometry hash (1.10.1) |
|---|---|---|---|
| wattle_roundhut | 1.0.0 (round 8) | 878,355 (876,619 before v4's closed 3 cm eave band, accepted by the producer as the reference) | 7e5e7c2df5c4d367 |
| hilltop_keep | 1.1.0 (round 7) | 1,166,874 | 3e2a219a5901afc5 (canonical 1fb5d4f5fe54ccc6) |
| tower_windmill | 1.2.0 (round 7) | 1,146,243 | 89bf4a2a2c60e049 |
| v1_stone_watchtower | variant | 1,057,164 (over note 15; to be reduced) | 47e4208df661a5a9 |
| v2_tiered_hall | variant | 954,925 | 87ba64b7f9d4a746 |
| v3_longhouse_roundend | variant | 483,508 (1.9.0 clearance fix) | 8a4e59687b3c7c4d (canonical c827824da304778d) |
| v4_mixed | variant, accepted | 938,453 | 2e87caad61b68d34 |

---

## 1.12.0 (2026-10-17): timber / waterfront family, soft roofs, eyebrow and barn options (producer)

Housekeeping step of the client's "Move forward with the quick fix, the housekeeping, and the add ons".  Two variant
builders added modules and options under the kit edit rules after 1.11.0.  v5 harbour house (rounds 1-8) added the
timber / rectangular / waterfront family, the soft `GableRoof` warp and the eyebrow-dormer add-on.  v6 barn (rounds
1-3) added the barn options on the same family.  This release merges them into one record.  The full per-round records
(signatures, proofs, hash re-runs) stay in `kit/changes/v5_harbour_house.md` and `kit/changes/v6_barn.md`.  The notes
proposed other version numbers, and they are superseded by this release: 1.12.0 for v5, the docstring tags "kit 1.13" /
"1.14" / "1.15" (v5 rounds 5 / 6 / 8), and 1.16 / 1.17 / 1.18 (v6 rounds 1 / 2 / 3).  The module docstrings still carry
those tags; they were not retagged here.  This release does not include the add-on work started after the merge.

### New modules

- **`components/timber_walls.py`** (v5 r1, reworked r2; options v5 r5-r6, v6 r1): the timber family's walls.
  `path_timber_wall(g, name, path, z0, top=2.6, top_fn=None, style="post_plank", gable_style="board_batten",
  openings=(), ..., backing=True, seed=301, ground_z=0.0, rough=None, bow=0.0, head_rule="clamp")` builds a post /
  plank (or board-and-batten gable) wall along a plan polyline on a sill beam, with plates, a closed backing and
  cladding up to a roof (`roof_top_fn(roof, tuck=0.02)`, which reads `under_z_world` on a warped roof).  Its options
  are `rough` (`ROUGH`: uneven board widths, fillets, out-of-true, sag, split arrises) and `bow` (every run bows at
  mid-run).  Also `boat_door(width=2.6, height=2.6, leaves=2, ..., head_rule=None, to_ground=False, pad=None)`,
  `loft_door`, `hoist_beam`, `rect_path`, `side_s`, `rect_openings`, `wbox`, `rough_opts`, `board_widths` (shared with
  `cruck`), `resolve_timber` and `TIMBER_OPENING`.  Since round 2 every opening is built by
  `wall_openings.build_opening(host=...)`, so the timber doors are the village's doors.  Used by v5 and v6.
- **`components/floor_stack.py`** (v5 r1, unchanged since): `jetty_floor(g, name, lower, z, jetty=None,
  joist=(0.15, 0.20), spacing=0.45, rim=0.20, proud=0.04, soffit_t=0.03, tail=0.70, seed=0)` builds the floor band
  between two storeys.  On a jettied side the joist ends show and the soffit is closed; elsewhere a rim beam closes the
  band.  `timber_storeys(g, name, rect, z_base, storeys, jetty=None, roof=None, floor=None, seed=500)` stacks
  `path_timber_wall` storeys with a jetty floor between each pair and publishes `g.STOREYS`.  Kept clean, but no
  building builds it (the ref4 hall has no jettied floor).
- **`components/waterfront.py`** (v5 r1, reworked r2, r3): `pile(..., r=0.13, lean=0.01, taper=0.12, cap=True)`,
  `pile_deck(g, name, rects, deck_z=0.5, bed_z=-2.5, ...)`, `ladder(g, name, top, out, z_bot, width=0.46, ...)`, and
  `stone_quay(g, name, path, top_z=0.0, bed_z=-2.5, water=None, cfg=None, seed=651, coping=True, detail_z=-0.9,
  core_blocks=False)`.  `stone_quay` is a quay edge of large blocks (`path_stone_wall` with `QUAY_BLOCKS`,
  `base=bed_z`).  Only its water runs are built down to the bed (note 6), and `g.QUAYS` carries the water faces for the
  waterline anchors.  Round 2 replaced `crib_quay` with `stone_quay` and removed `crib_quay`.  Used by v5.
- **`components/cruck.py`** (v5 r2; options v5 r2-r3, v6 r2-r3):
  `cruck_frame(g, name, O, t, n, half, top_fn, z_pier, clear, spring=2.2, tie=0.28, member_w=(-0.28, 0.02), post=0.24,
  arch_t=0.24, blade=0.30, collar_at=0.50, collar=0.22, braces=True, pads=True, infill="plank", ..., rough=True,
  seed=901, ...)` is the cruck / arched-brace gable frame over a wide opening.  It has jamb posts on dressed pads,
  segmental arched braces, curved blades following the rake (a warped roof gives curved blades), a collar on curved
  braces, and rough plank infill on a closed backing.  It publishes `g.CRUCKS`.  It is new because the kit had no
  curved timber members and no arch framed in timber.  v6 r2 added `arched_doors` (below).  Used by v5 (the water
  gable) and v6 (the cart entry).
- **`components/timber_roof.py`, `components/timber_finish.py`** (v5 r1, retired r2 under the reuse mandate):
  `timber_roof.verge_boards` is folded into `linear_roof(verge="board")`, without the crossed horns.
  `timber_finish.timber_hidden_cull` / `timber_decals` are folded into `composite_hidden_cull(parts=BACKED_PARTS)` /
  `composite_decals(timber=True, waterfront=True)`.  Both files are pointer stubs that raise `NotImplementedError`, and
  nothing imports them.  See "To delete".

### Optional parameters added to existing modules

New functions in existing modules are listed here too.  "Existing" means that the module existed before the
builder's round.  `timber_walls`, `waterfront` and `cruck` are this release's own new modules.

| module | parameter / function | added by | default keeps old behaviour? |
|---|---|---|---|
| `linear_roof` | `GableRoof(ridge_sag=0, eave_sag=0, eave_sweep=0, sweep_len=1.0, verge_flare=0, flare_len=1.6, wave=0, wave_seed=33)`: the note-17 soft lines as ONE vertical warp field, followed by every part and query; new methods `warp_z(x, y)`, `under_z_world(P)`; denser `_deck` stations on warped roofs only | v5 r2 | yes (all zero: `warped = False`, `to_world` / `to_local` bit-identical) |
| `linear_roof` | `linear_roof(verge=None)` (`"board"`: `VERGE_BOARD`, `_verge_boards`, the curved, apex-flared bargeboard), `apex_finial=None` (`"turned"`: `finial.turned_finial` on a fitted `finial.lead_hat`, `_apex_finials`); the plain path passes `rafter_skip` / `verge_apex` when given | v5 r2 | yes |
| `linear_roof` | **the eyebrow-dormer add-on**: `GableRoof(eyebrows=())`, `eyebrow(x, side=1, **kw)`, `EYEBROW` (`d=1.5, width=2.0, height=0.75, flat=0.70, plateau=0.18, fade=1.20, lip=0.20, set_back=0.04, window=dict(width=0.56, height=0.36, sill=0.05), min_front=0.14, seed=0`); `to_world` / `to_local` / `warp_z(..., brow=None)`; `_brow_eave_strip`; `_eyebrow_fronts` (own seeded rng, kit window via the timber host, publishes `roof.EYEBROW_FRONTS`).  It raises with thatch, with unknown keys, and with a wave within 0.30 m of the ridge | v5 r5 | yes (no bumps: the same grid, face order and rng draws) |
| `linear_roof` | `EYEBROW` keys `tilt=False`, `span_rows=False` (`_deck` split into `_deck` + `_deck_slab`: the old arrays in the old order without it), `eave_inset=0.0`, `close_ends=False` | v5 r6 | yes |
| `linear_roof` | `EYEBROW` keys `profile="bell"` (`"arch"`: one continuous `(1 - t^2)^2` arch, `GableRoof.brow_bell`, flanks at most 40 deg, `flat` ignored, other values raise) and `respace=False` (`_brow_respace`: even course spacing over the roll, monotone in `u`, no rng draws) | v5 r8 | yes |
| `linear_roof` | `GableRoof(eave_lifts=())` + `eave_lift()` / `EAVE_LIFT` (a soft arched eave lift over a wide door, a warp term that works on thatch and shingle); `GableRoof(ridge_seat=False)` (thatch ridge-roll flanks seated 3 cm under the covering) | v6 r1 | yes (`()` leaves `warped` / `warp_z` bit-identical) |
| `linear_roof` | `linear_roof(verge_roll=False)` (`VERGE_ROLL`, `_verge_rolls`, `_verge_roll_path`, `_LocalAcc`: one continuous rolled thatch edge, raises without two free verges), `comb_step=0.92`, `comb_backing=False`, `rafter_lift_max=None` (+ `GableRoof.lift_z`); private `_verge_faces(u_from=None, top_max=None)`, `roof._deck_round`.  With `ridge_seat` the binding spars now follow `_ridge_centre(x)` | v6 r2 | yes (the spar change is gated by the barn-only `ridge_seat`) |
| `linear_roof` | `VERGE_ROLL["apex_bend"]=None` (+ `_apex_bend`: the rake rolls bend over the apex in one sweep), `VERGE_ROLL["bend_over"]=0.24` | v6 r3 | yes (read only by `verge_roll`) |
| `timber_walls` | the round-2 rework: `path_timber_wall(rough=None, bow=0.0, head_rule="clamp")`, `boat_door(head_rule=None)`, `wbox(tilt, sag, floor)`, the run frame's optional 4th element `bow(s)`, `rough_opts`, `board_widths`, `resolve_timber`, `_plate_cut`; its own `_build_opening` was retired for `wall_openings` | v5 r2 | the new options yes; the round-1 openings and object names changed (only v5 built the module) |
| `timber_walls`, `wall_openings` | `TIMBER_OPENING["window"]["room_pad"]=(0.35, 0.6, 0.35)` | v5 r5 | yes (the old literals) |
| `timber_walls`, `wall_openings` | `TIMBER_OPENING["window"]["lights"]=4` (`2`: one vertical mullion, no transom) | v5 r6 | yes |
| `timber_walls`, `wall_openings` | `boat_door(to_ground=False, pad=None)` (a cart door from the ground on dressed stone pads, `_sill_cut`, `rec["sill_cut"]`); `window(gable=False)` (an opening above the plate, its head checked against the rake); `lights=0` (an open opening); `loft_door(width=1.20, height=1.70, sill=2.60, ...)`; `hoist_beam(g, name, at, out, z, length=1.10, tail=0.45, ...)` (new kit component); private `_build_opening(face=None)`, `_opening_layout(ground=None)`; backing z rows clamped at the sill line | v6 r1 | yes (the backing rows are the same set for every existing opening) |
| `wall_openings` | `build_opening(host=None)` (`TIMBER_HOST`, `_build_timber_opening`: the timber host builds doors, windows and boat doors in timber walls), `TIMBER_HOST["head_rule"]` = `"clamp"` / `"trim"` | v5 r2 | yes (`host=None`: the masonry opening, unchanged) |
| `rubble_walls` | `path_stone_wall(base=None, clip_z=None)`, `_quoin_courses(z0=-0.04)`, `RUBBLE_LARGE` (a `cfg=` override) | v5 r2 | yes (`None, None` run the old literals) |
| `rubble_walls` | `path_stone_wall(flush_runs=None)`: flush footing courses on the listed runs (own stream `seed + 19`) | v5 r3 | yes (`None` is the old code path) |
| `board_belt` | `board_belt(body=None, gaps=(), foot_ring=False, openings=())`: the belt on a plain round body on any frame | v5 r2 | yes (`body=None`: the tier-family belt) |
| `composite` | `composite_hidden_cull(parts=None)`, `BACKED_PARTS`; `composite_decals(timber=False, waterfront=False)` (+ `timber_anchors`, `waterfront_anchors`; the old body is `_composite_decals`, called unchanged) | v5 r2 | yes |
| `composite` | `composite_decals(timber_soot=True)` -> `timber_anchors(soot=)`: `False` drops the soot over timber openings only | v6 r2 | yes (the same call and the same rng draws) |
| `waterfront` | `stone_quay` replaces `crib_quay` (removed); `stone_quay(core_blocks=False)` (the submerged core as low-poly large blocks on a recessed backing) | v5 r2 | `crib_quay` removed (only v5 used it); `core_blocks` yes |
| `waterfront` | the `core_blocks=True` path: the joint backing is its own `<P>_<name>_backing_blocker` (in `composite.BACKING`); course beds per face group; convex water corners quoin-bonded | v5 r3 | `core_blocks=False` unchanged; the `True` path changed (only v5) |
| `cruck` | `cruck_frame(brace=0.17, pointed=False, pointed_t=0.26, pointed_at=0.74)` | v5 r2 (relaunched fixer) | yes (the 11:00 frame) |
| `cruck` | `cruck_frame(pad_clip_z=None, respond_z=None, respond_ch=(0.40, 0.56), king_strut=True)` (stone responds with their own stream `seed + 5`) | v5 r3 | yes (the round-2 frame) |
| `cruck` | `arched_doors(g, name, frame=None, leaves=2, setback=0.012, ..., lap=0.06, rough=True, strap=True)` (new kit component: round-headed plank cart doors); `g.CRUCKS` entries gain `a_in`, `R`, `zc`, `member_w`, `post` | v6 r2 | yes (record keys only; no geometry change for v5) |
| `cruck` | `cruck_frame(pad_top=None, gate=None)` + `_gate` (clearance envelopes, a FAIL raises `guards.ClearanceError`; sets `g.CRUCKS[-1]["gate"]` and `g.CRUCK_ENTRANCES`) | v6 r3 | yes (`None`: the same post / pad calls, no attribute set) |
| `guards` | `entrances_of(g)` also reads `g.CRUCK_ENTRANCES`, so the eave-lip gate checks a gated arch like a door | v6 r3 | yes (only `cruck_frame(gate=...)` sets it) |

### Behaviour changes to existing defaults

- **None.**  No default that another building reaches changed.  The notes record every change to an existing module
  as a new option, key or function whose default takes the old code path, with no rng draw added or moved.  This is
  stated in each round's "Hash rule" section of `kit/changes/v5_harbour_house.md` and `kit/changes/v6_barn.md`.  The
  hash runs confirm it.  The notes point to the director logs for the results:
  - **`kit/baseline/v5r2_hash/`** (10:52-11:28, all seven) and **`v5r2b_hash/`** (12:13-12:30, the keep, hut and mill
    rebuilt after the late `rubble_walls` / `board_belt` edits): "all seven buildings MATCH the 1.11.0 reference
    (geometry, UV and Mask)" (`director/log_variant_v5_harbour_house.md`, round-2 builder entry, "Hash rule").
  - **`kit/baseline/v5r3_hash/`** (13:09-13:45): "All seven MATCH the kit 1.11.0 reference (`6_r8kit_check`) on
    geometry, UV and Mask", re-checked by the director in the round-3 grade (same log, round-3 entry).  v5 rounds 4
    and 7 were recipe-only.  Rounds 5, 6 and 8 were defaults-off and had no run.
  - **`kit/baseline/v6r3_hash/`** (the audit condition for the barn's round 3, all eight rebuilt with the kit of that
    time): "keep, hut, mill, v1, v2, v3 and v4 are identical to `6_r8kit_check` on all three hashes (geometry, uv,
    mask); `geom_diff`: no object differs.  **v5 is per-object identical to `7_v5_ref`**" (geometry
    `c3d3a5343572dc73`, 714,452 tris) (`director/log_variant_v6_barn.md`, round-3 audit, "hash rule" row).  This run
    covers the whole release: v5 rounds 5-8 and v6 rounds 1-3.  `v6_barn.md`'s round-3 section says "Not triggered;
    not run".  It was written before the audit ran it.
- **Changes inside this release's own modules**, made before another building used them (recorded above, not
  defaults that another building reached): v5 r2 reworked `timber_walls` (openings moved onto `wall_openings`, so the
  object names changed) and `waterfront` (`crib_quay` removed), and retired `timber_roof` / `timber_finish`.  v5 r3
  changed `stone_quay(core_blocks=True)` (its own backing object, quoin-bonded corners).  v6 r2 made the barn-only
  `ridge_seat` option (v6 r1) also re-lay the binding spars.

### To delete (producer)

- `kit/village_kit/components/timber_roof.py` and `kit/village_kit/components/timber_finish.py`: the retired pointer
  stubs (v5 r2; deleting them was refused by the builder's permission guard).  No building or kit module imports them
  (`buildings/**/*.py` has no reference).  They were not deleted in this merge.

### Known limitations

The 1.11.0 list still stands.  This release adds:

- `GableRoof` warp (v5 r2): `ref_z` / `under_z` / `top_z` / `section_columns` stay the straight local profile (callers
  that need the warped deck use `under_z_world`).  The warp is vertical only: there is no plan bow of the eave line.
  `eave_lift` (v6 r1) is a vertical lift too.  It must stay clear of a junction body (it fades to 0 at +-width/2).
- Eyebrow (v5 r5-r8): shingle only (a thatch eyebrow would need the course sheets split at the step).  There is no
  overlap check against a verge, the eave band, another bump or a junction body.  It allows one front per bump, on a
  straight slope.  The flank lip is one rolled course.  With `profile="arch"` the shoulders' course butts still read
  as close diagonal lines square-on (spaced `e x cos(40 deg)`, a fixed course count).  `respace` spreads the
  compression but does not remove it: every course on the roll shows about 0.80 of the plain exposure.
- `cruck_frame` is symmetric about the gable centre, with one opening per frame.  The `gate` envelopes are centred.
  They do not model door leaves, a cart's hub-height bulge, or a figure walking beside a cart.
- `arched_doors`: the leaves' outer bottom corners stand into the proud pads' inner nosing, behind the posts.  The
  v6 note says 10 cm; the round-3 audit measured up to 5.8 cm, not visible as clipping.
- `stone_quay` water runs end in open, cut stone sections where the quay continues in the terrain (no `ends=` option).
- `board_belt(body=...)`: lookouts only (no doors); the window gaps cut whole boards.
- `floor_stack` has no building yet.  Two jettied sides that meet at a corner raise (a dragon beam is not built).
- `ridge_seat`: the seat depth is set from the straight profile at mid-slope.  The roll's end caps shrink the flanks
  over the last 16 cm before a verge face.
- `verge_roll`: the fillet radius is limited by the roll's visible inward depth (about 0.34 m).  With `apex_bend` the
  apex is two crossing sweeps, not one loop, and leaves a soft seam line under the lead hat's drip.  `comb_backing` is
  a plain board.
- `window(gable=True)`: one row only.  A gable opening's dark room is not checked against the roof deck (keep
  `room_pad` small, as `loft_door` does).  `hoist_beam`: a straight beam on a straight face, with no rope.
- `path_stone_wall` `RUBBLE_LARGE` hero stones (found by the v6 round-3 audit, not in either note): two large ground
  stones under the barn's east gable have inside-out winding, and so do some in the accepted v5 (`HARB_hall_stones`,
  `HARB_wing_stones`).  With one-sided UE materials they would drop out.  This is a kit item, still open.
- Resolved and dropped: the eyebrow "not built" (v5 r2, built in r5); the flank-shingle shear (r5, `tilt` in r6); the
  bell's flat top and steep 53 deg shoulders (r5-r7, `profile="arch"` in r8); the washboard course bunching on the
  fade (r6, `respace` in r8, now the 0.80-exposure item above); the long hidden tear rows (`span_rows`, r6); the knot of
  rake-roll ends at the apex (v6 r2, `apex_bend` in r3); and the kiln-junction notes of v6 r1 (the kiln was removed in
  v6 r2).

### Status

| Design | Status | Round | Triangles |
|---|---|---|---|
| v5_harbour_house | **FINAL** (client decision 19:35), director 8.6, audit upheld; snapshotted as `*_r08_accepted.*` | 8 | 714,452 (14.1 % hidden) |
| v6_barn | **PAUSED** at round 3 (client decision 22:05), director 8.4, audit rejected on one hard requirement: the see-through wedge at both cruck post heads, under the eyelid.  A quick fix (round 4, recipe / frame, defaults unchanged) is now running; it needs a re-audit, not a re-grade | 3 | 213,651 (audit) |

### Verification

The 1.12.0 kit is the kit `kit/baseline/v6r3_hash/` was built from (see "Behaviour changes").  The first seven rows
are unchanged from 1.11.0.  v5_harbour_house is added from its delivered round-8 build
(`kit/baseline/7_v5_ref/v5_harbour_house.json`), which `v6r3_hash` reproduced per object.  `tools/build_baseline.ps1`
now rebuilds eight buildings (v5_harbour_house added).  v6_barn is not in the table: it is paused and not accepted.

**Reference builds at kit 1.12.0** (the reference table for the HASH RULE from now on):

| Building | State | Triangles | Geometry | UV | Mask |
|---|---|---|---|---|---|
| hilltop_keep | kit reference (phase 1 is the deliverable) | 1,166,874 | `3e2a219a5901afc5` = | `10326b66883e3031` = | `cacc4885b10b1370` = |
| wattle_roundhut | kit reference (phase 1 is the deliverable) | 878,355 | `7e5e7c2df5c4d367` = | `c97c88e742be4887` = | `46bb1454fa4d264e` = |
| tower_windmill | signed off (kit r8) | 1,146,243 | `89bf4a2a2c60e049` = | `b006e70c2dc4750b` = | `3c0753f38798dad6` = |
| v1_stone_watchtower | accepted r5 | 937,933 | `465c7b1b8a7dbb22` = | `eadfb3aacdd78b6d` = | `37235edc68b2377f` = |
| v2_tiered_hall | accepted r7 (client decision) | 980,405 | `9522f17ed8b09646` = | `e3e6c05a78940663` = | `252e24bcf02ccdf5` = |
| v3_longhouse_roundend | accepted r8 | 617,342 | `38ff44b686efd26b` = | `ba1118a58beca64f` = | `e8e670cd18148d95` = |
| v4_mixed | accepted r4 | 938,453 | `2e87caad61b68d34` = | `230f3672711b12d4` = | `07a9171c30138f67` = |
| v5_harbour_house | FINAL r8 | 714,452 | `c3d3a5343572dc73` | `010c14c06ec9eb50` | `e23665ef913e5991` |

(`=`: unchanged from the 1.11.0 table.)

---

## 1.11.0 (2026-10-17): variant-builder modules merged (producer)

Phase-2 kit decision, client "Yes proceed", step 3.  The four variant builders -- v1 stone watchtower, v2 tiered
hall, v3 longhouse with round end, v4 mill-house (`v4_mixed`) -- added modules and options under the kit edit rules
during their rounds (kit 1.6.1 to 1.10.1).  This release merges them into one record; the full per-round records
(signatures, proofs, hero and hash re-runs) stay in `kit/changes/<variant>.md`.  Names are the current ones (the
1.8.0 renames in brackets).  The version numbers the notes proposed (1.7.0 for both v2 and v4, 1.7.1-1.7.3 and
1.10.2 / 1.10.3 for v2) are superseded by this release.

### New modules

- **`components/tower_roof.py`** (v1 r1-r3): the head of a round stone tower -- `corbelled_parapet`,
  `round_tower_roof` (bell-cast conical shingle roof on the hut's roof modules, via the `roof_frame` RoundFrame
  sub-frame), `drum_ceiling`, and the fast drum cull (`drum_precull`, `drum_view_masks`, `drum_ray_cull`,
  `tower_views_lite`, `tower_head_views`, `tower_hidden_cull`, `_close_pool`).  Used by v1; `roof_frame` also by v2's
  round tiers.
- **`components/tower_decals.py`** (v1 r1-r3): `round_tower_decals(_gated)`, `cabin_decals`, `BLOCKER_PARTS`,
  `drop_blocker_anchors`: note-11 anchors for a rotor-less stone tower, never on note-6 blockers.  Used by v1.
- **`components/square_cabin.py`** (v1 r2-r5): `square_cabin`: a square timber lookout cabin on any wall head (floor
  on bearers and joists, knee-strut brackets on corbel pads, framed plank walls with lookouts, ceiling, closed bed
  curb), roof by `pyramid_roof`.  Used by v1.
- **`components/pyramid_roof.py`** (v1 r4-r5): `pyramid_roof`, `PyramidSurface`: a bell-cast N-sided pyramid roof
  (bell, hip kick, sag) with closed deck, coursed kit shingles tucked under one closed saddle per hip, lead cap and
  turned finial; `tip` from the built mesh.  Used by v1 (through `square_cabin`); since 1.8.0 also the engine of
  `tier_roof.bell_tier` for non-octagonal tiers, which no building builds yet.
- **`components/level_probe.py`** (v1 r5): `level_sky_probe` (`LevelSeeThroughError`), `cabin_bed_probe`: a level
  see-through check for any horizontal junction band (floor sandwich, sole plate, jetty), the complement of the
  seal probe.  Used by v1.
- **Tier family** (v2 r1-r4): `tier_frame.py` (`TierFrame`, `Body`, `declare_bodies`, `roof_support`, `roof_z`, the
  roof-to-roof rule `roof_clearance` / `RoofClearanceError`), `stone_body.py` (`stone_body`, `framed_openings`,
  `coping_ledge`, quoins on polygon bodies), `tier_roof.py` (`bell_tier` / `round_tier`, `tier_finial`,
  `roof_flashing`, `eave_deck_lap`, `drop_empty_meshes`, `PROFILES` / `ROUND_PROFILES`), `board_belt.py`
  (`board_belt`), `tier_finish.py` (`tier_hidden_cull`, `tier_views`, `tier_decals`): a frame with no building in it,
  bodies and roof tiers declared by a recipe and found by name.  Used by v2; `stone_body` is re-exported by
  `masonry` (1.8.0).
- **`components/round_roof_parts.py`** (v2 r3): `roof_deck`, `eave_closure`: the round cone's sarking deck and eave
  frieze, promoted from `tower_roof`'s private helpers (now aliases; `eave.eave_closure(kind="ring")` since 1.8.0).
  Used by v1 and v2.
- **`components/seal_probe.py`** (v2 r4): `through_seal_probe`, `SealError`: the see-through check round a body
  rising through a tier.  Used by v2; generalised in 1.9.0 as the `guards.seal_probe` guard for every building, and
  its helpers are read by `guards`, `level_probe` and `tier_flashing`.
- **`components/tier_flashing.py`** (v2 r5-r7): `dressed_flashing`, `eave_cheek`, `flashing_clip_check`
  (`FlashingClipError`), `covering_envelope`, `masonry_envelope`, `masonry_meshes`, `flashing_lift`,
  `self_intersections`, `near_layers`: a lead apron dressed on the covering's real upper envelope with closed
  straight run ends, a cheek fitted to the masonry, and a build-failing clip / self / lift / near-layer check.  Used
  by v2 (instead of `tier_roof.roof_flashing`, which is unchanged).
- **`components/tier_cull.py`** (v2 r5): `tier_hidden_cull_lean`, `cap_views`: the tier cull with at most
  `max_views` building views per object.  Used by v2.
- **`components/linear_roof.py`** (v3 r1-r5): `GableRoof`, `linear_roof`: a straight gable roof over any
  rectangular body (deck, rafters, layered thatch courses or kit shingles, D eave roll, closed verge faces, ridge
  roll with rounded caps, comb), queryable as a solid (`keep_out`, `top_depth`, `eave_zone`).  Used by v3.
- **`components/roof_junction.py`** (v3 r1-r5): `cone_abutment`, `abutment_curve`, `cone_nose_apron` (was
  `end_apron`), `round_eave_fill`, `inside_cone`, `cone_ref_z`: a linear roof running into a `RoundFrame` cone
  (traced junction line, closed lead flashing, end aprons) and the eave fill on a round stone wall head.  Used by v3
  (the round-6 recipe); `eave.eave_closure(kind="fill")` reads `cone_ref_z`.
- **`roof_junction.wall_abutment`** (v3 r8, a new function): the cylinder version of `cone_abutment` -- a
  `GableRoof` running INTO a round wall that rises past its ridge: comb shakes near the face dropped, every roof part
  trimmed behind the battered face, the roof / wall line traced, a fitted mortar flaunching, closed lead end aprons,
  the junction registered with the seal guard; raises if the eaves would cross the cone's (that is `cone_abutment`).
  It reuses v4's `junctions` pieces unchanged.  Used by the v3 round-8 redesign
  (`redesign_r8_wip/build_v3_longhouse_roundend_r8.py`).
- **`components/wall_openings.py`** (v3 r1): `door_spec`, `window_spec`, `build_opening`, `opening_rects`,
  `opening_cut`: doors and windows for any masonry wall by a local frame (threshold, posts, lintel, plank leaf,
  ironwork; sill, mullioned frame, reveal, blocker room).  Used by v3 (through `rubble_walls`).
- **`components/rubble_walls.py`** (v3 r1, r8): `path_stone_wall` (coursed rubble along any plan polyline, quoins,
  gable top, openings, clip), `round_stone_body` (battered round body, openings by azimuth), `PathMap`.  Used by v3;
  re-exported by `masonry` (1.8.0).
- **`components/ball_finial.py`** (v3 r1-r3): `ball_finial`, `apex_blocker`, `fine_hat`, `hat_fit_units`,
  `cone_apex_z`: the stone ball finial over a fitted lead hat on a stone round end.  Used by v3.
- **`components/composite.py`** (v3 r1-r8): assembly helpers for multi-body buildings -- `cone_roof` (with
  `cone_soffit`, the cone keep-out / trim / soaker machinery `cone_keep_out`, `trim_units(_field)`, `cone_soakers`,
  `soaker_support`, `drop_slivers`, `footprint_field`), `inside_box` / `inside_round`, `set_entrance`,
  `footprint_views`, `composite_hidden_cull`, `recenter`, `composite_decals`, `mesh_islands`, `drop_units`.  Used by
  v3.
- **`village_kit/compound.py`** (v4 r1-r4): `Wing`, `build_compound`, `configure`, `patches_by_azimuth`,
  `thin_anchors`, `dedupe_views`, `compound_views`, `compound_cull`, `wall_head_views`, `wall_head_band`: one
  building from several family frames, one cull and one decal audit over all wings, protected wall-head bands.
  Used by v4.
- **`components/junctions.py`** (v4 r1-r3): `roof_tower_flashing`, `wall_tower_abutment`, `tower_of`,
  `round_wall_of`, `tower_field`, `clip_at_tower`, `trim_wing_at_tower`, `ride_fillet`, `trace_roof_on_tower`,
  `pole_plate_ledger`, `rafter_feet`, `rafter_bearings`, `wall_end_apron` (was `end_apron`): junction pieces between
  bodies of different families (roof into tower, wall against tower).  Used by v4 and, through `wall_abutment`, v3.
- **`components/round_apex.py`** (v4 r1): `turned_apex`: the keep's turned finial over a fitted lead hat on any
  RoundFrame cone.  Used by v4.
- **`village_kit/lod.py`** (v4 r4): `tmpl_lod`, `tmpl_lod_report`, `coarse_template`, `DRUM_LOD_PARTS`:
  height-banded grid LOD for template-instanced pieces (outline, arrises and placement kept).  Used by v4 and v1
  (round 5, note 15); `guards` ends its scope.

### Optional parameters added to existing modules

New functions in existing modules are listed here too.  "Existing" means the module existed before the builder's
round; several are other builders' new modules.

| module | parameter / function | added by | default keeps old behaviour? |
|---|---|---|---|
| `drum_frame` | `DrumFrame.WIN_DZ = None`, `BATTER_TOP = 4.6`, `WIN_SPEC = None`, `BAND_STYLE = "balustrade"`; `win_dz`, `win_list`, `WINDOW_FW`; `hw_window(dz=0.0, w=None)` | v1 r1-r2 | yes (the mill's windows unchanged) |
| `drum_frame` | `drum_window_spec` (was `window_spec`; `openings.drum_window` since 1.8.0), `fit_window_courses` | v1 r2-r3 | new functions |
| `drum_frame` | `drum_finish(checks=True)`: the rotor checks skip themselves when no rotor was built | v1 r3 | yes (the mill builds its rotor) |
| `drum_wall` | `round_stone_drum(window_z=None, batter_top=None, window_size=None, lookouts=None, course_fit=True)`, `zones=dict(string=...)`, `arcade=dict(n=0)` = no arcade; per-window spec / `dz` in `build_slit_windows`, `_drum_openings`, `wall_core_backing`; empty-arcade guards in `build_base`, `build_band_cornice_and_finish` | v1 r1-r3 | yes (`course_fit` is read only with `window_size` / `lookouts`) |
| `drum_wall`, `drum_band` | `lookout_room`; `string_course`, `string_course_profile` (`BAND_STYLE = "plain"`) | v1 r2 | new functions |
| `tower_roof` | `tower_hidden_cull(precull=DRUM_PRECULL, lite=DRUM_PRECULL)` | v1 r2 | no: the fast cull is the default (`precull=(), lite=()` = round 1); only v1 |
| `tower_decals` | `round_tower_decals(exclude=BLOCKER_PARTS)` | v1 r3 | no: blocker anchors dropped; only v1 |
| `square_cabin` | `roof=`, `roof_fn=`, `finial_scale=0.80`, `bed_fill=True`, `bearers=None`, `bed_n=16`; `open_sill` 1.00 -> 1.10 | v1 r4-r5 | no (finial 1.4 -> 0.8, bed fill on, sill raised); only v1 |
| `pyramid_roof` | `hip_tuck=None`, `hip_bed=0.30`; `coll=None` (1.8.0) | v1 r5 | no: the hip fix is on (`hip_tuck=0.012, hip_bed=0` = round 4); only v1 builds one |
| `stone_body` | `stone_body(joint_lap=0.06, quoins=True)` | v2 r2 | no for polygon bodies (quoins); round bodies as before; only v2 |
| `tier_roof` | `bell_tier(sides=None, deck_lap=True)`, `roof_flashing(drip=0.03)`, `ROUND_PROFILES["witch_hat"]`, `drop_empty_meshes`, `_register` | v2 r2-r4 | no (`deck_lap=False`, `drip=None` = kit 1.7.2); only v2 |
| `tier_frame` | `roof_clearance`, `TierFrame.roof_clear = 0.50`, `roof_stack = 0.20` | v2 r3 | no: the rule is on (`roof_clear=None` off); only v2 |
| `tier_finish` | `tier_hidden_cull(procs=None, seal=True, seal_kw=None)`, `cull_procs` | v2 r4 | no: workers per core, seal probe on; only v2 |
| `tier_flashing` | `dressed_flashing(dress="tight", end_line=True, normal_t=6.0, lift_rays=True, ...)`, `eave_cheek(fit=True, top_cap=, apron_under=)`, `flashing_clip_check(self_check=True, others=True, tier=True, bodies=None, layer_tol=None)` | v2 r6-r7 | no (`dress="max"`, `fit=False` = round 5); only v2 |
| `linear_roof` | `thatch_style="courses"`, `abut_wall_in=0.10`, `_eave_rolls(end_caps=True)`, `_verge_faces(roll_cover=0.012, ridge_cover=False)`; `ridge_caps=False`, `rafter_skip=None`, `verge_apex=False` | v3 r2-r5 | r2-r3 keywords no (`"clumps"`, `None` = round 1); r5 keywords yes; only v3 |
| `roof_junction` | `cone_abutment(end="apron", sweep_end="crest", taper=None, fit_kept=False)`, `abutment_curve(ends=, crest_over=)`, `cone_nose_apron(w_in_kept=False, u_top=0.10)`, `section_meets_cone`, `round_eave_fill(z_bot="wall")` option | v3 r2-r5 | `end="apron"` no (`end="nose"` = round 1); the rest yes; only v3 |
| `ball_finial` | `ball_finial(hat_drop=None, hat_pitch_deg=44.0, blocker=True, clear=0.02, hat_seg=40, fit=False)` | v3 r2-r3 | no for the hat / blocker (`hat_drop=0.34, blocker=False, clear=0.025` = round 1); `fit` yes; only v3 |
| `composite` | `cone_roof(soffit=True, abut_roof=None, abut_*, abut=None)`, `composite_hidden_cull(views="lean")`, `composite_decals(door_lichen="jamb", south_moss=False, walk_gate=True, moss_normal="hit")`, `cone_soffit(cut=None)`, `cone_keep_out(...)` keywords, `inside_box(z_fn=None)` | v3 r2-r8 | r2 / r4 soffit, views and decal defaults no (`soffit=False`, `views="full"`, `door_lichen="threshold"`, ...); r4-r8 keep-out keywords yes; only v3 |
| `rubble_walls` | `round_stone_body(open_z=None)` | v3 r8 | yes |
| `anchor_validate` (shared, heroes import it) | `validate_anchors(walk_zones=None, walk_types=("lichen", "moss"), walk_up_dot=0.7)` | v3 r4 | yes (heroes re-run) |
| `conical_roof` | `build_eave_closure`: `f"{g.prefix}_roof_..."` lookup (was literal `HUT_`) | v4 r1 | yes (bug fix; `eave.eave_closure(kind="door")` since 1.8.0) |
| `conical_roof` | `build_eave_closure(thickness=0.03)` | v4 r2 | **no**: closed 3 cm band, hut +1,736 tris (below) |
| `conical_roof`, `doors` | frame attributes `g.EAVE_CLOSURE_DOOR_HALF_DEG`, `g.DOOR_INFILL_DECK`, `g.SH_RING_STEP` | v4 r4 | yes when absent (since 1.9.0 the first two are set by `RoundFrame(steep_door="auto")` on cones > 52 deg) |
| `daub`, `plinth` | `g.DAUB_GRID`, `g.PLINTH_DENSE` | v4 r4 | yes when absent |
| `tmplmesh` | `LOD_HOOK = None`, `BatchAcc.add(_lod=True)` | v4 r4 | yes with no rule registered |
| `rotor_checks` | `rotor_clearance` / `tail_clearance`: absent or empty parts skipped | v4 r1 | yes (bug fix; the mill has props) |
| `tail_vane` | `tail_boom`: iron bands within 10 cm of / past the boom end skipped | v4 r1 | yes for the hero; not for the mill KIT_VARIANT (below) |
| `core` | `_vis_pre_bpy_path`, `_vis_map_watched`; workers stopped instead of joined | v4 r2 | yes (spawn-pool management only, cull results identical) |
| `compound` | `Wing(eye_heights=(1.0, 1.65))`, `compound_cull(wall_head=True)`, spec keys `cull_max_views=260`, `cull_procs=4`, `cull_wall_head=True` | v4 r2-r4 | no (`eye_heights=()` = round 3); only v4 |
| `junctions` | `roof_tower_flashing(ledger=True, trim=True, section="ride", bearing="corbels", apron_closed=True, ...)`, `wall_end_apron(closed_lip=False)` | v4 r2-r3 | no (`section="flaunch"`, `bearing="ledger"` = rounds 1 / 2); only v4 (and v3's `wall_abutment`) |

### Behaviour changes to existing defaults

- **`conical_roof.build_eave_closure(thickness=0.03)`** (v4 r2, director must-fix 4): the eave closure became a
  closed 3 cm band by default.  It moved the hut by **+1,736 triangles** (876,619 -> 878,355; v4's note estimated
  "about 1,900").  This **broke the edit rule** "never change the behaviour of an existing function another building
  uses" (v4's note records it under "Existing module changed").  It was accepted by the producer in 1.10.1 as an improvement
  (closed pieces, note 1): 878,355 is the hut's kit reference; the delivered hut is still the phase-1 version.
- **`tail_vane.tail_boom`** (v4 r1 bug fix): the mill hero (`boom_end` -6.08) keeps all five bands, but the mill
  KIT_VARIANT (`boom_end` -5.6) loses its floating -5.92 band.  A visible change to a variant output, accepted as a
  bug fix (the band floated past the boom).
- **`core._vis_spawn_pool`** returns a `ProcessPoolExecutor` since 1.6.1: v1's `tower_roof.drum_ray_cull` called
  `close()` / `join()` on it and died; fixed on v1's side (`tower_roof._close_pool`), no kit default reverted.
- **Defaults moved inside a design's own modules** (`tower_roof`, `tower_decals`, `square_cabin`, `pyramid_roof`,
  the tier family, `linear_roof`, `roof_junction`, `ball_finial`, `composite`, `compound`, `junctions`): the table
  above marks them "no".  Each note records the keyword that gives the old behaviour, and grep plus the hash re-runs
  (`kit/baseline/v1r5_hash/`, `v3_r5_hash/`, `v3_r6_hash/`, `v3_r8_hash/`) showed no other building reaching them.
  v1 r5 changed `pyramid_roof`'s defaults on purpose; it is the only caller (`tier_roof._pyramid_tier` imports it
  lazily for tier side counts no building uses).
- Already recorded elsewhere: the 1.9.0 `steep_door="auto"` flags (v4's door-head fix now set by the frame), and the
  1.8.0 `bell_tier(sides=None)` pyramid engine for non-octagonal polygon bodies (v2 r3's `ValueError` for those is
  gone).

### Known limitations

- v3: `path_stone_wall` has no batter (its quoins are solid boxes); `round_stone_body` batters at 2.5 deg by default
  (`batter_deg`; the round-8 recipe uses 1.5).
- v3: `cone_abutment` handles a roof whose ridge is horizontal and meets the cone on its near end.  The cylinder case
  (a round WALL taller than the roof) now exists as `roof_junction.wall_abutment` (round 8 of the longhouse
  redesign): built, grading in progress.
- v3: the `linear_roof` "courses" style is thatch only (the shingle covering is unchanged); `cone_nose_apron` reads
  the `GableRoof.ROLL` section (a covering without a roll gets a nominal nose).
- v3: the main recipe `buildings/variants/v3_longhouse_roundend/build_v3_longhouse_roundend.py` still imports and
  calls `composite.cone_cut_cover` (round 7), which round 8 removed from the kit; it cannot build against this kit
  until it is restored to round 6 (the client-cleared state) or replaced by the round-8 recipe.
- v3: v3's body thatch reads 55 % up / 44 % down slope in `analyze_uv_grain.py` (1.10.0, cause not investigated).
- v1: `square_cabin(struts=False)` has no dragon beams, so the bearer band on the +-X sides beyond the curb is closed
  only by the curb; `cabin_bed_probe` would catch a gap.
- v2: the kit's 0.05 m flashing lift / foot gates are not met on the delivered recipe (drip lift up to 0.083 m on
  `tur_nw`, upstand foot up to 0.097 m on the turrets' upslope back gutter); the recipe passes `max_lift=0.09,
  max_foot=0.10, layer_tol=0.001`.  `tier_flashing`'s `foot_d`, `adaptive`, `blunt_drip` are experimental, off.
- v4: the "house roof / mill tower" seal-probe junction is still opted out in the recipe (1.9.0, 13 of ~23k rays),
  queued for `junctions.roof_tower_flashing`.
- UV determinism (v3 r6 note): `uvgrain.regrain_mesh` sign-fixes the PCA major axis but not `B1`; the fix
  (`B1 = _sign_fix(B1)`) changes every building's UV hash, so it is left to a producer step.
- Resolved and dropped: v1's ~10 min drum-rubble cull (round-2 fast cull); the `HUT_` hard-coded names in
  `build_eave_closure` (v4 r1 fix); "no hero triangle count can move" (v3 r4 edited the shared `anchor_validate`
  with defaults off, and the heroes were re-run).

### Status of the designs that use them

| Design | Status | Round | Triangles |
|---|---|---|---|
| v1_stone_watchtower | accepted, 8.5 | 5 | 937,933 (note 15 met; was 1,057,164) |
| v2_tiered_hall | accepted by client decision (director 8.2); lookdev mitigation: a darker, grimier turret-apron lead (`lookdev/scripts/apply_lookdev.py`, `OBJECT_GRIME`) | 7 | 980,405 (the 954,925 once quoted in `HANDOFF.md` / `production_plan.md` was round 4's count; corrected) |
| v3_longhouse_roundend | **accepted**, 8.3, audit upheld: the round-8 redesign (`wall_abutment`); round 6 archived in `round06_archive/` | 8 | 617,342 |
| v4_mixed | accepted, 8.4 | 4 | 938,453 |

### Verification

All seven rebuilt from the 1.11.0 kit (with v3's round-8 edits to `roof_junction`, `rubble_walls` and `composite`) into
`kit/baseline/6_r8kit_check/` (`tools/build_baseline.ps1 -MaxParallel 2`, fingerprints `<id>.json` there). Every
geometry, UV and mask hash equals the building's accepted / reference build: the heroes and v4 equal the 1.10.1 table
above; v1, v2 and v3 equal their committed accepted `.blend` (`tools/geom_hash.py`). The v3 rebuild is also round 8's
determinism check (identical to the graded build).

**Reference builds at kit 1.11.0** (the reference table for the HASH RULE from now on):

| Building | State | Triangles | Geometry | UV | Mask |
|---|---|---|---|---|---|
| hilltop_keep | kit reference (phase 1 is the deliverable) | 1,166,874 | `3e2a219a5901afc5` = | `10326b66883e3031` | `cacc4885b10b1370` |
| wattle_roundhut | kit reference (phase 1 is the deliverable) | 878,355 | `7e5e7c2df5c4d367` = | `c97c88e742be4887` | `46bb1454fa4d264e` |
| tower_windmill | signed off (kit r8) | 1,146,243 | `89bf4a2a2c60e049` = | `b006e70c2dc4750b` | `3c0753f38798dad6` |
| v1_stone_watchtower | accepted r5 | 937,933 | `465c7b1b8a7dbb22` | `eadfb3aacdd78b6d` | `37235edc68b2377f` |
| v2_tiered_hall | accepted r7 (client decision) | 980,405 | `9522f17ed8b09646` | `e3e6c05a78940663` | `252e24bcf02ccdf5` |
| v3_longhouse_roundend | accepted r8 | 617,342 | `38ff44b686efd26b` | `ba1118a58beca64f` | `e8e670cd18148d95` |
| v4_mixed | accepted r4 | 938,453 | `2e87caad61b68d34` = | `230f3672711b12d4` | `07a9171c30138f67` |

(`=`: unchanged from the 1.10.1 table. Build times: 210-576 s, 2 at a time.)

---

## 1.10.1 (2026-10-17): deterministic needle repair (producer)

- **`core._needle_faces` / `core.nanite_clean`.** The needle faces and the edges to rotate or collapse were gathered
  in Python sets of BMesh elements, which iterate in memory-address order. So the repair order could change from
  build to build. In 2 of 6 kit-1.10 keep builds, 88 polygons of `KEEP_turret_cap_shingles` came out with
  **reversed winding** (the verifier's blocking issue). They are now de-duplicated in triangle order
  (`dict.fromkeys`), and the edge "sets" are ordered dicts.
- **Result.** All seven rebuilt (`kit/baseline/5_determinism/`). The hut, mill, v1, v2 and v4 have geometry hashes
  identical to 1.10.0. The keep and v3 have a new polygon order but **canonically identical geometry**
  (`canon_hash.py`): the keep matches the verifier's correct-winding canonical geometry 1fb5d4f5fe54ccc6, and v3
  matches its 1.10.0 canonical geometry. Three builds each of the keep and v3 gave identical hashes.
- **The hut's +1,736 triangles since round 11** come from the v4 builder's change to the `build_eave_closure`
  default (a closed 3 cm band, recorded in `kit/changes/v4_mixed.md`). That broke the edit rule "never change a
  default", but it is an improvement (closed pieces, note 1). The producer accepts 878,355 as the hut's kit reference.
  The delivered hut is still the phase-1 version.

---

## 1.10.0 (2026-10-17): the queued UV fix -- grain, collapsed UVs, no moss on walked tops (UV / MASK ENGINEER)

Phase-2 kit decision, client "Yes proceed", step 1 continued: the client-approved queued UV fix
(`director/queued_uv_fix.md`, found by the look-dev test `lookdev/scripts/analyze_uv_grain.py` /
`check_uv_stretch.py`).  **UV and `Mask` only: no vertex, polygon or material changed in any building** (geometry
hashes below).  Like 1.9.0 this deliberately changes defaults (every building's UVs and walked-top Mask B), as the
client's plan approved.

### New: `village_kit/uvgrain.py` (the kit's final UV writer) and `mask.clear_walked_tops`

`build_building` and `build_compound` call `uvgrain.finish_building(objects, entrances)` once the building is
finished (after the guards and the decal anchors, before the save).  Per mesh datablock (pooled meshes once):

1. **Grain along the piece.** Slots `M_timber`, `M_timber_weathered`, `M_roof_shingle`, `M_roof_shake`.  A piece is
   an edge-connected loose part split by its Mask R byte (one R per `Acc.add` / `BatchAcc` instance).  Timber:
   V = position along the piece's PCA long axis (continuous over the piece); U from a box map in the piece's own PCA
   frame (width axis on the broad faces, thickness axis on the edges) -- or wrapped round the axis for round / square
   pieces (cross-section aspect > 0.75); end grain mapped (width, thickness).  Shingles, shakes and sloped timber
   sheets without a long axis (cone / ring decks, apron soffits): V = z / (piece's mean sine of slope), so V runs
   up-slope on every face and stays continuous over a curled shake or a cone ring; U along the contour.  ~1 UV unit
   per metre, a per-piece offset from the piece's position.  **V is the grain axis**: the brief says "U must run
   along the piece's long axis", but the look-dev wood texture's grain runs vertically in the image (along V) and
   the acceptance test measures dP/dv, so V is what the brief's target measures; U along the grain would have
   turned every texture 90 degrees.  `M_thatch` UVs are kept (only its collapsed faces are touched).
2. **No collapsed UVs.** Every face (any slot) whose UV / 3D area ratio is < 0.25 (first triangle, the
   check_uv_stretch rule, or the whole face) is re-mapped with the nearest rigid map (SVD of its old map) at 1 UV
   unit per metre, centred on its old UV centre: thresholds, step tops, post-base tops, thatch course butts,
   shingle edges, wall plates, pegs, collars, finials, corbels.
3. **No moss on walked tops.** `mask.clear_walked_tops`: for every entrance (`guards.entrances_of`, or the spec's /
   wing's `entrances`; compound wings transformed to world), the up-facing faces (n.z > 0.7) inside the walking zone
   -- clear width + 0.1 m each side, from 1.0 m inside the wall face (threshold, sill) to 1.5 m out, at foot level --
   get Mask B <= 0.04 (byte 10, so <= 0.05 after quantisation).  CORNER domain: the step fronts, ends and outer edges
   keep their B.  Pooled hardware (nails, pintles, pegs) is left alone.  The entrances are stored on the scene as
   `kit_entrances` (JSON).

Changed existing code: `assembly.build_building` and `compound.build_compound` (new key `uv_finish`, default True;
the call above).  Nothing else.  New tools (the originals in `lookdev/scripts/` are unchanged):
`tools/uv_audit.py` (the two look-dev scripts' rules over every object, vectorised, plus the walked-top check, JSON
out), `tools/uv_measure.ps1` (both measurements on a baseline step), `tools/uv_fix_preview.py` (the UV pass on an
existing .blend, for iterating).

### Verification (all seven rebuilt into `kit/baseline/3_uvfix/`, fingerprinted with `tools/geom_hash.py`)

Six of seven have exactly the step-2 geometry hash (`kit/baseline/2_guardrails/`); only their uv and mask hashes
changed.  The keep's polygon ORDER varies between builds (see below); its vertices, polygons and materials are
identical.  decal_anchors.json is byte-identical to step 2 for all seven.

| Building | Triangles | Geometry (step 2 -> step 3) | UV step 2 -> step 3 | Mask step 2 -> step 3 |
|---|---:|---|---|---|
| hilltop_keep | 1,166,874 | `b2f847333a2ec943` (step-2 rerun = step 0) -> `12e47dd94bc7786e` (see below) | `0c1f12176f0f1235` -> `8a266ec2dbe568dd` | `c7ddfbfe5d33f6d8` -> `da6309933f84dd2f` |
| wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` = | `9c0dd5aecb5d869c` -> `c97c88e742be4887` | `794266c3463d1240` -> `46bb1454fa4d264e` |
| tower_windmill | 1,146,243 | `89bf4a2a2c60e049` = | `9f132597bb379825` -> `b006e70c2dc4750b` | `04f7ade47b360102` -> `3c0753f38798dad6` |
| v1_stone_watchtower | 1,057,164 | `47e4208df661a5a9` = | `9929b9e5101d3d5f` -> `c0dfea9bb1de1aa6` | `c8e787ab4b8e0bff` -> `0a1fe5428ca8ae19` |
| v2_tiered_hall | 954,925 | `87ba64b7f9d4a746` = | `15bb7bdc5ae3c360` -> `f1f86c015178281c` | `e976015053c38848` -> `b1391129bc4f32b2` |
| v3_longhouse_roundend | 483,508 | `6a7a7ecbea54aa07` = | `1a43d013c02f495e` -> `996bf2646564a2ad` | `27422448b80c6b19` -> `b592bfa6f503a77d` |
| v4_mixed | 938,453 | `2e87caad61b68d34` = | `a73b4ef99fd15564` -> `230f3672711b12d4` | `b6c2768f3068057b` -> `07a9171c30138f67` |

**The keep.**  Five keep builds with the 1.10 kit (`3_uvfix/hilltop_keep`, `hilltop_keep_rerun`,
`hilltop_keep_rerun2`, and `pass1/hilltop_keep`, `pass1/hilltop_keep_rerun`; pass 1 differed from the final code only
in the timber U axis, a UV-only change): one (`pass1/hilltop_keep_rerun`) has exactly the step-0 / step-2-rerun
geometry hash `b2f847333a2ec943`; the other four differ from it in ONE object, `KEEP_turret_cap_shingles`, whose vertex
array is identical, whose polygon set is identical and whose triangle count is identical -- only the polygon order
differs (the first build of step 2 had the same artefact in `KEEP_wing_wall_stones`, BASELINE.md).  Likely cause, not
fixed here (it would be a geometry-order change): `core._needle_faces` returns `list({...BMFace...})`, a set of bmesh
faces whose iteration order follows memory addresses, so the needle repair in `core.nanite_clean` can process faces
in a different order from run to run.  Recommended next kit fix: sort those faces by index.

Measurements (`kit/baseline/3_uvfix/audit_before/` = the step-2 builds, `audit_after/` = this step; `*.grain.txt`
= the original `analyze_uv_grain.py`, `*.audit.txt` / `*.json` = `tools/uv_audit.py`, same door zones for both):

| Building | Timber along the long axis (`analyze_uv_grain.py`, before -> after; in brackets: of the area the rule can judge, and the sheet area it cannot) | Shingles / shakes up-slope | Collapsed (objects >= 1 % of area at ratio < 0.2; worst object) | Walked tops in the door zones (Mask B) |
|---|---|---|---|---|
| hilltop_keep | M_timber 13 -> **92 %** (13.7 -> 98.2 %; sheets 18.1 of 300.3 m2); weathered 4 -> 83 % (4.6 -> 99.0 %; 4.6 of 29.2 m2: the drum backing) | shingle 87 -> 100 %; shake 92 -> 97 % | 42 -> **0**; 60.4 % (KEEP_threshold) -> 0.47 % (KEEP_hall_eave_plate) | 3.87 m2: B max 1.000 -> **0.039** |
| wattle_roundhut | M_timber 92 -> **95 %** (95.7 -> 98.7 %); weathered 4 -> 25 % (15.6 -> 99.9 %; sheets 52.9 of 70.5 m2: HUT_roof_blocker) | shingle 91 -> 100 % | 14 -> **0**; 83.5 % (HUT_wall_plate) -> 0.004 % | 2.22 m2: 1.000 -> **0.039** |
| tower_windmill | M_timber 4 -> 66 % (5.9 -> 99.2 %; sheets 75.8 of 229.3 m2: apron soffit ring, cap decks); weathered 23 -> **98 %** | cap shingle 7 -> 100 %; apron shake 0 -> 100 % | 1 -> **0**; 2.6 % (MILL_cap_shingles) -> 0.08 % | 2.48 m2: 1.000 -> **0.039** |
| v1_stone_watchtower | M_timber 9 -> 51 % (18.0 -> 98.9 %; sheets 103.8 of 218.5 m2: cabin floor, ceilings); weathered 27 -> 33 % (83.0 -> 99.8 %; sheets 178.5 of 268.8 m2: roof deck, floor) | shingle 91 -> 100 % | 5 -> **0**; 22.9 % (WATCH_cabin_corbels) -> 0.06 % | 2.45 m2: 1.000 -> **0.039** |
| v2_tiered_hall | M_timber 11 -> 58 % (18.1 -> 98.9 %; sheets 142.0 of 344.7 m2: skirt deck); weathered 3 -> 19 % (14.4 -> 99.9 %; sheets 317.2 of 391.3 m2: roof decks, bands, backings) | shingle 91 -> 100 % | 40 -> **0**; 90.6 % (HALL_cap_wall_plate) -> 0.02 % | 0.95 m2: 0.851 -> **0.039** |
| v3_longhouse_roundend | M_timber 54 -> **98 %** (54.6 -> 98.1 %); weathered 9 -> 68 % (12.7 -> 100 %; sheets 113.4 of 356.0 m2: roof / wall / apex blockers) | shingle 83 -> 100 %; shake 100 -> 100 % | 17 -> **0**; 84.9 % (LONG_wall_plate) -> 0.01 % | 0.92 m2: 0.804 -> **0.039** |
| v4_mixed | M_timber 25 -> 77 % (32.2 -> 98.7 %; sheets 49.3 of 225.5 m2); weathered 6 -> 68 % (9.5 -> 99.1 %; sheets 37.1 of 118.5 m2: V4H_roof_blocker) | shingle 90 -> 100 %; apron shake 0 -> 100 % | 16 -> **0**; 81.3 % (V4H_wall_plate) -> 0.10 % | 4.55 m2: 1.000 -> **0.039** |

`check_uv_stretch.py` (original, ratio < 0.3) on the objects the brief named: KEEP_threshold 1.27 -> 0.0 m2,
KEEP_hall_post_bases 0.57 -> 0, KEEP_wing_roof_thatch_courses 5.6 -> 0.5, KEEP_cap_shingles 1.57 -> 0.03,
HUT_roof_shingles 8.11 -> 0.02, HUT_wall_plate 9.5 -> 0, MILL_cap_shingles 0.57 -> 0.02 (`audit_*/check_uv_stretch_*.txt`).
Thatch (kept as the brief says): keep 96 % up-slope unchanged; v3's body thatch reads 55 % up / 44 % down before and
after (cause not investigated) -- not in this brief's scope, noted for the thatch module.
Look-dev: `lookdev/scripts/apply_lookdev.py` re-run on the keep, mill, hut and v4 (`kit/baseline/3_uvfix/lookdev/renders/`,
same shots as `lookdev/renders/`): shingles and shakes now show grain up the slope, blades / boards / boom / door
planks / threshold beams along their length, no smeared streaks on the thresholds, post bases and thatch butts, and
no moss on the thresholds and step tops (the step ends and outer edges keep it).

Targets: **shingles and shakes up-slope >= 90 %: met on all seven (97-100 %).  Collapsed UVs < 1 % of every
object's area: met (worst object 0.47 %, keep `KEEP_hall_eave_plate`; was 90.6 %).  Walked tops B <= 0.05: met
(max 0.039 on every door of all seven; was up to 1.0).**  Timber along the long axis >= 90 % in
`analyze_uv_grain.py`: met on the keep (M_timber), the hut (M_timber), the mill (M_timber_weathered) and v3
(M_timber); **not met as the script counts it elsewhere**, because the script divides by the slot's whole area but
can only credit faces on elongated parts (elongation > 1.5): decks, floors, ceilings, ring soffits, backing and
blocker sheets have no long axis, and their area (the "sheets" column) can never count as "along", whatever the UVs.
Of the area the script can judge, 98-100 % now runs along the long axis in every building (was 5-96 %), and
"across" fell to 0-1.4 % (was up to 79 %).  Those sheets' faces now carry up-slope (sloped decks) or one straight
PCA direction (floors, ceilings).

---

## 1.9.0 (2026-10-17): guard-rails ON by default (KIT ARCHITECT)

Phase-2 kit decision, client "Yes proceed", step 1 continued (guard-rails on by default + README).  The technical
review (`director/kit_feasibility_technical.md`, condition 4) listed five guard-rails that a new recipe had to know
about and switch on.  They are now ON by default in `assembly.build_building` and `compound.build_compound`; a
recipe that cannot pass one opts out explicitly, per guard (per junction for the seal probe), with a logged reason.
**This release deliberately changes defaults** (an exception to edit rule 1, approved by the client's plan): every
change it makes to an existing building is either a real fix recorded below or an explicit, reasoned opt-out in that
building's recipe.

### New module: `village_kit/guards.py`

| Guard | Default behaviour | Opt-out |
|---|---|---|
| `clearance` | `entrance_clearance(g)`: for every entrance the door components published (`entrances_of(g)`: the hut family's framed door, the drum door, the keep's arched hall door and annex plank door, `stone_body` doors, `wall_openings` doors; or `spec["entrances"]`), rays straight up from 5 x 5 stations across the clear width, 0.15-0.75 m in front of the face (0.25 / 0.35 m for tier / keep bodies); the door's own assembly (frame, lintel, leaf, step, threshold, ironwork, rooms behind it, matched by name: `DOOR_PARTS`) is passed through; a station whose first hit is a back face starts inside a solid and is ignored.  The lowest hit = the eave lip over the doorway; it must be >= 2.30 m (art bible 7) and >= the door head, else `ClearanceError` names the building, entrance, lip, station and object.  Runs after the last step (after the cull and `recenter`); per wing in a compound | `opt_out=dict(clearance=...)` |
| `decal_validate` | absent = `True`: `anchor_validate.validate_anchors` is APPLIED (anchors snapped, invalid ones dropped, `validation` counts written to the JSON); a dict passes its keywords as before.  A falsy value without an opt-out raises | `opt_out=dict(decal_validate=...)` (report only, the pre-1.9.0 behaviour) |
| `seal_probe` | `junction_seal_probe`: the tier family's see-through probe generalised to any roof-through-body junction a module registered with `register_junction(g, name, covering, center, radius(z), z_range)`.  Targets 8 cm inside the covering within 0.6 m of the body face (only where the build-up continues under them and the covering continues 0.2 m outward and sideways: eave lips, verges and comb tips are not junctions); 24 azimuths x 10-80 deg, 8 per target, none within 10 deg of grazing; a ray that passes the target and reaches the sky, a point > 0.6 m under the covering or the hollow body is a leak -> `SealError`.  Run after the last step; in a compound after the whole-building cull on the placed building.  The tier family keeps its own `through_seal_probe` (in `tier_hidden_cull`) | `opt_out=dict(seal_probe=...)` or `dict(seal_probe={junction: reason})` |
| `steep_cone_door` | `frame.RoundFrame(steep_door="auto")`: pitch > `STEEP_CONE_DEG` (52 deg, the top of the bible's hut range) sets `DOOR_INFILL_DECK = True` and `EAVE_CLOSURE_DOOR_HALF_DEG = 1.0` (the v4 round-4 door-head fix) | `RoundFrame(steep_door=False)` |
| `lod_scope` | `end_lod_scope(g)`: the frame's `lod.tmpl_lod` rule is unregistered at the end of its building / compound wing (also on an exception) | none |

Junctions registered (no geometry change in any of these modules: the registration only records the body and the
covering): `shake_apron.shake_apron` ("apron / smock tower"), `stone_cone.shake_collar` ("shake collar / stone
cone"), `thatch.thatch_junctions` ("wing thatch / turret", "wing thatch / hall"), `roof_junction.cone_abutment`
("<roof> / round body"), `junctions.roof_tower_flashing` ("<roof> roof / <tower> tower", on the compound).

### Changes to existing kit code

- `assembly.build_building`: `opt_out`, `entrances` keys; runs `guards.after_steps` (LOD scope, clearance, seal)
  after the steps; `decal_validate` default via the new `assembly.decal_gate_option`.
- `compound.Wing(..., opt_out=None, entrances=None)`; `build_compound`: `opt_out`; per wing LOD scope + clearance
  after the wing's steps; the decal guard default for each wing; the seal probe after the whole-building cull.
- `frame.RoundFrame(..., steep_door="auto")`, `frame.STEEP_CONE_DEG = 52.0`, `g.STEEP_DOOR`.
- `tower_roof.roof_frame`: its RoundFrame sub-frames pass `steep_door=False` (a tier / tower cap has no framed door
  under it; the flags were inert there, this only stops them being set and logged).
- Recipes: `hilltop_keep` (`OPT_OUT`, one junction), `v4_mixed` (`OPT_OUT`, one junction; the explicit steep-cone
  flags removed from `HOUSE_OPTS`), `v3_longhouse_roundend` (`WALL_Z` 2.75 -> 2.81).  No build script needed an
  output override added (all seven already had one).
- `roof_junction` header wording (`tools/check_headers.py`: 0 stale signatures).
- New tool `tools/guard_probe.py <file.blend> <building_id>`: the clearance gate and the seal probe on an
  already-built kit building, read-only (used to calibrate the guards on the step-1 builds before rebuilding).

### Per building: what the guards found and what was done

Calibrated first on the step-1 builds with `tools/guard_probe.py` (read-only), then every building was rebuilt.

| Building | clearance (lip over the door) | decal_validate | seal_probe | steep_cone_door / lod_scope | Action |
|---|---|---|---|---|---|
| hilltop_keep | hall door 3.711 m (skirt structure), annex door 2.396 m (wing thatch): PASS | now applied: 116 of 116 kept; one anchor re-snapped by 0.01 mm | wing thatch / turret 0 leaks, wing thatch / hall 0 leaks; **shake collar / stone cone: 3 of ~126k rays leak** (thread the jagged comb into the collar / cone void and out; sub-pixel) | n/a | **opt-out** of that one junction in the recipe (`OPT_OUT`): signed-off hero, geometry frozen in this step; the comb seal is queued for the keep family's next round |
| wattle_roundhut | 2.406 m (battens at the eave): PASS | already applied (its own dict) | no junction registered | 51 deg: no flags (unchanged) | none |
| tower_windmill | 4.417 m (apron rafters): PASS | now applied: 106 of 106 kept; one anchor re-snapped by 0.01 mm | apron / smock tower: 0 leaks | n/a | none |
| v1_stone_watchtower | 11.17 m (cabin roof frame: no eave over the drum door): PASS | now applied: 77 of 77 kept, unchanged | no junction registered | n/a | none |
| v2_tiered_hall | 3.188 m (skirt1 deck lap): PASS | already `True` | tier family's own probe: 4 junctions, 0 leaks (unchanged) | the round tiers' roof sub-frames now pass `steep_door=False` (no door under a tier cap) | none |
| v3_longhouse_roundend | **FAIL at first: 2.257 m** -- the body roof's rafter feet over the door (station 0.30 m out); the thatch eave roll was at 2.355 m | already applied (its own dict) | body_roof / round body: 0 leaks | 48 deg: no flags | **fixed in the recipe**: `WALL_Z` 2.75 -> 2.81 m (deck at the wall faces), lip now 2.317 m: PASS.  A real actor-scale fix (art bible 7; the recipe's own doc promised >= 2.30 m) |
| v4_mixed | house door 2.374 m (battens), mill door 5.326 m (apron rafters): PASS | the mill wing's gate is now applied too: 102 of 102 kept; the final JSON is byte-identical | apron / smock tower: 0 leaks; **house roof / mill tower: 13 of ~23k rays leak** (pass the trimmed roof 0.3 m from the drum face into the space under it: abutment posts, eave closure, wall plate, z 2.1-3.1) | 58 deg: flags now set by the frame; the recipe's explicit `DOOR_INFILL_DECK` / `EAVE_CLOSURE_DOOR_HALF_DEG` were removed (geometry identical); the V4M `tmpl_lod` rule is unregistered after the mill wing | **opt-out** of that one junction in the recipe (`OPT_OUT`): accepted variant, geometry frozen here; queued for `junctions.roof_tower_flashing` |

The probe's false positives at free covering edges were removed before the buildings were judged (targets must lie
inside the roof build-up and at least 0.2 m from an eave lip / verge / comb tip); without that, eave rolls next to
the keep turret and the v3 round end reported thousands of "leaks" that were rays coming round the eave.

### Verification: all seven rebuilt into `kit/baseline/2_guardrails/`

`tools/build_baseline.ps1 -Step 2_guardrails` (3 builds at once) after the last guard edit; v2 rebuilt again
(`-Only v2_tiered_hall`) after the final `tower_roof` sub-frame edit.  Fingerprints `2_guardrails/<id>.json`,
compared with step 1 (`1_consolidate`, identical to step 0):

| Building | Triangles | Geometry | UV | Mask | vs step 1 | decal_anchors.json | Build (s) |
|---|---:|---|---|---|---|---|---:|
| hilltop_keep | 1,166,874 | `d9c667967d7c32de` | `b2c490c5171a2199` | `e80fcf38200a4a8b` | same vertices and faces; polygon ORDER differs in one object (see below); a second build of the same code (`hilltop_keep_rerun.json`) gives the step-1 hashes `b2f847333a2ec943` / `0c1f12176f0f1235` / `c7ddfbfe5d33f6d8` | + `validation` block; 1 anchor moved 0.01 mm | 381 |
| wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` | `9c0dd5aecb5d869c` | `794266c3463d1240` | identical | byte-identical | 596 |
| tower_windmill | 1,146,243 | `89bf4a2a2c60e049` | `9f132597bb379825` | `04f7ade47b360102` | identical | + `validation` block; 1 anchor moved 0.01 mm | 235 |
| v1_stone_watchtower | 1,057,164 | `47e4208df661a5a9` | `9929b9e5101d3d5f` | `c8e787ab4b8e0bff` | identical | + `validation` block; anchors identical | 305 |
| v2_tiered_hall | 954,925 | `87ba64b7f9d4a746` | `15bb7bdc5ae3c360` | `e976015053c38848` | identical (both builds: before and after the `tower_roof` edit) | byte-identical | 446 |
| v3_longhouse_roundend | **483,508** (+4,631, +0.97 %) | `6a7a7ecbea54aa07` | `1a43d013c02f495e` | `27422448b80c6b19` | **changed (the clearance fix)**: 20 objects, every one of the body / roof / cone parts (the walls are 6 cm taller, the cull sees a different building); largest delta `LONG_body_wall_stones` +5,236 | 82 -> 76 anchors (27 identical, 14 moved, 41 removed, 35 new; `body.wall_z` 2.81) | 406 |
| v4_mixed | 938,453 | `2e87caad61b68d34` | `a73b4ef99fd15564` | `b6c2768f3068057b` | identical | byte-identical | 370 |

Every build exited 0; the only stderr line is the known numpy `All-NaN slice` warning from `mill_cap.py:194` (mill,
v4).  No delivered `.blend` / `decal_anchors.json` and no `signoff_*` folder was written.

**Found while verifying (pre-existing, not caused by the guards): the keep is not bit-reproducible run to run.**
In the first 2_guardrails keep build, `KEEP_wing_wall_stones` has the same 56,166 vertices (same order, max delta 0)
and the same 49,897 polygons, but 181 polygons near the end of the list are permuted, which changes all three of its
hashes.  A second build of the identical code reproduced the step-1 hashes exactly.  The order depends on memory
layout; the likely source is `core.nanite_clean`, which collects the edges to rotate / collapse in Python `set`s of
`BMEdge` (iteration order by object address) before `bmesh.ops.rotate_edges` / `collapse` append the new faces.  The
fix (insertion-ordered dicts) may re-order polygons in other buildings, so it belongs to its own step with its own
baseline; until then compare keep builds per object (`geom_diff.py`) and treat a pure polygon-order change in that
object as the known artefact.

---

## 1.8.0 (2026-10-17): consolidation -- one public API per concern (KIT ARCHITECT)

Phase-2 kit decision, client "Yes proceed", step 1 (kit consolidation).  Both kit reviews
(`director/kit_feasibility_director.md`, `director/kit_feasibility_technical.md`) listed parallel module families.
This release gives each concern ONE public entry point **without changing any building's geometry**: every old
name still exists as a thin wrapper or alias, and all seven kit buildings were rebuilt and fingerprinted against
the step-0 baseline (`kit/baseline/BASELINE.md`, the kit as it builds today).  The 1.7.x variant changes are still
recorded in `kit/changes/*.md` (not merged here); 1.8.0 sits on top of them.

### New modules (the consolidated public API)

| Module | Public API | Replaces (kept as wrappers / aliases) |
|---|---|---|
| `components/eave.py` | `eave_closure(g, r_b=None, mat="M_mortar", n_az=240, kind="ring" / "door" / "fill", **kw)`; `KINDS` (the historic constants per kind) | `conical_roof.build_eave_closure` (kind "door"), `round_roof_parts.eave_closure` and `tower_roof._eave_closure` (kind "ring"), `roof_junction.round_eave_fill` (kind "fill") |
| `components/openings.py` | `door(...)`, `window(...)`, `opening_spec(kind, ...)` -> an `Opening`; `Opening.at(position)`; `resolve(spec, family)`; the family dict builders `body_opening`, `wall_door`, `wall_window`, `annex_door`, `annex_window`, `drum_window`; `FAMILY_DEFAULTS` | `stone_body.opening`, `wall_openings.door_spec` / `window_spec`, `plank_doors.door_spec`, `windows.window_spec`, `drum_frame.window_spec` (= `drum_window_spec`) |
| `components/masonry.py` | `masonry_wall(g, name, path= / body= / round=, openings=, **kw)` + re-exports (`PathMap`, `SurfMap`, `path_stone_wall`, `round_stone_body`, `stone_body`, `framed_openings`, `coping_ledge`, `WALL_RUBBLE`, `BODY_RUBBLE`, `door`, `window`) | the choice between `stone_body` and `rubble_walls` (both kept, see below) |
| `components/plan_frame.py` | `PlanFrame(prefix, footprint, entrance, entrance_r, entrance_h, detail_rule, hygiene, ground_skirt, **dims)`, `rect_frame(...)`: a plain rectangular / free-form frame | borrowing `RoundFrame` for a building with no round part (the technical review's probe barn) |
| `components/finish.py` | `hidden_cull(g, family=None, **kw)`, `building_decals(g, family=None, **kw)`, `family_of(g)` | choosing among `round_` / `drum_` / `oct_` / `tower_` / `tier_` / `composite_hidden_cull` and the seven decal recipes |

New tool: `tools/check_headers.py` (parses every kit module header for documented signatures and reports the ones
that no longer match the code: unknown / missing arguments, stale defaults, full-signature headers that omit
parameters).  It reports 0 after this release.

### What each consolidation does

- **One eave closure.** `conical_roof.build_eave_closure` and `round_roof_parts.eave_closure` were one algorithm
  with different constants (door gap or closed ring, normals in or out, profile range, jitter / wobble seeds, the
  3 cm closed band).  They are now ONE implementation, `eave._ray_band`, statement for statement; the constants are
  the `KINDS` table.  `tower_roof._eave_closure` and `tower_roof._roof_deck` (byte-identical private copies of the
  `round_roof_parts` parts) are now aliases.  `round_eave_fill` solves its top from the cone's reference surface
  instead of ray-testing the built shingles, so it stays its own implementation (`eave._fill_band`) behind the same
  entry point (`kind="fill"`).
- **One polygonal bell-cast roof.** `bell_tier` now builds polygon tiers with ANY number of sides: sides != 8 (or
  `engine="pyramid"`) builds the tier with `pyramid_roof` / `PyramidSurface` and registers it like any tier, so
  `roof_flashing`, `roof_clearance`, `stone_body(below=)`, `tier_finial` and `tier_decals` work on it.  To make that
  possible, `PyramidSurface` and `OctRoof` now share one protocol: `n`, `tanh`, `phi`, `c`, `rot`, `p_lip`, `Pp`,
  `zb(p)`, `m_of_p`, `p_of_m`, `surf(k, x, p)` (added members only; nothing existing changed).
- **One stone-body module.** `masonry.masonry_wall` is the single entry point; `path=` / `round=` / `body=` select
  the builder.  All three take the unified opening specs.
- **One opening-spec API.** A recipe writes `door(width=1.0, height=2.10)` / `window(width=0.5, sill=1.25)` and
  hands the same spec to any wall builder: `stone_body` (place it with `.at(th_deg)`), `path_stone_wall` /
  `round_stone_body` (`(s, spec)` / `(az_deg, spec)` as before), the keep annex (`OctFrame(WDOOR=door().at(xc))`,
  also through `OctFrame.set`) and drum windows (`WIN_SPEC=[window(kind="lookout", ...)]`).  `None` sizes are the
  family defaults (`FAMILY_DEFAULTS`: the old spec functions' defaults, which differ per family).  Old family dicts
  pass through `resolve` unchanged, so every existing recipe builds the same objects.
- **The clashing `end_apron` names.** `junctions.end_apron` (a lead plate on a WALL face where a cut eave lip meets
  it) is now `junctions.wall_end_apron`; `roof_junction.end_apron` (the apron folded over a linear roof's eave NOSE
  against a cone) is now `roof_junction.cone_nose_apron`.  The kit calls the new names; `end_apron` stays in each
  module as a deprecated alias.
- **A plain generic frame.** `PlanFrame` publishes only what the generic modules read (`detail` / `ENTRANCE` for
  note 11, a buried-skirt ground cull, empty `OPENINGS` / `WALL_FACES` / `LINEAR_ROOFS` / `openings`, `sub()`,
  `name()`, `min_relief()`, `inside_plan()`, `extent()`, and any recipe dimensions as upper-case attributes).
  `composite_decals` no longer lays cone moss on a building without a cone, because a PlanFrame has no `R_EAVE`.
- **One cull and one decal entry point.** `finish.hidden_cull(g)` / `finish.building_decals(g)` dispatch on the
  frame's new `FAMILY` class attribute (`RoundFrame` "round", `DrumFrame` "drum", `OctFrame` "oct", `TierFrame`
  "tier", `PlanFrame` "plan") and its state (a drum with a tower roof -> "tower"; a round frame with path walls /
  linear roofs -> "composite").  `family=` overrides.  The family functions are unchanged and still callable.
- **Keep-family proxy, scoped.** `Building.activate()` (a no-op) is called by `build_building` and
  `build_compound` before every step and decal recipe; `OctFrame.activate()` and `TierFrame.activate()` point
  `oct_frame.FR` at themselves.  Two keep-family wings in one compound now each read their own table during their
  own steps.

### Additive changes to existing modules (defaults keep the old behaviour)

- `pyramid_roof.pyramid_roof(..., coll=None)`: the collection to build into (default `g.coll`).
- `pyramid_roof.PyramidSurface`: protocol members `phi`, `Pp`, `zb(p)`, `surf(k, x, p)`.
- `oct_frame.OctRoof`: class attributes `n = 8`, `tanh = TAN22`.
- `tier_roof.bell_tier(..., engine=None, pyramid=None)`; new private `_pyramid_tier`; `tier_finial` returns early
  for a pyramid tier (pyramid_roof already built its lead cap and turned finial).
- **One default changed, on an input no building uses:** `bell_tier(sides=None)` on a POLYGON body whose side count
  is not 8 used to force an octagonal OctRoof tier onto it; it now builds that body's own side count with the
  pyramid engine.  8-sided and round bodies are unchanged (v2 has only those).
- `tier_frame._roof_plan_box`: corner radius from the roof's `n` (default 8: the same expression as before).
- `tier_frame.roof_support`: doc only (it already read `roof.phi`).
- `assembly.Building`: `activate()` and `FAMILY = None`; `frame.RoundFrame.FAMILY = "round"`,
  `drum_frame.DrumFrame.FAMILY = "drum"`, `oct_frame.OctFrame.FAMILY = "oct"`, `tier_frame.TierFrame.FAMILY =
  "tier"`; `OctFrame.activate()`, `TierFrame.activate()`.
- `stone_body._prep_openings`, `wall_openings.opening_rects` / `opening_cut` / `build_opening`,
  `drum_frame.win_list`, `OctFrame.__init__` / `OctFrame.set`: accept `openings.Opening` specs (`resolve`); any
  other dict passes through unchanged.
- `drum_frame.WINDOW_FW` is now the same object as `openings.DRUM_WINDOW_FW` (same values).

### Kept as separate implementations (no identical merge possible), and why

- **`OctRoof` (+ `oct_roof.build_cap`) vs `PyramidSurface` (+ `pyramid_roof`).** The two surfaces integrate
  different profiles: OctRoof a 600-sample pitch table (`d_pts` / `a_pts`) with a low-frequency eave wave
  (`n1` noise) and sag normalised by the full run; PyramidSurface a 4001-sample cosine bell with sag normalised by
  the lip distance.  `build_cap` is octagon-specific throughout (`TAN22`, `range(8)`, `(8, 2)` random draws, the
  wall-head band and the tier decals).  Moving the octagonal tiers onto PyramidSurface would move every roof vertex
  of the keep and v2.  They now share one protocol, and `bell_tier` routes every non-octagonal tier to
  PyramidSurface.
- **`roof_junction.round_eave_fill` vs the ray-tested eave band.** The fill's top follows the cone's reference
  surface (+2 cm, no ray test against the built shingles, `n_az + 1` stations, `geom.Acc` + `finalize`); the band's
  top is ray-tested and built through `g.acc`.  Same entry point (`eave_closure(kind="fill")`), separate body.
- **`stone_body` vs `rubble_walls.path_stone_wall` / `round_stone_body`.** All three use the one stone generator,
  but with different plan maps (SurfMap / PathMap / round_map_factory), different coursing tables (the two
  `RUBBLE_CFG`s differ in course heights, stone lengths, `slant`, `ch_mix`, `pinch`), different quoin methods
  (rubble-layout corner bands vs solid `obox` blocks) and different mortar-body cuts.  Expressing one through
  another changes every stone.  Same entry point (`masonry_wall`), three bodies.
- **The seven hidden-geometry culls and seven decal recipes.** Each family's view set, target list and placement
  rules are tuned to its geometry and recorded in signed-off / accepted builds; they stay, behind `finish`.
- **`oct_frame.FR` (the keep family's module-global proxy) is NOT removed.** The keep family reads it 401 times in
  11 modules (`annex`, `oct_cull`, `oct_frame`, `oct_hall`, `oct_roof`, `plank_doors`, `stone_cone`, `thatch`,
  `turret`, `windows`, plus `tier_frame`'s activation).  About 30 envelope functions (`apo`, `hall_map`, `fmap`,
  `q_rr`, `wing_under`, `thatch_low`, `tur_r`, `skirt_z_at`, `cush_*`, `get_pool`, `place` ...) take no frame
  argument and are called from deep inside thatch / turret / stone-cone loops, and `oct_roof.build_cap` (used by
  v2 through TierFrame) reads `FR.units`, `FR.min_relief`, `FR.pools` and `FR.POOL_SPECS`.  Removing the proxy means
  changing the signature of every one of those public functions and threading `g` through every call chain of the
  keep family: a rewrite of the family, not a consolidation, and not verifiable inside this step's time box.  The
  hash risk itself is low (pure plumbing), so it is the right next step for the keep family when it is next worked
  on.  This release scopes the proxy instead (`activate()` before every step), which removes its practical failure
  (two keep-family wings in one compound).
- **Not touched: the wattle_roundhut +1,736-triangle drift** recorded in `BASELINE.md` (the v4 change to
  `build_eave_closure(thickness=0.03)`).  The consolidated "door" kind keeps `thickness=0.03` as its default, so
  the hut builds exactly the baseline; the producer still has to decide which hut is the reference.

### Stale module header signatures fixed (found by `tools/check_headers.py`)

`decal_gate.cast_raw(probe, origin, direction, dist=10.0)`; `geom.beam(acc, p0, p1, w, h, c, mat, ...)`;
`stones.stone_skin(P, faces, rng, ..., min_relief=...)`; `daub.build_wattle / build_daub / build_inner_skin(g, coll)`,
`daub.plinth_under_coat(g, V)`; `doors.build_door(g, coll, seed=1212)`, `doors.build_step(g, coll)`;
`finial.build_collar_finial(g, coll)`; `frame.RoundFrame(prefix, radius, eave_z, ...)` (was "RoundFrame(spec)");
`plank_doors.make_pintle(acc, i)`; `square_cabin.square_cabin(...)` (bearers default None, and the missing `bed_r`,
`bed_fill`, `finial_scale`, `roof`, `roof_fn`); `pyramid_roof.pyramid_roof(..., coll=None)`;
`tier_roof.roof_flashing(g, roof_name, body_name, ...)`; `wall_openings.opening_rects(sp)` / `opening_cut(sp)` /
`build_opening(g, sp, ...)`.  The headers of every module this release changed (`conical_roof`, `round_roof_parts`,
`tower_roof`, `roof_junction`, `junctions`, `stone_body`, `rubble_walls`, `tier_roof`) also name the new API.

### Verification

- **In-process A/B before the builds** (old kit snapshot vs 1.8.0, same scene, vertex / face / material / Mask / UV
  digests): `build_eave_closure` (default 3 cm band, `thickness=0`, frame `EAVE_CLOSURE_DOOR_HALF_DEG`),
  `round_roof_parts.eave_closure`, `tower_roof._eave_closure`, `tower_roof._roof_deck`, `round_eave_fill` (default
  and with `r_off` / `skip`) all identical; all 18 opening-spec cases identical (each old spec function, and each
  unified spec resolved to its family, against the old function's dict, key order included).  Every kit module
  imports.  A smoke build of the new API (a PlanFrame barn via `masonry_wall` + `door` / `window` + `linear_roof` +
  `building_decals`; a TierFrame with a hexagonal and a square body under 6- and 4-sided `bell_tier`s, a chimney
  body through the hexagonal tier with `roof_flashing`, `tier_finial`, `building_decals`) built and saved cleanly
  (scratch only, not a deliverable).
- **All seven kit buildings rebuilt** after the last code edit, to `kit/baseline/1_consolidate/<id>/` with
  `tools/build_baseline.ps1 -Step 1_consolidate` (3 builds at once), fingerprinted with `tools/geom_hash.py`
  (`1_consolidate/<id>.json`) and compared with the step-0 baseline:

| Building | Triangles | Geometry hash | UV hash | Mask hash | vs baseline | decal_anchors.json | Build (s) |
|---|---:|---|---|---|---|---|---:|
| hilltop_keep | 1,166,874 | `b2f847333a2ec943` | `0c1f12176f0f1235` | `c7ddfbfe5d33f6d8` | identical | byte-identical | 386 |
| wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` | `9c0dd5aecb5d869c` | `794266c3463d1240` | identical | byte-identical | 571 |
| tower_windmill | 1,146,243 | `89bf4a2a2c60e049` | `9f132597bb379825` | `04f7ade47b360102` | identical | byte-identical | 245 |
| v1_stone_watchtower | 1,057,164 | `47e4208df661a5a9` | `9929b9e5101d3d5f` | `c8e787ab4b8e0bff` | identical | byte-identical | 310 |
| v2_tiered_hall | 954,925 | `87ba64b7f9d4a746` | `15bb7bdc5ae3c360` | `e976015053c38848` | identical | byte-identical | 491 |
| v3_longhouse_roundend | 478,877 | `73e77867096725ec` | `71215dfc7294b03a` | `3d5ef6b3dc13b4fc` | identical | byte-identical | 416 |
| v4_mixed | 938,453 | `2e87caad61b68d34` | `a73b4ef99fd15564` | `b6c2768f3068057b` | identical | byte-identical | 371 |

  Every build exited 0 and saved its `.blend` and anchors; the only stderr line is the known numpy
  `All-NaN slice` warning from `mill_cap.py:194` (mill, v4), as in the baseline.  No build script was edited (all
  seven already had their output override); no delivered `.blend` / `decal_anchors.json` and no `signoff_*` folder
  was written.  The hut's triangle count is the baseline's 878,355 (the open drift question above), not the table's
  876,619.

---

## 1.6.1 (2026-10-16): multi-process hidden-geometry cull on Windows (producer, desktop handoff)

- **`core.visibility_cull`** used `multiprocessing` with `fork`, which Windows does not have, so every build on the
  desktop silently ran the cull on one core ("visibility: single process").  Where `fork` is unavailable it now runs
  the SAME chunks through the SAME `_vis_worker` in a `spawn` pool (`_vis_spawn_pool`, `_vis_spawn_init`,
  `_vis_spawn_worker`): one pool per call, each worker rebuilds the BVH once from the same triangle lists.  The pool
  starts with the pre-bpy `sys.path`, because after `import bpy` the parent's path resolves `bpy` to Blender's internal
  `scripts/modules/bpy`.  Linux / macOS (`fork`) are unchanged; any pool failure still falls back to one process.
- **Spawn workers are capped at 2 per build** (environment variable `VILLAGE_CULL_PROCS` overrides it). Each spawn
  worker holds its own BVH copy, and with four variant builders on one 16 GB desktop builds ran out of memory. The
  cull result does not depend on the worker count.
- **A dying spawn worker no longer hangs the build.** The pool is a `concurrent.futures.ProcessPoolExecutor`
  (not `mp.Pool`): a worker killed by MemoryError raises `BrokenProcessPool`, and the rest of that cull runs in one
  process with the same chunks and the same result. Tested by killing a worker on purpose: the error was raised in
  0.1 s, and spawn and single-process results still matched.
- **Build scripts must keep their build under `if __name__ == "__main__":`** (spawn re-imports the script in every
  worker).  All three hero scripts already do.
- **Verified** (all three rebuilt to scratch, in parallel): hilltop_keep **1,166,874**, wattle_roundhut **876,619**,
  tower_windmill **1,146,243**, all identical to the records.  Build times on the Ryzen 5 5600X with three builds at
  once: keep 587 -> 325 s, hut 829 -> 364 s, mill 345 -> 218 s.

### Hero gates closed (client direction, producer note 12)

- The interrupted keep round-10 fixer left opt-in options in `components/thatch.py` (`thatch_wing_roof(crisp=...)`,
  `d_roll` bundle butts, `thatch_junctions(point_roll_ends=...)`, the "kit 1.6.0 (keep round 10)" docstrings).  They
  are unverified and unused: the keep recipe was restored to its round-9 options (1,166,874 tris, above).  Its other
  partial edits are saved in `director/partial_fix_hilltop_keep_r10.patch`.
- From here on, variant builders record kit changes in `kit/changes/<variant id>.md`; the producer merges them here.

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
