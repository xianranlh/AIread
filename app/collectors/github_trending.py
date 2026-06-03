"""爬取 github.com/trending（官方无 API，HTML 结构多年稳定）。"""
import re

from bs4 import BeautifulSoup

from app.config import get_settings
from app.collectors.base import Collector, http_client
from app.models import RawItem


def _parse_int(text: str) -> int:
    return int(re.sub(r"[^\d]", "", text) or 0)


class GithubTrendingCollector(Collector):
    name = "github_trending"

    def fetch(self) -> list[RawItem]:
        s = get_settings()
        # 总榜 + 指定语言榜，daily
        targets = [""] + [f"/{lang.strip()}" for lang in s.collect_languages.split(",") if lang.strip()]
        seen: dict[str, RawItem] = {}
        with http_client() as client:
            for t in targets:
                resp = client.get(f"https://github.com/trending{t}?since=daily")
                resp.raise_for_status()
                for item in self._parse(resp.text):
                    seen.setdefault(item.url, item)
        return list(seen.values())

    def _parse(self, html: str) -> list[RawItem]:
        soup = BeautifulSoup(html, "html.parser")
        items = []
        for article in soup.select("article.Box-row"):
            a = article.select_one("h2 a")
            if not a or not a.get("href"):
                continue
            repo = a["href"].strip("/")
            desc_el = article.select_one("p")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            lang_el = article.select_one('[itemprop="programmingLanguage"]')
            stars_total = 0
            stars_today = 0
            star_link = article.select_one(f'a[href="/{repo}/stargazers"]')
            if star_link:
                stars_total = _parse_int(star_link.get_text())
            today_el = article.select_one("span.d-inline-block.float-sm-right")
            if today_el:
                stars_today = _parse_int(today_el.get_text())
            items.append(RawItem(
                source=self.name,
                title=repo,
                url=f"https://github.com/{repo}",
                summary=desc,
                metrics={
                    "stars": stars_total,
                    "stars_today": stars_today,
                    "language": lang_el.get_text(strip=True) if lang_el else None,
                },
            ))
        return items
