from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


VIETNAMESE_OVERRIDES = {
    "ampersand": "Dấu and",
    "run": "chạy",
    "walk": "đi bộ",
    "blueprint": "bản thiết kế",
}


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = "AnkiVocabApp/0.1"
    return session


_SESSION = _build_session()


def get_vietnamese_meaning(word: str) -> str:
    word_lower = word.lower().strip()

    if word_lower in VIETNAMESE_OVERRIDES:
        return VIETNAMESE_OVERRIDES[word_lower]

    if not word_lower:
        return ""

    try:
        response = _SESSION.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "en",
                "tl": "vi",
                "dt": "t",
                "q": word,
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        translated = "".join(
            part[0]
            for part in payload[0]
            if isinstance(part, list) and part and part[0]
        ).strip()
        if translated:
            return translated
    except Exception:
        pass

    return word_lower
