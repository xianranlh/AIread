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
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_questions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  domain     TEXT NOT NULL,        -- java|python|ai|agent|scene
  section    TEXT,                 -- 章节分组（如「集合容器」「JVM 与类加载」），JavaGuide 式层级
  ord        INTEGER DEFAULT 0,    -- 该 domain 内的递进顺序（由浅入深）
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

CREATE TABLE IF NOT EXISTS annotations (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id    INTEGER NOT NULL REFERENCES items(id),
  note_id    INTEGER,              -- 绑定的笔记库文件（note_files.id）；讲解页为 NULL
  quote      TEXT NOT NULL,        -- 选中的原文（用于定位高亮）
  occurrence INTEGER DEFAULT 0,    -- 同段内第几次出现（从0计），消歧
  note       TEXT NOT NULL,        -- 批注内容
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_annotations_item ON annotations(item_id);

CREATE TABLE IF NOT EXISTS note_files (   -- 笔记库：导入的 GitHub 仓库 markdown 文件
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL REFERENCES items(id),
  path    TEXT NOT NULL,        -- 仓库内文件路径，作目录
  ord     INTEGER DEFAULT 0,    -- 排序
  content TEXT NOT NULL         -- markdown 原文
);
CREATE INDEX IF NOT EXISTS idx_note_files_item ON note_files(item_id);

CREATE TABLE IF NOT EXISTS lc_categories (  -- LeetCode Hot 100 分类（含小白入门讲义）
  slug  TEXT PRIMARY KEY,
  name  TEXT NOT NULL,
  ord   INTEGER DEFAULT 0,
  intro TEXT                  -- markdown 入门讲义（什么是哈希表/双指针…）
);

CREATE TABLE IF NOT EXISTS lc_problems (    -- LeetCode Hot 100 题目讲义
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  category   TEXT NOT NULL REFERENCES lc_categories(slug),
  ord        INTEGER DEFAULT 0,  -- 全局顺序 1..100（推荐刷题顺序）
  lc_id      INTEGER,            -- 力扣题号
  title      TEXT NOT NULL,
  difficulty TEXT,               -- 简单/中等/困难
  url        TEXT,               -- 力扣题目链接
  content    TEXT,               -- markdown 讲义（题意/思路/双语代码/复杂度）
  done       INTEGER DEFAULT 0,  -- 已掌握标记
  done_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_lc_problems_cat ON lc_problems(category, ord);

CREATE TABLE IF NOT EXISTS lc_cards (  -- 刷题 FSRS 卡片（标记掌握后建卡，每题一卡）
  problem_id     INTEGER PRIMARY KEY REFERENCES lc_problems(id),
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
CREATE INDEX IF NOT EXISTS idx_lc_due ON lc_cards(due);

CREATE TABLE IF NOT EXISTS lc_reviews (  -- 刷题复习日志
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  problem_id   INTEGER REFERENCES lc_problems(id),
  rating       INTEGER,             -- 1忘了 2困难 3记得 4简单
  state_before INTEGER,
  due_after    TEXT,
  reviewed_at  TEXT
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
    # 迁移（必须在建表前）：旧版「笔记库」用的 notes 表(path/ord/content) 改名为 note_files，
    # 把 notes 这个名字让给「我的笔记」(title/content_md/...)。
    ncols = {r["name"] for r in conn.execute("PRAGMA table_info(notes)")}
    if ncols and "path" in ncols and "content_md" not in ncols:  # 旧笔记库表
        if {r["name"] for r in conn.execute("PRAGMA table_info(note_files)")}:
            conn.execute("INSERT INTO note_files(item_id, path, ord, content) "
                         "SELECT item_id, path, ord, content FROM notes")
            conn.execute("DROP TABLE notes")
        else:
            conn.execute("ALTER TABLE notes RENAME TO note_files")
        # 旧笔记库条目 source/status 'notes' → 'library'
        conn.execute("UPDATE items SET source='library', status='library' WHERE source='notes'")
    conn.executescript(SCHEMA)
    try:
        conn.executescript(FTS_SCHEMA)
    except sqlite3.OperationalError:
        # 老版本 SQLite 不支持 trigram，搜索会退化为 LIKE
        pass
    # 轻量迁移：给已存在的 annotations 表补 note_id 列（绑定具体笔记文件；讲解页为 NULL）
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(annotations)")}
    if cols and "note_id" not in cols:
        conn.execute("ALTER TABLE annotations ADD COLUMN note_id INTEGER")
    # 轻量迁移：给已存在的 quiz_questions 补 section/ord（JavaGuide 式章节分组）
    qcols = {r["name"] for r in conn.execute("PRAGMA table_info(quiz_questions)")}
    if qcols:
        if "section" not in qcols:
            conn.execute("ALTER TABLE quiz_questions ADD COLUMN section TEXT")
        if "ord" not in qcols:
            conn.execute("ALTER TABLE quiz_questions ADD COLUMN ord INTEGER DEFAULT 0")
    # 轻量迁移：给已存在的 notes（我的笔记）补 updated_at（编辑功能）
    ncols2 = {r["name"] for r in conn.execute("PRAGMA table_info(notes)")}
    if ncols2 and "updated_at" not in ncols2:
        conn.execute("ALTER TABLE notes ADD COLUMN updated_at TEXT")
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
