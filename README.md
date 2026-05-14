# Novel Studio

A local-first desktop application for managing AI-assisted long-form fiction production.

Built with Tauri, React, Python, and the Anthropic API. Everything runs on your machine. No cloud, no accounts, no sync.

## What it does

Novel Studio implements a structured chapter-by-chapter production pipeline:

1. Import your existing novel framework (spec, outline, character bible, world bible, continuity log, prohibited language rules)
2. Parse the outline and character bible into a SQLite database
3. Select a chapter and generate a draft — Claude assembles context automatically
4. Run QA passes: prose lint (deterministic), beat check, continuity check, voice check
5. Extract new continuity facts from the draft and approve or reject each one
6. Generate a 3-sentence chapter summary
7. Approve the chapter (copies draft to final)
8. Export all approved chapters as a single markdown manuscript

## Stack

| Layer | Technology |
|---|---|
| Desktop shell | Tauri |
| Frontend | React (Vite) |
| Backend | Python / FastAPI |
| Database | SQLite (aiosqlite) |
| AI | Anthropic API (claude-sonnet-4-6) |
| Storage | Local filesystem |

## Project structure

```
novel-studio/
  app/
    frontend/         Tauri + React app
    backend/          Python FastAPI backend
  templates/          Starter markdown files
  projects/           Your novel projects (created at runtime)
  data/               SQLite database (created at runtime)
  dev.md              How to run in development
```

Each project folder:

```
projects/my-novel/
  novel_spec.md
  outline.md
  character_bible.md
  world_bible.md
  continuity_log.md
  prohibited.yaml
  prompt_library.md
  writing-refiner.md
  chapters/
    CH001_DRAFT.md
    CH001_FINAL.md
  summaries/
    CH001_SUMMARY.md
  qa/
    CH001_LINT.md
    CH001_BEAT_CHECK.md
    CH001_CONTINUITY.md
    CH001_VOICE.md
  exports/
    manuscript.md
```

## Philosophy

AI assists. The human directs.

This is not a one-click novel generator. Every chapter is produced through explicit authorial decisions: the outline drives generation, the QA passes surface problems, continuity facts require approval before they become canon, and the chapter must be explicitly approved before it is included in the export.

The markdown files are first-class artifacts. The SQLite database supports the workflow; it does not replace the files.

## Requirements

- Node.js 18+
- Rust (stable)
- Python 3.11+
- GTK3 / WebKit2GTK (Linux — see HOWTO.md)
- Anthropic API key

## Quick start

See [HOWTO.md](HOWTO.md).

## License

MIT
