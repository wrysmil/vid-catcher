"""导出文件名清洗。

磁盘上的文件名就是用户的下载名：任务目录是 tmp_downloads/<task_id>/ 独占的，
接口下发时 FileResponse 直接取 path.name。所以落盘前必须把标题洗成合法文件名，
否则用户拿到的就是原始标题或者一堆下划线。

设计参考开源项目 free-video-downloader：保留 Unicode（中文/日文/emoji 原样保留），
只替换文件系统不接受的字符。在它的基础上补了两处 Windows 特有的坑：

- 保留设备名（CON / NUL / COM1 ...）会被 NTFS 当成设备，创建直接失败
- 结尾的 "." 和空格会被 Windows 静默吞掉，用户看到的扩展名就没了
"""

from __future__ import annotations

import re
import unicodedata

MAX_STEM_CHARS = 80

# "/" "\" 是路径分隔符，其余是 Windows 禁止出现在文件名里的字符；
# \x00-\x1f \x7f 是控制字符（换行、制表符等）。
_ILLEGAL_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]')
_UNDERSCORE_RUN_RE = re.compile(r"_{2,}")
_WHITESPACE_RE = re.compile(r"\s+")

# Windows 保留设备名，比较时只看第一个 "." 之前的部分。
_RESERVED_STEMS = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)


def safe_filename(
    title: str | None,
    fallback: str = "video",
    ext: str = "mp4",
    max_chars: int = MAX_STEM_CHARS,
) -> str:
    """把视频标题转成安全文件名（含扩展名）。

    title 洗完后为空（纯符号标题、或被非法字符占满）时退回 fallback，
    fallback 也为空则用 "video"，保证任何输入都能得到一个可用名字。
    """
    stem = _clean_stem(title, max_chars) or _clean_stem(fallback, max_chars) or "video"
    suffix = (ext or "").lstrip(".")
    return f"{stem}.{suffix}" if suffix else stem


def _clean_stem(value: str | None, max_chars: int) -> str:
    if not value:
        return ""

    # macOS 上传的标题常是 NFD（"é" = e + 组合符），先归一，避免同一标题出现两个文件名。
    text = unicodedata.normalize("NFC", str(value))
    text = _ILLEGAL_RE.sub("_", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _UNDERSCORE_RUN_RE.sub("_", text)
    text = text.strip("_. ")
    text = text[:max_chars]
    # 截断可能又切出结尾的 "." / "_" / 空格，再去一次。
    text = text.strip("_. ")
    if not text:
        return ""

    if text.split(".", 1)[0].upper() in _RESERVED_STEMS:
        text = f"_{text}"
    return text
