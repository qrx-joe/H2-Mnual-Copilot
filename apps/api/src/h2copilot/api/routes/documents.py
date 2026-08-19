"""文档管理与接入路由（契约 §1.2/§1.3）。

鉴权（技术规范 §62）：上传/管理需要 X-Admin-Password。
开发便利：ADMIN_PASSWORD 未配置时放行并在日志告警（生产必须配置）。
"""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select

from h2copilot.core.config import get_settings
from h2copilot.core.db import session_scope
from h2copilot.domain.enums import DocumentType, TrustLevel
from h2copilot.domain.models import Device, Document, DocumentVersion, IngestionJob
from h2copilot.ingestion.pipeline import (
    run_ingestion,
    sha256_bytes,
    storage_key_for,
)
from h2copilot.ingestion.storage import LocalFSStorage

router = APIRouter(prefix="/api/v1", tags=["documents"])
logger = logging.getLogger("h2copilot.documents")

MAX_PDF_BYTES = 50 * 1024 * 1024  # §65：PDF only MVP，≤50MB


async def require_admin(x_admin_password: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_password
    if not expected:
        logger.warning("ADMIN_PASSWORD 未配置：管理接口在开发模式下放行（生产必须配置）")
        return
    if x_admin_password != expected:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED_ADMIN")


class DocumentCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    document_type: DocumentType
    language: str = Field(default="en", max_length=16)
    trust_level: TrustLevel = TrustLevel.A_OFFICIAL


@router.post("/documents", status_code=201, dependencies=[Depends(require_admin)])
async def create_document(body: DocumentCreate) -> dict:
    async with session_scope() as session:
        device = await session.get(Device, body.device_id)
        if device is None:
            raise HTTPException(status_code=400, detail="设备不存在：请先创建设备")
        doc = Document(
            device_id=body.device_id,
            title=body.title,
            document_type=body.document_type,
            language=body.language,
            trust_level=body.trust_level,
        )
        session.add(doc)
        await session.commit()
        return {"document_id": str(doc.id), "status": doc.status.value}


@router.get("/documents")
async def list_documents() -> dict:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(Document, DocumentVersion)
                .join(DocumentVersion, DocumentVersion.document_id == Document.id, isouter=True)
                .order_by(Document.created_at)
            )
        ).fetchall()
        docs = []
        for doc, ver in rows:
            docs.append(
                {
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "device_id": doc.device_id,
                    "type": doc.document_type.value,
                    "language": doc.language,
                    "trust_level": doc.trust_level.value,
                    "status": doc.status.value,
                    "version": ver.version if ver else None,
                    "parse_status": ver.parse_status.value if ver else None,
                    "is_current": ver.is_current if ver else None,
                }
            )
        return {"documents": docs}


@router.post(
    "/documents/{document_id}/ingest",
    status_code=202,
    dependencies=[Depends(require_admin)],
)
async def ingest_document(
    document_id: uuid.UUID,
    file: UploadFile,
    version: str = "1.0",
    background_tasks: BackgroundTasks = None,  # type: ignore[assignment]
) -> dict:
    # 文件校验（§65）：扩展名 + 大小上限；MIME 由魔数复核
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 上传（PDF only MVP）")
    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="文件超过 50MB 上限")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="MIME 校验失败：内容不是 PDF")

    file_hash = sha256_bytes(data)

    async with session_scope() as session:
        doc = await session.get(Document, document_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        existing = (
            await session.execute(
                select(DocumentVersion).where(DocumentVersion.file_hash == file_hash)
            )
        ).first()
        if existing is not None:
            return {
                "job_id": None,
                "document_version_id": str(existing[0].id),
                "deduplicated": True,
                "message": "相同 file_hash 已索引，按幂等规则复用（§16）",
            }

        ver = DocumentVersion(
            document_id=doc.id,
            version=version,
            file_hash=file_hash,
            storage_key=storage_key_for(file_hash, file.filename or "doc.pdf"),
            is_current=True,
        )
        session.add(ver)
        await session.flush()

        job = IngestionJob(document_version_id=ver.id)
        session.add(job)
        await session.commit()

        job_id, version_id = str(job.id), str(ver.id)

    # 原始文件入对象存储（ADR-0007），临时文件交给后台解析任务
    storage = LocalFSStorage()
    await storage.put(storage_key_for(file_hash, file.filename or "doc.pdf"), data)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    background_tasks.add_task(run_ingestion, job_id, version_id, tmp_path)
    return {"job_id": job_id, "document_version_id": version_id, "deduplicated": False}


@router.get("/ingestion-jobs/{job_id}")
async def get_job(job_id: uuid.UUID) -> dict:
    async with session_scope() as session:
        job = await session.get(IngestionJob, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job 不存在")
        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "progress": job.progress,
            "error": job.error,
        }
