---
artifact: stack
route: source-driven-development
skills:
  - source-driven-development
skills_evidence:
  - harness-kit/.agents/skills/source-driven-development/SKILL.md
source:
  - frontend/package.json
  - backend/requirements.txt
  - harness-kit/project.profile.md
created_at: 2026-09-19
---

# Stack Detection — 解析后工作区布局（2026-09-19）

本期只改前端展示与交互，不新增依赖、不改后端协议。

## 前端（已安装，沿用）

| 依赖 | 版本（`frontend/package.json`） | 本期用法 |
| --- | --- | --- |
| vue | ^3.5.13 | `ref` / `computed` / 生命周期；`:class` 对象绑定切换 Hero 与工作区状态 |
| vite | ^6.0.7 | `npm run build` 验收 |
| @vitejs/plugin-vue | ^5.2.1 | SFC |
| marked | ^18.0.13 | 总结面板已用，本期不改渲染管线 |
| markmap-lib / markmap-view | ^0.18.12 | 导图已用，本期不改 |

**样式体系：** `frontend/src/style.css` 原生 CSS 变量（`--blue`、`--ink`、`--line-light`）。不引入 Tailwind。

**官方依据：**

- Vue 3 Class and Style Bindings：<https://vuejs.org/guide/essentials/class-and-style.html>
  - 「We can pass an object to `:class` to dynamically toggle classes」
  - 「The `:class` directive can also co-exist with the plain `class` attribute」
- Vue 3 Lifecycle Hooks：<https://vuejs.org/guide/essentials/lifecycle.html>
  - `onMounted` / `onBeforeUnmount` 注册与卸载全局 `keydown`

## 后端（本期只读，不改）

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| fastapi | 0.116.1 | 已有 `/api/parse`、`/api/summarize`、`/api/chat` |
| yt-dlp | 2026.8.19 | 解析与字幕 |

## 与旧 stack 的差异

`.ai-runtime-artifacts/stack/2026-09-19-stack.md` 写于总结能力落地前，其中「待新增 marked / markmap」已过时：当前 `package.json` 已安装。本期以本文件为准。
