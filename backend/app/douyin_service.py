"""抖音视频解析与下载服务。

方案对齐 free-video-downloader 开源项目（基于公开 API，无需 Cookie 和登录）：
短链/分享文本提取 URL -> GET 跟随重定向 -> 提取 video_id
  -> 官方公开 API（iesdouyin iteminfo）拿「原始 item」-> 读 video.play_addr.url_list 去水印
  -> 失败走分享页 HTML 解析，遇到 WAF SHA-256 挑战时用 cookie 解题重试。

关键点（与旧实现的不同）：
- API / 分享页返回的都是「原始 item dict」，直接读 `desc / author / statistics /
  video.play_addr.url_list / video.cover.url_list` 等 snake_case 字段，不再自造字段映射。
- WAF 挑战格式：cs 是 base64 的 JSON `{"v":{"a":<b64 prefix>,"c":<b64 hash>}}`，
  解出 candidate 后把 `d=<b64 candidate>` 写回并整体 base64 作为**同名 cookie** 提交重试，
  而不是走 query 参数。
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from .filenames import safe_filename
from .formats import PRESETS
from .urls import validate_http_url

logger = logging.getLogger("douyin")

# ─────────────────────────── 常量 ───────────────────────────

# 公开 API（iesdouyin 官方）
DOUYIN_API_URL = "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/"
# 分享页 URL（可能触发 WAF）
DOUYIN_SHARE_URL_TEMPLATE = "https://www.iesdouyin.com/share/video/{video_id}/"

# 桌面 UA
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://www.douyin.com/",
}

# 手机 UA（分享页用，规避部分风控）
MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.douyin.com/",
}

# WAF 挑战搜索空间上限（通常 1-10s 命中）
WAF_SEARCH_MAX = 1_000_000
# 重试次数上限（含首次）
MAX_RETRIES = 3
# 重试退避基数（秒）
RETRY_BASE_DELAY = 1.0
# 请求超时（连接, 读取）
TIMEOUT = (10, 30)

# 视频 ID 长度范围（8-24 位数字）
VIDEO_ID_MIN_LEN = 8
VIDEO_ID_MAX_LEN = 24

# ─────────────────────────── 正则 ───────────────────────────

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)

# 匹配路径中的视频 ID：/video/(\d+)、/note/(\d+)
_PATH_VIDEO_ID_RE = re.compile(r"/(?:video|note)/(\d{%d,%d})" % (VIDEO_ID_MIN_LEN, VIDEO_ID_MAX_LEN))

# 匹配 query string 中的视频 ID 参数
_QUERY_VIDEO_ID_RE = re.compile(r"(?:modal_id|item_ids|group_id|aweme_id)=(\d{%d,%d})" % (VIDEO_ID_MIN_LEN, VIDEO_ID_MAX_LEN))

# 独立视频 ID（长数字串）
STANDALONE_VIDEO_ID_RE = re.compile(r"(?<!\d)(\d{%d,%d})(?!\d)" % (VIDEO_ID_MIN_LEN, VIDEO_ID_MAX_LEN))

# WAF 挑战正则
_WCI_RE = re.compile(r'wci="([^"]+)"')
_CS_RE = re.compile(r'cs="([^"]+)"')

# 提取 window._ROUTER_DATA = {...}
_ROUTER_DATA_RE = re.compile(r"window\._ROUTER_DATA\s*=\s*")


class DouyinUpstreamError(Exception):
    """抖音解析上游失败。"""


# ─────────────────────────── URL 识别 ───────────────────────────

def is_douyin_url(url: str) -> bool:
    """判断是否为抖音域名 URL。"""
    if not url:
        return False
    lowered = url.lower()
    return any(
        host in lowered
        for host in ("douyin.com", "iesdouyin.com")
    )


def _extract_url(text: str) -> str:
    """从分享文本/链接中提取第一条 URL。"""
    match = _URL_RE.search(text)
    if not match:
        raise ValueError("未找到有效的抖音链接")
    candidate = match.group(0).strip().strip('"').strip("'")
    return candidate.rstrip(").,;!?")


def extract_video_id(url: str) -> str | None:
    """从 URL 中提取视频 ID。

    支持的 URL 格式：
    - https://v.douyin.com/abc123/（短链，需先跟随重定向）
    - https://www.douyin.com/video/7123456789012345678
    - https://www.iesdouyin.com/share/video/7123456789012345678/?extra=1
    - https://www.douyin.com/jingxuan?modal_id=7123456789012345678
    - https://www.douyin.com/discover?item_ids=7123456789012345678
    - https://www.douyin.com/note/7123456789012345678

    返回 None 表示没找到。
    """
    if not url:
        return None

    # 1. 优先从路径中提取（最准确）
    m = _PATH_VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)

    # 2. 从 query string 中提取
    m = _QUERY_VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)

    # 3. 独立视频 ID（在路径末尾等）
    m = STANDALONE_VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)

    return None


# ─────────────────────────── 去水印 ───────────────────────────

def strip_watermark(play_url: str) -> str:
    """playwm -> play；幂等；无 wm 原样返回。"""
    if not play_url:
        return play_url
    return play_url.replace("playwm", "play")


# ─────────────────────────── WAF 挑战解决 ───────────────────────────

def _decode_b64(value: str) -> bytes:
    """URL-safe base64 解码（自动补齐 padding）。"""
    normalized = value.replace("-", "+").replace("_", "/")
    normalized += "=" * (-len(normalized) % 4)
    return base64.b64decode(normalized)


def _check_waf_challenge(html: str) -> tuple[str | None, str | None]:
    """检查 HTML 是否包含 WAF 挑战。

    Returns:
        (wci, cs) 元组，如果无挑战则返回 (None, None)。
    """
    wci_m = _WCI_RE.search(html)
    cs_m = _CS_RE.search(html)

    if not wci_m or not cs_m:
        return None, None

    return wci_m.group(1), cs_m.group(1)


def _solve_waf_challenge(wci: str, cs: str) -> str | None:
    """解决抖音 WAF SHA-256 挑战，返回要种到 cookie 的值。

    挑战格式：cs 是 base64 的 JSON，形如
    {"v": {"a": <base64 prefix>, "c": <base64 hash字节>}}。
    需要暴力搜索 candidate，使 SHA256(prefix + str(candidate)) == hash，然后把
    candidate 以 base64 写回 challenge["d"]，整体再 base64 作为 cookie 值。

    Args:
        wci: cookie 名（HTML 中的 wci 值）
        cs: base64 编码的挑战数据

    Returns:
        可种入 `wci` cookie 的值；失败返回 None。
    """
    try:
        decoded = _decode_b64(cs).decode("utf-8")
        challenge_data = json.loads(decoded)
        prefix = _decode_b64(challenge_data["v"]["a"])
        expected = _decode_b64(challenge_data["v"]["c"]).hex()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    for candidate in range(WAF_SEARCH_MAX + 1):
        digest = hashlib.sha256(prefix + str(candidate).encode()).hexdigest()
        if digest == expected:
            challenge_data["d"] = base64.b64encode(str(candidate).encode()).decode()
            return base64.b64encode(
                json.dumps(challenge_data, separators=(",", ":")).encode()
            ).decode()

    return None


# ─────────────────────────── JSON 提取 ───────────────────────────

def _extract_router_data(html: str) -> dict | None:
    """从 HTML 中提取 window._ROUTER_DATA JSON。

    使用手写大括号深度匹配，而非正则（避免嵌套问题）。

    Returns:
        解析后的 dict，失败返回 None。
    """
    match = _ROUTER_DATA_RE.search(html)
    if not match:
        return None

    json_str, ok = _extract_json_by_braces(html, match.end())
    if not ok:
        return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def _extract_json_by_braces(text: str, start: int) -> tuple[str, bool]:
    """从 start 位置开始，匹配大括号提取完整 JSON 字符串。"""
    # 跳过空白
    while start < len(text) and text[start] in " \t\n\r":
        start += 1

    if start >= len(text) or text[start] != "{":
        return "", False

    depth = 0
    in_string = False
    escape = False
    json_start = start

    for i in range(start, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            if in_string:
                escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[json_start : i + 1], True

    return "", False


def _find_raw_item(node: Any) -> dict | None:
    """在 _ROUTER_DATA 中递归找「原始 item」：含 video.play_addr.url_list 的 dict。

    API 与分享页共用同一种原始 item 结构，找到即可统一走 _build_result。
    """
    if isinstance(node, dict):
        video = node.get("video")
        if isinstance(video, dict):
            play_addr = video.get("play_addr")
            if isinstance(play_addr, dict) and play_addr.get("url_list"):
                return node
        for value in node.values():
            found = _find_raw_item(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_raw_item(item)
            if found:
                return found
    return None


# ─────────────────────────── API 请求 ───────────────────────────

def _fetch_via_api(video_id: str) -> dict | None:
    """通过官方公开 API 获取「原始 item dict」。

    API: https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}

    注意：该接口近期返回 status_code=11110(encrypt_data)，需要加密签名才能用，
    正常情况会快速落空并回退到分享页；非 0 状态码不再重试。

    Returns:
        原始 item dict，失败返回 None。
    """
    params = {"item_ids": video_id}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(
                DOUYIN_API_URL,
                params=params,
                headers={
                    "User-Agent": UA,
                    "Referer": f"https://www.iesdouyin.com/share/video/{video_id}/",
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                continue
            return None

        if r.status_code != 200:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                continue
            return None

        try:
            payload = r.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            items = payload.get("item_list") or []
            if items:
                return items[0]
            # status_code != 0（如 11110 需要加密签名）说明接口已不可用，立即放弃
            if payload.get("status_code") not in (0, None):
                return None

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_BASE_DELAY * (2 ** attempt))

    return None


def _extract_item_from_html(html: str) -> dict | None:
    """从分享页 HTML 中提取「原始 item dict」。

    优先标准节点 loaderData.*.videoInfoRes.item_list[0]，兜底递归找含
    video.play_addr.url_list 的原始 item。
    """
    router_data = _extract_router_data(html)
    if not router_data:
        return None

    loader_data = router_data.get("loaderData", {})
    if isinstance(loader_data, dict):
        for node in loader_data.values():
            if not isinstance(node, dict):
                continue
            video_info_res = node.get("videoInfoRes")
            if not isinstance(video_info_res, dict):
                continue
            item_list = video_info_res.get("item_list") or []
            if item_list and isinstance(item_list[0], dict):
                return item_list[0]

    return _find_raw_item(router_data)


# 分享页复用同一个 session：抖音首次请求只返回页面外壳并下发 ttwid cookie，
# 带着该 cookie 的第二次请求才会把 videoInfoRes 渲染进 HTML。持久 session
# 让 cookie 在多次解析间复用（与开源项目保持一致）。
_share_session: requests.Session | None = None


def _get_share_session() -> requests.Session:
    global _share_session
    if _share_session is None:
        _share_session = requests.Session()
        _share_session.headers.update(MOBILE_HEADERS)
    return _share_session


def _fetch_via_share_page(video_id: str) -> dict | None:
    """通过分享页 HTML 解析获取「原始 item dict」。

    最多请求两次：第一次通常只拿到外壳（顺带下发 ttwid），第二次带 cookie
    才能拿到 videoInfoRes。遇到 WAF 挑战时解题并以 cookie 提交后重试。

    Returns:
        原始 item dict，失败返回 None。
    """
    share_url = DOUYIN_SHARE_URL_TEMPLATE.format(video_id=video_id)
    session = _get_share_session()

    for _ in range(2):
        try:
            r = session.get(share_url, timeout=TIMEOUT)
        except requests.RequestException:
            return None

        if r.status_code != 200:
            return None

        html = r.text or ""

        # WAF 挑战：解题后以 cookie 提交并重试
        wci, cs = _check_waf_challenge(html)
        if wci and cs:
            cookie_val = _solve_waf_challenge(wci, cs)
            if cookie_val:
                domain = urlparse(share_url).hostname or "www.iesdouyin.com"
                session.cookies.set(wci, cookie_val, domain=domain, path="/")
                try:
                    r = session.get(share_url, timeout=TIMEOUT)
                    if r.status_code == 200:
                        html = r.text or ""
                except requests.RequestException:
                    return None

        item = _extract_item_from_html(html)
        if item:
            return item
        # 首次可能只是外壳，带 ttwid 再请求一次

    return None


# ─────────────────────────── 原始 item -> 结果 ───────────────────────────

def _extract_media_url(item_info: dict, mode: str = "video") -> str | None:
    """从原始 item 提取无水印播放地址。"""
    video = item_info.get("video", {}) or {}

    if mode == "video":
        play_addrs = (video.get("play_addr", {}) or {}).get("url_list") or []
        for addr in play_addrs:
            if isinstance(addr, str) and addr.startswith("http"):
                return strip_watermark(addr)
        return None

    if mode == "audio":
        music = item_info.get("music", {}) or {}
        audio_urls = (music.get("play_url", {}) or {}).get("url_list") or []
        for addr in audio_urls:
            if isinstance(addr, str) and addr.startswith("http"):
                return addr
        return None

    return None


def _proxy_thumb(url: str | None) -> str | None:
    """统一走 /api/thumbnail 代理，避免 mixed-content / referer 问题。"""
    from urllib.parse import quote

    url = (url or "").strip()
    if not url:
        return None
    if not url.startswith("http"):
        return None
    return f"/api/thumbnail?url={quote(url, safe='')}"


def _build_result(item_info: dict, video_id: str, original_url: str) -> dict[str, Any]:
    """把原始 item 转成与 yt-dlp 解析结果兼容的统一格式。"""
    title = (item_info.get("desc") or "").strip() or f"抖音视频_{video_id}"
    author = item_info.get("author", {}) or {}
    stats = item_info.get("statistics", {}) or {}
    video = item_info.get("video", {}) or {}

    duration_ms = video.get("duration") or 0
    duration = duration_ms // 1000 if duration_ms > 1000 else (duration_ms or None)

    covers = (video.get("cover", {}) or {}).get("url_list") or []
    cover_url = covers[0] if covers and covers[0].startswith("http") else None

    play_url = _extract_media_url(item_info, "video")

    return {
        "title": title[:100],
        "thumbnail": _proxy_thumb(cover_url) if cover_url else None,
        "duration": duration,
        "extractor": "Douyin (公开 API)",
        "uploader": author.get("nickname"),
        "view_count": stats.get("play_count") or stats.get("digg_count"),
        "description": title[:200] or None,
        "webpage_url": original_url,
        # 内部使用：直接下载 URL
        "play_url": play_url,
        "aweme_id": item_info.get("aweme_id") or video_id,
        # 兼容格式（抖音只有单一选择）
        "presets": PRESETS,
        "formats": [],
        "choices": build_choices(),
    }


# ─────────────────────────── 主解析器 ───────────────────────────

class DouyinParser:
    """抖音视频解析器（方案对齐 free-video-downloader）。

    流程：提取 URL -> 跟随重定向 -> 提取 video_id
        -> 官方 API 拿原始 item -> 去水印 play_addr
        -> 失败走分享页 HTML（含 WAF cookie 挑战）。

    Usage:
        parser = DouyinParser()
        info = parser.parse("https://v.douyin.com/abc123/")
        parser.download(url, "douyin-nowm", dest_dir, progress_hook)
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    def parse(self, url: str) -> dict[str, Any]:
        """解析抖音视频 URL。

        Args:
            url: 抖音视频 URL 或包含链接的分享文本

        Returns:
            与 yt-dlp 兼容的视频信息 dict

        Raises:
            DouyinUpstreamError: 解析失败
        """
        # 1. 提取 URL 并跟随重定向
        try:
            share_url = _extract_url(url)
            final_url = self._resolve_redirect(share_url)
        except ValueError as exc:
            raise DouyinUpstreamError(str(exc)) from exc
        except requests.RequestException as exc:
            raise DouyinUpstreamError(f"链接解析失败：{exc.__class__.__name__}") from exc

        # 2. 提取 video_id
        video_id = extract_video_id(final_url)
        if not video_id:
            raise DouyinUpstreamError("无法从链接中提取视频ID，链接可能无效或已过期")

        # 3. 拿原始 item（API 优先，失败走分享页）
        item_info = self._fetch_item_info(video_id)

        # 4. 构建结果
        result = _build_result(item_info, video_id, url)
        if not result.get("play_url"):
            raise DouyinUpstreamError("无法获取视频信息，可能链接已失效或需要登录")

        return result

    def download(
        self,
        url: str,
        format_id: str,
        dest_dir: Path,
        progress_hook,
    ) -> Path:
        """下载抖音视频。

        Args:
            url: 抖音视频 URL
            format_id: 格式 ID（仅 douyin-nowm 有效）
            dest_dir: 下载目录
            progress_hook: 进度回调

        Returns:
            下载完成的文件路径
        """
        info = self.parse(url)
        play_url = info.get("play_url")
        if not play_url:
            raise DouyinUpstreamError("无播放地址")

        filename = safe_filename(
            info.get("title"),
            fallback=f"douyin_{info.get('aweme_id') or 'video'}",
            ext="mp4",
        )
        return _download_with_atomic_write(
            play_url,
            dest_dir,
            progress_hook,
            referer="https://www.douyin.com/",
            filename=filename,
        )

    # ─── 内部方法 ───

    def _resolve_redirect(self, share_url: str) -> str:
        """GET 跟随重定向（短链 v.douyin.com -> 真实视频页）。"""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.get(
                    share_url,
                    timeout=TIMEOUT,
                    allow_redirects=True,
                    headers=DEFAULT_HEADERS,
                )
                resp.raise_for_status()
                return resp.url or share_url
            except requests.RequestException:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
        raise DouyinUpstreamError("链接解析失败")

    def _fetch_item_info(self, video_id: str) -> dict:
        """获取原始 item，API 优先，失败走分享页。"""
        try:
            item = _fetch_via_api(video_id)
            if item:
                return item
        except Exception as exc:
            logger.warning("公开 API 获取失败(%s)，尝试分享页解析", exc)

        item = _fetch_via_share_page(video_id)
        if item:
            return item

        raise DouyinUpstreamError("无法获取视频信息，可能链接已失效或需要登录")


# ─────────────────────────── 下载 ───────────────────────────

def _download_with_atomic_write(
    url: str,
    dest_dir: Path,
    progress_hook,
    referer: str | None = None,
    filename: str = "douyin.mp4",
) -> Path:
    """原子写入下载：先写 .part 文件，下载完成后原子替换。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / filename
    part_path = out_path.with_name(out_path.name + ".part")

    headers: dict[str, str] = {
        "User-Agent": UA,
    }
    if referer:
        headers["Referer"] = referer

    try:
        with requests.get(
            url,
            headers=headers,
            timeout=30,
            stream=True,
        ) as r:
            if r.status_code >= 400:
                raise DouyinUpstreamError(
                    f"视频源下载失败：HTTP {r.status_code}"
                )

            total = int(r.headers.get("Content-Length") or 0)
            downloaded = 0
            block_size = 64 * 1024

            with open(part_path, "wb") as f:
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

        # 原子替换
        if part_path.exists():
            part_path.replace(out_path)

        progress_hook({"status": "finished"})

    except requests.RequestException as exc:
        # 清理 .part 文件
        if part_path.exists():
            part_path.unlink()
        raise DouyinUpstreamError(
            f"下载中断：{exc.__class__.__name__}"
        ) from exc

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise DouyinUpstreamError("下载完成但文件为空")

    return out_path


# ─────────────────────────── 兼容函数（原有 API） ───────────────────────────

def build_choices() -> list[dict[str, Any]]:
    """抖音只有一个公开选择：无水印视频（含音频）。"""
    return [
        {
            "id": "douyin-nowm",
            "label": "无水印视频",
            "note": "MP4 - 公开 API",
            "kind": "video",
            "ext": "mp4",
            "height": None,
            "filesize": None,
            "has_audio": True,
            "title": "无水印视频 (MP4)",
            "subtitle": "MP4 - 公开 API",
        }
    ]


def extract_video_id_from_long_url(url: str) -> str | None:
    """兼容旧 API：直接调用 extract_video_id。"""
    return extract_video_id(url)


def resolve_video_id(url: str) -> str:
    """兼容旧 API：完整解析流程。失败抛 DouyinUpstreamError。"""
    try:
        share_url = _extract_url(url)
        final_url = DouyinParser()._resolve_redirect(share_url)
    except Exception as exc:
        raise DouyinUpstreamError(f"链接解析失败：{exc}") from exc
    vid = extract_video_id(final_url)
    if not vid:
        raise DouyinUpstreamError("无法从链接中提取视频ID，链接可能无效或已过期")
    return vid


# 模块级解析器实例（复用连接）
_parser: DouyinParser | None = None


def _get_parser() -> DouyinParser:
    global _parser
    if _parser is None:
        _parser = DouyinParser()
    return _parser


def parse_video(url: str) -> dict[str, Any]:
    """解析抖音视频 URL（兼容旧 API）。"""
    return _get_parser().parse(url)


def download_video(
    url: str,
    format_id: str,
    dest_dir: Path,
    progress_hook,
) -> Path:
    """下载抖音视频（兼容旧 API）。

    Returns:
        下载完成的文件路径
    """
    return _get_parser().download(url, format_id, dest_dir, progress_hook)
