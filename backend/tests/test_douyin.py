"""抖音视频解析/下载服务的单元测试。

单测始终跑；live 烟雾测试见 test_parse_real_short_link_smoke，需 DOUYIN_SMOKE=1。
"""
from __future__ import annotations

from app.douyin_service import (
    build_choices,
    extract_video_id_from_long_url,
    is_douyin_url,
    strip_watermark,
)


# ─────────────────────────── 纯函数骨架（Task 1） ───────────────────────────


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


# ─────────────────────────── 主流程 parse_video（Task 2） ───────────────────────────

import responses

from app.douyin_service import DOUYIN_API_BASE, DouyinUpstreamError, parse_video


@responses.activate
def test_parse_video_short_link_resolves_and_strips_watermark():
    short_url = "https://v.douyin.com/abc123/"
    video_id = "7123456789012345678"
    final_url = f"https://www.iesdouyin.com/share/video/{video_id}/?extra=1"
    playwm = (
        "https://v26-cold.douyinvod.com/abcdef/index.m3u8"
        "?signature=xx&playwm=1"
    )
    play_no_wm = (
        "https://v26-cold.douyinvod.com/abcdef/index.m3u8"
        "?signature=xx&play=1"
    )

    # 短链 302 → final_url；follow 时再请求一次 final_url，给 200 OK 即可
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": final_url},
    )
    responses.add(responses.HEAD, final_url, status=200)
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
    # webpage_url 应包含原 short_url（不重写）
    assert info["webpage_url"] == short_url
    # thumbnail 走代理
    assert info["thumbnail"] and info["thumbnail"].startswith("/api/thumbnail?url=")


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
    responses.add(responses.HEAD, final_url, status=200)
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
        assert "短链" in str(exc) or "video_id" in str(exc)
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


@responses.activate
def test_parse_video_api_missing_data_raises():
    responses.add(
        responses.GET,
        f"{DOUYIN_API_BASE}/api/video/info",
        json={"code": 0, "data": None},
        status=200,
    )
    try:
        parse_video("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "信息" in str(exc) or "无效" in str(exc)
    else:
        raise AssertionError("should raise")


# ─────────────────────────── download_video 流式下载（Task 3） ───────────────────────────

from pathlib import Path

import app.douyin_service as ds
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
    )

    # 跳过真实短链/真实 API，monkeypatch 模块函数
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
    statuses = [e["status"] for e in events]
    assert "downloading" in statuses
    assert "finished" in statuses


@responses.activate
def test_download_video_http_error_raises(tmp_path: Path):
    play_url = "https://v26-cold.douyinvod.com/abc/play/"
    responses.add(
        responses.GET,
        play_url,
        status=403,
        body="forbidden",
    )
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
        ds._resolve_video_id = orig_resolve
        ds._fetch_video_info = orig_fetch


@responses.activate
def test_download_video_missing_source_raises(tmp_path: Path):
    """上游返回没有 playwm_url 也没 play_url，应抛错。"""
    orig_resolve = ds._resolve_video_id
    orig_fetch = ds._fetch_video_info
    ds._resolve_video_id = lambda url: "7123456789012345678"
    ds._fetch_video_info = lambda vid: {
        "title": "dl",
        "cover": "",
        "duration": 1,
        "playwm_url": "",
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
            assert "视频源" in str(exc) or "无效" in str(exc)
        else:
            raise AssertionError("should raise")
    finally:
        ds._resolve_video_id = orig_resolve
        ds._fetch_video_info = orig_fetch


# ─────────────────────────── main.py URL 分流（Task 4） ───────────────────────────

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@responses.activate
def test_api_parse_douyin_short_routes_to_douyin_service():
    short_url = "https://v.douyin.com/abc/"
    video_id = "7123456789012345678"
    final_url = f"https://www.douyin.com/video/{video_id}"
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": final_url},
    )
    responses.add(responses.HEAD, final_url, status=200)
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
    final_url = f"https://www.douyin.com/video/{video_id}"
    responses.add(
        responses.HEAD,
        short_url,
        status=302,
        headers={"Location": final_url},
    )
    responses.add(responses.HEAD, final_url, status=200)
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


def test_api_parse_non_douyin_url_passes_through_to_ytdlp(monkeypatch):
    """非抖音 URL 走 ytdlp 链路；这里用 monkeypatch 替换 ytdlp_service.parse_video，
    避免真实网络请求（yt-dlp 在没网时会跑很久且结果不定）。"""
    import app.main as main_mod

    called = {"flag": False}

    def fake_parse_video(url):
        called["flag"] = True
        return {
            "title": "yt-dlp mocked",
            "thumbnail": None,
            "duration": 1,
            "extractor": "Generic",
            "uploader": None,
            "view_count": None,
            "description": None,
            "webpage_url": url,
            "presets": [],
            "formats": [],
            "choices": [],
        }

    monkeypatch.setattr(main_mod, "parse_video", fake_parse_video)

    r = client.post("/api/parse", json={"url": "https://www.youtube.com/watch?v=abc"})
    assert r.status_code == 200, r.text
    assert called["flag"] is True
    assert r.json()["extractor"] == "Generic"


# ─────────────────────────── live 烟雾测试（Task 5；默认 skip） ───────────────────────────

import os

import pytest


@pytest.mark.skipif(
    os.environ.get("DOUYIN_SMOKE") != "1",
    reason="set DOUYIN_SMOKE=1 to run live smoke test",
)
@pytest.mark.live
def test_parse_real_short_link_smoke():
    """真实短链 → 真实 API 拿一次。需 DOUYIN_SMOKE=1 + DOUYIN_SMOKE_URL。"""
    if not os.environ.get("DOUYIN_SMOKE_URL"):
        pytest.skip("set DOUYIN_SMOKE_URL to a real v.douyin.com short link")
    info = parse_video(os.environ["DOUYIN_SMOKE_URL"])
    assert info["title"]
    assert info["choices"][0]["id"] == "douyin-nowm"