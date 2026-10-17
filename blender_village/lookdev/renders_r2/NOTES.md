# Look test r2: the UV-fixed kit (1.10.0) with the producer's material tweaks

Date: 2026-10-17. Renderer: Blender 5.1.2 Cycles, OptiX on the RTX 3060, 128 samples, 1920x1080. Light, sky,
ground, AgX look and camera rules are the same as in the first test.

## What was rendered

| Building | Shots (`renders_r2/<building>/`) | Compare with |
|---|---|---|
| hilltop_keep | hero, front, entrance_closeup, roof_detail, thatch_closeup | `lookdev/renders/hilltop_keep/` |
| tower_windmill | hero, front, entrance_closeup, roof_detail | `lookdev/renders/tower_windmill/` |
| wattle_roundhut | hero, front, entrance_closeup, wall_closeup | `lookdev/renders/wattle_roundhut/` |
| v3_longhouse_roundend | hero, front, entrance_closeup, thatch_closeup | no earlier textured render |
| v4_mixed | hero, front, entrance_closeup, wall_closeup | `kit/baseline/3_uvfix/lookdev/renders/v4_mixed/` (hero, front, entrance) |

The keep, mill and hut use exactly the same shots as the first test. v3 and v4 were not in the first test, so they
use the generic hero / front / entrance shots. I added a thatch close-up for v3 and a daub and wattle close-up for
v4 so that the tweaks can be seen on them as well.

**Side-by-side sheets** are in `renders_r2/compare/<building>__<shot>.jpg`. In each sheet the left image is the
earlier render and the right image is r2.

There are three ways to compare. Together they separate what the kit's UV fix changed from what the r2 material
grade changed:
- `lookdev/renders/`: the first test. Pre-UV-fix builds, r1 materials.
- `kit/baseline/3_uvfix/lookdev/renders/`: the UV-fixed kit, still with r1 materials.
- `lookdev/renders_r2/`: the UV-fixed kit with r2 materials. This test.

## Sources

The verifier's fresh kit 1.10.0 builds were copied from `kit/baseline/4_verify/<id>/<id>.blend` to
`lookdev/r2_src/<id>.blend`. The copies are byte-identical to the originals (SHA-256 checked before and after the
renders), and the originals were not touched. I fingerprinted each copy with `tools/geom_hash.py`; the results are in
`r2_src/<id>.fingerprint.json`. All five match the 4_verify run on every channel:

| Building | Triangles | Geometry | UV | Mask |
|---|---:|---|---|---|
| hilltop_keep | 1,166,874 | `b2f847333a2ec943` | `968a9ef37e5872c4` | `37113e4c0fc8de83` |
| tower_windmill | 1,146,243 | `89bf4a2a2c60e049` | `b006e70c2dc4750b` | `3c0753f38798dad6` |
| wattle_roundhut | 878,355 | `7e5e7c2df5c4d367` | `c97c88e742be4887` | `46bb1454fa4d264e` |
| v3_longhouse_roundend | 483,508 | `6a7a7ecbea54aa07` | `996bf2646564a2ad` | `b592bfa6f503a77d` |
| v4_mixed | 938,453 | `2e87caad61b68d34` | `230f3672711b12d4` | `07a9171c30138f67` |

The textured scenes were saved as `r2_src/<id>_lookdev.blend`. Only image files from `lookdev/textures/` were loaded;
no bundled .blend was opened and the zips were not touched.

To reproduce:
`powershell -NoProfile -ExecutionPolicy Bypass -File lookdev/scripts/run_r2.ps1`. This runs
`apply_lookdev.py --look r2` on the five copies, at most 3 at once. `--look r1` still gives the first test's grade.

## Before / after: what the kit UV fix changed

These changes come from the geometry-preserving UV and Mask fix in kit 1.10.0. They are already visible in the
`3_uvfix` renders, and r2 keeps them.

### Wood grain

The grain now runs along every board, shingle and shake.
- **Mill, roof_detail:** in r1 the cap shingles showed horizontal streaks across the slope. In r2 they show grain up
  the slope. The tail-vane boards and the boom run lengthwise.
- **Keep:** the door planks show long grain down each plank instead of short cross-hatching. The shake collar reads
  as radiating split boards.
- **Hut:** the threshold beam reads as one long beam. In r1 its grain ran across it like end grain.

### Smearing

The collapsed UVs that smeared the texture into streaks are gone.
- **Keep, thatch_closeup:** the dark vertical streak bands on the thatch course butts are gone. The butts now read
  as clean shadowed steps.
- **Keep, entrance_closeup:** the threshold and post-base tops now show stone texture instead of stretched streaks.
- **Hut:** the wall plate and the shingle edges are clean too. The CHANGELOG 1.10 audit measured the collapsed area
  of the wall plate at 83.5 % -> 0.004 % and of the shingles at 8.11 -> 0.02 m2. I did not frame them in a dedicated
  shot.

### Moss on steps

There is no longer any moss on walked surfaces.
- **Keep:** in r1 both step tops were covered in moss. The mean colour of the upper step top was (0.19, 0.16, 0.05),
  bright green-yellow. In r2 it is (0.43, 0.38, 0.33), grey stone.
- **Hut:** the lower step stone went from (0.24, 0.20, 0.09) to (0.44, 0.39, 0.37).
- **Mill:** the steps show the same change.
- The ends and outer edges of the steps and the plinth tops keep their moss, as the brief asked.

## The producer's tweaks

All five are in `lookdev/scripts/apply_lookdev.py` (`--look r2`, the "r2 grade" section). Each value is the r2
setting, followed by the r1 value it replaced.

### 1. Dressed stone 20-30 % less bright

- The HSV value on the softened lichen_rock is now **0.805 (r1: 1.15)**, which is **30 % less albedo**.
- A partial per-channel cap at linear 0.21 clips the white lichen splotches.
- The wear lightening is 0.08 (r1: 0.12).

Measured in the keep entrance_closeup, as the mean of the 8-bit display values (same camera and light):

| Area | r1 luma | r2 luma | Change | Highlight (99th percentile) |
|---|---:|---:|---:|---|
| Right jamb | 0.570 | 0.503 | -12 % | 0.717 -> 0.636 |
| Left jamb | 0.542 | 0.468 | -14 % | 0.714 -> 0.630 |
| Arch voussoirs | 0.532 | 0.463 | -13 % | 0.704 -> 0.616 |

That is about **25 % less light** once the display encoding is undone (sRGB-to-linear, approximately). AgX squeezes
the on-screen step to 12-14 %. The rubble wall next to the door is unchanged (0.446), so the dressed work still reads
a little lighter than the rubble, as it should.

If the producer meant 20-30 % darker *on screen*, the value needs to drop to about 0.55. At that point the dressed
stone would be as dark as the rubble.

### 2. Thatch more olive and mossy, less golden

- **Grade.** The multiply is now (0.95, 1.05, 0.55) (r1: a golden (1.35, 1.12, 0.78)), with saturation 0.85 and
  value 0.72.
- **Olive film.** An olive algae film is mixed in everywhere: 20 % on the walls rising to 35 % on up-facing slopes.
- **Moss.** Moss gain is 7 (r1: 5.5) with the threshold lowered to 0.25, plus broad world-space moss patches. The
  moss itself is slightly greener (hue +0.025).

Result in the lit area of the keep thatch_closeup: the mean colour went from (0.57, 0.46, 0.36) to (0.47, 0.41, 0.28).
R/G fell from 1.24 to 1.14 and B/G from 0.78 to 0.68, so the thatch is less golden and more olive. It reads as ref2's
mossy reed on the keep (thatch_closeup, roof_detail, hero) and on v3 (hero, thatch_closeup).

### 3. Plaster: tile half the size, lower normal strength

- **Tile.** The tile is 1 m (r1: 2 m), so the trowel swirls are half the size.
- **Normal.** The normal strength is **0.3 (r1: 0.6)**.
- **Albedo strokes.** The dark trowel-stroke lines in the albedo are pulled 50 % towards the image mean.
- **Row break-up.** A second sample at a non-commensurate 0.74 m tile is blended in through low-frequency world
  noise. The first r2 pass still showed regular rows of arcs on the skylit, shaded daub of v4's wall_closeup, which
  is why I added it.

The standard deviation of luma across the lit daub, which measures how strongly the pattern shows:
- hut wall_closeup: 0.069 -> 0.062;
- the smooth daub right of the hut door: 0.023 -> 0.014.

On the hut the fish-scale reading is gone. On v4's shaded wall the arcs are still faintly there, because the swirl
pattern is part of this texture (see open points).

### 4. Wattle uses a willow bark texture instead of a flat colour

The rods now have a bark texture along each rod, with per-rod offset and value / hue jitter, wear, damp and a bark
normal map (strength 0.8). This shows in the hut wall_closeup, hut entrance, v4 wall_closeup and v4 entrance.

The kit's rod UVs wrap once round the rod (U) and run along it at about 11 units per metre (V). The bark is mapped at
(0.30, 0.36), so one tile covers about a third of the circumference and about 0.25 m along the rod.

**The bark is a proxy.** The shortlisted `bark_willow_02` (Poly Haven) has not been downloaded, and downloading needs
the client's go-ahead. Until then the rods use the `rough_wood` images, compressed round the rod and graded to
grey-brown willow (multiply (0.95, 0.75, 0.50)). The script switches to the real texture automatically once its images
are extracted to `lookdev/textures/bark_willow_02_2k.blend/textures/` with Poly Haven's file names.

### 5. Windmill fan blades less pale

The blades share `M_timber` with the posts and doors, so the palette slot was left alone. Instead, the r2 script sets
a per-object custom property `lookdev_darken = 0.45` on `*_wheel_blades` (MILL and V4M). The material reads it through
an Object Attribute node and applies value x (1 - d) and saturation x (1 - 0.3 d). In Unreal this would be a scalar
on a per-mesh material instance.

Measured on the lower blade fan in the mill hero: luma went from 0.581 (r1) and 0.556 (3_uvfix) to **0.501**, a mid
weathered brown instead of a pale beige. The r2 hero, front and roof_detail shots and the v4 hero show it.

## Other fixes made after looking at every render

- **Lead read near-white.** The r2 renders showed the keep's wing valley flashing as a pale sliver against the olive
  thatch (roof_detail), and the hut and v4 cap collars as near-white cones (hero).
  - Change: the r2 lead base is darker, (0.115, 0.122, 0.135) (r1: (0.20, 0.215, 0.24)), with darker grime.
  - Result: the flashing now reads as dull lead.
- **The v3 entrance close-up was missing.** v3's door is merged into `LONG_body_wall_frames`, so the door finder
  found nothing.
  - Change: `find_door` now falls back to the entrance the kit stores on the scene (`kit_entrances`, kit 1.10).
  - Result: the v3 entrance_closeup is rendered.
- **New script options.** `--look`, `--render-dir` and `--blend-out`. The v3 and v4 close-up shots were also added.

## Open points for the producer (not changed here)

- **Willow bark proxy.** Approving the `bark_willow_02` download would replace the `rough_wood` proxy on the wattle.
- **Plaster swirls.** The swirls are part of `patterned_clay_plaster`, so they stay faintly visible in shade (v4
  wall_closeup). The shortlist's `clay_plaster` (earthier, without the swirl pattern) is the cleaner fix.
- **Pale weathered timber.** `M_timber_weathered` and `M_roof_shingle` are graded silver-grey (r1 values, untouched).
  In direct sun they read almost white on v3's door leaf (entrance_closeup), on the keep's wing door and on v4's hut
  roof, which also carries little moss. If the producer wants these less pale too, the same per-object darken or a
  slot-wide value cut would do it.
- **v3 thatch courses.** v3's thatch reads as regular horizontal bands in the hero. That comes from the geometry, not
  the material. The 1.10 changelog also notes that v3's body-thatch UVs run 55 % up and 44 % down the slope; I could
  not see that in these shots.
- **Dressed stone on screen.** See tweak 1 for the on-screen versus albedo reading of "20-30 %".

No kit code was changed, so there is no CHANGELOG entry. Everything above lives in `lookdev/scripts/`.
