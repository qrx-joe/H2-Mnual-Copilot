"""数据库实体（技术规范 §13–18；约束见 contracts.md §2）。

设计约束：
- Chunk 挂在 DocumentVersion 下（ADR-0004：版本隔离检索）。
- DocumentVersion.file_hash 唯一索引：相同文件不重复解析（技术规范 §16）。
- 同一 Document 至多一个 is_current=True 版本（应用层保证 + 部分唯一索引）。
"""

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from h2copilot.domain.enums import (
    DocumentType,
    ProcessingStatus,
    PublishStatus,
    TrustLevel,
)

# 向量维度固定 1024：与 text-embedding-v4 可配置维度对齐；
# FakeEmbedding 输出同维度，保证切换真实 provider 时无需迁移（§32 向量版本化另行记录）。
EMBEDDING_DIM = 1024


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    manufacturer: Mapped[str] = mapped_column(String(128), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="device")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    title: Mapped[str] = mapped_column(String(256))
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="document_type"))
    language: Mapped[str] = mapped_column(String(16), default="en")
    trust_level: Mapped[TrustLevel] = mapped_column(Enum(TrustLevel, name="trust_level"))
    status: Mapped[PublishStatus] = mapped_column(
        Enum(PublishStatus, name="publish_status"), default=PublishStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped[Device] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", order_by="DocumentVersion.created_at"
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_document_version"),
        # file_hash 唯一：幂等去重（技术规范 §16）
        Index("uq_document_version_file_hash", "file_hash", unique=True),
        # 同文档仅一个 current（ADR-0004）——部分唯一索引
        Index(
            "uq_document_version_current",
            "document_id",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[str] = mapped_column(String(32))
    file_hash: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(256), default="")
    parse_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"), default=ProcessingStatus.UPLOADED
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="versions")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_version_id", "chunk_index", name="uq_chunk_index"),
        Index("ix_chunks_tsv", "tsv", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id"), index=True
    )
    page_number: Mapped[int] = mapped_column(Integer)
    section_path: Mapped[str] = mapped_column(Text, default="")
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    # 词法检索列：'simple' 配置——精确服务于错误代码/型号（EN）；中文分词优化留 Phase 6 评估
    tsv: Mapped[object] = mapped_column(TSVECTOR)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    # 向量版本化（技术规范 §32）：升级 embedding 模型必须重建索引，不得混用
    embedding_model: Mapped[str] = mapped_column(String(64), default="")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    version: Mapped[DocumentVersion] = relationship(back_populates="chunks")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id"), index=True
    )
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"), default=ProcessingStatus.UPLOADED
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    request_id: Mapped[str] = mapped_column(String(32), default="")
    evidence_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(16), default="")
    model_alias: Mapped[str] = mapped_column(String(64), default="")
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    citations: Mapped[list["Citation"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class Citation(Base):
    """引用是数据库实体（技术规范 §18），不是前端拼的字符串。"""

    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id"), index=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    support_type: Mapped[str] = mapped_column(String(16), default="QUOTE")

    message: Mapped[Message] = relationship(back_populates="citations")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = _uuid_pk()
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id"), index=True)
    feedback_type: Mapped[str] = mapped_column(String(32))  # HELPFUL | INCORRECT | SAFETY_CONCERN
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
