from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

MAX_CONCURRENT = 2
TASK_TTL_SECONDS = 30 * 60


@dataclass
class DownloadTask:
    id: str
    url: str
    format_id: str
    status: str = "queued"
    progress: float = 0.0
    speed: Optional[float] = None
    eta: Optional[float] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, DownloadTask] = {}

    def active_count(self) -> int:
        with self._lock:
            self._purge_locked()
            return sum(1 for t in self._tasks.values() if t.status in {"queued", "downloading"})

    def create(self, url: str, format_id: str) -> DownloadTask:
        with self._lock:
            self._purge_locked()
            active = sum(1 for t in self._tasks.values() if t.status in {"queued", "downloading"})
            if active >= MAX_CONCURRENT:
                raise RuntimeError("同时下载已满，请等一条完成")
            task = DownloadTask(id=uuid.uuid4().hex, url=url, format_id=format_id)
            self._tasks[task.id] = task
            return task

    def get(self, task_id: str) -> Optional[DownloadTask]:
        with self._lock:
            self._purge_locked()
            return self._tasks.get(task_id)

    def update(self, task_id: str, **changes) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            for key, value in changes.items():
                setattr(task, key, value)

    def to_public(self, task: DownloadTask) -> dict:
        return {
            "id": task.id,
            "status": task.status,
            "progress": round(task.progress, 3),
            "speed": task.speed,
            "eta": task.eta,
            "filename": Path(task.filename).name if task.filename else None,
            "error": task.error,
            "ready": task.status == "finished" and bool(task.filename),
        }

    def _purge_locked(self) -> None:
        now = time.time()
        stale = [tid for tid, task in self._tasks.items() if now - task.created_at > TASK_TTL_SECONDS]
        for tid in stale:
            task = self._tasks.pop(tid, None)
            if task and task.filename:
                path = Path(task.filename)
                if path.exists():
                    path.unlink(missing_ok=True)


store = TaskStore()
