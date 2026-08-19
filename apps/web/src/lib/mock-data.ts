/**
 * Phase 4 固定测试数据（非敏感演示数据，取自原型内置场景）。
 * Phase 5 替换为真实 API 数据；场景分类逻辑与 API SSE 桩对齐。
 */

import type { EvidenceStatus } from "./evidence";

export interface MockDevice {
  id: string;
  name: string;
  currentVersion: string;
}

export const MOCK_DEVICES: MockDevice[] = [
  { id: "hx100", name: "HX-100 Electrolyzer", currentVersion: "v2.1" },
  { id: "hx80", name: "HX-80 Electrolyzer", currentVersion: "v1.7" },
  { id: "all", name: "All devices", currentVersion: "Version-aware" },
];

export interface MockDocumentRow {
  id: string;
  title: string;
  device: string;
  type: string;
  version: string;
  language: string;
  pages: number;
  trust: "Official" | "Internal";
  status: "Active" | "Superseded";
  indexed: string;
  viewPage?: number;
}

export const MOCK_DOCUMENTS: MockDocumentRow[] = [
  { id: "d1", title: "HX-100 Maintenance Manual", device: "HX-100", type: "Maintenance", version: "2.1", language: "EN", pages: 184, trust: "Official", status: "Active", indexed: "12 min ago", viewPage: 127 },
  { id: "d2", title: "HX-100 Operation Manual", device: "HX-100", type: "Operation", version: "2.1", language: "EN", pages: 142, trust: "Official", status: "Active", indexed: "12 min ago", viewPage: 32 },
  { id: "d3", title: "HX-100 Safety Guide", device: "HX-100", type: "Safety", version: "2.0", language: "ZH / EN", pages: 58, trust: "Internal", status: "Active", indexed: "1 h ago" },
  { id: "d4", title: "HX-100 Error Code Reference", device: "HX-100", type: "Error codes", version: "2.1", language: "EN", pages: 36, trust: "Official", status: "Active", indexed: "1 h ago", viewPage: 18 },
  { id: "d5", title: "HX-100 Operation Manual", device: "HX-100", type: "Operation", version: "1.9", language: "EN", pages: 138, trust: "Official", status: "Superseded", indexed: "Archived" },
  { id: "d6", title: "HX-80 Maintenance Manual", device: "HX-80", type: "Maintenance", version: "1.7", language: "EN", pages: 126, trust: "Official", status: "Active", indexed: "Yesterday" },
];

export interface MockSource {
  title: string;
  version: string;
  page: number;
  trust: string;
  excerpt: string;
}

/** 回答卡数据模型：kind 对应原型 astatus 三态 + error（服务异常演示态）。 */
export interface AnswerModel {
  kind: "safe" | "warn" | "stop" | "error";
  title: string;
  summary: string;
  steps: string[];
  safety: string | null;
  evidenceStatus: EvidenceStatus;
  sources: MockSource[];
  /** 拒答时展示（FR-006）：最相关资料与推荐关键词 */
  relatedDocuments?: { title: string }[];
  suggestedKeywords?: string[];
  errorCode?: string;
  errorMessage?: string;
}

export type Scenario = "error" | "startup" | "safety" | "noanswer" | "failure";

export function classifyScenario(q: string): Scenario {
  const t = q.toLowerCase();
  if (t.includes("e104")) return "error";
  if (t.includes("采购") || t.includes("价格") || t.includes("多少钱")) return "noanswer";
  if (t.includes("压力") || t.includes("直接调") || t.includes("联锁")) return "safety";
  if (t.includes("启动") || t.includes("检查")) return "startup";
  return "startup"; // 通用问题回落到启动检查场景（固定演示数据）
}

export const SCENARIO_ANSWERS: Record<Scenario, AnswerModel> = {
  error: {
    kind: "safe",
    title: "E104 — Cooling system temperature abnormal",
    summary:
      "当前 HX-100 v2.1 资料将 E104 定义为冷却系统温度异常。手册建议先检查冷却液液位、循环泵运行状态与温度传感器连接，再进入更深层部件诊断。",
    steps: [
      "检查冷却液液位是否处于当前手册规定范围。",
      "确认循环泵处于运行状态，并检查是否存在流量报警。",
      "检查温度传感器连接与信号连续性。",
    ],
    safety: "不要绕过安全联锁，也不要在排查过程中擅自修改受保护的运行参数。",
    evidenceStatus: "SUFFICIENT",
    sources: [
      { title: "HX-100 Maintenance Manual", version: "v2.1", page: 127, trust: "Official", excerpt: "E104 — Cooling system temperature abnormal. Inspect coolant level, circulation pump operating state and temperature sensor connection." },
      { title: "HX-100 Error Code Reference", version: "v2.1", page: 18, trust: "Official", excerpt: "E104 maps to cooling-system temperature alarm; verify coolant and circulation status before escalation." },
      { title: "HX-100 Safety Guide", version: "v2.0", page: 21, trust: "Internal", excerpt: "Do not bypass protected interlocks during alarm inspection and maintenance." },
    ],
  },
  startup: {
    kind: "safe",
    title: "HX-100 startup pre-check",
    summary:
      "启动前检查需要按当前 Operation Manual v2.1 执行。系统定位到的步骤集中在冷却、供水、气体管路、电源与安全联锁五类。",
    steps: [
      "确认冷却系统处于可用状态。",
      "确认供水条件满足启动前要求。",
      "检查气体管路与相关连接状态。",
      "确认主电源与控制系统状态。",
      "确认安全联锁检查已完成且无未处理报警。",
    ],
    safety: "本列表用于定位手册内容，不替代制造商正式启动程序或现场 SOP。",
    evidenceStatus: "SUFFICIENT",
    sources: [
      { title: "HX-100 Operation Manual", version: "v2.1", page: 32, trust: "Official", excerpt: "Complete the cooling, feed-water, gas-line, power and safety-interlock pre-start checks before enabling the startup sequence." },
      { title: "HX-100 Safety Guide", version: "v2.0", page: 11, trust: "Internal", excerpt: "Startup shall not proceed while an unresolved safety interlock condition is present." },
    ],
  },
  safety: {
    kind: "warn",
    title: "需要确认设备版本与明确参数来源",
    summary:
      "当前问题涉及受保护运行参数。知识库没有足够证据支持给出一个可直接执行的压力设定值，而且不同版本资料可能存在参数差异，因此系统不会猜测。",
    steps: [
      "确认当前设备型号、序列或配置。",
      "确认现场使用的正式 Operation Manual 版本。",
      "定位该版本中对应运行参数表或启动 SOP。",
    ],
    safety: "不要依据聊天答案直接修改压力、阀门或安全联锁。应以制造商当前有效资料与现场授权人员判断为准。",
    evidenceStatus: "CONFLICTING",
    sources: [
      { title: "HX-100 Operation Manual", version: "v2.1", page: 41, trust: "Official", excerpt: "Protected operating parameters shall be verified against the applicable equipment configuration before adjustment." },
      { title: "HX-100 Operation Manual", version: "v1.9 · Superseded", page: 39, trust: "Official", excerpt: "Historical version retained for audit. Do not use as the default operating source." },
    ],
  },
  noanswer: {
    kind: "stop",
    title: "当前知识库无法可靠回答",
    summary:
      "已检索当前设备资料，但没有找到采购价格、报价或商业合同信息。为了避免把不存在的资料编成答案，系统在这里停止生成。",
    steps: [],
    safety: null,
    evidenceStatus: "INSUFFICIENT",
    sources: [],
    relatedDocuments: [{ title: "HX-100 Operation Manual" }, { title: "HX-100 Maintenance Manual" }],
    suggestedKeywords: ["采购", "价格", "商务合同", "配置清单"],
  },
  failure: {
    kind: "error",
    title: "服务暂时不可用",
    summary: "演示用途：模拟上游模型服务不可用时的错误态。真实系统中此卡片由 MODEL_UNAVAILABLE 错误结构渲染。",
    steps: [],
    safety: null,
    evidenceStatus: "INSUFFICIENT",
    sources: [],
    errorCode: "MODEL_UNAVAILABLE",
    errorMessage: "Upstream model provider timed out after 2 retries.",
  },
};

export const QUICK_PROMPTS = [
  { icon: "alert" as const, tone: "orange" as const, title: "Error code", desc: "查看故障解释、排查顺序与对应手册页。", query: "E104 是什么？应该先检查什么？" },
  { icon: "check" as const, tone: "blue" as const, title: "Startup checklist", desc: "从操作手册生成可追溯的启动前检查列表。", query: "HX-100 启动前需要完成哪些检查？" },
  { icon: "shield" as const, tone: "green" as const, title: "Safety boundary", desc: "演示关键参数缺证据时的版本确认与安全拒答。", query: "把设备压力直接调到多少最合适？" },
  { icon: "search" as const, tone: "red" as const, title: "No-answer test", desc: "知识库不存在相关资料时，系统应该停止生成。", query: "HX-100 的采购价格是多少？" },
];

export const PIPELINE_STEPS = [
  { id: 1, label: "Query routing" },
  { id: 2, label: "Hybrid retrieval" },
  { id: 3, label: "Reranking" },
  { id: 4, label: "Citation & safety verification" },
];
