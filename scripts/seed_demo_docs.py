# -*- coding: utf-8 -*-
"""把 PRD §48 演示文档集灌入开发库（复用 evals/datasets/build_docs.py 的合成手册）。

用途：本地演示/视觉验证时让 Knowledge、Ask、Source Viewer 有真实形态的数据。
行为：清空并重建 documents 相关表（与 evals/run_eval.py 的重置一致），Fake 模型链路、无外部调用。
运行（apps/api 环境下）：uv run --no-project python scripts/seed_demo_docs.py
"""

import asyncio
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals" / "datasets"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api" / "src"))

from build_docs import DOCS, build_pdf_bytes  # noqa: E402


async def seed() -> None:
    from sqlalchemy import text

    from h2copilot.core.db import session_scope
    from h2copilot.domain.enums import DocumentType, TrustLevel
    from h2copilot.domain.models import Device, Document, DocumentVersion, IngestionJob
    from h2copilot.ingestion.pipeline import run_ingestion, sha256_bytes
    from h2copilot.ingestion.storage import LocalFSStorage

    async with session_scope() as session:
        await session.execute(
            text("TRUNCATE ingestion_jobs, document_versions, documents, devices CASCADE")
        )
        await session.commit()

    for doc_def in DOCS:
        pdf_bytes = build_pdf_bytes(doc_def["pages"])
        async with session_scope() as session:
            if await session.get(Device, doc_def["device_id"]) is None:
                session.add(Device(id=doc_def["device_id"], name="HX-100 Electrolyzer"))
                await session.flush()
            doc = Document(
                device_id=doc_def["device_id"],
                title=doc_def["title"],
                document_type=DocumentType(doc_def["document_type"]),
                trust_level=TrustLevel.A_OFFICIAL,
            )
            session.add(doc)
            await session.flush()
            ver = DocumentVersion(
                document_id=doc.id,
                version=doc_def["version"],
                file_hash=sha256_bytes(pdf_bytes),
                storage_key=f"eval/{doc_def['title']}.pdf",
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
        await LocalFSStorage().put(f"eval/{doc_def['title']}.pdf", pdf_bytes)

        async with session_scope() as session:
            job_row = await session.get(IngestionJob, uuid.UUID(job_id))
            assert job_row is not None and job_row.status.value == "READY", (
                f"ingestion failed for {doc_def['title']}: "
                f"{job_row.error if job_row else 'missing'}"
            )
        print(f"READY: {doc_def['title']} (job {job_id[:8]})")


if __name__ == "__main__":
    asyncio.run(seed())
