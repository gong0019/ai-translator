"""Shared, safe helpers for maintaining multilingual terminology catalogs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


LANGUAGE_CODES = ("en", "zh", "ja", "ko", "de", "fr", "es", "ru", "it")


def skills_directory() -> Path:
    """Return this checkout's skills directory, independent of its location."""
    directory = Path(__file__).resolve().parents[1] / "skills"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_record(item: Mapping[str, str] | Sequence[str]) -> dict[str, str]:
    if isinstance(item, Mapping):
        return dict(item)
    if len(item) != len(LANGUAGE_CODES):
        raise ValueError(f"expected {len(LANGUAGE_CODES)} fields, received {len(item)}")
    return dict(zip(LANGUAGE_CODES, item, strict=True))


def merge_records(
    existing: Iterable[Mapping[str, str]],
    additions: Iterable[Mapping[str, str] | Sequence[str]],
) -> list[dict[str, str]]:
    """Keep existing records authoritative and append only new English source keys."""
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in (*existing, *additions):
        record = normalize_record(item)
        source = record.get("en", "").strip()
        key = source.casefold()
        if not source or key in seen:
            continue
        seen.add(key)
        merged.append(record)
    return merged


def load_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("terms", [])
    if not isinstance(records, list):
        raise ValueError(f"{path} has no terms list")
    return [normalize_record(item) for item in records if isinstance(item, Mapping)]


def merge_catalog(filename: str, additions: Iterable[Mapping[str, str] | Sequence[str]]) -> int:
    path = skills_directory() / filename
    merged = merge_records(load_records(path), additions)
    path.write_text(
        json.dumps({"terms": merged}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(merged)


def validate_records(
    records: Iterable[Mapping[str, str]],
    required_languages: Sequence[str] = LANGUAGE_CODES,
) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for position, record in enumerate(records, start=1):
        source = record.get("en", "").strip()
        key = source.casefold()
        if not source:
            problems.append(f"record {position} missing language: en")
        elif key in seen:
            problems.append(f"duplicate source term: {source}")
        else:
            seen.add(key)
        for language in required_languages:
            value = record.get(language)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"record {position} missing language: {language}")
    return problems


def validate_catalog(path: Path) -> list[str]:
    return validate_records(load_records(path))
