import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from datetime import datetime
from anki_vocab_app.anki_builder import (
    DECK_NAME,
    GeneratedWord,
    deck_id_for,
    nested_deck_name,
)
from anki_vocab_app.core import (
    _translation_needs_refresh,
    get_cached_word,
    init_cache,
    resolve_deck_name,
    save_cached_word,
    split_words,
)
from anki_vocab_app.dictionary import is_placeholder_sentence
from anki_vocab_app.dictionary_inspector import format_dictionary_report
from anki_vocab_app.translator import _parse_translation, get_vietnamese_meaning
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

    def test_nested_deck_name_is_child_of_parent_deck(self):
        when = datetime(2026, 10, 7, 11, 31, 5)
        name = nested_deck_name("Anki Vocab App", when, "a1b2c3d4")
        self.assertTrue(name.startswith(f"{DECK_NAME}::"))
        self.assertEqual(name, "Anki Vocab App::2026-10-07 11:31:05 a1b2c3d4")

    def test_deck_ids_differ_for_different_subdecks(self):
        first = deck_id_for("Anki Vocab App::2026-10-07 11:31:05 a1b2c3d4")
        second = deck_id_for("Anki Vocab App::2026-10-07 12:00:00 b2c3d4e5")
        self.assertNotEqual(first, second)


class SplitWordsTests(unittest.TestCase):
    def test_split_words_skips_comments_and_blanks(self):
        self.assertEqual(split_words("# note\n\nrun\n walk "), ["run", "walk"])

    def test_split_words_skips_csv_header(self):
        self.assertEqual(split_words("word\nrun\nwalk"), ["run", "walk"])


class CacheTests(unittest.TestCase):
    def test_deck_name_is_parent_first_then_child(self):
        from anki_vocab_app import core

        with TemporaryDirectory() as tmp:
            original_db = core.CACHE_DB
            original_dir = core.CACHE_DIR
            original_ready = core._cache_ready
            try:
                core.CACHE_DB = Path(tmp) / "vocab_cache.sqlite"
                core.CACHE_DIR = Path(tmp)
                core._cache_ready = False
                when = datetime(2026, 10, 7, 11, 31, 5)
                first = resolve_deck_name("My Vocabulary", when, "a1b2c3d4")
                second = resolve_deck_name("My Vocabulary", when, "a1b2c3d4")
                self.assertEqual(first, "My Vocabulary")
                self.assertEqual(
                    second,
                    "My Vocabulary::2026-10-07 11:31:05 a1b2c3d4",
                )
            finally:
                core.CACHE_DB = original_db
                core.CACHE_DIR = original_dir
                core._cache_ready = original_ready

    def test_translation_refresh_is_needed_when_cache_contains_english_word(self):
        self.assertTrue(_translation_needs_refresh("resilient", "resilient"))
        self.assertFalse(_translation_needs_refresh("resilient", "đàn hồi"))
        self.assertTrue(_translation_needs_refresh("resilient", ""))

    def test_translation_payload_is_parsed_without_returning_source_word(self):
        self.assertEqual(
            _parse_translation([[["đàn hồi", "resilient", None]]]),
            "đàn hồi",
        )
        self.assertEqual(_parse_translation({"translation": "đàn hồi"}), "")

    def test_translation_comes_from_local_dictionary(self):
        translation = get_vietnamese_meaning("resilient")
        self.assertIn("đàn hồi", translation)
        self.assertIn("phục hồi", translation)

    def test_offline_dictionary_returns_ipa_pos_definitions_and_examples(self):
        from anki_vocab_app.offline_dictionary import lookup_offline_word

        entry = lookup_offline_word("resilient")
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertTrue(entry["pronounce"])
        self.assertFalse(entry["pronounce"].startswith("/"))
        self.assertIn("[A]", entry["meaning"])
        self.assertIn("Example:", entry["meaning"])
        self.assertIn("đàn hồi", entry["vietnamese"])

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
                    pronounce="rʌn",
                    sentence="I run every morning.",
                    sentence_cloze="I ____ every morning.",
                    vietnamese="chạy",
                    word_audio=tmp_path / "run_word.mp3",
                    sentence_audio=tmp_path / "run_sentence.mp3",
                    image_file=Path(),
                )
                save_cached_word(entry)
                first = get_cached_word("run")
                save_cached_word(entry)
                second = get_cached_word("run")
                self.assertEqual(first["created_at"], second["created_at"])
                self.assertEqual(second["word"], "run")
            finally:
                core.CACHE_DB = original_db
                core.CACHE_DIR = original_dir
                core._cache_ready = original_ready


class PlaceholderTests(unittest.TestCase):
    def test_placeholder_sentence_detects_fallback(self):
        self.assertTrue(is_placeholder_sentence("I learned the word run today.", "run"))
        self.assertFalse(is_placeholder_sentence("I run every morning.", "run"))


class DictionaryReportTests(unittest.TestCase):
    def test_empty_dictionary_report_lists_checked_paths(self):
        report = {
            "active": False,
            "paths_checked": ["one.tab", "two.mdx"],
        }
        text = format_dictionary_report(report)
        self.assertIn("No installed dictionary found", text)
        self.assertIn("one.tab", text)

    def test_dictionary_report_includes_structure(self):
        report = {
            "active": True,
            "format": "tab",
            "path": "dictionary.tab",
            "size_bytes": 123,
            "entry_count": 10,
            "fields": ["word", "meaning"],
            "samples": [{"word": "run"}],
        }
        text = format_dictionary_report(report)
        self.assertIn("Entries: 10", text)
        self.assertIn("Fields: word, meaning", text)
        self.assertIn("run", text)


if __name__ == "__main__":
    unittest.main()
