"""
Voice Auditor — AI-assisted POV voice consistency check.

run_voice_check(project_id, chapter_number, db) -> markdown report string
"""

import os

from llm_client import LLMClient

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


_SYSTEM_PROMPT = (
    "You are a voice editor for literary fiction. "
    "Your job is to assess whether the prose matches the established voice "
    "profile for this POV character."
)

_USER_TEMPLATE = """\
POV CHARACTER VOICE PROFILE:
{voice_description}

SAMPLE INTERNAL VOICE:
{sample_internal_voice}

WRITING REFINER STYLE GUIDE:
{writing_refiner}

CHAPTER DRAFT:
{draft_text}

TASK:
Assess the chapter draft for:
1. Consistency with the POV character's established voice
2. Adherence to the writing style guide
3. Any passages that feel generic or AI-like rather than character-specific
4. Any vocabulary or register violations

Output:
## Voice Consistency
(overall assessment, 2-3 sentences)

## Issues
(list specific passages with line references where voice breaks down)

## Strengths
(list 2-3 passages where the voice is working well)

End with: SCORE: [number 0-100]
"""


def _read_file_if_exists(path: str) -> str:
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


async def run_voice_check(project_id: int, chapter_number: int, db) -> str:
    """Run voice check on a chapter draft. Returns markdown report string."""

    # ── Fetch project root path ──────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        proj_row = await cur.fetchone()
    if not proj_row:
        return f"# Voice Check — Chapter {chapter_number}\n\nError: project not found.\n"

    root_path = proj_row[0]

    # ── Fetch chapter's POV character name ───────────────────────────────────
    async with db.execute(
        "SELECT pov_character FROM chapters WHERE project_id = ? AND chapter_number = ?",
        (project_id, chapter_number),
    ) as cur:
        ch_row = await cur.fetchone()

    if not ch_row:
        return f"# Voice Check — Chapter {chapter_number}\n\nError: chapter not found.\n"

    pov_character_name = ch_row[0] or ""

    # ── Read draft file ──────────────────────────────────────────────────────
    draft_filename = f"CH{chapter_number:03d}_DRAFT.md"
    draft_path = os.path.join(root_path, "chapters", draft_filename)

    if not os.path.isfile(draft_path):
        return (
            f"# Voice Check — Chapter {chapter_number}\n\n"
            "Error: draft file not found. Generate a draft first.\n"
        )

    with open(draft_path, "r", encoding="utf-8", errors="replace") as f:
        draft_text = f.read()

    # ── Fetch character voice fields from DB ─────────────────────────────────
    voice_description = ""
    sample_internal_voice = ""

    if pov_character_name:
        async with db.execute(
            """SELECT voice_description, sample_internal_voice
                 FROM characters
                WHERE project_id = ? AND name = ?""",
            (project_id, pov_character_name),
        ) as cur:
            char_row = await cur.fetchone()

        if char_row:
            voice_description = char_row[0] or ""
            sample_internal_voice = char_row[1] or ""

    if not voice_description:
        voice_description = "(No voice profile recorded for this character.)"
    if not sample_internal_voice:
        sample_internal_voice = "(No sample provided.)"

    # ── Read writing-refiner style guide ────────────────────────────────────
    writing_refiner = ""
    for candidate in ("writing-refiner.md", "writing_refiner.md",
                      "WRITING_REFINER.md", "WRITING-REFINER.md"):
        candidate_path = os.path.join(root_path, candidate)
        writing_refiner = _read_file_if_exists(candidate_path)
        if writing_refiner:
            break

    if not writing_refiner:
        writing_refiner = "(No writing refiner guide found.)"

    # ── Build prompt and call LLM ────────────────────────────────────────────
    user_prompt = _USER_TEMPLATE.format(
        voice_description=voice_description,
        sample_internal_voice=sample_internal_voice,
        writing_refiner=writing_refiner,
        draft_text=draft_text,
    )

    client = LLMClient()
    return client.complete(_SYSTEM_PROMPT, user_prompt)
