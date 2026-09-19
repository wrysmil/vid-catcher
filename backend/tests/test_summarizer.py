from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.summarizer import (
    SubtitleExtractor,
    VideoSummarizer,
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


class FakeDelta:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.delta = FakeDelta(content)


class FakeChunk:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


@patch.dict("os.environ", {"AI_API_KEY": "test-key"})
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


@patch.dict("os.environ", {}, clear=True)
def test_summarizer_missing_key():
    with pytest.raises(ValueError, match="AI_API_KEY"):
        VideoSummarizer()
