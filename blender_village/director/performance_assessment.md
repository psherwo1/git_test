# Performance assessment: cinematic lighting and volumetric fog (2026-10-17, session 2)

The client asked for an assessment of the performance implications of cinematic lighting and volume effects such as fog, before more designs and add-ons are built.

**Target** (art bible, note 13): Unreal Engine 5.8 with Nanite, rendered offline with Movie Render Queue (MRQ), no LED volume. The client's desktop has a Ryzen 5 5600X, **16 GB RAM** and an **RTX 3060 12 GB**.

**How to read the numbers:**
- Numbers marked **[measured]** come from this repository: the kit builds, or the Blender vignette on the client's machine (section 6).
- Numbers marked **[estimate]** are engineering estimates for UE 5.x on this class of GPU. They are not yet measured in UE, and the step-5 UE lookdev test must confirm them.
- I have not used UE 5.8 itself. Where the behaviour depends on the engine version (Nanite in ray tracing, the path tracer's fog support), I say so.

## 1. What the village is, in numbers

| Design | Triangles [measured] |
|---|---|
| hilltop_keep (kit reference) | 1,166,874 |
| tower_windmill | 1,146,243 |
| v2_tiered_hall | 980,405 |
| v1_stone_watchtower | 937,933 |
| v4_mixed | 938,453 |
| wattle_roundhut (kit reference) | 878,355 |
| v5_harbour_house | 714,452 |
| v3_longhouse_roundend | 617,342 |
| v6_barn (round 3) | 213,651 |
| **9 designs** | **about 7.6 M unique** |

- At 12-15 designs, the village is about **10-13 M unique triangles** [estimate].
- The 40-50 placements are instances (note 14), so unique geometry does not grow with the placement count.
- Every building is opaque, with no alpha-masked cards and no world-position-offset animation.
- Hidden geometry is at most 15 %.
- There are at most 10 material slots per building, sharing one palette and about 8 texture sets of 2K.

These are the conditions under which Nanite works best.

## 2. Geometry cost in UE: not the bottleneck

- **Nanite rasterisation** scales with screen pixels and visible clusters, not with scene triangles. About 10-13 M unique triangles in about 45 instances is modest for Nanite. On an RTX 3060 the geometry pass for this village should cost a few milliseconds at 1080p [estimate].
- **Disk and streaming:** about 0.15-0.3 GB of Nanite data for 12-15 unique designs [estimate]. This is lower than the plan's earlier 0.7-1.1 GB, which assumed 45 unique buildings. The streaming pool needs about 0.5-1 GB of VRAM.
- **What would make geometry expensive**, and is to be avoided:
  - world-position-offset (wind) on roofs;
  - alpha-masked thatch or foliage cards;
  - thousands of overlapping deferred decals;
  - many shadow-casting moving lights. Virtual Shadow Maps (VSM) re-render the pages that moving lights or geometry invalidate.

  A static sun is cheap; an animated time-of-day costs VSM page invalidation every frame.
- **Ray tracing and the path tracer.** In UE 5.x up to the versions I know, hardware ray tracing (Lumen HWRT, the path tracer) traces Nanite **fallback meshes**, not the full Nanite geometry. Newer versions add a native Nanite ray-tracing path: check what 5.8 does.
  - If fallbacks are used, set a generous fallback triangle percentage on the hero buildings. Otherwise shingle edges, thatch courses and the eyebrow can look coarser in reflections, ray-traced shadows and path-traced frames than in the raster view.
  - Cost: the ray-tracing BVH for about 10 M triangles is roughly 1-2 GB of VRAM [estimate], which fits in 12 GB.

## 3. Lighting options for the film

| Path | Quality | Speed on the RTX 3060 [estimate] | Fit |
|---|---|---|---|
| **Lumen** (software or hardware RT) in MRQ, high-quality settings, temporal / spatial samples for anti-aliasing and motion blur | Very good GI and reflections; soft contact shadows slightly approximate | **About 3-10 s / frame at 1080p; about 15-45 s / frame at 4K** with 8-16 temporal samples | **The recommended main path** |
| **Path tracer** in MRQ | Reference quality: true GI, soft shadows, accurate translucency | **About 1-5 min / frame at 1080p (512-2048 spp, denoised); about 4x that at 4K** | Hero stills, a few key shots, and look reference to tune Lumen against |
| Lumen real-time (editor / preview) | Good | About 25-50 fps at 1080p for this village; lower with volumetric fog at high settings | Layout, blocking, camera work |

**What this means for a hobby film at 24 fps** (1 minute = 1,440 frames) [estimate]:
- Lumen at 1080p, about 5 s / frame: **about 2 hours per film minute.**
- Lumen at 4K, about 25 s / frame: **about 10 hours per film minute.**
- Path tracer at 1080p, about 3 min / frame: **about 3 days per film minute**, and about 5-7 days with fog (section 4).

**Conclusion: Lumen with MRQ for the film, and the path tracer only for selected shots and stills.**

## 4. Volumetric effects, from cheap to expensive

| Effect | What it gives | Cost [estimate] | Notes |
|---|---|---|---|
| **Exponential Height Fog** (no volumetric) | Depth haze, fjord atmosphere | About 0.1 ms | Always on; free mood |
| **Volumetric Fog** (the froxel grid on the height fog) | Sunbeams / god rays through gaps, lit haze, shafts from windows and the boat arch | **About 1-3 ms at 1080p** at default grid; about 4-8 ms at a finer grid | **The main tool.** It is lit by the sun, by local lights and by Lumen (approximately). Temporal reprojection can smear or flicker in fast camera moves; in MRQ, raise the grid resolution and the temporal samples |
| **Local Fog Volumes** (UE 5.3+) | Ground mist pockets in the harbour, the slip, between buildings | About 0.1-0.5 ms each | Cheap and art-directable |
| **Heterogeneous Volumes / sparse volume textures** (VDB clouds, smoke, drifting sea fog) | Real 3D wisps and banks | **Expensive:** about 5-30 ms or more real-time; seconds per frame in MRQ | Use in a few shots only, offline |
| **Path-traced fog / volumes** | Physically correct scattering | **2-5x the path tracer's time**, and much more noise | Reserve for one or two hero stills |

**Fog-specific implications for these buildings:**
- **The god-ray look the concept art invites** (sun through the cruck arch, the boat slip, the tower lookouts, between roofs) is exactly what Volumetric Fog plus VSM shadows does well and cheaply. The buildings' closed junctions (no light leaks, an audit criterion all along) matter here: a light leak becomes a visible beam in fog.
- **Fog hides distance,** so background placements can use the kit's note-15 density controls or LODs without anyone noticing. That is a real saving, if memory ever bites.
- **Lumen in dense fog:** GI inside fog is approximate. Heavy fog with strong bounce light (lit interiors seen through haze) is where Lumen and the path tracer differ most. Tune by eye against path-traced references.

## 5. Memory: the binding constraint is 16 GB of system RAM

- **VRAM (12 GB)** [estimate]:
  - Nanite streaming pool: 0.5-1 GB;
  - textures: 0.1-0.2 GB;
  - VSM pool: about 1 GB;
  - Lumen scene and surface cache: about 0.5-1 GB;
  - MRQ high-resolution buffers at 4K: 1-2 GB;
  - ray-tracing BVH: 1-2 GB, if HWRT or the path tracer is used.

  That is **about 4-7 GB in total. It fits.**
- **System RAM (16 GB)** [estimate]:
  - the UE 5.8 editor with a level this size, plus shader compilation and MRQ: **about 10-14 GB**;
  - Windows and background apps take the rest.

  **This is the tightest budget.** Shader compilation after a material change and path-tracer BVH builds are the usual out-of-memory moments.
- **Recommendation: upgrade to 32 GB of RAM** (2x16 GB DDR4-3200, inexpensive). It is the single most effective hardware change for this production. Until then, close other apps during MRQ renders and render long shots in segments.

## 6. Measurements on the client's machine (Blender vignette, Cycles as a path-tracing proxy)

*To be filled in from `lookdev/vignette/renders/measurements.md`:*
- the scene's triangles;
- per-shot render time and peak memory;
- the fog vs no-fog difference.

Cycles on the RTX 3060 is an order-of-magnitude stand-in for UE's path tracer, not for Lumen.

## 7. Recommendations

1. **Render the film with Lumen in MRQ.** Use the path tracer for hero stills, a few signature shots, and as the reference to tune Lumen against.
2. **Fog stack:**
   - Exponential Height Fog everywhere;
   - Volumetric Fog for sunbeams and haze;
   - Local Fog Volumes for harbour and ground mist;
   - heterogeneous VDB volumes only in the few shots that need moving fog banks, offline.
3. **Keep the kit's constraints, because they are what keeps this cheap:**
   - at most 1 M triangles per design;
   - opaque geometry with no masked cards;
   - hidden geometry at most 15 %;
   - instancing;
   - closed junctions (no light leaks in fog);
   - one shared palette.
4. **Step 5 (the exporter and the UE 5.8 lookdev test) must measure**, and so replace the [estimate] figures above:
   - `stat Nanite`, `stat GPU`, `memreport`;
   - the Lumen and Volumetric Fog cost at 1080p;
   - MRQ seconds per frame for Lumen and the path tracer, with and without fog;
   - whether 5.8 path-traces Nanite natively or needs fallback settings.
5. **Hardware:** 32 GB of RAM is the best upgrade. The RTX 3060 12 GB is adequate for Lumen-based cinematics of this village. The path tracer works, but is slow at film length.
