"""LLM 客户端统一接口。"""
import json
import re
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


def extract_json(text: str):
    """从模型输出中稳健地抠出 JSON（容忍 ```json 围栏、前后废话）。"""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    # 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找第一个 { 或 [ 到最后一个 } 或 ]
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start, end = text.find(open_ch), text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"无法从输出中解析 JSON: {text[:200]}...")
