# This file is responsible for application configuration ko centralize karne ke liye.
# Yahan environment variables, service settings aur scoring thresholds manage kiye jate hain.
# Main purpose is runtime behavior ko consistent aur configurable rakhna.

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(_: Path | None = None) -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[2]
load_dotenv(PROJECT_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _optional_env(name: str) -> str | None:
    value = _env(name)
    return value or None


@dataclass(frozen=True)
class CopyrightAgentConfig:
    app_title: str = "Inspiration Safety Advisor"
    app_version: str = "2.0.0"
    copyright_check_route: str = "/check-copyright"
    log_level: str = "INFO"

    serpapi_api_key: str | None = _optional_env("SERPAPI_API_KEY")
    groq_api_key: str | None = _optional_env("GROQ_API_KEY")

    search_timeout_seconds: int = 8
    serpapi_result_count: int = 5

    groq_chat_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama-3.1-8b-instant"
    groq_retries: int = 3
    groq_backoff_max_seconds: int = 4

    local_songs_path: Path = BASE_DIR / "database" / "songs.json"
    public_domain_phrases_path: Path = BASE_DIR / "database" / "public_domain_phrases.json"
    public_domain_songs_path: Path = BASE_DIR / "database" / "public_domain_songs.json"

    input_title_or_phrase_max_words: int = 3
    input_short_lyric_max_words: int = 10
    input_analysis_confidence: float = 0.95

    evidence_base_confidence: float = 0.35
    evidence_source_weight: float = 0.12
    evidence_source_ratio_weight: float = 0.40
    evidence_max_confidence: float = 0.99
    evidence_local_confidence: float = 0.97
    evidence_local_url_prefix: str = "local://"

    llm_evidence_override_confidence: float = 0.95

    risk_high_confidence: float = 0.95
    risk_medium_confidence: float = 0.75
    risk_low_confidence: float = 0.40
    public_domain_confidence: float = 0.98
    original_confidence_floor: float = 0.91
    risk_max_confidence: float = 0.99

    def validate(self) -> None:
        if not self.copyright_check_route.startswith("/"):
            raise ValueError("COPYRIGHT_CHECK_ROUTE must start with '/'.")
        if self.log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
            raise ValueError("LOG_LEVEL must be a valid Python logging level.")

        positive_ints = {
            "SEARCH_TIMEOUT_SECONDS": self.search_timeout_seconds,
            "SERPAPI_RESULT_COUNT": self.serpapi_result_count,
            "GROQ_RETRIES": self.groq_retries,
            "GROQ_BACKOFF_MAX_SECONDS": self.groq_backoff_max_seconds,
        }
        for name, value in positive_ints.items():
            if value < 1:
                raise ValueError(f"{name} must be greater than zero.")

        confidence_values = {
            "INPUT_ANALYSIS_CONFIDENCE": self.input_analysis_confidence,
            "EVIDENCE_BASE_CONFIDENCE": self.evidence_base_confidence,
            "EVIDENCE_SOURCE_WEIGHT": self.evidence_source_weight,
            "EVIDENCE_SOURCE_RATIO_WEIGHT": self.evidence_source_ratio_weight,
            "EVIDENCE_MAX_CONFIDENCE": self.evidence_max_confidence,
            "EVIDENCE_LOCAL_CONFIDENCE": self.evidence_local_confidence,
            "LLM_EVIDENCE_OVERRIDE_CONFIDENCE": self.llm_evidence_override_confidence,
            "RISK_HIGH_CONFIDENCE": self.risk_high_confidence,
            "RISK_MEDIUM_CONFIDENCE": self.risk_medium_confidence,
            "RISK_LOW_CONFIDENCE": self.risk_low_confidence,
            "PUBLIC_DOMAIN_CONFIDENCE": self.public_domain_confidence,
            "ORIGINAL_CONFIDENCE_FLOOR": self.original_confidence_floor,
            "RISK_MAX_CONFIDENCE": self.risk_max_confidence,
        }
        for name, value in confidence_values.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")

        if self.input_title_or_phrase_max_words < 1:
            raise ValueError("INPUT_TITLE_OR_PHRASE_MAX_WORDS must be greater than zero.")
        if self.input_short_lyric_max_words < self.input_title_or_phrase_max_words:
            raise ValueError(
                "INPUT_SHORT_LYRIC_MAX_WORDS must be greater than or equal to "
                "INPUT_TITLE_OR_PHRASE_MAX_WORDS."
            )


config = CopyrightAgentConfig()
config.validate()
