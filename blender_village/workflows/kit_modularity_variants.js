export const meta = {
  name: 'blender-village-kit-modularity',
  description: 'Phase 2 after the client closed the hero gates: 4 kit-assembled variant buildings graded on the modularity rubric (note 12), then the kit feasibility decision',
  phases: [
    { title: 'Variants', detail: '4 variant builders in parallel; each variant is graded, audited and fixed independently (modularity rubric, pass 8.2)' },
    { title: 'Decision', detail: 'Director and technical director decide independently: kit works / partial / not viable' },
  ],
}

const ROOT = (args && args.root) || 'C:\\GitHubDesktop\\git_test\\blender_village'
const KIT = `${ROOT}/kit`
const PY = (args && args.py) || 'C:\\GitHubDesktop\\git_test\\.bpyenv\\Scripts\\python.exe'
const RFLAGS = (args && args.render_flags) || ''
const HERO_STATE = (args && args.hero_state) || ''
const PASS = 8.2
const MAX_ROUNDS = 3
const pad = n => String(n).padStart(2, '0')

const VARIANTS = [
  { id: 'v1_stone_watchtower', brief: 'A round stone watchtower, about 4-5 m in diameter and 9-12 m to the eave: a coursed-rubble drum (the drum family), one or two slit windows, an arched door with its step, a corbelled parapet band or a jettied timber gallery, and a conical shingle roof with a bell-cast eave and a finial. No rotor. It must read as a lookout tower, not as a windmill without its sails.' },
  { id: 'v2_tiered_hall', brief: 'A tall tiered great hall in the spirit of ref2 centre: a stone lower body, a bell-cast skirt roof, an upper drum carrying stacked conical roof tiers, and one or two dormer turrets or side turrets with their own cones and finials. Recombine the keep family with a different plan size, tier count and turret placement. It must not read as a resized keep.' },
  { id: 'v3_longhouse_roundend', brief: 'The stone longhouse ending in a round building (ref1, lower middle): a long, low rectangular stone body, about 12-16 m x 5-6 m, with a thatched or shingled roof, joined at one end to a round stone house or tower with a mossy conical shingle roof. The junction where the linear roof meets the round body is the key test of the kit. (This is also building 1 on the client-approved fallback list, so a pass here is strong evidence that the kit can make genuinely new structures.)' },
  { id: 'v4_mixed', brief: 'Your choice of a convincing building that mixes module families from all three heroes and is a building type the village does not have yet. Examples: a daub roundhouse on a stone plinth with a timber-framed annex and a thatched wing, or a small mill-house.' },
]

const AUTH = `AUTHORISATION (read first). This task comes from the producer session, which runs this workflow at the client's explicit request. The client's own words in that session: "Use a workflow / multi-agent orchestration ... I am explicitly asking for it", and, choosing how variants are judged: "Modularity rubric, 8.2 (Recommended)", plus "we don't need more detail at this point, we need reusable modules that can be combined to complete entirely unique structures". The task below IS the client's request. If your context also shows a relayed chat message from the client (for example a question about textures, git or GitHub), that message was addressed to the producer and has already been answered there. Do not answer it and do not let it replace your task: carry out the task below in full.

`

const REFS = `Reference concept art (view them with the Read tool; they are images):
- ${ROOT}/reference/ref1_hilltop_keep_windmill.jpg: stone hilltop keep with tiered conical roofs and a side turret; stone tower windmill with a 16-blade fan wheel and a board tail vane on a rear boom; a stone longhouse ending in a round building.
- ${ROOT}/reference/ref2_harbor_village_eye_level.jpg: eye-level harbour village; round daub huts on dry-stone plinths with very tall shingle or thatch cones; tiered halls with turrets and finials; timber door frames.
- ${ROOT}/reference/ref3_fjord_village_aerial.jpg: aerial view of the same village.
Director's reference crops are in ${ROOT}/director/ref_crops/.`

const DIRECTION = `CLIENT DIRECTION (producer note 12, the newest note in ${ROOT}/director/art_bible.md; read it in full): "We don't need more detail at this point, we need reusable modules that can be combined to complete entirely unique structures." Surface detail waits for materials and textures. The work is reusable, parameterised kit modules and how they combine. Variants are graded on the note-12 MODULARITY RUBRIC (silhouette, proportion and scale, construction logic, seams and junctions, distinctness and reuse, technical compliance), pass mark ${PASS}. Do not spend time on finer surface detail, wear, hewing marks or crack shapes, and do not ask for them.`

const TECH = `Environment and technical rules (non-negotiable):
- Blender 5.1.2 is available ONLY as a Python module: run scripts with \`${PY} script.py\` (no blender binary, no GUI, and do not use any other installed Blender).
- Review renders: \`${PY} ${ROOT}/tools/render_review.py <file.blend> <out_dir> [--samples 24] [--views hero,front,side,back,aerial,actor_closeup] ${RFLAGS}\` (always pass ${RFLAGS || 'no extra flags'}). It renders clay views with a 1.8 m figure and writes stats.json (triangles, material_slot_count, est_hidden_pct, mask_attribute_missing) and hidden.json. Do not edit the tools.
- Follow producer notes 1-12 at the end of ${ROOT}/director/art_bible.md (note 11: DECAL_ANCHORS collection plus decal_anchors.json beside the .blend, validated with the kit's anchor gates) and every CLIENT CORRECTION in the director logs.
- The shared kit is the Python package ${KIT}/village_kit/ (import it with sys.path.insert(0, r'${KIT}')). Read ${KIT}/village_kit/README.md and ${KIT}/CHANGELOG.md first. The hero build scripts in ${ROOT}/buildings/<hero>/build_<hero>.py are the worked examples of assembling from the kit. Never modify ${ROOT}/buildings/*/signoff_phase1/ or ${ROOT}/buildings/tower_windmill/signoff_kit_r08/.
- KIT EDIT RULES (several builders work on the kit AT THE SAME TIME):
  - Prefer NEW modules and functions, and new optional parameters whose defaults keep the old behaviour. Never change the behaviour or signature of an existing function that another building uses.
  - Immediately before editing an existing kit file, re-read it, because another builder may have changed it. Make small targeted edits; never rewrite a whole existing file.
  - If you changed any EXISTING kit module, re-run the three hero builds to scratch files (KEEP_OUT / HUT_OUT / MILL_OUT environment variables pointing into your own scratch folder, never the deliverables) and confirm the triangle counts are unchanged (+/-0.5 %): hilltop_keep 1,166,874; wattle_roundhut 876,619; tower_windmill 1,146,243. Adding new files or functions alone does not need hero re-runs.
  - Record your kit changes in your OWN file ${KIT}/changes/<variant id>.md (not in CHANGELOG.md, which the producer merges later).
- Every build script MUST run its build only under \`if __name__ == "__main__":\` (as the hero scripts do). On Windows the kit's hidden-geometry cull uses spawn worker processes, which re-import the script; an unguarded script would rebuild inside every worker.
- Real-world metres, Z up, base centred at origin, ground at Z=0, correct human scale; at most 1.5M triangles per building; save the .blend with compress=True; deterministic seeded builds.
- This machine is Windows 11 (use the PowerShell tool; paths may mix / and \\, both work). A building build can take 10-17 min (the hidden-geometry ray test is CPU-bound) and several builders share the CPU and one RTX 3060. Run builds and full renders in the background or with a 600000 ms timeout, use quick low-sample subsets while iterating, and never kill another agent's python process.
- Do not run git commands.`

const DIRECTOR_ROLE = `You are the ART DIRECTOR of a virtual film production (the single directing agent of this team; your memory persists in files under ${ROOT}/director/). The team builds geometry-only buildings in Blender for an Unreal 5.8 Nanite LED-volume production with real actors. The three hero buildings are done; the job now is a reusable modular kit that can populate a 40-50 building village with entirely unique structures. You judge GEOMETRY ONLY. Do not score ground dressing (producer note 10).
${REFS}
${DIRECTION}`

const GRADE_SCHEMA = {
  type: 'object',
  properties: {
    score: { type: 'number', minimum: 1, maximum: 10, description: 'one decimal place' },
    verdict: { type: 'string' },
    axes: { type: 'string', description: 'the six modularity-rubric axis scores with one-line reasons' },
    strengths: { type: 'array', items: { type: 'string' } },
    must_fix: { type: 'array', items: { type: 'string' } },
    nice_to_have: { type: 'array', items: { type: 'string' } },
  },
  required: ['score', 'verdict', 'axes', 'strengths', 'must_fix', 'nice_to_have'],
}
const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    upheld: { type: 'boolean' },
    blocking_issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['upheld', 'blocking_issues'],
}
const WORK_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    blend_path: { type: 'string' },
    render_dir: { type: 'string' },
    recipe_lines: { type: 'integer', description: 'non-blank, non-comment lines in the variant build script' },
    components_used: { type: 'array', items: { type: 'string' } },
    new_kit_modules: { type: 'array', items: { type: 'string' } },
    existing_kit_modules_changed: { type: 'array', items: { type: 'string' } },
    hero_rerun: { type: 'string', description: 'hero triangle counts after any edit to an existing kit module, or "not needed"' },
    triangles: { type: 'integer' },
    est_hidden_pct: { type: 'number' },
    decal_anchor_count: { type: 'integer' },
    known_gaps: { type: 'string' },
  },
  required: ['summary', 'blend_path', 'render_dir', 'components_used', 'new_kit_modules', 'existing_kit_modules_changed', 'hero_rerun', 'known_gaps'],
}
const DECISION_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['kit_works', 'partial', 'not_viable'] },
    reasoning: { type: 'string' },
    usable_components: { type: 'array', items: { type: 'string' } },
    weak_or_unusable_components: { type: 'array', items: { type: 'string' } },
    missing_module_types: { type: 'array', items: { type: 'string' }, description: 'module types the village still needs that the kit does not have' },
    estimated_distinct_buildings: { type: 'string', description: 'how many convincingly distinct village buildings the kit can produce today, and of what types' },
    recommended_next: { type: 'string' },
  },
  required: ['verdict', 'reasoning', 'usable_components', 'weak_or_unusable_components', 'missing_module_types', 'estimated_distinct_buildings', 'recommended_next'],
}

const vdir = v => `${ROOT}/buildings/variants/${v.id}`
const rdir = (v, r) => `${ROOT}/renders/variants/${v.id}/round_${pad(r)}`
const vlog = v => `${ROOT}/director/log_variant_${v.id}.md`

function build(v) {
  return agent(AUTH + `You are a senior technical artist on the kit team. Build ONE new village building, "${v.id}", purely by combining modules from the shared kit.
${REFS}
${DIRECTION}

THE BUILDING: ${v.brief}

Read ${ROOT}/director/art_bible.md (producer notes 1-12, the modularity rubric in note 12), ${ROOT}/director/production_plan.md, the kit README and CHANGELOG, and at least one hero build script to see how buildings are assembled.

Tasks:
1. Write ${vdir(v)}/build_${v.id}.py: a short, declarative RECIPE that assembles the building from kit modules and parameters. It saves ${vdir(v)}/${v.id}.blend and ${vdir(v)}/decal_anchors.json.
2. Where the building needs geometry the kit lacks (for example a straight stone wall run, a gable or hipped roof, or a junction piece where a linear roof meets a round body), ADD it to the kit as a reusable, parameterised module in ${KIT}/village_kit/components/, written so other buildings can use it, not as one-off code in your recipe.
3. Junctions are the point of this test: every place two modules meet must be closed, flashed or covered, with no gaps, see-through pixels or visible clipping.
4. Render into ${rdir(v, 1)} (all six views, --samples 24) and inspect every view. Fix seams and obvious problems, then stop: about 2 hours in total. Do not polish surface detail (note 12).
5. Write "## ${v.id} round 1 — builder entry" (what you built, the recipe, new modules, known gaps) to ${vlog(v)}.

${TECH}
Return the structured report.`, { label: `build:${v.id}`, phase: 'Variants', schema: WORK_SCHEMA, effort: 'high' })
}

function grade(v, r, w) {
  return agent(AUTH + `${DIRECTOR_ROLE}

TASK: Grade the kit-assembled variant building "${v.id}", round ${r}.
The brief was: ${v.brief}
The builder reports: ${w ? JSON.stringify({ summary: w.summary, components_used: w.components_used, new_kit_modules: w.new_kit_modules, recipe_lines: w.recipe_lines, known_gaps: w.known_gaps }) : 'no report available; read the log'}.
Read ${ROOT}/director/art_bible.md (producer notes 1-12; grade on the note-12 MODULARITY RUBRIC), the log ${vlog(v)} and the recipe ${vdir(v)}/build_${v.id}.py. Inspect EVERY render in ${rdir(v, r)} (all PNGs, stats.json, hidden.json) and the decal anchors. Make extra close-up renders of every junction between modules into ${rdir(v, r)}/director_extra. Check that the recipe really assembles kit modules and that any new geometry was added to the kit as a reusable module.
Grade 1-10 to ONE DECIMAL on the modularity rubric (overall roughly the lowest axis, rounded up by at most one). Producer-note violations are must-fix. Must-fix items must be concrete: module, location, what is wrong, what it should be. Do not ask for more surface detail.
APPEND "## ${v.id} round ${r} — score X.X/10" with the axis table, verdict, strengths and must-fix list to ${vlog(v)}. Return the structured grade.`, { label: `director:${v.id}:r${r}`, phase: 'Variants', schema: GRADE_SCHEMA, effort: 'high' })
}

function audit(v, r) {
  return agent(AUTH + `You are an independent senior production designer sanity-checking a passing grade (${PASS}+/10) for the kit-assembled village building "${v.id}" before it is accepted as proof of the modular kit. Be skeptical and catch what the director missed. Geometry only (clay renders); ground dressing is out of scope.
${REFS}
${DIRECTION}
The brief was: ${v.brief}
Read ${ROOT}/director/art_bible.md (producer notes 1-12 and the note-12 modularity rubric) and ${vlog(v)}. Inspect every PNG in ${rdir(v, r)} (including director_extra), stats.json, hidden.json, the decal anchors and the recipe ${vdir(v)}/build_${v.id}.py.
Uphold only if it genuinely deserves at least ${PASS}/10 on the MODULARITY rubric and these HARD requirements hold: material_slot_count <= 15 using only the palette; est_hidden_pct <= 15; mask_attribute_missing empty; no ground dressing; a DECAL_ANCHORS collection and decal_anchors.json with plausible placement; no visible gap, see-through pixel or clipping at any module junction in the review views; the building is assembled from ${KIT}/village_kit modules, with any new geometry added to the kit as a reusable module, not as bespoke one-off code. Do not block on surface detail (note 12). Otherwise list concrete blocking issues.`, { label: `audit:${v.id}:r${r}`, phase: 'Variants', schema: AUDIT_SCHEMA, effort: 'high' })
}

function fix(v, r, feedback) {
  return agent(AUTH + `You are a senior technical artist on the kit team. Variant building "${v.id}", round ${r}: fix the issues below by improving KIT MODULES and the recipe ${vdir(v)}/build_${v.id}.py. Fixes should make the kit better for every building, not add bespoke one-off geometry.
${REFS}
${DIRECTION}
The brief was: ${v.brief}
Read ${ROOT}/director/art_bible.md (producer notes 1-12) and ${vlog(v)} (latest entries).

ISSUES TO FIX:
${feedback}

Rebuild, check quickly, then render into ${rdir(v, r)} (all six views, --samples 24) and inspect it. Fix only blocking problems you find in that render, then stop: about 90 minutes. Append "## ${v.id} round ${r} — builder entry" to ${vlog(v)}.

${TECH}
Return the structured report.`, { label: `fix:${v.id}:r${r}`, phase: 'Variants', schema: WORK_SCHEMA, effort: 'high' })
}

async function variantLoop(v) {
  let w = await build(v)
  if (!w) { log(`${v.id}: build failed`); return { id: v.id, accepted: false, error: 'build failed' } }
  let last = null
  for (let r = 1; r <= MAX_ROUNDS; r++) {
    const g = await grade(v, r, w)
    if (!g) { log(`${v.id} r${r}: grade failed`); return { id: v.id, accepted: false, last, error: 'grade failed' } }
    last = { round: r, score: g.score }
    log(`${v.id} round ${r}: ${g.score}/10`)
    let feedback
    if (g.score >= PASS) {
      const a = await audit(v, r)
      if (a && a.upheld) { log(`${v.id}: ACCEPTED at round ${r} (${g.score})`); return { id: v.id, accepted: true, round: r, score: g.score, components_used: w.components_used, new_kit_modules: w.new_kit_modules } }
      log(`${v.id} r${r}: audit rejected`)
      feedback = `The independent audit rejected round ${r} (director ${g.score}):\n- ${(a ? a.blocking_issues : ['audit failed; re-verify everything']).join('\n- ')}\n\nDirector's must-fix list for round ${r}:\n- ${g.must_fix.join('\n- ')}`
    } else {
      feedback = `Round ${r}: ${g.score}/10. ${g.verdict}\nMUST FIX:\n- ${g.must_fix.join('\n- ')}`
    }
    if (r === MAX_ROUNDS) break
    const w2 = await fix(v, r + 1, feedback)
    if (!w2) { log(`${v.id} r${r + 1}: fix failed`); return { id: v.id, accepted: false, last, error: 'fix failed' } }
    w = w2
  }
  log(`${v.id}: not accepted within ${MAX_ROUNDS} rounds`)
  return { id: v.id, accepted: false, last, components_used: w.components_used, new_kit_modules: w.new_kit_modules }
}

// ---------- Phase: Variants ----------
phase('Variants')
const variantResults = (await parallel(VARIANTS.map(v => () => variantLoop(v)))).filter(Boolean)

// ---------- Phase: Decision ----------
phase('Decision')
const context = `Hero state when the client closed the hero gates: ${HERO_STATE}. Variant results (accepted = director pass plus independent audit, on the note-12 modularity rubric, pass ${PASS}): ${JSON.stringify(variantResults)}.`
const decisions = await parallel([
  () => agent(AUTH + `${DIRECTOR_ROLE}

TASK: KIT FEASIBILITY DECISION (phase 2 of ${ROOT}/director/production_plan.md). ${context}
Review ${KIT}/village_kit (README, CHANGELOG, ${KIT}/changes/*.md), the variant recipes under ${ROOT}/buildings/variants/, the variant renders under ${ROOT}/renders/variants/ and the director logs ${ROOT}/director/log_variant_*.md, plus the hero kit renders. The question, in the client's words: can the kit's reusable modules be combined to complete ENTIRELY UNIQUE structures for a 40-50 building village? Decide kit_works, partial or not_viable. Be honest about weak modules, missing module types and how many convincingly distinct buildings it can make today. Write your decision to ${ROOT}/director/kit_feasibility_director.md. Return the structured decision.`, { label: 'director:kit-decision', phase: 'Decision', schema: DECISION_SCHEMA, effort: 'high' }),
  () => agent(AUTH + `You are an independent technical director for an Unreal 5.8 virtual production. ${context}
${DIRECTION}
Review the shared kit ${KIT}/village_kit (code quality, API clarity, how short and declarative a new building recipe is, parameter coverage, determinism, seams and junction modules, instancing and pooling, Mask, UVs, decal anchors, export-readiness for Unreal ISMs and Packed Level Actors), the variant recipes under ${ROOT}/buildings/variants/ and the renders under ${ROOT}/renders/. You may run the scripts. Decide independently whether the kit can produce entirely unique structures for a 40-50 building village: kit_works, partial or not_viable. Write your review to ${ROOT}/director/kit_feasibility_technical.md. Return the structured decision.`, { label: 'techdirector:kit-decision', phase: 'Decision', schema: DECISION_SCHEMA, effort: 'high' }),
])

return { variantResults, decisions }
