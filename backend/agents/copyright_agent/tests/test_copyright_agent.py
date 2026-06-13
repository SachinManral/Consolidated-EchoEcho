# This file is responsible for copyright agent behavior tests ko organize karne ke liye.
# Yahan agents, services aur API flow ke expected outcomes validate kiye jate hain.

import pytest
from pydantic import ValidationError

from copyright_agent.agents.evidence_extractor_agent import EvidenceExtractorAgent
from copyright_agent.agents.input_analyzer_agent import InputAnalyzerAgent
from copyright_agent.agents.public_domain_agent import PublicDomainAgent
from copyright_agent.agents.risk_scorer_agent import RiskScorerAgent
from copyright_agent.agents.search_agent import SearchAgent
from copyright_agent.main import check_copyright
from copyright_agent.models.request_model import CopyrightCheckRequest
from copyright_agent.services.groq_service import GroqService


class WorkingProvider:
    def search(self, query):
        return [
            {
                "title": "Never Gonna Give You Up lyrics - Rick Astley",
                "snippet": "Never gonna give you up appears in Never Gonna Give You Up by Rick Astley.",
                "url": "https://example.test/song",
            }
        ]


def test_input_analyzer_classifies_short_inputs():
    agent = InputAnalyzerAgent()

    assert agent.run("hello")["type"] == "title_or_phrase"
    assert agent.run("through the darkness I found my light")["type"] == "short_lyric"
    assert agent.run("one two three four five six seven eight nine ten eleven")["type"] == "verse"


def test_public_domain_agent_matches_known_song_phrase():
    result = PublicDomainAgent().run("happy birthday to you jake")

    assert result["is_public_domain"] is True
    assert result["song_title"] == "Happy Birthday To You"
    assert result["artist"] == "Traditional"


def test_search_agent_uses_google_provider():
    agent = SearchAgent(providers={"google": WorkingProvider()})

    results = agent.run("never gonna give you up")

    assert results
    assert results[0]["title"].startswith("Never Gonna Give You Up")


def test_evidence_extractor_summarizes_structured_evidence():
    results = [
        {
            "title": "Never Gonna Give You Up lyrics - Rick Astley",
            "snippet": "Never gonna give you up appears in Never Gonna Give You Up by Rick Astley.",
            "url": "https://example.test/one",
        },
        {
            "title": "Never Gonna Give You Up song - Rick Astley",
            "snippet": "A result about the same song.",
            "url": "https://example.test/two",
        },
    ]

    evidence = EvidenceExtractorAgent().run(results)

    assert evidence["song_title"] == "Never Gonna Give You Up"
    assert evidence["artist"] == "Rick Astley"
    assert evidence["sources_found"] == 2
    assert evidence["confidence"] > 0.75


def test_groq_parser_repairs_json_wrapped_in_text():
    parsed = GroqService().parse_json(
        'Here is the answer: {"supports_existing_song": true, "confidence": 0.91, "reason": "match"}'
    )

    assert parsed["supports_existing_song"] is True
    assert parsed["confidence"] == 0.91


def test_risk_scorer_uses_requested_rules():
    scorer = RiskScorerAgent()

    high = scorer.run(
        {"is_public_domain": False},
        {"confidence": 0.97},
        {"supports_existing_song": True, "confidence": 0.91},
    )
    public_domain = scorer.run(
        {"is_public_domain": True},
        {"confidence": 0.99},
        {"supports_existing_song": True, "confidence": 0.99},
    )

    assert high["risk"] == "High"
    assert high["safe"] is False
    assert public_domain["risk"] == "None"
    assert public_domain["safe"] is True


def test_original_lyrics_return_safe_unknown_status():
    response = check_copyright(
        CopyrightCheckRequest(lyrics="through the darkness I found my light")
    )

    assert response.safe is True
    assert response.risk == "None"
    assert response.copyright_status == "Unknown"
    assert response.song_title == ""


def test_known_song_returns_high_risk():
    response = check_copyright(
        CopyrightCheckRequest(
            lyrics="never gonna give you up never gonna let you down"
        )
    )

    assert response.safe is False
    assert response.risk == "High"
    assert response.copyright_status == "Protected"
    assert response.song_title == "Never Gonna Give You Up"
    assert response.artist == "Rick Astley"


def test_empty_lyrics_are_rejected():
    with pytest.raises(ValidationError):
        CopyrightCheckRequest(lyrics="")


def test_public_domain_song_returns_no_risk():
    response = check_copyright(CopyrightCheckRequest(lyrics="happy birthday to you jake"))

    assert response.safe is True
    assert response.risk == "None"
    assert response.copyright_status == "Public Domain"
    assert response.song_title == "Happy Birthday To You"
