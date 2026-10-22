from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.rag.service import RAGService
from app.repositories.mongo_runs import MongoRunRepository


class RAGState(TypedDict, total=False):
    run_id: str
    question: str
    top_k: int
    scenario_id: str | None
    hits: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]


def build_rag_graph(repository: MongoRunRepository, rag: RAGService):
    def retrieve(state: RAGState) -> dict[str, Any]:
        hits = rag.retrieve(
            state["question"],
            top_k=state["top_k"],
            scenario_id=state.get("scenario_id"),
        )
        return {"hits": hits}

    def draft_answer(state: RAGState) -> dict[str, Any]:
        answer = rag.answer(state["question"], state["hits"])
        citations = [
            {
                "index": index,
                "id": hit["document_id"],
                "title": hit.get("title", ""),
                "source_name": hit.get("source_name", ""),
                "source_version": hit.get("source_version", ""),
                "scenario_id": hit.get("scenario_id", ""),
                "score": hit["score"],
                "snippet": hit.get("text", "")[:500],
            }
            for index, hit in enumerate(state["hits"], start=1)
        ]
        return {"answer": answer, "citations": citations}

    def persist(state: RAGState) -> dict[str, Any]:
        repository.complete(
            state["run_id"],
            {
                "answer": state["answer"],
                "citations": state["citations"],
                "retrieved_count": len(state["hits"]),
            },
        )
        return {}

    builder = StateGraph(RAGState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("draft_answer", draft_answer)
    builder.add_node("persist", persist)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "draft_answer")
    builder.add_edge("draft_answer", "persist")
    builder.add_edge("persist", END)
    return builder.compile()
