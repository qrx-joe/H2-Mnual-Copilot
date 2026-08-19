"""请求观测中间件（技术规范 §69、§73）。

日志红线：每条访问日志只记录 ID、方法、路径、状态码与耗时；
不得记录查询正文、检索上下文或任何机密内容。
"""

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("h2copilot.access")


def _new_request_id() -> str:
    return uuid.uuid4().hex[:12]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """为每个请求补充 X-Request-ID 并输出结构化访问日志。

    request_id 是后续 trace、错误结构（§104）与前端工单排查的公共关联键，
    因此在最早的中间件层生成：入站已携带（如来自网关）则透传复用。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or _new_request_id()
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # 异常路径也要留日志，否则失败请求在访问日志中不可见
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            logger.error(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "outcome": "exception",
                    },
                    ensure_ascii=False,
                )
            )
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
            )
        )
        return response
