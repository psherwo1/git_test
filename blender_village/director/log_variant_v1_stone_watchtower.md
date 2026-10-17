# Variant log: v1_stone_watchtower

## v1_stone_watchtower round 1 — builder entry

**What it is.** A round stone lookout tower assembled only from kit modules (producer note 12). It has a 4.7 m
battered coursed-rubble drum (r 2.35 m at the foot, 2.18 m at the top, an even batter of about 1.2 deg) that is
8.70 m to the top of a dentil-corbelled cornice. On the corbel table sits a rubble parapet, set 0.24 m out and
0.95 m tall with a dressed coping. Above that is a 56 deg chunky-shingle cone with a 15 deg bell-cast eave that
reaches 0.72 m beyond the parapet. It has a lead hat and a spike finial. The eave lip is at 9.31 m, the coping top
at 9.77 m and the finial tip at 15.25 m. The arched door (1.05 m clear, springing at 1.65 m) faces -Y with its
built-in step. Four slit windows are stacked up the shaft at 2.60, 4.15, 6.55 and 6.75 m, at azimuths 62, -128,
-18 and 150 deg, so they read as stair lights rising round the tower. A string course with a balustrade band marks
the upper-storey floor at 5.3-5.7 m. There is no arcade and no rotor.

How it differs from the mill drum: it is twice as tall, slimmer (H/D 1.9 against the mill's 0.9) and has larger
rubble (course height 0.10-0.22 m, length 0.20-0.70 m). It has no arcade, no apron and no smock tower. The silhouette
is a crown of corbels and parapet under a deep, overhanging witch-hat roof.

**Recipe** (`buildings/variants/v1_stone_watchtower/build_v1_stone_watchtower.py`, 48 code lines, one `KIT` table):

| step | module | parameters |
|---|---|---|
| 1 | `drum_wall.round_stone_drum` | r 2.35 to 2.18, height 8.70, `batter_top="full"`, band (5.30, 5.40, 5.57, 5.67), door 1.05 / 1.65, `arcade=dict(n=0)`, 4 windows + `window_z` |
| 2 | `drum_wall.drum_wall_core` | default |
| 3 | `drum_door.entrance_step` | default |
| 4 | `tower_roof.drum_ceiling` **(new)** | z 3.45 |
| 5 | `tower_roof.corbelled_parapet` **(new)** | height 0.95, proj 0.24 |
| 6 | `tower_roof.round_tower_roof` **(new)** | pitch 56, eave_out 0.72, bell 15 deg over 1.0 m, collar r 0.62 |
| 7 | `drum_frame.drum_finish` | `checks=False` (no rotor) |
| 8 | `tower_roof.tower_hidden_cull` **(new)** | procs 2 |
| decals | `tower_decals.round_tower_decals_gated` **(new)** | snap, validate and audit gates |

Frame: `DrumFrame(detail_rule=True, rubble=...)` with larger rubble.

**New kit modules** (details in `kit/changes/v1_stone_watchtower.md`):
- `components/tower_roof.py`:
  - `corbelled_parapet`: a coursed rubble parapet set out on any drum's corbel table. Its bottom course is bedded
    3 cm into the cornice cap, it has a dressed coping, and a continuous mortar backing sits behind it.
  - `round_tower_roof`: a conical shingle roof with a bell-cast eave on ANY round wall head. It runs the hut's own
    cone, rafter, batten, shingle, under-lap, wall-plate and finial modules on a `RoundFrame` sub-frame. The eave
    height is solved so the plate beds on the wall head. The plate moves out until the rafters clear the coping by
    7 cm or more.
  - Junction pieces: a sarking deck, closed over the overhang as a boarded soffit slab, and a mortar eave closure.
  - `drum_ceiling` and `tower_hidden_cull`.
- `components/tower_decals.py`: `round_tower_decals(_gated)`, decal anchors for any stone tower without a rotor.

**Existing modules changed.** These are optional parameters only. Their defaults reproduce the old builds.
- `drum_frame`: `WIN_DZ`, `BATTER_TOP`, `win_dz()`, and `hw_window(dz=)`.
- `drum_wall`: `round_stone_drum(window_z=, batter_top=)`, per-window `dz` in the slits, the wall core and
  `inside_clear`, any number of windows, and a drum with no arcade (two guards on empty arcade zones).
- Hero re-runs went to scratch. All three are identical to their records:
  - hilltop_keep: 1,166,874
  - wattle_roundhut: 876,619
  - tower_windmill: 1,146,243

**Junctions checked**, in close-up renders in the builder's scratch and in the review set:
- **Parapet on the cornice:** bedded, no shadow gap.
- **Plate on the coping:** bedded 1.2 cm.
- **Rafters over the coping arris:** 10 cm clear.
- **Eave closure:** runs between the rafter feet into the shingle stack.
- **Deck:** under every shingle. The first round showed a sunlit sliver on the parapet through an overhang joint.
  It was fixed by closing the overhang with the soffit slab.
- **Collar over the top course:** the top course was made to run 15 cm or more in under the lead hat.
- **Door passage and ceiling:** closed.
- **Slit embrasures:** closed. This is the kit's own geometry.

**Stats** (`renders/variants/v1_stone_watchtower/round_01/stats.json`, all six views at 24 samples):
- **Triangles:** 1,138,244.
- **est_hidden_pct:** 12.6 %.
- **Material slots:** 8, all from the palette.
- **mask_attribute_missing:** none.
- **Decal anchors:** 81. The audit and both gates found 0 failures.
- **Objects:** 141, of which 117 are linked duplicates of 24 pooled meshes, plus pooled pegs.
- **bbox:** 6.44 x 6.36 x 15.26 m, base centred, z from -0.005.
- **.blend:** 28.6 MB, compressed.
- **Build:** about 20 min with 2 cull workers on the shared machine.

The final build was written to scratch and then copied in, because two attempts died when other builders' jobs
ran the machine out of memory.

**Known gaps (not fixed in round 1):**
- The parapet is solid. It has no lookout openings or embrasures, so the lookout reading rests on the height, the
  slits and the crown. A jettied timber gallery module would make the lookout read more strongly and is the
  natural next module.
- The balustrade band is the mill's decorative blind band. It is reused as a storey string. A plain string-course
  option (band without balusters) is not in the kit yet.
- The interior above the ground floor is only the ceiling blocker; there are no upper floors.
- The hut's `conical_roof.build_rafters` still models full-length rafters in the "doorway" back arc. They are hidden
  under the deck and are culled.
- `conical_roof.build_eave_closure` still hard-codes `HUT_` object names. The new module carries a generic
  replacement instead of editing it.
- The base-stone cull is CPU-heavy: 10-13 minutes of the build.

## v1_stone_watchtower round 1 — score 8.0/10

**Graded by:** Art Director, against the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only; ground dressing not scored (note 10).

**Reviewed:** recipe `buildings/variants/v1_stone_watchtower/build_v1_stone_watchtower.py`; `build.log`; new modules `kit/village_kit/components/tower_roof.py` and `tower_decals.py`; `kit/changes/v1_stone_watchtower.md`; all six views in `renders/variants/v1_stone_watchtower/round_01` (hero, front, side, back, aerial, actor_closeup), `stats.json`, `hidden.json` and `buildings/variants/v1_stone_watchtower/decal_anchors.json` (81 anchors). Compared with ref1/ref2/ref3 and the director crops.

**Director close-ups** (`renders/variants/v1_stone_watchtower/round_01/director_extra/`, scripts `dir_render_r01.py` and `dir_lineup_r01.py`, same clay / sun / world as render_review):
- j01, j02: parapet on the corbel table and cornice cap (tele from the ground, and at eave level).
- j03, j04: soffit, rafter feet, wall plate and eave closure seen from below.
- j05: eave-lip profile on the silhouette. j06: eave over the parapet from a crane height.
- j07, j08: lead hat over the top shingle course, and the finial.
- j09, j10: string course / balustrade band on the shaft.
- j11, j12: slit embrasures at az -18 and az 62.
- j13: door step, threshold and footing. j14: door depth. j15: footing at the back.
- j16: thumbnail at 45 m. j17: top storey at a neighbour's eye level.
- j18: distinctness line-up of wattle_roundhut, the watchtower and tower_windmill.

| # | axis | score | one-line reason |
|---|---|---|---|
| 1 | Silhouette and massing | 7.8 | A tall, slim drum under a witch-hat cone with a corbelled crown, clearly of this village. But the top storey is blind (j17): the "parapet" is a roofed, unbroken rubble ring under the eave and the slits read as dots at 30 m. So it reads as a generic roofed tower or dovecote, not as a lookout. |
| 2 | Proportion and actor scale | 8.3 | The door (1.05 m, crown ~2.3 m), step and footing are right beside the 1.8 m figure. Drum 4.7 m, eave lip 9.31 m and tip 15.25 m are inside the brief. The slits keep the mill's hard-coded 0.16 x 0.55 m opening, too small for a 9 m shaft. The batter is 1.2 deg, under the bible's 2-4 deg. |
| 3 | Construction logic | 8.4 | The parapet is carried on dentil corbels and the cornice cap. The plate is bedded on the coping and the rafters clear the coping arris. The lead hat sits over the top course, and the door has its step. The mid-shaft blind balustrade is decoration with nothing behind it. |
| 4 | Seams and junctions | 8.7 | Every module junction closed in the close-ups: parapet into the cornice cap, soffit slab, eave closure between the rafter feet, plate on the coping, top course under the lead hat, slit embrasures, door step to the drum, and footing to Z=0. There are no see-through pixels, light leaks or visible clipping. |
| 5 | Distinctness and reuse | 8.5 | Unmistakably different from the hut and the mill (j18). The recipe is 8 kit steps from one table. The new head parts are generic modules: `round_tower_roof` works on any `WALL_HEAD` and reuses the hut's cone, rafter, shingle, plate and finial modules unchanged. Points lost: the mill's signature balustrade band reused as the string course; `_eave_closure` forks `conical_roof.build_eave_closure`; dummy arcade parameters are needed for `n=0`. |
| 6 | Technical compliance | 8.1 | 1,138,244 triangles, 12.6 % hidden, 8 palette slots, no missing `Mask`, 81 gated and plausibly placed anchors, 117 linked duplicates of 24 pooled meshes, deterministic. But the build takes about 20 min against the 10-min limit in art bible section 8. 765 s goes on the base-stone ray cull, which removes only 7.8 % of those polygons, and two builds ran out of memory. |

**Overall: 8.0/10** (lowest axis 7.8, rounded up). **Below the 8.2 pass mark: round 2 required.**

**Verdict.** This is a genuinely modular build. The recipe is short and declarative. The new tower head landed in the kit as reusable, parameterised modules, the hut's roof stack now runs on any round wall head, and every junction I rendered is closed. The variant fails the brief's one hard requirement, though: it must read as a LOOKOUT tower. The crown is a blind, roofed rubble ring, the slits are mill-sized dots, and the only mid-shaft feature is the mill's blind balustrade. At thumbnail size it is a handsome round tower with no evidence of watching. Round 2 is a module job, not a detail job: lookout openings, a plain string course and parameterised slits, plus bringing the build back under 10 minutes. No surface detail is requested.

**Strengths**
- The recipe is truly assembled. It is 48 lines with 8 kit steps driven by one `KitParams` table, and the recipe file holds no bespoke geometry.
- New parts are reusable kit modules. `round_tower_roof` sits on any `g.WALL_HEAD` through a `RoundFrame` sub-frame and reuses the hut's cone, rafter, batten, shingle, plate and finial modules unchanged. `corbelled_parapet` works on any drum-family cornice, and `drum_ceiling`, `tower_hidden_cull` and `round_tower_decals_gated` are general too.
- Changes to existing modules are optional parameters only. All three heroes were re-run and match their recorded triangle counts exactly.
- Junction engineering is solid. The parapet is bedded 3 cm into the cornice cap, the plate is solved to bed on the coping, rafter clearance over the coping arris is enforced (10 cm), a soffit slab closes the overhang, the eave closure is generic, and the top course runs 15 cm or more under the lead hat. No leaks were found in j01-j08.
- Clearly distinct from the heroes in the line-up (j18). The slim proportion (H/D 1.9) and the deep witch-hat crown give a new village silhouette from shared modules.
- Clean technical stats (palette, Mask, hidden %, pooling). The decal anchors are physically plausible: damp and moss at the foot and on north faces, streaks under the sills and band, rust under the hinges, cracks at the openings.

**Must-fix (round 2)**
1. **Lookout read (silhouette): `tower_roof.corbelled_parapet` and the top storey.** At z 8.65-9.77 the parapet is an unbroken rubble ring entirely under the eave (lip 9.31 m), and the storey below it has no opening wider than a slit (j17, j16). The tower does not read as a lookout. Add lookout openings as a reusable parameter, for example `corbelled_parapet(openings=dict(n=4, az=(0, 90, 180, 270), w=0.55, h=0.85, sill=...))`, or a `lookout_windows` option in `drum_wall`. Give them dressed jambs and lintels from the kit's existing surround modules, with a dark blocker behind at about 1.5 m depth (note 6). Place them so they are fully visible below the eave lip from the ground at 30 m: either raise the parapet so the eave lip clears the opening heads, or set the openings in the top storey of the drum (sill about 7.1 m). The alternative is the brief's other option, a new reusable `jettied_gallery` module (timber gallery on the corbels, open between posts, under the eave). One of the two must make the watch level read in the hero, front and side views.
2. **String course: `drum_band` (used through `round_stone_drum`, zones band 5.30-5.67 m).** The mill drum's blind balustrade (63 balusters) is reused as a storey string course. It is the mill's signature and is decoration-only on a solid shaft (j09, j10). Add a `style="plain"` (or `balusters=False`) option to `drum_band`: a dressed projecting string course about 0.2-0.3 m tall with 6-8 cm projection and a drip, no balusters. Use it on this tower. The mill default must stay unchanged.
3. **Slit windows: `drum_frame.DrumFrame.WIN` / `hw_window` and `drum_wall.build_slit_windows`.** The slit is hard-coded to the mill's 0.16 x 0.55 m opening (`WIN` z0 1.30 / z1 1.85, jamb courses `jz` [1.30, 1.56, 1.85], and the absolute thresholds 1.17 / 2.04 in `hw_window`). On a 9.3 m shaft the slits read as dots at 30 m (j16). Expose the clear width and height as parameters and derive the jamb courses and `hw_window` bands from them. Use about 0.16-0.20 x 0.90-1.00 m here. Also re-space `window_z`: 6.55 and 6.75 m are only 0.20 m apart. Use a rising sequence with the azimuth turning one way (for example 2.6 / 4.2 / 6.3 / 7.4 m) so the slits read as stair lights.
4. **Build time (art bible section 8, at most about 10 min): `tower_roof.tower_hidden_cull`.** The full build takes about 20 min with 2 workers. 765 s of it goes on ray-culling `WATCH_base_stones` against 515 viewpoints, which removes only 31,022 of 397,597 polygons, and two builds ran out of memory. Pre-cull analytically before ray casting: drop stone faces whose normal points inward, or whose centroid lies inside the wall-core radius plus the mortar recess. Restrict the base-stone ray pass to a reduced view set (the drum's eye-level and crane rings only). The full build must finish in 10 minutes or less with 2 workers, keeping est_hidden_pct at or below 15 %.

**Nice-to-have**
- Merge `tower_roof._eave_closure` and `conical_roof.build_eave_closure` into one prefix-agnostic function with a `facing=` parameter, with the hut defaults reproducing the hut.
- `round_stone_drum(arcade=None)` should mean "no arcade" without dummy `z_sill`, `clear_w` and `clear_h` values.
- `drum_finish` should skip the rotor checks automatically when no rotor exists, instead of the recipe passing `checks=False`.
- Batter is 1.2 deg against the bible's 2-4 deg; for example `r_base` 2.45 with `r_top` 2.18.
- Roof pitch is 56 deg, just above the bible's 48-55 deg cone range; 54 deg would sit inside it.
- `plaster_patch` anchors are on `M_stone`. Note 11 reserves them for daub and rendered walls, so use `repair_patch` there.
- `conical_roof.build_rafters` still makes full-length rafters in the hut's "doorway" arc; add a flag to turn them off.
- Fold the family-specific culls (`oct_cull`, the drum cull, `tower_hidden_cull`) into one `hidden_cull(g, views, targets)`.


## CLIENT DIRECTION (2026-10-16, after round 1) — the lookout read

Client's words: "for the watchtower, i am roughly ok with that silhouette. set dressing later can sell the image. alternatively, containing the cylindrical base with a square cabin perched atop it would probably be more instantly recognizable as a watch tower"

- **The round-1 silhouette is acceptable to the client.** "Does not read as a lookout" is no longer a blocking must-fix by itself; set dressing will sell it later. Do not fail the tower on the lookout read alone.
- **Preferred improvement (do it if it fits the round's time-box):** crown the cylindrical stone base with a **square timber lookout cabin perched on top**. Make it a new reusable kit module, for example `square_cabin(g, on=<wall head>, side, height, overhang, corbels/brackets, openings, roof)`. It needs:
  - a square plan wider than the drum top, cantilevered on brackets or corbels;
  - plank or framed walls with real lookout openings on all four sides;
  - its own roof, square pyramid or hipped, with the kit's shingles and finial.

  This also gives the kit a square timber-cabin module that other buildings (gatehouses, harbour houses) can reuse.
- The other round-1 must-fixes still stand: slit size as parameters, a plain string-course option instead of the mill balustrade, and build time.

## v1_stone_watchtower round 2 — builder entry

**What changed.** Round 2 was module work only. No surface detail was added. All four must-fixes were handled
in the kit, and the recipe stays one declarative `KIT` table: 8 steps, 51 code lines.

1. **Lookout read: a watch storey of reusable lookout windows.** I took the director's "top storey of the
   drum" option.
   - `round_stone_drum(lookouts=dict(n=4, az0=0, w=0.65, h=1.00, sill=6.85))` adds four 0.65 x 1.00 m lookout
     windows at az 0 / 90 / 180 / 270. One sits on the door axis, so the front view shows door, string course
     and lookout stacked on one line.
   - Each lookout has dressed jambs in 3 courses, a projecting sill with a drip (1.21 m) and a 0.24 m lintel
     (1.33 m). These are the drum's own surround module, now sized from the opening.
   - Behind each opening is a straight mortar reveal through the wall (to 0.66 m) and a closed dark room 1.5 m
     deep behind the face (note 6). The room has a boarded floor flush with the sill, a boarded ceiling 0.30 m
     above the head, and plastered sides and back. This is the new `drum_wall.lookout_room` (object
     `WATCH_lookout_rooms`, 96 tris, not culled).
   - Heads are at 7.85 m and the lintel tops at 8.10 m, under the 8.25 m cornice. The eave lip is at 9.34 m with
     r 3.14. From the ground at 30 m the sight line clears the eave by more than 1.5 m, so every opening is fully
     visible (`round_02/builder_extra/c01_watch_30m.png`; the 45 m thumbnail is `c05`).
   - The kind is generic: `window_spec(kind="lookout")` works on any drum-family building.
2. **String course: `zones=dict(string=(5.35, 5.60))`.**
   - The new `drum_band.string_course` is a plain dressed projecting course, 0.25 m tall and 7 cm proud. It has
     a weathered top and a 1.4 cm drip lip at the nose, and no balusters.
   - Selecting it through `zones=string` sets the new `DrumFrame.BAND_STYLE="plain"`. The mill's balustrade band
     is still the default and is byte-for-byte the same code path (re-indented only). See `c03_string_course`.
3. **Slit windows: parameterised.**
   - The new `drum_frame.window_spec(clear_w, clear_h, sill, kind)` derives the jamb courses (about 0.30 m each,
     faces alternating), the sill and lintel sizes and heights, and the rubble keep-out bands (`zb` / `zt` /
     `hw_*`) from the clear size.
   - `hw_window(w=)`, `inside_clear`, `_drum_openings` and `build_slit_windows` read the spec of each window
     through `win_list(g)`. The mill keeps `g.WIN` and its literal 1.17 / 2.04 / 0.31 / 0.37 numbers.
   - This tower has `window_size=(0.18, 0.95)`: three stair lights, each with 3 jamb courses and a splayed, closed
     embrasure. They rise clockwise: 2.50 m at az 45, 3.95 m at az -45, 6.10 m at az -135.
   - Slit 2 was lowered from 4.10 to 3.95 after a self-check close-up. A 9 cm strip of pinners between its lintel
     and the string-course drip became a full rubble course (`c04_slit`).
4. **Build time: `tower_roof.tower_hidden_cull`.**
   - Step 1, `drum_precull`: an analytic pre-cull that removes drum stone and mortar faces wholly behind the wall
     core, and inward faces behind the mortar skin. Faces near openings are never touched. It removed 3,954
     polygons in 0.2 s.
   - Then ONE ray pass, `drum_ray_cull`, over all 11 targets on a reduced view set: 323 views, made of eye / knee
     rings, lookout-level, eave-level and crane rings, door close-ups and the review cameras, against round 1's
     515.
   - Each polygon is tested only against the views whose sight line does not pass through the closed core shell
     (`drum_view_masks`, a chord test against the core cylinder, z 0.05 m to the cornice). The probes and the hit
     rule are `core.visibility_cull`'s. The mean is 163 of 323 views for a drum stone. There is one BVH and one
     2-worker pool.
   - `WATCH_base_stones` now takes 130 s on a moderately loaded machine (scratch run, total build 5:08), or 298 s
     with the CPU pinned at 100 % by three other builders (the deliverable run). Round 1 took 765 s.
   - The deliverable build took 9 min 21 s wall with `procs=2` while the CPU sat at 100 % (other agents' keep,
     v2 and v3 builds). The cull removed 50,037 polygons. No out-of-memory errors.

**Nice-to-haves taken**
- Batter: `r_base` 2.48 to 2.18 gives 2.1 deg (5.0 m at the foot).
- Roof pitch: 54 deg.
- `arcade=dict(n=0)` alone now means "no arcade".
- The anchor beside the door is now `repair_patch`. `plaster_patch` stays only on the plastered passage, so
  there is 1 of them.
- Window decal anchors (sill lichen and streaks, soot over the heads, head cracks) are derived from each window's
  spec.

**Stats** (`renders/variants/v1_stone_watchtower/round_02/stats.json`, all six views at 24 samples):
- **Triangles:** 1,106,412.
- **est_hidden_pct:** 11.8 %.
- **Material slots:** 8, all from the palette.
- **mask_attribute_missing:** none.
- **Objects:** 81. 56 of them are linked duplicates of 12 pooled corbel and peg meshes. The balusters are gone.
- **bbox:** 6.43 x 6.36 x 15.01 m, base centred, z from -0.005.
- **.blend:** 28.6 MB, compressed.
- **Decal anchors:** 93, gated: snap, validate, then audit with 0 failures.

**Kit changes** are in `kit/changes/v1_stone_watchtower.md`, under "Round 2":
- New functions: `window_spec`, `win_list`, `string_course`, `lookout_room`, `drum_precull`, `drum_view_masks`,
  `drum_ray_cull`, `tower_views_lite` and `tower_head_views`.
- New optional parameters and attributes on `hw_window`, `round_stone_drum`, `DrumFrame` and
  `tower_hidden_cull`. Their defaults keep the old builds.
- **Hero re-runs** (to scratch, after the last edit to an existing module):
  - tower_windmill: **1,146,243**, identical to the record
  - wattle_roundhut: **876,619**, identical
  - hilltop_keep: **1,166,874**, identical. All built without errors.

**Renders:**
- Review set: `renders/variants/v1_stone_watchtower/round_02/`. I inspected all six views: the watch storey
  reads in hero, front, back and aerial; the door, step and actor close-up are unchanged; no leaks were seen.
- Builder close-ups: `round_02/builder_extra/c01-c05`, covering the watch storey at 30 m and at a neighbour's eye
  level, the string course, a slit, and the 45 m thumbnail.

**Known gaps**
- Interiors and lighting:
  - Only the ground floor and the four lookout rooms have an interior. There are no upper floors or stair.
  - In strong sun the lookout rooms light up in the clay renders: their back wall shows grey, not black.
- Build time and culling:
  - The build-time margin depends on machine load. It was 5:08 on a moderately loaded machine and 9:21 with the
    CPU pinned at 100 %.
  - The analytic pre-cull removes little (about 1 %), because the kit's stones are already modelled without
    backs. Most of the gain comes from the per-polygon view masks.
- Kit debt carried over from round 1:
  - `_eave_closure` is still a fork of `conical_roof.build_eave_closure`.
  - The rotor checks are still switched off by `checks=False` in the recipe.
- Openings:
  - The lookouts are unglazed open openings, with no shutters or frames.
  - A thin row of pinners remains under the string-course drip lip above slit 2 (closed, no gap).


**Client direction after round 1 (square timber cabin).** I saw the "CLIENT DIRECTION (after round 1)" section
only when I appended this entry. It was added to this log after I read it at the start of the round. I followed
the parts that still stand: slit size as parameters, the plain string course and the build time. The lookout
openings keep the round-1 silhouette, which the client accepts, and make it read more strongly as a lookout.

The preferred `square_cabin(g, on=<wall head>, ...)` module is **not** built this round. It would mean:
- a square timber cabin wider than the drum, cantilevered on brackets;
- plank walls with lookouts on all four sides;
- a hipped or pyramid shingle roof with the kit's finial;
- a 9-minute rebuild, a render and a verification.

That does not fit the remaining time box. It is the natural round-3 module.

It would sit on the same `WALL_HEAD` contract that `round_tower_roof` uses, so the drum, the string course and
the stair lights carry over unchanged. Its lookout openings could reuse `window_spec(kind="lookout")` sizing.

Note for the producer: while this round ran, someone else edited my scratch close-up script and added "cabin"
shots (k01-k06). Another builder may already be working on the cabin.

**Concurrency note (this builder, 20:25).** At 20:22, while this round was being written up, someone else
replaced the recipe `build_v1_stone_watchtower.py` with a `square_cabin` version. That version drops the
lookouts, parapet and roof, and moves the slits to az 60 / -60 / 180. I did not revert it.

The `.blend`, `build.log` and `decal_anchors.json` (20:05) and `renders/variants/v1_stone_watchtower/round_02` in
the building folder all come from the lookout-storey recipe described above. Its `KIT` table is recorded in
`decal_anchors.json` under `kit_params` until the next rebuild overwrites it.

The kit modules from this round are independent of that recipe, so they serve both versions: `window_spec`,
`string_course`, `lookout_room` and the fast drum cull.


## PRODUCER NOTE (2026-10-16 ~20:25) — recipe on disk vs the round-2 deliverable

When the client's square-cabin direction was relayed, a second copy of the round-2 builder started. At 20:22 it rewrote `build_v1_stone_watchtower.py` for the square cabin. The **round-2 deliverable** is unaffected: the `.blend` (20:05), `decal_anchors.json` and `renders/.../round_02/` are the lookout-storey version and match each other. Grade round 2 on those files. The square-cabin version is being built separately as a preview in `buildings/variants/v1_stone_watchtower/square_cabin_preview/` and `renders/variants/v1_stone_watchtower/square_cabin_preview/`. It will be the starting point of round 3 if round 2 does not pass.

## v1_stone_watchtower round 2 — builder entry

**Note on the files.** The delivered `v1_stone_watchtower.blend`, `decal_anchors.json` and `round_02` renders are
this lookout build. Its exact KIT table is in `decal_anchors.json` (`kit_params`). Since then, following the
client direction, the recipe file builds the square-cabin crown instead (see the next entry). The lookout
parameters were `windows=(45, -45, -135)`, `window_z=(2.50, 3.95, 6.10)`, `window_size=(0.18, 0.95)`,
`lookouts=dict(n=4, az0=0, w=0.65, h=1.00, sill=6.85)`, plus `corbelled_parapet(height=0.95, proj=0.24)` and
`round_tower_roof(pitch_deg=54, ...)`.

**What changed.** Round 2 was module work only. No surface detail was added. All four must-fixes were handled
in the kit, and the recipe stays one declarative `KIT` table: 8 steps, 51 code lines.

1. **Lookout read: a watch storey of reusable lookout windows.** I took the director's "top storey of the
   drum" option.
   - `round_stone_drum(lookouts=dict(n=4, az0=0, w=0.65, h=1.00, sill=6.85))` adds four 0.65 x 1.00 m lookout
     windows at az 0 / 90 / 180 / 270. One sits on the door axis, so the front view shows door, string course
     and lookout stacked on one line.
   - Each lookout has dressed jambs in 3 courses, a projecting sill with a drip (1.21 m) and a 0.24 m lintel
     (1.33 m). These are the drum's own surround module, now sized from the opening.
   - Behind each opening is a straight mortar reveal through the wall (to 0.66 m) and a closed dark room 1.5 m
     deep behind the face (note 6). The room has a boarded floor flush with the sill, a boarded ceiling 0.30 m
     above the head, and plastered sides and back. This is the new `drum_wall.lookout_room` (object
     `WATCH_lookout_rooms`, 96 tris, not culled).
   - Heads are at 7.85 m and the lintel tops at 8.10 m, under the 8.25 m cornice. The eave lip is at 9.34 m with
     r 3.14. From the ground at 30 m the sight line clears the eave by more than 1.5 m, so every opening is fully
     visible (`round_02/builder_extra/c01_watch_30m.png`; the 45 m thumbnail is `c05`).
   - The kind is generic: `window_spec(kind="lookout")` works on any drum-family building.
2. **String course: `zones=dict(string=(5.35, 5.60))`.**
   - The new `drum_band.string_course` is a plain dressed projecting course, 0.25 m tall and 7 cm proud. It has
     a weathered top and a 1.4 cm drip lip at the nose, and no balusters.
   - Selecting it through `zones=string` sets the new `DrumFrame.BAND_STYLE="plain"`. The mill's balustrade band
     is still the default and is byte-for-byte the same code path (re-indented only). See `c03_string_course`.
3. **Slit windows: parameterised.**
   - The new `drum_frame.window_spec(clear_w, clear_h, sill, kind)` derives the jamb courses (about 0.30 m each,
     faces alternating), the sill and lintel sizes and heights, and the rubble keep-out bands (`zb` / `zt` /
     `hw_*`) from the clear size.
   - `hw_window(w=)`, `inside_clear`, `_drum_openings` and `build_slit_windows` read the spec of each window
     through `win_list(g)`. The mill keeps `g.WIN` and its literal 1.17 / 2.04 / 0.31 / 0.37 numbers.
   - This tower has `window_size=(0.18, 0.95)`: three stair lights, each with 3 jamb courses and a splayed, closed
     embrasure. They rise clockwise: 2.50 m at az 45, 3.95 m at az -45, 6.10 m at az -135.
   - Slit 2 was lowered from 4.10 to 3.95 after a self-check close-up. A 9 cm strip of pinners between its lintel
     and the string-course drip became a full rubble course (`c04_slit`).
4. **Build time: `tower_roof.tower_hidden_cull`.**
   - Step 1, `drum_precull`: an analytic pre-cull that removes drum stone and mortar faces wholly behind the wall
     core, and inward faces behind the mortar skin. Faces near openings are never touched. It removed 3,954
     polygons in 0.2 s.
   - Then ONE ray pass, `drum_ray_cull`, over all 11 targets on a reduced view set: 323 views, made of eye / knee
     rings, lookout-level, eave-level and crane rings, door close-ups and the review cameras, against round 1's
     515.
   - Each polygon is tested only against the views whose sight line does not pass through the closed core shell
     (`drum_view_masks`, a chord test against the core cylinder, z 0.05 m to the cornice). The probes and the hit
     rule are `core.visibility_cull`'s. The mean is 163 of 323 views for a drum stone. There is one BVH and one
     2-worker pool.
   - `WATCH_base_stones` now takes 130 s on a moderately loaded machine (scratch run, total build 5:08), or 298 s
     with the CPU pinned at 100 % by three other builders (the deliverable run). Round 1 took 765 s.
   - The deliverable build took 9 min 21 s wall with `procs=2` while the CPU sat at 100 % (other agents' keep,
     v2 and v3 builds). The cull removed 50,037 polygons. No out-of-memory errors.

**Nice-to-haves taken**
- Batter: `r_base` 2.48 to 2.18 gives 2.1 deg (5.0 m at the foot).
- Roof pitch: 54 deg.
- `arcade=dict(n=0)` alone now means "no arcade".
- The anchor beside the door is now `repair_patch`. `plaster_patch` stays only on the plastered passage, so
  there is 1 of them.
- Window decal anchors (sill lichen and streaks, soot over the heads, head cracks) are derived from each window's
  spec.

**Stats** (`renders/variants/v1_stone_watchtower/round_02/stats.json`, all six views at 24 samples):
- **Triangles:** 1,106,412.
- **est_hidden_pct:** 11.8 %.
- **Material slots:** 8, all from the palette.
- **mask_attribute_missing:** none.
- **Objects:** 81. 56 of them are linked duplicates of 12 pooled corbel and peg meshes. The balusters are gone.
- **bbox:** 6.43 x 6.36 x 15.01 m, base centred, z from -0.005.
- **.blend:** 28.6 MB, compressed.
- **Decal anchors:** 93, gated: snap, validate, then audit with 0 failures.

**Kit changes** are in `kit/changes/v1_stone_watchtower.md`, under "Round 2":
- New functions: `window_spec`, `win_list`, `string_course`, `lookout_room`, `drum_precull`, `drum_view_masks`,
  `drum_ray_cull`, `tower_views_lite` and `tower_head_views`.
- New optional parameters and attributes on `hw_window`, `round_stone_drum`, `DrumFrame` and
  `tower_hidden_cull`. Their defaults keep the old builds.
- **Hero re-runs** (to scratch, after the last edit to an existing module):
  - tower_windmill: 1,146,243 (identical)
  - wattle_roundhut: 876,619 (identical)
  - hilltop_keep: 1,166,874 (identical)

**Renders:**
- Review set: `renders/variants/v1_stone_watchtower/round_02/`. I inspected all six views: the watch storey
  reads in hero, front, back and aerial; the door, step and actor close-up are unchanged; no leaks were seen.
- Builder close-ups: `round_02/builder_extra/c01-c05`, covering the watch storey at 30 m and at a neighbour's eye
  level, the string course, a slit, and the 45 m thumbnail.

**Known gaps**
- Interiors and lighting:
  - Only the ground floor and the four lookout rooms have an interior. There are no upper floors or stair.
  - In strong sun the lookout rooms light up in the clay renders: their back wall shows grey, not black.
- Build time and culling:
  - The build-time margin depends on machine load. It was 5:08 on a moderately loaded machine and 9:21 with the
    CPU pinned at 100 %.
  - The analytic pre-cull removes little (about 1 %), because the kit's stones are already modelled without
    backs. Most of the gain comes from the per-polygon view masks.
- Kit debt carried over from round 1:
  - `_eave_closure` is still a fork of `conical_roof.build_eave_closure`.
  - The rotor checks are still switched off by `checks=False` in the recipe.
- Openings:
  - The lookouts are unglazed open openings, with no shutters or frames.
  - A thin row of pinners remains under the string-course drip lip above slit 2 (closed, no gap).


## v1_stone_watchtower round 2 — score 8.2/10

**Graded by:** Art Director, on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only. Ground dressing was not scored (note 10).

**What was graded.** The lookout-storey build: `buildings/variants/v1_stone_watchtower/v1_stone_watchtower.blend` with its `build.log` and `decal_anchors.json` (all 20:05), and `renders/variants/v1_stone_watchtower/round_02/`. Before rendering I copied the .blend to my scratch so a concurrent rebuild could not change it. That build's recipe survives only as the `kit_params` table in `decal_anchors.json`.

The `build_v1_stone_watchtower.py` on disk was rewritten at 20:22 into a `square_cabin` recipe. It does not build the graded .blend, and the square-cabin building has not been graded (see must-fix 1).

**Reviewed:**
- the recipe on disk (the cabin version) and the lookout KIT table in `decal_anchors.json` `kit_params`;
- `build.log`, which runs drum, core, step, ceiling, parapet, roof, finish, cull and decals, 559.9 s in all;
- the kit code: `drum_frame.window_spec` / `win_list` / `hw_window(w=)`; `drum_band.string_course` / `string_course_profile`; `drum_wall.lookout_room`, the `round_stone_drum(window_size=, lookouts=, zones=string)` branch and the `wall_core_backing` lookout holes; `tower_roof.drum_precull` / `drum_view_masks` / `drum_ray_cull`;
- `kit/changes/v1_stone_watchtower.md` (round 2);
- all six review views, `stats.json` and `hidden.json`;
- all 93 anchors (types, surfaces, heights and normals listed);
- builder close-ups c01-c05.

**Director close-ups.** These are in `renders/variants/v1_stone_watchtower/round_02/director_extra/`, made with `dir_render_r02.py` using the same clay, sun and world as render_review. j11-j19 were rendered on the CPU because the shared GPU ran out of memory.
- j01-j05: the lookout storey. j01 is the az-0 surround, j02 a raking view of the az-90 reveal and jamb return, j03 a look into the az-180 room, j04 the az-270 lintel-to-cornice junction, and j05 the storey at 30 m tele.
- j06-j08: the string course. j06 is the course at a raking angle, j07 the drip from below, and j08 the course over slit 2 at az -45.
- j09, j10: the slits. j09 is slit 1 (az 45) and j10 slit 3 (az -135).
- j11-j14: the head. j11 is the parapet on the corbel table, j12 the soffit and rafter feet, j13 the eave from a crane, and j14 the collar and finial.
- j15-j17: the ground. j15 is the door step, j16 the door depth and ceiling, and j17 the back footing.
- j18, j19: the reads. j18 is a 45 m thumbnail and j19 a neighbour's eye-level view of the watch storey.

| # | axis | score | one-line reason |
|---|---|---|---|
| 1 | Silhouette and massing | 8.4 | It now reads as a watchtower. Four 0.65 x 1.00 m dark lookouts under the corbel table show in the hero, front, side, back, aerial and thumbnail views (j18). With the stair lights and the plain string course, the storeys read vertically. The crown is still a roofed rubble ring, but the client accepts this silhouette. |
| 2 | Proportion and actor scale | 8.5 | The drum is 4.96 m at the foot and 4.36 m at the top, with a 2.1 deg batter. The eave lip is at 9.34 m and the tip at 15.0 m. Pitch is 54 deg. The door is 1.05 m with a ~2.3 m crown and has its step, and the 0.18 x 0.95 m slits read at 30 m. All of this sits inside the brief and the bible beside the 1.8 m figure. The lookout room floor is flush with the sill, so the storey has a 0 m sill height. That is invisible from outside. |
| 3 | Construction logic | 8.4 | The lookouts have dressed jambs, a projecting sill with a drip and a lintel. The string course is a real weathered course with a drip. The parapet sits on dentil corbels and the cornice cap. The plate beds on the coping, and the rafters and soffit carry the eave (j11-j13). Above each lookout, the lintel carries only a strip of pinners up to the cornice (j04). |
| 4 | Seams and junctions | 8.3 | Nothing leaks. The lookout reveal meets the dark room (j02, j03), the string course meets the drum and its drip shadow line is closed (j06, j07), the slit embrasures are closed (j09, j10), and the parapet, eave, collar and footing joints all hold (j11-j17). One junction is not resolved: the window keep-out band against fixed courses. Over every lookout, a 0.15 m void between the lintel top (8.10 m) and the cornice bed (8.25 m) is filled with two rows of 4-7 cm pinners. This zipper band reads at 30 m (j04, j05, j19, c02). The same happens under the string course over slit 2 (j08). |
| 5 | Distinctness and reuse | 8.5 | It is clearly a different building from the mill and the hut. All of the new geometry is kit modules, and the old paths are unchanged (heroes re-run identical). `window_spec` gives a slit, a stair light and a lookout from one function. `string_course` is generic, and `lookout_room` is generic. Points lost: there are now three unrelated `window_spec` functions in the kit (`drum_frame`, `windows`, `wall_openings`), and `_eave_closure` is still a fork. |
| 6 | Technical compliance | 8.1 | The build itself is clean: 1,106,412 triangles, 11.8 % hidden, 8 palette slots, no missing `Mask`, 56 linked duplicates of 12 pooled meshes, and 93 gated anchors with 0 audit failures. It built in 9:21 with the CPU at 100 %, about at the 10-minute limit. But the build script on disk does not reproduce the graded .blend (art bible section 8, single source of truth). In addition, 2 `repair_patch` anchors sit on the back walls of the lookout-room blockers. |

**Overall: 8.2/10.** The lowest axis is 8.1, rounded up. This is **a pass at the 8.2 mark**, and it applies to the lookout-storey build only. Must-fix 1 must be closed before this building goes into the village set.

**Verdict.** Round 2 did what was asked, and did it as kit work. Each of the four round-1 must-fixes became a reusable, parameterised module or option:
- lookout windows through `window_spec(kind="lookout")` and `lookout_room`;
- a plain `string_course` selected through `zones=string`;
- slit size as a parameter, with the jamb courses and keep-out bands derived from it;
- a culling pipeline that roughly halves the build (765 s down to 130-298 s on the base stones).

The tower now reads as a lookout at thumbnail size, and every module junction I rendered is closed. What holds the grade at the mark is not geometry. First, the deliverable's own recipe was overwritten by the cabin version, so the .blend cannot be rebuilt from its script. Second, the window modules do not yet negotiate with the fixed courses above them, which leaves pinner zippers. Both are concrete module and process fixes. No surface detail is requested.

**Strengths**
- All of the new geometry landed in the kit as general modules, with optional parameters whose defaults keep the old builds. The mill, hut and keep re-run to identical triangle counts.
- `window_spec(clear_w, clear_h, sill, kind)` is a good kit primitive. One call derives the jamb courses, the sill and lintel sizes and the rubble keep-out bands, so slits, stair lights and lookouts of any size come from one module and can go on any drum.
- `lookout_room` is the right note-6 answer: a straight reveal plus a closed 1.5 m room at 96 triangles. It is closed and dark in j03.
- `string_course` replaces the mill's signature balustrade with a proper dressed course with a drip. The mill keeps its default.
- The recipe is a declarative KIT table of 8 kit steps, as `kit_params` shows. `arcade=dict(n=0)` alone now means "no arcade".
- The cull is a reusable pipeline: an analytic pre-cull, then per-polygon view masks against the closed core, then one ray pass. Hidden is 11.8 % and there were no out-of-memory errors.
- The anchors follow the windows, because they are derived from each window's spec: lichen on the sills, streaks under the sills, soot over the heads and cracks at the heads. Damp and moss sit at the foot and on the north faces, and moss is on the north roof.
- The builder reported honestly. The recipe overwrite, the remaining pinner strip and the build-time margin under load were all flagged rather than hidden.

**Must-fix (before the building is used, or in round 3)**
1. **Source of truth (art bible section 8; rubric axis 6): `buildings/variants/v1_stone_watchtower/build_v1_stone_watchtower.py`.**
   - **What is wrong.** Since 20:22 it is a `square_cabin` recipe. It has slits at 60 / -60 / 180, no `lookouts`, no `corbelled_parapet` and no `round_tower_roof`, so it cannot rebuild the graded .blend.
   - **What it should be.** Restore the lookout recipe from `decal_anchors.json` `kit_params` as this building's script:
     - steps: `round_stone_drum`, `drum_wall_core`, `entrance_step`, `drum_ceiling(z=3.45)`, `corbelled_parapet(height=0.95, proj=0.24)`, `round_tower_roof(pitch_deg=54, eave_out=0.72, bell_deg=15, bell_len=1.0, collar_r=0.62)`, `drum_finish`, `tower_hidden_cull(procs=2)`;
     - drum: `windows=(45, -45, -135)`, `window_z=(2.50, 3.95, 6.10)`, `window_size=(0.18, 0.95)` and `lookouts=dict(n=4, az0=0, w=0.65, h=1.00, sill=6.85)`.
   - **How to verify.** Rebuild to scratch with `WATCH_OUT` and check that it gives exactly 1,106,412 triangles.
   - **The cabin.** Give the square-cabin recipe its own building id, for example `buildings/variants/v1b_watch_cabin/` with its own render folder. Otherwise, if the producer chooses the cabin as v1's crown, rebuild, re-render all six views and submit it as round 3. It is ungraded until then.
2. **Window head and sill against fixed courses (rubric axis 4): `drum_frame.window_spec` / `drum_wall.round_stone_drum`.**
   - **What is wrong.** A window's `zt` (lintel top plus 1.5 cm) is placed without regard to the next fixed course above it. The cornice bed is at `Z_CORN0` = height - 0.45 = 8.25 m, and the string-course bed at `zones["string"][0]`. Here `zt` = 8.105 m leaves a 0.145 m void over all four lookouts, which the pin-filler packs with tiny pinners (j04, j05, j19). The same happens over slit 2 under the string course (j08).
   - **What it should be.** Make this generic in the kit. When the gap between a window's `zt` and the bed of a fixed course above it is under one minimum rubble course (0.20 m for this rubble, `hr[0]` x 2), do one of two things:
     - raise `lintel_h` so the lintel beds directly under the course (here the lintel grows from 0.24 to about 0.385 m);
     - lower the window by the shortfall.
   - **Check.** Log or assert it in `round_stone_drum` so no recipe can produce it again. Apply the same rule under the sill against a fixed course below.
3. **Decal anchors on blocker surfaces (note 11 placement; note 6 blockers): `tower_decals.round_tower_decals_gated`.**
   - **What is wrong.** `DA_repair_patch_005` (-0.06, -0.71, 7.81) and `DA_repair_patch_007` (-0.71, 0.03, 7.37) sit on the back walls of the `WATCH_lookout_rooms` blockers, 1.5 m inside the face. They cannot be seen and are not a rendered wall.
   - **What it should be.** Exclude `<PREFIX>_lookout_rooms` (and `_interior` above the door head) from the snap and validate gates, so repair and plaster patches land only on exterior stone or the plastered door passage.

**Nice-to-have**
- **Window functions.** Rename `drum_frame.window_spec` (for example to `drum_window_spec`) or unify it with `windows.window_spec` and `wall_openings.window_spec`. Three functions with one name and different signatures will trip recipe authors.
- **Lookout room floor.** Set the `lookout_room` floor about 1.1 m below the sill (bible section 7), with the room ceiling unchanged. If an upper floor is ever seen, the watch then stands at a believable floor rather than at the sill.
- **Carried kit debt.** Merge `_eave_closure` into `conical_roof.build_eave_closure` with `facing=`. Make `drum_finish` skip the rotor checks automatically when there is no rotor, instead of the recipe passing `checks=False`.
- **Build-time margin.** It was 9:21 under full load. Consider `procs=3` when the machine allows, or dropping the eave-level ring from the base-stone view set.
- **v4_mixed.** Re-run `buildings/variants/v4_mixed`. It calls `round_stone_drum` with the mill's parameters and has not been re-run since these edits.
- **Square cabin.** If the square cabin becomes a kit module, make it sit on the same `WALL_HEAD` contract as `round_tower_roof`, and size its lookouts with `window_spec(kind="lookout")`.
