import unittest

from translation_quality import (
    find_missing_glossary_terms,
    find_unexpected_latin_tokens,
    normalize_source_structure,
    validate_translation,
)


class SourceNormalizationTests(unittest.TestCase):
    def test_repairs_word_split_by_terminal_wrap(self):
        self.assertEqual(
            normalize_source_structure("a\npproached Reno."),
            "approached Reno.",
        )

    def test_repairs_suffix_split_by_terminal_wrap(self):
        self.assertEqual(
            normalize_source_structure("weather contribut\ning to the spread."),
            "weather contributing to the spread.",
        )

    def test_joins_lowercase_soft_continuation(self):
        self.assertEqual(
            normalize_source_structure("the fire\ncontinued spreading."),
            "the fire continued spreading.",
        )

    def test_keeps_headline_separate_from_body(self):
        source = (
            "Thousands evacuate Nevada homes\n"
            "Tens of thousands of people were told to leave."
        )
        self.assertEqual(normalize_source_structure(source), source)

    def test_keeps_blank_paragraph_bullet_and_markdown_heading(self):
        source = "# Alert\n\n- Leave now\n- Use Route 80"
        self.assertEqual(normalize_source_structure(source), source)


class TranslationValidatorTests(unittest.TestCase):
    def test_reports_exact_unexpected_latin_tokens(self):
        self.assertEqual(
            find_unexpected_latin_tokens(
                "Bessent spoke to Reuters.",
                "贝森特向Reuters发表讲话。",
            ),
            ("Reuters",),
        )

    def test_requires_longest_non_overlapping_glossary_term(self):
        glossary = {"Scott Bessent": "斯科特·贝森特", "Bessent": "贝森特"}
        self.assertEqual(
            find_missing_glossary_terms(
                "Scott Bessent spoke. Bessent continued.",
                "斯科特·贝森特发表讲话。Bessent继续说道。",
                glossary,
            ),
            ("Bessent => 贝森特",),
        )

    def test_glossary_terms_require_token_boundaries(self):
        self.assertEqual(
            find_missing_glossary_terms(
                "The US criticized RUSSIA.",
                "美国批评了俄罗斯。",
                {"US": "美国"},
            ),
            (),
        )
        self.assertEqual(
            find_missing_glossary_terms(
                "Iranian officials spoke.",
                "伊朗官员发表了讲话。",
                {"Iran": "伊朗"},
            ),
            (),
        )

    def test_detects_empty_and_structure_loss(self):
        self.assertEqual(
            validate_translation("Title\nBody.", "", "zh"),
            ["EMPTY_OUTPUT"],
        )
        errors = validate_translation(
            "Title\nBody.\n\nNext paragraph.",
            "标题正文。",
            "zh",
        )
        self.assertIn("PARAGRAPH_COUNT_MISMATCH", errors)
        self.assertIn("LINE_STRUCTURE_LOSS", errors)
        self.assertIn("SENTENCE_COUNT_LOSS", errors)

    def test_detects_numbers_and_english_residual(self):
        source = (
            "Six people were injured; "
            "12 homes and 3.5% of land were affected."
        )
        output = "据 authorities 称，五人受伤；13所房屋和3.5%的土地受到影响。"
        errors = validate_translation(source, output, "zh")
        self.assertIn("ARABIC_NUMBER_MISMATCH", errors)
        self.assertIn("ENGLISH_NUMBER_MISMATCH", errors)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_accepts_chinese_numbers_and_protected_spans(self):
        source = "Six users opened https://example.com and `/opt/app/run.sh`."
        output = "六名用户打开了 https://example.com 和 `/opt/app/run.sh`。"
        self.assertEqual(validate_translation(source, output, "zh"), [])

    def test_accepts_arabic_numbers_rendered_as_equivalent_chinese_numbers(self):
        source = (
            "Freeman was sentenced to 18 months probation, "
            "240 hours of unpaid work, and a 12-month restriction."
        )
        output = (
            "弗里曼被判处十八个月缓刑、二百四十小时无偿劳动，"
            "并受到十二个月的人身自由限制。"
        )
        self.assertNotIn(
            "ARABIC_NUMBER_MISMATCH",
            validate_translation(source, output, "zh"),
        )

    def test_accepts_source_acronym_preserved_in_chinese_translation(self):
        source = "The victims told BBC Scotland News about the abuse."
        output = "受害者向BBC苏格兰新闻讲述了遭受虐待的经历。"
        self.assertNotIn(
            "TARGET_SCRIPT_RESIDUAL",
            validate_translation(source, output, "zh"),
        )

    def test_accepts_digit_bearing_news_acronyms_from_source(self):
        for acronym in ("G7", "G20", "COP28", "F-16"):
            with self.subTest(acronym=acronym):
                source = f"The {acronym} met today."
                output = f"{acronym}今天举行会议。"
                self.assertNotIn(
                    "TARGET_SCRIPT_RESIDUAL",
                    validate_translation(source, output, "zh"),
                )

    def test_rejects_ordinary_uppercase_headline_words(self):
        source = "BREAKING NEWS: Talks began."
        output = "BREAKING NEWS：会谈开始。"
        self.assertIn(
            "TARGET_SCRIPT_RESIDUAL",
            validate_translation(source, output, "zh"),
        )

    def test_rejects_extra_chinese_number(self):
        self.assertIn(
            "ARABIC_NUMBER_MISMATCH",
            validate_translation(
                "18 people attended.",
                "十八人参加，另有二十人。",
                "zh",
            ),
        )

    def test_accepts_non_quantity_chinese_numeral_idioms(self):
        cases = (
            ("Please do not leave.", "千万不要离开。"),
            ("They responded individually.", "他们一一回应。"),
        )
        for source, output in cases:
            with self.subTest(output=output):
                self.assertNotIn(
                    "ARABIC_NUMBER_MISMATCH",
                    validate_translation(source, output, "zh"),
                )

    def test_accepts_chinese_decimal_equivalent(self):
        self.assertEqual(
            validate_translation(
                "3.5% attended.",
                "百分之三点五的人参加。",
                "zh",
            ),
            [],
        )

    def test_accepts_complete_house_of_terror_article_translation(self):
        source = (
            'A mother, grandmother and stepfather subjected three children to years of abuse.\n\n'
            'Freeman, 51, and Stephen, 69, were found guilty. McColl, 50, admitted the crimes.\n\n'
            'Freeman received 18 months probation, 240 hours of unpaid work, and a 12-month restriction.\n\n'
            'Stephen received 150 hours of unpaid work and 18 months probation.\n\n'
            'McColl received 220 hours of unpaid work, 18 months probation, and an 11-month restriction.\n\n'
            'The victims, now 25 and 28, told BBC Scotland News about the abuse.'
        )
        output = (
            '一名母亲、祖母和继父对三名儿童实施了多年的虐待。\n\n'
            '弗里曼现年五十一岁，斯蒂芬六十九岁，两人被判有罪；五十岁的麦科尔承认犯罪。\n\n'
            '弗里曼被判十八个月缓刑、二百四十小时无偿劳动，并受到十二个月的人身自由限制。\n\n'
            '斯蒂芬被判完成一百五十小时无偿劳动，并接受十八个月缓刑。\n\n'
            '麦科尔被判完成二百二十小时无偿劳动、接受十八个月缓刑，并受到十一个月的人身自由限制。\n\n'
            '两名受害者现年二十五岁和二十八岁，他们向BBC苏格兰新闻讲述了受虐经历。'
        )
        errors = validate_translation(source, output, "zh")
        self.assertNotIn("ARABIC_NUMBER_MISMATCH", errors)
        self.assertNotIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_tens_of_thousands_requires_equivalent_quantity(self):
        source = "Tens of thousands of people evacuated."
        self.assertIn(
            "ENGLISH_NUMBER_MISMATCH",
            validate_translation(source, "数千人撤离。", "zh"),
        )
        self.assertEqual(
            validate_translation(source, "数以万计的人撤离。", "zh"),
            [],
        )

    def test_hundreds_of_thousands_requires_equivalent_quantity(self):
        source = "Hundreds of thousands of people evacuated."
        self.assertEqual(
            validate_translation(source, "数十万人撤离。", "zh"),
            [],
        )

if __name__ == "__main__":
    unittest.main()
