# a1_longhouse_addons: the WALL add-ons (lean-to, porch), proved on the longhouse (plan step 4)

## CLIENT DIRECTION (2026-10-17, session 2)

- Plan step 4 (client "Yes proceed"): the add-ons. The client said: "Move forward with the quick fix, the housekeeping, and the add ons. Make sure the add ons stick with the theme of the village".
- **This track builds the WALL add-ons:**
  - a **lean-to** (a mono-pitch roof against any wall);
  - a **porch / canopy** over any door.
- The other track (log_variant_v7_cottage.md) builds the valley, chimney and dormer at the same time.
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

**The host:** prove both add-ons on the **v3 longhouse**, without touching its accepted files.
- Write a demo recipe uildings/addon_demos/a1_longhouse_addons/build_a1_longhouse_addons.py. It re-uses v3's recipe (import its parameters / steps, or a thin copy that only adds steps) and adds:
  - one **lean-to** on the back long wall of the longhouse body;
  - one **porch** over the longhouse's front door.
- Output: 1_longhouse_addons.blend + decal_anchors.json in that folder.
- **Never modify** uildings/variants/v3_longhouse_roundend/ or any accepted file.

**The new kit add-ons:**
1. **lean_to:** a mono-pitch soft roof against any wall run.
   - It follows the host covering (thatch or shingle), with the soft options: sag, a swept eave, a rolled verge.
   - It sits on a low rubble or rough-boarded wall, or on posts.
   - It is sealed into the host wall (an abutment flashing / mortar fillet, re-using the wall_abutment pieces where they fit) and kept below the host eave.
   - It is a reusable component in a NEW module (e.g. components/lean_to.py).
2. **porch:** a small canopy or porch over any door.
   - Curved timber brackets or a small cruck-arched frame (re-use the cruck curves).
   - A soft swept roof in the host covering.
   - Sealed to the wall, with door clearance >= 2.30 m.
   - A new module (e.g. components/porch.py).

**File ownership while both tracks run:** this track must NOT edit linear_roof.py or oof_junction.py, because the other track owns them. Subclass, wrap or call them from the new modules. If something truly needs a change there, record it in the builder entry as a request for later and work around it.
## PRODUCER NOTE (2026-10-17, session 2, 23:10): early-preview feedback, apply in round 1 (the village theme)

From `round_01/preview/` (the first FAST build):
1. **Keep the eave lift over the front door.** The thatch waving up over the porch is exactly on theme.
2. **The porch hood is not yet on theme.** It is a flat, ruler-straight shingle canopy on square brackets under soft thatch.
   - Make it **soft**: a swept / bell-cast or gently arched hood (the `GableRoof` soft options, or a curved hood profile), in the host's covering or the village shingle with a rolled or flared edge.
   - Carry it on **curved timber brackets** (the `cruck` curves) or a small cruck-arched frame.
   - Seat it sealed into the wall.
   - Door clearance >= 2.30 m.
3. **The lean-to must read as a lean-to:** a real mono-pitch shed (a store or byre) against the back long wall. About 4-6 m along the wall and 2-3 m deep, low walls (rubble or rough boarding) or posts, its soft roof dying into the host wall under the host eave, with a door or opening of its own. It must not be a small canopy.