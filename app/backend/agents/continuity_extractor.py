"""
Continuity Extractor — extract new continuity facts from a chapter draft.

extract_continuity_facts(project_id, chapter_number, db) -> list[dict]

Each dict has keys: type, subject, fact
"""

import json
import os

from llm_client import LLMClient

_SYSTEM_PROMPT = (
    "You are a continuity tracker for a novel. "
    "Extract new facts introduced in this chapter that should be logged for future reference."
)

_USER_TEMPLATE = """\
EXISTING CONTINUITY FACTS (do not re-extract these):
{existing_facts}

CHAPTER {chapter_number} DRAFT:
{draft_text}

TASK:
Extract NEW facts introduced in this chapter. For each fact provide:
- type: one of: character_state, object_location, injury, death, promise, mystery, seed, timeline, world_fact, relationship, other
- subject: the character, object, or topic the fact is about
- fact: a concise one-sentence statement of the fact

Return ONLY a JSON array. No other text. Example:
[
  {{"type": "injury", "subject": "Marcus", "fact": "Marcus suffered a knife wound to the left forearm in the tavern fight."}},
  {{"type": "object_location", "subject": "silver key", "fact": "The silver key is now hidden under the floorboard in Elena's room."}}
]

If there are no new facts to log, return an empty array: []
"""


async def extract_continuity_facts(
    project_id: int, chapter_number: int, db
) -> list[dict]:
    """Extract new continuity facts from a chapter draft.

    Returns a list of dicts with keys: type, subject, fact.
    Returns [] on any error.
    """

    # ── Fetch project root path ──────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        proj_row = await cur.fetchone()
    if not proj_row:
        return []

    root_path = proj_row[0]

    # ── Read draft file ──────────────────────────────────────────────────────
    draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
    draft_path = os.path.join(root_path, "chapters", draft_filename)

    if not os.path.isfile(draft_path):
        return []

    with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
        draft_text = f.read()

    # ── Fetch last 30 active continuity facts for context ────────────────────
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
        existing_facts = "\n".join(fact_lines)
    else:
        existing_facts = "(No continuity facts recorded yet.)"

    # ── Build prompt and call LLM ────────────────────────────────────────────
    user_prompt = _USER_TEMPLATE.format(
        existing_facts=existing_facts,
        chapter_number=chapter_number,
        draft_text=draft_text,
    )

    client = LLMClient()
    raw = client.complete(_SYSTEM_PROMPT, user_prompt)

    # ── Parse JSON response ──────────────────────────────────────────────────
    try:
        # Strip markdown code fences if the LLM wrapped it
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # drop first and last fence lines
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()

        facts = json.loads(text)
        if not isinstance(facts, list):
            return []

        # Normalise and validate each item
        result = []
        for item in facts:
            if not isinstance(item, dict):
                continue
            fact_type = str(item.get("type", "other")).strip()
            subject = str(item.get("subject", "")).strip()
            fact = str(item.get("fact", "")).strip()
            if fact:
                result.append({"type": fact_type, "subject": subject, "fact": fact})

        return result

    except (json.JSONDecodeError, TypeError, ValueError):
        return []
