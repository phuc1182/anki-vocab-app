from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .validator import validate_nonempty_file


def _load_font(size: int):
	candidates = [
		"C:/Windows/Fonts/arial.ttf",
		"C:/Windows/Fonts/segoeui.ttf",
		"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
		"/System/Library/Fonts/Supplemental/Arial.ttf",
	]

	for font_path in candidates:
		try:
			return ImageFont.truetype(font_path, size)
		except Exception:
			continue

	return ImageFont.load_default()


def _make_gradient(width: int, height: int) -> Image.Image:
	base = Image.new("RGB", (width, height), color=(248, 250, 252))
	draw = ImageDraw.Draw(base)

	for y in range(height):
		ratio = y / max(height - 1, 1)
		r = int(241 - (241 - 226) * ratio)
		g = int(245 - (245 - 232) * ratio)
		b = int(249 - (249 - 240) * ratio)
		draw.line((0, y, width, y), fill=(r, g, b))

	return base


def create_word_card_image(word: str, vietnamese: str, meaning: str, sentence: str, output_path: Path) -> None:
	if output_path.exists() and output_path.stat().st_size > 0:
		return

	img = _make_gradient(1200, 800)
	draw = ImageDraw.Draw(img)

	font_title = _load_font(40)
	font_word = _load_font(92)
	font_subtitle = _load_font(30)
	font_body = _load_font(34)
	font_small = _load_font(24)

	draw.rounded_rectangle((60, 60, 1140, 740), radius=40, fill=(255, 255, 255), outline=(96, 165, 250), width=6)
	draw.rounded_rectangle((90, 95, 340, 150), radius=18, fill=(30, 64, 175))
	draw.text((118, 102), "VOCAB CARD", fill=(255, 255, 255), font=font_small)

	draw.text((100, 190), word, fill=(37, 99, 235), font=font_word)
	draw.text((104, 315), vietnamese, fill=(22, 163, 74), font=font_title)

	draw.text((104, 390), "Meaning", fill=(100, 116, 139), font=font_small)
	draw.text((104, 428), meaning, fill=(15, 23, 42), font=font_body)

	draw.text((104, 540), "Example", fill=(100, 116, 139), font=font_small)
	draw.text((104, 578), sentence, fill=(15, 23, 42), font=font_subtitle)

	draw.text((104, 675), "Auto-generated image and audio for learning", fill=(148, 163, 184), font=font_small)

	img.save(output_path, "JPEG", quality=92)
	validate_nonempty_file(output_path, "image file")
