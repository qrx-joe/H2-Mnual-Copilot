# To Do

完整任务池。任务必须有明确来源，不根据缺失资料臆造。

| ID | 状态 | 优先级 | 任务 | 完成标准 | 依赖/来源 |
| --- | --- | --- | --- | --- | --- |
| T-005 | 进行中 | P1 | 每轮交互更新协作记录 | 每轮结束前新增日期、用户意图、AI 行动、决定和待确认项 | 用户本轮要求 |
| T-008 | 待办 | P0 | 实现第一条端到端垂直切片 | 主流程跨越前端、接口、数据层并能用确定的测试输入完成一次可演示闭环 | T-006、T-007 |
| T-009 | 待办 | P1 | 补齐界面状态与异常路径 | 主流程覆盖正常、加载、空、错误、超时和不可用状态，并与视觉基线一致 | T-008、视觉方案 |
| T-010 | 待办 | P1 | 完成验收、发布准备和回滚设计 | 核心需求逐条有验证证据；已知风险、监控指标、发布步骤和回滚条件明确 | T-003、T-008、T-009 |
| T-012 | 待办 | P1 | 按阶段门禁使用 ZCode 推进项目 | 每次只执行一个 Phase，通过验收门后再进入下一阶段，并同步五份协作文档 | `tasks/zcode-execution-plan.md` |
| T-013 | 待办 | P0 | 数据模型与迁移：Device/Document/DocumentVersion/Chunk/Citation/Feedback/IngestionJob + Alembic + pgvector/tsvector 索引 | 迁移可执行可回滚；字段覆盖技术规范 §13–18 | T-007；FR-001/003/009 |
| T-014 | 待办 | P0 | 文档接入管线：上传 API（PDF/hash/50MB/设备绑定）+ 解析（PyMuPDF4LLM→MinerU）+ 结构化 chunk + embedding + 状态机 | 演示 PDF 上传后 UPLOADED→READY；file_hash 去重；失败进 FAILED | T-013；FR-001 |
| T-015 | 待办 | P0 | Hybrid 检索管线：intent 分类（含错误代码 regex 路由）+ metadata 过滤 + 双路召回 + RRF + rerank | E104 精确命中；语义问题召回正确；设备/版本过滤生效 | T-014；FR-002/004/005、FR-101 |
| T-016 | 待办 | P0 | 生成与验证：LLM provider adapter + 结构化 JSON + citation 校验 + abstention + safety notice + 版本冲突提示 | 无证据拒答；引用均来自真实检索；A1–A6 生效 | T-015；FR-003/006/008、FR-101 |
| T-017 | 待办 | P0 | Query API 与 SSE 流式：`POST /api/v1/query` + 事件序列 + 统一错误结构 | 前端可消费进度事件；错误码符合技术规范 §105 | T-016；FR-002、DoD |
| T-018 | 进行中 | P0 | Ask 页面：设备/版本选择、输入框、快捷入口、管线进度、回答卡、加载/空/错误状态 | 对照原型可逐项核对；键盘可用 | T-017、视觉基线；FR-002/005/008 |
| T-019 | 进行中 | P0 | Evidence 面板：evidence status 徽章 + 来源卡列表 | 四态徽章（SUFFICIENT/PARTIAL/INSUFFICIENT/CONFLICTING）；来源卡含文档/版本/页码/摘录 | T-018；FR-003、Q-006 |
| T-020 | 进行中 | P0 | Source Viewer：citation 点击打开 PDF 对应页并高亮 | E2E：ask→citation→页面定位（Demo Scene 4） | T-018；FR-007 |
| T-021 | 进行中 | P0 | Knowledge 页与简化 Admin：文档表格 + 上传入口 + 解析状态 | 列表与状态真实反映数据库；上传走真实管线 | T-014、T-018；FR-001、Q-007 |
| T-022 | 进行中 | P0 | 反馈：👍/👎/🚩 + 原因多选，落库 | 反馈可查询；视觉按 PRD §31（原型部分呈现按 PRD 补齐） | T-018；FR-009、基线 §8.2 |
| T-023 | 待办 | P0 | Golden dataset 与评测：≥30 条（Easy/Exact/Semantic/Cross-language/Version/No-answer）+ 指标脚本 | Recall@5/Faithfulness/No-answer 可重复计算并输出报告 | T-015、T-016；PRD §49–53 |
| T-024 | 待办 | P0 | 安全测试集：injection/citation attack/dangerous/unsupported 用例 | 全部用例按预期拒答或隔离 | T-016；技术规范 §82、A3 |
| T-025 | 待办 | P1 | P1 增强：Error Code 快捷入口、推荐问题、版本管理界面化、可信等级展示 | 演示加分项，MVP 后视余量逐项实现 | T-018+；FR-102–105 |

## 已完成

| ID | 完成日期 | 结果 |
| --- | --- | --- |
| T-000 | 2026-08-19 | 建立五份任务协作文档及目录说明 |
| T-011 | 2026-08-19 | 生成 ZCode 分阶段执行方案 v1，包含 Phase 0 至 Phase 8、验收门和执行提示词 |
| T-001 | 2026-08-19 | Phase 0 完成：PRD v1.0、技术规范 v1.0、前端原型登记入库 `docs/sources/`（哈希与版本见 `tasks/advice.md` 源资料登记表），Q-001 关闭 |
| T-004 | 2026-08-19 | 冲突与缺口识别完成：C-1—C-7 登记于 `tasks/advice.md`；C-1、C-2、C-5 经用户裁决关闭，C-3、C-4 按 PRD＞原型规则留待 Phase 1 收敛，C-7 留待 Phase 3 |
| T-002 | 2026-08-19 | 追踪矩阵完成：`docs/traceability-matrix.md`，P0/横切/P1 三层映射，无孤立项 |
| T-006 | 2026-08-19 | MVP 垂直闭环与非目标确定：`docs/implementation-baseline.md` §4（输入/处理/输出/四条失败路径）与 §6 |
| T-003 | 2026-08-19 | 首版研发任务拆分完成：T-013—T-025 入池，每项含范围、依赖、完成标准，均可回溯到矩阵需求行 |
| T-007 | 2026-08-19 | Phase 3 完成：apps/api（ruff/mypy/pytest 8 通过/uvicorn 冒烟）+ apps/web（16.3.1 锁定，lint/vitest/build 全绿）+ postgres+pgvector compose（V-3 冒烟通过）；实际命令与输出见 `docs/engineering-baseline.md`；C-7 随 Next.js 精确锁定关闭 |

> 原资料缺失期形成的流程骨架任务（T-007—T-010）保留为阶段级汇总任务；具体实现任务为 T-013—T-025，映射关系见 `docs/traceability-matrix.md`。
