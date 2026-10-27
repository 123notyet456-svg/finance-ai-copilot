"""POC 记录的 SQLite Repository Adapter。"""

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


class SQLiteRepository:
    provider_name = "sqlite"

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS poc_records (
                    collection TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (collection, record_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_poc_records_collection_created "
                "ON poc_records(collection, created_at DESC)"
            )
            connection.commit()

    def save(self, collection: str, record: dict[str, object]) -> str:
        if not collection.strip():
            raise ValueError("collection 不能为空")
        record_id = str(record.get("id") or uuid4())
        payload = {key: value for key, value in record.items() if key != "id"}
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO poc_records
                    (collection, record_id, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(collection, record_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (
                    collection,
                    record_id,
                    json.dumps(payload, ensure_ascii=False, default=str),
                    now,
                    now,
                ),
            )
            connection.commit()
        return record_id

    def list(self, collection: str) -> list[dict[str, object]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT record_id, payload_json, created_at, updated_at "
                "FROM poc_records WHERE collection = ? ORDER BY created_at DESC",
                (collection,),
            ).fetchall()
        return [
            {
                "id": row["record_id"],
                **json.loads(row["payload_json"]),
                "_stored_at": row["created_at"],
                "_updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def count(self, collection: str) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM poc_records WHERE collection = ?", (collection,)
            ).fetchone()
        return int(row[0])

