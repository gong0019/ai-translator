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
        # 单单元文档常在 1400 token 上下，必须落在可重译范围内，
        # 否则唯一能抓住数字被篡改的那一遍永远不会跑。
        self.assertTrue(translator_cli.allows_repair(DEFAULT_CONFIG, 1424))
        self.assertTrue(translator_cli.allows_repair(DEFAULT_CONFIG, 1600))
        self.assertFalse(translator_cli.allows_repair(DEFAULT_CONFIG, 1601))


class ConfigPersistenceTests(unittest.TestCase):
    def saved(self, config):
        cli = object.__new__(translator_cli.TranslatorCLI)
        cli.config = dict(DEFAULT_CONFIG)
        cli.config.update(config)
        cli.models_map = {"1": {"filename": "model.gguf"}}
        cli.active_model_idx = "1"
        written = {}

        def fake_open(path, *args, **kwargs):
            import io as _io

            class Sink(_io.StringIO):
                def __exit__(inner, *exc):
                    written[path] = inner.getvalue()
                    return False

                def __enter__(inner):
                    return inner

                def fileno(inner):
                    return 0

            return Sink()

        with patch("translator_cli.open", fake_open, create=True):
            with patch("translator_cli.os.fsync"):
                with patch("translator_cli.os.makedirs"):
                    cli.save_config()
        import json as _json

        return _json.loads(next(iter(written.values())))

    def test_a_tuning_key_left_at_its_default_is_not_persisted(self):
        # 把默认值写进文件，会让旧值永久盖住代码里的新默认值。
        payload = self.saved({})
        self.assertNotIn("retry_max_source_tokens", payload)
        self.assertNotIn("n_ctx", payload)

    def test_session_choices_are_always_persisted(self):
        payload = self.saved({"target_lang_key": "3"})
        self.assertEqual(payload["target_lang_key"], "3")
        self.assertEqual(payload["selected_model_filename"], "model.gguf")

    def test_a_hand_edited_tuning_key_survives(self):
        payload = self.saved({"retry_max_source_tokens": 400, "n_ctx": 4096})
        self.assertEqual(payload["retry_max_source_tokens"], 400)
        self.assertEqual(payload["n_ctx"], 4096)


class PromptSizeTests(unittest.TestCase):
    def prompt_for(self, source, compact):
        cli = object.__new__(translator_cli.TranslatorCLI)
        cli.config = {"target_lang_key": "1"}
        return cli.build_dynamic_prompt(source, compact=compact)[0]

    def test_a_short_source_drops_the_grammar_rules(self):
        short = "cut the generation from three passes to one"
        compact = self.prompt_for(short, True)
        full = self.prompt_for(short, False)
        self.assertLess(len(compact) * 4, len(full))
        # 契约和语向必须留下，规则才是可省的部分。
        self.assertIn("Translate every source fact exactly once.", compact)
        self.assertIn("ENGLISH → SIMPLIFIED CHINESE", compact)
        self.assertNotIn("## GRAMMAR", compact)
        self.assertIn("## GRAMMAR", full)

    def test_the_threshold_decides_which_prompt_a_unit_gets(self):
        config = translator_cli.DEFAULT_CONFIG
        self.assertFalse(translator_cli.wants_full_skill(config, 16))
        self.assertFalse(translator_cli.wants_full_skill(config, 79))
        self.assertTrue(translator_cli.wants_full_skill(config, 80))
        self.assertTrue(translator_cli.wants_full_skill(config, 1424))

    def test_an_invalid_threshold_falls_back_to_the_default(self):
        self.assertTrue(translator_cli.wants_full_skill({"full_skill_min_tokens": "x"}, 80))
        self.assertFalse(translator_cli.wants_full_skill({"full_skill_min_tokens": -1}, 79))

    def test_a_glossary_still_reaches_a_compact_prompt(self):
        cli = object.__new__(translator_cli.TranslatorCLI)
        cli.config = {"target_lang_key": "1"}
        prompt = cli.build_dynamic_prompt(
            "Reuters reported.", {"Reuters": "路透社"}, compact=True
        )[0]
        self.assertIn("- Reuters => 路透社", prompt)

if __name__ == "__main__":
    unittest.main()
