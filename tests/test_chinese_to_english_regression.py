"""Chinese-to-English regression coverage.

Every other regression fixture translates into Chinese, which let three
asymmetries survive: CJK residue in a non-Chinese translation went unreported,
spelled Chinese numerals were never checked at all, and a correct magnitude
conversion (3万 -> 30,000) was reported as a defect.
"""

from pathlib import Path
import unittest

from translation_quality import validate_translation


FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class ChineseToEnglishRegressionTests(unittest.TestCase):
    def test_complete_translation_is_accepted(self):
        self.assertEqual(
            validate_translation(
                _read("typhoon_zh.txt"), _read("typhoon_en_valid.txt"), "en"
            ),
            [],
        )

    def test_observed_defects_are_rejected(self):
        errors = validate_translation(
            _read("typhoon_zh.txt"), _read("typhoon_en_invalid.txt"), "en"
        )
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)
        self.assertIn("PARAGRAPH_COUNT_MISMATCH", errors)
        self.assertIn("SPELLED_NUMBER_MISMATCH", errors)

    def test_chinese_magnitude_must_be_converted_not_copied(self):
        source = "约3万名居民撤离。"
        self.assertEqual(
            validate_translation(source, "About 30,000 residents evacuated.", "en"),
            [],
        )
        self.assertIn(
            "ARABIC_NUMBER_MISMATCH",
            validate_translation(source, "About 3 residents evacuated.", "en"),
        )

    def test_spelled_chinese_numerals_are_checked_in_english_output(self):
        source = "六人受伤。"
        self.assertEqual(
            validate_translation(source, "Six people were injured.", "en"), []
        )
        self.assertEqual(
            validate_translation(source, "6 people were injured.", "en"), []
        )
        for wrong in ("Sixty people were injured.", "People were injured."):
            with self.subTest(output=wrong):
                self.assertIn(
                    "SPELLED_NUMBER_MISMATCH",
                    validate_translation(source, wrong, "en"),
                )

    def test_chinese_magnitude_phrases_require_english_equivalent(self):
        source = "数以万计的居民撤离。"
        self.assertEqual(
            validate_translation(
                source, "Tens of thousands of residents evacuated.", "en"
            ),
            [],
        )
        self.assertIn(
            "SPELLED_NUMBER_MISMATCH",
            validate_translation(source, "Hundreds of residents evacuated.", "en"),
        )

    def test_chinese_residue_is_rejected_only_for_non_cjk_targets(self):
        source = "当地政府下令撤离。"
        self.assertIn(
            "TARGET_SCRIPT_RESIDUAL",
            validate_translation(source, "Local 政府 ordered evacuation.", "en"),
        )
        # 日语目标合法使用汉字，不得误报。
        self.assertNotIn(
            "TARGET_SCRIPT_RESIDUAL",
            validate_translation(source, "地元政府は避難を命じた。", "ja"),
        )


if __name__ == "__main__":
    unittest.main()
