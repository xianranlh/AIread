"""LLM 角色配置解析：数据库（网页设置）优先，.env 兜底。

三个角色：scorer（粗筛）/ explainer（精讲）/ fallback（兜底）。
每个角色四个字段：provider / model / api_key / base_url，可指向不同厂商端点。
"""
from dataclasses import dataclass

from app.config import get_settings
from app.db import db, get_setting

ROLES = ("scorer", "explainer", "fallback")
FIELDS = ("provider", "model", "api_key", "base_url")


@dataclass
class LLMRoleConfig:
    role: str
    provider: str   # anthropic | openai_compat | mock
    model: str
    api_key: str
    base_url: str   # openai_compat 必填；anthropic 留空=官方端点（可填中转网关）

    def label(self) -> str:
        return f"{self.provider}:{self.model}"


def _env_defaults(role: str) -> dict:
    s = get_settings()
    provider, model = {
        "scorer": (s.scorer_provider, s.scorer_model),
        "explainer": (s.explainer_provider, s.explainer_model),
        "fallback": (s.fallback_provider, s.fallback_model),
    }[role]
    if provider == "anthropic":
        api_key, base_url = s.anthropic_api_key, ""
    elif provider == "openai_compat":
        api_key, base_url = s.openai_compat_api_key, s.openai_compat_base_url
    else:  # mock
        api_key, base_url = "", ""
    return {"provider": provider, "model": model, "api_key": api_key, "base_url": base_url}


def resolve_role(role: str) -> LLMRoleConfig:
    """DB 设置覆盖 .env 默认值。每次调用都重新读取（保存即生效）。"""
    assert role in ROLES, f"未知角色: {role}"
    cfg = _env_defaults(role)
    with db() as conn:
        for f in FIELDS:
            v = get_setting(conn, f"llm.{role}.{f}")
            if v is not None and v != "":
                cfg[f] = v
        # provider 在 DB 中被改过时，.env 的 key/base_url 默认值可能不匹配新 provider，
        # 因此 provider 来自 DB 而 key 为空时，再按新 provider 取一次 env 默认 key
        if cfg["api_key"] == "":
            s = get_settings()
            if cfg["provider"] == "anthropic":
                cfg["api_key"] = s.anthropic_api_key
            elif cfg["provider"] == "openai_compat":
                cfg["api_key"] = cfg["api_key"] or s.openai_compat_api_key
                cfg["base_url"] = cfg["base_url"] or s.openai_compat_base_url
    return LLMRoleConfig(role=role, **cfg)


def save_role(form: dict, role: str) -> None:
    """保存网页表单：api_key 留空 = 不修改原值。"""
    from app.db import set_setting
    with db() as conn:
        for f in FIELDS:
            v = (form.get(f"{role}_{f}") or "").strip()
            if f == "api_key" and v == "":
                continue  # 留空不覆盖
            set_setting(conn, f"llm.{role}.{f}", v)


def mask_key(key: str) -> str:
    if not key:
        return "未设置"
    if len(key) <= 12:
        return "已设置（短 key）"
    return f"{key[:6]}…{key[-4:]}"
