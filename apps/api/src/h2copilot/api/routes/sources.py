"""溯源路由（契约 §1.4）：citation → 原始文档定位信息 + PDF 文件流。"""

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from h2copilot.core.db import session_scope
from h2copilot.domain.models import Chunk, Document, DocumentVersion
from h2copilot.ingestion.storage import LocalFSStorage

router = APIRouter(prefix="/api/v1", tags=["sources"])


@router.get("/sources/{chunk_id}")
async def get_source(chunk_id: uuid.UUID) -> dict:
    async with session_scope() as session:
        chunk = await session.get(Chunk, chunk_id)
        if chunk is None:
            raise HTTPException(status_code=404, detail="chunk 不存在")
        ver = await session.get(DocumentVersion, chunk.document_version_id)
        assert ver is not None
        doc = await session.get(Document, ver.document_id)
        assert doc is not None
        return {
            "document": doc.title,
            "document_id": str(doc.id),
            "version": ver.version,
            "page": chunk.page_number,
            "section_path": chunk.section_path,
            "excerpt": chunk.content[:200],
            # 前端 Source Viewer 用它加载原始 PDF 并跳页（T-020）
            "file_url": f"/api/v1/files/{ver.id}",
        }


@router.get("/files/{version_id}")
async def get_file(version_id: uuid.UUID) -> Response:
    """原始 PDF 流（Source Viewer iframe 直接消费；MVP 不做签名 URL，Phase 7 部署前评估）。"""
    async with session_scope() as session:
        ver = await session.get(DocumentVersion, version_id)
        if ver is None or not ver.storage_key:
            raise HTTPException(status_code=404, detail="文件不存在")
        key = ver.storage_key
    storage = LocalFSStorage()
    if not await storage.exists(key):
        raise HTTPException(status_code=404, detail=f"对象存储缺文件：{key}")
    data = await storage.get(key)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},  # 浏览器内嵌展示，不触发下载
    )
