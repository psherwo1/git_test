# Production plan: village buildings

## Phase 1: hero buildings (in progress)

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

## Phase 3: delivery

- Export kit pieces and/or buildings for Unreal 5.8: FBX or USD, centimetre scale, Nanite-ready.
- Supply instance layouts for Packed Level Actors.
- Write import notes covering texturing with jointless Megascans surfaces, world-aligned projection and the `Mask` attribute.
