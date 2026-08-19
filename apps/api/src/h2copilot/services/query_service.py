"""问答编排（系统设计 §3.1）：intent → 过滤 → 双路检索 → RRF → 重排 → 生成 → 校验。

顺序不可随意改变（技术规范 §41）：rerank 只处理有限候选以控成本；
返回的 Chunk 携带完整 provenance，引用永远来自真实检索结果（A3）。
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass

from h2copilot.core.config import get_settings
from h2copilot.domain.enums import EvidenceStatus
from h2copilot.llm.generator import ExtractiveGenerator, GeneratedAnswer
from h2copilot.llm.providers import (
    get_embedding_provider,
    get_rerank_provider,
)
from h2copilot.retrieval.search import classify_intent, reciprocal_rank_fusion, search_chunks

logger = logging.getLogger("h2copilot.query")


@dataclass
class QueryResult:
    request_id: str
    intent: str
    retrieval_ms: int
    evidence_status: EvidenceStatus
    answer: GeneratedAnswer
    citations: list[dict]
    chunk_ids: list[str]
    model_alias: str = ""


class QueryService:
    def __init__(self) -> None:
        s = get_settings()
        self._embedder = get_embedding_provider(s.embedding_provider)
        self._reranker = get_rerank_provider(s.rerank_provider)
        self._generator = ExtractiveGenerator()

    async def run(self, query: str, device_id: str, version: str | None) -> QueryResult:
        request_id = uuid.uuid4().hex[:12]
        intent = classify_intent(query)

        started = time.perf_counter()
        query_vec = await self._embedder.embed_query(query)
        # ERROR_CODE 意图词法路加权：双路都查，但词法 top_k 提高（§38 exact lexical 优先）
        s = get_settings()
        lexical_k = s.retrieval_lexical_top_k * (2 if intent == "ERROR_CODE" else 1)
        lexical, dense = await search_chunks(
            query=query,
            query_embedding=query_vec,
            device_id=device_id,
            version=version,
            lexical_top_k=lexical_k,
            dense_top_k=s.retrieval_dense_top_k,
        )
        fused = reciprocal_rank_fusion(lexical, dense)[: s.rerank_candidates]
        evidence = await self._reranker.rerank(query, fused, s.rerank_top_k)
        retrieval_ms = int((time.perf_counter() - started) * 1000)

        generated = await self._generator.generate(query, evidence)

        # 引用对象只引用"实际用于回答"的 chunk（A3：不制造引用）
        citations = [
            {
                "citation_id": uuid.uuid4().hex[:12],
                "chunk_id": c.chunk_id,
                "document_title": c.document_title,
                "version": c.version,
                "page": c.page_number,
                "excerpt": c.content[:200],
                "support_type": "QUOTE",
            }
            for c in generated.used_chunks
        ]

        # AI 结构化日志（技术规范 §69）：只记 ID/指标/元数据，不记查询正文与上下文（§73）
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "stage": "query",
                    "intent": intent.value,
                    "retrieval_ms": retrieval_ms,
                    "chunks": len(evidence),
                    "evidence_status": generated.evidence_status.value,
                    "abstain": generated.abstain,
                    "model_alias": self._generator.name,
                    "embedder": self._embedder.name,
                    "reranker": self._reranker.name,
                },
                ensure_ascii=False,
            )
        )

        return QueryResult(
            request_id=request_id,
            intent=intent.value,
            retrieval_ms=retrieval_ms,
            evidence_status=generated.evidence_status,
            answer=generated,
            citations=citations,
            chunk_ids=[c.chunk_id for c in evidence],
            model_alias=self._generator.name,
        )
