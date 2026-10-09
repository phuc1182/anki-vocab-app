from __future__ import annotations

import json
import os
from itertools import islice
from pathlib import Path
from typing import Any

from .local_dictionary import USER_DICTIONARY_PATH
from .validator import DICTIONARY_PATH, DICTIONARY_TAB_PATH, OFFLINE_DICTIONARY_PATH


def _file_info(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "format": path.suffix.lower().lstrip(".") or "unknown",
        "size_bytes": stat.st_size,
        "modified_at": stat.st_mtime,
    }


def _json_analysis(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON dictionary root must be an object")
    entries = []
    fields: set[str] = set()
    for word, value in islice(payload.items(), 3):
        if isinstance(value, dict):
            fields.update(str(key) for key in value)
            entries.append({"word": str(word), "fields": sorted(value)})
        else:
            entries.append({"word": str(word), "fields": []})
    return {
        **_file_info(path),
        "entry_count": len(payload),
        "fields": sorted(fields),
        "samples": entries,
    }


def _tab_analysis(path: Path) -> dict[str, Any]:
    from .tab_dictionary import ensure_tab_index, inspect_tab_index

    ensure_tab_index(path)
    return {**_file_info(path), **inspect_tab_index(path)}


def _mdx_analysis(path: Path) -> dict[str, Any]:
    try:
        from mdict_utils.base.readmdict import MDX
        from mdict_utils.reader import meta
    except ImportError as exc:
        raise RuntimeError("mdict-utils is required to analyze MDX files") from exc

    dictionary = MDX(str(path), "")
    samples = []
    for key, value in islice(dictionary.items(), 3):
        word = key.decode("utf-8", errors="replace") if isinstance(key, bytes) else str(key)
        raw = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
        samples.append({"word": word, "content_length": len(raw)})
    metadata = meta(str(path))
    return {
        **_file_info(path),
        "entry_count": len(dictionary),
        "fields": ["html_entry"],
        "metadata": {str(key): str(value) for key, value in metadata.items()},
        "samples": samples,
    }


def _sqlite_analysis(path: Path) -> dict[str, Any]:
    import sqlite3

    conn = sqlite3.connect(path)
    try:
        tables = [
            name
            for (name,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        ]
        entry_count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        samples = [
            {"word": word, "fields": ["ipa", "pos", "definition", "example"]}
            for (word,) in conn.execute("SELECT word FROM words ORDER BY word LIMIT 3")
        ]
    finally:
        conn.close()
    return {
        **_file_info(path),
        "entry_count": entry_count,
        "fields": ["ipa", "pos", "definition", "example"],
        "tables": tables,
        "samples": samples,
    }


def inspect_installed_dictionary() -> dict[str, Any]:
    candidates = (
        (OFFLINE_DICTIONARY_PATH, _sqlite_analysis),
        (DICTIONARY_PATH, _mdx_analysis),
        (DICTIONARY_TAB_PATH, _tab_analysis),
        (USER_DICTIONARY_PATH, _json_analysis),
    )
    for path, analyzer in candidates:
        if path.is_file():
            report = analyzer(path)
            report["active"] = True
            return report
    return {
        "active": False,
        "format": "none",
        "entry_count": 0,
        "fields": [],
        "samples": [],
        "paths_checked": [str(path) for path, _ in candidates],
    }


def format_dictionary_report(report: dict[str, Any]) -> str:
    if not report.get("active"):
        checked = "\n".join(f"- {path}" for path in report["paths_checked"])
        return f"No installed dictionary found. Paths checked:\n{checked}"

    lines = [
        f"Format: {report['format'].upper()}",
        f"Path: {report['path']}",
        f"Size: {report['size_bytes']:,} bytes",
        f"Entries: {report['entry_count']:,}",
        f"Fields: {', '.join(report['fields']) or 'not detected'}",
    ]
    metadata = report.get("metadata", {})
    if metadata:
        lines.append("Metadata:")
        lines.extend(f"  {key}: {value}" for key, value in sorted(metadata.items()))
    samples = report.get("samples", [])
    if samples:
        lines.append("Samples:")
        lines.extend(f"  {sample['word']}" for sample in samples)
    return os.linesep.join(lines)
