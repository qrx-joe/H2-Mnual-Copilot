# H2 Manual Copilot · 一页实施基线

> 版本：v1.0（Phase 1 产出）  
> 日期：2026-08-19（Asia/Shanghai）  
> 来源：PRD v1.0、技术规范 v1.0、前端原型（SHA-256 a3739cd9），均已登记于 `tasks/advice.md` 源资料登记表  
> 裁决依据：Q-004（用户本人裁决，PRD＞技术规范＞原型）、Q-006/Q-007/Q-008/Q-009（Phase 0 检查点，2026-08-19）

## 1. 产品一句话

面向氢能设备技术资料的 Evidence-grounded Industrial Knowledge Copilot：通过设备与版本感知检索，把手册、维护资料、故障代码和安全文档变成可自然语言查询、可回溯原始证据、证据不足时主动拒答的智能知识服务。（PRD §67）

**阶段定位**：Hackathon MVP——3 分钟 Demo 黄金路径（PRD §59）是第一验收场景。

## 2. 目标用户（MVP 主打）

| 优先级 | 用户 | 典型问题 | 来源 |
| --- | --- | --- | --- |
| 主打 | Persona A 现场运维人员 | E104 是什么？启动前检查什么？ | PRD §9 |
| 次要 | Persona E 知识管理员 | 上传资料、查看解析状态 | PRD §9（Q-007 裁决：Admin 简化为上传 + 状态查看） |
| 覆盖但非主打 | Persona B 售后支持 / C 新员工 / D 海外客户 | 统一口径、学习定位、中英互查 | PRD §9 |

## 3. 核心场景（MVP 范围内）

| 场景 | 内容 | Demo 黄金路径 | 来源 |
| --- | --- | --- | --- |
| S2 报警代码查询 | 输入 E104 → 报警名称/解释/检查项/来源页码 | Scene 2–4（核心幕） | PRD §12、§59 |
| S1 操作流程查询 | 启动前检查清单，逐条带来源 | — | PRD §11 |
| S4+S5 安全拒答 | 关键参数证据不足 → 拒答并要求确认版本 | Scene 5（证明安全边界） | PRD §14、§59 |
| S5 跨语言查询 | 中文提问 → 英文检索 → 中文回答 + 英文证据 | Scene 6 | PRD §15、§59（Q-008：提为 P0） |
| S6 找原始文档 | 点击引用 → 打开 PDF 对应页 | Scene 4 | PRD §16 |

## 4. MVP 垂直闭环（T-006）

**主链路（问答）**：

- **输入**：设备上下文（device_id / version，默认 HX-100 v2.1）+ 问题文本（中文或英文，含错误代码如 `E104`）。
- **处理**：intent 分类（ERROR_CODE 走 exact lexical 优先路由）→ 设备/版本 metadata 过滤 → hybrid 检索（tsvector + pgvector，RRF 融合）→ rerank（Top30→6）→ 基于证据的结构化生成（JSON：answer/steps/citations/evidence_status/safety_notice/abstain）→ citation 与安全校验。（技术规范 §37–47、§57）
- **输出**：回答卡（答案 + 检查步骤 + 安全提示 + 引用徽章）、Evidence 面板（evidence status 徽章 + 来源列表：文档/版本/页码/摘录）；点击引用打开 Source Viewer 对应 PDF 页并高亮。（PRD §18–20；Q-006：状态徽章替代数值评分环）

**前置链路（知识接入）**：知识管理员上传 PDF → hash 去重 → 解析（PyMuPDF4LLM，复杂版式 fallback MinerU）→ 结构化 chunk → embedding → 状态机 UPLOADED→READY；页面提供上传入口与状态查看。（PRD §23；技术规范 §19–27、§75）

**关键失败路径（MVP 必须演示）**：

1. 证据不足 → 拒答 + 展示最相关资料与推荐关键词（FR-006，Demo Scene 5）。
2. 版本冲突 → 不任选其一，提示确认设备版本（PRD A6）。
3. 服务异常 → 统一错误结构与错误码（技术规范 §104–105）。
4. 解析失败 → 文档进入 FAILED 状态可重试（FR-001）。

## 5. 成功指标（可真实测量）

| 指标 | 目标 | 来源 |
| --- | --- | --- |
| Citation Coverage | ≥95% 关键事实有来源支持 | PRD §50 |
| No-answer Accuracy | 应拒答时能拒答 | PRD §51 |
| Retrieval Recall@5 | 正确 evidence 进入前 5 候选 | PRD §52 |
| Faithfulness | RAGAS 口径，事实由上下文支持 | PRD §53 |
| Answer Latency | P50 ≤4s，P95 ≤8s（不含解析） | PRD §54、技术规范 §74 |
| 评测数据 | ≥30 条 golden 问题（含跨语言与无答案类） | PRD §49、§58 |

## 6. 非目标（明确不做）

- 不做设备控制（无启停/PLC/阀门/联锁写操作，无 equipment write tool）。（PRD §6、§8；技术规范 §51）
- 不做自主诊断（Decision Support only）。（PRD §6）
- 不回答知识库外的一般氢能问题。（PRD §6）
- 不做 ERP/CRM/工单/派工/采购集成。（PRD §6）
- MVP 砍掉：Kubernetes、多 Agent、Knowledge Graph、Fine-tuning、自动 PLC、企业 SSO、Elasticsearch、Kafka、微服务、复杂工作流引擎。（PRD §57）
- 不进 MVP 的页面：Evaluation、Settings（评测走 CI/命令行）。（Q-007 裁决）
- 暂缓：Redis 缓存、LiteLLM Proxy、多租户 RBAC（生产门项）。（技术规范 §55、§63、§77、§121）

## 7. 边界

- **技术**：模块化单体（Next.js 16.x 前端 + FastAPI 后端 + PostgreSQL/pgvector），explicit pipeline 不用 Agent 框架；所有外部能力经 Provider 协议接入。（技术规范 ADR-001–003、§5）
- **安全**：文档内容视为 data 不是 instruction；fail closed；不展示未校准置信度数值；上传仅 PDF ≤50MB 带 hash；密钥仅服务端。（技术规范 §48–51、§65–66；Q-006）
- **数据**：演示集 5–15 份文档，以 HX-100 套件（Operation/Maintenance/Safety/Error Codes）+ 30 条测试问题为准。（PRD §47–49）
- **裁决**：用户本人，优先级 PRD＞技术规范＞原型。（Q-004）

## 8. 视觉基线收敛（Phase 1 决定，依据 Q-004 规则）

1. **布局（C-3）**：PRD §19 措辞为"建议采用三栏结构"，属建议而非硬性产品意图；采纳原型布局（全局侧边栏导航 + 会话区含答案 + 右侧 Evidence 常驻），它满足 PRD 的产品意图（设备上下文可见、答案为主、证据常驻右侧）。
2. **反馈（C-4）**：FR-009 为 P0 需求且 PRD 为准，实现完整反馈（👍/👎/🚩 + 原因多选）；原型中的简化按钮（Copy/Helpful/Safety concern）作为视觉起点扩展。
3. **评分环（C-1，已裁决）**：Evidence 面板用 SUFFICIENT / PARTIAL / INSUFFICIENT / CONFLICTING 四态徽章，不用数值评分环。

## 9. 结论来源与未验证假设

以上每节均已标注来源。**仍未验证的假设**（进入 Phase 2 最小验证清单，证据层级目前均为"文档推断"）：

1. text-embedding-v4 + qwen3-rerank 对中英混合设备文档的检索质量。
2. PyMuPDF4LLM 对演示 PDF 的解析质量；何时触发 MinerU fallback。
3. pgvector hybrid + RRF + rerank 全链路是否满足 P95 ≤8s。
4. 中文问题对英文资料的跨语言召回效果（Q-008 提为 P0 后风险上移）。
5. SSE 流式在目标部署环境的稳定性。
6. Next.js 16.x 需锁定的具体 patch 版本（C-7，Phase 3 确定）。
