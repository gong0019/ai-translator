# News Translation Accuracy Design

## Goal

Improve local-model news translation accuracy without enlarging the general prompt. Prioritize complete factual transfer, consistent proper names, exact quantities, and removal of unintended source-language residue. A completed translation must never be hidden by validation.

## Scope

This design replaces the current line-by-line translation flow with a document-aware pipeline. It applies to every supported language pair, with the first regression coverage focused on English-to-Simplified-Chinese news articles.

It does not add online APIs, require a larger model, or promise semantic perfection from a 3B quantized model.

## Pipeline

1. Normalize visual line wrapping while preserving real paragraphs, headings, lists, and quotations.
2. Detect likely truncated input before generation. A long English input ending in a partial token, dangling function word, or unfinished sentence produces a clear confirmation prompt; the model must not silently invent the missing ending.
3. Extract document terminology candidates deterministically: person names, abbreviated surnames, place names, organizations, publications, acronyms, currencies, time-zone abbreviations, and repeated technical terms.
4. Build one compact document glossary. Known entries use a local curated mapping; unknown proper names use one constrained model planning call. Planning output is parsed and validated before use. All chunks share the same glossary.
5. Choose translation granularity from the available context budget:
   - Translate a short article in one request.
   - Split a long article only at paragraph boundaries.
   - Never translate individual visual lines as independent documents.
6. Translate with a compact base contract, the relevant language-pair rules, and only the current document glossary.
7. Validate structure, quantities, glossary consistency, target-script residue, and generation truncation.
8. Retry only the defective chunk once with a concise defect-specific instruction. Do not include unrelated regression examples or the full rejected article in the repair prompt.
9. Always display the final translation. Never replace a paragraph with internal error codes. If a defect remains, show one short user-facing review note naming the concrete text, not validator identifiers.

## Prompt Design

The base prompt is reduced to these durable requirements:

- Translate all source information exactly once.
- Preserve paragraph order, headings, quotations, numbers, units, dates, times, modality, negation, and uncertainty.
- Follow the supplied document glossary exactly.
- Do not summarize, explain, censor, or complete missing source text.
- Output only the translation.

Language-pair Skills contain grammar and script rules only. Fixed article-specific examples such as Reno, Nevada, and the wildfire regression are removed from runtime prompts and retained only as tests.

## Terminology

The glossary planner receives only extracted candidates, not the entire translation contract. Its result has a strict mapping shape and must preserve every source key. Related forms are linked so that `Scott Bessent` and `Bessent` resolve to `斯科特·贝森特` and `贝森特` consistently.

Curated mappings cover stable news terms that models often mishandle, including major news agencies, publications, international organizations, geographic names, currencies, and time zones. Curated entries remain small and data-driven rather than being embedded in prompts.

If glossary planning fails or returns malformed data, translation continues with validated curated entries and exact acronym preservation. It must not crash or fabricate mappings.

## Chunking and Context Budget

The planner reserves context for the system prompt, glossary, and output. A document that fits safely is translated whole. Otherwise, consecutive complete paragraphs are grouped until the safe input budget is reached. Every chunk carries the same glossary; the preceding translated text is not copied into later prompts.

This removes the current contradiction where the prompt demands document-wide consistency but each line is translated without knowledge of the rest of the article.

## Validation and Repair

Validation remains deterministic and advisory:

- Arabic digits and equivalent target-language numerals compare by numeric value.
- Source glossary entries must use their selected target rendering consistently.
- Unexpected Latin residue in Chinese is reported by exact token.
- Paragraph and sentence coverage is checked without requiring identical punctuation style.
- A `length` finish reason marks only that chunk for repair.

The repair request contains the source chunk, its translation, the document glossary, and concrete defects such as `Reuters was left untranslated`. It does not expose internal codes to the user. After one repair, the application displays the result even if a defect remains.

## User Experience

- Normal output remains clean and contains the complete translation.
- Likely truncated input asks for confirmation before translation.
- Internal validation names never appear in normal mode.
- A remaining problem is described concretely, for example: `可能仍有未翻译内容：Reuters`.
- Quality validation and one targeted retry remain enabled by default.

## Tests

Regression coverage includes:

- The Nevada wildfire article for heading separation, quantities, and place-name consistency.
- The house-of-terror article for Chinese numeral equivalence, BBC preservation, and complete paragraph output.
- The Iran article for `Bessent`, `Reuters`, `Strait of Hormuz`, `BST`, `$4`, and truncated `ahead of th` input.
- Short-document whole translation and long-document paragraph chunking.
- Shared glossary use across chunks.
- Malformed glossary fallback.
- Targeted repair of one defective chunk without regenerating valid chunks.
- Final output remains visible after a failed repair and contains no internal error codes.

## Success Criteria

- The same entity has one selected rendering throughout a document.
- Known numeric, currency, date, time, and time-zone facts remain unchanged in meaning.
- Valid source acronyms may remain; unintended ordinary Latin words do not pass silently.
- Incomplete source endings are not invented without user confirmation.
- Runtime prompts are shorter than the current base plus language-pair prompt.
- All existing installation, model-selection, launcher, and translation tests continue to pass.
