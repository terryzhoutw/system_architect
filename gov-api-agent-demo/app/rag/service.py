import hashlib
from typing import Any

from app.rag.milvus_store import MilvusKnowledgeStore
from app.rag.providers import OpenAICompatibleProvider
from app.settings import settings


SYSTEM_PROMPT = """你是政务 API 运维知识助手。只能根据用户问题和给出的检索资料回答。
资料不足时明确说明无法确定，不得补造制度、阈值、根因或操作步骤。
引用检索资料时使用 [1]、[2] 等编号，对应资料列表顺序。
当前知识库是完全合成的学习样例，不是真实政府制度或生产事故；回答中要提醒用户以本单位正式制度、审批流程和实际监控证据为准。
不要输出任何未出现在资料中的个人信息。涉及封禁、发布、改配置等操作时只给出核查建议，不要声称已经执行。"""

NO_CONTEXT_ANSWER = "知识库中没有检索到足够相关的资料，无法基于现有样例可靠回答。请补充经授权的正式制度或转人工核实。"


class RAGService:
    def __init__(
        self,
        embedding_provider: OpenAICompatibleProvider,
        chat_provider: OpenAICompatibleProvider | None,
        store: MilvusKnowledgeStore,
        min_score: float,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.chat_provider = chat_provider
        self.store = store
        self.min_score = min_score

    def retrieve(
        self,
        question: str,
        top_k: int,
        scenario_id: str | None = None,
    ) -> list[dict[str, Any]]:
        vector = self.embedding_provider.embed([question])[0]
        hits = self.store.search(vector, top_k=top_k, scenario_id=scenario_id)
        return [hit for hit in hits if hit["score"] >= self.min_score]

    def answer(self, question: str, hits: list[dict[str, Any]]) -> str:
        if not hits:
            return NO_CONTEXT_ANSWER
        if self.chat_provider is None:
            raise ValueError("请配置 LLM_BASE_URL、LLM_API_KEY 和 LLM_MODEL")
        context = "\n\n".join(
            f"[{index}] 标题：{hit.get('title', '')}\n"
            f"场景：{hit.get('scenario_id', '')}\n"
            f"来源：{hit.get('source_name', '')}（{hit.get('source_version', '')}）\n"
            f"适用范围：{hit.get('department_scope', '')}\n"
            f"资料：{hit.get('text', '')}"
            for index, hit in enumerate(hits, start=1)
        )
        return self.chat_provider.chat(
            SYSTEM_PROMPT,
            f"用户问题：\n{question}\n\n检索资料：\n{context}",
        )

    def ingest_records(self, records: list[dict[str, Any]], batch_size: int = 32) -> int:
        prepared = []
        for record in records:
            text = _record_text(record)
            for chunk_index, chunk in enumerate(_split_text(text)):
                source_id = str(record.get("id", "unknown"))
                stable_id = hashlib.sha256(
                    f"{source_id}:{chunk_index}:{chunk}".encode("utf-8")
                ).hexdigest()[:64]
                prepared.append({
                    "id": stable_id,
                    "document_id": source_id,
                    "title": str(record.get("title", ""))[:512],
                    "text": chunk,
                    "source_name": str(record.get("source_name", ""))[:512],
                    "source_version": str(record.get("source_version", ""))[:128],
                    "scenario_id": str(record.get("scenario_id", "unknown"))[:128],
                    "security_level": str(record.get("security_level", ""))[:128],
                    "department_scope": str(record.get("department_scope", ""))[:256],
                    "effective_from": str(record.get("effective_from", ""))[:64],
                })

        self.store.ensure_collection()
        total = 0
        for start in range(0, len(prepared), batch_size):
            batch = prepared[start : start + batch_size]
            vectors = self.embedding_provider.embed([row["text"] for row in batch])
            if any(len(vector) != self.store.dimension for vector in vectors):
                actual = next(len(vector) for vector in vectors if len(vector) != self.store.dimension)
                raise ValueError(
                    f"模型向量维度为 {actual}，Milvus 配置维度为 {self.store.dimension}；"
                    "请检查 EMBEDDING_DIMENSION 与模型配置"
                )
            total += self.store.upsert(
                [{**row, "vector": vector} for row, vector in zip(batch, vectors)]
            )
        return total

    def close(self) -> None:
        self.embedding_provider.close()
        if self.chat_provider is not None:
            self.chat_provider.close()
        self.store.close()


def build_rag_service(include_chat: bool = True) -> RAGService:
    embedding = OpenAICompatibleProvider(
        settings.embedding_base_url,
        settings.embedding_api_key,
        settings.embedding_model,
    )
    chat = (
        OpenAICompatibleProvider(
            settings.llm_base_url,
            settings.llm_api_key,
            settings.llm_model,
        )
        if include_chat
        else None
    )
    store = MilvusKnowledgeStore(
        settings.milvus_uri,
        settings.milvus_token,
        settings.milvus_collection,
        settings.embedding_dimension,
    )
    return RAGService(embedding, chat, store, settings.rag_min_score)


def _record_text(record: dict[str, Any]) -> str:
    parts = [
        f"标题：{record.get('title', '')}",
        f"问题：{record.get('user_query', '')}",
        f"正文：{record.get('content', '')}",
        f"参考结论：{record.get('reference_conclusion', '')}",
    ]
    actions = record.get("recommended_actions", [])
    if actions:
        parts.append("建议核查：" + "；".join(str(action) for action in actions))
    return "\n".join(part for part in parts if not part.endswith("："))


def _split_text(text: str, chunk_size: int = 1200, overlap: int = 160) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]
