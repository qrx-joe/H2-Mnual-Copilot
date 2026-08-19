"""检索层：intent 路由、双路召回、RRF 融合（技术规范 §33–§41）。

RRF 与 regex 路由的算法行为已由 scratch/phase2/verify_logic.py 验证；
本模块是其在查询链路中的正式实现（独立可单测）。
"""

import re
from typing import Any

from sqlalchemy import text

from h2copilot.core.config import get_settings
from h2copilot.core.db import session_scope
from h2copilot.domain.enums import QueryIntent
from h2copilot.llm.providers import ChunkRef

RRF_K = 60
ERROR_CODE_RE = re.compile(r"^[A-Z]{1,4}[-_]?\d{2,6}$")


def classify_intent(query: str) -> QueryIntent:
    q = query.strip()
    if ERROR_CODE_RE.match(q.upper()):
        return QueryIntent.ERROR_CODE
    lowered = q.lower()
    if any(k in lowered for k in ("压力", "参数", "温度设定", "pressure", "parameter")):
        return QueryIntent.PARAMETER
    if any(
        k in lowered for k in ("步骤", "流程", "如何", "检查", "procedure", "how to", "checklist")
    ):
        return QueryIntent.PROCEDURE
    if any(k in lowered for k in ("故障", "报警", "排查", "异常", "alarm", "troubleshoot")):
        return QueryIntent.TROUBLESHOOTING
    return QueryIntent.GENERAL


def reciprocal_rank_fusion(*ranked_lists: list[ChunkRef]) -> list[ChunkRef]:
    """score = Σ 1/(k+rank)；稳定排序保证可重复测试。"""
    scores: dict[str, float] = {}
    by_id: dict[str, ChunkRef] = {}
    for ranked in ranked_lists:
        for rank, ref in enumerate(ranked, start=1):
            scores[ref.chunk_id] = scores.get(ref.chunk_id, 0.0) + 1.0 / (RRF_K + rank)
            by_id[ref.chunk_id] = ref
    return sorted(by_id.values(), key=lambda c: (-scores[c.chunk_id], c.chunk_id))


async def search_chunks(
    query: str,
    query_embedding: list[float],
    device_id: str,
    version: str | None,
    lexical_top_k: int,
    dense_top_k: int,
) -> tuple[list[ChunkRef], list[ChunkRef]]:
    """双路召回。检索域固定为 ACTIVE ∧ is_current（ADR-0004）；显式版本时放宽到该版本。"""

    # 版本过滤规则（ADR-0004）：未指定 → 只检索 current；指定 → 允许历史版本用于对比
    version_clause = (
        "AND dv.version = :version" if version else "AND dv.is_current"
    )
    base = f"""
        SELECT c.id::text, d.title, dv.version, c.page_number,
               c.section_path, c.content, d.trust_level::text AS trust_level
        FROM chunks c
        JOIN document_versions dv ON dv.id = c.document_version_id
        JOIN documents d ON d.id = dv.document_id
        WHERE d.status = 'ACTIVE' AND d.device_id = :device_id {version_clause}
    """

    lexical_sql = (
        base
        + """
        AND c.tsv @@ plainto_tsquery('simple', :q)
        ORDER BY ts_rank(c.tsv, plainto_tsquery('simple', :q)) DESC
        LIMIT :k
        """
    )
    dense_sql = (
        base
        + """
        AND (c.embedding <=> CAST(:vec AS vector)) < :max_dist
        ORDER BY c.embedding <=> CAST(:vec AS vector)
        LIMIT :k
        """
    )

    def to_ref(row: Any) -> ChunkRef:
        return ChunkRef(
            chunk_id=row[0],
            document_title=row[1],
            version=row[2],
            page_number=row[3],
            content=row[5],
            trust_level=row[6],
        )

    params_common = {"device_id": device_id, "version": version}
    max_dist = get_settings().retrieval_dense_max_distance
    async with session_scope() as session:
        lex_rows = (
            (
                await session.execute(
                    text(lexical_sql), {**params_common, "q": query, "k": lexical_top_k}
                )
            ).fetchall()
        )
        vec_str = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"
        dense_rows = (
            (
                await session.execute(
                    text(dense_sql),
                    {**params_common, "vec": vec_str, "k": dense_top_k, "max_dist": max_dist},
                )
            ).fetchall()
        )

    return [to_ref(r) for r in lex_rows], [to_ref(r) for r in dense_rows]
