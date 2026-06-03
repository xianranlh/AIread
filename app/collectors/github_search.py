"""GitHub Search API：近 7 天创建的高星新项目（补 Trending 盲区）。"""
from datetime import datetime, timedelta

from app.config import get_settings
from app.collectors.base import Collector, http_client
from app.models import RawItem


class GithubSearchCollector(Collector):
    name = "github_search"

    def fetch(self) -> list[RawItem]:
        s = get_settings()
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        headers = {"Accept": "application/vnd.github+json"}
        if s.github_token:
            headers["Authorization"] = f"Bearer {s.github_token}"
        with http_client(headers=headers) as client:
            resp = client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": f"created:>{since} stars:>100",
                    "sort": "stars", "order": "desc", "per_page": 30,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        items = []
        for repo in data.get("items", []):
            items.append(RawItem(
                source=self.name,
                title=repo["full_name"],
                url=repo["html_url"],
                summary=repo.get("description") or "",
                metrics={
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language"),
                    "topics": repo.get("topics", [])[:8],
                    "created_at": repo.get("created_at"),
                },
            ))
        return items
