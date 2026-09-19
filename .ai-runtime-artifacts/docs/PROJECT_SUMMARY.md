# VidCatcher 项目总结

> 本文档记录 VidCatcher（万能视频下载·学习向）项目的核心实现与架构设计。

## 项目概述

VidCatcher 是一个本地/局域网学习项目，通过封装开源 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 引擎并向前端转化，用于理解「薄封装开源引擎 + API 前端」的开发模式。

## 技术架构

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI (Python 3.11+) |
| 视频引擎 | yt-dlp |
| 前端框架 | Vue.js 3 + Vite |
| 下载工具 | ffmpeg（音视频合并）|

### 目录结构

```
vid-catcher/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 应用入口，路由定义
│   │   ├── ytdlp_service.py  # yt-dlp 封装，解析与下载
│   │   ├── douyin_service.py # 抖音自研解析链路
│   │   ├── filenames.py      # 安全文件名处理
│   │   ├── formats.py        # 视频格式配置
│   │   ├── tasks.py          # 下载任务状态管理
│   │   └── urls.py           # URL 验证工具
│   ├── tests/                # 后端单元测试
│   └── tmp_downloads/        # 临时下载目录
└── frontend/
    ├── src/
    │   ├── App.vue            # 主应用组件
    │   ├── main.js            # 前端入口
    │   └── style.css         # 全局样式
    └── index.html
```

## 核心功能实现

### 1. 视频解析

**通用平台（yt-dlp）**

入口：`POST /api/parse`

```python
# backend/app/ytdlp_service.py
def parse_video(url: str) -> dict:
    opts = {**_base_opts(), "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        raw = ydl.extract_info(url, download=False)
        info = ydl.sanitize_info(raw)
    # 返回标准化视频信息
```

**抖音平台（自研）**

入口：`POST /api/parse` → 判断 `is_douyin_url(url)` 后走 `_parse_douyin`

```python
# backend/app/douyin_service.py
class DouyinParser:
    def parse(self, url: str) -> dict:
        # 1. 提取 URL 并跟随重定向
        share_url = _extract_url(url)
        final_url = self._resolve_redirect(share_url)

        # 2. 提取 video_id
        video_id = extract_video_id(final_url)

        # 3. 拿原始 item（API 优先，失败走分享页）
        item_info = self._fetch_item_info(video_id)

        # 4. 构建结果
        return _build_result(item_info, video_id, url)
```

**抖音解析流程**：
1. 从分享文本提取 URL
2. GET 跟随重定向（v.douyin.com 短链 → 真实视频页）
3. 提取 video_id（支持多种 URL 格式）
4. 优先调用官方公开 API（iesdouyin/iteminfo）
5. 失败时走分享页 HTML 解析（含 WAF SHA-256 挑战解决）
6. 提取 video.play_addr.url_list 并去水印

### 2. 视频下载

**异步下载模式**

```python
# backend/app/main.py
@app.post("/api/download")
def start_download(payload: DownloadPayload):
    task = store.create(url, format_id)
    worker = threading.Thread(target=_run_download, args=(task.id,), daemon=True)
    worker.start()
    return store.to_public(task)
```

**下载进度跟踪**

```python
def hook(event: dict) -> None:
    if event.get("status") == "downloading":
        progress = downloaded / total if total else 0.0
        store.update(task_id, status="downloading", progress=progress, ...)
```

### 3. 前端交互

```javascript
// 解析视频
const res = await fetch("/api/parse", {
  method: "POST",
  body: JSON.stringify({ url })
});

// 下载并轮询状态
const res = await fetch("/api/download", {
  method: "POST",
  body: JSON.stringify({ url, format_id })
});
pollTask(taskId);  // 每 1.2s 轮询
```

### 4. URL 归一化

抖音链接格式转换（jingxuan → video）：

```python
# /jingxuan?modal_id=XXX → /video/XXX
def _normalize_douyin_url(url: str) -> str:
    # 让 yt-dlp 自带的 douyin extractor 能识别
```

### 5. 错误处理

关键场景的中文错误提示：

| 场景 | 错误提示 |
|------|----------|
| 不支持的 URL | "这个链接 yt-dlp 还不认识..." |
| YouTube 机器人验证 | "YouTube 现在需要浏览器 cookie..." |
| 抖音 Fresh cookies | "抖音风控需要浏览器 cookie..." |
| B 站 412 | "B 站风控拦了（HTTP 412）..." |

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/parse` | POST | 解析视频 URL |
| `/api/download` | POST | 发起下载任务 |
| `/api/tasks/{id}` | GET | 查询任务状态 |
| `/api/tasks/{id}/file` | GET | 下载文件 |
| `/api/thumbnail` | GET | 封面图代理（解决 Referer 防盗链）|

## 关键设计决策

### 1. Cookie 处理

B 站和抖音会拦截不像浏览器的请求：
- 后端预置常见 Referer/UA
- 支持通过环境变量从浏览器导入 Cookie：
  ```bash
  export YTDLP_COOKIES_FROM_BROWSER=chrome
  ```

### 2. 文件名安全

```python
# backend/app/filenames.py
def safe_filename(title, fallback, ext):
    # 清洗标题中的非法字符，保留中文
    # 回退到 video_{id} 确保文件名不为空
```

### 3. 抖音 WAF 挑战解决

```python
def _solve_waf_challenge(wci, cs) -> str:
    # 暴力搜索 candidate 使 SHA256(prefix + str(candidate)) == hash
    # 返回可种入 cookie 的 base64 值
```

### 4. 封面图代理

```python
# /api/thumbnail 统一代理封面图
# 避免浏览器 Referer 被 CDN 防盗链拦截
```

## 最近完成的功能

### feat: 前端界面改版
- 全新的 Hero 区域设计
- 动态 Orb 装饰效果
- 响应式布局优化
- 平台支持展示

### feat: 接入自研抖音解析链路
- 完整抖音视频解析服务
- 支持多种 URL 格式（短链、长链、分享文本）
- WAF 挑战自动解决
- 去水印视频源获取

### feat: URL 归一化
- `/jingxuan?modal_id=X` → `/video/X` 自动转换
- 兼容 yt-dlp 抖音 extractor

### feat: 错误中文翻译
- 常见错误场景的中文操作指引
- Fresh cookies、412 等特殊提示

## 启动方式

```bash
# 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端
cd frontend
npm install
npm run dev

# 访问 http://127.0.0.1:5173
```

## 合规声明

- 本项目为**学习项目**，仅供理解技术原理
- 请只下载有权保存的内容
- 不要破解 DRM、不要用 Cookie 对抗登录态
- 不要把服务裸挂公网当盗链站
- 站点改版时升级 yt-dlp 即可，不要自己写提取器
