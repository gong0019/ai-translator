from pathlib import Path
import unittest

from translation_quality import validate_translation


FIXTURES = Path(__file__).parent / "fixtures"


class NevadaRegressionTests(unittest.TestCase):
    def test_observed_defect_is_rejected(self):
        source = (FIXTURES / "nevada_wildfire_en.txt").read_text(
            encoding="utf-8"
        )
        invalid = (FIXTURES / "nevada_wildfire_zh_invalid.txt").read_text(
            encoding="utf-8"
        )
        errors = validate_translation(source, invalid, "zh")
        self.assertIn("LINE_STRUCTURE_LOSS", errors)
        self.assertIn("SENTENCE_COUNT_LOSS", errors)
        self.assertIn("ENGLISH_NUMBER_MISMATCH", errors)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_complete_translation_is_accepted(self):
        source = (FIXTURES / "nevada_wildfire_en.txt").read_text(
            encoding="utf-8"
        )
        valid = (FIXTURES / "nevada_wildfire_zh_valid.txt").read_text(
            encoding="utf-8"
        )
        self.assertEqual(validate_translation(source, valid, "zh"), [])
        self.assertIn("数以万计", valid)
        self.assertIn("里诺", valid)
        self.assertIn("六人", valid)


if __name__ == "__main__":
    unittest.main()
