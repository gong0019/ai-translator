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
_CAPITALIZED_WORD = r"(?:[A-Z][a-z]+(?:[A-Z][a-z]+)*|[A-Z]{2,})"
_CAPITALIZED_TERM_RE = re.compile(
    rf"\b{_CAPITALIZED_WORD}(?:\s+(?:(?:of|the|and|de|la)\s+)?{_CAPITALIZED_WORD})*\b"
)
_PERSON_WORD_RE = re.compile(rf"^{_CAPITALIZED_WORD}$")
_PERSON_TITLES = {"Sheriff"}
_FENCED_JSON_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)
_SENTENCE_CHUNK_RE = re.compile(r".+?(?:[.!?。！？]+(?:\s+|$)|$)", re.DOTALL)
_FALLBACK_CHUNK_TOKEN_RE = re.compile(
    r"[\u4e00-\u9fff]|[A-Za-z0-9]+|[^\w\s]|\s+"
)


def extract_term_candidates(text: str) -> tuple[str, ...]:
    candidates = []
    for match in _CAPITALIZED_TERM_RE.finditer(text):
        words = match.group().split()
        while words and (words[0] in _SENTENCE_STARTERS or words[0] in _PERSON_TITLES):
            words.pop(0)
        candidate = " ".join(words)
        for item in re.split(r"\s+and\s+", candidate):
            if item and item not in candidates:
                candidates.append(item)
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
    return _add_person_last_name_aliases(glossary)


def _add_person_last_name_aliases(glossary: dict[str, str]) -> dict[str, str]:
    expanded = dict(glossary)
    for source, target in glossary.items():
        source_words = source.split()
        target_words = [word for word in re.split(r"[·・\s]+", target) if word]
        if (
            len(source_words) == 2
            and len(target_words) >= 2
            and all(_PERSON_WORD_RE.fullmatch(word) for word in source_words)
        ):
            expanded.setdefault(source_words[-1], target_words[-1])
    return expanded


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
    stream_each_paragraph: bool = False,
) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if stream_each_paragraph:
        chunks = []
        for paragraph in paragraphs:
            chunks.extend(
                _split_oversized_paragraph(
                    paragraph,
                    count_tokens,
                    max_source_tokens,
                )
            )
        return chunks

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


def _split_oversized_paragraph(
    paragraph: str,
    count_tokens: Callable[[str], int],
    max_source_tokens: int,
) -> list[str]:
    if count_tokens(paragraph) <= max_source_tokens:
        return [paragraph]

    sentences = [part.strip() for part in _SENTENCE_CHUNK_RE.findall(paragraph) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = " ".join((*current, sentence))
        if current and count_tokens(candidate) > max_source_tokens:
            chunks.append(" ".join(current))
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        chunks.append(" ".join(current))

    expanded: list[str] = []
    for chunk in chunks:
        if count_tokens(chunk) <= max_source_tokens:
            expanded.append(chunk)
            continue
        expanded.extend(_split_at_token_boundaries(chunk, count_tokens, max_source_tokens))
    return expanded


def _split_at_token_boundaries(
    text: str,
    count_tokens: Callable[[str], int],
    max_source_tokens: int,
) -> list[str]:
    pieces = _FALLBACK_CHUNK_TOKEN_RE.findall(text)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = current + piece
        if current.strip() and count_tokens(candidate) > max_source_tokens:
            chunks.append(current.strip())
            current = piece.lstrip()
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text]
