# ADR-0006 MVP 范围裁决记录

- 状态：已接受（用户裁决）
- 日期：2026-08-19
- 来源：Q-007（C-2）、Q-008（C-5）；PRD §17–21、§58；前端原型

## 背景

PRD 信息架构含 Admin 区块但无 Evaluation/Settings；前端原型恰好相反。PRD DoD 要求中英文 Query 但 FR-101 列为 P1。

## 决策

1. **页面范围**：MVP 实现 Ask、Knowledge、Source Viewer；Admin 简化为"上传 + 解析状态查看"。Evaluation 与 Settings 页面不进 MVP——评测走命令行/CI 输出报告。
2. **跨语言**：中英文跨语言检索为 MVP 必须（FR-101 由 P1 提为 P0）。依据：3 分钟 Demo 第 6 幕依赖跨语言；所选 embedding 原生多语言，增量成本低。
3. **反馈**：按 PRD FR-009 完整实现（👍/👎/🚩 + 原因多选），原型的简化按钮仅作视觉起点（C-4 收敛）。

## 后果

- Phase 4 视觉骨架只建 Ask / Knowledge / Source Viewer（+上传弹窗），不建 Evaluation / Settings 路由。
- 评测报告入口为 CLI（`evals/`），不占用前端工时；T-025 承接 P1 加分项。
- 跨语言问题进入 golden dataset 必填类目（T-023）。
