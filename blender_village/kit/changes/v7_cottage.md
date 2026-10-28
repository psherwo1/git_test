# v7_cottage: kit changes (roof add-ons builder, plan step 4)

Variant: `buildings/variants/v7_cottage/build_v7_cottage.py` -- a low L-plan thatched cottage that proves the ROOF
add-ons (valley, chimney, gabled dormer). Proposed CHANGELOG version **1.19**; docstrings tag every change "kit 1.19".

---

## Round 1

Every change to an EXISTING module is a new option whose default takes the old code path, so **the hash rule is not
triggered** (no `v7r1_hash` run; see "Hash rule" below). The add-ons themselves live in ONE new module.

### NEW `components/roof_addons.py`

| function | what it is |
|---|---|
| `roof_valley(g, main, wing, name=None, width=(0.34, 0.34), crown=0.16, bury=(0.10, 0.10), dy=0.03, comb_clear=0.22, var=0.06, seed=0, taper=0.30, end_out=0.10, smooth=2, foot="crest")` | **KIT COMPONENT: the gable-to-gable valley** (L / T plans, any angle, any yaw; also a dormer roof into its host). Traces the true line where the wing's covering top meets the main roof's top (`valley_line`: up one valley, over the wing's ridge roll, down the other) and sweeps ONE soft **rolled thatch valley** along it (`_crease_roll`: buried keel, a skirt `width` out on each covering ending `bury` under it, a rounded back `crown` over the crease, +-6 % low-frequency swelling, tapered rounded ends). `foot="crest"` stops the line just past the wing's eave-roll crest (the two eave rolls cross under its end; no twisted section over the roll noses). Drops the wing's comb units within `comb_clear` of the main top. No metal gutter. -> `<P>_<name>` (M_thatch); `g.VALLEYS`. |
| `solid_clip(roof, under=True)` / `deck_clip(roof)` / `any_clip(*clips)` | the clips that make two roofs yield to each other at a valley: `linear_roof(clip=solid_clip(other), deck_clip=deck_clip(other))` -- coverings, rolls, ridge, comb and rafters are culled inside / under the other roof's solid; the decks are kept up to the line where the two DECKS cross, so the backing under the valley is closed. |
| `roofs_top_fn(roofs, tuck=0.02)` | wall `top_fn` under several roofs (an L plan): the highest deck underside over the point. |
| `top_world(roof, P)`, `top_normal(roof, P)` | the roof solid's world top / normal over plan points (warp included). |
| `GabledDormer(main, x, side=-1, d=0.55, width=1.30, pitch=50, overhang=0.22, verge=0.28, thick=0.24, step=0.08, window=None, plate_gap=0.10, soft=None, back_run=0.30, name="dormer", ...)` | the **gabled dormer** spec (sibling of `GableRoof(eyebrows=)`): its own small soft `GableRoof` (`.roof`, yaw +90 deg to the host, `DORMER_SOFT` sag / sweep / flare / wave), the front frame line `d` m in from the host wall face, the cheeks' run back into the host roof, the host clips `.clip_main()` / `.deck_clip_main()`. The window sill is raised (logged) until it clears the host thatch; raises if the dormer ridge comes within 0.15 m of the host ridge. |
| `gabled_dormer(g, D, seed=81, covering="thatch", finial=True, foot_roll=True, valley=None, walls=None, verge_roll=None)` | **KIT COMPONENT**: the dormer's walls (`timber_walls.path_timber_wall`, board_batten, rough, the kit window centred in the front), its roof (`linear_roof`, thatch, yielding to the host, comb backing, lead hat + turned finial at the front apex, optional `verge_roll` -- the rolled thatch hood), the valley into the host (`roof_valley`) and a rolled thatch **foot roll** round the cheeks and the front where the host thatch meets the boards (`_dormer_foot_roll`, the same crease sweep; front corners rounded). `g.DORMERS`. Thatch only in 1.19. |
| `chimney(g, name="chimney", center, r_base=0.62, batter_deg=2.0, top=None, roof=None, over_ridge=0.85, clip=None, cfg=None, seed=51, crown="louvre", cap=None, parts=None, louvre=None, pot=None, abut=None, shoulder=None)` | **KIT COMPONENT: the round chimney**: a battered rubble stack (`rubble_walls.round_stone_body`, the village rubble); `shoulder=dict(z, r_base, batter_deg, h)` gives a broad base, a rounded dressed-stone **weathered offset** (`<P>_<name>_weathering`) and a narrower upper stack. With `roof=` the roof is trimmed at the stack face and flaunched with the v3 / v5 junction (`roof_junction.wall_abutment(radius=<upper stack>)`: lime-mortar fillet on the true line, lead end aprons, seal-probe registration) when the roof meets part of the stack (a gable stack), or with a closed ring of flaunching (`_ring_abutment`, `junctions.ride_fillet` on a closed `_ring_trace`) when the roof surrounds it (through a slope / the ridge -- not yet proven on a build). A softly out-of-round dressed drip-course cap (`CHIMNEY_CAP`), a dark closed flue cup (`_flue_blocker`), and a round crown: `"pot"` (a round dressed-stone pot) or `"louvre"` (dressed posts under a little lead cone, `finial.lead_hat`, with the turned finial; dark smoke chamber `_louvre_blocker`). `g.CHIMNEYS`. |
| `chimney_decals(g, seed=1701)` | soot on each stack head (stone faces only) and lichen on the cap -- call it in the recipe's decals step. |

### `components/linear_roof.py` (existing module: new options only)

| option | default | what it does when on |
|---|---|---|
| `linear_roof(..., deck_clip=fn)` -> `_linear_roof_courses(deck_clip=)` | `None` = `clip(V, margin=0.10)` (old) | the deck's own cull (two roofs in a valley keep their decks up to the deck-to-deck line: closed backing). |
| `linear_roof(..., apex_ends=("lo",))` -> `_roof_edges(apex_ends=)` | `None` = every free verge (old) | the apex finial only on the listed free gables (a chimney stands at the other). |
| `linear_roof(verge_roll=...)` with ONE free verge; `_verge_roll_path(lo_free=, hi_free=)` | both `True` (old) | the rolled verge on a roof whose other end runs into another body (a cross wing, a dormer): the eave roll runs straight on to the buried end (no fillet, no rake, no apex bend there); the deck rounds only the free corners. Before 1.19 this raised; with two free verges the old calls are made with the old arguments. |

### Hash rule

Not triggered; not run. No existing default changed:
- `deck_clip=None` keeps `deck.cull = lambda V: clip(V, margin=0.10)` (same branch, same lambda) on the courses path; the plain path is untouched.
- `apex_ends=None` calls `_roof_edges` / `_apex_finials` exactly as before.
- `verge_roll` with two free verges: `kfr = {}` (the old `_verge_roll_path` arguments), both apex bends prepended / appended in the old order, `_deck_round["corners"]` the same two tuples in the same order. Only a roof with one free verge (which used to raise) takes the new branch.
- No rng draw was added or moved on any default path. The new module is only imported by v7.

### Known limitations (round 1)

- Valley: thatch only (the shingle laced / swept valley is not built; a shingle roof would need course lacing). At each re-entrant eave corner the two eave rolls cross under the valley's rounded foot; under them a small closed dark pocket remains in the corner soffit (no see-through: red twin clean).
- Valley over the wing ridge: a small shadowed notch under the roll's arch where the comb stops (comb units within 0.22 m dropped).
- Dormer: the dormer valley's skirts meet the host's cut course ends with some short ragged edges near the dormer eave ends. The dormer roof's rolled hood is large on a 1.3 m dormer (VERGE_ROLL section is the eave roll's).
- Chimney through a slope / the ridge (`_ring_abutment`): written, not proven on a build. A gable stack is the proven case.
- The rubble-wall windows (existing kit `window_spec`) let interior rays out at the sill line (40-65 mm pinch, `round_01/builder_extra/probe_interior_r01.txt`, ROOMS); not an add-on junction, every building has the same window.

## Round 2 (kit 1.19 r2): `roof_addons.py` only. It is a new module used only by v7, so the hash rule is not triggered; `linear_roof.py` is untouched this round

| change | what |
|---|---|
| `_crease_roll(sink=, n_tuck=4)` | Each end is now a **rounded tuck**: 4 rings on a quarter circle `end_out` past the end, shrinking to a point and diving `sink` under the bisector, closed by triangle fans. This replaces the flat, non-planar n-gon cap. |
| `_continuous`, `_smooth_rows` | In `roof_valley`, the skirt directions a / b stay continuous station to station; the per-station probe is only a majority vote. The normals and skirts are smoothed, so the foot section no longer twists and the arch has no folded lip. |
| `roof_valley(end_out=0.16, sink=0.06, ridge_cut=0.12, corner="auto")` | **ridge_cut**: `_cut_ridge_under_arch` bisects the wing's ridge roll and comb 0.12 m on the wing side of the arch crest, deletes the part toward the main roof and fills the cut, so the roll ends closed under the arch. **corner** ("auto" = eaves within 0.3 m of one height): `_corner_close` at each re-entrant eave corner does three things: drops rafter tails whole within 0.35 m of the other roof's plan columns; adds a closed boarded soffit slab (M_timber) between the wall faces and lips, under the lower deck; and adds a rounded thatch closing knot where the two eave rolls cross. |
| `_ring_trace` | Starts low (`z_guess = roof.z_lip`, where the battered face is widest). Round 1 started above the ridge, inside the trimmed hole, so it never hit. Gaps under 15 % are interpolated. `_ring_abutment` is now **registered for the seal probe** ("<roof> / stack ring"). |
| `DORMER_SOFT` | `ridge_seat=True`. |
| `dormer_verge_roll(hw, ...)` / `gabled_dormer(verge_roll="auto")` | The hood is scaled to the dormer: rc 0.18 hw, apex_bend 0.155 hw, bend_over 0.12 hw. A recipe dict is capped at 0.20 hw / 0.17 hw. |
| `_dormer_foot_roll(under_eave=0.16, taper=0.40, sink=0.10)` | Each end stops further under the dormer eave and tucks into the host thatch under the dormer valley's skirt. |
| `chimney(crown="pot")` | The default crown is now the round pot. `"louvre"` is opt-in, with h 0.24 by default and clamped to 0.30 m, and no finial by default (`finial=None`). |

**Proofs:**
- `buildings/variants/v7_cottage/scratch/ring_stack.py` is a FAST build: the cottage plus an r 0.52 stack through the back slope.
  - Ring flaunching: seal probe "roof / stack ring" 0 leaks in 57,961 rays.
  - `round_02/builder_extra` r01 / r02 void and i09 red: 0 red inside the attic.

## Round 3 (kit 1.19 r3)

`linear_roof.py` (existing module) gains ONE optional parameter with the old default; the rest is in the new `roof_addons.py` (used only by v7).

| change | what |
|---|---|
| `linear_roof(eave_roll=None)` -> `_linear_roof_courses(eave_roll=)` | NEW option: a dict of `GableRoof.eave_roll` keywords (radius / proud / drop / front / tail) for the "courses" thatch's eave-roll SECTION, which the verge roll / hood also sweeps. `None` calls `roof.eave_roll()` exactly as before (old behaviour, hash rule not triggered). |
| `GabledDormer(thick=0.13, step=0.05, deck_t=0.025, roll=None)` | The dormer's thatch is thinner and its roll section is scaled to it: `roll` defaults to `dict(radius=0.15 * hw, proud=0.02, drop=0.015)` and `gabled_dormer` passes it as `linear_roof(eave_roll=D.roll)`. The hood section is now about a fifth of the dormer's width (it was the host's 0.16 m roll on a 0.24 m thatch: the "pretzel"). |
| `dormer_verge_roll` docstring | Corrected: `rc` is the hood's eave-corner fillet and `apex_bend` the bend over the apex; the section comes from `GabledDormer(roll=)`. |
| `_corner_close(corner_r=0.25, cut=0.13, past=-0.05)` | The r2 ball knot is replaced by `_corner_roll`: ONE swept internal-corner roll, the eave roll's own D section (`main.roll_section()`, x 1.05) carried round the re-entrant lip corner on a 0.25 m plan fillet with 0.30 m runs along both lips, lip height and up-vector blended from one slope to the other, its ends tapered inside the straight rolls. The two straight eave rolls are cut back 0.13 m past the fillet's tangent points (`_drop_faces`), so their open ends lie inside it. The soffit slab now spans from 1.5 cm under the lower deck underside to just over the HIGHER deck top and stops 5 cm inside the lips, so the two decks' cut board ends where they cross are buried in it (no X of boards). -> `<P>_<name>_roll` replaces `<P>_<name>_knot`. |
| `roof_valley(foot_back=None, ridge_bury=0.12, ridge_bury_w=0.35)` | At a closed corner the line stops `foot_back` = 0.22 m short of the wing roll's crest (off the round nose where the section twisted), and each foot tuck runs on >= 0.26 m and sinks crown + 8 cm into the corner roll. Over the wing's ridge roll the skirts bury up to 0.12 m deeper, the wing skirt is steered onto the ridge axis and its END dives vertically (`_crease_roll(bury_dir=)`): the radial dive over the tight ridge-roll bend folded the skirt end back on itself (the two dark wedges). |
| `_crease_roll(bury=(array, array), bury_dir=(dA, dB))` | Per-station bury and an optional dive direction per skirt; defaults unchanged. |
| `_cut_ridge_under_arch` | The fill faces of the cut ridge roll / comb are oriented out of the kept part. |
| `valley_line(foot_back=0.0)` | New option, default old. |

**Hash rule:** not triggered. The only existing-module change is `linear_roof(eave_roll=None)`, whose default path is the old call; every other change is inside `roof_addons.py`, which only v7 imports.

## Round 4 (kit 1.20; producer notes 18 and 19, the client's "an oval on the rectangle" and the thatch eyebrow)

`linear_roof.py` (existing module) gains NEW optional parameters only; every default is the old code path (bit-identical; see "Hash rule" below). `roof_addons.py` (new in 1.19, used only by v7) gains two small options.

| change | what |
|---|---|
| `GableRoof(hips=None, hip_inset=None, hip_k=1.0, hip_seam=None)` | NEW: the **round hip** ("rounded hips", note 19). `hips="both"` or `("lo",)` / `("hi",)`: that end is a half-cone instead of a gable, so the eave runs round the end as a half oval in plan, oversailing the wall corners (auto inset: the corners stay 0.15 m inside the lip). Built as a **bend of the roof's own frame**: the slope coordinates run on past each hip centre by a quarter arc per slope (virtual `xa` / `xb`), and `to_world` / `to_local` / `under_z_world` fold that run round the hip centre (`_bend` / `_unbend`; the two slopes meet on the hip's nose line). So **every existing part and query follows the hip with no per-part code**: deck, courses, eave roll, ridge roll, rafters, `keep_out` / `top_depth` / `section_columns`, and the add-ons `roof_valley`, `GabledDormer`, `chimney` ring, `solid_clip` / `deck_clip`, `roofs_top_fn` (the end walls stop under the cone). `ridge_span()` returns the straight ridge (the hip centres). |
| `GableRoof(crown=0.0)` | NEW: the **soft crown**, a softly convex section: `crown x sin(pi/2 x s)`, s = 0 at the lip to 1 at the ridge roll's flank and flat over the roll, so the slope is steeper at the eave and eases into the rolled ridge without distorting the roll. A term of the existing warp field (works on gables too). |
| `_hip_warp` | The soft-line warp on a hipped roof: the sag runs over the straight ridge only (constant round each hip, so the cone's apex is one point); the wave is sampled at the folded plan point (the slopes agree on the nose line); sweep, lifts and crown as on a gable. |
| `_layered_courses` | Hips: the course irregularity (drift, lift, crown, noise) fades to 0 over 0.9 m at each nose line, so the two slopes' courses meet edge to edge with no step. Thatch eyebrows: see below. |
| `_hip_eave_roll` | Hips: ONE `thatch.d_roll` sweep round the whole oval eave (no joint at a nose). A two-hip roof is a closed oval that starts and ends at `hip_seam=(side, x)` (v7: under the cross wing). |
| `_ridge_roll` | Hips: the ridge roll runs on round each hip in the folded frame, where its section revolves into a **rounded dome over the hip apex** (the wander fades to 0 approaching each hip centre; the spars stay on the straight ridge). |
| `_hip_rafters` | Hips: rafter tails along the slopes and **radial** round each hip, each from the lip to 0.25 m inside the wall line it crosses (longer where the hip oversails the end wall), laid square to the folded surface. |
| `EYEBROW["grid"]="shingle"` + `_brow_rolls` | NEW (note 18): `eyebrow(..., grid="thatch")` lays the harbour-house eyebrow on a `"courses"` THATCH roof: the front is snapped to the thatch course grid, each continuous course is wholly lifted (from the wave's eave course up) or not (the existing warp, per course), the course under the front stops at the deck front over the bump, the lifted courses are re-spaced (`respace`), and the village eave roll (its own D section x 0.75) is swept along the wave's lip as ONE rolled arch over the window, its ends tapering and sinking into the thatch. The timber front, kit window, deck tear, framed opening and eave strip are the 1.13-1.15 eyebrow code, unchanged (`_eyebrow_fronts` is now also called by the `"courses"` path when a thatch eyebrow is present). `linear_roof` accepts eyebrows on thatch only with `grid="thatch"` (the old error otherwise). |
| `roof_addons.chimney(abut=dict(ring_fillet=dict(...)))` / `_ring_abutment(fillet=None)` | The ring flaunching's `ride_fillet` keywords (None = the 1.19 values). v7 uses `out=0.18, h_up=0.14, bury=0.05` round a stack rising through a round hip (the 1.19 fillet let 1 of 72,364 seal-probe rays through). |
| `_deck` (hips only) | A hipped deck (the backing, ~95 % hidden) is laid on a 0.6 m x 9-row grid (a gable keeps its 0.5 / 0.25 m x 13-row grid): the first final build had est_hidden 17.8 %; the chord error round the hip is <= 1 cm, inside the eave roll. |
| `_ring_abutment(fillet=dict(step_deg=))` | The ring trace / flaunching sampling (default 1 deg); v7 uses 2 deg (half the hidden flaunching triangles), seal probe 0 leaks. |
| `roof_addons.straight_span(*roofs)` | NEW context manager: while inside, each hipped roof reports its straight ridge span as `xa` / `xb` -- the recipe wraps `composite_decals` in it so the moss anchors (laid on the plain slope frame) stay off the folded hips. `composite.py` is not touched (file ownership). |

**Hash rule: not triggered.** Every existing-module change is behind a new parameter whose default keeps the old path: `HIPS is None` and `crown == 0` leave `to_world` / `to_local` / `warp_z` / `under_z_world` / `_rafters` / `_eave_rolls` / `_ridge_roll` on their old statements; `_layered_courses` runs the identical float expressions when there is no hip and no thatch eyebrow; the shingle eyebrow path is unchanged (`grid` defaults to `"shingle"`, the old exposure). No other building uses `hips`, `crown` or `grid="thatch"`.

**Recipe (not kit):** under each round hip the end wall would rise into the hip's deep oversail as a stone gablet nobody sees (most of the extra hidden triangles): the rubble stops at wall_z - 0.30 there and a rough board-and-batten HIP-END GABLET (`timber_walls.path_timber_wall`, post_plank + board_batten gable, rough) closes the attic up to the deck (W end, E end either side of the stack, wing S end).

**Known limitations (round 4):** round hips are thatch-proven only (the shingle path would lay straight shingle courses round the cone: not built or checked); the eyebrow front's window must stay under the lifted lip (`height` >= window head + ~0.2 m); `dir_world` is not folded (only the add-ons' straight-slope uses call it).

## Round 5 (kit 1.21; the round-4 seam must-fixes, local fixes only)

`linear_roof.py` gains one module constant read only on a round-hipped, seated roof; `roof_addons.py` (used only by v7) gains new options; one NEW small module `components/orient_fix.py`. No default path of any existing module changes (see "Hash rule").

| change | what |
|---|---|
| NEW `components/orient_fix.py`: `orient_open_islands(g, parts=("_stones",), min_score=0.25, face_dot=0.5)` | **KIT COMPONENT (post step, opt-in): re-orients INVERTED open-backed stone shells.** The round-4 "cull holes" at the W inside corner (d04 59,813 / x05 34,917 / d03 21,170 / d18 17,802 yellow) were mostly **not** the cull: the uncut FAST blend shows the same 35,026 in x05. `geom.finalize`'s `strict_clean` recalculates normals with bmesh's outside test, which is unreliable on open shells, and a few wall stones by the corner came out facing INTO the wall (e.g. a 292-face hero stone with only 30 faces pointing out). Each linked island is scored by its area-weighted normals along (centroid - open-boundary centroid); an island below -min_score is flipped whole, and in a mixed shell each face looking straight back at the open side is flipped on its own. v7: 7 islands + 590 faces on `walls_stones`, 116 / 186 faces on the chimney stones. |
| NEW `orient_fix.orient_closed_slabs(g, parts=("_deck",), reach=0.12)` | Same idea for thin CLOSED slabs: a face whose normal ray meets, within `reach`, a face of the same mesh looking the same way has its normal inside the slab and is flipped (v7: 20 faces on the main deck by the inside corner, 1 on the wing deck). |
| NEW `roof_addons.reentrant_views(footprint, reach=(0.35, 0.9, 1.7, 2.8, 4.0), heights=(0.9, 1.7, 2.5))` | Eye-level viewpoints in the exterior wedge of every re-entrant (concave) corner of a plan polygon (a 5 x 5 grid along the two walls x 3 heights). `composite.footprint_views` loops round the plan bounding box, so the pocket under the eave of an L's inside corner and its valley foot is seen by none of its views. |
| NEW `roof_addons.hidden_cull(g, extra_views=(), min_polys=0, procs=4)` | **KIT COMPONENT (post step):** `composite_hidden_cull(views="lean")` plus `extra_views` tested for every target (v7: `reentrant_views(FOOT)`, 150 views). `extra_views=()` is the lean cull. Lives here because `composite.py` is not this track's file; the producer may fold it into `composite_hidden_cull(extra_views=)` at the merge. |
| `roof_addons._corner_roll(blend=None)` | NEW: the internal-corner roll's end taper runs over the last `blend` m of each straight run as a smoothstep (tangent at both ends) -- a long, shallow overlap into the straight eave rolls instead of the 0.1 m step that read as a flat-faced **sleeve band**. None = the 1.19 r3 expression. |
| `roof_addons._corner_close(roll=None)` / `roof_valley(corner_opts=None)` | NEW: pass-through of `_corner_close` keywords (`corner_r`, `cut`, `past`, `roll=dict(ext=, blend=, grow=, end_f=)`). v7: `cut=0.08, past=0.02, roll=dict(ext=0.60, blend=0.42, grow=1.08, end_f=0.90)` -- the soffit fill now runs 2 cm past the lips, under the roll bodies, so the decks' cut edges at the corner are covered from below. |
| `roof_valley(ridge_cut=<negative>)` | Documented (no code change): a negative `ridge_cut` ends the wing's ridge roll that far PAST the arch's crest, buried in the main covering (a comb-less roof). v7: `-0.35`, with `ridge_bury=0.25, ridge_bury_w=0.45`. |
| `linear_roof.HIP_DOME_SEAT` + `_ridge_roll` (hipped + `ridge_seat` only) | NEW: past each hip centre the seated ridge-roll flank (a vertical drop, which revolves round the hip into a cylinder COLLAR under the dome) eases over 0.8 m into a BELL (flank foot 1.25 x further out and 5 cm deeper, the arc's lower flanks swelling half that), so the dome settles into the hip's top course. Read only when `HIPS is not None and ridge_seat`; `HIP_DOME_SEAT = {}` restores round 4. |

**Hash rule: not triggered, not run.** `orient_fix` is a new module and `reentrant_views` / `hidden_cull` are new functions that no other recipe calls; `_corner_roll(blend=None)` and `_corner_close(roll=None)` evaluate the old statements; `HIP_DOME_SEAT` is read only inside the `H is not None` (round-hip) branch of `_ridge_roll`, which only v7 reaches. `roof_addons` is imported only by v7 (and its scratch scripts).

**Recipe (not kit), round 5:** main pitch 47 -> 49 deg (into the bible's 48-52 thatch range) and crown 0.45 -> 0.55; the wing 44 -> 42 deg and crown 0.35 -> 0.12 -- the wing's ridge and its S hip dome sit ~0.6 m further under the main ridge, so nothing of the wing shows over the main ridge from the north (the round-4 "knob" in back / d01 was the wing's far S hip dome seen over the main ridge). The E hip-end gablets run 0.2 m into the stack and stand 0.16 m lower (the i06 pinhole). The stack's ring fillet is widened (`out=0.22, h_up=0.18, bury=0.06, step_deg=1.5`) for the steeper main roof (5 of 69,448 rays leaked with the round-4 fillet).

**Known limitations (round 5):** `orient_open_islands` judges a shell by its open boundary, so a stone with no open edge falls back to the radial test (fine for compact stones, not for long curved slabs -- hence the separate ray test for decks); the root cause (bmesh's recalc on open shells in `strict_clean`) is left in `geom.py` for the producer, since changing it would change every building's hash.
