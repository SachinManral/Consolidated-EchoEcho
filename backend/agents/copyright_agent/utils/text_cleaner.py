# This file is responsible for text cleanup utilities ko handle karne ke liye.
# Yahan lowercase, punctuation removal, whitespace cleanup aur tokenization manage kiya jata hai.

import re
import string


_PUNCTUATION_TABLE = str.maketrans("", "", string.punctuation)


def lowercase_text(text: str) -> str:
    return text.lower()


def remove_punctuation(text: str) -> str:
    return text.translate(_PUNCTUATION_TABLE)


def cleanup_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    cleaned = cleanup_whitespace(text)
    if not cleaned:
        return []
    return cleaned.split(" ")


def clean_text(text: str) -> str:
    return cleanup_whitespace(remove_punctuation(lowercase_text(text)))
