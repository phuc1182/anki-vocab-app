import asyncio
import html
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import edge_tts
import genanki
import requests
from PIL import Image, ImageDraw, ImageFont


# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "input" / "words.txt"
OUTPUT_DIR = BASE_DIR / "data" / "output"
AUDIO_DIR = BASE_DIR / "data" / "media" / "audio"
IMAGE_DIR = BASE_DIR / "data" / "media" / "images"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

DECK_NAME = "Vocabulary::Auto"
OUTPUT_APKG = OUTPUT_DIR / "vocabulary_auto.apkg"

VOICE_EN = "en-US-JennyNeural"
VOICE_VI = "vi-VN-HoaiMyNeural"

MODEL_ID = 1607392401
DECK_ID = 2059400201


# =========================
# BASIC FALLBACK DATA
# =========================

VIETNAMESE_OVERRIDES = {
    "ampersand": "Dấu and",
    "run": "chạy",
    "walk": "đi bộ",
    "blueprint": "bản thiết kế",
}


DEFINITION_OVERRIDES = {
    "ampersand": 'A symbol (&) representing the word "and" in written language.',
}


PRONOUNCE_OVERRIDES = {
    "ampersand": "ˈæmpərˌsænd",
}


EXAMPLE_OVERRIDES = {
    "ampersand": "The ampersand is often used in company names.",
}


# =========================
# UTILITIES
# =========================

def sanitize_filename(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "word"


def read_words() -> List[str]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    words = []
    for line in INPUT_FILE.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word and not word.startswith("#"):
            words.append(word)

    if not words:
        raise ValueError("words.txt is empty.")

    return words


def validate_file_exists(file_path: Path, label: str):
    if not file_path.exists():
        raise FileNotFoundError(f"[ERROR] Missing {label}: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValueError(f"[ERROR] Empty {label}: {file_path}")

    print(f"[OK] {label}: {file_path.name}")


def make_cloze_sentence(sentence: str, word: str) -> str:
    pattern = re.compile(re.escape(word), re.IGNORECASE)
    result = pattern.sub("____", sentence, count=1)

    if result == sentence:
        return f"____ means {word}."

    return result


def safe_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return html.escape(value.strip())


# =========================
# DICTIONARY SERVICE
# =========================

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
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=12)

        if response.status_code == 200:
            items = response.json()
            if isinstance(items, list) and items:
                item = items[0]

                if not data["pronounce"]:
                    data["pronounce"] = item.get("phonetic", "") or ""

                    if not data["pronounce"]:
                        for ph in item.get("phonetics", []):
                            if ph.get("text"):
                                data["pronounce"] = ph.get("text")
                                break

                meanings = item.get("meanings", [])
                for meaning_item in meanings:
                    definitions = meaning_item.get("definitions", [])
                    for definition_item in definitions:
                        if not data["meaning"] and definition_item.get("definition"):
                            data["meaning"] = definition_item["definition"]

                        if not data["sentence"] and definition_item.get("example"):
                            data["sentence"] = definition_item["example"]

                        if data["meaning"] and data["sentence"]:
                            break

                    if data["meaning"] and data["sentence"]:
                        break

    except Exception as e:
        print(f"[WARN] Dictionary lookup failed for '{word}': {e}")

    if not data["meaning"]:
        data["meaning"] = f"Definition for '{word}' was not found. Please review manually."

    if not data["sentence"]:
        data["sentence"] = f"I learned the word {word} today."

    return data


# =========================
# VIETNAMESE TRANSLATION
# =========================

def get_vietnamese_meaning(word: str, english_meaning: str) -> str:
    word_lower = word.lower().strip()

    if word_lower in VIETNAMESE_OVERRIDES:
        return VIETNAMESE_OVERRIDES[word_lower]

    # Fallback đơn giản để không làm app lỗi.
    # Sau này ta sẽ thay bằng AI Translate hoặc Microsoft Translator API.
    return f"Cần dịch: {word}"


# =========================
# AUDIO SERVICE
# =========================

async def create_audio(text: str, output_path: Path, voice: str):
    if output_path.exists() and output_path.stat().st_size > 0:
        return

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))

    validate_file_exists(output_path, "audio file")


# =========================
# IMAGE SERVICE
# =========================

def load_font(size: int):
    candidates = [
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass

    return ImageFont.load_default()


def create_placeholder_image(word: str, vietnamese: str, output_path: Path):
    if output_path.exists() and output_path.stat().st_size > 0:
        return

    img = Image.new("RGB", (900, 560), color=(239, 246, 255))
    draw = ImageDraw.Draw(img)

    font_big = load_font(76)
    font_medium = load_font(42)
    font_small = load_font(28)

    draw.rounded_rectangle(
        (35, 35, 865, 525),
        radius=28,
        outline=(37, 99, 235),
        width=6,
        fill=(255, 255, 255),
    )

    draw.text((80, 95), "Vocabulary", fill=(100, 116, 139), font=font_small)
    draw.text((80, 190), word, fill=(37, 99, 235), font=font_big)
    draw.text((80, 320), vietnamese, fill=(22, 163, 74), font=font_medium)

    draw.text(
        (80, 455),
        "Auto-generated learning image",
        fill=(148, 163, 184),
        font=font_small,
    )

    img.save(output_path, "JPEG", quality=92)

    validate_file_exists(output_path, "image file")


# =========================
# ANKI MODEL
# =========================

def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Auto Vocabulary Model",
        fields=[
            {"name": "words"},
            {"name": "meaning"},
            {"name": "sentenses"},
            {"name": "sentence_cloze"},
            {"name": "images"},
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
                        <div class="word">{{words}}</div>
                        <div class="pronounce">/{{pronounce}}/</div>
                        <div class="audio">{{sound}}</div>
                    </div>
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id="answer">
                    <div class="vietnamese">{{vietnamese}}</div>
                    <div class="meaning">{{meaning}}</div>
                    <div class="sentence">{{sentenses}}</div>
                    <div class="audio-row">{{sentence_sound}}</div>
                    <div class="audio-row">{{meaning_sound}}</div>
                    <div class="image-box">{{images}}</div>
                """,
            },
            {
                "name": "Card 2 - Type The Word",
                "qfmt": """
                    <div class="card-box">
                        <div class="label">Type the missing word</div>
                        <div class="sentence big-sentence">{{sentence_cloze}}</div>
                        <div class="hint">Nghĩa: {{vietnamese}}</div>
                        <div class="type-box">{{type:words}}</div>
                    </div>
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr id="answer">
                    <div class="answer-title">Correct answer</div>
                    <div class="word answer">{{words}}</div>
                    <div class="pronounce">/{{pronounce}}/</div>
                    <div class="meaning">{{meaning}}</div>
                    <div class="sentence">{{sentenses}}</div>
                    <div class="audio-row">{{sound}}</div>
                    <div class="audio-row">{{sentence_sound}}</div>
                    <div class="image-box">{{images}}</div>
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

            .card-box {
                padding: 22px;
            }

            .label {
                font-size: 18px;
                color: #64748b;
                margin-bottom: 16px;
            }

            .word {
                font-size: 48px;
                font-weight: bold;
                color: #2563eb;
                margin: 14px 0;
            }

            .pronounce {
                font-size: 24px;
                color: #64748b;
                margin-top: 8px;
            }

            .vietnamese {
                font-size: 36px;
                font-weight: bold;
                color: #16a34a;
                margin-top: 18px;
            }

            .meaning {
                font-size: 23px;
                color: #334155;
                margin-top: 16px;
                line-height: 1.45;
            }

            .sentence {
                font-size: 25px;
                color: #111827;
                margin-top: 18px;
                line-height: 1.45;
            }

            .big-sentence {
                font-size: 32px;
                font-weight: bold;
                margin: 24px 0;
            }

            .hint {
                font-size: 24px;
                color: #16a34a;
                margin-top: 12px;
            }

            .type-box {
                margin-top: 24px;
            }

            input[type=text] {
                font-size: 30px;
                padding: 12px 16px;
                border: 2px solid #2563eb;
                border-radius: 12px;
                text-align: center;
                max-width: 90%;
            }

            .answer-title {
                font-size: 18px;
                color: #64748b;
                margin-top: 16px;
            }

            .answer {
                color: #dc2626;
            }

            .audio {
                margin-top: 14px;
            }

            .audio-row {
                margin-top: 12px;
            }

            .image-box {
                margin-top: 22px;
            }

            .image-box img {
                max-width: 90%;
                max-height: 340px;
                border-radius: 18px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.16);
            }
        """,
    )


# =========================
# MAIN PROCESS
# =========================

async def process_words():
    words = read_words()

    model = build_model()
    deck = genanki.Deck(DECK_ID, DECK_NAME)

    all_media_files = []

    print(f"[INFO] Total words: {len(words)}")

    for index, word in enumerate(words, start=1):
        print(f"\n[INFO] Processing {index}/{len(words)}: {word}")

        safe_name = sanitize_filename(word)

        dictionary_data = fetch_dictionary_data(word)

        meaning = dictionary_data["meaning"]
        pronounce = dictionary_data["pronounce"]
        sentence = dictionary_data["sentence"]
        vietnamese = get_vietnamese_meaning(word, meaning)
        sentence_cloze = make_cloze_sentence(sentence, word)

        word_audio = AUDIO_DIR / f"{safe_name}_word.mp3"
        sentence_audio = AUDIO_DIR / f"{safe_name}_sentence.mp3"
        meaning_audio = AUDIO_DIR / f"{safe_name}_meaning_vi.mp3"
        image_file = IMAGE_DIR / f"{safe_name}.jpg"

        await create_audio(word, word_audio, VOICE_EN)
        await create_audio(sentence, sentence_audio, VOICE_EN)
        await create_audio(vietnamese, meaning_audio, VOICE_VI)

        create_placeholder_image(word, vietnamese, image_file)

        validate_file_exists(word_audio, "word audio")
        validate_file_exists(sentence_audio, "sentence audio")
        validate_file_exists(meaning_audio, "meaning audio")
        validate_file_exists(image_file, "image")

        sound_html = f"[sound:{word_audio.name}]"
        sentence_sound_html = f"[sound:{sentence_audio.name}]"
        meaning_sound_html = f"[sound:{meaning_audio.name}]"
        image_html = f'{image_file.name}'

        note = genanki.Note(
            model=model,
            fields=[
                word,
                safe_text(meaning),
                safe_text(sentence),
                safe_text(sentence_cloze),
                image_html,
                safe_text(pronounce),
                safe_text(vietnamese),
                sound_html,
                sentence_sound_html,
                meaning_sound_html,
            ],
            tags=["auto", "vocabulary"],
            guid=genanki.guid_for(word),
        )

        deck.add_note(note)

        all_media_files.extend([
            str(word_audio),
            str(sentence_audio),
            str(meaning_audio),
            str(image_file),
        ])

        time.sleep(0.2)

    package = genanki.Package(deck)
    package.media_files = all_media_files
    package.write_to_file(str(OUTPUT_APKG))

    validate_file_exists(OUTPUT_APKG, "APKG file")

    print("\n[DONE] APKG created successfully.")
    print(f"[DONE] Deck name: {DECK_NAME}")
    print(f"[DONE] Output: {OUTPUT_APKG}")
    print(f"[DONE] Total notes: {len(words)}")
    print(f"[DONE] Cards per note: 2")
    print(f"[DONE] Total expected cards: {len(words) * 2}")


if __name__ == "__main__":
    asyncio.run(process_words())