"""Web 站点：FastAPI + Jinja2 服务端渲染，直读 SQLite。"""
import json
import re
import secrets
from datetime import date, datetime
from pathlib import Path

import markdown as md
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.collectors.base import http_client
from app.config import get_settings
from app.db import connect, db, init_db, get_explanation, get_setting, now_iso, search_items, set_setting
from app.explainer.enricher import gather_material
from app.explainer.generator import explain_item
from app.explainer.related import find_related
from app.llm.config import ROLES, mask_key, resolve_role, save_role
from app.llm.providers import make_client
from app.models import CATEGORIES
from app.processors.cleaner import external_id

BASE = Path(__file__).parent
app = FastAPI(title="AI 技术雷达")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


# 笔记库图片等静态资源（存于挂载的数据卷，不打进镜像）
try:
    _lib_assets = Path("/data/lib-assets")
    _lib_assets.mkdir(parents=True, exist_ok=True)
    app.mount("/lib-assets", StaticFiles(directory=_lib_assets), name="lib-assets")
except Exception:  # noqa: BLE001 — 非容器环境（如本地测试）无 /data 时跳过
    pass


def render_md(text: str) -> str:
    return md.markdown(text or "", extensions=["fenced_code", "tables"])


templates.env.filters["md"] = render_md
templates.env.filters["loads"] = lambda s: json.loads(s or "{}")


def ctx(request: Request, **kw) -> dict:
    s = get_settings()
    return {"request": request, "site_title": s.site_title, "categories": CATEGORIES,
            "admin_username": s.admin_username, **kw}


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
        if row["source"] == "library":  # 笔记库条目 → 跳到笔记库浏览页
            return RedirectResponse(f"/library/{item_id}", status_code=307)
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


@app.get("/explanations", response_class=HTMLResponse)
def explanations_list(request: Request, page: int = Query(1, ge=1)):
    """讲解库：所有生成过深度讲解的条目（含手动「讲解仓库」），按生成时间倒序，永久可查。"""
    conn = _conn()
    try:
        per, off = 30, (page - 1) * 30
        rows = conn.execute(
            """SELECT i.* FROM items i JOIN explanations e ON e.item_id = i.id
               ORDER BY e.created_at DESC LIMIT ? OFFSET ?""",
            (per, off),
        ).fetchall()
        note_libs = []
        if page == 1:
            note_libs = [dict(r) for r in conn.execute(
                """SELECT id, title, summary, metrics, fetched_at FROM items
                   WHERE source='library' ORDER BY id DESC""").fetchall()]
        return render("listing.html", ctx(
            request, heading="📚 讲解库（历史讲解）", items=_rows_to_items(conn, rows),
            page=page, base_url="/explanations", note_libs=note_libs))
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


@app.get("/learn", response_class=HTMLResponse)
def learn(request: Request):
    """AI Agent 学习指南（静态 Markdown 渲染）。"""
    text = (BASE / "content" / "agent-learning-guide.md").read_text(encoding="utf-8")
    return render("learn.html", ctx(request, guide_html=render_md(text)))


@app.get("/healthz")
def healthz():
    return {"ok": True}


# ---------- 管理区（HTTP Basic 认证，用户名 admin）----------
_security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    s = get_settings()
    if not s.admin_password:
        raise HTTPException(403, "未设置 ADMIN_PASSWORD，管理功能已禁用（在 .env 中配置后重启）")
    user_ok = secrets.compare_digest(credentials.username.encode(), s.admin_username.encode())
    pwd_ok = secrets.compare_digest(credentials.password.encode(), s.admin_password.encode())
    if not (user_ok and pwd_ok):
        raise HTTPException(401, "认证失败", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def _parse_github(raw: str) -> str | None:
    """从各种形式的 GitHub 地址里抠出 owner/repo。"""
    raw = (raw or "").strip()
    m = re.search(r"github\.com[/:]([^/\s]+)/([^/\s#?]+)", raw)
    if m:
        owner, repo = m.group(1), m.group(2)
    elif re.fullmatch(r"[^/\s]+/[^/\s]+", raw):
        owner, repo = raw.split("/", 1)
    else:
        return None
    repo = repo.removesuffix(".git").rstrip("/")
    return f"{owner}/{repo}" if owner and repo else None


@app.get("/explain", response_class=HTMLResponse)
def explain_form(request: Request):
    return render("explain.html", ctx(request))


@app.post("/explain")
def explain_url(request: Request, url: str = Form(...),
                _: str = Depends(require_admin)):
    """输入 GitHub 仓库地址，调用讲解引擎现场生成一份深度讲解。"""
    full = _parse_github(url)
    if not full:
        return render("explain.html", ctx(
            request, error="无法识别，请输入形如 https://github.com/owner/repo 的地址"))
    canon = f"https://github.com/{full}"

    # 尽量拉一次仓库元数据丰富讲解材料；失败则降级为仅用地址
    title, summary, metrics = full, "", {}
    try:
        s = get_settings()
        headers = {"Accept": "application/vnd.github+json"}
        if s.github_token:
            headers["Authorization"] = f"Bearer {s.github_token}"
        with http_client(headers=headers) as client:
            r = client.get(f"https://api.github.com/repos/{full}")
        if r.status_code == 200:
            d = r.json()
            title = d.get("full_name") or full
            summary = d.get("description") or ""
            metrics = {"stars": d.get("stargazers_count", 0),
                       "language": d.get("language"),
                       "topics": (d.get("topics") or [])[:8]}
        elif r.status_code == 404:
            return render("explain.html", ctx(
                request, error=f"GitHub 上找不到仓库：{full}"))
    except Exception:  # noqa: BLE001
        pass

    conn = _conn()
    try:
        ext = external_id(canon)
        row = conn.execute("SELECT id FROM items WHERE external_id=?", (ext,)).fetchone()
        metrics_json = json.dumps(metrics, ensure_ascii=False)
        if row:
            item_id = row["id"]
            conn.execute(
                "UPDATE items SET title=?, summary=?, metrics=? WHERE id=?",
                (title, summary, metrics_json, item_id))
        else:
            item_id = conn.execute(
                """INSERT INTO items(external_id, source, title, url, summary, metrics,
                                     status, run_date, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (ext, "manual", title, canon, summary, metrics_json,
                 "raw", date.today().isoformat(), now_iso()),
            ).lastrowid
        conn.commit()
        item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        material = gather_material(dict(item))
        if not explain_item(conn, item, material):
            return render("explain.html", ctx(
                request, error="讲解生成失败，请稍后重试或检查模型配置（/settings）"))
        return RedirectResponse(f"/item/{item_id}", status_code=303)
    finally:
        conn.close()


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, _: str = Depends(require_admin), saved: int = 0):
    roles = {}
    for role in ROLES:
        cfg = resolve_role(role)
        roles[role] = {
            "provider": cfg.provider, "model": cfg.model,
            "base_url": cfg.base_url, "key_mask": mask_key(cfg.api_key),
        }
    conn = _conn()
    try:
        guidance = get_setting(conn, "explain.guidance") or ""
    finally:
        conn.close()
    return render("settings.html", ctx(request, roles=roles, saved=saved,
                                       explain_guidance=guidance))


@app.post("/settings/save")
async def settings_save(request: Request, _: str = Depends(require_admin)):
    form = dict(await request.form())
    for role in ROLES:
        save_role(form, role)
    with db() as conn:  # db() 上下文会自动 commit
        set_setting(conn, "explain.guidance", (form.get("explain_guidance") or "").strip())
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


@app.get("/item/{item_id}/annotations")
def annotations_list(item_id: int, note_id: int | None = None):
    """批注（公开可读）。笔记库按 note_id（文件）过滤，讲解页取 note_id 为 NULL 的。"""
    conn = _conn()
    try:
        if note_id is not None:
            rows = conn.execute(
                "SELECT id, quote, occurrence, note, updated_at FROM annotations "
                "WHERE item_id=? AND note_id=? ORDER BY id", (item_id, note_id)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, quote, occurrence, note, updated_at FROM annotations "
                "WHERE item_id=? AND note_id IS NULL ORDER BY id", (item_id,)).fetchall()
        return {"ok": True, "annotations": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.post("/item/{item_id}/annotations")
async def annotations_create(item_id: int, request: Request,
                             _: str = Depends(require_admin)):
    data = await request.json()
    quote = (data.get("quote") or "").strip()
    note = (data.get("note") or "").strip()
    occurrence = int(data.get("occurrence") or 0)
    note_id = data.get("note_id")
    note_id = int(note_id) if note_id else None
    if not quote or not note:
        raise HTTPException(400, "quote 与 note 都不能为空")
    conn = _conn()
    try:
        if not conn.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone():
            raise HTTPException(404)
        ts = now_iso()
        aid = conn.execute(
            """INSERT INTO annotations(item_id, note_id, quote, occurrence, note, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (item_id, note_id, quote[:2000], occurrence, note[:4000], ts, ts)).lastrowid
        conn.commit()
        return {"ok": True, "id": aid, "quote": quote, "occurrence": occurrence, "note": note}
    finally:
        conn.close()


@app.post("/item/{item_id}/annotations/{aid}")
async def annotations_update(item_id: int, aid: int, request: Request,
                             _: str = Depends(require_admin)):
    data = await request.json()
    note = (data.get("note") or "").strip()
    if not note:
        raise HTTPException(400, "note 不能为空")
    conn = _conn()
    try:
        cur = conn.execute(
            "UPDATE annotations SET note=?, updated_at=? WHERE id=? AND item_id=?",
            (note[:4000], now_iso(), aid, item_id))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(404)
        return {"ok": True, "id": aid, "note": note}
    finally:
        conn.close()


@app.delete("/item/{item_id}/annotations/{aid}")
def annotations_delete(item_id: int, aid: int, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        conn.execute("DELETE FROM annotations WHERE id=? AND item_id=?", (aid, item_id))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.post("/translate")
async def translate(request: Request, _: str = Depends(require_admin)):
    """专业名词翻译：把选中的英文/术语翻成中文并一句话解释。"""
    data = await request.json()
    text = (data.get("text") or "").strip()[:500]
    if not text:
        raise HTTPException(400, "text 为空")
    from app.llm.router import get_scorer
    system = ("你是面向中文工程师的技术术语翻译助手。把用户给的英文或中英混合的专业名词/短语翻译成中文："
              "先给中文译名，再用一句话解释它的含义；若本身是中文术语则直接解释其专业含义。"
              "只输出结果，简洁，不要寒暄或重复原词。")
    try:
        resp = get_scorer().complete(system, text, max_tokens=200)
        return {"ok": True, "text": resp.text.strip(), "model": resp.model}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


@app.post("/import-library")
def import_library(request: Request, url: str = Form(...),
                   _: str = Depends(require_admin)):
    """把「知识笔记」类仓库导入为笔记库：抓取所有 .md 文件，按目录浏览（不做 AI 讲解）。"""
    full = _parse_github(url)
    if not full:
        return render("explain.html", ctx(
            request, error="无法识别，请输入形如 https://github.com/owner/repo 的地址"))
    s = get_settings()
    headers = {"Accept": "application/vnd.github+json"}
    if s.github_token:
        headers["Authorization"] = f"Bearer {s.github_token}"
    try:
        with http_client(headers=headers) as client:
            meta = client.get(f"https://api.github.com/repos/{full}")
            if meta.status_code == 404:
                return render("explain.html", ctx(request, error=f"GitHub 上找不到仓库：{full}"))
            meta.raise_for_status()
            branch = meta.json().get("default_branch", "main")
            desc = meta.json().get("description") or ""
            tree = client.get(
                f"https://api.github.com/repos/{full}/git/trees/{branch}?recursive=1")
            tree.raise_for_status()
            paths = [b["path"] for b in tree.json().get("tree", [])
                     if b.get("type") == "blob"
                     and b["path"].lower().endswith((".md", ".markdown"))
                     and (b.get("size") or 0) <= 400_000]
            paths = sorted(paths)[:150]  # 控制规模
            if not paths:
                return render("explain.html", ctx(
                    request, error="该仓库没有可导入的 markdown 文件"))
            files = []
            for p in paths:
                raw = client.get(
                    f"https://raw.githubusercontent.com/{full}/{branch}/{p}")
                if raw.status_code == 200 and raw.text.strip():
                    files.append((p, raw.text))
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        return render("explain.html", ctx(request, error=f"导入失败：{str(e)[:200]}"))
    if not files:
        return render("explain.html", ctx(request, error="所有文件抓取失败，请稍后重试"))

    canon = f"https://github.com/{full}"
    conn = _conn()
    try:
        ext = external_id(canon)
        row = conn.execute("SELECT id FROM items WHERE external_id=?", (ext,)).fetchone()
        metrics_json = json.dumps({"library": True, "file_count": len(files)}, ensure_ascii=False)
        if row:
            item_id = row["id"]
            conn.execute("UPDATE items SET source='library', title=?, summary=?, metrics=? WHERE id=?",
                         (full, desc, metrics_json, item_id))
            conn.execute("DELETE FROM note_files WHERE item_id=?", (item_id,))  # 重新导入则覆盖
            conn.execute("DELETE FROM explanations WHERE item_id=?", (item_id,))  # 笔记库不保留 AI 讲解
        else:
            item_id = conn.execute(
                """INSERT INTO items(external_id, source, title, url, summary, metrics,
                                     status, run_date, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (ext, "library", full, canon, desc, metrics_json,
                 "library", date.today().isoformat(), now_iso())).lastrowid
        for i, (p, content) in enumerate(files):
            conn.execute(
                "INSERT INTO note_files(item_id, path, ord, content) VALUES (?,?,?,?)",
                (item_id, p, i, content))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(f"/library/{item_id}", status_code=303)


def _notes_tree(rows: list) -> dict:
    """把扁平文件路径列表构建成文件夹树：{dirs: {名: 子节点}, files: [{id, name}]}。"""
    root: dict = {"dirs": {}, "files": []}
    for r in rows:
        parts = r["path"].split("/")
        node = root
        for d in parts[:-1]:
            node = node["dirs"].setdefault(d, {"dirs": {}, "files": []})
        node["files"].append({"id": r["id"], "name": parts[-1]})
    return root


@app.get("/library/{item_id}", response_class=HTMLResponse)
def library_view(request: Request, item_id: int, note: int | None = None):
    """笔记库浏览页：左侧目录 / 中间内容 / 右侧批注。"""
    conn = _conn()
    try:
        item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not item:
            raise HTTPException(404)
        toc = conn.execute(
            "SELECT id, path FROM note_files WHERE item_id=? ORDER BY ord", (item_id,)).fetchall()
        if not toc:
            raise HTTPException(404, "该条目不是笔记库")
        cur = None
        if note is not None:
            cur = conn.execute(
                "SELECT * FROM note_files WHERE id=? AND item_id=?", (note, item_id)).fetchone()
        if cur is None:
            cur = conn.execute(
                "SELECT * FROM note_files WHERE item_id=? ORDER BY ord LIMIT 1", (item_id,)).fetchone()
        return render("library.html", ctx(
            request, item=dict(item), tree=_notes_tree(toc), file_count=len(toc),
            current=dict(cur), content_html=render_md(cur["content"])))
    finally:
        conn.close()


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


# ---------- 浮动 AI 笔记助手 ----------
NOTE_SYSTEM = """你是「AI 技术雷达」的学习笔记助手。基于给定上下文，输出一篇结构化 Markdown 学习笔记，结构必须为：

# <简洁标题>
> 来源：<URL>（如有）

## TL;DR
（一句话总结）

## 核心要点
（3-6 条要点列表）

## 详细笔记
（基于上下文展开，白话但技术准确，可用小标题/代码块）

## 延伸问题
（2-3 个值得继续探究的问题）

规则：只基于提供的上下文写作，上下文没有的信息不要编造（确需提及标注「待核实」）；全文中文，专有名词保留英文；直接输出 Markdown，不要代码围栏包裹。"""

NOTE_ROLE_LABELS = {"explainer": "精讲模型", "scorer": "粗筛模型", "fallback": "兜底模型"}


@app.get("/api/models")
def api_models():
    """浮动助手的模型下拉（公开，只暴露角色与模型名，不含密钥）。"""
    out = []
    for role in ("explainer", "scorer", "fallback"):
        cfg = resolve_role(role)
        out.append({"role": role, "label": NOTE_ROLE_LABELS[role],
                    "model": cfg.model, "provider": cfg.provider})
    return {"models": out}


@app.post("/api/note")
async def api_note(request: Request, _: str = Depends(require_admin)):
    """生成结构化 Markdown 笔记并保存。"""
    try:
        data = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "需要 JSON body")
    role = data.get("role") or "explainer"
    if role not in ROLES:
        raise HTTPException(400, "未知模型角色")
    instruction = (data.get("instruction") or "").strip()[:500]
    selection = (data.get("selection") or "").strip()[:8000]
    page = data.get("page") or {}
    title = (page.get("title") or "")[:200]
    url = (page.get("url") or "")[:500]
    item_id = page.get("item_id")
    parts = [f"页面标题: {title}", f"页面链接: {url}"]
    if item_id:
        conn = _conn()
        try:
            item = conn.execute("SELECT * FROM items WHERE id=?", (int(item_id),)).fetchone()
            if item:
                parts.append(f"条目: {item['title']}\n原始链接: {item['url']}\n简介: {item['summary'] or ''}")
                exp = get_explanation(conn, int(item_id))
                if exp:
                    parts.append("已有讲解: " + json.dumps(exp["content"], ensure_ascii=False))
                mat = conn.execute(
                    "SELECT content FROM materials WHERE item_id=?", (int(item_id),)
                ).fetchone()
                if mat:
                    parts.append("原始材料(节选):\n" + mat["content"][:15000])
        finally:
            conn.close()
    if selection:
        parts.append(f"用户选中的内容:\n{selection}")
    if instruction:
        parts.append(f"用户补充要求: {instruction}")
    from app.llm.router import RoutedLLM
    try:
        resp = RoutedLLM(role).complete(
            NOTE_SYSTEM, "\n\n".join(parts) + "\n\n请输出 Markdown 学习笔记。",
            max_tokens=2000)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:300]}
    md_text = resp.text.strip()
    fence = re.match(r"^```(?:markdown)?\s*(.*?)```\s*$", md_text, re.S)
    if fence:
        md_text = fence.group(1).strip()
    note_title = title or "未命名笔记"
    m = re.match(r"^#\s+(.+)", md_text)
    if m:
        note_title = m.group(1).strip()[:120]
    conn = _conn()
    try:
        cur = conn.execute(
            """INSERT INTO notes(title, source_url, item_id, content_md, model, created_at)
               VALUES (?,?,?,?,?,?)""",
            (note_title, url, item_id, md_text, resp.model, now_iso()))
        conn.commit()
        note_id = cur.lastrowid
    finally:
        conn.close()
    return {"ok": True, "id": note_id, "title": note_title,
            "markdown": md_text, "html": render_md(md_text), "model": resp.model}


@app.get("/notes", response_class=HTMLResponse)
def notes_list(request: Request, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT id, title, source_url, model, created_at FROM notes ORDER BY id DESC LIMIT 200"
        ).fetchall()
        return render("notes.html", ctx(request, notes=rows))
    finally:
        conn.close()


@app.get("/notes/export.md")
def notes_export(_: str = Depends(require_admin)):
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
        parts = [f"<!-- 笔记 #{r['id']} · {r['created_at']} · {r['model']} -->\n\n{r['content_md']}"
                 for r in rows]
        body = "\n\n---\n\n".join(parts) or "# 暂无笔记"
        return Response(content=body, media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="notes-export.md"'})
    finally:
        conn.close()


@app.get("/notes/{note_id}.md")
def note_download(note_id: int, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        return Response(content=row["content_md"], media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="note-{note_id}.md"'})
    finally:
        conn.close()


@app.get("/notes/{note_id}", response_class=HTMLResponse)
def note_view(request: Request, note_id: int, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if not row:
            return render("404.html", ctx(request), status_code=404)
        return render("note_view.html", ctx(
            request, note=row, content=render_md(row["content_md"])))
    finally:
        conn.close()


@app.post("/notes/{note_id}/delete")
def note_delete(note_id: int, _: str = Depends(require_admin)):
    conn = _conn()
    try:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse("/notes", status_code=303)


def _x(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rfc822(d: str) -> str:
    try:
        return datetime.fromisoformat(d).strftime("%a, %d %b %Y 08:00:00 +0800")
    except (ValueError, TypeError):
        return ""


# 八股复习系统路由（置于文件末尾以避免循环导入）
from app.web.quiz import router as quiz_router  # noqa: E402
app.include_router(quiz_router)
