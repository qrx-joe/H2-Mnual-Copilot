# ADR-0004 版本感知检索：按 DocumentVersion 隔离，冲突不静默裁决

- 状态：已接受
- 日期：2026-08-19
- 来源：技术规范 §16、§92；PRD P4、A6

## 背景

同一设备手册存在多版本（如 V1 1.5 MPa / V2 1.2 MPa）。旧版本内容不能默认覆盖新版本，AI 不得任选一个作答（PRD A6）。

## 决策

1. Chunk 挂在 DocumentVersion 而非 Document 下；检索必须带 document_version_id 维度。
2. 用户未指定版本时，只检索 is_current=True 且 ACTIVE 的版本。
3. 无法安全确定目标版本时返回 AMBIGUOUS_VERSION 错误，由用户确认；不允许 LLM 自行选择版本（技术规范 §92）。
4. 历史版本保留用于冲突识别与审计，默认不进检索候选。

## 后果

- 回答永远可归因到"哪个版本的哪一页"。
- Version 类 golden 问题（V1 vs V2 差异）必须进入评测集（T-023）。
