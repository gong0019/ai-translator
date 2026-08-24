from pathlib import Path
import unittest

from document_translation import (
    extract_term_candidates,
    load_curated_terms,
    looks_likely_truncated,
    parse_glossary_response,
    plan_paragraph_chunks,
)
from translation_quality import (
    find_missing_glossary_terms,
    find_unexpected_latin_tokens,
    validate_translation,
)


ROOT = Path(__file__).resolve().parents[1]

IRAN_ARTICLE = """Iran dismissed Bessent's comments and said it would shut down all oil exports from the region "if the war continues", according to news agency Reuters.

The Iranian regime warned shipping not to pass through the Strait of Hormuz without its permission.

Bessent made the comments in an opinion piece for the Financial Times. He is expected to hold a press conference in the US at 13:00 local time (18:00 BST) on Monday.

In the US, gasoline prices have surpassed $4 a gallon and affordability is among the top concerns of American voters ahead of th"""

COMPLETE_IRAN_ARTICLE = IRAN_ARTICLE[:-2] + "the election."

EXPECTED_TERMS = {
    "Reuters": "路透社",
    "Financial Times": "《金融时报》",
    "Strait of Hormuz": "霍尔木兹海峡",
    "BST": "英国夏令时",
}


class IranNewsRegressionTests(unittest.TestCase):
    def test_detects_truncated_article_tail(self):
        self.assertTrue(looks_likely_truncated(IRAN_ARTICLE, "en"))
        self.assertFalse(looks_likely_truncated(COMPLETE_IRAN_ARTICLE, "en"))

    def test_extracts_reported_news_terms_and_loads_curated_renderings(self):
        candidates = extract_term_candidates(IRAN_ARTICLE)
        for source_term in (*EXPECTED_TERMS, "Bessent"):
            self.assertIn(source_term, candidates)
        curated = load_curated_terms(str(ROOT / "skills/news_terms.json"), "en_to_zh")
        glossary = parse_glossary_response("{}", candidates, curated)
        for source_term, target_term in EXPECTED_TERMS.items():
            self.assertEqual(glossary[source_term], target_term)

    def test_complete_article_fits_one_chunk_when_budget_allows(self):
        self.assertEqual(
            plan_paragraph_chunks(
                COMPLETE_IRAN_ARTICLE,
                lambda value: len(value.split()),
                500,
            ),
            [COMPLETE_IRAN_ARTICLE],
        )

    def test_hand_checked_translation_preserves_terms_numbers_and_currency(self):
        source = (
            "Bessent wrote for the Financial Times and spoke at 13:00 "
            "local time (18:00 BST). Gasoline surpassed $4 a gallon, Reuters reported."
        )
        output = (
            "贝森特为《金融时报》撰文，并于当地时间13:00（英国夏令时18:00）发表讲话。"
            "据路透社报道，汽油价格突破每加仑4美元。"
        )
        glossary = {
            "Bessent": "贝森特",
            **EXPECTED_TERMS,
        }
        self.assertNotIn("ARABIC_NUMBER_MISMATCH", validate_translation(source, output, "zh"))
        self.assertEqual(find_missing_glossary_terms(source, output, glossary), ())
        self.assertEqual(find_unexpected_latin_tokens(source, output), ())


if __name__ == "__main__":
    unittest.main()
