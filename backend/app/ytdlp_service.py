from __future__ import annotations

import os
import re
from pathlib import Path

import requests
import yt_dlp

from .filenames import safe_filename
from .formats import PRESETS, assert_duration_ok, quality_choices, slim_formats

DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "tmp_downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _best_thumbnail(info: dict) -> str | None:
    """挑最大的封面并强制 HTTPS。B 站返回的 URL 多为 http://，
    HTTPS 页面下会被浏览器当 mixed content 拦掉，前端就直接回退成无图。"""
    candidates = list(info.get("thumbnails") or [])
    if info.get("thumbnail"):
        candidates.append({"url": info["thumbnail"]})

    def _area(t: dict) -> int:
        w = t.get("width") or 0
        h = t.get("height") or 0
        return w * h if (w and h) else 0

    candidates.sort(key=_area, reverse=True)
    for t in candidates:
        url = _normalize_thumb(t.get("url") or "")
        if url:
            return _proxy_thumb(url)
    return None


def _proxy_thumb(url: str) -> str:
    """把 CDN URL 换成同源代理路径，避免浏览器拿 127.0.0.1 Referer 被 B 站 CDN 拒。"""
    from urllib.parse import quote

    return f"/api/thumbnail?url={quote(url, safe='')}"


_BV_RE = re.compile(r"(BV[0-9A-Za-z]{2,})")
_TRANSPARENT = ("/transparent.png", "bfs/archive/transparent")


def _normalize_thumb(url: str) -> str | None:
    url = (url or "").strip()
    if not url:
        return None
    if url.endswith(_TRANSPARENT[0]) or _TRANSPARENT[1] in url:
        return None
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


def _bili_cover(bvid: str) -> str | None:
    """B 站 view 接口给的最权威 cover；yt-dlp 拿不到或只给 transparent 时用它兜底。"""
    try:
        r = requests.get(
            "https://api.bilibili.com/x/web-interface/view",
            params={"bvid": bvid},
            headers={"User-Agent": BROWSER_HEADERS["User-Agent"], "Referer": "https://www.bilibili.com/"},
            timeout=8,
        )
        data = (r.json() or {}).get("data") or {}
        url = _normalize_thumb(data.get("pic") or data.get("cover") or "")
        return _proxy_thumb(url) if url else None
    except Exception:
        return None

# Bilibili 412 常见原因：请求不像浏览器。只补公开请求头，不破解登录/大会员。
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": False,
        "overwrites": True,
        "noprogress": True,
        "http_headers": BROWSER_HEADERS,
    }
    cookie_file = os.environ.get("YTDLP_COOKIES")
    browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER")
    if cookie_file and Path(cookie_file).exists():
        opts["cookiefile"] = cookie_file
    elif browser:
        opts["cookiesfrombrowser"] = (browser.strip(),)
    return opts


def parse_video(url: str) -> dict:
    opts = {**_base_opts(), "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        raw = ydl.extract_info(url, download=False)
        info = ydl.sanitize_info(raw)

    if not info:
        raise ValueError("没有解析到视频信息")
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise ValueError("播放列表是空的，请贴单条视频")
        info = entries[0]

    assert_duration_ok(info.get("duration"))

    description = info.get("description") or ""
    if isinstance(description, str):
        description = " ".join(description.split())
        if len(description) > 160:
            description = description[:157] + "..."
    else:
        description = ""

    thumbnail = _best_thumbnail(info)
    if thumbnail is None and (info.get("extractor_key") or "").lower().startswith("bili"):
        m = _BV_RE.search(info.get("webpage_url") or url)
        if m:
            thumbnail = _bili_cover(m.group(1))

    return {
        "title": info.get("title") or "未命名视频",
        "thumbnail": thumbnail,
        "duration": info.get("duration"),
        "extractor": info.get("extractor_key") or info.get("extractor"),
        "uploader": info.get("uploader") or info.get("channel") or info.get("creator"),
        "view_count": info.get("view_count"),
        "description": description or None,
        "webpage_url": info.get("webpage_url") or url,
        "presets": PRESETS,
        "formats": slim_formats(info.get("formats")),
        "choices": quality_choices(info.get("formats")),
    }


def download_video(url: str, format_id: str, dest_dir: Path, progress_hook) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    # 中间名只求「能落盘」，最终名下载完再按标题重写（见 _rename_to_title）。
    # 不能开 restrictfilenames：它会把中文等非 ASCII 字符整个删掉，
    # 「测试视频」会变成空标题，文件名只剩 ".mp4"。
    outtmpl = str(dest_dir / "%(title).80s.%(ext)s")
    # 默认走 H.264 优先；avc1 没有时 /b 兜底到单文件最佳。
    fmt = (format_id or "").strip() or "bv*[vcodec^=avc1]+ba/b"
    opts = {
        **_base_opts(),
        "format": fmt,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise ValueError("下载失败")
        if info.get("_type") == "playlist":
            entries = [e for e in (info.get("entries") or []) if e]
            info = entries[0] if entries else info
        path = _resolve_output(ydl, info)
    return _rename_to_title(path, info)


def _resolve_output(ydl: yt_dlp.YoutubeDL, info: dict) -> Path:
    """定位 yt-dlp 实际写出的文件。

    merge_output_format 会把 "x.f137.mp4" 合并成 "x.mp4"，prepare_filename()
    给的还是合并前的名字，所以按三级兜底：原路径 -> 换 .mp4 -> 扫任务目录。
    """
    path = Path(ydl.prepare_filename(info))
    if path.exists():
        return path
    mp4 = path.with_suffix(".mp4")
    if mp4.exists():
        return mp4

    # 任务目录（tmp_downloads/<task_id>/）是本次下载独占的，里面只会有这一个产物。
    leftovers = [
        p
        for p in path.parent.iterdir()
        if p.is_file() and p.suffix not in {".part", ".ytdl", ".temp"}
    ]
    if leftovers:
        return max(leftovers, key=lambda p: p.stat().st_mtime)
    raise ValueError("文件写出失败，可能缺 ffmpeg")


def _rename_to_title(path: Path, info: dict) -> Path:
    """把中间名换成清洗后的标题名。目录独占，不需要防撞名。"""
    ext = path.suffix.lstrip(".") or "mp4"
    fallback = f"video_{info.get('id') or path.stem}"
    target = path.with_name(safe_filename(info.get("title"), fallback=fallback, ext=ext))
    if target != path:
        os.replace(path, target)
    return target
