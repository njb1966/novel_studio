"""
Draft Agent — generates a chapter draft by assembling context and calling the LLM.
"""

from context_assembler import assemble_chapter_context
from llm_client import LLMClient

_SYSTEM_PROMPT = (
    "You are a disciplined literary fiction drafting agent working inside a "
    "human-directed novel production system. Preserve the author's voice, obey "
    "the project specification, and do not introduce unsupported continuity."
)

_USER_TEMPLATE = """\
NOVEL SPEC:
{novel_spec}

POV CHARACTER:
{pov_character}

WORLD CONTEXT:
{world_bible}

CONTINUITY CONTEXT:
{recent_continuity}

OUTLINE ENTRY:
{outline_entry}

PREVIOUS CHAPTER SUMMARY:
{previous_summary}

PROHIBITED LANGUAGE RULES:
{prohibited_rules}

WRITING REFINER STYLE:
{writing_refiner}

TASK:
Draft Chapter {chapter_number}{title_part}.
Follow the outline goal, conflict, and revelation.
Write in {pov} point of view, {tense} tense.
Avoid all prohibited language.
Do not add meta-commentary, author notes, or chapter headings.
Output chapter prose only.
"""


async def generate_draft(project_id: int, chapter_number: int, db) -> str:
    """
    Assemble context for chapter_number and call the LLM to produce a draft.
    Returns the prose string.
    """
    ctx = await assemble_chapter_context(project_id, chapter_number, db)

    title_part = ""
    if ctx["chapter_title"]:
        title_part = f" — {ctx['chapter_title']}"

    user_prompt = _USER_TEMPLATE.format(
        novel_spec=ctx["novel_spec"] or "(not provided)",
        pov_character=ctx["pov_character"] or "(not provided)",
        world_bible=ctx["world_bible"] or "(not provided)",
        recent_continuity=ctx["recent_continuity"] or "(none recorded)",
        outline_entry=ctx["outline_entry"] or "(not provided)",
        previous_summary=ctx["previous_summary"] or "(none — this is the first chapter or no summary exists)",
        prohibited_rules=ctx["prohibited_rules"] or "(none specified)",
        writing_refiner=ctx["writing_refiner"] or "(none specified)",
        chapter_number=ctx["chapter_number"],
        title_part=title_part,
        pov=ctx["pov"] or "third limited",
        tense=ctx["tense"] or "past",
    )

    client = LLMClient()
    return client.complete(_SYSTEM_PROMPT, user_prompt)
