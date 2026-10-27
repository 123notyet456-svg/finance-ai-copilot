"""基于 SQLite 的轻量持久化向量库。"""

import json
from contextlib import closing
from math import sqrt
from pathlib import Path
import sqlite3
from typing import Sequence


class SQLiteVectorStoreAdapter:
    provider_name = "sqlite"

    def __init__(self, database_path: str | Path, *, namespace: str = "policy_qa") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.namespace = namespace
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_documents (
                    namespace TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    PRIMARY KEY (namespace, item_id)
                )
                """
            )
            connection.commit()

    def upsert(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[dict[str, object]],
    ) -> None:
        if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError("ids、texts、embeddings 与 metadatas 长度必须一致")
        rows = [
            (
                self.namespace,
                item_id,
                text,
                json.dumps(list(embedding)),
                json.dumps(metadata, ensure_ascii=False),
            )
            for item_id, text, embedding, metadata in zip(
                ids, texts, embeddings, metadatas, strict=True
            )
        ]
        with closing(self._connect()) as connection:
            connection.executemany(
                """
                INSERT INTO vector_documents
                    (namespace, item_id, text, embedding_json, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, item_id) DO UPDATE SET
                    text=excluded.text,
                    embedding_json=excluded.embedding_json,
                    metadata_json=excluded.metadata_json
                """,
                rows,
            )
            connection.commit()

    def reset(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "DELETE FROM vector_documents WHERE namespace = ?", (self.namespace,)
            )
            connection.commit()

    def query(self, embedding: Sequence[float], top_k: int = 5) -> list[dict[str, object]]:
        if top_k <= 0:
            return []
        query_vector = list(embedding)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT item_id, text, embedding_json, metadata_json "
                "FROM vector_documents WHERE namespace = ?",
                (self.namespace,),
            ).fetchall()
        ranked: list[dict[str, object]] = []
        for row in rows:
            stored_vector = json.loads(row["embedding_json"])
            if len(stored_vector) != len(query_vector):
                continue
            ranked.append(
                {
                    "id": row["item_id"],
                    "text": row["text"],
                    "embedding": stored_vector,
                    "metadata": json.loads(row["metadata_json"]),
                    "score": self._cosine(query_vector, stored_vector),
                }
            )
        return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)[:top_k]

    def count(self) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM vector_documents WHERE namespace = ?", (self.namespace,)
            ).fetchone()
        return int(row[0])

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sqrt(sum(value * value for value in left)) or 1.0
        right_norm = sqrt(sum(value * value for value in right)) or 1.0
        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))
