# village_kit: the shared modular kit for the Fjord Village buildings

Phase 2 of the production plan. The three signed-off hero buildings (hilltop keep, tower windmill, wattle
roundhut) are being moved onto one kit, so that 40 to 50 village buildings can be assembled from parameterised
components that share one material palette, one Mask writer, one stone generator and one roofing scale.

- **Status:** `wattle_roundhut` is migrated (round 8). The keep and the mill still run their phase-1 scripts. Their
  migrators add their components here, following the extension points below.
- **Runtime:** Blender 5.1.2 as a Python module (`/opt/bpyenv/bin/python`). Every building script starts with
  `sys.path.insert(0, ".../blender_village/kit")` and then `import village_kit...`.
- **Kit edit rules:** read `kit/CHANGELOG.md` before you edit anything here.
  - You may add modules, functions, and optional parameters whose defaults keep the old behaviour.
  - Never change the behaviour or signature of a function another building uses.
  - After every edit, rebuild every other building that imports the kit and check that its triangle count stays
    within ±0.5 %.
  - Record the change in the CHANGELOG.

```
village_kit/
  core.py        numpy/bmesh machinery: noise, primitives, Acc mesh accumulator, Nanite hygiene,
                 DetailRule (producer note 11), visibility cull (note 6), scene and save helpers
  palette.py     the 15-slot material palette (note 7). The ONLY place materials are created
  mask.py        the ONE `Mask` colour-attribute writer (note 9)
  pools.py       shared-mesh variant pools and linked duplicates (note 3)
  stones.py      ONE stone generator: make_stone(style, ...)
  shingles.py    ONE shingle / shake / board generator and the village-wide SIZE_TABLE
  decals.py      DECAL_ANCHORS empties and decal_anchors.json (note 11), plus placement helpers
  assembly.py    Building context, KitParams (the kit_set convention), build_building(spec)
  components/    parameterised building parts (see the table below)
```

## Conventions shared by every module

- **Units and orientation.** Units are metres, Z is up, and the ground datum is Z = 0. The building base is
  centred at the origin and the principal entrance faces −Y.
- **Azimuth.** `az` is measured from −Y toward +X. `core.az_pt(az, r, z)` returns the point. A "math angle"
  `theta` has x = cos and y = sin, and `cone.az2th` converts between the two.
- **Determinism.** Every component draws from its own `np.random.RandomState(seed)`. Seeds are parameters with
  fixed defaults, and `core.stable_seed()` / `core.rng()` derive salted seeds (crc32, never `hash()`). A build
  is reproducible bit for bit.
- **Object names.** Objects are named `<PREFIX>_<part>`: `g.acc("posts")` gives `HUT_posts`. Pooled linked
  duplicates are named `<PREFIX>_<part>_<nnn>` and live in `<PREFIX>_kit_instances`.
- **One add() call is one piece.** Each `Acc.add()` call is one stone, shingle, rod or plank. Mask R (per-piece
  random) and G (per-piece wear, from `wear=`) are written per call.

## core.py

| API | What it does |
|---|---|
| `Noise(seed)`, `vnoise`, `fbm`, `n2`, `ring_noise`, `smoothstep` | Deterministic value noise. The module-level functions use the hut's historic table (seed 4711); `Noise(90210)` reproduces the keep's table. |
| `nrm`, `rotx/y/z`, `xf`, `frame_R`, `R_y_to`, `az_pt`, `frame_wall` | Small linear-algebra helpers. |
| `grid_quads`, `tube`, `open_tube`, `chamfer_path`, `rbox`, `rbox2`, `lathe`, `slab`, `prism`, `smin` | Mesh primitives (numpy). `open_tube` models only the outward arc of a rod or pole (note 6). |
| `poly_area`, `poly_sdf`, `seg_dist`, `ccw`, `runs` | 2-D helpers. |
| `Acc(name, sharp, cull, moss, z_clamp, b_fn, hygiene)` | Numpy mesh accumulator: `add(V, faces, mat, uv, wrap, smooth, wear)`, then `build(coll)` or `build_mesh()`. It attaches palette slots and UVs (explicit or box), applies sharp-by-angle, culls faces whose vertices are all flagged by `cull(V)`, optionally runs `nanite_clean`, and writes the Mask. |
| `nanite_clean(me)`, `sliver_report(me)` | Nanite hygiene: remove doubles, dissolve degenerates, fix needle triangles (beauty re-triangulation, short-edge collapse, edge flip, delete what remains below 0.1 mm), drop zero-area faces. `sliver_report` returns (needles, zero-area). |
| `DetailRule(min_relief=0.02, entrance_relief=0.01, entrance=(x, y), entrance_r=3, entrance_h=2.5)` | Producer note 11. `min_at(p)`, `keeps(depth, p)`, `scale(depth, p)`. `DetailRule.off()` restores phase-1 behaviour. |
| `cull_object(ob, fn)` | Deletes the faces whose vertices are all flagged by `fn(V)`. |
| `visibility_cull(targets, extra_views)` | Deletes polygons that no viewpoint can see. It uses the review tool's viewpoints (`review_views`) plus your actor, door and crane views (`ring_views`, `review_cameras`). |
| `reset_scene`, `new_collection`, `count_triangles`, `save_blend` | Scene helpers. `save_blend` saves with compress=True and leaves no .blend1. |

## palette.py

`PALETTE` holds the 15 slots from producer note 7. `material(name)` creates a slot on first use and is
idempotent. `check(name)` raises on any slot outside the palette. `slots_in_use(objects)` lists the slots a set of
objects uses. No other module calls `bpy.data.materials.new`.

## mask.py

`write_mask(me, r=None, g=None, b=None, b_fn=None, moss=None)` writes `Mask` as a CORNER BYTE_COLOR attribute and
sets it as both the active and the default (render) colour attribute. Values are written raw (`color_srgb`), so
the stored byte is the value × 255.

- **R and G come from**, in priority order:
  1. explicit per-vertex arrays;
  2. the per-piece values that `Acc` attaches;
  3. mesh islands (R = hash, G = material wear base + spread).
- **B comes from** `b_fn(V, VN)`. The default `default_b` is high at the ground and the plinth, on up-facing
  surfaces and on north faces, and low under the eave. Pooled parts get a constant `moss`.

## pools.py

`Pools(prefix, collection)` is created by every `Building` as `g.pools`.

- `g.pools.mesh(pool, k, make, sharp)` builds variant `k` once: `make(acc, k)` fills an Acc in local
  coordinates.
- `g.pools.place(mesh, part, R, t, scale)` places a linked duplicate.

Use pools of 6 to 20 variants for small repeated parts: pegs, nails, hinge parts, chinking, balusters, and shingle
or stone variants placed rigidly.

## stones.py: one generator, `make_stone(style, rng, half=None, **params)`

| style | shape model | use |
|---|---|---|
| `rubble` | `rubble_stone`: flat-bedded, pillowed face, tilted ends, 0–2 fracture planes, 1–3 cm arrises | coursed rubble walls (keep, mill) |
| `dressed` | `dressed_stone`: planar faces, ~1 cm chamfer | surrounds, quoins, string courses |
| `voussoir` | `voussoir_stone`: dressed wedge (`wedge_deg`), thicker at the crown (`crown_extra`), irregular widths | round or segmental arches |
| `footing` | `field_stone`: crowned top, bulging front | footing course, projecting 5–10 cm |
| `plinth_slab` / `plinth_block` / `plinth_boulder` | `plinth_kind_stone` + hand-split skin | dry-stone plinths |
| `pad` | `pad_stone`: low and wide, flat tilted bearing bed | post pads |
| `spall` | `spall_stone`: 5–8 planar fracture faces | pinning and packing stones |
| `chink` | `chink_stone`: flat wedge | chinking in open dry-stone joints (pool it) |
| `boulder` | superellipsoid boulder | field boulders |
| `flag` | `shell_stone`: open shell from an outline | thresholds, steps, flags |
| `hearth` | `box_stone` | hearth rings |

All of them mesh by ray bisection (`facet_stone`) or as shells, densest on the exposed face.

The local frame for wall stones is x along the wall, y out (face), z up.

`min_relief`, `fine_scale` and `spall_scale` implement note 11. The hand-split skin (scars of 4–10 mm, lumps of
about 1 cm, pits) is dropped below the threshold. The random draws are unchanged, so the stone's shape is unchanged.

## shingles.py: the village roofing scale

`SIZE_TABLE` is the single table every kit roof reads.

- **`shingle`.** The shared CHUNKY unit: 0.35–0.55 m wide (course target 0.44, ±24 %), 0.30–0.40 m exposure,
  0.72 m long, 3.4–4.2 cm butt. This is the ensemble-review scale.
- **`shingle_apex`.** A documented exception: within 3 courses of an apex collar the target drops to 0.40 m,
  because the course circumference forces it.
- **`starter`.** The doubled eave starter course.
- **`shake`.** Long split shakes, 0.9–1.2 m. A different unit, used for collars and aprons.
- **`board`.** Vertical lantern or gable boards.

`SHINGLE_VARIANTS` holds 16 pooled hand-split base shapes. The helpers are:

- `shingle_mesh(W, L, var, ...)`: the shingle with cup, curl, ragged butt and rounded corners;
- `shake_mesh(rng, ...)`;
- `board_mesh(rng, ...)`;
- `course_widths(rng, circ, n)`;
- `units_per_course(r_mid)`.

To add a unit, add a named row with its reason. Never hard-code a size in a building.

## decals.py: producer note 11

`g.decals` (a `DecalAnchors`) collects anchors. `build_building` turns them into the `DECAL_ANCHORS` collection
and writes `buildings/<id>/decal_anchors.json`.

- **In Blender.** Each anchor is an empty `DA_<type>_<nnn>`. The empty's −Z points into the surface, +Z is the
  outward normal and +Y is the decal's up direction. Each carries the custom properties `decal_type`, `size_w`,
  `size_h`, `surface` (a palette slot), `probability` and `seed`.
- **In JSON.** The header gives units (metres), space (building-local, origin at the base centre on Z = 0) and
  axes. Each anchor records position, normal, up, size, type, surface, probability and seed.

`SurfaceProbe(objects)` ray-casts the built meshes, so every anchor sits on a real surface and reports that
surface's slot. These helpers encode the placement rules:

| helper | places | where |
|---|---|---|
| `base_ring` | `damp_rise`, `moss` | at the base of a wall, more likely on north faces |
| `tops` | `moss`, `lichen` | on up-facing stone tops, ledges and roof butts |
| `below_points` | `water_streak`, `rust_stain` | below sills, drips, wheel and boom ends, and ironwork |
| `above_opening` | `soot` | above openings and smoke holes |
| `opening_corners` | `crack`, `grime` | at opening corners, lintel ends and settlement points |
| `wall_scatter` | `plaster_patch`, `repair_patch`, and others | over a wall face, with a minimum separation |

Aim for 40–120 anchors per hero building.

## assembly.py: how a building is assembled

```python
KIT = KitParams(radius=3.5, eave_z=2.395, ...)       # the building's ONE dimension table
def kit_set(**kw): KIT.set(**kw)                      # unknown keys raise
build_building(dict(prefix="HUT", collection="HUT", frame=RoundFrame, params=KIT,
                    steps=[drystone_plinth, round_daub_wall, wall_plate, conical_roof, finial,
                           door_step, framed_door, interior, round_hidden_cull],
                    decals=round_building_decals, out=".../wattle_roundhut.blend",
                    decal_json=".../decal_anchors.json"))
```

- **`Building(prefix)`** is the context every component receives as `g`. It provides the collections,
  `g.pools`, `g.decals` and `g.acc(name, ...)`. `g.acc` returns an Acc with the building's ground cull, its
  buried-skirt clamp and hygiene.
- **A frame.** A building type with shared geometry subclasses `Building` with its frame. `RoundFrame` is the
  first.
- **`build_building(spec)`** does the following, in order:
  1. resets the scene;
  2. instantiates the frame with `params`;
  3. runs the steps in order, each step being `fn(g, **kw)`, and components publish on `g` what later steps need;
  4. places the decals and builds `DECAL_ANCHORS`;
  5. exports the JSON;
  6. logs the triangle count;
  7. saves compressed.
- **Variant switch.** A `<PREFIX>_KIT_VARIANT` environment variable selects an alternative table, so the same
  components build a different building. The keep and the mill already follow this convention.

## components/

Each component is a function `component(g, ..., seed=...)` that builds its own named objects. Dimensions come
from the frame `g`; seeds and options are parameters.

| module | public component(s) | objects |
|---|---|---|
| `frame.py` | `RoundFrame(prefix, radius, eave_z, overhang, pitch_deg, n_posts, n_raft, door_post_az_deg, finial_tip, collar_r, collar_pitch_deg, plinth_top, n_courses, sh_expose, daub_patches, cone_age, detail_rule, hygiene)`; `g.patch_at(az_deg, kind, cz, hs, hz, seed)`; `round_hidden_cull(g, targets)` | — |
| `plinth.py` | `drystone_plinth(g, seed)` | `_plinth_stones`, pooled `_plinth_chink_*` |
| `daub.py` | `round_daub_wall(g, patches, posts_seed)`: the daub fields, wattle where it shows, posts, plinth-top cull, coat with flakes, inner skin | `_wattle_rods`, `_wattle_stakes`, `_door_panel_backing`, `_posts`, `_daub`, `_daub_interior` |
| `wattle.py` | `weave_panel(...)`, `rope_panel(...)`, `wattle_patch(g, name, s0, s1, z0, z1, seed, radius / line)` | a free-standing woven panel |
| `round_wall.py` | `round_posts(g, seed)`, `wall_plate(g, seed)` | `_posts`, `_wall_plate`, pooled `_peg_*` |
| `cone.py` | geometry only: `surf` / `surf_frame` / `s_at_r` / `rafter_center` of a round conical roof (bell-cast eave kick, convexity, eave wave), and the age pass `age_defaults()` (low-frequency eave wave, 1–3 cm sag between rafters) | — |
| `conical_roof.py` | `conical_roof(g, seed)`: rafters with hub, purlin and batten rings, starter and shingle courses from `shingles.py`, blocker, eave closure | `_rafters`, `_purlin_rings`, `_battens`, `_roof_shingles`, `_roof_starter`, `_roof_blocker`, `_eave_closure` |
| `finial.py` | `finial(g, style="spike")` (alias `lead_hat_finial`): lead-hat collar, bell-cast upper collar, spindle, spike, ~1° lean | `_cap_collar`, `_finial` |
| `doors.py` | `framed_door(g, seed)`: the projecting framed door with leaf, ironwork and threshold; `door_step(g)` | `_door_frame`, `_door_leaf`, `_door_ironwork`, `_threshold`, `_step_stone`, pooled hinge and nail parts |
| `timber.py` | `round_post`, `hewn_member` (stroke-aligned adze, swell, wane, checks; note-11 switches `checks`, `hero_adze`, `adze_nonhero`), `timber_box`, peg and nail pools | — |
| `interior.py` | `interior(g, seed)`: earth floor and hearth | `_floor`, `_hearth` |
| `round_decals.py` | `round_building_decals(g, seed)`: about 100 anchors on a round daub building | `DECAL_ANCHORS` |

The derived dimensions reproduce the signed-off hut exactly at radius 3.50 and eave 2.395. The plate height, door
front plane, plinth face, floor edge, eave shadow heights, post and rafter counts and door-post azimuth all derive
from the radius and the eave height, so `RoundFrame(radius=2.9, eave_z=2.6)` builds a consistent smaller hut.
`HUT_KIT_VARIANT` builds exactly this hut.

### Extension points for the keep and mill migrators

- **Frames.**
  - Add `components/oct_frame.py` (octagonal hall, skirt roof, collar, cone, lantern) and
    `components/drum_frame.py` (battered stone drum, apron, smock tower) as `Building` subclasses.
  - Components take `g` and read only their own frame's attributes.
- **Stones.**
  - Add any extra style to `stones.STYLES` (for example the mill's vectorised `stone_local` split-stone
    language) under a new name.
  - Coursed-wall layout (`layout_wall`, `coursing`) belongs in a new `components/stone_wall.py` that calls
    `make_stone("rubble" / "dressed" / "voussoir")`.
- **Roofs.**
  - `components/oct_roof.py`: bell-cast octagonal caps and skirts. Read the unit sizes from
    `shingles.SIZE_TABLE["shingle"]`, so the turret and lantern caps go up to the chunky scale.
  - `shake_collar` uses `shingles.shake_mesh`.
- **Finials.** Extend `finial.FINIAL_STYLES`, for example with `"turned"` (keep) and `"ball"` (stone round
  ends).
- **Decal recipes.** Add `components/<type>_decals.py` and reuse the helpers in `decals.py`. The mill needs
  `below_points` at the wheel and boom ends.
- **Hidden-geometry cull.** Call `core.visibility_cull` with the building's own near and door views. The keep
  already does this the same way.
