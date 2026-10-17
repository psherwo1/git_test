# v5_harbour_house: the timber harbour house (approved building 3)

## CLIENT DIRECTION (2026-10-17, session 2)

- Approved building 3 (client-confirmed 2026-10-16): "a timber harbour house or boathouse on the waterfront (ref2 / ref3 right side)".
- Plan step 3 (client "Yes proceed"): the **timber, rectangular and waterfront kit family**, proved on the harbour house first, then a boathouse or barn.
- The client chose how to run it: "Workflow, up to 5 rounds (Recommended)": one builder, the Art Director grading every round on the note-12 modularity rubric, pass mark 8.2, an independent audit must uphold a pass, at most 5 rounds (build plus 4 fix rounds).
- Binding: producer notes 1-15 in `director/art_bible.md` (note 12 modularity over detail, note 13 no LED volume / hobby production / high polish, note 14 the kit is a toolbox for 12-15 curated designs, note 15 at most 1,000,000 triangles).

## Brief

A two-storey timber harbour house standing at the water's edge, in the spirit of the waterfront houses on the right of ref2 and ref3:
- a rectangular plan, roughly 8-10 m x 5-6 m;
- a low rubble plinth on the landward side, and on the water side a plank deck or short jetty on timber piles;
- timber walls: plank or weatherboard cladding, or a post-and-beam frame with plank infill;
- a jettied upper floor (it oversails the ground floor on at least one side, on joist ends and a bressummer);
- a steep shingle gable roof, the gables facing the water and the land;
- a large loading or boat door at the water side, an ordinary door and a few small shuttered windows.

It must read as a timber waterfront building, not as a stone building clad in planks.

**Datum.** The quay or landward ground is Z = 0. The piles run down past Z = 0 to the bed at about Z = -2.5 m, with the deck about 0.3-0.6 m above Z = 0. Record the datum in the builder entry so the UE placement can use it.

**The kit family is the deliverable as much as the house is.** The new modules must be reusable: the next design, a boathouse or barn, should be a short recipe. At least these modules:
- `path_timber_wall` along any polyline (post-and-plank, weatherboard or clapboard), taking openings from the shared opening spec;
- a floor stack with a jettied upper storey;
- piles or stilts with a plank deck or jetty;
- a large boat or barn door.

## CLIENT DIRECTION (2026-10-17, session 2): same builders, same techniques, same materials (producer note 16)

Client's words: "Remember that the new designs should still give off the feeling that they were built by the same people with the same techniques and materials of the other buildings".

Read producer note 16 at the end of `director/art_bible.md` in full; it is binding for this building from round 1.
- **Builder:** the harbour house must share the existing buildings' materials and details: the same palette, the rubble plinth and footing details, the timber sections, the shingle sizes and courses, the door and window frames, thresholds and shutters, iron hardware and lead flashing, eave rolls, verges and ridge, finials, and the same age and moss (`age_defaults`). Reuse the kit's existing detail modules for these rather than writing new ones; the new timber family supplies new FORMS, not a new style. If round 1 is already built, check it against this and record in your builder entry what you reused and what still differs.
- **Art Director and auditor:** grade "reads as the same village" under distinctness and reuse. Put it next to the keep, the roundhut and the longhouse at the same scale, and make one side-by-side or line-up render. Any material or detail found nowhere else in the village is a must-fix.