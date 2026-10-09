from __future__ import annotations

from .local_dictionary import lookup_local_word


def _parse_translation(payload: object) -> str:
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        return ""

    parts = []
    for part in payload[0]:
        if isinstance(part, list) and part and isinstance(part[0], str):
            parts.append(part[0])
    return "".join(parts).strip()


def get_vietnamese_meaning(word: str) -> str:
    entry = lookup_local_word(word)
    return entry.get("vietnamese", "") if entry else ""
