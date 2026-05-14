import os
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, HTTPException

from database import get_db_path
from parsers.outline_parser import parse_outline
from parsers.character_parser import parse_characters
from parsers.prohibited_parser import parse_prohibited

router = APIRouter(prefix="/projects", tags=["sync"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_file(folder: str, *candidates: str) -> str | None:
    """Return content of first matching filename in folder, or None."""
    for name in candidates:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    return None


@router.post("/{project_id}/sync")
async def sync_project(project_id: int):
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT root_path FROM projects WHERE id = ?", (project_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found.")
        root_path = row[0]

    # ── Outline / Chapters ──────────────────────────────────────────────────
    chapters_synced = 0
    outline_text = _read_file(
        root_path, "OUTLINE.md", "outline.md", "Outline.md"
    )
    if outline_text:
        parsed_chapters = parse_outline(outline_text)
        now = _now()
        async with aiosqlite.connect(get_db_path()) as db:
            for ch in parsed_chapters:
                async with db.execute(
                    "SELECT id FROM chapters WHERE project_id = ? AND chapter_number = ?",
                    (project_id, ch["chapter_number"]),
                ) as cur:
                    existing = await cur.fetchone()
                if existing:
                    await db.execute(
                        """UPDATE chapters SET
                            title = ?,
                            pov_character = ?,
                            outline_goal = ?,
                            outline_conflict = ?,
                            outline_revelation = ?,
                            outline_notes = ?,
                            updated_at = ?
                        WHERE project_id = ? AND chapter_number = ?""",
                        (
                            ch["title"],
                            ch["pov_character"],
                            ch["outline_goal"],
                            ch["outline_conflict"],
                            ch["outline_revelation"],
                            ch["outline_notes"],
                            now,
                            project_id,
                            ch["chapter_number"],
                        ),
                    )
                else:
                    await db.execute(
                        """INSERT INTO chapters
                            (project_id, chapter_number, title, pov_character,
                             outline_goal, outline_conflict, outline_revelation,
                             outline_notes, status, target_word_count,
                             actual_word_count, draft_path, final_path,
                             summary_path, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            project_id,
                            ch["chapter_number"],
                            ch["title"],
                            ch["pov_character"],
                            ch["outline_goal"],
                            ch["outline_conflict"],
                            ch["outline_revelation"],
                            ch["outline_notes"],
                            "draft",
                            3000,
                            0,
                            "",
                            "",
                            "",
                            now,
                            now,
                        ),
                    )
                chapters_synced += 1
            await db.commit()

        # ── Back-fill file paths for existing chapters on disk ──────────────
        chapters_dir = os.path.join(root_path, "chapters")
        summaries_dir = os.path.join(root_path, "summaries")
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute(
                "SELECT id, chapter_number FROM chapters WHERE project_id = ?",
                (project_id,),
            ) as cur:
                rows = await cur.fetchall()
            for ch_id, ch_num in rows:
                draft   = os.path.join("chapters",  f"CH{ch_num:03d}_DRAFT.md")
                final   = os.path.join("chapters",  f"CH{ch_num:03d}_FINAL.md")
                summary = os.path.join("summaries", f"CH{ch_num:03d}_SUMMARY.md")
                has_draft   = os.path.isfile(os.path.join(root_path, draft))
                has_final   = os.path.isfile(os.path.join(root_path, final))
                has_summary = os.path.isfile(os.path.join(root_path, summary))

                # word count from draft or final
                wc = 0
                for p in [os.path.join(root_path, final), os.path.join(root_path, draft)]:
                    if os.path.isfile(p):
                        try:
                            txt = open(p, encoding="utf-8", errors="replace").read()
                            wc = len(txt.split())
                        except OSError:
                            pass
                        break

                status = "approved" if has_final else ("draft" if has_draft else "draft")
                await db.execute(
                    """UPDATE chapters SET
                        draft_path   = CASE WHEN ? THEN ? ELSE draft_path END,
                        final_path   = CASE WHEN ? THEN ? ELSE final_path END,
                        summary_path = CASE WHEN ? THEN ? ELSE summary_path END,
                        actual_word_count = CASE WHEN ? > 0 THEN ? ELSE actual_word_count END,
                        status = ?
                    WHERE id = ?""",
                    (
                        has_draft,   draft,
                        has_final,   final,
                        has_summary, summary,
                        wc, wc,
                        status,
                        ch_id,
                    ),
                )
            await db.commit()

    # ── Characters ──────────────────────────────────────────────────────────
    characters_synced = 0
    char_text = _read_file(
        root_path,
        "CHARACTER_BIBLE.md",
        "character_bible.md",
        "Character_Bible.md",
        "CHARACTERS.md",
        "characters.md",
    )
    if char_text:
        parsed_chars = parse_characters(char_text)
        now = _now()
        async with aiosqlite.connect(get_db_path()) as db:
            for ch in parsed_chars:
                async with db.execute(
                    "SELECT id FROM characters WHERE project_id = ? AND name = ?",
                    (project_id, ch["name"]),
                ) as cur:
                    existing = await cur.fetchone()
                if existing:
                    await db.execute(
                        """UPDATE characters SET
                            role = ?, age = ?, physical = ?,
                            core_wound = ?, internal_flaw = ?, external_flaw = ?,
                            motivation = ?, voice_description = ?,
                            sample_internal_voice = ?,
                            arc_begin = ?, arc_midpoint = ?, arc_end = ?,
                            raw_markdown = ?
                        WHERE project_id = ? AND name = ?""",
                        (
                            ch["role"], ch["age"], ch["physical"],
                            ch["core_wound"], ch["internal_flaw"], ch["external_flaw"],
                            ch["motivation"], ch["voice_description"],
                            ch["sample_internal_voice"],
                            ch["arc_begin"], ch["arc_midpoint"], ch["arc_end"],
                            ch["raw_markdown"],
                            project_id, ch["name"],
                        ),
                    )
                else:
                    await db.execute(
                        """INSERT INTO characters
                            (project_id, name, role, age, physical,
                             core_wound, internal_flaw, external_flaw,
                             motivation, voice_description, sample_internal_voice,
                             arc_begin, arc_midpoint, arc_end, raw_markdown)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            project_id,
                            ch["name"], ch["role"], ch["age"], ch["physical"],
                            ch["core_wound"], ch["internal_flaw"], ch["external_flaw"],
                            ch["motivation"], ch["voice_description"],
                            ch["sample_internal_voice"],
                            ch["arc_begin"], ch["arc_midpoint"], ch["arc_end"],
                            ch["raw_markdown"],
                        ),
                    )
                characters_synced += 1
            await db.commit()

    # ── Prohibited ──────────────────────────────────────────────────────────
    prohibited_result = {"words": 0, "phrases": 0}
    try:
        prohibited_data = parse_prohibited(root_path)
        prohibited_result = {
            "words":   len(prohibited_data["words"]),
            "phrases": len(prohibited_data["phrases"]),
        }
    except Exception:
        pass  # prohibited list is optional

    return {
        "chapters_synced":   chapters_synced,
        "characters_synced": characters_synced,
        "prohibited_synced": prohibited_result,
    }
