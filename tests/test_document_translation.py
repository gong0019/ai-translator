import unittest
from pathlib import Path

from document_translation import (
    extract_term_candidates,
    format_glossary,
    load_curated_terms,
    looks_likely_truncated,
    match_curated_terms,
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

    def test_streaming_mode_emits_each_paragraph_immediately(self):
        text = "Heading\n\nFirst paragraph.\n\nSecond paragraph."
        self.assertEqual(
            plan_paragraph_chunks(
                text,
                lambda value: len(value.split()),
                20,
                stream_each_paragraph=True,
            ),
            ["Heading", "First paragraph.", "Second paragraph."],
        )

    def test_streaming_mode_splits_an_oversized_single_paragraph(self):
        text = "One two. Three four. Five six."
        self.assertEqual(
            plan_paragraph_chunks(
                text,
                lambda value: len(value.split()),
                3,
                stream_each_paragraph=True,
            ),
            ["One two.", "Three four.", "Five six."],
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

    def test_extracts_individual_people_with_camel_case_surnames(self):
        source = (
            "Shirley Freeman, Julia Stephen and David McColl's victims spoke. "
            "Sheriff Craig Findlater delivered the ruling."
        )
        candidates = extract_term_candidates(source)
        self.assertIn("Shirley Freeman", candidates)
        self.assertIn("Julia Stephen", candidates)
        self.assertIn("David McColl", candidates)
        self.assertIn("Craig Findlater", candidates)

    def test_sentence_starter_does_not_absorb_following_lowercase_words(self):
        self.assertEqual(
            extract_term_candidates("He said London was important."),
            ("London",),
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

    def test_person_glossary_adds_last_name_alias_for_later_paragraphs(self):
        glossary = parse_glossary_response(
            '{"David McColl":"戴维·麦科尔"}',
            ("David McColl",),
            {},
        )
        self.assertEqual(
            glossary,
            {"David McColl": "戴维·麦科尔", "McColl": "麦科尔"},
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

    def test_loads_multilingual_specialist_terms_for_requested_pair(self):
        terms_path = Path(__file__).parent.parent / "skills" / "finance_terms.json"
        self.assertEqual(
            load_curated_terms(str(terms_path), "en_to_zh")["quantitative easing"],
            "量化宽松",
        )
        self.assertEqual(
            load_curated_terms(str(terms_path), "en_to_ja")["inflation"],
            "インフレーション",
        )
        self.assertEqual(
            load_curated_terms(str(terms_path), "zh_to_en")["通货膨胀"],
            "inflation",
        )

    def test_loads_multilingual_hardware_and_material_terms(self):
        hardware_path = Path(__file__).parent.parent / "skills" / "hardware_terms.json"
        materials_path = Path(__file__).parent.parent / "skills" / "materials_terms.json"

        self.assertEqual(
            load_curated_terms(str(hardware_path), "en_to_zh")["printed circuit board"],
            "印制电路板",
        )
        self.assertEqual(
            load_curated_terms(str(hardware_path), "zh_to_ja")["水冷"],
            "水冷却",
        )
        self.assertEqual(
            load_curated_terms(str(materials_path), "en_to_zh")["polypropylene"],
            "聚丙烯（PP）",
        )
        self.assertEqual(
            load_curated_terms(str(materials_path), "zh_to_en")["聚乙烯（PE）"],
            "polyethylene",
        )

    def test_loads_multilingual_cross_border_and_trade_terms(self):
        commerce_path = Path(__file__).parent.parent / "skills" / "crossborder_ecommerce_terms.json"
        trade_path = Path(__file__).parent.parent / "skills" / "trade_terms.json"

        self.assertEqual(
            load_curated_terms(str(commerce_path), "en_to_zh")["order fulfillment"],
            "订单履约",
        )
        self.assertEqual(
            load_curated_terms(str(trade_path), "en_to_zh")["free on board"],
            "船上交货（FOB）",
        )
        self.assertEqual(
            load_curated_terms(str(trade_path), "zh_to_en")["提单"],
            "bill of lading",
        )

    def test_matches_lowercase_curated_terms_that_are_not_proper_nouns(self):
        matches = match_curated_terms(
            "Inflation rose while quantitative easing was discussed.",
            {
                "inflation": "通货膨胀",
                "quantitative easing": "量化宽松",
            },
        )
        self.assertEqual(
            matches,
            {"inflation": "通货膨胀", "quantitative easing": "量化宽松"},
        )

    def test_formats_non_empty_glossary_for_document_prompt(self):
        self.assertEqual(
            format_glossary({"Reuters": "路透社", "BST": "英国夏令时"}),
            "DOCUMENT GLOSSARY:\n- Reuters => 路透社\n- BST => 英国夏令时",
        )

    def test_formats_empty_glossary_as_empty_string(self):
        self.assertEqual(format_glossary({}), "")
