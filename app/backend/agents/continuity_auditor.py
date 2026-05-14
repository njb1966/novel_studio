"""
Continuity Auditor — AI-assisted consistency check.

run_continuity_check(project_id, chapter_number, db) -> markdown report string
"""

import os

from llm_client import LLMClient

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


_SYSTEM_PROMPT = (
    "You are a continuity editor for a novel. "
    "Your job is to flag any continuity errors in this chapter draft."
)

_USER_TEMPLATE = """\
ESTABLISHED CONTINUITY FACTS:
{continuity_facts}

CHAPTER DRAFT:
{draft_text}

TASK:
1. Identify any facts in this chapter that contradict established continuity.
2. Identify any character states, object locations, or injuries that appear inconsistent.
3. List NEW facts introduced in this chapter that should be logged.

Output three sections:
## Contradictions
(list each with: what the draft says vs. what continuity says)

## Inconsistencies
(list each with: what seems off and why)

## New Facts to Log
(list each candidate fact with: type, subject, fact)

End with: SCORE: [number 0-100, where 100 = no issues]
"""


async def run_continuity_check(project_id: int, chapter_number: int, db) -> str:
    """Run continuity check on a chapter draft. Returns markdown report string."""

    # ── Fetch project root path ──────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        proj_row = await cur.fetchone()
    if not proj_row:
        return f"# Continuity Check — Chapter {chapter_number}\n\nError: project not found.\n"

    root_path = proj_row[0]

    # ── Read draft file ──────────────────────────────────────────────────────
    draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
    draft_path = os.path.join(root_path, "chapters", draft_filename)

    if not os.path.isfile(draft_path):
        return (
            f"# Continuity Check — Chapter {chapter_number}\n\n"
            "Error: draft file not found. Generate a draft first.\n"
        )

    with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
        draft_text = f.read()

    # ── Fetch last 30 continuity facts ───────────────────────────────────────
    async with db.execute(
        """SELECT fact_type, subject, fact
             FROM continuity_facts
            WHERE project_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 30""",
        (project_id,),
    ) as cur:
        fact_rows = await cur.fetchall()

    if fact_rows:
        fact_lines = [
            f"- [{row[0]}] {(row[1] + ': ') if row[1] else ''}{row[2]}"
            for row in reversed(fact_rows)
        ]
        continuity_facts = "\n".join(fact_lines)
    else:
        continuity_facts = "(No continuity facts recorded yet.)"

    # ── Also pull active injury / death facts for prominence ────────────────
    async with db.execute(
        """SELECT fact_type, subject, fact
             FROM continuity_facts
            WHERE project_id = ? AND status = 'active'
              AND fact_type IN ('injury', 'death')
            ORDER BY id DESC""",
        (project_id,),
    ) as cur:
        state_rows = await cur.fetchall()

    if state_rows:
        state_lines = [
            f"- [{row[0]}] {(row[1] + ': ') if row[1] else ''}{row[2]}"
            for row in state_rows
        ]
        active_states = "\nACTIVE INJURIES / DEATHS:\n" + "\n".join(state_lines)
        continuity_facts = continuity_facts + "\n" + active_states

    # ── Build prompt and call LLM ────────────────────────────────────────────
    user_prompt = _USER_TEMPLATE.format(
        continuity_facts=continuity_facts,
        draft_text=draft_text,
    )

    client = LLMClient()
    return client.complete(_SYSTEM_PROMPT, user_prompt)
