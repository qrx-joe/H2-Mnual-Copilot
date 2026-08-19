"""/health 冒烟：进程可启动、配置可加载（Phase 3 验收项）。"""

import httpx


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # db_configured 只反映配置状态（本地 .env 已配置时应为 True）
    assert isinstance(body["db_configured"], bool)
    assert body["request_id"]


async def test_request_id_echoed_in_header(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health", headers={"X-Request-ID": "fixed-id-001"})
    # 入站携带的 request_id 必须透传复用（网关/测试场景的关联键）
    assert resp.headers["X-Request-ID"] == "fixed-id-001"
