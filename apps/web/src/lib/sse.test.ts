import { describe, expect, it } from "vitest";

import { eventNames, parseSSE } from "./sse";

const STUB_STREAM = `event: retrieval.started
data: {"request_id": "abc"}

event: generation.delta
data: {"text": "你好"}

event: done
data: {"request_id": "abc", "answer": {"evidence_status": "SUFFICIENT"}}
`;

describe("parseSSE（契约 §1.1）", () => {
  it("解析事件名与 JSON 载荷", () => {
    const events = parseSSE(STUB_STREAM);
    expect(eventNames(events)).toEqual(["retrieval.started", "generation.delta", "done"]);
    expect((events[0].data as { request_id: string }).request_id).toBe("abc");
  });

  it("容忍非 JSON 载荷（按原文保留）", () => {
    const events = parseSSE("event: error\ndata: not-json\n\n");
    expect(events[0].data).toBe("not-json");
  });

  it("空输入返回空数组", () => {
    expect(parseSSE("  ")).toEqual([]);
  });
});
