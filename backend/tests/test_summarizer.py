from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.summarizer import (
    SubtitleExtractor,
    VideoSummarizer,
    _douyin_summary_text,
    build_chat_completion_extra_kwargs,
    parse_vtt,
    time_to_seconds,
    truncate_text,
)


SAMPLE_VTT = """WEBVTT

00:00:01.000 --> 00:00:03.500
Hello <b>world</b>

00:00:03.500 --> 00:00:06.000
Second line
"""


def test_time_to_seconds():
    assert time_to_seconds("00:00:01.000") == 1.0
    assert time_to_seconds("00:01:30.500") == 90.5
    assert time_to_seconds("01:00:00.000") == 3600.0


def test_parse_vtt_basic():
    segs = parse_vtt(SAMPLE_VTT)
    assert len(segs) == 2
    assert segs[0]["start"] == 1.0
    assert segs[0]["end"] == 3.5
    assert segs[0]["text"] == "Hello world"
    assert segs[1]["text"] == "Second line"


def test_truncate_text_short():
    assert truncate_text("abc", 10) == "abc"


def test_truncate_text_long():
    text = "a" * 20000
    out = truncate_text(text, 15000)
    assert len(out) <= 15000
    assert "截断" in out


@patch.dict("os.environ", {"AI_REASONING": "off"}, clear=False)
def test_build_chat_completion_extra_kwargs_off():
    assert build_chat_completion_extra_kwargs() == {
        "extra_body": {"thinking": {"type": "disabled"}},
    }


@patch.dict("os.environ", {"AI_REASONING": "high"}, clear=False)
def test_build_chat_completion_extra_kwargs_level():
    assert build_chat_completion_extra_kwargs() == {
        "reasoning_effort": "high",
        "extra_body": {"thinking": {"type": "enabled"}},
    }


@patch.dict("os.environ", {"AI_REASONING": "on"}, clear=False)
def test_build_chat_completion_extra_kwargs_on():
    assert build_chat_completion_extra_kwargs() == {}


class FakeDelta:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)


class FakeChunk:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


@patch.dict(
    "os.environ",
    {
        "AI_API_KEY": "test-key",
        "AI_MODEL": "deepseek/deepseek-v4-flash",
        "AI_REASONING": "off",
    },
    clear=False,
)
@patch("app.summarizer.OpenAI")
def test_summarize_stream_yields_tokens(mock_openai):
    client = MagicMock()
    mock_openai.return_value = client
    client.chat.completions.create.return_value = [
        FakeChunk("Hello"),
        FakeChunk(" world"),
    ]
    vs = VideoSummarizer()
    tokens = list(vs.summarize_stream("subtitle text", "zh"))
    assert tokens == ["Hello", " world"]
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is True
    assert call_kwargs["model"] == "deepseek/deepseek-v4-flash"
    assert call_kwargs["extra_body"] == {"thinking": {"type": "disabled"}}


@patch.dict("os.environ", {}, clear=True)
def test_summarizer_missing_key():
    with pytest.raises(ValueError, match="AI_API_KEY"):
        VideoSummarizer()


@patch("app.summarizer.yt_dlp.YoutubeDL")
@patch("app.summarizer.parse_video")
def test_extract_douyin_jingxuan_uses_public_api_not_ytdlp(mock_parse, mock_ydl):
    """抖音 jingxuan 走公开 API，不得把原始 URL 丢给 yt-dlp。"""
    mock_parse.return_value = {
        "title": "一条很长的抖音文案内容用于总结",
        "description": "一条很长的抖音文案内容用于总结",
        "desc": "一条很长的抖音文案内容用于总结",
    }
    jingxuan = "https://www.douyin.com/jingxuan?modal_id=7686500203570023723"
    result = SubtitleExtractor().extract(jingxuan)

    mock_ydl.assert_not_called()
    mock_parse.assert_called_once_with(jingxuan, require_play_url=False)
    assert result["has_subtitle"] is True
    assert result["subtitle_type"] == "description"
    assert result["full_text"] == "一条很长的抖音文案内容用于总结"
    assert result["segments"][0]["text"] == result["full_text"]


@patch("app.summarizer.yt_dlp.YoutubeDL")
@patch("app.summarizer.parse_video")
def test_extract_douyin_empty_desc_has_no_subtitle(mock_parse, mock_ydl):
    mock_parse.return_value = {
        "title": "抖音视频_7686500203570023723",
        "description": None,
        "desc": "",
    }
    result = SubtitleExtractor().extract(
        "https://www.douyin.com/video/7686500203570023723"
    )
    mock_ydl.assert_not_called()
    assert result["has_subtitle"] is False
    assert result["full_text"] == ""


def test_douyin_summary_text_prefers_full_desc():
    assert _douyin_summary_text({"desc": "完整文案", "title": "截断"}) == "完整文案"
    assert _douyin_summary_text({"desc": "", "title": "抖音视频_123"}) == ""
    assert _douyin_summary_text({"desc": "", "title": "有内容的标题"}) == "有内容的标题"
