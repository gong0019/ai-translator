"""Scientific-text notation must survive the residue check.

Medical abstracts leave acronyms, statistical notation, units, and registry IDs
in Latin script on purpose. Before these rules existed, one Lancet abstract
reported seven residue tokens, every one of them correct as translated.
"""

import unittest

from translation_quality import find_unexpected_latin_tokens, validate_translation


SOURCE = (
    "Robotic-arm-assisted versus conventional total knee replacement "
    "(RACER-Knee): patients received cTKR or rTKR. "
    "The trial is registered with ISRCTN (ISRCTN27624068) and ClinicalTrials.gov "
    "(NCT04649489). Response was assessed per RECIST 1.1. "
    "Patients received atezolizumab 1200 mg every 3 weeks and bevacizumab "
    "15 mg/kg. The adjusted difference was -1.5 (95% CI -7.5 to 4.5; p=0.62; "
    "n=154). Vaccination used rVSVΔG-ZEBOV-GP."
)


class ScientificNotationTests(unittest.TestCase):
    def test_a_faithful_translation_reports_no_residue(self):
        output = (
            "机器人手臂辅助与传统全膝置换术（RACER-Knee）：患者接受 cTKR 或 rTKR。"
            "该试验已在 ISRCTN（ISRCTN27624068）和 ClinicalTrials.gov（NCT04649489）注册。"
            "疗效按 RECIST 1.1 评估。"
            "患者每 3 周接受阿替利珠单抗 1200 mg 与贝伐珠单抗 15 mg/kg。"
            "调整后差异为 -1.5（95% CI -7.5 至 4.5；p=0.62；n=154）。"
            "疫苗为 rVSVΔG-ZEBOV-GP。"
        )
        self.assertEqual(find_unexpected_latin_tokens(SOURCE, output), ())

    def test_normalized_decimal_marks_do_not_count_as_residue(self):
        # 柳叶刀原文用中点小数，模型规范成句点是正确的，不该判为未翻译。
        self.assertEqual(
            find_unexpected_latin_tokens(
                "Seroreactivity differed (p<0·0001).", "血清反应性存在差异（p<0.0001）。"
            ),
            (),
        )

    def test_an_untranslated_word_is_still_reported(self):
        output = "患者具有 macrovascular 浸润，按 RECIST 1.1 评估。"
        self.assertIn(
            "macrovascular",
            find_unexpected_latin_tokens(SOURCE, output),
        )
        self.assertIn(
            "TARGET_SCRIPT_RESIDUAL",
            validate_translation(SOURCE, output, "zh"),
        )

    def test_a_misspelled_acronym_is_not_treated_as_a_source_acronym(self):
        self.assertIn(
            "ctKR",
            find_unexpected_latin_tokens(SOURCE, "患者接受 ctKR 治疗。"),
        )

    def test_an_embedded_acronym_does_not_hollow_out_a_longer_one(self):
        # 裸 str.replace 会把 RECIST 里的 CI 挖掉，留下 "RE" 和 "ST"。
        residue = find_unexpected_latin_tokens(SOURCE, "疗效按 RECIST 1.1 评估。")
        self.assertNotIn("RE", residue)
        self.assertNotIn("ST", residue)



class NumericConventionTests(unittest.TestCase):
    def test_middle_dot_decimals_normalize_to_a_single_number(self):
        # 柳叶刀用 18·4 写小数；模型规范成 18.4 是正确的。
        self.assertEqual(
            validate_translation(
                "Median follow-up was 18·4 months (IQR 61·3-75·2).",
                "中位随访时间为18.4个月（IQR 61.3-75.2）。",
                "zh",
            ),
            [],
        )

    def test_month_names_and_month_numbers_are_the_same_quantity(self):
        self.assertEqual(
            validate_translation(
                "The cohort enrolled on August 15, 2018.",
                "该队列于2018年8月15日入组。",
                "zh",
            ),
            [],
        )
        self.assertEqual(
            validate_translation(
                "该队列于2018年8月15日入组。",
                "The cohort enrolled on August 15, 2018.",
                "en",
            ),
            [],
        )

    def test_a_duration_in_months_is_not_read_as_a_month_name(self):
        self.assertEqual(
            validate_translation(
                "Follow-up lasted 12 months.", "随访持续12个月。", "zh"
            ),
            [],
        )

    def test_liang_is_accepted_as_the_measure_word_form_of_two(self):
        for output in ("两组的安全性相似。", "二组的安全性相似。"):
            with self.subTest(output=output):
                self.assertEqual(
                    validate_translation(
                        "The two groups had similar safety.", output, "zh"
                    ),
                    [],
                )

    def test_a_spelled_number_never_consumes_a_decimal_digit(self):
        # "two" 不得吃掉 75.2 的小数位，否则会留下 75. 并凭空多出一个数字。
        self.assertEqual(
            validate_translation(
                "The two groups had a median age of 75.2 years.",
                "两组的中位年龄为75.2岁。",
                "zh",
            ),
            [],
        )

if __name__ == "__main__":
    unittest.main()
