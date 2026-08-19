/**
 * SSE 流解析（契约见 docs/architecture/contracts.md §1.1）。
 *
 * Phase 4：纯函数 + 单测，作为 Phase 5 接入真实 `POST /api/v1/query`
 * 的唯一解析 seam——届时 fetch body reader 逐块喂给 parseSSE 即可。
 */

export interface SSEEvent {
  event: string;
  data: unknown;
}

export function parseSSE(text: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  for (const block of text.trim().split("\n\n")) {
    if (!block) continue;
    const lines = block.split("\n");
    const eventLine = lines.find((l) => l.startsWith("event: "));
    const dataLine = lines.find((l) => l.startsWith("data: "));
    if (!eventLine || !dataLine) continue;
    let data: unknown = null;
    try {
      data = JSON.parse(dataLine.slice("data: ".length));
    } catch {
      data = dataLine.slice("data: ".length); // 非 JSON 载荷按原文保留
    }
    events.push({ event: eventLine.slice("event: ".length), data });
  }
  return events;
}

/** 断言事件名序列与契约一致（测试与 Phase 5 联调共用）。 */
export function eventNames(events: SSEEvent[]): string[] {
  return events.map((e) => e.event);
}
