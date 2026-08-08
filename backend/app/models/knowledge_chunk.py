import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import Base


class KnowledgeDomain(str, enum.Enum):
    FOOTBALL = "football"
    HYROX = "hyrox"
    BODYBUILDING = "bodybuilding"
    INJURY_PREVENTION = "injury_prevention"


class KnowledgeChunk(Base):
    """One chunk of expert fitness knowledge plus its embedding, for RAG retrieval.

    Chunks come from markdown docs in app/rag/knowledge/<domain>/, split by heading -
    see app/rag/ingest.py.
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[KnowledgeDomain] = mapped_column(Enum(KnowledgeDomain, name="knowledge_domain"))
    source: Mapped[str] = mapped_column(String(200))  # e.g. "football/injury_prevention.md"
    title: Mapped[str] = mapped_column(String(200))  # the heading this chunk came from
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
