import math
import re
from typing import Any, Optional

import httpx

from ..config import get_settings


class AirClient:
    """Thin ASU AIR client. Falls back to local heuristics when env keys are empty."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.air_enabled

    def transcribe(self, audio_url: str, fallback_transcript: str) -> str:
        if not self.enabled or not self.settings.AIR_ASR_MODEL:
            return fallback_transcript
        payload = {
            "model": self.settings.AIR_ASR_MODEL,
            "input": audio_url,
        }
        result = self._post("/audio/transcriptions", payload)
        return (result or {}).get("text", fallback_transcript)

    def complete_json(self, system_prompt: str, user_prompt: str) -> Optional[dict[str, Any]]:
        if not self.enabled or not self.settings.AIR_LLM_MODEL:
            return None
        payload = {
            "model": self.settings.AIR_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        result = self._post("/chat/completions", payload)
        if not result:
            return None
        try:
            import json

            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, TypeError, ValueError):
            return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.enabled and self.settings.AIR_EMBEDDING_MODEL:
            payload = {
                "model": self.settings.AIR_EMBEDDING_MODEL,
                "input": texts,
            }
            result = self._post("/embeddings", payload)
            if result and "data" in result:
                return [row["embedding"] for row in result["data"]]
        return [self.local_embed(text) for text in texts]

    def local_embed(self, text: str, dims: int = 64) -> list[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        vector = [0.0] * dims
        for token in tokens:
            idx = hash(token) % dims
            vector[idx] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _post(self, path: str, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        url = self.settings.AIR_API_BASE_URL.rstrip("/") + path
        headers = {
            "Authorization": f"Bearer {self.settings.AIR_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception:
            return None


air_client = AirClient()
