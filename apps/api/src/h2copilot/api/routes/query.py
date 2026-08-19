"""问答 SSE 路由（契约 §1.1）——替换 Phase 3 的桩（query_stub.py 已删除）。

事件序列固定：retrieval.started → retrieval.completed → generation.started
→ generation.delta* → verification.completed → done | error。
"""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from h2copilot.services.query_service import QueryService

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    device_id: str = Field(min_length=1, max_length=64)
    version: str | None = Field(default=None, max_length=32)
    language: str = Field(default="zh-CN", max_length=16)
    conversation_id: str | None = Field(default=None, max_length=64)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/query")
async def query(payload: QueryRequest) -> StreamingResponse:
    service = QueryService()

    async def stream() -> AsyncIterator[str]:
        try:
            yield _sse("retrieval.started", {"request_id": ""})
            result = await service.run(payload.query, payload.device_id, payload.version)

            yield _sse(
                "retrieval.completed",
                {"chunk_ids": result.chunk_ids, "retrieval_ms": result.retrieval_ms},
            )
            yield _sse("generation.started", {})

            # 增量输出：按句子切两段，模拟真实流式节奏（真实 LLM 接入后逐 token）
            text = result.answer.answer
            mid = len(text) // 2
            cut = text.find("。", mid)
            if cut == -1:
                cut = mid
            yield _sse("generation.delta", {"text": text[: cut + 1]})
            if cut + 1 < len(text):
                yield _sse("generation.delta", {"text": text[cut + 1 :]})

            yield _sse(
                "verification.completed",
                {"evidence_status": result.evidence_status.value},
            )
            yield _sse(
                "done",
                {
                    "request_id": result.request_id,
                    "intent": result.intent,
                    "answer": {
                        "answer": result.answer.answer,
                        "steps": result.answer.steps,
                        "citations": result.citations,
                        "evidence_status": result.evidence_status.value,
                        "safety_notice": result.answer.safety_notice,
                        "abstain": result.answer.abstain,
                        "abstain_reason": (
                            result.answer.abstain_reason.value
                            if result.answer.abstain_reason
                            else None
                        ),
                        "related_documents": [
                            {"title": t} for t in result.answer.related_documents
                        ],
                        "suggested_keywords": result.answer.suggested_keywords,
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001 —— SSE 错误以 error 事件收尾（契约 §1.1）
            import logging

            logging.getLogger("h2copilot.query").exception("query pipeline failed")
            yield _sse(
                "error",
                {
                    "error": {
                        "code": "RETRIEVAL_FAILED",
                        "message": f"查询链路失败：{exc}"[:200],
                        "request_id": None,
                    }
                },
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
