# Insight Flow MVP 任务清单

## 1. 说明

这份文档用于管理 Insight Flow MVP 的实现任务。

使用原则：

- 不走重型 spec 流程
- 但所有核心工作都要进入任务清单
- 每完成一项，就把状态改为已完成
- 优先按依赖顺序推进
- 开发、调试、测试、联调必须满足日志与可追溯性约定

关联文档：

- `docs/planning/insight_flow_logging_and_traceability_convention.md`

状态约定：

- `TODO`
- `DOING`
- `DONE`
- `BLOCKED`

---

## 2. 当前总体进度

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 01 工程骨架 | `DONE` | 后端基础骨架已完成第一版 |
| 02 数据与模型 | `DONE` | 模型、metadata 与本地 PostgreSQL migration 验证已完成 |
| 03 摄入与分析主链路 | `DONE` | 输入、抓取、标准化、质量评分、去重、分析、chunk、embedding 与 process 主链路已跑通 |
| 04 RAG 与周报 Workflow | `TODO` | 依赖模块 03 |
| 05 前端工作台 | `TODO` | 可在 03 后局部并行 |
| 06 联调与收尾 | `TODO` | 最后阶段 |

---

## 3. 模块 01：工程骨架

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M01-01 | 建立 `backend/` 目录结构 | `DONE` | 无 | 已完成 |
| M01-02 | 初始化 `pyproject.toml` | `DONE` | 无 | 已完成 |
| M01-03 | 增加 `.env.example` | `DONE` | 无 | 已完成 |
| M01-04 | 建立 `config.py` | `DONE` | M01-02 | 已完成 |
| M01-05 | 建立 `logging.py` | `DONE` | M01-02 | 已完成 |
| M01-06 | 建立 SQLAlchemy `Base` | `DONE` | M01-02 | 已完成 |
| M01-07 | 建立 DB session | `DONE` | M01-04, M01-06 | 已完成 |
| M01-08 | 建立 `mixins.py` | `DONE` | M01-06 | 已完成 |
| M01-09 | 建立 `enums.py` | `DONE` | M01-06 | 已完成 |
| M01-10 | 建立 `types.py` | `DONE` | M01-06 | 已完成 |
| M01-11 | 建立 FastAPI 入口 | `DONE` | M01-04, M01-05 | 已完成 |
| M01-12 | 建立 `/health` 接口 | `DONE` | M01-11 | 已完成 |
| M01-13 | 初始化 Alembic | `DONE` | M01-06 | 已完成 |
| M01-14 | 做基础语法校验 | `DONE` | M01-01 ~ M01-13 | 已完成 |

---

## 4. 模块 02：数据与模型

目标：

- 先把长期研究资产的数据库主干和 ORM 模型落下来

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M02-01 | 建立 `Source` model | `DONE` | M01 | |
| M02-02 | 建立 `Document` model | `DONE` | M01 | |
| M02-03 | 建立 `DocumentRelation` model | `DONE` | M02-02 | |
| M02-04 | 建立 `DocumentChunk` model | `DONE` | M02-02 | |
| M02-05 | 建立 `Summary` model | `DONE` | M02-02 | |
| M02-06 | 建立 `SummaryEmbedding` model | `DONE` | M02-05 | |
| M02-07 | 建立 `Cluster` model | `DONE` | M02-02, M02-05 | |
| M02-08 | 建立 `ClusterItem` model | `DONE` | M02-07 | |
| M02-09 | 建立 `WorkflowRun` model | `DONE` | M01 | |
| M02-10 | 建立 `WorkflowEvent` model | `DONE` | M02-09 | |
| M02-11 | 建立 `RetrievalRecord` model | `DONE` | M02-09 | |
| M02-12 | 建立 `ContextPack` model | `DONE` | M02-09 | |
| M02-13 | 建立 `Report` model | `DONE` | M02-09 | |
| M02-14 | 建立 `ReportItem` model | `DONE` | M02-13, M02-05 | |
| M02-15 | 建立 `UserEdit` model | `DONE` | M02-13 | |
| M02-16 | 导出 `models/__init__.py` | `DONE` | M02-01 ~ M02-15 | |
| M02-17 | 编写 Alembic 初始 migration | `DONE` | M02-01 ~ M02-16 | |
| M02-18 | 验证 migration 可执行 | `DONE` | M02-17 | 已完成本地 PostgreSQL 迁移验证，`alembic_version=20260416_0001` |
| M02-19 | 验证 ORM import 与 metadata 正常 | `DONE` | M02-16 | 已验证 15 张表已注册到 metadata |

### 模块 02 可并行项

| 并行组 | 可并行任务 |
| --- | --- |
| A | `M02-01 ~ M02-08` 内容资产模型 |
| B | `M02-09 ~ M02-15` workflow/reporting 模型 |
| C | `M02-17 ~ M02-18` 需等待 A+B 完成 |

---

## 5. 模块 03：摄入与分析主链路

目标：

- 跑通“输入 -> 清洗 -> 去重 -> 分析 -> 入库”

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M03-01 | 建立 Source API 基础路由 | `DONE` | M02 | 已增加 `/sources` 与 `/sources/rss` |
| M03-02 | 建立 Document API 基础路由 | `DONE` | M02 | 已增加 `/documents`、`/documents/url`、`/documents/manual-text` |
| M03-03 | 实现 RSS source 写入逻辑 | `DONE` | M03-01 | 已验证可写入 `sources` |
| M03-04 | 实现 URL 导入接口 | `DONE` | M03-02 | 已验证可写入 `documents`，含 canonical url 与冲突保护 |
| M03-05 | 实现手动文本导入接口 | `DONE` | M03-02 | 已验证可写入手动文本 document |
| M03-06 | 实现 `httpx + trafilatura` 抓取链路 | `DONE` | M02 | 已验证 URL 文档抓取与正文提取闭环 |
| M03-07 | 实现抓取 fallback 逻辑 | `DONE` | M03-06 | 已接入 Jina / Firecrawl fallback 配置路径，真实 provider 凭证验证待后续环境配置 |
| M03-08 | 实现 normalization service | `DONE` | M03-06 | 已验证 manual text 与 URL 文档标准化闭环 |
| M03-09 | 实现质量评分 service | `DONE` | M03-08 | 已落地启发式质量评分并接入 process 主链路 |
| M03-10 | 实现语义去重 service | `DONE` | M03-08, M02-06 | 已落地基于内容 hash + 本地 embedding 的相似度判定 |
| M03-11 | 实现 supporting-source 归并逻辑 | `DONE` | M03-10 | 已支持 `supporting_source` / `near_duplicate` 关系写入 |
| M03-12 | 实现文档分析 service | `DONE` | M03-08 | 已落地本地启发式单篇分析服务 |
| M03-13 | 输出摘要/标签/分类/观点/双语术语 | `DONE` | M03-12 | 已写入 `summaries` 结构化结果 |
| M03-14 | 实现 chunk 构建逻辑 | `DONE` | M03-08 | 已写入 `document_chunks` |
| M03-15 | 实现 embedding 写入逻辑 | `DONE` | M03-14, M03-13 | 已写入 chunk embedding 与 summary embedding |
| M03-16 | 打通 ingest -> analyze -> persist 主链路 | `DONE` | M03-03 ~ M03-15 | 已验证 `/documents/{id}/process` 端到端闭环与重复文档跳过逻辑 |

### 模块 03 可并行项

| 并行组 | 可并行任务 |
| --- | --- |
| A | `M03-01 ~ M03-05` API 基础路由 |
| B | `M03-06 ~ M03-08` 抓取与标准化 |
| C | `M03-09 ~ M03-13` 质量评分、去重、分析 |
| D | `M03-14 ~ M03-15` chunk 与 embedding |

---

## 6. 模块 04：RAG 与周报 Workflow

目标：

- 跑通 MVP 的周报主闭环

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M04-01 | 实现 cluster build service | `TODO` | M03, M02-07 | |
| M04-02 | 实现 summary 检索逻辑 | `TODO` | M03-15 | |
| M04-03 | 实现 source chunk backfill | `TODO` | M04-02 | |
| M04-04 | 实现 context pack builder | `TODO` | M04-03, M02-12 | |
| M04-05 | 实现 weekly draft service | `TODO` | M04-04 | |
| M04-06 | 实现 reviewer service | `TODO` | M04-05 | |
| M04-07 | 定义 LangGraph state schema 代码 | `TODO` | M02-09 ~ M02-12 | |
| M04-08 | 实现 `collect_inputs` 节点 | `TODO` | M04-07 | |
| M04-09 | 实现 `normalize_documents` 节点 | `TODO` | M04-07, M03-08 | |
| M04-10 | 实现 `score_and_dedup` 节点 | `TODO` | M04-07, M03-10 | |
| M04-11 | 实现 `analyze_documents` 节点 | `TODO` | M04-07, M03-12 | |
| M04-12 | 实现 `build_clusters` 节点 | `TODO` | M04-07, M04-01 | |
| M04-13 | 实现 `retrieve_history` 节点 | `TODO` | M04-07, M04-02 | |
| M04-14 | 实现 `backfill_evidence` 节点 | `TODO` | M04-07, M04-03 | |
| M04-15 | 实现 `draft_weekly_report` 节点 | `TODO` | M04-07, M04-05 | |
| M04-16 | 实现 `review_evidence` 节点 | `TODO` | M04-07, M04-06 | |
| M04-17 | 实现 `human_edit` 节点 | `TODO` | M04-07 | |
| M04-18 | 实现 `export_markdown` 节点 | `TODO` | M04-07 | |
| M04-19 | 组装 Weekly Report graph | `TODO` | M04-08 ~ M04-18 | |
| M04-20 | 接入 Postgres checkpoint saver | `TODO` | M04-19 | |
| M04-21 | 实现 workflow run API | `TODO` | M04-19 | |
| M04-22 | 实现 workflow resume API | `TODO` | M04-20 | |
| M04-23 | 跑通周报生成主链路 | `TODO` | M04-01 ~ M04-22 | |

### 模块 04 可并行项

| 并行组 | 可并行任务 |
| --- | --- |
| A | `M04-01 ~ M04-06` RAG / draft / reviewer services |
| B | `M04-07 ~ M04-18` LangGraph 节点代码 |
| C | `M04-21 ~ M04-22` API 可在 graph 接近完成时并行 |

---

## 7. 模块 05：前端工作台

目标：

- 把主闭环变成可操作的产品界面

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M05-01 | 初始化前端项目骨架 | `TODO` | 无 | 若还没做 |
| M05-02 | 建立基础布局与导航 | `TODO` | M05-01 | |
| M05-03 | 实现 Sources 页面 | `TODO` | M03-01 | |
| M05-04 | 实现 Documents 页面 | `TODO` | M03-02, M03-16 | |
| M05-05 | 实现 Weekly Reports 列表页 | `TODO` | M04-21 | |
| M05-06 | 实现 Report Editor 页面 | `TODO` | M04-23 | |
| M05-07 | 实现 Workflow Runs 页面 | `TODO` | M04-21 | |
| M05-08 | 接入 report export 操作 | `TODO` | M04-18 | |
| M05-09 | 打通前后端联调 | `TODO` | M05-03 ~ M05-08 | |

### 模块 05 可并行项

| 并行组 | 可并行任务 |
| --- | --- |
| A | `M05-03 ~ M05-04` Sources / Documents |
| B | `M05-05 ~ M05-06` Reports / Editor |
| C | `M05-07` Workflow Runs |

---

## 8. 模块 06：联调与收尾

目标：

- 让 MVP 变成真正可演示、可复跑的版本

| ID | 任务 | 状态 | 依赖 | 备注 |
| --- | --- | --- | --- | --- |
| M06-01 | 端到端联调 ingest -> report | `TODO` | M03, M04, M05 | |
| M06-02 | 测试 workflow checkpoint 恢复 | `TODO` | M04-20 | |
| M06-03 | 测试 reviewer 回路 | `TODO` | M04-16, M04-19 | |
| M06-04 | 验证引用链与来源回溯 | `TODO` | M04-23 | |
| M06-05 | 基础异常处理补齐 | `TODO` | M06-01 | |
| M06-06 | 补 README / 运行说明 | `TODO` | M06-01 | |
| M06-07 | 补最小演示数据或演示脚本 | `TODO` | M06-01 | |

---

## 9. 当前建议开工任务

当前应进入：

### 模块 02：数据与模型

优先任务顺序建议：

1. `M02-01 ~ M02-08`
   内容资产模型
2. `M02-09 ~ M02-15`
   workflow / report 模型
3. `M02-16`
   导出模型
4. `M02-17 ~ M02-19`
   migration 与 metadata 验证

---

## 10. 维护规则

后续执行时：

- 开始某任务时，把状态改成 `DOING`
- 完成后改成 `DONE`
- 被前置条件卡住时改成 `BLOCKED`

如果后续拆给多个 agent，直接按模块内“可并行项”分配即可。
