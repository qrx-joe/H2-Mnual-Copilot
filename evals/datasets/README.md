# 评测数据集

- `golden.jsonl`：≥30 条 golden 问题（PRD §49、技术规范 §79），类目必须覆盖
  Easy / Exact / Semantic / Cross-language / Version / No-answer（Q-008 裁决后
  Cross-language 为必填类目）。
- 数据来源：待用户提供 HX-100 演示 PDF 与问题素材（Q-011）后构建；
  在此之前不虚构评测数据。

每行 schema（技术规范 §79）：

```json
{"question": "E104 是什么？", "device_id": "hx100", "expected_document": "maintenance-v2.1", "expected_pages": [127], "answerable": true}
```
