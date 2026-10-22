import asyncio
from contextlib import asynccontextmanager
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.adapters.java_business_mock import JavaBusinessMock
from app.graph import build_analysis_graph
from app.repositories.mongo_runs import MongoRunRepository
from app.rag.graph import build_rag_graph
from app.rag.service import build_rag_service
from app.schemas import AnalysisRequest, AnalysisResponse, RAGAskRequest, RAGAskResponse
from app.settings import settings


repository = MongoRunRepository(
    settings.mongodb_uri,
    settings.mongodb_database,
    settings.mongodb_collection,
)
analysis_graph = build_analysis_graph(repository)
rag_service = None
rag_graph = None
rag_graph_lock = Lock()


def get_rag_graph():
    global rag_service, rag_graph
    with rag_graph_lock:
        if rag_graph is None:
            rag_service = build_rag_service()
            rag_graph = build_rag_graph(repository, rag_service)
    return rag_graph


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    if rag_service is not None:
        rag_service.close()
    repository.close()


app = FastAPI(
    title=settings.app_name,
    description="本地学习 Demo：FastAPI + LangGraph + 模拟 Java/Prometheus/ES + MongoDB 运行记录",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    try:
        repository.ping()
        mongo_status = "ok"
    except Exception as exc:  # health endpoint reports dependency state
        mongo_status = f"unavailable: {type(exc).__name__}"
    return {"status": "ok" if mongo_status == "ok" else "degraded", "mongodb": mongo_status}


@app.get("/api/alerts")
def list_alerts() -> list[dict]:
    return JavaBusinessMock().list_alerts()


@app.post("/api/analysis", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest) -> dict:
    run_id = str(uuid4())
    try:
        await asyncio.to_thread(
            repository.create,
            run_id,
            request.alert_id,
            request.question,
            request.user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="MongoDB 不可用，无法创建运行记录") from exc

    try:
        state = await asyncio.to_thread(
            analysis_graph.invoke,
            {
                "run_id": run_id,
                "alert_id": request.alert_id,
                "question": request.question,
            },
        )
    except KeyError as exc:
        await asyncio.to_thread(repository.fail, run_id, str(exc))
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        await asyncio.to_thread(repository.fail, run_id, f"{type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="分析流程失败，错误已记录") from exc

    return {
        "run_id": run_id,
        "status": "completed",
        "alert": state["alert"],
        "business_context": state["business_context"],
        "prometheus_metrics": state["prometheus_metrics"],
        "application_logs": state["application_logs"],
        "report": state["report"],
    }


@app.post("/api/rag/ask", response_model=RAGAskResponse)
async def rag_ask(request: RAGAskRequest) -> dict:
    run_id = str(uuid4())
    try:
        await asyncio.to_thread(
            repository.create,
            run_id,
            "rag_qa",
            request.question,
            request.user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="MongoDB 不可用，无法创建运行记录") from exc

    try:
        graph = get_rag_graph()
        state = await asyncio.to_thread(
            graph.invoke,
            {
                "run_id": run_id,
                "question": request.question,
                "top_k": request.top_k or settings.rag_top_k,
                "scenario_id": request.scenario_id,
            },
        )
    except Exception as exc:
        await asyncio.to_thread(repository.fail, run_id, f"{type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="RAG 检索或模型服务不可用；错误已记录") from exc

    return {
        "run_id": run_id,
        "answer": state["answer"],
        "citations": state["citations"],
    }


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    try:
        record = repository.get(run_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="MongoDB 不可用") from exc
    if record is None:
        raise HTTPException(status_code=404, detail="未找到该运行记录")
    return record
