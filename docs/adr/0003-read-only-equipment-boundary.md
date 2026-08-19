# ADR-0003 只读设备边界：系统不提供任何设备控制能力

- 状态：已接受
- 日期：2026-08-19
- 来源：技术规范 §51、§118；PRD §6、§8

## 背景

工业场景中"AI 建议操作"与"AI 执行操作"的风险完全不同。本产品定位是 Decision Support（PRD §6）。

## 决策

系统架构层不提供任何 equipment write tool（无 set_pressure/open_valve/shutdown 等接口）。未来接入 PLC/SCADA/IoT 遥测也必须经 ReadOnlyTelemetryAdapter，第一阶段不允许控制接口。

## 后果

- 这是架构级防护，不依赖 prompt 约束；prompt 注入最坏情况也只是"读"。
- 验收方式：代码审查确认无控制接口；该约束进入安全测试集（T-024）。
