import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from anki_vocab_app.anki_builder import GeneratedWord
from anki_vocab_app.core import get_cached_word, init_cache, save_cached_word, split_words
from anki_vocab_app.dictionary import is_placeholder_sentence
from anki_vocab_app.validator import (
    build_unique_apkg_path,
    make_cloze_sentence,
    sanitize_filename,
)


class ValidatorTests(unittest.TestCase):
    def test_sanitize_filename_removes_unsafe_characters(self):
        self.assertEqual(sanitize_filename("  Hello, World!  "), "hello_world")

    def test_sanitize_filename_uses_fallback_for_empty_text(self):
        self.assertEqual(sanitize_filename("!!!"), "word")

    def test_make_cloze_sentence_replaces_only_the_first_match(self):
        self.assertEqual(
            make_cloze_sentence("Run fast, then run again.", "run"),
            "____ fast, then run again.",
        )

    def test_make_cloze_sentence_uses_word_boundaries(self):
        self.assertEqual(
            make_cloze_sentence("The runner is running.", "run"),
            "____ means run.",
        )

    def test_build_unique_apkg_path_is_deterministic_for_same_words(self):
        first = build_unique_apkg_path(["run", "walk"])
        second = build_unique_apkg_path(["run", "walk"])
        self.assertEqual(first.name.split("_")[-1], second.name.split("_")[-1])
        self.assertTrue(first.name.endswith(".apkg"))


class SplitWordsTests(unittest.TestCase):
    def test_split_words_skips_comments_and_blanks(self):
        self.assertEqual(split_words("# note\n\nrun\n walk "), ["run", "walk"])

    def test_split_words_skips_csv_header(self):
        self.assertEqual(split_words("word\nrun\nwalk"), ["run", "walk"])


class CacheTests(unittest.TestCase):
    def test_save_cached_word_preserves_created_at(self):
        from anki_vocab_app import core

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_db = core.CACHE_DB
            original_dir = core.CACHE_DIR
            original_ready = core._cache_ready
            try:
                core.CACHE_DB = tmp_path / "vocab_cache.sqlite"
                core.CACHE_DIR = tmp_path
                core._cache_ready = False
                init_cache()
                entry = GeneratedWord(
                    word="run",
                    safe_name="run",
                    meaning="to move quickly",
                    pronounce="rʌn",
                    sentence="I run every morning.",
                    sentence_cloze="I ____ every morning.",
                    vietnamese="chạy",
                    word_audio=tmp_path / "run_word.mp3",
                    sentence_audio=tmp_path / "run_sentence.mp3",
                    meaning_audio=tmp_path / "run_meaning_vi.mp3",
                    image_file=Path(),
                )
                save_cached_word(entry)
                first = get_cached_word("run")
                entry.meaning = "updated"
                save_cached_word(entry)
                second = get_cached_word("run")
                self.assertEqual(first["created_at"], second["created_at"])
                self.assertEqual(second["meaning"], "updated")
            finally:
                core.CACHE_DB = original_db
                core.CACHE_DIR = original_dir
                core._cache_ready = original_ready


class PlaceholderTests(unittest.TestCase):
    def test_placeholder_sentence_detects_fallback(self):
        self.assertTrue(is_placeholder_sentence("I learned the word run today.", "run"))
        self.assertFalse(is_placeholder_sentence("I run every morning.", "run"))


if __name__ == "__main__":
    unittest.main()
