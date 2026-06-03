"""相关推荐：基于向量余弦相似度，从历史已讲解条目中找关联（学习路径）。"""
import sqlite3

import numpy as np


def find_related(conn: sqlite3.Connection, item_id: int, top_k: int = 5) -> list[sqlite3.Row]:
    me = conn.execute("SELECT embedding FROM items WHERE id=?", (item_id,)).fetchone()
    if not me or me["embedding"] is None:
        # 无向量时退化：同分类最近条目
        cat = conn.execute("SELECT category FROM items WHERE id=?", (item_id,)).fetchone()
        if not cat or not cat["category"]:
            return []
        return conn.execute(
            """SELECT id, title, category, run_date FROM items
               WHERE status='explained' AND id != ? AND category = ?
               ORDER BY run_date DESC LIMIT ?""",
            (item_id, cat["category"], top_k),
        ).fetchall()
    my_vec = np.frombuffer(me["embedding"], dtype=np.float32)
    rows = conn.execute(
        """SELECT id, title, category, run_date, embedding FROM items
           WHERE status='explained' AND id != ? AND embedding IS NOT NULL""",
        (item_id,),
    ).fetchall()
    scored = []
    for r in rows:
        vec = np.frombuffer(r["embedding"], dtype=np.float32)
        if vec.shape != my_vec.shape:
            continue
        scored.append((float(np.dot(my_vec, vec)), r))
    scored.sort(key=lambda x: -x[0])
    return [r for sim, r in scored[:top_k] if sim > 0.5]
