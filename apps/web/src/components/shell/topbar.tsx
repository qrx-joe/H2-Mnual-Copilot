"use client";

/**
 * 顶栏（原型 .topbar）：移动端菜单按钮 + 页面上下文 + 知识库状态 + 上传 + 主题切换。
 */

import { usePathname } from "next/navigation";

import { Icon } from "@/components/ui/icon";
import { useUI } from "@/components/shell/ui-context";

const CONTEXT: Record<string, { parent: string; current: string }> = {
  "/": { parent: "Hydrogen Lab", current: "HX-100 · Knowledge Copilot" },
  "/knowledge": { parent: "Knowledge governance", current: "Knowledge Library" },
};

export function Topbar({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const pathname = usePathname();
  const { openUpload, toggleTheme } = useUI();
  const ctx = CONTEXT[pathname] ?? { parent: "H2 Manual Copilot", current: "" };

  return (
    <header className="sticky top-0 z-40 flex h-[var(--spacing-topbar)] items-center justify-between border-b border-line-soft bg-glass px-5 backdrop-blur-2xl">
      <div className="flex min-w-0 items-center gap-2">
        <button
          aria-label="打开导航"
          className="hidden h-9 w-9 place-items-center rounded-full text-ink-2 hover:bg-surface-3 hover:text-ink max-[940px]:grid"
          onClick={onOpenMobileNav}
        >
          <Icon name="menu" />
        </button>
        <strong className="truncate text-[12px]">{ctx.parent}</strong>
        <span className="text-ink-3 max-[680px]:hidden">/</span>
        <span className="max-w-[260px] truncate text-[12px] text-ink-3 max-[680px]:hidden">{ctx.current}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="inline-flex h-[29px] items-center gap-[7px] rounded-full bg-green-soft px-2.5 text-[11px] font-semibold text-green max-[680px]:hidden">
          <span className="h-[7px] w-[7px] rounded-full bg-green" />
          Knowledge ready
        </span>
        <button
          className="inline-flex h-[38px] items-center gap-[7px] rounded-full border border-line bg-surface px-4 text-[12px] font-semibold hover:brightness-[.98] active:scale-[.97]"
          onClick={openUpload}
        >
          <Icon name="upload" className="h-[15px] w-[15px]" />
          Upload
        </button>
        <button
          aria-label="切换深浅主题"
          className="grid h-9 w-9 place-items-center rounded-full text-ink-2 hover:bg-surface-3 hover:text-ink"
          onClick={toggleTheme}
        >
          {/* 图标随主题类切换显示（CSS 驱动，避免 DOM→state 同步） */}
          <Icon name="moon" className="dark:hidden" />
          <Icon name="sun" className="hidden dark:block" />
        </button>
      </div>
    </header>
  );
}
