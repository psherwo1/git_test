# Vignette 3 - fjord village (street + aerial), kit-based harbour

Renders: `renders/street.png`, `renders/aerial.png` (1920x1080, Cycles OptiX, 192 samples, adaptive, OptiX denoise); previews `renders/preview_*.png`.
Scene: `vignette3.blend`. Rebuild: `python -I scripts/build_vignette3.py <out.blend>`; render:
`python -I scripts/render_vignette3.py <blend> <dir> --shots street,aerial --samples 192 [--preview] [--prefix preview_]`
(python = `C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe`). `scripts/prep_assets.py` builds the asset picks (needs the source downloads).
`scripts/retarget_aerial.py` was the last aerial camera tweak applied to the saved .blend (camera values are not in build_vignette3.py's AER_* constants).

## ASSETS - NOT FOR REDISTRIBUTION
`assets/` holds commercially licensed content (KitBash3D "Secrets of the Luminara" geometry, a downloaded modular wooden pier with textures).
It must stay on this machine and out of git (`blender_village/lookdev/vignette3/assets/` is appended to the root `.gitignore`).
Also do not commit `vignette3.blend` (it links the pier textures) or renders that expose kit geometry without checking the licence.
- `assets/wooden_pier_picks.blend` + `assets/textures_pier/` : modular_wooden_pier sections 01-05, poles, planks (the pier).
- `assets/kb3d_picks.blend` (7 MB): KB3D_SOL boat, fishing nets A/B, rope ladder A, anchor, buoys A/B, life buoy. The download shipped WITHOUT
  its KB3DTextures (empty folder), so only geometry is used; materials are reassigned to village textures (rough_wood, rusty metal).

## What changed vs vignette 2
- Piers/jetty: the modular wooden pier (section_01 shore end, alternating 02/03, section_04 tip), scale 0.85 (deck about 2.1 m wide), deck at +1.0 m. 4 piers + the south jetty.
- Boats: 3 kit boats (hull retextured wood: tar/red/cream); 14 procedural lofted rowboats with thwarts and oars (hollow shell, wood texture).
- Quay: textured planks, rounded bollards (cylinder + sphere cap, iron collar), barrels with hoops; net-drying racks with kit nets, kit anchor, buoys and rope ladders.
- Cliff: rugged east terrain (gullies, ledges), lichened-rock texture at two scales on steep slopes, ~140 displaced textured boulders.
- Trees: 3 species (spruce 3-5 tiers, tall fir, round-canopy broadleaf in green/yellow/rust), log-normal size, per-tree tint.
- Haze: world volume scatter, density falls with height (0.0007/m, 60 m scale), forward scattering.
- Figures: capsule-style bodies, head spheres, hats, arms in muted colours.
- Aerial camera: (48,-100,46) -> (-2,175,8), 26 mm.

## Still placeholder / primitive
Backdrop mountains + arch are still the concept-art image cards. Buildings unchanged. Figures are simple. Hay stacks, fences, woodpiles, well still primitive.
