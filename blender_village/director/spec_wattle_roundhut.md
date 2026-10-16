# SPEC: wattle_roundhut (prefix `HUT`, collection `HUT`)

**Files:**
- Build script: `buildings/wattle_roundhut/build_wattle_roundhut.py`
- Output: `buildings/wattle_roundhut/wattle_roundhut.blend`
- Renders: `renders/wattle_roundhut/round_NN/`
- Log: `director/log_wattle_roundhut.md`

**References:**
- Main: ref2 (the big foreground round hut, left of centre).
- Crops:
  - `director/ref_crops/hut_overall.png`
  - `hut_door.png`
  - `hut_wattle_daub_plinth.png`
  - `hut_cap_finial.png`
- Supporting, for the same roof vocabulary on other buildings: `style_thatch_and_tiered_tower.png` (ref2) and `style_aerial_village.png` (ref3).

Read `director/art_bible.md` first.

## 0. Scale derivation
In ref2 the hut's door opening is about 105 px tall, and a door of about 2.05 m gives about 52 px/m. The woman standing in front (about 95 px) confirms the scale.

Measured: the wall is about 2.4–2.8 m tall to the plate, the wall diameter about 7 m, and the roof eave diameter about 8.2 m. The roof rises about 4.5–5 m above the eave. The smooth apex collar is about 1.45 m in diameter and about 0.7 m tall, and the finial adds about 1.05 m above it. **Total height is ≈ 8.6 m.**

## 1. Orientation
- **Centre:** the hut centre is at the world origin.
- **Door:** the door is centred on **−Y**.
- **Daubed bay:** the large daubed bay sits immediately to the LEFT of the door when viewed from the front, i.e. toward −X, at azimuth about −25° to −45°. That matches ref2, where the plastered panel is beside the door.

## 2. Components

### A. Dry-stone plinth (`HUT_plinth_stones`)
- **Ring:** a ring of large rounded and sub-angular boulders with no mortar.
  - Outer Ø about 7.5 m, inner Ø about 6.4 m.
  - Top at about 0.35–0.42 m (uneven ±4 cm).
- **Stones:** mainly one course of big stones (0.30–0.60 m long, 0.2–0.35 m high) with smaller chinking stones in the gaps, and some stones bedded 5–10 cm below Z=0.
  - Bevelled and lumpy (no boxes).
  - At least 30 unique shapes.
- **At the door:** the plinth stops for the threshold.

### B. Main posts (×14) (`HUT_posts`)
- **Posts:** round-hewn timber Ø 0.20–0.24 m, slightly irregular (8–12 faceted sides + noise, or round with adze flats). They stand on the plinth at about 1.57 m spacing around r = 3.5 m, set in the wall line and about half proud of the wattle on the outside.
- **Height:** the post tops reach the wall plate at 2.85 m. Each post leans ±0.7° and tapers ±1 cm.
- **Door posts:** the two posts that flank the door are heavier (0.24 × 0.22 squared).

### C. Wattle panels (`HUT_wattle_stakes`, `HUT_wattle_rods`)
- **Stakes:** between the posts, vertical stakes (sails) Ø 4–6 cm at 0.26–0.32 m spacing, running from the plinth top to just under the plate.
- **Rods:** horizontal rods/withies Ø 1.6–3.5 cm, rows about every 3.5–4 cm, woven alternately in front of and behind the stakes, with each row offset by one stake. The weave depth (in–out amplitude) is about ±2.5 cm.
- **Variation:** rods vary in diameter, some run in pairs, some ends poke out at the posts (2–6 cm stubs), and rows drift ±2 cm.
- **Mesh construction:** use real tube geometry with 6–8 sides, following the wall curvature. Low-poly back sides are fine where covered by daub.
- **Wall height:** the wattle runs 0.38 → 2.85 m (about 2.45 m).

### D. Daub (`HUT_daub`)
- **Coverage:** about 25–30% of the wall area.
  - The **large bay left of the door** (as ref2) is daubed from about 0.55 m to the plate. Its lower edge is broken and eroded and shows the wattle beneath (irregular, chunky, 3–6 cm thick, with lumps and pitting at mesh level).
  - **One bay at the back right** is fully daubed.
  - **One partial patch** at the side.
- **Surface:** lumpy and hand-applied, with soft bulges of 1–2 cm. It meets the posts with a slight fillet or gap, and the edges crumble (no clean cut lines).

### E. Wall plate (`HUT_wall_plate`)
- A ring of 7 curved timber segments, 0.18 × 0.20 m, on top of the posts at 2.85–3.05 m.
- Scarf or lap joints over the posts with protruding pegs.
- Chamfered edges.

### F. Door assembly, the actor close-up hero (`HUT_door_frame`, `HUT_door_leaf`, `HUT_door_ironwork`, `HUT_threshold`)
Read `hut_door.png`. The door sits in a **projecting flat-fronted frame** that stands about 0.25 m proud of the curved wall.
- **Frame:**
  - Two heavy inner jambs 0.22 × 0.20 m and a lintel 0.22 m tall × 1.7 m long whose ends sit on two outer posts.
  - Narrow wattle side panels (about 0.25 m) between the jambs and the outer posts, as in ref2.
- **Clear opening:** 1.00 m wide × **2.08 m** from the threshold (threshold top at 0.20 m, so the head underside is at 2.28 m).
- **Threshold:** a worn timber sill on a large flat stone. Outside, one big flat step stone with its top at 0.08–0.10 m.
- **Stepping stones:** 6–10 flat paving/stepping stones (0.4–0.9 m, 8–12 cm thick, rounded edges) leading out about 3 m toward −Y, half-buried, as in ref2's paving.
- **Door leaf:** a plank leaf of 6 boards, 35 mm thick, with 2 ledges and a brace on the inside. It is hung on the inner face and **open inward about 75°** so the doorway reads deep and actors can pass.
  - Iron strap hinges with nail heads, pintles in the jamb, and a wooden latch bar with a keeper.
- **Interior:**
  - Earthen floor at 0.20 m and the inner face of the wall (a simple daubed inner skin is fine).
  - The underside of the roof (rafters and battens) visible inside.
  - A central post or hearth ring stones are optional bonuses.
  - The interior must give plausible dark depth through the door; no void into the sky.

### G. Roof structure (`HUT_rafters`, `HUT_purlin_rings`, `HUT_battens`)
- **Rafters:** 28 round pole rafters Ø 0.10–0.12 m from the apex to the plate, extending **0.6 m beyond the wall face**. Their ends are visible under the eave, cut slightly unevenly, some with split ends.
- **Rings:** purlin rings (Ø 7 cm poles) about every 0.8 m inside, and batten rings (3 × 5 cm laths) under the shingle courses, visible in the eave gap.
- **Pitch:** **51°**.
- **Eave lip:** the shingle eave lip sits at **2.38–2.45 m** (≥ 2.35 m everywhere and ≥ 2.40 m above the door), at radius about 4.1–4.15 m.

### H. Shingle cone (`HUT_roof_shingles`, `HUT_roof_starter`)
- **Profile:** very slightly convex (the midpoint bulges out 6–8 cm relative to the straight cone), with a gentle eave kick (the last 0.5 m about 4° flatter). Sag between rafters about 1–3 cm.
- **Courses:** **17–19 courses** from eave to collar.
  - Exposure 0.36–0.40 m along the slope.
  - Shingles 0.34–0.55 m wide and about 0.75 m long (double coverage), with a butt 3–3.5 cm thick tapering to 1 cm.
  - Slightly rounded corners, slight cup/curl, and staggered joints.
- **Starter:** a doubled starter course at the eave.
- **Count:** shingle count per course decreases toward the apex so that widths stay in range. Near the apex, use narrower shingles or the collar covers them.
- **Variation:** per art bible §6, including about 3% slipped, missing or split shingles and courses waving ±2 cm.
- **Look:** big chunky readable shingles as in `hut_overall.png`. This is THE look of the hut.

### I. Apex collar and finial (`HUT_cap_collar`, `HUT_finial`)
- **Collar ("lead hat"):** a smooth cone, base Ø **1.45 m** with its drip edge at about 6.55 m.
  - It overhangs the top shingle course by about 8 cm with a rolled drip lip and real thickness.
  - Shallower than the roof (about 44°). Apex at about 7.25 m.
  - Faint vertical seams (8–12 standing seams or board joints) as geometry. Slightly dented and irregular.
- **Upper collar:** a second smaller cone, base Ø 0.75 m, 7.25–7.55 m.
- **Finial:** a turned spindle with 2 rings and a bead (7.55–7.95 m), then a sharp tapering spike to **8.6 m**. Use 24–32 radial segments. It leans about 1°.

### J. Ground contact (`HUT_ground_rubble`)
- 25–50 small stones and pebbles of 0.04–0.3 m around the plinth, half-buried and clustered by the door and drip line.
- Optional bonus: a shallow drip-line trench (ring depression), as a separate mesh ring.

## 3. Budget guidance (target 0.7–1.3 M triangles)
- Wattle: about 350–450k. It is the wall's identity, so keep it real geometry.
- Shingles: about 200–300k.
- Plinth and rubble: about 120k.
- Timber, door and interior: about 120k.
- Collar and finial: about 10k.

## 4. 10/10 acceptance criteria
1. **Silhouette:** the hero and front renders read as ref2's foreground hut at a glance.
   - A squat round wall on a stone plinth under a huge steep shingle cone (roof height about 1.8× wall height).
   - A smooth wide apex collar and a slender spike finial.
   - A flat-fronted projecting door frame.
   - Proportions within ±10%: wall Ø 7.0, eave Ø 8.2–8.3, eave lip about 2.4 m, collar Ø 1.45, total 8.6 m.
2. **Scale:** the 1.8 m figure fits the door with about 0.28 m headroom. The eave lip over the door is ≥ 2.40 m. The step riser is ≤ 18 cm. Shingles read as about 0.45 m wide next to the figure.
3. **Wattle:** a real woven rod-and-stake weave with in/out alternation visible in the actor close-up, plus rod variation. No texture-like flat panels.
4. **Daub:** thick, lumpy, with an eroded lower edge revealing wattle, matching ref2's bay beside the door.
5. **Roof:**
   - Every shingle individually modelled with thickness and overlap.
   - Convex profile and eave kick.
   - Visible rafter ends, battens and plate under the eave.
   - The collar overhangs the shingles cleanly.
6. **Door close-up:** the projecting frame, side wattle panels, open plank leaf with ironwork, worn threshold and step stone, and plausible dark interior depth.
7. **Age pass:** convincing irregularity (wobbly eave line, post lean, shingle variation, slipped shingles, plinth stones varied). No perfect circles and no CG repetition.
8. **Technical:** all of art bible §8 (deterministic, oriented per §1, named objects, material slots `M_wattle`/`M_daub`/`M_roof_shingle`/`M_timber`/`M_stone`/`M_lead`/`M_iron`/`M_rubble`, UVs, ≤ 1.5 M triangles, `.blend` < 80 MB, no artefacts in the 6 views).
9. **Must-fix list empty**, and no objection in the Director's side-by-side with the reference crops.


## CLIENT CORRECTION — the exterior is MOSTLY INTACT DAUB (supersedes the earlier exposed-wattle balance)

The client says there is too much exposed wattle.

- **Daub coverage.** The exterior walls must be **mostly intact daub, about 80–90% of the wall face**.
- **Exposed wattle** appears only in **small sections**: about 3–5 patches around the whole hut, each roughly 0.3–1.0 m², where the daub has fallen away. Each patch has an eroded, ragged, thick daub edge, with rods visible beneath and a few clinging clumps. This is the existing "daub bay" erosion language, inverted.
- **The door side panels** may keep their visible woven rope look if they read as intentional framing. Otherwise daub them too.
- **Daub surface.** Keep a hand-applied, slightly bulging coat with shrinkage cracks, a weathered lower margin and slight sag. Avoid flat board-like daub.
- **Hidden geometry.** Rods behind intact daub become hidden geometry. **Delete them.** Keep wattle only inside the exposed patches, plus about 10 cm under the patch edges. Re-check est_hidden_pct ≤ 15%.
- **Ground dressing.** Per producer note 10, delete all path flags, stepping stones, ground rubble and the ground apron. Keep the stone plinth, the door-post pad stones and the threshold.
