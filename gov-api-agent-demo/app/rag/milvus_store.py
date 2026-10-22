from typing import Any

from pymilvus import MilvusClient


class MilvusKnowledgeStore:
    def __init__(
        self,
        uri: str,
        token: str,
        collection_name: str,
        dimension: int,
    ) -> None:
        if dimension <= 1:
            raise ValueError("Embedding 维度必须大于 1")
        self.collection_name = collection_name
        self.dimension = dimension
        self._client = MilvusClient(uri=uri, token=token or None)

    def ensure_collection(self) -> None:
        if not self._client.has_collection(self.collection_name):
            self._client.create_collection(
                collection_name=self.collection_name,
                dimension=self.dimension,
                primary_field_name="id",
                id_type="string",
                vector_field_name="vector",
                metric_type="COSINE",
                auto_id=False,
                max_length=128,
                enable_dynamic_field=True,
            )

    def upsert(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        self.ensure_collection()
        for row in rows:
            if len(row["vector"]) != self.dimension:
                raise ValueError(
                    f"向量维度为 {len(row['vector'])}，配置维度为 {self.dimension}"
                )
        self._client.upsert(collection_name=self.collection_name, data=rows)
        return len(rows)

    def search(
        self,
        vector: list[float],
        top_k: int,
        scenario_id: str | None = None,
    ) -> list[dict[str, Any]]:
        self.ensure_collection()
        if len(vector) != self.dimension:
            raise ValueError(
                f"查询向量维度为 {len(vector)}，配置维度为 {self.dimension}"
            )
        filters = []
        if scenario_id:
            escaped = scenario_id.replace("\\", "\\\\").replace('"', '\\"')
            filters.append(f'scenario_id == "{escaped}"')
        result = self._client.search(
            collection_name=self.collection_name,
            data=[vector],
            filter=" and ".join(filters),
            limit=top_k,
            output_fields=[
                "document_id",
                "title",
                "text",
                "source_name",
                "source_version",
                "scenario_id",
                "security_level",
                "department_scope",
                "effective_from",
            ],
        )
        hits = []
        for hit in result[0] if result else []:
            entity = hit.get("entity", {})
            hits.append({"id": hit["id"], "score": float(hit["distance"]), **entity})
        return hits

    def close(self) -> None:
        self._client.close()
