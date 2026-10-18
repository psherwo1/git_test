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
## PRODUCER NOTE (2026-10-18, session 2, 00:11): the eyebrow is a MUST-FIX

The round-2 fixer started before the 00:10 CLIENT DIRECTION. If you are still working, apply it now, and re-read this log before writing your entry. **Art Director:** a cottage round without an eyebrow dormer (producer note 18) cannot pass; give at most 8.1. **Next fixer:** do it first.

## CLIENT DIRECTION (2026-10-18, session 2, 00:20): ROUNDED ROOFS, "an oval on the rectangle" (producer note 19); a cottage must-fix

Client's words: "if the walls be square and angular we should counterbalance with rounded roofs. Not just /\ An oval on the rectangle". The client chose **"Rounded hips + soft crown"**. Read producer note 19 at the end of `director/art_bible.md`.

**For the cottage:**
- **Both wings keep their rectangular rubble walls**, but get **rounded roofs**:
  - every FREE end is a round hip (half-cone), so there are no gable ends;
  - the cross-section is softly convex with a rolled ridge;
  - sag and swept eaves stay;
  - thatch.
- **The L junction stays a soft valley.** The wing's joined end has no hip.
- **The chimney** moves through the roof (a ridge or slope stack) or rises against an end wall through the round hip. It stays short and chunky, with the round pot, and is flashed into the curved thatch.
- **Keep the gabled dormer** (a dormer is allowed on the rounded roof) **and add the thatch eyebrow** (note 18, the 00:10 direction).
- **Kit:** the rounded roof as a reusable option or module (note 19), defaults unchanged, hash rule if an existing default changes.

**Order for the fixers (time matters, but get it right):** the rounded roof is the biggest change.
- **Round-2 fixer:** if your round's builds are already done without it, finish the round-1 seam must-fixes and the eyebrow if you can, record what is left, and write your entry. Do NOT half-build the rounded roof.
- **The next fixer:** do the rounded roof first.
- **Art Director:** a cottage with /\ gable roofs, or without an eyebrow, cannot pass; give at most 8.1.
- The producer may extend the cottage's round cap so it can be done properly.
## v7_cottage round 3 — builder entry

I re-read this log before starting and again before writing. **The 00:10 / 00:11 / 00:20 CLIENT DIRECTIONS and PRODUCER NOTE (producer notes 18 and 19: the thatch eyebrow and the ROUNDED-HIP "loaf" roofs) are NOT applied in this round.** They reached the log after I started, when this round's build was already running. The 00:20 note says "do NOT half-build the rounded roof", and it needs a new kit roof option (round hips, convex crown, thatch eyebrow, a valley with no hip at the joined end, a chimney through curved thatch). That is a re-design, not a seam fix, and it does not fit in this round's roughly 75 minutes. **As built, this round cannot pass (at most 8.1, per the notes).** I recommend the producer extend the cottage's cap by one round for notes 18 and 19, done first and done properly. Everything below addresses only the round-2 must-fixes on the existing gabled design, and it carries over to the rounded design: the valley, the corner roll, the dormer hood section and the ridge arch.

**Must-fix, item by item** (code in `kit/village_kit/components/roof_addons.py`; one new option in `linear_roof.py`; table in `kit/changes/v7_cottage.md`, "Round 3"):

1. **Valley foot tuck** (x07, x17, x18):
   - At a closed corner the line now stops 0.22 m short of the wing roll's crest, off the round nose where the section twisted (`roof_valley(foot_back=)`).
   - Each foot tuck runs on 0.26 m and sinks crown + 8 cm into the new corner roll.
   - Void yellow, final blend, r2 -> r3: **x07 1,220 -> 498; x17 1,964 -> 113 (under 300); x18 1,024 -> 487.**
   - Clay x17: the folded flap is gone, but a small dark lip remains where the tuck enters the corner roll.
2. **Inside corners** (x05, x06, x16, x22, x23):
   - **(a)** The ball knot is replaced by ONE swept internal-corner roll (`_corner_roll`): the eave roll's own D section turned round the re-entrant lip corner on a 0.25 m fillet, blending from one slope to the other. The two straight eave rolls are cut back inside it.
   - **(b)** The soffit slab now spans from under the lower deck to just over the higher deck top, and stops 5 cm inside the lips under the roll bodies. The decks' crossing cut board ends are buried in it, so the X of boards is gone.
   - Hero and x22: the eave reads as one rolled edge running round the corner.
   - Yellow r2 -> r3: **x23 3,484 -> 77; x05 2,303 -> 1,216; x06 4,195 -> 1,660; x22 3,233 -> 2,799.** x05 and x06 are still above the ~600 target: thin slivers along the slab rim and the wall head, not a box or an X.
3. **Dormer hood, the real scale fix:**
   - NEW `linear_roof(eave_roll=None)`: a dict of `GableRoof.eave_roll` keywords sets the roll SECTION, which the verge hood also sweeps. `None` = the old call.
   - `GabledDormer` now has a thinner dormer thatch (thick 0.13, step 0.05, deck 0.025), and `roll=dict(radius=0.15 * hw, proud=0.02, drop=0.015)` is passed by `gabled_dormer`.
   - The `dormer_verge_roll` docstring is corrected (`rc` = the eave-corner fillet).
   - x19 / x04 / hero: a slim rolled hood, about a fifth of the dormer's width, with no pretzel. A small notch remains where the two rakes meet at the apex. The optional single continuous arch over the apex was not done.
4. **Wing ridge under the arch** (x08, x24):
   - The skirts bury up to 0.12 m deeper over the ridge roll.
   - The wing skirt is steered onto the ridge axis, and its end dives vertically (`_crease_roll(bury_dir=)`). The probe showed the radial dive over the tight bend folding the skirt end back on itself (ring 10 / 11 faces reversed).
   - The ridge-cut fill faces are oriented outward.
   - **Not fixed:** x08 1,641 -> 1,586 and x24 683 -> 616. The two dark wedges beside the comb remain in clay. The last change (the vertical dive) went into the final build without a FAST check, because of time. Next step: shorten the wing skirt to end before the comb gap, or drop the comb units under the whole skirt.

**Sealing:** i01 / i02 / i03 / i07 / i08 give exactly the round-2 counts (81,560 / 68,651 / 4,665 / 1 / 0 red, all the open floor below the wall heads). The new corner roll and slab opened nothing.

**Stats** (`round_03/stats.json`):
- 438,685 triangles (cap 1,000,000);
- est_hidden 11.8 %;
- 9 palette slots;
- Mask missing: none;
- 53 objects;
- bbox 12.2 x 12.2 x 8.4 m;
- door eave lip 2.312 m: PASS.

**Renders:**
- `round_03/`: the six views.
- `round_03/builder_extra/`, from the final blend (`b_render_r03.py`, copied from the director's r02 script; counts in `b_render_r03_final.log`):
  - x04-x08, x13, x16-x19, x22-x24;
  - i01-i03, i07, i08.
- `builder_extra/fast/` and `fast2/`: the two FAST iterations.
- `probe_*.py`: ray / mesh probes.

**Hash rule:** not triggered. The only existing-module change is `linear_roof(eave_roll=None)`, whose default is the old `roof.eave_roll()` call; everything else is in `roof_addons.py`, which only v7 imports.

**Known gaps:**
- **Producer notes 18 and 19 not applied:** the eyebrow, the rounded hips and crown, and moving the chimney.
- **x08 / x24:** the arch wedges.
- **x05 / x06:** slivers above target.
- **x17:** the small lip at the foot.
- **Dormer:** the apex notch, and the finial is kept.
- **Lead aprons:** not bent to the stack.
- **Valley:** thatch only.
- **Stray folders:** the first FAST render pass wrote into `C:\round_03\builder_extra\fast` (a relative path). The files were moved into `round_03/builder_extra/fast`, but the two empty folders remain at `C:\round_03` (removal was blocked).

## v7_cottage round 3 — score 7.9/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing, no surface-detail requests. Binding: producer notes 1-19, the CLIENT DIRECTIONS of 2026-10-17 and of 2026-10-18 00:10 / 00:20, and the PRODUCER NOTES of 23:12 and 00:11. I re-read this log before starting and again before writing: the latest entries are the 00:10 / 00:11 / 00:20 directions (notes 18 and 19) and the builder's round-3 entry. Nothing came after those. **Under the 00:11 and 00:20 notes, a cottage with /\ gable roofs and no eyebrow cannot pass and is capped at 8.1.** Both conditions hold here, as the builder states openly.

**Reviewed:**
- the recipe `build_v7_cottage.py`;
- the round-3 code in `roof_addons.py`: `_corner_roll`, `_corner_close`, `roof_valley(foot_back=, ridge_bury=)`, `_crease_roll(bury_dir=)`, `GabledDormer(roll=, thick=0.13)`, `dormer_verge_roll`;
- `linear_roof.py` (`eave_roll=None`; line 1713 calls `roof.eave_roll(**(eave_roll or {}))`, so the default is the old call);
- `kit/changes/v7_cottage.md`, "Round 3";
- the six `round_03` views, `stats.json`, `render_review.log`, and every builder close-up and twin in `builder_extra/` (including `fast/` and `fast2/`).

**Director checks** (`renders/variants/v7_cottage/round_03/director_extra/`; counts in `dir_counts_r03.txt`):
- `dir_render_r03.py` (copied from r02) re-runs every r02 shot on the final blend: i01-i08 and x01-x25.
- It adds five new add-on junction shots: x26 dormer apex close, x27 / x28 E / W corner roll from above, x29 E corner roll from below, and x30 E valley foot close.
- `dir_lineup_r03.py` (copied from r02) renders the note-16 line-up of v3, v5, v6, **v7** and the roundhut (`lineup/L01-L03`, `T*`).

**Numbers** (all compliant):
- 438,685 tris (cap 1,000,000);
- hidden 11.8 %;
- 9 palette slots;
- no mesh missing `Mask`;
- door eave lip 2.312 m: PASS;
- 53 objects.

**Sealing (interior volumes): PASS.** i01-i08 give exactly the r1 / r2 counts: i01 81,560, i02 68,651, i03 4,665, i04 655, i05 0, i06 0, i07 1 px, i08 0. All the red is the open floor below the wall heads. The corner roll, the soffit slab, the thinner dormer thatch and the deeper arch bury opened nothing. Exterior twins show no see-through at any add-on junction: x05's 46 red px are sky beyond the soffit edge, and the other red counts are sky in frame.

**Void yellow, r2 -> r3 (final blend; my counts equal the builder's):**

| shot | r2 | r3 | note |
|---|---|---|---|
| x01 | 413 | 1 | the thinner dormer thatch |
| x02 | 271 | 2 | the thinner dormer thatch |
| x03 | 507 | 507 | |
| x04 | 347 | 204 | |
| x05 | 2,303 | 1,216 | |
| x06 | 4,195 | 1,660 | |
| x07 | 1,220 | 498 | |
| x08 | 1,641 | 1,586 | |
| x17 | 1,964 | 113 | |
| x18 | 1,024 | 487 | |
| x19 | 397 | 232 | |
| x22 | 3,233 | 2,799 | |
| x23 | 3,484 | 77 | |
| x24 | 683 | 616 | |
| x26 | new | 149 | |
| x27 | new | 173 | |
| x28 | new | 0 | |
| x29 | new | 2,124 | thin slab and board rims |
| x30 | new | 1 | |

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **7.8** | **Better:** the dormer hood is now a slim roll about a fifth of the dormer's width. The pretzel is gone at mid distance and thumbnail (x19, x04, hero). The inside corners read as one rolled eave running round the corner (hero, x22). The low, domestic L is still right in the line-up. **Against (notes 18 / 19, client rules):** both wings are still plain /\ gables on square rubble walls, with three flat gable ends and no round hip or convex crown. There is also no eyebrow. In the line-up (L02) v7 is now the most angular roofline in the village: next to v3's round end, v5's tower, the barn's swept cart gable and the roundhut cone, it reads as the generic box the client warned against. The round element, the stack, sits at the back gable and cannot be seen from the front (front, hero). |
| 2 | Proportion and actor scale | **8.3** | Unchanged and right against the 1.8 m figure: the 1.95 m door under the 2.31 m eave, small deep windows, the dormer window, and the stack head about 0.8 m over the ridge (actor_closeup, x13). The thinner dormer thatch suits a 1.3 m dormer. |
| 3 | Construction logic | **8.3** | **Fixed:** the X of crossed wall-head / fascia boards is buried in the soffit slab (x05 / x06 / x29: only thin rim slivers remain). The corner is a built underside under one swept roll, not a ball plugged between two rolls (x23: 77). The walls carry both roofs, the dormer stands on its sill beam, and the stack is bonded and stepped. No floating or visibly interpenetrating parts. |
| 4 | Seams and junctions | **8.1** | **Fixed or much better:** the valley-foot flap is gone (x17 113, x30 1). The dormer back is essentially clean (x01 / x02: 1 / 2). The corner knot is gone (x23 77). **Still visible:** (a) the **wing ridge under the arch**: the two dark wedges either side of the comb and a ragged, frilled arch-skirt edge, seen from the ridge side (x08 1,586, x24 616; clay x08). (b) **The corner-roll joints:** at eye level by the door, the swept corner roll meets the straight eave rolls with two flat-faced "sleeve" bands, a visible pipe-fitting seam (x13, x22). From above, where the valley-foot tuck enters the corner roll, a small lumpy knot with a dark crack and a slot remains (x27, x17). (c) Thin slab and board rim slivers under the corner (x29 2,124; x05 / x06 above the ~600 target). (d) The dormer apex: a small notch where the two rake rolls meet under the lead hat (x26). (e) The dormer foot-roll cheek (x03 507, unchanged). |
| 5 | Distinctness and reuse | **7.9** | **Same village (note 16): PASS.** It uses the shared palette, the village rubble, the barn thatch with its rolled verges and comb, the lead hats and turned finials, the v3 / v5 lime flaunching and lead, the kit board-and-batten and window, and the round battered stack and pot. **Note 17 / 18 / 19 theme: NOT MET.** The client's 2026-10-18 rules make round hips, a convex crown and a thatch eyebrow the cottage's organic language; none is present. **Reuse:** `roof_valley`, `chimney` and `GabledDormer` are genuinely reusable kit functions with defaults. The new `linear_roof(eave_roll=)` and `GabledDormer(roll=)` make the hood scale correctly for any dormer, which is the right generic fix. **Against:** all three are thatch only, and none is yet proven with the note-19 rounded roof, which the bible says they must work with (valley, dormer, chimney through the roof or a round hip). |
| 6 | Technical compliance | **8.5** | All limits are met, the build is deterministic and seeded, and the hash rule is not triggered: the one existing-module change keeps the old default call (verified at `linear_roof.py:1713`). **Minor:** the stray empty folders at `C:\round_03\builder_extra\fast` are outside the project and still need to be removed. CHANGELOG 1.19 is not merged. |

**Overall 7.9 / 10: REVISE. Not a pass, and the 3-round cap is reached.** On its round-2 must-fixes this is the best round so far:
- the valley foot, the dormer hood scale, the dormer back and the inside-corner construction are fixed;
- the sealing is intact;
- the seam axis alone would sit at about 8.1-8.2.

It cannot pass, however. The client's 2026-10-18 rules (notes 18 and 19) are not applied, as the builder reported: there are plain /\ gables on square walls and no eyebrow, which puts silhouette and distinctness under the pass mark. **Recommendation to the producer:** extend the cottage by one round (the 00:20 note allows it). Do notes 18 and 19 first, as kit options, and carry the round-3 seam work over. The builder is right that this is a re-design of the roof form, not a seam fix.

**Village theme (notes 16 / 17 / 18 / 19):**
- **Notes 16 / 17:** materials and details PASS; soft lines PASS (sag, sweep, rolled verges, valleys and corners).
- **Notes 18 / 19:** FAIL. There is no eyebrow and no rounded hips or crown, and the only round element is hidden at the back gable from the main views.

**Add-on reusability:**
- **`roof_valley`:** reusable (any yaw, L / T, dormer-into-host, auto corner roll, ridge cut, foot_back). Thatch only; not yet on a rounded roof.
- **`chimney`:** reusable (gable `wall_abutment` and through-slope ring, proven in r2; pot default). PASS.
- **`GabledDormer` / `gabled_dormer`:** reusable, and now scales its own hood section from the dormer (`roll=0.15 * hw`). PASS for shingle-free hosts; thatch only.

**Strengths:**
- Honest, measured reporting, including the notes not applied and why.
- The right generic fixes: the roll section as a kit option rather than a recipe hack, and `foot_back` plus per-station `bury` / `bury_dir`.
- x01 / x02 / x17 / x23 / x30 are essentially clean.
- Interior volumes unchanged and closed.
- The triangle count is flat (+68 tris).

**Must-fix (the extension round; notes 18 / 19 FIRST):**
1. **Note 19, the rounded "loaf" roof, as a kit option** (`GableRoof(hips="round", crown=...)` or a `loaf_roof` component; thatch first; old defaults; hash rule if a default changes):
   - **Main wing:** a round hip (half-cone, oversailing the corners) at both free ends, W and E.
   - **Cross wing:** a round hip at its free S end; no hip at the joined end.
   - **Section and finish:** a softly convex cross-section with a rolled ridge; keep the sag and swept eaves.
   - **Courses:** the thatch courses run round the hips continuously, with the eave roll following the oval in plan.
   - **Proof:** the hero, front, side and back views; L02 (no flat gable ends); interior rays and i01-i08 red twins clean.
2. **`roof_valley` on the rounded roofs:**
   - the valley and the internal-corner roll work against the convex crown;
   - the wing's ridge runs into the main slope under the arch.

   Proof: x07 / x17 / x08 / x22 / x23 void twins and the i01-i03 red twins.
3. **Note 18, a thatch eyebrow** (`eyebrow(profile="arch", respace=True)` extended to `linear_roof(covering="thatch")`, defaults unchanged):
   - **Placement:** on the main roof's **back (north) slope**, which is a blank 10 m face in the back view. A second one on the main front slope's west half is optional.
   - **Form:** the thatch courses roll over one continuous arch, with the eave roll as a rolled lip over the kit window in a small rough-boarded front. It should be as smooth as the harbour house's round-8 eyelid.
   - **Proof:** sealed (interior red twin from the main attic toward it), plus one void twin of the lip ends.
4. **Chimney:**
   - Move it through the roof: a ridge or slope stack via the proven `_ring_abutment`, or rising through the E round hip.
   - Keep it short and chunky (about 0.8-1.2 m over the ridge), with the round pot, flashed into the curved thatch by the ring.
   - It should then read from the front views.
   - Proof: the seal probe and one void twin of the ring.
5. **Carry-over seams** (on whatever geometry survives the re-roof):
   - **(a) The wing ridge under the arch** (x08 / x24): shorten the wing skirt to end before the comb gap, or drop the comb units under the whole skirt. Target x08 < 500, with no dark wedge in clay.
   - **(b) The corner roll:** blend its ends into the straight rolls without the flat sleeve bands (x13 / x22 at eye level), and close the knot and crack where the valley-foot tuck enters it (x27).
   - **(c) Housekeeping:** delete the empty `C:\round_03` folders (ask for permission if blocked) and merge CHANGELOG 1.19.

**Nice-to-have:**
- One continuous dormer hood arch over the apex (x26 notch).
- Drop the dormer finial (fewer spikes).
- Bend the lead aprons to the stack.
- Taper the dormer foot roll under the valley skirt (x03).
- Later: a shingle valley and dormer, so the add-ons serve the shingle-roofed designs.

## PRODUCER NOTE (2026-10-18, session 2, 01:45): round 3 graded 7.9 (notes 18 / 19 not yet applied); client EXTENDS the cottage by up to 2 rounds

Client: "Extend by up to 2 rounds" for the rounded 'oval' roofs (note 19) and the thatch eyebrow (note 18). **Round 4 does the rounded roof and the eyebrow FIRST**, keeping round 3's seam fixes; then grade and audit; round 5 only if needed. The run paused at a usage limit (it resets at 3 am New York time), and continues after it.

## v7_cottage round 4 — builder entry

I re-read this log before starting and again before writing. The latest entry is the PRODUCER NOTE of 01:45 (round 4 does producer notes 19 and 18 first, keeping the round-3 seam work); nothing came after it. **Both client rules are applied: the cottage now has rounded "loaf" roofs (no gable end anywhere) and a thatch eyebrow dormer.** The gabled dormer is kept.

**What was built.** `buildings/variants/v7_cottage/build_v7_cottage.py` -> `v7_cottage.blend` + `decal_anchors.json` (recentred by (+0.001, +3.194)).
- **Main wing** 11.0 x 5.5 m (lengthened from 10 m so the wing's valleys and the dormer stay on the straight slopes) under a thatch loaf: `GableRoof(hips="both", crown=0.45)`, pitch 47 deg.
  - A **round hip (half-cone) at both ends**: the eave runs round the house as one oval, oversailing the corners (the nose is 1.9 m past the end walls, the corners 0.15 m inside the lip).
  - A **softly convex section** that eases into the rolled ridge. The ridge roll rounds over each hip apex as a dome.
  - Sag, swept eaves and the wave are kept. There is no comb, no verge and no finial: no gable is left.
- **Cross wing** 4.8 x 5.25 m: its own loaf, `hips=("lo",)`, crown 0.35, pitch 44 deg. A round hip at its free S end; **no hip at the joined end**, which runs into the main slope in the existing soft rolled valley each side and over its ridge (`roof_valley`, with the round-3 internal-corner rolls).
- **Thatch eyebrow** on the main back (N) slope, as the director placed it (x -0.8): `eyebrow(grid="thatch", profile="arch", respace=True, width 2.5, lift 0.90)`.
  - The courses roll over **one continuous arch**.
  - The eave roll runs over it as a **rolled lip** (the village D section x 0.75, its ends sinking into the thatch).
  - Under it is a rough board-and-batten front with the kit window (0.60 x 0.36).
- **Gabled dormer** kept on the front slope over the door (x -3.1), unchanged kit code.
- **Chimney** now **rises through the E round hip** (the client's "rising against an end wall through the round hip").
  - It is the same broad battered base against the end wall, with the rounded weathering at 3.0 m (now under the hip's soffit) and the round stack.
  - The hip surrounds it, so the proven `_ring_abutment` ring of lime flaunching seals it (fillet widened, see the kit table). Head 7.03 m, about 0.8 m over the ridge, with the round pot (crown 7.64 m).
  - It reads in the hero / front / side views.
- **Hip-end gablets.** Under each round hip the end wall used to rise into the deep, dark oversail as a stone gablet that no review viewpoint sees (est_hidden 17.8 % on the first final build). The rubble now stops at wall_z - 0.30 there, and a rough board-and-batten gablet (`timber_walls.path_timber_wall`, the village boards) closes the attic up to the deck: at the W end, at the E end either side of the stack, and at the wing's S end. This is "rough timber where it suits" (the Brief); it is a recipe choice, not kit code.

**Kit** (`kit/changes/v7_cottage.md` "Round 4"; a CHANGELOG entry "1.19 / 1.20" is added for the producer's merge):
- **Round hip** (`GableRoof(hips=, hip_inset=, hip_k=, hip_seam=)`). It is a bend of the roof's own frame: the slope coordinates run on past each hip centre by a quarter arc, and `to_world` / `to_local` / `under_z_world` fold that run round the hip.
  - Because of this, **every existing part and add-on follows the hip with no per-part code**: deck, courses, eave roll, ridge roll, rafters, keep_out / top_world, `roof_valley`, `GabledDormer`, the chimney ring, the clips and `roofs_top_fn`.
  - Hip-specific pieces: one eave roll sweep round the whole oval (`_hip_eave_roll`; the main roof's seam is under the cross wing); radial rafter tails (`_hip_rafters`); the course irregularity fades at each hip's nose line (no step where the slopes meet); a coarser deck (0.6 m x 9 rows; it is backing).
- **Soft crown** (`GableRoof(crown=)`): a term of the existing warp field, flat over the ridge roll.
- **Thatch eyebrow** (`eyebrow(grid="thatch")`, plus `_brow_rolls`): per-course lift, the course under the front stops at the deck front, respace, and the lip roll. The 1.13-1.15 front, window, deck tear and opening are reused unchanged.
- **roof_addons:** `chimney(abut=dict(ring_fillet=...))` (the ring fillet's keywords and step) and `straight_span(...)` (the recipe keeps the composite moss anchors off the folded hips; `composite.py`, which is not this track's file, is untouched).

**Hash rule: not triggered, not run.** Every existing-module change is behind a new parameter whose default keeps the old statements (`HIPS is None`, `crown == 0`, `grid == "shingle"`; `_layered_courses` evaluates the identical expressions when there is no hip and no thatch eyebrow). No other building uses the new options.

**Stats** (`round_04/stats.json`; 6 views, 24 samples):
- 413,548 triangles (cap 1,000,000);
- **est_hidden 13.0 %** (17.8 % before the gablets and the coarser deck);
- 9 palette slots;
- Mask missing: none;
- 76 decal anchors;
- 64 objects;
- bbox 15.3 x 13.4 x 7.7 m.

Guards: door eave lip 2.417 m (PASS); seal probe on the stack ring: 0 leaks in 58,819 rays. The first ring fillet let 1 of 72,364 rays through; it was widened.

**Sealing (interior red twins, final blend, `builder_extra/b_render_r04_final.log`).**
- i01 79,038 / i02 73,944 / i03 6,703 / i04 987 / i07 7 / i08 0 red. As in rounds 1-3, the red is the open floor below the wall heads.
- New volumes:
  - i06 attic to the E hip and stack: 10 px;
  - **i09 attic to the W hip: only the floor below**;
  - **i10 attic to the eyebrow: 0**;
  - i11 wing attic to the S hip: 200 px (floor).

**Void yellow (final blend):**

| shot | yellow | note |
|---|---|---|
| x17 E valley foot | 22 | r3: 113 |
| x07 W valley foot | 619 | r3: 498 |
| x06 E corner soffit | 1,006 | r3: 1,660 |
| x22 E corner at eye level | 750 | r3: 2,799 |
| x08 wing ridge under the arch | 1,607 | r3: 1,586; not improved |
| x24 wing ridge arch, side | 717 | r3: 616 |
| x04 dormer, mid distance | 114 | |
| x19 dormer hood | 64 | |
| h01 E hip and chimney | 443 | |
| h02 W hip | 371 | |
| h03 W hip soffit | 20 | |
| h04 W hip apex dome | 0 | |
| h05 wing S hip | 33 | |
| h06 wing S hip soffit | 390 | |
| c01 chimney ring | 1 | |
| c02 chimney ring | 409 | |
| c03 chimney base under the hip | 115 | |
| e01 eyebrow, eye level | 1,599 | a stone back face at the frame's bottom edge |
| e02 / e03 / e04 eyebrow | 0 / 2 / 0 | |
| **x05 W inside-corner soffit** | **34,917** | **regression**, see the known gaps |

**Renders:**
- `round_04/preview/`: hero / side / back of the first FAST build.
- `round_04/`: the six views.
- `round_04/builder_extra/`: `b_render_r04.py`, copied from the r03 script with the round-4 plan; shift from the env `COTT_SHIFT`.
  - The r03 junction shots, plus h01-h06 (hips), c01-c03 (chimney ring), e01-e04 (eyebrow) and i09-i11 (new volumes).
  - `fast/` and `fast2/`: the FAST iterations.
- Numeric bend check: `buildings/variants/v7_cottage/scratch/hip_check.py`. Round trip 3e-13; nose seams coincide; apex spread 0.

**Round-3 carry-over seams:**
- **(a) Wing ridge under the arch:** the comb is gone (the loaf has none), but x08 is unchanged at 1,607. Not fixed.
- **(b) Corner-roll sleeve bands:** not worked; still visible at eye level in x13.
- **(c) Housekeeping:** the CHANGELOG entry is added. Removing the empty `C:\round_03` folders was **blocked by the harness** ("protected from removal"); they need the client's or producer's permission, or a manual delete.

**Known gaps:**
- **x05 regression:** 34,917 yellow on the final blend against 632 on the FAST (uncut) blend. The hidden-geometry cull removed faces near the W inside corner (by the front door, next to the small front window) that this low, close eye-level camera sees; the cull's viewpoints miss that pocket under the deep eave. x13 at eye level by the door reads clean in clay. To fix, keep those wall / window objects out of the cull near the corner, or add a viewpoint there.
- **Hip apex:** the ridge roll's seated flank shows a thin collar and notch where it revolves into the apex dome (h04).
- **Eyebrow:** the courses above the arch show sharp folds on the fade's upper flanks (the vertical shear of the warp; `tilt` exists for shingles only). There is a small dark slot at the lip roll's E foot (e02).
- **Wing hip from the front:** seen end-on in the front view, the S hip reads as a cone. It is low and sits under the main ridge, but the director should judge it against "no conical turret".
- **Coverage:** round hips are proven on thatch only (shingle not built), and the valley and dormer are thatch only.
- **Not done (nice-to-haves):** the dormer finial (kept), bent lead aprons, the dormer foot roll.

I stopped at the time budget after the second final build and the review renders.
## v7_cottage round 4 — score 8.0/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing, no surface-detail requests. Binding: producer notes 1-19, the CLIENT DIRECTIONS of 2026-10-17 and of 2026-10-18 00:10 / 00:20, and the PRODUCER NOTES of 23:12, 00:11 and 01:45. I re-read this log before starting and again before writing: the latest entries are the PRODUCER NOTE of 01:45 (round 4 does notes 19 and 18 first; up to 2 extension rounds) and the builder's round-4 entry. Nothing came after them. **The 8.1 cap of the 00:11 / 00:20 notes no longer applies:** there is no /\ gable on the cottage's walls and there is a thatch eyebrow.

**Reviewed:**
- the recipe `build_v7_cottage.py` (a short declarative recipe; the hip-end gablets are recipe pieces built from `path_timber_wall`);
- the new kit code in `linear_roof.py`: `GableRoof(hips=, hip_inset=, hip_k=, hip_seam=, crown=)`, `_bend` / `_unbend`, `to_world` / `to_local` / `under_z_world`, `warp_z` / `_hip_warp` / `_crown_dz`, `_resolve_brow(grid="thatch")`; and `kit/changes/v7_cottage.md` "Round 4". The defaults keep the old statements (`HIPS is None`, `crown == 0`, `grid == "shingle"`);
- the six `round_04` views, the preview, `stats.json`, `render_review.log`, and every builder close-up and twin in `builder_extra/` (including `fast/` and `fast2/`).

**Director checks** (`renders/variants/v7_cottage/round_04/director_extra/`; counts in `dir_counts_r04.txt`):
- `dir_render_r04.py` (copied from the builder's r04 script) re-runs every builder shot on the final blend. My counts equal the builder's on every shot.
- It adds 27 director shots: di05 and di12-di17 (interior volumes), and d01-d20 (every add-on junction on the loaf roofs).
- **The script now makes its paths absolute.** Opening the blend changes the base for relative paths, which is how the `C:\round_03` strays were made. My first pass wrote to `C:\renders\variants\...`; I moved the files in and deleted that folder.
- `dir_lineup_r04.py` (copied from r03) renders the note-16 line-up of v3, v5, v6, **v7** and the roundhut (`lineup/L01-L03`, `T*`).

**Numbers** (all within the limits):
- 413,548 tris (cap 1,000,000);
- hidden 13.0 %;
- 9 palette slots;
- no mesh missing `Mask`;
- door eave lip 2.417 m: PASS;
- 64 objects;
- 76 decal anchors.

**Sealing (interior volumes): PASS, with one pinhole.**
- **The builder's shots, re-run:** i01 79,038, i02 73,944, i03 6,703, i04 987, i07 7, i08 0, i09 11,704, i10 0, i11 200. All of this red is the open floor below the wall heads.
- **i06: 10 px of real daylight.** It is NOT floor: a pinhole at the stack / S hip-end gablet / wall-head joint, at about z 2.6-2.9 (`i06_attic_to_E_hip_chimney_red.png`, x 535, y 595).
- **Director interiors:** di05 (dormer from the attic) 0, di13 (W gablet low) 0, di15 (the eyebrow from the side) 0, di16 (the ridge to the E dome and the stack) 0, di17 (the wing-ridge join from inside) 0.
- di12 and di14 are void as probes: the camera sits inside a solid, so the clay frame is black.
- **Stack ring:** the builder's ray probe reports 0 leaks in 58,819 rays.

**Void yellow, director shots (final blend):**

| shot | yellow | note |
|---|---|---|
| d01 ridge from N | 0 | but the wing ridge roll stands proud above the main ridge (clay) |
| d02 wing ridge join, above | 227 | ragged arch skirt |
| d03 W corner roll, eye level close | **21,170** | cull hole + sleeve band |
| d04 W inside corner, standing by the door | **59,813** | **cull hole in the stone** |
| d05 / d06 dormer back W / E | 0 / 13 | frilled ridge-cut skirt in d06 clay |
| d07 dormer apex | 119 | |
| d08 dormer cheek foot E | 868 | |
| d09 eyebrow lip W foot | 0 | |
| d10 chimney pot head | 2,531 | the pot's inner face (open flue, expected) |
| d11 E hip nose soffit | 71 | radial rafter tails crowd at the corner |
| d12 wing S hip, SE wide | 478 | reads as a hip, not a turret |
| d13 / d14 corner roll above E / W | 28 / 335 | |
| d15 W hip apex dome, N | 573 | collar notch |
| d16 E hip apex by the stack | 1,251 | collar notch |
| d17 eave seam under the wing | 0 | the oval's seam is hidden |
| d18 W valley foot, eye level | **17,802** | **cull hole in the stone, at eye level** |
| d19 W hip gablet, eye level | 70 | |
| d20 NE hip corner, eye level | 307 | |

| # | axis | score | why |
|---|---|---|---|
| 1 | Silhouette and massing | **8.6** | **Notes 18 and 19 are delivered and read at every scale.** The eave runs round the house as one oval over the rubble rectangle, oversailing the corners. The section is softly convex into a rolled ridge, with sag and swept eaves kept. There is no flat gable anywhere (hero, front, side, back, aerial, x14 / x15, L01 / L02). The eyebrow is a clear single arch on the 11 m back slope, which was blank in r3 (back). The round stack rising through the E hip now reads from the front (front, hero, side). In the line-up, v7 has moved from the most angular roofline to an unmistakable soft thatched loaf, kin to the roundhut cone and to v3's round end. From the SE (d12) the wing reads as a hipped loaf; end-on from the front it reads as a half-cone. That is the honest form of a round hip, not a "conical turret": it is low, under the main ridge, and joined by a valley. **Against:** from the back (back.png, d01), the wing's ridge roll end stands proud above the main ridge as a ringed knob, a small but real silhouette fault. |
| 2 | Proportion and actor scale | **8.4** | It is right against the 1.8 m figure: the 1.95 m door under a 2.42 m eave lip, small deep windows, and the 1.3 m dormer. The stack is short and chunky, about 0.8 m over the ridge, with the round pot (d10). The eyebrow window (0.60 x 0.36) is small but in scale for an attic light. The 1.9 m nose oversail is generous but believable for a loaf thatch. |
| 3 | Construction logic | **8.2** | The roof is carried believably. Radial rafter tails run under each hip. Under the oversail, a rough board-and-batten hip-end gablet stands on the rubble (d19, h06, c03): a real vernacular detail, and it cut the hidden share. The stack is sealed into the curved thatch by a continuous lime ring. **Against:** the wing ridge roll visibly runs through the main ridge (d01). The radial rafter tails bunch into a stacked cluster at each hip corner (d11, h06, c03). |
| 4 | Seams and junctions | **7.7** | **Clean:** the oval eave seam under the wing (d17: 0), the eyebrow (e02 / e04 / d09: 0, e03: 2), the chimney ring (c01: 1), the E valley foot (x17: 22), the dormer back (d05 / d06: 0 / 13), and the hip soffits (h03: 20, h05: 33). **Not closed:** (a) **holes from the hidden-geometry cull at the W inside corner by the front door**, seen from a standing eye point and from the approach to the valley foot (d04: 59,813; x05: 34,917; d03: 21,170; d18: 17,802 yellow). With single-sided UE materials these are holes into the wall at the entrance, which note 4 protects. (b) **The wing ridge under the arch:** the dark pocket and flat cut end (x08: 1,607; x24: 717) and the knob proud of the main ridge (d01). (c) **The corner-roll sleeve bands**, still plain at eye level (x13, x22, d03, d18). (d) The **hip apex collar / notch** where the ridge roll revolves into the dome (h04, d15, d16). (e) Smaller items: the i06 daylight pinhole; frilled ridge-cut skirts (d02, d06); faceted folds on the eyebrow's upper courses at close range (e02 / e04). |
| 5 | Distinctness and reuse | **8.6** | **Same village (note 16): PASS.** It uses the shared palette and the village rubble, the barn thatch courses and D-section rolls, the kit window and board-and-batten, the v3 / v5 lime flaunching and lead, the turned finial, and the round battered stack and pot. **Notes 17 / 18 / 19: PASS**, the cottage's round and soft language: an oval loaf, a convex crown, a thatch eyebrow, and a round stack through a round hip. **Reuse:** the round hip is the best kind of kit work. It is a bend of the roof's own frame (`_bend` / `_unbend` in `to_world` / `to_local` / `under_z_world`), so the deck, courses, rolls, rafters, valley, dormer, chimney ring, clips and `roofs_top_fn` all follow it with no per-part code. `crown=` also works on plain gables. `eyebrow(grid="thatch")` reuses the 1.13-1.15 front, window and deck tear. It is distinct from every hero and variant: the only loaf-roofed building. **Against:** shingle round hips have not been built (note 19 says "thatch first, shingle if feasible"). The valley and dormer remain thatch only. |
| 6 | Technical compliance | **8.0** | Every number is within its limit, the build is seeded and deterministic, and the hash rule is not triggered (the defaults keep the old code paths, verified in `linear_roof.py` at lines 168-196 and 305-365). **Against:** the hidden-geometry cull deletes faces that a standing visitor at the entrance sees (point 4a). That is a correctness failure of the note-6 cull, even though the 13.0 % figure complies. The i06 pinhole is daylight into the attic. The empty `C:\round_03` folders remain outside the project. CHANGELOG 1.19 / 1.20 are still waiting for the producer's merge. |

**Overall 8.0 / 10: REVISE (extension round 5 of the 2 the client allowed).**
- This is the round the cottage needed: both client rules are met, as kit options with old defaults. The roof form is now unmistakably this village's, and the kit gained a genuinely general round hip.
- It does not pass on the seam axis. A cull hole in the stone at the front-door inside corner (eye level, note 4) and the wing ridge roll poking through the main ridge are real defects, and so are the carried-over sleeve bands. All three are local fixes; none needs another redesign.

**Village theme (notes 16-19):**
- **Note 16:** PASS.
- **Note 17:** PASS. The oval eave, the convex crown, the rolled ridge and dome, the swept eaves, the rolled valleys and the round stack.
- **Note 18:** PASS. One continuous thatch arch over a kit window on the back slope; sealed (i10, di15: 0).
- **Note 19:** PASS. Round hips at every free end, no hip at the joined end, a soft crown, no flat gable. On the end-on wing hip: judged a round hip, not a turret (d12, L02).

**Add-on reusability:**
- **`roof_valley`:** reusable, and now proven against a crowned, hipped host with no new code (the bend carries it). Thatch only. The wing-ridge junction under the arch is still the weak point.
- **`chimney`:** reusable. Proven at a gable abutment (r2), through a slope (r2), and now **through a round hip** with the ring (0 / 58,819 leaks). PASS.
- **`GabledDormer` / `gabled_dormer`:** reusable, and proven on the crowned roof unchanged (x19, d05-d08). Thatch only. PASS.
- **New: `GableRoof(hips=, crown=)` and `eyebrow(grid="thatch")`:** reusable kit options with old defaults. PASS (thatch-proven).

**Strengths:**
- The client's form, built as a frame bend that every existing part and add-on inherits: the right abstraction, with a numeric round-trip check (`hip_check.py`, 3e-13).
- A clean eyebrow.
- A one-sweep oval eave roll with its seam hidden under the wing.
- The stack through the hip sealed at 0 leaks.
- Hidden geometry cut from 17.8 % to 13.0 % with a believable boarded gablet, not by deleting what is seen. The one exception is the W corner, which is must-fix 1.
- Triangles −25 k against r3.
- Honest reporting of the x05 regression and of the open seams.

**Must-fix (round 5; local fixes only, no redesign):**
1. **The cull holes at the W inside corner** (d04, x05, d03, d18):
   - Add eye-level viewpoints round both inside corners and the valley feet to `composite_hidden_cull` (a kit option, e.g. `extra_views=`), or keep the corner wall / window objects out of the cull within about 1.5 m of the re-entrant corner.
   - Target: d04 / x05 / d03 / d18 under 1,500 yellow each, with hidden still under 15 %.
2. **The wing ridge into the main roof** (d01, x08, x24, back.png):
   - End the wing's ridge roll (and its spars) on the main slope, below the main ridge roll, so nothing stands proud of the main ridge from the north.
   - Close the dark pocket and the flat cut end under the arch: shorten the arch skirt to end before the ridge-roll end, or bury the roll end under the skirt.
   - Target: no knob in back.png or d01; x08 under 500 with no dark wedge in clay.
3. **The corner-roll sleeve bands** (x13, x22, d03, d18):
   - Blend the swept internal-corner roll into the straight eave rolls with a tangent-continuous section (a shared section, or a 0.3-0.4 m blend overlap), not the flat-faced sleeves.
   - Proof: x13 and d03 in clay.
4. **The i06 daylight pinhole** at the stack / S hip-end gablet / wall-head joint: run the gablet into the stack's base clip, or extend its z0 below Z_CAP. Target: i06 0 red.
5. **The hip apex collar / notch** (h04, d15, d16): fade the ridge roll's seat flank before the dome, or revolve the seated section too, so the dome reads as one rounded cap.
6. **Housekeeping:**
   - Delete the empty `C:\round_03\builder_extra\fast` and `C:\round_03` (this needs the client's or producer's permission; the harness blocks it).
   - Merge CHANGELOG 1.19 / 1.20.
   - Make every render script's output path absolute before `open_mainfile` (as in `dir_render_r04.py`).

**Nice-to-have:**
- Thin the radial rafter tails at the hip corners (d11 / h06 / c03).
- Smooth the eyebrow's upper-course folds (a per-course shear limit, like the shingle `tilt`).
- Trim the frilled ridge-cut skirts (d02 / d06).
- Drop the dormer finial, bend the lead aprons to the stack, and taper the dormer foot roll.
- Later: shingle round hips, and a shingle valley and dormer.
