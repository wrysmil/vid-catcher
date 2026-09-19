---
artifact: verification-lite
route: leader-direct
topic: 抖音总结走公开 API
skills:
  - verification-before-completion
  - systematic-debugging
  - source-driven-development
  - test-driven-development
skills_evidence:
  - verification-before-completion@harness-kit/.agents/skills/verification-before-completion/SKILL.md loaded
  - systematic-debugging@harness-kit/.agents/skills/systematic-debugging/SKILL.md loaded
  - source-driven-development@harness-kit/.agents/skills/source-driven-development/SKILL.md loaded
source:
  - 用户报错 Unsupported URL jingxuan?modal_id=
  - 用户「可是抖音目前不是走公共API吗」
created_at: 2026-09-19
tier: 1
---

# 抖音总结走公开 API — 轻量验证（Tier 1）

## 范围

- `backend/app/summarizer.py`：抖音 URL 走 `parse_video(..., require_play_url=False)`，不再丢给 yt-dlp
- `backend/app/douyin_service.py`：`jingxuan?modal_id=` 直接抽 ID；解析结果带完整 `desc`
- `frontend/src/components/VideoSummary.vue`：`description` 显示为「视频文案」
- 测试：`test_summarizer.py`、`test_douyin.py`

## 命令与结果

| 命令 | 结果 |
| --- | --- |
| `pytest tests/test_summarizer.py::test_extract_douyin_*`（实现前） | RED：`summarizer` 无 `parse_video` |
| `cd backend && .venv/bin/pytest -q` | **88 passed, 8 skipped** |
| 直播抽取 `jingxuan?modal_id=7686500203570023723` | `has_subtitle=True`，`subtitle_type=description`，文案为《反相之地》锐评 |
| TestClient `POST /api/summarize` 同 URL | `subtitle → summary* → mindmap → done`，无 `Unsupported URL` |

## 未验证项

| 项 | 原因 |
| --- | --- |
| 正在跑的 uvicorn（无 `--reload`） | 需重启后前端才吃到新代码 |
| 浏览器四 Tab 手工点选 | 旧进程未加载本轮改动 |

## TDD

- 会话内先写失败测试再改生产代码：YES
- 独立 test/code commit：N/A（用户未要求提交）
- Happy path / 空文案 / jingxuan 不走重定向：YES

## Next

- 任务完成 → 重启后端后刷新页面再点「AI 总结」
- 无需暂停（除非用户要求 commit）
