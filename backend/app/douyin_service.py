"""抖音视频解析与下载服务。

不走 yt-dlp；通过第三方公开 API（lieshouyin.com）反向分析。
流程：短链 302 解析 → 公开 API 拉取 → playwm → play 去水印 → 流式下载。

约定：
- 抖音域识别：is_douyin_url() 严格匹配 v.douyin.com / www.douyin.com / iesdouyin.com。
- 公开 API 默认 base_url 写在 DOUYIN_API_BASE 常量；不引入环境变量（一期）。
- 上游失败统一抛 DouyinUpstreamError，main.py 兜底中文提示，不静默 fallback。
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import requests


DOUYIN_API_BASE = "https://www.lieshouyin.com"
DOUYIN_VIDEO_ID_RE = re.compile(r"(?<!\d)(\d{18,19})(?!\d)")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


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
    """从长链里抽 18-19 位 video_id（modal_id / 路径段）。返回 None 表示没找到。"""
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


def _resolve_video_id(url: str) -> str:
    """短链：HEAD 跟 302 拿最终 URL 再 regex 提 ID；
    长链：直接 regex。
    失败抛 DouyinUpstreamError。"""
    if "v.douyin.com/" in url:
        try:
            r = requests.head(
                url,
                allow_redirects=True,
                timeout=8,
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
    """统一走 /api/thumbnail 代理，避免 mixed-content / referer 问题。
    不引入 urls 循环依赖，直接拼路径。"""
    from urllib.parse import quote

    cover = (cover or "").strip()
    if not cover.startswith("http"):
        return None
    return f"/api/thumbnail?url={quote(cover, safe='')}"


def parse_video(url: str) -> dict:
    video_id = _resolve_video_id(url)
    data = _fetch_video_info(video_id)
    title = ((data.get("title") or "未命名视频").strip()) or "未命名视频"
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
    }


def _make_progress_hook(hook):
    """节流版 progress hook：每 0.3s 派发一次 downloading + 终态 finished。
    当前 download_video 实现里直接派发，保留本函数为后续扩展。"""
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
    url: str,
    format_id: str,
    dest_dir: Path,
    progress_hook,
) -> Path:
    """解析 → 拿到无水印播放地址 → 流式下载到 dest_dir/douyin.mp4。
    返回最终文件路径。失败抛 DouyinUpstreamError。"""
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
            headers={
                "User-Agent": UA,
                "Referer": "https://www.douyin.com/",
            },
            timeout=30,
            stream=True,
        ) as r:
            if r.status_code >= 400:
                raise DouyinUpstreamError(
                    f"抖音源下载失败：HTTP {r.status_code}"
                )
            total = int(r.headers.get("Content-Length") or 0)
            downloaded = 0
            block_size = 64 * 1024
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=block_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
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