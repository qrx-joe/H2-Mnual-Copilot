import type { Metadata } from "next";
import "./globals.css";

import { AppShell } from "@/components/shell/app-shell";

export const metadata: Metadata = {
  title: "H2 Manual Copilot",
  description: "问设备，也看证据——氢能设备智能手册助手（Evidence-grounded）。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        {/*
         * 主题初始化内联脚本：首帧前读取 localStorage，避免深色模式闪白。
         * 默认浅色（原型 body[data-theme="light"] 默认值）。
         */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{if(localStorage.getItem('h2-theme')==='dark'){document.documentElement.classList.add('dark')}}catch(e){}`,
          }}
        />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
