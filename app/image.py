from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageOps

from .validator import validate_nonempty_file


WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
LOREMFlickr_SOURCE = "https://loremflickr.com/1200/800/{query}"
UNSPLASH_SOURCE = "https://source.unsplash.com/featured/1200x800/?{query}"

IMAGE_QUERY_OVERRIDES = {
	"home": "house",
	"house": "house",
	"apartment": "home interior",
	"school": "school building",
	"car": "car",
	"computer": "computer",
	"phone": "smartphone",
	"book": "book",
}


def _candidate_queries(word: str, meaning: str) -> list[str]:
	queries: list[str] = []
	word_lower = word.strip().lower()
	meaning_words = [token.strip(".,;:!?()[]{}\"'") for token in meaning.lower().split()]

	if word_lower in IMAGE_QUERY_OVERRIDES:
		queries.append(IMAGE_QUERY_OVERRIDES[word_lower])

	queries.append(word.strip())

	stop_words = {
		"that",
		"this",
		"with",
		"from",
		"your",
		"have",
		"were",
		"been",
		"into",
		"over",
		"under",
		"when",
		"what",
		"where",
		"there",
		"these",
		"those",
		"their",
		"about",
		"after",
		"before",
		"because",
		"which",
	}
	for token in meaning_words:
		if len(token) >= 4 and token not in stop_words and token not in queries:
			queries.append(token)

	return queries


def _search_wikimedia_image(query: str) -> str | None:
	response = requests.get(
		WIKIMEDIA_API,
		params={
			"action": "query",
			"format": "json",
			"generator": "search",
			"gsrnamespace": 6,
			"gsrsearch": query,
			"gsrwhat": "text",
			"gsrlimit": 10,
			"prop": "imageinfo",
			"iiprop": "url|mime",
			"iiurlwidth": 1600,
		},
		timeout=15,
	)
	response.raise_for_status()
	payload = response.json()
	pages = (payload.get("query") or {}).get("pages") or {}

	for page in pages.values():
		imageinfo = page.get("imageinfo") or []
		if not imageinfo:
			continue
		info = imageinfo[0]
		url = info.get("thumburl") or info.get("url")
		mime = info.get("mime") or ""
		if url and mime.startswith("image/"):
			return url

	return None


def _download_photo(query: str) -> Image.Image | None:
	for candidate in _candidate_queries(query, query):
		try:
			image_url = _search_wikimedia_image(candidate)
			if image_url:
				image_response = requests.get(image_url, timeout=20)
				image_response.raise_for_status()
				return Image.open(BytesIO(image_response.content))
		except Exception:
			continue

	for candidate in _candidate_queries(query, query):
		try:
			fallback_url = LOREMFlickr_SOURCE.format(query=quote(candidate.strip() or "object"))
			image_response = requests.get(fallback_url, timeout=20, allow_redirects=True)
			image_response.raise_for_status()
			return Image.open(BytesIO(image_response.content))
		except Exception:
			continue

	try:
		fallback_url = UNSPLASH_SOURCE.format(query=quote(query.strip() or "object"))
		image_response = requests.get(fallback_url, timeout=20, allow_redirects=True)
		image_response.raise_for_status()
		return Image.open(BytesIO(image_response.content))
	except Exception:
		return None


def _fit_to_canvas(image: Image.Image, width: int, height: int) -> Image.Image:
	image = ImageOps.exif_transpose(image)
	image = image.convert("RGB")
	return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))


def create_word_card_image(word: str, vietnamese: str, meaning: str, sentence: str, output_path: Path) -> None:
	image = _download_photo(word)
	if image is None:
		raise RuntimeError(f"Unable to find a real image for '{word}'.")

	photo = _fit_to_canvas(image, 1200, 800)
	photo.save(output_path, "JPEG", quality=92)
	validate_nonempty_file(output_path, "image file")