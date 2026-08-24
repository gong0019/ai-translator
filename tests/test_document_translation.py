import unittest
from pathlib import Path

from document_translation import (
    extract_term_candidates,
    format_glossary,
    load_curated_terms,
    looks_likely_truncated,
    parse_glossary_response,
    plan_paragraph_chunks,
)


class InputCompletenessTests(unittest.TestCase):
    def test_detects_partial_english_tail(self):
        self.assertTrue(looks_likely_truncated("Voters ahead of th", "en"))

    def test_accepts_complete_english_sentence(self):
        self.assertFalse(looks_likely_truncated("Voters remain concerned.", "en"))


class ParagraphChunkPlanningTests(unittest.TestCase):
    def test_keeps_short_document_whole(self):
        text = "Heading\n\nFirst paragraph.\n\nSecond paragraph."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 20),
            [text],
        )

    def test_splits_only_at_paragraph_boundaries(self):
        text = "One two three.\n\nFour five six.\n\nSeven eight nine."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 6),
            ["One two three.\n\nFour five six.", "Seven eight nine."],
        )


class DocumentTerminologyTests(unittest.TestCase):
    def test_extracts_document_terms_without_sentence_starters(self):
        source = (
            "Scott Bessent wrote in the Financial Times. "
            "Bessent later spoke to Reuters at 18:00 BST."
        )
        self.assertEqual(
            extract_term_candidates(source),
            ("Scott Bessent", "Financial Times", "Bessent", "Reuters", "BST"),
        )

    def test_extracts_capitalized_terms_with_lowercase_connectors(self):
        self.assertEqual(
            extract_term_candidates("The Strait of Hormuz is strategically vital."),
            ("Strait of Hormuz",),
        )

    def test_curated_terms_override_model_and_malformed_values_are_dropped(self):
        response = '```json\n{"Bessent":"贝森特","Reuters":"路透通讯"}\n```'
        glossary = parse_glossary_response(
            response,
            ("Bessent", "Reuters", "BST"),
            {"Reuters": "路透社", "BST": "英国夏令时"},
        )
        self.assertEqual(
            glossary,
            {"Bessent": "贝森特", "Reuters": "路透社", "BST": "英国夏令时"},
        )

    def test_malformed_planner_json_falls_back_to_curated_terms(self):
        self.assertEqual(
            parse_glossary_response("not json", ("Reuters",), {"Reuters": "路透社"}),
            {"Reuters": "路透社"},
        )

    def test_json_array_falls_back_to_curated_terms(self):
        self.assertEqual(
            parse_glossary_response("[]", ("Reuters",), {"Reuters": "路透社"}),
            {"Reuters": "路透社"},
        )

    def test_loads_requested_curated_term_pair(self):
        terms_path = Path(__file__).parent.parent / "skills" / "news_terms.json"
        self.assertEqual(
            load_curated_terms(str(terms_path), "en_to_zh"),
            {
                "Reuters": "路透社",
                "Financial Times": "《金融时报》",
                "Strait of Hormuz": "霍尔木兹海峡",
                "BBC Scotland News": "英国广播公司苏格兰新闻部",
                "BBC": "BBC",
                "BST": "英国夏令时",
            },
        )

    def test_formats_non_empty_glossary_for_document_prompt(self):
        self.assertEqual(
            format_glossary({"Reuters": "路透社", "BST": "英国夏令时"}),
            "DOCUMENT GLOSSARY:\n- Reuters => 路透社\n- BST => 英国夏令时",
        )

    def test_formats_empty_glossary_as_empty_string(self):
        self.assertEqual(format_glossary({}), "")
