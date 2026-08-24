from collections.abc import Callable
import json
import re


_DANGLING_ENGLISH_WORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
    "or", "the", "to", "with", "without",
}

_SENTENCE_STARTERS = {
    "A", "An", "The", "One", "He", "She", "It", "They", "This", "That",
}
_CAPITALIZED_TERM_RE = re.compile(
    r"\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:\s+(?:(?:[a-z]+)\s+)?(?:[A-Z][a-z]+|[A-Z]{2,}))*\b"
)
_FENCED_JSON_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def extract_term_candidates(text: str) -> tuple[str, ...]:
    candidates = []
    for match in _CAPITALIZED_TERM_RE.finditer(text):
        words = match.group().split()
        while words and words[0] in _SENTENCE_STARTERS:
            words.pop(0)
        candidate = " ".join(words)
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return tuple(candidates)


def load_curated_terms(path: str, pair_key: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as terms_file:
        data = json.load(terms_file)
    terms = data.get(pair_key, {})
    if not isinstance(terms, dict):
        return {}
    return {
        source: target
        for source, target in terms.items()
        if isinstance(source, str) and isinstance(target, str) and target.strip()
    }


def parse_glossary_response(
    response: str,
    candidates: tuple[str, ...],
    curated: dict[str, str],
) -> dict[str, str]:
    json_text = response.strip()
    fenced_match = _FENCED_JSON_RE.fullmatch(json_text)
    if fenced_match:
        json_text = fenced_match.group(1).strip()
    try:
        proposed = json.loads(json_text)
    except json.JSONDecodeError:
        proposed = {}
    if not isinstance(proposed, dict):
        proposed = {}
    requested = set(candidates)
    glossary = {
        source: target
        for source, target in proposed.items()
        if source in requested
        and isinstance(source, str)
        and isinstance(target, str)
        and target.strip()
    }
    glossary.update(
        {
            source: target
            for source, target in curated.items()
            if source in requested and isinstance(target, str) and target.strip()
        }
    )
    return glossary


def format_glossary(glossary: dict[str, str]) -> str:
    if not glossary:
        return ""
    return "DOCUMENT GLOSSARY:\n" + "\n".join(
        f"- {source} => {target}" for source, target in glossary.items()
    )


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


def plan_paragraph_chunks(
    text: str,
    count_tokens: Callable[[str], int],
    max_source_tokens: int,
) -> list[str]:
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
