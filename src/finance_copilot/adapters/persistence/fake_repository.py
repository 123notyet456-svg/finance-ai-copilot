from copy import deepcopy
from uuid import uuid4


class FakeRepository:
    def __init__(self) -> None:
        self._collections: dict[str, list[dict[str, object]]] = {}

    def save(self, collection: str, record: dict[str, object]) -> str:
        record_id = str(record.get("id") or uuid4())
        stored = {**deepcopy(record), "id": record_id}
        self._collections.setdefault(collection, []).append(stored)
        return record_id

    def list(self, collection: str) -> list[dict[str, object]]:
        return deepcopy(self._collections.get(collection, []))

