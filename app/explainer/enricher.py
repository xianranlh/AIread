"""取证：为待讲解条目抓取一手材料（README / HN 高赞评论 / 摘要）。"""
import logging
import re

from app.config import get_settings
from app.collectors.base import http_client

log = logging.getLogger(__name__)


def _strip_noise(md: str) -> str:
    """README 降噪：去徽章图片、HTML 标签、超长空行。"""
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)          # 图片
    md = re.sub(r"<img[^>]*>", "", md, flags=re.I)
    md = re.sub(r"<[^>]+>", "", md)                        # 其余 HTML 标签
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)       # 链接保留文字
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def fetch_github_readme(repo_full_name: str) -> str:
    s = get_settings()
    headers = {"Accept": "application/vnd.github.raw+json"}
    if s.github_token:
        headers["Authorization"] = f"Bearer {s.github_token}"
    try:
        with http_client(headers=headers) as client:
            resp = client.get(f"https://api.github.com/repos/{repo_full_name}/readme")
            if resp.status_code != 200:
                return ""
            return _strip_noise(resp.text)[: s.readme_max_chars]
    except Exception:  # noqa: BLE001
        log.warning("README 抓取失败: %s", repo_full_name)
        return ""


def fetch_hn_comments(hn_id: str, top_n: int = 5) -> str:
    """取 HN 帖子高赞评论，作为社区视角材料。"""
    try:
        with http_client() as client:
            resp = client.get(f"https://hn.algolia.com/api/v1/items/{hn_id}")
            if resp.status_code != 200:
                return ""
            data = resp.json()
        comments = []
        for child in (data.get("children") or [])[:top_n]:
            text = re.sub(r"<[^>]+>", " ", child.get("text") or "")
            if len(text) > 60:
                comments.append(text[:600])
        return "\n---\n".join(comments)
    except Exception:  # noqa: BLE001
        return ""


def gather_material(item: dict) -> str:
    """根据来源组装讲解材料，控制总长度。"""
    import json
    metrics = json.loads(item["metrics"] or "{}")
    parts = [f"标题: {item['title']}", f"链接: {item['url']}", f"来源: {item['source']}"]
    if item.get("summary"):
        parts.append(f"简介/摘要: {item['summary']}")
    heat = {k: v for k, v in metrics.items()
            if k in ("stars", "stars_today", "points", "upvotes", "likes", "downloads", "language")}
    if heat:
        parts.append(f"热度数据: {json.dumps(heat, ensure_ascii=False)}")

    m = re.match(r"https://github\.com/([^/]+/[^/]+)$", item["url"])
    if m:
        readme = fetch_github_readme(m.group(1))
        if readme:
            parts.append(f"\n===== README =====\n{readme}")
    if metrics.get("hn_id"):
        comments = fetch_hn_comments(str(metrics["hn_id"]))
        if comments:
            parts.append(f"\n===== HN 高赞评论 =====\n{comments}")
    return "\n".join(parts)
