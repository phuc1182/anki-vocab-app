from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from .validator import OFFLINE_DICTIONARY_PATH


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(
        f"file:{path.as_posix()}?mode=ro",
        uri=True,
    )


def _format_meaning(definition: str, pos: str | None, sub_pos: str | None, example: str | None) -> str:
    label = "/".join(part.strip() for part in (pos, sub_pos) if part and part.strip())
    prefix = f"[{label}] " if label else ""
    result = f"{prefix}{definition.strip()}"
    if example and example.strip():
        result += f"\nExample: {example.strip()}"
    return result


def _normalise_ipa(value: str) -> str:
    ipa = value.strip()
    if len(ipa) >= 2 and ipa.startswith("/") and ipa.endswith("/"):
        return ipa[1:-1].strip()
    return ipa


@lru_cache(maxsize=2048)
def lookup_offline_word(word: str) -> dict[str, str] | None:
    if not OFFLINE_DICTIONARY_PATH.is_file():
        return None

    normalized = word.strip().casefold()
    if not normalized:
        return None

    try:
        conn = _connect(OFFLINE_DICTIONARY_PATH)
        try:
            rows = conn.execute(
                """
                SELECT d.definition, d.pos, d.sub_pos, wd.example
                FROM words AS w
                JOIN word_definitions AS wd ON wd.word_id = w.id
                JOIN definitions AS d ON d.id = wd.definition_id
                WHERE w.word = ? COLLATE NOCASE
                ORDER BY wd.id
                """,
                (normalized,),
            ).fetchall()
            pronunciations = conn.execute(
                """
                SELECT p.ipa, p.region
                FROM words AS w
                JOIN pronunciations AS p ON p.word_id = w.id
                WHERE w.word = ? COLLATE NOCASE
                ORDER BY
                    CASE lower(COALESCE(p.region, ''))
                        WHEN 'name' THEN 0
                        WHEN 'us' THEN 1
                        WHEN 'næ' THEN 1
                        WHEN 'uk' THEN 2
                        WHEN 'br' THEN 3
                        ELSE 4
                    END,
                    p.id
                """,
                (normalized,),
            ).fetchall()
        finally:
            conn.close()
    except (OSError, sqlite3.Error) as exc:
        raise RuntimeError(
            f"Không thể đọc từ điển offline: {OFFLINE_DICTIONARY_PATH}"
        ) from exc

    if not rows:
        return None

    meanings: list[str] = []
    examples: list[str] = []
    for definition, pos, sub_pos, example in rows:
        if not definition or not definition.strip():
            continue
        meanings.append(_format_meaning(definition, pos, sub_pos, example))
        if example and example.strip():
            examples.append(example.strip())

    if not meanings:
        return None

    ipa = next(
        (_normalise_ipa(str(ipa)) for ipa, _region in pronunciations if ipa and _normalise_ipa(str(ipa))),
        "",
    )
    sentence = next(
        (example for example in examples if word.casefold() in example.casefold()),
        examples[0] if examples else "",
    )
    vietnamese = "; ".join(
        dict.fromkeys(str(definition).strip() for definition, _pos, _sub_pos, _example in rows if definition)
    )
    return {
        "meaning": "\n\n".join(meanings),
        "pronounce": ipa,
        "sentence": sentence,
        "vietnamese": vietnamese,
    }


def clear_offline_dictionary_cache() -> None:
    lookup_offline_word.cache_clear()
