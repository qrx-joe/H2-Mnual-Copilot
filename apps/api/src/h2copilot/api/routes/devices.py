"""设备列表（契约 §1.6：FR-005 设备上下文的数据来源）。"""

from fastapi import APIRouter
from sqlalchemy import select

from h2copilot.core.db import session_scope
from h2copilot.domain.enums import PublishStatus
from h2copilot.domain.models import Device, Document, DocumentVersion

router = APIRouter(prefix="/api/v1", tags=["devices"])


@router.get("/devices")
async def list_devices() -> dict:
    async with session_scope() as session:
        devices = (await session.execute(select(Device).order_by(Device.id))).scalars().all()
        result = []
        for d in devices:
            # current_version：该设备下 ACTIVE 文档的 current 版本（按创建时间取最新）
            ver = (
                await session.execute(
                    select(DocumentVersion.version)
                    .join(Document, Document.id == DocumentVersion.document_id)
                    .where(
                        Document.device_id == d.id,
                        Document.status == PublishStatus.ACTIVE,
                        DocumentVersion.is_current,
                    )
                    .order_by(DocumentVersion.created_at.desc())
                    .limit(1)
                )
            ).first()
            result.append(
                {
                    "device_id": d.id,
                    "name": d.name,
                    "current_version": ver[0] if ver else "",
                }
            )
        return {"devices": result}
