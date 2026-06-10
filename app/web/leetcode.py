"""LeetCode Hot 100 刷题板块：分类入门讲义 + 逐题讲解 + FSRS 间隔复习。

复习模型：「标记已掌握」= 建 FSRS 卡并打一次「记得」进入复习周期；
之后题目页出现 4 档评分按钮，到期题进入 /leetcode/review 复习队列。
"""
import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import fsrs
from app.db import now_iso

log = logging.getLogger(__name__)
router = APIRouter()


# 延迟从 main 取共享工具（main 在底部 include 本路由，导入时 main 已定义完成）
def _m():
    from app.web import main as m
    return m


def _get_card(conn, pid: int) -> dict | None:
    row = conn.execute("SELECT * FROM lc_cards WHERE problem_id=?", (pid,)).fetchone()
    return dict(row) if row else None


def _apply_rating(conn, pid: int, rating: int) -> dict:
    """FSRS 打分 → 更新卡片 + 写复习日志（与八股 quizbank.apply_rating 同构）。"""
    card = _get_card(conn, pid)
    if not card:
        raise ValueError(f"卡片不存在: {pid}")
    state_before = card["state"]
    new = fsrs.rate(card, rating)
    conn.execute(
        """UPDATE lc_cards SET state=?, stability=?, difficulty=?, due=?,
           last_review=?, reps=?, lapses=?, scheduled_days=?, elapsed_days=?
           WHERE problem_id=?""",
        (new["state"], new["stability"], new["difficulty"], new["due"],
         new["last_review"], new["reps"], new.get("lapses") or 0,
         new["scheduled_days"], new["elapsed_days"], pid))
    conn.execute(
        """INSERT INTO lc_reviews(problem_id, rating, state_before, due_after, reviewed_at)
           VALUES (?,?,?,?,?)""",
        (pid, rating, state_before, new["due"], now_iso()))
    conn.commit()
    return new


def _due_ids(conn) -> list[int]:
    rows = conn.execute(
        "SELECT problem_id FROM lc_cards WHERE due <= ? ORDER BY due", (now_iso(),)).fetchall()
    return [r["problem_id"] for r in rows]


def _card_view(card: dict | None) -> dict | None:
    """卡片状态 + 评分按钮的间隔预览，供模板渲染。"""
    if not card:
        return None
    r = fsrs.card_retrievability(card)
    return {
        "state_name": fsrs.STATE_NAMES.get(card.get("state", 0), "新题"),
        "due": (card.get("due") or "")[:16].replace("T", " "),
        "is_due": bool(card.get("due") and card["due"] <= now_iso()),
        "reps": card.get("reps") or 0,
        "lapses": card.get("lapses") or 0,
        "retrievability": f"{r * 100:.0f}%" if r is not None else None,
        "preview": fsrs.preview(card),
    }


@router.get("/leetcode", response_class=HTMLResponse)
def lc_index(request: Request):
    m = _m()
    with m._conn() as conn:
        cats = conn.execute("SELECT * FROM lc_categories ORDER BY ord").fetchall()
        rows = conn.execute(
            "SELECT category, COUNT(*) AS total, SUM(done) AS done "
            "FROM lc_problems GROUP BY category").fetchall()
        stat = {r["category"]: (r["total"], r["done"] or 0) for r in rows}
        total = sum(t for t, _ in stat.values())
        done = sum(d for _, d in stat.values())
        # 「继续刷题」：全局顺序里第一道未掌握的题
        nxt = conn.execute(
            "SELECT id, title FROM lc_problems WHERE done=0 ORDER BY ord LIMIT 1").fetchone()
        due_count = len(_due_ids(conn))
        return m.render("leetcode_index.html", m.ctx(
            request,
            cats=[{**dict(c), "total": stat.get(c["slug"], (0, 0))[0],
                   "done": stat.get(c["slug"], (0, 0))[1]} for c in cats],
            total=total, done=done, next_p=dict(nxt) if nxt else None,
            due_count=due_count))


@router.get("/leetcode/review", response_class=HTMLResponse)
def lc_review(request: Request):
    """复习队列：跳到第一道到期的题；没有就回总览。"""
    m = _m()
    with m._conn() as conn:
        ids = _due_ids(conn)
    if ids:
        return RedirectResponse(f"/leetcode/p/{ids[0]}", status_code=307)
    return RedirectResponse("/leetcode", status_code=307)


@router.get("/leetcode/cat/{slug}", response_class=HTMLResponse)
def lc_category(request: Request, slug: str):
    m = _m()
    with m._conn() as conn:
        cat = conn.execute("SELECT * FROM lc_categories WHERE slug=?", (slug,)).fetchone()
        if not cat:
            raise HTTPException(404, "分类不存在")
        probs = conn.execute(
            """SELECT p.id, p.ord, p.lc_id, p.title, p.difficulty, p.done,
                      (c.due IS NOT NULL AND c.due <= ?) AS is_due
               FROM lc_problems p LEFT JOIN lc_cards c ON c.problem_id = p.id
               WHERE p.category=? ORDER BY p.ord""", (now_iso(), slug)).fetchall()
        cats = conn.execute("SELECT slug, name FROM lc_categories ORDER BY ord").fetchall()
        return m.render("leetcode_cat.html", m.ctx(
            request, cat=dict(cat), intro_html=m.render_md(cat["intro"] or ""),
            probs=[dict(p) for p in probs], cats=[dict(c) for c in cats]))


@router.get("/leetcode/p/{pid}", response_class=HTMLResponse)
def lc_problem(request: Request, pid: int):
    m = _m()
    with m._conn() as conn:
        p = conn.execute("SELECT * FROM lc_problems WHERE id=?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404, "题目不存在")
        cat = conn.execute("SELECT * FROM lc_categories WHERE slug=?", (p["category"],)).fetchone()
        prev = conn.execute("SELECT id, title FROM lc_problems WHERE ord<? ORDER BY ord DESC LIMIT 1",
                            (p["ord"],)).fetchone()
        nxt = conn.execute("SELECT id, title FROM lc_problems WHERE ord>? ORDER BY ord LIMIT 1",
                           (p["ord"],)).fetchone()
        siblings = conn.execute(
            "SELECT id, title, done FROM lc_problems WHERE category=? ORDER BY ord",
            (p["category"],)).fetchall()
        due_count = len(_due_ids(conn))
        return m.render("leetcode_problem.html", m.ctx(
            request, p=dict(p), cat=dict(cat) if cat else None,
            content_html=m.render_md(p["content"] or "（讲义生成中…）"),
            prev=dict(prev) if prev else None, nxt=dict(nxt) if nxt else None,
            siblings=[dict(s) for s in siblings],
            card=_card_view(_get_card(conn, pid)),
            rating_names=fsrs.RATING_NAMES, due_count=due_count))


@router.post("/leetcode/p/{pid}/toggle")
def lc_toggle(request: Request, pid: int):
    """标记/取消掌握。掌握 = 建 FSRS 卡 + 打「记得」入复习周期；取消 = 删卡。"""
    m = _m()
    with m._conn() as conn:
        p = conn.execute("SELECT done FROM lc_problems WHERE id=?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404, "题目不存在")
        if p["done"]:
            conn.execute("UPDATE lc_problems SET done=0, done_at=NULL WHERE id=?", (pid,))
            conn.execute("DELETE FROM lc_cards WHERE problem_id=?", (pid,))
            conn.commit()
        else:
            conn.execute("UPDATE lc_problems SET done=1, done_at=? WHERE id=?",
                         (now_iso(), pid))
            if not _get_card(conn, pid):
                conn.execute("INSERT INTO lc_cards(problem_id, state, due) VALUES (?, 0, ?)",
                             (pid, now_iso()))
            _apply_rating(conn, pid, fsrs.GOOD)   # 首次掌握按「记得」起步
    return RedirectResponse(f"/leetcode/p/{pid}", status_code=303)


@router.post("/leetcode/p/{pid}/rate")
def lc_rate(request: Request, pid: int, rating: int = Form(...)):
    """FSRS 复习打分（1忘了 2困难 3记得 4简单），打完跳到下一道到期题。"""
    if rating not in (1, 2, 3, 4):
        raise HTTPException(400, "rating 须为 1-4")
    m = _m()
    with m._conn() as conn:
        if not _get_card(conn, pid):
            raise HTTPException(404, "该题还没有复习卡（先标记已掌握）")
        _apply_rating(conn, pid, rating)
        remaining = [i for i in _due_ids(conn) if i != pid]
    if remaining:
        return RedirectResponse(f"/leetcode/p/{remaining[0]}", status_code=303)
    return RedirectResponse(f"/leetcode/p/{pid}", status_code=303)
