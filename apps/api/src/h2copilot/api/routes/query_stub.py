"""问答接口桩（STUB）——Phase 3 工程基线产物，Phase 5 由真实管线替换。

为什么现在做这个桩：
1. 落地 SSE 事件契约（docs/architecture/contracts.md §1.1），让 V-6
   （SSE 流式可用性）从"推断"升级为"本地验证"。
2. 给前端提供稳定的联调目标，避免 Phase 4/5 前后端互相阻塞。

桩的边界：返回内容是硬编码演示数据，不代表检索/生成结果；
数据形状与契约一致，替换时前端无需改动。
"""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryRequest(BaseModel):
    """POST /api/v1/query 请求体（contracts §1.1）。"""

    query: str = Field(min_length=1, max_length=2000)
    device_id: str = Field(min_length=1, max_length=64)
    version: str | None = Field(default=None, max_length=32)
    language: str = Field(default="zh-CN", max_length=16)
    conversation_id: str | None = Field(default=None, max_length=64)


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _event_stream(payload: QueryRequest) -> AsyncIterator[str]:
    """按契约顺序产出事件；异步生成器保持与真实管线相同的消费方式。"""
    request_id = uuid.uuid4().hex[:12]
    yield _sse("retrieval.started", {"request_id": request_id})
    await asyncio.sleep(0.01)  # 模拟检索耗时，验证流式分段到达
    yield _sse(
        "retrieval.completed",
        {"chunk_ids": ["stub-chunk-1"], "retrieval_ms": 42},
    )
    yield _sse("generation.started", {})
    await asyncio.sleep(0.01)
    yield _sse("generation.delta", {"text": "这是工程基线的 SSE 桩输出，"})
    yield _sse("generation.delta", {"text": "真实检索与生成在 Phase 5 接入。"})
    yield _sse("verification.completed", {"evidence_status": "SUFFICIENT"})
    yield _sse(
        "done",
        {
            "request_id": request_id,
            "answer": {
                "answer": "这是工程基线的 SSE 桩输出，真实检索与生成在 Phase 5 接入。",
                "steps": [],
                "citations": [],
                "evidence_status": "SUFFICIENT",
                "safety_notice": None,
                "abstain": False,
                "abstain_reason": None,
            },
            "stub": True,
            "echo": {"device_id": payload.device_id, "version": payload.version},
        },
    )


@router.post("/query")
async def query(payload: QueryRequest) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 防止反向代理缓冲破坏流式语义
        },
    )
