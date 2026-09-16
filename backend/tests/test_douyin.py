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