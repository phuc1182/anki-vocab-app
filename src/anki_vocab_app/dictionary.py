from __future__ import annotations

from typing import Dict

from .local_dictionary import lookup_local_word


def is_placeholder_sentence(sentence: str, word: str) -> bool:
    cleaned = sentence.strip()
    return cleaned.casefold() == f"I learned the word {word} today.".casefold()


def fetch_dictionary_data(word: str) -> Dict[str, str]:
    entry = lookup_local_word(word)
    if entry is None:
        raise LookupError(
            f"Không tìm thấy '{word}' trong các nguồn từ điển offline. "
            "Bạn có thể thêm dữ liệu vào %LOCALAPPDATA%\\AnkiVocabApp\\dictionary.json "
            "hoặc cài một file MDX/TAB tại thư mục dữ liệu ứng dụng."
        )
    required = ("sentence", "vietnamese")
    missing = [field for field in required if not entry.get(field)]
    if missing:
        raise ValueError(f"Dữ liệu local của '{word}' thiếu: {', '.join(missing)}")
    return {"word": word, **entry}
