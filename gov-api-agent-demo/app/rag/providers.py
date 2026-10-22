from typing import Any

import httpx


class OpenAICompatibleProvider:
    """Small HTTP client for OpenAI-compatible embeddings and chat completions."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45,
    ) -> None:
        if not base_url or not api_key or not model:
            raise ValueError("请配置模型服务的 base_url、api_key 和 model")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=self._timeout)

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}/{endpoint}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = self._post(
            "embeddings",
            {"model": self._model, "input": texts},
        )
        items = sorted(result["data"], key=lambda item: item.get("index", 0))
        vectors = [item["embedding"] for item in items]
        if len(vectors) != len(texts):
            raise RuntimeError("Embedding 服务返回的向量数量与输入文本数量不一致")
        return vectors

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        result = self._post(
            "chat/completions",
            {
                "model": self._model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )
        try:
            return result["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise RuntimeError("聊天模型返回内容格式不符合 OpenAI 兼容接口") from exc

    def close(self) -> None:
        self._client.close()
