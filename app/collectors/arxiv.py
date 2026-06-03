"""arXiv 官方 API：cs.AI / cs.CL / cs.LG 当日新论文。"""
import xml.etree.ElementTree as ET

from app.config import get_settings
from app.collectors.base import Collector, http_client
from app.models import RawItem

NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivCollector(Collector):
    name = "arxiv"

    def fetch(self) -> list[RawItem]:
        s = get_settings()
        cats = [c.strip() for c in s.arxiv_categories.split(",") if c.strip()]
        query = " OR ".join(f"cat:{c}" for c in cats)
        with http_client() as client:
            resp = client.get("https://export.arxiv.org/api/query", params={
                "search_query": query,
                "sortBy": "submittedDate", "sortOrder": "descending",
                "max_results": s.arxiv_max_results,
            })
            resp.raise_for_status()
        items = []
        root = ET.fromstring(resp.text)
        for entry in root.findall("atom:entry", NS):
            title = (entry.findtext("atom:title", "", NS) or "").replace("\n", " ").strip()
            abstract = (entry.findtext("atom:summary", "", NS) or "").replace("\n", " ").strip()
            link = entry.findtext("atom:id", "", NS) or ""
            authors = [a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)]
            if not title or not link:
                continue
            items.append(RawItem(
                source=self.name,
                title=title,
                url=link.replace("http://", "https://"),
                summary=abstract[:1200],
                metrics={"authors": authors[:5]},
            ))
        return items
