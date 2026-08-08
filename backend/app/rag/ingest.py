"""Ingestion pipeline: read knowledge/*.md -> chunk -> embed -> store in Postgres.

Run manually (not on every container start, unlike migrations - this populates
content, it doesn't change schema):

    uv run python -m app.rag.ingest

Safe to re-run: each file's existing chunks are deleted and re-inserted, so editing
a knowledge doc and re-running keeps the DB in sync with the source files.
"""

import asyncio
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.llm.ollama_client import embed_text
from app.models.knowledge_chunk import KnowledgeChunk, KnowledgeDomain
from app.rag.chunking import chunk_markdown

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


async def ingest_file(db: Session, path: Path) -> int:
    domain = KnowledgeDomain(path.stem)  # filename (minus .md) must match a domain value
    text = path.read_text()
    chunks = chunk_markdown(text)

    # Idempotent: clear this file's existing chunks before inserting fresh ones,
    # so re-running after editing a doc doesn't leave stale/duplicate chunks behind.
    db.query(KnowledgeChunk).filter(KnowledgeChunk.source == path.name).delete()

    for title, content in chunks:
        # Embed heading + body together so the heading's topical context influences
        # the vector, not just the body text in isolation.
        embedding = await embed_text(f"{title}\n\n{content}")
        db.add(
            KnowledgeChunk(
                domain=domain,
                source=path.name,
                title=title,
                content=content,
                embedding=embedding,
            )
        )

    db.commit()
    return len(chunks)


async def ingest_all() -> int:
    db = SessionLocal()
    total = 0
    try:
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            count = await ingest_file(db, path)
            print(f"  {path.name}: {count} chunks")
            total += count
    finally:
        db.close()
    return total


if __name__ == "__main__":
    print(f"Ingesting knowledge base from {KNOWLEDGE_DIR} ...")
    total_chunks = asyncio.run(ingest_all())
    print(f"Done: {total_chunks} chunks ingested.")
