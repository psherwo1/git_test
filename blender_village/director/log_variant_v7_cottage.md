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