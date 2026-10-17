# Variant v4_mixed: the mill-house

## v4_mixed round 1 — builder entry

**What I built.** A **mill-house**: a miller's wattle-and-daub roundhouse built against a small stone tower mill
that carries a fan wheel. The village has no mill-house yet. The building mixes module families from all three
heroes and is assembled from kit modules only.

- **House wing (hut family, `RoundFrame`, prefix `V4H`).**
  - Wall radius 2.85 m, eave 2.45 m.
  - Dry-stone plinth, daub wall with its exposed-wattle patches moved to the side away from the mill, pegged wall
    plate.
  - 51° chunky-shingle cone with the ensemble age pass.
  - Projecting framed door facing −Y, with its step and the interior behind it.
  - The apex carries the **keep family's** turned finial over a fitted lead hat (pitch 48°, shallower than the roof)
    instead of the hut's spike.
- **Mill wing (drum family, `DrumFrame`, prefix `V4M`).**
  - Slender battered rubble drum: r 1.95 → 1.82 m, 5.30 m to the cornice.
  - The balustrade band (3.62–3.99 m) and a 6-bay blind arcade are lifted clear of the house roof, so the roof
    meets plain rubble just under the band's lower string course.
  - Arched door facing −Y with its step; two slit windows on the +X and back faces.
  - Shake apron, boarded smock tower (6.35–10.05 m), hipped cap (yaw 25°).
  - 12-blade fan wheel (tip radius 3.05 m), tail vane on a 4.9 m rear boom.
  - No raking props.
- **Junctions (new kit module `components/junctions.py`, using keep-family pieces).**
  - **Roof to tower.** The house cone runs into the drum between z 2.61 and 3.45 m, over 79° of drum azimuth.
    The real roof-top / drum-face line is traced by ray casts on the built shingles. It is closed by one continuous
    lime-mortar flaunching band (the keep's `thatch.flaunch_loop` / `mortar_fillet`), 2.5 cm over the highest
    shingle and its back buried 3.5 cm in the masonry. Lead end-aprons cover the cut eave lips where the eave dies
    into the stone (object `V4J_roof_tower_fillet`).
  - **Wall to tower.** The daub wall runs 0.12 m into the drum. At both crossings a hewn abutment post (the keep's
    `hewn.hewn_square`, 0.22 × 0.22 m) stands from the plinth to the wall plate, with its drum half let 4 cm into
    the masonry so it straddles the daub / stone seam. A mortar pointing bead follows the post / stone seam up the
    batter (`V4J_abutment_posts`, `V4J_abutment_pointing`).
  - **Plinth to footing.** The house plinth boulders run into the drum's footing course (stone into stone).

**Plan.** House centre (−1.70, 0.15), drum centre (2.82, 1.36), 4.68 m apart on a 15° line. Both doors face −Y;
the house door is the principal entrance. The footprint is centred on the origin within about 0.3 m. The wheel and
tail push the bounding box to +X / +Y.

**The recipe.** `buildings/variants/v4_mixed/build_v4_mixed.py`: 92 non-blank, non-comment lines, including the
module docstring.
- It is two `Wing`s and two junction steps. Each wing is a list of the same component calls a hero recipe makes,
  with parameter dicts: `HOUSE`, `HOUSE_PATCHES`, `APEX`, `MILL` (drum / tower / apron / cap / wheel / tail) and
  `MILL_RUBBLE`.
- A different mill-house is a different `HOUSE_AT` / `MILL_AT` and parameter set.
- Environment switches: `V4_OUT` builds to scratch; `V4_FAST=1` skips the cull (look-dev only).

**New kit modules** (recorded in `kit/changes/v4_mixed.md`):
- **`village_kit/compound.py`.** `Wing` and `build_compound` assemble several family frames in one building.
  - Each wing is built at the origin with unmodified family components, then parked, then placed. Meshes are
    baked; pooled duplicates keep their matrices; anchors are transformed with the wing.
  - Junction steps run after placement.
  - ONE note-6 cull runs over every wing's targets. It uses each wing's actor / door / crane rings and drops
    viewpoints inside another wing's body.
  - The merged anchors are re-audited on the whole building (`anchor_audit`). Anchors covered by the neighbour or
    a flashing are dropped, and the rest are thinned per type to 120.
  - Step helpers: `configure` and `patches_by_azimuth`.
- **`components/junctions.py`.** `roof_tower_flashing` and `wall_tower_abutment`, which run on generic body
  descriptions (`tower_of`, `round_wall_of`), plus `trace_roof_on_tower` and `end_apron`.
- **`components/round_apex.py`.** `turned_apex`: the keep's turned finial and lead hat on any `RoundFrame` cone.

**Bug fixes to existing kit modules.** Each fix is behaviour-identical for the heroes.
- `conical_roof.build_eave_closure` looked up the literal `HUT_` names.
- `rotor_checks` crashed on a mill without props.
- `tail_vane.tail_boom` left iron bands floating past a boom shorter than the hero's.

**Stats** (`renders/variants/v4_mixed/round_01/stats.json`):

| Measure | Value |
|---|---|
| Triangles | 1,391,180 (1,587,416 before the compound cull; −99,224 polygons) |
| Hidden (est_hidden_pct) | 13.5 % |
| Material slots | 12, all from the palette |
| `mask_attribute_missing` | none |
| Objects | 285 |
| Bounding box | x −5.18 … 6.27, y −3.79 … 5.85, z −0.041 … 14.00 (size 11.45 × 9.64 × 14.04 m) |
| `.blend` | 31.7 MB, compressed |
| Decal anchors | 120 (191 placed; 19 dropped by the whole-building audit; 52 thinned) |

- Anchor counts by type: crack 29, moss 19, water_streak 19, damp_rise 14, lichen 11, rust_stain 7,
  plaster_patch 6, repair_patch 6, soot 5, grime 4.
- Anchor gates: house anchors `validate_anchors` (applied); mill anchors `drum_tower_decals_gated` (snap, validate,
  audit); every anchor `anchor_audit` on the finished building.

**Renders.** `renders/variants/v4_mixed/round_01/`: all six views at 24 samples. I inspected every view, plus
scratch close-ups of both junctions, both posts and the tail.
- No gaps or see-through pixels at the roof / drum line. The eave lips die into the stone under the lead aprons.
- The posts cover the daub / stone seam.
- The band sits clear above the flaunching.
- A floating iron band past the shortened boom end was found in look-dev and fixed in the kit (above).

**Known gaps.**
- From most angles the flaunching band reads as a soft mortar fillet half-hidden by the chunky shingle butts. In
  the round-1 renders it is not a strongly legible lead / mortar line.
- The house uses the kit-1.0.0 default daub coat (smooth). This was chosen for the triangle budget, and per note 12
  no surface detail was added.
- The junctions are built for round tower bodies (`tower_of` = `DrumFrame`). Another family's round body needs a
  one-line adapter.
- The compound cull is slow on the shared CPU (about 30 min, 15 targets × ~580–660 viewpoints).
- Under memory pressure a spawn worker can die. `core.visibility_cull` then hangs: respawned workers cannot import
  bpy. This happened in one of my runs (MemoryError), and I killed and re-ran that run with 3 processes.
- The house's eave closure (hut module) faces inward.
- No windows in the daub house; the kit has no window module for a round daub wall yet.

**Hero re-runs.** Existing kit modules were changed, so all three heroes were rebuilt to scratch via `KEEP_OUT` /
`HUT_OUT` / `MILL_OUT`, after the last kit edit. All three built without errors at exactly their recorded
triangle counts:

| Hero | Triangles | Record | Notes |
|---|---|---|---|
| tower_windmill | 1,146,243 | 1,146,243 | clearance PASS, 106 anchors |
| wattle_roundhut | 876,619 | 876,619 | |
| hilltop_keep | 1,166,874 | 1,166,874 | |
