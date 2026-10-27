from typing import Protocol, Sequence


class VectorStorePort(Protocol):
    def reset(self) -> None: ...

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[dict[str, object]],
    ) -> None: ...

    def query(self, embedding: Sequence[float], top_k: int = 5) -> list[dict[str, object]]: ...
