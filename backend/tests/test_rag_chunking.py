from app.rag.chunking import chunk_markdown


def test_chunk_markdown_splits_on_h2_headings():
    text = """\
## First Section

Some content here.
More content.

## Second Section

Different content.
"""
    chunks = chunk_markdown(text)

    assert len(chunks) == 2
    assert chunks[0] == ("First Section", "Some content here.\nMore content.")
    assert chunks[1] == ("Second Section", "Different content.")


def test_chunk_markdown_discards_preamble_before_first_heading():
    text = "Some intro text with no heading.\n\n## Real Section\n\nBody text.\n"
    chunks = chunk_markdown(text)

    assert len(chunks) == 1
    assert chunks[0][0] == "Real Section"


def test_chunk_markdown_skips_empty_sections():
    text = "## Empty Section\n\n## Real Section\n\nHas content.\n"
    chunks = chunk_markdown(text)

    assert len(chunks) == 1
    assert chunks[0][0] == "Real Section"


def test_chunk_markdown_returns_empty_list_for_no_headings():
    assert chunk_markdown("Just plain text, no headings at all.") == []
