"""Hugging Face：趋势模型（官方 API）+ Daily Papers（Papers with Code 的继任者）。"""
from app.collectors.base import Collector, http_client
from app.models import RawItem


class HuggingFaceCollector(Collector):
    name = "huggingface"

    def fetch(self) -> list[RawItem]:
        items: list[RawItem] = []
        with http_client() as client:
            # 1) 趋势模型
            resp = client.get("https://huggingface.co/api/models", params={
                "sort": "trendingScore", "direction": -1, "limit": 20,
            })
            if resp.status_code == 200:
                for m in resp.json():
                    mid = m.get("modelId") or m.get("id")
                    if not mid:
                        continue
                    items.append(RawItem(
                        source=self.name,
                        title=f"模型: {mid}",
                        url=f"https://huggingface.co/{mid}",
                        summary=f"pipeline: {m.get('pipeline_tag') or '未知'}",
                        metrics={
                            "likes": m.get("likes", 0),
                            "downloads": m.get("downloads", 0),
                            "hf_type": "model",
                        },
                    ))
            # 2) Daily Papers
            resp = client.get("https://huggingface.co/api/daily_papers", params={"limit": 25})
            if resp.status_code == 200:
                for p in resp.json():
                    paper = p.get("paper") or {}
                    pid = paper.get("id")
                    title = (p.get("title") or paper.get("title") or "").strip()
                    if not pid or not title:
                        continue
                    items.append(RawItem(
                        source=self.name,
                        title=title,
                        url=f"https://huggingface.co/papers/{pid}",
                        summary=(paper.get("summary") or "")[:1200],
                        metrics={"upvotes": paper.get("upvotes", 0), "hf_type": "paper"},
                    ))
        return items
