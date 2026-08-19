# ADR-0005 Evidence 面板使用四态徽章，不展示未校准的数值评分

- 状态：已接受（用户裁决）
- 日期：2026-08-19
- 来源：技术规范 §44；前端原型 Evidence 评分环；Q-006 裁决（C-1）

## 背景

前端原型 Evidence 面板使用数值评分环（95/63/12）。技术规范 §44 明确：未经概率校准不得展示置信度百分比。两者冲突。

## 决策

Evidence 充分度只用四态徽章表达：SUFFICIENT / PARTIAL / INSUFFICIENT / CONFLICTING，与后端 structured output 的 evidence_status 字段一一对应。不展示任何数值评分。

## 后果

- 前后端契约简化：徽章直接由 evidence_status 驱动，无需额外计算口径。
- 原型中的评分环在 Phase 4 实现时替换为徽章组件（保留环形视觉可后续用于已校准指标，MVP 不做）。
