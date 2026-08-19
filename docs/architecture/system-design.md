# H2 Manual Copilot · 系统设计与调用链（Phase 2）

> 版本：v1.0  
> 日期：2026-08-19（Asia/Shanghai）  
> 来源：技术规范 v1.0 + 实施基线 v1.0 + ADR-0001—0007  
> 证据层级标注：【规范】技术规范明文规定；【推断】由规范推导、尚未运行验证；【本地验证】已在 `scratch/phase2/` 实际运行；【待验证】需真实环境/凭据/数据

## 1. 运行入口

| 入口 | 命令（Phase 3 工程基线落实） | 说明 |
| --- | --- | --- |
| 基础设施 | `docker compose up -d postgres` | PostgreSQL 16 + pgvector（【推断】镜像与版本 Phase 3 锁定） |
| 后端 | `uv run uvicorn h2copilot.api.app:app --reload`（apps/api） | Python 3.12（本机 3.13，由 uv 锁定 3.12；【推断】） |
| 前端 | `pnpm dev`（apps/web） | Next.js 16.x 锁定 patch 版本（C-7，Phase 3 确定） |
| 评测 | `uv run python evals/run_eval.py` | golden dataset 指标报告（ADR-0006：不做页面） |
| 管理端鉴权 | Admin 路由经独立密码保护 | 比赛阶段问答匿名（技术规范 §62）【规范】 |

## 2. 模块职责（仓库结构 → 职责边界）

仓库结构沿用技术规范 §11；分层原则 API→Service→Domain→Repository/Provider（§12，禁止 router 直连 SQL/模型/prompt）。

| 模块 | 职责 | 关键约束 |
| --- | --- | --- |
| `apps/web`（Next.js） | Ask 会话、Knowledge 列表、Source Viewer、上传弹窗；SSE 消费；仅渲染 structured output | 不做业务判断；API Key 不进前端（§66）【规范】 |
| `apps/api` → `api/` | 路由层：`/api/v1` REST + SSE；参数校验（Pydantic）；鉴权中间件（Admin） | 不含业务逻辑 |
| `services/` | QueryService（问答编排）、DocumentService（文档管理）、IngestionService（接入编排）、FeedbackService | 管线编排唯一入口；抛领域错误码 |
| `domain/` | 实体与状态机（§13–19）；版本解析（ADR-0004）；abstention 判定 | 纯逻辑，无 IO，可单测 |
| `retrieval/` | intent 分类、错误代码路由、filter 构建、lexical/dense 双路、RRF、rerank 调用 | RRF 与路由为纯逻辑【本地验证】 |
| `ingestion/` | 解析编排（PyMuPDF4LLM→MinerU fallback）、结构化 chunk、embedding 写入 | 经 DocumentParser 协议（§22） |
| `llm/` | LLMProvider / EmbeddingProvider / RerankProvider 适配器（OpenAI-compatible，§52–54） | 应用层只见 model_alias |
| `safety/` | citation 校验、safety notice 注入、prompt 注入防护边界 | 文档内容永远视为 data（§48–49） |
| `repositories/` | Postgres 访问：文档/版本/chunk/citation/feedback/job | SQL 集中于此；tenant 字段生产阶段启用（§64） |
| `observability/` | OpenTelemetry trace（§72 结构）、AI 指标记录（§69）、日志脱敏（§73） | 只记 IDs/hashes/metrics |
| `packages/contracts` | 前后端共享类型（请求/响应/事件 schema 的 TS/Pydantic 双语定义） | Phase 3 建立，本文件 §契约先行 |

## 3. 主调用链

### 3.1 问答链路（Demo 黄金路径）

```text
Browser(Ask 页)
  → POST /api/v1/query（SSE）
    → QueryService.run()
      1 intent 分类            预算 <100ms   [纯逻辑；ERROR_CODE regex 路由]
      2 filter 构建             device/version→document_version_id（ADR-0004）
      3 双路检索（并行）         预算 <500ms   lexical(tsvector) ∥ dense(pgvector)
      4 RRF 融合 → Top30        [纯逻辑]
      5 rerank（provider）      预算 <1500ms  qwen3-rerank → Top6
      6 生成（provider）        预算 <5000ms  structured JSON（§43）
      7 citation 校验 + 安全校验               引用必须命中真实 chunk；safety notice
    ← SSE: retrieval.started → retrieval.completed → generation.started
           → generation.delta* → verification.completed → done
  ← 前端渲染回答卡 + Evidence（evidence_status 徽章，ADR-0005）
```

每步失败分支：intent/filter 失败→400；检索空结果→进入 abstention 判定（FR-006）；rerank/LLM 超时或 5xx→按 §106 仅重试 timeout/429/5xx，最终 MODEL_UNAVAILABLE；全程 P95 ≤8s（§74）【规范，性能待验证】。

### 3.2 知识接入链路（异步）

```text
Knowledge 页上传弹窗（Admin 密码）
  → POST /documents（元数据：device/type/version/language/trust）
  → POST /documents/{id}/ingest（file，PDF≤50MB，MIME+扩展名校验）
    → hash 计算；重复 hash 直接复用已有 DocumentVersion（幂等，§16）
    → 状态机 UPLOADED→PARSING→PARSED→INDEXING→VALIDATING→READY（§19）
      PARSE:  PyMuPDF4LLM；探测到扫描/复杂版式→MinerU（§20–21）
      CHUNK:  按 Chapter/Section/Paragraph 结构切分，350–700 token，overlap 50–100（§25–26）
      EMBED:  EmbeddingProvider（记录 embedding_model/version/dim，§32）
      STORE:  原始 PDF → ObjectStorage(LocalFS, ADR-0007)；chunk+向量 → Postgres
    → 失败任何一步 → FAILED（错误码 DOCUMENT_PARSE_FAILED），可重试
  ← GET /ingestion-jobs/{id} 轮询状态（前端显示 Parsing xx%）
```

后台执行用 FastAPI Background Task（MVP 不引入消息队列，§76）【规范】。

### 3.3 溯源链路（Source Viewer）

```text
回答卡/Evidence 点击 citation
  → GET /sources/{chunk_id}
  ← { document, version, page, excerpt, storage_key }
  → 前端 PDF 查看器加载原始文件，跳转 page 并高亮 excerpt
```

PDF 渲染用浏览器端 PDF.js（【推断】Phase 4 验证高亮定位精度）。

## 4. 数据流与数据归属

| 数据 | 归属 | 生命周期 |
| --- | --- | --- |
| 原始 PDF | ObjectStorage（MVP 本地卷 `data/storage/`，ADR-0007） | 永久；生产换 S3 versioning |
| 文档/版本/状态元数据 | Postgres `documents`/`document_versions` | 软删除→ARCHIVED（§58） |
| chunks + embedding + fts | Postgres `chunks`（pgvector + tsvector 列） | 索引可从原始文件重建（§102） |
| 会话与消息 | Postgres `conversations`/`messages` | MVP 保留；生产按租户策略 |
| citations | Postgres `citations`（实体，非前端拼接，§18） | 随消息 |
| feedback | Postgres `feedback` | 供评测与人工审核 |
| 审计事件 | Postgres `audit_events`（MVP 记录上传/状态变更） | 生产扩展（§121） |
| knowledge_revision | Postgres 单行计数器（§103） | 文档 add/update/archive 时 +1，用于缓存失效与复现 |
| 日志/trace | stdout/OTel（MVP 不部署 Langfuse 服务，SDK 留接口） | 脱敏规则 §73 |

## 5. 横切边界

- **鉴权**：问答匿名；Admin（上传/文档管理）独立密码（环境变量 `ADMIN_PASSWORD`，Basic 或头校验）【规范 §62】。生产 RBAC/多租户在 §63–64，MVP 表结构预留 tenant_id 但不启用。
- **限流**：query RPM、upload/day、文件 ≤50MB、模型 token 上限（§108）；MVP 用进程内简单限流，Redis 限流 P1。
- **超时与重试**：分阶段预算见 §3.1；仅 retry timeout/429/瞬态 5xx，指数退避 ≤2 次重试；invalid input/unauthorized/safety rejection 不重试（§106）【规范】。
- **幂等**：上传以 file_hash 去重（§16）；ingest 重复请求返回已有 job；query 只读天然幂等。
- **降级**：证据不足→abstention（不降级为"尽力回答"）；模型不可用→MODEL_UNAVAILABLE 错误（MVP 不做自动 fallback 模型，§107）；检索一路失败（如 dense 超时）→允许仅 lexical 结果并标记 PARTIAL（【推断】此为 MVP 新增降级点，进 contracts 错误码）。
- **日志红线**：不记录完整手册内容、完整 prompt context、API Key、token（§73）；AI 指标按 §69 字段记录；trace 按 §72 结构。
- **成本边界**：每请求记录 embedding/prompt/completion tokens 与 rerank 成本（§109）；rerank 候选上限 30；上传配额防滥用。
- **隐私**：企业文件不入公开日志；不同上传者文档经 trust_level 与 DRAFT 状态隔离，DRAFT 不进生产检索（§50）；密钥仅服务端（§66）。

## 6. 配置地图（.env，见技术规范 §95）

```text
DATABASE_URL=            # Postgres + pgvector
OBJECT_STORAGE_URL=      # MVP 留空=LocalFS（ADR-0007）
OBJECT_STORAGE_BUCKET=
LLM_PROVIDER= LLM_MODEL=
EMBEDDING_PROVIDER= EMBEDDING_MODEL=
RERANK_PROVIDER= RERANK_MODEL=
ADMIN_PASSWORD=
LANGFUSE_PUBLIC_KEY= LANGFUSE_SECRET_KEY=   # 可空：MVP 不启用
# 检索参数集中 Settings（§96）：dense_top_k=20 lexical_top_k=20 rerank_top_k=6 rerank_candidates=30
```

禁止任何 `NEXT_PUBLIC_*` 密钥；真实密钥绝不提交（§66、AGENTS.md 版本控制规则）。

## 7. 测试地图（技术规范 §84–87 → 任务映射）

| 层 | 范围 | 工具 | 关联任务 |
| --- | --- | --- | --- |
| 单元 | intent/regex 路由、RRF、filter、版本解析、abstention、chunk 切分 | pytest | T-013、T-015、T-016 |
| 集成 | 真实 Postgres+pgvector 检索 SQL；上传→READY 状态机；模型用 fake provider | pytest + docker | T-014、T-015 |
| 契约 | packages/contracts 双语 schema 一致性 | vitest/pytest 参数化 | T-017 |
| E2E | upload→ask→citation→source viewer 全链路（Demo 黄金路径） | Playwright | T-008、T-020 |
| 评测 | ≥30 golden：Recall@5/Faithfulness/No-answer/Citation | RAGAS/Promptfoo 脚本 | T-023 |
| 安全 | injection/citation attack/dangerous/unsupported 用例 | pytest + evals | T-024 |

## 8. MVP → 生产演进差异

| 维度 | MVP | 生产（技术规范出处） |
| --- | --- | --- |
| 对象存储 | LocalFS 卷（ADR-0007） | S3/MinIO + versioning（§5、§102） |
| 缓存 | 无 | Redis（P1，§77） |
| 异步 | FastAPI Background Task | Redis + RQ/Dramatiq/Celery（§76） |
| 模型网关 | 单 provider adapter | LiteLLM Proxy 路由/fallback（§55、§107） |
| 鉴权 | 匿名 + Admin 密码 | Org/Workspace/User RBAC + 多租户（§63–64） |
| 可观测 | OTel + 结构化日志 | + Langfuse 面板（§71） |
| 复杂解析 | PyMuPDF4LLM + MinerU | + 云 OCR/Docling（§22 替换路径） |

## 9. Phase 2 风险验证结论（证据层级）

| # | 假设（Phase 1 遗留） | 验证方式 | 结论与证据层级 |
| --- | --- | --- | --- |
| V-1 | RRF 融合、错误代码 regex 路由逻辑正确 | `scratch/phase2/verify_logic.py` 本地运行 | 【本地验证】通过：RRF 公式实现与多路排名融合行为符合预期；`^[A-Z]{1,4}[-_]?\d{2,6}$` 命中 E104/HX-100 类代码、拒绝普通语句 |
| V-2 | PyMuPDF4LLM 可安装并产出结构化 Markdown | `scratch/phase2/verify_parser.py`（合成 PDF 往返） | 【本地验证】机制级通过：pip 安装、PDF→Markdown、标题/段落结构保留；真实手册质量【待验证：需演示 PDF】 |
| V-3 | pgvector hybrid SQL 正确性与性能 | 未运行（需起容器） | 【推断】SQL 模式来自 pgvector 官方文档口径（§9、§36）；Phase 3 集成测试落为【本地验证】，性能证据 Phase 5 |
| V-4 | text-embedding-v4 + qwen3-rerank 检索质量 | 未运行（需 API 凭据） | 【待验证】阻塞于百炼 API Key（Q-010）与演示 PDF（Q-011） |
| V-5 | Next.js 16.x 当前可用 patch 版本 | npm registry 查询 | 【本地验证】见 `scratch/phase2/RESULTS.md`；锁定动作在 Phase 3 |
| V-6 | SSE 流式可用性 | 未单独验证 | 【推断】FastAPI/Next.js 标准能力，风险低；Phase 3 工程基线以冒烟测试落证据 |
