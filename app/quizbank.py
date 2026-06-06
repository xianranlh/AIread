"""八股题库业务层：种子导入、复习队列、统计、复盘材料。"""
import json
import logging
import sqlite3
from datetime import datetime, date
from pathlib import Path

from app import fsrs
from app.db import now_iso

log = logging.getLogger(__name__)

DOMAINS = {"java": "Java", "python": "Python", "ai": "AI 基础",
           "agent": "Agent", "mysql": "MySQL", "linux": "Linux",
           "git": "Git", "scene": "场景设计"}
SEED_PATH = Path(__file__).parent / "quiz_seed.json"


def ensure_seed(conn: sqlite3.Connection) -> int:
    """题库为空时导入种子题，并为每题建 FSRS 卡。返回当前题目总数。
    已存在题库时，回填缺失的 section/ord（JavaGuide 式章节分组）。"""
    n = conn.execute("SELECT COUNT(*) AS n FROM quiz_questions").fetchone()["n"]
    if n:
        _sync_seed(conn)
        return conn.execute("SELECT COUNT(*) AS n FROM quiz_questions").fetchone()["n"]
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for q in data:
        _insert_seed_q(conn, q)
    conn.commit()
    log.info("八股题库种子导入 %d 题", len(data))
    return len(data)


def _insert_seed_q(conn: sqlite3.Connection, q: dict) -> int:
    cur = conn.execute(
        """INSERT INTO quiz_questions(domain, section, ord, category, question,
                                      answer_md, source, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (q["domain"], q.get("section"), q.get("ord", 0), q.get("category", "基础"),
         q["question"], q.get("answer_md", ""), "seed", now_iso()))
    conn.execute("INSERT INTO quiz_cards(question_id, state, due) VALUES (?, 0, ?)",
                 (cur.lastrowid, now_iso()))
    return cur.lastrowid


def _sync_seed(conn: sqlite3.Connection) -> None:
    """让种子文件成为真相源（幂等）：1) 回填已有 seed 题缺失的 section/ord；
    2) 导入种子文件里新增的题（如新领域 MySQL/Linux/Git），不动用户/AI 题与复习进度。"""
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    have = {(r["domain"], r["question"]) for r in conn.execute(
        "SELECT domain, question FROM quiz_questions").fetchall()}
    added = 0
    for q in data:
        key = (q["domain"], q["question"])
        if key in have:  # 已存在 → 回填章节分组（幂等）
            conn.execute(
                "UPDATE quiz_questions SET section=?, ord=?, category=? "
                "WHERE source='seed' AND domain=? AND question=? "
                "AND (section IS NULL OR section='')",
                (q.get("section"), q.get("ord", 0), q.get("category", "基础"),
                 q["domain"], q["question"]))
        else:            # 新题 → 插入并建卡
            _insert_seed_q(conn, q)
            added += 1
    conn.commit()
    if added:
        log.info("种子同步：新增 %d 题", added)


def add_question(conn, domain: str, category: str, question: str,
                 answer_md: str, source: str = "ai", section: str | None = None,
                 ord: int = 0) -> int:
    cur = conn.execute(
        """INSERT INTO quiz_questions(domain, section, ord, category, question,
                                      answer_md, source, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (domain, section, ord, category, question, answer_md, source, now_iso()))
    conn.execute("INSERT INTO quiz_cards(question_id, state, due) VALUES (?, 0, ?)",
                 (cur.lastrowid, now_iso()))
    conn.commit()
    return cur.lastrowid


def grouped_questions(conn, domain: str) -> list[dict]:
    """按 section 分组、ord 递进排序，返回 JavaGuide 式层级结构。
    [{"section": "集合容器", "questions": [row, ...]}, ...]"""
    rows = conn.execute(
        """SELECT q.*, c.state, c.due FROM quiz_questions q
           LEFT JOIN quiz_cards c ON c.question_id = q.id
           WHERE q.domain = ? ORDER BY q.ord, q.id""", (domain,)).fetchall()
    groups: list[dict] = []
    for r in rows:
        sec = r["section"] or "其他"
        if not groups or groups[-1]["section"] != sec:
            groups.append({"section": sec, "questions": []})
        groups[-1]["questions"].append(r)
    return groups


def get_card(conn, qid: int) -> dict | None:
    row = conn.execute("SELECT * FROM quiz_cards WHERE question_id=?", (qid,)).fetchone()
    return dict(row) if row else None


def apply_rating(conn, qid: int, rating: int) -> dict:
    """FSRS 打分 → 更新卡片 + 写复习日志。返回新卡片状态。"""
    card = get_card(conn, qid)
    if not card:
        raise ValueError(f"卡片不存在: {qid}")
    state_before = card["state"]
    new = fsrs.rate(card, rating)
    conn.execute(
        """UPDATE quiz_cards SET state=?, stability=?, difficulty=?, due=?,
           last_review=?, reps=?, lapses=?, scheduled_days=?, elapsed_days=?
           WHERE question_id=?""",
        (new["state"], new["stability"], new["difficulty"], new["due"],
         new["last_review"], new["reps"], new.get("lapses") or 0,
         new["scheduled_days"], new["elapsed_days"], qid))
    conn.execute(
        """INSERT INTO quiz_reviews(question_id, rating, state_before, due_after, reviewed_at)
           VALUES (?,?,?,?,?)""",
        (qid, rating, state_before, new["due"], now_iso()))
    conn.commit()
    return new


def review_queue(conn, new_limit: int = 10, total_limit: int = 50) -> list[int]:
    """复习队列：到期卡（按 due 升序）优先 + 适量新卡。"""
    now = now_iso()
    due = conn.execute(
        """SELECT question_id FROM quiz_cards
           WHERE state != 0 AND due <= ? ORDER BY due LIMIT ?""",
        (now, total_limit)).fetchall()
    ids = [r["question_id"] for r in due]
    if len(ids) < total_limit:
        new = conn.execute(
            """SELECT question_id FROM quiz_cards WHERE state = 0
               ORDER BY question_id LIMIT ?""",
            (min(new_limit, total_limit - len(ids)),)).fetchall()
        ids += [r["question_id"] for r in new]
    return ids


def overview_stats(conn) -> dict:
    now = now_iso()
    today = date.today().isoformat()
    g = lambda sql, *a: conn.execute(sql, a).fetchone()["n"]  # noqa: E731
    total = g("SELECT COUNT(*) AS n FROM quiz_questions")
    due_now = g("SELECT COUNT(*) AS n FROM quiz_cards WHERE state != 0 AND due <= ?", now)
    new_cards = g("SELECT COUNT(*) AS n FROM quiz_cards WHERE state = 0")
    reviewed_today = g("SELECT COUNT(*) AS n FROM quiz_reviews WHERE reviewed_at >= ?", today)
    again_today = g("SELECT COUNT(*) AS n FROM quiz_reviews WHERE reviewed_at >= ? AND rating = 1", today)
    starred = g("SELECT COUNT(*) AS n FROM quiz_questions WHERE starred = 1")
    target = reviewed_today + due_now
    progress = round(reviewed_today / target * 100) if target else 100
    # 各领域状态分布
    domains = []
    for key, label in DOMAINS.items():
        rows = conn.execute(
            """SELECT c.state, COUNT(*) AS n FROM quiz_cards c
               JOIN quiz_questions q ON q.id = c.question_id
               WHERE q.domain = ? GROUP BY c.state""", (key,)).fetchall()
        dist = {0: 0, 1: 0, 2: 0, 3: 0}
        for r in rows:
            dist[r["state"]] = r["n"]
        d_total = sum(dist.values())
        d_due = conn.execute(
            """SELECT COUNT(*) AS n FROM quiz_cards c JOIN quiz_questions q ON q.id=c.question_id
               WHERE q.domain=? AND c.state != 0 AND c.due <= ?""", (key, now)).fetchone()["n"]
        domains.append({"key": key, "label": label, "total": d_total,
                        "dist": dist, "due": d_due})
    return {"total": total, "due_now": due_now, "new_cards": new_cards,
            "reviewed_today": reviewed_today, "again_today": again_today,
            "starred": starred, "progress": progress, "domains": domains}


def today_timeline(conn, limit: int = 100) -> list[dict]:
    """今日复习时间轴节点。"""
    today = date.today().isoformat()
    rows = conn.execute(
        """SELECT r.id, r.question_id, r.rating, r.reviewed_at, q.question, q.domain
           FROM quiz_reviews r JOIN quiz_questions q ON q.id = r.question_id
           WHERE r.reviewed_at >= ? ORDER BY r.id DESC LIMIT ?""",
        (today, limit)).fetchall()
    return [dict(r) for r in rows]


def retro_material(conn) -> str | None:
    """组装今日复盘材料给 LLM。"""
    today = date.today().isoformat()
    rows = conn.execute(
        """SELECT r.rating, q.domain, q.category, q.question
           FROM quiz_reviews r JOIN quiz_questions q ON q.id = r.question_id
           WHERE r.reviewed_at >= ? ORDER BY r.id""", (today,)).fetchall()
    if not rows:
        return None
    from collections import Counter
    by_domain = Counter(DOMAINS.get(r["domain"], r["domain"]) for r in rows)
    by_rating = Counter(r["rating"] for r in rows)
    weak = [f"- [{DOMAINS.get(r['domain'], r['domain'])}] {r['question']}（{fsrs.RATING_NAMES[r['rating']]}）"
            for r in rows if r["rating"] <= 2]
    now_s = now_iso()
    due_tomorrow = conn.execute(
        """SELECT COUNT(*) AS n FROM quiz_cards
           WHERE state != 0 AND due > ? AND due <= datetime(?, '+1 day')""",
        (now_s, now_s)).fetchone()["n"]
    lines = [
        f"日期: {today}",
        f"今日共复习 {len(rows)} 次；评分分布: " + ", ".join(
            f"{fsrs.RATING_NAMES[k]}×{v}" for k, v in sorted(by_rating.items())),
        "各领域复习量: " + ", ".join(f"{k}×{v}" for k, v in by_domain.items()),
        f"明天到期待复习: {due_tomorrow} 题",
        "",
        "答错/困难的题目（薄弱点）:",
        *(weak or ["- 无，全部记得"]),
    ]
    return "\n".join(lines)
