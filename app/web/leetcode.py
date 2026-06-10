"""LeetCode Hot 100 刷题板块：分类入门讲义 + 逐题讲解 + 掌握进度。"""
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.db import now_iso

log = logging.getLogger(__name__)
router = APIRouter()


# 延迟从 main 取共享工具（main 在底部 include 本路由，导入时 main 已定义完成）
def _m():
    from app.web import main as m
    return m


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
        return m.render("leetcode_index.html", m.ctx(
            request,
            cats=[{**dict(c), "total": stat.get(c["slug"], (0, 0))[0],
                   "done": stat.get(c["slug"], (0, 0))[1]} for c in cats],
            total=total, done=done, next_p=dict(nxt) if nxt else None))


@router.get("/leetcode/cat/{slug}", response_class=HTMLResponse)
def lc_category(request: Request, slug: str):
    m = _m()
    with m._conn() as conn:
        cat = conn.execute("SELECT * FROM lc_categories WHERE slug=?", (slug,)).fetchone()
        if not cat:
            raise HTTPException(404, "分类不存在")
        probs = conn.execute(
            "SELECT id, ord, lc_id, title, difficulty, done FROM lc_problems "
            "WHERE category=? ORDER BY ord", (slug,)).fetchall()
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
        return m.render("leetcode_problem.html", m.ctx(
            request, p=dict(p), cat=dict(cat) if cat else None,
            content_html=m.render_md(p["content"] or "（讲义生成中…）"),
            prev=dict(prev) if prev else None, nxt=dict(nxt) if nxt else None,
            siblings=[dict(s) for s in siblings]))


@router.post("/leetcode/p/{pid}/toggle")
def lc_toggle(request: Request, pid: int):
    m = _m()
    with m._conn() as conn:
        p = conn.execute("SELECT done FROM lc_problems WHERE id=?", (pid,)).fetchone()
        if not p:
            raise HTTPException(404, "题目不存在")
        conn.execute("UPDATE lc_problems SET done=?, done_at=? WHERE id=?",
                     (0 if p["done"] else 1, now_iso(), pid))
        conn.commit()
    return RedirectResponse(f"/leetcode/p/{pid}", status_code=303)
