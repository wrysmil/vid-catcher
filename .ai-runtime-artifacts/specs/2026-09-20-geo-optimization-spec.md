---
route: brainstorming
topic: VidCatcher GEO 生成式引擎优化
status: draft
approved: false
date: 2026-09-20
author: Leader
artifact: spec
skills:
  - seo-audit（其 references/ai-writing-detection.md + ai-seo 相关背景）
  - source-driven-development
source:
  - .ai-runtime-artifacts/specs/2026-09-20-seo-optimization-spec.md（既有 SEO 资产）
  - .ai-runtime-artifacts/plans/2026-09-20-seo-optimization-plan.md
  - frontend/index.html（既有 meta 与 JSON-LD）
  - frontend/src/App.vue（既有页面结构）
  - docs/需求文档.md
decisions:
  - 目标引擎: 国内 AI 助手（豆包 / 文心一言 / 通义千问 / Kimi / 讯飞星火 / DeepSeek）
  - 范围: 静态层 + 内容层（用户选定）
  - 权威信号: 仅 GitHub 项目源链接声明（占位 URL，不代贴）
  - 架构边界: 仅扩展 frontend/index.html、frontend/public/、frontend/src/App.vue（仅追加 section，不动现有 section 与业务逻辑）
  - 不做: 多语言 AI 摘要、独立路由页（/faq.html）、Schema.org DefinedTerm、外部反向链接运营
  - 同 SEO: 不改 vite.config.js / package.json / 后端 / 解析 / 下载 / AI 总结业务代码
  - 工具: llms.txt（llmstxt.org 规范 2024-Q4）+ 增强 JSON-LD + Dublin Core meta + App.vue 三新区块
---

# VidCatcher GEO 生成式引擎优化 Spec

## 1. 背景与目标

### 1.1 现状（基于 SEO 优化后资产）

| 资产 | 状态 |
| --- | --- |
| `<meta description>` 含主关键词 | ✅ 已有 |
| `<meta keywords>` 主词 + 长尾 | ✅ 已有 |
| `<link rel="canonical">` | ✅ 已有 |
| OG / Twitter 卡片 | ✅ 已有 |
| JSON-LD `SoftwareApplication` + `FAQPage` + `WebSite` | ✅ 已有 |
| `robots.txt` / `sitemap.xml` / `icon.svg` / `og-image.svg` | ✅ 已有 |

### 1.2 GEO 缺口（**本 spec 要补**）

| 缺口 | 影响 | 严重度 |
| --- | --- | --- |
| 无 `llms.txt` | 国内 AI 引擎抓取站点时无 LLM 友好的结构化导航 | 高 |
| JSON-LD 缺 `Organization` / `Article` / `HowTo` / `BreadcrumbList` | AI 引擎无法识别品牌、页面类型、操作步骤、面包屑结构 | 高 |
| 无 `Dublin Core` meta | 学术性元数据，AI 引擎对 dc.* 系列识别度高 | 中 |
| 无 AI 内容标识（`ai-content-declaration` 等） | 部分 AI 引擎会优先采用有明确署名的内容 | 中 |
| 页面正文无「怎么用」「FAQ」「关于」对应区块 | JSON-LD `FAQPage` / `HowTo` 缺视觉对应，用户看不到，AI 引擎置信度降低 | 高 |
| 无品牌「sameAs」反向链接占位 | AI 引擎对权威信号识别弱 | 中 |

### 1.3 目标

- **T1（必达）**：让豆包 / 文心 / 通义 / Kimi / DeepSeek / 讯飞等国内 AI 引擎在用户提问「视频下载」「怎么下 B 站视频」「AI 视频总结」时，能从 VidCatcher 提取到完整答案
- **T2（必达）**：JSON-LD 中至少 6 个 schema 被正确识别（WebSite + SoftwareApplication + FAQPage + Organization + Article + HowTo）
- **T3（必达）**：页面提供可被 AI 抓取的 3 个结构化文本区块（HowTo / FAQ / About），与对应 JSON-LD 双向印证
- **T4（扩展）**：预留 GitHub sameAs 占位，为后续反向链接运营铺路

### 1.4 非目标

- 不改业务代码（解析 / 下载 / AI 总结链路）
- 不做多语言 AI 摘要（仅中文）
- 不做独立路由页（如 /faq.html），所有内容在单页 App.vue 内
- 不在本次接入 AI 引擎主动提交 API（多数国内 AI 引擎无公开 API）
- 不引入 LLM 微调或知识图谱

## 2. 方案对比与推荐

| 方案 | 优点 | 缺点 | 推荐 |
| --- | --- | --- | --- |
| **A. llms.txt + 增强 JSON-LD + App.vue 三新区块（推荐）** | 业界共识 GEO 范式；与 SEO 资产叠加；内容层让 AI 与用户都能看到 FAQ / HowTo / About | 修改 App.vue 增加 ~150 行，但都是纯展示 section，不碰现有逻辑 | **是** |
| B. 仅 llms.txt + JSON-LD | 最小风险 | AI 引擎需要正文印证；JSON-LD 孤证可信度低于「结构化正文 + 结构化数据」双印证 | 否 |
| C. 独立路由 + Markdown 内容页 | 内容营销最佳实践 | 涉及 vue-router 引入，超出「不引入新依赖 / 不改架构」约束；超出当前 SPA 单页范围 | 否 |

**推荐方案 A。**

## 3. llms.txt 设计（参考 llmstxt.org 2024-Q4 规范）

### 3.1 文件位置

`frontend/public/llms.txt`

### 3.2 内容结构

```text
# VidCatcher

> 万能视频下载与 AI 视频总结工具，基于开源 yt-dlp 引擎，支持 1800+ 视频平台在线解析与免费下载，同时提供 AI 视频总结、字幕提取、思维导图、AI 问答等高级能力。

VidCatcher 是一个开源学习项目（前端 Vue 3 + 后端 FastAPI + yt-dlp + DeepSeek LLM），为个人用户提供跨平台视频下载与 AI 内容理解能力。

## 核心能力
- [视频下载](/#top)：粘贴链接 → 解析 → 选清晰度 → 下载，360p 至 4K 多档位可选
- [AI 视频总结](/#features)：自动提取字幕 + 大模型生成 Markdown 摘要、思维导图、AI 多轮问答
- [字幕提取与下载](/#features)：支持 SRT/VTT/TXT 多格式下载与展开收起
- [多平台支持](/#platforms)：YouTube、Bilibili、抖音、TikTok、Twitter/X、Instagram、Facebook、Vimeo、SoundCloud 等 1800+ 全球平台
- [响应式 UI](/#features)：手机 / 平板 / 桌面全适配，无需安装 App

## 使用步骤
1. 在首页输入框粘贴视频链接（支持多链接空格 / 逗号分隔）
2. 点击「解析视频」按钮，系统返回标题、缩略图、平台、清晰度选项
3. 选择目标清晰度，点击「立即下载」开始下载（直链或服务端代理）
4. 如需 AI 总结，点击「AI 总结」按钮，切换 Tab 查看摘要 / 字幕 / 思维导图 / AI 问答

## 常见问答
- Q: VidCatcher 支持哪些平台？
  A: 基于 yt-dlp 引擎，支持 YouTube、Bilibili、抖音、TikTok、Twitter/X、Instagram、Facebook、Vimeo、SoundCloud 等 1800+ 全球主流视频与音频平台。
- Q: VidCatcher 是免费的吗？
  A: 是的。免费版支持 720p 解析与下载；VIP 版支持 4K、批量下载、字幕下载、AI 视频总结等高级功能。
- Q: AI 视频总结怎么工作？
  A: 解析视频后点击「AI 总结」→ 自动提取平台自带字幕 → 调用 DeepSeek 大模型流式生成概述 / 思维导图 / 多轮 AI 问答。
- Q: 手机能用吗？
  A: 可以。响应式设计，手机浏览器直接打开即用，无需安装 App。
- Q: 清晰度由什么决定？
  A: 由原平台提供的最高清晰度决定；解析结果列出所有可选清晰度。

## 技术栈
- 前端：Vue 3 + Vite
- 后端：Python 3 + FastAPI
- 视频引擎：yt-dlp（开源）
- AI 模型：DeepSeek（通过 OpenAI 兼容协议）
- 部署：前后端分离，无数据库，临时文件定期清理

## 项目信息
- 类型：开源学习项目
- 引擎：yt-dlp
- 上线时间：2026 年
- GitHub：https://github.com/REPLACE_WITH_YOUR_REPO  <!-- TODO: 用户替换为真实 GitHub 仓库地址 -->
- 协议：仅供学习与个人合法使用，请尊重版权

## 适用人群
- 想从各平台下载保存视频的个人用户
- 需要批量采集素材的内容创作者
- 想快速了解长视频内容、提升学习效率的用户
- 需要在移动端下载视频的用户

## 不适用
- 任何侵犯版权 / 隐私 / 平台 ToS 的用途
- 商业化盗链 / 对抗平台风控

## 关联
- 软件应用类型：MultimediaApplication / VideoDownloader
- 界面语言：中文（zh-CN）
- 主要平台：Web（响应式）
```

### 3.3 关键设计

- 用 `# VidCatcher` 作为一级标题（Markdown H1）
- 用 `> 块引用` 给出 LLM 摘要（最容易被 LLM 提取的格式）
- 用 `## 二级标题` 分章节
- 用 `- [链接](url)` 给出可点击入口（带锚点，跳到 App.vue 的 section）
- FAQ 用 Q/A 两行结构
- 所有 URL 使用 `/#anchor` 形式指向单页 SPA 的 section
- GitHub URL 用占位 `REPLACE_WITH_YOUR_REPO`，注释提示用户替换

## 4. JSON-LD 增强

### 4.1 新增 schema

在 `frontend/index.html` 的 `<script type="application/ld+json">` 块中，**追加 4 个新 schema**（已有 3 个 + 新增 4 个 = 共 7 个）。

#### 4.1.1 Organization（品牌信息，最重要）

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "VidCatcher",
  "alternateName": "视频捕手",
  "url": "${SITE_ORIGIN}/",
  "logo": "${SITE_ORIGIN}/icon.svg",
  "description": "万能视频下载与 AI 总结工具项目团队",
  "sameAs": [
    "https://github.com/REPLACE_WITH_YOUR_REPO"
  ],
  "knowsAbout": [
    "视频下载",
    "yt-dlp",
    "AI 视频总结",
    "字幕提取",
    "视频内容理解",
    "Vue 3",
    "FastAPI"
  ]
}
```

#### 4.1.2 WebPage（页面元信息）

```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "${SITE_ORIGIN}/#webpage",
  "url": "${SITE_ORIGIN}/",
  "name": "VidCatcher · 万能视频下载与 AI 总结工具",
  "description": "万能视频下载工具，支持 1800+ 平台在线解析与免费下载，并提供 AI 视频总结、字幕提取、视频思维导图与 AI 问答。",
  "inLanguage": "zh-CN",
  "isPartOf": { "@id": "${SITE_ORIGIN}/#website" },
  "about": { "@id": "${SITE_ORIGIN}/#software" },
  "primaryImageOfPage": { "@type": "ImageObject", "url": "${SITE_ORIGIN}/og-image.svg" },
  "datePublished": "2026-01-01",
  "dateModified": "2026-09-20",
  "significantLink": [
    "${SITE_ORIGIN}/#features",
    "${SITE_ORIGIN}/#how-to",
    "${SITE_ORIGIN}/#faq",
    "${SITE_ORIGIN}/#about",
    "${SITE_ORIGIN}/#platforms",
    "${SITE_ORIGIN}/#plans"
  ]
}
```

#### 4.1.3 HowTo（使用步骤）

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "如何使用 VidCatcher 下载视频",
  "description": "3 步完成跨平台视频下载；4 步完成 AI 视频总结。",
  "totalTime": "PT2M",
  "step": [
    {
      "@type": "HowToStep",
      "position": 1,
      "name": "粘贴视频链接",
      "text": "在首页输入框粘贴视频链接，支持空格或逗号分隔多个链接。"
    },
    {
      "@type": "HowToStep",
      "position": 2,
      "name": "解析视频",
      "text": "点击「解析视频」按钮，系统返回标题、缩略图、平台来源、清晰度选项。"
    },
    {
      "@type": "HowToStep",
      "position": 3,
      "name": "选择清晰度并下载",
      "text": "从清晰度网格中选择目标档位（360p 至 4K），点击「立即下载」开始下载。"
    },
    {
      "@type": "HowToStep",
      "position": 4,
      "name": "（可选）AI 视频总结",
      "text": "点击「AI 总结」按钮，等待字幕提取与 AI 生成，可在四个 Tab 间切换查看摘要、字幕、思维导图、AI 问答。"
    }
  ]
}
```

#### 4.1.4 BreadcrumbList（导航结构）

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "首页",
      "item": "${SITE_ORIGIN}/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "功能特性",
      "item": "${SITE_ORIGIN}/#features"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "使用教程",
      "item": "${SITE_ORIGIN}/#how-to"
    },
    {
      "@type": "ListItem",
      "position": 4,
      "name": "常见问题",
      "item": "${SITE_ORIGIN}/#faq"
    },
    {
      "@type": "ListItem",
      "position": 5,
      "name": "关于项目",
      "item": "${SITE_ORIGIN}/#about"
    }
  ]
}
```

### 4.2 增强现有 schema

- **`SoftwareApplication`**：加 `author: {"@id": "${SITE_ORIGIN}/#organization"}` 形成 `@id` 关联；加 `featureList` 已含 8 条不变
- **`FAQPage`**：保持现有 5 个 Q&A
- **`WebSite`**：保持现有 + 加 `@id` 字段（供 WebPage 引用）

### 4.3 @id 引用策略

- WebSite: `${SITE_ORIGIN}/#website`
- WebPage: `${SITE_ORIGIN}/#webpage`
- SoftwareApplication: `${SITE_ORIGIN}/#software`
- Organization: `${SITE_ORIGIN}/#organization`
- FAQPage: `${SITE_ORIGIN}/#faq`
- HowTo: `${SITE_ORIGIN}/#howto`
- BreadcrumbList: `${SITE_ORIGIN}/#breadcrumb`

形成完整 entity graph：WebPage isPartOf WebSite, about SoftwareApplication, primaryImageOfPage og-image, significantLink 6 个 section 锚点；Organization 作为 author；FAQPage 与 HowTo 独立存在。

## 5. Dublin Core meta

在 `frontend/index.html` `<head>` 中加入 Dublin Core 元数据（学术界与部分 AI 引擎识别度高）。

| 标签 | 值 |
| --- | --- |
| `<meta name="DC.title">` | `VidCatcher · 万能视频下载与 AI 总结工具` |
| `<meta name="DC.creator">` | `VidCatcher Project` |
| `<meta name="DC.subject">` | `万能视频下载; AI 视频总结; 字幕提取; 思维导图; yt-dlp` |
| `<meta name="DC.description">` | （同 meta description） |
| `<meta name="DC.publisher">` | `VidCatcher` |
| `<meta name="DC.contributor">` | `yt-dlp; DeepSeek; Vue; FastAPI` |
| `<meta name="DC.date">` | `2026-09-20` |
| `<meta name="DC.type">` | `InteractiveResource` |
| `<meta name="DC.format">` | `text/html; charset=UTF-8` |
| `<meta name="DC.identifier">` | `${SITE_ORIGIN}/` |
| `<meta name="DC.language">` | `zh-CN` |
| `<meta name="DC.relation">` | `https://github.com/REPLACE_WITH_YOUR_REPO` |
| `<meta name="DC.rights">` | `学习项目，仅供个人合法使用` |

## 6. App.vue 三新区块（内容层）

### 6.1 现有结构（保留不动）

现有 sections（顺序）：
- `#top`（Hero）
- `结果卡片区`（条件渲染）
- `#features`（功能特性）
- `#plans`（套餐价格）
- `#platforms`（支持平台）

### 6.2 新增 sections（追加在 platforms 后、footer 前）

#### 6.2.1 `<section id="how-to">` 使用教程

```html
<section id="how-to" class="section alt">
  <h2>3 步开始使用</h2>
  <p class="section-sub">从粘贴链接到下载，再到 AI 总结</p>
  <ol class="how-to-steps">
    <li>
      <span class="step-num">01</span>
      <h3>粘贴视频链接</h3>
      <p>在首页输入框粘贴视频链接，支持空格或逗号分隔多个链接（YouTube、Bilibili、抖音、TikTok 等均可）。</p>
    </li>
    <li>
      <span class="step-num">02</span>
      <h3>解析视频</h3>
      <p>点击「解析视频」按钮，系统返回标题、缩略图、平台来源、清晰度选项（360p 至 4K）。</p>
    </li>
    <li>
      <span class="step-num">03</span>
      <h3>选择清晰度并下载</h3>
      <p>从清晰度网格中选择目标档位，点击「立即下载」开始下载。服务端代理模式可绕过防盗链平台限制。</p>
    </li>
    <li>
      <span class="step-num">04</span>
      <h3>（可选）AI 视频总结</h3>
      <p>点击「AI 总结」按钮，自动提取字幕后调用 AI 生成 Markdown 摘要、思维导图，可在四 Tab 间切换查看摘要 / 字幕 / 思维导图 / AI 问答。</p>
    </li>
  </ol>
</section>
```

样式：复用现有 `.section .section-sub`；新加 `.how-to-steps` 与 `.step-num` CSS（约 30 行）。

#### 6.2.2 `<section id="faq">` 常见问题

```html
<section id="faq" class="section">
  <h2>常见问题</h2>
  <p class="section-sub">关于 VidCatcher 的常见疑问</p>
  <details class="faq-item" open>
    <summary>VidCatcher 支持哪些视频平台？</summary>
    <p>VidCatcher 基于 yt-dlp 引擎，支持 YouTube、Bilibili、抖音、TikTok、Twitter/X、Instagram、Facebook、Vimeo、SoundCloud 等 1800+ 全球主流视频与音频平台。</p>
  </details>
  <details class="faq-item">
    <summary>VidCatcher 是免费的吗？</summary>
    <p>是的，VidCatcher 提供永久免费的解析与下载能力，免费版最高支持 720p 清晰度。VIP 版支持无限下载、4K、字幕下载与 AI 视频总结等高级功能。</p>
  </details>
  <details class="faq-item">
    <summary>VidCatcher 的 AI 视频总结功能是怎么工作的？</summary>
    <p>解析视频后点击「AI 总结」，系统自动提取平台自带字幕（人工字幕优先，自动字幕次之），再调用 DeepSeek 大模型生成视频概述、核心要点、一句话总结、可交互思维导图，并支持基于字幕内容的多轮 AI 问答。</p>
  </details>
  <details class="faq-item">
    <summary>手机端能用 VidCatcher 吗？</summary>
    <p>可以。VidCatcher 采用响应式设计，在手机浏览器直接打开即用，无需安装 App。</p>
  </details>
  <details class="faq-item">
    <summary>下载的视频清晰度由什么决定？</summary>
    <p>由原平台提供的最高清晰度决定。VidCatcher 在解析结果中列出所有可选清晰度（360p 至 4K），用户可手动选择。</p>
  </details>
  <details class="faq-item">
    <summary>VidCatcher 会保存我的下载历史或个人信息吗？</summary>
    <p>不会。VidCatcher 不使用数据库，不记录用户账户、不持久化下载历史。临时文件定期清理。</p>
  </details>
  <details class="faq-item">
    <summary>为什么我的视频下载失败了？</summary>
    <p>常见原因：①视频有地区限制；②视频为会员专属内容；③视频为直播流；④平台更新了反爬策略（yt-dlp 通常 1-2 周内跟进）。可尝试更换视频或等待 yt-dlp 升级。</p>
  </details>
</section>
```

样式：复用现有 `.section`；新加 `.faq-item` 与 `details/summary` CSS（约 30 行）。使用 `<details>` 原生折叠元素，无 JS。

#### 6.2.3 `<section id="about">` 关于项目

```html
<section id="about" class="section alt">
  <h2>关于 VidCatcher</h2>
  <p class="section-sub">一个开源的视频下载与 AI 内容理解学习项目</p>
  <div class="about-grid">
    <article class="about-card">
      <h3>项目背景</h3>
      <p>VidCatcher 是面向个人用户的跨平台视频下载与 AI 视频内容总结工具，旨在解决「多平台无法直接下载」「长视频内容理解成本高」两大痛点。</p>
    </article>
    <article class="about-card">
      <h3>技术栈</h3>
      <p>前端 Vue 3 + Vite；后端 Python 3 + FastAPI；视频引擎 yt-dlp（开源）；AI 模型 DeepSeek（OpenAI 兼容协议）。前后端分离，无数据库，临时文件定期清理。</p>
    </article>
    <article class="about-card">
      <h3>开源与协议</h3>
      <p>本项目为学习项目，仅供个人合法使用。请尊重版权，不要将服务公开部署为盗链站或用于对抗平台风控。视频解析能力完全来自开源 yt-dlp。</p>
    </article>
    <article class="about-card">
      <h3>反馈与建议</h3>
      <p>欢迎在 GitHub 仓库提 Issue 反馈问题与建议。VidCatcher 是学习项目，期待与社区一起迭代。</p>
    </article>
  </div>
</section>
```

样式：复用现有 `.section .section-sub`；新加 `.about-grid` 与 `.about-card` CSS（约 25 行）。

### 6.3 nav 链接扩展

现有 nav 链接：
```
- [功能特性](`#features`)
- [套餐价格](`#plans`)
- [支持平台](`#platforms`)
```

新增 3 个：
```
- [使用教程](`#how-to`)
- [常见问题](`#faq`)
- [关于项目](`#about`)
```

nav 链接总数：3 → 6。需确认在窄屏（移动端）是否仍能显示完整；如不能，下期做汉堡菜单。

### 6.4 增量 CSS

约 85 行新 CSS（how-to-steps / faq-item / about-grid / about-card），全部使用现有 CSS 变量（`--blue / --paper / --line / --ink / --muted`），保持视觉一致性。

### 6.5 风险评估

| 风险 | 应对 |
| --- | --- |
| nav 加 3 个链接在窄屏溢出 | 测试 360px 视口；溢出时允许横向滚动（不改布局） |
| `<details>` 折叠交互被部分 AI 引擎忽略 | 不影响 SEO / GEO，因 JSON-LD FAQPage 已完整列出所有 Q&A |
| 新增 CSS 影响现有布局 | 复用现有 CSS 变量与卡片样式；新增 class 名加 `how-to` / `faq` / `about` 前缀避免冲突 |
| 中文长标题在 H2 中溢出 | 现有 H2 已能容纳更长标题，不调整 |

## 7. sitemap.xml / robots.txt 调整

### 7.1 sitemap.xml：扩展 `<loc>`

把现有单 `<url>` 扩展为多 `<url>`（每 section 一个，标注 priority 与 changefreq）：

```xml
<urlset>
  <url>
    <loc>http://localhost:5173/</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#features</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#how-to</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#faq</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#about</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#platforms</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://localhost:5173/#plans</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
```

### 7.2 robots.txt：新增 llms.txt 引用与 LLM UA 分组

在现有 robots.txt 末尾追加：

```text
# LLM 友好摘要
Allow: /llms.txt

# 国内 AI 引擎常用 UA（基于公开 UA 模式）
User-agent: ChatGPT-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Applebot-Extended
Allow: /
```

> 注：豆包 / 文心 / 通义 / Kimi 等国内 AI 引擎目前**未公开** User-Agent（多数借用 Bingbot UA）。本研究不主动声明这些 UA（避免误判）。

## 8. 文件变更清单（最终）

### 8.1 新增

| 文件 | 行数估计 |
| --- | --- |
| `frontend/public/llms.txt` | ~60 行 Markdown 风格 |

### 8.2 修改

| 文件 | 变更 | 行数估计 |
| --- | --- | --- |
| `frontend/index.html` | 增 13 行 Dublin Core meta + 4 个新 JSON-LD script + 调整 @id 引用 + 增强 SoftwareApplication 加 author | +60 行 |
| `frontend/public/sitemap.xml` | 7 个 `<url>`（原 1 个） | +12 行 |
| `frontend/public/robots.txt` | 追加 LLM UA 与 llms.txt 引用 | +12 行 |
| `frontend/src/App.vue` | 追加 3 个 section + 3 个 nav 链接 | +120 行 HTML |
| `frontend/src/style.css` | 追加 how-to / faq / about 样式 | +85 行 |

### 8.3 不动

- `frontend/vite.config.js` / `package.json`
- `frontend/src/main.js` / `api/*` / `utils/*` / `components/VideoSummary.vue`
- `backend/app/*.py` / `backend/tests/*`

## 9. 验收口径

| # | 验收项 | 通过标准 |
|---|--------|----------|
| 1 | llms.txt 可访问 | `/llms.txt` 200，text/plain，含 `# VidCatcher` + `## 核心能力` + Q/A 块 |
| 2 | JSON-LD 7 个 schema | `index.html` 含 7 个 `application/ld+json`，对应 `@type` 全部出现 |
| 3 | @id 引用正确 | WebPage.isPartOf=WebSite, about=SoftwareApplication；Organization 提供 author |
| 4 | Dublin Core meta | index.html 含至少 10 个 DC.* meta |
| 5 | App.vue 三新区块 | `#how-to` / `#faq` / `#about` section 在 DOM 中，nav 含 6 个链接 |
| 6 | FAQ 双向印证 | App.vue FAQ 与 JSON-LD FAQPage Q&A 内容一致 |
| 7 | HowTo 双向印证 | App.vue HowTo 与 JSON-LD HowTo 步骤一致 |
| 8 | sitemap 多 url | 含 7 个 `<url>`，loc 包含所有 section 锚点 |
| 9 | robots.txt 扩 LLM | 含 ChatGPT-User / Claude-Web / PerplexityBot / Applebot-Extended |
| 10 | 业务零回归 | 解析 / 下载 / AI 总结三链路表现与改动前一致 |
| 11 | npm run build 成功 | exit 0，dist 含全部新文件 |
| 12 | Lighthouse SEO | ≥ 95（与 SEO 优化验收对齐） |

## 10. 风险与权衡

| 风险 | 应对 |
| --- | --- |
| 国内 AI 引擎未公开 UA，主动声明可能被忽略 | robots.txt 同时声明；llms.txt 主动提供 |
| App.vue 加 section 触发样式冲突 | 使用独立 class 前缀（how-to / faq / about）+ 复用 CSS 变量 |
| nav 链接加 3 个后窄屏溢出 | 桌面端 6 项横向显示；< 768px 不强制改造，留作下期汉堡菜单 |
| GitHub 占位 URL 长期不替换 | 在 README / 部署文档中标注「TODO」清单 |
| Dublin Core 部分 AI 引擎识别度低 | 不影响核心；与 JSON-LD + llms.txt 形成冗余 |

## 11. 后续（二期）

- AI 引擎主动提交（Perplexity / Bing IndexNow）
- 多语言 AI 摘要（英文 / 日文）
- 内容营销：长尾文章（如「怎么下载 B 站视频」「YouTube 视频怎么保存」）
- Vite prerender 真正静态化（让 AI 引擎抓取到完整正文 HTML）

---

## Spec 自检

- [x] 范围严格收敛：仅 index.html + public/ + App.vue + style.css
- [x] 不碰业务代码（解析 / 下载 / AI 总结 / 后端）
- [x] 与 SEO spec 资产对齐（不冲突，沿用同一 SITE_ORIGIN 占位）
- [x] JSON-LD 形成完整 entity graph（@id 互引）
- [x] 双向印证：JSON-LD FAQPage / HowTo 与 App.vue FAQ / HowTo 一致
- [x] 风险与回滚明确
- [x] 验收 12 项，可量化

---

## Next

**（写入后须暂停 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 方案无误 → 说「**写计划**」或「**开始实现**」
- 范围调整 → 拿全部 / 静态部分 / 范围调整
- 需要添加 / 移除内容 → 拿如「不要 about section」「FAQ 加问题 X」