import unittest

from document_translation import looks_likely_truncated, plan_paragraph_chunks


class InputCompletenessTests(unittest.TestCase):
    def test_detects_partial_english_tail(self):
        self.assertTrue(looks_likely_truncated("Voters ahead of th", "en"))

    def test_accepts_complete_english_sentence(self):
        self.assertFalse(looks_likely_truncated("Voters remain concerned.", "en"))


class ParagraphChunkPlanningTests(unittest.TestCase):
    def test_keeps_short_document_whole(self):
        text = "Heading\n\nFirst paragraph.\n\nSecond paragraph."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 20),
            [text],
        )

    def test_splits_only_at_paragraph_boundaries(self):
        text = "One two three.\n\nFour five six.\n\nSeven eight nine."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 6),
            ["One two three.\n\nFour five six.", "Seven eight nine."],
        )
