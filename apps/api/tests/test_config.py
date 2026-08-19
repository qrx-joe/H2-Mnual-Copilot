"""配置加载与检索参数默认值（技术规范 §96）。"""

from h2copilot.core.config import Settings, get_settings


def test_defaults_match_tech_spec() -> None:
    s = Settings()
    assert s.retrieval_dense_top_k == 20
    assert s.retrieval_lexical_top_k == 20
    assert s.rerank_top_k == 6
    assert s.rerank_candidates == 30


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("RERANK_TOP_K", "8")
    s = Settings()
    assert s.rerank_top_k == 8


def test_get_settings_is_cached_and_clearable(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("RERANK_TOP_K", "8")
    assert get_settings().rerank_top_k == 8
    assert get_settings() is get_settings()  # 单例
    get_settings.cache_clear()
    monkeypatch.delenv("RERANK_TOP_K")
    assert get_settings().rerank_top_k == 6  # 回到默认（.env 不含该项）
    get_settings.cache_clear()
