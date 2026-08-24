# Strict Translation Quality Design

## Objective

Prevent observable translation defects in every supported language route, with particular protection against:

- omission of a title, sentence, clause, modifier, or named fact;
- merging a title with the first body sentence;
- untranslated source-language words in the target output;
- changed or lost numbers, units, dates, times, percentages, and ranges;
- inconsistent treatment of the same proper noun within one input;
- summaries, paraphrases that remove facts, and unsupported additions.

The implementation must remain local, work with every discovered GGUF chat model, and require no network service.

## Non-goals

- The validator will not claim to prove semantic equivalence between arbitrary languages.
- The validator will not use a second model, embeddings, dictionaries downloaded at runtime, or online APIs.
- The validator will not retry indefinitely.
- The implementation will not add model-specific prompt templates outside llama.cpp's chat-template handling.

## Architecture

Translation quality will use three independent layers:

1. **Prompt contract:** `skills/base.md` defines exact invariants shared by every route. Pair-specific Skill files define only language-specific transformations and must not weaken the base contract.
2. **Uniform routing:** every route, including mixed-language-to-Chinese, receives the base contract followed by one specialized Skill. No specialized route may return before the base contract is composed.
3. **Deterministic validation and one retry:** local code checks observable output properties. A failed first result is retried once with an error-specific repair instruction and deterministic decoding. The second result is validated again.

## Prompt Contract

Every Skill file will use imperative requirements. A case-insensitive contract test will reject these discretionary terms and phrases: `appropriate`, `natural`, `naturally`, `idiomatic`, `prefer`, `try to`, `when needed`, `if needed`, `when necessary`, `if necessary`, `where needed`, `where necessary`, `where required`, `where possible`, `as needed`, `as appropriate`, `depending on context`, `according to context`, `context-appropriate`, `may choose`, and `can choose`.

The contract will define these exact invariants:

1. Translate every source title, sentence, clause, list item, label, caption, and footnote exactly once.
2. Do not delete, merge, duplicate, summarize, or invent any source information.
3. Keep each heading separate from the following body text.
4. Preserve the order and count of non-empty paragraphs. Preserve meaningful line boundaries inside a paragraph.
5. Preserve every number, numeric word, unit, currency, percentage, date, time, range, comparison, negation, condition, modality, causal relation, contrast, and uncertainty marker.
6. Use one target-language rendering for every repeated proper noun within one input.
7. Translate established geographic and organization names to their standard target-language names. Preserve source spelling only for protected spans.
8. Protected spans are limited to URLs, email addresses, inline or fenced code, shell commands, filesystem paths, variables, and placeholders. A Latin word is not protected merely because it is capitalized.
9. Output only the translation. Do not output analysis, labels, apologies, or the prompt.
10. Before emitting the answer, internally compare the source and translation against requirements 1–8. This instruction does not authorize visible analysis.

The contract will not require literal word order. Grammar may be restructured only when all source facts and logical relationships remain present.

## Pair-specific Skills

Every `skills/<source>_to_<target>.md` file will use the following fixed sections:

- `SCOPE`: exact source and target language/script.
- `MANDATORY COVERAGE`: target-specific zero-residual requirement and explicit coverage of nouns, verbs, adjectives, adverbs, pronouns, determiners, prepositions, conjunctions, particles, and discourse markers.
- `STRUCTURE`: rules for headings, quotations, sentences, and clauses.
- `GRAMMAR`: deterministic language-pair transformations.
- `TERMINOLOGY`: numbers, proper nouns, place names, organizations, abbreviations, and repeated-term consistency.
- `FORBIDDEN OUTPUT`: source-language residue, summaries, omitted clauses, merged headings, explanations, and invented facts.

The English-to-Chinese Skill will additionally require:

- translate quoted headlines by meaning and register; do not use a literal rendering that changes who experiences the emotion;
- keep a headline on its own output line when it occupies its own source line;
- translate every ordinary English word, including verbs, adverbs, conjunctions, prepositions, determiners, and words such as `authorities`;
- render `Reno` consistently as `里诺` and `Nevada` consistently as `内华达州` when used as United States place names;
- retain the distinction between `thousands` and `tens of thousands`;
- never move body information into a headline.

The concrete Reno and Nevada names are regression examples, not a closed vocabulary list. The general proper-noun rules remain authoritative.

## Input Structure Normalization

Before prompting, the translator will normalize accidental visual wrapping without discarding meaningful structure:

1. Normalize CRLF and CR to LF.
2. Remove trailing spaces from every line.
3. Preserve blank lines as paragraph separators.
4. Join two adjacent non-empty lines only when the previous line ends inside an alphanumeric word or the next line begins with a lowercase continuation and the previous line has no sentence-final punctuation.
5. Do not join a line whose next line begins with an uppercase letter, opening quotation mark, bullet, list number, or Markdown heading marker.

This rule keeps a news headline separate from a following sentence while repairing terminal wrapping such as `a\npproached`.

## Deterministic Validator

Add a pure function:

```python
validate_translation(source: str, output: str, target_code: str) -> list[str]
```

It returns zero or more stable error codes. It performs no model call and has no side effects.

### Error codes

- `EMPTY_OUTPUT`: output contains no non-whitespace character.
- `PARAGRAPH_COUNT_MISMATCH`: source and output have different counts of non-empty paragraphs.
- `LINE_STRUCTURE_LOSS`: a source paragraph contains two or more meaningful lines but the corresponding output paragraph contains fewer meaningful lines.
- `SENTENCE_COUNT_LOSS`: an output paragraph contains fewer sentence-final boundaries than its source paragraph. A standalone heading line counts as one unit.
- `ARABIC_NUMBER_MISMATCH`: the ordered lists of Arabic numeric tokens differ after normalizing comma separators and Unicode full-width digits.
- `ENGLISH_NUMBER_MISMATCH`: an English numeric expression is missing from Chinese output. The initial implementation supports `zero` through `nineteen`, tens from `twenty` through `ninety`, and magnitude expressions containing `hundred`, `thousand`, `million`, or `billion`. Chinese numerals and equivalent Arabic digits both satisfy this check.
- `TARGET_SCRIPT_RESIDUAL`: for target `zh`, output contains a Latin alphabetic token not copied from an extracted protected span.

Protected-span extraction is deterministic. It recognizes only:

- `https://` and `http://` URLs;
- email addresses containing one `@` and a dotted domain;
- Markdown inline code and fenced code;
- POSIX paths beginning `/`, `./`, or `../`;
- Windows drive paths such as `C:\\path`;
- shell variables beginning `$` and brace placeholders such as `{name}` or `{{name}}`.

Capitalized words and unknown product names are not automatically protected.

The validator deliberately reports observable defects only. It must not label an output valid as “semantically guaranteed.”

## Retry Behavior

The first translation uses the configured temperature and repeat penalty. If validation returns any error code:

1. Do not print the rejected first result or expose it to any downstream consumer.
2. Build a repair system message containing the base prompt, pair Skill, stable error codes, source text, and rejected translation.
3. Require a full replacement translation, not a patch or explanation.
4. Retry exactly once with `temperature=0.0`; keep the configured repeat penalty and token limit.
5. Validate the replacement.
6. If the replacement passes, print it.
7. If the replacement fails, print the replacement followed by a visible warning listing the remaining stable error codes. Never start a third model call.

Streaming cannot expose a result before validation. Each attempt will therefore be collected in memory first and printed only after its validation decision. A short status message may indicate that validation or a retry is in progress.

## Configuration

Add these defaults:

```json
{
  "quality_validation": true,
  "quality_retry_limit": 1
}
```

`quality_validation` accepts only the JSON booleans `true` and `false`; every other value is replaced with `true`. `quality_retry_limit` accepts only the JSON integers `0` and `1`; booleans, missing values, strings, negative integers, and integers greater than `1` are replaced with `1`. Existing configuration files remain valid because defaults are merged before use.

## Failure Handling

- A model exception follows the existing exception path and does not trigger a quality retry.
- An output that reaches `max_tokens` is treated as a failed attempt and assigned `OUTPUT_TRUNCATED` before retry.
- A validation implementation exception must not discard a completed translation. The program prints the translation and a warning containing `VALIDATOR_ERROR`; it does not retry because the error is not evidence of a translation defect.
- Validation warnings go to the terminal only. This feature must not restore the previously removed automatic clipboard-copy behavior.

## Tests

Tests will not require loading a GGUF model.

1. Prompt-routing tests prove that ordinary and mixed routes contain the base contract and their pair-specific Skill.
2. Static Skill-contract tests prove every pair file contains all six required section headers and contains none of the prohibited discretionary phrases.
3. Input-normalization tests cover soft wrapping inside `a\npproached`, lowercase continuation, a headline followed by `Tens`, blank paragraphs, bullets, and Markdown headings.
4. Validator tests cover empty output, paragraph loss, headline/body merging, sentence loss, Arabic number changes, `Six` → `六`, `tens of thousands` → `数以万计`, untranslated `authorities`, allowed URLs/code/paths, and a clean Chinese translation.
5. Retry orchestration tests use a fake completion function to prove zero retries for a valid result, exactly one retry for an invalid result, deterministic second-attempt temperature, suppression of the first invalid output, and a warning after a second failure.
6. The Nevada regression fixture must reject the previously observed defective output and accept a complete translation containing separate headline and body lines, `数以万计`, `里诺`, `六人`, and no ordinary English word.
7. Existing installer, model discovery, launcher, and symlink tests must continue to pass.

## Acceptance Criteria

The work is complete only when all conditions are true:

- every translation route composes `base.md` plus at most one pair-specific Skill;
- no Skill contains the prohibited discretionary phrases;
- the Nevada defective outputs supplied by the user fail validation for explicit error codes;
- the correct Nevada translation passes validation;
- an invalid first generation triggers exactly one repair attempt;
- no rejected first generation is displayed or exposed to another consumer;
- all new and existing automated tests pass;
- Python compilation and shell syntax checks pass;
- no network access or external service is required at runtime.
