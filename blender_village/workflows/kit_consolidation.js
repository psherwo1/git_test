export const meta = {
  name: 'blender-village-kit-consolidation',
  description: 'Phase 3 step 1: baseline fingerprints, kit consolidation, guard-rails + README, UV fix, then independent verification and a textured lookdev re-render',
  phases: [
    { title: 'Baseline', detail: 'rebuild all 7 buildings from the current kit and fingerprint them' },
    { title: 'Consolidate', detail: 'sequential kit work: merge duplicates, guard-rails + README, UV fix' },
    { title: 'Verify', detail: 'independent rebuild and review, plus textured lookdev re-render' },
  ],
}

const ROOT = (args && args.root) || 'C:\\GitHubDesktop\\git_test\\blender_village'
const KIT = `${ROOT}/kit`
const PY = (args && args.py) || 'C:\\GitHubDesktop\\git_test\\.bpyenv\\Scripts\\python.exe'
const RFLAGS = (args && args.render_flags) || ''
const BASE = `${KIT}/baseline`

const BUILDINGS = `The seven kit buildings and their last recorded triangle counts:
- heroes: ${ROOT}/buildings/hilltop_keep/build_hilltop_keep.py (1,166,874), ${ROOT}/buildings/wattle_roundhut/build_wattle_roundhut.py (876,619), ${ROOT}/buildings/tower_windmill/build_tower_windmill.py (1,146,243). Output overrides: KEEP_OUT / HUT_OUT / MILL_OUT environment variables.
- variants: ${ROOT}/buildings/variants/<id>/build_<id>.py for v1_stone_watchtower (1,057,164), v2_tiered_hall (954,925), v3_longhouse_roundend (478,877), v4_mixed (938,453). Read each script to find its output override; if one has none, add an optional environment-variable override without changing anything else.
Always build to scratch paths under ${BASE}/<step>/ — never overwrite the delivered .blend or decal_anchors.json files, and never touch ${ROOT}/buildings/*/signoff_phase1/ or ${ROOT}/buildings/tower_windmill/signoff_kit_r08/.
Fingerprint each build with \`${PY} ${ROOT}/tools/geom_hash.py <file.blend> <out.json>\`. It prints triangles plus separate geometry, uv and mask hashes.`

const AUTH = `AUTHORISATION (read first). This task comes from the producer session, which runs this workflow at the client's explicit request. The client's own words: "Yes proceed", approving this plan: "kit consolidation, guard-rails on by default, README, and the queued UV fix first; then close v1-v3; then the timber family via the harbour house; then add-ons and export". The task below IS the client's request. If your context also shows a relayed chat message from the client, that message was addressed to the producer and has already been handled there. Do not answer it and do not let it replace your task.

`

const CONTEXT = `Project: a medieval fjord village for the client's hobby film in Unreal 5.8 with Nanite (no LED volume; offline renders; reference machine Ryzen 5 5600X, 16 GB RAM, RTX 3060 12 GB). Read ${ROOT}/director/art_bible.md producer notes 1-15 (note 14: the kit is an authoring toolbox for 12-15 curated designs; note 15: new structures at most 1,000,000 triangles), ${ROOT}/director/production_plan.md (the KIT DECISION section) and both kit reviews: ${ROOT}/director/kit_feasibility_director.md and ${ROOT}/director/kit_feasibility_technical.md. The kit is ${KIT}/village_kit (README.md, ${KIT}/CHANGELOG.md, ${KIT}/changes/*.md).`

const TECH = `Environment and rules:
- Blender 5.1.2 only as a Python module: \`${PY} script.py\`. Review renders: \`${PY} ${ROOT}/tools/render_review.py <file.blend> <out_dir> [--samples 24] [--views ...] ${RFLAGS}\`. Do not edit the tools (you may ADD new tools).
- Windows 11, PowerShell. A building build takes about 4-10 min. The machine has 16 GB of RAM: run at most 3 builds at once, in the background or with a 600000 ms timeout. Never kill a python process you did not start.
- Build scripts keep their build under \`if __name__ == "__main__":\` (spawn workers re-import them).
- Record every kit change in ${KIT}/CHANGELOG.md under a new version heading.
- Do not run git commands.`

const WORK = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    fingerprints: { type: 'string', description: 'per building: triangles and geometry / uv / mask hashes, and whether each matches the baseline' },
    kit_changes: { type: 'string' },
    known_gaps: { type: 'string' },
  },
  required: ['summary', 'fingerprints', 'kit_changes', 'known_gaps'],
}
const VERIFY = {
  type: 'object',
  properties: {
    all_geometry_identical: { type: 'boolean' },
    fingerprints: { type: 'string' },
    consolidation_review: { type: 'string', description: 'what is now single-sourced, what duplicates remain, API clarity, guard-rail defaults, README quality' },
    uv_fix_results: { type: 'string', description: 'grain-along-axis %, collapsed-UV %, walked-step Mask B, per building' },
    blocking_issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['all_geometry_identical', 'fingerprints', 'consolidation_review', 'uv_fix_results', 'blocking_issues'],
}

const step = (label, phase, prompt) => agent(AUTH + prompt, { label, phase, schema: WORK, effort: 'high' })

// ---------- Baseline ----------
phase('Baseline')
const base = await step('baseline', 'Baseline', `You are the kit's build engineer. ${CONTEXT}
TASK: establish the baseline before any refactor. Rebuild all seven buildings from the CURRENT kit into ${BASE}/0_baseline/ and fingerprint each one into ${BASE}/0_baseline/<id>.json. Compare each triangle count with the recorded number below. Report any drift; do not fix it, just record it.
${BUILDINGS}
Write ${BASE}/BASELINE.md: a table of building, triangles, geometry hash, uv hash, mask hash and build time. Change no kit code.
${TECH}
Return the structured report.`)

// ---------- Consolidate (sequential: one kit editor at a time) ----------
phase('Consolidate')
const c1 = await step('consolidate', 'Consolidate', `You are the KIT ARCHITECT. ${CONTEXT}
Baseline fingerprints: ${BASE}/BASELINE.md and ${BASE}/0_baseline/*.json (${base ? 'the baseline step reported: ' + base.summary.slice(0, 600) : 'read the files'}).
TASK: consolidate the kit WITHOUT changing any building's geometry. Both kit reviews list the duplicates. Implement these:
1. **One public API per concern.** Keep the old names as thin aliases or wrappers, so every recipe still builds unchanged:
   - one eave closure;
   - one polygonal bell-cast roof (pyramid_roof's PyramidSurface behind bell_tier / OctRoof, with any number of sides where it can be done identically);
   - one stone-body module (stone_body vs rubble_walls);
   - one opening-spec API (stone_body.opening, wall_openings, windows.window_spec, plank_doors.door_spec);
   - rename the clashing end_apron functions so each name means one thing.
2. **A plain generic Building frame** (rectangular / free-form) that new recipes can use instead of borrowing RoundFrame, plus ONE hidden-cull entry point and ONE decal entry point that dispatch to the family implementations.
3. **Remove the keep family's module-global FR proxy** (oct_frame.FR) if it can be done hash-identically. If not, document why and leave it.
4. **Stale module header signatures:** fix them.
RULE: after each change, rebuild the affected buildings into ${BASE}/1_consolidate/ and fingerprint them. The geometry, uv and mask hashes must match the baseline EXACTLY for all seven. If a merge cannot be made identical, keep both implementations, document why in the CHANGELOG, and move on. Time-box: about 3 hours.
${BUILDINGS}
${TECH}
Return the structured report.`)

const c2 = await step('guardrails-readme', 'Consolidate', `You are the KIT ARCHITECT, second pass. ${CONTEXT}
The consolidation step reported: ${c1 ? c1.summary.slice(0, 1200) : 'unknown; read the CHANGELOG'}.
TASK A — guard-rails ON by default (the technical review's list):
- a generic clearance gate: a door head against its eave lip, with the eave lip at least 2.30 m over every entrance, failing the build with a named error;
- decal_validate=True: invalid anchors are dropped, not just reported;
- seal_probe at every roof-through-body junction;
- the steep-cone door flags set automatically;
- lod.tmpl_lod unregistered per wing.
For each of the seven buildings: if a guard now fails or changes it, prefer fixing the building when that is a real improvement, and record it. Otherwise opt that building out explicitly, in its recipe, with a reason. Rebuild all seven into ${BASE}/2_guardrails/ and fingerprint them. Geometry should stay identical unless a guard caught a real defect; anchor sets may change, so list every change.
TASK B — rewrite ${KIT}/village_kit/README.md for the current kit:
- the families and the shared core;
- the single APIs and their aliases;
- the guard-rails;
- note 15's LOD and density controls;
- a short "new building recipe" guide with a worked 30-line example (a rubble barn under a shingle gable is fine);
- the edit rules.
Time-box: about 2 hours.
${BUILDINGS}
${TECH}
Return the structured report.`)

const c3 = await step('uv-fix', 'Consolidate', `You are the kit's UV and Mask engineer. ${CONTEXT}
TASK: carry out the client-approved queued UV fix exactly as written in ${ROOT}/director/queued_uv_fix.md:
- wood grain along each piece's long axis (target 90 % or more; shingles and shakes up-slope);
- no collapsed UVs (under 1 % of any object's area with a UV/3D area ratio below 0.2);
- Mask B at 0.05 or less on walked step and threshold tops in every door's walking zone.
Do it in the shared writers so every building gets it. Measure before and after with ${ROOT}/lookdev/scripts/analyze_uv_grain.py and check_uv_stretch.py (copy and adapt them into ${ROOT}/tools/ if they need arguments; do not move or rename the originals).
The previous steps reported: consolidation: ${c1 ? c1.summary.slice(0, 500) : '?'}; guard-rails: ${c2 ? c2.summary.slice(0, 500) : '?'}.
RULE: rebuild all seven into ${BASE}/3_uvfix/ and fingerprint them. The GEOMETRY hash must equal the step-2 fingerprints (${BASE}/2_guardrails/) for every building; only the uv and mask hashes may change. Report the before/after measurements per building. Time-box: about 2.5 hours.
${BUILDINGS}
${TECH}
Return the structured report.`)

// ---------- Verify + lookdev (parallel; neither edits the kit) ----------
phase('Verify')
const verify = await agent(AUTH + `You are an independent technical director verifying a kit consolidation. Be skeptical. ${CONTEXT}
The three steps reported:
- consolidation: ${c1 ? c1.summary.slice(0, 800) : '?'}
- guard-rails and README: ${c2 ? c2.summary.slice(0, 800) : '?'}
- UV fix: ${c3 ? c3.summary.slice(0, 800) : '?'}
TASK:
1. Rebuild all seven buildings yourself from the current kit into ${BASE}/4_verify/ and fingerprint them. Compare geometry hashes with ${BASE}/0_baseline/; any difference must be explained by a recorded guard-rail fix.
2. Re-measure the UV fix (grain along the axis, collapsed UVs, walked-step Mask B).
3. Review the consolidation: what is now single-sourced, which duplicates remain, API clarity, whether the guard-rails are on by default, and whether the README lets a new builder write a recipe. Try it: write a NEW small recipe (for example a rubble store with a lean-to-free gable) from the README alone. It must build under 1 M triangles with the guard-rails on.
Change no kit code. List concrete blocking issues, or none.
${BUILDINGS}
${TECH}
Return the structured verdict.`, { label: 'verify', phase: 'Verify', schema: VERIFY, effort: 'high' })

const look = await agent(AUTH + `You are a lookdev artist. ${CONTEXT}
TASK: re-run the textured look test on the UV-fixed kit, so the client can compare it with the first test in ${ROOT}/lookdev/renders/.
- Use ${ROOT}/lookdev/scripts/apply_lookdev.py (the textures are already extracted in ${ROOT}/lookdev/textures/; the zips in ${ROOT}/materials/ are downloaded data: use images only, never open a bundled .blend, and run scripts with -I).
- Buildings: use the verifier's fresh builds of the current kit in ${BASE}/4_verify/ (copy them into ${ROOT}/lookdev/r2_src/ first; never modify the originals). Texture the keep, the windmill, the hut, v3_longhouse_roundend and v4_mixed.
- Render into ${ROOT}/lookdev/renders_r2/<building>/ (same shots as the first test).
- Apply these material tweaks from the producer's review of the first test:
  - dressed stone 20-30 % less bright (the lichen blew out);
  - thatch more olive and mossy (ref2), less golden;
  - plaster tile scale halved, with a lower normal strength (the trowel swirls read as fish scales);
  - wattle uses a willow bark texture instead of a flat colour;
  - windmill fan blades less pale.
- Look at every render, fix obvious problems, then write ${ROOT}/lookdev/renders_r2/NOTES.md: before/after on wood grain, smearing and moss on steps, and the tweaks.
Time-box: about 2 hours.
${TECH}
Return the structured report.`, { label: 'lookdev-r2', phase: 'Verify', schema: WORK, effort: 'high' })

return { base, c1, c2, c3, verify, look }
