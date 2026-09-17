"""main.py _public_error 错误信息本地化的单测。

不依赖网络；只测字符串映射。
"""
from __future__ import annotations

from app.main import _public_error


def test_public_error_unsupported_url_chinese():
    text = "Unsupported URL: https://example.com/abc"
    out = _public_error(RuntimeError(text))
    assert "yt-dlp" in out
    assert "YouTube" in out or "B 站" in out


def test_public_error_fresh_cookies_douyin_chinese():
    text = "[Douyin] 7659032704976981282: Fresh cookies (not necessarily logged in) are needed"
    out = _public_error(RuntimeError(text))
    assert "抖音" in out
    assert "cookie" in out.lower()
    assert "YTDLP_COOKIES_FROM_BROWSER" in out
    # 提到具体浏览器选项
    assert "chrome" in out or "brave" in out


def test_public_error_bili_412_chinese():
    text = "HTTP Error 412: Precondition Failed"
    out = _public_error(RuntimeError(text))
    assert "B 站" in out or "412" in out
    assert "YTDLP_COOKIES_FROM_BROWSER" in out


def test_public_error_youtube_bot_chinese():
    text = "ERROR: [youtube] YE7VzlLtp-4: Sign in to confirm you’re not a bot. Use --cookies-from-browser or --cookies"
    out = _public_error(RuntimeError(text))
    assert "YouTube" in out
    assert "cookie" in out.lower()
    assert "YTDLP_COOKIES_FROM_BROWSER" in out


def test_public_error_generic_truncates_long():
    text = "x" * 500
    out = _public_error(RuntimeError(text))
    assert len(out) <= 240


def test_public_error_empty_message_falls_back_to_class_name():
    out = _public_error(RuntimeError(""))
    assert out == "RuntimeError"