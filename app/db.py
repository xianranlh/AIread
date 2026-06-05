"""SQLite 存储层：单文件、WAL 模式、FTS5 搜索（trigram 对中文友好）。"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id TEXT UNIQUE,            -- canonical url 的 sha1，跨源去重锚点
  source      TEXT NOT NULL,
  title       TEXT NOT NULL,
  url         TEXT NOT NULL,
  summary     TEXT,
  metrics     TEXT DEFAULT '{}',      -- json: stars/points/作者等
  category    TEXT,
  tags        TEXT DEFAULT '[]',      -- json array
  score       REAL,
  score_reason TEXT,
  status      TEXT DEFAULT 'raw',     -- raw|dropped|scored|selected|explained
  drop_reason TEXT,
  simhash     INTEGER,
  embedding   BLOB,
  run_date    TEXT,                   -- YYYY-MM-DD（属于哪天的雷达）
  fetched_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_items_run_date ON items(run_date);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);

CREATE TABLE IF NOT EXISTS explanations (
  item_id    INTEGER PRIMARY KEY REFERENCES items(id),
  content    TEXT NOT NULL,           -- json：结构化讲解
  model      TEXT,
  tokens_in  INTEGER DEFAULT 0,
  tokens_out INTEGER DEFAULT 0,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS weekly_digests (
  week       TEXT PRIMARY KEY,        -- 如 2026-W23
  content_md TEXT NOT NULL,
  model      TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at  TEXT,
  finished_at TEXT,
  ok          INTEGER DEFAULT 0,
  stats       TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS materials (
  item_id    INTEGER PRIMARY KEY REFERENCES items(id),
  content    TEXT NOT NULL,        -- 讲解时收集的原始材料（问答 RAG 复用）
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS notes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  title      TEXT,
  source_url TEXT,
  item_id    INTEGER,
  content_md TEXT NOT NULL,
  model      TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_questions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  domain     TEXT NOT NULL,        -- java|python|ai|agent|scene
  category   TEXT,                 -- 基础|进阶|场景设计
  question   TEXT NOT NULL,
  answer_md  TEXT,
  source     TEXT DEFAULT 'seed',  -- seed|ai
  starred    INTEGER DEFAULT 0,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_quiz_domain ON quiz_questions(domain);

CREATE TABLE IF NOT EXISTS quiz_cards (  -- FSRS 卡片状态（每题一卡）
  question_id    INTEGER PRIMARY KEY REFERENCES quiz_questions(id),
  state          INTEGER DEFAULT 0,   -- 0New 1Learning 2Review 3Relearning
  stability      REAL DEFAULT 0,
  difficulty     REAL DEFAULT 0,
  due            TEXT,
  last_review    TEXT,
  reps           INTEGER DEFAULT 0,
  lapses         INTEGER DEFAULT 0,
  scheduled_days REAL DEFAULT 0,
  elapsed_days   REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_quiz_due ON quiz_cards(due);

CREATE TABLE IF NOT EXISTS quiz_reviews (  -- 复习日志（进度/复盘/时间轴）
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id  INTEGER REFERENCES quiz_questions(id),
  rating       INTEGER,             -- 1忘了 2困难 3记得 4简单
  state_before INTEGER,
  due_after    TEXT,
  reviewed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_quiz_reviews_at ON quiz_reviews(reviewed_at);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,   -- 如 llm.scorer.provider
  value TEXT
);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
  title, summary, explain_text, tokenize='trigram'
);
"""


def get_db_path() -> str:
    return get_settings().db_path


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    try:
        conn.executescript(FTS_SCHEMA)
    except sqlite3.OperationalError:
        # 老版本 SQLite 不支持 trigram，搜索会退化为 LIKE
        pass
    conn.commit()


@contextmanager
def db():
    conn = connect()
    init_db(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def fts_available(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items_fts'"
    ).fetchone()
    return row is not None


def fts_index_item(conn: sqlite3.Connection, item_id: int, title: str,
                   summary: str | None, explain_text: str | None) -> None:
    if not fts_available(conn):
        return
    conn.execute("DELETE FROM items_fts WHERE rowid=?", (item_id,))
    conn.execute(
        "INSERT INTO items_fts(rowid, title, summary, explain_text) VALUES (?,?,?,?)",
        (item_id, title, summary or "", explain_text or ""),
    )


def search_items(conn: sqlite3.Connection, q: str, limit: int = 50) -> list[sqlite3.Row]:
    q = q.strip()
    if not q:
        return []
    if fts_available(conn) and len(q) >= 3:  # trigram 需要至少 3 字符
        try:
            return conn.execute(
                """SELECT i.* FROM items_fts f JOIN items i ON i.id = f.rowid
                   WHERE items_fts MATCH ? ORDER BY rank LIMIT ?""",
                (q.replace('"', " "), limit),
            ).fetchall()
        except sqlite3.OperationalError:
            pass
    like = f"%{q}%"
    return conn.execute(
        """SELECT * FROM items WHERE status IN ('selected','explained')
           AND (title LIKE ? OR summary LIKE ?) ORDER BY run_date DESC LIMIT ?""",
        (like, like, limit),
    ).fetchall()


def get_setting(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_explanation(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM explanations WHERE item_id=?", (item_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["content"] = json.loads(d["content"])
    return d
