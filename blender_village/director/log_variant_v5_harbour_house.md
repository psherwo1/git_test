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