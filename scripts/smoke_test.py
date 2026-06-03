"""端到端冒烟测试：离线 fixtures + Mock LLM 跑通全管线，再验证所有页面。

运行：python scripts/smoke_test.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试环境变量必须在 import app 之前设置
_tmp = tempfile.mkdtemp()
os.environ.update({
    "DB_PATH": os.path.join(_tmp, "test.db"),
    "SCORER_PROVIDER": "mock",
    "EXPLAINER_PROVIDER": "mock",
    "FALLBACK_PROVIDER": "mock",
    "FALLBACK_MODEL": "mock",
    "EMBEDDING_ENABLED": "false",
    "ADMIN_PASSWORD": "test123",
})

from app.models import RawItem  # noqa: E402
import app.pipeline as pipeline  # noqa: E402
import app.weekly as weekly  # noqa: E402

FIXTURES = [
    RawItem(source="github_trending", title="acme/llm-server",
            url="https://github.com/acme/llm-server",
            summary="High-performance LLM inference server with continuous batching",
            metrics={"stars": 5200, "stars_today": 800, "language": "Python"}),
    RawItem(source="github_trending", title="acme/llm-server",
            url="https://github.com/acme/llm-server?utm_source=x",  # 跨源重复（带跟踪参数）
            summary="dup", metrics={"stars": 5200}),
    RawItem(source="hackernews", title="Show HN: We built a tiny RAG framework",
            url="https://example.com/rag", summary="A minimal RAG framework",
            metrics={"points": 320, "hn_id": "123", "hn_url": "https://news.ycombinator.com/item?id=123"}),
    RawItem(source="arxiv", title="Scaling Laws for Sparse Mixture Models",
            url="https://arxiv.org/abs/2606.01234", summary="We study scaling laws..."),
    RawItem(source="github_search", title="foo/awesome-llm",  # 应被黑名单过滤
            url="https://github.com/foo/awesome-llm", summary="curated list"),
    RawItem(source="huggingface", title="模型: acme/whisper-next",
            url="https://huggingface.co/acme/whisper-next",
            summary="pipeline: asr", metrics={"likes": 90, "downloads": 12000}),
    RawItem(source="blog_rss", title="Introducing Frontier Model X",
            url="https://example.org/blog/model-x", summary="Our new model...",
            metrics={"site": "Example Lab"}),
]


def fake_collect_all():
    return list(FIXTURES)


def fake_gather_material(item: dict) -> str:
    return f"标题: {item['title']}\n简介: {item.get('summary') or ''}\n（fixture 材料）"


def main():
    failures: list[str] = []

    # --- 管线（打两次补丁：采集 + 取证都不出网）---
    pipeline.collect_all = fake_collect_all
    pipeline.gather_material = fake_gather_material
    stats = pipeline.run("2026-06-03")
    print("管线统计:", stats)
    assert stats["collected"] == 7, "采集数不对"
    assert stats["cleaned"] == 5, f"清洗后应为 5 条（去掉黑名单+跨源重复），实际 {stats['cleaned']}"
    assert stats["inserted"] == 5
    assert stats["scoring"]["scored"] == 5
    assert stats["selected"] >= 1, "应有精选条目"
    assert stats["explained"] >= 1, "应有讲解生成"

    # --- 再跑一次：全部应被 external_id 去重，不重复入库 ---
    stats2 = pipeline.run("2026-06-03")
    assert stats2["inserted"] == 0, "二次运行不应重复入库"

    # --- 周报 ---
    week = weekly.run()
    assert week, "周报应生成"

    # --- Web 页面 ---
    from fastapi.testclient import TestClient
    from app.web.main import app as web_app
    client = TestClient(web_app)
    pages = ["/", "/archive", "/archive/2026-06-03", "/weekly", f"/weekly/{week}",
             "/search?q=LLM", "/category/开发工具", "/tag/mock",
             "/feed.xml", "/about", "/healthz"]
    # 找一个已讲解条目测详情页
    import sqlite3
    conn = sqlite3.connect(os.environ["DB_PATH"])
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id FROM items WHERE status='explained' LIMIT 1").fetchone()
    if row:
        pages.append(f"/item/{row['id']}")
    pages.append("/item/99999")  # 404 页

    for p in pages:
        r = client.get(p)
        expect = 404 if p == "/item/99999" else 200
        status = "✓" if r.status_code == expect else "✗"
        print(f"{status} {p} -> {r.status_code}")
        if r.status_code != expect:
            failures.append(f"{p} 返回 {r.status_code}")

    # --- 设置页：认证 + 保存 + 实时生效 + 测试连接 ---
    r = client.get("/settings")
    assert r.status_code == 401, f"未认证应 401，实际 {r.status_code}"
    auth = ("admin", "test123")
    r = client.get("/settings", auth=auth)
    assert r.status_code == 200, f"认证后应 200，实际 {r.status_code}"
    # 保存：把 scorer 切到自定义端点
    form = {}
    for role in ("scorer", "explainer", "fallback"):
        form.update({f"{role}_provider": "mock", f"{role}_model": f"mock-{role}",
                     f"{role}_base_url": "", f"{role}_api_key": ""})
    form["scorer_base_url"] = "https://my-endpoint.example/v1"
    r = client.post("/settings/save", data=form, auth=auth, follow_redirects=False)
    assert r.status_code == 303, f"保存应 303 重定向，实际 {r.status_code}"
    from app.llm.config import resolve_role
    cfg = resolve_role("scorer")
    assert cfg.model == "mock-scorer" and cfg.base_url == "https://my-endpoint.example/v1", \
        f"DB 设置未生效: {cfg}"
    # 测试连接
    r = client.post("/settings/test/scorer", auth=auth)
    d = r.json()
    assert d["ok"] and "mock-scorer" in d["model"], f"测试连接失败: {d}"
    print("✓ /settings 认证/保存/实时生效/测试连接")

    # --- /stats 统计页 ---
    assert client.get("/stats").status_code == 401
    assert client.get("/stats", auth=auth).status_code == 200
    # --- 详情页问答（基于存档材料 + Mock LLM）---
    item_id = row["id"]
    r = client.post(f"/item/{item_id}/ask", json={"question": "它是什么？"})
    assert r.status_code == 401, "问答未认证应 401"
    r = client.post(f"/item/{item_id}/ask", json={"question": "它是什么？"}, auth=auth)
    d = r.json()
    assert d["ok"] and d["answer_html"], f"问答失败: {d}"
    # --- 材料已存档（问答 RAG 数据来源）---
    n_mat = conn.execute("SELECT COUNT(*) FROM materials").fetchone()[0]
    assert n_mat >= 1, "讲解时应存档材料"
    # --- deep 过滤 + 日期导航参数 ---
    assert client.get("/?deep=1").status_code == 200
    assert client.get("/archive/2026-06-03?deep=1").status_code == 200
    # --- 推送摘要格式（不出网，仅格式化）---
    from app.notify import _digest, notify_daily
    from app.db import db as dbctx
    with dbctx() as c2:
        out = _digest(c2, "2026-06-03")
        assert out and "acme/llm-server" in out[0] and "<ol>" in out[1], "摘要格式异常"
        skip = notify_daily(c2, "2026-06-03")
        assert "skipped" in skip, "未配置渠道应跳过"
    print("✓ /stats、问答、材料存档、deep 过滤、推送摘要")

    if failures:
        print("\n失败项:", failures)
        sys.exit(1)
    print("\n✅ 冒烟测试全部通过")


if __name__ == "__main__":
    main()
