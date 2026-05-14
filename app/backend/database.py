import aiosqlite
import os

# Resolve data/ relative to the repo root (two levels up from app/backend/)
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_BACKEND_DIR))
DB_PATH = os.path.join(_REPO_ROOT, "data", "app.db")

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    root_path TEXT NOT NULL,
    target_word_count INTEGER DEFAULT 80000,
    pov TEXT DEFAULT '',
    tense TEXT DEFAULT '',
    genre TEXT DEFAULT '',
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    title TEXT DEFAULT '',
    pov_character TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    target_word_count INTEGER DEFAULT 3000,
    actual_word_count INTEGER DEFAULT 0,
    outline_goal TEXT DEFAULT '',
    outline_conflict TEXT DEFAULT '',
    outline_revelation TEXT DEFAULT '',
    outline_notes TEXT DEFAULT '',
    draft_path TEXT DEFAULT '',
    final_path TEXT DEFAULT '',
    summary_path TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    age TEXT DEFAULT '',
    physical TEXT DEFAULT '',
    core_wound TEXT DEFAULT '',
    internal_flaw TEXT DEFAULT '',
    external_flaw TEXT DEFAULT '',
    motivation TEXT DEFAULT '',
    voice_description TEXT DEFAULT '',
    sample_internal_voice TEXT DEFAULT '',
    arc_begin TEXT DEFAULT '',
    arc_midpoint TEXT DEFAULT '',
    arc_end TEXT DEFAULT '',
    raw_markdown TEXT DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS continuity_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    fact_type TEXT NOT NULL,
    subject TEXT DEFAULT '',
    fact TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS qa_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    chapter_id INTEGER,
    report_type TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    report_markdown TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


def get_db_path() -> str:
    return DB_PATH
