"""Regression tests for the AI-education article that lost a whole paragraph.

The observed failure chained three defects: sentence-initial words such as
``Only`` became mandatory glossary terms, the resulting false "missing term"
forced a repair, and the repair prompt — fed to a translation-only model — was
translated instead of obeyed and then overwrote a correct paragraph.
"""

import unittest

from document_translation import extract_term_candidates
from translation_quality import (
    CompletionResult,
    find_missing_glossary_terms,
    normalize_source_structure,
    run_quality_checked_completion,
    validate_translation,
)


ARTICLE = """The Impact of Artificial Intelligence on Education
In recent years, artificial intelligence (AI) has emerged as a transformative force in various sectors, with education being one of the most significantly affected fields.

Proponents argue that AI revolutionizes education by offering personalized learning experiences. Unlike traditional teaching methods, AI-powered platforms can analyze students' performance data.

However, concerns have been raised about the over-reliance on technology. Critics worry that excessive dependence on AI may hinder independent thinking. Additionally, issues related to data privacy remain unresolved.

In my opinion, while AI presents certain challenges, its positive impact on education is undeniable. To maximize its benefits, we should adopt a balanced approach. Schools should integrate AI as a supplementary tool. Meanwhile, policymakers must establish strict regulations. Only by combining the efficiency of AI with the warmth of human guidance can we create a more inclusive educational ecosystem."""

FINAL_PARAGRAPH = (
    "In my opinion, while AI presents certain challenges, its positive impact "
    "on education is undeniable. To maximize its benefits, we should adopt a "
    "balanced approach. Schools should integrate AI as a supplementary tool. "
    "Meanwhile, policymakers must establish strict regulations. Only by "
    "combining the efficiency of AI with the warmth of human guidance can we "
    "create a more inclusive educational ecosystem."
)

CORRECT_FINAL_TRANSLATION = (
    "在我看来，尽管人工智能带来了一定挑战，但它对教育的积极影响不容否认。"
    "为了最大化其效益，我们应采取平衡的方式。学校应将人工智能作为辅助工具。"
    "与此同时，政策制定者必须建立严格的监管。只有将人工智能的效率与人文指导"
    "的温度相结合，我们才能构建一个更具包容性的教育生态系统。"
)

# 模型对句首常用词最可能给出的孤立词典义。
PLANNED_GLOSSARY = {
    "AI": "人工智能",
    "Only": "仅",
    "Meanwhile": "同时",
    "Schools": "学校",
    "To": "为了",
}


class SentenceInitialTermTests(unittest.TestCase):
    def test_sentence_opening_words_are_not_treated_as_terminology(self):
        candidates = extract_term_candidates(normalize_source_structure(ARTICLE))
        for word in (
            "Only",
            "Meanwhile",
            "Schools",
            "However",
            "Critics",
            "Proponents",
            "Additionally",
            "Unlike",
            "In",
            "To",
        ):
            self.assertNotIn(word, candidates)

    def test_headline_does_not_absorb_the_next_sentence_opening_word(self):
        candidates = extract_term_candidates(normalize_source_structure(ARTICLE))
        self.assertNotIn("Education In", candidates)

    def test_acronym_used_mid_sentence_is_still_collected(self):
        candidates = extract_term_candidates(normalize_source_structure(ARTICLE))
        self.assertIn("AI", candidates)


class AdvisoryGlossaryTests(unittest.TestCase):
    def test_correct_paragraph_is_accepted_without_a_repair(self):
        calls = []

        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult(CORRECT_FINAL_TRANSLATION)

        outcome = run_quality_checked_completion(
            FINAL_PARAGRAPH,
            "zh",
            "SYSTEM",
            complete,
            0.1,
            1,
            glossary=PLANNED_GLOSSARY,
            advisory_terms=PLANNED_GLOSSARY,
        )

        self.assertEqual(outcome.text, CORRECT_FINAL_TRANSLATION)
        self.assertEqual(outcome.errors, ())
        self.assertEqual(len(calls), 1)

    def test_only_would_otherwise_be_reported_as_a_missing_term(self):
        """Without the advisory downgrade this exact mapping forced the repair."""
        self.assertEqual(
            validate_translation(
                FINAL_PARAGRAPH, CORRECT_FINAL_TRANSLATION, "zh"
            ),
            [],
        )
        self.assertEqual(
            find_missing_glossary_terms(
                FINAL_PARAGRAPH, CORRECT_FINAL_TRANSLATION, PLANNED_GLOSSARY
            ),
            ("Only => 仅",),
        )


class RepairRegressionGuardTests(unittest.TestCase):
    def test_translated_repair_instructions_never_replace_a_better_first_draft(self):
        # 纯翻译模型会把修复指令当原文翻译，这正是丢段的直接原因。
        leaked_instructions = (
            "仅修正下面列出的缺陷，其余翻译内容保持不变。\n使用要求的术语：仅"
        )
        outputs = iter(
            (
                CompletionResult(CORRECT_FINAL_TRANSLATION),
                CompletionResult(leaked_instructions),
            )
        )

        outcome = run_quality_checked_completion(
            FINAL_PARAGRAPH,
            "zh",
            "SYSTEM",
            lambda messages, temperature: next(outputs),
            0.1,
            1,
            glossary=PLANNED_GLOSSARY,
            previous_output="上一段的译文与本段无关。",
        )

        self.assertEqual(outcome.text, CORRECT_FINAL_TRANSLATION)
        self.assertNotIn("仅修正下面列出的缺陷", outcome.text)

    def test_repair_is_kept_only_when_it_strictly_reduces_defects(self):
        outputs = iter(
            (
                CompletionResult("Six people受伤。"),
                CompletionResult("六人受伤。"),
            )
        )
        improved = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: next(outputs),
            0.1,
            1,
        )
        self.assertEqual(improved.text, "六人受伤。")

        sideways = iter(
            (
                CompletionResult("Six people受伤。"),
                CompletionResult("authorities报道six人受伤。"),
            )
        )
        unchanged = run_quality_checked_completion(
            "Six people were injured.",
            "zh",
            "SYSTEM",
            lambda messages, temperature: next(sideways),
            0.1,
            1,
        )
        self.assertEqual(unchanged.text, "Six people受伤。")
        self.assertTrue(unchanged.retried)


if __name__ == "__main__":
    unittest.main()
