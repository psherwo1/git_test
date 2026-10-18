# Vignette render measurements

Machine: Windows 11, RTX 3060 12 GB, 16 GB RAM. bpy 5.1.2, Cycles OptiX GPU, 1920x1080, OptiX denoiser,
adaptive sampling (threshold 0.01), max bounces 8, volume bounces 0, AgX Medium High Contrast (inherited r2).
Persistent data OFF: every render re-syncs the scene and rebuilds the BVH, so each wall-clock time below covers
scene sync + BVH + texture upload + path tracing + denoise + PNG save. Opening the .blend takes about 3-4 s and is
not included.
Scripts: `scripts/build_vignette.py` builds the scene, `scripts/render_vignette.py` renders it (run through
`scripts/run_final.ps1`, which also samples nvidia-smi every 0.5 s), and `scripts/analyze.py` collates the numbers.
Raw data: `renders/measurements.jsonl`, `renders/b512/measurements_b512.jsonl`, `logs/gpu.csv`.

## Scene

| item | value |
|---|---|
| total render triangles | **7,919,786** |
| of which buildings (9) | 7,594,042 (keep 1.17 M, windmill 1.15 M, hall 0.98 M, mill-house 0.94 M, watchtower 0.94 M, roundhut 0.88 M, harbour house 0.71 M, longhouse 0.62 M, barn 0.21 M) |
| terrain | 325,744 (0.5 m grid over 160 x 126 m, 6 m grid out to the fjord walls) |
| mesh objects (renderable) | **1,288** (1,282 building parts + terrain, water, harbour bed, 3 quay land boxes) |
| other objects | 9 placement empties (BLD_<id>), 1 sun, 1 camera, 1 fog domain (only in B) |
| images | 26 unique 2K textures. Appending the nine files had created 198 image datablocks; 172 were duplicates by file path and were merged on build, so each texture is loaded once |
| materials | 92 |
| .blend | `work/vignette.blend`, 451 MB uncompressed (textures are external, not packed) |

## Per render

GPU baseline, measured by nvidia-smi before the render process loaded anything: **2,620 MiB of 12,288 MiB**. This
figure includes the desktop and any other agent's process, and the "GPU used" column includes it too.

| render | light | samples | wall-clock s | Cycles "Mem" MB | GPU used during render (nvidia-smi, all processes) MiB | bpy process RAM, working set after / peak MB | system RAM used before -> after GB (of 15.9) |
|---|---|---|---|---|---|---|---|
| s1_A | A r2 day | 128 | 10.6 | 2,608 | 5,637 | 1,466 / 4,197 | 10.00 -> 10.69 |
| s2_A | A | 128 | 11.0 | 2,608 | 5,614 | 1,560 / 4,264 | 11.05 -> 10.89 |
| s3_A | A | 128 | 11.1 | 2,608 | 5,114 | 1,789 / 4,197 | 10.04 -> 11.03 |
| s4_A | A | 128 | 12.9 | 2,608 | 5,612 | 1,392 / 4,211 | 11.03 -> 10.66 |
| s1_B | B cinematic + fog | 128 | 21.8 | 2,783 | 5,748 | 1,860 / 4,346 | 11.25 -> 11.12 |
| s2_B | B | 128 | 21.2 | 2,783 | 5,834 | 1,862 / 4,346 | 11.06 -> 11.11 |
| s1_B (renders/b512) | B | 512 | 35.2 | 2,784 | 5,834 | 1,791 / 4,277 | 10.03 -> 11.05 |
| s2_B (renders/b512) | B | 512 | 39.0 | 2,784 | 5,334 | 1,845 / 4,336 | 11.08 -> 11.11 |

Notes on the memory columns:
- Cycles in 5.1 reports only "Mem: NNNNM" in its render stats; there is no separate "Peak" field any more. The
  values above are the largest "Mem" seen during each render.
- nvidia-smi puts the render process at about 2.5-3.2 GB of GPU memory above the baseline, which matches Cycles' figure.
- The bpy process's peak working set is about 4.2-4.3 GB. That peak is reached while the .blend loads and textures
  are prepared; the working set during rendering is 1.4-1.9 GB.
- System RAM stayed at 10-11 GB used out of 15.9 GB, but that includes everything else running on the machine.
- Nothing ran out of memory, and no settings, geometry or textures were reduced. GPU headroom is about 6.4 GB.

## A (no fog) vs B (fog), same 128 samples

| shot | time A -> B | memory (Cycles Mem) A -> B | GPU used A -> B |
|---|---|---|---|
| s1 aerial | 10.6 s -> 21.8 s (**x2.06**, +11.2 s) | 2,608 -> 2,783 MB (**+175 MB**) | 5,637 -> 5,748 MiB |
| s2 eye level | 11.0 s -> 21.2 s (**x1.93**, +10.2 s) | 2,608 -> 2,783 MB (**+175 MB**) | 5,614 -> 5,834 MiB |

Fog setup: one homogeneous Principled Volume cube, 1000 x 1000 m in plan, Z -2..25 m. Density 0.0025 /m,
anisotropy 0.6, colour (0.92, 0.88, 0.82). Single volume scatter (volume bounces 0).
B lighting: sun at 10 deg elevation from the west, slightly south (azimuth vector (-0.97, -0.25)), strength 9.0
(r2 uses 6.0, but 144 m of fog dims the sunlight by about 30 %), colour (1.0, 0.56, 0.28).
B sky: the same multiple-scattering (Nishita-family) sky at 10 deg, air density 1.5 (A: 1.0), aerosol 6.0 (A: 2.5),
background strength 0.12 (A: 0.10).
In practice the fog doubles render time and adds less than 0.2 GB of memory. Memory is not a constraint for fog at
this scene size; time is.

## Fog noise

Method: a 480x270 crop at full resolution (horizontal 37.5-62.5 %, vertical 50-75 % of the frame, the haze over the
village centre) was rendered three ways with adaptive sampling off: denoised at N, raw at N, and raw at 4N.
- Raw noise: sigma = RMS(raw N - raw 4N) / sqrt(1.25), measured in 8-bit display levels.
- Samples needed: "clean without a denoiser" means noise of 1.5 levels RMS or less, assuming noise falls as
  1/sqrt(N).

| crop | N | raw noise at N (8-bit levels RMS) | at 4N | samples needed to be clean without a denoiser |
|---|---|---|---|---|
| s1_A (no fog) | 128 | 2.06 | 1.03 | about 240 |
| s2_A (no fog) | 128 | 2.17 | 1.08 | about 270 |
| s1_B (fog) | 128 | 3.10 | 1.55 | **about 550** |
| s2_B (fog) | 128 | 2.62 | 1.31 | **about 390** |

- Without denoising, fog raises the raw noise by about 1.2-1.5x at equal samples. That is about 1.5-2.3x the
  samples to reach the same raw cleanliness (400-550 spp vs 240-270 spp).
- With the OptiX denoiser, 128 spp B is already usable. Comparing the full frames at 128 spp vs 512 spp (both
  denoised): s1_B differs by 1.02 levels RMS, with 0.65 % of pixels off by more than 6 levels; s2_B by 1.38 levels
  RMS, with 1.36 % of pixels off by more than 6 levels. The differences are in the low-contrast haze gradients and
  shadow-shaft edges, which look slightly blotchy at 128 spp. Recommended B setting: 256 spp denoised, or 512 for
  hero frames. Because adaptive sampling stops early, 512 spp costs only 35-39 s here, not 4x the 128-spp time.

## Caveats

- One other agent may have been using the GPU or CPU at the same time; the baseline column shows what was already
  on the GPU. All renders ran one at a time in a single bpy process per batch.
- At 0.0025 density the god rays are faint. Shadow shafts are visible in s1_B as long streaks across the haze, but
  there are no strong beams.
  - Stronger beams would need either denser fog (cost goes up roughly with density x distance, and noise goes up)
    or a heterogeneous height-falloff or noise volume (a gradient-driven density switches Cycles from
    homogeneous to ray-marched/null-scattering volumes). Expect noticeably more than 2x the time; this was not
    measured.
