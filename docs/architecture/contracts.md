# H2 Manual Copilot · 接口与数据契约（Phase 2）

> 版本：v1.0  
> 日期：2026-08-19（Asia/Shanghai）  
> 来源：技术规范 §43、§56–61、§104–105；PRD FR 清单；ADR-0004/0005/0006  
> 落地方式：Phase 3 起由 `packages/contracts` 以 Pydantic（Python）+ zod/TS 类型双语实现，本文为权威定义  
> 标注：〔新增〕= 技术规范未明文定义、由 PRD 需求推导的契约（来源已注明），需在 Phase 3 评审确认

## 1. REST API（Base：`/api/v1`）

### 1.1 问答

`POST /api/v1/query`（SSE 流式；响应头 `content-type: text/event-stream`）

请求：

```json
{
  "query": "E104",
  "device_id": "hx100",
  "version": "2.1",          // 可选；缺省=该设备 is_current 且 ACTIVE（ADR-0004）
  "language": "zh-CN",       // 用户界面语言，不影响检索语言
  "conversation_id": "..."   // 可选；缺省新建会话
}
```

SSE 事件载荷：

| 事件 | data 结构 |
| --- | --- |
| `retrieval.started` | `{"request_id": "..."}` |
| `retrieval.completed` | `{"chunk_ids": [...], "retrieval_ms": 123}` |
| `generation.started` | `{}` |
| `generation.delta` | `{"text": "..."}`（answer 增量） |
| `verification.completed` | `{"evidence_status": "SUFFICIENT"}` |
| `done` | `{Answer 对象（见下），"request_id": "..."}` |
| `error` | `统一错误结构（§5），流中断即终止` |

`Answer`（终值，技术规范 §43 + ADR-0005）：

```json
{
  "answer": "…",
  "steps": ["…"],
  "citations": [
    {"citation_id": "…", "chunk_id": "…", "document_title": "HX-100 Maintenance Manual",
     "version": "2.1", "page": 127, "excerpt": "…", "support_type": "QUOTE"}
  ],
  "evidence_status": "SUFFICIENT | PARTIAL | INSUFFICIENT | CONFLICTING",
  "safety_notice": "… | null",
  "abstain": false,
  "abstain_reason": "NO_RELIABLE_SOURCE | CONFLICTING_VERSIONS | null",
  "related_documents": [{"title": "…", "document_id": "…"}],   // 拒答时的最相关资料（FR-006）〔新增，来源 PRD §28〕
  "suggested_keywords": ["…"]                                  // 拒答时的推荐关键词〔新增，来源 PRD §28〕
}
```

### 1.2 文档管理（Admin 密码）

| 方法与路径 | 语义 | 要点 |
| --- | --- | --- |
| `POST /documents` | 创建元数据 | device_id/type/language/trust_level 必填；状态初始 DRAFT（§50） |
| `GET /documents` | 列表 | 过滤：device/status/type/language；分页 |
| `GET /documents/{id}` | 详情 | 含版本列表与当前版本 |
| `PATCH /documents/{id}` | 更新元数据/状态 | 状态迁移限 DRAFT→ACTIVE→SUPERSEDED→ARCHIVED（§19） |
| `DELETE /documents/{id}` | 软删除 | 置 ARCHIVED，不物理删（§58） |

### 1.3 接入

| 方法与路径 | 语义 | 要点 |
| --- | --- | --- |
| `POST /documents/{id}/ingest` | 上传 PDF 触发解析 | multipart；PDF-only、≤50MB、MIME+扩展名双重校验、sha256 去重；返回 `{"job_id": "…"}`；异步执行（§75） |
| `GET /ingestion-jobs/{id}` | 轮询任务状态 | `{"status": "PARSING", "progress": 47, "error": null}`（§19 状态机） |

### 1.4 溯源

`GET /sources/{chunk_id}`（技术规范 §60）

```json
{
  "document": "HX-100 Maintenance Manual",
  "version": "2.1",
  "page": 127,
  "excerpt": "…",
  "file_url": "/api/v1/files/{storage_key}"   // 〔新增〕Source Viewer 加载原始 PDF 用，短期签名 URL 语义
}
```

### 1.5 反馈〔新增，来源 PRD FR-009 + 技术规范 §13 Feedback 实体〕

`POST /messages/{message_id}/feedback`

```json
{"type": "HELPFUL | INCORRECT | SAFETY_CONCERN",
 "reasons": ["WRONG_ANSWER", "IRRELEVANT_SOURCE", "WRONG_VERSION", "OUTDATED", "SAFETY_RISK"]}
```

幂等：同一 message 同 type 覆盖上一次提交。

### 1.6 设备〔新增，来源 FR-005 + 原型设备选择器〕

`GET /devices` → `[{"device_id": "hx100", "name": "HX-100 Electrolyzer", "current_version": "2.1"}]`

## 2. 数据契约（Postgres 实体）

沿用技术规范 §13–18 字段定义，补充约束：

| 实体 | 关键约束（本契约固化） |
| --- | --- |
| Device | id 唯一；name/manufacturer/model 必填 |
| Document | device_id FK；trust_level ∈ {A_OFFICIAL, B_INTERNAL, C_STANDARD, D_REFERENCE}（PRD §36） |
| DocumentVersion | (document_id, version) 唯一；file_hash 唯一索引（幂等去重）；同文档至多一个 is_current=True |
| Chunk | document_version_id FK（ADR-0004）；(document_version_id, chunk_index) 唯一；embedding 配套记录 embedding_model/version/dimension（§32） |
| Citation | message_id + chunk_id FK；page 必须等于 chunk.page_number（校验规则） |
| Message | 保存 request_id、evidence_status、prompt_version、模型与 token 计量（§69、§97） |
| Feedback | message_id FK；type/reasons 枚举见 §1.5 |
| IngestionJob | document_version_id FK；status/progress/error；失败可重试（新 job） |
| AuditEvent | MVP 记录：文档上传、状态变更、Admin 操作 |

处理状态机：`UPLOADED→PARSING→PARSED→INDEXING→VALIDATING→READY | FAILED`；发布状态：`DRAFT→ACTIVE→SUPERSEDED→ARCHIVED`（§19）。检索默认域：`ACTIVE ∧ is_current`（用户显式指定版本时放宽到该版本，ADR-0004）。

## 3. 枚举契约

```text
Intent:            ERROR_CODE | PARAMETER | PROCEDURE | TROUBLESHOOTING | GENERAL   （§37）
EvidenceStatus:    SUFFICIENT | PARTIAL | INSUFFICIENT | CONFLICTING                （§44，ADR-0005）
ErrorCode(API):    DOCUMENT_PARSE_FAILED | KNOWLEDGE_NOT_READY | MODEL_UNAVAILABLE
                   | RETRIEVAL_FAILED | AMBIGUOUS_VERSION | INSUFFICIENT_EVIDENCE
                   | FORBIDDEN_DOCUMENT | RATE_LIMITED | VALIDATION_ERROR | UNAUTHORIZED_ADMIN 〔新增后两个〕
                   | INTERNAL_ERROR 〔新增 v1.1（Phase 3）：未预期异常统一 500，不向客户端泄露内部细节〕
TrustLevel:        A_OFFICIAL | B_INTERNAL | C_STANDARD | D_REFERENCE               （PRD §36）
FeedbackType:      HELPFUL | INCORRECT | SAFETY_CONCERN                              （FR-009）
AbstainReason:     NO_RELIABLE_SOURCE | CONFLICTING_VERSIONS                          （§45 + A6）
```

## 4. Provider 协议（Python Protocol，技术规范 §22/§28/§40/§52 + ADR-0007）

```python
class DocumentParser(Protocol):
    async def parse(self, file_path: Path) -> ParsedDocument: ...

class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...

class RerankProvider(Protocol):          # 〔新增接口名，能力来自 §40〕
    async def rerank(self, query: str, candidates: list[ChunkRef], limit: int) -> list[ChunkRef]: ...

class LLMProvider(Protocol):
    async def generate(self, request: GenerationRequest) -> GenerationResponse: ...

class ObjectStorage(Protocol):           # ADR-0007
    async def put(self, key: str, data: bytes) -> None: ...
    async def get(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None: ...
    async def exists(self, key: str) -> bool: ...
```

实现清单：`QwenEmbeddingProvider`（百炼 text-embedding-v4）、`QwenRerankProvider`（qwen3-rerank）、`OpenAICompatibleLLMProvider`、`PyMuPDFParser` / `MinerUParser`、`LocalFSStorage`。测试替身：`FakeEmbedding`（哈希向量）、`FakeReranker`（恒等）、`FakeLLM`（固定 JSON）——集成测试使用，不算真实集成证据（执行方案 Phase 5 约定）。

## 5. 统一错误结构（技术规范 §104）

```json
{"error": {"code": "MODEL_UNAVAILABLE", "message": "…", "request_id": "…"}}
```

HTTP 映射：VALIDATION_ERROR→400；UNAUTHORIZED_ADMIN→401；FORBIDDEN_DOCUMENT→403；RATE_LIMITED→429；KNOWLEDGE_NOT_READY / MODEL_UNAVAILABLE / RETRIEVAL_FAILED / DOCUMENT_PARSE_FAILED→503 或按语义；AMBIGUOUS_VERSION / INSUFFICIENT_EVIDENCE→200 语义化响应（abstain/提示确认版本），非 HTTP 错误〔新增：这两类走 Answer.abstain 与提示文案，不报 4xx/5xx〕。

## 6. 契约变更规则

1. 本文件为唯一权威；Phase 3 起 schema 代码以本文件生成/对齐，双语不一致以测试失败暴露。
2. 变更须更新本文件版本号并在 `tasks/communicating.md` 留痕；破坏性变更需同步前端任务（T-018+）。
3. SSE 事件新增字段必须向后兼容（前端忽略未知字段）。
