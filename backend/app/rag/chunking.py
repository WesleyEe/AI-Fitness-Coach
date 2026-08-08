import re

# Split a markdown doc on level-2 headings ("## Heading") - each section becomes one
# chunk, small enough to stay topically coherent and to fit comfortably in an LLM
# context window later, without splitting mid-thought the way fixed-length chunking can.
_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs, one per '## ' section.

    Text before the first heading (if any) is discarded - our knowledge docs are
    written as pure heading + body sections with no preamble.
    """
    matches = list(_HEADING_RE.finditer(text))
    chunks: list[tuple[str, str]] = []

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            chunks.append((title, body))

    return chunks
