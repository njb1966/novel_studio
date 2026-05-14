"""
Assembles all context needed to generate a chapter draft.
Reads project files from disk and queries SQLite for dynamic data.
"""

import os
import re
from typing import Optional

import aiosqlite

from database import get_db_path
from parsers.outline_parser import parse_outline


# ── File helpers ────────────────────────────────────────────────────────────

def _read_file(folder: str, *candidates: str) -> str:
    """Return content of first matching filename in folder, or empty string."""
    for name in candidates:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    return ""


def _read_path(path: str) -> str:
    """Return content of a file at an absolute path, or empty string."""
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


# ── Chapter section extractor ────────────────────────────────────────────────

def _extract_outline_entry(outline_text: str, chapter_number: int) -> str:
    """
    Parse outline.md and return the raw_block for the given chapter_number.
    Falls back to empty string if the chapter is not found.
    """
    if not outline_text:
        return ""
    try:
        chapters = parse_outline(outline_text)
        for ch in chapters:
            if ch.get("chapter_number") == chapter_number:
                return ch.get("raw_block", "")
    except Exception:
        pass
    return ""


# ── Character section extractor ─────────────────────────────────────────────

def _extract_character_block(char_bible_text: str, character_name: str) -> str:
    """
    Scan character_bible.md for a ## or ### heading that matches character_name
    (case-insensitive, allows "Name — Role" format).
    Returns the full text of that section up to the next same-level heading.
    """
    if not char_bible_text or not character_name:
        return ""

    name_lower = character_name.lower().strip()
    lines = char_bible_text.splitlines(keepends=True)

    # Heading pattern: ## or ### followed by text
    heading_re = re.compile(r"^(#{2,3})\s+(.+)$")

    start_idx: Optional[int] = None
    start_level: Optional[int] = None

    for i, line in enumerate(lines):
        m = heading_re.match(line.rstrip())
        if not m:
            continue
        level = len(m.group(1))
        heading_text = m.group(2).strip()

        # Strip "Name — Role" format for matching
        for sep in [" — ", " – ", " - "]:
            if sep in heading_text:
                heading_text = heading_text.split(sep, 1)[0]
                break
        heading_text = heading_text.strip().lower()

        if start_idx is None:
            # Looking for the matching character heading
            if heading_text == name_lower:
                start_idx = i
                start_level = level
        else:
            # We're inside the block; stop at the next heading of same or higher level
            if level <= start_level:
                return "".join(lines[start_idx:i]).strip()

    if start_idx is not None:
        return "".join(lines[start_idx:]).strip()

    return ""


# ── Main assembler ───────────────────────────────────────────────────────────

async def assemble_chapter_context(project_id: int, chapter_number: int, db) -> dict:
    """
    Build the full generation context for a chapter.

    Returns a dict with string values for every key.
    All keys are present; missing/unavailable values are empty strings.
    """

    # ── Fetch project row ────────────────────────────────────────────────────
    async with db.execute(
        "SELECT root_path, pov, tense FROM projects WHERE id = ?",
        (project_id,),
    ) as cur:
        proj_row = await cur.fetchone()
    if not proj_row:
        raise ValueError(f"Project {project_id} not found.")

    root_path, proj_pov, proj_tense = proj_row
    proj_pov   = proj_pov   or ""
    proj_tense = proj_tense or ""

    # ── Fetch chapter row ────────────────────────────────────────────────────
    async with db.execute(
        """SELECT title, pov_character, outline_goal, outline_conflict,
                  outline_revelation, outline_notes
             FROM chapters
            WHERE project_id = ? AND chapter_number = ?""",
        (project_id, chapter_number),
    ) as cur:
        ch_row = await cur.fetchone()
    if not ch_row:
        raise ValueError(f"Chapter {chapter_number} not found in project {project_id}.")

    (
        ch_title,
        pov_character,
        outline_goal,
        outline_conflict,
        outline_revelation,
        outline_notes,
    ) = ch_row

    ch_title         = ch_title         or ""
    pov_character    = pov_character    or ""
    outline_goal      = outline_goal     or ""
    outline_conflict  = outline_conflict or ""
    outline_revelation = outline_revelation or ""
    outline_notes    = outline_notes    or ""

    # ── Read project files ───────────────────────────────────────────────────
    novel_spec = _read_file(
        root_path,
        "novel_spec.md", "NOVEL_SPEC.md", "Novel_Spec.md",
    )

    outline_text = _read_file(
        root_path,
        "outline.md", "OUTLINE.md", "Outline.md",
    )

    char_bible_text = _read_file(
        root_path,
        "character_bible.md", "CHARACTER_BIBLE.md", "Character_Bible.md",
        "characters.md", "CHARACTERS.md",
    )

    world_bible = _read_file(
        root_path,
        "world_bible.md", "WORLD_BIBLE.md", "World_Bible.md",
        "worldbuilding.md", "WORLDBUILDING.md",
    )

    prohibited_rules = _read_file(root_path, "PROHIBITED.md", "prohibited.md")

    writing_refiner = _read_file(
        root_path,
        "writing-refiner.md", "writing_refiner.md",
        "WRITING_REFINER.md", "WRITING-REFINER.md",
    )

    # ── Derived fields ───────────────────────────────────────────────────────
    outline_entry = _extract_outline_entry(outline_text, chapter_number)
    pov_char_block = _extract_character_block(char_bible_text, pov_character)

    # ── Previous chapter summary ─────────────────────────────────────────────
    previous_summary = ""
    if chapter_number > 1:
        prev_num = chapter_number - 1
        summary_filename = f"CH{prev_num:03d}_SUMMARY.md"
        summary_path = os.path.join(root_path, "summaries", summary_filename)
        previous_summary = _read_path(summary_path)

    # ── Recent continuity facts ──────────────────────────────────────────────
    async with db.execute(
        """SELECT fact_type, subject, fact
             FROM continuity_facts
            WHERE project_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 20""",
        (project_id,),
    ) as cur:
        fact_rows = await cur.fetchall()

    if fact_rows:
        fact_lines = [
            f"- [{r[0]}] {r[1] + ': ' if r[1] else ''}{r[2]}"
            for r in reversed(fact_rows)
        ]
        recent_continuity = "\n".join(fact_lines)
    else:
        recent_continuity = ""

    return {
        "novel_spec":        novel_spec,
        "outline_entry":     outline_entry,
        "pov_character":     pov_char_block,
        "world_bible":       world_bible,
        "recent_continuity": recent_continuity,
        "previous_summary":  previous_summary,
        "prohibited_rules":  prohibited_rules,
        "writing_refiner":   writing_refiner,
        "chapter_number":    chapter_number,
        "chapter_title":     ch_title,
        "pov":               proj_pov,
        "tense":             proj_tense,
        "outline_goal":      outline_goal,
        "outline_conflict":  outline_conflict,
        "outline_revelation": outline_revelation,
    }
