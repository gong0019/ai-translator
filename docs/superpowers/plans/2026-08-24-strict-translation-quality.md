# Strict Translation Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every translation route inherit exact anti-omission rules, reject deterministically observable defects, and perform no more than one hidden repair attempt before displaying output.

**Architecture:** Keep language detection and model loading in `translator_cli.py`; move source normalization, validation, repair-prompt construction, and retry orchestration into a pure `translation_quality.py` module. Every prompt becomes `base.md + one pair Skill`; model output is buffered until validation completes, so a rejected first attempt is never displayed.

**Tech Stack:** Python 3 standard library, `llama-cpp-python`, Markdown Skill files, `unittest`, existing shell regression tests.

**Spec:** `docs/superpowers/specs/2026-08-24-strict-translation-quality-design.md`

## Global Constraints

- Runtime translation and validation must remain fully local and must not require network access.
- Every route, including `mixed_to_zh`, must compose `skills/base.md` followed by at most one pair-specific Skill.
- Retry count is exactly zero or one; invalid configuration values resolve to one.
- The rejected first attempt must never be printed or exposed to another consumer.
- The feature must not restore automatic clipboard copying.
- Protected spans are limited to the exact categories in the design specification.
- Existing installer, model discovery, launcher, and symlink behavior must remain unchanged.
- Preserve all existing unrelated working-tree changes; stage and commit only files named by each task.

---

### Task 1: Enforce a uniform, non-ambiguous Skill contract

**Files:**
- Modify: `skills/base.md`
- Modify: every existing `skills/*_to_*.md` file
- Create: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: Markdown files loaded by `load_skill(skill_name: str) -> str`.
- Produces: one base contract and pair Skills with exact headers `SCOPE`, `MANDATORY COVERAGE`, `STRUCTURE`, `GRAMMAR`, `TERMINOLOGY`, and `FORBIDDEN OUTPUT`.

- [ ] **Step 1: Write the failing Skill-contract test**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "## SCOPE",
    "## MANDATORY COVERAGE",
    "## STRUCTURE",
    "## GRAMMAR",
    "## TERMINOLOGY",
    "## FORBIDDEN OUTPUT",
}
PROHIBITED = (
    "appropriate",
    "natural",
    "naturally",
    "idiomatic",
    "when appropriate",
    "where possible",
    "if needed",
    "when needed",
    "when necessary",
    "if necessary",
    "where needed",
    "where necessary",
    "where required",
    "as needed",
    "if appropriate",
    "as appropriate",
    "depending on context",
    "according to context",
    "context-appropriate",
    "prefer ",
    "try to",
    "may choose",
    "can choose",
    "as natural as possible",
)

class SkillContractTests(unittest.TestCase):
    def test_every_pair_skill_has_exact_sections(self):
        for path in sorted((ROOT / "skills").glob("*_to_*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(REQUIRED.issubset(set(text.splitlines())), path.name)

    def test_no_skill_uses_discretionary_phrases(self):
        for path in sorted((ROOT / "skills").glob("*.md")):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in PROHIBITED:
                self.assertNotIn(phrase, text, f"{path.name}: {phrase}")

    def test_base_contains_exact_invariants(self):
        text = (ROOT / "skills/base.md").read_text(encoding="utf-8")
        for required in (
            "Translate every source title, sentence, clause, list item, label, caption, and footnote exactly once.",
            "Keep each heading separate from the following body text.",
            "A Latin word is not protected merely because it is capitalized.",
        ):
            self.assertIn(required, text)
```

- [ ] **Step 2: Run the test and verify the existing files fail**

Run: `.venv/bin/python3 -m unittest tests.test_skill_contract -v`

Expected: FAIL because the existing pair Skills do not contain the six required section headers.

- [ ] **Step 3: Rewrite `base.md` and all pair Skills**

Use the ten exact invariants from the specification in `base.md`. Rewrite each pair file with all six required headers. Keep grammar rules language-specific, but use these exact cross-file requirements:

```markdown
## MANDATORY COVERAGE
Translate every noun, verb, adjective, adverb, pronoun, determiner, preposition, conjunction, particle, and discourse marker. Translate every title, sentence, and clause exactly once.

## STRUCTURE
Keep a source heading on a separate output line. Do not move body information into a heading. Preserve paragraph order, list order, quotations, and sentence boundaries.

## TERMINOLOGY
Preserve every number, unit, date, time, percentage, range, and comparison. Use one target-language rendering for each repeated proper noun.

## FORBIDDEN OUTPUT
Do not output source-language residue outside protected spans. Do not summarize, omit, merge, duplicate, or invent information.
```

For `en_to_zh.md`, also include the exact Nevada requirements from the specification and explicit coverage of verbs, adverbs, conjunctions, prepositions, determiners, and `authorities`.

- [ ] **Step 4: Run the Skill-contract test and verify it passes**

Run: `.venv/bin/python3 -m unittest tests.test_skill_contract -v`

Expected: PASS with three successful tests and no discretionary phrase match.

- [ ] **Step 5: Commit only the Skill contract changes**

```bash
git add skills/base.md skills/*_to_*.md tests/test_skill_contract.py
git commit -m "fix: enforce strict translation skill contracts"
```

---

### Task 2: Compose the base contract for every route

**Files:**
- Modify: `translator_cli.py:480-518`
- Create: `tests/test_prompt_routing.py`

**Interfaces:**
- Consumes: `load_skill(name: str) -> str`, `detect_language(text: str) -> tuple[str, str]`.
- Produces: `TranslatorCLI.build_dynamic_prompt(text: str) -> tuple[str, str, str]`, always containing the base contract and zero or one specialized Skill.

- [ ] **Step 1: Write the failing mixed-route test**

```python
import unittest
from translator_cli import TranslatorCLI

class PromptRoutingTests(unittest.TestCase):
    def make_cli(self):
        cli = object.__new__(TranslatorCLI)
        cli.config = {"target_lang_key": "1"}
        return cli

    def test_english_to_chinese_has_base_and_pair_skill(self):
        prompt, source, target = self.make_cli().build_dynamic_prompt("Local authorities ordered six evacuations.")
        self.assertIn("Translate every source title", prompt)
        self.assertIn("## SCOPE\nENGLISH → SIMPLIFIED CHINESE", prompt)
        self.assertEqual((source, target), ("English", "Simplified Chinese (简体中文)"))

    def test_mixed_to_chinese_has_base_and_pair_skill(self):
        prompt, source, target = self.make_cli().build_dynamic_prompt("这个 app 需要 update")
        self.assertIn("Translate every source title", prompt)
        self.assertIn("## SCOPE\nMIXED LANGUAGE → SIMPLIFIED CHINESE", prompt)
        self.assertEqual(prompt.count("## SCOPE"), 1)
        self.assertEqual((source, target), ("Mixed / 混合夹杂", "Simplified Chinese (简体中文)"))

    def test_every_supported_source_and_target_includes_base_once(self):
        samples = (
            "Local authorities ordered evacuations.",
            "当地政府下令撤离。",
            "当局は避難を命じた。",
            "당국은 대피를 명령했다.",
            "Власти приказали эвакуироваться.",
            "Die Behörden müssen Häuser räumen.",
            "Las autoridades ordenaron la evacuación.",
            "Les autorités ont ordonné l’évacuation.",
            "Le autorità hanno ordinato l'evacuazione.",
        )
        cli = self.make_cli()
        for target_key in map(str, range(1, 10)):
            cli.config["target_lang_key"] = target_key
            for source in samples:
                prompt, _, _ = cli.build_dynamic_prompt(source)
                self.assertEqual(prompt.count("Translate every source title"), 1)
                self.assertLessEqual(prompt.count("## SCOPE"), 1)
```

- [ ] **Step 2: Run the routing test and verify the mixed route fails**

Run: `.venv/bin/python3 -m unittest tests.test_prompt_routing -v`

Expected: the ordinary route passes and `test_mixed_to_chinese_has_base_and_pair_skill` fails because the current early return omits `base.md`.

- [ ] **Step 3: Remove the mixed-route early return**

Set `pair_key = "mixed_to_zh"`, preserve source display `Mixed / 混合夹杂`, and continue through the common base-plus-pair composition path. For all other routes, retain `pair_key = f"{source_code}_to_{target_code}"`. Do not load more than one pair Skill.

- [ ] **Step 4: Run routing and Skill tests**

Run: `.venv/bin/python3 -m unittest tests.test_prompt_routing tests.test_skill_contract -v`

Expected: PASS.

- [ ] **Step 5: Commit the routing fix**

```bash
git add tests/test_prompt_routing.py
git add -p translator_cli.py
git commit -m "fix: apply base translation contract to every route"
```

---

### Task 3: Normalize source structure deterministically

**Files:**
- Create: `translation_quality.py`
- Create: `tests/test_translation_quality.py`

**Interfaces:**
- Produces: `normalize_source_structure(text: str) -> str`.
- Consumed later by: `TranslatorCLI.stream_translate` and `validate_translation`.

- [ ] **Step 1: Write failing normalization tests**

```python
import unittest
from translation_quality import normalize_source_structure

class SourceNormalizationTests(unittest.TestCase):
    def test_repairs_word_split_by_terminal_wrap(self):
        self.assertEqual(normalize_source_structure("a\npproached Reno."), "approached Reno.")

    def test_joins_lowercase_soft_continuation(self):
        self.assertEqual(normalize_source_structure("the fire\ncontinued spreading."), "the fire continued spreading.")

    def test_keeps_headline_separate_from_body(self):
        source = "Thousands evacuate Nevada homes\nTens of thousands of people were told to leave."
        self.assertEqual(normalize_source_structure(source), source)

    def test_keeps_blank_paragraph_bullet_and_markdown_heading(self):
        source = "# Alert\n\n- Leave now\n- Use Route 80"
        self.assertEqual(normalize_source_structure(source), source)
```

- [ ] **Step 2: Run the normalization tests and verify import failure**

Run: `.venv/bin/python3 -m unittest tests.test_translation_quality.SourceNormalizationTests -v`

Expected: ERROR with `ModuleNotFoundError: No module named 'translation_quality'`.

- [ ] **Step 3: Implement `normalize_source_structure`**

Implement the five ordered normalization rules from the specification. Use explicit helpers `_ends_inside_word`, `_begins_lowercase_continuation`, and `_begins_structural_line`. Preserve blank-line count as one blank separator and never strip internal punctuation.

- [ ] **Step 4: Run the normalization tests**

Run: `.venv/bin/python3 -m unittest tests.test_translation_quality.SourceNormalizationTests -v`

Expected: PASS with four tests.

- [ ] **Step 5: Commit source normalization**

```bash
git add translation_quality.py tests/test_translation_quality.py
git commit -m "feat: normalize translated source structure"
```

---

### Task 4: Detect structural, numeric, and script defects

**Files:**
- Modify: `translation_quality.py`
- Modify: `tests/test_translation_quality.py`

**Interfaces:**
- Produces: `extract_protected_spans(text: str) -> list[str]`.
- Produces: `validate_translation(source: str, output: str, target_code: str) -> list[str]`.
- Error ordering: `EMPTY_OUTPUT`, `PARAGRAPH_COUNT_MISMATCH`, `LINE_STRUCTURE_LOSS`, `SENTENCE_COUNT_LOSS`, `ARABIC_NUMBER_MISMATCH`, `ENGLISH_NUMBER_MISMATCH`, `TARGET_SCRIPT_RESIDUAL`.

- [ ] **Step 1: Add failing validator tests**

```python
from translation_quality import validate_translation

class TranslationValidatorTests(unittest.TestCase):
    def test_detects_empty_and_structure_loss(self):
        self.assertEqual(validate_translation("Title\nBody.", "", "zh"), ["EMPTY_OUTPUT"])
        errors = validate_translation("Title\nBody.\n\nNext paragraph.", "标题正文。", "zh")
        self.assertIn("PARAGRAPH_COUNT_MISMATCH", errors)
        self.assertIn("LINE_STRUCTURE_LOSS", errors)

    def test_detects_numbers_and_english_residual(self):
        source = "Six people were injured; 12 homes and 3.5% of land were affected."
        output = "据 authorities 称，五人受伤；13所房屋和3.5%的土地受到影响。"
        errors = validate_translation(source, output, "zh")
        self.assertIn("ARABIC_NUMBER_MISMATCH", errors)
        self.assertIn("ENGLISH_NUMBER_MISMATCH", errors)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_accepts_chinese_numbers_and_protected_spans(self):
        source = "Six users opened https://example.com and `/opt/app/run.sh`."
        output = "六名用户打开了 https://example.com 和 `/opt/app/run.sh`。"
        self.assertEqual(validate_translation(source, output, "zh"), [])

    def test_tens_of_thousands_requires_equivalent_quantity(self):
        source = "Tens of thousands of people evacuated."
        self.assertIn("ENGLISH_NUMBER_MISMATCH", validate_translation(source, "数千人撤离。", "zh"))
        self.assertEqual(validate_translation(source, "数以万计的人撤离。", "zh"), [])
```

- [ ] **Step 2: Run validator tests and verify missing functions fail**

Run: `.venv/bin/python3 -m unittest tests.test_translation_quality.TranslationValidatorTests -v`

Expected: FAIL because `validate_translation` does not exist.

- [ ] **Step 3: Implement protected spans and structural checks**

Implement the exact protected-span patterns from the specification. Compare non-empty paragraph counts, meaningful line counts, and sentence/heading unit counts after `normalize_source_structure`. Return `EMPTY_OUTPUT` alone for empty output.

- [ ] **Step 4: Implement numeric and target-script checks**

Normalize full-width digits with `str.translate`; compare ordered Arabic token lists after comma removal. Canonicalize English number words using explicit dictionaries for zero–nineteen, tens, and `hundred`/`thousand`/`million`/`billion`; recognize Chinese equivalents and Arabic digits. Remove protected spans before scanning Chinese output for `[A-Za-z]+`.

- [ ] **Step 5: Run the quality test module**

Run: `.venv/bin/python3 -m unittest tests.test_translation_quality -v`

Expected: PASS.

- [ ] **Step 6: Commit deterministic validation**

```bash
git add translation_quality.py tests/test_translation_quality.py
git commit -m "feat: validate observable translation defects"
```

---

### Task 5: Buffer model output and retry exactly once

**Files:**
- Modify: `translation_quality.py`
- Modify: `translator_cli.py:66-74,306-320,593-665`
- Create: `tests/test_quality_retry.py`

**Interfaces:**
- Add dataclass: `CompletionResult(text: str, truncated: bool = False)`.
- Add dataclass: `QualityOutcome(text: str, errors: tuple[str, ...], retried: bool)`.
- Add function: `normalize_quality_settings(validation_value: object, retry_value: object) -> tuple[bool, int]`.
- Add function: `run_quality_checked_completion(source: str, target_code: str, system_prompt: str, complete: Callable[[list[dict[str, str]], float], CompletionResult], temperature: float, retry_limit: int, validation_enabled: bool = True) -> QualityOutcome`.
- Add method: `TranslatorCLI._collect_completion(messages: list[dict[str, str]], temperature: float, repeat_penalty: float, max_tokens: int) -> CompletionResult`.

- [ ] **Step 1: Write failing retry-orchestration tests**

```python
import unittest
from translation_quality import CompletionResult, normalize_quality_settings, run_quality_checked_completion

class QualityRetryTests(unittest.TestCase):
    def test_valid_output_is_returned_without_retry(self):
        calls = []
        def complete(messages, temperature):
            calls.append((messages, temperature))
            return CompletionResult("六人受伤。")
        result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", complete, 0.1, 1)
        self.assertEqual(result.text, "六人受伤。")
        self.assertFalse(result.retried)
        self.assertEqual(len(calls), 1)

    def test_invalid_output_retries_once_at_zero_temperature(self):
        outputs = iter((CompletionResult("Six people受伤。"), CompletionResult("六人受伤。")))
        calls = []
        def complete(messages, temperature):
            calls.append((messages, temperature))
            return next(outputs)
        result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", complete, 0.1, 1)
        self.assertEqual(result.text, "六人受伤。")
        self.assertTrue(result.retried)
        self.assertEqual([item[1] for item in calls], [0.1, 0.0])
        self.assertIn("TARGET_SCRIPT_RESIDUAL", calls[1][0][-1]["content"])

    def test_second_failure_is_returned_without_third_call(self):
        calls = []
        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult("authorities称Six people受伤。")
        result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", complete, 0.1, 1)
        self.assertEqual(len(calls), 2)
        self.assertTrue(result.errors)

    def test_truncation_forces_retry(self):
        outputs = iter((CompletionResult("六人", truncated=True), CompletionResult("六人受伤。")))
        result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", lambda m, t: next(outputs), 0.1, 1)
        self.assertTrue(result.retried)
        self.assertEqual(result.errors, ())

    def test_disabled_validation_returns_first_result(self):
        calls = []
        def complete(messages, temperature):
            calls.append(temperature)
            return CompletionResult("Six people受伤。")
        result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", complete, 0.1, 1, validation_enabled=False)
        self.assertEqual(result.text, "Six people受伤。")
        self.assertEqual(len(calls), 1)

    def test_validator_exception_preserves_output_without_retry(self):
        from unittest.mock import patch
        with patch("translation_quality.validate_translation", side_effect=RuntimeError("broken validator")):
            result = run_quality_checked_completion("Six people were injured.", "zh", "SYSTEM", lambda m, t: CompletionResult("六人受伤。"), 0.1, 1)
        self.assertEqual(result.text, "六人受伤。")
        self.assertEqual(result.errors, ("VALIDATOR_ERROR",))
        self.assertFalse(result.retried)

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
            self.assertEqual(normalize_quality_settings(*inputs), expected)
```

- [ ] **Step 2: Run retry tests and verify import failure**

Run: `.venv/bin/python3 -m unittest tests.test_quality_retry -v`

Expected: FAIL because the dataclasses and orchestration function do not exist.

- [ ] **Step 3: Implement the pure retry orchestrator**

Construct the second attempt as system prompt plus a final user repair message containing stable error codes, source text, rejected output, and the exact requirement `Return one complete replacement translation. Do not return a patch, explanation, or analysis.` Append `OUTPUT_TRUNCATED` when `CompletionResult.truncated` is true. Call `complete` no more than `retry_limit + 1` times. If validation is disabled, return the first completion without calling the validator. Catch validator exceptions, return the completed output with `("VALIDATOR_ERROR",)`, and do not retry.

- [ ] **Step 4: Add configuration defaults and sanitization**

Add `quality_validation: True` and `quality_retry_limit: 1` to `DEFAULT_CONFIG`. Implement and test `normalize_quality_settings` with this exact rule:

```python
validation_enabled = validation_value if type(validation_value) is bool else True
retry_limit = retry_value if type(retry_value) is int and retry_value in (0, 1) else 1
return validation_enabled, retry_limit
```

Add table-driven tests for `(True, 1)`, `(False, 0)`, `(None, None)`, `("false", "0")`, `(1, True)`, and `(True, 2)`.

- [ ] **Step 5: Replace immediate token printing with buffered collection**

`_collect_completion` may consume llama.cpp streaming chunks, but it must only accumulate text and `finish_reason`; it must not write to `stdout`. `stream_translate` normalizes source text, translates each paragraph, invokes `run_quality_checked_completion`, then prints only `QualityOutcome.text`. If second validation fails, print a terminal warning listing `QualityOutcome.errors`. Do not call `pyperclip.copy`.

- [ ] **Step 6: Run retry, quality, routing, and configuration tests**

Run: `.venv/bin/python3 -m unittest tests.test_quality_retry tests.test_translation_quality tests.test_prompt_routing tests.test_skill_contract -v`

Expected: PASS; retry tests prove one-call and two-call boundaries.

- [ ] **Step 7: Commit retry integration**

```bash
git add translation_quality.py tests/test_quality_retry.py
git add -p translator_cli.py
git commit -m "feat: retry translations that fail quality checks"
```

---

### Task 6: Lock the Nevada/Reno defect as a regression fixture

**Files:**
- Create: `tests/fixtures/nevada_wildfire_en.txt`
- Create: `tests/fixtures/nevada_wildfire_zh_valid.txt`
- Create: `tests/fixtures/nevada_wildfire_zh_invalid.txt`
- Create: `tests/test_nevada_regression.py`
- Modify: `README.md`
- Modify: `README_zh.md`

**Interfaces:**
- Consumes: `normalize_source_structure`, `validate_translation`, and strict Skill files.
- Produces: an immutable regression for headline/body separation, `tens of thousands`, `Reno`, `Six`, and zero ordinary English residual.

- [ ] **Step 1: Add the fixture files and failing regression test**

```python
from pathlib import Path
import unittest
from translation_quality import validate_translation

FIXTURES = Path(__file__).parent / "fixtures"

class NevadaRegressionTests(unittest.TestCase):
    def test_observed_defect_is_rejected(self):
        source = (FIXTURES / "nevada_wildfire_en.txt").read_text(encoding="utf-8")
        invalid = (FIXTURES / "nevada_wildfire_zh_invalid.txt").read_text(encoding="utf-8")
        errors = validate_translation(source, invalid, "zh")
        self.assertIn("LINE_STRUCTURE_LOSS", errors)
        self.assertIn("ENGLISH_NUMBER_MISMATCH", errors)
        self.assertIn("TARGET_SCRIPT_RESIDUAL", errors)

    def test_complete_translation_is_accepted(self):
        source = (FIXTURES / "nevada_wildfire_en.txt").read_text(encoding="utf-8")
        valid = (FIXTURES / "nevada_wildfire_zh_valid.txt").read_text(encoding="utf-8")
        self.assertEqual(validate_translation(source, valid, "zh"), [])
        self.assertIn("数以万计", valid)
        self.assertIn("里诺", valid)
        self.assertIn("六人", valid)
```

- [ ] **Step 2: Run the regression and verify at least one assertion fails**

Run: `.venv/bin/python3 -m unittest tests.test_nevada_regression -v`

Expected: FAIL until the validator and fixture formatting agree on meaningful headline/body lines and English quantity expressions.

- [ ] **Step 3: Complete fixture handling without weakening validation**

Use the user's exact English report as the source fixture. Use the observed output containing `authorities` and missing `Tens of thousands` as the invalid fixture. Use a complete Chinese translation with three preserved paragraphs and four meaningful lines, including a separate headline line, as the valid fixture. Correct validator tokenization if the valid fixture exposes a deterministic parsing defect; do not remove an error check to make the fixture pass.

- [ ] **Step 4: Document quality validation and latency behavior**

Add README configuration documentation stating that `quality_validation` defaults to `true`, `quality_retry_limit` accepts `0` or `1`, output is buffered until validation completes, and only a detected defect can cause one extra generation. State that validation catches observable defects but does not mathematically prove semantic equivalence.

- [ ] **Step 5: Run the full verification suite**

```bash
.venv/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
for test_script in tests/*.sh; do bash "$test_script"; done
.venv/bin/python3 -m py_compile translator_cli.py translation_quality.py
bash -n install.sh run.sh uninstall.sh
git diff --check
```

Expected: all Python and shell tests pass, compilation and shell parsing exit zero, and `git diff --check` prints nothing.

- [ ] **Step 6: Commit the regression and documentation**

```bash
git add tests/fixtures tests/test_nevada_regression.py README.md README_zh.md
git commit -m "test: prevent incomplete Nevada news translation"
```

---

### Task 7: Review final behavior against every acceptance criterion

**Files:**
- Review: `docs/superpowers/specs/2026-08-24-strict-translation-quality-design.md`
- Review: all files changed by Tasks 1–6

**Interfaces:**
- Consumes: the completed implementation and full verification output.
- Produces: an evidence-backed completion report; no new runtime interface.

- [ ] **Step 1: Run an acceptance scan**

```bash
rg -n -i 'appropriate|natural|naturally|idiomatic|prefer |try to|when needed|if needed|when necessary|if necessary|where needed|where necessary|where required|where possible|as needed|depending on context|according to context|may choose|can choose' skills
rg -n 'pyperclip\.copy' translator_cli.py translation_quality.py
```

Expected: both commands return no matches.

- [ ] **Step 2: Run the full verification suite again from a clean process**

Run the exact Task 6 Step 5 command block again.

Expected: every command exits zero with no test failure.

- [ ] **Step 3: Inspect the final diff and commit scope**

```bash
git status --short
git diff --stat HEAD~6..HEAD
git log -7 --oneline
```

Expected: strict-translation commits contain only planned files; pre-existing installer, launcher, icon, and model-discovery changes remain preserved and are not accidentally included.

- [ ] **Step 4: Report exact guarantees and limitations**

Report the passing test counts, Nevada regression result, retry call limit, and the explicit limitation that deterministic checks detect observable defects but cannot prove arbitrary semantic equivalence.
