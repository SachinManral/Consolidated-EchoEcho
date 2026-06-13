from __future__ import annotations

import os
from typing import Any

try:
    from crewai import Agent, Crew, LLM, Task
except ImportError:  # pragma: no cover - exercised only when optional dependency is missing.
    Agent = Crew = LLM = Task = None  # type: ignore[assignment]


class LyricsGenerationError(RuntimeError):
    pass


def create_lyrics_agent(llm: LLM) -> Agent:
    if Agent is None:
        raise LyricsGenerationError("CrewAI is not installed.")

    return Agent(
        role="Lyricist",
        goal=(
            "Write lyrics that complement the mood, melody, and chord progression. "
            "Include a verse and a chorus. Lyrics should match the rhythmic feel of the melody."
        ),
        backstory=(
            "You are an award-winning lyricist who has written songs across pop, indie, "
            "R&B, and folk. You craft words that feel natural to sing and deepen the "
            "emotional impact of the music."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def _default_model() -> str | None:
    if os.getenv("GROQ_API_KEY"):
        return "groq/llama-3.1-8b-instant"
    return None


def _create_llm() -> LLM:
    if LLM is None:
        raise LyricsGenerationError("CrewAI is not installed.")

    model = _default_model()
    if not model:
        raise LyricsGenerationError("No lyrics LLM API key is configured.")
    return LLM(model=model)


def generate_lyrics(context: dict[str, Any]) -> dict[str, str]:
    if Crew is None or Task is None:
        raise LyricsGenerationError("CrewAI is not installed.")

    mood = context.get("mood") or "the selected mood"
    genre = context.get("genre") or context.get("style") or "the selected style"
    theme = context.get("theme") or context.get("prompt") or "the song idea"
    tempo = context.get("tempo") or context.get("bpm") or "the chosen"
    prompt = context.get("prompt") or ""

    llm = _create_llm()
    agent = create_lyrics_agent(llm)
    task = Task(
        description=(
            "Write original, singable lyrics for this generated music idea.\n"
            f"Mood: {mood}\n"
            f"Genre/style: {genre}\n"
            f"Theme: {theme}\n"
            f"Tempo: {tempo} BPM\n"
            f"Music prompt: {prompt}\n\n"
            "Use this structure exactly: [Verse 1], [Chorus], [Verse 2], [Chorus]. "
            "Avoid quoting or imitating existing songs."
        ),
        expected_output=(
            "Original lyrics with section labels [Verse 1], [Chorus], [Verse 2], [Chorus]."
        ),
        agent=agent,
    )
    result = Crew(agents=[agent], tasks=[task], verbose=False).kickoff()
    text = str(result).strip()
    if not text:
        raise LyricsGenerationError("Lyrics agent returned an empty response.")
    return {"text": text, "structure": "verse/chorus"}
