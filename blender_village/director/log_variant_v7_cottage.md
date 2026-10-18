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
