"""Web 站点：FastAPI + Jinja2 服务端渲染，直读 SQLite。"""
import json
import secrets
from datetime import datetime
from pathlib import Path

import markdown as md
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import connect, init_db, get_explanation, search_items
from app.explainer.related import find_related
from app.llm.config import ROLES, mask_key, resolve_role, save_role
from app.llm.providers import make_client
from app.models import CATEGORIES

BASE = Path(__file__).parent
app = FastAPI(title="AI 技术雷达")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def render_md(text: str) -> str:
    return md.markdown(text or "", extensions=["fenced_code", "tables"])


templates.env.filters["md"] = render_md
templates.env.filters["loads"] = lambda s: json.loads(s or "{}")


def ctx(request: Request, **kw) -> dict:
    s = get_settings()
    return {"request": request, "site_title": s.site_title, "categories": CATEGORIES, **kw}


def render(name: str, context: dict, status_code: int = 200):
    """兼容新版 starlette 的 TemplateResponse(request, name, ...) 签名。"""
    return templates.TemplateResponse(
        context["request"], name, context, status_code=status_code)


def _conn():
    conn = connect()
    init_db(conn)
    return conn


def _rows_to_items(conn, rows) -> list[dict]:
    items = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["metrics"] = json.loads(d.get("metrics") or "{}")
        exp = get_explanation(conn, d["id"])
        d["explanation"] = exp["content"] if exp else None
        items.append(d)
    return items


def _date_nav(conn, current: str):
    """返回 (更早一天, 更新一天)。"""
    rows = conn.execute(
        """SELECT DISTINCT run_date AS d FROM items
           WHERE status IN ('selected','explained') ORDER BY run_date"""
    ).fetchall()
    dates = [r["d"] for r in rows]
    if current not in dates:
        return None, None
    i = dates.index(current)
    return (dates[i - 1] if i > 0 else None,
            dates[i + 1] if i < len(dates) - 1 else None)


def _day_page(request: Request, conn, run_date: str | None, deep: int,
              archive_mode: bool, total):
    items = []
    prev_date = next_date = None
    if run_date:
        rows = conn.execute(
            """SELECT * FROM items WHERE run_date=? AND status IN ('selected','explained')
               ORDER BY (status='explained') DESC, score DESC""",
            (run_date,),
        ).fetchall()
        if deep:
            rows = [r for r in rows if r["status"] == "explained"]
        items = _rows_to_items(conn, rows)
        prev_date, next_date = _date_nav(conn, run_date)
    return render("index.html", ctx(
        request, run_date=run_date, items=items, total=total,
        archive_mode=archive_mode, deep=deep,
        prev_date=prev_date, next_date=next_date))


@app.get("/", response_class=HTMLResponse)
def index(request: Request, deep: int = Query(0, ge=0, le=1)):
    conn = _conn()
    try:
        latest = conn.execute(
            "SELECT MAX(run_date) AS d FROM items WHERE status IN ('selected','explained')"
        ).fetchone()
        run_date = latest["d"] if latest else None
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM items WHERE status IN ('selected','explained')"
        ).fetchone()["n"]
        return _day_page(request, conn, run_date, deep, False, total)
    finally:
        conn.close()


@app.get("/archive/{run_date}", response_class=HTMLResponse)
def archive_day(request: Request, run_date: str, deep: int = Query(0, ge=0, le=1)):
    conn = _conn()
    try:
        return _day_page(request, conn, run_date, deep, True, None)
    finally:
        conn.close()


@app.get("/item/{item_id}", response_class=HTMLResponse)
def item_detail(request: Request, item_id: int):
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not row:
            return render("404.html", ctx(request), status_code=404)
        items = _rows_to_items(conn, [row])
        related = find_related(conn, item_id)
        # 同一天内按排序的上一篇/下一篇
        sibs = conn.execute(
            """SELECT id, title FROM items
               WHERE run_date=? AND status IN ('selected','explained')
               ORDER BY (status='explained') DESC, score DESC""",
            (row["run_date"],),
        ).fetchall()
        prev_item = next_item = None
        for i, sb in enumerate(sibs):
            if sb["id"] == item_id:
                if i > 0:
                    prev_item = sibs[i - 1]
                if i < len(sibs) - 1:
                    next_item = sibs[i + 1]
                break
        return render("item.html", ctx(
            request, item=items[0], related=related,
            prev_item=prev_item, next_item=next_item))
    finally:
        conn.close()


@app.get("/archive", response_class=HTMLResponse)
def archive(request: Request):
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT run_date, COUNT(*) AS n,
                      SUM(status='explained') AS explained
               FROM items WHERE status IN ('selected','explained')
               GROUP BY run_date ORDER BY run_date DESC LIMIT 120"""
        ).fetchall()
        return render("archive.html", ctx(request, days=rows))
    finally:
        conn.close()


@app.get("/category/{name}", response_class=HTMLResponse)
def by_category(request: Request, name: str, page: int = Query(1, ge=1)):
    conn = _conn()
    try:
        per, off = 30, (page - 1) * 30
        rows = conn.execute(
            """SELECT * FROM items WHERE category=? AND status IN ('selected','explained')
               ORDER BY run_date DESC, score DESC LIMIT ? OFFSET ?""",
            (name, per, off),
        ).fetchall()
        return render("listing.html", ctx(
            request, heading=f"分类 · {name}", items=_rows_to_items(conn, rows),
            page=page, base_url=f"/category/{name}", active_cat=name))
    finally:
        conn.close()


@app.get("/tag/{name}", response_class=HTMLResponse)
def by_tag(request: Request, name: str, page: int = Query(1, ge=1)):
    conn = _conn()
    try:
        per, off = 30, (page - 1) * 30
        rows = conn.execute(
            """SELECT * FROM items WHERE tags LIKE ? AND status IN ('selected','explained')
               ORDER BY run_date DESC, score DESC LIMIT ? OFFSET ?""",
            (f'%"{name}"%', per, off),
        ).fetchall()
        return render("listing.html", ctx(
            request, heading=f"标签 · {name}", items=_rows_to_items(conn, rows),
            page=page, base_url=f"/tag/{name}"))
    finally:
        conn.close()


@app.get("/weekly", response_class=HTMLResponse)
def weekly_list(request: Request):
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT week, created_at FROM weekly_digests ORDER BY week DESC"
        ).fetchall()
        return render("weekly_list.html", ctx(request, weeks=rows))
    finally:
        conn.close()


@app.get("/weekly/{week}", response_class=HTMLResponse)
def weekly_detail(request: Request, week: str):
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM weekly_digests WHERE week=?", (week,)
        ).fetchone()
        if not row:
            return render("404.html", ctx(request), status_code=404)
        return render("weekly.html", ctx(
            request, week=row["week"], content=render_md(row["content_md"])))
    finally:
        conn.close()


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    conn = _conn()
    try:
        rows = search_items(conn, q) if q else []
        return render("listing.html", ctx(
            request, heading=f"搜索 · {q}" if q else "搜索",
            items=_rows_to_items(conn, rows), search_q=q,
            page=1, base_url="/search"))
    finally:
        conn.close()


@app.get("/feed.xml")
def rss():
    s = get_settings()
    conn = _conn()
    try:
        rows = conn.execute(
            """SELECT i.*, e.content FROM items i
               JOIN explanations e ON e.item_id = i.id
               WHERE i.status='explained' ORDER BY i.run_date DESC, i.score DESC LIMIT 50"""
        ).fetchall()
        entries = []
        for r in rows:
            exp = json.loads(r["content"])
            desc = f"{exp.get('one_liner','')}\n\n{exp.get('problem','')}\n\n{exp.get('verdict','')}"
            entries.append(f"""  <item>
    <title>{_x(r['title'])}</title>
    <link>{s.site_url}/item/{r['id']}</link>
    <guid isPermaLink="false">radar-{r['id']}</guid>
    <pubDate>{_rfc822(r['run_date'])}</pubDate>
    <description>{_x(desc)}</description>
  </item>""")
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{_x(s.site_title)}</title>
  <link>{s.site_url}</link>
  <description>AI 自动拉取并讲解的 GitHub 热门项目与 AI 前沿技术</description>
{chr(10).join(entries)}
</channel></rss>"""
        return Response(content=xml, media_type="application/rss+xml")
    finally:
        conn.close()


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    conn = _conn()
    try:
        run = conn.execute(
            "SELECT * FROM runs WHERE ok=1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        stats = json.loads(run["stats"]) if run else {}
        return render("about.html", ctx(request, last_run=run, stats=stats))
    finally:
        conn.close()


@app.get("/healthz")
def healthz():
    return {"ok": True}


# ---------- 管理区（HTTP Basic 认证，用户名 admin）----------
_security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    s = get_settings()
    if not s.admin_password:
        raise HTTPException(403, "未设置 ADMIN_PASSWORD，管理功能已禁用（在 .env 中配置后重启）")
    user_ok = secrets.compare_digest(credentials.username.encode(), b"admin")
    pwd_ok = secrets.compare_digest(credentials.password.encode(), s.admin_password.encode())
    if not (user_ok and pwd_ok):
        raise HTTPException(401, "认证失败", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, _: str = Depends(require_admin), saved: int = 0):
    roles = {}
    for role in ROLES:
        cfg = resolve_role(role)
        roles[role] = {
            "provider": cfg.provider, "model": cfg.model,
            "base_url": cfg.base_url, "key_mask": mask_key(cfg.api_key),
        }
    return render("settings.html", ctx(request, roles=roles, saved=saved))


@app.post("/settings/save")
async def settings_save(request: Request, _: str = Depends(require_admin)):
    form = dict(await request.form())
    for role in ROLES:
        save_role(form, role)
    return RedirectResponse("/settings?saved=1", status_code=303)


@app.post("/settings/test/{role}")
def settings_test(role: str, _: str = Depends(require_admin)):
    if role not in ROLES:
        raise HTTPException(404)
    cfg = resolve_role(role)
    try:
        client = make_client(cfg)
        resp = client.complete("你是连接测试助手。", "连接测试：请只回复 OK", max_tokens=16)
        return {"ok": True, "model": cfg.label(),
                "reply": resp.text.strip()[:50] or "(空回复)"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "model": cfg.label(), "error": str(e)[:300]}


@app.post("/item/{item_id}/ask")
async def item_ask(item_id: int, request: Request, _: str = Depends(require_admin)):
    """详情页问答：基于讲解时存档的材料回答（RAG）。"""
    try:
        data = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "需要 JSON body")
    question = (data.get("question") or "").strip()[:500]
    if not question:
        raise HTTPException(400, "问题为空")
    conn = _conn()
    try:
        item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise HTTPException(404)
        parts = [f"标题: {item['title']}", f"链接: {item['url']}",
                 f"简介: {item['summary'] or ''}"]
        exp = get_explanation(conn, item_id)
        if exp:
            parts.append("已有讲解: " + json.dumps(exp["content"], ensure_ascii=False))
        mat = conn.execute(
            "SELECT content FROM materials WHERE item_id=?", (item_id,)
        ).fetchone()
        if mat:
            parts.append("原始材料:\n" + mat["content"][:20000])
    finally:
        conn.close()
    from app.llm.router import get_explainer
    system = ("你是 AI 技术雷达的问答助手。仅基于提供的材料回答关于该条目的问题："
              "中文、直接、简洁；材料没有的信息明确说「材料中没有提到」，不要编造。可用 markdown。")
    try:
        resp = get_explainer().complete(
            system, "\n".join(parts) + f"\n\n用户问题：{question}",
            max_tokens=get_settings().ask_max_tokens)
        return {"ok": True, "answer_html": render_md(resp.text), "model": resp.model}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}


PRICES = {  # USD / 1M tokens (输入, 输出)，仅供估算
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus": (5.0, 25.0),
    "deepseek": (0.3, 1.2),
}


def _price_for(model: str):
    for k, v in PRICES.items():
        if model and model.startswith(k):
            return v
    return None


@app.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        # 最近运行
        runs = []
        for r in conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 30").fetchall():
            st = {}
            try:
                st = json.loads(r["stats"] or "{}")
            except json.JSONDecodeError:
                pass
            dur = ""
            try:
                t0 = datetime.fromisoformat(r["started_at"])
                t1 = datetime.fromisoformat(r["finished_at"])
                dur = f"{(t1 - t0).seconds // 60}分{(t1 - t0).seconds % 60}秒"
            except (TypeError, ValueError):
                pass
            tok = st.get("tokens", {})
            runs.append({
                "at": (r["started_at"] or "")[:16].replace("T", " "),
                "ok": r["ok"], "dur": dur,
                "collected": st.get("collected", "-"), "inserted": st.get("inserted", "-"),
                "selected": st.get("selected", "-"), "explained": st.get("explained", "-"),
                "tin": tok.get("in", 0), "tout": tok.get("out", 0),
            })
        # 按模型累计用量与成本估算
        agg: dict = {}
        for r in conn.execute("SELECT stats FROM runs WHERE ok=1").fetchall():
            try:
                bm = json.loads(r["stats"]).get("tokens", {}).get("by_model", {})
            except (json.JSONDecodeError, AttributeError):
                continue
            for m, v in bm.items():
                a = agg.setdefault(m, {"in": 0, "out": 0})
                a["in"] += v.get("in", 0)
                a["out"] += v.get("out", 0)
        models = []
        total_cost = 0.0
        for m, v in sorted(agg.items()):
            price = _price_for(m)
            cost = None
            if price:
                cost = v["in"] / 1e6 * price[0] + v["out"] / 1e6 * price[1]
                total_cost += cost
            models.append({"model": m, "tin": v["in"], "tout": v["out"],
                           "cost": f"${cost:.2f}" if cost is not None else "—"})
        # 数据源健康（近7天）
        src_rows = conn.execute(
            """SELECT source, COUNT(*) AS n FROM items
               WHERE run_date >= date('now','-7 day') GROUP BY source ORDER BY n DESC"""
        ).fetchall()
        src_max = max([r["n"] for r in src_rows], default=1)
        sources = [{"source": r["n"] and r["source"], "n": r["n"],
                    "pct": round(r["n"] / src_max * 100)} for r in src_rows]
        # 每日趋势（近14天）
        trend_rows = conn.execute(
            """SELECT run_date, COUNT(*) AS n, SUM(status='explained') AS ex
               FROM items WHERE status IN ('selected','explained')
               GROUP BY run_date ORDER BY run_date DESC LIMIT 14"""
        ).fetchall()
        t_max = max([r["n"] for r in trend_rows], default=1)
        trend = [{"date": r["run_date"], "n": r["n"], "ex": r["ex"] or 0,
                  "pct": round(r["n"] / t_max * 100)} for r in reversed(trend_rows)]
        return render("stats.html", ctx(
            request, runs=runs, models=models,
            total_cost=f"${total_cost:.2f}", sources=sources, trend=trend))
    finally:
        conn.close()


def _x(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rfc822(d: str) -> str:
    try:
        return datetime.fromisoformat(d).strftime("%a, %d %b %Y 08:00:00 +0800")
    except (ValueError, TypeError):
        return ""
