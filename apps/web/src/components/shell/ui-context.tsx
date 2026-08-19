"use client";

/**
 * 全局 UI 上下文：源文件抽屉、上传弹窗、toast、主题。
 * 放在独立文件避免 app-shell ↔ 页面组件的循环引用。
 *
 * 主题说明：不维护 React 状态——主题类直接挂在 <html> 上，图标显示
 * 由 CSS dark: 变体驱动，避免"从 DOM 同步到 state"的 effect（React hooks 规则）。
 */

import { createContext, useContext } from "react";

import type { MockSource } from "@/lib/mock-data";

export interface ToastInput {
  tone: "info" | "success";
  title: string;
  message: string;
}

export interface UIContextValue {
  openSource: (source: MockSource) => void;
  closeSource: () => void;
  sourceOpen: boolean;
  activeSource: MockSource | null;
  openUpload: () => void;
  closeUpload: () => void;
  uploadOpen: boolean;
  toast: (t: ToastInput) => void;
  toggleTheme: () => void;
}

export const UIContext = createContext<UIContextValue | null>(null);

export function useUI(): UIContextValue {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error("useUI 必须在 <AppShell> 内使用");
  return ctx;
}
