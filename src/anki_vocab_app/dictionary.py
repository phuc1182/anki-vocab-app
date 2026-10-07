from __future__ import annotations

import html
import re
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


def _google_example(word: str) -> str:
	query = f'"{word}" "example sentence"'
	try:
		response = requests.get(
			"https://www.google.com/search",
			params={"q": query, "num": 8, "hl": "en"},
			headers={"User-Agent": "Mozilla/5.0"},
			timeout=12,
		)
		response.raise_for_status()
		matches = re.findall(
			r'<div[^>]+class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>',
			response.text,
			flags=re.DOTALL,
		)
		for raw_match in matches:
			candidate = html.unescape(re.sub(r"<[^>]+>", " ", raw_match))
			candidate = re.sub(r"\s+", " ", candidate).strip(" -")
			if (
				len(candidate) >= 20
				and re.search(rf"\b{re.escape(word)}\b", candidate, re.IGNORECASE)
				and not re.search(r"people also ask|translation|sign in", candidate, re.IGNORECASE)
			):
				return candidate
	except Exception:
		pass
	return ""


def _tatoeba_example(word: str) -> str:
	try:
		response = requests.get(
			"https://tatoeba.org/en/api_v0/search",
			params={
				"from": "eng",
				"query": word,
				"orphans": "no",
				"unapproved": "no",
				"limit": 20,
			},
			timeout=12,
		)
		response.raise_for_status()
		for result in response.json().get("results", []):
			candidate = re.sub(r"\s+", " ", result.get("text", "")).strip()
			if (
				len(candidate) >= 12
				and re.search(rf"\b{re.escape(word)}\b", candidate, re.IGNORECASE)
				and candidate.endswith((".", "!", "?"))
			):
				return candidate
	except Exception:
		pass
	return ""


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
					phonetics = [phonetic for phonetic in item.get("phonetics", []) if phonetic.get("text")]
					with_audio = [phonetic for phonetic in phonetics if phonetic.get("audio")]
					chosen = (with_audio or phonetics)
					if chosen:
						data["pronounce"] = chosen[0]["text"].strip().strip("/")
				if not data["pronounce"]:
					data["pronounce"] = item.get("phonetic", "").strip().strip("/")

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
		data["sentence"] = _google_example(word)

	if not data["sentence"]:
		data["sentence"] = _tatoeba_example(word)

	if not data["sentence"]:
		data["sentence"] = f"I learned the word {word} today."

	return data
