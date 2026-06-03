"""主管线：采集 → 清洗 → 历史去重 → AI 打分 → 精选 → 深度讲解。

手动运行：python -m app.pipeline
"""
import json
import logging
import sqlite3
from datetime import date

from app.collectors import collect_all
from app.config import get_settings
from app.db import db, now_iso
from app.explainer.enricher import gather_material
from app.explainer.generator import explain_item
from app.llm.base import USAGE
from app.processors.cleaner import clean, external_id
from app.processors.dedup import find_duplicate, simhash64
from app.processors.embedder import embed_one
from app.processors.scorer import composite_score, score_pending

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("pipeline")


def run(run_date: str | None = None) -> dict:
    s = get_settings()
    run_date = run_date or date.today().isoformat()
    stats: dict = {"run_date": run_date}

    with db() as conn:
        run_id = conn.execute(
            "INSERT INTO runs(started_at) VALUES (?)", (now_iso(),)
        ).lastrowid
        conn.commit()

        # ① 采集
        raw = collect_all()
        stats["collected"] = len(raw)

        # ② 规则清洗 + 跨源合并
        cleaned, n_dropped = clean(raw)
        stats["cleaned"] = len(cleaned)
        log.info("清洗后 %d 条（规则丢弃 %d）", len(cleaned), n_dropped)

        # ③ 入库 + 历史去重（simhash + 可选向量）
        inserted = 0
        for it in cleaned:
            ext_id = external_id(it.url)
            exists = conn.execute(
                "SELECT id FROM items WHERE external_id=?", (ext_id,)
            ).fetchone()
            if exists:
                continue  # 历史已收录过这个 URL
            text = f"{it.title} {it.summary or ''}"
            vec = embed_one(text)
            dup = find_duplicate(conn, it.title, it.summary, vec)
            status, drop_reason = ("dropped", dup) if dup else ("raw", None)
            conn.execute(
                """INSERT INTO items(external_id, source, title, url, summary, metrics,
                                     status, drop_reason, simhash, embedding, run_date, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ext_id, it.source, it.title, it.url, it.summary,
                 json.dumps(it.metrics, ensure_ascii=False, default=str),
                 status, drop_reason, _to_i64(simhash64(text)),
                 vec.tobytes() if vec is not None else None,
                 run_date, now_iso()),
            )
            inserted += 1
        conn.commit()
        stats["inserted"] = inserted
        log.info("新条目入库 %d 条", inserted)

        # ④ AI 打分分类
        stats["scoring"] = score_pending(conn, run_date)

        # ⑤ 精选 Top-N
        rows = conn.execute(
            "SELECT * FROM items WHERE run_date=? AND status='scored'", (run_date,)
        ).fetchall()
        ranked = sorted(
            rows,
            key=lambda r: -composite_score(r["score"] or 0, json.loads(r["metrics"] or "{}")),
        )
        deep_dive = [r for r in ranked
                     if json.loads(r["metrics"] or "{}").get("worth_deep_dive")][: s.explain_limit]
        for r in ranked:
            conn.execute("UPDATE items SET status='selected' WHERE id=?", (r["id"],))
        conn.commit()
        stats["selected"] = len(ranked)

        # ⑥ 深度讲解
        ok = 0
        for r in deep_dive:
            item = conn.execute("SELECT * FROM items WHERE id=?", (r["id"],)).fetchone()
            log.info("讲解中: %s", item["title"])
            material = gather_material(dict(item))
            if explain_item(conn, item, material):
                ok += 1
        stats["explained"] = ok

        # ⑦ 推送（未配置则跳过；失败不影响管线）
        try:
            from app.notify import notify_daily
            stats["notify"] = notify_daily(conn, run_date)
        except Exception:  # noqa: BLE001
            log.exception("推送失败（不影响管线）")

        # ⑧ 收尾
        stats["tokens"] = {"in": USAGE.tokens_in, "out": USAGE.tokens_out,
                           "calls": USAGE.calls, "by_model": USAGE.by_model}
        conn.execute(
            "UPDATE runs SET finished_at=?, ok=1, stats=? WHERE id=?",
            (now_iso(), json.dumps(stats, ensure_ascii=False), run_id),
        )
        conn.commit()

    log.info("管线完成: %s", json.dumps(stats, ensure_ascii=False))
    return stats


def _to_i64(u: int) -> int:
    """SQLite INTEGER 是有符号 64 位，把 uint64 映射过去。"""
    return u - (1 << 64) if u >= (1 << 63) else u


if __name__ == "__main__":
    run()
