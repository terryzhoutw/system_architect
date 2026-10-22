import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "gov_api_agent_demo")
    mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "agent_runs")
    app_name: str = os.getenv("APP_NAME", "政务 API 安全运营 Agent Demo")
    milvus_uri: str = os.getenv("MILVUS_URI", "./data/milvus_lite.db")
    milvus_token: str = os.getenv("MILVUS_TOKEN", "")
    milvus_collection: str = os.getenv("MILVUS_COLLECTION", "gov_api_knowledge")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    rag_min_score: float = float(os.getenv("RAG_MIN_SCORE", "0.25"))


settings = Settings()
