"""反馈路由（契约 §1.5，FR-009）：回答质量的 👍/👎/🚩 与多选原因落库。"""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from h2copilot.core.db import session_scope
from h2copilot.domain.models import Feedback, Message

router = APIRouter(prefix="/api/v1", tags=["feedback"])

FeedbackType = Literal["HELPFUL", "INCORRECT", "SAFETY_CONCERN"]


class FeedbackBody(BaseModel):
    type: FeedbackType
    reasons: list[str] = Field(default_factory=list, max_length=8)


@router.post("/messages/{message_id}/feedback", status_code=201)
async def submit_feedback(message_id: uuid.UUID, body: FeedbackBody) -> dict:
    async with session_scope() as session:
        msg = await session.get(Message, message_id)
        if msg is None:
            raise HTTPException(status_code=404, detail="消息不存在")
        # 幂等语义（契约 §1.5）：同消息同类型覆盖上一次提交
        existing = (
            await session.execute(
                select(Feedback).where(
                    Feedback.message_id == message_id, Feedback.feedback_type == body.type
                )
            )
        ).first()
        if existing is not None:
            existing[0].reasons = body.reasons
        else:
            session.add(
                Feedback(message_id=message_id, feedback_type=body.type, reasons=body.reasons)
            )
        await session.commit()
        return {"saved": True, "type": body.type}
