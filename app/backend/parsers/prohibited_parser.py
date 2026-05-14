"""
Parse PROHIBITED.md or prohibited.yaml and extract banned words/phrases.

Returns:
    {"words": [...], "phrases": [...]}

Also writes prohibited.yaml to the project folder.
"""

import os
import re
from typing import Dict, List


def _parse_markdown(text: str) -> Dict[str, List[str]]:
    """Extract banned items from PROHIBITED.md."""
    words: List[str] = []
    phrases: List[str] = []

    current_section = None
    for line in text.splitlines():
        stripped = line.strip()

        # Identify section context
        if re.match(r"^#{1,3}\s+(CATEGORY\s+1|BANNED WORDS|Ban(?:ned)? Words|Verbs|Adjectives|Nouns)", stripped, re.IGNORECASE):
            current_section = "words"
            continue
        if re.match(r"^#{1,3}\s+(CATEGORY\s+2|BANNED SENTENCES?|Banned Phrase|Sentence Pattern)", stripped, re.IGNORECASE):
            current_section = "phrases"
            continue
        if re.match(r"^#{1,3}\s+(CATEGORY\s+[34]|BANNED STRUCT|Novel-Specific|PRODUCTION RULES|RULE ZERO)", stripped, re.IGNORECASE):
            current_section = "phrases"
            continue

        # Bullet list items
        m = re.match(r"^[-*]\s+(?:\*\*)?(.+?)(?:\*\*)?\s*(?:—.*)?$", stripped)
        if m and current_section:
            item = m.group(1).strip()
            # Remove any trailing bold markers or extra whitespace
            item = re.sub(r"\*+", "", item).strip()
            if not item:
                continue
            # Heuristic: phrases contain spaces, words do not (mostly)
            word_count = len(item.split())
            if current_section == "words":
                if word_count <= 2:
                    words.append(item)
                else:
                    phrases.append(item)
            elif current_section == "phrases":
                phrases.append(item)

    # Deduplicate preserving order
    seen_w: set = set()
    seen_p: set = set()
    words_out = [w for w in words if not (w.lower() in seen_w or seen_w.add(w.lower()))]
    phrases_out = [p for p in phrases if not (p.lower() in seen_p or seen_p.add(p.lower()))]

    return {"words": words_out, "phrases": phrases_out}


def _parse_yaml(text: str) -> Dict[str, List[str]]:
    """Parse a simple prohibited.yaml without external deps."""
    words: List[str] = []
    phrases: List[str] = []
    current_key = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "words:":
            current_key = "words"
            continue
        if stripped == "phrases:":
            current_key = "phrases"
            continue
        m = re.match(r"^-\s+(.+)$", stripped)
        if m and current_key:
            item = m.group(1).strip().strip("'\"")
            if current_key == "words":
                words.append(item)
            elif current_key == "phrases":
                phrases.append(item)

    return {"words": words, "phrases": phrases}


def _write_yaml(project_folder: str, data: Dict[str, List[str]]) -> None:
    yaml_path = os.path.join(project_folder, "prohibited.yaml")
    lines = ["words:"]
    for w in data["words"]:
        lines.append(f"  - {w}")
    lines.append("phrases:")
    for p in data["phrases"]:
        # Quote phrases that contain colons or special chars
        safe = p.replace("'", "\\'")
        lines.append(f"  - '{safe}'")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def parse_prohibited(project_folder: str) -> Dict[str, List[str]]:
    """
    Try prohibited.yaml first, then PROHIBITED.md.
    Writes prohibited.yaml to project_folder.
    Returns {"words": [...], "phrases": [...]}.
    """
    yaml_path = os.path.join(project_folder, "prohibited.yaml")
    md_path = os.path.join(project_folder, "PROHIBITED.md")

    data: Dict[str, List[str]] = {"words": [], "phrases": []}

    if os.path.isfile(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = _parse_yaml(f.read())
    elif os.path.isfile(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            data = _parse_markdown(f.read())

    # Always (re)write yaml to project folder
    _write_yaml(project_folder, data)

    return data
