# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **Phase 4 收尾（等待用户）**：Q-012 —— 打开 `http://localhost:3000` 查看视觉还原度并确认或提出修改（重点：四态徽章观感、D-1～D-5 有意差异清单见 `docs/phase4-visual-baseline.md`）。

2. **执行 Phase 5：第一条端到端垂直切片（Q-012 不阻塞开工，阻塞验收）**
   - 输入：契约（contracts.md）、ADR、工程基线、前端骨架（本轮）、API SSE 桩。
   - 动作：T-013 数据模型与迁移 → T-014 接入管线 → T-015 hybrid 检索 → T-016 生成与验证 → T-017 真实 Query API+SSE → 前端换真实数据；先建集成测试再实现（fake provider）。
   - 硬前置：Q-010（百炼 API Key）、Q-011（演示 PDF）——没有它们只能做到 fake provider 级闭环，真实集成证据必须等凭据。

## 暂不执行

- Evaluation / Settings 页面实现（已裁决不进 MVP）。
- Evidence 数值评分环（已裁决改为状态徽章）。
- 真实付费 API 调用（等 Q-010 凭据与授权）。
- 未经确认向外部任务系统同步或发布内容。
