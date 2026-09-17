"""抖音视频解析/下载服务的单元测试（公开 API 方案版，对齐 free-video-downloader）。

单测始终跑；live 烟雾测试见 test_parse_real_short_link_smoke，需 DOUYIN_SMOKE=1。
"""
from __future__ import annotations

from app.douyin_service import (
    DouyinUpstreamError,
    build_choices,
    extract_video_id,
    extract_video_id_from_long_url,
    is_douyin_url,
    strip_watermark,
    DouyinParser,
)


# ─────────────────────────── 纯函数骨架 ───────────────────────────


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


def test_extract_video_id_basic():
    """路径中的视频 ID。"""
    vid = extract_video_id("https://www.douyin.com/video/7123456789012345678")
    assert vid == "7123456789012345678"


def test_extract_video_id_note():
    """note 路径。"""
    vid = extract_video_id("https://www.douyin.com/note/7123456789012345")
    assert vid == "7123456789012345"


def test_extract_video_id_query_modal_id():
    """query 参数 modal_id。"""
    vid = extract_video_id("https://www.douyin.com/jingxuan?modal_id=71234567")
    assert vid == "71234567"


def test_extract_video_id_query_item_ids():
    """query 参数 item_ids。"""
    vid = extract_video_id("https://www.douyin.com/discover?item_ids=71234567")
    assert vid == "71234567"


def test_extract_video_id_query_aweme_id():
    """query 参数 aweme_id。"""
    vid = extract_video_id("https://www.douyin.com/?aweme_id=71234567")
    assert vid == "71234567"


def test_extract_video_id_query_group_id():
    """query 参数 group_id。"""
    vid = extract_video_id("https://www.douyin.com/?group_id=71234567")
    assert vid == "71234567"


def test_extract_video_id_from_long_url_basic():
    """兼容旧 API。"""
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


# ─────────────────────────── DouyinParser 主流程 ───────────────────────────

import responses

from app.douyin_service import DOUYIN_API_URL, DouyinParser
from app.douyin_service import _fetch_via_api, _fetch_via_share_page


def test_parse_video_via_api(monkeypatch):
    """通过 API 成功解析。"""
    video_id = "7123456789012345678"

    # 直接 mock _fetch_via_api：返回「原始 item dict」（对齐开源项目方案）
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: {
            "aweme_id": vid,
            "desc": "测试视频",
            "author": {"nickname": "测试用户"},
            "statistics": {"play_count": 100, "digg_count": 50},
            "video": {
                "duration": 30000,
                "cover": {"url_list": ["https://p3.douyinpic.com/cover.jpg"]},
                "play_addr": {
                    "url_list": ["https://v26-cold.douyinvod.com/abcdef/index.m3u8?playwm=1"]
                },
            },
        },
    )

    parser = DouyinParser()
    info = parser.parse(f"https://www.douyin.com/video/{video_id}")

    assert info["title"] == "测试视频"
    assert info["duration"] == 30
    assert info["extractor"] == "Douyin (公开 API)"
    assert info["choices"][0]["id"] == "douyin-nowm"
    assert info["webpage_url"] == f"https://www.douyin.com/video/{video_id}"
    assert info["thumbnail"] is not None
    assert info["thumbnail"].startswith("/api/thumbnail?url=")


def test_parse_video_long_url(monkeypatch):
    """长链直接提取 ID，不走短链跟随。"""
    video_id = "7123456789012345"

    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: {
            "aweme_id": vid,
            "desc": "长链测试",
            "author": {},
            "video": {
                "duration": 15000,
                "play_addr": {"url_list": ["https://example.com/video.mp4"]},
            },
        },
    )

    parser = DouyinParser()
    info = parser.parse(f"https://www.douyin.com/video/{video_id}")
    assert info["title"] == "长链测试"
    assert info["duration"] == 15


def test_parse_video_short_link(monkeypatch):
    """短链需要 HEAD 跟随。"""
    video_id = "7123456789012345678"

    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: {
            "aweme_id": vid,
            "desc": "短链测试",
            "author": {},
            "video": {
                "duration": 20000,
                "play_addr": {"url_list": ["https://example.com/video.mp4"]},
            },
        },
    )

    # 短链重定向需要 mock，避免真实网络请求
    monkeypatch.setattr(
        "app.douyin_service.DouyinParser._resolve_redirect",
        lambda self, url: f"https://www.douyin.com/video/{video_id}",
    )

    parser = DouyinParser()
    info = parser.parse(f"https://v.douyin.com/abc123/")
    assert info["title"] == "短链测试"
    assert info["webpage_url"] == "https://v.douyin.com/abc123/"


def test_parse_video_api_error_raises(monkeypatch):
    """API 返回错误码。"""
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: None,  # API 失败
    )
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_share_page",
        lambda vid: None,  # 分享页也失败
    )

    from app.douyin_service import DouyinUpstreamError

    parser = DouyinParser()
    try:
        parser.parse("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "无法获取视频信息" in str(exc)
    else:
        raise AssertionError("should raise")


def test_parse_video_http_500_raises(monkeypatch):
    """API 返回 500。"""
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: None,
    )
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_share_page",
        lambda vid: None,
    )

    from app.douyin_service import DouyinUpstreamError

    parser = DouyinParser()
    try:
        parser.parse("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "无法获取视频信息" in str(exc)
    else:
        raise AssertionError("should raise")


def test_parse_video_no_video_url_raises(monkeypatch):
    """API 返回成功但没有视频 URL。"""
    monkeypatch.setattr(
        "app.douyin_service._fetch_via_api",
        lambda vid: {
            "aweme_id": vid,
            "desc": "无URL",
            "author": {},
            "video": {},  # 没有 play_addr
        },
    )

    from app.douyin_service import DouyinUpstreamError

    parser = DouyinParser()
    try:
        parser.parse("https://www.douyin.com/video/7123456789012345678")
    except DouyinUpstreamError as exc:
        assert "无法获取视频信息" in str(exc)
    else:
        raise AssertionError("should raise")


# ─────────────────────────── download_video 流式下载 ───────────────────────────

from pathlib import Path

import app.douyin_service as ds
from app.douyin_service import download_video


@responses.activate
def test_download_video_streams_to_file_and_invokes_hook(tmp_path: Path):
    """下载成功：原子写入 .part 文件后替换。"""
    play_url = "https://v26-cold.douyinvod.com/abc/play/"
    body = b"FAKE_MP4_BYTES_" * 1000  # ~16KB

    responses.add(
        responses.GET,
        play_url,
        status=200,
        body=body,
        headers={"Content-Length": str(len(body))},
    )

    # Mock _download_with_atomic_write 直接下载
    orig_download = ds._download_with_atomic_write
    ds._download_with_atomic_write = lambda url, dest, hook, referer=None, filename="douyin.mp4": orig_download(
        url, dest, hook, referer, filename
    )

    # Mock parse 返回 play_url
    orig_parse = ds._get_parser().parse
    ds._get_parser().parse = lambda url: {
        "title": "dl",
        "play_url": play_url,
        "thumbnail": None,
        "duration": 1,
        "extractor": "Douyin (自研解析)",
        "uploader": None,
        "view_count": None,
        "description": None,
        "webpage_url": url,
        "presets": [],
        "formats": [],
        "choices": build_choices(),
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
        ds._download_with_atomic_write = orig_download
        ds._get_parser().parse = orig_parse

    assert path.exists()
    assert path.read_bytes() == body
    # 文件名取自解析出的标题，而不是写死的 douyin.mp4
    assert path.name == "dl.mp4"
    statuses = [e["status"] for e in events]
    assert "downloading" in statuses
    assert "finished" in statuses


@responses.activate
def test_download_video_http_error_raises(tmp_path: Path):
    """下载返回 403。"""
    play_url = "https://v26-cold.douyinvod.com/abc/play/"
    responses.add(
        responses.GET,
        play_url,
        status=403,
        body="forbidden",
    )

    orig_parse = ds._get_parser().parse
    ds._get_parser().parse = lambda url: {
        "title": "dl",
        "play_url": play_url,
        "thumbnail": None,
        "duration": 1,
        "extractor": "Douyin (自研解析)",
        "uploader": None,
        "view_count": None,
        "description": None,
        "webpage_url": url,
        "presets": [],
        "formats": [],
        "choices": build_choices(),
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
        ds._get_parser().parse = orig_parse


@responses.activate
def test_download_video_missing_source_raises(tmp_path: Path):
    """解析返回无 play_url。"""
    orig_parse = ds._get_parser().parse
    ds._get_parser().parse = lambda url: {
        "title": "dl",
        "play_url": "",  # 空 URL
        "thumbnail": None,
        "duration": 1,
        "extractor": "Douyin (自研解析)",
        "uploader": None,
        "view_count": None,
        "description": None,
        "webpage_url": url,
        "presets": [],
        "formats": [],
        "choices": build_choices(),
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
            assert "无播放地址" in str(exc) or "视频源" in str(exc)
        else:
            raise AssertionError("should raise")
    finally:
        ds._get_parser().parse = orig_parse


# ─────────────────────────── main.py URL 分流 ───────────────────────────

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_parse_douyin_url_uses_douyin_service(monkeypatch):
    """2026-09-17 决策调整：抖音 URL 走自研 douyin_service，不再走 yt-dlp。
    这里 monkeypatch 替换 douyin_service.parse_video，避免真实网络请求。"""
    import app.main as main_mod

    called = {"flag": False}

    def fake_douyin_parse(url):
        called["flag"] = True
        return {
            "title": "douyin mocked",
            "thumbnail": None,
            "duration": 1,
            "extractor": "Douyin (自研解析)",
            "uploader": None,
            "view_count": None,
            "description": None,
            "webpage_url": url,
            "presets": [],
            "formats": [],
            "choices": [],
        }

    monkeypatch.setattr(main_mod, "douyin_parse", fake_douyin_parse)

    r = client.post(
        "/api/parse",
        json={"url": "https://www.douyin.com/jingxuan?modal_id=7668494715314097418"},
    )
    assert r.status_code == 200, r.text
    assert called["flag"] is True
    assert r.json()["extractor"] == "Douyin (自研解析)"


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


# ─────────────────────────── live 烟雾测试（默认 skip） ───────────────────────────

import os

import pytest

from app.douyin_service import parse_video


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


# ─────────────────────────── WAF 挑战相关 ───────────────────────────

import hashlib
import json

from app.douyin_service import (
    _check_waf_challenge,
    _solve_waf_challenge,
    _extract_router_data,
)


def test_check_waf_challenge_detects():
    """检测 WAF 挑战。"""
    html = '<div wci="abc123" cs="cHJlZml4fGhhc2g=">challenge</div>'
    wci, cs = _check_waf_challenge(html)
    assert wci == "abc123"
    assert cs == "cHJlZml4fGhhc2g="


def test_check_waf_challenge_none():
    """无 WAF 挑战。"""
    html = '<div>normal content</div>'
    wci, cs = _check_waf_challenge(html)
    assert wci is None
    assert cs is None


def test_solve_waf_challenge():
    """WAF 挑战解决：返回可种 cookie 的值（含 d=solution）。

    挑战格式对齐开源项目：cs 是 base64 的 JSON
    {"v": {"a": <b64 prefix>, "c": <b64 hash 字节>}}。
    """
    import base64
    prefix = b"test_prefix"
    target = 12345
    expected = hashlib.sha256(prefix + str(target).encode()).hexdigest()
    challenge = {
        "v": {
            "a": base64.b64encode(prefix).decode(),
            "c": base64.b64encode(bytes.fromhex(expected)).decode(),
        }
    }
    cs = base64.b64encode(json.dumps(challenge).encode()).decode()

    cookie_val = _solve_waf_challenge("wci123", cs)
    assert cookie_val is not None
    data = json.loads(base64.b64decode(cookie_val).decode())
    assert base64.b64decode(data["d"]).decode() == str(target)


def test_solve_waf_challenge_bad_cs_returns_none():
    """无法解析的挑战返回 None。"""
    assert _solve_waf_challenge("wci123", "not-base64!") is None
    assert _solve_waf_challenge("wci123", "cGxlYXNl") is None  # 合法 b64 但非 JSON


def test_extract_router_data():
    """提取 _ROUTER_DATA。"""
    # 构造一个简单的 JSON
    data = {"video": {"title": "测试", "url": "https://example.com/video.mp4"}}
    json_str = json.dumps(data, ensure_ascii=False)

    # 构造 HTML
    html = f'<script>window._ROUTER_DATA = {json_str};</script>'

    result = _extract_router_data(html)
    assert result is not None
    assert result["video"]["title"] == "测试"


def test_extract_router_data_invalid():
    """无效的 _ROUTER_DATA。"""
    html = '<div>no router data here</div>'
    result = _extract_router_data(html)
    assert result is None


# ─────────────────────────── 分享页两次请求预热 ───────────────────────────

from app.douyin_service import _fetch_via_share_page


@responses.activate
def test_fetch_via_share_page_warms_ttwid_then_succeeds():
    """抖音分享页首次只返回外壳（无 videoInfoRes），第二次才有数据。

    回归：旧实现只请求一次，永远拿不到 videoInfoRes。
    """
    item = {
        "aweme_id": "7663892095949737225",
        "desc": "狂飙解析",
        "video": {"play_addr": {"url_list": ["https://v/playwm/1"]}},
    }
    shell = (
        '<html><script>window._ROUTER_DATA = '
        '{"loaderData":{"video_(id)/page":{"renderInSSR":1}}};</script></html>'
    )
    full = (
        '<html><script>window._ROUTER_DATA = '
        + json.dumps({"loaderData": {"video_(id)/page": {"videoInfoRes": {"item_list": [item]}}}})
        + ";</script></html>"
    )
    url = "https://www.iesdouyin.com/share/video/7663892095949737225/"
    responses.add(responses.GET, url, body=shell, status=200)
    responses.add(responses.GET, url, body=full, status=200)

    out = _fetch_via_share_page("7663892095949737225")
    assert out is not None
    assert out["desc"] == "狂飙解析"


@responses.activate
def test_fetch_via_share_page_all_shells_returns_none():
    """两次都只有外壳则返回 None。"""
    shell = (
        '<html><script>window._ROUTER_DATA = '
        '{"loaderData":{"video_(id)/page":{"renderInSSR":1}}};</script></html>'
    )
    url = "https://www.iesdouyin.com/share/video/1234567890123456789/"
    responses.add(responses.GET, url, body=shell, status=200)
    responses.add(responses.GET, url, body=shell, status=200)

    assert _fetch_via_share_page("1234567890123456789") is None
