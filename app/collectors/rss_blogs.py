"""官方博客 RSS：OpenAI / Anthropic / DeepMind / HF Blog 等（.env 可增删）。"""
import time
from datetime import datetime, timedelta

import feedparser

from app.config import get_settings
from app.collectors.base import Collector, http_client
from app.models import RawItem


class BlogRssCollector(Collector):
    name = "blog_rss"

    def fetch(self) -> list[RawItem]:
        s = get_settings()
        feeds = [f.strip() for f in s.blog_feeds.split(",") if f.strip()]
        cutoff = datetime.now() - timedelta(days=3)
        items: list[RawItem] = []
        with http_client() as client:
            for feed_url in feeds:
                try:
                    resp = client.get(feed_url)
                    if resp.status_code != 200:
                        continue
                    parsed = feedparser.parse(resp.text)
                except Exception:  # noqa: BLE001
                    continue
                site = parsed.feed.get("title", feed_url)
                for e in parsed.entries[:10]:
                    published = e.get("published_parsed") or e.get("updated_parsed")
                    if published and datetime.fromtimestamp(time.mktime(published)) < cutoff:
                        continue
                    if not e.get("link") or not e.get("title"):
                        continue
                    items.append(RawItem(
                        source=self.name,
                        title=e["title"].strip(),
                        url=e["link"],
                        summary=(e.get("summary") or "")[:800] or None,
                        metrics={"site": site},
                    ))
        return items
