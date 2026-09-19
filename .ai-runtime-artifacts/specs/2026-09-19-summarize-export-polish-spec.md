---
artifact: spec
route: superpowers:brainstorming
topic: AI 总结面板导出与排版
status: draft
approved: false
created_at: 2026-09-19
skills:
  - brainstorming
  - source-driven-development
skills_evidence:
  - brainstorming@~/.cursor/skills/brainstorming loaded
  - source-driven-development@harness-kit/.agents/skills/source-driven-development loaded
  - api-and-interface-design: skipped（不新增对外 HTTP 资源；沿用现有 /api/summarize 与 /api/chat）
source:
  - docs/需求文档.md §3.6 §3.7
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-summarize-export-stack.md
  - frontend/src/components/VideoSummary.vue
  - frontend/src/api/summarize.js
  - backend/app/api_summarize.py
  - https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation
  - https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API
  - https://marked.js.org/using_advanced
  - https://www.w3.org/TR/webvtt1/
related_artifacts:
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/plans/2026-09-19-video-summarize-plan.md
  - .ai-runtime-artifacts/stack/2026-09-19-stack.md
decisions:
  - 不引入 Tailwind；Markdown 排版用现有 CSS 变量扩展
  - 字幕与导图导出全部在浏览器完成，不新增下载 API
  - summary / answer 的 token 用 JSON 字符串编码，避免换行被 SSE 拆行
  - 前端 SSE 按 WHATWG 规范：多行 data 拼接后再派发
---

# AI 总结面板：排版、导出与流式保真

## 1. 背景与目标

一期 AI 总结已经接通：解析结果页可生成摘要、字幕列表、思维导图和问答（见 `2026-09-19-video-summarize-spec.md`）。当前缺口集中在**阅读体验**和**结果带走**：

1. 摘要 / 问答的 Markdown 只覆盖了少量标题与列表，引用、代码块、表格几乎没有版式。
2. 思维导图只能在卡片里缩放平移，不能全屏看，也不能另存图片。
3. 字幕只能在页面里展开阅读，不能保存成常见字幕文件。
4. `summary` / `answer` 若出现换行，现有逐行 SSE 解析会拆丢段落结构。

`docs/需求文档.md` §3.6 要求总结可读、导图可交互；§3.7 将「字幕下载」列为扩展。本期把这四项补进现有四 Tab 面板，不另开页面、不加数据库。

**成功标准：** 用户读完摘要能看清层级与引用；能全屏看导图并下载完整画面；能把字幕存成 SRT / VTT / TXT；流式正文里的空行和列表缩进与模型输出一致。

## 2. 范围

### In scope

| 模块 | 内容 |
| --- | --- |
| SSE 保真 | 后端把 `summary` / `answer` token 编成 JSON 字符串；前端按规范拼接 `data:` 后再解码 |
| Markdown 排版 | `marked` 打开 GFM + 单换行转 `<br>`；摘要用完整 prose，问答用紧凑 prose |
| 字幕导出 | 用已有 `segments` 在浏览器生成 SRT / VTT / TXT，文件名带视频标题 |
| 导图全屏 | 原生 Fullscreen API，进出全屏后 `fit()` |
| 导图导出 | 导出完整内容边界的 PNG（高分辨率）与独立 SVG，不受当前缩放平移影响 |

### Out of scope

- 引入 Tailwind / typography 插件
- 新增 `/api/subtitle/download` 或服务端落盘
- 字幕翻译、Whisper、跨会话历史
- 改 parse / download 主链路
- VIP 次数与鉴权

### 与已有方案的关系

`2026-09-19-video-summarize-spec.md` §2 曾把「字幕文件下载」和「导图导出」标为一期不做。**本期覆盖这两条**，其余一期约束（无 DB、密钥不出前端、无 Whisper）继续有效。

## 3. 方案对比与推荐

### 3.1 排版

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. 现有 CSS 变量扩展（推荐）** | 在 `VideoSummary.vue` 补齐 `h1`–`table` / `blockquote` / `code` / `pre` | 零新依赖，色板与全站一致 | 要手写选择器 |
| B. 引入 Tailwind typography | 加 `@tailwindcss/typography` + `prose` | 现成排版 | 仅为一个面板引入整套原子化 CSS，和当前 `style.css` 体系冲突 |
| C. 外链 github-markdown-css | CDN 或本地一份通用样式 | 上手快 | 视觉语言与 VidCatcher 主色脱节 |

**选 A。** marked 18 的配置走官方 `marked.use({ gfm: true, breaks: true })`，不再用已过时的全局 `setOptions` 心智（见 [marked using_advanced](https://marked.js.org/using_advanced)）。

### 3.2 导出位置

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. 浏览器本地生成（推荐）** | `Blob` + `<a download>` | 无新接口；字幕数据已在内存 | 大字幕时主线程编码（可接受） |
| B. 后端再提供下载端点 | FastAPI 返回文件流 | 文件名策略可集中 | 多两个路由，且字幕已随 SSE 下发，重复传输 |
| C. 仅复制到剪贴板 | `clipboard.writeText` | 实现最短 | 不满足「字幕文件」诉求 |

**选 A。** 纯函数放独立模块，组件只负责菜单与触发下载。

### 3.3 Token 传输

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. JSON 编码 token（推荐）** | `json.dumps(token, ensure_ascii=False)` | 换行变成 `\n` 转义，单行 `data:` 即可完整送达 | 前端必须 `JSON.parse`，并兼容旧纯文本 |
| B. 只修前端拼接 | 依赖现有 `_sse()` 的多行 `data:` | 后端零改 | 空行 token、注释行、trim 行为仍容易踩坑 |
| C. Base64 | 二进制安全 | 调试不可读 | 过度 |

**选 A + 规范解析器。** HTML 标准明确：同一事件的多条 `data:` 用 U+000A 拼接，空行才派发事件（[§9.2.6 Interpreting an event stream](https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation)）。前端按这条重写；`subtitle` / `mindmap` / `error` 仍是 JSON 对象，行为不变。

## 4. 架构

```
模型 token（可能含换行）
        │
        ▼
api_summarize._sse("summary"|"answer", json.dumps(token))
        │
        ▼
frontend/src/api/summarize.js
  按空行 dispatch；data 行 join("\n")
  summary/answer → JSON.parse 得到原文
        │
        ├── 总结 Tab：marked.parse → .summary-prose
        ├── 问答气泡：marked.parse → .chat-prose
        ├── 字幕 Tab：列表 + 本地下载（SRT/VTT/TXT）
        └── 导图 Tab：markmap-view
              ├── 全屏：requestFullscreen → fit()
              └── 导出：完整 bbox → PNG / SVG
```

**文件边界（比把逻辑堆在单文件更清晰）：**

| 文件 | 职责 |
| --- | --- |
| `backend/app/api_summarize.py` | 仅改 token 编码 |
| `frontend/src/api/summarize.js` | SSE 解析与 JSON 解码 |
| `frontend/src/utils/subtitleFormat.js` | 分段 → SRT / VTT / TXT |
| `frontend/src/utils/mindmapExport.js` | 全内容 bbox、foreignObject 处理、PNG/SVG |
| `frontend/src/components/VideoSummary.vue` | Tab、菜单、全屏按钮、调用上述模块 |
| `backend/tests/test_api_summarize.py` | 断言 token 为 JSON 字符串且含换行时仍单行 data |

不改 `summarizer.py` 的 prompt 与模型调用。

## 5. 详细设计

### 5.1 SSE

**后端**

```python
yield _sse("summary", json.dumps(token, ensure_ascii=False))
yield _sse("answer", json.dumps(token, ensure_ascii=False))
```

`_sse()` 保持现状：按 `\n` 拆成多条 `data:`。JSON 字符串里的换行已被转义，实际几乎总是一行。

**前端解析（必须）**

- 不以 `trim()` 后的空串当作事件分隔；只有**原始空行**才 `dispatch`。
- `:` 开头为注释，忽略。
- 字段名取第一个冒号前；值去掉可选的一个前导空格（标准要求）。
- `event` 记录类型；`data` 推进数组；空行时 `dataLines.join("\n")` 交给回调。
- 流结束再 `dispatch` 一次，避免末包没有空行。
- `summary` / `answer`：`JSON.parse`，失败则回退原文（兼容手工调试）。

`subtitle` / `mindmap` / `error` 回调仍接收拼接后的字符串，由现有 `JSON.parse` 处理。

### 5.2 Markdown 排版

初始化一次：

```js
marked.use({ gfm: true, breaks: true });
```

`breaks` 依赖 `gfm`（marked 文档：*Requires gfm be true*）。

**摘要 `.summary-prose`：** `h1`/`h2`/`h3`、段落、列表、`li::marker` 用主色、`blockquote`、行内 `code`、深色 `pre`、表格、链接。颜色只用已有变量：`--ink` `--muted` `--line` `--line-light` `--blue` `--blue-soft` `--page`。

**问答 `.chat-prose`：** 同样元素，间距更紧，避免气泡被撑破。

流式过程仍显示纯文本 + 光标；流结束后再 `v-html` 渲染，避免半截 Markdown 抖动。此项保持现状。

`v-html` 只渲染本服务 SSE 产出的 Markdown。本期不引入 DOMPurify（与一期相同取舍）；若后续对外暴露用户任意 Markdown 再加。

### 5.3 字幕导出

输入：已有 `subtitleData.segments`（`start`/`end` 秒，`text`）。

| 格式 | 规则 |
| --- | --- |
| SRT | `序号` + `HH:MM:SS,mmm --> HH:MM:SS,mmm` + 文本 + 空行 |
| VTT | 首行 `WEBVTT` + 空行 + `HH:MM:SS.mmm --> HH:MM:SS.mmm` + 文本（[WebVTT](https://www.w3.org/TR/webvtt1/) 时间戳用点） |
| TXT | 每行一段纯文本，无时间戳 |

文件名：`{safeTitle} - 字幕.{ext}`。`safeTitle` 来自 `videoTitle`，去掉 `\ / * ? : " < > |`，最长 80。

交互：字幕 Tab 头部「下载字幕」按钮，展开三项菜单；点击页面其他区域关闭。无字幕时按钮不可用。

### 5.4 思维导图全屏

- 对导图容器调用 `requestFullscreen()`；退出用 `document.exitFullscreen()`。
- 监听 `fullscreenchange`（及 WebKit 前缀事件，覆盖旧 Safari）。
- `document.fullscreenElement` 非空视为全屏；随后 `nextTick` 调 `markmapInstance.fit()`。
- 全屏必须由用户点击触发（[MDN：需用户激活](https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API/Guide)）。API 不可用时按钮可点但给出轻提示，不中断其他 Tab。
- 全屏时容器铺满、白底、圆角取消；保留退出按钮（Esc 同样生效）。

### 5.5 思维导图导出

**完整边界：** 取 SVG 内根 `g` 的 `getBBox()`，再叠加其 `translate` / `scale`，得到内容矩形。不要用当前视口或用户缩放后的可见区域。失败则回退整棵 SVG 的 bbox，再失败用 `800×600`。

**PNG：**

1. 克隆 SVG。
2. 把 `foreignObject` 换成 SVG `<text>`（HTML 嵌入会让 Canvas 被标为 tainted，`toBlob` 失败）。
3. 按完整 bbox + 边距重设 `viewBox` / `width` / `height`。
4. `scale = max(4, ceil(3840 / vw))`，保证短边方向至少约 4K 宽度。
5. 白底 Canvas 绘制后 `toBlob('image/png')`。
6. 失败时提示改用 SVG。

**SVG：**

1. 克隆并清理含 `NaN` 的 `transform`。
2. 同样重设完整 `viewBox`。
3. 序列化时补 `xmlns`，并内联 markmap 用到的 CSS，保证脱离页面仍能显示文字。

文件名：`{safeTitle} - 思维导图.png|.svg`。无导图数据时按钮禁用。

### 5.6 错误与空态

| 场景 | 行为 |
| --- | --- |
| 尚无字幕 | 下载菜单不出现或按钮 disabled |
| 尚无导图 | 全屏 / 导出 disabled |
| 全屏被拒 | 保持窗口模式，可选 `console.warn`，不 `alert` 打断 |
| PNG 失败 | 中文提示改用 SVG |
| SSE JSON 解析失败 | 当纯文本追加，不中断流 |

## 6. 测试

### 后端（CI）

- mock 流式 token 含 `hello\n\n- item`：响应体中对应 `data:` 为 `json.dumps` 结果，且该事件只有一条（或等价的已转义）data 行。
- 现有「无字幕 → error」用例保持通过。

### 前端（无单测框架时）

- 新增 `frontend/src/utils/subtitleFormat.js` 的纯函数，可用 Node 断言脚本或后续补测；最低要求：手工核对三种文件头/时间戳分隔符。
- `npm run build` 通过。

### 手工

- 有字幕视频：三种字幕文件用播放器或文本编辑器打开，时间轴正确。
- 导图：缩放后再导出，PNG/SVG 仍是完整图，不是当前视口切片。
- 全屏：进入后图自适应，Esc 退出后布局恢复。
- 摘要含列表与空行：完成后 HTML 保留段落，不挤成一行。

## 7. 验收口径

| # | 项 | 通过 |
| --- | --- | --- |
| 1 | 排版 | 摘要可见标题下划线、引用条、代码块、表格线；问答气泡内列表不溢出 |
| 2 | 字幕下载 | SRT 逗号毫秒、VTT 有 `WEBVTT` 且点分毫秒、TXT 无时间戳 |
| 3 | 导图全屏 | 点击后占满屏幕并 `fit`；Esc / 按钮可退 |
| 4 | 导图导出 | PNG 分辨率不低于 4× 逻辑尺寸；SVG 可独立打开 |
| 5 | SSE | 含换行的 token 在摘要里显示为空行/列表，而不是被吃掉 |
| 6 | 回归 | 原 parse/download 与 `pytest` 全绿；密钥仍不进前端 |

## 8. 风险

| 风险 | 处理 |
| --- | --- |
| Safari 前缀全屏 | 同时听 `webkitfullscreenchange` |
| Canvas tainted | 导出前去掉 `foreignObject` |
| 超大导图内存 | scale 有下限 4，不再叠加用户缩放 |
| marked 18 全局配置 | 只在模块加载时 `use` 一次 |

## Spec 自检

- [x] 无 TBD 占位节
- [x] 与一期总结方案不冲突，仅覆盖其明确延期项
- [x] 不引入 Tailwind、不新增下载 API
- [x] 验收可测

---

## Next

**（写入后须暂停 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 确认方案无误 → 说「**写计划**」或「**制定实施计划**」
- 变更范围小、无需再拆计划 → 说「**直接实现**」或「**直接做**」
- 需要调整 → 直接说修改意见（例如：是否仍坚持不上 Tailwind、PNG 是否要 4K）
