/**
 * Evidence 状态徽章的展示映射（ADR-0005）。
 *
 * 约束：徽章文案只允许由后端 evidence_status 四态驱动，
 * 前端不得自行计算或展示任何"置信度数值"。
 */

export type EvidenceStatus =
  "SUFFICIENT" | "PARTIAL" | "INSUFFICIENT" | "CONFLICTING";

export interface EvidenceBadge {
  label: string;
  /** 语义色：与视觉原型的绿/橙/红体系一致；状态同时用文字表达，不只靠颜色 */
  tone: "positive" | "caution" | "negative";
}

const BADGES: Record<EvidenceStatus, EvidenceBadge> = {
  SUFFICIENT: { label: "证据充分", tone: "positive" },
  PARTIAL: { label: "证据部分覆盖", tone: "caution" },
  INSUFFICIENT: { label: "证据不足", tone: "negative" },
  CONFLICTING: { label: "证据冲突", tone: "caution" },
};

export function evidenceBadge(status: EvidenceStatus): EvidenceBadge {
  const badge = BADGES[status];
  if (!badge) {
    // 未知状态按最保守处理：宁可显示不足，也不虚构充分
    return BADGES.INSUFFICIENT;
  }
  return badge;
}
