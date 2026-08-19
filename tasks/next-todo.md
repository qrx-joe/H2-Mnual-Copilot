# Next To Do

这里只维护当前最值得推进且可以验证的下一步。

## 当前

1. **执行 Phase 3：工程基线**
   - 输入：`docs/architecture/system-design.md` + `docs/architecture/contracts.md` + ADR-0001—0007 + 技术规范 §11（仓库结构）。
   - 动作：按系统设计 §1 建立最小工程（apps/web + apps/api + packages/contracts + infra/compose + evals 骨架），锁定 Python 3.12 / Next.js 16.3.1（复查当日 latest），落实 `PYTHONUTF8=1`、.gitignore（data/、.env*）；建立 lint/typecheck/最小测试与 SSE 冒烟；实际运行并记录命令与输出。
   - 验证：T-007 完成——新环境可按文档复现安装、启动与检查；V-3（pgvector 集成测试）与 V-6（SSE 冒烟）落为本地验证证据。

2. **用户侧并行输入（不阻塞 Phase 3，阻塞 Phase 5）**
   - Q-010：提供百炼 API Key 的注入方式（.env.local，不入库）。
   - Q-011：提供 HX-100 演示 PDF 集与 golden 问题素材。

## 暂不执行

- Evaluation / Settings 页面实现（已裁决不进 MVP，仅作视觉参考）。
- Evidence 数值评分环实现（已裁决改为状态徽章）。
- 真实付费 API 调用（等 Q-010 凭据与授权）。
- 未经确认向外部任务系统同步或发布内容。
