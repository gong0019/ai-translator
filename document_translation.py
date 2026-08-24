from collections.abc import Callable
import re


_DANGLING_ENGLISH_WORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
    "or", "the", "to", "with", "without",
}


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
