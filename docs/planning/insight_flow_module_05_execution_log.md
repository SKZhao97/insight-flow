# Insight Flow 模块 05 第一阶段执行与验证记录

## 1. 目的

这份文档记录模块 05 当前已完成阶段，也就是：

- `M05-01 ~ M05-09`

当前已完成的实现和验证证据。

这一阶段的目标不是一次性做完所有交互，而是先把前端工作台真正搭起来，并让它能消费当前后端 API。

---

## 2. 当前范围

对应任务板：

- `M05-01 ~ M05-08`

当前状态：

- 前端项目骨架已建立
- 基础布局与导航已完成
- `Sources / Documents / Reports / Report Detail / Workflow Runs` 页面已完成
- report markdown 下载入口已完成
- 前后端 dev 联调已完成
- 模块 05 总体已完成

---

## 3. 本轮新增内容

新增前端工程：

- [frontend/package.json](/Users/sz/Code/insight-flow/frontend/package.json)
- [frontend/vite.config.ts](/Users/sz/Code/insight-flow/frontend/vite.config.ts)
- [frontend/index.html](/Users/sz/Code/insight-flow/frontend/index.html)
- [frontend/src/main.tsx](/Users/sz/Code/insight-flow/frontend/src/main.tsx)
- [frontend/src/router.tsx](/Users/sz/Code/insight-flow/frontend/src/router.tsx)
- [frontend/src/styles.css](/Users/sz/Code/insight-flow/frontend/src/styles.css)

新增页面与 UI：

- [frontend/src/ui/AppShell.tsx](/Users/sz/Code/insight-flow/frontend/src/ui/AppShell.tsx)
- [frontend/src/ui/PageSection.tsx](/Users/sz/Code/insight-flow/frontend/src/ui/PageSection.tsx)
- [frontend/src/ui/StateViews.tsx](/Users/sz/Code/insight-flow/frontend/src/ui/StateViews.tsx)
- [frontend/src/pages/DashboardPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/DashboardPage.tsx)
- [frontend/src/pages/SourcesPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/SourcesPage.tsx)
- [frontend/src/pages/DocumentsPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/DocumentsPage.tsx)
- [frontend/src/pages/ReportsPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/ReportsPage.tsx)
- [frontend/src/pages/ReportDetailPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/ReportDetailPage.tsx)
- [frontend/src/pages/WorkflowRunsPage.tsx](/Users/sz/Code/insight-flow/frontend/src/pages/WorkflowRunsPage.tsx)

新增前端数据层：

- [frontend/src/lib/api.ts](/Users/sz/Code/insight-flow/frontend/src/lib/api.ts)
- [frontend/src/lib/format.ts](/Users/sz/Code/insight-flow/frontend/src/lib/format.ts)
- [frontend/src/hooks/useAsyncResource.ts](/Users/sz/Code/insight-flow/frontend/src/hooks/useAsyncResource.ts)
- [frontend/src/types.ts](/Users/sz/Code/insight-flow/frontend/src/types.ts)

为前端补充的后端只读 API：

- [backend/app/api/routes/report.py](/Users/sz/Code/insight-flow/backend/app/api/routes/report.py)
- [backend/app/api/routes/workflow_runs.py](/Users/sz/Code/insight-flow/backend/app/api/routes/workflow_runs.py)
- [backend/app/api/schemas/report.py](/Users/sz/Code/insight-flow/backend/app/api/schemas/report.py)
- [backend/app/api/schemas/workflow_runs.py](/Users/sz/Code/insight-flow/backend/app/api/schemas/workflow_runs.py)
- [backend/app/services/report_service.py](/Users/sz/Code/insight-flow/backend/app/services/report_service.py)
- [backend/app/services/workflow_run_service.py](/Users/sz/Code/insight-flow/backend/app/services/workflow_run_service.py)

---

## 4. 本轮实际验证场景

## 4.1 场景 A：后端前端支撑接口导入验证

验证目标：

- 新增 `reports / workflow-runs` 路由和 service 可正常导入
- FastAPI 入口接线正常

验证方式：

- `py_compile`
- 直接 import 路由函数

结果：

```text
frontend_supporting_api_imports_ok True True True
```

## 4.2 场景 B：前端依赖安装

验证目标：

- `frontend/` 工程依赖可正常安装

验证方式：

- `npm install`

结果：

```text
added 72 packages
found 0 vulnerabilities
```

## 4.3 场景 C：前端生产构建

验证目标：

- React + TypeScript + Vite 工程可以成功 build
- 页面、路由、样式、API 层不存在阻塞性类型错误

验证方式：

- `npm run build`

结果：

```text
vite v7.3.2 building client environment for production...
✓ 53 modules transformed.
dist/index.html
dist/assets/index-BM3ipy3e.css
dist/assets/index-cadiye9j.js
✓ built in 2.01s
```

## 4.4 场景 D：report markdown 下载入口验证

验证目标：

- 后端 `GET /reports/{report_id}/markdown` 路由可正常导入
- 前端 Report Detail 页面可稳定通过 build

验证方式：

- `py_compile`
- 直接 import `download_report_markdown`
- 再次执行 `npm run build`

结果：

```text
report_download_import_ok True
vite v7.3.2 building client environment for production...
✓ built in 1.32s
```

## 4.5 场景 E：前后端 dev 联调

验证目标：

- Vite dev server 能通过代理访问 FastAPI
- 前端基础页面依赖的关键接口都能从 `5173` 正常返回

验证方式：

1. 启动后端：
   - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
2. 启动前端：
   - `npm run dev -- --host 127.0.0.1 --port 5173`
3. 通过 `curl` 访问：
   - `http://127.0.0.1:5173/sources`
   - `http://127.0.0.1:5173/documents`
   - `http://127.0.0.1:5173/reports`
   - `http://127.0.0.1:5173/workflow-runs`

结果摘要：

```text
GET /sources        -> 200 with JSON payload
GET /documents      -> 200 with JSON payload
GET /reports        -> 200 with JSON payload
GET /workflow-runs  -> 200 with JSON payload
```

---

## 5. 当前已成立的页面能力

### 5.1 Dashboard

- 展示 Sources / Documents / Reports / Workflow Runs 统计
- 展示最新 report 与 latest workflow 快捷入口

### 5.2 Sources

- 展示 source 列表
- 展示 feed URL、状态、最近同步时间

### 5.3 Documents

- 展示文档 ingestion 状态
- 展示 quality / dedup / status 三类处理状态

### 5.4 Reports

- 展示 report 列表
- 支持跳转到 report detail

### 5.5 Report Detail

- 展示 Markdown 正文
- 展示 item-level source URL 引用

### 5.6 Workflow Runs

- 展示 workflow run 列表
- 展示 window、status、retry、start/finish 时间

### 5.7 Report Export Entry

- Report Detail 页面增加 markdown 下载入口
- 后端增加 `/reports/{report_id}/markdown` 下载接口

### 5.8 Frontend-Backend Integration

- Vite proxy 已能代理到 FastAPI
- 前端工作台当前依赖的核心只读接口都已通过 dev 联调验证

---

## 6. 当前实现边界

模块 05 现在已经整体完成。

当前结论是：

- 前端工程已建立
- 前端基础页面已建立
- report 下载入口已建立
- 前后端 dev 联调已通过

此外，这一版前端仍然以“工作台浏览”优先，没有加入复杂交互表单。

---

## 7. 当前结论

模块 05 第一阶段已经证明：

- 项目已经具备真实前端工作台骨架
- 前端可以消费当前后端核心只读 API
- 模块 03 / 04 的核心产物已经不只存在于数据库和文档里，而是进入了实际界面层

下一步应该直接继续模块 06：

- `M06-01 ~ M06-07`
