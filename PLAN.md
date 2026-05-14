Below is the **copy/paste-ready prompt** to give Claude Code as `PLAN.md`.

````markdown
# PLAN.md — Local-First AI Novel Studio

Build a local-first desktop application for managing a structured AI-assisted long-form fiction workflow.

This is NOT a generic AI writing app. It is a human-directed novel production environment based on an existing markdown framework: novel spec, outline, character bible, world bible, continuity log, prohibited language rules, prompt library, and writing-refiner agent.

## Core Goal

Create a desktop app that streamlines this workflow:

1. Import or create a novel project.
2. Maintain structured project files:
   - NOVEL_SPEC.md
   - OUTLINE.md
   - CHARACTER_BIBLE.md
   - WORLD_BIBLE.md
   - CONTINUITY_LOG.md
   - PROHIBITED.md / prohibited.yaml
   - PROMPT_LIBRARY.md
   - chapters/
   - summaries/
3. Generate chapters using Claude via Anthropic API.
4. Automatically gather relevant context for each chapter.
5. Run QA passes:
   - beat check
   - continuity audit
   - voice audit
   - prose lint
   - ripple audit
   - structural review
6. Save chapters, summaries, revisions, QA reports, and continuity updates.
7. Keep everything local-first.
8. Export a manuscript.

## Technical Stack

Use:

- Tauri desktop app
- React frontend
- Python backend
- SQLite database
- Local filesystem project storage
- Anthropic API direct integration
- Markdown as primary human-readable format
- SQLite as machine-readable canonical state

Do NOT build:

- SaaS
- cloud sync
- auth
- billing
- collaboration
- user accounts
- beta reader portal
- cover generator
- image generation
- audiobook tools

## Project Philosophy

The app should preserve author control.

AI assists. The human directs.

The system should not push “one-click novel generation.” It should emphasize structured authorial governance: continuity, voice, chapter purpose, revision discipline, and anti-AI-prose linting.

## Initial Folder Structure

Create:

```text
novel-studio/
  README.md
  PLAN.md
  app/
    frontend/
    backend/
  templates/
    NOVEL_SPEC.md
    OUTLINE.md
    CHARACTER_BIBLE.md
    WORLD_BIBLE.md
    CONTINUITY_LOG.md
    PROHIBITED.md
    PROMPT_LIBRARY.md
    writing-refiner.md
  projects/
  data/
    app.db
````

Each project should look like:

```text
projects/
  project-slug/
    project.json
    novel_spec.md
    outline.md
    character_bible.md
    world_bible.md
    continuity_log.md
    prohibited.yaml
    prompt_library.md
    chapters/
      CH001_DRAFT.md
      CH001_FINAL.md
    summaries/
      CH001_SUMMARY.md
    qa/
      CH001_BEAT_CHECK.md
      CH001_CONTINUITY.md
      CH001_VOICE.md
      CH001_LINT.md
    revisions/
    exports/
```

## Database Schema

Use SQLite.

Create tables:

### projects

* id
* slug
* title
* created_at
* updated_at
* root_path
* target_word_count
* pov
* tense
* genre
* status

### chapters

* id
* project_id
* chapter_number
* title
* pov_character
* status
* target_word_count
* actual_word_count
* outline_goal
* outline_conflict
* outline_revelation
* outline_notes
* draft_path
* final_path
* summary_path
* created_at
* updated_at

### characters

* id
* project_id
* name
* role
* age
* physical
* core_wound
* internal_flaw
* external_flaw
* motivation
* voice_description
* sample_internal_voice
* arc_begin
* arc_midpoint
* arc_end
* raw_markdown

### world_facts

* id
* project_id
* category
* title
* fact
* source_file
* source_section
* created_at
* updated_at

### continuity_facts

* id
* project_id
* chapter_id
* fact_type
* subject
* fact
* status
* created_at

fact_type values:

* character_state
* object_location
* injury
* death
* promise
* mystery
* seed
* timeline
* world_fact
* relationship
* other

### object_locations

* id
* project_id
* object_name
* owner
* last_known_location
* chapter_id
* status

### injuries

* id
* project_id
* character_name
* injury
* introduced_chapter_id
* status

### deaths

* id
* project_id
* character_name
* death_description
* chapter_id
* confirmed

### promises

* id
* project_id
* who
* promise
* to_whom
* chapter_id
* kept_status

### mysteries

* id
* project_id
* mystery
* introduced_chapter_id
* target_resolution
* status

### seeds

* id
* project_id
* seed
* planted_chapter_id
* payoff_target
* status

### qa_reports

* id
* project_id
* chapter_id
* report_type
* score
* report_markdown
* created_at

report_type values:

* beat_check
* continuity_check
* voice_check
* prose_lint
* ripple_audit
* structural_review
* final_review

### revisions

* id
* project_id
* chapter_id
* revision_number
* before_path
* after_path
* change_summary
* created_at

## Backend Responsibilities

The Python backend should provide:

1. Project creation
2. Project import from markdown framework
3. Project loading
4. Project file parsing
5. SQLite sync
6. Chapter generation
7. QA pipeline execution
8. Prose linting
9. Continuity extraction
10. Chapter summary generation
11. Manuscript export

## API Endpoints / Commands

Implement backend functions callable by Tauri frontend:

```python
create_project(project_name: str) -> Project
import_project(folder_path: str) -> Project
get_projects() -> list[Project]
get_project(project_id: int) -> ProjectDetail
get_chapters(project_id: int) -> list[Chapter]
get_chapter(project_id: int, chapter_number: int) -> ChapterDetail
save_chapter(project_id: int, chapter_number: int, markdown: str) -> None
generate_chapter(project_id: int, chapter_number: int) -> GenerationResult
run_beat_check(project_id: int, chapter_number: int) -> QAReport
run_continuity_check(project_id: int, chapter_number: int) -> QAReport
run_voice_check(project_id: int, chapter_number: int) -> QAReport
run_prose_lint(project_id: int, chapter_number: int) -> LintReport
run_ripple_audit(project_id: int, chapter_number: int, change_summary: str) -> QAReport
generate_chapter_summary(project_id: int, chapter_number: int) -> str
approve_chapter(project_id: int, chapter_number: int) -> None
export_manuscript(project_id: int, format: str) -> ExportResult
```

## Anthropic Integration

Use Anthropic API directly.

Environment variable:

```bash
ANTHROPIC_API_KEY=
```

Create a model abstraction layer:

```python
class LLMClient:
    def complete(self, system_prompt: str, user_prompt: str, model: str) -> str:
        ...
```

Default model:

```text
claude-sonnet-4-5
```

Allow model to be configurable later.

Do not hard-code one provider throughout the app. Keep a provider abstraction so OpenAI/Ollama can be added later.

## Agent System

Create separate agent modules:

```text
backend/agents/
  draft_agent.py
  beat_editor.py
  continuity_auditor.py
  voice_auditor.py
  prose_linter.py
  ripple_auditor.py
  structural_reviewer.py
  summary_agent.py
  final_reviewer.py
```

Each agent should:

* assemble its own context
* use a prompt template
* call LLMClient if needed
* save output to project qa/ or summaries/
* update database where appropriate

## Context Assembly

For chapter generation, automatically assemble:

* full NOVEL_SPEC
* relevant OUTLINE entry
* POV character profile
* relevant character relationship entries
* relevant WORLD_BIBLE sections
* recent continuity facts
* unresolved seeds
* unresolved mysteries
* active injuries
* object locations relevant to chapter
* previous chapter summary
* prohibited language rules
* writing-refiner style instructions

Do NOT require manual copy/paste.

## Chapter Generation Prompt Shape

Use this structure:

```text
SYSTEM:
You are a disciplined literary fiction drafting agent working inside a human-directed novel production system. Preserve the author's voice, obey the project specification, and do not introduce unsupported continuity.

USER:
NOVEL SPEC:
...

POV CHARACTER:
...

WORLD CONTEXT:
...

CONTINUITY CONTEXT:
...

OUTLINE ENTRY:
...

PREVIOUS CHAPTER SUMMARY:
...

PROHIBITED LANGUAGE RULES:
...

WRITING REFINER STYLE:
...

TASK:
Draft Chapter [N].
Follow the outline goal, conflict, and revelation.
Write in the specified POV and tense.
Avoid prohibited language.
Do not add meta-commentary.
Output chapter prose only.
```

## Prose Linter

Implement a deterministic linter before relying on AI.

Rules:

* count em dashes
* flag banned words
* flag banned phrases
* flag “couldn’t help but”
* flag “a sense of”
* flag “washed over”
* flag “swept through”
* flag “flooded back”
* flag “hung in the air”
* flag “it was as if”
* flag “as though”
* flag “not X, but Y” pattern
* flag repetitive paragraph length
* flag repeated sentence openings
* flag excessive adverbs
* flag repeated metaphors if exact phrase repeats

Output:

```text
Line / paragraph
Issue type
Matched text
Recommendation
```

Save report to:

```text
qa/CH###_LINT.md
```

## Continuity Handling

The continuity log remains readable markdown, but SQLite is the canonical machine state.

When continuity audit finds new facts:

1. Save QA report.
2. Extract candidate facts.
3. Present them to user for approval.
4. On approval:

   * update SQLite
   * append formatted entry to continuity_log.md

Do not silently alter canon without user approval.

## UI Requirements

Create a clean, practical interface.

Primary screens:

### 1. Project Dashboard

Shows:

* project title
* chapters completed
* current chapter
* unresolved mysteries
* unresolved seeds
* active continuity warnings
* recent QA findings

Buttons:

* Open Project
* New Project
* Import Project

### 2. Project Workspace

Left sidebar:

* Novel Spec
* Outline
* Characters
* World Bible
* Continuity
* Chapters
* QA Dashboard
* Export

Main panel changes by section.

### 3. Chapter Pipeline Screen

For selected chapter:

* outline goal/conflict/revelation
* previous summary
* current draft editor
* QA reports
* action buttons

Buttons:

* Generate Draft
* Run Beat Check
* Run Continuity Check
* Run Voice Check
* Run Prose Lint
* Generate Summary
* Approve Chapter

### 4. Markdown Editor

Basic markdown editor with:

* save
* word count
* preview
* diff view later

### 5. Continuity Explorer

Show tabs:

* Facts
* Injuries
* Deaths
* Objects
* Promises
* Mysteries
* Seeds

Allow filtering by character, chapter, type, status.

### 6. QA Dashboard

Show:

* chapter
* report type
* date
* unresolved issues
* severity if available

## Import Existing Markdown Framework

Implement importer that accepts a folder containing:

* NOVEL_SPEC.md
* OUTLINE.md
* CHARACTER_BIBLE.md
* WORLD_BIBLE.md
* CONTINUITY_LOG.md
* PROHIBITED.md
* PROMPT_LIBRARY.md
* writing-refiner.md

The importer should:

1. Copy files into project folder.
2. Parse project title from NOVEL_SPEC if possible.
3. Parse outline chapter entries.
4. Parse character sections.
5. Parse continuity entries if possible.
6. Convert prohibited language into prohibited.yaml.
7. Store raw markdown if parsing is imperfect.
8. Never delete source files.

## Export

Implement markdown manuscript export first.

Output:

```text
exports/manuscript.md
```

Concatenate approved final chapters in order.

Later add:

* DOCX
* EPUB

But MVP only needs markdown export.

## MVP Milestones

### Milestone 1 — Project Shell

* Tauri app launches
* Python backend runs
* SQLite initializes
* Create project
* Import project folder
* Open project dashboard

### Milestone 2 — Markdown Project Management

* View/edit novel_spec
* View/edit outline
* View/edit character_bible
* View/edit world_bible
* View/edit continuity_log
* Save changes

### Milestone 3 — Parser + Database Sync

* Parse outline chapters
* Parse character bible
* Parse prohibited language
* Store parsed entities in SQLite
* Show chapters in UI

### Milestone 4 — Chapter Pipeline

* Select chapter
* Assemble context
* Generate draft using Anthropic API
* Save draft
* View/edit draft

### Milestone 5 — QA Pipeline

* Run beat check
* Run continuity check
* Run voice check
* Run deterministic prose lint
* Save QA reports
* Show reports in UI

### Milestone 6 — Continuity Approval

* Extract new continuity facts
* Present candidate facts
* User approves/rejects
* Update SQLite
* Append to continuity_log.md

### Milestone 7 — Chapter Summary + Approval

* Generate 3-sentence summary
* Save to summaries/
* Mark chapter approved
* Move/copy draft to final

### Milestone 8 — Export

* Export approved chapters to manuscript.md

## Development Rules

* Keep the app local-first.
* Do not add cloud features.
* Do not add auth.
* Do not add billing.
* Do not overbuild.
* Prefer simple working tools over elegant abstractions.
* Preserve markdown files as first-class artifacts.
* SQLite should support the workflow, not replace human-readable files.
* All AI outputs must be saved as files.
* User must approve canon-changing continuity updates.
* Avoid destructive operations.

## Initial Implementation Task

Start by scaffolding the repo.

Then implement Milestone 1 only.

After Milestone 1 works, proceed milestone by milestone.

Do not jump ahead into SaaS, cloud sync, or publishing features.

## Definition of Done for MVP

The MVP is done when I can:

1. Import my existing novel framework folder.
2. Open a project.
3. Select a chapter from the outline.
4. Generate a draft using Claude.
5. Run beat check.
6. Run continuity check.
7. Run voice check.
8. Run prose lint.
9. Approve continuity additions.
10. Save a chapter summary.
11. Approve the chapter.
12. Export approved chapters to one markdown manuscript.

Build that first.

````

Give Claude Code that as `PLAN.md`, then tell it:

```text
Read PLAN.md. Implement Milestone 1 only. Do not proceed to Milestone 2 until Milestone 1 is working.
````
