/**
 * 后端 API 客户端（契约 docs/architecture/contracts.md）。
 *
 * SSE 消费：fetch + ReadableStream 增量解析（parseSSE 处理完整块）；
 * 这是 Phase 4 留下的 seam 的真实接线。
 */

import type { EvidenceStatus } from "./evidence";
import { parseSSE, type SSEEvent } from "./sse";

// 非敏感配置：仅 API 地址，允许 NEXT_PUBLIC_ 前缀（密钥仍然只允许服务端，§66）
export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ApiCitation {
  citation_id: string;
  chunk_id: string;
  document_title: string;
  version: string;
  page: number;
  excerpt: string;
  support_type: string;
}

export interface ApiAnswer {
  answer: string;
  steps: string[];
  citations: ApiCitation[];
  evidence_status: EvidenceStatus;
  safety_notice: string | null;
  abstain: boolean;
  abstain_reason: string | null;
  related_documents: { title: string }[];
  suggested_keywords: string[];
}

export interface QueryStreamHandlers {
  onEvent: (ev: SSEEvent) => void;
}

export async function streamQuery(
  body: { query: string; device_id: string; version?: string | null },
  handlers: QueryStreamHandlers,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok || !resp.body) {
    // 网络/网关层错误：非 SSE，直接抛给调用方渲染错误卡
    throw new Error(`API ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;

  while (!finished) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE 以空行分块；最后一段可能不完整，留在 buffer
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      if (!block.trim()) continue;
      const events = parseSSE(block);
      for (const ev of events) {
        handlers.onEvent(ev);
        if (ev.event === "done" || ev.event === "error") finished = true;
      }
    }
  }
}

export interface ApiDevice {
  device_id: string;
  name: string;
  current_version: string;
}

export async function listDevices(): Promise<ApiDevice[]> {
  const resp = await fetch(`${API_BASE}/api/v1/devices`);
  if (!resp.ok) throw new Error(`devices ${resp.status}`);
  const data = (await resp.json()) as { devices: ApiDevice[] };
  return data.devices ?? [];
}

export interface ApiDocument {
  document_id: string;
  title: string;
  device_id: string;
  type: string;
  language: string;
  trust_level: string;
  status: string;
  version: string | null;
  parse_status: string | null;
}

export async function listDocuments(): Promise<ApiDocument[]> {
  const resp = await fetch(`${API_BASE}/api/v1/documents`);
  if (!resp.ok) throw new Error(`documents ${resp.status}`);
  const data = (await resp.json()) as { documents: ApiDocument[] };
  return data.documents ?? [];
}

export interface UploadResult {
  job_id: string | null;
  document_version_id: string;
  deduplicated: boolean;
}

/** 真实上传：先建文档元数据，再触发 ingest 并轮询到终态。 */
export async function uploadPdf(params: {
  deviceId: string;
  title: string;
  documentType: string;
  version: string;
  file: File;
  onProgress?: (pct: number, status: string) => void;
}): Promise<UploadResult> {
  const createResp = await fetch(`${API_BASE}/api/v1/documents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_id: params.deviceId,
      title: params.title,
      document_type: params.documentType,
      trust_level: "A_OFFICIAL",
      language: "en",
    }),
  });
  if (!createResp.ok) throw new Error(`create ${createResp.status}`);
  const { document_id } = (await createResp.json()) as { document_id: string };

  const form = new FormData();
  form.append("file", params.file);
  const ingestResp = await fetch(
    `${API_BASE}/api/v1/documents/${document_id}/ingest?version=${encodeURIComponent(params.version)}`,
    { method: "POST", body: form },
  );
  if (!ingestResp.ok) throw new Error(`ingest ${ingestResp.status}`);
  const result = (await ingestResp.json()) as UploadResult;

  // 轮询到终态（READY / FAILED）；去重直接视为完成
  if (result.job_id) {
    for (let i = 0; i < 120; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      const jobResp = await fetch(`${API_BASE}/api/v1/ingestion-jobs/${result.job_id}`);
      if (!jobResp.ok) continue;
      const job = (await jobResp.json()) as {
        status: string;
        progress: number;
        error: string | null;
      };
      params.onProgress?.(job.progress, job.status);
      if (job.status === "READY") return result;
      if (job.status === "FAILED") throw new Error(job.error ?? "解析失败");
    }
    throw new Error("解析超时（120s）");
  }
  return result;
}
