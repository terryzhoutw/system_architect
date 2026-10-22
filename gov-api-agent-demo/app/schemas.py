from typing import Any

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    alert_id: str = Field(min_length=3, max_length=64, examples=["SEC-2026-1012"])
    question: str = Field(default="请分析告警并给出排查建议", max_length=1000)
    user_id: str = Field(default="demo-user", max_length=100)


class AnalysisResponse(BaseModel):
    run_id: str
    status: str
    alert: dict[str, Any]
    business_context: dict[str, Any]
    prometheus_metrics: list[dict[str, Any]]
    application_logs: list[dict[str, Any]]
    report: dict[str, Any]


class RAGAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    user_id: str = Field(default="demo-user", max_length=100)
    scenario_id: str | None = Field(default=None, max_length=64)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RAGCitation(BaseModel):
    index: int
    id: str
    title: str
    source_name: str
    source_version: str
    scenario_id: str
    score: float
    snippet: str


class RAGAskResponse(BaseModel):
    run_id: str
    answer: str
    citations: list[RAGCitation]
