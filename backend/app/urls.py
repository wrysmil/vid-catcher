from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048

# 缩略图代理白名单：只允许 yt-dlp 实际会返回的 CDN 域名。避免把 /api/thumbnail
# 当成跳板做 SSRF（访问内网、读本地文件等）。
THUMB_ALLOWED_HOSTS = {
    "i0.hdslb.com",
    "i1.hdslb.com",
    "i2.hdslb.com",
    "bfs/archive",  # 占位，避免误伤（实际匹配的是子域）
    "yt3.ggpht.com",
    "i.ytimg.com",
    "i9.ytimg.com",
    "img.youtube.com",
}


def validate_http_url(raw: str) -> str:
    if raw is None:
        raise ValueError("请粘贴视频链接")
    url = raw.strip()
    if not url:
        raise ValueError("请粘贴视频链接")
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("链接过长")
    if any(ch.isspace() for ch in url):
        raise ValueError("一次只解析一条链接")
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("只支持 http / https 链接")
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError("链接不完整")
    return url


def validate_thumb_url(raw: str) -> str:
    """白名单内的图片 CDN URL；其余直接拒。"""
    url = validate_http_url(raw)
    host = urlparse(url).hostname or ""
    if host not in THUMB_ALLOWED_HOSTS:
        raise ValueError(f"缩略图域名不在白名单: {host}")
    return url
