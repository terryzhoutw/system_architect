from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection


class MongoRunRepository:
    """Stores one document per Agent execution in MongoDB."""

    def __init__(self, uri: str, database: str, collection: str = "agent_runs") -> None:
        self._client = MongoClient(uri, serverSelectionTimeoutMS=2500)
        self._collection: Collection = self._client[database][collection]

    def ping(self) -> bool:
        self._client.admin.command("ping")
        return True

    def create(self, run_id: str, alert_id: str, question: str, user_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._collection.insert_one({
            "run_id": run_id,
            "alert_id": alert_id,
            "question": question,
            "user_id": user_id,
            "status": "running",
            "created_at": now,
            "updated_at": now,
        })

    def complete(self, run_id: str, result: dict[str, Any]) -> None:
        self._collection.update_one(
            {"run_id": run_id},
            {"$set": {
                "status": "completed",
                "result": result,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

    def fail(self, run_id: str, error: str) -> None:
        self._collection.update_one(
            {"run_id": run_id},
            {"$set": {
                "status": "failed",
                "error": error[:500],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

    def get(self, run_id: str) -> dict[str, Any] | None:
        document = self._collection.find_one({"run_id": run_id}, {"_id": 0})
        return document

    def close(self) -> None:
        self._client.close()
