from __future__ import annotations

import html
import re
import sqlite3
from pathlib import Path
from threading import Lock

from .validator import DICTIONARY_INDEX_DB


_INDEX_LOCK = Lock()


def _plain_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _index_is_current(source: Path) -> bool:
    if not DICTIONARY_INDEX_DB.is_file():
        return False
    conn = sqlite3.connect(DICTIONARY_INDEX_DB)
    try:
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = 'source_mtime_ns'"
        ).fetchone()
    finally:
        conn.close()
    return row is not None and row[0] == str(source.stat().st_mtime_ns)


def _build_index(source: Path) -> None:
    DICTIONARY_INDEX_DB.parent.mkdir(parents=True, exist_ok=True)
    temporary_db = DICTIONARY_INDEX_DB.with_suffix(".tmp")
    temporary_db.unlink(missing_ok=True)
    conn = sqlite3.connect(temporary_db)
    try:
        conn.execute("CREATE TABLE entries (word TEXT PRIMARY KEY, meaning TEXT)")
        with source.open("r", encoding="utf-8-sig", errors="replace") as stream:
            for line in stream:
                word, separator, meaning = line.rstrip("\r\n").partition("\t")
                word = word.strip().casefold()
                if word and separator and meaning.strip():
                    conn.execute(
                        "INSERT OR REPLACE INTO entries(word, meaning) VALUES (?, ?)",
                        (word, meaning.strip()),
                    )
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO metadata(key, value) VALUES ('source_mtime_ns', ?)",
            (str(source.stat().st_mtime_ns),),
        )
        conn.commit()
    finally:
        conn.close()
    temporary_db.replace(DICTIONARY_INDEX_DB)


def ensure_tab_index(path: Path) -> None:
    with _INDEX_LOCK:
        if not _index_is_current(path):
            _build_index(path)


def inspect_tab_index(path: Path) -> dict[str, object]:
    conn = sqlite3.connect(DICTIONARY_INDEX_DB)
    try:
        count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        samples = [
            {"word": word, "fields": ["meaning", "vietnamese"]}
            for word, in conn.execute(
                "SELECT word FROM entries ORDER BY word LIMIT 3"
            )
        ]
    finally:
        conn.close()
    return {
        "entry_count": count,
        "fields": ["word", "meaning", "vietnamese"],
        "samples": samples,
        "index_path": str(DICTIONARY_INDEX_DB),
    }


def lookup_tab(path: Path, word: str) -> dict[str, str] | None:
    ensure_tab_index(path)
    conn = sqlite3.connect(DICTIONARY_INDEX_DB)
    try:
        row = conn.execute(
            "SELECT meaning FROM entries WHERE word = ?",
            (word.strip().casefold(),),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    meaning = _plain_text(row[0])
    return {
        "meaning": meaning,
        "pronounce": "",
        "sentence": f"The word {word} is used in this dictionary entry.",
        "vietnamese": meaning,
    }
