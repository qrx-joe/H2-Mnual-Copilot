"use client";

/**
 * 上传弹窗（简化 Admin，ADR-0006）——Phase 5 接真实管线：
 * POST /documents（元数据）→ POST ingest（PDF）→ 轮询 job 到 READY/FAILED。
 */

import { useRef, useState } from "react";

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import { API_BASE, listDevices, uploadPdf, type ApiDevice } from "@/lib/api";

const DOC_TYPES = [
  { value: "MAINTENANCE", label: "Maintenance" },
  { value: "OPERATION", label: "Operation" },
  { value: "SAFETY", label: "Safety" },
  { value: "ERROR_CODES", label: "Error codes" },
  { value: "FAQ", label: "FAQ" },
];

export function UploadModal() {
  const { uploadOpen, closeUpload, toast } = useUI();
  const [title, setTitle] = useState("");
  const [deviceId, setDeviceId] = useState("hx100");
  const [docType, setDocType] = useState("MAINTENANCE");
  const [version, setVersion] = useState("2.1");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [devices, setDevices] = useState<ApiDevice[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  if (!uploadOpen) return null;

  // 打开时拉取设备列表（失败回落默认 hx100）
  if (devices.length === 0) {
    listDevices()
      .then(setDevices)
      .catch(() => setDevices([{ device_id: "hx100", name: "HX-100 Electrolyzer", current_version: "" }]));
  }

  const deviceOptions =
    devices.length > 0
      ? devices
      : [{ device_id: "hx100", name: "HX-100 Electrolyzer", current_version: "" }];

  const reset = () => {
    setTitle("");
    setFile(null);
    setVersion("2.1");
    setUploading(false);
  };

  const submit = async () => {
    if (!file || !title.trim() || uploading) return;
    setUploading(true);
    try {
      toast({ tone: "info", title: "Parsing document", message: `${file.name} → hash → parse → chunk → embed → validate` });
      await uploadPdf({
        deviceId,
        title: title.trim(),
        documentType: docType,
        version: version || "1.0",
        file,
      });
      toast({ tone: "success", title: "Knowledge ready", message: `${title.trim()} ${version} 已完成索引。` });
      reset();
      closeUpload();
    } catch (e) {
      toast({ tone: "info", title: "解析失败", message: e instanceof Error ? e.message : String(e) });
      setUploading(false);
    }
  };

  const inputCls =
    "h-10 w-full rounded-xl border border-line bg-surface px-3 text-[12px] outline-none focus:border-blue disabled:opacity-50";

  return (
    <button
      aria-label="关闭上传弹窗"
      className="fixed inset-0 z-[160] grid place-items-center bg-black/35 p-6 backdrop-blur-md"
      onClick={closeUpload}
    >
      <div
        role="dialog"
        aria-label="添加知识文档"
        className="w-[min(460px,100%)] rounded-[26px] border border-line-soft bg-surface p-6 text-center shadow-e3"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="mx-auto grid h-[50px] w-[50px] place-items-center rounded-2xl bg-blue-soft text-blue">
          <Icon name="upload" />
        </span>
        <h3 className="mt-3 text-[17px] font-semibold">Add knowledge document</h3>
        <p className="mx-auto mt-1.5 max-w-[360px] text-[11px] leading-relaxed text-ink-2">
          上传将走真实管线（{API_BASE}）：校验 → hash → 解析 → 分块 → 向量化 → READY。
        </p>

        <div className="mt-4 grid gap-2 text-left">
          <input
            className={inputCls}
            placeholder="文档标题（如 HX-100 Maintenance Manual）"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={uploading}
            aria-label="文档标题"
          />
          <div className="grid grid-cols-3 gap-2">
            <select
              className={inputCls}
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              disabled={uploading}
              aria-label="设备"
            >
              {deviceOptions.map((d) => (
                <option key={d.device_id} value={d.device_id}>
                  {d.name}
                </option>
              ))}
            </select>
            <select
              className={inputCls}
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              disabled={uploading}
              aria-label="文档类型"
            >
              {DOC_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            <input
              className={inputCls}
              placeholder="版本"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              disabled={uploading}
              aria-label="版本号"
            />
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,application/pdf"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button
            className={`${inputCls} border-dashed text-ink-2`}
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
          >
            {file ? `已选择：${file.name}` : "选择 PDF 文件（≤50MB）"}
          </button>
        </div>

        <div className="mt-4 grid gap-2">
          <button
            className="h-[42px] rounded-full bg-blue text-[12px] font-semibold text-white hover:bg-blue-hover active:scale-[.98] disabled:opacity-40"
            disabled={!file || !title.trim() || uploading}
            onClick={submit}
          >
            {uploading ? "索引中…" : "Upload & index"}
          </button>
          <button
            className="h-[42px] rounded-full bg-surface-3 text-[12px] font-semibold hover:brightness-[.98]"
            onClick={closeUpload}
            disabled={uploading}
          >
            Cancel
          </button>
        </div>
      </div>
    </button>
  );
}
