# Insight Flow SQLAlchemy Models 草案

## 1. 文档目标

本文档用于将数据库 Schema 设计进一步收敛为 SQLAlchemy ORM 实现草案，覆盖：

- model 文件组织方式
- Declarative Base 设计
- 通用 mixin 与类型定义
- 核心 model 的字段映射
- relationship 关系设计
- 枚举、JSONB、vector、数组等字段的处理方式
- ORM 层的实现注意事项

这份文档的目标是为后续真正编写 `models/*.py` 提供直接依据。

---

## 2. ORM 设计原则

## 2.1 ORM 负责表达结构，不负责业务编排

ORM model 的职责是：

- 描述表结构
- 约束字段类型
- 声明关系
- 提供基础查询入口

ORM model 不负责：

- workflow 编排
- 复杂业务逻辑
- LLM 调用
- 检索策略

这些逻辑应在 `services/` 或 `workflow/nodes/` 中实现。

## 2.2 优先显式字段，不滥用动态 JSON

MVP 中可以接受部分 `jsonb` 字段，例如：

- `config_json`
- `key_points`
- `tags`
- `bilingual_terms`
- `score_snapshot`

但核心状态、外键关系、查询高频字段必须显式建列，而不是全部塞进 JSON。

## 2.3 枚举值在 ORM 层要收束

数据库层可用 `text + check constraint`，但 ORM 层建议配合 Python `Enum` 使用，降低状态拼写错误。

## 2.4 model 要为 Alembic 迁移友好

建议避免：

- 过度动态 metaclass
- 复杂运行时字段拼接
- 难以被 Alembic 自动识别的黑魔法

---

## 3. 推荐目录结构

```text
backend/
  app/
    db/
      base.py
      mixins.py
      types.py
      enums.py
      models/
        __init__.py
        source.py
        document.py
        summary.py
        cluster.py
        report.py
        workflow.py
```

## 3.1 模块划分建议

### `base.py`

放：

- `DeclarativeBase`
- naming convention

### `mixins.py`

放：

- `TimestampMixin`
- `UUIDPrimaryKeyMixin`

### `types.py`

放：

- `JSONB` 辅助类型
- `Vector` 类型导入封装

### `enums.py`

放所有状态枚举。

### `models/*.py`

按领域拆分 model，避免一个大文件堆满所有表。

---

## 4. Base 与通用组件

## 4.1 Declarative Base 草案

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)
```

## 4.2 通用 Mixin 草案

```python
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, func


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

## 4.3 PostgreSQL 专用类型

MVP 中建议直接使用：

- `UUID`
- `JSONB`
- `ARRAY`
- `Vector` from `pgvector.sqlalchemy`

示例：

```python
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from pgvector.sqlalchemy import Vector
```

---

## 5. 枚举设计

## 5.1 枚举组织建议

统一放在 `db/enums.py`：

- `SourceType`
- `SourceStatus`
- `DocumentIngestType`
- `DocumentStatus`
- `DocumentQualityStatus`
- `DocumentDedupStatus`
- `DocumentRelationType`
- `SummaryStatus`
- `ClusterType`
- `ClusterStatus`
- `ReportType`
- `ReportStatus`
- `WorkflowType`
- `WorkflowStatus`
- `WorkflowEventStatus`

## 5.2 枚举示例

```python
from enum import StrEnum


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    WAITING_HUMAN_EDIT = "waiting_human_edit"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_MANUAL_INTERVENTION = "needs_manual_intervention"
```

建议：

- Python 3.11 可直接用 `StrEnum`
- 若运行环境不允许，可退回 `str, Enum`

---

## 6. Model 组织草案

## 6.1 `source.py`

建议包含：

- `Source`

示例草案：

```python
class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["Document"]] = relationship(back_populates="source")
```

## 6.2 `document.py`

建议包含：

- `Document`
- `DocumentRelation`
- `DocumentChunk`

### `Document` 草案

```python
class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    ingest_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str | None] = mapped_column(String(16))
    raw_content: Mapped[str | None] = mapped_column(Text)
    cleaned_content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    dedup_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    source: Mapped["Source | None"] = relationship(back_populates="documents")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="document")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")
```

### `DocumentRelation` 草案

```python
class DocumentRelation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_relations"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    related_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

### `DocumentChunk` 草案

```python
class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    document: Mapped["Document"] = relationship(back_populates="chunks")
```

## 6.3 `summary.py`

建议包含：

- `Summary`
- `SummaryEmbedding`

### `Summary` 草案

```python
class Summary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "summaries"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    bilingual_terms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    quality_score: Mapped[int | None] = mapped_column(SmallInteger)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="summaries")
    embeddings: Mapped[list["SummaryEmbedding"]] = relationship(back_populates="summary")
```

### `SummaryEmbedding` 草案

```python
class SummaryEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "summary_embeddings"

    summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("summaries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_source: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    summary: Mapped["Summary"] = relationship(back_populates="embeddings")
```

## 6.4 `cluster.py`

建议包含：

- `Cluster`
- `ClusterItem`

### `Cluster` 草案

```python
class Cluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clusters"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    cluster_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    build_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    items: Mapped[list["ClusterItem"]] = relationship(back_populates="cluster")
```

### `ClusterItem` 草案

```python
class ClusterItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cluster_items"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int | None] = mapped_column(Integer)

    cluster: Mapped["Cluster"] = relationship(back_populates="items")
    document: Mapped["Document"] = relationship()
```

## 6.5 `report.py`

建议包含：

- `Report`
- `ReportItem`
- `UserEdit`

### `Report` 草案

```python
class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_by_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
    )

    items: Mapped[list["ReportItem"]] = relationship(back_populates="report")
    edits: Mapped[list["UserEdit"]] = relationship(back_populates="report")
```

### `ReportItem` 草案

```python
class ReportItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "report_items"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("summaries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clusters.id", ondelete="SET NULL"),
        index=True,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    report: Mapped["Report"] = relationship(back_populates="items")
    summary: Mapped["Summary"] = relationship()
    document: Mapped["Document"] = relationship()
    cluster: Mapped["Cluster | None"] = relationship()
```

### `UserEdit` 草案

```python
class UserEdit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_edits"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    editor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="human")
    before_content: Mapped[str] = mapped_column(Text, nullable=False)
    after_content: Mapped[str] = mapped_column(Text, nullable=False)
    edit_summary: Mapped[str | None] = mapped_column(Text)

    report: Mapped["Report"] = relationship(back_populates="edits")
```

## 6.6 `workflow.py`

建议包含：

- `WorkflowRun`
- `WorkflowEvent`
- `RetrievalRecord`
- `ContextPack`

### `WorkflowRun` 草案

```python
class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    workflow_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    week_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    week_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list["WorkflowEvent"]] = relationship(back_populates="workflow_run")
    retrieval_records: Mapped[list["RetrievalRecord"]] = relationship(back_populates="workflow_run")
    context_packs: Mapped[list["ContextPack"]] = relationship(back_populates="workflow_run")
```

### `WorkflowEvent` 草案

```python
class WorkflowEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_events"

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    input_snapshot_ref: Mapped[str | None] = mapped_column(String(255))
    output_snapshot_ref: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="events")
```

### `RetrievalRecord` 草案

```python
class RetrievalRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retrieval_records"

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filter_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retrieved_summary_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    retrieved_chunk_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)))
    score_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="retrieval_records")
```

### `ContextPack` 草案

```python
class ContextPack(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "context_packs"

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    build_version: Mapped[str] = mapped_column(String(64), nullable=False)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="context_packs")
```

---

## 7. Relationship 设计建议

## 7.1 一对多关系

主要是一对多：

- `Source -> Document`
- `Document -> Summary`
- `Document -> DocumentChunk`
- `Cluster -> ClusterItem`
- `Report -> ReportItem`
- `Report -> UserEdit`
- `WorkflowRun -> WorkflowEvent`
- `WorkflowRun -> RetrievalRecord`
- `WorkflowRun -> ContextPack`

## 7.2 自关联关系

`DocumentRelation` 是文档自关联，不建议在 `Document` 上做过于复杂的双向 relationship 名称，容易混淆。

建议：

- 先保留简单查询方式
- 需要时在 repository/service 层封装

## 7.3 级联策略

建议：

- 明确使用 `ondelete="CASCADE"` 处理强依赖表
- 在 ORM relationship 上也补上合理的 cascade

例如：

```python
summaries = relationship(
    "Summary",
    back_populates="document",
    cascade="all, delete-orphan",
)
```

但要注意：

- `Report -> WorkflowRun` 这类跨域引用不建议 delete-orphan

---

## 8. 约束与索引在 ORM 层的表达

## 8.1 `__table_args__` 建议

索引、唯一约束、检查约束统一放入 `__table_args__`。

示例：

```python
__table_args__ = (
    UniqueConstraint("document_id", "prompt_version", "model_name"),
    Index("idx_summaries_category", "category"),
)
```

## 8.2 PostgreSQL 部分唯一索引

如 `canonical_url` 的部分唯一索引，通常不适合完全靠 ORM model 表达，建议在 Alembic migration 中显式写 SQL 或使用 dialect-specific index。

因此：

- ORM model 中保留字段和普通索引
- 部分唯一索引交给 migration 层

---

## 9. Vector 字段实现建议

## 9.1 维度管理

`Vector(1536)` 只是示意。真正实现时不要把维度写死到各个 model 文件里。

建议：

- 在 `db/types.py` 中统一定义

例如：

```python
EMBEDDING_DIM = 1536
EmbeddingVector = Vector(EMBEDDING_DIM)
```

这样后续换 embedding 维度时更容易集中调整。

## 9.2 多模型 embedding

由于已经单独设计了 `embedding_model` 字段，因此：

- 不应覆盖旧向量
- 应新增新记录

这意味着：

- `SummaryEmbedding`
- `DocumentChunk`

都需要用唯一约束把模型版本维度纳入。

---

## 10. JSONB 字段注意事项

## 10.1 默认值

ORM 层不要直接写可变对象默认值，例如：

- `default=[]`
- `default={}`

应写为：

- `default=list`
- `default=dict`

## 10.2 JSONB 适用范围

当前设计中，以下字段适合 JSONB：

- `Source.config_json`
- `Summary.key_points`
- `Summary.tags`
- `Summary.bilingual_terms`
- `WorkflowRun.state_json`
- `RetrievalRecord.filter_json`
- `RetrievalRecord.score_snapshot`
- `ContextPack.context_json`

这些 JSONB 字段的共同点是：

- 结构会演进
- 查询粒度不是所有键都高频

---

## 11. Session 与 Repository 建议

## 11.1 不建议把复杂查询写进 model

例如：

- 向量召回
- 周报候选查询
- workflow 列表分页

这些不应写成 model method，而应放到：

- `repositories/`
- `services/`

## 11.2 Repository 粗分建议

```text
repositories/
  source_repository.py
  document_repository.py
  summary_repository.py
  cluster_repository.py
  report_repository.py
  workflow_repository.py
  retrieval_repository.py
```

---

## 12. 与 LangGraph 的接口约定

## 12.1 workflow state 引用的 ORM 对象

LangGraph state 中引用的主要对象：

- `workflow_runs.id`
- `reports.id`
- `summaries.id`
- `clusters.id`
- `context_packs.id`

因此 ORM 层要确保这些对象：

- 主键稳定
- 查询快速
- 状态字段可直接暴露给 workflow

## 12.2 `human_edit` 与 ORM

`human_edit` 流程中，ORM 至少涉及：

- 更新 `Report.status`
- 写入 `UserEdit`
- 更新 `WorkflowRun.status`

因此这三类 model 的事务边界要保持清晰，避免：

- 编辑已保存但 workflow 状态没更新
- workflow 已 resume 但 report 还没 finalized

---

## 13. MVP 明确不做的 ORM 设计

第一版不建议在 ORM 层加入：

- 多租户 owner 字段体系
- 用户模型和复杂权限关系
- polymorphic inheritance
- 审批流抽象基类
- graph node 通用插件注册表

这些都只会增加代码复杂度，不服务 MVP 主闭环。

---

## 14. 推荐优先实现顺序

按 ORM 代码落地顺序，建议：

1. `Base / Mixins / Enums / Types`
2. `Source`
3. `Document / DocumentRelation / DocumentChunk`
4. `Summary / SummaryEmbedding`
5. `Cluster / ClusterItem`
6. `WorkflowRun / WorkflowEvent / RetrievalRecord / ContextPack`
7. `Report / ReportItem / UserEdit`

这样做的好处是：

- 先把内容资产主干搭起来
- 再落 workflow 过程层
- 最后落周报输出与人工编辑链路

---

## 15. 结论

Insight Flow 的 SQLAlchemy model 设计不应只是数据库字段的机械映射，而应体现三个目标：

1. 模型关系足够清晰，支撑长期资产沉淀
2. workflow 相关对象足够稳定，支撑 LangGraph 恢复与追踪
3. 检索与引用链对象足够明确，支撑双路 RAG 和事实回溯

这份草案的定位是：

> 在不提前写正式代码的前提下，把 ORM 层的结构、边界和实现注意事项先定下来。

下一步如果要继续推进，最自然的是基于这份文档直接落第一版：

- `Base / Mixins / Enums / Types`
- `Document / Summary / WorkflowRun / Report` 这几组核心 model 代码
