"""OpenAI Provider Adapter；SDK 只存在于 adapters 层。"""

from typing import Sequence


class OpenAIEmbeddingAdapter:
    provider_name = "openai"

    def __init__(
        self,
        *,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        client: object | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if client is None:
            if not api_key:
                raise ValueError("OPENAI_API_KEY 未配置")
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        self._client = client
        self.model = model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        clean_texts = [text.strip() for text in texts]
        if not clean_texts or any(not text for text in clean_texts):
            raise ValueError("Embedding 输入不能为空")
        response = self._client.embeddings.create(
            model=self.model,
            input=clean_texts,
            encoding_format="float",
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


class OpenAILLMAdapter:
    provider_name = "openai"

    def __init__(
        self,
        *,
        model: str = "gpt-5-mini",
        api_key: str | None = None,
        client: object | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        if client is None:
            if not api_key:
                raise ValueError("OPENAI_API_KEY 未配置")
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        self._client = client
        self.model = model

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("LLM prompt 不能为空")
        response = self._client.responses.create(model=self.model, input=prompt)
        output_text = str(response.output_text).strip()
        if not output_text:
            raise RuntimeError("Provider 返回空文本")
        return output_text

