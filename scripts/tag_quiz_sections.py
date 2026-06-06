"""一次性：给 quiz_seed.json 的每题加上 section（章节分组）与 ord（递进顺序）。
JavaGuide 风格：大类(domain) → 章节(section, 由浅入深排序) → 题目(ord 升序)。
按题目在原 seed 中的索引映射，answer_md 原样保留。"""
import json
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "app" / "quiz_seed.json"

# index -> (section, ord)；ord 是该 domain 内的全局递进序号
MAP = {
    # Java
    0: ("集合容器", 0), 1: ("集合容器", 1),
    5: ("并发编程", 2), 6: ("并发编程", 3), 7: ("并发编程", 4),
    2: ("JVM 与类加载", 5), 3: ("JVM 与类加载", 6), 4: ("JVM 与类加载", 7),
    8: ("Spring 框架", 8), 9: ("Spring 框架", 9),
    # Python
    11: ("语言核心", 0), 12: ("语言核心", 1), 13: ("语言核心", 2),
    14: ("语言核心", 3), 19: ("语言核心", 4),
    15: ("内存与垃圾回收", 5),
    10: ("并发编程", 6), 16: ("并发编程", 7), 18: ("并发编程", 8),
    17: ("高级特性", 9),
    # AI 基础
    20: ("Transformer 架构", 0), 21: ("Transformer 架构", 1), 22: ("Transformer 架构", 2),
    23: ("训练与对齐", 3), 27: ("训练与对齐", 4),
    24: ("高效训练与推理", 5), 25: ("高效训练与推理", 6), 26: ("高效训练与推理", 7),
    28: ("评估与落地", 8), 29: ("评估与落地", 9),
    # Agent
    30: ("Agent 基础", 0), 31: ("Agent 基础", 1), 39: ("Agent 基础", 2),
    32: ("工具与检索增强", 3), 33: ("工具与检索增强", 4), 34: ("工具与检索增强", 5),
    37: ("工具与检索增强", 6),
    35: ("进阶架构与评测", 7), 36: ("进阶架构与评测", 8), 38: ("进阶架构与评测", 9),
    # 场景设计
    40: ("系统设计", 0), 41: ("系统设计", 1), 42: ("系统设计", 2), 43: ("系统设计", 3),
    44: ("分布式基础", 4), 47: ("分布式基础", 5), 49: ("分布式基础", 6),
    45: ("高可用与一致性", 7), 46: ("高可用与一致性", 8), 48: ("高可用与一致性", 9),
}

data = json.loads(SEED.read_text(encoding="utf-8"))
assert len(data) == len(MAP), f"题数 {len(data)} 与映射 {len(MAP)} 不一致"
for i, q in enumerate(data):
    section, ordv = MAP[i]
    # 重排字段顺序：domain, section, ord, category, question, answer_md
    new = {"domain": q["domain"], "section": section, "ord": ordv,
           "category": q.get("category", "基础"),
           "question": q["question"], "answer_md": q.get("answer_md", "")}
    data[i] = new

SEED.write_text(json.dumps(data, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
print(f"已为 {len(data)} 题写入 section/ord")
