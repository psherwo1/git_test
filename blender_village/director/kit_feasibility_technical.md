# Kit feasibility: technical director's review (phase 2)

Date: 2026-10-17. Reviewer: independent technical director (not a builder or the Art Director of any variant).
Scope: `kit/village_kit` (kit 1.6.1 plus the 1.7 variant additions recorded in `kit/changes/`), the four variant
recipes in `buildings/variants/`, their round-4 renders and director logs, and one new recipe I wrote and built to
test the kit myself. I judged the kit against producer notes 12 (modularity over detail), 14 (12-15 curated designs
fill 40-50 placements) and 15 (at most 1,000,000 triangles per new structure). I did not ask for, or score, any
surface detail.

## Verdict: KIT WORKS, with conditions

The kit works as an **authoring toolbox** for the note-14 village. Its architecture is proven:

- four new building types were assembled from it;
- a fifth type, which I wrote myself in about 30 lines, built cleanly on the first try.

Its weaknesses are coverage and consolidation, not architecture:

- one building family the plan needs (timber and waterfront) has no modules yet;
- the small add-ons the plan relies on for placement variety do not exist;
- parallel module families have grown up that should be merged.

These can all be fixed by adding to the kit. None of them calls for the custom-hero fallback.

I recommend against triggering the "3 new custom heroes" fallback in the phase-2 decision rule:

- Approved building 1 (the longhouse with the round end) already exists as kit variant v3.
- Approved building 2 (the tiered hall) already exists as kit variant v2.
- Approved building 3 (the harbour house) needs timber modules whichever route is taken, so it is cheaper built
  as kit modules.

## Evidence

### 1. The four variants (round 4, note-12 rubric, pass 8.2)

| Variant | Director | Audit | Triangles (note 15) | Hidden | Recipe | Families combined |
|---|---|---|---|---|---|---|
| v1 stone watchtower | 8.3 | r2 rejected, r4 not run | **1,057,164: over the cap** | 12.5 % | 57 lines | drum + square cabin + pyramid roof |
| v2 tiered hall | 8.4 | r2 rejected, r4 not run | 954,925 | 11.3 % | 22 steps + 2 tables | new tier family (TierFrame) |
| v3 longhouse with round end | 8.6 | not run | 478,877 | 13.8 % | 94 lines | RoundFrame + path walls + gable thatch + cone |
| v4 mill-house | 8.4 | **accepted** | 938,453 | 13.2 % | 104 lines | hut family + drum family via `compound` |

- Every variant reached a director pass within four rounds, and every round-4 fix landed in a kit module rather
  than in a recipe.
- Directors rebuilt v2, v3 and v4 and found them geometry-identical (v3 also had a byte-identical decal JSON).
- The renders show four buildings with clearly different silhouettes, all in one style. None is a near-copy of a
  hero.
- Weak point: only v4 has been through the full gate (director pass and independent audit). v1 must lose about
  6 % of its triangles before it can be audited at all.

### 2. My own test: a new building type written from the kit only

**What I built.** A rectangular rubble store or barn under a 45° shingle gable roof, with a south door and two
windows. No existing building has this form. The recipe is in the scratchpad (`probe_barn/build_probe_barn.py`)
and is not a deliverable. Its core:

```python
ROOF = GableRoof(x0=-4.5, x1=4.5, half=2.9, wall_z=2.55, pitch_deg=45, overhang=0.5, verge=(0.4, 0.4))
steps = [(set_entrance, dict(xy=(0, -2.9))),
         (path_stone_wall, dict(name="walls", path=PATH, top_fn=top, openings=OPENINGS, seed=11)),
         (linear_roof, dict(roof=ROOF, covering="shingle", seed=12)),
         composite_hidden_cull, recenter]
build_building(dict(prefix="BARN", frame=RoundFrame, params=KIT, steps=steps, decals=composite_decals, ...))
```

**Results.**

| Measure | Value |
|---|---|
| Build time, without the cull | 29 s |
| Build time, with the cull | 214 s |
| Triangles | 332,392 |
| `est_hidden_pct` | 10.7 % |
| Material slots | 8, all in the palette |
| `Mask` and UV map | on every mesh |
| Transforms | identity on every unique mesh |
| Decal anchors | 63 |

- **Deterministic.** Two separate builds gave the same geometry hash (`af9218715f95eebe`).
- **Renders.** At hero distance the clay renders read as a believable village building in the house style.

**What the test exposed.** These are real kit gaps, not problems with this barn:

- **No generic frame.** I had to borrow `RoundFrame` as the context for a building with no round part, because
  `composite_decals` reads `g.R_EAVE` and the walls read `g.detail`.
- **No clearance check on generic buildings.** I gave the barn a 2.05 m eave lip, which is under the bible's
  2.30 m over a door, and nothing warned me. Only `tier_frame.roof_clearance` has a gate like this.
- **The decal gate is off by default.** It only reports unless `decal_validate=True` is set. In report mode,
  13 of the 63 anchors failed the footprint test and were still exported.
- **No pooling in the stone and roof path.** There were 0 linked duplicates: every stone and every shingle went
  into one unique mesh per part.

### 3. Code review of the kit

**What is good:**

- **Assembly API.** `build_building(spec)` with `(fn, kw)` steps, `KitParams` (typo-safe `set`/`variant`) and
  `compound.build_compound` with `Wing`s is short, declarative and easy to read. A recipe is a parameter table plus
  a step list, and none of the four recipes contains geometry code.
- **Determinism.** Seeds are always explicit (`np.random` with fixed seeds, `crc32`-derived salts and no `hash()`).
  It has been verified by hash four times now, including my own probe.
- **Note 1-11 machinery is in one place:**
  - `palette.py` holds the 15 slots and raises on anything else;
  - `mask.py` is the single `Mask` writer;
  - UVs are box-projected at about 1 UV unit per metre;
  - `core.nanite_clean` / `geom.strict_clean` handle Nanite hygiene;
  - `DetailRule` implements note 11;
  - the visibility cull has a Windows spawn pool and capped workers;
  - decal anchors come from the `DecalAnchors` collection, are exported as JSON, and are snapped and audited by
    `anchor_validate` / `anchor_audit`.
- **Seam and junction tools that generalise:**
  - `seal_probe.through_seal_probe` is a see-through test that fails the build when a covering lets light through;
  - `compound`'s single whole-building cull drops viewpoints inside another wing and protects the wall-head band;
  - `composite.trim_units` / `drop_units` / `cone_soakers` cut a covering on a plane, cap it and back it with lead;
  - `roof_junction.cone_abutment` closes a gable roof against a cone;
  - `junctions.roof_tower_flashing` and `wall_tower_abutment` close a cone roof and a daub wall against a drum
    tower;
  - `pyramid_roof` / `PyramidSurface` builds an N-sided bell-cast cap, checked on 3, 6 and 8 sides.
- **Note-15 tooling.** `lod.tmpl_lod` is an opt-in, height-banded LOD that keeps each piece's outline. It took v4
  from 1.39 M to 0.94 M triangles with no visible change.
- **Kit edit discipline.** Kit edits only add things; heroes are re-run after every edit with the ±0.5 % triangle
  check; changes go into `kit/changes/<variant>.md`.

**What is weak:**

1. **Fragmentation into parallel families.** Each variant added a family alongside the ones already there instead
   of extending them. The kit now has:

   | Concern | Parallel versions |
   |---|---|
   | Frames | 4 (`RoundFrame`, `DrumFrame`, `OctFrame`, `TierFrame`) plus `compound` |
   | Hidden-geometry culls | 6 (`round_`, `drum_`, `oct_`, `tower_`, `tier_`, `composite_hidden_cull`) plus `compound`'s |
   | Decal recipes | 7 |
   | Polygonal bell-cast roofs | 2 (`pyramid_roof` and `tier_roof`/`OctRoof`) |
   | Eave closures | 3 |
   | Opening-spec APIs | 4 (`stone_body.opening`, `wall_openings.door_spec`/`window_spec`, `windows.window_spec`, `plank_doors.door_spec`) |
   | Mesh accumulators | 3 (`core.Acc`, `geom.Acc`, `tmplmesh.BatchAcc`) |
   | Wall surface maps | 3 (`PathMap`, `SurfMap`, `drum_wall.Wall`) |

   Two functions share the name `end_apron` (`junctions` and `roof_junction`). Every new author has to learn which
   family a module belongs to, and a junction written for one family does not work in another.
2. **The keep (octagonal) family is barely reusable.** It reads its dimensions through a module-global proxy
   (`oct_frame.FR`, one active frame at a time), so two `OctFrame` wings cannot share a compound. `annex.py` has
   one door and one window baked in. v2 had to build a new `TierFrame` rather than reuse it.
3. **Junction coverage is pairwise and only covers what has been built.** Covered pairs:
   - cone ↔ drum tower;
   - daub wall ↔ drum;
   - gable roof ↔ cone;
   - path wall ↔ round body;
   - tier roof ↔ through-body;
   - polygonal body ↔ engaged turret;
   - cabin ↔ drum head;
   - the keep's thatch wing ↔ hall.

   Not covered: gable ↔ gable (valley, for L and T plans), gable roof ↔ tower, mono-pitch lean-to ↔ wall,
   chimney ↔ roof, dormer ↔ roof slope, gable roof ↔ polygonal body. `compound` junctions also only accept a round
   roof against a drum.
4. **Opt-in flags a new recipe must know about.** `DOOR_INFILL_DECK`, `EAVE_CLOSURE_DOOR_HALF_DEG`, `ENTRANCE_R8`,
   `DAUB_GRID`, `PLINTH_DENSE` and `SH_RING_STEP` are set by bare `configure` / `setattr`. `cone_roof` has grown to
   12 flat keywords. The `tmpl_lod` rule is global and keyed by prefix, and is never unregistered.
5. **The documentation has fallen behind.** `village_kit/README.md` stops at kit 1.2.0. It does not cover
   `compound`, `composite`, `tier_*`, `rubble_walls`, `linear_roof`, `roof_junction`, `junctions`,
   `square_cabin`, `pyramid_roof`, `seal_probe` or `lod`. Several module header signatures are stale (for example
   `square_cabin`).
6. **Leftover clean-up items from the director logs.** Some objects are built but 100 % hidden (v3's wall plate and
   28 pegs, v1's `cabin_bed`). `eave_deck_lap` is a 21 k-triangle backing that note 6 says should be cheap.
   Open-shell eave pieces show back faces under one-sided rendering on every cone, the signed-off hut included.

### 4. Export readiness (Unreal 5.8, ISMs and Packed Level Actors)

- **Ready:**
  - real-world metres with Z up;
  - identity transforms on every unique mesh;
  - pooled parts are linked duplicates (they map to ISMs);
  - one UV map, `Mask` and palette slots on every mesh;
  - decal anchors as both empties and JSON;
  - the building base is centred on the origin with the entrance facing −Y, which suits Packed Level Actor
    authoring.
- **Not started:** there is no export code in the repository. Nothing writes FBX or USD, converts to centimetres,
  writes custom normals, maps `Mask` to vertex colour, or produces instance layouts.
- **Pooling is per building.** `Pools(prefix)` names meshes per building, so the same peg in two buildings exports
  as two meshes, and most stone and shingle work is merged into one unique mesh per part. The plan measured
  instancing at a 1-6 % saving. That is acceptable for Nanite on the client's RTX 3060, but only because whole
  designs are reused 3-4 times; the kit itself does not de-duplicate across buildings.

## How many distinct buildings the kit can produce today

**Built already (7):**

- the 3 heroes: keep, tower windmill and wattle roundhut;
- the 4 variants: watchtower, tiered hall, longhouse with round end, and mill-house.

**Can be authored now from existing modules, roughly a 30-100-line recipe each, with only junction polish to
expect (about 5):**

- a rubble store or barn under a shingle gable (proven by my test);
- a thatched rubble cottage or byre (`path_stone_wall` + `linear_roof(covering="thatch")`);
- a stone roundhouse under a cone (`round_stone_body` + `cone_roof` + `ball_finial`);
- a small and a large wattle roundhut (`RoundFrame` radius and eave);
- a lookout or gate tower using the drum and the round-2 "lookout" crown, or `square_cabin` on another drum.

That makes about **12 convincingly distinct designs**: the low end of note 14's 12-15. The `*_KIT_VARIANT`
parameter tables add near-copies of the heroes, which count for placements but not as unique designs.

**Cannot be built convincingly today:**

- the timber harbour house or boathouse (approved building 3);
- any timber-framed or plank-clad house;
- an L- or T-plan house;
- a gatehouse with a through-passage;
- the add-ons the plan relies on for placement variety: lean-to, porch, chimney and dormer.

## Conditions and recommended next steps, in priority order

1. **Timber and waterfront family**, needed for approved building 3 and the boathouse:
   - `path_timber_wall` along any polyline: post-and-plank, clapboard or log, with openings from the shared
     opening spec;
   - piles or stilts and a plank deck or jetty;
   - a large boat or barn door.
2. **Add-on modules with their junctions:**
   - `lean_to` (a mono-pitch `GableRoof` subclass) against any wall;
   - a gable-gable valley for L and T plans;
   - a chimney stack with flashing through any roof;
   - a dormer on a slope;
   - a porch or canopy.

   These supply both the missing designs and note 14's placement variety.
3. **Consolidate before anything else grows:**
   - one `Building` base frame with no round assumptions;
   - one opening spec;
   - one polygonal bell roof (`PyramidSurface` behind `bell_tier`);
   - one eave closure;
   - one cull entry point;
   - one decal entry point that reads `WALL_FACES`, `OPENINGS` and `LINEAR_ROOFS`;
   - rename one of the two `end_apron`s;
   - remove the `oct_frame.FR` global proxy.
4. **Turn guard-rails on by default for new recipes:**
   - a generic clearance gate (door head against eave lip, eave lip at least 2.30 m over an entrance, roof against
     roof);
   - `decal_validate=True`;
   - `seal_probe` at every junction;
   - automatic steep-cone door flags;
   - unregister `tmpl_lod` at the end of each wing.
5. **Close the gate on what exists.** Bring v1 under 1,000,000 triangles with `tmpl_lod` (its drum is the same
   family as v4's). Then audit v1, v2 and v3.
6. **Update `village_kit/README.md`** to cover kit 1.3-1.7, with a one-page "write a new building" recipe guide.
7. **Export.** Build the FBX or USD exporter (centimetres, custom normals, `Mask` as vertex colour, pooled meshes
   as ISMs, instance layouts for Packed Level Actors). Run the UE 5.8 lookdev test on the signed-off windmill before
   any further modelling.

This review only judges whether the kit is fit for purpose. It is not a grade on the note-12 rubric.
