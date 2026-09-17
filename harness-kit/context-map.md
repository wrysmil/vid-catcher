# Context Map

本文件由 Harness 初始化流程生成，用于帮助 AI 快速理解项目结构。迁移到新项目后，应通过 `harness-kit/init/project-profiler.prompt.md` 重新生成。

## 顶层结构

| 路径 | 类型 | 说明 |
| --- | --- | --- |
| `backend/` | 目录 | FastAPI 后端根目录 |
| `frontend/` | 目录 | Vue 3 前端根目录 |
| `harness-kit/` | 目录 | Agent Harness 脚手架（勿改） |
| `.ai-runtime-artifacts/` | 目录 | AI 运行时产物 |
| `README.md` | 文件 | 项目主文档 |
| `AGENTS.md` | 文件 | Harness 入口 |

## 主要入口

| 入口 | 说明 |
| --- | --- |
| `backend/app/main.py` | FastAPI 应用入口，API 路由定义 |
| `frontend/src/main.js` | Vue 3 前端入口 |
| `frontend/index.html` | 前端 HTML 入口 |

## 关键模块

| 模块 | 路径 | 说明 |
| --- | --- | --- |
| yt-dlp 封装 | `backend/app/ytdlp_service.py` | 视频解析与下载封装 |
| 任务管理 | `backend/app/tasks.py` | 线程池任务存储与状态管理 |
| URL 验证 | `backend/app/urls.py` | URL 格式校验 |
| API 路由 | `backend/app/main.py` | FastAPI 路由：/api/health, /api/parse, /api/download, /api/tasks/{id} |
| 抖音支持 | `backend/app/douyin_service.py` | 抖音特定 URL 处理（回退到 yt-dlp） |
| 前端 App | `frontend/src/App.vue` | Vue 3 根组件 |

## 待确认项

- 是否需要 API 文档（Swagger/OpenAPI）
- 是否需要监控/指标埋点
