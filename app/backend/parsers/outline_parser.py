"""
Parse outline.md to extract chapter entries.

Supported heading formats:
  **CHAPTER N — Title**          (bold, em dash)
  **CHAPTER N - Title**          (bold, hyphen)
  ## Chapter N — Title           (ATX heading, em dash)
  ## Chapter N: Title            (ATX heading, colon)
  ### Chapter N                  (ATX heading, no separator)
"""

import re
from typing import List, Dict


# Matches the **CHAPTER N — Title** format (case-insensitive, em dash or hyphen)
_BOLD_CHAPTER = re.compile(
    r"^\*\*CHAPTER\s+(\d+)\s*[—\-–]\s*(.+?)\*\*\s*$",
    re.IGNORECASE,
)

# Matches ## Chapter N — Title / ## Chapter N: Title / ### Chapter N
_ATX_CHAPTER = re.compile(
    r"^#{2,3}\s+CHAPTER\s+(\d+)(?:\s*[—\-–:]\s*(.+))?$",
    re.IGNORECASE,
)

# Field patterns (key: value on a line)
_FIELD_PATTERNS = {
    "pov_character":      re.compile(r"^POV:\s*(.+)$", re.IGNORECASE),
    "outline_goal":       re.compile(r"^Goal:\s*(.+)$", re.IGNORECASE),
    "outline_conflict":   re.compile(r"^Conflict:\s*(.+)$", re.IGNORECASE),
    "outline_revelation": re.compile(r"^(?:Revelation|Resolution):\s*(.+)$", re.IGNORECASE),
    "cliffhanger":        re.compile(r"^Cliffhanger:\s*(.+)$", re.IGNORECASE),
    "notes":              re.compile(r"^Notes:\s*(.*)$", re.IGNORECASE),
}


def _blank_chapter(number: int, title: str) -> Dict:
    return {
        "chapter_number":     number,
        "title":              title,
        "pov_character":      "",
        "outline_goal":       "",
        "outline_conflict":   "",
        "outline_revelation": "",
        "outline_notes":      "",
        "cliffhanger":        "",
        "raw_block":          "",
    }


def _match_chapter_heading(line: str):
    """Return (number, title) or None."""
    m = _BOLD_CHAPTER.match(line.strip())
    if m:
        return int(m.group(1)), m.group(2).strip()
    m = _ATX_CHAPTER.match(line.strip())
    if m:
        title = m.group(2).strip() if m.group(2) else ""
        return int(m.group(1)), title
    return None


def _is_section_divider(line: str) -> bool:
    """True for horizontal rules and act/section headings that are not chapters."""
    stripped = line.strip()
    if re.match(r"^-{3,}$", stripped):
        return False  # horizontal rules do not end a chapter block
    # Top-level headings like ## ACT I or # OUTLINE ... are section boundaries
    if re.match(r"^#{1,2}\s+(?:ACT|OUTLINE|How to Use)", stripped, re.IGNORECASE):
        return True
    return False


def parse_outline(text: str) -> List[Dict]:
    """Parse outline markdown text and return list of chapter dicts."""
    chapters: List[Dict] = []
    current: Dict | None = None
    block_lines: List[str] = []

    def _flush():
        nonlocal current, block_lines
        if current is None:
            return
        block_text = "\n".join(block_lines).strip()
        current["raw_block"] = block_text

        # Collect notes: lines not consumed by field patterns (excluding blank lines)
        remaining_lines = []
        for bline in block_lines:
            stripped = bline.strip()
            if not stripped:
                continue
            matched_field = False
            for field, pat in _FIELD_PATTERNS.items():
                if pat.match(stripped):
                    matched_field = True
                    break
            if not matched_field:
                remaining_lines.append(stripped)

        # Join leftover lines as outline_notes if no explicit notes field was set
        if not current["outline_notes"] and remaining_lines:
            current["outline_notes"] = "\n".join(remaining_lines)

        chapters.append(current)
        current = None
        block_lines = []

    for raw_line in text.splitlines():
        heading = _match_chapter_heading(raw_line)
        if heading:
            _flush()
            number, title = heading
            current = _blank_chapter(number, title)
            block_lines = []
            continue

        if _is_section_divider(raw_line):
            _flush()
            continue

        if current is not None:
            stripped = raw_line.strip()
            # Try to match known fields
            for field, pat in _FIELD_PATTERNS.items():
                m = pat.match(stripped)
                if m:
                    value = m.group(1).strip()
                    # Notes field maps to outline_notes
                    if field == "notes":
                        if not current["outline_notes"]:
                            current["outline_notes"] = value
                        else:
                            current["outline_notes"] += "\n" + value
                    else:
                        if not current.get(field):
                            current[field] = value
                    break
            else:
                block_lines.append(raw_line)

    _flush()
    return chapters
