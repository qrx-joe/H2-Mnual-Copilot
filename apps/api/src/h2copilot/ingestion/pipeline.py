"""接入编排（技术规范 §19、§75–§76）：hash 去重 → 解析 → 分块 → 向量化 → READY。

MVP 用 FastAPI BackgroundTask 异步执行；状态机推进写库，前端轮询 job。
"""

import hashlib
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update

from h2copilot.core.config import get_settings
from h2copilot.core.db import session_scope
from h2copilot.domain.enums import ProcessingStatus, PublishStatus
from h2copilot.domain.models import Chunk, Document, DocumentVersion, IngestionJob
from h2copilot.ingestion.parser import PyMuPDFParser, chunk_page
from h2copilot.llm.providers import get_embedding_provider


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tsv_expr(content: str) -> Any:
    """词法列：INSERT 时由数据库计算 to_tsvector('simple', :content)（§34）。"""
    return func.to_tsvector("simple", content)


async def _set_statuses(
    job_id: str,
    version_id: str,
    status: ProcessingStatus,
    progress: int,
    error: str | None = None,
) -> None:
    async with session_scope() as session:
        await session.execute(
            update(IngestionJob)
            .where(IngestionJob.id == uuid.UUID(job_id))
            .values(status=status, progress=progress, error=error)
        )
        await session.execute(
            update(DocumentVersion)
            .where(DocumentVersion.id == uuid.UUID(version_id))
            .values(parse_status=status)
        )
        await session.commit()


async def run_ingestion(job_id: str, version_id: str, pdf_path: Path) -> None:
    """后台任务主体：任何一步失败 → FAILED + 错误信息（可重试，新 job）。"""
    parser = PyMuPDFParser()
    embedder = get_embedding_provider(get_settings().embedding_provider)

    try:
        await _set_statuses(job_id, version_id, ProcessingStatus.PARSING, 20)
        parsed = await parser.parse(pdf_path)

        await _set_statuses(job_id, version_id, ProcessingStatus.PARSED, 45)
        pieces: list[tuple[int, str, str]] = []
        for page in parsed.pages:
            pieces.extend(chunk_page(page))
        if not pieces:
            # 疑似扫描件：MinerU fallback 待 Q-011 真实样本到位后接入
            raise ValueError("解析后无有效内容")

        await _set_statuses(job_id, version_id, ProcessingStatus.INDEXING, 60)
        embeddings = await embedder.embed_documents([c[2] for c in pieces])

        async with session_scope() as session:
            for idx, ((page_no, section, content), embedding) in enumerate(
                zip(pieces, embeddings, strict=True)
            ):
                # tsv 用数据库端表达式计算；embedding/页码直接写列
                session.add(
                    Chunk(
                        document_version_id=uuid.UUID(version_id),
                        page_number=page_no,
                        section_path=section,
                        chunk_index=idx,
                        content=content,
                        content_hash=sha256_bytes(content.encode()),
                        token_count=len(content) // 4,
                        tsv=_tsv_expr(content),
                        embedding=embedding,
                        embedding_model=embedder.name,
                    )
                )
            await session.commit()

        await _set_statuses(job_id, version_id, ProcessingStatus.VALIDATING, 90)
        # 校验：chunk 均已入库（引用页码是硬需求，FR-003/007）
        async with session_scope() as session:
            rows = (
                await session.execute(
                    select(Chunk.id).where(Chunk.document_version_id == uuid.UUID(version_id))
                )
            ).fetchall()
            if len(rows) != len(pieces):
                raise ValueError(f"索引校验失败：期望 {len(pieces)} chunk，实际 {len(rows)}")

        await _set_statuses(job_id, version_id, ProcessingStatus.READY, 100)
        # 就绪后激活：DRAFT → ACTIVE，进入默认检索域（§50：DRAFT 不进生产检索）
        async with session_scope() as session:
            ver = await session.get(DocumentVersion, uuid.UUID(version_id))
            assert ver is not None
            doc = await session.get(Document, ver.document_id)
            assert doc is not None
            doc.status = PublishStatus.ACTIVE
            await session.commit()
    except Exception as exc:  # noqa: BLE001 —— 状态机必须捕获一切失败并落库
        await _set_statuses(job_id, version_id, ProcessingStatus.FAILED, 0, str(exc)[:500])


def storage_key_for(file_hash: str, filename: str) -> str:
    return f"{file_hash}/{filename}"
