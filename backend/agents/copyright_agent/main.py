# This file is responsible for FastAPI copyright check flow ko handle karne ke liye.
# Yahan request pipeline, agent orchestration aur final API response manage kiya jata hai.
# Main purpose is lyrics safety workflow ko single backend entrypoint se organize karna.

from fastapi import FastAPI

from .config import config
from .agents.evidence_extractor_agent import EvidenceExtractorAgent
from .agents.input_analyzer_agent import InputAnalyzerAgent
from .agents.llm_judge_agent import LLMJudgeAgent
from .agents.public_domain_agent import PublicDomainAgent
from .agents.risk_scorer_agent import RiskScorerAgent
from .agents.search_agent import SearchAgent
from .logger import get_logger
from .models.request_model import CopyrightCheckRequest
from .models.response_model import CopyrightCheckResponse
from .services.preprocessing import preprocess_lyrics


app = FastAPI(title=config.app_title, version=config.app_version)
logger = get_logger(__name__)


def _public_domain_response(public_domain: dict, score: dict) -> CopyrightCheckResponse:
    return CopyrightCheckResponse(
        safe=score["safe"],
        risk=score["risk"],
        confidence=score["confidence"],
        copyright_status=score["copyright_status"],
        song_title=public_domain.get("song_title", ""),
        artist=public_domain.get("artist", ""),
        recommendation=score["recommendation"],
        details=score["details"],
    )


def _evidence_response(evidence: dict, score: dict) -> CopyrightCheckResponse:
    return CopyrightCheckResponse(
        safe=score["safe"],
        risk=score["risk"],
        confidence=score["confidence"],
        copyright_status=score["copyright_status"],
        song_title=evidence.get("song_title", "") if score["risk"] != "None" else "",
        artist=evidence.get("artist", "") if score["risk"] != "None" else "",
        recommendation=score["recommendation"],
        details=score["details"],
    )


@app.post(config.copyright_check_route, response_model=CopyrightCheckResponse)
def check_copyright(request: CopyrightCheckRequest) -> CopyrightCheckResponse:
    try:
        preprocessed = preprocess_lyrics(request.lyrics)
        InputAnalyzerAgent().run(preprocessed)

        public_domain = PublicDomainAgent().run(preprocessed)
        search_results = SearchAgent().run(request.lyrics)
        evidence = EvidenceExtractorAgent().run(search_results)
        llm_judgement = LLMJudgeAgent().run(request.lyrics, evidence)
        score = RiskScorerAgent().run(public_domain, evidence, llm_judgement)

        if public_domain.get("is_public_domain"):
            return _public_domain_response(public_domain, score)
        return _evidence_response(evidence, score)
    except Exception as exc:
        logger.exception("Copyright advisor failed safely: %s", exc)
        return CopyrightCheckResponse(
            safe=True,
            risk="None",
            confidence=0.0,
            copyright_status="Unknown",
            song_title="",
            artist="",
            recommendation="Appears original.",
            details="No strong evidence of existing lyrics.",
        )


# Future integration note:
# from copyright_agent.main import app as copyright_agent_app
# parent_app.mount("/copyright", copyright_agent_app)
