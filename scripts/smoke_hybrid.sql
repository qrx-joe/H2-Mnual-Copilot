-- Phase 3 冒烟（V-3）：验证 pgvector 扩展可用 + hybrid 检索 SQL 形态可执行。
-- 这是"扩展与语法级"验证；真实数据量下的性能证据在 Phase 5 评测产出。
-- 运行方式见 docs/engineering-baseline.md（docker exec psql）。

CREATE EXTENSION IF NOT EXISTS vector;

-- 扩展版本
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- 模拟 chunks 表的关键列：tsvector（词法）+ vector（语义），以及版本隔离列（ADR-0004）
CREATE TEMP TABLE smoke_chunks (
    id                   int PRIMARY KEY,
    document_version_id  text NOT NULL,
    is_current           boolean NOT NULL,
    content              text NOT NULL,
    tsv                  tsvector,
    embedding            vector(3)
);

INSERT INTO smoke_chunks VALUES
    (1, 'maint-v2.1', true,  'E104 cooling system temperature abnormal inspect coolant', to_tsvector('english', 'E104 cooling system temperature abnormal inspect coolant'), '[0.9, 0.1, 0.1]'),
    (2, 'maint-v2.1', true,  'feed water flow low check pump',                          to_tsvector('english', 'feed water flow low check pump'),                          '[0.1, 0.9, 0.1]'),
    (3, 'maint-v1.9', false, 'E104 legacy description superseded',                      to_tsvector('english', 'E104 legacy description superseded'),                      '[0.9, 0.1, 0.2]');

-- 词法路：错误代码精确匹配（E104），且默认域过滤掉历史版本（is_current）
SELECT id, content
FROM smoke_chunks
WHERE tsv @@ to_tsquery('english', 'E104')
  AND is_current
ORDER BY ts_rank(tsv, to_tsquery('english', 'E104')) DESC;

-- 向量路：语义近邻（cosine 距离），同样带版本域过滤
SELECT id, content, embedding <=> '[0.9, 0.1, 0.0]' AS cosine_distance
FROM smoke_chunks
WHERE is_current
ORDER BY embedding <=> '[0.9, 0.1, 0.0]'
LIMIT 2;

-- 混合形态：两路各自 rank 后在应用层 RRF 融合（V-1 已验证算法）；
-- 此处仅演示两路 SQL 均可独立执行并返回一致过滤语义
SELECT count(*) AS current_version_rows FROM smoke_chunks WHERE is_current;
