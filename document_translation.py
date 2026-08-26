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
    rf"\b{_CAPITALIZED_WORD}(?:[ \t]+(?:(?:of|the|and|de|la)[ \t]+)?{_CAPITALIZED_WORD})*\b"
)
_ACRONYM_RE = re.compile(r"[A-Z]{2,}")
_PERSON_WORD_RE = re.compile(rf"^{_CAPITALIZED_WORD}$")
_PERSON_TITLES = {"Sheriff"}
# 标题式大写（Title Case）的整行会让正则吃下整条标题，产出
# "Power Bottleneck Becomes National Priority" 这类伪术语。真实专有名词
# 极少超过三个词，用词数上限把标题片段挡在外面。
_MAX_TERM_WORDS = 3
# 术语规划要模型逐条生成 JSON 译名，是全流程最慢的一次生成。候选词多时只送
# 信息量最高的一批，其余交给行内翻译处理。
MAX_PLANNED_TERMS = 12
# 只有两行的段落才是"标题 + 正文"这一种会整段丢失的形态。更多行通常是列表，
# 逐行翻译会让每个条目各付一次完整提示词的代价。
_MAX_SPLIT_LINES = 2
_FENCED_JSON_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)
# CJK 句号后不跟空格，必须单独成组；拉丁句点仍要求空白或行尾，
# 否则 "3.5" 和 "U.S." 会被误切。
_SENTENCE_CHUNK_RE = re.compile(r".+?(?:[。！？]+\s*|[.!?]+(?:\s+|$)|$)", re.DOTALL)
_FALLBACK_CHUNK_TOKEN_RE = re.compile(
    r"[\u4e00-\u9fff]|[A-Za-z0-9]+|[^\w\s]|\s+"
)


def _opens_a_sentence(text: str, start: int) -> bool:
    """Report whether a match sits where any word would be capitalized anyway."""
    prefix = text[:start].rstrip(" \t")
    return not prefix or prefix[-1] in ".!?\n"


def extract_term_candidates(text: str) -> tuple[str, ...]:
    """Collect glossary candidates from capitalized spans.

    A lone word that is capitalized only because it opens a sentence is not
    evidence of terminology, so it is kept only when the same word also appears
    mid-sentence or inside a multi-word candidate. Without this, ordinary words
    such as ``Only`` or ``Meanwhile`` become mandatory glossary entries and every
    natural rendering is then reported as a missing term.
    """
    order: list[str] = []
    attested: set[str] = set()
    for match in _CAPITALIZED_TERM_RE.finditer(text):
        words = match.group().split()
        opens_sentence = _opens_a_sentence(text, match.start())
        while words and (words[0] in _SENTENCE_STARTERS or words[0] in _PERSON_TITLES):
            words.pop(0)
            opens_sentence = False
        candidate = " ".join(words)
        for position, item in enumerate(re.split(r"\s+and\s+", candidate)):
            if not item:
                continue
            if item not in order:
                order.append(item)
            if position or not opens_sentence:
                attested.add(item)
            if " " in item:
                attested.update(item.split())
                # 整条标题式大写会被词数上限挡掉，但其中的缩略语是可靠术语，
                # 单独留下（DOE Announces Loan Commitment -> DOE）。
                for word in item.split():
                    if _ACRONYM_RE.fullmatch(word) and word not in order:
                        order.append(word)
    return tuple(
        item
        for item in order
        if (
            len(item.split()) <= _MAX_TERM_WORDS
            and (" " in item or _ACRONYM_RE.fullmatch(item) or item in attested)
        )
    )


def rank_planning_candidates(
    candidates: tuple[str, ...], text: str
) -> tuple[str, ...]:
    """Keep only the candidates a plan can actually help with.

    A planned glossary exists to hold one rendering steady across chunks, so it
    is worth nothing for a term that occurs once — the model simply translates
    it in place. Requiring a repeat also discards the title-case fragments that
    headline-heavy copy produces ("Settlement Over", "In the News"), which would
    otherwise crowd out the real entities.
    """
    counted = []
    for term in candidates:
        prefix = r"(?<!\w)" if term[:1].isalnum() else ""
        suffix = r"(?!\w)" if term[-1:].isalnum() else ""
        flags = re.IGNORECASE if term.isascii() else 0
        occurrences = len(re.findall(prefix + re.escape(term) + suffix, text, flags))
        if occurrences >= 2:
            counted.append((occurrences, len(term.split()), len(term), term))
    counted.sort(reverse=True)
    return tuple(term for *_, term in counted[:MAX_PLANNED_TERMS])


def load_curated_terms(path: str, pair_key: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as terms_file:
        data = json.load(terms_file)
    if isinstance(data.get("terms"), list):
        try:
            source_code, target_code = pair_key.split("_to_", 1)
        except ValueError:
            return {}
        return {
            record[source_code]: record[target_code]
            for record in data["terms"]
            if isinstance(record, dict)
            and isinstance(record.get(source_code), str)
            and isinstance(record.get(target_code), str)
            and record[source_code].strip()
            and record[target_code].strip()
        }
    terms = data.get(pair_key, {})
    if not isinstance(terms, dict):
        return {}
    return {
        source: target
        for source, target in terms.items()
        if isinstance(source, str) and isinstance(target, str) and target.strip()
    }


def match_curated_terms(text: str, terms: dict[str, str]) -> dict[str, str]:
    """Return only curated entries that occur as complete source terms."""
    matches = {}
    for source, target in terms.items():
        if not source:
            continue
        prefix = r"(?<!\w)" if source[:1].isalnum() else ""
        suffix = r"(?!\w)" if source[-1:].isalnum() else ""
        flags = re.IGNORECASE if source.isascii() else 0
        if re.search(prefix + re.escape(source) + suffix, text, flags):
            matches[source] = target
    return matches


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


def last_sentence(text: str, limit: int = 180) -> str:
    """Return the final sentence, shortened from the left if it is very long."""
    parts = [part.strip() for part in _SENTENCE_CHUNK_RE.findall(text.strip()) if part.strip()]
    if not parts:
        return ""
    tail = parts[-1]
    return tail if len(tail) <= limit else "…" + tail[-limit:]


def format_previous_context(source_tail: str, translation_tail: str) -> str:
    """Carry one sentence of context so pronouns and tense survive a chunk break.

    Only the final sentence is passed, and it is labelled as already translated,
    because handing over a whole paragraph invites the model to translate it a
    second time.
    """
    if not source_tail or not translation_tail:
        return ""
    return (
        "PRECEDING CONTEXT — already translated. Use it only to keep pronouns, "
        "tense, and wording consistent. Do not translate or repeat it.\n"
        f"- source: {source_tail}\n"
        f"- translation: {translation_tail}"
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


def plan_translation_units(
    text: str,
    count_tokens: Callable[[str], int],
    max_source_tokens: int,
) -> list[tuple[str, str]]:
    """Split the document into one translation unit per source line.

    Returns ``(unit_text, separator)`` pairs, where the separator is what to emit
    before the unit's translation: ``""`` to continue the current line, ``"\\n"``
    for the next line of the same paragraph, ``"\\n\\n"`` for a new paragraph.

    A paragraph that holds a heading line plus a body line is the one shape a
    small model reliably collapses — it renders the heading and silently drops
    the body. Translating each line on its own removes that choice, and the
    preceding-context block keeps the heading visible while the body is done.

    Splitting is limited to two-line paragraphs. Doing it to every
    paragraph turns a bullet list into one model call per bullet, and each call
    re-processes the whole system prompt, so a long newsletter costs several
    times what it should.
    """
    units: list[tuple[str, str]] = []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        groups = (
            [[line] for line in lines]
            if 2 <= len(lines) <= _MAX_SPLIT_LINES
            else _batch_lines(lines, count_tokens, max_source_tokens)
        )
        for group_index, group in enumerate(groups):
            block = "\n".join(group)
            pieces = _split_oversized_paragraph(block, count_tokens, max_source_tokens)
            for piece_index, piece in enumerate(pieces):
                if not units:
                    separator = ""
                elif piece_index:
                    separator = ""
                elif group_index:
                    separator = "\n"
                else:
                    separator = "\n\n"
                units.append((piece, separator))
    return units


def _batch_lines(
    lines: list[str],
    count_tokens: Callable[[str], int],
    max_source_tokens: int,
) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        candidate = "\n".join((*current, line))
        if current and count_tokens(candidate) > max_source_tokens:
            groups.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append(current)
    return groups


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
