"""main.py URL 归一化辅助函数的单测。

不依赖网络 / yt-dlp；只测纯字符串处理。
"""
from __future__ import annotations

from app.main import _normalize_douyin_url


def test_normalize_jingxuan_with_modal_id_to_video_path():
    src = "https://www.douyin.com/jingxuan?modal_id=7659032704976981282"
    out = _normalize_douyin_url(src)
    assert out == "https://www.douyin.com/video/7659032704976981282"


def test_normalize_jingxuan_www_douyin_com():
    src = "https://www.douyin.com/jingxuan?modal_id=1234567890123456789&extra=1"
    out = _normalize_douyin_url(src)
    # query 全部清空，只保留 path
    assert out == "https://www.douyin.com/video/1234567890123456789"


def test_normalize_jingxuan_no_modal_id_unchanged():
    src = "https://www.douyin.com/jingxuan"
    assert _normalize_douyin_url(src) == src


def test_normalize_jingxuan_empty_modal_id_unchanged():
    src = "https://www.douyin.com/jingxuan?modal_id="
    assert _normalize_douyin_url(src) == src


def test_normalize_non_douyin_host_unchanged():
    src = "https://www.youtube.com/jingxuan?modal_id=1234567890123456789"
    assert _normalize_douyin_url(src) == src


def test_normalize_non_jingxuan_path_unchanged():
    src = "https://www.douyin.com/video/7659032704976981282"
    assert _normalize_douyin_url(src) == src


def test_normalize_short_link_unchanged():
    src = "https://v.douyin.com/abc123/"
    assert _normalize_douyin_url(src) == src


def test_normalize_iesdouyin_jingxuan_unchanged():
    """iesdouyin 域的 jingxuan 不归一化（避免误改其他平台的格式）。"""
    src = "https://www.iesdouyin.com/jingxuan?modal_id=1234567890123456789"
    # 严格匹配 douyin.com 才归一化；iesdouyin 不动
    assert _normalize_douyin_url(src) == src