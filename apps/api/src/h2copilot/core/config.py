"""集中配置（技术规范 §96）。

约束：检索参数等运行配置只允许出现在这里；
禁止把 top_k 之类的数值散落在多个文件中。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。真实值来自环境变量或 .env（.env 不入库）。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "h2copilot-api"

    # 基线阶段允许为空：/health 与 SSE 桩不依赖数据库和模型。
    # Phase 5 接入真实链路时，以下字段将改为必填，缺失时启动即报可诊断错误。
    database_url: str = ""
    # ADR-0007：留空 = LocalFS（data/storage/）；生产填 S3/MinIO 地址换适配器
    object_storage_url: str = ""
    object_storage_bucket: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    embedding_provider: str = ""
    embedding_model: str = ""
    rerank_provider: str = ""
    rerank_model: str = ""
    admin_password: str = ""

    # 检索参数（技术规范 §96 默认值；rerank_candidates 对应 §40 的 Top30 截断）
    retrieval_dense_top_k: int = 20
    retrieval_lexical_top_k: int = 20
    rerank_top_k: int = 6
    rerank_candidates: int = 30
    # 向量路相似度阈值（余弦距离上限）：无阈值时 ORDER BY 距离必然返回 k 条"最近邻"，
    # 无关查询会被当作有证据——拒答路径（FR-006）依赖此过滤。
    # 0.95 适配 FakeEmbedding（无共享词 ≈ 正交，距离 ≈ 1）；真实 embedding 需重标定。
    retrieval_dense_max_distance: float = 0.95

    # Phase 6 横切边界（技术规范 §74/§106/§108）
    query_timeout_seconds: float = 8.0  # 全链路预算上限（P95 目标同值）
    query_rpm: int = 60  # 进程内限流（每分钟查询数）；生产换 Redis 限流（§77）


@lru_cache
def get_settings() -> Settings:
    """进程内单例。测试如需覆盖环境变量，先调用 get_settings.cache_clear()。"""
    return Settings()
