# Vignette 2 - fjord village (street + aerial)

Renders: `renders/street.png`, `renders/aerial.png` (1920x1080, Cycles OptiX, 192 samples, adaptive, OptiX denoise). Previews: `renders/preview_*.png`.
Scene: `vignette2.blend` (rebuild with `scripts/build_vignette2.py <out.blend>`; render with
`scripts/render_vignette2.py <blend> <dir> --shots street,aerial --samples 192 [--preview]`; backdrop crops by `scripts/prep_backdrop.py`).
Run with `C:\GitHubDesktop\git_test\.bpyenv\Scripts\python.exe -I`.

- 32 building instances of 12 textured designs (collection instances, shared mesh data, no mirroring): v7 x5, v10 x5, v9 x4, wattle_roundhut x4,
  v3 x3, v8 x3, v6 x2 (low houses); accents tower_windmill x2, hilltop_keep, v1_stone_watchtower, v2_tiered_hall, v4_mixed x1 each.
  v5_harbour_house not used (it carries its own water stage).
- Procedural dressing: quay deck, 4 piers + jetty, 2 sailing boats, ~12 rowing boats, fences, haystacks, woodpiles, well, rocks, figures,
  1,500 conifers, fields and paths painted in the terrain shader.
- PLACEHOLDER: the mountain/arch/waterfall backdrop is two emission image cards cropped from the concept-art references
  (`ref/backdrop_street.png`, `ref/backdrop_aerial.png`) at y=670, with an alpha fade into the water. Replace with a real matte or model later.
