# This file is responsible for copyright risk scoring ko handle karne ke liye.
# Yahan public-domain, evidence aur LLM signals se final safety decision manage kiya jata hai.

from ..config import config


class RiskScorerAgent:
    def run(self, public_domain: dict, evidence: dict, llm_judgement: dict) -> dict:
        if public_domain.get("is_public_domain"):
            return {
                "risk": "None",
                "confidence": config.public_domain_confidence,
                "copyright_status": "Public Domain",
                "safe": True,
                "recommendation": "Safe to use.",
                "details": "Common public-domain phrase.",
            }

        evidence_confidence = float(evidence.get("confidence", 0.0))
        llm_supports_song = bool(llm_judgement.get("supports_existing_song", False))
        llm_confidence = float(llm_judgement.get("confidence", 0.0))

        if evidence_confidence > config.risk_high_confidence and llm_supports_song:
            risk = "High"
        elif evidence_confidence > config.risk_medium_confidence:
            risk = "Medium"
        elif evidence_confidence > config.risk_low_confidence:
            risk = "Low"
        else:
            risk = "None"

        confidence = max(evidence_confidence, llm_confidence)
        if risk == "None":
            confidence = max(confidence, config.original_confidence_floor)

        return {
            "risk": risk,
            "confidence": round(min(confidence, config.risk_max_confidence), 2),
            "copyright_status": "Protected" if risk in {"Medium", "High"} else "Unknown",
            "safe": risk in {"None", "Low"},
            "recommendation": self._recommendation(risk),
            "details": self._details(risk),
        }

    def _recommendation(self, risk: str) -> str:
        if risk == "High":
            return "Potential copyright conflict."
        if risk == "Medium":
            return "Review before release."
        if risk == "Low":
            return "Low concern, but consider revising if the phrase feels familiar."
        return "Appears original."

    def _details(self, risk: str) -> str:
        if risk == "High":
            return "Lyrics strongly resemble an existing song."
        if risk == "Medium":
            return "Some evidence suggests overlap with an existing song."
        if risk == "Low":
            return "Weak evidence of possible overlap was found."
        return "No strong evidence of existing lyrics."
