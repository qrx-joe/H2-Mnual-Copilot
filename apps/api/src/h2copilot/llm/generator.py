"""生成服务（FakeLLM，抽取式）——Phase 5 测试替身，Phase 6+ 换真实 LLM。

行为契约（对应 PRD A1–A6 / 技术规范 §43–§47）：
- 只基于检索证据生成（A1）：答案句子全部摘自 chunk 原文；
- 证据不足 → abstain（FR-006）；
- 版本冲突 → CONFLICTING + 提示确认版本（A6），不任选其一；
- 结构化输出与契约 §1.1 Answer 一一对应。
"""

from dataclasses import dataclass, field

from h2copilot.domain.enums import AbstainReason, EvidenceStatus
from h2copilot.llm.providers import ChunkRef


@dataclass
class GeneratedAnswer:
    answer: str
    steps: list[str] = field(default_factory=list)
    safety_notice: str | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.SUFFICIENT
    abstain: bool = False
    abstain_reason: AbstainReason | None = None
    used_chunks: list[ChunkRef] = field(default_factory=list)
    related_documents: list[str] = field(default_factory=list)
    suggested_keywords: list[str] = field(default_factory=list)


_SAFETY_HINTS = (
    "pressure",
    "压力",
    "hydrogen leak",
    "泄漏",
    "interlock",
    "联锁",
    "electrical",
    "电气",
)


def _first_sentences(text: str, limit: int = 3) -> list[str]:
    """按句号/换行切出前几句——抽取式摘录，不引入模型记忆（A2）。"""
    parts = [s.strip() for s in text.replace("\n", ". ").split(".") if len(s.strip()) > 8]
    return parts[:limit]


class ExtractiveGenerator:
    """确定性生成替身：answer/steps 全部来自证据文本。"""

    name = "fake-llm-extractive-v1"

    async def generate(self, query: str, evidence: list[ChunkRef]) -> GeneratedAnswer:
        if not evidence:
            return GeneratedAnswer(
                answer="当前知识库中没有足够证据可靠回答此问题。",
                evidence_status=EvidenceStatus.INSUFFICIENT,
                abstain=True,
                abstain_reason=AbstainReason.NO_RELIABLE_SOURCE,
                related_documents=[c.document_title for c in evidence],
                suggested_keywords=query.split()[:4],
            )

        # A6 版本冲突检测：同一文档不同版本同时进入证据集 → 不作答，要求确认版本
        by_doc: dict[str, set[str]] = {}
        for c in evidence:
            by_doc.setdefault(c.document_title, set()).add(c.version)
        conflicting = {t for t, vs in by_doc.items() if len(vs) > 1}
        if conflicting:
            titles = "、".join(sorted(conflicting))
            return GeneratedAnswer(
                answer=f"检测到不同版本资料存在冲突（{titles}），请确认当前设备使用的文档版本后再提问。",
                evidence_status=EvidenceStatus.CONFLICTING,
                abstain=True,
                abstain_reason=AbstainReason.CONFLICTING_VERSIONS,
                used_chunks=evidence,
            )

        top = evidence[0]
        sentences = _first_sentences(top.content)
        answer = " ".join(sentences) if sentences else top.content[:300]

        steps = [s for s in _first_sentences(evidence[1].content if len(evidence) > 1 else "", 3)]
        # 证据数量不足两个来源时降级为 PARTIAL（契约 evidence_status 语义）
        status = EvidenceStatus.SUFFICIENT if len(evidence) >= 2 else EvidenceStatus.PARTIAL

        joined = " ".join(c.content.lower() for c in evidence)
        safety = (
            "以下信息用于文档查询与操作辅助。实际设备操作应以制造商最新版正式手册、"
            "企业 SOP 和具备相应资质人员判断为准。"
            if any(h in joined or h in query.lower() for h in _SAFETY_HINTS)
            else None
        )

        return GeneratedAnswer(
            answer=answer,
            steps=steps,
            safety_notice=safety,
            evidence_status=status,
            used_chunks=evidence[:6],
        )
