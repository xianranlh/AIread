"""规则清洗：URL 规范化、黑名单、明显无关内容过滤。"""
import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from app.models import RawItem

# 这些仓库/域名一般是资源列表或与 AI 学习无关，直接降噪
BLACKLIST_PATTERNS = [
    r"github\.com/.*/awesome-",         # awesome 列表
    r"github\.com/.+/(interview|leetcode)",
    r"(coupon|deal|giveaway)",
]
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                   "utm_content", "ref", "ref_src", "fbclid", "gclid"}


def canonical_url(url: str) -> str:
    p = urlparse(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(p.query) if k not in TRACKING_PARAMS])
    path = p.path.rstrip("/")
    return urlunparse((p.scheme.lower() or "https", p.netloc.lower(), path, "", query, ""))


def external_id(url: str) -> str:
    return hashlib.sha1(canonical_url(url).encode()).hexdigest()


def is_blacklisted(item: RawItem) -> bool:
    target = f"{item.url} {item.title}".lower()
    return any(re.search(pat, target) for pat in BLACKLIST_PATTERNS)


def clean(items: list[RawItem]) -> tuple[list[RawItem], int]:
    """返回 (保留条目, 丢弃数)。同 canonical url 跨源合并 metrics。"""
    kept: dict[str, RawItem] = {}
    dropped = 0
    for it in items:
        if not it.title or not it.url or is_blacklisted(it):
            dropped += 1
            continue
        key = external_id(it.url)
        if key in kept:
            # 跨源重复：合并热度信息，保留信息更全的 summary
            old = kept[key]
            old.metrics.update({k: v for k, v in it.metrics.items() if v})
            old.metrics.setdefault("also_seen_on", []).append(it.source)
            if it.summary and len(it.summary or "") > len(old.summary or ""):
                old.summary = it.summary
        else:
            kept[key] = it
    return list(kept.values()), dropped
