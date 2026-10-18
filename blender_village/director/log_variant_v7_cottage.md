# v7_cottage: a low L-plan cottage proving the ROOF add-ons (plan step 4)

## CLIENT DIRECTION (2026-10-17, session 2)

- Plan step 4 (client "Yes proceed"): the add-ons: **lean-to, porch, chimney, dormer and gable-to-gable valley**. The client said: "Move forward with the quick fix, the housekeeping, and the add ons. Make sure the add ons stick with the theme of the village".
- **This track builds the ROOF add-ons** and proves them on a new low design: the **gable-to-gable valley** (L and T plans), a **chimney / smoke louvre** through any roof, and a **gabled dormer** (a sibling of the existing eyebrow option).
- The other track (log_addons_lean_porch.md) builds the lean-to and the porch at the same time.
- Team method: builder, Art Director (modularity rubric, pass 8.2), independent audit, **at most 3 rounds**. Time matters.

**Village theme (client: "Make sure the add ons stick with the theme of the village"; producer notes 16 and 17 are binding):**
- **Same builders, techniques and materials** as the village (note 16): the shared palette only, the village rubble and lime mortar, rough old timber, the village shingle and thatch courses, iron straps and pintles, and lead flashing dressed like the harbour house's and the longhouse's. Re-use the kit's existing detail modules for these.
- **Round structures and soft, organic lines** (note 17), as in `reference/ref4_harbour_boathouse_concept.jpg`:
  - swept or bell-cast eaves and gently sagging ridges (the `GableRoof` soft options);
  - rolled verges and eaves;
  - curved braces and brackets (the `cruck` family's curves);
  - battered, softened stone;
  - round elements where they fit, for example a round chimney pot or a round smoke louvre under a little cone.
  
  Nothing ruler-straight or generic.
- **Every add-on is a reusable kit module** with old-behaviour defaults: a short call in any recipe attaches it to any wall or roof of any design. Its junctions are closed, flashed or covered, with no see-through and no light leaks: they become visible beams in fog (`director/performance_assessment.md`).
- Low and working, not more towers: the vignette showed the village already has many conical turrets.

## Brief

A low village cottage on an **L plan**, built from rubble (lower walls or full walls) with rough timber where it suits.
- **Size:** main wing about 10 x 5.5 m, cross wing about 6 x 5 m; storey and a half at most.
- **Roofs:** two soft GableRoofs meeting in a **valley**, in thatch or village shingle (builder's choice; the director checks variety against v3 / v5 / v6).
- **One chimney or smoke louvre** through a slope or at a gable, with its round element.
- **One gabled dormer** on a slope.
- **A door, small windows, a doorstep.**
- **No tower and no conical turret.** The round elements are the chimney / louvre and the soft lines.

**The new kit add-ons:**
1. **oof_junction.valley** (or a GableRoof / linear_roof option): two linear roofs meeting at any angle (L, T), with a swept, soft valley.
   - Shingle: laced or swept valley courses.
   - Thatch: a rolled valley.
   - No hard straight metal gutter; a lead soaker under it is fine.
2. **chimney:** a rubble stack, slightly battered and softened, through any roof slope or ridge, or against a gable.
   - Mortar flaunching / lead apron and back gutter, by reusing wall_abutment / the lead pieces.
   - A round pot, or a round smoke louvre with a little cone.
3. **dormer:** a gabled dormer on any GableRoof slope, with swept cheeks and curved bargeboards, and the kit window.
   - It is sealed to the main slope.
   - It is reusable alongside GableRoof(eyebrows=).

**File ownership while both tracks run:** this track may edit linear_roof.py, oof_junction.py and its own new modules. The other track will not edit those two files.
## PRODUCER NOTE (2026-10-17, session 2, 23:12): early-preview feedback, apply in round 1 (the village theme)

From `round_01/preview/` (the first FAST build):
1. **Keep:** the L-plan, the soft thatch valley and the gabled dormer with its rolled thatch hood. All on theme.
2. **The chimney reads as a miniature lighthouse:** a tall, thin round shaft standing far above the ridge, with a cupola. The village must not gain more towers.
   - Make it a **short, chunky village chimney**: a battered rubble stack, broad at the base (it can be an external stack against the gable, as now), rising only about **0.8-1.2 m above the ridge**.
   - Give it softened shoulders (weathered offsets where it narrows).
   - Top it with a **round element of modest size**: a round clay / stone pot or a low smoke louvre under a little cone, at most about 0.6 m tall, with no lantern / cupola read.
   - Flash it into the roof properly.
3. **The thatch gable verges are saw-toothed** (stepped course ends against the sky, most visible on the cross wing). Use the kit's **`linear_roof(verge_roll=True)`** with the apex bend (from the barn, kit 1.12.0) on every thatch gable, so each rake is one soft rolled edge.
## v7_cottage round 1 — builder entry

**What was built.** `buildings/variants/v7_cottage/build_v7_cottage.py` -> `v7_cottage.blend` + `decal_anchors.json` (prefix COTT, PlanFrame, recentred by (-0.418, +2.587)). A low L-plan rubble cottage: main house 10.0 x 5.5 m (walls 2.85 m, 52 deg soft thatch), a cross wing 4.8 x 5.25 m projecting from the front (47 deg soft thatch) meeting the main slope in a rolled thatch valley each side, a gabled dormer over the plank door, and a round rubble chimney against the east gable. Every thatch gable has the barn's rolled verge with the apex bend (now on one-free-verge roofs too). Turned finials on lead hats at the west main gable, the wing gable and the dormer. The producer note of 23:12 is applied: the chimney is now a broad battered base (r 1.05 m) with a rounded dressed-stone weathered shoulder at 4.7 m, a narrower stack (r 0.60 -> 0.52) whose head is about 0.8 m over the ridge, and a 0.46 m round dressed-stone pot. There is no louvre cupola. The louvre option stays in the module, built lower. Verge rolls are on all three roofs.

**The add-ons (all in the NEW module `kit/village_kit/components/roof_addons.py`, kit 1.19; full table in `kit/changes/v7_cottage.md`):**
1. **Valley**: `roof_valley(g, main, wing, width=(0.34, 0.34), crown=0.16, bury=(0.10, 0.10), comb_clear=0.22, foot="crest", seed)`.
   - Build both roofs first with `linear_roof(clip=solid_clip(other), deck_clip=deck_clip(other))`.
   - It traces the true top-to-top line: up one valley, over the wing's ridge roll, down the other.
   - It sweeps one soft rolled thatch valley along that line (no metal gutter) and drops the wing comb near the main slope.
   - It works at any angle or yaw, for L or T plans, and for a dormer into its host.
2. **Chimney**: `chimney(g, name, center, r_base, batter_deg, top=None, roof=None, over_ridge, clip, crown="pot"|"louvre", shoulder=dict(z, r_base, batter_deg, h), pot=, louvre=, cap=, abut=)`.
   - The stack is round battered village rubble (`round_stone_body`).
   - It is flashed with the v3 / v5 `wall_abutment`: a lime-mortar fillet and lead aprons, registered with the seal probe.
   - When the roof surrounds the stack (through a slope or the ridge), a closed ring of flaunching is used instead.
   - The cap is a dressed drip course, with a dark flue cup and a round pot or a low louvre under a lead cone.
   - `chimney_decals(g)` adds soot and lichen anchors.
3. **Gabled dormer**: `GabledDormer(main, x, side, d, width, pitch, overhang, verge, thick, step, window=dict(width, height, sill, ...), soft=DORMER_SOFT)` + `gabled_dormer(g, D, seed, verge_roll=dict(...), valley=, walls=)`.
   - It builds a rough board-and-batten front and cheeks (`path_timber_wall`) with the kit window, raising the sill until it clears the thatch.
   - Its own soft thatch roof carries a lead hat and turned finial, plus the rolled hood (`verge_roll`).
   - It adds the valley into the host and a rolled thatch foot round the cheeks and front.
   - Host clips: `D.clip_main()`, `D.deck_clip_main()`.
   - It is reusable next to `GableRoof(eyebrows=)` (shingle eyebrow) and is thatch only for now.

**Existing-module changes** (`linear_roof.py` only; all defaults = old): `linear_roof(deck_clip=None, apex_ends=None)`; `verge_roll` now also accepts a roof with ONE free verge (`_verge_roll_path(lo_free=, hi_free=)`; it used to raise).

**Reuse table**

| piece | kit module(s) reused |
|---|---|
| walls | `rubble_walls.path_stone_wall` (RUBBLE_LARGE, one path round the L), `openings.door / window`, `roof_addons.roofs_top_fn` |
| roofs | `linear_roof` thatch "courses" + `GableRoof` soft options (ridge sag, eave sag / sweep, verge flare, wave, ridge_seat) + `verge_roll` apex bend + `comb_step / comb_backing` (barn) + `apex_finial="turned"` |
| valley | `GableRoof.keep_out / section_columns / ref_z`, `composite.drop_units`; the crease sweep follows `cone_abutment`'s loop language |
| dormer | `timber_walls.path_timber_wall` (board_batten, rough), `roof_top_fn`, the kit window, `linear_roof`, `roof_valley` |
| chimney | `rubble_walls.round_stone_body`, `roof_junction.wall_abutment` (`junctions.clip_at_tower / ride_fillet / wall_end_apron`), `geom.lathe_rz`, `finial.lead_hat / turned_finial` |
| frame / finish | `PlanFrame`, `composite_hidden_cull`, `recenter`, `composite_decals(timber=True, timber_soot=False)` |

**Stats.** These come from `round_01/stats.json` (6 views, 24 samples):
- 437,617 triangles (cap 1,000,000);
- est_hidden 11.9 %;
- 9 palette slots;
- Mask missing: none;
- 72 decal anchors (validated);
- 49 objects;
- bbox 12.2 x 12.2 x 8.4 m.

Guards:
- door eave lip 2.31 m (PASS);
- seal probe on the chimney junction: 0 leaks in 13,757 rays.

**Seal check by interior-volume rays.** The probe is `round_01/builder_extra/probe_interior.py`; results are in `probe_interior_r01.txt`.
- **Main attic:** 0 leaks in 18,000 rays.
- **Wing attic:** 0 leaks in 5,000 rays (valleys closed).
- **Dormer (behind its window room):** 0 leaks in 3,750 rays.
- **Rooms:** 43 escapes, all at the existing rubble-wall windows' sill line (window_spec, every building), not at an add-on.
- **Red twins of every close-up** (`builder_extra/*_red.png`): no red inside the roof outlines.

**Renders.**
- `round_01/` (six views);
- `round_01/preview/` (the first FAST build, before the producer note);
- `round_01/builder_extra/`:
  - v01-v06: valley;
  - d01-d05: dormer;
  - c01-c05: chimney;
  - h01: three-quarter view.

**Hash rule.** Not triggered, not run: every existing-module change is default-off (see `kit/changes/v7_cottage.md`, "Hash rule").

**Known gaps.**
- **Valley:** thatch only (no shingle laced valley).
- **Re-entrant corners:** a small closed dark pocket under the two crossing eave rolls at each inside corner (red clean).
- **Wing ridge:** a shadowed notch under the valley arch where the comb stops.
- **Dormer valley:** short ragged course ends near the dormer eave ends, and the dormer's rolled hood is chunky for a 1.3 m dormer.
- **Chimney through a slope / ridge:** the ring path is unproven.
- **Rubble-window sill escapes:** see above.
- **Recipe-only verge roll:** the house verge roll's rake runs straight into the stack and is trimmed and flaunched there.

## v7_cottage round 1 — score 7.8/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note 10), no surface-detail requests (note 12). Binding: producer notes 1-17, the CLIENT DIRECTION and Brief above, and the PRODUCER NOTE of 23:12. I re-read this log before starting and again before writing; no CLIENT DIRECTION or PRODUCER NOTE was added after the builder entry.

**Reviewed:**
- the recipe `build_v7_cottage.py` (133 lines), the new `kit/village_kit/components/roof_addons.py`, `kit/changes/v7_cottage.md` and `build.log` (guards, seal probe, the decal gate);
- the six `round_01` views, `stats.json`, `decal_anchors.json`, `preview/`, and all 33 builder close-ups and red twins, plus `probe_interior_r01.txt`.

**Director checks** (`renders/variants/v7_cottage/round_01/director_extra/`):
- `dir_render_r01.py`, adapted from v6 `dir_render_r03.py`, renders red and void twins with a red-pixel counter (`dir_render_r01.log`).
  - **i01-i08, interior volumes.** The camera sits inside the main attic (to both valleys, to the dormer, to the chimney gable), the wing attic (up to the main roof), and the rooms (up into both inside corners), with red twins.
    - Every red pixel is the open floor below the wall head: the building has no floors and the ground is hidden in the twin.
    - The roof volumes show **no daylight** at the valleys, the dormer (i04 and i05: 0 red at the dormer back), the chimney gable (i06: 0) or the inside corners (i07: 1 px; i08: 0).
    - This confirms the builder's interior rays.
  - **x01-x12, exterior junctions with void twins.** The dormer back (W and E), the dormer cheek foot, the dormer at mid distance, both inside-corner soffits, the W valley foot, the wing-ridge notch, both verge-into-stack junctions, the stack base against the gable, and the chimney shoulder.
  - **x13:** the door eave at actor eye level.
  - **x14 / x15:** thumbnails.
- `dir_lineup_r01.py` (copied from v6 `dir_lineup_r03.py`) renders the note-16 line-up of v3, v5, v6, **v7** and the roundhut at one scale (`lineup/L01-L03`), plus one-rig thumbnails (`lineup/T*`).

**Numbers** (all compliant):
- 437,617 tris (cap 1,000,000);
- hidden 11.9 % (cap 15 %);
- 9 palette slots;
- no mesh missing `Mask`;
- 72 decal anchors, 24 of them moss on the thatch;
- door eave lip 2.312 m (PASS) over a 2.09 m door head;
- chimney seal probe: 0 leaks in 13,757 rays.

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **8.1** | **Strengths:** a low, domestic L-plan that reads as a cottage at thumbnail (x14 / x15, T3). Its two sagging, swept thatch roofs meet in soft valleys. The producer note is applied: the chimney is now a short, chunky battered stack with a round pot, with no lighthouse read (side, c01, c02, L01). The verge rolls give one rolled line on every gable. **Against:** the dormer's rolled hood (recipe `verge_roll rc=0.22` on a 1.30 m dormer) is about a third of the dormer's width. At mid distance and at thumbnail it reads as a croissant or pretzel knot on the slope (x04, h01, hero, aerial), the one cartoon note in an otherwise believable roof (note 17: "never cartoon-wobbly"). Four spikes on a small cottage (two gable finials, the dormer finial and the chimney pot) are a little fussy. |
| 2 | Proportion and actor scale | **8.3** | **In scale:** a 1.95 m plank door with its threshold under a 2.31 m eave, small deep-set 0.40-0.55 m windows, and a storey and a half. Pitches are 52 / 47 / 50 deg, in range. The dormer window is 0.55 x 0.45 m and the stack head about 0.8 m over the ridge with a 0.46 m pot, all right next to the 1.8 m figure (actor_closeup, x13, L01). **Against:** the dormer hood's scale (axis 1). |
| 3 | Construction logic | **8.1** | **Sound:** the walls carry both roofs. The dormer cheeks stand on a sill beam under the host deck. The stack's broad battered base is bonded against the gable with no crevice (x11), and the rounded weathering steps it in at 4.7 m (x12). The roofs are trimmed and flaunched into the stack. **Against:** at both inside corners the clipped rafter tails end as **open-ended hollow boxes**, and thin deck or fascia **blades** poke out under the crossing eave rolls (x05 / x06 void: yellow box ends and blades; v06). It is the one place in the building that looks unbuilt, and it is 2.9 m up beside the front door. |
| 4 | Seams and junctions | **7.6** | **Closed:** every interior volume is closed (i01-i08), and the chimney junction is closed and probed. The valley crease is soft and fully covered, with no metal gutter (v01 / v02). **Against**, four visible defects, all at add-on junctions: (a) **inside corners:** a black pocket under the two crossing eave rolls, plus the open tails and blades above, all visible from eye level at the door (x13, v03, v04, v06). (b) **Valley foot:** the roll ends in a crumpled cap that faces inward (x07 void: yellow back faces; v03 / v04 / x13). (c) **Dormer back:** a dark slot runs under the dormer's ridge roll along its top course, visible at mid-shot (x01 / x02, d02 / d03, h01), and the valley arch over that ridge has a thin folded lip with a back-faced pocket (x01 void). (d) **Wing ridge:** two small holes where the comb stops under the valley arch (x08 void). The foot roll also crosses the dormer valley at each cheek with a back-faced sliver (x03 void, d04). |
| 5 | Distinctness and reuse | **8.0** | **Distinct, and the same village:** the first L-plan, dormer and chimney in the village, so clearly not v3 / v5 / v6. Note 16 holds in L01 / L02: the village rubble (`RUBBLE_LARGE`), the barn's thatch with its rolled verges and comb, lead hats and turned finials, the v3 / v5 lime fillet and lead aprons, and rough board-and-batten from `timber_walls`. **Reuse is good:** one new module built on about 15 existing ones, and `roof_valley` already serves twice (the wing and the dormer). **Reuse gaps:** (a) `chimney()`'s **default crown is still `"louvre"`**, the post-and-cone cupola the producer rejected at 23:12. A recipe that takes the defaults gets the lighthouse back. (b) The through-slope / ridge path (`_ring_abutment`) is unproven, while the Brief asks for "through any roof slope or ridge". (c) The valley and the dormer are thatch only (accepted for round 1; logged). |
| 6 | Technical compliance | **8.5** | **Within limits:** triangles, hidden %, palette, `Mask`, anchors (with thatch moss, unlike v6 r1). The build is deterministic and seeded, and every existing-module change defaults off. **Minor:** the recipe docstring still describes the chimney crown as "a round SMOKE LOUVRE ... lead cone ... turned finial". The hash rule was reasoned, not run (acceptable; the audit may run it). |

**Overall 7.8 / 10: REVISE (round 2 of at most 3).** The cottage is on theme and reads as the same village, and the three add-ons are real, reusable kit functions with sealed interiors. It is held below 8.2 by the junction finish where the add-ons meet the existing roof parts (the inside corners, the valley foot, the dormer back) and by the dormer hood's scale. All of these are local fixes in `roof_addons.py` and `linear_roof.py`; no re-design is needed.

**Village theme (notes 16 / 17): PASS, with one caveat.**
- **Same materials and details:** the shared palette only, with the village rubble, thatch, verge rolls, comb, finials and lead flashing all reused.
- **Round element:** the round battered stack with its rounded weathering and round pot is integral: bonded to the gable and flashed into the roof.
- **Soft lines:** ridge sag, swept eaves, rolled verges and rolled valleys.
- **Low and working, no tower:** in the line-up it is the lowest, most domestic building and a good counterpoint to the turreted v3 / v5.
- **Caveat:** the oversized dormer hood (must-fix 4b).

**Add-on reusability:**
- **`roof_valley`:** genuinely reusable. Any two GableRoofs at any yaw, proven for an L and for a dormer. Thatch only.
- **`GabledDormer` / `gabled_dormer`:** reusable on any GableRoof slope, with host clips. Thatch only.
- **`chimney`:** reusable, but proven at a gable only, and its default crown is the rejected one.

**Strengths:**
- One declarative recipe; the add-ons are a few lines each in any recipe.
- Sealing: the interior volumes are closed at every add-on (the builder's rays and the director's i01-i08 agree), and the chimney seal probe is clean.
- The producer note was applied in full: a chunky chimney and rolled verges on every thatch gable, including the one-free-verge kit option.
- On-palette decals, including moss on the thatch.

**Must-fix (round 2):**
1. **Inside (re-entrant) eave corners, W and E** (`roof_valley(foot="crest")` with the two `linear_roof` eave rolls and rafters; x05, x06, v06, x13):
   - drop or end-cap every rafter tail cut within about 0.35 m of the corner (no open box ends);
   - remove the thin deck / fascia blades that stand out under the rolls;
   - close the dark pocket with one rounded corner, for example a small closing cap or a crease-roll tuck that wraps both eave rolls, or a boarded soffit fill.

   Proof: x05 / x06 void twins with no yellow at the corner, and x13 clean at eye level.
2. **Valley foot cap** (`_crease_roll` ends, `roof_valley` orientation loop; x07, v03, v04): the foot cap faces inward and is crumpled. The per-station flips of `a` / `b` near the eave-roll crest are the likely cause of the twisted section. Keep the orientation continuous along the line, for example by flipping to agree with the previous station, then end the roll in a clean rounded tuck. Proof: x07 void shows no yellow.
3. **Valley over a ridge** (the wing ridge and the dormer ridge back; x01, x08):
   - make the arch section closed, with no thin folded lip;
   - close the comb-stop holes: end the comb on a rounded stop under the arch's skirt, or let the skirt bury the last comb units instead of dropping them.

   Proof: x01 / x08 void twins clean at the arch.
4. **Dormer** (`GabledDormer` / `gabled_dormer`, recipe):
   - (a) Close the dark slot under the dormer's ridge roll: give the dormer's GableRoof `ridge_seat=True` (put it in `DORMER_SOFT`), as the host has.
   - (b) Scale the hood to the dormer: about `rc 0.11-0.13` and `apex_bend about 0.10` for a 1.3 m dormer. Make `gabled_dormer`'s verge-roll default derive from `D.hw`, so a recipe cannot oversize it. Check x04 and the hero view.
   - (c) Taper the foot roll into the dormer valley's skirt at each cheek, rather than crossing it (x03 void sliver, d04 wedge).
5. **Chimney as a reusable add-on** (`roof_addons.chimney`):
   - (a) Make the default `crown="pot"`. Keep `"louvre"` opt-in, low (h ≤ 0.3 m), with no finial by default.
   - (b) Fix the recipe docstring.
   - (c) Prove `_ring_abutment` once, on a FAST scratch build: a stack of r ≈ 0.5 through a slope (v7's back slope or a copy of another design). Use the seal probe and one red / void twin pair. It does not have to stay in the cottage composition.

**Nice-to-have:**
- **Finials:** drop the dormer's finial and keep its lead hat, so the cottage has fewer spikes.
- **Lead aprons:** bend them to the stack radius; they read as flat boards on the round stack (x09, x10, c03).
- **Valley skirts:** taper the toothy cut course ends that show along both skirts (x07, v01).
- **Housekeeping:** merge the CHANGELOG 1.19 entry.
- **Outside the add-on scope:** the rubble-window sill escapes (kit window) are a separate kit item.

## v7_cottage round 2 — builder entry

I re-read this log before starting and again before writing. No CLIENT DIRECTION or PRODUCER NOTE was added after the round-1 grade. Every change is in `kit/village_kit/components/roof_addons.py` plus the recipe; `linear_roof.py` was not touched. The full table is in `kit/changes/v7_cottage.md`, "Round 2".

**Must-fix, item by item:**

1. **Inside eave corners W and E.** `roof_valley(corner="auto")` now runs `_corner_close` at each re-entrant corner:
   - **Rafter tails:** every tail within 0.35 m of the other roof's plan columns is dropped whole (161 rafter polygons), so there are no open box ends. The big yellow box in x05 is gone.
   - **Soffit fill:** a closed boarded slab (M_timber) sits under the lower deck between the two wall faces and lips.
   - **Pocket:** a rounded thatch closing knot sits where the two eave rolls cross, about the rolls' own size. The dark pocket is filled (x05, x06, x13, x16).
   - **Void counts (yellow):** x05 10,016 -> 2,303; x06 19,307 -> 4,195.
   - **Not fully clean:** what is left is two thin wall-head or board wedges near the wall corner (they were already there in round 1) and small slivers at the rolls' clipped ends.
2. **Valley foot cap.** The skirt directions are now continuous along the line (`_continuous`: the per-station probe only votes), and normals and skirts are smoothed. Each roll end is a rounded tuck: 4 quarter-circle rings, diving 6 cm, closed by triangle fans. This replaces the flat non-planar cap. x07 void yellow 3,994 -> 1,220: a small inward patch remains at the foot tuck where it meets the eave roll.
3. **Valley over a ridge.**
   - `_cut_ridge_under_arch` bisects the wing (and dormer) ridge roll and comb 0.12 m on the wing side of the arch crest and fills the cut, so the roll ends closed under the arch skirt.
   - With the smoothed normals, the arch lip is calmer.
   - x08 void 2,571 -> 1,641; x01 772 -> 423. Small remnants remain at the arch shoulders.
4. **Dormer.**
   - (a) `DORMER_SOFT` now has `ridge_seat=True`.
   - (b) New `dormer_verge_roll(D.hw)`: rc 0.117 / apex_bend 0.10 / bend_over 0.078 for the 1.3 m dormer. It is the `gabled_dormer(verge_roll="auto")` default, and a recipe dict is capped at 0.20 / 0.17 hw. The recipe now uses the default (it was rc 0.22).
   - (c) The foot roll stops 0.16 m under the dormer eave and tapers over 0.40 m into a tuck that dives 0.10 m into the host thatch. x03 void is 512 -> 507, so this one is not improved measurably.
5. **Chimney.**
   - (a) The default is now `crown="pot"`. The louvre is opt-in, with h 0.24 by default, clamped to 0.30 m, and no finial by default.
   - (b) The recipe docstring now describes the pot.
   - (c) **`_ring_abutment` proven** on a FAST scratch build, `scratch/ring_stack.py`: the cottage plus an r 0.52 stack through the back slope.
     - The proof found a real bug: `_ring_trace` started above the ridge, where the battered radius lies inside the trimmed hole, so it never hit the roof. It now starts at `z_lip`, gaps under 15 % are interpolated, and the ring is registered for the seal probe.
     - **Result:** "roof / stack ring" 0 leaks in 57,961 rays. Twins: `r01_ring_stack_NE_void` (338 yellow, at the stones' joints) and `r02_ring_stack_NW_low_void` (14 yellow); `i09_attic_to_ring_stack_red`: 0 red.

**Stats** (`round_02/stats.json`):
- 438,617 triangles (cap 1,000,000);
- est_hidden 12.1 %;
- 9 palette slots;
- Mask missing: none;
- 71 decal anchors;
- 53 objects;
- bbox 12.2 x 12.2 x 8.4 m.

**Guards:**
- door eave lip 2.312 m: PASS;
- chimney seal probe: 0 leaks in 13,757 rays.

**Renders:**
- `round_02/`: the six views.
- `round_02/builder_extra/` (`b_render_r02.py`, copied from the director's r01 script):
  - x05 / x06 / x07 / x08 / x13 / x16 from the final blend;
  - x01 / x03 / x04 and the ring twins (r01 / r02 / i09) from the FAST scratch blend, which has the same front geometry with no cull;
  - logs: `b_render_r02_final.log` and `b_render_r02_fast.log`.

**Hash rule.** Not triggered: `roof_addons.py` is new in kit 1.19 and used only by v7, and no existing module changed.

**Known gaps (for the grade):**
- The yellow at the corner, valley foot and arch is reduced, not zero (see above).
- At mid distance the smaller dormer hood still reads as two crossing rolls over the apex (hero).
- The dormer finial is kept (nice-to-have not done).
- The lead aprons are not bent to the stack radius (nice-to-have).
- The CHANGELOG is not merged.
- The rubble-window sill escapes are a separate kit item.

I stopped at the time budget after one build iteration and the final build.

## v7_cottage round 2 — score 8.0/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing, no surface-detail requests. Binding: producer notes 1-17, the CLIENT DIRECTION and Brief above, and the PRODUCER NOTE of 23:12. I re-read this log before starting and again before writing: there is no new CLIENT DIRECTION or PRODUCER NOTE after the round-1 grade.

**Reviewed:**
- the recipe `build_v7_cottage.py`, `roof_addons.py` (round-2 code: `_crease_roll` tucks, `_continuous` / `_smooth_rows`, `_corner_close`, `_cut_ridge_under_arch`, `dormer_verge_roll`, `_dormer_foot_roll`, `_ring_trace` / `_ring_abutment`, `chimney(crown="pot")`), `linear_roof.py` (`VERGE_ROLL`, `eave_roll`), `kit/changes/v7_cottage.md` "Round 2", `build.log`, `scratch/ring_stack.py`;
- the six `round_02` views, `stats.json`, and all 21 builder close-ups and twins in `round_02/builder_extra`.

**Director checks** (`renders/variants/v7_cottage/round_02/director_extra/`; counts in `dir_counts_r02.txt`):
- `dir_render_r02.py` (copied from `round_01/director_extra/dir_render_r01.py`): every r01 shot re-run on the **final** blend (i01-i08, x01-x15), plus new add-on junction shots: x17 E valley foot, x18 W valley foot at eye level, x19 dormer hood at mid distance at eye level, x21 chimney pot head, x22 E inside corner (wide, eye level), x23 W corner knot close, x24 wing ridge under the arch (side), x25 dormer W cheek. On the FAST ring-stack blend: ri10 (attic up to the through-slope stack, red) and rx26 (the stack at the ridge, void).
- `dir_lineup_r02.py` (copied from r01): the note-16 line-up v3 / v5 / v6 / **v7** / roundhut (`lineup/L01-L03`, thumbnails `T*`).

**Numbers** (all compliant): 438,617 tris (cap 1,000,000); hidden 12.1 %; 9 palette slots; no mesh missing `Mask`; 71 decal anchors; door eave lip 2.312 m PASS; chimney seal probe 0 / 13,757; ring seal probe 0 / 57,961.

**Sealing (interior volumes):** i01-i08 give exactly the round-1 counts (all red is the open floor below the wall heads; i05 / i06 / i08 0, i07 1 px), so the round-2 changes opened nothing. ri10 (attic to the through-slope ring stack): **0 red**. The volumes are closed at every add-on.

**Void yellow, round 1 -> round 2 (final blend):** x01 772 -> 413; x02 941 -> 271; x03 512 -> 507; x04 856 -> 347; x05 10,016 -> 2,303; x06 19,307 -> 4,195; x07 3,994 -> 1,220; x08 2,571 -> 1,641. New: x17 1,964; x18 1,024; x22 3,233; x23 3,484 (mostly the board wedge at the frame foot); x24 683; x25 0; rx26 20.

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **8.1** | **Strengths:** still the low, domestic L that reads as a cottage at thumbnail. The soft swept thatch, rolled verges and short round stack with its pot sit well in the line-up (L02: the lowest, most domestic building, a good counterpoint to the turreted v3 / v5). **Against:** the dormer hood is **unchanged in section**. It is still two fat sausage rolls meeting in a notch at the apex, with bulbous dropped ends (x19, x04, hero, front, T3 thumbnail: a "pretzel" knot). The cause is in the code, see must-fix 3: `rc` in `VERGE_ROLL` is the eave-corner **fillet** radius, not the roll's section. The section is always `GableRoof.eave_roll()`'s default radius 0.16 m (`linear_roof.py:1708` calls it with no arguments), the same as the host's 10 m roof. |
| 2 | Proportion and actor scale | **8.3** | The door, eave, windows, dormer window and stack head are unchanged and right against the 1.8 m figure (actor_closeup, x13). **Against:** the dormer hood scale (axis 1). |
| 3 | Construction logic | **8.2** | **Improved:** the open-ended rafter-tail boxes at the inside corners are gone (x05 / x06), and the soffit board gives the corner a built underside. The wing ridge roll and comb now end closed under the arch (x24). **Against:** under each inside corner a pair of thin wall-head / fascia boards still **crosses in an X** below the soffit board (x05, x06, x22: the two yellow wedges). The corner knot reads as a separate ball plugged between two butting rolls, with small dark slots beside it (x23, x16, x22). At eye level it is a knob, not the rolls running round the corner. |
| 4 | Seams and junctions | **7.9** | **Fixed or much better:** inside-corner yellow is down 77-78 %. The arch over the dormer ridge is calmer (x01 / x02 down 46-71 %). The chimney is flashed and sealed at the gable and, now, through a slope (ring flaunching, 0 leaks, 0 red). **Still visible:** (a) **the valley foot tuck is still crumpled.** A folded flap with a dark lip shows at both feet (x07, x17, x18), at eye level by the door (x13, top right), and as a dark pocket at mid distance (x04, bottom right). (b) **Wing ridge under the arch:** the two dark wedges either side of the ridge comb, where the arch skirt stands clear of the cut ridge-roll ends (x08 clay and void, 1,641 yellow). (c) The inside-corner slots beside the knot and the crossed boards (axis 3). (d) The dormer foot roll still crosses the dormer valley skirt at the cheek (x03, 507, not improved). |
| 5 | Distinctness and reuse | **8.3** | **Same village (notes 16 / 17): PASS.** It uses the shared palette, the village rubble, the barn's thatch with its rolled verges and comb, lead hats and turned finials, the v3 / v5 lime flaunching and lead, the kit board-and-batten and window, and the round battered stack with its round pot. The lines are soft throughout and there is no tower. **Reuse improved:** `chimney` now defaults to the pot, the louvre is opt-in and low, and the through-slope path is proven: the builder's proof found and fixed a real `_ring_trace` bug, and the ring is registered for the seal probe. `roof_valley(corner="auto", ridge_cut=)` is a generic option for any L / T plan or any dormer. **Against:** `dormer_verge_roll` does not do what its docstring says, so any recipe that reuses the dormer gets the oversized hood. The valley and dormer remain thatch only, while most village roofs are shingle (a logged kit gap; it matters for the later designs, but is not a must-fix here). |
| 6 | Technical compliance | **8.5** | All limits are met. The build is deterministic and seeded. The new options are default-on only inside the new module, so the hash rule is not triggered. The recipe docstring is fixed. Minor: the CHANGELOG 1.19 entry is not merged. |

**Overall 8.0 / 10: REVISE (round 3 of at most 3, the last).** This is real progress on every round-1 item, the interior sealing is intact, and the chimney is now a properly reusable add-on. The grade is held under 8.2 by three visible junction finishes: the valley foot tuck, the inside-corner read and the arch-over-ridge wedges. The dormer hood fix also missed its target, because `rc` is the wrong parameter. All four are local fixes in `roof_addons.py` and `linear_roof.py`; none needs a re-design.

**Village theme (notes 16 / 17): PASS.** The materials and details are the same as the village's. The round element (battered round stack, rounded weathering, round pot) is integral. The soft lines are everywhere: ridge sag, swept eaves, rolled verges, rolled valleys. It is low and working. The one off-theme note is the cartoon dormer hood (note 17: "never cartoon-wobbly"), must-fix 3.

**Add-on reusability:**
- **`roof_valley`:** genuinely reusable (any two GableRoofs at any yaw, L / T and dormer-into-host, with auto corner closing and the ridge cut). Thatch only.
- **`chimney`:** genuinely reusable: at a gable via `wall_abutment`, and through a slope via the ring (proven, sealed), with the pot as the default. Pass.
- **`GabledDormer` / `gabled_dormer`:** reusable on any GableRoof slope with host clips, but its hood sizing is ineffective (must-fix 3). Thatch only.

**Strengths:**
- Measured, honest reporting.
- The ring-stack proof found a real bug.
- The orientation fix in `_continuous` is the right kind of fix (continuity plus a majority vote).
- The ridge cut and the corner close are generic options with defaults, not recipe hacks.
- Interior volumes are unchanged and closed.
- The pot crown and low opt-in louvre honour the 23:12 note in the kit, not just in this recipe.

**Must-fix (round 3, final):**
1. **Valley foot tuck** (`_crease_roll` foot end, `roof_valley`; x07, x17, x18, x13, x04):
   - The folded flap still forms where the tuck rings (scaled copies of the last section) meet the eave-roll crest.
   - End the foot **inside the corner closer** instead of in the open. For example, extend the foot end to the knot / corner centre and set `sink` at least equal to the roll crown at that end, so the tuck dives into the knot or corner roll. Or stop the line about 0.25 m earlier and let the last section shrink to the eave roll's own crest line.
   - Proof: x07 / x17 void yellow under about 300, with no flap or dark lip in clay x13 / x17 / x18 / x04.
2. **Inside corners read as one rounded corner** (`_corner_close`; x05, x06, x16, x22, x23):
   - (a) Replace the ball knot with a short swept **internal-corner roll**: the eave roll's own D section turned through the re-entrant angle in plan, joining the two clipped roll ends (the same idea as the verge roll's corner fillet). Alternatively, enlarge and re-centre the knot so it fully envelops both clipped roll ends (about ru 1.5 Ru), its underside landing on the soffit board with no slots beside it.
   - (b) Clip or cover the two crossing wall-head / fascia boards under the corner. Extend the soffit board over them, or drop those units as the rafter tails are dropped.
   - Proof: x05 / x06 yellow under about 600, and x16 / x22 at eye level showing one rounded corner with no X of boards.
3. **Dormer hood: the real scale fix** (`linear_roof.py` + `GabledDormer`; x19, x04, hero, T3):
   - `VERGE_ROLL.rc` is the eave-corner fillet, so `dormer_verge_roll` changed only the fillet and the apex bend.
   - Add a roll-section option with old defaults, for example `GableRoof(eave_roll=dict(radius=, proud=, drop=))` or `linear_roof(roll_radius=None)` passed to `roof.eave_roll(...)` at line 1708.
   - Have `GabledDormer` set the eave and hood roll radius from the dormer, about 0.15 * hw (about 0.10 m for 1.3 m). Optionally merge the two rake rolls over the apex into one continuous arch, with no notch.
   - Fix the `dormer_verge_roll` docstring.
   - Proof: x19 / x04 / hero show a slim rolled hood about a sixth of the dormer's width or less, with no "pretzel" at thumbnail.
4. **Wing ridge under the arch** (`_cut_ridge_under_arch` / the arch section; x08): close the two dark wedges either side of the comb. Let the arch skirt bury into the cut ridge-roll end (deeper `bury` at stations with |ys| < 0.3), or round the cut end like the tucks. Proof: x08 yellow under about 500, with no dark wedge in clay.

**Nice-to-have:**
- **Dormer foot roll at the cheeks** (x03, unchanged at 507): end it under the dormer valley's skirt.
- **Dormer finial:** drop it and keep the lead hat (fewer spikes).
- **Lead aprons:** bend them to the stack radius.
- **Housekeeping:** merge CHANGELOG 1.19.
- **Later kit item:** a shingle (laced or swept) valley, so the valley and dormer serve the shingle-roofed designs too.

## CLIENT DIRECTION (2026-10-18, session 2, 00:10): the cottage needs an EYEBROW DORMER (producer note 18); apply in round 2

Client's words: "If the cottage will be rectangular / square it minimum needs a eyebrow dormer". Read producer note 18 at the end of `director/art_bible.md`.

**Round-2 fixer:** apply this in THIS round, together with the round-1 must-fixes.
- **Add at least one eyebrow dormer** to the cottage. Each of its wings is a rectangular block.
  - Put it on the main wing's other slope, or on the cross wing, wherever it reads best from the main views.
  - **Keep** the gabled dormer: the add-on track has to prove that one too.
- **The eyebrow on THATCH:** extend the eyebrow option to `linear_roof(covering="thatch")`, with defaults unchanged.
  - The thatch courses roll over one continuous arch (`profile="arch"`), with the same lift-along-slope / respace logic.
  - The thatch eave roll follows the arch over the window as a rolled lip.
  - Under it, the kit window in a small rough-boarded or daub-and-timber front.
  - This is the classic thatched eyebrow. Make it as smooth and continuous as the harbour house's round-8 eyelid.
  - Sealed (interior-volume rays); hidden <= 15 %; <= 1 M tris.
- **Hash rule:** if an existing default changes, rebuild and compare (8 buildings).