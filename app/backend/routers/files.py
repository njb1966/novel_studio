import os
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from models import FileContent

router = APIRouter(prefix="/projects", tags=["files"])

ALLOWED_FILENAMES = {
    "novel_spec.md",
    "outline.md",
    "character_bible.md",
    "world_bible.md",
    "continuity_log.md",
    "prohibited.yaml",
    "prompt_library.md",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_project_root(project_id: int) -> str:
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT root_path FROM projects WHERE id = ?", (project_id,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    return row[0]


@router.get("/{project_id}/files/{filename}")
async def get_file(project_id: int, filename: str):
    if filename not in ALLOWED_FILENAMES:
        raise HTTPException(status_code=400, detail=f"Filename '{filename}' is not permitted.")

    root_path = await _get_project_root(project_id)
    file_path = os.path.join(root_path, filename)

    if not os.path.isfile(file_path):
        return {"content": ""}

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {e}")

    return {"content": content}


@router.put("/{project_id}/files/{filename}")
async def save_file(project_id: int, filename: str, body: FileContent):
    if filename not in ALLOWED_FILENAMES:
        raise HTTPException(status_code=400, detail=f"Filename '{filename}' is not permitted.")

    root_path = await _get_project_root(project_id)
    file_path = os.path.join(root_path, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(body.content)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not write file: {e}")

    now = _now()
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id)
        )
        await db.commit()

    return {"ok": True}
