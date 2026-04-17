# Insight Flow 开发日志与可追溯性约定

## 1. 目的

这份文档定义 Insight Flow 项目在开发、调试、测试、联调和问题排查中的统一留痕要求。

目标不是“多打日志”，而是保证：

- 行为可追溯
- 问题可复盘
- 上下文可还原
- 关键链路可定位
- 后续多人或多 agent 并行开发时不丢信息

---

## 2. 统一共识

从现在开始，以下活动都必须留下可追溯记录：

- 功能开发
- 本地调试
- 数据迁移
- 工作流执行
- 外部抓取
- 模型调用
- RAG 检索
- Reviewer 审查
- 测试执行
- 错误处理与重试

结论：

- 不允许只凭终端瞬时输出判断问题
- 不允许只在对话里口头描述问题而不落日志
- 不允许关键任务执行后没有 run id、step id 或 error context

---

## 3. 分层日志要求

## 3.1 应用层日志

适用范围：

- API 请求
- service 调用
- 定时任务
- workflow 节点执行

最低要求：

- `timestamp`
- `level`
- `module`
- `event`
- `trace_id`
- `request_id` 或 `workflow_run_id`
- 关键对象 id，如 `source_id`、`document_id`、`report_id`
- 结果状态，如 `success` / `failed` / `skipped`

推荐原则：

- 优先结构化日志
- 日志内容要能让人不看代码也知道当前在做什么
- 不记录大段正文原文，避免噪音和敏感信息泄漏

---

## 3.2 工作流层日志

适用范围：

- LangGraph 节点执行
- graph 中断与恢复
- reviewer 回路
- human-in-the-loop 节点

最低要求：

- `workflow_run_id`
- `node_name`
- `node_attempt`
- `input_summary`
- `output_summary`
- `decision`
- `elapsed_ms`
- `error_type`
- `checkpoint_id` 或可恢复标识

必须保证：

- 每个节点进入时有日志
- 每个节点成功结束时有日志
- 每个节点失败时有错误日志
- 每次 resume 时能看出从哪个 checkpoint 继续

---

## 3.3 数据层日志

适用范围：

- migration
- 批量写库
- 去重归并
- embedding 写入
- 检索记录落库

最低要求：

- 操作类型
- 目标表
- 影响记录数
- 关键 id 范围或批次号
- 失败原因

要求：

- 重要批处理必须打印总数、成功数、失败数、跳过数
- 去重和归并必须能追溯“谁被合并进谁”

---

## 3.4 调试与测试日志

适用范围：

- 本地手工调试
- 集成测试
- E2E 测试
- 回归测试

最低要求：

- 测试名称
- 输入条件
- 预期结果
- 实际结果
- 失败样例
- 关联代码版本或时间点

要求：

- 不能只说“测过了”
- 至少要能说明“测了什么、怎么测的、结果怎样”

---

## 4. 核心追踪字段

建议后续统一采用以下追踪字段：

| 字段 | 含义 |
| --- | --- |
| `trace_id` | 单次完整调用链的追踪 id |
| `request_id` | 单个 API 请求 id |
| `workflow_run_id` | 单次 workflow 运行 id |
| `node_name` | 当前 workflow 节点名 |
| `source_id` | 来源 id |
| `document_id` | 文档 id |
| `summary_id` | 摘要 id |
| `cluster_id` | 事件簇 id |
| `report_id` | 报告 id |
| `retrieval_id` | 检索记录 id |
| `model_name` | 本次调用的模型名 |
| `provider` | 模型供应方 |
| `latency_ms` | 耗时 |
| `status` | 成功、失败、跳过、重试 |

---

## 5. 关键链路的必打日志

以下链路必须保证日志完整：

### 5.1 摄入链路

- 收到输入
- 开始抓取
- 抓取成功或失败
- 正文提取结果
- normalization 结果
- 质量评分结果
- 去重结果
- 是否进入分析

### 5.2 分析链路

- 开始调用模型
- 模型返回成功或失败
- 输出结构校验结果
- 摘要/标签/分类持久化结果
- chunk 与 embedding 写入结果

### 5.3 RAG 链路

- 检索 query
- 检索命中条数
- summary 命中结果
- source chunk 回填结果
- context pack 构建结果

### 5.4 周报 workflow 链路

- graph 启动
- 每个节点执行与耗时
- reviewer 判定结果
- 是否进入人工编辑
- markdown 导出结果

---

## 6. 错误日志要求

错误日志至少要包含：

- 错误发生位置
- 输入上下文摘要
- 异常类型
- 异常消息
- 是否可重试
- 当前重试次数
- 关联对象 id

要求：

- 不要只打 `str(e)`
- 对外部依赖错误要区分是网络、权限、解析、模型响应还是数据库错误

---

## 7. 落地要求

后续实现时，至少要同步落地这些内容：

1. `backend/app/core/logging.py`
   统一日志格式与 logger 获取方式
2. API middleware
   注入 `request_id` / `trace_id`
3. workflow 节点包装器
   统一打印节点开始、结束、失败日志
4. LLM 调用封装
   记录模型、耗时、结果状态、token 使用
5. repository/service 层关键操作日志
   记录持久化和批处理结果
6. 测试记录规范
   在任务推进时明确记录验证方式和结果

---

## 8. 执行原则

后续开发遵循下面三条：

1. 先定义日志点，再实现主逻辑
2. 新模块上线前，至少保证主成功路径和主失败路径都有日志
3. 没有可追溯信息的实现，不视为真正完成

---

## 9. 当前结论

这份文档从现在起作为项目共识执行。

后续我在这个项目里的开发、调试、测试、联调和排障，会默认把日志与追踪作为交付的一部分，而不是附属工作。
