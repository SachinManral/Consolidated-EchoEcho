# This file is responsible for lyrics preprocessing ko handle karne ke liye.
# Yahan raw lyrics ko cleaned text aur tokens mein organize kiya jata hai.

from dataclasses import dataclass

from ..utils.text_cleaner import clean_text, cleanup_whitespace, tokenize


@dataclass(frozen=True)
class PreprocessedLyrics:
    original: str
    cleaned: str
    tokens: list[str]


def preprocess_lyrics(lyrics: str) -> PreprocessedLyrics:
    normalized = clean_text(lyrics)
    return PreprocessedLyrics(
        original=lyrics,
        cleaned=cleanup_whitespace(normalized),
        tokens=tokenize(normalized),
    )
