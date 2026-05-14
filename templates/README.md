# NOVEL OPERATING SYSTEM

---

## Folder Structure

```
novel-os/
│
├── README.md                    ← This file
│
├── PROMPT_LIBRARY.md            ← All prompts to run the pipeline
│
├── NOVEL_SPEC.md                ← Master spec (voice, structure, themes) — THIS IS LAW
│
├── OUTLINE.md                   ← Scene-level chapter breakdown
│
├── CHARACTER_BIBLE.md           ← All character profiles
│
├── WORLD_BIBLE.md               ← Setting, world rules, factions
│
├── CONTINUITY_LOG.md            ← Running log of facts — UPDATE AFTER EVERY CHAPTER
│
├── chapters/
│   └── CH01_DRAFT.md            ← Chapter drafts go here
│
└── summaries/
    └── CH01_SUMMARY.md          ← 3-sentence summaries (input for next chapter's prompt)
```

---

## Starting a New Chapter: Quickstart

1. Open `OUTLINE.md` — find your chapter entry
2. Open `CHARACTER_BIBLE.md` — find the relevant POV character
3. Open `CONTINUITY_LOG.md` — scan for anything that affects this chapter
4. Open `PROMPT_LIBRARY.md` — run **CHAPTER DRAFT PROMPT** with the above pasted in
5. Run **BEAT CHECK PROMPT** on the result
6. Run **CONTINUITY CHECK PROMPT** — paste results back into `CONTINUITY_LOG.md`
7. Run **CHAPTER SUMMARY PROMPT** — save to `summaries/`
8. Every 3–4 chapters: run **VOICE CHECK**
9. Every 5 chapters: run **DEVELOPMENTAL MACRO PROMPT**

---

## Key Principles

**The spec is law.** If you want to change the spec, change it consciously and update `NOVEL_SPEC.md`. Don't let drafts drift from it silently.

**The continuity log is your memory.** Update it every single chapter. This is what prevents the novel from contradicting itself.

**Summaries are inputs, not outputs.** Save every chapter summary and feed them into subsequent drafts. The AI has no memory between sessions — summaries are how the story stays coherent.

**Beat check before moving on.** Don't draft the next chapter on top of one that scored a 2 on conflict escalation. Fix it first.

**You are the creative director.** AI gets you 70–85% of the way. You provide the restraint, the emotional truth, the pruning. The pipeline is a drafting tool, not a replacement for editorial judgment.

---

## What Each File Is For

| File | Purpose | When to reference |
|---|---|---|
| NOVEL_SPEC.md | Voice, structure, themes, banned phrases | Every draft session |
| OUTLINE.md | Chapter-level beats and goals | Before every chapter draft |
| CHARACTER_BIBLE.md | Who everyone is and how they talk | Every draft; paste relevant entries |
| WORLD_BIBLE.md | Where we are and what the rules are | When writing setting, special systems, travel |
| CONTINUITY_LOG.md | What has happened and been established | Before every chapter; update after |
| PROMPT_LIBRARY.md | The actual prompts | Every session |

---

## Recommended Session Rhythm

**Short session (1 chapter):**
→ Prep (10 min): read outline entry, skim continuity log
→ Draft (run prompt, review): 20 min
→ QA (beat check + continuity): 15 min
→ Log update: 5 min

**Long session (3 chapters):**
→ Prep all three outline entries
→ Draft, QA, log each in sequence
→ Voice check after third chapter
→ 5-chapter macro check if applicable

---

## Notes on Working With AI

The prompts in `PROMPT_LIBRARY.md` are designed for Claude (claude.ai). Use Claude Sonnet for drafting (faster, strong prose). Use Claude Opus for developmental review prompts if you want deeper analysis.

Paste the full relevant sections of each file into prompts — don't summarize them. The AI needs the actual text to maintain consistency.

If a chapter draft feels generically "AI," run the Voice Check prompt and look for the specific flagged phrases. Revise those sections yourself — ten minutes of human editing on flagged lines transforms a draft.
