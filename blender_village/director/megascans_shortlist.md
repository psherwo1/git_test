# Texture shortlist for the village (2026-10-16)

The look to match (ref1/ref2): cool grey lichened fieldstone, silver-brown weathered timber, cream hand-applied daub, olive Nordic moss on roofs and plinths, old dark thatch, dark wrought iron, dull lead.

**This is a hobby project, so the core set below is free.** Two sources:
- **Poly Haven** (polyhaven.com): CC0, free for any use, no account needed. Every texture also has a Blender download, which is handy for a lookdev preview before Unreal.
- **Fab, Quixel Megascans, Personal tier at $0.** Free under the Fab Personal licence, which suits a non-commercial project. Add them to your Fab library while signed in.

**How they fit the pipeline.** The geometry already models every stone, shingle, plank and rod, so use **jointless** surfaces: no textures with baked stone courses, shingle rows or plank joints. Per-piece variation comes from `Mask` R (UV offset/rotation and hue per piece), wear from `Mask` G, and moss/damp from `Mask` B blended with a world-up mask. Decals go on the `decal_anchors.json` points through PCG.

## Free core set, by palette slot

| Slot | Free pick | Free alternative | Notes |
|---|---|---|---|
| `M_stone`, `M_rubble` | [Lichened Rock Wall](https://www.fab.com/listings/6c46ef59-6687-4d28-8931-8530f563f27e) (Fab $0) | [lichen_rock](https://polyhaven.com/a/lichen_rock), [Rough Rock](https://www.fab.com/listings/9544433b-ee7f-4da6-acb2-bd9f4a57c762) (Fab $0), [rock_surface](https://polyhaven.com/a/rock_surface) | Grey with lichen. Blend two by `Mask` R so neighbouring stones differ. |
| `M_stone_dressed` | [rock_surface](https://polyhaven.com/a/rock_surface) | [Rough Rock](https://www.fab.com/listings/2915a771-db40-4140-a7b3-ecff8ea3d9e1) (Fab $0) | Smoother, finer grain for jambs and string courses. |
| `M_mortar` | [grey_plaster_02](https://polyhaven.com/a/grey_plaster_02) | [Rough Concrete](https://www.fab.com/listings/e15b90ea-bce9-4734-9bcb-52c5bc35e1b5) (Fab $0) | |
| `M_daub` | [patterned_clay_plaster](https://polyhaven.com/a/patterned_clay_plaster) | [Construction Plaster](https://www.fab.com/listings/c61bd44e-ce01-47ae-b0b8-eb0f4ff3cc60) (Fab $0), [clay_plaster](https://polyhaven.com/a/clay_plaster) (earthier) | The Poly Haven one is cream and visibly hand-applied, the closest match to ref2's huts. |
| Daub fracture faces | [Dry Cracked Mud](https://www.fab.com/listings/bdf4f488-008c-4da5-981b-c93e8617ab41) (Fab $0) | | On patch edges, via `Mask` G. |
| `M_wattle` | [bark_willow_02](https://polyhaven.com/a/bark_willow_02) | [bark_willow](https://polyhaven.com/a/bark_willow) | Map U along each rod. |
| `M_timber_weathered`, shingles, shakes | [rough_wood](https://polyhaven.com/a/rough_wood) | [wood_planks_grey](https://polyhaven.com/a/wood_planks_grey), [Cracked Wooden Planks](https://www.fab.com/listings/95c7a8b6-12c4-462b-b1be-ebe42439a3c3) (Fab $0) | `rough_wood` is close to a single weathered board, so it suits pieces that are already modelled. With plank textures, scale UVs so one texture board spans one modelled plank or shingle. |
| `M_timber` | [weathered_brown_planks](https://polyhaven.com/a/weathered_brown_planks) | [Worn Wooden Planks](https://www.fab.com/listings/7992bc73-2fd9-4b56-b25a-c549d7d9e1b5) (Fab $0) | Warmer wood for frames, posts and door leaves. |
| `M_thatch` | [thatch_roof_angled](https://polyhaven.com/a/thatch_roof_angled) | [riet_01](https://polyhaven.com/a/riet_01) (dark reed), [reed_roof_04](https://polyhaven.com/a/reed_roof_04) (golden, newer) | No free thatch on Fab; Poly Haven has three. The aged dark one fits the village, with moss layered on top. The straw must run down the slope (UV V downhill). |
| `M_iron` | [Rusty Metal Sheet](https://www.fab.com/listings/54c7decd-5aac-491c-ad3f-cdfde8d4b1c8) (Fab $0) | [Oxidized Coated Steel](https://www.fab.com/listings/e0555a3e-5ca9-4f87-8a41-de5ec8c0289d) (Fab $0) | Dark wrought iron for hinges, straps, rims. |
| `M_lead` | [Dirty Metal](https://www.fab.com/listings/17d58a5d-f1a8-4417-9e6f-f21ed6fc7031) (Fab $0) | | Desaturate to a dull blue-grey. |
| `M_moss` and the moss layer | [Nordic Moss](https://www.fab.com/listings/c24e3a49-0194-4fa0-9dde-72ec490393ac) (Fab $0) | [Moss](https://www.fab.com/listings/e96650f6-2181-4bc6-86cb-6abcfcc04216) (Fab $0), [mossy_rock](https://polyhaven.com/a/mossy_rock) | The olive moss on ref2's cones and plinths. Blend over stone, shingles and thatch with `Mask` B × world-up. |
| `M_earth` | [Mossy Rocky Ground](https://www.fab.com/listings/14bd2176-7db9-47e2-a916-2444d7631e6b) (Fab $0) | | Only the few earth-packing pieces; terrain is built in Unreal. |

## Free decals (for the `decal_anchors.json` types)

| Anchor type | Free pick (Fab Megascans, $0) |
|---|---|
| `moss` | [Moss Patch](https://www.fab.com/listings/b5fad446-5ca0-44b1-96cf-74051936b0e6) |
| `water_streak` | [Leakage](https://www.fab.com/listings/67af749b-5275-420b-9b8f-b172fb5c6b18), [Tileable Leakage](https://www.fab.com/listings/85ea60fc-f408-4cdc-bb35-422a0a00af0b) |
| `soot`, `grime` | [Charcoal Scatter](https://www.fab.com/listings/6f27bd7a-6ce5-46ad-a25d-6f960fb5443e) |
| `plaster_patch`, `repair_patch` | [Damaged Plaster Patch](https://www.fab.com/listings/261cf6b0-2810-4482-9c90-a0a175c7815f) |
| `damp_rise`, `lichen`, `crack`, `rust_stain` | No good free decal found. Paid options: [Damp Concrete Patch](https://www.fab.com/listings/acb8f54e-5a6c-447b-9a19-89b264999960), [Coast African Decal Lichen](https://www.fab.com/listings/ad0480f9-533a-45bf-af4c-10e20f6ee083) ($0.99 each, Personal). Otherwise fake them with the moss and mud surfaces in a decal material. |

## Paid upgrades (Personal tier, $0.99 each), only if a free pick disappoints

| Slot | Upgrade |
|---|---|
| Stone | [Rock Granite With Lichen](https://www.fab.com/listings/6286942b-20ed-4bc7-af59-17d93d5e3838), [Lichen Covered Rock](https://www.fab.com/listings/166c980b-7db2-4167-9809-06a240743da4) |
| Daub | [Rough Plaster Wall](https://www.fab.com/listings/19b9efb8-7012-47fd-aa62-f62c2b69f0c5) |
| Thatch | [Mossy Thatch Roof](https://www.fab.com/listings/5ffc00ed-d5f5-4910-8294-22a19c062051): the closest match to ref2's olive thatch |
| Timber | [Worn Grey Planks](https://www.fab.com/listings/a30a2801-31f2-456a-8917-e4f94014337a) |
| Moss | [Nordic Moss](https://www.fab.com/listings/b0c9cca4-e9aa-4a5f-8d9f-ba4b7168001a) (a second variant) |

## Before texturing

1. Fix the UV grain direction on planks, shingles and rafters (see the production plan), or the wood will read wrong regardless of the texture.
2. Do one lookdev test on the signed-off windmill with 3-4 of these (stone, rough_wood, Nordic Moss, iron) to prove the `Mask`-driven master material. It can be done first in Blender, using Poly Haven's Blender downloads.
