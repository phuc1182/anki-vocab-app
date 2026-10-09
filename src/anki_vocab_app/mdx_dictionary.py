from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path


def _plain_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _sentence(text: str, word: str) -> str:
    candidates = re.split(r"(?<=[.!?])\s+", text)
    for candidate in candidates:
        if len(candidate) >= 20 and re.search(rf"\b{re.escape(word)}\b", candidate, re.I):
            return candidate
    return f"The word {word} is used in this dictionary entry."


def _pronounce(text: str) -> str:
    match = re.search(r"/([^/]{2,40})/", text)
    return match.group(1).strip() if match else ""


def _query(source: str, word: str) -> str:
    try:
        from mdict_utils.reader import query
    except ImportError as exc:
        raise RuntimeError(
            "Để dùng từ điển MDX, hãy cài dependency 'mdict-utils'."
        ) from exc
    try:
        result = query(source, word)
    except (OSError, ValueError, RuntimeError) as exc:
        raise RuntimeError(f"Không thể đọc từ điển MDX: {source}") from exc
    return result if isinstance(result, str) else ""


@lru_cache(maxsize=512)
def lookup_mdx(path: str, word: str) -> dict[str, str] | None:
    raw = _query(path, word)
    if not raw:
        return None
    text = _plain_text(raw)
    if not text:
        return None
    return {
        "meaning": text,
        "pronounce": _pronounce(raw),
        "sentence": _sentence(text, word),
    }


def clear_mdx_cache() -> None:
    lookup_mdx.cache_clear()
