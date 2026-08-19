"use client";

/**
 * 检索管线进度卡（原型 .processing）：加载态的核心展示。
 * 步骤名与 API SSE 事件阶段一一对应（routing/retrieval/rerank/verification）。
 */

import { Icon } from "@/components/ui/icon";
import { PIPELINE_STEPS } from "@/lib/mock-data";

export interface PipelineState {
  currentStep: number; // 1..4，0 表示尚未开始
  note?: string; // 特殊路由标注（如 exact+dense / abstain）
}

export function ProcessingCard({ state }: { state: PipelineState }) {
  return (
    <div className="rounded-2xl border border-line-soft bg-surface p-3.5">
      <strong className="mb-2.5 flex items-center gap-2 text-[11px]">
        <span className="h-2 w-2 animate-pulse rounded-full bg-blue" />
        Searching grounded evidence
      </strong>
      <div className="grid gap-1.5">
        {PIPELINE_STEPS.map((step) => {
          const done = state.currentStep > step.id;
          const active = state.currentStep === step.id;
          return (
            <div
              key={step.id}
              className={`flex min-h-8 items-center gap-2 rounded-lg px-2 text-[10px] transition-colors ${
                done
                  ? "bg-green-soft text-green"
                  : active
                    ? "bg-blue-soft text-ink"
                    : "bg-surface-2 text-ink-3"
              }`}
            >
              {done ? <Icon name="check" className="h-[15px] w-[15px]" /> : <Icon name="search" className="h-[15px] w-[15px]" />}
              {step.label}
              <em className="ml-auto font-mono text-[9px] not-italic">
                {done ? "done" : active ? (state.note ?? "running") : "pending"}
              </em>
            </div>
          );
        })}
      </div>
    </div>
  );
}
