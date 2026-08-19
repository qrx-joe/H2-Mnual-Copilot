"use client";

/**
 * 上传弹窗（简化 Admin，ADR-0006）：MVP 只提供"上传 + 状态"入口。
 * Phase 4 为界面原型：选择文件后模拟 hash→parse→chunk→embed 流程提示；
 * Phase 5（T-014/T-021）接 POST /documents/{id}/ingest 真实管线与轮询。
 */

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";

export function UploadModal() {
  const { uploadOpen, closeUpload, toast } = useUI();
  if (!uploadOpen) return null;

  const simulateUpload = async () => {
    closeUpload();
    toast({ tone: "info", title: "Parsing document", message: "模拟：hash → parse → chunk → embed → validate" });
    await new Promise((r) => setTimeout(r, 900));
    toast({ tone: "success", title: "Knowledge ready", message: "HX-100 Service FAQ v1.0 已完成索引（原型模拟）。" });
  };

  return (
    <button
      aria-label="关闭上传弹窗"
      className="fixed inset-0 z-[160] grid place-items-center bg-black/35 p-6 backdrop-blur-md"
      onClick={closeUpload}
    >
      <div
        role="dialog"
        aria-label="添加知识文档"
        className="w-[min(430px,100%)] rounded-[26px] border border-line-soft bg-surface p-6 text-center shadow-e3"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="mx-auto grid h-[50px] w-[50px] place-items-center rounded-2xl bg-blue-soft text-blue">
          <Icon name="upload" />
        </span>
        <h3 className="mt-3 text-[17px] font-semibold">Add knowledge document</h3>
        <p className="mx-auto mt-2 max-w-[340px] text-[11px] leading-relaxed text-ink-2">
          这是上传工作流原型。生产版应继续做 MIME 校验、文件哈希、恶意文件扫描、版本字段与解析状态追踪（技术规范 §65）。
        </p>
        <div className="mt-4 grid gap-2">
          <button
            className="h-[42px] rounded-full bg-blue text-[12px] font-semibold text-white hover:bg-blue-hover active:scale-[.98]"
            onClick={simulateUpload}
          >
            Choose PDF
          </button>
          <button
            className="h-[42px] rounded-full bg-surface-3 text-[12px] font-semibold hover:brightness-[.98]"
            onClick={closeUpload}
          >
            Cancel
          </button>
        </div>
      </div>
    </button>
  );
}
