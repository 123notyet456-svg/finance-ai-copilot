from typing import Protocol


class LLMPort(Protocol):
    def generate(self, prompt: str) -> str: ...

