## v3_longhouse_roundend round 8 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). This is the client-approved redesign:
the round end is raised so that the thatch roof runs into the drum's wall below the cone's eave. Geometry only. No
ground dressing is scored (note 10), and no surface detail is asked for (note 12). There is no builder entry (the
fixer was stopped before writing it), so every finding below comes from the geometry.

**Reviewed:**
- The six review renders in `round_08/` against `round_06/`, plus `stats.json` and `decal_anchors_r8.json`.
- The recipe `redesign_r8_wip/build_v3_longhouse_roundend_r8.py`, the Round 8 entry in
  `kit/changes/v3_longhouse_roundend.md`, and `roof_junction.wall_abutment` / `round_body_face` /
  `LINEAR_ROOF_PARTS`.
- 21 director close-ups, 17 of them with red see-through twins, in `round_08/director_extra/` (`dir_render8.py`,
  `run8.log`). The cameras are placed relative to the drum centre, measured at (4.72, -0.02):
  - j01-j08: both eave ends, at eye level and in tele, and look-ups at the soffit;
  - j09-j16: both flaunching slopes, the ridge into the drum, top-down, and the cone over the roof;
  - j17-j21: the cone eave, the drum next to a 1.8 m figure, and the upper windows.
- A probe on the delivered file:
  - per-object bounding boxes;
  - a floating-island probe on the eave roll, the ridge, the comb and the abutment, measuring each island's gap to
    all other objects.

**Compliance:**
- 617,342 tris, under the 1 M cap (note 15). This is up 25 % on round 6, mostly from the taller drum: 97k stone polygons.
- est_hidden 9.2 %, 10 palette slots, nothing in `mask_attribute_missing`.
- 89 decal anchors, 43 of them above 3 m, with a plausible mix.
- `wall_abutment` has 0 floating islands, and so does the eave roll.
- The probe flagged ridge-strap and comb islands as more than 1 cm from other objects. These are false positives: they
  sit on their own object (the ridge roll and the comb), and the probe skips a piece's own object.
- **Not verified:** determinism (I made no second build) and the six-building hash rule. The Round 8 kit entry points
  to "results in the round-8 builder entry", and that entry does not exist.

**The redesigned junction (gable roof abutting a round wall):**
- **Gone:** the eave-crossing junction behind every rejection since round 3 no longer exists. The two eaves never meet.
- **Trimming is clean.** The deck, rafters, courses, eave rolls, ridge roll and comb all stop inside the stone. I found
  no cut ends, see-through or slots (j09-j14).
- **No see-through.** Every red twin is closed (for example j16_red, j11_red, j09_red).
- **The lime flaunching follows the true intersection curve eave to eave and over the ridge** (j09, j10, j11, j13,
  j14). It reads as built work at mid-shot distance.
- It is a real kit module that reuses the compound family's `clip_at_tower`, `trace_roof_on_tower`, `ride_fillet` and
  `wall_end_apron`. It also guards itself: it raises if the two eaves would cross.

**Key defects (none blocking):**
1. **The eave-end lead aprons read as stuck-on tabs.**
   - **Where:** each apron is a flat rectangular plate, about 0.18 x 0.28 m, standing a few cm proud of the stone
     beside the eave-roll nose. It does not dress over or around the cut roll end.
   - **Renders:** south j01 (px ≈ 790-865 / 160-290), j05 (px ≈ 950-1210 / 0-145) and j07 (px ≈ 850-1010 / 170-310);
     north j03 (px ≈ 405-480 / 165-290) and j10 (px ≈ 215-260 / 615-680).
   - **Effect:** closed, but visually unexplained at 3-4 m from an actor.
2. **The cone eave hovers tight over the end of the ridge comb.**
   - **Measured clearance:** comb top 5.71 m, cone rafter feet 5.89 m and starter 5.96 m, so only 0.18-0.25 m of air
     under a 0.72 m overhang.
   - **Renders:** from a crane (j12, px ≈ 330-560 / 180-300) and in the j16 corner (px ≈ 1080-1280 / 290-320), the cone
     lip appears to sit on the comb. This is the same "eaves nearly meet" read the redesign was meant to remove. It is
     clean from the official cameras.
   - **Fix:** about 0.3 m more eave, or a lower ridge.
3. **The north flaunching crest is lumpy.** The crest undulates over each thatch course (j10, px ≈ 560-900 / 120-560).
   The flaunching ends in a small pointed toe on top of the north eave roll (j03, px ≈ 460-520 / 190-235). The south
   side is smoother (j09, j13).
4. **The round end now reads as a tower, not a round house end.**
   - **Massing:** a 6.0 m eave on a 7.4 m drum, 11.3 m to the finial, over a 2.3 m body eave (hero, front, back, j18).
     That is about 3.7 m, well over one storey, higher than the body eave.
   - **What still reads as ref1:** the mossy cone, the ball finial and the stone drum.
   - **What is lost:** the low, hunkered ref1 character of round 6. The drum now dominates the longhouse. A drum
     about 0.6-0.8 m lower would still clear the ridge if the cone eave clearance were tuned.
5. **The upper storey is blank.** It has three 0.45 x 0.60 m windows at a 3.7 m sill on a drum about 23 m round
   (front, side, j19). Only one shows in each official view, so the upper storey reads mostly as blank masonry.
   Acceptable, not rich.
6. **Process:** the build is at a work-in-progress path with `_r8` file names, and there is no builder entry. The
   hash-rule and determinism checks are outstanding for the audit.

**Regressions from round 6:**
- None in the body, the gable, the door, the windows, the soffits or the official views.
- The `actor_closeup` dark pocket of round 6 is gone (the junction no longer exists).
- The only loss is massing character (defect 4).

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.3 | Still unmistakably the longhouse with a round stone end under a mossy cone with a ball finial. But the raised drum reads as a tower that dominates the low body, more than the "about one storey" the brief asked for. The ref1 hunkered round house is weakened. |
| 2 Proportion and actor scale | 8.4 | The door (1.00 x 2.10 m), the body eave (2.30 m over the door), the sills and the ground floor of the round end are unchanged and right next to the 1.8 m figure. The upper windows are believable but small for the drum's wall area (j18, j19). |
| 3 Construction logic | 8.4 | The roof is visibly carried and dies into the masonry. The flaunching sits on the covering and is buried in the wall, with no floating abutment or eave pieces (probe). Points off: the aprons stand as unexplained plates, and the cone eave hovers 0.2 m over the comb. |
| 4 Seams and junctions | 8.4 | The junction that failed five rounds is now closed, flashed and free of see-through, along the true curve. All red twins are clean. Points off for the apron tabs, the lumpy north crest with its toe beak, and the tight cone-over-comb slot. |
| 5 Distinctness and reuse | 8.6 | `wall_abutment` is a genuine, generic kit module (any GableRoof, any round body R(z)) that reuses the junctions family. The recipe is declarative, and the eave-crossing machinery is bypassed, not deleted. The round-7 orphans were removed cleanly. |
| 6 Technical compliance | 8.2 | 617k tris (cap 1 M), 9.2 % hidden, 10 slots, `Mask` complete, 89 plausible anchors, no ground dressing. Points off: there is no builder entry, the six-building hash-rule results are referenced but missing, determinism is unverified, and the build is at a WIP path. |

**Verdict: 8.3/10, PASS (>= 8.2).** The pass is subject to the independent audit confirming determinism and the
hash rule. The redesign removes the junction that has failed every audit since round 3, and it replaces it with a
clean, reusable "roof into round wall" module. The remaining defects are cosmetic and none of them shows see-through.
