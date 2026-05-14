"""
QA pipeline endpoints.

POST /projects/{project_id}/chapters/{chapter_number}/lint
POST /projects/{project_id}/chapters/{chapter_number}/beat-check
POST /projects/{project_id}/chapters/{chapter_number}/continuity-check
POST /projects/{project_id}/chapters/{chapter_number}/voice-check
GET  /projects/{project_id}/chapters/{chapter_number}/reports
GET  /projects/{project_id}/qa
"""

import os
import re
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from models import QAReport
from agents.prose_linter import lint_prose
from agents.beat_editor import run_beat_check
from agents.continuity_auditor import run_continuity_check
from agents.voice_auditor import run_voice_check
from parsers.prohibited_parser import parse_prohibited

router = APIRouter(prefix="/projects", tags=["qa"])

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_BACKEND_DIR)))
PROJECTS_DIR = os.path.join(_REPO_ROOT, "projects")

# Report type identifiers — also used as folder filenames
_TYPE_LINT        = "LINT"
_TYPE_BEAT        = "BEAT_CHECK"
_TYPE_CONTINUITY  = "CONTINUITY"
_TYPE_VOICE       = "VOICE"


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_score(text: str) -> int:
    """Parse 'SCORE: N' from end of report text. Returns 0 if not found."""
    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_root_path(db, project_id: int) -> str:
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    return row[0]


async def _get_chapter_id(db, project_id: int, chapter_number: int) -> int:
    async with db.execute(
        "SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?",
        (project_id, chapter_number),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    return row[0]


def _save_report_file(root_path: str, chapter_number: int, report_type: str, content: str) -> str:
    """Write report markdown to projects/<slug>/qa/CH{N}_{TYPE}.md. Returns relative path."""
    qa_dir = os.path.join(root_path, "qa")
    os.makedirs(qa_dir, exist_ok=True)
    filename = f"CH{chapter_number:03d}_{report_type}.md"
    abs_path = os.path.join(qa_dir, filename)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.join("qa", filename)


async def _insert_report(
    db,
    project_id: int,
    chapter_id: int,
    report_type: str,
    score: int,
    report_markdown: str,
) -> QAReport:
    now = _now()
    async with db.execute(
        """INSERT INTO qa_reports (project_id, chapter_id, report_type, score, report_markdown, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (project_id, chapter_id, report_type, score, report_markdown, now),
    ) as cur:
        row_id = cur.lastrowid
    await db.commit()

    return QAReport(
        id=row_id,
        project_id=project_id,
        chapter_id=chapter_id,
        report_type=report_type,
        score=score,
        report_markdown=report_markdown,
        created_at=now,
    )


def _row_to_report(row) -> QAReport:
    return QAReport(
        id=row[0],
        project_id=row[1],
        chapter_id=row[2],
        report_type=row[3],
        score=row[4],
        report_markdown=row[5],
        created_at=row[6],
    )


# ── Prose Lint ────────────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/lint")
async def run_lint(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        root_path  = await _get_root_path(db, project_id)
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        # Parse prohibited list from project folder
        prohibited = parse_prohibited(root_path)

        # Read draft text
        draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
        draft_path = os.path.join(root_path, "chapters", draft_filename)
        if not os.path.isfile(draft_path):
            raise HTTPException(status_code=404, detail="Draft not found. Generate a draft first.")

        with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
            draft_text = f.read()

        # Run linter (no LLM)
        report_markdown = lint_prose(draft_text, prohibited)

        # Save file
        _save_report_file(root_path, chapter_number, _TYPE_LINT, report_markdown)

        # Lint is not scored (returns 0)
        report = await _insert_report(db, project_id, chapter_id, _TYPE_LINT, 0, report_markdown)

    return report


# ── Beat Check ────────────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/beat-check")
async def run_beat_check_endpoint(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        root_path  = await _get_root_path(db, project_id)
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        report_markdown = await run_beat_check(project_id, chapter_number, db)
        score = extract_score(report_markdown)

        _save_report_file(root_path, chapter_number, _TYPE_BEAT, report_markdown)
        report = await _insert_report(db, project_id, chapter_id, _TYPE_BEAT, score, report_markdown)

    return report


# ── Continuity Check ──────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/continuity-check")
async def run_continuity_check_endpoint(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        root_path  = await _get_root_path(db, project_id)
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        report_markdown = await run_continuity_check(project_id, chapter_number, db)
        score = extract_score(report_markdown)

        _save_report_file(root_path, chapter_number, _TYPE_CONTINUITY, report_markdown)
        report = await _insert_report(db, project_id, chapter_id, _TYPE_CONTINUITY, score, report_markdown)

    return report


# ── Voice Check ───────────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/voice-check")
async def run_voice_check_endpoint(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        root_path  = await _get_root_path(db, project_id)
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        report_markdown = await run_voice_check(project_id, chapter_number, db)
        score = extract_score(report_markdown)

        _save_report_file(root_path, chapter_number, _TYPE_VOICE, report_markdown)
        report = await _insert_report(db, project_id, chapter_id, _TYPE_VOICE, score, report_markdown)

    return report


# ── Get chapter reports ───────────────────────────────────────────────────────

@router.get("/{project_id}/chapters/{chapter_number}/reports")
async def get_chapter_reports(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        async with db.execute(
            """SELECT id, project_id, chapter_id, report_type, score, report_markdown, created_at
                 FROM qa_reports
                WHERE project_id = ? AND chapter_id = ?
                ORDER BY id DESC""",
            (project_id, chapter_id),
        ) as cur:
            rows = await cur.fetchall()

    return [_row_to_report(r) for r in rows]


# ── Get all QA reports for project ───────────────────────────────────────────

@router.get("/{project_id}/qa")
async def get_project_qa(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            """SELECT id, project_id, chapter_id, report_type, score, report_markdown, created_at
                 FROM qa_reports
                WHERE project_id = ?
                ORDER BY id DESC""",
            (project_id,),
        ) as cur:
            rows = await cur.fetchall()

    return [_row_to_report(r) for r in rows]
