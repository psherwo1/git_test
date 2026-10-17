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