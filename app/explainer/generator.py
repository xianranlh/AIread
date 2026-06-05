"""深度讲解生成：基于材料 + 结构化 JSON 输出 + schema 校验重试。"""
import json
import logging
import sqlite3

from pydantic import ValidationError

from app.config import get_settings
from app.db import fts_index_item, get_setting, now_iso
from app.llm.base import extract_json
from app.llm.router import get_explainer
from app.models import Explanation

log = logging.getLogger(__name__)

SYSTEM = """你是一位擅长把前沿 AI 技术讲透的中文技术作者，读者是有编程基础、想跟进 AI 前沿的工程师。

根据提供的材料写一篇结构化讲解。要求：
1. 只基于材料写作，禁止编造材料中没有的功能、数据、评测结果
2. 材料不足或没说清的点，写进 confidence_notes
3. 白话讲原理，能用类比就用类比，但保持技术准确
4. 全部用中文（专有名词保留英文）

严格按此 JSON 格式输出（不要输出任何其他文字）：
{
  "one_liner": "一句话说清它是什么（30字内）",
  "problem": "解决什么问题？之前的方案差在哪？（100-200字）",
  "how_it_works": "核心技术原理，面向工程师的白话讲解，可用 markdown（200-400字）",
  "highlights": ["亮点1", "亮点2", "亮点3"],
  "getting_started": "10分钟上手路径：安装命令/关键步骤（可用 markdown）",
  "prerequisites": ["需要先懂的概念A：一句话解释", "概念B：一句话解释"],
  "related": ["值得对比的同类项目/论文及一句话差异"],
  "verdict": "适合谁用？现在值不值得投入学习？（50-100字，给明确建议）",
  "confidence_notes": "材料中没说清或可能不准的点；没有则留空字符串"
}"""


def build_system(conn: sqlite3.Connection) -> str:
    """SYSTEM + 用户在设置页自定义的讲解附加要求（结构/偏向），保存即生效。"""
    guidance = (get_setting(conn, "explain.guidance") or "").strip()
    if not guidance:
        return SYSTEM
    return (SYSTEM + "\n\n===== 额外写作要求（用户自定义，在不破坏上面 JSON 结构的前提下优先遵循）=====\n"
            + guidance)


def explain_item(conn: sqlite3.Connection, item: sqlite3.Row, material: str) -> bool:
    s = get_settings()
    llm = get_explainer()
    system = build_system(conn)
    user = f"===== 材料开始 =====\n{material}\n===== 材料结束 =====\n\n请输出讲解 JSON。"
    exp: Explanation | None = None
    resp = None
    for attempt in range(3):  # schema 校验失败最多重试两次
        try:
            resp = llm.complete(system, user, max_tokens=s.explain_max_tokens)
            exp = Explanation.model_validate(extract_json(resp.text))
            break
        except (ValidationError, ValueError) as e:
            log.warning("讲解输出校验失败(第%d次): %s", attempt + 1, e)
        except Exception:  # noqa: BLE001
            log.exception("讲解生成失败: %s", item["title"])
            return False
    if exp is None or resp is None:
        return False
    conn.execute(
        """INSERT OR REPLACE INTO explanations(item_id, content, model, tokens_in, tokens_out, created_at)
           VALUES (?,?,?,?,?,?)""",
        (item["id"], exp.model_dump_json(), resp.model,
         resp.tokens_in, resp.tokens_out, now_iso()),
    )
    conn.execute(
        "INSERT OR REPLACE INTO materials(item_id, content, created_at) VALUES (?,?,?)",
        (item["id"], material[:60000], now_iso()),
    )
    conn.execute("UPDATE items SET status='explained' WHERE id=?", (item["id"],))
    fts_index_item(conn, item["id"], item["title"], item["summary"], exp.to_search_text())
    conn.commit()
    return True
