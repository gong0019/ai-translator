import unittest

from translation_quality import normalize_source_structure


class SourceNormalizationTests(unittest.TestCase):
    def test_repairs_word_split_by_terminal_wrap(self):
        self.assertEqual(
            normalize_source_structure("a\npproached Reno."),
            "approached Reno.",
        )

    def test_joins_lowercase_soft_continuation(self):
        self.assertEqual(
            normalize_source_structure("the fire\ncontinued spreading."),
            "the fire continued spreading.",
        )

    def test_keeps_headline_separate_from_body(self):
        source = (
            "Thousands evacuate Nevada homes\n"
            "Tens of thousands of people were told to leave."
        )
        self.assertEqual(normalize_source_structure(source), source)

    def test_keeps_blank_paragraph_bullet_and_markdown_heading(self):
        source = "# Alert\n\n- Leave now\n- Use Route 80"
        self.assertEqual(normalize_source_structure(source), source)


if __name__ == "__main__":
    unittest.main()
