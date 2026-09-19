---
artifact: spec
route: superpowers:brainstorming
skills:
  - brainstorming
  - source-driven-development
skills_evidence:
  - brainstorming@~/.cursor/skills/brainstorming loaded
  - source-driven-development@harness-kit/.agents/skills/source-driven-development loaded
  - api-and-interface-design: skipped（不新增 HTTP 资源；沿用 /api/parse、/api/summarize、/api/chat）
source:
  - docs/需求文档.md §3.1 §3.4 §3.6
  - harness-kit/project.profile.md
  - harness-kit/context-map.md
  - frontend/src/App.vue
  - frontend/src/components/VideoSummary.vue
  - frontend/src/style.css
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-parse-workspace-stack.md
  - https://vuejs.org/guide/essentials/class-and-style.html
related_artifacts:
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - .ai-runtime-artifacts/specs/2026-09-19-summarize-export-polish-spec.md
  - .ai-runtime-artifacts/stack/2026-09-19-parse-workspace-stack.md
decisions:
  - 解析成功后进入「视频信息 + 总结面板」同屏工作区，桌面左右分栏，窄屏上下堆叠
  - 总结在解析成功后自动启动；左侧按钮改为重新生成，执行中禁用
  - Hero 在有结果后收成紧凑搜索条；展示态快捷键可重新露出标语，间距仍保持紧凑
  - 不引入 Tailwind；不拆独立路由；不改 SSE 与下载协议
created_at: 2026-09-19
status: draft
approved: false
---

# 解析后同屏工作区 Spec

## 1. 背景与目标

VidCatcher 首页当前是「高 Hero → 单列结果卡 → 手动展开总结」。解析成功后，用户要先滚过一段空白和口号，再点「AI 总结」才能对照视频信息阅读摘要。`docs/需求文档.md` §3.6 已要求总结与解析结果同页；§3.4 要求窄屏可用。一期总结能力（SSE、四 Tab）已经接通，缺的是**首屏信息密度**和**自动进入阅读态**。

**目标：** 解析成功后，搜索区让出垂直空间，视频元信息与总结面板同屏并列；总结自动开始；用户仍可手动重新生成。下载、清晰度选择、套餐/平台展示区保持原语义。

**成功标准：**

1. 桌面宽度下，结果区左右同屏：左栏视频信息（约 40%），右栏总结（约 60%），无需滚动即可同时看到封面与总结 Tab。
2. 解析成功即挂载总结面板并开始 SSE，不必先点按钮。
3. 有结果时 Hero 收缩为搜索条；标语、副文案、示例链接默认隐藏。
4. 窄屏回退为「视频在上、总结在下」。
5. 重新生成按钮在总结进行中不可点；完成后可再点。

## 2. 范围

### In scope

| 模块 | 内容 |
| --- | --- |
| Hero 状态 | 空态展开 / 有结果紧凑；展示态可重新露出标语 |
| 结果工作区 | 每条解析结果：左栏元信息 + 清晰度 + 下载 + 重新生成；右栏 `VideoSummary` |
| 总结启动 | 解析成功即挂载；用组件 `key` 控制重新生成 |
| 加载联动 | 总结面板向外报告 loading，供左侧按钮禁用 |
| 快捷键 | 非输入框内连续三次 Enter，切换展示态 |
| 样式 | 仅扩展 `style.css`，沿用现有 CSS 变量 |

### Out of scope

- 新增或修改 `/api/parse`、`/api/summarize`、`/api/chat` 字段
- 引入 Tailwind、CSS-in-JS、新路由、新页面
- 把 Hero / 结果卡拆成多个 SFC（现有 `App.vue` 单文件结构继续承担编排）
- VIP 真支付、登录、总结持久化
- 变更四 Tab 内容与导出能力（见 `2026-09-19-summarize-export-polish-spec.md`）

### 与已有方案的关系

`2026-09-19-video-summarize-spec.md` 把入口写成「用户点击 AI 总结」。本期把**首次触发**改为解析成功后自动启动；按钮语义改为「重新生成」。SSE 事件、字幕策略、密钥约束全部沿用，不重开后端设计。

## 3. 方案对比与推荐

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| **A. 同屏双栏工作区（推荐）** | 有结果后 Hero 收缩；结果区 `flex`/`grid` 左右分栏；总结默认挂载 | 首屏同时看到素材与结论；改动集中在 `App.vue` + `style.css` + 一处 emit | 多链接一次解析时，每条都会拉总结 |
| B. 保持单列，仅自动展开 | 解析后自动 `showSummary = true`，仍上下排列 | 改动最小 | 首屏仍看不到总结；Hero 仍占高 |
| C. 总结独立路由 | `/summary?url=` 新页 | 面板空间大 | 打断「解析 → 下载」主路径；与 §3.6「同页」不符 |

**推荐 A。** 后端契约不动，只调整首页编排与密度，符合学习向「薄封装 + 转化向前端」的边界。

## 4. 信息架构与页面结构

解析前：

1. Header
2. Hero（徽章 + 标题 + 副文案 + 搜索条 + 示例链接）
3. 功能 / 套餐 / 平台 / Footer

解析成功后：

1. Header
2. Hero（紧凑搜索条；展示态下标语可见，但上下内边距仍用紧凑档）
3. **工作区**（`max-width: 1280px` 量级，比现在的 900px 结果卡更宽，以便双栏）
   - 左栏 ≈ 40%：封面、标题、作者、平台、播放量、简介、清晰度、重新生成、下载
   - 右栏 ≈ 60%：现有 `VideoSummary` 四 Tab
4. 功能 / 套餐 / 平台 / Footer（位置与文案不变）

窄屏（沿用现有 `860px` 断点）：工作区改为单列，左栏在上、右栏在下。

## 5. 交互与状态

### 5.1 Hero

| 条件 | 内边距 | 徽章 / 标题 / 副文案 / 示例 |
| --- | --- | --- |
| `results.length === 0` | 现有宽松档 | 显示 |
| `results.length > 0` 且非展示态 | 紧凑档（约 `24–32px` 上下） | 隐藏 |
| `results.length > 0` 且展示态 | 仍用紧凑档 | 显示 |

搜索条始终可见。解析中按钮文案仍为「解析中...」。

实现方式：根节点 `:class="{ compact: hasResults, 'show-slogan': showSlogan }"`。`showSlogan` 在空态为 true；有结果时默认 false，展示态为 true。  
依据：<https://vuejs.org/guide/essentials/class-and-style.html>（`:class` 对象与静态 class 并存）。

### 5.2 自动总结与重新生成

- 每条结果在进入列表时即渲染 `VideoSummary`（去掉 `v-if="item.showSummary"`）。
- 现有面板 `onMounted → startSummarize()` 保持不变，因此挂载即启动。
- 每条结果带 `summaryKey`（数字）。父级把 `:key="item.summaryKey"` 绑到 `VideoSummary`；点「重新生成」只做 `summaryKey++`，触发卸载再挂载。
- 面板新增 `loading-change` 事件，把内部 `loading` 同步给该条 `item.summarizing`。
- 左栏按钮文案：`summarizing ? '总结中...' : '重新生成'`；`item.summarizing` 或 `item.busy` 时禁用。不再使用「收起 / 展开」。

### 5.3 展示态快捷键

- 在 `document` 上监听 `keydown`。
- 仅当 `event.key === 'Enter'`，且目标不是 `input, textarea, [contenteditable]`。
- 800ms 内累计 3 次则翻转 `presentMode`；超时清零。
- `onBeforeUnmount` 移除监听，避免泄漏。
- 该快捷键只影响标语显隐，不改搜索条、不改工作区分栏、不改总结进度。

### 5.4 多链接

现有 `parseAll` 仍按空白/逗号拆链接，并**整表替换**上一批结果。每条各自一排双栏、各自自动总结。一次贴很多链接会并发多路 SSE——接受为已知限制，不在本期做队列。

### 5.5 错误

解析失败、总结失败仍写页面顶部/Hero 下的 `error` 行，不改成 `alert`。下载进度与 CTA 语义不变。

## 6. 组件契约（前端内部）

`VideoSummary` 现有 props 不变：`videoUrl`、`videoTitle`。

新增：

| 方向 | 名称 | 类型 | 含义 |
| --- | --- | --- | --- |
| emit | `loading-change` | `boolean` | `loading` 变为 true/false 时各发一次；挂载开始总结时为 true，`done`/`error` 后为 false |

父级结果对象新增字段：

| 字段 | 初值 | 含义 |
| --- | --- | --- |
| `summaryKey` | `Date.now()` 或自增 | 强制重挂载 |
| `summarizing` | `false` | 左栏按钮禁用 |

删除字段：`showSummary`。

不改 `frontend/src/api/summarize.js`。

## 7. 视觉约束

- 颜色、圆角、按钮渐变继续用 `--blue` / `--vip` / `--page`，不另起皮肤。
- 左栏沿用现有结果卡白底与阴影；右栏沿用 `VideoSummary` 卡片，去掉「塞在左栏下面」时的多余顶边距。
- 左栏封面在双栏下可改为纵向铺满栏宽（不再强制 `240px + 文字` 横排），避免 40% 宽度里再切两列显得挤。窄屏恢复现在的封面在上、文字在下。
- 工作区左右间距约 `24px`。

## 8. 错误处理与边界

| 场景 | 行为 |
| --- | --- |
| 解析失败 | 不进入工作区；Hero 保持展开；展示错误文案 |
| 总结失败 | 右栏已有 error 回调；左栏 `summarizing` 回到 false，允许再点 |
| 封面加载失败 / 透明占位 | 继续用现有 `hasRealThumb` |
| 输入框里按 Enter | 走表单提交，不计入展示态连击 |
| 组件卸载 | 清掉 Enter 计时器与 keydown |

## 9. 测试与验收

仓库前端无单测框架，本期不以组件单测为门禁。

| 项 | 做法 |
| --- | --- |
| 构建 | `frontend` 下 `npm run build` 成功 |
| 后端回归 | 不改 Python；若本地有环境，可跑现有 `pytest` 确认无误伤 |
| 手工 | 空态 Hero 展开；解析后双栏 + 自动出流；按钮在生成中禁用；窄屏堆叠；三次 Enter 切换标语 |

## 10. Spec 自检

- 无 TBD / TODO。
- 与 `video-summarize-spec` 的冲突已写明：仅改「首次如何进入总结」，不改协议。
- 范围收在三个前端文件，不扩导出、不扩后端。
- 「约 40% / 60%」以 CSS `flex: 2 / 3` 或 `40% / 60%` 落实，断点与现网 `860px` 对齐，避免再引入一套栅格。

## Next

**（写入后须暂停，等用户明确继续 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 确认方案无误 → 说「写计划」或「制定实施计划」
- 变更范围小、无需计划 → 说「直接实现」或「直接做」
- 需要调整方案 → 直接说修改意见
