from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Iterable, List

import genanki


MODEL_ID = 1784529038
DECK_ID = 1784529037
DECK_NAME = "Anki Vocab App"


def nested_deck_name(parent_name: str, when: datetime, digest: str) -> str:
	label = when.strftime("%Y-%m-%d %H:%M:%S")
	suffix = f"{label} {digest}".strip()
	return f"{parent_name}::{suffix}"


def deck_id_for(name: str) -> int:
	value = int(sha1(f"anki-vocab-app:{name}".encode("utf-8")).hexdigest()[:8], 16)
	deck_id = 1_000_000_000 + (value % 1_000_000_000)
	if deck_id == MODEL_ID:
		return deck_id + 1
	return deck_id


@dataclass
class GeneratedWord:
	word: str
	safe_name: str
	pronounce: str
	sentence: str
	sentence_cloze: str
	vietnamese: str
	word_audio: Path
	sentence_audio: Path
	image_file: Path


def build_model() -> genanki.Model:
	return genanki.Model(
		MODEL_ID,
		"Auto Vocabulary Template Model",
		fields=[
			{"name": "words"},
			{"name": "sentenses"},
			{"name": "images"},
			{"name": "pronounce"},
			{"name": "vietnamese"},
			{"name": "sound"},
			{"name": "sentence_sound"},
		],
		templates=[
			{
				"name": "Card 1",
				"qfmt": """
					<div class="cardHead">
					  <div class="word">{{words}}</div>
					  <div class="pronounce">/ {{pronounce}} /</div>
					</div>
					<div class="cardBody">
						<div class="image">{{images}}</div>
					</div>
					<div style="display:none" >{{sound}} </div>
				""",
				"afmt": """
					<div class="cardHead">
					  <div class="word">{{words}}</div>
					  <div class="pronounce">/ {{pronounce}} /</div>
					</div>
					<div class="cardBody">
						<div class="vietnamese">{{sentenses}}</div>
						<hr>
						<div class="vietnamese">{{vietnamese}}</div>
					</div>
					<div style="display:none">{{sound}} {{sentence_sound}}</div>
				""",
			},
			{
				"name": "Card 2",
				"qfmt": """
				<div class="myCard">
				<div class="cardHead">
				  <div class="hiding" id="original">{{words}}</div>
				  <div class="word hint" id="hint"></div>
				  <div class="pronounce">/ {{pronounce}} /</div>
				</div>
			</div>

			<div class="hide-android"> 
			{{type:words}}
			</div>

			<script>
			function transformString(inputString) {
			  const words = inputString.split(' ');
			  const transformedWords = words.map((word) => {
			    if (word.length < 3) {
			      return word; // Skip words with 2 or fewer characters
			    }
					const index1 = Math.floor(Math.random() * (word.length - 1));
					const index2 = Math.floor(Math.random() * (word.length - 1));
			   const firstChar = word[index1];
			   const lastChar = word[index2];
			    const middleUnderscores = '_'.repeat(word.length);

					const newString = middleUnderscores.substring(0, index1) + firstChar + middleUnderscores.substring(index1 + 1);
					const newString2 = newString.substring(0, index2) + lastChar + newString.substring(index2 + 1);
			    if (word.length > 7) {
						const index2 = Math.floor(Math.random() * (word.length - 1));
						const lastChar = word[index2];
						const newString3 = newString2.substring(0, index2) + lastChar + newString2.substring(index2 + 1);
						return newString3;
					}
			    return newString2;
			  });
			  return transformedWords.join(' ');
			}


			function updateHint() {
			  const word = document.querySelector("#original").textContent;
			  document.querySelector("#hint").textContent =
				  transformString(word);
			}



			updateHint();

			</script>
				""",
				"afmt": """
				<div class="myCard">
				  <div class="cardHead">
					<div class="word">{{words}}</div>
					<div class="pronounce">/ {{pronounce}} /</div>
				  </div>
				  <div class="cardBody">
					 <div class="image">{{images}}</div>
					 <div class="vietnamese">{{sentenses}}</div>
					 <hr>
					 <div class="vietnamese">{{vietnamese}}</div>
				</div>
				</div>
				<div class="hiding">{{sound}} {{sentence_sound}}</div>
				<div class="hide-android"> 
					{{type:words}}
				</div>
				""",
			},
		],
		css="""
			* {
			  box-sizing: border-box;
			}
			.card {
			  text-align: center;
				background: rgb(245,245,245); 
				background: linear-gradient(90deg, rgba(245,245,245,1) 0%, rgba(230,230,230,1) 100%);
			  word-wrap: break-word;
			  width: 97vw;
			  height: 92vh;
			  display: flex;
			  justify-content: center;
			  font-family: sans-serif;
				margin-top : 20px;
				padding: 20px;
			}

			.cardHead {
				padding: 5px 20px;
				background: #f0f0f0;
				background: #ededed;
				border-radius:20px;
				overflow:hidden;
			  border-left: 5px solid #cccccc;
			  border-bottom: 6px solid #bbbbbb;
				width: 95vw;
			}

			.android .card .word {
			font-size: 25px;
			}

			.card .word {

				font-weight: bold;
				font-size: 40px; 
				color:#000000;

			}
			.android .cardHead .pronounce {
			font-size: 25px;
			color: #003366;
			}
			.pronounce {
			  color: #003366;
			  font-weight: bold;
			  font-family:"Voces", sans-serif;
			  font-size: 30px;
			  margin-top: 8px;
			}

			.cardBody {
			  padding: 4%;
			}
			.image {
				height: 200px;
				max-height: 100%;	
			}
			img {
				max-height: 100%;	
			}
			.vietnamese {
			  font-size: 25px;
			  font-weight: 600;
			  text-align: center;
			  word-wrap: inherit;
			  color: #005555;
			}

			.android .vietnamese {
			font-size: 20px;
			}
			.hint {
				font-weight: bold;
				font-size: 40px; 
				letter-spacing: 3px; 
			}
			/* NightMode */
			.card .nightMode {
			  background-color: #444;
			}
			.nightMode .myCard {
			  border-color: #666;
			}
			.nightMode .cardHead {
			  background-color: #666; 
			}

			.nightMode .word {
			  color: #eee;
			}

			.nightMode .pronounce {
			  color: #ddd;
			}

			.nightMode .vietnamese {
			  color: #ccc;
			}

			.hiding {
		display:none;}

			#typeans:focus {
				outline-width: 0;
			}


			#typeans {
			 font-family: 'Noto Mono' !important;
			 font-weight: 400 !important;
			 font-size: 35px !important;
			 margin-top: 10px; 
			 text-align: center;
			 border-radius: 50px;
			 padding: 1px 20px;
			}


			.android .hide-android {
			  display: none;
			}
			.android input {display: none;

			}
			code#typeans {
			 display: inline-block;
			 padding: 5px 0px; /* input { padding: 1px 0px; } */
			 border-radius: 100px;
			}

			
		""",
	)


def build_apkg(entries: Iterable[GeneratedWord], output_path: Path, deck_name: str | None = None) -> Path:
	model = build_model()
	resolved_name = deck_name or DECK_NAME
	deck = genanki.Deck(deck_id_for(resolved_name), resolved_name)
	media_files: List[str] = []

	for entry in entries:
		note = genanki.Note(
			model=model,
			fields=[
				entry.word,
					entry.sentence,
					"",
				entry.pronounce,
				entry.vietnamese,
				_sound_reference(entry.word_audio),
				_sound_reference(entry.sentence_audio),
			],
			tags=["auto", "toeic_auto"],
			guid=genanki.guid_for(entry.word, resolved_name),
		)

		deck.add_note(note)
		media_files.extend(
			str(path)
			for path in [entry.word_audio, entry.sentence_audio]
			if path.exists() and path.stat().st_size > 0
		)

	package = genanki.Package(deck)
	package.media_files = list(dict.fromkeys(media_files))
	package.write_to_file(str(output_path))
	return output_path


def _sound_reference(audio_path: Path) -> str:
	if not audio_path.exists() or audio_path.stat().st_size == 0:
		return ""
	return f"[sound:{audio_path.name}]"
