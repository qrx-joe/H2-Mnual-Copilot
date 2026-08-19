"""Provider 协议与实现（契约 §4；技术规范 §22/§28/§40/§52）。

证据边界（执行方案 Phase 5 约定）：
- Fake* 是确定性测试替身，用于本地贯通全链路；它们的输出**不构成**
  真实模型集成证据。真实 DashScope/OpenAI-compatible 实现等 Q-010
  凭据到位后在同协议下接入，应用层零改动（§53 provider adapter）。
"""

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from h2copilot.domain.models import EMBEDDING_DIM

# ---------- 协议 ----------

class DocumentParser(Protocol):
    name: str

    async def parse(self, file_path: Path) -> "ParsedDocument": ...


class EmbeddingProvider(Protocol):
    name: str

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...


class RerankProvider(Protocol):
    name: str

    async def rerank(
        self, query: str, candidates: Sequence["ChunkRef"], limit: int
    ) -> list["ChunkRef"]: ...


@dataclass
class ChunkRef:
    """检索候选的轻量引用：足够生成引用与排序，不携带全文。"""

    chunk_id: str
    document_title: str
    version: str
    page_number: int
    content: str
    trust_level: str


@dataclass
class ParsedPage:
    page_number: int  # 1 起算（V-2 验证结论：metadata.page_number）
    text: str


@dataclass
class ParsedDocument:
    pages: list[ParsedPage] = field(default_factory=list)


# ---------- Fake 实现（确定性，可重复测试） ----------

class FakeEmbedding:
    """确定性哈希向量：同一文本恒得同一向量，且与"相似文本"余弦更高。

    构造：把文本按 64 个桶做字符 n-gram 计数再归一化——词面重叠的文本
    向量夹角更小，使 dense 检索路径在测试中具备语义合理性（非随机）。
    停用词过滤：eval 报告显示，the/is 等常见词的单 token 重叠会把无关
    查询的余弦距离拉进阈值内（no-answer 准确率 28.6%），过滤后恢复可分性。
    """

    name = "fake-embedding-v1"

    # 高频功能词：不参与哈希（真实 embedding 自带语义权重，无需此表）
    _STOPWORDS = frozenset(
        "the a an is are was were be been what how why when where who which "
        "and or of to in on for with by from as at it its this that these those "
        "do does did not no yes about into over under before after during "
        "范围 什么 怎么 哪些 是 的 了 吗 请 在 和 与 对 从 被".split()
    )

    def _vector(self, text: str) -> list[float]:
        """每 token 占 3 个哈希位：单桶碰撞（1/1024）会让无关查询虚增相似度
        （eval 实测 purchase/price 与 pressure 撞桶导致 cos 0.26），三位联合
        把碰撞贡献压到 ≈0.05，低于拒答阈值。"""
        vec = [0.0] * EMBEDDING_DIM
        tokens = [
            t for t in text.lower().split()
            if t.strip(".,;:!?()[]") and t.strip(".,;:!?()[]") not in self._STOPWORDS
        ]
        for tok in tokens:
            digest = hashlib.sha256(tok.encode()).digest()
            for offset in (0, 4, 8):
                bucket = int.from_bytes(digest[offset : offset + 4], "big") % EMBEDDING_DIM
                vec[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class FakeReranker:
    """恒等重排：保持融合顺序，仅截断到 limit。真实 rerank 等凭据接入。"""

    name = "fake-rerank-v1"

    async def rerank(
        self, query: str, candidates: Sequence[ChunkRef], limit: int
    ) -> list[ChunkRef]:
        return list(candidates[:limit])


def get_embedding_provider(provider: str) -> EmbeddingProvider:
    """工厂：按配置选择实现；未知实现立即失败（fail fast，不静默降级）。"""
    if provider in ("", "fake"):
        return FakeEmbedding()
    raise RuntimeError(f"未知 EMBEDDING_PROVIDER={provider}；真实 DashScope 实现待 Q-010 凭据接入")


def get_rerank_provider(provider: str) -> RerankProvider:
    if provider in ("", "fake"):
        return FakeReranker()
    raise RuntimeError(f"未知 RERANK_PROVIDER={provider}；真实实现待 Q-010 凭据接入")
