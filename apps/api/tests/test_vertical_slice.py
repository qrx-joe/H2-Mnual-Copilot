"""垂直切片集成测试（真实 Postgres + Fake 模型替身）。

覆盖 T-008 验收形态：上传索引 → 问答成功路径 → 拒答失败路径。
模型层为 Fake（确定性替身）：这证明数据层/接口层真实贯通，
不构成真实模型集成证据（等 Q-010）。
"""

import uuid

import httpx
import pymupdf
import pytest
from httpx import ASGITransport
from sqlalchemy import text

from h2copilot.api.app import app
from h2copilot.core.config import get_settings
from h2copilot.core.db import dispose_engine, get_engine
from h2copilot.domain.enums import DocumentType, TrustLevel
from h2copilot.domain.models import Device, Document, DocumentVersion, IngestionJob
from h2copilot.ingestion.pipeline import run_ingestion, sha256_bytes

pytestmark = pytest.mark.integration


def _make_manual(path, pages: list[list[str]]) -> bytes:
    """构造合成手册 PDF：每页一组 (heading, body) 文本。"""
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        y = 72
        for i, ln in enumerate(lines):
            page.insert_text((72, y), ln, fontsize=16 if i == 0 else 10)
            y += 24 if i == 0 else 16
    doc.save(str(path))
    doc.close()
    return path.read_bytes()


@pytest.fixture(autouse=True)
def _test_database():
    """切到 h2copilot_test 库并跑迁移；测试间清空业务表保证隔离。"""
    import os

    base = os.environ.get("DATABASE_URL", "postgresql+asyncpg://h2copilot:h2copilot@localhost:5432/h2copilot")
    os.environ["DATABASE_URL"] = base.rsplit("/", 1)[0] + "/h2copilot_test"
    get_settings.cache_clear()

    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    yield

    get_settings.cache_clear()
    import asyncio

    asyncio.get_event_loop_policy()
    # 事件循环由 pytest-asyncio 管理；这里只清缓存，引擎由每个测试自行关闭
    os.environ["DATABASE_URL"] = base
    get_settings.cache_clear()


async def _truncate() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE citations, feedback, messages, conversations, chunks, "
                "ingestion_jobs, document_versions, documents, devices CASCADE"
            )
        )


async def _ingest_manual(pdf_bytes: bytes, device_id: str, title: str, version: str) -> None:
    """直接走 ingestion 管线（等价于 HTTP 上传后的后台任务）。"""
    import tempfile
    from pathlib import Path

    from h2copilot.core.db import session_scope

    async with session_scope() as session:
        session.add(Device(id=device_id, name=device_id.upper()))
        doc = Document(
            device_id=device_id,
            title=title,
            document_type=DocumentType.MAINTENANCE,
            trust_level=TrustLevel.A_OFFICIAL,
        )
        session.add(doc)
        await session.flush()
        ver = DocumentVersion(
            document_id=doc.id,
            version=version,
            file_hash=sha256_bytes(pdf_bytes),
            storage_key="test.pdf",
        )
        session.add(ver)
        await session.flush()
        job = IngestionJob(document_version_id=ver.id)
        session.add(job)
        await session.commit()
        job_id, ver_id = str(job.id), str(ver.id)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        pdf_path = Path(tmp.name)
    await run_ingestion(job_id, ver_id, pdf_path)

    async with session_scope() as session:
        job_row = await session.get(IngestionJob, uuid.UUID(job_id))
        assert job_row is not None
        assert job_row.status.value == "READY", f"ingestion 失败: {job_row.error}"


@pytest.fixture
async def client():
    await _truncate()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await dispose_engine()


MANUAL_PAGES = [
    [
        "7.4 Error Code E104",
        "E104 - Cooling system temperature abnormal.",
        "Inspect coolant level and circulation pump operating state before escalation.",
    ],
    [
        "3.2 Pre-start Checklist",
        "Complete the cooling, feed-water, gas-line, power and safety-interlock pre-start checks.",
    ],
]


def _parse_sse(resp_text: str) -> list[tuple[str, dict]]:
    import json

    events = []
    for block in resp_text.strip().split("\n\n"):
        lines = block.split("\n")
        ev = next(line[7:] for line in lines if line.startswith("event: "))
        data = next(json.loads(line[6:]) for line in lines if line.startswith("data: "))
        events.append((ev, data))
    return events


async def test_vertical_slice_success_and_abstain(tmp_path, client: httpx.AsyncClient) -> None:
    # 1) 索引合成手册
    pdf = tmp_path / "hx100-maintenance.pdf"
    data = _make_manual(pdf, MANUAL_PAGES)
    await _ingest_manual(data, "hx100", "HX-100 Maintenance Manual", "2.1")

    # 2) 成功路径：E104 → 证据 + 引用带页码
    resp = await client.post("/api/v1/query", json={"query": "E104", "device_id": "hx100"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    names = [n for n, _ in events]
    assert names[0] == "retrieval.started"
    assert "retrieval.completed" in names and "done" in names

    done = dict(events)["done"]
    assert done["intent"] == "ERROR_CODE"
    assert done["answer"]["abstain"] is False
    assert done["answer"]["evidence_status"] in ("SUFFICIENT", "PARTIAL")
    cits = done["answer"]["citations"]
    assert len(cits) >= 1
    assert cits[0]["page"] == 1  # V-2 页码溯源：E104 在第 1 页
    assert cits[0]["document_title"] == "HX-100 Maintenance Manual"
    assert cits[0]["version"] == "2.1"

    # 3) 失败路径：知识库外问题 → 明确拒答（FR-006）
    resp2 = await client.post(
        "/api/v1/query", json={"query": "HX-100 采购价格", "device_id": "hx100"}
    )
    events2 = _parse_sse(resp2.text)
    done2 = dict(events2)["done"]
    assert done2["answer"]["abstain"] is True
    assert done2["answer"]["evidence_status"] == "INSUFFICIENT"
    assert done2["answer"]["citations"] == []


async def test_device_scoping(client: httpx.AsyncClient, tmp_path) -> None:
    """FR-005：A 设备的资料不得回答 B 设备的问题。"""
    pdf = tmp_path / "hx100.pdf"
    data = _make_manual(pdf, MANUAL_PAGES[:1])
    await _ingest_manual(data, "hx100", "HX-100 Maintenance Manual", "2.1")

    resp = await client.post("/api/v1/query", json={"query": "E104", "device_id": "hx80"})
    events = _parse_sse(resp.text)
    done = dict(events)["done"]
    assert done["answer"]["abstain"] is True  # hx80 知识库为空 → 拒答
