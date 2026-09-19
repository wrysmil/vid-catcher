---
route: brainstorming
topic: AI 视频总结
status: draft
approved: false
date: 2026-09-19
author: Leader
artifact: spec
skills:
  - brainstorming
  - source-driven-development
skills_evidence:
  - brainstorming@~/.cursor/skills/brainstorming loaded
  - source-driven-development@harness-kit/.agents/skills/source-driven-development loaded
  - api-and-interface-design: skipped (单 feature 内聚；SSE 契约在本 spec 定义，无需独立 contracts 文件)
source:
  - docs/需求文档.md §3.6
  - 用户上传方案设计文档（万能视频下载网站 - 方案设计文档）
  - harness-kit/project.profile.md
  - harness-kit/context-map.md
  - .ai-runtime-artifacts/stack/2026-09-19-stack.md
related_artifacts:
  - .ai-runtime-artifacts/stack/2026-09-19-stack.md
  - .ai-runtime-artifacts/plans/2026-09-19-video-summarize-plan.md
decisions:
  - 字幕来源: 优先平台自带字幕（人工 > 自动）；B 站走专用 API；失败回退 yt-dlp；无字幕则明确报错，一期不做 Whisper
  - AI 提供商: Command Code Provider API（OpenAI Chat Completions 兼容），密钥仅服务端持有
  - 传输方式: SSE 流式推送总结/问答；字幕与思维导图一次性事件
  - 持久化: 无数据库；会话内前端缓存 subtitle_text 供问答复用
  - UI 集成: 解析结果卡片新增「AI 总结」入口 + 四 Tab 面板；不拆独立页面
---

# AI 视频总结 Spec

## 1. 背景与目标

VidCatcher 一期已完成「粘贴链接 → 解析 → 选清晰度 → 下载」主链路（见 `docs/需求文档.md` §3.1–3.2）。前端 VIP 套餐与功能列表已**占位**「AI 视频内容总结」（`frontend/src/App.vue`），但后端尚无对应 API，也无字幕提取与 LLM 调用能力。

**目标：** 用户在解析成功的视频卡片上点击「AI 总结」，系统提取字幕 → 调用 Command API 生成摘要与思维导图 → 前端 SSE 流式展示；用户可在同一面板内基于字幕上下文进行多轮问答。

**学习向定位：** 理解「字幕提取（yt-dlp / 平台 API）→ 文本截断 → LLM 流式输出 → SSE 推送 → 前端 Markdown / 导图渲染」的薄封装模式；不引入数据库、鉴权、真实付费门禁。

## 2. 范围

### In scope

| 模块 | 内容 |
| --- | --- |
| 后端字幕提取 | `SubtitleExtractor`：B 站专用 API + yt-dlp 通用回退；VTT 解析为分段结构 |
| 后端 AI 总结 | `VideoSummarizer`：Command API 流式摘要 + 一次性思维导图 Markdown |
| 后端 API | `POST /api/summarize`（SSE）、`POST /api/chat`（SSE） |
| 前端面板 | 四 Tab：总结摘要 / 字幕文本 / 思维导图 / AI 问答 |
| 前端 SSE 客户端 | `fetch` + `ReadableStream` 解析 `text/event-stream` |
| 错误处理 | 无字幕、API Key 缺失、上游超时 — 中文提示，不暴露堆栈 |
| 测试 | 字幕解析纯函数单测；AI 调用 mock 单测；可选 live 烟雾（默认 skip） |

### Out of scope（一期不做）

- Whisper 语音转文字（无字幕视频）
- 字幕文件下载 / 翻译
- 用户登录、用量统计、VIP 真实限流
- 总结结果持久化、跨会话历史
- 批量链接同时总结
- 抖音专用字幕链路（抖音走 yt-dlp 通用字幕能力，无则报错）
- 引入 Tailwind（沿用现有 `style.css`）

## 3. 方案对比与推荐

| 方案 | 描述 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. 服务端 SSE 一体化（推荐）** | 字幕提取 + LLM 调用均在 FastAPI；前端只消费 SSE | 密钥不出服务端；与现有 `/api` 代理一致；易测 | 长视频字幕大时单次请求耗时长 |
| B. 前端直连 LLM | 浏览器持 API Key 调 LLM | 服务端无 AI 负载 | **违反**项目密钥约束；CORS / 泄露风险 |
| C. WebSocket 双向通道 | WS 推送总结 + 问答 | 双向实时 | 过度设计；FastAPI SSE 已够用 |

**推荐方案 A。** 与源方案文档架构一致，且符合 `AGENTS.md`「密钥不出仓、不暴露给前端」约束。

## 4. 架构

```
用户点击「AI 总结」
        │
        ▼
frontend/src/api/summarize.js
  EventSource 或 fetch+stream 读 SSE
        │
        ▼
POST /api/summarize { url, language? }
        │
        ▼
backend/app/api_summarize.py（路由）
        │
        ├── SubtitleExtractor.extract(url)
        │     ├─ B站? → bilibili_subtitle API
        │     └─ 其他 → yt-dlp subtitles
        │     → [{start, end, text}, ...] + full_text
        │
        └── VideoSummarizer
              ├─ stream summary (Command API, max ~15000 chars input)
              ├─ once mindmap markdown
              └─ SSE events → 前端

POST /api/chat { url, question, subtitle_text? }
        │
        └── VideoSummarizer.chat(question, context)
              └─ SSE: answer tokens → done
```

**与现有模块关系：**

- `main.py`：挂载 summarize 路由（或 include `api_summarize` router）；**不改动** `parse` / `download` / `tasks` 契约
- `ytdlp_service.py`：字幕提取可复用 `_base_opts()` 与 Cookie 环境变量，但不把总结逻辑塞进 `parse_video`
- `douyin_service.py`：无改动；抖音 URL 总结时走 yt-dlp 字幕分支

## 5. API 设计

### 5.1 `POST /api/summarize`

**Request**

```json
{
  "url": "https://www.bilibili.com/video/BV1mAAmzqEfP",
  "language": "zh"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `url` | string | 是 | 与 `/api/parse` 相同；经 `validate_http_url` |
| `language` | string | 否 | 字幕语言偏好，默认 `zh` |

**Response：** `Content-Type: text/event-stream`

| event | data 结构 | 时机 |
| --- | --- | --- |
| `subtitle` | `{ "segments": [{ "start", "end", "text" }], "full_text": "..." }` | 字幕提取完成后**一次** |
| `summary` | `{ "token": "..." }` 或纯文本 token | 流式，多次 |
| `mindmap` | `{ "markdown": "# 标题\n- ..." }` | 摘要流结束后**一次** |
| `done` | `{}` 或 `{ "ok": true }` | 全流程结束 |
| `error` | `{ "message": "中文错误说明" }` | 任意失败 |

**HTTP 错误（非 SSE）：**

| 场景 | 状态码 |
| --- | --- |
| URL 非法 | 400 |
| 无 API Key | 503 |
| 字幕提取失败 / 无字幕 | 502（或在 SSE 内 `error` 事件，实现时二选一并文档化） |

> **实现约定：** 推荐连接建立后一律走 SSE `error` 事件，避免前端同时处理 JSON 错误体与 SSE 两套逻辑；仅在 URL 校验失败时返回 400 JSON。

### 5.2 `POST /api/chat`

**Request**

```json
{
  "url": "https://www.bilibili.com/video/BV1mAAmzqEfP",
  "question": "这个视频用了什么技术栈？",
  "subtitle_text": ""
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `url` | string | 是 | 标识上下文；可与 summarize 时的 url 一致 |
| `question` | string | 是 | 用户问题，1–2000 字符 |
| `subtitle_text` | string | 否 | 前端缓存的字幕全文；空则服务端重新 extract |

**Response SSE**

| event | 说明 |
| --- | --- |
| `answer` | 流式 token |
| `done` | 完成 |
| `error` | 失败 |

**多轮对话：** 一期可在前端维护 `messages[]`，每次 chat 将**最近 N 轮**与 `subtitle_text` 拼入 prompt；不存服务端 session。

## 6. 字幕提取设计

### 6.1 策略流程

```
extract(url)
    │
    ├─ is_bilibili_url(url)?
    │     └─ GET B站字幕 API（CC / AI 字幕）
    │           ├─ 成功 → parse → segments
    │           └─ 失败 → 回退 yt-dlp
    │
    └─ 其他平台
          └─ yt-dlp: lists subtitles / auto-subs
                ├─ 语言优先级: zh* > en > ja > ko > 其他
                ├─ 人工字幕优先于自动字幕
                └─ 下载 VTT → 解析
```

### 6.2 分段结构

```python
@dataclass
class SubtitleSegment:
    start: float   # 秒
    end: float
    text: str

# 返回
{
    "segments": [...],
    "full_text": "\n".join(s.text for s in segments),
    "language": "zh-Hans",
    "source": "bilibili_api" | "yt-dlp",
}
```

### 6.3 VTT 解析

- 支持 `WEBVTT` 基本格式与常见 YouTube/B 站导出样式
- 合并相邻重复行、去掉 HTML 标签
- 单段 `text` 过长时按句切分（可选，一期可整段保留）

### 6.4 无字幕

返回用户可读错误：**「该视频没有可用字幕，暂时无法生成 AI 总结」**；不尝试下载音视频做 ASR。

### 6.5 文本截断

- 送入 LLM 的 `full_text` 上限 **15000 字符**（与源方案一致）
- 超出时保留开头 + 结尾各一部分，中间插入 `...[内容已截断]...`，并在 summary prompt 中说明

## 7. AI 总结设计

### 7.1 配置

| 环境变量 | 说明 |
| --- | --- |
| `AI_API_KEY` | 必填；缺失时 `/api/summarize` 返回「AI 服务未配置」 |
| `AI_API_BASE_URL` | 可选，默认 `https://api.commandcode.ai/provider/v1` |
| `AI_MODEL` | 可选，默认 `deepseek/deepseek-v4-flash` |

API 文档：[Command Code Provider API](https://commandcode.ai/docs/provider)  
端点：`POST https://api.commandcode.ai/provider/v1/chat/completions`（OpenAI Chat Completions  schema，`stream: true` 支持 SSE 式 token 流）

密钥**仅**存在于 `backend/.env`，由用户手动填写，禁止提交 Git、禁止下发前端。

### 7.2 Prompt 要点

**摘要（流式）：**

- 输入：字幕全文（截断后）
- 输出 Markdown 结构：视频概述、内容大纲（有序列表）、核心要点、一句话总结
- `stream=True`，每个 delta 作为 SSE `summary` 事件

**思维导图（一次性）：**

- 同一字幕上下文；要求输出**仅** Markdown 标题层级（`#` / `##` / `-`），供 markmap 渲染
- 在摘要流完成后调用第二次 API（`stream=False`）

**问答：**

- System：基于提供的字幕回答，不知道则明确说不知道，勿编造
- User：`subtitle + question`（+ 可选 history）

### 7.3 超时与限流

- 单次 LLM 请求 timeout **120s**
- 总结链路串行：extract → summary stream → mindmap；总时长目标 < 90s（普通长度视频）
- 无并发队列；重复点击「AI 总结」时前端 abort 上一次 SSE

## 8. 前端设计

### 8.1 入口

在 `results` 卡片 `download-row` **上方或并列**增加按钮：

```text
[ AI 总结 ]   （解析成功且非 busy 时可点）
```

点击后展开 `VideoSummary` 面板（可做成 `frontend/src/components/VideoSummary.vue` 或 `App.vue` 内联区块）。

### 8.2 四 Tab

| Tab | 渲染 | 数据 source |
| --- | --- | --- |
| 总结摘要 | `marked` → `v-html`（注意 XSS：仅渲染自家 API 输出） | SSE `summary` 累积 |
| 字幕文本 | 可滚动列表，显示 `[mm:ss] text`；支持展开/收起 | SSE `subtitle` |
| 思维导图 | `markmap-lib` transform + `markmap-view` SVG | SSE `mindmap` |
| AI 问答 | 聊天气泡 + 输入框；流式 `answer` | `/api/chat` |

### 8.3 SSE 客户端

```javascript
// frontend/src/api/summarize.js
export async function summarizeVideo(url, { onEvent, signal }) {
  const res = await fetch("/api/summarize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, language: "zh" }),
    signal,
  });
  // 解析 res.body.getReader()，按 \n\n 拆 event
}
```

- 使用 `AbortController` 支持取消
- Tab 切换不中断 SSE；关闭面板时 abort

### 8.4 样式

- 沿用现有 CSS 变量与卡片圆角（源方案参考色 `#1777FF` 可与站点主色对齐）
- 面板默认最大高度 + 内部滚动，避免撑破结果卡片布局

## 9. 目录与文件（计划新增/修改）

```
backend/app/
├── subtitle_extractor.py   # 新：B站 API + yt-dlp + VTT 解析
├── summarizer.py           # 新：DeepSeek 客户端、prompt、流式封装
├── api_summarize.py        # 新：/api/summarize、/api/chat 路由
└── main.py                 # 改：挂载 router

backend/tests/
├── test_subtitle_extractor.py
└── test_summarizer.py      # mock openai

frontend/src/
├── components/VideoSummary.vue   # 新（推荐拆分）
├── api/summarize.js              # 新
└── App.vue                       # 改：按钮 + 面板挂载

backend/requirements.txt    # 改：+ openai, python-dotenv（如需要）
frontend/package.json       # 改：+ marked, markmap-lib, markmap-view
```

## 10. 错误处理

| 场景 | 用户可见提示 |
| --- | --- |
| 无字幕 | 该视频没有可用字幕，暂时无法生成 AI 总结 |
| `AI_API_KEY` 未配置 | AI 服务未配置，请联系管理员 |
| Command API 429 / 5xx | AI 服务暂时不可用，请稍后重试 |
| 字幕提取超时 | 字幕获取超时，请换条链接或稍后重试 |
| 问题为空 | 请输入问题 |
| B 站 412 / Cookie | 沿用现有 `_public_error` 风格的中文指引 |

日志：服务端 `logging.warning` 记录异常类型与 url 域名，**不**记录 API Key 与完整字幕。

## 11. 安全与合规

- 仅总结**用户主动提交**且已通过 `validate_http_url` 的公开 URL
- 不存储字幕与总结到磁盘（内存流式处理）
- LLM prompt 中不包含用户 Cookie；yt-dlp Cookie 仅用于字幕提取，与现有下载链路一致
- 前端 `v-html` 渲染前可考虑 marked 的 sanitize 或 DOMPurify（若引入，写入 plan 任务）
- 符合 `AGENTS.md`：不破解 DRM、不盗用 Cookie、不把服务裸挂公网

## 12. 测试

### 12.1 单元测试（CI 必跑）

- `test_parse_vtt` — 样例 VTT 字符串 → segments
- `test_truncate_subtitle` — 15000 字符截断逻辑
- `test_bilibili_subtitle_parse` — mock JSON 响应
- `test_summarizer_mock_stream` — mock OpenAI client，断言 SSE 事件顺序：subtitle → summary* → mindmap → done

### 12.2 Live 烟雾（`@pytest.mark.live`，默认 skip）

- 环境变量 `SUMMARIZE_SMOKE=1` + `AI_API_KEY`
- 固定 B 站公开视频 URL → extract 有字幕 → 不强制断言 LLM 文案

### 12.3 前端

- `npm run build` 无错误
- 手工：B 站链接 → 总结四 Tab 有内容；无字幕 YouTube 短视频 → 错误提示

## 13. 验收口径

| # | 验收项 | 通过标准 |
| --- | --- | --- |
| 1 | 入口可见 | 解析成功后结果卡片出现「AI 总结」按钮 |
| 2 | 字幕展示 | B 站有 CC 视频 → 「字幕文本」Tab 有时间戳列表 |
| 3 | 流式摘要 | 「总结摘要」Tab 逐字/逐段出现，完成后可读 |
| 4 | 思维导图 | 「思维导图」Tab 渲染可交互 SVG |
| 5 | 问答 | 输入问题 → 流式回答，内容与字幕相关 |
| 6 | 无字幕 | 无字幕视频 → 中文错误，不调用 LLM |
| 7 | 无 Key | 未配置 `AI_API_KEY` → 友好提示 |
| 8 | 回归 | 原有 parse/download 流程与 pytest 全绿 |
| 9 | 密钥 | `.env` 未入仓；前端网络面板无 API Key |

## 14. 风险与权衡

| 风险 | 应对 |
| --- | --- |
| B 站字幕 API 变更 | yt-dlp 回退；失败明确报错 |
| 长视频字幕超大 | 15000 字符截断 + prompt 说明 |
| Command API 费用 / 限流 | 学习项目本机使用；不做用量面板 |
| markmap 包体积 | 仅总结面板懒加载（动态 import） |
| 源方案 `/api/direct-url` | **不在本 spec**；VidCatcher 当前无直链 API，下载仍走 tasks |

## 15. 后续扩展（不进本期 plan）

- Whisper 本地 / API 转写（无字幕视频）
- 字幕下载 SRT/VTT
- 总结结果导出 Markdown / 图片
- VIP 次数限制与缓存
- 多语言总结输出

---

## Spec 自检

- [x] 无 TBD / 占位节
- [x] 与 `docs/需求文档.md` §3.6、`project.profile.md` 一期约束一致
- [x] 范围边界清晰（无 Whisper / 无 DB）
- [x] API 事件类型与源方案文档 §3.4–3.5 对齐并适配 VidCatcher 现状
- [x] 可拆分为单一 implementation plan

---

## Next

**（写入后须暂停 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 确认方案无误 → 说「**写计划**」或「**制定实施计划**」
- 变更范围小、无需详细 plan → 说「**直接实现**」或「**直接做**」
- 需要调整方案 → 直接说修改意见（例如：是否一期就要 DOMPurify、是否合并 summarize/chat 为单端点）
