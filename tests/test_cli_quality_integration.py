import contextlib
import io
import threading
import unittest
from unittest.mock import patch

from translator_cli import TranslatorCLI


class FakeLlama:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        text, finish_reason = next(self.responses)

        def chunks():
            yield {
                "choices": [
                    {"delta": {"content": text}, "finish_reason": None}
                ]
            }
            yield {
                "choices": [
                    {"delta": {}, "finish_reason": finish_reason}
                ]
            }

        return chunks()


class CLIQualityIntegrationTests(unittest.TestCase):
    def make_cli(self, responses):
        cli = object.__new__(TranslatorCLI)
        cli.config = {
            "target_lang_key": "1",
            "temperature": 0.1,
            "repeat_penalty": 1.08,
            "max_tokens": 4096,
            "quality_validation": True,
            "quality_retry_limit": 1,
            "idle_timeout": 60,
            "n_ctx": 8192,
        }
        cli.lock = threading.Lock()
        cli.is_busy = False
        cli.last_active_time = 0.0
        cli.llm = FakeLlama(responses)
        return cli

    def test_collect_completion_marks_length_finish_as_truncated(self):
        cli = self.make_cli((("六人", "length"),))
        result = cli._collect_completion([], 0.1, 1.08, 5)
        self.assertEqual(result.text, "六人")
        self.assertTrue(result.truncated)
        self.assertTrue(cli.llm.calls[0]["stream"])

    def test_stream_translate_never_prints_rejected_first_attempt(self):
        cli = self.make_cli(
            (
                ('{"Six":"六"}', "stop"),
                ("Six people受伤。", "stop"),
                ("六人受伤。", "stop"),
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate("Six people were injured.")
        rendered = output.getvalue()
        self.assertNotIn("Six people受伤。", rendered)
        self.assertIn("六人受伤。", rendered)
        self.assertEqual(len(cli.llm.calls), 3)
        self.assertEqual(cli.llm.calls[2]["temperature"], 0.0)

    def test_stream_translate_translates_headline_and_body_as_separate_units(self):
        cli = self.make_cli(
            (
                (
                    '{"Nevada":"内华达州","Reno":"里诺"}',
                    "stop",
                ),
                (
                    "“惊恐万分”：野火蔓延，数千人撤离内华达州家园\n"
                    "美国内华达州数以万计的居民被要求撤离家园，"
                    "因为一场野火逼近里诺市。",
                    "stop",
                ),
            )
        )
        source = (
            "'Scared to death': Thousands evacuate Nevada homes as wildfire spreads\n"
            "Tens of thousands of people in Nevada were told to evacuate "
            "as a wildfire approached Reno."
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate(source)
        rendered = output.getvalue()
        self.assertIn("“惊恐万分”：野火蔓延，数千人撤离内华达州家园", rendered)
        self.assertIn("数以万计", rendered)
        self.assertNotIn("质量校验未完全通过", rendered)
        self.assertEqual(len(cli.llm.calls), 2)

    def test_stream_translate_displays_second_attempt_without_internal_errors(self):
        cli = self.make_cli(
            (
                ('{"Six":"六"}', "stop"),
                ("首次错误译文：Six people受伤。", "stop"),
                ("最终译文：authorities称Six people受伤。", "stop"),
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate("Six people were injured.")
        rendered = output.getvalue()
        self.assertNotIn("首次错误译文", rendered)
        self.assertIn("最终译文：authorities称Six people受伤。", rendered)
        self.assertNotIn("翻译单元未通过质量校验", rendered)
        self.assertNotIn("TARGET_SCRIPT_RESIDUAL", rendered)
        self.assertNotIn("ENGLISH_NUMBER_MISMATCH", rendered)
        self.assertEqual(len(cli.llm.calls), 3)

    def test_short_document_uses_one_glossary_and_one_translation_request(self):
        cli = self.make_cli(
            (
                ('{"Scott Bessent":"斯科特·贝森特","Bessent":"贝森特"}', "stop"),
                (
                    "斯科特·贝森特发表讲话。\n\n"
                    "贝森特随后接受路透社采访。",
                    "stop",
                ),
            )
        )
        source = (
            "Scott Bessent made the comments.\n\n"
            "Bessent later spoke to Reuters."
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate(source)
        rendered = output.getvalue()
        self.assertIn("斯科特·贝森特发表讲话。", rendered)
        self.assertIn("贝森特随后接受路透社采访。", rendered)
        self.assertEqual(len(cli.llm.calls), 2)
        translation_call = cli.llm.calls[1]
        self.assertEqual(translation_call["messages"][1]["content"], source)
        self.assertIn(
            "- Reuters => 路透社",
            translation_call["messages"][0]["content"],
        )
        self.assertIn(
            "- Bessent => 贝森特",
            translation_call["messages"][0]["content"],
        )

    def test_declining_truncated_input_skips_all_model_calls(self):
        cli = self.make_cli(())
        output = io.StringIO()
        with patch.object(cli, "_confirm_truncated_input", return_value=False):
            with contextlib.redirect_stdout(output):
                cli.stream_translate("Voters ahead of th")
        self.assertEqual(cli.llm.calls, [])
        self.assertIn("输入末尾疑似不完整，已取消翻译。", output.getvalue())

    def test_only_defective_document_chunk_is_retried(self):
        cli = self.make_cli(
            (
                ('{"First":"第一"}', "stop"),
                ("第一段。", "stop"),
                ("Reuters报道。", "stop"),
                ("路透社报道。", "stop"),
            )
        )
        source = "First paragraph.\n\nReuters reported."
        output = io.StringIO()
        with patch(
            "translator_cli.plan_paragraph_chunks",
            return_value=["First paragraph.", "Reuters reported."],
        ):
            with contextlib.redirect_stdout(output):
                cli.stream_translate(source)
        rendered = output.getvalue()
        self.assertIn("第一段。", rendered)
        self.assertIn("路透社报道。", rendered)
        self.assertNotIn("Reuters报道。", rendered)
        translated_sources = [
            call["messages"][1]["content"]
            for call in cli.llm.calls[1:]
        ]
        self.assertEqual(translated_sources.count("First paragraph."), 1)
        self.assertEqual(len(cli.llm.calls), 4)


if __name__ == "__main__":
    unittest.main()
