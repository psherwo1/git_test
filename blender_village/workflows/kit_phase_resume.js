export const meta = {
  name: 'blender-village-kit-phase-resume',
  description: 'Resume phase 2 from saved state: optional hero kit gates, kit variants, and the kit feasibility decision (portable paths via args)',
  phases: [
    { title: 'Migrate heroes', detail: 'Keep and windmill move onto the kit; every migrated hero is regraded (8.2 + sign-off audit) so nothing regresses' },
    { title: 'Variants', detail: '4 kit-assembled variant buildings, graded by the director, fix rounds' },
    { title: 'Decision', detail: 'Director and technical reviewer decide: kit works / partial / not viable' },
  ],
}

const ROOT = (args && args.root) || '/home/user/git_test/blender_village'
const KIT = `${ROOT}/kit`
const PY = (args && args.py) || '/opt/bpyenv/bin/python'
const RFLAGS = (args && args.render_flags) || ''   // e.g. '--device GPU' on an RTX desktop
const PASS = 8.2
const MAX_HERO_ROUNDS = 4
const MAX_VARIANT_ROUNDS = 3
const pad = n => String(n).padStart(2, '0')

const REFS = `Reference concept art (view them with the Read tool; they are images):
- ${ROOT}/reference/ref1_hilltop_keep_windmill.jpg — stone hilltop keep with tiered conical roofs and side turret; stone tower windmill with a 16-blade fan wheel and a board tail vane on a rear boom; a stone longhouse ending in a round building.
- ${ROOT}/reference/ref2_harbor_village_eye_level.jpg — eye-level harbour village: round daub huts on dry-stone plinths with very tall shingle/thatch cones, tiered halls with turrets and finials, timber door frames.
- ${ROOT}/reference/ref3_fjord_village_aerial.jpg — aerial view of the same village.
Director's reference crops are in ${ROOT}/director/ref_crops/.`

const TECH = `Environment & technical rules (non-negotiable):
- Blender 5.1.2 is available ONLY as a Python module: run scripts with \`${PY} script.py\` (no blender binary, no GUI).
- Review renders: \`${PY} ${ROOT}/tools/render_review.py <file.blend> <out_dir> [--samples 32] [--views hero,front,side,back,aerial,actor_closeup] ${RFLAGS}\` (always pass ${RFLAGS || 'no extra flags'}) (clay views + 1.8 m figure; writes stats.json with triangles, material_slot_count, est_hidden_pct, mask_attribute_missing, and hidden.json). \`${PY} ${ROOT}/tools/hidden_tris.py <file.blend>\` estimates hidden triangles alone. Renders can take minutes: use Bash timeout 600000 or background runs, and low-sample subsets for quick checks. Several agents share the machine. Do not edit the tools.
- Follow EVERY producer note (1-11) at the end of ${ROOT}/director/art_bible.md, including note 11 (detail-scale rule + DECAL_ANCHORS collection + buildings/<id>/decal_anchors.json), and every CLIENT CORRECTION in the director logs/specs.
- The shared kit is the Python package ${KIT}/village_kit/ (import it with sys.path.insert(0, '${KIT}')). Building scripts live in ${ROOT}/buildings/<id>/build_<id>.py and save <id>.blend beside them. The signed-off phase-1 versions are preserved in ${ROOT}/buildings/<id>/signoff_phase1/ — never modify that folder.
- KIT EDIT RULES (several agents use the kit): you may ADD modules, functions and optional parameters with backward-compatible defaults. Do not change the behaviour or signature of an existing kit function another building uses. After any kit edit, re-run every OTHER building script that already imports village_kit and confirm it still builds without errors and with the same triangle count (±0.5%). Record kit changes in ${KIT}/CHANGELOG.md.
- Real-world metres, Z up, base centred at origin, ground Z=0; correct human scale; ≤ 1.5M triangles per building; .blend saved with compress=True; deterministic seeded builds.
- Do not run git commands.`

const DIRECTOR_ROLE = `You are the ART DIRECTOR of a virtual film production (the single directing agent of this team; your memory persists in files under ${ROOT}/director/). The team builds geometry-only buildings in Blender for an Unreal 5.8 Nanite LED-volume production with real actors, and is now turning the three signed-off heroes into a reusable modular kit for a 40-50 building village. You judge GEOMETRY ONLY (silhouette, proportions, construction, detail quality, fidelity to the concept-art style, actor scale, producer-note compliance). Do not score ground dressing (producer note 10). Do not penalise micro-detail that producer note 11 moves to materials/decals.
${REFS}`

const GRADE_SCHEMA = {
  type: 'object',
  properties: {
    score: { type: 'number', minimum: 1, maximum: 10, description: 'one decimal place' },
    verdict: { type: 'string' },
    strengths: { type: 'array', items: { type: 'string' } },
    must_fix: { type: 'array', items: { type: 'string' } },
    nice_to_have: { type: 'array', items: { type: 'string' } },
  },
  required: ['score', 'verdict', 'strengths', 'must_fix', 'nice_to_have'],
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
    files_changed: { type: 'array', items: { type: 'string' } },
    kit_changes: { type: 'string' },
    triangles: { type: 'integer' },
    est_hidden_pct: { type: 'number' },
    decal_anchor_count: { type: 'integer' },
    known_gaps: { type: 'string' },
  },
  required: ['summary', 'files_changed', 'kit_changes', 'known_gaps'],
}
const VARIANTS_SCHEMA = {
  type: 'object',
  properties: {
    variants: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          description: { type: 'string' },
          components_used: { type: 'array', items: { type: 'string' } },
          blend_path: { type: 'string' },
          render_dir: { type: 'string' },
        },
        required: ['id', 'description', 'components_used', 'blend_path', 'render_dir'],
      },
    },
    known_gaps: { type: 'string' },
  },
  required: ['variants', 'known_gaps'],
}
const DECISION_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['kit_works', 'partial', 'not_viable'] },
    reasoning: { type: 'string' },
    usable_components: { type: 'array', items: { type: 'string' } },
    weak_or_unusable_components: { type: 'array', items: { type: 'string' } },
    estimated_distinct_buildings: { type: 'string', description: 'how many convincingly distinct village buildings the kit can produce today, and of what types' },
    recommended_next: { type: 'string' },
  },
  required: ['verdict', 'reasoning', 'usable_components', 'weak_or_unusable_components', 'estimated_distinct_buildings', 'recommended_next'],
}

// ---------- helpers ----------
function grade(subject, renderDir, logPath, specNote, label, phaseName) {
  return agent(`${DIRECTOR_ROLE}

TASK: Grade ${subject}.
Read ${ROOT}/director/art_bible.md (all producer notes, especially 11), ${ROOT}/director/production_plan.md and the log ${logPath}. ${specNote}
Inspect EVERY render in ${renderDir} (all PNGs, stats.json, hidden.json) and the decal anchors (DECAL_ANCHORS collection / decal_anchors.json — check they are plausible and the count is sensible). Compare against the concept art. You may make extra close-up renders into ${renderDir}/director_extra.
Grade 1-10 to ONE DECIMAL, strictly and honestly against the art-bible rubric. Producer-note violations are must-fix. Must-fix items must be concrete (part, location, what is wrong, what it should be, with numbers).
APPEND "## ${label} — score X.X/10" with verdict, strengths and must-fix list to ${logPath}. Return the structured grade.`, { label: `director:${label}`, phase: phaseName, schema: GRADE_SCHEMA, effort: 'high' })
}

function audit(subject, renderDir, extra, label, phaseName) {
  return agent(`You are an independent senior production designer sanity-checking a passing grade (8.2+/10) before ${subject} is signed off for a virtual film production with real actors. Be skeptical; catch what the director missed. Geometry only (clay renders). Ground dressing is out of scope.
${REFS}
Read ${ROOT}/director/art_bible.md (producer notes 1-11). Inspect every PNG in ${renderDir}, stats.json, hidden.json and the decal anchors. ${extra}
Uphold only if it genuinely deserves at least 8.2/10 and these HARD requirements all hold: material_slot_count <= 15 using only the palette; est_hidden_pct <= 15; mask_attribute_missing empty; no ground dressing; producer note 11 met (no modelled micro relief below the thresholds, a DECAL_ANCHORS collection and decal_anchors.json with plausible placement); every applicable CLIENT CORRECTION implemented; the build script assembles the building from ${KIT}/village_kit components rather than private copies of shared generators. Otherwise list concrete blocking issues.`, { label: `audit:${label}`, phase: phaseName, schema: AUDIT_SCHEMA, effort: 'high' })
}

function fixRound(id, round, feedback, phaseName) {
  return agent(`You are a senior 3D environment modeller. Building: ${id}. This is phase-2 round ${round}: fix the issues below without regressing anything that was signed off in phase 1 (compare against ${ROOT}/buildings/${id}/signoff_phase1/ and its renders).
${REFS}
Read ${ROOT}/director/art_bible.md (producer notes 1-11), ${ROOT}/director/spec_${id}.md and ${ROOT}/director/log_${id}.md (latest entries, CLIENT CORRECTIONS).

ISSUES TO FIX:
${feedback}

${TECH}

Update the kit and/or ${ROOT}/buildings/${id}/build_${id}.py, rebuild, check quickly, then do the full review render into ${ROOT}/renders/${id}/round_${pad(round)} (all views, --samples 32) and inspect it. Time-box to ~90 minutes. Append "## Round ${round} — builder entry" to the log. Return the structured report.`, { label: `fix:${id}:r${round}`, phase: phaseName, schema: WORK_SCHEMA, effort: 'high' })
}

// Regression gate for a migrated hero: grade -> (audit) -> fix ... until signed off or cap.
async function heroGate(id, firstRound, phaseName) {
  let round = firstRound
  let last = null
  for (let i = 0; i < MAX_HERO_ROUNDS; i++) {
    const renderDir = `${ROOT}/renders/${id}/round_${pad(round)}`
    const g = await grade(`the KIT-MIGRATED version of hero building "${id}" (phase-2 round ${round})`, renderDir, `${ROOT}/director/log_${id}.md`,
      `Read ${ROOT}/director/spec_${id}.md. It was signed off in phase 1 (see the sign-off record in the production plan; phase-1 renders are in earlier round folders). It must still deserve a pass after moving onto the kit and applying producer note 11 and the ensemble consistency notes in ${ROOT}/director/ensemble_log.md.`,
      `Round ${round}`, phaseName)
    if (!g) { log(`${id} r${round}: grade failed`); break }
    last = { round, score: g.score }
    log(`${id} (kit) round ${round}: ${g.score}/10`)
    let feedback
    if (g.score >= PASS) {
      const a = await audit(`the kit-migrated hero "${id}"`, renderDir, `Also compare with the phase-1 sign-off renders of this building; the kit version must not be visibly worse.`, `${id}:r${round}`, phaseName)
      if (a && a.upheld) { log(`${id}: kit version SIGNED OFF at round ${round} (${g.score})`); return { id, signed_off: true, round, score: g.score } }
      feedback = `Sign-off audit rejected round ${round} (director ${g.score}):\n- ${(a ? a.blocking_issues : ['audit failed; re-verify everything']).join('\n- ')}`
    } else {
      feedback = `Round ${round}: ${g.score}/10. ${g.verdict}\nMUST FIX:\n- ${g.must_fix.join('\n- ')}`
    }
    if (i === MAX_HERO_ROUNDS - 1) break
    round++
    const w = await fixRound(id, round, feedback, phaseName)
    if (!w) { log(`${id} r${round}: fix agent failed`); break }
  }
  log(`${id}: kit version NOT signed off within ${MAX_HERO_ROUNDS} gate rounds — the phase-1 signed-off version remains the deliverable`)
  return { id, signed_off: false, last }
}

// ---------- Phase: Migrate heroes (resume) ----------
// args.hero_results: results already obtained in the cloud session (kept as-is).
// args.heroes_to_gate: [{id, round}] heroes whose kit gate still needs to run, starting by GRADING that round.
// args.heroes_to_migrate: [{id, round, components, ensemble, corrections, resume_note}] heroes whose kit migration
// was interrupted; the migrator continues from the files on disk, then the hero goes through its gate.
phase('Migrate heroes')
function migrate(id, notes) {
  return agent(`You are a senior technical artist on a film team. Move the signed-off hero "${id}" onto the shared kit ${KIT}/village_kit/ (read its README.md and CHANGELOG.md first; the roundhut is already migrated — use it as the pattern).
${REFS}
Read ${ROOT}/director/art_bible.md (producer notes 1-11), ${ROOT}/director/spec_${id}.md, the end of ${ROOT}/director/log_${id}.md (CLIENT CORRECTIONS), and ${ROOT}/director/ensemble_log.md.
Tasks:
1. Replace this building's private stone, shingle/shake, Mask, palette and pooling code with the kit's shared modules. Add this building's reusable parts to village_kit/components/ as parameterised functions (${notes.components}). Keep a kit_set() and a variant switch that builds a convincingly different variant.
2. Apply the ensemble consistency fix: ${notes.ensemble}
3. Apply producer note 11 (drop sub-threshold modelled relief except the entrance exception; DECAL_ANCHORS + decal_anchors.json).
4. Keep every phase-1 quality and CLIENT CORRECTION${notes.corrections}. The result must not look worse than ${ROOT}/buildings/${id}/signoff_phase1/ — compare renders side by side.
5. Render into ${ROOT}/renders/${id}/round_${pad(notes.round)} (all views, --samples 32), plus the variant into round_${pad(notes.round)}/kit_variant/. Append "## Round ${notes.round} — builder entry (kit migration)" to the log.

${TECH}
Return the structured report.`, { label: `migrate:${id}`, phase: 'Migrate heroes', schema: WORK_SCHEMA, effort: 'high' })
}

const priorHeroResults = (args && args.hero_results) || []
const gated = await parallel([
  ...((args && args.heroes_to_gate) || []).map(h => () => heroGate(h.id, h.round, 'Migrate heroes')),
  ...((args && args.heroes_to_migrate) || []).map(h => async () => {
    const m = await migrate(h.id, { ...h, components: h.components + (h.resume_note ? `. NOTE: ${h.resume_note}` : '') })
    if (!m) return { id: h.id, signed_off: false, error: 'migration failed' }
    return heroGate(h.id, h.round, 'Migrate heroes')
  }),
])
const heroResults = priorHeroResults.concat(gated.filter(Boolean))
const core = { summary: 'kit core built in the cloud session; see kit/village_kit/README.md and CHANGELOG.md' }

// ---------- Phase: Variants ----------
phase('Variants')
const vb = await agent(`You are the KIT ARCHITECT. The shared kit ${KIT}/village_kit/ now drives all three heroes (read README.md and CHANGELOG.md). Prove it can populate a 40-50 building village.
${REFS}
Read ${ROOT}/director/art_bible.md (producer notes 1-11) and ${ROOT}/director/production_plan.md.
Write ${KIT}/variants.py that assembles FOUR new variant buildings purely from kit components and parameters (no bespoke one-off geometry beyond small glue), each clearly a different building but unmistakably from the concept-art village:
  v1_small_roundhut — smaller daub roundhut, different radius/wall height/patches, maybe a lower cone;
  v2_stone_watchtower — a round stone tower with a conical shingle roof, bell cap and finial (keep/turret vocabulary);
  v3_tiered_hall — a hall with a bell-cast skirt roof and a smaller cone/turret, recombining keep components differently;
  v4_mixed — your choice of a convincing recombination across all three heroes (e.g. a stone-plinth daub house with a thatch wing, or a small mill-house).
Each variant: saved to ${ROOT}/buildings/variants/<vid>/<vid>.blend, follows every producer note (hidden ≤ 15%, palette, Mask, no ground dressing, decal anchors + decal_anchors.json, ≤ 1.5M tris), correct actor scale, clean seams/junctions between parts. Render each into ${ROOT}/renders/variants/<vid>/round_01 (all views, --samples 24) and inspect them. Fix seams and obvious problems before returning.

${TECH}
Return the structured list of variants.`, { label: 'architect:variants', phase: 'Variants', schema: VARIANTS_SCHEMA, effort: 'high' })

const variantResults = {}
if (vb && vb.variants && vb.variants.length) {
  let pending = vb.variants.map(v => v.id)
  for (let r = 1; r <= MAX_VARIANT_ROUNDS && pending.length; r++) {
    const grades = await parallel(pending.map(vid => () => {
      const v = vb.variants.find(x => x.id === vid)
      return grade(`kit VARIANT building "${vid}" (${v.description}; components: ${v.components_used.join(', ')}), variant round ${r}`,
        `${ROOT}/renders/variants/${vid}/round_${pad(r)}`, `${ROOT}/director/log_variants.md`,
        `This is not a reference building: judge it as a NEW building that must be unmistakably from the concept-art village, at the same quality bar as the signed-off heroes, with clean seams between kit parts.`,
        `Variant ${vid} round ${r}`, 'Variants').then(g => ({ vid, g }))
    }))
    const failing = []
    for (const x of grades.filter(Boolean)) {
      if (!x.g) continue
      variantResults[x.vid] = { round: r, score: x.g.score }
      log(`variant ${x.vid} r${r}: ${x.g.score}/10`)
      if (x.g.score < PASS) failing.push({ vid: x.vid, g: x.g })
    }
    pending = failing.map(f => f.vid)
    if (!pending.length || r === MAX_VARIANT_ROUNDS) break
    await agent(`You are the KIT ARCHITECT. Fix the failing kit variants below by improving the KIT COMPONENTS and variants.py (fixes should make the kit better, not add bespoke one-off geometry). Follow the kit edit rules.
${REFS}
${failing.map(f => `### ${f.vid} (${f.g.score}/10)\n${f.g.verdict}\nMUST FIX:\n- ${f.g.must_fix.join('\n- ')}`).join('\n\n')}

${TECH}
Rebuild ALL variants and all three heroes (heroes must still build with the same triangle counts ±0.5% unless a fix intentionally improves them — note it in the CHANGELOG). Render each failing variant into ${ROOT}/renders/variants/<vid>/round_${pad(r + 1)} (all views, --samples 24). Return the structured list of variants.`, { label: `architect:variant-fix:r${r + 1}`, phase: 'Variants', schema: VARIANTS_SCHEMA, effort: 'high' })
  }
} else {
  log('Variant builder returned no variants')
}

// ---------- Phase: Decision ----------
phase('Decision')
const context = `Hero kit-migration results: ${JSON.stringify(heroResults)}. Variant results (score at last graded round): ${JSON.stringify(variantResults)}. Pass mark ${PASS}.`
const decisions = await parallel([
  () => agent(`${DIRECTOR_ROLE}

TASK: KIT FEASIBILITY DECISION (phase 2 of ${ROOT}/director/production_plan.md). ${context}
Review ${KIT}/village_kit (README, CHANGELOG), the variant renders under ${ROOT}/renders/variants/, ${ROOT}/director/log_variants.md, and the migrated hero renders. Decide whether the kit can populate a 40-50 building village at the signed-off quality bar: kit_works, partial, or not_viable. Be honest about weak components and how many convincingly distinct buildings it can make today. Write your decision to ${ROOT}/director/kit_feasibility.md (section "Director decision"). Return the structured decision.`, { label: 'director:kit-decision', phase: 'Decision', schema: DECISION_SCHEMA, effort: 'high' }),
  () => agent(`You are an independent technical director for an Unreal 5.8 virtual production. ${context}
Review the shared kit ${KIT}/village_kit (code quality, API clarity, parameter coverage, determinism, seams, instancing/pooling, Mask, decal anchors, export-readiness for Unreal ISMs / Packed Level Actors) and the variant and hero renders under ${ROOT}/renders/. You may run the scripts. Decide independently: kit_works, partial, or not_viable for building a 40-50 building village. Append your review to ${ROOT}/director/kit_feasibility.md (section "Technical review"). Return the structured decision.`, { label: 'techdirector:kit-decision', phase: 'Decision', schema: DECISION_SCHEMA, effort: 'high' }),
])

return { core, heroResults, variants: vb, variantResults, decisions }
