"""问答 SSE 路由（契约 §1.1，v1.2：done 事件新增 message_id/conversation_id）。

Phase 6 横切：
- 限流（§108）：进程内 RPM，超限返回契约错误结构 429；
- 超时降级（§74/§106）：全链路 asyncio.wait_for，超时以 error 事件收尾；
- 持久化：Conversation + 双向 Message + Citation 实体落库（§18 引用是实体）。
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from h2copilot.core.config import get_settings
from h2copilot.core.db import session_scope
from h2copilot.core.ratelimit import get_limiter
from h2copilot.domain.models import Citation, Conversation, Message
from h2copilot.services.query_service import QueryResult, QueryService

router = APIRouter(prefix="/api/v1", tags=["query"])
logger = logging.getLogger("h2copilot.query")


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    device_id: str = Field(min_length=1, max_length=64)
    version: str | None = Field(default=None, max_length=32)
    language: str = Field(default="zh-CN", max_length=16)
    conversation_id: str | None = Field(default=None, max_length=64)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _check_rate_limit(request: Request) -> None:
    """按客户端地址限流。超限抛业务异常，由 app 的 HTTPException 处理器转契约结构。"""
    from fastapi import HTTPException

    key = request.client.host if request.client else "unknown"
    if not get_limiter().allow(key):
        raise HTTPException(status_code=429, detail="RATE_LIMITED")


async def _persist_messages(
    payload: QueryRequest, result: QueryResult, request_id: str
) -> tuple[str, str]:
    """会话与消息落库：assistant 消息挂 Citation 实体（技术规范 §18）。"""
    async with session_scope() as session:
        conv_id = (
            uuid.UUID(payload.conversation_id)
            if payload.conversation_id
            else uuid.uuid4()
        )
        if payload.conversation_id is None:
            session.add(Conversation(id=conv_id, device_id=payload.device_id))
        user_msg = Message(
            conversation_id=conv_id, role="user", content=payload.query, request_id=request_id
        )
        assistant_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=result.answer.answer,
            request_id=request_id,
            evidence_status=result.evidence_status.value,
            model_alias=result.model_alias,
        )
        session.add_all([user_msg, assistant_msg])
        await session.flush()
        for c in result.citations:
            session.add(
                Citation(
                    message_id=assistant_msg.id,
                    chunk_id=uuid.UUID(c["chunk_id"]),
                    page_number=c["page"],
                )
            )
        await session.commit()
        return str(conv_id), str(assistant_msg.id)


@router.post("/query", dependencies=[Depends(_check_rate_limit)])
async def query(payload: QueryRequest) -> StreamingResponse:
    service = QueryService()
    settings = get_settings()

    async def stream() -> AsyncIterator[str]:
        request_id = uuid.uuid4().hex[:12]
        try:
            yield _sse("retrieval.started", {"request_id": request_id})
            # 全链路超时预算：超时进入降级路径（T-009）
            result = await asyncio.wait_for(
                service.run(payload.query, payload.device_id, payload.version),
                timeout=settings.query_timeout_seconds,
            )

            conv_id, msg_id = await _persist_messages(payload, result, request_id)

            yield _sse(
                "retrieval.completed",
                {"chunk_ids": result.chunk_ids, "retrieval_ms": result.retrieval_ms},
            )
            yield _sse("generation.started", {})

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
                    "request_id": request_id,
                    "conversation_id": conv_id,
                    "message_id": msg_id,
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
        except TimeoutError:
            logger.warning(
                "query timeout request_id=%s budget=%ss",
                request_id,
                settings.query_timeout_seconds,
            )
            yield _sse(
                "error",
                {
                    "error": {
                        "code": "MODEL_UNAVAILABLE",
                        "message": f"查询超时（>{settings.query_timeout_seconds}s），已降级拒答。",
                        "request_id": request_id,
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001 —— SSE 错误以 error 事件收尾（契约 §1.1）
            logger.exception("query pipeline failed request_id=%s", request_id)
            yield _sse(
                "error",
                {
                    "error": {
                        "code": "RETRIEVAL_FAILED",
                        "message": f"查询链路失败：{exc}"[:200],
                        "request_id": request_id,
                    }
                },
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
