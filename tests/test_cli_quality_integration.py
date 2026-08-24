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


if __name__ == "__main__":
    unittest.main()
