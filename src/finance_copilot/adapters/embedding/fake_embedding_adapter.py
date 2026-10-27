"""基于字符桶的确定性、无网络向量模拟器。"""

from math import sqrt
from typing import Sequence


class FakeEmbeddingAdapter:
    provider_name = "fake"
    dimensions = 16

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for char in text.lower():
            vector[ord(char) % self.dimensions] += 1.0
        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
