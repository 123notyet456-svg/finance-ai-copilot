from typing import Protocol


class RepositoryPort(Protocol):
    def save(self, collection: str, record: dict[str, object]) -> str: ...

    def list(self, collection: str) -> list[dict[str, object]]: ...

