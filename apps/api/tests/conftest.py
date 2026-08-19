"""共享测试夹具：基于 ASGI 传输的 HTTP 客户端（不起真实端口）。"""

import collections.abc

import httpx
import pytest
from httpx import ASGITransport

from h2copilot.api.app import app


@pytest.fixture
async def client() -> collections.abc.AsyncIterator[httpx.AsyncClient]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
