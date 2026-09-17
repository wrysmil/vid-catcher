import unicodedata
from pathlib import Path

from app.filenames import safe_filename
from app.ytdlp_service import _rename_to_title


def test_keeps_chinese_and_emoji():
    # 回归点：之前开了 restrictfilenames，中文会被整个删掉，文件名只剩 ".mp4"
    assert safe_filename("【4K】猫咪的日常 vlog 🐱", ext="mp4") == "【4K】猫咪的日常 vlog 🐱.mp4"
    assert safe_filename("测试视频", ext="mp4") == "测试视频.mp4"


def test_replaces_illegal_and_control_chars():
    assert safe_filename('a/b\\c:d*e?f"g<h>i|j', ext="mp4") == "a_b_c_d_e_f_g_h_i_j.mp4"
    assert safe_filename("line1\nline2\tend", ext="mp4") == "line1_line2_end.mp4"


def test_collapses_separators_and_trims_edges():
    assert safe_filename("  ..hello___world..  ", ext="mp4") == "hello_world.mp4"
    assert safe_filename("...", ext="mp4") == "video.mp4"


def test_truncates_to_budget_and_retrims():
    name = safe_filename("字" * 200, ext="mp4")
    assert name == "字" * 80 + ".mp4"

    # 截断后落在分隔符上，要去掉尾巴，不能留下 "xxx_.mp4"
    tail = safe_filename("a" * 79 + "_" + "b" * 50, ext="mp4")
    assert tail == "a" * 79 + ".mp4"


def test_windows_reserved_device_names():
    # NTFS 会把这些当设备，直接创建失败，必须改名
    assert safe_filename("CON", ext="mp4") == "_CON.mp4"
    assert safe_filename("nul", ext="mp4") == "_nul.mp4"
    assert safe_filename("COM3", ext="mp4") == "_COM3.mp4"
    assert safe_filename("CON.raw", ext="mp4") == "_CON.raw.mp4"
    # 只是以保留名开头不算冲突
    assert safe_filename("CONSOLE", ext="mp4") == "CONSOLE.mp4"


def test_falls_back_when_title_is_unusable():
    assert safe_filename(None, fallback="douyin_7123", ext="mp4") == "douyin_7123.mp4"
    assert safe_filename("", fallback="douyin_7123", ext="mp4") == "douyin_7123.mp4"
    assert safe_filename("///", fallback="douyin_7123", ext="mp4") == "douyin_7123.mp4"
    # fallback 也洗不出东西时兜底到 video
    assert safe_filename(None, fallback="", ext="mp4") == "video.mp4"


def test_normalizes_nfd_to_nfc():
    nfd = unicodedata.normalize("NFD", "café")
    assert safe_filename(nfd, ext="mp4") == "café.mp4"


def test_accepts_ext_with_or_without_dot():
    assert safe_filename("t", ext="mp4") == "t.mp4"
    assert safe_filename("t", ext=".mp4") == "t.mp4"
    assert safe_filename("t", ext="") == "t"


def test_rename_to_title_uses_sanitized_title(tmp_path: Path):
    intermediate = tmp_path / "4K_vlog_1.mp4"
    intermediate.write_bytes(b"x")

    result = _rename_to_title(intermediate, {"title": "【4K】猫咪的日常 vlog #1", "id": "abc"})

    assert result.name == "【4K】猫咪的日常 vlog #1.mp4"
    assert result.read_bytes() == b"x"
    assert not intermediate.exists()


def test_rename_to_title_falls_back_to_video_id(tmp_path: Path):
    intermediate = tmp_path / "4K_vlog_1.mp4"
    intermediate.write_bytes(b"x")

    # 标题洗完后为空 -> 用 video_<id> 兜底，不能落成 ".mp4"
    result = _rename_to_title(intermediate, {"title": "...", "id": "7123456789012345678"})

    assert result.name == "video_7123456789012345678.mp4"
    assert result.read_bytes() == b"x"
