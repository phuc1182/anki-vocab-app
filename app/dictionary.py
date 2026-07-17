from __future__ import annotations

from typing import Dict

import requests


DEFINITION_OVERRIDES = {
	"ampersand": 'A symbol (&) representing the word "and" in written language.',
}

PRONOUNCE_OVERRIDES = {
	"ampersand": "ˈæmpərˌsænd",
}

EXAMPLE_OVERRIDES = {
	"ampersand": "The ampersand is often used in company names.",
}


def fetch_dictionary_data(word: str) -> Dict[str, str]:
	word_lower = word.lower().strip()

	data = {
		"word": word,
		"meaning": "",
		"pronounce": "",
		"sentence": "",
	}

	if word_lower in DEFINITION_OVERRIDES:
		data["meaning"] = DEFINITION_OVERRIDES[word_lower]

	if word_lower in PRONOUNCE_OVERRIDES:
		data["pronounce"] = PRONOUNCE_OVERRIDES[word_lower]

	if word_lower in EXAMPLE_OVERRIDES:
		data["sentence"] = EXAMPLE_OVERRIDES[word_lower]

	try:
		response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=12)
		if response.status_code == 200:
			items = response.json()
			if isinstance(items, list) and items:
				item = items[0]

				if not data["pronounce"]:
					data["pronounce"] = item.get("phonetic", "") or ""
					if not data["pronounce"]:
						for phonetic in item.get("phonetics", []):
							if phonetic.get("text"):
								data["pronounce"] = phonetic["text"]
								break

				for meaning_item in item.get("meanings", []):
					for definition_item in meaning_item.get("definitions", []):
						if not data["meaning"] and definition_item.get("definition"):
							data["meaning"] = definition_item["definition"]
						if not data["sentence"] and definition_item.get("example"):
							data["sentence"] = definition_item["example"]
						if data["meaning"] and data["sentence"]:
							break
					if data["meaning"] and data["sentence"]:
						break
	except Exception:
		pass

	if not data["meaning"]:
		data["meaning"] = f"Definition for '{word}' was not found. Please review manually."

	if not data["sentence"]:
		data["sentence"] = f"I learned the word {word} today."

	return data
