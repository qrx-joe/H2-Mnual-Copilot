# Phase 3 工程基线验证报告（实际命令与输出）

> 日期：2026-08-19（Asia/Shanghai）  
> 环境：Windows 11（Git Bash）、Python 3.12（uv 管理，本机 3.13 不用于本项目）、uv 0.11.14、Node 24.13.0、pnpm 10.32.1、Docker 29.4.1（Docker Desktop 由本轮启动）  
> 结论：T-007 完成标准达成——新环境按 `README.md` 可复现安装、启动与检查；下方为逐项实际输出。

## 1. 后端（apps/api）

| 检查 | 命令 | 实际结果 |
| --- | --- | --- |
| 依赖锁定 | `uv sync` | 成功生成并提交 `uv.lock`（fastapi/uvicorn/pydantic/pydantic-settings + dev 组） |
| 静态检查 | `uv run ruff check .` | `All checks passed!`（首轮发现 6 处 E501 超长 1 字符，已重构 conftest fixture 修复） |
| 类型检查 | `uv run mypy src` | `Success: no issues found in 10 source files`（首轮 1 处返回类型标注错误，已修复为 `AsyncIterator[str]`） |
| 单元/契约测试 | `uv run pytest -q` | `8 passed in 0.15s`（健康 2、配置 3、SSE 契约 3） |
| 进程冒烟 | `uv run uvicorn h2copilot.api.app:app --port 8001` 后 curl | `/health` → `{"status":"ok","app":"h2copilot-api","db_configured":false,"request_id":"636b491be9ce"}`；`POST /api/v1/query` → SSE 7 事件完整序列（retrieval.started → … → done），访问日志为 JSON 行（含 request_id/status/duration_ms） |

**V-6（SSE 流式）就此从【推断】升级为【本地验证】**：真实 uvicorn 进程、text/event-stream、契约事件序列、X-Request-ID 透传均实证。

## 2. 数据库（infra/compose）

| 检查 | 命令 | 实际结果 |
| --- | --- | --- |
| 容器启动 | `docker compose -f infra/compose/docker-compose.yml up -d` | 容器 10 秒内 `health=healthy`（pgvector/pgvector:0.8.0-pg16） |
| 扩展验证 | `docker exec -i h2copilot-postgres psql ... < scripts/smoke_hybrid.sql` | `CREATE EXTENSION`；`vector 0.8.0` |
| 词法路 | 同上（tsv @@ to_tsquery('E104') + is_current 过滤） | 命中 chunk 1；历史版本 chunk 3 被正确排除 |
| 向量路 | 同上（embedding <=> 查询向量，LIMIT 2） | chunk 1 距离 0.006、chunk 2 距离 0.782，排序正确 |
| 版本域 | `SELECT count(*) WHERE is_current` | 3 行中 2 行 current（v1.9 superseded 被隔离） |

**V-3 就此从【推断】升级为【本地验证（扩展与 SQL 语法级）】**；真实数据量下的性能证据仍留待 Phase 5 评测。

## 3. 前端（apps/web）

| 检查 | 命令 | 实际结果 |
| --- | --- | --- |
| 脚手架 | `pnpm create next-app@16.3.1 apps/web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm --disable-git --skip-install --yes` | 成功；`package.json` 中 `next: "16.3.1"`（精确版本，无 `^`）——**C-7 关闭** |
| 依赖安装 | 仓库根 `pnpm install`（workspace 含 contracts） | 成功（7m8s，Windows 文件系统较慢；提示忽略 esbuild/unrs-resolver 构建脚本，不影响 lint/test/build） |
| ESLint | `pnpm lint` | 通过（无输出） |
| Vitest | `pnpm test` | `2 passed`（evidence 四态徽章映射，ADR-0005） |
| 生产构建 | `pnpm build` | `Compiled successfully in 5.9s`；TypeScript 检查通过；4 个静态页生成 |

## 4. 失败事实与修复记录

1. ruff 首轮 6 处 E501（超长 1 字符）→ 提取 `tests/conftest.py` 共享 fixture 后全绿。
2. mypy 首轮 1 处 `StreamingResponse` 参数类型不匹配 → `_event_stream` 返回类型改为 `AsyncIterator[str]`。
3. Docker 守护进程初始未运行（`failed to connect to the dockerDesktopLinuxEngine`）→ 启动 Docker Desktop 后恢复；已如实记录，不视为基线缺陷。
4. Git Bash 控制台对部分中文提交信息显示乱码，git 内存储为正确 UTF-8（已用 `xxd` 验证字节）。

## 5. 未覆盖风险（进入 Phase 4/5 前须知）

- `uv run uvicorn` 尚未与真实 Postgres 建立连接（数据层 Phase 5 接入，T-013）。
- pnpm 提示的 esbuild 构建脚本未批准：vitest 当前可运行；若后续需要其二进制优化，运行 `pnpm approve-builds`。
- CI workflow 已编写但仓库无远端，未实际触发。
- SSE 冒烟基于桩数据；真实管线的流式行为（含错误事件）在 Phase 5 验证。
- Docker Desktop 在本机需手动启动（或设置为开机自启）；新环境文档已写明前置条件。
