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
    plan_translation_units,
    rank_planning_candidates,
    MAX_PLANNED_TERMS,
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
        terms_path = str(Path(__file__).parent.parent / "skills" / "news_terms.json")
        english_to_chinese = load_curated_terms(terms_path, "en_to_zh")
        # 不锁定整个词库内容，只保证方向取对且既有条目不丢。
        for source_term, target_term in (
            ("Reuters", "路透社"),
            ("Financial Times", "《金融时报》"),
            ("Strait of Hormuz", "霍尔木兹海峡"),
            ("BBC Scotland News", "英国广播公司苏格兰新闻部"),
            ("BBC", "BBC"),
            ("BST", "英国夏令时"),
        ):
            self.assertEqual(english_to_chinese[source_term], target_term)

    def test_news_terms_are_available_in_both_directions(self):
        terms_path = str(Path(__file__).parent.parent / "skills" / "news_terms.json")
        self.assertEqual(load_curated_terms(terms_path, "zh_to_en")["路透社"], "Reuters")
        self.assertEqual(
            load_curated_terms(terms_path, "en_to_ja")["Reuters"], "ロイター通信"
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


class TranslationUnitPlanTests(unittest.TestCase):
    def count(self, text):
        return len(text.split())

    def test_each_source_line_becomes_its_own_unit(self):
        source = "Headline goes here\nBody sentence follows.\n\nSecond paragraph."
        self.assertEqual(
            plan_translation_units(source, self.count, 100),
            [
                ("Headline goes here", ""),
                ("Body sentence follows.", "\n"),
                ("Second paragraph.", "\n\n"),
            ],
        )

    def test_separators_reproduce_the_source_layout(self):
        source = "A title\nA body line.\n\nNext paragraph.\nIts second line."
        units = plan_translation_units(source, self.count, 100)
        rebuilt = "".join(separator + text for text, separator in units)
        self.assertEqual(rebuilt, source)

    def test_an_oversized_line_is_split_without_adding_a_line_break(self):
        source = "First sentence here. Second sentence here. Third sentence here."
        units = plan_translation_units(source, self.count, 4)
        self.assertGreater(len(units), 1)
        # 同一行被拆开的片段不得引入换行，否则会伪造出新的行结构。
        self.assertEqual([separator for _, separator in units[1:]], [""] * (len(units) - 1))


class PlanningCostTests(unittest.TestCase):
    def count(self, text):
        return max(1, len(text.split()))

    def test_title_case_headline_fragments_are_not_terminology(self):
        source = (
            "In the News • FERC Moves to Fast-Track AI Data Centers as Power "
            "Bottleneck Becomes National Priority • DOE Announces Loan "
            "Commitment to Revive American Nuclear Supply Chain"
        )
        candidates = extract_term_candidates(source)
        for junk in (
            "Power Bottleneck Becomes National Priority",
            "Revive American Nuclear Supply Chain",
            "Track AI Data Centers",
        ):
            self.assertNotIn(junk, candidates)
        self.assertIn("FERC", candidates)
        self.assertIn("DOE", candidates)

    def test_real_proper_nouns_survive_the_word_cap(self):
        source = "Scott Bessent wrote about the Strait of Hormuz in the Financial Times."
        candidates = extract_term_candidates(source)
        for term in ("Scott Bessent", "Strait of Hormuz", "Financial Times"):
            self.assertIn(term, candidates)

    def test_only_repeated_terms_are_worth_planning(self):
        text = (
            "Canaan shipped the Avalon chip. Canaan said Avalon sold well. "
            "Settlement Over was a headline fragment. Canaan grew."
        )
        planned = rank_planning_candidates(("Canaan", "Avalon", "Settlement Over"), text)
        self.assertEqual(planned[0], "Canaan")
        self.assertIn("Avalon", planned)
        self.assertNotIn("Settlement Over", planned)

    def test_planning_is_capped(self):
        text = " ".join(f"Term{index} Term{index}" for index in range(30))
        candidates = tuple(f"Term{index}" for index in range(30))
        self.assertEqual(
            len(rank_planning_candidates(candidates, text)), MAX_PLANNED_TERMS
        )

    def test_only_a_two_line_paragraph_is_split_per_line(self):
        heading_and_body = "A headline here\nThe body sentence follows."
        self.assertEqual(
            [text for text, _ in plan_translation_units(heading_and_body, self.count, 100)],
            ["A headline here", "The body sentence follows."],
        )

    def test_a_list_block_stays_in_one_unit(self):
        # 逐行翻译列表会让每个条目各付一次完整提示词的代价。
        bullets = "\n".join(f"• Item number {index}" for index in range(6))
        units = plan_translation_units(bullets, self.count, 100)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0][0], bullets)
