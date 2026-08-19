# ADR-0001 使用 PostgreSQL + pgvector 作为唯一数据与检索底座

- 状态：已接受
- 日期：2026-08-19
- 来源：技术规范 §9–10、§33–36

## 背景

MVP 需要业务数据、全文检索（错误代码/型号精确匹配）与向量检索（语义问题）三种能力。独立向量库或搜索引擎会新增组件与运维成本。

## 决策

单个 PostgreSQL 实例承担：业务数据 + 元数据 + tsvector 全文检索 + pgvector 向量检索。Hybrid 检索用 RRF 融合两路结果（技术规范 §33–36）。检索过滤条件（device/version/status/language/trust）在同一 SQL 内生效。

## 后果

- 组件数最少，docker compose 只需 web/api/postgres（技术规范 §100）。
- 当出现百万级 chunks、sparse+dense 多向量或复杂过滤的性能压力时，再评估迁移 Qdrant；不提前迁移。
- 未验证项：pgvector hybrid 查询在真实数据量下的性能（Phase 3 集成测试 + Phase 5 评测给出证据）。
