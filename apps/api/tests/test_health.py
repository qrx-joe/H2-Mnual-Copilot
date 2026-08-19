"""/health 冒烟：进程可启动、配置可加载（Phase 3 验收项）。"""

import httpx


async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # 基线环境未配置 DATABASE_URL 时应为 False，而不是报错
    assert body["db_configured"] is False
    assert body["request_id"]


async def test_request_id_echoed_in_header(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health", headers={"X-Request-ID": "fixed-id-001"})
    # 入站携带的 request_id 必须透传复用（网关/测试场景的关联键）
    assert resp.headers["X-Request-ID"] == "fixed-id-001"
