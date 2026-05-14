"""
Prose Linter — deterministic, regex-based. No LLM calls.

lint_prose(text, prohibited) -> markdown report string
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple


# ── Hard-banned patterns (always checked) ────────────────────────────────────

HARD_BANNED: List[Tuple[str, str]] = [
    ("couldn't help but",    "Remove — cliché construction"),
    ("a sense of",           "Remove or specify concretely"),
    ("washed over",          "Remove — sensation cliché"),
    ("swept through",        "Remove — sensation cliché"),
    ("flooded back",         "Remove — memory cliché"),
    ("hung in the air",      "Remove — atmosphere cliché"),
    ("it was as if",         "Rewrite — distancing construction"),
    ("as though",            "Limit to 1 per chapter"),
]

NOT_X_BUT_Y = re.compile(r"\bnot\s.{1,30},\s*but\b", re.IGNORECASE)

EM_DASH_CHAR = "—"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lines(text: str) -> List[str]:
    return text.splitlines()


def _sentences(text: str) -> List[str]:
    """Split text into sentences on . ! ? boundaries (simple heuristic)."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def _first_word(sentence: str) -> str:
    m = re.match(r"([A-Za-z'\"]+)", sentence)
    return m.group(1).lower() if m else ""


# ── Check functions ───────────────────────────────────────────────────────────

def _check_em_dashes(text: str, total_words: int) -> List[str]:
    count = text.count(EM_DASH_CHAR)
    if total_words == 0:
        return []
    rate = count / (total_words / 1000)
    if rate > 5:
        return [f"Em dash count: **{count}** ({rate:.1f} per 1000 words, limit: 5)"]
    return []


def _check_banned_words(text: str, words: List[str]) -> List[Tuple[int, str]]:
    """Returns list of (line_number, word) for each hit."""
    hits = []
    lines = _lines(text)
    for word in words:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append((i, word))
    return hits


def _check_banned_phrases(text: str, phrases: List[str]) -> List[Tuple[int, str]]:
    hits = []
    lines = _lines(text)
    for phrase in phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append((i, phrase))
    return hits


def _check_hard_banned(text: str) -> List[Tuple[int, str, str]]:
    """Returns list of (line_number, matched_text, recommendation)."""
    hits = []
    lines = _lines(text)

    for phrase, rec in HARD_BANNED:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append((i, phrase, rec))

    # "not X, but Y" pattern
    for i, line in enumerate(lines, start=1):
        for m in NOT_X_BUT_Y.finditer(line):
            hits.append((i, m.group(0).strip(), 'Rewrite — "not X, but Y" construction'))

    return hits


def _check_rhythm(paragraphs: List[str]) -> List[str]:
    issues = []
    wcs = [_word_count(p) for p in paragraphs]

    # Long paragraphs
    for idx, (p, wc) in enumerate(zip(paragraphs, wcs), start=1):
        if wc > 150:
            issues.append(f"Paragraph {idx}: **{wc} words** (limit: 150)")

    # 3+ consecutive paragraphs with lengths within 20% of each other
    n = len(wcs)
    i = 0
    while i < n - 2:
        group = [wcs[i]]
        j = i + 1
        while j < n:
            base = sum(group) / len(group)
            if base > 0 and abs(wcs[j] - base) / base <= 0.20:
                group.append(wcs[j])
                j += 1
            else:
                break
        if len(group) >= 3:
            issues.append(
                f"Paragraphs {i + 1}–{i + len(group)}: repetitive rhythm "
                f"({', '.join(str(w) for w in group)} words)"
            )
            i += len(group)
        else:
            i += 1

    return issues


def _check_sentence_openers(text: str) -> List[str]:
    """Flag same first word opening 3+ sentences in any 10-sentence window."""
    sents = _sentences(text)
    issues = []
    window = 10

    for start in range(len(sents) - window + 1):
        chunk = sents[start: start + window]
        openers = [_first_word(s) for s in chunk]
        # count occurrences
        counts: Dict[str, int] = {}
        for w in openers:
            if w:
                counts[w] = counts.get(w, 0) + 1
        for word, cnt in counts.items():
            if cnt >= 3:
                # Deduplicate: only report once per word
                marker = f"opener:{word}:{start}"
                if marker not in issues:
                    issues.append(
                        f'Sentence opener **"{word}"** repeats {cnt}× in sentences {start + 1}–{start + window}'
                    )
    return issues


def _check_adverb_density(text: str) -> List[str]:
    words = text.split()
    if not words:
        return []
    adverbs = [w for w in words if re.match(r".+ly$", w, re.IGNORECASE) and len(w) > 3]
    rate = len(adverbs) / (len(words) / 100)
    if rate > 3:
        return [f"Adverb density: **{len(adverbs)}** adverbs ({rate:.1f} per 100 words, limit: 3)"]
    return []


def _check_repetitive_metaphors(text: str) -> List[str]:
    """Flag exact phrases of 4+ words appearing 2+ times."""
    issues = []
    words = text.lower().split()
    n = len(words)
    seen: Dict[str, int] = {}

    for length in range(4, 9):
        for i in range(n - length + 1):
            phrase = " ".join(words[i: i + length])
            # Strip leading/trailing punctuation from phrase tokens (rough)
            phrase = re.sub(r"[^\w\s]", "", phrase).strip()
            if not phrase or len(phrase) < 10:
                continue
            seen[phrase] = seen.get(phrase, 0) + 1

    for phrase, count in seen.items():
        if count >= 2:
            issues.append(f'Repeated phrase ({count}×): **"{phrase}"**')

    return issues


# ── Report builder ────────────────────────────────────────────────────────────

def _table_rows(rows: List[Tuple]) -> str:
    if not rows:
        return "_None_\n"
    lines = ["| Line | Matched | Recommendation |",
             "|------|---------|----------------|"]
    for row in rows:
        if len(row) == 2:
            line_no, matched = row
            rec = "Remove or rewrite"
        else:
            line_no, matched, rec = row
        lines.append(f"| {line_no} | {matched} | {rec} |")
    return "\n".join(lines) + "\n"


def lint_prose(text: str, prohibited: Dict) -> str:
    """
    Run all deterministic checks on text.

    prohibited: {"words": [...], "phrases": [...]}

    Returns a markdown report string.
    """
    total_words = _word_count(text)
    chapter_num = "N"  # caller can pass if needed; generic label works fine
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    paragraphs = _paragraphs(text)

    # Run checks
    em_dash_issues     = _check_em_dashes(text, total_words)
    banned_word_hits   = _check_banned_words(text, prohibited.get("words", []))
    banned_phrase_hits = _check_banned_phrases(text, prohibited.get("phrases", []))
    hard_banned_hits   = _check_hard_banned(text)
    rhythm_issues      = _check_rhythm(paragraphs)
    opener_issues      = _check_sentence_openers(text)
    adverb_issues      = _check_adverb_density(text)
    metaphor_issues    = _check_repetitive_metaphors(text)

    total_issues = (
        len(em_dash_issues)
        + len(banned_word_hits)
        + len(banned_phrase_hits)
        + len(hard_banned_hits)
        + len(rhythm_issues)
        + len(opener_issues)
        + len(adverb_issues)
        + len(metaphor_issues)
    )

    lines = [
        f"# Prose Lint Report — Chapter {chapter_num}",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        f"- Total issues: **{total_issues}**",
        f"- Em dashes: {text.count(EM_DASH_CHAR)} (limit: 5 per 1000 words)",
        f"- Banned words: {len(banned_word_hits)}",
        f"- Banned phrases: {len(banned_phrase_hits)}",
        f"- Pattern violations: {len(hard_banned_hits)}",
        f"- Rhythm issues: {len(rhythm_issues)}",
        f"- Sentence opener issues: {len(opener_issues)}",
        f"- Adverb issues: {len(adverb_issues)}",
        f"- Repetitive metaphors: {len(metaphor_issues)}",
        "",
        "## Issues",
        "",
    ]

    # Em dash
    if em_dash_issues:
        lines.append("### Em Dash Usage")
        for issue in em_dash_issues:
            lines.append(f"- {issue}")
        lines.append("")

    # Banned words
    lines.append("### Banned Words")
    lines.append(_table_rows([(ln, w) for ln, w in banned_word_hits]))

    # Banned phrases
    lines.append("### Banned Phrases")
    lines.append(_table_rows([(ln, p) for ln, p in banned_phrase_hits]))

    # Pattern violations (hard-banned + not-X-but-Y)
    lines.append("### Pattern Violations")
    lines.append(_table_rows(hard_banned_hits))

    # Rhythm
    lines.append("### Rhythm Issues")
    if rhythm_issues:
        for issue in rhythm_issues:
            lines.append(f"- {issue}")
        lines.append("")
    else:
        lines.append("_None_\n")

    # Sentence openers
    lines.append("### Sentence Openers")
    if opener_issues:
        for issue in opener_issues:
            lines.append(f"- {issue}")
        lines.append("")
    else:
        lines.append("_None_\n")

    # Adverbs
    lines.append("### Adverb Density")
    if adverb_issues:
        for issue in adverb_issues:
            lines.append(f"- {issue}")
        lines.append("")
    else:
        lines.append("_None_\n")

    # Repetitive metaphors
    lines.append("### Repetitive Metaphors")
    if metaphor_issues:
        for issue in metaphor_issues[:20]:  # cap at 20 to avoid huge reports
            lines.append(f"- {issue}")
        lines.append("")
    else:
        lines.append("_None_\n")

    return "\n".join(lines)
