"""健康检查路由。

/health 是工程基线的最小可检查入口（Phase 3 验收）：
不依赖数据库与模型，用于确认进程与配置加载正常。
"""

from fastapi import APIRouter, Request

from h2copilot.core.config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        # db_configured 只说明"配置里填了连接串"，不代表数据库可达；
        # 真实连通性检查在 Phase 5 数据层接入后提供独立探针。
        "db_configured": bool(settings.database_url),
        "request_id": getattr(request.state, "request_id", None),
    }
