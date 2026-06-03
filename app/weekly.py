"""每周综述：把本周精选条目汇总成一篇趋势长文。

手动运行：python -m app.weekly
"""
import json
import logging
from datetime import date, timedelta

from app.db import db, now_iso
from app.llm.router import get_explainer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("weekly")

SYSTEM = """你是「AI 技术雷达」的主编，请基于本周收录的条目写一篇中文周报（markdown）。

要求：
1. 开头 2-3 段总结本周 AI 领域的主线趋势（哪些方向在升温、有什么信号）
2. 按主题分 3-5 个小节展开，引用具体条目佐证（用条目标题，不要编造）
3. 结尾给出「本周最值得花时间的 3 件事」
4. 只基于提供的条目，不要编造；1000-1500 字"""


def run() -> str | None:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_key = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"
    with db() as conn:
        rows = conn.execute(
            """SELECT i.title, i.category, i.score, i.score_reason, i.url,
                      e.content FROM items i LEFT JOIN explanations e ON e.item_id=i.id
               WHERE i.run_date >= ? AND i.status IN ('selected','explained')
               ORDER BY i.score DESC LIMIT 60""",
            (monday.isoformat(),),
        ).fetchall()
        if len(rows) < 5:
            log.info("本周条目不足，跳过周报")
            return None
        lines = []
        for r in rows:
            one_liner = ""
            if r["content"]:
                one_liner = json.loads(r["content"]).get("one_liner", "")
            lines.append(f"- [{r['category']}] {r['title']}（分:{r['score']}）{one_liner or r['score_reason'] or ''}")
        user = f"本周（{week_key}）收录条目：\n" + "\n".join(lines)
        llm = get_explainer()
        resp = llm.complete(SYSTEM, user, max_tokens=3000)
        conn.execute(
            "INSERT OR REPLACE INTO weekly_digests(week, content_md, model, created_at) VALUES (?,?,?,?)",
            (week_key, resp.text.strip(), resp.model, now_iso()),
        )
        conn.commit()
    log.info("周报 %s 生成完成", week_key)
    return week_key


if __name__ == "__main__":
    run()
