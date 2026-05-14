# PROMPT LIBRARY
*Copy-paste prompts for each stage of the pipeline. Fill in [BRACKETS] before running.*

---

## HOW TO USE THIS SYSTEM

Run these prompts in order for each chapter:
1. DRAFT PROMPT → get raw chapter
2. BEAT CHECK PROMPT → score the draft
3. CONTINUITY CHECK PROMPT → catch errors
4. VOICE CHECK PROMPT → catch drift
5. Update CONTINUITY_LOG.md with new facts

Developmental review (MACRO PROMPT) runs every 5 chapters.

---

## 1. CHAPTER DRAFT PROMPT

Paste this entire prompt, replacing [BRACKETS]:

---

```
You are drafting a chapter of a literary post-apocalyptic novel. Follow all specifications below exactly.

---
NOVEL SPEC:
[Paste contents of NOVEL_SPEC.md]

---
CHARACTER PROFILES (relevant to this chapter):
[Paste relevant character entries from CHARACTER_BIBLE.md]

---
WORLD STATE:
[Paste relevant sections from WORLD_BIBLE.md]

---
CONTINUITY LOG (recent entries):
[Paste last 10 entries from CONTINUITY_LOG.md]

---
CHAPTER TO DRAFT:
Chapter number: [N]
Title: [Title]
POV: [Character name]
Goal: [What does the POV character want in this scene?]
Conflict: [What opposes them?]
Revelation: [What changes — plot or character?]
Previous chapter summary (2-3 sentences): [Summary]
Chapter beat target: [Copy from OUTLINE.md]

---
INSTRUCTIONS:
- Target length: 2,800–3,200 words
- Follow the narrative voice exactly as specified in the NOVEL SPEC
- Do not include any of the banned phrases listed in the spec
- Do not introduce new characters without flagging it as [NEW CHARACTER: name, description]
- Do not resolve plot threads assigned to later chapters
- End the chapter as specified in the outline (cliffhanger / resonant close)
- Write in past tense, third-person limited from the specified POV
- Do not add chapter summaries, headers, or meta-commentary
- Output the chapter text only
```

---

## 2. BEAT CHECK PROMPT

Run after every draft:

---

```
You are a developmental editor evaluating a chapter draft against story craft criteria. Score each item 1–5. Be honest — this is a working draft, not a finished product.

CHAPTER TEXT:
[Paste chapter draft]

CHAPTER BEAT TARGET (from outline):
Goal: [paste]
Conflict: [paste]
Revelation: [paste]

EVALUATE:
1. Goal clarity (1–5): Was the POV character's goal clear within the first 500 words?
2. Conflict escalation (1–5): Did tension build through the chapter rather than staying flat?
3. Revelation landing (1–5): Did the specified revelation land with appropriate weight?
4. Character consistency (1–5): Did the POV character behave consistently with their established profile?
5. Pacing (1–5): Was exposition balanced against action and dialogue?
6. Chapter close (1–5): Did the chapter end with forward momentum?
7. Prose quality (1–5): Any repetitive phrases, weak verbs, adverb-heavy sentences?

For any score below 4: provide one specific, actionable revision note.
Output format: scores + revision notes only. No preamble.
```

---

## 3. CONTINUITY CHECK PROMPT

Run after every draft:

---

```
You are a continuity editor. Your job is to catch factual inconsistencies between this chapter draft and established canon.

CONTINUITY LOG (full):
[Paste full CONTINUITY_LOG.md]

CHARACTER BIBLE (relevant entries):
[Paste relevant sections]

WORLD BIBLE (relevant sections):
[Paste relevant sections]

CHAPTER DRAFT:
[Paste chapter]

CHECK FOR:
- Character details contradicting established profiles (appearance, speech, injury, history)
- Timeline inconsistencies
- Geography errors (distances, locations)
- Object placement errors (where is [object] and is it consistent?)
- Any new facts introduced (list them for the continuity log)
- Any promises or compacts made (note them)

OUTPUT FORMAT:
CONTRADICTIONS: [list any found, or "None found"]
NEW FACTS INTRODUCED: [list all]
NEW PROMISES/COMPACTS: [list any]
CONTINUITY LOG ADDITIONS: [formatted entries ready to paste into CONTINUITY_LOG.md]
```

---

## 4. VOICE CHECK PROMPT

Run after every 3–4 chapters, or when something feels off:

---

```
You are a voice and style editor. Your job is to determine whether this chapter sounds consistent with the established voice of this novel.

VOICE SPECIFICATION (from NOVEL_SPEC.md):
[Paste the Narrative Voice section]

BANNED PHRASES/PATTERNS:
[Paste the banned list]

REFERENCE SAMPLE (a chapter you're happy with):
[Paste 500 words from a chapter you consider on-voice]

CHAPTER TO CHECK:
[Paste chapter]

EVALUATE:
1. Does the prose rhythm match the reference sample?
2. Are any banned phrases or patterns present? (List them with line context)
3. Is there any AI-voice intrusion? ("He couldn't help but feel", "She found herself", etc.) (List them)
4. Any modern slang or anachronistic language?
5. Sentence length variation: too uniform (all short or all long)?
6. Any repetitive metaphors or images?
7. Overall voice score 1–10

OUTPUT: Issues list with specific quotes. No preamble.
```

---

## 5. DEVELOPMENTAL MACRO PROMPT

Run every 5 chapters:

---

```
You are a developmental editor reviewing the cumulative structure of a novel in progress.

NOVEL SPEC (structure section):
[Paste structural model from NOVEL_SPEC.md]

OUTLINE (chapters covered):
[Paste outline entries for chapters reviewed]

CHAPTER SUMMARIES (2–3 sentences each):
Chapter [N]: [summary]
Chapter [N+1]: [summary]
[etc.]

EVALUATE:
1. Pacing: Is Act I/II/III balance tracking correctly for the target length?
2. Character arcs: Are all three primary POVs advancing their arcs?
3. Theme development: Which themes are landing? Which are underdeveloped?
4. Setup/payoff: Any setups that haven't been planted yet that need to be?
5. Redundancy: Any scenes that duplicate emotional or plot beats?
6. Momentum: Is there a weak chapter that needs strengthening?
7. Midpoint tracking: Are seeds for the midpoint revelation being planted?

OUTPUT: Numbered issues with specific chapter references. No preamble.
```

---

## 6. CHAPTER SUMMARY PROMPT

Run after finalizing each chapter (use summaries in subsequent drafts):

---

```
Write a 3-sentence summary of this chapter for use in continuity reference. Include:
- What happened (plot)
- What changed (character or relationship)
- What was revealed or seeded (for future payoff)

Keep it factual. No analysis. No spoilers beyond what the chapter contains.

CHAPTER TEXT:
[Paste chapter]
```

---

## 7. MULTI-PERSONA STRUCTURAL REVIEW

Run every 5 chapters, alongside or replacing the DEVELOPMENTAL MACRO PROMPT. Each persona reviews through a distinct lens — complete them in order, do not blend them.

---

```
You are five different editorial readers. Review the material below through each persona's lens separately. Complete one persona fully before moving to the next.

---
NOVEL SPEC:
[Paste relevant sections of NOVEL_SPEC.md]

---
OUTLINE (chapters covered):
[Paste outline entries for the chapters under review]

---
CHAPTER SUMMARIES:
Chapter [N]: [3-sentence summary]
Chapter [N+1]: [3-sentence summary]
[Continue for all chapters under review]

---

ARCHITECT — structural analysis
You see the novel as an engineering problem. Examine:
- Does the act structure hold at this stage? Is pacing tracking correctly for the target length?
- Are setups being planted for the payoffs specified in the outline?
- Is the midpoint revelation being seeded correctly?
- Are there structural gaps, redundant scenes, or chapters that carry no load?
Report: numbered issues with specific chapter references. No preamble.

---

ACTOR — character consistency
You inhabit each character. Examine:
- Does every character behave consistently with their established profile (core wound, flaw, motivation, voice)?
- Are there moments where a character acts for plot convenience rather than from their psychology?
- Are relationships evolving at a believable rate?
- Does each POV chapter sound distinct from the others?
Report: numbered issues with specific chapter references. No preamble.

---

EDITOR — redundancy and flatness
You cut for a living. Examine:
- Which scenes duplicate an emotional or plot beat already delivered?
- Which chapters have no revelation — nothing changes by the end?
- Where does pacing stall?
- What could be removed without losing anything the novel needs?
Report: numbered issues with specific chapter references. No preamble.

---

PHILOSOPHER — thematic coherence
You read for meaning. Examine:
- Which themes from the NOVEL_SPEC are landing in these chapters?
- Which are underdeveloped or absent?
- Are there scenes that argue against the thematic spine — that point toward the wrong conclusion?
- Is the novel's central question being genuinely complicated, or just restated?
Report: numbered issues with specific chapter references. No preamble.

---

DREAMER — originality and aliveness
You read for surprise. Examine:
- Where has the prose gone safe, generic, or predictable?
- Which scenes feel like the version of this story anyone would write, rather than the version only this author would write?
- Where is the language most alive? (Note these — they are the target register.)
- Any images, metaphors, or dialogue exchanges that feel borrowed rather than found?
Report: numbered issues with specific quotes where possible. Note the alive passages too. No preamble.
```

---

## 8. RIPPLE AUDIT

Run after any significant revision to an already-drafted chapter. Traces every downstream consequence of the change across remaining chapters.

---

```
You are a continuity and consequence auditor. A chapter has been revised. Trace every downstream effect of that revision across the remaining manuscript.

---
WHAT CHANGED:

Original chapter summary (before revision):
[2–3 sentences on what the chapter contained before]

Revised chapter summary (after revision):
[2–3 sentences on what is different now]

Specific changes made:
[List the exact facts, character states, plot points, seeded details, or object locations that are different in the revised version]

---
CONTINUITY LOG (full):
[Paste full CONTINUITY_LOG.md]

---
OUTLINE (all chapters after the revised one):
[Paste outline entries for every remaining chapter]

---

AUDIT FOR:

1. Contradictions created: Which established facts in later chapters now conflict with the revision?
2. Orphaned seeds: Which details seeded in chapters after the revised one now reference something the revision has changed or removed?
3. Character state errors: Which later chapters show a character in a state the revision no longer supports?
4. Timeline errors: Does the revision create any timeline inconsistencies in subsequent chapters?
5. Object / location errors: Are any objects or locations referenced later that the revision has moved, changed, or removed?
6. Promises broken: Has the revision altered any commitment or compact that is paid off in a later chapter?

OUTPUT FORMAT:
CONTRADICTIONS CREATED: [list, or "None found"]
ORPHANED SEEDS: [list, or "None found"]
CHARACTER STATE ERRORS: [list, or "None found"]
TIMELINE ERRORS: [list, or "None found"]
OBJECT/LOCATION ERRORS: [list, or "None found"]
PROMISES BROKEN: [list, or "None found"]
CONTINUITY LOG UPDATES NEEDED: [formatted entries ready to paste into CONTINUITY_LOG.md]
```

---

## WORKFLOW CHECKLIST (per chapter)

- [ ] Read relevant OUTLINE.md entry
- [ ] Read relevant CHARACTER_BIBLE.md entries
- [ ] Read relevant WORLD_BIBLE.md sections
- [ ] Check CONTINUITY_LOG.md for anything affecting this chapter
- [ ] Run DRAFT PROMPT
- [ ] Run BEAT CHECK PROMPT — revise if any score below 3
- [ ] Run CONTINUITY CHECK PROMPT — update CONTINUITY_LOG.md
- [ ] Run CHAPTER SUMMARY PROMPT — save to /summaries/CH[N]_SUMMARY.md
- [ ] Run VOICE CHECK every 3–4 chapters
- [ ] Run MULTI-PERSONA REVIEW every 5 chapters (replaces or supplements MACRO PROMPT)
- [ ] Run RIPPLE AUDIT after any revision to a previously completed chapter
