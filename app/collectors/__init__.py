"""采集器注册表：新增数据源 = 加一个文件 + 在此注册。"""
from app.collectors.base import Collector
from app.collectors.github_trending import GithubTrendingCollector
from app.collectors.github_search import GithubSearchCollector
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.arxiv import ArxivCollector
from app.collectors.huggingface import HuggingFaceCollector
from app.collectors.rss_blogs import BlogRssCollector

ALL_COLLECTORS: list[type[Collector]] = [
    GithubTrendingCollector,
    GithubSearchCollector,
    HackerNewsCollector,
    ArxivCollector,
    HuggingFaceCollector,
    BlogRssCollector,
]


def collect_all() -> list:
    items = []
    for cls in ALL_COLLECTORS:
        items.extend(cls().safe_fetch())
    return items
