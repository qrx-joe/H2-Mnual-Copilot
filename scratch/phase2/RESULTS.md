# Phase 2 风险验证结果

> 日期：2026-08-19（Asia/Shanghai）  
> 环境：Windows（Git Bash）、Python 3.13.6 / uv 0.11.14（验证用临时环境为 uv 管理的 3.12）、Node 24.13 / pnpm 10.32 / npm 11.6、Docker 29.4.1（本次未起容器）  
> 性质：本目录为隔离验证代码，结论可复现；Phase 5 后可整体删除，不得被产品代码引用。

## V-1 RRF 融合与错误代码路由 —— 【本地验证】通过

- 命令：`python scratch/phase2/verify_logic.py`（纯标准库）
- 结果：11/11 断言通过。
  - `^[A-Z]{1,4}[-_]?\d{2,6}$` 命中 E104 / e104（规范化后）/ HX-100 / E-12；拒绝自然语言、多词、纯数字。
  - RRF（k=60）：双路命中 chunk 排序高于单路命中；融合覆盖全部候选且无重复。
- 设计影响：`domain/retrieval` 纯逻辑实现方案成立；错误代码与设备型号共用精确词法路由（技术规范 §34、§38）。

## V-2 PyMuPDF4LLM 解析机制 —— 【本地验证】机制级通过

- 命令：`uv run --no-project --with pymupdf4llm python scratch/phase2/verify_parser.py`
- 版本：pymupdf4llm 1.28.2（依赖含 pymupdf、onnxruntime、pymupdf-layout，共 12 包）
- 结果：9/9 断言通过（含首轮失败后的修正）。
- **首轮发现（重要）**：默认 `to_markdown()` 输出不含页码标记；页码溯源必须使用 `page_chunks=True` 模式，页码取 `metadata.page_number`（1 起算，可直接作为引用页码）。该结论已固化到 `docs/architecture/system-design.md` §3.2，T-014 ingestion 实现须采用此模式。
- 证据边界：机制级验证（库可安装、标题/正文/页码保留）。**真实手册质量（多栏、表格、扫描件）【待验证】**，阻塞于演示 PDF（Q-011）；MinerU fallback 触发条件需真实样本才能标定。

## V-3 pgvector hybrid SQL 正确性与性能 —— 未运行【推断】

- 原因：需启动 postgres+pgvector 容器，属 Phase 3 集成测试范围。
- 当前证据层级：SQL 模式为技术规范 §9/§36 引用的 pgvector 官方口径，未在本机运行。Phase 3 集成测试升级为【本地验证】；性能预算证据在 Phase 5 评测产出。

## V-4 embedding/rerank 检索质量 —— 未运行【待验证】

- 阻塞条件：百炼 API 凭据（Q-010）+ 演示 PDF 与 golden 问题（Q-011）。
- 说明：调用付费 API 属外部操作，按执行方案需用户单独授权/提供凭据后再验证。

## V-5 Next.js 可锁定版本 —— 【本地验证】

- 命令：`npm view next version` / `npm view next dist-tags --json`
- 结果：latest = **16.3.1**（2026-08-19 查询），与技术规范 §6"当前官方发布线已到 16.3"一致。
- 设计影响：Phase 3 工程基线锁定候选为 `next@16.3.1`（pnpm 精确版本 + lockfile 提交）；锁定当日需复查是否有更新 patch。

## V-6 SSE 流式 —— 未单独验证【推断】

- FastAPI/Next.js 标准能力，风险低；Phase 3 工程基线以冒烟测试（curl SSE 端点断言事件序列）落为【本地验证】。

## 环境备注（Phase 3 需处理）

1. **Windows 控制台编码**：uv 子进程读取线程在 GBK 控制台下出现 UnicodeDecodeError 噪音（不影响验证结果）。Phase 3 统一在脚本/文档中设置 `PYTHONUTF8=1`（或 `PYTHONIOENCODING=utf-8`）。
2. **Python 版本**：本机 3.13.6，技术规范要求 3.12；工程基线用 uv `.python-version` 锁定 3.12（本次临时环境即 3.12，已验证可用）。
3. `import fitz` 已弃用，统一 `import pymupdf`。
