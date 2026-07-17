from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List

from .anki_builder import GeneratedWord, build_apkg
from .audio import create_audio
from .dictionary import fetch_dictionary_data
from .image import create_word_card_image
from .translator import get_vietnamese_meaning
from .validator import (
    AUDIO_DIR,
    CACHE_DB,
    CACHE_DIR,
    IMAGE_DIR,
    OUTPUT_DIR,
    build_unique_apkg_path,
    ensure_directories,
    make_cloze_sentence,
    safe_text,
    sanitize_filename,
    validate_nonempty_file,
)


VOICE_EN = "en-US-JennyNeural"
VOICE_VI = "vi-VN-HoaiMyNeural"


def _cache_to_generated(row: dict) -> GeneratedWord:
    return GeneratedWord(
        word=row["word"],
        safe_name=row["safe_name"],
        meaning=row["meaning"],
        pronounce=row["pronounce"],
        sentence=row["sentence"],
        sentence_cloze=row["sentence_cloze"],
        vietnamese=row["vietnamese"],
        word_audio=Path(row["word_audio"]),
        sentence_audio=Path(row["sentence_audio"]),
        meaning_audio=Path(row["meaning_audio"]),
        image_file=Path(row["image_file"]),
    )


def init_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocab_cache (
            word TEXT PRIMARY KEY,
            safe_name TEXT,
            meaning TEXT,
            pronounce TEXT,
            sentence TEXT,
            sentence_cloze TEXT,
            vietnamese TEXT,
            word_audio TEXT,
            sentence_audio TEXT,
            meaning_audio TEXT,
            image_file TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_cached_word(word: str):
    conn = sqlite3.connect(CACHE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vocab_cache WHERE word = ?", (word.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_cached_word(entry: GeneratedWord) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO vocab_cache (
            word, safe_name, meaning, pronounce, sentence, sentence_cloze,
            vietnamese, word_audio, sentence_audio, meaning_audio, image_file,
            created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            COALESCE((SELECT created_at FROM vocab_cache WHERE word = ?), ?),
            ?
        )
        """,
        (
            entry.word.lower().strip(),
            entry.safe_name,
            entry.meaning,
            entry.pronounce,
            entry.sentence,
            entry.sentence_cloze,
            entry.vietnamese,
            str(entry.word_audio),
            str(entry.sentence_audio),
            str(entry.meaning_audio),
            str(entry.image_file),
            entry.word.lower().strip(),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()


def generate_word_entry(word: str, log: Callable[[str], None] | None = None, regenerate: bool = False) -> GeneratedWord:
    ensure_directories()
    init_cache()

    word = word.strip()
    safe_name = sanitize_filename(word)
    word_audio = AUDIO_DIR / f"{safe_name}_word.mp3"
    sentence_audio = AUDIO_DIR / f"{safe_name}_sentence.mp3"
    meaning_audio = AUDIO_DIR / f"{safe_name}_meaning_vi.mp3"
    image_file = IMAGE_DIR / f"{safe_name}.jpg"

    if not regenerate:
        cached = get_cached_word(word)
        if cached:
            cached_entry = _cache_to_generated(cached)
            if all(path.exists() and path.stat().st_size > 0 for path in [cached_entry.word_audio, cached_entry.sentence_audio, cached_entry.meaning_audio, cached_entry.image_file]):
                if log:
                    log(f"[CACHE] {word}")
                create_word_card_image(word, cached_entry.vietnamese, cached_entry.meaning, cached_entry.sentence, cached_entry.image_file)
                return cached_entry

    if log:
        log(f"[NEW] {word}")

    dictionary_data = fetch_dictionary_data(word)
    meaning = dictionary_data["meaning"]
    pronounce = dictionary_data["pronounce"]
    sentence = dictionary_data["sentence"]
    vietnamese = get_vietnamese_meaning(word, meaning)
    sentence_cloze = make_cloze_sentence(sentence, word)

    async def _generate() -> None:
        await create_audio(word, word_audio, VOICE_EN)
        await create_audio(sentence, sentence_audio, VOICE_EN)
        await create_audio(vietnamese, meaning_audio, VOICE_VI)

    asyncio.run(_generate())
    create_word_card_image(word, vietnamese, meaning, sentence, image_file)

    for path, label in [(word_audio, "word audio"), (sentence_audio, "sentence audio"), (meaning_audio, "meaning audio"), (image_file, "image file")]:
        validate_nonempty_file(path, label)

    entry = GeneratedWord(
        word=word,
        safe_name=safe_name,
        meaning=safe_text(meaning),
        pronounce=safe_text(pronounce),
        sentence=safe_text(sentence),
        sentence_cloze=safe_text(sentence_cloze),
        vietnamese=safe_text(vietnamese),
        word_audio=word_audio,
        sentence_audio=sentence_audio,
        meaning_audio=meaning_audio,
        image_file=image_file,
    )
    save_cached_word(entry)
    return entry


def generate_deck(words: Iterable[str], log: Callable[[str], None] | None = None, output_path: Path | None = None):
    entries: List[GeneratedWord] = []
    word_list = [word.strip() for word in words if word.strip()]
    for cleaned in word_list:
        entries.append(generate_word_entry(cleaned, log=log))

    if not entries:
        raise ValueError("No words provided.")

    if output_path is None:
        output_path = build_unique_apkg_path(word_list)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_apkg(entries, output_path)
    validate_nonempty_file(output_path, "APKG file")
    return output_path, entries


def split_words(text: str) -> List[str]:
    lines = []
    for raw_line in text.replace(",", "\n").splitlines():
        word = raw_line.strip()
        if word and not word.startswith("#"):
            lines.append(word)
    return lines