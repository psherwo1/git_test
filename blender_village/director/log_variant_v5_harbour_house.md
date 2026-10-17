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
## v5_harbour_house round 1 — builder entry

**Built:** the timber harbour house (approved building 3) and the new **timber / rectangular / waterfront kit family** it needs. Every piece comes from a kit module. The recipe holds only dimensions and the step order.

- **Recipe:** `buildings/variants/v5_harbour_house/build_v5_harbour_house.py` (91 lines, 76 non-blank non-comment). Saves `v5_harbour_house.blend` (6.5 MB, compressed) and `decal_anchors.json` beside it. `HARB_FAST=1` skips the cull; `HARB_OUT=` writes elsewhere.
- **Renders:** `renders/variants/v5_harbour_house/round_01/` (all six views, `--samples 24`, plus `stats.json` / `hidden.json`).
  - Supplementary `round_01/quay_datum/` (hero, front, side, actor_closeup) comes from a scratch copy cut at Z = -0.05. The reason: render_review puts its ground plane and its 1.8 m figure at the bounding-box minimum, and here that is the harbour bed (Z = -2.5). In the six main views the figure therefore stands on the bed, 2.5 m below the door. Judge actor scale on the quay_datum set. It is not a deliverable, only an aid for the review.

### The building (dimensions before `recenter`; the build log records the shift, (0, -2.730))

| Part | Kit module | Dimensions |
|---|---|---|
| Plan | `PlanFrame` | 5.6 x 9.0 m frame faces, ridge along Y; the land gable faces -Y (principal door), the water gable faces +Y |
| Plinth | `masonry_wall(path=...)` (rubble, quoins) | 0.32 m |
| Ground storey | `path_timber_wall` style `post_plank` | sill 0.24 x 0.18 (floor Z = 0.50), posts <= 2.4 m apart, plate top Z = 3.05; door 1.0 x 2.10 with three built-in stone steps; six shuttered windows 0.55 x 0.60 at sill 1.15; the **boat door** 2.6 x 2.5 (two ledged-and-braced leaves) on the water gable |
| Floor band | `jetty_floor` | joists 0.15 x 0.20 at 0.45 m, Z 3.05-3.25; the upper storey **oversails the land gable by 0.5 m**: joist ends 4 cm proud under the bressummer, soffit planks plus blocking close every joist bay; rim beams on the other sides run out to the jetty line |
| Upper storey | `path_timber_wall` style `board_batten` | bressummer / sole plate 0.26 x 0.24; cladding runs unbroken from the sill to the roof deck (eave strip closed, gables filled to the rake); six windows; an upper loading door 1.2 x 1.5 (the boat-door spec, smaller) over the boat door |
| Roof | `GableRoof` (yaw 90) + `linear_roof(covering="shingle")` + `verge_boards` | 52 deg kit shingle gable: wall_z 5.957, overhang 0.45, verges 0.40, ridge comb, rafter tails; bargeboards (mitred) with crossed gable horns; ridge Z ≈ 9.6, overall 9.91 m above the quay |
| Waterfront | `crib_quay`, `pile_deck`, `ladder` | timber crib quay under the house (7.2 x 10.9 m, bed to Z = 0, cap with crossed corners, fill top round the plinth); plank deck at Z = 0.50 on piles from the water gable (5.6 x 3.9 m) plus a jetty finger 1.8 x 3.2 m in **one** `pile_deck` call (union of rects, land = S); piles to the bed, bearers, joists, fascia, X bracing with waling, two mooring posts, a ladder to the bed |

**Datum (for UE placement).**
- Building-local, Z up, metres.
- Quay / landward ground Z = 0. Harbour bed Z = -2.5 (piles, crib and ladder go down to it).
- Ground floor, boat-door threshold and deck top all at Z = 0.50. Door threshold Z = 0.50, reached by three risers of 0.167 m.
- After `recenter` the plan bounding box (deck and jetty included) is centred on the origin. The house centre sits at (0, -2.73) and the water end faces +Y.

### New kit modules (`kit/village_kit/components/`; full record in `kit/changes/v5_harbour_house.md`)

- **`timber_walls.py`**
  - `path_timber_wall(g, name, path, z0, top, top_fn=None, style="post_plank" | "weatherboard" | "board_batten", gable_style, openings=[(s, spec)], sill, plate, post, bay_max, lap_out, backing=True, seed, clip_z, ground_z)` works along any polyline.
    - Corner posts.
    - Crossed, halved sill and plate ends at outside corners (heights alternate by 1.5 cm, so there are no coplanar faces).
    - A closed backing slab behind the cladding, cut at the openings.
    - Rake-clamped gable boards.
  - Openings come from the kit's ONE opening spec (`openings.door / window`) with the timber defaults `TIMBER_OPENING`: door with steps, shuttered window, and `boat_door(width, height, leaves, jamb, head, bearing, ledges, room)`.
  - Helpers: `rect_path`, `rect_openings` (by side), `roof_top_fn(roof)`, `wbox`.
- **`floor_stack.py`**
  - `jetty_floor(g, name, lower, z, jetty={"S": d, ...}, joist, spacing, rim, proud, soffit_t, tail)`.
  - `timber_storeys(g, name, rect, z_base, storeys=[dict(height, style, openings=[(side, coord, spec)], ...)], jetty, roof, floor)`.
- **`waterfront.py`**
  - `pile(...)`.
  - `pile_deck(g, name, rects, deck_z, bed_z, land, pile_rows, pile_cols, ..., moor)`: any rectilinear plan as a union of rects.
  - `crib_quay(g, name, rect, top_z, bed_z, hole, ...)`.
  - `ladder(g, name, top, out, z_bot, ...)`.
- **`timber_roof.py`**: `verge_boards(g, roof, depth, t, horns, horn_len, ends)`.
- **`timber_finish.py`**:
  - `timber_hidden_cull` (composite cull limited to the backed parts);
  - `timber_decals` (composite decals plus timber and waterfront anchors).

**A boathouse or barn is now a short recipe:** `crib_quay` or `pile_deck` for the base, `timber_storeys` with one storey and `boat_door` openings, a `GableRoof` with `linear_roof`, then `verge_boards`.

**Existing kit modules changed: none.** `GableRoof` / `linear_roof`, `masonry_wall`, `PathMap`, `openings`, the composite cull and the composite decals are used unchanged.

**Hash rule: not needed (only new files).** No file in `kit/village_kit/` that existed before this round was modified, so the seven other kit buildings cannot have moved.

### Junctions (how each is closed)

- **Wall to wall:** a corner post at every outside corner, proud of both faces in the clad styles. The sill and plate ends cross and run 7 cm past the other face, with no coplanar faces.
- **Wall to plinth:** the sill beam sits on the 0.32 m rubble plinth and stands 2 cm proud of its face. The clad storey's boards lap 4 cm down over the sill.
- **Jetty oversail to the lower wall:**
  - the joists run through the lower wall head;
  - blocking boards between the joists sit over the lower plate;
  - plank soffits close the joist bays;
  - the rim beams close the ends;
  - the bressummer carries the upper wall.
- **Wall head to roof:** the upper cladding runs to the deck underside + 2 cm, both along the eaves (the strip between the rafter tails is closed) and up the gables. Bargeboards cover the deck ends, verge rafters and shingle ends, and mitre at the ridge.
- **Deck to house:** the deck runs to 1 cm off the sill beam, level with the boat-door threshold. The joists bear on a ledger on the crib cap. The piles start 0.75 m out, clear of the crib face.
- **Deck to piles:** each pile stands under a bearer, with iron dog plates.
- **Boat door in the wall:**
  - the jambs and the head beam (bearing 0.30 m past the jambs) frame it;
  - the cladding is cut to the jambs and the backing is cut to the clear opening;
  - the leaves are set into the reveal.

### Stats (round_01 `stats.json`)

| Measure | Value |
|---|---|
| Triangles | 254,626 (note 15 cap 1,000,000) |
| `est_hidden_pct` | 14.0 % |
| Material slots | 9, all in the palette |
| `mask_attribute_missing` | none |
| Objects | 35 (no pooled instances) |
| bbox | 7.20 x 18.06 x 12.41 m (bed to finial horn; 9.91 m above the quay) |
| Build time (cull included) | about 6.5 minutes |
| Decal anchors | 103 kept of 131 by the kit gate (`validate_anchors`, applied); `anchor_audit.audit_anchors` on the saved blend + JSON: 0 failures (scratch `audit_anchors.py`) |

- About 4.7 % of the hidden share is the crib and the piles below Z = 0, which `hidden_tris.py` counts as buried.
- Guards: the clearance gate PASSES at the principal door (lip 3.048 m on the jetty joists, against a door head of 2.60 m) and at the boat door (7.58 m). There is no roof-through-body junction for the seal probe. Steep-cone and lod-scope do not apply. No opt-outs.

### Known gaps

- **Review-tool datum:** render_review puts its ground plane and figure on the harbour bed (Z = -2.5), so in the six main views the figure stands 2.5 m below the door. Judge actor scale on `round_01/quay_datum/`.
- **Crib quay:** it is my addition so that the land half does not float over the bed plane in the clay renders. In UE the terrain at Z = 0 will bury its land faces. Drop the `crib_quay` step if the placement has its own quay.
- **`jetty_floor`:** two jettied sides meeting at a corner (a dragon beam) are not supported, so the jetty is on the land gable only.
- **`path_timber_wall`:** concave corners have no dedicated inside post.
- **Not built:** a hoist beam over the upper loading door, and a water-gable jetty.
- The roof is a plain kit-shingle gable with a comb. Its slopes face +-X, so composite_decals' "north slope" moss (local +y) lands on the -X slope.
- Surface detail is deliberately not pushed (note 12).

## CLIENT DIRECTION (2026-10-17, session 2, after the first round-1 renders): direction for round 2

The client reviewed the early round-1 clay renders (hero, back, actor close-up, 10:08) and chose these changes, binding from the next round. The round-1 Art Director should list them as must-fix items:

1. **Rougher, older timber.** Irregular board widths, slight sag and out-of-true, a chunkier hand-split look, and the same age and moss treatment (`age_defaults`) as the other buildings. The current boards are too even and too clean.
2. **The village's roof and finials.** The same chunky, mossy shingle and shake sizes and courses as the keep, the roundhut and the longhouse. Use the village's finial vocabulary (ball or spike finials, the kit's `ball_finial`) instead of the new crossed gable boards, which appear on no other building.
3. **A stronger jetty and a lower mass.** A clearly visible jettied upper floor (about 0.4-0.6 m oversail on joist ends and a bressummer), and slightly lower storeys, so it reads as a harbour house, not a tall farmhouse (the ridge is about 10 m now).
4. **Round structures and soft, organic lines (producer note 17; read it in full).** Client's words: "something that makes the initial concept art unique is the use of round structures and soft, organic lines. In my opinion It's what gives it a unique aesthetic rather than a more generic village building".
   - Give the harbour house at least one integral round element, built from the kit's round families where possible: for example a round stone or timber stair or lookout turret under a cone at one corner, or a round store or hoist at the quay end.
   - Soften the lines: bell-cast or swept eaves, a gently sagging ridge, rolled verges, curved braces and brackets.
   - It must still read as a timber harbour house.
5. **Not requested:** the client did not ask for a stone quay. The plank quay face may stay; the rubble plinth under the walls stays.

Make the new softness reusable kit options (e.g. a swept eave or ridge sag on `timber_roof` / `linear_roof`, a bow on `path_timber_wall`), and record them in `kit/changes/v5_harbour_house.md`.
## CLIENT DIRECTION (2026-10-17, session 2): the client's concept art for the harbour house — `reference/ref4_harbour_boathouse_concept.jpg`

The client attached concept art "for inspiration": `reference/ref4_harbour_boathouse_concept.jpg`. **Open it (Read tool) before you grade or build.** It is now the primary visual reference for this building. Where it differs from the "Brief" above, follow the concept, within producer notes 1-17 and the 1 M cap. What it shows, and what to take from it:

1. **A stone and timber boathouse-hall, not an all-timber house.**
   - The ground storey is coursed rubble, in the village's stone.
   - The water-facing gable is a heavy timber **cruck / arched-brace frame**: big curved members forming pointed and round arches, with plank infill in the upper gable.
   - A **wide arched boat opening** runs through it at water level; boats moor inside under the arch.
   - This replaces "rectangular timber house with a big door". The large boat door module becomes a **large arched opening framed by curved timbers**.
2. **A round stone tower at the landward corner.**
   - It is integral to the plan, with a timber-clad top storey (vertical boards, small windows, a timber sill band) under a steep, mossy, conical shingle roof with a spike finial.
   - It has small square windows in the stone, and the shingle roof abuts it.
   - Build it with the kit's round families: drum / `round_stone_body` + `cone_roof` + finial, with `roof_junction.wall_abutment` where the main roof meets it.
3. **A soft, sagging, swept roof.**
   - Thick, chunky, mossy shingles (the keep / roundhut sizes).
   - The ridge visibly sags and the eaves sweep.
   - Bargeboards / verges curve and flare up at the gable apex.
   - An **eyebrow dormer**: the shingles roll up over a small window with no hard edges.
   - A lower wing roof steps down at the side.
4. **A curved stone stair** wraps around the tower base, behind a curved parapet wall. It is a strong "round and organic" element; include it if the triangle budget allows.
5. **Waterfront.**
   - The building stands on a stone quay edge of large blocks; the boat hall opens onto water.
   - A plank jetty on posts runs out from the quay.
   - So the stone quay is now in: it follows the concept, and is consistent with note 16. This supersedes "the plank quay face may stay" in the entry above.
   - Piles and deck: a short jetty on timber posts, as in the concept.
6. **Optional, if budget allows:** the small round stone store with a conical shingle roof (concept, right edge). It could also be a separate small design later; record the choice.
7. **Out of scope (note 10, no ground dressing):** the cobbles, ropes, nets, barrels, crates, boats and cliffs. Leave decal anchors where they would go.

The round-2 direction above still applies (old, rough timber; the village's shingle and finials; soft organic lines; the jetty). The jettied upper floor is no longer required if the concept's cruck hall replaces the two-storey timber house. The **kit family** is still the deliverable: the cruck / arched-brace frame, the arched boat opening, the timber walls and the swept / sagging roof options must all be reusable modules. A boathouse or barn must still be a short recipe.
## CLIENT DIRECTION (2026-10-17, session 2): reuse as many existing modules as possible

Client's words: "Reuse as many existing modules as possible".

- **Builder and fixers:** build every part of the concept (ref4) that an existing kit module can make with that module, extended where needed by **optional parameters whose defaults keep the old behaviour** (the HASH RULE then applies: rebuild the seven others and match the kit 1.11.0 table). Write a new module only for what nothing in the kit can make, and say why in the builder entry. The mapping to start from (check the CHANGELOG 1.11.0 module list for more):

  | Concept part | Existing module(s) to use |
  |---|---|
  | rubble ground storey, quay edge | `rubble_walls.path_stone_wall` (and its openings) |
  | round stone tower | `rubble_walls.round_stone_body`, `composite.cone_roof` (mossy shingle cone), `ball_finial` / the existing spike finials, `RoundFrame` / `KitParams` |
  | timber top storey of the tower | the drum family's timber gallery / cabin pieces (`square_cabin` round-bed option, or the tier / drum timber bands): reuse before writing new |
  | main roof and lower wing roof | `linear_roof.GableRoof` / `linear_roof` (shingle covering, verge, ridge roll, eave roll); add sag / sweep / flared-verge OPTIONS to it rather than a parallel roof module |
  | roof meeting the tower | `roof_junction.wall_abutment` (the longhouse round-8 module) |
  | doors, windows, shutters, thresholds, steps | `wall_openings.door_spec` / `window_spec` and the existing door / step / threshold pieces |
  | age, moss, Mask, UVs, decals, cull | `age_defaults`, `mask`, `uvgrain`, `composite_decals`, `composite_hidden_cull` |
  | genuinely new (no existing module) | the cruck / arched-brace gable frame and the arched boat opening; the eyebrow dormer (planned add-on); the curved stair, if built; piles and jetty |

- **Round 1's new modules:** the round-2 fixer must check `timber_roof.py`, `timber_finish.py`, `timber_walls.py`, `floor_stack.py` and `waterfront.py` against the kit. Where one duplicates an existing module (for example `timber_roof` against `linear_roof`), fold it into the existing module as options and retire the duplicate. Keep only the timber pieces that are truly new.
- **Art Director and auditor:** score reuse explicitly under **distinctness and reuse**. List each existing module used and each new one with its justification. A new module that duplicates an existing one is a must-fix.

## v5_harbour_house round 1 — score 6.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing
(note 10), no surface-detail requests (note 12). Binding for this grade: producer notes 1-17 and every CLIENT
DIRECTION entry above, including the three that arrived after round 1 was built: the round-2 direction (rougher
timber, the village's finials, a lower mass, note 17), the ref4 concept (now the primary reference) and the reuse
mandate. Round 1 was built to the original Brief. **Against that Brief alone the house would score about 7.7**,
capped by construction logic. Against the binding direction it is the wrong building, so the grade is 6.3.

**Reviewed:**
- All 6 main renders, the 4 `quay_datum/` views, `stats.json` and `hidden.json` (both sets), and
  `decal_anchors.json` (103 anchors, plus the gate's validation block).
- The recipe (76 lines), the five new modules, `kit/changes/v5_harbour_house.md`, the scratch build logs (two full
  builds gave identical counts, 254,626 tris), ref1-ref4 and ref crops of the ref2 / ref3 waterfront houses.
- Director extras in `renders/variants/v5_harbour_house/round_01/director_extra/`:
  - 23 junction close-ups d01-d22, with 13 red see-through twins;
  - the note-16 line-up L01-L03 (keep, roundhut, longhouse, harbour house at one scale);
  - two geometry probes (`probe_r01_out.txt`, `probe2_r01_out.txt`: islands, transforms, `Mask`, and rays
    into the boat door and the shutters).

**Director-verified compliance:**
- 35 meshes, all with identity transforms and a `Mask` attribute (CORNER, BYTE_COLOR); 9 palette slots.
- Collections `HARB`, `HARB_kit_instances` (empty) and `DECAL_ANCHORS`.
- No see-through pixels in any of the 13 red twins: d02 corner, d03 jetty corner, d04 soffit, d05 eave strip,
  d06 / d20 verge foot, d07 / d08 apexes, d10 deck-to-sill, d13 east wall, d14 band corner, d17 loading door,
  d18 roof.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 5.8 | It is a believable timber waterfront house in the manner of ref2 / ref3 right side: jettied land gable, piles and a jetty finger (d19, L02). It is not the ref4 building, which is now the primary reference: a rubble boat hall with a cruck / arched-brace water gable, an arched boat opening, a round stone tower with a timber top under a cone, and a sagging, swept, mossy roof. It has no round element and its ridge, eaves, verges and walls are ruler-straight, so it could stand in any generic village (note 17 must-fix). The crossed gable horns read as foreign in the line-up (L01, L02). The 9.9 m ridge reads as a tall farmhouse (client direction 3). |
| 2 Proportion and actor scale | 8.2 | Land door 1.00 x 2.10 m on three 0.167 m dressed-stone risers, with the jetty joists 3.05 m above the quay over it. Windows 0.55 x 0.60 m at 1.15 m above the floor; storeys of believable height (quay_datum actor_closeup, d01, d16). The boat door's real clear height is only 2.35 m, not the 2.5 m specified (the plate crosses it, see axis 3). The mass is too tall for the client. |
| 3 Construction logic | 7.4 | The framing is right almost everywhere. Sill, posts at most 2.4 m apart and plate; jetty joists run through the wall head with blocking and a closed plank soffit under a bressummer (d03, d04); the deck sits on a ledger on the quay cap; piles carry bearers with dog irons, plus X-bracing and a waling (d11, d12). Two faults. **(a) The boat door is taller than its storey:** clear 0.50-3.00 m against a plate underside at 2.85 m. The plate runs across the opening in front of the top 16.5 cm of the leaves; the 0.30 m head beam (3.00-3.30) is stuck on the face of the plate, the floor-band rim and the upper sill, and carries nothing (d09, d14, d17, d22; ray probe). **(b) The shutters hang on nothing:** their iron straps lie on the jambs, 5-6 cm proud of the jamb face, not on the shutters, and no pintle is modelled (d15; ray probe at y -1.50 to -1.40 and -0.80 to -0.75). |
| 4 Seams and junctions | 7.7 | All 13 see-through twins are clean. Closed details: crossed, height-alternated sill / plate / rim ends (d02, d14); the eave strip clad to the deck (d05); bargeboards over the course ends (d06, d07); the deck stopping 1 cm off the sill, level with the threshold (d10). Defects: the boat-door jamb tops pass through the plate with coplanar front faces (w = +0.02), giving a z-fight patch at both jambs (d22). The head beam clips into the bressummer zone. The two horns of each apex pair are in one plane and interpenetrate at the crossing (d08). |
| 5 Distinctness and reuse | 6.4 | It is clearly a new building type, from a 76-line recipe with no hero file touched. **Existing modules used:** `assembly.build_building` / `KitParams`, `PlanFrame`, `masonry.masonry_wall` (rubble plinth), `rubble_walls.PathMap`, the `openings.door / window` SPEC only, `linear_roof.GableRoof` + `linear_roof(covering="shingle")` with the comb, `composite.recenter / composite_hidden_cull / composite_decals`, the guards, `uvgrain`, and the `geom` helpers. **New:** `waterfront.pile / pile_deck / ladder` (justified: nothing in the kit makes piles or a deck); `floor_stack` (justified for a jetty, which ref4 no longer needs); `timber_walls.path_timber_wall` (justified as a new wall form). **Duplicates, each a must-fix under the reuse mandate:** `timber_walls._build_opening` (its own door leaf, frames, window, shutters, steps and flat-bar straps, alongside `wall_openings.build_opening`, `plank_doors.plank_leaf / strap_hinge / make_pintle` and the `stone_body` shutters); `timber_roof.verge_boards` (alongside `linear_roof`'s verge finish); `timber_finish` (thin wrappers on the composite cull and decals); `crib_quay` (superseded by ref4's stone quay). **Note-16 details found nowhere else:** the crossed gable horns; strap hinges without a terminal, pintle or nails; no finial. Round families: none used. |
| 6 Technical compliance | 8.4 | 254,626 tris (cap 1 M); 14.0 % hidden (12.8 % on the quay-datum copy); 9 palette slots; `Mask` everywhere; deterministic (identical counts on two builds); 103 anchors, mostly plausible. Points off: the crib quay's land faces run 2.5 m below the quay datum the brief itself buries (note 6: nothing deeper than 5 cm). 13 decal anchors sit on those buried faces (`DA_damp_rise_019` to `_031` at z -0.6 to -1.4 on the crib's -Y and +-X faces). There is no pooling at all (0 pooled meshes, note 3: hinge irons, rungs, dog plates). |

**Verdict: 6.3/10, NOT PASSED (pass mark 8.2).** As a piece of kit engineering round 1 is good. The timber wall,
jetty floor and pile deck are genuinely parameterised; the junctions are closed and clean under every
see-through check; actor scale is right; and the numbers are well inside every cap. But the client has since
redefined the building (ref4: a stone boat hall with a cruck gable and a round tower), made round, soft lines the
village signature (note 17) and mandated maximum reuse of existing modules. Round 1 meets none of the three, so the
silhouette and reuse axes cap the grade. Two construction faults (the boat door against the plate, and shutter
straps on the jambs) must not carry into the new build, because the barn and the boathouse will use the same
opening code.

**Strengths**
- Junction discipline: 13 red see-through twins are all clean. Corners use crossed, height-alternated sill / plate
  / rim ends with no coplanar faces; the eave strip is clad to the deck; the verge is boarded over the course ends;
  the deck stops 1 cm off the sill, level with the threshold.
- `path_timber_wall` works along any polyline, with three cladding styles, the shared opening spec, rake-clamped
  gable boards and a closed backing slab cut at the openings. It is a sound base for the ref4 tower's timber top
  storey and the cruck gable's plank infill.
- `jetty_floor` / `timber_storeys` are honest construction: joists through the wall head, blocking over the plate, a
  closed soffit, rim beams to the jetty line, and a guard (it raises) for the unsupported dragon-beam corner.
- `pile_deck` takes any union of rectangles in one call, with bearers, dog irons, joists, a ledger, fascia on free
  edges only, X-bracing, a waling, mooring posts and notched planks. It is directly reusable for ref4's jetty.
- Technically clean: 254,626 tris, 14.0 % hidden, 9 slots, `Mask` everywhere, identity transforms, a deterministic
  rebuild, and the datum recorded for UE.

**Must-fix (round 2)**
1. **Build the ref4 building (CLIENT DIRECTION, ref4).**
   - Ground storey: coursed rubble with `rubble_walls.path_stone_wall` and its openings.
   - Water gable: a heavy timber cruck / arched-brace frame, built as ONE new reusable module (e.g.
     `cruck_frame(g, name, span, rise, arches, infill="plank")`). Through it runs a wide arched boat opening at
     water level, about 4-5 m wide, as an opening type of that module or of the shared opening spec. Boats moor
     inside: the hall floor is open water or a slip, so the wall's sill / plinth stops at the arch feet.
   - Landward corner: a round stone tower built from `round_stone_body` + `composite.cone_roof` (mossy shingle
     cone) + the kit's spike finial. Its timber top storey reuses the drum / tier timber band or the
     `square_cabin` round-bed pieces before anything new is written. Small square windows go in the stone.
   - The main roof meets the tower through `roof_junction.wall_abutment`, and a lower wing roof steps down at the
     side (a second `GableRoof`).
   - The building stands on a stone quay edge of large blocks (`path_stone_wall`, dressed / large-course options),
     with a short plank jetty on posts (`pile_deck`).
   - The curved stair and the eyebrow dormer are optional within budget. Record the choice, and the choice on the
     round store.
2. **Soft, organic lines as kit OPTIONS (note 17, client direction 4).** Today the ridge, both eaves, both verges
   and every wall run are ruler-straight (d18, d19, L02).
   - Add to `linear_roof.GableRoof` / `linear_roof`: `ridge_sag` (about 8-15 cm mid-span), `eave_sweep` /
     bell-cast at the eave, and `verge_flare`, a curved bargeboard / verge that flares up at the apex as in ref4.
     The defaults must keep the old behaviour (hash rule: rebuild the seven others and match the 1.11.0 table).
   - Add a `bow` / out-of-true option to `path_timber_wall` runs.
   - Curved braces belong to the cruck module.
3. **The village's finial and roof, not new ornament (note 16, client direction 2).**
   - Remove the crossed gable horns: `timber_roof.verge_boards(horns=0.42)`, the X at both apexes, about
     (0, -8.2, 9.4-9.9) and (0, 2.2, 9.4-9.9) after the recentre (d07, d08).
   - Put the kit's `ball_finial` or spike finial with its lead hat on the gable apex / ridge ends, and the spike
     finial on the tower cone.
   - Shingles: the keep / roundhut SIZE_TABLE sizes and courses, with the village's mossy age treatment
     (`age_defaults`, where the covering supports it).
4. **Rougher, older timber at FORM level (client direction 1).** Not surface detail (note 12).
   - Board widths irregular over a wider range: board_batten `w` is now 0.20-0.30 m, post_plank row heights
     0.20-0.30 m. Use about 0.16-0.40 m with occasional narrow fillets.
   - Boards and posts slightly out of true (±1 deg, bible 4).
   - Slight sag in long members, and chunkier, hand-split board edges.
   - All as `path_timber_wall` options shared with the cruck infill.
5. **Reuse mandate: retire the duplicates.**
   - `timber_walls._build_opening` (lines 290-414): doors, windows, shutters, steps and straps must come from
     `wall_openings.door_spec / window_spec / build_opening`, with `plank_doors.plank_leaf`, `strap_hinge` and
     the pooled `make_pintle` for every leaf and shutter. Add a timber-wall host option there if needed, instead
     of a second opening builder.
   - `timber_roof.verge_boards`: fold it into `linear_roof` as a verge option and delete the module.
   - `timber_finish`: fold the backed-only cull filter and the timber / waterfront anchors into
     `composite_hidden_cull` / `composite_decals` options, or a `finish.py` family entry.
   - `waterfront.crib_quay`: superseded by the stone quay.
   - `floor_stack`: keep it in the kit if it is still clean, but this recipe no longer needs a jetty.
   - In the builder entry, add a table of every existing module used and every new module with the reason
     nothing existing could make it.
6. **The opening must never cut through the storey head, in whichever module carries large doors.** Today this is
   `timber_walls.boat_door` inside `path_timber_wall`. Location: the water gable (0, 1.77), z 2.85-3.49 (d09,
   d14, d17, d22).
   - What is wrong: the clear opening reaches 3.00 m while the plate underside is at 2.85. The full-length plate
     crosses the opening in front of the leaves' top 16.5 cm; the 0.30 m head beam is laid on the face of the
     plate, the floor-band rim and the bressummer; the jamb tops share the plate's front plane (z-fight).
   - What it should be: when cz1 + head > the plate underside, either clamp the clear height so the plate is
     the lintel (leaves 1 cm under it, no separate head beam), or trim the plate at the jambs and let the head
     beam replace it flush, at the plate's own depth and top. Raise for anything else.
   - The clearance guard must report the effective head (it reported 3.00 m for a 2.85 m opening).
   - A barn door will hit this on its first build.
7. **Shutter hardware** (`timber_walls._build_opening`, lines 345-350, all 12 windows, d15).
   - What is wrong: the strap runs from the shutter's hinge edge toward the opening, over the jamb, 5-6 cm
     proud of it (`hs - sgn * sw * 0.6`), and the shutter itself has no strap and no pintle.
   - What it should be: straps on the shutter leaves, running from the hinge edge outward, with a pintle into the
     jamb and the shutter's back on the jamb face. This comes free if must-fix 5 moves shutters onto the kit's
     hinge / pintle pieces.
8. **No buried quay faces or anchors (note 6, note 11).**
   - What is wrong: `crib_quay` builds all four faces down to the bed, including the land faces the datum buries
     (y = -8.93 and x = +-3.5 after the recentre). 13 anchors (`DA_damp_rise_019` to `_031`, z -0.6 to -1.4) sit
     on those faces.
   - What it should be: whatever quay module replaces it takes `water_sides=`. Water faces run to the bed; land
     faces stop at a -0.05 m skirt. Waterline anchors go only on water faces, in the z -0.9 to 0 band.
9. **A lower mass (client direction 3).** The ridge is 9.9 m above the quay, under a 5.75 m wall stack. In the
   ref4 hall the roof dominates: the eave wall is about 3-3.5 m on the long sides; the ridge is about 8.5-9.5 m;
   the tower's cone tip stands clearly above the main ridge (about +3 m).
10. **The builder entry must carry the note-16 record** (what is reused and what still differs), as the note-16
    CLIENT DIRECTION entry requires. Round 1's entry does not have it.

**Nice-to-have**
- `tools/render_review.py`: a `--ground_z` option, or the datum read from `decal_anchors.json`, so the six main
  views put the figure on the quay. This round needed a second `quay_datum/` set. A producer tool change.
- `pile_deck`: accept `land` = "E" / "W", so a deck can run along a long side.
- Add a short scratch smoke recipe for a barn, a few lines long, to prove the family stays a short recipe.
- Pool the repeated small irons, ladder rungs and dog plates as linked duplicates (note 3).
- Composite decals: the "north slope" moss on a yaw-90 GableRoof lands on the -X slope; orient by world +Y
  after placement.
- The kit README still lists the timber family as "not covered yet"; it is for the producer's merge.
- A hoist beam over the upper loading door, if that door survives into the ref4 design.
## PRODUCER NOTE (2026-10-17, session 2, 12:10): round-2 fixer interrupted; relaunched

The first round-2 fixer was stopped at 11:36 by an unintended tool-use rejection (the client confirmed it was not intended). It had made:
- round-2 review renders (`renders/variants/v5_harbour_house/round_02/`, 11:22: 756,343 tris, **20.4 % hidden**, over the 15 % hard limit);
- kit edits, the last to `timber_walls.py` at 11:35;
- a completed hash run (`kit/baseline/v5r2_hash/`);
- a barn smoke test (`buildings/variants/v5_harbour_house/scratch/barn_smoke/`).

Its last full build (`scratch/r2_full2`) was killed part-way through the cull. It wrote no builder entry.

**The relaunched round-2 fixer:** review those edits and keep what is sound. Re-run the hash rule if any existing module changed after 11:28. Finish round 2 against the round-1 must-fix list and every CLIENT DIRECTION above, rebuild, render `round_02` again, and write the builder entry. The barn smoke test is welcome but optional.

## v5_harbour_house round 2 — builder entry

**Built:** the ref4 harbour boat hall (client direction, ref4 now primary). A coursed rubble hall with a heavy timber
cruck / arched-brace water gable over a 4.6 m arched boat opening, a round rubble tower with a timber top storey under
a mossy shingle cone at the landward corner, a lower rubble wing, a soft sagging / swept / flared shingle roof, a stone
quay edge of large blocks and a short jetty on piles. Two fixers did this round. The first (until 11:36) made the kit
work and the reuse fold-ins. The relaunched fixer (from 12:10) reviewed and kept those edits, then fixed what the
11:22 renders showed:
- the quay read as vertical planks;
- hidden geometry was 20.4 %;
- the cruck frame was timid;
- the tower's timber top was a thin band.

It then rebuilt, re-rendered and re-ran the hash rule.

- **Recipe:** `buildings/variants/v5_harbour_house/build_v5_harbour_house.py` (158 lines, 139 non-blank non-comment
  including the docstrings). It is dimensions plus the step order only. It writes `v5_harbour_house.blend` (19.0 MB,
  compressed) and `decal_anchors.json` (110 anchors). `HARB_FAST=1` skips the cull and `HARB_OUT=` writes elsewhere.
- **Renders:** `renders/variants/v5_harbour_house/round_02/` (all six views, `--samples 24`, 12:46, replacing the
  11:22 set), with `stats.json` and `hidden.json`.
- **Review-tool datum (unchanged quirk):** render_review puts its ground plane and figure at the bounding-box minimum,
  which here is the harbour bed (Z = -2.5). The building therefore "floats" 2.5 m over the clay ground, and the
  figure stands on the bed. This is not a model defect. In UE the terrain or water at Z = 0 meets the quay coping.

### The building (dimensions before `recenter`; the build log's shift is (-1.308, -5.973))

| Part | Kit module(s) | Dimensions |
|---|---|---|
| Hall | `rubble_walls.path_stone_wall(cfg=RUBBLE_LARGE, base=-0.04)` | 6.0 x 9.2 m. Eave walls 3.35 m (wall heads follow the warped deck + 2 cm). Land-gable door 1.0 x 2.10 on built-in steps, a gable window and three side windows (`door_spec` / `window_spec`). The open slip runs 3.2 m into the hall to a boarded partition. |
| Water gable | stone piers (the same `path_stone_wall`) + `cruck.cruck_frame` (new) | Piers to the eave line (3.38). Tie beam 0.32 m at 3.38-3.70 over +-2.75 m. Jamb posts 0.30 m on dressed pad stones. A segmental ARCH, face 0.34 m, from 2.00 to a 3.03 m crown (R 2.38) over the 4.6 m clear opening. Curved blades 0.40 m (elbowed) to the apex at 8.26. A collar at 5.98. A new two-centred POINTED inner arch, face 0.28 m, from the tie at +-1.7 m to the king strut. Rough plank infill is set 15-18 cm behind the member faces, and the members stand 6 cm proud of the stone face. |
| Partition | `timber_walls.path_timber_wall(style="board_batten", rough=True, bow=0.03)` | Boards up the rake, closing the hall behind the slip. |
| Main roof | `linear_roof.GableRoof` (yaw 90) + `linear_roof(covering="shingle", verge="board", apex_finial="turned")` | 58 deg, overhang 0.45. Verges 0.35 / 0.50. **ridge_sag 0.24, eave_sag 0.08, eave_sweep 0.28 over 1.0 m, verge_flare 0.36 over 2.0 m, wave 0.02.** Curved, apex-flared bargeboards with no horns. The keep's turned finial on a lead hat at both apexes (tips 9.57). Ridge top about 8.7 m. |
| Tower | `round_stone_body(cfg=RUBBLE_LARGE)` + `board_belt(body=...)` + `composite.cone_roof` + `finial(style="spike")` + `round_eave_fill` | r 2.30, batter 1.5 deg, stone to 6.90 with three small windows. **Timber top storey now 1.70 m** (6.90-8.60; it was 1.0 m): vertical boards, a hewn sill band ring at the foot and a head ring, and **four** cased lookouts 0.40 x 0.50. Kit-shingle cone (`AGE_R10` age) from the 8.60 eave, tip about 11.9, which is about 3.2 m over the main ridge, plus the spike finial (13.44). |
| Roof to tower | `roof_junction.wall_abutment` (main and wing) | Main run z 3.02-6.84, wing run 2.70-4.81, lead abutment flashing. The seal probe finds 0 leaks on both. |
| Wing | `path_stone_wall` + `GableRoof` / `linear_roof` | 6.0 x 3.4 m, eave 2.85, 50 deg, ridge_sag 0.14, eave_sweep 0.18, verge_flare 0.24. Door 1.0 x 2.10 and two windows. Turned finial on its free gable (tip 6.14). |
| Quay | `waterfront.stone_quay(detail_z=QZ, core_blocks=True)` | Water faces only, 18.8 m of face including the two slip returns and the slip head: x 9.6 to -3.0 along the water gable line. Laid as large blocks from the bed (-2.5) to the coping (-0.04): courses 42-58 cm, blocks 0.85-1.55 m, broken joints, a flush coping course and a recessed joint backing. No land faces are built. |
| Jetty | `waterfront.pile_deck` + `ladder` | 1.8 x 5.0 m deck at the quay level on 8 piles to the bed, with X-bracing, a waling, two mooring posts, and a ladder to the bed. |

**Datum (for UE placement).**
- Building-local, Z up, metres.
- Quay and landward ground Z = 0. The quay coping and the wall footings are at -0.04, the jetty deck at the quay
  level, and the harbour bed at Z = -2.5 (piles, quay face, ladder).
- The hall floor is open water (the boat slip). After `recenter` the plan bounding box is centred on the origin
  (shift (-1.308, -5.973)) and the water gable faces +Y. The datum is also in `decal_anchors.json` (`datum`).

### Round-1 must-fix list: what was done

| # | Must-fix | Done |
|---|---|---|
| 1 | Build the ref4 building | Done as in the table above. Ground storey `path_stone_wall`. Water gable `cruck_frame` (one reusable module) with a 4.6 m arched opening at water level, where the plinth stops at the arch feet (the hall wall path turns into the slip at the jambs). Tower `round_stone_body` + `cone_roof` + spike finial, with its timber storey from `board_belt` (the drum / tier band family, given a plain-body option). `wall_abutment` for the main roof and a lower wing GableRoof. Stone quay of large blocks and a `pile_deck` jetty. **Choices:** no eyebrow dormer, no curved stair, no round store (all optional). The store is better as its own small design later. |
| 2 | Note-17 softness as kit options | `GableRoof(ridge_sag, eave_sag, eave_sweep, sweep_len, verge_flare, flare_len, wave)`, one vertical warp field that every linear_roof part and query follows (see `kit/changes/v5_harbour_house.md`). `path_timber_wall(bow=)`. Curved members live in `cruck_frame`. Defaults are bit-identical (hash rule below). |
| 3 | Village finials and roof, no horns | `timber_roof.verge_boards` is retired: no crossed horns anywhere. `linear_roof(verge="board")` gives curved bargeboards. `apex_finial="turned"` places `finial.turned_finial` on a `finial.lead_hat` at each free apex, and the cone carries the spike finial. Shingles come from `shingles.SIZE_TABLE` (the keep / roundhut sizes); the cone uses `AGE_R10` `age_defaults`. Moss uses the village decal anchors (`moss_normal="slope"`). |
| 4 | Rougher timber at form level | `timber_walls.ROUGH` / `rough=True`: board widths 0.16-0.40 m log-uniform with 12 % fillets of 8-12 cm, +-1 deg out of true, long rows and plates sagging, 1.4 cm split arrises, +-1.5 cm uneven ends and 3.2-4.2 cm boards. Shared with the cruck infill through `board_widths` / `rough_opts`. |
| 5 | Reuse mandate | `timber_walls._build_opening` no longer builds anything: every door, window, shutter, boat door and step comes from `wall_openings.build_opening(host=TIMBER_HOST)`, with `plank_doors.plank_leaf`, `strap_widths` and the pooled `make_pintle`. `timber_roof.verge_boards` is folded into `linear_roof(verge=)`. `timber_finish` is folded into `composite_hidden_cull(parts=BACKED_PARTS)` and `composite_decals(timber=, waterfront=)`. Both retired files are stubs that raise `NotImplementedError` (deleting them was refused by the permission guard, so the producer can delete them at the merge). `crib_quay` is removed in favour of `stone_quay`. `floor_stack` is kept unchanged and is not used here. Tables are below. |
| 6 | Large door never crosses the storey head | `TIMBER_HOST["head_rule"]`. **"clamp"**: the clear height is clamped so the plate is the lintel (leaves 1 cm under it, no separate head beam). **"trim"**: the plate is cut between the jambs and the head beam replaces it flush at the plate's depth and top. Anything else raises. The opening record's `z1` is the effective head, so the clearance guard reports it. Barn smoke (12:4x): "head rule clamp: effective clear head 2.765 m" for a 3.0 m door in a 2.6 m storey, "head rule trim: effective clear head 2.680 m", and both clearance gates report 2.77 / 2.68 m. |
| 7 | Shutter hardware | The shutters are `plank_leaf` leaves. The forged straps lie on the leaves and run outward from the hinge edge, and pooled pintles go into the jamb (barn smoke: 20 linked pintle instances, 3 pooled meshes; see `scratch/barn_smoke/renders/actor_closeup.png`). The harbour house's own windows are in stone and use the masonry host's kit shutters. |
| 8 | No buried quay faces or anchors | `stone_quay(water=)` builds water faces only, so land runs are left to the terrain. All 9 anchors below Z = 0 are on quay water faces at z -0.35 to -0.72 (`M_stone`); none is on a land face. |
| 9 | Lower mass | Eave walls 3.35 m, ridge top about 8.7 m (it was 9.9), and the cone tip about 3.2 m over the main ridge. |
| 10 | Note-16 record | See below. |

### Fixes by the relaunched fixer (after the 11:22 renders)

1. **Quay read as vertical planks.** Below the 0.9 m rubble band the quay core was one flat slab per run, and the
   clay views (ground at the bed) showed it as tall panels. Fix: `stone_quay(core_blocks=True)` (new option in the v5
   module), which lays the face as low-poly large blocks (~60 tris each) on a recessed joint backing. With
   `detail_z >= top_z - 0.05` the whole face is block masonry with a flush coping course. Result: the back and side
   views now show coursed big blocks, as in ref4.
2. **20.4 % hidden (over the 15 % limit).** About 58k triangles of the old figure were the quay's rubble stones, which
   `hidden_tris.py` counts as buried (centroid below Z = -0.05) even on the visible water face. Fix: the block quay
   (19.4k rubble triangles replaced by about 5k block triangles) and a quay shortened from 23.9 m to 18.8 m (the
   stretch west of the hall carried nothing). Result: **13.5 %** (4.3 % of it below the datum).
3. **Timid cruck.** Heavier members (post 0.30, arch 0.34, blade 0.40, tie 0.32, collar 0.26), the frame 6 cm proud
   of the stone, the infill 15-18 cm behind the member faces, and a new `pointed=True` two-centred inner arch in place
   of the thin quarter-ellipse collar braces (`braces=False`). New `cruck_frame` options are `brace`, `pointed`,
   `pointed_t` and `pointed_at`.
4. **Thin tower top.** The cone eave was raised from 7.90 to 8.60 (`KIT eave_z`), so the timber storey is 1.70 m, with
   four lookouts.
5. **Softer roof.** ridge_sag 0.15 -> 0.24, eave_sag 0.05 -> 0.08, eave_sweep 0.22 -> 0.28; wing ridge_sag 0.08 ->
   0.14 and sweep 0.14 -> 0.18. These are recipe values only.
6. **A 10th material slot (`M_rubble`)** appeared in the 12:30 interim build from the block core. The core now uses
   `M_stone`, so the palette is back to 9 slots.

### Existing kit modules used (reuse table)

| Module | Used for |
|---|---|
| `assembly.build_building`, `KitParams` | the build pipeline and the two dimension tables |
| `frame.RoundFrame` | the tower / cone frame |
| `rubble_walls.path_stone_wall` (+ `RUBBLE_LARGE`, `base=`) | hall, water-gable piers, wing |
| `rubble_walls.round_stone_body` | the tower |
| `stone_wall` (through rubble_walls) | the one rubble generator, mortar, footing, quoins |
| `wall_openings.build_opening`, `door_spec`, `window_spec` | every door and window in stone, and (host=) in timber; steps, frames, dressed reveals |
| `openings.window` | the tower lookouts |
| `plank_doors.plank_leaf`, `strap_widths`, `make_pintle` | every leaf and shutter, straps and pintles (through wall_openings) |
| `linear_roof.GableRoof`, `linear_roof` | main and wing roofs: shingle covering, starter, comb ridge, rafters, deck, eave roll, verge boards, apex finials |
| `shingles.SIZE_TABLE` | the village shingle and comb sizes |
| `finial.finial`, `turned_finial`, `lead_hat` | spike finial on the cone; turned finials on lead hats at the gable apexes |
| `composite.cone_roof` | the mossy shingle cone |
| `cone.age_defaults(**AGE_R10)` | the village's age / moss settings on the cone |
| `board_belt.board_belt` (+ `body=`) | the tower's timber top storey (drum / tier band family) |
| `roof_junction.wall_abutment`, `round_eave_fill`, `LINEAR_ROOF_PARTS` | roof to tower junctions, the cone eave fill |
| `composite.inside_box`, `inside_round`, `set_entrance`, `recenter` | clips and placement |
| `composite.composite_hidden_cull`, `composite_decals` (+ `timber=`, `waterfront=`) | cull, decal anchors |
| guards (clearance, seal_probe, decal_validate, steep_cone_door, lod_scope), `uvgrain`, `mask`, `geom` | gates, grain UVs, Mask, mesh hygiene |

**Existing modules changed** (optional parameters or new functions, defaults = kit 1.11.0 behaviour; made by the first
fixer before 11:08): `linear_roof`, `rubble_walls`, `wall_openings`, `board_belt`, `composite`. The relaunched fixer
changed no existing module. It touched only the v5 modules `cruck.py` and `waterfront.py`.

**New modules, and why nothing existing could make them**

| New | Why |
|---|---|
| `cruck.cruck_frame` | Nothing in the kit builds curved timber members, a timber-framed arch or a gable frame over an opening. The keep's hewn / timber pieces are straight posts, plates and braces. |
| `waterfront.pile_deck`, `pile`, `ladder` (round 1) | Nothing makes piles, a plank deck or a ladder. |
| `waterfront.stone_quay` (+ `_core_blocks`) | A thin wrapper on `path_stone_wall` (water-only runs from the bed, `g.QUAYS` for the waterline anchors). The block core is new because a 2.5 m rubble face below the datum would be about 60k "buried" triangles. |
| `timber_walls.path_timber_wall` (round 1, reworked) | A new wall FORM. Its openings and hardware are the kit's (`wall_openings` host). |
| `floor_stack` (round 1, unchanged, not used here) | The jettied storey for the barn / harbour-house variants. |

### Note-16 record (same builders, techniques and materials)

- **Reused as-is:**
  - the 9-slot palette (`M_stone`, `M_stone_dressed`, `M_mortar`, `M_timber`, `M_timber_weathered`, `M_roof_shingle`, `M_roof_shake`, `M_iron`, `M_lead`; no new material);
  - the village coursed rubble, footing, quoins and dressed reveals (`stone_wall` via `rubble_walls`);
  - the door and window frames, thresholds and steps, plank leaves, forged straps and pintles (`wall_openings` / `plank_doors`);
  - the kit shingles and comb ridge (`SIZE_TABLE`), the eave roll and rafters (`linear_roof`);
  - the mossy shingle cone and its age (`cone_roof`, `AGE_R10`);
  - the turned and spike finials and lead hats (`finial`);
  - the lead abutment flashing (`wall_abutment`);
  - the board belt and hewn rings of the drum family (`board_belt`);
  - the decal / moss anchor recipe (`composite_decals`).
- **Still differs (new forms, not new style):**
  - the cruck frame's curved members, a form found on no other building;
  - the curved, apex-flared bargeboards, the first timber bargeboard in the village (the other buildings close their verges with thatch rolls, shake aprons or cone eaves);
  - the soft-roof warp itself;
  - the quay's squared big blocks (the village has no quay; ref4 shows big squared blocks, not rubble);
  - the jetty piles and deck.

  None of these introduces a new material or detail vocabulary. Iron dog plates on the jetty use `M_iron`.

### Hash rule

- **Run 1, `kit/baseline/v5r2_hash/`** (first fixer, 10:52-11:28, all seven): every geometry, UV and Mask hash equals
  the kit 1.11.0 table.

  | Building | Triangles | Geometry hash |
  |---|---|---|
  | hilltop_keep | 1,166,874 | `3e2a219a5901afc5` |
  | wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` |
  | tower_windmill | 1,146,243 | `89bf4a2a2c60e049` |
  | v1_stone_watchtower | 937,933 | `465c7b1b8a7dbb22` |
  | v2_tiered_hall | 980,405 | `9522f17ed8b09646` |
  | v3_longhouse_roundend | 617,342 | `38ff44b686efd26b` |
  | v4_mixed | 938,453 | `2e87caad61b68d34` |

- **Why a second run:** `rubble_walls` was edited at 11:06, after the keep, roundhut and windmill builds of that run
  had started (10:52 / 10:57 / 11:05), and `board_belt` at 10:59, after the keep and roundhut builds had started. v1-v4 started after the
  last edit to an existing module.
- **Run 2, `kit/baseline/v5r2b_hash/`** (12:13-12:30): those three were rebuilt with the final kit (`-Only
  hilltop_keep,wattle_roundhut,tower_windmill -MaxParallel 1`). The result is identical: `3e2a219a5901afc5` /
  `10326b66883e3031` / `cacc4885b10b1370`, `7e5e7c2df5c4d367` / `c97c88e742be4887` / `46bb1454fa4d264e`, and
  `89bf4a2a2c60e049` / `b006e70c2dc4750b` / `3c0753f38798dad6`.
- **Result: all seven buildings MATCH** the 1.11.0 reference (geometry, UV and Mask). The relaunched fixer's own
  edits are in v5-only modules (`cruck`, `waterfront`), which no other building imports.

### Stats (round_02 `stats.json`, 12:46)

| Measure | Value |
|---|---|
| Triangles | **699,138** (note-15 cap 1,000,000) |
| `est_hidden_pct` | **13.5 %** (4.3 % of all triangles are below Z = -0.05, which the tool counts as buried: the quay face, piles and ladder) |
| Material slots | 9, all in the palette |
| `mask_attribute_missing` | none |
| Objects | 68 (0 pooled: the stone-host windows have no pintles) |
| bbox | 16.59 x 17.17 x 15.94 m (bed to the spike finial; 13.44 m above the quay) |
| Build time (cull included) | 13.1 min |
| Decal anchors | 110 kept of 176 by the kit gate (131 composite + 28 timber + 17 waterfront; applied) |
| Guards | Clearance PASS at the hall door (eave lip 5.52 m) and the wing door (2.50 m against a 2.22 m head, rule >= 2.30). Seal probe: 0 leaks on roof / tower and wing roof / tower (101,613 rays). Steep-cone and lod-scope: no opt-outs. |

**Barn smoke (family proof, not a deliverable):** `buildings/variants/v5_harbour_house/scratch/barn_smoke/build_barn_smoke.py`
(30 lines). A post-and-plank barn on a rubble plinth with a clamp boat door, a trim boat door, two shuttered windows
and a soft shingle roof with finials. It was rebuilt at 12:4x with the final kit
(`scratch/barn_smoke2/`, 211,691 tris, 20 pooled pintle instances, both clearance gates PASS).

### Known gaps

- **Review-tool datum:** the clay views put the ground at the bed, so the building floats 2.5 m up. The land side of
  the slip-return blocks and the open land behind the quay are visible from below, where UE terrain would bury them.
  A `--ground_z` option for render_review is still the producer nice-to-have.
- **Not built (recipe choice):** the eyebrow dormer, the curved stair round the tower and the small round store.
- **The roof is still steeper than ref4's** (58 deg, so the brief's 8.5-9.5 m ridge band holds). Its sag (24 cm), its
  swept eaves and its apex flare are all visible in the side view, but ref4's slump is more exaggerated.
- **Cruck:** symmetric about the gable centre, one opening per frame. The pointed arch and the blades meet the tie and
  king strut by interpenetration (no modelled joints; note 12: no finer detail).
- **`GableRoof` warp:** vertical only, with no plan bow of the eave line. `ref_z` / `under_z` stay the straight
  profile (use `under_z_world`).
- **Retired files:** `timber_roof.py` and `timber_finish.py` remain as `NotImplementedError` stubs for the producer to
  delete at the merge.
- Kit changes are recorded in `kit/changes/v5_harbour_house.md` (proposed 1.12.0), not in CHANGELOG.md.

## v5_harbour_house round 2 — score 7.8/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note
10), no surface-detail requests (note 12). Binding: producer notes 1-17, every CLIENT DIRECTION entry above (ref4 is
the primary reference) and the reuse mandate. No new CLIENT DIRECTION or PRODUCER NOTE after the 12:10 relaunch note.

**Reviewed:**
- All six `round_02` views (12:44-12:45), `stats.json`, `hidden.json`, `decal_anchors.json` (110 anchors plus the
  validation block) and the r2c_full build log.
- The recipe (158 lines), `cruck.py`, `waterfront.py`, the barn smoke recipe and its renders and log (`barn_smoke2`,
  211,691 tris, 20 pooled pintles, both head-rule gates), the hash-rule folders `kit/baseline/v5r2_hash` and
  `v5r2b_hash`, and ref4 / ref1-ref3.
- Director extras in `renders/variants/v5_harbour_house/round_02/director_extra/`:
  - 34 views, x01-x34, staged with the land at the quay datum (top -0.045), a water plane at -0.9 and 1.8 m figures
    at both doors, on the jetty and on the quay;
  - 25 red see-through twins;
  - the note-16 line-up L01-L03 (keep, roundhut, longhouse, harbour house);
  - three probes: `probe_r02_out.txt` (objects, transforms, Mask, islands, junction rays, anchor occlusion),
    `probe2_r02_out.txt` (hole scans of every quay face, the slip and the water gable) and `pick_out.txt`
    (pixel picks in the nook).

**Director-verified compliance:**
- 68 meshes, all with identity transforms, a UV map and an active `Mask` (CORNER, BYTE_COLOR). 9 palette slots.
- Collections `HARB`, `HARB_kit_instances` (empty) and `DECAL_ANCHORS` (110 empties).
- 699,138 tris and 13.5 % hidden, both inside the limits.
- Clean red twins: both roof-to-tower abutments (x07, x08, x09, x10, x11), the tower and wing stone junctions (x04,
  x05), both eaves (x23, x24), the water and land apexes (x21, x25), the wing's free gable (x26), the tie at the pier
  (x16), the eave corner (x22) and the jetty deck at the quay (x30).
- The tie beam bears on the pier quoins (1 cm, ray probe). The arch sits under the tie. The partition foot sits on the
  slip-head coping.

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.0 | From the water (x01, x15, `back.png`) this is now recognisably the ref4 building: a rubble boat hall with a heavy timber water gable over a segmental boat arch; a round rubble tower with a 1.7 m boarded top storey and four lookouts under a mossy cone with a spike; a lower wing; a soft roof (24 cm ridge sag, swept eaves, apex-flared bargeboards: x21, x34); a block quay and a jetty on piles. Note 17 is met by integral round and soft forms. Held back for three reasons. (a) The 6.0 m, 58 deg gable is narrower and taller than ref4's broad, slumped hall. (b) The inset two-centred pointed arch, with the king strut and collar crossing inside it, reads as a chapel lancet with a cross (x01, x15). (c) From the land (x02, `front.png`, L02) it is the longhouse formula again: a rubble block plus a round rubble tower with a cone. |
| 2 Proportion and actor scale | 8.3 | Both doors are 1.00 x 2.10 m on built-in thresholds next to the figure (x03, x06). Windows are 0.55 m at 1.30 m sills. The wing eave lip sits 2.50 m over a 2.22 m head (rule 2.30: passes, though tight). The boat arch is 4.6 m clear with its crown at 3.03 m, about 3.9 m over a -0.9 m tide. The figure on the jetty reads right (x15, x30). The slip is only 3.2 m deep to the partition, short for the 4-5 m boats ref4 moors inside, and has no ledge to step ashore. |
| 3 Construction logic | 7.6 | Mostly carried and built: the tie on the pier quoins, a segmental arch under the tie, blades along the rake, plank infill 15-18 cm behind the members, roofs on the wall heads (deck + 2 cm), and the tower's timber storey on a hewn foot ring over the stone top (x12). The jetty has bearers on piles, a ledger at the quay face, bracing and a ladder. Two faults. **(a) The jamb posts hang over the water.** `cruck_frame` designs 0.30 m dressed pads (z -0.30 to 0), but the pads are finalised with the kit's default -0.05 clip and come out as 5 cm plates (`HARB_water_gable_pads` bbox z -0.05 to 0.00). They cantilever about 0.35 m off the quay corners into the slip, and each 0.30 m post carrying the arch stands on one (x17, x18, x32; the ray below each pad hits nothing). **(b) The slip walls' footing stones overhang the water.** The hall walls along the slip and the water-face piers stand flush on the quay face, and `path_stone_wall`'s projecting rounded footing stones hang over the quay edge (x17, x32). Minor: the jetty X-braces stand about 1 cm off the piles, and the waling about 0.5 cm off the braces (probe islands). |
| 4 Seams and junctions | 7.5 | The roof-to-tower seals are clean in every red twin and in the kit seal probe (0 leaks in 101,613 rays). The eave strips, verges, apexes, tie bearing and deck-to-coping are closed. Defects: **(a) See-through quay joints.** `composite_hidden_cull` removed 624 polygons from `HARB_quay_core`, including the recessed joint backing behind visible joints. Red pixels show through the joints of the slip head and both slip returns (x19_red, x32_red) and of the outer face (x33_red). The probe2 hole scans pass through on 20 of 336 rays (east slip return), 46 of 336 (west return), 15 of 480 (slip head) and 52 of 848 (outer face), along whole bed joints at z -0.3, -0.6, -0.9 and -1.95. **(b) Unbonded quay corners at the slip mouth.** At x -0.41 and 4.19 (y 3.43), `_core_blocks` lays each run on its own and stops it 2 cm past the corner, so a full-height vertical slot shows the backing (x17, x18, x32). Minor: both free quay ends (x -4.31 and 8.29) are raw cut ends (x27, x28). The lead abutment flashings end in boxy tabs on the tower face in the nook (x10, x11). |
| 5 Distinctness and reuse | 8.1 | **Existing modules used:** `assembly.build_building` / `KitParams`, `RoundFrame`, `rubble_walls.path_stone_wall` (`RUBBLE_LARGE`, `base=`) and `round_stone_body`, `wall_openings.door_spec / window_spec`, `openings.window`, `plank_doors` (through `wall_openings`), `linear_roof.GableRoof` + `linear_roof` with the new soft options, `shingles.SIZE_TABLE`, `finial` (spike, turned, lead hat), `composite.cone_roof`, `cone.age_defaults(AGE_R10)`, `board_belt(body=)`, `roof_junction.wall_abutment / round_eave_fill`, the composite cull / decals / clips / recenter, guards, `uvgrain`, `mask` and `geom`. **New, each justified:** `cruck.cruck_frame` (nothing in the kit makes curved members or a timber arch); `waterfront.stone_quay` (a wrapper on `path_stone_wall` plus a block core); `pile_deck` / `ladder`. The duplicates of round 1 are retired: `_build_opening` now goes through `wall_openings(host=)`, `verge_boards` through `linear_roof(verge=)` and `timber_finish` through composite options. The hash rule holds on all seven buildings. The soft-roof warp is an option on the existing roof, as note 17 asks. It reads as the same village in the line-up (L01-L03), with the same rubble, shingle, cone, finials and lead. **Family verdict:** the timber half (`path_timber_wall`, the `wall_openings` timber host with the clamp / trim head rules, the soft `GableRoof`) is genuinely reusable, proven by a 30-line barn smoke recipe. The waterfront half (`cruck_frame`, `stone_quay`, `pile_deck`) is parameterised and plane-agnostic, not one-off code, but no second recipe has exercised it yet, and the faults under axes 3 and 4 (pad clip, corner bond, cull, free ends, `pile_deck` land S / N only) would follow it into the boathouse. Points off for the land-side likeness to the v3 longhouse. |
| 6 Technical compliance | 7.9 | 699,138 tris (cap 1 M). 13.5 % hidden (4.3 % below the datum). 9 palette slots, `Mask` everywhere, identity transforms. Deterministic, the datum recorded in the anchors JSON, and the hash rule documented in two runs. 110 anchors, physically plausible: damp and moss on the quay water faces between -0.35 and -0.72 and on the slip walls, streaks under the cone eave and on the posts, lichen on the coping. One crack (DA_crack_021) sits just under the wing eave, which is harmless. **Producer note 6 is broken** ("Never open holes when culling"): the cull opened the quay joints (axis 4a). Pooling is still 0 in the house itself: dog plates and the door irons are unique (note 3, minor). |

**Verdict: 7.8/10, NOT PASSED (pass mark 8.2).** A large step from 6.3. This is now the client's ref4 building,
assembled almost entirely from existing kit modules. The note-17 softness lives as options on the existing roof. The
round-1 duplicates are retired, the hash rule holds, and every roof junction is sealed. What keeps it under the
mark is concentrated at the waterline. The cruck's jamb posts stand on 5 cm stone plates hanging over the slip,
because the kit clipped the pads. The cull opened the quay joints into see-through slits, against note 6. The quay
corners at the slip mouth are unbonded slots. The slip walls' footing stones overhang the water. All four are kit
bugs in modules the boathouse will reuse, so fix them in the modules, not in the recipe.

**Strengths**
- Reuse discipline: the round-1 duplicates are folded in. Every opening goes through `wall_openings`, every verge
  through `linear_roof`, and the cull and decals through composite options. The softness is an option on
  `GableRoof` with bit-identical defaults, proven on all seven buildings in two hash runs.
- The roof reads soft and village-like (x21, x34): a sagging comb ridge between turned finials on lead hats,
  apex-flared curved bargeboards and swept eaves. Its junctions with the tower are sealed (0 leaks, clean red twins
  in the nook and on both slopes).
- The water gable is now bold. Heavy posts, a 0.34 m segmental arch, a 0.32 m tie on the pier quoins, 0.40 m blades
  and an inner pointed arch, all proud of rough, set-back plank infill (x15, x16, x20).
- The tower is built from the kit's round family: `round_stone_body`, `board_belt(body=)` with four lookouts, a
  mossy `cone_roof` with `AGE_R10` and the spike finial. It is integral to the plan, and both roofs abut it.
- The quay now reads as ref4's big blocks at about 1 % of the old rubble triangles, and hidden geometry dropped from
  20.4 % to 13.5 %.
- The family proof is real: a 30-line barn recipe with both large-door head rules, gated effective heads and pooled
  pintles.

**Must-fix (round 3)**
1. **The cruck jamb posts must bear on stone, not on clipped plates over the water.** The module is
   `cruck.cruck_frame`, and the faulty pieces are `HARB_water_gable_pads` at x -0.44 to 0.00 and 3.80 to 4.22, y 3.06
   to 3.54 (after the recentre).
   - What is wrong: the pads are designed z -0.30 to 0, but `finalize(..., clip_z=CLIP_Z)` cuts them at -0.05, so
     each 0.30 m post carrying the arch stands on a 5 cm dressed plate that cantilevers about 0.35 m off the quay
     corner over the slip (x17, x18, x32).
   - What it should be: two changes.
     - Give `cruck_frame` a `pad_clip_z` / `clip_z` parameter, and finalise the pads with it. The default keeps
       today's behaviour.
     - Seat the posts so that at least 0.25 m of each post's depth bears on the quay coping or the pier (move them
       onto the jamb line). Alternatively, carry each pad down the quay corner as a dressed respond to the bed.
     - A post must visibly stand on masonry from every water-level view.
2. **No see-through quay joints (producer note 6, "never open holes when culling").** The fault is in
   `waterfront.stone_quay(core_blocks=True)` together with `composite_hidden_cull`, in `HARB_quay_core`.
   - What is wrong: the cull removed 624 polygons from the quay core, including the recessed joint backing (w -0.20
     to -0.07) behind joints that ARE visible. Red shows through the bed and head joints of the slip head (y 0.23),
     both slip returns (x -0.41 / 4.19) and the outer face (y 3.43). See x19_red, x32_red and x33_red, and the
     133 pass-through rays in `probe2_r02_out.txt`.
   - What it should be:
     - Build the joint backing as its own object (e.g. `<P>_<name>_backing`).
     - Exclude it from the cull, the way the kit protects its other backing sheets.
     - Re-run the red twins at the slip and the outer face: zero red pixels inside the quay outline.
3. **Bond the quay's convex corners.** The fault is in `waterfront._core_blocks` / `stone_quay` at the slip mouth,
   x -0.41 and x 4.19, y 3.43, z -2.5 to -0.04.
   - What is wrong: each run is laid on its own and extended only 2 cm past a convex corner, so a full-height
     vertical slot shows the backing at both corners (x17, x18, x32).
   - What it should be:
     - On alternate courses, the end block of one run overruns the corner by the block depth (0.30 m), and the
       other run's face butts it, as a quoin bond.
     - The backing is closed round the corner, with no vertical joint wider than the 2.2 cm course joint.
4. **No footing overhang on walls that stand flush on a quay face.** The fault is in
   `rubble_walls.path_stone_wall` as used by the hall: the slip side walls at x -0.41 / 4.19 for y 0.23 to 3.43, and
   the water-face piers at y 3.43.
   - What is wrong: the walls stand flush on the stone_quay water face, but their rounded footing stones project
     past it and hang over the water (x17, x32).
   - What it should be: an optional per-run footing control, e.g. `footing_out=0` / `footing=False` for listed runs,
     defaults unchanged (hash rule). Use it on the runs that stand on a quay face, or set those runs back from the
     quay face by the footing projection.

**Nice-to-have**
- `stone_quay`: an `ends=` option ("return": a 1 m return into the land; or "squared": header blocks) so the free
  ends at x -4.31 and 8.29 are not raw cut ends (x27, x28).
- Break the "lancet with a cross" read of the water gable (x01, x15). Stop the king strut at the pointed arch's
  apex, or replace the inset two-centred arch with curved blades that rise from the tie ends along the rake, closer
  to ref4's crucks. Bible 1.8 allows only round or segmental arches; ref4 overrides that for this frame, but it
  should read as timber framing, not church tracery.
- Closer to ref4's slump: the hall is 6.0 m wide under a 58 deg pitch. Try 6.6-7.0 m wide at 52-54 deg with
  `ridge_sag` 0.35-0.45, keeping the ridge in the 8.5-9.5 m band.
- Slip: about 4.5-5 m deep to the partition, and a short timber landing ledge along one side (`pile_deck`) so a
  boat can moor and a person can step ashore.
- A boathouse smoke recipe that exercises `cruck_frame` + `stone_quay` + `pile_deck`, as the barn smoke does for the
  timber half.
- `pile_deck`: accept `land="E" / "W"` (still raises), seat the X-braces and the waling on the piles (they stand
  about 1 cm and 0.5 cm off), and pool the dog plates (note 3).
- `wall_abutment`: end the lead flashing at the eave lip instead of the boxy tabs on the tower face in the nook (x10,
  x11).
- Shutters on a few of the stone-wall windows: the brief asks for "small shuttered windows", and the kit's stone
  host has them.
- `tools/render_review.py --ground_z` (producer tool): the six main views still float the building 2.5 m.
## CLIENT DIRECTION (2026-10-17, session 2, after the round-2 grade): a broader, slumped roof is must-fix in round 3

After reading the round-2 grade, the client chose, as their own direction: **"Broader, slumped roof"**. It is a MUST-FIX for round 3, alongside the director's four waterline must-fixes.
- Make the hall about **6.6-7.0 m wide** (it is 6.0) at about **52-54 deg** (it is 58), with **`ridge_sag` about 0.35-0.45 m** (it is 0.24). Keep the ridge in the 8.5-9.5 m band and keep the swept eaves and flared verges. The aim is ref4's heavy, slumped hall roof that dominates the building.
- Rework whatever the wider hall moves (the cruck span, the quay and slip, the roof-to-tower abutment, the wing) so that everything stays sealed and carried. The note-15 cap and the hash rule still apply.
- **Not chosen by the client this round:** the gable "lancet" rework, the deeper slip and ledge, and the curved stair / eyebrow dormer. These stay the director's nice-to-haves: do them only if they come cheaply and safely, and never at the expense of the must-fixes.
## v5_harbour_house round 3 — builder entry

**Built:** the round-2 ref4 boat hall, with the four waterline must-fixes made **in the kit modules**, so a boathouse
recipe inherits them. Nothing else in the massing changed. No CLIENT DIRECTION or PRODUCER NOTE was added after the
round-2 grade.

- **Recipe:** `buildings/variants/v5_harbour_house/build_v5_harbour_house.py` (165 lines, 144 non-blank non-comment).
  The round-3 changes are 4 recipe values: `ON_QUAY = (0, 1, 5, 6)`, `flush_runs=ON_QUAY` on the hall, and
  `respond_z=DIM["bed"]` and `king_strut=False` on the cruck. It writes `v5_harbour_house.blend` (18.0 MB, compressed)
  and `decal_anchors.json` (113 anchors).
- **Renders:** `renders/variants/v5_harbour_house/round_03/` (all six views, `--samples 24`), with `stats.json` and
  `hidden.json`. Builder close-ups at water level are in `round_03/builder_extra/` (`r3_slip_mouth`, `r3_corner_W`,
  `r3_corner_E`, `r3_outer_W`, `r3_gable`).
- **Datum (unchanged):**
  - quay and landward ground at Z = 0;
  - coping and wall footings at -0.04;
  - harbour bed at -2.5;
  - recentre shift (-1.308, -5.973);
  - the water gable faces +Y.

  The review tool's ground plane is still at the bed, so the six main views float the building by 2.5 m. That is
  the tool, not the model.

### Must-fix list: what was done

| # | Must-fix | Fix (module) | Check |
|---|---|---|---|
| 1 | Cruck jamb posts on 5 cm plates over the slip | `cruck.cruck_frame(pad_clip_z=None, respond_z=None, respond_ch=(0.40, 0.56))`. The pads are finalised with `pad_clip_z`; the default keeps the kit's -5 cm clip, so the round-2 behaviour stands. With `respond_z` set, each pad (now its full designed 0.30 m, z -0.30 to 0) is **carried down to the bed as a dressed respond**. That is 9 courses in all, with 1.2 cm joints and alternate courses set back 1.5 cm, closed by an inset core `HARB_water_gable_respond_blocker` (never culled). The responds stand against the quay corner and bond 2 cm into the quay blocks. | Probe `scratch/probe_r3.py` on the final blend: horizontal rays from the slip centre hit the respond face (`_pads`, 1.91-1.93 m) at every station from -2.40 to -0.05, both sides; above 0 they hit the post (1.95-1.96 m). A ray down from the post foot hits masonry at once (respond core 0.29 m below the pad top). See `r3_slip_mouth.png`: each post stands on a stone pier from the bed. |
| 2 | See-through quay joints after the cull (note 6) | `waterfront.stone_quay(core_blocks=True)`: the joint backing is its own object, **`HARB_quay_backing_blocker`** (266 faces). Its name falls in `composite.BACKING`, so `composite_hidden_cull` never targets it. The cull still trims the block core (`HARB_quay_core`: -566 of 4,428 polygons). | Probe (B), 5 cm x 2.5 cm grids of rays into every quay face from 30 cm out: **0 pass-through** on the outer face west (7,220 rays) and east (6,935), both slip returns (5,320 each) and the slip head (8,645). The same probe on the round-2 blend gives 359 / 391 / 256 / 291 / 508 pass-throughs, so the probe does catch the fault. |
| 3 | Unbonded slip-mouth corners | `waterfront._core_blocks(courses=, quoin=)` and `_block_courses`. The course beds are drawn once per face group and shared by its runs. At every CONVEX corner the two runs take opposite parities: on each course one run's end block runs through the corner to the other face (its end face is flush on that face, overrunning by the 0.30 m block depth), and the other run butts its back with a 1.1 cm joint. The backing on each run stops at the other run's backing face, so it is closed round the corner with nothing past either face. Plain ends and concave corners are unchanged. | Log: "2 convex corner(s) quoin-bonded". Probe (D): no diagonal ray at either corner arris gets in. On the round-2 blend the east corner ray passes straight through the slot. See `r3_corner_E.png` / `r3_corner_W.png`: long-and-short quoin bond, no vertical slot. |
| 4 | Footing stones overhanging the water | **`rubble_walls.path_stone_wall(flush_runs=None)`** (existing module; a new optional parameter, default = the old code path). The listed runs' footing course is laid flush: the same course height and lengths, the kit `front` projection, no field-stone bulge. The hall uses `flush_runs=(0, 1, 5, 6)`: both slip walls and both water piers (8 footing stones made flush). The land walls keep the village's stepped projecting footing. | Probe (C): rays straight down 6 cm off the quay faces under those runs hit **nothing above z -0.30** (the only hits are the partition sill on the slip-head coping and the respond pad, both by design). On the round-2 blend, 128 and 120 of 136 rays hit hall footing stones at about z 0.26. |

**Also done (from the nice-to-have list, small):** `cruck_frame(king_strut=True)`. With `king_strut=False` (recipe) the tie-to-collar strut inside the pointed arch is gone, so the water gable reads as a pointed arched brace under the collar, not "a lancet with a cross" (`r3_gable.png`).

### Existing kit modules changed

- `rubble_walls.path_stone_wall`: `flush_runs=None` (above). With `None` the call takes exactly the kit 1.11 / round-2 path.
- v5-only modules (no other building imports them): `cruck.cruck_frame` (`pad_clip_z`, `respond_z`, `respond_ch`, `king_strut`), and `waterfront.stone_quay` / `_core_blocks` / `_block_courses` (backing object, quoin bond).
- All recorded in `kit/changes/v5_harbour_house.md` (a new "Round 3" section).

### Hash rule

`kit/baseline/v5r3_hash/` (`build_baseline.ps1 -Step v5r3_hash -MaxParallel 1`, 13:09-13:45). It started after the
last `rubble_walls` edit (13:05). **All seven MATCH the kit 1.11.0 reference** (`6_r8kit_check`) on geometry, UV and
Mask:

| Building | Triangles | Geometry hash |
|---|---|---|
| hilltop_keep | 1,166,874 | `3e2a219a5901afc5` |
| wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` |
| tower_windmill | 1,146,243 | `89bf4a2a2c60e049` |
| v1_stone_watchtower | 937,933 | `465c7b1b8a7dbb22` |
| v2_tiered_hall | 980,405 | `9522f17ed8b09646` |
| v3_longhouse_roundend | 617,342 | `38ff44b686efd26b` |
| v4_mixed | 938,453 | `2e87caad61b68d34` |

### Stats (round_03 `stats.json`)

| Measure | Value |
|---|---|
| Triangles | **695,470** (note-15 cap 1,000,000) |
| `est_hidden_pct` | **14.2 %**, under the 15 % limit; 1.9 % is below the datum. It was 13.5 %: the protected quay backing and the respond cores are counted as hidden. |
| Material slots | 9, all in the palette (no new material) |
| `mask_attribute_missing` | none |
| Objects | 70: +`HARB_quay_backing_blocker`, +`HARB_water_gable_respond_blocker` |
| bbox | 16.59 x 17.17 x 15.94 m (unchanged) |
| Build time (cull included) | 13.5 min |
| Decal anchors | 113 kept of 176 by the kit gate |
| Guards | Clearance PASS at both doors (eave lips 5.52 / 2.50 m). Seal probe: 0 leaks on roof / tower and wing roof / tower. Steep-cone and lod-scope: no opt-outs. |

### Known gaps

- **Review-tool datum:** the clay views still put the ground at the bed (a producer `--ground_z` nice-to-have).
- **Quay free ends** at x -4.31 and 8.29 are still cut ends, with no `ends=` option. In UE the terrain continues the quay.
- **Not attempted this round (nice-to-haves):**
  - the broader, lower 52-54 deg hall;
  - a deeper slip with a landing ledge;
  - a boathouse smoke recipe for `cruck_frame` + `stone_quay` + `pile_deck`;
  - `pile_deck` E / W land sides and brace seating;
  - the `wall_abutment` flashing tabs;
  - shutters on the stone windows.
- **The responds narrow the clear width at water level** from 4.6 m to 3.8 m between the pads. The arch above is unchanged.
- The cruck posts stand 4 cm off the slip-wall face (as designed in round 2). The post-to-wall gap is visible from inside the slip.

## PRODUCER NOTE (2026-10-17, session 2, 13:48): round 3 missed the client's roof must-fix; it cannot be accepted without it

The round-3 fixer started at about 13:05, before the client's 13:21 CLIENT DIRECTION above ("Broader, slumped roof", a MUST-FIX for round 3). It did not see it: its entry says "No CLIENT DIRECTION ... after the round-2 grade" and lists the broader, lower hall as not attempted.

- **Art Director (round-3 grade):** the client's direction is binding. Grade round 3 as built, but list the broader, slumped roof as an open must-fix. **Round 3 cannot pass while it is open**, however well the waterline fixes score: give at most 8.1 if everything else passes.
- **Round-4 fixer:** do the broader, slumped roof first (hall about 6.6-7.0 m wide, 52-54 deg, `ridge_sag` 0.35-0.45, ridge in the 8.5-9.5 m band), keeping every round-3 waterline fix.

## v5_harbour_house round 3 — score 8.0/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note
10), no surface-detail requests (note 12). Binding: producer notes 1-17, every CLIENT DIRECTION entry above (ref4 is
the primary reference), the PRODUCER NOTE of 13:48, the reuse mandate and **the client's round-3 must-fix "Broader, slumped roof"** (the CLIENT
DIRECTION entry after the round-2 grade).

**Reviewed:**
- All six `round_03` views, `stats.json`, `hidden.json`, `decal_anchors.json` (113 anchors plus the validation
  block), the six builder extras, the recipe (165 lines), the round-3 section of `kit/changes/v5_harbour_house.md`,
  `cruck.py`, `waterfront.py` and `rubble_walls.path_stone_wall(flush_runs=)`, and ref4 / ref1-ref3.
- Hash rule checked by the director: all seven `kit/baseline/v5r3_hash/*.json` match `6_r8kit_check` on geometry and
  triangles (keep 3e2a219a5901afc5, roundhut 7e5e7c2df5c4d367, windmill 89bf4a2a2c60e049, v1 465c7b1b8a7dbb22, v2
  9522f17ed8b09646, v3 38ff44b686efd26b, v4 2e87caad61b68d34).
- Director extras in `renders/variants/v5_harbour_house/round_03/director_extra/`:
  - the round-2 set x01-x34 re-shot on the round-3 blend (same staging: land at the quay datum, water plane at -0.9,
    1.8 m figures), plus 15 new waterline shots, y01-y15 (the slip mouth, both responds from the slip and from the
    water, both post feet, a grazing view along a respond bed joint, the post-to-wall slot, the slip-head corners,
    both convex corners on the diagonal, the west free end, a high ref4 angle and a land three-quarter at eye level);
    `_nowater` shots hide the water plane so the responds and the quay can be read down to the bed;
  - 39 red see-through twins, pixel-counted against round 2 (identical counts at every roof, tower and wing junction,
    so nothing moved there);
  - two probes: `probe_r03_out.txt` (objects, transforms, Mask, junction rays, islands, anchor occlusion) and
    `probe2_r03_out.txt` (the round-2 hole scans plus new respond, post-foot, corner-diagonal and footing scans).

**Director-verified compliance:** 70 meshes, all with identity transforms, a UV map and an active `Mask` (CORNER,
BYTE_COLOR). 9 palette slots. Collections `HARB` (70), `HARB_kit_instances` (empty), `DECAL_ANCHORS` (113).
695,470 tris, 14.2 % hidden (1.9 % below the datum).

**The four round-2 must-fixes, checked:**

| # | round-2 must-fix | director check | result |
|---|---|---|---|
| 1 | Cruck posts on 5 cm plates over the slip | `HARB_water_gable_pads` now spans z -2.50 to 0.00, on an inset `_respond_blocker` core. Rays down from both post feet hit the pad at 1 cm. Horizontal rays from the slip hit the respond face at every station from -2.45 to -0.20 on both sides. In y01, y02-y07 each post stands on a dressed pier from the bed, with a slightly proud capping pad. | **fixed** |
| 2 | See-through quay joints (note 6) | Hole scans: 0 misses on the slip returns, the slip head and the outer face (2,000 rays; round 2: 133). x32_red and x33_red show no red inside the quay outline. x19_red drops from 649 to 27 px (see the nice-to-haves). | **fixed** |
| 3 | Unbonded slip-mouth corners | Diagonal rays at 30, 45 and 60 deg at 8 heights on both convex corners: none gets in. y11 / y12 show a long-and-short quoin bond with no slot. | **fixed** |
| 4 | Footing overhang on the quay faces | Rays straight down 6 cm off the faces: 0 hits above z -0.30 on both piers. On the slip walls, the only hits are the respond pads and the post feet, by design. y06 shows the pier quoin bedded flush on the coping. | **fixed** |

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.0 | The massing has not changed since round 2. It is still recognisably ref4 from the water (x01, y14, `back.png`): a rubble boat hall, a heavy timber water gable over the boat arch, a round tower with a boarded top under a mossy cone and spike, a lower wing, and a block quay and jetty. With `king_strut=False` the gable now reads as a pointed arched brace under the collar, not "a lancet with a cross" (x15, `r3_gable`), though it is still faintly ecclesiastical. **The client's round-3 must-fix was not attempted.** The hall is still 6.0 m wide under a 58 deg pitch with a 0.24 m ridge sag (recipe `DIM half=3.0, pitch=58.0`, `MAIN ridge_sag=0.24`). In `side.png` and x34 the roof reads tall and steep, a pointed hat, not ref4's broad, heavy, slumped hall roof that dominates the building. From the land (`front.png`, y15, x02) it is still the longhouse formula: a rubble block plus a round rubble tower with a cone. |
| 2 Proportion and actor scale | 8.3 | Unchanged and right: both doors are 1.00 x 2.10 m on built-in thresholds (x03, x06), windows are 0.55 m at 1.30 m sills, and the wing eave sits 2.50 m over a 2.22 m head. The boat arch crown is at 3.03 m. The responds narrow the water-level clear width from 4.6 m to 3.8 m, which still passes a 4-5 m boat but makes the slip read tighter. The slip is still 3.2 m deep. |
| 3 Construction logic | 8.4 | The waterline is now built and carried. The posts stand on 0.30 m pads carried to the bed as nine-course dressed responds bonded into the quay. The walls on the quay faces have flush footings. The quay corners are bonded. The tie bears on the pier quoins (probe: 1 cm), the arch sits under the tie, and the partition sits on the slip-head coping. Left over from round 2: the posts stand 4 cm off the slip-wall face, a dark open slot from inside the slip (y09; closed behind, black in the red twin), and the jetty X-braces and waling stand about 1 cm and 0.5 cm off the piles. |
| 4 Seams and junctions | 8.3 | Every quay joint and corner is closed (table above). The roof-to-tower, wing-to-tower, eave, verge and apex junctions are unchanged, with identical red-pixel counts to round 2 and the builder's seal probe at 0 leaks. Minor: two pinholes of about 13 px each at the ends of the boarded partition where it meets the slip-head coping and the slip walls (x19_red, about x -0.41 / 4.19, y 0.23, z 0.04). The quay's free ends at x -4.31 / 8.29 are still raw cut ends (y13, x27, x28). The lead abutment flashings still end in boxy tabs in the nook (x10, x11). |
| 5 Distinctness and reuse | 8.2 | All four fixes are made in modules with old-behaviour defaults: `path_stone_wall(flush_runs=)` on an existing module (hash verified), `cruck_frame(pad_clip_z, respond_z, respond_ch, king_strut)`, and `stone_quay` / `_core_blocks` (shared course beds, quoin bond at convex corners, a never-culled `<P>_<name>_backing_blocker`). The boathouse inherits them. The rest of the round-2 module ledger stands. It still reads as the same village (the round-2 line-up L01-L03 holds, since the massing has not changed). **Family verdict:** genuinely modular, not one-off code. `cruck_frame` takes any origin and orientation (`O, t, n`); `stone_quay` takes any polyline of water runs and bonds whatever convex corners it meets; `pile_deck` takes any union of rectangles. The timber half is proven by the round-2 barn smoke recipe. The waterfront half is still exercised by only one recipe, `pile_deck` still accepts only `land="S"` / `"N"`, and the recipe hard-codes run lengths that should derive from `DIM` (see must-fix 1). Points off for that and for the land-side likeness to v3. |
| 6 Technical compliance | 8.4 | 695,470 tris (cap 1 M). 14.2 % hidden, under 15 % but with only 0.8 % headroom for the wider roof. 9 palette slots, `Mask` everywhere, identity transforms, deterministic, the datum in the anchors JSON, and the hash rule verified. 113 anchors, physically plausible (damp and moss on the quay water faces at -0.35 to -0.72, lichen on the copings, streaks under the cone eave). One crack (DA_crack_022) sits 25 cm under the wing eave, which is harmless. **Producer note 6 is now met** (no holes opened by the cull). Minor (note 3): the house still pools nothing; dog plates and door irons are unique. Process (not held against the builder): the fixer started at about 13:05, before the client's 13:21 roof direction (PRODUCER NOTE 13:48), so its entry's "no CLIENT DIRECTION" was true when it started. |

**Verdict: 8.0/10, NOT PASSED (pass mark 8.2).** The waterline is now right: all four round-2 must-fixes are fixed in
the kit modules, and I verified each with probes and red twins. The posts stand on stone from the bed, the quay is
closed and bonded, nothing overhangs the water, and the cull no longer opens holes. Every other junction is
unchanged and sealed. What keeps it under the mark is the client's own round-3 must-fix, the broader, slumped
roof, which was not attempted. The hall is still 6.0 m at 58 deg with a 0.24 m sag, and this is the main remaining
difference from ref4's silhouette. An open client must-fix cannot pass. Round 4 should be that change and its knock-on
re-seals, with nothing else.

**Strengths**
- The fixes are in the kit and the defaults are bit-identical. Each fix is a module option: `flush_runs`,
  `respond_z`, the quoin bond and the protected backing. The hash rule is re-run and verified on all seven buildings.
- The water gable now bears visibly on masonry. The dressed responds read as stone piers from the bed with a capping
  pad under each post (y01-y07), the honest construction ref4 implies.
- The quay is solid in every view: 0 misses in the hole scans, quoin-bonded slip-mouth corners (y11, y12) and a
  closed slip head (y10).
- Dropping the king strut is a cheap, reusable way to soften the "church tracery" read of the gable.
- The budget is still healthy at 695 k tris, with 9 slots and complete `Mask` coverage.

**Must-fix (round 4)**
1. **The client's broader, slumped hall roof** (CLIENT DIRECTION after the round-2 grade). This is a recipe change
   on `build_v5_harbour_house.py` `DIM` / `MAIN`, plus the knock-on re-fits.
   - What is wrong: `DIM half=3.0` (hall 6.0 m), `pitch=58.0`, and `MAIN ridge_sag=0.24` (recipe lines 52 and
     59-61). The roof is tall and pointed (`side.png`, x34), not ref4's heavy slumped roof.
   - What it should be:
     - hall 6.6-7.0 m wide (`half` 3.3-3.5) at 52-54 deg with `ridge_sag` 0.35-0.45;
     - the gable apexes (comb top) 8.5-9.5 m above the quay;
     - the swept eaves (`eave_sweep`) and flared verges (`verge_flare`) kept, scaled to the wider span if needed;
     - widen toward +X, away from the tower (raise `hx` with `half` so that `XW` stays at 0.2), so the tower
       abutments change as little as possible.
   - Make the widening a parameter change. The recipe hard-codes `S_W, S_S, S_E = 3.2 + 0.7, ... + 9.2, ... + 6.0`
     (line 74), the `QUAY` ends (9.6, -3.0), the `JETTY` rect (7.2-9.0), the mooring posts, the ladder and
     `DOOR_X`. Derive them from `DIM`: `S_W = bay + half - clear / 2`, `S_S = S_W + len`, `S_E = S_S + 2 * half`,
     with the quay and jetty x positions relative to `XE`.
   - The cruck follows `half=HALF`. Optionally raise `clear` to about 5.0 so the responds leave about 4.2 m at water
     level.
   - Re-verify, as the client asked ("everything stays sealed and carried"):
     - the seal probe at 0 leaks on both `wall_abutment`s;
     - the clearance gate at both doors;
     - the quay hole scans and corner bond at the moved slip mouth;
     - the tie bearing on the new pier quoins;
     - hidden ≤ 15 % (14.2 % now: the wider roof adds covered shingle, so trim it in the cull);
     - ≤ 1 M tris;
     - the hash rule, only if a shared module is touched.
   - Builders: read the latest CLIENT DIRECTION / PRODUCER NOTE entries immediately before starting the round, and
     again before writing the builder entry.

**Nice-to-have**
- Close the two partition-end pinholes on the slip-head coping (x19_red, about x -0.41 / 4.19, y 0.23, z 0.04):
  carry the partition frame's end posts 1 cm into the slip walls, or run its sill 2 cm into the coping.
- Close the 4 cm post-to-slip-wall slot (y09). Set the posts 1 cm off the wall face, or add a timber fillet; the
  responds already carry the post line.
- Build the respond courses through the kit's dressed-stone path (`rubble_walls._quoin_courses` or the quoin
  stones) so they match the hall quoins (reuse mandate). Add `damp_rise` / `moss` anchors on the respond water faces
  between -0.9 and 0.
- `stone_quay(ends=)`: "return" or "squared" free ends (y13, x27, x28).
- A boathouse smoke recipe, about 30 lines, that exercises `cruck_frame` + `stone_quay` + `pile_deck` at a different
  size and orientation. This is the proof that the waterfront half is a short recipe, as the barn smoke is for the
  timber half.
- `pile_deck`: accept `land="E"` / `"W"`, seat the X-braces and waling on the piles, and pool the dog plates (note 3).
- `wall_abutment`: end the lead flashing at the eave lip, not in boxy tabs (x10, x11).
- Shutters on a few stone-wall windows (the brief's "small shuttered windows").
- A deeper slip (4.5-5 m) with a timber landing ledge.
- `tools/render_review.py --ground_z` (producer tool): the six main views still float the building 2.5 m.

## CLIENT DIRECTION (2026-10-17, session 2, 14:10): push the roof closer to ref4, IN ROUND 4; time matters

The client saw the early round-4 previews (`scratch/r4_fast/renders/`, 14:03). The deeper sag is right, but from the water the hall still reads as an upright gable. The client agreed with pushing it further toward ref4's broad, heavy, slumped hat, and added: **"time matters here: do not spend time that can be avoided, and the earlier a correct result is obtained, the better."**

**Round-4 fixer: apply this in THIS round,** even if a full build with 52-54 deg is already done. It is recipe values only, so one rebuild:
- **pitch about 48-50 deg** (not 52-54), **`ridge_sag` about 0.45-0.55 m**, the hall at the full **7.0 m** width;
- a heavier, deeper **`eave_sweep`** and overhang, so the roof reads thick and dominant, and the **verge flare** kept;
- **the ridge band is relaxed** to a comb top of at least about 7.8 m. Do not raise the eave walls: the boat arch has to stay under the tie;
- compare a side view and a water-side view against `reference/ref4_harbour_boathouse_concept.jpg` before the final render.

Keep every round-3 waterline fix, and re-verify only what the roof change touches: the seal probe on both `wall_abutment`s, the door clearances, hidden <= 15 %, and <= 1 M tris.

**Everyone (time matters):**
- No nice-to-haves this round.
- No re-runs that the change does not need. The hash rule only applies if a shared module is touched; this is a recipe change.
- Reuse existing probe scripts and camera setups.
- **Art Director:** grade round 4 promptly, re-using the round-3 camera set and probes where the geometry did not change. Judge the roof against ref4.

## v5_harbour_house round 4 — builder entry

**Built:** the client's broader, slumped hall roof, as a recipe parameter change only, with every round-3 waterline
fix kept. I read the CLIENT DIRECTION after the round-2 grade, the PRODUCER NOTE of 13:48 and the round-3 grade before
starting. I re-read the log before this entry and found the **CLIENT DIRECTION of 14:10**, which superseded my first
build (7.0 m at 53.5 deg, `ridge_sag` 0.42; its renders are kept in `scratch/r4_full/renders_53p5/`). I applied it in
this round with one rebuild. Nothing else was done (no nice-to-haves).

- **Recipe:** `buildings/variants/v5_harbour_house/build_v5_harbour_house.py` (175 lines, 151 non-blank non-comment).
  It writes `v5_harbour_house.blend` (19.2 MB, compressed) and `decal_anchors.json` (115 anchors).
- **Renders:** `renders/variants/v5_harbour_house/round_04/` (all six views, `--samples 24`), with `stats.json` and
  `hidden.json`. The builder close-ups (the round-3 camera set, moved with the slip mouth) are in
  `round_04/builder_extra/`: `r4_slip_mouth`, `r4_corner_W`, `r4_corner_E`, `r4_gable`, `r4_pier_W_out`,
  `r4_pier_W_in`, `r4_pier_E_out` and `r4_roof_ne` (a high three-quarter from the water side, the ref4 angle).
- **Datum (unchanged):** quay and landward ground at Z = 0, coping and footings at -0.04, bed at -2.5. The recentre
  shift is now **(-1.808, -5.973)** (round 3: -1.308), because the hall and quay grew 1.0 m toward +X. The review
  tool's ground plane is still at the bed, so the main views float the building by 2.5 m (the tool, not the model).

### The roof change

| | round 3 | round 4 | asked |
|---|---|---|---|
| hall width (`half`) | 6.0 m (3.0) | **7.0 m (3.5)** | 7.0 m (14:10) |
| pitch | 58 deg | **49 deg** | 48-50 deg (14:10) |
| `ridge_sag` | 0.24 m | **0.50 m** | 0.45-0.55 m (14:10) |
| eave overhang | 0.45 m | **0.70 m** | deeper (14:10) |
| `eave_sweep` / `sweep_len` | 0.28 / 1.0 m | **0.40 / 1.5 m** | heavier (14:10) |
| `verge_flare` / `flare_len` | 0.36 / 2.0 m | 0.42 / 2.33 m (scaled with the span) | kept |
| `eave_sag` | 0.08 | 0.10 | — |
| comb top at the gables | 8.69 m | **7.96 m** | at least about 7.8 m (14:10) |
| comb at mid-length | 7.75 m | 6.42 m | (the slump) |
| finial tips | 9.57 m | 8.82 m | — |
| eave wall height (`wall_z`) | 3.35 m | 3.35 m, **not raised** | not raised (14:10) |
| boat opening (`clear`) | 4.6 m | **5.0 m** (about 4.2 m between the responds) | optional 5.0 |

- **It widens toward +X only.** `DIM` now carries `xw=0.2` (the hall's west face against the tower) and derives
  `HX = xw + half`, so the tower abutments move as little as possible. The roof now meets the tower over z 2.67-6.22
  (round 3: 2.65-7.14), still under the tower's stone top at 6.90.
- **Everything derives from `DIM`:** the run distances `S_W = bay + half - clear/2`, `S_S = S_W + len`,
  `S_E = S_S + 2*half`; the `QUAY` ends (`XE + 3.4`, `XW - 3.2`); the `JETTY` rect, the moorings and the ladder from
  `XJT = XE + 1.0`; and `DOOR_X = HX + 1.1`. The unused `DIM["pier"]` and `DIM["hx"]` literals are gone, and
  `ridge_sag` is in `DIM`. A boathouse can be widened or narrowed by changing `half`.
- The cruck follows `half`: the tie spans ±3.14 m at 3.41-3.73 m, the arch runs 2.00 -> 3.07 m (R 2.72) under the tie,
  the collar is at 5.62 m and the apex at 7.51 m, with 46 infill boards. The boat arch stays under the tie because the
  eave walls were not raised.

### Re-verified (only what the roof change touches)

| check | result |
|---|---|
| seal probe on both `wall_abutment`s | roof / tower: 51,507 rays, **0 leaks**; wing roof / tower: 57,393 rays, **0 leaks** |
| clearance gate | **PASS** at both doors: hall door (land gable) 5.63 m eave lip; wing door 2.50 m (unchanged) |
| quay hole scans at the moved slip mouth (`scratch/probe_r4.py`, the round-3 probe re-derived from the new `DIM`) | outer E, both slip returns and the slip head: **0 pass-through**. On the outer W face, 4 of 7,885 rays: all in the one column 5 cm from the W arris, at bed-joint heights. They travel along a return-run bed joint and stop on `HARB_quay_backing_blocker` 3.57 m in, so they are not see-through. The round-3 blend gives 3 on the same column (`scratch/r4_corner_col.py`). The round-3 grid never sampled 5 cm from the arris. |
| corner bond at the moved slip mouth | "2 convex corner(s) quoin-bonded". Diagonal rays: none past the arris on either corner. |
| cruck posts on the responds | the horizontal rays hit the respond face at every station from -2.40 to -0.05 on both sides; the ray down from each post foot hits masonry |
| tie bearing on the new pier quoins | on the pre-cull blend (the final blend's culled hidden faces make the downward rays meaningless): the tie bears **1-6 mm** on the quoin tops over about 0.4 m of each pier. The 0.13-0.41 m readings are rays falling into the vertical joints between top-course quoins, as in round 3. `r4_pier_W_out` / `r4_pier_E_out` show the tie seated on the top course. |
| footing overhang | 0 footing hits above -0.30 off the flush faces (the only hits are the partition sill and the respond pad, by design) |
| hidden | **13.6 %** (round 3: 14.2 %), under the 15 % limit |
| triangles | **707,889** (cap 1,000,000) |
| slots / Mask | 9 palette slots; `mask_attribute_missing` none |
| objects | 70 (unchanged) |
| hash rule | **not needed**: no kit module was touched (recipe only). Noted in `kit/changes/v5_harbour_house.md` (Round 4). |

### Stats (round_04 `stats.json`)

707,889 tris, 13.6 % hidden (96,007 tris), 9 slots, 70 objects. The bbox is 17.59 x 17.17 x 15.94 m (the plan is
1.0 m wider in X). The build took 12.8 min with the cull. The kit gate kept 115 of 178 decal anchors.

### Known gaps

- From the water (`back.png`) the hall still reads as a gable with a lighter, lower hat, rather than ref4's fully
  sagging gable. The silhouette is broader and the slump is clear from the side (`side.png`) and from `r4_roof_ne`.
  A further step would need a lower `wall_z`. That would also lower the tie, and the boat arch under it (crown now
  3.07 m), so I did not do it unasked.
- The quay's free ends are still cut ends.
- The responds narrow the water-level clear width (now about 4.2 m).
- The posts stand 4 cm off the slip-wall face.
- The two partition-end pinholes are still open (round-3 nice-to-have, not attempted per 14:10).
- A small dark triangle remains between the tie end and the verge soffit over each pier (`r4_pier_W_out`). It was
  there in round 3 and is not new.
- The review tool's ground plane is at the bed.
## v5_harbour_house round 4 — score 8.3/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note
10), no surface-detail requests (note 12). Binding: producer notes 1-17, every CLIENT DIRECTION entry above (ref4 is
the primary reference), the PRODUCER NOTE of 13:48 and **the CLIENT DIRECTION of 14:10** (pitch 48-50 deg, `ridge_sag`
0.45-0.55, 7.0 m hall, heavier sweep and overhang, comb top at least about 7.8 m, eave walls not raised; "time matters").
No CLIENT DIRECTION or PRODUCER NOTE was added after the round-4 builder entry.

**Reviewed:**
- All six `round_04` views, `stats.json`, `hidden.json`, `decal_anchors.json` (115 anchors plus the validation block),
  the eight builder extras, the recipe (175 lines, every plan coordinate now derived from `DIM`) and the Round 4 note in
  `kit/changes/v5_harbour_house.md`.
- No kit module was touched in round 4: the newest files in `kit/village_kit/` are `cruck.py` 13:11, `waterfront.py` 13:11
  and `rubble_walls.py` 13:09, all round 3. So the hash rule does not apply.
- Director extras in `renders/variants/v5_harbour_house/round_04/director_extra/` (`dir_render_r04.py`):
  - the round-3 camera set re-used and moved with the geometry (slip centre unchanged at x 1.892, jambs at -0.608 / 4.392,
    hall faces at -1.608 / 5.392, tower axis at x -1.808), 31 shots;
  - 10 new roof shots (z01-z10): the W arris column, all four eave/verge corners, the ridge sag, the E soffit, the
    water gable from the jetty, the tie end / verge triangle, the roof-wing-tower nook from above, and a ref4 side angle;
  - 30 red twins, with enclosed-red counts in `redcount_r04.txt` (`dir_redcount_r04.py`);
  - an eave-corner probe in `probe_r04_out.txt` (`dir_probe_r04.py`).

**Director-verified compliance:** 707,889 tris (cap 1 M), 13.6 % hidden (1.8 % below the datum), 9 palette slots,
`mask_attribute_missing` empty, 70 objects, bbox 17.59 x 17.17 x 15.94 m.

**The round-3 must-fix (the client's broader, slumped roof, as revised at 14:10), checked:**

| asked (14:10) | built | director check | result |
|---|---|---|---|
| hall 7.0 m | `half=3.5`, widened toward +X only (`xw=0.2`) | the roof covering spans x -2.39 to 6.18 (7.0 m plus 2 x 0.70 m overhang plus the sweep) | met |
| pitch 48-50 deg | 49 deg | the moss anchors on the slope carry normal z 0.656 = cos 49 deg | met |
| `ridge_sag` 0.45-0.55 | 0.50 (comb 7.96 m at the gables, 6.65 m at mid-length) | z04, x34, `side.png`: a clear saddle between the turned finials | met |
| heavier, deeper sweep and overhang, verge flare kept | 0.70 m overhang, sweep 0.40 m over 1.5 m, flare 0.42 m over 2.33 m | x23, z05, x34: the eave kicks out flat over the last 1.5 m; the eave lip is at 2.85-2.92 m | met |
| comb top at least about 7.8 m, walls not raised | 7.96 m; `wall_z` 3.35 | the probe gives the apex finial tips at 8.82 m; the arch crown is at 3.07 m, under the 3.41 m tie | met |
| compare with ref4 | `r4_roof_ne` | x01, y14, z10 put side by side with ref4 | see axis 1 |

**Every round-3 waterline fix still holds** at the moved slip mouth:
- y01, y06, y07: the posts stand on the dressed responds;
- y11, y12, z01: the corner quoins are bonded, and the W arris column in z01_red shows no enclosed red inside the quay
  outline (the 17,912 enclosed px are the jetty X-brace bays);
- y01_red, y11_red, y12_red: 0 enclosed red;
- x16, `r4_pier_*_out`: the tie is seated on the top quoin course;
- the partition-end pinholes are down to 6 px in total (x19_red; round 3 had about 13 px each).

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.4 | This is the change round 3 lacked, and it lands. From the side (`side.png`, x34, z04) and at the ref4 three-quarter angle (x01, y14, z10), the hall is now ref4's building: a broad, low-slung shingle roof that dominates the walls (roof 4.6 m over 3.35 m walls), with a visible saddle between gable apexes that kick up on flared bargeboards, and eaves that sweep out flat. Under the roof sit the rubble boat hall, the heavy timber water gable over the boat arch, and the round tower with a boarded top under a mossy cone and spike. The swept saddle also separates it from the v3 longhouse at thumbnail size (x02, y15), which was round 3's main distinctness worry. Held below 8.5 for two reasons. Square-on from the water (`back.png`, x15, z06) it is still an upright gable, broader, with flared skirts; ref4's slump is mostly a three-quarter read, so I accept that, and the builder was right not to drop `wall_z` unasked. And the land elevation (`front.png`, x03) is still rubble gable plus round tower. |
| 2 Proportion and actor scale | 8.3 | Unchanged and right: both doors are 1.00 x 2.10 m on built-in thresholds (x03), the windows are 0.55 m at 1.30 m sills, and the wing eave sits 2.50 m over a 2.22 m head. No door sits under the 2.88 m side eave lip. The boat opening is wider (5.0 m clear, about 4.2 m between the responds at water level), with the crown at 3.07 m. The slip is still only 3.2 m deep. |
| 3 Construction logic | 8.4 | The roof sits on the wall heads (deck + 2 cm, z05), carried on rafter tails over a plate. The tie bears 1-6 mm on the pier quoins. The arch stays under the tie because the walls were not raised. Every round-3 bearing is intact at the new span. Left over: the posts stand 4 cm off the slip-wall face (y09; closed behind, black in the twin), the jetty X-braces and waling stand about 1 cm off the piles, and at the four main eave/verge corners the verge rafter tail drops 15 cm below the bargeboard foot (axis 4). |
| 4 Seams and junctions | 8.2 | The red twins are clean at every module junction: roof/tower x07, x08, x10 and z08 (0 enclosed); wing/tower x09 (36 px of distant eave sky); both eaves x23 and x24 (only sky between comb pieces); both apexes x21 and x25 (the 7,252 px in x25 are the open sky pocket between the verge and the tower top, not a hole); the corners z02, z03 and z09 (3-25 px). The builder's seal probe is at 0 leaks on both `wall_abutment`s. **New with the deeper sweep:** at all four main-roof corners the eave/verge end is untidy at eye level. The probe gives the bargeboard foot at z 2.87-2.88, cut level, while the straight verge rafter tail (`HARB_roof_rafters`) projects to z 2.73 below and outside it at a different angle (z02, z03, z09, x22), and a dark slot runs along the eave between the soffit board and the starter course (backed, black in the twins). Still open from round 3: the quay's raw free ends (x27, x28), the boxy lead tabs in the nook (x10), and the 4 cm post slot. None is see-through. |
| 5 Distinctness and reuse | 8.4 | The best modularity evidence so far. A 1.0 m wider, 9 deg lower, twice as slumped hall was done with **values only**, and every module re-fitted itself from `DIM`. `stone_quay` re-bonded the moved slip-mouth corners. `cruck_frame` re-spanned the tie, the arch and the responds. `path_stone_wall` re-topped the walls to the new deck, with `flush_runs` kept. Both `wall_abutment`s re-sealed. The soft `GableRoof` options carried a much stronger setting with no new code. Round 3's must-fix on hard-coded run distances is done: `S_W` / `S_S` / `S_E`, `QUAY`, `JETTY`, the moorings, the ladder and `DOOR_X` all derive from `DIM`. It still reads as the same village (the same rubble, shingle, cone, finials and lead). **Family verdict:** genuinely reusable, not one-off code dressed as modules. The timber half is proven by the round-2 barn smoke; the waterfront half has now been re-parameterised once with no code changes. It still lacks a second recipe at a different orientation, and `pile_deck` accepts only `land="S"` / `"N"`. Those are the first jobs of the boathouse design, not blockers here. |
| 6 Technical compliance | 8.5 | 707,889 tris, 13.6 % hidden (better than round 3's 14.2 %), 9 palette slots, `Mask` everywhere, deterministic, and the datum is recorded in the anchors JSON. 115 anchors, physically plausible: damp and moss on the quay water faces at -0.35 to -0.72, lichen on the copings, streaks under the cone eave and the sills, moss on the roof slope at 49 deg normals. Minor, carried over: roof moss is only on the -X slope (the `moss_normal="slope"` choice), three damp/moss anchors sit at the foot of the tower's timber belt at 7.2 m (plausible as a splash ledge), and the house pools nothing (dog plates and door irons are unique, note 3). The process is also good: the builder found the 14:10 direction mid-round and applied it in one rebuild. |

**Verdict: 8.3/10, PASSED (pass mark 8.2), subject to the independent audit.** The client's broader, slumped roof is in,
with the 14:10 values (7.0 m, 49 deg, 0.50 m sag, 0.70 m swept eaves, 7.96 m comb), and from the side and the ref4
three-quarter angle the hall now reads as ref4's heavy, dominant roof. It was done as a pure recipe-parameter change,
and every waterline fix, seal and bearing re-fitted itself and still checks out. That is strong proof that the family is
modular. Nothing open is see-through, floating or against a producer note. What remains is polish at the eave/verge
corners and the quay ends, plus the boathouse proof of the waterfront half.

**Strengths**
- The roof finally matches ref4: a broad, low, saddle-backed shingle roof with kicked gable apexes, flared bargeboards
  and flat swept eaves (x34, z04, z10, y14).
- The resize took values only. Twelve plan coordinates now derive from `DIM`, and `stone_quay`, `cruck_frame`,
  `path_stone_wall`, `wall_abutment` and the soft `GableRoof` re-fitted without a code change. The hash rule is not
  needed (no kit file is newer than round 3).
- The waterline is intact at the moved slip mouth: the posts are on the responds, the corners are quoin-bonded, the
  quay faces have 0 enclosed red, and the tie is seated.
- The red twins are clean at every roof/tower, wing/tower, eave and apex junction. The seal probe is at 0 leaks.
- The budget improved while the roof grew: 13.6 % hidden, 708 k tris, 9 slots, full `Mask`.

**Must-fix:** none open. The round-3 must-fix (the client's broader, slumped roof) is closed, and nothing found in this
round breaks a producer note or a client direction.

**Nice-to-have (carry into the boathouse / barn recipe; each is a kit change and inherits there)**
1. **Main-roof eave/verge corners (`linear_roof` verge="board" with `eave_sweep`).** At the four corners (final x -2.3
   / 6.1, y -6.2 / 3.9, z 2.7-3.0; z02, z03, z09, x22), the straight verge rafter tail projects 15 cm below and outside
   the level-cut bargeboard foot.
   - When `eave_sweep > 0`, skip or clip the verge rafter tail behind the bargeboard's inner face.
   - Cut the bargeboard foot plumb on the eave fascia line, so it caps the swept eave end.
   - Defaults unchanged, so no hash re-run.
2. Close the dark slot along the swept eave between the soffit board and the starter course (z05, z09). Seat the
   starter course on the eave board, or drop a fascia strip.
3. `stone_quay(ends=)`: "return" or "squared" free ends at x -4.81 / 8.79 (x27, x28).
4. A boathouse smoke recipe (about 30 lines) that runs `cruck_frame` + `stone_quay` + `pile_deck` at a different size
   and a rotated orientation, and `pile_deck` with `land="E"` / `"W"`, seated braces and waling, and pooled dog plates
   (note 3).
5. `wall_abutment`: end the lead flashing at the eave lip, not in boxy tabs (x10).
6. The 4 cm post-to-slip-wall slot (y09) and a deeper slip (4.5-5 m) with a landing ledge.
7. Roof moss on both slopes (or on the true north slope after placement); `tools/render_review.py --ground_z` for the
   2.5 m float in the clay views.

## v5_harbour_house round 4 — sign-off audit: UPHELD

The independent auditor checked the Art Director's round-4 pass (8.3/10) on the note-12 MODULARITY RUBRIC, pass mark 8.2.
The audit covers geometry only, with no ground dressing (note 10) and no surface-detail requests (note 12). It is binding on
producer notes 1-17, every CLIENT DIRECTION entry above (ref4 is the primary reference) and the 14:10 roof direction. No
CLIENT DIRECTION or PRODUCER NOTE was added after the round-4 grade.

**Reviewed:**
- the six `round_04` views, the 8 builder extras and the 41 director extras with their 30 red twins, plus `redcount_r04.txt` and `probe_r04_out.txt`;
- `stats.json`, `hidden.json`, `decal_anchors.json`, the recipe (175 lines), ref4 and ref1-ref3.

**My scripts** are read-only bpy, one process at a time, in `renders/variants/v5_harbour_house/round_04/audit/`:
- `aud_probe_r04.py`: compliance, anchors, door clearance, islands, and the verge rafter against the bargeboard;
- `aud_ring_r04.py`: 32 black / red-world see-through renders at 2560 x 1440. Sixteen are at eye level (z 1.7, 13 m out) and sixteen are crane views (z 6.0, 11 m out), all round the building. Enclosed red is sized in world units from the rim depth;
- `aud_probe2_r04.py` and `aud_probe3_r04.py`: the ridge comb, the slip-wall foot and the tower foot ring;
- `aud_recipe_match_r04.py`: whether the recipe matches the blend;
- `tools/hidden_tris.py`, re-run on its own.

### Hard requirements (measured on the saved blend)

| requirement | measured | result |
|---|---|---|
| ≤ 1,000,000 tris | 707,889 evaluated triangles (`stats.json` agrees) | PASS |
| ≤ 15 slots, palette only | 9 slots: `M_iron`, `M_lead`, `M_mortar`, `M_roof_shake`, `M_roof_shingle`, `M_stone`, `M_stone_dressed`, `M_timber`, `M_timber_weathered`. None is outside the palette. | PASS |
| est_hidden_pct ≤ 15 | 13.6 % in `stats.json`. My independent `hidden_tris.py` re-run (20,000 samples) gives **13.8 %**, with 1.9 % below ground. | PASS |
| `mask_attribute_missing` empty | Empty. All 70 meshes have `Mask` as CORNER BYTE_COLOR, set as both the active and the render colour. All transforms are identity. | PASS |
| DECAL_ANCHORS + json, plausible | The collection holds 115 empties with all six properties. The JSON has 115 anchors with the same names and carries the datum and the dims. **0 of 115** anchors have no surface within 20 cm behind them. Heights are plausible: damp and moss at -0.72 to -0.04 on the quay faces, lichen on the copings, rust 0.24-1.69 m under the door irons, cracks 1.07-5.39 m, streaks up to 8.57 m under the cone eave. | PASS |
| door clearance ≥ 2.30 m | I cast up-rays from above the thresholds, 0.05-1.20 m out, across ±0.55 m. **Wing S door:** the lowest overhead is the wing rafter tails at **2.464 m** (0.20 m out), then the deck at 2.59 and the covering lip at 2.64; the door head is at 2.22. **Hall land door:** it sits under the gable, and the lowest overhead is the verge deck / rafters at 5.56 m. | PASS |
| no see-through gap, floating piece or clipping > 2 cm at a module junction (ground / 6 m cameras) | **Floating:** I split the 70 meshes into 6,291 loose islands; none has a 2 cm-inflated bounding box that touches no other island. **Clipping:** at all three free main-roof eave corners, 0 verge-rafter vertices sit inside the bargeboard. **See-through:** the 32-camera ring found no real hole at any module junction (details below). | PASS |
| hash rule | No kit file is newer than round 3 (`cruck.py` 13:11:54 is the newest). The `v5r3_hash` rebuilds of all seven buildings started at 13:09:34, after the last `rubble_walls.py` edit at 13:09:21, so the round-3 match stands. Round 4 changed the recipe only. | PASS (not triggered) |
| new family = reusable kit modules | The recipe only imports and calls kit modules: `stone_quay`, `round_stone_body`, `path_stone_wall(flush_runs)`, `cruck_frame`, `path_timber_wall`, `linear_roof` / `GableRoof` soft options, `wall_abutment`, `board_belt`, `cone_roof`, `finial`, `round_eave_fill`, `pile_deck`, `ladder`, `composite_*`. The 1.0 m widening was values only. The barn smoke recipe exists. | PASS |

**Recipe and blend provenance.**
- `build_v5_harbour_house.py` was saved at 14:20:29, about 2.4 minutes after the final build started (14:18:05; the blend was saved at 14:30:53). So the build ran on the recipe as it was before that last save.
- I checked that the current recipe still describes the blend:
  - the `DIM` in `decal_anchors.json` is identical to the recipe's;
  - the recipe's `MAIN` and `WING` roofs, imported without building, predict the blend's deck undersides to a mean of 1.3 mm and at most 5.4 mm over 77 and 35 sample points.
- The late save therefore did not change the geometry I measured, but it was not rebuilt.

### See-through ring: what was found (none blocking)

1. **Ridge comb (`linear_roof` `_ridge_comb`).**
   - **What the ring found:** 43 enclosed patches on the main ridge and 18 on the wing ridge. They are vertical sky slits between the crossed comb shakes, hanging down from the crest line, about 6-14 cm tall.
   - **Measured:** horizontal rays on a 5 mm grid, square-on to both ridges, give slits of **at most 2.0 cm** (one at 2.0 cm, the rest smaller). The wing slits are at most 1.5 cm. The tallest is 12.5 cm.
   - **Why it is not blocking:** the crest stands 16 cm proud of a closed deck, so these are gaps between its teeth, not a hole through the roof. They sit at the 2 cm threshold.
   - **Fix:** a kit nice-to-have below.
2. **Slip-wall and pier feet over the quay (the `path_stone_wall` / `stone_quay` junction).**
   - **What the ring found:** in the red twins, 3-6 cm patches at z -0.05 to 0.13, at the E slip-wall foot (x 4.39) and the W slip-wall foot (x -0.73 / -0.90).
   - **Measured:** horizontal rays from the slip show that in about 5-14 % of each wall's length a slot up to about 4 cm high, between z -0.04 and 0.00, runs right through the 1 m of masonry: 1,164 rays on the W side, 1,224 on the E. None does above z -0.001. The constant 9 % above z 0 is the cruck posts in front of the wall, not a gap.
   - **Why it is not blocking:** the slots come out on the land side below the Z = 0 ground datum, so with terrain in place they are backed and are not see-through. They show red only because the red twin has no terrain.
   - **Nice-to-have:** start the flush footing course and the wall core at the coping top (-0.04), not just above it.
3. **Tower stone top / `board_belt` foot ring (z 6.9).**
   - **What the ring found:** 2-3 px pockets at the tower's limbs.
   - **Measured:** radial rays at 1-degree steps over z 6.70-7.20 never get inside r 2.077 m, and none reaches the belt line.
   - **Verdict:** these are silhouette pockets, not a gap.
4. **Other:**
   - the 7 k-18 k px regions in g06 / g07 / c06 / c07 are the open jetty X-brace bays;
   - the sky pocket between the tower and the land-gable verge (x25) is open space;
   - the partition-end pinhole is 0.7 cm wide;
   - mortar triple-point pinholes on the slip walls (x28_red, 1-3 px) are about 1 cm or less.

### Director's grade, re-checked

| axis | director | auditor | note |
|---|---|---|---|
| 1 Silhouette and massing | 8.4 | 8.3 | Agreed from the side (`side.png`, x34, z04) and the ref4 three-quarter (x01): the broad, slumped, swept roof now dominates. From the water (`back.png`) it is still an upright gable, and from the land (`front.png`, x03) it is still rubble gable plus round tower. |
| 2 Proportion and actor scale | 8.3 | 8.3 | Both doors are 1.00 x 2.10 m on 0.12 m thresholds (heads at 2.22 m). The wing eave is at 2.46 m. |
| 3 Construction logic | 8.4 | 8.3 | Everything is carried; no floating island was found. The 4 cm post-to-wall slot and the slip-wall foot slots (closed by the terrain, not by masonry) take a little off. |
| 4 Seams and junctions | 8.2 | 8.2 | Every module junction is closed. Seal probe 0 leaks. Red twins clean. My ring found no real junction hole. Open but non-blocking: the verge rafter tail 15 cm below the bargeboard foot (no interpenetration), comb slits up to 2.0 cm and the foot slots. |
| 5 Distinctness and reuse | 8.4 | 8.4 | Agreed: the widening was values only and every module re-fitted itself. It reads as the same village. |
| 6 Technical compliance | 8.5 | 8.5 | Every hard number verified independently. |

**Verdict: UPHELD at 8.3/10, the same as the Art Director's grade; my lowest axis is 8.2 (seams), above the 8.2 pass mark.** Every hard requirement holds
on measured evidence. The client's 14:10 roof direction is built as asked: 7.0 m, 49 deg, 0.50 m sag, 0.70 m swept eaves,
comb 7.96 m, walls not raised. The family is genuine reusable kit code. The director missed three things: the comb slits,
the slip-wall foot slots and the recipe's late save. All three are measured above, and none breaks a hard requirement in the
placed context.

**Blocking issues:** none.

**Carry into the boathouse / barn (kit, defaults unchanged; added to the director's nice-to-have list):**
1. `linear_roof._ridge_comb`: close the crest. Raise the overlap from `w * 0.92` to about `w * 0.80`, or put a thin ridge board behind the crest, so no sky slit shows between the shakes. They are up to 2.0 cm square-on now and wider at oblique angles.
2. `path_stone_wall(flush_runs)` on `stone_quay`: seat the flush footing course and the wall core down to the coping top. This removes the ≤ 4 cm through-slot at z -0.04 to 0.00 that only the terrain now hides.
3. Rebuild once the recipe file is final, so the saved blend and the recipe have the same timestamp order (process).

## PRODUCER NOTE (2026-10-17, session 2, 14:58): round 4 ACCEPTED

Director 8.3 (pass mark 8.2) and the independent audit upheld it. 707,889 tris, 13.6 % hidden, 9 palette slots, 115 decal anchors. The deliverable is `buildings/variants/v5_harbour_house/` (recipe, .blend, decal_anchors.json). No more rounds.

The nice-to-haves from the grade and the audit carry into the boathouse / barn design as kit fixes:
- the swept eave/verge corners;
- the eave slot;
- `stone_quay(ends=)`;
- the ridge-comb slits;
- the `wall_abutment` lead tabs;
- `pile_deck` E / W;
- the post slot;
- a deeper slip;
- moss on both slopes;
- `render_review --ground_z`.
## CLIENT DIRECTION (2026-10-17, session 2, after acceptance): add ref4's eyebrow dormer (round 5)

The client sent `reference/ref4b_eyebrow_dormer_markup.jpg`, the ref4 concept with one area circled in blue: "A detail I would like to see added is this section circled in the reference image." Open it (Read tool).

**What is circled:** an **eyebrow dormer** on the main hall roof. It sits on the slope that faces the lower wing and the tower, about midway between the water gable and the tower.
- The shingle courses swell up in one smooth, continuous wave over a small window. There are no cheeks, no hard valleys and no ridge: the courses bend over the window and run on.
- Under the wave, a short vertical timber front holds a small two-light window (about 0.6-0.8 m wide), with a little dark eave over it.

**Round 5 (one round; time matters):**
- **Kit first.** Build it as a reusable **add-on** (plan step 4 lists the dormer). Preferred: an option on the existing soft `GableRoof` / `linear_roof` warp, i.e. a local bump in the vertical warp field that every roof part already follows (covering, comb, rafters, deck, eave roll), plus a framed opening in the deck. The window comes from `wall_openings.window_spec` / the existing window pieces, set in a short `path_timber_wall` front, or the kit's plank front. Defaults unchanged: no eyebrow unless asked, so the hash rule does not trigger. If you change a shared module's default behaviour, it does.
- **Apply it to the harbour house:** one eyebrow on the slope facing the wing / tower, sized like ref4 (the wave about 1.6-2.2 m wide along the eave and about 0.5-0.8 m high, the window about 0.6-0.8 m wide), clear of the `wall_abutment` and the wing roof.
- **Seal it:** no see-through at the wave, the window front or the deck opening; the seal probe and red twins as usual. Keep hidden <= 15 % and <= 1 M tris.
- **Change nothing else.** Every accepted part of round 4 stays as it is. No nice-to-haves.
## v5_harbour_house round 5 — builder entry

**What I built:** ref4's eyebrow dormer, the area the client circled in `reference/ref4b_eyebrow_dormer_markup.jpg`.
- It is a reusable kit add-on on the soft `GableRoof` / `linear_roof`, applied once to the harbour house on the west slope, the one facing the wing and the tower.
- Nothing else in the recipe changed.
- I read the CLIENT DIRECTION "add ref4's eyebrow dormer (round 5)" before starting. I re-read the log before writing this entry: there is no newer CLIENT DIRECTION or PRODUCER NOTE.
- The `*_r04_accepted.*` files are untouched (still 14:20 / 14:30).
- No nice-to-haves.

**Files:**
- **Recipe:** `buildings/variants/v5_harbour_house/build_v5_harbour_house.py` (183 lines, 156 non-blank non-comment).
  - It was saved at 15:21. The final build started after that save and wrote the blend at 15:35, so the recipe and the blend are in order (the audit's process point).
  - The round-5 diff is the `BROW = eyebrow(...)` spec, `eyebrows=[BROW]` on `MAIN`, the import and the docstring.
  - Outputs: `v5_harbour_house.blend` (19.4 MB) and `decal_anchors.json` (112 anchors).
- **Renders:** `renders/variants/v5_harbour_house/round_05/` has all six views (`--samples 24`), `stats.json` and `hidden.json`.
- **Close-ups:** `round_05/builder_extra/` (`scratch/closeups_r5.py`; recentred coordinates, same shift as round 4):
  - `r5_brow_eye` (+ `_red`): eye level, 1.7 m, from the land west of the hall.
  - `r5_brow_ref4`: the ref4 three-quarter view from the NW over the water. The water gable is on the left, the tower on the right and the wing in front. This is ref4's own side; the round-4 "ref4 angle" x01 / z10 shots are from the NE and do not see this slope.
  - `r5_brow_graze` (+ `_red`): grazing along the west slope from the water end.
  - `r5_brow_close` (+ `_red`): the window, the wave's eave and the front's ends.
  - `r5_brow_probe_out.txt`: the see-through probe.

### The kit option: `GableRoof(eyebrows=[eyebrow(x, side, ...)])` (`components/linear_roof.py`)

**How the bump works:**
- It is one more term in the roof's single vertical warp field, so every part that follows the warp follows the bump.
- The term is a step at the front (slope distance `u_t`):
  - below the front, the slope runs on untouched;
  - above it, the roof is lifted by `height x bell(x)`: full height over `flat`, then a cosine fall to 0 at `±width/2`;
  - upslope it holds for `plateau`, then fades smoothly back into the slope over `fade`.
- So there are no cheeks, no valleys and no ridge: the courses bend over the window and run on.
- The front is snapped to the shingle course grid, so one whole course is the wave's lowest course. It overhangs the front by `lip`: the little dark eave.

**Parts that follow it:**
- **Pieces stay whole.** `to_world` / `warp_z(..., brow=)` can put a whole piece on one side of the step. Each shingle course is either wholly lifted or not, so no shingle is torn across the step.
  - The courses under the wave stop their heads at the deck front.
  - The wave's eave course has closed undersides.
- **The deck** gets two rows at the step. There it becomes a closed vertical deck front under the wave, with a framed opening (cells removed, cut edges closed) behind the window.
- **The eave strip** is a lifted board strip under the wave's eave course, so no slot shows under the eave.
- **`_eyebrow_fronts`** is called by `linear_roof` with its own rng, so the roof's other random draws are unchanged. It builds:
  - a sill beam on the slope;
  - the timber family's rough board-and-batten cladding (`timber_walls._clad`), clamped to the eave strip, so the front is the wave's arch;
  - a closed backing (`_sheet`), cut only at the clear opening;
  - end posts;
  - the kit window: `openings.window` through `resolve_timber` and `wall_openings.build_opening(host=timber)`. It is the cross-mullion two-light frame with no shutters, and its dark room is sized to stay under the wave.
- New objects: `HARB_roof_eyebrow0_frame`, `_boards`, `_blocker`, `_frames` and `_blockers`.

**Parameters (`EYEBROW` defaults, then the harbour-house values):**

| parameter | default | harbour house |
|---|---|---|
| `x` (along the ridge, local) | — | 4.6 (world y 4.6, over the west-wall window) |
| `side` | 1 | +1 (west slope) |
| `d` (in from the eave lip, plan) | 1.5 | 1.5 (snapped to 1.578: course 6 is the eave) |
| `width` | 2.0 | **2.2** |
| `height` | 0.75 | **0.72** |
| `flat` | 0.70 | 0.60 |
| `plateau` | 0.18 | 0.18 |
| `fade` | 1.20 | 1.20 |
| `lip` | 0.20 | 0.20 |
| `set_back` | 0.04 | 0.04 |
| `window` | 0.56 x 0.36, sill 0.05 | the same (0.72 m over the jambs) |
| `min_front` | 0.14 | 0.14 |

`height` is the vertical gap the front closes. `lip` is the wave's eave overhang. `set_back` is the front's face distance out from the deck front. `min_front` sets how far the front runs to each side: it is built where the gap is at least that tall, and the deck front closes the rest.

**As built:**
- The front is 1.67 m wide.
- In build coordinates (before the recentre), the sill is at z 4.04 and the wave's eave at 4.76. The wave fades out about 1.2 m under the ridge.
- Clearances: about 1.3 m from the tower face (the `wall_abutment` meets the tower at y < 2.3), and clear of the wing roof (y < 2.05) and the partition (y 6.2).

**Other kit change:** a new option `room_pad` (the dark room's margins) on the timber window, in `timber_walls.TIMBER_OPENING["window"]` and `wall_openings._build_timber_opening`. Its default `(0.35, 0.6, 0.35)` is the old hard-coded margins. Everything is recorded in `kit/changes/v5_harbour_house.md` (Round 5).

### Checks

| check | result |
|---|---|
| eyebrow see-through probe (`scratch/r5_brow_probe.py`) | 18,456 rays on a 3 cm grid over the whole front arch (the lower roof to 15 cm over the wave's eave, the full 2.2 m width), from 15 directions (square-on, ±25 / ±50 deg yaw, -15 / +15 / +35 deg pitch): **0 leaks**. No ray goes more than 0.70 m behind the face. 1,094 rays end on the window's dark room, the deepest at 0.5-0.6 m (the room's back). |
| red twins | `r5_brow_close_red`, `r5_brow_graze_red`: **0 enclosed red** at the wave, the front or the opening. `r5_brow_eye_red`: the only red inside the outline is the round-4 comb slits on the ridge (audit item 1; not new). |
| seal probe, both `wall_abutment`s | roof / tower: 51,484 rays, 0 leaks. Wing roof / tower: 57,465 rays, 0 leaks. |
| clearance gate | PASS: hall door eave lip 5.63 m; wing door 2.50 m (unchanged) |
| hidden | **14.4 %** (103,248 tris), under the 15 % limit (round 4: 13.6 %) |
| triangles | **715,139** (round 4: 707,889; the eyebrow adds about 7.3 k), cap 1,000,000 |
| slots / Mask | 9 palette slots; `mask_attribute_missing` none |
| objects | 75 (round 4: 70, plus the five eyebrow objects) |
| bbox | 17.59 x 17.17 x 15.94 m (unchanged); recentre shift (-1.808, -5.973) (unchanged) |
| six views | identical to round 4 apart from the eyebrow, which is visible on the west slope in `aerial`. `side` is the east elevation. |

### Hash rule

**Not triggered.** Only new options were added, and their defaults keep the old code path exactly:
- `GableRoof(eyebrows=())`;
- `to_world` / `to_local` / `warp_z(brow=None)`, ignored without eyebrows;
- the timber window's `room_pad` default, which equals the old margins.

With no eyebrows, `_deck` builds the same grid and the same face order, and `_shingle_courses` builds the same pieces with the same rng draws. No `v5r5_hash` run.

### Known gaps

- **Steep flanks.** The bump is vertical only. On the steepest part of the wave's flanks the shingles shear as they follow the field. With 2.2 m and `flat` 0.60 this reads as a soft wave (`r5_brow_close`), but it is not as smooth as ref4's painted flank.
- **Slots at the front ends.** Each end of the front leaves a short dark slot of a few cm between the end post and the wave's flank. It is backed by the deck front (0 leaks), not see-through.
- **Shingle only.** A thatch roof with `eyebrows` raises.
- **No overlap check.** A bump must not overlap a verge, the eave band, another bump or a junction body, and this is not checked. The wave is checked only against the ridge.
- **Decal anchors: 112** (round 4: 115). The same composite decal recipe runs, but the kit gate's random visibility cull now drops 3 more quay / jetty anchors (one lichen, one damp, one moss). The rest are renumbered, and 2 roof-moss anchors now sit on the wave. Not blocking. I did not chase it (no re-run the change does not need).
- **Carried over from round 4, unchanged:** the comb slits, the eave/verge corners, the quay's cut ends, the 4 cm post slot, the slip-wall foot slots and the review tool's ground plane at the bed.

## v5_harbour_house round 5 — score 8.4/10

Graded by the Art Director on the note-12 MODULARITY RUBRIC (pass mark 8.2). Geometry only, no ground dressing (note
10), no surface-detail requests (note 12). Binding: producer notes 1-17, every CLIENT DIRECTION entry above (ref4 is the
primary reference) and **the CLIENT DIRECTION "add ref4's eyebrow dormer (round 5)"** (ref4b, circled; kit add-on,
wave about 1.6-2.2 m wide and 0.5-0.8 m high, window about 0.6-0.8 m, sealed, change nothing else; "time matters").
I re-read the log before starting and before writing: no CLIENT DIRECTION or PRODUCER NOTE was added after the round-5
builder entry.

**Reviewed:** ref4b and ref4; the six `round_05` views, `stats.json`, `hidden.json`; the builder's 4 close-ups, 3 red
twins and `r5_brow_probe_out.txt`; the recipe diff against `build_v5_harbour_house_r04_accepted.py`; `linear_roof`
`eyebrow` / `_eyebrow_fronts`, the `room_pad` option and the Round 5 note in `kit/changes/v5_harbour_house.md`.

**Director checks** (`renders/variants/v5_harbour_house/round_05/director_extra/`, read-only bpy, one process at a time):
- `dir_regress_r05.py` -> `regress_r05_out.txt`: every mesh of the round-5 blend against the accepted round-4 blend
  (vertex count, max vertex move, KD-tree for re-counted meshes).
- `dir_regress2_r05.py` -> `regress2_r05_out.txt`: the distance of every round-5 deck / covering / comb vertex from the
  round-4 surface (BVH), inside and outside the eyebrow zone, plus the triangle diff of the meshes whose count changed.
- `dir_render_r05.py`: the round-4 camera set (`dir_render_r04.py`) with 10 eyebrow shots added (e01-e10), run for the
  eyebrow shots and the four west-slope junction shots that could be affected (x08, x10, x24, z08); 12 red twins,
  counted in `redcount_r05.txt` (`dir_redcount_r05.py`). (e06, a profile along the slope, ended up inside the verge
  and shows nothing; it is ignored.)

**Accepted round 4 preserved.** The `*_r04_accepted.*` files are at 14:20 / 14:30 (untouched). The recipe diff is only the
import, the `BROW = eyebrow(...)` spec, `eyebrows=[BROW]` on `MAIN` and the docstring. Mesh by mesh:

| result | meshes |
|---|---|
| identical, every vertex within 1 mm | 63 of 70 round-4 meshes, including every wall, the tower, the wing and its roof, the water gable, quay, jetty, verge, shingles, starter, soffit, rafters and both `wall_abutment`s |
| changed only in the eyebrow zone | `HARB_roof_covering` (moved shingles at y -2.92 to -0.07, x < 0.75; outside the zone every vertex is on the round-4 surface, 0.0 mm); `HARB_roof_deck` (re-gridded, +5.3 k tris, but outside the zone every vertex is within 0.8 mm of the round-4 surface) |
| changed just outside the zone | `HARB_roof_comb`: 3 vertices of one crest shake over the eyebrow (x 1.74, y -1.42, z 6.66) moved 7.4 cm. The wave's fade reaches one comb piece at the ridge. Not visible in e01 / e10 / `r5_brow_eye`. |
| scene-dependent hidden-face cull noise | `HARB_hall_stones` -2 tris (0.03 cm2 slivers at the land-gable head), `HARB_tower_stones` -6 tris (up to 9.6 cm2, at z 5.6 inside the main-roof / tower abutment), `HARB_hall_frames` +2 tris (a 0.15 m2 hidden head top on the E window). The x08 / x10 / z08 red twins are at 0 enclosed (as in round 4), and the seal probe is at 0 leaks, so no hole was opened (note 6). |
| new | the five `HARB_roof_eyebrow0_*` objects, all inside x -0.88..-0.18, y -2.21..-0.54, z 4.05..4.75 |

**Hard numbers:** 715,139 tris (cap 1 M), 14.4 % hidden (limit 15 %; round 4 13.6 %; the +5.3 k deck tris are nearly
all of the increase), 9 palette slots, `Mask` everywhere, 75 objects, bbox 17.59 x 17.17 x 15.94 m unchanged. Doors
unchanged (wing eave 2.50 m, hall land door under the gable).

**The client's eyebrow, checked:**

| asked (CLIENT DIRECTION) | built | director check | result |
|---|---|---|---|
| on the slope facing the wing / tower, about midway between the water gable and the tower | W slope, y -1.37 (final), over the W-wall window; 1.3 m clear of the abutment | e01, e10, `r5_brow_ref4`: midway along the W slope, clear of the tower, wing roof and abutment | met |
| one smooth wave of shingle, no cheeks, no valleys, no ridge | a bump in `GableRoof`'s single warp field; whole courses lifted, the fade runs back into the slope | e03, e08: the courses swell in one wave and run on above and to both sides; no cheek, valley or ridge anywhere | met |
| wave about 1.6-2.2 m wide, 0.5-0.8 m high | 2.2 x 0.72 m, 0.20 m lip | the eyebrow objects span y 1.67 m (front) inside the 2.2 m wave; z 4.05-4.75 | met |
| small two-light window about 0.6-0.8 m in a short vertical timber front, little dark eave | kit cross-mullion window, 0.56 x 0.36 m clear, 0.72 m over the jambs; board-and-batten front, sill, end posts | e09, e02: the window is framed and dark, set in a boarded front under the wave's eave course | met (four lights, not two; accepted) |
| kit add-on, defaults unchanged | `GableRoof(eyebrows=())`, `eyebrow()`, `EYEBROW` defaults, `room_pad` default = the old margins | the regression diff: no non-roof mesh changed except cull noise | met; hash rule not triggered |
| sealed | probe 18,456 rays, 0 leaks; both seal probes 0 leaks | e02-e09 red twins: 0 enclosed at the wave, front and opening (e02's 212 px are the round-4 ridge-comb slits, e04's 1 px is the verge rim) | met |
| change nothing else | recipe diff = the eyebrow only | see the table above | met |

| axis | score | reason |
|---|---|---|
| 1 Silhouette and massing | 8.5 | The circled detail is in, and it reads at every distance: at the 45 m thumbnail (e10) and the ref4 angle from the NW (e01, `r5_brow_ref4`) the W slope now has ref4's eyebrow hood midway between the water gable and the tower, which breaks the long plain slope the way the concept does. It is a little smaller and flatter than ref4's painted hood (ref4's wave is deeper with a heavier dark eave), but inside the client's range. Everything else is round 4's accepted massing, unchanged. |
| 2 Proportion and actor scale | 8.3 | The wave (2.2 x 0.72 m) and the 0.72 m window frame are in proportion with the 1.6 m courses and the 0.55 m wall windows below (e02). The 0.36 m clear height is a small attic light, right for an eyebrow. Doors and every other dimension unchanged. |
| 3 Construction logic | 8.4 | Buildable: a sill on the slope, a boarded front with a backing, end posts, a framed deck opening and a lifted eave board under the lowest wave course; the wave's courses are whole pieces that overlap correctly (e03, e09). Round-4 bearings untouched (the regression diff). |
| 4 Seams and junctions | 8.2 | The new junctions are sealed: 0 probe leaks, 0 enclosed red at the wave, front and opening, and the x08 / x10 / z08 junction twins are as clean as round 4. Held at 8.2: on the steepest part of both flanks the vertical-only warp shears the shingles into stacked thin slivers (e02, `r5_brow_close`), the lifted eave board shows as a pale strip along the arch (e03), a thin dark crescent shows between courses at the top of the plateau (e03, backed), and the front ends leave short dark slots (e04, backed). None is see-through. |
| 5 Distinctness and reuse | 8.5 | The cleanest add-on so far: one new term in the warp field that the covering, deck, eave board and comb already follow, a kit window through `resolve_timber` / `build_opening`, its own rng so the roof's other draws are unchanged, and the defaults reproduce the old path exactly (63 of 70 meshes are vertex-identical; the rest change only in the zone or by cull noise). It is a value-driven option any shingle `GableRoof` in the village can take. Gaps: shingle only, and no overlap check against verges, the eave band, junction bodies or other bumps. |
| 6 Technical compliance | 8.4 | 715 k tris, 14.4 % hidden, 9 slots, `Mask` everywhere, deterministic, recipe saved before the build (the round-4 audit's process point is fixed). Taken off: the deck tear rows are inserted along the whole roof length (+5.3 k hidden tris), so the hidden headroom fell from 1.4 % to 0.6 %; the decal cull dropped 3 more quay / jetty anchors (112, still plausible); one comb shake moved 7.4 cm outside the stated zone. |

**Verdict: 8.4/10, PASSED (pass mark 8.2), subject to the independent audit.** The client's circled detail is built
as asked: one smooth wave of shingle over a small framed window in a short timber front, with no cheeks, valleys or
ridge, on the slope facing the wing and the tower, sized inside the client's range. It is sealed, and it is a genuine
reusable kit option whose defaults leave every other building untouched. The regression diff shows that the accepted
round 4 is preserved: 63 of 70 meshes are vertex-identical, and the rest changed only inside the eyebrow zone or by a
few hidden-face cull triangles that open no hole.

**Must-fix:** none.

**Nice-to-have (kit, defaults unchanged; carry into the boathouse / barn, not another harbour-house round):**
1. `linear_roof._deck`: insert the eyebrow tear rows only over the bump's span, not the full roof length (+5.3 k hidden
   tris now; hidden headroom 0.6 %).
2. Flank shear: tilt or rotate each lifted shingle to the local slope of the bell (or widen `flat` / soften the flank
   default), so the steep flanks read as one smooth roll as in ref4 (e02, `r5_brow_close`).
3. Hide the lifted eave board behind the wave's eave course (inset it a few cm) and close the dark crescent at the top
   of the plateau (e03); close the front-end slots with the end post or a flank board (e04).
4. End the fade before the comb (or exclude the comb from the brow term) so the crest shake over the eyebrow stays put.
5. An overlap check (verge, eave band, `wall_abutment` bodies, other bumps), and thatch support, before the add-on is
   used elsewhere.
6. Optional `window=dict(lights=2)` for ref4's two-light (vertical mullion only) eyebrow window.

## v5_harbour_house round 5 — sign-off audit: UPHELD

The independent auditor checked the Art Director's round-5 pass (8.4/10) on the note-12 MODULARITY RUBRIC, pass mark 8.2.
Geometry only; no ground dressing (note 10), no surface-detail requests (note 12). Binding: producer notes 1-17, every
CLIENT DIRECTION above and the CLIENT DIRECTION "add ref4's eyebrow dormer (round 5)" (ref4b, circled). I re-read the
log before starting and before writing: no CLIENT DIRECTION or PRODUCER NOTE was added after the round-5 grade.

**Reviewed:** ref4b and ref4; the builder entry, close-ups, red twins and `r5_brow_probe_out.txt`; the director's
`regress_r05_out.txt`, `redcount_r05.txt` and e-shots; `stats.json`; the recipe diff against
`build_v5_harbour_house_r04_accepted.py`; the Round 5 note in `kit/changes/v5_harbour_house.md`; `room_pad` in
`timber_walls.py` / `wall_openings.py` and its use in `linear_roof._eyebrow_fronts`.

**My scripts** (read-only bpy, one process at a time, `renders/variants/v5_harbour_house/round_05/audit/`):
- `aud_probe_r05.py` (the round-4 probe + eyebrow checks) -> `aud_probe_r05_out.txt`;
- `aud_probe2_r05.py` (classifies the eyebrow ray-probe misses) -> `aud_probe2_r05_out.txt`;
- `aud_ring_r05.py`: the round-4 32-camera ring unchanged, plus 32 eyebrow-targeted red twins (7 azimuths x eye level
  7 / 12 m, 6 m crane 6 / 10 m, 5.2 m close 3.5 m; 3 cameras that fell inside geometry skipped) and 17 grey workbench
  views -> `aud_ring_r05_out.txt`, `ring/`;
- `aud_hash_r05.py` (bit-exact mesh comparison r04 accepted vs r05) -> `aud_hash_r05_out.txt`;
- `aud_g01px_r05.py` (identifies the only new ring pixels), `aud_anchors_r05.py` (buried anchors);
- `tools/hidden_tris.py` re-run (`aud_run_hidden.py` wrapper) -> `aud_hidden_out.txt`, `aud_hidden.json`.

**Accepted round 4 untouched:** `*_r04_accepted.*` still 14:20:29 / 14:30:52 / 14:30:53; the accepted blend's SHA-256
(11A2EEE4...2D58) is the same before and after my read-only runs. Recipe diff = the import, `BROW = eyebrow(...)`,
`eyebrows=[BROW]` on `MAIN`, the docstring. Recipe saved 15:21:20, blend 15:35:45 (order fixed).

### Hard requirements (measured on the saved blend)

| requirement | measured | result |
|---|---|---|
| ≤ 1,000,000 tris | 715,139 evaluated (stats agree) | PASS |
| ≤ 15 slots, palette only | 9 slots, the same nine as round 4, none outside the palette | PASS |
| est_hidden_pct ≤ 15 | 14.4 % (stats); my independent re-run (20,000 samples) **14.3 %**, 1.9 % below ground. `HARB_roof_deck` now 83 % hidden of 9,654 (the full-length tear rows) | PASS (0.6-0.7 % headroom) |
| `Mask` on every mesh | all 75 meshes CORNER BYTE_COLOR, active + render; all transforms identity | PASS |
| DECAL_ANCHORS + json | 112 empties, all six properties, names equal to the JSON's 112; 0 with no surface within 20 cm behind; **0 buried** (no surface within 5 cm in front); the 7 anchors within 2.5 m of the eyebrow sit on the W wall (cracks z 2.19) and the slope / wave (moss, one with a wave-flank normal) | PASS |
| door clearance ≥ 2.30 m | identical to round 4: wing S door lowest overhead 2.464 m (rafter tails, 0.20 m out), head 2.22; hall land door under the gable, lowest overhead 5.56 m | PASS |
| no see-through / floating / clipping > 2 cm (ground and 6 m cameras), esp. at the eyebrow | see below | PASS |
| hash rule | not triggered, verified bit-exact (below) | PASS |
| eyebrow = reusable kit option | `GableRoof(eyebrows=[eyebrow(...)])` in `linear_roof`; the window is `openings.window` -> `resolve_timber` -> `build_opening`; the cladding is `timber_walls._clad` / `_sheet`; the recipe only passes values (11 parameters). No bespoke geometry in the recipe | PASS |
| no regression of round 4 | 64 of 70 meshes **bit-identical**; the 32-camera ring identical shot by shot except 6 single pixels in g01 (below) | PASS |

### The eyebrow: geometric evidence

1. **See-through, eyebrow-targeted red twins:** 32 shots (eye level 7 / 12 m, crane 6 m at 6 / 10 m, close 3.5 m, ±70 deg
   round the front): **0 enclosed red patches with a rim within 2.0 m of the front centre** in every shot. The enclosed
   red elsewhere in those frames is the round-4 comb slits, the jetty bays and the quay-foot slots (as round 4).
2. **Ray probe through the front / wave / opening:** 34,720 rays on a 4 cm grid over y -2.60..-0.14, z 3.95..5.05 on the
   front plane, 5 yaws x 4 pitches, origins 4 m out. **0 first hits on an interior object** (no peek into the hall
   through the deck opening). 156 rays hit nothing: all are the two steepest upward rays (yaw ±50, pitch -30) through
   targets at z 4.83-5.03 that lie **above** the covering (a ray straight up from each target hits nothing; straight
   down hits the covering 0.12-0.17 m below), i.e. open air passing over the ridge, not a hole. 0 misses through a
   target under the roof.
3. **Floating:** 6,314 islands, none whose 2 cm-inflated box touches no other island. Every eyebrow island is within
   2 cm of the roof or touches another eyebrow part (the window mullions sit in the window frame, the boards on the
   sill / backing).
4. **Clipping:** the backing, boards, sill and window jambs run up to 0.05-0.23 m into the closed shingle bodies of the
   wave's eave course. They are tucked under the eave (the lip overhangs the front by 0.20 m); in the 17 grey views (3.5 m
   to 12 m, ground to 6 m) nothing pokes through a visible shingle face. Not a visible clip.
5. **Comb over the eyebrow:** the moved crest shake still sits on the roof: nearest-roof distance max 0.149 m over the
   eyebrow vs 0.149 / 0.147 m on the reference stretches either side (that is the comb's own 16 cm crest standing
   proud). No gap opened.
6. **Clearances:** the eyebrow objects stay inside x -0.88..-0.18, y -2.21..-0.54, z 4.05..4.75, clear of the
   `wall_abutment`, the wing roof and the partition (director check e01 / e10 confirmed in my bc / bC views).

### Hash rule, verified

`linear_roof.py` (15:17:30), `timber_walls.py` and `wall_openings.py` (15:17:45) are newer than the round-3 hash runs.
The defaults reproduce the old path **bit-exactly** in this building: the wing roof (a `GableRoof` with no eyebrows:
covering, deck, comb, rafters, verge) and the tower-top timber openings (default `room_pad`: frames, blockers, boards)
are bit-identical to the accepted round 4. Not triggered.

### What changed outside the eyebrow (none blocking)

- `HARB_roof_deck`: re-gridded along the **whole** roof length (+5.3 k tris, almost all hidden). Its only visible
  effect: **6 new single pixels in ring shot g01** (from the NE), which I ray-traced to sub-pixel cracks at the
  N verge / deck edge (y 3.93, z 4.6-5.9). One pixel there is 0.7 cm, so these are below 1 cm; the 2 cm
  threshold holds.
- `HARB_hall_stones` -2, `HARB_tower_stones` -6, `HARB_hall_frames` +2 tris: the hidden-face cull is scene-dependent.
  The 31 other ring shots match round 4 pixel count for pixel count, and so does g01 apart from the 6 pixels above, so
  no hole was opened.
- `HARB_roof_comb`: one crest shake follows the fade (see item 5).

### Director's grade, re-checked

| axis | director | auditor | note |
|---|---|---|---|
| 1 Silhouette and massing | 8.5 | 8.4 | The circled wave reads from 12 m eye level and the 6 m crane (bG / bC views). It is shallower than ref4's painted hood. |
| 2 Proportion and actor scale | 8.3 | 8.3 | 2.2 x 0.72 m wave, 0.72 m window frame; doors unchanged. The window is cross-mullion (four lights) where the direction said two-light; accepted at form level. |
| 3 Construction logic | 8.4 | 8.4 | Sill, boarded front, backing, end posts, a framed deck opening, every part carried. No floating island. |
| 4 Seams and junctions | 8.2 | 8.2 | Sealed at the wave, front and opening (0 enclosed, 0 interior peeks). Held at 8.2 for the flank shear (close views), the backed front-end slots and the sub-cm verge pinholes. |
| 5 Distinctness and reuse | 8.5 | 8.4 | A genuine value-driven kit option, verified bit-exact by default. Shingle only, no overlap check. |
| 6 Technical compliance | 8.4 | 8.4 | Every hard number verified independently. Hidden headroom is now under 1 %. |

**Verdict: UPHELD at 8.4/10, the Art Director's grade. My lowest axis is seams at 8.2, which is the pass mark.** The client's circled detail
is built as asked and sealed. It is a reusable kit add-on whose defaults leave every other building untouched (bit-exact
evidence). Every accepted part of round 4 is preserved: 64 of 70 meshes are bit-identical, and the ring is unchanged
except 6 sub-cm pixels.

**Blocking issues:** none.

**Carry into the boathouse / barn (kit, defaults unchanged; added to the director's list):**
1. `_deck`: limit the tear rows to the bump's span (director item 1). This also removes the sub-cm verge pinholes it adds
   along the W slope, and gets the hidden headroom back (0.6-0.7 % now).
2. Add a regression gate that compares the ring red twins before and after an add-on, as I did here. It costs about 3 minutes and
   catches junction changes away from the add-on.

## PRODUCER NOTE (2026-10-17, session 2, 16:30): round 5 (eyebrow dormer) ACCEPTED

Director 8.4 (pass mark 8.2) and the independent audit upheld it. 715,139 tris, 14.4 % hidden, 9 palette slots.
- The client's circled eyebrow dormer is built as the reusable kit option `linear_roof.GableRoof(eyebrows=[eyebrow(...)])`. Its defaults are off, so the hash rule is not triggered.
- The director's regression check found 63 of 70 meshes vertex-identical to round 4, and the roof unchanged outside the eyebrow zone (within 0.8 mm).
- Round 5 is the deliverable. Round 4 is kept as `buildings/variants/v5_harbour_house/*_r04_accepted.*`.

Nice-to-haves to carry into the next design, as kit changes with unchanged defaults:
- limit the eyebrow's deck tear rows to the bump's span (this gives back hidden-geometry headroom);
- tilt the lifted shingles to the bump's slope (the flanks shear the shingles into slivers);
- inset the lifted eave board, and close the plateau crescent and the front-end slots;
- end the fade before the comb;
- add an overlap check and thatch support;
- add a two-light window option;
- plus the round-4 list above.
## CLIENT DIRECTION (2026-10-17, session 2, 16:35): the eyebrow dormer bigger and bolder, like ref4 (round 6)

Client's words: "I want it to be bigger and bolder like the reference". Compare `reference/ref4b_eyebrow_dormer_markup.jpg` (the circled area) with `renders/variants/v5_harbour_house/round_05/director_extra/e01_brow_ref4_NW_high.png`. In ref4 the eyebrow is a big, pronounced swell that lifts a large part of the slope. Round 5's 2.2 x 0.72 m wave is a modest bump that gets lost on the big roof.

**Round 6 (one round; time matters):**
- **Size, as recipe values first:**
  - the wave about **3.2-3.8 m wide** along the eave and about **1.1-1.4 m high**, with a lip of about 0.25-0.30 m;
  - a longer plateau, and a fade that still ends before the comb;
  - a larger two-light window, about **0.8-0.9 m wide x 0.55-0.70 m** clear, in a front that is correspondingly taller and wider.
  - It must read boldly from the ref4 three-quarter angle and at 45 m. Compare with ref4b before the final render.
- **Placement:** the same slope (facing the wing / tower). Re-centre it if needed so it stays clear of the tower `wall_abutment` and the wing roof. Door clearances must still pass.
- **Kit fixes this needs (eyebrow option only, defaults unchanged, no hash re-run):**
  1. **Tilt each lifted shingle to the local slope of the bump's curve,** so the flanks no longer shear the shingles into slivers. A bolder bump makes this visible.
  2. **Limit the deck tear rows to the bump's span.** They run the whole roof length today: 5.3 k hidden triangles, and hidden is at 14.4 % against a 15 % limit.
  3. **Inset the lifted eave board,** and close the plateau crescent and the front-end slots.
- **Change nothing else.** Round 5 is kept as `*_r05_accepted.*`; never modify those files. Keep hidden <= 15 % and <= 1 M tris.