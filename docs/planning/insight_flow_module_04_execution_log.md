# Insight Flow 模块 04 执行与验证记录

## 1. 目的

这份文档记录模块 04 当前已完成阶段，也就是：

- `M04-01 ~ M04-23`

当前已完成的实现和验证证据。

当前阶段的目标不是把 LangGraph 全部跑起来，而是先证明下面这些核心服务和核心 workflow 节点已经独立成立：

1. `cluster build`
2. `summary retrieval`
3. `source chunk backfill`
4. `context pack builder`
5. `weekly draft`
6. `reviewer`
7. workflow `state schema`
8. `collect_inputs`
9. `normalize_documents`
10. `score_and_dedup`
11. `analyze_documents`
12. `build_clusters`
13. `retrieve_history`
14. `backfill_evidence`
15. `draft_weekly_report`
16. `review_evidence`
17. `human_edit`
18. `export_markdown`
19. Weekly Report graph assembly
20. Postgres checkpoint saver
21. workflow run API
22. workflow resume API
23. API-level workflow main loop

---

## 2. 当前范围

对应任务板：

- `M04-01 ~ M04-23`

当前状态：

- 服务层、节点层、graph 层与 API 层都已落地
- 模块 04 总体已完成
- 当前 M04 无剩余任务

任务板基线：

- [insight_flow_mvp_task_board.md](./insight_flow_mvp_task_board.md)

---

## 3. 本轮新增服务

新增服务文件：

- [backend/app/services/cluster_service.py](/Users/sz/Code/insight-flow/backend/app/services/cluster_service.py)
- [backend/app/services/workflow_service.py](/Users/sz/Code/insight-flow/backend/app/services/workflow_service.py)
- [backend/app/services/retrieval_service.py](/Users/sz/Code/insight-flow/backend/app/services/retrieval_service.py)
- [backend/app/services/context_pack_service.py](/Users/sz/Code/insight-flow/backend/app/services/context_pack_service.py)
- [backend/app/services/report_draft_service.py](/Users/sz/Code/insight-flow/backend/app/services/report_draft_service.py)
- [backend/app/services/reviewer_service.py](/Users/sz/Code/insight-flow/backend/app/services/reviewer_service.py)

新增 workflow 文件：

- [backend/app/workflows/weekly_report/state.py](/Users/sz/Code/insight-flow/backend/app/workflows/weekly_report/state.py)
- [backend/app/workflows/weekly_report/nodes.py](/Users/sz/Code/insight-flow/backend/app/workflows/weekly_report/nodes.py)
- [backend/app/workflows/weekly_report/__init__.py](/Users/sz/Code/insight-flow/backend/app/workflows/weekly_report/__init__.py)

这些服务当前承担的职责是：

- `cluster_service`
  从已处理文档构建周报事件簇
- `workflow_service`
  创建 weekly workflow run
- `retrieval_service`
  基于 cluster summary 检索历史 summary 和 evidence chunk
- `context_pack_service`
  把 cluster、历史 summary、evidence chunk 组装成 context pack
- `report_draft_service`
  生成周报草稿并写入 `reports / report_items`
- `reviewer_service`
  基于结构化判据审查草稿
- `workflow state`
  保存周报 workflow 的序列化状态结构
- `workflow nodes`
  定义前半段节点与统一的事件/状态持久化包装器

本轮补充完成的后半段 workflow 节点：

- `retrieve_history_node`
- `backfill_evidence_node`
- `draft_weekly_report_node`
- `review_evidence_node`
- `human_edit_node`
- `export_markdown_node`

本轮补充完成的 graph / API 文件：

- [backend/app/workflows/weekly_report/graph.py](/Users/sz/Code/insight-flow/backend/app/workflows/weekly_report/graph.py)
- [backend/app/api/routes/workflow.py](/Users/sz/Code/insight-flow/backend/app/api/routes/workflow.py)
- [backend/app/api/schemas/workflow.py](/Users/sz/Code/insight-flow/backend/app/api/schemas/workflow.py)

---

## 4. 本轮实际验证场景

## 4.1 场景 A：服务导入验证

验证目标：

- 新增服务全部可导入
- 模块间依赖没有循环或语法错误

验证方式：

- `py_compile`
- 直接 import 服务入口

验证结果：

- 通过

示例结果摘要：

```text
service_imports_ok
```

---

## 4.2 场景 B：模块 04 服务链数据库级联调

验证目标：

- `M04-01 ~ M04-06` 六个服务能按顺序串起来
- 相关表真实写库成功
- reviewer 能输出结构化 decision

验证方式：

1. 通过模块 03 API 创建并处理 3 条文档
   - 1 条历史内容
   - 2 条当前周内容
2. 调整 `created_at` 让它们落入不同时间窗
3. 调用服务层：
   - `create_weekly_workflow_run`
   - `build_weekly_clusters`
   - `retrieve_history_for_clusters`
   - `build_context_pack`
   - `draft_weekly_report`
   - `review_report_evidence`
4. 直接查数据库核验：
   - `clusters`
   - `cluster_items`
   - `retrieval_records`
   - `context_packs`
   - `reports`
   - `report_items`

## 4.3 场景 C：前半段 workflow 节点联调

验证目标：

- `M04-07 ~ M04-12` 节点可串联执行
- `workflow_runs.state_json` 会随节点推进而更新
- `workflow_events` 会按节点产生完整执行记录
- 遇到单条失败文档时，workflow 能继续处理其余文档

验证方式：

1. 新建 3 条 manual text 文档
2. 创建 weekly workflow run
3. 初始化 `WeeklyReportGraphState`
4. 顺序执行：
   - `collect_inputs_node`
   - `normalize_documents_node`
   - `score_and_dedup_node`
   - `analyze_documents_node`
   - `build_clusters_node`
5. 数据库核验：
   - `workflow_runs`
   - `workflow_events`
   - `clusters`

## 4.4 场景 D：核心 workflow 节点全链路联调

验证目标：

- `M04-07 ~ M04-16` 节点可按顺序完整串联
- 检索、context pack、report、review 结果都能落库
- reviewer decision 和 checks 能回写到 workflow state

验证方式：

1. 新建 3 条 manual text 文档
   - 1 条历史文档
   - 2 条当前周文档
2. 创建 weekly workflow run
3. 初始化 `WeeklyReportGraphState`
4. 顺序执行：
   - `collect_inputs_node`
   - `normalize_documents_node`
   - `score_and_dedup_node`
   - `analyze_documents_node`
   - `build_clusters_node`
   - `retrieve_history_node`
   - `backfill_evidence_node`
   - `draft_weekly_report_node`
   - `review_evidence_node`
5. 数据库核验：
   - `retrieval_records`
   - `context_packs`
   - `reports`
   - `report_items`
   - `workflow_events`

## 4.5 场景 E：human_edit 与 export_markdown 联调

验证目标：

- `human_edit` 能将 workflow/report 切换到人工编辑阶段
- `export_markdown` 能把 Markdown 文件真实落盘
- workflow 最终状态能转为 `completed`

验证方式：

1. 新建 3 条 manual text 文档
2. 运行完整节点链：
   - `collect_inputs_node`
   - `normalize_documents_node`
   - `score_and_dedup_node`
   - `analyze_documents_node`
   - `build_clusters_node`
   - `retrieve_history_node`
   - `backfill_evidence_node`
   - `draft_weekly_report_node`
   - `review_evidence_node`
   - `human_edit_node`
   - `export_markdown_node`
3. 核验：
   - `workflow_runs.status`
   - 导出的文件路径与文件大小

## 4.6 场景 F：graph compile 与 Postgres checkpoint 验证

验证目标：

- Weekly Report graph 能基于 LangGraph compile 成功
- Postgres checkpointer 能初始化并挂入 graph

验证方式：

1. 安装：
   - `langgraph`
   - `langgraph-checkpoint-postgres`
2. 编译 memory graph
3. 编译 Postgres-backed graph

结果摘要：

```text
weekly_graph_compile_ok True CompiledStateGraph
postgres_graph_compile_ok True CompiledStateGraph
```

## 4.7 场景 G：workflow run/resume API 联调

验证目标：

- `POST /workflows/weekly-report/run` 会运行到 `human_edit` 中断点
- `POST /workflows/{workflow_run_id}/resume` 会从 checkpoint 恢复并导出 Markdown

验证方式：

1. 使用 `TestClient`
2. 创建 3 条 manual text 文档并传入 `input_document_ids`
3. 调用 `run`
4. 调用 `resume`
5. 核验 API 返回和导出路径

---

## 5. 验证结果

### 5.1 Workflow Run

成功创建：

- `workflow_run_id = c950441f-e0bf-498a-a602-864f7ccb49fb`

示例日志：

```text
workflow_run.created workflow_run_id=c950... workflow_type=weekly_report
```

### 5.2 Cluster Build

成功写入：

- `cluster_count = 1`
- `cluster_item_count = 3`

说明：

- 本轮测试样本最终被聚成了 1 个 weekly event
- 3 篇文档都挂进了 cluster

示例日志：

```text
clusters.built ... cluster_count=1 build_version=m04_cluster_v1
```

### 5.3 Retrieval

成功写入：

- `retrieval_count = 1`
- `summary_hits = 2`
- `chunk_hits = 2`

示例结果摘要：

```text
retrieval_ids [summary_id_1, summary_id_2] [chunk_id_1, chunk_id_2]
```

示例日志：

```text
retrieval.completed workflow_run_id=c950... cluster_count=1 summary_hits=2 chunk_hits=2
```

### 5.4 Context Pack

成功写入：

- `context_pack_id = 071b40f8-83ba-42a5-b64c-f39d98ee7253`
- `context_pack_count = 1`

context pack 中已包含：

- 当前 cluster
- 历史 summary
- evidence chunk

示例日志：

```text
context_pack.built workflow_run_id=c950... context_pack_id=071b...
```

### 5.5 Weekly Draft

成功写入：

- `report_id = 35aa00fe-720c-481a-b97c-542cfa402590`
- `report_item_count = 3`

说明：

- 报告草稿已生成
- 3 条 report item 已落库
- 报告正文长度约 `1256`

示例日志：

```text
report.drafted workflow_run_id=c950... report_id=35aa... cluster_count=1 content_length=1256
```

### 5.6 Reviewer

成功输出：

- `decision = pass`

结构化判据：

```json
{
  "numeric_support_present": true,
  "source_diversity_sufficient": true,
  "evidence_traceable": true,
  "language_overclaim": false
}
```

示例日志：

```text
review.completed report_id=35aa... decision=pass evidence_traceable=True source_diversity_sufficient=True language_overclaim=False
```

### 5.7 Workflow Nodes

成功创建：

- `workflow_run_id = a7be95e7-e7f0-43ce-ac63-0ee71ddd5416`
- `workflow_event_count = 5`

节点联调结果摘要：

```text
input_count 15
normalized_count 14
accepted_count 5
summary_count 5
cluster_count 3 3
workflow_status running
state_status build_clusters
```

说明：

- `collect_inputs` 成功拉取当前时间窗候选文档
- `normalize_documents` 成功跳过 1 条抓取失败的 URL 文档
- 其余文档继续完成评分、去重、分析和 cluster 构建
- `workflow_runs.state_json` 已随节点推进更新
- `workflow_events` 已记录 5 个节点执行事件

### 5.8 Full Workflow Nodes

成功创建：

- `workflow_run_id = be3ef890-fc10-474f-a39b-42ad46ccf8a2`
- `workflow_event_count = 9`
- `retrieval_count = 1`
- `context_pack_count = 1`

完整节点联调结果摘要：

```text
cluster_count 3
retrieved_summary_count 4
retrieved_chunk_count 4
context_pack_ref e0370040-e257-4fda-b5e5-dea141831a40
report_id 39dd539c-c08b-4856-b479-7839e9487b71
report_item_count 6
review_decision pass
workflow_status running
workflow_event_count 9
```

review 判据：

```json
{
  "numeric_support_present": true,
  "source_diversity_sufficient": true,
  "evidence_traceable": true,
  "language_overclaim": false
}
```

说明：

- `retrieve_history` 已成功写入 `retrieval_records`
- `backfill_evidence` 已成功写入 `context_packs`
- `draft_weekly_report` 已成功写入 `reports / report_items`
- `review_evidence` 已成功将 decision/checks 回写到 state

### 5.9 Human Edit And Export

成功创建：

- `workflow_run_id = 909a2234-6db7-40c1-b94c-13526d86718e`

完整结果摘要：

```text
workflow_status completed
human_edit_status approved
export_path runtime_exports/reports/20260416_8a9d30f3-82c2-4e65-98ed-10ab39eff7e8.md
export_exists True
export_size 2719
review_decision pass
```

说明：

- `human_edit` 已成功把 report 标记为 `editing`
- `export_markdown` 已真实写出 Markdown 文件
- workflow 最终状态已转为 `completed`

### 5.10 Graph And Checkpointer

验证结果摘要：

```text
weekly_graph_compile_ok True CompiledStateGraph
postgres_graph_compile_ok True CompiledStateGraph
```

说明：

- graph 装配成功
- PostgresSaver 初始化成功
- graph 已具备 interrupt/resume 所需的 checkpoint 基础

### 5.11 Workflow APIs

API 级验证结果摘要：

```text
run_status_code 201
run_json {
  "status": "waiting_human_edit",
  "human_edit_status": "waiting",
  "report_id": "...",
  "review_decision": "pass"
}

resume_status_code 200
resume_json {
  "status": "completed",
  "human_edit_status": "approved",
  "report_id": "...",
  "review_decision": "pass",
  "exported_markdown_path": "runtime_exports/reports/20260416_614ef39d-23ba-4d82-a6ef-b503d30c4337.md"
}
```

说明：

- `run` API 已停在 `human_edit`
- `resume` API 已从 checkpoint 恢复到 `export_markdown`
- API 级周报主闭环已跑通

---

## 6. 本轮踩到并修复的问题

## 6.1 `pgvector` embedding 真值判断错误

问题：

- 检索阶段使用了 `item.embedding or []`
- `pgvector` 取出的数组对象不适合做布尔判断

表现：

- 抛出：
  `ValueError: The truth value of an array with more than one element is ambiguous`

修复：

- 改成显式判断 `is not None`

结果：

- 检索链恢复正常

## 6.2 `score_snapshot` JSON 序列化错误

问题：

- `score_snapshot` 中写入了 `numpy.float32`
- PostgreSQL JSONB 不接受这种对象

表现：

- 抛出：
  `TypeError: Object of type float32 is not JSON serializable`

修复：

- 在写 `score_snapshot` 时统一 `float(score)`

结果：

- `retrieval_records` 可正常落库

---

## 6.3 单条 URL 抓取失败会拖垮 workflow

问题：

- `collect_inputs` 会收集时间窗内所有候选文档
- 当其中包含无效 URL 文档时，`normalize_documents` 原本会直接抛异常
- 结果是整条 workflow 被单条坏文档中断

表现：

```text
DocumentFetchError: all fetch strategies failed for https://example.com/articles/2285dcdc
```

修复：

- 在 `normalize_documents_node` 内按文档粒度捕获：
  - `DocumentFetchError`
  - `DocumentNormalizationError`
  - `ValueError`
- 失败文档标记为 `DocumentStatus.FAILED`
- 节点记录 warning 日志并继续处理后续文档

结果：

- workflow 前半段节点联调通过
- 单条坏 URL 不再拖垮整批执行

---

## 7. 当前实现边界

模块 04 现在已经整体完成。

当前已经完成：

- 服务层验证
- 节点层验证
- graph 组装
- Postgres checkpoint saver
- workflow run/resume API
- API 级周报主闭环

---

## 8. 当前结论

模块 04 已经证明：

- Insight Flow 不只是能处理单篇文档
- 现在也已经具备了最小周报服务层闭环能力
- 并且已经具备了核心 workflow state + node 闭环能力

当前已成立的能力链路是：

```text
processed documents
-> clusters
-> retrieval
-> context pack
-> report draft
-> reviewer
```

以及：

```text
workflow_run
-> collect_inputs
-> normalize_documents
-> score_and_dedup
-> analyze_documents
-> build_clusters
-> retrieve_history
-> backfill_evidence
-> draft_weekly_report
-> review_evidence
-> human_edit
-> export_markdown
```

这为前端工作台和模块 06 的端到端联调提供了稳定基础。
