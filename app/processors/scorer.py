"""AI 批量打分分类（便宜模型，每批 score_batch_size 条）。"""
import json
import logging
import sqlite3

from pydantic import ValidationError

from app.config import get_settings
from app.llm.base import extract_json
from app.llm.router import get_scorer
from app.models import CATEGORIES, ScoreResult

log = logging.getLogger(__name__)

SYSTEM = f"""你是「AI 技术雷达」的资深编辑，任务是给候选条目打分，目标读者是想跟进 AI 前沿的中文工程师。

打分标准（0-10）：
- 9-10：重大发布/突破，所有人都该知道
- 7-8：高价值，值得深入了解（新颖、实用、增长异常快）
- 5-6：有点意思，但普通
- 0-4：噪音（营销、旧闻、与 AI/工程无关、纯资源列表）

category 必须从以下选择：{"、".join(CATEGORIES)}

对每条输出：
{{"id": <原id>, "score": <0-10>, "category": "<分类>", "tags": ["2-4个中文标签"], "reason": "<一句话评分理由，中文>", "worth_deep_dive": <true|false 是否值得深度讲解>}}

只输出 JSON 数组，不要任何其他文字。对所有输入条目都要给出结果。"""


def score_pending(conn: sqlite3.Connection, run_date: str) -> dict:
    """对当日 raw 条目批量打分，写回 DB。返回统计。"""
    s = get_settings()
    llm = get_scorer()
    rows = conn.execute(
        "SELECT id, source, title, summary, metrics FROM items WHERE run_date=? AND status='raw'",
        (run_date,),
    ).fetchall()
    stats = {"scored": 0, "kept": 0, "failed": 0}
    for i in range(0, len(rows), s.score_batch_size):
        batch = rows[i:i + s.score_batch_size]
        lines = []
        for r in batch:
            metrics = json.loads(r["metrics"] or "{}")
            heat = {k: metrics.get(k) for k in
                    ("stars", "stars_today", "points", "upvotes", "likes", "downloads") if metrics.get(k)}
            lines.append(json.dumps({
                "id": r["id"], "source": r["source"], "title": r["title"],
                "summary": (r["summary"] or "")[:300], "heat": heat,
            }, ensure_ascii=False) + ",")
        user = "候选条目：\n[\n" + "\n".join(lines) + "\n]"
        try:
            resp = llm.complete(SYSTEM, user, max_tokens=300 * len(batch))
            results = extract_json(resp.text)
        except Exception:  # noqa: BLE001
            log.exception("打分批次失败，该批跳过")
            stats["failed"] += len(batch)
            continue
        valid_ids = {r["id"] for r in batch}
        for raw in results if isinstance(results, list) else []:
            try:
                sr = ScoreResult.model_validate(raw)
            except ValidationError:
                continue
            if sr.id not in valid_ids:
                continue
            if sr.category not in CATEGORIES:
                sr.category = "其他"
            keep = sr.score >= s.min_score_keep
            conn.execute(
                """UPDATE items SET score=?, category=?, tags=?, score_reason=?,
                   status=?, drop_reason=? WHERE id=?""",
                (sr.score, sr.category, json.dumps(sr.tags, ensure_ascii=False),
                 sr.reason, "scored" if keep else "dropped",
                 None if keep else f"低分 {sr.score}",
                 sr.id),
            )
            # worth_deep_dive 暂存到 metrics
            if sr.worth_deep_dive and keep:
                conn.execute(
                    """UPDATE items SET metrics=json_set(metrics,'$.worth_deep_dive',1) WHERE id=?""",
                    (sr.id,),
                )
            stats["scored"] += 1
            stats["kept"] += int(keep)
        conn.commit()
    # 漏掉没打上分的（模型偶尔漏条目）标记为低优先级保留
    conn.execute(
        "UPDATE items SET status='dropped', drop_reason='打分缺失' WHERE run_date=? AND status='raw'",
        (run_date,),
    )
    conn.commit()
    return stats


def composite_score(score: float, metrics: dict) -> float:
    """综合分：AI 分为主，热度做小幅加成。"""
    import math
    heat = max(
        metrics.get("stars_today", 0) * 10,   # 当日新增星最能代表增速
        metrics.get("points", 0),
        metrics.get("upvotes", 0) * 5,
        metrics.get("stars", 0) / 100,
    )
    return score + min(2.0, math.log10(heat + 1))
