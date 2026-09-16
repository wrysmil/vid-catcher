import pytest

from app.urls import validate_http_url


def test_accepts_https_video_url():
    url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"
    assert validate_http_url(f"  {url}  ") == url


def test_rejects_empty():
    with pytest.raises(ValueError, match="请粘贴"):
        validate_http_url("   ")


def test_rejects_javascript_scheme():
    with pytest.raises(ValueError, match="http"):
        validate_http_url("javascript:alert(1)")


def test_rejects_whitespace_batch_in_one_field():
    with pytest.raises(ValueError, match="一条"):
        validate_http_url("https://a.com/x https://b.com/y")
