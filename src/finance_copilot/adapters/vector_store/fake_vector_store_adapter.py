"""进程内向量库模拟器。"""

from math import sqrt
from typing import Sequence


class FakeVectorStoreAdapter:
    def __init__(self) -> None:
        self._items: list[dict[str, object]] = []

    def reset(self) -> None:
        self._items = []

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[dict[str, object]],
    ) -> None:
        if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError("ids、texts、embeddings 与 metadatas 长度必须一致")
        existing = {str(item["id"]): item for item in self._items}
        for item_id, text, embedding, metadata in zip(ids, texts, embeddings, metadatas, strict=True):
            existing[item_id] = {
                "id": item_id,
                "text": text,
                "embedding": list(embedding),
                "metadata": dict(metadata),
            }
        self._items = list(existing.values())

    def query(self, embedding: Sequence[float], top_k: int = 5) -> list[dict[str, object]]:
        ranked = []
        for item in self._items:
            score = self._cosine(embedding, item["embedding"])
            ranked.append({**item, "score": score})
        return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)[:top_k]

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(value * value for value in left)) or 1.0
        right_norm = sqrt(sum(value * value for value in right)) or 1.0
        return max(0.0, min(1.0, dot / (left_norm * right_norm)))
