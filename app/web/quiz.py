"""八股复习系统路由：题库浏览、FSRS 复习、AI 出题/详解/复盘、星标。"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import fsrs, quizbank
from app.db import now_iso
from app.llm.base import extract_json
from app.llm.router import RoutedLLM, get_explainer

log = logging.getLogger(__name__)
router = APIRouter()

# 延迟从 main 取共享工具（main 在底部 include 本路由，导入时 main 已定义完成）
def _m():
    from app.web import main as m
    return m


GEN_SYSTEM = """你是资深技术面试出题人，为「八股文复习题库」出题。
要求：题目是中文面试高频题，覆盖基础概念与场景设计；答案为要点式 Markdown（列表为主，可含小段代码），准确、精炼、可背诵。
每题给出 section（章节分组名，用于把同主题的题归到一起，如「集合容器」「JVM 与类加载」），尽量复用我给你的已有章节名。
严格输出 JSON 数组，不要任何其他文字：
[{"question": "题目", "section": "章节名", "category": "基础|进阶|场景设计", "answer_md": "- 要点..."}]"""

EXPLAIN_SYSTEM = """你是技术面试教练，请对给定的八股文讲解（八股文讲解任务）。
在参考答案基础上输出更深入的 Markdown 详解：原理展开、常见追问与回答思路、易错点、记忆口诀。
只输出 Markdown 正文，不要重复题目。"""

RETRO_SYSTEM = """你是学习教练，根据今日复习数据写一篇中文复盘笔记（markdown）。
结构：# 八股复盘 <日期> / ## 今日概况（数据总结）/ ## 薄弱点分析（逐条给出该题的核心记忆要点）/ ## 记忆建议 / ## 明日计划。
只基于给定数据，不要编造。"""


def _q_payload(conn, qid: int) -> dict:
    m = _m()
    q = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (qid,)).fetchone()
    if not q:
        raise HTTPException(404, "题目不存在")
    card = quizbank.get_card(conn, qid) or {}
    r = fsrs.card_retrievability(card)
    return {
        "id": q["id"], "domain": q["domain"],
        "domain_label": quizbank.DOMAINS.get(q["domain"], q["domain"]),
        "section": q["section"] or "", "category": q["category"], "question": q["question"],
        "answer_md": q["answer_md"] or "",
        "answer_html": m.render_md(q["answer_md"] or "（暂无参考答案，点「AI 详解」生成）"),
        "starred": bool(q["starred"]), "source": q["source"],
        "card": {
            "state": card.get("state", 0),
            "state_name": fsrs.STATE_NAMES.get(card.get("state", 0), "新题"),
            "due": card.get("due"), "stability": card.get("stability") or 0,
            "difficulty": card.get("difficulty") or 0,
            "reps": card.get("reps") or 0, "lapses": card.get("lapses") or 0,
            "retrievability": round(r, 4) if r is not None else None,
        },
        "preview": fsrs.preview(card) if card else {},
    }


# ---------- 页面 ----------
@router.get("/quiz", response_class=HTMLResponse)
def quiz_overview(request: Request):
    m = _m()
    conn = m._conn()
    try:
        quizbank.ensure_seed(conn)
        stats = quizbank.overview_stats(conn)
        timeline = quizbank.today_timeline(conn)
        for t in timeline:
            t["rating_name"] = fsrs.RATING_NAMES.get(t["rating"], "?")
            t["domain_label"] = quizbank.DOMAINS.get(t["domain"], t["domain"])
        return m.render("quiz.html", m.ctx(
            request, stats=stats, timeline=timeline,
            domains=quizbank.DOMAINS, rating_names=fsrs.RATING_NAMES))
    finally:
        conn.close()


@router.get("/quiz/review", response_class=HTMLResponse)
def quiz_review_page(request: Request):
    m = _m()
    conn = m._conn()
    try:
        quizbank.ensure_seed(conn)
        return m.render("quiz_review.html", m.ctx(request))
    finally:
        conn.close()


@router.get("/quiz/starred", response_class=HTMLResponse)
def quiz_starred(request: Request):
    m = _m()
    conn = m._conn()
    try:
        rows = conn.execute(
            """SELECT q.*, c.state, c.due FROM quiz_questions q
               LEFT JOIN quiz_cards c ON c.question_id=q.id
               WHERE q.starred=1 ORDER BY q.id DESC""").fetchall()
        return m.render("quiz_list.html", m.ctx(
            request, heading="⭐ 星标题目", rows=rows,
            domains=quizbank.DOMAINS, state_names=fsrs.STATE_NAMES))
    finally:
        conn.close()


@router.get("/quiz/domain/{domain}", response_class=HTMLResponse)
def quiz_domain(request: Request, domain: str):
    m = _m()
    if domain not in quizbank.DOMAINS:
        raise HTTPException(404)
    conn = m._conn()
    try:
        quizbank.ensure_seed(conn)
        groups = quizbank.grouped_questions(conn, domain)
        total = sum(len(g["questions"]) for g in groups)
        return m.render("quiz_domain.html", m.ctx(
            request, domain=domain, domain_label=quizbank.DOMAINS[domain],
            groups=groups, total=total, domains=quizbank.DOMAINS,
            state_names=fsrs.STATE_NAMES))
    finally:
        conn.close()


@router.get("/quiz/q/{qid}", response_class=HTMLResponse)
def quiz_question_page(request: Request, qid: int):
    m = _m()
    conn = m._conn()
    try:
        quizbank.ensure_seed(conn)
        payload = _q_payload(conn, qid)
        return m.render("quiz_q.html", m.ctx(request, q=payload,
                                             q_json=json.dumps(payload, ensure_ascii=False)))
    finally:
        conn.close()


# ---------- API ----------
@router.get("/api/quiz/queue")
def api_queue(request: Request):
    m = _m()
    conn = m._conn()
    try:
        quizbank.ensure_seed(conn)
        return {"queue": quizbank.review_queue(conn)}
    finally:
        conn.close()


@router.get("/api/quiz/q/{qid}")
def api_question(qid: int):
    m = _m()
    conn = m._conn()
    try:
        return _q_payload(conn, qid)
    finally:
        conn.close()


@router.post("/api/quiz/rate")
async def api_rate(request: Request, _: str = Depends(lambda: None)):
    m = _m()
    # 评分需管理密码（个人记忆数据）
    await _require_admin_async(request)
    data = await request.json()
    qid, rating = int(data.get("question_id", 0)), int(data.get("rating", 0))
    if rating not in (1, 2, 3, 4):
        raise HTTPException(400, "rating 须为 1-4")
    conn = m._conn()
    try:
        new = quizbank.apply_rating(conn, qid, rating)
        return {"ok": True,
                "card": {"state": new["state"],
                         "state_name": fsrs.STATE_NAMES[new["state"]],
                         "due": new["due"], "stability": new["stability"],
                         "scheduled_days": new["scheduled_days"]},
                "message": f"已记录「{fsrs.RATING_NAMES[rating]}」，下次复习 {new['due'][:16].replace('T',' ')}"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    finally:
        conn.close()


async def _require_admin_async(request: Request):
    """已停用 Basic 认证（个人内网部署，全站免登录）。"""
    return


@router.post("/api/quiz/star/{qid}")
async def api_star(qid: int, request: Request):
    await _require_admin_async(request)
    m = _m()
    conn = m._conn()
    try:
        row = conn.execute("SELECT starred FROM quiz_questions WHERE id=?", (qid,)).fetchone()
        if not row:
            raise HTTPException(404)
        new_val = 0 if row["starred"] else 1
        conn.execute("UPDATE quiz_questions SET starred=? WHERE id=?", (new_val, qid))
        conn.commit()
        return {"ok": True, "starred": bool(new_val)}
    finally:
        conn.close()


@router.post("/api/quiz/explain/{qid}")
async def api_explain(qid: int, request: Request):
    """AI 详解：在参考答案后追加深入讲解。"""
    await _require_admin_async(request)
    m = _m()
    conn = m._conn()
    try:
        q = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (qid,)).fetchone()
        if not q:
            raise HTTPException(404)
        user = f"题目：{q['question']}\n\n现有参考答案：\n{q['answer_md'] or '（无）'}"
    finally:
        conn.close()
    try:
        resp = get_explainer().complete(EXPLAIN_SYSTEM, user, max_tokens=2000)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}
    addition = resp.text.strip()
    conn = m._conn()
    try:
        new_md = (q["answer_md"] or "").rstrip() + "\n\n---\n\n" + addition
        conn.execute("UPDATE quiz_questions SET answer_md=? WHERE id=?", (new_md, qid))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "answer_html": m.render_md(new_md), "model": resp.model}


@router.post("/api/quiz/ask/{qid}")
async def api_quiz_ask(qid: int, request: Request):
    """针对当前题目继续追问（对话节点，可收藏）。"""
    await _require_admin_async(request)
    m = _m()
    data = await request.json()
    question = (data.get("question") or "").strip()[:500]
    role = data.get("role") or "explainer"
    if not question:
        raise HTTPException(400, "问题为空")
    conn = m._conn()
    try:
        q = conn.execute("SELECT * FROM quiz_questions WHERE id=?", (qid,)).fetchone()
        if not q:
            raise HTTPException(404)
        material = f"八股题目：{q['question']}\n\n参考答案：\n{q['answer_md'] or '（无）'}"
    finally:
        conn.close()
    system = ("你是技术面试教练（八股问答）。基于题目与参考答案回答追问：中文、直接、准确；"
              "超出材料范围的可以用通用技术知识回答，但需标注。可用 markdown。")
    try:
        resp = RoutedLLM(role if role in ("explainer", "scorer", "fallback") else "explainer"
                         ).complete(system, material + f"\n\n追问：{question}", max_tokens=1200)
        return {"ok": True, "answer_md": resp.text,
                "answer_html": m.render_md(resp.text), "model": resp.model}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}


@router.post("/api/quiz/save_answer")
async def api_save_answer(request: Request):
    """星标收藏重要回答 → 存入笔记。"""
    await _require_admin_async(request)
    m = _m()
    data = await request.json()
    qid = data.get("question_id")
    title = (data.get("title") or "八股问答收藏")[:120]
    content = (data.get("content_md") or "").strip()
    if not content:
        raise HTTPException(400, "内容为空")
    conn = m._conn()
    try:
        cur = conn.execute(
            """INSERT INTO notes(title, source_url, item_id, content_md, model, created_at)
               VALUES (?,?,?,?,?,?)""",
            (f"⭐ {title}", f"/quiz/q/{qid}" if qid else "", None, content, "quiz-ask", now_iso()))
        conn.commit()
        return {"ok": True, "note_id": cur.lastrowid}
    finally:
        conn.close()


@router.post("/api/quiz/generate")
async def api_generate(request: Request):
    """AI 出题扩充题库。"""
    await _require_admin_async(request)
    m = _m()
    data = await request.json()
    domain = data.get("domain")
    n = min(int(data.get("n") or 5), 10)
    if domain not in quizbank.DOMAINS:
        raise HTTPException(400, "未知领域")
    conn = m._conn()
    try:
        existing = [r["question"] for r in conn.execute(
            "SELECT question FROM quiz_questions WHERE domain=?", (domain,)).fetchall()]
        sections = [r["section"] for r in conn.execute(
            "SELECT DISTINCT section FROM quiz_questions WHERE domain=? AND section IS NOT NULL "
            "ORDER BY ord", (domain,)).fetchall()]
        next_ord = (conn.execute(
            "SELECT COALESCE(MAX(ord), 0) AS m FROM quiz_questions WHERE domain=?",
            (domain,)).fetchone()["m"]) + 1
    finally:
        conn.close()
    user = (f"领域：{quizbank.DOMAINS[domain]}\n出 {n} 道新题。\n"
            f"已有章节（尽量归入这些，不合适再新建）：{', '.join(sections) or '无'}\n"
            f"已有题目（避免重复）：\n" + "\n".join(f"- {q}" for q in existing[:60]))
    try:
        resp = get_explainer().complete(GEN_SYSTEM, user, max_tokens=3000)
        items = extract_json(resp.text)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}
    added = []
    conn = m._conn()
    try:
        for it in items if isinstance(items, list) else []:
            if not it.get("question"):
                continue
            qid = quizbank.add_question(
                conn, domain, it.get("category") or "基础",
                it["question"].strip(), (it.get("answer_md") or "").strip(),
                section=(it.get("section") or "AI 扩充").strip(), ord=next_ord)
            next_ord += 1
            added.append(qid)
    finally:
        conn.close()
    return {"ok": True, "added": len(added), "ids": added, "model": resp.model}


@router.post("/api/quiz/retro")
async def api_retro(request: Request):
    """一键生成今日复盘笔记 → 存入笔记。"""
    await _require_admin_async(request)
    m = _m()
    conn = m._conn()
    try:
        material = quizbank.retro_material(conn)
    finally:
        conn.close()
    if not material:
        return {"ok": False, "error": "今天还没有复习记录，先去复习几题吧"}
    try:
        resp = get_explainer().complete(RETRO_SYSTEM, material, max_tokens=2000)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}
    md_text = resp.text.strip()
    from datetime import date
    conn = m._conn()
    try:
        cur = conn.execute(
            """INSERT INTO notes(title, source_url, item_id, content_md, model, created_at)
               VALUES (?,?,?,?,?,?)""",
            (f"八股复盘 {date.today().isoformat()}", "/quiz", None,
             md_text, resp.model, now_iso()))
        conn.commit()
        nid = cur.lastrowid
    finally:
        conn.close()
    return {"ok": True, "note_id": nid, "html": m.render_md(md_text)}
