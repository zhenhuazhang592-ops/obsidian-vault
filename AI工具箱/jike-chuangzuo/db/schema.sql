-- 即刻创作 · SQLite Schema v1.0
-- 11 tables: project / storyline / outline / asset / segment / shot / image / video / config / prompts / chat_history

CREATE TABLE IF NOT EXISTS t_project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'short_drama',
    art_style TEXT DEFAULT 'cyber_ink',
    video_ratio TEXT DEFAULT '16:9',
    status TEXT DEFAULT 'draft',
    create_time TEXT DEFAULT (datetime('now')),
    update_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_storyline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES t_project(id),
    name TEXT,
    content TEXT NOT NULL,
    chapter_range TEXT,
    state TEXT DEFAULT 'draft',
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_outline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES t_project(id),
    episode_index INTEGER NOT NULL,
    title TEXT,
    data TEXT NOT NULL,
    state TEXT DEFAULT 'draft',
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES t_project(id),
    name TEXT NOT NULL,
    intro TEXT,
    type TEXT NOT NULL,
    prompt TEXT,
    remark TEXT,
    video_prompt TEXT,
    image_path TEXT,
    state TEXT DEFAULT 'draft',
    episode TEXT,
    duration INTEGER,
    file_path TEXT,
    shot_refs TEXT,
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_segment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storyboard_id INTEGER NOT NULL,
    "index" INTEGER NOT NULL,
    content TEXT NOT NULL,
    emotion TEXT,
    action TEXT,
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_shot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL REFERENCES t_segment(id),
    "index" INTEGER NOT NULL,
    title TEXT,
    fragment_content TEXT,
    prompt TEXT,
    motion_prompt TEXT,
    image_path TEXT,
    duration REAL DEFAULT 3.0,
    assets_tags TEXT,
    state TEXT DEFAULT 'pending',
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shot_id INTEGER NOT NULL REFERENCES t_shot(id),
    file_path TEXT,
    type TEXT DEFAULT 'shot',
    state TEXT DEFAULT 'pending',
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_video (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shot_id INTEGER NOT NULL REFERENCES t_shot(id),
    file_path TEXT,
    model TEXT,
    duration REAL,
    state TEXT DEFAULT 'pending',
    error_reason TEXT,
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    model TEXT NOT NULL,
    api_key TEXT,
    base_url TEXT,
    manufacturer TEXT,
    create_time TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS t_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT,
    type TEXT,
    default_value TEXT NOT NULL,
    custom_value TEXT,
    parent_code TEXT
);

CREATE TABLE IF NOT EXISTS t_chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    project_id INTEGER REFERENCES t_project(id),
    messages TEXT NOT NULL,
    create_time TEXT DEFAULT (datetime('now'))
);
