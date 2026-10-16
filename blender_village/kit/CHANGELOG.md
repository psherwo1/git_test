# village_kit CHANGELOG

## Kit edit rules (all agents)

- You may ADD modules, functions, and optional parameters whose defaults keep the old behaviour.
- Never change the behaviour or the signature of an existing kit function that another building uses.
- After any kit edit:
  1. re-run every OTHER building script that imports `village_kit`;
  2. confirm it still builds without errors;
  3. confirm its triangle count is unchanged (within ±0.5 %);
  4. record the edit below, with the buildings you re-ran.

| Building | Imports village_kit since | Triangles at last check |
|---|---|---|
| wattle_roundhut | 1.0.0 (round 8) | 744,105 (re-run after 1.1.0: 744,105) |
| hilltop_keep | 1.1.0 (round 7) | 1,123,849 (variant 1,025,777) |
| tower_windmill | 1.2.0 (round 7) | 1,134,993 (variant 865,123) |

---

## 1.2.0 (2026-10-16): the stone-drum tower family, tower windmill migrated (MILL builder, round 7)

### New modules (no existing module changed behaviour)

- **`tmplmesh.py`.** The mill's template-instanced mesh machinery: `tmpl_box` / `tmpl_rings` topologies with the
  buried / covered faces dropped, `rbox`, `sweep`, `lathe`, `profile_block`, `add_grid`, transforms, smooth noise,
  `hewn_beam` / `hewn_between` / `facet_shave` (note-11 `min_relief`, draws unchanged), and `BatchAcc` (N pieces per
  `add()`; palette slots via `palette.material`, box UVs, sharp-by-angle, degenerate / buried-face removal,
  `core.nanite_clean` + a < 1e-8 m2 polygon sweep, Mask through `mask.write_mask` with per-piece R / G); `mesh_tmpl`
  (a kit mesh such as `shingles.shingle_mesh` / `shake_mesh` as a batch template), `fill_acc` (a batch into a
  `core.Acc` so pooled variants go through `pools.Pools.mesh`), `tower_b` (Mask B for tall buildings).
- **`split_stones.py`.** The mill's vectorised split-stone language (`split_batch`, `SPLIT_STYLES`, `conchoidal`),
  with `min_relief` per stone (note 11: face skin, spalls and scoops below the threshold dropped, draws unchanged).
- **`components/`**: `drum_frame` (`DrumFrame`, helpers taking the frame first, `relief_min`, `drum_finish`,
  `drum_hidden_cull`), `drum_wall` (`round_stone_drum`, `blind_arcade`, `coursing` with wandering beds / pinch-outs,
  `follow_beds`, `Wall`), `drum_band` (`baluster_row` aged, `dentil_corbels`), `drum_door` (`arched_door`,
  `entrance_step`), `shake_apron`, `smock_tower`, `mill_cap`, `fan_wheel` (+ alias `wind_wheel`), `tail_vane`
  (`rear_tail_vane`), `raking_props`, `rotor_checks` (`rotor_clearance`), `drum_decals` (`drum_tower_decals`).

### Additions to existing modules (append-only)

- **`stones.py`.** At the end: imports the split styles and registers `split_rubble`, `split_footing`, `split_pin`,
  `split_dressed`, `split_hero`, `split_ashlar`, `split_flag` in `STYLES` (`make_stone("split_rubble", rng,
  half=...)`).  No existing style or function changed.
- **`shingles.py`.** At the end: SIZE_TABLE row `shingle_small` (the gablet hood over a windshaft, with its
  reason).  The mill cap now uses the shared chunky `shingle` unit and the apron the shared `shake_mesh`.
- **`README.md`.** Status line and a "Kit 1.2.0" section.

### Verification

- **Pure refactor.** Before any intentional change, the kit mill reproduced the phase-1 script exactly: all 236
  accumulated arrays (every part's vertices, faces and material indices, every pooled variant and every linked-
  duplicate matrix) identical, for the hero and for `MILL_KIT_VARIANT`.
- **Round 7 (note 11 on, ensemble roughening, chunky cap, kit shakes, cull):** 1,134,993 triangles, 12.1 % hidden,
  10 slots, Mask complete, 0 needle / 0 zero-area polygons, 107 decal anchors; variant 865,123 triangles, 13.2 %
  hidden, 108 anchors.  Deterministic: a second build gave the same triangle count and an identical
  `decal_anchors.json`.
- **Other buildings re-run after the 1.2.0 edits** (to scratch files):
  - `wattle_roundhut`: builds without errors, **744,105 triangles** (record 744,105, 0.0 %).
  - `hilltop_keep`: builds without errors, **1,123,849 triangles** (1.1.0 record 1,123,849, 0.0 %).
- `__init__.__version__` was left for the kit architect to bump (it still reads 1.0.0).

---

## 1.1.0 (2026-10-16): the tiered octagonal family, hilltop keep migrated (KEEP builder, round 7)

### New modules

- **`geom.py`.** Vectorised primitives from the keep: `rbox_v` (many rounded / chamfered boxes at once from
  per-instance axis rows `ax4` / `ax5` / `axn` / `axr`), `inst_faces`, `obox`, `beam`, `sweep`, `prof_rect`,
  `prof_circle`, `lathe_rz`; 2-D helpers (`rot2`, `rounded_outline`, `inside_poly`, `catmull_closed`, `smooth_wave`,
  `softplus`, `box_sum`, `runs_of`); the keep's noise (`n1`, `fbm90`, `vnoise90` on `core.Noise(90210)`); the strict
  hygiene hook `strict_clean` (clip at -5 cm, `core.nanite_clean`, 5e-8 m2 zero-area, outward normals, mesh
  tessellation re-pass, sharp edges re-applied after the clean-up, per-island Mask R / G); `Acc(name)` and
  `finalize(acc, coll, smooth_deg, recalc, clip_z)`.
- **`components/oct_frame.py`.** `OctFrame(Building)`: the frame / dimension table of a tiered octagonal hall
  building (`PARAMS`), `derive()` / `set()`, `OctRoof`, the envelope functions, `min_relief(P)` (note 11), pooled
  part helpers `get_pool` / `place` over `g.pools`.
- **`components/stone_wall.py`.** Coursed rubble on any parametric wall surface: `layout_wall`, `fill_voids`,
  `polygonize`, `rough_footing`, `dress_irregular`, `lay_stones` / `lay_poly_stones` (make_stone + mapping + per-stone
  note-11 threshold), `mortar_sheet`, `round_stone_wall`.
- **`components/oct_hall.py`** (`oct_hall_walls`, `oct_hall_frame`, `door_threshold`), **`plank_doors.py`**
  (`arched_door`, `plank_door`, `door_spec`, `plank_leaf`, `strap_hinge`, `make_pintle`), **`windows.py`**
  (`hall_windows`, `annex_window`, `window_spec`), **`oct_roof.py`** (`skirt_roof`, `build_cap`, `cap_shingles`,
  `covering_boards`, `sarking_deck`, `hip_boards`, `eave_structure`), **`stone_cone.py`** (`shake_collar`,
  `stone_cone`, `lantern`, `cone_cap`), **`turret.py`** (`side_turret`, `corbel_cushion`), **`annex.py`**
  (`annex_walls`), **`thatch.py`** (`thatch_wing_roof`, `ridge_comb`, `thatch_junctions`, `d_roll`, `tuft_fringe`,
  `mortar_fillet`, `stepped_flashing`), **`hewn.py`** (`hewn_square`, `peg`, `nail_heads` over the kit's pooled
  `timber.make_peg` / `make_nail_head`), **`oct_cull.py`** (`oct_hidden_cull`), **`oct_decals.py`**
  (`oct_building_decals`).

### Additions to existing modules (append-only; no existing function changed its signature or default behaviour)

- **`core.py`.** `Acc.build_mesh`: `hygiene` may now be a callable hook `hygiene(me)` run at the same point as
  `nanite_clean` (after validate, before the Mask).  `hygiene=True` still runs `nanite_clean`; `False` nothing.
- **`stones.py`.** Styles `coursed` (`coursed_batch`: a whole batch of coursed rubble / dressed blocks in surface
  coordinates) and `coursed_poly` (`poly_rubble_stone`: one hero stone from its polygonal outline), `stone_outline`.
  Both take `min_relief` (scalar or per stone) without changing the random draws.
- **`shingles.py`.** SIZE_TABLE rows `skirt_board`, `collar_shake`, `comb_shake`, `hip_board` (each with its reason);
  `riven_shakes` (the keep's riven collar shakes, vectorised, note-11 aware).
- **`components/finial.py`.** The "turned" style: `TURNED_PROFILE`, `turned_finial(acc, base, scale, lean_deg,
  lean_dir)`, `lead_hat(acc, cx, cy, z_apex, r0, h0, cover=...)` (fits the drip and cone over the covering under it).
  `finial(g, style)` and `FINIAL_STYLES` are unchanged.
- **`README.md`.** Status line and a "Kit 1.1.0" section.

### Verification

- **Pure refactor.** With `units="phase1"`, `detail_rule=False` and no cull, the kit keep matched a phase-1 build
  object by object: 52 of 55 unique meshes vertex-identical (vertex / triangle count, bounds, coordinate sum); the
  skirt boards and the two cap coverings within 4 vertices (clean-up order).  Pegs and nails changed on purpose (kit
  pools).
- **Round 7 (`units="kit"`, note 11 on):** 1,123,849 triangles, 14.1 % hidden, 11 slots, Mask complete, 0 needle /
  0 zero-area faces, 104 decal anchors.  Variant: 1,025,777 triangles, 14.9 % hidden, 107 anchors.
- **Other buildings re-run after the 1.1.0 edits:**
  - `wattle_roundhut` (HUT_OUT to a scratch file): builds without errors, **744,105 triangles** (round-8 record
    744,105, 0.0 %), 105 anchors.
  - `tower_windmill` (MILL_OUT to a scratch file; its migration to the kit is in progress by its own builder):
    builds without errors at **1,134,997 triangles** and 107 decal anchors (16:20).  There is no earlier
    kit-based triangle record to compare with yet; the only 1.1.0 change to code the mill calls is the `Acc` hygiene
    dispatch, which is unchanged for `hygiene=True` / `False`, so 1,134,997 is the mill's own number on this kit.

---

## 1.0.0 (2026-10-16): kit created, roundhut migrated (KIT ARCHITECT)

### New modules

- **`core.py`.** Based on the hut's proven numpy machinery:
  - noise, primitives, `open_tube`, 2-D polygon helpers, and the `Acc` accumulator with per-piece Mask R / G;
  - from the keep: Nanite hygiene (`nanite_clean`, `sliver_report`), the windmill's sliver test, and
    `visibility_cull`;
  - new: `DetailRule` (producer note 11), `review_views`, `review_cameras`, `ring_views`, `stable_seed`, `rng`,
    `Noise(seed)`, and the scene and save helpers.
- **`palette.py`.** The 15-slot palette. This is the only module that creates materials.
- **`mask.py`.** The one `Mask` writer. It replaces the hut's `Acc` writer, the keep's `write_mask` and the mill's
  `set_mask`.
  - The values are now stored raw (`color_srgb`), as the keep and mill already did. The phase-1 hut wrote them
    through a linear→sRGB conversion.
- **`pools.py`.** Shared-mesh variant pools and linked duplicates.
- **`stones.py`.** One generator, `make_stone(style, ...)`.
  - The hut's generators: facet / field / plinth / pad / spall / boulder / shell / box.
  - New styles: `rubble`, `dressed`, `voussoir` and `chink`.
  - `min_relief` / `fine_scale` / `spall_scale` implement note 11.
- **`shingles.py`.**
  - `SIZE_TABLE`, the village roofing scale. The shared unit is the chunky 0.35–0.55 m shingle. `shingle_apex`
    (0.40 m target) is a documented exception.
  - The hut's 16 shingle variants and `shingle_mesh`.
  - New: `shake_mesh`, `board_mesh`, `course_widths`, `units_per_course`.
- **`decals.py`.**
  - `DecalAnchors`, which builds the `DECAL_ANCHORS` collection and exports `decal_anchors.json`.
  - `SurfaceProbe`.
  - Placement helpers: `base_ring`, `tops`, `below_points`, `above_opening`, `opening_corners`, `wall_scatter`.
- **`assembly.py`.** The `Building` context, `KitParams` (the kit_set convention) and `build_building(spec)`.
- **`components/`.**
  - `frame` (`RoundFrame`, `round_hidden_cull`), `cone`, `conical_roof`, `plinth`, `daub`, `wattle`,
    `round_wall`, `finial`, `doors`, `timber`, `interior`, `round_decals`.
  - All of these are hut phase-1 code. Its module globals became the explicit frame `g`, and every hard-coded
    radius-dependent number was derived from the frame.

### Verification

- **Before the intentional round-8 changes**, the kit-based hut was compared with the signed-off round-7 build:
  all 123 objects were bit-identical (vertex positions and matrices hashed at 1e-6), with 1,309,222 triangles.
- **Then these changes were applied:**
  - Producer note 11. The sub-2 cm relief is dropped (1 cm stays in the entrance zone).
  - Ensemble age pass on the cone.
  - Nanite hygiene on every mesh.
  - Hidden-geometry cull.
  - Decal anchors.
- **Other buildings re-run:** none. No other building imports the kit yet.

### Round-8 results for wattle_roundhut on 1.0.0

| | Hero | `HUT_KIT_VARIANT` |
|---|---|---|
| Triangles | 744,105 | 662,300 |
| est_hidden_pct | 7.7 % | 6.6 % |
| Material slots | 10 | 10 |
| Mask missing | none | none |
| Needle / zero-area faces | 0 / 0 | — |
| Decal anchors | 105 | 98 |
| Deterministic rebuild | 0 of 229 objects differ | — |

- The variant hut has a 2.9 m radius and a 2.60 m eave.
