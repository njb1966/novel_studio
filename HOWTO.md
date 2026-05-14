# HOWTO — Novel Studio

Step-by-step guide to installing, running, and using Novel Studio.

---

## 1. Prerequisites

### System packages (Debian/Ubuntu)

```bash
sudo apt-get install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libjavascriptcoregtk-4.1-dev \
  librsvg2-dev \
  libssl-dev \
  libglib2.0-dev \
  libcairo2-dev \
  libpango1.0-dev \
  libgdk-pixbuf-2.0-dev
```

### Toolchains

- **Node.js 18+** — `node --version`
- **Rust (stable)** — install via [rustup.rs](https://rustup.rs)
- **Python 3.11+** — `python3 --version`

### Anthropic API key

Get one at [console.anthropic.com](https://console.anthropic.com). Set it in your environment:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Add that line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

---

## 2. Install

```bash
git clone https://github.com/njb1966/novel_studio.git
cd novel_studio
```

Install frontend dependencies:

```bash
cd app/frontend
npm install
cd ../..
```

The backend installs its own virtualenv on first run (Step 3).

---

## 3. Run (development)

Open two terminals.

**Terminal 1 — Python backend:**

```bash
cd app/backend
bash start.sh
```

This creates a `.venv`, installs Python dependencies, and starts FastAPI on `http://localhost:8765`.

You should see:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8765
```

**Terminal 2 — Tauri frontend:**

```bash
cd app/frontend
npm run tauri dev
```

The Rust build takes a few minutes on first run. Subsequent starts are fast.

---

## 4. Create or import a project

### Import an existing novel framework

If you already have a folder with markdown files (`NOVEL_SPEC.md`, `OUTLINE.md`, `CHARACTER_BIBLE.md`, `WORLD_BIBLE.md`, `CONTINUITY_LOG.md`, `PROHIBITED.md`, `writing-refiner.md`):

1. Click **Import** on the dashboard
2. Enter the full path to the folder, e.g. `/home/nick/my-novel`
3. The app copies the files into `projects/<slug>/` and reads the title from `NOVEL_SPEC.md`

### Create a new project

1. Click **+ New Project**
2. Fill in title, genre, POV, tense, target word count
3. Template files from `templates/` are copied into the new project folder

---

## 5. Sync the project

After creating or importing a project, click **Sync** in the workspace header.

This parses:
- `outline.md` → chapters table in SQLite
- `character_bible.md` → characters table
- `PROHIBITED.md` → `prohibited.yaml`

You only need to sync again if you manually edit the markdown files outside the app.

---

## 6. Write a chapter

1. Click **Open** on the project dashboard
2. Click **Chapters** in the sidebar
3. Click a chapter row to open the chapter pipeline

### Generate a draft

Click **Generate Draft**. The app assembles context automatically:

- Full novel spec
- The chapter's outline entry (goal, conflict, revelation)
- POV character profile
- World bible
- Recent continuity facts
- Previous chapter summary
- Prohibited language rules
- Writing refiner style guide

Claude generates the draft prose (15–60 seconds). The result appears in the editor.

Edit the draft directly in the textarea. Click **Save Draft** to save.

---

## 7. Run QA passes

Four QA checks are available in the chapter pipeline:

| Check | Method | What it does |
|---|---|---|
| Prose Lint | Deterministic | Flags banned words, phrases, patterns, rhythm problems, adverb density |
| Beat Check | Claude | Verifies the chapter delivers its outlined goal, conflict, revelation |
| Continuity Check | Claude | Checks the draft against all logged continuity facts |
| Voice Check | Claude | Assesses whether the prose matches the POV character's voice profile |

Each check saves a report to `projects/<slug>/qa/CH001_*.md` and shows a score badge (green ≥80, yellow 60–79, red <60).

Run **Prose Lint** first — it's instant and catches the most common AI prose problems before spending API calls on the others.

---

## 8. Manage continuity

### Extract new facts

After the continuity check, click **Extract New Facts**. Claude reads the draft and returns a JSON list of candidate continuity facts (injuries, deaths, promises, mysteries, seeds, object locations, etc.).

### Approve or reject

Click **Continuity** in the sidebar to open the Continuity Explorer.

- **Pending Approval tab**: review each candidate fact, click Approve or Reject
- Approved facts are written to SQLite and appended to `continuity_log.md`
- Rejected facts are discarded
- **Active Facts tab**: browse all approved facts, filter by type, search by subject

These facts become context for future chapter generation automatically.

---

## 9. Finalise a chapter

### Generate summary

Click **Generate Summary**. Claude produces a 3-sentence summary covering:
1. What happened
2. What changed
3. What was revealed or set up

Saved to `summaries/CH001_SUMMARY.md`. Used as context when generating the next chapter.

### Approve chapter

Click **Approve Chapter** (only enabled when both draft and summary exist).

- Copies `CH001_DRAFT.md` → `CH001_FINAL.md`
- Sets chapter status to `approved`
- Locks the chapter (Generate Draft is disabled)

---

## 10. Export the manuscript

1. Click **Export** in the sidebar
2. Choose options:
   - Include chapter headings (on by default)
   - Include summaries after each chapter (off by default)
3. Click **Export Approved Chapters**

Output is written to `projects/<slug>/exports/manuscript.md`.

Only approved chapters are included, in chapter number order.

---

## File locations

All project files are plain markdown on disk:

```
projects/<slug>/
  novel_spec.md            Edit via sidebar or any text editor
  outline.md
  character_bible.md
  world_bible.md
  continuity_log.md        Auto-appended when continuity facts are approved
  prohibited.yaml          Generated from PROHIBITED.md on sync
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

You can edit any of these files in your text editor. Run Sync again after editing the outline or character bible to update the database.

---

## Troubleshooting

### "Backend: Offline" in the status bar

The Python backend is not running. Start it:

```bash
cd app/backend
bash start.sh
```

### `ANTHROPIC_API_KEY` not set

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Set this before starting the backend. Or add it to your shell profile.

### Port 8765 already in use

```bash
fuser -k 8765/tcp
```

Then restart the backend.

### Tauri build fails — missing GTK/WebKit

Install the system packages listed in Section 1. On Debian 13, the package name may be `libwebkit2gtk-4.1-dev` — check with `apt-cache search webkit2gtk`.

### Characters not appearing after sync

The character parser skips headings that are placeholders (e.g. `[CHARACTER NAME]`). Your `character_bible.md` must have real character names as `##` headings for them to parse.

### Chapters not appearing after sync

The outline parser looks for `## Chapter N` or `**CHAPTER N**` headings. Check that your `outline.md` uses one of these formats.
