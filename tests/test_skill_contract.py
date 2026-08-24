from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE_CONTRACT = (
    "Translate every source fact exactly once.",
    "Preserve paragraph order, headings, quotations, names, numbers, units, dates, times, negation, modality, and uncertainty.",
    "Follow the supplied document glossary exactly.",
    "Do not summarize, explain, censor, or complete missing source text.",
    "Output only the complete translation in {target_name}.",
)


class SkillContractTests(unittest.TestCase):
    def test_base_contains_durable_translation_contract(self):
        text = (ROOT / "skills/base.md").read_text(encoding="utf-8")
        for required in BASE_CONTRACT:
            self.assertIn(required, text)

    def test_english_to_chinese_keeps_only_language_specific_rules(self):
        text = (ROOT / "skills/en_to_zh.md").read_text(encoding="utf-8")
        self.assertIn("natural Simplified Chinese grammar", text)
        self.assertIn("consistent transliteration", text)
        self.assertIn("established Chinese organization and place names", text)
        self.assertIn("no ordinary English residue", text)


if __name__ == "__main__":
    unittest.main()
