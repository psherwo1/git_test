# Junction test: textured look at the roof-junction defects (2026-10-17)

Quick r2 look test for the client: how visible the known roof-junction defects are once the buildings are textured instead of clay. The buildings are copies of the longhouse at round 6 (`src/v3_longhouse_roundend_r06.blend`) and the tiered hall at round 7 (`src/v2_tiered_hall_r07.blend`).

**Method.**
- **Texturing:** `lookdev/scripts/apply_lookdev.py --look r2`.
- **Shots:** `junction_test/scripts/jt_shots.py`. Textured renders use Cycles OptiX at 1920x1080 with 112 adaptive samples, denoised, under r2 lighting (a low warm sun from the south-east and a dim sky).
- **Cameras:** the director's junction cameras, matched exactly, plus hand-placed ground-level and pan frames.
- **Pan blur:** `*_panblur` frames use camera-rotation motion blur equivalent to a fast pan, about 90 deg/s at 24 fps with a 180 deg shutter.
- **Compare sheets:** `renders/compare/`, clay on the left and textured on the right. Clay twins are in `renders/clay_twins/`.

## Verdicts (textured): (a) ground level, (b) quick pan

### Longhouse (round 6; being redesigned so the eaves no longer cross)

| Defect | (a) Ground level | (b) Quick pan |
|---|---|---|
| South-east eave-crossing stack | **Noticeable** from an eye-level east angle (d03 at 5 m, d46 at 3 m): the plate ends read as loose boards. **Barely noticeable** from the front (8-12 m) | Invisible from the front; at most a busy patch from the east |
| Dark pocket at the south roll nose | Barely noticeable: it reads as one more course shadow | Invisible |
| Floating eave-band pieces (1.8-4.2 cm) | Invisible in normal shots; barely noticeable only in a deliberate look-up | Invisible |

### Tiered hall (round 7; out of rounds, client decision pending)

| Defect | (a) Ground level | (b) Quick pan |
|---|---|---|
| Turret lead apron down the flank: stepped, spiky drip edge | **Noticeable** when the camera sees the sunlit turret flank (about 6 m): the pale, untextured r2 lead contrasts with the stone and shingles, more than in clay. **Invisible** in the official actor close-up (hidden behind the hip) | Barely noticeable: a pale lead band remains |
| Run-end lead blades | Noticeable only at about 1 m; barely noticeable from the ground at 6 m | Invisible |
| Saw-edge of the cheek returns and 2-5 cm slots under the soffit | Invisible in r2 light (deep shade, dark wood); expect barely noticeable under overcast or fill light | Invisible |
| Rubble through the upstands and lantern drip spikes (back gutters, 10.5 m) | Invisible | Invisible |

## Bottom line

- **Texture hides the defects that sit in shadow:** the cheek saw-edge, the roll-nose pocket and the floating pieces.
- **It does not hide outline or lit-lead defects:**
  - the longhouse's east-angle stack, which is moot after the redesign;
  - the hall's pale sawtooth apron on a sunlit turret flank.
- **In a quick pan only the hall's pale apron band survives.**
- **A cheap lookdev mitigation for the hall:** darker or grimier lead with texture or normal variation on the turret aprons. It cuts the contrast but does not fix the geometry.

## Files

**Renders:**
- longhouse: `renders/v3_longhouse_roundend/`: d03, d46, d07, actor_closeup, d23, pan8m_front, pan8m_front_panblur;
- hall: `renders/v2_tiered_hall/`: a08, c13, c17, c22, actor_closeup, o01, up6m_turE_junction, up6m_turE_junction_panblur.

**Compare sheets:** `renders/compare/`.

**Scripts:** `scripts/jt_shots.py` and `scripts/jt_crop.py`.

**Camera sources:**
- longhouse: `renders/variants/v3_longhouse_roundend/round_06/director_extra/dir_render6.py`;
- hall: the director's round-7 camera scripts were in the old session's scratchpad, not in the repo; their cameras are reproduced in `jt_shots.py`.

## Session 2: the client's lead mitigation for the tiered hall (2026-10-17)

The client accepted the hall at round 7 with darker, grimier lead on the turret aprons. `apply_lookdev.py` (r2) now
reads a per-object `lookdev_grime` (set from `OBJECT_GRIME`, full hall object names): value x 0.6, saturation x 0.7,
dark run-off streaks, slightly rougher, and a faint hammered-sheet normal. It is applied to both turret aprons and
their cheeks and, for consistency, to the hall's drum and lantern flashings. Other buildings' lead is unchanged.
Result (`renders/v2_lead_mitigation/`, before / after): the sunlit turret apron reads as dark weathered lead instead
of a pale band; the stepped drip-edge outline is still there (geometry), with much less contrast. UE: a per-mesh
material-instance scalar.