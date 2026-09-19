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
  - .ai-runtime-artifacts/stack/2026-09-19-stack.md
created_at: 2026-09-19
---

# Stack Detection — 总结面板导出与排版增量

复用 `2026-09-19-stack.md` 的基线，仅记录本期会碰到的已安装版本。

## 后端（不变）

| 依赖 | 版本 | 本期用法 |
| --- | --- | --- |
| Python | 3.11+ | 运行时 |
| fastapi | 0.116.1 | `StreamingResponse` 输出 `text/event-stream` |
| 标准库 `json` | — | `summary` / `answer` token 编码为 JSON 字符串 |

不新增 Python 依赖。

## 前端（已安装，本期复用）

| 依赖 | 版本 | 本期用法 |
| --- | --- | --- |
| vue | ^3.5.13 | `VideoSummary.vue` 面板与交互 |
| vite | ^6.0.7 | 构建 / 开发代理 |
| marked | ^18.0.13 | `marked.use({ gfm: true, breaks: true })` 后 `parse` |
| markmap-lib | ^0.18.12 | Markdown → 导图数据；导出时取用样式资源 |
| markmap-view | ^0.18.12 | SVG 渲染、`fit()` |

**不引入：** Tailwind CSS、`@tailwindcss/typography`。排版继续走现有 `style.css` 变量 + 组件 scoped CSS。

## 浏览器平台能力（无新包）

| 能力 | 权威来源 | 本期用法 |
| --- | --- | --- |
| SSE 解析 | [HTML Living Standard §9.2](https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation) | 空行派发事件；多行 `data:` 用 `\n` 拼接 |
| Fullscreen | [MDN Fullscreen API](https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API) | `Element.requestFullscreen()` / `document.exitFullscreen()` |
| Canvas 2D | [HTML canvas](https://html.spec.whatwg.org/multipage/canvas.html) | SVG → Image → `toBlob('image/png')` |
| 字幕文件 | [WebVTT](https://www.w3.org/TR/webvtt1/)；SRT 为常见互换格式 | 前端由已有 `segments` 生成下载内容 |
