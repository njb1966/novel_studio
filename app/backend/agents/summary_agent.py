"""
Summary agent — generates a 3-sentence chapter summary for use as context
in future chapter generation.
"""

import os

from llm_client import LLMClient


async def generate_summary(project_id: int, chapter_number: int, db) -> str:
    """
    Read the chapter draft and outline data, call the LLM, and return the
    3-sentence summary text.  Does NOT write any files or update the DB —
    that is the caller's responsibility.
    """
    # ── Fetch chapter row ────────────────────────────────────────────────────
    async with db.execute(
        """SELECT title, outline_goal, outline_revelation, draft_path, project_id
             FROM chapters
            WHERE project_id = ? AND chapter_number = ?""",
        (project_id, chapter_number),
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        raise ValueError(f"Chapter {chapter_number} not found for project {project_id}.")

    title, outline_goal, outline_revelation, draft_path, ch_project_id = row

    if not draft_path:
        raise ValueError(f"Chapter {chapter_number} has no draft to summarise.")

    # ── Resolve draft file ───────────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        proj_row = await cur.fetchone()

    if proj_row is None:
        raise ValueError(f"Project {project_id} not found.")

    root_path = proj_row[0]
    abs_draft = os.path.join(root_path, draft_path)

    if not os.path.isfile(abs_draft):
        raise ValueError(f"Draft file not found: {abs_draft}")

    with open(abs_draft, "r", encoding="utf-8", errors="replace") as f:
        draft_text = f.read()

    # ── Build prompts ────────────────────────────────────────────────────────
    system_prompt = (
        "You are a literary editor writing chapter summaries for a novel production "
        "system. These summaries are used as context when generating future chapters "
        "— they must be precise, concrete, and continuity-aware."
    )

    user_prompt = (
        f"CHAPTER {chapter_number}: {title or '(untitled)'}\n"
        f"OUTLINE GOAL: {outline_goal or '(none)'}\n"
        f"OUTLINE REVELATION: {outline_revelation or '(none)'}\n"
        f"\nCHAPTER DRAFT:\n{draft_text}\n"
        "\nTASK:\n"
        "Write a 3-sentence summary of this chapter. Each sentence should cover:\n"
        "1. What happened (the main action or event)\n"
        "2. What changed (character state, relationship, or situation)\n"
        "3. What was revealed or set up (for future chapters)\n"
        "\nBe specific. Use character names. Include any facts that future chapters "
        "need to know.\n"
        "Output the 3 sentences only. No headings, no labels, no explanation."
    )

    # ── Call LLM ─────────────────────────────────────────────────────────────
    client = LLMClient()
    summary = client.complete(system_prompt, user_prompt)
    return summary.strip()
