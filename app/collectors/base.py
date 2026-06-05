"""采集器基类：统一接口 + 容错（单源失败不影响整体）。"""
import logging

import httpx

from app.models import RawItem

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 ai-tech-radar/1.0")


def http_client(**kw) -> httpx.Client:
    # 把调用方自定义的 headers 与默认 UA 合并，避免与下面的 headers= 形成重复关键字
    headers = {"User-Agent": UA, **(kw.pop("headers", None) or {})}
    return httpx.Client(
        headers=headers,
        timeout=httpx.Timeout(20, connect=10),
        follow_redirects=True,
        **kw,
    )


class Collector:
    name = "base"

    def fetch(self) -> list[RawItem]:
        raise NotImplementedError

    def safe_fetch(self) -> list[RawItem]:
        try:
            items = self.fetch()
            log.info("[%s] 采集 %d 条", self.name, len(items))
            return items
        except Exception:  # noqa: BLE001
            log.exception("[%s] 采集失败，跳过该源", self.name)
            return []
