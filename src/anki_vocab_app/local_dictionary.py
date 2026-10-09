from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from threading import Lock
from typing import Any

from .validator import BASE_DIR
from .validator import DICTIONARY_PATH
from .validator import DICTIONARY_TAB_PATH
from .mdx_dictionary import lookup_mdx
from .offline_dictionary import lookup_offline_word
from .tab_dictionary import lookup_tab


USER_DICTIONARY_PATH = BASE_DIR / "dictionary.json"
_LOAD_LOCK = Lock()
_ENTRIES: dict[str, dict[str, str]] | None = None


def _normalise_entry(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(value.get(key, "")).strip()
        for key in ("meaning", "pronounce", "sentence", "vietnamese")
    }


def _read_dictionary(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Không thể đọc từ điển local: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Từ điển local phải là một JSON object: {path}")
    entries: dict[str, dict[str, str]] = {}
    for word, value in payload.items():
        key = str(word).strip().casefold()
        if key:
            entries[key] = _normalise_entry(value)
    return entries


def _load_entries() -> dict[str, dict[str, str]]:
    global _ENTRIES
    with _LOAD_LOCK:
        if _ENTRIES is not None:
            return _ENTRIES

        bundled_path = Path(
            str(files("anki_vocab_app").joinpath("data").joinpath("dictionary.json"))
        )
        entries = _read_dictionary(bundled_path)
        if USER_DICTIONARY_PATH != bundled_path:
            entries.update(_read_dictionary(USER_DICTIONARY_PATH))
        _ENTRIES = entries
        return entries


def lookup_local_word(word: str) -> dict[str, str] | None:
    key = word.strip().casefold()
    entry: dict[str, str] = {}
    offline_entry = lookup_offline_word(word)
    if offline_entry:
        entry.update(offline_entry)
    bundled_entry = _load_entries().get(key, {})
    for field, value in bundled_entry.items():
        if not entry.get(field) and value:
            entry[field] = value
    if DICTIONARY_PATH.is_file():
        mdx_entry = lookup_mdx(str(DICTIONARY_PATH), word.strip())
        if mdx_entry:
            for field, value in mdx_entry.items():
                if not entry.get(field) and value:
                    entry[field] = value
    if not entry and DICTIONARY_TAB_PATH.is_file():
        entry = lookup_tab(DICTIONARY_TAB_PATH, word.strip()) or {}
    return entry or None


def reset_dictionary_cache() -> None:
    """Clear the in-memory dictionary cache for tests or an import operation."""
    global _ENTRIES
    with _LOAD_LOCK:
        _ENTRIES = None
