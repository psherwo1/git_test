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