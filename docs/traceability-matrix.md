# H2 Manual Copilot · 需求追踪矩阵

> 版本：v1.0（Phase 1 产出）  
> 日期：2026-08-19（Asia/Shanghai）  
> 列定义：**需求**（PRD 编号）→ **技术模块**（技术规范实现层）→ **视觉状态**（前端原型/PRD 页面）→ **任务**（`tasks/todo.md` 任务 ID）→ **验收证据**（可检查方式）  
> 来源基线：PRD v1.0、技术规范 v1.0、前端原型（a3739cd9）；裁决见 `tasks/question.md` 已解决表  
> 状态约定：任务状态以 `tasks/todo.md` 为准，本矩阵不重复维护状态，只维护映射关系。

## P0 需求（MVP 必须）

| 需求 | 技术模块 | 视觉状态 | 任务 | 验收证据 |
| --- | --- | --- | --- | --- |
| FR-001 知识文档管理：PDF 上传、列表、状态、设备绑定、版本/语言/类型（PRD §23） | Documents API；Ingestion Worker（parse/normalize/chunk/embed/validate）；Document/DocumentVersion/Chunk 实体与状态机（技术规范 §58–59、§13–17、§19） | Knowledge 表格（类型/版本/语言/状态/可信徽章）、上传弹窗、解析进度提示 | T-014、T-021 | 演示 PDF 上传后状态 UPLOADED→READY 可见；file_hash 去重；集成测试 |
| FR-002 自然语言问答：答案+来源+页码（PRD §24） | Query Service；hybrid 检索管线；结构化生成（技术规范 §41、§57） | Ask 会话流、管线进度（routing→retrieval→rerank→verification）、回答卡 | T-015、T-016、T-017、T-018 | E2E 问答链路通过；golden 问题集回答正确 |
| FR-003 Source Citation：每回答至少 Document/Version/Page/Excerpt（PRD §25） | Citation 数据库实体 + citation verification（技术规范 §18、§42） | 引用徽章（doc · p.N）；Evidence 来源卡（标题/版本页码/摘录） | T-016、T-019 | Citation Coverage ≥95%（Metric 1）；引用均来自真实检索结果 |
| FR-004 错误代码检索：exact/lexical 优先（PRD §26） | Error code regex 路由（`^[A-Z]{1,4}[-_]?\d{2,6}$`）→ exact lexical → metadata → dense fallback（技术规范 §38） | 快捷入口 Error code；E104 回答卡（报警名/解释/检查项/来源页） | T-015 | golden 集 Exact 类问题命中正确文档与页码 |
| FR-005 设备过滤：Device/Model/Version（PRD §27） | metadata filter（device_id/manufacturer/model/version/status/language/trust，技术规范 §39） | 设备/版本选择器下拉（HX-100 v2.1 等） | T-015、T-018 | 跨设备问题不串答案；版本过滤单元测试；默认仅 ACTIVE/current |
| FR-006 资料不足处理：拒答+最相关资料+推荐关键词（PRD §28） | abstention 判定与 abstain_reason（技术规范 §45） | 红色 stop 状态回答卡"当前知识库无法可靠回答" | T-016、T-018 | No-answer Accuracy 达标（Metric 2）；Demo Scene 5 可演示 |
| FR-007 Evidence Viewer：点击 citation 跳转 PDF 对应页（PRD §29） | Source API `GET /sources/{chunk_id}` 返回 document/version/page/excerpt（技术规范 §60） | Source Viewer 抽屉：PDF 页 + 高亮引用区 + 页码 + 版本信息 | T-020 | E2E：ask→citation→打开对应页并高亮（Demo Scene 4） |
| FR-008 安全提示：压力/氢气/电气/联锁/紧急停机/维修场景（PRD §30） | structured output 的 safety_notice 字段（技术规范 §43） | 回答卡橙色 Safety Note 提示条 | T-016、T-018 | 涉及上述主题的回答 100% 携带安全提示；golden 集抽检 |
| FR-009 反馈：👍/👎/🚩 + 原因多选（PRD §31） | Feedback 实体 + 写入 API（技术规范 §13） | 回答卡操作区反馈按钮与原因选择（按 PRD 补齐，见基线 §8.2） | T-022 | 反馈落库可查询；三种类型均可提交 |
| FR-101 中英跨语言（提为 P0，Q-008）：中文问→英文检索→中文答→英文证据（PRD §32） | 多语言 embedding（text-embedding-v4 / Qwen3 系列，技术规范 §28–31）；检索与生成不假设同语言 | 中文回答卡 + 英文摘录证据卡并存 | T-015、T-016 | 跨语言 golden 问题通过（Demo Scene 6）；证据为英文原文 |

## 横切需求（约束级）

| 需求 | 技术模块 | 视觉状态 | 任务 | 验收证据 |
| --- | --- | --- | --- | --- |
| A1/A2/A3 Grounded 回答、不补关键参数、不造 citation（PRD §38–40） | prompt 规范（技术规范 §46–47）+ citation verifier；prompt 版本化（§97） | 回答区分 AI Summary 与 Source（PRD A4） | T-016、T-024 | RAGAS Faithfulness（Metric 4）；citation attack 用例拒答 |
| A5 单位保留、A6 版本冲突提醒（PRD §42–43） | 参数不换算约束进 prompt；版本冲突检测返回 AMBIGUOUS_VERSION（技术规范 §105） | 版本冲突提示卡（要求确认设备版本） | T-016 | Version 类 golden 问题（V1 vs V2）正确提示冲突 |
| Prompt injection 防护：文档=data、trust boundary、DRAFT 不入生产检索（技术规范 §48–50） | trust boundary 层级；ingestion 记录 source/uploader/checksum/trust_level | 无直接 UI；上传文档默认 DRAFT 状态可见 | T-024、T-014 | injection 用例（"Ignore previous instructions"）不改变系统行为 |
| 只读设备边界：无任何设备写工具（技术规范 §51） | 架构层不提供 equipment write tool | 设置页只读边界说明（不进 MVP，仅原型参考） | 架构约束，无独立任务 | 代码审查确认无控制接口；ADR 记录 |
| 流式与状态：SSE 事件序列、Loading/Error/Empty（PRD DoD；技术规范 §61） | SSE：retrieval.started→…→done；统一错误结构（§104–105） | 管线进度条、加载/空/错误状态（原型已有模式） | T-017、T-009 | E2E 断言事件序列；空库与异常场景展示正确 |
| 可观测与日志红线：AI 指标记录、不记录完整 prompt/机密（技术规范 §69–73） | OpenTelemetry trace 结构；日志脱敏 | 无直接 UI | T-007、T-016 | trace 含各阶段耗时；日志审查无完整上下文泄漏 |
| 评测与回归：≥30 golden、Recall@5/Faithfulness/No-answer、安全测试集（PRD §49–53；技术规范 §78–83） | evals/ 目录 + pytest/RAGAS/Promptfoo（技术规范 §78–88） | Evaluation 页不进 MVP（Q-007），报告走命令行/CI | T-023、T-024 | 指标可重复计算并输出报告；检索/提示词变更触发回归 |
| MVP DoD 12 条（PRD §58） | 汇总项 | 汇总项 | T-010 | DoD 清单逐条勾选留证 |

## P1 暂缓项（比赛加分，MVP 后视余量）

| 需求 | 说明 | 视觉参考 | 任务 |
| --- | --- | --- | --- |
| FR-102 Error Code 快捷模式 | 首页独立错误代码输入入口 | 原型快捷卡 Error code | T-025 |
| FR-103 推荐问题 | 按当前设备推荐 startup/maintenance/safety 等 | 原型快捷问题区（MVP 可先静态） | T-025 |
| FR-104 版本管理界面化 | DRAFT/ACTIVE/SUPERSEDED/ARCHIVED 管理操作 | Knowledge 表格状态徽章（MVP 仅展示） | T-025 |
| FR-105 来源可信等级展示 | Level A–D 优先级影响检索排序 | Knowledge Trust 徽章（MVP 仅展示字段） | T-025 |

## 孤立项检查结论

- 10 条 P0 需求（FR-001–009 + FR-101）均映射到技术模块、视觉状态、任务和验收方式，无孤立项。
- 横切约束中"只读设备边界"无独立任务，属架构级约束，将在 Phase 2 架构决策记录（ADR）中固化并代码审查验收，不产生孤儿实现。
- P1 项归并为 T-025，不阻塞 MVP。
- 任务池（`tasks/todo.md` T-007、T-013–T-025）中每个实现任务都能在本矩阵找到需求来源，无来源不明任务。

## Phase 6 证据回填（2026-08-20）

> 详细证据见 `docs/phase6-quality-report.md`；模型层为 Fake 替身（Q-010 未到），标注【待真实】的项等待真实模型复测。

| 需求 | 验收证据（现状） |
| --- | --- |
| FR-001 文档管理 | 集成测试 + 浏览器真实上传（合成手册→READY<4s）；hash 去重有路由实现；MinerU fallback【待 Q-011】 |
| FR-002 自然语言问答 | 浏览器全链路（快捷卡/输入框→SSE→回答卡）；26 测试含成功路径 |
| FR-003 Citation | Citation 数据库实体落库（消息级）；引用来自真实 chunk（A3 由安全测试锁定） |
| FR-004 错误代码 | §38 路由（含混合中文问句收窄规则）；golden exact 8/8 |
| FR-005 设备过滤 | 集成测试（hx80 隔离）+ golden 设备隔离条目通过 |
| FR-006 拒答 | golden no-answer 6/6；超时降级路径测试 |
| FR-007 Evidence Viewer | /sources + /files 路由 + 浏览器实测（Original PDF 徽章、跳页）；页内高亮【后续版本：PDF.js 文本层】 |
| FR-008 安全提示 | 安全提示随 interlock/hydrogen 关键词触发（单元+golden 覆盖） |
| FR-009 反馈 | 落库 API（幂等覆盖）+ 浏览器实测 Helpful→dev 库记录 |
| FR-101 跨语言 | 错误代码混合问句已通（§38 路由）；语义跨语言 8 条 golden【待 Q-010】 |
| A1–A6 / 安全 | 安全测试集 5 用例（注入/编造引用/危险请求/编参数/鉴权）全过 |
| 横切（限流/超时/日志） | 429 契约结构、SSE error 降级、§69 结构化日志（含红线断言） |
| 评测（T-023） | golden 30 条；recall@citation 1.0 / no-answer 1.0（Fake 层）；真实指标【待 Q-010】 |
