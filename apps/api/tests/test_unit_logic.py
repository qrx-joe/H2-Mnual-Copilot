"""纯逻辑单元测试：intent 路由、RRF、抽取式生成（无 IO，毫秒级）。"""

from h2copilot.domain.enums import EvidenceStatus, QueryIntent
from h2copilot.llm.generator import ExtractiveGenerator
from h2copilot.llm.providers import ChunkRef
from h2copilot.retrieval.search import classify_intent, reciprocal_rank_fusion


def _ref(cid: str, title: str = "Manual", version: str = "2.1") -> ChunkRef:
    return ChunkRef(
        chunk_id=cid,
        document_title=title,
        version=version,
        page_number=1,
        content=(
            "E104 cooling system temperature abnormal. Inspect coolant level and "
            "pump. Keep hydrogen leak interlocks engaged."
        ),
        trust_level="A_OFFICIAL",
    )


# ---------- intent ----------


def test_intent_error_code() -> None:
    assert classify_intent("E104") is QueryIntent.ERROR_CODE
    assert classify_intent("e104 ") is QueryIntent.ERROR_CODE  # 规范化后命中
    assert classify_intent("HX-100") is QueryIntent.ERROR_CODE  # 型号走同一词法路径


def test_intent_natural_language() -> None:
    assert classify_intent("冷却系统异常怎么办") is QueryIntent.TROUBLESHOOTING
    assert classify_intent("正常工作压力是多少") is QueryIntent.PARAMETER
    assert classify_intent("启动前检查步骤") is QueryIntent.PROCEDURE
    assert classify_intent("你好") is QueryIntent.GENERAL


# ---------- RRF ----------


def test_rrf_prefers_dual_path_hits() -> None:
    lexical = [_ref("a"), _ref("b"), _ref("c")]
    dense = [_ref("b"), _ref("d"), _ref("a")]
    fused = reciprocal_rank_fusion(lexical, dense)
    ids = [c.chunk_id for c in fused]
    assert ids[0] == "b"  # 双路第一/榜首
    assert ids.index("a") < ids.index("c")
    assert sorted(ids) == ["a", "b", "c", "d"]  # 无重复、无遗漏


# ---------- 生成替身 ----------


async def test_generator_abstains_without_evidence() -> None:
    gen = ExtractiveGenerator()
    result = await gen.generate("HX-100 的采购价格是多少？", [])
    assert result.abstain is True
    assert result.evidence_status is EvidenceStatus.INSUFFICIENT


async def test_generator_flags_version_conflict() -> None:
    gen = ExtractiveGenerator()
    evidence = [
        _ref("a", "HX-100 Operation Manual", "2.1"),
        _ref("b", "HX-100 Operation Manual", "1.9"),
    ]
    result = await gen.generate("正常工作压力是多少？", evidence)
    assert result.abstain is True
    assert result.evidence_status is EvidenceStatus.CONFLICTING
    assert "版本" in result.answer


async def test_generator_extractive_answer_with_safety() -> None:
    gen = ExtractiveGenerator()
    evidence = [_ref("a"), _ref("b")]
    result = await gen.generate("E104 是什么？", evidence)
    assert result.abstain is False
    # 抽取式约束（A1/A2）：答案必须是证据原文的子串拼接
    assert "cooling system temperature abnormal" in result.answer
    assert result.safety_notice is not None  # 命中 interlock/hydrogen leak 提示
    assert result.evidence_status is EvidenceStatus.SUFFICIENT


async def test_generator_partial_with_single_source() -> None:
    gen = ExtractiveGenerator()
    result = await gen.generate("E104", [_ref("only")])
    assert result.evidence_status is EvidenceStatus.PARTIAL
