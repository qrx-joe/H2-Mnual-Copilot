"use client";

/**
 * Ask 工作区 —— Phase 5 已接真实后端（POST /api/v1/query SSE）。
 * 管线进度由真实事件驱动：retrieval.* → generation.* → verification → done/error。
 */

import { useEffect, useRef, useState } from "react";

import { AnswerCard } from "@/components/ask/answer-card";
import { Composer } from "@/components/ask/composer";
import { EvidencePanel } from "@/components/ask/evidence-panel";
import { ProcessingCard, type PipelineState } from "@/components/ask/processing-card";
import { Welcome } from "@/components/ask/welcome";
import { Icon } from "@/components/ui/icon";
import { streamQuery, type ApiAnswer, type ApiDevice } from "@/lib/api";
import type { AnswerModel, MockSource } from "@/lib/mock-data";
import type { SSEEvent } from "@/lib/sse";

type Entry =
  | { kind: "user"; text: string }
  | { kind: "answer"; model: AnswerModel };

/** 契约 Answer → 展示模型：四态映射（ADR-0005），冲突/拒答优先级高于普通态 */
function toAnswerModel(a: ApiAnswer, messageId?: string): AnswerModel {
  if (a.abstain && a.abstain_reason === "CONFLICTING_VERSIONS") {
    return {
      kind: "warn", title: "检测到版本冲突", summary: a.answer, steps: [],
      safety: null, evidenceStatus: a.evidence_status, sources: [],
      relatedDocuments: a.related_documents, suggestedKeywords: a.suggested_keywords,
      messageId,
    };
  }
  if (a.abstain) {
    return {
      kind: "stop", title: "当前知识库无法可靠回答", summary: a.answer, steps: [],
      safety: null, evidenceStatus: a.evidence_status, sources: [],
      relatedDocuments: a.related_documents, suggestedKeywords: a.suggested_keywords,
      messageId,
    };
  }
  const sources: MockSource[] = a.citations.map((c) => ({
    title: c.document_title, version: `v${c.version}`, page: c.page,
    trust: "", excerpt: c.excerpt, chunkId: c.chunk_id,
  }));
  return {
    kind: a.evidence_status === "CONFLICTING" ? "warn" : "safe",
    title: "Grounded answer",
    summary: a.answer,
    steps: a.steps,
    safety: a.safety_notice,
    evidenceStatus: a.evidence_status,
    sources,
    messageId,
  };
}

export default function AskPage() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [busy, setBusy] = useState(false);
  const [pipeline, setPipeline] = useState<PipelineState | null>(null);
  const [lastAnswer, setLastAnswer] = useState<AnswerModel | null>(null);
  const [devices, setDevices] = useState<ApiDevice[]>([]);
  const lastQuery = useRef("");
  const lastDevice = useRef("hx100");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [entries, pipeline]);

  // 设备列表来自后端（FR-005 数据源）；失败静默保留默认 hx100
  useEffect(() => {
    import("@/lib/api").then(({ listDevices }) =>
      listDevices()
        .then(setDevices)
        .catch(() => undefined),
    );
  }, []);

  const submit = async (query: string, deviceId: string) => {
    if (busy) return;
    lastQuery.current = query;
    lastDevice.current = deviceId;
    setEntries((prev) => [...prev, { kind: "user", text: query }]);
    setBusy(true);
    setLastAnswer(null);
    setPipeline({ currentStep: 1 });

    try {
      await streamQuery({ query, device_id: deviceId }, {
        onEvent: (ev: SSEEvent) => {
          if (ev.event === "retrieval.started") {
            setPipeline({ currentStep: 2 }); // routing 完成，进入检索
          } else if (ev.event === "retrieval.completed") {
            const d = ev.data as { chunk_ids: string[] };
            setPipeline({ currentStep: 3, note: d.chunk_ids.length ? undefined : "no hits" });
          } else if (ev.event === "generation.started") {
            setPipeline({ currentStep: 4 });
          } else if (ev.event === "done") {
            const d = ev.data as { answer: ApiAnswer; message_id?: string };
            const model = toAnswerModel(d.answer, d.message_id);
            setEntries((prev) => [...prev, { kind: "answer", model }]);
            setLastAnswer(model);
            setPipeline(null);
            setBusy(false);
          } else if (ev.event === "error") {
            const d = ev.data as { error: { code: string; message: string } };
            const model: AnswerModel = {
              kind: "error", title: "服务暂时不可用", summary: d.error.message,
              steps: [], safety: null, evidenceStatus: "INSUFFICIENT", sources: [],
              errorCode: d.error.code, errorMessage: d.error.message,
            };
            setEntries((prev) => [...prev, { kind: "answer", model }]);
            setLastAnswer(model);
            setPipeline(null);
            setBusy(false);
          }
        },
      });
    } catch {
      // 网络层失败（后端不可达等）：渲染错误卡（真实失败路径）
      const model: AnswerModel = {
        kind: "error", title: "无法连接服务",
        summary: "后端 API 不可达，请确认 apps/api 已启动（uvicorn，端口 8000）。",
        steps: [], safety: null, evidenceStatus: "INSUFFICIENT", sources: [],
        errorCode: "MODEL_UNAVAILABLE", errorMessage: "API unreachable",
      };
      setEntries((prev) => [...prev, { kind: "answer", model }]);
      setLastAnswer(model);
      setPipeline(null);
      setBusy(false);
    }
  };

  return (
    <section
      className="mx-auto grid max-w-[1440px] gap-4 px-7 pb-16 pt-7 max-[940px]:grid-cols-1 max-[680px]:px-3"
      style={{ gridTemplateColumns: "minmax(0,1fr) 360px", minHeight: "calc(100vh - var(--spacing-topbar) - 56px)" }}
    >
      <div className="relative flex min-h-[680px] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e1">
        <div className="flex items-center gap-2 border-b border-line-soft px-4 py-2.5">
          <span className="text-[11px] text-ink-3">
            回答由后端检索链路实时生成；答案与证据来自已索引文档（FR-005 设备隔离）。
          </span>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-auto px-6 pb-[184px] pt-6 max-[680px]:px-3.5">
          {entries.length === 0 && !pipeline ? (
            <Welcome onQuickPick={(q) => submit(q, lastDevice.current)} />
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
                            ? () => submit(lastQuery.current, lastDevice.current)
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

        <Composer busy={busy} onSubmit={(q, d) => submit(q, d)} devices={devices} />
      </div>

      <EvidencePanel answer={lastAnswer} />
    </section>
  );
}
