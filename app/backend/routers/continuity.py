"""
Continuity facts endpoints.

POST   /projects/{project_id}/chapters/{chapter_number}/extract-facts
GET    /projects/{project_id}/continuity/pending
GET    /projects/{project_id}/continuity/facts
POST   /projects/{project_id}/continuity/facts/{fact_id}/approve
POST   /projects/{project_id}/continuity/facts/{fact_id}/reject
DELETE /projects/{project_id}/continuity/facts/{fact_id}
"""

import os
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from models import ContinuityFact
from agents.continuity_extractor import extract_continuity_facts

router = APIRouter(prefix="/projects", tags=["continuity"])

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_BACKEND_DIR)))


# ── Helpers ───────────────────────────────────────────────────────────────────

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


async def _get_fact(db, project_id: int, fact_id: int) -> ContinuityFact:
    async with db.execute(
        """SELECT cf.id, cf.project_id, cf.chapter_id, cf.fact_type, cf.subject,
                  cf.fact, cf.status, cf.created_at, ch.chapter_number
             FROM continuity_facts cf
             LEFT JOIN chapters ch ON ch.id = cf.chapter_id
            WHERE cf.id = ? AND cf.project_id = ?""",
        (fact_id, project_id),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Fact not found.")
    return _row_to_fact(row)


def _row_to_fact(row) -> ContinuityFact:
    return ContinuityFact(
        id=row[0],
        project_id=row[1],
        chapter_id=row[2],
        fact_type=row[3],
        subject=row[4],
        fact=row[5],
        status=row[6],
        created_at=row[7],
        chapter_number=row[8] if len(row) > 8 else None,
    )


# ── Extract facts ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/chapters/{chapter_number}/extract-facts")
async def extract_facts_endpoint(project_id: int, chapter_number: int):
    async with aiosqlite.connect(get_db_path()) as db:
        chapter_id = await _get_chapter_id(db, project_id, chapter_number)

        facts = await extract_continuity_facts(project_id, chapter_number, db)

        inserted = []
        now = _now()
        for fact in facts:
            async with db.execute(
                """INSERT INTO continuity_facts
                       (project_id, chapter_id, fact_type, subject, fact, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (
                    project_id,
                    chapter_id,
                    fact["type"],
                    fact["subject"],
                    fact["fact"],
                    now,
                ),
            ) as cur:
                row_id = cur.lastrowid

            inserted.append(
                ContinuityFact(
                    id=row_id,
                    project_id=project_id,
                    chapter_id=chapter_id,
                    fact_type=fact["type"],
                    subject=fact["subject"],
                    fact=fact["fact"],
                    status="pending",
                    created_at=now,
                    chapter_number=chapter_number,
                )
            )

        await db.commit()

    return inserted


# ── Pending facts ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/continuity/pending")
async def get_pending_facts(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            """SELECT cf.id, cf.project_id, cf.chapter_id, cf.fact_type, cf.subject,
                      cf.fact, cf.status, cf.created_at, ch.chapter_number
                 FROM continuity_facts cf
                 LEFT JOIN chapters ch ON ch.id = cf.chapter_id
                WHERE cf.project_id = ? AND cf.status = 'pending'
                ORDER BY cf.created_at ASC""",
            (project_id,),
        ) as cur:
            rows = await cur.fetchall()

    return [_row_to_fact(r) for r in rows]


# ── Active facts ──────────────────────────────────────────────────────────────

@router.get("/{project_id}/continuity/facts")
async def get_active_facts(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            """SELECT cf.id, cf.project_id, cf.chapter_id, cf.fact_type, cf.subject,
                      cf.fact, cf.status, cf.created_at, ch.chapter_number
                 FROM continuity_facts cf
                 LEFT JOIN chapters ch ON ch.id = cf.chapter_id
                WHERE cf.project_id = ? AND cf.status = 'active'
                ORDER BY cf.created_at DESC""",
            (project_id,),
        ) as cur:
            rows = await cur.fetchall()

    return [_row_to_fact(r) for r in rows]


# ── Approve ───────────────────────────────────────────────────────────────────

@router.post("/{project_id}/continuity/facts/{fact_id}/approve")
async def approve_fact(project_id: int, fact_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        fact = await _get_fact(db, project_id, fact_id)

        await db.execute(
            "UPDATE continuity_facts SET status = 'active' WHERE id = ?",
            (fact_id,),
        )
        await db.commit()

        # Reload to get updated status
        fact = await _get_fact(db, project_id, fact_id)

        # Append to continuity_log.md in the project folder
        root_path = await _get_root_path(db, project_id)

    # Accept either case variant; prefer existing uppercase if present
    log_path = os.path.join(root_path, "CONTINUITY_LOG.md")
    if not os.path.exists(log_path):
        log_path = os.path.join(root_path, "continuity_log.md")
    timestamp = _now()
    chapter_label = f"Ch {fact.chapter_number}" if fact.chapter_number else "?"

    entry = (
        f"\n## [{chapter_label}] {fact.fact_type.upper()} — {fact.subject}\n"
        f"{fact.fact}\n"
        f"_(Added: {timestamp})_\n\n---\n"
    )

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return fact


# ── Reject ────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/continuity/facts/{fact_id}/reject")
async def reject_fact(project_id: int, fact_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        # Verify it exists and belongs to project
        await _get_fact(db, project_id, fact_id)

        await db.execute(
            "UPDATE continuity_facts SET status = 'rejected' WHERE id = ?",
            (fact_id,),
        )
        await db.commit()

        fact = await _get_fact(db, project_id, fact_id)

    return fact


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}/continuity/facts/{fact_id}")
async def delete_fact(project_id: int, fact_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        fact = await _get_fact(db, project_id, fact_id)

        if fact.status == "active":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete an active fact. Reject it first.",
            )

        await db.execute(
            "DELETE FROM continuity_facts WHERE id = ?",
            (fact_id,),
        )
        await db.commit()

    return {"deleted": fact_id}
