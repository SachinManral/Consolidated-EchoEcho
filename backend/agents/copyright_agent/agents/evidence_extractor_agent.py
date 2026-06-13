# This file is responsible for search evidence ko structured summary mein convert karne ke liye.
# Yahan song title, artist aur confidence signals manage kiye jate hain.
# Main purpose is raw search results ko scoring-ready evidence mein organize karna.

import re
from collections import Counter

from ..config import config


class EvidenceExtractorAgent:
    def _extract_title_artist(self, result: dict) -> tuple[str, str]:
        title = result.get("title", "").strip()
        snippet = result.get("snippet", "").strip()

        local_match = re.search(r"appears in (?P<title>.+?) by (?P<artist>.+?)\.", snippet)
        if local_match:
            return local_match.group("title").strip(), local_match.group("artist").strip()

        cleaned_title = re.sub(r"\b(lyrics|song|official|genius|spotify)\b", "", title, flags=re.I)
        cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip(" -|")

        for separator in [" - ", " by ", " | "]:
            if separator in cleaned_title:
                left, right = cleaned_title.split(separator, 1)
                if "lyrics" in title.lower():
                    return left.strip(), right.strip()
                return left.strip(), right.strip()

        return cleaned_title, ""

    def run(self, search_results: list[dict]) -> dict:
        if not search_results:
            return {
                "song_title": "",
                "artist": "",
                "confidence": 0.0,
                "sources_found": 0,
            }

        candidates: list[tuple[str, str]] = []
        for result in search_results:
            song_title, artist = self._extract_title_artist(result)
            if song_title:
                candidates.append((song_title, artist))

        if not candidates:
            return {
                "song_title": "",
                "artist": "",
                "confidence": 0.0,
                "sources_found": len(search_results),
            }

        counter = Counter(candidates)
        (song_title, artist), count = counter.most_common(1)[0]
        sources_found = len(search_results)
        source_ratio = count / max(len(candidates), 1)
        confidence = min(
            config.evidence_max_confidence,
            config.evidence_base_confidence
            + (config.evidence_source_weight * sources_found)
            + (config.evidence_source_ratio_weight * source_ratio),
        )

        if any(
            str(result.get("url", "")).startswith(config.evidence_local_url_prefix)
            for result in search_results
        ):
            confidence = max(confidence, config.evidence_local_confidence)

        return {
            "song_title": song_title,
            "artist": artist,
            "confidence": round(confidence, 2),
            "sources_found": sources_found,
        }
