"""Deterministic source normalization and translation quality checks."""

from __future__ import annotations

import re


_SENTENCE_FINAL = tuple(".!?。！？:：;；")
_STRUCTURAL_PREFIX = re.compile(
    r"^(?:[#>*+-]\s|\d+[.)]\s|[-+*]\s|[\"'“‘（(\[]|[A-ZÀ-Þ])"
)


def _begins_structural_line(line: str) -> bool:
    return bool(_STRUCTURAL_PREFIX.match(line.lstrip()))


def _ends_inside_word(previous: str, current: str) -> bool:
    """Recognize the narrow single-letter wrap seen in terminal captures."""
    previous_match = re.search(r"([a-z])$", previous)
    current_match = re.match(r"([a-z]+)", current.lstrip())
    if not previous_match or not current_match:
        return False
    previous_token = re.search(r"([A-Za-z]+)$", previous)
    return bool(previous_token and len(previous_token.group(1)) == 1)


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
