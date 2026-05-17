from pydantic import BaseModel
from typing import Optional


class Project(BaseModel):
    id: int
    slug: str
    title: str
    created_at: str
    updated_at: str
    root_path: str
    target_word_count: int = 0
    actual_word_count: int = 0
    pov: str = ""
    tense: str = ""
    genre: str = ""
    status: str = "active"


class ProjectCreate(BaseModel):
    title: str
    target_word_count: int = 80000
    pov: str = ""
    tense: str = ""
    genre: str = ""
    storage_path: str = ""


class ProjectImport(BaseModel):
    folder_path: str


class FileContent(BaseModel):
    content: str


class Chapter(BaseModel):
    id: int
    project_id: int
    chapter_number: int
    title: str
    pov_character: str
    status: str
    target_word_count: int
    actual_word_count: int
    outline_goal: str
    outline_conflict: str
    outline_revelation: str
    outline_notes: str
    draft_path: str
    final_path: str
    summary_path: str
    summary_snippet: str = ""
    created_at: str
    updated_at: str


class SummaryResult(BaseModel):
    chapter_number: int
    summary: str
    summary_path: str


class ApproveResult(BaseModel):
    chapter_number: int
    status: str
    final_path: str


class ContinuityFact(BaseModel):
    id: int
    project_id: int
    chapter_id: Optional[int]
    fact_type: str
    subject: str
    fact: str
    status: str
    created_at: str
    chapter_number: Optional[int] = None  # joined from chapters table when available


class QAReport(BaseModel):
    id: int
    project_id: int
    chapter_id: Optional[int]
    report_type: str
    score: int          # 0–100, 0 = not scored
    report_markdown: str
    created_at: str


class ExportOptions(BaseModel):
    include_summaries: bool = False
    include_chapter_headings: bool = True


class ExportResult(BaseModel):
    path: str
    absolute_path: str
    chapter_count: int
    word_count: int
    chapters_included: list[int]


class ExportStatus(BaseModel):
    exists: bool
    path: str = ""
    absolute_path: str = ""
    word_count: int = 0
    modified_at: str = ""
    approved_chapters: int = 0
    total_chapters: int = 0
