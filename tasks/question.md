# Question

记录会影响范围、方案、优先级或验收的未决问题。

| ID | 状态 | 问题 | 为什么需要回答 | 来源 | 结论去向 |
| --- | --- | --- | --- | --- | --- |
| Q-003 | 待确认 | 任务文档是否只需保存在仓库，还是还要同步到外部任务系统？ | 外部系统写入会改变第三方状态，需要单独授权 | 用户本轮要求 | 待确认 |
| Q-010 | 待确认 | 百炼（DashScope）API Key 何时提供、以何种方式注入（.env.local / 环境变量）？ | V-4 假设验证与 Phase 5 真实集成（embedding/rerank/LLM）都依赖凭据；密钥只进服务端环境，不进仓库 | 2026-08-19 交互 009（V-4） | 待补充 |
| Q-011 | 待确认 | HX-100 演示文档集（Operation/Maintenance/Safety/Error Codes PDF）与 ≥30 条 golden 问题素材何时到位？ | 真实解析质量验证（V-2 后半）、MinerU 触发条件标定、T-023 评测全部阻塞于此；属关键路径输入 | 2026-08-19 交互 009 | 待补充 |
| Q-012 | 待确认 | Phase 4 视觉基线确认：请打开 `http://localhost:3000`（服务已在本地运行）查看 Ask/Knowledge/Source Viewer，确认视觉还原度或提出修改；重点确认四态徽章替代评分环后的观感 | Phase 4 验收门要求视觉差异由负责人确认（`docs/phase4-visual-baseline.md` §3–§5） | 2026-08-19 交互 011 | 待确认 |

## 已解决问题

| ID | 解决日期 | 结论 | 结论去向 |
| --- | --- | --- | --- |
| Q-002 | 2026-08-19 | 默认记录本 Codex 项目任务中的每轮项目相关交流；其他渠道只有在用户明确要求并提供可访问内容时纳入 | `AGENTS.md`、`tasks/README.md` |
| Q-005 | 2026-08-19 | ZCode 侧确认：会读取并遵守根目录 `AGENTS.md`（交互 005 已实际执行该规则），具备斜杠命令与技能系统，但没有强制的专有阶段工作流；执行方案中的通用自然语言提示词可直接复制执行，无需专有适配 | `tasks/advice.md`（交互 005 评审）、`tasks/communicating.md` |
| Q-001 | 2026-08-19 | 三份源资料已由用户提供（`D:\EdgeDownload\`）并复制登记入库 `docs/sources/`，副本与原件 SHA-256 一致；版本与哈希见 `tasks/advice.md` 源资料登记表 | `docs/sources/`、`tasks/advice.md`（交互 007）、`tasks/communicating.md` |
| Q-004 | 2026-08-19 | 用户本人为最终裁决人；优先级 PRD＞技术规范＞视觉原型（产品意图以 PRD 为准，技术约束以技术规范为准，原型服从前两者） | `tasks/advice.md`（交互 007 检查点裁决）、`tasks/communicating.md` |
| Q-006 | 2026-08-19 | Evidence 面板不展示数值评分环，改为 evidence status 徽章（SUFFICIENT / PARTIAL / INSUFFICIENT / CONFLICTING） | 同上 |
| Q-007 | 2026-08-19 | MVP 页面范围以 PRD P0 为准：Ask、Knowledge、Source Viewer；Admin 简化为上传 + 状态查看；Evaluation / Settings 不进 MVP，评测走 CI / 命令行 | 同上 |
| Q-008 | 2026-08-19 | 中英文跨语言检索列为 MVP 必须，FR-101 由 P1 提为 P0（依据：Demo 黄金路径第 6 幕依赖跨语言；所选 embedding 原生多语言，增量成本低） | 同上 |
| Q-009 | 2026-08-19 | 视觉方案基线以入库文件 SHA-256（a3739cd9）标识；后续如补发带版本号的视觉方案则重新登记 | `tasks/advice.md` 源资料登记表 |
