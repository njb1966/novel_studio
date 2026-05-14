"""
Chapter pipeline endpoints.

POST /projects/{project_id}/chapters/{chapter_number}/generate
GET  /projects/{project_id}/chapters/{chapter_number}
GET  /projects/{project_id}/chapters/{chapter_number}/draft
PUT  /projects/{project_id}/chapters/{chapter_number}/draft
POST /projects/{project_id}/chapters/{chapter_number}/summary
GET  /projects/{project_id}/chapters/{chapter_number}/summary
POST /projects/{project_id}/chapters/{chapter_number}/approve
"""

import os
import shutil
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db_path
from agents.draft_agent import generate_draft
from agents.summary_agent import generate_summary

router = APIRouter(prefix="/projects", tags=["chapters"])

# Path helpers — mirrors the layout used in routers/projects.py
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_BACKEND_DIR)))
PROJECTS_DIR = os.path.join(_REPO_ROOT, "projects")


class DraftContent(BaseModel):
    content: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _word_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


async def _get_chapter_row(db, project_id: int, chapter_number: int):
    """Return the full chapter row or None."""
    async with db.execute(
        """SELECT id, project_id, chapter_number, title, pov_character,
                  status, target_word_count, actual_word_count,
                  outline_goal, outline_conflict, outline_revelation,
                  outline_notes, draft_path, final_path, summary_path,
                  created_at, updated_at
             FROM chapters
            WHERE project_id = ? AND chapter_number = ?""",
        (project_id, chapter_number),
    ) as cur:
        return await cur.fetchone()


async def _get_root_path(db, project_id: int) -> str:
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    return row[0]


# ── Generate draft ───────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/generate")
async def generate_chapter_draft(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        # Verify chapter exists
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")

        root_path = await _get_root_path(db, project_id)

        # Generate prose (this blocks for 15–60 seconds)
        prose = await generate_draft(project_id, chapter_number, db)

    # Save draft file
    chapters_dir = os.path.join(root_path, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
    draft_abs_path = os.path.join(chapters_dir, draft_filename)
    with open(draft_abs_path, "w", encoding="utf-8") as f:
        f.write(prose)

    draft_rel_path = f"chapters/{draft_filename}"
    wc = _word_count(prose)
    now = _now()

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            """UPDATE chapters
                  SET draft_path = ?,
                      actual_word_count = ?,
                      status = 'draft',
                      updated_at = ?
                WHERE project_id = ? AND chapter_number = ?""",
            (draft_rel_path, wc, now, project_id, chapter_number),
        )
        await db.commit()

    return {
        "chapter_number": chapter_number,
        "draft_path":     draft_rel_path,
        "word_count":     wc,
        "content":        prose,
    }


# ── Get single chapter detail ────────────────────────────────────────────────

@router.get("/{project_id}/chapters/{chapter_number}")
async def get_chapter(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        root_path = await _get_root_path(db, project_id)

    (
        ch_id, ch_project_id, ch_number, ch_title, pov_character,
        status, target_wc, actual_wc,
        outline_goal, outline_conflict, outline_revelation, outline_notes,
        draft_path, final_path, summary_path,
        created_at, updated_at,
    ) = ch_row

    draft_content = ""
    if draft_path:
        abs_draft = os.path.join(root_path, draft_path)
        if os.path.isfile(abs_draft):
            with open(abs_draft, "r", encoding="utf-8", errors="replace") as f:
                draft_content = f.read()

    return {
        "id":                ch_id,
        "project_id":        ch_project_id,
        "chapter_number":    ch_number,
        "title":             ch_title or "",
        "pov_character":     pov_character or "",
        "status":            status or "draft",
        "target_word_count": target_wc or 3000,
        "actual_word_count": actual_wc or 0,
        "outline_goal":      outline_goal or "",
        "outline_conflict":  outline_conflict or "",
        "outline_revelation": outline_revelation or "",
        "outline_notes":     outline_notes or "",
        "draft_path":        draft_path or "",
        "final_path":        final_path or "",
        "summary_path":      summary_path or "",
        "created_at":        created_at or "",
        "updated_at":        updated_at or "",
        "draft_content":     draft_content,
    }


# ── Get draft content ────────────────────────────────────────────────────────

@router.get("/{project_id}/chapters/{chapter_number}/draft")
async def get_chapter_draft(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        root_path = await _get_root_path(db, project_id)

    draft_path = ch_row[12]  # draft_path column index

    if not draft_path:
        return {"content": ""}

    abs_draft = os.path.join(root_path, draft_path)
    if not os.path.isfile(abs_draft):
        return {"content": ""}

    with open(abs_draft, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return {"content": content}


# ── Save draft content ───────────────────────────────────────────────────────

@router.put("/{project_id}/chapters/{chapter_number}/draft")
async def save_chapter_draft(project_id: int, chapter_number: int, body: DraftContent):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        root_path = await _get_root_path(db, project_id)

        draft_path = ch_row[12]

        # If no draft_path yet, create one
        if not draft_path:
            draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
            draft_path = f"chapters/{draft_filename}"

        abs_draft = os.path.join(root_path, draft_path)
        os.makedirs(os.path.dirname(abs_draft), exist_ok=True)

        with open(abs_draft, "w", encoding="utf-8") as f:
            f.write(body.content)

        wc = _word_count(body.content)
        now = _now()

        await db.execute(
            """UPDATE chapters
                  SET draft_path = ?,
                      actual_word_count = ?,
                      updated_at = ?
                WHERE project_id = ? AND chapter_number = ?""",
            (draft_path, wc, now, project_id, chapter_number),
        )
        await db.commit()

    return {"draft_path": draft_path, "word_count": wc}


# ── Generate summary ─────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/summary")
async def generate_chapter_summary(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        if not ch_row[12]:  # draft_path
            raise HTTPException(status_code=400, detail="Chapter has no draft. Generate a draft first.")

        root_path = await _get_root_path(db, project_id)

        summary_text = await generate_summary(project_id, chapter_number, db)

    # Write summary file
    summaries_dir = os.path.join(root_path, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)

    summary_filename = f"CH{chapter_number:03d}_SUMMARY.md"
    abs_summary_path = os.path.join(summaries_dir, summary_filename)
    with open(abs_summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    summary_rel_path = f"summaries/{summary_filename}"
    now = _now()

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            """UPDATE chapters
                  SET summary_path = ?,
                      updated_at = ?
                WHERE project_id = ? AND chapter_number = ?""",
            (summary_rel_path, now, project_id, chapter_number),
        )
        await db.commit()

    return {
        "chapter_number": chapter_number,
        "summary":        summary_text,
        "summary_path":   summary_rel_path,
    }


# ── Get summary ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/chapters/{chapter_number}/summary")
async def get_chapter_summary(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        root_path = await _get_root_path(db, project_id)

    summary_path = ch_row[14]  # summary_path column index

    if not summary_path:
        return {"summary": ""}

    abs_summary = os.path.join(root_path, summary_path)
    if not os.path.isfile(abs_summary):
        return {"summary": ""}

    with open(abs_summary, "r", encoding="utf-8", errors="replace") as f:
        summary_text = f.read()

    return {"summary": summary_text}


# ── Approve chapter ───────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/approve")
async def approve_chapter(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        ch_row = await _get_chapter_row(db, project_id, chapter_number)
        if ch_row is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")

        draft_path = ch_row[12]
        if not draft_path:
            raise HTTPException(status_code=400, detail="Chapter has no draft to approve.")

        root_path = await _get_root_path(db, project_id)

    abs_draft = os.path.join(root_path, draft_path)
    if not os.path.isfile(abs_draft):
        raise HTTPException(status_code=400, detail="Draft file not found on disk.")

    # Copy draft → final
    final_filename = f"CH{chapter_number:03d}_FINAL.md"
    final_rel_path = f"chapters/{final_filename}"
    abs_final = os.path.join(root_path, "chapters", final_filename)
    shutil.copy2(abs_draft, abs_final)

    now = _now()

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            """UPDATE chapters
                  SET status = 'approved',
                      final_path = ?,
                      updated_at = ?
                WHERE project_id = ? AND chapter_number = ?""",
            (final_rel_path, now, project_id, chapter_number),
        )
        await db.commit()

    return {
        "chapter_number": chapter_number,
        "status":         "approved",
        "final_path":     final_rel_path,
    }
