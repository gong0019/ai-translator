# News Translation Accuracy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace line-by-line local-model translation with a document-aware news pipeline that shares terminology, detects truncated input, uses compact prompts, and repairs only defective chunks.

**Architecture:** Add a pure `document_translation.py` module for input completeness, term extraction, glossary validation, and paragraph chunking. Keep llama.cpp lifecycle and terminal interaction in `translator_cli.py`, while extending `translation_quality.py` with glossary-aware concrete defect reporting and targeted repair prompts.

**Tech Stack:** Python 3.14, standard library (`dataclasses`, `json`, `re`), llama-cpp-python, unittest, Markdown Skills, JSON terminology data.

**Spec:** `docs/superpowers/specs/2026-08-25-news-translation-accuracy-design.md`

## Global Constraints

- Do not add online APIs or new Python dependencies.
- Runtime prompts must be shorter than the current `skills/base.md + skills/en_to_zh.md` prompt.
- Translate short documents whole; split long documents only at paragraph boundaries.
- Never hide a completed translation or display internal validator codes.
- Preserve existing macOS, Linux, and Windows launcher behavior.
- Preserve the user's unrelated uncommitted installer, launcher, model-scan, and asset changes.

---

### Task 1: Input Completeness and Paragraph Chunk Planning

**Files:**
- Create: `document_translation.py`
- Create: `tests/test_document_translation.py`

**Interfaces:**
- Produces: `looks_likely_truncated(text: str, source_code: str) -> bool`
- Produces: `plan_paragraph_chunks(text: str, count_tokens: Callable[[str], int], max_source_tokens: int) -> list[str]`
- Consumes: normalized text from `normalize_source_structure`

- [ ] **Step 1: Write failing completeness and chunking tests**

```python
class InputCompletenessTests(unittest.TestCase):
    def test_detects_partial_english_tail(self):
        self.assertTrue(looks_likely_truncated("Voters ahead of th", "en"))

    def test_accepts_complete_english_sentence(self):
        self.assertFalse(looks_likely_truncated("Voters remain concerned.", "en"))


class ParagraphChunkPlanningTests(unittest.TestCase):
    def test_keeps_short_document_whole(self):
        text = "Heading\n\nFirst paragraph.\n\nSecond paragraph."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 20),
            [text],
        )

    def test_splits_only_at_paragraph_boundaries(self):
        text = "One two three.\n\nFour five six.\n\nSeven eight nine."
        self.assertEqual(
            plan_paragraph_chunks(text, lambda value: len(value.split()), 6),
            ["One two three.\n\nFour five six.", "Seven eight nine."],
        )
```

- [ ] **Step 2: Run the new tests and verify RED**

Run: `.venv/bin/python -m unittest tests.test_document_translation -v`

Expected: import failure because `document_translation` does not exist.

- [ ] **Step 3: Implement minimal pure planning functions**

```python
from collections.abc import Callable
import re


_DANGLING_ENGLISH_WORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
    "or", "the", "to", "with", "without",
}


def looks_likely_truncated(text: str, source_code: str) -> bool:
    if source_code != "en":
        return False
    stripped = text.rstrip()
    if not stripped or stripped.endswith((".", "!", "?", '"', "'", "”", "’")):
        return False
    final_match = re.search(r"([A-Za-z]+)$", stripped)
    if not final_match:
        return False
    final_word = final_match.group(1).lower()
    return len(final_word) <= 2 or final_word in _DANGLING_ENGLISH_WORDS


def plan_paragraph_chunks(text, count_tokens, max_source_tokens):
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks = []
    current = []
    for paragraph in paragraphs:
        candidate = "\n\n".join((*current, paragraph))
        if current and count_tokens(candidate) > max_source_tokens:
            chunks.append("\n\n".join(current))
            current = [paragraph]
        else:
            current.append(paragraph)
    if current:
        chunks.append("\n\n".join(current))
    return chunks
```

- [ ] **Step 4: Run tests and verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_document_translation -v`

Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add document_translation.py tests/test_document_translation.py
git commit -m "feat: plan complete news translation chunks"
```

---

### Task 2: Document Terminology and Curated News Mappings

**Files:**
- Modify: `document_translation.py`
- Modify: `tests/test_document_translation.py`
- Create: `skills/news_terms.json`

**Interfaces:**
- Produces: `extract_term_candidates(text: str) -> tuple[str, ...]`
- Produces: `load_curated_terms(path: str, pair_key: str) -> dict[str, str]`
- Produces: `parse_glossary_response(response: str, candidates: tuple[str, ...], curated: dict[str, str]) -> dict[str, str]`
- Produces: `format_glossary(glossary: dict[str, str]) -> str`

- [ ] **Step 1: Write failing terminology tests**

```python
def test_extracts_document_terms_without_sentence_starters(self):
    source = (
        "Scott Bessent wrote in the Financial Times. "
        "Bessent later spoke to Reuters at 18:00 BST."
    )
    self.assertEqual(
        extract_term_candidates(source),
        ("Scott Bessent", "Financial Times", "Bessent", "Reuters", "BST"),
    )

def test_curated_terms_override_model_and_malformed_values_are_dropped(self):
    response = '```json\n{"Bessent":"贝森特","Reuters":"路透通讯"}\n```'
    glossary = parse_glossary_response(
        response,
        ("Bessent", "Reuters", "BST"),
        {"Reuters": "路透社", "BST": "英国夏令时"},
    )
    self.assertEqual(
        glossary,
        {"Bessent": "贝森特", "Reuters": "路透社", "BST": "英国夏令时"},
    )

def test_malformed_planner_json_falls_back_to_curated_terms(self):
    self.assertEqual(
        parse_glossary_response("not json", ("Reuters",), {"Reuters": "路透社"}),
        {"Reuters": "路透社"},
    )
```

- [ ] **Step 2: Run tests and verify RED**

Run: `.venv/bin/python -m unittest tests.test_document_translation -v`

Expected: failures for the three missing terminology functions.

- [ ] **Step 3: Add the compact curated data file**

```json
{
  "en_to_zh": {
    "Reuters": "路透社",
    "Financial Times": "《金融时报》",
    "Strait of Hormuz": "霍尔木兹海峡",
    "BBC Scotland News": "英国广播公司苏格兰新闻部",
    "BBC": "BBC",
    "BST": "英国夏令时"
  }
}
```

- [ ] **Step 4: Implement extraction, strict JSON parsing, curated precedence, and formatting**

Candidate extraction must preserve first occurrence, prefer the longest capitalized phrase at each location, include all-uppercase acronyms, and filter sentence starters `A`, `An`, `The`, `One`, `He`, `She`, `It`, `They`, `This`, and `That`. `parse_glossary_response` must accept an optional fenced JSON object, keep only requested string keys with non-empty string values, then overwrite them with curated mappings.

```python
def format_glossary(glossary: dict[str, str]) -> str:
    if not glossary:
        return ""
    return "DOCUMENT GLOSSARY:\n" + "\n".join(
        f"- {source} => {target}" for source, target in glossary.items()
    )
```

- [ ] **Step 5: Run tests and verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_document_translation -v`

Expected: all document terminology tests pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add document_translation.py tests/test_document_translation.py skills/news_terms.json
git commit -m "feat: build shared news terminology glossaries"
```

---

### Task 3: Glossary-Aware Validation and Concrete Repair Instructions

**Files:**
- Modify: `translation_quality.py:348-487`
- Modify: `tests/test_translation_quality.py`
- Modify: `tests/test_quality_retry.py`

**Interfaces:**
- Produces: `find_unexpected_latin_tokens(source: str, output: str) -> tuple[str, ...]`
- Produces: `find_missing_glossary_terms(source: str, output: str, glossary: dict[str, str]) -> tuple[str, ...]`
- Extends: `run_quality_checked_completion(..., glossary: dict[str, str] | None = None) -> QualityOutcome`
- Extends: `QualityOutcome.review_notes: tuple[str, ...] = ()`

- [ ] **Step 1: Write failing exact-defect tests**

```python
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
```

- [ ] **Step 2: Write a failing repair-prompt behavior test**

Use a fake `complete` function whose first result contains `Reuters` and whose second result is valid. Assert that the second user message contains `Translate this remaining source token: Reuters`, contains the chunk glossary, does not contain `TARGET_SCRIPT_RESIDUAL`, and exactly two completions occur.

Add a second fake whose repair still contains `Reuters`; assert `outcome.text` remains present and `outcome.review_notes == ("可能仍有未翻译内容：Reuters",)`.

- [ ] **Step 3: Run tests and verify RED**

Run: `.venv/bin/python -m unittest tests.test_translation_quality tests.test_quality_retry -v`

Expected: missing exact-defect functions and missing `glossary` argument.

- [ ] **Step 4: Implement concrete defect discovery and targeted repair text**

`find_unexpected_latin_tokens` must reuse protected-span and source-acronym allowances. `find_missing_glossary_terms` must match source terms longest-first without double-counting `Bessent` inside `Scott Bessent`. `_repair_messages` must receive concrete defect strings and format a compact request:

```python
def _concrete_defects(source, output, target_code, glossary):
    defects = []
    if target_code == "zh":
        defects.extend(
            f"Translate this remaining source token: {token}"
            for token in find_unexpected_latin_tokens(source, output)
        )
    defects.extend(
        f"Use this required term: {mapping}"
        for mapping in find_missing_glossary_terms(source, output, glossary)
    )
    return tuple(defects)


def _user_review_notes(source, output, target_code, glossary):
    if target_code != "zh":
        return ()
    tokens = find_unexpected_latin_tokens(source, output)
    return (("可能仍有未翻译内容：" + "、".join(tokens)),) if tokens else ()
```

```text
Correct only the defects listed below while preserving every other translated fact.
- Translate this remaining source token: Reuters
- Use this required term: Bessent => 贝森特

DOCUMENT GLOSSARY:
- Reuters => 路透社

SOURCE CHUNK:
...

CURRENT TRANSLATION:
...

Return the complete corrected translation only.
```

- [ ] **Step 5: Run quality tests and verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_translation_quality tests.test_quality_retry -v`

Expected: all quality and retry tests pass.

- [ ] **Step 6: Commit Task 3**

```bash
git add translation_quality.py tests/test_translation_quality.py tests/test_quality_retry.py
git commit -m "feat: repair concrete translation defects"
```

---

### Task 4: Compact Runtime Skills

**Files:**
- Modify: `skills/base.md`
- Modify: `skills/en_to_zh.md`
- Modify: other `skills/*_to_*.md` only where they duplicate the base contract
- Modify: `tests/test_skill_contract.py`
- Modify: `tests/test_prompt_routing.py`

**Interfaces:**
- Consumes: `format_glossary` output appended by `TranslatorCLI.build_dynamic_prompt`
- Preserves: `load_skill(skill_name: str) -> str`

- [ ] **Step 1: Write failing compact-prompt contract tests**

```python
def test_runtime_prompt_excludes_fixed_regression_examples(self):
    prompt, _, _ = self.make_cli().build_dynamic_prompt("Bessent spoke to Reuters.")
    self.assertNotIn("Reno", prompt)
    self.assertNotIn("Nevada", prompt)
    self.assertNotIn("wildfire", prompt.lower())

def test_runtime_prompt_is_compact(self):
    prompt, _, _ = self.make_cli().build_dynamic_prompt("Bessent spoke to Reuters.")
    self.assertLess(len(prompt), 2200)
```

- [ ] **Step 2: Run prompt tests and verify RED**

Run: `.venv/bin/python -m unittest tests.test_skill_contract tests.test_prompt_routing -v`

Expected: fixed regression examples remain and the current prompt exceeds the compact limit.

- [ ] **Step 3: Replace the base Skill with the five approved durable rules**

```markdown
You are a professional {source_name}-to-{target_name} news translator.

Translate every source fact exactly once. Preserve paragraph order, headings, quotations, names, numbers, units, dates, times, negation, modality, and uncertainty. Follow the supplied document glossary exactly. Do not summarize, explain, censor, or complete missing source text. Output only the complete translation in {target_name}.
```

Keep `en_to_zh.md` limited to natural Simplified Chinese grammar, consistent transliteration, established Chinese organization/place names, and no ordinary English residue. Remove the Nevada regression wording.

- [ ] **Step 4: Run prompt and Skill tests and verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_skill_contract tests.test_prompt_routing -v`

Expected: compact prompt tests and all routing tests pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add skills tests/test_skill_contract.py tests/test_prompt_routing.py
git commit -m "refactor: compact runtime translation skills"
```

---

### Task 5: Document-Aware CLI Orchestration

**Files:**
- Modify: `translator_cli.py:30-41, 495-535, 642-715`
- Modify: `tests/test_cli_quality_integration.py`

**Interfaces:**
- Consumes: all Task 1 and Task 2 functions
- Produces: `TranslatorCLI._build_document_glossary(text: str, pair_key: str) -> dict[str, str]`
- Produces: `TranslatorCLI._count_tokens(text: str) -> int`
- Produces: `TranslatorCLI._resolve_translation_route(text: str) -> tuple[str, str, str, str]`, returning source name, target name, resolved target code, and pair key
- Extends: `TranslatorCLI.build_dynamic_prompt(text: str, glossary: dict[str, str] | None = None)`

- [ ] **Step 1: Write a failing short-document integration test**

Create a `FakeLlama` response sequence for one glossary-planning call and one whole-document translation call. Pass a three-paragraph article containing `Scott Bessent`, `Bessent`, and `Reuters`. Assert that translation uses one document request rather than three line requests, the translation prompt contains the shared glossary, and output paragraph order is preserved.

- [ ] **Step 2: Write a failing long-document and targeted-repair integration test**

Use a deterministic token counter that forces two paragraph chunks. Return a valid first chunk, an invalid second chunk containing `Reuters`, and a corrected retry. Assert the first chunk is generated once, the second twice, and only the corrected outputs are displayed.

- [ ] **Step 3: Write a failing truncated-input confirmation test**

Patch `TranslatorCLI._confirm_truncated_input` to return `False`, call `stream_translate("Voters ahead of th")`, and assert zero model completions and the Chinese message `输入末尾疑似不完整，已取消翻译。`.

- [ ] **Step 4: Run CLI integration tests and verify RED**

Run: `.venv/bin/python -m unittest tests.test_cli_quality_integration -v`

Expected: the current line-by-line implementation makes too many calls and has no glossary or truncation confirmation.

- [ ] **Step 5: Implement document orchestration**

`stream_translate` must:

1. Normalize input once.
2. Detect source language once.
3. Ask confirmation for likely truncation.
4. Build one glossary using curated terms plus one constrained planning call for unknown candidates.
5. Reserve 40% of `n_ctx`, capped at 3000 source tokens, and call `plan_paragraph_chunks`.
6. Build one prompt per chunk with the same glossary.
7. Call `run_quality_checked_completion` once per chunk, allowing one targeted retry.
8. Print every final chunk in order and no internal validation identifiers.
9. Collect `outcome.review_notes` and print each unique concrete note once after the complete translation.

The glossary planning prompt must request a JSON object with exactly the supplied keys, `temperature=0.0`, and `max_tokens=min(1024, configured max_tokens)`. If parsing fails, use curated terms only.

```python
normalized_text = normalize_source_structure(text)
source_code, _ = detect_language(normalized_text)
if looks_likely_truncated(normalized_text, source_code):
    if not self._confirm_truncated_input():
        console.print("[yellow]输入末尾疑似不完整，已取消翻译。[/]")
        return

_, _, resolved_target_code, pair_key = self._resolve_translation_route(normalized_text)
glossary = self._build_document_glossary(normalized_text, pair_key)
max_source_tokens = min(3000, max(256, int(self.config["n_ctx"] * 0.4)))
chunks = plan_paragraph_chunks(normalized_text, self._count_tokens, max_source_tokens)
review_notes = []
for chunk in chunks:
    prompt, _, target_name = self.build_dynamic_prompt(chunk, glossary)
    outcome = run_quality_checked_completion(
        source=chunk,
        target_code=resolved_target_code,
        system_prompt=prompt,
        complete=lambda messages, attempt_temperature: self._collect_completion(
            messages,
            attempt_temperature,
            repeat_penalty,
            max_tokens,
        ),
        temperature=temperature,
        retry_limit=retry_limit,
        validation_enabled=validation_enabled,
        glossary=glossary,
    )
    sys.stdout.write(outcome.text + ("" if outcome.text.endswith("\n") else "\n"))
    review_notes.extend(outcome.review_notes)
for note in dict.fromkeys(review_notes):
    console.print(f"[yellow]⚠ {note}[/]")
```

- [ ] **Step 6: Run CLI integration tests and verify GREEN**

Run: `.venv/bin/python -m unittest tests.test_cli_quality_integration -v`

Expected: all document-aware integration tests pass.

- [ ] **Step 7: Commit only the translation orchestration hunk**

Because `translator_cli.py` already contains an unrelated uncommitted model-scan filter, use interactive staging and verify the cached diff excludes that pre-existing hunk.

```bash
git add -p translator_cli.py
git add tests/test_cli_quality_integration.py
git diff --cached -- translator_cli.py tests/test_cli_quality_integration.py
git commit -m "feat: translate news with shared document context"
```

---

### Task 6: Iran Regression, Documentation, and Full Verification

**Files:**
- Create: `tests/test_iran_regression.py`
- Modify: `README.md:123-145`
- Modify: `README_zh.md:123-145`

**Interfaces:**
- Tests the public document-planning, glossary, validation, and CLI behavior from Tasks 1-5.

- [ ] **Step 1: Add the exact Iran regression fixture**

The source fixture must include `Scott Bessent`, later `Bessent`, `Reuters`, `Strait of Hormuz`, `Financial Times`, `13:00`, `18:00 BST`, `$4`, and the final truncated text `ahead of th`. Use hand-checked expected glossary literals:

```python
EXPECTED_TERMS = {
    "Reuters": "路透社",
    "Financial Times": "《金融时报》",
    "Strait of Hormuz": "霍尔木兹海峡",
    "BST": "英国夏令时",
}
```

Assert truncation is detected, curated terms load exactly, complete input produces paragraph chunks without mid-paragraph splits, and the final rendered output contains no internal validator codes.

- [ ] **Step 2: Run the Iran regression and verify it passes**

Run: `.venv/bin/python -m unittest tests.test_iran_regression -v`

Expected: all Iran regression tests pass.

- [ ] **Step 3: Update user documentation**

Document that short inputs translate whole, long inputs split at paragraph boundaries, document terminology is shared, likely truncated input requires confirmation, quality repair is limited to one defective-chunk retry, and the accuracy mode can take roughly 1.5-2 times as long as the previous line-by-line flow.

- [ ] **Step 4: Run the complete Python suite**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`

Expected: zero failures and zero errors.

- [ ] **Step 5: Run every shell regression test**

Run: `for test_script in tests/*.sh; do bash "$test_script" || exit; done`

Expected: exit code 0.

- [ ] **Step 6: Run syntax and diff verification**

Run: `.venv/bin/python -m py_compile translator_cli.py translation_quality.py document_translation.py`

Expected: exit code 0.

Run: `git diff --check`

Expected: no output and exit code 0.

- [ ] **Step 7: Commit regression coverage and documentation**

```bash
git add tests/test_iran_regression.py README.md README_zh.md
git commit -m "test: cover accurate Iran news translation"
```
