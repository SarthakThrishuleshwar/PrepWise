import math
import threading
from typing import Protocol
import httpx
from app.core.errors import AppError


class ModelGateway(Protocol):
    def generate(self, messages: list[dict], schema: dict) -> dict: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def capabilities(self) -> dict: ...


class OllamaGateway:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self._permit = threading.Lock()

    def _client(self):
        return httpx.Client(base_url=self.settings.model_base_url, timeout=httpx.Timeout(self.settings.model_timeout_seconds, connect=2), transport=self.transport)

    def capabilities(self):
        models = []
        if self.settings.reasoning_model or self.settings.embedding_model:
            try:
                with self._client() as client:
                    response = client.get("/api/tags", timeout=2)
                    response.raise_for_status()
                    models = [item["name"] for item in response.json().get("models", [])]
            except (httpx.HTTPError, ValueError, KeyError):
                pass
        return {"provider": "ollama", "reasoning_model": self.settings.reasoning_model or None,
                "embedding_model": self.settings.embedding_model or None,
                "reasoning_available": self.settings.reasoning_model in models,
                "embedding_available": self.settings.embedding_model in models,
                "test_mode": False}

    def generate(self, messages: list[dict], schema: dict) -> dict:
        if not self.settings.reasoning_model:
            raise AppError("MODEL_NOT_CONFIGURED", "Configure the reasoning model before generation.", 503)
        try:
            with self._permit, self._client() as client:
                response = client.post("/api/chat", json={"model": self.settings.reasoning_model, "messages": messages, "format": schema, "stream": False, "options": {"temperature": 0}})
                response.raise_for_status()
                import json
                content = json.loads(response.json()["message"]["content"])
                if not isinstance(content, dict):
                    raise ValueError("Expected structured object")
                return content
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise AppError("MODEL_UNAVAILABLE", "The model did not return a valid structured response.", 503) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.embedding_model:
            raise AppError("MODEL_NOT_CONFIGURED", "Configure an embedding model before semantic retrieval.", 503)
        try:
            with self._permit, self._client() as client:
                response = client.post("/api/embed", json={"model": self.settings.embedding_model, "input": texts})
                response.raise_for_status()
                vectors = response.json()["embeddings"]
                if len(vectors) != len(texts) or not vectors or not vectors[0]:
                    raise ValueError("Missing vectors")
                dimension = len(vectors[0])
                for vector in vectors:
                    if len(vector) != dimension or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vector) or not any(vector):
                        raise ValueError("Invalid embedding vector")
                return vectors
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise AppError("EMBEDDING_UNAVAILABLE", "The embedding response is unavailable or invalid.", 503) from exc
