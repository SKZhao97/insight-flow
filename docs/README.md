# Insight Flow 文档索引

## 1. 文档目录说明

当前项目文档按用途分为四类：

- `product/`
  产品定位、价值分析、PRD 与场景定义
- `architecture/`
  技术方案、workflow、数据库和 ORM 设计
- `planning/`
  版本路线图、实现顺序、学习地图、模块实现 spec
- `archive/`
  早期讨论稿与历史版本归档

---

## 2. 推荐阅读顺序

如果第一次进入项目，建议按下面顺序阅读。

### 第一步：理解项目是什么

1. [foundation_prd](./product/insight_flow_foundation_prd.md)
2. [value_analysis](./product/insight_flow_value_analysis.md)
3. [vs_gpt_analysis](./product/insight_flow_vs_gpt_analysis.md)
4. [vertical_scenario_analysis](./product/insight_flow_vertical_scenario_analysis.md)

### 第二步：理解 MVP 和技术方向

1. [mvp_technical_design](./architecture/insight_flow_mvp_technical_design.md)
2. [version_roadmap](./planning/insight_flow_version_roadmap.md)
3. [implementation_order](./planning/insight_flow_implementation_order.md)

### 第三步：理解关键实现细节

1. [langgraph_detailed_design](./architecture/insight_flow_langgraph_detailed_design.md)
2. [m04_technical_design_details](./architecture/insight_flow_m04_technical_design_details.md)
3. [database_schema_design](./architecture/insight_flow_database_schema_design.md)
4. [sqlalchemy_models_draft](./architecture/insight_flow_sqlalchemy_models_draft.md)
5. [current_codebase_walkthrough](./architecture/insight_flow_current_codebase_walkthrough.md)
6. [database_table_flow](./architecture/insight_flow_database_table_flow.md)
7. [url_to_report_lifecycle](./architecture/insight_flow_url_to_report_lifecycle.md)
8. [schema_design_rationale](./architecture/insight_flow_schema_design_rationale.md)

### 第四步：进入具体开发

1. [module_01_project_bootstrap_spec](./planning/insight_flow_module_01_project_bootstrap_spec.md)
2. 后续模块 spec

---

## 3. 文档索引

## 3.1 Product

- [基础 PRD](./product/insight_flow_foundation_prd.md)
- [MVP PRD](./product/insight_flow_mvp_prd.md)
- [定位与 MVP 设计](./product/insight_flow_positioning_and_mvp.md)
- [项目价值分析](./product/insight_flow_value_analysis.md)
- [垂直场景分析](./product/insight_flow_vertical_scenario_analysis.md)
- [与 GPT 对比分析](./product/insight_flow_vs_gpt_analysis.md)

## 3.2 Architecture

- [MVP 技术方案](./architecture/insight_flow_mvp_technical_design.md)
- [LangGraph 详细设计](./architecture/insight_flow_langgraph_detailed_design.md)
- [M04 技术设计细节](./architecture/insight_flow_m04_technical_design_details.md)
- [数据库 Schema 设计](./architecture/insight_flow_database_schema_design.md)
- [SQLAlchemy Models 草案](./architecture/insight_flow_sqlalchemy_models_draft.md)
- [当前代码导读](./architecture/insight_flow_current_codebase_walkthrough.md)
- [数据库表流转关系梳理](./architecture/insight_flow_database_table_flow.md)
- [URL 到 Report 生命周期](./architecture/insight_flow_url_to_report_lifecycle.md)
- [Schema 设计动机详解](./architecture/insight_flow_schema_design_rationale.md)

## 3.3 Planning

- [版本路线图](./planning/insight_flow_version_roadmap.md)
- [实现顺序规划](./planning/insight_flow_implementation_order.md)
- [模块技术栈与学习地图](./planning/insight_flow_module_learning_map.md)
- [开发日志与可追溯性约定](./planning/insight_flow_logging_and_traceability_convention.md)
- [模块 01 实现 Spec](./planning/insight_flow_module_01_project_bootstrap_spec.md)
- [模块 03 执行与验证记录](./planning/insight_flow_module_03_execution_log.md)
- [模块 04 执行与验证记录](./planning/insight_flow_module_04_execution_log.md)

## 3.4 Archive

- [项目讨论原稿](./archive/insight_flow_project_discussion.md)
- [项目讨论增强版](./archive/insight_flow_project_discussion_enhanced.md)

---

## 4. 开发阶段怎么用这些文档

### 如果要确认方向

优先看：

- `product/foundation_prd`
- `product/value_analysis`
- `product/vs_gpt_analysis`

### 如果要开始实现

优先看：

- `planning/implementation_order`
- `architecture/mvp_technical_design`
- 当前模块对应的 `planning/module_xx_spec`

### 如果要实现后端核心逻辑

优先看：

- `architecture/langgraph_detailed_design`
- `architecture/m04_technical_design_details`
- `architecture/database_schema_design`
- `architecture/sqlalchemy_models_draft`
- `architecture/current_codebase_walkthrough`
- `architecture/database_table_flow`
- `architecture/url_to_report_lifecycle`
- `architecture/schema_design_rationale`

---

## 5. 当前项目状态

当前已经完成：

- 项目定位与价值分析
- MVP 范围定义
- 版本路线图
- MVP 技术方案
- LangGraph 详细设计
- 数据库 Schema 设计
- SQLAlchemy model 草案
- 模块 01 实现 spec
- 后端工程骨架初始化
- 模块 03：摄入与分析主链路
- 模块 04：服务层与节点层

接下来主要推进方向：

- 模块 05：前端工作台与前后端联调

当前执行约束：

- 开发、调试、测试、联调与排障必须遵循 `planning/logging_and_traceability_convention`

---

## 6. 文档维护原则

后续新增文档时，建议遵循：

- 产品文档放 `product/`
- 技术设计放 `architecture/`
- 执行计划与模块 spec 放 `planning/`
- 旧版本和讨论稿放 `archive/`

这样项目根目录就能保持干净，文档结构也更容易长期维护。
