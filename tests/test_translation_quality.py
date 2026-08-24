import unittest

from translation_quality import normalize_source_structure, validate_translation


class SourceNormalizationTests(unittest.TestCase):
    def test_repairs_word_split_by_terminal_wrap(self):
        self.assertEqual(
            normalize_source_structure("a\npproached Reno."),
            "approached Reno.",
        )

    def test_repairs_suffix_split_by_terminal_wrap(self):
        self.assertEqual(
            normalize_source_structure("weather contribut\ning to the spread."),
            "weather contributing to the spread.",
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


class TranslationValidatorTests(unittest.TestCase):
    def test_detects_empty_and_structure_loss(self):
        self.assertEqual(
            validate_translation("Title\nBody.", "", "zh"),
            ["EMPTY_OUTPUT"],
        )
        errors = validate_translation(
            "Title\nBody.\n\nNext paragraph.",
            "标题正文。",
            "zh",
        )
        self.assertIn("PARAGRAPH_COUNT_MISMATCH", errors)
        self.assertIn("LINE_STRUCTURE_LOSS", errors)
        self.assertIn("SENTENCE_COUNT_LOSS", errors)

    def test_detects_numbers_and_english_residual(self):
        source = (
            "Six people were injured; "
            "12 homes and 3.5% of land were affected."
        )
        output = "据 authorities 称，五人受伤；13所房屋和3.5%的土地受到影响。"
        errors = validate_translation(source, output, "zh")
        self.assertIn("ARABIC_NUMBER_MISMATCH", errors)
        self.assertIn("ENGLISH_NUMBER_MISMATCH", errors)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_accepts_chinese_numbers_and_protected_spans(self):
        source = "Six users opened https://example.com and `/opt/app/run.sh`."
        output = "六名用户打开了 https://example.com 和 `/opt/app/run.sh`。"
        self.assertEqual(validate_translation(source, output, "zh"), [])

    def test_tens_of_thousands_requires_equivalent_quantity(self):
        source = "Tens of thousands of people evacuated."
        self.assertIn(
            "ENGLISH_NUMBER_MISMATCH",
            validate_translation(source, "数千人撤离。", "zh"),
        )
        self.assertEqual(
            validate_translation(source, "数以万计的人撤离。", "zh"),
            [],
        )

    def test_hundreds_of_thousands_requires_equivalent_quantity(self):
        source = "Hundreds of thousands of people evacuated."
        self.assertEqual(
            validate_translation(source, "数十万人撤离。", "zh"),
            [],
        )

if __name__ == "__main__":
    unittest.main()
