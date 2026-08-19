"use client";

/**
 * Ask 工作区（原型 #page-ask）：左会话 + 右 Evidence 双栏。
 *
 * Phase 4 边界：管线进度与回答均为本地固定数据按时序模拟（同原型做法），
 * 用于验证加载/成功/拒答/错误等全部界面状态；Phase 5 将 submit() 中的
 * 定时器替换为对 POST /api/v1/query 的 SSE 消费（lib/sse.ts 已备好解析 seam）。
 */

import { useEffect, useRef, useState } from "react";

import { AnswerCard } from "@/components/ask/answer-card";
import { Composer } from "@/components/ask/composer";
import { EvidencePanel } from "@/components/ask/evidence-panel";
import { ProcessingCard, type PipelineState } from "@/components/ask/processing-card";
import { Welcome } from "@/components/ask/welcome";
import { Icon } from "@/components/ui/icon";
import {
  SCENARIO_ANSWERS,
  classifyScenario,
  type AnswerModel,
} from "@/lib/mock-data";

type Entry =
  | { kind: "user"; text: string }
  | { kind: "answer"; model: AnswerModel };

const STEP_MS = 320;

export default function AskPage() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [busy, setBusy] = useState(false);
  const [pipeline, setPipeline] = useState<PipelineState | null>(null);
  const [lastAnswer, setLastAnswer] = useState<AnswerModel | null>(null);
  const lastQuery = useRef<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // 新消息后滚动到底部（原型 convo-body 滚动行为）
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [entries, pipeline]);

  const runPipeline = (query: string) => {
    const scenario = classifyScenario(query);
    const failure = query.includes("服务异常");
    let step = 0;

    setPipeline({ currentStep: 1 });
    const timer = setInterval(() => {
      step += 1;

      // 失败场景：在 rerank 阶段模拟上游错误（渲染 error 卡 + 重试入口）
      if (failure && step === 3) {
        clearInterval(timer);
        setPipeline(null);
        const model = SCENARIO_ANSWERS.failure;
        setEntries((prev) => [...prev, { kind: "answer", model }]);
        setLastAnswer(model);
        setBusy(false);
        return;
      }

      if (step >= 4) {
        clearInterval(timer);
        setPipeline(null);
        const model = SCENARIO_ANSWERS[scenario];
        setEntries((prev) => [...prev, { kind: "answer", model }]);
        setLastAnswer(model);
        setBusy(false);
        return;
      }

      setPipeline({
        currentStep: step + 1,
        note:
          (scenario === "error" && step + 1 === 2 ? "exact+dense" : undefined) ??
          (scenario === "noanswer" && step + 1 === 4 ? "abstain" : undefined),
      });
    }, STEP_MS);
  };

  const submit = (query: string) => {
    if (busy) return;
    lastQuery.current = query;
    setEntries((prev) => [...prev, { kind: "user", text: query }]);
    setBusy(true);
    setLastAnswer(null);
    runPipeline(query);
  };

  return (
    <section
      className="mx-auto grid max-w-[1440px] gap-4 px-7 pb-16 pt-7 max-[940px]:grid-cols-1 max-[680px]:px-3"
      style={{ gridTemplateColumns: "minmax(0,1fr) 360px", minHeight: "calc(100vh - var(--spacing-topbar) - 56px)" }}
    >
      {/* 会话面板 */}
      <div className="relative flex min-h-[680px] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e1">
        <div className="flex items-center gap-2 border-b border-line-soft px-4 py-2.5">
          <span className="text-[11px] text-ink-3">
            会话与设备上下文绑定；回答仅在当前选中设备的知识范围内生成（FR-005）。输入含“服务异常”可演示错误态。
          </span>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-auto px-6 pb-[184px] pt-6 max-[680px]:px-3.5">
          {entries.length === 0 && !pipeline ? (
            <Welcome onQuickPick={submit} />
          ) : (
            <div className="mx-auto block max-w-[780px]">
              {entries.map((e, i) =>
                e.kind === "user" ? (
                  <div key={i} className="mb-6 flex justify-end gap-3">
                    <div className="max-w-[86%] rounded-2xl rounded-br-[5px] bg-surface-3 px-3.5 py-2.5 text-[13px]">
                      {e.text}
                    </div>
                    <span className="grid h-[31px] w-[31px] shrink-0 place-items-center rounded-full bg-[#636366] text-[10px] font-bold text-white">
                      ME
                    </span>
                  </div>
                ) : (
                  <div key={i} className="mb-6 flex gap-3">
                    <span className="grid h-[31px] w-[31px] shrink-0 place-items-center rounded-full bg-ink text-surface">
                      <Icon name="spark" className="h-4 w-4" />
                    </span>
                    <div className="w-full max-w-[680px]">
                      <div className="mb-1.5 flex items-center gap-2">
                        <strong className="text-[11px]">H2 Copilot</strong>
                        <span className="text-[9px] text-ink-3">verified answer</span>
                      </div>
                      <AnswerCard
                        answer={e.model}
                        onRetry={
                          e.model.kind === "error"
                            ? () => submit(lastQuery.current.replace("服务异常", "").trim() || "E104")
                            : undefined
                        }
                      />
                    </div>
                  </div>
                ),
              )}
              {pipeline && (
                <div className="mb-6 flex gap-3">
                  <span className="grid h-[31px] w-[31px] shrink-0 place-items-center rounded-full bg-ink text-surface">
                    <Icon name="spark" className="h-4 w-4" />
                  </span>
                  <div className="w-full max-w-[680px]">
                    <div className="mb-1.5 flex items-center gap-2">
                      <strong className="text-[11px]">H2 Copilot</strong>
                      <span className="text-[9px] text-ink-3">working</span>
                    </div>
                    <ProcessingCard state={pipeline} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <Composer busy={busy} onSubmit={submit} />
      </div>

      <EvidencePanel answer={lastAnswer} />
    </section>
  );
}
