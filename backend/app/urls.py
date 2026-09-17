from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048

# 缩略图代理白名单：只允许真实 CDN 域名，避免把 /api/thumbnail 当成跳板做 SSRF。
THUMB_ALLOWED_HOSTS = {
    "yt3.ggpht.com",
    "i.ytimg.com",
    "i9.ytimg.com",
    "img.youtube.com",
}

# 允许的 CDN 后缀（含所有子域）：B 站 i0/i1/i2.hdslb.com、抖音 p3/p26-sign.douyinpic.com 等。
THUMB_ALLOWED_SUFFIXES = {
    "hdslb.com",
    "douyinpic.com",
    "douyinvod.com",
}


def _thumb_host_allowed(host: str) -> bool:
    if host in THUMB_ALLOWED_HOSTS:
        return True
    return any(host == suffix or host.endswith("." + suffix) for suffix in THUMB_ALLOWED_SUFFIXES)


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
    if not _thumb_host_allowed(host):
        raise ValueError(f"缩略图域名不在白名单: {host}")
    return url
