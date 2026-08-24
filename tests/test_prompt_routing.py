import unittest

from translator_cli import TranslatorCLI


class PromptRoutingTests(unittest.TestCase):
    def make_cli(self):
        cli = object.__new__(TranslatorCLI)
        cli.config = {"target_lang_key": "1"}
        return cli

    def test_english_to_chinese_has_base_and_pair_skill(self):
        prompt, source, target = self.make_cli().build_dynamic_prompt(
            "Local authorities ordered six evacuations."
        )
        self.assertIn("Translate every source title", prompt)
        self.assertIn("## SCOPE\nENGLISH → SIMPLIFIED CHINESE", prompt)
        self.assertEqual(prompt.count("## SCOPE"), 1)
        self.assertEqual(
            (source, target),
            ("English", "Simplified Chinese (简体中文)"),
        )

    def test_mixed_to_chinese_has_base_and_pair_skill(self):
        prompt, source, target = self.make_cli().build_dynamic_prompt(
            "这个 app 需要 update"
        )
        self.assertIn("Translate every source title", prompt)
        self.assertIn("## SCOPE\nMIXED LANGUAGE → SIMPLIFIED CHINESE", prompt)
        self.assertEqual(prompt.count("## SCOPE"), 1)
        self.assertEqual(
            (source, target),
            ("Mixed / 混合夹杂", "Simplified Chinese (简体中文)"),
        )

    def test_every_supported_source_and_target_includes_base_once(self):
        samples = (
            "Local authorities ordered evacuations.",
            "当地政府下令撤离。",
            "これはひなんしてください。",
            "당국은 대피를 명령했다.",
            "Власти приказали эвакуироваться.",
            "Die Behörden müssen Häuser räumen.",
            "¿Las autoridades ordenaron la evacuación?",
            "Les autorités ont annoncé que ça commence.",
            "Gli abitanti sono in una città e non partono.",
        )
        cli = self.make_cli()
        for target_key in map(str, range(1, 10)):
            cli.config["target_lang_key"] = target_key
            for source in samples:
                prompt, _, _ = cli.build_dynamic_prompt(source)
                self.assertEqual(prompt.count("Translate every source title"), 1)
                self.assertLessEqual(prompt.count("## SCOPE"), 1)


if __name__ == "__main__":
    unittest.main()
