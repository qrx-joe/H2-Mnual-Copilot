# H2 Manual Copilot｜氢能设备智能手册助手

Evidence-grounded Industrial Knowledge Copilot：面向氢能设备手册的智能问答，答案可追溯到具体文档、版本与页码，证据不足时明确拒答。

- 产品需求：`docs/sources/`（PRD v1.0）
- 实施基线：`docs/implementation-baseline.md`
- 系统设计：`docs/architecture/system-design.md`；接口契约：`docs/architecture/contracts.md`
- 架构决策：`docs/adr/`
- 任务与协作记录：`tasks/`

## 环境要求

| 工具 | 版本 | 用途 |
| --- | --- | --- |
| uv | ≥ 0.11 | Python 依赖管理（锁定 3.12，`apps/api/.python-version`） |
| pnpm | ≥ 10 | Node 依赖管理（workspace，lockfile 已提交） |
| Node.js | ≥ 20（本机验证 24） | 前端构建 |
| Docker | ≥ 24（本机验证 29） | PostgreSQL + pgvector |

Windows 提示：建议设置 `PYTHONUTF8=1`，避免控制台 GBK 编码噪音（见 `scratch/phase2/RESULTS.md`）。

## 快速开始

```bash
# 1. 基础设施（PostgreSQL 16 + pgvector）
docker compose -f infra/compose/docker-compose.yml up -d
# 等待 healthy：docker inspect --format "{{.State.Health.Status}}" h2copilot-postgres

# 2. 后端（FastAPI，端口 8000）
cd apps/api
cp .env.example .env        # 本地开发可直接用默认值；密钥绝不提交
uv sync
uv run uvicorn h2copilot.api.app:app --reload

# 3. 前端（Next.js，端口 3000）
cd apps/web
pnpm install                # 或在仓库根目录执行（workspace）
pnpm dev
```

## 检查与测试

```bash
# 后端（apps/api）
uv run ruff check .         # 静态检查
uv run mypy src             # 类型检查
uv run pytest -q            # 单元/契约测试（SSE 事件序列）

# 前端（apps/web）
pnpm lint                   # ESLint
pnpm test                   # Vitest
pnpm build                  # 生产构建（含 TypeScript 检查）

# 基础设施冒烟（V-3：扩展 + 词法/向量双路 SQL）
docker exec -i h2copilot-postgres psql -U h2copilot -d h2copilot < scripts/smoke_hybrid.sql

# 运行中服务冒烟
curl -s http://127.0.0.1:8000/health
curl -s -N -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" -d '{"query":"E104","device_id":"hx100"}'
```

Phase 3 基线的实际命令与输出记录：`docs/engineering-baseline.md`。

## 仓库结构

```text
apps/
  web/        Next.js 16.3.1（精确锁定）+ Tailwind + TypeScript
  api/        FastAPI（Python 3.12，uv 管理）—— src/h2copilot 分层
packages/
  contracts/  前后端共享契约类型（权威定义：docs/architecture/contracts.md）
infra/
  compose/    开发环境 docker compose（postgres + pgvector）
scripts/      冒烟与辅助脚本
evals/        评测数据集与脚本（golden dataset 待 Q-011 素材）
docs/         源资料、基线、架构、ADR、验证报告
tasks/        人机协作记录（todo/question/advice/communicating/next-todo）
scratch/      隔离验证代码（Phase 2 风险验证，可删除）
```

## 当前状态

- Phase 0–6 完成（资料基线、MVP 收敛、架构契约、工程基线、视觉骨架、垂直切片、质量与异常）。
- **Phase 7 候选版本 `v0.1.0-rc1`（本地标记）**：验收报告见 `docs/acceptance-report.md`；发布与回滚清单见 `docs/release-checklist.md`（未部署）。
- 模型层为确定性测试替身（Fake）——拒答/引用/版本冲突/安全提示等产品逻辑已验证；真实模型质量指标待百炼 API Key（Q-010）与真实手册（Q-011）。

## 已知限制（候选版本）

1. 答案为抽取式替身输出，不代表真实 LLM 质量；跨语言语义检索待真实 embedding。
2. Source Viewer 为"原始 PDF 跳页 + 高亮摘录卡"，页内文本高亮需 PDF.js 文本层（后续版本）。
3. 限流为进程内实现；对象存储为本地卷（`data/storage/`，生产换 S3 适配器，ADR-0007）。
4. `ADMIN_PASSWORD` 未配置时管理接口在开发模式放行——生产必须配置。
5. `scratch/` 目录为 Phase 2 隔离验证代码，可整体删除。
