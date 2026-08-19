"use client";

/**
 * 应用壳层：侧边栏 + 顶栏 + 全局浮层（源文件抽屉/上传弹窗/toast）。
 * 布局对应原型 .shell（grid: sidebar + main）与 940px 以下抽屉化侧边栏。
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { SourceDrawer } from "@/components/source-viewer/drawer";
import { Sidebar } from "@/components/shell/sidebar";
import { Topbar } from "@/components/shell/topbar";
import { UIContext, type ToastInput, type UIContextValue } from "@/components/shell/ui-context";
import { UploadModal } from "@/components/upload/upload-modal";
import type { MockSource } from "@/lib/mock-data";

const TOAST_TTL_MS = 4200;

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [source, setActiveSource] = useState<MockSource | null>(null);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [toasts, setToasts] = useState<(ToastInput & { id: number })[]>([]);

  // 主题不进 React 状态：切换时直接改 <html> 类并持久化；
  // 图标与配色全部由 CSS（.dark / dark: 变体）响应，无 DOM→state 同步 effect。
  const toggleTheme = useCallback(() => {
    const el = document.documentElement;
    const next = el.classList.toggle("dark") ? "dark" : "light";
    try {
      localStorage.setItem("h2-theme", next);
    } catch {
      /* 隐私模式下 localStorage 可能不可用，主题不持久化即可 */
    }
  }, []);

  const toast = useCallback((t: ToastInput) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== id)), TOAST_TTL_MS);
  }, []);

  const openSource = useCallback((s: MockSource) => {
    setActiveSource(s);
    setSourceOpen(true);
  }, []);

  const value: UIContextValue = {
    openSource,
    closeSource: () => setSourceOpen(false),
    sourceOpen,
    activeSource: source,
    openUpload: () => setUploadOpen(true),
    closeUpload: () => setUploadOpen(false),
    uploadOpen,
    toast,
    toggleTheme,
  };

  // 全局键盘：⌘K/Ctrl+K 聚焦提问框（原型行为）；ESC 关闭全部浮层
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        router.push("/");
        setTimeout(() => document.getElementById("composer")?.focus(), 30);
      }
      if (e.key === "Escape") {
        setSourceOpen(false);
        setUploadOpen(false);
        setMobileNavOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  return (
    <UIContext.Provider value={value}>
      <div
        className="grid min-h-screen max-[940px]:block"
        style={{ gridTemplateColumns: "var(--spacing-sidebar) minmax(0,1fr)" }}
      >
        <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
        {mobileNavOpen && (
          <button
            aria-label="关闭导航"
            className="fixed inset-0 z-40 bg-black/20 max-[940px]:block"
            onClick={() => setMobileNavOpen(false)}
          />
        )}
        <main className="min-w-0">
          <Topbar onOpenMobileNav={() => setMobileNavOpen(true)} />
          {children}
        </main>
      </div>

      <SourceDrawer />
      <UploadModal />

      {/* toast 堆栈（原型 .toasts：右上角） */}
      <div className="fixed right-4 top-[72px] z-[210] grid w-[min(350px,calc(100vw-36px))] gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className="flex items-start gap-2 rounded-[15px] border border-line-soft bg-glass p-3 shadow-e3 backdrop-blur-xl"
          >
            <span
              className={`grid h-[27px] w-[27px] shrink-0 place-items-center rounded-lg ${
                t.tone === "success" ? "bg-green-soft text-green" : "bg-blue-soft text-blue"
              }`}
            >
              <span
                className={`inline-block h-3 w-3 ${
                  t.tone === "success" ? "bg-green" : "bg-blue"
                } [clip-path:polygon(14%_44%,0_65%,40%_100%,100%_16%,80%_0,37%_62%)]`}
              />
            </span>
            <div className="min-w-0 flex-1">
              <strong className="block text-[11px]">{t.title}</strong>
              <small className="mt-0.5 block text-[10px] leading-snug text-ink-3">{t.message}</small>
            </div>
            <button
              aria-label="关闭提示"
              className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-ink-3 hover:bg-surface-3"
              onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            >
              <svg
                viewBox="0 0 24 24"
                className="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.8}
                strokeLinecap="round"
              >
                <path d="m7 7 10 10M17 7 7 17" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </UIContext.Provider>
  );
}
