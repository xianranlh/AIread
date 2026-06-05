"""三种 provider：anthropic / openai_compat（DeepSeek/Qwen/Kimi 等）/ mock。

凭据由 LLMRoleConfig 显式传入（来自网页设置或 .env），每个角色可用不同端点。
"""
import hashlib
import json

from app.llm.base import LLMClient, LLMResponse
from app.llm.config import LLMRoleConfig


class AnthropicClient(LLMClient):
    def __init__(self, model: str, api_key: str, base_url: str = ""):
        import anthropic
        if not api_key:
            raise RuntimeError("缺少 Anthropic API Key")
        kw = {"api_key": api_key}
        if base_url:
            kw["base_url"] = base_url  # 可填中转网关
        self.client = anthropic.Anthropic(**kw)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> LLMResponse:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return LLMResponse(
            text=text,
            tokens_in=msg.usage.input_tokens,
            tokens_out=msg.usage.output_tokens,
            model=self.model,
        )


class OpenAICompatClient(LLMClient):
    """任何 OpenAI 兼容端点：DeepSeek / OpenAI / Qwen / Kimi / 智谱 / 本地 Ollama 等。"""

    def __init__(self, model: str, api_key: str, base_url: str):
        from openai import OpenAI
        if not api_key:
            raise RuntimeError("缺少 API Key (openai_compat)")
        if not base_url:
            raise RuntimeError("缺少 base_url (openai_compat)")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> LLMResponse:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        # 某些 OpenAI 兼容中转网关返回的不是标准 ChatCompletion 结构，
        # openai SDK 在无法解析时会把原始 body 当作字符串直接返回。
        if not getattr(resp, "choices", None):
            raise RuntimeError(
                f"网关返回了非标准 OpenAI 响应（缺少 choices）：{str(resp)[:300]}"
            )
        msg = resp.choices[0].message
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=(getattr(msg, "content", "") or ""),
            tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
            tokens_out=getattr(usage, "completion_tokens", 0) or 0,
            model=self.model,
        )


class MockClient(LLMClient):
    """离线/无 Key 时跑通全流程用：返回确定性的合规 JSON。"""

    def __init__(self, model: str = "mock"):
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> LLMResponse:
        if "打分" in system or "score" in system.lower():
            ids = []
            for line in user.splitlines():
                if line.strip().startswith('{"id":'):
                    try:
                        ids.append(json.loads(line.rstrip(","))["id"])
                    except Exception:
                        pass
            results = []
            for i in ids:
                h = int(hashlib.md5(str(i).encode()).hexdigest(), 16)
                results.append({
                    "id": i, "score": 5.0 + (h % 50) / 10, "category": "开发工具",
                    "tags": ["mock", "测试"], "reason": "Mock 打分",
                    "worth_deep_dive": True,
                })
            return LLMResponse(text=json.dumps(results, ensure_ascii=False), model=self.model)
        if "周报" in system:
            return LLMResponse(text="## 本周综述（Mock）\n\n这是 Mock 模式生成的占位周报。", model=self.model)
        if "学习笔记" in system:
            return LLMResponse(text="# Mock 学习笔记\n\n## TL;DR\n占位笔记，配置真实 Key 后由大模型生成。\n\n## 核心要点\n- 要点一\n- 要点二", model=self.model)
        if "出题人" in system:
            qs = [{"question": "Mock 出题：什么是 XX？", "category": "基础",
                   "answer_md": "- Mock 答案要点一\n- 要点二"},
                  {"question": "Mock 出题：如何设计 YY 系统？", "category": "场景设计",
                   "answer_md": "- Mock 设计要点"}]
            return LLMResponse(text=json.dumps(qs, ensure_ascii=False), model=self.model)
        if "复盘" in system:
            return LLMResponse(text="# Mock 复盘笔记\n\n## 今日概况\n占位内容\n\n## 薄弱点\n- 占位", model=self.model)
        if "八股文讲解" in system:
            return LLMResponse(text="## AI 详解（Mock）\n\n这里是占位详解，配置真实 Key 后生成。", model=self.model)
        if "连接测试" in user:
            return LLMResponse(text="OK", model=self.model)
        exp = {
            "one_liner": "（Mock）这是一个占位讲解，配置真实 API Key 后将由 LLM 生成。",
            "problem": "演示用占位内容。", "how_it_works": "演示用占位内容。",
            "highlights": ["占位亮点 1", "占位亮点 2"],
            "getting_started": "pip install demo", "prerequisites": ["无"],
            "related": [], "verdict": "占位结论。", "confidence_notes": "Mock 模式生成",
        }
        return LLMResponse(text=json.dumps(exp, ensure_ascii=False), model=self.model)


def make_client(cfg: LLMRoleConfig) -> LLMClient:
    if cfg.provider == "anthropic":
        return AnthropicClient(cfg.model, cfg.api_key, cfg.base_url)
    if cfg.provider == "openai_compat":
        return OpenAICompatClient(cfg.model, cfg.api_key, cfg.base_url)
    if cfg.provider == "mock":
        return MockClient(cfg.model or "mock")
    raise ValueError(f"未知 provider: {cfg.provider}")
