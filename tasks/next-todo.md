# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **执行 Phase 7：验收与交付准备**
   - 输入：Phase 6 证据回填后的追踪矩阵 + `docs/phase6-quality-report.md` 边界清单。
   - 动作：全量测试/类型/构建复跑；Alembic downgrade→upgrade 演练（T-013 残余）；运行说明与已知限制汇总（README 更新）；发布/回滚清单；检查变更范围（无凭据/缓存/临时文件入库）。
   - 验证：T-010 完成；候选版本可复现；**不部署**——真实部署等待用户授权。

2. **用户侧输入（决定 Phase 7 后走向）**
   - Q-010：百炼 API Key → 接真实模型 + 重标定阈值 + golden 全量重跑（跨语言 8 条解锁）。
   - Q-011：真实手册 PDF + golden 素材 → 真实解析质量与 MinerU 触发条件。
   - Q-012：视觉确认（localhost:3000 现为真实链路，含 PDF 抽屉与反馈）。

## 暂不执行

- 真实部署/外部写入/付费 API 调用（等待授权与 Q-010）。
- Evaluation / Settings 页面、Evidence 数值评分环（已裁决）。
