from __future__ import annotations


VIETNAMESE_OVERRIDES = {
	"ampersand": "Dấu and",
	"run": "chạy",
	"walk": "đi bộ",
	"blueprint": "bản thiết kế",
}


def get_vietnamese_meaning(word: str, english_meaning: str) -> str:
	word_lower = word.lower().strip()

	if word_lower in VIETNAMESE_OVERRIDES:
		return VIETNAMESE_OVERRIDES[word_lower]

	if english_meaning:
		return f"Nghĩa tiếng Việt: {word}"

	return f"Cần dịch: {word}"
