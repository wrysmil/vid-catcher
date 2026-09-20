---
route: brainstorming
topic: VidCatcher SEO 搜索引擎优化
status: draft
approved: false
date: 2026-09-20
author: Leader
artifact: spec
skills:
  - seo-audit
  - source-driven-development
source:
  - docs/需求文档.md
  - .ai-runtime-artifacts/specs/2026-09-19-video-summarize-spec.md
  - frontend/index.html
  - frontend/src/App.vue
  - frontend/src/style.css
decisions:
  - 目标引擎: 国内优先（百度、搜狗、360、神马），兼顾 Bing/Google 国际抓取
  - 域名: 用占位常量 VID_CATCHER_SITE_ORIGIN（默认 http://localhost:5173），构建时由 CI 注入
  - 语言: 仅中文 zh-CN，不做 hreflang
  - 架构边界: 仅扩展现有 index.html、frontend/public/、vite.config.js 与新增静态文件；不改动业务代码（App.vue / VideoSummary.vue / 后端 / 解析链路）
  - 范围限定: meta 标签、结构化数据 JSON-LD、robots.txt、sitemap.xml、favicon 套件、站长验证 meta 占位；不引入 prerender/SSG
  - OG 图: 自生成 SVG og-image.svg（1200x630），不含外部图片资源
  - favicon: 自生成 SVG 套件（icon.svg、apple-touch-icon），避免引入二进制资源
---

# VidCatcher SEO 搜索引擎优化 Spec

## 1. 背景与目标

### 1.1 现状（已审计）

| 问题 | 严重度 | 证据 |
| --- | --- | --- |
| `<title>` 不含核心搜索词 | 高 | `frontend/index.html:6` 当前 "VidCatcher — 视频捕手 / 一键保存" 缺少"视频下载""在线下载""万能"等高搜索量词 |
| 无 `<meta name="description">` | 高 | `frontend/index.html` 全文件 19 行，完全缺失 |
| 无 `<meta name="keywords">` | 高 | 缺失 |
| 无 OG / Twitter 卡片 | 高 | 缺失，社交分享与百度展示无预览 |
| 无结构化数据 JSON-LD | 高 | 缺失；SoftwareApplication / FAQ / BreadcrumbList 均无 |
| 无 favicon | 中 | `frontend/public/` 目录不存在；浏览器标签页空白 |
| 无 `robots.txt` | 高 | 缺失；搜索引擎抓取无指引，`/api/*` 路径可能被错误索引 |
| 无 `sitemap.xml` | 高 | 缺失 |
| 无 `canonical` | 中 | 缺失，多域名/路径变体可能造成内容重复 |
| 无 `apple-touch-icon` / `theme-color` | 中 | PWA 与移动端体验缺失 |
| 无百度/Google 站长验证 meta | 中 | 用户后续手动填，先留占位 |
| H1/H2 在 SPA 渲染后才出现 | 中 | Vue 3 CSR；首屏 HTML 只含 `<div id="app">`，搜索引擎抓取需要 meta 与 JSON-LD 兜底 |

### 1.2 目标

- **T1（必达）**：让百度、搜狗、360、神马、Bing、Google 的爬虫在第一次抓取时即获得完整语义信号
- **T2（必达）**：被用户用「视频下载工具」「万能视频下载」「B站视频下载」「AI 视频总结」「视频字幕提取」等关键词搜索时，能进入搜索结果前列
- **T3（扩展）**：为后续 prerender / SSG / 多语言扩展预留结构

### 1.3 非目标

- 不改业务代码（App.vue / 后端 / 解析 / 下载 / AI 总结）
- 不引入后端渲染（Prerender / SSR / SSG）—— 留作后续单独 spec
- 不做多语言 / 国际化 hreflang
- 不接百度主动推送 API（需要 token，且需要后端代理；留 spec 后续扩展点）
- 不引入图标字体、二进制图片资源（用 SVG 自生成）
- 不在本次 spec 内做 SEO 内容营销（发外链、买量、刷点击）—— 留作后续运营任务

## 2. 关键词矩阵

### 2.1 主关键词（首页 title / description 必含）

| 关键词 | 搜索意图 | 优先级 |
| --- | --- | --- |
| 万能视频下载 | 工具型 | P0 |
| 视频下载工具 | 工具型 | P0 |
| 在线视频下载 | 工具型 | P0 |
| 免费视频下载 | 工具型 | P0 |
| 跨平台视频下载 | 工具型 | P1 |
| AI 视频总结 | 信息型 | P1 |
| 视频内容总结 | 信息型 | P2 |

### 2.2 长尾关键词（description / JSON-LD keywords / 内容中嵌入）

- 平台型：B站视频下载、抖音视频下载、YouTube视频下载、TikTok视频下载、Twitter视频下载
- 功能型：视频字幕提取、视频转文字、AI 视频问答、视频思维导图、视频摘要生成
- 场景型：怎么下载网页视频、网页视频怎么保存到本地、手机下载视频

## 3. 方案对比与推荐

| 方案 | 优点 | 缺点 | 推荐 |
| --- | --- | --- | --- |
| **A. 静态 meta + JSON-LD + 自生成 SVG 资源（推荐）** | 改动小（仅 index.html / public / vite.config），不碰业务；上线即生效 | SPA 内容仍是 JS 渲染，但首页 meta 与 JSON-LD 足以兜底首屏 SEO | **是** |
| B. 引入 Vite SSG（vite-ssg / prerender-spa-plugin） | 真正静态化，所有搜索引擎都友好 | 改动巨大（router、main.js、异步数据加载），超出本任务"不碰业务代码"约束 | 否 |
| C. 后端注入 meta | 服务端可控 | 与现有 FastAPI 静态托管前端冲突；增加模板渲染复杂度 | 否 |

**推荐方案 A。** 与用户"不改动现有功能、只扩展"原则一致；国内 SEO 优化中静态 meta + JSON-LD 已能解决 80% 抓取问题。

## 4. 架构与文件变更

### 4.1 文件新增（frontend/public/）

```
frontend/public/
├── favicon.ico                  # 多尺寸 ICO（含 16/32/48），用脚本一次性生成
├── icon.svg                     # 现代浏览器 SVG favicon（32x32 viewBox）
├── apple-touch-icon.png         # 180x180 PNG（iOS 主屏图标）
├── og-image.svg                 # OG / Twitter 卡片图（1200x630，矢量无依赖）
├── robots.txt                   # 抓取规则
├── sitemap.xml                  # 站点地图（单文件）
└── site.webmanifest             # PWA 最小清单（name / theme_color / icons）
```

### 4.2 文件修改

| 文件 | 变更 | 风险 |
| --- | --- | --- |
| `frontend/index.html` | 在 `<head>` 注入：description / keywords / robots / canonical / og:* / twitter:* / theme-color / format-detection / 站长验证占位 / JSON-LD（3 个 script：WebSite + SoftwareApplication + FAQPage） | 低；纯 HTML 增量 |
| `frontend/vite.config.js` | 读取 `VID_CATCHER_SITE_ORIGIN` 环境变量注入到 `index.html` 模板（可选；本期可降级为硬编码 http://localhost:5173） | 中；需先 Read 现有 vite.config.js |

### 4.3 不动的文件

- `frontend/src/App.vue` / `VideoSummary.vue` / `style.css` / `main.js`
- `frontend/src/api/summarize.js`
- 所有后端文件（`backend/app/*.py`、`backend/tests/*`）

## 5. Meta 标签设计

### 5.1 `<title>` 模板

```
VidCatcher · 万能视频下载工具 | 在线解析YouTube/B站/抖音视频 · AI视频总结
```

- 长度：约 50 字符（百度/Google 截断阈值内）
- 主关键词前置："万能视频下载工具"
- 品牌后置："VidCatcher"
- 长尾追加："在线解析YouTube/B站/抖音视频 · AI视频总结"

### 5.2 `<meta name="description">`

```
万能视频下载工具，支持 YouTube、Bilibili、抖音、TikTok、Twitter 等 1800+ 平台在线解析与免费下载。VidCatcher 还提供 AI 视频总结、字幕提取、视频思维导图与 AI 问答，免费好用，手机电脑都能用。
```

- 长度：约 110 中文字符（按 CJK 1 字 ≈ 1.5 拉丁字符换算约 165 字符）
- 含主关键词 + 差异化卖点（AI 总结）

### 5.3 `<meta name="keywords">`

```
万能视频下载, 视频下载工具, 在线视频下载, 免费视频下载,
YouTube视频下载, B站视频下载, 抖音视频下载, TikTok视频下载,
AI视频总结, 视频字幕提取, 视频内容总结, 视频思维导图
```

### 5.4 OG / Twitter 卡片

| 标签 | 值 |
| --- | --- |
| `og:title` | 同 `<title>` |
| `og:description` | 同 `<meta description>` |
| `og:type` | `website` |
| `og:url` | `${SITE_ORIGIN}/` |
| `og:image` | `${SITE_ORIGIN}/og-image.svg` |
| `og:image:width` | `1200` |
| `og:image:height` | `630` |
| `og:image:alt` | `VidCatcher 万能视频下载与 AI 总结工具` |
| `og:site_name` | `VidCatcher` |
| `og:locale` | `zh_CN` |
| `twitter:card` | `summary_large_image` |
| `twitter:title` | 同 `og:title` |
| `twitter:description` | 同 `og:description` |
| `twitter:image` | 同 `og:image` |

### 5.5 canonical / robots / 其他

| 标签 | 值 |
| --- | --- |
| `<link rel="canonical">` | `${SITE_ORIGIN}/` |
| `<meta name="robots">` | `index, follow, max-image-preview:large, max-snippet:-1` |
| `<meta name="theme-color">` | `#2f6fed`（与现有 CSS 变量 `--blue` 对齐） |
| `<meta name="format-detection">` | `telephone=no` |
| `<meta name="baidu-site-verification">` | `<!-- TODO: 用户填入 token -->` 占位 |
| `<meta name="google-site-verification">` | `<!-- TODO: 用户填入 token -->` 占位 |
| `<meta name="msvalidate.01">` | `<!-- TODO: 用户填入 token（Bing）-->` 占位 |
| `<meta name="360-site-verification">` | `<!-- TODO: 用户填入 token -->` 占位 |

### 5.6 域名占位常量

- 源码常量：`VID_CATCHER_SITE_ORIGIN`
- `frontend/index.html` 中通过 Vite `define` 注入：`import.meta.env.VITE_SITE_ORIGIN || "http://localhost:5173"`
- `.env.example` 中声明：`VITE_SITE_ORIGIN=https://你的域名`
- 不在本次实现 CI 注入；本地调试用默认值

## 6. 结构化数据（JSON-LD）

在 `frontend/index.html` 中注入 **三个** JSON-LD script（用 `<script type="application/ld+json">`），与 seo-audit 框架 Schema Markup Detection 章节建议一致。

### 6.1 WebSite（站点级）

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "VidCatcher",
  "alternateName": "视频捕手",
  "url": "${SITE_ORIGIN}/",
  "inLanguage": "zh-CN",
  "description": "万能视频下载工具，支持 1800+ 平台在线解析与免费下载，并提供 AI 视频总结。",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "${SITE_ORIGIN}/?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

> 注：`SearchAction` 中的 `?q=` 当前 Vite SPA 实际未消费，仅作搜索建议声明；搜索引擎对此不强制要求实际可用。

### 6.2 SoftwareApplication（应用级，最重要）

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "VidCatcher",
  "alternateName": "万能视频下载总结器",
  "operatingSystem": "WEB",
  "applicationCategory": "MultimediaApplication",
  "applicationSubCategory": "VideoDownloader",
  "description": "在线万能视频下载与 AI 总结工具",
  "url": "${SITE_ORIGIN}/",
  "image": "${SITE_ORIGIN}/og-image.svg",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "CNY",
    "category": "free"
  },
  "featureList": [
    "支持 YouTube / Bilibili / 抖音 / TikTok / Twitter 等 1800+ 平台",
    "一键解析视频链接，多种清晰度可选（360p 至 4K）",
    "服务端代理下载，兼容防盗链平台",
    "AI 视频内容总结（Markdown 流式输出）",
    "视频字幕提取与时间戳展示",
    "视频内容思维导图可视化",
    "基于字幕上下文的 AI 多轮问答",
    "响应式布局，手机 / 平板 / 桌面全适配"
  ]
}
```

### 6.3 FAQPage（FAQ 抓取位，必含用户高频疑问）

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "VidCatcher 支持哪些视频平台？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "VidCatcher 基于 yt-dlp 引擎，支持 YouTube、Bilibili、抖音、TikTok、Twitter/X、Instagram、Facebook、Vimeo、SoundCloud 等 1800+ 全球主流视频与音频平台。"
      }
    },
    {
      "@type": "Question",
      "name": "VidCatcher 是免费的吗？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "是的，VidCatcher 提供永久免费的解析与下载能力，最高支持 720p 清晰度。VIP 版支持无限下载、4K、字幕下载与 AI 视频总结等高级功能。"
      }
    },
    {
      "@type": "Question",
      "name": "VidCatcher 的 AI 视频总结功能是怎么工作的？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "解析视频后点击「AI 总结」，系统自动提取平台自带字幕，调用大模型生成视频概述、核心要点、一句话总结、可交互思维导图，并支持基于字幕内容的多轮 AI 问答。"
      }
    },
    {
      "@type": "Question",
      "name": "手机端能用 VidCatcher 吗？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "可以。VidCatcher 采用响应式设计，在手机浏览器直接打开即用，无需安装 App。"
      }
    },
    {
      "@type": "Question",
      "name": "下载的视频清晰度由什么决定？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "由原平台提供的最高清晰度决定。VidCatcher 在解析结果中列出所有可选清晰度（360p 至 4K），用户可手动选择。"
      }
    }
  ]
}
```

## 7. robots.txt 设计

```text
# /robots.txt — VidCatcher
User-agent: *
Allow: /
Disallow: /api/
Disallow: /tasks/

# 国内主流爬虫显式放行（百度/搜狗/360/神马/Bingbot/Googlebot）
User-agent: Baiduspider
Allow: /

User-agent: 360Spider
Allow: /

User-agent: Sogou Spider
Allow: /

User-agent: YisouSpider
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Googlebot
Allow: /

# 站点地图
Sitemap: ${SITE_ORIGIN}/sitemap.xml
```

- 拦截 `/api/*` 与 `/tasks/*`（前端内部调用，不应被索引）
- `${SITE_ORIGIN}` 占位；构建期由 CI 注入真实域名

## 8. sitemap.xml 设计

### 8.1 单文件结构（一期）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${SITE_ORIGIN}/</loc>
    <lastmod>2026-09-20</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

### 8.2 后续扩展（留接口，不实现）

- 二期可拆 `sitemap-index.xml` + `sitemap-static.xml` + `sitemap-news.xml`
- 若后续生成动态视频页面，引入 `sitemap-videos.xml`（Google Video Sitemap 扩展）

## 9. PWA / favicon 套件

### 9.1 icon.svg（32x32）

- viewBox `0 0 32 32`
- 复用现有 logo 视觉（蓝色圆角矩形 + 白色播放三角）
- 颜色：`#2f6fed`（与 CSS `--blue` 对齐）
- 兼容 SVG favicon（Chrome 80+、Firefox 41+、Safari 9+）

### 9.2 apple-touch-icon.png（180x180）

- 同一图标渲染为 PNG
- **生成策略**：用一个 Node 脚本（构建期一次性运行）`scripts/build-favicon.mjs`，调用 `sharp` 把 `icon.svg` 转成 PNG 套件
- 但 **本任务不引入新依赖**：改用更轻量做法 —— 仅生成 SVG，让现代浏览器直接用 SVG；iOS 兼容性作为已知限制记录
- **最终交付**：`apple-touch-icon.svg`（多数现代 iOS 已支持），并在 `index.html` 用 `<link rel="apple-touch-icon" href="/apple-touch-icon.svg">`
- 如用户强烈要求 PNG 180x180，单独确认后引入 `sharp`

### 9.3 site.webmanifest

```json
{
  "name": "VidCatcher",
  "short_name": "VidCatcher",
  "description": "万能视频下载与 AI 总结工具",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f7f9fc",
  "theme_color": "#2f6fed",
  "lang": "zh-CN",
  "icons": [
    { "src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any" },
    { "src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "maskable" }
  ]
}
```

### 9.4 og-image.svg（1200x630）

- 纯 SVG 矢量图，含：
  - 左侧：放大版 VidCatcher logo + 文字 "VidCatcher 视频捕手"
  - 右侧：4 个特性标签（1800+ 平台 / AI 视频总结 / 多清晰度 / 免费）
  - 底色：`#f7f9fc`（与页面背景一致），点缀 `#2f6fed`
- 不引用任何外部字体（避免在 OG 抓取器中字体加载失败导致渲染空白）；用 SVG 内置 `text` 节点 + `font-family="sans-serif"`

## 10. Vite 配置

### 10.1 当前 vite.config.js（先读取）

在 plan 阶段先 `Read frontend/vite.config.js`，确认是否已配置 `define` / 环境变量注入。

### 10.2 拟定变更（如需要）

- 检查 `define`：当前若为空，本次新增 `define: { 'import.meta.env.VITE_SITE_ORIGIN': JSON.stringify(envValue) }`
- 若已有 `define`，**不覆盖**，仅追加
- 若 vite.config.js 根本不存在（项目无配置文件），跳过；改在 `index.html` 中直接硬编码 `http://localhost:5173` 并通过 `<script>` 内联 `window.__SITE_ORIGIN__` 方案

**降级方案**：本期 `index.html` 直接硬编码 `http://localhost:5173`；部署时手动替换。最小化对构建系统的影响。

## 11. 风险与权衡

| 风险 | 应对 |
| --- | --- |
| SPA CSR 导致搜索引擎对实际内容抓取不完整 | meta + JSON-LD 已能解决首屏 80% 信号；后续 prerender 留作独立 spec |
| OG 图用 SVG，部分爬虫不渲染（如部分微信旧版） | og:image 宽度至少 1200，矢量无字体依赖即可最大兼容 |
| iOS apple-touch-icon 不接受 SVG | 仅记录限制；不影响 SEO 核心指标（SEO 不依赖 apple-touch-icon） |
| `${SITE_ORIGIN}` 占位需手动替换 | 部署 README 注明；二期接入 CI |
| 站长验证 token 留空时 meta 是死代码 | 占位注释明显，用户填入即生效 |
| 百度对 JSON-LD 抓取有限 | 主要靠 meta description + title；JSON-LD 在百度也认，但优先级低于 meta |

## 12. 验收口径

| # | 验收项 | 通过标准 |
|---|--------|----------|
| 1 | meta 标签完整 | `index.html` 含 description / keywords / robots / canonical / og:* / twitter:* / theme-color |
| 2 | 站长验证占位 | index.html 含百度 / Google / Bing / 360 四个 verification meta 占位 |
| 3 | JSON-LD 注入 | index.html 含 3 个 ld+json script，可通过 `curl + grep` 验证；用 Google Rich Results Test 渲染 SoftwareApplication 正确 |
| 4 | robots.txt | `/robots.txt` 返回 200，含 User-agent 分组与 Sitemap 引用 |
| 5 | sitemap.xml | `/sitemap.xml` 返回 200，格式合法，可通过 Bing Webmaster / sitemap validators 校验 |
| 6 | favicon | `/icon.svg` 200，浏览器标签页显示 logo |
| 7 | OG 卡片 | `/og-image.svg` 200，1200x630 矢量；用 Twitter Card Validator / Facebook Sharing Debugger 渲染正确 |
| 8 | webmanifest | `/site.webmanifest` 200，合法 JSON |
| 9 | 业务零回归 | 解析 / 下载 / AI 总结三链路前端表现与改动前一致（手动 / Playwright smoke） |
| 10 | 构建产物 | `npm run build` 成功；`dist/index.html` 含全部新标签 |
| 11 | Lighthouse SEO | 本地起服后 Lighthouse SEO 评分 ≥ 95 |

## 13. 后续扩展（不进本期 plan）

- Vite prerender 静态化（vite-ssg / prerender-spa-plugin）
- 百度站长主动推送 API（需后端代理 + token）
- Bing IndexNow 一键提交
- 多语言版本（hreflang + 文案翻译）
- 富媒体搜索结果（视频 VideoObject schema，需动态内容页）
- 内容营销：发布"如何下载XX视频"长尾文章页（programmatic-seo）

---

## Spec 自检

- [x] 范围边界清晰：仅扩展 meta / public / vite.config；不碰业务代码
- [x] 与项目约定一致：使用 SVG 自生成图标、不引入新依赖；占位常量便于 CI 注入
- [x] 与 SEO 框架对齐：Crawlability → On-Page → Content → Authority 优先级正确
- [x] 关键词矩阵含主词 + 长尾，覆盖功能/平台/场景三个维度
- [x] 风险与权衡已识别
- [x] 验收口径可执行（11 项）
- [x] 与既有 specs 不冲突（不引用 / 不修改既有接口）

---

## Next

**（写入后须暂停 — 见 `harness-kit/core/routing.md` § 阶段门禁）**

- 方案无误 → 说「**写计划**」或「**开始实现**」
- 需要调整方案 → 直接指出修改意见
- 范围过宽 / 不想要某些项 → 勾掉对应章节（例如：「不要 PWA manifest」「不要站长占位」）