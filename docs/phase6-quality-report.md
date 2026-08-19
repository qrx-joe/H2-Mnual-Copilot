# Phase 6 质量与异常能力验证报告

> 日期：2026-08-20（Asia/Shanghai）  
> 证据分层沿用 Phase 5 约定：数据层/接口层/浏览器为【真实】；模型层为【Fake】（Q-010 未到）  
> 提交：26ff81b / a3d7d02 / 87f4319 / 5fe2794（错误代码路由收窄）

## 1. 交付与验证结论

| 项 | 实现 | 验证证据 |
| --- | --- | --- |
| T-009 状态与异常 | 限流（进程内 RPM→429 契约结构）；全链路超时（wait_for→SSE error 事件）；拒答/设备隔离/空库路径 | `test_query_rate_limited`、`test_query_timeout_degrades_to_error_event`、Phase 5 集成测试 |
| T-020 Source Viewer | `GET /sources/{chunk_id}` + `GET /files/{version_id}`（LocalFS 流）；前端抽屉 iframe 内嵌原始 PDF + `#page=N` 跳页 + 摘录卡 | `test_source_and_file_endpoints`（%PDF 字节校验）；浏览器实测：引用点击→"Original PDF"徽章+摘录 |
| T-022 反馈 | 会话/消息/Citation 实体落库；`POST /messages/{id}/feedback`（幂等覆盖）；done 事件回传 message_id（契约 v1.2） | `test_feedback_persists_and_overwrites`；浏览器实测 Helpful→toast→dev 库 feedback 表出现记录 |
| T-023 评测 | `evals/datasets/golden.jsonl`（30 条：exact 8 / easy 5 / semantic_zh 5 / version 2 / no_answer 6 / cross_language 4）+ `run_eval.py` + `report.json` | **recall@citation=1.0，no-answer accuracy=1.0**（22 可跑条目；8 条跨语言阻塞待真实 embedding） |
| T-024 安全测试集 | 注入保持 data、引用不编造、危险请求 fail-closed、无据参数不编数值、Admin 鉴权 401 | `test_phase6.py` 5 个安全用例全过 |
| 可观测 | 查询结构化日志（§69 字段：intent/retrieval_ms/chunks/evidence_status/model_alias）；HTTPException→契约错误结构 | `test_query_log_has_ai_metrics`（含"日志不含查询正文"红线断言） |
| 回归 | API：ruff/mypy/pytest **26 全绿**；web：lint/vitest(5)/build 全绿 | CI 命令见 README |

## 2. 评测驱动发现并修复的缺陷（本阶段核心价值）

| # | 缺陷 | 现象（eval 证据） | 修复 |
| --- | --- | --- | --- |
| 1 | dense 检索无阈值 | no-answer 准确率 28.6%：无关查询返回"最近邻"垃圾证据 | 距离阈值（初 0.95） |
| 2 | FakeEmbedding 停用词污染 | "the/is" 单词重叠把无关查询拉进阈值 | 英/中停用词过滤 |
| 3 | 哈希桶碰撞 | "purchase/price" 与 "pressure" 撞桶，cos 虚高 0.26 | 每 token 3 哈希位（碰撞贡献 ≈0.05）+ 阈值重标定 0.78 |
| 4 | 错误代码路由过宽 | "HX-100 purchase price" 被退化成裸型号检索命中一切 | 仅"纯代码/代码+非拉丁文本"走代码路由（§38 收窄） |
| 5 | Alembic 禁用应用 logger | 测试中应用日志全部消失（logger.disabled=True） | env.py `disable_existing_loggers=False` |

每项修复都有 golden 条目或测试锁定，防回归。

## 3. 已知边界与待真实环境项

1. **跨语言语义检索**（8 条 golden 阻塞）：FakeEmbedding 无跨语言能力；错误代码类混合问句（"E104 是什么？"）已通过 §38 精确路由覆盖。
2. **真实模型指标**（Faithfulness/真实 Recall）：Q-010 后用同一 golden 集重跑 `evals/run_eval.py`，并重标定 `retrieval_dense_max_distance`。
3. Source Viewer 页内文本高亮需 PDF.js 文本层（当前：跳页 + 摘录卡）。
4. 限流为进程内实现，多实例部署需换 Redis（§77）。
5. 性能：单文档量级检索 15-18ms；真实手册规模压测在 Phase 7 前。
