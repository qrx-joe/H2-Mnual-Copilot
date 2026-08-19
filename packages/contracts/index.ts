/**
 * 前后端共享契约类型。
 *
 * 权威定义：docs/architecture/contracts.md（Phase 2）。
 * 契约变更规则（contracts.md §6）：先改文档再改代码；新增字段必须向后兼容。
 *
 * Phase 3 说明：本包暂以纯 TS 源码形态存在（无构建产物），
 * Phase 4 起通过 Next.js transpilePackages 接入 apps/web；
 * Python 侧 schema 在 apps/api 内以 Pydantic 实现，一致性由 T-017 契约测试保证。
 */

/** 技术规范 §44 / ADR-0005：证据充分度只有四态，不使用未校准数值评分。 */
export type EvidenceStatus = "SUFFICIENT" | "PARTIAL" | "INSUFFICIENT" | "CONFLICTING";

/** 技术规范 §37：查询意图，决定检索路由（ERROR_CODE 走精确词法优先）。 */
export type QueryIntent = "ERROR_CODE" | "PARAMETER" | "PROCEDURE" | "TROUBLESHOOTING" | "GENERAL";

/** 引用对象：必须来自真实检索结果（PRD A3），页码 1 起算。 */
export interface Citation {
  citation_id: string;
  chunk_id: string;
  document_title: string;
  version: string;
  page: number;
  excerpt: string;
  support_type: "QUOTE" | "PARAPHRASE";
}

/** POST /api/v1/query 的终值（contracts.md §1.1 Answer）。 */
export interface Answer {
  answer: string;
  steps: string[];
  citations: Citation[];
  evidence_status: EvidenceStatus;
  safety_notice: string | null;
  abstain: boolean;
  abstain_reason: "NO_RELIABLE_SOURCE" | "CONFLICTING_VERSIONS" | null;
  related_documents: { title: string; document_id: string }[];
  suggested_keywords: string[];
}

/** POST /api/v1/query 请求体。device_id 必填（FR-005：答案与设备绑定）。 */
export interface QueryRequest {
  query: string;
  device_id: string;
  version?: string;
  language?: string;
  conversation_id?: string;
}

/** SSE 事件载荷的判别联合（contracts.md §1.1，v1.2：done 新增 message_id/conversation_id）。 */
export type QueryStreamEvent =
  | { event: "retrieval.started"; data: { request_id: string } }
  | { event: "retrieval.completed"; data: { chunk_ids: string[]; retrieval_ms: number } }
  | { event: "generation.started"; data: Record<string, never> }
  | { event: "generation.delta"; data: { text: string } }
  | { event: "verification.completed"; data: { evidence_status: EvidenceStatus } }
  | {
      event: "done";
      data: {
        request_id: string;
        message_id?: string;
        conversation_id?: string;
        answer: Answer;
      };
    }
  | { event: "error"; data: ApiError };

/** GET /sources/{chunk_id}（契约 §1.4）：Source Viewer 定位信息。 */
export interface SourceInfo {
  document: string;
  document_id: string;
  version: string;
  page: number;
  section_path: string;
  excerpt: string;
  file_url: string;
}

/** POST /messages/{id}/feedback 载荷（契约 §1.5，FR-009）。 */
export interface FeedbackBody {
  type: "HELPFUL" | "INCORRECT" | "SAFETY_CONCERN";
  reasons?: string[];
}

/** 统一错误结构（技术规范 §104）。 */
export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string | null;
  };
}
