# 发布与回滚清单（Phase 7 产出，未执行）

> 适用：Hackathon Demo 部署（技术规范 §99：Vercel/VM/compose 单机）  
> 前置授权：任何真实部署、第三方写入、生产变更都需要用户明确授权（AGENTS.md 与执行方案约定）

## 1. 发布前检查（全部通过才可发布）

- [ ] 全量检查链绿（见 `docs/acceptance-report.md` §1 的命令）
- [ ] `ADMIN_PASSWORD`、`DASHSCOPE_API_KEY` 等敏感配置只在服务端环境（禁止任何 `NEXT_PUBLIC_*` 密钥）
- [ ] `.env` / `data/` / `node_modules` / `.next` 未入库（`git ls-files` 复核）
- [ ] Alembic 回滚演练通过（`downgrade base → upgrade head`，本阶段已验证）
- [ ] 评测指标不回退（`run_eval.py` 与上一版 `evals/report.json` 对比）
- [ ] Q-010/Q-011 已提供并完成真实模型复验（或用户明确接受 Fake 级演示）

## 2. 发布步骤（Demo 单机 compose 方案）

1. 准备目标机器：Docker、git checkout `v0.1.0-rc1`（或后续正式 tag）。
2. `docker compose -f infra/compose/docker-compose.yml up -d`（postgres+pgvector）。
3. API：`cd apps/api && cp .env.example .env` → 填入真实配置 → `uv sync` → `uv run alembic upgrade head` → `uv run uvicorn h2copilot.api.app:app --port 8000`（生产建议容器化：Dockerfile 待 Phase 8 按需补充）。
4. Web：`cd apps/web && pnpm install && pnpm build && pnpm start`（或 `NEXT_PUBLIC_API_URL` 指向 API 地址后构建）。
5. 冒烟：`/health` 200 → 上传手册 → E104 问答 → 引用打开 PDF。
6. 演示数据：`scripts/make_sample_manual.py`（合成）或真实手册（Q-011）。

## 3. 回滚条件与步骤

**触发条件**：健康检查连续失败；问答错误率骤增（日志 evidence_status 异常分布）；数据库故障；评测指标回退超阈值。

**步骤**（按影响面从小到大）：
1. 进程级：重启 API/Web 容器（无状态，数据在 Postgres）。
2. 配置级：回滚 `.env` 变更（模型/阈值类改动无需动数据）。
3. Schema 级：`alembic downgrade -1` → 修复 → `upgrade head`（ENUM DROP 已验证可逆）。
4. 数据级：恢复 Postgres 备份（生产要求每日备份，§102）；对象存储原始 PDF 是索引重建的唯一真源，不可只备份向量。
5. 版本级：`git checkout <上一 tag>` 重新构建部署。

## 4. 监控指标（上线后观察）

- 结构化日志已具备（§69）：`intent / retrieval_ms / chunks / evidence_status / abstain / model_alias`——按 request_id 关联。
- 告警建议：evidence_status=INSUFFICIENT 占比突增（知识库或检索退化）；retrieval_ms P95 > 500ms；429 频率；ingestion FAILED 数。
- Langfuse/OTel：SDK 接入位预留（技术规范 §70–71），生产按需开启。

## 5. 明确不做（本版本）

- 不自动推送远程、不写第三方系统、不申请云资源——全部等待用户授权。
