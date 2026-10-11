"""Importable, privacy-limited text processing shared by training and reproduction."""

import re
from pathlib import Path

SAFE = set((Path(__file__).parent / "safe_lexicon.txt").read_text().split())


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[a-z]{2,}", text.lower()))


def safe_text(text: str) -> str:
    return " ".join(word for word in re.findall(r"[a-z]{2,}", text.lower()) if word in SAFE)
