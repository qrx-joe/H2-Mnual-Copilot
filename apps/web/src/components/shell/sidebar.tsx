"use client";

/**
 * 侧边栏导航（原型 .sidebar）。
 * 与原型的差异（ADR-0006 裁决）：导航只保留 Ask / Knowledge；
 * 原型的 Evaluation / Settings 不在 MVP 范围，不建路由。
 * 940px 以下：固定定位抽屉化，由顶栏菜单按钮唤出。
 */

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/ui/icon";

const NAV = [
  { href: "/", label: "Ask", icon: "spark" as const, key: "⌘K" },
  { href: "/knowledge", label: "Knowledge", icon: "book" as const, key: "6" },
];

export function Sidebar({ mobileOpen, onClose }: { mobileOpen: boolean; onClose: () => void }) {
  const pathname = usePathname();

  return (
    <aside
      aria-label="主导航"
      className={`fixed bottom-0 left-0 top-0 z-50 flex w-[var(--spacing-sidebar)] flex-col border-r border-line-soft bg-glass backdrop-blur-2xl transition-transform duration-200 max-[940px]:w-[250px] max-[940px]:shadow-e3 ${
        mobileOpen ? "translate-x-0" : "max-[940px]:-translate-x-[104%]"
      }`}
    >
      {/* 品牌（原型 .brand + .mark 轨道图标） */}
      <div className="flex h-[72px] items-center gap-3 px-[18px] py-4">
        <div className="relative grid h-[38px] w-[38px] place-items-center rounded-xl bg-ink text-surface">
          <span className="absolute h-[11px] w-[30px] rounded-full border border-current opacity-25 rotate-[28deg]" />
          <span className="absolute h-[11px] w-[30px] rounded-full border border-current opacity-25 -rotate-[28deg]" />
          <span className="h-[7px] w-[7px] rounded-full bg-[#5ac8fa] shadow-[0_0_0_4px_rgba(90,200,250,.12)]" />
        </div>
        <div className="min-w-0">
          <strong className="block text-[15px] tracking-tight">H2 Manual Copilot</strong>
          <small className="mt-px block text-[10px] text-ink-3">Evidence-grounded workspace</small>
        </div>
      </div>

      <nav className="px-3 py-2">
        <div className="px-2.5 pb-1.5 pt-2 text-[10px] font-semibold uppercase tracking-wider text-ink-3">
          Workspace
        </div>
        <div className="grid gap-[3px]">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-[42px] items-center gap-[11px] rounded-[10px] px-[11px] text-[13px] font-medium transition-colors ${
                  active
                    ? "bg-surface text-ink shadow-e1 [&>svg:first-child]:text-blue"
                    : "text-ink-2 hover:bg-surface-3 hover:text-ink"
                }`}
              >
                <Icon name={item.icon} className="h-[18px] w-[18px] shrink-0" />
                {item.label}
                <span className="ml-auto grid h-5 min-w-[22px] place-items-center rounded-full bg-surface-3 px-1.5 text-[10px] text-ink-3">
                  {item.key}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="mt-auto border-t border-line-soft p-3">
        <div className="flex items-center gap-2 rounded-xl p-2.5 hover:bg-surface-3">
          <span className="grid h-[34px] w-[34px] place-items-center rounded-full bg-[#636366] text-[11px] font-bold text-white">
            OP
          </span>
          <div className="min-w-0 flex-1">
            <strong className="block text-[12px]">Operator</strong>
            <small className="mt-px block text-[10px] text-ink-3">Knowledge Admin · Demo</small>
          </div>
        </div>
      </div>
    </aside>
  );
}
