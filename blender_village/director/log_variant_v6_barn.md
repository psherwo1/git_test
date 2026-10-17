# v6_barn: the village barn (plan step 3, after the harbour house)

## CLIENT DIRECTION (2026-10-17, session 2)

- Plan step 3 (client "Yes proceed"): the timber / rectangular / waterfront family through the harbour house, **then a boathouse or barn**. The client chose: "Let's do the barn".
- Team method as before: one builder; the Art Director grades every round on the note-12 modularity rubric (pass mark 8.2); an independent audit must uphold a pass. **At most 3 rounds** (time matters: the client said "do not spend time that can be avoided, and the earlier a correct result is obtained, the better").
- Binding: producer notes 1-17 in `director/art_bible.md`, in particular:
  - **note 16:** the same builders, techniques and materials as the rest of the village;
  - **note 17:** round structures and soft, organic lines are the village's signature.

  The client's reuse mandate also stands: "Reuse as many existing modules as possible".

## Brief

A working village barn for hay, carts and animals, standing on ordinary ground (Z = 0).
- **Plan:** rectangular, about 12-14 m x 6.5-7.5 m.
- **Walls:** the village rubble as a plinth or the lower walls (`path_stone_wall`), with rough, old timber boarding above (`path_timber_wall(rough=True)`), or rubble gable ends with boarded long walls.
- **Openings:**
  - large double **cart doors** in a long side (the timber host's large-door head rules);
  - a **hayloft door** high in a gable, with a hoist beam;
  - a man door;
  - a few small openings or slits.
- **Roof:** the village's soft, slumped roof (`GableRoof` ridge sag, eave sweep, verge flare), steep and dominant.
  - **Thatch is preferred** for variety, since the roundhut and the longhouse are thatched and the harbour house is shingled, if `linear_roof`'s thatch covering takes the soft options cleanly. Otherwise use the village shingle.
  - Village finials (ball or turned) at the gables.
- **Round element (note 17):** at least one round element that is integral to the composition.
  - It must **not** repeat the "rectangular block + round stone tower at one corner" formula of v3 and v5.
  - Options, builder's choice, with the reason recorded:
    1. a half-round (apsidal) end under a half-cone or round-hipped roof;
    2. a round stone granary or drying kiln built into the middle of a long side, under its own cone, breaking the eave;
    3. a round-arched cart entrance through a cruck frame, as the barn's signature (`cruck_frame` on dry land).
  - The director checks distinctness against v3 and v5 at thumbnail size.
- **Optional, if cheap:** an eyebrow over the hayloft door (`GableRoof(eyebrows=[eyebrow(profile="arch", respace=True)])`). It is shingle-only today.

**Start from the family proof:** `buildings/variants/v5_harbour_house/scratch/barn_smoke/build_barn_smoke.py` (30 lines). It is a post-and-plank barn on a rubble plinth with clamp / trim boat doors, shuttered windows, and a soft shingle roof with finials.

**Kit polish to fold in, ONLY where the barn uses the part** (kit changes, defaults unchanged), from the harbour-house grades:
- the swept eave / verge corners (the `linear_roof verge="board"` rafter tail below the bargeboard foot);
- the dark slot along a swept eave;
- the ridge-comb slits;
- the eyebrow's tower-side shoulder and window margin, if an eyebrow is built.

Everything else on that list waits.
