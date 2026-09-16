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