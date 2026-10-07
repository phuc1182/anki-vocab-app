from __future__ import annotations

import requests


VIETNAMESE_OVERRIDES = {
	"ampersand": "Dấu and",
	"run": "chạy",
	"walk": "đi bộ",
	"blueprint": "bản thiết kế",
}


def get_vietnamese_meaning(word: str) -> str:
	word_lower = word.lower().strip()

	if word_lower in VIETNAMESE_OVERRIDES:
		return VIETNAMESE_OVERRIDES[word_lower]

	if not word_lower:
		return ""

	try:
		response = requests.get(
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
