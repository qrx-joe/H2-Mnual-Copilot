"use client";

/**
 * Evidence 面板（原型 .evidence）。
 * 与原型的关键差异（ADR-0005，用户裁决）：数值评分环替换为 evidence status
 * 四态徽章，直接由后端 evidence_status 驱动，不展示任何置信度数值。
 */

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import { evidenceBadge } from "@/lib/evidence";
import type { AnswerModel } from "@/lib/mock-data";

const TONE_CLS = {
  positive: "bg-green-soft text-green",
  caution: "bg-orange-soft text-orange",
  negative: "bg-red-soft text-red",
};

export function EvidencePanel({ answer }: { answer: AnswerModel | null }) {
  const { openSource } = useUI();

  // 空状态（原型 .empty）：初始与拒答时展示
  if (!answer || answer.sources.length === 0) {
    return (
      <aside className="flex min-h-[680px] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e1 max-[940px]:min-h-[420px]">
        <div className="flex min-h-[58px] items-center gap-2 border-b border-line-soft px-4">
          <Icon name="doc" className="text-blue" />
          <strong className="text-[12px]">Evidence</strong>
          <small className="ml-auto text-[9px] text-ink-3">
            {answer ? "0 reliable sources" : "No sources yet"}
          </small>
        </div>
        <div className="grid flex-1 place-items-center p-8 text-center">
          <div className="max-w-[250px]">
            <span className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-[15px] bg-surface-3 text-ink-3">
              <Icon name="book" />
            </span>
            <h3 className="text-[12px] font-semibold">
              {answer ? "没有可靠来源，系统已拒答" : "证据会出现在这里"}
            </h3>
            <p className="mt-1.5 text-[10px] leading-relaxed text-ink-3">
              {answer
                ? answer.suggestedKeywords?.length
                  ? "可尝试左侧推荐关键词，或更换设备/版本后重试。"
                  : "当前问题在知识库中没有匹配证据。"
                : "每条关键事实绑定具体文档、版本和页码。点击来源可打开对应页。"}
            </p>
          </div>
        </div>
      </aside>
    );
  }

  const badge = evidenceBadge(answer.evidenceStatus);

  return (
    <aside className="flex min-h-[680px] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e1 max-[940px]:min-h-[420px]">
      <div className="flex min-h-[58px] items-center gap-2 border-b border-line-soft px-4">
        <Icon name="doc" className="text-blue" />
        <strong className="text-[12px]">Evidence</strong>
        <small className="ml-auto text-[9px] text-ink-3">{answer.sources.length} sources</small>
      </div>

      {/* 状态徽章区（替代原型评分环，ADR-0005） */}
      <div className="border-b border-line-soft px-4 py-3">
        <div className="flex items-center gap-3">
          <span className={`grid h-[38px] w-[38px] place-items-center rounded-xl ${TONE_CLS[badge.tone]}`}>
            <Icon name={badge.tone === "positive" ? "check" : "alert"} />
          </span>
          <div>
            <strong className="block text-[11px]">{badge.label}</strong>
            <small className="mt-0.5 block text-[9px] text-ink-3">
              {answer.sources.length} supporting passages · current version
            </small>
          </div>
        </div>
      </div>

      {/* 来源卡列表（原型 .ecard） */}
      <div className="grid content-start gap-2 overflow-auto p-2.5">
        {answer.sources.map((s, i) => (
          <button
            key={i}
            onClick={() => openSource(s)}
            className={`rounded-[13px] border p-3 text-left transition-all hover:-translate-y-px hover:bg-surface hover:border-line ${
              i === 0 ? "border-[rgba(0,113,227,.25)] bg-blue-soft" : "border-line-soft bg-surface-2"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="grid h-[29px] w-[29px] shrink-0 place-items-center rounded-lg bg-blue-soft text-blue">
                <Icon name="doc" className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <strong className="block truncate text-[10px]">{s.title}</strong>
                <small className="mt-0.5 block text-[8px] text-ink-3">
                  {s.version} · Page {s.page} · {s.trust}
                </small>
              </div>
            </div>
            {/* 摘录：与 Source Viewer 高亮区同源，保证可核对 */}
            <div className="mt-2 border-l-2 border-[rgba(0,113,227,.24)] pl-2 text-[9.5px] leading-snug text-ink-2">
              {s.excerpt}
            </div>
          </button>
        ))}
      </div>

      <div className="mt-auto border-t border-line-soft p-2.5">
        <button
          className="flex h-[38px] w-full items-center justify-center gap-[7px] rounded-full bg-surface-3 text-[12px] font-semibold hover:brightness-[.98]"
          onClick={() => openSource(answer.sources[0])}
        >
          <Icon name="doc" className="h-[15px] w-[15px]" />
          Open best source
        </button>
      </div>
    </aside>
  );
}
