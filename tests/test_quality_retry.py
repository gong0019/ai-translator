import unittest
from unittest.mock import patch

from translation_quality import (
    CompletionResult,
    normalize_quality_settings,
    run_quality_checked_completion,
)


class QualityRetryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
