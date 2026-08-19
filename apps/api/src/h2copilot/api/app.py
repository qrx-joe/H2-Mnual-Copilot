"""FastAPI 应用工厂。

分层约束（技术规范 §12）：路由层只做参数校验与响应组装；
业务编排在 services/ingestion/retrieval 层，SQL 集中在 repositories/检索模块。
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from h2copilot.api.routes import devices, documents, feedback, health, query, sources
from h2copilot.core.config import get_settings
from h2copilot.observability.middleware import RequestContextMiddleware

logger = logging.getLogger("h2copilot.app")


def _configure_logging() -> None:
    # Windows 控制台默认 GBK，强制 UTF-8 避免中文日志抛编码异常（V-2 验证发现）
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def _seed_devices() -> None:
    """幂等种子数据：演示设备（HX-100/HX-80）。"""

    from h2copilot.core.db import session_scope
    from h2copilot.domain.models import Device

    seeds = [
        Device(id="hx100", name="HX-100 Electrolyzer", manufacturer="Hydrogen Lab", model="HX-100"),
        Device(id="hx80", name="HX-80 Electrolyzer", manufacturer="Hydrogen Lab", model="HX-80"),
    ]
    async with session_scope() as session:
        for d in seeds:
            existing = await session.get(Device, d.id)
            if existing is None:
                session.add(d)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _configure_logging()
    settings = get_settings()
    if settings.database_url:
        # 引擎惰性创建 + 预热一次连接（失败即启动报错：可诊断，不静默）
        from h2copilot.core.db import dispose_engine, get_engine

        engine = get_engine()
        async with engine.connect():
            pass
        await _seed_devices()
        logger.info("database ready: %s", settings.database_url.split("@")[-1])
        yield
        await dispose_engine()
    else:
        # 允许无数据库启动（/health 与静态演示），但真实链路会明确报错
        logger.warning("DATABASE_URL 未配置：仅健康检查可用，问答/上传将返回错误")
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="H2 Manual Copilot API",
        version="0.2.0",
        description="Evidence-grounded industrial knowledge copilot (MVP).",
        lifespan=lifespan,
    )

    # 前后端分离（ADR-002）：本地开发允许 Next.js dev/prod 源
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(documents.router)
    app.include_router(devices.router)
    app.include_router(sources.router)
    app.include_router(feedback.router)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        """业务 HTTP 错误（401/429/404…）转统一错误结构（契约 §5）。"""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": str(exc.detail),
                    "message": str(exc.detail),
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        # 统一错误结构（技术规范 §104）：未预期异常不向客户端泄露内部细节
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
