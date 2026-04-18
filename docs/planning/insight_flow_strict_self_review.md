# Insight Flow 严格自查报告

## 1. 范围

这份文档是对当前 Insight Flow MVP 仓库的一次严格自查，标准偏向代码审查而不是功能介绍。

关注重点：

- 行为正确性
- workflow 状态一致性
- 数据边界与隔离性
- 可追溯性是否真的成立
- 文档/验证是否存在“看起来成立但实际有洞”的问题

---

## 2. 结论

整体判断：

- 这轮自查最初发现了 7 项核心问题，其中 3 项 `High`，4 项 `Medium`
- 截至 `2026-04-18`，这些问题已完成修复并通过回归验证
- 当前项目可以视为“工程质量已收口到 MVP 可接受水平”，但仍需后续版本继续增强测试覆盖和运行环境隔离

下面的 findings 按严重程度排序。

### 2.1 修复状态概览

| Finding | 状态 | 修复摘要 |
| --- | --- | --- |
| `F1` workflow 输入边界不成立 | `RESOLVED` | cluster 构建改为显式接收当前 run 的 `document_ids`，不再重扫整周全库 |
| `F2` cluster 跨 run 互相覆盖 | `RESOLVED` | `clusters` 新增 `workflow_run_id`，cluster rebuild 仅清理当前 run 产物 |
| `F3` reviewer loop 无真实修正 | `RESOLVED` | 增加 `draft_constraints / retrieval_overrides`，让 reviewer 回路会真实改变草稿或检索范围 |
| `F4` retry_count 不一致 | `RESOLVED` | `update_workflow_run_state()` 同步 `workflow_runs.retry_count` |
| `F5` 错误日志丢 trace 上下文 | `RESOLVED` | middleware 改为在 `finally` 清理 context，错误处理日志保留 `request_id / trace_id` |
| `F6` ORM / migration drift | `RESOLVED` | `Document` ORM 补齐 `canonical_url` partial unique index |
| `F7` 周窗口只依赖 `created_at` | `RESOLVED` | workflow / cluster / retrieval 改为优先 `published_at`，缺失时回退 `created_at` |

### 2.2 回归验证

已完成的回归验证包括：

- `python scripts/run_demo_flow.py`
  结果：`demo_final_status=completed`，`demo_trace_item_count=3`
- `python scripts/run_module_06_validation.py`
  结果：scenario 1 完整闭环通过，scenario 2 reviewer 经一次纠偏后收敛为 `pass`
- `pytest -q`
  结果：`3 passed`

额外修复：

- demo / validation 脚本现在会在执行前重置数据库状态，避免旧数据污染 dedup / retrieval
- 脚本通过 `finally` 保证失败时也清理临时数据
- pytest fixture 在每个测试前后清库，避免跨测试污染

---

## 3. Findings

### F1. Weekly workflow 会把同一时间窗中的无关文档混进当前 run，输入边界不成立

严重程度：

- `High`

位置：

- [backend/app/services/cluster_service.py:44](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/cluster_service.py:44)
- [backend/app/workflows/weekly_report/nodes.py:155](\/Users\/sz\/Code\/insight-flow\/backend\/app\/workflows\/weekly_report\/nodes.py:155)

问题：

- `collect_inputs_node` 在未显式传入 `input_document_ids` 时，会按 `Document.created_at` 抓整周文档
- 更关键的是，`build_weekly_clusters()` 根本不使用当前 run 的 `accepted_document_ids`，而是重新按时间窗扫描全库中所有 `accepted + primary` 文档
- 这意味着：
  - 即使 workflow 明确只处理某一组文档
  - cluster 和最终 report 仍可能混入同周其他 run 的文档

影响：

- 周报内容不再是当前 workflow 的可解释结果
- 同一周多次运行会互相污染
- “输入什么，产出什么”的产品语义不成立

建议：

- `build_weekly_clusters()` 改为显式接收 `document_ids`
- cluster 构建只允许基于当前 run 的 accepted primary documents
- 时间窗只作为过滤辅助条件，不应作为唯一数据边界

---

### F2. Cluster rebuild 会直接删除同一时间窗已有 clusters，多个 workflow run 之间会互相覆盖

严重程度：

- `High`

位置：

- [backend/app/services/cluster_service.py:56](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/cluster_service.py:56)

问题：

- 当前实现会在每次构建 cluster 时，先删除同一 `window_start/window_end` 下已有的 `clusters` 和 `cluster_items`
- 这个设计默认假设：
  - 一个时间窗只会有一个有效 cluster 集合
  - 并且没有并发 run、没有重跑历史窗口、没有多版本对比

影响：

- 同周第二次 run 会破坏第一次 run 的聚类结果
- 已生成 report 中引用的 `cluster_id` 可能被 `SET NULL`
- workflow 之间不是隔离关系，而是共享并覆盖同一批 cluster 数据

建议：

- 给 `Cluster` 增加 `workflow_run_id` 或 `cluster_set_id`
- 让 cluster 成为“某次 run 的产物”，而不是“某个时间窗的全局单例”
- 只有在明确做 rebuild/replace 操作时才允许清理旧数据

---

### F3. Reviewer loop 没有真正的修正动作，只会重复生成同一份草稿直到达到最大重试次数

严重程度：

- `High`

位置：

- [backend/app/workflows/weekly_report/graph.py:91](\/Users\/sz\/Code\/insight-flow\/backend\/app\/workflows\/weekly_report\/graph.py:91)
- [backend/app/services/report_draft_service.py:22](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/report_draft_service.py:22)
- [backend/app/workflows/weekly_report/nodes.py:418](\/Users\/sz\/Code\/insight-flow\/backend\/app\/workflows\/weekly_report\/nodes.py:418)

问题：

- reviewer 返回 `conclusion_too_strong` 或 `too_redundant` 后，graph 会回到 `draft_weekly_report`
- 但当前 draft 是 deterministic template，没有任何输入变化：
  - 没有降低措辞强度
  - 没有过滤重复项
  - 没有基于 reviewer checks 修改 context
- 所以下一次 draft 与上一次本质相同

影响：

- reviewer loop 是“形式成立，语义不成立”
- 实际结果是固定重试 2 次后再降级到人工编辑
- 这会制造额外 report 记录和 event 记录，但不会提升质量

建议：

- 在 reviewer 返回非 `pass` 时，对 draft step 注入修正指令
- 至少支持两类 patch：
  - `conclusion_too_strong` -> 降低绝对化措辞
  - `too_redundant` -> 去掉重复 cluster/report item
- 如果不做真正修正，就不要回环，直接进入 `human_edit`

---

### F4. `workflow_runs.retry_count` 从未同步更新，前端看到的重试次数是错误的

严重程度：

- `Medium`

位置：

- [backend/app/workflows/weekly_report/nodes.py:418](\/Users\/sz\/Code\/insight-flow\/backend\/app\/workflows\/weekly_report\/nodes.py:418)
- [backend/app/services/workflow_service.py:57](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/workflow_service.py:57)
- [backend/app/api/schemas/workflow_runs.py:17](\/Users\/sz\/Code\/insight-flow\/backend\/app\/api\/schemas\/workflow_runs.py:17)

问题：

- retry 只写进 `state_json["retry_count"]`
- `workflow_runs.retry_count` 这个实体字段没有同步更新
- 但前端 `Workflow Runs` 页面读的是表字段，不是 `state_json`

影响：

- UI/查询层看到的 retry_count 不可信
- 数据模型和真实状态分裂
- 后续如果要按 retry_count 做监控、排序、告警，会得到错误结果

建议：

- 在 `update_workflow_run_state()` 里同步 `workflow_run.retry_count = state_json.get("retry_count", 0)`
- 或者彻底删掉表字段，只保留 state_json 一处真相源

---

### F5. 异常场景下 trace 上下文被提前清空，错误日志会丢失 request_id / trace_id

严重程度：

- `Medium`

位置：

- [backend/app/api/middleware.py:28](\/Users\/sz\/Code\/insight-flow\/backend\/app\/api\/middleware.py:28)
- [backend/app/api/error_handlers.py:49](\/Users\/sz\/Code\/insight-flow\/backend\/app\/api\/error_handlers.py:49)

问题：

- middleware 在 `except Exception` 分支中先 `clear_request_context()`，再 `raise`
- 后续异常处理器仍然会记录错误，但日志 filter 里的 contextvars 已经变成 `-`
- 返回体里的 `request_id/trace_id` 还在，因为它来自 `request.state`
- 但日志行本身已经失去关联 id

影响：

- 最重要的失败日志反而最难查
- “返回体可追溯”和“日志可追溯”发生分裂
- 这违反了项目自己定下来的 traceability 共识

建议：

- 不要在异常分支里提前清空 context
- 把 `clear_request_context()` 放到 finally 或响应完成后统一执行

---

### F6. ORM model 与 migration 存在 drift：`canonical_url` 的唯一性只存在于 migration，不存在于 model

严重程度：

- `Medium`

位置：

- [backend/app/db/models/document.py:30](\/Users\/sz\/Code\/insight-flow\/backend\/app\/db\/models\/document.py:30)
- [backend/alembic/versions/20260416_0001_initial_schema.py:107](\/Users\/sz\/Code\/insight-flow\/backend\/alembic\/versions\/20260416_0001_initial_schema.py:107)
- [backend/app/services/document_service.py:64](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/document_service.py:64)

问题：

- 代码逻辑假设 `canonical_url` 冲突会触发 `IntegrityError`
- migration 里确实创建了部分唯一索引 `uq_documents_canonical_url_not_null`
- 但 ORM `Document.__table_args__` 里没有对应唯一约束/索引定义

影响：

- model 和真实 schema 不一致
- 后续如果根据 model autogenerate migration，容易把这个约束意外删掉
- 文档和代码理解成本提高

建议：

- 在 ORM 层补齐对应的 partial unique index 说明或显式声明
- 至少在 schema 文档里明确“这是 migration-managed constraint”

---

### F7. Weekly window 依赖 `created_at` 而不是 `published_at`，会导致报告按入库时间而不是事件时间聚合

严重程度：

- `Medium`

位置：

- [backend/app/workflows/weekly_report/nodes.py:158](\/Users\/sz\/Code\/insight-flow\/backend\/app\/workflows\/weekly_report\/nodes.py:158)
- [backend/app/services/cluster_service.py:47](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/cluster_service.py:47)
- [backend/app/services/retrieval_service.py:38](\/Users\/sz\/Code\/insight-flow\/backend\/app\/services\/retrieval_service.py:38)

问题：

- workflow 的周窗口判断核心使用的是 `Document.created_at`
- 对 URL/RSS 文档，更合理的语义通常应该优先用 `published_at`
- 当前实现实际上更接近“这周导入了什么”，而不是“这周发生了什么”

影响：

- 补录旧文章会被错误计入本周
- 延迟抓取会让历史事件出现在错误的周报里
- 历史检索窗口也会偏向“入库时间”而非“事件时间”

建议：

- 明确区分：
  - ingest-time workflow
  - publication-time workflow
- 对研究型产品，默认应优先使用 `published_at`，缺失时再退回 `created_at`

---

## 4. 其他风险与缺口

这些不一定是立即的 bug，但在严格标准下属于明显缺口。

### R1. 缺少正式测试套件

当前验证主要依赖：

- demo script
- validation script
- 手工联调

仓库里没有系统化的后端测试目录和前端测试目录。当前可以证明“能跑”，但还不能证明“改完不会坏”。

### R2. 验证脚本会向真实数据库写入演示数据

位置：

- [backend/scripts/run_demo_flow.py](\/Users\/sz\/Code\/insight-flow\/backend\/scripts\/run_demo_flow.py)
- [backend/scripts/run_module_06_validation.py](\/Users\/sz\/Code\/insight-flow\/backend\/scripts\/run_module_06_validation.py)

风险：

- 如果在共享/长期使用的数据库上执行，会污染真实数据集
- 当前没有 cleanup / sandbox database / fixture namespace

### R3. runtime artifacts 持续累积

位置：

- [backend/runtime_exports/reports](/Users/sz/Code/insight-flow/backend/runtime_exports/reports)
- [backend/runtime_exports/validation](/Users/sz/Code/insight-flow/backend/runtime_exports/validation)

风险：

- demo / validation 产物会不断堆积
- 没有 retention 或归档策略

---

## 5. 优先级建议

如果按最严格的工程优先级，我建议先修这四件事：

1. 修 `F1 + F2`
   先把 workflow 输入边界和 cluster 隔离性修正
2. 修 `F5`
   确保异常日志不丢 trace
3. 修 `F4`
   让 workflow run 的 retry_count 与真实状态一致
4. 决策 `F3`
   要么给 reviewer loop 增加真实修正动作，要么取消回环

之后再处理：

5. 修 `F6`
   消除 model/migration drift
6. 修 `F7`
   明确周窗口时间语义
7. 补测试套件和 demo 数据隔离

---

## 6. 总结

当前 Insight Flow MVP 的主要问题不是“功能不全”，而是：

- 有些能力已经存在外形，但还没有形成严格的工程闭环

尤其是：

- workflow 输入边界
- reviewer 回路有效性
- 状态持久化一致性
- 失败时的 trace 完整性

这些问题如果不修，项目虽然可以演示，但在严格标准下还不能算“可长期信任”的研究工作流系统。
