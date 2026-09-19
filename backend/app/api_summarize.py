"""AI 视频总结相关 API 路由（独立模块，通过 include_router 挂载）"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .summarizer import SubtitleExtractor, VideoSummarizer
from .urls import validate_http_url

router = APIRouter(prefix="/api", tags=["AI 总结"])


class SummarizeRequest(BaseModel):
    url: str
    language: str = "zh"


class ChatRequest(BaseModel):
    url: str
    question: str
    subtitle_text: str = ""


def _sse(event: str, data: str) -> str:
    lines = data.split("\n")
    payload = "".join(f"data: {line}\n" for line in lines)
    return f"event: {event}\n{payload}\n\n"


_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _get_summarizer() -> VideoSummarizer:
    """延迟初始化 VideoSummarizer（仅在首次调用时创建）"""
    if not hasattr(_get_summarizer, "_instance"):
        try:
            _get_summarizer._instance = VideoSummarizer()
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _get_summarizer._instance


def _get_extractor() -> SubtitleExtractor:
    """延迟初始化 SubtitleExtractor"""
    if not hasattr(_get_extractor, "_instance"):
        _get_extractor._instance = SubtitleExtractor()
    return _get_extractor._instance


@router.post("/summarize")
async def summarize_video(req: SummarizeRequest):
    """
    AI 视频总结（SSE 流式）
    事件类型: subtitle / summary / summary_done / mindmap / done / error
    """
    try:
        validate_http_url(req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def event_generator():
        try:
            yield ": keepalive subtitle\n\n"
            loop = asyncio.get_running_loop()
            extractor = _get_extractor()
            subtitle_data = await loop.run_in_executor(
                None, extractor.extract, req.url
            )

            yield _sse(
                "subtitle",
                json.dumps(subtitle_data, ensure_ascii=False),
            )

            if not subtitle_data["has_subtitle"]:
                yield _sse(
                    "error",
                    json.dumps(
                        {"message": "该视频没有可用的字幕，无法生成总结"},
                        ensure_ascii=False,
                    ),
                )
                return

            full_text = subtitle_data["full_text"]
            summarizer = _get_summarizer()

            yield ": keepalive summary\n\n"
            for token in summarizer.summarize_stream(full_text, req.language):
                yield _sse("summary", token)
                await asyncio.sleep(0)

            yield _sse("summary_done", "[DONE]")

            yield ": keepalive mindmap\n\n"
            mindmap_md = await loop.run_in_executor(
                None, summarizer.generate_mindmap, full_text, req.language
            )
            yield _sse(
                "mindmap",
                json.dumps({"markdown": mindmap_md}, ensure_ascii=False),
            )

            yield _sse("done", "[DONE]")

        except Exception as e:
            yield _sse(
                "error",
                json.dumps({"message": f"总结失败: {str(e)}"}, ensure_ascii=False),
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/chat")
async def chat_with_video(req: ChatRequest):
    """AI 视频问答（SSE 流式）"""
    try:
        validate_http_url(req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def event_generator():
        try:
            if not req.subtitle_text.strip():
                loop = asyncio.get_running_loop()
                extractor = _get_extractor()
                subtitle_data = await loop.run_in_executor(
                    None, extractor.extract, req.url
                )
                if not subtitle_data["has_subtitle"]:
                    yield _sse(
                        "error",
                        json.dumps(
                            {"message": "该视频没有可用的字幕，无法回答问题"},
                            ensure_ascii=False,
                        ),
                    )
                    return
                subtitle_text = subtitle_data["full_text"]
            else:
                subtitle_text = req.subtitle_text

            summarizer = _get_summarizer()
            for token in summarizer.chat_stream(subtitle_text, req.question):
                yield _sse("answer", token)
                await asyncio.sleep(0)

            yield _sse("done", "[DONE]")

        except Exception as e:
            yield _sse(
                "error",
                json.dumps({"message": f"回答失败: {str(e)}"}, ensure_ascii=False),
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
