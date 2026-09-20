---
route: planning
topic: VidCatcher GEO 生成式引擎优化
status: draft
approved: false
date: 2026-09-20
author: Leader
artifact: plan
source:
  - .ai-runtime-artifacts/specs/2026-09-20-geo-optimization-spec.md
related_artifacts:
  - .ai-runtime-artifacts/specs/2026-09-20-geo-optimization-spec.md
  - .ai-runtime-artifacts/specs/2026-09-20-seo-optimization-spec.md
  - .ai-runtime-artifacts/plans/2026-09-20-seo-optimization-plan.md
---

# VidCatcher GEO 优化 - 实施计划

## 0. 决策记录

- **目标引擎**：国内 AI 助手（豆包/文心/通义/Kimi/DeepSeek/讯飞）
- **范围**：静态层 + 内容层（用户选定）
- **GitHub**：占位 `https://github.com/REPLACE_WITH_YOUR_REPO`，注释 TODO
- **架构边界**：仅扩展 `frontend/index.html`、`frontend/public/`、`frontend/src/App.vue`、`frontend/src/style.css`；不动业务代码与构建配置

## 1. 范围锁定

### 1.1 允许修改文件

| 文件 | 变更类型 |
|------|----------|
| `frontend/index.html` | 改 |
| `frontend/public/llms.txt` | 新增 |
| `frontend/public/sitemap.xml` | 改 |
| `frontend/public/robots.txt` | 改 |
| `frontend/src/App.vue` | 改（追加 3 section + 3 nav 项） |
| `frontend/src/style.css` | 改（追加 ~85 行新 CSS） |

### 1.2 禁止触碰

- `frontend/vite.config.js` / `package.json`
- `frontend/src/main.js` / `api/*` / `utils/*` / `components/VideoSummary.vue`
- `backend/app/*.py` / `backend/tests/*`

## 2. WU 拆解

### WU-1：llms.txt + robots/sitemap 扩展

**类型**：implementer
**依赖**：无
**风险**：低

**产出**：
1. `frontend/public/llms.txt` —— llmstxt.org 规范，~60 行
2. `frontend/public/sitemap.xml` —— 单 url → 7 个 url（section 锚点）
3. `frontend/public/robots.txt` —— 追加 `Allow: /llms.txt` + 4 个 LLM UA（ChatGPT-User / Claude-Web / PerplexityBot / Applebot-Extended）

**验收**：HTTP 200，文件格式合法

---

### WU-2：index.html Dublin Core + 4 个新 JSON-LD

**类型**：coder
**依赖**：无（与 WU-1 并行）
**风险**：中（涉及 JSON-LD @id 互引）

**产出**：
1. 在 `<head>` 中加入 13 个 Dublin Core meta（DC.title / DC.creator / DC.subject / DC.description / DC.publisher / DC.contributor / DC.date / DC.type / DC.format / DC.identifier / DC.language / DC.relation / DC.rights）
2. 调整既有 3 个 JSON-LD：
   - WebSite 加 `@id`
   - SoftwareApplication 加 `@id` + `author` 指向 Organization
   - FAQPage 加 `@id`
3. 新增 4 个 JSON-LD：
   - Organization（`@id`, `sameAs: [GitHub 占位]`, `knowsAbout: [7 项]`）
   - WebPage（`@id`, `isPartOf: WebSite`, `about: SoftwareApplication`, `primaryImageOfPage`, `datePublished/Modified`, `significantLink: 6 锚点`）
   - HowTo（`@id`, 4 步骤，与 App.vue how-to 一致）
   - BreadcrumbList（`@id`, 6 项导航）

**验收**：JSON-LD 共 7 个，@id 互引正确，JSON.parse 不报错

---

### WU-3：App.vue 三新区块 + nav 扩展 + CSS

**类型**：coder
**依赖**：无（与 WU-1/WU-2 并行）
**风险**：中（修改 App.vue 是最敏感的一步）

**产出**：

#### 3.1 `<template>` 追加（platforms section 之后、footer 之前）

1. `<section id="how-to">` —— 4 步使用流程
2. `<section id="faq">` —— 7 个 `<details>` 折叠问答
3. `<section id="about">` —— 4 个 about-card（项目背景 / 技术栈 / 开源协议 / 反馈）

#### 3.2 nav 扩展（现有 3 个 → 6 个）
- `#how-to`
- `#faq`
- `#about`

#### 3.3 `<style>` 追加

约 85 行新 CSS：
- `.how-to-steps` / `.step-num`（how-to 区块）
- `.faq-item` / `details/summary`（faq 区块）
- `.about-grid` / `.about-card`（about 区块）
- 全部使用现有 CSS 变量（`--blue / --paper / --line / --ink / --muted`）

#### 3.4 内容与 JSON-LD 一致性

- FAQ 7 条与 JSON-LD FAQPage 5 条 + 2 条新增（前端零持久化 / 下载失败原因）
- HowTo 4 步与 JSON-LD HowTo 完全一致

**验收**：
- `#how-to` / `#faq` / `#about` 在 DOM 中可定位
- nav 含 6 个 `<a>` 链接
- 现有所有 section 与功能（Hero / 解析按钮 / 工作区 / features / plans / platforms / footer）完好
- 解析/下载/AI 总结三链路零回归

---

### WU-4：构建验证 + smoke

**类型**：coder
**依赖**：WU-1 / WU-2 / WU-3
**风险**：中

**步骤**：
1. `npm run build` exit 0
2. 检查 `dist/llms.txt` / `dist/sitemap.xml` / `dist/robots.txt` 全部 200
3. 检查 `dist/index.html` 含 13 DC meta + 7 JSON-LD
4. 用 Playwright 访问 http://127.0.0.1:5173/：
   - 验证 nav 6 项
   - 验证 how-to / faq / about 三 section 渲染
   - 验证 JSON.parse 7 个 schema
   - 验证 favicon / og-image / llms.txt / sitemap / robots 全部可访问
   - 验证 Lighthouse SEO ≥ 95（条件允许）
5. 业务零回归 smoke：现有 UI 元素完好

---

## 3. 执行顺序

```
启动 ──→ WU-1（llms + robots + sitemap）   ─┐
     ──→ WU-2（index.html DC + JSON-LD）    ─┼─→ WU-4（构建验证 + smoke）
     ──→ WU-3（App.vue 三 section + CSS）   ─┘
```

理论可并行；实际由 Leader 串行执行（文件数少、确定性高、避免 subagent 边界协调成本）。

## 4. 风险与回滚

| 风险 | 回滚方式 |
|------|----------|
| App.vue section 引入样式冲突 | `git checkout` 恢复 App.vue / style.css |
| JSON-LD @id 互引错误 | 用 Playwright 验证 JSON.parse；失败时恢复 index.html |
| 窄屏 nav 溢出 | 留作下期汉堡菜单，本期不强制改造 |
| GitHub 占位 URL 未替换 | 部署文档标注 TODO |

## 5. 验收口径（与 spec §9 对齐）

| # | 项 | 通过 |
|---|----|------|
| 1 | `/llms.txt` 200，含 `# VidCatcher` + `## 核心能力` + Q/A 块 | ✅ |
| 2 | `index.html` 含 7 个 JSON-LD（WebSite + SoftwareApplication + FAQPage + Organization + WebPage + HowTo + BreadcrumbList） | ✅ |
| 3 | @id 互引正确（WebPage.isPartOf=WebSite, about=SoftwareApplication; SoftwareApplication.author=Organization） | ✅ |
| 4 | Dublin Core meta ≥ 10 个 | ✅ |
| 5 | App.vue 三 section（#how-to / #faq / #about）+ nav 6 项 | ✅ |
| 6 | FAQ 内容与 JSON-LD FAQPage 一致（7 ≥ 5） | ✅ |
| 7 | HowTo 步骤与 JSON-LD HowTo 一致 | ✅ |
| 8 | sitemap 含 7 个 `<url>` | ✅ |
| 9 | robots.txt 含 ChatGPT-User / Claude-Web / PerplexityBot / Applebot-Extended + Allow /llms.txt | ✅ |
| 10 | 业务零回归（解析/下载/AI 总结） | ✅ |
| 11 | npm run build exit 0 | ✅ |
| 12 | Lighthouse SEO ≥ 95 | ✅ |

## 6. 后续（二期）

- AI 引擎主动提交（Perplexity / Bing IndexNow）
- 多语言 AI 摘要（英文 / 日文）
- 内容营销：长尾文章页
- Vite prerender

---

## Plan 自检

- [x] 范围严格收敛到 6 个允许文件
- [x] WU 依赖清晰
- [x] 风险与回滚方案明确
- [x] 验收 12 项，可量化

---

## Next

用户已明确授权「开始实现」，本 plan 写完后 Leader 直接进入 WU-1。