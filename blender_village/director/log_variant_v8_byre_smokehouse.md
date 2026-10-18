# v8_byre_smokehouse (BYRE) -- variant log

## Design brief
A long low single-storey rubble byre / smokehouse (about 12 x 5 m, wall 2.4 m) under a thatch loaf with round hips both
ends (note 19), ONE thatch eyebrow on the front slope over a hay-loft window (note 18), an integral ROUND stone smoke
hood rising through the east round hip (roof_addons.chimney), and a rounded apsidal lean-to (lean_to roof_ends="round")
on the back long wall. Wide plank cart door (the kit has no arched-head door; plain door used).
Recipe: `buildings/variants/v8_byre_smokehouse/build_v8_byre_smokehouse.py` (template v7_cottage + a1 lean-to). No new kit code.

## Dimension table (summary)
main 12.0 x 5.0 m, wall_z 2.4, pitch 46, crown 0.50, ridge ~5.4 m (hip loaf, eave 2.4 m; eave arches lift it to ~4.0 m over
the lean-to and ~3.0 m over the door); eyebrow x=+1.8 front; stack at x=+6.15 r 1.0 (batter 3.5, shoulder 2.9); cart door
x=-2.6 1.7 x 2.05; lean-to centre x=-1.2, 4.4 wide x 1.8 deep, z_face 2.44, pitch 13, overhang 0.12.

## Preview (FAST build, round 0, ungraded)
Tris 424,272 (uncut; cull will reduce). Seal probes: roof/stack ring 0 leaks, lean_to/wall 0 leaks. Previews in `preview/`.
Deviations to the kit defaults, all in the recipe: lean-to below_clear 0.05 (default 0.08), headroom guard (1.7, 1.55) (default
2.10/1.95, the lower 2.4 m wall forces a low hay lean-to), gate=False (lean-to is a hay store, not an entrance), brace drop 0.20.

## PRODUCER NOTES
(placeholder)

## Round 2 BUILD (producer note 20, wattle and daub across the village) -- FAST preview, ungraded
Changed in `build_v8_byre_smokehouse.py` (kit: new `components/daub_wall.py`, optional `lean_to(ends="none")`; see kit/CHANGELOG.md 1.21.0):
- The rounded lean-to is now an enclosed wattle-and-daub APSE outshot: no end walls / posts / plate (lean_to ends="none", plate=None), a superellipse
  apse (half width 2.0, depth 1.55, ne 2.2, max eave rho 0.83 = inside the oval roof with 0.3-0.45 m oversail) of a rubble plinth
  (0.55 m, 0.40 thick, a hand wider than the wall, path_stone_wall RUBBLE_LARGE, quoins off on the curve) under a daub wall between 4 hewn
  posts (5 bays) with the hut's coat section, bedded foot, post slit dips, and 2 fallen-out patches showing the hut's woven wattle (49 rods).
  The porch-hood reading is gone: the roof is the oval over a round wall.
- The three hip-end gablets (W, E_s, E_n) are daub infill between hewn posts on a sill (path_daub_wall, sill=True) instead of board-and-batten.
  They sit under the round hips and are NOT visible from outside in the six views (weakness, see report).
- Preview: 458,601 tris (uncut; was 424,272), seal probes 0 leaks (roof/stack ring, lean_to/wall), clearance gate PASS. Images in `preview_r2/`
  (six clay views + apse_*_colour / apse_*_clay close-ups and east_end). Not graded or audited. kit 8-building baseline NOT re-run (required before grading).
