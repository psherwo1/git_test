# Valley terrain blockout: report

## Read this first

**No `.blend` file and no Blender render exist.** Blender is not installed in this container, and you asked me not to install anything. Everything below was produced with numpy and PIL instead.

| Deliverable | Status |
|---|---|
| `.blend` file | **Not produced.** `blender_build.py` builds it when you run it in Blender (command below). |
| 32-bit EXR, 2048² | Produced by `run_pipeline.py`, **not rendered by Blender**. |
| 16-bit PNG, 2017² | Produced by `run_pipeline.py`, **not rendered by Blender**. |
| `bake_meta.json` | Produced. |
| Report and check results | This file. The check results come from the numpy bake, not from a Blender render. |
| Screenshots | Previews from my own numpy renderer, **not Blender viewport screenshots**. |

**One of your four checks fails.** The waterfall base reads about +41 m high. It is not an axis or scale error; the cause is below.

## Files (`terrain_blockout/`)

- `outputs/valley_blockout_height_2048.exr`: 32-bit float EXR, RGB with R=G=B. Uncompressed, 50 MB.
- `outputs/valley_blockout_height_2017_16bit.png`: 16-bit grayscale PNG.
- `outputs/bake_meta.json`: the numbers for Unreal.
- `outputs/blockout_vertices_101x101_m.csv` and `.npy`: the 101×101 mesh heights in metres. Row 0 is the north edge.
- `outputs/pipeline_results.json`: every number quoted in this report.
- `blender_build.py`: the Blender script. `terrain_common.py` and `run_pipeline.py`: shared numpy code and the standalone run.
- `inputs/`: your PNG and JSON. `valley_map_polygons.json` holds the water and playable-edge outlines I took from the Valley Map artifact, for cross-checks only.
- `previews/`: the screenshots.

## Check at your four coordinates

Expected values are from your brief. Both differences use the baked files read back at those map coordinates. The tolerance is 3 m.

| Point | (x, y) m | Expected m | Raw source m | EXR m | PNG m | Δ EXR | Δ PNG | |
|---|---|---|---|---|---|---|---|---|
| Waterfall base | 542, 1932 | 12.9 | 12.90 | 53.57 | 54.53 | **+40.67** | **+41.63** | **FAIL** |
| Terrace hamlet | 337, 1882 | 195.6 | 195.50 | 195.69 | 195.73 | +0.09 | +0.13 | ok |
| North town | 737, 537 | 5.6 | 5.60 | 5.65 | 5.61 | +0.05 | +0.01 | ok |
| East town | 1737, 1417 | 3.0 | 3.00 | 3.13 | 3.10 | +0.13 | +0.10 | ok |

**The axes and scale are right.** Reading your source PNG directly (row = y/5, column = x/5, no flip, no transpose) gives your expected value at all four points, to within 0.1 m. A transpose or a vertical flip gives wrong values at every point. The three flat-ground points then agree with the baked files to within 0.15 m.

**The waterfall base fails because of the 25 m mesh, not an axis or scale error.**
- The point sits at the foot of an almost vertical wall. The source drops from about 170 m to 13 m within about 10 to 15 m in plan, a slope of about 86°.
- A 25 m mesh cannot represent that. With **no smoothing at all**, the 25 m mesh reads 44.3 m at that point. The 15 m Gaussian adds about 10 m on top (54.8 m).
- Smaller sigma does not fix it (5 m gives 44.0 m, 10 m gives 48.6 m), so I did not tune it to pass.
- The same limit applies to the whole long valley wall: near-vertical cliffs become steep ramps. Gaea will have to re-cut them. The unsmoothed reference object keeps the original walls for that.

Options if you want this point to pass:
1. Refine the mesh locally, for example a 5 m patch along the long wall. This breaks the uniform 100×100 spec.
2. Move the check point 15 to 20 m out onto the flat ground.
3. Accept it. The point is on a cliff foot, and the other three show the scale and axes are right.

## Lakes

The water level is **0.0 m**. This is the data minimum, and 30,973 samples (0.77 km²) sit exactly on it as one connected flat body. The Valley Map artifact's water outline matches it: it has the same bounding box and its area is 1.4% smaller (763,249 vs 774,325 m²). The artifact also notes both lakes and the river share one water level.

| Lake | Level m | Area m² | Area ha | Centroid (x, y) m | Bounding box x, y m |
|---|---|---|---|---|---|
| West Lake | 0.0 | 461,275 | 46.1 | 612, 1054 | 125–1120, 480–1715 |
| East Lake | 0.0 | 305,825 | 30.6 | 1763, 1704 | 1165–2135, 1260–1990 |

- **East Lake island:** the island at about x 1905–2040, y 1585–1680 is a hole in the lake mask and has no plane over it.
- **River:** the two lakes are joined by a river, with 7,225 m² (289 samples) not counted in either lake. It is **narrower than the 25 m mesh spacing**, so the blockout cannot carry it. I left it to Gaea. It is kept in the reference object.
- **Lake split:** I separated lakes from river by removing anything narrower than about 40 m (a 20 m radius opening).
- **Possible clamp:** 0.0 m is also the minimum of the whole file. If the source clamped anything lower to 0, the real water depth is not recorded.
- **Other flat patches:** flat patches at 1.2, 2.8 and 2.9 m exist (East town, for one, sits on a 2.9 to 3.0 m flat). The artifact lists only two lakes, so I treated these as land.
- **Shoreline:** land is blurred with the lake pixels masked out, so the shore is not pulled toward the water. Any mesh vertex whose 25 m neighbourhood is mostly lake is pinned to exactly 0.0 m. The lake planes follow the 5 m mask outline.

## bake_meta.json

| Key | Value |
|---|---|
| `map_width_m` | 2500.0 |
| `min_height_m` | 0.0 |
| `max_height_m` | 389.0 |
| `pixel_size_m` | 1.2394646 (2017 px PNG) |
| `exports.exr.pixel_size_m` | 1.220703125 (2048 px EXR) |
| `exports.png.vertex_spacing_if_corner_aligned_m` | 1.2400794 (2500 / 2016) |
| `blockout_actual_height_range_m` | 0.0 to 369.06 |

- **Encoding:** value = (height_m − 0) / (389 − 0), in both the EXR and the PNG. The 16-bit PNG maps 0 to 65535 onto 0 to 389 m, which is your source mapping. The blockout only reaches 369 m, so the PNG uses about 95% of its range.
- **Pixel size:** I used 2500 divided by the pixel count, because a render samples pixel centres. If you import the PNG as a 2017-vertex landscape spanning the whole map, the vertex spacing is 2500/2016 instead. That is a 0.6 m difference over the map.
- **Unreal Z scale:** for a 389 m span, with the usual convention that the full 16-bit range at Z scale 100 is 512 m, Z scale = 100 × 389 / 512 = **75.98**. Because 0 m is encoded as 0, the landscape then needs a Z offset of about +194.5 m. I have not verified this against UE 5.8, so please check it.

## Verification and its limits

- **Round trip:** my EXR writer's output reads back bit-identical in both my own reader and ffmpeg's independent EXR decoder (all three channels, 0 difference, range 0 to 369.15 m). The PNG reads back as 16-bit, 2017×2017.
- **Playable area:** the playable area, taken from the artifact's dashed edge outline, is 4.25 km² and peaks at 202.1 m in the source, matching your "near 202 m". It peaks at 200.8 m after smoothing. The rim mountains are inside the same 2500 m file, so I did not crop anything.
- **Smoothing error over the whole map:** against the source, the bake has an RMS error of 7.4 m and a 95th-percentile error of 15.7 m. The maximum is 98.6 m, on cliff faces.
- **Blender triangulation:** a Blender render splits each quad into two triangles, while my bake interpolates each quad bilinearly. On steep quads the two can differ by up to **13.9 m** (99th percentile 6.8 m; 22% of cells differ by more than 1 m). Flat ground is not affected, so the three passing points would not change.
- **`blender_build.py` has never been run in Blender.** I ran its logic against a fake `bpy` that feeds it the real input and output images. That confirmed the following:
  - the source-data guard passes and the row-flip logic is right;
  - the terrain mesh faces point up and the north edge is at Y = 2500;
  - the mesh vertex heights match the standalone pipeline;
  - the grid cells land correctly (A1 at the north-west corner, Y25 at the south-east);
  - the check table reproduces the table above.

  A fake `bpy` accepts any attribute, so it **cannot catch a wrong Blender API name or enum**. The script prints its own check table at the end, and the real `.blend` can be checked against the table above.

## Run in Blender

```
cd terrain_blockout
blender -b --factory-startup -P blender_build.py -- --out outputs_blender
```

This writes `valley_blockout.blend`, `valley_blockout_height_2048.exr`, `valley_blockout_height_2017_16bit.png`, `bake_meta.json`, `blender_checks.json` and two Workbench screenshots into `outputs_blender/`.

- **Collections:** `Blockout`, `Lakes`, `Grid` (sub-collections `Grid_Lines`, `Grid_Cells`, `Grid_Labels`), `Reference` (hidden) and `Bake`.
- **Blockout mesh:** a plain 101×101 mesh with no modifiers, so it is hand-editable.
- **Lakes:** `Lake_West` and `Lake_East`, two flat planes at 0.0 m.
- **Grid:** the lines, plus 625 cell objects `Cell_A1` to `Cell_Y25` and 625 text labels.
- **Bake:** Cycles at 1 sample with a 0.01 pixel filter, emission only, black world, standard view transform, and no film transform.
- **PNG colour handling:** the PNG render switches to the **Raw** view transform for that one render. A PNG is display-referred, and with Standard the sRGB curve would be baked into the heights. The EXR is scene-linear either way.

## Assumptions and simplifications

- **Coordinates:** Blender world X = map x, Y = 2500 − map y, so a top-down camera sees map y = 0 at the top. Grid columns A to Y run west to east and rows 1 to 25 run north to south.
- **Smoothing:** a Gaussian with σ = 15 m. It passes about 29% of a 60 m wavelength, about 64% of 100 m and about 90% of 200 m.
- **Mesh sampling:** the mesh samples the smoothed field at the vertices, with pixel centres at (c + 0.5) × 5 m.
- **Bake range:** I fixed the bake range to 0 to 389 m, the source scale, and not to the blockout's own 0 to 369 m. Say if you would rather use the full 16-bit range.
- **EXR contents:** the EXR stores normalised 0 to 1 values, not metres, so it matches the PNG.
- **Bake height field:** the bake is the higher of the terrain mesh and the lake plane at each pixel, which is what a top-down render of the two would show.
- **Previews:** the previews use my own simple shading and an oblique painter's-algorithm render, so they will not look like Blender's.
