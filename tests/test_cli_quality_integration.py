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
                (
                    '{"Nevada":"内华达州","Reno":"里诺"}',
                    "stop",
                ),
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
        # 标题行与正文行各自成为一个翻译单元，模型无法只翻标题就交差。
        self.assertEqual(len(cli.llm.calls), 3)
        self.assertEqual(
            cli.llm.calls[1]["messages"][1]["content"],
            "'Scared to death': Thousands evacuate Nevada homes as wildfire spreads",
        )
        self.assertTrue(
            cli.llm.calls[2]["messages"][1]["content"].startswith("Tens of thousands")
        )
        # 同一段落内的两行仍以换行而非空行相连。
        self.assertIn(
            "内华达州家园\n美国内华达州数以万计",
            rendered,
        )

    def test_stream_translate_displays_second_attempt_without_internal_errors(self):
        cli = self.make_cli(
            (
                ("首次错误译文：Six people受伤。", "stop"),
                ("最终译文：六人受伤，people在场。", "stop"),
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate("Six people were injured.")
        rendered = output.getvalue()
        self.assertNotIn("首次错误译文", rendered)
        self.assertIn("最终译文：六人受伤，people在场。", rendered)
        self.assertNotIn("翻译单元未通过质量校验", rendered)
        self.assertNotIn("TARGET_SCRIPT_RESIDUAL", rendered)
        self.assertNotIn("SPELLED_NUMBER_MISMATCH", rendered)
        self.assertNotIn("可能仍有未翻译内容", rendered)
        self.assertNotIn("可能存在结构或内容缺失", rendered)
        self.assertNotIn("可能存在数字不一致", rendered)
        self.assertEqual(len(cli.llm.calls), 2)

    def test_multi_paragraph_document_uses_one_glossary_and_per_paragraph_requests(self):
        cli = self.make_cli(
            (
                ('{"Scott Bessent":"斯科特·贝森特","Bessent":"贝森特"}', "stop"),
                ("斯科特·贝森特发表讲话。", "stop"),
                (
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
        self.assertEqual(len(cli.llm.calls), 3)
        self.assertIn(
            "en_to_zh",
            cli.llm.calls[0]["messages"][0]["content"],
        )
        translation_call = cli.llm.calls[1]
        self.assertEqual(
            translation_call["messages"][1]["content"],
            "Scott Bessent made the comments.",
        )
        self.assertIn(
            "- Bessent => 贝森特",
            translation_call["messages"][0]["content"],
        )
        # 术语表只规划一次，但每个单元只注入本单元命中的条目：
        # Reuters 只出现在第二段，不该塞进第一段的提示词。
        self.assertNotIn(
            "- Reuters => 路透社",
            translation_call["messages"][0]["content"],
        )
        self.assertIn(
            "- Reuters => 路透社",
            cli.llm.calls[2]["messages"][0]["content"],
        )
        self.assertEqual(
            cli.llm.calls[2]["messages"][1]["content"],
            "Bessent later spoke to Reuters.",
        )
        self.assertNotIn(
            "PREVIOUS CONFIRMED TRANSLATION",
            cli.llm.calls[2]["messages"][0]["content"],
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
            for call in cli.llm.calls
        ]
        self.assertEqual(translated_sources.count("First paragraph."), 1)
        self.assertEqual(len(cli.llm.calls), 3)

    def test_next_paragraph_carries_one_labelled_sentence_of_context(self):
        cli = self.make_cli(
            (
                ("路透社发布了报告。该报告长达百页。", "stop"),
                ("该机构补充了更多细节。", "stop"),
            )
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.stream_translate(
                "Reuters published the report. It ran to a hundred pages."
                "\n\nThe agency added more detail."
            )

        self.assertIn("路透社发布了报告。该报告长达百页。", output.getvalue())
        self.assertIn("该机构补充了更多细节。", output.getvalue())

        first_prompt = cli.llm.calls[0]["messages"][0]["content"]
        second_prompt = cli.llm.calls[1]["messages"][0]["content"]
        # 第一段没有前文可带。
        self.assertNotIn("PRECEDING CONTEXT", first_prompt)
        # 术语只注入命中它的单元：Reuters 在第一段，不在第二段。
        self.assertIn("- Reuters => 路透社", first_prompt)
        self.assertNotIn("DOCUMENT GLOSSARY", second_prompt)
        # 只带最后一句，且明确标注为已翻译、不得重译。
        self.assertIn("PRECEDING CONTEXT", second_prompt)
        self.assertIn("Do not translate or repeat it.", second_prompt)
        self.assertIn("- translation: 该报告长达百页。", second_prompt)
        self.assertNotIn("路透社发布了报告。", second_prompt)
        self.assertNotIn("Reuters published the report.", second_prompt)

    def test_multi_paragraph_translation_shows_progress_while_next_chunk_runs(self):
        cli = self.make_cli(
            (
                ("第一段。", "stop"),
                ("第二段。", "stop"),
            )
        )
        with patch("translator_cli.console.status") as status:
            with contextlib.redirect_stdout(io.StringIO()):
                cli.stream_translate("First paragraph.\n\nSecond paragraph.")

        self.assertEqual(status.call_count, 2)
        self.assertIn("第 1/2 段", status.call_args_list[0].args[0])
        self.assertIn("第 2/2 段", status.call_args_list[1].args[0])

    def test_specialist_glossaries_match_lowercase_terms_and_skip_ambiguous_blockchain_words(self):
        cli = self.make_cli(())
        finance, _ = cli._build_document_glossary(
            "Inflation rose after quantitative easing.",
            "en_to_zh",
        )
        ordinary_wallet, _ = cli._build_document_glossary(
            "The stolen wallet was returned to its owner.",
            "en_to_zh",
        )
        crypto_wallet, _ = cli._build_document_glossary(
            "The Bitcoin wallet uses a smart contract.",
            "en_to_zh",
        )

        self.assertEqual(finance["inflation"], "通货膨胀")
        self.assertEqual(finance["quantitative easing"], "量化宽松")
        self.assertNotIn("wallet", ordinary_wallet)
        self.assertEqual(crypto_wallet["wallet"], "钱包")
        self.assertEqual(cli.llm.calls, [])

    def test_hardware_and_material_glossaries_require_domain_context(self):
        cli = self.make_cli(())
        ordinary_water, _ = cli._build_document_glossary(
            "The city upgraded its water system after the storm.",
            "en_to_zh",
        )
        hardware, _ = cli._build_document_glossary(
            "The GPU uses water cooling on a printed circuit board.",
            "en_to_zh",
        )
        materials, _ = cli._build_document_glossary(
            "The packaging supplier selected polypropylene and polyethylene film.",
            "en_to_zh",
        )

        self.assertNotIn("water cooling", ordinary_water)
        self.assertEqual(hardware["water cooling"], "水冷")
        self.assertEqual(hardware["printed circuit board"], "印制电路板")
        self.assertEqual(materials["polypropylene"], "聚丙烯（PP）")
        self.assertEqual(materials["polyethylene"], "聚乙烯（PE）")
        self.assertEqual(cli.llm.calls, [])

    def test_cross_border_and_trade_glossaries_require_domain_context(self):
        cli = self.make_cli(())
        ordinary_order, _ = cli._build_document_glossary(
            "The court issued an order after the hearing.",
            "en_to_zh",
        )
        commerce, _ = cli._build_document_glossary(
            "The Amazon seller completed order fulfillment and issued a refund.",
            "en_to_zh",
        )
        trade, _ = cli._build_document_glossary(
            "The bill of lading lists FOB terms and a customs declaration.",
            "en_to_zh",
        )

        self.assertNotIn("order fulfillment", ordinary_order)
        self.assertEqual(commerce["order fulfillment"], "订单履约")
        self.assertEqual(commerce["refund"], "退款")
        self.assertEqual(trade["bill of lading"], "提单")
        self.assertEqual(trade["FOB"], "船上交货（FOB）")
        self.assertEqual(cli.llm.calls, [])


if __name__ == "__main__":
    unittest.main()


class LiveOutputTests(CLIQualityIntegrationTests):
    class TokenStub:
        def __init__(self, pieces):
            self.pieces = pieces
            self.calls = []

        def tokenize(self, data, add_bos=False):
            return [0] * (len(data) // 3)

        def create_chat_completion(self, **kwargs):
            self.calls.append(kwargs)

            def chunks():
                for piece in self.pieces:
                    yield {
                        "choices": [
                            {"delta": {"content": piece}, "finish_reason": None}
                        ]
                    }
                yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}

            return chunks()

    def writes_for(self, source):
        cli = self.make_cli(())
        cli.llm = self.TokenStub(("变压器", "短缺", "成为瓶颈。"))
        recorded = []

        class Recorder(io.StringIO):
            def write(self, value):
                if value.strip():
                    recorded.append(value)
                return super().write(value)

        with contextlib.redirect_stdout(Recorder()):
            cli.stream_translate(source)
        return [value for value in recorded if "变压器" in value or "短缺" in value]

    def test_a_unit_too_large_to_repair_is_shown_as_it_arrives(self):
        long_source = " ".join(["Transformer lead times keep growing."] * 200)
        self.assertGreater(len(self.writes_for(long_source)), 1)

    def test_a_repairable_unit_is_still_withheld_until_validated(self):
        # 可能被重译替换的译文不得提前显示。
        self.assertEqual(len(self.writes_for("Lead times keep growing.")), 1)
