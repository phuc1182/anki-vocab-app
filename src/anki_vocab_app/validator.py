from __future__ import annotations

import html
import os
import re
from hashlib import sha1
from pathlib import Path
from datetime import datetime


if os.name == "nt":
	DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:
	DATA_ROOT = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
BASE_DIR = DATA_ROOT / "AnkiVocabApp"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "Anki Vocab App"
MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
CACHE_DIR = BASE_DIR / "cache"
CACHE_DB = CACHE_DIR / "vocab_cache.sqlite"
DICTIONARY_PATH = BASE_DIR / "dictionary.mdx"
DICTIONARY_TAB_PATH = BASE_DIR / "dictionary.tab"
DICTIONARY_INDEX_DB = CACHE_DIR / "dictionary_index.sqlite"
OFFLINE_DICTIONARY_PATH = Path(__file__).resolve().parent / "data" / "dictionary_en_vi.db"
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
	pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
	result, count = pattern.subn("____", sentence, count=1)
	if count == 0:
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


def words_digest(words: list[str]) -> str:
	joined = "|".join(word.strip().lower() for word in words if word.strip())
	return sha1(joined.encode("utf-8")).hexdigest()[:8]


def build_unique_apkg_path(words: list[str], when: datetime | None = None) -> Path:
	created_at = when or datetime.now()
	digest = words_digest(words)
	timestamp = created_at.strftime("%Y%m%d_%H%M%S")
	day_stamp = created_at.strftime("%Y%m%d")
	return OUTPUT_DIR / f"Vocabulary_{day_stamp}_Action_{timestamp}_{digest}.apkg"
