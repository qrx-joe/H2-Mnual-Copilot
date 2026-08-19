"""进程内滑动窗口限流（技术规范 §108：query RPM）。

MVP 单进程语义；生产阶段替换 Redis 限流（§77），接口保持不变。
"""

import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._hits: dict[str, deque[float]] = {}

    def allow(self, key: str, now: float | None = None) -> bool:
        """记录一次请求并判定是否放行。key 通常为客户端 IP。"""
        current = now if now is not None else time.monotonic()
        window = self._hits.setdefault(key, deque())
        while window and current - window[0] > 60.0:
            window.popleft()
        if len(window) >= self.max_per_minute:
            return False
        window.append(current)
        return True


_limiter = SlidingWindowLimiter(60)


def get_limiter() -> SlidingWindowLimiter:
    """按配置刷新容量（配置只在进程内读取一次；测试可直接改 max_per_minute）。"""
    from h2copilot.core.config import get_settings

    _limiter.max_per_minute = get_settings().query_rpm
    return _limiter
