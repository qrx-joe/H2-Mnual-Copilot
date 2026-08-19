# 项目任务协作记录

本目录用于持续维护项目决策、任务状态和人机协作记录。

## 文档职责

- [`question.md`](./question.md)：尚未回答、会影响实现或验收的问题。
- [`todo.md`](./todo.md)：已确认要做、但尚未开始或完成的任务。
- [`next-todo.md`](./next-todo.md)：当前唯一优先推进的下一批动作。
- [`communicating.md`](./communicating.md)：用户与 AI 每轮交互的事实性摘要及形成的决定。
- [`advice.md`](./advice.md)：AI 的建议、把握程度、遗漏项和风险提示。

补充执行文档：

- [`zcode-execution-plan.md`](./zcode-execution-plan.md)：供 ZCode 按阶段执行的目标、任务、验收门和可复制提示词。

项目交付文档（`docs/`）：

- [`docs/implementation-baseline.md`](../docs/implementation-baseline.md)：一页实施基线（Phase 1 产出）。
- [`docs/traceability-matrix.md`](../docs/traceability-matrix.md)：需求追踪矩阵（Phase 1 产出）。
- [`docs/sources/`](../docs/sources/)：三类源资料登记基线（Phase 0 入库）。

## 维护约定

1. 每轮项目交互结束前更新 `communicating.md`，写明 Asia/Shanghai 时间、交互编号、智能体身份、该智能体实际写入的文件和内容摘要。
2. 新出现且未解决的问题写入 `question.md`；得到答案后标记为已解决，并记录结论去向。
3. `todo.md` 保存完整任务池；`next-todo.md` 只保留近期可执行、依赖清楚的事项。
4. 建议与事实分开：建议、推测和不确定性统一写入 `advice.md`。
5. 任务状态统一使用：`待确认`、`待办`、`进行中`、`阻塞`、`已完成`、`取消`。
6. 任何任务或结论都应注明来源；无资料支撑时明确写为“未验证”或“假设”。
7. 不追认无法验证的作者或时间；历史记录缺少信息时明确标注“未知”。

## 当前资料状态

2026-08-19 Phase 0 已完成：PRD v1.0、技术规范 v1.0 与前端交互原型已由用户提供并登记入库 `docs/sources/`（路径、版本、哈希见 [`advice.md`](./advice.md) 源资料登记表；git 提交 `eaa3ef4`）。前端原型无版本号，暂以 SHA-256 为基线标识。三份资料间的冲突与缺口见 [`advice.md`](./advice.md) Phase 0 清单与 [`question.md`](./question.md) Q-004、Q-006—Q-009；相关 P0 决策关闭前不进入 Phase 1 实现。
