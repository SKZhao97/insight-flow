# Insight Flow 模块技术栈与学习地图

## 1. 文档目的

本文档用于回答三个问题：

1. 每个模块会用到哪些技术栈
2. 为实现该模块需要学习哪些知识点
3. 对应有哪些值得优先看的学习资源

本文档按“模块 -> 技术栈 -> 学习点 -> 推荐资源”组织，资源优先官方文档。

---

## 2. 学习优先级原则

不是所有技术都要同深度学习。

建议按三层优先级学习：

### P0：必须先掌握

- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 基础
- LangGraph 基础
- 结构化输出

### P1：实现时同步掌握

- pgvector
- RAG 设计
- trafilatura / feedparser
- React / Next.js 工作台页面

### P2：主闭环跑通后再深入

- Reviewer 优化
- 检索优化
- 异构模型策略
- 负反馈学习

---

## 3. 模块总览

| 模块 | 技术栈 | 学习优先级 |
| --- | --- | --- |
| 工程骨架 | FastAPI, Next.js, SQLAlchemy, Alembic | P0 |
| 数据模型 | PostgreSQL, SQLAlchemy, Alembic | P0 |
| 内容摄入 | httpx, feedparser, trafilatura | P1 |
| 质量评分与去重 | Embedding, pgvector, LLM structured output | P1 |
| 文档分析 | Prompt, structured output, provider abstraction | P0 |
| RAG 检索 | pgvector, retrieval design | P1 |
| LangGraph workflow | LangGraph, checkpoint, state machine | P0 |
| Reviewer | structured review schema, LLM evaluation | P1 |
| 前端工作台 | Next.js, React, TypeScript | P1 |
| 数据迁移与运维 | Alembic, PostgreSQL, logging | P0 |

---

## 4. 模块级学习地图

## 4.1 模块：工程骨架

### 用到的技术栈

- Python
- FastAPI
- Next.js
- TypeScript
- SQLAlchemy
- Alembic

### 需要学习的内容

- FastAPI 项目组织方式
- 路由、依赖注入、请求/响应模型
- Next.js App Router 基础
- TypeScript 基础类型约束
- SQLAlchemy 2.0 的 Declarative ORM
- Alembic migration 基础流程

### 推荐资源

- FastAPI 官方文档  
  https://fastapi.tiangolo.com/
- SQLAlchemy Unified Tutorial  
  https://docs.sqlalchemy.org/20/tutorial/index.html
- SQLAlchemy ORM 文档  
  https://docs.sqlalchemy.org/en/20/orm/
- Alembic 官方教程  
  https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Next.js 官方文档  
  https://nextjs.org/docs
- React 官方文档  
  https://react.dev/learn

### 学习建议

- 这部分不要追求“学全”
- 目标是能搭起项目骨架并稳定增量迭代

---

## 4.2 模块：数据模型与数据库

### 用到的技术栈

- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- pgvector

### 需要学习的内容

- PostgreSQL 常用类型
  `jsonb / array / timestamptz / uuid`
- 索引设计
- 外键与 cascade
- SQLAlchemy relationship
- migration 设计与变更顺序
- pgvector 的表设计与索引方式

### 推荐资源

- PostgreSQL 官方文档  
  https://www.postgresql.org/docs/
- SQLAlchemy Core 文档  
  https://docs.sqlalchemy.org/20/core/
- SQLAlchemy ORM 文档  
  https://docs.sqlalchemy.org/en/20/orm/
- Alembic 文档  
  https://alembic.sqlalchemy.org/en/latest/
- pgvector 官方仓库  
  https://github.com/pgvector/pgvector

### 学习建议

- 重点不是 SQL 炫技，而是把 schema 做稳定
- 对这个项目来说，数据库设计是核心资产之一

---

## 4.3 模块：内容摄入与抓取

### 用到的技术栈

- httpx
- feedparser
- trafilatura
- Jina Reader / Firecrawl fallback

### 需要学习的内容

- RSS 基本结构
- 网页抓取与正文抽取
- 抽取失败 fallback 设计
- canonical URL 处理
- 基础清洗和元数据提取

### 推荐资源

- httpx 文档  
  https://www.python-httpx.org/
- feedparser 文档  
  https://feedparser.readthedocs.io/
- trafilatura 文档  
  https://trafilatura.readthedocs.io/
- Jina Reader  
  https://jina.ai/reader/
- Firecrawl 文档  
  https://docs.firecrawl.dev/

### 学习建议

- 抓取模块先追求“稳”，不要追求全站通吃
- MVP 阶段只要对目标场景常见站点足够好用就够了

---

## 4.4 模块：质量评分与语义去重

### 用到的技术栈

- LLM structured output
- embedding
- pgvector
- similarity search

### 需要学习的内容

- 质量评分 prompt 设计
- 语义相似度基本概念
- 去重阈值怎么设
- supporting-source 与 duplicate 的区分
- embedding 存储与相似度查询

### 推荐资源

- OpenAI Structured Outputs 相关文档或等价 provider 文档
- pgvector 官方仓库  
  https://github.com/pgvector/pgvector
- SQLAlchemy + pgvector Python 库  
  https://github.com/pgvector/pgvector-python
- LangChain / LangGraph 检索相关文档  
  https://docs.langchain.com/

### 学习建议

- 先从简单阈值策略做起
- 不要一开始就追求复杂 rerank 或多路检索

---

## 4.5 模块：文档分析

### 用到的技术栈

- LLM provider abstraction
- structured output
- Prompt engineering
- Pydantic

### 需要学习的内容

- 如何让模型稳定输出摘要、标签、分类、关键观点
- 如何设计双语术语表输出
- 如何用 Pydantic 约束模型返回结构
- prompt versioning 的基本思路

### 推荐资源

- Pydantic 文档  
  https://docs.pydantic.dev/latest/
- FastAPI Request/Response Models  
  https://fastapi.tiangolo.com/tutorial/body/
- LangChain structured output / output parser 相关文档  
  https://docs.langchain.com/

### 学习建议

- 这是 MVP 的高频调用模块
- 先把结构化输出稳定性做出来，比 prompt 写得“华丽”更重要

---

## 4.6 模块：RAG 与检索

### 用到的技术栈

- pgvector
- summary retrieval
- chunk backfill
- hybrid retrieval

### 需要学习的内容

- RAG 在本项目中的真实职责
- 为什么先检索 summary，再回填原文 chunk
- 时间窗过滤 + 标签过滤 + 向量召回
- context pack 设计
- citation / 引用链回溯

### 推荐资源

- pgvector 官方仓库  
  https://github.com/pgvector/pgvector
- LangGraph / LangChain 检索文档  
  https://docs.langchain.com/
- PostgreSQL 文档  
  https://www.postgresql.org/docs/

### 学习建议

- 本项目的 RAG 重点不是聊天问答
- 重点是“历史资产复用”和“证据回溯”

---

## 4.7 模块：LangGraph workflow

### 用到的技术栈

- LangGraph
- state machine
- checkpoint persistence
- human-in-the-loop

### 需要学习的内容

- graph / node / edge / conditional edge
- state schema 设计
- durable execution
- checkpointer
- interrupt / resume
- 节点幂等性

### 推荐资源

- LangGraph Python Overview  
  https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph Docs Home  
  https://docs.langchain.com/oss/python/langgraph

### 学习建议

- 不要把 LangGraph 学成“框架 API 背诵”
- 重点理解：
  为什么这个项目需要显式状态、回路、人工中断和恢复

---

## 4.8 模块：Reviewer 审查

### 用到的技术栈

- structured review schema
- heterogenous models
- prompt constraints

### 需要学习的内容

- reviewer 和 generator 为什么最好解耦
- 如何设计 review checks
- `need_more_evidence / too_redundant / conclusion_too_strong`
  这种决策输出怎么做
- 如何避免 reviewer 只会说套话

### 推荐资源

- LangGraph 文档  
  https://docs.langchain.com/oss/python/langgraph/overview
- 各 LLM provider 的 structured output / JSON mode 文档

### 学习建议

- Reviewer 重点不是“文采”
- 重点是“路由决定是否可靠”

---

## 4.9 模块：前端工作台

### 用到的技术栈

- Next.js
- React
- TypeScript

### 需要学习的内容

- App Router
- 数据获取与基本状态管理
- 表单与编辑器页面组织
- 工作台型页面布局

### 推荐资源

- Next.js 官方文档  
  https://nextjs.org/docs
- React 官方文档  
  https://react.dev/learn
- TypeScript 官方文档  
  https://www.typescriptlang.org/docs/

### 学习建议

- MVP 前端重点是可用，不是炫 UI
- 优先保证文档列表、报告编辑、workflow 状态能跑通

---

## 4.10 模块：迁移、可观测性与运维

### 用到的技术栈

- Alembic
- structured logging
- PostgreSQL

### 需要学习的内容

- migration 变更顺序
- 环境配置管理
- workflow run 和 event log 的记录方式
- checkpoint 与 DB 快照的关系

### 推荐资源

- Alembic 文档  
  https://alembic.sqlalchemy.org/en/latest/
- SQLAlchemy 文档  
  https://docs.sqlalchemy.org/20/
- PostgreSQL 文档  
  https://www.postgresql.org/docs/

### 学习建议

- 这部分决定后续 debug 成本
- 对 Insight Flow 这种 workflow 系统来说，不是“附属能力”

---

## 5. 跨模块核心技术专题

## 5.1 RAG

### 本项目要学什么

- 不是通用 QA RAG
- 是“summary retrieval + source chunk backfill”
- 是“研究资产复用”的 RAG

### 推荐资源

- pgvector  
  https://github.com/pgvector/pgvector
- LangGraph / LangChain 检索文档  
  https://docs.langchain.com/

### 学习目标

- 能自己解释为什么不能只检索摘要
- 能实现双路上下文

---

## 5.2 LangGraph

### 本项目要学什么

- stateful workflow
- checkpoint
- interrupt / resume
- conditional routing

### 推荐资源

- LangGraph Python Overview  
  https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph Docs  
  https://docs.langchain.com/oss/python/langgraph

### 学习目标

- 能把 Weekly Report graph 跑起来
- 能解释为什么 `human_edit` 必须是 graph 正式节点

---

## 5.3 SQLAlchemy + Alembic

### 本项目要学什么

- Declarative ORM
- relationship
- session
- migration
- PostgreSQL 特性映射

### 推荐资源

- SQLAlchemy Unified Tutorial  
  https://docs.sqlalchemy.org/20/tutorial/index.html
- SQLAlchemy ORM  
  https://docs.sqlalchemy.org/en/20/orm/
- Alembic Tutorial  
  https://alembic.sqlalchemy.org/en/latest/tutorial.html

### 学习目标

- 能独立维护 schema 演进
- 不被 migration 和 relationship 卡住

---

## 5.4 PostgreSQL + pgvector

### 本项目要学什么

- jsonb
- array
- 索引设计
- ivfflat / hnsw
- 向量检索与业务表 join

### 推荐资源

- PostgreSQL 文档  
  https://www.postgresql.org/docs/
- pgvector  
  https://github.com/pgvector/pgvector
- pgvector Python  
  https://github.com/pgvector/pgvector-python

### 学习目标

- 能解释为什么 MVP 先用 PG + pgvector
- 能自己设计向量表与索引

---

## 6. 推荐学习顺序

最合理的补课顺序建议是：

1. FastAPI
2. SQLAlchemy 2.0
3. Alembic
4. PostgreSQL 基础
5. 文档抓取链路
6. 结构化输出
7. pgvector
8. LangGraph
9. Reviewer / RAG 优化
10. Next.js / React 工作台页面

原因：

- 先学后端主干
- 再学 AI 工作流
- 最后补前端体验

---

## 7. 最终建议

Insight Flow 这个项目涉及的技术不少，但不需要一开始全部学透。

更合理的方式是：

> 按模块开发顺序学习，每个阶段只补实现当前模块真正需要的知识。

因此后续执行时建议：

- 用 `insight_flow_implementation_order.md` 管实现排期
- 用这份学习地图补各模块的知识短板

这样不会陷入“先把所有 AI 工程知识学完再开始”的低效率路径。
