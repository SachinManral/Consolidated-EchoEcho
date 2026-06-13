# This file is responsible for public-domain lyrics checks ko handle karne ke liye.
# Yahan known songs, common phrases aur public-domain matching manage kiya jata hai.

import json
from pathlib import Path

from ..config import config
from ..logger import get_logger
from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


logger = get_logger(__name__)

DEFAULT_PUBLIC_DOMAIN_SONGS = [
    {
        "title": "Happy Birthday To You",
        "artist": "Traditional",
        "phrases": ["happy birthday to you", "happy birthday"],
    },
    {"title": "Jingle Bells", "artist": "Traditional", "phrases": ["jingle bells"]},
    {"title": "Silent Night", "artist": "Traditional", "phrases": ["silent night"]},
    {
        "title": "Twinkle Twinkle Little Star",
        "artist": "Traditional",
        "phrases": ["twinkle twinkle little star"],
    },
    {
        "title": "Old MacDonald Had a Farm",
        "artist": "Traditional",
        "phrases": ["old macdonald had a farm"],
    },
    {
        "title": "Mary Had a Little Lamb",
        "artist": "Traditional",
        "phrases": ["mary had a little lamb"],
    },
]


class PublicDomainAgent:
    def __init__(
        self,
        phrases_path: Path | None = None,
        songs_path: Path | None = None,
    ) -> None:
        self.phrases_path = phrases_path or config.public_domain_phrases_path
        self.songs_path = songs_path or config.public_domain_songs_path
        self.songs = self._load_songs()
        self.phrases = self._load_phrases()

    def _load_songs(self) -> list[dict]:
        try:
            with self.songs_path.open("r", encoding="utf-8") as songs_file:
                return json.load(songs_file)
        except Exception as exc:
            logger.info("Public-domain song database unavailable: %s", exc)
            return DEFAULT_PUBLIC_DOMAIN_SONGS

    def _load_phrases(self) -> list[str]:
        try:
            with self.phrases_path.open("r", encoding="utf-8") as phrases_file:
                phrases = json.load(phrases_file)
        except Exception as exc:
            logger.info("Public-domain phrase database unavailable: %s", exc)
            phrases = []

        song_phrases: list[str] = []
        for song in self.songs:
            song_phrases.extend(song.get("phrases", []))
            song_phrases.append(song.get("title", ""))
        return [preprocess_lyrics(phrase).cleaned for phrase in phrases + song_phrases]

    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )

        for song in self.songs:
            for phrase in song.get("phrases", []) + [song.get("title", "")]:
                normalized_phrase = preprocess_lyrics(phrase).cleaned
                if normalized_phrase and normalized_phrase in preprocessed.cleaned:
                    return {
                        "is_public_domain": True,
                        "song_title": song.get("title", ""),
                        "artist": song.get("artist", ""),
                        "reason": "Common public-domain expression.",
                    }

        for phrase in self.phrases:
            if phrase and phrase in preprocessed.cleaned:
                return {
                    "is_public_domain": True,
                    "song_title": "",
                    "artist": "",
                    "reason": "Common public-domain expression.",
                }

        return {
            "is_public_domain": False,
            "song_title": "",
            "artist": "",
            "reason": "",
        }
