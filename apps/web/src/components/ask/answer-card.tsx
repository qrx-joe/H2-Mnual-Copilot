"use client";

/**
 * 回答卡（原型 .answer）：四态（safe/warn/stop/error）+ 步骤 + 安全提示 + 引用徽章 + 反馈。
 * 反馈按 PRD FR-009 完整实现（👍/👎/🚩 + 原因多选），超出原型的简化按钮
 * （C-4 收敛：PRD 为准）。Phase 4 反馈只 toast，Phase 5（T-022）落库。
 */

import { useState } from "react";

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import type { AnswerModel, MockSource } from "@/lib/mock-data";

const KIND_STYLES = {
  safe: { icon: "check" as const, cls: "bg-green-soft text-green" },
  warn: { icon: "alert" as const, cls: "bg-orange-soft text-orange" },
  stop: { icon: "x" as const, cls: "bg-red-soft text-red" },
  error: { icon: "alert" as const, cls: "bg-red-soft text-red" },
};

/** FR-009 反馈原因（PRD §31），Insufficient/Incorrect 与安全共用同一集合 */
const REASONS = ["错误答案", "来源不相关", "版本错误", "信息过时", "安全风险"];

export function AnswerCard({ answer, onRetry }: { answer: AnswerModel; onRetry?: () => void }) {
  const { openSource, toast } = useUI();
  const [feedbackPanel, setFeedbackPanel] = useState<"incorrect" | "safety" | null>(null);
  const [selectedReasons, setSelectedReasons] = useState<string[]>([]);
  const kind = KIND_STYLES[answer.kind];

  const toggleReason = (r: string) =>
    setSelectedReasons((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]));

  const submitFeedback = async (type: string, reasons: string[] = []) => {
    // 真实链路：落库（T-022）；无 message_id（演示数据）时仅提示
    if (answer.messageId) {
      const apiType = type === "Safety concern" ? "SAFETY_CONCERN" : type === "Incorrect" ? "INCORRECT" : "HELPFUL";
      try {
        const { submitFeedback: post } = await import("@/lib/api");
        await post(answer.messageId, apiType as "HELPFUL", reasons);
        toast({ tone: "success", title: "Feedback saved", message: `已记录${type}反馈${reasons.length ? `（${reasons.join("、")}）` : ""}。` });
      } catch {
        toast({ tone: "info", title: "反馈提交失败", message: "后端不可达，反馈未保存。" });
      }
    } else {
      toast({ tone: "success", title: "Feedback saved", message: `已记录${type}反馈（演示数据，不落库）。` });
    }
    setFeedbackPanel(null);
    setSelectedReasons([]);
  };

  return (
    <div className="overflow-hidden rounded-r3 border border-line-soft bg-surface">
      {/* 头部：状态图标 + 标题 + 证据状态徽章（ADR-0005：状态文字，非数值） */}
      <div className="flex items-start gap-2.5 border-b border-line-soft px-4 pb-3 pt-3.5">
        <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-[10px] ${kind.cls}`}>
          <Icon name={kind.icon} className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <h3 className="text-[15px] leading-snug font-semibold">{answer.title}</h3>
          {answer.kind === "error" && answer.errorCode ? (
            <small className="mt-0.5 block font-mono text-[9px] text-ink-3">
              error_code={answer.errorCode} · {answer.errorMessage}
            </small>
          ) : null}
        </div>
      </div>

      <div className="p-4">
        <p className="text-[13px] leading-relaxed">{answer.summary}</p>

        {answer.steps.length > 0 && (
          <>
            <div className="mb-2 mt-4 text-[10px] font-bold tracking-wider text-ink-3 uppercase">
              Recommended checks
            </div>
            <div className="grid gap-2">
              {answer.steps.map((s, i) => (
                <div key={i} className="flex gap-2 text-[12px] leading-normal">
                  <span className="mt-px grid h-[21px] w-[21px] shrink-0 place-items-center rounded-lg bg-blue-soft text-[9px] font-bold text-blue">
                    {i + 1}
                  </span>
                  <span>{s}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {answer.safety && (
          <div className="mt-4 flex gap-2 rounded-xl bg-orange-soft p-3 text-[11px] leading-normal text-orange">
            <Icon name="shield" className="h-4 w-4 shrink-0" />
            <span>{answer.safety}</span>
          </div>
        )}

        {/* 引用徽章：点击打开 Source Viewer（FR-007 交互路径） */}
        {answer.sources.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {answer.sources.map((s: MockSource, i) => (
              <button
                key={i}
                onClick={() => openSource(s)}
                className="inline-flex min-h-[30px] items-center gap-1 rounded-full border border-[rgba(0,113,227,.18)] bg-blue-soft px-2.5 text-[10px] font-semibold text-blue"
              >
                <Icon name="doc" className="h-[15px] w-[15px]" />
                {s.title} · p.{s.page}
              </button>
            ))}
          </div>
        )}

        {/* FR-006：拒答时的最相关资料与推荐关键词 */}
        {answer.kind === "stop" && answer.relatedDocuments && (
          <div className="mt-4 rounded-xl bg-surface-2 p-3">
            <div className="mb-1.5 text-[10px] font-bold text-ink-3">Related documents</div>
            <ul className="list-inside list-disc text-[11px] text-ink-2">
              {answer.relatedDocuments.map((d) => (
                <li key={d.title}>{d.title}</li>
              ))}
            </ul>
            <div className="mt-2 mb-1.5 text-[10px] font-bold text-ink-3">Suggested keywords</div>
            <div className="flex flex-wrap gap-1.5">
              {(answer.suggestedKeywords ?? []).map((k) => (
                <span key={k} className="rounded-full border border-line-soft bg-surface px-2 py-0.5 text-[10px] text-ink-2">
                  {k}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 错误态：重试按钮（真实链路的幂等重试入口） */}
        {answer.kind === "error" && onRetry && (
          <button
            className="mt-4 h-9 rounded-full bg-blue px-4 text-[12px] font-semibold text-white hover:bg-blue-hover"
            onClick={onRetry}
          >
            Retry
          </button>
        )}
      </div>

      {/* 反馈区（FR-009）：三种类型 + 原因多选 */}
      {answer.kind !== "error" && (
        <div className="border-t border-line-soft px-3 py-2">
          <div className="flex gap-1">
            <button
              className="inline-flex h-7 items-center gap-1 rounded-lg px-2 text-[10px] text-ink-3 hover:bg-surface-3 hover:text-ink"
              onClick={() => submitFeedback("Helpful")}
            >
              <Icon name="thumb" className="h-[15px] w-[15px]" />
              Helpful
            </button>
            <button
              className={`inline-flex h-7 items-center gap-1 rounded-lg px-2 text-[10px] hover:bg-surface-3 hover:text-ink ${
                feedbackPanel === "incorrect" ? "text-ink" : "text-ink-3"
              }`}
              onClick={() => {
                setFeedbackPanel(feedbackPanel === "incorrect" ? null : "incorrect");
                setSelectedReasons([]);
              }}
            >
              <Icon name="x" className="h-[15px] w-[15px]" />
              Incorrect
            </button>
            <button
              className={`inline-flex h-7 items-center gap-1 rounded-lg px-2 text-[10px] hover:bg-surface-3 hover:text-ink ${
                feedbackPanel === "safety" ? "text-ink" : "text-ink-3"
              }`}
              onClick={() => {
                setFeedbackPanel(feedbackPanel === "safety" ? null : "safety");
                setSelectedReasons([]);
              }}
            >
              <Icon name="flag" className="h-[15px] w-[15px]" />
              Safety concern
            </button>
          </div>

          {feedbackPanel && (
            <div className="mt-2 rounded-xl bg-surface-2 p-3">
              <div className="mb-2 text-[10px] text-ink-3">请选择原因（可多选）：</div>
              <div className="flex flex-wrap gap-1.5">
                {REASONS.map((r) => (
                  <button
                    key={r}
                    aria-pressed={selectedReasons.includes(r)}
                    onClick={() => toggleReason(r)}
                    className={`rounded-full border px-2.5 py-1 text-[10px] ${
                      selectedReasons.includes(r)
                        ? "border-[rgba(0,113,227,.25)] bg-blue-soft text-blue"
                        : "border-line-soft bg-surface text-ink-2"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
              <button
                className="mt-2.5 h-8 rounded-full bg-blue px-3 text-[11px] font-semibold text-white hover:bg-blue-hover disabled:opacity-40"
                disabled={selectedReasons.length === 0}
                onClick={() =>
                  submitFeedback(
                    feedbackPanel === "safety" ? "Safety concern" : "Incorrect",
                    selectedReasons,
                  )
                }
              >
                提交
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
