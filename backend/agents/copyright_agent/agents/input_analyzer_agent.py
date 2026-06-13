# This file is responsible for incoming lyrics input ko classify karne ke liye.
# Yahan phrase, short lyric aur verse type ka lightweight analysis manage kiya jata hai.

from ..config import config
from ..services.preprocessing import PreprocessedLyrics, preprocess_lyrics


class InputAnalyzerAgent:
    def run(self, lyrics: str | PreprocessedLyrics) -> dict:
        preprocessed = (
            lyrics if isinstance(lyrics, PreprocessedLyrics) else preprocess_lyrics(lyrics)
        )
        word_count = len(preprocessed.tokens)

        if word_count <= config.input_title_or_phrase_max_words:
            input_type = "title_or_phrase"
        elif word_count <= config.input_short_lyric_max_words:
            input_type = "short_lyric"
        else:
            input_type = "verse"

        return {"type": input_type, "analysis_confidence": config.input_analysis_confidence}
