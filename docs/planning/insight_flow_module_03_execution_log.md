# Insight Flow 模块 03 执行与验证记录

## 1. 目的

这份文档用于为模块 03 当前已完成的工作留下可追溯证据。

它回答四件事：

1. 模块 03 到底做了哪些事情
2. 这些事情是如何验证的
3. 已经验证通过的边界是什么
4. 还有哪些边界没有真正验证

这份文档是任务板之外的“执行证明”。

---

## 2. 当前范围

对应任务板：

- `M03-01 ~ M03-16`

当前状态：

- 模块 03 已整体推进到 `DONE`
- 但“DONE”不代表所有外部依赖都完成了真实联调
- 特别是第三方 fallback provider 仍然只完成了代码接入，没有真实凭证验证

任务板基线：

- [insight_flow_mvp_task_board.md](./insight_flow_mvp_task_board.md)

---

## 3. 模块 03 已落地能力

当前模块 03 已落地的能力包括：

### 3.1 输入入口

- `GET /sources`
- `POST /sources/rss`
- `GET /documents`
- `POST /documents/url`
- `POST /documents/manual-text`

### 3.2 抓取与标准化

- `POST /documents/{document_id}/normalize`

支持：

- URL 文档抓取与提取
- manual text 文档标准化

### 3.3 主处理链路

- `POST /documents/{document_id}/process`

处理步骤包括：

- normalize
- quality scoring
- dedup
- summary generation
- chunk rebuild
- summary embedding 写入

---

## 4. 本轮实际验证过的场景

## 4.1 场景 A：Source 创建验证

验证目标：

- `sources` 表可写入
- `/sources/rss` API 可用
- 日志可记录 `source_id`

验证方式：

- 通过 FastAPI `TestClient` 调用 `POST /sources/rss`

验证结果：

- 返回 `201`
- 成功生成 `source_id`
- `source_type = rss`
- `status = active`

示例结果摘要：

```text
source_status 201
source.created source_id=... source_type=rss feed_url=https://example.com/feed.xml
```

---

## 4.2 场景 B：URL 导入验证

验证目标：

- `documents` 可通过 URL 入口写入
- `canonical_url` 归一逻辑生效
- 基础冲突控制已接上

验证方式：

- 调用 `POST /documents/url`

验证结果：

- 返回 `201`
- 成功生成 `document_id`
- `ingest_type = url`
- `status = ingested`
- `canonical_url` 被写入

示例结果摘要：

```text
url_status 201
document.ingested document_id=... ingest_type=url canonical_url=https://example.com/
```

---

## 4.3 场景 C：手动文本导入验证

验证目标：

- `manual_text` 类型文档可写入
- `raw_content / cleaned_content` 初始入库逻辑生效

验证方式：

- 调用 `POST /documents/manual-text`

验证结果：

- 返回 `201`
- 成功生成 `document_id`
- `ingest_type = manual_text`
- `status = ingested`

示例结果摘要：

```text
manual_status 201
document.ingested document_id=... ingest_type=manual_text ...
```

---

## 4.4 场景 D：manual text 标准化验证

验证目标：

- `normalize_text()` 生效
- 手动文本可以进入 `normalized` 状态
- `content_hash` 会更新

验证方式：

1. 创建 manual text document
2. 调用 `POST /documents/{id}/normalize`

验证结果：

- 返回 `200`
- `status = normalized`
- `content_hash` 已更新
- 日志里可以看到：
  - `document.processing.started`
  - `document.normalize.completed`
  - `document.processing.completed`

示例结果摘要：

```text
normalize_status 200
status=normalized extraction_method=local content_hash=...
```

---

## 4.5 场景 E：URL 抓取与标准化验证

验证目标：

- `httpx + trafilatura` 主抓取链路可工作
- 实际网页可抓取并提取正文
- URL 文档可进入 `normalized`

验证方式：

1. 创建 URL document
2. 调用 `POST /documents/{id}/normalize`
3. 实际抓取 `https://example.com/`

验证结果：

- 抓取返回 `200`
- `trafilatura` 提取出正文
- `document.fetch.success strategy=httpx_trafilatura`
- 文档最终进入 `normalized`

示例结果摘要：

```text
document.fetch.started url=https://example.com/
document.fetch.success strategy=httpx_trafilatura url=https://example.com/ elapsed_ms=...
document.processing.completed document_id=... status=normalized extraction_method=local
```

---

## 4.6 场景 F：主处理链路验证

验证目标：

- `/documents/{id}/process` 能跑通从 normalize 到 persist 的整条主链路
- `summaries`
- `document_chunks`
- `summary_embeddings`
  都能真实写库

验证方式：

1. 创建 manual text document
2. 调用 `POST /documents/{id}/process`
3. 直接查 PostgreSQL 核验相关表记录

验证结果：

- 返回 `200`
- `quality_status = accepted`
- `dedup_status = primary`
- 成功生成 `summary_id`
- `chunk_count = 1`
- `summary_embedding_count = 1`

同时数据库核验：

- `summaries` 有 1 条
- `document_chunks` 有 1 条
- `summary_embeddings` 有 1 条

示例结果摘要：

```text
process_primary_status 200
{
  "status": "normalized",
  "quality_status": "accepted",
  "dedup_status": "primary",
  "summary_id": "...",
  "chunk_count": 1,
  "summary_embedding_count": 1
}

db_counts 1 1 1 ...
```

---

## 4.7 场景 G：重复文档跳过验证

验证目标：

- 相同内容再次进入系统时会被识别为重复
- `document_relations` 会写入
- 重复项不会继续生成新的 summary / chunk / embedding

验证方式：

1. 写入一篇 manual text 作为 primary
2. 再写入一篇内容完全相同的 manual text
3. 调用第二篇文档的 `/process`
4. 查 `document_relations`

验证结果：

- 第二篇文档处理返回 `200`
- `dedup_status = duplicate`
- `summary_id = null`
- `chunk_count = 0`
- `summary_embedding_count = 0`
- `skipped_reason = duplicate_document`
- `document_relations` 新增 1 条 `near_duplicate`

示例结果摘要：

```text
process_secondary_status 200
{
  "dedup_status": "duplicate",
  "summary_id": null,
  "chunk_count": 0,
  "summary_embedding_count": 0,
  "skipped_reason": "duplicate_document"
}

document.dedup.related ... relation_type=near_duplicate similarity=1.0000
db_counts ... duplicate 1
```

---

## 5. 本轮验证涉及的关键日志事件

本轮已经实际打出并看到的日志事件包括：

### 应用层

- `request.started`
- `request.completed`
- `request.failed`

### 摄入层

- `source.created`
- `document.ingested`
- `document.fetch.started`
- `document.fetch.success`
- `document.fetch.attempt_failed`
- `document.normalize.completed`

### 主链路

- `document.processing.started`
- `document.processing.completed`
- `document.processing.skipped`
- `document.processing.pipeline_completed`

### 质量与去重

- `document.quality.evaluated`
- `document.dedup.primary`
- `document.dedup.related`

### 分析与向量

- `document.summary.upserted`
- `document.chunks.rebuilt`
- `embedding.created`
- `summary.embedding.upserted`

这说明模块 03 当前不仅“跑通了”，而且关键链路都有留痕。

---

## 6. 当前仍未完成真实验证的边界

以下内容目前是“代码已接入”，但还没有做真实联调证明。

### 6.1 Jina Reader fallback

状态：

- 代码路径已写
- 配置项已写
- 未提供真实可用地址做联调

### 6.2 Firecrawl fallback

状态：

- 代码路径已写
- API key 配置项已写
- 未提供真实凭证做联调

### 6.3 外部 LLM / embedding provider

状态：

- 当前模块 03 采用本地启发式实现
- 还没有接 OpenAI 或其他外部模型

这不是 bug，而是当前阶段的明确取舍：

- 先把主链路跑通并可验证
- 再逐步替换本地 heuristic provider

---

## 7. 模块 03 交付结论

模块 03 当前可以认为已经完成了 MVP 范围内的“最小可运行内容资产处理链”：

- 可摄入
- 可抓取
- 可标准化
- 可评分
- 可去重
- 可生成摘要
- 可切 chunk
- 可写 embedding
- 可留下结构化日志

并且这些不是口头成立，而是已经做过实际验证和数据库核验。

---

## 8. 下一步

模块 03 之后，下一步进入模块 04：

- cluster build
- history retrieval
- context pack
- weekly draft
- reviewer
- LangGraph workflow

也就是说，接下来重点会从“单篇内容资产处理”转向“周报工作流闭环”。
