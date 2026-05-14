"""
Parse character_bible.md to extract character entries.

Characters are delimited by ## or ### headings.
Sections inside a character block are ### sub-headings.
"""

import re
from typing import List, Dict


# A character heading: ## or ### followed by the name
_CHAR_HEADING = re.compile(r"^#{2,3}\s+(.+)$")

# Sub-sections we recognise inside a character block
_SECTION_HEADINGS = {
    "physical",
    "psychological profile",
    "voice and speech",
    "relationships",
    "arc",
    "supporting characters",
    "antagonists",
    "continuity rules",
    "key trait",
}

# Skip these pseudo-character headings
_SKIP_HEADINGS = re.compile(
    r"^(?:Supporting Characters|Antagonists?|Major Forces|CONTINUITY RULES)",
    re.IGNORECASE,
)

# Field patterns within a block (bare label: value)
_FIELD_PATTERNS = {
    "role":           re.compile(r"^(?:\*\*)?(?:Pre-story role|Role in story|Role)(?:\*\*)?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "age":            re.compile(r"^(?:\*\*)?Age(?:\*\*)?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "physical":       re.compile(r"^(?:\*\*)?(?:Physical|Appearance)(?:\*\*)?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "core_wound":     re.compile(r"^Core wound\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "internal_flaw":  re.compile(r"^Internal flaw\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "external_flaw":  re.compile(r"^External flaw\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "motivation":     re.compile(r"^Motivation\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "voice":          re.compile(r"^Voice(?:\s+and\s+speech)?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "arc_begin":      re.compile(r"^Begins?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "arc_midpoint":   re.compile(r"^Midpoints?\s*[:\-]\s*(.+)$", re.IGNORECASE),
    "arc_end":        re.compile(r"^Ends?\s*[:\-]\s*(.+)$", re.IGNORECASE),
}

# Section-level headings for multi-line fields
_SECTION_PHYSICAL = re.compile(r"^###\s+Physical\s*$", re.IGNORECASE)
_SECTION_PSYCH    = re.compile(r"^###\s+Psychological\s+profile\s*$", re.IGNORECASE)
_SECTION_VOICE    = re.compile(r"^###\s+Voice\s+and\s+speech\s*$", re.IGNORECASE)
_SECTION_ARC      = re.compile(r"^###\s+Arc\b", re.IGNORECASE)
_SECTION_REL      = re.compile(r"^###\s+Relationships\s*$", re.IGNORECASE)


def _blank_char(name: str) -> Dict:
    return {
        "name":                 name,
        "role":                 "",
        "age":                  "",
        "physical":             "",
        "core_wound":           "",
        "internal_flaw":        "",
        "external_flaw":        "",
        "motivation":           "",
        "voice_description":    "",
        "sample_internal_voice": "",
        "arc_begin":            "",
        "arc_midpoint":         "",
        "arc_end":              "",
        "raw_markdown":         "",
    }


def _is_char_heading(line: str):
    """Return name string if line is a ##/### character heading, else None."""
    m = _CHAR_HEADING.match(line.strip())
    if not m:
        return None
    name = m.group(1).strip()
    # Filter out known skip headings
    if _SKIP_HEADINGS.match(name):
        return None
    # Filter out sub-section headings (### Physical etc.)
    lower = name.lower()
    for sec in _SECTION_HEADINGS:
        if lower.startswith(sec):
            return None
    return name


def _extract_name_and_role(raw_name: str):
    """Split 'CHARACTER NAME — Primary Protagonist' into (name, role)."""
    for sep in [" — ", " - ", " – "]:
        if sep in raw_name:
            parts = raw_name.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return raw_name.strip(), ""


def parse_characters(text: str) -> List[Dict]:
    """Parse character bible markdown and return list of character dicts."""
    characters: List[Dict] = []
    current: Dict | None = None
    raw_lines: List[str] = []
    current_section = None  # which multi-line section we're accumulating

    def _flush():
        nonlocal current, raw_lines, current_section
        if current is None:
            return
        current["raw_markdown"] = "\n".join(raw_lines).strip()
        # Skip placeholders that have no real content
        name = current["name"]
        if re.search(r"\[.+?\]", name):
            current = None
            raw_lines = []
            current_section = None
            return
        characters.append(current)
        current = None
        raw_lines = []
        current_section = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        # Check for a new character heading
        name_candidate = _is_char_heading(raw_line)
        if name_candidate is not None:
            _flush()
            name, role_from_heading = _extract_name_and_role(name_candidate)
            current = _blank_char(name)
            if role_from_heading:
                current["role"] = role_from_heading
            raw_lines = [raw_line]
            current_section = None
            continue

        if current is None:
            continue

        raw_lines.append(raw_line)

        # Section transitions within a character block
        if _SECTION_PHYSICAL.match(stripped):
            current_section = "physical"
            continue
        if _SECTION_PSYCH.match(stripped):
            current_section = "psych"
            continue
        if _SECTION_VOICE.match(stripped):
            current_section = "voice"
            continue
        if _SECTION_ARC.match(stripped):
            current_section = "arc"
            continue
        if _SECTION_REL.match(stripped):
            current_section = "relationships"
            continue

        # Skip horizontal rules and blank lines for field parsing
        if not stripped or stripped == "---":
            continue

        # Try explicit field patterns
        matched = False
        for field, pat in _FIELD_PATTERNS.items():
            m = pat.match(stripped)
            if m:
                value = m.group(1).strip()
                if field == "role" and not current["role"]:
                    current["role"] = value
                elif field == "age" and not current["age"]:
                    current["age"] = value
                elif field == "physical" and not current["physical"]:
                    current["physical"] = value
                elif field == "core_wound" and not current["core_wound"]:
                    current["core_wound"] = value
                elif field == "internal_flaw" and not current["internal_flaw"]:
                    current["internal_flaw"] = value
                elif field == "external_flaw" and not current["external_flaw"]:
                    current["external_flaw"] = value
                elif field == "motivation" and not current["motivation"]:
                    current["motivation"] = value
                elif field == "voice" and not current["voice_description"]:
                    current["voice_description"] = value
                elif field == "arc_begin" and not current["arc_begin"]:
                    current["arc_begin"] = value
                elif field == "arc_midpoint" and not current["arc_midpoint"]:
                    current["arc_midpoint"] = value
                elif field == "arc_end" and not current["arc_end"]:
                    current["arc_end"] = value
                matched = True
                break

        if matched:
            continue

        # Accumulate multi-line section text
        if current_section == "physical" and not current["physical"]:
            # Grab the first non-empty paragraph under ### Physical
            if stripped and not stripped.startswith("#"):
                current["physical"] += (" " if current["physical"] else "") + stripped
        elif current_section == "voice" and not current["voice_description"]:
            if stripped and not stripped.startswith("#") and not stripped.startswith("**Sample"):
                current["voice_description"] += (" " if current["voice_description"] else "") + stripped
        elif current_section == "voice":
            # Sample internal voice block (blockquote lines)
            if stripped.startswith(">"):
                voice_text = stripped.lstrip("> ").strip()
                current["sample_internal_voice"] += (" " if current["sample_internal_voice"] else "") + voice_text

    _flush()
    return characters
