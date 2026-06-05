"""LLM 客户端统一接口。"""
import json
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""


@dataclass
class Usage:
    """进程内用量累计，管线结束时打印成本概览。"""
    tokens_in: int = 0
    tokens_out: int = 0
    calls: int = 0
    by_model: dict = field(default_factory=dict)

    def add(self, resp: LLMResponse) -> None:
        self.calls += 1
        self.tokens_in += resp.tokens_in
        self.tokens_out += resp.tokens_out
        m = self.by_model.setdefault(resp.model, {"in": 0, "out": 0})
        m["in"] += resp.tokens_in
        m["out"] += resp.tokens_out


USAGE = Usage()


class LLMClient:
    def complete(self, system: str, user: str, max_tokens: int = 1024) -> LLMResponse:
        raise NotImplementedError


def _balanced(text: str, open_ch: str, close_ch: str) -> str | None:
    """从首个 open_ch 起做括号配对截取，正确跳过字符串字面量里的括号/引号。"""
    start = text.find(open_ch)
    if start == -1:
        return None
    depth = 0
    in_str = esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def extract_json(text: str):
    """从模型输出中稳健地抠出 JSON（容忍 ```json 围栏、前后废话、值内嵌 markdown/代码块）。"""
    text = (text or "").strip()
    # 只剥「最外层」代码围栏：避免被 JSON 字符串内部的 ``` 代码块误伤而提前截断。
    if text.startswith("```"):
        text = text[3:]
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    # 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 括号配对兜底：取最先出现的 { 或 [ 做配对截取，使对象({})与数组([])都能被正确识别，
    # 且不会把对象内部的数组当成顶层结果（讲解输出是对象，打分输出是数组）。
    candidates = []
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        snippet = _balanced(text, open_ch, close_ch)
        if start != -1 and snippet:
            candidates.append((start, snippet))
    for _, snippet in sorted(candidates):
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"无法从输出中解析 JSON: {text[:200]}...")
