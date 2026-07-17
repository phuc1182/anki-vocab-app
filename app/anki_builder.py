from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import genanki


MODEL_ID = 1607392401
DECK_ID = 2059400201


@dataclass
class GeneratedWord:
	word: str
	safe_name: str
	meaning: str
	pronounce: str
	sentence: str
	sentence_cloze: str
	vietnamese: str
	word_audio: Path
	sentence_audio: Path
	meaning_audio: Path
	image_file: Path


def build_model() -> genanki.Model:
	return genanki.Model(
		MODEL_ID,
		"Auto Vocabulary Model",
		fields=[
			{"name": "word"},
			{"name": "meaning"},
			{"name": "sentence"},
			{"name": "sentence_cloze"},
			{"name": "image"},
			{"name": "pronounce"},
			{"name": "vietnamese"},
			{"name": "sound"},
			{"name": "sentence_sound"},
			{"name": "meaning_sound"},
		],
		templates=[
			{
				"name": "Card 1 - Word To Meaning",
				"qfmt": """
					<div class="card-box">
						<div class="label">What does this word mean?</div>
						<div class="word">{{word}}</div>
						<div class="pronounce">/{{pronounce}}/</div>
						<div class="audio">{{sound}}</div>
					</div>
				""",
				"afmt": """
					{{FrontSide}}
					<hr id="answer">
					<div class="vietnamese">{{vietnamese}}</div>
					<div class="meaning">{{meaning}}</div>
					<div class="sentence">{{sentence}}</div>
					<div class="audio-row">{{sentence_sound}}</div>
					<div class="audio-row">{{meaning_sound}}</div>
					<div class="image-box">{{image}}</div>
				""",
			},
			{
				"name": "Card 2 - Type The Word",
				"qfmt": """
					<div class="card-box">
						<div class="label">Type the missing word</div>
						<div class="sentence big-sentence">{{sentence_cloze}}</div>
						<div class="hint">Nghĩa: {{vietnamese}}</div>
						<div class="type-box">{{type:word}}</div>
					</div>
				""",
				"afmt": """
					{{FrontSide}}
					<hr id="answer">
					<div class="answer-title">Correct answer</div>
					<div class="word answer">{{word}}</div>
					<div class="pronounce">/{{pronounce}}/</div>
					<div class="meaning">{{meaning}}</div>
					<div class="sentence">{{sentence}}</div>
					<div class="audio-row">{{sound}}</div>
					<div class="audio-row">{{sentence_sound}}</div>
					<div class="image-box">{{image}}</div>
				""",
			},
		],
		css="""
			.card {
				font-family: Arial, sans-serif;
				font-size: 24px;
				text-align: center;
				color: #1f2937;
				background-color: #ffffff;
			}
			.card-box { padding: 22px; }
			.label { font-size: 18px; color: #64748b; margin-bottom: 16px; }
			.word { font-size: 48px; font-weight: bold; color: #2563eb; margin: 14px 0; }
			.pronounce { font-size: 24px; color: #64748b; margin-top: 8px; }
			.vietnamese { font-size: 36px; font-weight: bold; color: #16a34a; margin-top: 18px; }
			.meaning { font-size: 23px; color: #334155; margin-top: 16px; line-height: 1.45; }
			.sentence { font-size: 25px; color: #111827; margin-top: 18px; line-height: 1.45; }
			.big-sentence { font-size: 32px; font-weight: bold; margin: 24px 0; }
			.hint { font-size: 24px; color: #16a34a; margin-top: 12px; }
			.type-box { margin-top: 24px; }
			input[type=text] { font-size: 30px; padding: 12px 16px; border: 2px solid #2563eb; border-radius: 12px; text-align: center; max-width: 90%; }
			.answer-title { font-size: 18px; color: #64748b; margin-top: 16px; }
			.answer { color: #dc2626; }
			.audio { margin-top: 14px; }
			.audio-row { margin-top: 12px; }
			.image-box { margin-top: 22px; }
			.image-box img { max-width: 90%; max-height: 340px; border-radius: 18px; box-shadow: 0 4px 18px rgba(0,0,0,0.16); }
		""",
	)


def build_apkg(entries: Iterable[GeneratedWord], output_path: Path, deck_name: str = "Vocabulary::Auto") -> Path:
	model = build_model()
	deck = genanki.Deck(DECK_ID, deck_name)
	media_files: List[str] = []

	for entry in entries:
		note = genanki.Note(
			model=model,
			fields=[
				entry.word,
				entry.meaning,
				entry.sentence,
				entry.sentence_cloze,
				f'<img src="{entry.image_file.name}">',
				entry.pronounce,
				entry.vietnamese,
				f"[sound:{entry.word_audio.name}]",
				f"[sound:{entry.sentence_audio.name}]",
				f"[sound:{entry.meaning_audio.name}]",
			],
			tags=["auto", "vocabulary"],
			guid=genanki.guid_for(entry.word),
		)

		deck.add_note(note)
		media_files.extend([str(entry.word_audio), str(entry.sentence_audio), str(entry.meaning_audio), str(entry.image_file)])

	package = genanki.Package(deck)
	package.media_files = media_files
	package.write_to_file(str(output_path))
	return output_path
