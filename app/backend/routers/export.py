import os
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from models import ExportOptions, ExportResult, ExportStatus

router = APIRouter(prefix="/projects", tags=["export"])

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_BACKEND_DIR)))
PROJECTS_DIR = os.path.join(_REPO_ROOT, "projects")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_words(text: str) -> int:
    return len(text.split())


@router.post("/{project_id}/export", response_model=ExportResult)
async def export_manuscript(project_id: int, options: ExportOptions = None):
    if options is None:
        options = ExportOptions()

    async with aiosqlite.connect(get_db_path()) as db:
        # Fetch project
        async with db.execute(
            "SELECT id, slug, title, root_path FROM projects WHERE id = ?",
            (project_id,),
        ) as cur:
            proj = await cur.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")

        proj_title = proj[2]
        root_path = proj[3]

        # Fetch approved chapters ordered by chapter_number
        async with db.execute(
            """SELECT chapter_number, title, final_path, summary_path
               FROM chapters
               WHERE project_id = ? AND status = 'approved'
               ORDER BY chapter_number ASC""",
            (project_id,),
        ) as cur:
            rows = await cur.fetchall()

        # Update project updated_at
        await db.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (_now(), project_id),
        )
        await db.commit()

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No approved chapters found. Approve at least one chapter before exporting.",
        )

    parts = [f"# {proj_title}", ""]
    total_words = 0
    chapters_included = []

    for chapter_number, title, final_path, summary_path in rows:
        # Read prose
        prose = ""
        if final_path:
            abs_final = os.path.join(root_path, final_path) if not os.path.isabs(final_path) else final_path
            if os.path.isfile(abs_final):
                try:
                    with open(abs_final, "r", encoding="utf-8", errors="replace") as f:
                        prose = f.read().strip()
                except OSError:
                    prose = ""

        if not prose:
            # Skip chapters whose file is missing or empty
            continue

        chapters_included.append(chapter_number)
        total_words += _count_words(prose)

        parts.append("---")
        parts.append("")

        if options.include_chapter_headings:
            heading = f"## Chapter {chapter_number}"
            if title:
                heading += f" — {title}"
            parts.append(heading)
            parts.append("")

        parts.append(prose)
        parts.append("")

        if options.include_summaries and summary_path:
            abs_summary = os.path.join(root_path, summary_path) if not os.path.isabs(summary_path) else summary_path
            if os.path.isfile(abs_summary):
                try:
                    with open(abs_summary, "r", encoding="utf-8", errors="replace") as f:
                        summary_text = f.read().strip()
                    if summary_text:
                        parts.append(f"> **Summary:** {summary_text}")
                        parts.append("")
                except OSError:
                    pass

    if not chapters_included:
        raise HTTPException(
            status_code=422,
            detail="Approved chapters were found but their files are missing.",
        )

    manuscript = "\n".join(parts)

    # Write to exports/manuscript.md
    exports_dir = os.path.join(root_path, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    out_path = os.path.join(exports_dir, "manuscript.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(manuscript)

    return ExportResult(
        path="exports/manuscript.md",
        absolute_path=out_path,
        chapter_count=len(chapters_included),
        word_count=total_words,
        chapters_included=chapters_included,
    )


@router.get("/{project_id}/export/status", response_model=ExportStatus)
async def export_status(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT id, root_path FROM projects WHERE id = ?",
            (project_id,),
        ) as cur:
            proj = await cur.fetchone()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")

        root_path = proj[1]

        async with db.execute(
            "SELECT COUNT(*) FROM chapters WHERE project_id = ? AND status = 'approved'",
            (project_id,),
        ) as cur:
            approved_count = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM chapters WHERE project_id = ?",
            (project_id,),
        ) as cur:
            total_count = (await cur.fetchone())[0]

    out_path = os.path.join(root_path, "exports", "manuscript.md")

    if not os.path.isfile(out_path):
        return ExportStatus(
            exists=False,
            approved_chapters=approved_count,
            total_chapters=total_count,
        )

    stat = os.stat(out_path)
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    with open(out_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    word_count = _count_words(text)

    return ExportStatus(
        exists=True,
        path="exports/manuscript.md",
        absolute_path=out_path,
        word_count=word_count,
        modified_at=modified_at,
        approved_chapters=approved_count,
        total_chapters=total_count,
    )
