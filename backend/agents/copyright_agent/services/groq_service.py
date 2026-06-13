# This file handles Groq-backed evidence interpretation for copyright scoring.

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from ..config import config
from ..logger import get_logger


logger = get_logger(__name__)


class GroqService:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client

    def parse_json(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            return json.loads(content[start : end + 1])

    def neutral_response(self) -> dict[str, Any]:
        return {
            "supports_existing_song": False,
            "confidence": 0.0,
            "reason": "Groq analysis unavailable.",
        }

    def judge(self, lyrics: str, evidence: dict) -> dict[str, Any]:
        if not config.groq_api_key:
            logger.info("Groq API key is not configured.")
            return self.neutral_response()

        payload = {
            "model": config.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an evidence interpreter for an inspiration safety advisor. "
                        "Do not decide legal risk. Answer only valid JSON with keys: "
                        "supports_existing_song, confidence, reason."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Lyrics: {lyrics}\n"
                        f"Evidence: {json.dumps(evidence, ensure_ascii=True)}"
                    ),
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {config.groq_api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None

        for attempt in range(1, config.groq_retries + 1):
            try:
                if self.client:
                    response = self.client.post(
                        config.groq_chat_url,
                        headers=headers,
                        json=payload,
                        timeout=config.search_timeout_seconds,
                    )
                else:
                    response = httpx.post(
                        config.groq_chat_url,
                        headers=headers,
                        json=payload,
                        timeout=config.search_timeout_seconds,
                    )
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                parsed = self.parse_json(content or "{}")
                return {
                    "supports_existing_song": bool(
                        parsed.get("supports_existing_song", False)
                    ),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "reason": str(parsed.get("reason", "")),
                }
            except Exception as exc:
                last_error = exc
                logger.info("Groq judge attempt %s failed: %s", attempt, exc)
                if attempt < config.groq_retries:
                    time.sleep(min(2 ** (attempt - 1), config.groq_backoff_max_seconds))

        logger.info("Groq judge unavailable after retries: %s", last_error)
        return self.neutral_response()
