"""SSE 桩契约测试（contracts §1.1；V-6 的自动化证据）。

断言事件名顺序与终值结构，不关心桩的文本内容——
这样 Phase 5 替换为真实管线时，本测试可直接改为对真实事件的联调基线。
"""

import json

import httpx

EXPECTED_EVENTS = [
    "retrieval.started",
    "retrieval.completed",
    "generation.started",
    "generation.delta",
    "generation.delta",
    "verification.completed",
    "done",
]


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line[len("event: ") :] for line in lines if line.startswith("event: "))
        data_line = next(line for line in lines if line.startswith("data: "))
        events.append((event, json.loads(data_line[len("data: ") :])))
    return events


async def test_query_stream_event_sequence(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/v1/query", json={"query": "E104", "device_id": "hx100"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    assert [name for name, _ in events] == EXPECTED_EVENTS

    done_data = events[-1][1]
    assert done_data["stub"] is True
    assert done_data["request_id"]
    assert done_data["answer"]["evidence_status"] == "SUFFICIENT"
    assert done_data["answer"]["abstain"] is False
    # 设备上下文必须回显（FR-005：答案与设备绑定）
    assert done_data["echo"] == {"device_id": "hx100", "version": None}


async def test_query_rejects_empty_query(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/v1/query", json={"query": "", "device_id": "hx100"})
    # 契约：参数错误 → 422（VALIDATION_ERROR，Phase 5 统一错误结构映射）
    assert resp.status_code == 422


async def test_query_rejects_missing_device(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/v1/query", json={"query": "E104"})
    assert resp.status_code == 422
