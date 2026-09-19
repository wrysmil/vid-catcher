---
artifact: verification-lite
route: leader-direct
skills:
  - verification-before-completion
skills_evidence:
  - ~/.claude/skills/verification-before-completion/SKILL.md (loaded implicitly via routing.md § 按判定加载「Leader 直做 / Tier 1」)
source:
  - .ai-runtime-artifacts/specs/2026-09-17-douyin-adapter-spec.md
  - .ai-runtime-artifacts/plans/2026-09-17-douyin-adapter-plan.md
created_at: 2026-09-17
tier: 1
---

# 抖音视频下载适配 — 轻量验证（Tier 1）

> **纪律：** Leader 直做简单任务。先跑命令再给结论，每条命令附实际输出。

## 防跳过提醒

| 合理化借口 | 现实 |
|-----------|------|
| "只改了一行，不用验证" | 本次改动触及 main.py 路由分发 + 新模块 + requirements.txt，回归面覆盖全 API |
| "上次跑过了" | 每 Task commit 后都重跑测试，但尾盘必须独立验证一次 |
| "看起来没问题" | 抖音 service 集成涉及短链 302 + 上游 API + 流式下载三步串联，单元绿 ≠ 集成绿 |
| "太简单了，省掉吧" | main.py 的 `_run_download` 改动会让抖音 / 其它平台走不同 download_fn，必须回归 |

## 范围

| 改动文件 | 动作 |
| --- | --- |
| `backend/app/douyin_service.py` | 新建（纯函数 + parse_video + download_video + DouyinUpstreamError） |
| `backend/tests/test_douyin.py` | 新建（25 单测 + 2 API 集成测试 + 1 live 烟雾默认 skip） |
| `backend/app/main.py` | 修改（`/api/parse` 加抖音分流 + `_public_error` 加中文兜底 + `_run_download` 选 download_fn） |
| `backend/pytest.ini` | 修改（注册 `live` marker） |
| `backend/requirements.txt` | 修改（pin `responses==0.26.3`） |
| `.gitignore` | 修改（排除含明文 API key 的 `.mcp.json`） |
| 前端 / `ytdlp_service.py` / `tasks.py` / `formats.py` | **不动** |

- 路由判定：Tier 1（Leader 直做，单 WU 单 GROUP，不委派）
- 用户授权方式：本会话先写 spec → 写 plan → 用户说「a」/「开始实现」三步授权

## 命令与结果

| 命令 | 结果 |
| --- | --- |
| `.venv/bin/pytest tests/test_douyin.py -v`（Task 1 写完后） | `12 passed in 0.01s` |
| `.venv/bin/pytest tests/test_douyin.py -v`（Task 2 写完后） | `19 passed in 0.06s`（含重定向链 + 短链失败 + API 错误 + HTTP 500 + 缺数据） |
| `.venv/bin/pytest tests/test_douyin.py -v`（Task 3 写完后） | `22 passed in 0.07s`（含流式下载 + 403 + 缺源） |
| `.venv/bin/pytest tests/test_douyin.py -v`（Task 4 写完后） | `25 passed in 0.20s`（含 2 个 API 集成测试 + monkeypatch 透传非抖音） |
| `.venv/bin/pytest tests/test_douyin.py::test_parse_real_short_link_smoke -v` | `1 skipped`（live 默认 skip） |
| `.venv/bin/pytest -v`（尾盘全量回归） | `40 passed, 1 skipped`（15 现有 + 25 抖音，live skip） |
| `uvicorn app.main:app --host 127.0.0.1 --port 8000` + `curl /api/health` | `{"ok":true,"engine":"yt-dlp"}` HTTP 200 |
| `git log --oneline`（commit 链） | `ad98c59 chore(deps) → ac2cde1 test(live) → 72853b5 feat(main) → 1f9a634 feat(download) → 602c0e2 feat(parse) → c5f8f33 chore(initial)` |

## 验收口径 vs 实际

| spec § 7 验收项 | 结果 |
| --- | --- |
| 抖音短链解析 → title / cover / duration + 1 个选择 | `test_parse_video_short_link_resolves_and_strips_watermark` ✓ + `test_api_parse_douyin_short_routes_to_douyin_service` ✓ |
| 抖音长链解析 | `test_parse_video_long_url_skips_redirect` ✓ |
| 下载成功 → mp4 文件，画面无水印 | `test_download_video_streams_to_file_and_invokes_hook` ✓（mock body 验证 bytes 一致 + downloading/finished 事件派发）。**真实视觉无水印需 live 验证** |
| 上游失败 → 中文提示，不暴露堆栈 | `test_api_parse_douyin_upstream_failure_returns_502_chinese` ✓（detail 含 "boom" / "抖音"） |
| 其他平台不受影响 | `test_api_parse_non_douyin_url_passes_through_to_ytdlp` ✓（monkeypatch ytdlp.parse_video 被调用）+ 现有 4 个 ytdlp 链路单测全绿 |
| 单元测试全绿；live 默认 skip | `40 passed, 1 skipped` ✓ |
| `/api/health` 返回 `{"ok": true, "engine": "yt-dlp"}` | 实测一致 ✓ |

## 未验证项（声明已知边界）

| 项 | 原因 | 影响 |
| --- | --- | --- |
| live 烟雾测试（真实短链 → 真实 API） | 缺真实 `v.douyin.com/xxx` 短链 + 第三方 API 网络可达性不定 | 默认 skip；用户手上有真实链接时可手动 `DOUYIN_SMOKE=1 DOUYIN_SMOKE_URL=... pytest -v -m live` |
| 真实视觉无水印（播放验证） | 沙箱无 GUI 播放器；mock 流式下载字节一致已验证 | 需用户在网页端点真实链接目测 |
| upstream 限流 / 高并发被 ban | 学习版范围内不模拟 | 单进程串行下载 + MAX_CONCURRENT=2 已保留 |
| CDN token TTL 引发的下载失效 | 上游 play_url 几分钟后过期 | 与现有 yt-dlp 行为对齐；解析后尽快下载 |
| 前端 UI 视觉 | 未改 `App.vue`；`displayPlatform` 已含 `douyin` → `TikTok` 分支 | 用户打开网页可见 extractor 字段标为 "Douyin (API 解析)" |

## 风险与权衡（与 spec § 8 对齐）

- `lieshouyin.com` 是个人项目，可能跑路 / 改版 → 上游失败路径已透传中文，不引入 fallback 链
- 视频源 URL 有 CDN token TTL → 解析后尽快下载
- 单格式选择（无水印视频） → 前端 `quality-grid` 显示一张卡，与现有行为一致
- `responses==0.26.3` 是清华源下能找到的最新版本（无 0.25.3），API 兼容（去掉了 `stream=True` 参数）

## Next

- 任务完成，可关闭本次 GROUP
- 用户可手动跑 live 烟雾测试验证真实链路：
  ```bash
  export DOUYIN_SMOKE=1
  export DOUYIN_SMOKE_URL='https://v.douyin.com/真实短链/'
  cd backend && .venv/bin/pytest tests/test_douyin.py::test_parse_real_short_link_smoke -v -s
  ```
- 范围未扩大，无需升级 Tier 2 编排
- 推送 / 开 PR：按 `project.git.md` Leader **不**自动推，须用户确认后再执行