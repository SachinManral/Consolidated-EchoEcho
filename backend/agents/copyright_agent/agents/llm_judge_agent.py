# This file coordinates LLM evidence interpretation and structured evidence support.

from ..config import config
from ..services.groq_service import GroqService


class LLMJudgeAgent:
    def __init__(self, groq_service: GroqService | None = None) -> None:
        self.groq_service = groq_service or GroqService()

    def run(self, lyrics: str, evidence: dict) -> dict:
        result = self.groq_service.judge(lyrics, evidence)
        if (
            not result.get("supports_existing_song")
            and float(evidence.get("confidence", 0.0)) > config.llm_evidence_override_confidence
            and evidence.get("song_title")
        ):
            return {
                "supports_existing_song": True,
                "confidence": float(evidence.get("confidence", 0.0)),
                "reason": "Structured evidence supports an existing song match.",
            }
        return result
