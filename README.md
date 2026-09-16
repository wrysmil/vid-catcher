# 万能视频下载站（学习向）

本机/局域网学习项目：网页封装 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，用来理解「薄封装开源引擎 + 转化向前端」的开发方式。

请只下载你有权保存的内容。不要破解 DRM、不要用平台 Cookie 去碰登录态、不要把服务裸挂公网当盗链站。站点改版导致失败时，升级 `yt-dlp` 即可，不要自己写提取器。

## 启动

需要 Python 3.11+、Node.js 18+、本机 `ffmpeg`（合并音视频）。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5173

## 接口

- `GET /api/health`
- `POST /api/parse` `{"url":"..."}`
- `POST /api/download` `{"url":"...","format_id":"bv*+ba/b"}`
- `GET /api/tasks/{id}`
- `GET /api/tasks/{id}/file`

一期无数据库、无真实支付。页面上的总结 / 翻译 / 批量是占位。

## B 站 412

B 站会拦不像浏览器的请求。后端已带常见 Referer / UA。若仍 412：

1. 用本机浏览器先打开该视频（让站点自己过校验）
2. 重启后端时带上你自己的浏览器 Cookie（不要用别人的）：

```bash
export YTDLP_COOKIES_FROM_BROWSER=chrome   # 或 safari / firefox
```

大会员、付费、需登录才能看的内容不在学习版范围。
