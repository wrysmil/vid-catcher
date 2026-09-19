---
artifact: implementation-plan
route: superpowers:writing-plans
skills:
  - writing-plans
  - source-driven-development
skills_evidence:
  - writing-plans@harness-kit/.agents/skills/writing-plans loaded
  - source-driven-development@harness-kit/.agents/skills/source-driven-development loaded
dispatch: n/a
source:
  - AGENTS.md
  - harness-kit/core/routing.md
  - .ai-runtime-artifacts/specs/2026-09-19-parse-workspace-layout-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-parse-workspace-stack.md
created_at: 2026-09-19
status: draft
approved: false
---

# 解析后同屏工作区 Implementation Plan

> **For agentic workers:** 本计划在 VidCatcher 主 checkout 顺序执行（`dispatch: n/a`）。用户单独说「开始实现」后再改业务代码。提交只在用户明确要求时进行。

**Goal:** 解析成功后，首页收成紧凑搜索条，并让视频信息与 AI 总结左右同屏；总结自动开始，按钮只负责重新生成。

**Architecture:** 状态仍留在 `App.vue`。有结果时给 Hero 加 `compact` class；每条结果改成工作区行，左卡右总结。`VideoSummary` 增加 `loading-change`，父级用 `summaryKey` 强制重挂载。样式只加在 `style.css`，沿用现有变量与 `860px` 断点。

**Tech Stack:** Vue 3.5、Vite 6、原生 CSS。不新增 npm 包。Class 绑定按 <https://vuejs.org/guide/essentials/class-and-style.html>。

---

## 文件地图

| 文件 | 职责 |
| --- | --- |
| `frontend/src/components/VideoSummary.vue` | 向外报告 `loading`；其余 Tab / SSE 不动 |
| `frontend/src/App.vue` | Hero 状态、展示态快捷键、工作区结构、`summaryKey` |
| `frontend/src/style.css` | 紧凑 Hero、工作区双栏、左栏纵向封面 |

不新建 SFC，不改 `frontend/src/api/summarize.js`，不改 `backend/`。

---

### Task 1: 总结面板报告 loading

**Files:**
- Modify: `frontend/src/components/VideoSummary.vue`

- [ ] **Step 1: 增加 emit，并在 `loading` 变化时同步**

在现有 `defineEmits(["error"])` 改为同时声明 `loading-change`。在 `startSummarize` 里每次改 `loading.value` 的前后，或用 `watch(loading, ...)` 统一发出：

```js
const emit = defineEmits(["error", "loading-change"]);

watch(loading, (value) => {
  emit("loading-change", value);
}, { immediate: true });
```

`watch` 从 `vue` 的现有 import 补上（文件已 import `ref, watch, nextTick, onMounted`）。`immediate: true` 保证父级在挂载当下就能禁用按钮。

不要改 `startSummarize` 的 SSE 分支逻辑。

- [ ] **Step 2: 自检**

确认模板里没有使用新 prop。`onMounted(() => startSummarize())` 保持原样。

---

### Task 2: App 编排工作区与 Hero 状态

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 增加展示态与派生量**

在 script 顶部 import 补 `onMounted`（已有 `onBeforeUnmount`、`computed`、`ref`）：

```js
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
```

新增状态（名称固定，后续 Task 3 的 class 依赖它们）：

```js
const presentMode = ref(false);
const hasResults = computed(() => results.value.length > 0);
const showSlogan = computed(() => !hasResults.value || presentMode.value);
```

- [ ] **Step 2: 注册三次 Enter 快捷键**

```js
let enterCount = 0;
let enterTimer = null;

function onGlobalKeydown(event) {
  if (event.key !== "Enter") return;
  const target = event.target;
  if (target instanceof Element && target.matches("input, textarea, [contenteditable]")) {
    return;
  }
  enterCount += 1;
  clearTimeout(enterTimer);
  if (enterCount >= 3) {
    presentMode.value = !presentMode.value;
    enterCount = 0;
    return;
  }
  enterTimer = setTimeout(() => {
    enterCount = 0;
  }, 800);
}

onMounted(() => {
  document.addEventListener("keydown", onGlobalKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onGlobalKeydown);
  clearTimeout(enterTimer);
  timers.forEach(clearInterval);
});
```

把原来 `onBeforeUnmount` 里只清 `timers` 的逻辑合并进上面这一段，避免两个卸载钩子打架。

- [ ] **Step 3: 解析结果补字段，去掉展开开关**

`parseAll` 里 `next.push({...})` 删除 `showSummary: false`，改为：

```js
summaryKey: Date.now() + next.length,
summarizing: false,
```

`results.value = next` 时顺带 `presentMode.value = false`，避免上一次展示态残留。

新增：

```js
function restartSummary(item) {
  if (item.summarizing) return;
  item.summaryKey += 1;
}

function onSummaryLoading(item, isLoading) {
  item.summarizing = Boolean(isLoading);
}
```

- [ ] **Step 4: 改 Hero 模板 class 与条件渲染**

Hero `section`：

```html
<section id="top" class="hero" :class="{ compact: hasResults }">
```

徽章、`h1`、`.lead`、`.tries` 分别加 `v-if="showSlogan"`。搜索表单与 `error-line` 始终渲染。

- [ ] **Step 5: 结果区改成工作区双栏**

把现在的

```html
<section v-if="results.length" class="results">
  <article v-for="item in results" :key="item.key" class="result-card">
    ...
    <div class="summary-row">...</div>
    <VideoSummary v-if="item.showSummary" ... />
    <div class="download-row">...</div>
  </article>
</section>
```

改成（结构必须按此分层，class 名与 Task 3 对齐）：

```html
<section v-if="results.length" class="workspace">
  <div v-for="item in results" :key="item.key" class="workspace-row">
    <article class="result-card workspace-meta">
      <!-- 保留现有 result-head / quality / download-row -->
      <div class="summary-row">
        <button
          type="button"
          class="summary-btn"
          :disabled="item.busy || item.summarizing"
          @click="restartSummary(item)"
        >
          {{ item.summarizing ? "总结中..." : "重新生成" }}
        </button>
      </div>
    </article>
    <div class="workspace-summary">
      <VideoSummary
        :key="item.summaryKey"
        :video-url="item.url"
        :video-title="item.title"
        @error="(msg) => (error = msg)"
        @loading-change="(on) => onSummaryLoading(item, on)"
      />
    </div>
  </div>
</section>
```

`result-head`、清晰度、下载按钮的内部标记保持不动，避免回归下载主路径。

---

### Task 3: 样式 — 紧凑 Hero 与双栏

**Files:**
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Hero 紧凑档**

在现有 `.hero { padding: 72px 20px 36px; }` 后追加，不要改空态观感：

```css
.hero.compact {
  padding: 28px 20px 16px;
}

.hero.compact .capsule {
  margin-top: 0;
}

.hero.compact h1 {
  margin-top: 12px;
  font-size: clamp(28px, 4vw, 36px);
}

.hero.compact .lead {
  margin-top: 8px;
}

.hero.compact .tries {
  margin-top: 12px;
}
```

标语显隐由模板 `v-if` 控制，CSS 不负责 `display:none`。

- [ ] **Step 2: 工作区双栏**

用新的 `.workspace` 替换（或旁路）旧 `.results` 宽度限制。旧 `.results` 规则可留着但不再被模板使用。

```css
.workspace {
  width: min(1280px, calc(100% - 40px));
  margin: 8px auto 0;
  display: grid;
  gap: 20px;
}

.workspace-row {
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.workspace-meta {
  flex: 0 0 40%;
  max-width: 40%;
  min-width: 0;
}

.workspace-summary {
  flex: 1 1 60%;
  min-width: 0;
}

.workspace-summary .summary-panel {
  margin-top: 0;
}

.workspace-meta .result-head {
  grid-template-columns: 1fr;
}

.workspace-meta .thumb {
  height: 180px;
}
```

- [ ] **Step 3: 窄屏回退**

在现有 `@media (max-width: 860px)` 内追加：

```css
.workspace-row {
  flex-direction: column;
}

.workspace-meta {
  flex-basis: auto;
  max-width: none;
  width: 100%;
}
```

不要改该断点里已经存在的 `.nav-links` / `.features` 规则。

---

### Task 4: 验证

**Files:** 无新文件

- [ ] **Step 1: 前端构建**

```bash
npm run build
```

工作目录：`frontend/`。期望：Vite 退出码 0。

- [ ] **Step 2: 手工清单（有浏览器时）**

1. 打开首页：徽章、大标题、示例链接可见。
2. 解析一条公开视频：Hero 收缩；左侧封面与右侧 Tab 同屏；右栏自动出现「正在提取视频字幕」。
3. 生成过程中左侧按钮为「总结中...」且不可点。
4. 完成后按钮变为「重新生成」，点击后面板重挂载并重新出流。
5. 视口收到 375px：总结跑到视频卡下方。
6. 焦点不在输入框时连按三次 Enter：标语回来，Hero 仍是紧凑间距；再三次恢复隐藏。
7. 输入框内回车：只触发解析，不切换展示态。
8. 下载主按钮与进度条仍可用。

- [ ] **Step 3: 后端（仅防误伤）**

未改 Python。若环境可用：

```bash
python -m pytest
```

工作目录：`backend/`。期望：既有用例通过。

- [ ] **Step 4: 提交**

默认不做。用户说「提交」后再按 `git-xywh` + `project.git.md` 处理。

---

## Plan 自检

| Spec 条目 | 对应 Task |
| --- | --- |
| 桌面 40% / 60% 同屏 | Task 2 结构 + Task 3 flex |
| 解析后自动总结 | Task 2 去掉 `v-if`，沿用面板 `onMounted` |
| 按钮改为重新生成且执行中禁用 | Task 1 emit + Task 2 `restartSummary` |
| Hero 收缩、展示态三次 Enter | Task 2 `showSlogan` / `onGlobalKeydown` + Task 3 compact |
| 窄屏堆叠 | Task 3 `860px` |
| 不改 API / 不引入 Tailwind | 文件地图已排除 |

无 TBD。事件名全程是 `loading-change`，字段名全程是 `summaryKey` / `summarizing` / `presentMode`。

## Next

**（写入后须暂停 — 即使用户句末含「然后执行」）**

- 计划确认 → 说「开始实现」或「执行」
- 需要调整 → 直接说修改意见
- 本计划 `dispatch: n/a`，确认后由 Leader 在主 checkout 顺序落地，不拆并行 WU
