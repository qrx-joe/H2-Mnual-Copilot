# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **执行 Phase 6：质量、异常、安全与可观测性**
   - 输入：Phase 5 切片（`docs/phase5-vertical-slice.md` §4 边界清单）+ 追踪矩阵。
   - 动作：T-009 状态补齐（超时/不可用）；T-020 Source Viewer 真实 PDF（PDF.js 页定位）；T-022 反馈落库 API；T-023 golden dataset（合成样例集先建 30 条）；T-024 安全测试集；性能与日志核对。
   - 验证：核心需求逐条有测试或人工验收步骤；阻塞缺陷有状态。
   - 说明：真实模型相关评测仍等 Q-010/Q-011。

2. **用户侧输入（阻塞真实模型证据）**
   - Q-010：百炼 API Key（.env.local 注入）→ 接入真实 embedding/rerank/LLM 并重标定距离阈值。
   - Q-011：HX-100 演示 PDF + golden 问题素材 → 真实解析质量与 MinerU 触发条件。
   - Q-012：Phase 4 视觉确认（localhost:3000 现已跑真实链路，可一并体验）。

## 暂不执行

- Evaluation / Settings 页面（已裁决不进 MVP）。
- Evidence 数值评分环（已裁决改为状态徽章）。
- 真实付费 API 调用（等 Q-010 凭据与授权）。
- 未经确认向外部任务系统同步或发布内容。
