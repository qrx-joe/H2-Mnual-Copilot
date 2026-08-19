# ADR-0007 MVP 对象存储使用本地文件系统适配器

- 状态：已接受
- 日期：2026-08-19
- 来源：技术规范 §5（Object Storage: S3/MinIO）、§100（compose 仅 web/api/postgres）

## 背景

技术规范技术栈要求 S3/MinIO 对象存储，但 docker compose MVP 服务清单只有 web/api/postgres 三个服务。原始 PDF 文件需要一个明确的归属位置（Phase 2 验收门要求主链路无未决数据归属）。

## 决策

1. 定义 ObjectStorage 协议（put/get/delete/exists），MVP 实现 LocalFSStorage：文件存于容器卷挂载目录（如 `./data/storage`，git 忽略），以 storage_key 寻址。
2. DocumentVersion.storage_key 只存逻辑键，不感知底层是本地盘还是 S3。
3. 生产演进时实现 S3Storage 适配器替换，业务层与数据层不改动；知识索引可从原始文件重建（技术规范 §102）。

## 后果

- MVP 不引入 MinIO 服务，compose 保持三服务。
- 备份策略 MVP 阶段为"备份 data 卷 + Postgres"；生产切换 S3 versioning（技术规范 §102）。
- 本地卷需在 .gitignore 排除（Phase 3 工程基线落实）。
