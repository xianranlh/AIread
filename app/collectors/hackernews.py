"""Hacker News：Algolia Search API（免费无需 Key）。前页高分 + AI 关键词搜索。"""
from datetime import datetime, timedelta

from app.config import get_settings
from app.collectors.base import Collector, http_client
from app.models import RawItem

API = "https://hn.algolia.com/api/v1"


class HackerNewsCollector(Collector):
    name = "hackernews"

    def fetch(self) -> list[RawItem]:
        s = get_settings()
        since = int((datetime.now() - timedelta(days=1)).timestamp())
        seen: dict[str, RawItem] = {}
        with http_client() as client:
            # 1) 24h 内高分前页帖
            resp = client.get(f"{API}/search", params={
                "tags": "front_page", "hitsPerPage": 30,
            })
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                item = self._to_item(hit)
                if item:
                    seen.setdefault(item.url, item)
            # 2) AI 关键词近 24h 高分搜索
            for kw in [k.strip() for k in s.hn_query_keywords.split(",") if k.strip()]:
                resp = client.get(f"{API}/search", params={
                    "query": kw, "tags": "story",
                    "numericFilters": f"created_at_i>{since},points>30",
                    "hitsPerPage": 15,
                })
                if resp.status_code != 200:
                    continue
                for hit in resp.json().get("hits", []):
                    item = self._to_item(hit)
                    if item:
                        seen.setdefault(item.url, item)
        return list(seen.values())

    def _to_item(self, hit: dict) -> RawItem | None:
        title = hit.get("title")
        if not title:
            return None
        hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        url = hit.get("url") or hn_url
        return RawItem(
            source=self.name,
            title=title,
            url=url,
            summary=(hit.get("story_text") or "")[:500] or None,
            metrics={
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
                "hn_id": hit.get("objectID"),
                "hn_url": hn_url,
            },
        )
