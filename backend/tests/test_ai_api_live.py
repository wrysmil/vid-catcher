"""AI API 联调测试 — 调试 Command Provider 与总结链路。

在 backend/ 目录运行:

    AI_SMOKE=1 pytest tests/test_ai_api_live.py -v -s

可选:
    AI_SMOKE_URL=https://www.bilibili.com/video/BV1GJ411x7h7
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from openai import OpenAI

from app.main import app
from app.summarizer import SubtitleExtractor, VideoSummarizer

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

DEFAULT_BILI_URL = "https://www.bilibili.com/video/BV1GJ411x7h7"
SAMPLE_SUBTITLE = (
    "这是一段用于 API 调试的测试字幕。"
    "视频介绍了如何使用 Python FastAPI 构建后端，以及如何通过 SSE 推送流式响应。"
)


def _skip_unless_smoke() -> None:
    if os.environ.get("AI_SMOKE") != "1":
        pytest.skip("set AI_SMOKE=1 to run live AI API tests")


def _mask_secret(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _ai_config() -> tuple[str, str, str]:
    api_key = os.getenv("AI_API_KEY", "").strip()
    base_url = os.getenv("AI_API_BASE_URL", "https://api.commandcode.ai/provider/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "deepseek/deepseek-v4-flash")
    return api_key, base_url, model


def _parse_sse(body: str) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    current_event = ""
    data_lines: list[str] = []
    for line in body.split("\n"):
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif line.strip() == "" and (current_event or data_lines):
            events.append((current_event, "\n".join(data_lines)))
            current_event = ""
            data_lines = []
    if current_event or data_lines:
        events.append((current_event, "\n".join(data_lines)))
    return events


@pytest.mark.live
class TestCommandApiLive:
    """逐步验证：环境变量 → HTTP → SDK → Summarizer → 字幕 → SSE 端点。"""

    def test_01_env_config(self):
        _skip_unless_smoke()
        api_key, base_url, model = _ai_config()
        print(f"\n[step 1] .env path={ENV_PATH} exists={ENV_PATH.exists()}")
        print(f"[step 1] AI_API_KEY={_mask_secret(api_key)} len={len(api_key)}")
        print(f"[step 1] AI_API_BASE_URL={base_url}")
        print(f"[step 1] AI_MODEL={model}")
        if not api_key:
            pytest.fail("AI_API_KEY 未设置，请在 backend/.env 中填写后重试")

    def test_02_raw_http_chat_completion(self):
        _skip_unless_smoke()
        api_key, base_url, model = _ai_config()
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "回复 OK 两个字母即可"}],
            "stream": False,
            "max_tokens": 16,
        }
        print(f"\n[step 2] POST {url}")
        try:
            resp = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
        except httpx.HTTPError as exc:
            pytest.fail(f"HTTP 请求失败: {exc}")

        print(f"[step 2] status={resp.status_code}")
        print(f"[step 2] body={resp.text[:800]}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        msg = data["choices"][0]["message"]
        content = (msg.get("content") or "").strip()
        reasoning = (msg.get("reasoning") or "").strip()
        print(f"[step 2] content={content!r} reasoning={reasoning[:80]!r}")
        assert content or reasoning, (
            "API 200 但 message 无 content/reasoning，可能是模型或 max_tokens 过小"
        )

    def test_03_openai_sdk_stream(self):
        _skip_unless_smoke()
        api_key, base_url, model = _ai_config()
        client = OpenAI(api_key=api_key, base_url=base_url)
        print(f"\n[step 3] OpenAI SDK base_url={base_url} model={model}")
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "用中文说：测试成功"}],
            stream=True,
            max_tokens=32,
        )
        chunks = []
        for chunk in stream:
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                chunks.append(delta.content)
            elif getattr(delta, "reasoning", None):
                chunks.append(delta.reasoning)
        text = "".join(chunks)
        print(f"[step 3] stream text={text!r}")
        assert text.strip(), "流式响应未收到 content/reasoning token"

    def test_04_video_summarizer_stream(self):
        _skip_unless_smoke()
        summarizer = VideoSummarizer()
        print(f"\n[step 4] model={summarizer.model}")
        tokens = []
        for token in summarizer.summarize_stream(SAMPLE_SUBTITLE, "zh"):
            tokens.append(token)
            if len("".join(tokens)) >= 80:
                break
        preview = "".join(tokens)
        print(f"[step 4] summary preview={preview[:200]!r}")
        assert preview.strip(), "VideoSummarizer 未产出摘要 token"

    def test_05_subtitle_extract_bilibili(self):
        _skip_unless_smoke()
        video_url = os.environ.get("AI_SMOKE_URL", DEFAULT_BILI_URL)
        print(f"\n[step 5] extract url={video_url}")
        data = SubtitleExtractor().extract(video_url)
        print(
            f"[step 5] has_subtitle={data['has_subtitle']} "
            f"lang={data.get('language')} type={data.get('subtitle_type')} "
            f"segments={len(data.get('segments') or [])}"
        )
        if data.get("full_text"):
            print(f"[step 5] full_text preview={data['full_text'][:120]!r}")
        assert data["has_subtitle"], (
            "B 站字幕提取失败。可换 AI_SMOKE_URL 或检查网络；"
            "抖音等无字幕链接无法走总结。"
        )

    def test_06_sse_summarize_endpoint(self):
        _skip_unless_smoke()
        video_url = os.environ.get("AI_SMOKE_URL", DEFAULT_BILI_URL)
        client = TestClient(app)
        print(f"\n[step 6] POST /api/summarize url={video_url}")
        with client.stream(
            "POST",
            "/api/summarize",
            json={"url": video_url, "language": "zh"},
        ) as resp:
            assert resp.status_code == 200, resp.text
            body = "".join(resp.iter_text())

        events = _parse_sse(body)
        event_names = [name for name, _ in events]
        print(f"[step 6] events={event_names}")
        for name, payload in events:
            if name == "error":
                try:
                    msg = json.loads(payload).get("message", payload)
                except json.JSONDecodeError:
                    msg = payload
                pytest.fail(f"SSE error 事件: {msg}")
            if name == "summary":
                print(f"[step 6] summary token sample={payload[:80]!r}")
                break
        else:
            pytest.fail(f"未收到 summary 事件，完整 SSE:\n{body[:1500]}")

    def test_07_douyin_jingxuan_uses_public_api_desc(self):
        """抖音 jingxuan 走公开 API：有文案则进入总结，无文案才报错。"""
        _skip_unless_smoke()
        douyin_url = os.environ.get(
            "AI_SMOKE_DOUYIN_URL",
            "https://www.douyin.com/jingxuan?modal_id=7686500203570023723",
        )
        print(f"\n[step 7] douyin url={douyin_url}")
        data = SubtitleExtractor().extract(douyin_url)
        print(
            f"[step 7] extract has_subtitle={data['has_subtitle']} "
            f"type={data.get('subtitle_type')} text={data.get('full_text', '')[:80]!r}"
        )
        assert "Unsupported URL" not in (data.get("full_text") or "")

        client = TestClient(app)
        with client.stream(
            "POST",
            "/api/summarize",
            json={"url": douyin_url, "language": "zh"},
        ) as resp:
            body = "".join(resp.iter_text())
        events = _parse_sse(body)
        event_names = [name for name, _ in events]
        print(f"[step 7] SSE events={event_names}")
        assert "subtitle" in event_names, f"应先推字幕/文案事件，SSE:\n{body[:800]}"
        assert "Unsupported URL" not in body
        if data["has_subtitle"]:
            assert "summary" in event_names or "done" in event_names
        else:
            assert "error" in event_names
