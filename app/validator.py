from __future__ import annotations

import html
import re
import sys
from hashlib import sha1
from pathlib import Path
from datetime import datetime


if getattr(sys, "frozen", False):
	BASE_DIR = Path(sys.executable).resolve().parent
else:
	BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
CACHE_DIR = BASE_DIR / "cache"
CACHE_DB = CACHE_DIR / "vocab_cache.sqlite"
INPUT_FILE = INPUT_DIR / "words.csv"
OUTPUT_APKG = OUTPUT_DIR / "VocabularyAuto.apkg"


def ensure_directories() -> None:
	for directory in [INPUT_DIR, OUTPUT_DIR, AUDIO_DIR, CACHE_DIR]:
		directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(text: str) -> str:
	text = text.lower().strip()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	text = re.sub(r"_+", "_", text).strip("_")
	return text[:80] or "word"


def make_cloze_sentence(sentence: str, word: str) -> str:
	pattern = re.compile(re.escape(word), re.IGNORECASE)
	result = pattern.sub("____", sentence, count=1)
	if result == sentence:
		return f"____ means {word}."
	return result


def safe_text(value: str | None) -> str:
	if not value:
		return ""
	return html.escape(value.strip())


def validate_nonempty_file(file_path: Path, label: str) -> None:
	if not file_path.exists():
		raise FileNotFoundError(f"Missing {label}: {file_path}")
	if file_path.stat().st_size == 0:
		raise ValueError(f"Empty {label}: {file_path}")


def build_unique_apkg_path(words: list[str]) -> Path:
	joined = "|".join(word.strip().lower() for word in words if word.strip())
	digest = sha1(joined.encode("utf-8")).hexdigest()[:8]
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	day_stamp = datetime.now().strftime("%Y%m%d")
	return OUTPUT_DIR / f"Vocabulary_{day_stamp}_Action_{timestamp}_{digest}.apkg"
