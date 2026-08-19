# H2 Manual Copilot｜氢能设备智能手册助手
## 产品需求文档 PRD

**文档版本：** v1.0  
**文档日期：** 2026-08-19  
**项目阶段：** Hackathon MVP → 企业 PoC → Production  
**参赛方向：** 企业知识智能服务助手  
**产品类型：** 工业设备知识 Copilot / RAG Knowledge Assistant  
**核心定位：** 面向氢能设备手册、操作文档、维护资料和 FAQ 的安全、可追溯、版本感知型智能知识助手。

---

# 1. 文档目的

本文定义 H2 Manual Copilot 的：

- 产品目标；
- 用户对象；
- 核心场景；
- 功能范围；
- 产品交互；
- AI 行为约束；
- 安全边界；
- 数据要求；
- 验收标准；
- 产品指标；
- MVP 与后续版本规划。

本文回答的是：

> **“应该做什么，以及做到什么程度算完成。”**

具体技术实现、系统架构、数据库设计、RAG Pipeline、API、测试、部署和代码规范，统一放在独立《技术规范文档》中。

---

# 2. 产品背景

## 2.1 行业背景

现代工业设备通常伴随大量：

- 用户手册；
- 安装手册；
- 维护手册；
- 安全规范；
- 故障代码表；
- 参数表；
- SOP；
- FAQ；
- 培训材料。

西门子当前工业 AI 产品已经将 manuals、work instructions、technical and safety specifications、checklists、PLC data、error logs 等作为工业 Copilot 可访问的重要上下文，并将自然语言故障排查作为典型工业场景。

因此真正的问题已经不是：

> “能不能对 PDF 提问？”

而是：

> **能否快速得到可信、可追溯、与具体设备及版本匹配的答案，并知道答案来自哪里。**

---

# 3. 问题定义

传统设备知识获取主要存在五个问题。

## P1：文档多

工作人员需要在几十页甚至几百页 PDF 中人工搜索。

## P2：知识分散

同一个问题的答案可能分散在：

- Operation Manual；
- Installation Guide；
- Maintenance Manual；
- Safety Manual；
- FAQ。

## P3：精确关键词依赖严重

用户可能知道：

> “E104”

但不知道：

> “Coolant circulation system abnormal”。

传统全文搜索非常依赖原始术语。

---

## P4：设备版本容易混淆

同一个设备可能存在：

- V1；
- V2；
- 不同固件；
- 不同地区版本；
- 不同年份手册。

旧版本内容不能默认覆盖新版本。

---

## P5：生成式 AI 存在错误确定性风险

工业环境最危险的不是：

> “AI 不知道。”

而是：

> “AI 不知道，但说得像知道。”

因此 H2 Manual Copilot 必须允许：

> **“当前资料不足，无法可靠回答。”**

而不是强行生成答案。

---

# 4. 产品定位

## 4.1 一句话定位

> **让复杂工业设备手册变成一个能够回答问题、定位证据和辅助排查的可信 AI Copilot。**

---

# 5. 产品名称

正式参赛名称：

# H2 Manual Copilot

中文名：

# 氢能设备智能手册助手

对外副标题：

> **Ask the equipment. Verify the evidence.**

中文：

> **问设备，也看证据。**

---

# 6. 产品不是做什么

为了控制项目范围，本产品明确不是：

### 不是设备自动控制系统

AI 不允许：

- 启停设备；
- 修改 PLC；
- 调整压力；
- 控制阀门；
- 修改安全联锁；
- 自动执行维护命令。

---

### 不是设备诊断系统

产品定义为：

> **Decision Support / Troubleshooting Assistance**

而不是：

> Autonomous Diagnosis。

---

### 不是万能氢能 ChatGPT

不回答与知识库无关的一切氢能问题。

---

### 不是企业超级 Agent

MVP 不包含：

- 自动派工；
- ERP；
- CRM；
- 工单系统；
- 自动采购；
- 自动设备控制。

---

# 7. 产品目标

## 7.1 MVP 目标

用户能够完成一条完整路径：

```text
提出设备问题
↓
检索相关手册
↓
AI生成答案
↓
展示对应证据
↓
查看具体文档 / 页码
```

---

## 7.2 核心目标 G1

**缩短找资料时间。**

---

## 7.3 核心目标 G2

**让回答可以追溯到具体资料。**

---

## 7.4 核心目标 G3

**降低 AI 幻觉带来的错误确定性。**

---

## 7.5 核心目标 G4

支持：

- 中文提问；
- 英文资料；
- 中英文跨语言检索。

Qwen3 Embedding 系列原生面向多语言检索场景，BGE-M3 也支持多语言与不同粒度检索，因此跨语言知识检索在当前技术栈下是成熟可行的。

---

# 8. 产品原则

## Principle 1｜Evidence First

答案必须能够展示来源。

---

## Principle 2｜Fail Closed

资料不足时：

> 不回答。

而不是猜。

---

## Principle 3｜Source ≠ Truth

资料本身也存在：

- 旧版本；
- 错误资料；
- 非官方资料。

因此必须维护：

> Source Trust Level。

---

## Principle 4｜Safety before Fluency

工业场景下：

**安全 > 回答完整度 > 语言漂亮程度。**

---

## Principle 5｜Human in Control

AI 负责：

- 检索；
- 整理；
- 解释；
- 导航。

最终操作责任仍由：

- 操作人员；
- 工程师；
- 企业 SOP；

决定。

---

# 9. 目标用户

## Persona A｜现场运维人员

典型问题：

> E104 是什么意思？

> 设备启动前检查哪些内容？

> 为什么冷却系统报警？

需求特点：

- 快；
- 明确；
- 不想翻手册；
- 希望直接看到操作步骤。

---

## Persona B｜售后技术支持

典型问题：

> 客户报告这个报警，该先检查什么？

需求：

- 快速找到知识；
- 统一回答口径；
- 找原始文档。

---

## Persona C｜新员工

问题：

> PEM 电解槽启动流程是什么？

需求：

- 学习；
- 理解术语；
- 快速定位资料。

---

## Persona D｜海外客户 / 海外售后

问题：

> 中文资料中这个故障对应的解决方法是什么？

需求：

- 中英文互查；
- 技术翻译；
- 原文验证。

---

## Persona E｜知识管理员

负责：

- 上传资料；
- 更新版本；
- 下线旧文档；
- 检查解析结果；
- 管理文档可信等级。

---

# 10. Jobs To Be Done

用户真正想完成的是：

> **当设备相关问题出现时，我希望不用搜索几十页资料，也能快速获得一个基于正式资料、能够回到原文验证的答案。**

---

# 11. 核心使用场景

## S1｜操作流程查询

用户：

> PEM 电解槽启动前需要检查什么？

系统返回：

1. 检查冷却系统；
2. 检查供水；
3. 检查气体管路；
4. 检查电源；
5. 检查安全联锁。

每一点显示对应来源。

---

# 12. S2｜报警代码查询

用户输入：

> E104

系统识别：

```text
Query Type
ERROR_CODE
```

返回：

**报警名称**

**手册解释**

**可能检查项**

**相关章节**

**来源页码**

---

# 13. S3｜自然语言排查

用户：

> 冷却液温度突然很高应该检查什么？

系统：

```text
问题理解
↓
相关故障条目
↓
维护手册
↓
安全文档
↓
生成辅助排查顺序
```

---

# 14. S4｜参数查询

例如：

> 正常工作压力是多少？

这种问题属于高风险参数问题。

系统必须：

1. 判断设备型号；
2. 判断版本；
3. 找到明确参数；
4. 引用来源。

如果设备型号未知：

> **要求用户先选择设备。**

不能跨设备猜测。

---

# 15. S5｜跨语言查询

用户中文提问：

> 如何检查氢气纯度？

资料为英文。

系统：

- 检索英文；
- 中文解释；
- 保留英文原始术语；
- 展示英文原文证据。

---

# 16. S6｜找原始文档

用户：

> 带我看相关手册。

系统直接：

> Maintenance Manual V2.1 · Page 127

---

# 17. 产品信息架构

```text
H2 Manual Copilot
│
├── Ask
│   ├── 普通问题
│   ├── 错误代码
│   └── 操作流程
│
├── Knowledge
│   ├── Devices
│   ├── Manuals
│   ├── FAQ
│   └── Standards
│
├── Source Viewer
│
└── Admin
    ├── Documents
    ├── Versions
    ├── Parsing
    └── Feedback
```

---

# 18. MVP 页面设计

## Page 1｜Ask

顶部：

# H2 Manual Copilot

输入框：

> 输入设备问题、报警代码或操作步骤

快捷入口：

- 启动流程
- 报警代码
- 安全要求
- 维护流程
- 参数查询

---

# 19. Page 2｜Answer Workspace

建议采用三栏结构：

```text
左栏
会话 / 设备

中栏
AI Answer

右栏
Evidence
```

中间答案：

### Answer

### Recommended Checks

### Safety Note

右侧：

### Evidence

```text
Maintenance Manual
Version 2.1
Page 127
```

---

# 20. Page 3｜Source Viewer

展示：

- PDF；
- 对应页面；
- 高亮引用区域；
- 页码；
- 文档版本；
- 发布时间；
- 来源。

---

# 21. Page 4｜Knowledge Library

列表字段：

| 字段 | 内容 |
|---|---|
| Document | 文档名 |
| Device | 对应设备 |
| Type | Manual / FAQ / Safety |
| Version | 文档版本 |
| Language | 中文 / English |
| Status | Active / Superseded |
| Trust | Official / Internal / Reference |

---

# 22. 功能优先级

采用：

- P0：必须完成；
- P1：比赛加分；
- P2：后续企业化。

---

# 23. P0 功能

## FR-001｜知识文档管理

支持：

- PDF 上传；
- 文档列表；
- 文档状态；
- 设备绑定；
- 版本字段；
- 文档语言；
- 文档类型。

### 验收

上传文档后能够：

```text
UPLOAD
→
PROCESSING
→
READY
```

---

# 24. FR-002｜自然语言问答

用户可以输入：

> 如何执行启动前检查？

系统返回：

- 答案；
- 信息来源；
- 相关页码。

---

# 25. FR-003｜Source Citation

每个回答至少展示：

- Document；
- Version；
- Page；
- Relevant excerpt。

AWS Bedrock Knowledge Bases 的 RAG API 本身就将 Citation 设计为“生成内容片段与知识库来源之间的关联对象”，说明 citation/grounding 已经属于企业级知识 AI 的基础产品模式，而不是额外装饰。

---

# 26. FR-004｜错误代码检索

例如：

```text
E104
```

优先进行：

> exact / lexical search

而不是纯语义搜索。

返回：

- Error Name；
- Explanation；
- Related Section；
- Suggested Checks；
- Source。

---

# 27. FR-005｜设备过滤

用户必须能够指定：

```text
Device
Model
Version
```

避免：

> A 型设备资料回答 B 型设备。

---

# 28. FR-006｜资料不足处理

如果检索不到可靠证据：

必须返回：

> **当前知识库中没有足够证据可靠回答此问题。**

随后展示：

- 最相关资料；
- 推荐检索关键词。

禁止编造答案。

---

# 29. FR-007｜Evidence Viewer

点击 citation：

直接跳转至：

> PDF 对应页面。

---

# 30. FR-008｜安全提示

涉及：

- 压力；
- 氢气泄漏；
- 电气；
- 联锁；
- 紧急停机；
- 维修；

等操作时增加：

### Safety Notice

> 以下信息用于文档查询与操作辅助。实际设备操作应以制造商最新版正式手册、企业 SOP 和具备相应资质人员判断为准。

---

# 31. FR-009｜反馈

答案下方：

👍 Helpful

👎 Incorrect

🚩 Safety concern

用户可以选择：

- 错误答案；
- 来源不相关；
- 版本错误；
- 信息过时；
- 安全风险。

---

# 32. P1 功能

## FR-101｜中英文双语

支持：

```text
中文 Query
↓
英文文档 Retrieval
↓
中文 Answer
↓
英文 Evidence
```

---

# 33. FR-102｜Error Code Quick Mode

首页提供独立入口：

```text
Enter error code
[E104          ]
```

这会成为 Demo 的视觉亮点。

---

# 34. FR-103｜Recommended Questions

根据当前设备提供：

- Startup checklist
- Maintenance
- Safety
- Error codes
- Specifications

---

# 35. FR-104｜文档版本管理

状态：

```text
DRAFT
ACTIVE
SUPERSEDED
ARCHIVED
```

默认检索：

> ACTIVE。

---

# 36. FR-105｜来源可信等级

```text
Level A
Manufacturer official

Level B
Enterprise internal

Level C
Industry standard

Level D
Reference
```

AI 优先使用更高可信来源。

---

# 37. P2 功能

后续可以增加：

### Equipment Knowledge Graph

```text
Device
├── Component
├── Error Code
├── Procedure
├── Parameter
└── Document
```

---

### Maintenance Work Order

与企业工单系统连接。

---

### Live Device Context

读取：

- error log；
- sensor；
- PLC telemetry。

但依然：

> **Read Only First。**

---

# 38. 核心 AI 行为规范

## A1｜回答必须 Grounded

凡属于：

- 参数；
- 操作步骤；
- 故障代码；
- 安全要求；

的事实陈述，必须对应知识库证据。

---

# 39. A2｜不得用模型常识补全关键工业事实

例如资料只写：

> 检查冷却系统。

模型不得自行变成：

> 将水温调整至 35°C。

除非来源明确给出 35°C。

---

# 40. A3｜不得制造 Citation

Citation 必须来源于实际 Retrieval Result。

这一点也应进入自动安全测试。Promptfoo 当前专门提供 RAG Source Attribution 测试，用于识别系统是否虚构文档、引用或来源。

---

# 41. A4｜区分“资料原文”与“AI 总结”

UI 中建议明确：

**AI Summary**

与：

**Source**

避免用户误认为 AI 输出就是手册原文。

---

# 42. A5｜风险信息必须保留原单位

例如：

- MPa；
- bar；
- °C；
- Nm；
- V；
- A。

不得未经明确规则自动换算关键工业参数。

---

# 43. A6｜版本冲突必须提醒

如果：

```text
Manual V1 → 1.5 MPa
Manual V2 → 1.2 MPa
```

系统不得任选一个回答。

必须：

> 检测到不同版本资料存在冲突，请确认当前设备版本。

---

# 44. 安全设计

本项目建议参考 NIST AI RMF Generative AI Profile，将风险治理纳入产品生命周期，而不是上线前临时加一个免责声明；NIST 的 GenAI Profile 明确用于帮助组织识别生成式 AI 特有风险并规划对应治理措施。

---

# 45. 氢能领域安全边界

2026 年当前应优先关注：

- ISO 22734-1:2025：水电解制氢系统安全；
- ISO/TS 15916:2026：氢系统基础安全考虑；
- ISO 19880-1:2020：加氢站的一般设计、运行、检查和维护要求。

国内可参考当前仍为现行状态的：

- GB/T 37562-2019《压力型水电解制氢系统技术条件》；
- GB/T 37563-2019《压力型水电解制氢系统安全要求》。

需要特别注意：

> ISO 22734:2019 已撤销并被 ISO 22734-1:2025 替代，因此知识库必须具备标准版本和失效状态管理，不能简单“上传以后永久有效”。

---

# 46. 标准内容版权原则

产品不得默认抓取、复制或再分发受版权保护的完整标准文件。

企业生产版只能处理：

1. 企业拥有合法使用权的资料；
2. 企业内部文件；
3. 合法公开资料；
4. 已获得授权的标准文本。

公开演示建议优先使用：

- 自建 Sample Manual；
- 明确公开的厂商资料；
- 合法公开 FAQ；
- 标准公开 metadata / abstract。

---

# 47. 数据策略

MVP 不追求：

> 1000 份文档。

而追求：

> **5～15 份质量高、结构清楚、能够覆盖 Demo 场景的文档。**

推荐构成：

```text
3 × Operation Manual
2 × Maintenance Manual
1 × Safety Guide
2 × FAQ
1 × Error Code Reference
```

---

# 48. Demo 数据集

建议人为构建：

## Device A

PEM Electrolyzer HX-100

### Documents

- HX-100 Operation Manual V2.1
- HX-100 Maintenance Manual V2.1
- HX-100 Safety Guide
- HX-100 Error Codes

---

# 49. Demo 测试问题

预置至少 30 个问题。

例如：

### Easy

> HX-100 支持什么语言？

### Exact

> E104 是什么？

### Semantic

> 冷却系统异常应该检查什么？

### Cross-language

> 启动前要确认哪些 safety interlock？

### Version

> V1 和 V2 的启动压力一样吗？

### No Answer

> HX-100 的采购价格是多少？

---

# 50. 产品成功指标

MVP 不用虚构“节省 80% 时间”。

没有真实用户实验，就不要替未来用户编 KPI。

比赛阶段采用可以真实测量的指标。

---

## Metric 1｜Citation Coverage

定义：

> 有来源支持的关键事实 / 全部关键事实。

目标：

**≥95%**

---

# 51. Metric 2｜No-answer Accuracy

测试无法回答的问题。

目标：

> 系统应该拒绝时能够拒绝。

---

# 52. Metric 3｜Retrieval Recall@5

预先给测试问题标注正确文档。

要求：

> 正确 evidence 出现在前 5 个候选中。

---

# 53. Metric 4｜Faithfulness

RAGAS 将 Faithfulness 定义为“生成答案中的事实是否能够由检索上下文支持”，Context Precision 则衡量相关 chunks 是否能排在检索结果前部。这两项非常适合本项目。

---

# 54. Metric 5｜Answer Latency

MVP 目标：

P50：

≤ 4 秒

P95：

≤ 8 秒

不把 PDF 解析时间算入问答延迟。

---

# 55. 产品级非功能需求

## Availability

比赛：

> Demo 流程稳定优先。

生产：

≥99.9% 月度可用性目标。

---

## Accessibility

至少支持：

- 键盘操作；
- 清晰字体；
- 高对比度；
- 不只靠颜色表达状态。

---

# 56. 隐私要求

默认：

- 不将企业文件公开；
- 不允许不同租户相互检索；
- 不在日志中记录完整机密文档；
- API Key 不进入前端。

若未来处理用户个人信息，应遵循个人信息处理的合法、正当、必要与最小化原则。我国《个人信息保护法》要求个人信息处理应有明确合理目的，并与处理目的直接相关。

---

# 57. MVP 不需要的东西

以下内容比赛阶段全部砍掉：

- Kubernetes；
- 多 Agent；
- Knowledge Graph；
- Fine-tuning；
- 自动 PLC；
- 企业 SSO；
- Elasticsearch；
- Kafka；
- 微服务；
- 复杂工作流引擎。

理由：

> 它们不能帮助三天内证明核心价值。

---

# 58. MVP Definition of Done

比赛提交前必须满足：

- [ ] 至少 5 份知识资料成功解析
- [ ] 文档可查看
- [ ] 能回答自然语言问题
- [ ] 能检索 Error Code
- [ ] 每个重要答案有 Citation
- [ ] Citation 可以打开对应页面
- [ ] 支持中英文 Query
- [ ] 没有资料时会明确拒答
- [ ] 页面存在 Loading / Error / Empty State
- [ ] Demo 环境可以稳定部署
- [ ] 至少 30 条 Golden Test
- [ ] README 可以从零运行项目

---

# 59. 比赛 Demo Golden Path

总演示控制在约 3 分钟。

---

## Scene 1｜问题

主持人：

> 一线工程师面对几百页设备资料，出现 E104 后如何最快找到答案？

---

## Scene 2｜输入

```text
E104
```

---

## Scene 3｜AI

展示：

### E104 — Cooling System Temperature Abnormal

可能相关检查：

1. Cooling loop；
2. circulation pump；
3. temperature sensor。

---

## Scene 4｜Evidence

右边：

```text
HX-100 Maintenance Manual
Version 2.1
Page 127
```

点击。

PDF 自动打开 Page 127。

---

# 60. Scene 5｜证明安全边界

用户：

> 那我应该把压力直接调到多少？

系统因为资料不足：

> 当前文档不足以可靠确定该操作参数，请确认设备版本或参考制造商正式操作程序。

这一幕很重要。

因为它证明：

> **这个产品不仅会回答，也知道什么时候不应该回答。**

---

# 61. Scene 6｜跨语言

问：

> 启动之前安全联锁需要检查什么？

检索英文 Manual。

中文回答。

展示英文 Source。

---

# 62. 核心差异化

| 普通 RAG | H2 Manual Copilot |
|---|---|
| PDF Chat | Equipment-oriented |
| Semantic Search | Hybrid Retrieval |
| 一个知识库 | Device / Version scoped |
| 有答案就返回 | 支持 Abstention |
| Citation 可选 | Citation mandatory |
| 文档没有状态 | Active / Superseded |
| 普通知识问答 | Error Code 快速路由 |
| AI 是主角 | Evidence 是主角 |

---

# 63. 同类产品参考

## Siemens Industrial Copilot

西门子正在把自然语言、工业工程信息和故障排查结合到 Industrial Copilot，并允许工业助手访问 manuals、work instructions、technical and safety specifications、process/equipment checklists、error logs 等内容。

**本项目借鉴：**

- 工业场景；
- Troubleshooting；
- Manual-first；
- Context-specific assistance。

---

## Microsoft Copilot Studio

Copilot Studio 当前支持配置多个知识源，并允许将知识来源标记为 official source，以此作为 agent grounding 的知识基础。

**本项目借鉴：**

> Source governance。

---

## Amazon Bedrock Knowledge Bases

Bedrock Knowledge Bases 将企业数据接入 RAG，并通过 Retrieve & Generate 返回知识库 grounded response 和 citations。

**本项目借鉴：**

> Retrieval + Generation + Citation。

---

## IBM watsonx Assistant

IBM 将 retrieval 与企业知识文档结合，使生成答案基于企业特定信息，而不是仅依赖模型内部知识。

---

# 64. H2 Manual Copilot 的真正差异

我们不试图复制这些平台。

我们只解决一个窄问题：

> **工业现场“问设备手册”这一条链路。**

因此核心资产不是聊天框。

而是：

```text
Document Governance
+
Hybrid Retrieval
+
Version Awareness
+
Evidence
+
Safety
```

---

# 65. 路线图

## V0.1｜Hackathon

```text
PDF
↓
Question
↓
Answer
↓
Citation
```

---

## V0.2

增加：

- Error Code；
- Version；
- Multilingual；
- Evaluation。

---

## V0.5｜PoC

增加：

- 企业账号；
- RBAC；
- 审计；
- 文档同步；
- 管理后台；
- LLM observability。

---

## V1.0｜Production

增加：

```text
Enterprise Knowledge
↓
Equipment Context
↓
Maintenance Copilot
↓
Work Order Integration
```

但依然保持：

> **AI 不直接控制工业设备。**

---

# 66. 风险矩阵

| 风险 | 概率 | 影响 | 处理 |
|---|---:|---:|---|
| PDF 解析错误 | 中 | 高 | Source Viewer + Parser fallback |
| AI 幻觉 | 中 | 高 | Grounded generation |
| 错误版本 | 中 | 极高 | Version filter |
| Citation 错误 | 中 | 高 | Citation verifier |
| Prompt Injection | 中 | 高 | 文档隔离 + 系统规则 |
| 旧标准 | 中 | 高 | lifecycle status |
| 数据不足 | 高 | 中 | Abstention |
| Demo 超范围 | 高 | 高 | P0 Freeze |

---

# 67. 产品最终定义

H2 Manual Copilot 不应该被描述成：

> **氢能知识库 Chatbot。**

正式定义应该是：

> **H2 Manual Copilot 是一个面向氢能设备技术资料的 Evidence-grounded Industrial Knowledge Copilot。它通过设备与版本感知检索，将操作手册、维护资料、故障代码和安全文档转化为可以自然语言查询、可回溯原始证据、能够在证据不足时主动拒答的智能知识服务。**

---

# 68. 产品核心公式

最终产品逻辑可以归结为：

> **Question → Evidence → Answer → Action Support**

而不是：

> Question → LLM → Answer。

这个差别，就是本项目从“又一个 RAG Demo”走向真正工业 AI 产品的关键。