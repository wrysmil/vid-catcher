from __future__ import annotations

MAX_DURATION_SECONDS = 3 * 60 * 60
MAX_FORMAT_BYTES = int(1.5 * 1024 * 1024 * 1024)

PRESETS = [
    {"id": "bv*[vcodec^=avc1]+ba/b", "label": "最高清", "note": "自动合并音视频", "kind": "video"},
    {"id": "bv*[height<=1080][vcodec^=avc1]+ba/b", "label": "1080p", "note": "够用且更快", "kind": "video"},
    {"id": "bv*[height<=720][vcodec^=avc1]+ba/b", "label": "720p", "note": "省流量", "kind": "video"},
    {"id": "bestaudio/b", "label": "仅音频", "note": "适合听课", "kind": "audio"},
]


def slim_formats(raw_formats: list | None) -> list[dict]:
    if not raw_formats:
        return []
    seen: set[tuple] = set()
    slim: list[dict] = []
    for item in raw_formats:
        if not isinstance(item, dict):
            continue
        vcodec = item.get("vcodec") or "none"
        acodec = item.get("acodec") or "none"
        if vcodec == "none" and acodec == "none":
            continue
        kind = "audio" if vcodec == "none" else "video"
        height = item.get("height")
        ext = item.get("ext") or "mp4"
        format_id = item.get("format_id")
        if not format_id:
            continue
        filesize = item.get("filesize") or item.get("filesize_approx")
        if filesize and filesize > MAX_FORMAT_BYTES:
            continue
        key = (kind, height, ext)
        if key in seen:
            continue
        seen.add(key)
        has_audio = acodec != "none"
        slim.append(
            {
                "id": str(format_id),
                "label": _format_label(kind, height, ext),
                "note": item.get("format_note") or ext,
                "kind": kind,
                "ext": ext,
                "height": height,
                "filesize": filesize,
                "has_audio": has_audio,
                "title": _choice_title(kind, height, ext, has_audio, filesize),
                "subtitle": _choice_subtitle(kind, ext, has_audio),
            }
        )
        if len(slim) >= 12:
            break
    return slim


def quality_choices(raw_formats: list | None) -> list[dict]:
    slim = slim_formats(raw_formats)
    heights = [item["height"] for item in slim if item.get("kind") == "video" and item.get("height")]
    max_height = max(heights) if heights else None
    best_label = f"{max_height}p 最佳 (视频+音频合并)" if max_height else "最佳 (视频+音频合并)"
    cards = [
        {
            "id": "bv*[vcodec^=avc1]+ba/b",
            "label": best_label,
            "note": "MP4 · 含音频",
            "kind": "merged",
            "ext": "mp4",
            "height": max_height,
            "filesize": None,
            "has_audio": True,
            "title": best_label,
            "subtitle": "MP4 · 含音频",
        }
    ]
    if max_height and max_height > 720:
        cards.append(
            {
                "id": "bv*[height<=720][vcodec^=avc1]+ba/b",
                "label": "720p 最佳 (视频+音频合并)",
                "note": "MP4 · 含音频",
                "kind": "merged",
                "ext": "mp4",
                "height": 720,
                "filesize": None,
                "has_audio": True,
                "title": "720p 最佳 (视频+音频合并)",
                "subtitle": "MP4 · 含音频",
            }
        )
    for item in slim:
        if item["kind"] == "audio":
            continue
        cards.append(item)
        if len(cards) >= 7:
            break
    audio = next((item for item in slim if item["kind"] == "audio"), None)
    if audio:
        cards.append(audio)
    return cards


def _choice_title(kind: str, height: int | None, ext: str, has_audio: bool, filesize) -> str:
    ext_label = (ext or "mp4").upper()
    size = _pretty_size(filesize)
    if kind == "audio":
        return f"仅音频 ({ext_label}{f', {size}' if size else ''})"
    height_label = f"{height}p" if height else "视频"
    if has_audio:
        return f"{height_label} {ext_label} (含音频{f', {size}' if size else ''})"
    return f"{height_label} {ext_label} (仅视频{f', {size}' if size else ''})"


def _choice_subtitle(kind: str, ext: str, has_audio: bool) -> str:
    ext_label = (ext or "mp4").upper()
    if kind == "audio":
        return f"{ext_label} · 音频"
    return f"{ext_label} · {'含音频' if has_audio else '仅视频'}"


def _pretty_size(filesize) -> str | None:
    if not filesize:
        return None
    try:
        size = float(filesize)
    except (TypeError, ValueError):
        return None
    mb = size / 1_000_000
    if mb < 0.1:
        return f"{size / 1000:.0f}KB"
    return f"{mb:.1f}MB"


def _format_label(kind: str, height: int | None, ext: str) -> str:
    if kind == "audio":
        return f"音频 · {ext}"
    if height:
        return f"{height}p · {ext}"
    return f"视频 · {ext}"


def assert_duration_ok(duration) -> None:
    if duration is None:
        return
    try:
        seconds = float(duration)
    except (TypeError, ValueError):
        return
    if seconds > MAX_DURATION_SECONDS:
        raise ValueError("视频超过 3 小时，学习版先不接")
