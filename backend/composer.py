"""Groq-powered song composer.

Produces the full creative spec for a song — title, key, chord progression,
section-by-section lyrics with a chord per line, and a vocal-performance plan —
using Groq's free-tier chat completions API. Falls back to a deterministic
local composition when the API is unreachable so generation never hard-fails.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
REQUEST_TIMEOUT_SECONDS = 45

CHORD_PATTERN = re.compile(r"^[A-G][#b]?m?$")

SYSTEM_PROMPT = """You are Echo Echo's resident songwriter — a hit-making lyricist and \
music theorist. Given a creative brief you compose an original, singable song spec.

Respond with ONLY a JSON object in exactly this shape:
{
  "title": "two to four word evocative song title",
  "key": "musical key, e.g. 'A minor'",
  "chords": ["Am", "F", "C", "G"],
  "sections": [
    {"name": "Verse 1", "lines": [{"chord": "Am", "text": "lyric line"}, ...]},
    {"name": "Chorus",  "lines": [...]},
    {"name": "Verse 2", "lines": [...]},
    {"name": "Bridge",  "lines": [...]},
    {"name": "Chorus",  "lines": [...]}
  ],
  "vocal": {"pitch": 1.0, "rate": 1.0, "style": "soft"}
}

Rules:
- chords: a 4-chord progression that fits the mood and key. Use ONLY simple major or
  minor triads written like C, Cm, F#, Bbm, Am, G (no 7ths, no slashes, no sus).
- Every line's "chord" must come from the progression.
- Verses: 4 lines each. Chorus: 4 lines. Bridge: 2 lines. 6-10 syllables per line,
  natural to sing at the given BPM. Never quote or imitate an existing song.
- vocal.pitch: 0.6-1.8 (lower = darker voice, higher = brighter), vocal.rate: 0.7-1.15,
  vocal.style: one word like "soft", "breathy", "bold", "dreamy".
- Lyrics must reflect the mood, theme, genre and the user's prompt."""


def _brief(payload: dict[str, Any]) -> str:
    parts = {
        "Mood": payload.get("mood"),
        "Genre": payload.get("genre"),
        "Theme": payload.get("theme"),
        "Lead instrument": payload.get("instrument"),
        "Style": payload.get("style"),
        "Tempo feel": payload.get("tempoFeel"),
        "BPM": payload.get("bpm"),
        "Creative prompt": payload.get("prompt"),
    }
    lines = [f"{label}: {value}" for label, value in parts.items() if value]
    return "Compose a song for this brief:\n" + "\n".join(lines)


def _call_groq(api_key: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0.9,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _brief(payload)},
            ],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def _clean_chord(value: Any, fallback: str) -> str:
    chord = str(value or "").strip().replace("♯", "#").replace("♭", "b")
    chord = re.sub(r"(maj|min|dim|aug|sus\d?|add\d+|7|9|11|13|/.*)$", "", chord)
    if chord.endswith("M"):
        chord = chord[:-1]
    return chord if CHORD_PATTERN.match(chord) else fallback


def _normalize(raw: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    chords = [_clean_chord(c, "") for c in (raw.get("chords") or [])]
    chords = [c for c in chords if c][:8] or ["Am", "F", "C", "G"]

    sections: list[dict[str, Any]] = []
    for index, section in enumerate(raw.get("sections") or []):
        if not isinstance(section, dict):
            continue
        lines = []
        for line_index, line in enumerate(section.get("lines") or []):
            if isinstance(line, str):
                line = {"text": line}
            if not isinstance(line, dict):
                continue
            text = str(line.get("text") or "").strip()
            if not text:
                continue
            lines.append({
                "chord": _clean_chord(line.get("chord"), chords[line_index % len(chords)]),
                "text": text,
            })
        if lines:
            sections.append({"name": str(section.get("name") or f"Section {index + 1}"), "lines": lines})
    if not sections:
        raise ValueError("Composer returned no usable lyric sections.")

    vocal = raw.get("vocal") if isinstance(raw.get("vocal"), dict) else {}

    def _clamp(value: Any, low: float, high: float, default: float) -> float:
        try:
            return round(min(high, max(low, float(value))), 2)
        except (TypeError, ValueError):
            return default

    return {
        "title": str(raw.get("title") or "").strip() or _fallback_title(payload),
        "key": str(raw.get("key") or "").strip() or "A minor",
        "chords": chords,
        "sections": sections,
        "vocal": {
            "pitch": _clamp(vocal.get("pitch"), 0.6, 1.8, 1.0),
            "rate": _clamp(vocal.get("rate"), 0.7, 1.15, 1.0),
            "style": str(vocal.get("style") or "soft").strip().lower(),
        },
    }


MINOR_MOODS = {"melancholy", "melancholic", "sad", "dark", "moody", "mysterious", "rainy", "heartbreak"}

FALLBACK_PROGRESSIONS = {
    "minor": ("A minor", ["Am", "F", "C", "G"]),
    "major": ("C major", ["C", "G", "Am", "F"]),
}


def _fallback_title(payload: dict[str, Any]) -> str:
    theme = str(payload.get("theme") or "").strip()
    mood = str(payload.get("mood") or "").strip()
    return " ".join(part for part in (mood, theme) if part) or "Echo Sketch"


def _fallback_song(payload: dict[str, Any]) -> dict[str, Any]:
    mood = str(payload.get("mood") or "dreamy").lower()
    theme = str(payload.get("theme") or "the night").lower()
    instrument = str(payload.get("instrument") or "piano").lower()
    flavor = "minor" if any(word in mood for word in MINOR_MOODS) else "major"
    key, chords = FALLBACK_PROGRESSIONS[flavor]

    def lines(texts: list[str]) -> list[dict[str, str]]:
        return [{"chord": chords[i % len(chords)], "text": text} for i, text in enumerate(texts)]

    return {
        "title": _fallback_title(payload).title(),
        "key": key,
        "chords": chords,
        "sections": [
            {"name": "Verse 1", "lines": lines([
                f"Caught inside a {mood} glow",
                f"Chasing {theme} down a road",
                f"Every {instrument} note we play",
                "Echoes what we couldn't say",
            ])},
            {"name": "Chorus", "lines": lines([
                "Sing it back to me, echo echo",
                "Turn this feeling into sound",
                "Every heartbeat, soft and mellow",
                "Plays the song that we have found",
            ])},
            {"name": "Verse 2", "lines": lines([
                f"Morning paints the {theme} new",
                "Melodies in every hue",
                "Hold the rhythm, let it grow",
                "Let the music overflow",
            ])},
            {"name": "Chorus", "lines": lines([
                "Sing it back to me, echo echo",
                "Turn this feeling into sound",
                "Every heartbeat, soft and mellow",
                "Plays the song that we have found",
            ])},
        ],
        "vocal": {"pitch": 0.9 if flavor == "minor" else 1.1, "rate": 0.95, "style": "soft"},
    }


def compose_song(payload: dict[str, Any]) -> dict[str, Any]:
    """Compose lyrics, chords and a vocal plan for the given brief."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key:
        for model in GROQ_MODELS:
            try:
                song = _normalize(_call_groq(api_key, model, payload), payload)
                song["source"] = f"groq/{model}"
                return song
            except Exception as exc:
                logger.warning("Groq composition with %s failed: %s", model, exc)
    else:
        logger.warning("GROQ_API_KEY is not configured; using fallback composer.")

    song = _fallback_song(payload)
    song["source"] = "fallback"
    return song
