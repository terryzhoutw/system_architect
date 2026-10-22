import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "gov_api_agent_demo")
    mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "agent_runs")
    app_name: str = os.getenv("APP_NAME", "政务 API 安全运营 Agent Demo")


settings = Settings()
