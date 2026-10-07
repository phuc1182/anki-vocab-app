import unittest

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

    def test_build_unique_apkg_path_is_deterministic_for_same_words(self):
        first = build_unique_apkg_path(["run", "walk"])
        second = build_unique_apkg_path(["run", "walk"])
        self.assertEqual(first.name.split("_")[-1], second.name.split("_")[-1])
        self.assertTrue(first.name.endswith(".apkg"))


if __name__ == "__main__":
    unittest.main()
