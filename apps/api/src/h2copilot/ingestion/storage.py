"""对象存储：LocalFS 实现（ADR-0007）。生产替换 S3 适配器，业务层不变。"""

from pathlib import Path

from h2copilot.core.config import get_settings


class LocalFSStorage:
    """以 data/storage/<key> 寻址；目录整体被 .gitignore 排除。"""

    def __init__(self, root: Path | None = None) -> None:
        # root 参数便于测试注入临时目录
        self.root = root or Path(get_settings().object_storage_url or "data/storage")
        self.root.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    async def exists(self, key: str) -> bool:
        return (self.root / key).exists()
