---
artifact: implementation-plan
route: superpowers:writing-plans
topic: AI 总结面板导出与排版
status: draft
approved: true
approved_by: 用户原话「开始实现吧」+「可以并行执行」
created_at: 2026-09-19
source:
  - .ai-runtime-artifacts/specs/2026-09-19-summarize-export-polish-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-summarize-export-stack.md
  - AGENTS.md
  - harness-kit/core/routing.md
skills:
  - writing-plans
skills_evidence:
  - writing-plans@~/.cursor/skills/writing-plans/SKILL.md loaded
dispatch: .ai-runtime-artifacts/plans/2026-09-19-summarize-export-polish-dispatch.md
---

# 总结面板排版与导出 Implementation Plan

> **For agentic workers:** 用户确认后由 Leader 在主 checkout 顺序执行（SSE 编码与前端解析必须同批上线）。Steps 用 `- [ ]` 跟踪。未经用户明确要求不要 `git commit`。

**Goal:** 在现有 AI 总结四 Tab 上补齐 Markdown 排版、字幕三种格式下载、思维导图全屏/导出，并让 SSE 流式正文保留换行。

**Architecture:** 后端只把 `summary`/`answer` token 打成 JSON 字符串；前端按 WHATWG SSE 规则拼接后再解码。导出逻辑拆到 `subtitleFormat.js` 与 `mindmapExport.js`，`VideoSummary.vue` 只负责交互。不引入 Tailwind，不新增 HTTP 下载接口。

**Tech Stack:** FastAPI `StreamingResponse`、标准库 `json`、Vue 3、marked 18、markmap-lib/view 0.18、Fullscreen API、Canvas `toBlob`。

---

## 变更范围一览

| 文件 | 动作 |
| --- | --- |
| `backend/app/api_summarize.py` | `summary` / `answer` 改为 `json.dumps(token)` |
| `backend/tests/test_api_summarize.py` | 增加含换行 token 的 SSE 断言 |
| `frontend/src/api/summarize.js` | 重写解析器；解码 JSON token |
| `frontend/src/utils/subtitleFormat.js` | **新建** SRT/VTT/TXT |
| `frontend/src/utils/mindmapExport.js` | **新建** bbox / PNG / SVG |
| `frontend/src/components/VideoSummary.vue` | 菜单、全屏、排版 class、接入工具模块 |
| `docs/需求文档.md` | §3.6 / §3.7 与本期能力对齐（可选，与代码同批） |

**不动：** `summarizer.py` prompt、parse/download、`ytdlp_service.py`。

---

### Task 1: SSE token 编码与后端测试

**Files:**
- Modify: `backend/tests/test_api_summarize.py`
- Modify: `backend/app/api_summarize.py`

- [ ] **Step 1: 先写失败测试**

在 `test_api_summarize.py` 追加：

```python
@patch("app.api_summarize._get_extractor")
@patch("app.api_summarize._get_summarizer")
def test_summarize_sse_encodes_summary_token_as_json(mock_sum, mock_ext):
    ext = MagicMock()
    ext.extract.return_value = {
        "has_subtitle": True,
        "language": "zh",
        "subtitle_type": "manual",
        "segments": [{"start": 0, "end": 1, "text": "你好"}],
        "full_text": "你好",
    }
    mock_ext.return_value = ext

    summarizer = MagicMock()
    summarizer.summarize_stream.return_value = iter(["概述\n\n- 要点"])
    summarizer.generate_mindmap.return_value = "# 图"
    mock_sum.return_value = summarizer

    with client.stream(
        "POST",
        "/api/summarize",
        json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
    ) as resp:
        body = "".join(resp.iter_text())

    encoded = json.dumps("概述\n\n- 要点", ensure_ascii=False)
    assert f"data: {encoded}" in body
    assert "event: summary" in body
```

文件顶部已有 `from unittest.mock import MagicMock, patch`，补：

```python
import json
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd backend && .venv/bin/pytest tests/test_api_summarize.py::test_summarize_sse_encodes_summary_token_as_json -q
```

Expected: FAIL（响应里是裸 token，不含 JSON 引号）

- [ ] **Step 3: 改路由**

`summarize_video` 循环改为：

```python
for token in summarizer.summarize_stream(full_text, req.language):
    yield _sse("summary", json.dumps(token, ensure_ascii=False))
    await asyncio.sleep(0)
```

`chat_with_video` 循环改为：

```python
for token in summarizer.chat_stream(subtitle_text, req.question):
    yield _sse("answer", json.dumps(token, ensure_ascii=False))
    await asyncio.sleep(0)
```

- [ ] **Step 4: 再跑测试**

```bash
cd backend && .venv/bin/pytest tests/test_api_summarize.py -q
```

Expected: PASS

---

### Task 2: 前端 SSE 解析器

**Files:**
- Modify: `frontend/src/api/summarize.js`

- [ ] **Step 1: 替换 `parseSSELine` + `handleSSEStream`**

整文件改为：

```javascript
/**
 * AI 视频总结 API：fetch + ReadableStream 读 SSE。
 * 解析规则对齐 WHATWG HTML §9.2.6。
 */

function decodeToken(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

async function handleSSEStream(response, callbacks) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  let dataLines = [];
  let hasData = false;

  function dispatch() {
    if (hasData && currentEvent) {
      const handler = callbacks[currentEvent];
      if (handler) {
        const payload = dataLines.join("\n");
        if (currentEvent === "summary" || currentEvent === "answer") {
          handler(decodeToken(payload));
        } else {
          handler(payload);
        }
      }
    }
    dataLines = [];
    hasData = false;
    currentEvent = "";
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line === "") {
        dispatch();
        continue;
      }
      if (line.startsWith(":")) continue;

      const colonIdx = line.indexOf(":");
      if (colonIdx < 0) continue;

      const field = line.slice(0, colonIdx);
      let val = line.slice(colonIdx + 1);
      if (val.startsWith(" ")) val = val.slice(1);

      if (field === "event") {
        currentEvent = val;
      } else if (field === "data") {
        hasData = true;
        dataLines.push(val);
      }
    }
  }

  dispatch();
}

export async function summarizeVideo(url, language = "zh", callbacks = {}) {
  const response = await fetch("/api/summarize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, language }),
  });

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }

  await handleSSEStream(response, callbacks);
}

export async function chatWithVideo(url, question, subtitleText = "", callbacks = {}) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, question, subtitle_text: subtitleText }),
  });

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }

  await handleSSEStream(response, callbacks);
}
```

`VideoSummary.vue` 里 `summary` / `answer` 回调改为直接 `+= data`（解析器已 decode）。去掉对 token 再 `JSON.parse` 的尝试，避免双重解析。

```javascript
summary: (data) => {
  summaryStreaming.value = true;
  summaryText.value += data;
  scrollSummaryToBottom();
},
```

```javascript
answer: (data) => {
  chatMessages.value[aiIdx].content += data;
  scrollChatToBottom();
},
```

---

### Task 3: 字幕格式纯函数

**Files:**
- Create: `frontend/src/utils/subtitleFormat.js`

- [ ] **Step 1: 写入模块**

```javascript
function pad(n, width = 2) {
  return String(n).padStart(width, "0");
}

export function formatSrtTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  return `${pad(h)}:${pad(m)}:${pad(s)},${pad(ms, 3)}`;
}

export function formatVttTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  return `${pad(h)}:${pad(m)}:${pad(s)}.${pad(ms, 3)}`;
}

export function segmentsToSrt(segments) {
  return segments
    .map((seg, i) => {
      const start = formatSrtTime(seg.start);
      const end = formatSrtTime(seg.end);
      return `${i + 1}\n${start} --> ${end}\n${seg.text}\n`;
    })
    .join("\n");
}

export function segmentsToVtt(segments) {
  const body = segments
    .map((seg) => `${formatVttTime(seg.start)} --> ${formatVttTime(seg.end)}\n${seg.text}\n`)
    .join("\n");
  return `WEBVTT\n\n${body}`;
}

export function segmentsToTxt(segments) {
  return segments.map((seg) => seg.text).join("\n");
}

export function safeDownloadName(title, fallback = "视频") {
  return (title || fallback).replace(/[\\/*?:"<>|]/g, "_").slice(0, 80);
}

export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function buildSubtitleBlob(segments, format) {
  if (format === "srt") {
    return { content: segmentsToSrt(segments), ext: "srt" };
  }
  if (format === "vtt") {
    return { content: segmentsToVtt(segments), ext: "vtt" };
  }
  return { content: segmentsToTxt(segments), ext: "txt" };
}
```

---

### Task 4: 思维导图导出纯函数

**Files:**
- Create: `frontend/src/utils/mindmapExport.js`

- [ ] **Step 1: 写入模块**

```javascript
import { triggerDownload } from "./subtitleFormat.js";

export function getContentBBox(svgEl) {
  const fallback = { x: 0, y: 0, width: 800, height: 600 };
  if (!svgEl) return fallback;

  const gRoot = svgEl.querySelector("g");
  if (gRoot) {
    try {
      const bbox = gRoot.getBBox();
      if (bbox.width > 0 && bbox.height > 0) {
        const transform = gRoot.getAttribute("transform") || "";
        const translateMatch = transform.match(/translate\(\s*([-\d.e]+)\s*[,\s]\s*([-\d.e]+)\s*\)/);
        const scaleMatch = transform.match(/scale\(\s*([-\d.e]+)/);
        const tx = translateMatch ? parseFloat(translateMatch[1]) : 0;
        const ty = translateMatch ? parseFloat(translateMatch[2]) : 0;
        const sc = scaleMatch ? parseFloat(scaleMatch[1]) : 1;
        return {
          x: bbox.x * sc + tx,
          y: bbox.y * sc + ty,
          width: bbox.width * sc,
          height: bbox.height * sc,
        };
      }
    } catch {
      /* getBBox 在未插入文档时可能抛错 */
    }
  }

  try {
    const bbox = svgEl.getBBox();
    if (bbox.width > 0 && bbox.height > 0) return bbox;
  } catch {
    /* ignore */
  }
  return fallback;
}

function sanitizeTransforms(root) {
  root.querySelectorAll("[transform]").forEach((el) => {
    const t = el.getAttribute("transform");
    if (t && t.includes("NaN")) {
      el.setAttribute("transform", "translate(0,0) scale(1)");
    }
  });
}

export function buildExportableSvg(svgEl) {
  if (!svgEl) return null;
  const cloned = svgEl.cloneNode(true);
  sanitizeTransforms(cloned);

  cloned.querySelectorAll("foreignObject").forEach((fo) => {
    const textContent = fo.textContent?.trim() || "";
    if (!textContent) {
      fo.remove();
      return;
    }
    const x = parseFloat(fo.getAttribute("x")) || 0;
    const y = parseFloat(fo.getAttribute("y")) || 0;
    const h = parseFloat(fo.getAttribute("height")) || 20;
    const textEl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    textEl.setAttribute("x", String(x + 4));
    textEl.setAttribute("y", String(y + h / 2 + 5));
    textEl.setAttribute("font-size", "14");
    textEl.setAttribute("font-family", "sans-serif");
    textEl.setAttribute("fill", "#333");
    textEl.setAttribute("dominant-baseline", "middle");
    textEl.textContent = textContent;
    fo.parentNode.replaceChild(textEl, fo);
  });

  return cloned;
}

export function setFullViewBox(svgClone, svgEl) {
  const dims = getContentBBox(svgEl);
  const padding = 60;
  const vx = dims.x - padding;
  const vy = dims.y - padding;
  const vw = dims.width + padding * 2;
  const vh = dims.height + padding * 2;
  svgClone.setAttribute("viewBox", `${vx} ${vy} ${vw} ${vh}`);
  svgClone.setAttribute("width", String(vw));
  svgClone.setAttribute("height", String(vh));
  return { vw, vh };
}

export function serializeSvg(svgEl, extraCss = "") {
  const serializer = new XMLSerializer();
  let svgString = serializer.serializeToString(svgEl);
  if (!svgString.includes("xmlns=")) {
    svgString = svgString.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
  }
  if (extraCss && !svgString.includes("<style")) {
    svgString = svgString.replace(">", `><style>${extraCss}</style>`);
  }
  return svgString;
}

export async function downloadMindmapPng(svgEl, filename, extraCss = "") {
  const exportSvg = buildExportableSvg(svgEl);
  if (!exportSvg) return false;
  const { vw, vh } = setFullViewBox(exportSvg, svgEl);
  const scale = Math.max(4, Math.ceil(3840 / vw));
  const svgString = serializeSvg(exportSvg, extraCss);

  const canvas = document.createElement("canvas");
  canvas.width = vw * scale;
  canvas.height = vh * scale;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const img = new Image();
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  return new Promise((resolve) => {
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((pngBlob) => {
        if (pngBlob) triggerDownload(pngBlob, filename);
        resolve(Boolean(pngBlob));
      }, "image/png");
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(false);
    };
    img.src = url;
  });
}

export function downloadMindmapSvg(svgEl, filename, extraCss = "") {
  if (!svgEl) return false;
  const cloned = svgEl.cloneNode(true);
  sanitizeTransforms(cloned);
  setFullViewBox(cloned, svgEl);
  const svgString = serializeSvg(cloned, extraCss);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  triggerDownload(blob, filename);
  return true;
}
```

---

### Task 5: 面板交互与排版

**Files:**
- Modify: `frontend/src/components/VideoSummary.vue`

- [ ] **Step 1: script 增加 marked 配置与工具导入**

在现有 import 后追加：

```javascript
import { onBeforeUnmount } from "vue";
import {
  buildSubtitleBlob,
  safeDownloadName,
  triggerDownload,
} from "../utils/subtitleFormat.js";
import { downloadMindmapPng, downloadMindmapSvg } from "../utils/mindmapExport.js";

marked.use({ gfm: true, breaks: true });
```

（`onMounted` 已导入则改成 `import { ref, watch, nextTick, onMounted, onBeforeUnmount } from "vue"`。）

新增状态与函数（插入 `renderMindmap` 附近，并保存 `markmapInstance`）：

```javascript
const mindmapContainer = ref(null);
let markmapInstance = null;
const isFullscreen = ref(false);
const showSubtitleDropdown = ref(false);
const subtitleDropdownRef = ref(null);
const subtitleFormats = [
  { key: "srt", label: "SRT 字幕", ext: "srt" },
  { key: "vtt", label: "VTT 字幕", ext: "vtt" },
  { key: "txt", label: "纯文本", ext: "txt" },
];
const exportHint = ref("");

function renderMindmap(md) {
  if (!mindmapSvg.value) return;
  try {
    mindmapSvg.value.innerHTML = "";
    const transformer = new Transformer();
    const { root } = transformer.transform(md);
    markmapInstance = Markmap.create(mindmapSvg.value, { autoFit: true }, root);
  } catch (e) {
    console.warn("思维导图渲染失败:", e);
  }
}

async function toggleFullscreen() {
  if (!mindmapContainer.value) return;
  try {
    if (!document.fullscreenElement) {
      const el = mindmapContainer.value;
      if (el.requestFullscreen) await el.requestFullscreen();
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    } else if (document.exitFullscreen) {
      await document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
  } catch (e) {
    console.warn("全屏不可用:", e);
  }
}

function onFullscreenChange() {
  isFullscreen.value = Boolean(document.fullscreenElement);
  nextTick(() => {
    if (markmapInstance) markmapInstance.fit();
  });
}

function handleClickOutside(e) {
  if (subtitleDropdownRef.value && !subtitleDropdownRef.value.contains(e.target)) {
    showSubtitleDropdown.value = false;
  }
}

function downloadSubtitle(format) {
  showSubtitleDropdown.value = false;
  const segments = subtitleData.value.segments;
  if (!segments?.length) return;
  const { content, ext } = buildSubtitleBlob(segments, format);
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  triggerDownload(blob, `${safeDownloadName(props.videoTitle)} - 字幕.${ext}`);
}

async function onDownloadPng() {
  exportHint.value = "";
  const ok = await downloadMindmapPng(
    mindmapSvg.value,
    `${safeDownloadName(props.videoTitle)} - 思维导图.png`,
  );
  if (!ok) exportHint.value = "PNG 导出失败，请改用 SVG";
}

function onDownloadSvg() {
  downloadMindmapSvg(
    mindmapSvg.value,
    `${safeDownloadName(props.videoTitle)} - 思维导图.svg`,
  );
}

onMounted(() => {
  startSummarize();
  document.addEventListener("fullscreenchange", onFullscreenChange);
  document.addEventListener("webkitfullscreenchange", onFullscreenChange);
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("fullscreenchange", onFullscreenChange);
  document.removeEventListener("webkitfullscreenchange", onFullscreenChange);
  document.removeEventListener("click", handleClickOutside);
});
```

问答气泡的 assistant 成品加上 `class="chat-prose"`：

```html
<div v-else-if="msg.role === 'assistant'" class="chat-prose" v-html="renderMarkdown(msg.content)"></div>
```

- [ ] **Step 2: 字幕头增加下载菜单**

放在 `subtitle-head` 内、展开按钮旁：

```html
<div
  v-if="subtitleData.segments.length"
  ref="subtitleDropdownRef"
  class="export-menu"
>
  <button
    type="button"
    class="export-btn"
    @click.stop="showSubtitleDropdown = !showSubtitleDropdown"
  >
    下载字幕
  </button>
  <div v-if="showSubtitleDropdown" class="export-pop">
    <button
      v-for="fmt in subtitleFormats"
      :key="fmt.key"
      type="button"
      class="export-item"
      @click="downloadSubtitle(fmt.key)"
    >
      {{ fmt.label }}
      <span class="export-ext">.{{ fmt.ext }}</span>
    </button>
  </div>
</div>
```

- [ ] **Step 3: 导图工具条与全屏容器**

把思维导图 Tab 换成：

```html
<div v-show="activeTab === 'mindmap'">
  <div v-if="mindmapMarkdown" ref="mindmapContainer" class="mindmap-wrap" :class="{ fullscreen: isFullscreen }">
    <div class="mindmap-toolbar">
      <button type="button" class="export-btn" @click="onDownloadPng">PNG</button>
      <button type="button" class="export-btn" @click="onDownloadSvg">SVG</button>
      <button type="button" class="export-btn" @click="toggleFullscreen">
        {{ isFullscreen ? "退出全屏" : "全屏" }}
      </button>
    </div>
    <p v-if="exportHint" class="summary-muted small">{{ exportHint }}</p>
    <svg ref="mindmapSvg" class="mindmap-svg"></svg>
  </div>
  <!-- 保留原 loading / empty 分支 -->
</div>
```

- [ ] **Step 4: 样式**

在现有 `.summary-prose` 规则上扩到完整集合，并加菜单 / 全屏 / `.chat-prose`。关键块：

```css
.export-menu {
  position: relative;
}
.export-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  font-size: 12px;
  cursor: pointer;
}
.export-pop {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 160px;
  background: #fff;
  border: 1px solid var(--line-light);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
  padding: 6px;
  z-index: 5;
}
.export-item {
  width: 100%;
  display: flex;
  justify-content: space-between;
  border: none;
  background: transparent;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}
.export-item:hover {
  background: var(--blue-soft);
}
.export-ext {
  color: var(--soft);
}
.mindmap-toolbar {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--line-light);
}
.mindmap-wrap.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 40;
  border-radius: 0;
  border: none;
  background: #fff;
}
.mindmap-wrap.fullscreen .mindmap-svg {
  min-height: calc(100vh - 56px);
}
.summary-prose :deep(h1) { /* 1.25rem / 底边 --blue-soft */ }
.summary-prose :deep(blockquote) { border-left: 3px solid var(--blue); background: var(--page); }
.summary-prose :deep(pre) { background: #1e293b; color: #e2e8f0; border-radius: 8px; padding: 1rem; }
.chat-prose :deep(p:last-child) { margin-bottom: 0; }
```

实现时按 spec §5.2 把 h1–a、table、code 写全，不要留「等」字样的省略。

---

### Task 6: 需求文档口径（可选同批）

**Files:**
- Modify: `docs/需求文档.md`

- [ ] **Step 1:** §3.6 总结摘要补「完成后按 GFM 排版」；字幕补「可下载 SRT / VTT / TXT」；思维导图补「全屏与 PNG/SVG 导出」。§3.7 字幕下载一行改为「字幕翻译」仍预留。

不要写外部仓库名或「移植 / 对齐某项目」一类表述。

---

### Task 7: 验证

- [ ] **Step 1: 后端**

```bash
cd backend && .venv/bin/pytest tests/test_api_summarize.py tests/test_summarizer.py -q
```

Expected: 全绿

- [ ] **Step 2: 前端构建**

```bash
cd frontend && npm run build
```

Expected: 无 error

- [ ] **Step 3: 手工（有浏览器时）**

有字幕链接走一遍：摘要换行、三种字幕文件、导图全屏、缩放后导出 PNG/SVG。无浏览器工具时在 verification 里写明未做项。

- [ ] **Step 4: 落盘** `verifications/2026-09-19-summarize-export-polish-verification-lite.md`

---

## Plan 自检

1. **Spec 覆盖：** SSE → Task 1–2；排版 → Task 5；字幕 → Task 3+5；导图 → Task 4–5；需求口径 → Task 6；验收 → Task 7。
2. **无 TBD。** 提交步骤已按用户规则省略。
3. **类型一致：** `buildSubtitleBlob(segments, format)`、`safeDownloadName`、`downloadMindmapPng(svgEl, filename)` 前后统一。
4. **dispatch:** 前后端必须同批，故 `n/a`，不拆并行 WU。

---

## Next

**（写入后须暂停 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 计划确认 → 说「**开始实现**」或「**执行**」
- 需要调整 → 直接说修改意见
- 想拆并行 → 本计划刻意单线程，不建议拆
