from app.formats import assert_duration_ok, quality_choices, slim_formats


def test_slim_formats_keeps_video_and_audio():
    raw = [
        {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360, "ext": "mp4"},
        {"format_id": "22", "vcodec": "avc1", "acodec": "mp4a", "height": 720, "ext": "mp4"},
        {"format_id": "22b", "vcodec": "avc1", "acodec": "mp4a", "height": 720, "ext": "mp4"},
        {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "ext": "m4a"},
        {"format_id": "skip", "vcodec": "none", "acodec": "none", "ext": "mhtml"},
    ]
    slim = slim_formats(raw)
    ids = [item["id"] for item in slim]
    assert ids == ["18", "22", "140"]
    assert slim[1]["label"] == "720p · mp4"
    assert slim[1]["title"] == "720p MP4 (含音频)"
    assert slim[1]["subtitle"] == "MP4 · 含音频"


def test_quality_choices_puts_merged_first():
    raw = [
        {
            "format_id": "30080",
            "vcodec": "avc1",
            "acodec": "none",
            "height": 1080,
            "ext": "mp4",
            "filesize": 18_900_000,
        },
        {
            "format_id": "30064",
            "vcodec": "avc1",
            "acodec": "none",
            "height": 720,
            "ext": "mp4",
            "filesize": 10_600_000,
        },
        {"format_id": "30280", "vcodec": "none", "acodec": "mp4a", "ext": "m4a"},
    ]
    cards = quality_choices(raw)
    assert cards[0]["id"] == "bv*[vcodec^=avc1]+ba/b"
    assert cards[0]["title"] == "1080p 最佳 (视频+音频合并)"
    assert cards[1]["id"] == "bv*[height<=720][vcodec^=avc1]+ba/b"
    assert cards[2]["title"] == "1080p MP4 (仅视频, 18.9MB)"
    assert cards[-1]["kind"] == "audio"


def test_reject_too_long_video():
    assert_duration_ok(120)
    try:
        assert_duration_ok(3 * 60 * 60 + 1)
    except ValueError as exc:
        assert "3 小时" in str(exc)
    else:
        raise AssertionError("expected duration reject")
