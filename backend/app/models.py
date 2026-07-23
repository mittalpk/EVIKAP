"""
Database Session, Engine & Migration Infrastructure (US-005).

Provides async SQLAlchemy engine setup, session management, and table models for:
- Source (registry entity)
- Chunk (vector/semantic entity with Graph-Ready metadata: parent_doc_id, references)
- PermissionCache (permission caching model)
"""

import os
from typing import AsyncGenerator, Dict, List, Optional
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",  # In-memory default fallback for tests
)

# Replace postgresql:// or postgres:// with postgresql+asyncpg:// if postgres URL is passed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


class Source(Base):
    """Source entity backing FR-007 and Data Architecture §5."""

    __tablename__ = "sources"

    id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # github_repo, confluence_wiki, database_schema
    endpoint_url = Column(Text, nullable=False)
    secret_reference = Column(String(255), nullable=False)
    owner_email = Column(String(255), nullable=False)
    sensitivity_level = Column(String(50), nullable=False, default="internal-general")
    sensitivity_signed_off = Column(Boolean, nullable=False, default=False)
    refresh_cadence_minutes = Column(Integer, nullable=False, default=1440)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)

    chunks = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")



class Chunk(Base):
    """Chunk entity storing vector embeddings and Graph-Ready metadata (parent_doc_id, references)."""

    __tablename__ = "chunks"

    id = Column(String(100), primary_key=True)
    source_id = Column(String(100), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(255), nullable=False)
    parent_doc_id = Column(String(255), nullable=True)  # Graph-Ready: section/parent hierarchy
    content = Column(Text, nullable=False)
    permissions_ref = Column(String(255), nullable=True)

    checksum = Column(String(64), nullable=False)
    
    # Store references as JSON string or comma-separated string for multi-DB compatibility (SQLite + Postgres)
    references_json = Column(Text, nullable=True, default="[]")
    
    # Text field for vector string representation (pgvector vector(1536) in PostgreSQL)
    embedding_vector_str = Column(Text, nullable=True)

    last_indexed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    source = relationship("Source", back_populates="chunks")


    __table_args__ = (
        Index("idx_chunks_source_id", "source_id"),
        Index("idx_chunks_permissions_ref", "permissions_ref"),
        Index("idx_chunks_parent_doc_id", "parent_doc_id"),
    )


class PermissionCacheModel(Base):
    """PermissionCache entity backing FR-006 and ADR-001."""

    __tablename__ = "permission_cache"

    cache_id = Column(String(100), primary_key=True)
    requester_identity = Column(String(255), nullable=False)
    source_id = Column(String(100), nullable=False)
    access_level = Column(String(50), nullable=False, default="read")
    granted_acl_refs_json = Column(Text, nullable=False, default="[]")
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ttl_seconds = Column(Integer, nullable=False, default=900)

    __table_args__ = (
        Index("idx_perm_cache_identity_source", "requester_identity", "source_id"),
    )


class EvaluationCase(Base):
    """EvaluationCase entity backing US-009, US-021, and Data Architecture §5."""

    __tablename__ = "evaluation_cases"

    id = Column(String(100), primary_key=True)
    query = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    expected_chunk_ids_json = Column(Text, nullable=False, default="[]")
    source_type = Column(String(50), nullable=False)  # github_repo, confluence_wiki, cross_source
    tags_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


async def init_db():

    """Helper to initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for FastAPI / application database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
