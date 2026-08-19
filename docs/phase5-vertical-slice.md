# Phase 5 垂直切片验证报告（证据分层）

> 日期：2026-08-19（Asia/Shanghai）  
> 证据分层（执行方案约定）：**【真实】**= 真实 Postgres/HTTP/浏览器；**【Fake】**= 确定性测试替身，不构成真实模型集成证据  
> 未验证项：真实模型调用（等 Q-010 API Key）、真实手册解析质量（等 Q-011 演示 PDF）

## 1. 已贯通的链路（全部【真实】）

| 环节 | 命令/入口 | 结果 |
| --- | --- | --- |
| 数据模型迁移 | `alembic upgrade head`（Alembic + SQLAlchemy + pgvector/tsvector） | 10 表建成（真实 Postgres，含 file_hash 唯一、is_current 部分唯一索引） |
| 文档接入 | `POST /documents` → `POST /documents/{id}/ingest`（合成 HX-100 手册 3 页，`scripts/make_sample_manual.py` 生成） | 状态机 UPLOADED→PARSING→…→READY（<4s）；DRAFT→ACTIVE；页码/section 结构入库 |
| 问答成功路径 | `POST /api/v1/query {"query":"E104","device_id":"hx100"}` | intent=ERROR_CODE；检索 15ms；答案抽取自第 1 页 chunk 原文；引用含 title/version=2.1/page=1/excerpt；safety_notice 命中 interlock 关键词 |
| 拒答路径 | 同上，query="HX-100 采购价格是多少" | abstain=true、INSUFFICIENT、NO_RELIABLE_SOURCE、citations=[]（FR-006） |
| 设备隔离 | query=E104, device_id=hx80 | abstain=true（A 设备资料不答 B 设备，FR-005） |
| 前端全链路 | 浏览器 UI 提交 E104 | 用户消息→管线进度（真实事件驱动）→Grounded answer→引用徽章 p.1→Evidence"证据部分覆盖"+来源卡 v2.1 Page 1 |
| 自动化测试 | `uv run pytest -q` | 14 通过：单元（intent/RRF/生成四态）+ 集成（真实 Postgres：成功/拒答/隔离） |

## 2. 【Fake】层说明（当前生效的测试替身）

| 替身 | 位置 | 行为 | 换真实实现的条件 |
| --- | --- | --- | --- |
| FakeEmbedding | `llm/providers.py` | 词哈希 1024 维确定性向量；与词面重叠文本余弦更近 | Q-010：百炼 text-embedding-v4（工厂已就绪，实现待凭据） |
| FakeReranker | 同上 | 恒等保序截断 Top6 | Q-010：qwen3-rerank |
| ExtractiveGenerator | `llm/generator.py` | 抽取式答案（只摘证据原文，满足 A1/A2）；拒答/冲突/安全提示逻辑真实 | Q-010：OpenAI-compatible LLM + 结构化 JSON 输出 |

**诚实声明**：当前系统的"答案质量"是抽取式替身水平，不代表真实 LLM 效果；但拒答、引用、版本冲突、安全提示等**行为逻辑**是产品逻辑，与模型无关，已全部落地并有测试。

## 3. 本阶段发现并修复的缺陷

| 缺陷 | 影响 | 修复 |
| --- | --- | --- |
| dense 检索无相似度阈值 | 无关查询也返回"最近邻"垃圾证据 → 拒答路径失效（FR-006 被击穿） | `retrieval_dense_max_distance=0.95`（配置化，真实 embedding 需重标定）；拒答路径测试恢复通过 |
| 集成测试污染开发库 | 测试 fixture 的 env 覆盖时机不可靠，测试数据写进 h2copilot 库 | conftest 顶层（收集期）切 h2copilot_test；残留数据已清理；复测确认开发库不再被写 |
| Alembic 部分唯一索引 WHERE 子句生成错误 | 迁移失败 | `postgresql_where=text("is_current")`（非 func.text） |
| `session_scope` 缺 `@asynccontextmanager` | 运行时无法 `async with`（mypy 抓出） | 已修复 |

## 4. 已知边界（移交 Phase 6 / 待输入）

1. 跨语言检索（FR-101，P0）：FakeEmbedding 无跨语言语义，中文问英文文档当前只能靠词法精确词命中——**必须等 Q-010 真实 embedding 才能验证**（V-4 同源）。
2. 版本冲突 E2E：冲突检测逻辑有单测；受 is_current 唯一约束，默认检索域不会自然触发多版本冲突，E2E 冲突演示需要双版本数据集（Phase 6 构建）。
3. Source Viewer 仍为模拟 PDF 页（T-020 PDF.js 待做）；反馈按钮 UI 有、落库 API 未接（T-022）。
4. Git Bash 控制台以 GBK 发送中文 JSON 体会报 body parse 错误——API 无缺陷（UTF-8 文件体正常），已记录避坑。
5. 性能：单次检索 15ms（1 chunk 数据量）；真实数据量的性能证据在 Phase 6 负载与 Phase 5 评测。
