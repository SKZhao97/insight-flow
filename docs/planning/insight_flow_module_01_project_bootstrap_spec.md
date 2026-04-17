# Insight Flow 模块 01 实现 Spec

## 1. 模块名称

`Project Bootstrap`

中文可称为：

`工程骨架模块`

---

## 2. 模块目标

本模块的目标不是实现业务能力，而是为后续所有模块提供稳定的工程基础。

完成后，项目应具备：

- 可运行的后端服务骨架
- 可连接的 PostgreSQL 数据库配置
- 可复用的 SQLAlchemy 基础设施
- 可执行的 Alembic 迁移体系
- 基础日志与环境变量加载
- 一个最小健康检查 API

一句话定义：

> 先把项目从“空目录”变成“可启动、可迁移、可扩展”的后端工程。

---

## 3. 模块边界

## 3.1 本模块要做什么

- 建立后端目录结构
- 建立配置加载机制
- 建立数据库 engine / session
- 建立 SQLAlchemy Base / Mixins / Enums / Types
- 初始化 Alembic
- 建立 FastAPI 应用入口
- 增加健康检查接口
- 增加基础日志配置

## 3.2 本模块不做什么

- 不写任何业务 model
- 不写 Source / Document / Report 等表
- 不写抓取逻辑
- 不写 LangGraph workflow
- 不写前端页面
- 不接入 LLM provider

这点非常关键。

这个模块只做底座，不碰业务闭环。

---

## 4. 前置依赖

本模块无业务前置依赖。

但默认需要：

- Python 环境可用
- PostgreSQL 本地或可访问实例可用
- 包管理方式已选定
  建议统一为 `uv` 或 `poetry` 或 `pip + venv`

---

## 5. 建议目录结构

建议先搭出后端最小结构：

```text
backend/
  app/
    api/
      routes/
        health.py
    core/
      config.py
      logging.py
    db/
      base.py
      session.py
      mixins.py
      enums.py
      types.py
      models/
        __init__.py
    main.py
  alembic/
  alembic.ini
```

说明：

- `api/`：放路由
- `core/`：放配置和日志
- `db/`：放数据库基础设施
- `models/`：先留空壳，后续模块再填

---

## 6. 交付物

本模块完成后，至少应交付以下内容：

## 6.1 后端应用入口

- `backend/app/main.py`

功能：

- 创建 FastAPI app
- 注册基础路由
- 暴露健康检查接口

## 6.2 配置模块

- `backend/app/core/config.py`

功能：

- 从环境变量读取配置
- 至少支持：
  - `APP_ENV`
  - `DATABASE_URL`
  - `LOG_LEVEL`

## 6.3 日志模块

- `backend/app/core/logging.py`

功能：

- 初始化结构化或统一格式日志
- 在 app 启动时加载

## 6.4 DB 基础设施

- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/mixins.py`
- `backend/app/db/enums.py`
- `backend/app/db/types.py`

功能：

- `DeclarativeBase`
- naming convention
- engine / sessionmaker
- UUID 主键 mixin
- timestamp mixin
- PostgreSQL 类型封装

## 6.5 Alembic 初始化

- `backend/alembic/`
- `backend/alembic.ini`

功能：

- Alembic 可运行
- 可自动发现 `Base.metadata`

## 6.6 健康检查路由

- `backend/app/api/routes/health.py`

功能：

- 至少提供：
  - `GET /health`
  - 返回应用运行状态

---

## 7. 技术栈

本模块会用到：

- Python
- FastAPI
- Pydantic / pydantic-settings
- SQLAlchemy 2.0
- Alembic
- PostgreSQL

可选：

- `uv` 作为包管理与运行工具

---

## 8. 实现顺序

建议按以下顺序实现：

1. 建立后端目录结构
2. 初始化依赖管理与 Python 环境
3. 写 `config.py`
4. 写 `logging.py`
5. 写 `db/base.py`
6. 写 `db/session.py`
7. 写 `db/mixins.py / enums.py / types.py`
8. 写 `main.py`
9. 写 `health.py`
10. 初始化 Alembic
11. 验证服务启动与数据库连接

---

## 9. 可并行拆分

如果交给多个 agent，可按下面拆：

### Agent A：后端应用骨架

负责：

- `main.py`
- `health.py`
- `config.py`
- `logging.py`

### Agent B：数据库基础设施

负责：

- `base.py`
- `session.py`
- `mixins.py`
- `enums.py`
- `types.py`
- Alembic 初始化

要求：

- 两边都不要改未来业务 model
- 通过约定的 import 结构对齐

---

## 10. 验收标准

本模块完成的最低验收标准：

1. 后端服务可以本地启动
2. `GET /health` 可以返回成功响应
3. 应用可以成功读取 `DATABASE_URL`
4. SQLAlchemy engine / session 能初始化
5. Alembic 可以成功执行基础命令
   例如 `current`、`revision --autogenerate` 的准备工作完成
6. 项目目录结构稳定，后续可直接往 `models/` 和 `services/` 扩展

---

## 11. 风险点

本模块最容易出问题的地方：

- 配置加载方式不统一
- `Base.metadata` 与 Alembic 没接通
- session 管理后面不好扩展
- 提前写了业务代码，把骨架模块做重

因此本模块应坚持：

> 只做通用底座，不做业务对象。

---

## 12. 完成后的下一模块

本模块完成后，下一步进入：

`数据与模型模块`

也就是开始实现：

- Source
- Document
- Summary
- Chunk
- Report
- WorkflowRun

对应的 SQLAlchemy model 与 migration。

---

## 13. 最终说明

这个模块虽然“看起来不产出功能”，但它决定了后面所有实现的稳定性。

如果这一层搭得干净，后续：

- schema 演进
- workflow 接入
- report API
- 前端联调

都会顺很多。

所以这个模块的目标不是快，而是稳。
