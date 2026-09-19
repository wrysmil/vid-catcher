from __future__ import annotations

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
