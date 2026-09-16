from app.urls import validate_thumb_url
from app.ytdlp_service import _best_thumbnail


def test_thumbnail_forces_https_then_proxies():
    info = {"thumbnail": "http://i0.hdslb.com/bfs/archive/abc.jpg"}
    out = _best_thumbnail(info)
    assert out.startswith("/api/thumbnail?url=https%3A%2F%2F")


def test_thumbnail_picks_largest():
    info = {
        "thumbnail": "http://a/small.jpg",
        "thumbnails": [
            {"url": "http://a/small.jpg", "width": 160, "height": 90},
            {"url": "http://a/big.jpg", "width": 1920, "height": 1080},
            {"url": "http://a/med.jpg", "width": 640, "height": 360},
        ],
    }
    assert _best_thumbnail(info) == "/api/thumbnail?url=https%3A%2F%2Fa%2Fbig.jpg"


def test_thumbnail_skips_transparent_placeholder():
    info = {
        "thumbnail": "https://i0.hdslb.com/bfs/archive/transparent.png",
        "thumbnails": [
            {"url": "https://i0.hdslb.com/bfs/archive/transparent.png"},
            {"url": "http://i2.hdslb.com/bfs/archive/real.jpg", "width": 800, "height": 450},
        ],
    }
    assert _best_thumbnail(info) == "/api/thumbnail?url=https%3A%2F%2Fi2.hdslb.com%2Fbfs%2Farchive%2Freal.jpg"


def test_thumbnail_returns_none_when_empty():
    assert _best_thumbnail({}) is None
    assert _best_thumbnail({"thumbnail": ""}) is None


def test_validate_thumb_accepts_whitelist():
    validate_thumb_url("https://i2.hdslb.com/bfs/archive/abc.jpg")
    validate_thumb_url("https://i.ytimg.com/vi/abc/maxresdefault.jpg")


def test_validate_thumb_rejects_non_whitelist():
    import pytest

    with pytest.raises(ValueError, match="白名单"):
        validate_thumb_url("https://evil.example.com/x.jpg")