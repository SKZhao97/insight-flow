# Insight Flow 模块 06 执行与验证记录

## 1. 目的

这份文档记录模块 06 已完成的联调与收尾工作，也就是：

- `M06-01 ~ M06-07`

当前阶段的目标是把 MVP 从“主要功能已完成”推进到“可复跑、可演示、可追溯”的状态。

---

## 2. 当前范围

对应任务板：

- `M06-01` 端到端联调 ingest -> report
- `M06-02` 测试 workflow checkpoint 恢复
- `M06-03` 测试 reviewer 回路
- `M06-04` 验证引用链与来源回溯
- `M06-05` 基础异常处理补齐
- `M06-06` 补 README / 运行说明
- `M06-07` 补最小演示数据或演示脚本

当前状态：

- 模块 06 已完成
- MVP 六个模块整体已收口
- 后续自查修复已补齐验证脚本隔离、pytest 集成测试与 reviewer corrective loop 验证

---

## 3. 本轮新增内容

### 3.1 基础异常处理

新增：

- [backend/app/api/error_handlers.py](/Users/sz/Code/insight-flow/backend/app/api/error_handlers.py)

接入：

- [backend/app/main.py](/Users/sz/Code/insight-flow/backend/app/main.py)

当前行为：

- `RequestValidationError` 返回结构化 `422`
- 未捕获异常返回结构化 `500`
- 返回体附带 `request_id / trace_id`
- 同步写入统一错误日志

### 3.2 报告引用链 Trace API

新增：

- [backend/app/api/routes/report.py](/Users/sz/Code/insight-flow/backend/app/api/routes/report.py)
- [backend/app/api/schemas/report.py](/Users/sz/Code/insight-flow/backend/app/api/schemas/report.py)
- [backend/app/services/report_service.py](/Users/sz/Code/insight-flow/backend/app/services/report_service.py)

新增接口：

- `GET /reports/{report_id}/trace`

作用：

- 显式返回 `report -> report_items -> summary -> document -> source_url`
- 让来源回溯不再只存在于数据库内部

### 3.3 演示脚本

新增：

- [backend/scripts/run_demo_flow.py](/Users/sz/Code/insight-flow/backend/scripts/run_demo_flow.py)

作用：

- 创建演示数据
- 处理文档
- 运行 weekly workflow
- 从 `human_edit` checkpoint 恢复
- 打印导出路径和 trace item 数量
- 运行前清空应用数据，避免旧数据污染 dedup / retrieval
- 通过 `finally` 保证即使脚本失败也会清理数据库中的临时数据

### 3.4 模块 06 验证脚本

新增：

- [backend/scripts/run_module_06_validation.py](/Users/sz/Code/insight-flow/backend/scripts/run_module_06_validation.py)

作用：

- 执行模块 06 的四类核心验证
- 将结果写出为 JSON 证明文件
- 运行前重置数据库状态
- 通过 `finally` 保证失败时也清理测试数据

### 3.5 Pytest 集成测试

新增：

- [backend/tests/conftest.py](/Users/sz/Code/insight-flow/backend/tests/conftest.py)
- [backend/tests/test_mvp_integration.py](/Users/sz/Code/insight-flow/backend/tests/test_mvp_integration.py)

作用：

- 验证端到端 weekly workflow
- 验证 reviewer corrective loop
- 验证异常响应仍保留 `request_id / trace_id`
- 通过测试 fixture 在每个测试前后重置数据库状态，消除数据污染
### 3.6 运行说明

新增：

- [README.md](/Users/sz/Code/insight-flow/README.md)

作用：

- 给出完整运行方式
- 说明 demo / validation 脚本怎么执行
- 说明关键 API 和目录结构

---

## 4. 实际验证场景

## 4.1 场景 A：Demo Flow

验证方式：

- 运行 `python scripts/run_demo_flow.py`

验证目标：

- 最小演示链路真实可跑
- `run -> human_edit -> resume -> export -> trace` 闭环成立

结果摘要：

```text
demo_final_status completed
demo_trace_item_count 3
demo_export_exists True
```

## 4.2 场景 B：端到端 ingest -> report

验证方式：

- 运行 `python scripts/run_module_06_validation.py`
- Scenario 1 使用隔离时间窗和独立测试数据

验证目标：

- 手动文本输入能经过完整处理链路
- weekly workflow 能暂停并恢复
- 最终 report 能导出

结果摘要：

```text
scenario_1_final_status completed
scenario_1_export_exists True
```

## 4.3 场景 C：Workflow Checkpoint Recovery

验证目标：

- `run` 调用后停在 `waiting_human_edit`
- `resume` 从 Postgres checkpoint 恢复
- 最终 workflow 状态变为 `completed`

结果摘要：

- `checkpoint_state.status = waiting_human_edit`
- `resume_payload.status = completed`

## 4.4 场景 D：Reviewer 回路

验证目标：

- 构造包含过强措辞的样本
- reviewer 首次识别 `conclusion_too_strong`
- graph 回到 `draft_weekly_report` 并注入 `soften_language` 约束
- 二次审查后收敛为 `pass`
- workflow 最终进入 `human_edit`

结果摘要：

```text
scenario_2_review_decision pass
scenario_2_retry_count 1
```

示例日志：

```text
review.completed ... decision=conclusion_too_strong
report.drafted ... version=2
review.completed ... decision=pass
```

## 4.5 场景 E：引用链与来源回溯

验证目标：

- `GET /reports/{report_id}/trace` 返回 report provenance
- 每个 `report_item` 都具备：
  - `summary_id`
  - `document_id`
  - `source_url`
- `summary.document_id == report_item.document_id`

结果摘要：

```text
scenario_1_trace_items 2
citation_validation.mismatch_count 0
```

---

## 5. 证明文件

模块 06 验证脚本会写出 JSON 证明文件。

本轮生成的证明文件：

- [module_06_validation_20260418_220458.json](/Users/sz/Code/insight-flow/backend/runtime_exports/validation/module_06_validation_20260418_220458.json)

这个文件包含：

- scenario 1 run / checkpoint / resume 结果
- trace API payload
- citation validation 结果
- scenario 2 reviewer loop 结果

---

## 6. 当前结论

模块 06 已证明：

- MVP 已具备真实端到端闭环
- checkpoint 恢复不是概念设计，而是实际可运行能力
- reviewer loop 会在高风险措辞下起作用，并且能在最大重试次数后安全降级到人工编辑
- report provenance 已可通过 API 直接查看
- 仓库已具备 README、演示脚本、验证脚本和证明文件

当前可以把 Insight Flow MVP 视为：

- 可运行
- 可演示
- 可追溯
- 可测试
- 可继续迭代

额外验证结论：

- `pytest -q` 已通过，当前结果为 `3 passed`
- demo / validation 脚本会在执行前重置数据库，在结束或异常时清理临时数据
- 自查中暴露的 reviewer loop 空转、workflow 输入边界和测试污染问题已修正

---

## 7. 关联文档

- [docs/planning/insight_flow_mvp_task_board.md](./insight_flow_mvp_task_board.md)
- [docs/planning/insight_flow_logging_and_traceability_convention.md](./insight_flow_logging_and_traceability_convention.md)
- [docs/architecture/insight_flow_mvp_technical_design.md](../architecture/insight_flow_mvp_technical_design.md)
