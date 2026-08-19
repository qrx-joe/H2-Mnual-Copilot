# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **执行 Phase 2：架构边界、调用链与契约**
   - 输入：`docs/implementation-baseline.md` + `docs/traceability-matrix.md` + 技术规范 v1.0。
   - 动作：使用 `tasks/zcode-execution-plan.md` 的 Phase 2 提示词，产出运行入口、模块边界、主调用链、数据流、接口/数据契约、错误与降级策略、关键决策记录（ADR）；对 `tasks/advice.md` 交互 008 的 6 条未验证假设做最小技术验证（验证代码与生产实现隔离）。
   - 验证：主链路无阻塞性 P0 架构问题；每项结论标注证据层级（代码推断/本地验证/真实环境证据）。

2. **并行准备（用户侧，不阻塞 Phase 2）**
   - 准备 HX-100 演示文档集（Operation/Maintenance/Safety/Error Codes，PRD §47–48）与 ≥30 条 golden 问题的原始素材。

## 暂不执行

- Evaluation / Settings 页面实现（已裁决不进 MVP，仅作视觉参考）。
- Evidence 数值评分环实现（已裁决改为状态徽章）。
- 未经确认向外部任务系统同步或发布内容。
