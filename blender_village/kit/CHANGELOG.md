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
| wattle_roundhut | 1.0.0 (round 8) | see the round-8 log entry |
| hilltop_keep | not yet (phase-1 script) | — |
| tower_windmill | not yet (phase-1 script) | — |

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
