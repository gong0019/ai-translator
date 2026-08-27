import unittest
from unittest.mock import patch

from translation_quality import (
    CompletionResult,
    normalize_quality_settings,
    run_quality_checked_completion,
)
import translator_cli


class QualityRetryTests(unittest.TestCase):
    def test_retry_prompt_describes_non_lexical_defects_without_internal_codes(self):
        cases = (
            (
                "empty",
                "Six people attended.",
                CompletionResult(""),
                CompletionResult("六人参加。"),
                "Provide a complete translation; the current translation is empty.",
            ),
            (
                "structure",
                "One.\n\nTwo.",
                CompletionResult("一。二。"),
                CompletionResult("一。\n\n二。"),
                "Preserve all source paragraphs in the same order.",
            ),
            (
                "numeric",
                "18 people attended.",
                CompletionResult("二十人参加。"),
                CompletionResult("十八人参加。"),
                "Preserve every source number exactly and do not add numbers.",
            ),
            (
                "truncation",
                "Six people attended.",
                CompletionResult("六人参加。", truncated=True),
                CompletionResult("六人参加。"),
                "Complete the translation; the previous output was truncated.",
            ),
        )
        internal_codes = (
            "EMPTY_OUTPUT",
            "PARAGRAPH_COUNT_MISMATCH",
            "LINE_STRUCTURE_LOSS",
            "SENTENCE_COUNT_LOSS",
            "ARABIC_NUMBER_MISMATCH",
            "SPELLED_NUMBER_MISMATCH",
            "OUTPUT_TRUNCATED",
        )
        for name, source, first, second, expected_instruction in cases:
            with self.subTest(name=name):
                outputs = iter((first, second))
                calls = []

                def complete(messages, temperature):
                    calls.append((messages, temperature))
                    return next(outputs)

                run_quality_checked_completion(
                    source,
                    "zh",
                    "SYSTEM",
                    complete,
                    0.1,
                    1,
                )

                repair_request = calls[1][0][-1]["content"]
                self.assertIn(expected_instruction, repair_request)
                for code in internal_codes:
                    self.assertNotIn(code, repair_request)

    def test_persistent_non_lexical_defects_have_concrete_chinese_review_notes(self):
        cases = (
            (
                "glossary",
                "Reuters reported.",
                CompletionResult("路透报道。"),
                {"Reuters": "路透社"},
                ("可能未使用指定术语：Reuters => 路透社",),
            ),
            (
                "numeric",
                "18 people attended.",
                CompletionResult("二十人参加。"),
                None,
                ("可能存在数字不一致，请人工检查。",),
            ),
            (
                "structure",
                "One.\n\nTwo.",
                CompletionResult("一。二。"),
                None,
                ("可能存在结构或内容缺失，请人工检查。",),
            ),
            (
                "truncation",
                "Six people attended.",
                CompletionResult("六人参加。", truncated=True),
                None,
                ("译文可能被截断，请人工检查。",),
            ),
        )
        for name, source, failed_result, glossary, expected_notes in cases:
            with self.subTest(name=name):
                calls = []

                def complete(messages, temperature):
                    calls.append((messages, temperature))
                    return failed_result

                outcome = run_quality_checked_completion(
                    source,
                    "zh",
                    "SYSTEM",
                    complete,
                    0.1,
                    1,
                    glossary=glossary,
                )

                self.assertEqual(len(calls), 2)
                self.assertEqual(outcome.review_notes, expected_notes)
                self.assertFalse(
                    any(note in outcome.errors for note in outcome.review_notes)
                )

    def test_retry_prompt_names_concrete_defects_and_includes_glossary(self):
        outputs = iter(
            (
                CompletionResult("贝森特向Reuters发表讲话。"),
                CompletionResult("贝森特向路透社发表讲话。"),
            )
        )
        calls = []

        def complete(messages, temperature):
            calls.append((messages, temperature))
            return next(outputs)

        outcome = run_quality_checked_completion(
            "Bessent spoke to Reuters.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
            glossary={"Reuters": "路透社"},
        )

        repair_request = calls[1][0][-1]["content"]
        self.assertEqual(outcome.text, "贝森特向路透社发表讲话。")
        self.assertIn("Translate this remaining source token: Reuters", repair_request)
        self.assertIn("DOCUMENT GLOSSARY:\n- Reuters => 路透社", repair_request)
        self.assertNotIn("TARGET_SCRIPT_RESIDUAL", repair_request)
        self.assertEqual(len(calls), 2)

    def test_failed_repair_preserves_text_and_reports_concrete_review_note(self):
        calls = []

        def complete(messages, temperature):
            calls.append((messages, temperature))
            return CompletionResult("贝森特向Reuters发表讲话。")

        outcome = run_quality_checked_completion(
            "Bessent spoke to Reuters.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
            glossary={"Reuters": "路透社"},
        )

        self.assertEqual(outcome.text, "贝森特向Reuters发表讲话。")
        self.assertEqual(outcome.review_notes, ("可能仍有未翻译内容：Reuters",))
        self.assertEqual(len(calls), 2)

    def test_valid_output_is_returned_without_retry(self):
        calls = []

        def complete(messages, temperature):
            calls.append((messages, temperature))
            return CompletionResult("六人受伤。")

        result = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
        )
        self.assertEqual(result.text, "六人受伤。")
        self.assertFalse(result.retried)
        self.assertEqual(len(calls), 1)

    def test_invalid_output_retries_once_at_zero_temperature(self):
        outputs = iter(
            (
                CompletionResult("Six people受伤。"),
                CompletionResult("六人受伤。"),
            )
        )
        calls = []

        def complete(messages, temperature):
            calls.append((messages, temperature))
            return next(outputs)

        result = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
        )
        self.assertEqual(result.text, "六人受伤。")
        self.assertTrue(result.retried)
        self.assertEqual([item[1] for item in calls], [0.1, 0.0])
        self.assertIn(
            "Translate this remaining source token: Six",
            calls[1][0][-1]["content"],
        )
        self.assertNotIn("TARGET_SCRIPT_RESIDUAL", calls[1][0][-1]["content"])

    def test_second_failure_is_returned_without_third_call(self):
        calls = []

        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult("authorities称Six people受伤。")

        result = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
        )
        self.assertEqual(len(calls), 2)
        self.assertTrue(result.errors)

    def test_retries_a_chunk_that_copies_too_much_of_the_previous_translation(self):
        outputs = iter(
            (
                CompletionResult("上一段新闻称六人受伤，火势仍在蔓延。"),
                CompletionResult("第二段说明，当局正在调查事故原因。"),
            )
        )
        calls = []

        outcome = run_quality_checked_completion(
            "Authorities are investigating the cause.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: (calls.append(temperature), next(outputs))[1],
            0.1,
            1,
            previous_output="上一段新闻称六人受伤，火势仍在蔓延。",
        )

        self.assertEqual(outcome.text, "第二段说明，当局正在调查事故原因。")
        self.assertEqual(calls, [0.1, 0.0])

    def test_truncation_forces_retry(self):
        outputs = iter(
            (
                CompletionResult("六人", truncated=True),
                CompletionResult("六人受伤。"),
            )
        )
        result = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: next(outputs),
            0.1,
            1,
        )
        self.assertTrue(result.retried)
        self.assertEqual(result.errors, ())

    def test_disabled_validation_returns_first_result(self):
        calls = []

        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult("Six people受伤。")

        result = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
            validation_enabled=False,
        )
        self.assertEqual(result.text, "Six people受伤。")
        self.assertEqual(len(calls), 1)

    def test_validator_exception_preserves_output_without_retry(self):
        calls = []

        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult("六人受伤。")

        with patch(
            "translation_quality.validate_translation",
            side_effect=RuntimeError("broken validator"),
        ):
            result = run_quality_checked_completion(
                "Six people were injured.",
                "zh",
                "SYSTEM",
                complete,
                0.1,
                1,
            )
        self.assertEqual(result.text, "六人受伤。")
        self.assertEqual(result.errors, ("VALIDATOR_ERROR",))
        self.assertFalse(result.retried)
        self.assertEqual(len(calls), 1)

    def test_quality_settings_accept_only_json_boolean_and_zero_or_one_integer(self):
        cases = (
            ((True, 1), (True, 1)),
            ((False, 0), (False, 0)),
            ((None, None), (True, 1)),
            (("false", "0"), (True, 1)),
            ((1, True), (True, 1)),
            ((True, 2), (True, 1)),
        )
        for inputs, expected in cases:
            with self.subTest(inputs=inputs):
                self.assertEqual(normalize_quality_settings(*inputs), expected)



class AdaptiveRetryPolicyTests(unittest.TestCase):
    """吸收自 cbbd989，错误码已随重命名同步。"""

    def test_fast_document_filter_does_not_retry_noncritical_residual_text(self):
        calls = []
        result = run_quality_checked_completion(
            "The Lancet published the article.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: (
                calls.append(temperature),
                CompletionResult("《柳叶刀》发表了The Lancet文章。"),
            )[1],
            0.1,
            1,
            retryable_errors={"ARABIC_NUMBER_MISMATCH"},
        )
        self.assertEqual(result.text, "《柳叶刀》发表了The Lancet文章。")
        self.assertFalse(result.retried)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", result.errors)
        self.assertEqual(calls, [0.1])

    def test_fast_document_filter_still_retries_changed_numbers(self):
        outputs = iter((CompletionResult("二十人参加。"), CompletionResult("十八人参加。")))
        calls = []
        result = run_quality_checked_completion(
            "18 people attended.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: (calls.append(temperature), next(outputs))[1],
            0.1,
            1,
            retryable_errors={"ARABIC_NUMBER_MISMATCH", "SPELLED_NUMBER_MISMATCH"},
        )
        self.assertEqual(result.text, "十八人参加。")
        self.assertTrue(result.retried)
        self.assertEqual(calls, [0.1, 0.0])

    def test_adaptive_policy_only_uses_fast_mode_for_long_documents(self):
        config = {"adaptive_quality_mode": True, "adaptive_quality_min_chunks": 5}
        self.assertIsNone(translator_cli.retryable_errors_for_document(config, 4))
        self.assertEqual(
            translator_cli.retryable_errors_for_document(config, 5),
            translator_cli.FAST_DOCUMENT_RETRY_ERRORS,
        )
        self.assertIsNone(
            translator_cli.retryable_errors_for_document(
                {"adaptive_quality_mode": False}, 99
            )
        )

    def test_the_renamed_number_code_is_still_retryable(self):
        # 改名后若忘记同步，这条过滤规则会静默失效：数字被改不再触发重译。
        self.assertIn(
            "SPELLED_NUMBER_MISMATCH", translator_cli.FAST_DOCUMENT_RETRY_ERRORS
        )
        self.assertNotIn(
            "ENGLISH_NUMBER_MISMATCH", translator_cli.FAST_DOCUMENT_RETRY_ERRORS
        )

if __name__ == "__main__":
    unittest.main()
