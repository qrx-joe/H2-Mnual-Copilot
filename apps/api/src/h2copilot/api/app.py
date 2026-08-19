"""FastAPI 应用工厂。

分层约束（技术规范 §12）：路由层只做参数校验与响应组装；
业务编排在 services 层（Phase 5 引入），此处不出现 SQL、模型调用与 prompt。
"""

import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from h2copilot.api.routes import health, query_stub
from h2copilot.observability.middleware import RequestContextMiddleware


def _configure_logging() -> None:
    # Windows 控制台默认 GBK，强制 UTF-8 避免中文日志抛编码异常（V-2 验证发现）
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(
        title="H2 Manual Copilot API",
        version="0.1.0",
        description="Evidence-grounded industrial knowledge copilot (MVP).",
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(query_stub.router)

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        # 统一错误结构（技术规范 §104）。未预期异常不向客户端泄露内部细节，
        # 关联键是 request_id，细节只留在服务端日志。
        request_id = getattr(request.state, "request_id", None)
        logging.getLogger("h2copilot.error").exception("unhandled error, request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error.",
                    "request_id": request_id,
                }
            },
        )

    return app


app = create_app()


# 供测试与 uvicorn 使用的模块级句柄说明：
#   uvicorn h2copilot.api.app:app --reload
async def _lifespan_placeholder() -> AsyncIterator[None]:
    # Phase 5 在此挂接数据库连接池与模型客户端的生命周期管理
    yield
