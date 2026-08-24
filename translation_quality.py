"""Deterministic source normalization and translation quality checks."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable


_SENTENCE_FINAL = tuple(".!?。！？:：;；")
_STRUCTURAL_PREFIX = re.compile(
    r"^(?:[#>*+-]\s|\d+[.)]\s|[-+*]\s|[\"'“‘（(\[]|[A-ZÀ-Þ])"
)
_WORD_WRAP_SUFFIXES = {
    "able",
    "al",
    "ed",
    "er",
    "est",
    "ible",
    "ing",
    "ion",
    "ive",
    "ly",
    "ment",
    "ness",
    "ous",
    "s",
    "tion",
}
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
_ARABIC_NUMBER = re.compile(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?")
_LATIN_TOKEN = re.compile(r"[A-Za-z]+")
_PROTECTED_PATTERNS = (
    re.compile(r"```[\s\S]*?```"),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"https?://[^\s<>\]\[(){}\"'，。！？；：]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\w)(?:\.\.?/|/)[^\s<>\"'，。！？；：]+"),
    re.compile(r"\b[A-Za-z]:\\[^\s<>\"'，。！？；：]+"),
    re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"),
    re.compile(r"\{\{?[A-Za-z_][A-Za-z0-9_.-]*\}\}?"),
)

_ENGLISH_NUMBER_VALUES = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_CHINESE_NUMBER_VALUES = {
    0: "零",
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
    11: "十一",
    12: "十二",
    13: "十三",
    14: "十四",
    15: "十五",
    16: "十六",
    17: "十七",
    18: "十八",
    19: "十九",
    20: "二十",
    30: "三十",
    40: "四十",
    50: "五十",
    60: "六十",
    70: "七十",
    80: "八十",
    90: "九十",
}
_MAGNITUDE_EQUIVALENTS = {
    "hundreds": ("数百",),
    "hundreds_of_thousands": ("数十万",),
    "thousands": ("数千",),
    "tens_of_thousands": ("数以万计", "数万"),
    "millions": ("数百万",),
    "billions": ("数十亿",),
    "hundred": ("百",),
    "thousand": ("千",),
    "million": ("百万",),
    "billion": ("十亿",),
}


@dataclass(frozen=True)
class CompletionResult:
    text: str
    truncated: bool = False


@dataclass(frozen=True)
class QualityOutcome:
    text: str
    errors: tuple[str, ...]
    retried: bool


def _begins_structural_line(line: str) -> bool:
    return bool(_STRUCTURAL_PREFIX.match(line.lstrip()))


def _ends_inside_word(previous: str, current: str) -> bool:
    """Recognize single-letter prefixes and standalone suffix wrap fragments."""
    previous_match = re.search(r"([a-z])$", previous)
    current_match = re.match(r"([a-z]+)", current.lstrip())
    if not previous_match or not current_match:
        return False
    previous_token = re.search(r"([A-Za-z]+)$", previous)
    if previous_token and len(previous_token.group(1)) == 1:
        return True
    return current_match.group(1).lower() in _WORD_WRAP_SUFFIXES


def _begins_lowercase_continuation(line: str) -> bool:
    return bool(re.match(r"[a-zà-öø-ÿ]", line.lstrip()))


def normalize_source_structure(text: str) -> str:
    """Repair deterministic soft wraps while preserving document structure."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    source_lines = [line.rstrip() for line in normalized.split("\n")]
    output_lines: list[str] = []

    for line in source_lines:
        if not line.strip():
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            continue

        if output_lines and output_lines[-1] != "":
            previous = output_lines[-1]
            if _ends_inside_word(previous, line):
                output_lines[-1] = previous + line.lstrip()
                continue
            if (
                not previous.endswith(_SENTENCE_FINAL)
                and _begins_lowercase_continuation(line)
                and not _begins_structural_line(line)
            ):
                output_lines[-1] = previous.rstrip() + " " + line.lstrip()
                continue

        output_lines.append(line)

    while output_lines and output_lines[-1] == "":
        output_lines.pop()
    return "\n".join(output_lines)


def extract_protected_spans(text: str) -> list[str]:
    """Return only the exact protected span categories from the contract."""
    occupied: list[tuple[int, int]] = []
    spans: list[tuple[int, str]] = []
    for pattern in _PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            spans.append((start, match.group(0)))
    return [value for _, value in sorted(spans)]


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _meaningful_lines(paragraph: str) -> list[str]:
    return [line.strip() for line in paragraph.splitlines() if line.strip()]


def _sentence_units(paragraph: str) -> int:
    units = 0
    for line in _meaningful_lines(paragraph):
        boundaries = re.findall(r"[.!?。！？]+", line)
        units += len(boundaries) if boundaries else 1
    return units


def _arabic_numbers(text: str) -> list[str]:
    translated = text.translate(_FULLWIDTH_DIGITS)
    return [match.group(0).replace(",", "") for match in _ARABIC_NUMBER.finditer(translated)]


def _english_number_concepts(text: str) -> list[object]:
    lowered = text.lower()
    concepts: list[tuple[int, object]] = []
    occupied: list[tuple[int, int]] = []
    phrase_patterns = (
        (r"\btens\s+of\s+thousands\b", "tens_of_thousands"),
        (r"\bhundreds\s+of\s+thousands\b", "hundreds_of_thousands"),
        (r"\bhundreds\b", "hundreds"),
        (r"\bthousands\b", "thousands"),
        (r"\bmillions\b", "millions"),
        (r"\bbillions\b", "billions"),
        (r"\bhundred\b", "hundred"),
        (r"\bthousand\b", "thousand"),
        (r"\bmillion\b", "million"),
        (r"\bbillion\b", "billion"),
    )
    for pattern, concept in phrase_patterns:
        for match in re.finditer(pattern, lowered):
            start, end = match.span()
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            concepts.append((start, concept))

    word_pattern = re.compile(r"\b(" + "|".join(_ENGLISH_NUMBER_VALUES) + r")\b")
    for match in word_pattern.finditer(lowered):
        start, end = match.span()
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        concepts.append((start, _ENGLISH_NUMBER_VALUES[match.group(1)]))
    return [concept for _, concept in sorted(concepts)]


def _consume_number_equivalent(output: str, concept: object) -> tuple[str, bool]:
    if isinstance(concept, int):
        equivalents = (str(concept), _CHINESE_NUMBER_VALUES[concept])
    else:
        equivalents = _MAGNITUDE_EQUIVALENTS[str(concept)]
    positions = [
        (output.find(value), value)
        for value in equivalents
        if output.find(value) >= 0
    ]
    if not positions:
        return output, False
    position, value = min(positions, key=lambda item: item[0])
    return output[:position] + (" " * len(value)) + output[position + len(value):], True


def _has_english_number_mismatch(source: str, output: str) -> bool:
    remaining = output.translate(_FULLWIDTH_DIGITS)
    for concept in _english_number_concepts(source):
        remaining, found = _consume_number_equivalent(remaining, concept)
        if not found:
            return True
    return False


def _remove_allowed_protected_spans(source: str, output: str) -> str:
    allowed = set(extract_protected_spans(source))
    cleaned = output
    for span in extract_protected_spans(output):
        if span in allowed:
            cleaned = cleaned.replace(span, " ")
    return cleaned


def validate_translation(source: str, output: str, target_code: str) -> list[str]:
    """Return stable codes for deterministic, observable translation defects."""
    if not output.strip():
        return ["EMPTY_OUTPUT"]

    normalized_source = normalize_source_structure(source)
    normalized_output = normalize_source_structure(output)
    source_paragraphs = _paragraphs(normalized_source)
    output_paragraphs = _paragraphs(normalized_output)
    errors: list[str] = []

    if len(source_paragraphs) != len(output_paragraphs):
        errors.append("PARAGRAPH_COUNT_MISMATCH")

    if any(
        len(_meaningful_lines(source_part)) >= 2
        and len(_meaningful_lines(output_part)) < len(_meaningful_lines(source_part))
        for source_part, output_part in zip(source_paragraphs, output_paragraphs)
    ):
        errors.append("LINE_STRUCTURE_LOSS")

    if any(
        _sentence_units(output_part) < _sentence_units(source_part)
        for source_part, output_part in zip(source_paragraphs, output_paragraphs)
    ):
        errors.append("SENTENCE_COUNT_LOSS")

    if _arabic_numbers(normalized_source) != _arabic_numbers(normalized_output):
        errors.append("ARABIC_NUMBER_MISMATCH")

    if _has_english_number_mismatch(normalized_source, normalized_output):
        errors.append("ENGLISH_NUMBER_MISMATCH")

    if target_code == "zh":
        unprotected_output = _remove_allowed_protected_spans(
            normalized_source,
            normalized_output,
        )
        if _LATIN_TOKEN.search(unprotected_output):
            errors.append("TARGET_SCRIPT_RESIDUAL")

    return errors


def normalize_quality_settings(
    validation_value: object,
    retry_value: object,
) -> tuple[bool, int]:
    """Accept only JSON-compatible booleans and integer retry limits."""
    validation_enabled = validation_value if type(validation_value) is bool else True
    retry_limit = (
        retry_value
        if type(retry_value) is int and retry_value in (0, 1)
        else 1
    )
    return validation_enabled, retry_limit


def _validation_errors(
    source: str,
    result: CompletionResult,
    target_code: str,
) -> tuple[str, ...]:
    errors = validate_translation(source, result.text, target_code)
    if result.truncated and "OUTPUT_TRUNCATED" not in errors:
        errors.append("OUTPUT_TRUNCATED")
    return tuple(errors)


def _repair_messages(
    system_prompt: str,
    source: str,
    rejected: str,
    errors: tuple[str, ...],
) -> list[dict[str, str]]:
    repair_request = (
        "The previous translation failed deterministic validation.\n"
        f"ERROR_CODES: {', '.join(errors)}\n\n"
        "SOURCE_TEXT:\n"
        f"{source}\n\n"
        "REJECTED_TRANSLATION:\n"
        f"{rejected}\n\n"
        "Return one complete replacement translation. "
        "Do not return a patch, explanation, or analysis."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": repair_request},
    ]


def run_quality_checked_completion(
    source: str,
    target_code: str,
    system_prompt: str,
    complete: Callable[[list[dict[str, str]], float], CompletionResult],
    temperature: float,
    retry_limit: int,
    validation_enabled: bool = True,
) -> QualityOutcome:
    """Generate, validate, and perform no more than one repair attempt."""
    first_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": source},
    ]
    first_result = complete(first_messages, temperature)
    if not validation_enabled:
        return QualityOutcome(first_result.text, (), False)

    try:
        first_errors = _validation_errors(source, first_result, target_code)
    except Exception:
        return QualityOutcome(first_result.text, ("VALIDATOR_ERROR",), False)

    if not first_errors:
        return QualityOutcome(first_result.text, (), False)
    if retry_limit != 1:
        return QualityOutcome(first_result.text, first_errors, False)

    second_result = complete(
        _repair_messages(
            system_prompt,
            source,
            first_result.text,
            first_errors,
        ),
        0.0,
    )
    try:
        second_errors = _validation_errors(source, second_result, target_code)
    except Exception:
        return QualityOutcome(second_result.text, ("VALIDATOR_ERROR",), True)
    return QualityOutcome(second_result.text, second_errors, True)
