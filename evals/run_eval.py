# -*- coding: utf-8 -*-
"""Golden dataset 评测（T-023；技术规范 §78–§81）。

运行方式（仓库根）：
  cd apps/api && PYTHONUTF8=1 uv run python ../../evals/run_eval.py

指标（Fake 模型替身下的可测子集）：
- Recall@citation：answerable 问题的期望文档+页码出现在返回引用中；
- No-answer accuracy：不可回答问题正确拒答（abstain）；
- Faithfulness / 跨语言召回：需要真实模型（Q-010），条目标记跳过。

报告输出：evals/report.json + 控制台摘要。
"""

import asyncio
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API_DIR = REPO / "apps" / "api"
sys.path.insert(0, str(API_DIR / "src"))
sys.path.insert(0, str(API_DIR / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "datasets"))

# 与集成测试相同的安全约定：评测只写 h2copilot_test，绝不碰开发库
_base = os.environ.get("DATABASE_URL") or "postgresql+asyncpg://h2copilot:h2copilot@localhost:5432/h2copilot"
os.environ["DATABASE_URL"] = _base.rsplit("/", 1)[0] + "/h2copilot_test"


def _setup() -> None:
    """同步准备：settings 缓存清理 + 迁移（alembic 内部用 asyncio.run，不能在事件循环里调）。"""
    from alembic import command
    from alembic.config import Config

    from h2copilot.core.config import get_settings

    get_settings.cache_clear()
    cfg = Config(str(API_DIR / "alembic.ini"))
    command.upgrade(cfg, "head")


async def main() -> int:
    from httpx import ASGITransport
    import httpx
    from sqlalchemy import text

    from h2copilot.api.app import app
    from h2copilot.core.db import dispose_engine, get_engine, session_scope
    from h2copilot.domain.models import Device, Document, DocumentVersion, IngestionJob
    from h2copilot.ingestion.pipeline import run_ingestion, sha256_bytes
    from build_docs import DOCS, build_pdf_bytes

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE citations, feedback, messages, conversations, chunks, "
                "ingestion_jobs, document_versions, documents, devices CASCADE"
            )
        )

    # 索引全部合成文档
    for doc_def in DOCS:
        data = build_pdf_bytes(doc_def["pages"])
        await _ingest_manual_direct(doc_def, data)
    print(f"indexed {len(DOCS)} synthetic docs")

    # 逐条评测
    golden = [
        json.loads(line)
        for line in (Path(__file__).parent / "datasets" / "golden.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    results = []
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://eval") as client:
        for g in golden:
            if g.get("requires_real_embedding"):
                results.append({**g, "status": "blocked_real_embedding"})
                continue
            body = {"query": g["question"], "device_id": g["device_id"]}
            if g.get("version"):
                body["version"] = g["version"]
            resp = await client.post("/api/v1/query", json=body)
            events = _parse(resp.text)
            if "error" in events:
                results.append({**g, "status": "error", "detail": events["error"]})
                continue
            done = events["done"]
            answer = done["answer"]
            citations = answer["citations"]
            if g["answerable"]:
                hit = any(
                    c["document_title"] == g["expected_document"] and c["page"] in g["expected_pages"]
                    for c in citations
                )
                status = "pass" if hit and not answer["abstain"] else "fail"
            else:
                status = "pass" if answer["abstain"] else "fail"
            results.append(
                {**g, "status": status, "abstain": answer["abstain"],
                 "citations": [(c["document_title"], c["page"]) for c in citations]}
            )

    await dispose_engine()

    runnable = [r for r in results if r["status"] not in ("blocked_real_embedding", "error")]
    answerable = [r for r in runnable if r["answerable"]]
    no_answer = [r for r in runnable if not r["answerable"]]
    recall = sum(1 for r in answerable if r["status"] == "pass") / max(len(answerable), 1)
    no_ans_acc = sum(1 for r in no_answer if r["status"] == "pass") / max(len(no_answer), 1)
    summary = {
        "total": len(results),
        "runnable": len(runnable),
        "blocked_real_embedding": sum(1 for r in results if r["status"] == "blocked_real_embedding"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "recall_at_citation": round(recall, 4),
        "no_answer_accuracy": round(no_ans_acc, 4),
        "model_layer": "Fake providers（真实模型指标待 Q-010）",
    }

    out = Path(__file__).parent / "report.json"
    out.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for r in results:
        if r["status"] == "fail":
            print(f"FAIL [{r['category']}] {r['question']!r} citations={r.get('citations')}")
    return 0


def _parse(resp_text: str) -> dict:
    events: dict[str, dict] = {}
    for block in resp_text.strip().split("\n\n"):
        lines = block.split("\n")
        ev = next((l[7:] for l in lines if l.startswith("event: ")), None)
        data = next((l[6:] for l in lines if l.startswith("data: ")), None)
        if ev and data:
            events[ev] = json.loads(data)
    return events


async def _ingest_manual_direct(doc_def: dict, pdf_bytes: bytes) -> None:
    """与 HTTP 上传等价的直连索引（复用测试验证过的管线）。"""
    import tempfile
    from pathlib import Path as P

    from h2copilot.core.db import session_scope
    from h2copilot.domain.enums import DocumentType, TrustLevel
    from h2copilot.domain.models import Device, Document, DocumentVersion, IngestionJob
    from h2copilot.ingestion.pipeline import run_ingestion, sha256_bytes
    from h2copilot.ingestion.storage import LocalFSStorage

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
        pdf_path = P(tmp.name)
    await run_ingestion(job_id, ver_id, pdf_path)
    await LocalFSStorage().put(f"eval/{doc_def['title']}.pdf", pdf_bytes)

    async with session_scope() as session:
        job_row = await session.get(IngestionJob, uuid.UUID(job_id))
        assert job_row is not None and job_row.status.value == "READY", (
            f"eval ingestion failed: {job_row.error if job_row else 'missing'}"
        )


if __name__ == "__main__":
    _setup()
    raise SystemExit(asyncio.run(main()))
