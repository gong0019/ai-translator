import contextlib
import io
import threading
import unittest

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
        self.assertEqual(len(cli.llm.calls), 2)
        self.assertEqual(cli.llm.calls[1]["temperature"], 0.0)

    def test_stream_translate_translates_headline_and_body_as_separate_units(self):
        cli = self.make_cli(
            (
                ("“惊恐万分”：野火蔓延，数千人撤离内华达州家园", "stop"),
                (
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

    def test_stream_translate_never_prints_second_failed_attempt(self):
        cli = self.make_cli(
            (
                ("Six people受伤。", "stop"),
                ("authorities称Six people受伤。", "stop"),
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate("Six people were injured.")
        rendered = output.getvalue()
        self.assertNotIn("Six people受伤。", rendered)
        self.assertNotIn("authorities称Six people受伤。", rendered)
        self.assertIn("翻译单元未通过质量校验", rendered)
        self.assertEqual(len(cli.llm.calls), 2)


if __name__ == "__main__":
    unittest.main()
