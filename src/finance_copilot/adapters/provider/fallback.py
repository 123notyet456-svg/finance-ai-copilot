"""真实 Provider 不可用时自动回退到 Fake 的弹性适配器。"""

from typing import Sequence

from finance_copilot.core.ports import EmbeddingPort, LLMPort


class FallbackEmbeddingAdapter:
    def __init__(self, primary: EmbeddingPort | None, fallback: EmbeddingPort) -> None:
        self._primary = primary
        self._fallback = fallback
        self.fallback_used = primary is None
        self.last_error: str | None = "primary_unavailable" if primary is None else None
        self.active_provider = "fake" if primary is None else "primary"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self._primary is not None:
            try:
                result = self._primary.embed(texts)
                self.fallback_used = False
                self.last_error = None
                self.active_provider = str(getattr(self._primary, "provider_name", "primary"))
                return result
            except Exception as exc:
                self.last_error = type(exc).__name__
                self._primary = None
        self.fallback_used = True
        self.active_provider = str(getattr(self._fallback, "provider_name", "fake"))
        return self._fallback.embed(texts)


class FallbackLLMAdapter:
    def __init__(self, primary: LLMPort | None, fallback: LLMPort) -> None:
        self._primary = primary
        self._fallback = fallback
        self.fallback_used = primary is None
        self.last_error: str | None = "primary_unavailable" if primary is None else None
        self.active_provider = "fake" if primary is None else "primary"

    def generate(self, prompt: str) -> str:
        if self._primary is not None:
            try:
                result = self._primary.generate(prompt)
                self.fallback_used = False
                self.last_error = None
                self.active_provider = str(getattr(self._primary, "provider_name", "primary"))
                return result
            except Exception as exc:
                self.last_error = type(exc).__name__
                self._primary = None
        self.fallback_used = True
        self.active_provider = str(getattr(self._fallback, "provider_name", "fake"))
        return self._fallback.generate(prompt)
