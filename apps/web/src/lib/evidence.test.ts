import { describe, expect, it } from "vitest";

import { evidenceBadge } from "./evidence";

describe("evidenceBadge（ADR-0005：四态徽章，无数值）", () => {
  it("覆盖全部四态且无数值评分", () => {
    const statuses = ["SUFFICIENT", "PARTIAL", "INSUFFICIENT", "CONFLICTING"] as const;
    for (const s of statuses) {
      const badge = evidenceBadge(s);
      expect(badge.label.length).toBeGreaterThan(0);
      expect(badge.tone).toBeTruthy();
      expect(badge.label).not.toMatch(/\d/); // 徽章文案不得包含数值
    }
  });

  it("未知状态回落到最保守展示", () => {
    // @ts-expect-error 故意传入非法值验证防御
    expect(evidenceBadge("MAYBE").label).toBe("证据不足");
  });
});
