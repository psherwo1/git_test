# Production plan: village buildings

## Phase 1: hero buildings (COMPLETE: all three signed off, ensemble approved at 8.4 on 2026-10-16)

**Buildings:**
- hilltop keep
- tower windmill
- wattle roundhut

**Pass rule:** 9/10 from the Art Director, confirmed by an independent sign-off audit.

**Binding client producer notes:**
- Unreal 5.8 / Nanite target
- modular-kit-ready code
- shared or instanced mesh data
- hidden triangles ≤ 15%, with backing surfaces so culling opens no holes
- the shared 15-slot material palette
- the mandatory `Mask` colour attribute

After the three heroes pass, there is an ensemble review for one coherent style.

## Phase 2: kit feasibility decision (after phase 1)

Target: populate a village of 40-50 buildings.

**Assessment.** The director and a technical reviewer assess whether the three hero build scripts break apart into a usable modular kit. A usable kit has:
- parameterised components: walls (stone and wattle, several radii), roofs (conical, bell-cast skirt, tiered, hipped mill cap, thatch), doors and windows, finials and caps, turrets, plinths, timber frames and braces, mill rotor and tail vane;
- assembly into convincing variants at the same 9/10 quality bar;
- correct seams and junctions between parts.

**Proof of concept.** Generate 3-5 variants from the kit. The director grades them against the concept art.

**Decision rule (client-approved):**
- **The kit works:** proceed with the kit, variant generator and Unreal export.
- **The kit does NOT break apart into a usable kit (or only partly):** build **3 new custom hero buildings**. Client permission was given on 2026-10-16. They go through the same director-led loop and the same producer notes, and reuse any kit parts that do work.

**Approved new buildings**, chosen to widen the village's vocabulary and taken from the concept art (client-confirmed on 2026-10-16):
1. the stone longhouse ending in a round building with a mossy conical shingle roof (ref1, lower middle);
2. the tall tiered great hall with stacked conical roofs and dormer turrets (ref2 centre);
3. a timber harbour house or boathouse on the waterfront (ref2 / ref3 right side).

**Client decision (2026-10-16): the decal and detail-scale rule (producer note 11) applies in phase 2.** Every migrated hero and every kit variant must follow it and export decal anchors.

**Signed-off phase-1 heroes are preserved** in `buildings/<id>/signoff_phase1/`. If a migrated hero cannot get back to a signed-off pass, the phase-1 version stays the deliverable.

## Phase 3: delivery

- Export kit pieces and/or buildings for Unreal 5.8: FBX or USD, centimetre scale, Nanite-ready.
- Supply instance layouts for Packed Level Actors.
- Write import notes covering texturing with jointless Megascans surfaces, world-aligned projection and the `Mask` attribute.

## Sign-off record

| Building | Round | Director score | Sign-off audit | Date |
|---|---|---|---|---|
| tower_windmill | 6 | 9.1 | upheld | 2026-10-16 |
| hilltop_keep | 6 | 8.4 | upheld | 2026-10-16 |
| wattle_roundhut | 7 | 8.5 | upheld (round 6 at 8.3 was rejected) | 2026-10-16 |

Sign-off rules in force: pass mark 8.2 (client, "for now"), producer notes 1-10, and all client corrections.

### Phase 2 kit sign-offs (the kit version replaces the phase-1 deliverable)

| Building | Kit round | Director score | Sign-off audit | Date | Snapshot |
|---|---|---|---|---|---|
| tower_windmill | 8 | 9.0 | upheld (round 7 at 8.8 was rejected) | 2026-10-16 | `buildings/tower_windmill/signoff_kit_r08/` (1,146,243 tris, 13.3 % hidden, 106 anchors) |

Rules in force for phase-2 sign-offs: pass mark 8.2, producer notes 1-11, all client corrections.

### Client direction, 2026-10-16: hero gates closed, modularity first (producer note 12)

The client stopped the hero detail rounds: "we don't need more detail at this point, we need reusable modules that can be combined to complete entirely unique structures". Surface detail waits for materials and textures. Kit variants are graded on the modularity rubric in the art bible (note 12), pass mark 8.2.

Hero outcomes when the gates closed:

| Building | Last kit round | Director | Audit | Deliverable |
|---|---|---|---|---|
| tower_windmill | 8 | 9.0 | upheld | **kit r8** (`signoff_kit_r08/`) |
| wattle_roundhut | 11 | 8.9 | not run (gates closed); r9 8.6 and r10 8.8 were rejected | phase 1 stays the signed-off deliverable; the kit r11 build is the kit's reference hut |
| hilltop_keep | 9 | 8.6 | rejected (wing thatch note 11 / macro-form); r7 8.3 and r8 8.5 were also rejected | phase 1 stays the signed-off deliverable; the kit r9 build is the kit's reference keep |

The interrupted keep round-10 fixer's kit edits are saved in `director/partial_fix_hilltop_keep_r10.patch` and were reverted from the kit.

**Texturing readiness (checked 2026-10-16 on the signed-off kit windmill):** every unique mesh has one `UVMap` (box projection at real-world scale, about 1 UV unit per metre, no zero-area UV faces), `Mask` everywhere and the 15-slot palette. Still to do before a texturing pass: check that wood grain (U axis) follows the long axis of planks, shingles and rafters; choose UV0 tiling versus world-aligned in Unreal; build the export (FBX/USD, cm, custom normals, `Mask` as vertex colour); and run one lookdev test in UE 5.8 on the signed-off windmill before any further modelling detail.

Ensemble review 1: 8.4/10, APPROVED. These non-blocking consistency items carry into phase 2:
- **Shared shingle size table.** The keep's turret and lantern caps go up to the chunky 0.35-0.55 m scale.
- **Age passes.** Roughen the windmill's drum masonry and balusters. Add an age pass to the roundhut cone.
- **Shared module.** Merge the stone, shingle and Mask code into one module.
- **Roundhut kit entry point.** Add one to the roundhut.
