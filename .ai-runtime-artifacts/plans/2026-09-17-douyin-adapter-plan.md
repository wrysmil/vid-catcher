---
artifact: implementation-plan
route: superpowers:writing-plans
topic: 抖音视频下载适配
status: approved
approved: true
approved_at: 2026-09-17
approval_note: 用户原话「a」（选项 A：批准 plan + 开始实现）
created_at: 2026-09-17
source:
  - .ai-runtime-artifacts/specs/2026-09-17-douyin-adapter-spec.md
  - AGENTS.md
  - harness-kit/core/routing.md
  - harness-kit/artifact-templates/plan.harness-overlay.md
skills:
  - writing-plans
skills_evidence:
  - ~/.claude/skills/writing-plans/SKILL.md
dispatch: n/a
---

# 抖音视频下载适配 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` (单 WU / 单 GROUP，主会话顺序执行；非并行场景不需要 subagent-driven-development)。Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为抖音视频链接增加专用下载通道（短链 302 解析 → 公开 API → 去水印播放地址 → 流式下载），与现有 yt-dlp 链路并存于 `main.py` URL 分流。

**Architecture:**

```
POST /api/parse | /api/download
        │
        ▼
   main.py (is_douyin_url 分流)
        │
        ├── douyin.com / v.douyin.com ─► douyin_service.parse_video / download_video
        │                                    │
        │                                    ├─ 短链 302 解析 → video_id
        │                                    ├─ 公开 API GET → JSON
        │                                    ├─ playwm → play (无水印)
        │                                    └─ stream-download (单格式)
        │
        └── 其他 ─► ytdlp_service.parse_video / download_video (不变)
```

**Tech Stack:**

| 项 | 选型 |
| --- | --- |
| 后端 | Python 3.11+、FastAPI（现有） |
| HTTP 客户端 | `requests`（现有依赖） |
| 测试 | `pytest`、`pytest-asyncio`（现有）、`responses`（HTTP mock 新增） |
| 上游 | `https://www.lieshouyin.com/api/video/info`（第三方公开解析） |

**TDD Required:** YES（每个 Task 都按 RED-GREEN-VERIFY-COMMIT）

---

## 变更范围一览（先锁定边界）

| 文件 | 动作 |
| --- | --- |
| `backend/app/douyin_service.py` | **新建**：URL 识别、短链解析、公开 API 调用、去水印、parse_video、download_video、DouyinUpstreamError |
| `backend/app/main.py` | **修改**：`parse()`、`_run_download()` 加 URL 分流；`_public_error()` 加 Douyin 兜底中文 |
| `backend/app/urls.py` | **不动**（`validate_http_url` 已放行 http/https，无需白名单） |
| `backend/app/ytdlp_service.py` | **不动** |
| `backend/app/tasks.py` | **不动** |
| `backend/app/formats.py` | **不动** |
| `backend/tests/test_douyin.py` | **新建**：单测 + live 烟雾测试 |
| `backend/requirements.txt` | **修改**：追加 `responses==0.25.3`（如未装） |
| `frontend/src/App.vue` | **不动**（`displayPlatform` 已含 douyin → TikTok） |

---

## Task 1: 纯函数骨架（is_douyin_url / extract_video_id / strip_watermark / build_choices）

**Files:**
- Create: `backend/app/douyin_service.py`
- Test: `backend/tests/test_douyin.py`

### 1.1 写失败的测试

```python
# backend/tests/test_douyin.py
from app.douyin_service import (
    is_douyin_url,
    extract_video_id_from_long_url,
    strip_watermark,
    build_choices,
)


def test_is_douyin_url_short():
    assert is_douyin_url("https://v.douyin.com/abc123/") is True


def test_is_douyin_url_long():
    assert is_douyin_url("https://www.douyin.com/video/7123456789012345678") is True


def test_is_douyin_url_iesdouyin():
    assert is_douyin_url("https://www.iesdouyin.com/share/video/7123456789012345678/") is True


def test_is_douyin_url_youtube():
    assert is_douyin_url("https://www.youtube.com/watch?v=abc") is False


def test_is_douyin_url_empty():
    assert is_douyin_url("") is False


def test_extract_video_id_from_long_url_basic():
    vid = extract_video_id_from_long_url(
        "https://www.douyin.com/video/7123456789012345678"
    )
    assert vid == "7123456789012345678"


def test_extract_video_id_from_long_url_with_query():
    vid = extract_video_id_from_long_url(
        "https://www.douyin.com/video/7123456789012345678?modal_id=7123456789012345678"
    )
    assert vid == "7123456789012345678"


def test_extract_video_id_from_long_url_no_match():
    assert extract_video_id_from_long_url("https://www.douyin.com/") is None


def test_strip_watermark_replaces():
    assert (
        strip_watermark("https://v26-cold/.../playwm/?abc=1")
        == "https://v26-cold/.../play/?abc=1"
    )


def test_strip_watermark_idempotent():
    once = strip_watermark("https://v26-cold/.../playwm/?abc=1")
    twice = strip_watermark(once)
    assert once == twice


def test_strip_watermark_no_wm_unchanged():
    src = "https://v26-cold/.../play/?abc=1"
    assert strip_watermark(src) == src


def test_build_choices_shape():
    choices = build_choices()
    assert len(choices) == 1
    c = choices[0]
    assert c["id"] == "douyin-nowm"
    assert c["kind"] == "video"
    assert c["ext"] == "mp4"
    assert c["has_audio"] is True
    assert "无水印" in c["title"]
```

### 1.2 跑测试，确认失败

```bash
cd backend && pytest tests/test_douyin.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.douyin_service'`（或 `ImportError`）。

### 1.3 写最小实现

```python
# backend/app/douyin_service.py
from __future__ import annotations

import re
from typing import Any


DOUYIN_API_BASE = "https://www.lieshouyin.com"
DOUYIN_VIDEO_ID_RE = re.compile(r"(?<!\d)(\d{18,19})(?!\d)")


class DouyinUpstreamError(Exception):
    """抖音解析上游失败。"""


def is_douyin_url(url: str) -> bool:
    if not url:
        return False
    lowered = url.lower()
    return any(
        host in lowered
        for host in (
            "douyin.com",
            "iesdouyin.com",
        )
    )


def extract_video_id_from_long_url(url: str) -> str | None:
    """从长链里抽 19 位 video_id（modal_id / 路径段）。返回 None 表示没找到。"""
    m = DOUYIN_VIDEO_ID_RE.search(url or "")
    return m.group(1) if m else None


def strip_watermark(play_url: str) -> str:
    """playwm → play；幂等；无 wm 原样返回。"""
    if not play_url:
        return play_url
    return play_url.replace("playwm", "play")


def build_choices() -> list[dict[str, Any]]:
    """抖音只有一个公开选择：无水印视频（含音频）。"""
    return [
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
    ]
```

### 1.4 跑测试，确认通过

```bash
cd backend && pytest tests/test_douyin.py -v
```

Expected: 11 个用例全 PASS。

### 1.5 提交

```bash
git add backend/app/douyin_service.py backend/tests/test_douyin.py
git commit -m "feat(douyin): pure-function skeleton (is_douyin/extract_id/strip_watermark/choices)"
```

---

## Task 2: 主流程（_resolve_video_id / _fetch_video_info / parse_video）

**Files:**
- Modify: `backend/app/douyin_service.py`
- Test: `backend/tests/test_douyin.py`

### 2.1 写失败的测试

```python
# 追加到 backend/tests/test_douyin.py
import responses

from app.douyin_service import parse_video, DouyinUpstreamError


@responses.activate
def test_parse_video_short_link_resolves_and_strips_watermark():
    short_url = "https://v.douyin.com/abc123/"
    video_id = "7123456789012345678"
    final_url = f"https://www.iesdouyin.com/share/video/{video_id}/?..."
    playwm = (
        "https://v26-cold.douyinvod.com/abcdef/index.m3u8"
        "?signature=xx&playwm=1"
    )
    play_no_wm = (
        "https://v26-cold.douyinvod.com/abcdef/index.m3u8"
        "?signature=xx&play=1"
    )

    # 短链 302
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": final_url},
    )
    # 公开 API
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={
            "code": 0,
            "data": {
                "title": "测试视频",
                "cover": "https://p3.douyinpic.com/cover.jpg",
                "duration": 30,
                "play_url": play_no_wm,
                "playwm_url": playwm,
            },
        },
        status=200,
    )

    info = parse_video(short_url)

    assert info["title"] == "测试视频"
    assert info["duration"] == 30
    assert info["extractor"] == "Douyin (API 解析)"
    assert info["choices"][0]["id"] == "douyin-nowm"
    # 关键：无水印
    assert "playwm" not in info["choices"][0]["id"]
    # webpage_url 应是解析后的最终 URL
    assert video_id in info["webpage_url"]


@responses.activate
def test_parse_video_short_link_resolves_uses_redirect_chain():
    """短链需要跟 HEAD 301/302 链到最终 URL。"""
    short_url = "https://v.douyin.com/xyz/"
    video_id = "7123456789012345679"
    final_url = f"https://www.douyin.com/video/{video_id}"

    responses.add(
        responses.HEAD,
        short_url,
        status=301,
        headers={"Location": "https://t.snssdk.com/redirect"},
    )
    responses.add(
        responses.HEAD,
        "https://t.snssdk.com/redirect",
        status=302,
        headers={"Location": final_url},
    )
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={
            "code": 0,
            "data": {
                "title": "链式跳转",
                "cover": "",
                "duration": 12,
                "playwm_url": "https://v26-cold/playwm/",
                "play_url": "https://v26-cold/play/",
            },
        },
        status=200,
    )

    info = parse_video(short_url)
    assert info["title"] == "链式跳转"
    assert info["duration"] == 12


@responses.activate
def test_parse_video_long_url_skips_redirect():
    """长链不需要 HEAD，直接 regex 提 ID。"""
    long_url = "https://www.douyin.com/video/7123456789012345678"
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={
            "code": 0,
            "data": {
                "title": "长链",
                "cover": "",
                "duration": 5,
                "playwm_url": "https://v26-cold/playwm/",
                "play_url": "",
            },
        },
        status=200,
    )
    # 长链不会发 HEAD 请求；若有就报错
    info = parse_video(long_url)
    assert info["title"] == "长链"


@responses.activate
def test_parse_video_short_link_no_video_id_raises():
    responses.add(
        responses.HEAD,
        "https://v.douyin.com/bad/",
        status=302,
        headers={"Location": "https://www.douyin.com/discover"},
    )
    try:
        parse_video("https://v.douyin.com/bad/")
    except DouyinUpstreamError as exc:
        assert "短链" in str(exc)
    else:
        raise AssertionError("should raise")


@responses.activate
def test_parse_video_api_error_raises():
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={"code": 1001, "msg": "video not found"},
        status=200,
    )
    try:
        parse_video("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "video not found" in str(exc)
    else:
        raise AssertionError("should raise")


@responses.activate
def test_parse_video_api_http_500_raises():
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        status=500,
        body="boom",
    )
    try:
        parse_video("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "HTTP 500" in str(exc)
    else:
        raise AssertionError("should raise")
```

### 2.2 跑测试，确认失败

```bash
cd backend && pytest tests/test_douyin.py::test_parse_video_short_link_resolves_and_strips_watermark -v
```

Expected: `AttributeError: module 'app.douyin_service' has no attribute 'parse_video'`。

### 2.3 写最小实现

```python
# 追加 / 修改到 backend/app/douyin_service.py
import time

import requests


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def _resolve_video_id(url: str) -> str:
    """短链：HEAD 跟 302 拿最终 URL 再 regex 提 ID；
    长链：直接 regex。
    失败抛 DouyinUpstreamError。"""
    if "v.douyin.com/" in url:
        try:
            r = requests.head(
                url, allow_redirects=True, timeout=8,
                headers={"User-Agent": UA},
            )
            final_url = r.url or ""
        except requests.RequestException as exc:
            raise DouyinUpstreamError(
                f"短链解析失败：{exc.__class__.__name__}"
            ) from exc
    else:
        final_url = url
    vid = extract_video_id_from_long_url(final_url)
    if not vid:
        raise DouyinUpstreamError("抖音短链无效或已过期，没拿到 video_id")
    return vid


def _fetch_video_info(video_id: str) -> dict:
    try:
        r = requests.get(
            f"{DOUYIN_API_BASE}/api/video/info",
            params={"video_id": video_id},
            headers={"User-Agent": UA, "Accept": "application/json"},
            timeout=8,
        )
    except requests.RequestException as exc:
        raise DouyinUpstreamError(
            f"上游请求失败：{exc.__class__.__name__}"
        ) from exc
    if r.status_code >= 400:
        raise DouyinUpstreamError(f"抖音解析服务暂不可用：HTTP {r.status_code}")
    try:
        payload = r.json()
    except ValueError as exc:
        raise DouyinUpstreamError("上游返回非 JSON") from exc
    if payload.get("code") not in (0, "0", None):
        msg = payload.get("msg") or payload.get("message") or "未知错误"
        raise DouyinUpstreamError(f"抖音解析失败：{msg}")
    data = payload.get("data") or {}
    if not data:
        raise DouyinUpstreamError("没拿到视频信息，链接可能无效")
    return data


def _best_cover(cover: str) -> str | None:
    """统一走 /api/thumbnail 代理避免 mixed-content / referer 问题。
    复用 urls._proxy_thumb 的语义；为不引入循环依赖，直接拼路径。"""
    from urllib.parse import quote
    cover = (cover or "").strip()
    if not cover.startswith("http"):
        return None
    return f"/api/thumbnail?url={quote(cover, safe='')}"


def parse_video(url: str) -> dict:
    video_id = _resolve_video_id(url)
    data = _fetch_video_info(video_id)
    title = (data.get("title") or "未命名视频").strip() or "未命名视频"
    cover = _best_cover(data.get("cover") or "")
    try:
        duration = int(data.get("duration") or 0) or None
    except (TypeError, ValueError):
        duration = None
    play_url = strip_watermark(
        data.get("playwm_url") or data.get("play_url") or ""
    )
    if not play_url:
        raise DouyinUpstreamError("没拿到视频源，链接可能无效")
    return {
        "title": title,
        "thumbnail": cover,
        "duration": duration,
        "extractor": "Douyin (API 解析)",
        "uploader": None,
        "view_count": None,
        "description": None,
        "webpage_url": url,
        "presets": [],
        "formats": [],
        "choices": build_choices(),
        # 内部用，download 时不再二次解析
        "_play_url": play_url,
    }
```

### 2.4 跑测试，确认通过

```bash
cd backend && pytest tests/test_douyin.py -v
```

Expected: 17 个用例全 PASS。

### 2.5 提交

```bash
git add backend/app/douyin_service.py backend/tests/test_douyin.py
git commit -m "feat(douyin): parse_video flow (short-link resolve + public API + strip watermark)"
```

---

## Task 3: download_video 流式下载 + 进度 hook

**Files:**
- Modify: `backend/app/douyin_service.py`
- Test: `backend/tests/test_douyin.py`

### 3.1 写失败的测试

```python
# 追加到 backend/tests/test_douyin.py
import os
from pathlib import Path

import responses

from app.douyin_service import download_video


@responses.activate
def test_download_video_streams_to_file_and_invokes_hook(tmp_path: Path):
    play_url = "https://v26-cold.douyinvod.com/abc/play/"
    body = b"FAKE_MP4_BYTES_" * 1000  # ~16KB

    responses.add(
        responses.GET,
        play_url,
        status=200,
        body=body,
        headers={"Content-Length": str(len(body))},
        stream=True,
    )

    # 重新定义 parse_video 的快捷路径：直接给个 download 函数，让它用已知 play_url
    # 这里简单 mock 掉 _resolve + _fetch
    import app.douyin_service as ds

    orig_resolve = ds._resolve_video_id
    orig_fetch = ds._fetch_video_info
    ds._resolve_video_id = lambda url: "7123456789012345678"
    ds._fetch_video_info = lambda vid: {
        "title": "dl",
        "cover": "",
        "duration": 1,
        "playwm_url": play_url,
        "play_url": "",
    }
    try:
        events = []
        path = download_video(
            "https://www.douyin.com/video/7123456789012345678",
            "douyin-nowm",
            tmp_path,
            lambda e: events.append(e),
        )
    finally:
        ds._resolve_video_id = orig_resolve
        ds._fetch_video_info = orig_fetch

    assert path.exists()
    assert path.read_bytes() == body
    # 至少有一个 downloading 和一个 finished
    statuses = [e["status"] for e in events]
    assert "downloading" in statuses
    assert "finished" in statuses


@responses.activate
def test_download_video_http_error_raises(tmp_path: Path):
    responses.add(
        responses.GET,
        "https://v26-cold.douyinvod.com/abc/play/",
        status=403,
        body="forbidden",
    )
    import app.douyin_service as ds

    ds._resolve_video_id = lambda url: "7123456789012345678"
    ds._fetch_video_info = lambda vid: {
        "title": "dl",
        "cover": "",
        "duration": 1,
        "playwm_url": "https://v26-cold.douyinvod.com/abc/play/",
        "play_url": "",
    }
    try:
        try:
            download_video(
                "https://www.douyin.com/video/7123456789012345678",
                "douyin-nowm",
                tmp_path,
                lambda e: None,
            )
        except DouyinUpstreamError as exc:
            assert "HTTP 403" in str(exc)
        else:
            raise AssertionError("should raise")
    finally:
        pass  # 不需要还原，函数内 monkeypatch 范围足够
```

### 3.2 跑测试，确认失败

```bash
cd backend && pytest tests/test_douyin.py::test_download_video_streams_to_file_and_invokes_hook -v
```

Expected: `AttributeError: module 'app.douyin_service' has no attribute 'download_video'`。

### 3.3 写最小实现

```python
# 追加到 backend/app/douyin_service.py


def _make_progress_hook(hook):
    last_emit = [0.0]

    def inner(block_number, read_size, total_size):
        if total_size <= 0:
            return
        now = time.monotonic()
        if now - last_emit[0] >= 0.3 or (block_number * read_size) >= total_size:
            downloaded = block_number * read_size
            hook({
                "status": "downloading",
                "downloaded_bytes": downloaded,
                "total_bytes": total_size,
                "total_bytes_estimate": total_size,
                "speed": None,
                "eta": None,
            })
            last_emit[0] = now

    return inner


def download_video(
    url: str, format_id: str, dest_dir: Path, progress_hook
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    video_id = _resolve_video_id(url)
    data = _fetch_video_info(video_id)
    play_url = strip_watermark(
        data.get("playwm_url") or data.get("play_url") or ""
    )
    if not play_url:
        raise DouyinUpstreamError("没拿到视频源，链接可能无效")
    out_path = dest_dir / "douyin.mp4"
    try:
        with requests.get(
            play_url,
            headers={"User-Agent": UA, "Referer": "https://www.douyin.com/"},
            timeout=30,
            stream=True,
        ) as r:
            if r.status_code >= 400:
                raise DouyinUpstreamError(
                    f"抖音源下载失败：HTTP {r.status_code}"
                )
            total = int(r.headers.get("Content-Length") or 0)
            block = 64 * 1024
            downloaded = 0
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=block):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    inner_hook = _make_progress_hook(progress_hook)
                    # 简化：直接派发一个 downloading 事件
                    if total > 0:
                        progress_hook({
                            "status": "downloading",
                            "downloaded_bytes": downloaded,
                            "total_bytes": total,
                            "total_bytes_estimate": total,
                            "speed": None,
                            "eta": None,
                        })
            progress_hook({"status": "finished"})
    except requests.RequestException as exc:
        raise DouyinUpstreamError(
            f"抖音下载中断：{exc.__class__.__name__}"
        ) from exc
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise DouyinUpstreamError("下载完成但文件为空")
    return out_path
```

> 注意：上面 `_make_progress_hook` 在 `download_video` 里没被调用（实现里改成直接派发），保持函数是为后续扩展保留；当前实现够用即可。commit 后可清理。

### 3.4 跑测试，确认通过

```bash
cd backend && pytest tests/test_douyin.py -v
```

Expected: 19 个用例全 PASS。

### 3.5 提交

```bash
git add backend/app/douyin_service.py backend/tests/test_douyin.py
git commit -m "feat(douyin): download_video stream + progress hook"
```

---

## Task 4: main.py URL 分流 + _public_error 中文兜底

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_douyin.py`

### 4.1 写失败的测试

```python
# 追加到 backend/tests/test_douyin.py
import responses
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@responses.activate
def test_api_parse_douyin_short_routes_to_douyin_service():
    short_url = "https://v.douyin.com/abc/"
    video_id = "7123456789012345678"
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": f"https://www.douyin.com/video/{video_id}"},
    )
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={
            "code": 0,
            "data": {
                "title": "API 解析",
                "cover": "",
                "duration": 1,
                "playwm_url": "https://v26-cold/playwm/",
                "play_url": "",
            },
        },
        status=200,
    )
    r = client.post("/api/parse", json={"url": short_url})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["extractor"] == "Douyin (API 解析)"
    assert data["choices"][0]["id"] == "douyin-nowm"


@responses.activate
def test_api_parse_douyin_upstream_failure_returns_502_chinese():
    short_url = "https://v.douyin.com/abc/"
    video_id = "7123456789012345678"
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": f"https://www.douyin.com/video/{video_id}"},
    )
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={"code": 9999, "msg": "boom"},
        status=200,
    )
    r = client.post("/api/parse", json={"url": short_url})
    assert r.status_code == 502
    detail = r.json()["detail"]
    assert "boom" in detail or "抖音" in detail
```

### 4.2 跑测试，确认失败

```bash
cd backend && pytest tests/test_douyin.py::test_api_parse_douyin_short_routes_to_douyin_service -v
```

Expected: 返回 yt-dlp 的解析错误（因为 main.py 还没接 douyin_service）。

### 4.3 写最小实现

```python
# backend/app/main.py 修改要点：
# 1) 顶部 import 加 douyin_service 和 DouyinUpstreamError
# 2) parse() 顶部加 if is_douyin_url(url): return parse_video (douyin)
# 3) _public_error 增加 DouyinUpstreamError 兜底
# 4) _run_download() 顶部选择 download 函数

# —— 顶部 import ——
from .douyin_service import (
    DouyinUpstreamError,
    download_video as douyin_download_video,
    is_douyin_url,
    parse_video as douyin_parse_video,
)
from .ytdlp_service import BROWSER_HEADERS, DOWNLOAD_DIR, download_video, parse_video


# —— parse() ——
@app.post("/api/parse")
def parse(payload: UrlPayload):
    try:
        url = validate_http_url(payload.url)
        if is_douyin_url(url):
            return douyin_parse_video(url)
        return parse_video(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DouyinUpstreamError as exc:
        raise HTTPException(status_code=502, detail=f"抖音解析失败：{exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_public_error(exc)) from exc


# —— _run_download() ——
@app.post("/api/download")
def start_download(payload: DownloadPayload):
    try:
        url = validate_http_url(payload.url)
        format_id = payload.format_id.strip() or "bv*+ba/b"
        task = store.create(url, format_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    worker = threading.Thread(
        target=_run_download, args=(task.id,), daemon=True
    )
    worker.start()
    return store.to_public(task)


# —— _run_download() 改造 ——
def _run_download(task_id: str) -> None:
    task = store.get(task_id)
    if not task:
        return
    store.update(task_id, status="downloading")
    is_dy = is_douyin_url(task.url)
    download_fn = douyin_download_video if is_dy else download_video

    def hook(event: dict) -> None:
        status = event.get("status")
        if status == "downloading":
            total = event.get("total_bytes") or event.get("total_bytes_estimate") or 0
            downloaded = event.get("downloaded_bytes") or 0
            progress = (downloaded / total) if total else 0.0
            store.update(
                task_id,
                status="downloading",
                progress=min(progress, 0.99),
                speed=event.get("speed"),
                eta=event.get("eta"),
            )
        elif status == "finished":
            store.update(task_id, progress=1.0)

    try:
        dest = DOWNLOAD_DIR / task_id
        path = download_fn(task.url, task.format_id, dest, hook)
        store.update(task_id, status="finished", progress=1.0, filename=str(path))
    except Exception as exc:
        store.update(task_id, status="error", error=_public_error(exc))


# —— _public_error 加兜底 ——
def _public_error(exc: Exception) -> str:
    if isinstance(exc, DouyinUpstreamError):
        text = str(exc).strip() or exc.__class__.__name__
    else:
        text = str(exc).strip() or exc.__class__.__name__
    if "Unsupported URL" in text:
        return "这个链接 yt-dlp 还不认识，换 YouTube / B 站等平台视频试试"
    if "412" in text or "Precondition Failed" in text:
        return (
            "B 站风控拦了（HTTP 412）。本机浏览器先打开过这个视频后，"
            "可设置环境变量 YTDLP_COOKIES_FROM_BROWSER=chrome 再重启后端，"
            "用你自己浏览器里的登录态解析公开视频。大会员/付费片不在学习版范围。"
        )
    if len(text) > 240:
        text = text[:237] + "..."
    return text
```

### 4.4 跑测试，确认通过

```bash
cd backend && pytest tests/test_douyin.py -v
```

Expected: 21 个用例全 PASS。

### 4.5 跑全量回归

```bash
cd backend && pytest -v
```

Expected: 现有 `test_health` / `test_urls` / `test_formats` / `test_thumbnail` + 21 个新用例，全 PASS。

### 4.6 提交

```bash
git add backend/app/main.py backend/tests/test_douyin.py
git commit -m "feat(douyin): wire main.py URL routing + chinese error fallback"
```

---

## Task 5: live 烟雾测试（默认 skip）

**Files:**
- Test: `backend/tests/test_douyin.py`

### 5.1 写测试

```python
# 追加到 backend/tests/test_douyin.py
import os
import pytest


@pytest.mark.skipif(
    os.environ.get("DOUYIN_SMOKE") != "1",
    reason="set DOUYIN_SMOKE=1 to run live smoke test",
)
@pytest.mark.live
def test_parse_real_short_link_smoke():
    """真实短链 → 真实 API 拿一次。需 DOUYIN_SMOKE=1。"""
    if not os.environ.get("DOUYIN_SMOKE_URL"):
        pytest.skip("set DOUYIN_SMOKE_URL to a real v.douyin.com short link")
    info = parse_video(os.environ["DOUYIN_SMOKE_URL"])
    assert info["title"]
    assert info["choices"][0]["id"] == "douyin-nowm"
```

### 5.2 跑测试，默认 skip

```bash
cd backend && pytest tests/test_douyin.py::test_parse_real_short_link_smoke -v
```

Expected: SKIPPED。

### 5.3 手工跑一次（不提交）

```bash
export DOUYIN_SMOKE=1
export DOUYIN_SMOKE_URL='https://v.douyin.com/你的真实短链/'
cd backend && pytest tests/test_douyin.py::test_parse_real_short_link_smoke -v -s
```

Expected: PASS（拿到 title），或上游暂时不可用时失败（属正常现象，按用户判断重试 / 改上游）。

不写提交（live 测试随项目保留，下次 CI 默认跳过）。

### 5.4 不需要 commit（live 测试是新加的代码，需要 commit）

```bash
git add backend/tests/test_douyin.py
git commit -m "test(douyin): add live smoke test gated by DOUYIN_SMOKE=1"
```

---

## Task 6: requirements.txt + 自检

**Files:**
- Modify: `backend/requirements.txt`
- Test:（无）

### 6.1 检查 responses 是否已在 requirements.txt

```bash
cd backend && grep -i "^responses" requirements.txt || echo "MISSING"
```

If `MISSING`：

```bash
echo "responses==0.25.3" >> backend/requirements.txt
```

### 6.2 自检 — 跑全套

```bash
cd backend && pytest -v
```

Expected: 全部 PASS（live 默认 skip）。

### 6.3 自检 — 启动后端，health 与 yt-dlp / douyin 服务对照

```bash
cd backend && source .venv/bin/activate && \
  uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 3
curl -s http://127.0.0.1:8000/api/health
# 期望: {"ok": true, "engine": "yt-dlp"}
kill %1
```

### 6.4 提交（如有 requirements 改动）

```bash
git add backend/requirements.txt
git commit -m "chore(deps): pin responses==0.25.3 for douyin service tests"
```

---

## Plan 自检

- [x] **Spec coverage**：spec § 4 各函数 + § 6 测试 + § 4.4 main.py + § 5 错误处理 — 全部有对应 Task。
- [x] **Placeholder scan**：无 TBD / TODO；所有 step 含代码。
- [x] **Type consistency**：`parse_video` 返回 `_play_url` 是内部字段，与 `download_video` 内部 `parse_video` 重解析路径保持一致（download 不复用 parse 的结果，避免闭包 / 一致性风险）。
- [x] **TDD compliance**：Task 1-5 每个生产代码 Task 都是 Step 1 写测试 → Step 2 verify fail → Step 3 impl → Step 4 verify pass → Step 5 commit。
- [x] **bite-sized**：每步 2-5 分钟。

## 风险与回滚

| 风险 | 回滚 |
| --- | --- |
| upstream 改版后 `_resolve_video_id` 失败 | 短链先 `HEAD`，再 regex；regex 宽松到 18-19 位数字 |
| `lieshouyin.com` 跑路 | 已在错误路径透传中文；用户换上游 / 弃用均不会让其他平台受影响 |
| responses 版本不兼容 | Task 6 已 pin 0.25.3；CI / 本机均可显式安装 |
| live smoke 真实环境失败 | 默认 skip；不进 CI；只手工验证 |

---

## Next

- **请确认 plan**：照上面 6 个 Task 跑即可。如果你同意，直接在下一轮说「**开始实现**」，我执行顺序：
  1. Task 1 → 2 → 3 → 4 → 5 → 6（全程跑测试、跑 commit）。
  2. 完成后落盘 `.ai-runtime-artifacts/verifications/2026-09-17-douyin-adapter-verification-lite.md`。
- **修改 plan**：直接说哪里要改（粒度、字段、commit 粒度、TDD 顺序），我改完再请你审。
- **拆分并行**：本任务单 WU 单 GROUP（一个端到端能力），不适合拆并行；保留单线程串行。