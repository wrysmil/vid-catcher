from __future__ import annotations

import threading
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from .tasks import store
from .urls import validate_http_url, validate_thumb_url
from .ytdlp_service import BROWSER_HEADERS, DOWNLOAD_DIR, download_video, parse_video

app = FastAPI(title="Free Video Downloader", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UrlPayload(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class DownloadPayload(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    format_id: str = Field(default="bv*+ba/b", max_length=120)


@app.get("/api/health")
def health():
    return {"ok": True, "engine": "yt-dlp"}


@app.post("/api/parse")
def parse(payload: UrlPayload):
    try:
        url = validate_http_url(payload.url)
        return parse_video(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_public_error(exc)) from exc


@app.post("/api/download")
def start_download(payload: DownloadPayload):
    try:
        url = validate_http_url(payload.url)
        format_id = payload.format_id.strip() or "bv*+ba/b"
        task = store.create(url, format_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    worker = threading.Thread(target=_run_download, args=(task.id,), daemon=True)
    worker.start()
    return store.to_public(task)


@app.get("/api/tasks/{task_id}")
def task_status(task_id: str):
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return store.to_public(task)


@app.get("/api/tasks/{task_id}/file")
def task_file(task_id: str):
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if task.status != "finished" or not task.filename:
        raise HTTPException(status_code=409, detail="还没下完")
    path = Path(task.filename).resolve()
    download_root = DOWNLOAD_DIR.resolve()
    if download_root not in path.parents and path != download_root:
        raise HTTPException(status_code=400, detail="非法文件路径")
    if not path.exists():
        raise HTTPException(status_code=410, detail="文件已清理")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.get("/api/thumbnail")
def thumbnail(url: str):
    """后端代理封面图，绕开浏览器 Referer 被 CDN 防盗链拦截的问题。"""
    try:
        target = validate_thumb_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        r = requests.get(
            target,
            headers={
                "User-Agent": BROWSER_HEADERS["User-Agent"],
                "Referer": "https://www.bilibili.com/",
            },
            timeout=8,
            stream=False,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"上游拉取失败: {exc.__class__.__name__}") from exc
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"上游返回 {r.status_code}")
    media_type = r.headers.get("content-type", "image/jpeg").split(";")[0].strip() or "image/jpeg"
    return Response(content=r.content, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


def _run_download(task_id: str) -> None:
    task = store.get(task_id)
    if not task:
        return
    store.update(task_id, status="downloading")

    def hook(event: dict) -> None:
        status = event.get("status")
        if status == "downloading":
            total = event.get("total_bytes") or event.get("total_bytes_estimate") or 0
            downloaded = event.get("downloaded_bytes") or 0
            progress = (downloaded / total) if total else 0.0
            store.update(
                task_id,
                status="downloading",
                progress=min(progress, 0.99),
                speed=event.get("speed"),
                eta=event.get("eta"),
            )
        elif status == "finished":
            store.update(task_id, progress=1.0)

    try:
        dest = DOWNLOAD_DIR / task_id
        path = download_video(task.url, task.format_id, dest, hook)
        store.update(task_id, status="finished", progress=1.0, filename=str(path))
    except Exception as exc:
        store.update(task_id, status="error", error=_public_error(exc))


def _public_error(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    if "Unsupported URL" in text:
        return "这个链接 yt-dlp 还不认识，换 YouTube / B 站等平台视频试试"
    if "412" in text or "Precondition Failed" in text:
        return (
            "B 站风控拦了（HTTP 412）。本机浏览器先打开过这个视频后，"
            "可设置环境变量 YTDLP_COOKIES_FROM_BROWSER=chrome 再重启后端，"
            "用你自己浏览器里的登录态解析公开视频。大会员/付费片不在学习版范围。"
        )
    if len(text) > 240:
        text = text[:237] + "..."
    return text
