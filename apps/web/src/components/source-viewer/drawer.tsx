"use client";

/**
 * Source Viewer 抽屉（原型 .drawer）：模拟 PDF 页 + 高亮引用区 + 页码。
 *
 * Phase 4 边界：PDF 内容为固定演示 DOM（同原型做法），不是真实 PDF 渲染；
 * Phase 5（T-020）替换为 PDF.js 加载原始文件并定位页码。抽屉开关与数据流不变。
 */

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import { Badge } from "@/components/ui/badge";

export function SourceDrawer() {
  const { sourceOpen, closeSource, activeSource } = useUI();
  if (!sourceOpen || !activeSource) return null;

  const s = activeSource;
  const thumbs = [s.page - 2, s.page - 1, s.page, s.page + 1].filter((p) => p > 0);

  return (
    <>
      <button
        aria-label="关闭源文件"
        className="fixed inset-0 z-[130] bg-black/25 backdrop-blur-[3px]"
        onClick={closeSource}
      />
      <aside
        role="dialog"
        aria-label={`源文件：${s.title}`}
        className="fixed bottom-2.5 right-2.5 top-2.5 z-[140] flex w-[min(720px,calc(100vw-20px))] flex-col overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e3"
      >
        {/* 头部：文档 + 版本 + 状态（PRD FR-003 四要素中的三者，摘录在正文中） */}
        <div className="flex min-h-[62px] items-center gap-2 border-b border-line-soft px-4">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-blue-soft text-blue">
            <Icon name="doc" className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <strong className="block truncate text-[13px]">{s.title}</strong>
            <div className="mt-0.5 flex items-center gap-1.5">
              <span className="text-[10px] text-ink-3">Version {s.version.replace("v", "")}</span>
              <Badge tone="blue">{s.trust}</Badge>
              <Badge tone="green">Active</Badge>
            </div>
          </div>
          <button
            aria-label="关闭"
            className="grid h-9 w-9 place-items-center rounded-full text-ink-2 hover:bg-surface-3 hover:text-ink"
            onClick={closeSource}
          >
            <Icon name="x" />
          </button>
        </div>

        <div className="grid min-h-0 flex-1 grid-cols-[110px_minmax(0,1fr)] bg-surface-3 max-[680px]:grid-cols-1">
          {/* 缩略图列（原型 .thumbs，静态示意） */}
          <div className="grid content-start gap-2 border-r border-line-soft bg-surface-2 p-2.5 max-[680px]:hidden">
            {thumbs.map((p) => (
              <div
                key={p}
                className={`relative grid h-[118px] place-items-center rounded-lg border bg-white text-[8px] text-ink-3 ${
                  p === s.page ? "border-2 border-blue" : "border-line-soft"
                }`}
              >
                <span className="absolute bottom-1 right-1.5 font-mono text-ink-2">{p}</span>
              </div>
            ))}
          </div>

          {/* 模拟 PDF 页面（白底固定内容，与抽屉外主题无关） */}
          <div className="grid place-items-start justify-items-center overflow-auto p-6 max-[680px]:p-3">
            <article className="relative min-h-[750px] w-[min(520px,100%)] rounded bg-white px-[52px] py-12 text-ink shadow-[0_8px_30px_rgba(0,0,0,.12)] max-[680px]:min-h-[620px] max-[680px]:px-7">
              <div className="text-[8px] uppercase tracking-widest text-ink-2">
                {s.title} · Referenced section
              </div>
              <h2 className="mt-2 text-[23px] leading-tight text-[#1d1d1f]">Section · Page {s.page}</h2>
              <h3 className="mt-6 text-[14px] text-[#1d1d1f]">Referenced passage</h3>
              {/* 高亮引用区（原型 .highlight）：excerpt 必须与 Evidence 卡片一致（可核对性） */}
              <div className="mt-3 rounded-lg bg-[rgba(0,113,227,.11)] p-3 text-[11px] leading-relaxed text-[#1d1d1f] outline-2 outline-[rgba(0,113,227,.17)]">
                {s.excerpt}
              </div>
              <div className="mt-4 border-l-[3px] border-[#ff9500] bg-[rgba(255,149,0,.10)] p-3 text-[10px] leading-relaxed text-[#1d1d1f]">
                <strong>Safety:</strong> Do not bypass interlocks or alter protected operating
                parameters while diagnosing the alarm.
              </div>
              <div className="absolute bottom-7 right-12 text-[8px] text-ink-3 max-[680px]:right-7">
                {s.page}
              </div>
            </article>
          </div>
        </div>
      </aside>
    </>
  );
}
