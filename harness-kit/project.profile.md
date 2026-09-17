# Project Profile

本文件是当前项目画像，由 Harness 初始化（project-profiler）生成。迁移到其他项目时须重新生成并由人 review 推断项与待确认项。

## 项目身份

**VidCatcher（万能视频下载 · 学习向）** — 基于 yt-dlp 封装的网页版视频下载工具。目标是通过「薄封装开源引擎 + 转化向前端」的方式学习 Python FastAPI + Vue 3 开发模式。当前处于 **初始开发阶段**（分支 `main`）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3、原生 JS、Vite 6、Axios |
| 后端 | Python 3.11+、FastAPI、uvicorn、线程池任务管理 |
| 下载引擎 | yt-dlp（最新版本自动跟随上游） |
| 测试 | pytest、responses（mock） |
| 部署 | 本机/局域网运行，无容器化 |

## 主要目录

| 路径 | 职责 |
| --- | --- |
| `backend/` | FastAPI 后端，API 路由、yt-dlp 封装、任务管理 |
| `frontend/` | Vue 3 前端，Vite 构建 |
| `backend/app/` | 主要业务代码：main.py、ytdlp_service.py、tasks.py、urls.py |
| `backend/tests/` | pytest 测试用例 |
| `harness-kit/` | Agent Harness 规范（勿当业务模块改） |
| `.ai-runtime-artifacts/` | spec/plan/verification 等过程产物 |

## 禁区

- **勿读、勿提交**：`.env`、密钥、token、`.cursor/mcp.json`
- **勿引入**：DRM 破解、Cookie 盗用、绕过登录态
- **勿自写提取器**：站点改版失败时升级 `yt-dlp` 版本，不自己写提取器
- **子 Agent 默认不** `git commit` / `push`（Leader + `git-xywh` 执行）

## 交付口径

- 非琐碎需求：spec → 人确认 → plan → 人确认 → 实现 → 尾盘（集体测试 + 审查）
- 验收标准：后端 pytest 全部通过，前端 `npm run build` 无错误
- 一期明确**无数据库、无鉴权、无真实支付**

## 推断项

- 项目为个人学习向，暂无 CI/CD 配置
- 无 .github workflows / .gitlab-ci.yml
- 无 commitlint / husky 约束
- 提交格式：无强制规范，建议使用语义化提交（feat/fix/chore/docs）

## 待确认项

- 是否需要引入 TypeScript（前端）
- 是否需要数据库持久化任务状态
- 是否需要用户认证功能
