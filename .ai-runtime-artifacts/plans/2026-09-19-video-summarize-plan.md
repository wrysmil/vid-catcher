---
artifact: implementation-plan
route: superpowers:writing-plans
topic: AI 视频总结
status: draft
approved: false
created_at: 2026-09-19
source:
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-stack.md
  - https://commandcode.ai/docs/provider
  - https://github.com/liyupi/free-video-downloader/commit/93f75c60ebae25d84641b035ceac3fd32519cdd2
  - AGENTS.md
  - harness-kit/core/routing.md
skills:
  - writing-plans
skills_evidence:
  - writing-plans@~/.cursor/skills/writing-plans/SKILL.md loaded
dispatch: n/a
---

# AI 视频总结 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans`（单 WU 顺序执行；后端 → 前端 → 验证）。Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 VidCatcher 现有解析/下载链路上增加 AI 视频总结：字幕提取 → Command API 流式摘要/思维导图/问答 → 前端四 Tab 面板（SSE）。

**Architecture:**

```
解析成功 → 用户点「AI 总结」
    → POST /api/summarize (SSE)
        → SubtitleExtractor（B站 dm/view API → yt-dlp 回退）
        → VideoSummarizer（OpenAI SDK → Command API base_url）
        → events: subtitle | summary | mindmap | done | error
    → POST /api/chat (SSE)
        → 基于缓存或重新提取的字幕问答
    → VideoSummary.vue 渲染 Markdown / markmap
```

**Tech Stack:**

| 层 | 选型 |
| --- | --- |
| 后端 | FastAPI 0.116+、`StreamingResponse` 手写 SSE（当前版本无 `fastapi.sse`） |
| 字幕 | yt-dlp + httpx（B 站 `x/v2/dm/view`） |
| LLM | OpenAI Python SDK → Command Provider API |
| 前端 | Vue 3、marked、markmap-lib、markmap-view |
| 测试 | pytest、unittest.mock |

**参考实现（模块对齐，非 verbatim）：**

开源仓库 [free-video-downloader@93f75c60](https://github.com/liyupi/free-video-downloader/commit/93f75c60ebae25d84641b035ceac3fd32519cdd2) 已验证该功能链路。本计划按**相同模块边界**落地到 VidCatcher 的 `backend/app/` 包结构，并按项目约束替换 LLM 为 Command API、样式对齐现有 `style.css`（不引入 Tailwind）。

| 参考文件 | VidCatcher 目标 | 适配要点 |
| --- | --- | --- |
| `backend/summarizer.py` | `backend/app/summarizer.py` | 包内相对导入；`AI_*` 环境变量 |
| `backend/api_summarize.py` | `backend/app/api_summarize.py` | `StreamingResponse` 替代 `EventSourceResponse` |
| `frontend/src/api/summarize.js` | `frontend/src/api/summarize.js` | 逻辑一致 |
| `frontend/src/components/VideoSummary.vue` | `frontend/src/components/VideoSummary.vue` | Tailwind class → 项目 CSS |
| `VideoResult.vue` 按钮 | `App.vue` 结果卡片 | 单文件 App 结构 |

**Command API 接入（替代原方案 DeepSeek）：**

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url=os.getenv("AI_API_BASE_URL", "https://api.commandcode.ai/provider/v1"),
)
client.chat.completions.create(
    model=os.getenv("AI_MODEL", "deepseek/deepseek-v4-flash"),
    messages=[...],
    stream=True,
)
```

文档：https://commandcode.ai/docs/provider  
密钥：用户手动写入 `backend/.env` 的 `AI_API_KEY=`（**不入仓**）。

**TDD Required:** YES（后端纯函数 + mock LLM；前端 build 验证）

---

## 变更范围一览

| 文件 | 动作 |
| --- | --- |
| `backend/requirements.txt` | 追加 `openai`、`python-dotenv`、`httpx` |
| `backend/app/summarizer.py` | **新建**：`SubtitleExtractor` + `VideoSummarizer` |
| `backend/app/api_summarize.py` | **新建**：SSE 路由 |
| `backend/app/main.py` | **修改**：`load_dotenv()` + `include_router` |
| `backend/tests/test_summarizer.py` | **新建** |
| `backend/tests/test_api_summarize.py` | **新建** |
| `frontend/package.json` | 追加 `marked`、`markmap-lib`、`markmap-view` |
| `frontend/src/api/summarize.js` | **新建** |
| `frontend/src/components/VideoSummary.vue` | **新建** |
| `frontend/src/App.vue` | **修改**：AI 总结按钮 + 面板 |
| `frontend/src/style.css` | **修改**：总结面板样式 |
| `README.md` | **修改**：环境变量说明（不含真实 key） |

**不动：** `ytdlp_service.py`、`douyin_service.py`、`tasks.py` 下载主链路。

---

## Task 0: 依赖与环境变量骨架

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/main.py`（仅 dotenv 两行，router 在 Task 3 挂）
- Modify: `README.md`

- [ ] **Step 1: 更新 requirements.txt**

在末尾追加：

```text
openai>=1.0.0
python-dotenv>=1.0.0
httpx>=0.28.0
```

- [ ] **Step 2: 安装依赖**

```bash
cd backend && source .venv/bin/activate && pip install -r requirements.txt
```

Expected: 无报错

- [ ] **Step 3: main.py 加载 .env**

在 `backend/app/main.py` 最顶部（`from __future__` 之后）追加：

```python
from dotenv import load_dotenv

load_dotenv()
```

- [ ] **Step 4: README 文档化环境变量**

在 `README.md`「启动」段落后追加：

```markdown
## AI 总结（可选）

在 `backend/.env` 中配置（文件勿提交 Git）：

```bash
AI_API_KEY=            # Command Code API Key，用户自行填写
AI_API_BASE_URL=https://api.commandcode.ai/provider/v1
AI_MODEL=deepseek/deepseek-v4-flash
```

未配置 `AI_API_KEY` 时，解析/下载仍可用，AI 总结返回友好提示。
```

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/main.py README.md
git commit -m "chore: add Command API and dotenv deps for video summarize"
```

---

## Task 1: VTT 解析与时间转换（纯函数）

**Files:**
- Create: `backend/app/summarizer.py`（先写工具函数）
- Create: `backend/tests/test_summarizer.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_summarizer.py
from app.summarizer import parse_vtt, time_to_seconds, truncate_text


SAMPLE_VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello <b>world</b>

00:00:04.000 --> 00:00:07.000
Second line
"""


def test_time_to_seconds():
    assert time_to_seconds("00:01:02.500") == 62.5


def test_parse_vtt_basic():
    segs = parse_vtt(SAMPLE_VTT)
    assert len(segs) == 2
    assert segs[0]["text"] == "Hello world"
    assert segs[0]["start"] == 1.0


def test_truncate_text_short():
    assert truncate_text("abc", 10) == "abc"


def test_truncate_text_long():
    text = "a" * 20000
    out = truncate_text(text, 15000)
    assert len(out) <= 15000
    assert "截断" in out
```

- [ ] **Step 2: 运行确认 FAIL**

```bash
cd backend && pytest tests/test_summarizer.py -v
```

Expected: `ModuleNotFoundError` 或 `ImportError`

- [ ] **Step 3: 实现纯函数**

在 `backend/app/summarizer.py` 写入（节选）：

```python
"""AI 视频总结：字幕提取 + Command API 总结"""

from __future__ import annotations

import os
import re
from typing import Optional


def time_to_seconds(time_str: str) -> float:
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def parse_vtt(content: str) -> list[dict]:
    segments: list[dict] = []
    blocks = re.split(r"\n\n+", content)
    time_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})"
    )
    seen: set[str] = set()
    for block in blocks:
        lines = block.strip().split("\n")
        time_match = None
        text_lines: list[str] = []
        for line in lines:
            m = time_pattern.search(line)
            if m:
                time_match = m
            elif time_match and line.strip() and not line.strip().isdigit():
                clean = re.sub(r"<[^>]+>", "", line.strip())
                if clean:
                    text_lines.append(clean)
        if time_match and text_lines:
            text = " ".join(text_lines)
            if text in seen:
                continue
            seen.add(text)
            segments.append({
                "start": round(time_to_seconds(time_match.group(1)), 2),
                "end": round(time_to_seconds(time_match.group(2)), 2),
                "text": text,
            })
    return segments


def truncate_text(text: str, limit: int = 15000) -> str:
    if len(text) <= limit:
        return text
    head = limit // 2 - 20
    tail = limit // 2 - 20
    return text[:head] + "\n...[内容已截断]...\n" + text[-tail:]
```

- [ ] **Step 4: 运行 PASS**

```bash
pytest tests/test_summarizer.py::test_time_to_seconds tests/test_summarizer.py::test_parse_vtt_basic tests/test_summarizer.py::test_truncate_text_long -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/summarizer.py backend/tests/test_summarizer.py
git commit -m "feat: add VTT parse helpers for subtitle extraction"
```

---

## Task 2: SubtitleExtractor（B 站 API + yt-dlp）

**Files:**
- Modify: `backend/app/summarizer.py`
- Modify: `backend/tests/test_summarizer.py`

**实现指引：** 参考 free-video-downloader@93f75c60 的 `SubtitleExtractor` 类，保持返回结构：

```python
{
    "has_subtitle": bool,
    "language": str,
    "subtitle_type": "manual" | "auto" | "none",
    "segments": [{"start", "end", "text"}],
    "full_text": str,
}
```

- [ ] **Step 1: 写 B 站 JSON 解析测试（mock httpx）**

```python
# 追加到 test_summarizer.py
from unittest.mock import patch, MagicMock
from app.summarizer import SubtitleExtractor


BILI_SUB_JSON = {
    "body": [
        {"from": 0.0, "to": 2.5, "content": "你好"},
        {"from": 2.5, "to": 5.0, "content": "世界"},
    ]
}


@patch("app.summarizer.httpx.get")
def test_bilibili_subtitle_segments(mock_get):
    def side_effect(url, **kwargs):
        resp = MagicMock()
        resp.json.return_value = {}
        if "view?bvid=" in url:
            resp.json.return_value = {"data": {"cid": 1, "aid": 2}}
        elif "dm/view" in url:
            resp.json.return_value = {
                "data": {"subtitle": {"subtitles": [{"lan": "zh", "subtitle_url": "https://example.com/sub.json"}]}}
            }
        elif url.endswith("/sub.json"):
            resp.json.return_value = BILI_SUB_JSON
        return resp

    mock_get.side_effect = side_effect
    ext = SubtitleExtractor()
    result = ext._extract_bilibili("https://www.bilibili.com/video/BV1xx411c7mD")
    assert result["has_subtitle"] is True
    assert len(result["segments"]) == 2
    assert "你好" in result["full_text"]
```

- [ ] **Step 2: 实现 SubtitleExtractor**

在 `summarizer.py` 追加完整类（与参考实现逻辑一致，导入改为包内）：

- `_is_bilibili_url` / `_parse_bvid`
- `_extract_bilibili`：`view` → `dm/view` → 下载 subtitle JSON
- `_get_video_info` / `_pick_best_subtitle` / `_download_and_parse` / `_parse_vtt` 文件版
- 公开方法 `extract(url)`

`PREFERRED_LANGS = ["zh-Hans", "zh", "zh-CN", "en", "ja", "ko"]`

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_summarizer.py -v -k "bilibili or parse_vtt or truncate"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/summarizer.py backend/tests/test_summarizer.py
git commit -m "feat: add subtitle extractor with bilibili API and yt-dlp fallback"
```

---

## Task 3: VideoSummarizer（Command API）

**Files:**
- Modify: `backend/app/summarizer.py`
- Modify: `backend/tests/test_summarizer.py`

- [ ] **Step 1: 写 mock 流式测试**

```python
from unittest.mock import patch, MagicMock
from app.summarizer import VideoSummarizer


class FakeDelta:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)


class FakeChunk:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


@patch.dict("os.environ", {"AI_API_KEY": "test-key"})
@patch("app.summarizer.OpenAI")
def test_summarize_stream_yields_tokens(mock_openai):
    client = MagicMock()
    mock_openai.return_value = client
    client.chat.completions.create.return_value = [
        FakeChunk("Hello"),
        FakeChunk(" world"),
    ]
    vs = VideoSummarizer()
    tokens = list(vs.summarize_stream("subtitle text", "zh"))
    assert tokens == ["Hello", " world"]
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is True
    assert "deepseek" in call_kwargs["model"] or call_kwargs["model"]


@patch.dict("os.environ", {}, clear=True)
def test_summarizer_missing_key():
    import pytest
    with pytest.raises(ValueError, match="AI_API_KEY"):
        VideoSummarizer()
```

- [ ] **Step 2: 实现 VideoSummarizer**

```python
from openai import OpenAI


class VideoSummarizer:
    def __init__(self):
        api_key = os.getenv("AI_API_KEY", "")
        if not api_key:
            raise ValueError("AI_API_KEY 环境变量未设置")
        base_url = os.getenv(
            "AI_API_BASE_URL",
            "https://api.commandcode.ai/provider/v1",
        )
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("AI_MODEL", "deepseek/deepseek-v4-flash")

    def summarize_stream(self, subtitle_text: str, language: str = "zh"):
        prompt = self._build_summary_prompt(truncate_text(subtitle_text), language)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的视频内容分析助手，擅长提取关键信息并生成结构化的总结。"},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=4096,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def generate_mindmap(self, subtitle_text: str, language: str = "zh") -> str:
        prompt = self._build_mindmap_prompt(truncate_text(subtitle_text), language)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的思维导图生成助手，擅长将内容组织为清晰的层级结构。"},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.5,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def chat_stream(self, subtitle_text: str, question: str):
        prompt = self._build_chat_prompt(truncate_text(subtitle_text, 12000), question)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个视频内容问答助手。根据提供的视频字幕内容来回答用户的问题。如果问题超出视频内容范围，请诚实告知。"},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=2048,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    # _build_summary_prompt / _build_mindmap_prompt / _build_chat_prompt
    # → 与 spec §7.2 及参考实现 prompt 结构一致（15000 字符截断）
```

- [ ] **Step 3: 运行测试 PASS**

```bash
pytest tests/test_summarizer.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/summarizer.py backend/tests/test_summarizer.py
git commit -m "feat: add VideoSummarizer using Command Provider API"
```

---

## Task 4: SSE 路由 api_summarize

**Files:**
- Create: `backend/app/api_summarize.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_api_summarize.py`

**SSE 实现（兼容 FastAPI 0.116，不用 `fastapi.sse`）：**

```python
def _sse(event: str, data: str) -> str:
    # data 行内换行需按 SSE 规范转义；token 单行则直接发送
    lines = data.split("\n")
    payload = "".join(f"data: {line}\n" for line in lines)
    return f"event: {event}\n{payload}\n"
```

- [ ] **Step 1: 创建 api_summarize.py**

核心逻辑对齐参考 `api_summarize.py`：

- `SummarizeRequest` / `ChatRequest`
- 延迟单例 `_get_summarizer` / `_get_extractor`
- `POST /summarize`：`run_in_executor` 提取字幕 → yield subtitle → 无字幕 error → summary 流 → mindmap → done
- `POST /chat`：复用 `subtitle_text` 或重新 extract → answer 流 → done
- 返回 `StreamingResponse(event_generator(), media_type="text/event-stream")`

**包导入：**

```python
from .summarizer import SubtitleExtractor, VideoSummarizer
```

**URL 校验（与 parse 一致）：**

```python
from .urls import validate_http_url

url = validate_http_url(req.url)
```

- [ ] **Step 2: main.py 挂载**

```python
from .api_summarize import router as summarize_router

app.include_router(summarize_router)
```

- [ ] **Step 3: API 测试（mock extractor + summarizer）**

```python
# backend/tests/test_api_summarize.py
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.api_summarize._get_extractor")
@patch("app.api_summarize._get_summarizer")
def test_summarize_sse_no_subtitle(mock_sum, mock_ext):
    ext = MagicMock()
    ext.extract.return_value = {
        "has_subtitle": False, "language": "", "subtitle_type": "none",
        "segments": [], "full_text": "",
    }
    mock_ext.return_value = ext

    with client.stream("POST", "/api/summarize", json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"}) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
        assert "event: subtitle" in body
        assert "event: error" in body
        assert "没有可用" in body
```

- [ ] **Step 4: 全量 pytest**

```bash
cd backend && pytest -q
```

Expected: 全部 PASS（含既有 douyin/parse 测试）

- [ ] **Step 5: Commit**

```bash
git add backend/app/api_summarize.py backend/app/main.py backend/tests/test_api_summarize.py
git commit -m "feat: add SSE endpoints for video summarize and chat"
```

---

## Task 5: 前端依赖与 SSE 客户端

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/api/summarize.js`

- [ ] **Step 1: 安装 npm 依赖**

```bash
cd frontend && npm install marked markmap-lib markmap-view
```

`package.json` dependencies 应包含：

```json
"marked": "^17.0.3",
"markmap-lib": "^0.18.12",
"markmap-view": "^0.18.12"
```

- [ ] **Step 2: 创建 summarize.js**

内容与参考实现一致（`parseSSELine`、`handleSSEStream`、`summarizeVideo`、`chatWithVideo`），路径 `/api/summarize` 与 `/api/chat`。

可选增强：为 `summarizeVideo` / `chatWithVideo` 增加 `signal` 参数传入 `fetch`，支持 AbortController。

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/api/summarize.js
git commit -m "feat: add frontend SSE client for video summarize API"
```

---

## Task 6: VideoSummary 组件

**Files:**
- Create: `frontend/src/components/VideoSummary.vue`
- Modify: `frontend/src/style.css`

**实现指引：**

- `<script setup>` 逻辑对齐参考 `VideoSummary.vue`：四 Tab、marked 渲染、markmap 渲染、`startSummarize` onMounted
- **模板/CSS：** 将 Tailwind utility class 映射为项目现有 class（`.result-card`、`.cta`、主色等）
- 错误提示：用 `emit('error', message)` 替代 `alert()`，由 `App.vue` 写入 `error` ref
- markmap：**动态 import** 减小首屏体积

```javascript
const { Transformer } = await import("markmap-lib");
const { Markmap } = await import("markmap-view");
```

- [ ] **Step 1: 创建组件 + 样式**

- [ ] **Step 2: build 验证**

```bash
cd frontend && npm run build
```

Expected: 无 error

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/VideoSummary.vue frontend/src/style.css
git commit -m "feat: add VideoSummary panel with four tabs"
```

---

## Task 7: App.vue 集成入口

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 结果卡片增加状态**

在 `parseAll` 推入的 item 对象增加：

```javascript
showSummary: false,
```

- [ ] **Step 2: 模板：下载行上方加按钮与面板**

在 `.quality` 与 `.download-row` 之间：

```vue
<div class="summary-row">
  <button
    type="button"
    class="summary-btn"
    :disabled="item.busy"
    @click="item.showSummary = !item.showSummary"
  >
    {{ item.showSummary ? "收起总结" : "AI 总结" }}
  </button>
</div>
<VideoSummary
  v-if="item.showSummary"
  :video-url="item.url"
  :video-title="item.title"
  @error="(msg) => (error = msg)"
/>
```

- [ ] **Step 3: script 导入**

```javascript
import VideoSummary from "./components/VideoSummary.vue";
```

- [ ] **Step 4: features 列表**

将 `features` 数组增加一项（与 VIP 占位文案一致）：

```javascript
{ icon: "🤖", tone: "blue", title: "AI 视频总结", desc: "自动生成摘要、字幕、思维导图，支持针对内容提问" },
```

- [ ] **Step 5: build + 手工冒烟**

```bash
cd frontend && npm run build
```

手工：B 站链接 → 解析 → AI 总结 → 四 Tab 有内容（需本机已填 `AI_API_KEY`）

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: wire AI summarize entry into parse result cards"
```

---

## Task 8: 尾盘验证

**Files:**
- Create: `.ai-runtime-artifacts/verifications/2026-09-19-video-summarize-verification-lite.md`

- [ ] **Step 1: 后端测试**

```bash
cd backend && pytest -q
```

- [ ] **Step 2: 前端构建**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: 写 verification-lite**

| 项 | 命令/操作 | 结果 |
| --- | --- | --- |
| pytest | `pytest -q` | 记录 pass/fail 数 |
| frontend build | `npm run build` | 记录 |
| 无 Key 提示 | 未设 AI_API_KEY 点总结 | SSE error 中文 |
| B 站总结 | 有 Key + BV 链接 | 四 Tab 有内容 |
| 回归下载 | 原 parse/download | 不受影响 |

- [ ] **Step 4: Commit verification（可选，用户未要求则可只落盘不 commit）**

---

## Plan 自检

### Spec 覆盖

| Spec 章节 | 对应 Task |
| --- | --- |
| §5 API SSE 事件 | Task 4 |
| §6 字幕提取 | Task 2 |
| §7 Command API | Task 3 |
| §8 前端四 Tab | Task 6–7 |
| §10 错误处理 | Task 4（error 事件）+ Task 6（emit） |
| §12 测试 | Task 1–4 + Task 8 |
| §13 验收 | Task 8 |

### 占位扫描

- [x] 无 TBD / implement later
- [x] 环境变量、端点、文件路径均已明确
- [x] Command API 文档已引用

### 类型/命名一致性

- SSE 事件名：`subtitle` / `summary` / `mindmap` / `answer` / `done` / `error` — 前后端统一
- 字幕结构 `has_subtitle` / `full_text` — 与参考实现一致

---

## Next

**（计划已写入，须暂停 — 见 routing § 阶段门禁）**

- 确认计划 → 说「**开始实现**」或「**执行**」
- 需调整（例如模型名、是否升级 FastAPI 到 0.135 用原生 SSE）→ 直接说修改意见
- 计划确认后可进入 Tier 1 Leader 直做，落盘 `verification-lite.md`
