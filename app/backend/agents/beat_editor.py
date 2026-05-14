"""
Beat Editor — AI-assisted structural check.

run_beat_check(project_id, chapter_number, db) -> markdown report string
"""

import os

import aiosqlite

from database import get_db_path
from llm_client import LLMClient

# Path helper — mirrors pattern in other routers/agents
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_BACKEND_DIR))
PROJECTS_DIR = os.path.join(_REPO_ROOT, "projects")


_SYSTEM_PROMPT = (
    "You are a structural editor reviewing a novel chapter draft. "
    "Your job is to verify whether the chapter delivers its promised beats."
)

_USER_TEMPLATE = """\
CHAPTER OUTLINE:
Goal: {outline_goal}
Conflict: {outline_conflict}
Revelation: {outline_revelation}
Notes: {outline_notes}

CHAPTER DRAFT:
{draft_text}

TASK:
Check whether this chapter:
1. Delivers the stated goal
2. Contains the stated conflict
3. Delivers the revelation or moves toward it
4. Has a clear scene structure (opening/middle/end)
5. Does not drift from the POV character

For each point: PASS, PARTIAL, or FAIL with a one-sentence explanation.
Then give an overall score 0-100.
End with: SCORE: [number]
"""


async def run_beat_check(project_id: int, chapter_number: int, db) -> str:
    """Run beat check on a chapter draft. Returns markdown report string."""

    # ── Fetch project root path ──────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        proj_row = await cur.fetchone()
    if not proj_row:
        return f"# Beat Check — Chapter {chapter_number}\n\nError: project not found.\n"

    root_path = proj_row[0]

    # ── Fetch chapter outline fields ─────────────────────────────────────────
    async with db.execute(
        """SELECT outline_goal, outline_conflict, outline_revelation, outline_notes
             FROM chapters
            WHERE project_id = ? AND chapter_number = ?""",
        (project_id, chapter_number),
    ) as cur:
        ch_row = await cur.fetchone()

    if not ch_row:
        return f"# Beat Check — Chapter {chapter_number}\n\nError: chapter not found.\n"

    outline_goal, outline_conflict, outline_revelation, outline_notes = ch_row

    # ── Read draft file ──────────────────────────────────────────────────────
    draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
    draft_path = os.path.join(root_path, "chapters", draft_filename)

    if not os.path.isfile(draft_path):
        return (
            f"# Beat Check — Chapter {chapter_number}\n\n"
            "Error: draft file not found. Generate a draft first.\n"
        )

    with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
        draft_text = f.read()

    # ── Build prompt and call LLM ────────────────────────────────────────────
    user_prompt = _USER_TEMPLATE.format(
        outline_goal=outline_goal or "(not specified)",
        outline_conflict=outline_conflict or "(not specified)",
        outline_revelation=outline_revelation or "(not specified)",
        outline_notes=outline_notes or "(none)",
        draft_text=draft_text,
    )

    client = LLMClient()
    return client.complete(_SYSTEM_PROMPT, user_prompt)
