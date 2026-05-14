import os
import json
import shutil
import re
from datetime import datetime, timezone
from typing import List

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from models import Project, ProjectCreate, ProjectImport, Chapter

router = APIRouter(prefix="/projects", tags=["projects"])

# Repo root is two levels up from app/backend/
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_BACKEND_DIR)))
PROJECTS_DIR = os.path.join(_REPO_ROOT, "projects")
TEMPLATES_DIR = os.path.join(_REPO_ROOT, "templates")

PROJECT_SUBDIRS = ["chapters", "summaries", "qa", "revisions", "exports"]


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_project(row, actual_word_count: int = 0) -> Project:
    return Project(
        id=row[0],
        slug=row[1],
        title=row[2],
        created_at=row[3],
        updated_at=row[4],
        root_path=row[5],
        target_word_count=row[6],
        actual_word_count=actual_word_count,
        pov=row[7] or "",
        tense=row[8] or "",
        genre=row[9] or "",
        status=row[10] or "active",
    )


def _extract_title_from_markdown(folder_path: str) -> str | None:
    """Try to read NOVEL_SPEC.md (or any .md) and pull a title."""
    candidates = ["NOVEL_SPEC.md", "README.md"]
    for fname in candidates:
        fpath = os.path.join(folder_path, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        # Match "# Title: Some Name" or just "# Some Name"
                        m = re.match(r"^#+\s+Title:\s*(.+)$", line, re.IGNORECASE)
                        if m:
                            return m.group(1).strip()
                        m = re.match(r"^#\s+(.+)$", line)
                        if m:
                            return m.group(1).strip()
            except OSError:
                continue
    return None


@router.get("", response_model=List[Project])
async def list_projects():
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            """SELECT p.id, p.slug, p.title, p.created_at, p.updated_at, p.root_path,
                      p.target_word_count, p.pov, p.tense, p.genre, p.status,
                      COALESCE(SUM(CASE WHEN c.status = 'approved' THEN c.actual_word_count ELSE 0 END), 0)
               FROM projects p
               LEFT JOIN chapters c ON c.project_id = p.id
               GROUP BY p.id
               ORDER BY p.created_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()
    return [_row_to_project(r, actual_word_count=r[11]) for r in rows]


@router.post("", response_model=Project, status_code=201)
async def create_project(data: ProjectCreate):
    slug = _slugify(data.title)
    if not slug:
        raise HTTPException(status_code=400, detail="Title produces an empty slug.")

    project_path = os.path.join(PROJECTS_DIR, slug)

    # Check for slug collision in DB
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute("SELECT id FROM projects WHERE slug = ?", (slug,)) as cur:
            existing = await cur.fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=f"A project with slug '{slug}' already exists.")

    # Create folder structure
    os.makedirs(project_path, exist_ok=True)
    for subdir in PROJECT_SUBDIRS:
        os.makedirs(os.path.join(project_path, subdir), exist_ok=True)

    # Copy templates if available
    if os.path.isdir(TEMPLATES_DIR):
        for fname in os.listdir(TEMPLATES_DIR):
            src = os.path.join(TEMPLATES_DIR, fname)
            if os.path.isfile(src):
                dst = os.path.join(project_path, fname)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)

    now = _now()

    # Write project.json
    project_meta = {
        "slug": slug,
        "title": data.title,
        "created_at": now,
        "updated_at": now,
        "target_word_count": data.target_word_count,
        "pov": data.pov,
        "tense": data.tense,
        "genre": data.genre,
        "status": "active",
    }
    with open(os.path.join(project_path, "project.json"), "w", encoding="utf-8") as f:
        json.dump(project_meta, f, indent=2)

    # Insert into DB
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "INSERT INTO projects (slug, title, created_at, updated_at, root_path, "
            "target_word_count, pov, tense, genre, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (slug, data.title, now, now, project_path,
             data.target_word_count, data.pov, data.tense, data.genre, "active"),
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cur:
            row = await cur.fetchone()
            project_id = row[0]

    return Project(
        id=project_id,
        slug=slug,
        title=data.title,
        created_at=now,
        updated_at=now,
        root_path=project_path,
        target_word_count=data.target_word_count,
        pov=data.pov,
        tense=data.tense,
        genre=data.genre,
        status="active",
    )


@router.post("/import", response_model=Project, status_code=201)
async def import_project(data: ProjectImport):
    src_path = os.path.abspath(os.path.expanduser(data.folder_path))
    if not os.path.isdir(src_path):
        raise HTTPException(status_code=400, detail=f"Folder not found: {src_path}")

    title = _extract_title_from_markdown(src_path)
    if not title:
        # Fall back to folder name
        title = os.path.basename(src_path.rstrip("/"))

    slug = _slugify(title)
    if not slug:
        raise HTTPException(status_code=400, detail="Could not derive a valid slug from the folder.")

    # Check collision
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute("SELECT id FROM projects WHERE slug = ?", (slug,)) as cur:
            existing = await cur.fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=f"A project with slug '{slug}' already exists.")

    dest_path = os.path.join(PROJECTS_DIR, slug)
    os.makedirs(dest_path, exist_ok=True)
    for subdir in PROJECT_SUBDIRS:
        os.makedirs(os.path.join(dest_path, subdir), exist_ok=True)

    # Copy source files into dest
    for fname in os.listdir(src_path):
        src_file = os.path.join(src_path, fname)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, os.path.join(dest_path, fname))

    now = _now()

    project_meta = {
        "slug": slug,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "target_word_count": 80000,
        "pov": "",
        "tense": "",
        "genre": "",
        "status": "active",
    }
    with open(os.path.join(dest_path, "project.json"), "w", encoding="utf-8") as f:
        json.dump(project_meta, f, indent=2)

    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "INSERT INTO projects (slug, title, created_at, updated_at, root_path, "
            "target_word_count, pov, tense, genre, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (slug, title, now, now, dest_path, 80000, "", "", "", "active"),
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cur:
            row = await cur.fetchone()
            project_id = row[0]

    return Project(
        id=project_id,
        slug=slug,
        title=title,
        created_at=now,
        updated_at=now,
        root_path=dest_path,
        target_word_count=80000,
        pov="",
        tense="",
        genre="",
        status="active",
    )


def _read_summary_snippet(root_path: str, summary_path: str) -> str:
    """Return the first sentence of a summary file, truncated to 80 chars."""
    if not summary_path:
        return ""
    abs_path = os.path.join(root_path, summary_path)
    if not os.path.isfile(abs_path):
        return ""
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read().strip()
        # First sentence = text up to the first '.' or the whole string
        dot_idx = text.find(".")
        first_sentence = text[: dot_idx + 1] if dot_idx != -1 else text
        if len(first_sentence) > 80:
            return first_sentence[:77] + "..."
        return first_sentence
    except OSError:
        return ""


@router.get("/{project_id}/chapters", response_model=List[Chapter])
async def list_chapters(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute("SELECT id, root_path FROM projects WHERE id = ?", (project_id,)) as cur:
            proj_row = await cur.fetchone()
            if not proj_row:
                raise HTTPException(status_code=404, detail="Project not found.")
            root_path = proj_row[1]
        async with db.execute(
            """SELECT id, project_id, chapter_number, title, pov_character,
                      status, target_word_count, actual_word_count,
                      outline_goal, outline_conflict, outline_revelation,
                      outline_notes, draft_path, final_path, summary_path,
                      created_at, updated_at
               FROM chapters
               WHERE project_id = ?
               ORDER BY chapter_number ASC""",
            (project_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [
        Chapter(
            id=r[0], project_id=r[1], chapter_number=r[2], title=r[3] or "",
            pov_character=r[4] or "", status=r[5] or "draft",
            target_word_count=r[6] or 3000, actual_word_count=r[7] or 0,
            outline_goal=r[8] or "", outline_conflict=r[9] or "",
            outline_revelation=r[10] or "", outline_notes=r[11] or "",
            draft_path=r[12] or "", final_path=r[13] or "",
            summary_path=r[14] or "",
            summary_snippet=_read_summary_snippet(root_path, r[14] or ""),
            created_at=r[15] or "",
            updated_at=r[16] or "",
        )
        for r in rows
    ]


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT id, slug, title, created_at, updated_at, root_path, "
            "target_word_count, pov, tense, genre, status FROM projects WHERE id = ?",
            (project_id,),
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _row_to_project(row)
