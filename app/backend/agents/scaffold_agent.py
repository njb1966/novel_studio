"""
Scaffold Agent — generates NOVEL_SPEC.md, CHARACTER_BIBLE.md, WORLD_BIBLE.md,
and CONTINUITY_LOG.md from an existing outline and project metadata.

All four LLM calls run concurrently via asyncio.run_in_executor.
"""

import asyncio
from llm_client import LLMClient

_SYSTEM = (
    "You are a novel development assistant helping an author scaffold foundational "
    "project documents from an outline. Be specific and concrete — infer details "
    "from the outline rather than producing generic placeholder text. "
    "Output clean, well-structured markdown only. No preamble, no meta-commentary."
)

_NOVEL_SPEC_PROMPT = """\
PROJECT METADATA:
Title: {title}
Genre: {genre}
Point of View: {pov}
Tense: {tense}
Target word count: {word_count:,}

OUTLINE:
{outline}

TASK:
Generate a comprehensive NOVEL_SPEC.md for this novel. Use this structure:

# {title}

## Premise
Two or three sentences that capture what the story is and why it matters.

## Genre & Subgenre
What shelf it sits on and any genre conventions to honour or subvert.

## Point of View & Tense
Exactly how the novel is narrated — who, how close, which tense.

## Themes
Bulleted list of the central ideas the novel explores.

## Tone & Style
The emotional register, prose density, pacing expectations.

## Narrative Structure
How the story is shaped — acts, arc, structural choices.

## Core Conflict
The engine driving the plot: what is at stake and for whom.

## Resolution Direction
The thematic trajectory (not a plot spoiler — what the story is building toward emotionally and thematically).

## Working Notes
Anything else that will guide an AI drafting agent: recurring motifs, things to
avoid, narrative rules specific to this story.
"""

_CHARACTER_BIBLE_PROMPT = """\
PROJECT TITLE: {title}

OUTLINE:
{outline}

TASK:
Generate a CHARACTER_BIBLE.md. For every named character mentioned or clearly
implied by the outline, produce a profile section. Lead with POV and major
characters; be briefer for supporting and minor roles.

Use this structure for each character:

## [Character Name]
- **Role**: protagonist / antagonist / supporting / minor
- **Age & Physical Description**: brief, vivid
- **Background**: relevant history that shapes present behaviour
- **Personality**: three to five defining traits
- **Voice & Speech Pattern**: how they speak — cadence, vocabulary, verbal tics
- **Arc**: where they begin, what changes, where they end
- **Key Relationships**: connections to other named characters
- **Secrets / Hidden Motivations**: what others don't know about them

Do not invent characters not implied by the outline.
"""

_WORLD_BIBLE_PROMPT = """\
PROJECT TITLE: {title}

OUTLINE:
{outline}

TASK:
Generate a WORLD_BIBLE.md grounded in what the outline establishes. Use this structure:

# World Bible — {title}

## Setting Overview
Time period, geographic scope, overall atmosphere.

## Key Locations
One sub-section per significant location the outline references:

### [Location Name]
- Physical description and scale
- Atmosphere and what makes it distinctive
- Who inhabits or controls it, and why it matters to the story

## Social & Political Context
Power structures, factions, tensions, and hierarchies relevant to the plot.

## Rules & Logic
What governs this world: technology level, any speculative or fantastical elements,
social norms, laws, economic realities — whatever shapes character choices.

## Sensory Palette
Recurring sights, sounds, smells, and textures that define the world's feel and
should thread through the prose.

## History & Backstory
Key events that happened before the novel opens and cast a shadow over the present.

Do not invent world elements that contradict the outline.
"""

_CONTINUITY_LOG_PROMPT = """\
PROJECT TITLE: {title}

OUTLINE:
{outline}

TASK:
Generate a CONTINUITY_LOG.md that records established facts at the START of the
story — before Chapter 1. This seeds the continuity tracker so an AI drafting
agent can check consistency as chapters are written.

Format each fact as a bullet: **[Category]** — [fact]

Use these categories (include only those the outline supports):
- **Character** — status, location, relationships, physical state at story start
- **World State** — political or social conditions, key events in the recent past
- **Object** — significant items and who possesses them
- **Timeline** — any firm dates or time anchors established in backstory
- **Secret** — facts true in the world but not yet known to certain characters

End the file with:

---
*Log seeded from outline. Update after each approved chapter.*

Only include facts clearly established by the outline. Omit anything ambiguous.
"""


async def scaffold_documents(
    title: str,
    genre: str,
    pov: str,
    tense: str,
    target_word_count: int,
    outline: str,
    targets: set[str] | None = None,
) -> dict[str, str]:
    """
    Generate scaffold documents concurrently. Returns {filename: content}.
    Pass targets to generate only a subset; None means all four.
    """
    all_targets = {
        "novel_spec.md",
        "character_bible.md",
        "world_bible.md",
        "continuity_log.md",
    }
    to_run = targets if targets is not None else all_targets

    common = dict(
        title=title,
        genre=genre or "unspecified",
        pov=pov or "unspecified",
        tense=tense or "unspecified",
        word_count=target_word_count or 80000,
        outline=outline,
    )

    jobs = {
        "novel_spec.md":      _NOVEL_SPEC_PROMPT.format(**common),
        "character_bible.md": _CHARACTER_BIBLE_PROMPT.format(**common),
        "world_bible.md":     _WORLD_BIBLE_PROMPT.format(**common),
        "continuity_log.md":  _CONTINUITY_LOG_PROMPT.format(**common),
    }

    client = LLMClient()
    loop = asyncio.get_event_loop()

    async def _call(prompt: str) -> str:
        return await loop.run_in_executor(
            None,
            lambda: client.complete(_SYSTEM, prompt, max_tokens=4096),
        )

    tasks = {
        fname: asyncio.create_task(_call(prompt))
        for fname, prompt in jobs.items()
        if fname in to_run
    }

    results = {}
    for fname, task in tasks.items():
        results[fname] = await task

    return results
