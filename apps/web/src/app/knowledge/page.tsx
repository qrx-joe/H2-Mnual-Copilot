"use client";

/**
 * Knowledge Library（原型 #page-knowledge）：文档表格 + 筛选 + 搜索 + 上传入口。
 * 行数据为固定演示数据（Phase 5 换 GET /documents）；"查看"打开 Source Viewer。
 */

import { useMemo, useState } from "react";

import { useUI } from "@/components/shell/ui-context";
import { Badge } from "@/components/ui/badge";
import { Icon } from "@/components/ui/icon";
import { MOCK_DOCUMENTS, type MockDocumentRow } from "@/lib/mock-data";

type Filter = "all" | "active" | "superseded";

export default function KnowledgePage() {
  const { openSource, openUpload } = useUI();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return MOCK_DOCUMENTS.filter(
      (r) =>
        (!q || `${r.title} ${r.device} ${r.version}`.toLowerCase().includes(q)) &&
        (filter === "all" || r.status.toLowerCase() === filter),
    );
  }, [query, filter]);

  const openRow = (r: MockDocumentRow) => {
    openSource({
      title: r.title,
      version: `v${r.version}`,
      page: r.viewPage ?? 1,
      trust: r.trust,
      excerpt: "Demo excerpt — Phase 5 将展示该文档的真实检索段落（chunk 摘录）。",
    });
  };

  return (
    <section className="mx-auto max-w-[1440px] px-7 pb-16 pt-7 max-[680px]:px-3">
      <div className="mb-5">
        <div className="mb-2 text-[10px] font-bold tracking-wider text-ink-3 uppercase">
          Knowledge governance
        </div>
        <h1 className="text-[clamp(30px,4vw,40px)] leading-tight font-semibold tracking-tighter">
          Knowledge Library
        </h1>
        <p className="mt-2.5 max-w-[720px] text-[14px] leading-relaxed text-ink-2">
          管理设备资料、版本、可信等级与索引状态。默认检索只使用 Active / Current 版本，历史版本保留用于冲突识别与审计（ADR-0004）。
        </p>
      </div>

      {/* 工具栏：搜索 + 状态筛选 + 上传 */}
      <div className="mb-3.5 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[260px] flex-1">
          <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-3" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索文档、设备或版本…"
            aria-label="搜索文档"
            className="h-10 w-full rounded-xl border border-line bg-surface pl-10 pr-3 text-[12px] outline-none focus:border-blue focus:shadow-[0_0_0_3px_rgba(0,113,227,.12)]"
          />
        </div>
        {(["all", "active", "superseded"] as Filter[]).map((f) => (
          <button
            key={f}
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={`inline-flex h-[33px] items-center rounded-full border px-3 text-[11px] font-semibold ${
              filter === f
                ? "border-[rgba(0,113,227,.25)] bg-blue-soft text-blue"
                : "border-line-soft bg-surface text-ink-2 hover:border-line hover:text-ink"
            }`}
          >
            {f === "all" ? "All" : f === "active" ? "Active" : "Superseded"}
          </button>
        ))}
        <button
          className="inline-flex h-[38px] items-center gap-[7px] rounded-full bg-blue px-4 text-[12px] font-semibold text-white hover:bg-blue-hover"
          onClick={openUpload}
        >
          <Icon name="upload" className="h-[15px] w-[15px]" />
          Add document
        </button>
      </div>

      {/* 文档表格 */}
      <div className="overflow-hidden rounded-r4 border border-line-soft bg-surface shadow-e1">
        <div className="overflow-auto">
          <table className="w-full min-w-[920px] border-collapse">
            <thead>
              <tr>
                {["Document", "Device", "Type", "Version", "Trust", "Status", "Indexed", ""].map((h) => (
                  <th
                    key={h}
                    className="border-b border-line-soft bg-surface-2 px-3.5 py-3 text-left text-[9px] font-bold tracking-wider text-ink-3 uppercase"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="hover:bg-surface-2">
                  <td className="border-b border-line-soft px-3.5 py-3 text-[11px]">
                    <div className="flex items-center gap-2">
                      <span
                        className={`grid h-9 w-9 place-items-center rounded-[11px] ${
                          r.status === "Active" ? "bg-blue-soft text-blue" : "bg-surface-3 text-ink-3"
                        }`}
                      >
                        <Icon name="doc" />
                      </span>
                      <span>
                        <strong className="block text-[11px]">{r.title}</strong>
                        <small className="mt-0.5 block text-[9px] text-ink-3">
                          PDF · {r.pages} pages · {r.language}
                        </small>
                      </span>
                    </div>
                  </td>
                  <td className="border-b border-line-soft px-3.5 py-3 text-[11px]">{r.device}</td>
                  <td className="border-b border-line-soft px-3.5 py-3 text-[11px]">{r.type}</td>
                  <td className="border-b border-line-soft px-3.5 py-3 text-[11px]">{r.version}</td>
                  <td className="border-b border-line-soft px-3.5 py-3">
                    <Badge tone="blue">{r.trust}</Badge>
                  </td>
                  <td className="border-b border-line-soft px-3.5 py-3">
                    <Badge tone={r.status === "Active" ? "green" : "orange"}>{r.status}</Badge>
                  </td>
                  <td className="border-b border-line-soft px-3.5 py-3 text-[11px] text-ink-3">{r.indexed}</td>
                  <td className="border-b border-line-soft px-3.5 py-3">
                    <button
                      aria-label={`查看 ${r.title}`}
                      className="grid h-[30px] w-[30px] place-items-center rounded-full text-ink-3 hover:bg-surface-3 hover:text-ink"
                      onClick={() => openRow(r)}
                    >
                      <Icon name="more" />
                    </button>
                  </td>
                </tr>
              ))}
              {/* 空状态：筛选无结果时的明确反馈（不静默显示空表） */}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-3.5 py-10 text-center text-[11px] text-ink-3">
                    没有匹配的文档。调整搜索词或筛选条件试试。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
