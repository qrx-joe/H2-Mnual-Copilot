"""领域枚举（契约 docs/architecture/contracts.md §2–§3）。

单个来源定义，避免字符串字面量散落各层。
"""

import enum


class ProcessingStatus(str, enum.Enum):
    """文档处理状态机（技术规范 §19）：UPLOADED→…→READY | FAILED。"""

    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    INDEXING = "INDEXING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    FAILED = "FAILED"


class PublishStatus(str, enum.Enum):
    """文档发布状态（技术规范 §19）：DRAFT→ACTIVE→SUPERSEDED→ARCHIVED。"""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class DocumentType(str, enum.Enum):
    OPERATION = "OPERATION"
    MAINTENANCE = "MAINTENANCE"
    SAFETY = "SAFETY"
    ERROR_CODES = "ERROR_CODES"
    FAQ = "FAQ"
    STANDARD = "STANDARD"


class TrustLevel(str, enum.Enum):
    """PRD §105：A 官方 > B 企业内部 > C 行业标准 > D 参考资料。"""

    A_OFFICIAL = "A_OFFICIAL"
    B_INTERNAL = "B_INTERNAL"
    C_STANDARD = "C_STANDARD"
    D_REFERENCE = "D_REFERENCE"


class EvidenceStatus(str, enum.Enum):
    """技术规范 §44 / ADR-0005：只有四态，无数值评分。"""

    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"


class QueryIntent(str, enum.Enum):
    """技术规范 §37。ERROR_CODE 决定精确词法优先路由。"""

    ERROR_CODE = "ERROR_CODE"
    PARAMETER = "PARAMETER"
    PROCEDURE = "PROCEDURE"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    GENERAL = "GENERAL"


class AbstainReason(str, enum.Enum):
    NO_RELIABLE_SOURCE = "NO_RELIABLE_SOURCE"
    CONFLICTING_VERSIONS = "CONFLICTING_VERSIONS"
