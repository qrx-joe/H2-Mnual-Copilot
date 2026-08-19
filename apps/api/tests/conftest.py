"""共享测试配置。

关键约定：在模块导入阶段（早于任何测试模块导入 app）把 DATABASE_URL
切到独立的 h2copilot_test 库——否则集成测试会污染开发库
（本文件曾因 fixture 时机问题泄漏，已提升到收集期修复）。
"""

import os
from pathlib import Path


# apps/api/.env 优先作为基础 URL（含连接凭据），环境变量次之，最后本地默认
def _base_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    return "postgresql+asyncpg://h2copilot:h2copilot@localhost:5432/h2copilot"


os.environ["DATABASE_URL"] = _base_url().rsplit("/", 1)[0] + "/h2copilot_test"

import collections.abc  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from httpx import ASGITransport  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db() -> None:
    """测试库 schema：会话开始时对齐到最新迁移（与开发库同一套 Alembic）。"""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")


@pytest.fixture
async def client() -> collections.abc.AsyncIterator[httpx.AsyncClient]:
    """ASGI 客户端：每个测试前清空业务表（隔离），结束后释放引擎。"""
    from sqlalchemy import text

    from h2copilot.api.app import app
    from h2copilot.core.db import dispose_engine, get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE citations, feedback, messages, conversations, chunks, "
                "ingestion_jobs, document_versions, documents, devices CASCADE"
            )
        )

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await dispose_engine()
