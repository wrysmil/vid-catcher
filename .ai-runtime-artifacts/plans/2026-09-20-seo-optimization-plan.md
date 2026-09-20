---
route: planning
topic: VidCatcher SEO 搜索引擎优化
status: draft
approved: false
date: 2026-09-20
author: Leader
artifact: plan
source:
  - .ai-runtime-artifacts/specs/2026-09-20-seo-optimization-spec.md
related_artifacts:
  - .ai-runtime-artifacts/specs/2026-09-20-seo-optimization-spec.md
---

# VidCatcher SEO 优化 - 实施计划

## 0. 决策记录（用户最新指示）

> 用户原话：**"图标策略先用 SVG，如果需要生图的话，可以给我生图提示词，我生成之后把文件给你。生图提示词是二期的事情，目前先用 SVG"**

- **本期**：所有图标/OG 图全部 SVG 自生成（不引入 `sharp`、不引入二进制资源）
- **二期（不进本期 plan）**：如需更精美 OG 图，会给用户生成 AI 绘图提示词；用户生成后回传 PNG/SVG 文件覆盖 og-image.svg

## 1. 范围锁定（用户硬约束）

> 用户原话：**"一定不要影响任何现有的功能，只扩展我让你做的能力"**

**仅允许修改/新增的文件清单：**

| 文件 | 类型 |
|------|------|
| `frontend/index.html` | 改：注入 meta + JSON-LD + 站长占位 |
| `frontend/public/`（新建目录） | 新增 |
| `frontend/public/icon.svg` | 新增 |
| `frontend/public/apple-touch-icon.svg` | 新增 |
| `frontend/public/og-image.svg` | 新增 |
| `frontend/public/site.webmanifest` | 新增 |
| `frontend/public/robots.txt` | 新增 |
| `frontend/public/sitemap.xml` | 新增 |

**禁止触碰的文件清单（回归保护）：**
- `frontend/src/App.vue`
- `frontend/src/components/VideoSummary.vue`
- `frontend/src/style.css`
- `frontend/src/main.js`
- `frontend/src/api/summarize.js`
- `frontend/src/utils/*`
- `frontend/package.json`
- `frontend/vite.config.js`
- `backend/app/*.py`
- `backend/requirements.txt`

## 2. WU 拆解与执行图

### WU-1：index.html meta 注入

**类型**：coder
**目标文件**：`frontend/index.html`
**依赖**：无
**风险**：中（涉及 SEO 核心，且要保持 `<head>` 结构合法）

**具体变更**：
1. `<title>` → `VidCatcher · 万能视频下载工具 | 在线解析YouTube/B站/抖音视频 · AI视频总结`
2. 新增 meta 块（在 `<meta name="viewport">` 之后）：
   - `description`（~110 中文字符）
   - `keywords`（主词 + 长尾）
   - `robots`（`index, follow, max-image-preview:large, max-snippet:-1`）
   - `theme-color`（`#2f6fed`）
   - `format-detection`（`telephone=no`）
   - 4 个站长验证 meta 占位（baidu / google / msvalidate / 360）
3. 新增 link 块：
   - `canonical`（`http://localhost:5173/`，部署时替换）
   - `icon.svg`
   - `apple-touch-icon`
   - `manifest`
4. 新增 OG / Twitter 卡片（11 个 og:* + 4 个 twitter:*）
5. 新增 3 个 JSON-LD script：
   - WebSite（含 SearchAction）
   - SoftwareApplication（含 featureList、offers）
   - FAQPage（5 个 Q&A）
6. 保持现有 preconnect / Google Fonts 不变
7. 保留 `<div id="app"></div>` 与 `/src/main.js` 入口

**验收**：
- HTML 合法（标签闭合、嵌套正确）
- 30+ 新标签全部就位
- `view-source:` 能看到所有 meta 与 JSON-LD

---

### WU-2：public/ 静态资源

**类型**：implementer
**目标目录**：`frontend/public/`
**依赖**：无（与 WU-1 并行）
**风险**：低（纯新增静态文件）

**具体产出**：

| 文件 | 用途 | 设计要点 |
|------|------|----------|
| `icon.svg` | 现代浏览器 favicon | 32x32 viewBox；蓝色圆角矩形 `#2f6fed` + 白色播放三角；复用 `style.css --blue` 视觉 |
| `apple-touch-icon.svg` | iOS 主屏图标 | 180x180 viewBox；与 icon.svg 同视觉；矢量自适应 |
| `og-image.svg` | OG / Twitter 卡片图 | 1200x630；左侧 logo + 文字、右侧 4 个特性标签；底色 `#f7f9fc`；纯 SVG 内置 `text` + `sans-serif`（不依赖外部字体） |
| `site.webmanifest` | PWA 清单 | name/short_name/display/theme_color/icons |

**验收**：
- 文件 200，浏览器可访问
- SVG 渲染正确（浏览器直接打开看视觉效果）

---

### WU-3：robots.txt + sitemap.xml

**类型**：implementer
**目标文件**：`frontend/public/robots.txt`、`frontend/public/sitemap.xml`
**依赖**：无（与 WU-1 / WU-2 并行）
**风险**：低

**具体内容**：
- `robots.txt`：
  - `User-agent: *` 允许 `/`，禁止 `/api/` 与 `/tasks/`
  - 国内爬虫显式分组（百度 / 360 / 搜狗 / 神马）
  - 国际爬虫（Bingbot / Googlebot）
  - `Sitemap:` 引用 `http://localhost:5173/sitemap.xml`
- `sitemap.xml`：
  - 合法 XML 头
  - 单 `<url>` 节点：loc=`http://localhost:5173/`, lastmod=`2026-09-20`, changefreq=`weekly`, priority=`1.0`

**验收**：
- 200 响应
- XML 合法（`xmllint` 或浏览器解析无误）
- robots.txt 符合 Robots Exclusion Protocol

---

### WU-4：构建验证 + 回归 smoke

**类型**：coder
**依赖**：WU-1 / WU-2 / WU-3
**风险**：中（涉及 npm build 与 dist 检查）

**具体步骤**：
1. `cd frontend && npm run build` —— 必须成功，无报错
2. 检查 `dist/index.html` —— 确认所有新 meta / JSON-LD 注入
3. 检查 `dist/icon.svg` / `dist/og-image.svg` / `dist/robots.txt` / `dist/sitemap.xml` / `dist/site.webmanifest` —— 全部 200
4. 业务零回归 smoke（按需）：
   - 启动 `npm run dev` 后浏览器访问 `http://127.0.0.1:5173/`
   - `view-source:` 检查 title / description
   - 访问 `/robots.txt` 与 `/sitemap.xml` 看响应
   - 视觉确认 favicon 与 OG 图渲染正确

**验收**：
- `npm run build` exit 0
- `dist/` 含全部新增文件
- `dist/index.html` 含 30+ meta + 3 JSON-LD
- 浏览器渲染 favicon / OG 图正常

---

## 3. 执行顺序

```
        ┌─ WU-1（index.html meta 注入）   ─┐
启动 ───┼─ WU-2（public/ 静态资源）        ─┼─→ WU-4（构建验证 + smoke）
        └─ WU-3（robots + sitemap）         ─┘
```

**说明**：因 WU 1-3 互不依赖，理论上可并行；但本期由 Leader 直接执行（文件数少、确定性高、避免 subagent 边界协调成本）。实际按 WU-1 → WU-2 → WU-3 顺序串行，最后 WU-4 验证。

## 4. 风险与回滚

| 风险 | 触发条件 | 回滚方式 |
|------|----------|----------|
| HTML 标签闭合错误 | WU-1 写入后 `npm run build` 报错 | 恢复 `frontend/index.html` 到原 19 行版本（git checkout） |
| 资源 404 | WU-2 文件路径错误 | 删除 `frontend/public/` 目录（git clean） |
| OG 图渲染空白 | og-image.svg 字体回退失败 | 改用纯几何元素，无 text 节点 |
| 用户域名替换遗漏 | 部署时未替换 `http://localhost:5173` | 在 plan 之外补 README 部署说明 |

## 5. 验收口径（与 spec §12 对齐）

| # | 项 | 通过 |
|---|----|------|
| 1 | `frontend/index.html` 含 description / keywords / canonical / og:* / twitter:* / theme-color | ✅ |
| 2 | `frontend/index.html` 含 4 个站长验证 meta 占位（百度 / Google / Bing / 360） | ✅ |
| 3 | `frontend/index.html` 含 3 个 JSON-LD script（WebSite + SoftwareApplication + FAQPage） | ✅ |
| 4 | `frontend/public/robots.txt` 返回 200，含分组 UA + Sitemap 引用 | ✅ |
| 5 | `frontend/public/sitemap.xml` 返回 200，合法 XML | ✅ |
| 6 | `frontend/public/icon.svg` 200，浏览器标签显示 logo | ✅ |
| 7 | `frontend/public/og-image.svg` 200，1200x630 矢量 | ✅ |
| 8 | `frontend/public/site.webmanifest` 200，合法 JSON | ✅ |
| 9 | 业务零回归：解析 / 下载 / AI 总结链路表现一致 | ✅ |
| 10 | `npm run build` exit 0；`dist/index.html` 含全部新标签 | ✅ |

## 6. 后续（二期）

- AI 绘图提示词（OG 图美化版）
- Vite prerender（vite-ssg / prerender-spa-plugin）
- 百度站长主动推送 API（需后端代理 + token）
- Bing IndexNow 一键提交
- 多语言 hreflang + 文案翻译
- 富媒体 VideoObject（动态内容页）

---

## Plan 自检

- [x] 范围严格收敛到 spec 限定文件清单
- [x] WU 之间依赖清晰
- [x] 风险与回滚方案明确
- [x] 验收口径可量化（10 项）
- [x] 不引入新依赖

---

## Next

用户已明确指示「写计划然后实现」，本 plan 写完后 Leader 直接进入 WU-1 实现阶段。