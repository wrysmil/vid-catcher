from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api_summarize._get_extractor")
@patch("app.api_summarize._get_summarizer")
def test_summarize_sse_no_subtitle(mock_sum, mock_ext):
    ext = MagicMock()
    ext.extract.return_value = {
        "has_subtitle": False,
        "language": "",
        "subtitle_type": "none",
        "segments": [],
        "full_text": "",
    }
    mock_ext.return_value = ext

    with client.stream(
        "POST",
        "/api/summarize",
        json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
    ) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
        assert "event: subtitle" in body
        assert "event: error" in body
        assert "没有可用" in body


@patch("app.api_summarize._get_extractor")
@patch("app.api_summarize._get_summarizer")
def test_summarize_sse_encodes_summary_token_as_json(mock_sum, mock_ext):
    ext = MagicMock()
    ext.extract.return_value = {
        "has_subtitle": True,
        "language": "zh",
        "subtitle_type": "manual",
        "segments": [{"start": 0, "end": 1, "text": "你好"}],
        "full_text": "你好",
    }
    mock_ext.return_value = ext

    summarizer = MagicMock()
    summarizer.summarize_stream.return_value = iter(["概述\n\n- 要点"])
    summarizer.generate_mindmap.return_value = "# 图"
    mock_sum.return_value = summarizer

    with client.stream(
        "POST",
        "/api/summarize",
        json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
    ) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())

    encoded = json.dumps("概述\n\n- 要点", ensure_ascii=False)
    assert f"data: {encoded}" in body
    assert "event: summary" in body


@patch("app.api_summarize._get_extractor")
@patch("app.api_summarize._get_summarizer")
def test_chat_sse_encodes_answer_token_as_json(mock_sum, mock_ext):
    summarizer = MagicMock()
    summarizer.chat_stream.return_value = iter(["第一行\n第二行"])
    mock_sum.return_value = summarizer

    with client.stream(
        "POST",
        "/api/chat",
        json={
            "url": "https://www.bilibili.com/video/BV1xx411c7mD",
            "question": "核心观点？",
            "subtitle_text": "字幕正文",
        },
    ) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())

    encoded = json.dumps("第一行\n第二行", ensure_ascii=False)
    assert f"data: {encoded}" in body
    assert "event: answer" in body
