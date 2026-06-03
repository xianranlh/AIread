"""与历史去重：simhash（零依赖实现）+ 可选向量相似度。"""
import hashlib
import re
import sqlite3
from datetime import datetime, timedelta

import numpy as np

from app.config import get_settings


# ---------- simhash ----------
def _tokens(text: str) -> list[str]:
    text = text.lower()
    # CJK 按字 + 英文按词，再做 2-gram shingle
    parts = re.findall(r"[一-鿿]|[a-z0-9]+", text)
    if len(parts) < 2:
        return parts
    return [parts[i] + parts[i + 1] for i in range(len(parts) - 1)]


def simhash64(text: str) -> int:
    v = [0] * 64
    for tok in _tokens(text):
        h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:8], "big")
        for i in range(64):
            v[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(64):
        if v[i] > 0:
            out |= 1 << i
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


# ---------- 历史去重 ----------
def find_duplicate(conn: sqlite3.Connection, title: str, summary: str | None,
                   embedding: np.ndarray | None) -> str | None:
    """与近 N 天非丢弃条目比对，返回重复原因（None = 不重复）。"""
    s = get_settings()
    cutoff = (datetime.now() - timedelta(days=s.dedup_days)).strftime("%Y-%m-%d")
    sh = simhash64(f"{title} {summary or ''}")
    rows = conn.execute(
        """SELECT id, simhash, embedding FROM items
           WHERE run_date >= ? AND status != 'dropped' AND simhash IS NOT NULL""",
        (cutoff,),
    ).fetchall()
    mask = (1 << 64) - 1
    for row in rows:
        if hamming(sh & mask, row["simhash"] & mask) <= s.simhash_max_distance:
            return f"simhash 重复 (item #{row['id']})"
    if embedding is not None:
        for row in rows:
            if row["embedding"] is None:
                continue
            other = np.frombuffer(row["embedding"], dtype=np.float32)
            if other.shape != embedding.shape:
                continue
            sim = float(np.dot(embedding, other))  # 向量已归一化
            if sim > s.vector_dup_threshold:
                return f"语义重复 sim={sim:.2f} (item #{row['id']})"
    return None
