# Resume prompt (desktop session 3)

The machine is already set up (see HANDOFF.md section 6). Open Claude Code in `C:\GitHubDesktop\git_test` and paste:

```
You are taking over an in-progress production from a previous Claude Code session on this same desktop. Work in C:\GitHubDesktop\git_test on branch claude/blender-buildings-film-nfzv6a. Use workflows / multi-agent orchestration as before. I am explicitly asking for it, as in the earlier sessions.

READ FIRST:
- blender_village/HANDOFF.md: the full state, every decision, and the machine notes;
- the files it lists in section 2;
- the producer notes 1-19 at the end of blender_village/director/art_bible.md;
- blender_village/director/production_plan.md (the variant table).
Treat them as the source of truth and do not re-litigate recorded decisions.

FIRST, confirm the state in HANDOFF section 4 (everything was accepted and nothing was running at the handoff) and give me a short status summary.

THEN continue my approved plan, in this order:
1. More LOW, ROOFED designs toward the 12-15 curated designs. No more towers. Every new design follows producer notes 16-19:
   - the same builders, techniques and materials;
   - round structures and soft, organic lines;
   - a rectangular or square cottage carries at least one eyebrow dormer;
   - square walls get rounded roofs: round hips plus a soft crown, "an oval on the rectangle".
   Use the kit's add-ons (valley, chimney, gabled dormer, eyebrow, lean-to, porch) for variety.
2. Step 5: the Unreal exporter (FBX/USD, cm, Nanite, Mask as vertex colour, decal_anchors.json, Packed Level Actor / ISM layouts), then a UE 5.8 lookdev test that measures Lumen, volumetric fog and the path tracer on the village (see director/performance_assessment.md).

WORKING CONVENTIONS:
- Time matters: do not spend time that can be avoided; the earlier a correct result is obtained, the better.
  - Fold my direction into the round in progress through the variant log, never by messaging a workflow agent.
  - Show me early preview renders so I can steer before grading.
  - Skip nice-to-haves and re-runs a change does not need.
- Reuse as many existing kit modules as possible.
- Team method: one builder; the Art Director grades on the modularity rubric (pass mark 8.2); an independent audit must uphold a pass. Audits use interior-volume see-through rays. Rounds are capped (ask me before going beyond the cap).
- Commit and push progress regularly with clear messages.
- Send me key screenshots (as file paths), the scores, the main notes and your own honest read whenever something is graded.
- Tell me straight away when anything is accepted or signed off.
- Keep me posted with short status updates, and ask me only for decisions that are genuinely mine.
```
