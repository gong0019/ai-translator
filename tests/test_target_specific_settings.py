"""Target-specific generation settings and script-aware OCR."""

import unittest
from unittest.mock import patch

import translator_cli
from translator_cli import DEFAULT_CONFIG, ocr_extract_text, resolve_repeat_penalty


class RepeatPenaltyTests(unittest.TestCase):
    def test_alphabetic_targets_get_a_lower_repeat_penalty(self):
        for target in ("en", "de", "fr", "es", "it", "ru"):
            with self.subTest(target=target):
                self.assertEqual(
                    resolve_repeat_penalty(DEFAULT_CONFIG, target), 1.02
                )

    def test_cjk_targets_keep_the_configured_penalty(self):
        for target in ("zh", "ja", "ko"):
            with self.subTest(target=target):
                self.assertEqual(
                    resolve_repeat_penalty(DEFAULT_CONFIG, target), 1.08
                )

    def test_a_lower_configured_penalty_is_never_raised(self):
        self.assertEqual(
            resolve_repeat_penalty({"repeat_penalty": 1.0}, "en"), 1.0
        )
        self.assertEqual(
            resolve_repeat_penalty({"repeat_penalty": 1.0}, "zh"), 1.0
        )


class ScriptAwareOcrTests(unittest.TestCase):
    def _language_argument(self, script, installed):
        recorded = {}

        def fake_run(cmd, **kwargs):
            if "-l" in cmd:
                recorded["langs"] = cmd[cmd.index("-l") + 1]
            return type("R", (), {"returncode": 0, "stdout": ""})()

        with patch.object(translator_cli, "detect_image_script", return_value=script):
            with patch.object(
                translator_cli,
                "get_installed_tesseract_languages",
                return_value=installed,
            ):
                with patch.object(translator_cli.subprocess, "run", fake_run):
                    ocr_extract_text("page.png")
        return recorded.get("langs", "")

    def test_detected_script_narrows_the_language_packs(self):
        installed = ["chi_sim", "chi_tra", "eng", "jpn", "kor", "rus", "deu"]
        self.assertEqual(self._language_argument("Japanese", installed), "jpn")
        self.assertEqual(self._language_argument("Hangul", installed), "kor")
        self.assertEqual(self._language_argument("Cyrillic", installed), "rus")
        self.assertEqual(
            self._language_argument("HanS", installed), "chi_sim"
        )
        # 拉丁字母无法只凭字形区分语种，同字母表的包一起用。
        self.assertEqual(self._language_argument("Latin", installed), "eng+deu")

    def test_failed_detection_falls_back_to_every_installed_pack(self):
        installed = ["chi_sim", "eng", "jpn"]
        self.assertEqual(
            self._language_argument("", installed), "chi_sim+eng+jpn"
        )

    def test_unavailable_pack_for_a_detected_script_falls_back(self):
        self.assertEqual(
            self._language_argument("Japanese", ["chi_sim", "eng"]), "chi_sim+eng"
        )



class GenerationBudgetTests(unittest.TestCase):
    def test_generation_is_bounded_by_the_source_it_translates(self):
        # 短句不该拿到 4096 的上限，否则小模型会一路跑飞并填满上下文。
        self.assertEqual(translator_cli.resolve_max_tokens(DEFAULT_CONFIG, 20), 256)
        self.assertEqual(translator_cli.resolve_max_tokens(DEFAULT_CONFIG, 1424), 2659)

    def test_the_configured_ceiling_is_never_exceeded(self):
        self.assertEqual(
            translator_cli.resolve_max_tokens({"max_tokens": 512}, 5000), 512
        )

    def test_a_repair_is_only_attempted_for_a_bounded_unit(self):
        self.assertTrue(translator_cli.allows_repair(DEFAULT_CONFIG, 250))
        self.assertTrue(translator_cli.allows_repair(DEFAULT_CONFIG, 800))
        self.assertFalse(translator_cli.allows_repair(DEFAULT_CONFIG, 801))

if __name__ == "__main__":
    unittest.main()
