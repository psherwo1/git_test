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
