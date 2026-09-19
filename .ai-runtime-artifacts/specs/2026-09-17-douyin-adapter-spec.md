---
route: brainstorming
topic: 抖音视频下载适配
status: approved
approved: true
approved_at: 2026-09-17
approval_note: 用户原话「a」（选项 A：批准 spec + 进入 writing-plans + 开始实现三合一授权）
date: 2026-09-17
author: Leader
skills_evidence:
  - brainstorming@~/.claude/skills/brainstorming loaded
  - source-driven-development: skipped (no framework docs to cite; project rules + relevant source already read)
  - api-and-interface-design: skipped (single new module; no multi-WU contracts needed)
related_artifacts:
  - .ai-runtime-artifacts/plans/2026-09-17-douyin-adapter-plan.md
  - .ai-runtime-artifacts/verifications/2026-09-17-douyin-adapter-verification-lite.md
revisions:
  - 2026-09-17: 用户实测发现 lieshouyin.com 在本机 DNS 层不可达（关闭代理后 'Could not resolve host'），整体上游不可用。用户决策调整：回退到 yt-dlp 自带 douyin extractor；douyin_service.py 模块保留但 main.py 不再调用。commit 286661a。
decisions:
  - 集成方式: 全部走 yt-dlp（抖音 URL 也走 yt-dlp 自带 douyin extractor）；douyin_service.py 模块保留不调用，未来恢复时只需在 main.py 重新挂上 is_douyin_url 分流即可
  - 降级策略: 不需要——抖音直接走 yt-dlp
  - 测试覆盖: 单元逻辑 + live 烟雾；新增 test_api_parse_douyin_url_falls_back_to_ytdlp 验证回退
  - 前端可见性: extractor 字段由 yt-dlp 抖音 extractor 决定
---

# 抖音视频下载适配 Spec

## 1. 背景与目标

现有后端用 yt-dlp 薄封装，能解 YouTube / B 站 / Twitter 等，但抖音的反爬策略比一般视频平台更严：

1. 强制登录态：接口需有效 Cookie，未登录返回的链接无法正常下载。
2. 签名校验：接口请求需携带动态签名，URL 直拼无效。
3. 短链跳转：用户分享的是 `v.douyin.com/xxx`，要先解析出真实 video_id。

不破解登录 / 签名（项目硬约束见 `AGENTS.md` 禁区）。方案是找到第三方开源解析服务（`lieshouyin.com`）作为中转；它走抖音公开信息接口反向分析，已实现无 Cookie 解析。我们把它集成进来，对抖音链接走专用下载模块，其他平台继续走 yt-dlp。

## 2. 范围

**In scope**

- 新增 `backend/app/douyin_service.py`：短链解析 → 调上游公开 API → 无水印播放地址构造 → 流式下载。
- `backend/app/main.py`：`/api/parse` 与 `/api/download` 入口加 URL 识别，分流到 `douyin_service` 或 `ytdlp_service`。
- `backend/app/urls.py`：识别「抖音域」用于分流（不增加白名单，原有 `validate_http_url` 已放行）。
- `backend/tests/test_douyin.py`：纯函数单测 + 标记为 live 的烟雾测试。
- 错误处理：上游失败 → 502 + 中文提示，不静默 fallback。

**Out of scope（一期不做）**

- 批量抖音链接、列表解析
- 抖音直播流
- 用户登录态 / Cookie 注入
- 第三方 API 的可配置化（默认就一个 base_url，写死在常量里）
- 前端 UI 改动

## 3. 架构

```
HTTP POST /api/parse {url}
        │
        ▼
   main.py parse()
        │
        ├─── is_douyin_url(url)? ── yes ──► douyin_service.parse_video(url)
        │                                       │
        │                                       ├─ ① 解析短链 → 拿 video_id
        │                                       ├─ ② GET 公开 API → 拿 JSON
        │                                       ├─ ③ playwm → play（无水印）
        │                                       └─ 返回 choices=[无水印视频]
        │
        └─── no ──► ytdlp_service.parse_video(url)  (原有逻辑不动)


HTTP POST /api/download {url, format_id}
        │
        ▼
   main.py _run_download()
        │
        ├─── is_douyin_url(url)? ── yes ──► douyin_service.download_video(url, fmt, dest_dir, hook)
        │                                       │
        │                                       └─ stream-download 到 dest_dir/{task_id}.mp4
        │
        └─── no ──► ytdlp_service.download_video(url, fmt, dest_dir, hook)  (原有逻辑不动)
```

`ytdlp_service.py` / `tasks.py` / `formats.py` / 进度回调契约**完全不动**。

## 4. 模块设计

### 4.1 `backend/app/douyin_service.py`（新文件）

模块暴露三个公开函数 + 一个内部 helper：

```python
DOUYIN_API_BASE = "https://www.lieshouyin.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def is_douyin_url(url: str) -> bool: ...
def parse_video(url: str) -> dict: ...
def download_video(url: str, format_id: str, dest_dir: Path, progress_hook) -> Path: ...

def _resolve_video_id(url: str) -> str: ...   # 短链 302 / 长链正则
def _fetch_video_info(video_id: str) -> dict: ...   # 调公开 API
def _strip_watermark(play_url: str) -> str: ...   # playwm → play
```

### 4.2 核心步骤详解

**Step ① 短链解析**

`v.douyin.com/xxx` 是 302 重定向到 `www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=...` 这类长链。

实现：`requests.head(url, allow_redirects=True, timeout=8, headers={"User-Agent": UA})`，最终 URL 上的 `item_ids=` 参数或路径里的 19 位数字 ID 即为 video_id。

长链（`www.douyin.com/video/7123456789012345678` 或 `www.iesdouyin.com/.../video/...`）：正则提取 19 位数字 ID。

**Step ② 调公开 API**

`GET {DOUYIN_API_BASE}/api/video/info?video_id={id}`，返回 JSON：

```json
{
  "code": 0,
  "data": {
    "title": "...",
    "cover": "https://p3-sign.douyinpic.com/...",
    "duration": 30,
    "play_url": "https://v26-cold.douyinvod.com/...playwm...",
    "playwm_url": "https://v26-cold.douyinvod.com/...playwm..."
  }
}
```

**Step ③ 去水印**

若 `data.playwm_url` 含 `playwm`：直接 `playwm → play` 替换得无水印 URL；若只有 `play_url`（已无 wm）则原样用。

**Step ④ 进度回调契约**

为和 `ytdlp_service` 一致，构造一个最小可用的 progress_hook：

```python
def _make_hook(hook):
    last_emit = [0.0]
    def inner(block_number, read_size, total_size):
        if total_size > 0:
            now = time.monotonic()
            if now - last_emit[0] >= 0.3 or read_size == total_size:
                hook({"status": "downloading",
                      "downloaded_bytes": block_number * read_size,
                      "total_bytes": total_size,
                      "total_bytes_estimate": total_size,
                      "speed": None, "eta": None})
                last_emit[0] = now
    return inner
```

最终 `finished` 时调一次 `hook({"status": "finished"})` 与 yt-dlp hook 语义对齐。

### 4.3 返回 `parse_video` 的 dict 结构（必须与 `ytdlp_service.parse_video` 对齐）

```python
{
    "title": str,
    "thumbnail": str | None,        # 走 /api/thumbnail 代理
    "duration": int | None,
    "extractor": "Douyin (API 解析)",
    "uploader": str | None,
    "view_count": int | None,        # 公开 API 没给则为 None
    "description": str | None,
    "webpage_url": str,
    "presets": [...],                # 占位，与 yt-dlp 同源
    "formats": [...],                # 空列表
    "choices": [                     # 只有一条
        {
            "id": "douyin-nowm",
            "label": "无水印视频",
            "note": "MP4 · 第三方解析",
            "kind": "video",
            "ext": "mp4",
            "height": None,
            "filesize": None,
            "has_audio": True,
            "title": "无水印视频 (MP4)",
            "subtitle": "MP4 · 第三方解析",
        }
    ],
}
```

### 4.4 `main.py` 改动

最小侵入：在两个入口函数顶部加 `if is_douyin_url(url): return douyin_service.parse_video(url)`。

- `parse()` 加一行 if。
- `_run_download()` 的 `download_video(...)` 调用改成 `download_video_fn(url, format_id, dest, hook)`，根据 URL 选择。
- 错误处理保持：`_public_error` 仍把 "Unsupported URL" / 412 等兜底文本透传。
- 新增一个 douyin 专属错误：在 `_public_error` 捕获 `DouyinUpstreamError` 时返回「抖音解析服务暂不可用：XXX，换条链接重试」。

### 4.5 前端

`App.vue` 不动。`displayPlatform("douyin (api 解析)")` 走 `key.includes("douyin")` 分支显示为「TikTok」（项目现有逻辑）。

## 5. 错误处理

| 场景 | HTTP | 中文提示 |
| --- | --- | --- |
| 短链 30x 后仍无 video_id | 502 | 「抖音短链无效或已过期」 |
| 上游 API 非 200 | 502 | 「抖音解析服务暂不可用：HTTP 502」 |
| API 返回 `code != 0` | 502 | 「抖音解析失败：<msg>」 |
| 缺 `playwm_url` 且 `play_url` 也无 | 502 | 「没拿到视频源，链接可能无效」 |
| 下载 HTTP 4xx/5xx | task error | 「抖音源下载失败：HTTP XXX」 |
| 流中断 / 超时 | task error | 「抖音下载中断：<exc>」 |

错误路径上抛 `DouyinUpstreamError` 自定义异常，`_public_error` 统一兜底中文。

## 6. 测试

`backend/tests/test_douyin.py`：

### 6.1 纯函数单测（永远跑）

- `test_is_douyin_url` — `v.douyin.com/xxx` / `www.douyin.com/video/7123` / `www.iesdouyin.com/...` / 非抖音（YouTube）四类。
- `test_extract_video_id_from_long_url` — 19 位数字正则。
- `test_strip_watermark` — `playwm` → `play` 替换；幂等；无 `playwm` 时原样返回。
- `test_build_choices` — choices 列表构造正确。
- `test_resolve_video_id_short_url` — 用 `requests-mock`/`responses` 模拟 302（首选 `responses`，避免拉新依赖）。

### 6.2 live 烟雾测试（标记 `@pytest.mark.live`，默认 skip）

- `DOUYIN_SMOKE=1` 才跑。
- 真实短链 → 拿到 video_id。
- 真实 API 调用 → 拿到 JSON（有 `code==0` 时算通过）。
- 不下载真实视频（避免依赖在线带宽）。
- 失败不阻塞 CI；仅做手工验证时打开。

### 6.3 回归

`pytest` 现有用例（`test_health` / `test_urls` / `test_formats` / `test_thumbnail`）必须仍通过。

## 7. 验收口径

| 项 | 验收 |
| --- | --- |
| 抖音短链解析 | 浏览器粘贴 `https://v.douyin.com/xxxx/` → 前端拿到 title / cover / duration，显示 1 个「无水印视频」选择 |
| 抖音长链解析 | 同上，用 `https://www.douyin.com/video/19位数字` |
| 下载成功 | 点下载 → 拿到 mp4 文件，文件名是 `{task_id}.mp4`，视频画面**无水印** |
| 上游失败 | 网络断 / 域名解析失败时，前端 error-line 显示中文提示，不暴露堆栈 |
| 其他平台不受影响 | YouTube / B 站 / Twitter 链接继续走 yt-dlp，行为不变 |
| 单元测试 | `pytest` 全绿；live 标记默认 skip |
| 后端 health | `/api/health` 返回 `{"ok": true, "engine": "yt-dlp"}`（不变；扩展字段不在本次范围） |

## 8. 风险与权衡

| 风险 | 应对 |
| --- | --- |
| `lieshouyin.com` 是个人项目，可能跑路 / 改版 | 错误信息直接透传给用户；学习版范围内不引入 fallback 链 |
| 上游限流 / 高并发被 ban | 单进程串行下载（已有 `MAX_CONCURRENT=2`）；生产环境不该把本项目裸挂公网 |
| 抖音改版后 video_id 提取失败 | 在 `urls.py` 仅放宽识别规则；不绕过签名 / 登录态 |
| 短链服务响应慢（>8s） | `timeout=8` 立刻失败；不拖死前端轮询 |
| 视频源 URL 过期（CDN token TTL） | 解析和下载之间间隔长会失败；前端拿到 choices 后尽快点击（已与现有行为一致） |
| 单格式选择 | 抖音只有「无水印视频」一种；前端 `quality-grid` 仍正常显示一张卡 |

## 9. 后续可选（不进本次 plan）

- 把 `DOUYIN_API_BASE` 提到环境变量
- 增加多个上游 API 列表 + 自动 failover
- 抖音直播支持
- TikTok 国际版适配（同样的 lieshouyin 路径）

---

## Next

- **用户审 spec**：本会话请确认上面 § 1–9 是否符合预期。修改意见请直接说，spec 仍在 `status: draft`。
- **通过后**：进入 `writing-plans` 阶段，产出 `.ai-runtime-artifacts/plans/2026-09-17-douyin-adapter-plan.md`。
- **再之后**：实现 + 落盘 `verification-lite.md`。