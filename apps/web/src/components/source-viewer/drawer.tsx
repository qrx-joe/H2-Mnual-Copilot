"use client";

/**
 * Source Viewer 抽屉（T-020）。
 *
 * 真实链路：点击引用（带 chunkId）→ GET /sources/{chunk_id} → 原始 PDF 以
 * iframe 内嵌打开并跳转对应页（Chromium 原生查看器支持 #page=N）。
 * 已知边界（phase6 报告）：页内文本高亮需 PDF.js 文本层，MVP 以
 * "高亮摘录卡 + 精确跳页"保证可核对性，PDF.js 高亮留待后续版本。
 * 演示数据（无 chunkId，如 Knowledge 行点击）沿用模拟页。
 *
 * 结构：外壳负责开关；SourceBody 以 chunkId 为 key——切换来源时重挂载，
 * 加载态成为初始 state，避免 effect 内同步 setState（React hooks 规则）。
 */

import { useEffect, useState } from "react";

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import { Badge } from "@/components/ui/badge";
import { API_BASE, getSource } from "@/lib/api";
import type { MockSource } from "@/lib/mock-data";

export function SourceDrawer() {
  const { sourceOpen, closeSource, activeSource } = useUI();
  if (!sourceOpen || !activeSource) return null;

  return (
    <>
      <button
        aria-label="关闭源文件"
        className="fixed inset-0 z-[130] bg-black/25 backdrop-blur-[3px]"
        onClick={closeSource}
      />
      <aside
        role="dialog"
        aria-label={`源文件：${activeSource.title}`}
        className="fixed bottom-2.5 right-2.5 top-2.5 z-[140] flex w-[min(760px,calc(100vw-20px))] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e3"
      >
        <SourceBody key={activeSource.chunkId ?? "demo"} source={activeSource} onClose={closeSource} />
      </aside>
    </>
  );
}

function SourceBody({ source: s, onClose }: { source: MockSource; onClose: () => void }) {
  // chunkId 存在 → 初始即加载态；effect 只发起异步请求（setState 全在回调中）
  const [meta, setMeta] = useState<{
    document: string;
    version: string;
    page: number;
    excerpt: string;
    fileUrl: string | null;
  } | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!s.chunkId) return;
    let cancelled = false;
    getSource(s.chunkId)
      .then((info) => {
        if (cancelled) return;
        setMeta({
          document: info.document,
          version: `v${info.version}`,
          page: info.page,
          excerpt: info.excerpt,
          fileUrl: `${API_BASE}${info.file_url}`,
        });
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [s.chunkId]);

  const title = meta?.document ?? s.title;
  const version = meta?.version ?? s.version;
  const page = meta?.page ?? s.page;
  const loading = Boolean(s.chunkId) && !meta && !failed;

  return (
    <>
      <div className="flex min-h-[62px] items-center gap-2 border-b border-line-soft px-4">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-blue-soft text-blue">
          <Icon name="doc" className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <strong className="block truncate text-[13px]">{title}</strong>
          <div className="mt-0.5 flex items-center gap-1.5">
            <span className="text-[10px] text-ink-3">
              Version {version.replace("v", "")} · Page {page}
            </span>
            {meta?.fileUrl ? <Badge tone="green">Original PDF</Badge> : <Badge tone="blue">Demo</Badge>}
          </div>
        </div>
        <button
          aria-label="关闭"
          className="grid h-9 w-9 place-items-center rounded-full text-ink-2 hover:bg-surface-3 hover:text-ink"
          onClick={onClose}
        >
          <Icon name="x" />
        </button>
      </div>

      {/* 高亮摘录卡：引用原文与 Evidence 面板同源（可核对性） */}
      <div className="border-b border-line-soft px-4 py-3">
        <div className="mb-1.5 text-[10px] font-bold text-ink-3">REFERENCED PASSAGE</div>
        <div className="rounded-xl bg-blue-soft p-3 text-[11px] leading-relaxed">
          {meta?.excerpt ?? s.excerpt}
        </div>
      </div>

      {/* 主体：真实 PDF（iframe 跳页）或演示页 */}
      <div className="grid min-h-0 flex-1 place-items-stretch bg-surface-3">
        {loading ? (
          <div className="grid place-items-center text-[11px] text-ink-3">加载源文件…</div>
        ) : meta?.fileUrl ? (
          <iframe
            key={`${meta.fileUrl}#${page}`}
            src={`${meta.fileUrl}#page=${page}&toolbar=1&view=FitH`}
            title={`${title} Page ${page}`}
            className="h-full w-full border-0 bg-white"
          />
        ) : (
          <div className="grid place-items-start justify-items-center overflow-auto p-6">
            <article className="relative min-h-[560px] w-[min(520px,100%)] rounded bg-white px-[52px] py-12 text-ink shadow-[0_8px_30px_rgba(0,0,0,.12)] max-[680px]:px-7">
              <div className="text-[8px] uppercase tracking-widest text-ink-2">
                {title} · Referenced section
              </div>
              <h2 className="mt-2 text-[23px] leading-tight text-[#1d1d1f]">Section · Page {page}</h2>
              <div className="mt-3 rounded-lg bg-[rgba(0,113,227,.11)] p-3 text-[11px] leading-relaxed text-[#1d1d1f] outline-2 outline-[rgba(0,113,227,.17)]">
                {meta?.excerpt ?? s.excerpt}
              </div>
              <div className="mt-4 border-l-[3px] border-[#ff9500] bg-[rgba(255,149,0,.10)] p-3 text-[10px] leading-relaxed text-[#1d1d1f]">
                <strong>Safety:</strong> Do not bypass interlocks or alter protected operating
                parameters while diagnosing the alarm.
              </div>
              <div className="absolute bottom-7 right-12 text-[8px] text-ink-3 max-[680px]:right-7">
                {page}
              </div>
              <div className="mt-2 text-[9px] text-ink-3">
                （演示页：真实引用点击会内嵌打开原始 PDF 并跳页）
              </div>
            </article>
          </div>
        )}
      </div>
    </>
  );
}
