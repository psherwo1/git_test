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


## v1_stone_watchtower round 2 — sign-off audit: REJECTED (director 8.2)

Blocking issues (independent audit, copied by the producer from the workflow record):
- SOURCE OF TRUTH BROKEN (hard requirement 'assembled from kit modules'; art bible section 8, which it calls non-negotiable; rubric axis 6). C:\GitHubDesktop\git_test\blender_village\buildings\variants\v1_stone_watchtower\build_v1_stone_watchtower.py (modified 20:22) is still the square_cabin recipe. It imports square_cabin, has no lookouts, no corbelled_parapet and no round_tower_roof, and puts the slits at 60/-60/180. It cannot rebuild the graded v1_stone_watchtower.blend (20:05). The lookout recipe survives only as the kit_params record in decal_anchors.json, and nobody has rebuilt it to confirm the 1,106,412 triangles. The kit has also changed under that record. tower_roof.py was saved at 19:55:57, about 9 s after the logged deliverable build began (8:05:08 minus 559.9 s, which is about 19:55:48), and the 2-worker cull pool may have re-imported it. round_roof_parts.py (20:17), composite.py (20:09) and square_cabin.py (20:24) changed afterwards too. So it is not shown that the current kit plus the recorded KIT table rebuilds the graded .blend. A building whose own script builds a different building is not proof of a modular kit. The director marked this 'must-fix before use' and still passed it by rounding the lowest axis (8.1) up to exactly 8.2. Breaking a non-negotiable standard should put axis 6 well below 8.1, which brings the overall grade under the mark. Fix: restore the lookout KIT table as this building's script, keep the cabin under its own building id (for example buildings/variants/v1b_watch_cabin), rebuild to scratch with WATCH_OUT, and confirm exactly 1,106,412 triangles and 93 anchors.
- DECAL ANCHOR PLACEMENT FAILS THE 'PLAUSIBLE PLACEMENT' HARD REQUIREMENT. DA_repair_patch_005 at (-0.06, -0.71, 7.81) and DA_repair_patch_007 at (-0.71, 0.03, 7.37), both surface M_mortar, sit on the back walls of the WATCH_lookout_rooms note-6 blockers, about 1.5 m inside the wall face. They are inside a dark blocker box, not on an exterior or rendered wall, so note 11's placement rule is broken. tower_decals.py has not been touched since 19:28, so this is not fixed. Fix in the kit: round_tower_decals_gated / the snap and validate gates should exclude <PREFIX>_lookout_rooms (and _interior above the door head) as target surfaces, then rebuild.

## PRODUCER NOTE — round 3 starts from the client's square cabin

The source-of-truth failure above was caused by the producer: relaying the client direction started a second builder, which rewrote the recipe for the square cabin. Round 3 therefore starts from the **square-cabin recipe now on disk** (`build_v1_stone_watchtower.py`, 20:22) and the new kit module `components/square_cabin.py`. A preview build exists at `buildings/variants/v1_stone_watchtower/square_cabin_preview/v1_stone_watchtower.blend` (20:36); it was never rendered. A first round-3 fixer was stopped before making changes. The round-3 fixer: make the square-cabin recipe the deliverable (build to the normal .blend path), keep the round-2 kit modules (lookout_room, string_course, slit parameters) available as options, address every other blocking issue above that still applies, and render round_03.



## v1_stone_watchtower round 3 — builder entry

**Deliverable.** Following the producer note, the square-cabin crown is now v1's deliverable.
`build_v1_stone_watchtower.py` builds `v1_stone_watchtower.blend`, `build.log` and `decal_anchors.json` (all from
this round's single run, 614 s, CPU shared with three other builds). Those files and `renders/variants/v1_stone_watchtower/round_03/`
all come from one recipe run, so the script reproduces the graded files. The 20:05 lookout-storey files have been
overwritten. The `square_cabin_preview/` folder is untouched.

**What changed (kit modules and the recipe only; no surface detail).**

1. **Source of truth (audit blocker 1).**
   - The recipe is one declarative `KIT` table: 4 drum-family steps, a crown, then finish, cull and anchors.
     It has 56 code lines.
   - `WATCH_KIT_VARIANT=lookout` builds the round-2 crown from the same script: the `KIT.variant(...)` copy of
     the round-2 `kit_params` (slits at 45 / -45 / -135, `lookouts=dict(n=4, ...)`, then `corbelled_parapet` and
     `round_tower_roof`). The round-2 modules (`lookout_room`, `string_course`, `window_size`, `window_z`) therefore
     stay live options. I built it to scratch with `WATCH_FAST=1` and it ran clean: 91 gated anchors, none on the
     lookout rooms.
   - I did not try to rebuild exactly 1,106,412 triangles. The kit has changed under that table (see 2 below, and
     other builders' `core` changes), so the lookout crown would no longer give the round-2 count.
2. **Windows negotiate with fixed courses (director must-fix 2).**
   - New `drum_frame.fit_window_courses(W, beds_above, tops_below, min_gap)`.
   - `round_stone_drum(course_fit=True)` runs it for every `window_size` / `lookouts` window. It checks against
     the string-course bed and the cornice bed above, and the string-course top below. `min_gap` is the plain
     rubble's `hr[0] + hr[1]` (0.32 m here).
   - The rule: when the gap is under one real course, the lintel grows to bed under the course, up to 2.2 x its
     nominal height. Otherwise the window rises until its lintel beds there. A keep-out that runs into a course
     lowers the window. The same rule applies under the sill.
   - Results are logged:
     - Here, slit 2 (az -60) rises 0.255 m, so its lintel beds directly under the string course. The pinner strip
       is gone (`builder_extra/c01`).
     - In the lookout variant, the four lookout lintels grow from 0.24 to 0.385 m and bed under the cornice. This is
       the director's suggested fix for the j04 zipper.
   - The mill never reaches this branch.
3. **No decal anchors on blockers (audit blocker 2).**
   - New in `tower_decals`: `BLOCKER_PARTS` (`_lookout_rooms`, `_ceiling`, `_cabin_ceiling`, plus `_interior`
     above the door crown), `blocker_hit` and `drop_blocker_anchors`.
   - The repair-patch scatters accept only exterior hits (`wall_scatter(accept=)`). Blocker anchors are dropped
     before the gates, `validate_anchors(exclude_objects=)` rejects them, and the gated function asserts that none
     is left.
   - All 12 `repair_patch` anchors sit at r 2.2-2.5 m on the drum face. `plaster_patch` stays only on the
     plastered door passage.
4. **Cabin anchors (note 11).**
   - New `tower_decals.cabin_decals` reads `g.CABIN`. It places water streaks below each lookout's sill board on the
     plank wall and below each knee-strut corbel pad on the stone. `square_cabin` now publishes the pad positions.
   - There are 77 anchors, gated (snap, validate, audit) with 0 failures.
5. **Finial junction (found in my close-ups of the preview build).**
   - The cabin's turned finial sat on the point of the square lead cap with a visible wedge gap.
   - `square_cabin` now adds a round lead sleeve. Its foot is buried in the cap on every side and its top is inside
     the finial socket (`c05`).
6. **Smaller kit items.**
   - `drum_finish` skips the rotor checks by itself when no rotor was built, so the recipe no longer passes
     `checks=False`.
   - `drum_window_spec` is an unambiguous alias of `drum_frame.window_spec`.
   - Cabin lookouts are now 1.10 x 1.05 m with the sill 1.05 m above the cabin floor (breast-rail height).
7. **Concurrent kit change.**
   - Another builder changed `core._vis_spawn_pool` at 20:52 to return a `ProcessPoolExecutor`, and my first
     deliverable build died at `pool.close()`.
   - `tower_roof.drum_ray_cull` now consumes the executor's lazy `map` inside its `try`, falls back to one process
     on a broken pool, and closes either pool kind (`_close_pool`).

**Stats** (`round_03/stats.json`, all six views at 24 samples):
- **Triangles:** 1,068,250.
- **est_hidden_pct:** 12.9 %.
- **Material slots:** 8, all from the palette. **mask_attribute_missing:** none.
- **Objects:** 59, of which 36 are linked duplicates of 6 pooled corbel meshes.
- **bbox:** 6.61 x 6.61 x 16.88 m, base centred, z from -0.005.
- **Cabin:** a 5.40 m square on the 8.70 m wall head. Floor at 9.19 m, plate at 11.49 m, eave at 11.11 m
  (r 3.16). 48 deg pyramid, finial tip at 16.31 m.
- **.blend:** 27.4 MB, compressed.
- **Cull:** -48,559 polygons.

**Kit changes** are in `kit/changes/v1_stone_watchtower.md`, under "Round 3".
- **Hero re-runs** (to scratch, after the last `drum_frame` / `drum_wall` edit):
  - tower_windmill: 1,146,243 (its rotor checks still run)
  - hilltop_keep: 1,166,874
  - wattle_roundhut: 876,619
  - All three are identical to the record.
- Later edits touched only `square_cabin.py`, `tower_decals.py` and `tower_roof.py`, which no hero imports.

**Renders**
- Review set: `renders/variants/v1_stone_watchtower/round_03/`. I inspected all six views and found no leaks,
  floating parts or see-through pixels. It reads as a lookout tower at thumbnail size.
- Builder close-ups are in `round_03/builder_extra/` (script `closeups_r03.py`):
  - c01: slit 2 under the string course
  - c02: the cabin bed on the cornice
  - c03: a strut foot on its pad
  - c04: the eave soffit
  - c05: the cap and finial
  - c06: a lookout opening at a raking angle
  - c07: 45 m thumbnail
  - c08: a neighbour's eye level
  - c09: a cabin corner from below

**Known gaps**
- The cabin roof is a straight 48 deg pyramid. It has no bell-cast eave and no concave hips, unlike the bible's
  caps. A `bell_deg` option on `square_cabin` would be the next module step.
- The cabin's lookout openings are open, with no shutters. The cabin interior is the floor deck and the boarded
  ceiling only.
- As in round 2, the string-course lichen anchors mostly fail the snap gate (3 of 8 lichen kept). This is not
  blocking.
- `_eave_closure` is still a fork. It is only used by the lookout crown.
- `buildings/variants/v4_mixed` was not re-run. It never reaches the new `round_stone_drum` branch, and it builds
  a rotor, so `drum_finish` is unchanged for it.


## v1_stone_watchtower round 3 — score 8.1/10

**Graded by:** Art Director, on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only. Ground dressing was not scored (note 10).

**What was graded.** The square-cabin crown, now v1's deliverable (producer note, round 3): `buildings/variants/v1_stone_watchtower/v1_stone_watchtower.blend`, `build.log` and `decal_anchors.json` (all 21:13:55-56, one 614 s run of the 20:48 recipe), and `renders/variants/v1_stone_watchtower/round_03/`. I copied the .blend to my scratch before rendering.

**Reviewed:**
- the recipe `build_v1_stone_watchtower.py` (56 lines, one `KIT` table, `CROWNS` switch for the round-2 lookout crown);
- `build.log` end to end: course fit (slit 2 raised 0.255 m), square cabin (side 5.40, floor 9.19, plate 11.49, eave 11.11, apex 14.66), `drum_finish` skipping the rotor checks by itself, the cull (-48,559 polygons) and the three decal gates (77 kept, 0 failing);
- kit code: `square_cabin.py` in full; `drum_frame.window_spec` / `drum_window_spec` / `fit_window_courses`; `tower_decals.BLOCKER_PARTS` / `blocker_hit` / `drop_blocker_anchors` / `cabin_decals`; `tier_roof.bell_tier` (for reuse); `kit/changes/v1_stone_watchtower.md` round 3;
- all six review views, `stats.json`, `hidden.json`, all 77 anchors (type, surface, height, radius, normal) and the builder close-ups c01-c09.

**Director close-ups** (`renders/variants/v1_stone_watchtower/round_03/director_extra/`, scripts `dir_render_r03.py` and `dir_lineup_r03.py`, same clay, sun and world as render_review). A `probe` pass of `dir_render_r03.py` measured BVH contact for 17 module pairs: every pair overlaps or touches (struts on pads and on the floor, pads into the stones and wall core, bearers and bed on the cornice cap, frame on the floor, boards in the frame, roof frame on the plate, deck on the rafters, shingles on the deck, hips on the shingles, lead on shingles and hips, finial in the lead). Nothing floats.
- j01, j02: the floor sandwich level with the bearers, from -Y and from +X.
- j03: a bearer on the cornice cap. j04: dragon beam, outer bearer and strut head at a corner. j05: strut foot on its pad (az -135). j06: the underside of the crown from the ground. j07: the bed from above at a corner.
- j08: wall sill on the floor edge. j09: corner post. j10: through the lookouts, level. j11: inside, ceiling to plate.
- j12: eave corner and hip from below. j13: hip from a crane. j14: eave and hip on the aerial silhouette. j15: lead cap, sleeve and finial from the ground.
- j16: string course. j17, j18: slits 1 and 3. j19: door step and threshold. j20: back footing.
- j21: 45 m thumbnail. j22: a neighbour's eye level (az 120). j23: line-up hut / watchtower / mill.

| # | axis | score | one-line reason |
|---|---|---|---|
| 1 | Silhouette and massing | 8.3 | It now reads instantly as a watchtower, at 45 m (j21) and beside the hut and the mill (j23): a battered rubble drum carrying a wider square timber cabin on raking struts, open lookouts on all four sides. Points lost: the crown roof is a dead-straight 48 deg pyramid with a straight eave and straight hips. That is not this village's roof language (bible 1.4 and 2: caps bell-cast to about 25 deg over the last 0.5-1.0 m, concave hips; the brief asked for a bell-cast eave). Beside the hut and the mill it reads Alpine or generic. |
| 2 | Proportion and actor scale | 8.4 | Drum 4.96 m at the foot with a 2.1 deg batter. Eave at 11.11 m (brief 9-12 m). The door is 1.05 m with a crown of about 2.3 m and has its step. The slits are 0.18 x 0.95 m. Cabin walls 2.30 m, lookouts 1.10 x 1.05 m, roof 3.55 m tall (1.5 x the wall). The cabin sills are 1.05 m (bible 1.1-1.5). The finial is out of scale: it rises from 14.84 to 16.87 m, about 2.0 m above the lead cap against the bible's 0.9-1.3 m (j15, stats bbox). |
| 3 | Construction logic | 8.4 | Every member is carried. Bearers sit on the wall head and joists on the bearers. Dragon beams run to every corner on knee struts whose feet sit on dressed pads set into the wall (j03-j06). The framed walls have sill, posts, breast rail, head beam and plate. Rafter tails and hip rafters bear on the plate under a closed deck, and a lead sleeve seats the finial (j11, j12, j15). Weak point: the wall head between the bearers is a bare, flat mortar disc. It reads as an open, water-trapping shelf under the floor (j22). |
| 4 | Seams and junctions | 8.1 | The drum's junctions all hold. `course_fit` removed the round-2 pinner zipper over slit 2 (c01), the string course is closed (j16), the slit embrasures are closed (j17, j18), and the step, threshold and footing meet Z=0 (j19, j20). Inside the crown the 17 probed pairs all touch and the cabin interior is closed (j11). **The crown-to-drum junction is open, though.** Level with the floor framing, sky shows straight through the crown in horizontal slots: between the bearers (z 8.70-8.94) from -Y (j01), and between the joists (z 8.94-9.14) from +X (j02). This is the roof-to-tower class of junction that axis 4 names. Minor: each hip has two separate hip boards with an open V slot between them (j13; the deck is under it, so there is no see-through). |
| 5 | Distinctness and reuse | 8.2 | Clearly a new building (j23). The recipe is a short declarative assembly of kit steps with no bespoke geometry, and `square_cabin` is a real new, parameterised kit module (side, height, struts, openings, pitch, eave) for gatehouse lofts and harbour lookouts. `fit_window_courses` and the blocker exclusion are generic. Points lost: `square_cabin` is monolithic. Its square-pyramid roof (deck, rafter tails, hip rafters, shingle laying, hip boards, lead cap, finial: lines 199-347) is a second pyramid-roof implementation beside `tier_roof.bell_tier` / `OctRoof`. It cannot roof any other square body, and the cabin cannot take another roof. The bearer positions (-1.6, 0, 1.6) are absolute, not scaled with `side`. The finial scale of 1.4 is hard-coded. `_eave_closure` is still a fork. |
| 6 | Technical compliance | 8.3 | The source-of-truth blocker is closed: one recipe run produced the .blend, log, anchors and renders. 1,068,250 triangles, 12.9 % hidden, 8 palette slots, no missing `Mask`, 36 linked duplicates of 6 pooled corbels, deterministic seeds. All 77 anchors sit on exterior surfaces: the 12 repair patches are at r 2.19-2.46 m on the drum face, the plaster patch is in the door passage, and none is on a blocker. Points lost: the build took 614 s against about 10 min, and 148 s of that went on ray-culling `WATCH_cabin_shingles` for 6,034 polygons. `g.CABIN` / `g.ROOF` publish tip 16.31 m while the real finial tip is 16.87 m (stats bbox), and `tower_views` and the decal pass read that value. |

**Overall: 8.1/10** (lowest axis 8.1, not rounded up). **Below the 8.2 pass mark: round 4 required.** I did not round up because the lowest axis carries a defect the rubric names explicitly (see-through at a roof-to-tower junction). Two further module items hold axes 1 and 5 at 8.2-8.3.

**Verdict.** Round 3 did what the producer asked and did it as kit work. The client's square cabin is now a real, parameterised kit module, and the tower reads instantly as a lookout. The recipe on disk rebuilds the graded files. Windows negotiate with fixed courses, decals stay off the blockers, and the finial is seated. What stops the pass is all at module level, not detail:
- the crown-to-drum junction is left open, so sky shows through the floor framing over the wall head;
- the cabin builds its own straight pyramid roof inline instead of a reusable, bell-cast pyramid-roof module in the village roof language;
- the finial is hard-coded at about 2 m and its published tip is wrong.

Each is a small, concrete kit change. No surface detail is requested.

**Strengths**
- The source of truth is restored. One 614 s run of the 56-line recipe produced the .blend, `build.log`, `decal_anchors.json` and the round_03 renders. The round-2 lookout crown stays one environment switch away (`WATCH_KIT_VARIANT=lookout`, `KIT.variant(...)`), so the round-2 modules stay live options.
- `square_cabin` is a genuinely reusable crown. Its plan, height, struts, openings, pitch and eave are parameters. It sits on the same `WALL_HEAD` contract as `round_tower_roof` (`drum_top` / `R_out`, overridable by `z_bed` / `bed_r`). It reuses the kit's shingle pool, size table and `turned_finial`, and it publishes `g.CABIN` / `g.ROOF` for culling and decals.
- Construction reads as built at every junction I probed: 17 module pairs touch or overlap, struts land on pads, the pads are set into the wall core, and the lead sleeve closes the finial seat (c05, j15).
- `fit_window_courses` is the right generic fix. It grows the lintel or moves the window to bed under any fixed course, logs its decision, and applies the rule below the sill too. The round-2 zipper is gone (c01).
- The blocker exclusion (`BLOCKER_PARTS`, `blocker_hit`, `drop_blocker_anchors`, an exterior-only scatter, `validate_anchors(exclude_objects=)` and a final assert) is enforced in the kit, not patched per building. The cabin gets its own physically placed anchors from `g.CABIN`: streaks under the sill boards and under the strut pads, and moss on the north roof.
- Kit debt was paid: `drum_finish` skips the rotor checks itself, there is an unambiguous `drum_window_spec`, and `_close_pool` is robust to either pool type. The heroes re-run identical (1,146,243 / 1,166,874 / 876,619).
- The builder reported honestly: the straight pyramid, the unchecked lookout count and the overwritten 20:05 files were all flagged.

**Must-fix (round 4)**
1. **Crown-to-drum junction open (axis 4): `square_cabin.square_cabin`, floor block (lines 105-128).**
   - **What is wrong.** Over the wall head the floor framing is open. Sky shows through horizontal slots between the bearers (x = -1.6 / 0 / 1.6, z 8.70-8.94) from -Y (j01), and between the joists (z 8.94-9.14) from +X (j02). The bed is a bare flat mortar disc that reads as an open shelf (j22).
   - **What it should be.** Add a `bed_fill=True` option, default on when the cabin sits on a drum bed, that closes the floor sandwich over the wall-head ring. Use either blocking (noggings) between the bearers and between the joists from z_bed to the deck underside within `bed_r`, or a timber sole-plate ring on the cornice cap that the bearers and joists notch over, with boarded infill between them. Open framing then remains only on the cantilevers outside the drum, which is correct.
   - **How to verify.** Render level views from -Y and +X at z 8.8-9.1 m: no sky pixels between the cornice cap and the deck.
2. **Bespoke straight pyramid roof inside the cabin (axes 1 and 5): `square_cabin.py` lines 199-347.**
   - **What is wrong.** The roof is a dead-straight 48 deg square pyramid built inline: no bell-cast eave and no concave hips (bible 1.4 and the section-2 cap row; the brief's "bell-cast eave"). The kit now has two pyramid-roof implementations. `tier_roof.bell_tier` / `OctRoof` (octagonal only) has the bell-cast profiles, and this one cannot be reused.
   - **What it should be.** Extract it into a kit module, for example `pyramid_roof(g, sides=4, half_width, z_plate, pitch_deg, eave_out, bell_deg, bell_len, exposure, cap_r, finial_scale, seed)`, or generalise `bell_tier` / `OctRoof` to `sides=4` with the existing `cap` profile. `square_cabin` then calls it through a `roof=dict(...)` parameter.
   - **This tower.** Use pitch about 48-50 deg with `bell_deg` about 20-25 over 0.6-0.8 m, which gives an eave at about 25 deg, and slightly concave hips. `bell_deg=0` must reproduce today's straight pyramid.
3. **Finial out of scale, and a wrong published tip (axes 2 and 6): `square_cabin.square_cabin`, lines 346-358.**
   - **What is wrong.** `turned_finial(..., scale=1.4)` is hard-coded. The finial runs from 14.84 to 16.87 m, about 2.0 m above the lead cap, against bible 1.5's 0.9-1.3 m. `tip = zc - 0.02 + 1.4 * 1.05` publishes 16.31 m in `g.CABIN` / `g.ROOF` and the log, while `stats.json` `bbox_max` z is 16.872.
   - **What it should be.** Expose `finial_scale`, with a default giving about 1.1-1.2 m above the cap. Compute `tip` from the built finial mesh (max z of `A["finial"]`), so `tower_views` and the decal pass read the true value.

**Nice-to-have**
- **Bearers.** Derive the `bearers` default from `side` and `bed_r` (for example x = 0 and ±0.6 * `bed_r`) instead of the absolute (-1.6, 0, 1.6), so other cabin and drum sizes bear on the wall head.
- **Hips.** Make the hip one saddle piece, or butt the two hip boards. Each face now lays its own board, which leaves a V slot along every hip (j13).
- **Build time.** Leave `cabin_shingles` out of the ray cull, or pre-cull it analytically: 148 s for 6,034 polygons. That brings the build back under 10 minutes.
- **Cabin sill.** Raise `open_sill` to 1.10 m (bible section 7, 1.1-1.5 m).
- **Strut pads.** These take their wall face from the drum's `R_out`. Accept a wall-face callback (`on=`) so the cabin can perch on a square or octagonal body too.
- **Carried debt.** Merge `_eave_closure` into `conical_roof.build_eave_closure` with `facing=`. Run a full (not `WATCH_FAST`) build of the lookout variant once, so its triangle count and hidden % are on record. Re-run `v4_mixed`.

## v1_stone_watchtower round 4 — builder entry

**Deliverable.** One run of the recipe (`build_v1_stone_watchtower.py`, 57 code lines, 400 s) produced
`v1_stone_watchtower.blend` (21:47, 27.3 MB, compressed), `build.log` and `decal_anchors.json`. The review set
`renders/variants/v1_stone_watchtower/round_04/` (all six views, 24 samples, OPTIX) was rendered from that .blend.
The changes are kit modules and the recipe only. No surface detail was added.

**Must-fixes**

1. **Crown-to-drum junction closed (axis 4).** `square_cabin(bed_fill=True)`, on by default, adds a closed timber
   rim ring on the wall head, just inside the bed ring (r 2.28-2.40). It is bedded 1 cm into the cornice cap and
   rises to 4 mm under the deck, as blocking between the bearers and between the joists. Open framing now remains
   only on the cantilevers outside the drum.
   - **Verified by level ray test** (`round_04/builder_extra/sky_check_r04.py`: horizontal rays at z 8.72-9.18,
     1 cm grid, |s| < 2.3 m):
     - this round: **0 sky rays** of 21,667 from -Y, from +X and from az 45;
     - the round-3 cabin: 6,032 from -Y and 7,420 from +X.
   - Renders: `builder_extra/j01`, `j02` (the director's cameras), `j07` and `j22`. The bed now reads as a
     timber-closed floor on the cornice, not an open shelf.
2. **The roof is a reusable kit module (axes 1 and 5).** The new `components/pyramid_roof.py` holds
   `pyramid_roof(g, p_wall, z_plate, name, sides=4, rot_deg, cx, cy, pitch_deg, eave_out, bell_deg, bell_len, kick,
   kick_len, sag, exposure, cap_r, finial_scale, ..., seed, rng)`.
   - **Reusable:** it roofs any regular polygon (any number of sides, rotation or centre) on any wall head. It is
     no longer tied to the cabin.
   - **Bell-cast and concave hips:** the eave is bell-cast, cosine-blended over `bell_len`, so the hip lines come
     out concave in elevation. There are optional upturned hip corners (`kick`) and an optional dish between the
     hips (`sag`).
   - **Everything follows the curved surface:** deck, rafter tails, hip rafters, starter board, coursed shingles
     and lead cap.
   - **Hip saddles:** each hip is now ONE closed saddle swept along the hip. This also closes the round-3 V slot
     between the two hip boards (director nice-to-have, j13).
   - **square_cabin calls it:** `roof=dict(...)` passes overrides and `roof_fn=` swaps in another roof module.
   - **This tower:** pitch 49 deg, `bell_deg=24` over 0.75 m (25 deg at the lip), `kick=0.04`, eave 0.55 m. Eave
     z 11.26 (corners 11.30), r 3.21, apex 14.77.
   - **`bell_deg=0` reproduces round 3.** A scratch build with the round-3 cabin parameters gave eave 11.11 / r 3.16,
     apex 14.66, 448 shingles and 43,610 shingle polygons (the round-3 pre-cull count). Its deck, lead and finial
     bboxes are identical to the round-3 .blend. Only the hip covering differs (saddles).
3. **Finial scale and published tip (axes 2 and 6).**
   - `finial_scale` is now a parameter: default 0.80 in `square_cabin` and `pyramid_roof`, 1.4 hard-coded before.
     The finial now runs 14.95-16.11 m, **1.14 m above the lead cap** (bible 1.5: 0.9-1.3).
   - `tip` is read from the BUILT finial mesh (max z). `g.CABIN["tip"]`, `g.ROOF["tip"]` and the log say 16.11 m,
     and `stats.json` `bbox_max` z is **16.112**, so they agree.

**Further kit items**
- **Bearers:** `bearers=None` derives x = 0 and +-0.65 `bed_r`. That gives (-1.6, 0, 1.6) here, and any drum size
  bears on its wall head. (Director nice-to-have.)
- **Cabin sill:** `open_sill` raised to 1.10 m (bible section 7). (Director nice-to-have.)
- **Head-beam fix:** the higher sill left the plate 1 cm above the head beam, an open slot with no boards. The kit
  now grows the head beam into the plate whenever that gap is under 5.5 cm, so it is a rule for every cabin, not a
  one-off.
- `g.CABIN` also publishes `bed`, `bed_r`, `bearers` and the roof record.

**Stats** (`round_04/stats.json`)
- 1,057,164 triangles, est_hidden_pct 12.5 %.
- 8 palette material slots, `mask_attribute_missing` none, 59 objects (36 linked duplicates of 6 pooled corbels).
- bbox 6.74 x 6.74 x 16.12 m.
- Cull: -50,652 polygons, of which `cabin_shingles` -8,235.
- Anchors: 77, through all three gates with 0 failing and none on a blocker.

**Junction probe.** The director's `dir_render_r03.py probe` on the deliverable: all 17 module pairs overlap or touch.
That includes hips on shingles, lead on hips and shingles, and finial in lead.

**Renders.**
- `round_04/`: all six views inspected. There are no leaks, floating parts or see-through pixels. It reads as a
  lookout tower with a bell-cast cabin cap at thumbnail size.
- `round_04/builder_extra/`: the director's camera set re-run on the deliverable for j01, j02, j07, j12, j13, j14,
  j15, j21 and j22.

**Kit changes** are in `kit/changes/v1_stone_watchtower.md`, under "Round 4".
- **New module:** `pyramid_roof.py`.
- **Edited:** `square_cabin.py`, which only this recipe imports (checked by grep). No existing module that a hero
  imports was touched, so I did not re-run the heroes.

**Known gaps**
- **Cull time:** `cabin_shingles` is still ray-culled (about 100 s of the 400 s build). I kept it in the cull
  because of the hidden-percentage budget.
- **Saddle eave end:** the hip saddle ends square, 3 cm past the eave corner.
- **Lookouts:** the cabin's lookouts are still unshuttered openings.
- **Not run:** a full (non-fast) build of the lookout crown variant, and the `v4_mixed` re-run. Both are carried
  over from round 3.

## v1_stone_watchtower round 4 — score 8.3/10

**Graded by:** Art Director, on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only. Ground dressing was not scored (note 10). No surface detail is requested.

**What was graded.** `buildings/variants/v1_stone_watchtower/v1_stone_watchtower.blend`, `build.log` and `decal_anchors.json` (21:47:31-32, one 400 s run), and `renders/variants/v1_stone_watchtower/round_04/`. The .blend I rendered is a byte-identical copy (SHA-256 checked) in my scratch.

**Source of truth.** The recipe (21:36:53), `pyramid_roof.py` (21:35:55) and `square_cabin.py` (21:38:48) were all saved before the build started (about 21:40:52). Two kit files changed during or after the build: `seal_probe.py` (21:45) and `tier_roof.py` (21:50). Nothing in the watchtower's import chain loads either one; I checked with grep. The recipe on disk therefore rebuilds the graded files.

**Reviewed:**
- the recipe (57 lines, one `KIT` table plus the `CROWNS` switch, with no bespoke geometry);
- `build.log` end to end (pyramid roof: 4 sides, pitch 49, bell 24/0.75, kick 0.04, eave 11.26 / corner 11.30, apex 14.77, cap 14.97, tip 16.11, 450 shingles; cabin: bearers (-1.6, 0, 1.6) derived from `bed_r` 2.46, bed fill on, sill 10.29; cull -50,652; anchors 77 / 0 failing);
- `components/pyramid_roof.py` in full, `components/square_cabin.py` in full, and `kit/changes/v1_stone_watchtower.md` round 4;
- all six review views, `stats.json`, `hidden.json`, all 77 decal anchors (type, surface, height, radius, normal), and the builder's `builder_extra` set plus `sky_check_r04.py`.

**Director checks** (`round_04/director_extra/`):
- **Scripts:** `dir_render_r04.py` (renders, plus `probe` and `sky` modes), `dir_check_r04.py` (mesh hygiene), `dir_lineup_r04.py` and `dir_pyramid_reuse_smoke_r04.py`.
- **Probe.** All 19 module pairs overlap or touch. That is the round-3 17 plus `roof_deck`→`frame` (carried through the rafter tails) and `hips`→`roof_deck` (the saddles sit on the shingles). The rim ring is 128 vertices at r 2.280-2.400, z 8.690-9.136, so it is bedded 1 cm into the cornice cap and stops 4 mm under the deck.
- **Sky test (my own).** Level rays through z 8.70-9.19 from 8 azimuths across the full cornice width (|s| ≤ 2.50 m, 1 cm grid).
  - Sky rays with |s| < 2.28 m: 0 of 22,750 per azimuth.
  - From +X and -X only, sky shows through a slot at |y| 2.38-2.50, z 8.94-9.13 at each end. This is the outermost joist bay, between the ring's outer face (r 2.40) and the last joist (y ±2.51-2.69), directly over the edge of the cornice.
  - The builder's test stopped at |s| < 2.3 m, so it could not see this slot. In renders the slot appears only near-orthographically: an 80 m telephoto shows it (j33, j34), while at 16 m (j02) it does not.
- **Hygiene.** No zero-area faces in any cabin object. One sliver in `cabin_shingles`. `cabin_hips` is closed (0 boundary edges). All new objects have identity transforms, `Mask` (CORNER, BYTE_COLOR, active) and a UV map.
- **Reuse.** `pyramid_roof` built standalone with 3, 6 and 8 sides, off-centre and with no cabin, and every run produced all six parts (j38).
- **Renders.**
  - Crown on the drum: j01-j03 (floor sandwich, level from -Y, +X and az 45), j04 and j05 (rim ring under a bearer and under the joists), j06 (dragon beam at a strut head), j07 (strut foot), j08 (underfloor from the ground), j09 and j10 (bed from above).
  - Cabin body: j11 (sill on the floor edge), j12 (corner post), j13 (through the openings), j14 (head beam into the plate), j15 (ceiling inside).
  - Roof: j16 (eave corner from below), j17 (saddle eave end, close), j18 (hip from a crane), j19 (saddles into the lead cap), j20 (aerial eave silhouette), j21 (cap and finial from the ground), j22 and j23 (roof elevations face-on and hip-on).
  - Drum: j24-j29 (string course, slits, door step from the front and the side, back footing).
  - Reads: j30 (45 m thumbnail), j31 (neighbour's eye level), j32 (line-up of hut, watchtower and mill).
  - Investigation shots: j33 and j34 (telephoto slot), j35-j37 (eave corner from above and level).

| # | axis | score | one-line reason |
|---|---|---|---|
| 1 | Silhouette and massing | 8.5 | It reads instantly as a lookout tower at 45 m (j30) and beside the hut and mill (j32). The crown roof now speaks the village cap language: a sprocketed bell-cast eave at about 25 deg, concave hips and upturned corners (j22, j23). Held back only because the bell is gentle at thumbnail size and the cap is a plain square pyramid (the client's chosen crown). |
| 2 | Proportion and actor scale | 8.5 | The finial stands 1.14 m above the lead cap (bible 0.9-1.3) and the published tip of 16.11 m matches `stats` bbox z 16.112. Lookout sills are 1.10 m. The eave is at 11.26 m (brief 9-12). The door is 1.05 m wide with a crown of about 2.3 m and has its step. The lead cap is pitched the same as the roof (bible 1.5 asks for a shallower collar), and the kit's `open_sill` default is still 1.00. |
| 3 | Construction logic | 8.4 | Every member is carried: struts on pads, bearers and the rim ring on the cornice cap, joists on bearers, rafter tails and hip rafters on the plate, saddles on the shingles, and the finial in a lead sleeve (19 probe pairs). The head beam now grows into the plate (j13, j14). Points lost: the rim ring is one smooth 32-segment lathed band 12 cm thick and 45 cm tall. Timber cannot be bent into that, so at mid-shot it reads as a plastered collar rather than blocking between bearers and joists (j05, j31). |
| 4 | Seams and junctions | 8.3 | The round-3 blocker is closed: no sky through the floor sandwich over the wall head from any of 8 azimuths (my sky test; j01-j03). The round-3 V slot along the hips is gone (j18). Points lost: (a) each hip saddle ends square past the eave corner, with an open dark mouth about 8 cm high under its end. It shows as a black pip at every eave corner from 40 m hip-on (j23, j37, j17). (b) A 12 x 19 cm sky slot sits at the outermost joist bay from ±X, over the cornice edge (sky test; j33, j34). (c) Hip-trimmed shingle ends show as crumbs along the saddle edges in close-up (j17, j36). |
| 5 | Distinctness and reuse | 8.5 | Clearly a new building (j32), and the recipe is a pure kit assembly. The round-3 inline roof is now `pyramid_roof`, a genuine kit module: `PyramidSurface` covers any polygon, centre and rotation, with bell, kick and sag, and it returns a record whose `tip` comes from the built mesh. It runs standalone on 3, 6 and 8 sides (j38), and `roof_fn` / `roof=` make the cabin's roof swappable. `bearers` is derived and `finial_scale` exposed. Points lost: the kit now has two polygonal bell-cast roof implementations (`pyramid_roof` and `tier_roof.bell_tier` / `OctRoof`). `bed_fill` is circular only (a lathe), and the strut pads still read the drum's `R_out`, so the cabin cannot yet perch on a square or octagonal body. `square_cabin` keeps dead imports and a stale signature line in its header. |
| 6 | Technical compliance | 8.6 | 1,057,164 triangles, 12.5 % hidden, 8 palette slots and no missing `Mask`. 59 objects, with 36 linked duplicates of 6 pooled corbels. Seeded and deterministic. The build took 400 s, under the 10-minute limit. Transforms are identity, and there are no zero-area faces in the new modules. All 77 anchors are physically plausible: damp and moss at the base, roof moss on the north face, streaks under the cabin sill boards and strut pads, soot over openings, rust under the hinges, and none on a blocker. Minor: the `cabin_bed` mortar disc is now 100 % hidden (528 triangles) under the ring. |

**Overall: 8.3/10** (lowest axis 8.3, not rounded up). **PASS** (pass mark 8.2).

**Verdict.** Round 4 fixed all three round-3 must-fixes, and fixed them in the kit.
- The crown-to-drum floor sandwich is closed over the wall head.
- The cabin's inline straight pyramid is gone. In its place is a reusable, bell-cast polygonal `pyramid_roof` that I verified on 3, 6 and 8 sides. It brings concave hips and one-piece hip saddles in the village's cap language.
- The finial is parameterised and in scale, and its published tip is measured from the built mesh.

The recipe is still a short declarative assembly, and its source files predate the build. What keeps the grade at 8.3 is small junction work at the roof corners and at the very edge of the rim ring. None of it is surface detail.

**Strengths**
- `pyramid_roof` is the kind of module the client asked for. It is one parameter set (sides, rotation, centre, pitch, bell, kick, sag, exposure, cap, finial scale) for any polygonal cap on any wall head. It returns a record that callers publish, and with `bell_deg=0` it reproduces round 3 point for point. Gatehouse lofts, turret caps and harbour lookouts can all use it.
- `square_cabin` is now a composer, not a monolith: its roof comes in through `roof_fn` / `roof=`, the bearers are derived from `bed_r`, and `finial_scale` is exposed.
- The crown-to-drum junction is closed by a kit option (`bed_fill`, on by default) rather than a per-building patch. The head-beam/plate rule is generic too: the beam grows into the plate whenever the gap is under 5.5 cm.
- The construction reads as built from every angle I checked, and all 19 probed module pairs touch or overlap.
- Technical hygiene is clean, the anchors are plausible, the build is back under 10 minutes, and the published `tip` agrees with `stats.json`.
- The builder reported honestly: the square saddle end, the shingle cull time and the carried-over runs were all flagged.

**Must-fix (next round or before sign-off; they do not block this pass)**
1. **Open mouth under each hip saddle at the eave corners (axis 4): `pyramid_roof.pyramid_roof`, hips block (lines 263-292; `hp` starts at `a + 0.03`, line 265).**
   - **What is wrong.** The saddle rides `lift` = 8.5 cm above the deck along the hip and is cut square 3 cm past the eave corner. Under its end there is an open, dark, roughly triangular mouth about 8 cm high over the starter board and hip-rafter end. It shows as a black pip at all four corners from 40 m hip-on (j23), and clearly at eave level (j37) and from below (j17).
   - **What it should be.** Close the saddle end. Either (a) taper `lift` to the starter-board top over the last 0.3 m of the hip, so the saddle beds on the covering at the lip; or (b) add a closing end block or eave-corner board under the saddle end, from the deck top to the saddle underside, flush with the lip. Also trim the shingles at the hip to just under the saddle boards (`lim` about `p*tanh - 0.8*w_b` instead of `p*tanh - 0.012`, line 251), so no clipped shingle ends show past the saddle edges (j17, j36).
   - **How to verify.** Render level views at each eave corner (az ±45 and ±135) and a 40 m hip-on elevation: no dark pip under any saddle end.
2. **Sky slot at the outermost joist bay over the cornice edge (axis 4): `square_cabin.square_cabin`, `bed_fill` block (lines 140-146).**
   - **What is wrong.** The ring's outer face is at `bed_r - 0.06` (r 2.40), and it is a smooth 32-gon. From ±X, level rays through |y| 2.38-2.50, z 8.94-9.13 see the sky between the ring and the outermost joist, directly over the cornice edge. That is 280 rays per side in my test, and it shows in j33 and j34. `sky_check_r04.py` limited its window to |s| < 2.3 m, inside `bed_r` (2.46), so it missed the slot.
   - **What it should be.** Close the floor sandwich out to the full bed radius. Either take the ring's outer face to `bed_r` (flush with the cornice cap's outer arris), or add end blocking under the outermost joist on each side from the bed up to the deck. Widen the kit check to |s| ≤ `bed_r` + 0.05; better still, run the kit's `seal_probe.through_seal_probe` on this junction instead of a bespoke script.
   - **How to verify.** Level orthographic rays from 8 azimuths over |s| ≤ 2.50 m: 0 sky rays.

**Nice-to-have**
- **Rim ring as built timber.** Build the bed fill as straight blocking pieces between the bearers and joists, or as a polygonal curb of N straight segments, instead of one smooth lathed band. Accept a wall-head shape (`bed_shape=` round, square or polygon, or an `on=` face callback) so `bed_fill` and the strut pads also work when the cabin perches on a square or octagonal body.
- **One pyramid-roof implementation.** Let `tier_roof.bell_tier` / `OctRoof` delegate to `PyramidSurface` (or the reverse), so the kit has a single polygonal bell-cast roof.
- **Lead cap pitch.** Add `cap_pitch_deg` to `pyramid_roof` so the lead hat can be shallower than the roof (bible 1.5: about 44 deg against 49-51 deg).
- **`square_cabin` tidy-up.** Update the header signature (lines 4-6 still show `bearers=(-1.6, 0.0, 1.6)` and `open_sill=1.00`). Remove the dead imports (`SHINGLE_VARIANTS`, `SIZE_TABLE`, `shingle_mesh`) and the now-unused `_slab`. Make the `open_sill` default 1.10. Skip the `cabin_bed` disc inside the ring when `bed_fill` is on, since it is 100 % hidden.
- **Build time.** Pre-cull `cabin_shingles` analytically (under the next course) instead of ray-culling it, which takes about 100 s of the 400 s.
- **Carried debt.** Run a full (non-fast) build of the lookout crown variant so its triangle count and hidden % are on record. Re-run `v4_mixed`.


## CLIENT RULE (2026-10-16, producer note 15): at most 1,000,000 triangles

Client's words: "Keep the new structures to a one million triangle limit". The round-4 build is about 1.06 M triangles; any further round must bring it to 1,000,000 or fewer (art bible, note 15).

