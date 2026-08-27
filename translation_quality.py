"""Deterministic source normalization and translation quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from collections.abc import Collection, Iterable
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
# 柳叶刀等期刊用中点写小数（0·5）。模型规范成 0.5 是正确的，但逐字解析会把
# 源文读成 [0, 5] 两个数、译文读成一个 0.5，于是正确译文被判为数字不一致。
# 人名分隔号（斯科特·贝森特）不在数字之间，前后向断言已将其排除。
_MIDDLE_DOT_DECIMAL = re.compile(r"(?<=\d)[·・‧](?=\d)")


def _normalize_digits(text: str) -> str:
    return _MIDDLE_DOT_DECIMAL.sub(".", text.translate(_FULLWIDTH_DIGITS))


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
    # 科技文献里的缩略语常带小写前缀（cTKR、rTKR、mRNA）、长于 5 个字母
    # （ISRCTN、RECIST），或与代号、希腊字母连写（RACER-Knee、rVSVΔG-ZEBOV-GP）。
    # 注册号可以很长（NCT04649489、ISRCTN27624068），digits 不能只留 4 位。
    r"(?<![A-Za-z0-9])(?:"
    r"[a-z]{0,2}[A-Z][A-ZΑ-Ω]{1,7}[Α-Ω]?(?:-[A-Za-zΑ-Ω0-9]+)*\d{0,10}"
    r"|[A-Z]{1,6}-?\d{1,10}"
    r")(?![A-Za-z0-9])"
)
# 这些记号在任何目标语言的译文里都照写，与源文是否逐字相同无关：
# 模型常把柳叶刀的中点小数 p<0·0001 规范成 p<0.0001，逐字比对会误判为未翻译。
_NOTATION_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{1,3}\s*[=<>≤≥]\s*[−–-]?[\d.,·]+"),
    re.compile(
        r"(?<![A-Za-z0-9])\d[\d.,·]*\s*"
        r"(?:mg|kg|µg|ng|g|mL|dL|L|IU|mmol|µmol|mmHg|kPa|cm|mm|km|Gy|Sv|Bq)"
        r"(?:/(?:kg|m2|mL|L|day|h|week))?(?![A-Za-z0-9])"
    ),
    re.compile(
        r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9-]*\.(?:gov|org|com|net|edu|int)"
        r"(?![A-Za-z0-9])"
    ),
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
    # 统计记号（n=154、p=0·62、p<0.001）在中文科技译文里照写不译。
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{1,3}\s*[=<>≤≥]\s*[−–-]?[\d.·]+"),
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
_MAGNITUDE_LATIN_EQUIVALENTS = {
    "hundreds": ("hundreds",),
    "hundreds_of_thousands": ("hundreds of thousands",),
    "thousands": ("thousands",),
    "tens_of_thousands": ("tens of thousands",),
    "millions": ("millions",),
    "billions": ("billions",),
    "hundred": ("hundred",),
    "thousand": ("thousand",),
    "million": ("million",),
    "billion": ("billion",),
}
_LATIN_NUMBER_WORDS = {
    value: word for word, value in reversed(list(_ENGLISH_NUMBER_VALUES.items()))
}
_LATIN_MAGNITUDE_PATTERNS = (
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
# 长短语必须先匹配，否则"数以万计"会被"数万"之外的短模式切碎。
_CHINESE_MAGNITUDE_PATTERNS = (
    ("数以万计", "tens_of_thousands"),
    ("数十万", "hundreds_of_thousands"),
    ("数百万", "millions"),
    ("数十亿", "billions"),
    ("数万", "tens_of_thousands"),
    ("数千", "thousands"),
    ("数百", "hundreds"),
)
_CHINESE_MAGNITUDE_FACTORS = {"百": 100, "千": 1000, "万": 10_000, "亿": 100_000_000}
_ARABIC_MAGNITUDE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([百千万亿])")
# 月份名译成数字（August 15 -> 8月15日）会在译文里凭空多出一个数字。
# 只匹配首字母大写的形式，避免把 may、march 这类普通词当成月份。
_MONTH_NUMBERS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
_MONTH_NAMES = {number: name for name, number in _MONTH_NUMBERS.items()}
# 量词前的 2 在中文里写作"两"（两组、两例），只认"二"会误判正确译文。
# _parse_chinese_integer 早已把"两"读作 2，等价物表必须与之一致。
_CHINESE_NUMBER_ALTERNATES = {2: ("两",)}
_MONTH_NAME_RE = re.compile(r"\b(" + "|".join(_MONTH_NUMBERS) + r")\b")
# "8月" 是月份，"12个月" 是时长，量词 个 把两者区分开。
_CHINESE_MONTH_RE = re.compile(r"(?<!\d)(\d{1,2})\s*月")
_CJK_TOKEN = re.compile(r"[一-鿿぀-ゟ゠-ヿ가-힯]")
_CJK_TARGETS = frozenset({"zh", "ja", "ko"})


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


def _overlaps(occupied: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < used_end and end > used_start for used_start, used_end in occupied)


def _arabic_magnitude_spans(text: str) -> list[tuple[int, int, int | str]]:
    """Resolve digit-plus-magnitude compounds such as ``3万`` into 30000.

    Reading the digit alone reports a correct conversion (``3万`` -> ``30,000``)
    as a defect, and reading the magnitude alone invents a second number.
    """
    spans: list[tuple[int, int, int | str]] = []
    for match in _ARABIC_MAGNITUDE_RE.finditer(text):
        scaled = float(match.group(1)) * _CHINESE_MAGNITUDE_FACTORS[match.group(2)]
        value: int | str = int(scaled) if scaled.is_integer() else str(scaled)
        spans.append((match.start(), match.end(), value))
    return spans


def _month_spans(text: str) -> list[tuple[int, int, int]]:
    """Locate month expressions in either script.

    ``August`` and ``8月`` denote the same month, but one is a word and the other
    a digit, so counting them as plain numbers makes every translated date look
    like an added or missing number.
    """
    spans = [
        (match.start(), match.end(), _MONTH_NUMBERS[match.group(1)])
        for match in _MONTH_NAME_RE.finditer(text)
    ]
    for match in _CHINESE_MONTH_RE.finditer(text):
        number = int(match.group(1))
        if 1 <= number <= 12:
            spans.append((match.start(), match.end(), number))
    return spans


def _arabic_number_values(text: str) -> list[int | str]:
    normalized = _normalize_digits(text)
    entries: list[tuple[int, int | str]] = []
    occupied: list[tuple[int, int]] = [
        (start, end) for start, end, _ in _month_spans(normalized)
    ]
    for start, end, value in _arabic_magnitude_spans(normalized):
        entries.append((start, value))
        occupied.append((start, end))
    for match in _ARABIC_NUMBER.finditer(normalized):
        start, end = match.span()
        if _overlaps(occupied, start, end):
            continue
        token = match.group(0).replace(",", "")
        entries.append((start, int(token) if "." not in token else token))
    return [value for _, value in sorted(entries)]


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
    normalized = _normalize_digits(text)
    candidates: list[tuple[int, int | str, bool]] = []
    occupied: list[tuple[int, int]] = [
        (start, end) for start, end, _ in _month_spans(normalized)
    ]
    for start, end, value in _arabic_magnitude_spans(normalized):
        candidates.append((start, value, True))
        occupied.append((start, end))
    for match in _ARABIC_NUMBER.finditer(normalized):
        start, end = match.span()
        if _overlaps(occupied, start, end):
            continue
        token = match.group(0).replace(",", "")
        value: int | str = int(token) if "." not in token else token
        candidates.append((start, value, True))
        occupied.append((start, end))
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
        if _overlaps(occupied, start, end):
            continue
        token = match.group(0)
        strict_extra = len(token) > 1 and bool(
            _CHINESE_QUANTITY_SUFFIX.match(normalized[end:])
            or _CHINESE_QUANTITY_PREFIX.search(normalized[:start])
        )
        candidates.append((match.start(), _parse_chinese_integer(token), strict_extra))
    return sorted(candidates)


def _has_arabic_number_mismatch(source: str, output: str, target_code: str) -> bool:
    remaining_output = _normalize_digits(output)
    for concept in _spelled_number_concepts(source):
        remaining_output, _ = _consume_number_equivalent(
            remaining_output, concept, target_code
        )

    candidates = _numeric_candidates(remaining_output)
    for expected_value in _arabic_number_values(source):
        # 译文重排数字是正常语序差异，按多重集比对而不是按出现顺序。
        for position, (_, value, _strict) in enumerate(candidates):
            if value == expected_value:
                candidates.pop(position)
                break
        else:
            return True

    return any(strict_extra for _, _, strict_extra in candidates)


def _spelled_number_concepts(text: str) -> list[object]:
    """Collect number words and magnitude phrases from either script."""
    # 中点小数替换为等长的句点，因此位置偏移仍然有效。
    text = _normalize_digits(text)
    concepts: list[tuple[int, object]] = []
    occupied: list[tuple[int, int]] = [
        (start, end) for start, end, _ in _arabic_magnitude_spans(text)
    ]
    lowered = text.lower()
    for pattern, concept in _LATIN_MAGNITUDE_PATTERNS:
        for match in re.finditer(pattern, lowered):
            start, end = match.span()
            if _overlaps(occupied, start, end):
                continue
            occupied.append((start, end))
            concepts.append((start, concept))

    for phrase, concept in _CHINESE_MAGNITUDE_PATTERNS:
        for match in re.finditer(re.escape(phrase), text):
            start, end = match.span()
            if _overlaps(occupied, start, end):
                continue
            occupied.append((start, end))
            concepts.append((start, concept))

    for start, end, number in _month_spans(text):
        if _overlaps(occupied, start, end):
            continue
        occupied.append((start, end))
        concepts.append((start, ("month", number)))

    word_pattern = re.compile(r"\b(" + "|".join(_ENGLISH_NUMBER_VALUES) + r")\b")
    for match in word_pattern.finditer(lowered):
        start, end = match.span()
        if _overlaps(occupied, start, end):
            continue
        occupied.append((start, end))
        concepts.append((start, _ENGLISH_NUMBER_VALUES[match.group(1)]))

    for match in _CHINESE_NUMBER.finditer(text):
        start, end = match.span()
        if _overlaps(occupied, start, end):
            continue
        # 只接受带量词或数量前缀的中文数字，放过"千万不要""一一回应"这类成语。
        if not (
            _CHINESE_QUANTITY_SUFFIX.match(text[end:])
            or _CHINESE_QUANTITY_PREFIX.search(text[:start])
        ):
            continue
        occupied.append((start, end))
        concepts.append((start, _parse_chinese_integer(match.group(0))))
    return [concept for _, concept in sorted(concepts)]


def _numeric_equivalents(concept: object, target_code: str) -> tuple[str, ...]:
    """Accept only spellings that are legitimate in the target language.

    Counting an English numeral as satisfied by the English word would let an
    untranslated ``Six`` pass the number check on a Chinese translation.
    """
    spells_cjk = target_code in _CJK_TARGETS
    if isinstance(concept, tuple) and concept[0] == "month":
        number = concept[1]
        if spells_cjk:
            return (f"{number}月", f"{_CHINESE_NUMBER_VALUES[number]}月")
        return (_MONTH_NAMES[number],)
    if not isinstance(concept, int):
        key = str(concept)
        return (
            _MAGNITUDE_EQUIVALENTS[key]
            if spells_cjk
            else _MAGNITUDE_LATIN_EQUIVALENTS[key]
        )
    equivalents = [str(concept)]
    spelled = (_CHINESE_NUMBER_VALUES if spells_cjk else _LATIN_NUMBER_WORDS).get(
        concept
    )
    if spelled:
        equivalents.append(spelled)
    if spells_cjk:
        equivalents.extend(_CHINESE_NUMBER_ALTERNATES.get(concept, ()))
    return tuple(equivalents)


def _find_equivalent(output: str, value: str) -> int:
    """Locate an equivalent without matching inside a longer word or number.

    The head and tail need separate guards. A bare ``2`` must not be taken from
    inside ``75.2`` — that leaves ``75.`` behind and invents a number — while
    ``8月`` ends in a CJK character and must still match when a day follows it.
    """
    if not value[:1].isascii() or not value[:1].isalnum():
        return output.find(value)

    def guard(char: str, lookbehind: bool) -> str:
        direction = "<" if lookbehind else ""
        if char.isdigit():
            return f"(?{direction}![A-Za-z0-9.,·])"
        if char.isascii() and char.isalpha():
            return f"(?{direction}![A-Za-z])"
        return ""

    pattern = (
        guard(value[0], True) + re.escape(value) + guard(value[-1], False)
    )
    match = re.search(pattern, output, re.IGNORECASE)
    return match.start() if match else -1


def _consume_number_equivalent(
    output: str, concept: object, target_code: str
) -> tuple[str, bool]:
    positions = [
        (found, value)
        for found, value in (
            (_find_equivalent(output, value), value)
            for value in _numeric_equivalents(concept, target_code)
        )
        if found >= 0
    ]
    if not positions:
        return output, False
    position, value = min(positions, key=lambda item: item[0])
    return output[:position] + (" " * len(value)) + output[position + len(value):], True


def _has_spelled_number_mismatch(source: str, output: str, target_code: str) -> bool:
    remaining = _normalize_digits(output)
    for concept in _spelled_number_concepts(source):
        remaining, found = _consume_number_equivalent(remaining, concept, target_code)
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
    for acronym in sorted(acronyms, key=len, reverse=True):
        # 必须按词边界替换：裸 str.replace 会把 RECIST 里的 CI 挖成 "RE ST"。
        cleaned = re.sub(
            r"(?<![A-Za-z0-9])" + re.escape(acronym) + r"(?![A-Za-z0-9])",
            " ",
            cleaned,
        )
    for pattern in _NOTATION_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)
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


def has_excessive_previous_translation_overlap(
    previous_output: str,
    output: str,
) -> bool:
    """Detect accidental reuse of a substantial part of the prior chunk."""
    previous = re.sub(r"[\W_]+", "", previous_output)
    current = re.sub(r"[\W_]+", "", output)
    if min(len(previous), len(current)) < 12:
        return False
    longest_match = SequenceMatcher(None, previous, current).find_longest_match().size
    return longest_match >= 12 and longest_match / min(len(previous), len(current)) >= 0.45


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

    if _has_arabic_number_mismatch(normalized_source, normalized_output, target_code):
        errors.append("ARABIC_NUMBER_MISMATCH")

    if _has_spelled_number_mismatch(normalized_source, normalized_output, target_code):
        errors.append("SPELLED_NUMBER_MISMATCH")

    unprotected_output = _remove_allowed_protected_spans(
        normalized_source,
        normalized_output,
    )
    if target_code == "zh":
        if _LATIN_TOKEN.search(unprotected_output):
            errors.append("TARGET_SCRIPT_RESIDUAL")
    elif target_code not in _CJK_TARGETS and _CJK_TOKEN.search(unprotected_output):
        # 日语和韩语目标可以合法使用汉字，只有非 CJK 目标才算残留。
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
    previous_output: str,
) -> tuple[str, ...]:
    errors = validate_translation(source, result.text, target_code)
    if find_missing_glossary_terms(source, result.text, glossary):
        errors.append("GLOSSARY_TERM_MISSING")
    if result.truncated and "OUTPUT_TRUNCATED" not in errors:
        errors.append("OUTPUT_TRUNCATED")
    if has_excessive_previous_translation_overlap(previous_output, result.text):
        errors.append("CROSS_CHUNK_REPETITION")
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
        "SPELLED_NUMBER_MISMATCH": (
            "Preserve every source number exactly and do not add numbers."
        ),
        "OUTPUT_TRUNCATED": "Complete the translation; the previous output was truncated.",
        "CROSS_CHUNK_REPETITION": (
            "Translate only the current source chunk; do not repeat the prior chunk."
        ),
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
        for error in ("ARABIC_NUMBER_MISMATCH", "SPELLED_NUMBER_MISMATCH")
    ):
        notes.append("可能存在数字不一致，请人工检查。")
    if "OUTPUT_TRUNCATED" in errors:
        notes.append("译文可能被截断，请人工检查。")
    if "CROSS_CHUNK_REPETITION" in errors:
        notes.append("当前段可能重复了上一段，请人工检查。")
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
    previous_output: str = "",
    advisory_terms: Iterable[str] = (),
    retryable_errors: Collection[str] | None = None,
) -> QualityOutcome:
    """Generate, validate, and keep one repair only when it strictly improves.

    ``advisory_terms`` name glossary entries the model proposed rather than ones
    curated by hand. A miss on those is reported to the reader but never forces a
    repair, because an isolated dictionary gloss is often wrong in context.

    ``retryable_errors`` restricts which defects are worth a second generation.
    Residue and glossary misses are the two that most often turn out to be
    correct on inspection, so a long document can decline to redo a chunk for
    them while still redoing one whose figures changed.
    """
    chunk_glossary = glossary or {}
    advisory = frozenset(advisory_terms)
    enforced_glossary = {
        source_term: target_term
        for source_term, target_term in chunk_glossary.items()
        if source_term not in advisory
    }

    def outcome(text: str, errors: tuple[str, ...], retried: bool) -> QualityOutcome:
        return QualityOutcome(
            text,
            errors,
            retried,
            _user_review_notes(source, text, target_code, chunk_glossary, errors),
        )

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
            enforced_glossary,
            previous_output,
        )
    except Exception:
        return QualityOutcome(first_result.text, ("VALIDATOR_ERROR",), False)

    if not first_errors:
        return QualityOutcome(first_result.text, (), False)
    worth_retrying = (
        first_errors
        if retryable_errors is None
        else tuple(error for error in first_errors if error in retryable_errors)
    )
    if retry_limit != 1 or not worth_retrying:
        return outcome(first_result.text, first_errors, False)

    second_result = complete(
        _repair_messages(
            system_prompt,
            source,
            first_result.text,
            _concrete_defects(
                source,
                first_result.text,
                target_code,
                enforced_glossary,
                worth_retrying,
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
            enforced_glossary,
            previous_output,
        )
    except Exception:
        # 无法证明重译更好时保留第一次结果，宁可不改也不要改坏。
        return outcome(first_result.text, first_errors, True)

    if set(second_errors) < set(first_errors):
        return outcome(second_result.text, second_errors, True)
    # 重译没有严格减少缺陷，可能是模型把修复指令当原文翻译了，丢弃它。
    return outcome(first_result.text, first_errors, True)
