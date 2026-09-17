---
artifact: verification-lite
route: leader-direct | 小改动直做
skills:
  - verification-before-completion
skills_evidence:
  - ~/.agents/skills/verification-before-completion/SKILL.md
source:
  - "用户：目前视频导出的文件名有问题，参考下 free-video-downloader 怎么设计导出文件名的 / 直接优化"
created_at: 2026-09-17
tier: 1
---

# 导出文件名清洗 — 轻量验证（Tier 1）

## 范围

- 改动文件：
  - `backend/app/filenames.py`（新增，`safe_filename` 共享清洗）
  - `backend/app/ytdlp_service.py`（去 `restrictfilenames`，新增 `_resolve_output` / `_rename_to_title`）
  - `backend/app/douyin_service.py`（`_download_with_atomic_write` 支持 `filename` 参数，不再写死 `douyin.mp4`）
  - `backend/tests/test_filenames.py`（新增，11 例）
  - `backend/tests/test_douyin.py`（shim 跟随新签名 + 补文件名断言）
- 路由判定：Tier 1（Leader 直做）

## 根因（实证）

| 链路 | 问题 | 证据 |
| --- | --- | --- |
| yt-dlp | `restrictfilenames: True` 会**删除**所有非 ASCII 字符 | `sanitize_filename('【4K】猫咪的日常 vlog #1', restricted=True)` → `'4K_vlog_1'`；`'测试 视频.mp4'` → `'.mp4'`（标题整个消失） |
| 抖音 | 文件名硬编码为 `douyin.mp4`，解析出的 title 未被使用 | `douyin_service.py:659` |

参考项目 `free-video-downloader` 的做法：保留 Unicode，只替换文件系统非法字符 + 去首尾杂符 + 截断 + 折叠连续下划线 + 空标题回退到 ID。本项目在其基础上补了 Windows 保留设备名与结尾 `.`/空格两项。

## 命令与结果

| 命令 | 结果 |
| --- | --- |
| `cd backend && python -m pytest -q` | **77 passed, 1 skipped**（6.03s；skipped 为改动前既有） |
| `cd backend && python -c "import app.main"` | `import ok` |
| `python -m py_compile app/filenames.py app/ytdlp_service.py app/douyin_service.py` | `compile ok` |
| 端到端链路脚本（模拟 yt-dlp 中间名 → 重命名，无网络） | 见下表 |

端到端输出：

| 标题 | yt-dlp 中间名 | 最终文件名 |
| --- | --- | --- |
| `【4K】猫咪的日常 vlog #1` | `【4K】猫咪的日常 vlog #1.mp4` | `【4K】猫咪的日常 vlog #1.mp4` |
| `测试 视频` | `测试 视频.mp4` | `测试 视频.mp4` |
| `C++/Rust: 对比?` | `C++⧸Rust： 对比？.mp4` | `C++_Rust_ 对比.mp4` |
| `a`×200 | 80 个 a | 80 个 a（截断 + 补扩展名） |

边界用例（单测覆盖）：全非法字符回退 `douyin_7123.mp4`、`CON` → `_CON.mp4`、NFD→NFC、`ext` 带不带点、截断后落在分隔符上需二次 trim。

## 未验证项

- **未做真实联网下载**（YouTube / B 站 / 抖音）。端到端链路用 `yt_dlp.utils.sanitize_filename` 生成真实中间名 + 桩文件重命名来覆盖，但「yt-dlp 实际落盘的路径能否被 `_resolve_output` 命中」只在 `prepare_filename` / `.mp4` / 扫目录三级逻辑上做了静态确认，未跑真机。
- **未在浏览器验证 Content-Disposition**。`FileResponse(filename=path.name)` 对非 ASCII 走 Starlette 的 RFC 5987 `filename*=utf-8''`，属框架既有行为，本次未改动该行。
- `harness-check.sh` 报 `.claude/rules/leader.md`、`.claude/hooks/block-native-plan-mode.sh`、`.claude/settings.json.example` 缺失 —— 会话开始时的 `git status` 已显示 `.claude/` 下大量文件处于**已暂存删除**状态，与本次改动无关，未处理。

## Next

- 任务完成 → 无需暂停（除非用户要求 commit/MR）
- 建议后续：联网跑一次真实 B 站 + 抖音下载，确认落盘名与浏览器保存名
- 范围扩大 → 补 spec/plan 或升级 Tier 2 编排
