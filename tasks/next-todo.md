# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **执行 Phase 4：视觉系统与前端骨架**
   - 输入：前端原型（`docs/sources/H2_Manual_Copilot_Frontend_Prototype.html`，基线 a3739cd9）+ 追踪矩阵视觉状态列 + ADR-0005/0006。
   - 动作：提取 design tokens；实现 Ask / Knowledge / Source Viewer 页面壳层与核心组件（正常/加载/空/错误/禁用状态）；Evidence 用四态徽章（不用评分环）；固定测试数据接 SSE 桩联调；不建 Evaluation/Settings 路由。
   - 验证：页面结构与原型可逐项对照；lint/vitest/build 全绿；浏览器截图核对（注明证据边界）。

2. **用户侧并行输入（不阻塞 Phase 4，阻塞 Phase 5）**
   - Q-010：提供百炼 API Key 的注入方式（.env.local，不入库）。
   - Q-011：提供 HX-100 演示 PDF 集与 golden 问题素材。

## 暂不执行

- Evaluation / Settings 页面实现（已裁决不进 MVP，仅作视觉参考）。
- Evidence 数值评分环实现（已裁决改为状态徽章）。
- 真实付费 API 调用（等 Q-010 凭据与授权）。
- 未经确认向外部任务系统同步或发布内容。
