"""
Scaffold endpoint — generates foundational project documents from OUTLINE.md.

POST /projects/{project_id}/scaffold
"""

import os
from pydantic import BaseModel
import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from agents.scaffold_agent import scaffold_documents

router = APIRouter(prefix="/projects", tags=["scaffold"])

_UPPERCASE = {
    "outline.md":         "OUTLINE.md",
    "novel_spec.md":      "NOVEL_SPEC.md",
    "character_bible.md": "CHARACTER_BIBLE.md",
    "world_bible.md":     "WORLD_BIBLE.md",
    "continuity_log.md":  "CONTINUITY_LOG.md",
}

SCAFFOLD_TARGETS = [
    "novel_spec.md",
    "character_bible.md",
    "world_bible.md",
    "continuity_log.md",
]


def _read(root_path: str, filename: str) -> str:
    for name in (filename, _UPPERCASE.get(filename, "")):
        if name:
            path = os.path.join(root_path, name)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
    return ""


def _write_path(root_path: str, filename: str) -> str:
    """Return the path to write to: existing uppercase file if present, else lowercase."""
    upper = _UPPERCASE.get(filename)
    if upper:
        p = os.path.join(root_path, upper)
        if os.path.isfile(p):
            return p
    return os.path.join(root_path, filename)


class ScaffoldRequest(BaseModel):
    force: bool = False


@router.post("/{project_id}/scaffold")
async def scaffold_project(project_id: int, body: ScaffoldRequest = ScaffoldRequest()):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT root_path, title, genre, pov, tense, target_word_count "
            "FROM projects WHERE id = ?",
            (project_id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")

    root_path, title, genre, pov, tense, target_word_count = row

    outline = _read(root_path, "outline.md")
    if not outline.strip():
        raise HTTPException(
            status_code=400,
            detail="OUTLINE.md is empty or missing. Add your outline before scaffolding.",
        )

    skipped = []
    to_generate = []
    for fname in SCAFFOLD_TARGETS:
        if not body.force and _read(root_path, fname).strip():
            skipped.append(fname)
        else:
            to_generate.append(fname)

    if not to_generate:
        return {
            "generated": [],
            "skipped": skipped,
            "errors": [],
            "message": "All documents already exist. Pass force=true to overwrite.",
        }

    docs = await scaffold_documents(
        title=title,
        genre=genre or "",
        pov=pov or "",
        tense=tense or "",
        target_word_count=target_word_count or 80000,
        outline=outline,
        targets=set(to_generate),
    )

    generated = []
    errors = []
    for fname, content in docs.items():
        try:
            with open(_write_path(root_path, fname), "w", encoding="utf-8") as f:
                f.write(content)
            generated.append(fname)
        except OSError as e:
            errors.append({"file": fname, "error": str(e)})

    return {
        "generated": generated,
        "skipped": skipped,
        "errors": errors,
    }


@router.get("/{project_id}/scaffold/status")
async def scaffold_status(project_id: int):
    """Return which scaffold documents exist and have content."""
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT root_path FROM projects WHERE id = ?", (project_id,)
        ) as cur:
            row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")

    root_path = row[0]
    outline = _read(root_path, "outline.md")

    files = {}
    for fname in SCAFFOLD_TARGETS:
        content = _read(root_path, fname)
        files[fname] = bool(content.strip())

    return {
        "has_outline": bool(outline.strip()),
        "files": files,
    }
