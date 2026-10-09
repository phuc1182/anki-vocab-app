from __future__ import annotations

import asyncio
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List

from .anki_builder import DECK_NAME, GeneratedWord, build_apkg, nested_deck_name
from .audio import create_audio
from .dictionary import fetch_dictionary_data, is_placeholder_sentence
from .translator import get_vietnamese_meaning
from .validator import (
    AUDIO_DIR,
    CACHE_DB,
    CACHE_DIR,
    build_unique_apkg_path,
    ensure_directories,
    words_digest,
    make_cloze_sentence,
    safe_text,
    sanitize_filename,
    validate_nonempty_file,
)


VOICE_EN = "en-US-JennyNeural"
MAX_PARALLEL_WORDS = 4

_CACHE_LOCK = threading.Lock()
_cache_ready = False


def _connect_cache() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _cache_to_generated(row: dict) -> GeneratedWord:
    return GeneratedWord(
        word=row["word"],
        safe_name=row["safe_name"],
        pronounce=row["pronounce"],
        sentence=row["sentence"],
        sentence_cloze=row["sentence_cloze"],
        vietnamese=row["vietnamese"],
        word_audio=Path(row["word_audio"]),
        sentence_audio=Path(row["sentence_audio"]),
        image_file=Path(row["image_file"] or ""),
    )


def _audio_files_ready(*paths: Path) -> bool:
    return all(path.exists() and path.stat().st_size > 0 for path in paths)


def _translation_needs_refresh(word: str, vietnamese: str) -> bool:
    translated = vietnamese.strip()
    return not translated or translated.casefold() == word.strip().casefold()


def _require_vietnamese_translation(word: str, translated: str) -> str:
    cleaned = translated.strip()
    if _translation_needs_refresh(word, cleaned):
        raise RuntimeError(
            f"Could not translate '{word}' to Vietnamese. "
            "Check the internet connection and try again."
        )
    return cleaned


def init_cache() -> None:
    global _cache_ready
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with _CACHE_LOCK:
        if _cache_ready:
            return
        conn = _connect_cache()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vocab_cache (
                    word TEXT PRIMARY KEY,
                    safe_name TEXT,
                    pronounce TEXT,
                    sentence TEXT,
                    sentence_cloze TEXT,
                    vietnamese TEXT,
                    word_audio TEXT,
                    sentence_audio TEXT,
                    image_file TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deck_registry (
                    deck_name TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        _cache_ready = True


def _register_deck_name(deck_name: str) -> bool:
    init_cache()
    with _CACHE_LOCK:
        conn = _connect_cache()
        try:
            existing = conn.execute(
                "SELECT 1 FROM deck_registry WHERE deck_name = ?",
                (deck_name,),
            ).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO deck_registry (deck_name, created_at) VALUES (?, ?)",
                (deck_name, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
            return True
        finally:
            conn.close()


def resolve_deck_name(parent_name: str, when: datetime, digest: str) -> str:
    cleaned_name = " ".join(parent_name.split()).strip(" :")
    if not cleaned_name:
        cleaned_name = DECK_NAME
    if _register_deck_name(cleaned_name):
        return cleaned_name
    return nested_deck_name(cleaned_name, when, digest)


def get_cached_word(word: str):
    init_cache()
    with _CACHE_LOCK:
        conn = _connect_cache()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM vocab_cache WHERE word = ?",
                (word.lower().strip(),),
            ).fetchone()
        finally:
            conn.close()
    return dict(row) if row else None


def save_cached_word(entry: GeneratedWord) -> None:
    init_cache()
    now = datetime.now().isoformat(timespec="seconds")
    with _CACHE_LOCK:
        conn = _connect_cache()
        try:
            conn.execute(
                """
                INSERT INTO vocab_cache (
                    word, safe_name, pronounce, sentence, sentence_cloze,
                    vietnamese, word_audio, sentence_audio, image_file,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET
                    safe_name=excluded.safe_name,
                    pronounce=excluded.pronounce,
                    sentence=excluded.sentence,
                    sentence_cloze=excluded.sentence_cloze,
                    vietnamese=excluded.vietnamese,
                    word_audio=excluded.word_audio,
                    sentence_audio=excluded.sentence_audio,
                    image_file=excluded.image_file,
                    updated_at=excluded.updated_at
                """,
                (
                    entry.word.lower().strip(),
                    entry.safe_name,
                    entry.pronounce,
                    entry.sentence,
                    entry.sentence_cloze,
                    entry.vietnamese,
                    str(entry.word_audio),
                    str(entry.sentence_audio),
                    str(entry.image_file),
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def generate_word_entry(word: str, log: Callable[[str], None] | None = None, regenerate: bool = False) -> GeneratedWord:
    ensure_directories()
    init_cache()

    word = word.strip()
    safe_name = sanitize_filename(word)
    word_audio = AUDIO_DIR / f"{safe_name}_word.mp3"
    sentence_audio = AUDIO_DIR / f"{safe_name}_sentence.mp3"
    image_file = Path()

    if not regenerate:
        cached = get_cached_word(word)
        if cached:
            cached_entry = _cache_to_generated(cached)
            audio_ok = _audio_files_ready(cached_entry.word_audio, cached_entry.sentence_audio)
            if audio_ok and not is_placeholder_sentence(cached_entry.sentence, word):
                if log:
                    log(f"[CACHE] {word}")
                return cached_entry
            if is_placeholder_sentence(cached_entry.sentence, word):
                sentence_audio.unlink(missing_ok=True)

    if log:
        log(f"[NEW] {word}")

    async def _build() -> tuple[dict, str]:
        dictionary_data = fetch_dictionary_data(word)
        vietnamese = get_vietnamese_meaning(word)
        vietnamese = _require_vietnamese_translation(word, vietnamese)
        # Lookup is complete before any network-backed audio work starts.
        audio_tasks = [
            create_audio(word, word_audio, VOICE_EN),
            create_audio(dictionary_data["sentence"], sentence_audio, VOICE_EN),
        ]
        audio_labels = ("word audio", "sentence audio")
        audio_results = await asyncio.gather(*audio_tasks, return_exceptions=True)
        for label, result in zip(audio_labels, audio_results):
            if isinstance(result, Exception):
                if log:
                    log(f"[WARNING] {word}: không tạo được {label}; bộ thẻ sẽ không có audio này.")
        return dictionary_data, vietnamese

    dictionary_data, vietnamese = asyncio.run(_build())
    pronounce = dictionary_data["pronounce"]
    sentence = dictionary_data["sentence"]
    sentence_cloze = make_cloze_sentence(sentence, word)

    for path, label in [(word_audio, "word audio"), (sentence_audio, "sentence audio")]:
        if path.exists():
            validate_nonempty_file(path, label)

    entry = GeneratedWord(
        word=word,
        safe_name=safe_name,
        pronounce=safe_text(pronounce),
        sentence=safe_text(sentence),
        sentence_cloze=safe_text(sentence_cloze),
        vietnamese=safe_text(vietnamese),
        word_audio=word_audio,
        sentence_audio=sentence_audio,
        image_file=image_file,
    )
    save_cached_word(entry)
    return entry


def generate_deck(
    words: Iterable[str],
    log: Callable[[str], None] | None = None,
    output_path: Path | None = None,
    deck_name: str = DECK_NAME,
):
    word_list: List[str] = []
    seen: set[str] = set()
    for word in words:
        cleaned = word.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            word_list.append(cleaned)
            seen.add(key)

    if not word_list:
        raise ValueError("No words provided.")

    ensure_directories()
    init_cache()

    def _one(item: str) -> GeneratedWord:
        try:
            return generate_word_entry(item, log=log)
        except Exception as exc:
            raise RuntimeError(f"Failed on '{item}': {exc}") from exc

    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_WORDS, len(word_list))) as executor:
        entries = list(executor.map(_one, word_list))

    created_at = datetime.now()
    if output_path is None:
        output_path = build_unique_apkg_path(word_list, when=created_at)

    resolved_deck_name = resolve_deck_name(deck_name, created_at, words_digest(word_list))
    if log:
        log(f"[DECK] {resolved_deck_name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_apkg(entries, output_path, deck_name=resolved_deck_name)
    validate_nonempty_file(output_path, "APKG file")
    return output_path, entries


def split_words(text: str) -> List[str]:
    lines = []
    for raw_line in text.replace(",", "\n").splitlines():
        word = raw_line.strip()
        if word and not word.startswith("#"):
            lines.append(word)

    if lines and lines[0].casefold() in {"word", "words", "vocabulary", "vocab"}:
        lines = lines[1:]
    return lines
