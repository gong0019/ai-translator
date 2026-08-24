from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "## SCOPE",
    "## MANDATORY COVERAGE",
    "## STRUCTURE",
    "## GRAMMAR",
    "## TERMINOLOGY",
    "## FORBIDDEN OUTPUT",
}
PROHIBITED = (
    "appropriate",
    "natural",
    "naturally",
    "idiomatic",
    "when appropriate",
    "where possible",
    "if needed",
    "when needed",
    "when necessary",
    "if necessary",
    "where needed",
    "where necessary",
    "where required",
    "as needed",
    "if appropriate",
    "as appropriate",
    "depending on context",
    "according to context",
    "context-appropriate",
    "prefer ",
    "try to",
    "may choose",
    "can choose",
    "as natural as possible",
)


class SkillContractTests(unittest.TestCase):
    def test_every_pair_skill_has_exact_sections(self):
        for path in sorted((ROOT / "skills").glob("*_to_*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(REQUIRED.issubset(set(text.splitlines())), path.name)

    def test_no_skill_uses_discretionary_phrases(self):
        for path in sorted((ROOT / "skills").glob("*.md")):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in PROHIBITED:
                self.assertNotIn(phrase, text, f"{path.name}: {phrase}")

    def test_base_contains_exact_invariants(self):
        text = (ROOT / "skills/base.md").read_text(encoding="utf-8")
        for required in (
            "Translate every source title, sentence, clause, list item, label, caption, and footnote exactly once.",
            "Keep each heading separate from the following body text.",
            "A Latin word is not protected merely because it is capitalized.",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
