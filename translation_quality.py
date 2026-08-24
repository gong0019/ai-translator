"""Deterministic source normalization and translation quality checks."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable

from document_translation import format_glossary


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
_ARABIC_NUMBER = re.compile(r"(?<![A-Za-z0-9_.])\d+(?:,\d{3})*(?:\.\d+)?")
_CHINESE_NUMBER = re.compile(r"[零〇一二两三四五六七八九十百千万亿]+")
_CHINESE_DECIMAL = re.compile(
    r"(?:百分之)?(?P<integer>[零〇一二两三四五六七八九十百千万亿]+)"
    r"点(?P<fraction>[零〇一二两三四五六七八九]+)"
)
_CHINESE_QUANTITY_SUFFIX = re.compile(
    r"(?:[%％]|人|名|位|个|只|条|件|项|次|岁|年|月|天|日|周|时|分|秒|"
    r"小时|分钟|个月|家|国|所|辆|吨|克|千克|米|公里|元|万元|美元|英镑|"
    r"欧元|倍)"
)
_CHINESE_QUANTITY_PREFIX = re.compile(
    r"(?:第|约|近|超过|不足|人民币|美元|英镑|欧元|[$￥¥£€]|百分之)$"
)
_SOURCE_ACRONYM = re.compile(
    r"\b(?:[A-Z]{2,5}|[A-Z]{1,6}(?:-\d{1,3}|\d{1,3}))\b"
)
_ORDINARY_UPPERCASE_WORDS = {
    "ALERT",
    "BREAKING",
    "EXCLUSIVE",
    "LIVE",
    "NEWS",
    "UPDATE",
    "URGENT",
}
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
    review_notes: tuple[str, ...] = ()


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
        boundaries = re.findall(r"(?<!\d)\.(?!\d)|[!?。！？]+", line)
        units += len(boundaries) if boundaries else 1
    return units


def _arabic_numbers(text: str) -> list[str]:
    translated = text.translate(_FULLWIDTH_DIGITS)
    return [match.group(0).replace(",", "") for match in _ARABIC_NUMBER.finditer(translated)]


def _parse_chinese_integer(token: str) -> int:
    digits = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    units = {"十": 10, "百": 100, "千": 1000, "万": 10_000, "亿": 100_000_000}
    if not any(char in units for char in token):
        return int("".join(str(digits[char]) for char in token))

    total = 0
    section = 0
    number = 0
    for char in token:
        if char in digits:
            number = digits[char]
            continue
        unit = units[char]
        if unit < 10_000:
            section += (number or 1) * unit
        else:
            section += number
            total += (section or 1) * unit
            section = 0
        number = 0
    return total + section + number


def _numeric_candidates(text: str) -> list[tuple[int, int | str, bool]]:
    normalized = text.translate(_FULLWIDTH_DIGITS)
    candidates: list[tuple[int, int | str, bool]] = []
    occupied: list[tuple[int, int]] = []
    for match in _ARABIC_NUMBER.finditer(normalized):
        token = match.group(0).replace(",", "")
        value: int | str = int(token) if "." not in token else token
        candidates.append((match.start(), value, True))
        occupied.append(match.span())
    decimal_digits = {
        "零": "0",
        "〇": "0",
        "一": "1",
        "二": "2",
        "两": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
    }
    for match in _CHINESE_DECIMAL.finditer(normalized):
        integer = _parse_chinese_integer(match.group("integer"))
        fraction = "".join(decimal_digits[char] for char in match.group("fraction"))
        candidates.append((match.start(), f"{integer}.{fraction}", True))
        occupied.append(match.span())
    for match in _CHINESE_NUMBER.finditer(normalized):
        start, end = match.span()
        if any(start < used_end and end > used_start for used_start, used_end in occupied):
            continue
        token = match.group(0)
        strict_extra = len(token) > 1 and bool(
            _CHINESE_QUANTITY_SUFFIX.match(normalized[end:])
            or _CHINESE_QUANTITY_PREFIX.search(normalized[:start])
        )
        candidates.append((match.start(), _parse_chinese_integer(token), strict_extra))
    return sorted(candidates)


def _has_arabic_number_mismatch(source: str, output: str) -> bool:
    remaining_output = output.translate(_FULLWIDTH_DIGITS)
    for concept in _english_number_concepts(source):
        remaining_output, _ = _consume_number_equivalent(remaining_output, concept)

    expected = [int(token) if "." not in token else token for token in _arabic_numbers(source)]
    candidates = _numeric_candidates(remaining_output)
    position = 0
    for expected_value in expected:
        while position < len(candidates) and candidates[position][1] != expected_value:
            position += 1
        if position == len(candidates):
            return True
        candidates.pop(position)

    return any(strict_extra for _, _, strict_extra in candidates)


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
    acronyms = {
        acronym
        for acronym in _SOURCE_ACRONYM.findall(source)
        if acronym not in _ORDINARY_UPPERCASE_WORDS
    }
    for acronym in acronyms:
        cleaned = cleaned.replace(acronym, " ")
    return cleaned


def find_unexpected_latin_tokens(source: str, output: str) -> tuple[str, ...]:
    """Return distinct target-script residuals that are not allowed spans."""
    cleaned = _remove_allowed_protected_spans(source, output)
    return tuple(dict.fromkeys(_LATIN_TOKEN.findall(cleaned)))


def find_missing_glossary_terms(
    source: str,
    output: str,
    glossary: dict[str, str],
) -> tuple[str, ...]:
    """Return required mappings missing after longest source terms are claimed."""
    occupied: list[tuple[int, int]] = []
    matches: list[tuple[int, str, str]] = []
    for source_term, target_term in sorted(
        glossary.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        prefix = r"(?<!\w)" if source_term[:1].isalnum() else ""
        suffix = r"(?!\w)" if source_term[-1:].isalnum() else ""
        pattern = prefix + re.escape(source_term) + suffix
        for match in re.finditer(pattern, source):
            start, end = match.span()
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            matches.append((start, source_term, target_term))

    remaining_output = output
    missing: list[str] = []
    for _, source_term, target_term in sorted(
        matches,
        key=lambda item: (-len(item[1]), item[0]),
    ):
        position = remaining_output.find(target_term)
        if position >= 0:
            remaining_output = (
                remaining_output[:position]
                + (" " * len(target_term))
                + remaining_output[position + len(target_term):]
            )
            continue
        mapping = f"{source_term} => {target_term}"
        if mapping not in missing:
            missing.append(mapping)
    return tuple(missing)


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

    if _has_arabic_number_mismatch(normalized_source, normalized_output):
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
    glossary: dict[str, str],
) -> tuple[str, ...]:
    errors = validate_translation(source, result.text, target_code)
    if find_missing_glossary_terms(source, result.text, glossary):
        errors.append("GLOSSARY_TERM_MISSING")
    if result.truncated and "OUTPUT_TRUNCATED" not in errors:
        errors.append("OUTPUT_TRUNCATED")
    return tuple(errors)


def _concrete_defects(
    source: str,
    output: str,
    target_code: str,
    glossary: dict[str, str],
    errors: tuple[str, ...],
) -> tuple[str, ...]:
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
    instructions = {
        "EMPTY_OUTPUT": "Provide a complete translation; the current translation is empty.",
        "PARAGRAPH_COUNT_MISMATCH": "Preserve all source paragraphs in the same order.",
        "LINE_STRUCTURE_LOSS": "Preserve every meaningful source line.",
        "SENTENCE_COUNT_LOSS": "Restore every missing source sentence.",
        "ARABIC_NUMBER_MISMATCH": (
            "Preserve every source number exactly and do not add numbers."
        ),
        "ENGLISH_NUMBER_MISMATCH": (
            "Preserve every source number exactly and do not add numbers."
        ),
        "OUTPUT_TRUNCATED": "Complete the translation; the previous output was truncated.",
    }
    for error in errors:
        instruction = instructions.get(error)
        if instruction and instruction not in defects:
            defects.append(instruction)
    return tuple(defects)


def _user_review_notes(
    source: str,
    output: str,
    target_code: str,
    glossary: dict[str, str],
    errors: tuple[str, ...],
) -> tuple[str, ...]:
    notes = []
    tokens: tuple[str, ...] = ()
    if target_code == "zh":
        tokens = find_unexpected_latin_tokens(source, output)
        if tokens:
            notes.append("可能仍有未翻译内容：" + "、".join(tokens))
    missing_terms = find_missing_glossary_terms(source, output, glossary)
    if missing_terms and not tokens:
        notes.append("可能未使用指定术语：" + "、".join(missing_terms))
    if "EMPTY_OUTPUT" in errors:
        notes.append("译文为空，请人工检查。")
    if any(
        error in errors
        for error in (
            "PARAGRAPH_COUNT_MISMATCH",
            "LINE_STRUCTURE_LOSS",
            "SENTENCE_COUNT_LOSS",
        )
    ):
        notes.append("可能存在结构或内容缺失，请人工检查。")
    if any(
        error in errors
        for error in ("ARABIC_NUMBER_MISMATCH", "ENGLISH_NUMBER_MISMATCH")
    ):
        notes.append("可能存在数字不一致，请人工检查。")
    if "OUTPUT_TRUNCATED" in errors:
        notes.append("译文可能被截断，请人工检查。")
    return tuple(notes)


def _repair_messages(
    system_prompt: str,
    source: str,
    rejected: str,
    defects: tuple[str, ...],
    glossary: dict[str, str],
) -> list[dict[str, str]]:
    sections = [
        "Correct only the defects listed below while preserving every other translated fact."
        + ("\n" + "\n".join(f"- {defect}" for defect in defects) if defects else "")
    ]
    glossary_text = format_glossary(glossary)
    if glossary_text:
        sections.append(glossary_text)
    sections.extend(
        (
            f"SOURCE CHUNK:\n{source}",
            f"CURRENT TRANSLATION:\n{rejected}",
            "Return the complete corrected translation only.",
        )
    )
    repair_request = "\n\n".join(sections)
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
    glossary: dict[str, str] | None = None,
) -> QualityOutcome:
    """Generate, validate, and perform no more than one repair attempt."""
    chunk_glossary = glossary or {}
    first_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": source},
    ]
    first_result = complete(first_messages, temperature)
    if not validation_enabled:
        return QualityOutcome(first_result.text, (), False)

    try:
        first_errors = _validation_errors(
            source,
            first_result,
            target_code,
            chunk_glossary,
        )
    except Exception:
        return QualityOutcome(first_result.text, ("VALIDATOR_ERROR",), False)

    if not first_errors:
        return QualityOutcome(first_result.text, (), False)
    if retry_limit != 1:
        return QualityOutcome(
            first_result.text,
            first_errors,
            False,
            _user_review_notes(
                source,
                first_result.text,
                target_code,
                chunk_glossary,
                first_errors,
            ),
        )

    second_result = complete(
        _repair_messages(
            system_prompt,
            source,
            first_result.text,
            _concrete_defects(
                source,
                first_result.text,
                target_code,
                chunk_glossary,
                first_errors,
            ),
            chunk_glossary,
        ),
        0.0,
    )
    try:
        second_errors = _validation_errors(
            source,
            second_result,
            target_code,
            chunk_glossary,
        )
    except Exception:
        return QualityOutcome(second_result.text, ("VALIDATOR_ERROR",), True)
    return QualityOutcome(
        second_result.text,
        second_errors,
        True,
        _user_review_notes(
            source,
            second_result.text,
            target_code,
            chunk_glossary,
            second_errors,
        ),
    )
