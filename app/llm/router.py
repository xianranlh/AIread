"""按角色路由模型：配置实时解析（网页设置保存即生效），主供应商失败自动降级。"""
import logging
import time

from app.llm.base import LLMClient, LLMResponse, USAGE
from app.llm.config import resolve_role
from app.llm.providers import make_client

log = logging.getLogger(__name__)


class RoutedLLM:
    def __init__(self, role: str):
        # 构造时解析最新配置（每次管线运行都会重新构造）
        self.primary_cfg = resolve_role(role)
        self.fallback_cfg = resolve_role("fallback")
        self._primary: LLMClient | None = None
        self._fallback: LLMClient | None = None

    def _get(self, which: str) -> LLMClient:
        if which == "primary":
            if self._primary is None:
                self._primary = make_client(self.primary_cfg)
            return self._primary
        if self._fallback is None:
            self._fallback = make_client(self.fallback_cfg)
        return self._fallback

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 retries: int = 2) -> LLMResponse:
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = self._get("primary").complete(system, user, max_tokens)
                USAGE.add(resp)
                return resp
            except Exception as e:  # noqa: BLE001
                last_err = e
                wait = 2 ** attempt
                log.warning("主模型 %s 调用失败(%s)，%ds 后重试",
                            self.primary_cfg.label(), e, wait)
                time.sleep(wait)
        if self.fallback_cfg.provider and self.fallback_cfg.label() != self.primary_cfg.label():
            try:
                log.warning("切换到降级模型 %s", self.fallback_cfg.label())
                resp = self._get("fallback").complete(system, user, max_tokens)
                USAGE.add(resp)
                return resp
            except Exception as e:  # noqa: BLE001
                last_err = e
        raise RuntimeError(f"LLM 调用失败（含降级）: {last_err}")


def get_scorer() -> RoutedLLM:
    return RoutedLLM("scorer")


def get_explainer() -> RoutedLLM:
    return RoutedLLM("explainer")
