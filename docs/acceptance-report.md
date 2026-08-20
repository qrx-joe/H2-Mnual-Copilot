# MVP 候选版本验收报告（Phase 7）

> 日期：2026-08-20（Asia/Shanghai）  
> 候选版本：git `main` @ `v0.1.0-rc1`（本地标记，未推送）  
> 证据分层：数据层/接口层/浏览器【真实】；模型层【Fake 替身，Q-010 未提供】  
> 复现命令：`README.md`（安装/启动/检查）；评测 `cd apps/api && uv run python ../../evals/run_eval.py`

## 1. 全量检查链（本阶段实际复跑）

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| API 静态 | `uv run ruff check .` | All checks passed |
| API 类型 | `uv run mypy src` | 31 文件无问题 |
| API 测试 | `uv run pytest -q` | **26 通过**（单元 + 真实 Postgres 集成 + 安全集） |
| Web 静态 | `pnpm lint` | 通过 |
| Web 测试 | `pnpm test` | 5 通过 |
| Web 构建 | `pnpm build` | 成功（/, /knowledge，含 TS 检查） |
| 评测 | `run_eval.py` | recall@citation **1.0** / no-answer **1.0**（22 可跑；8 条阻塞待真实 embedding） |
| 迁移回滚 | `alembic downgrade base && upgrade head`（测试库） | 通过（发现并修复 ENUM 未 DROP 缺陷） |
| E2E | 浏览器实测（Phase 6）：提问→引用→原始 PDF→反馈落库 | 通过 |

## 2. PRD §58 MVP DoD 逐条核对

| DoD 条目 | 状态 | 证据 / 缺口 |
| --- | --- | --- |
| 至少 5 份知识资料成功解析 | ⚠️ 部分 | 合成手册管线验证（4 文档集）；**真实手册待 Q-011**（PRD §46 自建样例为授权替代） |
| 文档可查看 | ✅ | Knowledge 页真实数据 + 上传（浏览器实测） |
| 能回答自然语言问题 | ✅（Fake 层） | 集成测试 + 浏览器实测；真实 LLM 待 Q-010 |
| 能检索 Error Code | ✅ | golden exact 8/8（含混合中文问句路由） |
| 每个重要答案有 Citation | ✅ | 引用实体落库；A3 由安全测试锁定 |
| Citation 可以打开对应页面 | ✅ | /sources + /files + iframe 跳页（浏览器实测） |
| 支持中英文 Query | ⚠️ 部分 | 代码类混合问句已通（§38 路由）；**语义跨语言待真实 embedding（8 条 golden 阻塞）** |
| 没有资料时会明确拒答 | ✅ | no-answer 6/6；拒答红线有阈值+测试双保险 |
| 页面存在 Loading / Error / Empty State | ✅ | Phase 4 状态清单全过 + 超时/不可用降级实测 |
| Demo 环境可以稳定部署 | ❌ 待部署 | 本地可复现（README）；**部署动作等用户授权（Phase 7 门禁）** |
| 至少 30 条 Golden Test | ✅ | `evals/datasets/golden.jsonl` 30 条 + 自动评测 |
| README 可以从零运行项目 | ✅ | 新环境命令齐备（uv/pnpm/docker 前置） |

**结论：12 条中 9 条达成、2 条部分达成（阻塞于 Q-010/Q-011）、1 条待部署授权。** 在用户提供 API Key 与真实手册并授权部署前，本候选版本定位为"本地可验收的 Fake 模型级 MVP"。

## 3. 追踪矩阵终态

见 `docs/traceability-matrix.md`（Phase 6 证据回填节）：10 条 P0 需求中 8 条有完整证据，FR-101（跨语言）与 FR-001（真实手册解析）的部分证据阻塞于外部输入，均已登记归属。

## 4. 已知限制（README 同步摘要）

1. 模型层为确定性替身：答案质量不代表真实 LLM；行为逻辑（拒答/引用/冲突/安全）为产品逻辑已验证。
2. 跨语言语义检索、Faithfulness 指标：待 Q-010。
3. MinerU fallback、真实手册解析质量：待 Q-011。
4. Source Viewer 页内文本高亮：需 PDF.js 文本层（当前为跳页+摘录卡）。
5. 限流为进程内实现（多实例需 Redis）；对象存储为本地卷（生产换 S3 适配器）。
6. Admin 口令未配置时开发模式放行（生产必须配置 `ADMIN_PASSWORD`）。

## 5. 发布与回滚

见 `docs/release-checklist.md`。**本阶段未执行任何部署、外部写入或生产变更。**

## 6. 验收请求

请用户：① 查看本报告与运行中的 localhost:3000（Fake 模型级）；② 决定是否提供 Q-010/Q-011 后复验；③ 授权部署或进入试运行（Phase 8）。
