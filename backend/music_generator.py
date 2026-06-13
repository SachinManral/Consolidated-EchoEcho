import logging
import time
from typing import Any
from pathlib import Path


MODEL_ID = "facebook/musicgen-small"
SAMPLE_RATE = 32_000
TARGET_SECONDS = 30
TOKENS_PER_SECOND = 50
MAX_NEW_TOKENS = TARGET_SECONDS * TOKENS_PER_SECOND
GENERATED_DIR = Path(__file__).resolve().parent / "generated"

logger = logging.getLogger("echoecho.music_generator")

KNOWN_INSTRUMENTS = [
    "piano",
    "acoustic guitar",
    "electric guitar",
    "guitar",
    "violin",
    "strings",
    "bass",
    "drums",
    "synthesizers",
    "saxophone",
    "flute",
    "choir pads",
    "brass",
    "percussion",
]

MOOD_DESCRIPTIONS = {
    "sad": "melancholic, emotional, reflective, lonely",
    "melancholic": "melancholic, emotional, reflective, lonely",
    "romantic": "warm, intimate, nostalgic",
    "happy": "uplifting, bright, cheerful",
    "nostalgic": "dreamy memories, emotional atmosphere",
    "hopeful": "gentle optimism, tender warmth, forward-looking emotion",
    "dreamy": "soft-focus, floating, hazy, dreamlike",
    "dark": "shadowy, tense, brooding",
    "energetic": "driving, lively, high-motion",
    "epic": "wide, cinematic, dramatic",
    "relaxed": "calm, unhurried, easygoing",
}

THEME_DESCRIPTIONS = {
    "love": "sentimental atmosphere, emotional recollections, longing, dreamy mood",
    "memories": "sentimental atmosphere, emotional recollections, longing, dreamy mood",
    "love and memories": "sentimental atmosphere, emotional recollections, longing, dreamy mood",
    "heartbreak": "sorrow, loneliness, melancholy",
    "rain": "soft rainy ambience",
    "rainy day": "soft rainy ambience",
    "night": "late-night atmosphere",
    "city night": "late-night atmosphere",
    "summer": "warm nostalgic memories",
    "sunset": "golden-hour warmth, reflective ending, soft glow",
    "space": "weightless atmosphere, vast distance, quiet wonder",
    "fantasy": "enchanted atmosphere, storybook wonder",
    "cyberpunk": "neon-lit tension, futuristic city atmosphere",
    "adventure": "curious movement, open-road momentum",
    "nature": "organic calm, open air, gentle landscape",
}


def _format_list(values: list[str]) -> str:
    """Format prompt selections as a readable English list."""
    cleaned = [value.strip() for value in values if value and value.strip()]

    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return f"{', '.join(cleaned[:-1])} and {cleaned[-1]}"


def _describe_values(values: list[str], descriptions: dict[str, str]) -> list[str]:
    described = []
    for value in values:
        key = value.strip().lower()
        if not key:
            continue
        described.append(descriptions.get(key, key))
    return described


def _describe_themes(themes: list[str]) -> list[str]:
    keys = {theme.strip().lower() for theme in themes if theme.strip()}
    described = []

    if "love" in keys and "memories" in keys:
        described.append(THEME_DESCRIPTIONS["love and memories"])
        keys.remove("love")
        keys.remove("memories")

    for key in keys:
        described.append(THEME_DESCRIPTIONS.get(key, key))

    return described


def _build_instrument_constraints(instruments: list[str]) -> list[str]:
    selected = [instrument.strip().lower() for instrument in instruments if instrument.strip()]
    if not selected:
        return [
            "Sparse instrumental arrangement.",
            "No vocals.",
            "No lyrics.",
        ]

    selected_set = set(selected)
    selected_display = _format_list(selected)
    constraints = []

    if len(selected) == 1:
        instrument = selected[0]
        constraints.extend(
            [
                f"Solo {instrument} performance.",
                f"Solo {instrument} only.",
                f"Only {instrument}.",
                "No accompanying instruments.",
            ]
        )
    elif len(selected) == 2:
        constraints.extend(
            [
                f"{selected_display} duet only.",
                f"Only {selected_display}.",
                "No hidden accompaniment.",
            ]
        )
    else:
        constraints.extend(
            [
                f"{selected_display} ensemble only.",
                f"Only these instruments: {selected_display}.",
                "No hidden accompaniment.",
            ]
        )

    negative_instruments = []
    for instrument in KNOWN_INSTRUMENTS:
        covered = instrument in selected_set
        if instrument == "guitar":
            covered = "acoustic guitar" in selected_set or "electric guitar" in selected_set
        if instrument == "percussion":
            covered = "drums" in selected_set
        if instrument == "synthesizers":
            covered = "synth" in selected_set
        if not covered:
            negative_instruments.append(instrument)

    for instrument in dict.fromkeys(negative_instruments):
        constraints.append(f"No {instrument}.")

    constraints.extend(["Instrumental only.", "No vocals.", "No lyrics."])
    return constraints


def load_model() -> tuple[Any, Any]:
    """Load MusicGen once for the API process lifetime."""
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    start_time = time.perf_counter()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info("Loading %s on %s", MODEL_ID, device)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL_ID)
    if device.type == "cuda":
        model.to(device=device, dtype=torch.float16)
    else:
        model.to(device)
    model.eval()

    logger.info("Model loaded in %.1f seconds", time.perf_counter() - start_time)
    return model, processor


def build_prompt(
    moods: list[str],
    genres: list[str],
    themes: list[str],
    instruments: list[str],
    tempo: int,
    complexity: str,
    energy: int,
    custom_prompt: str,
    duration_seconds: int = TARGET_SECONDS,
) -> str:
    """Build the final prompt sent to MusicGen."""
    prompt_parts = [f"{duration_seconds}-second instrumental inspiration sketch."]

    if moods:
        mood_text = _format_list(_describe_values(moods, MOOD_DESCRIPTIONS))
        prompt_parts.append(f"{mood_text} mood.")
    if genres:
        prompt_parts.append(f"{_format_list([genre.lower() for genre in genres])} style.")
    if themes:
        theme_text = _format_list(_describe_themes(themes))
        prompt_parts.append(f"Theme: {theme_text}.")
    if instruments:
        prompt_parts.extend(_build_instrument_constraints(instruments))

    prompt_parts.extend(
        [
            f"Tempo {tempo} BPM.",
            f"{complexity} complexity.",
            f"Energy level {energy}.",
        ]
    )

    if custom_prompt.strip():
        prompt_parts.append(custom_prompt.strip())

    prompt_parts.extend(
        [
            "Memorable melody.",
            "Creative sketch.",
            "Suitable for inspiring songwriters.",
        ]
    )

    return " ".join(prompt_parts)


def generate_music(
    model: Any,
    processor: Any,
    prompt: str,
    output_path: Path,
    progress_callback=None,
    duration_seconds: int = TARGET_SECONDS,
) -> dict:
    """Generate a 30-second WAV file using an already-loaded model."""
    import numpy as np
    import soundfile as sf
    import torch

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    device = next(model.parameters()).device
    max_new_tokens = max(1, int(duration_seconds)) * TOKENS_PER_SECOND

    logger.info("Generation started: %s", prompt)
    total_start = time.perf_counter()

    token_start = time.perf_counter()
    if progress_callback:
        progress_callback("Encoding prompt", 10)
    inputs = processor(text=[prompt], padding=True, return_tensors="pt")
    inputs = {name: value.to(device) for name, value in inputs.items()}
    logger.info("Prompt tokenized in %.2f seconds", time.perf_counter() - token_start)

    with torch.inference_mode():
        generation_start = time.perf_counter()
        if progress_callback:
            progress_callback("Starting generation", 20)
            progress_callback("Generating music", 20)
        audio_values = model.generate(
            **inputs,
            do_sample=True,
            top_k=250,
            temperature=1.0,
            guidance_scale=3.0,
            max_new_tokens=max_new_tokens,
        )
        inference_seconds = time.perf_counter() - generation_start
        if progress_callback:
            progress_callback("Saving audio", 85)
        logger.info("Inference time: %.2f seconds", inference_seconds)

    render_start = time.perf_counter()
    if progress_callback:
        progress_callback("Saving audio", 85)
    audio = audio_values[0].detach().cpu().float().numpy()

    # MusicGen returns channel-first audio. soundfile expects samples-first audio.
    if audio.ndim == 2:
        audio = np.transpose(audio)

    audio = np.clip(audio, -1.0, 1.0)
    logger.info("Audio rendered in %.2f seconds", time.perf_counter() - render_start)

    wav_start = time.perf_counter()
    if progress_callback:
        progress_callback("Saving audio", 90)
    sf.write(output_path, audio, SAMPLE_RATE, format="WAV")
    wav_seconds = time.perf_counter() - wav_start
    logger.info("WAV saved: %s in %.2f seconds", output_path, wav_seconds)

    total_seconds = time.perf_counter() - total_start
    logger.info("Generation completed in %.2f seconds", total_seconds)
    return {
        "output_path": output_path,
        "inference_seconds": inference_seconds,
        "wav_export_seconds": wav_seconds,
        "total_seconds": total_seconds,
    }
